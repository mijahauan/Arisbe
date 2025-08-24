#!/usr/bin/env python3
"""
TikZ exporter for Arisbe render commands.

Converts platform-agnostic render commands into a standalone TikZ picture.
This is a minimal scaffold that supports vertices, predicates (edges), cuts, and ligatures.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple
from styling.style_manager import create_style_manager


def _tikz_header() -> str:
    return "\n".join([
        "\\documentclass[tikz]{standalone}",
        "\\usepackage{tikz}",
        "\\begin{document}",
        "\\begin{tikzpicture}[x=1pt,y=1pt]",
    ])


def _tikz_footer() -> str:
    return "\n".join([
        "\\end{tikzpicture}",
        "\\end{document}",
        "",
    ])


def _escape_text(s: str) -> str:
    # Minimal escaping for TikZ
    return s.replace("_", "\\_")


def _emit_vertex(cmd: Dict[str, Any], styles) -> str:
    b = cmd.get("bounds", {})
    x = float(b.get("x", 0.0)) + float(b.get("width", 0.0)) / 2.0
    y = float(b.get("y", 0.0)) + float(b.get("height", 0.0)) / 2.0
    label = cmd.get("vertex_name") or cmd.get("element_id", "")
    s = styles.resolve(type="vertex", role="vertex.label")
    fs = float(s.get("font_size", styles.resolve(type="global").get("font_size", 10)))
    baselineskip = fs + 2
    return (
        f"\\fill ( {x:.2f} , {y:.2f} ) circle [radius=2pt] "
        f"node[anchor=west,font=\\fontsize{{{fs:.0f}}}{{{baselineskip:.0f}}}\\selectfont] "
        f"{{ {_escape_text(label)} }};"
    )


def _emit_predicate(cmd: Dict[str, Any], styles) -> str:
    b = cmd.get("bounds", {})
    x = float(b.get("x", 0.0))
    y = float(b.get("y", 0.0))
    w = float(b.get("width", 0.0))
    h = float(b.get("height", 0.0))
    label = cmd.get("relation_name") or cmd.get("element_id", "")
    # Background fill follows cut fill based on area parity; border is transparent
    ap = int(cmd.get("area_parity", 0))
    s_fill_cut = styles.resolve(type="cut", role="cut.fill")
    # Derive opacity from rgba(...) if present, else default 0.31 for shaded
    fill_opacity = 0.31
    fc = str(s_fill_cut.get("fill_color", "rgba(240,240,240,0.31)"))
    if fc.startswith("rgba"):
        try:
            alpha_str = fc.split("(")[1].split(")")[0].split(",")[-1].strip()
            fill_opacity = float(alpha_str)
        except Exception:
            pass
    rect = "% predicate background\n"
    if ap == 1:
        rect += f"\\draw[fill=black,fill opacity={fill_opacity:.2f},draw=none] ( {x:.2f} , {y:.2f} ) rectangle ( {x+w:.2f} , {y+h:.2f} );"
    else:
        rect += f"% even parity: no background for predicate box\n"
    ts = styles.resolve(type="edge", role="edge.label_text")
    fs = float(ts.get("font_size", styles.resolve(type="global").get("font_size", 10)))
    baselineskip = fs + 2
    text = (
        f"\\node[font=\\fontsize{{{fs:.0f}}}{{{baselineskip:.0f}}}\\selectfont] "
        f"at ( {x + w/2:.2f} , {y + h/2:.2f} ) {{{_escape_text(label)}}};"
    )
    return rect + "\n" + text


def _emit_cut(cmd: Dict[str, Any], styles) -> str:
    b = cmd.get("bounds", {})
    x = float(b.get("x", 0.0))
    y = float(b.get("y", 0.0))
    w = float(b.get("width", 100.0))
    h = float(b.get("height", 100.0))
    # Rounded rectangle border; fill depends on area parity
    ap = int(cmd.get("area_parity", 0))
    s_border = styles.resolve(type="cut", role="cut.border")
    s_fill = styles.resolve(type="cut", role="cut.fill")
    line_w_pt = float(s_border.get("line_width", 1)) * 0.4  # rough mapping
    radius = float(s_border.get("radius", 8))
    fc = str(s_fill.get("fill_color", "rgba(240,240,240,0.31)"))
    fill_opacity = 0.31
    if fc.startswith("rgba"):
        try:
            alpha_str = fc.split("(")[1].split(")")[0].split(",")[-1].strip()
            fill_opacity = float(alpha_str)
        except Exception:
            pass
    if ap == 1:
        return (
            f"\\draw[line width={line_w_pt:.2f}pt,rounded corners={radius:.1f}pt,fill=black,fill opacity={fill_opacity:.2f}] "
            f"( {x:.2f} , {y:.2f} ) rectangle ( {x+w:.2f} , {y+h:.2f} );"
        )
    else:
        return (
            f"\\draw[line width={line_w_pt:.2f}pt,rounded corners={radius:.1f}pt] "
            f"( {x:.2f} , {y:.2f} ) rectangle ( {x+w:.2f} , {y+h:.2f} );"
        )


def _emit_ligature(cmd: Dict[str, Any], styles) -> str:
    pts: List[Tuple[float, float]] = cmd.get("path_points", []) or []
    if len(pts) < 2:
        return "% ligature with insufficient points"
    path_parts = [f"( {pts[0][0]:.2f} , {pts[0][1]:.2f} )"]
    for (x, y) in pts[1:]:
        path_parts.append(f"-- ( {x:.2f} , {y:.2f} )")
    path = " ".join(path_parts)
    s = styles.resolve(type="ligature", role=cmd.get("role"))
    lw = float(s.get("line_width", 3)) * 0.4  # rough mapping to pt
    cap = str(s.get("cap", "round")).lower()
    if cap == "round":
        cap_opt = "round"
    elif cap == "square":
        cap_opt = "rect"
    else:
        cap_opt = "butt"
    return f"\\draw[line width={lw:.2f}pt,line cap={cap_opt}] {path};"


def generate_tikz(render_commands: List[Dict[str, Any]], standalone: bool = True) -> str:
    """Generate TikZ from Arisbe render commands.

    If standalone is True, returns a full LaTeX document; otherwise returns only the tikzpicture body.
    """
    body_lines: List[str] = []

    # Draw cuts first, then predicates, vertices, then ligatures on top
    cuts = [c for c in render_commands if c.get("type") == "cut"]
    edges = [c for c in render_commands if c.get("type") == "edge"]
    vertices = [c for c in render_commands if c.get("type") == "vertex"]
    ligatures = [c for c in render_commands if c.get("type") == "ligature"]

    styles = create_style_manager()

    for c in cuts:
        body_lines.append(_emit_cut(c, styles))
    for e in edges:
        body_lines.append(_emit_predicate(e, styles))
    for v in vertices:
        body_lines.append(_emit_vertex(v, styles))
    for l in ligatures:
        body_lines.append(_emit_ligature(l, styles))

    body = "\n".join(body_lines) + "\n"

    if not standalone:
        return "\n".join(["% tikzpicture", "\\begin{tikzpicture}[x=1pt,y=1pt]", body, "\\end{tikzpicture}", ""]) 

    return "\n".join([_tikz_header(), body, _tikz_footer()])
