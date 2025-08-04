#!/usr/bin/env python3
"""
Content-Driven Layout Engine for Existential Graphs

Implements a professional layout approach:
1. First: Position all contents (predicates, vertices, lines of identity) optimally
2. Then: Size cuts to appropriately contain their contents  
3. Finally: Adjust overall layout to prevent overlaps and ensure clean presentation

This is the correct architectural approach for professional layout systems.
"""

import math
from typing import Dict, Set, List, Tuple, Optional
from dataclasses import dataclass

from egi_core_dau import RelationalGraphWithCuts, ElementID
from layout_engine_clean import SpatialPrimitive, LayoutResult, Bounds, Coordinate


@dataclass
class ContentGroup:
    """A group of content elements that will be contained within a cut."""
    area_id: ElementID
    vertices: List[SpatialPrimitive]
    edges: List[SpatialPrimitive]
    child_cuts: List['ContentGroup']
    
    def get_bounding_box(self) -> Bounds:
        """Calculate the bounding box that contains all content in this group."""
        if not (self.vertices or self.edges or self.child_cuts):
            return (0, 0, 100, 100)  # Default minimum size
        
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        # Include vertices
        for vertex in self.vertices:
            x, y = vertex.position
            min_x, min_y = min(min_x, x), min(min_y, y)
            max_x, max_y = max(max_x, x), max(max_y, y)
        
        # Include edges (predicates)
        for edge in self.edges:
            x, y = edge.position
            # Account for text bounds
            if edge.bounds:
                x1, y1, x2, y2 = edge.bounds
                min_x, min_y = min(min_x, x1), min(min_y, y1)
                max_x, max_y = max(max_x, x2), max(max_y, y2)
            else:
                min_x, min_y = min(min_x, x), min(min_y, y)
                max_x, max_y = max(max_x, x), max(max_y, y)
        
        # Include child cuts
        for child_group in self.child_cuts:
            child_bounds = child_group.get_bounding_box()
            cx1, cy1, cx2, cy2 = child_bounds
            min_x, min_y = min(min_x, cx1), min(min_y, cy1)
            max_x, max_y = max(max_x, cx2), max(max_y, cy2)
        
        return (min_x, min_y, max_x, max_y)


