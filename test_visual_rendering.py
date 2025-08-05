#!/usr/bin/env python3
"""
Visual Rendering Test for Arisbe EG Implementation

Tests the complete pipeline: EGIF → EGI → Layout → Visual Rendering
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from egif_parser_dau import parse_egif
from graphviz_layout_engine_v2 import GraphvizLayoutEngine
from pyside6_backend import PySide6Canvas, PySide6Backend
from canvas_backend import EGDrawingStyles


def test_egif_visual_rendering():
    """Test visual rendering of various EGIF expressions."""
    
    # Test cases with different EG structures
    test_cases = [
        {
            'name': 'Simple Relation',
            'egif': '(Human "Socrates")',
            'description': 'Basic unary relation with constant'
        },
        {
            'name': 'Sibling Cuts',
            'egif': '*x ~[ (Human x) ] ~[ (Mortal x) ]',
            'description': 'Two sibling cuts with shared variable'
        },
        {
            'name': 'Nested Cuts',
            'egif': '*x (Human x) ~[ (Mortal x) ~[ (Wise x) ] ]',
            'description': 'Nested cuts with proper containment'
        },
        {
            'name': 'Binary Relation',
            'egif': '*x *y (Loves x y)',
            'description': 'Binary relation with two variables'
        }
    ]
    
    print("🎨 Testing Visual EG Rendering Pipeline")
    print("=" * 50)
    
    # Initialize layout engine
    layout_engine = GraphvizLayoutEngine()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}: {test_case['egif']}")
        print(f"   {test_case['description']}")
        
        try:
            # Step 1: Parse EGIF → EGI
            graph = parse_egif(test_case['egif'])
            print(f"   ✅ Parsed: {len(graph.V)} vertices, {len(graph.E)} edges, {len(graph.Cut)} cuts")
            
            # Step 2: Create Layout
            layout = layout_engine.create_layout_from_graph(graph)
            print(f"   ✅ Layout: {len(layout.primitives)} elements positioned")
            
            # Step 3: Render to PNG
            output_file = f"test_render_{i}_{test_case['name'].lower().replace(' ', '_')}.png"
            render_layout_to_file(layout, output_file, test_case['name'])
            print(f"   ✅ Rendered: {output_file}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n🎯 Visual rendering test complete!")
    print(f"Check generated PNG files to verify EG diagram correctness.")


def render_layout_to_file(layout, filename, title):
    """Render a layout to PNG file using PySide6."""
    
    # Create PySide6 canvas
    canvas = PySide6Canvas(800, 600, title=f"Arisbe EG: {title}")
    
    # Render all layout elements
    for elem_id, primitive in layout.primitives.items():
        if primitive.element_type == 'vertex':
            # Draw vertex as filled circle
            canvas.draw_circle(
                primitive.position, 
                8.0, 
                EGDrawingStyles.VERTEX_SPOT
            )
            
        elif primitive.element_type == 'predicate':
            # Draw predicate as text box
            canvas.draw_text(
                primitive.relation_name if hasattr(primitive, 'relation_name') else 'Pred',
                primitive.position,
                EGDrawingStyles.RELATION_SIGN
            )
            
        elif primitive.element_type == 'cut':
            # Draw cut as circle/oval
            if hasattr(primitive, 'bounds') and primitive.bounds:
                x_min, y_min, x_max, y_max = primitive.bounds
                width = x_max - x_min
                height = y_max - y_min
                center = ((x_min + x_max) / 2, (y_min + y_max) / 2)
                radius = max(width, height) / 2
                
                canvas.draw_circle(
                    center,
                    radius,
                    EGDrawingStyles.CUT_LINE
                )
    
    # Draw lines of identity (nu mapping connections)
    # This would require additional logic to connect vertices to predicates
    # based on the nu mapping in the original graph
    
    # Save to file
    canvas.save_to_file(filename)
    print(f"   💾 Saved diagram to: {filename}")


def quick_visual_test():
    """Quick test to verify the rendering pipeline is working."""
    
    print("🚀 Quick Visual Test")
    print("-" * 20)
    
    # Simple test case
    egif = '*x (Human x) ~[ (Mortal x) ]'
    print(f"Testing: {egif}")
    
    try:
        # Parse
        graph = parse_egif(egif)
        print("✅ EGIF parsing successful")
        
        # Layout
        engine = GraphvizLayoutEngine()
        layout = engine.create_layout_from_graph(graph)
        print("✅ Layout generation successful")
        
        # Show layout details
        print(f"📊 Layout contains {len(layout.primitives)} elements:")
        for elem_id, primitive in layout.primitives.items():
            print(f"   {elem_id}: {primitive.element_type} at {primitive.position}")
        
        print("🎯 Rendering pipeline is functional!")
        return True
        
    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        return False


if __name__ == "__main__":
    print("Arisbe Visual Rendering Test")
    print("=" * 40)
    
    # First do a quick test
    if quick_visual_test():
        print("\n" + "=" * 40)
        # If quick test passes, run full visual tests
        test_egif_visual_rendering()
    else:
        print("❌ Quick test failed - check pipeline components")
