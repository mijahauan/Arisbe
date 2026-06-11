"""Clockwise hook placement — Peirce's writing convention for argument order
(`docs/EXACT_CORRESPONDENCE.md` Phase 3c).

ν *specifies* the argument order, so the drawing should *show* it: a relation's
hooks are placed **clockwise around the spot in ν-order**, by construction (CP
4.470 / Conv. 13).  The reader then recovers ν from the clockwise placement.
This is the writing convention — the order is in the geometry, not in a number on
every line.

Two design facts make it tractable:

- **Crossings are inevitable but minimized.**  A vertex shared by several
  relations can't sit in the clockwise-correct slot for all of them at once, so
  some lines must cross near a spot.  We minimize them by choosing the *rotation*
  of the clockwise fan that best aligns each hook slot with the direction its own
  vertex actually lies (a 1-parameter fit) — when the layout already placed the
  vertices in ν-clockwise order, the fit makes the hooks point straight at them
  and nothing crosses; otherwise it picks the orientation with the least bending.
- **One mark carries the start.**  The clockwise *order* is in the placement; a
  reader still needs to know which hook is ν's first.  Pinning the fan to
  "vertically above" would fight the crossing-minimizing fit, so instead a single
  start anchor (the numeral 1 on ν's first line — Conv. 13's start index, drawn by
  ``eg_reader.assign_order_labels``) marks it.  One mark, any arity — not a number
  on every line.

Each re-hooked line is rerouted around cuts and label boxes (the two-tier router)
and locally guarded (crossing-multiset + area endpoints unchanged, no
non-incident-box occlusion); a predicate that would not stay §3.3-sound is left at
its natural hooks.  The whole result is re-attested by the caller as a backstop.
"""

import dataclasses
import math
from typing import Dict, List, Tuple

from layout_dto import LayoutDTO, LigaturePath, Point, BoundingBox
from presentation_ops import (
    count_cut_crossings,
    crossing_sequence,
    cut_parents,
    element_area,
    path_intersects_box,
    point_in_cut,
    predicate_label_box,
    vertex_label_box,
)

# The widest a clockwise fan opens between adjacent hooks.  For low arity this
# keeps the spokes a comfortable fan facing the arguments rather than flung to
# opposite sides of the spot; for high arity the even spacing 2π/n is narrower
# and wins, so the hooks ring the spot like a clock face.
MAX_GAP_DEG = 75.0

# Rotation-fit search resolution (degrees).  The fan is rigidly rotated to the
# orientation that best aligns each hook with its vertex; 5° is finer than the
# eye resolves and cheap for the small n a relation has.
_FIT_STEP_DEG = 5.0


def _circ_dist(a: float, b: float) -> float:
    d = abs((a - b) % (2.0 * math.pi))
    return min(d, 2.0 * math.pi - d)


