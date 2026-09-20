"""Chapter 15 — the six transformation rules, as worked textbook cases.

Dau, *Mathematical Logic with Diagrams*, Ch. 14/15 (PDF page = book page + 10).

**Why this file was rewritten (2026-09-20).** Its predecessor could not fail. All
nine of its tests wrapped every check in ``try/except Exception: print(...)``,
and every ``target_area`` it named — ``"sheet_of_assertion"``, ``"cut_area"``,
``"positive_area"`` — was a string that exists in no graph. Run with ``-s`` it
printed

    ✅ DC+ preconditions validation: (False, 'Target area sheet_of_assertion does not exist')
    ⚠️  IT+ subgraph requirements test: 'frozenset' object is not subscriptable

and reported **9 passed**. It even printed ✅ beside a ``False``. It had never
tested Chapter 15, and while probing the real API to rewrite it, the very first
thing that turned up was a live defect it should have caught: engine-level INS
reporting success on an unchanged graph (see ``TestInsertionRule``).

**What this file is, and is not.** It is the *hand-built, citation-carrying*
complement to the enumerated calculus property suite (``tests/calculus_*.py``,
``test_calculus_soundness.py``, ``test_calculus_legal.py``). That suite reads
Dau's preconditions fresh in ``legal()`` and sweeps tens of thousands of moves;
this one holds one readable textbook case per rule, on one screen, with its page
number. The difference is between "we enumerated 30,000 moves" and "here is the
figure from the book". Neither replaces the other.

Every expected value below was **measured against the engine before it was
written down**, never guessed; and no assertion here sits inside a handler that
could swallow it.
"""

from __future__ import annotations

import pytest

from egif_generator_dau import generate_egif
from egif_parser_dau import parse_egif
from formal_transformation_rules import (
    AreaPolarity,
    DeiterationRule,
    DoubleCutErasureRule,
    DoubleCutInsertionRule,
    ErasureRule,
    FormalTransformationEngine,
    HeavyDotInsertionRule,
    InsertionRule,
    IterationRule,
)

ENGINE = FormalTransformationEngine()


# --------------------------------------------------------------------------- #
# helpers — real element ids, never a fictional area name                      #
# --------------------------------------------------------------------------- #

def _only_cut(egi):
    """The single cut of a one-cut graph."""
    cuts = sorted(c.id for c in egi.Cut)
    assert len(cuts) == 1, f"expected exactly one cut, got {len(cuts)}"
    return cuts[0]


def _edges_in(egi, area_id):
    edge_ids = {e.id for e in egi.E}
    return sorted(x for x in egi.area.get(area_id, ()) if x in edge_ids)


def _apply(rule, egi, target_area, selection=frozenset(), **kw):
    return ENGINE.apply_rule(rule, egi, target_area=target_area,
                             selected_subgraph=frozenset(selection), **kw)


# --------------------------------------------------------------------------- #
# The rules answer to their own names (Def 15.2, p.164-166)                    #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("key, cls, name", [
    ("DC+", DoubleCutInsertionRule, "DC+ (Double Cut Insertion)"),
    ("DC-", DoubleCutErasureRule, "DC- (Double Cut Erasure)"),
    ("INS", InsertionRule, "INS (Insertion)"),
    ("ERA", ErasureRule, "ERA (Erasure)"),
    ("IT+", IterationRule, "IT+ (Iteration)"),
    ("IT-", DeiterationRule, "IT- (Deiteration)"),
    ("HEAVY_DOT", HeavyDotInsertionRule, "HEAVY_DOT (Heavy Dot Insertion)"),
])
def test_the_engine_dispatches_each_key_to_its_rule(key, cls, name):
    """The engine's table is the rule set, not a superset or a subset."""
    rule = ENGINE.rules[key]
    assert isinstance(rule, cls)
    assert rule.get_rule_name() == name


def test_a_fictional_target_area_is_refused_not_silently_accepted():
    """The predecessor's whole failure in one test.

    Every area name it used was fictional, so every rule refused, so every
    `if result.success:` body was skipped — and it printed ✅ and passed. The
    refusal itself is correct behaviour and is pinned here so the shape is
    visible rather than merely absent.
    """
    egi = parse_egif('(P "a")')
    result = _apply("DC+", egi, "sheet_of_assertion")
    assert result.success is False
    assert "does not exist" in result.error_message


# --------------------------------------------------------------------------- #
# DC+ / DC-  — the double cut, an equivalence in any context (Def 15.2, p.164) #
# --------------------------------------------------------------------------- #

