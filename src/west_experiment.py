"""The MONO and FED arrangements for the West-in-kytē E1 harness.

MONO: one kytos reads the whole vault (one big developing M). FED (Task 7): one
member kytos per top-folder + one journal-member + one coordinator (Task 5/6).
Both run the same total rounds R over the same generated corpus; cost/quality are
compared on equal work."""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from vault_world import VaultWorld, VaultFeed, JOURNAL_SPINE_RELATIONS
from attention_economy import AttentionEconomy, Horizon
from agon_evolution import run
from west_measure import (CountingMaterializer, CostBreakdown, QualityReading,
                          read_quality, peel_proxy, TracingMaterializer,
                          read_member_costs, MemberCostReading,
                          fit_power_law, PowerLawFit, MIN_FIT_POINTS)
from west_coordinator import Coordinator, member_relation_names


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


def _pair_comparisons(held_count: int) -> int:
    """Comparisons one NAIVE full scan makes over ``held_count`` cells — every
    unordered pair once. Identical by construction to what
    ``Coordinator.consistency_scan`` counts (pinned by test)."""
    return held_count * (held_count - 1) // 2


def _incremental_comparisons(held_count: int, new_count: int) -> int:
    """Comparisons one INCREMENTAL scan makes: each new cell against every
    already-scanned cell, plus each new pair once. Identical by construction to
    what ``Coordinator.consistency_scan_incremental`` counts (pinned by test)."""
    old = held_count - new_count
    return new_count * old + new_count * (new_count - 1) // 2


@dataclass(frozen=True)
class CoordinatorTax:
    """The three readings of the per-round coordinator tax, from one replay
    (E2 spec §3.1, §3.2).

    ``naive_member_round`` is **Arm N** (pre-registered): a full O(H²) pass after
    every member-round export — the pessimistic bound. ``incremental`` is
    **Arm I** (pre-registered): delta-scan, totalling H(H−1)/2 for a whole run
    however long it is. ``naive_global_round`` is a **disclosed secondary**
    reading — one full pass per synchronized global round — reported because
    E1 spec §4.1's "one scan/round" is ambiguous between it and Arm N. **No
    pre-registered prior depends on ``naive_global_round``.**"""
    cells_written: int
    naive_member_round: int
    naive_global_round: int
    incremental: int


def replay_coordinator_tax(
    trajectories: Dict[str, List[frozenset]],
) -> CoordinatorTax:
    """Replay the passive coordinator round-by-round over per-member relation-name
    trajectories and return all three tax readings (:class:`CoordinatorTax`).

    ``trajectories`` maps folder name -> the list of that member's per-round
    relation-name sets (from :class:`west_measure.TracingMaterializer`). Global
    round ``g`` is the synchronized round in which every member takes its ``g``-th
    step; a member with a shorter trajectory has simply finished.

    **Interleaving assumption (disclosed, verdict-bearing):** global round
    ``g`` models every member's ``g``-th step as taken *concurrently* — Arm
    N's per-member-round tax (:func:`_pair_comparisons`) fires once per
    member within round ``g``, interleaved across members, before the round
    advances. This is a modelling choice about a *federation*, whose members
    conceptually run in parallel, not a description of how this harness
    happens to execute them: ``_fed_members`` runs members sequentially (F0's
    whole round share, then F1's, ...) purely for harness convenience. The
    two orderings are not equivalent — for 3 members x 10 rounds x 8 relation
    names each they give ``naive_member_round`` totals ~26% apart (3956
    interleaved vs 3148 sequential) — because Arm N's cost depends on how big
    ``held`` is *at each individual export*, and that depends on the order
    exports are counted in. The interleaved (pessimistic) reading is used
    deliberately, since it is what a genuinely concurrent federation would
    pay; ``incremental`` and ``cells_written`` are invariant to this choice
    (both are pure set-cardinality totals over the fully-held set), so only
    ``naive_member_round`` is affected.

    Exact for the PASSIVE coordinator only: it is read-only, so replaying it
    cannot perturb what it measures. The active broker feeds routes back to
    members and would require true lockstep — callers must not use this for a
    broker arrangement (spec §3.1)."""
    folders = sorted(trajectories)
    global_rounds = max((len(trajectories[f]) for f in folders), default=0)
    held: set = set()
    unscanned: set = set()
    cells_written = 0
    naive_member_round = 0
    naive_global_round = 0
    incremental = 0

    for g in range(global_rounds):
        for f in folders:
            traj = trajectories[f]
            if g >= len(traj):
                continue                      # this member has finished
            # Determinism comes from sorted(folders) above and set-cardinality
            # accumulators (held/unscanned/cells_written) — not from ordering
            # this set-builder's source, which cannot affect its result.
            new = {(f, rel) for rel in traj[g]} - held
            held |= new
            unscanned |= new
            cells_written += len(new)
            # Arm N: one full pass after every member-round export.
            naive_member_round += _pair_comparisons(len(held))
        # Disclosed secondary: one full pass per synchronized global round.
        naive_global_round += _pair_comparisons(len(held))
        # Arm I: delta-scan once per synchronized global round.
        incremental += _incremental_comparisons(len(held), len(unscanned))
        unscanned = set()

    return CoordinatorTax(cells_written=cells_written,
                          naive_member_round=naive_member_round,
                          naive_global_round=naive_global_round,
                          incremental=incremental)


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


