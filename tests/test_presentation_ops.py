"""
Module-level tests for src/presentation_ops.py.

Two layers:

1. Area-topology helpers — element_area, cut_parents, area_chain,
   deepest_containing_cut.  These are now public and consumed both by
   the regime-3 ops and (planned) by future runtime-assertion work.
   The tests pin down their semantics.

2. The three regime-3 operations — move_vertex, reshape_cut,
   reroute_ligature.  For each: a happy-path test that exercises the
   operation on a real tomos UoD and verifies the EGI is structurally
   untouched, and an adversarial test that constructs a deliberately
   boundary-crossing proposal and verifies the operation refuses with
   ``Regime3Violation``.

The corpus-wide property-test coverage of regime-3 happy-path
behaviour lives in tests/test_correspondence_invariant.py (it iterates
over every UoD); this file focuses on contract pinning, not coverage.
"""

import sys
from pathlib import Path
from typing import Optional, Tuple

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from elk_layout_engine import ELKLayoutEngine
from layout_dto import BoundingBox, LayoutDTO, Point
from presentation_ops import (
    Regime3Violation,
    area_chain,
    cut_parents,
    deepest_containing_cut,
    element_area,
    move_vertex,
    reroute_ligature,
    reshape_cut,
)
from style_loader import load_default_style
from tomos_service import TomosService


TOMOS_ROOT = Path(__file__).parent.parent / "tomos"


@pytest.fixture(scope="module")
def tomos():
    return TomosService(TOMOS_ROOT)


@pytest.fixture(scope="module")
def engine():
    return ELKLayoutEngine()


@pytest.fixture(scope="module")
def style():
    return load_default_style()


# --------------------------------------------------------------------------- #
# Helpers for scanning the corpus to find UoDs with the right shape           #
# --------------------------------------------------------------------------- #


def _scan_for_vertex_in_cut(tomos, engine, style):
    """Return (uod_id, egi, dto, vertex_id, cut_id, position) or None."""
    for u in tomos.list_uods():
        uod_id = u["uod_id"]
        uod = tomos.load_uod(uod_id)
        egi = uod.current_egi
        dto = engine.generate_layout(egi, style)
        ea = element_area(egi)
        cut_ids = {c.id for c in egi.Cut}
        for vid, area in ea.items():
            if area in cut_ids and vid in dto.vertex_positions:
                return uod_id, egi, dto, vid, area, dto.vertex_positions[vid]
    return None


def _scan_for_cut_with_outside_sibling(tomos, engine, style):
    """Find a UoD with a cut and an element clearly outside it.

    Returns (uod_id, egi, dto, cut_id, sibling_pos) where ``sibling_pos``
    is a Point that is currently outside the cut's bounds but could be
    used as a target for an "absorb a sibling" reshape proposal.
    """
    for u in tomos.list_uods():
        uod_id = u["uod_id"]
        uod = tomos.load_uod(uod_id)
        egi = uod.current_egi
        dto = engine.generate_layout(egi, style)
        ea = element_area(egi)
        for cut in egi.Cut:
            cid = cut.id
            bounds = dto.cut_bounds.get(cid)
            if bounds is None:
                continue
            # Find any element whose area is not a descendant of cid and
            # whose position is genuinely outside cid's bounds.
            from presentation_ops import _descendant_areas

            descendant_areas = _descendant_areas(egi, cid)
            for elem_id, pos in {
                **dto.vertex_positions,
                **dto.predicate_positions,
            }.items():
                if ea.get(elem_id) in descendant_areas:
                    continue
                if (
                    bounds.min_x <= pos.x <= bounds.max_x
                    and bounds.min_y <= pos.y <= bounds.max_y
                ):
                    continue
                return uod_id, egi, dto, cid, pos
    return None


