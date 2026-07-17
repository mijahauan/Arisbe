"""The standing world-scroll (world_scroll.py) — M resident in cells at even
depth (M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE §9, ratified 2026-07-16).

Covers: structural recognition of the cells shape (+ fallback; the retired
level-1 shape falls back to the sheet), m_view as the union of cell interiors
(id-preservation, same-graph fidelity), the rule-licensed wrap (DC+ · INS of a
cell) round-trip, the structural adapter, enlargement (INS of a closed cell —
one licensed move), retraction (ERA inside a cell — one licensed move; scars
stand), and the world-withdrawal triple retained for full replacement."""

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
    retract_from_m,
    withdraw_and_resupply,
    wrap_m,
    wrap_state,
)

SWAN_M = ('(swan "Ciel") (swan "Dover") (white "Ciel") (white "Dover") '
          '~[ (swan *x) ~[ (white x) ] ]')
WRAPPED_SWAN = f"~[ ~[ {SWAN_M} ] ~[ ] ]"          # one cell + the hold
OLD_WRAPPED_SWAN = f"~[ {SWAN_M} ~[ ] ]"           # the retired level-1 shape


class TestRecognition:
    def test_wrapped_m_is_recognized(self):
        egi = parse_egif(WRAPPED_SWAN)
        scroll = find_world_scroll(egi)
        assert scroll is not None
        assert scroll.cut_id in nav.child_cuts(egi, egi.sheet)
        assert len(scroll.cell_ids) == 1
        assert len(scroll.hold_ids) == 1
        assert not egi.get_area(scroll.hold_id)
        assert egi.get_area(scroll.cell_ids[0])

    def test_sheet_level_m_falls_back(self):
        egi = parse_egif(SWAN_M)
        assert find_world_scroll(egi) is None
        assert m_area(egi) == egi.sheet
        assert m_view(egi) is egi  # identity, not a copy

    def test_old_level1_shape_falls_back(self):
        # the retired residence: M's ink directly in W (a W-level edge) is
        # NOT the shape — left visible rather than misread as cells
        egi = parse_egif(OLD_WRAPPED_SWAN)
        assert find_world_scroll(egi) is None
        assert m_view(egi) is egi

    def test_sheet_edge_defeats_recognition(self):
        egi = parse_egif(f'(bird "Pip") {WRAPPED_SWAN}')
        assert find_world_scroll(egi) is None

    def test_two_sheet_cuts_defeat_recognition(self):
        egi = parse_egif(f'{WRAPPED_SWAN} ~[ (dog "Rex") ]')
        assert find_world_scroll(egi) is None

    def test_missing_hold_defeats_recognition(self):
        # a cell but no empty cut: the outer negation would BIND
        egi = parse_egif(f"~[ ~[ {SWAN_M} ] ]")
        assert find_world_scroll(egi) is None

    def test_scars_are_recognized(self):
        # several empty cuts = the hold + scars, one kind (verdict D3)
        egi = parse_egif(f"~[ ~[ {SWAN_M} ] ~[ ] ~[ ] ]")
        scroll = find_world_scroll(egi)
        assert scroll is not None
        assert len(scroll.hold_ids) == 2
        assert len(scroll.cell_ids) == 1

    def test_empty_residence_is_recognized(self):
        # DC+ alone creates the residence: W + hold, zero cells
        egi = parse_egif("~[ ~[ ] ]")
        scroll = find_world_scroll(egi)
        assert scroll is not None
        assert scroll.cell_ids == ()
        assert nav.same_graph(m_view(egi), parse_egif(""))

    def test_multiple_cells_are_recognized(self):
        egi = parse_egif('~[ ~[ (swan "Ciel") ] ~[ (black "Nox") ] ~[ ] ]')
        scroll = find_world_scroll(egi)
        assert scroll is not None
        assert len(scroll.cell_ids) == 2

    def test_blank_sheet_has_no_scroll(self):
        assert find_world_scroll(parse_egif("")) is None

    def test_arena_polarity(self):
        egi = parse_egif(WRAPPED_SWAN)
        scroll = find_world_scroll(egi)
        assert polarity_of(egi, scroll.cut_id) == "negative"
        assert polarity_of(egi, scroll.hold_id) == "positive"
        # the cells are the Verifier's territory: even depth, positive
        assert polarity_of(egi, scroll.cell_ids[0]) == "positive"


