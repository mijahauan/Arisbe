"""
R-tree based cut tracking system for EGI spatial mapping.

This module provides spatial indexing for tracking cuts on an unbounded canvas
representing the sheet of assertion. Each cut is tracked with spatial bounds,
parent area, and nesting level.
"""

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


class CutPlacementType(Enum):
    """Types of cut placement operations."""

    BESIDE = "beside"  # Siblings in the same area
    NESTED = "nested"  # Inside an existing cut
    ENCLOSING = "enclosing"  # Enclosing existing cuts


@dataclass
class SpatialBounds:
    """Represents spatial bounds of a rectangular area."""

    x: float
    y: float
    width: float
    height: float

    @property
    def left(self) -> float:
        return self.x

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def top(self) -> float:
        return self.y

    @property
    def bottom(self) -> float:
        return self.y + self.height

    @property
    def center_x(self) -> float:
        return self.x + self.width / 2

    @property
    def center_y(self) -> float:
        return self.y + self.height / 2

    def contains_point(self, x: float, y: float) -> bool:
        """Check if point is inside bounds."""
        return self.left <= x <= self.right and self.top <= y <= self.bottom

    def intersects(self, other: "SpatialBounds") -> bool:
        """Check if this bounds intersects with another."""
        return not (
            self.right < other.left
            or self.left > other.right
            or self.bottom < other.top
            or self.top > other.bottom
        )

    def contains_bounds(self, other: "SpatialBounds") -> bool:
        """Check if this bounds completely contains another."""
        return (
            self.left <= other.left
            and self.right >= other.right
            and self.top <= other.top
            and self.bottom >= other.bottom
        )


@dataclass
class CutSpatialInfo:
    """Information about a cut in the spatial index."""

    cut_id: str
    bounds: SpatialBounds
    parent_area: Optional[str]  # None for root-level cuts
    nesting_level: int

    def __hash__(self):
        return hash(self.cut_id)


class RTreeNode:
    """Node in the R-tree spatial index."""

    def __init__(self, is_leaf: bool = True, max_entries: int = 4):
        self.is_leaf = is_leaf
        self.max_entries = max_entries
        self.entries: List[Any] = (
            []
        )  # CutSpatialInfo for leaves, RTreeNode for internal
        self.bounds: Optional[SpatialBounds] = None

    def add_entry(self, entry: Any):
        """Add an entry to this node."""
        self.entries.append(entry)
        self._update_bounds()

    def remove_entry(self, entry: Any):
        """Remove an entry from this node."""
        if entry in self.entries:
            self.entries.remove(entry)
            self._update_bounds()

    def _update_bounds(self):
        """Update the bounding box to encompass all entries."""
        if not self.entries:
            self.bounds = None
            return

        if self.is_leaf:
            # Entries are CutSpatialInfo objects
            min_x = min(cut.bounds.left for cut in self.entries)
            max_x = max(cut.bounds.right for cut in self.entries)
            min_y = min(cut.bounds.top for cut in self.entries)
            max_y = max(cut.bounds.bottom for cut in self.entries)
        else:
            # Entries are child nodes
            min_x = min(node.bounds.left for node in self.entries if node.bounds)
            max_x = max(node.bounds.right for node in self.entries if node.bounds)
            min_y = min(node.bounds.top for node in self.entries if node.bounds)
            max_y = max(node.bounds.bottom for node in self.entries if node.bounds)

        self.bounds = SpatialBounds(
            x=min_x, y=min_y, width=max_x - min_x, height=max_y - min_y
        )

    def is_full(self) -> bool:
        """Check if node has reached maximum capacity."""
        return len(self.entries) >= self.max_entries

    def search(self, query_bounds: SpatialBounds) -> List[CutSpatialInfo]:
        """Search for cuts that intersect with query bounds."""
        results = []

        if not self.bounds or not self.bounds.intersects(query_bounds):
            return results

        if self.is_leaf:
            for cut in self.entries:
                if cut.bounds.intersects(query_bounds):
                    results.append(cut)
        else:
            for child in self.entries:
                results.extend(child.search(query_bounds))

        return results


