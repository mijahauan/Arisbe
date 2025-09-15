"""
Hierarchical View System with Collapsible Contexts

This system enables multi-scale visualization of EGI graphs by:
1. Collapsing large graph segments into single visual contexts
2. Supporting depth-limited views with level-of-detail rendering
3. Using R-tree spatial indexing for efficient hierarchical queries
4. Enabling seamless navigation between abstraction levels

Key insight: "Whole worlds of graphs might lie in a single collapsed context"
"""

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

# Import our existing EGI and spatial types
from egi_core_dau import Cut, RelationalGraphWithCuts


class ViewLevel(Enum):
    """Defines the level of detail for viewing contexts."""

    COLLAPSED = "collapsed"  # Show only as single box with summary
    SUMMARY = "summary"  # Show immediate children only
    DETAILED = "detailed"  # Show full internal structure
    EXPANDED = "expanded"  # Show all nested levels


@dataclass
class SpatialBounds:
    """Spatial bounding rectangle."""

    x: float
    y: float
    width: float
    height: float

    def contains_point(self, px: float, py: float) -> bool:
        return (
            self.x <= px <= self.x + self.width and self.y <= py <= self.y + self.height
        )

    def intersects(self, other: "SpatialBounds") -> bool:
        return not (
            self.x + self.width < other.x
            or other.x + other.width < self.x
            or self.y + self.height < other.y
            or other.y + other.height < self.y
        )

    def area(self) -> float:
        return self.width * self.height


@dataclass
class ContextSummary:
    """Summary information for collapsed contexts."""

    cut_count: int
    max_nesting_depth: int
    predicate_count: int
    vertex_count: int
    complexity_score: float

    def get_display_text(self) -> str:
        return f"Context: {self.cut_count} cuts, depth {self.max_nesting_depth}"


class ViewContext:
    """Represents a collapsible context in the hierarchical view."""

    def __init__(self, context_id: str, parent_id: Optional[str] = None):
        self.context_id = context_id
        self.parent_id = parent_id
        self.view_level = ViewLevel.SUMMARY
        self.spatial_bounds: Optional[SpatialBounds] = None
        self.children: List[str] = []
        self.contained_cuts: Set[str] = set()
        self.summary: Optional[ContextSummary] = None
        self.is_visible = True
        self.zoom_threshold = 1.0  # Minimum zoom level to show details

    def should_show_details(self, current_zoom: float) -> bool:
        """Determine if context should show internal details at current zoom."""
        return current_zoom >= self.zoom_threshold and self.view_level in [
            ViewLevel.DETAILED,
            ViewLevel.EXPANDED,
        ]

    def calculate_complexity(self, egi: RelationalGraphWithCuts) -> float:
        """Calculate complexity score for level-of-detail decisions."""
        cut_count = len(self.contained_cuts)
        max_depth = self._calculate_max_depth(egi)

        # Complexity increases with cuts and nesting depth
        return cut_count * (1 + max_depth * 0.5)

    def _calculate_max_depth(self, egi: RelationalGraphWithCuts) -> int:
        """Calculate maximum nesting depth within this context."""
        max_depth = 0
        for cut_id in self.contained_cuts:
            depth = self._get_cut_depth(cut_id, egi)
            max_depth = max(max_depth, depth)
        return max_depth

    def _get_cut_depth(self, cut_id: str, egi: RelationalGraphWithCuts) -> int:
        """Get nesting depth of a specific cut."""
        depth = 0
        current_area = self._find_parent_area(cut_id, egi)

        while current_area != "sheet":
            depth += 1
            current_area = self._find_parent_area(current_area, egi)
            if depth > 100:  # Prevent infinite loops
                break

        return depth

    def _find_parent_area(self, cut_id: str, egi: RelationalGraphWithCuts) -> str:
        """Find parent area of a cut."""
        for area_id, contained_cuts in egi.area.items():
            if cut_id in contained_cuts:
                return area_id
        return "sheet"


