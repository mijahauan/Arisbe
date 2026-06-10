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
    boxes_overlap,
    cut_parents,
    deepest_containing_cut,
    element_area,
    move_vertex,
    move_predicate,
    path_intersects_box,
    reroute_ligature,
    reshape_cut,
    move_cut,
    vertex_label_box,
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


# --------------------------------------------------------------------------- #
# move_predicate — happy + refusal (the predicate-side twin of move_vertex)    #
# --------------------------------------------------------------------------- #


def _egi_dto(egif, engine, style):
    from egif_parser_dau import parse_egif
    egi = parse_egif(egif)
    return egi, engine.generate_layout(egi, style)


def test_move_predicate_happy_path_follows_ligature_and_attests(engine, style):
    """Translating a predicate inside a cut updates its position, drags the
    ligature predicate-side endpoint with it, leaves the EGI untouched, and the
    result still passes §3.3 correspondence."""
    from correspondence_attestation import attest_correspondence

    egi, dto = _egi_dto("~[ (P *x) ]", engine, style)
    pid = next(iter(dto.predicate_positions))
    pos = dto.predicate_positions[pid]
    area = element_area(egi)[pid]
    bounds = dto.cut_bounds[area]
    if pos.x + 1.0 >= bounds.max_x or pos.y + 1.0 >= bounds.max_y:
        pytest.skip("predicate too close to cut edge for a safe nudge")

    # predicate-side endpoint (points[0]) of P's ligature, before.
    before_ends = {
        (lp.predicate_id, lp.vertex_id, lp.port_index): lp.points[0]
        for lp in dto.ligature_paths if lp.predicate_id == pid
    }
    snapshot = egi
    new_dto = move_predicate(egi, dto, pid, 1.0, 1.0)

    assert egi is snapshot
    assert new_dto is not dto
    assert new_dto.predicate_positions[pid].x == pytest.approx(pos.x + 1.0)
    assert new_dto.predicate_positions[pid].y == pytest.approx(pos.y + 1.0)
    assert dto.predicate_positions[pid] == pos  # original untouched
    for lp in new_dto.ligature_paths:
        if lp.predicate_id != pid:
            continue
        b = before_ends[(lp.predicate_id, lp.vertex_id, lp.port_index)]
        assert lp.points[0].x == pytest.approx(b.x + 1.0)
        assert lp.points[0].y == pytest.approx(b.y + 1.0)
    # The §3.3 backstop is satisfied — the move preserved correspondence.
    attest_correspondence(egi, new_dto, context="test_move_predicate")


def test_move_predicate_refuses_when_leaving_area(engine, style):
    """A translation large enough to push the predicate out of its cut raises
    Regime3Violation (a silent area change, not a regime-3 op)."""
    egi, dto = _egi_dto("~[ (P *x) ]", engine, style)
    pid = next(iter(dto.predicate_positions))
    pos = dto.predicate_positions[pid]
    bounds = dto.cut_bounds[element_area(egi)[pid]]
    dx = (bounds.max_x - pos.x) + 50.0
    with pytest.raises(Regime3Violation) as exc:
        move_predicate(egi, dto, pid, dx, 0.0)
    assert "area" in str(exc.value).lower()


def test_move_predicate_refuses_unknown_predicate(engine, style):
    egi, dto = _egi_dto("(P *x)", engine, style)
    with pytest.raises(Regime3Violation):
        move_predicate(egi, dto, "nonexistent_pred", 1.0, 1.0)


# --------------------------------------------------------------------------- #
# move_cut — rigid translation of a cut + everything it contains              #
# --------------------------------------------------------------------------- #


