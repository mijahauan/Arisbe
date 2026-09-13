"""Structure (spec 2026-09-10 §5.2): a rule changes what it licenses, and
nothing else; the result is an EGI; the B-min maps travel with it."""
from dataclasses import replace

import pytest
from frozendict import frozendict

import eg_navigation as nav
from calculus_apply import Outcome, apply_move
from calculus_enum import DEFAULT_BOUNDS, tier_a
from calculus_expected import expected, iterate, maps_carried
from calculus_layers import structure
from calculus_ledger import Failure, assert_extent, check_ledger, ledgered
from calculus_rules import Move
from calculus_run import Record, run
from egif_parser_dau import parse_egif
from tarski import dominating_nodes


def _rec(g, m, result):
    return Record("A", "hand", g, m, "hand|key", Outcome(True, result, ""), True, "")


def test_the_instrument_catches_a_rule_that_does_nothing():
    # The shape of the HEAVY_DOT defect found while planning (a second
    # application reports success and inserts nothing), built by hand so the
    # instrument is tested, not the engine.
    g = parse_egif("~[ (P *x) ]")
    c = next(iter(g.Cut)).id
    label, detail = structure(_rec(g, Move("VERTEX_INS", (), c), g), {})
    assert detail and "licensed change" in detail


def test_the_instrument_catches_a_line_moved_inward():
    g = parse_egif("(P *x) ~[ (Q x) ]")
    bad = parse_egif("~[ (P *x) (Q x) ]")
    p = next(e for e in g.nu if g.rel[e] == "P")
    label, detail = structure(_rec(g, Move("IT+", (p,), next(iter(g.Cut)).id), bad), {})
    assert detail


def test_iterate_reuses_outer_lines():
    g = parse_egif("(P *x) ~[ ]")
    p = next(iter(g.nu))
    h = iterate(g, (p,), next(iter(g.Cut)).id)
    assert nav.same_graph(h, parse_egif("(P *x) ~[ (P x) ]"))


def test_iteration_within_its_context_accepts_both_licensed_forms():
    """Task 7 review: {e1} is not a Def 12.10 subgraph (p.134: V_e ⊆ V′); its
    completion {e1, v1} iterated with W_v = ∅ (Def 15.2, p.166) is the fresh
    copy, and the reuse form is W_v = {v1} followed by a merge (Def 16.6,
    p.175). Both are licensed; anything else is not."""
    g = parse_egif("*x (P x)")
    m = Move("IT+", (next(iter(g.nu)),), g.sheet)
    assert structure(_rec(g, m, parse_egif("*x *y (P x) (P y)")), {})[1] is None
    assert structure(_rec(g, m, parse_egif("*x (P x) (P x)")), {})[1] is None
    assert structure(_rec(g, m, parse_egif("*x *y (P x) (P y) (P y)")), {})[1]


def test_iteration_chooses_reuse_or_fresh_per_vertex():
    """Task 10 (foaf_core): Def 15.2 chooses W_v PER VERTEX (p.166), so
    iterating (R x y) may reuse x's line and copy y fresh, or the reverse.
    Task 7 accepted only all-reused or all-fresh."""
    g = parse_egif("*x *y (R x y)")
    m = Move("IT+", (next(iter(g.nu)),), g.sheet)
    for text in ("*x *y (R x y) (R x y)", "*x *y *z (R x y) (R z y)",
                 "*x *y *z (R x y) (R x z)", "*x *y *z *w (R x y) (R z w)"):
        assert structure(_rec(g, m, parse_egif(text)), {})[1] is None, text
    assert structure(_rec(g, m, parse_egif("*x *y (R x y) (R y x)")), {})[1]


def test_expected_results_carry_the_maps():
    """Task 10: the expected-result builders kept no B-min maps, so on a
    maps-bearing corpus graph every licensed INS/DC+/VERTEX_INS result
    'differed' from the engine's — the suite's defect, not the engine's."""
    from calculus_expected import double_cut
    from egi_core_dau import AlphabetDAU
    from frozendict import frozendict
    from dataclasses import replace
    g = parse_egif('(P "a")')
    v = next(iter(g.V)).id
    g = replace(g, alphabet=AlphabetDAU(C=frozenset({"a"}), R=frozenset({"P"}),
                                        ar=frozendict({"P": 1, "a": 1})),
                rho=frozendict({v: "a"}))
    h = double_cut(g, tuple(g.nu), g.sheet)
    assert h.alphabet == g.alphabet and dict(h.rho) == {v: "a"}


def test_double_cut_of_a_cut_named_with_its_contents():
    """Task 7 review: naming a cut with some of its contents names the cut
    alone (Def 12.10, p.134); the raw selection built an invalid graph."""
    from calculus_expected import double_cut
    g = parse_egif("~[ (P *x) ]")
    c = next(iter(g.Cut)).id
    e, v = next(iter(g.nu)), next(iter(g.V)).id
    alone = double_cut(g, (c,), g.sheet)
    assert nav.same_graph(alone, parse_egif("~[ ~[ ~[ (P *x) ] ] ]"))
    for sel in ((c, e, v), (c, e), (c, v)):
        assert nav.same_graph(double_cut(g, sel, g.sheet), alone)


