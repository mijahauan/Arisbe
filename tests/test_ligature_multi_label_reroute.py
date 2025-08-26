#!/usr/bin/env python3
"""
Multi-label rerouting tests:
- Ligature paths avoid pass-throughs across multiple predicate label rectangles
- Reuses the Chapter 16 helpers to validate segments
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from styling.style_manager import create_style_manager
from qt_correspondence_integration import create_qt_correspondence_integration
from egi_system import create_egi_system

# Import helper functions from chapter16 test by copying minimal logic
# (We avoid importing test internals across files.)

def _rect_from_bounds(b: Dict[str, float]) -> Tuple[float, float, float, float]:
    return float(b.get("x", 0.0)), float(b.get("y", 0.0)), float(b.get("width", 0.0)), float(b.get("height", 0.0))


def _orientation(a: Tuple[float, float], b: Tuple[float, float], c: Tuple[float, float]) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _on_segment(a: Tuple[float, float], b: Tuple[float, float], c: Tuple[float, float]) -> bool:
    return min(a[0], b[0]) - 1e-9 <= c[0] <= max(a[0], b[0]) + 1e-9 and min(a[1], b[1]) - 1e-9 <= c[1] <= max(a[1], b[1]) + 1e-9


def _segments_intersect(p1: Tuple[float, float], p2: Tuple[float, float], q1: Tuple[float, float], q2: Tuple[float, float]) -> bool:
    o1 = _orientation(p1, p2, q1)
    o2 = _orientation(p1, p2, q2)
    o3 = _orientation(q1, q2, p1)
    o4 = _orientation(q1, q2, p2)
    if o1 * o2 < 0 and o3 * o4 < 0:
        return True
    if abs(o1) < 1e-9 and _on_segment(p1, p2, q1):
        return True
    if abs(o2) < 1e-9 and _on_segment(p1, p2, q2):
        return True
    if abs(o3) < 1e-9 and _on_segment(q1, q2, p1):
        return True
    if abs(o4) < 1e-9 and _on_segment(q1, q2, p2):
        return True
    return False


def _segment_intersects_rect(p0: Tuple[float, float], p1: Tuple[float, float], rect: Tuple[float, float, float, float]) -> bool:
    x, y, w, h = rect
    rx0, ry0, rx1, ry1 = x, y, x + w, y + h
    x0, y0 = p0
    x1, y1 = p1
    if (x0 < rx0 and x1 < rx0) or (x0 > rx1 and x1 > rx1) or (y0 < ry0 and y1 < ry0) or (y0 > ry1 and y1 > ry1):
        return False
    inside0 = (rx0 < x0 < rx1) and (ry0 < y0 < ry1)
    inside1 = (rx0 < x1 < rx1) and (ry0 < y1 < ry1)
    if inside0 or inside1:
        return True
    edges = [((rx0, ry0), (rx1, ry0)), ((rx1, ry0), (rx1, ry1)), ((rx1, ry1), (rx0, ry1)), ((rx0, ry1), (rx0, ry0))]
    for a, b in edges:
        if _segments_intersect(p0, p1, a, b):
            return True
    return False


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


def _collect_pred_rects(render_commands: List[Dict[str, Any]]) -> List[Tuple[float, float, float, float]]:
    pred_rects: List[Tuple[float, float, float, float]] = []
    for cmd in render_commands:
        if cmd.get("type") == "edge":
            pred_rects.append(_rect_from_bounds(cmd.get("bounds", {})))
    return pred_rects


def test_ligature_avoids_multiple_label_rects():
    styles = create_style_manager()
    egi = create_egi_system()
    v = "Alice"
    egi.insert_vertex(v)
    # Insert several predicates likely to cluster near the vertex label rects
    preds = [
        ("e1", "Knows"),
        ("e2", "Loves"),
        ("e3", "Hates"),
        ("e4", "Respects"),
    ]
    for pid, name in preds:
        egi.insert_edge(pid, name, [v])

    integration = create_qt_correspondence_integration(egi)
    scene = integration.generate_qt_scene()
    cmds = scene.get("render_commands", [])

    pred_rects = _collect_pred_rects(cmds)
    lig_paths: List[List[Tuple[float, float]]] = [cmd.get("path_points", []) for cmd in cmds if cmd.get("type") == "ligature"]

    # Validate: no segment performs a true pass-through of any predicate label rect
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
                a_in = _point_in_rect(a, r) or _point_on_rect_border(a, r)
                b_in = _point_in_rect(b, r) or _point_on_rect_border(b, r)
                # Allow single-endpoint entries/exits; forbid pass-throughs
                assert a_in ^ b_in, f"Ligature segment pass-through across label rect {r}: {a}->{b}"
