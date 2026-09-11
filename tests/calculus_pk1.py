"""P-K1: does colore_field's EGIF round trip change its meaning, and is a line
placed above its uses the reason? See the plan, Task 3, for the procedure.

Precondition added after the first run (2026-09-10 fix round 1): the search
below assumes GA/GB are well-formed EGIs. The first run found that
assumption false — colore_field's own *stored* graph violates Dau's
dominating-nodes law (Def 12.5) independent of any round trip, so
``satisfies`` refused before a single structure could be tried. A corpus
census (controller, independent of this module) confirms colore_field is
one of exactly two non-EGI graphs in the whole corpus (the other is
bfo_core) and that both are exactly the round-trip residue tracked in
``test_tomos_parsing.KNOWN_BROKEN`` — so the pre-registered "lines above
their uses" diagnosis was wrong; the true defect is a precondition failure,
not a meaning-changing round trip. ``pk1()`` now checks
``tarski.dominating_nodes(g)`` immediately after loading ``g`` and, if it
fails, reports the violation directly (component/line counts are reported
as zero in that branch — they depend on machinery, e.g. ``sheet_components``
and matching against ``back``, that has not run yet at that point) instead
of running the unchanged search into the same crash. The search itself
(everything below the precondition check) is untouched from the
pre-registered operationalization.
"""
from __future__ import annotations

from pathlib import Path

from frozendict import frozendict

import eg_navigation as nav
from calculus_enum import TOMOS, ancestors, edges_on, graph_key, lca, line_above_uses
from egif_generator_dau import generate_egif
from egif_parser_dau import parse_egif
from tarski import dominating_nodes, restrict, satisfies, sheet_components, universe, vocabulary
from tomos_service import TomosService

SIZES = (1, 2, 3)
CAP, SAMPLES, SEED = 12, 4000, 20260910


def _def_12_5_violations(g):
    """(edge, vertex) pairs and distinct vertices violating Dau Def 12.5:
    ctx(v) must be ctx(e) or an ancestor of it, for every v in nu[e]."""
    pairs = []
    vertices = set()
    for e, seq in g.nu.items():
        chain = ancestors(g, g.get_context(e))
        for v in seq:
            if g.get_context(v) not in chain:
                pairs.append((e, v))
                vertices.add(v)
    return pairs, vertices


def _match(ga, comps_a, gb, comps_b):
    """Pair components by isomorphism; return the unmatched ids of each side."""
    free_b = list(comps_b)
    unmatched_a = []
    for ca in comps_a:
        sa = restrict(ga, ca)
        hit = next((cb for cb in free_b
                    if graph_key(restrict(gb, cb)) == graph_key(sa)
                    and nav.same_graph(sa, restrict(gb, cb))), None)
        if hit is None:
            unmatched_a.append(ca)
        else:
            free_b.remove(hit)
    return unmatched_a, free_b


def _moved_down(g, vid):
    """g with vertex ``vid`` moved to the least common area of its uses."""
    old = g.get_context(vid)
    new = lca(g, [g.get_context(e) for e in edges_on(g, vid)])
    area = dict(g.area)
    area[old] = area[old] - {vid}
    area[new] = area.get(new, frozenset()) | {vid}
    return type(g)(V=g.V, E=g.E, nu=g.nu, sheet=g.sheet, Cut=g.Cut,
                   area=frozendict(area), rel=g.rel)


def pk1() -> dict:
    g = TomosService(Path(TOMOS)).load_uod("colore_field", attest=False).current_egi
    viol_pairs, viol_vertices = _def_12_5_violations(g)
    if viol_pairs:
        back = parse_egif(generate_egif(g))
        return dict(
            components_g=0, components_back=0, unmatched_g=0, unmatched_back=0,
            lines_above_uses=0, lines_in_unmatched=0, structures_tried=0, separating=0,
            attributed=0, attributed_lines=[], whole_graph_confirmed=0,
            stored_graph_is_egi=False,
            def_12_5_violations=len(viol_pairs),
            def_12_5_vertices=len(viol_vertices),
            back_is_egi=dominating_nodes(back),
            outcome="REFUTED: premise — colore_field is not an EGI (Def 12.5); "
                    "the round trip repairs it",
        )
    back = parse_egif(generate_egif(g))
    cg, cb = sheet_components(g), sheet_components(back)
    ua, ub = _match(g, cg, back, cb)
    ids_a = frozenset().union(*ua) if ua else frozenset()
    ids_b = frozenset().union(*ub) if ub else frozenset()
    GA, GB = restrict(g, ids_a), restrict(back, ids_b)
    M = restrict(g, frozenset(x for c in cg if c not in ua for x in c))
    lines = sorted(v.id for v in g.V if v.is_generic and line_above_uses(g, v.id))
    in_a = [v for v in lines if v in ids_a]
    out = dict(components_g=len(cg), components_back=len(cb), unmatched_g=len(ua),
               unmatched_back=len(ub), lines_above_uses=len(lines),
               lines_in_unmatched=len(in_a), structures_tried=0, separating=0,
               attributed=0, attributed_lines=[], whole_graph_confirmed=0,
               stored_graph_is_egi=True)
    moved = {v: _moved_down(GA, v) for v in in_a}
    rels, consts = vocabulary(GA, GB, M)
    for n in SIZES:
        structures, _ = universe(rels, consts, n, cap=CAP, sample_n=SAMPLES, seed=SEED)
        for s in structures:
            out["structures_tried"] += 1
            a, b = satisfies(GA, s), satisfies(GB, s)
            if a == b:
                continue
            out["separating"] += 1
            who = [v for v, h in moved.items() if satisfies(h, s) == b]
            if who:
                out["attributed"] += 1
                out["attributed_lines"] = sorted(set(out["attributed_lines"]) | set(who))
                if satisfies(M, s):
                    out["whole_graph_confirmed"] += 1
    if out["attributed"]:
        out["outcome"] = "HELD"
    elif out["separating"]:
        out["outcome"] = "REFUTED: separation not attributed"
    else:
        out["outcome"] = "REFUTED: no separation found at this budget"
    return out
