"""West-in-kytē E3b — the basin map (endogenous-partition landscape census):
enumerate the Arm-N local optima the E3 walk discipline reaches from a fixed
structured start set, and their attractor sets.

Spec: docs/superpowers/specs/2026-07-24-west-in-kyte-e3b-design.md
Reuses west_meta_agon UNCHANGED; unprotected, additive."""

from dataclasses import dataclass
from typing import Dict, List

from west_meta_agon import Bucketing, MemoEvaluator, WalkResult, bucketing_key, canonical, run_meta_walk
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
               merge_k: int = 3, max_rounds: int = 20) -> BasinMap:
    """Descend each structured start through the verbatim E3 Arm-N walk on ONE
    shared MemoEvaluator (spec §2-§4); invert termini to watersheds."""
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
