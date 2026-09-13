"""The rule table follows Dau, not the engine (spec 2026-09-10 §1a.2).

Every engine entry point must map to a Dau rule, and every Dau rule with no
entry point is named — so a rule the engine grows, or one it lacks, cannot go
unnoticed.
"""
import inspect

import pytest

from calculus_apply import Outcome, apply_move, engine_entry_points
from calculus_rules import (
    DAU_RULES, INS_CATALOGUE, RULES, UNIMPLEMENTED, Move, moves, units,
)
from egif_parser_dau import parse_egif


def test_every_engine_entry_point_is_a_dau_rule_and_vice_versa():
    assert {r.engine for r in DAU_RULES if r.engine} == engine_entry_points()


def test_the_unimplemented_dau_rules_are_exactly_these():
    assert UNIMPLEMENTED == {"ORIENT_IDENTITY", "LIGATURE_VERTEX", "CONSTANT_IDENTITY",
                             "CONSTANT_EXISTENCE", "SEPARATE_CONSTANT"}


def test_the_ins_protocol_cannot_perform_edge_insertion_directly():
    """A recorded fact, not a pass: Dau p.165 defines erasing an edge e from
    ctx(e) with V^(e) := V — the edge goes, its vertices stay — and inserting
    e into c as its inverse, so in a negative context an edge may be inserted
    onto vertices already there: *x ~[ ] -> *x ~[ (P x) ]. The protocol's INS
    takes standalone EGIF only, and ``(P x)`` names a line it cannot see
    ('Undefined variable x'), so the move is refused. INS_EDGE's own entry
    point (below, calculus_rules.py) reaches the same protocol and is refused
    the same way — its candidates are enumerated so the gap is counted as
    INCOMPLETE on every run, not fixed here (that is the engine arc)."""
    g = parse_egif("*x ~[ ]")
    cut = next(iter(g.Cut)).id
    out = apply_move(g, Move("INS", (), cut, "(P x)"))
    assert not out.applied and not out.crashed
    assert "Undefined variable x" in out.message


def test_ins_edge_moves_are_enumerated_and_the_engine_refuses_them():
    from calculus_apply import apply_move
    g = parse_egif("*x ~[ ]")
    ms = [m for m in moves("INS_EDGE", g, "A")]
    assert ms, "INS_EDGE must offer at least one candidate on *x ~[ ]"
    out = apply_move(g, ms[0])
    assert not out.applied and not out.crashed        # counted INCOMPLETE, never a crash


def test_split_merge_module_holds_exactly_two_rules():
    import vertex_splitting_merging_rules as m
    from formal_transformation_rules import FormalTransformationRule
    found = sorted(n for n, c in inspect.getmembers(m, inspect.isclass)
                   if issubclass(c, FormalTransformationRule)
                   and c is not FormalTransformationRule and c.__module__ == m.__name__)
    assert found == ["VertexMergingRule", "VertexSplittingRule"]


def test_every_rule_has_a_direction_and_a_citation():
    for r in DAU_RULES:
        assert r.direction in ("one-way", "equivalence") and r.cite.startswith(("Def", "Lemma"))
    assert {r.name for r in DAU_RULES if r.direction == "one-way"} == {"ERA", "INS", "INS_EDGE"}


@pytest.mark.parametrize("text", INS_CATALOGUE)
def test_ins_catalogue_parses(text):
    parse_egif(text)


def test_tier_a_move_counts_on_a_known_graph():
    g = parse_egif("(P *x) ~[ ]")          # three elements, two areas
    assert len(list(moves("ERA", g, "A"))) == 7
    assert len(list(moves("DC+", g, "A"))) == 8 * 2
    assert len(list(moves("INS", g, "A"))) == 2 * len(INS_CATALOGUE)
    assert len(list(moves("VERTEX_INS", g, "A"))) == 2


def test_units_are_edges_cuts_closed_vertices_and_areas():
    g = parse_egif("(P *x) ~[ (Q x) ]")
    us = units(g)
    assert any(len(u) == 3 for u in us)    # the vertex with both its edges
    assert len(us) == len(set(us))


def test_apply_move_reports_refusal_without_raising():
    g = parse_egif("~[ (P *x) ]")
    e = next(iter(g.E)).id
    out = apply_move(g, Move("ERA", (e,)))
    assert isinstance(out, Outcome) and not out.applied and not out.crashed


def test_apply_move_applies_a_lawful_erasure():
    g = parse_egif("(P *x) (Q x)")
    q = next(e.id for e in g.E if g.rel[e.id] == "Q")
    out = apply_move(g, Move("ERA", (q,)))
    assert out.applied and len(out.result.E) == 1


