"""West-in-kytē E3b — the basin map (endogenous-partition landscape census):
enumerate the Arm-N local optima the E3 walk discipline reaches from a fixed
structured start set, and their attractor sets.

Spec: docs/superpowers/specs/2026-07-24-west-in-kyte-e3b-design.md
Reuses west_meta_agon UNCHANGED; unprotected, additive."""

from dataclasses import dataclass
from typing import Dict, List

from west_meta_agon import (Bucketing, MemoEvaluator, WalkResult, arm_cost, bucketing_key, bucket_sizes,
                            canonical, merge_moves, run_meta_walk, split_moves)
from west_measure import round_robin_buckets


def _compositions(n: int, k: int):
    """All ordered compositions of n into k positive parts (tuples)."""
    if k == 1:
        yield (n,)
        return
    for first in range(1, n - k + 2):
        for rest in _compositions(n - first, k - 1):
            yield (first,) + rest


def contiguous_compositions(folders, parts: int, cap: int) -> List[Bucketing]:
    """The ``cap`` size-largest contiguous ``parts``-block partitions of the
    sorted folders (spec §3). Each composition (s1..sk) maps to contiguous
    blocks of the sorted folder order; compositions ordered lexicographically
    DESCENDING by their size-tuple, then the first ``cap`` taken."""
    fs = sorted(folders)
    n = len(fs)
    comps = sorted(_compositions(n, parts), reverse=True)[:cap]
    out: List[Bucketing] = []
    for comp in comps:
        blocks = []
        i = 0
        for s in comp:
            blocks.append(fs[i:i + s])
            i += s
        out.append(canonical(blocks))
    return out


def structured_starts(manifest, *, comp_parts=(3, 4),
                      comp_cap: int = 12) -> List[Bucketing]:
    """The deterministic seed set (spec §3): round-robin N=1..F0, the capped
    contiguous compositions for each part-count, and the three E3 starts;
    deduped by canonical key, deterministic order."""
    fs = sorted(manifest.folders)
    starts: List[Bucketing] = []
    # 1. round-robin N = 1..F0
    for n in range(1, len(fs) + 1):
        starts.append(canonical(round_robin_buckets(manifest.folders, n)))
    # 2. contiguous compositions
    for parts in comp_parts:
        starts.extend(contiguous_compositions(manifest.folders, parts, comp_cap))
    # 3. the E3 starts. N=1 and N=F0 are general; the 6/3/2/1 mid-start is
    # specific to F0=12 (E3 continuity) — its fixed slices only partition a
    # 12-folder vault, so it is added only there (smoke F0=4 is covered by the
    # round-robin + compositions above).
    starts.append(canonical([fs]))                                  # N=1
    starts.append(canonical([[f] for f in fs]))                     # N=F0
    if len(fs) >= 12:
        starts.append(canonical([fs[0:6], fs[6:9], fs[9:11], fs[11:12]]))  # 6/3/2/1
    # dedup by canonical key, preserve first-seen order
    seen = set()
    out: List[Bucketing] = []
    for b in starts:
        key = bucketing_key(b)
        if key not in seen:
            seen.add(key)
            out.append(b)
    return out


@dataclass
class BasinMap:
    """The descent map (spec §5): every structured start's Arm-N terminus, and
    the inverted watersheds (terminus -> the starts that reach it)."""
    terminus_by_start: Dict[str, WalkResult]
    watersheds: Dict[str, List[str]]
    evaluator: MemoEvaluator
    manifest: object


def map_basins(root, manifest, starts, *, rounds: int, ttl: int, theta: float,
               merge_k: int = 3, max_rounds: int = 20, evaluator=None) -> BasinMap:
    """Descend each structured start through the verbatim E3 Arm-N walk on ONE
    shared MemoEvaluator (spec §2-§4); invert termini to watersheds.
    Evaluator is injectable (for testing); if None, builds a new MemoEvaluator."""
    if evaluator is None:
        evaluator = MemoEvaluator(root, manifest, rounds=rounds, ttl=ttl)
    terminus_by_start: Dict[str, WalkResult] = {}
    for b in starts:
        wr = run_meta_walk(b, name="basin", arm="naive", manifest=manifest,
                           evaluate=evaluator.evaluate, theta=theta,
                           merge_k=merge_k, max_rounds=max_rounds,
                           ledger_path=None)
        terminus_by_start[bucketing_key(b)] = wr
    watersheds: Dict[str, List[str]] = {}
    for start_key, wr in terminus_by_start.items():
        term_key = bucketing_key(wr.final)
        watersheds.setdefault(term_key, []).append(start_key)
    for members in watersheds.values():
        members.sort()
    return BasinMap(terminus_by_start=terminus_by_start, watersheds=watersheds,
                    evaluator=evaluator, manifest=manifest)


