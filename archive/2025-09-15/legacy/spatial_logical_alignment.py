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
        return (
            self.x <= px <= self.x + self.width and self.y <= py <= self.y + self.height
        )

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
    """Iron-clad spatial-logical correspondence enforcement engine.

    Maintains strict correspondence between spatial regions and logical areas:
    - Area transition ⟷ Negation transition
    - Juxtaposition within area ⟷ Conjunction within logical context
    - Every pixel belongs to exactly one logical area
    """

    def __init__(self, egi, region_manager=None):
        from spatial_region_manager import SpatialRegionManager

        self.egi = egi
        self.region_manager = region_manager or SpatialRegionManager(
            800, 600
        )  # Default canvas size
        self._initialize_regions_from_egi()

    def _initialize_regions_from_egi(self):
        """Initialize spatial regions based on EGI cut structure."""
        if not self.egi or not hasattr(self.egi, "Cut"):
            return

        # Create regions for each cut in the EGI
        for cut in self.egi.Cut:
            cut_area_id = f"cut_{cut.id}"
            parent_area_id = self._get_parent_area_for_cut(cut)

            try:
                self.region_manager.create_cut_region(
                    cut_logical_area_id=cut_area_id,
                    parent_logical_area_id=parent_area_id,
                )
            except ValueError as e:
                print(f"Warning: Could not create region for cut {cut.id}: {e}")

    def _get_parent_area_for_cut(self, cut) -> str:
        """Determine parent logical area for a cut based on EGI area mapping."""
        if hasattr(self.egi, "area") and hasattr(cut, "id"):
            # Find which area contains this cut
            for area_id, contents in self.egi.area.items():
                if cut.id in contents:
                    return area_id if area_id != "S" else "sheet"
        return "sheet"  # Default to sheet

    def generate_layout(self) -> Dict[str, SpatialElement]:
        """Generate layout with strict spatial-logical correspondence."""
        layout = {}

        if not self.egi:
            return layout

        # Generate spatial elements for vertices
        if hasattr(self.egi, "V"):
            for i, vertex in enumerate(self.egi.V):
                logical_area = self._get_logical_area_for_element(vertex.id)
                region = self.region_manager.get_region_for_logical_area(logical_area)

                if region:
                    # Position within the assigned region
                    x = region.x + 20 + (i % 3) * 40
                    y = region.y + 20 + (i // 3) * 40

                    layout[vertex.id] = SpatialElement(
                        id=vertex.id,
                        type="vertex",
                        bounds=SpatialBounds(x, y, 20, 20),
                        logical_area=logical_area,
                    )

        # Generate spatial elements for predicates/edges
        if hasattr(self.egi, "E"):
            for i, edge in enumerate(self.egi.E):
                logical_area = self._get_logical_area_for_element(edge.id)
                region = self.region_manager.get_region_for_logical_area(logical_area)

                if region:
                    # Position within the assigned region
                    x = region.x + 60 + (i % 2) * 80
                    y = region.y + 60 + (i // 2) * 50

                    layout[edge.id] = SpatialElement(
                        id=edge.id,
                        type="predicate",
                        bounds=SpatialBounds(x, y, 60, 30),
                        logical_area=logical_area,
                    )

        return layout

    def _get_logical_area_for_element(self, element_id: str) -> str:
        """Get the logical area assignment for an element from EGI."""
        if not hasattr(self.egi, "area"):
            return "sheet"

        for area_id, contents in self.egi.area.items():
            if element_id in contents:
                return area_id if area_id != "S" else "sheet"
        return "sheet"

    def handle_spatial_drag(
        self,
        current_layout: Dict[str, SpatialElement],
        element_id: str,
        new_position: Tuple[float, float],
    ) -> Dict[str, SpatialElement]:
        """Handle spatial drag with iron-clad correspondence enforcement."""
        x, y = new_position

        # Determine which logical area contains the new position
        new_logical_area = self.region_manager.get_logical_area_at_point(x, y)

        # Get current element
        current_element = current_layout.get(element_id)
        if not current_element:
            return current_layout

        old_logical_area = current_element.logical_area

        # Check if area transition occurred
        if new_logical_area != old_logical_area:
            print(
                f"CORRESPONDENCE: Element {element_id} transitioning from {old_logical_area} to {new_logical_area}"
            )

            # This represents a logical area change - must update EGI structure
            updated_layout = current_layout.copy()
            updated_layout[element_id] = SpatialElement(
                id=element_id,
                type=current_element.type,
                bounds=SpatialBounds(
                    x, y, current_element.bounds.width, current_element.bounds.height
                ),
                logical_area=new_logical_area,
            )

            # Signal that EGI regeneration is required
            self._signal_egi_update_required(
                element_id, old_logical_area, new_logical_area
            )

            return updated_layout
        else:
            # Same logical area - just update position without logical change
            updated_layout = current_layout.copy()
            updated_layout[element_id] = SpatialElement(
                id=element_id,
                type=current_element.type,
                bounds=SpatialBounds(
                    x, y, current_element.bounds.width, current_element.bounds.height
                ),
                logical_area=current_element.logical_area,
            )
            return updated_layout

    def _signal_egi_update_required(
        self, element_id: str, old_area: str, new_area: str
    ):
        """Signal that EGI structure needs updating due to area transition."""
        print(f"EGI UPDATE REQUIRED: {element_id} moved from {old_area} to {new_area}")
        # This would trigger EGI regeneration in the coordinator

    def validate_spatial_logical_consistency(
        self, layout: Dict[str, SpatialElement]
    ) -> bool:
        """Validate that spatial layout maintains logical consistency."""
        for element in layout.values():
            # Check that element is positioned within its assigned logical area
            region = self.region_manager.get_region_for_logical_area(
                element.logical_area
            )
            if not region:
                print(
                    f"CONSISTENCY ERROR: No region for logical area {element.logical_area}"
                )
                return False

            if not region.contains_point(element.bounds.x, element.bounds.y):
                print(
                    f"CONSISTENCY ERROR: Element {element.id} outside its logical area {element.logical_area}"
                )
                return False

        return True

    def get_conjunctive_groups(
        self, layout: Dict[str, SpatialElement]
    ) -> Dict[str, List[str]]:
        """Get elements that form conjunctions by being in the same logical area."""
        groups = {}
        for element in layout.values():
            area = element.logical_area
            if area not in groups:
                groups[area] = []
            groups[area].append(element.id)
        return groups


def create_spatial_alignment_engine(egi) -> SpatialAlignmentEngine:
    """Factory for the minimal alignment engine used by tests."""
    return SpatialAlignmentEngine(egi)


__all__.extend(["SpatialAlignmentEngine", "create_spatial_alignment_engine"])