class RTreeCutTracker:
    """R-tree based spatial index for tracking cuts."""

    def __init__(self, canvas_width: float = 10000, canvas_height: float = 10000):
        self.canvas_bounds = SpatialBounds(0, 0, canvas_width, canvas_height)
        self.root = RTreeNode(is_leaf=True)
        self.cuts: Dict[str, CutSpatialInfo] = {}
        self.min_spacing = 10.0  # Minimum spacing between cuts

    def add_cut(
        self,
        cut_id: str,
        bounds: SpatialBounds,
        parent_area: Optional[str] = None,
        placement_type: CutPlacementType = CutPlacementType.BESIDE,
    ) -> bool:
        """Add a cut to the spatial index."""

        # Validate placement
        if not self._validate_placement(bounds, parent_area, placement_type):
            return False

        # Determine nesting level
        nesting_level = 0
        if parent_area:
            parent_cut = self.cuts.get(parent_area)
            if parent_cut:
                nesting_level = parent_cut.nesting_level + 1

        cut_info = CutSpatialInfo(cut_id, bounds, parent_area, nesting_level)
        self.cuts[cut_id] = cut_info

        # Insert into R-tree
        self._insert(cut_info)

        return True

    def remove_cut(self, cut_id: str) -> bool:
        """Remove a cut from the spatial index."""
        if cut_id not in self.cuts:
            return False

        cut_info = self.cuts[cut_id]
        del self.cuts[cut_id]

        # Remove from R-tree
        self._remove(cut_info)

        return True

    def move_cut(self, cut_id: str, new_bounds: SpatialBounds) -> bool:
        """Move a cut to new spatial bounds."""
        if cut_id not in self.cuts:
            return False

        cut_info = self.cuts[cut_id]
        old_bounds = cut_info.bounds

        # Temporarily update bounds for validation
        cut_info.bounds = new_bounds

        # Validate new position
        if not self._validate_placement(
            new_bounds, cut_info.parent_area, CutPlacementType.BESIDE
        ):
            # Restore old bounds if validation fails
            cut_info.bounds = old_bounds
            return False

        # Update R-tree
        self._remove(cut_info)
        self._insert(cut_info)

        return True

    def get_cuts_in_area(self, area_id: Optional[str]) -> List[CutSpatialInfo]:
        """Get all cuts directly contained in an area."""
        return [cut for cut in self.cuts.values() if cut.parent_area == area_id]

    def get_nested_cuts(self, area_id: Optional[str]) -> List[CutSpatialInfo]:
        """Get all cuts nested within an area (recursively)."""
        result = []
        direct_cuts = self.get_cuts_in_area(area_id)

        for cut in direct_cuts:
            result.append(cut)
            result.extend(self.get_nested_cuts(cut.cut_id))

        return result

    def get_spatial_extent(self, area_id: Optional[str]) -> Optional[SpatialBounds]:
        """Get the spatial extent of all cuts in an area."""
        cuts = self.get_nested_cuts(area_id)

        if not cuts:
            return None

        min_x = min(cut.bounds.left for cut in cuts)
        max_x = max(cut.bounds.right for cut in cuts)
        min_y = min(cut.bounds.top for cut in cuts)
        max_y = max(cut.bounds.bottom for cut in cuts)

        return SpatialBounds(min_x, min_y, max_x - min_x, max_y - min_y)

    def query_region(self, bounds: SpatialBounds) -> List[CutSpatialInfo]:
        """Query cuts that intersect with the given spatial region."""
        return self.root.search(bounds)

    def _validate_placement(
        self,
        bounds: SpatialBounds,
        parent_area: Optional[str],
        placement_type: CutPlacementType,
    ) -> bool:
        """Validate that cut placement follows spatial constraints."""

        # Check canvas bounds
        if not self.canvas_bounds.contains_bounds(bounds):
            return False

        # Check for overlaps with existing cuts
        overlapping = self.query_region(bounds)
        for cut in overlapping:
            if self._cuts_overlap_with_spacing(bounds, cut.bounds):
                return False

        # Validate parent containment
        if parent_area and parent_area in self.cuts:
            parent_cut = self.cuts[parent_area]
            if not parent_cut.bounds.contains_bounds(bounds):
                return False

        return True

    def _cuts_overlap_with_spacing(
        self, bounds1: SpatialBounds, bounds2: SpatialBounds
    ) -> bool:
        """Check if two cuts overlap considering minimum spacing."""
        expanded1 = SpatialBounds(
            bounds1.x - self.min_spacing,
            bounds1.y - self.min_spacing,
            bounds1.width + 2 * self.min_spacing,
            bounds1.height + 2 * self.min_spacing,
        )
        return expanded1.intersects(bounds2)

    def _insert(self, cut_info: CutSpatialInfo):
        """Insert cut into R-tree."""
        if self.root.is_leaf:
            self.root.add_entry(cut_info)
            if self.root.is_full():
                self._split_root()
        else:
            self._insert_recursive(self.root, cut_info)

    def _insert_recursive(self, node: RTreeNode, cut_info: CutSpatialInfo):
        """Recursively insert cut into R-tree."""
        if node.is_leaf:
            node.add_entry(cut_info)
            if node.is_full():
                self._split_node(node)
        else:
            # Find best child to insert into
            best_child = self._choose_subtree(node, cut_info)
            self._insert_recursive(best_child, cut_info)

    def _choose_subtree(self, node: RTreeNode, cut_info: CutSpatialInfo) -> RTreeNode:
        """Choose the best subtree for insertion."""
        best_child = None
        min_enlargement = float("inf")

        for child in node.entries:
            if child.bounds:
                enlargement = self._calculate_enlargement(child.bounds, cut_info.bounds)
                if enlargement < min_enlargement:
                    min_enlargement = enlargement
                    best_child = child

        return best_child or node.entries[0]

    def _calculate_enlargement(
        self, existing_bounds: SpatialBounds, new_bounds: SpatialBounds
    ) -> float:
        """Calculate area enlargement needed to include new bounds."""
        min_x = min(existing_bounds.left, new_bounds.left)
        max_x = max(existing_bounds.right, new_bounds.right)
        min_y = min(existing_bounds.top, new_bounds.top)
        max_y = max(existing_bounds.bottom, new_bounds.bottom)

        new_area = (max_x - min_x) * (max_y - min_y)
        old_area = existing_bounds.width * existing_bounds.height

        return new_area - old_area

    def _split_root(self):
        """Split the root node when it becomes full."""
        old_root = self.root
        self.root = RTreeNode(is_leaf=False)

        new_node1, new_node2 = self._split_node_entries(
            old_root.entries, old_root.is_leaf
        )
        self.root.add_entry(new_node1)
        self.root.add_entry(new_node2)

    def _split_node(self, node: RTreeNode):
        """Split a full node into two nodes."""
        new_node1, new_node2 = self._split_node_entries(node.entries, node.is_leaf)

        # Replace current node with first split
        node.entries = new_node1.entries
        node._update_bounds()

        # Add second split to parent (simplified - would need parent tracking)
        return new_node2

    def _split_node_entries(
        self, entries: List[Any], is_leaf: bool
    ) -> Tuple[RTreeNode, RTreeNode]:
        """Split entries into two nodes."""
        # Simple split - take first half and second half
        mid = len(entries) // 2

        node1 = RTreeNode(is_leaf=is_leaf)
        node2 = RTreeNode(is_leaf=is_leaf)

        for entry in entries[:mid]:
            node1.add_entry(entry)
        for entry in entries[mid:]:
            node2.add_entry(entry)

        return node1, node2

    def _remove(self, cut_info: CutSpatialInfo):
        """Remove cut from R-tree."""
        self._remove_recursive(self.root, cut_info)

    def _remove_recursive(self, node: RTreeNode, cut_info: CutSpatialInfo) -> bool:
        """Recursively remove cut from R-tree."""
        if node.is_leaf:
            if cut_info in node.entries:
                node.remove_entry(cut_info)
                return True
        else:
            for child in node.entries[
                :
            ]:  # Copy list to avoid modification during iteration
                if child.bounds and child.bounds.intersects(cut_info.bounds):
                    if self._remove_recursive(child, cut_info):
                        # If child becomes empty, remove it
                        if not child.entries:
                            node.remove_entry(child)
                        return True
        return False

    def get_cut_info(self, cut_id: str) -> Optional[CutSpatialInfo]:
        """Get information about a specific cut."""
        return self.cuts.get(cut_id)

    def get_all_cuts(self) -> List[CutSpatialInfo]:
        """Get all cuts in the tracker."""
        return list(self.cuts.values())

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the spatial index."""
        return {
            "total_cuts": len(self.cuts),
            "max_nesting_level": max(
                (cut.nesting_level for cut in self.cuts.values()), default=0
            ),
            "canvas_bounds": self.canvas_bounds,
            "min_spacing": self.min_spacing,
        }
