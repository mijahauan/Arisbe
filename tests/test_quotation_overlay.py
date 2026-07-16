"""The quotation overlay — Stage ⓪ of the second-order crossing
(``src/quotation_overlay.py``; docs/CROSSING_DECISION_BRIEFS.md verdicts,
docs/SECOND_ORDER_CORE_OPENING.md §5 step 1).

Pins the production shapes around :mod:`second_order_check`'s law: the mark
round-trips like an annotation; S1 reads the *drawn* enclosure (never a stored
field) and the impredicative-flat refusal bites at the mark level; resolution is
mention, not use (the host is untouched); the three blessed corpus exemplars —
the swan's third tense, ``(forces s φ)``, the peirce_law mention — attest
S1/S2/S4/S5 with the real ELK engine and name S3 as the skip it honestly is;
and the dotted-oval glyph is pure chrome (default output byte-identical,
decoration only when fed, no DTO change).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from eg_navigation import same_graph, vertex_by_label
from egif_generator_dau import generate_egif
from egif_parser_dau import parse_egif
from quotation_overlay import (
    ChainQuotationResolver,
    ChainStepQuotationResolver,
    EGIFQuotationResolver,
    QuotationMark,
    UoDQuotationResolver,
    attest_quotation_mark,
    attest_quotation_mark_trajectory,
    find_cut_matching,
    is_enclosed,
    lift_cut,
    mark_quotation,
    quotation_candidate,
    quotation_horizon,
    quotation_marks_from_list,
    quotation_marks_to_list,
    render_quotation_marks,
    run_quotation_mark,
    run_quotation_mark_trajectory,
)
from second_order_check import SORT_PROPOSITION, SecondOrderViolation
from tomos_service import TomosService

TOMOS_ROOT = Path(__file__).parent.parent / "tomos"

LAW = "~[ (swan *x) ~[ (white x) ] ]"
EXHIBIT = '(superseded "M_swan_law" "Nox")'


def _layout_fn(egi):
    from web_api.services.layout_service import generate_layout

    dto, _svg = generate_layout(egi)
    return dto


@pytest.fixture(scope="module")
def tomos():
    return TomosService(TOMOS_ROOT)


# --------------------------------------------------------------------------- #
# The mark — an overlay record beside the EGI.
# --------------------------------------------------------------------------- #

class TestQuotationMark:
    def test_round_trips_like_an_annotation(self):
        mark = QuotationMark(
            element_id="v_1", target=LAW, sort=SORT_PROPOSITION,
            kind="egif", origin="here", impredicative=None,
            extra={"note": "n"})
        assert QuotationMark.from_dict(mark.to_dict()) == mark
        assert quotation_marks_from_list(
            quotation_marks_to_list([mark])) == [mark]

    def test_defaults_are_mention_shaped(self):
        mark = QuotationMark(element_id="v_1", target=LAW)
        assert mark.warrant == "low"          # a mention is not a truth-claim
        assert mark.sort == SORT_PROPOSITION
        assert mark.impredicative is None     # detection left to the harness

    def test_mark_quotation_refuses_missing_ink_and_dangling_target(self):
        host = parse_egif(EXHIBIT)
        resolver = EGIFQuotationResolver()
        with pytest.raises(ValueError):
            mark_quotation(host, "v_nowhere", LAW, resolver)
        vid = vertex_by_label(host, "M_swan_law")
        with pytest.raises(ValueError):
            mark_quotation(host, vid, "~[ not egif", resolver)


# --------------------------------------------------------------------------- #
# S1 reads the drawing — enclosure computed, never stored.
# --------------------------------------------------------------------------- #

class TestEnclosureOffTheDrawing:
    def test_flat_vs_enclosed(self):
        flat = parse_egif('(names "g")')
        assert is_enclosed(flat, vertex_by_label(flat, "g")) is False
        fenced = parse_egif('~[ (names "g") ]')
        assert is_enclosed(fenced, vertex_by_label(fenced, "g")) is True

    def test_candidate_carries_the_drawn_enclosure(self):
        resolver = EGIFQuotationResolver()
        flat = parse_egif('(names "g")')
        mark = mark_quotation(flat, vertex_by_label(flat, "g"), LAW, resolver)
        assert quotation_candidate(flat, mark, resolver).enclosed is False
        fenced = parse_egif('~[ (names "g") ]')
        mark2 = mark_quotation(fenced, vertex_by_label(fenced, "g"), LAW, resolver)
        assert quotation_candidate(fenced, mark2, resolver).enclosed is True

    def test_impredicative_flat_refused_enclosed_admitted(self):
        """The comprehension floor at the mark level: dragon 9 drawn as a rule."""
        resolver = EGIFQuotationResolver()
        flat = parse_egif('(names "itself")')
        mark = mark_quotation(flat, vertex_by_label(flat, "itself"),
                              '(names "itself")', resolver, impredicative=True)
        with pytest.raises(SecondOrderViolation, match="stratified"):
            attest_quotation_mark(flat, mark, resolver)

        fenced = parse_egif('~[ (names "itself") ]')
        mark2 = mark_quotation(fenced, vertex_by_label(fenced, "itself"),
                               '(names "itself")', resolver, impredicative=True)
        attest_quotation_mark(fenced, mark2, resolver)  # no raise

    def test_direct_self_quote_detected_structurally(self):
        """No explicit override needed: quoted_ground same_graph host → impredicative."""
        resolver = EGIFQuotationResolver()
        host = parse_egif('(names "itself")')
        mark = mark_quotation(host, vertex_by_label(host, "itself"),
                              '(names "itself")', resolver)
        assert quotation_candidate(host, mark, resolver).is_impredicative()
        with pytest.raises(SecondOrderViolation, match="stratified"):
            attest_quotation_mark(host, mark, resolver)


# --------------------------------------------------------------------------- #
# Lifting — the quoted object recovered structurally from a drawn sheet.
# --------------------------------------------------------------------------- #

class TestLifting:
    def test_lift_cut_recovers_the_law(self):
        state = parse_egif(f'(swan "Ciel") (white "Ciel") {LAW}')
        cid = find_cut_matching(state, parse_egif(LAW))
        assert cid is not None
        assert same_graph(lift_cut(state, cid), parse_egif(LAW))

    def test_no_match_is_none_not_an_error(self):
        state = parse_egif('(swan "Ciel")')
        assert find_cut_matching(state, parse_egif(LAW)) is None

    def test_inner_cut_does_not_shadow_the_law(self):
        """The law's own inner cut is a candidate too — it must simply not match."""
        state = parse_egif(LAW)
        cid = find_cut_matching(state, parse_egif(LAW))
        lifted = lift_cut(state, cid)
        assert same_graph(lifted, parse_egif(LAW))


