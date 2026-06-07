"""
Tension layout — the vertex tree as an organizing principle (the structural core).

A *line of identity* is elastic: identified things want to be near each other.
This module turns that into a concrete, **correspondence-safe** choice for one of
layout's free dimensions — the left-to-right order of an area's sibling blocks
(the `projection_conventions.sibling_cut_ordering` choice, logically free per
spec §5.3).

The model (see ``docs/TENSION_LAYOUT.md``):

- A **spring** is one predicate–vertex incidence (from ``ν``).
- A **block** is a direct child of an area (a sub-cut, vertex, or predicate);
  every deeper element belongs to the top-level block that contains it.
- For a 1-D ordering of an area's blocks,
  ``tension(order) = Σ over intra-area springs |pos[block(u)] − pos[block(v)]|``.
- ``sibling_order`` returns the tension-minimizing order, tie-broken by a caller
  supplied deterministic key (the engine's structural key), so isomorphic areas
  still lay out identically.

Why this is safe to feed into layout: a ligature's *crossing-sequence* (the §3.3
homotopy class) is computed from the area tree alone, so it is **identical under
every ordering**.  Reordering siblings moves only the free projection dimension;
correspondence is untouched.  This module owns no geometry — it consumes the EGI
structure and returns an order; the engine realizes it.
"""

import collections
from itertools import permutations
from typing import Callable, Dict, List, Optional, Tuple

from egi_core_dau import ElementID, RelationalGraphWithCuts
from presentation_ops import element_area, cut_parents

# Brute-force the exact minimum up to this many blocks; above it, a barycenter
# sweep (an area with more siblings than this is rare and the heuristic is good).
_EXACT_MAX = 8


def springs(egi: RelationalGraphWithCuts) -> List[Tuple[ElementID, ElementID]]:
    """One spring per predicate–vertex incidence (the ``ν`` function)."""
    out: List[Tuple[ElementID, ElementID]] = []
    for e in egi.E:
        for v in egi.nu.get(e.id, ()):
            out.append((e.id, v))
    return out


def block_of(
    elem: ElementID,
    area: ElementID,
    elem_area: Dict[ElementID, ElementID],
    parent_map: Dict[ElementID, ElementID],
) -> Optional[ElementID]:
    """The direct child of ``area`` that contains ``elem`` (or ``elem`` itself if
    it sits directly in ``area``); ``None`` if ``elem`` is outside ``area``."""
    a = elem_area.get(elem)
    if a is None:
        return None
    if a == area:
        return elem
    cur: Optional[ElementID] = a
    while cur is not None and cur != area:
        if parent_map.get(cur) == area:
            return cur
        cur = parent_map.get(cur)
    return None


def _intra_springs(
    egi: RelationalGraphWithCuts,
    area: ElementID,
    elem_area: Dict[ElementID, ElementID],
    parent_map: Dict[ElementID, ElementID],
) -> List[Tuple[ElementID, ElementID]]:
    """Springs whose two endpoints lie in *different* direct children of
    ``area`` (the only ones whose tension an in-area ordering can change)."""
    out: List[Tuple[ElementID, ElementID]] = []
    for e, v in springs(egi):
        bu = block_of(e, area, elem_area, parent_map)
        bv = block_of(v, area, elem_area, parent_map)
        if bu is not None and bv is not None and bu != bv:
            out.append((bu, bv))
    return out


def tension(order: List[ElementID], intra: List[Tuple[ElementID, ElementID]]) -> float:
    """Σ |index difference| of the blocks each intra-area spring connects."""
    idx = {b: i for i, b in enumerate(order)}
    return float(sum(abs(idx[bu] - idx[bv]) for bu, bv in intra))


def optimize_order(
    blocks: List[ElementID],
    intra: List[Tuple[ElementID, ElementID]],
) -> List[ElementID]:
    """Tension-minimizing 1-D order of ``blocks``.

    ``blocks`` must already be in a deterministic base order (the caller's
    structural key); the result is then deterministic and tie-broken toward that
    base — exact for ≤ ``_EXACT_MAX`` blocks (the first minimal permutation in
    base order), a barycenter sweep above it.
    """
    if not intra or len(blocks) < 3:
        return list(blocks)
    if len(blocks) <= _EXACT_MAX:
        return list(min(permutations(blocks), key=lambda o: tension(list(o), intra)))

    from collections import defaultdict
    nbr: Dict[ElementID, List[ElementID]] = defaultdict(list)
    for bu, bv in intra:
        nbr[bu].append(bv)
        nbr[bv].append(bu)
    order = list(blocks)
    best, best_t = list(order), tension(order, intra)
    for _ in range(20):
        idx = {b: i for i, b in enumerate(order)}
        bary = {b: (sum(idx[n] for n in nbr[b]) / len(nbr[b]) if nbr[b] else idx[b])
                for b in order}
        # Sort by barycentre, tie-broken by the base index for determinism.
        base_idx = {b: i for i, b in enumerate(blocks)}
        order = sorted(order, key=lambda b: (bary[b], base_idx[b]))
        t = tension(order, intra)
        if t < best_t:
            best, best_t = list(order), t
    return best


