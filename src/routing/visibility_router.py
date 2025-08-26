#!/usr/bin/env python3
"""
Visibility-graph router using pyvisgraph to compute obstacle-avoiding paths.
Falls back gracefully if pyvisgraph is unavailable.

Obstacles are provided as axis-aligned rectangles: (x, y, w, h).
Returns a polyline as list of (x, y) tuples, or [] if no route found.
"""
from __future__ import annotations
from typing import List, Tuple

try:
    import pyvisgraph as vg
except Exception:  # pragma: no cover - optional dependency
    vg = None


class PyVisVisibilityRouter:
    def __init__(self, pad: float = 0.0):
        # Optional outward padding of obstacles (already padded by caller typically)
        self.pad = float(pad)

    def _rect_to_polygon(self, r: Tuple[float, float, float, float]) -> List[vg.Point]:
        x, y, w, h = r
        x -= self.pad
        y -= self.pad
        w += 2 * self.pad
        h += 2 * self.pad
        return [
            vg.Point(x, y),
            vg.Point(x + w, y),
            vg.Point(x + w, y + h),
            vg.Point(x, y + h),
        ]

    def route(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        obstacles: List[Tuple[float, float, float, float]],
    ) -> List[Tuple[float, float]]:
        if vg is None:
            return []
        try:
            # Build polygons for visibility graph
            polys = [self._rect_to_polygon(r) for r in obstacles]
            g = vg.VisGraph()
            # Build graph; use workers=1 to avoid multiprocessing complexities in IDE
            g.build(polys, workers=1)
            rs = vg.Point(start[0], start[1])
            re = vg.Point(end[0], end[1])
            path = g.shortest_path(rs, re)
            if not path:
                return []
            pts = [(p.x, p.y) for p in path]
            # Ensure start and end included
            if pts[0] != (start[0], start[1]):
                pts.insert(0, (start[0], start[1]))
            if pts[-1] != (end[0], end[1]):
                pts.append((end[0], end[1]))
            # Deduplicate consecutive duplicates
            compact: List[Tuple[float, float]] = []
            for p in pts:
                if not compact or compact[-1] != p:
                    compact.append(p)
            return compact
        except Exception:
            return []
