"""The MONO and FED arrangements for the West-in-kytē E1 harness.

MONO: one kytos reads the whole vault (one big developing M). FED (Task 7): one
member kytos per top-folder + one journal-member + one coordinator (Task 5/6).
Both run the same total rounds R over the same generated corpus; cost/quality are
compared on equal work."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from vault_world import VaultWorld, VaultFeed, JOURNAL_SPINE_RELATIONS
from attention_economy import AttentionEconomy, Horizon
from agon_evolution import run
from west_measure import (CountingMaterializer, CostBreakdown, QualityReading,
                          read_quality, peel_proxy)


@dataclass
class ArrangementResult:
    name: str
    cost: CostBreakdown
    quality: QualityReading
    member_costs: List[int] = field(default_factory=list)
    coverage: Optional[float] = None
    conflicts: int = 0
    routes: int = 0


def run_mono(root: Path, *, rounds: int, ttl: int) -> ArrangementResult:
    """Run one whole-vault kytos over ``root`` for ``rounds`` rounds, developing
    one M from the entire vault (all folders + the journal). Returns cost
    (materialization atoms + peel proxy) and quality (K2/K3/final |M|) readings,
    with member_costs=[] and coverage=None — MONO has no federation members and
    pays no coherence tax."""
    world = VaultWorld(root)
    economy = AttentionEconomy()
    horizon = Horizon()
    feed = VaultFeed(world, economy, horizon=horizon)   # whole vault, journal on
    cm = CountingMaterializer()
    res = run(
        "", feed, rounds=rounds, uod_id="west_mono",
        name="West E1 MONO", description="MONO arrangement (whole-vault kytos).",
        ttl=ttl if ttl > 0 else None,
        pinned_relations=JOURNAL_SPINE_RELATIONS,
        materializer=cm,
    )
    cost = CostBreakdown(materialization_atoms=cm.total_atoms(),
                         peel_proxy=peel_proxy(res))
    return ArrangementResult(name="MONO", cost=cost, quality=read_quality(res))
