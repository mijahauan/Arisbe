"""
Presentation-only (regime-3) operations over a (EGI, LayoutDTO) pair.

This module implements the closed algebra over the projection that
docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md §4.3 and §5.5 require: a user
may freely reposition a vertex, reshape a cut, or reroute a ligature
*as long as* the EGI is untouched and the resulting drawing remains in
correspondence with it.

The operations exposed here — ``move_vertex``, ``move_predicate``,
``reshape_cut``, ``move_cut``, ``reroute_ligature`` — take an EGI and a
LayoutDTO and return a *new* LayoutDTO.  They never mutate the EGI.  They
refuse (by raising ``Regime3Violation``) any proposal that would cross a
regime boundary:

- a vertex / predicate translation that would push the element outside its
  current area;
- a cut reshape that would change which elements are geometrically
  inside the cut (the §5.5 interior-preservation rule);
- a cut *move* (rigid translation of the cut and everything it contains)
  that would leave its parent area, absorb a non-descendant element, or
  overlap a non-descendant cut;
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

import math
from typing import Dict, Iterable, Optional, Sequence, Set, Tuple

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


def _tree_path(
    a: Optional[ElementID],
    b: Optional[ElementID],
    parent_map: Dict[ElementID, ElementID],
) -> Tuple[list, Optional[ElementID], list]:
    """Canonical area-tree walk shared by ``area_chain`` and
    ``crossing_sequence`` — the single source of truth for the path
    between two areas.

    Returns ``(a_side, lca, b_side)`` where:

    - ``a_side`` is the ordered list of areas from ``a`` up to (but
      *excluding*) the lowest common ancestor;
    - ``b_side`` is the ordered list of areas from ``b`` up to (but
      *excluding*) the LCA;
    - ``lca`` is the lowest common ancestor area, or ``None`` if the two
      lie in disjoint trees (should not happen under a single sheet
      root).

    The boundary-*crossing* structure (``crossing_sequence``) is
    ``a_side`` + reversed ``b_side`` — the cuts you exit going out from
    ``a``, then the cuts you enter going in to ``b``.  The *area* set
    the path may occupy (``area_chain``) is ``a_side ∪ b_side ∪ {lca}``.
    The LCA's boundary is not crossed but its area is occupied — that is
    exactly the distinction between the two derived quantities.
    """
    if a is None or b is None:
        return [], None, []

    anc_a: list = []
    cur: Optional[ElementID] = a
    while cur is not None:
        anc_a.append(cur)
        cur = parent_map.get(cur)
    anc_a_set = set(anc_a)

    b_side: list = []
    cur = b
    while cur is not None and cur not in anc_a_set:
        b_side.append(cur)
        cur = parent_map.get(cur)
    lca = cur  # the first ancestor of b on a's chain, or None if disjoint

    if lca is None:
        a_side = list(anc_a)
    else:
        a_side = anc_a[: anc_a.index(lca)]
    return a_side, lca, b_side


def area_chain(
    a: ElementID,
    b: ElementID,
    parent_map: Dict[ElementID, ElementID],
) -> Set[ElementID]:
    """Return the set of areas on the path from ``a`` to ``b`` in the area tree.

    The path goes a -> ancestors -> LCA -> ... -> b.  Both endpoints
    and the LCA are included.  ``parent_map.get(sheet)`` is None — the
    sheet is the tree's root.

    Derived from the shared ``_tree_path`` walk (see
    ``crossing_sequence`` for the boundary-crossing counterpart).
    """
    a_side, lca, b_side = _tree_path(a, b, parent_map)
    result: Set[ElementID] = set(a_side) | set(b_side)
    if lca is not None:
        result.add(lca)
    return result


def crossing_sequence(
    pred_area: Optional[ElementID],
    vert_area: Optional[ElementID],
    parent_map: Dict[ElementID, ElementID],
) -> Tuple[ElementID, ...]:
    """Ordered cuts whose boundary a ligature must cross, from
    ``pred_area`` outward to the meet then inward to ``vert_area``.

    The projection-independent crossing structure: the cuts on the
    area-tree path *excluding* the lowest common ancestor (whose
    boundary is occupied, not crossed).  Empty for same-area
    incidences.  This is the single authoritative computation;
    ``natural_layout.authorized_crossings`` is a semantic alias for the
    projection-independent layer, and ``ELKLayoutEngine._authorized_cuts``
    consumes it (as a set) for obstacle determination — so the walk is
    computed once, not three times.
    """
    a_side, _lca, b_side = _tree_path(pred_area, vert_area, parent_map)
    return tuple(a_side + list(reversed(b_side)))


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
# Boundary-crossing count — projection-side geometry for the crossing-        #
# multiset form of §3.3 identity fidelity.                                    #
# --------------------------------------------------------------------------- #


def _orient(ax, ay, bx, by, cx, cy) -> float:
    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)


def _segments_properly_cross(
    ax, ay, bx, by, cx, cy, dx, dy
) -> bool:
    """True iff segments (a,b) and (c,d) cross at an interior point.

    Strict (proper) crossing: a segment merely *touching* an edge
    endpoint or running *along* it does not count.  This matters because
    routing intentionally runs ligatures along the outside edge of
    unauthorized cuts (see ``deepest_containing_cut``'s strict-bounds
    note) — grazing must not be miscounted as a crossing.
    """
    d1 = _orient(cx, cy, dx, dy, ax, ay)
    d2 = _orient(cx, cy, dx, dy, bx, by)
    d3 = _orient(ax, ay, bx, by, cx, cy)
    d4 = _orient(ax, ay, bx, by, dx, dy)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))


def _outside_edge_crossings(a: "Point", b: "Point", r: BoundingBox) -> int:
    """Count proper intersections of segment (a,b) with the 4 rect edges.

    Used only when *both* endpoints are outside the rect; for a convex
    rectangle a straight segment then crosses the boundary 0 or 2 times
    (a clean pass-through), never 1.
    """
    edges = (
        (r.min_x, r.min_y, r.max_x, r.min_y),
        (r.max_x, r.min_y, r.max_x, r.max_y),
        (r.max_x, r.max_y, r.min_x, r.max_y),
        (r.min_x, r.max_y, r.min_x, r.min_y),
    )
    return sum(
        1
        for (x1, y1, x2, y2) in edges
        if _segments_properly_cross(a.x, a.y, b.x, b.y, x1, y1, x2, y2)
    )


def count_boundary_crossings(points, rect: BoundingBox) -> int:
    """Number of times a polyline crosses the boundary of an AABB.

    A convex rectangle bounds each straight segment to 0/1/2 boundary
    crossings: 1 when its endpoints straddle the boundary, else 0 unless
    the segment passes clean through (then 2).  This is the projection
    geometry behind the crossing-multiset form of §3.3 identity
    fidelity — for an authorized cut the count must be 1 (net once), for
    an unauthorized cut 0 (the line must not enter it at all).
    """
    total = 0
    for i in range(len(points) - 1):
        a, b = points[i], points[i + 1]
        a_in, b_in = _point_in(a, rect), _point_in(b, rect)
        if a_in != b_in:
            total += 1
        elif not a_in and not b_in:
            total += _outside_edge_crossings(a, b, rect)
    return total


# --------------------------------------------------------------------------- #
# Shape-aware cut geometry — the drawn cut boundary IS the region.            #
#                                                                            #
# A cut's bounding box (``cut_bounds``) is a single geometric handle; the     #
# *style's* ``cut_shape`` says how to read "inside" it, and that reading is   #
# the **same one the renderer draws**.  So containment is determined by the   #
# drawn curve, identically across styles — the shape (rounded rectangle,      #
# inscribed ellipse, …) is immaterial to *which* area an element is in.  An   #
# oval style draws the ellipse inscribed in the box (renderer: rx=w/2,        #
# ry=h/2), so "inside" is the inscribed ellipse, not the box.                 #
# --------------------------------------------------------------------------- #


def _is_oval(shape) -> bool:
    return shape in ("oval", "circle")


def _ellipse_norm(x: float, y: float, b: BoundingBox) -> Tuple[float, float]:
    """Map a point into the cut's inscribed-ellipse frame (unit circle)."""
    cx, cy = (b.min_x + b.max_x) / 2.0, (b.min_y + b.max_y) / 2.0
    rx = (b.max_x - b.min_x) / 2.0 or 1e-9
    ry = (b.max_y - b.min_y) / 2.0 or 1e-9
    return (x - cx) / rx, (y - cy) / ry


