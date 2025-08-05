#!/usr/bin/env python3
"""
Dau's Existential Graph Renderer

This module implements a proper EG renderer that follows Peirce's visual conventions
as formalized by Frithjof Dau. It produces diagrams that are mathematically correct
representations of Existential Graphs.

Key Visual Elements per Dau's Formalism:
1. Heavy lines of identity - Thick lines extending from vertex spots to predicates
2. Identity spots - Small filled circles where lines intersect or terminate
3. Predicate attachment - Predicates attach to line ends via hooks
4. Cut ovals - Fine-drawn closed curves (ovals) for negation
5. Area containment - Visual nesting reflects logical containment
6. Proper spacing - Elements don't overlap inappropriately
"""

import math
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from egi_core_dau import RelationalGraphWithCuts, ElementID
from layout_engine_clean import LayoutResult, SpatialPrimitive
from pyside6_canvas import PySide6Canvas


@dataclass
class EGVisualElement:
    """Visual element in an EG diagram with Dau's conventions."""
    element_type: str  # 'identity_line', 'identity_spot', 'predicate', 'cut_oval'
    position: Tuple[float, float]
    size: Tuple[float, float]
    style: Dict[str, any]
    connections: List[str] = None  # Connected element IDs


class DauEGRenderer:
    """
    Proper EG renderer implementing Dau's formalism.
    
    This renderer takes EGI structure and layout coordinates to produce
    diagrams that correctly represent Existential Graphs according to
    Peirce's conventions as formalized by Dau.
    """
    
    def __init__(self):
        # Visual parameters per Dau's conventions
        self.identity_line_width = 3.0      # Heavy lines of identity
        self.identity_spot_radius = 3.0     # Identity spots
        self.cut_line_width = 1.5          # Fine-drawn cut ovals
        self.predicate_hook_length = 8.0   # Predicate attachment hooks
        self.minimum_spacing = 10.0        # Minimum element separation
        
        # Colors per EG conventions
        self.identity_color = (0, 0, 0)     # Black for identity elements
        self.cut_color = (0, 0, 0)          # Black for cuts
        self.predicate_color = (0, 0, 0)    # Black for predicates
        self.background_color = (255, 255, 255)  # White background
    
    def render_eg_diagram(self, canvas: PySide6Canvas, graph: RelationalGraphWithCuts, 
                         layout_result: LayoutResult) -> None:
        """
        Render a complete EG diagram following Dau's formalism.
        
        Args:
            canvas: Drawing canvas
            graph: EGI structure (logical truth)
            layout_result: Spatial coordinates from layout engine
        """
        canvas.clear()
        
        # Step 1: Analyze EGI structure to determine visual elements
        visual_elements = self._analyze_egi_structure(graph, layout_result)
        
        # Step 2: Render in proper layering order (background to foreground)
        self._render_cut_ovals(canvas, visual_elements)
        self._render_identity_lines(canvas, visual_elements)
        self._render_predicates_with_hooks(canvas, visual_elements)
        self._render_identity_spots(canvas, visual_elements)
        
        # Step 3: Add diagram title and metadata
        self._render_diagram_metadata(canvas, graph)
    
    def _analyze_egi_structure(self, graph: RelationalGraphWithCuts, 
                              layout_result: LayoutResult) -> Dict[str, EGVisualElement]:
        """
        Analyze EGI structure to determine what visual elements to draw.
        
        This is where we translate logical EGI structure into Dau's visual conventions.
        """
        visual_elements = {}
        
        # 1. Analyze vertices and their connections to determine identity lines
        for vertex_id, vertex in graph._vertex_map.items():
            if vertex_id in layout_result.primitives:
                vertex_primitive = layout_result.primitives[vertex_id]
                
                # Find all predicates connected to this vertex
                connected_predicates = self._find_connected_predicates(vertex_id, graph, layout_result)
                
                if connected_predicates:
                    # Create identity lines from vertex to each predicate
                    for i, pred_info in enumerate(connected_predicates):
                        line_id = f"identity_line_{vertex_id}_{pred_info['id']}"
                        visual_elements[line_id] = self._create_identity_line(
                            vertex_primitive.position, pred_info['position'], i, len(connected_predicates)
                        )
                
                # Create identity spot at vertex center
                spot_id = f"identity_spot_{vertex_id}"
                visual_elements[spot_id] = EGVisualElement(
                    element_type='identity_spot',
                    position=vertex_primitive.position,
                    size=(self.identity_spot_radius * 2, self.identity_spot_radius * 2),
                    style={'color': self.identity_color, 'fill': True}
                )
                
                # Add vertex label if present
                if vertex.label:
                    label_id = f"vertex_label_{vertex_id}"
                    label_pos = (vertex_primitive.position[0], vertex_primitive.position[1] + 20)
                    visual_elements[label_id] = EGVisualElement(
                        element_type='vertex_label',
                        position=label_pos,
                        size=(len(vertex.label) * 8, 12),
                        style={'text': f'"{vertex.label}"', 'color': self.identity_color}
                    )
        
        # 2. Analyze cuts to determine oval boundaries
        for cut in graph.Cut:
            if cut.id in layout_result.primitives:
                cut_primitive = layout_result.primitives[cut.id]
                
                # Create cut oval
                oval_id = f"cut_oval_{cut.id}"
                visual_elements[oval_id] = EGVisualElement(
                    element_type='cut_oval',
                    position=cut_primitive.position,
                    size=(cut_primitive.bounds[2] - cut_primitive.bounds[0],
                          cut_primitive.bounds[3] - cut_primitive.bounds[1]),
                    style={'color': self.cut_color, 'line_width': self.cut_line_width, 'fill': False}
                )
        
        # 3. Analyze predicates for proper attachment
        for edge_id, vertex_sequence in graph.nu.items():
            predicate_name = graph.rel.get(edge_id, edge_id)
            
            if len(vertex_sequence) == 1:
                # Monadic predicate - attach to identity line end
                vertex_id = vertex_sequence[0]
                if vertex_id in layout_result.primitives:
                    pred_id = f"predicate_{edge_id}"
                    visual_elements[pred_id] = self._create_predicate_attachment(
                        edge_id, predicate_name, vertex_id, graph, layout_result
                    )
            
            elif len(vertex_sequence) > 1:
                # Polyadic predicate - create relation structure
                pred_id = f"relation_{edge_id}"
                visual_elements[pred_id] = self._create_relation_structure(
                    edge_id, predicate_name, vertex_sequence, graph, layout_result
                )
        
        return visual_elements
    
    def _find_connected_predicates(self, vertex_id: str, graph: RelationalGraphWithCuts, 
                                  layout_result: LayoutResult) -> List[Dict]:
        """Find all predicates connected to a vertex."""
        connected = []
        
        for edge_id, vertex_sequence in graph.nu.items():
            if vertex_id in vertex_sequence:
                predicate_name = graph.rel.get(edge_id, edge_id)
                
                # Calculate predicate position (for monadic predicates)
                if len(vertex_sequence) == 1 and edge_id in layout_result.primitives:
                    pred_primitive = layout_result.primitives[edge_id]
                    connected.append({
                        'id': edge_id,
                        'name': predicate_name,
                        'position': pred_primitive.position,
                        'arity': len(vertex_sequence)
                    })
        
        return connected
    
    def _create_identity_line(self, vertex_pos: Tuple[float, float], 
                             predicate_pos: Tuple[float, float], 
                             line_index: int, total_lines: int) -> EGVisualElement:
        """Create a heavy line of identity from vertex to predicate."""
        
        # Calculate line direction and length
        dx = predicate_pos[0] - vertex_pos[0]
        dy = predicate_pos[1] - vertex_pos[1]
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance == 0:
            # Fallback for coincident points
            end_pos = (vertex_pos[0] + 30, vertex_pos[1])
        else:
            # Apply angular separation if multiple lines from same vertex
            if total_lines > 1:
                base_angle = math.atan2(dy, dx)
                separation = math.pi / 6  # 30 degrees
                angle_offset = (line_index - (total_lines - 1) / 2) * separation / max(1, total_lines - 1)
                final_angle = base_angle + angle_offset
                
                # Line extends most of the way to predicate
                line_length = distance * 0.8
                end_pos = (
                    vertex_pos[0] + math.cos(final_angle) * line_length,
                    vertex_pos[1] + math.sin(final_angle) * line_length
                )
            else:
                # Single line - extend most of the way to predicate
                line_length = distance * 0.8
                end_pos = (
                    vertex_pos[0] + dx * 0.8,
                    vertex_pos[1] + dy * 0.8
                )
        
        return EGVisualElement(
            element_type='identity_line',
            position=((vertex_pos[0] + end_pos[0]) / 2, (vertex_pos[1] + end_pos[1]) / 2),
            size=(abs(end_pos[0] - vertex_pos[0]), abs(end_pos[1] - vertex_pos[1])),
            style={
                'start': vertex_pos,
                'end': end_pos,
                'color': self.identity_color,
                'line_width': self.identity_line_width
            }
        )
    
    def _create_predicate_attachment(self, edge_id: str, predicate_name: str, 
                                   vertex_id: str, graph: RelationalGraphWithCuts,
                                   layout_result: LayoutResult) -> EGVisualElement:
        """Create predicate attachment at the end of an identity line."""
        
        if edge_id in layout_result.primitives:
            pred_primitive = layout_result.primitives[edge_id]
            
            return EGVisualElement(
                element_type='predicate',
                position=pred_primitive.position,
                size=(len(predicate_name) * 8 + 10, 20),
                style={
                    'text': predicate_name,
                    'color': self.predicate_color,
                    'hook_length': self.predicate_hook_length,
                    'attached_to': vertex_id
                }
            )
        
        # Fallback if no layout primitive found
        return EGVisualElement(
            element_type='predicate',
            position=(100, 100),
            size=(len(predicate_name) * 8 + 10, 20),
            style={'text': predicate_name, 'color': self.predicate_color}
        )
    
    def _create_relation_structure(self, edge_id: str, predicate_name: str,
                                  vertex_sequence: List[str], graph: RelationalGraphWithCuts,
                                  layout_result: LayoutResult) -> EGVisualElement:
        """Create visual structure for polyadic relations."""
        
        # For now, create a simple relation node
        # TODO: Implement proper polyadic relation rendering per Dau
        if edge_id in layout_result.primitives:
            rel_primitive = layout_result.primitives[edge_id]
            position = rel_primitive.position
        else:
            position = (200, 200)  # Fallback
        
        return EGVisualElement(
            element_type='relation',
            position=position,
            size=(len(predicate_name) * 8 + 20, 25),
            style={
                'text': predicate_name,
                'color': self.predicate_color,
                'arity': len(vertex_sequence),
                'vertices': vertex_sequence
            }
        )
    
    def _render_cut_ovals(self, canvas: PySide6Canvas, visual_elements: Dict[str, EGVisualElement]):
        """Render cut ovals as fine-drawn closed curves."""
        
        for element_id, element in visual_elements.items():
            if element.element_type == 'cut_oval':
                # Draw oval using canvas ellipse method
                x, y = element.position
                w, h = element.size
                
                canvas.draw_ellipse(
                    (x - w/2, y - h/2, x + w/2, y + h/2),
                    {
                        'color': element.style['color'],
                        'line_width': element.style['line_width'],
                        'fill_color': None  # No fill for cuts
                    }
                )
    
    def _render_identity_lines(self, canvas: PySide6Canvas, visual_elements: Dict[str, EGVisualElement]):
        """Render heavy lines of identity."""
        
        for element_id, element in visual_elements.items():
            if element.element_type == 'identity_line':
                start = element.style['start']
                end = element.style['end']
                
                canvas.draw_line(
                    start, end,
                    {
                        'color': element.style['color'],
                        'line_width': element.style['line_width']
                    }
                )
    
    def _render_predicates_with_hooks(self, canvas: PySide6Canvas, visual_elements: Dict[str, EGVisualElement]):
        """Render predicates with proper attachment hooks."""
        
        for element_id, element in visual_elements.items():
            if element.element_type in ['predicate', 'relation']:
                x, y = element.position
                text = element.style['text']
                
                # Draw predicate text
                canvas.draw_text(
                    text, (x, y),
                    {
                        'color': element.style['color'],
                        'font_size': 12,
                        'bold': False
                    }
                )
                
                # Draw attachment hook if specified
                if 'hook_length' in element.style:
                    hook_length = element.style['hook_length']
                    # Draw small hook line extending from predicate
                    canvas.draw_line(
                        (x - hook_length, y), (x, y),
                        {
                            'color': element.style['color'],
                            'line_width': 1.5
                        }
                    )
    
    def _render_identity_spots(self, canvas: PySide6Canvas, visual_elements: Dict[str, EGVisualElement]):
        """Render identity spots where lines intersect or terminate."""
        
        for element_id, element in visual_elements.items():
            if element.element_type == 'identity_spot':
                x, y = element.position
                radius = self.identity_spot_radius
                
                canvas.draw_circle(
                    (x, y), radius,
                    {
                        'color': element.style['color'],
                        'fill_color': element.style['color']  # Filled spots
                    }
                )
            
            elif element.element_type == 'vertex_label':
                x, y = element.position
                text = element.style['text']
                
                canvas.draw_text(
                    text, (x, y),
                    {
                        'color': element.style['color'],
                        'font_size': 10,
                        'bold': False
                    }
                )
    
    def _render_diagram_metadata(self, canvas: PySide6Canvas, graph: RelationalGraphWithCuts):
        """Add diagram title and metadata."""
        
        canvas.draw_text(
            "Existential Graph (Dau's Formalism)",
            (10, 20),
            {
                'color': (0, 0, 0),
                'font_size': 14,
                'bold': True
            }
        )
        
        # Add structure summary
        vertices = len(graph._vertex_map)
        edges = len(graph.nu)
        cuts = len(graph.Cut)
        
        canvas.draw_text(
            f"Structure: {vertices} vertices, {edges} predicates, {cuts} cuts",
            (10, 40),
            {
                'color': (100, 100, 100),
                'font_size': 10,
                'bold': False
            }
        )


# Factory function for easy use
def create_dau_eg_renderer() -> DauEGRenderer:
    """Create a Dau EG renderer with standard parameters."""
    return DauEGRenderer()


if __name__ == "__main__":
    # Test the Dau EG renderer
    from egif_parser_dau import parse_egif
    from graphviz_layout_engine_v2 import create_graphviz_layout
    from pyside6_canvas import create_qt_canvas
    
    print("🎨 Testing Dau EG Renderer")
    
    # Test case
    test_egif = '(Human "Socrates") ~[ (Mortal "Socrates") ]'
    
    try:
        # Parse and layout
        graph = parse_egif(test_egif)
        layout_result = create_graphviz_layout(graph)
        
        # Create canvas and renderer
        canvas = create_qt_canvas(800, 600, "Dau EG Renderer Test")
        renderer = create_dau_eg_renderer()
        
        # Render proper EG diagram
        renderer.render_eg_diagram(canvas, graph, layout_result)
        
        # Show result
        canvas.show()
        canvas.app.exec()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