class TestMView:
    def test_view_is_same_graph_as_unwrapped_m(self):
        wrapped = parse_egif(WRAPPED_SWAN)
        assert nav.same_graph(m_view(wrapped), parse_egif(SWAN_M))

    def test_view_unions_the_cells(self):
        wrapped = parse_egif(
            '~[ ~[ (swan "Ciel") (white "Ciel") ] ~[ (black "Nox") ] ~[ ] ]')
        assert nav.same_graph(
            m_view(wrapped),
            parse_egif('(swan "Ciel") (white "Ciel") (black "Nox")'))

    def test_view_preserves_element_ids(self):
        wrapped = parse_egif(WRAPPED_SWAN)
        scroll = find_world_scroll(wrapped)
        view = m_view(wrapped)
        inside = set()
        for cell in scroll.cell_ids:
            inside |= set(wrapped.get_full_context(cell)) - {cell}
        view_ids = ({v.id for v in view.V} | {e.id for e in view.E}
                    | {c.id for c in view.Cut})
        assert view_ids == inside

    def test_view_excludes_holds_and_cell_husks(self):
        wrapped = parse_egif(f"~[ ~[ {SWAN_M} ] ~[ ] ~[ ] ]")
        view = m_view(wrapped)
        # every sheet-level cut of the view is real M content (the law), never
        # an empty hold/scar or the cell's own husk
        assert all(view.get_area(c) for c in nav.child_cuts(view, view.sheet))

    def test_m_element_ids_is_the_union_of_cell_areas(self):
        wrapped = parse_egif(WRAPPED_SWAN)
        scroll = find_world_scroll(wrapped)
        ids = m_element_ids(wrapped)
        for hold in scroll.hold_ids:
            assert hold not in ids
        expected = set()
        for cell in scroll.cell_ids:
            expected |= set(wrapped.get_area(cell))
        assert ids == frozenset(expected)

    def test_relation_names_survive_structurally(self):
        # names like "Warm-blooded" (from CLIF/OWL imports) cannot round-trip
        # EGIF — the very reason m_view copies structurally. Build directly.
        from egi_core_dau import create_cut, create_edge, create_empty_graph, create_vertex

        g = create_empty_graph()
        w, cell, h = create_cut(), create_cut(), create_cut()
        g = (g.with_cut(w).with_cut(cell, context_id=w.id)
             .with_cut(h, context_id=w.id))
        v = create_vertex(label="Leo", is_generic=False)
        g = g.with_vertex_in_context(v, cell.id)
        g = g.with_edge(create_edge(), (v.id,), "Warm-blooded", context_id=cell.id)
        assert find_world_scroll(g) is not None
        view = m_view(g)
        assert set(view.rel.values()) == {"Warm-blooded"}


class TestWrap:
    def test_wrap_m_round_trips_through_recognition(self):
        m = parse_egif(SWAN_M)
        wrapped, scroll = wrap_m(m)
        assert find_world_scroll(wrapped) == scroll
        assert len(scroll.cell_ids) == 1        # initial supply = one cell (D2)
        assert nav.same_graph(m_view(wrapped), m)

    def test_wrap_blank_m(self):
        wrapped, scroll = wrap_m(parse_egif(""))
        assert find_world_scroll(wrapped) == scroll
        assert scroll.cell_ids == ()            # the empty residence
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
    def test_enlarge_adds_a_new_cell(self):
        wrapped, scroll = wrap_m(parse_egif(SWAN_M))
        bigger = enlarge_m(wrapped, '(swan "Nox")')
        assert nav.same_graph(
            m_view(bigger), parse_egif(f'{SWAN_M} (swan "Nox")'))
        after = find_world_scroll(bigger)
        assert after is not None
        assert len(after.cell_ids) == len(scroll.cell_ids) + 1  # its own cell

    def test_enlarge_accepts_a_law(self):
        wrapped, _ = wrap_m(parse_egif('(bird "Pip")'))
        bigger = enlarge_m(wrapped, "~[ (bird *x) ~[ (flies x) ] ]")
        assert nav.same_graph(
            m_view(bigger),
            parse_egif('(bird "Pip") ~[ (bird *x) ~[ (flies x) ] ]'))

    def test_enlarge_refuses_without_scroll(self):
        with pytest.raises(ValueError, match="world-scroll"):
            enlarge_m(parse_egif(SWAN_M), '(swan "Nox")')


