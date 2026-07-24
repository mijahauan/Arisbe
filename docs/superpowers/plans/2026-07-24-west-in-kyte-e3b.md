# West-in-kytē E3b (the basin map) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Map the Arm-N local optima the E3 walk discipline reaches from a fixed structured start set, and their attractor sets, to characterize the multi-basin structure E3's PE2 revealed (spec `docs/superpowers/specs/2026-07-24-west-in-kyte-e3b-design.md`).

**Architecture:** One new unprotected module `src/west_basin_map.py` (deterministic start set, basin mapping via the verbatim E3 walk on a shared memo, the shortlist-shadowed diagnostic, the PM1–PM4 verdict layer) + driver `tools/run_west_e3b.py`. Everything reuses `src/west_meta_agon.py` **unchanged**; E3/E2/E2b entry points byte-frozen.

**Tech Stack:** Python 3.12, uv, pytest. No new dependencies.

## Global Constraints

- **Pre-registered knobs (spec §3–§6, fixed):** `SEED=20260721, F0=12, N_NOTES=40, P_BASE=0.15, JOURNAL=40, TTL=120, R=325, THETA=0.20, MERGE_K=3, MAX_ROUNDS=20, COMP_PARTS=(3,4), COMP_CAP=12, ARM="naive"`. E3 comparators: `E3_W1_COST=119935` (sizes `3/8/1`), `E3_W2_COST=101411` (sizes `10/1/1`).
- **`src/west_meta_agon.py` is byte-frozen** (and E2/E2b entry points). E3b only *imports* from it; never edit it. Zero protected-core change; if one seems needed, STOP and report.
- **Arm N only** — every walk/optimum/cost is `arm="naive"`. Arm-I is a control confirmed once in the driver, not mapped.
- **Numbers-only stdout** in the driver: bucketings print as sizes (`bucket_sizes`), never folder names. (Corpus synthetic; convention discipline — the E3/E2b custody rule.)
- **Determinism:** no RNG, no wall-clock in any decision path (wall seconds may be printed, never compared or stored in a decision field). Canonical folder order is lexicographic `sorted()` everywhere.
- Run all commands via `uv run …` from the repo root. Tests must not hit the network.

**Reused `west_meta_agon` API (exact signatures — do not redefine):**
- `Bucketing = Tuple[Tuple[str, ...], ...]`; `canonical(iterable_of_iterables) -> Bucketing`; `bucketing_key(b) -> str` (`"a,b;c;d"`); `bucket_sizes(b) -> str` (`"2/1/1"`).
- `split_moves(b) -> List[(label, Bucketing)]`; `merge_moves(b, manifest, k=3) -> List[(label, Bucketing)]` (top-k by cross-bucket link count; **pass a large k to get ALL pairwise merges**).
- `MemoEvaluator(root, manifest, *, rounds, ttl)` with `.evaluate(b) -> MetaEvidence`, `.hits`, `.misses`.
- `MetaEvidence` fields: `n, cost_naive, cost_incremental, gap, coverage, m_fed, k2, k3, cut_links, cv, mean_member`. `arm_cost(ev, arm) -> int`.
- `run_meta_walk(start, *, name, arm, manifest, evaluate, theta, merge_k=3, max_rounds=20, ledger_path=None) -> WalkResult`; `WalkResult` fields: `name, arm, start_key, rounds, final (Bucketing), final_evidence (MetaEvidence), halt ("converged"|"max_rounds"), moves (List[str])`.
- `west_measure.round_robin_buckets(folders, n) -> List[frozenset]`.

---

### Task 1: The deterministic structured start set

**Files:**
- Create: `src/west_basin_map.py`
- Test: `tests/test_west_basin_map.py`

**Interfaces:**
- Consumes: `west_meta_agon.canonical/bucketing_key/bucket_sizes`; `west_measure.round_robin_buckets`; `vault_generator.VaultManifest` (field `.folders`, a tuple of folder-name strings).
- Produces:
  - `contiguous_compositions(folders, parts: int, cap: int) -> List[Bucketing]` — the `cap` size-largest contiguous `parts`-block partitions of the sorted folders.
  - `structured_starts(manifest, *, comp_parts=(3, 4), comp_cap=12) -> List[Bucketing]` — round-robin N=1..F0 + the compositions + the three E3 starts, deduped by canonical key, deterministic order.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_west_basin_map.py`:

```python
"""West-in-kytē E3b — the basin map.
Spec: docs/superpowers/specs/2026-07-24-west-in-kyte-e3b-design.md"""