# --------------------------------------------------------------------------- #
# Resolution is mention, not use.
# --------------------------------------------------------------------------- #

class TestMentionNotUse:
    def test_resolving_never_touches_the_host(self):
        host = parse_egif(EXHIBIT)
        before = generate_egif(host)
        resolver = EGIFQuotationResolver()
        mark = mark_quotation(host, vertex_by_label(host, "M_swan_law"),
                              LAW, resolver)
        resolved = resolver.resolve(mark)
        assert same_graph(resolved, parse_egif(LAW))
        assert generate_egif(host) == before          # not one element spliced

    def test_chain_dispatches_by_kind(self, tomos):
        chain = ChainQuotationResolver(
            EGIFQuotationResolver(), UoDQuotationResolver(tomos))
        host = parse_egif('(cites "peirce_law" "Peirce-1885")')
        vid = vertex_by_label(host, "peirce_law")
        by_uod = mark_quotation(host, vid, "peirce_law", chain, kind="uod")
        assert by_uod.kind == "uod"
        resolved = chain.resolve(by_uod)
        assert same_graph(
            resolved,
            parse_egif("~[ ~[ ~[ (P) ~[ (Q) ] ] ~[ (P) ] ] ~[ (P) ] ]"))

    def test_unresolvable_raises_not_silences(self):
        chain = ChainQuotationResolver(EGIFQuotationResolver())
        mark = QuotationMark(element_id="v_1", target="no_such_uod", kind="uod")
        assert chain.can_resolve(mark) is False
        with pytest.raises(ValueError):
            chain.resolve(mark)


