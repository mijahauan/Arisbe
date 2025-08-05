#!/usr/bin/env python3
"""
Direct PySide6 Integration Test

This test bypasses the problematic CleanDiagramRenderer and renders EG diagrams
directly using PySide6, maintaining the beautiful quality we saw in the simple tests.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pyside6_backend import PySide6Backend
from canvas_backend import DrawingStyle
from egif_parser_dau import parse_egif
from constraint_layout_integration import ConstraintLayoutIntegration
import math


def render_eg_directly(canvas, layout_result, graph, title="EG Diagram"):
    """Render EG diagram directly using PySide6, following Dau's conventions."""
    
    canvas.clear()
    
    # Title
    canvas.draw_text(title, (20, 20), DrawingStyle(font_size=16, color=(0, 0, 128)))
    
    # Get spatial primitives from layout
    primitives = layout_result.primitives
    
    # Render in proper Z-order: cuts first, then lines, then vertices, then predicates
    
    # 1. Render cuts (background)
    for element_id, primitive in primitives.items():
        if primitive.element_type == 'cut':
            render_cut_oval(canvas, primitive)
    
    # 2. Render lines of identity (connecting elements)
    render_identity_lines(canvas, layout_result, graph)
    
    # 3. Render vertices (heavy lines of identity extending to predicates)
    for element_id, primitive in primitives.items():
        if primitive.element_type == 'vertex':
            render_vertex_as_heavy_line_unit(canvas, primitive, graph, primitives)
    
    # 4. Predicates are now rendered directly at the end of heavy lines in vertex rendering
    # (No separate predicate rendering needed)


def render_cut_oval(canvas, cut_primitive):
    """Render a cut as a proper oval following Dau's conventions."""
    
    bounds = cut_primitive.bounds  # (x1, y1, x2, y2)
    center_x = (bounds[0] + bounds[2]) / 2
    center_y = (bounds[1] + bounds[3]) / 2
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    
    # Create oval points
    oval_points = []
    for i in range(36):  # 36 points for smooth oval
        angle = i * 10 * math.pi / 180
        x = center_x + (width / 2) * math.cos(angle)
        y = center_y + (height / 2) * math.sin(angle)
        oval_points.append((x, y))
    
    # Draw as closed curve (fine line for cuts)
    canvas.draw_curve(oval_points, DrawingStyle(color=(0, 0, 0), line_width=1), closed=True)


