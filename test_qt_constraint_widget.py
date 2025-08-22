#!/usr/bin/env python3
"""
Test Qt widget with interactive constraint enforcement on 9-phase pipeline output.
"""

import sys
import os
from pathlib import Path

# Add src to path
REPO_ROOT = Path(__file__).parent
sys.path.insert(0, str(REPO_ROOT / 'src'))
os.chdir(REPO_ROOT)

try:
    from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QPainter, QPen, QBrush, QColor
except ImportError:
    print("PySide6 not available - skipping Qt test")
    sys.exit(0)

class ConstraintTestWidget(QWidget):
    """Simple Qt widget to test constraint enforcement interactively."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pipeline Constraint Test")
        self.setGeometry(100, 100, 500, 400)
        
        # Initialize constraint system and pipeline data
        self.setup_pipeline_data()
        self.setup_ui()
        
    def setup_pipeline_data(self):
        """Setup 9-phase pipeline output and constraint system."""
        from egif_parser_dau import EGIFParser
        from layout_phase_implementations import (
            ElementSizingPhase, ContainerSizingPhase, CollisionDetectionPhase,
            PredicatePositioningPhase, VertexPositioningPhase, HookAssignmentPhase,
            RectilinearLigaturePhase, BranchOptimizationPhase, AreaCompactionPhase,
            PhaseStatus
        )
        from spatial_awareness_system import SpatialAwarenessSystem
        from spatial_constraint_system import SpatialConstraintSystem
        
        # Parse EGIF
        egif_text = '~[ (Human "Socrates") ~[ (Mortal "Socrates") ] ]'
        parser = EGIFParser(egif_text)
        self.egi = parser.parse()
        
        # Run 9-phase pipeline
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
        for phase in phases:
            result = phase.execute(self.egi, context)
            if result.status != PhaseStatus.COMPLETED:
                print(f"Pipeline phase failed: {result.error_message}")
                break
        
        # Extract and convert pipeline output
        element_tracking = context.get('element_tracking', {})
        relative_bounds = context.get('relative_bounds', {})
        
        canvas_width, canvas_height = 400, 300
        self.layout_data = {}
        
        # Convert elements to absolute coordinates
        for container_id, elements in element_tracking.items():
            if isinstance(elements, list):
                for element in elements:
                    if isinstance(element, dict):
                        rel_pos = element.get('relative_position', (0, 0))
                        abs_x = rel_pos[0] * canvas_width
                        abs_y = rel_pos[1] * canvas_height
                        
                        self.layout_data[element['element_id']] = {
                            'element_id': element['element_id'],
                            'element_type': element.get('element_type', 'unknown'),
                            'position': (abs_x, abs_y),
                            'bounds': (abs_x-5, abs_y-5, abs_x+5, abs_y+5)
                        }
        
        # Add cuts
        for cut_id, bounds in relative_bounds.items():
            if cut_id != 'sheet':
                abs_bounds = (
                    bounds[0] * canvas_width,
                    bounds[1] * canvas_height,
                    bounds[2] * canvas_width,
                    bounds[3] * canvas_height
                )
                center_x = (abs_bounds[0] + abs_bounds[2]) / 2
                center_y = (abs_bounds[1] + abs_bounds[3]) / 2
                
                self.layout_data[cut_id] = {
                    'element_id': cut_id,
                    'element_type': 'cut',
                    'position': (center_x, center_y),
                    'bounds': abs_bounds
                }
        
        # Initialize constraint system
        self.constraint_system = SpatialConstraintSystem()
        self.constraint_system.set_egi_reference(self.egi)
        
        # Find vertex for testing
        self.test_vertex_id = next(
            (k for k, v in self.layout_data.items() if v.get('element_type') == 'vertex'), 
            None
        )
        self.original_vertex_pos = None
        if self.test_vertex_id:
            self.original_vertex_pos = self.layout_data[self.test_vertex_id]['position']
        
        print(f"Pipeline data loaded: {len(self.layout_data)} elements")
        print(f"Test vertex: {self.test_vertex_id} at {self.original_vertex_pos}")
    
    def setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout()
        
        self.status_label = QLabel("Constraint system ready")
        layout.addWidget(self.status_label)
        
        self.test_button = QPushButton("Test Constraint Violation")
        self.test_button.clicked.connect(self.test_constraint_violation)
        layout.addWidget(self.test_button)
        
        self.fix_button = QPushButton("Apply Constraint Fix")
        self.fix_button.clicked.connect(self.apply_constraint_fix)
        layout.addWidget(self.fix_button)
        
        self.reset_button = QPushButton("Reset to Original")
        self.reset_button.clicked.connect(self.reset_to_original)
        layout.addWidget(self.reset_button)
        
        self.setLayout(layout)
        
        # Initial constraint check
        self.check_constraints()
    
    def check_constraints(self):
        """Check current constraint status."""
        violations = self.constraint_system.validate_layout(self.layout_data)
        if violations:
            self.status_label.setText(f"❌ {len(violations)} constraint violations")
            self.status_label.setStyleSheet("color: red")
        else:
            self.status_label.setText("✅ All constraints satisfied")
            self.status_label.setStyleSheet("color: green")
        
        return violations
    
    def test_constraint_violation(self):
        """Create a constraint violation by moving vertex outside cuts."""
        if self.test_vertex_id:
            # Move vertex way outside
            self.layout_data[self.test_vertex_id]['position'] = (450, 350)
            self.layout_data[self.test_vertex_id]['bounds'] = (448, 348, 452, 352)
            
            violations = self.check_constraints()
            print(f"Created {len(violations)} violations")
            for v in violations:
                print(f"  - {v.description}")
    
    def apply_constraint_fix(self):
        """Apply constraint fixes to resolve violations."""
        violations = self.constraint_system.validate_layout(self.layout_data)
        if violations:
            fixed_layout = self.constraint_system.apply_constraint_fixes(violations, self.layout_data)
            self.layout_data = fixed_layout
            
            new_violations = self.check_constraints()
            print(f"After fix: {len(new_violations)} violations remaining")
            
            if self.test_vertex_id:
                new_pos = self.layout_data[self.test_vertex_id]['position']
                print(f"Vertex moved to: {new_pos}")
    
    def reset_to_original(self):
        """Reset vertex to original position."""
        if self.test_vertex_id and self.original_vertex_pos:
            self.layout_data[self.test_vertex_id]['position'] = self.original_vertex_pos
            self.layout_data[self.test_vertex_id]['bounds'] = (
                self.original_vertex_pos[0]-5, self.original_vertex_pos[1]-5,
                self.original_vertex_pos[0]+5, self.original_vertex_pos[1]+5
            )
            
            self.check_constraints()
            print(f"Reset vertex to original position: {self.original_vertex_pos}")

def test_qt_constraint_widget():
    """Test Qt widget with constraint enforcement."""
    app = QApplication(sys.argv)
    
    widget = ConstraintTestWidget()
    widget.show()
    
    # Auto-test sequence
    def run_tests():
        print("\n=== Auto-testing constraint widget ===")
        
        # Test 1: Create violation
        widget.test_constraint_violation()
        
        # Test 2: Apply fix after delay
        QTimer.singleShot(1000, widget.apply_constraint_fix)
        
        # Test 3: Reset after delay
        QTimer.singleShot(2000, widget.reset_to_original)
        
        # Close after tests
        QTimer.singleShot(3000, app.quit)
    
    # Start auto-tests after widget is shown
    QTimer.singleShot(500, run_tests)
    
    return app.exec()

if __name__ == "__main__":
    result = test_qt_constraint_widget()
    print(f"\n✅ Qt constraint widget test completed (exit code: {result})")
