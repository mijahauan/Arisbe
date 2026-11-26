"""The kernel: Dau's rules as an independent judge of single steps.

Two questions are answered here, and nothing else. ``legal(g, move)`` — may this
rule be applied to this graph at this place, by Dau's stated precondition? And
``acceptable(g, move)`` / ``postconditions(g, move, h)`` — is ``h`` a result
Dau's rule licenses? Every citation is to *Mathematical Logic with Diagrams* by
definition and page.

**This module imports no engine code**, and ``tests/test_dau_kernel.py`` fails
if it ever does. Its only imports from this repository are the data model
(``egi_core_dau``), the isomorphism engine (``graph_isomorphism_engine``, for
``same_graph``) and ``egif_parser_dau`` (for the content of an insertion). The
rule engine, the interaction protocol, the closure analyser and the ligature
engine are judged by this module and so may not be consulted by it.

``same_graph`` is taken from the isomorphism engine directly (the author's
ruling, 2026-11-25) rather than through ``eg_navigation``, whose import brings
the presentation algebra, the layout's data types and a road to the closure
analyser with it. What the kernel trusts is then five modules of this
repository: the three named, ``hierarchical_index`` (every graph builds one)
and ``canonical_signature`` (the isomorphism engine's colouring).

Moved here unchanged on 2026-11-25 (calculus-conformance specification §3.1)
from the calculus property suite, where it was written as the suite's oracle:
``legal`` and its helpers from ``tests/calculus_rules.py``, the licensed results
and ``postconditions`` from ``tests/calculus_expected.py``. The suite now
imports them from here. Which engine entry point performs each rule, and which
candidate moves the suite tries, stayed in ``tests/calculus_rules.py``: the
kernel names Dau's rules, never the code that performs them.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import List, Optional, Tuple

from frozendict import frozendict

from egi_core_dau import Cut as CutEl
from egi_core_dau import Edge, RelationalGraphWithCuts, Vertex
from egif_parser_dau import parse_egif
from graph_isomorphism_engine import GraphIsomorphismEngine

G = RelationalGraphWithCuts


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


def edges_on(g: G, vid: str) -> List[str]:
    return sorted(e for e, seq in g.nu.items() if vid in seq)


def dominating_nodes(g: G) -> bool:
    """Dau Def 12.5: ctx(e) <= ctx(v) — each vertex's context is the edge's or encloses it.

    A copy, not a move: ``tests/tarski.py`` keeps its own, because the semantic
    evaluator that checks the kernel's results must not borrow from the kernel."""
    for e, seq in g.nu.items():
        chain = ancestors(g, g.get_context(e))
        if any(g.get_context(v) not in chain for v in seq):
            return False
    return True


# -- Dau's rules --------------------------------------------------------------

@dataclass(frozen=True)
class Rule:
    name: str
    cite: str
    direction: str          # "one-way" | "equivalence"
    judged: bool            # does legal() judge this rule's moves?


