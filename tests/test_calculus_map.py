"""The calculus map — which modules are the calculus, and what pins each one.

**Why this replaces "protected core" (2026-09-21, the author's ruling.)**

``tools/core_protection_system.py`` names 14 modules and says they "cannot be
modified without authorization". That sentence was never true in the sense it
invites. The mechanism is a commit-time speed bump in a local git hook: absent on
a fresh clone, invisible to CI, and bypassed by ``--no-verify`` — which the
project's own documented workflow uses on every commit, because the hook fails on
a missing ``python`` alias. **No test referenced it at all**, so the claim that
those modules are protected was itself unmeasured, which is the exact shape this
arc exists to find.

Worse, the label did the work that checking should have done. The one-day 2025
deposit of tests that cannot fail reached *into* that set
(``test_chapter15_formal_calculus``, ``test_egi_core_comprehensive``), and being
**named** core shielded it from scrutiny rather than subjecting it to any. The
boundary is also drawn wrong in both directions: a core Dau property — a line's
area is its quantification — lived entirely *outside* the set in three copies,
while ``has_dominating_nodes`` sat **inverted inside** it and nothing caught it.

So the two jobs that file conflates are separated here:

1. **The map** — "these modules are the calculus" — is genuinely useful and is
   kept, below. It is documentation, not a guarantee.
2. **The attestation** — a module earns its place because a **named suite pins
   its contract**, and that suite is itself admissible (it can fail; see
   ``tests/admission_ledger.json``). That is a test, and it is this file.

The **pause** — confirm with the author before changing the calculus — stays, and
stays a *convention*. It works on a careful agent and does nothing against a
careless one, which is the honest description. Calling it protection is how it
became a substitute for checking.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
TESTS = REPO / "tests"
PROTECTION_TOOL = REPO / "tools" / "core_protection_system.py"
ADMISSION_LEDGER = TESTS / "admission_ledger.json"


# --------------------------------------------------------------------------- #
# The map: module -> (suites that pin its contract, what they pin)
#
# A suite earns a place here only if it exercises the module DIRECTLY. Being
# reached transitively is not attestation: it means some other module's tests
# happen to run this code, and they will not notice when its own contract
# changes.
# --------------------------------------------------------------------------- #

CALCULUS_MAP: dict[str, tuple[tuple[str, ...], str]] = {
    # The data model and its IO
    "egi_core_dau.py": (
        ("test_second_order_core.py", "test_calculus_structure.py"),
        "the immutable EGI, its builders and B-min maps; Def 12.5 enforced at "
        "construction, and has_dominating_nodes held to Dau p.125",
    ),
    "egi_io.py": (
        ("test_second_order_conservativity.py",),
        "to_dict/from_dict round trips, byte-identical re-save corpus-wide",
    ),
    "hierarchical_index.py": ((), ""),          # unattested — see the test below
    # Diachronic state
    "universe_of_discourse.py": (
        ("test_universe_of_discourse.py",),
        "the UoD entity: synchronic EGI plus diachronic history",
    ),
    "egi_transformation_history.py": (
        ("test_egi_transformation_history.py",),
        "the branching DAG of states and transformations",
    ),
    # The rules and the stepwise protocol
    "formal_transformation_rules.py": (
        ("test_calculus_soundness.py", "test_chapter15_formal_calculus.py",
         "test_rules_second_order.py"),
        "the six Dau rules: soundness over every structure, the worked textbook "
        "case per rule, and B-min opacity",
    ),
    "rule_interaction.py": (
        ("test_rule_interaction.py",),
        "the headless stepwise protocol for every rule",
    ),
    # Beta-aware validation and matching
    "subgraph_closure_validator.py": (
        ("test_subgraph_closure_validation.py",),
        "closure validation, including the Beta free-vertex reading",
    ),
    "graph_isomorphism_engine.py": (
        ("test_graph_isomorphism_engine.py",),
        "VF2 matching, the authority behind same_graph",
    ),
    # The correspondence enforcers
    "correspondence_attestation.py": (
        ("test_correspondence_attestation.py",),
        "the runtime check, with an adversarial falsifier per property",
    ),
    "presentation_ops.py": (
        ("test_presentation_ops.py",),
        "the regime-3 algebra: happy and refusal paths for each op",
    ),
    "natural_layout.py": (
        ("test_natural_layout.py",),
        "the coordinate-free projection-independent layer",
    ),
    # Ligature machinery
    "ligature_manipulation_rules.py": (
        ("test_chapter16_ligature_rules.py", "test_calculus_soundness.py"),
        "Lemma 16.2's extension as worked cases, and soundness over the "
        "ligature rules at full extent",
    ),
    "single_object_ligature_detector.py": ((), ""),   # unattested — see below
}

# Modules on the map that NO suite exercises directly. Named here rather than
# left to be noticed, in the manner of
# `test_the_unimplemented_dau_rules_are_exactly_these`: a gap that is counted is
# a gap someone can close; a gap that is merely absent is one nobody can see.
#
# Both are reached only transitively — `hierarchical_index` through
# `egi_core_dau` (which imports it), `single_object_ligature_detector` through
# `chapter17_soundness_evaluation`. So their code runs, and their *contracts* are
# pinned by nothing.
UNATTESTED = frozenset({
    "hierarchical_index.py",
    "single_object_ligature_detector.py",
})


def _tool_modules() -> frozenset[str]:
    """The set `tools/core_protection_system.py` actually carries."""
    src = PROTECTION_TOOL.read_text(encoding="utf-8")
    m = re.search(r"self\.protected_modules = \{(.*?)\n        \}", src, re.S)
    assert m, "could not find protected_modules in the protection tool"
    return frozenset(re.findall(r"'([A-Za-z0-9_]+\.py)'", m.group(1)))


def test_the_map_and_the_tool_name_the_same_modules():
    """Two lists of the calculus would drift, and the drift would be silent."""
    assert frozenset(CALCULUS_MAP) == _tool_modules()


def test_every_attested_module_names_a_suite_that_exists():
    missing = []
    for module, (suites, _what) in CALCULUS_MAP.items():
        if module in UNATTESTED:
            continue
        assert suites, f"{module} claims attestation but names no suite"
        for suite in suites:
            if not (TESTS / suite).exists():
                missing.append(f"{module} -> {suite}")
    assert not missing, f"named suites that do not exist: {missing}"


def test_every_attested_module_says_what_its_suite_pins():
    """A suite name alone is not attestation; the claim has to be stated."""
    for module, (suites, what) in CALCULUS_MAP.items():
        if module in UNATTESTED:
            continue
        assert what.strip(), f"{module} names {suites} but not what they pin"


def _imported_names(text: str) -> set:
    """Every module name ``text`` actually imports, read from its AST.

    This was a regex over the source text until 2026-09-21, and it counted a
    mention in a comment, a docstring or a string literal as an import — all
    four of these passed::

        # from egi_core_dau import Foo
        \"\"\"see: import natural_layout for details\"\"\"
        #import presentation_ops
        msg = "import egi_core_dau to fix"

    which made "the suite reaches the module" satisfiable by *talking about*
    reaching it. Clause 3 of the admission gate is the reason that is no longer
    acceptable: the check is the evidence for an attestation, and evidence that
    a comment can forge is not evidence. Parsing means only real import
    statements count. (Rewriting it changed no verdict on any of the 16 current
    module→suite pairs — it closes what the check would let through, not what
    is in the tree today.)

    Both spellings are collected. ``from src.X import`` is the non-conforming
    form — CLAUDE.md's stated pattern is ``from X import`` — but several older
    suites use it and an import is an import. Recorded rather than silently
    accepted: see ``test_the_suites_that_use_the_non_conforming_src_prefix``.
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:  # a suite that will not parse imports nothing
        return set()

    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            names.add(node.module)
    # "src.egi_core_dau" also attests "egi_core_dau"
    return names | {n[len("src."):] for n in names if n.startswith("src.")}