def test_move_cut_happy_path_translates_contents_and_attests(engine, style):
    """Moving a cut slides its bounds and every contained element together,
    leaves the EGI untouched, and still passes §3.3."""
    from correspondence_attestation import attest_correspondence

    # A cut with content, plus a sibling far enough away to clear a small move.
    egi, dto = _egi_dto("~[ (P *x) ] (Q *y)", engine, style)
    cid = next(iter(c.id for c in egi.Cut))
    ea = element_area(egi)
    inside = [eid for eid, a in ea.items() if a == cid]
    assert inside, "expected content inside the cut"
    cb = dto.cut_bounds[cid]
    before_inside = {
        eid: (dto.vertex_positions.get(eid) or dto.predicate_positions.get(eid))
        for eid in inside
    }

    dx, dy = -3.0, -3.0  # nudge up-left, away from the sibling Q
    snapshot = egi
    new_dto = move_cut(egi, dto, cid, dx, dy)

    assert egi is snapshot
    assert new_dto.cut_bounds[cid].min_x == pytest.approx(cb.min_x + dx)
    assert new_dto.cut_bounds[cid].max_y == pytest.approx(cb.max_y + dy)
    for eid, p in before_inside.items():
        np = new_dto.vertex_positions.get(eid) or new_dto.predicate_positions.get(eid)
        assert np.x == pytest.approx(p.x + dx)
        assert np.y == pytest.approx(p.y + dy)
    attest_correspondence(egi, new_dto, context="test_move_cut")


def test_move_cut_refuses_overlapping_sibling(engine, style):
    """Sliding a cut onto a sibling element/cut raises Regime3Violation (it
    would appear to absorb / collide with material it doesn't contain)."""
    egi, dto = _egi_dto("~[ (P *x) ] (Q *y)", engine, style)
    cid = next(iter(c.id for c in egi.Cut))
    cb = dto.cut_bounds[cid]
    # Find Q's position (the sheet-level sibling predicate) and aim the cut at it.
    ea = element_area(egi)
    sib = next(
        p for p, a in ea.items()
        if a != cid and p in dto.predicate_positions
    )
    qp = dto.predicate_positions[sib]
    cx = (cb.min_x + cb.max_x) / 2
    cy = (cb.min_y + cb.max_y) / 2
    with pytest.raises(Regime3Violation):
        move_cut(egi, dto, cid, qp.x - cx, qp.y - cy)


def test_move_cut_refuses_leaving_parent(engine, style):
    """An inner cut slid far enough to leave its enclosing cut raises
    Regime3Violation (a change of nesting depth)."""
    egi, dto = _egi_dto("~[ ~[ (P *x) ] ]", engine, style)
    # The inner cut is the one whose parent is another cut.
    pm = cut_parents(egi)
    inner = next(cid for cid, parent in pm.items() if parent in {c.id for c in egi.Cut})
    outer = pm[inner]
    span = dto.cut_bounds[outer].max_x - dto.cut_bounds[outer].min_x
    with pytest.raises(Regime3Violation):
        move_cut(egi, dto, inner, span + 100.0, 0.0)


def test_move_cut_refuses_unknown_cut(engine, style):
    egi, dto = _egi_dto("~[ (P *x) ]", engine, style)
    with pytest.raises(Regime3Violation):
        move_cut(egi, dto, "nonexistent_cut", 1.0, 1.0)


# --------------------------------------------------------------------------- #
# rebuild_ligature_anchors — the attachment point is derived, not stored       #
# --------------------------------------------------------------------------- #


def test_rebuild_anchors_follows_vertex_after_move(engine, style):
    """After a vertex move, re-deriving anchors slides the predicate hook to
    face the line's new incident direction — the bug 'the attachment point on
    the predicate did not change' is fixed by recomputing, not dragging."""
    egi, dto = _egi_dto("(P *x)", engine, style)
    vid = next(iter(dto.vertex_positions))
    hook_before = dto.ligature_paths[0].points[0]

    moved = move_vertex(egi, dto, vid, 0.0, 120.0)         # push vertex far down
    assert moved.ligature_paths[0].points[0] == hook_before  # rigid: hook frozen

    re = engine.rebuild_ligature_anchors(egi, moved)
    hook_after = re.ligature_paths[0].points[0]
    assert hook_after.y != pytest.approx(hook_before.y)      # hook moved to face it
    assert re.ligature_paths[0].points[-1].y == pytest.approx(
        moved.vertex_positions[vid].y)                        # vertex end pinned


