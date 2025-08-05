"""
Simple Qt Debug Demo - Minimal test to verify Qt rendering works
"""

import sys
sys.path.insert(0, '.')

from egif_parser_dau import parse_egif
from constraint_layout_integration import ConstraintLayoutIntegration
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget
from PySide6.QtGui import QPainter, QPen, QBrush, QColor
from PySide6.QtCore import Qt

class SimpleQtCanvas(QWidget):
    """Minimal Qt canvas for debugging."""
    
    def __init__(self, width=800, height=600):
        super().__init__()
        self.setFixedSize(width, height)
        self.setStyleSheet("background-color: white;")
        
        # Store layout result for rendering
        self.layout_result = None
        
    def set_layout_result(self, layout_result):
        """Set the layout result to render."""
        self.layout_result = layout_result
        print(f"🎨 Canvas received {len(layout_result.primitives)} primitives")
        self.update()  # Trigger repaint
        
    def paintEvent(self, event):
        """Paint the layout result."""
        painter = QPainter(self)
        
        # Enable high-quality rendering
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        
        # Clear background
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        
        if self.layout_result is None:
            # Draw a test pattern to verify Qt is working
            painter.setPen(QPen(QColor(255, 0, 0), 2.0))
            painter.drawText(50, 50, "Qt Canvas - No Layout Data")
            painter.drawCircle(100, 100, 30)
            painter.drawLine(50, 150, 200, 150)
            return
        
        print(f"🖌️ Painting {len(self.layout_result.primitives)} primitives...")
        
        # Render each primitive
        for prim_id, primitive in self.layout_result.primitives.items():
            print(f"  Rendering {primitive.element_type} {prim_id}")
            
            if primitive.element_type == 'cut':
                # Draw cut as oval
                x_min, y_min, x_max, y_max = primitive.bounds
                painter.setPen(QPen(QColor(0, 0, 0), 2.0))
                painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
                painter.drawEllipse(x_min, y_min, x_max - x_min, y_max - y_min)
                print(f"    Drew cut oval at ({x_min}, {y_min}) to ({x_max}, {y_max})")
                
            elif primitive.element_type == 'vertex':
                # Draw vertex as filled circle
                x, y = primitive.position
                painter.setPen(QPen(QColor(0, 0, 0), 1.0))
                painter.setBrush(QBrush(QColor(0, 0, 0)))
                painter.drawEllipse(x - 4, y - 4, 8, 8)
                print(f"    Drew vertex at ({x}, {y})")
                
            elif primitive.element_type == 'edge':
                # Draw edge text
                x, y = primitive.position
                text = getattr(primitive, 'text', 'EDGE')
                painter.setPen(QPen(QColor(0, 0, 0), 1.0))
                painter.drawText(x, y, text)
                print(f"    Drew edge text '{text}' at ({x}, {y})")
                
            elif primitive.element_type == 'line':
                # Draw connection line
                if hasattr(primitive, 'start') and hasattr(primitive, 'end'):
                    start_x, start_y = primitive.start
                    end_x, end_y = primitive.end
                    painter.setPen(QPen(QColor(0, 0, 0), 2.0))
                    painter.drawLine(start_x, start_y, end_x, end_y)
                    print(f"    Drew line from ({start_x}, {start_y}) to ({end_x}, {end_y})")


class SimpleQtDemo(QMainWindow):
    """Simple Qt demo window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔧 Simple Qt Debug Demo")
        self.setGeometry(100, 100, 900, 700)
        
        # Create canvas
        self.canvas = SimpleQtCanvas(800, 600)
        self.setCentralWidget(self.canvas)
        
        # Test with a simple EGIF
        self.test_rendering()
        
    def test_rendering(self):
        """Test rendering with a simple EGIF."""
        try:
            print("🔧 Testing simple EGIF rendering...")
            
            # Parse simple EGIF
            egif = '~[ (P "x") ] ~[ (Q "x") ]'
            print(f"EGIF: {egif}")
            
            graph = parse_egif(egif)
            print(f"✅ Parsed: {len(graph.V)} vertices, {len(graph.E)} edges, {len(graph.Cut)} cuts")
            
            # Generate layout
            layout_engine = ConstraintLayoutIntegration()
            layout_result = layout_engine.layout_graph(graph)
            print(f"✅ Layout: {len(layout_result.primitives)} primitives")
            
            # Set layout result in canvas
            self.canvas.set_layout_result(layout_result)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Run simple Qt demo."""
    app = QApplication(sys.argv)
    
    demo = SimpleQtDemo()
    demo.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
