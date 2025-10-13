#!/usr/bin/env python3
"""Test that bottom-up engine produces renderable SVG diagrams."""

import sys
sys.path.insert(0, 'src')

from egi_io import load_egi_json
from bottom_up_d3_engine import BottomUpD3Engine
from style_loader import StyleLoader
from graphviz_svg_renderer import GraphvizSVGRenderer

# Test graph
graph_path = "corpus/graphs/dau_2006_p112_ligature/dau_2006_p112_ligature.egi.json"

print(f"Testing: {graph_path}")
print()

# Load
egi = load_egi_json(graph_path)
print(f"Loaded: {len(egi.V)}V, {len(egi.E)}E")

# Layout
style = StyleLoader().load_default_style()
engine = BottomUpD3Engine()
dto = engine.generate_layout(egi, style)

print()
print(f"DTO generated:")
print(f"  Vertices: {len(dto.vertices)}")
print(f"  Edges: {len(dto.edge_labels)}")
print(f"  Ligatures: {len(dto.ligatures)}")
print(f"  Areas: {len(dto.areas)}")
print()

# Render
renderer = GraphvizSVGRenderer(style)
svg_content = renderer.render_to_svg(dto)

print(f"SVG generated: {len(svg_content)} bytes")
print()

# Save
output_path = "/tmp/test_bottom_up_render.svg"
with open(output_path, 'w') as f:
    f.write(svg_content)

print(f"✅ Saved to: {output_path}")
print(f"   Open with: open {output_path}")
