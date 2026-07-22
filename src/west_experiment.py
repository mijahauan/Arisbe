"""The MONO and FED arrangements for the West-in-kytē E1 harness.

MONO: one kytos reads the whole vault (one big developing M). FED (Task 7): one
member kytos per top-folder + one journal-member + one coordinator (Task 5/6).
Both run the same total rounds R over the same generated corpus; cost/quality are
compared on equal work."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from vault_world import VaultWorld, VaultFeed, JOURNAL_SPINE_RELATIONS
from attention_economy import AttentionEconomy, Horizon
from agon_evolution import run
from west_measure import (CountingMaterializer, CostBreakdown, QualityReading,
                          read_quality, peel_proxy)
from west_coordinator import Coordinator


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


def _apportion(rounds: int, members: int) -> List[int]:
    """Round-robin: floor share to each member, remainder to the earliest."""
    base, rem = divmod(rounds, members)
    return [base + (1 if i < rem else 0) for i in range(members)]


def _run_member(root: Path, *, folders: Optional[frozenset], include_journal: bool,
                rounds: int, ttl: int, uid: str):
    """Run one FED member kytos (a folder-member or the journal-member) with
    its own CountingMaterializer. ``folders`` is passed straight through to
    :class:`VaultFeed` — ``frozenset()`` (no scan wants, the journal-member)
    is never coerced to ``None`` (all folders, the MONO semantics). Returns
    ``(EvolutionResult, CountingMaterializer)``."""
    world = VaultWorld(root)
    economy = AttentionEconomy()
    horizon = Horizon()
    feed = VaultFeed(world, economy, horizon=horizon,
                     folders=folders, include_journal=include_journal)
    cm = CountingMaterializer()
    res = run(
        "", feed, rounds=rounds, uod_id=uid, name=f"West E1 FED {uid}",
        description="FED member kytos (West-in-kyte E1).",
        ttl=ttl if ttl > 0 else None,
        pinned_relations=JOURNAL_SPINE_RELATIONS,
        materializer=cm,
    )
    return res, cm


def _fed_members(root: Path, manifest, *, rounds: int, ttl: int) -> tuple:
    """Shared member-running loop for the FED arrangements (Task 7 ``run_fed``
    and Task 8 ``run_fed_broker``): run F folder-members + 1 journal-member
    (adaptation A2) over ``root``, apportioning ``rounds`` round-robin across
    the F+1 members (:func:`_apportion`), each with its own developing M, and
    have the coordinator (Task 5/6) ingest each *folder*-member's final M
    (the journal-member is excluded — journal facts are never cross-folder
    link targets).

    Returns ``(coord, member_ms, member_costs, mat_atoms, peel, k2s, k3s,
    total_m)`` — the coordinator (already ingested), the folder->EGI map, and
    the raw per-member/aggregate cost+quality figures both callers assemble
    into their own :class:`ArrangementResult`."""
    folders = list(manifest.folders)
    # A2: FED members = one per content folder + one journal-only member.
    # folders=frozenset() means "no scan wants" (distinct from folders=None,
    # which means "all folders") — passed through to VaultFeed unmodified.
    member_specs = [(frozenset({f}), False, f"west_fed_{f}") for f in folders]
    member_specs.append((frozenset(), True, "west_fed_journal"))
    shares = _apportion(rounds, len(member_specs))

    coord = Coordinator()
    member_ms: Dict[str, object] = {}
    member_costs: List[int] = []
    mat_atoms = 0
    peel = 0
    k2s: List[float] = []
    k3s: List[float] = []
    total_m = 0

    for (folder_set, incl_journal, uid), share in zip(member_specs, shares):
        res, cm = _run_member(root, folders=folder_set, include_journal=incl_journal,
                              rounds=share, ttl=ttl, uid=uid)
        member_cost = cm.total_atoms() + peel_proxy(res)
        member_costs.append(member_cost)
        mat_atoms += cm.total_atoms()
        peel += peel_proxy(res)
        q = read_quality(res)
        if q.k2_stick_rate is not None:
            k2s.append(q.k2_stick_rate)
        k3s.append(q.k3_ratio)
        total_m += q.final_m_size
        # The coordinator ingests only folder members — a folder-member's
        # folder_set is a non-empty singleton {f}; the journal-member's is
        # the empty set, which folder_name below turns into None (skipped).
        folder_name = next(iter(folder_set)) if folder_set else None
        if folder_name is not None:
            coord.ingest(folder_name, res.uod.current_egi)
            member_ms[folder_name] = res.uod.current_egi

    return coord, member_ms, member_costs, mat_atoms, peel, k2s, k3s, total_m


def run_fed(root: Path, manifest, *, rounds: int, ttl: int) -> ArrangementResult:
    """Run the FED arrangement (:func:`_fed_members`) and compute coverage +
    the passive consistency-scan tax.

    FED cost = Σ member (materialization atoms + peel proxy) + coordinator
    cost (cells_written + scan_comparisons) — the coherence tax made visible.
    Quality is aggregated across all F+1 members: mean K2 (over members that
    report one), mean K3, and the summed final |M|."""
    (coord, member_ms, member_costs, mat_atoms, peel,
     k2s, k3s, total_m) = _fed_members(root, manifest, rounds=rounds, ttl=ttl)

    conflicts = coord.consistency_scan()
    cov, _unresolved = coord.coverage(manifest, member_ms)
    coordinator_cost = coord.cells_written + coord.scan_comparisons

    cost = CostBreakdown(materialization_atoms=mat_atoms, peel_proxy=peel,
                         coordinator_cost=coordinator_cost)
    quality = QualityReading(
        k2_stick_rate=(sum(k2s) / len(k2s)) if k2s else None,
        k3_ratio=(sum(k3s) / len(k3s)) if k3s else 0.0,
        final_m_size=total_m,
    )
    return ArrangementResult(name="FED", cost=cost, quality=quality,
                             member_costs=member_costs, coverage=cov,
                             conflicts=conflicts)


def run_fed_broker(root: Path, manifest, *, rounds: int, ttl: int) -> ArrangementResult:
    """The active-broker path (E1b): identical to :func:`run_fed`, but after
    the members run, the coordinator additionally drives one
    :meth:`Coordinator.route` per cross-folder link in ``manifest.cross_links``
    — the real coordination workload, rather than the passive registry
    :func:`run_fed` computes via :meth:`Coordinator.coverage`. Route attempts
    are added to ``coordinator_cost`` alongside the cells-written and
    scan-comparisons taxes, and ``ArrangementResult.routes`` records the
    count."""
    (coord, member_ms, member_costs, mat_atoms, peel,
     k2s, k3s, total_m) = _fed_members(root, manifest, rounds=rounds, ttl=ttl)

    conflicts = coord.consistency_scan()
    cov, _unresolved = coord.coverage(manifest, member_ms)
    for cl in manifest.cross_links:
        coord.route(cl.source_folder, cl.target_note, cl.target_folder, member_ms)
    coordinator_cost = coord.cells_written + coord.scan_comparisons + coord.routes

    cost = CostBreakdown(materialization_atoms=mat_atoms, peel_proxy=peel,
                         coordinator_cost=coordinator_cost)
    quality = QualityReading(
        k2_stick_rate=(sum(k2s) / len(k2s)) if k2s else None,
        k3_ratio=(sum(k3s) / len(k3s)) if k3s else 0.0,
        final_m_size=total_m,
    )
    return ArrangementResult(name="FED-broker", cost=cost, quality=quality,
                             member_costs=member_costs, coverage=cov,
                             conflicts=conflicts, routes=coord.routes)
