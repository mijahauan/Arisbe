"""
DEPRECATED: Use `src/diagram_renderer_dau.py` as the sole canonical renderer.

This module was an alternative visual-only renderer. To ensure a single
rendering pathway that enforces Dau-compliant visuals, strict containment,
and sibling separation using the canonical layout post-processing pipeline,
all tools and GUIs must use `DiagramRendererDau`.

This file remains temporarily for reference and will be removed after
downstream imports are updated.
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
    
    # Dau's visual conventions - ENHANCED for full compliance
    vertex_color: str = "black"
    vertex_radius: float = 3.5  # Prominent identity spots (slightly larger than before)
    
    # Heavy lines for lines of identity (Dau's key convention)
    identity_line_width: float = 4.0  # ENHANCED: Even more prominent heavy lines
    identity_line_color: str = "black"
    identity_line_style: str = "solid"  # Solid heavy lines
    
    # Fine lines for cuts (Dau's key convention)
    cut_line_width: float = 1.0  # MAINTAINED: Fine-drawn boundaries
    cut_line_color: str = "black"
    cut_fill_color: str = "transparent"  # No fill - just boundary
    cut_line_style: str = "solid"  # Fine solid lines
    
    # Predicate text and hooks
    predicate_text_size: int = 12
    predicate_text_color: str = "black"
    predicate_background_color: str = "white"  # Clear background for readability
    # NOTE: Hook lines removed - hooks are invisible positions per Dau formalism
    # Heavy identity lines connect directly to predicate boundary positions
    
    # Argument order labels (for multi-ary predicates)
    argument_label_size: int = 10
    argument_label_color: str = "blue"
    show_argument_numbers: bool = True  # Show numbered hooks for n-ary predicates
    
    # Spacing and margins (enhanced for visual clarity)
    minimum_element_spacing: float = 20.0  # Minimum distance between elements
    cut_padding: float = 15.0  # Padding inside cuts around contents
    predicate_margin: float = 8.0  # Margin around predicate text
    
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
            elif primitive.element_type == 'predicate':  
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
        # Per Dau: do not render a literal spot; the identity is a single heavy line.
        # Keep this function for potential selection overlay only.
        
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
        # NOTE: Hook lines removed per Dau formalism - EGI_DIAGRAM_CORRESPONDENCE.md
        # Heavy identity lines connect directly to predicate boundary positions
        # Connections are handled by _render_lines_of_identity method
        
        # Argument order labels are handled by annotation system when enabled
    
    def _render_lines_of_identity(self, layout_result: LayoutResult, graph: RelationalGraphWithCuts) -> None:
        """
        Render lines of identity as single continuous heavy lines per ligature (vertex-centric):
        - Degree 2: draw one line between two predicate periphery hooks.
        - Degree 1: draw line from predicate periphery to a free endpoint beyond the vertex position.
        - Degree >=3: draw branching lines from a junction (vertex position) to each hook.
        """
        identity_style = DrawingStyle(
            color=self._hex_to_rgb(self.theme.identity_line_color),
            line_width=self.theme.identity_line_width
        )

        # Build adjacency: vertex -> list of (edge_id, predicate_primitive)
        vertex_to_predicates: Dict[ElementID, List[SpatialPrimitive]] = {}
        for eid, prim in layout_result.primitives.items():
            if prim.element_type != 'edge':
                continue
            rel_vertices = graph.nu.get(eid, ())
            for vid in rel_vertices:
                if vid not in layout_result.primitives:
                    continue
                vertex_to_predicates.setdefault(vid, []).append(prim)

        for vid, preds in vertex_to_predicates.items():
            vprim = layout_result.primitives.get(vid)
            if not vprim or not preds:
                continue

            # Compute hook points on predicate peripheries
            hook_points: List[Tuple[float, float]] = []
            for pprim in preds:
                hook = self._predicate_periphery_point(pprim, vprim.position)
                hook_points.append(hook)

            deg = len(hook_points)
            if deg == 1:
                # Free endpoint: extend a bit past the vertex position away from predicate
                hx, hy = hook_points[0]
                vx, vy = vprim.position
                dx, dy = vx - hx, vy - hy
                mag = max((dx*dx + dy*dy) ** 0.5, 1e-6)
                ux, uy = dx / mag, dy / mag
                free_len = max(30.0, self.theme.identity_line_width * 6)
                free_pt = (vx + ux * free_len, vy + uy * free_len)
                self.canvas.draw_line(start=hook_points[0], end=free_pt, style=identity_style)
            elif deg == 2:
                # Single continuous line between two hooks
                self.canvas.draw_line(start=hook_points[0], end=hook_points[1], style=identity_style)
            else:
                # Branching: draw from junction near vertex position to each hook
                junction = vprim.position
                for hook in hook_points:
                    self.canvas.draw_line(start=junction, end=hook, style=identity_style)

    def _predicate_periphery_point(self, predicate_primitive: SpatialPrimitive, toward: Tuple[float, float]) -> Tuple[float, float]:
        """Compute the point on the predicate's rectangular bounds closest in the direction of 'toward'."""
        if predicate_primitive.bounds:
            x1, y1, x2, y2 = predicate_primitive.bounds
            cx = (x1 + x2) / 2.0
            cy = (y1 + y2) / 2.0
            tx, ty = toward
            dx, dy = tx - cx, ty - cy
            # Avoid division by zero
            if abs(dx) < 1e-6 and abs(dy) < 1e-6:
                return (cx, y1)  # arbitrary top
            # Compute intersection with rectangle periphery in direction (dx, dy)
            candidates: List[Tuple[float, float]] = []
            if abs(dx) > 1e-6:
                # Intersect with left (x1) and right (x2)
                t_left = (x1 - cx) / dx
                y_left = cy + t_left * dy
                if 0 <= t_left <= 1e6 and y1 <= y_left <= y2:
                    candidates.append((x1, y_left))
                t_right = (x2 - cx) / dx
                y_right = cy + t_right * dy
                if 0 <= t_right <= 1e6 and y1 <= y_right <= y2:
                    candidates.append((x2, y_right))
            if abs(dy) > 1e-6:
                # Intersect with top (y1) and bottom (y2)
                t_top = (y1 - cy) / dy
                x_top = cx + t_top * dx
                if 0 <= t_top <= 1e6 and x1 <= x_top <= x2:
                    candidates.append((x_top, y1))
                t_bottom = (y2 - cy) / dy
                x_bottom = cx + t_bottom * dx
                if 0 <= t_bottom <= 1e6 and x1 <= x_bottom <= x2:
                    candidates.append((x_bottom, y2))
            if candidates:
                # Choose candidate closest to 'toward'
                tx, ty = toward
                candidates.sort(key=lambda p: (p[0]-tx)**2 + (p[1]-ty)**2)
                return candidates[0]
        # Fallback: use predicate center
        return predicate_primitive.position
    
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
        
        # Hook ends at predicate boundary - reduced for proper connection
        # Smaller distance for accurate periphery connection
        hook_length = 15  # Reduced from 35 to 15 for proper predicate periphery
        end_x = pred_x - (dx / length) * hook_length
        end_y = pred_y - (dy / length) * hook_length
        
        return (end_x, end_y)


