#!/usr/bin/env python3
"""Debug why A* pathfinding is producing straight lines"""

import sys
sys.path.insert(0, 'src')

from pathlib import Path
from entity_storage import EntityStorageManager
from definitive_egi_layout_engine import DefinitiveEGILayoutEngine
from style_loader import StyleLoader

# Patch the pathfinding method to add debug output
original_calc_path = DefinitiveEGILayoutEngine._calculate_area_aware_path_to_port

def debug_calc_path(self, vertex, edge_label, target_port, area_grid, grid_bounds, hierarchy):
    print(f"\n=== Pathfinding Debug ===")
    print(f"From: vertex {vertex.id[:8]} in {vertex.parent_area_id[:8]}")
    print(f"To: edge {edge_label.id[:8]} '{edge_label.label}' in {edge_label.parent_area_id[:8]}")
    
    # Calculate legal corridor
    legal_areas = self._calculate_legal_corridor(
        vertex.parent_area_id, edge_label.parent_area_id, hierarchy
    )
    print(f"Legal corridor: {[a[:8] for a in legal_areas]}")
    
    # Check if start/end are walkable
    start_x = int((vertex.pos[0] - grid_bounds.x) * self.grid_resolution)
    start_y = int((vertex.pos[1] - grid_bounds.y) * self.grid_resolution)
    
    if target_port:
        target_x = int((target_port.position[0] - grid_bounds.x) * self.grid_resolution)
        target_y = int((target_port.position[1] - grid_bounds.y) * self.grid_resolution)
    else:
        target_x = int((edge_label.rect.x + edge_label.rect.width/2 - grid_bounds.x) * self.grid_resolution)
        target_y = int((edge_label.rect.y + edge_label.rect.height/2 - grid_bounds.y) * self.grid_resolution)
    
    # Clamp
    start_x = max(0, min(start_x, area_grid.width - 1))
    start_y = max(0, min(start_y, area_grid.height - 1))
    target_x = max(0, min(target_x, area_grid.width - 1))
    target_y = max(0, min(target_y, area_grid.height - 1))
    
    print(f"Grid coords: start=({start_x}, {start_y}), target=({target_x}, {target_y})")
    print(f"Grid size: {area_grid.width}x{area_grid.height}")
    
    try:
        start_node = area_grid.node(start_x, start_y)
        end_node = area_grid.node(target_x, target_y)
        print(f"Start walkable: {start_node.walkable}, area: {area_grid.area_map[start_y][start_x]}")
        print(f"End walkable: {end_node.walkable}, area: {area_grid.area_map[target_y][target_x]}")
    except Exception as e:
        print(f"Error accessing nodes: {e}")
    
    # Call original
    result = original_calc_path(self, vertex, edge_label, target_port, area_grid, grid_bounds, hierarchy)
    print(f"Path result: {len(result) if result else 0} points")
    if result and len(result) == 2:
        print(f"⚠️  Fallback to straight line!")
    
    return result

DefinitiveEGILayoutEngine._calculate_area_aware_path_to_port = debug_calc_path

# Test
storage = EntityStorageManager(Path('tomos/graphs'))
layout_engine = DefinitiveEGILayoutEngine()
style_loader = StyleLoader()
style = style_loader.load_default_style()

entity = storage.load_entity('peirce_modus_ponens')
egi = entity.current_egi

print("Testing: peirce_modus_ponens")
print(f"EGIF: {entity.get_current_egif()}\n")

dto = layout_engine.generate_layout(egi, style, None)

print(f"\n{'='*60}")
print(f"Summary: Generated {len(dto.ligatures)} ligatures")
