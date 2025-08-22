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

from src.egif_parser_dau import EGIFParser  # type: ignore
from src.layout_phase_implementations import NinePhaseLayoutPipeline  # type: ignore
from src.diagram_renderer_dau import DiagramRendererDau  # type: ignore
from src.pyside6_canvas import PySide6Canvas  # type: ignore
from PySide6.QtWidgets import QApplication  # type: ignore

# Minimal EGIF -> EGI helper using existing parser pieces.
# If a higher-level parse function exists, replace this logic accordingly.

def parse_egif_to_egi(text: str):
    parser = EGIFParser(text)
    return parser.parse()


def render_egif_samples(samples: dict[str, str], outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)

    pipeline = NinePhaseLayoutPipeline()
    renderer = DiagramRendererDau()

    for name, egif in samples.items():
        egi = parse_egif_to_egi(egif)
        layout_result = pipeline.execute_pipeline(egi)

        canvas = PySide6Canvas(width=900, height=700, title=f"EGIF {name}")
        # Ensure widgets are realized before grabbing image
        canvas.show()
        renderer.render_diagram(canvas, egi, layout_result)
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
