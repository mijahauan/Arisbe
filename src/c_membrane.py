"""Membrane-level scoring for the C-series.

A unit is scored on what it anticipated against what arrived AT ITS OWN
MEMBRANE — never against the field's regime (spec premise 1). Abstention
(arrived but unanticipated) is not an error: open-world silence places no
bet. The three-valued discipline is `resolving_membrane.classify`'s.
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

    def score(self, anticipated: Set[Fact], arrived: Set[Fact],
              round_idx: int) -> None:
        for f in sorted(anticipated):
            self.entries.append(
                MembraneEntry(round_idx, f, classify("true", f in arrived)))
        for f in sorted(arrived - anticipated):
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
        """Hits minus misses — stable at low bet volumes, where a bare ratio is
        not (one lucky hit reads as a perfect score). This is the statistic to
        compare two arms by, and the only one an abstainer can honestly share a
        scale with: abstention is 0, not a fabricated worst case."""
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