def render_vertex_as_heavy_line_unit(canvas, vertex_primitive, graph, all_primitives):
    """Render vertex as heavy line of identity extending to connected predicates (Dau's formalism)."""
    
    vertex_id = vertex_primitive.element_id
    vertex_center = vertex_primitive.position
    
    # Find all predicates connected to this vertex
    connected_predicates = []
    for edge_id, vertex_sequence in graph.nu.items():
        if vertex_id in vertex_sequence:
            if edge_id in all_primitives:
                predicate_primitive = all_primitives[edge_id]
                connected_predicates.append(predicate_primitive)
    
    if not connected_predicates:
        # Unpredicated vertex - draw ONLY the identity spot (no stubs)
        canvas.draw_circle(vertex_center, 3, DrawingStyle(color=(0, 0, 0), fill_color=(0, 0, 0)))
        return
    
    # Draw heavy lines extending to each connected predicate with angular separation
    if len(connected_predicates) == 1:
        # Single predicate: direct line
        predicate_primitive = connected_predicates[0]
        predicate_pos = predicate_primitive.position
        
        # Calculate line from vertex center to predicate boundary
        dx = predicate_pos[0] - vertex_center[0]
        dy = predicate_pos[1] - vertex_center[1]
        distance = (dx*dx + dy*dy)**0.5
        
        if distance > 0:
            dx /= distance
            dy /= distance
            predicate_boundary = (predicate_pos[0] - dx * 20, predicate_pos[1] - dy * 20)
            canvas.draw_line(vertex_center, predicate_boundary, 
                           DrawingStyle(color=(0, 0, 0), line_width=3))
    
    else:
        # Multiple predicates: use angular separation and move predicates with lines
        import math
        
        # Get vertex label info to protect it from being drawn through
        vertex_label = None
        vertex_label_bounds = None
        if vertex_id in graph._vertex_map:
            vertex = graph._vertex_map[vertex_id]
            if vertex.label is not None:
                vertex_label = vertex.label
                # Estimate label bounds (rough approximation)
                label_width = len(f'"{vertex_label}"') * 6
                label_height = 12
                vertex_label_bounds = (
                    vertex_center[0] - label_width/2,
                    vertex_center[1] + 5,  # Below the spot
                    vertex_center[0] + label_width/2,
                    vertex_center[1] + 5 + label_height
                )
        
        # Calculate base angles to each predicate
        predicate_angles = []
        for predicate_primitive in connected_predicates:
            predicate_pos = predicate_primitive.position
            dx = predicate_pos[0] - vertex_center[0]
            dy = predicate_pos[1] - vertex_center[1]
            angle = math.atan2(dy, dx)
            predicate_angles.append((angle, predicate_primitive))
        
        # Sort by angle for consistent ordering
        predicate_angles.sort(key=lambda x: x[0])
        
        # Apply angular separation to prevent overlap
        min_angular_separation = math.pi / 6  # 30 degrees minimum separation
        
        for i, (base_angle, predicate_primitive) in enumerate(predicate_angles):
            # Calculate separated angle
            if len(predicate_angles) == 2:
                # Two predicates: spread them apart by at least min_angular_separation
                angle_diff = abs(predicate_angles[1][0] - predicate_angles[0][0])
                if angle_diff < min_angular_separation:
                    # Spread them apart
                    if i == 0:
                        separated_angle = base_angle - min_angular_separation/2
                    else:
                        separated_angle = base_angle + min_angular_separation/2
                else:
                    separated_angle = base_angle
            else:
                # Multiple predicates: distribute evenly with minimum separation
                total_span = min(math.pi, len(predicate_angles) * min_angular_separation)
                start_angle = base_angle - total_span/2
                separated_angle = start_angle + i * (total_span / (len(predicate_angles) - 1))
            
            # Calculate line length - avoid drawing through vertex label
            base_distance = ((predicate_primitive.position[0] - vertex_center[0])**2 + 
                           (predicate_primitive.position[1] - vertex_center[1])**2)**0.5
            line_length = max(base_distance * 0.8, 60)  # Substantial line length
            
            # Avoid drawing through vertex label area
            if vertex_label_bounds:
                # Check if line would pass through label area
                label_center_x = (vertex_label_bounds[0] + vertex_label_bounds[2]) / 2
                label_center_y = (vertex_label_bounds[1] + vertex_label_bounds[3]) / 2
                
                # If line angle would pass near label, adjust line length to stop before label
                line_end_x = vertex_center[0] + math.cos(separated_angle) * line_length
                line_end_y = vertex_center[1] + math.sin(separated_angle) * line_length
                
                # Check if line passes through label bounds
                if (vertex_label_bounds[0] <= line_end_x <= vertex_label_bounds[2] and
                    vertex_label_bounds[1] <= line_end_y <= vertex_label_bounds[3]):
                    # Shorten line to avoid label
                    line_length = max(25, line_length * 0.4)
            
            # Calculate final line endpoint
            line_end_x = vertex_center[0] + math.cos(separated_angle) * line_length
            line_end_y = vertex_center[1] + math.sin(separated_angle) * line_length
            
            # Draw heavy line of identity
            canvas.draw_line(vertex_center, (line_end_x, line_end_y), 
                           DrawingStyle(color=(0, 0, 0), line_width=3))
            
            # CRITICAL: Move predicate to the end of the heavy line
            # This ensures predicate moves with the line when angular constraints are applied
            predicate_name = graph.rel.get(predicate_primitive.element_id, "Unknown")
            canvas.draw_text(predicate_name, (line_end_x + 5, line_end_y - 5),
                           DrawingStyle(font_size=12, color=(0, 0, 0)))
    
    # Identity spot at vertex center
    canvas.draw_circle(vertex_center, 3, DrawingStyle(color=(0, 0, 0), fill_color=(0, 0, 0)))
    
    # If this is a constant vertex, display the constant value as compact unit
    vertex_id = vertex_primitive.element_id
    if vertex_id in graph._vertex_map:
        vertex = graph._vertex_map[vertex_id]
        if vertex.label is not None:  # This is a constant like "Socrates"
            # Position label to form compact unit, ensuring it stays within bounds
            bounds = vertex_primitive.bounds
            label_offset = 12  # Compact spacing
            label_x = vertex_center[0]
            label_y = vertex_center[1] + label_offset
            
            # Ensure label stays within vertex bounds (critical for area containment)
            max_label_y = bounds[3] - 8  # Leave small margin at bottom
            if label_y > max_label_y:
                label_y = max_label_y
            
            # Ensure label doesn't extend beyond horizontal bounds
            label_text = f'"{vertex.label}"'
            # Estimate text width (rough approximation)
            estimated_text_width = len(label_text) * 6  # ~6px per character
            
            # Adjust x position if text would extend beyond bounds
            if label_x + estimated_text_width/2 > bounds[2] - 2:
                label_x = bounds[2] - estimated_text_width/2 - 2
            if label_x - estimated_text_width/2 < bounds[0] + 2:
                label_x = bounds[0] + estimated_text_width/2 + 2
            
            label_pos = (label_x, label_y)
            canvas.draw_text(label_text, label_pos,
                           DrawingStyle(font_size=9, color=(0, 0, 128)))  # Slightly smaller font