def test_maps_carried_names_what_was_dropped():
    # Stubs, not graphs: the core validates rho against an alphabet, and the
    # point here is only which attribute comparison names which loss.
    from types import SimpleNamespace as NS
    before = NS(alphabet=NS(R={"P"}), rho={"v1": "a"}, sort={}, quotation={},
                V=[NS(id="v1")], Cut=[])
    after = NS(alphabet=None, rho={}, sort={}, quotation={}, V=[NS(id="v1")], Cut=[])
    assert maps_carried(before, after) == ["alphabet dropped", "rho lost for 1 vertex"]
    assert maps_carried(before, before) == []


def _layer(mode):
    lr = run(mode).layers["structure"]
    problems = check_ledger("structure", lr.evaluated_ledgered, lr.failures, mode)
    assert not problems, "\n\n".join(problems)


def test_structure():
    _layer("default")


def _extent(mode):
    """The structure counts, plus how many checked records had a source
    carrying a B-min map (label suffix ``:maps``). Tier A carries none; tier B
    does (14 corpus UoDs' current graphs carry a map: alphabet/rho, and three
    of them a sort, two of those a quotation), and the pin must stay positive
    or the maps clause is untested again (Task 10 ruling)."""
    counts = dict(sorted(run(mode).layers["structure"].counts.items()))
    counts["maps-bearing records"] = sum(v for k, v in counts.items() if k.endswith(":maps"))
    assert counts["maps-bearing records"] > 0, "the maps clause was never exercised"
    return counts



def test_structure_extent():
    assert_extent("default:structure", _extent("default"))


@pytest.mark.exhaustive
def test_structure_exhaustive():
    _layer("exhaustive")


@pytest.mark.exhaustive
def test_structure_extent_exhaustive():
    assert_extent("exhaustive:structure", _extent("exhaustive"))


def test_a_no_op_ligature_move_is_now_a_failure():
    """The defect shape the suite could not see: success that changes nothing."""
    g = parse_egif('(= "a" "b")')
    m = Move("RETRACT_LIGATURE", tuple(sorted(v.id for v in g.V)), g.sheet)
    rec = Record("A", "hand", g, m, "hand|noop", Outcome(True, g, ""), None, "not judged")
    label, detail = structure(rec, {})
    assert label.endswith("egi-only") and detail and "changes nothing" in detail


def test_a_ligature_move_that_drops_a_relation_is_a_failure():
    g = parse_egif('(P "a") (= "a" "b")')
    h = parse_egif('(= "a" "b")')          # the P edge has vanished
    m = Move("MOVE_BRANCHES", tuple(sorted(v.id for v in g.V)), g.sheet)
    rec = Record("A", "hand", g, m, "hand|dropped", Outcome(True, h, ""), None, "not judged")
    assert "relations" in structure(rec, {})[1]


def test_split_must_add_one_vertex_and_one_identity_edge():
    """A genuine +2/+2 result (not the identical-object stand-in, which would
    also trip 'changes nothing' and leave this clause untested in isolation):
    two fresh vertices and two identity edges where Def 16.6 (p.175) licenses
    exactly one of each."""
    g = parse_egif("(P *x) (Q x)")
    bad = parse_egif("(P *x) (Q x) (= x *y) (= x *z)")
    m = Move("SPLIT_VERTEX", (sorted(v.id for v in g.V)[0],), g.sheet)
    rec = Record("A", "hand", g, m, "hand|split", Outcome(True, bad, ""), None, "not judged")
    assert "+1 vertex" in structure(rec, {})[1]


def test_a_real_retraction_passes_its_postconditions():
    """`(= "a" "b")` retracted to one vertex: fewer vertices, no identity edge
    left, and the non-identity relations untouched (there are none)."""
    g = parse_egif('(= "a" "b")')
    h = parse_egif('"a"')
    m = Move("RETRACT_LIGATURE", tuple(sorted(v.id for v in g.V)), g.sheet)
    rec = Record("A", "hand", g, m, "hand|real", Outcome(True, h, ""), None, "not judged")
    assert structure(rec, {})[1] is None


def test_rearrange_ligature_may_choose_the_same_shape():
    """Def 16.4 (p.174) replaces a ligature (W,F) with a FRESH (W',F') that
    realizes the same partition; Cor 16.5 (p.175) says only that the result is
    syntactically equivalent, never that F' differs from F. With a 2-vertex
    ligature there is exactly one tree connecting them, so a genuine
    rearrangement is necessarily isomorphic to the source — licensed, not a
    no-op defect. Pinned to the engine's own output (a fresh edge id), the
    live instance found in Step 5 (A|813a0c4dfed7030b#0|REARRANGE_LIGATURE|...),
    not the identical-object stand-in."""
    g = parse_egif('(= "a" "b")')
    v1, v2 = sorted(v.id for v in g.V)
    m = Move("REARRANGE_LIGATURE", (v1, v2), g.sheet)
    outcome = apply_move(g, m)
    assert outcome.applied
    rec = Record("A", "hand", g, m, "hand|rearrange-same-shape", outcome, None, "not judged")
    assert structure(rec, {})[1] is None


