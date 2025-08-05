#!/usr/bin/env python3
"""
QtDiagramCanvas Dau-Compliant Rendering Validation

This test validates that our QtDiagramCanvas correctly renders Existential Graphs
with full Dau convention compliance:
- Heavy identity lines (4.0 width)
- Fine cut boundaries (1.0 width) 
- Prominent vertex spots (3.5 radius)
- Enhanced hook lines (1.5 width)
- Professional spacing and layout

Phase 1A: Establish rock-solid Dau-compliant rendering foundation
"""

import sys
import os
sys.path.insert(0, 'src')

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel
from PySide6.QtCore import Qt
from qt_diagram_canvas import QtDiagramCanvas, QtDiagramCanvasIntegration, DauRenderingStyle

class DauRenderingValidator(QMainWindow):
    """Validation window for Dau-compliant rendering."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎯 Phase 1A: QtDiagramCanvas Dau-Compliant Rendering Validation")
        self.setGeometry(100, 100, 1200, 800)
        
        # Test cases for Dau convention validation
        self.test_cases = [
            {
                "name": "Heavy Identity Line",
                "description": "4.0 width heavy line connecting vertex to predicate",
                "elements": self._create_identity_line_test
            },
            {
                "name": "Fine Cut Boundary", 
                "description": "1.0 width fine oval boundary",
                "elements": self._create_cut_boundary_test
            },
            {
                "name": "Prominent Vertex Spots",
                "description": "3.5 radius black filled circles",
                "elements": self._create_vertex_spots_test
            },
            {
                "name": "Enhanced Hook Lines",
                "description": "1.5 width predicate connection lines",
                "elements": self._create_hook_lines_test
            },
            {
                "name": "Complete EG Diagram",
                "description": "All elements together with proper spacing",
                "elements": self._create_complete_diagram_test
            }
        ]
        
        self.current_test = 0
        self.setup_ui()
        self.render_current_test()
    
    def setup_ui(self):
        """Set up the validation UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("QtDiagramCanvas Dau-Compliant Rendering Validation")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Test controls
        controls_layout = QHBoxLayout()
        
        self.prev_button = QPushButton("← Previous Test")
        self.prev_button.clicked.connect(self.previous_test)
        controls_layout.addWidget(self.prev_button)
        
        self.test_label = QLabel()
        self.test_label.setAlignment(Qt.AlignCenter)
        self.test_label.setStyleSheet("font-weight: bold; margin: 0 20px;")
        controls_layout.addWidget(self.test_label)
        
        self.next_button = QPushButton("Next Test →")
        self.next_button.clicked.connect(self.next_test)
        controls_layout.addWidget(self.next_button)
        
        layout.addLayout(controls_layout)
        
        # Test description
        self.description_label = QLabel()
        self.description_label.setAlignment(Qt.AlignCenter)
        self.description_label.setStyleSheet("margin: 10px; color: #666;")
        layout.addWidget(self.description_label)
        
        # Canvas
        self.canvas = QtDiagramCanvas(width=800, height=500)
        layout.addWidget(self.canvas)
        
        # Validation info
        validation_info = QLabel(
            "✅ Validation Criteria:\n"
            "• Heavy identity lines: 4.0 width (clearly heavier than cuts)\n"
            "• Fine cut boundaries: 1.0 width (fine-drawn appearance)\n" 
            "• Prominent vertex spots: 3.5 radius (clear identity markers)\n"
            "• Enhanced hook lines: 1.5 width (visible predicate connections)\n"
            "• Professional spacing and anti-aliased rendering"
        )
        validation_info.setStyleSheet("background: #f0f0f0; padding: 10px; margin: 10px;")
        layout.addWidget(validation_info)
        
        # Save button
        save_button = QPushButton("💾 Save Current Test as PNG")
        save_button.clicked.connect(self.save_current_test)
        layout.addWidget(save_button)
    
    def render_current_test(self):
        """Render the current test case."""
        test_case = self.test_cases[self.current_test]
        
        # Update UI
        self.test_label.setText(f"Test {self.current_test + 1}/{len(self.test_cases)}: {test_case['name']}")
        self.description_label.setText(test_case['description'])
        
        # Clear and render
        self.canvas.clear_elements()
        test_case['elements']()
        self.canvas.render_complete()
    
    def _create_identity_line_test(self):
        """Test heavy identity line rendering."""
        # Vertex at left
        self.canvas.add_vertex((100, 250), "vertex1")
        
        # Heavy identity line (should be 4.0 width)
        self.canvas.add_identity_line((100, 250), (300, 250), "identity1")
        
        # Predicate at right
        self.canvas.add_predicate_text((320, 250), "Human", "pred1")
        
        # Hook line to predicate
        self.canvas.add_hook_line((300, 250), (320, 250), "hook1")
        
        # Reference fine line for comparison
        self.canvas.add_element({
            "element_type": "line",
            "element_id": "ref_line",
            "coordinates": [(100, 300), (300, 300)],
            "style_override": {"line_width": 1.0}
        })
        
        # Labels
        self.canvas.add_predicate_text((200, 220), "Heavy Identity Line (4.0 width)", "label1")
        self.canvas.add_predicate_text((200, 320), "Fine Reference Line (1.0 width)", "label2")
    
    def _create_cut_boundary_test(self):
        """Test fine cut boundary rendering."""
        # Cut boundary (should be 1.0 width, fine appearance)
        self.canvas.add_cut((150, 150, 300, 200), "cut1")
        
        # Content inside cut
        self.canvas.add_vertex((200, 175), "vertex1")
        self.canvas.add_predicate_text((250, 175), "Mortal", "pred1")
        self.canvas.add_hook_line((200, 175), (250, 175), "hook1")
        
        # Label
        self.canvas.add_predicate_text((225, 120), "Fine Cut Boundary (1.0 width)", "label1")
    
    def _create_vertex_spots_test(self):
        """Test prominent vertex spot rendering."""
        positions = [(150, 200), (250, 200), (350, 200), (450, 200)]
        radii = [2.0, 2.5, 3.0, 3.5]  # Show progression to Dau's 3.5
        
        for i, (pos, radius) in enumerate(zip(positions, radii)):
            # Override radius for comparison
            self.canvas.add_element({
                "element_type": "vertex",
                "element_id": f"vertex{i}",
                "coordinates": [pos],
                "style_override": {"vertex_radius": radius}
            })
            
            # Label
            self.canvas.add_predicate_text((pos[0], pos[1] + 40), f"{radius}r", f"label{i}")
        
        self.canvas.add_predicate_text((300, 150), "Vertex Spot Radius Progression → Dau's 3.5", "title")
    
    def _create_hook_lines_test(self):
        """Test enhanced hook line rendering."""
        # Vertex
        self.canvas.add_vertex((150, 250), "vertex1")
        
        # Multiple predicates with hook lines of different widths
        predicates = [
            ("Pred1", (250, 200), 1.0),
            ("Pred2", (250, 250), 1.5),  # Dau's enhanced width
            ("Pred3", (250, 300), 2.0)
        ]
        
        for i, (text, pos, width) in enumerate(predicates):
            self.canvas.add_predicate_text(pos, text, f"pred{i}")
            self.canvas.add_element({
                "element_type": "hook_line",
                "element_id": f"hook{i}",
                "coordinates": [(150, 250), pos],
                "style_override": {"line_width": width}
            })
            
            # Width label
            self.canvas.add_predicate_text((pos[0] + 50, pos[1]), f"{width}w", f"width_label{i}")
        
        self.canvas.add_predicate_text((200, 150), "Hook Line Width Comparison → Dau's 1.5", "title")
    
    def _create_complete_diagram_test(self):
        """Test complete EG diagram with all Dau conventions."""
        # Sheet-level predicate
        self.canvas.add_vertex((100, 200), "vertex_socrates")
        self.canvas.add_identity_line((100, 200), (180, 200), "identity1")
        self.canvas.add_predicate_text((200, 200), "Human", "pred_human")
        self.canvas.add_hook_line((180, 200), (200, 200), "hook1")
        
        # Cut with negated content
        self.canvas.add_cut((250, 150, 200, 100), "cut1")
        
        # Inside cut: same individual with different predicate
        self.canvas.add_vertex((300, 200), "vertex_socrates2")
        self.canvas.add_identity_line((300, 200), (380, 200), "identity2")
        self.canvas.add_predicate_text((400, 200), "Mortal", "pred_mortal")
        self.canvas.add_hook_line((380, 200), (400, 200), "hook2")
        
        # Connect the identity lines (same individual)
        self.canvas.add_identity_line((180, 200), (300, 200), "identity_bridge")
        
        # Label
        self.canvas.add_predicate_text((300, 100), 'Complete EG: (Human "Socrates") ~[ (Mortal "Socrates") ]', "title")
    
    def previous_test(self):
        """Go to previous test."""
        self.current_test = (self.current_test - 1) % len(self.test_cases)
        self.render_current_test()
    
    def next_test(self):
        """Go to next test."""
        self.current_test = (self.current_test + 1) % len(self.test_cases)
        self.render_current_test()
    
    def save_current_test(self):
        """Save current test as PNG."""
        test_name = self.test_cases[self.current_test]['name'].replace(' ', '_').lower()
        filename = f"qt_dau_validation_{test_name}.png"
        self.canvas.save_to_file(filename)
        print(f"✅ Saved: {filename}")

def main():
    """Run the Dau-compliant rendering validation."""
    print("🎯 Phase 1A: QtDiagramCanvas Dau-Compliant Rendering Validation")
    print("=" * 60)
    print("Validating:")
    print("• Heavy identity lines (4.0 width)")
    print("• Fine cut boundaries (1.0 width)")
    print("• Prominent vertex spots (3.5 radius)")
    print("• Enhanced hook lines (1.5 width)")
    print("• Professional Qt rendering quality")
    print()
    
    app = QApplication(sys.argv)
    
    # Set application style for professional appearance
    app.setStyle('Fusion')
    
    validator = DauRenderingValidator()
    validator.show()
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
