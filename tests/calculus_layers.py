"""Per-record checks, one per layer (spec 2026-09-10 §5). Each returns
(label, detail): the label is counted; detail is None on a pass."""
from __future__ import annotations

from typing import Callable, Dict, Optional, Tuple

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


LAYERS: Dict[str, Check] = {"refusal": refusal}
