"""Use as participation in work.

The E-series defined use as re-delivery: an atom survived because the feed
announced it again, whether or not anything was ever done with it. Here an
atom counts as used when it appears in the SUPPORT of something derived.
Both clocks are kept side by side so their difference is measurable.
"""

from __future__ import annotations

from typing import Dict, FrozenSet, List, Set

from model_materialization import Fact


def work_used(provenance: Dict[Fact, FrozenSet[Fact]]) -> Set[Fact]:
    """The atoms that did work: every atom appearing in any support. The
    derived conclusions themselves are not counted — doing work means being
    a premise."""
    out: Set[Fact] = set()
    for support in provenance.values():
        out.update(support)
    return out


class WorkUsageLedger:
    """Two clocks over the same atoms: one driven by work, one by arrival."""

    def __init__(self, ttl: int):
        self.ttl = ttl
        self._work: Dict[Fact, int] = {}
        self._arrival: Dict[Fact, int] = {}

    def touch_work(self, provenance: Dict[Fact, FrozenSet[Fact]],
                   round_idx: int) -> None:
        for f in work_used(provenance):
            self._work[f] = round_idx
            self._arrival.setdefault(f, round_idx)

    def touch_arrival(self, delivered: Set[Fact], round_idx: int) -> None:
        for f in delivered:
            self._arrival[f] = round_idx
            self._work.setdefault(f, round_idx)

    def stale(self, round_idx: int, mode: str) -> List[Fact]:
        if mode not in ("work", "arrival"):
            raise ValueError(f"mode must be 'work' or 'arrival', got {mode!r}")
        clock = self._work if mode == "work" else self._arrival
        return sorted(f for f, last in clock.items()
                      if round_idx - last >= self.ttl)
