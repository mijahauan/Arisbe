"""Rung 1 — the economy-of-research ordering of reaches (the attention socket).

Design-of-record: docs/BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md §3 (criteria S1–S5
pre-registered); spec docs/superpowers/specs/2026-07-17-rung1-attention-economy-design.md.
World-agnostic: wants come from a docket, from the meta-learning frontier, or from a
world's musement candidates; the scorer orders them by severity-weighted decayed yield
per unit cost. Deterministic (no RNG, no wall clock); a scoring failure degrades to the
mechanical tie-break, never raises into the loop.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple


@dataclass
class Want:
    """One candidate reach. ``severity`` is the epistemic weight of the want's *shape*
    (testing a standing universal outranks another particular — Peirce's economy of
    research values what a result would settle, not only what it costs)."""
    kind: str
    key: Tuple
    payload: Any = None
    cost: float = 1.0
    severity: float = 1.0
    created_round: int = 0
    attempts: int = 0


class AttentionEconomy:
    def __init__(
        self,
        *,
        prior: float = 0.05,
        yield_decay: float = 0.8,
        attempt_decay: float = 0.7,
        max_wants: int = 500,
        musement_fraction: float = 0.1,
        boredom_rounds: int = 5,
    ):
        self._prior = prior
        self._yield_decay = yield_decay
        self._attempt_decay = attempt_decay
        self._max = max_wants
        self._eps = musement_fraction
        self._boredom_rounds = boredom_rounds
        self._wants: Dict[Tuple[str, Tuple], Want] = {}
        self._y: Dict[str, float] = {}
        self._streak = 0            # consecutive all-zero-yield observe() batches
        self.dropped = 0            # register() refusals at the cap — counted, never silent
        self.fallbacks = 0          # choose() degradations to the mechanical order

    # -- register / settle ---------------------------------------------------
    def register(self, want: Want) -> bool:
        k = (want.kind, want.key)
        if k in self._wants:
            return False
        if len(self._wants) >= self._max:
            self.dropped += 1
            return False
        self._wants[k] = want
        return True

    def wants(self) -> List[Want]:
        return list(self._wants.values())

    def settle(self, kind: str, key: Tuple) -> None:
        self._wants.pop((kind, key), None)

    # -- scoring -------------------------------------------------------------
    def kind_yield(self, kind: str) -> float:
        return self._y.get(kind, 0.0)

    def _score(self, w: Want) -> float:
        y = self._y.get(w.kind, 0.0)
        return w.severity * (y + self._prior) / max(w.cost, 1e-9) \
            * (self._attempt_decay ** w.attempts)

    def _mechanical(self, ws: List[Want]) -> List[Want]:
        return sorted(ws, key=lambda w: (w.attempts, w.created_round, w.kind, repr(w.key)))

    def choose(self, k: int, round_idx: int) -> List[Want]:
        pool = list(self._wants.values())
        muse = [w for w in pool if w.kind == "musement"]
        rest = [w for w in pool if w.kind != "musement"]
        try:
            m = self._musement_slots(k, round_idx) if muse else 0
            muse_sorted = sorted(muse, key=lambda w: (-w.created_round, repr(w.key)))
            rest_sorted = sorted(
                rest, key=lambda w: (-self._score(w), w.attempts, w.created_round,
                                     w.kind, repr(w.key)))
            chosen = muse_sorted[:m] + rest_sorted[: max(0, k - min(m, len(muse_sorted)))]
            chosen = chosen[:k]
        except Exception:
            self.fallbacks += 1
            chosen = self._mechanical(pool)[:k]
        for w in chosen:
            w.attempts += 1
        return chosen

    # -- musement (Task 2 wires the boredom detector into this) ---------------
    def effective_musement(self) -> float:
        if self._streak >= self._boredom_rounds:
            return min(0.5, self._eps * 2)
        return self._eps

    def _musement_slots(self, k: int, round_idx: int) -> int:
        eps = self.effective_musement()
        if eps <= 0:
            return 0
        base = int(eps * k)
        period = max(1, int(round(1 / eps)))
        extra = 1 if (base == 0 and round_idx % period == 0) else 0
        return min(k, base + extra)

    # -- feedback ------------------------------------------------------------
    def observe(self, round_idx: int, results: Sequence[Tuple[Want, int]]) -> None:
        total = 0
        for want, events in results:
            total += events
            y = self._y.get(want.kind, 0.0)
            self._y[want.kind] = self._yield_decay * y + (1 - self._yield_decay) * events
        self._streak = 0 if total > 0 else self._streak + 1

    def snapshot(self) -> dict:
        return {
            "kinds": dict(sorted(self._y.items())),
            "wants": len(self._wants),
            "dropped": self.dropped,
            "fallbacks": self.fallbacks,
            "streak": self._streak,
            "effective_musement": self.effective_musement(),
        }
