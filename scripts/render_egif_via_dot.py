#!/usr/bin/env python3
"""
Render EGIF expressions to PNG using the canonical pipeline and a headless Qt canvas.

Pipeline:
  EGIF → EGI → GraphvizLayoutEngine (DOT/xdot) → LayoutResult (post-processed) → DiagramRendererDau → PNG

Outputs into reports/sanity_egif_dot/.
We still emit a .dot file for diagnostics, but rendering is done by our Dau-compliant renderer.
"""
from __future__ import annotations
import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.egif_parser_dau import parse_egif  # type: ignore
from src.graphviz_layout_engine_v2 import GraphvizLayoutEngine  # type: ignore
from src.diagram_renderer_dau import DiagramRendererDau  # type: ignore
from src.pyside6_canvas import PySide6Canvas  # type: ignore


def render_one(name: str, egif_text: str, outdir: Path, mode: str = "default") -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    graph = parse_egif(egif_text)
    engine = GraphvizLayoutEngine(mode=mode)
    # Diagnostics: write DOT content used by the layout engine
    dot_content = engine._generate_dot_from_egi(graph)  # noqa: SLF001 (diagnostic export only)
    dot_path = outdir / f"{name}.dot"
    dot_path.write_text(dot_content, encoding="utf-8")

    # Also emit xdot for diagnostics (to inspect parser issues)
    try:
        import subprocess, shlex
        xdot_path = outdir / f"{name}.xdot"
        cmd = f"dot -Txdot {shlex.quote(str(dot_path))}"
        xdot_out = subprocess.check_output(cmd, shell=True, text=True)
        xdot_path.write_text(xdot_out, encoding="utf-8")
    except Exception as e:
        print(f"⚠️  Failed to write xdot for {name}: {e}")

    # Canonical layout + render
    layout = engine.create_layout_from_graph(graph)
    canvas = PySide6Canvas(width=900, height=650, title=f"EG: {name}")
    renderer = DiagramRendererDau()
    renderer.render_diagram(canvas, graph, layout)

    # Add EGIF source at the bottom-left margin for logic checking
    margin_x, margin_y = 14.0, 630.0  # slightly above bottom to avoid clipping
    canvas.draw_text(
        text=egif_text,
        position=(margin_x, margin_y),
        style={
            'font_family': 'Menlo',
            'font_size': 11,
            'color': (80, 80, 80),
            'draggable': False,
        }
    )

    png_path = outdir / f"{name}.png"
    canvas.save_to_file(str(png_path))
    print(f"Wrote {png_path}")


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["default", "default_raw", "logical"], default="default", help="Layout mode: default (Graphviz-based), default_raw (no post-process), or logical (coherent baseline)")
    args = ap.parse_args()
    samples = {
        # baseline
        "unary_socrates": '(Man "Socrates")',
        "binary_loves": '(Loves "Socrates" "Plato")',
        # negation & double cut
        "negation": '~[(Mortal "Socrates")]',
        "double_cut": '~[ ~[(Mortal "Socrates")] ]',
        # ligature same var twice
        "reflexive": '(Loves *x x)',
        # ligature across cut
        "across_cut": '(Human *x) ~[(Immortal x)]',
        # disjunction: sibling cuts
        "disjunction1": '~[ ~[(Man "Socrates")] ~[(Mortal "Socrates")] ]',
        "disjunction2": '~[ ~[(Rained)] ~[(Snowed)] ]',
        "disjunction_var": '~[ ~[(Human *x)] ~[(Immortal x)] ]',
        # implications
        "implication_simple": '~[ (Human *x) ~[(Mortal x)] ]',
        "implication_const": '~[ (Loves "Socrates" "Plato") ~[(Happy "Plato")] ]',
        "implication_nested": '~[ (A) ~[ (B) ~[(C)] ] ]',
        "implication_conj_ante": '~[ (A) (B) ~[(C)] ]',
    }
    outdir = PROJECT_ROOT / "reports" / "sanity_egif_dot"
    for name, egif in samples.items():
        render_one(name, egif, outdir, mode=args.mode)


if __name__ == "__main__":
    main()
