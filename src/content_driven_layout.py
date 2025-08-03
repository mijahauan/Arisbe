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
        self.cut_padding = 30.0  # Padding around cut contents
        self.predicate_spacing = 90.0  # Minimum distance between predicates
        
        # Z-index layers
        self.z_cuts = 0
        self.z_vertices = 1
        self.z_edges = 2
    
    def layout_graph(self, graph: RelationalGraphWithCuts) -> LayoutResult:
        """
        Main entry point: Content-driven layout approach.
        
        Process:
        1. Position all content elements (vertices, edges) optimally
        2. Group content by containing areas
        3. Size cuts to fit their contents
        4. Adjust overall layout for clean presentation
        """
        
        # Step 1: Position all content elements first (without cut constraints)
        vertex_primitives = self._position_vertices_freely(graph)
        edge_primitives = self._position_edges_optimally(graph, vertex_primitives)
        
        # Step 2: Group content by areas and build hierarchy
        content_groups = self._build_content_hierarchy(graph, vertex_primitives, edge_primitives)
        
        # Step 3: Size cuts to fit their contents
        cut_primitives = self._size_cuts_to_content(content_groups)
        
        # Step 4: Final layout adjustment and optimization
        all_primitives = {**vertex_primitives, **edge_primitives, **cut_primitives}
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
        
        # Position cut-contained vertices (will be positioned after cut layout)
        # For now, give them temporary positions that will be refined later
        cut_vertex_index = 0
        for area_id, vertices in vertices_by_area.items():
            if area_id == graph.sheet:
                continue  # Already handled
            
            for vertex in vertices:
                # Temporary position - will be refined when cuts are sized
                x = 300 + (cut_vertex_index * 60)
                y = 200 + (cut_vertex_index * 60)
                cut_vertex_index += 1
                
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
        
        # Position cut-contained edges in their designated areas
        for area_id, edges in edges_by_area.items():
            if area_id == graph.sheet:
                continue  # Already handled
            
            # Position cut edges in a cluster, separate from sheet elements
            base_x = 300  # Start cut predicates away from sheet area
            base_y = 200
            
            for i, edge in enumerate(edges):
                # Arrange cut predicates in a vertical stack
                pred_x = base_x + (i * 20)  # Slight horizontal offset
                pred_y = base_y + (i * self.predicate_spacing)
                
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
        """Size cuts to appropriately contain their contents."""
        cut_primitives = {}
        
        for area_id, group in content_groups.items():
            # Skip sheet area (not a cut)
            if area_id.startswith('sheet_'):
                continue
            
            # Calculate bounding box of all content in this group
            content_bounds = group.get_bounding_box()
            x1, y1, x2, y2 = content_bounds
            
            # Add padding around content
            cut_x1 = x1 - self.cut_padding
            cut_y1 = y1 - self.cut_padding
            cut_x2 = x2 + self.cut_padding
            cut_y2 = y2 + self.cut_padding
            
            # Cut center and bounds
            center_x = (cut_x1 + cut_x2) / 2
            center_y = (cut_y1 + cut_y2) / 2
            cut_bounds = (cut_x1, cut_y1, cut_x2, cut_y2)
            
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
    
    def _optimize_global_layout(self, primitives: Dict[ElementID, SpatialPrimitive]):
        """Final optimization to prevent overlaps and ensure clean presentation."""
        # This is where we could add sophisticated optimization algorithms
        # For now, we rely on the content-driven approach providing good initial layout
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
