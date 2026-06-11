"""
Shared layout DTO types for Arisbe layout engines.

Both ELKLayoutEngine and UnifiedD3Engine produce LayoutDTO objects.
Importing from this module is the canonical way to access these types.
For backward compatibility, unified_d3_engine.py re-exports them all.
"""

from typing import Dict, List, Optional, Set, Tuple
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
    """Path for a ligature connection.

    `port_index` is the 0-based position of `vertex_id` in the
    predicate's ν tuple — i.e. argument 1 has port_index=0, argument 2
    has port_index=1, etc.  When a vertex appears multiple times in the
    same predicate's ν (e.g. (Eq *x x)), each occurrence becomes a
    distinct LigaturePath with its own port_index.
    """
    predicate_id: ElementID
    vertex_id: ElementID
    points: Tuple[Point, ...]
    port_index: int = 0
    # The argument-order numeral drawn on this line, or None to draw none.  Set
    # by the active style's order convention (eg_reader.assign_order_labels):
    # "numbered" labels every ≥2-ary line; "clockwise" labels only where the
    # natural clockwise reading of the hooks would not match ν (Peirce's
    # Convention-13 numeric-index override).  When set it is the 1-based index;
    # the renderer draws it and eg_reader reads it back.
    order_label: Optional[int] = None


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
    # Optional per-cut **drawn boundary** as an explicit closed polyline (the
    # literal curve, Phase 4 of docs/EXACT_CORRESPONDENCE.md).  Present for a cut
    # that has no analytic shape behind it — a human-drawn cut on the freeform
    # canvas, where the polyline IS the cut.  When absent, the boundary is derived
    # from cut_bounds + the style (rounded rectangle / inscribed ellipse / wobble);
    # see presentation_ops.resolve_cut_boundaries.  §3.3 and the browser both read
    # containment off this curve.
    cut_boundary: Optional[Dict[ElementID, Tuple[Point, ...]]] = None
