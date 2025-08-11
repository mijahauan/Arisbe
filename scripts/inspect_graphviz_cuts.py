#!/usr/bin/env python3
"""
Inspect DOT cluster nesting vs xdot bbox containment for cut-only cases.
- Dumps DOT and xdot to out_debug/
- Parses DOT cluster nesting tree (canonical containment)
- Parses xdot cluster bboxes and computes bbox-based containment tree
- Compares both trees and prints discrepancies
"""
from __future__ import annotations
import os
import re
from typing import Dict, List, Tuple, Optional

from egif_parser_dau import parse_egif
from graphviz_layout_engine_v2 import GraphvizLayoutEngine
from xdot_parser_simple import parse_xdot_file

Case = Tuple[str, str]
CASES: List[Case] = [
    ("case4_nested_siblings", "~[~[] ~[]]"),
    ("case5_mixed_nesting", "~[ ~[] ~[ ~[] ~[] ] ]"),
]

# ---- DOT cluster tree parsing ----
class DotClusterNode:
    def __init__(self, name: str, span: Tuple[int,int]):
        self.name = name
        self.span = span
        self.children: List[DotClusterNode] = []
    def add(self, child: 'DotClusterNode'):
        self.children.append(child)
    def to_dict(self) -> Dict:
        return {self.name: [c.to_dict() for c in self.children]}

DOT_CLUSTER_RE = re.compile(r"subgraph\s+(cluster_[A-Za-z0-9_]+)\s*\{")

def _match_brace_span(s: str, open_pos: int) -> int:
    depth = 0
    i = open_pos
    while i < len(s):
        if s[i] == '{':
            depth += 1
        elif s[i] == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1

def parse_dot_cluster_tree(dot: str) -> DotClusterNode:
    # Find all cluster starts and their block spans
    clusters: List[Tuple[str,int,int]] = []  # (name, start_idx, end_idx)
    for m in DOT_CLUSTER_RE.finditer(dot):
        name = m.group(1)
        brace_open = dot.find('{', m.end()-1)
        if brace_open == -1:
            continue
        brace_close = _match_brace_span(dot, brace_open)
        if brace_close == -1:
            continue
        clusters.append((name, brace_open, brace_close))
    # Build nodes
    nodes = [DotClusterNode(name, (start, end)) for name, start, end in clusters]
    # Determine parents by span containment (smallest containing span)
    parent: Dict[int, Optional[int]] = {i: None for i in range(len(nodes))}
    for i, ni in enumerate(nodes):
        best_j = None
        best_len = None
        s_i, e_i = ni.span
        for j, nj in enumerate(nodes):
            if i == j:
                continue
            s_j, e_j = nj.span
            if s_j < s_i and e_i < e_j:
                span_len = e_j - s_j
                if best_len is None or span_len < best_len:
                    best_j = j
                    best_len = span_len
        parent[i] = best_j
    # Attach to build tree
    root = DotClusterNode("ROOT", (0,0))
    for i, node in enumerate(nodes):
        pj = parent[i]
        if pj is None:
            root.add(node)
        else:
            nodes[pj].add(node)
    return root

# ---- BBox containment tree ----
BBox = Tuple[float,float,float,float]

def normalize(b: BBox) -> BBox:
    x1,y1,x2,y2 = b
    if x1 > x2: x1,x2 = x2,x1
    if y1 > y2: y1,y2 = y2,y1
    return (x1,y1,x2,y2)

def contains(a: BBox, b: BBox, tol=1e-6) -> bool:
    ax1,ay1,ax2,ay2 = a
    bx1,by1,bx2,by2 = b
    return (bx1 > ax1 + tol) and (by1 > ay1 + tol) and (bx2 < ax2 - tol) and (by2 < ay2 - tol)

class BoxNode:
    def __init__(self, name: str, bb: BBox):
        self.name = name
        self.bb = normalize(bb)
        self.children: List['BoxNode'] = []
    def add(self, child: 'BoxNode'):
        self.children.append(child)
    def to_dict(self) -> Dict:
        return {self.name: [c.to_dict() for c in self.children]}

def build_bbox_tree(cluster_bbs: Dict[str, BBox]) -> BoxNode:
    # Create nodes
    nodes = {name: BoxNode(name, bb) for name, bb in cluster_bbs.items()}
    # Determine parents by strict containment choosing the smallest container
    names = list(nodes.keys())
    parent: Dict[str, Optional[str]] = {n: None for n in names}
    for n in names:
        bb = nodes[n].bb
        best: Optional[Tuple[str,float]] = None
        for m in names:
            if m == n:
                continue
            if contains(nodes[m].bb, bb):
                area = (nodes[m].bb[2]-nodes[m].bb[0])*(nodes[m].bb[3]-nodes[m].bb[1])
                if best is None or area < best[1]:
                    best = (m, area)
        parent[n] = best[0] if best else None
    # Attach
    root = BoxNode("ROOT", (0,0,0,0))
    for n in names:
        p = parent[n]
        if p is None:
            root.add(nodes[n])
        else:
            nodes[p].add(nodes[n])
    return root

# ---- main ----

def main(outdir: str = "out_debug") -> None:
    os.makedirs(outdir, exist_ok=True)
    engine = GraphvizLayoutEngine(mode="default-nopp")

    for name, egif in CASES:
        print(f"\n=== {name} ===")
        g = parse_egif(egif)
        # Access internal steps to dump DOT and xdot
        dot = engine._generate_dot_from_egi(g)  # type: ignore
        xdot = engine._execute_graphviz(dot)    # type: ignore
        with open(os.path.join(outdir, f"{name}.dot"), "w", encoding="utf-8") as f:
            f.write(dot)
        with open(os.path.join(outdir, f"{name}.xdot"), "w", encoding="utf-8") as f:
            f.write(xdot)
        print(f"  wrote DOT and xdot to {outdir}/")

        # Parse DOT cluster tree
        dot_tree = parse_dot_cluster_tree(dot)
        # Parse xdot cluster bboxes
        clusters, _, _ = parse_xdot_file(xdot)
        bb_map: Dict[str,BBox] = {c.name: c.bb for c in clusters}
        box_tree = build_bbox_tree(bb_map)

        print("  DOT cluster tree:")
        print(f"    {dot_tree.to_dict()}")
        print("  BBox containment tree:")
        print(f"    {box_tree.to_dict()}")

    print("\nDone.")

if __name__ == "__main__":
    main()