def test_rearrange_ligature_reshape_preserves_partition_and_hooks():
    """A genuine 3-vertex reshape (beyond the 2-vertex degenerate case above):
    the real engine's own output on a path ligature carrying a hook, checked
    against Def 16.4 (p.174) / Cor 16.5 (p.175) independently of the engine's
    own partition self-check (ligature_manipulation_rules.py).

    A CONSTANT path, selected by label: rearrangement adds and removes no
    vertex, so Def 24.10's genericity condition (p.270) does not reach it —
    Def 24.9 (p.269) lets a ligature mix generic and constant vertices."""
    g = parse_egif('(P "a") (= "a" "b") (= "b" "c")')
    labels = {v.label: v.id for v in g.V}
    m = Move("REARRANGE_LIGATURE", (labels["a"], labels["b"]), g.sheet)
    outcome = apply_move(g, m)
    assert outcome.applied
    rec = Record("A", "hand", g, m, "hand|rearrange-reshape", outcome, None, "not judged")
    assert structure(rec, {})[1] is None


def test_rearrange_ligature_split_partition_is_reported():
    """Cor 16.5 (p.175): a rearranged ligature must 'keep connected' — the
    same co-denotation partition must survive. Built by hand: the b-c
    identity edge of an a-b-c ligature silently dropped, splitting one
    3-vertex ligature into {a,b} and {c}."""
    g = parse_egif('(= "a" "b") (= "b" "c")')
    labels = {v.label: v.id for v in g.V}
    a, b, c = labels["a"], labels["b"], labels["c"]
    drop = next(e for e in g.nu if g.rel[e] == "=" and set(g.nu[e]) == {b, c})
    new_area = dict(g.area)
    new_area[g.sheet] = frozenset(new_area[g.sheet] - {drop})
    h = replace(g, E=frozenset(e for e in g.E if e.id != drop),
                nu=frozendict({e: v for e, v in g.nu.items() if e != drop}),
                rel=frozendict({e: r for e, r in g.rel.items() if e != drop}),
                area=frozendict(new_area))
    m = Move("REARRANGE_LIGATURE", (a, b), g.sheet)
    rec = Record("A", "hand", g, m, "hand|rearrange-split", Outcome(True, h, ""), None, "not judged")
    detail = structure(rec, {})[1]
    assert detail and "partition" in detail


def test_core_dominating_nodes_check_agrees_with_dau():
    """Def 12.5 is part of what an EGI is. The core's has_dominating_nodes was
    found inverted while planning; its disagreements are ledgered here."""
    known = ledgered("core-dominating")
    failures, evaluated = [], set()
    for gname, g in tier_a(DEFAULT_BOUNDS).graphs:
        key = f"A|{gname}|graph"
        if key in known:
            evaluated.add(key)
        if g.has_dominating_nodes() != dominating_nodes(g):
            failures.append(Failure("core-dominating", key,
                                    f"core says {g.has_dominating_nodes()}, Def 12.5 says {dominating_nodes(g)}"))
    problems = check_ledger("core-dominating", evaluated, failures)
    assert not problems, "\n\n".join(problems)


def test_the_core_check_now_agrees_with_dau():
    """Def 12.5 (p.125): ctx(e) <= ctx(v). The helper tested the relation
    backwards and passed any edge on the sheet."""
    from frozendict import frozendict
    from egi_core_dau import Cut, Edge, RelationalGraphWithCuts, Vertex
    lawful = parse_egif("[*x] ~[ (Q x) ]")
    assert lawful.has_dominating_nodes()
    unlawful = RelationalGraphWithCuts(
        V=frozenset({Vertex("v1")}), E=frozenset({Edge("e1")}),
        nu=frozendict({"e1": ("v1",)}), sheet="S", Cut=frozenset({Cut("c1")}),
        area=frozendict({"S": frozenset({"e1", "c1"}), "c1": frozenset({"v1"})}),
        rel=frozendict({"e1": "P"}))
    assert not unlawful.has_dominating_nodes()


def test_a_lawful_hook_move_is_accepted():
    """Def 12.9 (p.128): a hook may be replaced by a vertex whose context
    encloses the edge's. The inverted helper refused exactly this."""
    g = parse_egif("[*x] ~[ [*y] (Q y) ]")
    outer = next(v.id for v in g.V if g.get_context(v.id) == g.sheet)
    edge = next(iter(g.E)).id
    moved = g.replace_vertex_on_hook(edge, 1, outer)
    assert moved.nu[edge] == (outer,)
