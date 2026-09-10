"""A small evaluator written from Dau's semantics, independent of Arisbe's.

Dau, Mathematical Logic with Diagrams (2006): Def 13.1 (models: non-empty
universe, ``=`` interpreted as equality), Def 13.4 (endoporeutic evaluation —
each vertex is existentially assigned at its own context), Def 24.2 (a
constant vertex is fixed at the denotation of its name; nothing forbids two
names co-denoting). Declared extension: Def 13.1 as printed covers arities
k >= 1 only, while the syntax admits 0-ary relations (Defs 12.1, 12.6); here a
0-ary relation holds iff its extension contains the empty tuple.

Imports only the data model. Quotation ovals are skipped (mention, not use).
"""
from __future__ import annotations

import itertools
import random
from typing import Dict, FrozenSet, Iterable, List, Mapping, Tuple

from frozendict import frozendict

from egi_core_dau import RelationalGraphWithCuts

G = RelationalGraphWithCuts


class NotAnEGI(ValueError):
    """The graph violates dominating nodes (Dau Def 12.5), so it is not an EGI."""


def _chain(g: G, area: str) -> List[str]:
    out = [area]
    while area != g.sheet:
        area = g.get_context(area)
        out.append(area)
    return out


def dominating_nodes(g: G) -> bool:
    """Dau Def 12.5: ctx(e) <= ctx(v) — each vertex's context is the edge's or encloses it."""
    for e, seq in g.nu.items():
        chain = _chain(g, g.get_context(e))
        if any(g.get_context(v) not in chain for v in seq):
            return False
    return True


class Structure:
    """(U, I) with U = {0..size-1}; ``const`` names -> individuals; ``ext`` relation -> tuples."""

    __slots__ = ("size", "const", "ext", "_key")

    def __init__(self, size: int, const: Mapping[str, int], ext: Mapping[str, Iterable[tuple]]):
        if size < 1:
            raise ValueError("Dau Def 13.1: the universe is non-empty")
        self.size = size
        self.const = dict(const)
        self.ext = {r: frozenset(map(tuple, ts)) for r, ts in ext.items()}
        self._key = (size, tuple(sorted(self.const.items())),
                     tuple(sorted((r, tuple(sorted(ts))) for r, ts in self.ext.items())))

    def value(self, label: str) -> int:
        return self.const[label]

    def holds(self, rel: str, args: Tuple[int, ...]) -> bool:
        if rel == "=":
            return len(args) == 2 and args[0] == args[1]
        return args in self.ext.get(rel, frozenset())

    def __repr__(self) -> str:
        return f"Structure{self._key}"

    def __eq__(self, other) -> bool:
        return isinstance(other, Structure) and self._key == other._key

    def __hash__(self) -> int:
        return hash(self._key)


def satisfies(g: G, s: Structure) -> bool:
    """Dau Def 13.4, read at the sheet with the empty valuation."""
    if not dominating_nodes(g):
        raise NotAnEGI("dominating nodes violated (Dau Def 12.5)")
    vmap = {v.id: v for v in g.V}
    cuts = {c.id for c in g.Cut}
    return _holds(g, s, g.sheet, {}, vmap, cuts)


def _holds(g, s, c, val, vmap, cuts) -> bool:
    contents = g.area.get(c, frozenset())
    local = sorted(x for x in contents if x in vmap and vmap[x].is_generic)
    edges = sorted(x for x in contents if x in g.nu)
    inner = sorted(x for x in contents if x in cuts and x not in g.quotation)
    for combo in itertools.product(range(s.size), repeat=len(local)):
        v2 = {**val, **dict(zip(local, combo))}
        if all(s.holds(g.rel[e], tuple(_value(v, v2, vmap, s) for v in g.nu[e])) for e in edges) \
                and not any(_holds(g, s, d, v2, vmap, cuts) for d in inner):
            return True
    return False


def _value(v, val, vmap, s) -> int:
    vert = vmap[v]
    return val[v] if vert.is_generic else s.value(vert.label)


