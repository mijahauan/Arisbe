"""
PySide6 Canvas Backend for Arisbe

Implements the Canvas interface for PySide6, providing high-quality vector graphics
rendering for Existential Graph diagrams.
"""

from typing import List, Tuple, Optional, Dict, Any, Callable
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath
from PySide6.QtCore import Qt, QPointF, QRectF
import sys

from canvas_backend import Canvas, CanvasBackend, DrawingStyle, Coordinate, EventType


class PySide6Canvas(Canvas):
    """PySide6 implementation of the Canvas interface."""
    
    def __init__(self, width: int, height: int, title: str = "Arisbe Diagram"):
        super().__init__(width, height)
        self.title = title
        
        # Initialize Qt application if needed
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
        else:
            self.app = QApplication.instance()
        
        # Create main window and canvas widget
        self.main_window = QMainWindow()
        self.main_window.setWindowTitle(title)
        self.main_window.resize(width, height)
        
        # Create custom widget for drawing
        self.canvas_widget = EGCanvasWidget(width, height)
        self.main_window.setCentralWidget(self.canvas_widget)
    
    def clear(self):
        """Clear the canvas."""
        self.canvas_widget.clear()
        self.update()
    
    def draw_line(self, start: Coordinate, end: Coordinate, style: DrawingStyle):
        """Draw a line from start to end."""
        self.canvas_widget.add_element({
            'type': 'line',
            'start': start,
            'end': end,
            'style': style
        })
    
    def draw_curve(self, points: List[Coordinate], style: DrawingStyle, closed: bool = False):
        """Draw a smooth curve through points."""
        self.canvas_widget.add_element({
            'type': 'curve',
            'points': points,
            'closed': closed,
            'style': style
        })
    
    def draw_circle(self, center: Coordinate, radius: float, style: DrawingStyle):
        """Draw a circle."""
        self.canvas_widget.add_element({
            'type': 'circle',
            'center': center,
            'radius': radius,
            'style': style
        })
    
    def draw_text(self, text: str, position: Coordinate, style: DrawingStyle):
        """Draw text at position."""
        self.canvas_widget.add_element({
            'type': 'text',
            'text': text,
            'position': position,
            'style': style
        })
    
    def draw_polygon(self, points: List[Coordinate], style: DrawingStyle):
        """Draw a filled polygon."""
        self.canvas_widget.add_element({
            'type': 'polygon',
            'points': points,
            'style': style
        })
    
    def get_text_bounds(self, text: str, style: DrawingStyle) -> Tuple[float, float]:
        """Get width and height of text when rendered."""
        return self.canvas_widget.get_text_bounds(text, style)
    
    def bind_event(self, event_name: str, callback: Callable):
        """Bind a callback function to a canvas event."""
        # Map Tkinter-style event names to Qt events
        # For now, we'll store the callbacks but Qt event handling
        # would need to be implemented in the widget
        pass
    
    def update(self):
        """Update/refresh the canvas display."""
        self.canvas_widget.update()
    
    def save_to_file(self, filename: str, format: str = "png"):
        """Save canvas content to file."""
        pixmap = self.canvas_widget.grab()
        pixmap.save(filename)
    
    def show(self):
        """Show the canvas window."""
        self.main_window.show()
    
    def run(self):
        """Run the Qt event loop."""
        self.show()
        return self.app.exec()


