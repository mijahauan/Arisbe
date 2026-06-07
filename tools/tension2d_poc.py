#!/usr/bin/env python3
"""
Tension-driven 2-D placement — proof of concept (docs/TENSION_LAYOUT.md).

The readability target: the Peircean *single-line reading* where a relation sits
**between** its argument vertices — ``Cat —•— On —•— Mat`` — instead of ELK's
bipartite two-column split (predicates in one column, line-of-identity dots in
the next).

The mechanism: treat the incidence graph (predicates + vertices as nodes, one
spring per ``ν`` incidence as an edge) and place it by **stress majorization**
(SMACOF) — the exact "minimize ligature tension" energy
``Σ w_ij (‖p_i − p_j‖ − d_ij)²`` with ideal distances ``d_ij`` = graph distance,
``w_ij = 1/d_ij²``.  A path lays out as a straight line in order; a star as a
hub — both readable.  No scipy (pure numpy), deterministic init.

This PoC is positions-only and **unconstrained** — it deliberately ignores cut
containment so we can see (a) the clean win on the cut-free ``cat_on_mat`` and
(b) honestly, the containment violation on a graph *with* cuts that the real,
constrained version must fix.

Usage:  uv run python tools/tension2d_poc.py
"""

import collections
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from egif_parser_dau import parse_egif
from elk_layout_engine import ELKLayoutEngine
from presentation_ops import element_area, deepest_containing_cut
from style_loader import load_default_style
from tension_layout import springs, stress_majorize
from tomos_service import TomosService


def stress_layout(nodes, edges, iters=400):
    """Thin wrapper over the shared ``tension_layout.stress_majorize`` (single
    source of truth), returning numpy arrays for this tool's analysis."""
    return {u: np.array(p) for u, p in
            stress_majorize(nodes, edges, iters=iters).items()}


def _names(egi):
    nm = {}
    for e in egi.E:
        nm[e.id] = egi.get_relation_name(e.id)
    for v in egi.V:
        nm[v.id] = "•"
    return nm


def _total_tension(pos, edges):
    """Σ straight-line length over the springs (the tension we minimize)."""
    return float(sum(np.linalg.norm(np.asarray(pos[a]) - np.asarray(pos[b]))
                     for a, b in edges))


def report_clean(uid_or_egif, title):
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")
    if uid_or_egif.startswith("(") or uid_or_egif.startswith("~"):
        egi = parse_egif(uid_or_egif)
    else:
        egi = TomosService(Path(__file__).resolve().parent.parent / "tomos") \
            .load_uod(uid_or_egif).current_egi

    nm = _names(egi)
    nodes = list(nm)
    edges = springs(egi)

    # ELK (the current engine) — show the two-column split.
    elk = ELKLayoutEngine().generate_layout(egi, load_default_style())
    elk_pos = {**{k: (p.x, p.y) for k, p in elk.vertex_positions.items()},
               **{k: (p.x, p.y) for k, p in elk.predicate_positions.items()}}
    pred_xs = sorted({round(p.x, 1) for p in elk.predicate_positions.values()})
    vert_xs = sorted({round(p.x, 1) for p in elk.vertex_positions.values()})
    print(f"ELK columns — predicate x's {pred_xs}, vertex x's {vert_xs}")
    print(f"ELK total tension (Σ line length) = {_total_tension(elk_pos, edges):.1f}")

    # Stress (tension-driven 2-D).
    sp = stress_layout(nodes, edges)
    P = np.array([sp[u] for u in nodes])
    P = P - P.mean(0)
    axis = np.linalg.svd(P)[2][0]
    order = sorted(range(len(nodes)), key=lambda i: float(P[i] @ axis))
    line = " ".join(nm[nodes[i]] for i in order)
    # Scale stress (unit-ish) up to ELK's scale for a comparable tension number.
    span = (P @ axis).ptp() or 1.0
    scale = (max(pred_xs + vert_xs) - min(pred_xs + vert_xs)) / span
    st_pos = {u: sp[u] * scale for u in nodes}
    print(f"\nstress (tension-2D) reading order: {line}")
    print(f"stress total tension (scaled)     = {_total_tension(st_pos, edges):.1f}")

    # Readability check: is each binary relation between its two arguments?
    proj = {nodes[i]: float(P[i] @ axis) for i in range(len(nodes))}
    for e in egi.E:
        vs = list(egi.nu.get(e.id, ()))
        if len(vs) == 2:
            a, b, r = proj[vs[0]], proj[vs[1]], proj[e.id]
            between = (a - r) * (b - r) < 0
            print(f"  relation {nm[e.id]!r} between its arguments: "
                  f"{'YES' if between else 'no'}")


def report_containment_gap(uid):
    print(f"\n{'=' * 70}\nContainment gap (honest): {uid}\n{'=' * 70}")
    svc = TomosService(Path(__file__).resolve().parent.parent / "tomos")
    egi = svc.load_uod(uid).current_egi
    if not egi.Cut:
        print("  (no cuts)"); return
    nm = _names(egi)
    nodes = list(nm)
    sp = stress_layout(nodes, springs(egi))
    # Lay the cuts' bounds out by ELK just to *test* containment of stress points.
    elk = ELKLayoutEngine().generate_layout(egi, load_default_style())
    ea = element_area(egi)
    cut_ids = {c.id for c in egi.Cut}
    # Scale stress into the ELK viewport for a fair containment test.
    P = np.array([sp[u] for u in nodes]); P -= P.min(0)
    vb = elk.viewport_bounds
    P = P / (P.max(0) + 1e-9) * np.array([vb.max_x - vb.min_x, vb.max_y - vb.min_y])
    from layout_dto import Point
    inside = outside = 0
    for i, u in enumerate(nodes):
        area = ea.get(u)
        if area in cut_ids:
            # Is the stress point actually inside its required cut? (Using ELK's
            # cut bounds purely as a yardstick — the stress layout never made any.)
            pt = Point(P[i][0] + vb.min_x, P[i][1] + vb.min_y)
            got = deepest_containing_cut(pt, elk, egi)
            (inside := inside + 1) if got == area else (outside := outside + 1)
    print(f"  elements that must sit inside a cut: {inside + outside}")
    print(f"  unconstrained stress places OUTSIDE their cut: {outside}")
    print("  → pure stress ignores containment; the real version must constrain")
    print("    each point to its area (hierarchical / projected SMACOF). This is")
    print("    the §3.3-preserving work the wiring needs — see the plan.")


def main():
    report_clean("(Cat *x) (On x *y) (Mat y)", "cat on mat — the target reading")
    report_clean("sowa_cat_on_mat", "Corpus: sowa_cat_on_mat")
    report_containment_gap("peirce_modus_ponens")


if __name__ == "__main__":
    main()
