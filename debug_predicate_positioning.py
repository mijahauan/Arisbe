#!/usr/bin/env python3
"""
Debug script to trace predicate positioning logic for Roberts' Disjunction.
"""

import sys
import os

# Add src to path
src_path = os.path.join(os.path.dirname(__file__), 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from egif_parser import parse_egif
from layout_engine import GraphvizLayoutEngine

def debug_predicate_positioning():
    """Debug predicate positioning for Roberts' Disjunction."""
    
    egif = '~[ ~[ (P "x") ] ~[ (Q "x") ] ]'
    print(f"=== Debugging Predicate Positioning ===")
    print(f"EGIF: {egif}")
    
    # Parse EGIF
    try:
        graph = parse_egif(egif)
        print(f"✓ Parsed successfully")
        print(f"Graph areas: {list(graph.areaMap.keys())}")
        
        # Debug vertex-edge relationships
        print(f"\n=== Vertex-Edge Analysis ===")
        for vertex_id, vertex in graph.vertices.items():
            print(f"Vertex {vertex_id}: {vertex}")
            connected_edges = [edge_id for edge_id, edge in graph.edges.items() 
                             if vertex_id in edge.nu.values()]
            print(f"  Connected edges: {connected_edges}")
            
        print(f"\n=== Edge-Area Analysis ===")
        for edge_id, edge in graph.edges.items():
            area = None
            for area_id, elements in graph.areaMap.items():
                if edge_id in elements:
                    area = area_id
                    break
            print(f"Edge {edge_id} ({edge.rel}): area={area}, nu={edge.nu}")
            
    except Exception as e:
        print(f"❌ Parse error: {e}")
        return
    
    # Create layout engine with debug output
    layout_engine = GraphvizLayoutEngine()
    
    # Temporarily add debug prints to layout engine
    original_calculate_method = layout_engine._calculate_predicate_position_in_area
    
    def debug_calculate_predicate_position_in_area(vertex_pos, predicate_index, total_predicates, available_bounds, all_layouts, area_offset=0):
        print(f"\n=== Predicate Position Calculation ===")
        print(f"vertex_pos: {vertex_pos}")
        print(f"predicate_index: {predicate_index}")
        print(f"total_predicates: {total_predicates}")
        print(f"available_bounds: {available_bounds}")
        print(f"area_offset: {area_offset}")
        
        result = original_calculate_method(vertex_pos, predicate_index, total_predicates, available_bounds, all_layouts, area_offset)
        print(f"calculated position: {result}")
        return result
    
    layout_engine._calculate_predicate_position_in_area = debug_calculate_predicate_position_in_area
    
    # Generate layout
    try:
        layout_result = layout_engine.generate_layout(graph)
        print(f"\n=== Layout Result ===")
        
        for element_id, layout_element in layout_result.elements.items():
            print(f"{element_id}: {layout_element.element_type} at {layout_element.bounds}")
            
    except Exception as e:
        print(f"❌ Layout error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_predicate_positioning()
