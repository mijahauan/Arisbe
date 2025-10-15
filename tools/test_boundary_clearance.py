#!/usr/bin/env python3
"""Test boundary clearance enforcement"""

import sys
sys.path.insert(0, 'src')

from pathlib import Path
from entity_storage import EntityStorageManager
from diagram_controller import DiagramController
from graphviz_svg_renderer import GraphvizSVGRenderer

storage = EntityStorageManager(Path('tomos/graphs'))
controller = DiagramController()

# Test the problematic graph
entity_name = 'shared_constant_disjunction'
entity = storage.load_entity(entity_name)

print(f"Testing: {entity_name}")
print(f"EGIF: {entity.get_current_egif()}")

# Load and layout
controller.load_egi(entity.current_egi)
dto = controller.current_layout_dto

print(f"\n=== LAYOUT RESULTS ===")
print(f"Vertices: {len(dto.vertices)}")
print(f"Edges: {len(dto.edge_labels)}")
print(f"Areas: {len(dto.areas)}")

# Check vertex positions relative to cut boundaries
for vertex in dto.vertices:
    print(f"\nVertex {vertex.id[:8]}:")
    print(f"  Position: ({vertex.pos[0]:.1f}, {vertex.pos[1]:.1f})")
    print(f"  Area: {vertex.parent_area_id[:8]}")
    
    # Find nearest cut boundary
    min_dist = float('inf')
    nearest_cut = None
    
    for area in dto.areas:
        if area.is_sheet or area.id == vertex.parent_area_id:
            continue
        
        # Distance to each edge
        dist_left = abs(vertex.pos[0] - area.rect.x)
        dist_right = abs(vertex.pos[0] - (area.rect.x + area.rect.width))
        dist_top = abs(vertex.pos[1] - area.rect.y)
        dist_bottom = abs(vertex.pos[1] - (area.rect.y + area.rect.height))
        
        edge_dist = min(dist_left, dist_right, dist_top, dist_bottom)
        if edge_dist < min_dist:
            min_dist = edge_dist
            nearest_cut = area.id
    
    if min_dist < 25:
        print(f"  ⚠️  {min_dist:.1f} pixels from cut {nearest_cut[:8]} boundary")
    else:
        print(f"  ✅ {min_dist:.1f} pixels clearance from nearest cut")

# Generate SVG
output_dir = Path("test_outputs/boundary_clearance")
output_dir.mkdir(parents=True, exist_ok=True)

renderer = GraphvizSVGRenderer()
svg_path = renderer.save_svg(
    dto,
    f"{entity_name} (Boundary Clearance)",
    entity.get_current_egif(),
    f"{entity_name}_clearance",
    output_dir
)

print(f"\n📊 SVG saved: {svg_path}")
print("Check if vertex is now clearly away from cut boundaries!")
