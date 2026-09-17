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


class TestEpisode:
    """The EPG episode lifecycle in ink (M_RESIDENCE §10): entertain (DC+ ·
    IT+ · INS behind the vacuity rider), discharge (drawn modus ponens —
    IT− · IT− · DC−), abandon (one ERA). And the episode theorem: the DC+
    must land in an even context at depth ≥ 2 — at depth 0 the discharge is
    unreachable by rule."""

    M0 = '(dog "Rex") ~[ (dog *x) ~[ (mammal x) ] ]'
    P = '(mammal "Rex")'

    def _entertained(self):
        from world_scroll import entertain_episode
        g, _ = wrap_m(parse_egif(self.M0))
        g, derivation = entertain_episode(g, self.P)
        return g, derivation

    def test_entertain_builds_the_vacuous_exhibit(self):
        g, derivation = self._entertained()
        assert derivation[0] == "DC+" and derivation[-1] == "INS"
        assert all(d == "IT+" for d in derivation[1:-1]) and len(derivation) >= 3
        scroll = find_world_scroll(g)
        assert scroll is not None and is_ligature_closed(g, scroll)

    def test_discharge_is_drawn_modus_ponens(self):
        from world_scroll import discharge_episode
        g, _ = self._entertained()
        g, derivation = discharge_episode(g, self.P)
        assert derivation[-1] == "DC-"
        assert all(d == "IT-" for d in derivation[:-1])
        # P stands at the level of the original M (round-trip unifies the
        # discharged constant's fresh vertex with the standing one)
        view = parse_egif(generate_egif(m_view(g)))
        assert nav.same_graph(view, parse_egif(f'{self.M0} {self.P}'))

    def test_abandon_is_one_era_and_m_unchanged(self):
        from world_scroll import abandon_episode
        g, _ = self._entertained()
        g, derivation = abandon_episode(g, self.P)
        assert derivation == ["ERA"]
        assert nav.same_graph(parse_egif(generate_egif(m_view(g))),
                              parse_egif(self.M0))

    def test_discharge_refuses_without_an_exhibit(self):
        from world_scroll import discharge_episode
        g, _ = wrap_m(parse_egif(self.M0))
        with pytest.raises(ValueError, match="entertain it first"):
            discharge_episode(g, self.P)

    def test_the_bottom_door_is_licensed_but_visible(self):
        """The ⊥-door (M_RESIDENCE §10): with the standing hold in scope, four
        licensed moves scribe ARBITRARY content into M — which is exactly why
        ruling (b) puts the earning in the record (the gate's m_view tripwire
        and discharge citation), never in the licence."""
        from proof_authoring import apply_rule
        from world_scroll import _fresh_double_cut
        g, scroll = wrap_m(parse_egif(self.M0))
        cell = scroll.cell_ids[0]
        g, outer, rider = _fresh_double_cut(g, cell)          # DC+
        g = apply_rule("INS", g, egif='~[ (unicorn "Q") ]', target=outer)
        g = apply_rule("IT-", g, selection=[rider])           # rider ⇠ hold
        g = apply_rule("DC-", g, selection=[outer])
        view = parse_egif(generate_egif(m_view(g)))
        assert nav.same_graph(
            view, parse_egif(f'{self.M0} (unicorn "Q")'))     # licensed, uncontested

    def test_the_episode_theorem_depth_zero_discharge_is_unreachable(self):
        """At depth 0 (the sheet — even, but outside the residence) the arena's
        vacuity rider has NO standing empty cut in an enclosing area, so its
        deiteration is refused and the discharge can never fire: 'no
        unconditioned posit' enforced by rule-reachability (M_RESIDENCE §10)."""
        from proof_authoring import apply_rule
        from world_scroll import _fresh_double_cut
        g, _ = wrap_m(parse_egif(self.M0))
        g, outer, rider = _fresh_double_cut(g, g.sheet)       # sheet-level arena
        g = apply_rule("INS", g, egif='~[ (unicorn "Q") ]', target=outer)
        with pytest.raises(AssertionError):
            apply_rule("IT-", g, selection=[rider])           # nothing licenses it