class RTreeNode:
    """R-tree node for spatial indexing of hierarchical contexts."""

    def __init__(self, is_leaf: bool = True):
        self.is_leaf = is_leaf
        self.bounds: Optional[SpatialBounds] = None
        self.children: List["RTreeNode"] = []
        self.contexts: List[str] = []  # Context IDs for leaf nodes
        self.max_children = 4  # R-tree branching factor

    def insert_context(
        self,
        context_id: str,
        bounds: SpatialBounds,
        view_system: "HierarchicalViewSystem",
    ) -> None:
        """Insert a context into the R-tree."""
        if self.is_leaf:
            self.contexts.append(context_id)
            self._update_bounds(bounds)

            # Split if too many contexts
            if len(self.contexts) > self.max_children:
                self._split_leaf(view_system)
        else:
            # Find best child to insert into
            best_child = self._choose_subtree(bounds)
            best_child.insert_context(context_id, bounds, view_system)
            self._update_bounds(bounds)

    def query_region(self, query_bounds: SpatialBounds) -> List[str]:
        """Query contexts that intersect with the given region."""
        results = []

        if not self.bounds or not self.bounds.intersects(query_bounds):
            return results

        if self.is_leaf:
            return self.contexts.copy()
        else:
            for child in self.children:
                results.extend(child.query_region(query_bounds))

        return results

    def _update_bounds(self, new_bounds: SpatialBounds) -> None:
        """Update node bounds to include new bounds."""
        if self.bounds is None:
            self.bounds = SpatialBounds(
                new_bounds.x, new_bounds.y, new_bounds.width, new_bounds.height
            )
        else:
            min_x = min(self.bounds.x, new_bounds.x)
            min_y = min(self.bounds.y, new_bounds.y)
            max_x = max(
                self.bounds.x + self.bounds.width, new_bounds.x + new_bounds.width
            )
            max_y = max(
                self.bounds.y + self.bounds.height, new_bounds.y + new_bounds.height
            )

            self.bounds = SpatialBounds(min_x, min_y, max_x - min_x, max_y - min_y)

    def _choose_subtree(self, bounds: SpatialBounds) -> "RTreeNode":
        """Choose the best subtree for insertion."""
        best_child = None
        min_enlargement = float("inf")

        for child in self.children:
            if child.bounds:
                enlargement = self._calculate_enlargement(child.bounds, bounds)
                if enlargement < min_enlargement:
                    min_enlargement = enlargement
                    best_child = child

        return best_child or self.children[0]

    def _calculate_enlargement(
        self, current: SpatialBounds, new: SpatialBounds
    ) -> float:
        """Calculate area enlargement needed to include new bounds."""
        combined_bounds = SpatialBounds(
            min(current.x, new.x),
            min(current.y, new.y),
            max(current.x + current.width, new.x + new.width) - min(current.x, new.x),
            max(current.y + current.height, new.y + new.height) - min(current.y, new.y),
        )
        return combined_bounds.area() - current.area()

    def _split_leaf(self, view_system: "HierarchicalViewSystem") -> None:
        """Split a leaf node when it becomes too full."""
        # Simple split: divide contexts spatially
        # In production, use more sophisticated R-tree splitting algorithms
        mid_point = len(self.contexts) // 2

        new_node = RTreeNode(is_leaf=True)
        new_node.contexts = self.contexts[mid_point:]
        self.contexts = self.contexts[:mid_point]

        # Recalculate bounds for both nodes
        self._recalculate_bounds(view_system)
        new_node._recalculate_bounds(view_system)

    def _recalculate_bounds(self, view_system: "HierarchicalViewSystem") -> None:
        """Recalculate bounds based on contained contexts."""
        if not self.contexts:
            self.bounds = None
            return

        first_context = view_system.contexts[self.contexts[0]]
        if first_context.spatial_bounds:
            self.bounds = SpatialBounds(
                first_context.spatial_bounds.x,
                first_context.spatial_bounds.y,
                first_context.spatial_bounds.width,
                first_context.spatial_bounds.height,
            )

            for context_id in self.contexts[1:]:
                context = view_system.contexts[context_id]
                if context.spatial_bounds:
                    self._update_bounds(context.spatial_bounds)


