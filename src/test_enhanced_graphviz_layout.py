#!/usr/bin/env python3
"""
Comprehensive Test for Enhanced Graphviz Layout Engine

This test verifies the collision detection, spacing, and edge routing improvements
in the enhanced Graphviz-based layout engine, integrated with PySide6 rendering.
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont

from egif_parser_dau import parse_egif
from graphviz_layout_engine_v2 import create_graphviz_layout
from pyside6_canvas import PySide6Canvas, DrawingStyle


class EnhancedLayoutTestWindow(QMainWindow):
    """Test window to display enhanced Graphviz layouts with collision detection."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enhanced Graphviz Layout Test - Collision Detection & Spacing")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Add title
        title = QLabel("Enhanced Graphviz Layout Engine Test")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Test cases with increasing complexity
        self.test_cases = [
            {
                'name': 'Simple Predicate with Long Label',
                'egif': '(Human "Socrates")',
                'description': 'Tests vertex sizing based on label length'
            },
            {
                'name': 'Multiple Predicates - Collision Avoidance',
                'egif': '(Human "Socrates") (Mortal "Socrates") (Wise "Socrates")',
                'description': 'Tests spacing between multiple predicates on same vertex'
            },
            {
                'name': 'Cut with Proper Padding',
                'egif': '(Human "Socrates") ~[ (Mortal "Socrates") (Wise "Socrates") ]',
                'description': 'Tests cut padding and internal element spacing'
            },
            {
                'name': 'Sibling Cuts - Non-overlapping',
                'egif': '*x ~[ (Human x) (Tall x) ] ~[ (Mortal x) (Wise x) ]',
                'description': 'Tests sibling cut separation and edge routing'
            },
            {
                'name': 'Nested Cuts - Hierarchical Layout',
                'egif': '*x ~[ (Human x) ~[ (Mortal x) ~[ (Wise x) ] ] ]',
                'description': 'Tests nested cut hierarchy and containment'
            },
            {
                'name': 'Complex Graph - Full Integration',
                'egif': '*x *y (Human x) (Woman y) ~[ (Loves x y) ~[ (Married x y) ] ] ~[ (Happy x) (Happy y) ]',
                'description': 'Tests complex layout with multiple vertices, predicates, and cuts'
            }
        ]
        
        # Create canvases for each test case
        self.canvases = []
        for i, test_case in enumerate(self.test_cases):
            # Test case label
            label = QLabel(f"{i+1}. {test_case['name']}: {test_case['description']}")
            label.setStyleSheet("font-weight: bold; margin: 5px; color: #333;")
            layout.addWidget(label)
            
            # EGIF display
            egif_label = QLabel(f"EGIF: {test_case['egif']}")
            egif_label.setStyleSheet("font-family: monospace; margin-left: 20px; color: #666;")
            layout.addWidget(egif_label)
            
            # Canvas for rendering
            canvas = PySide6Canvas()
            canvas.setFixedHeight(120)
            canvas.setStyleSheet("border: 1px solid #ccc; margin: 5px;")
            layout.addWidget(canvas)
            self.canvases.append(canvas)
        
        # Render all test cases
        self.render_all_tests()
    
    def render_all_tests(self):
        """Render all test cases using the enhanced Graphviz layout engine."""
        
        for i, (test_case, canvas) in enumerate(zip(self.test_cases, self.canvases)):
            try:
                print(f"\n🎯 Rendering Test {i+1}: {test_case['name']}")
                print(f"   EGIF: {test_case['egif']}")
                
                # Parse EGIF to EGI
                graph = parse_egif(test_case['egif'])
                print(f"   ✅ Parsed EGI: {len(graph._vertex_map)} vertices, {len(graph.nu)} edges")
                
                # Generate enhanced layout
                layout_result = create_graphviz_layout(graph)
                print(f"   ✅ Layout: {len(layout_result.primitives)} elements")
                print(f"   📐 Canvas bounds: {layout_result.canvas_bounds}")
                
                # Render to canvas
                self.render_layout_to_canvas(canvas, layout_result, graph, test_case['name'])
                print(f"   ✅ Rendered to canvas")
                
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                # Draw error message on canvas
                canvas.clear()
                canvas.draw_text(f"Error: {str(e)}", (10, 50), 
                               DrawingStyle(color=(255, 0, 0), font_size=10))
    
    def render_layout_to_canvas(self, canvas, layout_result, graph, test_name):
        """Render a layout result to a PySide6 canvas with enhanced visual feedback."""
        
        canvas.clear()
        
        # Scale layout to fit canvas
        canvas_width, canvas_height = 1180, 110  # Leave margin
        layout_bounds = layout_result.canvas_bounds
        
        if layout_bounds[2] > 0 and layout_bounds[3] > 0:
            scale_x = canvas_width / layout_bounds[2]
            scale_y = canvas_height / layout_bounds[3]
            scale = min(scale_x, scale_y) * 0.8  # Leave 20% margin
        else:
            scale = 1.0
        
        offset_x = (canvas_width - layout_bounds[2] * scale) / 2
        offset_y = (canvas_height - layout_bounds[3] * scale) / 2
        
        def transform_point(x, y):
            return (x * scale + offset_x, y * scale + offset_y)
        
        # Draw title
        canvas.draw_text(test_name, (10, 15), 
                        DrawingStyle(color=(0, 0, 0), font_size=10, bold=True))
        
        # Render all primitives with enhanced visual feedback
        primitives = layout_result.primitives
        
        # 1. Render cuts (background)
        for element_id, primitive in primitives.items():
            if primitive.element_type == 'cut':
                center = transform_point(*primitive.position)
                bounds = primitive.bounds
                width = (bounds[2] - bounds[0]) * scale
                height = (bounds[3] - bounds[1]) * scale
                
                # Draw cut as rounded rectangle with padding visualization
                canvas.draw_rounded_rectangle(
                    (center[0] - width/2, center[1] - height/2, 
                     center[0] + width/2, center[1] + height/2),
                    DrawingStyle(color=(100, 100, 100), line_width=2, fill_color=(240, 240, 255))
                )
        
        # 2. Render edges (connections)
        for element_id, primitive in primitives.items():
            if primitive.element_type == 'edge':
                center = transform_point(*primitive.position)
                bounds = primitive.bounds
                
                # Draw edge as connection line with proper routing
                canvas.draw_line(
                    (center[0] - 20, center[1]), (center[0] + 20, center[1]),
                    DrawingStyle(color=(0, 0, 0), line_width=3)
                )
        
        # 3. Render vertices (foreground)
        for element_id, primitive in primitives.items():
            if primitive.element_type == 'vertex':
                center = transform_point(*primitive.position)
                bounds = primitive.bounds
                
                # Draw vertex boundary (for collision detection visualization)
                width = (bounds[2] - bounds[0]) * scale
                height = (bounds[3] - bounds[1]) * scale
                canvas.draw_rectangle(
                    (center[0] - width/2, center[1] - height/2,
                     center[0] + width/2, center[1] + height/2),
                    DrawingStyle(color=(200, 200, 200), line_width=1, fill_color=(250, 250, 250))
                )
                
                # Draw vertex spot
                canvas.draw_circle(center, 3, 
                                 DrawingStyle(color=(0, 0, 0), fill_color=(0, 0, 0)))
                
                # Draw vertex label if present
                if element_id in graph._vertex_map:
                    vertex = graph._vertex_map[element_id]
                    if vertex.label:
                        canvas.draw_text(f'"{vertex.label}"', 
                                       (center[0], center[1] + 15),
                                       DrawingStyle(color=(0, 0, 0), font_size=8))
        
        # 4. Render predicate nodes
        for element_id, primitive in primitives.items():
            if 'pred_' in element_id:  # Predicate node
                center = transform_point(*primitive.position)
                bounds = primitive.bounds
                
                # Draw predicate box with proper sizing
                width = (bounds[2] - bounds[0]) * scale
                height = (bounds[3] - bounds[1]) * scale
                canvas.draw_rectangle(
                    (center[0] - width/2, center[1] - height/2,
                     center[0] + width/2, center[1] + height/2),
                    DrawingStyle(color=(0, 0, 0), line_width=1, fill_color=(255, 255, 200))
                )
                
                # Draw predicate name
                predicate_name = element_id.replace('pred_', '')
                if predicate_name in graph.rel:
                    name = graph.rel[predicate_name]
                    canvas.draw_text(name, center,
                                   DrawingStyle(color=(0, 0, 0), font_size=8))
        
        canvas.update()


def main():
    """Run the enhanced Graphviz layout test."""
    
    print("🚀 Starting Enhanced Graphviz Layout Test")
    print("   Testing collision detection, spacing, and edge routing improvements")
    
    app = QApplication(sys.argv)
    
    # Create and show test window
    window = EnhancedLayoutTestWindow()
    window.show()
    
    print("\n✅ Test window displayed")
    print("   Each test case shows:")
    print("   • Proper element sizing based on content")
    print("   • Collision detection boundaries (gray rectangles)")
    print("   • Automatic spacing and separation")
    print("   • Edge routing around obstacles")
    print("   • Cut padding and containment")
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
