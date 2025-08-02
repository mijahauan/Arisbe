"""
Pure Diagram Renderer for Existential Graph Visualization
Handles visual presentation following Dau's drawing conventions.
Completely separated from layout and data concerns.
"""

from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
from enum import Enum
import math

# Handle imports for both module and script execution
try:
    from .layout_engine import LayoutResult, LayoutElement, Coordinate, Bounds
    from .canvas_backend import Canvas, DrawingStyle, EGDrawingStyles
    from .egi_core_dau import RelationalGraphWithCuts, ElementID, Vertex, Edge, Cut
except ImportError:
    from layout_engine import LayoutResult, LayoutElement, Coordinate, Bounds
    from canvas_backend import Canvas, DrawingStyle, EGDrawingStyles
    from egi_core_dau import RelationalGraphWithCuts, ElementID, Vertex, Edge, Cut


class RenderingMode(Enum):
    """Different rendering modes for different contexts"""
    NORMAL = "normal"                    # Standard diagram rendering
    SELECTION_OVERLAY = "selection_overlay"  # With selection handles/highlights
    EDITING = "editing"                  # With editing affordances
    PRESENTATION = "presentation"        # Clean presentation mode
    DEBUG = "debug"                      # With debug information


class VisualTheme(Enum):
    """Visual themes following different conventions"""
    DAU_STANDARD = "dau_standard"        # Standard Dau conventions
    PEIRCE_CLASSIC = "peirce_classic"    # Classic Peirce style
    MODERN_CLEAN = "modern_clean"        # Modern, clean aesthetic
    HIGH_CONTRAST = "high_contrast"      # High contrast for accessibility


@dataclass(frozen=True)
class RenderingContext:
    """Context and state for rendering operations"""
    mode: RenderingMode = RenderingMode.NORMAL
    theme: VisualTheme = VisualTheme.DAU_STANDARD
    
    # Selection state
    selected_elements: Set[ElementID] = None
    highlighted_elements: Set[ElementID] = None
    
    # Visual state
    show_debug_info: bool = False
    show_element_ids: bool = False
    show_containment_hierarchy: bool = False
    
    # Animation state
    animation_progress: float = 0.0  # 0.0 to 1.0 for smooth transitions
    
    def __post_init__(self):
        if self.selected_elements is None:
            object.__setattr__(self, 'selected_elements', set())
        if self.highlighted_elements is None:
            object.__setattr__(self, 'highlighted_elements', set())