from vault_generator import CrossLink, VaultManifest

from west_meta_agon import bucketing_key
from west_basin_map import contiguous_compositions, structured_starts


def _manifest(folders, links=()):
    cross = tuple(
        CrossLink(source_note=f"{s}/n{i}.md", source_folder=s,
                  target_note=f"{t}/m{i}.md", target_folder=t)
        for i, (s, t) in enumerate(links))
    return VaultManifest(folders=tuple(folders), notes=(),
                         cross_links=cross, journal_len=0)


class TestContiguousCompositions:
    def test_three_parts_of_four_folders(self):
        m = _manifest(["a", "b", "c", "d"])
        comps = contiguous_compositions(m.folders, 3, cap=99)
        # compositions of 4 into 3 positive contiguous parts: (2,1,1),(1,2,1),(1,1,2)
        # sorted by size-tuple descending -> (2,1,1),(1,2,1),(1,1,2)
        assert [bucket_sizes(b) for b in comps] == ["2/1/1", "1/2/1", "1/1/2"]
        # (2,1,1) => contiguous blocks {a,b},{c},{d}
        assert comps[0] == (("a", "b"), ("c",), ("d",))

    def test_cap_takes_largest_first(self):
        m = _manifest(["a", "b", "c", "d", "e", "f"])
        comps = contiguous_compositions(m.folders, 2, cap=2)
        # compositions of 6 into 2 parts, size-desc: (5,1),(4,2),(3,3),(2,4),(1,5)
        # cap=2 -> (5,1),(4,2)
        assert [bucket_sizes(b) for b in comps] == ["5/1", "4/2"]

    def test_contiguous_assignment_in_sorted_order(self):
        m = _manifest(["d", "a", "c", "b"])  # unsorted input
        comps = contiguous_compositions(m.folders, 2, cap=1)  # (3,1)
        # sorted folders a,b,c,d ; (3,1) -> {a,b,c},{d}
        assert comps[0] == (("a", "b", "c"), ("d",))


class TestStructuredStarts:
    def test_includes_round_robin_endpoints_and_e3_starts(self):
        m = _manifest([f"Folder-{k}" for k in range(12)])
        starts = structured_starts(m, comp_parts=(3, 4), comp_cap=12)
        keys = {bucketing_key(b) for b in starts}
        fs = sorted(m.folders)
        n1 = bucketing_key(tuple((tuple(sorted(fs)),)))       # monolith
        n12 = bucketing_key(tuple((f,) for f in fs))          # singletons
        mid = bucketing_key(
            __import__("west_meta_agon").canonical(
                [fs[0:6], fs[6:9], fs[9:11], fs[11:12]]))     # 6/3/2/1
        assert n1 in keys and n12 in keys and mid in keys

    def test_deduped_and_deterministic(self):
        m = _manifest([f"Folder-{k}" for k in range(12)])
        a = structured_starts(m, comp_parts=(3, 4), comp_cap=12)
        b = structured_starts(m, comp_parts=(3, 4), comp_cap=12)
        keys = [bucketing_key(x) for x in a]
        assert keys == [bucketing_key(x) for x in b]          # deterministic
        assert len(keys) == len(set(keys))                    # deduped
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_west_basin_map.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'west_basin_map'`

- [ ] **Step 3: Write the implementation**

Create `src/west_basin_map.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_west_basin_map.py -q`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add src/west_basin_map.py tests/test_west_basin_map.py
git commit -m "west-e3b: deterministic structured start set (Task 1)"
```

---

### Task 2: `map_basins` + `BasinMap` — descend every start, invert to watersheds

**Files:**
- Modify: `src/west_basin_map.py` (append)
- Test: `tests/test_west_basin_map.py` (append)

**Interfaces:**
- Consumes: Task 1's `structured_starts`; `west_meta_agon.MemoEvaluator/run_meta_walk/bucketing_key/bucket_sizes`.
- Produces:
  - `@dataclass BasinMap`: `terminus_by_start: Dict[str, WalkResult]` (start_key → its Arm-N walk result), `watersheds: Dict[str, List[str]]` (terminus_key → sorted list of start_keys), `evaluator: MemoEvaluator`, `manifest`.
  - `map_basins(root, manifest, starts, *, rounds, ttl, theta, merge_k=3, max_rounds=20) -> BasinMap` — one shared `MemoEvaluator`; each start descended via `run_meta_walk` (arm="naive", `ledger_path=None`); watersheds inverted from termini.
  - `distinct_optima(bm: BasinMap) -> List[str]` — sorted distinct terminus keys.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_west_basin_map.py`:

```python
import pytest

