#!/usr/bin/env python3
"""
Full integration test for UnifiedD3Engine with real EGI.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from unified_d3_engine import UnifiedD3Engine
from egif_parser_dau import parse_egif
from style_loader import StyleLoader

print("Testing UnifiedD3Engine with Real EGI")
print("=" * 70)

# Test case: Simple graph with vertex and predicate
test_egif = "[*x] (Human x)"
print(f"\nTest EGIF: {test_egif}")

# Parse EGI
print("\n1. Parsing EGIF...")
try:
    egi = parse_egif(test_egif)
    print(f"   ✅ Parsed successfully")
    print(f"   - Vertices: {len(egi.V)}")
    print(f"   - Edges: {len(egi.E)}")
    print(f"   - Cuts: {len(egi.Cut)}")
except Exception as e:
    print(f"   ❌ Parsing failed: {e}")
    sys.exit(1)

# Load style
print("\n2. Loading style...")
try:
    style_loader = StyleLoader()
    style = style_loader.load_default_style()
    print(f"   ✅ Style loaded")
    print(f"   - Vertex radius: {style.vertex_radius}")
    print(f"   - Cut padding: {style.cut_padding}")
except Exception as e:
    print(f"   ❌ Style loading failed: {e}")
    sys.exit(1)

# Create engine and generate layout
print("\n3. Generating layout...")
try:
    engine = UnifiedD3Engine(timeout_seconds=10)
    dto = engine.generate_layout(egi, style, layout_deltas=None)
    print(f"   ✅ Layout generated successfully!")
    print(f"   - Vertex positions: {len(dto.vertex_positions)}")
    print(f"   - Predicate positions: {len(dto.predicate_positions)}")
    print(f"   - Cut bounds: {len(dto.cut_bounds)}")
    print(f"   - Viewport: {dto.viewport_bounds}")
    
    # Show actual positions
    print(f"\n4. Layout details:")
    for vid, pos in dto.vertex_positions.items():
        print(f"   - Vertex {vid}: ({pos.x:.1f}, {pos.y:.1f})")
    for pid, pos in dto.predicate_positions.items():
        print(f"   - Predicate {pid}: ({pos.x:.1f}, {pos.y:.1f})")
        
except Exception as e:
    import traceback
    print(f"   ❌ Layout generation failed: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("✅ Full integration test PASSED!")
