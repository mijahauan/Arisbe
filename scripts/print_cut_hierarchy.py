#!/usr/bin/env python3
from __future__ import annotations
from typing import Dict, Optional, Tuple

from egif_parser_dau import parse_egif
from graphviz_layout_engine_v2 import GraphvizLayoutEngine
from xdot_parser_simple import parse_xdot_file

def contains(a, b, tol=1e-6):
    ax1,ay1,ax2,ay2 = a
    bx1,by1,bx2,by2 = b
    return (bx1 > ax1 + tol) and (by1 > ay1 + tol) and (bx2 < ax2 - tol) and (by2 < ay2 - tol)

def cut_parent_map(egif: str) -> Dict[str, Optional[str]]:
    g = parse_egif(egif)
    eng = GraphvizLayoutEngine(mode="default-nopp")
    dot = eng._generate_dot_from_egi(g)  # type: ignore
    xdot = eng._execute_graphviz(dot)    # type: ignore
    clusters, _, _ = parse_xdot_file(xdot)
    bb = {c.name: c.bb for c in clusters}
    ids = list(bb.keys())
    parent: Dict[str, Optional[str]] = {k: None for k in ids}
    for i in ids:
        best = None
        best_area = None
        bi = bb[i]
        for j in ids:
            if i == j: continue
            bj = bb[j]
            if contains(bj, bi):
                area = (bj[2]-bj[0])*(bj[3]-bj[1])
                if best_area is None or area < best_area:
                    best, best_area = j, area
        parent[i] = best
    return parent

if __name__ == "__main__":
    cases = [
        ("case4_nested_siblings", "~[~[] ~[]]"),
        ("case5_mixed_nesting", "~[ ~[] ~[ ~[] ~[] ] ]"),
    ]
    for name, egif in cases:
        print(f"\n{name}")
        pm = cut_parent_map(egif)
        for k, v in pm.items():
            print(f"  {k} -> {v}")