# --------------------------------------------------------------------------- #
# The corpus exemplars — the blessed slate, attested as saved.
# --------------------------------------------------------------------------- #

class TestSwanThirdTense:
    """Exemplar (i): the withdrawn law as labeled exhibit."""

    def test_saved_mark_attests_s1_s2_with_real_elk(self, tomos):
        uod = tomos.load_uod("swan_third_tense")
        assert uod is not None, "run tools/build_quotation_exemplars.py"
        marks = quotation_marks_from_list(tomos.load_quotations("swan_third_tense"))
        assert len(marks) == 1
        mark = marks[0]
        resolver = ChainStepQuotationResolver(tomos)
        attest_quotation_mark(uod.current_egi, mark, resolver,
                              layout_fn=_layout_fn,
                              quoted_ground=parse_egif(LAW))

    def test_s3_is_skip_named_never_silently_passed(self, tomos):
        uod = tomos.load_uod("swan_third_tense")
        mark = quotation_marks_from_list(
            tomos.load_quotations("swan_third_tense"))[0]
        report = run_quotation_mark(uod.current_egi, mark,
                                    ChainStepQuotationResolver(tomos),
                                    quoted_ground=parse_egif(LAW))
        assert report.ok
        assert report.read_back_faithful is None
        assert any("S3" in lim for lim in report.honest_limits)

    def test_s5_trajectory_names_where_the_law_stood(self, tomos):
        """Cohen's R_G on the real revision chain: the name resolves exactly
        at s4–s7; every other state is horizon, named, never failed."""
        uod = tomos.load_uod("swan_third_tense")
        mark = quotation_marks_from_list(
            tomos.load_quotations("swan_third_tense"))[0]
        states = tomos.load_chain("dialogue_swan_revision").states
        report = run_quotation_mark_trajectory(uod.current_egi, mark, LAW, states)
        assert report.ok, report.failures
        assert report.checked_states == ["s4", "s5", "s6", "s7"]
        assert report.unresolved_states == ["s0", "s1", "s2", "s3", "s8", "s9"]

    def test_s5_falsifier_a_doctored_state_fails_naming_it(self, tomos):
        """Doctor one state's drawn law and the trajectory must fail *there*."""
        uod = tomos.load_uod("swan_third_tense")
        mark = quotation_marks_from_list(
            tomos.load_quotations("swan_third_tense"))[0]
        states = dict(tomos.load_chain("dialogue_swan_revision").states)
        wrong = "~[ (swan *x) ~[ (black x) ] ]"
        states["s5"] = parse_egif(f'(white "Ciel") {wrong}')
        # the doctored law does not match the shape, so s5 reads as horizon —
        # unless we ask for the *wrong* shape at every state:
        report = run_quotation_mark_trajectory(uod.current_egi, mark, LAW, states)
        assert "s5" in report.unresolved_states  # honest horizon, not a pass

    def test_exhibit_resolves_via_the_withdrawal_record(self, tomos):
        """The quotation's resolver path is the REVISE_M step's own record —
        the withdrawal step names exactly what it withdrew."""
        mark = quotation_marks_from_list(
            tomos.load_quotations("swan_third_tense"))[0]
        assert mark.kind == "chain-step"
        assert mark.target.startswith("dialogue_swan_revision#")
        resolved = ChainStepQuotationResolver(tomos).resolve(mark)
        assert same_graph(resolved, parse_egif(LAW))