def place_clockwise_hooks(egi, dto: LayoutDTO, style, engine) -> LayoutDTO:
    """Return ``dto`` with every ≥2-ary predicate's hooks placed clockwise in
    ν-order (best-fit rotation, crossings minimized).  Only acts under the
    clockwise convention; otherwise returns ``dto`` unchanged.

    ``engine`` is an ``ELKLayoutEngine`` whose static ``_predicate_hook_point`` /
    ``_route_avoiding_cuts`` / ``_authorized_cuts`` and ``_compute_element_sizes``
    are reused, so the re-hooked lines route around cuts and label boxes exactly
    as the cold layout does.

    Applied for **every** style — drawing a relation's hooks clockwise in ν-order
    is correct layout, not a Peirce-only flourish, so the picture reads the same
    across styles and layouts.  The ``argument_order_convention`` style setting
    governs only whether numerals are *also* drawn (Dau numbers / Peirce anchor),
    not the placement.
    """
    cut_shape = getattr(style, "cut_shape", "rounded_rectangle")
    cut_radius = float(getattr(style, "cut_corner_radius", 0) or 0)
    cut_bounds = dto.cut_bounds
    parent_map = cut_parents(egi)
    elem_area = element_area(egi)
    sizes = engine._compute_element_sizes(egi, style)

    # Label boxes (owner-tagged) — soft obstacles for the rerouted stubs.
    show_vertex_labels = (
        getattr(style, "vertex_rendering_mode", "dot_and_label") != "dot_only"
    )
    label_boxes: List[Tuple[str, str, BoundingBox]] = []
    for edge in egi.E:
        c = dto.predicate_positions.get(edge.id)
        if c is not None:
            label_boxes.append((
                "predicate", edge.id,
                predicate_label_box(egi.get_relation_name(edge.id), c, style),
            ))
    if show_vertex_labels:
        for vertex in egi.V:
            if not getattr(vertex, "label", None):
                continue
            c = dto.vertex_positions.get(vertex.id)
            if c is not None:
                label_boxes.append((
                    "vertex", vertex.id,
                    vertex_label_box(vertex.label, c, style, dto.ligature_paths,
                                     vertex.id, egi=egi, cut_bounds=cut_bounds),
                ))

    # Index paths by predicate, preserving their position in dto.ligature_paths.
    by_pred: Dict[str, List[int]] = {}
    for i, p in enumerate(dto.ligature_paths):
        by_pred.setdefault(p.predicate_id, []).append(i)

    new_paths = list(dto.ligature_paths)

    for pid, idxs in by_pred.items():
        if len(idxs) < 2:
            continue
        P = dto.predicate_positions.get(pid)
        if P is None:
            continue
        # ν order = ascending port_index.
        order = sorted(idxs, key=lambda gi: dto.ligature_paths[gi].port_index)
        paths = [dto.ligature_paths[gi] for gi in order]
        verts = [dto.vertex_positions.get(p.vertex_id) for p in paths]
        if any(v is None for v in verts):
            continue
        n = len(paths)

        # Clockwise slots in ν-order at the best-fit rotation.  key increases
        # clockwise (= (θ+π/2) mod 2π); slot i at key base + i·g, so reading
        # clockwise-from-above visits the ports in ν-order (up to where the seam
        # falls — the single anchor pins that).
        dirs = [math.atan2(v.y - P.y, v.x - P.x) for v in verts]
        g = min(2.0 * math.pi / n, math.radians(MAX_GAP_DEG))
        steps = max(1, int(round(360.0 / _FIT_STEP_DEG)))
        best_thetas = None
        best_cost = None
        for s in range(steps):
            base = s / steps * 2.0 * math.pi
            thetas = [(base + i * g) - math.pi / 2.0 for i in range(n)]
            cost = sum(_circ_dist(thetas[i], dirs[i]) for i in range(n))
            if best_cost is None or cost < best_cost:
                best_cost, best_thetas = cost, thetas

        pred_w, pred_h = sizes.get(pid, (40.0, 16.0))
        candidate: Dict[int, LigaturePath] = {}
        sound = True
        for i, gi in enumerate(order):
            old = dto.ligature_paths[gi]
            theta = best_thetas[i]
            dirx, diry = math.cos(theta), math.sin(theta)
            far = Point(P.x + dirx * 1000.0, P.y + diry * 1000.0)
            # Hook on the spot's edge at the clockwise slot.  The line then runs
            # straight to its vertex — no artificial stub, so no kink/bend; the
            # *hook position* (points[0]) carries the order, read clockwise.
            hook = engine._predicate_hook_point(P, pred_w, pred_h, far)
            vpos = verts[i]

            pred_area = elem_area.get(pid)
            vert_area = elem_area.get(old.vertex_id)
            authorized = engine._authorized_cuts(pred_area, vert_area, parent_map)
            hard = [cut_bounds[c] for c in cut_bounds if c not in authorized]
            soft = [
                box for kind, owner, box in label_boxes
                if not ((kind == "predicate" and owner == pid)
                        or (kind == "vertex" and owner == old.vertex_id))
            ]
            route = engine._route_avoiding_cuts(
                hook, vpos, hard, soft_obstacles=soft,
                detour_pad=engine.conventions.detour_pad,
                visibility_pad=engine.conventions.visibility_pad,
            )
            points = tuple(route)  # points[0] == hook (the slot); straight to vertex
            new_p = dataclasses.replace(old, points=points)

            if not _path_sound(new_p, old, egi, cut_bounds, cut_shape, cut_radius,
                               parent_map, elem_area, label_boxes):
                sound = False
                break
            candidate[gi] = new_p

        if sound:
            for gi, np_ in candidate.items():
                new_paths[gi] = np_

    return dataclasses.replace(dto, ligature_paths=new_paths)


def _path_sound(
    new_p: LigaturePath, old_p: LigaturePath, egi, cut_bounds, cut_shape,
    cut_radius, parent_map, elem_area, label_boxes,
) -> bool:
    """Local §3.3 guard for one re-hooked line: its crossing-multiset and area
    endpoints must be unchanged (identity fidelity), and it must not be driven
    through a label box it is not incident to (occlusion check #3)."""
    pts = new_p.points
    if len(pts) < 2:
        return False
    if (pts[-1].x, pts[-1].y) != (old_p.points[-1].x, old_p.points[-1].y):
        return False
    p_area = elem_area.get(new_p.predicate_id)
    if p_area in cut_bounds:
        if not point_in_cut(pts[0], cut_bounds[p_area], cut_shape, cut_radius):
            return False
    v_area = elem_area.get(new_p.vertex_id, egi.sheet)
    pa = elem_area.get(new_p.predicate_id, egi.sheet)
    required = set(crossing_sequence(pa, v_area, parent_map))
    for cut in egi.Cut:
        b = cut_bounds.get(cut.id)
        if b is None:
            continue
        actual = count_cut_crossings(pts, b, cut_shape, cut_radius)
        if cut.id in required:
            if actual != 1:
                return False
        elif actual > 0:
            return False
    for kind, owner, box in label_boxes:
        incident = (
            (kind == "predicate" and owner == new_p.predicate_id)
            or (kind == "vertex" and owner == new_p.vertex_id)
        )
        if incident:
            continue
        if path_intersects_box(pts, box):
            return False
    return True