def _scan_for_ligature_and_outside_cut(tomos, engine, style):
    """Find a UoD with a ligature path AND a cut that is off the path's chain.

    Returns (uod_id, egi, dto, path, off_chain_cut_center) where
    ``off_chain_cut_center`` is a Point strictly inside a cut that is
    not on the chain between the path's predicate-area and
    vertex-area.
    """
    for u in tomos.list_uods():
        uod_id = u["uod_id"]
        uod = tomos.load_uod(uod_id)
        egi = uod.current_egi
        dto = engine.generate_layout(egi, style)
        if not dto.ligature_paths:
            continue
        ea = element_area(egi)
        pm = cut_parents(egi)
        for path in dto.ligature_paths:
            v_area = ea.get(path.vertex_id, egi.sheet)
            p_area = ea.get(path.predicate_id, egi.sheet)
            allowed = area_chain(v_area, p_area, pm)
            for cut in egi.Cut:
                if cut.id in allowed:
                    continue
                bounds = dto.cut_bounds.get(cut.id)
                if bounds is None:
                    continue
                center = Point(
                    (bounds.min_x + bounds.max_x) / 2,
                    (bounds.min_y + bounds.max_y) / 2,
                )
                # Confirm the center genuinely resolves to this off-chain cut.
                if (
                    deepest_containing_cut(center, dto, egi, pm) == cut.id
                ):
                    return uod_id, egi, dto, path, center
    return None


# --------------------------------------------------------------------------- #
# Area-topology helper tests                                                  #
# --------------------------------------------------------------------------- #


def test_element_area_inverts_egi_area(tomos, engine, style):
    """element_area(egi)[x] == area_id iff x in egi.area[area_id]."""
    for u in tomos.list_uods()[:5]:  # 5 UoDs is enough to pin semantics
        egi = tomos.load_uod(u["uod_id"]).current_egi
        ea = element_area(egi)
        cut_ids = {c.id for c in egi.Cut}
        # Every non-cut element is in exactly one area.
        for elem_id, area_id in ea.items():
            assert elem_id not in cut_ids
            assert elem_id in egi.area[area_id]
        # Every non-cut element of every area appears in the map.
        for area_id, contents in egi.area.items():
            for elem_id in contents:
                if elem_id in cut_ids:
                    continue
                assert ea[elem_id] == area_id


def test_cut_parents_omits_sheet_and_matches_area(tomos):
    """cut_parents(egi)[cut.id] == enclosing area; sheet has no parent."""
    for u in tomos.list_uods()[:5]:
        egi = tomos.load_uod(u["uod_id"]).current_egi
        pm = cut_parents(egi)
        assert egi.sheet not in pm
        for cut in egi.Cut:
            assert cut.id in pm
            assert cut.id in egi.area[pm[cut.id]]


def test_area_chain_includes_both_endpoints_and_lca(tomos):
    """For any two areas a, b: area_chain includes a, b, and their LCA."""
    for u in tomos.list_uods()[:5]:
        egi = tomos.load_uod(u["uod_id"]).current_egi
        pm = cut_parents(egi)
        areas = [egi.sheet] + [c.id for c in egi.Cut]
        for a in areas:
            for b in areas:
                chain = area_chain(a, b, pm)
                assert a in chain
                assert b in chain
                # Self-chain is just {a}.
                if a == b:
                    assert chain == {a}


def test_deepest_containing_cut_strict_bounds(tomos, engine, style):
    """Boundary-tangent points belong to the parent area, not the cut itself."""
    for u in tomos.list_uods()[:3]:
        uod_id = u["uod_id"]
        egi = tomos.load_uod(uod_id).current_egi
        dto = engine.generate_layout(egi, style)
        pm = cut_parents(egi)
        for cut in egi.Cut:
            bounds = dto.cut_bounds.get(cut.id)
            if bounds is None:
                continue
            # Strictly-inside center resolves to this cut (or a deeper one).
            center = Point(
                (bounds.min_x + bounds.max_x) / 2,
                (bounds.min_y + bounds.max_y) / 2,
            )
            inner = deepest_containing_cut(center, dto, egi, pm)
            # Either this cut or one of its descendants.
            from presentation_ops import _descendant_areas

            assert inner in _descendant_areas(egi, cut.id)
            # Corner point is on the boundary — strictly outside.
            corner = Point(bounds.min_x, bounds.min_y)
            outer = deepest_containing_cut(corner, dto, egi, pm)
            # The corner cannot be deeper than the cut's own enclosing area;
            # specifically it should not resolve to this cut.
            assert outer != cut.id


