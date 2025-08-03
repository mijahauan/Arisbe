"""
Clean Diagram Renderer (Layer 3) - Pure Visual Presentation
Takes spatial primitives from Layout Engine and renders complete EG diagrams.

This layer handles only visual drawing - no spatial calculations or logical decisions.
Follows Dau's visual conventions for Existential Graphs.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Protocol
from layout_engine_clean import SpatialPrimitive, LayoutResult, Coordinate
from egi_core_dau import RelationalGraphWithCuts, ElementID
from canvas_backend import DrawingStyle


# Canvas abstraction protocol
class CanvasProtocol(Protocol):
    """Protocol for canvas backends (Tkinter, Pygame, etc.)"""
    
    def draw_line(self, start: Coordinate, end: Coordinate, width: float, color: str) -> None:
        """Draw a line from start to end."""
        ...
    
    def draw_circle(self, center: Coordinate, radius: float, fill_color: str, outline_color: str, outline_width: float) -> None:
        """Draw a circle."""
        ...
    
    def draw_curve(self, points: List[Coordinate], width: float, color: str, fill: bool = False) -> None:
        """Draw a curve through points."""
        ...
    
    def draw_text(self, position: Coordinate, text: str, font_size: int, color: str) -> None:
        """Draw text at position."""
        ...
    
    def clear(self) -> None:
        """Clear the canvas."""
        ...


@dataclass(frozen=True)
class RenderingTheme:
    """Visual theme for EG diagram rendering following Dau's conventions."""
    
    # Dau's visual conventions
    vertex_color: str = "black"
    vertex_radius: float = 6.0
    
    # Heavy lines for lines of identity
    identity_line_width: float = 3.0
    identity_line_color: str = "black"
    
    # Fine lines for cuts
    cut_line_width: float = 1.0
    cut_line_color: str = "black"
    cut_fill_color: str = "transparent"
    
    # Predicate text and hooks
    predicate_text_size: int = 12
    predicate_text_color: str = "black"
    hook_line_width: float = 1.0
    hook_line_color: str = "black"
    
    # Argument order labels (for multi-ary predicates)
    argument_label_size: int = 10
    argument_label_color: str = "blue"
    
    # Background
    background_color: str = "white"


