"""Dau's rules and the moves that try them (spec 2026-09-10 §1a.2–§1a.4, §3.3).

The table is Dau's, cited by definition and book page; each rule names the
engine entry point that performs it, or None. ``legal`` (Task 5) states each
precondition independently of the engine and lives in this module, which
therefore must never import the rule modules — see calculus_apply for that.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Iterator, List, Optional, Tuple

from calculus_enum import all_areas, ancestors, edges_on
from egi_core_dau import RelationalGraphWithCuts

G = RelationalGraphWithCuts


@dataclass(frozen=True)
class DauRule:
    name: str
    cite: str
    direction: str          # "one-way" | "equivalence"
    engine: Optional[str]   # "protocol:X" | "engine:X" | "ligature:X" | "split" | "merge" | None
    judged: bool            # is refusal agreement judged by legal()?


DAU_RULES: Tuple[DauRule, ...] = (
    DauRule("ERA", "Def 15.2 erasure, p.164-165: positive contexts", "one-way", "protocol:ERA", True),
    DauRule("INS", "Def 15.2 insertion, p.164-165: negative contexts", "one-way", "protocol:INS", True),
    DauRule("IT+", "Def 15.2 iteration, p.164, 166: no polarity condition", "equivalence", "protocol:IT+", True),
    DauRule("IT-", "Def 15.2 deiteration, p.164, 166", "equivalence", "protocol:IT-", True),
    DauRule("DC+", "Def 15.2 double cuts, p.164: any context", "equivalence", "protocol:DC+", True),
    DauRule("DC-", "Def 15.2 double cuts, p.164: any context", "equivalence", "protocol:DC-", True),
    DauRule("VERTEX_INS", "Def 15.2 inserting a vertex, p.164, 166: any context", "equivalence", "engine:HEAVY_DOT", True),
    DauRule("VERTEX_ERA", "Def 15.2 erasing a vertex, p.164, 166: any context", "equivalence", "protocol:ERA", True),
    DauRule("MOVE_BRANCHES", "Lemma 16.1, p.169", "equivalence", "ligature:MOVE_BRANCHES", False),
    DauRule("EXTEND_LIGATURE", "Lemma 16.2, p.172", "equivalence", "ligature:EXTEND_LIGATURE", False),
    DauRule("RETRACT_LIGATURE", "Lemma 16.3, p.173", "equivalence", "ligature:RETRACT_LIGATURE", False),
    DauRule("REARRANGE_LIGATURE", "Def 16.4, Cor 16.5, p.174-175", "equivalence", "ligature:REARRANGE_LIGATURE", False),
    DauRule("SPLIT_VERTEX", "Def 16.6, Lemma 16.7, p.175-178", "equivalence", "split", False),
    DauRule("MERGE_VERTICES", "Def 16.6 merging, p.176", "equivalence", "merge", False),
    DauRule("ORIENT_IDENTITY", "Def 12.14 orientation of an identity edge, p.138", "equivalence", None, False),
    DauRule("LIGATURE_VERTEX", "Def 12.14 adding/removing a vertex, p.138", "equivalence", None, False),
    DauRule("CONSTANT_IDENTITY", "Def 24.10 constant identity rule, p.271", "equivalence", None, False),
    DauRule("CONSTANT_EXISTENCE", "Def 24.10 existence of constants, p.271", "equivalence", None, False),
    DauRule("SEPARATE_CONSTANT", "Def 24.6, Def 24.10, p.265-271", "equivalence", None, False),
)
RULES = {r.name: r for r in DAU_RULES}
IMPLEMENTED = tuple(r for r in DAU_RULES if r.engine)
UNIMPLEMENTED = frozenset(r.name for r in DAU_RULES if r.engine is None)
LIGATURE_RULES = ("MOVE_BRANCHES", "EXTEND_LIGATURE", "RETRACT_LIGATURE", "REARRANGE_LIGATURE")

# Standalone EGIF. EGIF cannot write a 0-ary relation or an isolated constant,
# so INS never offers them (spec §1a.6).
INS_CATALOGUE: Tuple[str, ...] = (
    "~[ ]", "[*x]", "(P *x)", '(P "a")', "(R *x *y)", "~[ (P *x) ]", '(R "a" *x)',
)


@dataclass(frozen=True)
class Move:
    rule: str
    selection: Tuple[str, ...] = ()
    target: Optional[str] = None
    content: Optional[str] = None
    hooks: Tuple[Tuple[str, int], ...] = ()   # SPLIT_VERTEX: (edge id, 0-based position)


def elements(g: G) -> List[str]:
    return sorted([v.id for v in g.V] + [e.id for e in g.E] + [c.id for c in g.Cut])


def _subsets(xs, lo=0, hi=None):
    hi = len(xs) if hi is None else min(hi, len(xs))
    for k in range(lo, hi + 1):
        yield from itertools.combinations(xs, k)


def units(g: G) -> List[Tuple[str, ...]]:
    """Each edge; each cut; each vertex with its edges; each non-empty area's contents."""
    out = [(e,) for e in sorted(g.nu)]
    out += [(c,) for c in sorted(c.id for c in g.Cut)]
    out += [tuple(sorted({v, *edges_on(g, v)})) for v in sorted(v.id for v in g.V)]
    out += [tuple(sorted(g.area[a])) for a in all_areas(g) if g.area.get(a)]
    return list(dict.fromkeys(out))


