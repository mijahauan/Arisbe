#!/usr/bin/env python3
"""
Debug script to generate SVG output after each pass.
This helps identify where layout problems occur.
"""

import sys
sys.path.insert(0, 'src')

from egi_io import load_egi_json
from definitive_three_pass_engine import DefinitiveThreePassEngine
from style_loader import StyleLoader

# Load the problematic graph
graph_path = "corpus/graphs/peirce_complex_scope/peirce_complex_scope.egi.json"
print(f"Loading graph: {graph_path}")
print()

egi = load_egi_json(graph_path)

print(f"Graph loaded:")
print(f"  Vertices: {len(egi.V)}")
print(f"  Edges: {len(egi.E)}")
print(f"  Areas: {len(egi.area)}")
print()

# Generate layout with DEBUG output
style = StyleLoader().load_default_style()
engine = DefinitiveThreePassEngine()

print("Generating layout with debug SVG output...")
print()

dto = engine.generate_layout(egi, style, debug_prefix="debug/peirce_scope")

print()
print("=" * 70)
print("DEBUG SVG FILES GENERATED:")
print("=" * 70)
print("  1. debug/peirce_scope_pass1_containers.svg - After Pass 1 (containers)")
print("  2. debug/peirce_scope_pass2_content.svg    - After Pass 2 (content layout)")
print("  3. debug/peirce_scope_pass3_final.svg      - After Pass 3 (ligatures)")
print()
print("Open these files to see where the layout breaks down.")
print()
