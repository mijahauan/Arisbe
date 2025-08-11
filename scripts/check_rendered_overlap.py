#!/usr/bin/env python3
from __future__ import annotations
from typing import Tuple, Dict, List

from egif_parser_dau import parse_egif
from graphviz_layout_engine_v2 import GraphvizLayoutEngine
from renderer_minimal_dau import transformed_bounds_map

CASES = [
    ("case4_nested_siblings", "~[~[] ~[]]"),
    ("case5_mixed_nesting", "~[ ~[] ~[ ~[] ~[] ] ]"),
]

def overlap(a: Tuple[float,float,float,float], b: Tuple[float,float,float,float], tol: float=0.0) -> bool:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    # Strict overlap (positive area intersection)
    return (min(ax2, bx2) - max(ax1, bx1) > tol) and (min(ay2, by2) - max(ay1, by1) > tol)

# Build simple parent map from layout.areas (if present) else fallback to bbox containment

def contains(a, b, tol=1e-6):
    ax1,ay1,ax2,ay2 = a
    bx1,by1,bx2,by2 = b
    return (bx1 > ax1 + tol) and (by1 > ay1 + tol) and (bx2 < ax2 - tol) and (by2 < ay2 - tol)

if __name__ == "__main__":
    eng = GraphvizLayoutEngine(mode="default-nopp")
    for name, egif in CASES:
        print(f"\n{name}")
        g = parse_egif(egif)
        layout = eng.create_layout_from_graph(g)
        print(f"world canvas_bounds={layout.canvas_bounds}")
        raw_cuts = {k: v.bounds for k, v in layout.primitives.items() if k.startswith('c_')}
        for k,v in raw_cuts.items():
            print(f"  raw {k}: {v}")
        tb = transformed_bounds_map(layout, canvas_px=(800,600))
        # Parent inference by bbox containment on transformed space
        ids = [k for k in tb.keys() if k.startswith('c_')]
        parent = {k: None for k in ids}
        for i in ids:
            bi = tb[i]
            best = None
            best_area = None
            for j in ids:
                if i == j: continue
                bj = tb[j]
                if contains(bj, bi):
                    area = (bj[2]-bj[0])*(bj[3]-bj[1])
                    if best_area is None or area < best_area:
                        best, best_area = j, area
            parent[i] = best
        # Group siblings by parent
        groups: Dict[str, List[str]] = {}
        for cid, p in parent.items():
            groups.setdefault(p or "<root>", []).append(cid)
        # Test overlaps among siblings
        for p, kids in groups.items():
            if len(kids) < 2:
                continue
            print(f"  parent {p}: {kids}")
            for i in range(len(kids)):
                for j in range(i+1, len(kids)):
                    ci, cj = kids[i], kids[j]
                    oi = overlap(tb[ci], tb[cj], tol=0.5)
                    print(f"    overlap({ci}, {cj}) -> {oi}  {tb[ci]} vs {tb[cj]}")