class ElementRenderer:
    """
    Renders individual elements following Dau's conventions.
    Pure rendering logic with no layout or data concerns.
    """
    
    def __init__(self, canvas: Canvas, theme: VisualTheme = VisualTheme.DAU_STANDARD):
        self.canvas = canvas
        self.theme = theme
        self.styles = self._create_theme_styles(theme)
    
    def render_vertex(self, layout_element: LayoutElement, vertex: Vertex, 
                     context: RenderingContext) -> None:
        """Render a vertex as heavy spot following Dau's conventions"""
        position = layout_element.position
        
        # Determine style based on context
        style = self.styles['vertex_spot']
        if layout_element.element_id in context.selected_elements:
            style = self.styles['vertex_selected']
        elif layout_element.element_id in context.highlighted_elements:
            style = self.styles['vertex_highlighted']
        
        # Render heavy spot (Dau convention: vertices are heavy drawn)
        self.canvas.draw_circle(position, 5.0, style)
        
        # Render label if present
        if vertex.label:
            label_style = self.styles['vertex_label']
            label_pos = (position[0] + 8, position[1] - 8)
            self.canvas.draw_text(vertex.label, label_pos, label_style)
        
        # Render selection handles if selected
        if (layout_element.element_id in context.selected_elements and 
            context.mode == RenderingMode.SELECTION_OVERLAY):
            self._render_vertex_selection_handles(position)
        
        # Debug info
        if context.show_debug_info:
            self._render_debug_info(layout_element, position)
    
    def render_edge(self, layout_element: LayoutElement, edge: Edge,
                   context: RenderingContext) -> None:
        """Render an edge as relation with proper attachment following Dau's conventions"""
        
        # Determine style
        style = self.styles['relation_line']
        if layout_element.element_id in context.selected_elements:
            style = self.styles['relation_selected']
        
        # Render connection lines between vertices
        if layout_element.curve_points and len(layout_element.curve_points) >= 2:
            points = layout_element.curve_points
            
            # Draw lines connecting vertices (identity lines are heavy)
            for i in range(len(points) - 1):
                self.canvas.draw_line(points[i], points[i + 1], self.styles['identity_line'])
        
        # Render relation name with hooks to attachment points
        if hasattr(edge, 'relation') and edge.relation:
            center = layout_element.position
            relation_style = self.styles['relation_sign']
            self.canvas.draw_text(edge.relation, center, relation_style)
            
            # Render hooks to attachment points (Dau convention)
            if layout_element.attachment_points:
                self._render_predicate_hooks(center, layout_element.attachment_points)
        
        # Selection handles
        if (layout_element.element_id in context.selected_elements and 
            context.mode == RenderingMode.SELECTION_OVERLAY):
            self._render_edge_selection_handles(layout_element)
    
    def render_cut(self, layout_element: LayoutElement, cut: Cut,
                  context: RenderingContext) -> None:
        """Render a cut as fine-drawn closed curve following Dau's conventions"""
        
        # Determine style
        style = self.styles['cut_line']
        if layout_element.element_id in context.selected_elements:
            style = self.styles['cut_selected']
        elif layout_element.element_id in context.highlighted_elements:
            style = self.styles['cut_highlighted']
        
        # Render closed curve (Dau convention: cuts are fine-drawn)
        if layout_element.curve_points:
            self.canvas.draw_curve(layout_element.curve_points, style, closed=True)
        
        # Selection handles for resizing
        if (layout_element.element_id in context.selected_elements and 
            context.mode == RenderingMode.SELECTION_OVERLAY):
            self._render_cut_selection_handles(layout_element)
        
        # Debug info
        if context.show_debug_info:
            self._render_debug_info(layout_element, layout_element.position)
    
    def render_selection_rectangle(self, start: Coordinate, end: Coordinate) -> None:
        """Render selection rectangle for drag-to-select"""
        x1, y1 = start
        x2, y2 = end
        
        # Normalize coordinates
        left, right = min(x1, x2), max(x1, x2)
        top, bottom = min(y1, y2), max(y1, y2)
        
        # Draw selection rectangle
        points = [(left, top), (right, top), (right, bottom), (left, bottom)]
        self.canvas.draw_curve(points, self.styles['selection_rectangle'], closed=True)
    
    def _render_vertex_selection_handles(self, position: Coordinate) -> None:
        """Render selection handles around a vertex"""
        x, y = position
        handle_size = 3
        handle_style = self.styles['selection_handle']
        
        # Four corner handles
        handles = [
            (x - 8, y - 8), (x + 8, y - 8),
            (x - 8, y + 8), (x + 8, y + 8)
        ]
        
        for handle_pos in handles:
            self.canvas.draw_circle(handle_pos, handle_size, handle_style)
    
    def _render_edge_selection_handles(self, layout_element: LayoutElement) -> None:
        """Render selection handles for an edge"""
        if layout_element.curve_points:
            handle_style = self.styles['selection_handle']
            
            # Handles at endpoints and midpoints
            for point in layout_element.curve_points:
                self.canvas.draw_circle(point, 3, handle_style)
    
    def _render_cut_selection_handles(self, layout_element: LayoutElement) -> None:
        """Render resize handles around a cut"""
        x1, y1, x2, y2 = layout_element.bounds
        handle_style = self.styles['selection_handle']
        
        # Corner and edge handles for resizing
        handles = [
            # Corners
            (x1, y1), (x2, y1), (x2, y2), (x1, y2),
            # Edges
            ((x1 + x2) / 2, y1), (x2, (y1 + y2) / 2),
            ((x1 + x2) / 2, y2), (x1, (y1 + y2) / 2)
        ]
        
        for handle_pos in handles:
            self.canvas.draw_circle(handle_pos, 4, handle_style)
    
    def _render_predicate_hooks(self, center: Coordinate, 
                               attachment_points: Dict[str, Coordinate]) -> None:
        """Render hooks from predicate to attachment points (Dau convention)"""
        hook_style = self.styles['predicate_hook']
        
        for attachment_point in attachment_points.values():
            # Draw line from predicate center to attachment point
            self.canvas.draw_line(center, attachment_point, hook_style)
            
            # Draw small hook indicator
            self.canvas.draw_circle(attachment_point, 2, hook_style)
    
    def _render_debug_info(self, layout_element: LayoutElement, position: Coordinate) -> None:
        """Render debug information for development"""
        debug_style = self.styles['debug_text']
        
        # Element ID
        id_text = f"ID: {layout_element.element_id[:8]}"
        self.canvas.draw_text(id_text, (position[0] + 10, position[1] + 10), debug_style)
        
        # Bounds
        x1, y1, x2, y2 = layout_element.bounds
        bounds_points = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
        self.canvas.draw_curve(bounds_points, self.styles['debug_bounds'], closed=True)
    
    def _create_theme_styles(self, theme: VisualTheme) -> Dict[str, DrawingStyle]:
        """Create drawing styles for the specified theme"""
        if theme == VisualTheme.DAU_STANDARD:
            return {
                # Dau's conventions: heavy lines for identity, fine lines for cuts
                'vertex_spot': DrawingStyle(
                    color=(0, 0, 0), line_width=2.0, fill_color=(0, 0, 0)
                ),
                'vertex_selected': DrawingStyle(
                    color=(255, 0, 0), line_width=3.0, fill_color=(255, 0, 0)
                ),
                'vertex_highlighted': DrawingStyle(
                    color=(0, 100, 255), line_width=2.0, fill_color=(0, 100, 255)
                ),
                'vertex_label': DrawingStyle(
                    color=(0, 0, 0), font_size=10, font_family="Arial"
                ),
                'identity_line': DrawingStyle(
                    color=(0, 0, 0), line_width=3.0  # Heavy line
                ),
                'cut_line': DrawingStyle(
                    color=(0, 0, 0), line_width=1.0  # Fine line
                ),
                'cut_selected': DrawingStyle(
                    color=(255, 0, 0), line_width=2.0
                ),
                'cut_highlighted': DrawingStyle(
                    color=(0, 100, 255), line_width=1.5
                ),
                'relation_line': DrawingStyle(
                    color=(0, 0, 0), line_width=1.0
                ),
                'relation_selected': DrawingStyle(
                    color=(255, 0, 0), line_width=2.0
                ),
                'relation_sign': DrawingStyle(
                    color=(0, 0, 0), font_size=12, font_family="Arial"
                ),
                'predicate_hook': DrawingStyle(
                    color=(0, 0, 0), line_width=1.0
                ),
                'selection_rectangle': DrawingStyle(
                    color=(0, 100, 255), line_width=1.0, dash_pattern=[5, 5]
                ),
                'selection_handle': DrawingStyle(
                    color=(255, 255, 255), line_width=1.0, fill_color=(0, 100, 255)
                ),
                'debug_text': DrawingStyle(
                    color=(128, 128, 128), font_size=8, font_family="Arial"
                ),
                'debug_bounds': DrawingStyle(
                    color=(128, 128, 128), line_width=1.0, dash_pattern=[2, 2]
                )
            }
        
        # Add other themes as needed
        return self._create_theme_styles(VisualTheme.DAU_STANDARD)


