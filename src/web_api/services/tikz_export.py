"""
Portable TikZ export — a LayoutDTO rendered as standalone TikZ/LaTeX.

This is the *geometric* LaTeX path (Dau / Sowa): it consumes the
``LayoutDTO`` (absolute positions) and emits plain TikZ parametrised by
the chosen style's widths / radii / cut shape / parity shading.  It needs
no special package, so it compiles anywhere and drops into LyX/LaTeX.

(The *authentic Peirce* path is different — structural, driven by the
coordinate-free NaturalLayout and ``egpeirce.sty`` macros — and is built
separately.  See docs/MANIFEST_AND_MEANING.md and the export roadmap.)

Mirrors ``simple_svg_renderer`` for labels (``egi.get_relation_name`` /
vertex ``label``) and parity shading (cut nesting depth) so the TikZ and
SVG manifests of a graph agree.
"""

from typing import Optional

import render_geometry as rg
from egi_core_dau import RelationalGraphWithCuts
from layout_dto import LayoutDTO


_TEX_SPECIAL = {
    "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
    "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
    "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
}


def _tex_escape(s: str) -> str:
    return "".join(_TEX_SPECIAL.get(ch, ch) for ch in str(s))


def _cut_depths(egi: RelationalGraphWithCuts) -> dict:
    """Cut nesting depth (sheet=0). Mirrors SimpleSVGRenderer._compute_cut_depths."""
    if egi is None:
        return {}
    cut_ids = {c.id for c in egi.Cut}
    child_to_parent = {}
    for area_id, contents in egi.area.items():
        for elem_id in contents:
            if elem_id in cut_ids:
                child_to_parent[elem_id] = area_id
    depths = {}
    for cut_id in cut_ids:
        depth, current = 0, cut_id
        while current in child_to_parent:
            depth += 1
            current = child_to_parent[current]
        depths[cut_id] = depth
    return depths


