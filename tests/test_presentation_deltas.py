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
    record_delta,
    apply_deltas,
    delta_key,
    merge_inherited,
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
