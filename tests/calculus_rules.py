"""The engine entry point for each of Dau's rules, and the moves that try them
(spec 2026-09-10 §1a.2–§1a.4, §3.3).

The rule table itself — name, citation, direction, whether ``legal`` judges it —
is the kernel's (``src/dau_kernel.py``), with ``legal`` and the licensed results;
they were this module's until 2026-11-25. What stays here is the suite's own:
which entry point performs each rule, or None, and every candidate move. This
module still must never import the rule modules — see calculus_apply for that.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Iterator, List, Optional, Tuple

from calculus_enum import all_areas, ancestors, edges_on
from dau_kernel import RULE_TABLE, Move, elements, positive
from egi_core_dau import RelationalGraphWithCuts

G = RelationalGraphWithCuts


@dataclass(frozen=True)
class DauRule:
    name: str
    cite: str
    direction: str          # "one-way" | "equivalence"
    engine: Optional[str]   # "protocol:X" | "engine:X" | "ligature:X" | "split" | "merge" | None
    judged: bool            # is refusal agreement judged by legal()?


# A rule absent from this map has no entry point at all.
ENGINE = {
    "ERA": "protocol:ERA",
    "INS": "protocol:INS",
    "INS_EDGE": "protocol:INS",
    "IT+": "protocol:IT+",
    "IT-": "protocol:IT-",
    "DC+": "protocol:DC+",
    "DC-": "protocol:DC-",
    "VERTEX_INS": "engine:HEAVY_DOT",
    "VERTEX_ERA": "engine:VERTEX_ERA",
    "CONSTANT_EXISTENCE": "engine:CONSTANT_EXISTENCE",
    "CONSTANT_IDENTITY": "engine:CONSTANT_IDENTITY",
    "MOVE_BRANCHES": "ligature:MOVE_BRANCHES",
    "EXTEND_LIGATURE": "ligature:EXTEND_LIGATURE",
    "RETRACT_LIGATURE": "ligature:RETRACT_LIGATURE",
    "REARRANGE_LIGATURE": "ligature:REARRANGE_LIGATURE",
    "SPLIT_VERTEX": "split",
    "MERGE_VERTICES": "merge",
}
assert set(ENGINE) <= {r.name for r in RULE_TABLE}, "an entry point names no Dau rule"

DAU_RULES: Tuple[DauRule, ...] = tuple(
    DauRule(r.name, r.cite, r.direction, ENGINE.get(r.name), r.judged) for r in RULE_TABLE)
RULES = {r.name: r for r in DAU_RULES}
IMPLEMENTED = tuple(r for r in DAU_RULES if r.engine)
UNIMPLEMENTED = frozenset(r.name for r in DAU_RULES if r.engine is None)
LIGATURE_RULES = ("MOVE_BRANCHES", "EXTEND_LIGATURE", "RETRACT_LIGATURE", "REARRANGE_LIGATURE")

# Standalone EGIF. EGIF cannot write a 0-ary relation or an isolated constant,
# so INS never offers them (spec §1a.6).
INS_CATALOGUE: Tuple[str, ...] = (
    "~[ ]", "[*x]", "(P *x)", '(P "a")', "(R *x *y)", "~[ (P *x) ]", '(R "a" *x)',
)


# Bare constant names for CONSTANT_EXISTENCE's insertion: "a" is the constant
# tier A builds its graphs from, "k" is one no enumerated graph uses.
CONSTANT_CATALOGUE: Tuple[str, ...] = ("a", "k")


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
    if tier in ("A", "S"):
        # Tier S is hand-chosen and small, so it is enumerated exhaustively as
        # tier A is: every subset of the elements, not just the units.
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
    elif rule == "INS_EDGE":
        # Dau p.165: an edge inserted into a negative context onto vertices
        # already present. The content names the host's own line by its EGIF
        # bound label, which is what the engine cannot parse.
        for a in areas:
            if positive(g, a):
                continue
            for v in sorted(x.id for x in g.V if x.is_generic):
                label = g.variable_names.get(v)
                # The line must be in scope at the target: ctx(v) encloses it
                # (Def 12.5), i.e. ctx(v) is on the target's ancestor chain.
                if label is None or g.get_context(v) not in ancestors(g, a):
                    continue          # unnamed line, or out of scope here
                yield Move(rule, (v,), a, f"(P {label})")
    elif rule == "VERTEX_INS":
        for a in areas:
            yield Move(rule, (), a)
    elif rule == "VERTEX_ERA":
        # Dau's vertex rule is about vertices, so only vertices are offered:
        # isolated or not, generic or carrying a constant.
        for x in sorted(v.id for v in g.V):
            yield Move(rule, (x,))
    elif rule == "CONSTANT_EXISTENCE":
        # Def 24.10 (p.271), both directions: every vertex offered for erasure
        # (generic, constant, isolated or not), and into every context a
        # constant the graph may already use and one it cannot.
        for x in sorted(v.id for v in g.V):
            yield Move(rule, (x,))
        for a in areas:
            for name in CONSTANT_CATALOGUE:
                yield Move(rule, (), a, name)
    elif rule == "CONSTANT_IDENTITY":
        # Def 24.10 (p.271): every identity link offered for erasure; every
        # pair of vertices offered for linking, in every context. Pairs sharing
        # a constant come first, so a budgeted tier reaches the moves the rule
        # is about before the ones it must refuse.
        for e in sorted(g.nu):
            if g.rel[e] == "=":
                yield Move(rule, (e,))
        label = {v.id: (None if v.is_generic else v.label) for v in g.V}
        pairs = sorted(itertools.combinations(sorted(label), 2),
                       key=lambda p: not (label[p[0]] is not None and label[p[0]] == label[p[1]]))
        for v, w in pairs:
            for a in areas:
                yield Move(rule, (v, w), a)
    elif rule in LIGATURE_RULES:
        # Task 7: the engine's choice of vertex within the selection (the one
        # kept, or moved from) is now a function of the graph — its canonical
        # signature — not of the order the selection arrives in, so a selection
        # is ONE candidate. Enumerating both orders tested nothing the engine
        # could still tell apart.
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
