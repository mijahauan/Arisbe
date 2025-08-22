#!/usr/bin/env python3
"""
Batch EGIF → EGI → Layout (Graphviz) → Render (Dau) validator.

- Loads all EGIF files in corpus/* (recursively)
- Generates layout with GraphvizLayoutEngineV2
- Renders with DiagramRendererDau on a PySide6Canvas (offscreen)
- Saves PNGs under reports/corpus_visuals/<name>.png
- Emits JSON report with basic geometry checks
"""
import os
import sys
import json
import traceback
from typing import List, Dict, Tuple

# Local imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from egif_parser_dau import EGIFParser
from egi_core_dau import RelationalGraphWithCuts
from layout_phase_implementations import NinePhaseLayoutPipeline
from diagram_renderer_dau import DiagramRendererDau
from pyside6_canvas import create_qt_canvas


def find_egif_files(root: str) -> List[str]:
    egifs = []
    for base, _, files in os.walk(root):
        for f in files:
            if f.lower().endswith('.egif') or f.lower().endswith('.txt'):
                egifs.append(os.path.join(base, f))
    return sorted(egifs)


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def basic_geometry_checks(graph: RelationalGraphWithCuts, layout_result) -> List[str]:
    """Very light checks for now. Extend as needed.
    - All primitives have finite bounds
    - Predicates are within canvas area bounds (assumes positive coords)
    """
    issues = []
    for pid, prim in layout_result.primitives.items():
        bx1, by1, bx2, by2 = prim.bounds
        if any(not isinstance(v, (int, float)) for v in (bx1, by1, bx2, by2)):
            issues.append(f"non-numeric bounds for {pid}")
        if bx2 < bx1 or by2 < by1:
            issues.append(f"invalid bounds for {pid}: {prim.bounds}")
    return issues


def render_to_png(out_path: str, renderer: DiagramRendererDau, graph: RelationalGraphWithCuts, layout_result) -> None:
    canvas = create_qt_canvas(1200, 900, title="Corpus Render")
    renderer.render_diagram(canvas, graph, layout_result)
    canvas.save_to_file(out_path)


def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    corpus_dir = os.path.join(repo_root, 'corpus')
    # Prefer top-level corpus dir (avoid nested dup)
    if not os.path.isdir(corpus_dir):
        # fallback to nested corpus/corpus
        corpus_dir = os.path.join(repo_root, 'corpus', 'corpus')
    if not os.path.isdir(corpus_dir):
        print("No corpus directory found.")
        return 1

    out_dir = os.path.join(repo_root, 'reports', 'corpus_visuals')
    ensure_dir(out_dir)

    pipeline = NinePhaseLayoutPipeline()
    renderer = DiagramRendererDau()

    results: List[Dict] = []

    egif_files = find_egif_files(corpus_dir)
    if not egif_files:
        print("No EGIF files found in corpus.")
        return 1

    for path in egif_files:
        name = os.path.splitext(os.path.basename(path))[0]
        rec: Dict = {"file": os.path.relpath(path, repo_root), "status": "ok", "issues": []}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                egif_text = f.read()
            graph = EGIFParser(egif_text).parse()
            layout_result = pipeline.execute_pipeline(graph)
            rec["issues"].extend(basic_geometry_checks(graph, layout_result))
            png_path = os.path.join(out_dir, f"{name}.png")
            render_to_png(png_path, renderer, graph, layout_result)
            rec["image"] = os.path.relpath(png_path, repo_root)
        except Exception as e:
            rec["status"] = "error"
            rec["error"] = str(e)
            rec["trace"] = traceback.format_exc(limit=5)
        results.append(rec)
        print(f"Processed: {rec['file']} -> {rec['status']}")

    report_path = os.path.join(repo_root, 'reports', 'corpus_report.json')
    ensure_dir(os.path.dirname(report_path))
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({"results": results}, f, indent=2)
    print(f"Report written to {report_path}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
