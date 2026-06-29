"""
Authentic-Peirce Existential Graph → LaTeX/TikZ export.

This is the *authentic Peirce* counterpart to the geometric
``web_api/services/tikz_export`` (Dau/Sowa boxes).  It reimplements the
**function** of Jukka Nikulainen's ``egpeirce.sty`` — oval cuts, scrolls,
heavy lines of identity, hooks, argument order — but in **pure TikZ** that
compiles with plain ``pdflatex`` (no PSTricks), via the shipped semantic
macro package ``src/tex/arisbe-eg.sty``.

Two things make it more than a typesetting package:

* **Wedded to the logic.**  egpeirce draws marks with no model underneath.
  This exporter is a *pure function of a §3.3-attested* ``LayoutDTO`` (the
  pair (EGI, DTO) is verified by ``attest_correspondence`` inside
  ``generate_layout`` *before* this runs).  The drawing therefore provably
  denotes the same Existential Graph as the EGI.  Every cut / predicate /
  vertex id is emitted as a comment, so the ``.tex`` is traceable to the EGI.

* **Correspondence for free.**  Because it draws the DTO's own coordinates —
  ovals at ``cut_bounds``; heavy lines from ``vertex_positions`` to a hook on
  the ``predicate → points[0]`` ray (which *preserves the hook angle* the
  reader keys argument order off) — the picture *is* the DTO.  So the existing
  reader (``eg_reader.read_drawing`` + ``reading_matches_egi``) vouches for
  the printed graph; see ``tests/test_peirce_latex.py``.

The "Peirce-authentic" *style* (``styles/peirce-authentic@1.0.json``) supplies
oval cut shape, heavy round-capped ligatures, organic routing, hand-drawn
waver, and bridges at crossings; this exporter reads those knobs and draws
accordingly.  The shared "hand" (curve + waver + bridge geometry) is
``render_geometry``, used identically by the SVG and geometric-TikZ renderers,
so the three manifests of a graph agree.
"""

from collections import defaultdict
from pathlib import Path
from typing import Optional

import render_geometry as rg
from egi_core_dau import RelationalGraphWithCuts
from layout_dto import LayoutDTO, Point

# 1 layout px ≈ 0.75 pt — a sensible printed size (matches tikz_export).
SCALE = 0.75

_STY_PATH = Path(__file__).parent / "tex" / "arisbe-eg.sty"

_TEX_SPECIAL = {
    "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
    "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
    "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
}


def _tex_escape(s: str) -> str:
    return "".join(_TEX_SPECIAL.get(ch, ch) for ch in str(s))


def _cut_depths(egi: RelationalGraphWithCuts) -> dict:
    """Cut nesting depth (sheet=0).  Mirrors SimpleSVGRenderer._compute_cut_depths
    and tikz_export._cut_depths so parity shading agrees across renderers."""
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


def _macro_preamble() -> str:
    """The ``arisbe-eg`` macro definitions, ready to inline into a standalone
    preamble: the shipped ``.sty`` minus its package boilerplate (we add our own
    ``\\usepackage{tikz}`` and wrap the block in ``\\makeatletter`` so the ``@``
    in the internal control sequences is a letter outside a package)."""
    text = _STY_PATH.read_text(encoding="utf-8")
    keep = []
    for line in text.splitlines():
        s = line.lstrip()
        if (s.startswith("\\NeedsTeXFormat")
                or s.startswith("\\ProvidesPackage")
                or s.startswith("\\RequirePackage")
                or s.startswith("\\endinput")):
            continue
        keep.append(line)
    return "\n".join(keep)


def _hook_point(P: Point, half_w: float, half_h: float, toward: Point) -> Point:
    """Where the line of identity should terminate at the predicate's label box:
    the intersection of the ray ``P → toward`` with the axis-aligned box of
    half-extents ``(half_w, half_h)`` centred at ``P``.  Staying on the
    ``P → toward`` ray preserves the hook *angle* (so ``read_drawing``'s
    clockwise argument order is unchanged), while trimming the heavy line off
    the relation text."""
    dx, dy = toward.x - P.x, toward.y - P.y
    if dx == 0 and dy == 0:
        return toward
    tx = half_w / abs(dx) if dx != 0 else float("inf")
    ty = half_h / abs(dy) if dy != 0 else float("inf")
    t = min(tx, ty)
    return Point(P.x + dx * t, P.y + dy * t)