def test_rebuild_anchors_idempotent_on_fresh_layout(engine, style):
    """On an unedited layout the hook is already the perimeter anchor, so
    re-deriving changes nothing (same derive rule as the cold layout)."""
    egi, dto = _egi_dto("(P *x) (Q *y)", engine, style)
    re = engine.rebuild_ligature_anchors(egi, dto)
    for a, b in zip(dto.ligature_paths, re.ligature_paths):
        assert a.points[0].x == pytest.approx(b.points[0].x)
        assert a.points[0].y == pytest.approx(b.points[0].y)
        assert a.points[-1].x == pytest.approx(b.points[-1].x)


def test_rebuild_anchors_preserves_reroute_interior(engine, style):
    """An explicit reroute waypoint survives a re-anchor — only the endpoints
    are recomputed."""
    egi, dto = _egi_dto("(P *x)", engine, style)
    lp = dto.ligature_paths[0]
    mid = Point((lp.points[0].x + lp.points[-1].x) / 2,
                (lp.points[0].y + lp.points[-1].y) / 2 + 8.0)
    routed = reroute_ligature(egi, dto, lp.predicate_id, lp.vertex_id,
                              lp.port_index, [mid])
    re = engine.rebuild_ligature_anchors(egi, routed)
    # The interior waypoint is unchanged; the path still has 3 points.
    assert len(re.ligature_paths[0].points) == 3
    assert re.ligature_paths[0].points[1].x == pytest.approx(mid.x)
    assert re.ligature_paths[0].points[1].y == pytest.approx(mid.y)


def test_layout_direction_is_a_style_knob(engine, style):
    """layout.direction (the reading axis) is honored: sibling-heavy structure
    stacks vertically under RIGHT and spreads horizontally under DOWN."""
    import dataclasses
    egi = __import__("egif_parser_dau").parse_egif("(P *x) (Q *y) (R *z) (S *w)")
    right = engine.generate_layout(egi, dataclasses.replace(style, layout_direction="RIGHT"))
    down = engine.generate_layout(egi, dataclasses.replace(style, layout_direction="DOWN"))

    def ratio(dto):
        vb = dto.viewport_bounds
        return (vb.max_y - vb.min_y) / (vb.max_x - vb.min_x)

    assert ratio(right) > 1.0   # tall (siblings stacked on the vertical axis)
    assert ratio(down) < 1.0    # wide (siblings spread left-to-right)


# --- exact containment: rounded-rect corner void (docs/EXACT_CORRESPONDENCE.md) --- #
#
# The cut "inside" must be the shape the renderer draws. A Dau cut is a
# <rect rx=corner_radius>, so its rounded-away corners are NOT inside it — a mark
# parked there reads outside, matching the eye. Phase 1: point_in_cut /
# bounds_in_cut take the corner radius and test the rounded rectangle exactly.

def test_point_in_cut_excludes_the_rounded_corner_void():
    from presentation_ops import point_in_cut
    b = BoundingBox(0, 0, 100, 100)
    r = 20.0
    # Deep in a corner triangle (within the box, outside the rounded curve).
    corner = Point(3, 3)
    assert point_in_cut(corner, b, "rounded_rectangle", 0.0) is True   # box proxy: inside
    assert point_in_cut(corner, b, "rounded_rectangle", r) is False     # rounded: outside
    # The corner's arc center stays inside; the box interior is unaffected.
    assert point_in_cut(Point(r, r), b, "rounded_rectangle", r) is True
    assert point_in_cut(Point(50, 50), b, "rounded_rectangle", r) is True
    # A point on a straight edge (away from corners) is still inside.
    assert point_in_cut(Point(50, 1), b, "rounded_rectangle", r) is True


