#!/usr/bin/env python3
"""
EGDF Sanity Check Script

Test the canonical EGDF pipeline by rendering the same EGIF cases
that work perfectly in render_logical_baseline.py.

This will help isolate whether issues are in:
1. EGDF generation (canonical pipeline)
2. GUI rendering (Qt display pipeline)
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from canonical import get_canonical_pipeline
from renderer_minimal_dau import render_layout_to_svg

# Same test cases as render_logical_baseline.py
CASES = [
    ("unary", "(Man \"Socrates\")"),
    ("binary", "(Loves \"Socrates\" \"Plato\")"),
    ("negation", "~[(Mortal \"Socrates\")]"),
    ("double_cut", "~[ ~[(Mortal \"Socrates\")] ]"),
    ("across_cut", "(Human *x) ~[(Immortal x)]"),
    ("disj", "~[ ~[(Rained)] ~[(Snowed)] ]"),
    ("implic", "~[(Human *x) ~[(Mortal x)] ]"),
]

def test_egdf_pipeline():
    """Test EGDF pipeline with known working cases."""
    print("🔍 Testing EGDF Pipeline Sanity Check")
    print("=" * 50)
    
    # Create output directory
    output_dir = Path("test_egdf_output")
    output_dir.mkdir(exist_ok=True)
    
    pipeline = get_canonical_pipeline()
    
    for name, egif in CASES:
        print(f"\n📝 Testing {name}: {egif}")
        
        try:
            # Step 1: Parse EGIF
            print("  Step 1: Parsing EGIF...")
            egi = pipeline.parse_egif(egif)
            print(f"  ✓ EGI: {len(egi.V)} vertices, {len(egi.E)} edges, {len(egi.Cut)} cuts")
            
            # Step 2: Generate EGDF
            print("  Step 2: Converting to EGDF...")
            egdf = pipeline.egi_to_egdf(egi)
            print(f"  ✓ EGDF: {type(egdf).__name__}")
            
            # Step 3: Check EGDF content
            if hasattr(egdf, 'visual_layout') and egdf.visual_layout:
                spatial_prims = egdf.visual_layout.get('spatial_primitives', [])
                print(f"  ✓ Spatial primitives: {len(spatial_prims)}")
                
                # Show what primitives were created
                for prim in spatial_prims:
                    if isinstance(prim, dict):
                        elem_id = prim.get('element_id', 'unknown')
                        elem_type = prim.get('element_type', 'unknown')
                        pos = prim.get('position', (0, 0))
                        print(f"    - {elem_id}: {elem_type} at {pos}")
                    else:
                        print(f"    - {prim}")
            else:
                print("  ⚠ No visual_layout in EGDF")
            
            # Step 4: Render to SVG (same approach as render_logical_baseline.py)
            print("  Step 3: Rendering to SVG...")
            svg_path = output_dir / f"{name}_egdf.svg"
            try:
                # Extract layout from EGDF spatial primitives
                # We need to convert EGDF back to the layout format that render_layout_to_svg expects
                # For now, let's use the original EGI + GraphvizLayoutEngine approach
                from graphviz_layout_engine_v2 import GraphvizLayoutEngine
                layout_engine = GraphvizLayoutEngine()
                layout = layout_engine.create_layout_from_graph(egi)
                
                # Use same rendering approach as render_logical_baseline.py
                render_layout_to_svg(
                    layout,
                    str(svg_path),
                    canvas_px=(800, 600),
                    graph=egi,
                    background_color="white",
                    cut_corner_radius=12.0,
                    pred_font_size=14,
                    pred_char_width=8,
                    pred_pad_x=6,
                    pred_pad_y=4,
                )
                print(f"  ✓ SVG saved: {svg_path}")
            except Exception as render_error:
                print(f"  ⚠ SVG rendering failed: {render_error}")
            
            # Step 5: Test round-trip
            print("  Step 4: Testing round-trip...")
            round_trip_egif = pipeline.egdf_to_egif(egdf)
            print(f"  ✓ Round-trip EGIF: {round_trip_egif}")
            
            print(f"  🎉 {name}: COMPLETE SUCCESS")
            
        except Exception as e:
            print(f"  ❌ {name}: FAILED - {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🏁 EGDF Pipeline Sanity Check Complete")

if __name__ == "__main__":
    test_egdf_pipeline()
