#!/usr/bin/env python3
"""Visualize ligature paths to see if they properly enter/exit cuts"""

import sys
sys.path.insert(0, 'src')

from pathlib import Path
from entity_storage import EntityStorageManager
from definitive_egi_layout_engine import DefinitiveEGILayoutEngine
from style_loader import StyleLoader

storage = EntityStorageManager(Path('corpus/graphs'))
layout_engine = DefinitiveEGILayoutEngine()
style_loader = StyleLoader()
style = style_loader.load_default_style()

entity = storage.load_entity('peirce_modus_ponens')
egi = entity.current_egi
dto = layout_engine.generate_layout(egi, style, None)

print("EGIF: *x (P x) ~[ (P x) ~[ (Q x) ] ]")
print("\nCut rectangles:")
for area in dto.areas:
    if not area.is_sheet:
        print(f"  {area.id[:8]}: ({area.rect.x:.1f}, {area.rect.y:.1f}) "
              f"{area.rect.width:.1f}x{area.rect.height:.1f}")

print("\nLigature paths:")
for lig in dto.ligatures:
    # Find endpoint info
    vertex = next((v for v in dto.vertices if v.id == lig.start_vertex_id), None)
    edge = next((e for e in dto.edge_labels if e.id == lig.end_edge_id), None)
    
    if vertex and edge:
        print(f"\n{vertex.id[:8]} (SHEET) → {edge.id[:8]} '{edge.label}' ({edge.parent_area_id[:8]})")
        print(f"  Path has {len(lig.path_points)} points:")
        for i, (x, y) in enumerate(lig.path_points):
            # Check which areas this point is in
            in_areas = []
            for area in dto.areas:
                if not area.is_sheet:
                    if (area.rect.x <= x <= area.rect.x + area.rect.width and
                        area.rect.y <= y <= area.rect.y + area.rect.height):
                        in_areas.append(area.id[:8])
            
            location = f"in cuts: {in_areas}" if in_areas else "in SHEET"
            print(f"    [{i}] ({x:.1f}, {y:.1f}) - {location}")