# -- universes of structures -------------------------------------------------

def vocabulary(*graphs: G):
    rels = sorted({(g.rel[e], len(g.nu[e])) for g in graphs for e in g.nu if g.rel[e] != "="})
    consts = sorted({v.label for g in graphs for v in g.V if not v.is_generic})
    return tuple(rels), tuple(consts)


def tuple_bits(rels, size: int) -> int:
    return sum(size ** ar for _, ar in rels)


def _assignments(consts, size, una):
    for a in itertools.product(range(size), repeat=len(consts)):
        if una and len(set(a)) != len(a):
            continue
        yield dict(zip(consts, a))


def universe(rels, consts, size, *, cap, sample_n, seed, una=False):
    """Every structure over (rels, consts) of this size when the tuple bits fit
    under ``cap``; otherwise a seeded sample of ``sample_n``. Returns
    (structures, exhaustive). ``una`` restricts to injective name assignments."""
    tuples = {r: list(itertools.product(range(size), repeat=ar)) for r, ar in rels}
    flat = [(r, t) for r, _ in rels for t in tuples[r]]
    assigns = list(_assignments(consts, size, una))
    if not assigns:
        return [], True
    if len(flat) <= cap:
        out = []
        for a in assigns:
            for mask in range(2 ** len(flat)):
                ext: Dict[str, set] = {r: set() for r, _ in rels}
                for i, (r, t) in enumerate(flat):
                    if mask >> i & 1:
                        ext[r].add(t)
                out.append(Structure(size, a, ext))
        return out, True
    rng = random.Random(f"{seed}|{rels}|{consts}|{size}|{una}")
    out = []
    for _ in range(sample_n):
        a = rng.choice(assigns)
        ext = {r: set() for r, _ in rels}
        for r, t in flat:
            if rng.random() < 0.5:
                ext[r].add(t)
        out.append(Structure(size, a, ext))
    return out, False


def model_set(g: G, structures: List[Structure]) -> int:
    """The models of ``g`` among ``structures``, as a bitset over their indices."""
    bits = 0
    for i, s in enumerate(structures):
        if satisfies(g, s):
            bits |= 1 << i
    return bits


# -- components ---------------------------------------------------------------

def _subtree(g: G, x: str) -> List[str]:
    out = [x]
    for y in g.area.get(x, frozenset()):
        out += _subtree(g, y)
    return out


def sheet_components(g: G) -> List[FrozenSet[str]]:
    """Sheet-level items joined when they share a sheet vertex; each component
    is the item ids with their whole subtrees. Conjuncts in different
    components share no line, so the graph holds iff each component holds."""
    items = sorted(g.area.get(g.sheet, frozenset()))
    sheet_vertices = {x for x in items if x in {v.id for v in g.V}}
    parent = {x: x for x in items}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for x in items:
        for y in _subtree(g, x):
            for v in g.nu.get(y, ()):
                if v in sheet_vertices and v != x:
                    parent[find(x)] = find(v)
    groups: Dict[str, List[str]] = {}
    for x in items:
        groups.setdefault(find(x), []).append(x)
    return [frozenset(y for x in grp for y in _subtree(g, x)) for _, grp in sorted(groups.items())]


def restrict(g: G, ids: FrozenSet[str]) -> G:
    """The sub-EGI on ``ids`` (a union of sheet components), built directly."""
    keep = set(ids)
    area = {g.sheet: frozenset(x for x in g.area.get(g.sheet, ()) if x in keep)}
    for c in g.Cut:
        if c.id in keep:
            area[c.id] = frozenset(g.area.get(c.id, frozenset()))
    return G(V=frozenset(v for v in g.V if v.id in keep),
             E=frozenset(e for e in g.E if e.id in keep),
             nu=frozendict({e: s for e, s in g.nu.items() if e in keep}), sheet=g.sheet,
             Cut=frozenset(c for c in g.Cut if c.id in keep), area=frozendict(area),
             rel=frozendict({e: r for e, r in g.rel.items() if e in keep}))