def test_bounds_in_cut_rounded_rejects_a_child_poking_into_a_corner():
    from presentation_ops import bounds_in_cut
    outer = BoundingBox(0, 0, 100, 100)
    r = 20.0
    # A child whose own corner sits in the parent's rounded-away corner triangle.
    poking = BoundingBox(2, 2, 40, 40)
    assert bounds_in_cut(poking, outer, "rounded_rectangle", 0.0) is True    # box proxy
    assert bounds_in_cut(poking, outer, "rounded_rectangle", r) is False      # rounded: not contained
    # A child kept clear of the corners is contained either way.
    clear = BoundingBox(30, 30, 70, 70)
    assert bounds_in_cut(clear, outer, "rounded_rectangle", r) is True


# --- exact crossing: the corner graze is not a crossing (EXACT_CORRESPONDENCE Phase 2) --- #
#
# Phase 1 made *containment* read off the rounded curve. Phase 2 makes *crossing*
# read off the same curve, so a ligature that clips a rounded-away corner is counted
# as the eye sees it — outside the cut — not as a spurious entry. count_cut_crossings
# takes the corner radius and tests the rounded rectangle the renderer draws.

def test_count_cut_crossings_ignores_a_rounded_corner_graze():
    from presentation_ops import count_cut_crossings
    b = BoundingBox(0, 0, 100, 100)
    r = 20.0
    # A segment that clips the top-left square corner: it crosses the box's left and
    # top edges (entering at (0,5), leaving at (5,0)) but stays out in the corner
    # triangle, clear of the rounded arc.
    graze = [Point(-5, 10), Point(10, -5)]
    assert count_cut_crossings(graze, b, "rounded_rectangle", 0.0) == 2   # square box: enters + exits
    assert count_cut_crossings(graze, b, "rounded_rectangle", r) == 0     # rounded: never inside


def test_count_cut_crossings_rounded_straddle_and_passthrough():
    from presentation_ops import count_cut_crossings
    b = BoundingBox(0, 0, 100, 100)
    r = 20.0
    # One endpoint inside, one outside → exactly one boundary crossing.
    straddle = [Point(50, 50), Point(50, -10)]
    assert count_cut_crossings(straddle, b, "rounded_rectangle", r) == 1
    # Both endpoints outside, a clean vertical pass through the middle → two.
    through = [Point(50, -10), Point(50, 110)]
    assert count_cut_crossings(through, b, "rounded_rectangle", r) == 2
    # A predicate-to-vertex line that legitimately enters once and stops inside.
    entering = [Point(50, -10), Point(50, 40)]
    assert count_cut_crossings(entering, b, "rounded_rectangle", r) == 1


# --- exact extent: a predicate is a label box, not a point (EXACT_CORRESPONDENCE Phase 3) --- #
#
# §3.3 reads a predicate's containment off the drawn label box. predicate_label_box
# is the single source of truth — the same box the renderer draws — so the box may
# not straddle a cut boundary.

class _FakeStyle:
    predicate_char_width = 8.0
    predicate_height = 20.0


def test_predicate_label_box_matches_the_drawn_formula():
    from presentation_ops import predicate_label_box
    box = predicate_label_box("loves", Point(100, 50), _FakeStyle())
    # width = len*char_width + 2*pad_h (2) ; height = predicate_height + 2*pad_v (1)
    assert (box.max_x - box.min_x) == 5 * 8.0 + 4.0
    assert (box.max_y - box.min_y) == 20.0 + 2.0
    # Centred on the anchor.
    assert (box.min_x + box.max_x) / 2 == 100
    assert (box.min_y + box.max_y) / 2 == 50


def test_predicate_label_box_defaults_when_style_is_none():
    from presentation_ops import predicate_label_box
    box = predicate_label_box("P", Point(0, 0), None)  # falls back to defaults
    assert box.max_x > box.min_x and box.max_y > box.min_y


