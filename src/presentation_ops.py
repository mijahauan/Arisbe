"""
Presentation-only (regime-3) operations over a (EGI, LayoutDTO) pair.

This module implements the closed algebra over the projection that
docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md §4.3 and §5.5 require: a user
may freely reposition a vertex, reshape a cut, or reroute a ligature
*as long as* the EGI is untouched and the resulting drawing remains in
correspondence with it.

The three operations exposed here — ``move_vertex``, ``reshape_cut``,
``reroute_ligature`` — take an EGI and a LayoutDTO and return a *new*
LayoutDTO.  They never mutate the EGI.  They refuse (by raising
``Regime3Violation``) any proposal that would cross a regime boundary:

- a vertex translation that would push the vertex outside its current
  area;
- a cut reshape that would change which elements are geometrically
  inside the cut (the §5.5 interior-preservation rule);
- a ligature reroute whose new interior points or segment midpoints
  would leave the area chain between predicate-area and vertex-area
  (changes W-realisation).

These refusals are the "structural impossibility of regime-3 abuse"
from §5.5: an ill-defined operation is not detected after the fact, it
is refused at the API surface.

Four area-topology helpers are also exposed publicly:

- ``element_area`` — inverse of ``egi.area``: element_id -> area_id
- ``cut_parents`` — area-tree parent map: cut_id -> enclosing area_id
- ``area_chain`` — set of areas on the path between two areas in the
  area tree (inclusive of endpoints and LCA)
- ``deepest_containing_cut`` — deepest-by-depth cut whose bounds
  strictly contain a point; returns ``egi.sheet`` if none.

These are duplicated across several test files today (correspondence
invariant tests, ELK ligature edge-case tests).  Consolidating them
here gives both this module and future runtime-assertion work a
canonical home.
"""

from typing import Dict, Iterable, Optional, Set, Tuple

from egi_core_dau import ElementID, RelationalGraphWithCuts
from layout_dto import BoundingBox, LayoutDTO, LigaturePath, Point


class Regime3Violation(ValueError):
    """Raised when a proposed regime-3 op would cross a regime boundary.

    A regime-3 operation is, by definition, one whose effect on the
    (EGI, projection) pair is restricted to the projection component.
    A proposal that would change area membership, alter the W-partition
    on the drawing, or otherwise touch structural data is not a
    regime-3 op — it is refused at the API surface.
    """


# --------------------------------------------------------------------------- #
# Area-topology helpers (public)                                              #
# --------------------------------------------------------------------------- #


def element_area(egi: RelationalGraphWithCuts) -> Dict[ElementID, ElementID]:
    """Inverse of ``egi.area``: each vertex and edge ID -> its area ID.

    Cuts are omitted (they *are* areas; their parent area is in
    ``cut_parents``).
    """
    cut_ids = {c.id for c in egi.Cut}
    result: Dict[ElementID, ElementID] = {}
    for area_id, contents in egi.area.items():
        for elem_id in contents:
            if elem_id not in cut_ids:
                result[elem_id] = area_id
    return result


def cut_parents(egi: RelationalGraphWithCuts) -> Dict[ElementID, ElementID]:
    """Area-tree parent map: each cut ID -> the area that encloses it.

    The sheet has no parent and is omitted from the result.
    """
    cut_ids = {c.id for c in egi.Cut}
    result: Dict[ElementID, ElementID] = {}
    for area_id, contents in egi.area.items():
        for elem_id in contents:
            if elem_id in cut_ids:
                result[elem_id] = area_id
    return result


def area_chain(
    a: ElementID,
    b: ElementID,
    parent_map: Dict[ElementID, ElementID],
) -> Set[ElementID]:
    """Return the set of areas on the path from ``a`` to ``b`` in the area tree.

    The path goes a -> ancestors -> LCA -> ... -> b.  Both endpoints
    and the LCA are included.  ``parent_map.get(sheet)`` is None — the
    sheet is the tree's root.
    """
    anc_a: list = []
    cur: Optional[ElementID] = a
    while cur is not None:
        anc_a.append(cur)
        cur = parent_map.get(cur)
    anc_a_set = set(anc_a)
    chain_b: list = []
    cur = b
    while cur is not None and cur not in anc_a_set:
        chain_b.append(cur)
        cur = parent_map.get(cur)
    if cur is None:
        # Disjoint trees — should not happen with a single sheet root.
        return set(chain_b) | anc_a_set
    idx = anc_a.index(cur)
    return set(chain_b) | set(anc_a[: idx + 1])


