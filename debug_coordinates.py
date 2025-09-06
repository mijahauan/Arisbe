#!/usr/bin/env python3
"""Debug coordinate system to verify element positions."""

import sys
sys.path.append('src')

from diagram_coordinator import DiagramCoordinator, Point2D
from coordinate_negotiator import CoordinateNegotiator
from PySide6.QtWidgets import QApplication, QGraphicsScene

def debug_coordinate_system():
    """Test coordinate system accuracy."""
    print("=== COORDINATE SYSTEM DEBUG ===")
    
    # Create minimal test setup
    app = QApplication.instance() or QApplication(sys.argv)
    scene = QGraphicsScene()
    
    # Create coordinator
    from styling.style_manager import StyleManager
    style_manager = StyleManager()
    coordinator = DiagramCoordinator(scene, style_manager)
    
    # Test click at specific position
    test_x, test_y = 100.0, 50.0
    print(f"\n1. Testing click at scene position ({test_x}, {test_y})")
    
    # Check coordinate conversion
    data_x, data_y = coordinator.coordinate_negotiator.get_data_position_for_rendering(test_x, test_y)
    print(f"   Converted to data coordinates: ({data_x}, {data_y})")
    
    # Create vertex at this position
    vertex_id = coordinator.create_vertex(Point2D(data_x, data_y), "sheet")
    print(f"   Created vertex: {vertex_id}")
    
    # Check where vertex actually ended up in diagram_state
    if vertex_id in coordinator.diagram_state.vertices:
        vertex = coordinator.diagram_state.vertices[vertex_id]
        actual_x, actual_y = vertex.position.x, vertex.position.y
        print(f"   Vertex stored at: ({actual_x}, {actual_y})")
        
        # Convert back to rendering coordinates
        render_x, render_y = coordinator.coordinate_negotiator.get_rendering_position_for_data(actual_x, actual_y)
        print(f"   Should render at: ({render_x}, {render_y})")
        
        # Check if positions match
        position_match = abs(render_x - test_x) < 1.0 and abs(render_y - test_y) < 1.0
        print(f"   Position accuracy: {'✓ PASS' if position_match else '✗ FAIL'}")
        
        if not position_match:
            print(f"   ERROR: Expected ({test_x}, {test_y}), got ({render_x}, {render_y})")
    else:
        print(f"   ERROR: Vertex {vertex_id} not found in diagram_state")
    
    # Check scene items
    print(f"\n2. Scene items check:")
    scene_items = list(scene.items())
    print(f"   Total scene items: {len(scene_items)}")
    
    for item in scene_items:
        if hasattr(item, 'vertex_id'):
            pos = item.pos()
            print(f"   Vertex {item.vertex_id} rendered at: ({pos.x()}, {pos.y()})")
        elif hasattr(item, 'predicate_id'):
            pos = item.pos()
            print(f"   Predicate {item.predicate_id} rendered at: ({pos.x()}, {pos.y()})")
    
    # Test coordinate negotiator state
    print(f"\n3. Coordinate negotiator state:")
    print(f"   Element positions tracked: {len(coordinator.coordinate_negotiator.element_positions)}")
    for elem_id, (x, y) in coordinator.coordinate_negotiator.element_positions.items():
        print(f"   {elem_id}: ({x}, {y})")
    
    return coordinator

if __name__ == "__main__":
    debug_coordinate_system()
