#!/usr/bin/env python3
"""
Debug argument order preservation in EGIF round-trip
Isolates exactly where the ν mapping order is being lost
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    from egi_core_dau import RelationalGraphWithCuts, create_empty_graph, create_vertex, create_edge
    from egif_parser_dau import parse_egif
    from egif_generator_dau import generate_egif
    from frozendict import frozendict
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all dependencies are installed")
    sys.exit(1)

def debug_argument_order():
    """Debug exactly where argument order is lost"""
    
    # Test case that shows the problem
    egif_input = '~[ (loves *x *y) ]'
    print(f"🔍 Debugging argument order for: {egif_input}")
    print("=" * 60)
    
    # Step 1: Parse EGIF
    print("\n1. Parsing EGIF...")
    graph = parse_egif(egif_input)
    
    # Step 2: Examine the ν mapping directly
    print("\n2. Examining ν mapping in parsed graph:")
    for edge in graph.E:
        vertex_sequence = graph.nu[edge.id]
        relation_name = graph.rel[edge.id]
        print(f"   Edge {edge.id} ({relation_name}):")
        print(f"   ν mapping: {vertex_sequence}")
        
        for i, vertex_id in enumerate(vertex_sequence):
            vertex = graph.get_vertex(vertex_id)
            print(f"     Arg {i+1}: {vertex_id} (generic={vertex.is_generic}, label={vertex.label})")
    
    # Step 3: Generate EGIF and check what happens
    print("\n3. Generating EGIF...")
    egif_output = generate_egif(graph)
    print(f"   Generated: {egif_output}")
    
    # Step 4: Parse the generated EGIF and compare ν mappings
    print("\n4. Parsing generated EGIF to compare ν mappings...")
    graph2 = parse_egif(egif_output)
    
    print("\n5. Comparing ν mappings:")
    edges1 = list(graph.E)
    edges2 = list(graph2.E)
    
    if len(edges1) != len(edges2):
        print(f"   ❌ Different number of edges: {len(edges1)} vs {len(edges2)}")
        return
    
    # Compare the ν mappings
    edge1 = edges1[0]  # Should be only one edge
    edge2 = edges2[0]
    
    seq1 = graph.nu[edge1.id]
    seq2 = graph2.nu[edge2.id]
    
    print(f"   Original ν: {seq1}")
    print(f"   Round-trip ν: {seq2}")
    
    # Check if the vertex labels are in the same order
    labels1 = []
    labels2 = []
    
    for vertex_id in seq1:
        vertex = graph.get_vertex(vertex_id)
        if vertex.is_generic:
            labels1.append(f"*{vertex.label or 'generic'}")
        else:
            labels1.append(f'"{vertex.label}"')
    
    for vertex_id in seq2:
        vertex = graph2.get_vertex(vertex_id)
        if vertex.is_generic:
            labels2.append(f"*{vertex.label or 'generic'}")
        else:
            labels2.append(f'"{vertex.label}"')
    
    print(f"   Original labels: {labels1}")
    print(f"   Round-trip labels: {labels2}")
    
    if labels1 == labels2:
        print("   ✅ Argument order preserved!")
    else:
        print("   ❌ Argument order LOST!")
        print("   🔧 This violates Dau's formalism - ν mapping must be preserved")

def test_multiple_cases():
    """Test multiple argument order cases"""
    test_cases = [
        '(loves *x *y)',
        '(between *a *b *c)',
        '~[ (loves *x *y) ]',
        '(loves "Alice" *x)',
        '(loves *x "Bob")',
    ]
    
    print("\n" + "=" * 60)
    print("Testing multiple argument order cases")
    print("=" * 60)
    
    for egif_input in test_cases:
        print(f"\n🧪 Testing: {egif_input}")
        try:
            graph = parse_egif(egif_input)
            egif_output = generate_egif(graph)
            
            if egif_input.strip() == egif_output.strip():
                print(f"   ✅ Perfect preservation: {egif_output}")
            else:
                print(f"   ⚠️  Changed to: {egif_output}")
                
                # Check if it's just variable renaming vs actual order change
                # This requires more sophisticated comparison
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    print("Debugging Argument Order Preservation in EGIF Round-trip")
    print("Testing Dau's ν mapping preservation")
    
    debug_argument_order()
    test_multiple_cases()
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("The ν mapping in Dau's formalism MUST preserve exact argument order.")
    print("Any loss of order violates the mathematical foundation of EG.")
    print("=" * 60)
