"""What each rule should produce, built from the data model directly
(spec 2026-09-10 §5.2). No rule module is imported."""
from __future__ import annotations

from typing import List, Optional

from frozendict import frozendict

from calculus_rules import Move, expand, tops
from egi_core_dau import Cut as CutEl
from egi_core_dau import Edge, RelationalGraphWithCuts, Vertex
from egif_parser_dau import parse_egif

G = RelationalGraphWithCuts


def _g(g, *, V, E, nu, Cut, area, rel) -> G:
    return G(V=frozenset(V), E=frozenset(E), nu=frozendict(nu), sheet=g.sheet,
             Cut=frozenset(Cut), area=frozendict({k: frozenset(v) for k, v in area.items()}),
             rel=frozendict(rel))


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
    """The licensed result, or None where only postconditions are checked."""
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


def acceptable(g: G, m: Move) -> Optional[List[G]]:
    """Every licensed result, or None where only postconditions are checked.
    IT+ has two: the copy attached to the reused outer lines (iteration with
    W_v = {v} then a merge, Def 16.6 p.175), and Dau's literal iteration of
    the Def 12.10 completion with W_v = ∅ (Def 15.2, p.166)."""
    exp = expected(g, m)
    if exp is None:
        return None
    if m.rule == "IT+":
        return [exp, iterate(g, tuple(completed(g, m.selection)), m.target)]
    return [exp]


def maps_carried(g: G, h: G) -> List[str]:
    """The B-min maps must survive the step for every element that survives."""
    out = []
    if g.alphabet is not None:
        if h.alphabet is None:
            out.append("alphabet dropped")
        elif not set(g.alphabet.R) <= set(h.alphabet.R):
            out.append("alphabet lost relation names")
    hv, hc = {v.id for v in h.V}, {c.id for c in h.Cut}
    rho = [v for v, c in g.rho.items() if c is not None and v in hv and h.rho.get(v) != c]
    if rho:
        out.append(f"rho lost for {len(rho)} vertex" + ("es" if len(rho) > 1 else ""))
    if [v for v, s in g.sort.items() if v in hv and h.sort.get(v) != s]:
        out.append("sort lost")
    if [c for c, q in g.quotation.items() if c in hc and h.quotation.get(c) != q]:
        out.append("quotation lost")
    return out
