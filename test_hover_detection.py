#!/usr/bin/env python3
"""
Test hover detection by simulating mouse positions over known elements.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.egif_parser_dau import EGIFParser
from src.graphviz_layout_engine_v2 import create_canonical_layout

def test_hover_positions():
    """Test hover detection at specific positions."""
    egif = '~[ (Human "Socrates") ~[ (Mortal "Socrates") ] ]'
    print(f"Testing hover for: {egif}")
    print("=" * 50)
    
    # Parse and layout
    parser = EGIFParser(egif)
    egi = parser.parse()
    layout_result = create_canonical_layout(egi)
    
    if not hasattr(layout_result, 'primitives'):
        print("ERROR: No primitives in layout")
        return
    
    primitives = list(layout_result.primitives.values())
    print(f"Found {len(primitives)} spatial primitives:")
    
    # Print all elements with their positions and types
    for i, prim in enumerate(primitives):
        print(f"\n{i+1}. {prim.element_id} ({prim.element_type})")
        print(f"   Position: {prim.position}")
        print(f"   Bounds: {prim.bounds}")
        
        if prim.element_type == 'edge':
            # Check if it's a ligature or predicate
            relation = egi.rel.get(prim.element_id, 'UNKNOWN')
            is_synthetic = prim.element_id.startswith('edge_') and relation == 'UNKNOWN'
            print(f"   Relation: {relation}")
            print(f"   Is synthetic ligature: {is_synthetic}")
            
            if is_synthetic:
                # Test ligature path reconstruction
                parts = prim.element_id.split('_')
                if len(parts) >= 4:
                    vertex_id = f"{parts[1]}_{parts[2]}"
                    predicate_id = f"{parts[3]}_{parts[4]}"
                    print(f"   Connects: {vertex_id} -> {predicate_id}")
                    
                    # Find vertex and predicate positions
                    vertex_pos = None
                    predicate_pos = None
                    for p in primitives:
                        if p.element_id == vertex_id:
                            vertex_pos = p.position
                        elif p.element_id == predicate_id:
                            predicate_pos = p.position
                    
                    if vertex_pos and predicate_pos:
                        print(f"   Vertex at: {vertex_pos}")
                        print(f"   Predicate at: {predicate_pos}")
                        
                        # Test positions along the line
                        vx, vy = vertex_pos
                        px, py = predicate_pos
                        mid_x = (vx + px) / 2
                        mid_y = (vy + py) / 2
                        print(f"   Midpoint: ({mid_x}, {mid_y}) <- TEST THIS POSITION")

if __name__ == "__main__":
    test_hover_positions()
