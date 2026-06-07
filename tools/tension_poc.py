#!/usr/bin/env python3
"""
Tension layout — proof of concept (docs/TENSION_LAYOUT.md §8).

Tests the smallest concrete claim: that minimizing *ligature tension* picks the
readable arrangement of a layout's **free** choices — here, the left-to-right
order of an area's sibling blocks (the open `sibling_cut_ordering` convention) —
and that doing so has **zero** effect on the correspondence invariant.

This is a STRUCTURAL sketch: no geometry, no solver.  A "block" is a direct
child of a chosen area (a sub-cut, vertex, or predicate); each deeper element
belongs to the top-level block that contains it.  A "spring" is one
predicate–vertex incidence (from `ν`).  For a 1-D ordering of the blocks,

    tension(order) = Σ over intra-area springs  |pos[block(u)] − pos[block(v)]|

We find the tension-minimizing order (brute force for few blocks; a barycenter
sweep otherwise) and compare it to the baseline (id) order.

The invariant check is the point: every ligature's crossing-sequence is computed
from the area tree alone (`presentation_ops.crossing_sequence`), so it is
identical under *every* ordering — tension optimizes the free projection
dimension while the §3.3 homotopy class never moves.

Usage:
    uv run python tools/tension_poc.py            # constructed + a tomos example
    uv run python tools/tension_poc.py <uod_id>   # a specific corpus UoD
"""

import sys
from itertools import permutations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from egif_parser_dau import parse_egif
from presentation_ops import element_area, cut_parents, crossing_sequence
from tension_layout import springs, block_of, tension, optimize_order
from tomos_service import TomosService


# --------------------------------------------------------------------------- #
# Driver                                                                      #
# --------------------------------------------------------------------------- #


def _label(egi, eid):
    """A short human label for an element id."""
    for e in egi.E:
        if e.id == eid:
            return f"({egi.get_relation_name(eid)})"
    for v in egi.V:
        if v.id == eid:
            return f"•{v.label}" if v.label else "•"
    if any(c.id == eid for c in egi.Cut):
        return "~[…]"
    return eid[:8]


def best_area(egi):
    """Pick the area with the most direct children that also carries cross-block
    springs — the most interesting place to order."""
    elem_area = element_area(egi)
    parent_map = cut_parents(egi)
    sp = springs(egi)
    best, best_score = None, -1
    for area in list(egi.area.keys()):
        blocks = list(egi.area.get(area, frozenset()))
        if len(blocks) < 2:
            continue
        cross = 0
        for e, v in sp:
            bu, bv = block_of(e, area, elem_area, parent_map), block_of(v, area, elem_area, parent_map)
            if bu is not None and bv is not None and bu != bv:
                cross += 1
        score = len(blocks) * 100 + cross
        if cross > 0 and score > best_score:
            best, best_score = area, score
    return best


def report(title, egi, area=None):
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")
    elem_area = element_area(egi)
    parent_map = cut_parents(egi)
    sp = springs(egi)

    if area is None:
        area = best_area(egi)
    if area is None:
        print("  (no area with ≥2 connected sibling blocks — nothing to order)")
        return

    blocks = list(egi.area.get(area, frozenset()))
    area_name = "sheet" if area == egi.sheet else f"cut {area[:8]}"
    print(f"Ordering the {len(blocks)} blocks of {area_name}:")
    for b in blocks:
        print(f"    {_label(egi, b):10}  [{b[:8]}]")

    intra = []
    for e, v in sp:
        bu = block_of(e, area, elem_area, parent_map)
        bv = block_of(v, area, elem_area, parent_map)
        if bu is not None and bv is not None and bu != bv:
            intra.append((bu, bv))
    print(f"\nIntra-area springs (cross-block lines of identity): {len(intra)}")

    base = list(blocks)
    opt = optimize_order(blocks, intra)
    tb, to = tension(base, intra), tension(opt, intra)

    # For a small area, also report the WORST order so the spread is visible —
    # tension must *discriminate* orderings for it to be an organizing signal.
    worst = None
    if len(blocks) <= 8:
        worst = max(permutations(blocks), key=lambda o: tension(o, intra))
        tw = tension(worst, intra)

    print(f"\n  stored order   : {[_label(egi, b) for b in base]}  → tension {tb:.0f}")
    if worst is not None:
        print(f"  worst order    : {[_label(egi, b) for b in worst]}  → tension {tw:.0f}")
    print(f"  tension-min    : {[_label(egi, b) for b in opt]}  → tension {to:.0f}")
    if worst is not None and tw > to:
        print(f"  → tension spans {to:.0f}..{tw:.0f} across orderings; the minimum"
              f" clusters connected blocks adjacent.")
    if tb > to:
        print(f"  → reorders the stored layout, cutting tension {100*(tb-to)/tb:.0f}%.")

    # Invariant check: crossing-sequences are a function of the area tree only.
    cs = {}
    for e, v in sp:
        cs[(e, v)] = crossing_sequence(elem_area.get(e), elem_area.get(v), parent_map)
    n_crossing = sum(1 for seq in cs.values() if seq)
    print(f"\n  invariant: {len(cs)} ligatures, {n_crossing} cross ≥1 cut.")
    print(f"  every crossing-sequence is computed from the area tree alone —")
    print(f"  identical under EVERY ordering. Tension touches the free dimension")
    print(f"  only; the §3.3 homotopy class never moves.")


def main():
    # 1. Constructed: two identity clusters that should separate.  x ties
    #    A,B,E together; y ties C,D,F together — a readable layout keeps each
    #    cluster contiguous, an unreadable one interleaves them.
    egi = parse_egif("(A *x) (B x) (C *y) (D y) (E x) (F y)")
    report("Constructed: two clusters — x:{A,B,E}  y:{C,D,F}", egi, egi.sheet)

    # 2. A real corpus UoD (default has orderable sibling structure).
    svc = TomosService(Path(__file__).resolve().parent.parent / "tomos")
    uod_id = sys.argv[1] if len(sys.argv) > 1 else "sowa_cat_on_mat"
    u = svc.load_uod(uod_id)
    if u is None:
        print(f"\n(could not load UoD '{uod_id}')")
        return
    report(f"Corpus UoD: {uod_id}", u.current_egi)


if __name__ == "__main__":
    main()
