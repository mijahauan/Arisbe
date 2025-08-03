#!/usr/bin/env python3
"""
Debug Identity Lines

Analyze how identity lines should be rendered in problematic cases.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from egif_parser_dau import EGIFParser
from layout_engine_clean import CleanLayoutEngine

def debug_identity_case(name: str, egif_string: str):
    """Debug a specific identity case."""
    print(f"\n{'='*60}")
    print(f"DEBUGGING: {name}")
    print(f"EGIF: {egif_string}")
    print('='*60)
    
    # Parse EGIF
    parser = EGIFParser(egif_string)
    graph = parser.parse()
    
    print(f"Sheet ID: {graph.sheet}")
    print(f"Vertices: {len(graph.V)}")
    print(f"Edges: {len(graph.E)}")
    print(f"Cuts: {len(graph.Cut)}")
    
    # Show vertex details
    print("\nVertex Analysis:")
    for v_id in graph.V:
        vertex = graph.get_vertex(v_id)
        area_id = None
        for area, elements in graph.area.items():
            if v_id in elements:
                area_id = area
                break
        area_name = "SHEET" if area_id == graph.sheet else f"CUT {area_id[-8:]}"
        print(f"  {v_id[-8:]}: label='{vertex.label}', generic={vertex.is_generic}, area={area_name}")
    
    # Show edge details
    print("\nEdge Analysis:")
    for e_id in graph.E:
        relation_name = graph.rel[e_id]
        vertex_sequence = graph.nu[e_id]
        area_id = None
        for area, elements in graph.area.items():
            if e_id in elements:
                area_id = area
                break
        area_name = "SHEET" if area_id == graph.sheet else f"CUT {area_id[-8:]}"
        print(f"  {e_id[-8:]}: {relation_name} -> {[v[-8:] for v in vertex_sequence]}, area={area_name}")
    
    # Show area containment
    print("\nArea Containment:")
    for area_id, elements in graph.area.items():
        area_name = "SHEET" if area_id == graph.sheet else f"CUT {area_id[-8:]}"
        vertices_in_area = [e for e in elements if e in graph.V]
        edges_in_area = [e for e in elements if e in graph.E]
        cuts_in_area = [e for e in elements if e in graph.Cut]
        print(f"  {area_name}: {len(vertices_in_area)} vertices, {len(edges_in_area)} edges, {len(cuts_in_area)} cuts")
    
    # Generate layout to see positioning
    layout_engine = CleanLayoutEngine()
    layout_result = layout_engine.layout_graph(graph)
    
    print("\nLayout Positioning:")
    for element_id, primitive in layout_result.primitives.items():
        if element_id in graph.V:
            vertex = graph.get_vertex(element_id)
            print(f"  Vertex {element_id[-8:]} ('{vertex.label}'): {primitive.position}")
        elif element_id in graph.E:
            relation_name = graph.rel[element_id]
            print(f"  Edge {element_id[-8:]} ({relation_name}): {primitive.position}")
    
    # Analyze the identity problem
    print("\nIdentity Analysis:")
    
    # Find vertices with the same label/identity
    vertex_groups = {}
    for v_id in graph.V:
        vertex = graph.get_vertex(v_id)
        key = vertex.label if not vertex.is_generic else f"VAR_{vertex.label}"
        if key not in vertex_groups:
            vertex_groups[key] = []
        vertex_groups[key].append(v_id)
    
    for identity, vertex_list in vertex_groups.items():
        if len(vertex_list) > 1:
            print(f"  Identity '{identity}' appears in {len(vertex_list)} vertices:")
            for v_id in vertex_list:
                vertex = graph.get_vertex(v_id)
                area_id = None
                for area, elements in graph.area.items():
                    if v_id in elements:
                        area_id = area
                        break
                area_name = "SHEET" if area_id == graph.sheet else f"CUT {area_id[-8:]}"
                pos = layout_result.primitives[v_id].position if v_id in layout_result.primitives else "N/A"
                print(f"    {v_id[-8:]}: {area_name}, position={pos}")
            
            print(f"  ❌ PROBLEM: Line of identity should connect these vertices directly,")
            print(f"     not pass through predicates or cut boundaries inappropriately!")
    
    return graph, layout_result

def main():
    """Debug the problematic identity cases."""
    
    # Case 1: Constants with same name in different areas
    debug_identity_case(
        "Case 1: Same Constant", 
        '(Human "Socrates") ~[ (Mortal "Socrates") ]'
    )
    
    # Case 3: Variable in different areas  
    debug_identity_case(
        "Case 3: Variable Identity", 
        '*x (Human x) ~[ (Mortal x) (Wise x) ]'
    )
    
    print(f"\n{'='*60}")
    print("CONCLUSION:")
    print("The current rendering draws lines from vertices to predicates,")
    print("but it should draw lines of identity BETWEEN vertices that")
    print("represent the same individual, regardless of area boundaries.")
    print('='*60)

if __name__ == "__main__":
    main()
