#!/usr/bin/env python3
"""
Debug script to diagnose hover issues in the GUI.
Prints spatial primitive structure and hit-testing details.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.egif_parser_dau import EGIFParser
from src.graphviz_layout_engine_v2 import create_canonical_layout

def debug_spatial_primitives():
    """Debug the spatial primitives for the hover test case."""
    egif = '~[ (Human "Socrates") ~[ (Mortal "Socrates") ] ]'
    print(f"Debugging EGIF: {egif}")
    print("=" * 50)
    
    # Parse to EGI
    parser = EGIFParser(egif)
    egi = parser.parse()
    
    print(f"EGI Structure:")
    print(f"  Vertices: {len(egi.V)} - {list(egi.V)}")
    print(f"  Edges: {len(egi.E)} - {list(egi.E)}")
    print(f"  Relations (κ): {dict(egi.rel)}")
    print(f"  Nu mapping (ν): {dict(egi.nu)}")
    print()
    
    # Generate layout
    layout_result = create_canonical_layout(egi)
    
    if hasattr(layout_result, 'primitives'):
        primitives = list(layout_result.primitives.values())
        print(f"Spatial Primitives: {len(primitives)}")
        print("-" * 30)
        
        for i, prim in enumerate(primitives):
            print(f"Primitive {i}:")
            print(f"  ID: {prim.element_id}")
            print(f"  Type: {prim.element_type}")
            print(f"  Position: {prim.position}")
            print(f"  Bounds: {prim.bounds}")
            print(f"  Z-index: {getattr(prim, 'z_index', 'N/A')}")
            print(f"  Curve points: {getattr(prim, 'curve_points', 'N/A')}")
            
            # Check relation type for edges
            if prim.element_type == 'edge':
                relation = egi.rel.get(prim.element_id, 'UNKNOWN')
                print(f"  Relation (κ): {relation}")
                if relation == '=':
                    print(f"    → Identity ligature")
                else:
                    print(f"    → Predicate: {relation}")
            print()
    else:
        print("ERROR: No primitives found in layout result")
        print(f"Layout result type: {type(layout_result)}")
        print(f"Layout result attributes: {dir(layout_result)}")

if __name__ == "__main__":
    debug_spatial_primitives()
