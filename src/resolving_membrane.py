"""The first *raise-and-resolve* membrane — a membrane with world-teeth.

Design-of-record: ``docs/AUTOMATED_ENDOPOREUTIC_GAME.md`` §4b. The raise-only membrane
(``discourse_membrane``) surfaces propositions and cross-source conflict but cannot check them
against reality — it models *the discourse, not the world*. A **raise-and-resolve** membrane
adds the missing thing: the world returns a **verdict over time**, so M can *predict* and be
*empirically falsified*. Selection gets teeth — the Robot-Scientist flavour.

The mechanism, and how it reuses what is already here:

* **M's prediction is the peel.** Because ``peel`` materializes M's Horn laws first, M
  *predicts* things it was never directly told: ``peel(M, claim, closed=False)`` is M's own
  bet on ``claim`` (open-world, so a claim M neither entails nor refutes reads UNKNOWN — an
  *abstention*, not a false guess). This is taken **before** the world's outcome is folded in,
  so it is a genuine forecast.
* **The world resolves.** A :class:`ResolvingItem` carries the world's ``happened`` verdict and
  the ground-truth graph to scribe (``world_egif``). At its round the feed records M's forecast
  in a :class:`PredictionLedger`, then hands the ground truth to the ordinary loop — where the
  **existing mechanical panel** disposes it (a confirmed fact → ``new_fact``; a swan-that-is-not-
  white that refutes M's standing law → ``challenge_to_M`` relinquishes the over-general law).
  No new referee: the world's outcome is *data*, and the calculus still decides.
* **Selection scores predictors.** The ledger tallies hits / misses / abstentions; a theory
  whose laws over-reach earns misses, a conservative one abstains. :func:`select_best` picks the
  better predictor by net score (hits − misses) — *the world selecting against the over-general
  theory*, which competing DAG branches (or ablation arms) are ranked by.

Correspondence, not truth, still holds: a resolved market/API is **low-warrant data** (it can
be wrong or manipulated); M self-certifies coherence and a *track record*, not truth about the
world. Offline and replayable by construction (the outcomes are recorded), so it is CI-safe; a
live source (prediction market, sports/weather API, constraint-checked DB) attaches at the same
:class:`agon_evolution.Proposer` socket, only the outcome's origin differing. Additive,
geometry-free, imports no protected module's internals.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

from agon_evolution import peel


# --------------------------------------------------------------------------- #
# A claim the world resolves                                                   #
# --------------------------------------------------------------------------- #

@dataclass
class ResolvingItem:
    """One claim the world resolves. ``claim_egif`` is the proposition M is scored on (its
    forecast target); ``happened`` is the world's verdict; ``world_egif`` is the ground-truth
    graph scribed for the panel to dispose — defaulting to the plain claim when it happened, or
    a bare negation when it did not (a *law-falsifying counterexample* like
    ``(swan "Nox") ~[ (white "Nox") ]`` is supplied explicitly so the Challenger sees it)."""
    claim_egif: str
    happened: bool
    world_egif: Optional[str] = None

    def ground_truth(self) -> str:
        if self.world_egif is not None:
            return self.world_egif
        return self.claim_egif if self.happened else f"~[ {self.claim_egif} ]"


# --------------------------------------------------------------------------- #
# The scoring ledger — the teeth                                               #
# --------------------------------------------------------------------------- #

def classify(predicted: str, happened: bool) -> str:
    """Score M's forecast against the world. A definite forecast that matches the outcome is a
    ``hit``; one that contradicts it is a ``miss``; ``unknown`` (M had no basis — open-world)
    is an ``abstain`` (no bet placed, so neither rewarded nor penalised)."""
    if predicted == "unknown":
        return "abstain"
    forecast_true = predicted == "true"
    return "hit" if forecast_true == happened else "miss"


@dataclass
class ScoreEntry:
    round_idx: int
    claim_egif: str
    predicted: str        # M's open-world forecast: true / false / unknown
    happened: bool
    result: str           # hit / miss / abstain


@dataclass
class PredictionLedger:
    """M's empirical track record — the world's selection signal on a theory."""
    entries: List[ScoreEntry] = field(default_factory=list)

    def record(self, item: ResolvingItem, predicted: str, round_idx: int) -> ScoreEntry:
        entry = ScoreEntry(round_idx, item.claim_egif, predicted,
                           item.happened, classify(predicted, item.happened))
        self.entries.append(entry)
        return entry

    @property
    def hits(self) -> int:
        return sum(1 for e in self.entries if e.result == "hit")

    @property
    def misses(self) -> int:
        return sum(1 for e in self.entries if e.result == "miss")

    @property
    def abstentions(self) -> int:
        return sum(1 for e in self.entries if e.result == "abstain")

    @property
    def net_score(self) -> int:
        """Net correct forecasts (``hits − misses``) — the selection key. A theory that never
        bets wrong stays at 0; an over-general one that gets falsified goes negative."""
        return self.hits - self.misses

    @property
    def accuracy(self) -> Optional[float]:
        """Hits over *definite* forecasts (abstentions excluded). ``None`` if M never bet."""
        decided = self.hits + self.misses
        return (self.hits / decided) if decided else None


# --------------------------------------------------------------------------- #
# The feed as a Proposer (the membrane)                                        #
# --------------------------------------------------------------------------- #

class ResolvingFeed:
    """A raise-and-resolve open membrane: at each item's round it records M's open-world
    forecast on the claim (into ``ledger``) and hands the world's ground truth to the loop for
    the mechanical panel to dispose. Implements the ``agon_evolution.Proposer`` socket."""

    def __init__(self, items: Sequence[ResolvingItem]):
        self._items = list(items)
        self.ledger = PredictionLedger()

    def propose(self, model, round_idx: int) -> Optional[str]:
        i = round_idx - 1
        if not (0 <= i < len(self._items)):
            return None                                              # the feed is exhausted
        item = self._items[i]
        predicted = peel(model, item.claim_egif, closed=False).verdict.value
        self.ledger.record(item, predicted, round_idx)              # M's forecast, pre-outcome
        return item.ground_truth()


# --------------------------------------------------------------------------- #
# Selection — the world ranking the predictors                                 #
# --------------------------------------------------------------------------- #

def select_best(arms: Sequence[Tuple[str, PredictionLedger]]) -> Optional[str]:
    """Rank competing theories (DAG branches / ablation arms) by their empirical track record
    and return the winner's label — *the world selecting against the over-general theory*.
    Order: higher net score, then higher accuracy, then fewer bets (parsimony). ``None`` for an
    empty field."""
    if not arms:
        return None

    def key(arm: Tuple[str, PredictionLedger]):
        _label, led = arm
        acc = led.accuracy if led.accuracy is not None else 0.0
        bets = led.hits + led.misses
        return (led.net_score, acc, -bets)

    return max(arms, key=key)[0]


__all__ = [
    "ResolvingItem", "classify", "ScoreEntry", "PredictionLedger",
    "ResolvingFeed", "select_best",
]
