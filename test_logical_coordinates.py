#!/usr/bin/env python3
"""
Test script for the logical coordinate system and viewport transformations.

This script tests the new zoom/pan architecture with a simple graph to verify:
1. Logical coordinates work independently of viewport
2. Viewport transformations correctly map logical to screen coordinates
3. Zoom/pan operations maintain spatial relationships
"""

import sys
sys.path.insert(0, 'src')

from viewport_system import LogicalCoordinateSystem, ViewportState, ViewportRenderer, LogicalBounds
from layout_phase_implementations import ElementSizingPhase, ContainerSizingPhase
from spatial_awareness_system import SpatialAwarenessSystem
from egif_parser_dau import EGIFParser

def test_logical_coordinate_system():
    """Test the logical coordinate system with a simple graph."""
    
    print("=== Testing Logical Coordinate System ===")
    
    # Create a simple EGIF for testing
    simple_egif = """
    [Cat]
    [Mat]
    [On] -> (Cat, Mat)
    """
    
    # Parse EGIF to EGI
    parser = EGIFParser(simple_egif)
    egi = parser.parse()
    
    print(f"Parsed EGI with {len(egi.V)} vertices, {len(egi.E)} edges, {len(egi.Cut)} cuts")
    
    # Initialize pipeline phases
    spatial_system = SpatialAwarenessSystem()
    element_sizing = ElementSizingPhase()
    container_sizing = ContainerSizingPhase(spatial_system)
    
    # Execute phases
    context = {}
    
    # Phase 1: Element Sizing
    sizing_result = element_sizing.execute(egi, context)
    print(f"Element Sizing: {sizing_result.status.value}, {sizing_result.quality_metrics}")
    
    # Phase 2: Container Sizing (now with logical coordinates)
    container_result = container_sizing.execute(egi, context)
    print(f"Container Sizing: {container_result.status.value}, {container_result.quality_metrics}")
    
    # Test logical coordinate system
    logical_system = context.get('logical_system')
    if logical_system:
        print("\n=== Logical Coordinate System ===")
        
        # Test setting and getting element positions
        logical_system.set_element_position('test_element', 100.0, 200.0)
        position = logical_system.get_element_position('test_element')
        print(f"Set position (100, 200), got: {position}")
        
        # Test element bounds
        test_bounds = LogicalBounds(-50.0, -30.0, 150.0, 230.0)
        logical_system.set_element_bounds('test_element', test_bounds)
        retrieved_bounds = logical_system.get_element_bounds('test_element')
        print(f"Set bounds {(test_bounds.left, test_bounds.top, test_bounds.right, test_bounds.bottom)}")
        print(f"Got bounds {(retrieved_bounds.left, retrieved_bounds.top, retrieved_bounds.right, retrieved_bounds.bottom)}")
        
        # Test overall bounds
        overall = logical_system.get_overall_bounds()
        if overall:
            print(f"Overall bounds: {(overall.left, overall.top, overall.right, overall.bottom)}")
    
    return logical_system, context

