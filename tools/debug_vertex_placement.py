#!/usr/bin/env python3
"""Debug script to check vertex area assignments"""

import sys
sys.path.insert(0, 'src')

from pathlib import Path
from egi_io import load_egi_json
from entity_storage import EntityStorageManager

# Load the Socrates example
corpus_path = Path("corpus/graphs")
storage = EntityStorageManager(corpus_path)

# Check the "shared_constant_disjunction" from user's screenshot
entity = storage.load_entity("shared_constant_disjunction")
egi = entity.current_egi

print(f"=== EGIF ===")
print(entity.get_current_egif())
print()
print(f"=== Expected Structure from EGIF ===")
print("EGIF: (Human \"Socrates\") ~[ ~[ (Mortal \"Socrates\") ] ]")
print("Should mean:")
print("  SHEET: Human edge, vertex 'Socrates', first cut")
print("  First cut: second cut")
print("  Second cut: Mortal edge")
print()

print("=== EGI Structure ===")
print(f"Vertices: {[v.id for v in egi.V]}")
print(f"Edges: {[e.id for e in egi.E]}")
print(f"Cuts: {[c.id for c in egi.Cut]}")
print()

print("=== Area Assignments ===")
for area_id, elements in sorted(egi.area.items()):
    # Translate element IDs to readable names
    readable = []
    for elem_id in elements:
        # Check if it's an edge
        edge = next((e for e in egi.E if e.id == elem_id), None)
        if edge:
            rel_name = egi.rel.get(elem_id, "?")
            readable.append(f"{rel_name}({elem_id[:8]})")
        # Check if it's a vertex
        elif any(v.id == elem_id for v in egi.V):
            readable.append(f"vertex({elem_id[:8]})")
        # Check if it's a cut
        elif any(c.id == elem_id for c in egi.Cut):
            readable.append(f"cut({elem_id[:8]})")
        else:
            readable.append(elem_id[:8])
    
    area_name = "SHEET" if area_id == egi.sheet else f"cut({area_id[:8]})"
    print(f"{area_name}: {readable}")
print()

print("=== Nu Mapping (edge -> vertices) ===")
for edge_id, vertex_seq in egi.nu.items():
    edge_obj = next((e for e in egi.E if e.id == edge_id), None)
    rel_name = egi.rel.get(edge_id, "?")
    print(f"{edge_id} ({rel_name}): {vertex_seq}")
print()

# Find which area each vertex is in
print("=== Vertex Locations ===")
for vertex in egi.V:
    for area_id, elements in egi.area.items():
        if vertex.id in elements:
            print(f"Vertex {vertex.id}: in area {area_id}")
            break
    else:
        print(f"Vertex {vertex.id}: NOT FOUND IN ANY AREA!")
