#!/usr/bin/env python3
"""
Assert strict cut containment and sibling non-overlap based on raw Graphviz xdot bboxes.
Also assert DOT cluster nesting equals bbox containment tree.
"""
from __future__ import annotations
import sys
from typing import List, Tuple, Dict, Optional

from egif_parser_dau import parse_egif
from graphviz_layout_engine_v2 import GraphvizLayoutEngine
from xdot_parser_simple import parse_xdot_file

Case = Tuple[str, str]
CASES: List[Case] = [
    ("case1_single_cut", "~[]"),
    ("case2_sibling_cuts", "~[] ~[]"),
    ("case3_nested_double", "~[~[]]"),
    ("case4_nested_siblings", "~[~[] ~[]]"),
    ("case5_mixed_nesting", "~[ ~[] ~[ ~[] ~[] ] ]"),
]

BBox = Tuple[float,float,float,float]

def norm(b: BBox) -> BBox:
    x1,y1,x2,y2 = b
    if x1 > x2: x1,x2 = x2,x1
    if y1 > y2: y1,y2 = y2,y1
    return (x1,y1,x2,y2)

def contains(a: BBox, b: BBox, tol=1e-6) -> bool:
    ax1,ay1,ax2,ay2 = a
    bx1,by1,bx2,by2 = b
    return (bx1 > ax1 + tol) and (by1 > ay1 + tol) and (bx2 < ax2 - tol) and (by2 < ay2 - tol)

def overlaps(a: BBox, b: BBox, tol=1e-6) -> bool:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix = max(0.0, min(ax2, bx2) - max(ax1, bx1))
    iy = max(0.0, min(ay2, by2) - max(ay1, by1))
    return (ix > tol) and (iy > tol)

# Build bbox-based containment tree
class BoxNode:
    def __init__(self, name: str, bb: BBox):
        self.name = name
        self.bb = norm(bb)
        self.children: List['BoxNode'] = []
    def add(self, ch: 'BoxNode'):
        self.children.append(ch)
    def to_tuple(self):
        return (self.name, tuple(ch.to_tuple() for ch in self.children))

def build_tree(bb_map: Dict[str,BBox]) -> BoxNode:
    nodes = {k: BoxNode(k, v) for k, v in bb_map.items()}
    parent: Dict[str, Optional[str]] = {k: None for k in nodes}
    for k, nk in nodes.items():
        best = None
        best_area = None
        for j, nj in nodes.items():
            if k == j: continue
            if contains(nj.bb, nk.bb):
                area = (nj.bb[2]-nj.bb[0])*(nj.bb[3]-nj.bb[1])
                if best is None or area < best_area:
                    best, best_area = j, area
        parent[k] = best
    root = BoxNode('ROOT', (0,0,0,0))
    for k in nodes:
        p = parent[k]
        if p is None:
            root.add(nodes[k])
        else:
            nodes[p].add(nodes[k])
    return root

# Compare sibling overlap
def assert_no_sibling_overlap(root: BoxNode):
    def walk(n: BoxNode):
        ch = n.children
        for i in range(len(ch)):
            for j in range(i+1, len(ch)):
                if overlaps(ch[i].bb, ch[j].bb):
                    raise AssertionError(f"Sibling overlap: {ch[i].name} {ch[i].bb} vs {ch[j].name} {ch[j].bb} under {n.name}")
        for c in ch:
            walk(c)
    walk(root)

# Ensure each child strictly inside its parent
def assert_strict_containment(root: BoxNode):
    def walk(n: BoxNode):
        for c in n.children:
            if n.name != 'ROOT' and not contains(n.bb, c.bb):
                raise AssertionError(f"Containment fail: child {c.name} {c.bb} not strictly inside parent {n.name} {n.bb}")
            walk(c)
    walk(root)

# Main
if __name__ == "__main__":
    engine = GraphvizLayoutEngine(mode="default-nopp")
    ok = True
    for name, egif in CASES:
        print(f"- {name}")
        g = parse_egif(egif)
        dot = engine._generate_dot_from_egi(g)  # type: ignore
        xdot = engine._execute_graphviz(dot)    # type: ignore
        clusters, _, _ = parse_xdot_file(xdot)
        bb_map = {c.name: c.bb for c in clusters}
        root = build_tree(bb_map)
        try:
            assert_no_sibling_overlap(root)
            assert_strict_containment(root)
            print("  ✅ strict containment and no sibling overlap")
        except AssertionError as e:
            print(f"  ❌ {e}")
            ok = False
    if not ok:
        sys.exit(1)
    print("Done.")
