#!/usr/bin/env python3
"""
DiagramRenderer for Existential Graphs (Dau's Formalism)

This module implements the visual presentation layer that takes layout coordinates
from the Graphviz layout engine and renders proper Existential Graph diagrams
according to Peirce's conventions as formalized by Frithjof Dau.

The DiagramRenderer is the visual bridge that makes the abstract EGI model
understandable by adhering to precise rules of visual representation.
"""

import math
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from egi_core_dau import RelationalGraphWithCuts, ElementID
from layout_engine_clean import LayoutResult, SpatialPrimitive
from pyside6_canvas import PySide6Canvas


@dataclass
class VisualConvention:
    """Visual parameters for Peirce/Dau conventions."""
    # Line weights per Dau's formalism
    identity_line_width: float = 4.0      # Heavy lines of identity (thicker)
    cut_line_width: float = 1.5           # Fine-drawn cut curves
    hook_line_width: float = 1.5          # Predicate attachment hooks
    
    # Sizes and spacing
    identity_spot_radius: float = 3.0     # Identity spots
    hook_length: float = 12.0             # Predicate hook length
    argument_label_offset: float = 8.0    # Distance for argument numbers
    
    # Colors (all black per EG conventions)
    line_color: Tuple[int, int, int] = (0, 0, 0)
    text_color: Tuple[int, int, int] = (0, 0, 0)
    cut_color: Tuple[int, int, int] = (0, 0, 0)


