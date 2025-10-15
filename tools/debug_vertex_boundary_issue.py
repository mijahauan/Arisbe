#!/usr/bin/env python3
"""
Debug why vertex appears near cut boundary in unified layout.
Focus on the shared_constant_disjunction graph.
"""

import sys
sys.path.insert(0, 'src')

from pathlib import Path
from entity_storage import EntityStorageManager
from definitive_egi_layout_engine import DefinitiveEGILayoutEngine
from style_loader import StyleLoader

storage = EntityStorageManager(Path('tomos/graphs'))
entity = storage.load_entity('shared_constant_disjunction')
egi = entity.current_egi

layout_engine = DefinitiveEGILayoutEngine()
style_loader = StyleLoader()
style = style_loader.load_default_style()

print("EGIF:", entity.get_current_egif())
print("Expected: (Human \"Socrates\") ~[ ~[ (Mortal \"Socrates\") ] ]")
print()
print("Logical structure:")
print("  SHEET: vertex 'Socrates', edge Human, cut1")
print("  Cut1: cut2")
print("  Cut2: edge Mortal")
print()

# Run unified layout
positions = layout_engine._unified_force_directed_layout(egi, style, None)
area_bounds = layout_engine._calculate_bounding_boxes(egi, positions, style)

print("=== VERTEX POSITION ===")
for v_id, v_data in positions['vertices'].items():
    print(f"Vertex {v_id[:8]}: ({v_data['x']:.1f}, {v_data['y']:.1f})")
    print(f"  Assigned to area: {v_data['parent_area_id'][:8]}")

print("\n=== EDGE POSITIONS ===")
for e_id, e_data in positions['edge_labels'].items():
    rel_name = egi.rel.get(e_id, "?")
    print(f"Edge {e_id[:8]} '{rel_name}': ({e_data['x']:.1f}, {e_data['y']:.1f})")
    print(f"  Assigned to area: {e_data['parent_area_id'][:8]}")

print("\n=== AREA BOUNDS ===")
for area_id, bounds in sorted(area_bounds.items()):
    area_name = "SHEET" if area_id == egi.sheet else area_id[:8]
    print(f"{area_name}: x={bounds.x:.1f}, y={bounds.y:.1f}, w={bounds.width:.1f}, h={bounds.height:.1f}")

print("\n=== BOUNDARY ANALYSIS ===")
for v_id, v_data in positions['vertices'].items():
    area_id = v_data['parent_area_id']
    bounds = area_bounds.get(area_id)
    
    if area_id == egi.sheet:
        print(f"Vertex on SHEET - checking against all cut boundaries...")
        for cut_id, cut_bounds in area_bounds.items():
            if cut_id == egi.sheet:
                continue
            
            # Calculate distance to each edge of cut
            dist_left = abs(v_data['x'] - cut_bounds.x)
            dist_right = abs(v_data['x'] - (cut_bounds.x + cut_bounds.width))
            dist_top = abs(v_data['y'] - cut_bounds.y)
            dist_bottom = abs(v_data['y'] - (cut_bounds.y + cut_bounds.height))
            
            min_dist = min(dist_left, dist_right, dist_top, dist_bottom)
            
            if min_dist < 20:  # Within 20 pixels of boundary
                print(f"  ⚠️  NEAR boundary of cut {cut_id[:8]}: {min_dist:.1f} pixels")
                print(f"     Vertex: ({v_data['x']:.1f}, {v_data['y']:.1f})")
                print(f"     Cut: x={cut_bounds.x:.1f}, y={cut_bounds.y:.1f}, w={cut_bounds.width:.1f}, h={cut_bounds.height:.1f}")

print("\n=== EDGE CONNECTIONS ===")
print("Why is vertex positioned there? Check what it connects to:")
for e_id, vertex_seq in egi.nu.items():
    rel_name = egi.rel.get(e_id, "?")
    for v_id in vertex_seq:
        if v_id in positions['vertices']:
            e_pos = positions['edge_labels'].get(e_id)
            v_pos = positions['vertices'][v_id]
            if e_pos:
                distance = ((e_pos['x'] - v_pos['x'])**2 + (e_pos['y'] - v_pos['y'])**2)**0.5
                print(f"Vertex {v_id[:8]} -> Edge '{rel_name}': distance={distance:.1f}")
                print(f"  Vertex area: {v_pos['parent_area_id'][:8]}")
                print(f"  Edge area: {e_pos['parent_area_id'][:8]}")

print("\n=== ROOT CAUSE ===")
print("Graphviz's force-directed algorithm minimizes total edge length.")
print("If vertex connects to edges in different areas, it may position")
print("vertex as a compromise - potentially near area boundaries.")
print("\nSOLUTION: Add bias to keep vertices away from non-parent cut boundaries.")