@dataclass
class ExperimentReport:
    """The θ-decided paired-comparison report + the P1-P4 pre-registered
    verdicts (spec §4.3, §6). ``gap = 1 - fed.coverage`` — the passive
    registry's unresolved fraction; ``broker_used`` records whether the
    caller re-ran the active broker (fed.name == "FED-broker") after a
    theta breach."""
    mono: ArrangementResult
    fed: ArrangementResult
    theta: float
    tol: float
    gap: float
    broker_used: bool
    priors: Dict[str, str]


def _quality_within_band(fed_q: QualityReading, mono_q: QualityReading,
                         tol: float) -> bool:
    """A1: parity judged on K2 (with K3 + |M| alongside). FED passes if its K2 is
    within tol below MONO's; if either K2 is None, fall back to final_m_size band."""
    if fed_q.k2_stick_rate is not None and mono_q.k2_stick_rate is not None:
        return fed_q.k2_stick_rate >= mono_q.k2_stick_rate - tol
    if mono_q.final_m_size == 0:
        return True
    return fed_q.final_m_size >= mono_q.final_m_size * (1 - tol)


def assemble_report(mono: ArrangementResult, fed: ArrangementResult, *,
                    theta: float, tol: float) -> ExperimentReport:
    """Compute the coherence gap, decide the theta branch, and evaluate the
    four pre-registered priors P1-P4 (spec §6) into a
    ``{"P1": "held"|"refuted", ...}`` verdict dict."""
    gap = 1.0 - (fed.coverage if fed.coverage is not None else 1.0)
    band_ok = _quality_within_band(fed.quality, mono.quality, tol)
    # P1 (headline): FED total cost < MONO total cost at comparable quality.
    p1 = "held" if (fed.cost.total() < mono.cost.total() and band_ok) else "refuted"
    # P2 (Q-C foreshadow): per-member cost-per-cycle clusters (CV < 0.5).
    mc = fed.member_costs
    if mc and sum(mc) > 0:
        mean = sum(mc) / len(mc)
        var = sum((c - mean) ** 2 for c in mc) / len(mc)
        cv = (var ** 0.5) / mean if mean else 0.0
        p2 = "held" if cv < 0.5 else "refuted"
    else:
        p2 = "refuted"
    # P3 (coherence): passive registry resolves >= 1 - theta.
    p3 = "held" if gap <= theta else "refuted"
    # P4 (refutation): FED loses if quality outside band (super-linear-F tax is E2's).
    p4 = "refuted" if not band_ok else "held"
    return ExperimentReport(mono=mono, fed=fed, theta=theta, tol=tol, gap=gap,
                            broker_used=(fed.name == "FED-broker"),
                            priors={"P1": p1, "P2": p2, "P3": p3, "P4": p4})


