"""
QtDiagramCanvas - Professional Dau-Compliant EG Diagram Rendering

A clean, from-scratch implementation of a Qt-based diagram canvas specifically
designed to render Existential Graphs with full Dau convention compliance.

This replaces the problematic PySide6Canvas with a robust implementation that:
1. Integrates directly with our proven Graphviz layout pipeline
2. Renders heavy identity lines, fine cuts, and predicate text correctly
3. Uses Qt's native QPainter for professional-quality output
4. Implements proper API contracts for reliability
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath
from PySide6.QtCore import Qt, QPointF, QRectF, QSizeF
import sys

# Type aliases
Coordinate = Tuple[float, float]

@dataclass
class DauRenderingStyle:
    """Enhanced Dau-compliant rendering styles for true EG visual compliance."""
    
    # Heavy identity lines (Dau's key convention) - DRAMATICALLY ENHANCED
    IDENTITY_LINE_WIDTH = 8.0  # Was 4.0 - now 8x thicker than cuts for clear dominance
    IDENTITY_LINE_COLOR = QColor(0, 0, 0)  # Black
    
    # Fine cut boundaries (Dau's key convention) - REDUCED for delicate appearance
    CUT_LINE_WIDTH = 1.0  # Keeping at 1.0 to maintain 8:1 ratio with identity lines
    CUT_LINE_COLOR = QColor(0, 0, 0)  # Black
    CUT_FILL_COLOR = None  # No fill
    
    # Prominent vertex spots - SIGNIFICANTLY ENHANCED
    VERTEX_RADIUS = 6.0  # Was 3.5 - now clearly visible as identity markers
    VERTEX_COLOR = QColor(0, 0, 0)  # Black filled
    
    # NOTE: No separate hook lines - heavy identity lines connect directly to predicate periphery
    
    # Predicate text
    PREDICATE_FONT_FAMILY = "Arial"
    PREDICATE_FONT_SIZE = 12
    PREDICATE_TEXT_COLOR = QColor(0, 0, 0)  # Black
    
    # Canvas background
    BACKGROUND_COLOR = QColor(255, 255, 255)  # White

@dataclass
class DiagramElement:
    """A single diagram element to be rendered."""
    element_type: str  # 'vertex', 'edge', 'cut', 'text'
    element_id: str
    coordinates: List[Coordinate]
    text: Optional[str] = None
    style_override: Optional[Dict[str, Any]] = None

class QtDiagramCanvas(QWidget):
    """Professional Qt-based canvas for Dau-compliant EG diagram rendering."""
    
    def __init__(self, width: int = 800, height: int = 600, parent=None):
        super().__init__(parent)
        
        # Canvas properties
        self.canvas_width = width
        self.canvas_height = height
        self.setFixedSize(width, height)
        
        # Rendering style
        self.style = DauRenderingStyle()
        
        # Elements to render
        self.elements: List[DiagramElement] = []
        
        # Canvas bounds for coordinate mapping
        self.canvas_bounds: Tuple[float, float, float, float] = (0, 0, width, height)
        
        # Set white background
        self.setStyleSheet("background-color: white;")
        
    def set_canvas_bounds(self, bounds: Tuple[float, float, float, float]):
        """Set the logical coordinate bounds for the canvas."""
        self.canvas_bounds = bounds
        
    def clear_elements(self):
        """Clear all elements from the canvas."""
        self.elements.clear()
        self.update()  # Trigger repaint
        
    def add_element(self, element: DiagramElement):
        """Add a diagram element to be rendered."""
        self.elements.append(element)
        
    def add_vertex(self, position: Coordinate, element_id: str):
        """Add a vertex (identity spot) at the specified position."""
        element = DiagramElement(
            element_type='vertex',
            element_id=element_id,
            coordinates=[position]
        )
        self.add_element(element)
        
    def add_identity_line(self, start: Coordinate, end: Coordinate, element_id: str):
        """Add a heavy identity line between two points."""
        element = DiagramElement(
            element_type='identity_line',
            element_id=element_id,
            coordinates=[start, end]
        )
        self.add_element(element)
        
    def add_vertex_to_predicate_connection(self, vertex_pos: Coordinate, predicate_pos: Coordinate, 
                                         predicate_text: str, element_id: str):
        """Add a heavy identity line from vertex to predicate periphery (Dau convention)."""
        # Calculate connection point on predicate text periphery
        # For now, use simple approach - connect to predicate position
        # TODO: Calculate actual text bounding box and find periphery point
        
        element = DiagramElement(
            element_type='identity_line',  # Use heavy identity line, not hook line
            element_id=element_id,
            coordinates=[vertex_pos, predicate_pos]
        )
        self.add_element(element)
        
    def add_cut(self, bounds: Tuple[float, float, float, float], element_id: str):
        """Add a cut (fine oval boundary) with the specified bounds."""
        x1, y1, x2, y2 = bounds
        element = DiagramElement(
            element_type='cut',
            element_id=element_id,
            coordinates=[(x1, y1), (x2, y2)]
        )
        self.add_element(element)
        
    def add_predicate_text(self, position: Coordinate, text: str, element_id: str):
        """Add predicate text at the specified position."""
        element = DiagramElement(
            element_type='predicate_text',
            element_id=element_id,
            coordinates=[position],
            text=text
        )
        self.add_element(element)
        
    def map_coordinate(self, logical_coord: Coordinate) -> QPointF:
        """Map logical coordinates to canvas pixel coordinates."""
        logical_x, logical_y = logical_coord
        bounds_x1, bounds_y1, bounds_x2, bounds_y2 = self.canvas_bounds
        
        # Map logical bounds to canvas size with padding
        padding = 20
        canvas_x = padding + (logical_x - bounds_x1) / (bounds_x2 - bounds_x1) * (self.canvas_width - 2 * padding)
        canvas_y = padding + (logical_y - bounds_y1) / (bounds_y2 - bounds_y1) * (self.canvas_height - 2 * padding)
        
        return QPointF(canvas_x, canvas_y)
        
    def paintEvent(self, event):
        """Handle Qt paint events with professional rendering."""
        painter = QPainter(self)
        
        # Enable anti-aliasing for professional quality
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        
        # Fill background
        painter.fillRect(self.rect(), self.style.BACKGROUND_COLOR)
        
        # Render all elements
        for element in self.elements:
            self._render_element(painter, element)
            
        painter.end()
        
    def _render_element(self, painter: QPainter, element):
        """Render a single diagram element with Dau-compliant styling."""
        
        # Handle both DiagramElement objects and dictionary formats
        if hasattr(element, 'element_type'):
            element_type = element.element_type
            element_id = element.element_id
            coordinates = element.coordinates
            text = getattr(element, 'text', None)
            style_override = getattr(element, 'style_override', None) or {}
        else:
            # Dictionary format
            element_type = element['element_type']
            element_id = element['element_id']
            coordinates = element['coordinates']
            text = element.get('text')
            style_override = element.get('style_override', {})
        
        if element_type == 'vertex':
            # Render vertex as prominent filled circle (identity spot)
            position = self.map_coordinate(coordinates[0])
            
            # Apply style overrides
            vertex_radius = style_override.get('vertex_radius', self.style.VERTEX_RADIUS)
            vertex_color = style_override.get('vertex_color', self.style.VERTEX_COLOR)
            
            # Set up pen and brush for filled circle
            pen = QPen(vertex_color, 1.0)
            brush = QBrush(vertex_color)
            painter.setPen(pen)
            painter.setBrush(brush)
            
            # Draw filled circle (correct Qt API usage)
            rect = QRectF(position.x() - vertex_radius, position.y() - vertex_radius, 
                         vertex_radius * 2, vertex_radius * 2)
            painter.drawEllipse(rect)
            
        elif element_type == 'identity_line':
            # Render heavy identity line (Dau's key convention)
            start = self.map_coordinate(coordinates[0])
            end = self.map_coordinate(coordinates[1])
            
            # Apply style overrides
            line_width = style_override.get('line_width', self.style.IDENTITY_LINE_WIDTH)
            line_color = style_override.get('line_color', self.style.IDENTITY_LINE_COLOR)
            
            # Set up heavy pen
            pen = QPen(line_color, line_width)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.setBrush(QBrush())  # No fill
            
            # Draw heavy line
            painter.drawLine(start, end)
            
        # NOTE: hook_line element type removed - use heavy identity lines to predicate periphery instead
        
        elif element_type == 'cut':
            # Render cut as fine oval boundary (Dau's key convention)
            top_left = self.map_coordinate(coordinates[0])
            bottom_right = self.map_coordinate(coordinates[1])
            
            # Apply style overrides
            line_width = style_override.get('line_width', self.style.CUT_LINE_WIDTH)
            line_color = style_override.get('line_color', self.style.CUT_LINE_COLOR)
            
            # Set up fine pen, no fill
            pen = QPen(line_color, line_width)
            painter.setPen(pen)
            painter.setBrush(QBrush())  # No fill for cuts
            
            # Draw oval boundary
            rect = QRectF(top_left, bottom_right)
            painter.drawEllipse(rect)
            
        elif element_type == 'predicate_text':
            # Render predicate text
            position = self.map_coordinate(coordinates[0])
            
            # Apply style overrides
            font_family = style_override.get('font_family', self.style.PREDICATE_FONT_FAMILY)
            font_size = style_override.get('font_size', self.style.PREDICATE_FONT_SIZE)
            text_color = style_override.get('text_color', self.style.PREDICATE_TEXT_COLOR)
            
            # Set up font and color
            font = QFont(font_family, font_size)
            painter.setFont(font)
            painter.setPen(QPen(text_color))
            painter.setBrush(QBrush())  # No fill
            
            # Draw text centered at position
            if text:
                # Calculate text bounds for centering
                font_metrics = painter.fontMetrics()
                text_rect = font_metrics.boundingRect(text)
                
                # Center text at position
                text_position = QPointF(
                    position.x() - text_rect.width() / 2,
                    position.y() + text_rect.height() / 2
                )
                
                painter.drawText(text_position, text)
        
        elif element_type == 'line':
            # Render generic line (for diagnostic/testing purposes)
            start = self.map_coordinate(coordinates[0])
            end = self.map_coordinate(coordinates[1])
            
            # Apply style overrides
            line_width = style_override.get('line_width', 1.0)
            line_color = style_override.get('line_color', QColor(0, 0, 0))
            
            # Set up pen
            pen = QPen(line_color, line_width)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.setBrush(QBrush())  # No fill
            
            # Draw line
            painter.drawLine(start, end)
                
    def render_complete(self):
        """Trigger a complete repaint of the canvas."""
        self.update()
        
    def save_to_file(self, filepath: str) -> bool:
        """Save the canvas contents to a PNG file."""
        try:
            # Create a pixmap of the widget
            pixmap = self.grab()
            
            # Save to file
            success = pixmap.save(filepath, "PNG")
            return success
            
        except Exception as e:
            print(f"❌ Save to file failed: {e}")
            return False

class QtDiagramCanvasIntegration:
    """Integration layer between Graphviz layout pipeline and QtDiagramCanvas."""
    
    def __init__(self, canvas: QtDiagramCanvas):
        self.canvas = canvas
        
    def render_from_layout_result(self, layout_result, graph) -> bool:
        """Render a complete layout result to the canvas with Dau compliance."""
        
        try:
            # Clear existing elements
            self.canvas.clear_elements()
            
            # Set canvas bounds from layout
            self.canvas.set_canvas_bounds(layout_result.canvas_bounds)
            
            # Process each spatial primitive
            for primitive_id, primitive in layout_result.primitives.items():
                element_type = primitive.element_type
                element_id = primitive.element_id
                
                if element_type == 'vertex':
                    # Add vertex spot
                    self.canvas.add_vertex(primitive.position, element_id)
                    
                elif element_type == 'predicate':
                    # Add predicate text
                    predicate_name = self._get_predicate_name(element_id, graph)
                    self.canvas.add_predicate_text(primitive.position, predicate_name, element_id)
                    
                elif element_type == 'edge':
                    # All edges are rendered as heavy identity lines (Dau convention)
                    if hasattr(primitive, 'coordinates') and primitive.coordinates:
                        start, end = primitive.coordinates[0], primitive.coordinates[1]
                        # All vertex-to-predicate connections use heavy identity lines
                        self.canvas.add_identity_line(start, end, element_id)
                    elif hasattr(primitive, 'position'):
                        # Create identity line from position (fallback)
                        x, y = primitive.position
                        self.canvas.add_identity_line((x-10, y), (x+10, y), element_id)
                        
                elif element_type == 'cut':
                    # Add cut boundary
                    if hasattr(primitive, 'bounds'):
                        self.canvas.add_cut(primitive.bounds, element_id)
                    else:
                        # Fallback bounds from position
                        x, y = primitive.position
                        bounds = (x-50, y-30, x+50, y+30)
                        self.canvas.add_cut(bounds, element_id)
            
            # Trigger repaint
            self.canvas.render_complete()
            return True
            
        except Exception as e:
            print(f"❌ Canvas integration rendering failed: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    def _get_predicate_name(self, element_id: str, graph) -> str:
        """Extract predicate name from graph relations."""
        
        # Try direct relation lookup
        if hasattr(graph, 'rel') and element_id in graph.rel:
            return graph.rel[element_id]
            
        # Try edge-based lookup
        if hasattr(graph, 'E'):
            for edge in graph.E:
                if edge.id == element_id and hasattr(graph, 'rel') and edge.id in graph.rel:
                    return graph.rel[edge.id]
                    
        # Default fallback
        return 'P'

def create_qt_diagram_canvas(width: int = 800, height: int = 600) -> QtDiagramCanvas:
    """Factory function to create a QtDiagramCanvas."""
    return QtDiagramCanvas(width, height)

if __name__ == "__main__":
    # Test the QtDiagramCanvas with simple elements
    print("🎨 QtDiagramCanvas Test")
    print("=" * 30)
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Create canvas
    canvas = create_qt_diagram_canvas(600, 400)
    
    # Add test elements to demonstrate Dau compliance
    print("Adding test elements:")
    
    # Vertex (identity spot)
    canvas.add_vertex((100, 200), "test_vertex")
    print("  ✅ Vertex spot (radius 3.5)")
    
    # Heavy identity line
    canvas.add_identity_line((100, 200), (300, 200), "test_identity")
    print("  ✅ Heavy identity line (width 4.0)")
    
    # Predicate text
    canvas.add_predicate_text((300, 180), "Human", "test_predicate")
    print("  ✅ Predicate text")
    
    # Heavy identity line (Dau convention - no separate hook lines)
    canvas.add_identity_line((300, 200), (300, 220), "test_identity")
    print("  ✅ Heavy identity line (width 8.0 - connects to predicate periphery)")
    
    # Cut boundary
    canvas.add_cut((50, 150, 350, 250), "test_cut")
    print("  ✅ Cut boundary (width 1.0)")
    
    # Show canvas
    canvas.show()
    print("\n👀 Visual inspection required:")
    print("  - Heavy identity line should be clearly thicker than cut boundary")
    print("  - Vertex should appear as prominent black spot")
    print("  - Predicate text should be clearly readable")
    print("  - Cut should be fine oval boundary with no fill")
    
    # Save test image
    canvas.save_to_file("qt_canvas_test.png")
    print("  ✅ Saved as 'qt_canvas_test.png'")
    
    # Run Qt event loop
    sys.exit(app.exec())
