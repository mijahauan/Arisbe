#!/usr/bin/env python3
"""
Visual Selection System Test - Demonstrates robust, coherent selection functionality
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QTextEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush

from egif_parser_dau import EGIFParser
from layout_engine_clean import GraphvizLayoutEngine
from mode_aware_selection import ModeAwareSelectionSystem, Mode, ActionType

class SelectionDemoWidget(QWidget):
    """Minimal widget to demonstrate visual selection system."""
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(600, 400)
        
        # Initialize components
        self.parser = EGIFParser()
        self.layout_engine = GraphvizLayoutEngine()
        self.selection_system = ModeAwareSelectionSystem()
        
        # Test data
        self.test_egif = '(Human "Socrates") ~[ (Mortal "Socrates") ]'
        self.egi = None
        self.spatial_primitives = []
        self.selected_elements = set()
        self.hover_element = None
        self.current_mode = Mode.WARMUP
        
        # Load test diagram
        self.load_test_diagram()
        
    def load_test_diagram(self):
        """Load a test diagram for selection demonstration."""
        try:
            # Parse EGIF
            self.egi = self.parser.parse(self.test_egif)
            print(f"✓ Parsed EGI: {len(self.egi.V)} vertices, {len(self.egi.E)} edges, {len(self.egi.Cut)} cuts")
            
            # Generate layout
            layout_result = self.layout_engine.generate_layout(self.egi)
            self.spatial_primitives = layout_result.primitives
            print(f"✓ Generated layout: {len(self.spatial_primitives)} spatial primitives")
            
            # Initialize selection system
            self.selection_system.set_graph(self.egi)
            print(f"✓ Selection system initialized in {self.current_mode.value} mode")
            
            # Print element details for testing
            print("\nAvailable elements for selection:")
            for i, primitive in enumerate(self.spatial_primitives):
                print(f"  {i+1}. {primitive.element_id} ({primitive.element_type}) at {primitive.position}")
                
        except Exception as e:
            print(f"✗ Error loading test diagram: {e}")
            import traceback
            traceback.print_exc()
    
    def switch_mode(self, new_mode: Mode):
        """Switch selection mode."""
        self.current_mode = new_mode
        self.selection_system.switch_mode(new_mode)
        self.selected_elements.clear()
        print(f"✓ Switched to {new_mode.value} mode")
        self.update()
    
    def paintEvent(self, event):
        """Render the test diagram with selection overlays."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Clear background
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        
        if not self.spatial_primitives:
            painter.setPen(QPen(QColor(128, 128, 128), 1))
            painter.drawText(self.rect(), Qt.AlignCenter, "No diagram loaded")
            return
        
        # Render spatial primitives
        for primitive in self.spatial_primitives:
            self._render_primitive(painter, primitive)
        
        # Render selection overlays
        self._render_selection_overlays(painter)
        
        # Render mode indicator
        mode_color = QColor(0, 122, 255) if self.current_mode == Mode.WARMUP else QColor(40, 167, 69)
        painter.setPen(QPen(mode_color, 2))
        painter.drawText(10, 20, f"Mode: {self.current_mode.value.title()}")
        
        # Render selection status
        if self.selected_elements:
            painter.drawText(10, 40, f"Selected: {len(self.selected_elements)} elements")
            available_actions = self.selection_system.get_available_actions()
            if available_actions:
                actions_text = ", ".join([action.value.replace('_', ' ').title() for action in sorted(available_actions, key=lambda x: x.value)][:3])
                painter.drawText(10, 60, f"Actions: {actions_text}")
        else:
            painter.drawText(10, 40, "Click elements to select them")
    
    def _render_primitive(self, painter, primitive):
        """Render a spatial primitive."""
        x1, y1, x2, y2 = primitive.bounds
        element_type = primitive.element_type
        is_selected = primitive.element_id in self.selected_elements
        is_hovered = primitive.element_id == self.hover_element
        
        if element_type == "vertex":
            # Render vertex as dot
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            radius = 4
            
            color = QColor(0, 0, 0)
            if is_hovered:
                color = QColor(128, 128, 128)
            
            painter.setPen(QPen(color, 2))
            painter.setBrush(QBrush(color))
            painter.drawEllipse(center_x - radius, center_y - radius, 2*radius, 2*radius)
            
        elif element_type == "predicate":
            # Render predicate as text
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            
            color = QColor(0, 0, 0)
            if is_hovered:
                color = QColor(128, 128, 128)
            
            painter.setPen(QPen(color, 1))
            
            # Get predicate name
            if self.egi:
                edge_id = primitive.element_id
                relation_name = self.egi.rel.get(edge_id, edge_id)
                painter.drawText(center_x - 20, center_y + 5, relation_name)
            
        elif element_type == "cut":
            # Render cut as rectangle
            color = QColor(0, 0, 0)
            if is_hovered:
                color = QColor(128, 128, 128)
            
            painter.setPen(QPen(color, 1))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(x1, y1, x2 - x1, y2 - y1)
    
    def _render_selection_overlays(self, painter):
        """Render selection overlays."""
        if not self.selected_elements:
            return
        
        # Mode-aware selection colors
        if self.current_mode == Mode.WARMUP:
            selection_color = QColor(0, 122, 255, 80)
            border_color = QColor(0, 122, 255, 200)
        else:
            selection_color = QColor(40, 167, 69, 80)
            border_color = QColor(40, 167, 69, 200)
        
        painter.setPen(QPen(border_color, 3, Qt.SolidLine))
        painter.setBrush(QBrush(selection_color))
        
        for element_id in self.selected_elements:
            primitive = next((p for p in self.spatial_primitives 
                            if p.element_id == element_id), None)
            if primitive:
                x1, y1, x2, y2 = primitive.bounds
                padding = 5
                painter.drawRect(x1 - padding, y1 - padding, 
                               x2 - x1 + 2*padding, y2 - y1 + 2*padding)
    
    def mousePressEvent(self, event):
        """Handle mouse clicks for selection."""
        if event.button() == Qt.LeftButton:
            clicked_element = self._find_element_at_position(event.x(), event.y())
            
            if clicked_element:
                # Multi-select with Ctrl
                multi_select = bool(event.modifiers() & Qt.ControlModifier)
                result = self.selection_system.select_element(clicked_element, multi_select)
                
                # Update selection state
                self.selected_elements = self.selection_system.selection_state.selected_elements.copy()
                
                # Print feedback
                available_actions = self.selection_system.get_available_actions()
                print(f"✓ Selected {clicked_element} in {self.current_mode.value} mode")
                print(f"  Available actions: {[action.value for action in available_actions]}")
                
                if not result.is_valid:
                    print(f"⚠ Selection warning: {result.error_message}")
            else:
                # Clear selection
                if self.selected_elements:
                    print(f"✓ Cleared selection in {self.current_mode.value} mode")
                self.selection_system.clear_selection()
                self.selected_elements.clear()
            
            self.update()
    
    def mouseMoveEvent(self, event):
        """Handle mouse movement for hover effects."""
        hover_element = self._find_element_at_position(event.x(), event.y())
        
        if hover_element != self.hover_element:
            self.hover_element = hover_element
            self.update()
    
    def _find_element_at_position(self, x, y):
        """Find element at position with robust hit-testing."""
        for primitive in self.spatial_primitives:
            x1, y1, x2, y2 = primitive.bounds
            element_type = primitive.element_type
            
            if element_type == "vertex":
                # Circular hit-testing for vertices
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                radius = max(15, (x2 - x1) / 2 + 10)
                distance = ((x - center_x)**2 + (y - center_y)**2)**0.5
                if distance <= radius:
                    return primitive.element_id
            else:
                # Rectangular hit-testing with padding
                padding = 10
                if (x1 - padding) <= x <= (x2 + padding) and (y1 - padding) <= y <= (y2 + padding):
                    return primitive.element_id
        
        return None