class CleanDiagramRenderer:
    """
    Pure Diagram Renderer - converts spatial primitives to visual elements.
    
    Key Principles:
    1. Takes complete spatial primitives from Layout Engine
    2. No spatial calculations - only visual drawing
    3. Follows Dau's visual conventions strictly
    4. Supports lines of identity crossing cut boundaries
    5. Renders proper hooks and argument ordering
    """
    
    def __init__(self, canvas: CanvasProtocol, theme: Optional[RenderingTheme] = None):
        self.canvas = canvas
        self.theme = theme or RenderingTheme()
    
    def _hex_to_rgb(self, color: str) -> Tuple[int, int, int]:
        """Convert color string (hex or name) to RGB tuple."""
        # Handle common color names
        color_map = {
            'black': (0, 0, 0),
            'white': (255, 255, 255),
            'red': (255, 0, 0),
            'green': (0, 255, 0),
            'blue': (0, 0, 255),
            'gray': (128, 128, 128),
            'grey': (128, 128, 128)
        }
        
        if color.lower() in color_map:
            return color_map[color.lower()]
        
        # Handle hex colors
        if color.startswith('#'):
            color = color[1:]
        
        if len(color) == 6:
            return tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        
        # Fallback to black
        return (0, 0, 0)
    
    def render_diagram(self, layout_result: LayoutResult, graph: RelationalGraphWithCuts) -> None:
        """
        Main entry point: render complete EG diagram from spatial primitives.
        
        Rendering order (Z-index):
        1. Cuts (background, z=0)
        2. Lines of identity (connecting vertices to predicates, z=1)
        3. Vertices (heavy spots, z=1) 
        4. Predicates with hooks (foreground, z=2)
        """
        self.canvas.clear()
        
        # Sort primitives by z-index for proper layering
        sorted_primitives = sorted(
            layout_result.primitives.values(),
            key=lambda p: p.z_index
        )
        
        # Render in z-order
        for primitive in sorted_primitives:
            if primitive.element_type == 'cut':
                self._render_cut(primitive)
            elif primitive.element_type == 'vertex':
                self._render_vertex(primitive, graph)
            elif primitive.element_type == 'edge':
                self._render_edge(primitive, graph, layout_result.primitives)
        
        # Render lines of identity (after all elements are positioned)
        self._render_lines_of_identity(layout_result, graph)
    
    def _render_cut(self, cut_primitive: SpatialPrimitive) -> None:
        """Render cut as fine-drawn closed curve (Dau's convention)."""
        if not cut_primitive.curve_points:
            # Fallback: render as rectangle
            x1, y1, x2, y2 = cut_primitive.bounds
            points = [(x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)]
        else:
            points = cut_primitive.curve_points
        
        from canvas_backend import DrawingStyle
        style = DrawingStyle(
            color=self._hex_to_rgb(self.theme.cut_line_color),
            line_width=self.theme.cut_line_width,
            fill_color=None
        )
        self.canvas.draw_curve(points=points, style=style, closed=True)
    
    def _render_vertex(self, vertex_primitive: SpatialPrimitive, graph: RelationalGraphWithCuts) -> None:
        """Render vertex as heavy spot (Dau's convention)."""
        vertex = graph.get_vertex(vertex_primitive.element_id)
        
        # Draw heavy spot
        from canvas_backend import DrawingStyle
        style = DrawingStyle(
            color=self._hex_to_rgb(self.theme.vertex_color),
            line_width=1.0,
            fill_color=self._hex_to_rgb(self.theme.vertex_color)
        )
        self.canvas.draw_circle(
            center=vertex_primitive.position,
            radius=self.theme.vertex_radius,
            style=style
        )
        
        # If vertex has a constant label, draw it
        if vertex.label and not vertex.is_generic:
            label_x, label_y = vertex_primitive.position
            text_style = DrawingStyle(
                color=self._hex_to_rgb(self.theme.predicate_text_color),
                font_size=self.theme.predicate_text_size,
                font_family="Arial"
            )
            self.canvas.draw_text(
                position=(label_x, label_y - 20),
                text=vertex.label,
                style=text_style
            )
    
    def _render_edge(self, edge_primitive: SpatialPrimitive, graph: RelationalGraphWithCuts,
                    all_primitives: Dict[ElementID, SpatialPrimitive]) -> None:
        """Render edge as predicate with hooks to incident vertices."""
        relation_name = graph.get_relation_name(edge_primitive.element_id)
        vertex_sequence = graph.nu.get(edge_primitive.element_id, ())
        
        # Draw predicate text
        text_style = DrawingStyle(
            color=self._hex_to_rgb(self.theme.predicate_text_color),
            font_size=self.theme.predicate_text_size,
            font_family="Arial"
        )
        self.canvas.draw_text(
            position=edge_primitive.position,
            text=relation_name,
            style=text_style
        )
        
        # Draw hooks to incident vertices
        if edge_primitive.attachment_points:
            for i, (vertex_key, vertex_pos) in enumerate(edge_primitive.attachment_points.items()):
                # Draw hook line from predicate to vertex
                hook_style = DrawingStyle(
                    color=self._hex_to_rgb(self.theme.hook_line_color),
                    line_width=self.theme.hook_line_width
                )
                self.canvas.draw_line(
                    start=edge_primitive.position,
                    end=vertex_pos,
                    style=hook_style
                )
                
                # For multi-ary predicates, draw argument order labels
                if len(edge_primitive.attachment_points) > 1:
                    # Calculate label position along the hook
                    pred_x, pred_y = edge_primitive.position
                    vert_x, vert_y = vertex_pos
                    label_x = pred_x + 0.3 * (vert_x - pred_x)
                    label_y = pred_y + 0.3 * (vert_y - pred_y)
                    
                    self.canvas.draw_text(
                        position=(label_x, label_y),
                        text=str(i + 1),  # 1-based numbering
                        font_size=self.theme.argument_label_size,
                        color=self.theme.argument_label_color
                    )
    
    def _render_lines_of_identity(self, layout_result: LayoutResult, graph: RelationalGraphWithCuts) -> None:
        """
        Render lines of identity (heavy lines) that can cross cut boundaries.
        
        This is the key feature that allows vertices at sheet level to connect
        to predicates inside cuts, following Dau's conventions.
        """
        # For each edge, draw identity lines from vertices to the edge
        for edge_id, edge_primitive in layout_result.primitives.items():
            if edge_primitive.element_type != 'edge':
                continue
            
            vertex_sequence = graph.nu.get(edge_id, ())
            
            for vertex_id in vertex_sequence:
                if vertex_id in layout_result.primitives:
                    vertex_primitive = layout_result.primitives[vertex_id]
                    
                    # Draw heavy line of identity from vertex to predicate
                    # This line can cross cut boundaries
                    identity_style = DrawingStyle(
                        color=self._hex_to_rgb(self.theme.identity_line_color),
                        line_width=self.theme.identity_line_width
                    )
                    self.canvas.draw_line(
                        start=vertex_primitive.position,
                        end=edge_primitive.position,
                        style=identity_style
                    )
    
    def _calculate_hook_endpoint(self, predicate_pos: Coordinate, vertex_pos: Coordinate) -> Coordinate:
        """Calculate where hook line should end (near predicate edge, not center)."""
        pred_x, pred_y = predicate_pos
        vert_x, vert_y = vertex_pos
        
        # Calculate direction vector
        dx = pred_x - vert_x
        dy = pred_y - vert_y
        
        # Normalize and scale to predicate boundary
        import math
        length = math.sqrt(dx*dx + dy*dy)
        if length == 0:
            return predicate_pos
        
        # Hook ends at predicate boundary (approximately)
        hook_length = 25  # Distance from predicate center to hook endpoint
        end_x = pred_x - (dx / length) * hook_length
        end_y = pred_y - (dy / length) * hook_length
        
        return (end_x, end_y)


