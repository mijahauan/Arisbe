#!/usr/bin/env python3
"""Test bottom-up layout with cuts as positioned rectangles"""

import sys
sys.path.insert(0, 'src')

from pathlib import Path
from entity_storage import EntityStorageManager
from definitive_egi_layout_engine import DefinitiveEGILayoutEngine
from graphviz_svg_renderer import GraphvizSVGRenderer
from style_loader import StyleLoader

# Test on the problematic graph
storage = EntityStorageManager(Path('tomos/graphs'))
layout_engine = DefinitiveEGILayoutEngine()
style_loader = StyleLoader()
style = style_loader.load_default_style()

test_graphs = [
    'shared_constant_disjunction',  # Socrates example
    'peirce_modus_ponens',          # Modus ponens
    'roberts_domain_modeling',      # More complex
]

output_dir = Path("test_outputs/bottom_up_cuts")
output_dir.mkdir(parents=True, exist_ok=True)

for entity_name in test_graphs:
    print(f"\n{'='*60}")
    print(f"Testing: {entity_name}")
    print(f"{'='*60}")
    
    entity = storage.load_entity(entity_name)
    egi = entity.current_egi
    
    print(f"EGIF: {entity.get_current_egif()}")
    print(f"Graph: {len(egi.V)} vertices, {len(egi.E)} edges, {len(egi.Cut)} cuts")
    
    try:
        # Generate layout with new approach
        dto = layout_engine.generate_layout(egi, style, None)
        
        print(f"\n✅ Layout generated successfully")
        print(f"   Vertices: {len(dto.vertices)}")
        print(f"   Edges: {len(dto.edge_labels)}")
        print(f"   Areas: {len(dto.areas)}")
        
        # Check for boundary clarity
        print(f"\n=== Boundary Check ===")
        for vertex in dto.vertices:
            min_dist = float('inf')
            nearest_cut = None
            
            for area in dto.areas:
                if area.is_sheet or area.id == vertex.parent_area_id:
                    continue
                
                # Distance to cut boundaries
                dx = min(abs(vertex.pos[0] - area.rect.x),
                        abs(vertex.pos[0] - (area.rect.x + area.rect.width)))
                dy = min(abs(vertex.pos[1] - area.rect.y),
                        abs(vertex.pos[1] - (area.rect.y + area.rect.height)))
                dist = min(dx, dy)
                
                if dist < min_dist:
                    min_dist = dist
                    nearest_cut = area.id
            
            if min_dist < 25:
                print(f"⚠️  Vertex {vertex.id[:8]}: {min_dist:.1f}px from cut {nearest_cut[:8]}")
            else:
                print(f"✅ Vertex {vertex.id[:8]}: {min_dist:.1f}px clearance")
        
        # Generate SVG
        renderer = GraphvizSVGRenderer()
        svg_path = renderer.save_svg(
            dto,
            f"{entity_name} (Bottom-Up with Cut Rectangles)",
            entity.get_current_egif(),
            f"{entity_name}_bottom_up",
            output_dir
        )
        
        print(f"\n📊 SVG saved: {svg_path}")
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()

print(f"\n{'='*60}")
print(f"All SVGs saved to: {output_dir}")
print(f"Check if vertices are clearly separated from cut boundaries!")