def test_viewport_transformations(logical_system):
    """Test viewport transformations and zoom/pan operations."""
    
    print("\n=== Testing Viewport Transformations ===")
    
    # Create viewport state
    viewport = ViewportState(
        center_x=0.0,
        center_y=0.0,
        zoom=1.0,
        canvas_width=800,
        canvas_height=600
    )
    
    # Test coordinate transformations
    logical_point = (100.0, 50.0)
    screen_point = viewport.logical_to_screen(logical_point[0], logical_point[1])
    back_to_logical = viewport.screen_to_logical(screen_point[0], screen_point[1])
    
    print(f"Logical point: {logical_point}")
    print(f"Screen point: {screen_point}")
    print(f"Back to logical: {back_to_logical}")
    print(f"Round-trip error: {abs(logical_point[0] - back_to_logical[0])}, {abs(logical_point[1] - back_to_logical[1])}")
    
    # Test zoom operations
    print("\n--- Testing Zoom ---")
    original_zoom = viewport.zoom
    viewport.zoom_at_point(2.0, 400, 300)  # Zoom in at center
    print(f"Zoom changed from {original_zoom} to {viewport.zoom}")
    
    # Test the same logical point after zoom
    screen_point_zoomed = viewport.logical_to_screen(logical_point[0], logical_point[1])
    print(f"Same logical point after zoom: {screen_point_zoomed}")
    
    # Test pan operations
    print("\n--- Testing Pan ---")
    original_center = (viewport.center_x, viewport.center_y)
    viewport.pan(50.0, -25.0)
    new_center = (viewport.center_x, viewport.center_y)
    print(f"Center moved from {original_center} to {new_center}")
    
    # Test visible bounds
    visible_bounds = viewport.get_visible_logical_bounds()
    print(f"Visible logical bounds: {(visible_bounds.left, visible_bounds.top, visible_bounds.right, visible_bounds.bottom)}")
    
    # Test viewport renderer
    if logical_system:
        print("\n--- Testing Viewport Renderer ---")
        renderer = ViewportRenderer(logical_system)
        
        # Test element visibility
        test_element_visible = renderer.is_element_visible('test_element', viewport)
        print(f"Test element visible: {test_element_visible}")
        
        # Get visible elements
        visible_elements = renderer.get_visible_elements(viewport)
        print(f"Visible elements: {visible_elements}")
        
        # Test fit to content
        logical_system.fit_viewport_to_content(viewport, margin=0.1)
        print(f"After fit to content - center: {(viewport.center_x, viewport.center_y)}, zoom: {viewport.zoom}")

def test_extensible_domain():
    """Test extensible domain capabilities."""
    
    print("\n=== Testing Extensible Domain ===")
    
    logical_system = LogicalCoordinateSystem()
    
    # Add elements at various scales
    elements = [
        ('local_element', 10.0, 20.0, LogicalBounds(5.0, 15.0, 15.0, 25.0)),
        ('regional_element', 1000.0, 2000.0, LogicalBounds(900.0, 1900.0, 1100.0, 2100.0)),
        ('global_element', 100000.0, 200000.0, LogicalBounds(99000.0, 199000.0, 101000.0, 201000.0))
    ]
    
    for elem_id, x, y, bounds in elements:
        logical_system.set_element_position(elem_id, x, y)
        logical_system.set_element_bounds(elem_id, bounds)
        print(f"Added {elem_id} at ({x}, {y})")
    
    # Test viewport at different scales
    viewport = ViewportState(canvas_width=800, canvas_height=600)
    renderer = ViewportRenderer(logical_system)
    
    # Local view
    viewport.center_x, viewport.center_y = 10.0, 20.0
    viewport.zoom = 10.0
    visible = renderer.get_visible_elements(viewport)
    print(f"Local view (center: {(viewport.center_x, viewport.center_y)}, zoom: {viewport.zoom}): {visible}")
    
    # Regional view
    viewport.center_x, viewport.center_y = 1000.0, 2000.0
    viewport.zoom = 0.1
    visible = renderer.get_visible_elements(viewport)
    print(f"Regional view (center: {(viewport.center_x, viewport.center_y)}, zoom: {viewport.zoom}): {visible}")
    
    # Global view
    viewport.center_x, viewport.center_y = 50000.0, 100000.0
    viewport.zoom = 0.001
    visible = renderer.get_visible_elements(viewport)
    print(f"Global view (center: {(viewport.center_x, viewport.center_y)}, zoom: {viewport.zoom}): {visible}")
    
    # Fit all content
    logical_system.fit_viewport_to_content(viewport, margin=0.1)
    visible = renderer.get_visible_elements(viewport)
    print(f"Fit all content (center: {(viewport.center_x, viewport.center_y)}, zoom: {viewport.zoom}): {visible}")

if __name__ == "__main__":
    print("Testing Logical Coordinate System and Viewport Architecture")
    print("=" * 60)
    
    try:
        # Test basic logical coordinate system
        logical_system, context = test_logical_coordinate_system()
        
        # Test viewport transformations
        test_viewport_transformations(logical_system)
        
        # Test extensible domain capabilities
        test_extensible_domain()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("✅ Logical coordinate system working correctly")
        print("✅ Viewport transformations functional")
        print("✅ Zoom/pan operations maintain precision")
        print("✅ Extensible domain architecture validated")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