class TestForcingForces:
    """Exemplar (ii): (forces s φ) under the Montague rider."""

    def test_three_claims_attest_and_recompute(self, tomos):
        import modal_query as mq

        uod = tomos.load_uod("forcing_forces")
        assert uod is not None, "run tools/build_quotation_exemplars.py"
        marks = quotation_marks_from_list(tomos.load_quotations("forcing_forces"))
        assert len(marks) == 3
        resolver = EGIFQuotationResolver()
        chain = tomos.load_chain("forcing_conditions")
        for mark in marks:
            attest_quotation_mark(uod.current_egi, mark, resolver,
                                  quoted_ground=parse_egif(mark.target))
            # the Montague rider: the relation is DEFINED — every scribed
            # settlement recomputes from the machinery, forever
            recomputed = mq.settlement(
                chain, mq.scribes_relation(mark.extra["relation"])).status
            assert recomputed == mark.extra["settlement"]

    def test_the_trichotomy_is_drawn(self, tomos):
        """settled/open/excluded as ink: two positive claims + a genuine
        drawn negation for the excluded case."""
        from world_scroll import m_view

        uod = tomos.load_uod("forcing_forces")
        view = m_view(uod.current_egi)
        rels = sorted(view.rel[e.id] for e in view.E)
        assert rels.count("forces") == 3
        # the excluded claim is enclosed (a negation); the two positive
        # claims stand at M's own level
        enclosed = [is_enclosed(view, e.id) for e in view.E
                    if view.rel[e.id] == "forces"]
        assert sorted(enclosed) == [False, False, True]


class TestPeirceLawMention:
    """Exemplar (iii): cross-UoD mention with a real citation."""

    def test_mention_resolves_to_the_theorem_without_import(self, tomos):
        uod = tomos.load_uod("peirce_law_commentary")
        assert uod is not None, "run tools/build_quotation_exemplars.py"
        mark = quotation_marks_from_list(
            tomos.load_quotations("peirce_law_commentary"))[0]
        assert mark.kind == "uod" and mark.target == "peirce_law"
        resolver = UoDQuotationResolver(tomos)
        ground = parse_egif("~[ ~[ ~[ (P) ~[ (Q) ] ] ~[ (P) ] ] ~[ (P) ] ]")
        attest_quotation_mark(uod.current_egi, mark, resolver,
                              quoted_ground=ground)
        # mention, not use: the host still draws only the citation spot
        view_rels = sorted(uod.current_egi.rel.values())
        assert view_rels == ["cites"]

    def test_carries_the_scholarly_citation(self, tomos):
        import json

        from scholarly_citation import citation_for

        prov = json.loads(
            (TOMOS_ROOT / "universes" / "peirce_law" / "provenance.json")
            .read_text())
        cite = citation_for(provenance=prov)
        assert cite["has_source"]
        anns = tomos.load_annotations("peirce_law_commentary")
        assert any("Peirce, Charles Sanders (1885)" in a.get("text", "")
                   for a in anns)


# --------------------------------------------------------------------------- #
# The glyph — pure chrome, off by default.
# --------------------------------------------------------------------------- #

class TestQuotationGlyph:
    def _render(self, host, marks=None, resolver=None):
        from simple_svg_renderer import SimpleSVGRenderer

        dto = _layout_fn(host)
        qm = (render_quotation_marks(marks, resolver)
              if marks is not None else None)
        return dto, SimpleSVGRenderer().render_to_svg(
            dto, egi=host, quotation_marks=qm)

    def test_default_output_is_byte_identical(self):
        host = parse_egif(EXHIBIT)
        _, plain1 = self._render(host)
        _, plain2 = self._render(host)
        assert plain1 == plain2
        assert "quotation-oval" not in plain1

    def test_glyph_appears_only_when_fed(self):
        host = parse_egif(EXHIBIT)
        resolver = EGIFQuotationResolver()
        mark = mark_quotation(host, vertex_by_label(host, "M_swan_law"),
                              LAW, resolver)
        _, svg = self._render(host, [mark], resolver)
        assert "quotation-spot" in svg
        assert "quotation-oval" in svg
        assert 'data-quotation-sort="proposition"' in svg
        assert f"⌜+{quotation_horizon(mark, resolver)}⌝" in svg

    def test_glyph_changes_no_attested_dto_geometry(self):
        """The dotted oval is drawn stroke only: the DTO the §3.3 check reads
        is produced before the renderer runs and is identical either way."""
        host = parse_egif(EXHIBIT)
        resolver = EGIFQuotationResolver()
        mark = mark_quotation(host, vertex_by_label(host, "M_swan_law"),
                              LAW, resolver)
        dto_plain, _ = self._render(host)
        dto_marked, _ = self._render(host, [mark], resolver)
        assert dto_plain.vertex_positions == dto_marked.vertex_positions
        assert dto_plain.predicate_positions == dto_marked.predicate_positions
        assert dto_plain.cut_bounds == dto_marked.cut_bounds

    def test_horizon_counts_the_quoted_graph(self):
        resolver = EGIFQuotationResolver()
        host = parse_egif(EXHIBIT)
        mark = mark_quotation(host, vertex_by_label(host, "M_swan_law"),
                              LAW, resolver)
        quoted = parse_egif(LAW)
        assert quotation_horizon(mark, resolver) == (
            len(quoted.V) + len(quoted.E) + len(quoted.Cut))


