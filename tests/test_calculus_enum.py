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