class HierarchicalViewSystem:
    """
    Manages hierarchical views with collapsible contexts and R-tree spatial indexing.

    This system enables scalable visualization by:
    1. Organizing EGI elements into hierarchical contexts
    2. Supporting multiple levels of detail (collapsed, summary, detailed, expanded)
    3. Using R-tree for efficient spatial queries
    4. Enabling context collapse/expansion based on zoom and complexity
    """

    def __init__(self, viewport_bounds: SpatialBounds):
        self.viewport_bounds = viewport_bounds
        self.contexts: Dict[str, ViewContext] = {}
        self.context_hierarchy: Dict[str, List[str]] = {}
        self.spatial_index = RTreeNode(is_leaf=True)
        self.current_zoom = 1.0
        self.max_visible_contexts = 100  # Performance limit
        self.egi: Optional[RelationalGraphWithCuts] = None  # Store EGI reference

    def build_hierarchical_view(
        self, egi: RelationalGraphWithCuts, max_depth: int = 3
    ) -> None:
        """Build hierarchical view system from EGI structure."""
        # Store EGI reference for later use
        self.egi = egi

        # Clear previous state
        self.contexts.clear()
        self.context_hierarchy.clear()
        self.spatial_index = RTreeNode(is_leaf=True)

        # Create root context for sheet
        root_context = ViewContext("sheet_context", None)
        self.contexts["sheet_context"] = root_context

        # Build context hierarchy based on EGI structure and complexity
        self._build_context_hierarchy(egi, max_depth)

        # Calculate spatial layout for all contexts
        self._layout_contexts(egi)

        # Build spatial index
        self._build_spatial_index()

        # Set initial view levels based on complexity
        self._optimize_view_levels()

    def get_visible_contexts(
        self, query_bounds: Optional[SpatialBounds] = None
    ) -> List[ViewContext]:
        """Get contexts visible in the current viewport."""
        if query_bounds is None:
            query_bounds = self.viewport_bounds

        # Query R-tree for potentially visible contexts
        context_ids = self.spatial_index.query_region(query_bounds)

        visible_contexts = []
        for context_id in context_ids:
            context = self.contexts.get(context_id)
            if context and context.is_visible:
                # Check if context should be shown at current zoom
                if context.should_show_details(self.current_zoom):
                    visible_contexts.append(context)

        # Limit number of visible contexts for performance
        if len(visible_contexts) > self.max_visible_contexts and self.egi:
            # Sort by importance (complexity, size, etc.)
            visible_contexts.sort(
                key=lambda c: c.calculate_complexity(self.egi), reverse=True
            )
            visible_contexts = visible_contexts[: self.max_visible_contexts]

        return visible_contexts

    def collapse_context(self, context_id: str) -> None:
        """Collapse a context to summary view."""
        if context_id in self.contexts:
            context = self.contexts[context_id]
            context.view_level = ViewLevel.COLLAPSED

            # Hide child contexts
            for child_id in context.children:
                if child_id in self.contexts:
                    self.contexts[child_id].is_visible = False

    def expand_context(self, context_id: str) -> None:
        """Expand a context to show internal structure."""
        if context_id in self.contexts:
            context = self.contexts[context_id]
            context.view_level = ViewLevel.DETAILED

            # Show immediate child contexts
            for child_id in context.children:
                if child_id in self.contexts:
                    self.contexts[child_id].is_visible = True

    def set_zoom_level(self, zoom: float) -> None:
        """Update zoom level and adjust context visibility."""
        self.current_zoom = zoom

        # Automatically adjust context detail levels based on zoom
        if self.egi:
            for context in self.contexts.values():
                if zoom < 0.5:
                    # Very zoomed out - show only major contexts
                    if context.calculate_complexity(self.egi) < 10:
                        context.view_level = ViewLevel.COLLAPSED
                elif zoom < 1.0:
                    # Medium zoom - show summaries
                    context.view_level = ViewLevel.SUMMARY
                else:
                    # Zoomed in - show details
                    context.view_level = ViewLevel.DETAILED

    def _build_context_hierarchy(
        self, egi: RelationalGraphWithCuts, max_depth: int
    ) -> None:
        """Build hierarchy of contexts based on EGI structure and complexity."""
        # Start with root areas
        root_cuts = [
            c.id for c in egi.Cut if self._find_parent_area(c.id, egi) == "sheet"
        ]

        # Group cuts into contexts based on complexity and spatial proximity
        context_groups = self._group_cuts_into_contexts(root_cuts, egi, max_depth)

        for i, cut_group in enumerate(context_groups):
            context_id = f"context_{i}"
            context = ViewContext(context_id, "sheet_context")
            context.contained_cuts = set(cut_group)

            # Calculate summary information
            context.summary = self._calculate_context_summary(cut_group, egi)

            self.contexts[context_id] = context

            # Build nested contexts recursively
            self._build_nested_contexts(context_id, cut_group, egi, max_depth - 1)

    def _group_cuts_into_contexts(
        self, cuts: List[str], egi: RelationalGraphWithCuts, max_depth: int
    ) -> List[List[str]]:
        """Group cuts into contexts based on complexity and relationships."""
        if not cuts or max_depth <= 0:
            return [cuts] if cuts else []

        # Simple grouping strategy - can be enhanced with clustering algorithms
        max_cuts_per_context = 8
        groups = []

        for i in range(0, len(cuts), max_cuts_per_context):
            group = cuts[i : i + max_cuts_per_context]
            groups.append(group)

        return groups

    def _build_nested_contexts(
        self,
        parent_context_id: str,
        parent_cuts: List[str],
        egi: RelationalGraphWithCuts,
        remaining_depth: int,
    ) -> None:
        """Recursively build nested contexts."""
        if remaining_depth <= 0:
            return

        # Find all cuts nested within parent cuts
        nested_cuts = []
        for parent_cut in parent_cuts:
            children = egi.area.get(parent_cut, [])
            nested_cuts.extend([c for c in children if isinstance(c, str)])

        if nested_cuts:
            # Group nested cuts into sub-contexts
            nested_groups = self._group_cuts_into_contexts(
                nested_cuts, egi, remaining_depth
            )

            for i, nested_group in enumerate(nested_groups):
                nested_context_id = f"{parent_context_id}_nested_{i}"
                nested_context = ViewContext(nested_context_id, parent_context_id)
                nested_context.contained_cuts = set(nested_group)
                nested_context.summary = self._calculate_context_summary(
                    nested_group, egi
                )

                self.contexts[nested_context_id] = nested_context

                # Add to parent's children
                if parent_context_id not in self.context_hierarchy:
                    self.context_hierarchy[parent_context_id] = []
                self.context_hierarchy[parent_context_id].append(nested_context_id)

                # Continue recursion
                self._build_nested_contexts(
                    nested_context_id, nested_group, egi, remaining_depth - 1
                )

    def _calculate_context_summary(
        self, cuts: List[str], egi: RelationalGraphWithCuts
    ) -> ContextSummary:
        """Calculate summary information for a context."""
        cut_count = len(cuts)
        max_depth = 0

        # Calculate maximum nesting depth
        for cut_id in cuts:
            depth = self._calculate_cut_depth(cut_id, egi)
            max_depth = max(max_depth, depth)

        # Count predicates and vertices (placeholder - would need actual EGI predicate/vertex data)
        predicate_count = 0  # TODO: Count predicates in context
        vertex_count = 0  # TODO: Count vertices in context

        # Calculate complexity score
        complexity_score = cut_count * (1 + max_depth * 0.5)

        return ContextSummary(
            cut_count, max_depth, predicate_count, vertex_count, complexity_score
        )

    def _calculate_cut_depth(self, cut_id: str, egi: RelationalGraphWithCuts) -> int:
        """Calculate nesting depth of a cut."""
        depth = 0
        current_area = self._find_parent_area(cut_id, egi)

        while current_area != "sheet":
            depth += 1
            current_area = self._find_parent_area(current_area, egi)
            if depth > 100:  # Prevent infinite loops
                break

        return depth

    def _find_parent_area(self, cut_id: str, egi: RelationalGraphWithCuts) -> str:
        """Find parent area of a cut."""
        for area_id, contained_cuts in egi.area.items():
            if cut_id in contained_cuts:
                return area_id
        return "sheet"

    def _layout_contexts(self, egi: RelationalGraphWithCuts) -> None:
        """Calculate spatial layout for all contexts."""
        # Layout root contexts first
        root_contexts = [
            c for c in self.contexts.values() if c.parent_id == "sheet_context"
        ]
        self._layout_sibling_contexts(root_contexts, self.viewport_bounds)

        # Layout nested contexts recursively
        for context in root_contexts:
            self._layout_nested_contexts(context.context_id, egi)

    def _layout_sibling_contexts(
        self, contexts: List[ViewContext], parent_bounds: SpatialBounds
    ) -> None:
        """Layout sibling contexts within parent bounds."""
        if not contexts:
            return

        # Grid layout for siblings
        cols = math.ceil(math.sqrt(len(contexts)))
        rows = math.ceil(len(contexts) / cols)

        padding = 20
        margin = 30

        available_width = parent_bounds.width - (2 * margin) - (padding * (cols - 1))
        available_height = parent_bounds.height - (2 * margin) - (padding * (rows - 1))

        context_width = max(100, available_width / cols)
        context_height = max(80, available_height / rows)

        for i, context in enumerate(contexts):
            row = i // cols
            col = i % cols

            x = parent_bounds.x + margin + col * (context_width + padding)
            y = parent_bounds.y + margin + row * (context_height + padding)

            context.spatial_bounds = SpatialBounds(x, y, context_width, context_height)

    def _layout_nested_contexts(
        self, parent_context_id: str, egi: RelationalGraphWithCuts
    ) -> None:
        """Layout nested contexts within their parent."""
        child_context_ids = self.context_hierarchy.get(parent_context_id, [])
        if not child_context_ids:
            return

        parent_context = self.contexts[parent_context_id]
        if not parent_context.spatial_bounds:
            return

        child_contexts = [self.contexts[cid] for cid in child_context_ids]
        self._layout_sibling_contexts(child_contexts, parent_context.spatial_bounds)

        # Recursively layout deeper levels
        for child_id in child_context_ids:
            self._layout_nested_contexts(child_id, egi)

    def _build_spatial_index(self) -> None:
        """Build R-tree spatial index for efficient queries."""
        self.spatial_index = RTreeNode(is_leaf=True)

        for context_id, context in self.contexts.items():
            if context.spatial_bounds:
                self.spatial_index.insert_context(
                    context_id, context.spatial_bounds, self
                )

    def _optimize_view_levels(self) -> None:
        """Set optimal view levels based on context complexity and zoom."""
        for context in self.contexts.values():
            if context.summary:
                complexity = context.summary.complexity_score

                # Set view level based on complexity
                if complexity > 50:
                    context.view_level = ViewLevel.COLLAPSED
                elif complexity > 20:
                    context.view_level = ViewLevel.SUMMARY
                else:
                    context.view_level = ViewLevel.DETAILED

                # Set zoom threshold
                context.zoom_threshold = max(0.1, 1.0 / math.sqrt(complexity))