def test_box_intrudes_cut_detects_a_straddle():
    from presentation_ops import box_intrudes_cut
    cut = BoundingBox(0, 0, 100, 100)
    # Box overlapping the left edge — a corner inside the cut → intrudes.
    straddling = BoundingBox(-10, 40, 10, 60)
    assert box_intrudes_cut(straddling, cut, "rounded_rectangle", 0.0) is True
    # Box wholly outside → no intrusion.
    outside = BoundingBox(-30, 40, -10, 60)
    assert box_intrudes_cut(outside, cut, "rounded_rectangle", 0.0) is False
    # Box engulfing the cut (cut corners inside the box) → intrudes.
    engulfing = BoundingBox(-10, -10, 110, 110)
    assert box_intrudes_cut(engulfing, cut, "rounded_rectangle", 0.0) is True


def test_boxes_overlap_positive_area_only():
    """Phase 3b: text-on-text overlap is positive-area; a shared edge or corner
    (abutting labels) is still legible and does not count."""
    a = BoundingBox(0, 0, 10, 10)
    assert boxes_overlap(a, BoundingBox(5, 5, 15, 15)) is True   # genuine overlap
    assert boxes_overlap(a, BoundingBox(10, 0, 20, 10)) is False  # abutting edge
    assert boxes_overlap(a, BoundingBox(10, 10, 20, 20)) is False  # corner touch
    assert boxes_overlap(a, BoundingBox(20, 0, 30, 10)) is False  # disjoint


def test_path_intersects_box_interior_not_border():
    """Phase 3b primitive (the obstacle test the deferred ligature-routing task will
    use): a polyline passing through a box's interior counts; one merely touching the
    border does not."""
    box = BoundingBox(0, 0, 10, 10)
    # Straight segment through the middle.
    assert path_intersects_box([Point(-5, 5), Point(15, 5)], box) is True
    # Endpoint strictly inside.
    assert path_intersects_box([Point(5, 5), Point(20, 20)], box) is True
    # Running along the top edge — touches, not interior.
    assert path_intersects_box([Point(-5, 0), Point(15, 0)], box) is False
    # Passing clear of the box.
    assert path_intersects_box([Point(-5, 20), Point(15, 20)], box) is False


def test_vertex_label_box_is_cut_aware(tomos, engine, style):
    """Phase 3b: cut-aware placement keeps a constant's label inside its area cut
    when a direction fits.  A cut large enough for the label in some direction yields
    a box wholly inside it; a cut too small in every direction falls back to the free
    placement (which §3.3 then flags), so the helper never silently hides a cramped
    layout."""
    from egif_parser_dau import parse_egif
    from presentation_ops import bounds_in_cut

    egi = parse_egif('~[ (Human "Socrates") ]')
    (cut_id,) = [c.id for c in egi.Cut]
    (vid,) = [v.id for v in egi.V]
    dto = engine.generate_layout(egi, style)
    shape = getattr(style, "cut_shape", "rounded_rectangle")
    radius = float(getattr(style, "cut_corner_radius", 0) or 0)

    # Engine layout: cut-aware box lies wholly inside the cut.
    box = vertex_label_box("Socrates", dto.vertex_positions[vid], style,
                           dto.ligature_paths, vid, egi=egi,
                           cut_bounds=dto.cut_bounds)
    assert bounds_in_cut(box, dto.cut_bounds[cut_id], shape, radius)

    # Shrink the cut below the label in every direction: placement can't fit, so it
    # returns the free box (which then straddles) rather than pretending it fits.
    vp = dto.vertex_positions[vid]
    tiny = {**dto.cut_bounds, cut_id: BoundingBox(vp.x - 4, vp.y - 4,
                                                  vp.x + 4, vp.y + 4)}
    cramped = vertex_label_box("Socrates", vp, style, dto.ligature_paths, vid,
                               egi=egi, cut_bounds=tiny)
    assert not bounds_in_cut(cramped, tiny[cut_id], shape, radius)