def _point_in_rounded_rect(p: Point, b: BoundingBox, radius: float) -> bool:
    """Exact: ``p`` is inside a rounded rectangle (box ``b`` with quarter-circle
    corners of ``radius``) — the shape the renderer actually draws for the Dau
    style (`<rect rx=corner_radius>`).  A rounded rect is exactly the Minkowski sum
    of the *inner* rectangle (``b`` shrunk by ``radius`` on every side) and a disk
    of ``radius``: ``p`` is inside iff its distance to that inner rectangle is
    ``<= radius``.  So a point in a rounded-away corner reads *outside*, matching
    the drawing — no corner void.  ``radius`` is clamped to half the smaller side.
    """
    r = max(0.0, min(radius, (b.max_x - b.min_x) / 2.0, (b.max_y - b.min_y) / 2.0))
    if r <= 0.0:
        return _point_in(p, b)
    nx = min(max(p.x, b.min_x + r), b.max_x - r)   # nearest point on inner rect
    ny = min(max(p.y, b.min_y + r), b.max_y - r)
    return (p.x - nx) ** 2 + (p.y - ny) ** 2 <= r * r + 1e-9


# --------------------------------------------------------------------------- #
# The cut boundary as an explicit closed polyline — Phase 4 of                 #
# docs/EXACT_CORRESPONDENCE.md.  "A cut IS its drawn curve": one generator      #
# samples the literal curve the renderer draws (rounded rectangle, inscribed    #
# ellipse, or Peirce's hand-drawn wobble), so the renderer draws it, §3.3 tests #
# it (point-in-polygon), and the browser hit-tests it (isPointInFill) — all     #
# from one source of truth.  An arbitrary human-drawn cut is just such a        #
# polyline with no analytic shape behind it (the freeform canvas).              #
# --------------------------------------------------------------------------- #


def _ellipse_polyline(
    cx: float, cy: float, rx: float, ry: float,
    wobble_amplitude: float, seed, samples: int,
) -> Tuple[Point, ...]:
    """``samples`` points around the inscribed ellipse; with a positive
    ``wobble_amplitude`` and a ``seed`` they trace Peirce's hand-drawn loop — the
    *same* low-frequency two-harmonic deviation the renderer draws
    (`simple_svg_renderer._wobbled_oval_path`), so the polyline and the picture
    are one curve.  Amplitude is capped at 8% of the smaller radius (the renderer's
    cap)."""
    if wobble_amplitude > 0.0 and seed is not None:
        from render_geometry import jitter
        amp = min(wobble_amplitude, 0.08 * min(rx, ry))
        phi1 = jitter(seed, 1) * math.pi
        phi2 = jitter(seed, 2) * math.pi
        k1 = 2 + int(round(abs(jitter(seed, 3)) * 1.49))
        k2 = 4 + int(round(abs(jitter(seed, 4)) * 1.49))
        out = []
        for i in range(samples):
            t = 2.0 * math.pi * i / samples
            dev = amp * (0.6 * math.sin(k1 * t + phi1) + 0.4 * math.sin(k2 * t + phi2))
            out.append(Point(cx + (rx + dev) * math.cos(t), cy + (ry + dev) * math.sin(t)))
        return tuple(out)
    return tuple(
        Point(cx + rx * math.cos(2.0 * math.pi * i / samples),
              cy + ry * math.sin(2.0 * math.pi * i / samples))
        for i in range(samples)
    )


