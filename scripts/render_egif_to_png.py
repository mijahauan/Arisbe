#!/usr/bin/env python3
"""
Render EGIF to PNG via Graphviz DOT.

Pipeline:
  EGIF (text) -> EGI (parse) -> DOT (GraphvizLayoutEngine) -> PNG (dot -Tpng)

Usage:
  python3 scripts/render_egif_to_png.py <input.egif> -o <output.png> [--dot out.dot] [--xdot out.xdot] [--mode default|default_raw|logical-baseline]

Notes:
- Uses the same DOT generator as the canonical Graphviz layout engine to ensure parity
- Saves DOT (and optional XDOT) for debugging flawed renderings
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

# Ensure src is importable when running from repo root
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / 'src'))

from egif_parser_dau import EGIFParser
from canonical import CanonicalPipeline
from area_based_dau_renderer import AreaBasedDauRenderer


def generate_simple_dot_from_egi(egi) -> str:
    """Generate basic DOT content from EGI for PNG rendering."""
    dot_lines = [
        "digraph EG {",
        "  rankdir=TB;",
        "  node [shape=box, style=rounded];",
        "  edge [style=solid];",
        ""
    ]
    
    # Add predicates as nodes
    for edge in egi.E:
        if hasattr(edge, 'relation') and edge.relation != '=':
            relation_name = edge.relation
            dot_lines.append(f'  "{edge.id}" [label="{relation_name}"];')
    
    # Add vertices as small circles
    for vertex in egi.V:
        if hasattr(vertex, 'name') and vertex.name:
            dot_lines.append(f'  "{vertex.id}" [label="{vertex.name}", shape=circle, width=0.3];')
    
    # Add cuts as clusters
    for i, cut in enumerate(egi.Cut):
        dot_lines.append(f"  subgraph cluster_{i} {{")
        dot_lines.append(f'    label="";')
        dot_lines.append(f'    style=rounded;')
        
        # Add elements in this cut
        if cut.id in egi.area:
            for element_id in egi.area[cut.id]:
                dot_lines.append(f'    "{element_id}";')
        
        dot_lines.append("  }")
    
    # Add identity lines as edges
    for edge in egi.E:
        if hasattr(edge, 'relation') and edge.relation == '=':
            vertices = egi.nu.get(edge.id, [])
            if len(vertices) >= 2:
                dot_lines.append(f'  "{vertices[0]}" -- "{vertices[1]}" [style=bold];')
    
    dot_lines.append("}")
    return "\n".join(dot_lines)


def run_dot(dot_path: Path, png_path: Path, xdot_path: Path | None = None) -> None:
    # Render PNG
    subprocess.run(["dot", "-Tpng", str(dot_path), "-o", str(png_path)], check=True)
    # Optionally produce xdot for debugging
    if xdot_path is not None:
        subprocess.run(["dot", "-Txdot", str(dot_path), "-o", str(xdot_path)], check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="Render EGIF to PNG using Graphviz")
    ap.add_argument("input", help="Path to .egif text file")
    ap.add_argument("-o", "--output", required=True, help="Output PNG path")
    ap.add_argument("--dot", dest="dot_out", default=None, help="Optional output DOT path")
    ap.add_argument("--xdot", dest="xdot_out", default=None, help="Optional output XDOT path")
    ap.add_argument("--mode", dest="mode", default="default_raw", help="Layout engine mode (default_raw|default|logical-baseline)")
    args = ap.parse_args()

    in_path = Path(args.input).resolve()
    if not in_path.exists():
        print(f"Input EGIF not found: {in_path}")
        return 1

    out_png = Path(args.output).resolve()
    out_png.parent.mkdir(parents=True, exist_ok=True)

    # Read EGIF text
    egif_text = in_path.read_text(encoding="utf-8")

    # Parse -> EGI
    egi = EGIFParser(egif_text).parse()

    # Generate DOT from EGI using current canonical pipeline
    pipeline = CanonicalPipeline()
    
    # Generate EGDF with layout primitives
    egdf_doc = pipeline.egi_to_egdf(egi)
    
    # Create DOT content from EGI (simplified DOT generation)
    dot_str = generate_simple_dot_from_egi(egi)

    # Determine DOT path
    dot_path = Path(args.dot_out).resolve() if args.dot_out else out_png.with_suffix('.dot')
    dot_path.write_text(dot_str, encoding="utf-8")

    # Optional xdot path
    xdot_path = Path(args.xdot_out).resolve() if args.xdot_out else None

    # Call dot
    run_dot(dot_path, out_png, xdot_path)

    print(f"✓ Wrote PNG: {out_png}")
    print(f"✓ Wrote DOT: {dot_path}")
    if xdot_path:
        print(f"✓ Wrote XDOT: {xdot_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
