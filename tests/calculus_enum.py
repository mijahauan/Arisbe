"""Graph enumeration for the calculus property suite.

Spec: docs/superpowers/specs/2026-09-10-calculus-property-suite-design.md §3.
Tier A builds every small graph directly with the core's constructors, never
from a linear form, so no linear form's blind spots are inherited. Tier B
gathers the corpus as used. Every count is returned so a caller can pin it.
"""
from __future__ import annotations

import functools
import hashlib
import itertools
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, FrozenSet, Iterable, List, Optional, Sequence, Tuple

from frozendict import frozendict

import eg_navigation as nav
from canonical_signature import compute_canonical_signatures
from egi_core_dau import Cut, Edge, RelationalGraphWithCuts, Vertex

G = RelationalGraphWithCuts
TOMOS = Path(__file__).resolve().parent.parent / "tomos"

# Above this many elements a key collision is counted as a duplicate without
# an isomorphism search (same_graph does not finish on sumo_upper).
SAME_GRAPH_CEILING = 150


@dataclass(frozen=True)
class Bounds:
    max_cuts: int = 2
    max_edges: int = 3
    max_generics: int = 2
    constants: Tuple[str, ...] = ("a", "b")
    max_constant_spots: int = 2
    max_elements: int = 7
    relations: Tuple[Tuple[str, int], ...] = (("p", 0), ("P", 1), ("=", 2), ("R", 2), ("T", 3))


# Measured in Task 1 Step 6; the decision rule is written there.
DEFAULT_BOUNDS = Bounds(max_cuts=2, max_edges=2, max_generics=1, constants=("a", "b"),
                        max_constant_spots=2, max_elements=3,
                        relations=(("p", 0), ("P", 1), ("=", 2), ("T", 3)))
EXHAUSTIVE_BOUNDS = Bounds(max_elements=4)

REQUIRED_SHAPES = frozenset({
    "empty_cut", "zero_arity", "ternary", "identity_edge", "two_names",
    "unnormalized_constant", "line_above_uses", "isolated_vertex",
})


# -- area helpers -------------------------------------------------------------

def all_areas(g: G) -> List[str]:
    return [g.sheet] + sorted(c.id for c in g.Cut)


def ancestors(g: G, area: str) -> List[str]:
    """``area`` and every context enclosing it, innermost first, ending at the sheet."""
    out = [area]
    while area != g.sheet:
        area = g.get_context(area)
        out.append(area)
    return out


def lca(g: G, areas: Iterable[str]) -> str:
    """The innermost context enclosing every area given."""
    chains = [ancestors(g, a) for a in areas]
    common = set(chains[0]).intersection(*map(set, chains[1:]))
    return next(a for a in chains[0] if a in common)


def edges_on(g: G, vid: str) -> List[str]:
    return sorted(e for e, seq in g.nu.items() if vid in seq)


def line_above_uses(g: G, vid: str) -> bool:
    """A vertex placed strictly outside the least common area of its edges."""
    uses = edges_on(g, vid)
    if not uses:
        return False
    return g.get_context(vid) != lca(g, [g.get_context(e) for e in uses])


def shapes(g: G) -> FrozenSet[str]:
    out = set()
    if any(not g.area.get(c.id) for c in g.Cut):
        out.add("empty_cut")
    if any(len(g.nu[e.id]) == 0 for e in g.E):
        out.add("zero_arity")
    if any(len(g.nu[e.id]) == 3 for e in g.E):
        out.add("ternary")
    if any(g.rel[e.id] == "=" for e in g.E):
        out.add("identity_edge")
    labels = [v.label for v in g.V if not v.is_generic]
    if len(set(labels)) >= 2:
        out.add("two_names")
    if len(labels) != len(set(labels)):
        out.add("unnormalized_constant")
    if any(v.is_generic and line_above_uses(g, v.id) for v in g.V):
        out.add("line_above_uses")
    if any(not edges_on(g, v.id) for v in g.V):
        out.add("isolated_vertex")
    return frozenset(out)


# -- canonical key and de-duplication ----------------------------------------

def graph_key(g: G) -> str:
    """A UUID-independent key. Equal keys do NOT prove isomorphism (the
    signature is a Weisfeiler-Leman refinement, not a complete invariant), so
    ``dedupe`` confirms within a bucket with ``same_graph``."""
    vs, es, cs = compute_canonical_signatures(g)
    sheet = sorted(
        ("V" if x in vs else "E" if x in es else "C", repr(vs.get(x) or es.get(x) or cs.get(x)))
        for x in g.area.get(g.sheet, frozenset())
    )
    payload = repr((sorted(map(repr, vs.values())), sorted(map(repr, es.values())),
                    sorted(map(repr, cs.values())), sheet))
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def _size(g: G) -> int:
    return len(g.V) + len(g.E) + len(g.Cut)


