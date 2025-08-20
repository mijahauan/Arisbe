#!/usr/bin/env python3
"""
Area-Based Dau Renderer

Clean, modern renderer that directly consumes AreaBasedLayoutEngine output
and generates Dau-compliant visual primitives with no legacy assumptions.

Replaces egdf_dau_canonical.py with a direct Area-Based Layout Engine integration.
"""

from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
import math

# Handle imports for both module and script execution
try:
    from .egi_core_dau import RelationalGraphWithCuts, ElementID, Vertex, Edge, Cut
    from .layout_types import LayoutResult, LayoutElement
except ImportError:
    from egi_core_dau import RelationalGraphWithCuts, ElementID, Vertex, Edge, Cut
    from layout_types import LayoutResult, LayoutElement

# Type aliases
Coordinate = Tuple[float, float]
Bounds = Tuple[float, float, float, float]  # x1, y1, x2, y2


@dataclass
class DauVisualConstants:
    """Dau-compliant visual constants per specification."""
    
    # Ligatures (Chapter 16) - Heavy lines for identity
    ligature_width: float = 2.5
    ligature_color: str = "#000000"
    ligature_clearance: float = 8.0
    
    # Vertices (Identity spots) - Only slightly larger than heavy line width
    vertex_radius: float = 1.5  # Slightly larger than ligature_width (2.5)
    vertex_color: str = "#000000"
    vertex_label_offset: float = 12.0
    
    # Cuts (Negation boundaries) - Fine lines
    cut_line_width: float = 1.5
    cut_color: str = "#000000"
    cut_corner_radius: float = 8.0
    cut_padding: float = 16.0
    
    # Predicates (Relations)
    predicate_font_size: int = 12
    predicate_color: str = "#000000"
    predicate_padding_x: float = 6.0
    predicate_padding_y: float = 4.0
    
    # Optional annotations
    arity_annotation_font_size: int = 8
    arity_annotation_color: str = "#666666"
    identity_annotation_text: str = "="
    identity_annotation_font_size: int = 10
    identity_annotation_color: str = "#444444"


@dataclass
class DauRenderPrimitive:
    """Clean rendering primitive for Dau-compliant visual output."""
    element_id: ElementID
    element_type: str  # 'vertex', 'predicate', 'cut', 'ligature'
    position: Coordinate
    bounds: Bounds
    
    # Visual properties
    text: Optional[str] = None
    color: str = "#000000"
    line_width: float = 1.0
    font_size: int = 12
    
    # Geometric properties
    curve_points: Optional[List[Coordinate]] = None
    attachment_points: Optional[Dict[str, Coordinate]] = None
    
    # Containment
    parent_area: Optional[ElementID] = None
    contained_elements: Set[ElementID] = None
    
    def __post_init__(self):
        if self.contained_elements is None:
            self.contained_elements = set()