from vault_generator import generate_vault
from west_meta_agon import MemoEvaluator, bucket_sizes, run_meta_walk

from west_basin_map import BasinMap, distinct_optima, map_basins


@pytest.fixture(scope="module")
def small_vault(tmp_path_factory):
    dest = tmp_path_factory.mktemp("e3b")
    manifest = generate_vault(dest, seed=20260721, folders=4,
                              notes_per_folder=3,
                              cross_folder_link_prob=0.5, journal_len=3)
    return dest, manifest


class TestMapBasins:
    def test_terminus_matches_direct_walk(self, small_vault):
        dest, manifest = small_vault
        starts = structured_starts(manifest, comp_parts=(2, 3), comp_cap=4)
        bm = map_basins(dest, manifest, starts, rounds=12, ttl=120, theta=0.2)
        # Every recorded terminus is a converged halt.
        for wr in bm.terminus_by_start.values():
            assert wr.halt == "converged"
        # Re-running one start's walk directly reproduces its terminus.
        s0 = starts[0]
        direct = run_meta_walk(s0, name="chk", arm="naive", manifest=manifest,
                               evaluate=MemoEvaluator(dest, manifest, rounds=12,
                                                      ttl=120).evaluate,
                               theta=0.2)
        assert (bm.terminus_by_start[bucketing_key(s0)].final_evidence.cost_naive
                == direct.final_evidence.cost_naive)

    def test_watersheds_partition_the_starts(self, small_vault):
        dest, manifest = small_vault
        starts = structured_starts(manifest, comp_parts=(2, 3), comp_cap=4)
        bm = map_basins(dest, manifest, starts, rounds=12, ttl=120, theta=0.2)
        # Every start appears in exactly one watershed; the union is all starts.
        flat = [s for members in bm.watersheds.values() for s in members]
        assert sorted(flat) == sorted(bucketing_key(s) for s in starts)
        assert len(flat) == len(set(flat))          # disjoint
        # Each watershed key is a terminus of each of its members.
        for term_key, members in bm.watersheds.items():
            for s_key in members:
                assert bucketing_key(bm.terminus_by_start[s_key].final) == term_key

    def test_shared_memo_saves_evals(self, small_vault):
        dest, manifest = small_vault
        starts = structured_starts(manifest, comp_parts=(2, 3), comp_cap=4)
        bm = map_basins(dest, manifest, starts, rounds=12, ttl=120, theta=0.2)
        assert bm.evaluator.hits > 0        # overlap across starts was reused
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_west_basin_map.py -q`
Expected: FAIL — `ImportError: cannot import name 'map_basins'`

- [ ] **Step 3: Append the implementation**

Append to `src/west_basin_map.py` (add the imports to the top-of-file import block):

```python
from dataclasses import dataclass
from typing import Dict

from west_meta_agon import MemoEvaluator, WalkResult, run_meta_walk


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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_west_basin_map.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/west_basin_map.py tests/test_west_basin_map.py
git commit -m "west-e3b: map_basins + watershed inversion (Task 2)"
```

---

### Task 3: `full_neighbourhood_improver` — the `shortlist_shadowed` diagnostic

**Files:**
- Modify: `src/west_basin_map.py` (append)
- Test: `tests/test_west_basin_map.py` (append)

**Interfaces:**
- Consumes: `west_meta_agon.split_moves/merge_moves/arm_cost`.
- Produces: `full_neighbourhood_improver(bucketing, manifest, evaluate, *, theta, arm="naive") -> bool` — does the FULL neighbourhood (all splits + **all** pairwise merges, no shortlist) contain a gap-admissible strict Arm-N improver? `evaluate` is any `Callable[[Bucketing], MetaEvidence]` (the shared memo in the driver; a fake in tests).

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_west_basin_map.py`:

```python
from west_meta_agon import MetaEvidence, canonical

from west_basin_map import full_neighbourhood_improver


def _ev(n, naive, gap=0.0):
    return MetaEvidence(n=n, cost_naive=naive, cost_incremental=naive, gap=gap,
                        coverage=1.0 - gap, m_fed=0, k2=None, k3=0.0,
                        cut_links=0, cv=0.0, mean_member=0.0)


class TestShadowDiagnostic:
    def test_shortlist_hides_an_improving_merge(self):
        # 4 singletons, no links -> merge_moves(k=3) would shortlist by weight,
        # but the ONLY cheaper child is a low-weight merge the top-3 could rank
        # out. full_neighbourhood_improver must still find it.
        m = _manifest(["a", "b", "c", "d"])
        incumbent = canonical([["a"], ["b"], ["c"], ["d"]])   # N=4
        table = {bucketing_key(incumbent): _ev(4, 100)}
        # exactly one cheaper neighbour: merging c+d (a low/zero-weight pair)
        cheaper = canonical([["a"], ["b"], ["c", "d"]])
        table[bucketing_key(cheaper)] = _ev(3, 50)

        def evaluate(b):
            return table.get(bucketing_key(b), _ev(len(b), 999))

        assert full_neighbourhood_improver(
            incumbent, m, evaluate, theta=0.2) is True

    def test_true_optimum_has_no_improver(self):
        m = _manifest(["a", "b", "c", "d"])
        incumbent = canonical([["a", "b"], ["c", "d"]])
        table = {}

        def evaluate(b):
            # incumbent is 100; every neighbour is dearer.
            return _ev(len(b), 100 if bucketing_key(b) ==
                       bucketing_key(incumbent) else 200)

        assert full_neighbourhood_improver(
            incumbent, m, evaluate, theta=0.2) is False

    def test_incoherent_cheaper_neighbour_is_not_an_improver(self):
        # a cheaper neighbour with gap>theta is refused -> not a shadow.
        m = _manifest(["a", "b", "c", "d"])
        incumbent = canonical([["a", "b"], ["c", "d"]])
        table = {bucketing_key(incumbent): _ev(2, 100)}

        def evaluate(b):
            if bucketing_key(b) == bucketing_key(incumbent):
                return _ev(2, 100)
            return _ev(len(b), 10, gap=0.5)     # cheaper but incoherent

        assert full_neighbourhood_improver(
            incumbent, m, evaluate, theta=0.2) is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_west_basin_map.py -q`
Expected: FAIL — `ImportError: cannot import name 'full_neighbourhood_improver'`

- [ ] **Step 3: Append the implementation**

Append to `src/west_basin_map.py` (add `split_moves`, `merge_moves`, `arm_cost` to the top-of-file `west_meta_agon` import):

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_west_basin_map.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/west_basin_map.py tests/test_west_basin_map.py
git commit -m "west-e3b: full-neighbourhood shortlist_shadowed diagnostic (Task 3)"
```

---

### Task 4: `assemble_basin_report` — the optima table + PM1–PM4 (killer fixtures per conjunct)

**Files:**
- Modify: `src/west_basin_map.py` (append)
- Test: `tests/test_west_basin_map.py` (append)

**Interfaces:**
- Consumes: Task 2's `BasinMap`; `west_meta_agon.bucket_sizes/bucketing_key`.
- Produces:
  - `@dataclass Optimum`: `key: str, sizes: str, n: int, cost: int, watershed_count: int, shadowed: bool`.
  - `@dataclass BasinReport`: `optima: List[Optimum]` (cost-ascending), `priors: Dict[str, str]`, `consistency_ok: bool`, `cheapest_cost: int`, `distinct_count: int`.
  - `assemble_basin_report(bm, shadowed, *, e3_w1_cost=119935, e3_w2_cost=101411, e3_known_sizes=("3/8/1", "10/1/1")) -> BasinReport` — `shadowed` is `Dict[terminus_key, bool]` (computed by the driver via Task 3). Verdict rules (spec §6, exact):
    - **PM1** `held` iff ≥2 distinct optima with `n == 3`, else `refuted`.
    - **PM2** `held` iff every start with `start_n > 3` whose terminus has `n == 3` reaches a cost **strictly less than** the monolith start's terminus cost (the start with `start_n == 1`); else `refuted`. (`start_n = len(start_key.split(";"))`.) If no monolith start is present, PM2 is `refuted` (the map is malformed — it must include N=1).
    - **PM3** `held` iff `cheapest_cost >= e3_w2_cost`, else `refuted`.
    - **PM4** `held` iff `distinct_count <= 5`, else `refuted`.
    - `consistency_ok` iff both `e3_known_sizes` appear among the optima's `sizes`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_west_basin_map.py`. Build a `BasinMap` by hand from tiny fake `WalkResult`s so the verdict logic is tested in isolation:

```python
from west_meta_agon import WalkResult

from west_basin_map import BasinReport, Optimum, assemble_basin_report


def _wr(start_key, term_bucketing, cost):
    ev = _ev(len(term_bucketing), cost)
    return WalkResult(name="b", arm="naive", start_key=start_key, rounds=[],
                      final=term_bucketing, final_evidence=ev,
                      halt="converged", moves=[])


def _bm(entries):
    """entries: list of (start_key, terminus_bucketing, cost)."""
    tbs = {sk: _wr(sk, tb, c) for sk, tb, c in entries}
    watersheds = {}
    for sk, wr in tbs.items():
        watersheds.setdefault(bucketing_key(wr.final), []).append(sk)
    for m_ in watersheds.values():
        m_.sort()
    return BasinMap(terminus_by_start=tbs, watersheds=watersheds,
                    evaluator=None, manifest=None)


# canonical N=3 optima used across the verdict tests. bucket_sizes renders
# sizes in CANONICAL bucket order (buckets sorted lexicographically by
# content), NOT size order — so the fixtures are built so the big bucket sorts
# first (its min element "Folder-0" precedes the singletons' "Folder-10"/"-11").
CHEAP = canonical([[f"Folder-{k}" for k in range(10)],       # Folder-0..9
                   ["Folder-10"], ["Folder-11"]])            # -> "10/1/1"
DEAR = canonical([[f"Folder-{k}" for k in range(0, 3)],      # Folder-0,1,2
                  [f"Folder-{k}" for k in range(3, 11)],     # Folder-3..10 (min "Folder-10")
                  ["Folder-11"]])                            # -> "3/8/1"
# sanity (the fixtures must render the E3-known sizes, else consistency breaks):
assert bucket_sizes(CHEAP) == "10/1/1"
assert bucket_sizes(DEAR) == "3/8/1"


def _mono_key():
    return bucketing_key(canonical([[f"Folder-{k}" for k in range(12)]]))


class TestVerdictLayer:
    def test_all_expected_baseline(self):
        # monolith (N=1) -> DEAR@120k ; a merge start (N=12) -> CHEAP@101k
        bm = _bm([(_mono_key(), DEAR, 119935),
                  (bucketing_key(canonical([[f"Folder-{k}"] for k in range(12)])),
                   CHEAP, 101411)])
        shadowed = {bucketing_key(DEAR): False, bucketing_key(CHEAP): False}
        rep = assemble_basin_report(bm, shadowed)
        assert rep.priors == {"PM1": "held", "PM2": "held",
                              "PM3": "held", "PM4": "held"}
        assert rep.consistency_ok is True
        assert rep.cheapest_cost == 101411
        assert rep.distinct_count == 2
        # optima cost-ascending
        assert [o.cost for o in rep.optima] == [101411, 119935]

    def test_pm1_single_n3_optimum_refutes(self):
        mono = _mono_key()
        # both starts land in the same optimum -> only ONE distinct N=3 optimum
        bm = _bm([(mono, CHEAP, 101411),
                  (bucketing_key(canonical([[f"Folder-{k}"] for k in range(12)])),
                   CHEAP, 101411)])
        rep = assemble_basin_report(bm, {bucketing_key(CHEAP): False})
        assert rep.priors["PM1"] == "refuted"

    def test_pm2_merge_start_dearer_than_monolith_refutes(self):
        mono = _mono_key()
        merge_start = bucketing_key(
            canonical([[f"Folder-{k}"] for k in range(12)]))   # N=12
        # monolith reaches CHEAP@101k, merge start reaches DEAR@120k -> refute
        bm = _bm([(mono, CHEAP, 101411), (merge_start, DEAR, 119935)])
        shadowed = {bucketing_key(CHEAP): False, bucketing_key(DEAR): False}
        rep = assemble_basin_report(bm, shadowed)
        assert rep.priors["PM2"] == "refuted"

    def test_pm2_refuted_when_no_monolith_start(self):
        merge_start = bucketing_key(
            canonical([[f"Folder-{k}"] for k in range(12)]))
        bm = _bm([(merge_start, CHEAP, 101411)])
        rep = assemble_basin_report(bm, {bucketing_key(CHEAP): False})
        assert rep.priors["PM2"] == "refuted"

    def test_pm3_cheaper_basin_refutes(self):
        mono = _mono_key()
        merge_start = bucketing_key(
            canonical([[f"Folder-{k}"] for k in range(12)]))
        bm = _bm([(mono, DEAR, 119935), (merge_start, CHEAP, 90000)])  # < 101411
        shadowed = {bucketing_key(DEAR): False, bucketing_key(CHEAP): False}
        rep = assemble_basin_report(bm, shadowed)
        assert rep.priors["PM3"] == "refuted"
        assert rep.cheapest_cost == 90000

    def test_pm4_more_than_five_optima_refutes(self):
        mono = _mono_key()
        entries = [(mono, DEAR, 119935)]
        # add six MORE distinct N=2 optima (7 total > 5)
        for k in range(6):
            term = canonical([[f"Folder-{k}"],
                              [f"Folder-{j}" for j in range(12) if j != k]])
            entries.append((bucketing_key(term), term, 130000 + k))
        bm = _bm(entries)
        shadowed = {t: False for t in bm.watersheds}
        rep = assemble_basin_report(bm, shadowed)
        assert rep.priors["PM4"] == "refuted"

    def test_consistency_fails_when_known_optimum_absent(self):
        mono = _mono_key()
        # only CHEAP present, DEAR (3/8/1) missing
        bm = _bm([(mono, CHEAP, 101411)])
        rep = assemble_basin_report(bm, {bucketing_key(CHEAP): False})
        assert rep.consistency_ok is False

    def test_shadowed_flag_carried_onto_optimum(self):
        mono = _mono_key()
        bm = _bm([(mono, CHEAP, 101411)])
        rep = assemble_basin_report(bm, {bucketing_key(CHEAP): True})
        opt = [o for o in rep.optima if o.sizes == "10/1/1"][0]
        assert opt.shadowed is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_west_basin_map.py -q`
