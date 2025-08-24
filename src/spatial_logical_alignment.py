"""
Minimal spatial_logical_alignment module for tests.
Provides SpatialBounds and SpatialElement used by test_spatial_logical_alignment.py.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class SpatialBounds:
    x: float
    y: float
    width: float
    height: float

    def contains_point(self, px: float, py: float) -> bool:
        return (self.x <= px <= self.x + self.width and self.y <= py <= self.y + self.height)

    def to_dict(self) -> Dict[str, float]:
        return {"x": self.x, "y": self.y, "width": self.width, "height": self.height}


@dataclass
class SpatialElement:
    id: str
    type: str  # e.g., 'vertex', 'predicate', 'cut'
    bounds: SpatialBounds
    logical_area: str

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type,
            "bounds": self.bounds.to_dict(),
            "logical_area": self.logical_area,
        }


__all__ = ["SpatialBounds", "SpatialElement"]


# Minimal alignment engine API expected by VisualEGIBridge
class SpatialAlignmentEngine:
    """Lightweight engine that produces a simple layout and handles drags.

    This stub ensures imports and calls from VisualEGIBridge work during tests
    without implementing full constraint logic. It returns a basic empty layout
    and treats drags as no-ops (no logical area changes computed here).
    """

    def __init__(self, egi):
        # Hold a reference to the EGI if needed later
        self.egi = egi

    def generate_layout(self) -> Dict[str, SpatialElement]:
        """Produce a minimal layout dictionary keyed by element id.

        For now, return an empty layout to avoid imposing spatial assumptions.
        VisualEGIBridge can still operate (it will see no change on drag).
        """
        return {}

    def handle_spatial_drag(
        self,
        current_layout: Dict[str, SpatialElement],
        element_id: str,
        new_position: Tuple[float, float],
    ) -> Dict[str, SpatialElement]:
        """Return an updated layout after a drag attempt.

        This stub returns the layout unchanged, effectively rejecting spatial
        changes while allowing the test path to execute without errors.
        """
        return current_layout


def create_spatial_alignment_engine(egi) -> SpatialAlignmentEngine:
    """Factory for the minimal alignment engine used by tests."""
    return SpatialAlignmentEngine(egi)

__all__.extend(["SpatialAlignmentEngine", "create_spatial_alignment_engine"])
