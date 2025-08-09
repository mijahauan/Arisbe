#!/usr/bin/env python3
"""
Enhanced Diagram Renderer with Dau-Compliant Visual Quality

Professional rendering system that integrates with the canonical pipeline
and provides high-quality visual output following Dau's conventions.
"""

import sys
import os
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass

# Add src to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from egi_core_dau import RelationalGraphWithCuts, ElementID
from layout_engine_clean import SpatialPrimitive, LayoutResult
from dau_rendering_theme import get_current_theme, RenderingTheme, RenderingQuality
from mode_aware_selection import Mode, SelectionState

try:
    from PySide6.QtWidgets import QWidget
    from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath, QFontMetrics
    from PySide6.QtCore import Qt, QPointF, QRectF
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False
    # Create dummy classes for type hints when PySide6 not available
    class QPainter: pass
    class QWidget: pass
    class QColor: pass
    class QFont: pass


@dataclass
class RenderingContext:
    """Context information for rendering operations."""
    egi: Optional[RelationalGraphWithCuts]
    spatial_primitives: List[SpatialPrimitive]
    selection_state: SelectionState
    current_mode: Mode
    show_annotations: bool = False
    show_argument_labels: bool = False
    show_context_backgrounds: bool = True


class EnhancedDiagramRenderer:
    """Professional diagram renderer with Dau-compliant visual quality."""
    
    def __init__(self):
        self.theme: RenderingTheme = get_current_theme()
        self.rendering_context: Optional[RenderingContext] = None
        
    def set_theme(self, theme_name: str):
        """Set the rendering theme."""
        from dau_rendering_theme import get_theme_manager
        theme_manager = get_theme_manager()
        if theme_manager.set_theme(theme_name):
            self.theme = theme_manager.get_current_theme()
    
    def render_diagram(self, painter: QPainter, context: RenderingContext):
        """Render complete diagram with professional quality."""
        if not PYSIDE6_AVAILABLE:
            return
            
        self.rendering_context = context
        
        # Configure painter for quality
        self._configure_painter_quality(painter)
        
        # Render in proper layering order
        self._render_canvas_background(painter)
        
        if context.show_context_backgrounds and context.current_mode == Mode.PRACTICE:
            self._render_context_backgrounds(painter)
        
        self._render_diagram_elements(painter)
        
        if context.show_annotations:
            self._render_annotations(painter)
        
        self._render_selection_overlays(painter)
        
        if context.show_argument_labels:
            self._render_argument_labels(painter)
    
    def _configure_painter_quality(self, painter: QPainter):
        """Configure painter for rendering quality."""
        if self.theme.quality == RenderingQuality.PUBLICATION:
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.TextAntialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        elif self.theme.quality == RenderingQuality.STANDARD:
            painter.setRenderHint(QPainter.Antialiasing, self.theme.antialiasing)
            painter.setRenderHint(QPainter.TextAntialiasing, True)
        # DRAFT mode uses minimal antialiasing for speed
    
    def _render_canvas_background(self, painter: QPainter):
        """Render canvas background."""
        painter.fillRect(painter.viewport(), QColor(self.theme.conventions.CANVAS_BACKGROUND))
    
    def _render_context_backgrounds(self, painter: QPainter):
        """Render context backgrounds for Practice mode."""
        if not self.rendering_context or not self.rendering_context.egi:
            return
            
        egi = self.rendering_context.egi
        
        # Render cut interiors with negative context backgrounds
        for primitive in self.rendering_context.spatial_primitives:
            if primitive.element_type == "cut":
                cut_id = primitive.element_id
                
                # Check if this is a negative context
                try:
                    # For now, assume all cuts are negative contexts
                    # This can be enhanced with proper context analysis
                    is_negative = True
                    
                    if is_negative:
                        brush = self.theme.get_brush_for_context(is_negative=True)
                        painter.setPen(Qt.NoPen)
                        painter.setBrush(brush)
                        
                        # Draw background with margin inside cut
                        x1, y1, x2, y2 = primitive.bounds
                        margin = self.theme.conventions.MIN_CUT_MARGIN / 2
                        
                        painter.drawRect(QRectF(
                            x1 + margin, y1 + margin,
                            x2 - x1 - 2*margin, y2 - y1 - 2*margin
                        ))
                        
                except Exception:
                    # Skip if context analysis fails
                    pass
    
    def _render_diagram_elements(self, painter: QPainter):
        """Render all diagram elements in proper order."""
        if not self.rendering_context:
            return
            
        # Render in order: cuts (backgrounds), identity lines, vertices, predicates
        self._render_cuts(painter)
        self._render_identity_lines(painter)
        self._render_vertices(painter)
        self._render_predicates(painter)
    
    def _render_cuts(self, painter: QPainter):
        """Render cut boundaries."""
        for primitive in self.rendering_context.spatial_primitives:
            if primitive.element_type == "cut":
                self._render_cut_boundary(painter, primitive)
    
    def _render_cut_boundary(self, painter: QPainter, primitive: SpatialPrimitive):
        """Render a single cut boundary."""
        element_id = primitive.element_id
        bounds = primitive.bounds
        
        # Check selection/hover state
        is_selected = element_id in self.rendering_context.selection_state.selected_elements
        is_hovered = element_id == self.rendering_context.selection_state.hover_element
        
        # Get appropriate pen
        pen = self.theme.get_pen_for_element("cut", is_selected, is_hovered)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        
        # Draw cut boundary as rectangle (can be enhanced for rounded corners)
        x1, y1, x2, y2 = bounds
        painter.drawRect(QRectF(x1, y1, x2 - x1, y2 - y1))
    
    def _render_identity_lines(self, painter: QPainter):
        """Render heavy lines of identity."""
        for primitive in self.rendering_context.spatial_primitives:
            if primitive.element_type == "edge":
                self._render_identity_line(painter, primitive)
    
    def _render_identity_line(self, painter: QPainter, primitive: SpatialPrimitive):
        """Render a heavy line of identity."""
        element_id = primitive.element_id
        
        # Check selection/hover state
        is_selected = element_id in self.rendering_context.selection_state.selected_elements
        is_hovered = element_id == self.rendering_context.selection_state.hover_element
        
        # Get appropriate pen for heavy line
        pen = self.theme.get_pen_for_element("edge", is_selected, is_hovered)
        painter.setPen(pen)
        
        # Get line endpoints from primitive
        if hasattr(primitive, 'line_points') and primitive.line_points:
            points = primitive.line_points
            for i in range(len(points) - 1):
                x1, y1 = points[i]
                x2, y2 = points[i + 1]
                painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        elif hasattr(primitive, 'bounds'):
            # Fallback: draw line across bounds
            x1, y1, x2, y2 = primitive.bounds
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
    
    def _render_vertices(self, painter: QPainter):
        """Render vertices as identity spots."""
        for primitive in self.rendering_context.spatial_primitives:
            if primitive.element_type == "vertex":
                self._render_vertex_spot(painter, primitive)
    
    def _render_vertex_spot(self, painter: QPainter, primitive: SpatialPrimitive):
        """Render a vertex as an identity spot."""
        element_id = primitive.element_id
        position = primitive.position
        
        # Check selection/hover state
        is_selected = element_id in self.rendering_context.selection_state.selected_elements
        is_hovered = element_id == self.rendering_context.selection_state.hover_element
        
        # Get vertex properties
        radius = self.theme.conventions.VERTEX_RADIUS
        if is_selected:
            radius = self.theme.conventions.VERTEX_SELECTION_RADIUS
        
        # Set pen and brush
        pen = self.theme.get_pen_for_element("vertex", is_selected, is_hovered)
        painter.setPen(pen)
        painter.setBrush(self.theme.vertex_brush)
        
        # Draw identity spot
        x, y = position
        painter.drawEllipse(QPointF(x, y), radius, radius)
    
    def _render_predicates(self, painter: QPainter):
        """Render predicate labels."""
        for primitive in self.rendering_context.spatial_primitives:
            if primitive.element_type == "predicate":
                self._render_predicate_label(painter, primitive)
    
    def _render_predicate_label(self, painter: QPainter, primitive: SpatialPrimitive):
        """Render a predicate label."""
        element_id = primitive.element_id
        position = primitive.position
        
        # Get predicate name from EGI
        predicate_name = "P"  # Default
        if self.rendering_context.egi and element_id in self.rendering_context.egi.rel:
            predicate_name = self.rendering_context.egi.rel[element_id]
        
        # Check selection/hover state
        is_selected = element_id in self.rendering_context.selection_state.selected_elements
        is_hovered = element_id == self.rendering_context.selection_state.hover_element
        
        # Set font and color
        font = self.theme.get_font_for_element("predicate")
        painter.setFont(font)
        
        color = QColor(self.theme.conventions.PREDICATE_TEXT_COLOR)
        if is_selected:
            color = QColor(self.theme.conventions.SELECTION_COLOR)
        elif is_hovered:
            color = QColor(self.theme.conventions.HOVER_COLOR)
        
        painter.setPen(QPen(color))
        
        # Calculate text position (centered)
        metrics = QFontMetrics(font)
        text_rect = metrics.boundingRect(predicate_name)
        x, y = position
        text_x = x - text_rect.width() / 2
        text_y = y + text_rect.height() / 2
        
        # Draw predicate name
        painter.drawText(QPointF(text_x, text_y), predicate_name)
    
    def _render_selection_overlays(self, painter: QPainter):
        """Render selection overlays and feedback."""
        if not self.rendering_context.selection_state.selected_elements:
            return
            
        # Draw selection rectangles around selected elements
        for element_id in self.rendering_context.selection_state.selected_elements:
            primitive = self._find_primitive_by_id(element_id)
            if primitive:
                self._render_selection_overlay(painter, primitive)
    
    def _render_selection_overlay(self, painter: QPainter, primitive: SpatialPrimitive):
        """Render selection overlay for a primitive."""
        pen = self.theme.selection_pen
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        
        # Draw selection rectangle with margin
        margin = 5
        if hasattr(primitive, 'bounds'):
            x1, y1, x2, y2 = primitive.bounds
            painter.drawRect(QRectF(
                x1 - margin, y1 - margin,
                x2 - x1 + 2*margin, y2 - y1 + 2*margin
            ))
        elif hasattr(primitive, 'position'):
            x, y = primitive.position
            size = 20  # Default selection size
            painter.drawRect(QRectF(
                x - size/2 - margin, y - size/2 - margin,
                size + 2*margin, size + 2*margin
            ))
    
    def _render_annotations(self, painter: QPainter):
        """Render diagram annotations."""
        # Placeholder for annotation rendering
        # This will be enhanced with the annotation system
        pass
    
    def _render_argument_labels(self, painter: QPainter):
        """Render argument labels on predicate connections."""
        if not self.rendering_context.egi:
            return
            
        font = self.theme.get_font_for_element("argument_label")
        painter.setFont(font)
        painter.setPen(QPen(QColor(self.theme.conventions.PREDICATE_TEXT_COLOR)))
        
        # Render argument numbers for each predicate
        for edge_id, vertex_sequence in self.rendering_context.egi.nu.items():
            if len(vertex_sequence) > 1:  # Only for multi-argument predicates
                self._render_predicate_argument_labels(painter, edge_id, vertex_sequence)
    
    def _render_predicate_argument_labels(self, painter: QPainter, edge_id: ElementID, 
                                        vertex_sequence: List[ElementID]):
        """Render argument labels for a specific predicate."""
        # Find predicate primitive
        predicate_primitive = self._find_primitive_by_id(edge_id)
        if not predicate_primitive:
            return
            
        px, py = predicate_primitive.position
        
        # Render argument numbers
        for i, vertex_id in enumerate(vertex_sequence):
            vertex_primitive = self._find_primitive_by_id(vertex_id)
            if vertex_primitive:
                vx, vy = vertex_primitive.position
                
                # Calculate label position (midpoint of connection)
                label_x = (px + vx) / 2
                label_y = (py + vy) / 2
                
                # Draw argument number
                painter.drawText(QPointF(label_x, label_y), str(i + 1))
    
    def _find_primitive_by_id(self, element_id: ElementID) -> Optional[SpatialPrimitive]:
        """Find spatial primitive by element ID."""
        if not self.rendering_context:
            return None
            
        for primitive in self.rendering_context.spatial_primitives:
            if primitive.element_id == element_id:
                return primitive
        return None


if __name__ == "__main__":
    print("=== Enhanced Diagram Renderer ===")
    print("Professional rendering system with Dau-compliant visual quality")
    
    # Test theme integration
    renderer = EnhancedDiagramRenderer()
    print(f"Current theme: {renderer.theme.name}")
    print(f"Heavy line width: {renderer.theme.conventions.HEAVY_LINE_WIDTH}")
    print(f"Quality level: {renderer.theme.quality.value}")