def deepest_containing_cut(
    point: Point,
    dto: LayoutDTO,
    egi: RelationalGraphWithCuts,
    parent_map: Optional[Dict[ElementID, ElementID]] = None,
) -> ElementID:
    """Deepest-by-depth cut whose bounds strictly contain ``point``.

    Strict bounds (< not ≤) treat boundary-tangent points as outside
    the cut — important because routing intentionally runs along the
    outside edge of unauthorized cuts and we don't want to confuse
    those with violations.

    Returns ``egi.sheet`` if no cut strictly contains the point.
    """
    if parent_map is None:
        parent_map = cut_parents(egi)
    cut_ids = {c.id for c in egi.Cut}

    def depth(cid: ElementID) -> int:
        d = 0
        cur = cid
        while parent_map.get(cur) is not None:
            cur = parent_map[cur]
            d += 1
        return d

    candidates = [
        cid
        for cid, b in dto.cut_bounds.items()
        if cid in cut_ids
        and b.min_x < point.x < b.max_x
        and b.min_y < point.y < b.max_y
    ]
    if not candidates:
        return egi.sheet
    return max(candidates, key=depth)


# --------------------------------------------------------------------------- #
# Internal: containment + DTO copy helpers                                    #
# --------------------------------------------------------------------------- #


def _point_in(p: Point, b: BoundingBox) -> bool:
    return b.min_x <= p.x <= b.max_x and b.min_y <= p.y <= b.max_y


def _bounds_in(inner: BoundingBox, outer: BoundingBox) -> bool:
    return (
        outer.min_x <= inner.min_x
        and outer.max_x >= inner.max_x
        and outer.min_y <= inner.min_y
        and outer.max_y >= inner.max_y
    )


def _bounds_overlap(a: BoundingBox, b: BoundingBox) -> bool:
    return not (
        a.max_x < b.min_x
        or a.min_x > b.max_x
        or a.max_y < b.min_y
        or a.min_y > b.max_y
    )


def _descendant_areas(
    egi: RelationalGraphWithCuts, area_id: ElementID
) -> Set[ElementID]:
    """``area_id`` plus every area transitively reachable downward in the area tree."""
    cut_ids = {c.id for c in egi.Cut}
    result: Set[ElementID] = {area_id}
    stack = [area_id]
    while stack:
        cur = stack.pop()
        for child in egi.area.get(cur, frozenset()):
            if child in cut_ids and child not in result:
                result.add(child)
                stack.append(child)
    return result


def _clone_dto(
    dto: LayoutDTO,
    *,
    vertex_positions: Optional[Dict[ElementID, Point]] = None,
    predicate_positions: Optional[Dict[ElementID, Point]] = None,
    cut_bounds: Optional[Dict[ElementID, BoundingBox]] = None,
    ligature_paths: Optional[list] = None,
) -> LayoutDTO:
    """Shallow-copy ``dto`` with the given fields overridden."""
    return LayoutDTO(
        vertex_positions=(
            vertex_positions
            if vertex_positions is not None
            else dict(dto.vertex_positions)
        ),
        predicate_positions=(
            predicate_positions
            if predicate_positions is not None
            else dict(dto.predicate_positions)
        ),
        cut_bounds=(
            cut_bounds if cut_bounds is not None else dict(dto.cut_bounds)
        ),
        ligature_paths=(
            ligature_paths
            if ligature_paths is not None
            else list(dto.ligature_paths)
        ),
        area_hierarchy={k: set(v) for k, v in dto.area_hierarchy.items()},
        viewport_bounds=dto.viewport_bounds,
        sheet_id=dto.sheet_id,
        style=dto.style,
    )


# --------------------------------------------------------------------------- #
# The three regime-3 operations                                               #
# --------------------------------------------------------------------------- #