class DiagramRendererDau:
    """
    DiagramRenderer implementing Peirce's conventions as formalized by Dau.
    
    Takes layout coordinates from Graphviz and renders proper EG diagrams
    with correct visual encoding of the abstract EGI model.
    """
    
    def __init__(self, conventions: VisualConvention = None):
        self.conv = conventions or VisualConvention()
        
    def render_diagram(self, canvas: PySide6Canvas, graph: RelationalGraphWithCuts, 
                      layout_result: LayoutResult) -> None:
        """
        Render complete EG diagram with Peirce/Dau visual conventions.
        
        Args:
            canvas: Drawing surface
            graph: EGI structure (logical truth)
            layout_result: Spatial coordinates from Graphviz layout engine
        """
        canvas.clear()
        
        # Calculate centering offset to properly position diagram
        offset_x, offset_y = self._calculate_centering_offset(canvas, layout_result)
        
        # Apply centering offset to all coordinates
        centered_layout = self._apply_centering_offset(layout_result, offset_x, offset_y)
        
        # Render in proper layering order (background to foreground)
        self._render_cuts_as_fine_curves(canvas, graph, centered_layout)
        self._render_ligatures_and_identity_lines(canvas, graph, centered_layout)
        self._render_predicates_with_hooks(canvas, graph, centered_layout)
        self._render_identity_spots_and_constants(canvas, graph, centered_layout)
        
        # Add diagram metadata
        self._render_diagram_title(canvas, graph)
    
    def _render_cuts_as_fine_curves(self, canvas: PySide6Canvas, graph: RelationalGraphWithCuts,
                                   layout_result: LayoutResult) -> None:
        """
        Render cuts as fine-drawn, closed curves with correct nesting.
        
        The nesting of curves must reflect the areaMap of the underlying EGI,
        ensuring that a cut's visual area correctly contains all its enclosed elements.
        """
        # Process cuts in hierarchical order (outermost first)
        cut_hierarchy = self._build_cut_hierarchy(graph)
        
        for cut in graph.Cut:
            if cut.id in layout_result.primitives:
                cut_primitive = layout_result.primitives[cut.id]
                
                # Determine cut boundaries from layout
                bounds = cut_primitive.bounds
                center_x = (bounds[0] + bounds[2]) / 2
                center_y = (bounds[1] + bounds[3]) / 2
                width = bounds[2] - bounds[0]
                height = bounds[3] - bounds[1]
                
                # Render as fine-drawn closed curve (oval)
                canvas.draw_oval(
                    bounds[0], bounds[1], bounds[2], bounds[3],
                    {
                        'color': self.conv.cut_color,
                        'width': self.conv.cut_line_width,  # FIXED: API mismatch
                        'fill_color': None  # No fill - just the curve
                    }
                )
                
                # Add cut label (optional, for debugging)
                canvas.draw_text(
                    f"Cut {cut.id[:6]}",
                    (center_x, bounds[1] - 10),
                    {
                        'color': (100, 100, 100),
                        'font_size': 8
                    }
                )
    
    def _render_ligatures_and_identity_lines(self, canvas: PySide6Canvas, 
                                           graph: RelationalGraphWithCuts,
                                           layout_result: LayoutResult) -> None:
        """
        Draw ligatures and lines of identity as bold, continuous lines.
        
        Must handle branches, junctions, and connections to predicates correctly.
        """
        # For each vertex, draw heavy lines to connected predicates
        for vertex_id, vertex in graph._vertex_map.items():
            if vertex_id not in layout_result.primitives:
                continue
                
            vertex_primitive = layout_result.primitives[vertex_id]
            vertex_pos = vertex_primitive.position
            
            # Find all predicates connected to this vertex
            connected_predicates = self._find_vertex_predicates(vertex_id, graph, layout_result)
            
            if connected_predicates:
                # Draw heavy lines of identity to each predicate
                for i, pred_info in enumerate(connected_predicates):
                    self._draw_identity_line_to_predicate(
                        canvas, vertex_pos, pred_info, i, len(connected_predicates)
                    )
    
    def _render_predicates_with_hooks(self, canvas: PySide6Canvas,
                                    graph: RelationalGraphWithCuts,
                                    layout_result: LayoutResult) -> None:
        """
        Render predicates as textual signs with hooks and argument order labels.
        
        FIXED: Ensures predicate text never crosses cut boundaries and lines
        connect cleanly to predicate periphery per Dau's conventions.
        """
        for edge_id, vertex_sequence in graph.nu.items():
            predicate_name = graph.rel.get(edge_id, edge_id)
            
            # Find predicate position from layout
            pred_position = self._find_predicate_position(edge_id, layout_result)
            if not pred_position:
                continue
            
            # FIXED: Calculate predicate text bounds
            pred_bounds = self._calculate_predicate_bounds(predicate_name, pred_position)
            
            # FIXED: Ensure predicate stays within cut boundaries if inside a cut
            adjusted_position = self._ensure_predicate_within_area(edge_id, pred_bounds, graph, layout_result)
            
            # Render predicate name at adjusted position
            canvas.draw_text(
                predicate_name,
                adjusted_position,
                {
                    'color': self.conv.text_color,
                    'font_size': 12,
                    'bold': False
                }
            )
            
            # For multi-place predicates, add argument order labels
            if len(vertex_sequence) > 1:
                self._render_argument_order_labels(
                    canvas, pred_position, vertex_sequence, graph, layout_result
                )
            
            # Draw hooks connecting to identity lines
            self._render_predicate_hooks(
                canvas, pred_position, vertex_sequence, graph, layout_result
            )
    
    def _render_identity_spots_and_constants(self, canvas: PySide6Canvas,
                                           graph: RelationalGraphWithCuts,
                                           layout_result: LayoutResult) -> None:
        """
        Render identity spots and constant names.
        
        When a vertex is labeled with a constant name, display the name near
        the vertex spot or use the name in place of the spot for direct representation.
        """
        for vertex_id, vertex in graph._vertex_map.items():
            if vertex_id not in layout_result.primitives:
                continue
                
            vertex_primitive = layout_result.primitives[vertex_id]
            vertex_pos = vertex_primitive.position
            
            # Draw identity spot (small filled circle)
            canvas.draw_circle(
                vertex_pos,
                self.conv.identity_spot_radius,
                {
                    'color': self.conv.line_color,
                    'fill_color': self.conv.line_color
                }
            )
            
            # Draw constant name if present
            if vertex.label:
                # Position label below the spot to avoid line conflicts
                label_pos = (vertex_pos[0], vertex_pos[1] + 20)
                canvas.draw_text(
                    f'"{vertex.label}"',
                    label_pos,
                    {
                        'color': self.conv.text_color,
                        'font_size': 10,
                        'bold': False
                    }
                )
    
    def _build_cut_hierarchy(self, graph: RelationalGraphWithCuts) -> Dict[str, List[str]]:
        """Build hierarchical structure of cuts for proper nesting."""
        hierarchy = {}
        
        # Build parent -> children mapping
        for cut in graph.Cut:
            parent_area = self._find_cut_parent_area(cut.id, graph)
            if parent_area not in hierarchy:
                hierarchy[parent_area] = []
            hierarchy[parent_area].append(cut.id)
        
        return hierarchy
    
    def _find_cut_parent_area(self, cut_id: str, graph: RelationalGraphWithCuts) -> str:
        """Find the parent area that contains this cut."""
        for area_id, contents in graph.area.items():
            if cut_id in contents:
                return area_id
        return graph.sheet  # Default to sheet level
    
    def _find_vertex_predicates(self, vertex_id: str, graph: RelationalGraphWithCuts,
                               layout_result: LayoutResult) -> List[Dict]:
        """Find all predicates connected to a vertex with their positions."""
        connected = []
        
        for edge_id, vertex_sequence in graph.nu.items():
            if vertex_id in vertex_sequence:
                predicate_name = graph.rel.get(edge_id, edge_id)
                pred_position = self._find_predicate_position(edge_id, layout_result)
                
                if pred_position:
                    connected.append({
                        'edge_id': edge_id,
                        'name': predicate_name,
                        'position': pred_position,
                        'vertex_sequence': vertex_sequence,
                        'argument_index': vertex_sequence.index(vertex_id)
                    })
        
        return connected
    
    def _find_predicate_position(self, edge_id: str, layout_result: LayoutResult) -> Optional[Tuple[float, float]]:
        """Find predicate position from layout result."""
        # Look for predicate node created by Graphviz
        pred_node_id = f"pred_{edge_id}"
        if pred_node_id in layout_result.primitives:
            return layout_result.primitives[pred_node_id].position
        
        # Fallback: look for edge primitive
        if edge_id in layout_result.primitives:
            return layout_result.primitives[edge_id].position
        
        return None
    
    def _calculate_predicate_bounds(self, predicate_name: str, position: Tuple[float, float], 
                                   font_size: int = 12) -> Tuple[float, float, float, float]:
        """Calculate the bounding box of predicate text."""
        # Estimate text dimensions (this should use actual font metrics)
        char_width = font_size * 0.6  # Approximate character width
        char_height = font_size * 1.2  # Approximate character height
        
        text_width = len(predicate_name) * char_width
        text_height = char_height
        
        # Calculate bounds (x1, y1, x2, y2)
        x1 = position[0] - text_width / 2
        y1 = position[1] - text_height / 2
        x2 = position[0] + text_width / 2
        y2 = position[1] + text_height / 2
        
        return (x1, y1, x2, y2)
    
    def _ensure_predicate_within_area(self, edge_id: str, predicate_bounds: Tuple[float, float, float, float],
                                     graph: RelationalGraphWithCuts, layout_result: LayoutResult,
                                     margin: float = 5.0) -> Tuple[float, float]:
        """Ensure predicate stays within its designated area (cut or sheet) boundaries."""
        pred_x1, pred_y1, pred_x2, pred_y2 = predicate_bounds
        
        # Find which area this predicate belongs to
        predicate_area = graph.get_area(edge_id)
        
        # Get area bounds
        if predicate_area != graph.sheet and predicate_area in layout_result.primitives:
            # Predicate is inside a cut - enforce cut boundaries
            cut_primitive = layout_result.primitives[predicate_area]
            cut_bounds = cut_primitive.bounds
            
            # Adjust position to stay within cut boundaries
            return self._adjust_position_within_bounds(predicate_bounds, cut_bounds, margin)
        else:
            # Predicate is on sheet - use original position (no cut constraints)
            return ((pred_x1 + pred_x2) / 2, (pred_y1 + pred_y2) / 2)
    
    def _adjust_position_within_bounds(self, item_bounds: Tuple[float, float, float, float],
                                      container_bounds: Tuple[float, float, float, float],
                                      margin: float) -> Tuple[float, float]:
        """Adjust item position to ensure it stays within container boundaries."""
        item_x1, item_y1, item_x2, item_y2 = item_bounds
        container_x1, container_y1, container_x2, container_y2 = container_bounds
        
        # Calculate current center
        center_x = (item_x1 + item_x2) / 2
        center_y = (item_y1 + item_y2) / 2
        
        # Calculate item dimensions
        item_width = item_x2 - item_x1
        item_height = item_y2 - item_y1
        
        # Adjust if item extends beyond container boundaries
        if item_x1 < container_x1 + margin:
            center_x = container_x1 + margin + item_width / 2
        elif item_x2 > container_x2 - margin:
            center_x = container_x2 - margin - item_width / 2
            
        if item_y1 < container_y1 + margin:
            center_y = container_y1 + margin + item_height / 2
        elif item_y2 > container_y2 - margin:
            center_y = container_y2 - margin - item_height / 2
        
        return (center_x, center_y)
    
    def _calculate_line_connection_point(self, predicate_bounds: Tuple[float, float, float, float],
                                        vertex_position: Tuple[float, float]) -> Tuple[float, float]:
        """Calculate where a line should connect to the predicate boundary."""
        pred_x1, pred_y1, pred_x2, pred_y2 = predicate_bounds
        vertex_x, vertex_y = vertex_position
        
        # Calculate predicate center
        pred_center_x = (pred_x1 + pred_x2) / 2
        pred_center_y = (pred_y1 + pred_y2) / 2
        
        # Calculate direction from vertex to predicate center
        dx = pred_center_x - vertex_x
        dy = pred_center_y - vertex_y
        
        # Find intersection with predicate boundary
        if abs(dx) > abs(dy):
            # Horizontal approach - connect to left or right edge
            if dx > 0:
                return (pred_x1, pred_center_y)  # Left edge
            else:
                return (pred_x2, pred_center_y)  # Right edge
        else:
            # Vertical approach - connect to top or bottom edge
            if dy > 0:
                return (pred_center_x, pred_y1)  # Top edge
            else:
                return (pred_center_x, pred_y2)  # Bottom edge
    
    def _draw_identity_line_to_predicate(self, canvas: PySide6Canvas, vertex_pos: Tuple[float, float],
                                       pred_info: Dict, line_index: int, total_lines: int) -> None:
        """Draw a heavy line of identity from vertex to predicate.
        
        CRITICAL: Line must pass through cuts to reach predicates inside cuts,
        as per Dau's formalism where lines of identity can cross cut boundaries.
        """
        pred_pos = pred_info['position']
        
        # Calculate line direction
        dx = pred_pos[0] - vertex_pos[0]
        dy = pred_pos[1] - vertex_pos[1]
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance == 0:
            return  # Skip zero-length lines
        
        # Apply angular separation for multiple lines
        if total_lines > 1:
            base_angle = math.atan2(dy, dx)
            separation = math.pi / 8  # 22.5 degrees
            angle_offset = (line_index - (total_lines - 1) / 2) * separation
            final_angle = base_angle + angle_offset
            
            # FIXED: Line extends ALL THE WAY to predicate (passes through cuts)
            line_length = distance * 0.9  # Almost to predicate (leave small gap for hook)
            end_pos = (
                vertex_pos[0] + math.cos(final_angle) * line_length,
                vertex_pos[1] + math.sin(final_angle) * line_length
            )
        else:
            # FIXED: Single line extends ALL THE WAY to predicate (passes through cuts)
            line_length = distance * 0.9  # Almost to predicate (leave small gap for hook)
            end_pos = (
                vertex_pos[0] + dx * 0.9,
                vertex_pos[1] + dy * 0.9
            )
        
        # FIXED: Calculate proper line endpoint at predicate periphery
        predicate_name = pred_info['name']
        pred_bounds = self._calculate_predicate_bounds(predicate_name, pred_info['position'])
        line_endpoint = self._calculate_line_connection_point(pred_bounds, vertex_pos)
        
        # Draw heavy line of identity to predicate periphery (not center)
        canvas.draw_line(
            vertex_pos, line_endpoint,
            {
                'color': self.conv.line_color,
                'width': self.conv.identity_line_width  # FIXED: API mismatch - Now 4.0 (thicker)
            }
        )
    
    def _render_argument_order_labels(self, canvas: PySide6Canvas, pred_position: Tuple[float, float],
                                    vertex_sequence: List[str], graph: RelationalGraphWithCuts,
                                    layout_result: LayoutResult) -> None:
        """Render argument order numbers for multi-place predicates."""
        for i, vertex_id in enumerate(vertex_sequence):
            if vertex_id in layout_result.primitives:
                vertex_pos = layout_result.primitives[vertex_id].position
                
                # Calculate position for argument label (midpoint of connection)
                mid_x = (pred_position[0] + vertex_pos[0]) / 2
                mid_y = (pred_position[1] + vertex_pos[1]) / 2
                
                # Offset slightly to avoid line overlap
                label_pos = (mid_x + self.conv.argument_label_offset, 
                           mid_y - self.conv.argument_label_offset)
                
                # Draw argument number
                canvas.draw_text(
                    str(i + 1),  # 1-indexed argument numbers
                    label_pos,
                    {
                        'color': self.conv.text_color,
                        'font_size': 8,
                        'bold': True
                    }
                )
    
    def _render_predicate_hooks(self, canvas: PySide6Canvas, pred_position: Tuple[float, float],
                              vertex_sequence: List[str], graph: RelationalGraphWithCuts,
                              layout_result: LayoutResult) -> None:
        """Handle predicate attachment to identity lines.
        
        NOTE: In Dau's formalism, hooks are conceptual attachment points, not visible lines.
        The attachment is invisible but functional - predicates and lines move together.
        This method is kept for future interactive functionality but renders nothing visually.
        """
        # Hooks are invisible attachment points in Dau's formalism
        # The conceptual attachment is handled by the layout engine positioning
        # No visual rendering needed - predicates are positioned near line endpoints
        pass
    
    def _calculate_centering_offset(self, canvas: PySide6Canvas, layout_result: LayoutResult) -> Tuple[float, float]:
        """Calculate offset to center the diagram in the viewport."""
        if not layout_result.primitives:
            return (0, 0)
        
        # Find bounding box of all elements
        all_bounds = [p.bounds for p in layout_result.primitives.values() if hasattr(p, 'bounds')]
        if not all_bounds:
            return (0, 0)
        
        min_x = min(bounds[0] for bounds in all_bounds)
        min_y = min(bounds[1] for bounds in all_bounds)
        max_x = max(bounds[2] for bounds in all_bounds)
        max_y = max(bounds[3] for bounds in all_bounds)
        
        # Calculate diagram dimensions
        diagram_width = max_x - min_x
        diagram_height = max_y - min_y
        
        # Calculate canvas dimensions (assume standard size)
        canvas_width = canvas.width
        canvas_height = canvas.height
        
        # Calculate centering offset with title space
        title_space = 80  # Space for title and metadata
        offset_x = (canvas_width - diagram_width) / 2 - min_x
        offset_y = (canvas_height - diagram_height) / 2 - min_y + title_space
        
        return (offset_x, offset_y)
    
    def _apply_centering_offset(self, layout_result: LayoutResult, offset_x: float, offset_y: float) -> LayoutResult:
        """Apply centering offset to all primitives in the layout."""
        centered_primitives = {}
        
        for prim_id, primitive in layout_result.primitives.items():
            # Create new primitive with offset position and bounds
            new_position = (primitive.position[0] + offset_x, primitive.position[1] + offset_y)
            new_bounds = (
                primitive.bounds[0] + offset_x,
                primitive.bounds[1] + offset_y,
                primitive.bounds[2] + offset_x,
                primitive.bounds[3] + offset_y
            )
            
            centered_primitive = SpatialPrimitive(
                element_id=primitive.element_id,
                element_type=primitive.element_type,
                position=new_position,
                bounds=new_bounds,
                z_index=primitive.z_index
            )
            centered_primitives[prim_id] = centered_primitive
        
        return LayoutResult(
            primitives=centered_primitives,
            canvas_bounds=layout_result.canvas_bounds,
            containment_hierarchy=layout_result.containment_hierarchy
        )
    
    def _render_diagram_title(self, canvas: PySide6Canvas, graph: RelationalGraphWithCuts) -> None:
        """Add diagram title and structural information."""
        canvas.draw_text(
            "Existential Graph (Peirce/Dau Formalism)",
            (10, 20),
            {
                'color': self.conv.text_color,
                'font_size': 14,
                'bold': True
            }
        )
        
        # Structural summary
        vertices = len(graph._vertex_map)
        predicates = len(graph.nu)
        cuts = len(graph.Cut)
        
        canvas.draw_text(
            f"Structure: {vertices} vertices, {predicates} predicates, {cuts} cuts",
            (10, 40),
            {
                'color': (100, 100, 100),
                'font_size': 10
            }
        )


