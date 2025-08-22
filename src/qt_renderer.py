"""
Clean Qt renderer for Dau-compliant EG visualization.

Takes styled EGDF primitives from the rendering pipeline and draws them
with QPainter. Implements proper Dau specification:
- Rectilinear ligatures (no curves, no hook lines)
- Style-driven colors and fonts
- Tight cut boundaries
- Proper vertex and predicate labeling
"""
from __future__ import annotations
from typing import Dict, Tuple, Any, Optional
from dataclasses import dataclass

try:
    from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPixmap
    from PySide6.QtCore import QRectF, Qt
except ImportError:
    QPainter = object  # type: ignore


@dataclass
class RenderBounds:
    """Canvas bounds for coordinate transformation."""
    x1: float
    y1: float
    x2: float
    y2: float
    
    @property
    def width(self) -> float:
        return self.x2 - self.x1
    
    @property
    def height(self) -> float:
        return self.y2 - self.y1


class QtRenderer:
    """Clean Qt renderer that takes styled EGDF primitives and renders to QPixmap."""
    
    def __init__(self, margin: int = 50):
        self.margin = margin
        from rendering_styles import DauStyle
        self.default_style = DauStyle()
    
    def create_canvas(self):
        """Create Qt canvas widget for rendering."""
        try:
            from PySide6.QtWidgets import QWidget
            from PySide6.QtCore import QSize
            from PySide6.QtGui import QPainter, QPixmap
            
            class EGCanvasWidget(QWidget):
                def __init__(self, renderer):
                    super().__init__()
                    self.renderer = renderer
                    self.pixmap = None
                    self.setMinimumSize(600, 400)
                
                def set_pixmap(self, pixmap):
                    self.pixmap = pixmap
                    self.update()
                
                def update_graph(self, layout_result, egi):
                    """Update canvas with new graph data."""
                    try:
                        # Get canvas size
                        canvas_size = (self.width(), self.height())
                        
                        # Get canvas bounds from layout_result
                        if hasattr(layout_result, 'canvas_bounds'):
                            bounds = layout_result.canvas_bounds
                            canvas_bounds = RenderBounds(bounds[0], bounds[1], bounds[2], bounds[3])
                        else:
                            # Default bounds
                            canvas_bounds = RenderBounds(0, 0, 200, 150)
                        
                        # Get primitives from layout_result
                        if hasattr(layout_result, 'primitives'):
                            primitives = layout_result.primitives
                        else:
                            primitives = {}
                        
                        # Render to pixmap
                        pixmap = self.renderer.render(primitives, canvas_bounds, canvas_size, self.renderer.default_style)
                        self.set_pixmap(pixmap)
                        
                    except Exception as e:
                        print(f"Canvas update error: {e}")
                        import traceback
                        traceback.print_exc()
                
                def paintEvent(self, event):
                    painter = QPainter(self)
                    if self.pixmap:
                        painter.drawPixmap(0, 0, self.pixmap)
                    else:
                        painter.fillRect(self.rect(), self.renderer.default_style.background_color)
                        painter.setPen(self.renderer.default_style.text_color)
                        painter.drawText(self.rect(), Qt.AlignCenter, "No graph loaded")
                
                def sizeHint(self):
                    return QSize(600, 400)
            
            return EGCanvasWidget(self)
            
        except ImportError:
            return None
    
    def render(self, styled_primitives: Dict[str, Any], canvas_bounds: RenderBounds, 
               canvas_size: Tuple[int, int], style) -> QPixmap:
        """
        Render styled EGDF primitives to QPixmap.
        
        Args:
            styled_primitives: Output from DauStyle.apply_style()
            canvas_bounds: Logical bounds of the graph
            canvas_size: Target pixel dimensions (width, height)
            style: DauStyle instance for colors/fonts
            
        Returns:
            QPixmap ready for display
        """
        width, height = canvas_size
        pixmap = QPixmap(width, height)
        pixmap.fill(style.background_color)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate transform from logical bounds to screen pixels
        scale_x = (width - 2 * self.margin) / max(1e-6, canvas_bounds.width)
        scale_y = (height - 2 * self.margin) / max(1e-6, canvas_bounds.height)
        scale = min(scale_x, scale_y)  # Uniform scaling
        
        offset_x = self.margin + (width - 2 * self.margin - canvas_bounds.width * scale) / 2
        offset_y = self.margin + (height - 2 * self.margin - canvas_bounds.height * scale) / 2
        
        def transform_point(x: float, y: float) -> Tuple[float, float]:
            """Transform logical coordinates to screen pixels."""
            screen_x = (x - canvas_bounds.x1) * scale + offset_x
            screen_y = (y - canvas_bounds.y1) * scale + offset_y
            return screen_x, screen_y
        
        def transform_bounds(bounds: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
            """Transform logical bounds to screen bounds."""
            x1, y1, x2, y2 = bounds
            sx1, sy1 = transform_point(x1, y1)
            sx2, sy2 = transform_point(x2, y2)
            return sx1, sy1, sx2, sy2
        
        # Render in proper order: cuts, predicates, vertices, then ligatures connecting them
        self._render_cuts(painter, styled_primitives, transform_bounds, style)
        self._render_predicates(painter, styled_primitives, transform_bounds, style)
        self._render_vertices(painter, styled_primitives, transform_point, style)
        self._render_ligatures(painter, styled_primitives, transform_point, style)
        
        painter.end()
        return pixmap
    
    def _render_cuts(self, painter: QPainter, primitives: Dict, transform_bounds, style):
        """Render cut boundaries."""
        cut_pen = QPen(style.cut_color, style.cut_line_width, Qt.PenStyle.SolidLine)
        painter.setPen(cut_pen)
        painter.setBrush(QBrush())  # No fill
        
        for prim_id, primitive in primitives.items():
            if getattr(primitive, 'element_type', None) == 'cut' and hasattr(primitive, 'bounds'):
                sx1, sy1, sx2, sy2 = transform_bounds(primitive.bounds)
                width = max(0, sx2 - sx1)
                height = max(0, sy2 - sy1)
                
                # Draw rounded rectangle for cut
                corner_radius = getattr(style, 'cut_corner_radius', 5)
                painter.drawRoundedRect(QRectF(sx1, sy1, width, height), 
                                     corner_radius, corner_radius)
    
    def _render_ligatures(self, painter: QPainter, primitives: Dict, transform_point, style):
        """Render rectilinear ligatures (no curves, no hooks)."""
        ligature_pen = QPen(style.ligature_color, style.ligature_width, Qt.PenStyle.SolidLine)
        ligature_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(ligature_pen)
        
        for prim_id, primitive in primitives.items():
            if getattr(primitive, 'element_type', None) == 'ligature':
                # Get start and end points
                if hasattr(primitive, 'start_pos') and hasattr(primitive, 'end_pos'):
                    sx1, sy1 = transform_point(*primitive.start_pos)
                    sx2, sy2 = transform_point(*primitive.end_pos)
                    
                    # Draw rectilinear path (right angles only)
                    if abs(sx2 - sx1) > abs(sy2 - sy1):
                        # Horizontal first, then vertical
                        painter.drawLine(sx1, sy1, sx2, sy1)
                        painter.drawLine(sx2, sy1, sx2, sy2)
                    else:
                        # Vertical first, then horizontal
                        painter.drawLine(sx1, sy1, sx1, sy2)
                        painter.drawLine(sx1, sy2, sx2, sy2)
    
    def _render_predicates(self, painter: QPainter, primitives: Dict, transform_bounds, style):
        """Render predicate labels."""
        predicate_pen = QPen(style.text_color, 1.0, Qt.PenStyle.SolidLine)
        painter.setPen(predicate_pen)
        
        font = QFont(style.predicate_font_family, style.predicate_font_size)
        painter.setFont(font)
        
        for prim_id, primitive in primitives.items():
            if getattr(primitive, 'element_type', None) == 'predicate':
                if hasattr(primitive, 'bounds') and hasattr(primitive, 'label'):
                    sx1, sy1, sx2, sy2 = transform_bounds(primitive.bounds)
                    
                    # Draw centered text
                    rect = QRectF(sx1, sy1, sx2 - sx1, sy2 - sy1)
                    painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, primitive.label)
    
    def _render_vertices(self, painter: QPainter, primitives: Dict, transform_point, style):
        """Render vertices as dots with optional labels."""
        vertex_pen = QPen(style.vertex_color, 1.0, Qt.PenStyle.SolidLine)
        vertex_brush = QBrush(style.vertex_color)
        painter.setPen(vertex_pen)
        painter.setBrush(vertex_brush)
        
        for prim_id, primitive in primitives.items():
            if getattr(primitive, 'element_type', None) == 'vertex':
                if hasattr(primitive, 'position'):
                    sx, sy = transform_point(*primitive.position)
                    radius = getattr(style, 'vertex_radius', 3)
                    
                    # Draw vertex dot
                    painter.drawEllipse(QRectF(sx - radius, sy - radius, 
                                             2 * radius, 2 * radius))
                    
                    # Draw label if present
                    if hasattr(primitive, 'label') and primitive.label:
                        font = QFont(style.predicate_font_family, style.predicate_font_size)
                        painter.setFont(font)
                        painter.setPen(QPen(style.text_color))
                        
                        # Position label near vertex
                        label_rect = QRectF(sx + radius + 2, sy - 10, 50, 20)
                        painter.drawText(label_rect, Qt.AlignmentFlag.AlignLeft, primitive.label)
