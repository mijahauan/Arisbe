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
from egif_parser_dau import parse_egif
from tarski import dominating_nodes

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
    # INS is the insertion of standalone content — a closed subgraph (an isolated
    # vertex included) — which is what the protocol's INS performs. Inserting an
    # edge onto vertices already present (p.165: erasing an edge keeps its
    # vertices, V^(e) := V, and insertion is its inverse) is INS_EDGE, below.
    DauRule("INS", "Def 15.2 insertion of a closed subgraph, p.164-165: negative contexts", "one-way", "protocol:INS", True),
    DauRule("INS_EDGE", "Def 15.2 insertion of an edge onto existing vertices, p.165: negative contexts", "one-way", None, False),
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
        # Dau's vertex rule is about vertices; an edge offered here would be
        # performed by the ERA entry point and read as applied-but-illegal.
        for x in sorted(v.id for v in g.V):
            yield Move(rule, (x,))
    elif rule in LIGATURE_RULES:
        # The ligature engine reads its unordered selection in iteration order
        # (the first vertex is the one kept, or moved from), so the order is part
        # of the move: calculus_apply hands the selection over in the tuple's
        # order, and each order of a two-element selection is its own candidate.
        for s in _subsets(elements(g), 1, 2):
            for p in dict.fromkeys((s, s[::-1])):
                for a in areas:
                    yield Move(rule, p, a)
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


# -- legal -------------------------------------------------------------------

Verdict = Tuple[Optional[bool], str]
IT_MINUS_BUDGET = 20000


def expand(g: G, ids) -> set:
    """``ids`` with the whole contents of every cut among them."""
    out, stack = set(), list(ids)
    while stack:
        x = stack.pop()
        if x not in out:
            out.add(x)
            stack.extend(g.area.get(x, ()))
    return out


def tops(g: G, X: set) -> List[str]:
    return sorted(x for x in X if g.get_context(x) not in X)


def positive(g: G, area: str) -> bool:
    """The sheet is positive; an outermost cut's area is negative (the reading
    the calculus requires — Def 12.4's printed count includes the cut itself)."""
    return (len(ancestors(g, area)) - 1) % 2 == 0


def _one_context(g: G, X: set) -> Optional[str]:
    ctxs = {g.get_context(t) for t in tops(g, X)}
    return next(iter(ctxs)) if len(ctxs) == 1 else None


def _nothing_dangles(g: G, X: set) -> bool:
    vids = {v.id for v in g.V}
    return all(set(edges_on(g, x)) <= X for x in X if x in vids)


def _touches_quotation(g: G, ids, target) -> bool:
    """Whether the *whole* selection — not just the ids named — reaches the
    quotation apparatus or an oval's interior. A cut in ``ids`` carries
    everything under it into the check (Def 15.2's rules act on a selection
    plus its contents, e.g. ERA of a closed subgraph), so a plain cut that
    merely CONTAINS an oval must be caught too, not only the oval cut itself."""
    if not g.quotation and not g.sort:
        return False
    apparatus = set(g.quotation) | set(g.quotation.values()) | set(g.sort)
    inside = set().union(*(expand(g, [c]) for c in g.quotation)) if g.quotation else set()
    X = expand(g, ids)
    return bool(X & (apparatus | inside)) or target in inside


def legal(g: G, m: Move) -> Verdict:
    rule = RULES[m.rule]
    if not rule.judged:
        return None, f"not judged: {m.rule}'s parameters underdetermine the move"
    if not dominating_nodes(g):
        return None, "not judged: the source is not an EGI (Def 12.5)"
    known = set(elements(g))
    if any(x not in known for x in m.selection):
        return False, "the selection names an unknown element"
    if m.target is not None and m.target not in all_areas(g):
        return False, "the target is not a context"
    if m.rule in ("IT+", "IT-") and (g.quotation or g.sort):
        # Iteration/deiteration compare structure across two contexts (Def
        # 15.2, p.164, 166); a quotation-bearing graph makes that comparison
        # cross the B-min opacity boundary (Arisbe's, not Dau's) no matter
        # which elements are selected, so the whole rule is left unjudged
        # rather than checked selection-by-selection.
        return None, "not judged: IT± on a quotation-bearing graph (B-min opacity)"
    if _touches_quotation(g, m.selection, m.target):
        return None, "not judged: the quotation apparatus (B-min is Arisbe's, not Dau's)"
    return _LEGAL[m.rule](g, m)