class EGCanvasWidget(QWidget):
    """Custom Qt widget for rendering EG diagrams."""
    
    def __init__(self, width: int, height: int):
        super().__init__()
        self.setFixedSize(width, height)
        self.elements = []
        self.setStyleSheet("background-color: white;")
    
    def clear(self):
        """Clear all elements."""
        self.elements = []
    
    def add_element(self, element: dict):
        """Add a drawing element."""
        self.elements.append(element)
    
    def get_text_bounds(self, text: str, style: DrawingStyle) -> Tuple[float, float]:
        """Get text dimensions."""
        font = self._create_font(style)
        metrics = self.fontMetrics()
        rect = metrics.boundingRect(text)
        return float(rect.width()), float(rect.height())
    
    def paintEvent(self, event):
        """Handle paint events with high-quality rendering."""
        painter = QPainter(self)
        
        # Enable anti-aliasing for professional quality
        painter.setRenderHints(
            QPainter.RenderHint.Antialiasing |
            QPainter.RenderHint.TextAntialiasing |
            QPainter.RenderHint.SmoothPixmapTransform
        )
        
        # Clear background
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        
        # Render all elements
        for element in self.elements:
            self._render_element(painter, element)
    
    def _render_element(self, painter: QPainter, element: dict):
        """Render a single drawing element."""
        element_type = element['type']
        style = element.get('style', {})
        
        # Configure pen and brush
        pen = self._create_pen(style)
        brush = self._create_brush(style)
        painter.setPen(pen)
        painter.setBrush(brush)
        
        if element_type == 'line':
            start = QPointF(*element['start'])
            end = QPointF(*element['end'])
            painter.drawLine(start, end)
        
        elif element_type == 'curve':
            points = [QPointF(*pt) for pt in element['points']]
            if len(points) >= 2:
                path = QPainterPath()
                path.moveTo(points[0])
                for pt in points[1:]:
                    path.lineTo(pt)
                if element.get('closed', False):
                    path.closeSubpath()
                painter.drawPath(path)
        
        elif element_type == 'circle':
            center = element['center']
            radius = element['radius']
            rect = QRectF(center[0] - radius, center[1] - radius, 
                         radius * 2, radius * 2)
            painter.drawEllipse(rect)
        
        elif element_type == 'text':
            position = QPointF(*element['position'])
            font = self._create_font(style)
            painter.setFont(font)
            painter.drawText(position, element['text'])
        
        elif element_type == 'polygon':
            points = [QPointF(*pt) for pt in element['points']]
            if points:
                polygon = QPolygonF(points)
                painter.drawPolygon(polygon)
    
    def _create_pen(self, style) -> QPen:
        """Create Qt pen from style."""
        # Handle both dict and DrawingStyle dataclass
        if hasattr(style, 'color'):
            color = getattr(style, 'color', (0, 0, 0))
            width = getattr(style, 'line_width', 1.0)
            dash_pattern = getattr(style, 'dash_pattern', None)
        else:
            color = style.get('color', (0, 0, 0))
            width = style.get('line_width', 1.0)
            dash_pattern = style.get('dash_pattern', None)
        
        if isinstance(color, tuple):
            qcolor = QColor(*color)
        else:
            qcolor = QColor(color)
        
        pen = QPen(qcolor)
        pen.setWidthF(width)
        
        if dash_pattern:
            pen.setStyle(Qt.PenStyle.DashLine)
        
        return pen
    
    def _create_brush(self, style) -> QBrush:
        """Create Qt brush from style."""
        # Handle both dict and DrawingStyle dataclass
        if hasattr(style, 'fill_color'):
            fill_color = getattr(style, 'fill_color', None)
        else:
            fill_color = style.get('fill_color', None)
        
        if fill_color is None:
            return QBrush(Qt.BrushStyle.NoBrush)
        
        if isinstance(fill_color, tuple):
            qcolor = QColor(*fill_color)
        else:
            qcolor = QColor(fill_color)
        
        return QBrush(qcolor)
    
    def _create_font(self, style) -> QFont:
        """Create Qt font from style."""
        # Handle both dict and DrawingStyle dataclass
        if hasattr(style, 'font_family'):
            font_family = getattr(style, 'font_family', 'Arial')
            font_size = getattr(style, 'font_size', 12)
            bold = getattr(style, 'bold', False)
            italic = getattr(style, 'italic', False)
        else:
            font_family = style.get('font_family', 'Arial')
            font_size = style.get('font_size', 12)
            bold = style.get('bold', False)
            italic = style.get('italic', False)
        
        font = QFont(font_family, font_size)
        
        if bold:
            font.setBold(True)
        if italic:
            font.setItalic(True)
        
        return font


class PySide6Backend(CanvasBackend):
    """Factory for creating PySide6 canvas instances."""
    
    def create_canvas(self, width: int, height: int, title: str = "Arisbe Diagram") -> Canvas:
        """Create a new PySide6 canvas instance."""
        return PySide6Canvas(width, height, title)
    
    def is_available(self) -> bool:
        """Check if PySide6 is available."""
        try:
            from PySide6.QtWidgets import QApplication
            return True
        except ImportError:
            return False
    
    def run_event_loop(self):
        """Start the Qt event loop."""
        app = QApplication.instance()
        if app:
            return app.exec()
        return 0
    
    def stop_event_loop(self):
        """Stop the Qt event loop."""
        app = QApplication.instance()
        if app:
            app.quit()


# Test the backend
if __name__ == "__main__":
    backend = PySide6Backend()
    if backend.is_available():
        print("Testing PySide6 backend...")
        canvas = backend.create_canvas(600, 400, "PySide6 Test")
        
        # Draw test elements
        from canvas_backend import DrawingStyle
        
        canvas.draw_line((50, 50), (550, 350), DrawingStyle(color=(0, 0, 255), line_width=2))
        canvas.draw_circle((300, 200), 50, DrawingStyle(color=(255, 0, 0), fill_color=(255, 255, 0)))
        canvas.draw_text("PySide6 Backend Working!", (200, 100), 
                        DrawingStyle(color=(0, 128, 0), font_size=16))
        
        canvas.run()
    else:
        print("PySide6 not available")
