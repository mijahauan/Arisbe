"""
Professional Qt-Based Constraint Layout Demo for Existential Graphs

This demonstration showcases the constraint-based layout engine with high-quality
Qt rendering, replacing Tkinter for professional diagram output.
"""

import sys
sys.path.insert(0, '.')

from egif_parser_dau import parse_egif
from constraint_layout_integration import ConstraintLayoutIntegration
from diagram_renderer_clean import CleanDiagramRenderer, DrawingStyle
from pyside6_canvas import create_qt_canvas
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QComboBox
from PySide6.QtCore import Qt
import time

class QtEGDemoWindow(QMainWindow):
    """Professional Qt-based EG demonstration window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎯 Constraint-Based Layout Engine Demo - Qt Professional Rendering")
        self.setGeometry(100, 100, 1000, 700)
        
        # Test cases for demonstration
        self.test_cases = {
            "Simple Predicate": '(Human "Socrates")',
            "Negation": '~[ (Mortal "Socrates") ]',
            "Sibling Cuts": '~[ (P "x") ] ~[ (Q "x") ]',
            "Double Negation": '~[ ~[ (Human "Socrates") ] ]',
            "Mixed Cut and Sheet": '*x (Human x) ~[ (Mortal x) ]',
            "Nested Cuts": '~[ ~[ ~[ (P "x") ] ] ]',
            "Binary Relation": '(Loves "John" "Mary")',
            "Complex Example": '*x *y (Human x) (Human y) ~[ (Loves x y) ]'
        }
        
        self.current_case = "Sibling Cuts"
        self.layout_engine = ConstraintLayoutIntegration()
        
        # Create UI
        self.setup_ui()
        
        # Initial render
        self.render_current_case()
    
    def setup_ui(self):
        """Set up the Qt user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Control panel
        control_panel = QHBoxLayout()
        
        # Test case selector
        control_panel.addWidget(QLabel("Test Case:"))
        self.case_selector = QComboBox()
        self.case_selector.addItems(list(self.test_cases.keys()))
        self.case_selector.setCurrentText(self.current_case)
        self.case_selector.currentTextChanged.connect(self.on_case_changed)
        control_panel.addWidget(self.case_selector)
        
        # Navigation buttons
        prev_button = QPushButton("◀ Previous")
        prev_button.clicked.connect(self.previous_case)
        control_panel.addWidget(prev_button)
        
        next_button = QPushButton("Next ▶")
        next_button.clicked.connect(self.next_case)
        control_panel.addWidget(next_button)
        
        refresh_button = QPushButton("🔄 Refresh")
        refresh_button.clicked.connect(self.render_current_case)
        control_panel.addWidget(refresh_button)
        
        control_panel.addStretch()
        
        # Status label
        self.status_label = QLabel("Ready")
        control_panel.addWidget(self.status_label)
        
        main_layout.addLayout(control_panel)
        
        # EGIF display
        self.egif_label = QLabel()
        self.egif_label.setStyleSheet("font-family: monospace; background-color: #f0f0f0; padding: 10px; border: 1px solid #ccc;")
        main_layout.addWidget(self.egif_label)
        
        # Canvas container
        canvas_container = QWidget()
        canvas_container.setMinimumHeight(500)
        canvas_container.setStyleSheet("border: 1px solid #ccc; background-color: white;")
        main_layout.addWidget(canvas_container)
        
        # Store canvas container for later canvas insertion
        self.canvas_container = canvas_container
        self.canvas_layout = QVBoxLayout(canvas_container)
        
    def on_case_changed(self, case_name: str):
        """Handle test case selection change."""
        self.current_case = case_name
        self.render_current_case()
    
    def previous_case(self):
        """Navigate to previous test case."""
        cases = list(self.test_cases.keys())
        current_index = cases.index(self.current_case)
        previous_index = (current_index - 1) % len(cases)
        self.case_selector.setCurrentText(cases[previous_index])
    
    def next_case(self):
        """Navigate to next test case."""
        cases = list(self.test_cases.keys())
        current_index = cases.index(self.current_case)
        next_index = (current_index + 1) % len(cases)
        self.case_selector.setCurrentText(cases[next_index])
    
    def render_current_case(self):
        """Render the current test case with Qt."""
        try:
            start_time = time.time()
            
            # Get EGIF and parse
            egif = self.test_cases[self.current_case]
            self.egif_label.setText(f"EGIF: {egif}")
            
            self.status_label.setText("Parsing...")
            QApplication.processEvents()
            
            graph = parse_egif(egif)
            
            self.status_label.setText("Generating layout...")
            QApplication.processEvents()
            
            # Generate constraint-based layout
            layout_result = self.layout_engine.layout_graph(graph)
            
            self.status_label.setText("Rendering with Qt...")
            QApplication.processEvents()
            
            # Clear previous canvas
            if hasattr(self, 'current_canvas_widget'):
                self.canvas_layout.removeWidget(self.current_canvas_widget)
                self.current_canvas_widget.deleteLater()
            
            # Create new Qt canvas widget for embedding
            from pyside6_canvas import EGCanvasWidget
            canvas_widget = EGCanvasWidget(800, 400)
            self.current_canvas_widget = canvas_widget
            self.canvas_layout.addWidget(canvas_widget)
            
            # Render with professional Qt quality
            self.render_layout_to_qt_widget(layout_result, canvas_widget)
            
            # Update canvas
            canvas_widget.update()
            
            end_time = time.time()
            self.status_label.setText(f"✅ Rendered successfully in {end_time - start_time:.3f}s")
            
        except Exception as e:
            self.status_label.setText(f"❌ Error: {str(e)}")
            print(f"Rendering error: {e}")
    
    def render_layout_to_qt_widget(self, layout_result, canvas_widget):
        """Render layout result directly to Qt widget."""
        elements = []
        
        print(f"🎨 Rendering {len(layout_result.primitives)} primitives to Qt widget...")
        
        # Define professional drawing styles using correct API
        styles = {
            'vertex': DrawingStyle(
                color=(0, 0, 0),  # Black RGB tuple
                fill_color=(0, 0, 0),  # Black fill
                line_width=1.0
            ),
            'edge': DrawingStyle(
                color=(0, 0, 0),  # Black RGB tuple
                line_width=1.5
            ),
            'cut': DrawingStyle(
                color=(0, 0, 0),  # Black RGB tuple
                line_width=2.0,
                fill_color=None
            ),
            'line_of_identity': DrawingStyle(
                color=(0, 0, 0),  # Black RGB tuple
                line_width=4.0  # Heavy line for LoI
            )
        }
        
        # Render all primitives
        for primitive in layout_result.primitives.values():
            if primitive.element_type == 'vertex':
                # Render vertex as filled circle (professional size)
                center = primitive.position
                radius = 4.0  # Professional vertex size
                style = styles['vertex']
                
                element = {
                    'type': 'circle',
                    'center': center,
                    'radius': radius,
                    'style': {
                        'color': style.color,
                        'fill_color': style.fill_color,
                        'width': style.line_width
                    }
                }
                elements.append(element)
            
            elif primitive.element_type == 'edge':
                # Render edge text
                position = primitive.position
                text = primitive.text
                style = styles['edge']
                
                element = {
                    'type': 'text',
                    'text': text,
                    'position': position,
                    'style': {
                        'color': style.color,
                        'font_size': style.font_size,
                        'font_family': style.font_family
                    }
                }
                elements.append(element)
            
            elif primitive.element_type == 'cut':
                # Render cut as precise oval
                x_min, y_min, x_max, y_max = primitive.bounds
                style = styles['cut']
                
                element = {
                    'type': 'oval',
                    'bounds': (x_min, y_min, x_max, y_max),
                    'style': {
                        'color': style.color,
                        'width': style.line_width,
                        'fill_color': style.fill_color
                    }
                }
                elements.append(element)
            
            elif primitive.element_type == 'line':
                # Render connection lines
                start = primitive.start
                end = primitive.end
                
                # Determine line style based on context
                if hasattr(primitive, 'line_type') and primitive.line_type == 'identity':
                    style = styles['line_of_identity']
                else:
                    style = styles['edge']
                
                element = {
                    'type': 'line',
                    'start': start,
                    'end': end,
                    'style': {
                        'color': style.color,
                        'width': style.line_width
                    }
                }
                elements.append(element)
        
        # Set elements for Qt widget rendering
        canvas_widget.elements = elements


def main():
    """Run the Qt-based constraint layout demonstration."""
    app = QApplication(sys.argv)
    
    # Set application style for professional appearance
    app.setStyle('Fusion')
    
    # Create and show demo window
    demo_window = QtEGDemoWindow()
    demo_window.show()
    
    # Run Qt event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