def dedupe(named: Iterable[Tuple[str, G]]) -> Tuple[List[Tuple[str, G]], int, int]:
    """Keep one representative per isomorphism class.

    Returns (kept, duplicates, duplicates_by_key_only). Tier-A graphs are
    keyed ``<graph_key>#<index in bucket>``; a tier-B graph keeps its source name.
    """
    buckets: Dict[str, List[G]] = {}
    kept: List[Tuple[str, G]] = []
    dups = key_only = 0
    for name, g in named:
        k = graph_key(g)
        bucket = buckets.setdefault(k, [])
        hit = False
        for h in bucket:
            if _size(g) > SAME_GRAPH_CEILING:
                key_only += 1
                hit = True
                break
            if nav.same_graph(g, h):
                hit = True
                break
        if hit:
            dups += 1
            continue
        bucket.append(g)
        kept.append((name if name else f"{k}#{len(bucket) - 1}", g))
    return kept, dups, key_only


# -- tier A -------------------------------------------------------------------

def _cut_trees(max_cuts: int) -> List[Dict[str, str]]:
    """Every tree of at most two cuts under the sheet, as child -> parent."""
    if max_cuts > 2:
        raise ValueError("cut trees are enumerated for at most two cuts")
    trees = [{}]
    if max_cuts >= 1:
        trees.append({"c1": "S"})
    if max_cuts >= 2:
        trees += [{"c1": "S", "c2": "S"}, {"c1": "S", "c2": "c1"}]
    return trees


def _chain(parent: Dict[str, str], area: str) -> List[str]:
    out = [area]
    while area != "S":
        area = parent[area]
        out.append(area)
    return out


def build(parent: Dict[str, str], vertices: Sequence[Tuple[Optional[str], str]],
          edges: Sequence[Tuple[str, Tuple[int, ...], str]]) -> G:
    """Construct directly: sheet ``S``, cuts ``c1..``, vertices ``v1..``, edges ``e1..``."""
    area: Dict[str, set] = {a: set() for a in ["S", *parent]}
    for c, p in parent.items():
        area[p].add(c)
    V = []
    for i, (label, a) in enumerate(vertices, 1):
        vid = f"v{i}"
        V.append(Vertex(vid) if label is None else Vertex(vid, label=label, is_generic=False))
        area[a].add(vid)
    E, nu, rel = [], {}, {}
    for j, (name, args, a) in enumerate(edges, 1):
        eid = f"e{j}"
        E.append(Edge(eid))
        nu[eid] = tuple(f"v{k + 1}" for k in args)
        rel[eid] = name
        area[a].add(eid)
    return G(V=frozenset(V), E=frozenset(E), nu=frozendict(nu), sheet="S",
             Cut=frozenset(Cut(c) for c in parent),
             area=frozendict({k: frozenset(v) for k, v in area.items()}),
             rel=frozendict(rel))


@dataclass
class TierAReport:
    bounds: Bounds
    built: int = 0
    refused_by_core: int = 0
    duplicates: int = 0
    graphs: List[Tuple[str, G]] = field(default_factory=list)

    def extent(self) -> Dict[str, int]:
        return {"built": self.built, "refused_by_core": self.refused_by_core,
                "duplicates": self.duplicates, "kept": len(self.graphs)}


def _raw(b: Bounds):
    kinds: List[Optional[str]] = [None, *b.constants]
    for parent in _cut_trees(b.max_cuts):
        areas = ["S", *parent]
        options = [(k, a) for k in kinds for a in areas]
        for nv in range(0, b.max_generics + b.max_constant_spots + 1):
            for vs in itertools.combinations_with_replacement(options, nv):
                if sum(1 for k, _ in vs if k is None) > b.max_generics:
                    continue
                if sum(1 for k, _ in vs if k is not None) > b.max_constant_spots:
                    continue
                if len(parent) + nv > b.max_elements:
                    continue
                edge_opts = [
                    (name, args, a)
                    for name, ar in b.relations
                    for args in itertools.product(range(nv), repeat=ar)
                    for a in areas
                    # dominating nodes (Dau Def 12.5): ctx(e) <= ctx(v)
                    if all(vs[k][1] in _chain(parent, a) for k in args)
                ]
                room = b.max_elements - len(parent) - nv
                for ne in range(0, min(b.max_edges, room) + 1):
                    for es in itertools.combinations_with_replacement(edge_opts, ne):
                        yield parent, vs, es


@functools.lru_cache(maxsize=None)
def tier_a(bounds: Bounds = DEFAULT_BOUNDS) -> TierAReport:
    report = TierAReport(bounds)
    built: List[Tuple[str, G]] = []
    for parent, vs, es in _raw(bounds):
        report.built += 1
        try:
            built.append(("", build(parent, vs, es)))
        except ValueError:
            report.refused_by_core += 1
    report.graphs, report.duplicates, _ = dedupe(built)
    return report