class SelectionDemoWindow(QMainWindow):
    """Main window for selection system demonstration."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visual Selection System Demo - Robust Evidence")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        warmup_btn = QPushButton("Warmup Mode")
        warmup_btn.setCheckable(True)
        warmup_btn.setChecked(True)
        warmup_btn.clicked.connect(lambda: self.switch_mode(Mode.WARMUP))
        controls_layout.addWidget(warmup_btn)
        
        practice_btn = QPushButton("Practice Mode")
        practice_btn.setCheckable(True)
        practice_btn.clicked.connect(lambda: self.switch_mode(Mode.PRACTICE))
        controls_layout.addWidget(practice_btn)
        
        self.warmup_btn = warmup_btn
        self.practice_btn = practice_btn
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Demo widget
        self.demo_widget = SelectionDemoWidget()
        layout.addWidget(self.demo_widget)
        
        # Instructions
        instructions = QTextEdit()
        instructions.setMaximumHeight(100)
        instructions.setPlainText(
            "VISUAL SELECTION SYSTEM DEMONSTRATION:\n"
            "• Click elements to select them (blue in Warmup, green in Practice)\n"
            "• Ctrl+Click for multi-select\n"
            "• Hover for preview effects\n"
            "• Console shows available actions for each selection"
        )
        instructions.setReadOnly(True)
        layout.addWidget(instructions)
        
        print("=" * 60)
        print("VISUAL SELECTION SYSTEM DEMO LAUNCHED")
        print("=" * 60)
        print("This demonstrates robust, coherent evidence of:")
        print("1. Selection process (click elements)")
        print("2. Selection status (visual overlays)")
        print("3. Selection options (available actions)")
        print("4. Mode-aware behavior (Warmup vs Practice)")
        print("=" * 60)
    
    def switch_mode(self, mode):
        """Switch selection mode with visual feedback."""
        self.warmup_btn.setChecked(mode == Mode.WARMUP)
        self.practice_btn.setChecked(mode == Mode.PRACTICE)
        self.demo_widget.switch_mode(mode)

def main():
    """Run the visual selection system demonstration."""
    app = QApplication(sys.argv)
    window = SelectionDemoWindow()
    window.show()
    
    print("\n✓ Visual Selection System Demo is running")
    print("✓ Click elements in the diagram to see selection feedback")
    print("✓ Switch modes to see different selection behaviors")
    print("✓ Check console for detailed selection status")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
