#!/usr/bin/env python3
"""
Simple Test for Enhanced Graphviz Layout Engine

This test verifies the collision detection, spacing, and edge routing improvements
in the enhanced Graphviz-based layout engine with a direct rendering approach.
"""

import sys
from egif_parser_dau import parse_egif
from graphviz_layout_engine_v2 import create_graphviz_layout
from pyside6_canvas import create_qt_canvas


def test_enhanced_layout():
    """Test the enhanced Graphviz layout engine with various complexity levels."""
    
    print("🚀 Testing Enhanced Graphviz Layout Engine")
    print("   Features: Collision detection, spacing, edge routing")
    print()
    
    # Test cases with increasing complexity
    test_cases = [
        {
            'name': 'Simple Predicate with Long Label',
            'egif': '(Human "Socrates")',
            'description': 'Tests vertex sizing based on label length'
        },
        {
            'name': 'Multiple Predicates - Collision Avoidance',
            'egif': '(Human "Socrates") (Mortal "Socrates") (Wise "Socrates")',
            'description': 'Tests spacing between multiple predicates on same vertex'
        },
        {
            'name': 'Cut with Proper Padding',
            'egif': '(Human "Socrates") ~[ (Mortal "Socrates") (Wise "Socrates") ]',
            'description': 'Tests cut padding and internal element spacing'
        },
        {
            'name': 'Sibling Cuts - Non-overlapping',
            'egif': '*x ~[ (Human x) (Tall x) ] ~[ (Mortal x) (Wise x) ]',
            'description': 'Tests sibling cut separation and edge routing'
        },
        {
            'name': 'Complex Graph - Full Integration',
            'egif': '*x *y (Human x) (Woman y) ~[ (Loves x y) ~[ (Married x y) ] ] ~[ (Happy x) (Happy y) ]',
            'description': 'Tests complex layout with multiple vertices, predicates, and cuts'
        }
    ]
    
    # Test each case and report results
    for i, test_case in enumerate(test_cases):
        print(f"🎯 Test {i+1}: {test_case['name']}")
        print(f"   EGIF: {test_case['egif']}")
        print(f"   Goal: {test_case['description']}")
        
        try:
            # Parse EGIF to EGI
            graph = parse_egif(test_case['egif'])
            vertices = len(graph._vertex_map)
            edges = len(graph.nu)
            cuts = len(graph.Cut)
            
            print(f"   📊 EGI Structure: {vertices} vertices, {edges} edges, {cuts} cuts")
            
            # Generate enhanced layout
            layout_result = create_graphviz_layout(graph)
            elements = len(layout_result.primitives)
            bounds = layout_result.canvas_bounds
            
            print(f"   📐 Layout Result: {elements} elements")
            print(f"   📏 Canvas Bounds: {bounds[2]:.1f} × {bounds[3]:.1f}")
            
            # Analyze spacing and sizing
            analyze_layout_quality(layout_result, graph)
            
            print(f"   ✅ SUCCESS - Enhanced layout generated")
            
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
        
        print()
    
    # Create visual demonstration
    print("🎨 Creating Visual Demonstration...")
    create_visual_demo(test_cases[-1])  # Use the most complex test case


