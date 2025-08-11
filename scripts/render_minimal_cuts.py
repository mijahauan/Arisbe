#!/usr/bin/env python3
"""
Render the five reference cut-only cases to SVG using the minimal deterministic renderer.
"""
import os
from typing import List, Tuple

from egif_parser_dau import parse_egif
from graphviz_layout_engine_v2 import GraphvizLayoutEngine
from renderer_minimal_dau import render_layout_to_svg

CASES: List[Tuple[str, str]] = [
    ("case1_single_cut", "~[]"),
    ("case2_sibling_cuts", "~[] ~[]"),
    ("case3_nested_double", "~[~[]]"),
    ("case4_nested_siblings", "~[~[] ~[]]"),
    ("case5_mixed_nesting", "~[ ~[] ~[ ~[] ~[] ] ]"),
]

def main(outdir: str = "out_minimal") -> None:
    os.makedirs(outdir, exist_ok=True)
    engine = GraphvizLayoutEngine(mode="default-nopp")
    for name, egif in CASES:
        print(f"- {name}: {egif}")
        g = parse_egif(egif)
        layout = engine.create_layout_from_graph(g)
        svg_path = os.path.join(outdir, f"{name}.svg")
        render_layout_to_svg(layout, svg_path)
        print(f"  saved -> {svg_path}")
    print("Done.")

if __name__ == "__main__":
    main()
