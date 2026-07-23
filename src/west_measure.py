"""Deterministic cost + quality readers for the West-in-kytē E1 harness.

Cost is the spec §5.1 primary: Σ_rounds (atoms forward-chained by the materializer)
+ a deterministic peel proxy (Σ proposal atoms). Quality is the A1-adapted reading:
K2 stickiness primary, K3 ratio + final |M| alongside (K1 is N/A for a raise-only
membrane — see the plan's Adaptations)."""

from __future__ import annotations

import math
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


MIN_FIT_POINTS = 6
MIN_FIT_R_SQUARED = 0.90


@dataclass
class PowerLawFit:
    """An OLS fit of log(cost) on log(size): ``cost ∝ size**beta``.

    ``weak`` is the pre-registered guard (E2 spec §4): fewer than six usable
    points, or R² below 0.90, means the instrument is too blunt to support a
    verdict — the dependent prior is recorded "undetermined", never held or
    refuted."""
    beta: float
    stderr: float
    r_squared: float
    n: int
    weak: bool


def fit_power_law(sizes, costs) -> PowerLawFit:
    """Ordinary least squares of ``log(costs)`` on ``log(sizes)``.

    Raises ValueError on mismatched lengths or non-positive values (log is
    undefined there) — a silent drop would misreport the point count the
    weak-fit rule depends on."""
    if len(sizes) != len(costs):
        raise ValueError("sizes and costs must have the same length")
    if any(s <= 0 for s in sizes) or any(c <= 0 for c in costs):
        raise ValueError("power-law fit needs strictly positive sizes and costs")
    n = len(sizes)
    if n < 2:
        return PowerLawFit(0.0, 0.0, 0.0, n, True)

    xs = [math.log(s) for s in sizes]
    ys = [math.log(c) for c in costs]
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:                       # no variance in size — nothing to fit
        return PowerLawFit(0.0, 0.0, 0.0, n, True)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    beta = sxy / sxx
    intercept = my - beta * mx

    ss_res = sum((y - (intercept + beta * x)) ** 2 for x, y in zip(xs, ys))
    ss_tot = sum((y - my) ** 2 for y in ys)
    r_squared = 1.0 if ss_tot == 0 else 1.0 - ss_res / ss_tot
    if n > 2:
        stderr = math.sqrt(max(ss_res, 0.0) / (n - 2) / sxx)
    else:
        stderr = 0.0

    weak = (n < MIN_FIT_POINTS) or (r_squared < MIN_FIT_R_SQUARED)
    return PowerLawFit(beta=beta, stderr=stderr, r_squared=r_squared,
                       n=n, weak=weak)


def round_robin_buckets(folders, n: int) -> List[frozenset]:
    """Partition ``folders`` (an ordered tuple/list of folder-name strings) into
    ``n`` buckets by ``folder_index mod n`` — the quality-blind baseline
    bucketing (spec §2). Balanced when ``len(folders)`` is divisible by ``n``.
    ``n == 1`` returns a single bucket of all folders (the monolith bucketing)."""
    if n < 1:
        raise ValueError("n must be >= 1")
    ordered = list(folders)
    groups: List[set] = [set() for _ in range(n)]
    for k, f in enumerate(ordered):
        groups[k % n].add(f)
    return [frozenset(g) for g in groups]


def cut_link_count(buckets: List[frozenset], manifest) -> int:
    """Number of cross-folder links whose source and target folders fall in
    DIFFERENT buckets — the coherence-cost proxy (a lower count = a partition
    that respects the link structure). Spec §4."""
    where = {}
    for i, b in enumerate(buckets):
        for f in b:
            where[f] = i
    cut = 0
    for cl in manifest.cross_links:
        if where.get(cl.source_folder) != where.get(cl.target_folder):
            cut += 1
    return cut


