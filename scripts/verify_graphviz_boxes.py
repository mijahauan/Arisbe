#!/usr/bin/env python3
"""
Verify that raw Graphviz (no post-processing) produces strict boxes-in-boxes for reference cut-only cases.
Checks:
- For each parent/child, child strictly inside parent (no touching edges)
- For siblings, no overlap and positive gap
"""
from typing import List, Tuple

from egif_parser_dau import parse_egif
from graphviz_layout_engine_v2 import GraphvizLayoutEngine

CASES: List[Tuple[str, str]] = [
    ("case1_single_cut", "~[]"),
    ("case2_sibling_cuts", "~[] ~[]"),
    ("case3_nested_double", "~[~[]]"),
    ("case4_nested_siblings", "~[~[] ~[]]"),
    ("case5_mixed_nesting", "~[ ~[] ~[ ~[] ~[] ] ]"),
]

def contains(bbig, bsmall, tol=1e-6):
    X1,Y1,X2,Y2 = bbig
    x1,y1,x2,y2 = bsmall
    return (x1 > X1 + tol) and (y1 > Y1 + tol) and (x2 < X2 - tol) and (y2 < Y2 - tol)

def overlaps(a, b, tol=1e-6):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix = max(0.0, min(ax2, bx2) - max(ax1, bx1))
    iy = max(0.0, min(ay2, by2) - max(ay1, by1))
    return (ix > tol) and (iy > tol)

def normalize(b):
    x1,y1,x2,y2 = b
    if x1 > x2: x1,x2 = x2,x1
    if y1 > y2: y1,y2 = y2,y1
    return (x1,y1,x2,y2)

def verify_case(name: str, egif: str) -> None:
    print(f"- {name}: {egif}")
    g = parse_egif(egif)
    engine = GraphvizLayoutEngine(mode="default-nopp")
    layout = engine.create_layout_from_graph(g)
    # Extract cuts and normalize bounds ordering
    cuts = []
    for c in g.Cut:
        spr = layout.primitives.get(c.id)
        if spr and spr.bounds:
            cuts.append((c.id, normalize(spr.bounds)))
    # Sort by area asc
    cuts.sort(key=lambda t: (t[1][2]-t[1][0])*(t[1][3]-t[1][1]))
    # Parent assignment by center-in-rect among larger cuts
    parents = {}
    for i,(cid, cb) in enumerate(cuts):
        cx, cy = (cb[0]+cb[2])/2.0, (cb[1]+cb[3])/2.0
        parent = None
        for j in range(i+1, len(cuts)):
            pid, pb = cuts[j]
            if pb[0] < cx < pb[2] and pb[1] < cy < pb[3]:
                parent = pid
                break
        parents[cid] = parent
    # Check containment strictness and sibling non-overlap
    ok = True
    # Containment
    id_to_bounds = dict(cuts)
    for cid, pid in parents.items():
        if pid is None:
            continue
        if not contains(id_to_bounds[pid], id_to_bounds[cid]):
            print(f"  ❌ Containment fail: child {cid} {id_to_bounds[cid]} not strictly inside parent {pid} {id_to_bounds[pid]}")
            ok = False
    # Siblings
    by_parent = {}
    for cid, pid in parents.items():
        by_parent.setdefault(pid, []).append(cid)
    for pid, lst in by_parent.items():
        for i in range(len(lst)):
            for j in range(i+1, len(lst)):
                a = id_to_bounds[lst[i]]; b = id_to_bounds[lst[j]]
                if overlaps(a, b):
                    print(f"  ❌ Sibling overlap: {lst[i]} {a} vs {lst[j]} {b} under parent {pid}")
                    ok = False
    if ok:
        print("  ✅ Raw Graphviz cuts are strictly nested with no sibling overlap.")

if __name__ == "__main__":
    for name, egif in CASES:
        verify_case(name, egif)
    print("Done.")