def _era(g: G, m: Move) -> Verdict:
    """Def 15.2 erasure (p.164-165): in a positive context, any directly
    enclosed edge, isolated vertex, or closed subgraph may be erased.

    Shared-vertex reading: an edge may go without its vertex — Dau's edge
    rule carries no closure condition (p.165) — and a selection holding an
    edge on an outer line is Dau's own worked derivation (add a vertex to the
    ligature, erase, erase; p.166-167). A multi-element selection is a run of
    erasures in one context, so it must sit in one positive context and leave
    no edge without its vertex."""
    if not m.selection:
        return False, "empty selection"
    X = expand(g, m.selection)
    c = _one_context(g, X)
    if c is None:
        return False, "the selection spans several contexts"
    if not positive(g, c):
        return False, "the context is negative"
    if not _nothing_dangles(g, X):
        return False, "a selected vertex would leave an edge behind"
    return True, "positive context, nothing left dangling"


def _ins(g: G, m: Move) -> Verdict:
    """Def 15.2 insertion (p.164-165): in a negative context, any edge,
    isolated vertex, or closed subgraph may be inserted. The content is a
    standalone graph, so it is closed and has dominating nodes.

    The result must still be an EGI over one alphabet: a relation name has ONE
    arity ar(R) (Def 12.6, p.126) and every edge carries it, |e| = ar(κ(e))
    (Def 12.7, p.126). So the content may not use a name at an arity the
    graph's declared alphabet — or, lacking one, its own edges — give it
    otherwise (Task 10: tier B's dau_2006_p112_ligature declares R unary)."""
    try:
        h = parse_egif(m.content or "")
    except Exception:
        return False, "the content does not parse"
    if m.target is None or positive(g, m.target):
        return False, "the target is not a negative context"
    arity = {}
    if g.alphabet is not None:
        arity.update({r: n for r, n in g.alphabet.ar.items() if r in g.alphabet.R})
    for e, seq in g.nu.items():
        arity.setdefault(g.rel[e], len(seq))
    if any(arity.get(h.rel[e], len(seq)) != len(seq) for e, seq in h.nu.items()):
        return False, "the content uses a relation name at another arity (Def 12.6-12.7, p.126)"
    return True, "negative context"


def _dc_plus(g: G, m: Move) -> Verdict:
    """Def 15.2 double cuts (p.164): area(c1) = {c2}, in any context.
    Insertion reverses erasure, so c1 enters the target and c2 receives some
    of the target's direct contents. A vertex may move inward only with all
    its edges, or the result breaks dominating nodes (Def 12.5). A cut named
    with some of its contents is the subgraph of the cut alone (Def 12.10,
    p.134), so it is the selection's TOP elements that must be in the target."""
    if m.target is None:
        return False, "no target"
    X = expand(g, m.selection)
    if any(g.get_context(x) != m.target for x in tops(g, X)):
        return False, "the selection is not directly in the target"
    if not _nothing_dangles(g, X):
        return False, "a vertex would move inside its own edge's context"
    return True, "any context"


def _dc_minus(g: G, m: Move) -> Verdict:
    """Def 15.2 double cuts (p.164): two cuts with area(c1) = {c2} may be erased, any context."""
    cuts = {c.id for c in g.Cut}
    if len(m.selection) != 1 or m.selection[0] not in cuts:
        return False, "select exactly the outer cut"
    inner = g.area.get(m.selection[0], frozenset())
    if len(inner) != 1 or next(iter(inner)) not in cuts:
        return False, "its area is not exactly one cut"
    return True, "a double cut"


def _it_plus(g: G, m: Move) -> Verdict:
    """Def 15.2 iteration (p.164, 166): a (not necessarily closed) subgraph in
    context c0 may be copied into any context c <= c0, c not inside it; no
    polarity condition, and c = c0 is allowed.

    Shared-vertex reading: an unselected vertex of a selected edge is the
    Θ-linked vertex of Def 15.2's second clause, reused by pointing at it
    rather than joined by an identity edge — for c = c0, equivalent by
    Lemma 16.3 (p.173) (retracting the identity edge back to a single line);
    for c < c0, equivalent by merging the copy vertex into the source vertex
    along its identity edge, Def 16.6 / Lemma 16.7 (p.175-178)."""
    if not m.selection:
        return False, "empty selection"
    X = expand(g, m.selection)
    c0 = _one_context(g, X)
    if c0 is None:
        return False, "the selection spans several contexts"
    if m.target is None or c0 not in ancestors(g, m.target):
        return False, "the target is not within the source context"
    if m.target in X:
        return False, "the target lies inside the selection"
    return True, "target within the source context"