def _run_member_traced(root: Path, *, folders: Optional[frozenset],
                       include_journal: bool, rounds: int, ttl: int, uid: str):
    """As :func:`_run_member`, but with a :class:`TracingMaterializer` so the
    member's per-round relation-name trajectory is captured for the coordinator
    replay. Returns ``(EvolutionResult, TracingMaterializer)``."""
    world = VaultWorld(root)
    economy = AttentionEconomy()
    horizon = Horizon()
    feed = VaultFeed(world, economy, horizon=horizon,
                     folders=folders, include_journal=include_journal)
    tm = TracingMaterializer()
    res = run(
        "", feed, rounds=rounds, uod_id=uid, name=f"West E2 FED {uid}",
        description="FED member kytos (West-in-kyte E2).",
        ttl=ttl if ttl > 0 else None,
        pinned_relations=JOURNAL_SPINE_RELATIONS,
        materializer=tm,
    )
    return res, tm


def run_fed_traced(root: Path, manifest, *, rounds: int, ttl: int):
    """Run the passive FED arrangement capturing each folder-member's per-round
    relation trajectory, and replay the coordinator over it (spec §3.1).

    Returns ``(ArrangementResult, CoordinatorTax)``. The ``ArrangementResult``'s
    ``cost.coordinator_cost`` carries the E1-comparable end-of-run snapshot so
    the two measurement bases stay side by side; the per-round readings live in
    the returned :class:`CoordinatorTax`.

    Passive only — the broker is not replay-exact (spec §3.1)."""
    folders = list(manifest.folders)
    member_specs = [(frozenset({f}), False, f"west_e2_{f}") for f in folders]
    member_specs.append((frozenset(), True, "west_e2_journal"))
    shares = _apportion(rounds, len(member_specs))

    coord = Coordinator()
    member_ms: Dict[str, object] = {}
    member_costs: List[int] = []
    trajectories: Dict[str, List[frozenset]] = {}
    mat_atoms = 0
    peel = 0
    k2s: List[float] = []
    k3s: List[float] = []
    total_m = 0

    for (folder_set, incl_journal, uid), share in zip(member_specs, shares):
        res, tm = _run_member_traced(root, folders=folder_set,
                                     include_journal=incl_journal,
                                     rounds=share, ttl=ttl, uid=uid)
        member_costs.append(tm.total_atoms() + peel_proxy(res))
        mat_atoms += tm.total_atoms()
        peel += peel_proxy(res)
        q = read_quality(res)
        if q.k2_stick_rate is not None:
            k2s.append(q.k2_stick_rate)
        k3s.append(q.k3_ratio)
        total_m += q.final_m_size
        folder_name = next(iter(folder_set)) if folder_set else None
        if folder_name is not None:
            coord.ingest(folder_name, res.uod.current_egi)
            member_ms[folder_name] = res.uod.current_egi
            # CORRECTION (Task 6 review finding): TracingMaterializer.materialize()
            # is invoked once per round from inside agon_evolution.run()'s loop as
            # `model = pc.current` THEN `peel(model, ..., materializer=mat)`, with
            # the round's disposition (pc.apply_derived) applied only AFTER that
            # peel call. So per_round_relations[0] is the PRE-round-1 seed, and
            # per_round_relations[i] for i >= 1 is really "M after round i" (the
            # state left by round i's disposition, captured at the START of round
            # i+1). The state produced by the member's FINAL round's own
            # disposition is never captured by any materialize() call, because
            # there is no round R+1 to trigger it — so the raw trace is shifted
            # one round early and is missing the last round's growth entirely.
            # Fix it here, in the consumer (per the review's ruling — the capture
            # point in TracingMaterializer is correct for what it documents):
            # drop the leading pre-round seed and append the member's true final
            # M, read the same way coord.ingest/member_ms already read it (via
            # member_relation_names), so the corrected trajectory means "M after
            # round g" for each round the member actually executed (which may be
            # fewer than its share if the feed exhausts).
            # Do not revert this — without it, replay_coordinator_tax
            # systematically understates the per-round coherence tax and can
            # even invert the "per-round >= end-of-run snapshot" inequality.
            raw_trajectory = list(tm.per_round_relations)
            if raw_trajectory:
                trajectories[folder_name] = (
                    raw_trajectory[1:] + [member_relation_names(res.uod.current_egi)]
                )
            else:
                trajectories[folder_name] = []

    conflicts = coord.consistency_scan()
    cov, _unresolved = coord.coverage(manifest, member_ms)
    snapshot_cost = coord.cells_written + coord.scan_comparisons

    cost = CostBreakdown(materialization_atoms=mat_atoms, peel_proxy=peel,
                         coordinator_cost=snapshot_cost)
    quality = QualityReading(
        k2_stick_rate=(sum(k2s) / len(k2s)) if k2s else None,
        k3_ratio=(sum(k3s) / len(k3s)) if k3s else 0.0,
        final_m_size=total_m,
    )
    arrangement = ArrangementResult(name="FED", cost=cost, quality=quality,
                                    member_costs=member_costs, coverage=cov,
                                    conflicts=conflicts)
    return arrangement, replay_coordinator_tax(trajectories)