def _imports(text: str, stem: str) -> bool:
    """Does ``text`` import ``stem``? (See ``_imported_names``.)"""
    return stem in _imported_names(text)


def _tests_local_modules(text: str) -> list[str]:
    """Sibling modules under tests/ that this file imports — the suite's own
    adapters, e.g. ``calculus_apply``."""
    return sorted(n for n in _imported_names(text) if (TESTS / f"{n}.py").exists())


def test_each_suite_actually_exercises_the_module_it_attests():
    """Attestation means the suite reaches the module on purpose.

    Directly, or through one of its own ``tests/`` adapters — the calculus suite
    deliberately routes every engine call through ``calculus_apply`` so that
    ``calculus_rules.legal()`` can stay engine-free, and that indirection is the
    design, not an accident. What does NOT count is reaching the module because
    some unrelated module happens to import it; that is how a contract goes
    unpinned while its code still runs.
    """
    wrong = []
    for module, (suites, _what) in CALCULUS_MAP.items():
        if module in UNATTESTED:
            continue
        stem = module[:-3]
        for suite in suites:
            text = (TESTS / suite).read_text(encoding="utf-8")
            if _imports(text, stem):
                continue
            via = [m for m in _tests_local_modules(text)
                   if _imports((TESTS / f"{m}.py").read_text(encoding="utf-8"), stem)]
            if not via:
                wrong.append(f"{suite} does not reach {stem}")
    assert not wrong, wrong


