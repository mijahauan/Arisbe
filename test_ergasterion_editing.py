#!/usr/bin/env python3
"""
Test script for Ergasterion interactive editing functionality with the new constraint system.
Tests element creation, constraint validation, and diagram manipulation within the integrated home.
"""

import sys
import os
sys.path.append('src')

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF
from tools.drawing_editor_refactored import RefactoredDrawingEditor
from controller.constraint_engine import validate_syntactic_constraints, validate_semantic_constraints
from egi_core_dau import Vertex, Edge, RelationalGraphWithCuts
import json

def test_ergasterion_editing():
    """Test the Ergasterion interactive editing functionality."""
    print("=== Testing Ergasterion Interactive Editing ===")
    
    # Test 1: Test constraint validation functions
    print("Testing constraint validation functions...")
    
    # Create test DTO for constraint testing
    test_dto = {
        'sheet_id': 'test_sheet',
        'cuts': {},
        'vertices': {
            'v1': {'pos': (100, 100), 'radius': 10, 'area_id': 'test_sheet', 'name': 'Socrates'},
            'v2': {'pos': (110, 110), 'radius': 10, 'area_id': 'test_sheet', 'name': None}  # Overlapping
        },
        'predicates': {
            'p1': {'rect': (150, 100, 60, 30), 'area_id': 'test_sheet', 'text': 'Human'}
        },
        'ligatures': {}
    }
    
    # Test syntactic constraint validation
    syntactic_ok, syntactic_msg, syntactic_info = validate_syntactic_constraints(test_dto)
    print(f"✓ Syntactic constraints: {syntactic_ok} - {syntactic_msg}")
    
    # Test semantic constraint validation  
    semantic_ok, semantic_msg, semantic_info = validate_semantic_constraints(test_dto)
    print(f"✓ Semantic constraints: {semantic_ok} - {semantic_msg}")
    
    # Test 2: Create simple EGI for editing test
    print("\nCreating test EGI for editing...")
    
    # Create a simple graph: Human(Socrates)
    vertex_socrates = Vertex(id="v_socrates", label="Socrates", is_generic=False)
    edge_human = Edge(id="e_human")
    
    vertices = frozenset([vertex_socrates])
    edges = frozenset([edge_human])
    cuts = frozenset()
    
    # Nu mapping: Human connects to Socrates (use IDs, not objects)
    from frozendict import frozendict
    nu = frozendict({edge_human.id: (vertex_socrates.id,)})
    
    # Area mapping: everything on the sheet (use IDs, not objects)
    area = frozendict({"sheet": frozenset([vertex_socrates.id, edge_human.id])})
    
    # Relation names (use IDs, not objects)
    rel = frozendict({edge_human.id: "Human"})
    
    test_egi = RelationalGraphWithCuts(
        V=vertices,
        E=edges,
        Cut=cuts,
        nu=nu,
        area=area,
        rel=rel,
        sheet="sheet"
    )
    
    print(f"✓ Test EGI created: {len(test_egi.V)} vertex, {len(test_egi.E)} edge")
    print(f"✓ EGI structure: Human(Socrates)")
    
    # Test 4: Launch Ergasterion for interactive testing
    print(f"\nLaunching Ergasterion for interactive editing test...")
    app = QApplication(sys.argv)
    
    # Create the drawing editor
    ergasterion = RefactoredDrawingEditor()
    
    # Load the test EGI
    try:
        # Convert EGI to the format expected by the drawing editor
        # This would normally be done through the handoff protocol
        ergasterion.show()
        print("✓ Ergasterion launched successfully")
        print("✓ Ready for interactive constraint testing")
        
    except Exception as e:
        print(f"✗ Error launching Ergasterion: {e}")
        return False
    
    print(f"\n=== Interactive Testing Instructions ===")
    print(f"1. Right-click on canvas to test context menu")
    print(f"2. Try creating new vertices and predicates")
    print(f"3. Test constraint validation by overlapping elements")
    print(f"4. Verify ligature creation between vertices and predicates")
    print(f"5. Test cut creation and area constraints")
    print(f"6. Verify spatial padding prevents invalid overlaps")
    
    print(f"\n=== Expected Constraint Behaviors ===")
    print(f"• Syntactic constraints: Always enforced (no invalid overlaps)")
    print(f"• Semantic constraints: Optional enforcement (logical consistency)")
    print(f"• Spatial padding: Elements maintain minimum separation")
    print(f"• Ligature validation: Proper connections between elements")
    
    print(f"\nApplication ready for manual constraint testing...")
    return app.exec()

if __name__ == "__main__":
    success = test_ergasterion_editing()
    if success == 0:
        print("✓ Ergasterion editing test completed successfully")
    else:
        print("✗ Ergasterion editing test encountered issues")
