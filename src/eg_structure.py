"""
Coordinate-free structural summary of an EGI — the shared foundation for the
adaptive-scope viewer projection spike (`docs/ADAPTIVE_SCOPE_SPIKE.md`).

Every candidate projection (zoomable circle-packing, 3-D nested shells, hyperbolic
focus+context) is a different *realization* of the same projection-independent facts.
This module emits those facts as plain JSON: the containment tree + polarity, recursive
content counts per area, the predicate/vertex inventory, and the per-ligature **required
crossing-sequence** (the homotopy class that lets any projection route a line across cut
boundaries correctly). It reuses `natural_layout` (the "own the dimensionality" layer) and
`eg_navigation`; it holds **no geometry** and **never mutates** the EGI.

Crucially it is **O(n), not geometric** — no layout engine runs — so it returns the
250-cut SUMO taxonomy that chokes ELK (≈74 s) in milliseconds. That is exactly the
perf-frontier case the spike needs to exercise.
"""

from __future__ import annotations

from typing import Dict, Optional

import eg_navigation as nav
from egi_core_dau import ElementID, RelationalGraphWithCuts
from natural_layout import natural_layout


def subtree_summary(egi: RelationalGraphWithCuts, area_id: ElementID) -> Dict[str, int]:
    """Recursive count of everything strictly inside ``area_id`` — the badge a
    collapsed cut would show. Built on ``eg_navigation`` child enumeration."""
    cuts = nav.child_cuts(egi, area_id)
    total = {
        "cuts": len(cuts),
        "vertices": len(nav.child_vertices(egi, area_id)),
        "predicates": len(nav.child_edges(egi, area_id)),
    }
    for c in cuts:
        sub = subtree_summary(egi, c)
        total["cuts"] += sub["cuts"]
        total["vertices"] += sub["vertices"]
        total["predicates"] += sub["predicates"]
    return total


def egi_structure(egi: RelationalGraphWithCuts) -> dict:
    """The full coordinate-free structure of ``egi`` as JSON-serializable dict.

    Keys: ``sheet``, ``areas`` (sheet + every cut, each with parent / polarity /
    direct child cuts / recursive ``summary``), ``vertices``, ``predicates``,
    ``ligatures`` (each with its required ``crossings`` sequence), and ``counts``.
    """
    nl = natural_layout(egi)
    area_ids = [egi.sheet] + [c.id for c in egi.Cut]

    def area_depth(a: ElementID) -> int:
        """Negation depth of an area: cuts crossed from the sheet (sheet = 0)."""
        d, cur = 0, a
        while cur is not None and cur != egi.sheet:
            cur = nl.cut_parent.get(cur)
            d += 1
        return d

    areas = []
    for a in area_ids:
        is_cut = a != egi.sheet
        depth = area_depth(a)
        areas.append({
            "id": a,
            "kind": "cut" if is_cut else "sheet",
            "parent": nl.cut_parent.get(a),                  # None for the sheet
            "depth": depth,                                  # z-axis / nesting level
            # Peirce's recto/verso: odd negation depth is a denial (negative).
            "polarity": "negative" if depth % 2 == 1 else "positive",
            "child_cuts": nav.child_cuts(egi, a),
            "summary": subtree_summary(egi, a),
        })

    vertices = [
        {
            "id": v.id,
            "label": v.label,
            "is_generic": v.is_generic,
            "area": nl.element_area.get(v.id, egi.sheet),
        }
        for v in egi.V
    ]
    predicates = [
        {
            "id": e.id,
            "name": egi.get_relation_name(e.id),
            "area": nl.element_area.get(e.id, egi.sheet),
            "arity": len(egi.nu.get(e.id, ())),
        }
        for e in egi.E
    ]
    ligatures = [
        {
            "predicate_id": lg.predicate_id,
            "vertex_id": lg.vertex_id,
            "port_index": lg.port_index,
            "crossings": list(lg.required_crossings),
        }
        for lg in nl.ligatures
    ]

    return {
        "sheet": egi.sheet,
        "areas": areas,
        "vertices": vertices,
        "predicates": predicates,
        "ligatures": ligatures,
        "counts": {
            "areas": len(area_ids),
            "cuts": len(egi.Cut),
            "vertices": len(egi.V),
            "predicates": len(egi.E),
            "max_depth": _max_depth(nl.cut_parent, egi.sheet),
        },
    }


def _max_depth(cut_parent: Dict[ElementID, ElementID], sheet: ElementID) -> int:
    """Deepest cut nesting (sheet = 0) — useful for the z-axis range in 3-D."""
    def depth(cid: Optional[ElementID]) -> int:
        d = 0
        while cid is not None and cid != sheet:
            cid = cut_parent.get(cid)
            d += 1
        return d
    return max((depth(c) for c in cut_parent), default=0)


__all__ = ["egi_structure", "subtree_summary"]