@dataclass
class E2ConfigResult:
    """One point of the E2 grid: MONO and FED at a given (folders, rounds, ttl),
    with FED's total reported under **both** pre-registered coordinator arms
    (spec §3.2)."""
    folders: int
    rounds: int
    ttl: int
    mono: ArrangementResult
    fed: ArrangementResult
    tax: CoordinatorTax
    member_reading: MemberCostReading
    fed_cost_naive: int
    fed_cost_incremental: int
    gap: float


def run_e2_config(root: Path, manifest, *, folders: int, rounds: int,
                  ttl: int) -> E2ConfigResult:
    """Run one grid point: MONO plus the traced passive FED, and assemble both
    arm totals. ``folders`` is recorded as the size axis S (spec §2)."""
    mono = run_mono(root, rounds=rounds, ttl=ttl)
    fed, tax = run_fed_traced(root, manifest, rounds=rounds, ttl=ttl)
    base = fed.cost.materialization_atoms + fed.cost.peel_proxy
    return E2ConfigResult(
        folders=folders, rounds=rounds, ttl=ttl, mono=mono, fed=fed, tax=tax,
        member_reading=read_member_costs(fed.member_costs),
        fed_cost_naive=base + tax.cells_written + tax.naive_member_round,
        fed_cost_incremental=base + tax.cells_written + tax.incremental,
        gap=1.0 - (fed.coverage if fed.coverage is not None else 1.0),
    )


P1_MIN_MONO_BETA = 1.3
P2_MAX_CV = 0.5
P2_MAX_MEAN_RATIO = 1.25
P3_MIN_TAX_BETA = 2.0


