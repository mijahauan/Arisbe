#!/usr/bin/env python3
"""
Debug Vertex Identity Issue

Investigate why identical constants create separate vertices instead of shared ones.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from egif_parser_dau import EGIFParser

def debug_vertex_identity():
    """Debug the vertex identity issue in Case 1."""
    
    print('=== Debugging Vertex Identity Issue ===')
    print('Case: (Human "Socrates") ~[ (Mortal "Socrates") ]')
    print('Expected: 1 vertex for "Socrates" connected to both predicates')
    print('='*60)
    
    # Parse the problematic case
    parser = EGIFParser('(Human "Socrates") ~[ (Mortal "Socrates") ]')
    graph = parser.parse()
    
    print(f'Total vertices: {len(graph.V)}')
    print(f'Total edges: {len(graph.E)}')
    print(f'Total cuts: {len(graph.Cut)}')
    
    # Examine vertices
    print('\nVertex Analysis:')
    vertex_labels = {}
    for vertex in graph.V:
        print(f'  Vertex ID: {vertex.id}')
        print(f'    Label: "{vertex.label}"')
        print(f'    Generic: {vertex.is_generic}')
        
        # Track labels for duplicate detection
        if vertex.label not in vertex_labels:
            vertex_labels[vertex.label] = []
        vertex_labels[vertex.label].append(vertex.id)
        print()
    
    # Check for duplicate labels
    print('Label Analysis:')
    for label, vertex_ids in vertex_labels.items():
        if len(vertex_ids) > 1:
            print(f'  ❌ DUPLICATE: Label "{label}" appears in {len(vertex_ids)} vertices: {vertex_ids}')
        else:
            print(f'  ✅ UNIQUE: Label "{label}" appears in 1 vertex: {vertex_ids[0]}')
    
    # Examine edges and their connections
    print('\nEdge Analysis:')
    for edge_id in graph.E:
        relation_name = graph.rel[edge_id]
        vertex_sequence = graph.nu[edge_id]
        print(f'  Edge: {relation_name}')
        print(f'    Connected to vertices: {[v for v in vertex_sequence]}')
        
        # Show which vertex labels are connected
        connected_labels = []
        for vertex_id in vertex_sequence:
            for vertex in graph.V:
                if vertex.id == vertex_id:
                    connected_labels.append(vertex.label)
                    break
        print(f'    Connected to labels: {connected_labels}')
        print()
    
    # Show area containment
    print('Area Containment:')
    for area_id, elements in graph.area.items():
        area_name = 'SHEET' if area_id == graph.sheet else f'CUT {area_id[-8:]}'
        vertices_in_area = [e for e in elements if any(v.id == e for v in graph.V)]
        edges_in_area = [e for e in elements if e in graph.E]
        print(f'  {area_name}:')
        print(f'    Vertices: {vertices_in_area}')
        print(f'    Edges: {edges_in_area}')
    
    print('\n' + '='*60)
    print('DIAGNOSIS:')
    if len(vertex_labels.get('Socrates', [])) > 1:
        print('❌ BUG CONFIRMED: Multiple vertices created for same constant "Socrates"')
        print('   This violates EG formalism - identical constants should share vertices')
        print('   Root cause: EGIF parser creates separate vertices for each predicate occurrence')
        print('   Fix needed: Parser should reuse existing vertices for identical constants')
    else:
        print('✅ No duplicate vertex issue detected')
    
    return graph

if __name__ == "__main__":
    debug_vertex_identity()