class TestDischargeNormalizesConstants:
    """A fact landing in M joins the line already standing for that individual.

    ``discharge_episode`` brings P out of the arena and into M's cell. P was
    scribed as fresh ink by INS, so it arrives carrying its own line for any
    individual it names — and if M already stands on that individual, the cell
    ends up holding two lines for one constant. That says exactly what one line
    says, but no linear form can write it down, so the discharged M could not
    survive its own EGIF.

    The merge happens here, where M's content is constructed, and not in the
    rules: ``apply_rule`` and the six transformations are exactly as Dau states
    them. Entertaining is left alone too — the arena's exhibit is the calculus's
    own working, not part of the record.
    """

    def _episode(self):
        from egif_parser_dau import parse_egif
        from world_scroll import wrap_m, entertain_episode, discharge_episode

        proposal = '(mammal "Rex")'
        resident, _ = wrap_m(parse_egif('(dog "Rex") ~[ (dog *x) ~[ (mammal x) ] ]'))
        entertained, _ = entertain_episode(resident, proposal)
        discharged, derivation = discharge_episode(entertained, proposal)
        return entertained, discharged, derivation

    def test_the_discharged_graph_holds_one_line_per_constant(self):
        from vertex_scope import constants_normalized

        _, discharged, _ = self._episode()
        assert constants_normalized(discharged)
        assert len([v for v in discharged.V if v.label == "Rex"]) == 1

    def test_the_discharged_graph_survives_its_own_egif(self):
        import eg_navigation as nav
        from egif_generator_dau import generate_egif
        from egif_parser_dau import parse_egif

        _, discharged, _ = self._episode()
        assert nav.same_graph(discharged, parse_egif(generate_egif(discharged)))

    def test_the_derivation_is_still_the_drawn_modus_ponens(self):
        """Normalizing chooses a representative; it applies no rule and must
        not appear in the record of what was done."""
        _, _, derivation = self._episode()
        assert derivation[-1] == "DC-"
        assert set(derivation) <= {"IT-", "DC-"}

    def test_the_fact_actually_landed_in_m(self):
        from world_scroll import m_view
        from egif_generator_dau import generate_egif

        _, discharged, _ = self._episode()
        assert '(mammal "Rex")' in generate_egif(m_view(discharged))


# The probe the seed test runs in a fresh interpreter per PYTHONHASHSEED.
# Printed as JSON so the parent asserts on what was CHOSEN, not merely on a
# stable output.
_JOIN_PROBE = r'''
import json, sys
sys.path.insert(0, sys.argv[1])
from frozendict import frozendict
from egi_core_dau import Edge, RelationalGraphWithCuts, Vertex
from egif_parser_dau import parse_egif
from oracle_notes import bank_answer
from world_scroll import enlarge_m, find_world_scroll, wrap_m, wrap_state

out = {}

# 1. M holds a plain "Ciel" (on swan) and a QUOTED "Ciel" inside an oval.
m, _ = wrap_m(parse_egif('(swan "Ciel")'))
m, oval = bank_answer(m, "Ciel", qid="q", note_date="2026-09-17")
swan = next(e for e in m.rel if m.rel[e] == "swan")
utterance = next(e for e in m.rel if m.rel[e] == "utterance")
oval_before = sorted(m.area[oval])
quoted_before = {e: m.nu[e] for e in m.area[oval] if e in m.nu}
try:
    g = enlarge_m(m, '(white "Ciel")')
except Exception as exc:
    out["quoted"] = {"raised": f"{type(exc).__name__}: {exc}"}
else:
    white = next(e for e in g.rel if g.rel[e] == "white")
    out["quoted"] = {
        "white_hangs_on_the_plain_line": g.nu[white] == g.nu[swan],
        "white_hangs_on_the_quoted_line": g.nu[white] == g.nu[utterance],
        "oval_contents_untouched": sorted(g.area[oval]) == oval_before,
        "quoted_incidence_untouched": all(
            g.nu.get(e) == seq for e, seq in quoted_before.items()),
        "quotation_map_untouched": dict(g.quotation) == dict(m.quotation),
    }

# 2. Two plain standing "Ciel" lines (fixed ids): which one the admitted
#    mention joins must be a function of the graph.
sheet = RelationalGraphWithCuts(
    V=frozenset({Vertex("v_on_bird", "Ciel", False),
                 Vertex("v_on_swan", "Ciel", False)}),
    E=frozenset({Edge("e_bird"), Edge("e_swan")}),
    nu=frozendict({"e_bird": ("v_on_bird",), "e_swan": ("v_on_swan",)}),
    sheet="S", Cut=frozenset(),
    area=frozendict({"S": frozenset({"v_on_bird", "v_on_swan",
                                     "e_bird", "e_swan"})}),
    rel=frozendict({"e_bird": "bird", "e_swan": "swan"}))
m2, _ = wrap_state(sheet)
try:
    g2 = enlarge_m(m2, '(white "Ciel")')
except Exception as exc:
    out["two_lines"] = {"raised": f"{type(exc).__name__}: {exc}"}
else:
    white = next(e for e in g2.rel if g2.rel[e] == "white")
    out["two_lines"] = {"anchor": g2.nu[white][0]}
print(json.dumps(out))
'''


