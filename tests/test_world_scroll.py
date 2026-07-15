"""The standing world-scroll (world_scroll.py) — the polarity shift of
M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE §3–§4 made operational.

Covers: structural recognition (+ ambiguity/fallback), m_view id-preservation
and same-graph fidelity, the rule-licensed wrap (DC+ · INS) round-trip, the
structural adapter, enlargement (INS into the negative arena), and the
world-withdrawal triple (ERA / DC+ / INS) with the derivation earned."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

import eg_navigation as nav
from contest_context import polarity_of
from egif_generator_dau import generate_egif
from egif_parser_dau import parse_egif
from world_scroll import (
    WorldScroll,
    enlarge_m,
    find_world_scroll,
    is_ligature_closed,
    m_area,
    m_element_ids,
    m_view,
    withdraw_and_resupply,
    wrap_m,
    wrap_state,
)

SWAN_M = ('(swan "Ciel") (swan "Dover") (white "Ciel") (white "Dover") '
          '~[ (swan *x) ~[ (white x) ] ]')
WRAPPED_SWAN = f"~[ {SWAN_M} ~[ ] ]"


class TestRecognition:
    def test_wrapped_m_is_recognized(self):
        egi = parse_egif(WRAPPED_SWAN)
        scroll = find_world_scroll(egi)
        assert scroll is not None
        # W is the sheet's only cut; H is the empty cut inside it
        assert scroll.cut_id in nav.child_cuts(egi, egi.sheet)
        assert not egi.get_area(scroll.hold_id)

    def test_sheet_level_m_falls_back(self):
        egi = parse_egif(SWAN_M)
        assert find_world_scroll(egi) is None
        assert m_area(egi) == egi.sheet
        assert m_view(egi) is egi  # identity, not a copy

    def test_sheet_edge_defeats_recognition(self):
        egi = parse_egif(f'(bird "Pip") {WRAPPED_SWAN}')
        assert find_world_scroll(egi) is None

    def test_two_sheet_cuts_defeat_recognition(self):
        egi = parse_egif(f'{WRAPPED_SWAN} ~[ (dog "Rex") ]')
        assert find_world_scroll(egi) is None

    def test_missing_hold_defeats_recognition(self):
        egi = parse_egif(f"~[ {SWAN_M} ]")  # would DENY M, not suppose it
        assert find_world_scroll(egi) is None

    def test_two_empty_cuts_are_ambiguous(self):
        egi = parse_egif(f"~[ {SWAN_M} ~[ ] ~[ ] ]")
        assert find_world_scroll(egi) is None

    def test_blank_sheet_has_no_scroll(self):
        assert find_world_scroll(parse_egif("")) is None

    def test_arena_polarity_is_negative(self):
        egi = parse_egif(WRAPPED_SWAN)
        scroll = find_world_scroll(egi)
        assert polarity_of(egi, scroll.cut_id) == "negative"
        assert polarity_of(egi, scroll.hold_id) == "positive"


class TestMView:
    def test_view_is_same_graph_as_unwrapped_m(self):
        wrapped = parse_egif(WRAPPED_SWAN)
        assert nav.same_graph(m_view(wrapped), parse_egif(SWAN_M))

    def test_view_preserves_element_ids(self):
        wrapped = parse_egif(WRAPPED_SWAN)
        scroll = find_world_scroll(wrapped)
        view = m_view(wrapped)
        inside = set(wrapped.get_full_context(scroll.cut_id)) - {scroll.hold_id}
        inside.discard(scroll.cut_id)
        view_ids = ({v.id for v in view.V} | {e.id for e in view.E}
                    | {c.id for c in view.Cut})
        assert view_ids == {i for i in inside}

    def test_view_excludes_the_hold(self):
        wrapped = parse_egif(WRAPPED_SWAN)
        view = m_view(wrapped)
        # one cut only: the law scroll's outer + inner = 2 cuts, no empty hold
        assert all(view.get_area(c.id) for c in view.Cut
                   if c.id in nav.child_cuts(view, view.sheet))

    def test_m_element_ids_excludes_hold(self):
        wrapped = parse_egif(WRAPPED_SWAN)
        scroll = find_world_scroll(wrapped)
        ids = m_element_ids(wrapped)
        assert scroll.hold_id not in ids
        assert ids == wrapped.get_area(scroll.cut_id) - {scroll.hold_id}

    def test_relation_names_survive_structurally(self):
        # names like "Warm-blooded" (from CLIF/OWL imports) cannot round-trip
        # EGIF — the very reason m_view copies structurally. Build directly.
        from egi_core_dau import create_cut, create_edge, create_empty_graph, create_vertex

        g = create_empty_graph()
        w, h = create_cut(), create_cut()
        g = g.with_cut(w).with_cut(h, context_id=w.id)
        v = create_vertex(label="Leo", is_generic=False)
        g = g.with_vertex_in_context(v, w.id)
        g = g.with_edge(create_edge(), (v.id,), "Warm-blooded", context_id=w.id)
        assert find_world_scroll(g) is not None
        view = m_view(g)
        assert set(view.rel.values()) == {"Warm-blooded"}


class TestWrap:
    def test_wrap_m_round_trips_through_recognition(self):
        m = parse_egif(SWAN_M)
        wrapped, scroll = wrap_m(m)
        assert find_world_scroll(wrapped) == scroll
        assert nav.same_graph(m_view(wrapped), m)

    def test_wrap_blank_m(self):
        wrapped, scroll = wrap_m(parse_egif(""))
        assert find_world_scroll(wrapped) == scroll
        assert nav.same_graph(m_view(wrapped), parse_egif(""))

    def test_wrap_state_preserves_ids(self):
        m = parse_egif(SWAN_M)
        wrapped, scroll = wrap_state(m)
        assert find_world_scroll(wrapped) == scroll
        m_ids = {v.id for v in m.V} | {e.id for e in m.E} | {c.id for c in m.Cut}
        w_ids = ({v.id for v in wrapped.V} | {e.id for e in wrapped.E}
                 | {c.id for c in wrapped.Cut})
        assert m_ids <= w_ids
        assert nav.same_graph(m_view(wrapped), m)

    def test_wrap_state_is_idempotent(self):
        wrapped, _ = wrap_state(parse_egif(SWAN_M))
        again, scroll = wrap_state(wrapped)
        assert again is wrapped
        assert scroll == find_world_scroll(wrapped)

    def test_wrapped_scroll_is_ligature_closed(self):
        wrapped, scroll = wrap_m(parse_egif(SWAN_M))
        assert is_ligature_closed(wrapped, scroll)


class TestEnlarge:
    def test_enlarge_adds_to_the_arena(self):
        wrapped, scroll = wrap_m(parse_egif(SWAN_M))
        bigger = enlarge_m(wrapped, '(swan "Nox")')
        assert nav.same_graph(
            m_view(bigger), parse_egif(f'{SWAN_M} (swan "Nox")'))
        # still the standing scroll
        assert find_world_scroll(bigger) is not None

    def test_enlarge_accepts_a_law(self):
        wrapped, _ = wrap_m(parse_egif('(bird "Pip")'))
        bigger = enlarge_m(wrapped, "~[ (bird *x) ~[ (flies x) ] ]")
        assert nav.same_graph(
            m_view(bigger),
            parse_egif('(bird "Pip") ~[ (bird *x) ~[ (flies x) ] ]'))

    def test_enlarge_refuses_without_scroll(self):
        with pytest.raises(ValueError, match="world-scroll"):
            enlarge_m(parse_egif(SWAN_M), '(swan "Nox")')


class TestWithdrawal:
    def test_withdraw_and_resupply(self):
        wrapped, _ = wrap_m(parse_egif(SWAN_M))
        new_m = ('(swan "Ciel") (swan "Dover") (swan "Nox") (white "Ciel") '
                 '(white "Dover") (black "Nox")')  # law relinquished, anomaly in
        revised, derivation = withdraw_and_resupply(wrapped, new_m)
        assert derivation == ["ERA", "DC+", "INS"]
        assert find_world_scroll(revised) is not None
        assert nav.same_graph(m_view(revised), parse_egif(new_m))
        # the over-general law is gone: the new arena holds no cut but the hold
        scroll = find_world_scroll(revised)
        assert nav.child_cuts(revised, scroll.cut_id) == [scroll.hold_id]

    def test_withdraw_refuses_without_scroll(self):
        with pytest.raises(ValueError, match="world-scroll"):
            withdraw_and_resupply(parse_egif(SWAN_M), "")

    def test_withdraw_to_blank_m(self):
        wrapped, _ = wrap_m(parse_egif('(swan "Ciel")'))
        revised, _ = withdraw_and_resupply(wrapped, "")
        scroll = find_world_scroll(revised)
        assert scroll is not None
        assert nav.same_graph(m_view(revised), parse_egif(""))


class TestLayoutAndAttestation:
    """The residence must render and attest (§3.3) like any canonical graph."""

    def test_wrapped_m_attests(self):
        from correspondence_attestation import attest_correspondence
        from elk_layout_engine import ELKLayoutEngine
        from style_loader import load_default_style

        wrapped, _ = wrap_m(parse_egif(SWAN_M))
        dto = ELKLayoutEngine().generate_layout(wrapped, load_default_style())
        attest_correspondence(wrapped, dto)  # raises on failure
