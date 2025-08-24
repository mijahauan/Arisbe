#!/usr/bin/env python3
"""
Chapter 16 compliance tests:
- Ligature paths do not intersect predicate label rectangles
- Ligature paths do not intersect vertex label rectangles (estimated from style tokens)
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple
import math

from styling.style_manager import create_style_manager
from qt_correspondence_integration import create_qt_correspondence_integration
from egi_system import create_egi_system


def _rect_from_bounds(b: Dict[str, float]) -> Tuple[float, float, float, float]:
    return float(b.get("x", 0.0)), float(b.get("y", 0.0)), float(b.get("width", 0.0)), float(b.get("height", 0.0))


def _segment_intersects_rect(p0: Tuple[float, float], p1: Tuple[float, float], rect: Tuple[float, float, float, float]) -> bool:
    # Liang-Barsky or Cohen–Sutherland would be ideal; use robust AABB and segment clipping.
    x, y, w, h = rect
    rx0, ry0, rx1, ry1 = x, y, x + w, y + h

    x0, y0 = p0
    x1, y1 = p1

    # Quick reject if both points on one outside side
    if (x0 < rx0 and x1 < rx0) or (x0 > rx1 and x1 > rx1) or (y0 < ry0 and y1 < ry0) or (y0 > ry1 and y1 > ry1):
        return False

    # If either endpoint is strictly inside the rect
    inside0 = (rx0 < x0 < rx1) and (ry0 < y0 < ry1)
    inside1 = (rx0 < x1 < rx1) and (ry0 < y1 < ry1)
    if inside0 or inside1:
        return True

    # Check intersection with all four edges
    edges = [((rx0, ry0), (rx1, ry0)), ((rx1, ry0), (rx1, ry1)), ((rx1, ry1), (rx0, ry1)), ((rx0, ry1), (rx0, ry0))]
    for a, b in edges:
        if _segments_intersect(p0, p1, a, b):
            return True
    return False


def _orientation(a: Tuple[float, float], b: Tuple[float, float], c: Tuple[float, float]) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _on_segment(a: Tuple[float, float], b: Tuple[float, float], c: Tuple[float, float]) -> bool:
    return min(a[0], b[0]) - 1e-9 <= c[0] <= max(a[0], b[0]) + 1e-9 and min(a[1], b[1]) - 1e-9 <= c[1] <= max(a[1], b[1]) + 1e-9


def _segments_intersect(p1: Tuple[float, float], p2: Tuple[float, float], q1: Tuple[float, float], q2: Tuple[float, float]) -> bool:
    o1 = _orientation(p1, p2, q1)
    o2 = _orientation(p1, p2, q2)
    o3 = _orientation(q1, q2, p1)
    o4 = _orientation(q1, q2, p2)

    # General case
    if o1 * o2 < 0 and o3 * o4 < 0:
        return True

    # Colinear special cases
    if abs(o1) < 1e-9 and _on_segment(p1, p2, q1):
        return True
    if abs(o2) < 1e-9 and _on_segment(p1, p2, q2):
        return True
    if abs(o3) < 1e-9 and _on_segment(q1, q2, p1):
        return True
    if abs(o4) < 1e-9 and _on_segment(q1, q2, p2):
        return True

    return False


def _estimate_vertex_label_rect(center: Tuple[float, float], name: str, styles) -> Tuple[float, float, float, float]:
    s = styles.resolve(type="vertex", role="vertex.label_text")
    ecw = float(s.get("estimate_char_width", 6.0))
    eh = float(s.get("estimate_height", 12.0))
    pad = s.get("padding", [2, 1])
    off = s.get("offset", [8, -8])
    try:
        pad_x = float(pad[0]) if isinstance(pad, (list, tuple)) else 2.0
        pad_y = float(pad[1]) if isinstance(pad, (list, tuple)) else 1.0
    except Exception:
        pad_x, pad_y = 2.0, 1.0
    try:
        off_x = float(off[0]) if isinstance(off, (list, tuple)) else 8.0
        off_y = float(off[1]) if isinstance(off, (list, tuple)) else -8.0
    except Exception:
        off_x, off_y = 8.0, -8.0

    w = max(10.0, ecw * len(name) + 2 * pad_x)
    h = eh + 2 * pad_y
    cx, cy = center
    x = cx + off_x
    y = cy + off_y
    return x, y, w, h


def _collect_rects(render_commands: List[Dict[str, Any]], styles) -> Tuple[List[Tuple[float, float, float, float]], List[Tuple[float, float, float, float]]]:
    pred_rects: List[Tuple[float, float, float, float]] = []
    vertex_label_rects: List[Tuple[float, float, float, float]] = []

    vertex_centers: Dict[str, Tuple[float, float]] = {}
    for cmd in render_commands:
        if cmd.get("type") == "edge":
            pred_rects.append(_rect_from_bounds(cmd.get("bounds", {})))
        elif cmd.get("type") == "vertex":
            b = cmd.get("bounds", {})
            cx = float(b.get("x", 0.0)) + float(b.get("width", 0.0)) / 2.0
            cy = float(b.get("y", 0.0)) + float(b.get("height", 0.0)) / 2.0
            vertex_centers[cmd.get("element_id", "")] = (cx, cy)

    # Build vertex label rects
    for cmd in render_commands:
        if cmd.get("type") == "vertex":
            name = cmd.get("vertex_name") or cmd.get("element_id", "")
            center = vertex_centers.get(cmd.get("element_id", ""))
            if center:
                vertex_label_rects.append(_estimate_vertex_label_rect(center, name, styles))

    return pred_rects, vertex_label_rects


def _point_in_rect(p: Tuple[float, float], r: Tuple[float, float, float, float]) -> bool:
    x, y, w, h = r
    return (x <= p[0] <= x + w) and (y <= p[1] <= y + h)


def _point_on_rect_border(p: Tuple[float, float], r: Tuple[float, float, float, float], eps: float = 1e-3) -> bool:
    x, y, w, h = r
    rx0, ry0, rx1, ry1 = x, y, x + w, y + h
    on_left = abs(p[0] - rx0) <= eps and ry0 - eps <= p[1] <= ry1 + eps
    on_right = abs(p[0] - rx1) <= eps and ry0 - eps <= p[1] <= ry1 + eps
    on_top = abs(p[1] - ry0) <= eps and rx0 - eps <= p[0] <= rx1 + eps
    on_bottom = abs(p[1] - ry1) <= eps and rx0 - eps <= p[0] <= rx1 + eps
    return on_left or on_right or on_top or on_bottom


def _rect_center(r: Tuple[float, float, float, float]) -> Tuple[float, float]:
    x, y, w, h = r
    return (x + w / 2.0, y + h / 2.0)


def _nearest_rect_to_point(p: Tuple[float, float], rects: List[Tuple[float, float, float, float]]) -> Tuple[float, float, float, float] | None:
    if not rects:
        return None
    best = None
    best_d2 = float('inf')
    for r in rects:
        cx, cy = _rect_center(r)
        d2 = (cx - p[0]) ** 2 + (cy - p[1]) ** 2
        if d2 < best_d2:
            best_d2 = d2
            best = r
    return best


def test_chapter16_no_ligature_cross_label_rects():
    styles = create_style_manager()

    # Build a simple graph with one vertex and two predicates connected to it
    egi = create_egi_system()
    v = "Tom"
    egi.insert_vertex(v)
    egi.insert_edge("e1", "Person", [v])
    egi.insert_edge("e2", "Happy", [v])

    integration = create_qt_correspondence_integration(egi)
    scene = integration.generate_qt_scene()
    cmds = scene.get("render_commands", [])

    pred_rects, vertex_label_rects = _collect_rects(cmds, styles)

    # Gather ligature paths
    lig_paths: List[List[Tuple[float, float]]] = [cmd.get("path_points", []) for cmd in cmds if cmd.get("type") == "ligature"]

    # Check all segments against all rectangles
    for path in lig_paths:
        if len(path) < 2:
            continue
        for i in range(1, len(path)):
            a = path[i - 1]
            b = path[i]
            for r in pred_rects:
                inter = _segment_intersects_rect(a, b, r)
                if not inter:
                    continue
                # Allow segments that EITHER enter or exit the predicate label rect (exactly one
                # endpoint lies inside or on its border). Forbid only true pass-throughs where both
                # endpoints are outside but the segment cuts across the rect.
                a_in = _point_in_rect(a, r) or _point_on_rect_border(a, r)
                b_in = _point_in_rect(b, r) or _point_on_rect_border(b, r)
                if a_in ^ b_in:
                    continue
                assert False, f"Ligature segment intersects predicate label rect: {r}"
            for r in vertex_label_rects:
                assert not _segment_intersects_rect(a, b, r), f"Ligature segment intersects vertex label rect: {r}"
