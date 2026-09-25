"""Per-record checks, one per layer (spec 2026-09-10 §5). Each returns
(label, detail): the label is counted; detail is None on a pass."""
from __future__ import annotations

from typing import Callable, Dict, Optional, Tuple

import eg_navigation as nav
from calculus_expected import acceptable, maps_carried, postconditions
from calculus_rules import RULES
from tarski import dominating_nodes, model_set, universe, vocabulary

Check = Callable[[object, dict], Tuple[str, Optional[str]]]

# The rules whose licensed result is not built, so postconditions carry the
# check instead (spec 2026-09-12 §3.1).
POSTCONDITION_RULES = frozenset({
    "MOVE_BRANCHES", "EXTEND_LIGATURE", "RETRACT_LIGATURE", "REARRANGE_LIGATURE",
    "SPLIT_VERTEX", "MERGE_VERTICES",
})


# legal()'s abstentions, tagged so the extent shows which reason grew
# (spec 2026-09-12 §3.4). The order is longest-match-first; an unrecognised
# reason is tagged "other", which the tests pin at 0.
_ABSTENTIONS = (
    ("underdetermine", "underdetermined"),
    ("quotation-bearing graph", "quotation-bearing"),
    ("quotation apparatus", "quotation-apparatus"),
    ("Θ clause", "theta-clause"),
    ("search budget", "search-budget"),
    ("not an EGI", "not-an-EGI"),
)


def _abstention(why: str) -> str:
    for needle, tag in _ABSTENTIONS:
        if needle in why:
            return tag
    return "other"


def _refused(out) -> str:
    """A move that did not apply: the core's Def 12.5 refusal is kept apart
    from the engine's own."""
    return "core-refused-non-egi" if out.core_refused_non_egi else "refused"


def refusal(rec, cache) -> Tuple[str, Optional[str]]:
    """§5.1: engine (applied/refused) against legal (true/false). A crash is
    a defect whatever the rule; a not-judged instance is counted, not scored."""
    out = rec.outcome
    if out.core_refused_non_egi:
        # The core would not build the engine's result (Def 12.5). Counted
        # under its own label; on a move legal() judges legal it still fails.
        label = f"not:{rec.move.rule}:core-refused-non-egi"
        if rec.verdict is True:
            return label, (f"INCOMPLETE refused but legal ({rec.why}); the core refused "
                           f"the engine's result as a non-EGI: {out.message[:120]}")
        return label, None
    if out.crashed:
        return f"{rec.move.rule}:crash", f"CRASH {out.message[:160]}"
    if rec.verdict is None:
        return f"not:{rec.move.rule}:{_abstention(rec.why)}", None
    label = f"{rec.move.rule}:{'applied' if out.applied else 'refused'}/" \
            f"{'legal' if rec.verdict else 'illegal'}"
    if out.applied and not rec.verdict:
        return label, f"SEVERE applied but illegal — legal says: {rec.why}"
    if not out.applied and rec.verdict:
        return label, f"INCOMPLETE refused but legal ({rec.why}); engine: {out.message[:120]}"
    return label, None