def test_the_suites_that_use_the_non_conforming_src_prefix():
    """CLAUDE.md: "Import pattern: ``from module_name import Foo`` (not
    ``from src.module_name``)". Two attesting suites predate that convention.

    Counted rather than tidied in passing: the fix is mechanical, but changing
    imports in a core-gate suite is its own change with its own verification, and
    an unexplained edit buried in another arc is how drift starts.
    """
    offenders = sorted({
        suite for _m, (suites, _w) in CALCULUS_MAP.items() for suite in suites
        if re.search(r"from\s+src\.", (TESTS / suite).read_text(encoding="utf-8"))
    })
    assert offenders == ["test_graph_isomorphism_engine.py"], offenders


def test_no_attesting_suite_is_itself_inadmissible():
    """A suite that cannot fail attests nothing.

    This is the join between the two halves of the gate: clause 1 (a test must
    be able to fail) applied to the suites the calculus map leans on. When the
    map was written, `test_chapter15_formal_calculus` had just been rewritten for
    exactly this reason — all nine of its tests were inadmissible, and it was
    attesting the six transformation rules.
    """
    ledger = json.loads(ADMISSION_LEDGER.read_text(encoding="utf-8"))["entries"]
    inadmissible_files = {Path(v["path"]).name for v in ledger.values()}
    guilty = []
    for module, (suites, _what) in CALCULUS_MAP.items():
        for suite in suites:
            if suite in inadmissible_files:
                guilty.append(f"{module} is attested by {suite}, which is in the "
                              f"admission ledger — it cannot fail")
    assert not guilty, guilty


def test_the_unattested_modules_are_exactly_these():
    """The honest gap, counted rather than absent.

    Shrink this set by giving the module a suite that pins its contract — not by
    deleting the name.
    """
    declared = {m for m, (suites, _w) in CALCULUS_MAP.items() if not suites}
    assert declared == UNATTESTED


@pytest.mark.parametrize("module", sorted(UNATTESTED))
def test_an_unattested_module_is_still_reachable_from_src(module):
    """If nothing imports it either, it is not load-bearing and does not belong
    on the map at all — the reasoning that dropped two modules in 2026-05."""
    stem = module[:-3]
    pattern = re.compile(rf"\b(?:import\s+{stem}\b|from\s+{stem}\s+import)")
    importers = [
        p.name for p in (REPO / "src").rglob("*.py")
        if p.name != module and pattern.search(p.read_text(encoding="utf-8"))
    ]
    assert importers, (
        f"{module} is on the calculus map, has no suite, and nothing in src/ "
        f"imports it — it is orphaned and should be dropped from the map")
