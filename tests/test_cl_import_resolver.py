"""
Tests for cl-imports auto-resolution (``src/cl_import_resolver.py``) and its
wiring into the domain-model importer.

The closure walk is exercised purely offline with a :class:`MappingResolver`
(diamond imports dedupe, missing modules are reported not dropped, cycles are
safe), the :class:`DirectoryResolver` / :class:`CachingResolver` are pinned on a
tmp directory, and the end-to-end path is checked through ``from_clif_text`` /
``from_clif_file`` — an ontology that *imports* its axioms imports complete.

The real-network :class:`ColoreWebResolver` is covered by one opt-in test that
skips cleanly when the COLORE repo is unreachable (CI/offline), like the
Playwright E2E suites.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from cl_import_resolver import (
    COLORE_PREFIX,
    CachingResolver,
    ChainResolver,
    ColoreWebResolver,
    DirectoryResolver,
    MappingResolver,
    extract_imports,
    resolve_from_iri,
    resolve_from_text,
)
from domain_model_importer import from_clif_file, from_clif_text


# A small synthetic COLORE-shaped closure:
#
#   root ─┬─> a ──> base
#         └─> b ──> base        (diamond: base reached two ways, included once)
P = COLORE_PREFIX
ROOT = P + "demo/root.clif"
A = P + "demo/a.clif"
B = P + "demo/b.clif"
BASE = P + "demo/base.clif"

ROOT_TEXT = (
    f"(cl-text {ROOT}\n"
    f"  (cl-imports {A})\n"
    f"  (cl-imports {B})\n"
    "  (forall (x) (if (Root x) (A x))))"
)
A_TEXT = (
    f"(cl-text {A}\n"
    f"  (cl-imports {BASE})\n"
    "  (forall (x) (if (A x) (Base x))))"
)
B_TEXT = (
    f"(cl-text {B}\n"
    f"  (cl-imports {BASE})\n"
    "  (forall (x) (if (B x) (Base x))))"
)
BASE_TEXT = f"(cl-text {BASE}\n  (forall (x) (if (Base x) (Thing x))))"

CLOSURE = {ROOT: ROOT_TEXT, A: A_TEXT, B: B_TEXT, BASE: BASE_TEXT}


# --------------------------------------------------------------------------- #
# extract_imports                                                             #
# --------------------------------------------------------------------------- #

class TestExtractImports:
    def test_finds_all_in_order(self):
        assert extract_imports(ROOT_TEXT) == [A, B]

    def test_none_when_absent(self):
        assert extract_imports("(forall (x) (P x))") == []

    def test_iri_not_confused_with_comment(self):
        # the // in http:// must not be read as a comment delimiter
        assert extract_imports(f"(cl-imports {BASE})") == [BASE]


# --------------------------------------------------------------------------- #
# Closure walk                                                                #
# --------------------------------------------------------------------------- #

class TestClosureWalk:
    def test_diamond_dedupes_base(self):
        closure = resolve_from_text(ROOT_TEXT, MappingResolver(CLOSURE), root_iri=ROOT)
        assert closure.is_complete
        # root + a + b + base — base reached via both a and b, included once
        assert closure.resolved_iris == [ROOT, A, B, BASE]
        assert closure.combined_clif.count(f";; ===== {BASE} =====") == 1

    def test_combined_carries_every_axiom(self):
        closure = resolve_from_text(ROOT_TEXT, MappingResolver(CLOSURE), root_iri=ROOT)
        for token in ("Root", "(A x)", "(B x)", "Base", "Thing"):
            assert token in closure.combined_clif

    def test_root_text_used_verbatim_not_refetched(self):
        # root_iri is NOT in the resolver; the supplied text is the root
        closure = resolve_from_text(
            ROOT_TEXT, MappingResolver({A: A_TEXT, B: B_TEXT, BASE: BASE_TEXT}),
            root_iri=ROOT)
        assert closure.is_complete
        assert closure.resolved_iris[0] == ROOT

    def test_missing_module_reported_not_dropped(self):
        partial = dict(CLOSURE)
        del partial[BASE]
        closure = resolve_from_text(ROOT_TEXT, MappingResolver(partial), root_iri=ROOT)
        assert not closure.is_complete
        assert closure.unresolved == [BASE]
        # the gap is recorded honestly in the assembled source
        assert f"UNRESOLVED: {BASE}" in closure.combined_clif
        # everything that DID resolve is still present
        assert {ROOT, A, B} == set(closure.resolved_iris)

    def test_cycle_is_safe(self):
        # base imports root → a cycle; the walk must terminate, each module once
        cyclic = dict(CLOSURE)
        cyclic[BASE] = f"(cl-text {BASE}\n  (cl-imports {ROOT})\n  (forall (x) (Base x)))"
        closure = resolve_from_text(ROOT_TEXT, MappingResolver(cyclic), root_iri=ROOT)
        assert closure.resolved_iris == [ROOT, A, B, BASE]

    def test_resolve_from_iri_fetches_root_too(self):
        closure = resolve_from_iri(ROOT, MappingResolver(CLOSURE))
        assert closure.is_complete
        assert closure.resolved_iris == [ROOT, A, B, BASE]

    def test_unresolvable_root_yields_empty_closure(self):
        closure = resolve_from_iri(ROOT, MappingResolver({}))
        assert closure.modules == []
        assert closure.unresolved == [ROOT]

    def test_summary_mentions_counts(self):
        closure = resolve_from_text(ROOT_TEXT, MappingResolver(CLOSURE), root_iri=ROOT)
        assert "4 module" in closure.summary


# --------------------------------------------------------------------------- #
# Directory / Caching / Chain resolvers                                       #
# --------------------------------------------------------------------------- #

class TestDirectoryResolver:
    def test_maps_iri_path_under_base(self, tmp_path):
        (tmp_path / "demo").mkdir()
        (tmp_path / "demo" / "base.clif").write_text(BASE_TEXT, encoding="utf-8")
        r = DirectoryResolver(tmp_path)
        assert r.resolve(BASE) == BASE_TEXT

    def test_miss_returns_none(self, tmp_path):
        assert DirectoryResolver(tmp_path).resolve(BASE) is None

    def test_foreign_prefix_returns_none(self, tmp_path):
        assert DirectoryResolver(tmp_path).resolve("http://other.org/x.clif") is None


class TestCachingResolver:
    def test_caches_remote_to_disk(self, tmp_path):
        remote = MappingResolver(CLOSURE)
        caching = CachingResolver(remote, tmp_path)
        # first hit fetches from remote and writes a local mirror
        assert caching.resolve(BASE) == BASE_TEXT
        cached = tmp_path / "demo" / "base.clif"
        assert cached.is_file()
        assert cached.read_text(encoding="utf-8") == BASE_TEXT
        # a now-empty remote still serves the module from cache (offline replay)
        offline = CachingResolver(MappingResolver({}), tmp_path)
        assert offline.resolve(BASE) == BASE_TEXT


class TestChainResolver:
    def test_first_hit_wins(self, tmp_path):
        local = DirectoryResolver(tmp_path)  # empty
        chain = ChainResolver(local, MappingResolver(CLOSURE))
        assert chain.resolve(BASE) == BASE_TEXT

    def test_none_when_all_miss(self, tmp_path):
        chain = ChainResolver(DirectoryResolver(tmp_path), MappingResolver({}))
        assert chain.resolve(BASE) is None


# --------------------------------------------------------------------------- #
# End-to-end through the importer                                             #
# --------------------------------------------------------------------------- #

class TestImporterIntegration:
    def test_from_clif_text_resolves_closure(self):
        result = from_clif_text(
            ROOT_TEXT, resolver=MappingResolver(CLOSURE), root_iri=ROOT)
        # every module's axiom crossed into the EGI (4 conditionals → 4 scrolls)
        from egif_generator_dau import generate_egif
        egif = generate_egif(result.egi)
        for token in ("Root", "Base", "Thing"):
            assert token in egif
        assert result.resolved_modules == [ROOT, A, B, BASE]
        assert result.unresolved_imports == []

    def test_without_resolver_imports_are_only_skipped(self):
        # the legacy behaviour: cl-imports are no-ops, so only the root's own
        # axiom crosses — the imported Base/Thing axioms are absent
        from egif_generator_dau import generate_egif
        result = from_clif_text(ROOT_TEXT)
        egif = generate_egif(result.egi)
        assert "Root" in egif
        assert "Thing" not in egif  # base.clif was never pulled in
        assert result.resolved_modules == []

    def test_unresolved_surfaces_on_result(self):
        partial = dict(CLOSURE)
        del partial[BASE]
        result = from_clif_text(
            ROOT_TEXT, resolver=MappingResolver(partial), root_iri=ROOT)
        assert result.unresolved_imports == [BASE]

    def test_from_clif_file_resolves_closure(self, tmp_path):
        root_file = tmp_path / "root.clif"
        root_file.write_text(ROOT_TEXT, encoding="utf-8")
        result = from_clif_file(
            root_file, resolver=MappingResolver(CLOSURE), root_iri=ROOT)
        from egif_generator_dau import generate_egif
        assert "Thing" in generate_egif(result.egi)


# --------------------------------------------------------------------------- #
# Real network (opt-in; skips when COLORE is unreachable)                     #
# --------------------------------------------------------------------------- #

def _colore_reachable() -> bool:
    # Use the resolver's own SSL-aware fetch (the venv Python often lacks a system
    # trust store, so a bare urlopen would falsely report "unreachable").
    return ColoreWebResolver().resolve(COLORE_PREFIX + "between/bet.clif") is not None


@pytest.mark.skipif(not _colore_reachable(),
                    reason="COLORE repository unreachable (offline/CI)")
class TestColoreWebResolverLive:
    def test_density_closure_resolves(self, tmp_path):
        # density → mass/amount + size/spatial_volume → ringoids/field → … (7 modules)
        caching = CachingResolver(ColoreWebResolver(), tmp_path)
        closure = resolve_from_iri(P + "density/density.clif", caching)
        assert closure.is_complete, closure.summary
        assert len(closure.modules) >= 4
        # and the whole closure imports to a real EGI
        result = from_clif_text(closure.combined_clif)
        assert len(result.egi.E) > 0
