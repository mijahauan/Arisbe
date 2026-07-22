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
from west_coordinator import member_relation_names


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


class TracingMaterializer(CountingMaterializer):
    """A :class:`CountingMaterializer` that additionally records the distinct
    relation names present in M at each round.

    ``materialize(egi)`` is invoked once per round with M itself — but only
    when ``agon_evolution.run()`` is called WITHOUT ``standing_proposal``. In
    that case (the E2 harness's usage: no standing proposal is passed to
    ``run(..., materializer=tm)``) this is an exact 1:1 per-round capture — no
    hook in ``agon_evolution`` and no chain-walking required.

    **Known limit — do not rely on 1:1 alignment when ``standing_proposal`` is
    set.** ``run()``'s loop calls ``peel(model, g_egif, materializer=mat)``
    once per round for the proposal itself, but *also* calls
    ``_verdict_or_none(pc.current, standing_proposal, mat)`` on every round
    (both the no-winner and winner branches) to audit the standing proposal —
    and ``_verdict_or_none`` performs a *second* ``peel(..., materializer=mat)``
    whenever ``standing_proposal`` is not ``None``, i.e. a second
    ``materialize()`` call through this same materializer. With a standing
    proposal set, ``len(per_round_relations)`` exceeds the round count and the
    entries no longer align 1:1 with rounds — see
    ``test_tracing_materializer_standing_proposal_breaks_1to1_alignment`` in
    ``tests/test_west_measure.py``, which pins this as regression-visible.
    The captured trajectory is what the E2 coordinator-tax replay (spec §3.1)
    consumes: the tax depends only on which (folder, relation-name) cells the
    coordinator holds at each round — hence the E2 harness always calls
    ``run()`` without a ``standing_proposal`` when tracing."""

    def __init__(self):
        super().__init__()
        self.per_round_relations: List[frozenset] = []

    def materialize(self, egi):
        out = super().materialize(egi)
        self.per_round_relations.append(member_relation_names(egi))
        return out


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


@dataclass
class MemberCostReading:
    """Per-member cost split so the CV statistic means what P2² says it means
    (E2 spec §3.3). ``cv`` and ``mean`` are over **folder-members only**; the
    journal-member (adaptation A2) is reported beside them, never inside them."""
    folder_member_costs: List[int]
    journal_member_cost: Optional[int]
    mean: float
    cv: float


def read_member_costs(member_costs: List[int]) -> MemberCostReading:
    """Split ``member_costs`` as ``_fed_members`` produces it — F folder-members
    followed by the single trailing journal-member — and compute the coefficient
    of variation over the folder-members alone.

    E1 read CV over all F+1 members, so the ~30x-cheaper journal-member alone
    could flip the verdict at small F (CV 0.68 at F=2 vs 0.035 over
    folder-members) while being diluted at larger F. That made E1's P2 statistic
    move with F for reasons unrelated to terminal-unit invariance."""
    if not member_costs:
        return MemberCostReading([], None, 0.0, 0.0)
    folder_costs = list(member_costs[:-1])
    journal_cost = member_costs[-1]
    if not folder_costs:
        return MemberCostReading([], journal_cost, 0.0, 0.0)
    mean = sum(folder_costs) / len(folder_costs)
    if mean == 0:
        return MemberCostReading(folder_costs, journal_cost, 0.0, 0.0)
    var = sum((c - mean) ** 2 for c in folder_costs) / len(folder_costs)
    return MemberCostReading(folder_costs, journal_cost, mean, (var ** 0.5) / mean)