def test_a_ligature_selection_is_one_move_whatever_order_it_arrives_in():
    """Task 7 retired the suite's InOrder workaround: the engine chooses the
    vertex it keeps (or moves from) by canonical signature, so the order the
    selection is handed over in changes nothing, and the enumerator offers a
    selection once rather than twice."""
    g = parse_egif("[*x] [*y] (= x y) (P x)")
    a, b = sorted(v.id for v in g.V)
    sels = {m.selection for m in moves("RETRACT_LIGATURE", g, "A") if m.target == g.sheet}
    assert (a, b) in sels and (b, a) not in sels
    kept = lambda sel: {v.id for v in apply_move(g, Move("RETRACT_LIGATURE", sel, g.sheet)).result.V}  # noqa: E731
    assert kept((a, b)) == kept((b, a)) and len(kept((a, b))) == 1


def test_retraction_refuses_a_ligature_whose_edge_is_deeper_than_its_vertices():
    """Lemma 16.3 (p.173) requires ctx(w) = c = ctx(f) for every vertex AND
    every identity edge. `*x *y ~[ (= x y) ]` says two things differ; retracting
    it gave `*x ~[ ]`, which is false."""
    from calculus_apply import apply_move
    g = parse_egif("[*x] [*y] ~[ (= x y) ]")
    out = apply_move(g, Move("RETRACT_LIGATURE", tuple(sorted(v.id for v in g.V)), g.sheet))
    assert not out.applied and "same context" in out.message


def test_the_ligature_rules_refuse_constant_vertices():
    """Def 24.10 (p.270-272) states them for generic vertices; joining
    constants is the Constant Identity rule, which requires the same name."""
    from calculus_apply import apply_move
    g = parse_egif('(= "a" "b")')
    out = apply_move(g, Move("RETRACT_LIGATURE", tuple(sorted(v.id for v in g.V)), g.sheet))
    assert not out.applied and "generic" in out.message


def test_merging_refuses_a_constant_vertex_and_still_merges_generic_ones():
    """Def 24.10 (p.270-272) again, at the other entry point: merging erases v2
    (Def 16.6, p.176), and with it the name a constant vertex carries. The
    generic merge is left alone — the condition is about names, not about
    merging."""
    from calculus_apply import apply_move
    g = parse_egif('(= "a" "b")')
    v1, v2 = sorted(v.id for v in g.V)
    e = next(iter(g.nu))
    out = apply_move(g, Move("MERGE_VERTICES", (v1, v2, e)))
    assert not out.applied and "generic" in out.message
    h = parse_egif("(= *x *y) (P x)")
    w1, w2 = h.nu[next(e for e in h.nu if h.rel[e] == "=")]
    ok = apply_move(h, Move("MERGE_VERTICES", (w1, w2, next(e for e in h.nu if h.rel[e] == "="))))
    assert ok.applied and len(ok.result.V) == 1


def test_a_lawful_move_over_a_constant_anchor_applies():
    """Def 24.10 (p.270) restricts genericity to the vertex ADDED or REMOVED:
    "Let v ∈ V be a vertex which is attached to a hook (e,i) … a new GENERIC
    vertex v′ and a new identity-edge between v and v′ is inserted". So a
    constant may anchor an extension, and a generic vertex may be merged INTO
    a constant — the name survives, and the adjudication's own control measures
    that merge as an equivalence. The first form of this condition tested the
    whole selection and refused both: a lawful move blocked."""
    from calculus_apply import apply_move
    g = parse_egif('(= "a" *y) (P y)')
    a = next(v.id for v in g.V if v.label == "a")
    y = next(v.id for v in g.V if v.is_generic)
    join = next(e for e in g.nu if g.rel[e] == "=")

    ext = apply_move(g, Move("EXTEND_LIGATURE", (a,), g.sheet))
    assert ext.applied and not ext.crashed, ext.message
    assert len(ext.result.V) > len(g.V)                 # v′ added, "a" still there
    assert {v.label for v in ext.result.V if v.label} == {"a"}

    merged = apply_move(g, Move("MERGE_VERTICES", (a, y, join)))
    assert merged.applied and not merged.crashed, merged.message
    assert {v.label for v in merged.result.V} == {"a"}  # the name survives


