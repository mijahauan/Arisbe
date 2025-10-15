#!/usr/bin/env python3
"""
Test the three-pass layout engine on a simple graph.
"""

import sys
sys.path.insert(0, 'src')

from pathlib import Path
from entity_storage import EntityStorageManager
from three_pass_layout_engine import ThreePassLayoutEngine

def test_simple_graph():
    """Test on peirce_cp_4_394_man_mortal (simple case)."""
    storage = EntityStorageManager(Path('tomos/graphs'))
    engine = ThreePassLayoutEngine()
    
    print("Loading peirce_cp_4_394_man_mortal...")
    entity = storage.load_entity('peirce_cp_4_394_man_mortal')
    egi = entity.current_egi
    
    print(f"  Vertices: {len(egi.V)}")
    print(f"  Edges: {len(egi.rel)}")
    print(f"  Areas: {len(egi.area)}")
    print()
    
    print("Executing 3-pass layout...")
    try:
        dto = engine.generate_layout(egi, None, None)
        
        print(f"✅ Layout complete!")
        print(f"   Areas: {len(dto.areas)}")
        print(f"   Vertices: {len(dto.vertices)}")
        print(f"   Edge labels: {len(dto.edge_labels)}")
        print(f"   Ligatures: {len(dto.ligatures)}")
        print()
        
        # Check containment
        violations = 0
        for v in dto.vertices:
            parent = next(a for a in dto.areas if a.id == v.parent_area_id)
            if not (parent.rect.x <= v.pos[0] <= parent.rect.x + parent.rect.width and
                    parent.rect.y <= v.pos[1] <= parent.rect.y + parent.rect.height):
                violations += 1
                print(f"❌ Vertex {v.id[:8]} at ({v.pos[0]:.1f},{v.pos[1]:.1f}) outside parent {v.parent_area_id[:8]}")
                print(f"   Parent rect: x={parent.rect.x:.1f}, y={parent.rect.y:.1f}, w={parent.rect.width:.1f}, h={parent.rect.height:.1f}")
        
        if violations == 0:
            print("✅ All elements within bounds")
        
        # Check ligature lengths
        min_len = float('inf')
        for lig in dto.ligatures:
            if len(lig.path_points) >= 2:
                start = lig.path_points[0]
                end = lig.path_points[-1]
                length = ((end[0]-start[0])**2 + (end[1]-start[1])**2)**0.5
                min_len = min(min_len, length)
        
        print(f"Minimum ligature length: {min_len:.1f}px")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_simple_graph()
