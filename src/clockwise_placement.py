"""Canonical clockwise hook placement — Peirce's Convention-13 placement as the
argument-order carrier (`docs/EXACT_CORRESPONDENCE.md` Phase 3c).

Under the **clockwise** argument-order convention a relation's argument order (its
ν sequence) is read off the *clockwise order its hooks leave the spot*, from
vertically-above (Peirce, CP 4.470 / Conv. 13).  The reader
(``eg_reader._clockwise_order``) already recovers ν from those hook angles.  The
gap this closes is *robustness*: when two hooks leave the spot at nearly the same
angle (the shared-vertex fan-in — ``roberts_domain_modeling`` has two hooks 0.6°
apart), the clockwise reading is fragile and a person could not tell the order
without the numeral.  This pass **spreads a fragile predicate's hooks into
well-separated slots**, so the placement carries order unambiguously and the
numeral can be safely hidden (``argument_order_numerals: never``).

It is a **hybrid, no-crossing** move:

- It re-hooks a predicate *only* when its hooks are fragile (a pair closer than
  ``FRAGILE_BELOW_DEG``), leaving comfortable layouts untouched.
- It **preserves the hooks' natural cyclic order** (each path keeps its rank in
  the clockwise-from-above sort), so no two lines are made to cross near the
  spot — it only widens the gaps.  A predicate whose hooks already read ν keeps
  reading ν (now robustly); one whose natural order ≠ ν still reads its natural
  order, so the Convention-13 numeric override (``assign_order_labels``) still
  fires for it under ``auto`` — exactly the cases geometry cannot fix without a
  crossing.

Each re-hooked predicate is validated locally (the ligature crossing-multiset and
its area endpoints must be unchanged — the §3.3 identity properties); a predicate
that would not stay sound is reverted to its original hooks.  The whole result is
re-attested by the caller as a backstop.
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

# A predicate is "fragile" — worth re-hooking — when its two closest hooks leave
# the spot within this many degrees of each other (the reader cannot reliably
# order them).  Comfortable layouts (all gaps wider) are left untouched.
FRAGILE_BELOW_DEG = 15.0

# The target separation a re-hooked predicate's adjacent hooks are spread to.
TARGET_GAP_DEG = 40.0


def _key(theta: float) -> float:
    """Clockwise-from-vertically-above sort key, matching ``eg_reader``: screen y
    grows downward, so increasing ``atan2`` is clockwise; rotate so straight-up
    (−y) is the 0 start."""
    return (theta + math.pi / 2.0) % (2.0 * math.pi)


def place_clockwise_hooks(
    egi, dto: LayoutDTO, style, engine
) -> LayoutDTO:
    """Return ``dto`` with fragile ≥2-ary predicates' hooks spread into
    well-separated clockwise slots (natural order preserved).  Only acts under
    the clockwise convention; otherwise returns ``dto`` unchanged.

    ``engine`` is an ``ELKLayoutEngine`` (its static ``_predicate_hook_point`` /
    ``_route_avoiding_cuts`` / ``_authorized_cuts`` and ``_compute_element_sizes``
    are reused so the re-hooked lines route around cuts and label boxes exactly
    as the cold layout does).
    """
    if getattr(style, "argument_order_convention", "numbered") != "clockwise":
        return dto

    cut_shape = getattr(style, "cut_shape", "rounded_rectangle")
    cut_radius = float(getattr(style, "cut_corner_radius", 0) or 0)
    cut_bounds = dto.cut_bounds
    parent_map = cut_parents(egi)
    elem_area = element_area(egi)
    sizes = engine._compute_element_sizes(egi, style)

    # Label boxes (owner-tagged) — soft obstacles for the rerouted stubs, exactly
    # as ``_build_ligature_paths`` treats them.
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
        paths = [dto.ligature_paths[i] for i in idxs]
        if any(len(p.points) < 2 for p in paths):
            continue

        # Natural hook keys (the direction each line currently leaves the spot).
        def nat_key(p: LigaturePath) -> float:
            ref = p.points[1]
            return _key(math.atan2(ref.y - P.y, ref.x - P.x))

        keys = [nat_key(p) for p in paths]
        ordered = sorted(range(len(paths)), key=lambda k: keys[k])  # C
        skeys = sorted(keys)
        gaps = [
            (skeys[(j + 1) % len(skeys)] - skeys[j]) % (2.0 * math.pi)
            for j in range(len(skeys))
        ]
        if not gaps or math.degrees(min(gaps)) >= FRAGILE_BELOW_DEG:
            continue  # comfortable separation already — leave it untouched

        # Canonical slots: evenly spread by TARGET_GAP_DEG, centred on the mean
        # direction of the incident vertices (so the fan still faces them).
        vdirs = [
            math.atan2(
                dto.vertex_positions[p.vertex_id].y - P.y,
                dto.vertex_positions[p.vertex_id].x - P.x,
            )
            for p in paths
        ]
        mx = sum(math.cos(a) for a in vdirs)
        my = sum(math.sin(a) for a in vdirs)
        mean = math.atan2(my, mx) if (mx or my) else 0.0
        n = len(paths)
        step = math.radians(TARGET_GAP_DEG)
        slot_thetas = [mean + (j - (n - 1) / 2.0) * step for j in range(n)]
        # Assign the j-th-smallest-key slot to the j-th-smallest-key path, so the
        # clockwise rank of every path is preserved (no reorder ⇒ no crossing).
        slot_by_key = sorted(range(n), key=lambda j: _key(slot_thetas[j]))
        assign: Dict[int, float] = {}
        for j in range(n):
            assign[ordered[j]] = slot_thetas[slot_by_key[j]]

        pred_w, pred_h = sizes.get(pid, (40.0, 16.0))
        candidate: Dict[int, LigaturePath] = {}
        sound = True
        for local_k, gi in enumerate(idxs):
            old = dto.ligature_paths[gi]
            theta = assign[local_k]
            dirx, diry = math.cos(theta), math.sin(theta)
            far = Point(P.x + dirx * 1000.0, P.y + diry * 1000.0)
            hook = engine._predicate_hook_point(P, pred_w, pred_h, far)
            stub_d = math.hypot(hook.x - P.x, hook.y - P.y) + 14.0
            stub = Point(P.x + dirx * stub_d, P.y + diry * stub_d)
            vpos = dto.vertex_positions.get(old.vertex_id)
            if vpos is None:
                sound = False
                break

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
                stub, vpos, hard, soft_obstacles=soft,
                detour_pad=engine.conventions.detour_pad,
                visibility_pad=engine.conventions.visibility_pad,
            )
            points = (hook,) + tuple(route)  # points[1] == stub ⇒ reads the slot
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
    # Vertex endpoint pinned.
    if (pts[-1].x, pts[-1].y) != (old_p.points[-1].x, old_p.points[-1].y):
        return False
    # Predicate-side endpoint must sit in the predicate's area cut (if any).
    p_area = elem_area.get(new_p.predicate_id)
    if p_area in cut_bounds:
        if not point_in_cut(pts[0], cut_bounds[p_area], cut_shape, cut_radius):
            return False
    # Crossing-multiset: every cut crossed exactly as required.
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
    # Occlusion: not through a non-incident label box.
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