def structure(rec, cache) -> Tuple[str, Optional[str]]:
    """§5.2: the result is an EGI, keeps the B-min maps, and — where the
    licensed result can be built — equals one of the licensed forms. Only
    applied moves are checked. The label says how much was checked:
    ``exact`` — a legal move of a judged rule, compared with its licensed
    forms; ``illegal`` — an applied move legal() rejects, EGI-hood and maps
    only; ``egi-only`` — a move legal() does not judge. For the six rules in
    POSTCONDITION_RULES (the four ligature rules, split, merge) an ``egi-only``
    move is now checked for EGI-hood, maps, **and** the rule's postconditions
    (calculus_expected.postconditions) — these rules re-plumb identity, and
    the postconditions are the check a built licensed form would otherwise
    provide. Only an abstention on a *judged* rule is checked for EGI-hood and
    maps alone. A record whose source carries a B-min map is labelled with a
    ``:maps`` suffix, so the pinned extent shows whether the maps clause was
    ever exercised."""
    out = rec.outcome
    if not out.applied:
        return f"not:{rec.move.rule}:{_refused(out)}", None
    g, h, m = rec.g, out.result, rec.move
    problems = []
    if dominating_nodes(g) and not dominating_nodes(h):
        problems.append("the result is not an EGI (Def 12.5)")
    problems += maps_carried(g, h)
    forms = acceptable(g, m) if rec.verdict else None
    if forms is None and m.rule in POSTCONDITION_RULES:
        problems += postconditions(g, m, h)
    if forms is not None and not any(nav.same_graph(f, h) for f in forms):
        problems.append("the result differs from the licensed change")
    # Four cases, and the fourth only became reachable on 2026-09-20, when the
    # five remaining ligature/vertex rules gained legal() oracles:
    #   exact         — a legal move whose licensed forms are built and compared
    #   egi-only      — legal() does not judge it (verdict None)
    #   postcondition — legal() judges it LEGAL but its licensed result is not
    #                   built, so postconditions() above carries the check
    #   illegal       — legal() judges it illegal and the engine applied anyway
    # Before the oracles, no POSTCONDITION_RULES move ever reached verdict True,
    # so a legal-but-unbuilt move fell through to "illegal" and would have been
    # read as the severe cell. The check was always right; the label was not.
    if forms is not None:
        kind = "exact"
    elif rec.verdict is None:
        kind = "egi-only"
    elif m.rule in POSTCONDITION_RULES:
        kind = "postcondition"
    else:
        kind = "illegal"
    # What the maps clause actually inspects, and nothing else: a constant on a
    # surviving vertex, a sort, a quotation. It read `g.alphabet is not None or
    # bool(g.rho or ...)` until 2026-09-24, when the core began DERIVING both
    # the alphabet and rho — after which `g.alphabet is not None` is true of
    # every graph ever built and `g.rho` is non-empty whenever V is, so the
    # suffix would have marked the whole extent and told no one anything. The
    # alphabet clause is gone (calculus_expected.maps_carried says why) and rho
    # is checked only where it is a constant, which is what this now asks.
    maps = any(c is not None for c in g.rho.values()) or bool(g.sort or g.quotation)
    return f"{m.rule}:{kind}" + (":maps" if maps else ""), "; ".join(problems) or None


LAYERS: Dict[str, Check] = {"refusal": refusal}
LAYERS["structure"] = structure


def layer_universe(rels, consts, n, sem, tier):
    """The structures the soundness layer evaluates: tarski.universe under the
    mode's budget, except that at tier B an exhaustive universe larger than
    ``sem.tier_b_max_structures`` is replaced by the seeded sample."""
    cap = sem.tuple_cap
    limit = sem.tier_b_max_structures
    if tier == "B" and limit is not None:
        bits = sum(n ** ar for _, ar in rels)
        if bits <= cap and 2 ** bits * n ** len(consts) > limit:
            cap = -1
    return universe(rels, consts, n, cap=cap, sample_n=sem.sample_n, seed=sem.seed)


def _first(bits: int) -> int:
    return (bits & -bits).bit_length() - 1


def soundness(rec, cache) -> Tuple[str, Optional[str]]:
    """§5.3: Dau's direction for the rule, checked over finite structures.
    The source's model sets are cached per graph (the cache is reset per
    source graph by the run)."""
    out, m, g = rec.outcome, rec.move, rec.g
    if not out.applied:
        return f"not:{m.rule}:{_refused(out)}", None
    sem = cache["_sem"]
    h = out.result
    if len(g.V) + len(g.E) + len(g.Cut) > sem.max_elements:
        return f"not:{m.rule}:too-large", None
    if not (dominating_nodes(g) and dominating_nodes(h)):
        return f"not:{m.rule}:not-an-EGI", None
    direction = RULES[m.rule].direction
    rels, consts = vocabulary(g, h)
    exhaustive = True
    for n in sem.sizes:
        us, exh = layer_universe(rels, consts, n, sem, rec.tier)
        exhaustive &= exh
        k = ("models", rels, consts, n)
        if k not in cache:
            cache[k] = model_set(g, us)
        mg, mh = cache[k], model_set(h, us)
        if mg & ~mh:
            return f"{m.rule}:failed", f"UNSOUND at size {n}: a model of G is not a model of G' — {us[_first(mg & ~mh)]}"
        if direction == "equivalence" and mh & ~mg:
            return f"{m.rule}:failed", f"NOT AN EQUIVALENCE at size {n}: a model of G' is not a model of G — {us[_first(mh & ~mg)]}"
    return f"{m.rule}:{'exhaustive' if exhaustive else 'sampled'}", None


LAYERS["soundness"] = soundness
