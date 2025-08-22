#!/usr/bin/env python3
"""
Render the five reference cut-only cases to SVG using the minimal deterministic renderer.
"""
import os
from typing import List, Tuple

from egif_parser_dau import EGIFParser
from layout_phase_implementations import NinePhaseLayoutPipeline
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
    pipeline = NinePhaseLayoutPipeline()
    for name, egif in CASES:
        print(f"- {name}: {egif}")
        g = EGIFParser(egif).parse()
        layout = pipeline.execute_pipeline(g)
        svg_path = os.path.join(outdir, f"{name}.svg")
        render_layout_to_svg(layout, svg_path)
        print(f"  saved -> {svg_path}")
    print("Done.")

if __name__ == "__main__":
    main()