def analyze_layout_quality(layout_result, graph):
    """Analyze the quality of the enhanced layout."""
    
    primitives = layout_result.primitives
    
    # Check element spacing
    positions = [p.position for p in primitives.values()]
    if len(positions) > 1:
        min_distance = float('inf')
        for i, pos1 in enumerate(positions):
            for j, pos2 in enumerate(positions[i+1:], i+1):
                distance = ((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)**0.5
                min_distance = min(min_distance, distance)
        print(f"   🔍 Minimum element distance: {min_distance:.1f}")
    
    # Check element sizing
    vertex_count = sum(1 for p in primitives.values() if p.element_type == 'vertex')
    edge_count = sum(1 for p in primitives.values() if p.element_type == 'edge')
    
    print(f"   📦 Element distribution: {vertex_count} vertices, {edge_count} edges")
    
    # Check bounds utilization
    bounds = layout_result.canvas_bounds
    area = bounds[2] * bounds[3]
    density = len(primitives) / area if area > 0 else 0
    print(f"   📊 Layout density: {density:.4f} elements/unit²")


def create_visual_demo(test_case):
    """Create a visual demonstration of the enhanced layout."""
    
    try:
        print(f"   Rendering: {test_case['name']}")
        
        # Parse and layout
        graph = parse_egif(test_case['egif'])
        layout_result = create_graphviz_layout(graph)
        
        # Create Qt canvas
        canvas = create_qt_canvas(800, 600, "Enhanced Graphviz Layout Demo")
        
        # Render the layout
        render_enhanced_layout(canvas, layout_result, graph)
        
        # Show the canvas
        canvas.show()
        
        print(f"   ✅ Visual demo created - showing enhanced layout features")
        print(f"   💡 Look for: proper spacing, collision avoidance, edge routing")
        
        # Run Qt event loop
        canvas.app.exec()
        
    except Exception as e:
        print(f"   ❌ Visual demo failed: {e}")


def render_enhanced_layout(canvas, layout_result, graph):
    """Render the enhanced layout to demonstrate spacing and collision detection."""
    
    canvas.clear()
    
    # Scale layout to fit canvas
    bounds = layout_result.canvas_bounds
    canvas_width, canvas_height = 780, 580  # Leave margin
    
    if bounds[2] > 0 and bounds[3] > 0:
        scale_x = canvas_width / bounds[2]
        scale_y = canvas_height / bounds[3]
        scale = min(scale_x, scale_y) * 0.8  # Leave 20% margin
    else:
        scale = 1.0
    
    offset_x = (canvas_width - bounds[2] * scale) / 2 + 10
    offset_y = (canvas_height - bounds[3] * scale) / 2 + 10
    
    def transform_point(x, y):
        return (x * scale + offset_x, y * scale + offset_y)
    
    primitives = layout_result.primitives
    
    # 1. Draw collision boundaries (light gray) to show spacing
    for element_id, primitive in primitives.items():
        center = transform_point(*primitive.position)
        bounds = primitive.bounds
        width = (bounds[2] - bounds[0]) * scale
        height = (bounds[3] - bounds[1]) * scale
        
        # Draw boundary rectangle
        canvas.draw_rectangle(
            (center[0] - width/2, center[1] - height/2,
             center[0] + width/2, center[1] + height/2),
            {'color': (220, 220, 220), 'line_width': 1, 'fill_color': (250, 250, 250)}
        )
    
    # 2. Draw cuts with enhanced padding
    for element_id, primitive in primitives.items():
        if primitive.element_type == 'cut':
            center = transform_point(*primitive.position)
            bounds = primitive.bounds
            width = (bounds[2] - bounds[0]) * scale
            height = (bounds[3] - bounds[1]) * scale
            
            # Draw cut as rounded rectangle
            canvas.draw_rounded_rectangle(
                (center[0] - width/2, center[1] - height/2,
                 center[0] + width/2, center[1] + height/2),
                {'color': (100, 100, 100), 'line_width': 2, 'fill_color': (240, 240, 255)}
            )
    
    # 3. Draw edges with proper routing
    for element_id, primitive in primitives.items():
        if primitive.element_type == 'edge':
            center = transform_point(*primitive.position)
            # Draw edge as heavy line
            canvas.draw_line(
                (center[0] - 30, center[1]), (center[0] + 30, center[1]),
                {'color': (0, 0, 0), 'line_width': 3}
            )
    
    # 4. Draw vertices with labels
    for element_id, primitive in primitives.items():
        if primitive.element_type == 'vertex':
            center = transform_point(*primitive.position)
            
            # Draw vertex spot
            canvas.draw_circle(center, 4, 
                             {'color': (0, 0, 0), 'fill_color': (0, 0, 0)})
            
            # Draw vertex label if present
            if element_id in graph._vertex_map:
                vertex = graph._vertex_map[element_id]
                if vertex.label:
                    canvas.draw_text(f'"{vertex.label}"', 
                                   (center[0], center[1] + 20),
                                   {'color': (0, 0, 0), 'font_size': 10})
    
    # 5. Draw predicate nodes
    for element_id, primitive in primitives.items():
        if 'pred_' in element_id:
            center = transform_point(*primitive.position)
            bounds = primitive.bounds
            width = (bounds[2] - bounds[0]) * scale
            height = (bounds[3] - bounds[1]) * scale
            
            # Draw predicate box
            canvas.draw_rectangle(
                (center[0] - width/2, center[1] - height/2,
                 center[0] + width/2, center[1] + height/2),
                {'color': (0, 0, 0), 'line_width': 1, 'fill_color': (255, 255, 200)}
            )
            
            # Draw predicate name
            predicate_name = element_id.replace('pred_', '')
            if predicate_name in graph.rel:
                name = graph.rel[predicate_name]
                canvas.draw_text(name, center,
                               {'color': (0, 0, 0), 'font_size': 9})
    
    # Add title and feature annotations
    canvas.draw_text("Enhanced Graphviz Layout - Collision Detection & Spacing", 
                   (10, 25), {'color': (0, 0, 0), 'font_size': 14, 'bold': True})
    
    canvas.draw_text("Features: • Element sizing • Collision boundaries • Automatic spacing • Edge routing", 
                   (10, 45), {'color': (100, 100, 100), 'font_size': 10})


if __name__ == "__main__":
    test_enhanced_layout()
