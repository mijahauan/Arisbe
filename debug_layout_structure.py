#!/usr/bin/env python3
"""
Debug Layout Structure

Investigate what the GraphvizLayoutEngine actually produces
to fix our canonical EGDF generator.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from canonical import get_canonical_pipeline
from graphviz_layout_engine_v2 import GraphvizLayoutEngine


def debug_layout_structure():
    """Debug what layout structure we actually get."""
    
    print("🔍 Debugging Layout Structure")
    print("=" * 40)
    
    pipeline = get_canonical_pipeline()
    layout_engine = GraphvizLayoutEngine()
    
    egif = "*x (Human x) ~[ (Mortal x) ]"
    
    try:
        # Parse EGIF → EGI
        egi = pipeline.parse_egif(egif)
        print(f"✓ EGI: {len(egi.V)} vertices, {len(egi.E)} edges, {len(egi.Cut)} cuts")
        
        # Generate layout
        layout_result = layout_engine.create_layout_from_graph(egi)
        print(f"✓ Layout type: {type(layout_result)}")
        print(f"✓ Layout attributes: {dir(layout_result)}")
        
        # Inspect primitives
        if hasattr(layout_result, 'primitives'):
            print(f"✓ Primitives count: {len(layout_result.primitives)}")
            
            for element_id, primitive in layout_result.primitives.items():
                print(f"  - {element_id}: {primitive.element_type}")
                print(f"    Position: {primitive.position}")
                print(f"    Bounds: {primitive.bounds}")
                if hasattr(primitive, 'z_index'):
                    print(f"    Z-index: {primitive.z_index}")
                print()
        
        # Check EGI elements for comparison
        print("EGI Elements:")
        print(f"  Vertices: {[v.id for v in egi.V]}")
        print(f"  Edges: {[e.id for e in egi.E]}")
        print(f"  Cuts: {list(egi.Cut)}")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    debug_layout_structure()
