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
    DauRule("INS_EDGE", "Def 15.2 insertion of an edge onto existing vertices, p.165: negative contexts", "one-way", "protocol:INS", True),
    DauRule("IT+", "Def 15.2 iteration, p.164, 166: no polarity condition", "equivalence", "protocol:IT+", True),
    DauRule("IT-", "Def 15.2 deiteration, p.164, 166", "equivalence", "protocol:IT-", True),
    DauRule("DC+", "Def 15.2 double cuts, p.164: any context", "equivalence", "protocol:DC+", True),
    DauRule("DC-", "Def 15.2 double cuts, p.164: any context", "equivalence", "protocol:DC-", True),
    DauRule("VERTEX_INS", "Def 15.2 inserting a vertex, p.164, 166: any context", "equivalence", "engine:HEAVY_DOT", True),
    DauRule("VERTEX_ERA", "Def 15.2 erasing a vertex, p.164, 166: any context", "equivalence", "protocol:ERA", True),
    DauRule("MOVE_BRANCHES", "Lemma 16.1, p.169", "equivalence", "ligature:MOVE_BRANCHES", True),
    DauRule("EXTEND_LIGATURE", "Lemma 16.2, p.172", "equivalence", "ligature:EXTEND_LIGATURE", True),
    DauRule("RETRACT_LIGATURE", "Lemma 16.3, p.173", "equivalence", "ligature:RETRACT_LIGATURE", True),
    DauRule("REARRANGE_LIGATURE", "Def 16.4, Cor 16.5, p.174-175", "equivalence", "ligature:REARRANGE_LIGATURE", True),
    DauRule("SPLIT_VERTEX", "Def 16.6, Lemma 16.7, p.175-178", "equivalence", "split", True),
    DauRule("MERGE_VERTICES", "Def 16.6 merging, p.176", "equivalence", "merge", True),
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
        # Dau's vertex rule is about vertices; an edge offered here would be
        # performed by the ERA entry point and read as applied-but-illegal.
        for x in sorted(v.id for v in g.V):
            yield Move(rule, (x,))
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
    (Def 12.7, p.126). So the content may not use a name at an arity the host's
    own edges already give it (Task 10: tier B's dau_2006_p112_ligature,
    ``*x (P x) ~[ (Q x) (R x) ]``, uses R unary).

    This consulted ``g.alphabet`` first and fell back to the edges. Since
    2026-09-24 the alphabet is derived from those same edges, so the two
    branches read one fact twice; the edges are kept because they are the fact,
    and legal() is left owing the core nothing but the ink."""
    try:
        h = parse_egif(m.content or "")
    except Exception:
        return False, "the content does not parse"
    if m.target is None or positive(g, m.target):
        return False, "the target is not a negative context"
    arity = {}
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


def _ins_edge(g: G, m: Move) -> Verdict:
    """Def 15.2 insertion, p.165: erasing an edge keeps its vertices
    (V^(e) := V), so its inverse inserts an edge onto vertices already
    present, in a negative context. The selection names those vertices; the
    content is the edge, written with the host's bound label."""
    if m.target is None or positive(g, m.target):
        return False, "the target is not a negative context"
    if len(m.selection) != 1 or m.selection[0] not in {v.id for v in g.V}:
        return False, "select the existing vertex the edge hooks onto"
    v = m.selection[0]
    if g.get_context(v) not in ancestors(g, m.target):
        return False, "the vertex's context must enclose the target (Def 12.5)"
    return True, "an edge onto an existing line, negative context"


def theta(g: G, v: str, w: str, without: Optional[str] = None) -> bool:
    """Def 15.1 (Θ, p.163), stated here from the book, not from the engine.

    "vΘw iff there exist vertices v1, ..., vn (n ∈ N) with 1. either v = v1
    and vn = w, or w = v1 and vn = v, 2. ctx(v1) ≥ ctx(v2) ≥ ... ≥ ctx(vn),
    and 3. for each i = 1, ..., n − 1, there exists an identity edge
    ei = {vi, vi+1} between vi and vi+1 with ctx(ei) = ctx(vi+1)."

    Clause 3 is what distinguishes Θ from bare `=`-connectivity: an identity
    edge may lawfully lie DEEPER than the vertices it joins (Def 12.5, p.125,
    asks only that each vertex's context enclose the edge's), but there it
    asserts an identity under a cut rather than wiring two spots into one
    ligature, and Θ does not hold. Clause 2 makes each chain run inward, so
    the two orientations of clause 1 are separate claims — Dau notes Θ is
    reflexive and symmetric but not transitive (p.163).

    ``without`` sets one identity edge aside, which is how Lemma 16.1's side
    condition is asked: does the join survive the hook about to be moved?
    """
    return _theta_one_way(g, v, w, without) or _theta_one_way(g, w, v, without)


