#!/usr/bin/env python3
"""
Cut-Area Correspondence System: Fundamental Logic ↔ Spatial Mapping

This module implements the core correspondence between logical negation (cuts)
and spatial areas on the canvas. It establishes the foundational mapping that
ensures every logical negation corresponds exactly to a spatial cut, and every
spatial area corresponds to a logical assertion space.

Key Principles:
1. Logical Negation ↔ Spatial Cut: Bijective mapping
2. Area Containment: EGI area mapping ↔ spatial containment
3. Canvas Totality: Complete EGI ↔ total canvas area
4. Arbitrary Nesting: Support unlimited cut nesting levels
5. Sibling Management: Handle multiple cuts at same nesting level
"""

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from egi_core_dau import Cut, RelationalGraphWithCuts


@dataclass
class SpatialBounds:
    """Spatial bounding rectangle for cuts and areas."""

    x: float
    y: float
    width: float
    height: float

    def contains_point(self, px: float, py: float) -> bool:
        """Check if point is within bounds."""
        return (
            self.x <= px <= self.x + self.width and self.y <= py <= self.y + self.height
        )

    def contains_bounds(self, other: "SpatialBounds") -> bool:
        """Check if other bounds are fully contained."""
        return self.contains_point(other.x, other.y) and self.contains_point(
            other.x + other.width, other.y + other.height
        )

    def center(self) -> Tuple[float, float]:
        """Get center point."""
        return (self.x + self.width / 2, self.y + self.height / 2)

    def area(self) -> float:
        """Calculate area."""
        return self.width * self.height

    def overlaps(self, other: "SpatialBounds") -> bool:
        """Check if bounds overlap with another bounds."""
        return not (
            self.x + self.width <= other.x
            or other.x + other.width <= self.x
            or self.y + self.height <= other.y
            or other.y + other.height <= self.y
        )


@dataclass
class CutArea:
    """Represents a spatial area corresponding to a logical cut."""

    cut_id: str
    logical_parent: str  # "sheet" or parent cut ID
    spatial_bounds: SpatialBounds
    nesting_depth: int
    children: List[str] = field(default_factory=list)


@dataclass
class CanvasArea:
    """Represents the total canvas area (sheet of assertion)."""

    bounds: SpatialBounds
    cuts: List[CutArea] = field(default_factory=list)


