"""``POST /api/area/at-point`` answers from the cut as drawn, not its bounding box.

Docket 6m (found 2026-09-25 while closing 6f). The route tested a click against
``dto.cut_bounds`` as a rectangle, but a cut is drawn as an inscribed ellipse
(oval styles) or a rounded rectangle (the default). So a click in a bounding-box
corner, which the picture shows on the sheet, was reported inside the cut and
negative. Charter principle 4: the picture never lies.

The authority is ``presentation_ops.point_in_cut``, the same containment test the
correspondence check (§3.3) uses. Each case pairs the corner (outside the curve,
inside the box) with the centre (inside both), so a route that always answered
"sheet" would fail too.
"""

from __future__ import annotations

import pytest

from egif_parser_dau import parse_egif

fastapi = pytest.importorskip("fastapi", reason="needs the 'web' extra")
from fastapi.testclient import TestClient  # noqa: E402

from layout_dto import Point  # noqa: E402
from presentation_ops import point_in_cut, resolve_cut_boundaries  # noqa: E402
from web_api.main import app  # noqa: E402
from web_api.services.layout_service import generate_layout  # noqa: E402
from web_api.services.session_manager import get_session_manager  # noqa: E402

STYLES = [None, "peirce-authentic@1.0", "sowa-compliant@1.0"]


@pytest.fixture
def client():
    return TestClient(app)


def _session(egif: str, style):
    egi = parse_egif(egif)
    dto, _ = generate_layout(egi, style_name=style)
    return get_session_manager().create_session(egi, dto), egi, dto


def _at(client, session_id, p: Point) -> dict:
    body = client.post(
        "/api/area/at-point", json={"session_id": session_id, "x": p.x, "y": p.y}
    ).json()
    assert body["success"], body
    return body["data"]


def _drawn(dto, cid, p: Point) -> bool:
    return point_in_cut(
        p, dto.cut_bounds[cid], dto.style.cut_shape,
        float(dto.style.cut_corner_radius or 0), resolve_cut_boundaries(dto).get(cid),
    )


def _only_cut(egi):
    (cut,) = egi.Cut
    return cut.id


@pytest.mark.parametrize("style", STYLES)
def test_a_bbox_corner_outside_the_drawn_curve_is_the_sheet(client, style):
    sid, egi, dto = _session('(P "a") ~[ (Q "a") ]', style)
    cid = _only_cut(egi)
    b = dto.cut_bounds[cid]
    corner = Point(b.min_x + 0.5, b.min_y + 0.5)
    assert not _drawn(dto, cid, corner), "fixture: the corner must lie outside the curve"

    data = _at(client, sid, corner)
    assert data["area_id"] == egi.sheet
    assert data["polarity"] == "positive"


@pytest.mark.parametrize("style", STYLES)
def test_the_centre_of_a_cut_is_the_cut(client, style):
    sid, egi, dto = _session('(P "a") ~[ (Q "a") ]', style)
    cid = _only_cut(egi)
    b = dto.cut_bounds[cid]
    centre = Point((b.min_x + b.max_x) / 2, (b.min_y + b.max_y) / 2)

    data = _at(client, sid, centre)
    assert data["area_id"] == cid
    assert data["polarity"] == "negative"


@pytest.mark.parametrize("style", STYLES)
def test_inner_bbox_corner_inside_the_outer_curve_is_the_outer_cut(client, style):
    """Nesting: the deepest cut whose *drawn curve* holds the point, not whose box does."""
    sid, egi, dto = _session('~[ (P "a") ~[ (Q "a") ] ]', style)
    parent = {c.id: None for c in egi.Cut}
    for area, members in egi.area.items():
        for m in members:
            if m in parent:
                parent[m] = area
    inner = next(c for c, p in parent.items() if p != egi.sheet)
    outer = parent[inner]
    b = dto.cut_bounds[inner]
    corner = Point(b.min_x + 0.5, b.min_y + 0.5)
    assert not _drawn(dto, inner, corner), "fixture: outside the inner curve"
    assert _drawn(dto, outer, corner), "fixture: inside the outer curve"

    data = _at(client, sid, corner)
    assert data["area_id"] == outer
    assert data["polarity"] == "negative"