def _scroll_map(egi, cut_ids):
    """Map each scroll's outer cut id → its inner cut id: an outer cut whose area
    holds exactly one child cut AND some non-cut content A (Peirce's
    ``~[ A ~[ B ] ]``).  A bare double cut ``~[~[]]`` (no antecedent A) is NOT a
    scroll."""
    out = {}
    for cid in cut_ids:
        area = egi.get_area(cid)
        children = [e for e in area if e in cut_ids]
        non_cut = [e for e in area if e not in cut_ids]
        if len(children) == 1 and non_cut:
            out[cid] = children[0]
    return out


def _scroll_outer_points(bo, bi, n: int = 40):
    """The outer curve of an iconic scroll: the outer oval (bounds ``bo``) with a
    downward cusp at the top that dips to kiss the inner oval (bounds ``bi``).
    Returned as an ordered closed ring of DTO points (the caller closes it)."""
    import math
    cxo, cyo = (bo.min_x + bo.max_x) / 2.0, (bo.min_y + bo.max_y) / 2.0
    rxo, ryo = (bo.max_x - bo.min_x) / 2.0, (bo.max_y - bo.min_y) / 2.0
    cxi, cyi = (bi.min_x + bi.max_x) / 2.0, (bi.min_y + bi.max_y) / 2.0
    rxi, ryi = (bi.max_x - bi.min_x) / 2.0, (bi.max_y - bi.min_y) / 2.0
    top = -math.pi / 2.0     # min-y direction in DTO (y-down) coords
    gap = math.radians(26)   # the opening at the top where the neck tucks in
    pts = []
    a0, a1 = top + gap, top + 2.0 * math.pi - gap  # the long way round (through the bottom)
    for i in range(n + 1):
        t = a0 + (a1 - a0) * i / n
        pts.append(Point(cxo + rxo * math.cos(t), cyo + ryo * math.sin(t)))
    # The neck: from the right side of the gap, plunge down and wrap over the
    # inner oval's top, back up to the left side — so the inner loop nestles in
    # the scroll's neck (Peirce's self-continuing curve).
    pts.append(Point(cxi + rxi * 0.85, cyi - ryi * 0.75))  # inner upper-right
    pts.append(Point(cxi, cyi - ryi - 0.5))                # inner top (kissed)
    pts.append(Point(cxi - rxi * 0.85, cyi - ryi * 0.75))  # inner upper-left
    return pts


def _closed_path_spec(pts) -> str:
    """A smooth closed TikZ path (cyclic Catmull-Rom) through ``pts``."""
    ring = [(p.x, p.y) for p in pts] + [(pts[0].x, pts[0].y)]
    s = f"({ring[0][0]:.2f},{ring[0][1]:.2f})"
    for c1, c2, p2 in rg.catmull_rom_segments(ring):
        s += (f" .. controls ({c1[0]:.2f},{c1[1]:.2f}) and "
              f"({c2[0]:.2f},{c2[1]:.2f}) .. ({p2[0]:.2f},{p2[1]:.2f})")
    return s + " -- cycle"


def _path_spec(pts, curved: bool) -> str:
    """A TikZ path body through ``pts``: a flowing Catmull-Rom curve (Peirce's
    organic line of identity) when ``curved`` and ≥3 points, else straight
    segments.  Coordinates are in the picture's (scaled, y-flipped) units."""
    coords = [(p.x, p.y) for p in pts]
    if curved and len(coords) >= 3:
        s = f"({coords[0][0]:.2f},{coords[0][1]:.2f})"
        for c1, c2, p2 in rg.catmull_rom_segments(coords):
            s += (f" .. controls ({c1[0]:.2f},{c1[1]:.2f}) and "
                  f"({c2[0]:.2f},{c2[1]:.2f}) .. ({p2[0]:.2f},{p2[1]:.2f})")
        return s
    return " -- ".join(f"({x:.2f},{y:.2f})" for x, y in coords)