class ContentDrivenLayoutEngine:
    """
    Professional content-driven layout engine.
    
    Key principle: Content determines container size, not the reverse.
    """
    
    def __init__(self, canvas_width: float = 800, canvas_height: float = 600):
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        
        # Layout parameters
        self.margin = 50.0
        self.vertex_radius = 6.0
        self.min_vertex_spacing = 80.0
        self.cut_padding = 50.0  # Padding around cut contents
        self.predicate_spacing = 90.0  # Minimum distance between predicates
        
        # Z-index layers
        self.z_cuts = 0
        self.z_vertices = 1
        self.z_edges = 2
    
    def layout_graph(self, graph: RelationalGraphWithCuts) -> LayoutResult:
        """
        Main entry point: Inside-out hierarchical layout approach.
        
        Process:
        1. Build containment hierarchy from graph structure
        2. Layout from innermost to outermost level
        3. Ensure proper hierarchical containment at each level
        4. Position sheet-level elements outside all cuts
        """
        
        # Store graph reference for exclusive area allocation
        self._current_graph = graph
        
        # Step 1: Build containment hierarchy from graph structure
        hierarchy_levels = self._build_containment_hierarchy_from_graph(graph)
        
        # Step 2: Layout from inside out
        all_primitives = self._layout_inside_out(graph, hierarchy_levels)
        
        # Step 3: Final optimization
        self._optimize_global_layout(all_primitives)
        
        # Build final result
        canvas_bounds = self._calculate_canvas_bounds(all_primitives)
        containment_hierarchy = self._build_containment_hierarchy(graph)
        
        return LayoutResult(
            primitives=all_primitives,
            canvas_bounds=canvas_bounds,
            containment_hierarchy=containment_hierarchy
        )
    
    def _position_vertices_freely(self, graph: RelationalGraphWithCuts) -> Dict[ElementID, SpatialPrimitive]:
        """Position vertices respecting their logical area containment."""
        vertex_primitives = {}
        
        # Group vertices by their logical areas
        vertices_by_area = {}
        for vertex in graph.V:
            area = self._find_vertex_area(vertex.id, graph)
            if area not in vertices_by_area:
                vertices_by_area[area] = []
            vertices_by_area[area].append(vertex)
        
        # Position sheet-level vertices outside cut areas
        sheet_vertices = vertices_by_area.get(graph.sheet, [])
        for i, vertex in enumerate(sheet_vertices):
            # Position sheet vertices in the left margin area, clearly outside cuts
            x = self.margin + 50  # Fixed position in left margin
            y = self.margin + 100 + (i * self.min_vertex_spacing)
            
            bounds = (
                x - self.vertex_radius, y - self.vertex_radius,
                x + self.vertex_radius, y + self.vertex_radius
            )
            
            vertex_primitives[vertex.id] = SpatialPrimitive(
                element_id=vertex.id,
                element_type='vertex',
                position=(x, y),
                bounds=bounds,
                z_index=self.z_vertices
            )
        
        # Position cut-contained vertices with proper hierarchical spacing
        cut_areas = [area_id for area_id in vertices_by_area.keys() if not area_id.startswith('sheet_')]
        
        # Allocate exclusive areas for sibling cuts to ensure no overlaps
        cut_area_allocations = self._allocate_exclusive_cut_areas(graph, cut_areas)
        
        for area_id in cut_areas:
            if area_id not in vertices_by_area or area_id not in cut_area_allocations:
                continue
                
            vertices = vertices_by_area[area_id]
            allocated_bounds = cut_area_allocations[area_id]
            
            # Position vertices within the allocated exclusive area for this cut
            area_x, area_y, area_width, area_height = allocated_bounds
            base_x = area_x + area_width * 0.3  # Position content within allocated area
            base_y = area_y + area_height * 0.5  # Center vertically in allocated area
            
            for j, vertex in enumerate(vertices):
                # Position vertices within the cut area
                x = base_x + (j * 80)  # Space vertices within cut
                y = base_y
                
                bounds = (
                    x - self.vertex_radius, y - self.vertex_radius,
                    x + self.vertex_radius, y + self.vertex_radius
                )
                
                vertex_primitives[vertex.id] = SpatialPrimitive(
                    element_id=vertex.id,
                    element_type='vertex',
                    position=(x, y),
                    bounds=bounds,
                    z_index=self.z_vertices
                )
        
        return vertex_primitives
    
    def _build_cut_containment_hierarchy(self, graph: RelationalGraphWithCuts, cut_areas: List[ElementID]) -> List[List[ElementID]]:
        """Build hierarchical levels of cuts based on their containment relationships."""
        if not cut_areas:
            return []
        
        # Build containment relationships from graph.area mapping
        contains = {}  # parent_cut -> [child_cuts]
        contained_by = {}  # child_cut -> parent_cut
        
        for cut_area in cut_areas:
            contains[cut_area] = []
            
            # Find what this cut contains by looking at graph.area
            if cut_area in graph.area:
                contained_elements = graph.area[cut_area]
                for elem_id in contained_elements:
                    # Check if this element is another cut
                    if elem_id in cut_areas:
                        contains[cut_area].append(elem_id)
                        contained_by[elem_id] = cut_area
        
        # Build levels from innermost (no children) to outermost (not contained by others)
        levels = []
        remaining_cuts = set(cut_areas)
        
        while remaining_cuts:
            # Find cuts at current level (innermost remaining cuts - no children remaining)
            current_level = []
            for cut_id in list(remaining_cuts):
                children = contains.get(cut_id, [])
                # A cut is at current level if none of its children are still remaining
                if all(child not in remaining_cuts for child in children):
                    current_level.append(cut_id)
            
            if not current_level:
                # Fallback: take all remaining cuts
                current_level = list(remaining_cuts)
            
            levels.append(current_level)
            remaining_cuts -= set(current_level)
        
        return levels
    
    def _allocate_exclusive_cut_areas(self, graph: RelationalGraphWithCuts, cut_areas: List[ElementID]) -> Dict[ElementID, Tuple[float, float, float, float]]:
        """Allocate exclusive, non-overlapping areas for cuts to ensure proper EG logic.
        
        Returns: Dict mapping cut_id -> (x, y, width, height) of allocated area
        """
        if not cut_areas:
            return {}
        
        # Build containment hierarchy
        cut_hierarchy = self._build_cut_containment_hierarchy(graph, cut_areas)
        
        # Build parent-child relationships
        parent_of = {}  # child_cut -> parent_cut
        children_of = {}  # parent_cut -> [child_cuts]
        
        for cut_area in cut_areas:
            children_of[cut_area] = []
            if cut_area in graph.area:
                for elem_id in graph.area[cut_area]:
                    if elem_id in cut_areas:  # This element is another cut
                        parent_of[elem_id] = cut_area
                        children_of[cut_area].append(elem_id)
        
        # Allocate areas starting from outermost cuts
        allocations = {}
        
        # Start with sheet-level cuts (outermost)
        sheet_level_cuts = [cut_id for cut_id in cut_areas if cut_id not in parent_of]
        
        # Allocate sheet-level cuts side-by-side
        canvas_start_x = 100
        canvas_start_y = 100
        cut_width = 200
        cut_height = 150
        spacing = 50
        
        for i, cut_id in enumerate(sheet_level_cuts):
            x = canvas_start_x + i * (cut_width + spacing)
            y = canvas_start_y
            allocations[cut_id] = (x, y, cut_width, cut_height)
        
        # Recursively allocate areas for nested cuts
        def allocate_children(parent_cut_id):
            if parent_cut_id not in allocations:
                return
            
            parent_x, parent_y, parent_width, parent_height = allocations[parent_cut_id]
            children = children_of.get(parent_cut_id, [])
            
            if not children:
                return
            
            # Allocate exclusive areas within parent for sibling cuts
            child_padding = 30
            available_width = parent_width - 2 * child_padding
            available_height = parent_height - 2 * child_padding
            
            if len(children) == 1:
                # Single child gets most of the parent area
                child_width = available_width * 0.8
                child_height = available_height * 0.8
                child_x = parent_x + child_padding + (available_width - child_width) / 2
                child_y = parent_y + child_padding + (available_height - child_height) / 2
                allocations[children[0]] = (child_x, child_y, child_width, child_height)
            else:
                # Multiple siblings: divide area horizontally with exclusive regions
                child_width = available_width / len(children)
                child_height = available_height * 0.8
                
                for i, child_id in enumerate(children):
                    child_x = parent_x + child_padding + i * child_width
                    child_y = parent_y + child_padding + (available_height - child_height) / 2
                    # Ensure no overlap by slightly reducing width if needed
                    actual_width = child_width * 0.9  # 10% margin between siblings
                    allocations[child_id] = (child_x, child_y, actual_width, child_height)
            
            # Recursively allocate for grandchildren
            for child_id in children:
                allocate_children(child_id)
        
        # Allocate areas for all nested cuts
        for cut_id in sheet_level_cuts:
            allocate_children(cut_id)
        
        return allocations
    
    def _position_edges_optimally(self, graph: RelationalGraphWithCuts, 
                                 vertex_primitives: Dict[ElementID, SpatialPrimitive]) -> Dict[ElementID, SpatialPrimitive]:
        """Position edges (predicates) respecting their logical area containment."""
        edge_primitives = {}
        
        # Group edges by their logical areas first
        edges_by_area = {}
        for edge in graph.E:
            area = self._find_edge_area(edge.id, graph)
            if area not in edges_by_area:
                edges_by_area[area] = []
            edges_by_area[area].append(edge)
        
        # Position sheet-level edges with improved spacing logic
        sheet_edges = edges_by_area.get(graph.sheet, [])
        
        # Group sheet edges by their connected vertex for better positioning
        edges_by_vertex = {}
        for edge in sheet_edges:
            vertex_sequence = graph.nu.get(edge.id, ())
            vertex_id = vertex_sequence[0] if vertex_sequence else None
            if vertex_id not in edges_by_vertex:
                edges_by_vertex[vertex_id] = []
            edges_by_vertex[vertex_id].append(edge)
        
        edge_index = 0
        for vertex_id, edges in edges_by_vertex.items():
            if vertex_id and vertex_id in vertex_primitives:
                vertex_pos = vertex_primitives[vertex_id].position
                vertex_x, vertex_y = vertex_pos
                
                # Position predicates around this vertex
                for local_i, edge in enumerate(edges):
                    # Use both global index and local index for spacing
                    pred_x = vertex_x + self.predicate_spacing
                    pred_y = vertex_y + (edge_index * self.predicate_spacing * 0.7)  # Slightly tighter global spacing
                    
                    # Get predicate name for bounds calculation
                    predicate_name = graph.rel.get(edge.id, "Unknown")
                    text_width = len(predicate_name) * 8
                    text_height = 20
                    
                    bounds = (
                        pred_x - text_width/2, pred_y - text_height/2,
                        pred_x + text_width/2, pred_y + text_height/2
                    )
                    
                    # Create attachment points for rendering
                    attachment_points = {}
                    if vertex_id:
                        attachment_points[vertex_id] = vertex_primitives[vertex_id].position
                    
                    edge_primitives[edge.id] = SpatialPrimitive(
                        element_id=edge.id,
                        element_type='edge',
                        position=(pred_x, pred_y),
                        bounds=bounds,
                        z_index=self.z_edges,
                        attachment_points=attachment_points
                    )
                    
                    edge_index += 1
            else:
                # Handle disconnected predicates
                for edge in edges:
                    pred_x = 200 + (edge_index * 100)
                    pred_y = 200
                    
                    # Get predicate name for bounds calculation
                    predicate_name = graph.rel.get(edge.id, "Unknown")
                    text_width = len(predicate_name) * 8
                    text_height = 20
                    
                    bounds = (
                        pred_x - text_width/2, pred_y - text_height/2,
                        pred_x + text_width/2, pred_y + text_height/2
                    )
                    
                    # Create attachment points for rendering
                    attachment_points = {}
                    
                    edge_primitives[edge.id] = SpatialPrimitive(
                        element_id=edge.id,
                        element_type='edge',
                        position=(pred_x, pred_y),
                        bounds=bounds,
                        z_index=self.z_edges,
                        attachment_points=attachment_points
                    )
                    
                    edge_index += 1
        
        # Position cut-contained edges in their designated areas with proper spacing
        cut_edge_areas = [area_id for area_id in edges_by_area.keys() if not area_id.startswith('sheet_')]
        
        for area_index, area_id in enumerate(cut_edge_areas):
            edges = edges_by_area[area_id]
            
            # Position cut edges with proper area separation
            base_x = 400 + (area_index * 200)  # Spread cut areas horizontally
            base_y = 200 + (area_index * 100)  # Vertical offset for nesting
            
            for i, edge in enumerate(edges):
                # Arrange cut predicates with good spacing within each area
                pred_x = base_x + (i * 30)  # Horizontal spacing within area
                pred_y = base_y + (i * self.predicate_spacing * 0.8)  # Vertical spacing
                
                # Find connected vertex for attachment
                vertex_sequence = graph.nu.get(edge.id, ())
                vertex_id = vertex_sequence[0] if vertex_sequence else None
                
                # Get predicate name for bounds calculation
                predicate_name = graph.rel.get(edge.id, "Unknown")
                text_width = len(predicate_name) * 8
                text_height = 20
                
                bounds = (
                    pred_x - text_width/2, pred_y - text_height/2,
                    pred_x + text_width/2, pred_y + text_height/2
                )
                
                # Create attachment points for rendering
                attachment_points = {}
                if vertex_id and vertex_id in vertex_primitives:
                    attachment_points[vertex_id] = vertex_primitives[vertex_id].position
                
                edge_primitives[edge.id] = SpatialPrimitive(
                    element_id=edge.id,
                    element_type='edge',
                    position=(pred_x, pred_y),
                    bounds=bounds,
                    z_index=self.z_edges,
                    attachment_points=attachment_points
                )
        
        return edge_primitives
    
    def _build_content_hierarchy(self, graph: RelationalGraphWithCuts,
                                vertex_primitives: Dict[ElementID, SpatialPrimitive],
                                edge_primitives: Dict[ElementID, SpatialPrimitive]) -> Dict[ElementID, ContentGroup]:
        """Build hierarchy of content groups by area - ONLY including elements that logically belong to each area."""
        content_groups = {}
        
        # Process each area in the graph
        for area_id, element_ids in graph.area.items():
            vertices = []
            edges = []
            
            # CRITICAL: Only include elements that logically belong to this area
            for element_id in element_ids:
                if element_id in vertex_primitives:
                    vertices.append(vertex_primitives[element_id])
                elif element_id in edge_primitives:
                    edges.append(edge_primitives[element_id])
            
            content_groups[area_id] = ContentGroup(
                area_id=area_id,
                vertices=vertices,
                edges=edges,
                child_cuts=[]  # Will be populated in next step
            )
        
        # Build parent-child relationships for cuts
        for cut in graph.Cut:
            parent_area = self._find_parent_area(cut.id, graph)
            if parent_area and parent_area in content_groups:
                child_group = content_groups.get(cut.id)
                if child_group:
                    content_groups[parent_area].child_cuts.append(child_group)
        
        return content_groups
    
    def _size_cuts_to_content(self, content_groups: Dict[ElementID, ContentGroup]) -> Dict[ElementID, SpatialPrimitive]:
        """Size cuts using pre-allocated exclusive areas to ensure no overlaps."""
        cut_primitives = {}
        
        # Get the graph from the content groups (we need it for area allocation)
        # This is a bit of a hack, but we need access to the graph structure
        sample_group = next(iter(content_groups.values()))
        if hasattr(self, '_current_graph'):
            graph = self._current_graph
        else:
            # Fallback: we'll need to pass the graph differently
            # For now, use the old method as fallback
            return self._size_cuts_to_content_old(content_groups)
        
        # Get cut areas
        cut_areas = [area_id for area_id in content_groups.keys() if not area_id.startswith('sheet_')]
        
        # Allocate exclusive areas for all cuts
        area_allocations = self._allocate_exclusive_cut_areas(graph, cut_areas)
        
        # Create cut primitives using the allocated exclusive areas
        for area_id in cut_areas:
            if area_id not in area_allocations:
                continue
                
            # Use the pre-allocated exclusive area directly
            alloc_x, alloc_y, alloc_width, alloc_height = area_allocations[area_id]
            
            # Convert allocation to bounds
            cut_x1 = alloc_x
            cut_y1 = alloc_y
            cut_x2 = alloc_x + alloc_width
            cut_y2 = alloc_y + alloc_height
            
            cut_bounds = (cut_x1, cut_y1, cut_x2, cut_y2)
            center_x = (cut_x1 + cut_x2) / 2
            center_y = (cut_y1 + cut_y2) / 2
            
            # Generate curve points for cut boundary
            curve_points = self._generate_cut_curve(cut_bounds)
            
            cut_primitives[area_id] = SpatialPrimitive(
                element_id=area_id,
                element_type='cut',
                position=(center_x, center_y),
                bounds=cut_bounds,
                z_index=self.z_cuts,
                curve_points=curve_points
            )
        
        return cut_primitives
    
    def _build_cut_hierarchy(self, content_groups: Dict[ElementID, ContentGroup]) -> List[List[ElementID]]:
        """Build hierarchy levels of cuts based on logical containment structure."""
        cut_areas = [area_id for area_id in content_groups.keys() if not area_id.startswith('sheet_')]
        
        if not cut_areas:
            return []
        
        # Build containment relationships from the content groups
        contains = {}  # parent_cut -> [child_cuts]
        contained_by = {}  # child_cut -> parent_cut
        
        for area_id in cut_areas:
            contains[area_id] = []
            group = content_groups[area_id]
            
            # Check if this area contains other cuts as child_cuts
            for child_group in group.child_cuts:
                if child_group and child_group.area_id in cut_areas:
                    contains[area_id].append(child_group.area_id)
                    contained_by[child_group.area_id] = area_id
        
        # Build levels from innermost (no children) to outermost (not contained)
        levels = []
        remaining_cuts = set(cut_areas)
        
        while remaining_cuts:
            # Find cuts at current level (innermost remaining cuts)
            current_level = []
            for cut_id in list(remaining_cuts):
                # A cut is at current level if none of its children are still remaining
                children = contains.get(cut_id, [])
                if all(child not in remaining_cuts for child in children):
                    current_level.append(cut_id)
            
            if not current_level:
                # Fallback: just take remaining cuts
                current_level = list(remaining_cuts)
            
            levels.append(current_level)
            remaining_cuts -= set(current_level)
        
        return levels
    
    def _calculate_hierarchical_bounds(self, group: ContentGroup, existing_cuts: Dict[ElementID, SpatialPrimitive]) -> Bounds:
        """Calculate bounds including ALL content: direct elements AND complete child cut areas."""
        # Start with bounds of direct content (vertices and edges in this area)
        if group.vertices or group.edges:
            bounds = group.get_bounding_box()
        else:
            # If no direct content, start with a minimal bounds that will be expanded
            bounds = (float('inf'), float('inf'), float('-inf'), float('-inf'))
        
        # CRITICAL: Include the COMPLETE area of any child cuts that have been processed
        for child_group in group.child_cuts:
            if child_group and child_group.area_id in existing_cuts:
                child_cut = existing_cuts[child_group.area_id]
                child_bounds = child_cut.bounds
                
                # The containing cut MUST encompass the entire child cut area
                if bounds[0] == float('inf'):  # First child cut
                    bounds = child_bounds
                else:
                    bounds = (
                        min(bounds[0], child_bounds[0]),
                        min(bounds[1], child_bounds[1]),
                        max(bounds[2], child_bounds[2]),
                        max(bounds[3], child_bounds[3])
                    )
        
        # Ensure we have valid bounds
        if bounds[0] == float('inf'):
            # Fallback for empty groups
            bounds = (0, 0, 100, 100)
        
        return bounds
    
    def _ensure_non_overlapping_bounds(self, proposed_bounds: Bounds, 
                                      existing_cuts: Dict[ElementID, SpatialPrimitive],
                                      current_area_id: ElementID) -> Bounds:
        """Ensure cut bounds don't overlap with sibling cuts using improved positioning."""
        x1, y1, x2, y2 = proposed_bounds
        width = x2 - x1
        height = y2 - y1
        
        # Find all existing cuts that could potentially overlap
        overlapping_cuts = []
        for area_id, cut_primitive in existing_cuts.items():
            if area_id == current_area_id:
                continue
            
            ex1, ey1, ex2, ey2 = cut_primitive.bounds
            
            # Check if bounds would overlap
            if not (x2 < ex1 or x1 > ex2 or y2 < ey1 or y1 > ey2):
                overlapping_cuts.append((area_id, cut_primitive))
        
        # If no overlaps, return original bounds
        if not overlapping_cuts:
            return (x1, y1, x2, y2)
        
        # Strategy: Position sibling cuts side-by-side with adequate spacing
        # Calculate how many cuts we need to position (including this one)
        num_cuts = len(overlapping_cuts) + 1
        
        # Find the rightmost position of existing cuts
        max_right = max(cut_prim.bounds[2] for _, cut_prim in overlapping_cuts)
        
        # Position this cut to the right of all existing cuts with padding
        new_x1 = max_right + self.cut_padding * 2  # Extra spacing between sibling cuts
        new_x2 = new_x1 + width
        
        # Keep the same vertical position
        return (new_x1, y1, new_x2, y2)
    
    def _generate_cut_curve(self, bounds: Bounds) -> List[Coordinate]:
        """Generate curve points for cut boundary (Dau's circular convention)."""
        x1, y1, x2, y2 = bounds
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        radius_x = (x2 - x1) / 2
        radius_y = (y2 - y1) / 2
        
        # Generate elliptical curve points
        points = []
        num_points = 32
        for i in range(num_points):
            angle = 2 * math.pi * i / num_points
            x = center_x + radius_x * math.cos(angle)
            y = center_y + radius_y * math.sin(angle)
            points.append((x, y))
        
        return points
    
    def _build_containment_hierarchy_from_graph(self, graph: RelationalGraphWithCuts) -> List[List[ElementID]]:
        """Build containment hierarchy levels from graph structure (innermost to outermost)."""
        # Start with all areas
        all_areas = list(graph.area.keys())
        
        # Build parent-child relationships
        children_of = {}  # parent_area -> [child_areas]
        parent_of = {}    # child_area -> parent_area
        
        for area_id in all_areas:
            children_of[area_id] = []
            
            # Find child areas (cuts contained in this area)
            for element_id in graph.area[area_id]:
                if element_id in [c.id for c in graph.Cut]:
                    children_of[area_id].append(element_id)
                    parent_of[element_id] = area_id
        
        # Build levels from innermost (no children) to outermost
        levels = []
        remaining_areas = set(all_areas)
        
        while remaining_areas:
            # Find areas with no remaining children (innermost at current level)
            current_level = []
            for area_id in list(remaining_areas):
                children = children_of.get(area_id, [])
                if all(child not in remaining_areas for child in children):
                    current_level.append(area_id)
            
            if not current_level:
                # Fallback: take remaining areas
                current_level = list(remaining_areas)
            
            levels.append(current_level)
            remaining_areas -= set(current_level)
        
        return levels
    
    def _layout_inside_out(self, graph: RelationalGraphWithCuts, hierarchy_levels: List[List[ElementID]]) -> Dict[ElementID, SpatialPrimitive]:
        """Layout elements from innermost to outermost level."""
        all_primitives = {}
        
        # Process each level from innermost to outermost
        for level_index, areas_at_level in enumerate(hierarchy_levels):
            for area_id in areas_at_level:
                if area_id.startswith('sheet_'):
                    # Handle sheet level (outermost)
                    sheet_primitives = self._layout_sheet_level(graph, area_id, all_primitives)
                    all_primitives.update(sheet_primitives)
                else:
                    # Handle cut level
                    cut_primitives = self._layout_cut_level(graph, area_id, all_primitives, level_index)
                    all_primitives.update(cut_primitives)
        
        return all_primitives
    
    def _layout_sheet_level(self, graph: RelationalGraphWithCuts, sheet_id: ElementID, existing_primitives: Dict[ElementID, SpatialPrimitive]) -> Dict[ElementID, SpatialPrimitive]:
        """Layout sheet-level elements (outside all cuts)."""
        primitives = {}
        
        # Position sheet-level elements in left margin, clearly outside cuts
        element_index = 0
        
        for element_id in graph.area[sheet_id]:
            if element_id in [v.id for v in graph.V]:
                # Sheet-level vertex
                x = self.margin + 50
                y = self.margin + 100 + (element_index * self.min_vertex_spacing)
                
                bounds = (
                    x - self.vertex_radius, y - self.vertex_radius,
                    x + self.vertex_radius, y + self.vertex_radius
                )
                
                primitives[element_id] = SpatialPrimitive(
                    element_id=element_id,
                    element_type='vertex',
                    position=(x, y),
                    bounds=bounds,
                    z_index=self.z_vertices
                )
                element_index += 1
                
            elif element_id in [e.id for e in graph.E]:
                # Sheet-level predicate
                # Find connected vertex for positioning
                vertex_sequence = graph.nu.get(element_id, ())
                vertex_id = vertex_sequence[0] if vertex_sequence else None
                
                if vertex_id and vertex_id in primitives:
                    vertex_pos = primitives[vertex_id].position
                    pred_x = vertex_pos[0] + self.predicate_spacing
                    pred_y = vertex_pos[1] + (element_index * 40)
                else:
                    pred_x = self.margin + 200
                    pred_y = self.margin + 100 + (element_index * 60)
                
                predicate_name = graph.rel.get(element_id, "Unknown")
                text_width = len(predicate_name) * 12  # More accurate character width
                text_height = 24  # Slightly taller for better readability
                
                bounds = (
                    pred_x - text_width/2, pred_y - text_height/2,
                    pred_x + text_width/2, pred_y + text_height/2
                )
                
                attachment_points = {}
                if vertex_id and vertex_id in primitives:
                    attachment_points[vertex_id] = primitives[vertex_id].position
                
                primitives[element_id] = SpatialPrimitive(
                    element_id=element_id,
                    element_type='edge',
                    position=(pred_x, pred_y),
                    bounds=bounds,
                    z_index=self.z_edges,
                    attachment_points=attachment_points
                )
                element_index += 1
        
        return primitives
    
    def _layout_cut_level(self, graph: RelationalGraphWithCuts, cut_id: ElementID, existing_primitives: Dict[ElementID, SpatialPrimitive], level_index: int) -> Dict[ElementID, SpatialPrimitive]:
        """Layout a cut and its contents."""
        primitives = {}
        
        # Position cut contents first
        base_x = 400 + (level_index * 150)  # Spread levels horizontally
        base_y = 200 + (level_index * 50)   # Slight vertical offset
        
        content_index = 0
        content_bounds = []
        
        for element_id in graph.area[cut_id]:
            if element_id in [v.id for v in graph.V]:
                # Cut-contained vertex
                x = base_x + (content_index * 80)
                y = base_y
                
                bounds = (
                    x - self.vertex_radius, y - self.vertex_radius,
                    x + self.vertex_radius, y + self.vertex_radius
                )
                
                primitives[element_id] = SpatialPrimitive(
                    element_id=element_id,
                    element_type='vertex',
                    position=(x, y),
                    bounds=bounds,
                    z_index=self.z_vertices
                )
                content_bounds.append(bounds)
                content_index += 1
                
            elif element_id in [e.id for e in graph.E]:
                # Cut-contained predicate
                x = base_x + (content_index * 30)
                y = base_y + (content_index * self.predicate_spacing * 0.8)
                
                predicate_name = graph.rel.get(element_id, "Unknown")
                text_width = len(predicate_name) * 12  # More accurate character width
                text_height = 24  # Slightly taller for better readability
                
                bounds = (
                    x - text_width/2, y - text_height/2,
                    x + text_width/2, y + text_height/2
                )
                
                # Find connected vertex for attachment
                vertex_sequence = graph.nu.get(element_id, ())
                vertex_id = vertex_sequence[0] if vertex_sequence else None
                
                attachment_points = {}
                if vertex_id and vertex_id in existing_primitives:
                    attachment_points[vertex_id] = existing_primitives[vertex_id].position
                elif vertex_id and vertex_id in primitives:
                    attachment_points[vertex_id] = primitives[vertex_id].position
                
                primitives[element_id] = SpatialPrimitive(
                    element_id=element_id,
                    element_type='edge',
                    position=(x, y),
                    bounds=bounds,
                    z_index=self.z_edges,
                    attachment_points=attachment_points
                )
                content_bounds.append(bounds)
                content_index += 1
            
            elif element_id in existing_primitives:
                # Child cut already processed
                child_bounds = existing_primitives[element_id].bounds
                content_bounds.append(child_bounds)
        
        # Size cut to contain all content
        if content_bounds:
            min_x = min(b[0] for b in content_bounds)
            min_y = min(b[1] for b in content_bounds)
            max_x = max(b[2] for b in content_bounds)
            max_y = max(b[3] for b in content_bounds)
            
            # Add padding
            cut_x1 = min_x - self.cut_padding
            cut_y1 = min_y - self.cut_padding
            cut_x2 = max_x + self.cut_padding
            cut_y2 = max_y + self.cut_padding
        else:
            # Empty cut
            cut_x1, cut_y1 = base_x - 50, base_y - 50
            cut_x2, cut_y2 = base_x + 50, base_y + 50
        
        cut_bounds = (cut_x1, cut_y1, cut_x2, cut_y2)
        center_x = (cut_x1 + cut_x2) / 2
        center_y = (cut_y1 + cut_y2) / 2
        
        curve_points = self._generate_cut_curve(cut_bounds)
        
        primitives[cut_id] = SpatialPrimitive(
            element_id=cut_id,
            element_type='cut',
            position=(center_x, center_y),
            bounds=cut_bounds,
            z_index=self.z_cuts,
            curve_points=curve_points
        )
        
        return primitives
    
    def _optimize_global_layout(self, primitives: Dict[ElementID, SpatialPrimitive]):
        """Final optimization to prevent overlaps and ensure clean presentation."""
        # This is where we could add sophisticated optimization algorithms
        # For now, we rely on the inside-out approach providing good initial layout
        pass
    
    def _find_vertex_area(self, vertex_id: ElementID, graph: RelationalGraphWithCuts) -> ElementID:
        """Find which area contains this vertex."""
        for area_id, elements in graph.area.items():
            if vertex_id in elements:
                return area_id
        return graph.sheet  # Default to sheet if not found
    
    def _find_edge_area(self, edge_id: ElementID, graph: RelationalGraphWithCuts) -> ElementID:
        """Find which area contains this edge."""
        for area_id, elements in graph.area.items():
            if edge_id in elements:
                return area_id
        return graph.sheet  # Default to sheet if not found
    
    def _find_parent_area(self, element_id: ElementID, graph: RelationalGraphWithCuts) -> Optional[ElementID]:
        """Find which area directly contains this element."""
        for area_id, elements in graph.area.items():
            if element_id in elements:
                return area_id
        return None
    
    def _calculate_canvas_bounds(self, primitives: Dict[ElementID, SpatialPrimitive]) -> Bounds:
        """Calculate overall canvas bounds containing all primitives."""
        if not primitives:
            return (0, 0, self.canvas_width, self.canvas_height)
        
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        for primitive in primitives.values():
            if primitive.bounds:
                x1, y1, x2, y2 = primitive.bounds
                min_x, min_y = min(min_x, x1), min(min_y, y1)
                max_x, max_y = max(max_x, x2), max(max_y, y2)
        
        return (min_x - self.margin, min_y - self.margin, 
                max_x + self.margin, max_y + self.margin)
    
    def _build_containment_hierarchy(self, graph: RelationalGraphWithCuts) -> Dict[ElementID, Set[ElementID]]:
        """Build containment hierarchy for the graph."""
        hierarchy = {}
        for area_id, elements in graph.area.items():
            hierarchy[area_id] = set(elements)
        return hierarchy


# Test function
def test_content_driven_layout():
    """Test the content-driven layout engine."""
    from egif_parser_dau import EGIFParser
    
    # Parse test graph
    egif = '*x (Human x) ~[ (Mortal x) (Wise x) ]'
    parser = EGIFParser(egif)
    graph = parser.parse()
    
    # Generate content-driven layout
    layout_engine = ContentDrivenLayoutEngine()
    layout = layout_engine.layout_graph(graph)
    
    print("=== Content-Driven Layout Results ===")
    for elem_id, primitive in layout.primitives.items():
        if primitive.element_type == 'edge':
            predicate_name = graph.rel.get(elem_id, 'Unknown')
            print(f"{predicate_name}: {primitive.position}")
        else:
            print(f"{primitive.element_type} {elem_id[-8:]}: {primitive.position}")


if __name__ == "__main__":
    test_content_driven_layout()