def move_vertex(
    egi: RelationalGraphWithCuts,
    dto: LayoutDTO,
    vertex_id: ElementID,
    dx: float,
    dy: float,
) -> LayoutDTO:
    """Translate a vertex by ``(dx, dy)`` and cascade to ligature endpoints.

    The vertex's new position must remain inside the cut bounds of its
    EGI area (if its area is a cut; sheet vertices have no bounds
    constraint).  Every LigaturePath with ``vertex_id == vertex_id``
    has its vertex-side endpoint (``points[-1]``) updated to the new
    position, preserving §3.3 identity-endpoint correspondence.

    Raises Regime3Violation if:
      - ``vertex_id`` is not in ``dto.vertex_positions``;
      - the vertex's area is a cut and the translated position would
        fall outside ``dto.cut_bounds[area]`` (this would silently
        change area membership — not a regime-3 op).
    """
    if vertex_id not in dto.vertex_positions:
        raise Regime3Violation(
            f"move_vertex: {vertex_id} not in dto.vertex_positions"
        )
    old_pos = dto.vertex_positions[vertex_id]
    new_pos = Point(old_pos.x + dx, old_pos.y + dy)

    elem_area_map = element_area(egi)
    cut_ids = {c.id for c in egi.Cut}
    v_area = elem_area_map.get(vertex_id)
    if v_area in cut_ids:
        bounds = dto.cut_bounds.get(v_area)
        if bounds is None:
            raise Regime3Violation(
                f"move_vertex: vertex {vertex_id} is in area {v_area} "
                f"but that area has no cut_bounds entry"
            )
        if not _point_in(new_pos, bounds):
            raise Regime3Violation(
                f"move_vertex: translating {vertex_id} by ({dx}, {dy}) "
                f"would move it from inside area {v_area} "
                f"(bounds x∈[{bounds.min_x},{bounds.max_x}], "
                f"y∈[{bounds.min_y},{bounds.max_y}]) "
                f"to ({new_pos.x},{new_pos.y}) — outside the area. "
                f"That is a structural area change, not a regime-3 op."
            )

    new_positions = dict(dto.vertex_positions)
    new_positions[vertex_id] = new_pos

    new_paths = []
    for path in dto.ligature_paths:
        if path.vertex_id != vertex_id:
            new_paths.append(path)
            continue
        pts = list(path.points)
        if not pts:
            new_paths.append(path)
            continue
        pts[-1] = new_pos
        new_paths.append(
            LigaturePath(
                predicate_id=path.predicate_id,
                vertex_id=path.vertex_id,
                points=tuple(pts),
                port_index=path.port_index,
            )
        )

    return _clone_dto(
        dto, vertex_positions=new_positions, ligature_paths=new_paths
    )


def reshape_cut(
    egi: RelationalGraphWithCuts,
    dto: LayoutDTO,
    cut_id: ElementID,
    new_bounds: BoundingBox,
) -> LayoutDTO:
    """Replace ``dto.cut_bounds[cut_id]`` with ``new_bounds``.

    The new bounds must preserve interior membership in both
    directions (§5.5):

      - every element the EGI says is in ``area[cut_id]`` (or in any
        descendant area) must still be geometrically inside; and
      - no element outside those descendant areas may become
        geometrically inside.

    Raises Regime3Violation if either direction fails, or if
    ``cut_id`` is not in ``dto.cut_bounds``.
    """
    if cut_id not in dto.cut_bounds:
        raise Regime3Violation(
            f"reshape_cut: {cut_id} not in dto.cut_bounds"
        )

    cut_ids = {c.id for c in egi.Cut}
    if cut_id not in cut_ids:
        raise Regime3Violation(
            f"reshape_cut: {cut_id} is not a cut in the EGI"
        )

    own_areas = _descendant_areas(egi, cut_id)
    elem_area_map = element_area(egi)
    parent_map = cut_parents(egi)

    def _is_descendant_cut(cid: ElementID) -> bool:
        cur: Optional[ElementID] = cid
        while cur is not None:
            if cur == cut_id:
                return True
            cur = parent_map.get(cur)
        return False

    # Vertices and predicates.
    for elem_id, pos in list(dto.vertex_positions.items()) + list(
        dto.predicate_positions.items()
    ):
        area = elem_area_map.get(elem_id)
        in_own = area in own_areas
        in_new = _point_in(pos, new_bounds)
        if in_own and not in_new:
            raise Regime3Violation(
                f"reshape_cut: element {elem_id} is in egi.area[{area}] "
                f"(a descendant area of {cut_id}) but its position "
                f"({pos.x},{pos.y}) lies outside the proposed new bounds "
                f"x∈[{new_bounds.min_x},{new_bounds.max_x}], "
                f"y∈[{new_bounds.min_y},{new_bounds.max_y}]. "
                f"The reshape would push it out of {cut_id}'s area."
            )
        if not in_own and in_new:
            raise Regime3Violation(
                f"reshape_cut: element {elem_id} is in egi.area[{area}] "
                f"(outside {cut_id}'s descendant areas) but its position "
                f"({pos.x},{pos.y}) lies inside the proposed new bounds. "
                f"The reshape would absorb it into {cut_id}'s area."
            )

    # Sub-cuts: a child cut's bounds must be inside iff the child is in
    # cut_id's descendant area set.
    for other_id, other_bounds in dto.cut_bounds.items():
        if other_id == cut_id:
            continue
        is_descendant = _is_descendant_cut(other_id)
        bounds_inside = _bounds_in(other_bounds, new_bounds)
        bounds_outside = not _bounds_overlap(other_bounds, new_bounds)
        if is_descendant and not bounds_inside:
            raise Regime3Violation(
                f"reshape_cut: sub-cut {other_id} is a descendant of "
                f"{cut_id} but its bounds would not fit inside the "
                f"proposed new bounds for {cut_id}."
            )
        if (not is_descendant) and not bounds_outside:
            raise Regime3Violation(
                f"reshape_cut: cut {other_id} is not a descendant of "
                f"{cut_id} but its bounds would overlap the proposed "
                f"new bounds for {cut_id}."
            )

    new_cut_bounds = dict(dto.cut_bounds)
    new_cut_bounds[cut_id] = new_bounds
    return _clone_dto(dto, cut_bounds=new_cut_bounds)