class CutAreaCorrespondence:
    """
    Core correspondence engine between EGI logical structure and spatial cuts.

    This class maintains the fundamental mapping:
    - EGI cuts ↔ spatial cut rectangles
    - EGI area mapping ↔ spatial containment
    - EGI sheet ↔ total canvas area
    """

    def __init__(self, canvas_bounds: SpatialBounds):
        """Initialize with canvas dimensions."""
        self.canvas = CanvasArea(canvas_bounds)
        self.cut_areas: Dict[str, CutArea] = {}
        self.area_hierarchy: Dict[str, List[str]] = {}

    def build_correspondence(self, egi: RelationalGraphWithCuts) -> None:
        """Build complete correspondence between EGI and spatial layout."""
        # Clear previous state
        self.cut_areas.clear()
        self.area_hierarchy.clear()
        self.canvas.cuts.clear()

        # Build logical area hierarchy from EGI
        self._build_area_hierarchy(egi)

        # Calculate spatial bounds for all cuts
        self._layout_cuts(egi)

        # Validate correspondence integrity
        self._validate_correspondence(egi)

    def _build_area_hierarchy(self, egi: RelationalGraphWithCuts) -> None:
        """Build hierarchy of logical areas from EGI area mapping."""
        # Initialize with sheet
        self.area_hierarchy["sheet"] = []

        # Process each area in EGI
        for area_id, contained_cuts in egi.area.items():
            if area_id not in self.area_hierarchy:
                self.area_hierarchy[area_id] = []

            # Add contained cuts as children
            for cut_id in contained_cuts:
                if isinstance(cut_id, str):
                    self.area_hierarchy[area_id].append(cut_id)
                    # Initialize cut as area if not exists
                    if cut_id not in self.area_hierarchy:
                        self.area_hierarchy[cut_id] = []

    def _find_parent_area(self, cut_id: str, egi: RelationalGraphWithCuts) -> str:
        """Find the logical parent area of a cut."""
        for area_id, contained_cuts in egi.area.items():
            if cut_id in contained_cuts:
                return area_id
        return "sheet"  # Default to sheet if not found

    def _layout_cuts(self, egi: RelationalGraphWithCuts) -> None:
        """Layout all cuts spatially based on their logical hierarchy."""
        # Calculate nesting depths
        depths = self._calculate_nesting_depths()

        # Sort cuts by depth (shallowest first)
        cuts_by_depth = sorted(egi.Cut, key=lambda c: depths.get(c.id, 0))

        # Layout cuts level by level
        for cut in cuts_by_depth:
            parent_area = self._find_parent_area(cut.id, egi)
            depth = depths.get(cut.id, 0)

            if parent_area == "sheet":
                # Root level cut - place in canvas
                bounds = self._layout_cut_in_canvas(cut.id, egi)
            else:
                # Nested cut - place in parent cut
                bounds = self._layout_cut_in_parent(cut.id, parent_area, egi)

            cut_area = CutArea(
                cut_id=cut.id,
                logical_parent=parent_area,
                spatial_bounds=bounds,
                nesting_depth=depth,
                children=self.area_hierarchy.get(cut.id, []),
            )

            self.cut_areas[cut.id] = cut_area
            if parent_area == "sheet":
                self.canvas.cuts.append(cut_area)

    def _calculate_nesting_depths(self) -> Dict[str, int]:
        """Calculate nesting depth for each cut."""
        depths = {}

        def calculate_depth(area_id: str, current_depth: int) -> None:
            if area_id != "sheet":
                depths[area_id] = current_depth

            for child_id in self.area_hierarchy.get(area_id, []):
                calculate_depth(child_id, current_depth + 1)

        calculate_depth("sheet", 0)
        return depths

    def _layout_cut_in_canvas(
        self, cut_id: str, egi: RelationalGraphWithCuts
    ) -> SpatialBounds:
        """Layout a root-level cut within the canvas."""
        # Get all root-level cuts (complete set)
        root_cuts = [
            c.id for c in egi.Cut if self._find_parent_area(c.id, egi) == "sheet"
        ]
        root_cuts.sort()  # Ensure consistent ordering

        # Find position of this cut in the complete set
        cut_index = root_cuts.index(cut_id)
        sibling_count = len(root_cuts)

        # Grid layout for all siblings
        cols = math.ceil(math.sqrt(sibling_count))
        rows = math.ceil(sibling_count / cols)

        row = cut_index // cols
        col = cut_index % cols

        # Calculate bounds with proper spacing
        padding = 30
        margin = 40

        available_width = (
            self.canvas.bounds.width - (2 * margin) - (padding * (cols - 1))
        )
        available_height = (
            self.canvas.bounds.height - (2 * margin) - (padding * (rows - 1))
        )

        cut_width = max(50, available_width / cols)
        cut_height = max(50, available_height / rows)

        x = self.canvas.bounds.x + margin + col * (cut_width + padding)
        y = self.canvas.bounds.y + margin + row * (cut_height + padding)

        return SpatialBounds(x, y, cut_width, cut_height)

    def _layout_cut_in_parent(
        self, cut_id: str, parent_id: str, egi: RelationalGraphWithCuts
    ) -> SpatialBounds:
        """Layout a nested cut within its parent cut."""
        parent_cut = self.cut_areas[parent_id]

        # Get all children of parent (complete set)
        children = list(self.area_hierarchy.get(parent_id, []))
        children.sort()  # Ensure consistent ordering

        # Find position of this cut in the complete set
        cut_index = children.index(cut_id)
        sibling_count = len(children)

        # Grid layout within parent bounds
        cols = math.ceil(math.sqrt(sibling_count))
        rows = math.ceil(sibling_count / cols)

        row = cut_index // cols
        col = cut_index % cols

        # Calculate bounds with proper spacing inside parent
        padding = 15
        margin = 25
        parent_bounds = parent_cut.spatial_bounds

        available_width = parent_bounds.width - (2 * margin) - (padding * (cols - 1))
        available_height = parent_bounds.height - (2 * margin) - (padding * (rows - 1))

        cut_width = max(30, available_width / cols)
        cut_height = max(30, available_height / rows)

        x = parent_bounds.x + margin + col * (cut_width + padding)
        y = parent_bounds.y + margin + row * (cut_height + padding)

        return SpatialBounds(x, y, cut_width, cut_height)

    def get_area_for_point(self, x: float, y: float) -> str:
        """Get the logical area ID for a spatial point."""
        # Check if point is outside canvas
        if not self.canvas.bounds.contains_point(x, y):
            raise ValueError(f"Point ({x}, {y}) is outside canvas bounds")

        # Find deepest cut containing the point
        deepest_cut = None
        max_depth = -1

        for cut_area in self.cut_areas.values():
            if cut_area.spatial_bounds.contains_point(x, y):
                if cut_area.nesting_depth > max_depth:
                    max_depth = cut_area.nesting_depth
                    deepest_cut = cut_area

        # Return the area inside the deepest cut, or sheet if no cuts contain point
        return deepest_cut.cut_id if deepest_cut else "sheet"

    def get_correspondence_summary(self) -> Dict[str, Any]:
        """Get summary of the current correspondence state."""
        return {
            "canvas_bounds": {
                "x": self.canvas.bounds.x,
                "y": self.canvas.bounds.y,
                "width": self.canvas.bounds.width,
                "height": self.canvas.bounds.height,
            },
            "total_cuts": len(self.cut_areas),
            "root_cuts": len(
                [c for c in self.cut_areas.values() if c.logical_parent == "sheet"]
            ),
            "max_nesting_depth": max(
                [c.nesting_depth for c in self.cut_areas.values()], default=0
            ),
            "area_hierarchy": dict(self.area_hierarchy),
            "cut_bounds": {
                cut_id: {
                    "x": cut_area.spatial_bounds.x,
                    "y": cut_area.spatial_bounds.y,
                    "width": cut_area.spatial_bounds.width,
                    "height": cut_area.spatial_bounds.height,
                    "parent": cut_area.logical_parent,
                    "depth": cut_area.nesting_depth,
                }
                for cut_id, cut_area in self.cut_areas.items()
            },
        }

    def _validate_correspondence(self, egi: RelationalGraphWithCuts) -> None:
        """Validate the integrity of the EGI-spatial correspondence."""
        # 1. Every EGI cut has a spatial area
        for cut in egi.Cut:
            if cut.id not in self.cut_areas:
                raise ValueError(f"Cut {cut.id} missing spatial area")

        # 2. Every spatial area has an EGI cut
        egi_cut_ids = {cut.id for cut in egi.Cut}
        for cut_id in self.cut_areas:
            if cut_id not in egi_cut_ids:
                raise ValueError(f"Spatial area {cut_id} missing EGI cut")

        # 3. Logical parent-child relationships match spatial containment
        for cut_id, cut_area in self.cut_areas.items():
            logical_parent = self._find_parent_area(cut_id, egi)
            if cut_area.logical_parent != logical_parent:
                raise ValueError(f"Cut {cut_id} containment mismatch")

        # 4. No spatial overlaps between sibling cuts
        self._validate_no_sibling_overlaps()

        # 5. All cuts contained within their parents
        self._validate_spatial_containment()

    def _validate_no_sibling_overlaps(self) -> None:
        """Validate that sibling cuts don't overlap spatially."""
        for parent_id, children in self.area_hierarchy.items():
            if len(children) <= 1:
                continue

            for i, child1_id in enumerate(children):
                for child2_id in children[i + 1 :]:
                    if child1_id in self.cut_areas and child2_id in self.cut_areas:
                        bounds1 = self.cut_areas[child1_id].spatial_bounds
                        bounds2 = self.cut_areas[child2_id].spatial_bounds
                        if bounds1.overlaps(bounds2):
                            raise ValueError(
                                f"Sibling cuts {child1_id} and {child2_id} overlap"
                            )

    def _validate_spatial_containment(self) -> None:
        """Validate that all cuts are spatially contained within their parents."""
        for cut_id, cut_area in self.cut_areas.items():
            if cut_area.logical_parent == "sheet":
                # Root cuts must be contained within canvas
                if not self.canvas.bounds.contains_bounds(cut_area.spatial_bounds):
                    raise ValueError(f"Root cut {cut_id} not contained in canvas")
            else:
                # Nested cuts must be contained within parent
                parent_cut = self.cut_areas[cut_area.logical_parent]
                if not parent_cut.spatial_bounds.contains_bounds(
                    cut_area.spatial_bounds
                ):
                    raise ValueError(
                        f"Cut {cut_id} not contained in parent {cut_area.logical_parent}"
                    )