# Usage example and performance characteristics
"""
Performance Analysis for Hierarchical View System with R-tree:

1. **Context Creation**: O(n log k) where n = total cuts, k = contexts per level
   - Groups cuts into hierarchical contexts
   - Each cut processed once per hierarchy level

2. **Spatial Indexing (R-tree)**: O(n log n) build, O(log n) query
   - R-tree provides logarithmic spatial queries
   - Efficient for hierarchical bounding box queries
   - Ideal for level-of-detail rendering

3. **View Rendering**: O(v log n) where v = visible contexts
   - Only processes visible contexts at current zoom/detail level
   - R-tree enables efficient viewport culling
   - Performance independent of total graph size

4. **Context Collapse/Expand**: O(1) for individual operations
   - Simply changes view level flags
   - No spatial recalculation needed
   - Batch operations: O(k) for k contexts

5. **Zoom Level Changes**: O(v) where v = visible contexts
   - Updates detail levels for visible contexts only
   - R-tree enables efficient visibility queries

Key Advantages of R-tree for this system:
- Hierarchical bounding boxes match context hierarchy naturally
- Efficient range queries for viewport culling
- Supports dynamic insertion/deletion of contexts
- Scales logarithmically with context count
- Enables smooth level-of-detail transitions

This approach can handle arbitrarily large EGI graphs by:
1. Collapsing complex regions into single visual contexts
2. Using R-tree for efficient spatial queries
3. Rendering only visible contexts at appropriate detail levels
4. Supporting seamless navigation between abstraction levels
"""
