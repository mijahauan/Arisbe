#!/usr/bin/env python3

"""Debug script to examine vertex sequences in nu mapping."""

from src.egif_transformation_interface import EGIFTransformationInterface, TransformationRequest
from src.egif_generator_dau import EGIFGenerator

def debug_vertex_sequences():
    print("=== Debug Vertex Sequences in Nu Mapping ===")
    
    interface = EGIFTransformationInterface()
    original_egif = '~[ *x *y (Loves x y) ]'
    
    request = TransformationRequest(
        source_egif=original_egif,
        rule_name='INS',
        target_area_description='first_cut',
        operation_details={'insert_content': '(Hates y x)'},
        description='Insert (Hates y x) into the negative area'
    )
    
    response = interface.apply_transformation(request)
    result_egi = response.result_egi
    
    print(f"Original EGIF: {original_egif}")
    print(f"Result EGIF: {response.result_egif}")
    print()
    
    # Examine the nu mapping for all edges
    print("=== Nu Mapping (Edge -> Vertex Sequence) ===")
    for edge_id in result_egi._edge_map.keys():
        vertex_sequence = result_egi.nu[edge_id]
        relation_name = result_egi.rel[edge_id]
        print(f"Edge {edge_id}: {relation_name} -> vertices {vertex_sequence}")
        
        # Show vertex labels for each vertex in sequence
        vertex_labels = []
        for vertex_id in vertex_sequence:
            vertex = result_egi.get_vertex(vertex_id)
            vertex_labels.append(f"{vertex_id}({vertex.label})")
        print(f"  Vertex details: {vertex_labels}")
    
    print()
    
    # Show how EGIF generator assigns variable names
    print("=== EGIF Generator Variable Assignment ===")
    generator = EGIFGenerator(result_egi)
    result_egif = generator.generate()  # This calls _assign_labels internally
    
    print("Vertex labels assigned by generator:")
    for vertex_id, label in generator.vertex_labels.items():
        vertex = result_egi.get_vertex(vertex_id)
        print(f"  Vertex {vertex_id}({vertex.label}) -> variable '{label}'")
    
    print()
    print("=== Expected vs Actual Relation Generation ===")
    for edge_id in result_egi._edge_map.keys():
        vertex_sequence = result_egi.nu[edge_id]
        relation_name = result_egi.rel[edge_id]
        
        # Show what the generator produces
        actual_relation = generator._generate_relation(edge_id)
        print(f"Edge {edge_id} ({relation_name}):")
        print(f"  Vertex sequence: {vertex_sequence}")
        print(f"  Generated relation: {actual_relation}")
        
        # Show what we expect based on insertion
        if relation_name == "Hates":
            print(f"  Expected: (Hates y x)")
        elif relation_name == "Loves":
            print(f"  Expected: (Loves x y)")
    
    print()
    print("=== Analysis ===")
    print("The issue is that the EGIF generator assigns variables based on vertex processing order,")
    print("not preserving the original variable-to-vertex mapping from the insertion.")

if __name__ == "__main__":
    debug_vertex_sequences()