RULE_TABLE: Tuple[Rule, ...] = (
    Rule("ERA", "Def 15.2 erasure, p.164-165: positive contexts", "one-way", True),
    # INS is the insertion of standalone content — a closed subgraph (an isolated
    # vertex included) — which is what the protocol's INS performs. Inserting an
    # edge onto vertices already present (p.165: erasing an edge keeps its
    # vertices, V^(e) := V, and insertion is its inverse) is INS_EDGE, below.
    Rule("INS", "Def 15.2 insertion of a closed subgraph, p.164-165: negative contexts", "one-way", True),
    Rule("INS_EDGE", "Def 15.2 insertion of an edge onto existing vertices, p.165: negative contexts", "one-way", True),
    Rule("IT+", "Def 15.2 iteration, p.164, 166: no polarity condition", "equivalence", True),
    Rule("IT-", "Def 15.2 deiteration, p.164, 166", "equivalence", True),
    Rule("DC+", "Def 15.2 double cuts, p.164: any context", "equivalence", True),
    Rule("DC-", "Def 15.2 double cuts, p.164: any context", "equivalence", True),
    Rule("VERTEX_INS", "Def 15.2 inserting a vertex, p.164, 166: any context", "equivalence", True),
    Rule("VERTEX_ERA", "Def 15.2 erasing a vertex, p.164, 166: any context", "equivalence", True),
    Rule("MOVE_BRANCHES", "Lemma 16.1, p.169", "equivalence", True),
    Rule("EXTEND_LIGATURE", "Lemma 16.2, p.172", "equivalence", True),
    Rule("RETRACT_LIGATURE", "Lemma 16.3, p.173", "equivalence", True),
    Rule("REARRANGE_LIGATURE", "Def 16.4, Cor 16.5, p.174-175", "equivalence", True),
    Rule("SPLIT_VERTEX", "Def 16.6, Lemma 16.7, p.175-178", "equivalence", True),
    Rule("MERGE_VERTICES", "Def 16.6 merging, p.176", "equivalence", True),
    Rule("ORIENT_IDENTITY", "Def 12.14 orientation of an identity edge, p.138", "equivalence", False),
    Rule("LIGATURE_VERTEX", "Def 12.14 adding/removing a vertex, p.138", "equivalence", False),
    Rule("CONSTANT_IDENTITY", "Def 24.10 constant identity rule, p.271", "equivalence", True),
    Rule("CONSTANT_EXISTENCE", "Def 24.10 existence of constants, p.271", "equivalence", True),
    Rule("SEPARATE_CONSTANT", "Def 24.6, Def 24.10, p.265-271", "equivalence", False),
)
RULES = {r.name: r for r in RULE_TABLE}


@dataclass(frozen=True)
class Move:
    rule: str
    selection: Tuple[str, ...] = ()
    target: Optional[str] = None
    content: Optional[str] = None
    hooks: Tuple[Tuple[str, int], ...] = ()   # SPLIT_VERTEX: (edge id, 0-based position)


def elements(g: G) -> List[str]:
    return sorted([v.id for v in g.V] + [e.id for e in g.E] + [c.id for c in g.Cut])