class AreaBasedDauRenderer:
    """
    Clean Dau renderer that directly consumes AreaBasedLayoutEngine output.
    
    No legacy Graphviz assumptions - works directly with LayoutResult and LayoutElement.
    Generates Dau-compliant visual primitives for rendering.
    """
    
    def __init__(self, visual_constants: Optional[DauVisualConstants] = None):
        """Initialize with Dau visual constants."""
        self.constants = visual_constants or DauVisualConstants()
        
    def render_from_layout(self, egi: RelationalGraphWithCuts, 
                          layout_result: LayoutResult) -> List[DauRenderPrimitive]:
        """
        Generate Dau-compliant render primitives from Area-Based Layout Engine output.
        
        Direct consumption of LayoutResult with no legacy assumptions.
        """
        primitives = []
        
        # First, render sheet background (positive context - white)
        sheet_element = layout_result.elements.get(egi.sheet)
        if sheet_element:
            sheet_background = self._render_sheet_background(egi.sheet, sheet_element)
            primitives.extend(sheet_background)
        
        # Process each layout element directly
        for element_id, layout_element in layout_result.elements.items():
            if layout_element.element_type == 'cut':
                primitives.extend(self._render_cut(element_id, layout_element, egi))
            elif layout_element.element_type == 'vertex':
                primitives.extend(self._render_vertex(element_id, layout_element, egi))
            elif layout_element.element_type == 'predicate':
                primitives.extend(self._render_predicate(element_id, layout_element, egi))
        
        # Generate ligatures (heavy lines) between connected elements
        ligature_primitives = self._generate_ligatures(egi, layout_result)
        primitives.extend(ligature_primitives)
        
        return primitives
    
    def _render_cut(self, cut_id: ElementID, layout_element: LayoutElement, 
                   egi: RelationalGraphWithCuts) -> List[DauRenderPrimitive]:
        """Render a cut as a Dau-compliant fine-drawn closed curve with context background."""
        x1, y1, x2, y2 = layout_element.bounds
        
        # Generate smooth closed curve for cut boundary
        curve_points = self._generate_smooth_cut_boundary(x1, y1, x2, y2)
        
        # Cut background primitive (negative context - light gray)
        cut_background = DauRenderPrimitive(
            element_id=f"{cut_id}_background",
            element_type='cut_background',
            position=(x1, y1),
            bounds=layout_element.bounds,
            color="#F5F5F5",  # Light gray for negative context
            line_width=0,  # No border for background
            curve_points=curve_points,  # Smooth boundary
            parent_area=layout_element.parent_area,
            contained_elements=layout_element.contained_elements.copy()
        )
        
        # Cut boundary primitive with smooth curve
        cut_primitive = DauRenderPrimitive(
            element_id=cut_id,
            element_type='cut',
            position=(x1, y1),
            bounds=layout_element.bounds,
            color=self.constants.cut_color,
            line_width=self.constants.cut_line_width,
            curve_points=curve_points,  # Smooth closed curve
            parent_area=layout_element.parent_area,
            contained_elements=layout_element.contained_elements.copy()
        )
        
        return [cut_background, cut_primitive]
    
    def _render_vertex(self, vertex_id: ElementID, layout_element: LayoutElement,
                      egi: RelationalGraphWithCuts) -> List[DauRenderPrimitive]:
        """Render a vertex as a Dau-compliant heavy spot with optional label."""
        x, y = layout_element.position
        radius = self.constants.vertex_radius
        
        # Vertex spot primitive
        vertex_primitive = DauRenderPrimitive(
            element_id=vertex_id,
            element_type='vertex',
            position=(x, y),
            bounds=(x - radius, y - radius, x + radius, y + radius),
            color=self.constants.vertex_color,
            line_width=self.constants.ligature_width,  # Heavy spot
            parent_area=layout_element.parent_area
        )
        
        primitives = [vertex_primitive]
        
        # Add vertex label if it has a constant name (properly positioned)
        vertex = self._find_vertex_by_id(vertex_id, egi)
        if vertex and hasattr(vertex, 'name') and vertex.name:
            # Position label relative to identity spot and connected ligatures
            label_position = self._calculate_optimal_label_position(
                vertex_id, (x, y), vertex.name, egi, layout_element
            )
            label_x, label_y = label_position
            
            # Estimate text bounds using Dau conventions
            char_width = self.constants.predicate_font_size * 0.6
            text_width = len(vertex.name) * char_width
            text_height = self.constants.predicate_font_size
            
            label_primitive = DauRenderPrimitive(
                element_id=f"{vertex_id}_label",
                element_type='vertex_label',
                position=(label_x, label_y),
                bounds=(label_x - 2, label_y - 2, 
                       label_x + text_width + 2, label_y + text_height + 2),
                text=vertex.name,
                color=self.constants.predicate_color,
                font_size=self.constants.predicate_font_size,
                parent_area=layout_element.parent_area
            )
            primitives.append(label_primitive)
        
        return primitives
    
    def _render_predicate(self, predicate_id: ElementID, layout_element: LayoutElement,
                         egi: RelationalGraphWithCuts) -> List[DauRenderPrimitive]:
        """Render a predicate as Dau-compliant relation text."""
        x, y = layout_element.position
        
        # Find the relation name
        relation_name = self._get_relation_name(predicate_id, egi)
        
        # Calculate text bounds
        text_width = len(relation_name) * 8  # Approximate
        text_height = self.constants.predicate_font_size
        
        predicate_primitive = DauRenderPrimitive(
            element_id=predicate_id,
            element_type='predicate',
            position=(x, y),
            bounds=(x - self.theme.conventions.PREDICATE_PADDING_X, 
                   y - self.theme.conventions.PREDICATE_PADDING_Y,
                   x + text_width + self.theme.conventions.PREDICATE_PADDING_X,
                   y + text_height + self.theme.conventions.PREDICATE_PADDING_Y),
            text=relation_name,
            color=self.constants.predicate_color,
            font_size=self.constants.predicate_font_size,
            parent_area=layout_element.parent_area
        )
        
        return [predicate_primitive]
    
    def _generate_ligatures(self, egi: RelationalGraphWithCuts, 
                           layout_result: LayoutResult) -> List[DauRenderPrimitive]:
        """Generate enhanced ligatures (heavy lines) with advanced routing and attachment."""
        ligatures = []
        
        # For each edge (predicate), create ligatures to its vertices
        for edge in egi.E:
            edge_id = edge.id if hasattr(edge, 'id') else str(edge)
            
            # Find predicate position
            predicate_element = layout_result.elements.get(edge_id)
            if not predicate_element:
                continue
                
            predicate_pos = predicate_element.position
            predicate_bounds = predicate_element.bounds
            
            # Create ligatures to each argument vertex using nu mapping
            vertex_sequence = egi.nu.get(edge_id, [])
            for i, vertex_id in enumerate(vertex_sequence):
                vertex_element = layout_result.elements.get(vertex_id)
                if not vertex_element:
                    continue
                    
                vertex_pos = vertex_element.position
                
                # Enhanced ligature with smart attachment and routing
                ligature_primitive = self._create_enhanced_ligature(
                    edge_id, vertex_id, i, len(vertex_sequence),
                    predicate_pos, predicate_bounds, vertex_pos,
                    predicate_element.parent_area
                )
                
                ligatures.append(ligature_primitive)
                
                # Add argument order label for n-ary predicates (Dau convention)
                if len(vertex_sequence) > 1:
                    arg_label_primitive = self._create_argument_label(
                        edge_id, vertex_id, i + 1,  # 1-based indexing
                        ligature_primitive.curve_points or [ligature_primitive.position, vertex_pos],
                        predicate_element.parent_area
                    )
                    ligatures.append(arg_label_primitive)
        
        return ligatures
    
    def _create_enhanced_ligature(self, edge_id: ElementID, vertex_id: ElementID,
                                 arg_index: int, total_args: int,
                                 predicate_pos: Coordinate, predicate_bounds: Bounds,
                                 vertex_pos: Coordinate, parent_area: Optional[ElementID]) -> DauRenderPrimitive:
        """Create an enhanced ligature with smart attachment points and routing."""
        
        # Calculate smart attachment point on predicate
        attachment_point = self._calculate_predicate_attachment(
            predicate_pos, predicate_bounds, vertex_pos, arg_index, total_args
        )
        
        # Generate rectilinear routing path
        routing_path = self._generate_rectilinear_path(attachment_point, vertex_pos)
        
        # Create ligature ID with argument position info
        ligature_id = f"ligature_{edge_id}_{vertex_id}_arg{arg_index}"
        
        ligature_primitive = DauRenderPrimitive(
            element_id=ligature_id,
            element_type='ligature',
            position=attachment_point,  # Smart attachment point
            bounds=self._calculate_path_bounds(routing_path),
            color=self.constants.ligature_color,
            line_width=self.constants.ligature_width,
            curve_points=routing_path,  # Enhanced routing
            parent_area=parent_area,
            attachment_points={
                'predicate': attachment_point,
                'vertex': vertex_pos,
                'arg_index': arg_index
            }
        )
        
        return ligature_primitive
    
    def _calculate_predicate_attachment(self, predicate_pos: Coordinate, predicate_bounds: Bounds,
                                       vertex_pos: Coordinate, arg_index: int, total_args: int) -> Coordinate:
        """Calculate cardinal direction attachment point on predicate with close positioning."""
        px, py = predicate_pos
        vx, vy = vertex_pos
        x1, y1, x2, y2 = predicate_bounds
        
        # Calculate direction from predicate to vertex
        dx = vx - px
        dy = vy - py
        
        if arg_index < 4:  # Cardinal directions for up to 4 arguments
            # Use cardinal directions: North, East, South, West with minimal padding
            if arg_index == 0:
                attach_x = px
                attach_y = y1 - self.theme.conventions.PREDICATE_PADDING_Y  # North
            elif arg_index == 1:
                attach_x = x2 + self.theme.conventions.PREDICATE_PADDING_X  # East
                attach_y = py
            elif arg_index == 2:
                attach_x = px
                attach_y = y2 + self.theme.conventions.PREDICATE_PADDING_Y  # South
            else:  # arg_index == 3
                attach_x = x1 - self.theme.conventions.PREDICATE_PADDING_X  # West
                attach_y = py
        else:
            # For >4 arguments, distribute around perimeter with minimal padding
            angle = (arg_index * 2 * math.pi) / total_args
            radius_x = (x2 - x1) / 2 + self.theme.conventions.PREDICATE_PADDING_X
            radius_y = (y2 - y1) / 2 + self.theme.conventions.PREDICATE_PADDING_Y
            attach_x = px + radius_x * math.cos(angle)
            attach_y = py + radius_y * math.sin(angle)
        
        return (attach_x, attach_y)
    
    def _generate_rectilinear_path(self, start: Coordinate, end: Coordinate) -> List[Coordinate]:
        """Generate rectilinear path with minimal 90-degree angles (shortest path routing)."""
        sx, sy = start
        ex, ey = end
        
        # Calculate shortest rectilinear path with minimal turns
        dx = abs(ex - sx)
        dy = abs(ey - sy)
        
        # Use single turn if possible (L-shaped path)
        if dx > dy:
            # Horizontal-first routing (fewer turns for wide spacing)
            mid_x = ex
            mid_y = sy
            return [start, (mid_x, mid_y), end]
        else:
            # Vertical-first routing (fewer turns for tall spacing)
            mid_x = sx
            mid_y = ey
            return [start, (mid_x, mid_y), end]
    
    def _path_intersects_predicates(self, start: Coordinate, end: Coordinate) -> bool:
        """Check if direct path between points intersects any predicate text."""
        # For now, assume intersection if path is too close to any predicate
        # This would be enhanced with actual predicate bounds checking
        return False  # Simplified for initial implementation
    
    def _generate_curved_avoidance_path(self, start: Coordinate, end: Coordinate) -> List[Coordinate]:
        """Generate curved path that avoids predicate text obstacles."""
        sx, sy = start
        ex, ey = end
        
        # Calculate control points for smooth curve around obstacles
        mid_x = (sx + ex) / 2
        mid_y = (sy + ey) / 2
        
        # Add curve offset perpendicular to direct line
        dx = ex - sx
        dy = ey - sy
        length = math.sqrt(dx*dx + dy*dy)
        
        if length > 0:
            # Perpendicular offset for curve
            offset_x = -dy / length * 20  # 20px curve offset
            offset_y = dx / length * 20
            
            # Control points for smooth curve
            ctrl1_x = sx + dx * 0.25 + offset_x * 0.5
            ctrl1_y = sy + dy * 0.25 + offset_y * 0.5
            ctrl2_x = sx + dx * 0.75 + offset_x * 0.5
            ctrl2_y = sy + dy * 0.75 + offset_y * 0.5
            
            return [start, (ctrl1_x, ctrl1_y), (ctrl2_x, ctrl2_y), end]
        else:
            return [start, end]
    
    def _generate_smooth_curve(self, start: Coordinate, end: Coordinate) -> List[Coordinate]:
        """Generate smooth curve between two points."""
        sx, sy = start
        ex, ey = end
        
        # Simple bezier curve with control points
        ctrl1_x = sx + (ex - sx) * 0.33
        ctrl1_y = sy + (ey - sy) * 0.1
        ctrl2_x = sx + (ex - sx) * 0.67
        ctrl2_y = sy + (ey - sy) * 0.9
        
        return [start, (ctrl1_x, ctrl1_y), (ctrl2_x, ctrl2_y), end]
    
    def _calculate_path_bounds(self, path: List[Coordinate]) -> Bounds:
        """Calculate bounding box for a path of points."""
        if not path:
            return (0, 0, 0, 0)
            
        xs = [p[0] for p in path]
        ys = [p[1] for p in path]
        
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        # Add padding for line width
        padding = self.constants.ligature_width / 2
        return (min_x - padding, min_y - padding, max_x + padding, max_y + padding)
    
    def _find_vertex_by_id(self, vertex_id: ElementID, 
                          egi: RelationalGraphWithCuts) -> Optional[Vertex]:
        """Find vertex by ID in the EGI."""
        for vertex in egi.V:
            if (hasattr(vertex, 'id') and vertex.id == vertex_id) or str(vertex) == vertex_id:
                return vertex
        return None
    
    def _get_relation_name(self, edge_id: ElementID, 
                          egi: RelationalGraphWithCuts) -> str:
        """Get relation name for an edge."""
        for edge in egi.E:
            if (hasattr(edge, 'id') and edge.id == edge_id) or str(edge) == edge_id:
                return edge.relation if hasattr(edge, 'relation') else str(edge)
        return "R"  # Default relation name
    
    def _calculate_line_bounds(self, start: Coordinate, end: Coordinate) -> Bounds:
        """Calculate bounding box for a line."""
        x1, y1 = start
        x2, y2 = end
        
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)
        
        # Add small padding for line width
        padding = self.constants.ligature_width / 2
        return (min_x - padding, min_y - padding, max_x + padding, max_y + padding)
    
    def _create_argument_label(self, edge_id: ElementID, vertex_id: ElementID, 
                              arg_number: int, ligature_path: List[Coordinate],
                              parent_area: Optional[ElementID]) -> DauRenderPrimitive:
        """Create numerical argument label for n-ary predicate connections (Dau convention)."""
        
        # Find midpoint of ligature for label placement
        if len(ligature_path) >= 2:
            start_point = ligature_path[0]
            end_point = ligature_path[-1]
            # Place label at 1/3 distance from predicate toward vertex
            label_x = start_point[0] + (end_point[0] - start_point[0]) * 0.33
            label_y = start_point[1] + (end_point[1] - start_point[1]) * 0.33
        else:
            # Fallback to first point
            label_x, label_y = ligature_path[0] if ligature_path else (0, 0)
        
        # Offset label slightly from line to avoid overlap
        label_offset = 8.0
        label_x += label_offset
        label_y -= label_offset
        
        # Create label primitive
        label_id = f"arg_label_{edge_id}_{vertex_id}_{arg_number}"
        label_text = str(arg_number)
        
        # Estimate text bounds
        char_width = self.constants.arity_annotation_font_size * 0.6
        text_width = len(label_text) * char_width
        text_height = self.constants.arity_annotation_font_size
        
        label_primitive = DauRenderPrimitive(
            element_id=label_id,
            element_type='argument_label',
            position=(label_x, label_y),
            bounds=(label_x - 2, label_y - 2, 
                   label_x + text_width + 2, label_y + text_height + 2),
            text=label_text,
            color=self.constants.arity_annotation_color,
            font_size=self.constants.arity_annotation_font_size,
            parent_area=parent_area
        )
        
        return label_primitive
    
    def _render_sheet_background(self, sheet_id: ElementID, layout_element: LayoutElement) -> List[DauRenderPrimitive]:
        """Render sheet background (positive context - white)."""
        x1, y1, x2, y2 = layout_element.bounds
        
        sheet_background = DauRenderPrimitive(
            element_id=f"{sheet_id}_background",
            element_type='sheet_background',
            position=(x1, y1),
            bounds=layout_element.bounds,
            color="#FFFFFF",  # White for positive context
            line_width=0,  # No border for background
            parent_area=None,  # Sheet has no parent
            contained_elements=layout_element.contained_elements.copy()
        )
        
        return [sheet_background]
    
    def _generate_smooth_cut_boundary(self, x1: float, y1: float, x2: float, y2: float) -> List[Coordinate]:
        """Generate smooth closed curve boundary for cuts (Dau convention)."""
        width = x2 - x1
        height = y2 - y1
        
        # Corner radius for smooth curves
        radius = min(self.constants.cut_corner_radius, width * 0.2, height * 0.2)
        
        # Generate rounded rectangle as closed curve
        points = []
        
        # Top edge with rounded corners
        points.append((x1 + radius, y1))  # Start after top-left curve
        points.append((x2 - radius, y1))  # End before top-right curve
        
        # Top-right corner curve
        points.append((x2 - radius * 0.3, y1 + radius * 0.3))
        points.append((x2, y1 + radius))
        
        # Right edge
        points.append((x2, y2 - radius))
        
        # Bottom-right corner curve
        points.append((x2 - radius * 0.3, y2 - radius * 0.3))
        points.append((x2 - radius, y2))
        
        # Bottom edge
        points.append((x1 + radius, y2))
        
        # Bottom-left corner curve
        points.append((x1 + radius * 0.3, y2 - radius * 0.3))
        points.append((x1, y2 - radius))
        
        # Left edge
        points.append((x1, y1 + radius))
        
        # Top-left corner curve (close the shape)
        points.append((x1 + radius * 0.3, y1 + radius * 0.3))
        points.append((x1 + radius, y1))  # Back to start
        
        return points
    
    def _calculate_optimal_label_position(self, vertex_id: ElementID, vertex_pos: Coordinate, 
                                         label_text: str, egi: RelationalGraphWithCuts,
                                         layout_element: LayoutElement) -> Coordinate:
        """Calculate optimal position for vertex constant label relative to identity spot and ligatures."""
        vx, vy = vertex_pos
        
        # Find connected predicates to determine ligature directions
        connected_predicates = []
        for edge in egi.E:
            edge_id = edge.id if hasattr(edge, 'id') else str(edge)
            vertex_sequence = egi.nu.get(edge_id, [])
            if vertex_id in vertex_sequence:
                connected_predicates.append(edge_id)
        
        # Default position: right of vertex with slight offset
        default_offset_x = self.constants.vertex_label_offset
        default_offset_y = -4  # Slight upward offset
        
        if not connected_predicates:
            # No connections - use default position
            return (vx + default_offset_x, vy + default_offset_y)
        
        # Calculate average direction of connected ligatures to avoid overlap
        total_dx = 0
        total_dy = 0
        
        # This is a simplified version - in full implementation would use actual predicate positions
        # For now, use default positioning with slight randomization based on vertex_id hash
        hash_offset = hash(str(vertex_id)) % 4
        if hash_offset == 0:
            return (vx + default_offset_x, vy + default_offset_y)
        elif hash_offset == 1:
            return (vx - default_offset_x - len(label_text) * 4, vy + default_offset_y)
        elif hash_offset == 2:
            return (vx, vy + default_offset_x)
        else:
            return (vx, vy - default_offset_x)
    
    def _find_vertex_by_id(self, vertex_id: ElementID, egi: RelationalGraphWithCuts):
        """Find vertex object by ID in EGI."""
        for vertex in egi.V:
            if (hasattr(vertex, 'id') and vertex.id == vertex_id) or str(vertex) == str(vertex_id):
                return vertex
        return None


def create_area_based_dau_renderer(visual_constants: Optional[DauVisualConstants] = None) -> AreaBasedDauRenderer:
    """Create an Area-Based Dau Renderer with optional custom visual constants."""
    return AreaBasedDauRenderer(visual_constants)
