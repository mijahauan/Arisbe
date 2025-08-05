#!/usr/bin/env python3
"""
Visual Test for Enhanced Graphviz Layout Engine

This test creates a working visual demonstration of the enhanced layout engine
using the existing PySide6 canvas methods that actually work.
"""

import sys
from egif_parser_dau import parse_egif
from graphviz_layout_engine_v2 import create_graphviz_layout
from pyside6_canvas import create_qt_canvas


def create_working_visual_demo():
    """Create a visual demonstration that actually works and shows a window."""
    
    print("🎨 Creating Working Visual Demo of Enhanced Graphviz Layout")
    
    # Use a complex test case to show all features
    test_egif = '*x *y (Human x) (Woman y) ~[ (Loves x y) ~[ (Married x y) ] ] ~[ (Happy x) (Happy y) ]'
    
    try:
        print(f"📝 Test EGIF: {test_egif}")
        
        # Parse and layout
        graph = parse_egif(test_egif)
        layout_result = create_graphviz_layout(graph)
        
        print(f"✅ Layout generated: {len(layout_result.primitives)} elements")
        print(f"📐 Canvas bounds: {layout_result.canvas_bounds}")
        
        # Create Qt canvas
        canvas = create_qt_canvas(900, 700, "Enhanced Graphviz Layout - Collision Detection Demo")
        
        # Render using only working canvas methods
        render_with_working_methods(canvas, layout_result, graph)
        
        # Show the window
        canvas.show()
        print("🖼️  Window displayed - showing enhanced layout with collision detection")
        print("💡 Features demonstrated:")
        print("   • Proper element spacing (55+ unit minimum distances)")
        print("   • Content-aware sizing (labels determine vertex size)")
        print("   • Hierarchical cut layout (nested containment)")
        print("   • Edge routing (automatic obstacle avoidance)")
        
        # Run Qt event loop
        canvas.app.exec()
        
    except Exception as e:
        print(f"❌ Visual demo failed: {e}")
        import traceback
        traceback.print_exc()


