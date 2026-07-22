"""Deterministic cost + quality readers for the West-in-kytē E1 harness.

Cost is the spec §5.1 primary: Σ_rounds (atoms forward-chained by the materializer)
+ a deterministic peel proxy (Σ proposal atoms). Quality is the A1-adapted reading:
K2 stickiness primary, K3 ratio + final |M| alongside (K1 is N/A for a raise-only
membrane — see the plan's Adaptations)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from model_materialization import IncrementalMaterializer, materialization_ratio
from agon_evolution import sheet_atom_keys, EvolutionResult, delivered_atom_keys
from agon_metalearning import episodes_from, resolution_principles


class CountingMaterializer(IncrementalMaterializer):
    """Records per-call (base + derived) atom counts — the per-round forward-chain
    work. run() reuses one materializer across rounds and threads it into the peel
    (agon_evolution.py:680, :696), so one call ≈ one round's materialization."""

    def __init__(self):
        super().__init__()
        self.per_round_atoms: List[int] = []

    def materialize(self, egi):
        facts, report = super().materialize(egi)
        self.per_round_atoms.append(report.base_facts + report.derived_facts)
        return facts, report

    def total_atoms(self) -> int:
        return sum(self.per_round_atoms)


@dataclass
class CostBreakdown:
    materialization_atoms: int
    peel_proxy: int
    coordinator_cost: int = 0

    def total(self) -> int:
        return self.materialization_atoms + self.peel_proxy + self.coordinator_cost


@dataclass
class QualityReading:
    k2_stick_rate: Optional[float]
    k3_ratio: float
    final_m_size: int


def peel_proxy(result: EvolutionResult) -> int:
    """A deterministic proxy for peel-layer visits: Σ over rounds of the proposal's
    atom count (deeper/larger proposals visit more layers)."""
    total = 0
    for o in result.outcomes:
        if o.proposal_egif:
            total += len(delivered_atom_keys(o.proposal_egif))
    return total


def read_quality(result: EvolutionResult) -> QualityReading:
    final = result.uod.current_egi
    principles = resolution_principles(episodes_from(result))
    if principles:
        rates = [p.stick_rate for p in principles if p.stick_rate is not None]
        k2 = sum(rates) / len(rates) if rates else None
    else:
        k2 = None
    k3 = materialization_ratio(final).ratio
    return QualityReading(k2_stick_rate=k2, k3_ratio=k3,
                          final_m_size=len(sheet_atom_keys(final)))