def same_graph(g: G, h: G) -> bool:
    """Whether two EGIs are one graph up to the names of their elements — full
    isomorphism over every vertex, edge and cut. The same question, put to the
    same engine, as ``eg_navigation.same_graph``; asked here without importing
    that module (see the note at the top)."""
    return GraphIsomorphismEngine().test_cross_egi_isomorphism(
        g, frozenset(elements(g)), h, frozenset(elements(h))).is_isomorphic


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
    erased from ANY context. This is the GENERIC vertex's rule. An isolated
    constant vertex goes by Def 24.10's Existence of Constants rule (p.271),
    which says so of a vertex "with ρ(v) = C" and is judged by
    ``_constant_existence``; until 2026-11-26 this judge passed both, and its
    own docstring said it should not."""
    if len(m.selection) != 1 or m.selection[0] not in {v.id for v in g.V}:
        return False, "not a single vertex"
    if _constant_of(g, m.selection[0]) is not None:
        return False, ("a constant vertex is erased by the Existence of Constants "
                       "rule (Def 24.10, p.271), not by the vertex rule")
    if edges_on(g, m.selection[0]):
        return False, "the vertex is not isolated"
    return True, "an isolated vertex, any context"


def _constant_of(g: G, vid: str) -> Optional[str]:
    """ρ(v) where it is a constant name, else None (a generic vertex, ρ(v) = ∗)."""
    v = next((x for x in g.V if x.id == vid), None)
    return None if v is None or v.is_generic or not v.label else v.label


def _constant_existence(g: G, m: Move) -> Verdict:
    """Def 24.10, Existence of Constants Rule (p.271).

    "Let C be a constant name. In each context c, we may add a fresh vertex v
    with ρ(v) = C. Vice versa, if v is an isolated vertex with ρ(v) = C v may
    be erased from c."

    One rule, two directions, told apart by what the move names: a selected
    vertex is the erasure; a target context and a name (``content``, the bare
    constant name) is the insertion. No polarity condition either way."""
    if m.selection:
        if len(m.selection) != 1 or m.selection[0] not in {v.id for v in g.V}:
            return False, "the erasure names one vertex (p.271)"
        v = m.selection[0]
        if _constant_of(g, v) is None:
            return False, "ρ(v) is not a constant name; a generic vertex goes by Def 15.2 (p.166)"
        if edges_on(g, v):
            return False, "the vertex is not isolated (p.271)"
        return True, "an isolated vertex with ρ(v) = C, any context (p.271)"
    if m.target is None:
        return False, "the insertion names a context (p.271)"
    if not m.content:
        return False, "the insertion names a constant C (p.271)"
    return True, "a fresh vertex with ρ(v) = C, any context (p.271)"


def _constant_identity(g: G, m: Move) -> Verdict:
    """Def 24.10, Constant Identity Rule (p.271), as the author ruled its
    text on 2026-11-25 (the print has "ν(id) = (ve, vf)" and "into d", carried
    over from the Functional Property Rule above it):

    "Let C ∈ C be a constant name. Let v, w be vertices with ρ(v) = ρ(w) = C.
    Let c be a context with c ≤ ctx(v) and c ≤ ctx(w). Then arbitrary
    identity-links id with ν(id) = (v, w) may be inserted into c or erased
    from c."

    Two selected vertices and a target context is the insertion; one selected
    identity link is the erasure. Read with v ≠ w: the rule joins two
    vertices, and a loop on one vertex is neither offered by the engine nor
    judged legal here — a limit of this judge, not a claim about the book.
    For the erasure, c ≤ ctx(v), ctx(w) is what Def 12.5 already gives any
    edge, so the conditions that bite are the link's kind and its ends' names."""
    sel = tuple(dict.fromkeys(m.selection))
    vids = {v.id for v in g.V}
    if len(sel) == 1 and sel[0] in g.nu:
        e = sel[0]
        if g.rel.get(e) != "=" or len(set(g.nu[e])) != 2:
            return False, "not an identity link between two vertices (p.271)"
        names = {_constant_of(g, x) for x in g.nu[e]}
        if None in names or len(names) != 1:
            return False, "ρ(v) = ρ(w) = C fails for the link's ends (p.271)"
        return True, "an identity link between two vertices named C (p.271)"
    if len(sel) == 2 and set(sel) <= vids:
        v, w = sel
        if _constant_of(g, v) is None or _constant_of(g, v) != _constant_of(g, w):
            return False, "ρ(v) = ρ(w) = C fails (p.271)"
        if m.target is None:
            return False, "the insertion names a context c (p.271)"
        if g.get_context(v) not in ancestors(g, m.target) or \
                g.get_context(w) not in ancestors(g, m.target):
            return False, "c ≤ ctx(v) and c ≤ ctx(w) fails (p.271)"
        return True, "ρ(v) = ρ(w) = C and c ≤ ctx(v), ctx(w) (p.271)"
    return False, "names two vertices and a context, or one identity link (p.271)"


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

    Def 24.10 (p.270-272) again: v₂ is *erased*, so it may not carry a name
    that would be lost with it. **Where v₁ carries the same constant nothing
    is lost,** and the merge stands (the author's ruling of 2026-11-25, R2:
    Def 16.6's merge covers two vertices carrying one constant; §24.4, p.275,
    carries the Chapter 16 results over "as long as we do not change the set
    of its labels"). It is the second half of joining two lines of one name,
    after the Constant Identity Rule has linked them.
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
    if _named(g, v2) and _constant_of(g, v1) != _constant_of(g, v2):
        return False, "v₂ is erased and carries a name v₁ does not (Def 24.10, p.270)"
    return True, "an identity edge with ctx(v₁) ≥ ctx(e) = ctx(v₂) (p.176)"


_LEGAL = {"ERA": _era, "INS": _ins, "DC+": _dc_plus, "DC-": _dc_minus, "IT+": _it_plus,
          "IT-": _it_minus, "VERTEX_INS": _vertex_ins, "VERTEX_ERA": _vertex_era,
          "INS_EDGE": _ins_edge, "MOVE_BRANCHES": _move_branches,
          "CONSTANT_EXISTENCE": _constant_existence, "CONSTANT_IDENTITY": _constant_identity,
          "EXTEND_LIGATURE": _extend_ligature, "RETRACT_LIGATURE": _retract_ligature,
          "REARRANGE_LIGATURE": _rearrange_ligature, "SPLIT_VERTEX": _split_vertex,
          "MERGE_VERTICES": _merge_vertices}


# -- licensed results ----------------------------------------------------------

def _g(g, *, V, E, nu, Cut, area, rel) -> G:
    """Build a result graph. The B-min maps (spec §5.2) travel with every
    element that survives: sort and quotation are kept for surviving vertices
    and cuts.

    Neither the alphabet nor rho is passed. Both are DERIVED by the core from
    the ink it is handed (egi_core_dau.__post_init__, 2026-09-24), so anything
    passed here would be discarded; a constant travels in its own Vertex's
    ``label``/``is_generic``, which every caller below already carries across.
    This used to hand over a pruned rho and an alphabet grown by a ``_alphabet``
    helper — both now deleted rather than left in place looking load-bearing."""
    vids, cids = {v.id for v in V}, {c.id for c in Cut}
    return G(V=frozenset(V), E=frozenset(E), nu=frozendict(nu), sheet=g.sheet,
             Cut=frozenset(Cut), area=frozendict({k: frozenset(v) for k, v in area.items()}),
             rel=frozendict(rel),
             sort=frozendict({k: s for k, s in g.sort.items() if k in vids}),
             quotation=frozendict({k: q for k, q in g.quotation.items() if k in cids and q in vids}))


def remove(g: G, X) -> G:
    X = set(X)
    return _g(g, V=[v for v in g.V if v.id not in X], E=[e for e in g.E if e.id not in X],
              nu={e: s for e, s in g.nu.items() if e not in X},
              Cut=[c for c in g.Cut if c.id not in X],
              area={k: set(v) - X for k, v in g.area.items() if k not in X},
              rel={e: r for e, r in g.rel.items() if e not in X})


def insert(g: G, target: str, text: str) -> G:
    h = parse_egif(text)
    p = "ins:{}".format
    area = {k: set(v) for k, v in g.area.items()}
    area.setdefault(target, set()).update(p(x) for x in h.area.get(h.sheet, ()))
    for c in h.Cut:
        area[p(c.id)] = {p(x) for x in h.area.get(c.id, ())}
    return _g(g, V=[*g.V, *(Vertex(p(v.id), label=v.label, is_generic=v.is_generic) for v in h.V)],
              E=[*g.E, *(Edge(p(e.id)) for e in h.E)],
              nu={**g.nu, **{p(e): tuple(p(v) for v in s) for e, s in h.nu.items()}},
              Cut=[*g.Cut, *(CutEl(p(c.id)) for c in h.Cut)], area=area,
              rel={**g.rel, **{p(e): r for e, r in h.rel.items()}})


def double_cut(g: G, S, target: str) -> G:
    # A cut named with some of its contents is the subgraph of the cut alone
    # (Def 12.10, p.134): only the selection's top elements move inward.
    S = set(tops(g, expand(g, S)))
    area = {k: set(v) for k, v in g.area.items()}
    area[target] = (area.get(target, set()) - S) | {"dc:outer"}
    area["dc:outer"], area["dc:inner"] = {"dc:inner"}, S
    return _g(g, V=g.V, E=g.E, nu=g.nu, Cut=[*g.Cut, CutEl("dc:outer"), CutEl("dc:inner")],
              area=area, rel=g.rel)


def erase_double_cut(g: G, c1: str) -> G:
    (c2,) = g.area[c1]
    c0 = g.get_context(c1)
    area = {k: set(v) for k, v in g.area.items() if k not in (c1, c2)}
    area[c0] = (area[c0] - {c1}) | set(g.area.get(c2, ()))
    return _g(g, V=g.V, E=g.E, nu=g.nu, Cut=[c for c in g.Cut if c.id not in (c1, c2)],
              area=area, rel=g.rel)


def add_vertex(g: G, target: str, constant: Optional[str] = None) -> G:
    """A fresh isolated vertex in ``target``: generic, or named ``constant``."""
    area = {k: set(v) for k, v in g.area.items()}
    area.setdefault(target, set()).add("hd:new")
    new = Vertex("hd:new") if constant is None else Vertex("hd:new", label=constant, is_generic=False)
    return _g(g, V=[*g.V, new], E=g.E, nu=g.nu, Cut=g.Cut, area=area, rel=g.rel)


def add_identity_link(g: G, v: str, w: str, target: str) -> G:
    """A fresh identity link with ν(id) = (v, w) in ``target``."""
    area = {k: set(x) for k, x in g.area.items()}
    area.setdefault(target, set()).add("ci:new")
    return _g(g, V=g.V, E=[*g.E, Edge("ci:new")], nu={**g.nu, "ci:new": (v, w)}, Cut=g.Cut,
              area=area, rel={**g.rel, "ci:new": "="})


def iterate(g: G, S, target: str) -> G:
    """Copy expand(S) into target; a vertex outside the copy is reused."""
    X = expand(g, S)
    p = "it:{}".format
    vmap = {v.id: v for v in g.V}
    cuts = {c.id for c in g.Cut}
    area = {k: set(v) for k, v in g.area.items()}
    for x in X:
        if x in cuts:
            area.setdefault(p(x), set())
    for x in X:
        parent = g.get_context(x)
        area.setdefault(target if parent not in X else p(parent), set()).add(p(x))
    return _g(g, V=[*g.V, *(Vertex(p(x), label=vmap[x].label, is_generic=vmap[x].is_generic)
                         for x in X if x in vmap)],
              E=[*g.E, *(Edge(p(x)) for x in X if x in g.nu)],
              nu={**g.nu, **{p(x): tuple(p(v) if v in X else v for v in g.nu[x])
                             for x in X if x in g.nu}},
              Cut=[*g.Cut, *(CutEl(p(x)) for x in X if x in cuts)], area=area,
              rel={**g.rel, **{p(x): g.rel[x] for x in X if x in g.nu}})


def expected(g: G, m: Move) -> Optional[G]:
    """The licensed result, or None where it is not built (the ligature rules,
    split, merge): there the structure layer checks EGI-hood and maps only."""
    if m.rule in ("ERA", "VERTEX_ERA", "IT-"):
        return remove(g, expand(g, m.selection))
    if m.rule == "CONSTANT_EXISTENCE":
        return remove(g, m.selection) if m.selection else add_vertex(g, m.target, m.content)
    if m.rule == "CONSTANT_IDENTITY":
        sel = tuple(dict.fromkeys(m.selection))
        return remove(g, sel) if len(sel) == 1 else add_identity_link(g, *sel, m.target)
    if m.rule == "INS":
        return insert(g, m.target, m.content)
    if m.rule == "DC+":
        return double_cut(g, m.selection, m.target)
    if m.rule == "DC-":
        return erase_double_cut(g, m.selection[0])
    if m.rule == "VERTEX_INS":
        return add_vertex(g, m.target)
    if m.rule == "IT+":
        return iterate(g, m.selection, m.target)
    return None


def completed(g: G, S) -> set:
    """S with every vertex in ctx(S) that an edge of expand(S) reaches — the
    Def 12.10 (p.134) subgraph S generates (V_e ⊆ V′)."""
    X = expand(g, S)
    c0 = g.get_context(tops(g, X)[0])
    return set(S) | {v for e in X if e in g.nu for v in g.nu[e] if g.get_context(v) == c0}


# More completion vertices than this and the per-vertex forms are not enumerated.
MAX_REUSE_CHOICES = 12


def acceptable(g: G, m: Move) -> Optional[List[G]]:
    """Every licensed result, or None where it is not built (then the structure
    layer checks EGI-hood and maps only). IT+ chooses W_v PER VERTEX (Def 15.2, p.166: "for each vertex v ∈ W_0 let
    W_v ⊆ V be a (possibly empty) set"): each vertex of the Def 12.10
    completion that the selection itself leaves out is either copied fresh
    (W_v = ∅) or reused — iterated with W_v = {v} and the copy merged into v
    (Def 16.6 merging, p.175; Lemma 16.7). Task 10 found the engine reusing
    one line and copying the other (foaf_core); the two all-or-nothing forms
    Task 7 accepted are the extremes of this set."""
    exp = expected(g, m)
    if exp is None:
        return None
    if m.rule == "IT+":
        extra = sorted(completed(g, m.selection) - set(expand(g, m.selection)))
        if len(extra) > MAX_REUSE_CHOICES:
            # Intended: a loud abort (a crash of the run), never a silent skip —
            # no graph in either mode reaches it, and one that does must be seen.
            raise ValueError(f"{len(extra)} completion vertices: too many per-vertex forms")
        return [iterate(g, tuple(m.selection) + fresh, m.target)
                for k in range(len(extra) + 1) for fresh in itertools.combinations(extra, k)]
    if m.rule == "CONSTANT_IDENTITY" and len(set(m.selection)) == 2:
        # The rule's hypothesis is symmetric in v and w, so the link may be
        # scribed either way round.
        v, w = dict.fromkeys(m.selection)
        return [exp, add_identity_link(g, w, v, m.target)]
    return [exp]


def maps_carried(g: G, h: G) -> List[str]:
    """The B-min maps must survive the step for every element that survives.

    There is no alphabet clause, and that is a decision, not an omission. This
    held ``set(g.alphabet.R) <= set(h.alphabet.R)`` — the alphabet must never
    lose a relation name — until the alphabet stopped being stored
    (egi_core_dau, 2026-09-24: derived from the ink, never kept). Derived,
    ``h.alphabet.R`` *is* ``set(h.rel.values())``, so the clause says only
    "every name g uses, h uses too", which ERA falsifies by design the moment
    it erases a name's last edge — 1,205 of them in the default mode alone.
    The nearest true replacement, "h's alphabet equals h's own relation names",
    is true by construction of ``derive_alphabet`` and would test that function
    rather than the calculus; it is tested where it belongs, in
    ``test_alphabet_derivation.py``. So the clause is gone rather than
    weakened.

    ``rho`` stays, and means something it did not before: derived, ρ(v) is the
    label of the vertex object itself, so "a surviving vertex keeps its
    constant" is now a claim about the step's ink and not about a summary
    travelling alongside it."""
    out = []
    hv, hc = {v.id for v in h.V}, {c.id for c in h.Cut}
    rho = [v for v, c in g.rho.items() if c is not None and v in hv and h.rho.get(v) != c]
    if rho:
        out.append(f"rho lost for {len(rho)} vertex" + ("es" if len(rho) > 1 else ""))
    if [v for v, s in g.sort.items() if v in hv and h.sort.get(v) != s]:
        out.append("sort lost")
    if [c for c, q in g.quotation.items() if c in hc and h.quotation.get(c) != q]:
        out.append("quotation lost")
    return out


# The six rules with no expected form (the four ligature rules, split, merge)
# re-plumb identity and nothing else, so the non-identity-relations postcondition
# holds for all of them, and each (save REARRANGE_LIGATURE) carries its own
# element-count delta. Dau: Lemmas 16.1-16.3 and Def 16.4 (p.169-175) rewire a
# ligature; Def 16.6 (p.175-176) splits and merges. None of them adds, drops or
# re-relates a non-identity edge.
#
# REARRANGE_LIGATURE is not held to "the result differs from the source": Def
# 16.4 (p.174) replaces (W,F) with a new (W',F') realizing the SAME partition,
# and Cor 16.5 (p.175) states only that the two graphs are syntactically
# equivalent — never that F' differs from F. With a 2-vertex ligature there is
# exactly one tree connecting them, so the rearrangement is necessarily
# isomorphic to the source; that is a licensed degenerate instance of Def 16.4,
# not a no-op defect (test_rearrange_ligature_may_choose_the_same_shape). Nor
# is it held to a count delta: Def 16.4 (p.174) lets |W'|/|F'| differ from
# |W|/|F| (this engine happens to keep them equal, but nothing in Dau requires
# it) — see _rearrange_ligature_ok below for what IS required.
_IDENTITY = "="


def _relation_multiset(g: G):
    return sorted((g.rel[e], len(g.nu[e])) for e in g.nu if g.rel[e] != _IDENTITY)


def _counts(g: G):
    ids = sum(1 for e in g.nu if g.rel[e] == _IDENTITY)
    return len(g.V), ids


def _rearrange_ligature_ok(g: G, m: Move, h: G) -> List[str]:
    """Def 16.4 (p.174) touches one ligature (W,F) in one context and leaves
    the rest of the graph alone; Cor 16.5 (p.175) licenses any reshape of it
    "as long as it keeps connected" — not "must differ" (exempted above) and
    not "same counts" (Def 16.4 lets |W'|/|F'| differ). What IS required, and
    checked here independently of the engine's own partition self-check
    (ligature_manipulation_rules.py:708-720, "the instrument's job" per
    review): the whole-graph co-denotation partition (Dau's ligatures, as
    connected components of identity edges) is unchanged, and every
    non-identity hook that sat on a vertex of the touched ligature still sits
    on a vertex of it (Def 16.4: an edge on w "is now connected to a vertex
    w' of the new ligature" — some vertex of it, not necessarily the same
    one, since every vertex of a ligature co-denotes)."""
    problems: List[str] = []
    g_partition = frozenset(frozenset(c) for c in g.get_ligatures())
    h_partition = frozenset(frozenset(c) for c in h.get_ligatures())
    if g_partition != h_partition:
        problems.append("rearrangement changed the co-denotation partition (Def 16.4, "
                        "p.174; Cor 16.5, p.175: 'as long as it keeps connected')")
        return problems
    if not m.selection:
        return problems
    v0 = m.selection[0]
    W = next((c for c in g_partition if v0 in c), frozenset())
    stray = [e for e in g.nu if g.rel.get(e) != _IDENTITY and any(v in W for v in g.nu[e])
             and not (e in h.nu and any(v in W for v in h.nu[e]))]
    if stray:
        problems.append(f"rearrangement moved {len(stray)} non-identity hook"
                        + ("s" if len(stray) > 1 else "") +
                        " off the ligature (Def 16.4, p.174: a hook on the ligature "
                        "lands on a vertex of the new one)")
    return problems


def postconditions(g: G, m: Move, h: G) -> List[str]:
    """What must hold of a rule whose licensed result the suite does not build.
    Returns the problems; empty means the result satisfies every one."""
    problems: List[str] = []
    if m.rule != "REARRANGE_LIGATURE" and same_graph(g, h):
        problems.append("the move reports success and changes nothing")
    if _relation_multiset(g) != _relation_multiset(h):
        problems.append("the non-identity relations changed: these rules re-plumb "
                        "identity only (Lemmas 16.1-16.3, Def 16.4, Def 16.6)")
    (v0, i0), (v1, i1) = _counts(g), _counts(h)
    if m.rule == "SPLIT_VERTEX" and (v1 - v0, i1 - i0) != (1, 1):
        problems.append(f"split must add +1 vertex and +1 identity edge (Def 16.6, p.175), "
                        f"got {v1 - v0:+d} vertex and {i1 - i0:+d} identity edge")
    if m.rule == "MERGE_VERTICES" and (v1 - v0, i1 - i0) != (-1, -1):
        problems.append(f"merge must drop 1 vertex and 1 identity edge (Def 16.6, p.176), "
                        f"got {v1 - v0:+d} vertex and {i1 - i0:+d} identity edge")
    if m.rule == "MOVE_BRANCHES" and (v1, i1) != (v0, i0):
        problems.append(f"moving a branch changes no counts (Lemma 16.1, p.169), "
                        f"got {v1 - v0:+d} vertex and {i1 - i0:+d} identity edge")
    # Lemma 16.3 (p.173) admits the degenerate case W = {w0} (nothing to
    # retract); Lemma 16.2 (p.172) admits V' = ∅ with a loop added instead of
    # a fresh vertex. Neither is reachable through this engine today
    # (RetractLigatureRule refuses fewer than 2 selected vertices;
    # ExtendRestrictLigatureRule always adds exactly 2 vertices and 2 identity
    # edges), so a future engine change implementing either is not to be read
    # as failing these clauses without revisiting them.
    if m.rule == "RETRACT_LIGATURE" and not (v1 < v0 and i1 < i0):
        problems.append(f"retraction collapses a ligature to one vertex (Lemma 16.3, p.173): "
                        f"fewer vertices and fewer identity edges, got {v1 - v0:+d} and {i1 - i0:+d}")
    if m.rule == "EXTEND_LIGATURE" and not (v1 > v0 and i1 > i0):
        problems.append(f"extension adds vertices and identity edges (Lemma 16.2, p.172), "
                        f"got {v1 - v0:+d} and {i1 - i0:+d}")
    if m.rule == "REARRANGE_LIGATURE":
        problems += _rearrange_ligature_ok(g, m, h)
    return problems


# -- checking one step (calculus-conformance specification §3.2) ---------------

# The rules whose licensed result is not built, so ``postconditions`` carries
# the check instead.
POSTCONDITION_RULES = frozenset({
    "MOVE_BRANCHES", "EXTEND_LIGATURE", "RETRACT_LIGATURE", "REARRANGE_LIGATURE",
    "SPLIT_VERTEX", "MERGE_VERTICES",
})

ACCEPTED, REJECTED, UNJUDGED = "accepted", "rejected", "unjudged"


@dataclass(frozen=True)
class StepCheck:
    status: str      # ACCEPTED | REJECTED | UNJUDGED
    why: str


def check_step(g: G, m: Move, h: G) -> StepCheck:
    """Is ``h`` what Dau's rule ``m`` makes of ``g``?

    ACCEPTED iff ``legal(g, m)`` holds and ``h`` is ``same_graph`` to one of the
    licensed results — or, for the six rules whose result is not built,
    ``postconditions(g, m, h)`` finds nothing. REJECTED when the move is not
    legal or the result is not a licensed one. UNJUDGED when the kernel cannot
    say: ``legal`` abstains, or no check of the result exists for the rule. An
    unjudged step is not a certified one.
    """
    verdict, why = legal(g, m)
    if verdict is None:
        return StepCheck(UNJUDGED, why)
    if not verdict:
        return StepCheck(REJECTED, f"not a legal {m.rule}: {why}")
    problems: List[str] = []
    if not dominating_nodes(h):
        problems.append("the result is not an EGI (Def 12.5)")
    problems += maps_carried(g, h)
    try:
        forms = acceptable(g, m)
    except ValueError as exc:
        return StepCheck(UNJUDGED, f"not judged: {exc}")
    if forms is None:
        if m.rule not in POSTCONDITION_RULES:
            return StepCheck(UNJUDGED, f"not judged: no licensed result is built for {m.rule}")
        problems += postconditions(g, m, h)
    elif not any(same_graph(f, h) for f in forms):
        problems.append("the result differs from the licensed change")
    if problems:
        return StepCheck(REJECTED, "; ".join(problems))
    return StepCheck(ACCEPTED, why)
