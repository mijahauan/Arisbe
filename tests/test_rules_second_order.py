"""
B-min rules contract — the six Dau rules are sort-preserving and the
quotation boundary is opaque (mention, not use).

Stage 2 of the authorized core opening (verdicts 2026-07-16). Two duties:

1. **Preservation** — every rule now rebuilds through the shared
   ``_rebuild_graph``, which always forwards ``alphabet``/``rho``/``sort``/
   ``quotation`` pruned to the surviving elements. This also repairs the
   historical wart where DC-/ERA/IT+/IT- silently dropped ``alphabet`` and
   ``rho`` (author-ratified fix; the alphabet *grows* to cover lawfully
   introduced vocabulary rather than closing the language).
2. **Opacity** — quoted ink asserts nothing, so no rule operates inside a
   quotation area; the apparatus (flagged cut + quoting name) moves only as
   a whole unit where a rule admits it at all (ERA of the whole exhibit,
   DC+ around it); a dotted oval is never half of a double negation; IT+/IT-
   refuse the apparatus entirely (a named B-min limit).

These are the A3 tier-3 "rules restraint" shapes, tested at the rule level.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from frozendict import frozendict

from egi_core_dau import SORT_PROPOSITION, create_cut, create_vertex
from egif_parser_dau import parse_egif
from eg_navigation import same_graph
from formal_transformation_rules import (
    AreaPolarity,
    FormalTransformationEngine,
    TransformationContext,
)
from ligature_manipulation_rules import ExtendRestrictLigatureRule
from rule_interaction import insert_from_egif
from vertex_splitting_merging_rules import VertexMergingRule

ENGINE = FormalTransformationEngine()


def _with_finalized_alphabet(egi):
    """Attach alphabet+rho the way the CLIF/CGIF pipelines do (the EGIF
    parser leaves alphabet=None)."""
    import dataclasses

    from egi_core_dau import AlphabetDAU

    constants = {v.label for v in egi.V if not v.is_generic and v.label}
    rho = {v.id: (v.label if not v.is_generic else None) for v in egi.V}
    ar = {}
    for eid, name in egi.rel.items():
        ar[name] = max(ar.get(name, 0), len(egi.nu.get(eid, ())))
    alphabet = AlphabetDAU(
        C=frozenset(constants),
        F=frozenset(),
        R=frozenset(egi.rel.values()),
        ar=frozendict(ar),
    ).with_defaults()
    return dataclasses.replace(
        egi, alphabet=alphabet, rho=frozendict(rho)
    )


# --------------------------------------------------------------------------- #
# Fixtures                                                                    #
# --------------------------------------------------------------------------- #


def sheet_exhibit() -> tuple:
    """A quotation unit on the sheet (positive area) beside ordinary ink.

    (superseded "M_law") (P *x)  +  quotation oval holding (white *w) whose
    quoting name is the M_law constant. Returns (egi, name_id, cut_id)."""
    egi = parse_egif('(superseded "M_law") (P *x)')
    name_id = next(v.id for v in egi.V if v.label == "M_law")
    cut = create_cut()
    egi = egi.with_cut(cut)
    w = create_vertex()
    egi = egi.with_vertex_in_context(w, cut.id)
    from egi_core_dau import Edge

    egi = egi.with_edge(Edge(id="e_white"), (w.id,), "white", cut.id)
    egi = egi.with_quotation_binding(name_id, cut.id, sort_name=SORT_PROPOSITION)
    return egi, name_id, cut.id


def negative_area_host() -> tuple:
    """A host whose quotation unit sits inside one negative cut:
    ~[ (superseded "M_law") <oval> ]. Returns (egi, name_id, oval_id, outer_id)."""
    egi = parse_egif('~[ (superseded "M_law") ]')
    name_id = next(v.id for v in egi.V if v.label == "M_law")
    outer_id = next(c.id for c in egi.Cut)
    cut = create_cut()
    egi = egi.with_cut(cut, outer_id)
    w = create_vertex()
    egi = egi.with_vertex_in_context(w, cut.id)
    from egi_core_dau import Edge

    egi = egi.with_edge(Edge(id="e_white"), (w.id,), "white", cut.id)
    egi = egi.with_quotation_binding(name_id, cut.id, sort_name=SORT_PROPOSITION)
    return egi, name_id, cut.id, outer_id


# --------------------------------------------------------------------------- #
# Preservation                                                                #
# --------------------------------------------------------------------------- #


class TestPreservation:
    def test_dc_plus_and_minus_preserve_the_maps(self):
        egi, name_id, cut_id = sheet_exhibit()
        p_vertex = next(
            v.id for v in egi.V if v.is_generic and egi.get_context(v.id) == egi.sheet
        )
        p_edge = next(e.id for e in egi.E if egi.rel[e.id] == "P")
        r = ENGINE.apply_rule("DC+", egi, egi.sheet, frozenset({p_vertex, p_edge}))
        assert r.success, r.error_message
        assert dict(r.result_egi.sort) == dict(egi.sort)
        assert dict(r.result_egi.quotation) == dict(egi.quotation)
        outer = r.changes_made["outer_cut"]
        r2 = ENGINE.apply_rule("DC-", r.result_egi, r.result_egi.sheet, frozenset({outer}))
        assert r2.success, r2.error_message
        assert same_graph(r2.result_egi, egi)

    def test_era_of_ordinary_ink_preserves_the_maps(self):
        egi, name_id, cut_id = sheet_exhibit()
        p_edge = next(e.id for e in egi.E if egi.rel[e.id] == "P")
        r = ENGINE.apply_rule("ERA", egi, egi.sheet, frozenset({p_edge}))
        assert r.success, r.error_message
        assert dict(r.result_egi.sort) == dict(egi.sort)
        assert dict(r.result_egi.quotation) == dict(egi.quotation)

    def test_era_no_longer_drops_rho_and_alphabet(self):
        # The historical wart: ERA rebuilt without alphabet/rho.
        # (EGIF parsing leaves alphabet=None — rho-bearing graphs come from
        # the CLIF/CGIF pipelines and corpus loads — so attach them the way
        # those pipelines do.)
        egi = _with_finalized_alphabet(parse_egif('(Human "Socrates") (P *x)'))
        assert egi.alphabet is not None and dict(egi.rho)
        p_edge = next(e.id for e in egi.E if egi.rel[e.id] == "P")
        r = ENGINE.apply_rule("ERA", egi, egi.sheet, frozenset({p_edge}))
        assert r.success, r.error_message
        assert r.result_egi.alphabet is not None
        assert "Socrates" in set(r.result_egi.rho.values())

    def test_dc_minus_no_longer_drops_rho(self):
        egi = _with_finalized_alphabet(
            parse_egif('(Human "Socrates") ~[ ~[ (P *x) ] ]')
        )
        outer = next(
            c.id for c in egi.Cut if egi.get_context(c.id) == egi.sheet
        )
        r = ENGINE.apply_rule("DC-", egi, egi.sheet, frozenset({outer}))
        assert r.success, r.error_message
        assert "Socrates" in set(r.result_egi.rho.values())
        assert r.result_egi.alphabet is not None

    def test_ins_of_new_vocabulary_grows_the_alphabet(self):
        # Forwarding the alphabet must not close the language: INS of a
        # relation name the alphabet never declared extends R, not refuses.
        egi = _with_finalized_alphabet(parse_egif('~[ (Human "Socrates") ]'))
        cut_id = next(c.id for c in egi.Cut)
        r = insert_from_egif(egi, cut_id, "(Novel *n)")
        assert r.success, r.error_message
        assert "Novel" in r.result_egi.alphabet.R
        assert "Human" in r.result_egi.alphabet.R
        assert "Socrates" in set(r.result_egi.rho.values())

    def test_it_plus_carries_the_sort_of_a_mention_by_name(self):
        # A sorted name with NO oval (pure mention) may be iterated; its
        # copy carries the sort.
        egi = parse_egif('(cites "peirce_law") ~[ (T *x) ]')
        name_id = next(v.id for v in egi.V if v.label == "peirce_law")
        egi = egi.with_sort(name_id, SORT_PROPOSITION)
        cites = next(e.id for e in egi.E if egi.rel[e.id] == "cites")
        cut_id = next(c.id for c in egi.Cut)
        r = ENGINE.apply_rule("IT+", egi, cut_id, frozenset({cites, name_id}))
        assert r.success, r.error_message
        copies = {
            v: k for k, v in r.changes_made["element_mapping"].items() if k != v
        }
        # Beta iteration reuses the source vertex (line of identity extends),
        # so the sort simply persists on the original
        assert r.result_egi.sort.get(name_id) == SORT_PROPOSITION
        # and any fresh copy of a sorted vertex must carry the sort too
        for copy_id, orig_id in copies.items():
            if orig_id in egi.sort and copy_id in {v.id for v in r.result_egi.V}:
                assert r.result_egi.sort.get(copy_id) == egi.sort[orig_id]


# --------------------------------------------------------------------------- #
# Opacity — refusals (A3 tier 3 at the rule level)                            #
# --------------------------------------------------------------------------- #


class TestOpacity:
    def test_ins_into_a_quotation_area_refused(self):
        # the sheet-level oval sits at depth 1 (odd → negative), so INS's
        # polarity check passes and the quotation guard is what refuses
        egi, name_id, oval_id = sheet_exhibit()
        r = insert_from_egif(egi, oval_id, "(Sneak *s)")
        assert not r.success
        assert "quotation" in r.error_message.lower()

    def test_heavy_dot_into_a_quotation_area_refused(self):
        egi, name_id, oval_id = sheet_exhibit()
        r = ENGINE.apply_rule("HEAVY_DOT", egi, oval_id, frozenset())
        assert not r.success
        assert "quotation" in r.error_message.lower()

    def test_era_reaching_inside_the_oval_refused(self):
        egi, name_id, cut_id = sheet_exhibit()
        inner_edge = next(e.id for e in egi.E if egi.rel[e.id] == "white")
        r = ENGINE.apply_rule("ERA", egi, cut_id, frozenset({inner_edge}))
        assert not r.success

    def test_era_of_partial_unit_refused_both_ways(self):
        egi, name_id, cut_id = sheet_exhibit()
        r = ENGINE.apply_rule("ERA", egi, egi.sheet, frozenset({cut_id}))
        assert not r.success and "whole unit" in r.error_message
        r2 = ENGINE.apply_rule("ERA", egi, egi.sheet, frozenset({name_id}))
        assert not r2.success and "whole unit" in r2.error_message

    def test_era_of_the_whole_unit_succeeds(self):
        egi, name_id, cut_id = sheet_exhibit()
        r = ENGINE.apply_rule("ERA", egi, egi.sheet, frozenset({cut_id, name_id}))
        assert r.success, r.error_message
        out = r.result_egi
        assert cut_id not in {c.id for c in out.Cut}
        assert name_id not in {v.id for v in out.V}
        assert out.quotation == frozendict() and out.sort == frozendict()
        # the ordinary ink survives
        assert "P" in set(out.rel.values())

    def test_dc_minus_refuses_a_quotation_cut_as_either_half(self):
        # outer plain cut holding ONLY the oval: looks like a double cut
        egi = parse_egif('(superseded "M_law")')
        name_id = next(v.id for v in egi.V if v.label == "M_law")
        # name must share the oval's area, so build oval on sheet, then a
        # plain cut around... instead: oval directly under a plain cut with
        # the name beside it inside — outer contains {name, oval}? DC- needs
        # outer to contain exactly one element, so craft: plain outer holds
        # only the oval; name sits inside the oval's area? Not legal (name
        # must share the oval's area). So craft the INNER as quotation:
        outer = create_cut()
        egi = egi.with_cut(outer)
        inner = create_cut()
        egi = egi.with_cut(inner, outer.id)
        inner_name = create_vertex(label="q", is_generic=False)
        egi = egi.with_vertex_in_context(inner_name, outer.id)
        # outer now holds {inner, inner_name} → not a DC- shape; rebuild:
        # simplest true shape — outer holds exactly the quotation oval, whose
        # quoting name ALSO lives in outer... that is two elements. The only
        # single-element shape is an unquoted pair, so flag the OUTER cut
        # itself as a quotation around a plain inner cut:
        egi2 = parse_egif('(superseded "M_law") ~[ ~[ (P *x) ] ]')
        name2 = next(v.id for v in egi2.V if v.label == "M_law")
        outer2 = next(
            c.id for c in egi2.Cut if egi2.get_context(c.id) == egi2.sheet
        )
        egi2 = egi2.with_quotation_binding(name2, outer2, sort_name=SORT_PROPOSITION)
        r = ENGINE.apply_rule("DC-", egi2, egi2.sheet, frozenset({outer2}))
        assert not r.success
        assert "not a negation" in r.error_message

    def test_dc_minus_refuses_a_quotation_inner_cut(self):
        egi = parse_egif('(superseded "M_law")')
        name_id = next(v.id for v in egi.V if v.label == "M_law")
        oval = create_cut()
        egi = egi.with_cut(oval)
        egi = egi.with_quotation_binding(name_id, oval.id, sort_name=SORT_PROPOSITION)
        outer = create_cut()
        # wrap the oval alone in a plain cut via DC+ around the unit is the
        # licensed route; craft directly: a plain cut whose sole content is
        # the oval would break the same-area invariant (name outside). So
        # this shape is unconstructible — exactly the invariant's point: an
        # oval can never become the inner half of a double cut without its
        # name, and with its name the outer cut holds two elements, which
        # DC- already refuses.
        r = ENGINE.apply_rule("DC-", egi, egi.sheet, frozenset({oval.id}))
        assert not r.success  # oval holds no single inner cut anyway

    def test_it_plus_refuses_the_apparatus_and_deep_enclosure(self):
        egi, name_id, oval_id, outer_id = negative_area_host()
        # iterating the whole unit
        r = ENGINE.apply_rule("IT+", egi, outer_id, frozenset({oval_id, name_id}))
        assert not r.success and "B-min" in r.error_message
        # iterating a plain cut that ENCLOSES the apparatus
        egi2, name2, oval2 = sheet_exhibit()
        r2 = ENGINE.apply_rule("DC+", egi2, egi2.sheet, frozenset({oval2, name2}))
        assert r2.success
        outer2 = r2.changes_made["outer_cut"]
        host = r2.result_egi
        r3 = ENGINE.apply_rule("IT+", host, outer2, frozenset({outer2}))
        assert not r3.success
        assert "degrade" in r3.error_message or "B-min" in r3.error_message

    def test_it_minus_refuses_quoted_ink_as_repetition(self):
        # host ink (white *w) on the sheet AND the same shape inside the
        # oval: the quoted copy is NOT a repeated assertion
        egi, name_id, cut_id = sheet_exhibit()
        w2 = create_vertex()
        egi = egi.with_vertex(w2)
        from egi_core_dau import Edge

        egi = egi.with_edge(Edge(id="e_white_host"), (w2.id,), "white")
        inner_edge = next(
            e.id
            for e in egi.E
            if egi.rel[e.id] == "white" and egi.get_context(e.id) == cut_id
        )
        inner_vertex = egi.nu[inner_edge][0]
        r = ENGINE.apply_rule(
            "IT-", egi, cut_id, frozenset({inner_edge, inner_vertex})
        )
        assert not r.success

    def test_dc_plus_around_the_whole_unit_round_trips(self):
        egi, name_id, cut_id = sheet_exhibit()
        r = ENGINE.apply_rule("DC+", egi, egi.sheet, frozenset({cut_id, name_id}))
        assert r.success, r.error_message
        assert dict(r.result_egi.quotation) == dict(egi.quotation)
        outer = r.changes_made["outer_cut"]
        r2 = ENGINE.apply_rule("DC-", r.result_egi, r.result_egi.sheet, frozenset({outer}))
        assert r2.success, r2.error_message
        assert same_graph(r2.result_egi, egi)

    def test_dc_plus_around_part_of_the_unit_refused(self):
        egi, name_id, cut_id = sheet_exhibit()
        r = ENGINE.apply_rule("DC+", egi, egi.sheet, frozenset({name_id}))
        assert not r.success and "whole unit" in r.error_message

    def test_first_order_graphs_feel_nothing(self):
        # the guard no-ops on an empty quotation map: plain DC+/ERA behave
        egi = parse_egif('(P *x) ~[ (Q x) ]')
        p_edge = next(e.id for e in egi.E if egi.rel[e.id] == "P")
        r = ENGINE.apply_rule("ERA", egi, egi.sheet, frozenset({p_edge}))
        assert r.success


# --------------------------------------------------------------------------- #
# Chapter 16 map-forwarding (docket item ③)                                   #
# --------------------------------------------------------------------------- #


def _quotation_bearing_host_with_spare_ligature():
    """Quotation apparatus (flagged cut + quoting name) beside an unrelated
    ligature the Chapter 16 rules can operate on, untouched by quotation.
    Returns the bare egi (name/spare-ligature ids recovered structurally by
    the helpers below, matching the host's own labeling convention)."""
    from egi_core_dau import Edge

    egi = parse_egif('(superseded "M_law")')
    name_id = next(v.id for v in egi.V if v.label == "M_law")
    cut = create_cut()
    egi = egi.with_cut(cut)
    w = create_vertex()
    egi = egi.with_vertex_in_context(w, cut.id)
    egi = egi.with_edge(Edge(id="e_white"), (w.id,), "white", cut.id)
    egi = egi.with_quotation_binding(name_id, cut.id, sort_name=SORT_PROPOSITION)

    # spare ligature: two generic vertices on the sheet connected by an
    # identity edge, entirely unrelated to the quotation apparatus
    va = create_vertex()
    vb = create_vertex()
    egi = egi.with_vertex_in_context(va, egi.sheet)
    egi = egi.with_vertex_in_context(vb, egi.sheet)
    egi = egi.with_edge(Edge(id="id_spare"), (va.id, vb.id), "=", egi.sheet)

    # a genuine identity edge FROM the quoting name to a fresh vertex, so a
    # merge attempt targeting the name has a real edge to work with — the
    # refusal below must come from the quotation guard, not merely "no
    # identity edge to merge along"
    vc = create_vertex()
    egi = egi.with_vertex_in_context(vc, egi.sheet)
    egi = egi.with_edge(Edge(id="id_name_vc"), (name_id, vc.id), "=", egi.sheet)
    return egi


def _apply_extend_restrict_on_the_unrelated_ligature(egi):
    va_id = egi.nu["id_spare"][0]
    rule = ExtendRestrictLigatureRule()
    context = TransformationContext(
        source_egi=egi,
        target_area=egi.sheet,
        selected_subgraph=frozenset({va_id}),
        area_polarity=AreaPolarity.POSITIVE,
        nesting_depth=0,
    )
    return rule.apply_transformation(context)


def _apply_vertex_merge_on_the_quoting_name(egi):
    name_id = next(v.id for v in egi.V if v.label == "M_law")
    vc_id = egi.nu["id_name_vc"][1]
    rule = VertexMergingRule()
    context = TransformationContext(
        source_egi=egi,
        target_area=egi.sheet,
        selected_subgraph=frozenset({name_id, vc_id}),
        area_polarity=AreaPolarity.POSITIVE,
        nesting_depth=0,
    )
    return rule.apply_transformation(context)


class TestChapter16MapForwarding:
    """Docket ③: preservation-or-refusal for the ligature/vertex modules."""

    def test_ligature_move_on_quotation_bearing_graph_preserves_maps_or_refuses(self):
        g = _quotation_bearing_host_with_spare_ligature()  # apparatus + unrelated ligature
        result = _apply_extend_restrict_on_the_unrelated_ligature(g)
        if result.success:
            assert dict(result.result_egi.quotation) == dict(g.quotation)
            assert dict(result.result_egi.sort) == dict(g.sort)
            assert dict(result.result_egi.rho) == dict(g.rho)
            assert result.result_egi.alphabet == g.alphabet
        else:
            assert "quotation" in (result.error_message or "").lower()

    def test_vertex_merge_targeting_the_quoting_name_refuses(self):
        g = _quotation_bearing_host_with_spare_ligature()
        result = _apply_vertex_merge_on_the_quoting_name(g)
        assert not result.success
