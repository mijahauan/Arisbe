#!/usr/bin/env python3
"""
Shared rendering geometry utilities for EG diagrams (Dau/Peirce conventions).

Centralizes geometry used by renderers and exporters so there is a single
source of truth for predicate periphery hooks, junction placement, and basic
path helpers.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional

Coordinate = Tuple[float, float]
Bounds = Tuple[float, float, float, float]  # x1, y1, x2, y2


def predicate_periphery_point(bounds: Bounds, toward: Coordinate) -> Coordinate:
    """Compute the connection point on the rectangle periphery in the direction of 'toward'.

    This matches the Dau convention: heavy identity lines terminate on the
    predicate text periphery (no separate hook line). The rectangle represents
    the padded text bounds.
    """
    x1, y1, x2, y2 = bounds
    cx = (x1 + x2) / 2.0
    cy = (y1 + y2) / 2.0
    tx, ty = toward
    dx, dy = tx - cx, ty - cy
    if abs(dx) < 1e-6 and abs(dy) < 1e-6:
        return (cx, y1)
    candidates: List[Coordinate] = []
    if abs(dx) > 1e-6:
        t_left = (x1 - cx) / dx
        y_left = cy + t_left * dy
        if y1 <= y_left <= y2:
            candidates.append((x1, y_left))
        t_right = (x2 - cx) / dx
        y_right = cy + t_right * dy
        if y1 <= y_right <= y2:
            candidates.append((x2, y_right))
    if abs(dy) > 1e-6:
        t_top = (y1 - cy) / dy
        x_top = cx + t_top * dx
        if x1 <= x_top <= x2:
            candidates.append((x_top, y1))
        t_bottom = (y2 - cy) / dy
        x_bottom = cx + t_bottom * dx
        if x1 <= x_bottom <= x2:
            candidates.append((x_bottom, y2))
    if candidates:
        candidates.sort(key=lambda p: (p[0]-tx)**2 + (p[1]-ty)**2)
        return candidates[0]
    return (cx, cy)


def branching_junction(vertex_pos: Coordinate, hooks: List[Coordinate]) -> Coordinate:
    """Return the junction point for degree ≥ 3 ligatures.

    For now, use the vertex position as the junction. Future improvements may
    bias the junction slightly to minimize angular distortion or avoid overlaps.
    """
    return vertex_pos


def straight_path(p0: Coordinate, p1: Coordinate) -> List[Coordinate]:
    """Return a simple straight path between two points (as a list of points)."""
    return [p0, p1]
