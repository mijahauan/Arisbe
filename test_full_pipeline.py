#!/usr/bin/env python3
"""
Full unstyled EGIF → EGDF → Qt → constraints pipeline with interactive editing.
"""

import sys
import os
from pathlib import Path

# Add src to path
REPO_ROOT = Path(__file__).parent
sys.path.insert(0, str(REPO_ROOT / 'src'))
os.chdir(REPO_ROOT)

try:
    from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                   QHBoxLayout, QLabel, QPushButton, QTextEdit, QSplitter)
    from PySide6.QtCore import Qt, QPoint, QRect
    from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QMouseEvent
except ImportError:
    print("PySide6 not available - skipping Qt test")
    sys.exit(0)

class EGDrawingWidget(QWidget):
    """Interactive drawing widget for Existential Graphs with constraint enforcement."""
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(600, 400)
        self.setMouseTracking(True)
        
        # Drawing data
        self.layout_data = {}
        self.constraint_system = None
        self.egi = None
        
        # Interaction state
        self.dragging_element = None
        self.drag_offset = QPoint(0, 0)
        self.mouse_pos = QPoint(0, 0)
        
        # Visual settings (basic, no style)
        self.vertex_radius = 8
        self.cut_line_width = 2
        self.predicate_padding = 10
        
    def load_egif(self, egif_text):
        """Load EGIF through full pipeline: EGIF → 9-phase → EGDF → constraints."""
        from egif_parser_dau import EGIFParserDau
        from layout_phase_implementations import (
            ElementSizingPhase, ContainerSizingPhase, CollisionDetectionPhase,
            PredicatePositioningPhase, VertexPositioningPhase, CutPositioningPhase,
            LigatureRoutingPhase, FinalLayoutPhase, CoordinateTransformationPhase
        )
        from spatial_awareness_system import SpatialAwarenessSystem
        from spatial_constraint_system import SpatialConstraintSystem
        from layout_phase_implementations import PhaseStatus
        
        print(f"Loading EGIF: {egif_text}")
        self.current_egif = egif_text  # Store for layout decisions
        
        # Step 1: Parse EGIF to EGI
        parser = EGIFParserDau()
        try:
            self.egi = parser.parse(egif_text)
        except Exception as e:
            print(f"Failed to parse EGIF: {e}")
            return False
        
        print(f"EGI: {len(self.egi.V)} vertices, {len(self.egi.E)} edges, {len(self.egi.Cut)} cuts")
        
        # Step 2: Execute 9-phase pipeline → EGDF
        spatial_system = SpatialAwarenessSystem()
        phases = [
            ElementSizingPhase(),
            ContainerSizingPhase(spatial_system),
            CollisionDetectionPhase(spatial_system),
            PredicatePositioningPhase(spatial_system),
            VertexPositioningPhase(spatial_system),
            HookAssignmentPhase(),
            RectilinearLigaturePhase(),
            BranchOptimizationPhase(),
            AreaCompactionPhase()
        ]
        
        context = {}
        for i, phase in enumerate(phases):
            result = phase.execute(self.egi, context)
            if result.status != PhaseStatus.COMPLETED:
                print(f"Phase {i+1} failed: {result.error_message}")
                return False
        
        print("9-phase pipeline completed")
        
        # Step 3: Extract EGDF primitives from pipeline output
        print(f"DEBUG: Pipeline context keys: {list(context.keys())}")
        
        element_tracking = context.get('element_tracking', {})
        relative_bounds = context.get('relative_bounds', {})
        predicate_elements = context.get('predicate_elements', {})
        vertex_elements = context.get('vertex_elements', {})
        
        print(f"DEBUG: element_tracking: {element_tracking}")
        print(f"DEBUG: predicate_elements: {predicate_elements}")
        print(f"DEBUG: vertex_elements: {vertex_elements}")
        
        # Convert to absolute coordinates for drawing
        canvas_width, canvas_height = self.width() - 20, self.height() - 20
        self.layout_data = {}
        
        # Add vertices from pipeline output
        for vertex_id, vertex_data in vertex_elements.items():
            if hasattr(vertex_data, 'position'):
                rel_pos = vertex_data.position
                abs_x = 10 + rel_pos[0] * canvas_width
                abs_y = 10 + rel_pos[1] * canvas_height
                
                # Get vertex label from EGI
                vertex_label = vertex_id
                if self.egi:
                    for vertex in self.egi.V:
                        if vertex.id == vertex_id:
                            vertex_label = getattr(vertex, 'label', vertex.id)
                            break
                
                self.layout_data[vertex_id] = {
                    'element_id': vertex_id,
                    'element_type': 'vertex',
                    'position': (abs_x, abs_y),
                    'bounds': (abs_x-self.vertex_radius, abs_y-self.vertex_radius, 
                             abs_x+self.vertex_radius, abs_y+self.vertex_radius),
                    'label': vertex_label
                }
        
        # Add predicates from pipeline output
        for edge_id, edge_data in predicate_elements.items():
            if hasattr(edge_data, 'position'):
                rel_pos = edge_data.position
                abs_x = 10 + rel_pos[0] * canvas_width
                abs_y = 10 + rel_pos[1] * canvas_height
                
                # Get predicate label from EGI
                predicate_label = edge_id
                if self.egi:
                    predicate_label = self.egi.rel.get(edge_id, edge_id)
                
                self.layout_data[edge_id] = {
                    'element_id': edge_id,
                    'element_type': 'predicate',
                    'position': (abs_x, abs_y),
                    'bounds': (abs_x-self.predicate_padding, abs_y-10,
                             abs_x+self.predicate_padding, abs_y+10),
                    'label': predicate_label
                }
        
        # Add cuts from pipeline output (no hardcoded overrides)
        cuts = list(self.egi.Cut) if self.egi else []
        print(f"DEBUG: Processing {len(cuts)} cuts from EGI")
        print(f"DEBUG: Current EGIF: {getattr(self, 'current_egif', 'unknown')}")
        print(f"DEBUG: Pipeline relative_bounds: {relative_bounds}")
        
        # Use pipeline output for all cuts
        for cut_id, bounds in relative_bounds.items():
            if cut_id != 'sheet':
                abs_bounds = (
                    10 + bounds[0] * canvas_width,
                    10 + bounds[1] * canvas_height,
                    10 + bounds[2] * canvas_width,
                    10 + bounds[3] * canvas_height
                )
                center_x = (abs_bounds[0] + abs_bounds[2]) / 2
                center_y = (abs_bounds[1] + abs_bounds[3]) / 2
                
                self.layout_data[cut_id] = {
                    'element_id': cut_id,
                    'element_type': 'cut',
                    'position': (center_x, center_y),
                    'bounds': abs_bounds
                }
        
        # Step 4: Initialize constraint system
        self.constraint_system = SpatialConstraintSystem()
        self.constraint_system.set_egi_reference(self.egi)
        
        print(f"Loaded {len(self.layout_data)} elements with constraints")
        self.update()
        return True
    
    def paintEvent(self, event):
        """Draw the EG elements."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Clear background
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        
        if not self.layout_data:
            painter.drawText(self.rect(), Qt.AlignCenter, "Load an EGIF to see the graph")
            return
        
        # Draw cuts first (background)
        for element_id, element in self.layout_data.items():
            if element.get('element_type') == 'cut':
                self._draw_cut(painter, element)
        
        # Draw predicates
        for element_id, element in self.layout_data.items():
            if element.get('element_type') == 'predicate':
                self._draw_predicate(painter, element)
        
        # Draw vertices (foreground)
        for element_id, element in self.layout_data.items():
            if element.get('element_type') == 'vertex':
                self._draw_vertex(painter, element)
        
        # Draw ligatures (connections)
        self._draw_ligatures(painter)
        
        # Show constraint violations
        if self.constraint_system:
            violations = self.constraint_system.validate_layout(self.layout_data)
            if violations:
                painter.setPen(QPen(QColor(255, 0, 0), 3))
                painter.drawText(10, 20, f"⚠ {len(violations)} constraint violations")
    
    def _draw_cut(self, painter, element):
        """Draw a cut as a rounded rectangle."""
        bounds = element.get('bounds', (0, 0, 100, 100))
        rect = QRect(int(bounds[0]), int(bounds[1]), 
                    int(bounds[2] - bounds[0]), int(bounds[3] - bounds[1]))
        
        painter.setPen(QPen(QColor(0, 0, 0), self.cut_line_width))
        painter.setBrush(QBrush(QColor(240, 240, 240, 100)))
        painter.drawRoundedRect(rect, 10, 10)
    
    def _draw_predicate(self, painter, element):
        """Draw a predicate as text."""
        pos = element.get('position', (0, 0))
        label = element.get('label', element.get('element_id', '?'))
        
        painter.setPen(QPen(QColor(0, 0, 0)))
        painter.setFont(QFont("Arial", 12))
        painter.drawText(int(pos[0]), int(pos[1]), label)
    
    def _draw_vertex(self, painter, element):
        """Draw a vertex as a filled circle."""
        pos = element.get('position', (0, 0))
        label = element.get('label', element.get('element_id', '?'))
        
        # Draw vertex circle
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.setBrush(QBrush(QColor(100, 100, 100)))
        painter.drawEllipse(int(pos[0] - self.vertex_radius), int(pos[1] - self.vertex_radius),
                          self.vertex_radius * 2, self.vertex_radius * 2)
        
        # Draw vertex label
        painter.setPen(QPen(QColor(0, 0, 0)))
        painter.setFont(QFont("Arial", 10))
        painter.drawText(int(pos[0] + self.vertex_radius + 5), int(pos[1] + 5), label)
    
    def _draw_ligatures(self, painter):
        """Draw ligatures connecting predicates to vertices."""
        if not self.egi:
            return
        
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        
        # Draw connections based on EGI nu mapping
        for edge_id, vertex_ids in self.egi.nu.items():
            edge_pos = None
            if edge_id in self.layout_data:
                edge_pos = self.layout_data[edge_id].get('position')
            
            if edge_pos:
                for vertex_id in vertex_ids:
                    if vertex_id in self.layout_data:
                        vertex_pos = self.layout_data[vertex_id].get('position')
                        if vertex_pos:
                            painter.drawLine(int(edge_pos[0]), int(edge_pos[1]),
                                           int(vertex_pos[0]), int(vertex_pos[1]))
    
    def mousePressEvent(self, event):
        """Handle mouse press for dragging elements."""
        if event.button() == Qt.LeftButton:
            # Find element under mouse
            for element_id, element in self.layout_data.items():
                if element.get('element_type') in ['vertex', 'predicate']:
                    pos = element.get('position', (0, 0))
                    distance = ((event.x() - pos[0])**2 + (event.y() - pos[1])**2)**0.5
                    if distance < 20:  # Click tolerance
                        self.dragging_element = element_id
                        self.drag_offset = QPoint(int(pos[0] - event.x()), int(pos[1] - event.y()))
                        break
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging elements."""
        self.mouse_pos = event.pos()
        
        if self.dragging_element and self.dragging_element in self.layout_data:
            # Update element position
            new_x = event.x() + self.drag_offset.x()
            new_y = event.y() + self.drag_offset.y()
            
            self.layout_data[self.dragging_element]['position'] = (new_x, new_y)
            
            # Update bounds for vertices
            if self.layout_data[self.dragging_element].get('element_type') == 'vertex':
                self.layout_data[self.dragging_element]['bounds'] = (
                    new_x - self.vertex_radius, new_y - self.vertex_radius,
                    new_x + self.vertex_radius, new_y + self.vertex_radius
                )
            
            self.update()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release - apply constraint fixes."""
        if self.dragging_element and self.constraint_system:
            # Check for constraint violations
            violations = self.constraint_system.validate_layout(self.layout_data)
            if violations:
                print(f"Constraint violations detected: {len(violations)}")
                for v in violations:
                    print(f"  - {v.description}")
                
                # Apply constraint fixes
                fixed_layout = self.constraint_system.apply_constraint_fixes(violations, self.layout_data)
                self.layout_data = fixed_layout
                print("Applied constraint fixes")
                self.update()
        
        self.dragging_element = None

class EGMainWindow(QMainWindow):
    """Main window for the EG interactive editor."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Existential Graph Interactive Editor (Unstyled)")
        self.setGeometry(100, 100, 1000, 700)
        
        # Create main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Create layout
        layout = QHBoxLayout(main_widget)
        
        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Create drawing widget
        self.drawing_widget = EGDrawingWidget()
        splitter.addWidget(self.drawing_widget)
        
        # Create control panel
        control_panel = self._create_control_panel()
        splitter.addWidget(control_panel)
        
        # Set splitter proportions
        splitter.setSizes([700, 300])
        
        # Load default example
        self._load_default_example()
    
    def _create_control_panel(self):
        """Create the control panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # EGIF input
        layout.addWidget(QLabel("EGIF Input:"))
        self.egif_input = QTextEdit()
        self.egif_input.setMaximumHeight(100)
        self.egif_input.setPlainText('~[ (Human "Socrates") ~[ (Mortal "Socrates") ] ]')
        layout.addWidget(self.egif_input)
        
        # Load button
        load_button = QPushButton("Load EGIF")
        load_button.clicked.connect(self._load_egif)
        layout.addWidget(load_button)
        
        # Status display
        layout.addWidget(QLabel("Status:"))
        self.status_display = QTextEdit()
        self.status_display.setReadOnly(True)
        layout.addWidget(self.status_display)
        
        # Example buttons
        layout.addWidget(QLabel("Examples:"))
        
        examples = [
            ("Simple Predicate", '*x (Human x)'),
            ("Binary Relation", '*x *y (Loves x y)'),
            ("Socrates Example", '~[ (Human "Socrates") ~[ (Mortal "Socrates") ] ]'),
            ("Double Cut", '*x ~[ ~[ (P x) ] ]'),
        ]
        
        for name, egif in examples:
            button = QPushButton(name)
            button.clicked.connect(lambda checked, e=egif: self._load_example(e))
            layout.addWidget(button)
        
        layout.addStretch()
        return panel
    
    def _load_egif(self):
        """Load EGIF from input."""
        egif_text = self.egif_input.toPlainText().strip()
        if egif_text:
            success = self.drawing_widget.load_egif(egif_text)
            if success:
                self.status_display.setPlainText(f"✅ Loaded: {egif_text}")
            else:
                self.status_display.setPlainText(f"❌ Failed to load: {egif_text}")
    
    def _load_example(self, egif_text):
        """Load an example EGIF."""
        self.egif_input.setPlainText(egif_text)
        self._load_egif()
    
    def _load_default_example(self):
        """Load the default example."""
        self._load_egif()

def main():
    """Run the interactive EG editor."""
    app = QApplication(sys.argv)
    
    window = EGMainWindow()
    window.show()
    
    return app.exec()

if __name__ == "__main__":
    result = main()
    print(f"\n✅ Interactive EG editor completed (exit code: {result})")
