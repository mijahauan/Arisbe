"""Membrane-level scoring for the C-series.

A unit is scored on what it anticipated against what arrived AT ITS OWN
MEMBRANE — never against the field's regime (spec premise 1). Abstention
(arrived but unanticipated) is not an error: open-world silence places no
bet. The three-valued discipline is `resolving_membrane.classify`'s.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import List, Set, Tuple

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
    def accuracy(self) -> float:
        bets = self.hits + self.misses
        return self.hits / bets if bets else 0.0