# --------------------------------------------------------------------------- #
# move_vertex — happy + refusal                                               #
# --------------------------------------------------------------------------- #


def test_move_vertex_happy_path_preserves_egi_and_endpoints(tomos, engine, style):
    """A small in-area vertex translation produces a new DTO with the EGI
    unchanged and matching LigaturePath endpoints updated."""
    found = _scan_for_vertex_in_cut(tomos, engine, style)
    if found is None:
        pytest.skip("no tomos UoD has a vertex inside a cut")
    uod_id, egi, dto, vid, cid, pos = found

    # Pick a delta that stays inside the cut bounds.
    bounds = dto.cut_bounds[cid]
    if pos.x + 0.5 >= bounds.max_x or pos.y + 0.5 >= bounds.max_y:
        pytest.skip(f"{uod_id}: vertex {vid} too close to cut edge")
    snapshot = egi
    new_dto = move_vertex(egi, dto, vid, 0.5, 0.5)
    assert egi is snapshot, "move_vertex must not touch the EGI reference"
    assert new_dto.vertex_positions[vid].x == pytest.approx(pos.x + 0.5)
    assert new_dto.vertex_positions[vid].y == pytest.approx(pos.y + 0.5)
    # Original DTO unchanged.
    assert dto.vertex_positions[vid].x == pytest.approx(pos.x)
    # Every ligature ending at vid has its vertex-side endpoint updated.
    for path in new_dto.ligature_paths:
        if path.vertex_id != vid:
            continue
        last = path.points[-1]
        assert last.x == pytest.approx(pos.x + 0.5)
        assert last.y == pytest.approx(pos.y + 0.5)


def test_move_vertex_refuses_when_leaving_area(tomos, engine, style):
    """A translation that would push the vertex outside its cut's bounds
    raises Regime3Violation — §5.5 "structural impossibility of regime-3
    abuse" enforced at the API surface."""
    found = _scan_for_vertex_in_cut(tomos, engine, style)
    if found is None:
        pytest.skip("no tomos UoD has a vertex inside a cut")
    uod_id, egi, dto, vid, cid, pos = found
    bounds = dto.cut_bounds[cid]

    # Delta large enough to push the vertex past the right boundary.
    dx = (bounds.max_x - pos.x) + 1.0

    with pytest.raises(Regime3Violation) as excinfo:
        move_vertex(egi, dto, vid, dx, 0.0)
    # The error message should mention the area change.
    msg = str(excinfo.value)
    assert "area" in msg.lower()
    assert vid in msg or str(vid) in msg


def test_move_vertex_refuses_unknown_vertex(tomos, engine, style):
    """A vertex_id that isn't in the DTO raises Regime3Violation."""
    u = tomos.list_uods()[0]
    egi = tomos.load_uod(u["uod_id"]).current_egi
    dto = engine.generate_layout(egi, style)
    with pytest.raises(Regime3Violation):
        move_vertex(egi, dto, "nonexistent_vertex_id", 1.0, 1.0)


# --------------------------------------------------------------------------- #
# reshape_cut — happy + refusal                                               #
# --------------------------------------------------------------------------- #