# Factory function
def create_dau_diagram_renderer(conventions: VisualConvention = None) -> DiagramRendererDau:
    """Create a DiagramRenderer with Peirce/Dau conventions."""
    return DiagramRendererDau(conventions)


if __name__ == "__main__":
    # Test the DiagramRenderer with proper architecture
    from egif_parser_dau import parse_egif
    from graphviz_layout_engine_v2 import create_graphviz_layout
    from pyside6_canvas import create_qt_canvas
    
    print("🎨 Testing DiagramRenderer (Peirce/Dau Formalism)")
    
    # Test case with clear EG structure
    test_egif = '(Human "Socrates") ~[ (Mortal "Socrates") ]'
    print(f"📝 Test EGIF: {test_egif}")
    
    try:
        # Step 1: Parse EGIF to EGI
        graph = parse_egif(test_egif)
        print(f"✅ EGI parsed: {len(graph._vertex_map)} vertices, {len(graph.nu)} predicates, {len(graph.Cut)} cuts")
        
        # Step 2: Generate layout coordinates with Graphviz
        layout_result = create_graphviz_layout(graph)
        print(f"✅ Layout generated: {len(layout_result.primitives)} spatial primitives")
        
        # Step 3: Create canvas and DiagramRenderer
        canvas = create_qt_canvas(800, 600, "DiagramRenderer Test - Peirce/Dau Formalism")
        renderer = create_dau_diagram_renderer()
        
        # Step 4: Render proper EG diagram
        renderer.render_diagram(canvas, graph, layout_result)
        print("✅ EG diagram rendered with Peirce/Dau conventions")
        
        # Step 5: Display result
        canvas.show()
        print("🖼️  Window displayed - should show proper EG with:")
        print("   • Heavy lines of identity connecting vertices to predicates")
        print("   • Fine-drawn cut oval containing negated content")
        print("   • Identity spots at vertex centers")
        print("   • Proper predicate attachment with hooks")
        print("   • Constant labels positioned correctly")
        
        canvas.app.exec()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
