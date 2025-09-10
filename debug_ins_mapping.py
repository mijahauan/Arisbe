#!/usr/bin/env python3
"""
Debug the exact INS transformation mapping to understand why we're getting wrong results.
"""

from src.egif_parser_dau import parse_egif
from src.egif_generator_dau import EGIFGenerator
import re

def debug_ins_mapping():
    """Debug the INS transformation mapping step by step."""
    
    # Original graph
    original_egif = "~[ *x *y (Loves x y) ]"
    original_egi = parse_egif(original_egif)
    
    print("=== Step 1: Original Graph Analysis ===")
    print(f"Original EGIF: {original_egif}")
    
    # Get variable mapping
    generator = EGIFGenerator(original_egi)
    regenerated_egif = generator.generate()
    var_pattern = r'\*([a-zA-Z][a-zA-Z0-9]*)'
    declared_vars = re.findall(var_pattern, regenerated_egif)
    
    original_var_to_vertex = {}
    for edge_id, vertex_sequence in original_egi.nu.items():
        if edge_id in original_egi.rel:
            for i, vertex_id in enumerate(vertex_sequence):
                if i < len(declared_vars):
                    var_name = declared_vars[i]
                    if var_name not in original_var_to_vertex:
                        original_var_to_vertex[var_name] = vertex_id
    
    print(f"Variable mapping: {original_var_to_vertex}")
    
    # Parse insertion
    insertion_spec = "(Hates y x)"
    relation_match = re.match(r'\(\s*(\w+)\s+(.*?)\s*\)', insertion_spec.strip())
    relation_name = relation_match.group(1)
    args_str = relation_match.group(2)
    arg_tokens = re.findall(r'(\*?\w+|"[^"]*")', args_str)
    
    print(f"\n=== Step 2: Insertion Analysis ===")
    print(f"Insertion spec: {insertion_spec}")
    print(f"Relation name: {relation_name}")
    print(f"Arguments: {arg_tokens}")
    
    # Map arguments
    mapped_vertex_sequence = []
    for arg in arg_tokens:
        var_name = arg.lstrip('*')
        if var_name in original_var_to_vertex:
            mapped_vertex_sequence.append(original_var_to_vertex[var_name])
            print(f"  {var_name} -> {original_var_to_vertex[var_name]}")
        else:
            print(f"  ERROR: {var_name} not found")
    
    print(f"Mapped vertex sequence: {tuple(mapped_vertex_sequence)}")
    
    # Simulate the transformation
    print(f"\n=== Step 3: Expected Result ===")
    print(f"New edge should connect: {tuple(mapped_vertex_sequence)}")
    print(f"With relation: {relation_name}")
    print(f"Expected EGIF: ~[ *x *y (Loves x y) (Hates y x) ]")
    
    # Check what we actually get by examining the vertex order
    print(f"\n=== Step 4: Vertex Order Check ===")
    for edge_id, vertex_sequence in original_egi.nu.items():
        if original_egi.rel[edge_id] == "Loves":
            print(f"Original Loves edge: {vertex_sequence}")
            print(f"  First vertex ({vertex_sequence[0]}) = x")
            print(f"  Second vertex ({vertex_sequence[1]}) = y")
    
    print(f"New Hates edge: {tuple(mapped_vertex_sequence)}")
    print(f"  First vertex ({mapped_vertex_sequence[0]}) = y")  
    print(f"  Second vertex ({mapped_vertex_sequence[1]}) = x")
    print(f"This should give us (Hates y x)")

if __name__ == "__main__":
    debug_ins_mapping()
