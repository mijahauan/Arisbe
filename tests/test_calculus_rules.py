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
    assert {r.name for r in DAU_RULES if r.direction == "one-way"} == {"ERA", "INS"}


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


def test_ligature_moves_offer_both_orders_and_apply_in_order():
    """Task 10: the ligature engine keeps (or moves from) the FIRST element of
    its selection, and a plain frozenset's order follows the hash seed. The
    suite hands the order over (calculus_apply.InOrder) and offers both."""
    from calculus_apply import InOrder
    g = parse_egif("(= *x *y)")
    a, b = sorted(v.id for v in g.V)
    sels = {m.selection for m in moves("RETRACT_LIGATURE", g, "A") if m.target == g.sheet}
    assert (a, b) in sels and (b, a) in sels
    assert list(InOrder((b, a))) == [b, a] and next(iter(InOrder((a, b)))) == a
    kept = lambda sel: {v.id for v in apply_move(g, Move("RETRACT_LIGATURE", sel, g.sheet)).result.V}  # noqa: E731
    assert kept((a, b)) == {a} and kept((b, a)) == {b}
