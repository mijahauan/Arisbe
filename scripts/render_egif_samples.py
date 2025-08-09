#!/usr/bin/env python3
"""
Render a handful of EGIF expressions through the canonical pipeline to PNGs.
Outputs into reports/sanity_egif/.
"""
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.egif_parser_dau import EGIFLexer, EGIFSyntaxValidator, parse_egif  # type: ignore
from src.egi_core_dau import RelationalGraphWithCuts  # type: ignore
from src.graphviz_layout_engine_v2 import GraphvizLayoutEngine  # type: ignore
from src.layout_post_processor import LayoutPostProcessor  # type: ignore
from src.diagram_renderer_dau import DiagramRendererDau  # type: ignore
from src.pyside6_canvas import PySide6Canvas  # type: ignore
from PySide6.QtWidgets import QApplication  # type: ignore

# Minimal EGIF -> EGI helper using existing parser pieces.
# If a higher-level parse function exists, replace this logic accordingly.

def parse_egif_to_egi(text: str) -> RelationalGraphWithCuts:
    lex = EGIFLexer(text)
    tokens = lex.tokenize()
    if not EGIFSyntaxValidator(tokens).validate():
        raise ValueError("Invalid EGIF syntax")
    return parse_egif(text)


def render_egif_samples(samples: dict[str, str], outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)

    engine = GraphvizLayoutEngine()
    post = LayoutPostProcessor()
    renderer = DiagramRendererDau()

    for name, egif in samples.items():
        graph = parse_egif_to_egi(egif)
        layout = engine.layout(graph)
        layout2 = post.process_layout(layout)

        canvas = PySide6Canvas(width=900, height=700, title=f"EGIF {name}")
        # Ensure widgets are realized before grabbing image
        canvas.show()
        renderer.render_diagram(canvas, graph, layout2)
        # Process events to ensure paint
        app = QApplication.instance()
        if app is not None:
            app.processEvents()
        png_path = outdir / f"{name}.png"
        canvas.save_to_file(str(png_path))
        print(f"Wrote {png_path}")


def main():
    samples = {
        # unary and binary
        "unary_socrates": '(Man "Socrates")',
        "binary_loves": '(Loves "Socrates" "Plato")',
        # negation & double cut
        "negation": '~[(Mortal "Socrates")]',
        "double_cut": '~[ ~[(Mortal "Socrates")] ]',
        # ligature same var twice
        "reflexive": '(Loves *x x)',
        # ligature across cut
        "across_cut": '(Human *x) ~[(Immortal x)]',
        # disjunction as sibling cuts
        "disjunction1": '~[ ~[(Man "Socrates")] ~[(Mortal "Socrates")] ]',
        "disjunction2": '~[ ~[(Rained)] ~[(Snowed)] ]',
        "disjunction_var": '~[ ~[(Human *x)] ~[(Immortal x)] ]',
        # implication patterns
        "implication_simple": '~[ (Human *x) ~[(Mortal x)] ]',
        "implication_const": '~[ (Loves "Socrates" "Plato") ~[(Happy "Plato")] ]',
        "implication_nested": '~[ (A) ~[ (B) ~[(C)] ] ]',
        "implication_conj_ante": '~[ (A) (B) ~[(C)] ]',
    }

    outdir = Path("reports/sanity_egif")
    render_egif_samples(samples, outdir)


if __name__ == "__main__":
    main()