def _theta_one_way(g: G, start: str, goal: str, without: Optional[str]) -> bool:
    if start == goal:
        return True                      # n = 1
    seen, stack = {start}, [start]
    while stack:
        cur = stack.pop()
        for e, seq in sorted(g.nu.items()):
            if e == without or g.rel.get(e) != "=" or len(seq) != 2 or cur not in seq:
                continue
            nxt = seq[1] if seq[0] == cur else seq[0]
            if nxt in seen or g.get_context(e) != g.get_context(nxt):
                continue                 # clause 3
            if g.get_context(cur) not in ancestors(g, g.get_context(nxt)):
                continue                 # clause 2: ctx(v_i) >= ctx(v_i+1)
            if nxt == goal:
                return True
            seen.add(nxt)
            stack.append(nxt)
    return False


def _move_branches(g: G, m: Move) -> Verdict:
    """Lemma 16.1 (Moving Branches along a Ligature in a Context, p.169-171).

    "Let va, vb be two vertices with c := ctx(va) = ctx(vb) and vaΘvb, and let
    e be an edge such that the hook (e, i) is attached to va. Let G' be
    obtained from G by replacing va by vb on the hook (e, i). Then G and G'
    are syntactically equivalent."

    Three conditions, all on the selection: two vertices, one context, Θ.
    The lemma names no target — the context is fixed by ctx(va) = ctx(vb) —
    so a target cannot make the move illegal, and every target offered for one
    selection reads alike.

    A fourth condition comes from the proof (p.170-171), which deiterates a
    copy of vb against a vaΘvb that must still hold once the hook has moved:
    the hook moved may not sit on the join's only witness. The lemma says only
    "an edge e", so this asks whether SOME hook on either vertex qualifies —
    which is the same question the move itself is, since the selection does
    not name the hook.
    """
    vs = {v.id for v in g.V}
    if len(set(m.selection)) != 2 or not set(m.selection) <= vs:
        return False, "Lemma 16.1 is stated for two vertices (p.169)"
    va, vb = m.selection
    if g.get_context(va) != g.get_context(vb):
        return False, "the two vertices are not in one context: c := ctx(va) = ctx(vb) (p.169)"
    if not theta(g, va, vb):
        return False, "vaΘvb fails (Def 15.1, p.163: ctx(e_i) = ctx(v_i+1))"
    for src, dst in ((va, vb), (vb, va)):
        for e in edges_on(g, src):
            if theta(g, src, dst, without=e):
                return True, "two vertices, one context, vaΘvb, and a hook to move"
    return False, "every hook sits on the join's only witness (Lemma 16.1's proof, p.170-171)"


# --- the ligature and vertex rules (Lemmas 16.2-16.3, Defs 16.4/16.6) --------
#
# Written 2026-09-20. Until then these five were `judged=False`: legal() abstained,
# so the refusal layer scored none of their moves and only the soundness layer
# judged them at all. MOVE_BRANCHES sat in exactly that blind spot with an unsound
# move inside it for a whole arc, and was caught only by a 2.5-hour exhaustive
# sweep at the end. "The layers are quiet" is a question, not an answer.


def _ligature_vertices(g: G, m: Move, least: int) -> Optional[Tuple[str, ...]]:
    """The selection as vertices, or None if it is not `least`-or-more of them."""
    vs = {v.id for v in g.V}
    sel = tuple(dict.fromkeys(m.selection))
    if len(sel) < least or not set(sel) <= vs:
        return None
    return sel


def _identity_edges_within(g: G, W: set) -> List[str]:
    """Every identity edge both of whose ends lie in ``W`` — the ligature's F."""
    return [e for e in sorted(g.nu)
            if g.rel.get(e) == "=" and set(g.nu[e]) <= W and len(set(g.nu[e])) > 1]


def _connected_by_identity(g: G, W: Tuple[str, ...]) -> bool:
    """Is ``W`` one ligature — connected through identity edges among its own?"""
    F = _identity_edges_within(g, set(W))
    seen, stack = {W[0]}, [W[0]]
    while stack:
        cur = stack.pop()
        for e in F:
            ends = set(g.nu[e])
            if cur in ends:
                for w in ends - seen:
                    seen.add(w)
                    stack.append(w)
    return seen >= set(W)


def _named(g: G, vid: str) -> bool:
    v = next(x for x in g.V if x.id == vid)
    return not v.is_generic and bool(v.label)