def export_tikz(
    dto: LayoutDTO,
    egi: RelationalGraphWithCuts,
    *,
    standalone: bool = True,
    style=None,
) -> str:
    """Render *dto* as TikZ.  ``standalone`` wraps it in a compilable document.

    The picture uses ``y=-…`` so the SVG's y-down coordinates map directly
    (no manual flipping), and 1 layout px ≈ 0.75 pt for a sensible size.
    """
    style = style or dto.style
    cut_lw = getattr(style, "cut_line_width", 1.5)
    lig_lw = getattr(style, "ligature_line_width", 2.0)
    v_r = getattr(style, "vertex_radius", 3.0)
    corner = getattr(style, "cut_corner_radius", 8.0)
    raw = getattr(style, "raw_style_data", {}) or {}
    cut_shape = raw.get("cut", {}).get("shape", "rounded_rectangle")
    shade = getattr(style, "alternating_shading_enabled", True)
    v_mode = getattr(style, "vertex_rendering_mode", "dot_and_label")
    font_pt = getattr(style, "font_size", 11)
    # Hand-drawn line of identity (Peirce): organic curve + deterministic
    # waver, computed by the same shared "hand" the SVG renderer uses so the
    # two manifests agree.  Dau (orthogonal) and Sowa (manhattan) declare
    # neither, so their ligatures stay straight `--` and byte-identical.
    lig_routing = raw.get("ligature", {}).get("routing_mode", "orthogonal")
    lig_wobble = float(raw.get("ligature", {}).get("hand_drawn_variation", 0.0))
    lig_crossing_marks = raw.get("ligature", {}).get("crossing_marks", "none")

    depths = _cut_depths(egi)
    lines = []
    lines.append("\\begin{tikzpicture}[x=0.75pt,y=-0.75pt]")
    lines.append(f"  % font ~{font_pt}pt; style: {getattr(style, 'style_name', '?')}")

    # --- cuts (deepest last so even fills cover odd) ---
    cuts = sorted(
        ((cid, b) for cid, b in dto.cut_bounds.items() if cid != dto.sheet_id),
        key=lambda kv: depths.get(kv[0], 1),
    )
    for cid, b in cuts:
        depth = depths.get(cid, 1)
        fill = ""
        if shade:
            fill = "fill=black!8" if depth % 2 == 1 else "fill=white"
        opts = f"line width={cut_lw}pt" + (f",{fill}" if fill else "")
        if cut_shape == "oval":
            cx, cy = (b.min_x + b.max_x) / 2, (b.min_y + b.max_y) / 2
            rx, ry = (b.max_x - b.min_x) / 2, (b.max_y - b.min_y) / 2
            lines.append(f"  \\draw[{opts}] ({cx:.1f},{cy:.1f}) ellipse ({rx:.1f} and {ry:.1f});")
        else:
            lines.append(
                f"  \\draw[{opts},rounded corners={corner:.1f}pt] "
                f"({b.min_x:.1f},{b.min_y:.1f}) rectangle ({b.max_x:.1f},{b.max_y:.1f});"
            )

    # --- ligatures ---
    # Mirror simple_svg_renderer: a non-zero wobble first nudges the interior
    # points off the polyline; an organic/curved routing (or any wobble) then
    # draws a smooth Catmull-Rom curve; otherwise Dau's straight segments.
    curved = lig_routing in ("organic", "natural", "curved") or lig_wobble > 0
    for lig in dto.ligature_paths:
        if len(lig.points) < 2:
            continue
        pts = lig.points
        if lig_wobble > 0:
            seed = f"{lig.predicate_id}|{lig.vertex_id}|{lig.port_index}"
            pts = rg.hand_drawn_points(pts, lig_wobble * 2.0, seed)
        if curved and len(pts) >= 3:
            coords = [(p.x, p.y) for p in pts]
            path = f"({coords[0][0]:.1f},{coords[0][1]:.1f})"
            for c1, c2, p2 in rg.catmull_rom_segments(coords):
                path += (f" .. controls ({c1[0]:.1f},{c1[1]:.1f}) and "
                         f"({c2[0]:.1f},{c2[1]:.1f}) .. ({p2[0]:.1f},{p2[1]:.1f})")
            lines.append(f"  \\draw[line width={lig_lw}pt] {path};")
        else:
            seg = " -- ".join(f"({p.x:.1f},{p.y:.1f})" for p in pts)
            lines.append(f"  \\draw[line width={lig_lw}pt] {seg};")

    # --- bridge marks (Peirce's hop) at ligature crossings ---
    # Same detection + geometry as the SVG renderer; convention-gated, so
    # styles that don't declare "bridges" emit nothing here (byte-identical).
    if lig_crossing_marks == "bridges":
        radius = max(6.0, lig_lw * 2.5)
        for cr in rg.ligature_crossings(dto.ligature_paths):
            br = rg.bridge_path(cr, radius)
            # 1. erase the over-line's straight passage through the crossing
            lines.append(
                f"  \\draw[white,line width={lig_lw + 1.0}pt] "
                f"({br.a[0]:.1f},{br.a[1]:.1f}) -- ({br.b[0]:.1f},{br.b[1]:.1f});"
            )
            # 2. restore the under-line straight through the crossing
            lines.append(
                f"  \\draw[line width={lig_lw}pt] "
                f"({br.under_a[0]:.1f},{br.under_a[1]:.1f}) -- "
                f"({br.under_b[0]:.1f},{br.under_b[1]:.1f});"
            )
            # 3. the hop arc (the over-line lifting over)
            lines.append(
                f"  \\draw[line width={lig_lw}pt] ({br.a[0]:.1f},{br.a[1]:.1f}) "
                f".. controls ({br.c1[0]:.1f},{br.c1[1]:.1f}) and "
                f"({br.c2[0]:.1f},{br.c2[1]:.1f}) .. ({br.b[0]:.1f},{br.b[1]:.1f});"
            )

    # --- vertices ---
    show_dot = v_mode in ("dot_only", "dot_and_label")
    for vid, pos in dto.vertex_positions.items():
        if show_dot:
            lines.append(f"  \\fill ({pos.x:.1f},{pos.y:.1f}) circle ({v_r:.1f}pt);")
        label = ""
        v = next((v for v in egi.V if v.id == vid), None) if egi else None
        if v is not None and getattr(v, "label", None):
            label = v.label
        if label and v_mode != "dot_only":
            lines.append(
                f"  \\node[anchor=west,inner sep=1pt] at ({pos.x + v_r + 4:.1f},{pos.y:.1f}) "
                f"{{{_tex_escape(label)}}};"
            )

    # --- predicates ---
    for pid, pos in dto.predicate_positions.items():
        label = egi.get_relation_name(pid) if egi else "?"
        lines.append(
            f"  \\node[inner sep=1pt] at ({pos.x:.1f},{pos.y:.1f}) {{{_tex_escape(label)}}};"
        )

    lines.append("\\end{tikzpicture}")
    body = "\n".join(lines)

    if not standalone:
        return body
    return (
        "\\documentclass[border=8pt]{standalone}\n"
        "\\usepackage{tikz}\n"
        "\\begin{document}\n"
        f"{body}\n"
        "\\end{document}\n"
    )
