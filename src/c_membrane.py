"""Membrane-level scoring for the C-series.

A unit is scored on what it anticipated against what arrived AT ITS OWN
MEMBRANE — never against the field's regime (spec premise 1). Abstention
(arrived but unanticipated) is not an error: open-world silence places no
bet. The three-valued discipline is `resolving_membrane.classify`'s.

A FORECAST RESOLVES EXACTLY ONCE, at the round it is due. The record is the
one place that knows what it has already charged for, so it is the place that
refuses to charge twice — see `MembraneLedger.score`.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import List, Optional, Set

from model_materialization import Fact
from resolving_membrane import classify


@dataclass(frozen=True)
class MembraneEntry:
    round_idx: int
    fact: Fact
    result: str          # "hit" | "miss" | "abstain"


@dataclass
class MembraneLedger:
    """A unit's own track record — K1, made live."""
    entries: List[MembraneEntry] = dc_field(default_factory=list)
    resolved: Set[Fact] = dc_field(default_factory=set)
    """Every fact this record has already resolved, hit or miss. THE UNIT OF
    ACCOUNT IS THE PROPOSITION, not the round and not the delivery: once a
    forecast of `head(a17)` has been resolved, this record will never enter a
    second verdict on `head(a17)`. It is read by `Unit.anticipate`, which is
    what keeps a settled claim from being re-offered in the first place; the
    refusal here is the guard that makes the statistic incorruptible by any
    other caller (a channel-fed unit in stage 3, a hand-built ledger in a
    test)."""
    restaked: int = 0
    """How many already-resolved forecasts were offered again and REFUSED
    rather than re-charged. Observability, never a score. In normal operation
    it stays 0, because `Unit.anticipate` filters first; a nonzero value says
    some caller is re-offering settled bets and would have corrupted
    `net_score` under the old contract."""
    late_arrivals: int = 0
    """How many already-resolved facts arrived after their due round. This is
    the measured PRICE of resolving once: a forecast that missed and whose
    fact later turns up takes no credit for it. Read it beside `hits` to see
    what the discipline forgoes."""

    def score(self, anticipated: Set[Fact], arrived: Set[Fact],
              round_idx: int) -> None:
        """Resolve this round's forecasts against this round's arrivals — each
        forecast exactly once, ever.

        WHY ONCE. A bet placed from a body seen at round r−1 is due at round r;
        the field delivers its consequents with a one-round lag, so that is the
        round at which the claim is decided. Charging it again at r+1, r+2, …
        does not measure a second failure, it re-measures the first one: under
        the old contract a single withheld consequent became a standing bet
        re-charged for the rest of the run, so misses grew with the SQUARE of
        the run length while hits grew linearly, and a law the field genuinely
        carried could still lose money (measured: the planted
        `b_local -> b_head` held alone scored 28 hits / 44 misses = −16). A
        statistic that worsens with run length for a TRUE law is measuring run
        length, not knowledge.

        A RE-DELIVERED FACT IS NOT AN ABSTENTION EITHER. Abstention means
        "arrived with no bet on it"; a fact whose forecast this record has
        already resolved was bet on, so a late arrival is counted in
        `late_arrivals` and left out of the entries rather than entered as a
        fresh abstention it plainly is not.
        """
        fresh = {f for f in anticipated if f not in self.resolved}
        self.restaked += len(anticipated) - len(fresh)
        for f in sorted(fresh):
            self.entries.append(
                MembraneEntry(round_idx, f, classify("true", f in arrived)))
        self.resolved.update(fresh)
        for f in sorted(arrived - anticipated):
            if f in self.resolved:
                self.late_arrivals += 1
                continue
            self.entries.append(
                MembraneEntry(round_idx, f, classify("unknown", True)))

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
        """Hits minus misses. **OBSERVABILITY, NEVER A GATE** — the standing
        `restaked` and `late_arrivals` already carry, retired from the gate role
        by author ruling on 2026-07-31.

        WHY IT WAS RETIRED. Five measured inversions, each with its outcome
        recorded beside it: the score rose 988 while the channels destroyed 64 of
        the 64 true laws the field carried, then rose a further 327 while 28 of
        them were restored. A statistic that rises in both directions of the
        thing under study cannot gate it. (The other three:
        `tests/test_c_channels.py::test_gate_one_...` names them all.)

        REPORT IT, NEVER ASSERT A VERDICT ON IT. No gate may be decided by
        comparing this number BETWEEN ARMS; a cross-arm gate is decided on the
        law components — true laws held, converses held — and must carry a
        participation clause, because an arm can improve this number by very
        nearly ceasing to forecast, and one did. Within a single arm, whether a
        held law pays is stated on `hits` and `misses` directly. Pinning an exact
        measured value is reporting, and stays.

        It remains computed and remains read: GATE 1's whole argument is that
        this number rose while the community learned less, which needs the number
        legible. `resolving_membrane.PredictionLedger.net_score` is a different
        class and is unaffected."""
        return self.hits - self.misses

    @property
    def accuracy(self) -> Optional[float]:
        """Hits over bets placed (abstentions excluded), or ``None`` when the
        unit never bet — an abstainer has no accuracy rather than a zero one,
        the same discipline `resolving_membrane.PredictionLedger` keeps. Read it
        beside `net_score`, never instead of it: over a handful of bets the
        ratio is unstable, and one lucky hit reads as 1.0."""
        bets = self.hits + self.misses
        return self.hits / bets if bets else None