def _selections(g: G, tier: str, lo: int, units_only: bool):
    if tier == "A":
        yield from _subsets(elements(g), lo)
        return
    seen = set()
    first = [()] if lo == 0 else []
    rest = [u for u in units(g) if len(u) >= lo]
    if not units_only:
        rest += list(_subsets(elements(g), max(lo, 1), 2))
    for s in first + rest:
        if s not in seen:
            seen.add(s)
            yield s


def moves(rule: str, g: G, tier: str, units_only: bool = False) -> Iterator[Move]:
    """Every candidate application of ``rule`` to ``g`` — legal or not."""
    areas = all_areas(g)
    sels = lambda lo: _selections(g, tier, lo, units_only)  # noqa: E731
    if rule in ("ERA", "IT-", "DC-"):
        for s in sels(1):
            yield Move(rule, s)
    elif rule == "DC+":
        for s in sels(0):
            for a in areas:
                yield Move(rule, s, a)
    elif rule == "IT+":
        for s in sels(1):
            for a in areas:
                yield Move(rule, s, a)
    elif rule == "INS":
        for a in areas:
            for c in INS_CATALOGUE:
                yield Move(rule, (), a, c)
    elif rule == "VERTEX_INS":
        for a in areas:
            yield Move(rule, (), a)
    elif rule == "VERTEX_ERA":
        for x in elements(g):
            yield Move(rule, (x,))
    elif rule in LIGATURE_RULES:
        for s in _subsets(elements(g), 1, 2):
            for a in areas:
                yield Move(rule, s, a)
    elif rule == "SPLIT_VERTEX":
        # Only Def 16.6's domain: ctx(v) >= c >= ctx(e_k) for every moved hook.
        for v in sorted(x.id for x in g.V):
            hooks = [(e, i) for e in edges_on(g, v) for i, w in enumerate(g.nu[e]) if w == v]
            for hs in _subsets(hooks, 1):
                for a in areas:
                    if g.get_context(v) in ancestors(g, a) and all(
                            a in ancestors(g, g.get_context(e)) for e, _ in hs):
                        yield Move(rule, (v,), a, hooks=hs)
    elif rule == "MERGE_VERTICES":
        # Def 16.6 merging (p.176): e = (v1, v2) with ctx(v1) >= ctx(e) = ctx(v2); v2 into v1.
        for e in sorted(g.nu):
            if g.rel[e] == "=" and len(g.nu[e]) == 2:
                for v1, v2 in (g.nu[e], g.nu[e][::-1]):
                    if g.get_context(v2) == g.get_context(e) and \
                            g.get_context(v1) in ancestors(g, g.get_context(e)) and v1 != v2:
                        yield Move(rule, (v1, v2, e))
    else:
        raise KeyError(f"no move generator for {rule}")