def render_predicate_with_heavy_line_attachment(canvas, predicate_primitive, graph, all_primitives):
    """Render predicate text attached directly to heavy lines of identity (Dau's formalism)."""
    
    # Get predicate name from graph
    edge_id = predicate_primitive.element_id
    if edge_id in graph.rel:
        predicate_name = graph.rel[edge_id]
        
        # Draw predicate text
        canvas.draw_text(predicate_name, predicate_primitive.position,
                        DrawingStyle(font_size=12, color=(0, 0, 0)))
        
        # NO separate hook lines - predicates attach directly to heavy line ends
        # The heavy line of identity IS the connection (Dau's formalism)
        
        # Draw argument numbers for n-ary relations (if needed)
        if edge_id in graph.nu:
            vertex_sequence = graph.nu[edge_id]
            if len(vertex_sequence) > 1:
                # Only show argument numbers for multi-argument predicates
                for i, vertex_id in enumerate(vertex_sequence):
                    if vertex_id in all_primitives:
                        vertex_pos = all_primitives[vertex_id].position
                        predicate_pos = predicate_primitive.position
                        
                        # Position argument number near the predicate, towards the vertex
                        dx = vertex_pos[0] - predicate_pos[0]
                        dy = vertex_pos[1] - predicate_pos[1]
                        length = (dx*dx + dy*dy)**0.5
                        if length > 0:
                            # Normalize and position number
                            dx /= length
                            dy /= length
                            arg_pos = (predicate_pos[0] + dx * 20, predicate_pos[1] + dy * 20 - 5)
                            canvas.draw_text(str(i + 1), arg_pos,
                                           DrawingStyle(font_size=10, color=(128, 128, 128)))


def render_identity_lines(canvas, layout_result, graph):
    """Render lines of identity (heavy lines) connecting related vertices."""
    
    primitives = layout_result.primitives
    
    # Find vertices that should be connected by lines of identity
    # (This is a simplified version - full implementation would trace identity paths)
    
    for vertex_id, vertex_primitive in primitives.items():
        if vertex_primitive.element_type == 'vertex':
            # For now, just render a short identity line segment at each vertex
            pos = vertex_primitive.position
            
            # Draw a short heavy line segment (representing line of identity)
            line_start = (pos[0] - 15, pos[1])
            line_end = (pos[0] + 15, pos[1])
            canvas.draw_line(line_start, line_end,
                           DrawingStyle(color=(0, 0, 0), line_width=3))


def calculate_hook_endpoint(predicate_pos, vertex_pos):
    """Calculate where hook line should end (near predicate edge, not center)."""
    
    # Simple version: offset from predicate center toward vertex
    dx = vertex_pos[0] - predicate_pos[0]
    dy = vertex_pos[1] - predicate_pos[1]
    
    # Normalize and scale to predicate boundary
    length = math.sqrt(dx*dx + dy*dy)
    if length > 0:
        dx /= length
        dy /= length
        
        # Offset by approximate text width/height
        offset_x = dx * 30  # Approximate text width
        offset_y = dy * 8   # Approximate text height
        
        return (predicate_pos[0] + offset_x, predicate_pos[1] + offset_y)
    
    return predicate_pos


def test_direct_pyside6_integration():
    """Test direct PySide6 integration with proper EG rendering."""
    
    print("🎨 Testing Direct PySide6 Integration")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        {
            "name": "Simple Predicate",
            "egif": '(Human "Socrates")',
        },
        {
            "name": "Mixed Cut and Sheet",
            "egif": '(Human "Socrates") ~[ (Mortal "Socrates") ]',
        },
        {
            "name": "Double Negation",
            "egif": '~[ ~[ (Human "Socrates") ] ]',
        },
        {
            "name": "Sibling Cuts",
            "egif": '*x ~[ (Human x) ] ~[ (Mortal x) ]',
        }
    ]
    
    backend = PySide6Backend()
    if not backend.is_available():
        print("❌ PySide6 not available")
        return False
    
    layout_engine = ConstraintLayoutIntegration()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🎯 Test {i}: {test_case['name']}")
        print(f"   EGIF: {test_case['egif']}")
        
        try:
            # Parse and layout
            graph = parse_egif(test_case['egif'])
            layout_result = layout_engine.layout_graph(graph)
            
            # Create canvas
            canvas = backend.create_canvas(800, 600, f"Direct Integration: {test_case['name']}")
            
            # Render directly with proper EG conventions
            render_eg_directly(canvas, layout_result, graph, 
                             f"Test {i}: {test_case['name']} - EGIF: {test_case['egif']}")
            
            # Show window
            canvas.show()
            print("   ✓ Window displayed - close to continue...")
            canvas.run()
            
            print(f"   ✅ Test {i} completed!")
            
        except Exception as e:
            print(f"   ❌ Test {i} failed: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n🎉 Direct integration tests completed!")
    return True


if __name__ == "__main__":
    print("🚀 Direct PySide6 Integration Test")
    print("Bypassing problematic renderer, using direct PySide6 rendering")
    print("=" * 60)
    
    test_direct_pyside6_integration()