# Tkinter Canvas Implementation
class TkinterCanvas:
    """Tkinter implementation of CanvasProtocol."""
    
    def __init__(self, tk_canvas):
        self.tk_canvas = tk_canvas
    
    def draw_line(self, start: Coordinate, end: Coordinate, width: float = 2.0, color: str = "black", style=None) -> None:
        """Draw a line from start to end."""
        # Handle style parameter if provided
        if style is not None:
            color = f"#{style.color[0]:02x}{style.color[1]:02x}{style.color[2]:02x}" if style.color else color
            width = style.line_width if hasattr(style, 'line_width') else width
        
        self.tk_canvas.create_line(
            start[0], start[1], end[0], end[1],
            width=width, fill=color
        )
    
    def draw_circle(self, center: Coordinate, radius: float, fill_color: str = None, outline_color: str = None, outline_width: float = 1.0, style=None) -> None:
        """Draw a circle."""
        x, y = center
        
        # Handle style parameter if provided
        if style is not None:
            fill_color = f"#{style.fill_color[0]:02x}{style.fill_color[1]:02x}{style.fill_color[2]:02x}" if style.fill_color else fill_color
            outline_color = f"#{style.color[0]:02x}{style.color[1]:02x}{style.color[2]:02x}" if style.color else outline_color
            outline_width = style.line_width if hasattr(style, 'line_width') else outline_width
        
        self.tk_canvas.create_oval(
            x - radius, y - radius, x + radius, y + radius,
            fill=fill_color or "white", outline=outline_color or "black", width=outline_width
        )
    
    def draw_curve(self, points: List[Coordinate], width: float = 2.0, color: str = "black", fill: bool = False, style=None, closed: bool = False) -> None:
        """Draw a curve through points."""
        if len(points) < 2:
            return
        
        # Handle style parameter if provided
        if style is not None:
            color = f"#{style.color[0]:02x}{style.color[1]:02x}{style.color[2]:02x}" if style.color else color
            width = style.line_width if hasattr(style, 'line_width') else width
        
        # Flatten points for Tkinter
        flat_points = []
        for x, y in points:
            flat_points.extend([x, y])
        
        if fill:
            self.tk_canvas.create_polygon(flat_points, outline=color, width=width, fill="")
        else:
            self.tk_canvas.create_line(flat_points, width=width, fill=color)
    
    def draw_text(self, position: Coordinate, text: str, font_size: int = 12, color: str = "black", style=None) -> None:
        """Draw text at position."""
        x, y = position
        
        # Handle style parameter if provided
        if style is not None:
            color = f"#{style.color[0]:02x}{style.color[1]:02x}{style.color[2]:02x}" if style.color else color
            font_size = style.font_size if hasattr(style, 'font_size') else font_size
        
        self.tk_canvas.create_text(
            x, y, text=text, font=("Arial", font_size), fill=color
        )
    
    def clear(self) -> None:
        """Clear the canvas."""
        self.tk_canvas.delete("all")
