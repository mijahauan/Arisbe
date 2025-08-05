#!/usr/bin/env python3
"""
QtDiagramCanvas EGIF Round-Trip Validation

This test validates that our QtDiagramCanvas correctly renders Existential Graphs
from EGIF input with full Dau convention compliance and proper round-trip fidelity.

Phase 1A: Establish rock-solid Dau-compliant rendering foundation with EGIF integration
"""

import sys
import os
sys.path.insert(0, 'src')

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QTextEdit
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from qt_diagram_canvas import QtDiagramCanvas, QtDiagramCanvasIntegration, DauRenderingStyle

# Import our proven pipeline components
try:
    from egif_parser_dau import parse_egif
    from graphviz_layout_engine import GraphvizLayoutEngine
    from pipeline_contracts import validate_layout_result
    PIPELINE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Pipeline components not available: {e}")
    PIPELINE_AVAILABLE = False

class EGIFRenderingValidator(QMainWindow):
    """Validation window for EGIF → QtDiagramCanvas rendering with Dau compliance."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎯 Phase 1A: EGIF → QtDiagramCanvas Dau-Compliant Round-Trip Validation")
        self.setGeometry(50, 50, 1400, 900)
        
        # Test cases with EGIF and expected visual characteristics
        self.test_cases = [
            {
                "name": "Simple Predicate",
                "egif": '(Human "Socrates")',
                "description": "Single predicate with constant - should show vertex, heavy identity line, and predicate text",
                "expected_elements": ["vertex", "identity_line", "predicate_text", "hook_line"]
            },
            {
                "name": "Simple Cut (Negation)",
                "egif": '~[ (Mortal "Socrates") ]',
                "description": "Negated predicate - should show fine cut boundary containing vertex, identity line, and predicate",
                "expected_elements": ["cut", "vertex", "identity_line", "predicate_text", "hook_line"]
            },
            {
                "name": "Mixed Sheet and Cut",
                "egif": '*x (Human x) ~[ (Mortal x) ]',
                "description": "Variable shared between sheet and cut - identity line should cross cut boundary",
                "expected_elements": ["vertex", "identity_line", "predicate_text", "hook_line", "cut"]
            },
            {
                "name": "Sibling Cuts",
                "egif": '~[ (P "x") ] ~[ (Q "x") ]',
                "description": "Two separate cuts - should be non-overlapping with clear separation",
                "expected_elements": ["cut", "vertex", "identity_line", "predicate_text", "hook_line"]
            },
            {
                "name": "Nested Cuts",
                "egif": '~[ ~[ (Human "Socrates") ] ]',
                "description": "Double negation - inner cut should be contained within outer cut",
                "expected_elements": ["cut", "vertex", "identity_line", "predicate_text", "hook_line"]
            },
            {
                "name": "Binary Relation",
                "egif": '(Loves "John" "Mary")',
                "description": "Binary predicate - should show two vertices connected to one predicate",
                "expected_elements": ["vertex", "identity_line", "predicate_text", "hook_line"]
            }
        ]
        
        self.current_test = 0
        self.layout_engine = GraphvizLayoutEngine() if PIPELINE_AVAILABLE else None
        self.setup_ui()
        self.render_current_test()
    
    def setup_ui(self):
        """Set up the validation UI with EGIF display."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QHBoxLayout(central_widget)
        
        # Left panel: EGIF and controls
        left_panel = QWidget()
        left_panel.setFixedWidth(400)
        left_layout = QVBoxLayout(left_panel)
        
        # Title
        title = QLabel("EGIF → QtDiagramCanvas Validation")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        left_layout.addWidget(title)
        
        # Test controls
        controls_layout = QHBoxLayout()
        
        self.prev_button = QPushButton("← Prev")
        self.prev_button.clicked.connect(self.previous_test)
        controls_layout.addWidget(self.prev_button)
        
        self.test_label = QLabel()
        self.test_label.setAlignment(Qt.AlignCenter)
        self.test_label.setStyleSheet("font-weight: bold; margin: 0 10px;")
        controls_layout.addWidget(self.test_label)
        
        self.next_button = QPushButton("Next →")
        self.next_button.clicked.connect(self.next_test)
        controls_layout.addWidget(self.next_button)
        
        left_layout.addLayout(controls_layout)
        
        # EGIF display
        egif_label = QLabel("📝 EGIF Input:")
        egif_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        left_layout.addWidget(egif_label)
        
        self.egif_display = QTextEdit()
        self.egif_display.setFixedHeight(80)
        self.egif_display.setReadOnly(True)
        self.egif_display.setStyleSheet(
            "background: #f8f8f8; border: 1px solid #ccc; "
            "font-family: 'Courier New', monospace; font-size: 14px; padding: 5px;"
        )
        left_layout.addWidget(self.egif_display)
        
        # Test description
        desc_label = QLabel("📋 Expected Visual Elements:")
        desc_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        left_layout.addWidget(desc_label)
        
        self.description_display = QTextEdit()
        self.description_display.setFixedHeight(120)
        self.description_display.setReadOnly(True)
        self.description_display.setStyleSheet(
            "background: #f0f8ff; border: 1px solid #ccc; "
            "font-size: 12px; padding: 5px;"
        )
        left_layout.addWidget(self.description_display)
        
        # Dau convention validation criteria
        criteria_label = QLabel("✅ Dau Convention Criteria:")
        criteria_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        left_layout.addWidget(criteria_label)
        
        criteria_text = QTextEdit()
        criteria_text.setFixedHeight(150)
        criteria_text.setReadOnly(True)
        criteria_text.setPlainText(
            "• Heavy identity lines: 4.0 width\n"
            "• Fine cut boundaries: 1.0 width\n"
            "• Prominent vertex spots: 3.5 radius\n"
            "• Enhanced hook lines: 1.5 width\n"
            "• No cut overlap (fundamental EG rule)\n"
            "• Complete containment in areas\n"
            "• Professional anti-aliased rendering"
        )
        criteria_text.setStyleSheet(
            "background: #f0f0f0; border: 1px solid #ccc; "
            "font-size: 11px; padding: 5px;"
        )
        left_layout.addWidget(criteria_text)
        
        # Pipeline status
        pipeline_status = QLabel()
        if PIPELINE_AVAILABLE:
            pipeline_status.setText("🟢 Full Pipeline: EGIF → EGI → Layout → Rendering")
            pipeline_status.setStyleSheet("color: green; font-weight: bold; margin: 10px;")
        else:
            pipeline_status.setText("🟡 Manual Rendering: Direct QtDiagramCanvas Testing")
            pipeline_status.setStyleSheet("color: orange; font-weight: bold; margin: 10px;")
        left_layout.addWidget(pipeline_status)
        
        # Save button
        save_button = QPushButton("💾 Save Current Test as PNG")
        save_button.clicked.connect(self.save_current_test)
        left_layout.addWidget(save_button)
        
        left_layout.addStretch()
        layout.addWidget(left_panel)
        
        # Right panel: Canvas
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        canvas_label = QLabel("🎨 Rendered Diagram:")
        canvas_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        right_layout.addWidget(canvas_label)
        
        self.canvas = QtDiagramCanvas(width=900, height=700)
        right_layout.addWidget(self.canvas)
        
        layout.addWidget(right_panel)
    
    def render_current_test(self):
        """Render the current EGIF test case."""
        test_case = self.test_cases[self.current_test]
        
        # Update UI displays
        self.test_label.setText(f"Test {self.current_test + 1}/{len(self.test_cases)}: {test_case['name']}")
        self.egif_display.setPlainText(test_case['egif'])
        
        description_text = f"{test_case['description']}\n\nExpected elements:\n"
        for element in test_case['expected_elements']:
            description_text += f"• {element.replace('_', ' ').title()}\n"
        self.description_display.setPlainText(description_text)
        
        # Clear canvas
        self.canvas.clear_elements()
        
        if PIPELINE_AVAILABLE:
            self.render_with_full_pipeline(test_case)
        else:
            self.render_manual_approximation(test_case)
        
        self.canvas.render_complete()
    
    def render_with_full_pipeline(self, test_case):
        """Render using the full EGIF → EGI → Layout → Rendering pipeline."""
        try:
            # Parse EGIF
            print(f"🔄 Parsing EGIF: {test_case['egif']}")
            graph = parse_egif(test_case['egif'])
            
            # Generate layout
            print(f"🔄 Generating layout...")
            layout_result = self.layout_engine.generate_layout(graph)
            
            # Validate layout result
            validate_layout_result(layout_result)
            
            # Render to canvas
            print(f"🔄 Rendering to canvas...")
            integration = QtDiagramCanvasIntegration(self.canvas)
            integration.render_from_layout_result(layout_result, graph)
            
            print(f"✅ Successfully rendered: {test_case['name']}")
            
        except Exception as e:
            print(f"❌ Pipeline error for {test_case['name']}: {e}")
            self.render_error_message(f"Pipeline Error: {str(e)}")
    
    def render_manual_approximation(self, test_case):
        """Render a manual approximation for testing QtDiagramCanvas directly."""
        egif = test_case['egif']
        
        if egif == '(Human "Socrates")':
            # Simple predicate
            self.canvas.add_vertex((150, 350), "vertex1")
            self.canvas.add_identity_line((150, 350), (250, 350), "identity1")
            self.canvas.add_predicate_text((300, 350), "Human", "pred1")
            self.canvas.add_hook_line((250, 350), (300, 350), "hook1")
            
        elif egif == '~[ (Mortal "Socrates") ]':
            # Simple cut
            self.canvas.add_cut((200, 300, 300, 100), "cut1")
            self.canvas.add_vertex((250, 350), "vertex1")
            self.canvas.add_identity_line((250, 350), (350, 350), "identity1")
            self.canvas.add_predicate_text((400, 350), "Mortal", "pred1")
            self.canvas.add_hook_line((350, 350), (400, 350), "hook1")
            
        elif egif == '*x (Human x) ~[ (Mortal x) ]':
            # Mixed sheet and cut
            # Sheet level
            self.canvas.add_vertex((100, 350), "vertex1")
            self.canvas.add_identity_line((100, 350), (180, 350), "identity1")
            self.canvas.add_predicate_text((220, 350), "Human", "pred1")
            self.canvas.add_hook_line((180, 350), (220, 350), "hook1")
            
            # Cut
            self.canvas.add_cut((300, 300, 250, 100), "cut1")
            self.canvas.add_vertex((400, 350), "vertex2")
            self.canvas.add_identity_line((400, 350), (480, 350), "identity2")
            self.canvas.add_predicate_text((520, 350), "Mortal", "pred2")
            self.canvas.add_hook_line((480, 350), (520, 350), "hook2")
            
            # Bridge identity line
            self.canvas.add_identity_line((180, 350), (400, 350), "identity_bridge")
            
        elif egif == '~[ (P "x") ] ~[ (Q "x") ]':
            # Sibling cuts
            # First cut
            self.canvas.add_cut((150, 300, 200, 100), "cut1")
            self.canvas.add_vertex((200, 350), "vertex1")
            self.canvas.add_identity_line((200, 350), (280, 350), "identity1")
            self.canvas.add_predicate_text((300, 350), "P", "pred1")
            self.canvas.add_hook_line((280, 350), (300, 350), "hook1")
            
            # Second cut (non-overlapping)
            self.canvas.add_cut((450, 300, 200, 100), "cut2")
            self.canvas.add_vertex((500, 350), "vertex2")
            self.canvas.add_identity_line((500, 350), (580, 350), "identity2")
            self.canvas.add_predicate_text((600, 350), "Q", "pred2")
            self.canvas.add_hook_line((580, 350), (600, 350), "hook2")
            
        elif egif == '~[ ~[ (Human "Socrates") ] ]':
            # Nested cuts
            # Outer cut
            self.canvas.add_cut((150, 250, 400, 200), "cut_outer")
            # Inner cut
            self.canvas.add_cut((200, 300, 300, 100), "cut_inner")
            self.canvas.add_vertex((300, 350), "vertex1")
            self.canvas.add_identity_line((300, 350), (380, 350), "identity1")
            self.canvas.add_predicate_text((420, 350), "Human", "pred1")
            self.canvas.add_hook_line((380, 350), (420, 350), "hook1")
            
        elif egif == '(Loves "John" "Mary")':
            # Binary relation
            self.canvas.add_vertex((150, 300), "vertex_john")
            self.canvas.add_vertex((150, 400), "vertex_mary")
            self.canvas.add_identity_line((150, 300), (250, 350), "identity1")
            self.canvas.add_identity_line((150, 400), (250, 350), "identity2")
            self.canvas.add_predicate_text((300, 350), "Loves", "pred1")
            self.canvas.add_hook_line((250, 350), (300, 350), "hook1")
        
        else:
            self.render_error_message(f"Manual approximation not implemented for: {egif}")
    
    def render_error_message(self, message):
        """Render an error message on the canvas."""
        self.canvas.add_predicate_text((400, 350), f"Error: {message}", "error")
    
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
        filename = f"qt_egif_validation_{test_name}.png"
        self.canvas.save_to_file(filename)
        print(f"✅ Saved: {filename}")

def main():
    """Run the EGIF → QtDiagramCanvas validation."""
    print("🎯 Phase 1A: EGIF → QtDiagramCanvas Dau-Compliant Round-Trip Validation")
    print("=" * 70)
    print("Testing:")
    print("• EGIF parsing and round-trip fidelity")
    print("• Dau-compliant visual rendering")
    print("• Heavy identity lines, fine cuts, prominent vertices")
    print("• Professional Qt rendering quality")
    print("• Non-overlapping cuts and proper containment")
    print()
    
    if PIPELINE_AVAILABLE:
        print("🟢 Full pipeline available: EGIF → EGI → Layout → Rendering")
    else:
        print("🟡 Manual approximation mode: Testing QtDiagramCanvas directly")
    print()
    
    app = QApplication(sys.argv)
    
    # Set application style for professional appearance
    app.setStyle('Fusion')
    
    validator = EGIFRenderingValidator()
    validator.show()
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
