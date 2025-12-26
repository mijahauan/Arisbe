#!/usr/bin/env python3
"""
Test complete pipeline: EGI -> Layout -> SVG rendering
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from unified_d3_engine import UnifiedD3Engine
from egif_parser_dau import parse_egif
from style_loader import StyleLoader
from simple_svg_renderer import SimpleSVGRenderer

print("Testing Complete SVG Rendering Pipeline")
print("=" * 70)

# Parse EGI
test_egif = "[*s] (Human s) ~[ (Mortal s) ]"
print(f"\n1. Parsing EGIF: {test_egif}")
egi = parse_egif(test_egif)
print(f"   ✅ Parsed: {len(egi.V)}V, {len(egi.E)}E, {len(egi.Cut)}C")

# Load style
print("\n2. Loading style...")
style_loader = StyleLoader()
style = style_loader.load_default_style()
print(f"   ✅ Style loaded")

# Generate layout
print("\n3. Generating layout with UnifiedD3Engine...")
engine = UnifiedD3Engine(timeout_seconds=10)
dto = engine.generate_layout(egi, style, layout_deltas=None)
print(f"   ✅ Layout generated")
print(f"   - Vertices: {len(dto.vertex_positions)}")
print(f"   - Predicates: {len(dto.predicate_positions)}")
print(f"   - Cuts: {len(dto.cut_bounds)}")

# Render to SVG
print("\n4. Rendering to SVG...")
renderer = SimpleSVGRenderer()
svg_content = renderer.render_to_svg(
    dto,
    title="Test Graph",
    egif=test_egif,
    egi=egi
)
print(f"   ✅ SVG generated ({len(svg_content)} chars)")

# Save SVG for inspection
output_path = Path(__file__).parent / "test_output.svg"
output_path.write_text(svg_content)
print(f"   ✅ Saved to: {output_path}")

print("\n" + "=" * 70)
print("✅ Complete pipeline test PASSED!")
print(f"\nOpen {output_path} in a browser to view the rendered graph.")
