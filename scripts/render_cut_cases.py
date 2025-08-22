#!/usr/bin/env python3
"""
Render five cut-only EGIF cases using the Dau renderer and Graphviz-based layout.
Outputs PNG files to the specified directory (default: ./src).
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import List, Tuple

# Ensure local src/ is importable regardless of where the script is run from
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SRC_DIR = os.path.join(REPO_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# Correct imports
from egif_parser_dau import EGIFParser
from layout_phase_implementations import NinePhaseLayoutPipeline
from pyside6_canvas import PySide6Canvas
from diagram_renderer_dau import DiagramRendererDau


CASES: List[Tuple[str, str]] = [
    ("case1_single_cut", "~[]"),
    ("case2_sibling_cuts", "~[] ~[]"),
    ("case3_nested_double", "~[~[]]"),
    ("case4_nested_siblings", "~[~[] ~[]]"),
    ("case5_mixed_nesting", "~[ ~[] ~[ ~[] ~[] ] ]"),
]


def _cut_nesting_levels(layout) -> List[Tuple[str, int]]:
    """Return list of (cut_id, depth), depth=0 for outermost.
    Uses rectangle containment on layout.primitives bounds in their current coords.
    """
    cuts = [(eid, prim) for eid, prim in layout.primitives.items() if getattr(prim, "element_type", "") == "cut"]
    if not cuts:
        return []
    # Simple containment check
    def contains(bbig, bsmall, tol=0.0):
        x1,y1,x2,y2 = bbig
        a1,b1,a2,b2 = bsmall
        return (a1 >= x1 - tol) and (b1 >= y1 - tol) and (a2 <= x2 + tol) and (b2 <= y2 + tol)
    bounds = {eid: prim.bounds for eid, prim in cuts}
    # Compute depth by counting number of containers
    depths = {}
    for eid, b in bounds.items():
        d = 0
        for oid, ob in bounds.items():
            if oid == eid:
                continue
            if contains(ob, b, tol=1e-6):
                d += 1
        depths[eid] = d
    # Normalize so outermost has smallest depth (0)
    min_d = min(depths.values())
    return [(eid, depths[eid] - min_d) for eid in depths]

def _level_style(level: int):
    """Return color and fill for a given nesting level."""
    palette = [
        ("#1976D2", (25, 118, 210, 30)),   # blue
        ("#388E3C", (56, 142, 60, 30)),    # green
        ("#F57C00", (245, 124, 0, 30)),    # orange
        ("#7B1FA2", (123, 31, 162, 30)),   # purple
        ("#00796B", (0, 121, 107, 30)),    # teal
    ]
    c, fill = palette[level % len(palette)]
    return c, fill

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--outdir",
        default=SRC_DIR,
        help="Directory to write PNG files (default: %(default)s)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1000,
        help="Canvas width in pixels (default: %(default)s)",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=800,
        help="Canvas height in pixels (default: %(default)s)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Draw debug overlays (cut bounds and IDs)",
    )
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    print("Rendering EGIF cut-only cases with Dau renderer...")
    for name, egif in CASES:
        print(f"- {name}: {egif}")
        g = EGIFParser(egif).parse()
        # Print EGI area hierarchy for diagnostics
        try:
            print("  EGI areas (cuts only):")
            # Build parent->children for cuts using graph.area
            area = getattr(g, 'area', {})
            cuts = {c.id for c in getattr(g, 'Cut', [])}
            for aid, contents in area.items():
                cut_children = [cid for cid in contents if cid in cuts]
                if cut_children:
                    print(f"    {aid} -> {cut_children}")
        except Exception as e:
            print(f"  (could not print area hierarchy: {e})")
        pipeline = NinePhaseLayoutPipeline()
        layout = pipeline.execute_pipeline(g)
        canvas = PySide6Canvas(args.width, args.height, title=f"Arisbe EG: {name}")
        DiagramRendererDau().render_diagram(canvas, g, layout, selected_ids=None)

        # Debug overlays: draw cut bounds and IDs as emitted by Graphviz/layout
        if args.debug:
            levels = dict(_cut_nesting_levels(layout))
            for eid, prim in layout.primitives.items():
                if getattr(prim, "element_type", "") != "cut":
                    continue
                x1, y1, x2, y2 = prim.bounds
                lvl = levels.get(eid, 0)
                color, fill = _level_style(lvl)
                # Inset overlays slightly to avoid coincident edges with production outline
                inset = 2.0 + 1.0 * min(lvl, 3)
                ix1, iy1, ix2, iy2 = x1 + inset, y1 + inset, x2 - inset, y2 - inset
                rect_pts = [(ix1, iy1), (ix2, iy1), (ix2, iy2), (ix1, iy2)]
                canvas.draw_curve(
                    rect_pts,
                    style={"color": color, "width": 1.0, "line_style": "dashed", "fill_color": fill},
                    closed=True,
                )
                canvas.draw_text(
                    f"{eid}",
                    (ix1 + 4, iy1 + 14),
                    style={"color": color, "font_size": 10},
                )
        out_path = os.path.join(args.outdir, f"render_{name}.png")
        canvas.save_to_file(out_path)
        print(f"  saved -> {out_path}")

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