class DiagramRenderer:
    """
    Main diagram renderer coordinating all visual presentation.
    Pure rendering logic with complete separation from layout and data.
    """
    
    def __init__(self, canvas: Canvas, theme: VisualTheme = VisualTheme.DAU_STANDARD):
        self.canvas = canvas
        self.theme = theme
        self.element_renderer = ElementRenderer(canvas, theme)
        
        # Rendering state
        self.last_rendered_layout: Optional[LayoutResult] = None
        self.rendering_in_progress = False
    
    def render_diagram(self, layout_result: LayoutResult, graph: RelationalGraphWithCuts,
                      context: RenderingContext = None) -> None:
        """
        Render complete diagram from layout result.
        Pure rendering with no layout calculations.
        """
        if self.rendering_in_progress:
            return  # Prevent infinite rendering loops
        
        if context is None:
            context = RenderingContext()
        
        self.rendering_in_progress = True
        
        try:
            # Clear canvas
            self.canvas.clear()
            
            # Render in proper order: cuts first (background), then vertices and edges
            self._render_cuts(layout_result, graph, context)
            self._render_vertices(layout_result, graph, context)
            self._render_edges(layout_result, graph, context)
            
            # Render overlays
            if context.mode == RenderingMode.SELECTION_OVERLAY:
                self._render_selection_overlays(layout_result, context)
            
            # Update canvas
            self.canvas.update()
            
            self.last_rendered_layout = layout_result
            
        finally:
            self.rendering_in_progress = False
    
    def render_selection_rectangle(self, start: Coordinate, end: Coordinate) -> None:
        """Render selection rectangle for drag-to-select operations"""
        self.element_renderer.render_selection_rectangle(start, end)
        self.canvas.update()
    
    def clear_canvas(self) -> None:
        """Clear the canvas"""
        self.canvas.clear()
        self.canvas.update()
    
    def _render_cuts(self, layout_result: LayoutResult, graph: RelationalGraphWithCuts,
                    context: RenderingContext) -> None:
        """Render all cuts in proper order (outermost first)"""
        # Get cuts sorted by depth (outermost first for proper layering)
        cuts_by_depth = {}
        
        for cut in graph.Cut:
            if cut.id in layout_result.elements:
                depth = self._calculate_rendering_depth(cut.id, layout_result)
                if depth not in cuts_by_depth:
                    cuts_by_depth[depth] = []
                cuts_by_depth[depth].append(cut)
        
        # Render from outermost to innermost
        for depth in sorted(cuts_by_depth.keys()):
            for cut in cuts_by_depth[depth]:
                layout_element = layout_result.elements[cut.id]
                self.element_renderer.render_cut(layout_element, cut, context)
    
    def _render_vertices(self, layout_result: LayoutResult, graph: RelationalGraphWithCuts,
                        context: RenderingContext) -> None:
        """Render all vertices"""
        for vertex in graph.V:
            if vertex.id in layout_result.elements:
                layout_element = layout_result.elements[vertex.id]
                self.element_renderer.render_vertex(layout_element, vertex, context)
    
    def _render_edges(self, layout_result: LayoutResult, graph: RelationalGraphWithCuts,
                     context: RenderingContext) -> None:
        """Render all edges"""
        for edge in graph.E:
            if edge.id in layout_result.elements:
                layout_element = layout_result.elements[edge.id]
                self.element_renderer.render_edge(layout_element, edge, context)
    
    def _render_selection_overlays(self, layout_result: LayoutResult, 
                                  context: RenderingContext) -> None:
        """Render selection overlays and handles"""
        # Selection overlays are rendered by individual element renderers
        # This method can add global selection UI elements if needed
        pass
    
    def _calculate_rendering_depth(self, element_id: ElementID, 
                                  layout_result: LayoutResult) -> int:
        """Calculate rendering depth for proper layering"""
        depth = 0
        current_element = layout_result.elements.get(element_id)
        
        while current_element and current_element.parent_area:
            depth += 1
            current_element = layout_result.elements.get(current_element.parent_area)
        
        return depth
    
    def get_element_at_point(self, point: Coordinate) -> Optional[ElementID]:
        """Find element at point using last rendered layout"""
        if self.last_rendered_layout:
            return self.last_rendered_layout.find_element_at_point(point)
        return None
    
    def save_diagram(self, filename: str, format: str = "png") -> None:
        """Save rendered diagram to file"""
        self.canvas.save_to_file(filename, format)


# Utility functions for integration

def create_rendering_context(mode: RenderingMode = RenderingMode.NORMAL,
                           selected_elements: Set[ElementID] = None,
                           highlighted_elements: Set[ElementID] = None) -> RenderingContext:
    """Factory function to create rendering context"""
    return RenderingContext(
        mode=mode,
        selected_elements=selected_elements or set(),
        highlighted_elements=highlighted_elements or set()
    )


def create_diagram_renderer(canvas: Canvas, 
                          theme: VisualTheme = VisualTheme.DAU_STANDARD) -> DiagramRenderer:
    """Factory function to create diagram renderer"""
    return DiagramRenderer(canvas, theme)
