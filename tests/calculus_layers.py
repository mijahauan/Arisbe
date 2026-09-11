"""Per-record checks, one per layer (spec 2026-09-10 §5). Each returns
(label, detail): the label is counted; detail is None on a pass."""
from __future__ import annotations

from typing import Callable, Dict, Optional, Tuple

import eg_navigation as nav
from calculus_expected import expected, maps_carried
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
    licensed result can be built — equals it. Only applied moves are checked;
    an applied-but-illegal move is checked for EGI-hood and maps only."""
    out = rec.outcome
    if not out.applied:
        return f"not:{rec.move.rule}:refused", None
    g, h, m = rec.g, out.result, rec.move
    problems = []
    if dominating_nodes(g) and not dominating_nodes(h):
        problems.append("the result is not an EGI (Def 12.5)")
    problems += maps_carried(g, h)
    exp = expected(g, m) if rec.verdict else None
    if exp is not None and not nav.same_graph(exp, h):
        problems.append("the result differs from the licensed change")
    kind = "exact" if exp is not None else ("postcondition" if rec.verdict is None else "illegal")
    return f"{m.rule}:{kind}", "; ".join(problems) or None


LAYERS: Dict[str, Check] = {"refusal": refusal}
LAYERS["structure"] = structure
