#!/usr/bin/env python3
"""
Debug script to examine what the Graphviz layout engine is producing
and why the DiagramRenderer isn't finding the correct elements.
"""

from egif_parser_dau import parse_egif
from graphviz_layout_engine_v2 import create_graphviz_layout

def debug_layout_output():
    """Debug the layout output to understand what's available for rendering."""
    
    test_egif = '(Human "Socrates") ~[ (Mortal "Socrates") ]'
    print(f"🔍 Debugging layout for: {test_egif}")
    print()
    
    # Step 1: Parse EGIF to EGI
    graph = parse_egif(test_egif)
    print("📊 EGI Structure:")
    print(f"  Vertices: {list(graph._vertex_map.keys())}")
    print(f"  Nu mapping: {dict(graph.nu)}")
    print(f"  Rel mapping: {dict(graph.rel)}")
    print(f"  Cuts: {[cut.id for cut in graph.Cut]}")
    print(f"  Areas: {dict(graph.area)}")
    print()
    
    # Step 2: Generate layout
    layout_result = create_graphviz_layout(graph)
    print("🗺️  Layout Result:")
    print(f"  Total primitives: {len(layout_result.primitives)}")
    print()
    
    # Step 3: Examine each primitive
    print("📍 Spatial Primitives:")
    for prim_id, primitive in layout_result.primitives.items():
        print(f"  {prim_id}:")
        print(f"    Type: {type(primitive).__name__}")
        print(f"    Position: {primitive.position}")
        if hasattr(primitive, 'bounds'):
            print(f"    Bounds: {primitive.bounds}")
        if hasattr(primitive, 'size'):
            print(f"    Size: {primitive.size}")
        print()
    
    # Step 4: Check what the DiagramRenderer is looking for
    print("🔎 DiagramRenderer Expectations:")
    
    # Check vertex positions
    print("  Vertex lookups:")
    for vertex_id in graph._vertex_map.keys():
        if vertex_id in layout_result.primitives:
            print(f"    ✅ {vertex_id} found at {layout_result.primitives[vertex_id].position}")
        else:
            print(f"    ❌ {vertex_id} NOT FOUND")
    
    # Check predicate positions
    print("  Predicate lookups:")
    for edge_id in graph.nu.keys():
        pred_node_id = f"pred_{edge_id}"
        if pred_node_id in layout_result.primitives:
            print(f"    ✅ {pred_node_id} found at {layout_result.primitives[pred_node_id].position}")
        elif edge_id in layout_result.primitives:
            print(f"    ✅ {edge_id} found at {layout_result.primitives[edge_id].position}")
        else:
            print(f"    ❌ {edge_id} (as {pred_node_id}) NOT FOUND")
    
    # Check cut positions
    print("  Cut lookups:")
    for cut in graph.Cut:
        if cut.id in layout_result.primitives:
            print(f"    ✅ {cut.id} found with bounds {layout_result.primitives[cut.id].bounds}")
        else:
            print(f"    ❌ {cut.id} NOT FOUND")

if __name__ == "__main__":
    debug_layout_output()
