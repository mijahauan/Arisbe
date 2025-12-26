"""
Test Hierarchical Area System with EGIF Example
Tests the pixel-perfect logical-spatial correspondence system.
"""

import sys
import os
sys.path.insert(0, 'src')

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPainter, QPen, QBrush, QColor

from hierarchical_area_system import HierarchicalAreaSystem, LogicalArea
from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut, ElementID
from frozendict import frozendict


class HierarchicalAreaTestWindow(QMainWindow):
    """Test window for hierarchical area system."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hierarchical Area System Test")
        self.setGeometry(100, 100, 1000, 700)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Test buttons
        test_egif_btn = QPushButton("Test EGIF: ~[ ~[ ] ~[ ] ~[ ~[ ] ] ]")
        test_egif_btn.clicked.connect(self.test_egif_example)
        layout.addWidget(test_egif_btn)
        
        test_point_btn = QPushButton("Test Point Detection")
        test_point_btn.clicked.connect(self.test_point_detection)
        layout.addWidget(test_point_btn)
        
        validate_btn = QPushButton("Validate Hierarchy")
        validate_btn.clicked.connect(self.validate_hierarchy)
        layout.addWidget(validate_btn)
        
        # Output area
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)
        
        # Initialize system
        self.area_system = HierarchicalAreaSystem()
        self.test_egi = None
        
    def log(self, message: str):
        """Add message to output."""
        self.output.append(message)
        print(message)
    
    def test_egif_example(self):
        """Test with EGIF: ~[ ~[ ] ~[ ] ~[ ~[ ] ] ]"""
        self.log("=== Testing EGIF: ~[ ~[ ] ~[ ] ~[ ~[ ] ] ] ===")
        
        # Create EGI structure for this EGIF
        # 5 cuts: c1, c2, c3, c4, c5
        # Hierarchy: sheet contains [c1, c2, c3], c3 contains [c4], c4 contains [c5]
        
        vertices = frozenset([
            Vertex("v1"), Vertex("v2"), Vertex("v3")
        ])
        
        edges = frozenset([
            Edge("e1"), Edge("e2")
        ])
        
        cuts = frozenset([
            Cut("c1"), Cut("c2"), Cut("c3"), Cut("c4"), Cut("c5")
        ])
        
        # Nu mapping (edges to vertices)
        nu_mapping = frozendict({
            "e1": frozenset(["v1", "v2"]),
            "e2": frozenset(["v2", "v3"])
        })
        
        # Area mapping reflecting EGIF structure
        sheet_id = "sheet"
        area_mapping = frozendict({
            sheet_id: frozenset(["c1", "c2", "c3"]),  # Sheet contains 3 sibling cuts
            "c1": frozenset([]),                       # Empty cut
            "c2": frozenset([]),                       # Empty cut  
            "c3": frozenset(["c4", "v1"]),           # Cut c3 contains c4 and vertex v1
            "c4": frozenset(["c5", "e1"]),           # Cut c4 contains c5 and edge e1
            "c5": frozenset(["v2", "v3", "e2"])      # Cut c5 contains vertices and edge
        })
        
        # Relation mapping
        rel_mapping = frozendict({
            "e1": "R",
            "e2": "S"
        })
        
        # Create EGI
        self.test_egi = RelationalGraphWithCuts(
            V=vertices,
            E=edges,
            nu=nu_mapping,
            sheet=sheet_id,
            Cut=cuts,
            area=area_mapping,
            rel=rel_mapping
        )
        
        # Build hierarchy
        root_area = self.area_system.build_hierarchy_from_egi(self.test_egi)
        
        # Log structure
        self.log(f"Root area: {root_area.area_id}")
        self.log(f"Canvas bounds: {self.area_system.canvas_bounds}")
        
        # Log all areas and their hierarchy
        self._log_area_hierarchy(root_area, 0)
        
        # Log area bounds
        self.log("\n--- Area Bounds ---")
        for area_id, area in self.area_system.areas.items():
            self.log(f"Area {area_id}: {area.bounds}, level={area.nesting_level}, elements={area.elements}")
    
    def _log_area_hierarchy(self, area: LogicalArea, indent: int):
        """Recursively log area hierarchy."""
        prefix = "  " * indent
        self.log(f"{prefix}Area {area.area_id} (level {area.nesting_level})")
        self.log(f"{prefix}  Bounds: {area.bounds}")
        self.log(f"{prefix}  Elements: {area.elements}")
        self.log(f"{prefix}  Children: {len(area.children)}")
        
        for child in area.children:
            self._log_area_hierarchy(child, indent + 1)
    
    def test_point_detection(self):
        """Test point-in-area detection."""
        if not self.test_egi:
            self.log("Run EGIF test first!")
            return
        
        self.log("\n=== Testing Point Detection ===")
        
        # Test points at various locations
        test_points = [
            QPointF(100, 100),   # Should be in sheet
            QPointF(200, 200),   # Should be in a cut
            QPointF(300, 300),   # Should be in nested cut
        ]
        
        for point in test_points:
            area = self.area_system.get_area_at_point(point)
            if area:
                self.log(f"Point {point} is in area {area.area_id} (level {area.nesting_level})")
            else:
                self.log(f"Point {point} is not in any area")
    
    def validate_hierarchy(self):
        """Validate the hierarchy for consistency."""
        if not self.test_egi:
            self.log("Run EGIF test first!")
            return
        
        self.log("\n=== Validating Hierarchy ===")
        
        errors = self.area_system.validate_hierarchy()
        if errors:
            self.log("Validation errors found:")
            for error in errors:
                self.log(f"  ERROR: {error}")
        else:
            self.log("Hierarchy validation passed!")
        
        # Additional checks
        self.log("\n--- Containment Check ---")
        for area_id, area in self.area_system.areas.items():
            if area.parent and area.bounds and area.parent.bounds:
                if area.parent.bounds.contains(area.bounds):
                    self.log(f"✓ Area {area_id} properly contained in {area.parent.area_id}")
                else:
                    self.log(f"✗ Area {area_id} extends outside {area.parent.area_id}")
        
        # Check sibling overlap
        self.log("\n--- Sibling Overlap Check ---")
        for area_id, area in self.area_system.areas.items():
            if len(area.children) > 1:
                for i, child1 in enumerate(area.children):
                    for child2 in area.children[i+1:]:
                        if (child1.bounds and child2.bounds and 
                            child1.bounds.intersects(child2.bounds)):
                            self.log(f"✗ Siblings {child1.area_id} and {child2.area_id} overlap")
                        else:
                            self.log(f"✓ Siblings {child1.area_id} and {child2.area_id} don't overlap")


def main():
    app = QApplication([])
    window = HierarchicalAreaTestWindow()
    window.show()
    
    # Auto-run the EGIF test
    window.test_egif_example()
    window.validate_hierarchy()
    
    return app.exec()


if __name__ == "__main__":
    main()