def export_peirce_latex(
    dto: LayoutDTO,
    egi: RelationalGraphWithCuts,
    *,
    standalone: bool = True,
    style=None,
    document_class: str = "standalone",
    scroll_glyph: bool = False,
) -> str:
    """Render the §3.3-attested *dto* of *egi* as authentic-Peirce TikZ.

    ``scroll_glyph`` (opt-in) draws a detected scroll ``~[ A ~[ B ] ]`` as the
    **iconic self-continuing scroll** — the outer cut as an oval with a downward
    cusp at the top that kisses the inner oval — instead of two plain nested
    ovals.  It is **ink only**: ``cut_bounds`` is untouched, so §3.3 and
    ``read_drawing`` (which read the DTO, not the stroke) still validate exactly,
    just like the hand-drawn waver and the crossing bridges.  Default off so the
    robust nested-oval rendering stays the corpus-faithful baseline.

    ``standalone`` wraps the picture in a compilable single-file document (the
    ``arisbe-eg`` macros inlined, so it needs nothing installed beyond a LaTeX +
    TikZ toolchain); otherwise it returns the bare ``tikzpicture`` (use with
    ``\\usepackage{arisbe-eg}``).

    ``document_class`` selects the standalone wrapper: ``"standalone"`` (the
    publication default — a tightly-cropped PDF ready to ``\\includegraphics``,
    needs the ``standalone`` class from a full TeX install) or ``"article"`` (a
    universal fallback that compiles on a minimal install such as BasicTeX).
    """
    style = style or dto.style
    raw = getattr(style, "raw_style_data", {}) or {}

    cut_lw = float(getattr(style, "cut_line_width", 1.5))
    lig_lw = float(getattr(style, "ligature_line_width", 2.0))
    shade = bool(getattr(style, "alternating_shading_enabled", True))
    v_mode = getattr(style, "vertex_rendering_mode", "label_only")
    style_name = getattr(style, "style_name", "?")

    lig_routing = raw.get("ligature", {}).get("routing_mode", "organic")
    lig_wobble = float(raw.get("ligature", {}).get("hand_drawn_variation", 0.0))
    lig_crossing_marks = raw.get("ligature", {}).get("crossing_marks", "none")
    char_w = float(raw.get("predicate", {}).get(
        "char_width_estimate", getattr(style, "predicate_char_width", 6.5)))
    char_h = float(raw.get("predicate", {}).get(
        "height_estimate", getattr(style, "predicate_height", 13.0)))
    pad = raw.get("predicate", {}).get("label_box_padding", [3, 2])
    pad_x, pad_y = float(pad[0]), float(pad[1])
    variable_labels = raw.get("variable_labels", {}).get("enabled", False)

    cut_ids = {c.id for c in egi.Cut}
    depths = _cut_depths(egi)
    dot_radius = max(2.0, lig_lw) * SCALE  # branch spot a touch heavier than the line

    L = []
    L.append(f"\\begin{{tikzpicture}}[x={SCALE:g}pt,y=-{SCALE:g}pt]")
    L.append(f"  % authentic Peirce EG · style: {style_name}")
    L.append(f"  \\egset{{cut width={cut_lw:.2f}pt, loi width={lig_lw:.2f}pt, "
             f"dot radius={dot_radius:.2f}pt}}")

    # A scroll = an outer cut whose area holds exactly one child cut AND some
    # non-cut content A (Peirce's `~[ A ~[ B ] ]`); a bare double cut `~[~[]]`
    # is NOT a scroll.  `scroll_glyph` draws the outer cut as the iconic
    # self-continuing curve; otherwise (and always for the inner cut) a plain oval.
    scrolls = _scroll_map(egi, cut_ids) if scroll_glyph else {}

    # --- cuts: ovals at cut_bounds, deepest last so even fills cover odd -----
    cuts = sorted((c.id for c in egi.Cut), key=lambda cid: depths.get(cid, 1))
    for cid in cuts:
        b = dto.cut_bounds.get(cid)
        if b is None:
            continue
        depth = depths.get(cid, 1)
        cx, cy = (b.min_x + b.max_x) / 2.0, (b.min_y + b.max_y) / 2.0
        rx, ry = (b.max_x - b.min_x) / 2.0, (b.max_y - b.min_y) / 2.0
        fill = "black!6" if (shade and depth % 2 == 1) else "none"
        if cid in scrolls:
            inner_b = dto.cut_bounds.get(scrolls[cid])
            if inner_b is not None:
                L.append(f"  % scroll outer={cid} inner={scrolls[cid]} depth {depth}")
                path = _closed_path_spec(_scroll_outer_points(b, inner_b))
                L.append(f"  \\draw[eg cut, fill={fill}] {path};")
                continue
        L.append(f"  % cut {cid} depth {depth}")
        L.append(f"  \\egcut{{{cx:.2f}}}{{{cy:.2f}}}"
                 f"{{{rx * SCALE:.2f}pt}}{{{ry * SCALE:.2f}pt}}{{{fill}}}")

    # When not drawing the iconic glyph, still annotate detected scrolls so the
    # `.tex` records the conditional structure (the nested ovals already read it).
    if not scroll_glyph:
        for cid, inner in _scroll_map(egi, cut_ids).items():
            L.append(f"  % scroll: outer={cid} inner={inner}")

    # --- lines of identity (a branching tree, grouped by vertex) ------------
    groups = defaultdict(list)
    for lig in dto.ligature_paths:
        groups[lig.vertex_id].append(lig)

    curved = lig_routing in ("organic", "natural", "curved") or lig_wobble > 0
    for lig in dto.ligature_paths:
        if len(lig.points) < 2:
            continue
        pts = list(lig.points)
        # Trim the predicate end to the label-box edge along the hook ray.
        P = dto.predicate_positions.get(lig.predicate_id)
        if P is not None:
            label = egi.get_relation_name(lig.predicate_id)
            half_w = 0.5 * max(1, len(label)) * char_w + pad_x
            half_h = 0.5 * char_h + pad_y
            pts[0] = _hook_point(P, half_w, half_h, pts[0])
        if lig_wobble > 0:
            seed = f"{lig.predicate_id}|{lig.vertex_id}|{lig.port_index}"
            pts = rg.hand_drawn_points(pts, lig_wobble * 2.0, seed)
        L.append(f"  \\egloi{{{_path_spec(pts, curved)}}}")

    # --- bridges (Peirce's hop) at genuine projection crossings -------------
    if lig_crossing_marks == "bridges":
        radius = max(6.0, lig_lw * 2.5)
        for cr in rg.ligature_crossings(dto.ligature_paths):
            br = rg.bridge_path(cr, radius)
            L.append(f"  \\draw[eg bridge erase] ({br.a[0]:.2f},{br.a[1]:.2f}) "
                     f"-- ({br.b[0]:.2f},{br.b[1]:.2f});")
            L.append(f"  \\draw[eg loi] ({br.under_a[0]:.2f},{br.under_a[1]:.2f}) "
                     f"-- ({br.under_b[0]:.2f},{br.under_b[1]:.2f});")
            L.append(f"  \\draw[eg loi] ({br.a[0]:.2f},{br.a[1]:.2f}) .. controls "
                     f"({br.c1[0]:.2f},{br.c1[1]:.2f}) and ({br.c2[0]:.2f},{br.c2[1]:.2f}) "
                     f".. ({br.b[0]:.2f},{br.b[1]:.2f});")

    # --- vertices: identity / branch spots + constant labels ----------------
    rho = getattr(egi, "rho", {})
    var_names = getattr(egi, "variable_names", {})
    for vid, pos in dto.vertex_positions.items():
        k = len(groups.get(vid, []))
        const = rho.get(vid)
        # Always emit the id (traceability), even when the spot is suppressed.
        L.append(f"  % vertex {vid}")
        # k==0 isolated vertex, or k>=3 teridentity → a visible spot.  k in {1,2}
        # is a continuous line; suppress the bare dot under label_only.
        if k == 0 or k >= 3 or v_mode != "label_only":
            L.append(f"  \\egdot{{{pos.x:.2f}}}{{{pos.y:.2f}}}")
        if const:
            L.append(f"  \\egconst{{{pos.x + 6:.2f}}}{{{pos.y:.2f}}}{{{_tex_escape(const)}}}")
        elif variable_labels and var_names.get(vid):
            L.append(f"  \\egconst{{{pos.x + 6:.2f}}}{{{pos.y:.2f}}}"
                     f"{{$_{{{_tex_escape(var_names[vid])}}}$}}")

    # --- predicates (relation spots) ----------------------------------------
    for pid, pos in dto.predicate_positions.items():
        label = egi.get_relation_name(pid)
        L.append(f"  % pred {pid} {label!r}")
        L.append(f"  \\egpred{{{pos.x:.2f}}}{{{pos.y:.2f}}}{{{_tex_escape(label)}}}")

    # --- argument-order numerals (honour the DTO's order_label) -------------
    for lig in dto.ligature_paths:
        n = getattr(lig, "order_label", None)
        if n is None or len(lig.points) < 2:
            continue
        hook, nxt = lig.points[0], lig.points[1]
        dx, dy = nxt.x - hook.x, nxt.y - hook.y
        seg = (dx * dx + dy * dy) ** 0.5 or 1.0
        ux, uy = dx / seg, dy / seg
        lx = hook.x + ux * 15.0 - uy * 6.0
        ly = hook.y + uy * 15.0 + ux * 6.0
        L.append(f"  \\egnum{{{lx:.2f}}}{{{ly:.2f}}}{{{n}}}")

    L.append("\\end{tikzpicture}")
    body = "\n".join(L)

    return _wrap_document(body, standalone, document_class)


