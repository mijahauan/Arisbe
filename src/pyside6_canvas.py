"""
PySide6 Canvas Backend for Professional EG Diagram Rendering

This module provides a high-quality Qt-based canvas implementation for rendering
Existential Graph diagrams with precise vector graphics, anti-aliasing, and 
professional visual quality.
"""

from typing import Tuple, List, Optional, Any
from PySide6.QtWidgets import QWidget, QApplication, QVBoxLayout, QMainWindow
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPolygonF
from PySide6.QtCore import Qt, QPointF, QRectF
import sys

# Type aliases for coordinates and styling
Coordinate = Tuple[float, float]
DrawingStyle = dict

class PySide6Canvas:
    """Professional Qt-based canvas for EG diagram rendering."""
    
    def __init__(self, width: int = 800, height: int = 600, title: str = "EG Diagram"):
        """Initialize Qt canvas with specified dimensions."""
        self.width = width
        self.height = height
        self.title = title
        
        # Initialize Qt application if not already running
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
        
        # Drawing state
        self.elements = []  # Store drawing commands for repainting
        
    def clear(self):
        """Clear the canvas."""
        self.elements.clear()
        self.canvas_widget.elements = []
        self.canvas_widget.update()
    
    def draw_line(self, start: Coordinate, end: Coordinate, style: DrawingStyle = None) -> Any:
        """Draw a line with professional quality."""
        if style is None:
            style = {}
        
        element = {
            'type': 'line',
            'start': start,
            'end': end,
            'style': style
        }
        self.elements.append(element)
        self.canvas_widget.elements.append(element)
        return len(self.elements) - 1  # Return element ID
    
    def draw_circle(self, center: Coordinate, radius: float, style: DrawingStyle = None) -> Any:
        """Draw a circle with anti-aliasing."""
        if style is None:
            style = {}
        
        element = {
            'type': 'circle',
            'center': center,
            'radius': radius,
            'style': style
        }
        self.elements.append(element)
        self.canvas_widget.elements.append(element)
        return len(self.elements) - 1
    
    def draw_oval(self, x_min: float, y_min: float, x_max: float, y_max: float, 
                  style: DrawingStyle = None) -> Any:
        """Draw an oval/ellipse with precise boundaries."""
        if style is None:
            style = {}
        
        element = {
            'type': 'oval',
            'bounds': (x_min, y_min, x_max, y_max),
            'style': style
        }
        self.elements.append(element)
        self.canvas_widget.elements.append(element)
        return len(self.elements) - 1
    
    def draw_curve(self, points: List[Coordinate], style: DrawingStyle = None, 
                   closed: bool = False) -> Any:
        """Draw a smooth curve through points."""
        if style is None:
            style = {}
        
        element = {
            'type': 'curve',
            'points': points,
            'closed': closed,
            'style': style
        }
        self.elements.append(element)
        self.canvas_widget.elements.append(element)
        return len(self.elements) - 1
    
    def draw_text(self, text: str, position: Coordinate, style: DrawingStyle = None) -> Any:
        """Draw text with professional typography."""
        if style is None:
            style = {}
        
        element = {
            'type': 'text',
            'text': text,
            'position': position,
            'style': style
        }
        self.elements.append(element)
        self.canvas_widget.elements.append(element)
        return len(self.elements) - 1
    
    def show(self):
        """Display the canvas window."""
        self.main_window.show()
        self.canvas_widget.update()  # Trigger repaint
    
    def save_to_file(self, filename: str):
        """Save canvas to file (PNG, PDF, SVG supported)."""
        # Qt supports native export to multiple formats
        pixmap = self.canvas_widget.grab()
        pixmap.save(filename)
    
    def run(self):
        """Run the Qt event loop."""
        return self.app.exec()


