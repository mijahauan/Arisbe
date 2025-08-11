#!/usr/bin/env python3
import os
from typing import List, Tuple

from src.egif_parser_dau import parse_egif  # type: ignore
from src.graphviz_layout_engine_v2 import GraphvizLayoutEngine  # type: ignore

CASES: List[Tuple[str, str]] = [
    ("case1_single_cut", "~[]"),
    ("case2_sibling_cuts", "~[] ~[]"),
    ("case3_nested_double", "~[~[]]"),
    ("case4_nested_siblings", "~[~[] ~[]]"),
    ("case5_mixed_nesting", "~[ ~[] ~[ ~[] ~[] ] ]"),
]

def overlaps(a: Tuple[float,float,float,float], b: Tuple[float,float,float,float]) -> bool:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    return not (ax2 <= bx1 or bx2 <= ax1 or ay2 <= by1 or by2 <= ay1)

def test_canonical_cut_bounds_and_no_sibling_overlap():
    os.environ["ARISBE_CANONICAL"] = "1"
    engine = GraphvizLayoutEngine(mode="default-nopp")

    for name, egif in CASES:
        g = parse_egif(egif)
        layout = engine.create_layout_from_graph(g)

        # Collect cut primitives and containment
        cuts = {c.id for c in g.Cut}
        prims = layout.primitives
        # Build parent->children for cuts via g.area
        for parent_id, contents in g.area.items():
            # Only consider children that are cuts
            child_cuts = [cid for cid in contents if cid in cuts]
            # Sibling overlap check in raw coordinates (canonical mode preserves Graphviz bounds)
            for i in range(len(child_cuts)):
                for j in range(i+1, len(child_cuts)):
                    ci = child_cuts[i]
                    cj = child_cuts[j]
                    bi = prims[ci].bounds
                    bj = prims[cj].bounds
                    assert bi is not None and bj is not None
                    assert not overlaps(bi, bj), f"sibling overlap in {name}: {ci} vs {cj} with {bi} and {bj}"

        # Assert all cuts present with bounds
        for cid in cuts:
            assert cid in prims and prims[cid].bounds is not None, f"missing bounds for cut {cid} in {name}"
