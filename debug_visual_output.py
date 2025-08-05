#!/usr/bin/env python3
"""
Debug Visual Output - Find Why Rendering Claims Don't Match Reality

The user is absolutely right: the generated images show no heavy lines, 
no predicates, and are not compliant with Dau conventions. Let's debug
what's actually happening in the rendering pipeline.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def debug_simple_case():
    """Debug a simple case to see what's actually being rendered."""
    
    print("🔍 DEBUGGING VISUAL OUTPUT")
    print("=" * 40)
    print("User feedback: No heavy lines, no predicates, not compliant")
    print("Let's trace what's actually happening...")
    print()
    
    try:
        from egif_parser_dau import parse_egif
        from graphviz_layout_engine_v2 import GraphvizLayoutEngine
        
        # Simple test case
        egif = '*x (Human x)'
        print(f"📋 Test EGIF: {egif}")
        print("   Expected: Heavy identity line + predicate text + vertex spot")
        print()
        
        # Parse EGIF
        graph = parse_egif(egif)
        print(f"✅ Parsed Graph:")
        print(f"   Vertices: {len(graph.V)} - {[v.id for v in graph.V]}")
        print(f"   Edges: {len(graph.E)} - {[e.id for e in graph.E]}")
        print(f"   Relations: {graph.rel}")
        print()
        
        # Generate layout
        layout_engine = GraphvizLayoutEngine()
        layout_result = layout_engine.create_layout_from_graph(graph)
        
        print(f"✅ Layout Result:")
        print(f"   Primitives: {len(layout_result.primitives)}")
        print(f"   Canvas bounds: {layout_result.canvas_bounds}")
        print()
        
        print(f"🔍 Detailed Primitive Analysis:")
        for primitive_id, primitive in layout_result.primitives.items():
            print(f"   {primitive_id}:")
            print(f"     Type: {primitive.element_type}")
            print(f"     Position: {primitive.position}")
            if hasattr(primitive, 'bounds'):
                print(f"     Bounds: {primitive.bounds}")
            if hasattr(primitive, 'coordinates'):
                print(f"     Coordinates: {primitive.coordinates}")
            print()
        
        # Now let's see what the contract system produces
        from pyside6_contract_integration import LayoutToPySide6Converter
        from diagram_renderer_clean import RenderingTheme
        
        converter = LayoutToPySide6Converter(RenderingTheme())
        request = converter.convert_layout_to_request(
            layout_result, graph, 800, 600, "Debug Test"
        )
        
        print(f"🔍 Contract Conversion Analysis:")
        print(f"   Drawing commands: {len(request.drawing_commands)}")
        for i, cmd in enumerate(request.drawing_commands):
            print(f"   Command {i+1}:")
            print(f"     Type: {cmd.command_type}")
            print(f"     Coordinates: {cmd.coordinates}")
            print(f"     Style: line_width={cmd.style.line_width}, radius={cmd.style.radius}")
            if cmd.text:
                print(f"     Text: '{cmd.text}'")
            print(f"     Element ID: {cmd.element_id}")
            print()
        
        # Let's also check what the PySide6Canvas actually receives
        print(f"🔍 Expected Visual Elements for '{egif}':")
        print(f"   1. VERTEX SPOT: Black filled circle, radius 3.5")
        print(f"   2. PREDICATE TEXT: 'Human' text label")
        print(f"   3. IDENTITY LINE: Heavy black line (width 4.0) connecting vertex to predicate")
        print()
        
        print(f"❓ Questions to investigate:")
        print(f"   - Are the drawing commands being created correctly?")
        print(f"   - Is the PySide6Canvas actually drawing them?")
        print(f"   - Are the styles being applied correctly?")
        print(f"   - Is the canvas saving correctly?")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def debug_canvas_drawing():
    """Debug what the canvas is actually drawing."""
    
    print(f"\n🎨 DEBUGGING CANVAS DRAWING")
    print("-" * 30)
    
    try:
        # Let's create a minimal test with direct canvas calls
        from pyside6_canvas import PySide6Canvas
        
        print("Creating test canvas...")
        canvas = PySide6Canvas(400, 300, "Debug Canvas")
        
        print("Drawing test elements:")
        
        # Test 1: Draw a heavy line
        print("  1. Heavy identity line (width 4.0)")
        canvas.draw_line((50, 150), (200, 150), {'width': 4.0, 'fill': 'rgb(0,0,0)'})
        
        # Test 2: Draw a vertex spot
        print("  2. Vertex spot (radius 3.5)")
        canvas.draw_circle((50, 150), 3.5, {'fill': 'rgb(0,0,0)', 'outline': 'rgb(0,0,0)'})
        
        # Test 3: Draw predicate text
        print("  3. Predicate text")
        canvas.draw_text((200, 140), "Human", {'font': ('Arial', 12, 'normal'), 'fill': 'rgb(0,0,0)'})
        
        # Test 4: Draw a cut
        print("  4. Cut boundary (width 1.0)")
        canvas.draw_oval(100, 100, 300, 200, {'width': 1.0, 'outline': 'rgb(0,0,0)'})
        
        print("Saving test canvas...")
        canvas.save_to_file("debug_canvas_test.png")
        
        print("✅ Debug canvas saved as 'debug_canvas_test.png'")
        print("👀 Please check this file to see if basic drawing works")
        
        return True
        
    except Exception as e:
        print(f"❌ Canvas debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def analyze_existing_output():
    """Analyze what's actually in the existing PNG files."""
    
    print(f"\n📊 ANALYZING EXISTING OUTPUT")
    print("-" * 30)
    
    # Check file sizes and existence
    test_files = [
        "visual_example_simple_predicate.png",
        "visual_example_identity_line.png",
        "contract_test_1.png"
    ]
    
    for filename in test_files:
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"✅ {filename}: {size:,} bytes")
            
            # Very small files might indicate empty/minimal content
            if size < 5000:
                print(f"   ⚠️  Suspiciously small file size - might be mostly empty")
            elif size > 50000:
                print(f"   ✅ Reasonable file size - likely has content")
            else:
                print(f"   ? Moderate file size - needs visual inspection")
        else:
            print(f"❌ {filename}: Not found")
    
    print(f"\n🔍 DIAGNOSIS:")
    print(f"The user reports the images show:")
    print(f"  ❌ No heavy lines")
    print(f"  ❌ No predicates") 
    print(f"  ❌ Not compliant with Dau conventions")
    print(f"")
    print(f"This suggests:")
    print(f"  1. Canvas drawing commands may not be working")
    print(f"  2. Style parameters may not be applied")
    print(f"  3. Elements may be positioned outside visible area")
    print(f"  4. Canvas save may not be capturing drawn elements")

if __name__ == "__main__":
    print("Visual Output Debugging")
    print("User is absolutely right - let's find the real issues")
    print()
    
    # Debug the pipeline step by step
    debug_simple_case()
    debug_canvas_drawing()
    analyze_existing_output()
    
    print(f"\n🎯 NEXT STEPS:")
    print(f"1. Visually inspect debug_canvas_test.png")
    print(f"2. If basic canvas drawing works, debug the pipeline")
    print(f"3. If basic canvas drawing fails, fix canvas implementation")
    print(f"4. Do NOT claim success until visually verified")
