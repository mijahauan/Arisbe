"""
Shared layout DTO types for Arisbe layout engines.

Both ELKLayoutEngine and UnifiedD3Engine produce LayoutDTO objects.
Importing from this module is the canonical way to access these types.
For backward compatibility, unified_d3_engine.py re-exports them all.
"""

from typing import Dict, List, Set, Tuple
from dataclasses import dataclass

from egi_core_dau import ElementID


@dataclass
class Point:
    """2D point."""
    x: float
    y: float


@dataclass
class BoundingBox:
    """Axis-aligned bounding box."""
    min_x: float
    min_y: float
    max_x: float
    max_y: float

    @property
    def width(self) -> float:
        return self.max_x - self.min_x

    @property
    def height(self) -> float:
        return self.max_y - self.min_y

    @property
    def center(self) -> Point:
        return Point(
            (self.min_x + self.max_x) / 2,
            (self.min_y + self.max_y) / 2,
        )


@dataclass
class LigaturePath:
    """Path for a ligature connection."""
    predicate_id: ElementID
    vertex_id: ElementID
    points: Tuple[Point, ...]


@dataclass
class LayoutDTO:
    """Platform-independent layout result."""
    vertex_positions: Dict[ElementID, Point]
    predicate_positions: Dict[ElementID, Point]
    cut_bounds: Dict[ElementID, BoundingBox]
    ligature_paths: List[LigaturePath]
    area_hierarchy: Dict[ElementID, Set[ElementID]]
    viewport_bounds: BoundingBox
    sheet_id: ElementID
    style: object = None
