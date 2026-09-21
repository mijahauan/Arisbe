"""Chapter 16 — the ligature rules, as worked textbook cases.

Dau, *Mathematical Logic with Diagrams*, Ch. 16 (PDF page = book page + 10).

The hand-built, citation-carrying complement to the enumerated calculus property
suite, in the manner of ``test_chapter15_formal_calculus``: that suite sweeps tens
of thousands of moves and pins their extent; this one holds the figure from the
book on one screen, with its page number.

It starts with **Lemma 16.2** because that is where the property suite's newest
oracle found a departure, and this file is the readable record of its repair. It
is deliberately *not* ``test_chapter16_17_ligature_soundness_simplified.py``,
which is one of the 63 tests in ``tests/admission_ledger.json`` that cannot fail
(eight of its own are ledgered as validation theatre); repairing that file is a
separate, queued job.
"""

from __future__ import annotations

import pytest

from egif_parser_dau import parse_egif
from ligature_manipulation_rules import LigatureManipulationEngine

ENGINE = LigatureManipulationEngine()


def _only_vertex(egi):
    vs = sorted(v.id for v in egi.V)
    assert len(vs) == 1, f"expected one vertex, got {len(vs)}"
    return vs[0]


def _identity_edges(egi):
    return [e for e in sorted(egi.nu) if egi.rel.get(e) == "="]


def _extend(egi, vertex_id):
    return ENGINE.apply_rule(
        "EXTEND_LIGATURE", egi, egi.sheet, frozenset([vertex_id]))


# --------------------------------------------------------------------------- #
# Lemma 16.2 — Extending or Restricting a Ligature in a Context (p.172)
#
#   "Let a EGI 𝔊 be given with a vertex v. Let V′ be a set of fresh vertices and
#    E′ be a set of fresh edges ... placed in the context ctx(v), and all fresh
#    edges are identity edges between the vertices of {v} ⊍ V′ such that we have
#    vΘv′ for each v′ ∈ V′. Then 𝔊 and 𝔊′ are syntactically equivalent."
#
# The only precondition on the SOURCE is that v be a vertex. Every other clause
# governs what is built.
# --------------------------------------------------------------------------- #

class TestLemma162Extension:
    def test_a_lone_vertex_is_a_ligature_of_one_and_may_be_extended(self):
        """The repair of 2026-09-21, and the case that used to be refused.

        `ExtendRestrictLigatureRule` demanded that the anchor already carry an
        identity edge — "Selected vertex must be on an existing ligature" —
        declining half of an equivalence rule on 524 moves in the default
        calculus mode and 6,538 at exhaustive bounds. Dau requires no such
        thing: a vertex standing alone is a ligature of one.
        """
        egi = parse_egif('(P *x)')
        v = _only_vertex(egi)
        assert _identity_edges(egi) == [], "the fixture must have no ligature yet"

        result = _extend(egi, v)

        assert result.success, result.error_message
        after = result.result_egi
        assert len(_identity_edges(after)) > 0, "no identity edge was added"
        assert len(after.V) > len(egi.V), "no fresh vertex was added"

    def test_the_fresh_material_lands_in_the_anchors_context(self):
        """"...placed in the context ctx(v)" (p.172) — including inside a cut."""
        egi = parse_egif('~[ (P *x) ]')
        v = _only_vertex(egi)
        cut = sorted(c.id for c in egi.Cut)[0]
        assert egi.get_context(v) == cut

        after = _extend(egi, v).result_egi

        fresh_v = {x.id for x in after.V} - {x.id for x in egi.V}
        fresh_e = set(_identity_edges(after)) - set(_identity_edges(egi))
        assert fresh_v and fresh_e
        for x in fresh_v | fresh_e:
            assert after.get_context(x) == cut, (
                f"{x} landed in {after.get_context(x)}, not ctx(v)={cut}")

    def test_every_fresh_edge_is_an_identity_edge(self):
        """"...all fresh edges are identity edges" (p.172)."""
        egi = parse_egif('(P *x)')
        after = _extend(egi, _only_vertex(egi)).result_egi
        fresh = {e for e in after.nu} - set(egi.nu)
        assert fresh
        assert all(after.rel.get(e) == "=" for e in fresh), (
            {e: after.rel.get(e) for e in fresh})

    def test_the_anchor_and_its_own_ink_survive(self):
        """Extension adds; it does not disturb what was already scribed."""
        egi = parse_egif('(P *x)')
        v = _only_vertex(egi)
        after = _extend(egi, v).result_egi
        assert v in {x.id for x in after.V}
        assert {after.get_relation_name(e) for e in after.nu
                if after.rel.get(e) != "="} == {"P"}

    def test_an_already_ligatured_vertex_still_extends(self):
        """The case that always worked keeps working — the fix removed a
        precondition, it did not swap one restriction for another."""
        egi = parse_egif('*x *y (= x y) (P x)')
        before = len(_identity_edges(egi))
        v = sorted(x.id for x in egi.V)[0]
        result = _extend(egi, v)
        assert result.success, result.error_message
        assert len(_identity_edges(result.result_egi)) > before

    def test_extension_needs_a_vertex_not_an_edge(self):
        """Lemma 16.2 extends at a *vertex*; the refusal that remains correct."""
        egi = parse_egif('(P *x)')
        edge = sorted(egi.nu)[0]
        result = ENGINE.apply_rule(
            "EXTEND_LIGATURE", egi, egi.sheet, frozenset([edge]))
        assert result.success is False
        assert "vertex" in result.error_message.lower()

    def test_extension_needs_exactly_one_anchor(self):
        egi = parse_egif('*x *y (= x y) (P x)')
        both = frozenset(x.id for x in egi.V)
        result = ENGINE.apply_rule("EXTEND_LIGATURE", egi, egi.sheet, both)
        assert result.success is False