class TestDoubleCutRules:
    def test_dc_plus_wraps_the_sheet_in_exactly_two_cuts(self):
        egi = parse_egif('(P "a")')
        result = _apply("DC+", egi, egi.sheet)
        assert result.success, result.error_message
        assert len(result.result_egi.Cut) - len(egi.Cut) == 2
        assert generate_egif(result.result_egi) == '~[ ~[ (P "a") ] ]'

    def test_dc_minus_removes_a_double_cut(self):
        egi = parse_egif('~[ ~[ (P "a") ] ]')
        cut_ids = {c.id for c in egi.Cut}
        outer = next(x for x in egi.area[egi.sheet] if x in cut_ids)
        result = _apply("DC-", egi, egi.sheet, {outer})
        assert result.success, result.error_message
        assert generate_egif(result.result_egi) == '(P "a")'

    def test_dc_plus_then_dc_minus_returns_the_original(self):
        """The pair is an equivalence, so the round trip is the identity."""
        egi = parse_egif('(P "a")')
        wrapped = _apply("DC+", egi, egi.sheet)
        assert wrapped.success, wrapped.error_message
        g = wrapped.result_egi
        cut_ids = {c.id for c in g.Cut}
        outer = next(x for x in g.area[g.sheet] if x in cut_ids)
        back = _apply("DC-", g, g.sheet, {outer})
        assert back.success, back.error_message
        assert generate_egif(back.result_egi) == generate_egif(egi)


# --------------------------------------------------------------------------- #
# INS / ERA — polarity is the whole precondition (Def 15.2, p.165)             #
#                                                                              #
# Insertion is weakening under a negation: sound in an ODD (negative) area.     #
# Erasure is weakening outright: sound in an EVEN (positive) area.              #
# --------------------------------------------------------------------------- #

class TestInsertionRule:
    def test_ins_refuses_a_positive_area(self):
        egi = parse_egif('~[ (P "a") ]')
        result = _apply("INS", egi, egi.sheet, insertion_egif='(Q "b")')
        assert result.success is False
        assert "negatively-enclosed" in result.error_message

    def test_ins_inserts_the_given_content_into_a_negative_area(self):
        """The defect this rewrite found.

        The engine's INS took a ``selected_subgraph`` of element ids and only
        ever inserted ids literally prefixed ``"new_vertex_"`` or
        ``"inserted_"``. Every real id fell through, nothing was inserted, and
        it returned ``success=True`` on an unchanged graph — which is what
        ``POST /transform/apply`` did with a user's EGIF. INS now routes through
        ``rule_interaction.insert_from_egif``, the canonical implementation the
        protocol and the game engine already share.
        """
        egi = parse_egif('~[ (Q "b") ]')
        cut = _only_cut(egi)
        result = _apply("INS", egi, cut, insertion_egif='(P "a")')
        assert result.success, result.error_message
        after = result.result_egi
        assert generate_egif(after) != generate_egif(egi), (
            "INS reported success and changed nothing")
        names = {after.get_relation_name(e) for e in _edges_in(after, cut)}
        assert names == {"Q", "P"}, f"expected Q and P inside the cut, got {names}"

    def test_ins_without_content_refuses_rather_than_silently_succeeding(self):
        """A contentless INS is a caller error, and must read as one.

        Reporting success on a no-op is the worse failure: it tells the caller
        the graph changed when it did not.
        """
        egi = parse_egif('~[ (Q "b") ]')
        result = _apply("INS", egi, _only_cut(egi))
        assert result.success is False
        assert "content" in result.error_message.lower()

    def test_ins_refuses_to_insert_into_a_quotation_area(self):
        """B-min opacity: quoted ink is mention, not use — no rule operates there."""
        from quotation_overlay import scribe_quotation

        host = parse_egif('~[ (Q "b") ]')
        quoted, name_vid, oval = scribe_quotation(
            host, "phi", parse_egif('(P "a")'), area_id=_only_cut(host))
        result = _apply("INS", quoted, oval, insertion_egif='(R "c")')
        assert result.success is False
        assert "quotation" in result.error_message.lower()


class TestErasureRule:
    def test_era_erases_from_a_positive_area(self):
        egi = parse_egif('(P "a") (Q "b")')
        target = _edges_in(egi, egi.sheet)[0]
        result = _apply("ERA", egi, egi.sheet, {target})
        assert result.success, result.error_message
        assert len(result.result_egi.E) == len(egi.E) - 1

    def test_era_refuses_a_negative_area(self):
        egi = parse_egif('~[ (P "a") (Q "b") ]')
        cut = _only_cut(egi)
        result = _apply("ERA", egi, cut, {_edges_in(egi, cut)[0]})
        assert result.success is False
        assert "positively-enclosed" in result.error_message