class EGCanvasWidget(QWidget):
    """Custom Qt widget for rendering EG diagrams."""
    
    def __init__(self, width: int, height: int):
        super().__init__()
        self.setFixedSize(width, height)
        self.elements = []
        
        # Set white background
        self.setStyleSheet("background-color: white;")
    
    def paintEvent(self, event):
        """Handle paint events with professional rendering."""
        painter = QPainter(self)
        
        # Enable high-quality rendering
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        
        # Clear background
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        
        # Render all elements
        for element in self.elements:
            self._render_element(painter, element)
    
    def _render_element(self, painter: QPainter, element: dict):
        """Render a single drawing element with Qt."""
        element_type = element['type']
        style = element.get('style', {})
        
        # Configure pen and brush from style
        pen = self._create_pen(style)
        brush = self._create_brush(style)
        painter.setPen(pen)
        painter.setBrush(brush)
        
        if element_type == 'line':
            start = QPointF(*element['start'])
            end = QPointF(*element['end'])
            painter.drawLine(start, end)
        
        elif element_type == 'circle':
            center = element['center']
            radius = element['radius']
            rect = QRectF(center[0] - radius, center[1] - radius, 
                         radius * 2, radius * 2)
            painter.drawEllipse(rect)
        
        elif element_type == 'oval':
            x_min, y_min, x_max, y_max = element['bounds']
            rect = QRectF(x_min, y_min, x_max - x_min, y_max - y_min)
            painter.drawEllipse(rect)
        
        elif element_type == 'curve':
            points = [QPointF(*pt) for pt in element['points']]
            polygon = QPolygonF(points)
            if element.get('closed', False):
                painter.drawPolygon(polygon)
            else:
                painter.drawPolyline(polygon)
        
        elif element_type == 'text':
            position = QPointF(*element['position'])
            font = self._create_font(style)
            painter.setFont(font)
            painter.drawText(position, element['text'])
    
    def _create_pen(self, style: dict) -> QPen:
        """Create Qt pen from style dictionary."""
        color = style.get('color', 'black')
        width = style.get('width', 1.0)
        
        # Convert color string to QColor
        if isinstance(color, str):
            qcolor = QColor(color)
        else:
            qcolor = QColor(*color)
        
        pen = QPen(qcolor)
        pen.setWidthF(width)
        
        # Handle line styles
        line_style = style.get('line_style', 'solid')
        if line_style == 'dashed':
            pen.setStyle(Qt.PenStyle.DashLine)
        elif line_style == 'dotted':
            pen.setStyle(Qt.PenStyle.DotLine)
        
        return pen
    
    def _create_brush(self, style: dict) -> QBrush:
        """Create Qt brush from style dictionary."""
        fill_color = style.get('fill_color', None)
        
        if fill_color is None:
            return QBrush(Qt.BrushStyle.NoBrush)
        
        if isinstance(fill_color, str):
            qcolor = QColor(fill_color)
        else:
            qcolor = QColor(*fill_color)
        
        return QBrush(qcolor)
    
    def _create_font(self, style: dict) -> QFont:
        """Create Qt font from style dictionary."""
        font_family = style.get('font_family', 'Arial')
        font_size = style.get('font_size', 12)
        
        font = QFont(font_family, font_size)
        
        if style.get('bold', False):
            font.setBold(True)
        if style.get('italic', False):
            font.setItalic(True)
        
        return font


def create_qt_canvas(width: int = 800, height: int = 600, title: str = "EG Diagram") -> PySide6Canvas:
    """Factory function to create a Qt canvas."""
    return PySide6Canvas(width, height, title)


if __name__ == "__main__":
    # Test the Qt canvas with a simple diagram
    canvas = create_qt_canvas(600, 400, "Qt Canvas Test")
    
    # Draw test elements
    canvas.draw_circle((100, 100), 30, {'color': 'black', 'width': 2.0})
    canvas.draw_oval(200, 50, 350, 150, {'color': 'blue', 'width': 1.5})
    canvas.draw_line((100, 100), (275, 100), {'color': 'red', 'width': 3.0})
    canvas.draw_text("Qt Test", (400, 100), {'font_size': 16, 'color': 'green'})
    
    canvas.show()
    canvas.run()