class TestRetract:
    """Retraction is ONE licensed ERA inside a cell (the §9 fallibilist pole)."""

    def test_retract_law_is_a_single_era(self):
        wrapped, _ = wrap_m(parse_egif(SWAN_M))
        revised, derivation = retract_from_m(
            wrapped, subgraph_egif="~[ (swan *x) ~[ (white x) ] ]")
        assert derivation == ["ERA"]
        assert nav.same_graph(
            m_view(revised),
            parse_egif('(swan "Ciel") (swan "Dover") (white "Ciel") '
                       '(white "Dover")'))
        assert find_world_scroll(revised) is not None

    def test_retract_atom_keeps_shared_vertex(self):
        # (white "Ciel") goes; the "Ciel" vertex survives — (swan "Ciel") uses it
        wrapped, _ = wrap_m(parse_egif(SWAN_M))
        revised, derivation = retract_from_m(
            wrapped, relation="white", labels=["Ciel"])
        assert derivation == ["ERA"]
        assert nav.same_graph(
            m_view(revised),
            parse_egif('(swan "Ciel") (swan "Dover") (white "Dover") '
                       '~[ (swan *x) ~[ (white x) ] ]'))

    def test_retract_relation_prunes_orphans(self):
        wrapped, _ = wrap_m(parse_egif('(swan "Alba") (black "Nox")'))
        revised, derivation = retract_from_m(wrapped, relation="black")
        assert derivation == ["ERA"]
        # "Nox" was only ever posited by the retracted habit — pruned with it
        assert nav.same_graph(m_view(revised), parse_egif('(swan "Alba")'))

    def test_retract_relation_takes_every_atom_of_the_name(self):
        wrapped, _ = wrap_m(parse_egif(SWAN_M))
        revised, derivation = retract_from_m(wrapped, relation="white")
        assert derivation == ["ERA", "ERA"]
        assert nav.same_graph(
            m_view(revised),
            parse_egif('(swan "Ciel") (swan "Dover") '
                       '~[ (swan *x) ~[ (white x) ] ]'))

    def test_emptied_husk_stands_as_a_scar(self):
        wrapped, scroll = wrap_m(parse_egif('(rumor "Old")'))
        revised, _ = retract_from_m(wrapped, relation="rumor")
        after = find_world_scroll(revised)
        assert after is not None
        # the cell emptied: it now reads as a second empty cut beside the hold
        assert len(after.hold_ids) == len(scroll.hold_ids) + 1
        assert after.cell_ids == ()
        assert nav.same_graph(m_view(revised), parse_egif(""))

    def test_retraction_only_touches_its_cell(self):
        wrapped, _ = wrap_m(parse_egif('(swan "Alba")'))
        bigger = enlarge_m(wrapped, '(black "Nox")')
        revised, _ = retract_from_m(bigger, relation="black")
        assert nav.same_graph(m_view(revised), parse_egif('(swan "Alba")'))
        after = find_world_scroll(revised)
        assert len(after.cell_ids) == 1         # the first cell untouched
        assert len(after.hold_ids) == 2         # the second is now a scar

    def test_no_match_raises(self):
        wrapped, _ = wrap_m(parse_egif(SWAN_M))
        with pytest.raises(ValueError, match="to retract"):
            retract_from_m(wrapped, relation="unicorn")
        with pytest.raises(ValueError, match="to retract"):
            retract_from_m(wrapped, subgraph_egif='~[ (dragon *x) ]')

    def test_refuses_without_scroll(self):
        with pytest.raises(ValueError, match="world-scroll"):
            retract_from_m(parse_egif(SWAN_M), relation="white")

    def test_requires_something_to_retract(self):
        wrapped, _ = wrap_m(parse_egif(SWAN_M))
        with pytest.raises(ValueError, match="needs"):
            retract_from_m(wrapped)


class TestWithdrawal:
    """The triple retires to the rare full-replacement case, but must work."""

    def test_withdraw_and_resupply(self):
        wrapped, _ = wrap_m(parse_egif(SWAN_M))
        new_m = ('(swan "Ciel") (swan "Dover") (swan "Nox") (white "Ciel") '
                 '(white "Dover") (black "Nox")')  # law relinquished, anomaly in
        revised, derivation = withdraw_and_resupply(wrapped, new_m)
        assert derivation == ["ERA", "DC+", "INS"]
        scroll = find_world_scroll(revised)
        assert scroll is not None
        assert nav.same_graph(m_view(revised), parse_egif(new_m))
        # a fresh residence: one cell, one hold, no scars carried over
        assert len(scroll.cell_ids) == 1
        assert len(scroll.hold_ids) == 1

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

    def test_scarred_residence_attests(self):
        from correspondence_attestation import attest_correspondence
        from elk_layout_engine import ELKLayoutEngine
        from style_loader import load_default_style

        wrapped, _ = wrap_m(parse_egif('(swan "Alba") (rumor "Old")'))
        bigger = enlarge_m(wrapped, '(black "Nox")')
        revised, _ = retract_from_m(bigger, relation="black")  # scar stands
        dto = ELKLayoutEngine().generate_layout(revised, load_default_style())
        attest_correspondence(revised, dto)
