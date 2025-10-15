#!/usr/bin/env python3
"""Debug script to check vertex area assignments"""

import sys
sys.path.insert(0, 'src')

from pathlib import Path
from egi_io import load_egi_json
from entity_storage import EntityStorageManager

# Load the Socrates example
corpus_path = Path("tomos/graphs")
storage = EntityStorageManager(corpus_path)

# Try Roberts domain modeling example (what user is looking at)
entity = storage.load_entity("roberts_domain_modeling")
egi = entity.current_egi

print("=== EGI Structure ===")
print(f"Vertices: {[v.id for v in egi.V]}")
print(f"Edges: {[e.id for e in egi.E]}")
print(f"Cuts: {[c.id for c in egi.Cut]}")
print()

print("=== Area Assignments ===")
for area_id, elements in sorted(egi.area.items()):
    print(f"{area_id}: {list(elements)}")
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
