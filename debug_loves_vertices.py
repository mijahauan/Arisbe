#!/usr/bin/env python3
"""
Debug script to analyze the missing second vertex issue in the Loves example.
EGIF: *x *y (Loves x y) ~[ (Happy x) ]
Expected: 2 vertices (*x and *y)
Actual: Only 1 vertex rendered
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.egif_parser_dau import EGIFParser
from src.graphviz_layout_engine_v2 import GraphvizLayoutEngine

def debug_loves_vertices():
    print("=== DEBUGGING MISSING SECOND VERTEX IN LOVES EXAMPLE ===")
    
    # Parse the problematic EGIF
    egif_text = "*x *y (Loves x y) ~[ (Happy x) ]"
    print(f"EGIF: {egif_text}")
    
    parser = EGIFParser(egif_text)
    result = parser.parse()
    egi = result.egi
    
    print(f"\n=== EGI STRUCTURE ===")
    print(f"Vertices: {len(egi.V)}")
    for i, v in enumerate(egi.V):
        print(f"  {i+1}. {v.id}: label='{v.label}', generic={v.is_generic}")
    
    print(f"\nEdges: {len(egi.E)}")
    for i, e in enumerate(egi.E):
        print(f"  {i+1}. {e.id}")
    
    print(f"\n=== NU MAPPING (Edge -> Vertices) ===")
    for edge_id, vertex_seq in egi.nu.items():
        rel_name = egi.rel.get(edge_id, "UNKNOWN")
        print(f"  {edge_id} ({rel_name}) -> {vertex_seq}")
    
    # Build vertex-to-predicates mapping (same as GUI logic)
    print(f"\n=== VERTEX CONNECTIONS MAPPING ===")
    vertex_connections = {}
    for predicate_id, vertex_sequence in egi.nu.items():
        for vertex_id in vertex_sequence:
            if vertex_id not in vertex_connections:
                vertex_connections[vertex_id] = []
            vertex_connections[vertex_id].append(predicate_id)
    
    print(f"Vertex connections: {vertex_connections}")
    
    # Check layout engine
    print(f"\n=== LAYOUT ENGINE OUTPUT ===")
    layout_engine = GraphvizLayoutEngine()
    layout_result = layout_engine.generate_layout(egi)
    
    vertex_primitives = [p for p in layout_result.spatial_primitives if p.element_type == 'vertex']
    print(f"Vertex spatial primitives: {len(vertex_primitives)}")
    for p in vertex_primitives:
        print(f"  {p.element_id}: {p.position}")
    
    # Identify the issue
    print(f"\n=== ISSUE ANALYSIS ===")
    print(f"EGI vertices: {len(egi.V)}")
    print(f"Vertex connections: {len(vertex_connections)}")
    print(f"Spatial primitives: {len(vertex_primitives)}")
    
    if len(egi.V) != len(vertex_connections):
        missing_from_connections = [v.id for v in egi.V if v.id not in vertex_connections]
        print(f"❌ MISSING FROM CONNECTIONS: {missing_from_connections}")
    
    if len(egi.V) != len(vertex_primitives):
        missing_from_layout = [v.id for v in egi.V if v.id not in [p.element_id for p in vertex_primitives]]
        print(f"❌ MISSING FROM LAYOUT: {missing_from_layout}")
    
    if len(egi.V) == len(vertex_connections) == len(vertex_primitives):
        print("✅ All vertices are present in connections and layout")

if __name__ == "__main__":
    debug_loves_vertices()