# --------------------------------------------------------------------------- #
# Persistence — quotations.json beside annotations.json.
# --------------------------------------------------------------------------- #

class TestPersistence:
    def test_exemplars_persist_their_marks(self, tomos):
        for uod_id, n in (("swan_third_tense", 1), ("forcing_forces", 3),
                          ("peirce_law_commentary", 1)):
            items = tomos.load_quotations(uod_id)
            assert len(items) == n, uod_id
            marks = quotation_marks_from_list(items)
            assert all(m.warrant == "low" for m in marks)

    def test_absent_overlay_reads_empty(self, tomos):
        assert tomos.load_quotations("peirce_law") == []
        assert tomos.load_quotations("no_such_uod") == []


# --------------------------------------------------------------------------- #
# B-min (stage ①): the core-carried quotation — scribe, convert, project.     #
# --------------------------------------------------------------------------- #


class TestScribeAndProject:
    """The construction half of the core opening: ``scribe_quotation`` /
    ``quote_existing_name`` put the sort and the oval IN the graph;
    ``project_first_order`` is the A3 erasure projection (strips the layer,
    recovering exactly the never-quoted host)."""

    def test_scribe_then_project_recovers_the_host(self):
        from quotation_overlay import project_first_order, scribe_quotation

        host = parse_egif('(P *x) ~[ (Q x) ]')
        quoted = parse_egif('~[ (swan *s) ~[ (white s) ] ]')
        new_host, mark, cut_id = scribe_quotation(host, "M_law", quoted)
        assert cut_id in new_host.quotation
        assert new_host.sort[new_host.quotation[cut_id]] == SORT_PROPOSITION
        assert same_graph(project_first_order(new_host), host)

    def test_scribed_oval_lifts_to_the_quoted_graph(self):
        from quotation_overlay import lift_quotation, scribe_quotation

        host = parse_egif('(P *x)')
        quoted = parse_egif('~[ (swan *s) ~[ (white s) ] ]')
        new_host, _mark, cut_id = scribe_quotation(host, "M_law", quoted)
        # the oval's CONTENTS are the quoted object (the dotted curve is the
        # device, not part of the object): lift_quotation, not lift_cut
        assert same_graph(lift_quotation(new_host, cut_id), quoted)

    def test_quote_existing_name_binds_in_the_names_area(self):
        from quotation_overlay import quote_existing_name

        host = parse_egif('~[ (superseded "M_law") ]')
        name_id = vertex_by_label(host, "M_law")
        quoted = parse_egif('(white *w)')
        new_host, cut_id = quote_existing_name(host, name_id, quoted)
        assert new_host.quotation[cut_id] == name_id
        assert new_host.get_context(cut_id) == new_host.get_context(name_id)

    def test_default_mark_target_is_the_quoted_egif(self):
        from quotation_overlay import EGIFQuotationResolver, scribe_quotation

        host = parse_egif('(P *x)')
        quoted = parse_egif('(white *w)')
        _h, mark, _c = scribe_quotation(host, "M_law", quoted)
        assert same_graph(EGIFQuotationResolver().resolve(mark), quoted)


