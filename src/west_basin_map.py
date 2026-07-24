"""West-in-kytē E3b — the basin map (endogenous-partition landscape census):
enumerate the Arm-N local optima the E3 walk discipline reaches from a fixed
structured start set, and their attractor sets.

Spec: docs/superpowers/specs/2026-07-24-west-in-kyte-e3b-design.md
Reuses west_meta_agon UNCHANGED; unprotected, additive."""

from typing import List

from west_meta_agon import Bucketing, bucketing_key, canonical
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