def reroute_ligature(
    egi: RelationalGraphWithCuts,
    dto: LayoutDTO,
    predicate_id: ElementID,
    vertex_id: ElementID,
    port_index: int,
    new_interior: Iterable[Point],
) -> LayoutDTO:
    """Replace the interior of a ligature path with ``new_interior``.

    Endpoints are pinned: ``new_path.points[0] == old_path.points[0]``
    (predicate side) and ``new_path.points[-1] == old_path.points[-1]``
    (vertex side).  Moving an endpoint is a different operation —
    ``move_vertex`` cascades to the vertex-side endpoint; the
    predicate-side endpoint is a hook on the predicate's box and is
    not user-configurable.

    The reroute is regime-3 only if every new interior point AND every
    new segment midpoint lies on the area chain between
    predicate-area and vertex-area (§3.3 identity-fidelity area-chain
    traversal).  A waypoint that wanders into a sibling cut, or a
    straight segment that crosses an unauthorized cut, would change
    W-realisation — refused.

    Raises Regime3Violation if no path matches the (predicate_id,
    vertex_id, port_index) key or if any new point/midpoint leaves the
    chain.
    """
    target_index = None
    for i, p in enumerate(dto.ligature_paths):
        if (
            p.predicate_id == predicate_id
            and p.vertex_id == vertex_id
            and p.port_index == port_index
        ):
            target_index = i
            break
    if target_index is None:
        raise Regime3Violation(
            f"reroute_ligature: no path found with "
            f"predicate={predicate_id}, vertex={vertex_id}, "
            f"port_index={port_index}"
        )

    old_path = dto.ligature_paths[target_index]
    if len(old_path.points) < 2:
        raise Regime3Violation(
            f"reroute_ligature: target path has fewer than 2 points; "
            f"cannot identify endpoints to pin"
        )
    pred_end = old_path.points[0]
    vert_end = old_path.points[-1]

    interior = tuple(new_interior)
    new_points: Tuple[Point, ...] = (pred_end,) + interior + (vert_end,)

    elem_area_map = element_area(egi)
    parent_map = cut_parents(egi)
    v_area = elem_area_map.get(vertex_id, egi.sheet)
    p_area = elem_area_map.get(predicate_id, egi.sheet)
    allowed = area_chain(v_area, p_area, parent_map)

    # Check every new interior point.
    for i, pt in enumerate(interior, start=1):
        area = deepest_containing_cut(pt, dto, egi, parent_map)
        if area not in allowed:
            raise Regime3Violation(
                f"reroute_ligature: proposed interior point[{i}] "
                f"({pt.x},{pt.y}) lies in area {area}, off the chain "
                f"between vertex-area {v_area} and predicate-area "
                f"{p_area}. Allowed: {sorted(allowed)}."
            )

    # Check every segment midpoint on the new path.
    for i in range(len(new_points) - 1):
        a = new_points[i]
        b = new_points[i + 1]
        mid = Point((a.x + b.x) / 2, (a.y + b.y) / 2)
        area = deepest_containing_cut(mid, dto, egi, parent_map)
        if area not in allowed:
            raise Regime3Violation(
                f"reroute_ligature: midpoint of segment[{i}->{i+1}] "
                f"({mid.x},{mid.y}) lies in area {area}, off the chain "
                f"between vertex-area {v_area} and predicate-area "
                f"{p_area}. Allowed: {sorted(allowed)}."
            )

    new_paths = list(dto.ligature_paths)
    new_paths[target_index] = LigaturePath(
        predicate_id=predicate_id,
        vertex_id=vertex_id,
        points=new_points,
        port_index=port_index,
    )
    return _clone_dto(dto, ligature_paths=new_paths)


__all__ = [
    "Regime3Violation",
    "element_area",
    "cut_parents",
    "area_chain",
    "deepest_containing_cut",
    "move_vertex",
    "reshape_cut",
    "reroute_ligature",
]