def _rounded_rect_polyline(
    b: BoundingBox, radius: float, samples: int
) -> Tuple[Point, ...]:
    """Closed polyline of the rounded rectangle the renderer draws (`<rect
    rx=radius>`): four straight edges inset by ``radius`` joined by four
    quarter-circle corner arcs — the same boundary ``_point_in_rounded_rect`` /
    ``_rounded_rect_secant_crossings`` model.  ``radius`` 0 gives the plain box."""
    r = max(0.0, min(radius, (b.max_x - b.min_x) / 2.0, (b.max_y - b.min_y) / 2.0))
    if r <= 0.0:
        return (
            Point(b.min_x, b.min_y), Point(b.max_x, b.min_y),
            Point(b.max_x, b.max_y), Point(b.min_x, b.max_y),
        )
    ix0, iy0, ix1, iy1 = b.min_x + r, b.min_y + r, b.max_x - r, b.max_y - r
    per = max(2, samples // 4)
    out: list = []
    # Four corners, clockwise from top-right; each arc swept about its inner
    # corner from the start angle through +90°.
    for (cxp, cyp, a0) in (
        (ix1, iy0, -math.pi / 2.0),   # top-right
        (ix1, iy1, 0.0),              # bottom-right
        (ix0, iy1, math.pi / 2.0),    # bottom-left
        (ix0, iy0, math.pi),          # top-left
    ):
        for k in range(per + 1):
            a = a0 + (math.pi / 2.0) * (k / per)
            out.append(Point(cxp + r * math.cos(a), cyp + r * math.sin(a)))
    # Drop consecutive duplicates (corner arc endpoints meet the next start).
    dedup: list = []
    for p in out:
        if not dedup or abs(dedup[-1].x - p.x) > 1e-9 or abs(dedup[-1].y - p.y) > 1e-9:
            dedup.append(p)
    return tuple(dedup)


def cut_boundary(
    bounds: BoundingBox, shape, corner_radius: float = 0.0,
    wobble_amplitude: float = 0.0, seed=None, samples: int = 96,
) -> Tuple[Point, ...]:
    """The closed polyline of a cut's **drawn** boundary — the single source of
    truth for "what the cut is" as a curve.  Oval/circle → (optionally wobbled)
    inscribed ellipse; otherwise the rounded rectangle (`corner_radius`).  The
    points are in DTO coordinates and the polygon is implicitly closed (last → first)."""
    cx = (bounds.min_x + bounds.max_x) / 2.0
    cy = (bounds.min_y + bounds.max_y) / 2.0
    rx = (bounds.max_x - bounds.min_x) / 2.0
    ry = (bounds.max_y - bounds.min_y) / 2.0
    if _is_oval(shape):
        return _ellipse_polyline(cx, cy, rx, ry, wobble_amplitude, seed, samples)
    return _rounded_rect_polyline(bounds, corner_radius, samples)


def resolve_cut_boundaries(dto) -> Dict[ElementID, Optional[Tuple[Point, ...]]]:
    """Per-cut drawn-boundary polyline to test containment against, or ``None``
    where the cut has an analytic drawn shape.  The "boundary of record" shared by
    §3.3 and ``eg_reader``:

    - a cut **carried as an explicit polyline** (``dto.cut_boundary`` — a human-drawn
      freeform cut, where the polyline *is* the cut, with no analytic shape behind
      it) → that polyline, tested point-in-polygon;
    - any cut from the analytic engines (inscribed ellipse / rounded rectangle) →
      ``None``: ``point_in_cut`` reads the exact drawn shape from ``cut_bounds`` +
      style.  (The hand-drawn *wobble* is a stroke-only cosmetic flourish applied at
      render time and capped within the containment margin — see ``render_geometry``;
      it is deliberately not part of the attested geometry, so it is not resolved
      here.)
    """
    carried = getattr(dto, "cut_boundary", None) or {}
    return {
        cid: (tuple(carried[cid]) if carried.get(cid) else None)
        for cid in dto.cut_bounds
    }


def point_in_polygon(p: Point, poly: Sequence[Point]) -> bool:
    """Ray-casting test: is ``p`` strictly inside the closed polygon ``poly``
    (implicitly closed last → first)?  This is the exact reading of "inside the
    drawn cut" once the cut is carried as its literal polyline — what the browser's
    ``isPointInFill`` computes on the same path."""
    n = len(poly)
    if n < 3:
        return False
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = poly[i].x, poly[i].y
        xj, yj = poly[j].x, poly[j].y
        if (yi > p.y) != (yj > p.y):
            x_cross = xi + (xj - xi) * (p.y - yi) / (yj - yi)
            if p.x < x_cross:
                inside = not inside
        j = i
    return inside


def _seg_proper_cross(a: Point, b: Point, c: Point, d: Point) -> bool:
    """True iff open segments ab and cd cross (share an interior point)."""
    def orient(p, q, r):
        return (q.x - p.x) * (r.y - p.y) - (q.y - p.y) * (r.x - p.x)
    o1, o2 = orient(a, b, c), orient(a, b, d)
    o3, o4 = orient(c, d, a), orient(c, d, b)
    return (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0)


def polyline_polygon_crossings(points: Sequence[Point], poly: Sequence[Point]) -> int:
    """How many times the open polyline ``points`` crosses the closed polygon
    boundary ``poly`` — the polygon analogue of ``count_cut_crossings`` for a cut
    carried as its literal curve."""
    n = len(poly)
    if n < 3:
        return 0
    total = 0
    for i in range(len(points) - 1):
        a, b = points[i], points[i + 1]
        for j in range(n):
            if _seg_proper_cross(a, b, poly[j], poly[(j + 1) % n]):
                total += 1
    return total


def point_in_cut(
    p: Point, bounds: BoundingBox, shape, corner_radius: float = 0.0,
    boundary: Optional[Sequence[Point]] = None,
) -> bool:
    """Whether point ``p`` is inside the cut **as the style draws it**.  When the
    cut's literal ``boundary`` polyline is supplied (Phase 4), test point-in-polygon
    against it — the exact drawn curve, wobble and all.  Otherwise fall back to the
    analytic drawn shape: the inscribed ellipse for an oval/circle, the rounded
    rectangle (with ``corner_radius``) for a Dau box, the plain box when 0.

    Testing the *drawn* shape (not a bounding-box proxy) is what makes containment
    exact (`docs/EXACT_CORRESPONDENCE.md`).  ``corner_radius`` defaults to 0;
    callers with the style pass ``style.cut_corner_radius``.
    """
    if boundary is not None:
        return point_in_polygon(p, boundary)
    if _is_oval(shape):
        nx, ny = _ellipse_norm(p.x, p.y, bounds)
        return nx * nx + ny * ny <= 1.0 + 1e-9
    if corner_radius > 0.0:
        return _point_in_rounded_rect(p, bounds, corner_radius)
    return _point_in(p, bounds)


def bounds_in_cut(
    inner: BoundingBox, outer: BoundingBox, shape, corner_radius: float = 0.0,
    boundary: Optional[Sequence[Point]] = None,
) -> bool:
    """Whether the whole ``inner`` box lies inside the cut ``outer`` as drawn —
    every corner of ``inner`` inside ``outer``'s drawn shape (the literal
    ``boundary`` polyline when given, else inscribed ellipse / rounded rectangle /
    box)."""
    corners = (
        (inner.min_x, inner.min_y), (inner.max_x, inner.min_y),
        (inner.max_x, inner.max_y), (inner.min_x, inner.max_y),
    )
    if boundary is not None:
        return all(point_in_polygon(Point(x, y), boundary) for x, y in corners)
    if _is_oval(shape):
        for x, y in corners:
            nx, ny = _ellipse_norm(x, y, outer)
            if nx * nx + ny * ny > 1.0 + 1e-9:
                return False
        return True
    if corner_radius > 0.0:
        return all(
            _point_in_rounded_rect(Point(x, y), outer, corner_radius)
            for x, y in corners
        )
    return _bounds_in(inner, outer)


# Padding the renderer adds around the predicate text, in DTO units.  Kept here so
# the drawn box and the §3.3 extent are computed from one formula.
_PRED_LABEL_PAD_H = 2.0
_PRED_LABEL_PAD_V = 1.0


def predicate_label_box(label: str, center, style) -> BoundingBox:
    """The axis-aligned **extent** of a predicate's drawn label box, centred on
    ``center`` (its ``predicate_positions`` anchor).  This is the rectangle the
    renderer actually draws (`simple_svg_renderer`): width
    ``len(label)·char_width + 2·pad_h``, height ``predicate_height + 2·pad_v``.

    §3.3 reads a predicate's containment off *this extent*, not the anchor point —
    so a label may not straddle a cut boundary (`docs/EXACT_CORRESPONDENCE.md`
    Phase 3).  Single source of truth: the renderer draws from this same box, so
    test and picture agree.  ``style`` may be ``None`` (defaults are used)."""
    char_width = float(getattr(style, "predicate_char_width", 8.0) or 8.0)
    height = float(getattr(style, "predicate_height", 20.0) or 20.0)
    w = len(label) * char_width + 2.0 * _PRED_LABEL_PAD_H
    h = height + 2.0 * _PRED_LABEL_PAD_V
    return BoundingBox(
        center.x - w / 2.0, center.y - h / 2.0,
        center.x + w / 2.0, center.y + h / 2.0,
    )


def box_intrudes_cut(
    box: BoundingBox, bounds: BoundingBox, shape, corner_radius: float = 0.0
) -> bool:
    """Whether any part of ``box`` lies inside the cut ``bounds`` as drawn — used to
    forbid a label box from dipping into a cut that is *not* its container (the box
    analogue of the ligature "enters forbidden cut" check).  True if any corner of
    ``box`` is inside the cut, or any corner of the cut's bounds is inside ``box``
    (the box engulfing part of the cut).  This catches every straddle where a corner
    crosses the boundary; a pure cross-overlap with no corner inside either is not a
    case the engine produces for axis-aligned label boxes."""
    box_corners = (
        (box.min_x, box.min_y), (box.max_x, box.min_y),
        (box.max_x, box.max_y), (box.min_x, box.max_y),
    )
    if any(point_in_cut(Point(x, y), bounds, shape, corner_radius) for x, y in box_corners):
        return True
    cut_corners = (
        (bounds.min_x, bounds.min_y), (bounds.max_x, bounds.min_y),
        (bounds.max_x, bounds.max_y), (bounds.min_x, bounds.max_y),
    )
    return any(_point_in(Point(x, y), box) for x, y in cut_corners)


# Width of one character of a vertex/constant label as a fraction of the font
# size — a sans-serif advance estimate (the renderer draws plain text with no box,
# so this is the faithful extent, not a measured glyph run).
_VERTEX_CHAR_W_RATIO = 0.6


# --- Vertex-label placement primitives (shared by vertex_label_box + the global
# --- place_label_boxes pass, so single-box and global placement stay identical).

def _vertex_label_dims(label, style):
    """The (width, height) extent of a vertex/constant label's box."""
    font_size = float(getattr(style, "font_size", 14.0) or 14.0)
    w = len(label) * font_size * _VERTEX_CHAR_W_RATIO + 2.0 * _PRED_LABEL_PAD_H
    h = font_size + 2.0 * _PRED_LABEL_PAD_V
    return w, h


def _vertex_incident_angles(ligature_paths, vertex_id):
    """The outgoing directions of the lines of identity incident to a vertex."""
    angs = []
    for lp in ligature_paths:
        if vertex_id is not None and getattr(lp, "vertex_id", None) != vertex_id:
            continue
        pts = getattr(lp, "points", ())
        if len(pts) >= 2:
            a, b = pts[-1], pts[-2]
            angs.append(math.atan2(b.y - a.y, b.x - a.x))
    return angs


def _vertex_free_angle(angs):
    """The *freest* angular gap between incident lines (so the label never sits on
    a ligature it is incident to); to the right of the dot when east is clear."""
    east_blocked = any(
        abs(math.atan2(math.sin(a), math.cos(a))) < math.radians(50) for a in angs
    )
    if not east_blocked or not angs:
        return 0.0  # to the right of the dot
    angs = sorted(angs)
    best_gap, free_ang = -1.0, -math.pi / 2.0  # default: above
    for i in range(len(angs)):
        a0 = angs[i]
        a1 = angs[(i + 1) % len(angs)] + (
            2.0 * math.pi if i + 1 == len(angs) else 0.0)
        if a1 - a0 > best_gap:
            best_gap, free_ang = a1 - a0, (a0 + a1) / 2.0
    return free_ang


def _vertex_box_at(center, ang, w, h, vr, extra=0.0) -> BoundingBox:
    """The label box placed in direction ``ang`` from the dot.  ``extra`` pushes it
    farther out (the ladder the global pass uses to spread crowded labels)."""
    dirx, diry = math.cos(ang), math.sin(ang)
    # Distance from dot to box centre = dot clearance + extra push + the box's
    # half-extent projected onto the placement direction.
    d = vr + 8.0 + extra + abs(dirx) * w / 2.0 + abs(diry) * h / 2.0
    bcx, bcy = center.x + dirx * d, center.y + diry * d
    return BoundingBox(bcx - w / 2.0, bcy - h / 2.0, bcx + w / 2.0, bcy + h / 2.0)


def _vertex_cut_context(egi, vertex_id, cut_bounds, style):
    """(container, non-ancestor-cut obstacles, cut shape, corner radius) for the
    cut-containment test — the area a label box must stay inside / clear of."""
    cut_id_set = {c.id for c in egi.Cut}
    area_cut = element_area(egi).get(vertex_id, egi.sheet)
    parent_map = cut_parents(egi)
    ancestors = set()
    cur = area_cut
    while cur in cut_id_set:
        ancestors.add(cur)
        cur = parent_map.get(cur, egi.sheet)
    shape = getattr(style, "cut_shape", "rounded_rectangle")
    radius = float(getattr(style, "cut_corner_radius", 0) or 0)
    container = cut_bounds.get(area_cut) if area_cut in cut_id_set else None
    obstacles = [
        cut_bounds[cid] for cid in cut_id_set
        if cid not in ancestors and cid in cut_bounds
    ]
    return container, obstacles, shape, radius


def _fits_cuts(box, container, obstacles, shape, radius) -> bool:
    """Whether ``box`` stays wholly inside its area cut and clear of every
    non-ancestor cut (the cut-straddle clause of the §3.3 occlusion test)."""
    if container is not None and not bounds_in_cut(box, container, shape, radius):
        return False
    return not any(box_intrudes_cut(box, ob, shape, radius) for ob in obstacles)


def vertex_label_box(
    label, center, style, ligature_paths=(), vertex_id=None,
    egi=None, cut_bounds=None,
) -> BoundingBox:
    """The axis-aligned **extent** of a vertex/constant label, placed adjacent to
    its dot.  The preferred direction is the *freest* angular gap between the lines
    of identity incident to the vertex (so the label never sits on a ligature it is
    incident to), defaulting to the right of the dot when no incident line leaves
    eastward.

    **Single-box placement** (cut-aware, sibling-*blind*).  This is the per-vertex
    primitive the layout engine / clockwise reader use as a soft-obstacle estimate.
    When ``egi`` and ``cut_bounds`` are supplied, the preferred direction is only
    taken if the resulting box stays wholly inside the vertex's area cut and clear
    of every non-ancestor cut; otherwise the freest direction is tried, then the
    four cardinals, and the first that fits is used, falling back to the freest gap.

    The authoritative, **sibling-aware** placement the renderer draws and §3.3
    attests is ``place_label_boxes`` (which builds on these same primitives so the
    two never diverge); this function is unchanged so its existing callers keep
    identical geometry.  ``style`` may be ``None`` (defaults used); the width is a
    faithful font-size estimate, not pixel-exact."""
    vr = float(getattr(style, "vertex_radius", 5.0) or 5.0)
    w, h = _vertex_label_dims(label, style)
    angs = _vertex_incident_angles(ligature_paths, vertex_id)
    free_ang = _vertex_free_angle(angs)

    if egi is None or cut_bounds is None or vertex_id is None:
        return _vertex_box_at(center, free_ang, w, h, vr)

    container, obstacles, shape, radius = _vertex_cut_context(
        egi, vertex_id, cut_bounds, style)
    for ang in (free_ang, -math.pi / 2.0, math.pi / 2.0, math.pi, 0.0):
        box = _vertex_box_at(center, ang, w, h, vr)
        if _fits_cuts(box, container, obstacles, shape, radius):
            return box
    return _vertex_box_at(center, free_ang, w, h, vr)


def boxes_overlap(a: BoundingBox, b: BoundingBox) -> bool:
    """True iff two axis-aligned boxes share a positive-area region.  Boxes that
    merely abut along an edge or touch at a corner do *not* overlap — text that just
    touches is still legible; only genuine area overlap is occlusion."""
    return (
        a.min_x < b.max_x - 1e-9 and b.min_x < a.max_x - 1e-9
        and a.min_y < b.max_y - 1e-9 and b.min_y < a.max_y - 1e-9
    )


def _clip_segment_to_box(a: Point, b: Point, box: BoundingBox):
    """Liang–Barsky clip of segment (a,b) to the closed ``box``.  Returns the
    clipped sub-segment as ``(x0, y0, x1, y1)`` or ``None`` if it misses the box."""
    x0, y0, dx, dy = a.x, a.y, b.x - a.x, b.y - a.y
    p = (-dx, dx, -dy, dy)
    q = (x0 - box.min_x, box.max_x - x0, y0 - box.min_y, box.max_y - y0)
    t0, t1 = 0.0, 1.0
    for pi, qi in zip(p, q):
        if abs(pi) < 1e-12:
            if qi < 0.0:  # parallel to this slab and outside it
                return None
        else:
            t = qi / pi
            if pi < 0.0:
                if t > t1:
                    return None
                t0 = max(t0, t)
            else:
                if t < t0:
                    return None
                t1 = min(t1, t)
    if t1 < t0:
        return None
    return (x0 + t0 * dx, y0 + t0 * dy, x0 + t1 * dx, y0 + t1 * dy)


def path_intersects_box(points, box: BoundingBox) -> bool:
    """True iff a polyline passes through the *open interior* of ``box`` — some
    segment has a portion strictly inside, or a vertex strictly inside.  A line
    merely touching or running along the border (e.g. a ligature grazing the box's
    edge) stays on the boundary and does not count, so a label sitting against a line
    is not falsely flagged.  This is the obstacle-test primitive for the deferred
    label-aware ligature routing (`docs/EXACT_CORRESPONDENCE.md` Phase 3b)."""
    for i in range(len(points) - 1):
        clipped = _clip_segment_to_box(points[i], points[i + 1], box)
        if clipped is None:
            continue
        mx, my = (clipped[0] + clipped[2]) / 2.0, (clipped[1] + clipped[3]) / 2.0
        if (box.min_x + 1e-9 < mx < box.max_x - 1e-9
                and box.min_y + 1e-9 < my < box.max_y - 1e-9):
            return True
    return False


# Candidate directions for a crowded vertex label, tried in order — the aesthetic
# free direction first, then the four cardinals, then the four diagonals — each at
# a small ladder of push-out distances.  Enough spread that two long adjacent
# labels find non-overlapping homes (the F1⁵ Warner-Bros collision class).
_VERTEX_PUSH_LADDER = (0.0, 12.0, 26.0, 44.0, 68.0)


def place_label_boxes(
    egi, predicate_positions, vertex_positions, ligature_paths, cut_bounds, style,
    show_vertex_labels=True,
):
    """Global, deterministic, **sibling-aware** placement of every label box — the
    single source of truth the renderer draws from and §3.3 attests, so picture and
    test never diverge.

    ``vertex_label_box`` places each label alone (cut-aware but blind to the other
    labels), so two long constant labels whose dots sit near each other both default
    to the right of their dot and overlap — a genuine text-on-text occlusion whose
    appearance flips with parse tie-breaks, the coin-flip that killed run 5
    (``runs/RUN_5_LOG.md`` F1⁵).  This pass places all labels *together* so each
    avoids the others.

    Predicate boxes are anchored (no placement freedom) and enter first as fixed
    obstacles.  Vertex/constant labels are then placed **longest-first** (the hardest
    to fit claims space early; tie-break by label then id, so two parses agree), each
    taking the first candidate direction+distance that

      (1) stays inside its area cut and clear of every non-ancestor cut,
      (2) overlaps no already-placed box, and
      (3) is not struck through by a line of identity it is not incident to

    — i.e. the chosen spot satisfies all three §3.3 occlusion clauses by
    construction.  Only when *no* candidate fits (a genuinely cramped area the engine
    must widen) does it fall back to the freest gap, which §3.3 then flags honestly.

    Returns ``{element_id: BoundingBox}`` over edge ids (predicates) and the vertex
    ids of labelled vertices.  ``style`` may be ``None``.
    """
    placed = {}
    obstacle_boxes = []  # every box placed so far (predicate + vertex)

    # Predicates first — fixed extent at their anchor; order is irrelevant (each is
    # independent) so plain E iteration is fine.
    for edge in egi.E:
        ppos = predicate_positions.get(edge.id)
        if ppos is None:
            continue
        box = predicate_label_box(egi.get_relation_name(edge.id), ppos, style)
        placed[edge.id] = box
        obstacle_boxes.append(box)

    if not show_vertex_labels:
        return placed

    vr = float(getattr(style, "vertex_radius", 5.0) or 5.0)

    labelled = [
        v for v in egi.V
        if getattr(v, "label", None) and vertex_positions.get(v.id) is not None
    ]
    # Deterministic, id-independent up to genuinely identical labels.
    labelled.sort(key=lambda v: (-len(v.label), v.label, str(v.id)))

    directions = (
        None,  # placeholder for each vertex's free angle, filled per-vertex below
        -math.pi / 2.0, math.pi / 2.0, math.pi, 0.0,
        -math.pi / 4.0, math.pi / 4.0, -3.0 * math.pi / 4.0, 3.0 * math.pi / 4.0,
    )

    for v in labelled:
        center = vertex_positions[v.id]
        w, h = _vertex_label_dims(v.label, style)
        angs = _vertex_incident_angles(ligature_paths, v.id)
        free_ang = _vertex_free_angle(angs)
        if cut_bounds is not None:
            container, cut_obstacles, shape, radius = _vertex_cut_context(
                egi, v.id, cut_bounds, style)
        else:
            container, cut_obstacles, shape, radius = None, [], None, 0.0
        nonincident = [
            lp for lp in ligature_paths if getattr(lp, "vertex_id", None) != v.id
        ]
        cand_dirs = tuple(free_ang if d is None else d for d in directions)

        chosen = None
        for extra in _VERTEX_PUSH_LADDER:
            for ang in cand_dirs:
                box = _vertex_box_at(center, ang, w, h, vr, extra)
                if not _fits_cuts(box, container, cut_obstacles, shape, radius):
                    continue
                if any(boxes_overlap(box, ob) for ob in obstacle_boxes):
                    continue
                if any(path_intersects_box(getattr(lp, "points", ()), box)
                       for lp in nonincident):
                    continue
                chosen = box
                break
            if chosen is not None:
                break
        if chosen is None:
            chosen = _vertex_box_at(center, free_ang, w, h, vr)
        placed[v.id] = chosen
        obstacle_boxes.append(chosen)

    return placed


def _ellipse_secant_crossings(a: Point, b: Point, bounds: BoundingBox) -> int:
    """Proper intersections of segment (a,b) with the inscribed ellipse when
    *both* endpoints are outside — 0 (miss/tangent) or 2 (clean pass-through),
    the ellipse analogue of ``_outside_edge_crossings``."""
    ax, ay = _ellipse_norm(a.x, a.y, bounds)
    bx, by = _ellipse_norm(b.x, b.y, bounds)
    dx, dy = bx - ax, by - ay
    A = dx * dx + dy * dy
    if A < 1e-12:
        return 0
    B = 2.0 * (ax * dx + ay * dy)
    C = ax * ax + ay * ay - 1.0
    disc = B * B - 4.0 * A * C
    if disc <= 1e-9:  # miss, or tangent (a graze is not a crossing)
        return 0
    s = math.sqrt(disc)
    roots = ((-B - s) / (2.0 * A), (-B + s) / (2.0 * A))
    return sum(1 for t in roots if 1e-9 < t < 1.0 - 1e-9)


def _seg_arc_crossings(
    a: Point, b: Point, cx: float, cy: float, r: float, sx: int, sy: int
) -> int:
    """Proper intersections of segment (a,b) with one quarter-circle corner arc —
    the arc of radius ``r`` about ``(cx, cy)`` lying in the *outward* quadrant given
    by the sign pair ``(sx, sy)`` (e.g. ``(-1, -1)`` is the top-left corner, the arc
    where ``x <= cx`` and ``y <= cy``).  The rounded-rect analogue of an edge test:
    intersect the segment with the full circle, keep roots strictly interior to the
    segment whose point falls in the arc's quadrant."""
    ax, ay = a.x - cx, a.y - cy
    bx, by = b.x - cx, b.y - cy
    dx, dy = bx - ax, by - ay
    A = dx * dx + dy * dy
    if A < 1e-12:
        return 0
    B = 2.0 * (ax * dx + ay * dy)
    C = ax * ax + ay * ay - r * r
    disc = B * B - 4.0 * A * C
    if disc <= 1e-9:  # miss, or tangent (a graze is not a crossing)
        return 0
    s = math.sqrt(disc)
    count = 0
    for t in ((-B - s) / (2.0 * A), (-B + s) / (2.0 * A)):
        if 1e-9 < t < 1.0 - 1e-9:
            px, py = ax + t * dx, ay + t * dy  # relative to the arc's centre
            if px * sx >= -1e-9 and py * sy >= -1e-9:
                count += 1
    return count


def _rounded_rect_secant_crossings(
    a: Point, b: Point, bnd: BoundingBox, radius: float
) -> int:
    """Proper intersections of segment (a,b) with the rounded-rectangle boundary
    when *both* endpoints are outside — 0 (miss/tangent) or 2 (clean pass-through),
    the rounded-rect analogue of ``_outside_edge_crossings`` / ``_ellipse_secant_crossings``.

    The boundary the renderer draws (`<rect rx=radius>`) is four straight edges —
    each inset by ``radius`` so it spans only the flat part of a side — joined by
    four quarter-circle arcs of ``radius`` centred at the inner-rectangle corners.
    Counting crossings against *these* pieces (not the square box edges) is what
    makes the crossing test read off the same drawn curve as Phase 1's containment,
    so a line grazing a rounded-away corner is not miscounted as entering the cut."""
    r = max(0.0, min(radius, (bnd.max_x - bnd.min_x) / 2.0, (bnd.max_y - bnd.min_y) / 2.0))
    if r <= 0.0:
        return _outside_edge_crossings(a, b, bnd)
    ix0, iy0 = bnd.min_x + r, bnd.min_y + r   # inner-rectangle corners
    ix1, iy1 = bnd.max_x - r, bnd.max_y - r
    edges = (
        (ix0, bnd.min_y, ix1, bnd.min_y),   # top    (flat span)
        (bnd.max_x, iy0, bnd.max_x, iy1),   # right
        (ix1, bnd.max_y, ix0, bnd.max_y),   # bottom
        (bnd.min_x, iy1, bnd.min_x, iy0),   # left
    )
    total = sum(
        1
        for (x1, y1, x2, y2) in edges
        if _segments_properly_cross(a.x, a.y, b.x, b.y, x1, y1, x2, y2)
    )
    for cx, cy, sx, sy in (
        (ix0, iy0, -1, -1),   # top-left
        (ix1, iy0,  1, -1),   # top-right
        (ix1, iy1,  1,  1),   # bottom-right
        (ix0, iy1, -1,  1),   # bottom-left
    ):
        total += _seg_arc_crossings(a, b, cx, cy, r, sx, sy)
    return total


def count_cut_crossings(
    points, bounds: BoundingBox, shape, corner_radius: float = 0.0,
    boundary: Optional[Sequence[Point]] = None,
) -> int:
    """Number of times a polyline crosses the cut boundary as the style draws it.
    When the cut's literal ``boundary`` polyline is supplied (Phase 4), count
    crossings of the actual drawn curve (``polyline_polygon_crossings``); otherwise
    the analytic drawn shape — inscribed ellipse for an oval/circle, rounded
    rectangle (with ``corner_radius``) for a Dau box, plain box when 0.

    The crossing-multiset form of §3.3 reads off the *drawn* curve, so this consumes
    the same boundary as Phase 1's containment (``point_in_cut``): a ligature that
    clips a rounded-away corner is counted exactly as the eye sees it — not as a
    spurious entry into the cut (`docs/EXACT_CORRESPONDENCE.md` Phase 2).
    ``corner_radius`` defaults to 0; callers with the style pass
    ``style.cut_corner_radius``."""
    if boundary is not None:
        return polyline_polygon_crossings(points, boundary)
    if _is_oval(shape):
        inside = lambda p: point_in_cut(p, bounds, shape)
        secant = lambda a, b: _ellipse_secant_crossings(a, b, bounds)
    elif corner_radius > 0.0:
        inside = lambda p: _point_in_rounded_rect(p, bounds, corner_radius)
        secant = lambda a, b: _rounded_rect_secant_crossings(a, b, bounds, corner_radius)
    else:
        return count_boundary_crossings(points, bounds)
    total = 0
    for i in range(len(points) - 1):
        a, b = points[i], points[i + 1]
        a_in, b_in = inside(a), inside(b)
        if a_in != b_in:
            total += 1
        elif not a_in and not b_in:
            total += secant(a, b)
    return total


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
        # B-min committed second-order marks ride through regime-3 ops
        # unchanged (they are annotation, not geometry).
        cut_stroke=(
            dict(dto.cut_stroke) if getattr(dto, "cut_stroke", None) else None
        ),
        vertex_sorts=(
            dict(dto.vertex_sorts) if getattr(dto, "vertex_sorts", None) else None
        ),
        quotation_ties=(
            dict(dto.quotation_ties)
            if getattr(dto, "quotation_ties", None) else None
        ),
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


def move_predicate(
    egi: RelationalGraphWithCuts,
    dto: LayoutDTO,
    predicate_id: ElementID,
    dx: float,
    dy: float,
) -> LayoutDTO:
    """Translate a predicate (edge / relation label) by ``(dx, dy)`` and
    cascade to its ligature predicate-side endpoints.

    A relation's *drawn position* carries no logic: where the label ``P`` sits
    is pure presentation, so long as it stays in its EGI area and its incident
    identity lines keep their endpoints attached.  This is the predicate-side
    twin of ``move_vertex`` — every ``LigaturePath`` with
    ``predicate_id == predicate_id`` has its predicate-side endpoint
    (``points[0]``, the hook on the predicate's box) translated by the same
    ``(dx, dy)`` so the line follows the label, while the vertex-side endpoint
    stays pinned.

    Raises ``Regime3Violation`` if:
      - ``predicate_id`` is not in ``dto.predicate_positions``;
      - the predicate's area is a cut and the translated position would fall
        outside ``dto.cut_bounds[area]`` (a silent area change, not regime-3).

    As with ``move_vertex`` the explicit guard is area-containment of the
    predicate's anchor point; a stretched first segment that would mis-cross a
    cut is caught by the §3.3 attestation backstop at the service boundary.
    """
    if predicate_id not in dto.predicate_positions:
        raise Regime3Violation(
            f"move_predicate: {predicate_id} not in dto.predicate_positions"
        )
    old_pos = dto.predicate_positions[predicate_id]
    new_pos = Point(old_pos.x + dx, old_pos.y + dy)

    elem_area_map = element_area(egi)
    cut_ids = {c.id for c in egi.Cut}
    p_area = elem_area_map.get(predicate_id)
    if p_area in cut_ids:
        bounds = dto.cut_bounds.get(p_area)
        if bounds is None:
            raise Regime3Violation(
                f"move_predicate: predicate {predicate_id} is in area {p_area} "
                f"but that area has no cut_bounds entry"
            )
        if not _point_in(new_pos, bounds):
            raise Regime3Violation(
                f"move_predicate: translating {predicate_id} by ({dx}, {dy}) "
                f"would move it from inside area {p_area} to "
                f"({new_pos.x},{new_pos.y}) — outside the area. "
                f"That is a structural area change, not a regime-3 op."
            )

    new_predicates = dict(dto.predicate_positions)
    new_predicates[predicate_id] = new_pos

    new_paths = []
    for path in dto.ligature_paths:
        if path.predicate_id != predicate_id:
            new_paths.append(path)
            continue
        pts = list(path.points)
        if not pts:
            new_paths.append(path)
            continue
        pts[0] = Point(pts[0].x + dx, pts[0].y + dy)
        new_paths.append(
            LigaturePath(
                predicate_id=path.predicate_id,
                vertex_id=path.vertex_id,
                points=tuple(pts),
                port_index=path.port_index,
            )
        )

    return _clone_dto(
        dto, predicate_positions=new_predicates, ligature_paths=new_paths
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


def move_cut(
    egi: RelationalGraphWithCuts,
    dto: LayoutDTO,
    cut_id: ElementID,
    dx: float,
    dy: float,
) -> LayoutDTO:
    """Rigidly translate a cut **and everything it contains** by ``(dx, dy)``.

    Unlike ``reshape_cut`` (which moves one boundary and must preserve which
    elements are inside) a *move* slides the whole subtree together — the cut's
    bounds, every descendant cut's bounds, the vertices and predicates in its
    descendant areas, and the ligature points that ride inside it.  Because the
    contents move with the boundary, interior membership is preserved by
    construction; the structural risk is only at the cut's *own* boundary.

    Raises ``Regime3Violation`` if the translated cut would:
      - leave its parent area (translated outer bounds no longer fit inside the
        parent cut's bounds) — a change of nesting depth, not regime-3;
      - absorb a non-descendant vertex/predicate (one that didn't move would
        fall inside the translated bounds);
      - overlap a non-descendant cut.

    A line of identity that *crosses* the cut boundary keeps its outside
    endpoint fixed and its inside endpoint translated, so the crossing is
    preserved; the §3.3 attestation backstops the stretched segment.
    """
    if cut_id not in dto.cut_bounds:
        raise Regime3Violation(f"move_cut: {cut_id} not in dto.cut_bounds")
    cut_ids = {c.id for c in egi.Cut}
    if cut_id not in cut_ids:
        raise Regime3Violation(f"move_cut: {cut_id} is not a cut in the EGI")

    parent_map = cut_parents(egi)
    elem_area_map = element_area(egi)
    own_areas = _descendant_areas(egi, cut_id)  # cut_id + descendant cut ids

    def tbox(b: BoundingBox) -> BoundingBox:
        return BoundingBox(b.min_x + dx, b.min_y + dy, b.max_x + dx, b.max_y + dy)

    def tpt(p: Point) -> Point:
        return Point(p.x + dx, p.y + dy)

    new_outer = tbox(dto.cut_bounds[cut_id])

    # 1. Parent containment — the cut may not slide out of its enclosing area.
    parent = parent_map.get(cut_id)
    if parent is not None and parent in dto.cut_bounds:
        if not _bounds_in(new_outer, dto.cut_bounds[parent]):
            raise Regime3Violation(
                f"move_cut: translating {cut_id} by ({dx}, {dy}) would push it "
                f"outside its parent area {parent} — a change of nesting, not a "
                f"regime-3 op."
            )

    # 2. No non-descendant vertex/predicate (which does not move) may end up
    #    inside the translated bounds.
    for eid, pos in list(dto.vertex_positions.items()) + list(
        dto.predicate_positions.items()
    ):
        if elem_area_map.get(eid) in own_areas:
            continue  # descendant — rides along, stays in by construction
        if _point_in(pos, new_outer):
            raise Regime3Violation(
                f"move_cut: the moved cut {cut_id} would come to enclose "
                f"{eid}, which is not inside it — that would change the area "
                f"hierarchy."
            )

    # 3. No *unrelated* cut may overlap the translated bounds. A cut's own
    #    ancestors are excluded: a nested cut legitimately sits *inside* its
    #    parent chain (that containment is required, and checked in step 1) —
    #    flagging the parent as an "overlap" would freeze every nested cut in
    #    place (it can never leave its parent, so it always overlaps it). Only
    #    siblings / cousins / their subtrees are genuine collisions.
    ancestors: Set[ElementID] = set()
    cur = parent_map.get(cut_id)
    while cur is not None:
        ancestors.add(cur)
        cur = parent_map.get(cur)
    for other_id, other_bounds in dto.cut_bounds.items():
        if other_id in own_areas or other_id in ancestors:
            continue  # self / descendant (moves with it) or ancestor (contains it)
        if _bounds_overlap(other_bounds, new_outer):
            raise Regime3Violation(
                f"move_cut: the moved cut {cut_id} would overlap cut "
                f"{other_id}, which is not part of it."
            )

    # Build the translated DTO: every moving cut / element / inside-point shifts.
    new_cut_bounds = dict(dto.cut_bounds)
    for cid in dto.cut_bounds:
        if cid in own_areas:
            new_cut_bounds[cid] = tbox(dto.cut_bounds[cid])

    new_vpos = dict(dto.vertex_positions)
    moved_v: Set[ElementID] = set()
    for vid, pos in dto.vertex_positions.items():
        if elem_area_map.get(vid) in own_areas:
            new_vpos[vid] = tpt(pos)
            moved_v.add(vid)

    new_ppos = dict(dto.predicate_positions)
    moved_p: Set[ElementID] = set()
    for pid, pos in dto.predicate_positions.items():
        if elem_area_map.get(pid) in own_areas:
            new_ppos[pid] = tpt(pos)
            moved_p.add(pid)

    old_outer = dto.cut_bounds[cut_id]
    new_paths = []
    for path in dto.ligature_paths:
        pts = list(path.points)
        if pts:
            if path.predicate_id in moved_p:
                pts[0] = tpt(pts[0])
            if path.vertex_id in moved_v:
                pts[-1] = tpt(pts[-1])
            for i in range(1, len(pts) - 1):
                if _point_in(path.points[i], old_outer):
                    pts[i] = tpt(path.points[i])
        new_paths.append(
            LigaturePath(
                predicate_id=path.predicate_id,
                vertex_id=path.vertex_id,
                points=tuple(pts),
                port_index=path.port_index,
            )
        )

    return _clone_dto(
        dto,
        vertex_positions=new_vpos,
        predicate_positions=new_ppos,
        cut_bounds=new_cut_bounds,
        ligature_paths=new_paths,
    )


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
    "crossing_sequence",
    "count_boundary_crossings",
    "point_in_cut",
    "bounds_in_cut",
    "predicate_label_box",
    "box_intrudes_cut",
    "vertex_label_box",
    "place_label_boxes",
    "boxes_overlap",
    "path_intersects_box",
    "count_cut_crossings",
    "cut_boundary",
    "resolve_cut_boundaries",
    "point_in_polygon",
    "polyline_polygon_crossings",
    "deepest_containing_cut",
    "move_vertex",
    "move_predicate",
    "reshape_cut",
    "move_cut",
    "reroute_ligature",
]
