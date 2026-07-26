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


@dataclass
class HorizonItem:
    """One not-yet-legible thing: retained, counted, re-attemptable."""
    kind: str
    ref: str
    size: int
    reason: str
    registered_round: int
    attempts: int = 0


class Horizon:
    """The horizon register (BOOTSTRAP_AND_DIRECTED_ENGAGEMENT §3, built at the
    vault stage where illegibility is real): what came back not-yet-legible,
    kept with counted size and re-attempted as legibility improves — where
    tomorrow's sensor space waits. Bounded, dedup'd by ref, drops counted.
    ``max_items`` defaults to 20000 (raised from 2000 after RUN 13's real
    digest showed ``horizon: open 2000, dropped 7100`` — the old default was
    under-sized for a real vault's ~1,400 images + clips; a register of
    tuples is cheap enough to hold the larger bound)."""

    def __init__(self, max_items: int = 20000):
        self._max = max_items
        self._items: Dict[str, HorizonItem] = {}
        self.dropped = 0

    def register(self, item: HorizonItem) -> bool:
        if item.ref in self._items:
            return False
        if len(self._items) >= self._max:
            self.dropped += 1
            return False
        self._items[item.ref] = item
        return True

    def open_items(self) -> List[HorizonItem]:
        return sorted(self._items.values(),
                      key=lambda i: (i.attempts, i.registered_round, i.ref))

    def reattempt(self, round_idx: int, k: int = 1) -> List[HorizonItem]:
        out = self.open_items()[:k]
        for i in out:
            i.attempts += 1
        return out

    def settle(self, ref: str) -> None:
        self._items.pop(ref, None)

    def snapshot(self) -> dict:
        by_kind: Dict[str, int] = {}
        by_reason: Dict[str, int] = {}
        for i in self._items.values():
            by_kind[i.kind] = by_kind.get(i.kind, 0) + 1
            by_reason[i.reason] = by_reason.get(i.reason, 0) + 1
        return {"open": len(self._items), "dropped": self.dropped,
                "by_kind": dict(sorted(by_kind.items())),
                "by_reason": dict(sorted(by_reason.items()))}


# --------------------------------------------------------------------------- #
# Intake adapters — the docket and the meta-learning frontier become wants.    #
# Non-invasive: QueryDocket and agon_metalearning are read, never modified.    #
# --------------------------------------------------------------------------- #

def wants_from_docket(docket, *, round_idx: int = 0, cost: float = 1.0) -> List[Want]:
    """Each open docket entry (a named want M neither holds nor denies) as a Want.
    ``created_round`` is back-dated by the entry's age so older doubts win ties;
    the entry's own attempt count carries over (a barren docket want sinks here too)."""
    out: List[Want] = []
    for entry in docket.open_entries:
        out.append(Want(
            kind="docket", key=entry.key, payload=entry, cost=cost,
            created_round=round_idx - entry.age, attempts=entry.attempts))
    return out


def wants_from_frontier(episodes, *, round_idx: int = 0, cost: float = 1.0,
                        severity: float = 4.0) -> List[Want]:
    """The ◇-contested horizon as wants: claims no mechanism settled
    (``agon_metalearning.unresolved_frontier``) — cross-run feedback, the
    game-studying-the-game edge. Higher severity than a bare particular: a
    contested claim's resolution settles more."""
    from agon_metalearning import unresolved_frontier
    return [
        Want(kind="frontier", key=(claim,), payload=claim, cost=cost,
             severity=severity, created_round=round_idx)
        for claim in unresolved_frontier(episodes)
    ]


class QuarantineRegister:
    """The adversarial cell of the reception taxonomy (spec §5): bounded,
    dedup'd by ref, drops counted, snapshot/restore — and deliberately NO
    reattempt method (quarantine is not the Horizon; nothing leaves it
    without a deliberate act)."""

    def __init__(self, max_items: int = 1000):
        self._max = max_items
        self._items: Dict[str, dict] = {}
        self.dropped = 0

    def register(self, ref: str, *, source: str, reason: str,
                 round_idx: int) -> bool:
        if ref in self._items:
            return False
        if len(self._items) >= self._max:
            self.dropped += 1
            return False
        self._items[ref] = {"source": source, "reason": reason,
                            "round": round_idx}
        return True

    def refs(self) -> List[str]:
        return sorted(self._items)

    def settle(self, ref: str) -> None:
        self._items.pop(ref, None)

    def snapshot(self) -> dict:
        return {"max": self._max, "dropped": self.dropped,
                "items": {k: dict(v) for k, v in sorted(self._items.items())}}

    @staticmethod
    def restore(state: dict) -> "QuarantineRegister":
        q = QuarantineRegister(max_items=int(state.get("max", 1000)))
        q.dropped = int(state.get("dropped", 0))
        q._items = {k: dict(v) for k, v in state.get("items", {}).items()}
        return q


ALTERNATIVE_SEVERITY = {"material": 8.0, "untraced": 4.0, "bare": 2.0}


def wants_from_alternatives(register, *, round_idx: int = 0, cost: float = 1.0,
                            s_register=None, source_record=None) -> List[Want]:
    """Open AlternativeRecords as wants, severity from the TRACED materiality
    (spec §6): material > untraced (the trace itself is a worthwhile reach) >
    bare; spurious not emitted. A distinction already standing in the
    S-register reads at half severity — the S-register's first reader (V.5
    closed). A reception nudges severity ONLY when it bears evidence AND its
    source has a positive track record; untracked + agrees earns exactly
    nothing (ruling R-B's teeth)."""
    out: List[Want] = []
    for record in register.open_records():
        tier = record.materiality.tier if record.materiality else "untraced"
        if tier == "spurious":
            continue
        severity = ALTERNATIVE_SEVERITY[tier]
        if s_register is not None and f"distinction:{record.relation}" in s_register:
            severity *= 0.5
        if source_record is not None:
            for rec in record.receptions:
                if not rec.bears_evidence:
                    continue
                tr = source_record.track_record(rec.source)
                if tr is not None and tr.hits > tr.misses:
                    severity *= 1.25
                    break                          # bounded, one-shot
        out.append(Want(kind="alternative", key=(record.key,), payload=record,
                        cost=cost, severity=severity,
                        created_round=record.emerged_round))
    return out


__all__ = ["Want", "AttentionEconomy", "wants_from_docket", "wants_from_frontier",
           "Horizon", "HorizonItem", "QuarantineRegister", "ALTERNATIVE_SEVERITY",
           "wants_from_alternatives"]
