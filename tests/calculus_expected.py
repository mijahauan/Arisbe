"""What each rule should produce, built from the data model directly
(spec 2026-09-10 §5.2). No rule module is imported."""
from __future__ import annotations

import itertools
from typing import List, Optional

from frozendict import frozendict

import eg_navigation as nav
from calculus_rules import Move, expand, tops
from egi_core_dau import Cut as CutEl
from egi_core_dau import Edge, RelationalGraphWithCuts, Vertex
from egif_parser_dau import parse_egif

G = RelationalGraphWithCuts


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


def add_vertex(g: G, target: str) -> G:
    area = {k: set(v) for k, v in g.area.items()}
    area.setdefault(target, set()).add("hd:new")
    return _g(g, V=[*g.V, Vertex("hd:new")], E=g.E, nu=g.nu, Cut=g.Cut, area=area, rel=g.rel)


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
    if m.rule != "REARRANGE_LIGATURE" and nav.same_graph(g, h):
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