def _extend_ligature(g: G, m: Move) -> Verdict:
    """Lemma 16.2 (Extending or Restricting a Ligature in a Context, p.172).

    "Let a EGI 𝔊 be given with a vertex v. Let V' be a set of fresh vertices and
    E' be a set of fresh edges ... obtained from 𝔊 such that all fresh vertices
    and edges are placed in the context ctx(v), and all fresh edges are identity
    edges between the vertices of {v} ⊍ V' such that we have vΘv' for each
    v' ∈ V'. Then 𝔊 and 𝔊' are syntactically equivalent."

    The lemma's only precondition on the *source* is that v be a vertex: every
    other clause governs what is built, which is the structure layer's business,
    not legality. In particular Dau does **not** require v to lie on an existing
    ligature — a lone vertex is a ligature of one, and the lemma extends it.
    The target names no context (ctx(v) fixes it), so it cannot make the move
    illegal.
    """
    sel = _ligature_vertices(g, m, 1)
    if sel is None or len(sel) != 1:
        return False, "Lemma 16.2 extends at one vertex v (p.172)"
    return True, "a vertex v: fresh material goes in ctx(v) with vΘv' (p.172)"


def _retract_ligature(g: G, m: Move) -> Verdict:
    """Lemma 16.3 (Retracting a Ligature in a Context, p.173).

    "Let (W,F) be a ligature which is placed in a context c, i.e., ctx(w) = c =
    ctx(f) for all w ∈ W and f ∈ F, and let w₀ ∈ W ... all vertices of W\\{w₀}
    and all edges of F are removed from c."

    Three conditions, all on the selection: W is two or more vertices; they are
    one connected ligature; and the **whole** ligature sits in one context —
    *edges included*, which is the clause an earlier arc found the engine
    ignoring (it collapsed along an identity edge deeper than both its vertices).

    A fourth comes from Def 24.10 (p.270-272): W\\{w₀} is *erased*, and these
    rules never erase a name. The lemma says only "let w₀ ∈ W", so it asks
    whether SOME survivor works — which leaves at most one named vertex in W.
    """
    sel = _ligature_vertices(g, m, 2)
    if sel is None:
        return False, "Lemma 16.3 retracts a ligature of two or more vertices (p.173)"
    if not _connected_by_identity(g, sel):
        return False, "the selection is not one connected ligature (p.173)"
    ctxs = {g.get_context(w) for w in sel}
    if len(ctxs) != 1:
        return False, "the vertices are not in one context: ctx(w) = c (p.173)"
    c = ctxs.pop()
    for e in _identity_edges_within(g, set(sel)):
        if g.get_context(e) != c:
            return False, "an identity edge lies outside c: ctx(f) = c fails (p.173)"
    if sum(1 for w in sel if _named(g, w)) > 1:
        return False, "no w₀ leaves W\\{w₀} nameless — erasing would take a name (Def 24.10, p.270)"
    return True, "a connected ligature, vertices and edges in one context, a lawful w₀"


def _rearrange_ligature(g: G, m: Move) -> Verdict:
    """Definition 16.4 / Corollary 16.5 (Rearranging Ligatures in a Context,
    p.174-175).

    "Let (W,F) be a ligature which is placed in a context c, i.e., ctx(w) = c =
    ctx(f) for all w ∈ W and f ∈ F ... The ligature (W,F) is replaced by a new
    ligature (W',F')." Cor 16.5: the result is syntactically equivalent, and the
    text summarises it as "A ligature in a context may be arbitrarily changed,
    as long as it keeps connected."

    Same precondition as Lemma 16.3 — it is proved by retracting then extending
    — so the same three clauses, and **no more**. In particular a constant in W
    does *not* make the move illegal: Cor 16.5 gives syntactic equivalence, so
    the replacement ligature still carries the name. Keeping the name is a
    postcondition on the result, not a precondition on the move. (A first draft
    of this oracle read Def 24.10 as forbidding a named vertex here and scored 8
    tier-A applications as SEVERE; the engine was right and the oracle was
    wrong — `*x (= x "a")` rearranges to `*x (= "a" x)`, which loses nothing.)
    """
    sel = _ligature_vertices(g, m, 2)
    if sel is None:
        return False, "Def 16.4 rearranges a ligature of two or more vertices (p.174)"
    if not _connected_by_identity(g, sel):
        return False, "the selection is not one connected ligature (p.174)"
    ctxs = {g.get_context(w) for w in sel}
    if len(ctxs) != 1:
        return False, "the vertices are not in one context: ctx(w) = c (p.174)"
    c = ctxs.pop()
    for e in _identity_edges_within(g, set(sel)):
        if g.get_context(e) != c:
            return False, "an identity edge lies outside c: ctx(f) = c fails (p.174)"
    return True, "a connected ligature wholly placed in one context (p.174)"