def sibling_order(
    egi: RelationalGraphWithCuts,
    area: ElementID,
    base_order: List[ElementID],
) -> List[ElementID]:
    """Reorder an area's direct children (``base_order``, in the engine's
    deterministic structural order) to minimize ligature tension.

    Areas with no cross-block lines of identity keep ``base_order`` unchanged —
    tension is indifferent there, so the change is surgical.  The crossing
    sequence of every ligature is order-independent, so this never affects §3.3.
    """
    elem_area = element_area(egi)
    parent_map = cut_parents(egi)
    intra = _intra_springs(egi, area, elem_area, parent_map)
    if not intra:
        return list(base_order)
    return optimize_order(list(base_order), intra)


def incidence(egi: RelationalGraphWithCuts) -> Dict:
    """Adjacency of the incidence graph: each predicate/vertex → its incident
    elements (a predicate to its ν vertices, a vertex to its predicates)."""
    inc: Dict = {}
    for e in egi.E:
        for v in egi.nu.get(e.id, ()):
            inc.setdefault(e.id, []).append(v)
            inc.setdefault(v, []).append(e.id)
    return inc


def extract_thread(egi: RelationalGraphWithCuts) -> Optional[List]:
    """The ordered element chain ``[pred, vertex, pred, …]`` of a graph that is a
    **single thread** — one connected line of identity with no branches (every
    predicate/vertex has degree ≤ 2).  Returns ``None`` if the graph is empty,
    disconnected, branched (a degree-≥3 junction), or a pure cycle.

    Deterministic: the walk starts at the lexicographically smallest degree-1
    endpoint."""
    inc = incidence(egi)
    if not inc:
        return None
    if any(len(ns) > 2 for ns in inc.values()):
        return None
    ends = sorted(n for n, ns in inc.items() if len(ns) == 1)
    if not ends:
        return None  # cycle, or nothing
    start = ends[0]
    order, prev, cur = [start], None, start
    while True:
        nxts = [n for n in inc[cur] if n != prev]
        if not nxts:
            break
        prev, cur = cur, nxts[0]
        order.append(cur)
    # Single thread ⇔ the walk covered every incident element.
    if len(order) != len(inc):
        return None
    return order


def stress_majorize(
    nodes: List,
    edges: List[Tuple],
    *,
    iters: int = 300,
    scale: float = 1.0,
) -> Dict:
    """Deterministic 2-D stress majorization (SMACOF) of a graph.

    Minimizes the tension energy ``Σ w_ij (‖p_i − p_j‖ − d_ij)²`` with ideal
    distances ``d_ij`` = graph (BFS) distance and ``w_ij = 1/d_ij²`` — a path
    relaxes to a straight line in order, a star to a hub.  Disconnected pairs get
    a large finite ideal distance (they simply repel).  Pure numpy (no scipy);
    the fixed line-init makes it reproducible (layout invariant L1).

    Returns ``{node: (x, y)}`` as plain floats, scaled by ``scale``.
    """
    import numpy as np

    n = len(nodes)
    if n == 0:
        return {}
    if n == 1:
        return {nodes[0]: (0.0, 0.0)}

    idx = {u: i for i, u in enumerate(nodes)}
    adj = collections.defaultdict(set)
    for a, b in edges:
        if a in idx and b in idx and a != b:
            adj[a].add(b)
            adj[b].add(a)

    D = np.zeros((n, n))
    for s in nodes:
        dist = {s: 0}
        q = collections.deque([s])
        while q:
            u = q.popleft()
            for w in adj[u]:
                if w not in dist:
                    dist[w] = dist[u] + 1
                    q.append(w)
        for t, dd in dist.items():
            D[idx[s], idx[t]] = dd
    big = D.max() + 1 if n else 1.0
    for i in range(n):
        for j in range(n):
            if i != j and D[i, j] == 0:
                D[i, j] = big

    with np.errstate(divide="ignore", invalid="ignore"):
        W = np.where(D > 0, 1.0 / D ** 2, 0.0)

    X = np.column_stack([np.arange(n, dtype=float), (np.arange(n) % 2) * 0.3])
    for _ in range(iters):
        diff = X[:, None] - X[None, :]
        dist = np.linalg.norm(diff, axis=2)
        np.fill_diagonal(dist, 1.0)
        Xn = np.zeros_like(X)
        for i in range(n):
            num = np.zeros(2)
            den = 0.0
            for j in range(n):
                if i == j or W[i, j] == 0:
                    continue
                num += W[i, j] * (X[j] + D[i, j] * (X[i] - X[j]) / dist[i, j])
                den += W[i, j]
            Xn[i] = num / den if den else X[i]
        X = Xn
    X = X * scale
    return {u: (float(X[idx[u], 0]), float(X[idx[u], 1])) for u in nodes}


__all__ = [
    "springs",
    "block_of",
    "tension",
    "optimize_order",
    "sibling_order",
    "stress_majorize",
    "incidence",
    "extract_thread",
]
