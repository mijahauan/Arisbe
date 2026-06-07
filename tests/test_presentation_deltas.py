"""
Tests for src/presentation_deltas.py — the recorded, tagged, replayable
regime-3 delta vocabulary (the foundation of the projection ladder:
style = universal default, deltas = sparse human overrides).

Covers:
- record_delta tags a delta's target with its structural description
  (eg_navigation.describe) — the handle a future extrapolator generalizes by.
- apply_deltas replays a delta over a base LayoutDTO via presentation_ops,
  preserving §3.3, and **drops** (does not fail on) a delta that no longer
  applies — the best-effort discipline the design requires.
- the JSON round-trip (to_dict/from_dict) preserves the act.
- layout_service.generate_layout consumes deltas (a nudge shows up in the
  rendered DTO), finally making the formerly-dead layout_deltas path live.

See docs/PRESENTATION_DELTAS_AND_STYLE.md.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from egif_parser_dau import parse_egif
from style_loader import load_default_style
from elk_layout_engine import ELKLayoutEngine
from presentation_ops import element_area
from presentation_deltas import (
    PresentationDelta,
    MOVE_VERTEX,
    MOVE_PREDICATE,
    RESHAPE_CUT,
    MOVE_CUT,
    record_delta,
    apply_deltas,
    delta_key,
    merge_inherited,
    generalization_key,
    extrapolate_deltas,
    deltas_to_list,
    deltas_from_list,
)


def _mv(vid, dx, dy):
    return PresentationDelta(op=MOVE_VERTEX, params={"vertex_id": vid, "dx": dx, "dy": dy})


def _egi_and_dto(egif: str):
    egi = parse_egif(egif)
    dto = ELKLayoutEngine().generate_layout(egi, load_default_style())
    return egi, dto


def _a_sheet_vertex(egi, dto):
    """A vertex that sits on the sheet (no cut-bounds constraint on its move)."""
    cut_ids = {c.id for c in egi.Cut}
    for vid, area in element_area(egi).items():
        if area not in cut_ids and vid in dto.vertex_positions:
            return vid
    return None


def test_record_delta_tags_target_with_structural_description():
    egi, dto = _egi_and_dto("(P *x)")
    vid = _a_sheet_vertex(egi, dto)
    assert vid is not None

    d = record_delta(egi, MOVE_VERTEX, {"vertex_id": vid, "dx": 10.0, "dy": 5.0})

    assert d.op == MOVE_VERTEX
    assert d.params["vertex_id"] == vid
    # The tag is what makes a delta a *sample of an intent*, not a pixel fact.
    assert d.target.get("kind") == "vertex"
    assert "area" in d.target


def test_apply_deltas_moves_vertex_and_round_trips():
    egi, dto = _egi_and_dto("(P *x)")
    vid = _a_sheet_vertex(egi, dto)
    before = dto.vertex_positions[vid]

    d = record_delta(egi, MOVE_VERTEX, {"vertex_id": vid, "dx": 30.0, "dy": -12.0})
    new_dto, dropped = apply_deltas(egi, dto, [d])

    assert dropped == []
    after = new_dto.vertex_positions[vid]
    assert after.x == pytest.approx(before.x + 30.0)
    assert after.y == pytest.approx(before.y - 12.0)

    # JSON round-trip preserves the act verbatim.
    again = deltas_from_list(deltas_to_list([d]))
    assert again[0].to_dict() == d.to_dict()


def test_apply_deltas_drops_unapplicable_delta():
    """A delta whose target is absent from this (EGI, DTO) is dropped, not fatal;
    the base layout is returned unchanged."""
    egi, dto = _egi_and_dto("(P *x)")
    d = PresentationDelta(
        op=MOVE_VERTEX,
        params={"vertex_id": "does-not-exist", "dx": 1.0, "dy": 1.0},
    )
    new_dto, dropped = apply_deltas(egi, dto, [d])

    assert len(dropped) == 1
    assert new_dto.vertex_positions == dto.vertex_positions


# --------------------------------------------------------------------------- #
# Chain inheritance (increment 3): effective deltas accrue along the ancestry  #
# --------------------------------------------------------------------------- #


def test_delta_key_groups_by_element_not_magnitude():
    assert delta_key(_mv("v1", 1, 1)) == delta_key(_mv("v1", 9, 9))  # same vertex
    assert delta_key(_mv("v1", 1, 1)) != delta_key(_mv("v2", 1, 1))  # different


def test_merge_inherited_carries_parent_delta_forward():
    """A survivor nudged at an ancestor inherits to the descendant."""
    eff = merge_inherited(["S0", "S1"], {"S0": [_mv("v1", 10, 0)], "S1": []})
    assert [d.params["vertex_id"] for d in eff] == ["v1"]
    assert eff[0].params["dx"] == 10


def test_merge_inherited_descendant_authorship_supersedes_same_key():
    """Re-adjusting the same element later replaces the ancestor's delta — no
    double-application."""
    eff = merge_inherited(
        ["S0", "S1"], {"S0": [_mv("v1", 10, 0)], "S1": [_mv("v1", 99, 0)]}
    )
    assert len(eff) == 1
    assert eff[0].params["dx"] == 99


def test_merge_inherited_keeps_distinct_keys_and_within_state_order():
    """Distinct elements coexist; same-key drags within the winning state stay
    in authored order (cumulative)."""
    eff = merge_inherited(
        ["S0", "S1"],
        {"S0": [_mv("v1", 10, 0), _mv("v1", 5, 0)], "S1": [_mv("v2", 1, 0)]},
    )
    assert [d.params["vertex_id"] for d in eff] == ["v1", "v1", "v2"]


def test_state_ancestry_orders_initial_to_target():
    from web_api.services.ergasterion_session_manager import state_ancestry
    from tomos_service import TransformationChain, ChainStep

    chain = TransformationChain(
        initial_state_id="S0",
        steps=[ChainStep(step_id="x", rule_name="DC+", from_state_id="S0",
                         to_state_id="S1", parameters={}, timestamp="t")],
        states={},
    )
    assert state_ancestry(chain, "S1") == ["S0", "S1"]
    assert state_ancestry(chain, "S0") == ["S0"]


# --------------------------------------------------------------------------- #
# Extrapolation (increment 4, scale 1): generalize tagged deltas within a view #
# --------------------------------------------------------------------------- #


def test_generalization_key_reads_tags_and_drops_untaggable():
    """The generalization key is the coarse structural handle (a subset of the
    describe tags), distinct from delta_key's element identity; a missing field
    makes the delta ungeneralizable."""
    tagged = {"kind": "vertex", "area_polarity": "positive", "area_depth": 0}
    assert generalization_key(tagged, ("kind", "area_polarity")) == (
        ("kind", "vertex"),
        ("area_polarity", "positive"),
    )
    # Same key for the same structural description, regardless of element id.
    assert generalization_key(tagged, ("kind", "area_polarity")) == \
        generalization_key(dict(tagged, id="whatever"), ("kind", "area_polarity"))
    # An absent field → None (can't generalize by structure).
    assert generalization_key({"kind": "vertex"}, ("kind", "area_polarity")) is None


def test_extrapolate_generalizes_move_to_structural_sibling():
    """The conceptual heart: nudging one vertex generalizes the *same intent* to
    an untouched sibling of the same structural description — and never touches
    the explicitly-adjusted element."""
    egi, _ = _egi_and_dto("(P *x) (Q *y)")  # two vertices, both on the sheet
    vids = [v.id for v in egi.V]
    assert len(vids) == 2

    d = record_delta(egi, MOVE_VERTEX, {"vertex_id": vids[0], "dx": 0.0, "dy": 25.0})
    synth = extrapolate_deltas(egi, [d])

    by_target = {s.params["vertex_id"]: s for s in synth}
    assert vids[0] not in by_target          # explicit element is never overridden
    assert vids[1] in by_target              # the structural sibling is generalized to
    assert by_target[vids[1]].params["dy"] == pytest.approx(25.0)
    assert by_target[vids[1]].params["dx"] == pytest.approx(0.0)
    assert by_target[vids[1]].op == MOVE_VERTEX
    # The synthetic delta carries the sibling's own tag (a real sample of intent).
    assert by_target[vids[1]].target.get("kind") == "vertex"


def test_extrapolate_averages_multiple_exemplars():
    """Several exemplars in one structural group → the mean translation (the raw
    signal a future 'study' layer reads)."""
    egi, _ = _egi_and_dto("(P *x) (Q *y) (R *z)")  # three sheet vertices
    vids = [v.id for v in egi.V]
    assert len(vids) == 3

    deltas = [
        record_delta(egi, MOVE_VERTEX, {"vertex_id": vids[0], "dx": 0.0, "dy": 10.0}),
        record_delta(egi, MOVE_VERTEX, {"vertex_id": vids[1], "dx": 0.0, "dy": 30.0}),
    ]
    synth = extrapolate_deltas(egi, deltas)

    # Only the one untouched vertex gets a synthetic delta, with the mean dy.
    assert [s.params["vertex_id"] for s in synth] == [vids[2]]
    assert synth[0].params["dy"] == pytest.approx(20.0)


def test_extrapolate_only_generalizes_move_vertex():
    """reshape_cut bounds are absolute geometry, not a transferable translation —
    they are not extrapolated (no relative encoding yet)."""
    egi, _ = _egi_and_dto("~[ (P *x) ] (Q *y)")
    cut_id = next(iter(c.id for c in egi.Cut))
    reshape = PresentationDelta(
        op=RESHAPE_CUT,
        params={"cut_id": cut_id,
                "bounds": {"min_x": 0, "min_y": 0, "max_x": 9, "max_y": 9}},
        target={"kind": "cut", "area_polarity": "positive"},
    )
    assert extrapolate_deltas(egi, [reshape]) == []


def test_extrapolate_respects_polarity_grouping():
    """A vertex nudged in a positive area does not generalize to a vertex inside
    a cut (negative polarity) — different structural class, different key."""
    # x, w on the sheet (positive); y inside a cut (negative).
    egi, _ = _egi_and_dto("(P *x) (S *w) ~[ (Q *y) ]")
    pos = [v.id for v in egi.V if describe_polarity(egi, v.id) == "positive"]
    neg = [v.id for v in egi.V if describe_polarity(egi, v.id) == "negative"]
    assert len(pos) == 2 and len(neg) == 1

    d = record_delta(egi, MOVE_VERTEX, {"vertex_id": pos[0], "dx": 0.0, "dy": 15.0})
    synth = extrapolate_deltas(egi, [d])

    touched = {s.params["vertex_id"] for s in synth}
    assert pos[1] in touched      # same-polarity sibling IS generalized to
    assert neg[0] not in touched  # opposite-polarity vertex is left alone


def test_extrapolate_covers_new_element_in_current_egi():
    """The scale-1→2 bridge: extrapolation iterates the *current* EGI's vertices,
    so a vertex that exists at this state but carries no explicit delta — e.g. one
    a transformation step just introduced — picks up the generalized intent, while
    the explicitly-nudged survivor (still present by id) is excluded."""
    # Survivor vid_a carries an explicit nudge; vid_b is "new" (no delta).
    egi = parse_egif("(P *x) (Q *y)")
    vids = [v.id for v in egi.V]
    survivor, newcomer = vids[0], vids[1]
    d = record_delta(egi, MOVE_VERTEX, {"vertex_id": survivor, "dx": 0.0, "dy": 18.0})

    synth = extrapolate_deltas(egi, [d])

    by_target = {s.params["vertex_id"]: s for s in synth}
    assert survivor not in by_target            # explicit (inherited-by-id) excluded
    assert newcomer in by_target                # the new element is covered
    assert by_target[newcomer].params["dy"] == pytest.approx(18.0)


def describe_polarity(egi, vid):
    from eg_navigation import describe
    return describe(egi, vid).get("area_polarity")


# --------------------------------------------------------------------------- #
# move_predicate / move_cut deltas — record, apply round-trip, extrapolate     #
# --------------------------------------------------------------------------- #


def _a_predicate(egi, dto):
    for e in egi.E:
        if e.id in dto.predicate_positions:
            return e.id
    return None


def test_record_and_apply_move_predicate_round_trips():
    egi, dto = _egi_and_dto("(P *x) (Q *y)")
    pid = _a_predicate(egi, dto)
    assert pid is not None
    before = dto.predicate_positions[pid]

    d = record_delta(egi, MOVE_PREDICATE, {"predicate_id": pid, "dx": 12.0, "dy": -4.0})
    assert d.target.get("kind") == "edge"  # tagged as a predicate
    new_dto, dropped = apply_deltas(egi, dto, [d])

    assert dropped == []
    after = new_dto.predicate_positions[pid]
    assert after.x == pytest.approx(before.x + 12.0)
    assert after.y == pytest.approx(before.y - 4.0)
    # JSON round-trip preserves the act.
    again = deltas_from_list(deltas_to_list([d]))
    assert again[0].to_dict() == d.to_dict()


def test_record_and_apply_move_cut_round_trips():
    egi, dto = _egi_and_dto("~[ (P *x) ] (Q *y)")
    cid = next(iter(c.id for c in egi.Cut))
    before = dto.cut_bounds[cid]

    d = record_delta(egi, MOVE_CUT, {"cut_id": cid, "dx": -3.0, "dy": -3.0})
    assert d.target.get("kind") == "cut"
    new_dto, dropped = apply_deltas(egi, dto, [d])

    assert dropped == []
    after = new_dto.cut_bounds[cid]
    assert after.min_x == pytest.approx(before.min_x - 3.0)
    assert after.min_y == pytest.approx(before.min_y - 3.0)


def test_delta_key_distinguishes_predicate_from_vertex():
    pv = PresentationDelta(op=MOVE_VERTEX, params={"vertex_id": "n1", "dx": 1, "dy": 1})
    pe = PresentationDelta(op=MOVE_PREDICATE, params={"predicate_id": "n1", "dx": 1, "dy": 1})
    # Same raw id, different element kind → different keys (no spurious merge).
    assert delta_key(pv) != delta_key(pe)


def test_extrapolate_generalizes_move_predicate_to_sibling():
    """The predicate-side of extrapolation: nudging one relation generalizes the
    intent to an untouched relation of the same structural class."""
    egi, _ = _egi_and_dto("(P *x) (Q *y)")  # two sheet-level predicates
    pids = [e.id for e in egi.E]
    assert len(pids) == 2

    d = record_delta(egi, MOVE_PREDICATE, {"predicate_id": pids[0], "dx": 0.0, "dy": 14.0})
    synth = extrapolate_deltas(egi, [d])

    by_target = {s.params["predicate_id"]: s for s in synth}
    assert pids[0] not in by_target          # explicit predicate untouched
    assert pids[1] in by_target              # sibling generalized to
    assert by_target[pids[1]].op == MOVE_PREDICATE
    assert by_target[pids[1]].params["dy"] == pytest.approx(14.0)


def test_generate_layout_consumes_deltas():
    """The consumption side: generate_layout(deltas=…) replays the nudge over the
    base it builds, so a recorded hand-adjustment shows up in the served DTO."""
    from web_api.services.layout_service import generate_layout

    egi = parse_egif("(P *x)")
    dto0, _ = generate_layout(egi)  # base, no deltas
    vid = _a_sheet_vertex(egi, dto0)
    before = dto0.vertex_positions[vid]

    d = record_delta(egi, MOVE_VERTEX, {"vertex_id": vid, "dx": 40.0, "dy": 20.0})
    dto1, svg = generate_layout(egi, deltas=[d])

    after = dto1.vertex_positions[vid]
    assert after.x == pytest.approx(before.x + 40.0)
    assert after.y == pytest.approx(before.y + 20.0)
    assert "<svg" in svg
