"""Per-record checks, one per layer (spec 2026-09-10 §5). Each returns
(label, detail): the label is counted; detail is None on a pass."""
from __future__ import annotations

from typing import Callable, Dict, Optional, Tuple

import eg_navigation as nav
from calculus_expected import acceptable, maps_carried
from tarski import dominating_nodes

Check = Callable[[object, dict], Tuple[str, Optional[str]]]


def refusal(rec, cache) -> Tuple[str, Optional[str]]:
    """§5.1: engine (applied/refused) against legal (true/false). A crash is
    a defect whatever the rule; a not-judged instance is counted, not scored."""
    out = rec.outcome
    if out.crashed:
        return f"{rec.move.rule}:crash", f"CRASH {out.message[:160]}"
    if rec.verdict is None:
        return f"not:{rec.move.rule}", None
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
    applied moves are checked; an applied-but-illegal move is checked for
    EGI-hood and maps only. A record whose source carries a B-min map is
    labelled with a ``:maps`` suffix, so the pinned extent shows whether the
    maps clause was ever exercised."""
    out = rec.outcome
    if not out.applied:
        return f"not:{rec.move.rule}:refused", None
    g, h, m = rec.g, out.result, rec.move
    problems = []
    if dominating_nodes(g) and not dominating_nodes(h):
        problems.append("the result is not an EGI (Def 12.5)")
    problems += maps_carried(g, h)
    forms = acceptable(g, m) if rec.verdict else None
    if forms is not None and not any(nav.same_graph(f, h) for f in forms):
        problems.append("the result differs from the licensed change")
    kind = "exact" if forms is not None else ("postcondition" if rec.verdict is None else "illegal")
    maps = g.alphabet is not None or bool(g.rho or g.sort or g.quotation)
    return f"{m.rule}:{kind}" + (":maps" if maps else ""), "; ".join(problems) or None


LAYERS: Dict[str, Check] = {"refusal": refusal}
LAYERS["structure"] = structure

from calculus_rules import RULES
from tarski import model_set, universe, vocabulary


def _first(bits: int) -> int:
    return (bits & -bits).bit_length() - 1


def soundness(rec, cache) -> Tuple[str, Optional[str]]:
    """§5.3: Dau's direction for the rule, checked over finite structures.
    The source's model sets are cached per graph (the cache is reset per
    source graph by the run)."""
    out, m, g = rec.outcome, rec.move, rec.g
    if not out.applied:
        return f"not:{m.rule}:refused", None
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
        us, exh = universe(rels, consts, n, cap=sem.tuple_cap, sample_n=sem.sample_n, seed=sem.seed)
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