class TestQuoteStep:
    """The explicit QUOTE chain step — the scribing recorded, earned at
    record time, neutral in proof_character (a mention asserts nothing)."""

    def test_quote_step_records_and_transforms(self):
        from proof_authoring import ProofChain
        from quotation_overlay import quote_step

        pc = ProofChain.from_blank()
        pc.apply("DC+", into=lambda g: g.sheet)
        import eg_navigation as nav

        pc.apply("INS", insert='(superseded "M_law")',
                 into=lambda g: nav.child_cuts(g, g.sheet)[0])
        quote_step(pc, "M_law", '~[ (swan *s) ~[ (white s) ] ]')
        host = pc.current
        assert len(host.quotation) == 1
        step = pc._steps[-1]
        assert step.rule_name == "QUOTE"
        assert step.parameters["act"] == "quotation"
        assert step.parameters["earned"] is True

    def test_quote_is_neutral_in_proof_character(self):
        from proof_character import NEUTRAL_RULES

        assert "QUOTE" in NEUTRAL_RULES

    def test_sort_step_gives_the_mention_by_name_state(self):
        from proof_authoring import ProofChain
        from quotation_overlay import sort_step

        pc = ProofChain.from_blank()
        pc.apply("DC+", into=lambda g: g.sheet)
        import eg_navigation as nav

        pc.apply("INS", insert='(cites "peirce_law")',
                 into=lambda g: nav.child_cuts(g, g.sheet)[0])
        sort_step(pc, "peirce_law", target="peirce_law")
        host = pc.current
        name_id = vertex_by_label(host, "peirce_law")
        assert host.sort[name_id] == SORT_PROPOSITION
        assert host.quotation == {}  # no oval: the named horizon


class TestInterpreterOpacity:
    """Quoted ink asserts nothing: the peel, the materializer, and the modal
    reading all skip a quotation area (mention, not use)."""

    def _quoted_m(self):
        from quotation_overlay import scribe_quotation

        m = parse_egif('(swan "Alba") (white "Alba")')
        law = parse_egif('~[ (swan *x) ~[ (black x) ] ]')
        quoted_m, _mark, _cut = scribe_quotation(m, "old_law", law)
        return m, quoted_m

    def test_peel_ignores_quoted_ink(self):
        from domain_oracle import CorpusOracle
        from semantic_game import evaluate

        m, quoted_m = self._quoted_m()
        oracle = CorpusOracle([("M", m)], closed=True)
        g = quoted_m  # evaluate the quotation-bearing graph AS the proposal
        verdict = evaluate(g, oracle, closed=True).verdict.value
        # the host's own atoms hold in M; the quoted law (which M would
        # falsify — Alba is white, and the law demands black) is skipped
        assert verdict == "true"

    def test_materializer_skips_a_quoted_law(self):
        from model_materialization import materialize_egi

        _m, quoted_m = self._quoted_m()
        facts_egi, report = materialize_egi(quoted_m)
        assert report.rules_applied == 0
        assert any(s.reason == "quotation" for s in report.skipped)
        assert "black" not in set(facts_egi.rel.values())

    def test_scribes_relation_ignores_quoted_ink(self):
        from modal_query import scribes_relation

        _m, quoted_m = self._quoted_m()
        assert scribes_relation("swan")(quoted_m)      # host ink counts
        assert not scribes_relation("black")(quoted_m)  # quoted ink does not

    def test_copy_area_carries_the_maps(self):
        from quotation_overlay import scribe_quotation
        from world_scroll import _copy_area
        from egi_core_dau import create_empty_graph

        host = parse_egif('(P *x)')
        quoted = parse_egif('(white *w)')
        quoted_host, _mark, cut_id = scribe_quotation(host, "M_law", quoted)
        view = create_empty_graph()
        copied = _copy_area(quoted_host, view, quoted_host.sheet, view.sheet)
        assert dict(copied.quotation) == dict(quoted_host.quotation)
        assert dict(copied.sort) == dict(quoted_host.sort)