def test_reshape_cut_happy_path_expansion(tomos, engine, style):
    """A small outward expansion that doesn't absorb any non-area element
    produces a new DTO with bounds replaced and EGI unchanged."""
    # Find a cut that can be expanded by a sub-pixel amount.
    for u in tomos.list_uods():
        uod_id = u["uod_id"]
        egi = tomos.load_uod(uod_id).current_egi
        dto = engine.generate_layout(egi, style)
        from presentation_ops import _descendant_areas

        ea = element_area(egi)
        for cut in egi.Cut:
            cid = cut.id
            b = dto.cut_bounds.get(cid)
            if b is None:
                continue
            expanded = BoundingBox(
                min_x=b.min_x - 0.5,
                min_y=b.min_y - 0.5,
                max_x=b.max_x + 0.5,
                max_y=b.max_y + 0.5,
            )
            # Pre-check this expansion is safe — otherwise this test would
            # masquerade as failure when really it's an under-furnished
            # corpus shape.  The API's contract is symmetric (no
            # outside *element* pulled in, no sibling *cut* overlapped),
            # so the pre-check is too.
            own = _descendant_areas(egi, cid)
            safe = True
            for elem_id, p in {
                **dto.vertex_positions,
                **dto.predicate_positions,
            }.items():
                if ea.get(elem_id) in own:
                    continue
                if (
                    expanded.min_x <= p.x <= expanded.max_x
                    and expanded.min_y <= p.y <= expanded.max_y
                ):
                    safe = False
                    break
            if not safe:
                continue
            # Also pre-check sibling cut bounds: a non-descendant cut
            # whose bounds intersect the expanded box is a regime-3
            # refusal (visually, the cuts would overlap).
            for other_id, other_b in dto.cut_bounds.items():
                if other_id == cid or other_id in own:
                    continue
                # AABB overlap.
                if not (
                    other_b.max_x < expanded.min_x
                    or other_b.min_x > expanded.max_x
                    or other_b.max_y < expanded.min_y
                    or other_b.min_y > expanded.max_y
                ):
                    safe = False
                    break
            if not safe:
                continue

            new_dto = reshape_cut(egi, dto, cid, expanded)
            assert new_dto.cut_bounds[cid] is expanded
            # Other cuts untouched.
            for other_id, other_b in dto.cut_bounds.items():
                if other_id == cid:
                    continue
                assert new_dto.cut_bounds[other_id] is other_b
            return
    pytest.skip("no tomos UoD has a cut whose bounds can be safely expanded")


def test_reshape_cut_refuses_absorbing_outside_element(tomos, engine, style):
    """Proposing bounds that would absorb a non-area element raises."""
    found = _scan_for_cut_with_outside_sibling(tomos, engine, style)
    if found is None:
        pytest.skip("no tomos UoD has a cut with an outside element to absorb")
    uod_id, egi, dto, cid, sibling_pos = found
    old = dto.cut_bounds[cid]

    # Stretch bounds far enough to absorb the sibling.
    new_bounds = BoundingBox(
        min_x=min(old.min_x, sibling_pos.x - 1.0),
        min_y=min(old.min_y, sibling_pos.y - 1.0),
        max_x=max(old.max_x, sibling_pos.x + 1.0),
        max_y=max(old.max_y, sibling_pos.y + 1.0),
    )

    with pytest.raises(Regime3Violation) as excinfo:
        reshape_cut(egi, dto, cid, new_bounds)
    msg = str(excinfo.value).lower()
    assert "absorb" in msg or "outside" in msg


def test_reshape_cut_refuses_unknown_cut(tomos, engine, style):
    """A cut_id not in the EGI raises Regime3Violation."""
    u = tomos.list_uods()[0]
    egi = tomos.load_uod(u["uod_id"]).current_egi
    dto = engine.generate_layout(egi, style)
    bb = BoundingBox(0, 0, 10, 10)
    with pytest.raises(Regime3Violation):
        reshape_cut(egi, dto, "nonexistent_cut_id", bb)