@dataclass
class E2Report:
    """The assembled size-sweep result: the fitted exponents, the crossover, and
    the pre-registered verdicts P1²-P4² (spec §6). P4² belongs to the ttl rider
    and reads "deferred" here.

    ``crossover_f`` is the F at which ``COST_fed(N)`` overtakes ``COST_mono``;
    ``crossover_kind`` (F3) says how it was determined so a caller can never
    misread one for the other:

    - ``"observed"`` — a genuine within-range transition: some smaller swept F
      has FED <= MONO and a larger swept F has FED > MONO.
    - ``"extrapolated"`` — no such transition appears in the swept data; the
      value is where the two *fitted* lines cross, and that value lies above
      the swept range (flagged, per spec §6).
    - ``"below-range"`` (Task 7 re-review, 2026-07-22) — FED-naive is above
      MONO at *every* swept F: no in-range transition to observe, but no
      extrapolation is needed either — the crossover lies below the range,
      which is the strongest confirmation coordination binds. ``crossover_f``
      is ``None`` here (the below-range F itself is never computed).
    - ``"none"`` — neither: ``crossover_f`` is ``None``.

    ``theta`` / ``tol`` (F5) are carried through from the call for the record.
    ``broker_forced`` (F5) lists the swept F values whose passive-registry gap
    exceeded ``theta`` — spec §3.1: that config's coordinator tax is not
    replay-exact and must be read as broker-forced, not silently folded in.
    ``tax_clamped_count`` (F6) counts configs whose ``tax.naive_member_round``
    was <= 0 and had to be clamped to 1 to take its log; a nonzero count
    forces ``fit_tax_naive.weak`` True (a clamped point is fabricated, not
    measured, and should never by itself carry a verdict)."""
    configs: List["E2ConfigResult"]
    fit_mono: PowerLawFit
    fit_fed_incremental: PowerLawFit
    fit_fed_naive: PowerLawFit
    fit_tax_naive: PowerLawFit
    crossover_f: Optional[float]
    crossover_kind: str
    theta: float
    tol: float
    broker_forced: List[int]
    tax_clamped_count: int
    priors: Dict[str, str]


def _crossover(fit_fed_naive: PowerLawFit, fit_mono: PowerLawFit,
               configs) -> Tuple[Optional[float], str]:
    """The F at which COST_fed(N) overtakes COST_mono, and how that F was
    determined — ``(value, kind)`` with ``kind`` one of ``"observed"``,
    ``"extrapolated"``, ``"below-range"``, ``"none"`` (F3; refined in the
    Task 7 re-review, 2026-07-22).

    A genuine **observed** crossover requires an actual within-range
    transition: some smaller swept F with FED <= MONO followed by a larger
    swept F with FED > MONO.

    FED-naive already being above MONO at *every* swept F is not that
    transition — there is nothing to observe — but it is not "no crossover"
    either: it means the crossover, if it exists, lies **below** the swept
    range, which is the *strongest* possible confirmation that coordination
    binds (P3² § below). That reads ``"below-range"``, distinct from
    ``"none"``.

    Absent an observed transition, extrapolates from the two fitted lines'
    intercepts (recovered in log space). The result is only honestly
    ``"extrapolated"`` when it lands **above** the swept range
    (``> max(folders)``) — an extrapolated F at or inside the range is not
    "beyond what we swept", it is a fit artifact, and is never reported as a
    value (a review probe once produced a physically meaningless
    ``crossover_f`` of ~0.02 folders this way — no E2 run has been executed
    yet). In that case the honest read falls back to ``"below-range"`` (if
    FED dominated the whole sweep) or ``"none"``.

    Returns ``(None, "none")`` when there is nothing to report: no configs,
    or no observed transition, FED did not dominate the whole sweep, and the
    FED-naive exponent does not exceed MONO's (the fitted lines do not cross
    going forward, so extrapolation would be meaningless or divide by zero).

    ``configs`` must already be sorted by ``folders`` ascending — the sole
    caller, :func:`assemble_e2_report`, sorts once and passes that list
    straight through; re-sorting here would be dead work on data that is
    already sorted."""
    if not configs:
        return None, "none"

    seen_at_or_below = False
    for c in configs:
        if c.fed_cost_naive <= c.mono.cost.total():
            seen_at_or_below = True
        elif seen_at_or_below:
            return float(c.folders), "observed"

    # No observed within-range transition. FED never having been at or
    # below MONO anywhere in the sweep is the below-range signal.
    fed_dominates_throughout = not seen_at_or_below

    def _fallback() -> Tuple[Optional[float], str]:
        return (None, "below-range") if fed_dominates_throughout else (None, "none")

    if fit_fed_naive.beta <= fit_mono.beta:
        return _fallback()
    # Recover each line's intercept in log space from its own points.
    xs = [math.log(c.folders) for c in configs]
    mx = sum(xs) / len(xs)
    ly_fed = [math.log(c.fed_cost_naive) for c in configs]
    ly_mono = [math.log(c.mono.cost.total()) for c in configs]
    a_fed = sum(ly_fed) / len(ly_fed) - fit_fed_naive.beta * mx
    a_mono = sum(ly_mono) / len(ly_mono) - fit_mono.beta * mx
    denom = fit_fed_naive.beta - fit_mono.beta   # > 0, guarded above
    f_star = math.exp((a_mono - a_fed) / denom)

    max_f = max(c.folders for c in configs)
    if f_star > max_f:
        return f_star, "extrapolated"
    return _fallback()


