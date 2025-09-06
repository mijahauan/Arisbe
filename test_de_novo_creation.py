#!/usr/bin/env python3
"""
Test script for de novo graph creation in Ergasterion.
Tests the ability to create new existential graph elements from scratch.
"""

import sys
import os
sys.path.append('src')

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF
from tools.drawing_editor_refactored import RefactoredDrawingEditor
from diagram_coordinator import DiagramCoordinator

def test_de_novo_creation():
    """Test de novo graph creation functionality."""
    print("=== Testing De Novo Graph Creation ===")
    
    # Test 1: Initialize DiagramCoordinator for element creation
    print("Testing DiagramCoordinator element creation...")
    
    coordinator = DiagramCoordinator()
    
    # Test vertex creation
    print("Testing vertex creation...")
    vertex_id = coordinator.add_vertex_at_position(100, 100)
    print(f"✓ Created vertex: {vertex_id}")
    
    # Test predicate creation
    print("Testing predicate creation...")
    predicate_id = coordinator.add_predicate_at_position(200, 100, "Human")
    print(f"✓ Created predicate: {predicate_id}")
    
    # Test current state
    current_state = coordinator.get_current_diagram_state()
    print(f"✓ Current diagram state: {len(current_state.vertices)} vertices, {len(current_state.predicates)} predicates")
    
    # Test 2: Launch Ergasterion for interactive testing
    print(f"\nLaunching Ergasterion for de novo creation test...")
    app = QApplication(sys.argv)
    
    # Create the drawing editor
    ergasterion = RefactoredDrawingEditor()
    ergasterion.show()
    
    print("✓ Ergasterion launched successfully")
    print("✓ Ready for de novo element creation testing")
    
    print(f"\n=== Manual Testing Instructions ===")
    print(f"1. LEFT-CLICK on empty canvas to open context menu")
    print(f"2. Select 'Add Vertex here' to create a new vertex")
    print(f"3. Select 'Add Predicate here' to create a new predicate")
    print(f"4. Select 'Add Cut here' to create a new cut")
    print(f"5. Verify elements appear on canvas with proper rendering")
    print(f"6. Test constraint validation by trying to overlap elements")
    print(f"7. Right-click on existing elements for modification options")
    
    print(f"\n=== Expected Behaviors ===")
    print(f"• Left-click on empty canvas → Context menu appears")
    print(f"• Vertex creation → Black dot with optional label")
    print(f"• Predicate creation → Text box with relation name")
    print(f"• Cut creation → Oval boundary for negation")
    print(f"• Constraint validation → Prevents invalid overlaps")
    print(f"• Element modification → Right-click context menus")
    
    print(f"\nApplication ready for de novo creation testing...")
    return app.exec()

if __name__ == "__main__":
    success = test_de_novo_creation()
    if success == 0:
        print("✓ De novo creation test completed successfully")
    else:
        print("✗ De novo creation test encountered issues")
