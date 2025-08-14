#!/usr/bin/env python3
"""
Debug Zero-Vertex Case

Debug the specific case "(P) ~[(Q)]" that has 0 vertices but 2 predicates.
This should help us understand why the layout engine fails for this case.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from canonical import get_canonical_pipeline
from graphviz_layout_engine_v2 import GraphvizLayoutEngine


def debug_zero_vertex_case():
    """Debug the zero-vertex case that's failing."""
    
    print("🔍 Debugging Zero-Vertex Case: (P) ~[(Q)]")
    print("=" * 50)
    
    pipeline = get_canonical_pipeline()
    layout_engine = GraphvizLayoutEngine()
    
    egif = "(P) ~[(Q)]"
    
    try:
        # Step 1: Parse EGIF → EGI
        print("📝 Step 1: Parsing EGIF...")
        egi = pipeline.parse_egif(egif)
        print(f"✓ EGI: {len(egi.V)} vertices, {len(egi.E)} edges, {len(egi.Cut)} cuts")
        
        # Inspect EGI structure
        print("\n🔍 EGI Structure:")
        print(f"  Vertices: {[v.id for v in egi.V]}")
        print(f"  Edges: {[e.id for e in egi.E]}")
        print(f"  Cuts: {list(egi.Cut)}")
        print(f"  Nu mapping: {dict(egi.nu)}")
        print(f"  Rel mapping: {dict(egi.rel)}")
        
        # Step 2: Try layout generation with detailed debugging
        print("\n📝 Step 2: Generating layout...")
        
        # Enable debug mode in layout engine if possible
        if hasattr(layout_engine, 'debug_mode'):
            layout_engine.debug_mode = True
        
        try:
            layout_result = layout_engine.create_layout_from_graph(egi)
            print(f"✓ Layout successful: {len(layout_result.primitives)} primitives")
            
            # Inspect layout primitives
            print("\n🔍 Layout Primitives:")
            for element_id, primitive in layout_result.primitives.items():
                print(f"  - {element_id}: {primitive.element_type}")
                print(f"    Position: {primitive.position}")
                print(f"    Bounds: {primitive.bounds}")
                
        except Exception as layout_error:
            print(f"❌ Layout failed: {layout_error}")
            
            # Try to inspect what the layout engine actually generated
            print("\n🔍 Attempting to inspect layout engine state...")
            
            # Check if we can access internal state
            if hasattr(layout_engine, '_last_dot_content'):
                print("DOT content:")
                print(layout_engine._last_dot_content)
            
            if hasattr(layout_engine, '_last_xdot_content'):
                print("xdot content:")
                print(layout_engine._last_xdot_content[:500] + "..." if len(layout_engine._last_xdot_content) > 500 else layout_engine._last_xdot_content)
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()


def compare_working_case():
    """Compare with a working case that has vertices."""
    
    print("\n🔄 Comparing with Working Case")
    print("=" * 40)
    
    pipeline = get_canonical_pipeline()
    layout_engine = GraphvizLayoutEngine()
    
    # Working case with vertices
    working_egif = '*x (Human x) ~[ (Mortal x) ]'
    
    try:
        print(f"📝 Working case: {working_egif}")
        egi = pipeline.parse_egif(working_egif)
        print(f"✓ EGI: {len(egi.V)} vertices, {len(egi.E)} edges, {len(egi.Cut)} cuts")
        
        layout_result = layout_engine.create_layout_from_graph(egi)
        print(f"✓ Layout: {len(layout_result.primitives)} primitives")
        
        # Show what primitives are generated
        primitive_types = {}
        for element_id, primitive in layout_result.primitives.items():
            ptype = primitive.element_type
            primitive_types[ptype] = primitive_types.get(ptype, 0) + 1
        
        print(f"  Primitive types: {primitive_types}")
        
    except Exception as e:
        print(f"❌ Working case failed: {e}")


if __name__ == "__main__":
    debug_zero_vertex_case()
    compare_working_case()