def _wrap_document(body: str, standalone: bool, document_class: str) -> str:
    if not standalone:
        return body

    if document_class == "article":
        opening = "\\documentclass{article}\n\\usepackage{tikz}\n"
        begin = "\\begin{document}\n\\thispagestyle{empty}\n\\noindent\n"
    else:
        opening = "\\documentclass[border=8pt]{standalone}\n\\usepackage{tikz}\n"
        begin = "\\begin{document}\n"
    return (
        f"{opening}"
        "\\makeatletter\n"
        f"{_macro_preamble()}\n"
        "\\makeatother\n"
        f"{begin}"
        f"{body}\n"
        "\\end{document}\n"
    )


def export_peirce_chain_document(figures, *, title=None, document_class: str = "article") -> str:
    """Assemble a **worked-chain** LaTeX document — a reasoning episode in print.

    ``figures`` is an ordered list of ``(tikz_body, caption_latex)`` pairs (each
    ``tikz_body`` from ``export_peirce_latex(..., standalone=False)``; each
    ``caption_latex`` already-formed LaTeX, e.g. a ``\\textbf{Step k …}`` line).
    The ``arisbe-eg`` macros are inlined once; every step is a centred figure
    captioned by the rule that produced it — Peirce's "moving picture of thought"
    laid out page by page for the Peirce Edition Project (the roadmap's "and
    likely a worked chain" clause).

    Defaults to the ``article`` class so the figures flow down the page (a
    multi-figure derivation, unlike a single cropped ``standalone`` graph).
    """
    parts = [f"\\documentclass{{{document_class}}}", "\\usepackage{tikz}",
             "\\makeatletter", _macro_preamble(), "\\makeatother",
             "\\begin{document}"]
    if title:
        parts.append(f"\\begin{{center}}\\Large {_tex_escape(title)}\\par\\end{{center}}")
        parts.append("\\medskip")
    for body, caption in figures:
        parts.append("\\begin{center}")
        parts.append(body)
        parts.append("\\end{center}")
        if caption:
            parts.append(f"\\noindent {caption}\\par\\medskip")
    parts.append("\\end{document}")
    return "\n".join(parts) + "\n"
