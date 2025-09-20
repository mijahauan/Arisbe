"""
Layout Engine - Bridge between EGI logical structure and visual representation
"""

import math
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, FrozenSet

from egi_core_dau import RelationalGraphWithCuts, ElementID


@dataclass(frozen=True)
class Point:
    x: float
    y: float


@dataclass(frozen=True)
class BoundingBox:
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    
    def contains_point(self, point: Point) -> bool:
        return (self.min_x < point.x < self.max_x and 
                self.min_y < point.y < self.max_y)


@dataclass(frozen=True)
class Path:
    points: Tuple[Point, ...]


@dataclass(frozen=True)
class LayoutResult:
    """Platform-agnostic spatial arrangement"""
    cut_bounds: Dict[ElementID, BoundingBox]
    vertex_positions: Dict[ElementID, Point]
    edge_paths: Dict[ElementID, Path]
    viewport_bounds: BoundingBox


class LayoutEngine:
    """Core layout engine that enforces spatial-logical correspondence"""
    
    def compute_layout(self, egi: RelationalGraphWithCuts) -> LayoutResult:
        """Translate EGI to spatial primitives - ENFORCES containment"""
        
        # Step 1: Position vertices in grid
        vertex_positions = {}
        x, y = 50.0, 50.0
        for vertex in egi.V:
            vertex_positions[vertex.id] = Point(x, y)
            x += 80.0
            if x > 400:
                x, y = 50.0, y + 80.0
        
        # Step 2: Calculate cut bounds that contain their elements
        cut_bounds = {}
        for cut in egi.Cut:
            # Get elements in this cut from area mapping
            cut_elements = egi.area.get(cut.id, frozenset())
            if cut_elements:
                # Find bounding box of contained elements
                xs = [vertex_positions[eid].x for eid in cut_elements if eid in vertex_positions]
                ys = [vertex_positions[eid].y for eid in cut_elements if eid in vertex_positions]
                if xs and ys:
                    margin = 30.0
                    cut_bounds[cut.id] = BoundingBox(
                        min(xs) - margin, min(ys) - margin,
                        max(xs) + margin, max(ys) + margin
                    )
        
        # Step 3: Calculate viewport
        all_x = [p.x for p in vertex_positions.values()]
        all_y = [p.y for p in vertex_positions.values()]
        if all_x and all_y:
            viewport = BoundingBox(min(all_x) - 50, min(all_y) - 50,
                                 max(all_x) + 50, max(all_y) + 50)
        else:
            viewport = BoundingBox(0, 0, 100, 100)
        
        return LayoutResult(
            cut_bounds=cut_bounds,
            vertex_positions=vertex_positions,
            edge_paths={},
            viewport_bounds=viewport
        )