def link_aware_buckets(manifest, n: int) -> List[frozenset]:
    """Greedy agglomerative bucketing that groups the most heavily cross-linked
    folders together, capped at ``len(folders)//n`` folders per bucket, to
    minimise cross-bucket links (spec §4). Deterministic: pair weights are the
    symmetric cross-link counts, ties break by (smallest min-folder-index, then
    smallest other-index). Assumes ``len(folders)`` divisible by ``n``."""
    if n < 1:
        raise ValueError("n must be >= 1")
    folders = list(manifest.folders)
    idx = {f: i for i, f in enumerate(folders)}
    cap = len(folders) // n
    # Symmetric pair weights.
    weight = {}
    for cl in manifest.cross_links:
        a, b = cl.source_folder, cl.target_folder
        if a == b:
            continue
        key = tuple(sorted((a, b), key=lambda f: idx[f]))
        weight[key] = weight.get(key, 0) + 1
    groups: List[set] = [{f} for f in folders]

    def group_key(g):                       # deterministic ordering of a group
        return min(idx[f] for f in g)

    def inter_weight(ga, gb):
        w = 0
        for a in ga:
            for b in gb:
                key = tuple(sorted((a, b), key=lambda f: idx[f]))
                w += weight.get(key, 0)
        return w

    while len(groups) > n:
        best = None  # (-weight, key_a, key_b, i, j)
        for i in range(len(groups)):
            for j in range(i + 1, len(groups)):
                if len(groups[i]) + len(groups[j]) > cap:
                    continue
                w = inter_weight(groups[i], groups[j])
                ka, kb = sorted((group_key(groups[i]), group_key(groups[j])))
                cand = (-w, ka, kb, i, j)
                if best is None or cand < best:
                    best = cand
        if best is None:
            # No weighted merge fits the cap; merge the two lowest-key groups
            # whose union fits — deterministic fallback so we always reach n.
            order = sorted(range(len(groups)), key=lambda i: group_key(groups[i]))
            merged = False
            for a in range(len(order)):
                for b in range(a + 1, len(order)):
                    i, j = order[a], order[b]
                    if len(groups[i]) + len(groups[j]) <= cap:
                        groups[i] |= groups[j]
                        del groups[j]
                        merged = True
                        break
                if merged:
                    break
            if not merged:
                raise ValueError("cannot reach n buckets under the capacity")
            continue
        _, _, _, i, j = best
        groups[i] |= groups[j]
        del groups[j]

    return [frozenset(g) for g in sorted(groups, key=group_key)]


@dataclass
class UCurveReading:
    """The Sweep-B U-curve reduced to its verdict inputs (spec §5). ``interior``
    means the cost-minimising granularity is a strict interior point
    (1 < argmin_n < max n) — PB1's condition. ``monotone_nonincreasing`` is
    PB2's condition (Arm I: splitting is ~free, so cost never rises with n)."""
    argmin_n: int
    argmin_cost: int
    interior: bool
    monotone_nonincreasing: bool
    costs_by_n: dict


def read_ucurve(points, which: str) -> UCurveReading:
    """Reduce Sweep-B points to a U-curve reading for arm ``which`` (\"naive\" or
    \"incremental\"). ``points`` each expose ``.n`` and ``.fed_cost_naive`` /
    ``.fed_cost_incremental``."""
    if which not in ("naive", "incremental"):
        raise ValueError("which must be 'naive' or 'incremental'")
    attr = "fed_cost_naive" if which == "naive" else "fed_cost_incremental"
    ordered = sorted(points, key=lambda p: p.n)
    costs = {p.n: getattr(p, attr) for p in ordered}
    ns = [p.n for p in ordered]
    argmin_n = min(ns, key=lambda n: (costs[n], n))
    argmin_cost = costs[argmin_n]
    interior = len(ns) >= 3 and ns[0] < argmin_n < ns[-1]
    seq = [costs[n] for n in ns]
    monotone_nonincreasing = all(b <= a for a, b in zip(seq, seq[1:]))
    return UCurveReading(argmin_n=argmin_n, argmin_cost=argmin_cost,
                         interior=interior,
                         monotone_nonincreasing=monotone_nonincreasing,
                         costs_by_n=costs)