# Tkinter Canvas Implementation
class TkinterCanvas:
    """Tkinter implementation of CanvasProtocol."""
    
    def __init__(self, tk_canvas):
        self.tk_canvas = tk_canvas
    
    def draw_line(self, start: Coordinate, end: Coordinate, width: float, color: str) -> None:
        """Draw a line from start to end."""
        self.tk_canvas.create_line(
            start[0], start[1], end[0], end[1],
            width=width, fill=color
        )
    
    def draw_circle(self, center: Coordinate, radius: float, fill_color: str, outline_color: str, outline_width: float) -> None:
        """Draw a circle."""
        x, y = center
        self.tk_canvas.create_oval(
            x - radius, y - radius, x + radius, y + radius,
            fill=fill_color, outline=outline_color, width=outline_width
        )
    
    def draw_curve(self, points: List[Coordinate], width: float, color: str, fill: bool = False) -> None:
        """Draw a curve through points."""
        if len(points) < 2:
            return
        
        # Flatten points for Tkinter
        flat_points = []
        for x, y in points:
            flat_points.extend([x, y])
        
        if fill:
            self.tk_canvas.create_polygon(flat_points, outline=color, width=width, fill="")
        else:
            self.tk_canvas.create_line(flat_points, width=width, fill=color)
    
    def draw_text(self, position: Coordinate, text: str, font_size: int, color: str) -> None:
        """Draw text at position."""
        self.tk_canvas.create_text(
            position[0], position[1],
            text=text, font=("Arial", font_size), fill=color
        )
    
    def clear(self) -> None:
        """Clear the canvas."""
        self.tk_canvas.delete("all")
