#!/usr/bin/env python3
"""
Test UnifiedD3Engine with complex EGI containing cuts.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from unified_d3_engine import UnifiedD3Engine
from egif_parser_dau import parse_egif
from style_loader import StyleLoader

print("Testing UnifiedD3Engine with Cuts")
print("=" * 70)

# Test case: Graph with nested cut
test_egif = "[*x] (Human x) ~[ (Mortal x) ]"
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
    
    # Show actual positions
    print(f"\n4. Layout details:")
    for vid, pos in dto.vertex_positions.items():
        depth = dto.containment_depth.get(vid, 0)
        print(f"   - Vertex {vid}: ({pos.x:.1f}, {pos.y:.1f}) [depth={depth}]")
    for pid, pos in dto.predicate_positions.items():
        depth = dto.containment_depth.get(pid, 0)
        print(f"   - Predicate {pid}: ({pos.x:.1f}, {pos.y:.1f}) [depth={depth}]")
    for cid, bounds in dto.cut_bounds.items():
        depth = dto.containment_depth.get(cid, 0)
        width = bounds.max_x - bounds.min_x
        height = bounds.max_y - bounds.min_y
        print(f"   - Cut {cid}: ({bounds.min_x:.1f}, {bounds.min_y:.1f}) -> ({bounds.max_x:.1f}, {bounds.max_y:.1f}) [{width:.1f}x{height:.1f}, depth={depth}]")
        
except Exception as e:
    import traceback
    print(f"   ❌ Layout generation failed: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("✅ Complex EGI test PASSED!")