def assemble_e2_report(configs, *, theta: float, tol: float) -> E2Report:
    """Fit the exponents over the grid and decide P1²-P3² (spec §6). ``theta``
    and ``tol`` are carried for the record and for the coherence read (F5); the
    weak-fit rule turns any fit-dependent prior into "undetermined".

    **P1² (Ruling B, 2026-07-22)** has three outcomes, not two:

    - ``"refuted"`` — reserved for the pre-committed refutation only:
      ``beta_mono <= beta_fed_incremental`` (the federation hypothesis fails
      in its scaling form).
    - ``"separation-only"`` — separation holds (``beta_mono >
      beta_fed_incremental``) but ``beta_mono`` misses the 1.3 magnitude bar:
      a genuinely different outcome from the pre-committed refutation, so it
      gets its own name rather than being folded into "refuted".
    - ``"held"`` — separation holds *and* ``beta_mono > 1.3``.
    - ``"undetermined"`` — either fit is weak; checked first, before either
      of the above conditions.

    **P3² (Ruling A, 2026-07-22; reordered in the third re-review, same day)**
    requires *both* ``beta_tax_naive >= 2.0`` *and* a crossover existing —
    observed in range, extrapolated above it, or below the range (FED-naive
    dearer than MONO throughout the sweep, per the Task 7 re-review);
    ``gamma >= 2`` with no crossover means coordination diverges without ever
    being shown to overtake MONO — not the binding constraint the prior
    claims — so it reads "refuted". Because P3² is a conjunction, the checks
    run in this order: (1) the weak-fit gate on ``fit_tax_naive`` itself —
    "undetermined" if weak; (2) the determinate ``gamma < 2.0`` refutation,
    decided off ``fit_tax_naive`` alone, *before* the crossover is consulted
    at all — a weak crossover fit must never suppress a refutation the tax
    fit alone already settles; (3) only once gamma >= 2.0 is established, a
    **second** weak-fit gate applies to a crossover reading of
    ``"extrapolated"`` *or* ``"none"`` — both are decided entirely off
    ``fit_fed_naive``/``fit_mono`` (an extrapolated F* is read off their
    intercepts; a "none" reading is either ``beta_fed_naive <= beta_mono`` or
    an extrapolated F* landing inside the range), so if either of *those*
    fits is weak the reading cannot be trusted and P3² reads "undetermined"
    rather than "held" or "refuted" off a blunt fit. An observed or
    below-range crossover is a pointwise data comparison, not a fit, and
    needs no such gate."""
    ordered = sorted(configs, key=lambda c: c.folders)
    sizes = [c.folders for c in ordered]
    fit_mono = fit_power_law(sizes, [c.mono.cost.total() for c in ordered])
    fit_fed_incr = fit_power_law(sizes, [c.fed_cost_incremental for c in ordered])
    fit_fed_naive = fit_power_law(sizes, [c.fed_cost_naive for c in ordered])

    # F6: naive_member_round can only be <= 0 for a config whose coordinator
    # never held a cell (won't happen on real data — see CoordinatorTax's
    # docstring) — clamp to 1 so log() is defined, but never silently: record
    # how many points needed it and force the fit weak, since a clamped point
    # is fabricated, not measured, and must never carry a verdict alone.
    tax_values = [c.tax.naive_member_round for c in ordered]
    tax_clamped_count = sum(1 for v in tax_values if v <= 0)
    fit_tax_naive = fit_power_law(sizes, [max(v, 1) for v in tax_values])
    if tax_clamped_count:
        fit_tax_naive = replace(fit_tax_naive, weak=True)

    # P1² — the headline exponent separation (Ruling B).
    if fit_mono.weak or fit_fed_incr.weak:
        p1 = "undetermined"
    elif fit_mono.beta <= fit_fed_incr.beta:
        p1 = "refuted"
    elif fit_mono.beta > P1_MIN_MONO_BETA:
        p1 = "held"
    else:
        p1 = "separation-only"

    # P2² — terminal-unit invariance: tight within each config, flat across
    # them. A cross-size claim, so it needs the same n-point guard as the
    # fits (F4) — fewer than MIN_FIT_POINTS configs is too few to say
    # anything (a single config reads "flat" trivially; zero configs must
    # not read as a refutation from no data).
    if len(ordered) < MIN_FIT_POINTS:
        p2 = "undetermined"
    else:
        means = [c.member_reading.mean for c in ordered if c.member_reading.mean > 0]
        tight = all(c.member_reading.cv < P2_MAX_CV for c in ordered)
        flat = bool(means) and (max(means) / min(means) < P2_MAX_MEAN_RATIO)
        p2 = "held" if (tight and flat) else "refuted"

    # P3² — coordination is the binding constraint under Arm N (Ruling A).
    # P3² is a conjunction (gamma >= 2 AND a crossover exists), so a
    # determinate gamma < 2 refutation must be decided *before* the
    # crossover-fit gate below — otherwise a weak fed/mono fit can suppress a
    # refutation the tax fit alone already settles (Finding 1, third
    # re-review, 2026-07-22).
    crossover, crossover_kind = _crossover(fit_fed_naive, fit_mono, ordered)
    if fit_tax_naive.weak:
        p3 = "undetermined"
    elif fit_tax_naive.beta < P3_MIN_TAX_BETA:
        p3 = "refuted"
    elif crossover_kind in ("extrapolated", "none") and (fit_fed_naive.weak or fit_mono.weak):
        # An "extrapolated" F* is read off these two fits, not off the swept
        # data, so a weak one must never carry a "held" verdict. A "none"
        # reading is *also* decided entirely by these two fits (either
        # beta_fed_naive <= beta_mono, or the extrapolated F* landing inside
        # the range) — the same gate applies (Finding 2, third re-review,
        # 2026-07-22). Observed/below-range crossovers are pointwise data
        # comparisons, not fits, and pass through untouched by this gate.
        p3 = "undetermined"
    elif crossover_kind != "none":
        p3 = "held"
    else:
        p3 = "refuted"

    # F5: spec §3.1 — a config whose passive-registry gap exceeds theta is
    # broker-forced; its coordinator tax is not replay-exact and must be
    # named, not silently folded into the fits above.
    broker_forced = sorted(c.folders for c in ordered if c.gap > theta)

    return E2Report(configs=ordered, fit_mono=fit_mono,
                    fit_fed_incremental=fit_fed_incr,
                    fit_fed_naive=fit_fed_naive, fit_tax_naive=fit_tax_naive,
                    crossover_f=crossover, crossover_kind=crossover_kind,
                    theta=theta, tol=tol, broker_forced=broker_forced,
                    tax_clamped_count=tax_clamped_count,
                    priors={"P1": p1, "P2": p2, "P3": p3, "P4": "deferred"})
