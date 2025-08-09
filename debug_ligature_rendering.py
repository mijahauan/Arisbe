#!/usr/bin/env python3
"""
Debug script to identify why the y ligature is missing in the Loves example.
"""

import sys
import os
sys.path.insert(0, 'src')

from src.egif_parser_dau import EGIFParser
from src.graphviz_layout_engine_v2 import GraphvizLayoutEngine

def debug_ligature_rendering():
    # Parse the EGIF expression from the GUI
    egif = '*x *y (Loves x y) ~[ (Happy x) ]'
    parser = EGIFParser(egif)
    egi = parser.parse()

    # Generate layout
    layout_engine = GraphvizLayoutEngine()
    layout_result = layout_engine.create_layout_from_graph(egi)

    print('=== LIGATURE RENDERING DEBUG ===')
    
    # Step 1: Check ν mapping
    print('ν mapping:')
    for edge_id, vertex_sequence in egi.nu.items():
        print(f'  {edge_id}: {vertex_sequence}')
    
    # Step 2: Build vertex connections (same logic as GUI)
    vertex_connections = {}
    for predicate_id, vertex_sequence in egi.nu.items():
        for vertex_id in vertex_sequence:
            if vertex_id not in vertex_connections:
                vertex_connections[vertex_id] = []
            vertex_connections[vertex_id].append(predicate_id)
    
    print(f'\nVertex connections:')
    for vertex_id, connected_predicates in vertex_connections.items():
        print(f'  {vertex_id}: {connected_predicates} ({len(connected_predicates)} connections)')
    
    # Step 3: Check spatial primitives
    print(f'\nSpatial primitives:')
    vertex_positions = {}
    predicate_positions = {}
    
    for element_id, primitive in layout_result.primitives.items():
        if primitive.element_type == 'vertex':
            vertex_positions[element_id] = primitive.position
            print(f'  VERTEX {element_id}: {primitive.position}')
        elif primitive.element_type == 'predicate':
            predicate_positions[element_id] = primitive.position
            print(f'  PREDICATE {element_id}: {primitive.position}')
    
    # Step 4: Simulate ligature layout calculation for each vertex
    print(f'\nLigature layout simulation:')
    for vertex_id, connected_predicates in vertex_connections.items():
        print(f'\nProcessing vertex {vertex_id}:')
        print(f'  Connected predicates: {connected_predicates}')
        
        # Check if vertex has spatial primitive
        if vertex_id not in vertex_positions:
            print(f'  ❌ ERROR: No spatial primitive for vertex {vertex_id}')
            continue
        
        vertex_pos = vertex_positions[vertex_id]
        print(f'  Vertex position: {vertex_pos}')
        
        # Check predicate positions
        predicate_pos_list = []
        for pred_id in connected_predicates:
            if pred_id in predicate_positions:
                pred_pos = predicate_positions[pred_id]
                predicate_pos_list.append(pred_pos)
                print(f'  Predicate {pred_id} position: {pred_pos}')
            else:
                print(f'  ❌ ERROR: No spatial primitive for predicate {pred_id}')
        
        # Classify ligature type
        num_connections = len(connected_predicates)
        if num_connections == 0:
            ligature_type = 'standalone'
        elif num_connections == 1:
            ligature_type = 'single'
        elif num_connections == 2:
            ligature_type = 'two_connection'
        else:
            ligature_type = 'branching'
        
        print(f'  Ligature type: {ligature_type}')
        
        # Check if this would render
        if ligature_type == 'single' and predicate_pos_list:
            print(f'  ✅ Should render line: {vertex_pos} → {predicate_pos_list[0]}')
        elif ligature_type == 'two_connection' and len(predicate_pos_list) >= 2:
            print(f'  ✅ Should render curved line: {predicate_pos_list[0]} ↔ {predicate_pos_list[1]}')
        else:
            print(f'  ❌ ISSUE: Cannot render ligature - missing data')

if __name__ == "__main__":
    debug_ligature_rendering()