class TestTheAdmissionJoin:
    """``enlarge_m`` ties an admitted constant to the line already standing:
    Dau's Constant Identity Rule (p.271) scribes the identity link, and the
    project's one-constant-one-line normal form collapses the pair. Every
    intermediate graph must be an EGI (Def 12.5, p.125), the standing line
    moves only outward, and a quoted or quoting line is never touched."""

    def test_a_constant_in_two_cells_becomes_one_line_in_w(self):
        m, _ = wrap_m(parse_egif('(swan "Ciel")'))
        g = enlarge_m(m, '(white "Ciel")')
        w = find_world_scroll(g).cut_id
        ciel = [v.id for v in g.V if v.label == "Ciel"]
        assert len(ciel) == 1
        assert g.get_context(ciel[0]) == w
        by_rel = {g.rel[e]: g.nu[e] for e in g.nu}
        assert by_rel["swan"] == by_rel["white"] == (ciel[0],)
        assert "=" not in by_rel
        assert g.has_dominating_nodes()

    def test_a_standing_line_above_w_is_not_moved_inward(self):
        from egi_core_dau import Vertex

        m, _ = wrap_m(parse_egif('(swan "Dover")'))
        m = m.with_vertex(Vertex("v_ciel", "Ciel", False))
        assert find_world_scroll(m) is not None
        g = enlarge_m(m, '(white "Ciel")')
        white = next(e for e in g.rel if g.rel[e] == "white")
        assert g.nu[white] == ("v_ciel",)
        assert g.get_context("v_ciel") == g.sheet
        assert [v.id for v in g.V if v.label == "Ciel"] == ["v_ciel"]

    @pytest.mark.parametrize("seeds", [(0, 1, 2, 3, 4, 5, 42)])
    def test_the_choice_is_the_graphs_and_quoted_ink_stays_in_its_oval(
        self, seeds
    ):
        import json
        import os
        import subprocess

        src = str(Path(__file__).parent.parent / "src")
        results = {}
        for seed in seeds:
            env = {**os.environ, "PYTHONHASHSEED": str(seed)}
            run = subprocess.run(
                [sys.executable, "-c", _JOIN_PROBE, src],
                capture_output=True, text=True, env=env, timeout=120,
            )
            assert run.returncode == 0, run.stderr
            results[seed] = json.loads(run.stdout.strip().splitlines()[-1])

        for seed, result in results.items():
            assert result["quoted"] == {
                "white_hangs_on_the_plain_line": True,
                "white_hangs_on_the_quoted_line": False,
                "oval_contents_untouched": True,
                "quoted_incidence_untouched": True,
                "quotation_map_untouched": True,
            }, f"PYTHONHASHSEED={seed}: {result['quoted']}"
            assert "anchor" in result["two_lines"], (
                f"PYTHONHASHSEED={seed}: {result['two_lines']}")

        anchors = {seed: r["two_lines"]["anchor"] for seed, r in results.items()}
        assert len(set(anchors.values())) == 1, anchors