def test_merging_an_unordered_mixed_pair_removes_the_generic_vertex():
    """Which vertex a merge removes must be a function of the graph, and on a
    mixed pair Def 24.10 (p.270) decides it outright: the vertex removed must
    be generic, so the generic one goes and the constant stays.

    This pins the CHOICE, not merely its stability: a rule that deterministically
    removed the constant would pass a stability test and still be wrong. The
    unordered entry point (apply_transformation, which takes its pair from a
    frozenset) is the one under test — it used to apply under PYTHONHASHSEED 3
    and 7 and refuse under 1, 2, 5 and 11 on this very graph."""
    from formal_transformation_rules import AreaPolarity, TransformationContext
    from vertex_splitting_merging_rules import VertexMergingRule
    g = parse_egif('(= "a" *y) (P y)')
    a = next(v.id for v in g.V if v.label == "a")
    y = next(v.id for v in g.V if v.is_generic)
    ctx = TransformationContext(
        source_egi=g, target_area=g.sheet, selected_subgraph=frozenset([a, y]),
        area_polarity=AreaPolarity.POSITIVE, nesting_depth=0,
    )
    res = VertexMergingRule().apply_transformation(ctx)
    assert res.success, res.error_message
    assert {v.label for v in res.result_egi.V} == {"a"}        # the name survives
    assert y not in {v.id for v in res.result_egi.V}           # the generic vertex went
    assert res.changes_made["merged_vertex"] == str(y)
    assert res.changes_made["target_vertex"] == str(a)


def test_a_merge_that_would_erase_the_name_is_still_refused():
    """The other direction of the same move, which the narrowing must keep out:
    merging the constant INTO the generic vertex erases "a", and with it the
    only thing the graph says about that object by name (Def 24.10, p.270 —
    the vertex removed must be generic)."""
    from calculus_apply import apply_move
    g = parse_egif('(= "a" *y) (P y)')
    a = next(v.id for v in g.V if v.label == "a")
    y = next(v.id for v in g.V if v.is_generic)
    join = next(e for e in g.nu if g.rel[e] == "=")
    out = apply_move(g, Move("MERGE_VERTICES", (y, a, join)))
    assert not out.applied and "generic" in out.message


def test_the_survivor_does_not_depend_on_the_hash_seed():
    """Two vertices, both generic, one ligature: whichever survives, the
    choice is a function of the graph (canonical signature), not of the
    process."""
    from calculus_apply import apply_move
    g = parse_egif("[*x] [*y] (= x y) (P x)")
    sel = tuple(sorted(v.id for v in g.V))
    first = apply_move(g, Move("RETRACT_LIGATURE", sel, g.sheet))
    second = apply_move(g, Move("RETRACT_LIGATURE", tuple(reversed(sel)), g.sheet))
    assert first.applied and second.applied
    assert sorted(v.id for v in first.result.V) == sorted(v.id for v in second.result.V)


def test_move_branches_refuses_to_move_the_edge_that_witnesses_the_link():
    """Lemma 16.1 (p.169-171) needs v_aΘv_b to hold in the graph without the
    hook being moved; its proof's deiteration step is otherwise unlicensed.
    Here the identity edge is the only hook v_a carries, so there is no hook
    to move that the lemma licenses."""
    from calculus_apply import apply_move
    g = parse_egif("[*x] [*y] (= x y)")
    out = apply_move(g, Move("MOVE_BRANCHES", tuple(sorted(v.id for v in g.V)), g.sheet))
    assert not out.applied and "witness" in out.message


def test_move_branches_still_moves_a_hook_the_lemma_licenses():
    """The other half of Lemma 16.1 (p.169): the side condition is about the
    ONE hook being moved, not about every edge on v_a. Each vertex here
    carries a relation hook beside the identity edge that joins them, so
    whichever vertex the engine takes as v_a, moving that relation hook
    leaves v_aΘv_b standing — and the lemma licenses it. A condition that
    refused this would block a lawful move, which is the same class of error
    as the unlawful move it is there to stop."""
    from calculus_apply import apply_move
    g = parse_egif("(P *x) (= x *y) (Q y)")
    out = apply_move(g, Move("MOVE_BRANCHES", tuple(sorted(v.id for v in g.V)), g.sheet))
    assert out.applied and not out.crashed, out.message
    # the identity edge still joins the same two vertices: only a hook moved
    join = next(e for e in g.nu if g.rel[e] == "=")
    assert out.result.nu[join] == g.nu[join]
    assert sorted(out.result.rel.values()) == sorted(g.rel.values())


def test_the_engine_refuses_iteration_into_its_own_selection():
    """Dau Def 15.2 (p.164, 166): the destination must satisfy c <= ctx(G0) AND
    c not in Cut0. Without the second half, `~[ ~[ ] ]` (true in every
    structure) becomes `~[ ~[ ~[ ] ] ]` (false in every structure)."""
    from calculus_apply import apply_move
    from tarski import Structure, satisfies
    g = parse_egif("~[ ~[ ] ]")
    inner = next(c.id for c in g.Cut if g.get_context(c.id) != g.sheet)
    out = apply_move(g, Move("IT+", (inner,), inner))
    assert not out.applied and not out.crashed, out.message
    assert satisfies(g, Structure(1, {}, {}))          # the source still holds