def distinct_optima(bm: BasinMap) -> List[str]:
    """Sorted distinct terminus keys (the basins reached)."""
    return sorted(bm.watersheds.keys())


def full_neighbourhood_improver(bucketing, manifest, evaluate, *, theta: float,
                                arm: str = "naive") -> bool:
    """The shortlist_shadowed diagnostic (spec §2): does the FULL neighbourhood
    — all splits + ALL pairwise merges (no top-k shortlist) — contain a
    gap-admissible strict Arm-``arm`` improver over ``bucketing``? Reported,
    never acted on. A merge_k larger than any bucket count forces the full
    merge slate."""
    inc = evaluate(bucketing)
    full_k = len(bucketing) * len(bucketing) + 1        # >= C(N,2), all pairs
    neighbours = split_moves(bucketing) + merge_moves(bucketing, manifest,
                                                      k=full_k)
    for _label, child in neighbours:
        ev = evaluate(child)
        if ev.gap > theta:
            continue
        if arm_cost(ev, arm) < arm_cost(inc, arm):
            return True
    return False


@dataclass
class Optimum:
    """One distinct basin bottom (spec §5)."""
    key: str
    sizes: str
    n: int
    cost: int
    watershed_count: int
    shadowed: bool


@dataclass
class BasinReport:
    """The assembled map + PM1-PM4 verdicts (spec §5-§6)."""
    optima: List["Optimum"]
    priors: Dict[str, str]
    consistency_ok: bool
    cheapest_cost: int
    distinct_count: int


def assemble_basin_report(bm: BasinMap, shadowed: Dict[str, bool], *,
                          e3_w1_cost: int = 119935, e3_w2_cost: int = 101411,
                          e3_known_sizes=("3/8/1", "10/1/1")) -> BasinReport:
    """Decide PM1-PM4 and build the optima table (spec §6). ``shadowed`` maps a
    terminus key to its full-neighbourhood diagnostic (Task 3)."""
    # Build the optima table (one per distinct terminus).
    optima: List[Optimum] = []
    for term_key, members in bm.watersheds.items():
        # every member reaches this terminus; read cost/n from any one.
        wr = bm.terminus_by_start[members[0]]
        optima.append(Optimum(
            key=term_key, sizes=bucket_sizes(wr.final), n=wr.final_evidence.n,
            cost=wr.final_evidence.cost_naive, watershed_count=len(members),
            shadowed=bool(shadowed.get(term_key, False))))
    optima.sort(key=lambda o: (o.cost, o.key))

    n3 = [o for o in optima if o.n == 3]
    distinct_count = len(optima)
    cheapest_cost = min((o.cost for o in optima), default=0)

    # PM1 — >= 2 distinct N=3 optima.
    pm1 = "held" if len(n3) >= 2 else "refuted"

    # PM2 — every merge-direction (start_n>3) start reaching N=3 is strictly
    # cheaper than the monolith (start_n==1) start's terminus.
    mono_keys = [sk for sk in bm.terminus_by_start
                 if len(sk.split(";")) == 1]
    if not mono_keys:
        pm2 = "refuted"
    else:
        mono_cost = bm.terminus_by_start[mono_keys[0]].final_evidence.cost_naive
        pm2 = "held"
        for start_key, wr in bm.terminus_by_start.items():
            start_n = len(start_key.split(";"))
            if start_n > 3 and wr.final_evidence.n == 3:
                if wr.final_evidence.cost_naive >= mono_cost:
                    pm2 = "refuted"
                    break

    # PM3 — no cheaper basin than E3's W2 hides.
    pm3 = "held" if cheapest_cost >= e3_w2_cost else "refuted"

    # PM4 — few-basin (<= 5 distinct optima).
    pm4 = "held" if distinct_count <= 5 else "refuted"

    sizes_present = {o.sizes for o in optima}
    consistency_ok = all(s in sizes_present for s in e3_known_sizes)

    return BasinReport(
        optima=optima,
        priors={"PM1": pm1, "PM2": pm2, "PM3": pm3, "PM4": pm4},
        consistency_ok=consistency_ok, cheapest_cost=cheapest_cost,
        distinct_count=distinct_count)
