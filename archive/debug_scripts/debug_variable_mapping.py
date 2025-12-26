#!/usr/bin/env python3
"""
Debug variable mapping in INS transformation.
"""

from src.egif_parser_dau import parse_egif
from src.egif_generator_dau import EGIFGenerator

def debug_variable_mapping():
    """Debug how variables are being mapped in the insertion."""
    print("=== Debugging Variable Mapping ===")
    
    # Parse original EGIF
    original_egif = "~[ *x *y (Loves x y) ]"
    original_egi = parse_egif(original_egif)
    
    print(f"Original EGIF: {original_egif}")
    print("Original vertices:")
    for vertex in original_egi.V:
        vertex_obj = original_egi.get_vertex(vertex.id)
        print(f"  {vertex.id}: label='{vertex_obj.label}', is_generic={vertex_obj.is_generic}")
    
    # Parse insertion content with context
    insertion_spec = "(Hates y x)"
    context_egif = "*x *y (Hates y x)"  # Provide context
    insertion_egi = parse_egif(context_egif)
    
    print(f"\nInsertion EGIF: {context_egif}")
    print("Insertion vertices:")
    for vertex in insertion_egi.V:
        vertex_obj = insertion_egi.get_vertex(vertex.id)
        print(f"  {vertex.id}: label='{vertex_obj.label}', is_generic={vertex_obj.is_generic}")
    
    # Test variable matching logic
    print("\nVariable matching:")
    element_id_mapping = {}
    
    for vertex in insertion_egi.V:
        vertex_obj = insertion_egi.get_vertex(vertex.id)
        matching_vertex_id = None
        
        print(f"  Looking for match for insertion vertex {vertex.id} (label='{vertex_obj.label}')")
        
        if vertex_obj.is_generic:
            # For generic vertices, find existing vertex with same variable name
            for orig_vertex in original_egi.V:
                orig_vertex_obj = original_egi.get_vertex(orig_vertex.id)
                print(f"    Checking original vertex {orig_vertex.id} (label='{orig_vertex_obj.label}')")
                if (orig_vertex_obj.is_generic and 
                    orig_vertex_obj.label == vertex_obj.label):
                    matching_vertex_id = orig_vertex.id
                    print(f"    ✅ MATCH FOUND: {vertex.id} -> {matching_vertex_id}")
                    break
        
        if matching_vertex_id:
            element_id_mapping[vertex.id] = matching_vertex_id
        else:
            element_id_mapping[vertex.id] = vertex.id
            print(f"    ❌ NO MATCH: using original ID {vertex.id}")
    
    print(f"\nFinal mapping: {element_id_mapping}")
    
    # Test edge mapping
    print("\nEdge mapping:")
    for edge in insertion_egi.E:
        if edge.id in insertion_egi.nu:
            old_sequence = insertion_egi.nu[edge.id]
            new_sequence = tuple(element_id_mapping.get(vid, vid) for vid in old_sequence)
            print(f"  Edge {edge.id}: {old_sequence} -> {new_sequence}")
            relation_name = insertion_egi.rel.get(edge.id, "Unknown")
            print(f"    Relation: {relation_name}")

if __name__ == "__main__":
    debug_variable_mapping()
