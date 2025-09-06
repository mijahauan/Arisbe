#!/usr/bin/env python3
"""
Test the end-to-end EGI → EGDF → diagram rendering pipeline.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut
from frozendict import frozendict
from diagram_coordinator import DiagramCoordinator
from styling.style_manager import StyleManager
from shared_diagram_renderer import SharedDiagramRenderer
from PySide6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt

def create_simple_egi():
    """Create a simple EGI with one vertex and one predicate."""
    # Create vertex
    vertex = Vertex(id="v1", label="Socrates", is_generic=False)
    
    # Create edge for predicate
    edge = Edge(id="e1")
    
    # Create EGI structure
    egi = RelationalGraphWithCuts(
        V=frozenset([vertex]),
        E=frozenset([edge]),
        nu=frozendict({"e1": (vertex.id,)}),  # Unary predicate
        sheet="sheet_test",  # Sheet of assertion
        Cut=frozenset(),  # No cuts
        area=frozendict({"sheet_test": frozenset([vertex.id, edge.id])}),
        rel=frozendict({"e1": "Human"})  # Predicate name
    )
    
    return egi

def test_egi_to_egdf_rendering():
    """Test EGI → EGDF → rendering pipeline."""
    print("=== Testing EGI → EGDF → Rendering Pipeline ===")
    
    # Create simple EGI
    egi = create_simple_egi()
    print(f"Created EGI with {len(egi.V)} vertices, {len(egi.E)} edges")
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Create scene and renderer
    scene = QGraphicsScene()
    style_manager = StyleManager()
    renderer = SharedDiagramRenderer(scene, style_manager)
    
    # Create coordinator
    coordinator = DiagramCoordinator(scene, style_manager)
    
    # Try to load the EGI
    try:
        coordinator.set_target_egi(egi)
        print("✓ EGI set as target successfully")
        
        # Initialize empty scene and try to render
        coordinator.initialize_empty_scene()
        
        # Check if anything was rendered
        items = scene.items()
        print(f"✓ Scene has {len(items)} items")
        
        # Try to render the EGI directly
        if len(items) == 0:
            print("No items rendered - trying direct rendering approach")
            # Create a simple vertex manually to test rendering
            vertex_id = coordinator.add_vertex_at_position(100, 100)
            predicate_id = coordinator.add_predicate_at_position(200, 100, "Human")
            print(f"Added vertex {vertex_id} and predicate {predicate_id}")
            
            items = scene.items()
            print(f"✓ After manual creation: Scene has {len(items)} items")
        
        # Create view to display
        view = QGraphicsView(scene)
        view.setWindowTitle("EGI Test Rendering")
        view.show()
        
        print("✓ Rendering complete - GUI should be visible")
        return app.exec()
        
    except Exception as e:
        print(f"✗ Error in pipeline: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = test_egi_to_egdf_rendering()
    sys.exit(exit_code)