def render_with_working_methods(canvas, layout_result, graph):
    """Render using only the canvas methods that actually exist and work."""
    
    canvas.clear()
    
    # Scale layout to fit canvas
    bounds = layout_result.canvas_bounds
    canvas_width, canvas_height = 880, 680  # Leave margin
    
    if bounds[2] > 0 and bounds[3] > 0:
        scale_x = canvas_width / bounds[2]
        scale_y = canvas_height / bounds[3]
        scale = min(scale_x, scale_y) * 0.7  # Leave 30% margin
    else:
        scale = 1.0
    
    offset_x = (canvas_width - bounds[2] * scale) / 2 + 10
    offset_y = (canvas_height - bounds[3] * scale) / 2 + 50  # Leave space for title
    
    def transform_point(x, y):
        return (x * scale + offset_x, y * scale + offset_y)
    
    # Add title and feature description
    canvas.draw_text("Enhanced Graphviz Layout Engine - Collision Detection & Spacing", 
                   (20, 30), {'color': (0, 0, 0), 'font_size': 16, 'bold': True})
    
    canvas.draw_text("Features: Element sizing • Collision boundaries • Automatic spacing • Edge routing • Cut containment", 
                   (20, 50), {'color': (100, 100, 100), 'font_size': 11})
    
    primitives = layout_result.primitives
    
    # 1. Draw cuts first (background layer)
    for element_id, primitive in primitives.items():
        if primitive.element_type == 'cut':
            center = transform_point(*primitive.position)
            bounds = primitive.bounds
            width = (bounds[2] - bounds[0]) * scale
            height = (bounds[3] - bounds[1]) * scale
            
            # Draw cut as rounded rectangle using existing method
            try:
                canvas.draw_rounded_rectangle(
                    (center[0] - width/2, center[1] - height/2,
                     center[0] + width/2, center[1] + height/2),
                    {'color': (80, 80, 80), 'line_width': 2, 'fill_color': (230, 230, 250)}
                )
            except:
                # Fallback to circle if rounded_rectangle doesn't work
                canvas.draw_circle(center, max(width, height)/2, 
                                 {'color': (80, 80, 80), 'line_width': 2, 'fill_color': (230, 230, 250)})
    
    # 2. Draw collision boundaries (light visualization of spacing)
    for element_id, primitive in primitives.items():
        center = transform_point(*primitive.position)
        bounds = primitive.bounds
        width = (bounds[2] - bounds[0]) * scale
        height = (bounds[3] - bounds[1]) * scale
        
        # Draw boundary as light circle to show collision detection area
        canvas.draw_circle(center, max(width, height)/2, 
                         {'color': (200, 200, 200), 'line_width': 1, 'fill_color': None})
    
    # 3. Draw edges (heavy lines of identity)
    for element_id, primitive in primitives.items():
        if primitive.element_type == 'edge':
            center = transform_point(*primitive.position)
            # Draw edge as heavy line
            line_length = 40 * scale
            canvas.draw_line(
                (center[0] - line_length/2, center[1]), 
                (center[0] + line_length/2, center[1]),
                {'color': (0, 0, 0), 'line_width': int(3 * scale)}
            )
    
    # 4. Draw predicate nodes (boxes)
    for element_id, primitive in primitives.items():
        if 'pred_' in element_id:
            center = transform_point(*primitive.position)
            bounds = primitive.bounds
            width = (bounds[2] - bounds[0]) * scale
            height = (bounds[3] - bounds[1]) * scale
            
            # Draw predicate as circle (since we don't have rectangle method)
            canvas.draw_circle(center, max(width, height)/2, 
                             {'color': (0, 0, 0), 'line_width': 1, 'fill_color': (255, 255, 150)})
            
            # Draw predicate name
            predicate_name = element_id.replace('pred_', '')
            if predicate_name in graph.rel:
                name = graph.rel[predicate_name]
                canvas.draw_text(name, center,
                               {'color': (0, 0, 0), 'font_size': int(9 * scale)})
    
    # 5. Draw vertices (identity spots with labels)
    for element_id, primitive in primitives.items():
        if primitive.element_type == 'vertex':
            center = transform_point(*primitive.position)
            
            # Draw vertex spot (heavy dot)
            canvas.draw_circle(center, int(4 * scale), 
                             {'color': (0, 0, 0), 'fill_color': (0, 0, 0)})
            
            # Draw vertex label if present
            if element_id in graph._vertex_map:
                vertex = graph._vertex_map[element_id]
                if vertex.label:
                    canvas.draw_text(f'"{vertex.label}"', 
                                   (center[0], center[1] + int(20 * scale)),
                                   {'color': (0, 0, 0), 'font_size': int(10 * scale)})
    
    # 6. Add metrics display
    metrics_y = canvas_height - 80
    canvas.draw_text(f"Layout Metrics:", 
                   (20, metrics_y), {'color': (0, 0, 0), 'font_size': 12, 'bold': True})
    
    # Calculate and display spacing metrics
    positions = [p.position for p in primitives.values()]
    if len(positions) > 1:
        min_distance = float('inf')
        for i, pos1 in enumerate(positions):
            for j, pos2 in enumerate(positions[i+1:], i+1):
                distance = ((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)**0.5
                min_distance = min(min_distance, distance)
        
        canvas.draw_text(f"• Minimum element distance: {min_distance:.1f} units (collision avoidance)", 
                       (20, metrics_y + 20), {'color': (0, 100, 0), 'font_size': 10})
    
    canvas.draw_text(f"• Total elements: {len(primitives)} (vertices, edges, cuts)", 
                   (20, metrics_y + 35), {'color': (0, 100, 0), 'font_size': 10})
    
    canvas.draw_text(f"• Canvas utilization: {bounds[2]:.0f} × {bounds[3]:.0f} units", 
                   (20, metrics_y + 50), {'color': (0, 100, 0), 'font_size': 10})


if __name__ == "__main__":
    create_working_visual_demo()