# --------------------------------------------------------------------------- #
# IT+ / IT- — iteration into a deeper context (Def 15.2, p.164-166)            #
# --------------------------------------------------------------------------- #

class TestIterationRules:
    def test_it_plus_copies_a_subgraph_into_a_nested_cut(self):
        egi = parse_egif('(P "a") ~[ (Q "b") ]')
        cut = _only_cut(egi)
        edge = _edges_in(egi, egi.sheet)[0]
        result = _apply("IT+", egi, cut, {edge} | set(egi.nu[edge]))
        assert result.success, result.error_message
        after = result.result_egi
        names = sorted(after.get_relation_name(e) for e in _edges_in(after, cut))
        assert names == ["P", "Q"], f"expected the P copy beside Q, got {names}"
        assert {after.get_relation_name(e)
                for e in _edges_in(after, after.sheet)} == {"P"}, (
            "iteration must leave the original in place")

    def test_it_minus_erases_a_copy_in_a_deeper_context(self):
        egi = parse_egif('(P "a") ~[ (P "a") ]')
        cut = _only_cut(egi)
        inner = _edges_in(egi, cut)[0]
        result = _apply("IT-", egi, cut, {inner})
        assert result.success, result.error_message
        after = result.result_egi
        assert _edges_in(after, cut) == [], "the inner copy should be gone"
        assert {after.get_relation_name(e)
                for e in _edges_in(after, after.sheet)} == {"P"}, (
            "deiteration must leave the original in place")


# --------------------------------------------------------------------------- #
# HEAVY_DOT — an isolated line, negative contexts only                          #
#                                                                              #
# Dau licenses the isolated vertex in arbitrary contexts (Def 24.10, p.270-272);#
# this engine restricts it to negative ones. That is *stricter* than Dau, so it #
# is sound — it refuses some moves he allows. `derived_rules` relies on exactly  #
# this restriction, and it is pinned here rather than left implicit.            #
# --------------------------------------------------------------------------- #

class TestHeavyDotRule:
    def test_heavy_dot_adds_an_isolated_line_in_a_negative_area(self):
        egi = parse_egif('~[ (P "a") ]')
        result = _apply("HEAVY_DOT", egi, _only_cut(egi))
        assert result.success, result.error_message
        assert len(result.result_egi.V) == len(egi.V) + 1

    def test_heavy_dot_refuses_a_positive_area(self):
        egi = parse_egif('~[ (P "a") ]')
        result = _apply("HEAVY_DOT", egi, egi.sheet)
        assert result.success is False
        assert "negatively-enclosed" in result.error_message


# --------------------------------------------------------------------------- #
# Polarity, and composition                                                    #
# --------------------------------------------------------------------------- #

def test_area_polarity_alternates_with_depth():
    """Even depth is positive, odd is negative — the ground of INS/ERA above."""
    egi = parse_egif('~[ ~[ (P "a") ] ]')
    cut_ids = {c.id for c in egi.Cut}
    outer = next(x for x in egi.area[egi.sheet] if x in cut_ids)
    inner = next(x for x in egi.area[outer] if x in cut_ids)

    rule = ENGINE.rules["DC+"]
    assert rule.calculate_area_polarity(egi, egi.sheet) == (AreaPolarity.POSITIVE, 0)
    assert rule.calculate_area_polarity(egi, outer) == (AreaPolarity.NEGATIVE, 1)
    assert rule.calculate_area_polarity(egi, inner) == (AreaPolarity.POSITIVE, 2)


def test_a_sequence_of_rules_composes_and_each_step_is_checked():
    """DC+ then INS into the new negative area — each step asserted, not printed."""
    egi = parse_egif('(P "a")')

    wrapped = _apply("DC+", egi, egi.sheet)
    assert wrapped.success, wrapped.error_message
    g = wrapped.result_egi

    cut_ids = {c.id for c in g.Cut}
    outer = next(x for x in g.area[g.sheet] if x in cut_ids)
    assert ENGINE.rules["INS"].calculate_area_polarity(g, outer)[0] is AreaPolarity.NEGATIVE

    inserted = _apply("INS", g, outer, insertion_egif='(Q "b")')
    assert inserted.success, inserted.error_message
    after = inserted.result_egi
    assert {after.get_relation_name(e) for e in _edges_in(after, outer)} == {"Q"}