def _it_minus(g: G, m: Move) -> Verdict:
    """Def 15.2 deiteration (p.164, 166): a subgraph may be erased if it could
    have been inserted by iteration — there is a source, disjoint from it, in
    a context enclosing (or equal to) its own, of which it is a copy: same
    kinds, relation names and constant labels, same nesting, and each edge
    reaching either the copy of its source's vertex or the very same vertex
    (a reused line — the shared-vertex form of the Θ clause).

    Not modelled: Def 15.2's Θ clause in its literal form (p.166), where
    iteration may add identity edges F = {e_{v,w}} from a copy's vertices to
    a Θ-linked vertex w OUTSIDE the copy, and deiteration erases the copy
    together with F. A selection containing such an identity edge is left
    unjudged rather than wrongly refused."""
    if not m.selection:
        return False, "empty selection"
    X = expand(g, m.selection)
    if any(g.rel.get(e) == "=" and any(v not in X for v in g.nu[e])
           for e in X if e in g.nu):
        return None, ("not judged: an identity edge links the copy outside it "
                       "— Def 15.2's Θ clause (p.166) is not modelled")
    c = _one_context(g, X)
    if c is None:
        return False, "the selection spans several contexts"
    if not _nothing_dangles(g, X):
        return False, "erasing it would leave an edge behind"
    found = _source_of_copy(g, X, c)
    if found is None:
        return None, "not judged: the IT- search budget was exceeded"
    return (True, "a source exists") if found else (False, "no source of which this is a copy")


def _source_of_copy(g: G, X: set, c: str) -> Optional[bool]:
    vmap = {v.id: v for v in g.V}
    cuts = {k.id for k in g.Cut}
    order = (sorted((x for x in X if x in cuts), key=lambda x: len(ancestors(g, x)))
             + sorted(x for x in X if x in vmap) + sorted(x for x in X if x in g.nu))
    budget = [IT_MINUS_BUDGET]
    for c1 in ancestors(g, c):
        if _extend(g, X, order, 0, {}, c, c1, vmap, cuts, budget):
            return True
        if budget[0] < 0:
            return None
    return False


def _same_kind(g, x, y, vmap, cuts, X, f) -> bool:
    if x in cuts:
        return y in cuts
    if x in vmap:
        return y in vmap and vmap[x].is_generic == vmap[y].is_generic \
            and vmap[x].label == vmap[y].label
    if y not in g.nu or g.rel[x] != g.rel[y] or len(g.nu[x]) != len(g.nu[y]):
        return False
    for v, w in zip(g.nu[x], g.nu[y]):
        if (f.get(v) != w) if v in X else (v != w):
            return False
    return True


def _extend(g, X, order, i, f, c, c1, vmap, cuts, budget) -> bool:
    if i == len(order):
        return all(set(g.area.get(f[x], ())) == {f[y] for y in g.area.get(x, ())}
                   for x in order if x in cuts)
    x = order[i]
    px = g.get_context(x)
    py = c1 if px == c else f.get(px)
    if py is None:
        return False
    used = set(f.values())
    for y in sorted(g.area.get(py, ())):
        budget[0] -= 1
        if budget[0] < 0:
            return False
        if y in X or y in used or not _same_kind(g, x, y, vmap, cuts, X, f):
            continue
        f[x] = y
        if _extend(g, X, order, i + 1, f, c, c1, vmap, cuts, budget):
            return True
        del f[x]
    return False


def _vertex_ins(g: G, m: Move) -> Verdict:
    """Def 15.2 inserting a vertex (p.164, 166): an isolated vertex may be inserted in ANY context."""
    return (True, "any context") if m.target is not None else (False, "no target")


def _vertex_era(g: G, m: Move) -> Verdict:
    """Def 15.2 erasing a vertex (p.164, 166): an isolated vertex may be
    erased from ANY context. Note: this covers a GENERIC isolated vertex;
    an isolated CONSTANT vertex's erasure is properly Def 24.10's Existence
    of Constants rule (p.271), which this judge does not separately model."""
    if len(m.selection) != 1 or m.selection[0] not in {v.id for v in g.V}:
        return False, "not a single vertex"
    if edges_on(g, m.selection[0]):
        return False, "the vertex is not isolated"
    return True, "an isolated vertex, any context"


_LEGAL = {"ERA": _era, "INS": _ins, "DC+": _dc_plus, "DC-": _dc_minus, "IT+": _it_plus,
          "IT-": _it_minus, "VERTEX_INS": _vertex_ins, "VERTEX_ERA": _vertex_era}
