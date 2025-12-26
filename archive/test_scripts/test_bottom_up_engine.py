#!/usr/bin/env python3
"""
Test the new bottom-up d3-only engine.

This engine:
- NO Graphviz Pass 1 (no size guessing)
- Pure bottom-up recursion with d3-force
- Content determines container size
"""

import sys
sys.path.insert(0, 'src')

from egi_io import load_egi_json
from bottom_up_d3_engine import BottomUpD3Engine
from style_loader import StyleLoader

# Test graphs
test_graphs = [
    "corpus/graphs/dau_2006_p112_ligature/dau_2006_p112_ligature.egi.json",
    "corpus/graphs/mixed_quantifier_complex/mixed_quantifier_complex.egi.json",
    "corpus/graphs/peirce_complex_scope/peirce_complex_scope.egi.json",
]

style = StyleLoader().load_default_style()
engine = BottomUpD3Engine()

for graph_path in test_graphs:
    print()
    print("=" * 80)
    print(f"Testing: {graph_path}")
    print("=" * 80)
    
    egi = load_egi_json(graph_path)
    print(f"Graph: {len(egi.V)}V, {len(egi.E)}E, {len([c for c in egi.area if c.startswith('c_')])} cuts")
    print()
    
    dto = engine.generate_layout(egi, style)
    
    print()
    print("Results:")
    print(f"  Vertices positioned: {len(dto.vertices)}")
    print(f"  Edge labels positioned: {len(dto.edge_labels)}")
    print(f"  Areas sized: {len(dto.areas)}")
    
    # Show area sizes
    print()
    print("  Area sizes (width x height):")
    for area in dto.areas:
        area_type = "Sheet" if area.is_sheet else "Cut"
        print(f"    {area.id}: {area.rect.width:.0f} x {area.rect.height:.0f} ({area_type})")
    
    print()
    print("✅ Layout generated successfully!")
    print()
