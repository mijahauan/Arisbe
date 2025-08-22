#!/usr/bin/env python3
"""
Render a set of EGIF examples using the logical-baseline mode:
- Preserves Graphviz cluster (_bb) for cuts exactly
- Deterministically places predicates/vertices using Graphviz node positions
- Draws heavy identity lines from vertex centers to predicate periphery
Outputs SVGs to out_logical_baseline/.
"""
from pathlib import Path
from typing import List, Tuple
import argparse

from egif_parser_dau import EGIFParser
from layout_phase_implementations import NinePhaseLayoutPipeline
from renderer_minimal_dau import render_layout_to_svg

CASES: List[Tuple[str, str]] = [
    ("unary", '(Man "Socrates")'),
    ("binary", '(Loves "Socrates" "Plato")'),
    ("negation", '~[(Mortal "Socrates")]'),
    ("double_cut", '~[ ~[(Mortal "Socrates")] ]'),
    ("across_cut", '(Human *x) ~[(Immortal x)]'),
    ("disj", '~[ ~[(Rained)] ~[(Snowed)] ]'),
    ("implic", '~[(Human *x) ~[(Mortal x)] ]')
]


def main() -> None:
    ap = argparse.ArgumentParser(description="Render EGIF examples with logical-baseline layout to SVG")
    ap.add_argument("--outdir", default="out_logical_baseline", help="Output directory for SVGs")
    ap.add_argument("--width", type=int, default=800, help="Canvas width in px")
    ap.add_argument("--height", type=int, default=600, help="Canvas height in px")
    ap.add_argument("--bg", default="#fafafa", help="Background color (CSS color)")
    ap.add_argument("--cut-radius", type=float, default=14.0, help="Rounded corner radius for cuts")
    ap.add_argument("--pred-font", type=float, default=12.0, help="Predicate label font size")
    ap.add_argument("--pred-char", type=float, default=7.0, help="Approx px per character for tight box")
    ap.add_argument("--pred-pad-x", type=float, default=6.0, help="Horizontal padding around predicate text")
    ap.add_argument("--pred-pad-y", type=float, default=4.0, help="Vertical padding around predicate text")
    args = ap.parse_args()

    outdir = args.outdir
    Path(outdir).mkdir(parents=True, exist_ok=True)
    pipeline = NinePhaseLayoutPipeline()
    for name, egif in CASES:
        print(f"- {name}: {egif}")
        g = EGIFParser(egif).parse()
        layout = pipeline.execute_pipeline(g)
        svg_path = str(Path(outdir) / f"{name}.svg")
        # Pass graph and CLI tunables to draw predicates/vertices/ligatures
        render_layout_to_svg(
            layout,
            svg_path,
            canvas_px=(args.width, args.height),
            graph=g,
            background_color=args.bg,
            cut_corner_radius=args.cut_radius,
            pred_font_size=args.pred_font,
            pred_char_width=args.pred_char,
            pred_pad_x=args.pred_pad_x,
            pred_pad_y=args.pred_pad_y,
        )
        print(f"  saved -> {svg_path}")
    print("Done.")


if __name__ == "__main__":
    main()