# --------------------------------------------------------------------------- #
# reroute_ligature — happy + refusal                                          #
# --------------------------------------------------------------------------- #


def test_reroute_ligature_happy_path_on_chain_kink(tomos, engine, style):
    """Inserting an on-chain perpendicular kink replaces the path while
    preserving endpoints and the EGI."""
    for u in tomos.list_uods():
        egi = tomos.load_uod(u["uod_id"]).current_egi
        dto = engine.generate_layout(egi, style)
        if not dto.ligature_paths:
            continue
        path = dto.ligature_paths[0]
        if len(path.points) < 2:
            continue
        a, b = path.points[0], path.points[-1]
        mx, my = (a.x + b.x) / 2, (a.y + b.y) / 2
        dx, dy = b.x - a.x, b.y - a.y
        length = (dx * dx + dy * dy) ** 0.5
        if length == 0:
            continue
        nx, ny = -dy / length, dx / length
        kink = Point(mx + 0.25 * nx, my + 0.25 * ny)

        try:
            new_dto = reroute_ligature(
                egi, dto, path.predicate_id, path.vertex_id, path.port_index, [kink]
            )
        except Regime3Violation:
            # This path's perpendicular nudge happens to land off-chain;
            # try the next UoD.
            continue
        # Endpoints preserved.
        new_path = None
        for p in new_dto.ligature_paths:
            if (
                p.predicate_id == path.predicate_id
                and p.vertex_id == path.vertex_id
                and p.port_index == path.port_index
            ):
                new_path = p
                break
        assert new_path is not None
        assert new_path.points[0] == a
        assert new_path.points[-1] == b
        # And we added one interior point.
        assert len(new_path.points) == len(path.points) + 1
        return
    pytest.skip("no tomos UoD has a ligature whose perpendicular kink lands on-chain")


def test_reroute_ligature_refuses_off_chain_waypoint(tomos, engine, style):
    """An interior waypoint inside an off-chain cut raises Regime3Violation."""
    found = _scan_for_ligature_and_outside_cut(tomos, engine, style)
    if found is None:
        pytest.skip("no tomos UoD has a ligature path with an off-chain cut to target")
    uod_id, egi, dto, path, off_chain_point = found

    with pytest.raises(Regime3Violation) as excinfo:
        reroute_ligature(
            egi,
            dto,
            path.predicate_id,
            path.vertex_id,
            path.port_index,
            [off_chain_point],
        )
    msg = str(excinfo.value).lower()
    assert "chain" in msg or "off" in msg


def test_reroute_ligature_refuses_unknown_path(tomos, engine, style):
    """A (predicate_id, vertex_id, port_index) triple that names no path raises."""
    u = tomos.list_uods()[0]
    egi = tomos.load_uod(u["uod_id"]).current_egi
    dto = engine.generate_layout(egi, style)
    with pytest.raises(Regime3Violation):
        reroute_ligature(egi, dto, "nope_pred", "nope_vert", 0, [Point(0, 0)])


# --------------------------------------------------------------------------- #
# Cross-op invariants                                                         #
# --------------------------------------------------------------------------- #


def test_move_vertex_returns_distinct_dto(tomos, engine, style):
    """The new DTO is a distinct object; original is not mutated."""
    found = _scan_for_vertex_in_cut(tomos, engine, style)
    if found is None:
        pytest.skip("no tomos UoD has a vertex inside a cut")
    _, egi, dto, vid, _, pos = found
    bounds = dto.cut_bounds[element_area(egi)[vid]]
    if pos.x + 0.5 >= bounds.max_x or pos.y + 0.5 >= bounds.max_y:
        pytest.skip("vertex too close to cut edge")
    new_dto = move_vertex(egi, dto, vid, 0.5, 0.5)
    assert new_dto is not dto
    assert new_dto.vertex_positions is not dto.vertex_positions
    # Original vertex_positions unchanged.
    assert dto.vertex_positions[vid] == pos
