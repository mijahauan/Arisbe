#!/usr/bin/env python3
"""
Test the Graphviz three-pass layout engine on the entire corpus.
"""

import sys
sys.path.insert(0, 'src')

from pathlib import Path
from entity_storage import EntityStorageManager
from graphviz_three_pass_engine import GraphvizThreePassEngine

def test_corpus():
    """Test on entire corpus."""
    storage = EntityStorageManager(Path('corpus/graphs'))
    engine = GraphvizThreePassEngine()
    
    corpus_dir = Path('corpus/graphs')
    
    print("=" * 70)
    print("GRAPHVIZ THREE-PASS LAYOUT ENGINE - CORPUS TEST")
    print("=" * 70)
    print()
    
    success_count = 0
    fail_count = 0
    containment_violations = 0
    
    for graph_dir in sorted(corpus_dir.iterdir()):
        if not graph_dir.is_dir():
            continue
        
        egi_files = list(graph_dir.glob('*.egi.json'))
        if not egi_files:
            continue
        
        name = graph_dir.name
        
        try:
            entity = storage.load_entity(name)
            egi = entity.current_egi
            
            # Generate layout (suppress internal output)
            import io
            import contextlib
            
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                dto = engine.generate_layout(egi, None, None)
            
            # Check containment
            violations = 0
            for v in dto.vertices:
                parent = next((a for a in dto.areas if a.id == v.parent_area_id), None)
                if parent and not (parent.rect.x <= v.pos[0] <= parent.rect.x + parent.rect.width and
                                  parent.rect.y <= v.pos[1] <= parent.rect.y + parent.rect.height):
                    violations += 1
            
            for e in dto.edge_labels:
                parent = next((a for a in dto.areas if a.id == e.parent_area_id), None)
                cx = e.rect.x + e.rect.width/2
                cy = e.rect.y + e.rect.height/2
                if parent and not (parent.rect.x <= cx <= parent.rect.x + parent.rect.width and
                                  parent.rect.y <= cy <= parent.rect.y + parent.rect.height):
                    violations += 1
            
            # Check ligature visibility
            min_len = float('inf')
            for lig in dto.ligatures:
                if len(lig.path_points) >= 2:
                    start = lig.path_points[0]
                    end = lig.path_points[-1]
                    length = ((end[0]-start[0])**2 + (end[1]-start[1])**2)**0.5
                    min_len = min(min_len, length)
            
            status = "✅" if violations == 0 else "⚠️"
            min_len_str = f"{min_len:.1f}px" if min_len != float('inf') else "N/A"
            print(f"{status} {name:35s} V:{len(dto.vertices)} E:{len(dto.edge_labels)} A:{len(dto.areas)-1} L:{len(dto.ligatures)} min:{min_len_str}")
            
            if violations > 0:
                print(f"   ⚠️  {violations} containment violations")
                containment_violations += violations
            
            success_count += 1
            
        except Exception as e:
            print(f"❌ {name:35s} FAILED: {str(e)[:50]}")
            fail_count += 1
    
    print()
    print("=" * 70)
    print(f"Results: {success_count} success, {fail_count} failed")
    print(f"Total containment violations: {containment_violations}")
    print("=" * 70)

if __name__ == '__main__':
    test_corpus()