Expected: FAIL — `ImportError: cannot import name 'assemble_basin_report'`

- [ ] **Step 3: Append the implementation**

Append to `src/west_basin_map.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_west_basin_map.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/west_basin_map.py tests/test_west_basin_map.py
git commit -m "west-e3b: assemble_basin_report — PM1-PM4 verdicts + optima table (Task 4)"
```

---

### Task 5: The numbers-only driver + contract test + gitignore

**Files:**
- Create: `tools/run_west_e3b.py`
- Modify: `.gitignore` (append two lines after the `!runs/WEST_E3_LOG.md` line)
- Test: `tests/test_run_west_e3b_driver.py`

**Interfaces:**
- Consumes: everything above; `vault_generator.generate_vault`; `west_meta_agon.canonical/bucket_sizes/bucketing_key/run_meta_walk/MemoEvaluator`.
- Produces stdout contract (each line `flush=True`):
  - header `=== West-in-kytē E3b — the basin map (numbers only) ===` + config line
  - `start=<sizes> -> optimum=<sizes> cost=<n>` per structured start
  - `optimum sizes=<s> n=<n> cost=<c> watershed=<w> shadowed=<bool>` per distinct optimum (cost-ascending)
  - `consistency_ok=<bool> cheapest=<c> distinct_optima=<n>`
  - `arm_i_control final_n=<n> final_sizes=<s>` (one Arm-I walk from N=1 → expect finest)
  - `priors: {...}`, `determinism_canary: PASS|FAIL`, a `notes:` block

- [ ] **Step 1: Write the failing contract test**

Create `tests/test_run_west_e3b_driver.py`:

```python
"""Driver contract: tools/run_west_e3b.py --smoke runs end-to-end and prints
the numbers-only basin-map lines."""

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def test_smoke_driver_contract(tmp_path):
    proc = subprocess.run(
        [sys.executable, str(REPO / "tools" / "run_west_e3b.py"),
         "--smoke", "--dest", str(tmp_path)],
        capture_output=True, text=True, timeout=600)
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout
    assert "West-in-kytē E3b" in out
    assert "optimum sizes=" in out
    assert "consistency_ok=" in out
    assert "arm_i_control" in out
    assert "priors: {" in out
    assert "determinism_canary: PASS" in out
    assert "notes:" in out
    assert "Folder-" not in out          # numbers-only custody
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_run_west_e3b_driver.py -q`
Expected: FAIL — driver does not exist.

- [ ] **Step 3: Write the driver**

Create `tools/run_west_e3b.py`:

```python
"""West-in-kytē E3b driver — the basin map: descend a fixed structured start
set through the E3 Arm-N walk, enumerate the reached optima and their
watersheds, run the shortlist_shadowed diagnostic, decide PM1-PM4.

Numbers-only stdout (custody): bucketings print as sizes, never folder names.
Spec: docs/superpowers/specs/2026-07-24-west-in-kyte-e3b-design.md"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from vault_generator import generate_vault
from west_meta_agon import (MemoEvaluator, bucket_sizes, bucketing_key,
                            canonical, run_meta_walk)
from west_basin_map import (assemble_basin_report, full_neighbourhood_improver,
                            map_basins, structured_starts)

# Pre-registered E3b knobs (spec §3-§6 — fixed).
SEED = 20260721
F0 = 12
N_NOTES = 40
P_BASE = 0.15
JOURNAL = 40
TTL = 120
R_FIXED = 325
THETA = 0.20
MERGE_K = 3
MAX_ROUNDS = 20
COMP_PARTS = (3, 4)
COMP_CAP = 12

# Smoke — driver contract test only, never a real run.
SMOKE_F0 = 4
SMOKE_NOTES = 3
SMOKE_JOURNAL = 3
SMOKE_R = 12
SMOKE_PARTS = (2, 3)
SMOKE_CAP = 4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", default=None)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--no-canary", action="store_true")
    args = ap.parse_args()

    import tempfile
    dest = Path(args.dest) if args.dest else Path(tempfile.mkdtemp(prefix="west_e3b_"))
    dest.mkdir(parents=True, exist_ok=True)

    if args.smoke:
        f0, notes, journal, rfix = SMOKE_F0, SMOKE_NOTES, SMOKE_JOURNAL, SMOKE_R
        parts, cap = SMOKE_PARTS, SMOKE_CAP
        mode = "smoke"
    else:
        f0, notes, journal, rfix = F0, N_NOTES, JOURNAL, R_FIXED
        parts, cap = COMP_PARTS, COMP_CAP
        mode = "full"

    print("=== West-in-kytē E3b — the basin map (numbers only) ===", flush=True)
    print(f"mode={mode} seed={SEED} F0={f0} n={notes} p_base={P_BASE} "
          f"J={journal} ttl={TTL} R={rfix} theta={THETA} merge_k={MERGE_K} "
          f"max_rounds={MAX_ROUNDS} comp_parts={parts} comp_cap={cap}",
          flush=True)

    vault = dest / "vault"
    manifest = generate_vault(vault, seed=SEED, folders=f0,
                              notes_per_folder=notes,
                              cross_folder_link_prob=P_BASE,
                              journal_len=journal)
    starts = structured_starts(manifest, comp_parts=parts, comp_cap=cap)
    print(f"structured_starts={len(starts)}", flush=True)

    t0 = time.time()
    bm = map_basins(vault, manifest, starts, rounds=rfix, ttl=TTL, theta=THETA,
                    merge_k=MERGE_K, max_rounds=MAX_ROUNDS)

    for b in starts:
        wr = bm.terminus_by_start[bucketing_key(b)]
        print(f"start={bucket_sizes(b)} -> optimum={bucket_sizes(wr.final)} "
              f"cost={wr.final_evidence.cost_naive}", flush=True)

    # The shortlist_shadowed diagnostic per distinct optimum (shared memo).
    shadowed = {}
    for term_key, members in bm.watersheds.items():
        wr = bm.terminus_by_start[members[0]]
        shadowed[term_key] = full_neighbourhood_improver(
            wr.final, manifest, bm.evaluator.evaluate, theta=THETA)

    rep = assemble_basin_report(bm, shadowed)
    for o in rep.optima:
        print(f"optimum sizes={o.sizes} n={o.n} cost={o.cost} "
              f"watershed={o.watershed_count} shadowed={o.shadowed}", flush=True)
    print(f"consistency_ok={rep.consistency_ok} cheapest={rep.cheapest_cost} "
          f"distinct_optima={rep.distinct_count} "
          f"memo_hits={bm.evaluator.hits} memo_misses={bm.evaluator.misses} "
          f"wall_s={round(time.time() - t0, 1)}", flush=True)

    # Arm-I control: one walk from N=1 should run to the finest partition.
    fs = sorted(manifest.folders)
    ctrl = run_meta_walk(canonical([fs]), name="ctrl", arm="incremental",
                         manifest=manifest,
                         evaluate=MemoEvaluator(vault, manifest, rounds=rfix,
                                                ttl=TTL).evaluate,
                         theta=THETA, merge_k=MERGE_K, max_rounds=MAX_ROUNDS)
    print(f"arm_i_control final_n={ctrl.final_evidence.n} "
          f"final_sizes={bucket_sizes(ctrl.final)}", flush=True)

    print(f"priors: {rep.priors}", flush=True)

    canary = "skipped"
    if not args.no_canary:
        # Re-run a deterministic mid-set start with a CLEARED memo and compare
        # to its recorded terminus (it is guaranteed to be in `starts`).
        cstart = starts[len(starts) // 2]
        fresh = MemoEvaluator(vault, manifest, rounds=rfix, ttl=TTL)
        again = run_meta_walk(cstart, name="canary", arm="naive",
                              manifest=manifest, evaluate=fresh.evaluate,
                              theta=THETA, merge_k=MERGE_K,
                              max_rounds=MAX_ROUNDS)
        ref = bm.terminus_by_start[bucketing_key(cstart)]
        same = (again.moves == ref.moves and again.final == ref.final
                and again.final_evidence.cost_naive
                == ref.final_evidence.cost_naive)
        canary = "PASS" if same else "FAIL"
    print(f"determinism_canary: {canary}", flush=True)

    print("notes: E3b maps the Arm-N basins THIS walk discipline (full-slate "
          "steepest descent, top-3 link-guided merge shortlist) reaches from a "
          "FIXED structured start set (round-robin N=1..F0 + capped contiguous "
          "3/4-part compositions + the three E3 starts) — not the landscape's "
          "optima in the absolute. shortlisted=True on an optimum means its FULL "
          "neighbourhood (all pairwise merges) has a cheaper coherent point the "
          "top-3 attention could not see — a disclosed confound, never acted on. "
          "Watershed counts are over the seed set, NOT an unbiased attractor "
          "measure. PM1 = >=2 distinct N=3 optima; PM2 = merge-direction starts "
          "(N>3) reach strictly cheaper than the monolith start; PM3 = no basin "
          "below E3's W2 (101,411); PM4 = <=5 distinct optima. Arm-N interleaving "
          "assumption carries (verdict-bearing). Synthetic corpus, one seed: the "
          "basin structure is the generator's. A meta-Agon is not a community "
          "(THE_COMMENS).", flush=True)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Append the gitignore entries**

In `.gitignore`, directly after the `!runs/WEST_E3_LOG.md` line, append:

```
# E3b (same pattern: outputs ignored, the tracked run log spared).
runs/west_e3b*
!runs/WEST_E3B_LOG.md
```

- [ ] **Step 5: Run the contract test + verify ignore**

Run: `uv run pytest tests/test_run_west_e3b_driver.py -q`
Expected: PASS (allow ~3 min; smoke corpus is tiny)

Run: `git check-ignore -v runs/west_e3b_run1/ ; git check-ignore -v runs/WEST_E3B_LOG.md`
Expected: first matches `runs/west_e3b*`; second reports the `!` negation rule.

- [ ] **Step 6: Commit**

```bash
git add tools/run_west_e3b.py tests/test_run_west_e3b_driver.py .gitignore
git commit -m "west-e3b: numbers-only driver + smoke contract + gitignore (Task 5)"
```

---

### Task 6: Full-suite gate + byte-freeze audit

**Files:** none created; verification only.

- [ ] **Step 1: Byte-freeze audit**

Run: `git diff main -- src/west_meta_agon.py src/west_experiment.py src/west_measure.py src/west_coordinator.py src/vault_generator.py tools/run_west_e3.py tools/run_west_e2b.py tools/run_west_e2.py`
Expected: EMPTY (E3b only *adds* `west_basin_map.py` + its driver/tests; it touches no prior West file).

- [ ] **Step 2: Full test suite**

Run: `uv run pytest tests/ -q`
Expected: everything passes (4100+ at branch base; new tests add to that; 0 failed). Paste the tail into the task report.

- [ ] **Step 3: Quality gate**

Run: `uv run python tools/quality_gate_system.py`
Expected: passes.

- [ ] **Step 4: Report ready-to-merge**

```bash
git status --short   # clean but for untracked runs/run13_console.txt
```

---

## Execution notes (for the orchestrator)

- Tasks 1→5 are sequential (each appends to the same module/test file). Task boundaries are the review gates; Task 4 (the verdict layer) is the mutation-prone one — per-task review should re-derive PM1–PM4 and hunt surviving mutations, as with every prior West verdict layer.
- The RUN itself (the full driver invocation, `runs/WEST_E3B_LOG.md`, CURRENT_PLAN/memory updates) is NOT part of this plan — it follows after merge, as with E3.
```
