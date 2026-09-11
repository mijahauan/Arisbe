"""Tier-A enumeration: built directly, de-duplicated up to isomorphism, shape-complete.

Spec 2026-09-10 §3.1. The old EGIF strategy never offered an empty cut or a
zero-arity relation; these tests make the enumerator prove it offers every
shape the calculus must meet, and that it counts what it discarded.
"""
import eg_navigation as nav
from calculus_enum import (
    DEFAULT_BOUNDS, REQUIRED_SHAPES, Bounds, dedupe, graph_key, lca,
    line_above_uses, shapes, tier_a,
)
from egif_parser_dau import parse_egif


def test_every_required_shape_occurs_in_the_default_slice():
    report = tier_a(DEFAULT_BOUNDS)
    seen = set()
    for _, g in report.graphs:
        seen |= shapes(g)
    assert REQUIRED_SHAPES <= seen, f"missing shapes: {sorted(REQUIRED_SHAPES - seen)}"


def test_no_two_kept_graphs_are_isomorphic():
    report = tier_a(Bounds(max_cuts=1, max_edges=1, max_generics=1,
                           constants=("a",), max_constant_spots=1, max_elements=3,
                           relations=(("P", 1),)))
    gs = [g for _, g in report.graphs]
    for i in range(len(gs)):
        for j in range(i + 1, len(gs)):
            assert not nav.same_graph(gs[i], gs[j])


def test_dedupe_merges_isomorphic_graphs_with_different_ids():
    a = parse_egif("(P *x) ~[ (P x) ]")
    b = parse_egif("(P *y) ~[ (P y) ]")
    kept, dups, key_only = dedupe([("a", a), ("b", b)])
    assert (len(kept), dups, key_only) == (1, 1, 0)
    assert graph_key(a) == graph_key(b)


def test_counts_add_up():
    r = tier_a(DEFAULT_BOUNDS)
    assert r.built == r.refused_by_core + r.duplicates + len(r.graphs)


def test_every_kept_graph_has_dominating_nodes():
    # Dau Def 12.5 is part of what an EGI is (Def 12.7); the enumerator must
    # never build a non-EGI, since the core would not refuse one.
    from tarski import dominating_nodes
    assert all(dominating_nodes(g) for _, g in tier_a(DEFAULT_BOUNDS).graphs)


def test_line_above_uses_is_detected():
    g = parse_egif("[*x] ~[ (P x) ]")
    v = next(iter(g.V)).id
    assert line_above_uses(g, v)
    h = parse_egif("~[ (P *x) ]")
    assert not line_above_uses(h, next(iter(h.V)).id)


def test_lca_of_one_area_is_itself():
    g = parse_egif("~[ (P *x) ]")
    c = next(iter(g.Cut)).id
    assert lca(g, [c]) == c


def test_tier_b_covers_every_uod_and_every_chain_state():
    from calculus_enum import TOMOS, tier_b
    from calculus_ledger import assert_extent
    from tomos_service import TomosService
    svc = TomosService(TOMOS)
    uods = [u["uod_id"] for u in svc.list_uods()]
    states = sum(len(c.states) for c in map(svc.load_chain, uods) if c)
    r = tier_b(include_chains=True)
    assert r.sources == len(uods) + states
    assert r.sources == r.duplicates + len(r.graphs)
    assert tier_b(include_chains=False).sources == len(uods)
    assert_extent("tier_b", r.extent())


def test_every_corpus_graph_is_an_egi():
    """Task 10 ruling: a standing guard. Dau Def 12.7 (p.126) makes dominating
    nodes (Def 12.5, p.125) part of what an EGI is; the core does not enforce
    it and its own check is inverted, so nothing else in the repository would
    catch a stored non-EGI. Every tier-B source — each UoD's current graph and
    every chain state — is held to it; the known violators are ledgered."""
    from calculus_enum import dominating_violations, tier_b_sources
    from calculus_ledger import Failure, assert_extent, check_ledger, ledgered
    from tarski import dominating_nodes
    known = ledgered("corpus-egi")
    failures, evaluated, bad_states = [], set(), 0
    sources = tier_b_sources(include_chains=True)
    for name, g in sources:
        key = f"B|{name}|graph"
        if key in known:
            evaluated.add(key)
        bad = dominating_violations(g)
        assert bool(bad) == (not dominating_nodes(g))
        if bad:
            bad_states += not name.endswith(":current")
            failures.append(Failure("corpus-egi", key, f"not an EGI (Def 12.5): {len(bad)} "
                                    f"edge-vertex pair(s) on {len({v for _, v in bad})} vertex(es)"))
    problems = check_ledger("corpus-egi", evaluated, failures)
    assert not problems, "\n\n".join(problems)
    assert_extent("corpus-egi", {"sources": len(sources), "not_an_egi": len(failures),
                                 "not_an_egi_chain_states": bad_states})
