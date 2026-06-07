#!/usr/bin/env python3
"""
Thread-layout PoC (docs/TENSION_LAYOUT.md) — lay the *line of identity* as the
primary object: one taut thread through the nested cuts, predicates hung on it,
instead of placing predicates/vertices as independent nodes.

The insight (from dau_theorem_proving): its graph is a single chain
``P — x — Q — y — R — z — S`` threading 5 nested cuts.  Laying that chain along
one axis, with each cut a box around its contiguous run of the thread, makes the
whole line of identity **collinear** — straight through every predicate, vertex,
and cut-crossing — which node placement (ELK columns / tension stars) can't give.

Scope: a *single monotone thread* (every element degree ≤ 2; depth non-decreasing
along the thread — the dau_theorem_proving shape).  Branches / non-monotone
threads are the generalization, noted at the end.  This is positions-only; it
builds a LayoutDTO, attests §3.3, and renders an SVG to compare with ELK.

    uv run python tools/thread_layout_poc.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tomos_service import TomosService
from elk_layout_engine import ELKLayoutEngine
from simple_svg_renderer import SimpleSVGRenderer
from egif_generator_dau import EGIFGenerator
from layout_dto import LayoutDTO, BoundingBox, LigaturePath, Point
from style_loader import load_style, load_default_style
from presentation_ops import element_area, cut_parents, crossing_sequence
from correspondence_attestation import attest_correspondence, CorrespondenceViolation

STEP = 90.0   # spacing between consecutive thread elements
PAD = 22.0    # nesting inset per cut level
ROWH = 26.0   # half-height of the innermost band


def extract_thread(egi):
    """Return the ordered element chain of a single degree-≤2 ligature:
    [pred, vertex, pred, vertex, …].  Walk from a degree-1 endpoint."""
    inc = {}  # element -> set of incident elements (pred<->vertex)
    for e in egi.E:
        for v in egi.nu.get(e.id, ()):
            inc.setdefault(e.id, []).append(v)
            inc.setdefault(v, []).append(e.id)
    if any(len(ns) > 2 for ns in inc.values()):
        raise ValueError("not a simple thread (a vertex/predicate has degree > 2)")
    ends = [n for n, ns in inc.items() if len(ns) == 1]
    if not ends:
        raise ValueError("no degree-1 endpoint (cycle?)")
    start = min(ends)  # deterministic
    order, prev, cur = [start], None, start
    while True:
        nxts = [n for n in inc[cur] if n != prev]
        if not nxts:
            break
        prev, cur = cur, nxts[0]
        order.append(cur)
    return order


def thread_layout(egi, style):
    ea = element_area(egi)
    pm = cut_parents(egi)
    cut_ids = {c.id for c in egi.Cut}
    edge_ids = {e.id for e in egi.E}
    sizes = ELKLayoutEngine()._compute_element_sizes(egi, style)

    thread = extract_thread(egi)
    idx = {eid: i for i, eid in enumerate(thread)}

    # 1. Place the thread collinear: x by order, y = 0.
    vpos, ppos = {}, {}
    for eid in thread:
        p = Point(idx[eid] * STEP, 0.0)
        (ppos if eid in edge_ids else vpos)[eid] = p

    # 2. Cut boxes bottom-up: each cut bounds its direct children + inset, so
    #    nesting holds by construction and the cuts telescope along the thread.
    def depth(a):
        d, cur = 0, a
        while cur in pm and pm[cur] is not None:
            d += 1; cur = pm[cur]
        return d

    cbounds = {}
    def box(cid):
        if cid in cbounds:
            return cbounds[cid]
        xs, ys = [], []
        for child in egi.area.get(cid, ()):
            if child in cut_ids:
                b = box(child)
                xs += [b.min_x, b.max_x]; ys += [b.min_y, b.max_y]
            else:
                p = vpos.get(child) or ppos.get(child)
                if p is None:
                    continue
                w, h = sizes.get(child, (10.0, 10.0))
                xs += [p.x - w / 2, p.x + w / 2]; ys += [p.y - h / 2, p.y + h / 2]
        if not xs:
            xs, ys = [0.0], [0.0]
        b = BoundingBox(min(xs) - PAD, min(ys) - ROWH - PAD,
                        max(xs) + PAD, max(ys) + ROWH + PAD)
        cbounds[cid] = b
        return b
    for c in egi.Cut:
        box(c.id)

    # 3. Ligature paths: each incidence is a segment along the thread, with a
    #    crossing point on each cut boundary it must pass (y = 0 → all collinear).
    paths = []
    hook = ELKLayoutEngine._predicate_hook_point
    for e in egi.E:
        if e.id not in ppos:
            continue
        pc = ppos[e.id]
        pw, ph = sizes.get(e.id, (40.0, 18.0))
        for port, v in enumerate(egi.nu.get(e.id, ())):
            if v not in vpos:
                continue
            vp = vpos[v]
            seq = crossing_sequence(ea.get(e.id), ea.get(v), pm)
            # Each crossed cut: the thread (horizontal) meets its near vertical
            # edge between the predicate and vertex x's, at y = 0.
            lo, hi = sorted((pc.x, vp.x))
            mids = []
            for c in seq:
                b = cbounds[c]
                edge = b.min_x if abs(b.min_x - lo) < abs(b.max_x - lo) else b.max_x
                edge = min(max(edge, lo), hi)
                mids.append(Point(edge, 0.0))
            mids.sort(key=lambda p: abs(p.x - pc.x))
            h = hook(pc, pw, ph, mids[0] if mids else vp)
            pts = [h] + mids + [vp]
            paths.append(LigaturePath(e.id, v, tuple(pts), port))

    allx = [p.x for p in list(vpos.values()) + list(ppos.values())]
    ally = [p.y for p in list(vpos.values()) + list(ppos.values())]
    for b in cbounds.values():
        allx += [b.min_x, b.max_x]; ally += [b.min_y, b.max_y]
    vb = BoundingBox(min(allx) - 40, min(ally) - 40, max(allx) + 40, max(ally) + 40)
    return LayoutDTO(
        vertex_positions=vpos, predicate_positions=ppos, cut_bounds=cbounds,
        ligature_paths=paths, area_hierarchy={a: set(c) for a, c in egi.area.items()},
        viewport_bounds=vb, sheet_id=egi.sheet, style=style,
    )


def main():
    svc = TomosService(Path(__file__).resolve().parent.parent / "tomos")
    egi = svc.load_uod("dau_theorem_proving").current_egi
    thread = extract_thread(egi)
    nm = {}
    for e in egi.E: nm[e.id] = egi.get_relation_name(e.id)
    for v in egi.V: nm[v.id] = "•"
    print("thread:", " — ".join(nm.get(t, t[:4]) for t in thread))

    for style_name, style in [("dau", load_default_style()),
                              ("peirce", load_style("peirce-authentic@1.0"))]:
        dto = thread_layout(egi, style)
        # collinearity: all thread elements share y
        ys = {round(p.y, 3) for p in list(dto.vertex_positions.values())
              + list(dto.predicate_positions.values())}
        try:
            attest_correspondence(egi, dto, context="thread_poc")
            attested = "YES"
        except CorrespondenceViolation as exc:
            attested = "NO — " + str(exc).split("\n")[1].strip()
        egif = EGIFGenerator(egi).generate()
        svg = SimpleSVGRenderer().render_to_svg(dto, egif=egif, egi=egi)
        out = Path(f"/tmp/thread_dau_{style_name}.svg")
        out.write_text(svg)
        print(f"[{style_name}] collinear (one y): {len(ys) == 1} (ys={ys});  "
              f"§3.3 attests: {attested}")
        print(f"        wrote {out}")


if __name__ == "__main__":
    main()