def _split_vertex(g: G, m: Move) -> Verdict:
    """Definition 16.6 (Splitting a Vertex, p.175-176).

    "Let v be a vertex in the context c₀ attached to hooks (e₁,i₁),…,(eₙ,iₙ),
    placed in contexts c₁,…,cₙ. Let c be a context such that c₁,…,cₙ ≤ c ≤ c₀.
    Then ... In c, a new vertex v' and a new identity-link between v and v' is
    inserted. On the hooks (e₁,i₁),…,(eₙ,iₙ), v is replaced by v'."

    The hooks are "some (not necessarily all)" of v's, so any non-empty subset
    of them is Dau's domain. The whole precondition is the sandwich on c: the
    target context must be enclosed by (or equal to) ctx(v), and must enclose
    (or equal) the context of every hook's edge.
    """
    if len(m.selection) != 1 or m.selection[0] not in {v.id for v in g.V}:
        return False, "Def 16.6 splits one vertex v (p.175)"
    v = m.selection[0]
    if not m.hooks:
        return False, "Def 16.6 moves at least one hook (p.175)"
    for e, i in m.hooks:
        if e not in g.nu or i >= len(g.nu[e]) or g.nu[e][i] != v:
            return False, "a named hook is not attached to v (p.175)"
    if m.target is None or m.target not in all_areas(g):
        return False, "the target is not a context"
    if g.get_context(v) not in ancestors(g, m.target):
        return False, "c ≤ c₀ fails: the target is not enclosed by ctx(v) (p.175)"
    for e, _i in m.hooks:
        if m.target not in ancestors(g, g.get_context(e)):
            return False, "cₖ ≤ c fails: a hook's edge is not enclosed by the target (p.175)"
    return True, "c₁,…,cₙ ≤ c ≤ c₀ — Def 16.6's sandwich holds (p.175)"


def _merge_vertices(g: G, m: Move) -> Verdict:
    """Definition 16.6 (Merging two Vertices, p.176).

    "Let e ∈ E^id be an identity edge with ν(e) = (v₁, v₂) such that ctx(v₁) ≥
    ctx(e) = ctx(v₂). Then v₂ may be merged into v₁, i.e., v₂ and e are erased
    and, for every edge e ∈ E, e|ᵢ = v₁ is replaced by e|ᵢ = v₂."

    ``ctx(e) ≤ ctx(v₁)`` is already guaranteed by Def 12.5 for any EGI, so the
    clause that bites is **ctx(e) = ctx(v₂)**: the identity edge must sit in the
    very context of the vertex being merged away. Collapsing along an edge
    deeper than its vertices is what an earlier arc found the engine doing.

    Def 24.10 (p.270-272) again: v₂ is *erased*, so it may not carry a name.
    """
    sel = tuple(dict.fromkeys(m.selection))
    if len(sel) != 3:
        return False, "Def 16.6 merging names v₁, v₂ and the identity edge e (p.176)"
    v1, v2, e = sel
    if e not in g.nu or g.rel.get(e) != "=" or len(set(g.nu[e])) != 2:
        return False, "e is not a two-ended identity edge (p.176)"
    if {v1, v2} != set(g.nu[e]):
        return False, "v₁ and v₂ are not e's own ends (p.176)"
    if g.get_context(e) != g.get_context(v2):
        return False, "ctx(e) = ctx(v₂) fails — the edge is not in v₂'s context (p.176)"
    if g.get_context(e) not in ancestors(g, g.get_context(e)) or \
            g.get_context(v1) not in ancestors(g, g.get_context(e)):
        return False, "ctx(v₁) ≥ ctx(e) fails (p.176)"
    if _named(g, v2):
        return False, "v₂ is erased and carries a name (Def 24.10, p.270)"
    return True, "an identity edge with ctx(v₁) ≥ ctx(e) = ctx(v₂) (p.176)"


_LEGAL = {"ERA": _era, "INS": _ins, "DC+": _dc_plus, "DC-": _dc_minus, "IT+": _it_plus,
          "IT-": _it_minus, "VERTEX_INS": _vertex_ins, "VERTEX_ERA": _vertex_era,
          "INS_EDGE": _ins_edge, "MOVE_BRANCHES": _move_branches,
          "EXTEND_LIGATURE": _extend_ligature, "RETRACT_LIGATURE": _retract_ligature,
          "REARRANGE_LIGATURE": _rearrange_ligature, "SPLIT_VERTEX": _split_vertex,
          "MERGE_VERTICES": _merge_vertices}
