# West-in-kytē E3 (endogenous partition) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the meta-Agon over folder-bucketings — split/merge walks on E2b's measured landscape (spec `docs/superpowers/specs/2026-07-23-west-in-kyte-e3-design.md`) — plus the rider E2b′ and the PE1–PE5 verdict layer, behind a numbers-only driver.

**Architecture:** One new unprotected module `src/west_meta_agon.py` (bucketing/moves/slate, memoized evaluator, panel + walk + JSONL ledger + replay, rider, verdicts) + one additive function in `src/west_experiment.py` (`run_fed_bucketed_broker`) + driver `tools/run_west_e3.py`. Everything reuses the E2b harness (`run_fed_bucketed`, `round_robin_buckets`, `link_aware_buckets`, `cut_link_count`, `read_member_costs`).

**Tech Stack:** Python 3.12, uv, pytest. No new dependencies.

## Global Constraints

- **Pre-registered knobs (spec §2–§6, fixed):** `SEED=20260721, F0=12, NOTES=40, P_BASE=0.15, JOURNAL=40, TTL=120, R=325, THETA=0.20, TOL=0.10, MERGE_K=3, MAX_ROUNDS=20, TROUGH_E2B=137129, RIDER_TTLS=(60,30,15), RIDER_NS=(2,4), QUALITY_N=4`.
- **E1/E2/E2b entry points stay byte-frozen.** `west_experiment.py` may gain NEW functions only; never edit an existing function body. Zero protected-core change; if one seems needed, STOP and report.
- **Numbers-only stdout** in the driver: bucketings print as sizes (e.g. `sizes=6/3/2/1`), never folder names. (Corpus is synthetic; this is convention discipline.)
- **Determinism:** no wall-clock/randomness in any decision path (wall seconds may be *printed*, never recorded in a ledger row's decision fields or compared).
- Run all commands via `uv run …` from the repo root. Tests must not hit the network.
- Canonical folder order is **lexicographic `sorted()`** everywhere (folder names are `Folder-0`…`Folder-11`; lexicographic ≠ numeric — that is fine, it is pre-registered as *a* deterministic order, not a meaningful one).

---

### Task 1: Bucketing canonicalisation, moves, and the shortlisted slate

**Files:**
- Create: `src/west_meta_agon.py`
- Test: `tests/test_west_meta_agon.py`

**Interfaces:**
- Consumes: `vault_generator.VaultManifest` / `CrossLink` (fields: `source_note, source_folder, target_note, target_folder`).
- Produces (later tasks rely on these exact names):
  - `Bucketing = Tuple[Tuple[str, ...], ...]`
  - `canonical(buckets: Iterable[Iterable[str]]) -> Bucketing`
  - `bucketing_key(b: Bucketing) -> str`
  - `bucket_sizes(b: Bucketing) -> str` (e.g. `"6/3/2/1"`, in canonical bucket order)
  - `split_moves(b: Bucketing) -> List[Tuple[str, Bucketing]]` (labels `"split:<i>"`)
  - `merge_moves(b: Bucketing, manifest, k: int = 3) -> List[Tuple[str, Bucketing]]` (labels `"merge:<i>+<j>"`)
  - `slate_moves(b: Bucketing, manifest, k: int = 3) -> List[Tuple[str, Bucketing]]` (splits first, then merges)

- [ ] **Step 1: Write the failing tests**

Create `tests/test_west_meta_agon.py`:

```python
"""West-in-kytē E3 — meta-Agon over folder-bucketings.
Spec: docs/superpowers/specs/2026-07-23-west-in-kyte-e3-design.md"""

from vault_generator import CrossLink, VaultManifest

from west_meta_agon import (bucketing_key, bucket_sizes, canonical,
                            merge_moves, slate_moves, split_moves)


def _manifest(folders, links):
    """A hand-built manifest: links = [(src_folder, tgt_folder), ...]."""
    cross = tuple(
        CrossLink(source_note=f"{s}/n{i}.md", source_folder=s,
                  target_note=f"{t}/m{i}.md", target_folder=t)
        for i, (s, t) in enumerate(links)
    )
    return VaultManifest(folders=tuple(folders), notes=(),
                         cross_links=cross, journal_len=0)


class TestCanonical:
    def test_canonical_sorts_within_and_across_buckets(self):
        b = canonical([["b", "a"], ["d"], ["c"]])
        assert b == (("a", "b"), ("c",), ("d",))

    def test_key_is_stable_and_order_independent(self):
        b1 = canonical([["b", "a"], ["c"]])
        b2 = canonical([["c"], ["a", "b"]])
        assert bucketing_key(b1) == bucketing_key(b2) == "a,b;c"

    def test_sizes_string(self):
        assert bucket_sizes((("a", "b", "c"), ("d",))) == "3/1"


class TestSplitMoves:
    def test_balanced_contiguous_split(self):
        b = canonical([["a", "b", "c", "d", "e"]])
        moves = split_moves(b)
        assert len(moves) == 1
        label, child = moves[0]
        assert label == "split:0"
        # ceil(5/2)=3 first, 2 rest, contiguous in sorted order.
        assert child == (("a", "b", "c"), ("d", "e"))

    def test_singletons_cannot_split(self):
        assert split_moves((("a",), ("b",))) == []

    def test_split_every_eligible_bucket(self):
        b = (("a", "b"), ("c",), ("d", "e"))
        labels = [m[0] for m in split_moves(b)]
        assert labels == ["split:0", "split:2"]


class TestMergeMoves:
    def test_shortlist_top_k_by_cross_bucket_links(self):
        # 4 singletons; links make (a,b) weight 3, (a,c) weight 2,
        # (b,c) weight 1, (c,d) weight 1 — tie broken by canonical pair.
        m = _manifest(
            ["a", "b", "c", "d"],
            [("a", "b"), ("a", "b"), ("b", "a"),
             ("a", "c"), ("c", "a"), ("b", "c"), ("c", "d")])
        b = canonical([["a"], ["b"], ["c"], ["d"]])
        moves = merge_moves(b, m, k=3)
        labels = [lab for lab, _ in moves]
        # top-3 pairs: (0,1) w=3, (0,2) w=2, then w=1 tie -> (1,2) before (2,3).
        assert labels == ["merge:0+1", "merge:0+2", "merge:1+2"]
        assert moves[0][1] == (("a", "b"), ("c",), ("d",))

    def test_all_pairs_when_fewer_than_k(self):
        m = _manifest(["a", "b"], [])
        b = canonical([["a"], ["b"]])
        assert [lab for lab, _ in merge_moves(b, m, k=3)] == ["merge:0+1"]

    def test_n1_cannot_merge(self):
        m = _manifest(["a", "b"], [])
        assert merge_moves((("a", "b"),), m) == []


class TestSlate:
    def test_splits_first_then_merges_deterministic(self):
        m = _manifest(["a", "b", "c"], [("a", "c")])
        b = (("a", "b"), ("c",))
        labels = [lab for lab, _ in slate_moves(b, m, k=3)]
        assert labels == ["split:0", "merge:0+1"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_west_meta_agon.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'west_meta_agon'`

- [ ] **Step 3: Write the implementation**

Create `src/west_meta_agon.py`:

```python
"""West-in-kytē E3 — the meta-Agon over folder-bucketings (endogenous
partition): split/merge as licensed, recorded moves adjudicated on measured
cost/gap evidence, walked by full-slate steepest descent.

Spec: docs/superpowers/specs/2026-07-23-west-in-kyte-e3-design.md
Unprotected, additive; E1/E2/E2b entry points untouched."""

from typing import Iterable, List, Tuple

Bucketing = Tuple[Tuple[str, ...], ...]


def canonical(buckets: Iterable[Iterable[str]]) -> Bucketing:
    """Canonical form: each bucket lexicographically sorted, buckets ordered
    by their sorted content. The memo key and ledger id derive from this."""
    return tuple(sorted(tuple(sorted(b)) for b in buckets))


def bucketing_key(b: Bucketing) -> str:
    return ";".join(",".join(bucket) for bucket in b)


def bucket_sizes(b: Bucketing) -> str:
    """Numbers-only rendering for stdout (custody convention)."""
    return "/".join(str(len(bucket)) for bucket in b)


def split_moves(b: Bucketing) -> List[Tuple[str, Bucketing]]:
    """Every legal balanced contiguous split (spec §2): bucket i of size s>=2
    splits into its first ceil(s/2) folders vs the rest, in sorted order."""
    moves = []
    for i, bucket in enumerate(b):
        if len(bucket) < 2:
            continue
        half = (len(bucket) + 1) // 2
        child = list(b[:i]) + [bucket[:half], bucket[half:]] + list(b[i + 1:])
        moves.append((f"split:{i}", canonical(child)))
    return moves


def _pair_weight(b1: Tuple[str, ...], b2: Tuple[str, ...], manifest) -> int:
    """Cross-links between the two buckets, either direction."""
    s1, s2 = set(b1), set(b2)
    w = 0
    for cl in manifest.cross_links:
        if ((cl.source_folder in s1 and cl.target_folder in s2)
                or (cl.source_folder in s2 and cl.target_folder in s1)):
            w += 1
    return w


def merge_moves(b: Bucketing, manifest, k: int = 3) -> List[Tuple[str, Bucketing]]:
    """The top-k merge shortlist (spec §2, the slate economy): bucket-pairs
    ranked by cross-bucket link count, descending; ties by canonical pair
    index. Proposer attention, disclosed — never touches how a move is
    judged."""
    ranked = sorted(
        ((-_pair_weight(b[i], b[j], manifest), i, j)
         for i in range(len(b)) for j in range(i + 1, len(b))),
    )
    moves = []
    for _negw, i, j in ranked[:k]:
        child = [bucket for t, bucket in enumerate(b) if t not in (i, j)]
        child.append(b[i] + b[j])
        moves.append((f"merge:{i}+{j}", canonical(child)))
    return moves


def slate_moves(b: Bucketing, manifest, k: int = 3) -> List[Tuple[str, Bucketing]]:
    """The full slate the proposer tables each round: all legal splits, then
    the top-k merge shortlist (spec §2)."""
    return split_moves(b) + merge_moves(b, manifest, k=k)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_west_meta_agon.py -q`
Expected: PASS (9 tests)

- [ ] **Step 5: Commit**

```bash
git add src/west_meta_agon.py tests/test_west_meta_agon.py
git commit -m "west-e3: bucketing canonicalisation, split/merge moves, shortlisted slate (Task 1)"
```

---

### Task 2: `run_fed_bucketed_broker` — the bucketed broker path (additive to west_experiment)

**Files:**
- Modify: `src/west_experiment.py` (APPEND one function at end of file; touch nothing existing)
- Test: `tests/test_west_experiment_e3.py` (new file — keeps E2b's test files untouched)

**Interfaces:**
- Consumes: `run_fed_bucketed(root, manifest, *, buckets, rounds, ttl) -> (ArrangementResult, CoordinatorTax)` (existing, byte-frozen).
- Produces: `run_fed_bucketed_broker(root, manifest, *, buckets: List[frozenset], rounds: int, ttl: int) -> (ArrangementResult, CoordinatorTax)` — identical to `run_fed_bucketed` except: after the members run, the coordinator drives one `Coordinator.route` per **cross-bucket** link (a link inside one bucket needs no routing — same member), route attempts are added to `coordinator_cost`, and `ArrangementResult.routes` records the count. Later tasks read: `result.routes`, `result.cost.coordinator_cost`, `tax.cells_written`, `tax.naive_member_round`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_west_experiment_e3.py`:

```python
"""E3 additions to west_experiment: the bucketed broker path (spec §5b).
E1/E2/E2b entry points are byte-frozen; this file tests only the addition."""

import pytest

from vault_generator import generate_vault
from west_experiment import run_fed_bucketed, run_fed_bucketed_broker
from west_measure import round_robin_buckets


@pytest.fixture(scope="module")
def vault(tmp_path_factory):
    dest = tmp_path_factory.mktemp("e3broker")
    manifest = generate_vault(dest, seed=20260721, folders=4,
                              notes_per_folder=3,
                              cross_folder_link_prob=0.8, journal_len=3)
    return dest, manifest


def _cross_bucket_links(buckets, manifest):
    where = {}
    for i, b in enumerate(buckets):
        for f in b:
            where[f] = i
    return [cl for cl in manifest.cross_links
            if where[cl.source_folder] != where[cl.target_folder]]


def test_broker_routes_cross_bucket_links_only(vault):
    dest, manifest = vault
    buckets = round_robin_buckets(manifest.folders, 2)
    res, _tax = run_fed_bucketed_broker(dest, manifest, buckets=buckets,
                                        rounds=12, ttl=120)
    assert res.routes == len(_cross_bucket_links(buckets, manifest))
    assert res.routes > 0  # p=0.8 on 4 folders guarantees cross links


def test_broker_equals_passive_plus_routes(vault):
    dest, manifest = vault
    buckets = round_robin_buckets(manifest.folders, 2)
    passive, ptax = run_fed_bucketed(dest, manifest, buckets=buckets,
                                     rounds=12, ttl=120)
    broker, btax = run_fed_bucketed_broker(dest, manifest, buckets=buckets,
                                           rounds=12, ttl=120)
    # Members are identical; only the coordinator differs by the route count.
    assert broker.cost.materialization_atoms == passive.cost.materialization_atoms
    assert broker.cost.peel_proxy == passive.cost.peel_proxy
    assert broker.cost.coordinator_cost == (passive.cost.coordinator_cost
                                            + broker.routes)
    assert broker.coverage == passive.coverage
    assert (btax.cells_written, btax.naive_member_round, btax.incremental) == \
        (ptax.cells_written, ptax.naive_member_round, ptax.incremental)


def test_single_bucket_routes_nothing(vault):
    dest, manifest = vault
    buckets = round_robin_buckets(manifest.folders, 1)
    res, _ = run_fed_bucketed_broker(dest, manifest, buckets=buckets,
                                     rounds=12, ttl=120)
    assert res.routes == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_west_experiment_e3.py -q`
Expected: FAIL — `ImportError: cannot import name 'run_fed_bucketed_broker'`

- [ ] **Step 3: Append the implementation to `src/west_experiment.py`**

Append at end of file (after `assemble_e2b_report`). The body mirrors
`run_fed_bucketed` (same member loop) plus the route pass — copy it exactly;
do NOT refactor the existing function (byte-frozen):

```python
def run_fed_bucketed_broker(root: Path, manifest, *, buckets: List[frozenset],
                            rounds: int, ttl: int):
    """E3 rider (E3 spec §5b): :func:`run_fed_bucketed` plus the active broker
    — after the members run, one :meth:`Coordinator.route` per CROSS-BUCKET
    link (a link inside one bucket resolves within its own member; only
    cross-bucket references need coordination). Route attempts are added to
    ``coordinator_cost`` and ``ArrangementResult.routes`` records the count.
    The broker tax remains an end-of-run snapshot (A3-style lower bound,
    disclosed — E2b spec §8). Additive: E1/E2/E2b entry points untouched."""
    member_specs = [(frozenset(b), False, f"e3_bucket_{i:02d}")
                    for i, b in enumerate(buckets)]
    member_specs.append((frozenset(), True, "e3_journal"))
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
        if folder_set:
            bucket_m = res.uod.current_egi
            for f in folder_set:
                member_ms[f] = bucket_m
            coord.ingest(uid, bucket_m)
            raw = list(tm.per_round_relations)
            trajectories[uid] = (
                raw[1:] + [member_relation_names(bucket_m)] if raw else []
            )

    conflicts = coord.consistency_scan()
    cov, _unresolved = coord.coverage(manifest, member_ms)

    where = {}
    for i, b in enumerate(buckets):
        for f in b:
            where[f] = i
    for cl in manifest.cross_links:
        if where.get(cl.source_folder) != where.get(cl.target_folder):
            coord.route(cl.source_folder, cl.target_note, cl.target_folder,
                        member_ms)
    coordinator_cost = coord.cells_written + coord.scan_comparisons + coord.routes

    cost = CostBreakdown(materialization_atoms=mat_atoms, peel_proxy=peel,
                         coordinator_cost=coordinator_cost)
    quality = QualityReading(
        k2_stick_rate=(sum(k2s) / len(k2s)) if k2s else None,
        k3_ratio=(sum(k3s) / len(k3s)) if k3s else 0.0,
        final_m_size=total_m,
    )
    arrangement = ArrangementResult(name="FED-bucketed-broker", cost=cost,
                                    quality=quality, member_costs=member_costs,
                                    coverage=cov, conflicts=conflicts,
                                    routes=coord.routes)
    return arrangement, replay_coordinator_tax(trajectories)
```

Note: `ArrangementResult` already has a `routes` field (used by
`run_fed_broker`); check its definition at the top of the file — if `routes`
defaults to `None` this works as-is. All names used (`_apportion`,
`_run_member_traced`, `Coordinator`, `peel_proxy`, `read_quality`,
`member_relation_names`, `CostBreakdown`, `QualityReading`,
`ArrangementResult`, `replay_coordinator_tax`) already exist in the module.

- [ ] **Step 4: Run tests to verify they pass; verify byte-freeze**

Run: `uv run pytest tests/test_west_experiment_e3.py -q`
Expected: PASS (3 tests)

Run: `git diff src/west_experiment.py | grep -E "^-" | grep -v "^---"`
Expected: NO output (pure append — nothing deleted or modified).

- [ ] **Step 5: Run the existing west tests (freeze check)**

Run: `uv run pytest tests/ -q -k "west"`
Expected: all pass, no regressions.

- [ ] **Step 6: Commit**

```bash
git add src/west_experiment.py tests/test_west_experiment_e3.py
git commit -m "west-e3: run_fed_bucketed_broker — bucketed broker path, additive (Task 2)"
```

---

### Task 3: `MetaEvidence` + the memoized evaluator

**Files:**
- Modify: `src/west_meta_agon.py` (append)
- Test: `tests/test_west_meta_agon.py` (append)

**Interfaces:**
- Consumes: `west_experiment.run_fed_bucketed`, `west_experiment.run_sweepb_point` (cross-check only), `west_measure.read_member_costs`, `west_measure.cut_link_count`, `west_measure.round_robin_buckets`; Task 1's `Bucketing`, `canonical`, `bucketing_key`.
- Produces:
  - `@dataclass MetaEvidence`: fields `n: int, cost_naive: int, cost_incremental: int, gap: float, coverage: float, m_fed: int, k2: Optional[float], k3: float, cut_links: int, cv: float, mean_member: float`
  - `class MemoEvaluator`: `__init__(self, root, manifest, *, rounds: int, ttl: int)`; `evaluate(self, b: Bucketing) -> MetaEvidence`; counters `self.hits: int`, `self.misses: int`
  - `arm_cost(ev: MetaEvidence, arm: str) -> int` (`arm` ∈ `"naive" | "incremental"`, else `ValueError`)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_west_meta_agon.py`:

```python
import pytest

from vault_generator import generate_vault
from west_experiment import run_sweepb_point
from west_measure import round_robin_buckets

from west_meta_agon import MemoEvaluator, MetaEvidence, arm_cost


@pytest.fixture(scope="module")
def small_vault(tmp_path_factory):
    dest = tmp_path_factory.mktemp("e3vault")
    manifest = generate_vault(dest, seed=20260721, folders=4,
                              notes_per_folder=3,
                              cross_folder_link_prob=0.5, journal_len=3)
    return dest, manifest


class TestMemoEvaluator:
    def test_matches_run_sweepb_point_on_round_robin(self, small_vault):
        dest, manifest = small_vault
        ev = MemoEvaluator(dest, manifest, rounds=12, ttl=120)
        b = canonical(round_robin_buckets(manifest.folders, 2))
        got = ev.evaluate(b)
        ref = run_sweepb_point(dest, manifest, n=2, rounds=12, ttl=120,
                               bucketing="round_robin")
        assert (got.n, got.cost_naive, got.cost_incremental) == \
            (ref.n, ref.fed_cost_naive, ref.fed_cost_incremental)
        assert got.gap == ref.gap
        assert got.m_fed == ref.m_fed
        assert got.cut_links == ref.cut_links
        assert got.cv == ref.member_reading.cv

    def test_memo_hit_skips_rerun(self, small_vault):
        dest, manifest = small_vault
        ev = MemoEvaluator(dest, manifest, rounds=12, ttl=120)
        b = canonical(round_robin_buckets(manifest.folders, 2))
        first = ev.evaluate(b)
        assert (ev.hits, ev.misses) == (0, 1)
        second = ev.evaluate(b)
        assert (ev.hits, ev.misses) == (1, 1)
        assert second is first  # the cached object, not a re-run

    def test_key_is_canonical_not_order(self, small_vault):
        dest, manifest = small_vault
        ev = MemoEvaluator(dest, manifest, rounds=12, ttl=120)
        f = sorted(manifest.folders)
        a = canonical([[f[0], f[1]], [f[2], f[3]]])
        b = canonical([[f[3], f[2]], [f[1], f[0]]])
        ev.evaluate(a)
        ev.evaluate(b)
        assert (ev.hits, ev.misses) == (1, 1)


class TestArmCost:
    def test_selects_currency(self):
        e = MetaEvidence(n=2, cost_naive=10, cost_incremental=7, gap=0.0,
                         coverage=1.0, m_fed=5, k2=1.0, k3=0.0, cut_links=1,
                         cv=0.0, mean_member=5.0)
        assert arm_cost(e, "naive") == 10
        assert arm_cost(e, "incremental") == 7
        with pytest.raises(ValueError):
            arm_cost(e, "mono")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_west_meta_agon.py -q`
Expected: FAIL — `ImportError: cannot import name 'MemoEvaluator'`

- [ ] **Step 3: Append the implementation**

Append to `src/west_meta_agon.py` (add the new imports at the top of the
file with the existing ones):

```python
from dataclasses import dataclass
from typing import Dict, Optional

from west_experiment import run_fed_bucketed
from west_measure import cut_link_count, read_member_costs


@dataclass
class MetaEvidence:
    """One evaluation of one bucketing at full R (spec §2): both arms' costs
    plus the reported-never-verdict-bearing vector (|M|, K2, K3)."""
    n: int
    cost_naive: int
    cost_incremental: int
    gap: float
    coverage: float
    m_fed: int
    k2: Optional[float]
    k3: float
    cut_links: int
    cv: float
    mean_member: float


def arm_cost(ev: MetaEvidence, arm: str) -> int:
    """The walk's adjudication currency (spec §2): Arm N for the main walks,
    Arm I for the control."""
    if arm == "naive":
        return ev.cost_naive
    if arm == "incremental":
        return ev.cost_incremental
    raise ValueError("arm must be 'naive' or 'incremental'")


class MemoEvaluator:
    """Memoized full-R evaluation, shared across every walk in one run
    (spec §2): deterministic harness => a revisited bucketing is free.
    ``hits``/``misses`` are printed by the driver (no silent caching)."""

    def __init__(self, root, manifest, *, rounds: int, ttl: int):
        self.root = root
        self.manifest = manifest
        self.rounds = rounds
        self.ttl = ttl
        self.hits = 0
        self.misses = 0
        self._memo: Dict[str, MetaEvidence] = {}

    def evaluate(self, b: Bucketing) -> MetaEvidence:
        key = bucketing_key(b)
        if key in self._memo:
            self.hits += 1
            return self._memo[key]
        self.misses += 1
        buckets = [frozenset(x) for x in b]
        fed, tax = run_fed_bucketed(self.root, self.manifest, buckets=buckets,
                                    rounds=self.rounds, ttl=self.ttl)
        base = fed.cost.materialization_atoms + fed.cost.peel_proxy
        reading = read_member_costs(fed.member_costs)
        ev = MetaEvidence(
            n=len(b),
            cost_naive=base + tax.cells_written + tax.naive_member_round,
            cost_incremental=base + tax.cells_written + tax.incremental,
            gap=1.0 - (fed.coverage if fed.coverage is not None else 1.0),
            coverage=(fed.coverage if fed.coverage is not None else 1.0),
            m_fed=fed.quality.final_m_size,
            k2=fed.quality.k2_stick_rate,
            k3=fed.quality.k3_ratio,
            cut_links=cut_link_count(buckets, self.manifest),
            cv=reading.cv,
            mean_member=reading.mean,
        )
        self._memo[key] = ev
        return ev
```

(The cost assembly copies `run_sweepb_point`'s exactly — the cross-check test
pins that equivalence.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_west_meta_agon.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/west_meta_agon.py tests/test_west_meta_agon.py
git commit -m "west-e3: MetaEvidence + memoized full-R evaluator (Task 3)"
```

---

### Task 4: The panel, the walk, the JSONL ledger, and `replay_walk`

**Files:**
- Modify: `src/west_meta_agon.py` (append)
- Test: `tests/test_west_meta_agon.py` (append)

**Interfaces:**
- Consumes: Task 1's `slate_moves`/`canonical`/`bucketing_key`; Task 3's `MetaEvidence`/`arm_cost`.
- Produces:
  - `@dataclass SlateEntry`: `move: str, key: str, evidence: MetaEvidence, refused: bool, improving: bool`
  - `@dataclass WalkRound`: `round_no: int, incumbent_key: str, incumbent_evidence: MetaEvidence, slate: List[SlateEntry], disposition: str, chosen_key: Optional[str]`
  - `@dataclass WalkResult`: `name: str, arm: str, start_key: str, rounds: List[WalkRound], final: Bucketing, final_evidence: MetaEvidence, halt: str` (`halt` ∈ `"converged" | "max_rounds"`), `moves: List[str]`
  - `run_meta_walk(start, *, name: str, arm: str, manifest, evaluate, theta: float, merge_k: int = 3, max_rounds: int = 20, ledger_path=None) -> WalkResult` — `evaluate` is any `Callable[[Bucketing], MetaEvidence]` (the real `MemoEvaluator.evaluate` or a test fake).
  - `replay_walk(ledger_path) -> dict` with keys `ok: bool, rounds: int, mismatches: List[str]` — recomputes every disposition from the RECORDED evidence (no re-evaluation).
  - Panel rule (spec §2, exact): refuse candidates with `evidence.gap > theta`; among non-refused candidates with `arm_cost(ev, arm) < arm_cost(incumbent_ev, arm)` strictly, accept the one minimizing `(arm_cost, bucketing_key)`; disposition = `"accept:split"` if its move label starts with `split`, else `"accept:merge"`; if none, `"halt:converged"`. The gate never applies to the incumbent.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_west_meta_agon.py`:

```python
import json

from west_meta_agon import (WalkResult, replay_walk, run_meta_walk)


def _ev(n, naive, incr=None, gap=0.0):
    return MetaEvidence(n=n, cost_naive=naive,
                        cost_incremental=(incr if incr is not None else naive),
                        gap=gap, coverage=1.0 - gap, m_fed=0, k2=None, k3=0.0,
                        cut_links=0, cv=0.0, mean_member=0.0)


class FakeEvaluator:
    """Evidence by bucketing key; unknown keys get a default expensive read."""
    def __init__(self, table):
        self.table = table
        self.calls = []

    def evaluate(self, b):
        key = bucketing_key(b)
        self.calls.append(key)
        return self.table.get(key, _ev(len(b), 10**9))


def _walk_manifest():
    return _manifest(["a", "b", "c", "d"], [("a", "b"), ("c", "d")])


class TestWalk:
    def test_descends_and_halts_converged(self, tmp_path):
        m = _walk_manifest()
        start = canonical([["a", "b", "c", "d"]])
        # N=1 costs 100; its split (ab|cd) costs 80; children of that cost
        # more -> converge at N=2 after one accept.
        fake = FakeEvaluator({
            "a,b,c,d": _ev(1, 100),
            "a,b;c,d": _ev(2, 80),
        })
        led = tmp_path / "w.jsonl"
        res = run_meta_walk(start, name="T", arm="naive", manifest=m,
                            evaluate=fake.evaluate, theta=0.20,
                            ledger_path=led)
        assert res.halt == "converged"
        assert res.moves == ["split:0"]
        assert bucketing_key(res.final) == "a,b;c,d"
        assert res.rounds[0].disposition == "accept:split"
        assert res.rounds[1].disposition == "halt:converged"

    def test_gap_gate_refuses_regardless_of_cost(self):
        m = _walk_manifest()
        start = canonical([["a", "b", "c", "d"]])
        # The split is far cheaper but incoherent -> refused -> halt.
        fake = FakeEvaluator({
            "a,b,c,d": _ev(1, 100),
            "a,b;c,d": _ev(2, 10, gap=0.5),
        })
        res = run_meta_walk(start, name="T", arm="naive", manifest=m,
                            evaluate=fake.evaluate, theta=0.20)
        assert res.halt == "converged"
        assert res.moves == []
        entry = res.rounds[0].slate[0]
        assert entry.refused is True

    def test_incumbent_gap_never_gated(self):
        # A standing-incoherent incumbent (the N=1 start, spec §2) can still
        # accept a coherent improving move.
        m = _walk_manifest()
        start = canonical([["a", "b", "c", "d"]])
        fake = FakeEvaluator({
            "a,b,c,d": _ev(1, 100, gap=0.58),
            "a,b;c,d": _ev(2, 90),
        })
        res = run_meta_walk(start, name="T", arm="naive", manifest=m,
                            evaluate=fake.evaluate, theta=0.20)
        assert res.moves == ["split:0"]

    def test_steepest_not_first_improvement(self):
        # Two improving splits; the CHEAPER one wins even though it is
        # tabled second.
        m = _manifest(["a", "b", "c", "d"], [])
        start = canonical([["a", "b"], ["c", "d"]])
        fake = FakeEvaluator({
            "a,b;c,d": _ev(2, 100),
            "a;b;c,d": _ev(3, 90),   # split:0
            "a,b;c;d": _ev(3, 85),   # split:1 — steepest
        })
        res = run_meta_walk(start, name="T", arm="naive", manifest=m,
                            evaluate=fake.evaluate, theta=0.20)
        assert res.moves[0] == "split:1"

    def test_arm_currency_selects_winner(self):
        # Under naive the split improves; under incremental it worsens.
        m = _walk_manifest()
        start = canonical([["a", "b", "c", "d"]])
        fake = FakeEvaluator({
            "a,b,c,d": _ev(1, 100, incr=50),
            "a,b;c,d": _ev(2, 80, incr=60),
        })
        res_n = run_meta_walk(start, name="T", arm="naive", manifest=m,
                              evaluate=fake.evaluate, theta=0.20)
        res_i = run_meta_walk(start, name="T", arm="incremental", manifest=m,
                              evaluate=fake.evaluate, theta=0.20)
        assert res_n.moves == ["split:0"]
        assert res_i.moves == []

    def test_max_rounds_reports_non_converged(self):
        # An ever-improving ladder (each split cheaper) with max_rounds=2.
        m = _manifest(["a", "b", "c", "d"], [])
        start = canonical([["a", "b", "c", "d"]])
        fake = FakeEvaluator({
            "a,b,c,d": _ev(1, 100),
            "a,b;c,d": _ev(2, 90),
            "a;b;c,d": _ev(3, 80),
            "a,b;c;d": _ev(3, 85),
            "a;b;c;d": _ev(4, 70),
        })
        res = run_meta_walk(start, name="T", arm="naive", manifest=m,
                            evaluate=fake.evaluate, theta=0.20, max_rounds=2)
        assert res.halt == "max_rounds"
        assert len(res.moves) == 2


class TestLedger:
    def test_ledger_replays_ok(self, tmp_path):
        m = _walk_manifest()
        start = canonical([["a", "b", "c", "d"]])
        fake = FakeEvaluator({
            "a,b,c,d": _ev(1, 100),
            "a,b;c,d": _ev(2, 80),
        })
        led = tmp_path / "w.jsonl"
        run_meta_walk(start, name="T", arm="naive", manifest=m,
                      evaluate=fake.evaluate, theta=0.20, ledger_path=led)
        rep = replay_walk(led)
        assert rep["ok"] is True
        assert rep["rounds"] == 2
        assert rep["mismatches"] == []

    def test_replay_flags_doctored_disposition(self, tmp_path):
        m = _walk_manifest()
        start = canonical([["a", "b", "c", "d"]])
        fake = FakeEvaluator({
            "a,b,c,d": _ev(1, 100),
            "a,b;c,d": _ev(2, 80),
        })
        led = tmp_path / "w.jsonl"
        run_meta_walk(start, name="T", arm="naive", manifest=m,
                      evaluate=fake.evaluate, theta=0.20, ledger_path=led)
        lines = led.read_text().splitlines()
        row = json.loads(lines[1])          # line 0 is the header
        row["disposition"] = "halt:converged"
        lines[1] = json.dumps(row)
        led.write_text("\n".join(lines) + "\n")
        rep = replay_walk(led)
        assert rep["ok"] is False
        assert rep["mismatches"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_west_meta_agon.py -q`
Expected: FAIL — `ImportError: cannot import name 'run_meta_walk'`

- [ ] **Step 3: Append the implementation**

Append to `src/west_meta_agon.py` (add `import json`, `from pathlib import Path`, `from typing import Callable, List as _List` as needed at the top):

```python
import json
from pathlib import Path
from typing import Callable


@dataclass
class SlateEntry:
    """One tabled move, as judged (spec §2)."""
    move: str
    key: str
    evidence: MetaEvidence
    refused: bool
    improving: bool


@dataclass
class WalkRound:
    round_no: int
    incumbent_key: str
    incumbent_evidence: MetaEvidence
    slate: List[SlateEntry]
    disposition: str
    chosen_key: Optional[str]


@dataclass
class WalkResult:
    name: str
    arm: str
    start_key: str
    rounds: List[WalkRound]
    final: Bucketing
    final_evidence: MetaEvidence
    halt: str                     # "converged" | "max_rounds"
    moves: List[str]


def _dispose(incumbent_ev: MetaEvidence, entries: List[SlateEntry],
             arm: str) -> tuple:
    """The panel rule (spec §2): gate, then steepest strict descent, ties by
    canonical key; else halt. Returns (disposition, chosen SlateEntry|None)."""
    admissible = [e for e in entries if not e.refused and e.improving]
    if not admissible:
        return "halt:converged", None
    best = min(admissible, key=lambda e: (arm_cost(e.evidence, arm), e.key))
    kind = "accept:split" if best.move.startswith("split") else "accept:merge"
    return kind, best


def _evidence_dict(ev: MetaEvidence) -> dict:
    return {"n": ev.n, "cost_naive": ev.cost_naive,
            "cost_incremental": ev.cost_incremental, "gap": ev.gap,
            "coverage": ev.coverage, "m_fed": ev.m_fed, "k2": ev.k2,
            "k3": ev.k3, "cut_links": ev.cut_links, "cv": ev.cv,
            "mean_member": ev.mean_member}


def run_meta_walk(start, *, name: str, arm: str, manifest,
                  evaluate: Callable, theta: float, merge_k: int = 3,
                  max_rounds: int = 20, ledger_path=None) -> WalkResult:
    """Full-slate steepest descent over bucketings (spec §2-§3), every round
    appended to the JSONL move ledger. A ``max_rounds`` exit is reported as
    non-converged, never as convergence (spec §2)."""
    incumbent = canonical(start)
    rounds: List[WalkRound] = []
    moves: List[str] = []
    lines: List[str] = []
    lines.append(json.dumps({"walk": name, "arm": arm, "theta": theta,
                             "merge_k": merge_k,
                             "start": bucketing_key(incumbent)}))
    halt = "max_rounds"
    inc_ev = evaluate(incumbent)
    for round_no in range(max_rounds + 1):
        entries: List[SlateEntry] = []
        for move, child in slate_moves(incumbent, manifest, k=merge_k):
            ev = evaluate(child)
            refused = ev.gap > theta
            improving = (not refused
                         and arm_cost(ev, arm) < arm_cost(inc_ev, arm))
            entries.append(SlateEntry(move=move, key=bucketing_key(child),
                                      evidence=ev, refused=refused,
                                      improving=improving))
        disposition, chosen = _dispose(inc_ev, entries, arm)
        wr = WalkRound(round_no=round_no,
                       incumbent_key=bucketing_key(incumbent),
                       incumbent_evidence=inc_ev, slate=entries,
                       disposition=disposition,
                       chosen_key=(chosen.key if chosen else None))
        rounds.append(wr)
        lines.append(json.dumps({
            "round": round_no, "incumbent": wr.incumbent_key,
            "incumbent_evidence": _evidence_dict(inc_ev),
            "slate": [{"move": e.move, "key": e.key,
                       "evidence": _evidence_dict(e.evidence),
                       "refused": e.refused, "improving": e.improving}
                      for e in entries],
            "disposition": disposition, "chosen": wr.chosen_key,
        }))
        if chosen is None:
            halt = "converged"
            break
        moves.append(chosen.move)
        incumbent = canonical(tuple(tuple(x) for x in
                                    _bucketing_from_key(chosen.key)))
        inc_ev = chosen.evidence
        if len(moves) >= max_rounds:
            break
    if ledger_path is not None:
        Path(ledger_path).write_text("\n".join(lines) + "\n")
    return WalkResult(name=name, arm=arm,
                      start_key=bucketing_key(canonical(start)),
                      rounds=rounds, final=incumbent, final_evidence=inc_ev,
                      halt=halt, moves=moves)


def _bucketing_from_key(key: str) -> Bucketing:
    return canonical(bucket.split(",") for bucket in key.split(";"))


def replay_walk(ledger_path) -> dict:
    """Recompute every panel disposition from the RECORDED evidence — no
    re-evaluation (spec §2: the record is re-checkable). Returns
    {ok, rounds, mismatches}."""
    lines = Path(ledger_path).read_text().splitlines()
    header = json.loads(lines[0])
    arm, theta = header["arm"], header["theta"]
    mismatches: List[str] = []
    n_rounds = 0
    for raw in lines[1:]:
        row = json.loads(raw)
        n_rounds += 1
        inc = MetaEvidence(**row["incumbent_evidence"])
        entries = []
        for s in row["slate"]:
            ev = MetaEvidence(**s["evidence"])
            refused = ev.gap > theta
            improving = (not refused
                         and arm_cost(ev, arm) < arm_cost(inc, arm))
            if refused != s["refused"] or improving != s["improving"]:
                mismatches.append(
                    f"round {row['round']}: flags differ on {s['key']}")
            entries.append(SlateEntry(move=s["move"], key=s["key"],
                                      evidence=ev, refused=refused,
                                      improving=improving))
        disposition, chosen = _dispose(inc, entries, arm)
        if disposition != row["disposition"] or \
                (chosen.key if chosen else None) != row["chosen"]:
            mismatches.append(
                f"round {row['round']}: disposition differs "
                f"({disposition!r} vs recorded {row['disposition']!r})")
    return {"ok": not mismatches, "rounds": n_rounds,
            "mismatches": mismatches}
```

Note for the implementer: the loop must express exactly the tested behavior —
`halt:converged` when no admissible improving move; `max_rounds` halt after
`max_rounds` *accepted* moves (the `len(moves) >= max_rounds` break, with
`halt` still `"max_rounds"`); the incumbent is never gap-gated.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_west_meta_agon.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/west_meta_agon.py tests/test_west_meta_agon.py
git commit -m "west-e3: panel + steepest-descent walk + JSONL ledger + replay (Task 4)"
```

---

### Task 5: The rider E2b′ — regime finder + broker-active quality re-test

**Files:**
- Modify: `src/west_meta_agon.py` (append)
- Test: `tests/test_west_meta_agon.py` (append)

**Interfaces:**
- Consumes: `west_experiment.run_sweepb_point` (regime cells), Task 2's `run_fed_bucketed_broker`, `west_measure.round_robin_buckets` / `link_aware_buckets`.
- Produces:
  - `@dataclass RegimeCell`: `n: int, ttl: int, gap: float`
  - `@dataclass BrokerQuality`: `ttl: int, rr_cost: int, la_cost: int, rr_cut: int, la_cut: int, rr_routes: int, la_routes: int, material: bool`
  - `find_biting_regime(root, manifest, *, rounds: int, ttls=(60, 30, 15), ns=(2, 4), theta: float, point_fn=None) -> Tuple[List[RegimeCell], Optional[int]]` — biting ttl = the LARGEST ttl in `ttls` with `gap > theta` at `n=4`; `point_fn(root, manifest, n=, rounds=, ttl=)` defaults to `run_sweepb_point` (injectable for tests).
  - `run_broker_quality(root, manifest, *, n: int, rounds: int, ttl: int, tol: float, broker_fn=None) -> BrokerQuality` — broker-active total per bucketing = `mat + peel + tax.cells_written + tax.naive_member_round + routes`; `material = la_cost <= rr_cost * (1 - tol)`; `broker_fn` defaults to `run_fed_bucketed_broker` (injectable).

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_west_meta_agon.py`:

```python
from west_meta_agon import (BrokerQuality, RegimeCell, find_biting_regime,
                            run_broker_quality)


class TestRegimeFinder:
    def _fake_point(self, gaps):
        """gaps: {(n, ttl): gap}. Returns a stand-in for run_sweepb_point."""
        class P:
            def __init__(self, gap):
                self.gap = gap
        def fn(root, manifest, *, n, rounds, ttl, bucketing="round_robin"):
            return P(gaps[(n, ttl)])
        return fn

    def test_picks_largest_biting_ttl_at_n4(self):
        gaps = {(2, 60): 0.0, (2, 30): 0.1, (2, 15): 0.3,
                (4, 60): 0.1, (4, 30): 0.25, (4, 15): 0.4}
        cells, biting = find_biting_regime(
            None, None, rounds=1, theta=0.20,
            point_fn=self._fake_point(gaps))
        assert biting == 30            # largest ttl with gap>theta at n=4
        assert len(cells) == 6
        assert RegimeCell(n=4, ttl=30, gap=0.25) in cells

    def test_none_when_nothing_bites_at_n4(self):
        gaps = {(2, 60): 0.5, (2, 30): 0.5, (2, 15): 0.5,
                (4, 60): 0.0, (4, 30): 0.1, (4, 15): 0.2}  # 0.2 NOT > 0.20
        cells, biting = find_biting_regime(
            None, None, rounds=1, theta=0.20,
            point_fn=self._fake_point(gaps))
        assert biting is None          # n=2 biting does not define the regime


class TestBrokerQuality:
    def test_material_and_totals(self):
        # Fake broker keyed on CALL ORDER: run_broker_quality must call
        # round-robin FIRST, then link-aware (pinned by this test).
        class Res:
            def __init__(self, mat, peel, routes, cov):
                class C:
                    materialization_atoms = mat
                    peel_proxy = peel
                self.cost = C()
                self.routes = routes
                self.coverage = cov
        class Tax:
            cells_written = 10
            naive_member_round = 100
            incremental = 5
        calls = {"i": 0}
        def fake_broker(root, manifest, *, buckets, rounds, ttl):
            calls["i"] += 1
            if calls["i"] == 1:        # round-robin: dear
                return Res(1000, 100, 50, 0.9), Tax()
            return Res(700, 100, 20, 0.95), Tax()   # link-aware: cheaper
        m = _manifest(["a", "b", "c", "d"], [("a", "c"), ("b", "d")])
        q = run_broker_quality(None, m, n=2, rounds=1, ttl=60, tol=0.10,
                               broker_fn=fake_broker)
        assert q.rr_cost == 1000 + 100 + 10 + 100 + 50
        assert q.la_cost == 700 + 100 + 10 + 100 + 20
        assert q.material is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_west_meta_agon.py -q`
Expected: FAIL — `ImportError: cannot import name 'find_biting_regime'`

- [ ] **Step 3: Append the implementation**

```python
from west_experiment import run_fed_bucketed_broker, run_sweepb_point
from west_measure import link_aware_buckets, round_robin_buckets


@dataclass
class RegimeCell:
    """One rider-(a) cell: the passive gap at (n, ttl) (spec §5a)."""
    n: int
    ttl: int
    gap: float


@dataclass
class BrokerQuality:
    """Rider (b): round-robin vs link-aware at n, broker-active (spec §5b)."""
    ttl: int
    rr_cost: int
    la_cost: int
    rr_cut: int
    la_cut: int
    rr_routes: int
    la_routes: int
    material: bool


def find_biting_regime(root, manifest, *, rounds: int, ttls=(60, 30, 15),
                       ns=(2, 4), theta: float, point_fn=None):
    """Rider (a) — sweep ttl at fixed round-robin bucketings; the biting
    regime is the LARGEST ttl with gap > theta at n=4 (n=2 recorded for the
    mechanism read, never regime-defining — spec §5a). Returns
    (cells, biting_ttl|None)."""
    fn = point_fn if point_fn is not None else run_sweepb_point
    cells: List[RegimeCell] = []
    biting = None
    for n in ns:
        for ttl in ttls:
            pt = fn(root, manifest, n=n, rounds=rounds, ttl=ttl,
                    bucketing="round_robin")
            cells.append(RegimeCell(n=n, ttl=ttl, gap=pt.gap))
    for ttl in sorted(ttls, reverse=True):
        if any(c.gap > theta for c in cells if c.n == 4 and c.ttl == ttl):
            biting = ttl
            break
    return cells, biting


def _broker_total(res, tax) -> int:
    """Broker-active Arm-N total (spec §5b): passive naive total + routes."""
    return (res.cost.materialization_atoms + res.cost.peel_proxy
            + tax.cells_written + tax.naive_member_round + res.routes)


def run_broker_quality(root, manifest, *, n: int, rounds: int, ttl: int,
                       tol: float, broker_fn=None) -> BrokerQuality:
    """Rider (b) — PB4's deferred test under force: round-robin FIRST, then
    link-aware, both broker-active, at the biting regime (spec §5b)."""
    fn = broker_fn if broker_fn is not None else run_fed_bucketed_broker
    from west_measure import cut_link_count as _clc
    rr_buckets = round_robin_buckets(manifest.folders, n)
    la_buckets = link_aware_buckets(manifest, n)
    rr, rr_tax = fn(root, manifest, buckets=rr_buckets, rounds=rounds, ttl=ttl)
    la, la_tax = fn(root, manifest, buckets=la_buckets, rounds=rounds, ttl=ttl)
    rr_cost = _broker_total(rr, rr_tax)
    la_cost = _broker_total(la, la_tax)
    return BrokerQuality(
        ttl=ttl, rr_cost=rr_cost, la_cost=la_cost,
        rr_cut=_clc(rr_buckets, manifest), la_cut=_clc(la_buckets, manifest),
        rr_routes=rr.routes, la_routes=la.routes,
        material=(la_cost <= rr_cost * (1 - tol)),
    )
```

(Fold the `cut_link_count` import into the top-of-file imports rather than
the local import shown; shown locally only for patch clarity.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_west_meta_agon.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/west_meta_agon.py tests/test_west_meta_agon.py
git commit -m "west-e3: rider E2b' — regime finder + broker-active quality re-test (Task 5)"
```

---

### Task 6: `assemble_e3_report` — the PE1–PE5 verdict layer (killer fixtures per conjunct)

**Files:**
- Modify: `src/west_meta_agon.py` (append)
- Test: `tests/test_west_meta_agon.py` (append)

**Interfaces:**
- Consumes: Task 4's `WalkResult`, Task 5's `RegimeCell`/`BrokerQuality`.
- Produces:
  - `TROUGH_E2B = 137129` (module constant — E2b's measured Arm-N trough, the pre-registered comparator)
  - `@dataclass E3Report`: `priors: Dict[str, str]`, `final_costs: Dict[str, int]`, `biting_ttl: Optional[int]`
  - `assemble_e3_report(w1, w2, w3, w4, cells, biting_ttl, quality, *, tol: float, trough: int = TROUGH_E2B, sweep_max_n: int = 12) -> E3Report`
  - Verdict rules (spec §6, exact):
    - PE1 `held` iff BOTH w1 and w2 have `halt == "converged"` AND `1 < final_evidence.n < sweep_max_n` AND `final_evidence.cost_naive <= trough * (1 + tol)`; else `refuted`.
    - PE2 `held` iff max/min over the three Arm-N final `cost_naive` ≤ `1 + tol`; else `refuted`.
    - PE3 `held` iff w4 `halt == "converged"` AND `final_evidence.n == sweep_max_n`; else `refuted`.
    - PE4 `held` iff `biting_ttl is not None`; else `refuted`.
    - PE5: `undetermined` if PE4 refuted; else `held` iff `quality.material`, else `refuted`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_west_meta_agon.py`. Build minimal `WalkResult`s by
hand; each PE conjunct gets its own killer fixture (the E2/E2b
mutation-review lesson):

```python
from west_meta_agon import TROUGH_E2B, assemble_e3_report


def _walk(halt, n, cost_naive, name="W", arm="naive"):
    ev = _ev(n, cost_naive)
    return WalkResult(name=name, arm=arm, start_key="s", rounds=[],
                      final=tuple(), final_evidence=ev, halt=halt, moves=[])


def _quality(material):
    return BrokerQuality(ttl=30, rr_cost=100, la_cost=(80 if material else 99),
                         rr_cut=10, la_cut=5, rr_routes=9, la_routes=4,
                         material=material)


def _report(w1=None, w2=None, w3=None, w4=None, biting=30, material=True):
    w1 = w1 or _walk("converged", 3, 137000)
    w2 = w2 or _walk("converged", 3, 137000)
    w3 = w3 or _walk("converged", 3, 137000)
    w4 = w4 or _walk("converged", 12, 37917, arm="incremental")
    q = _quality(material) if biting is not None else None
    return assemble_e3_report(w1, w2, w3, w4, cells=[], biting_ttl=biting,
                              quality=q, tol=0.10)


class TestVerdictLayer:
    def test_all_held_baseline(self):
        r = _report()
        assert r.priors == {"PE1": "held", "PE2": "held", "PE3": "held",
                            "PE4": "held", "PE5": "held"}

    # --- PE1: each conjunct has a killer ---
    def test_pe1_endpoint_halt_refutes(self):
        assert _report(w1=_walk("converged", 1, 100000)).priors["PE1"] == "refuted"

    def test_pe1_max_rounds_refutes(self):
        assert _report(w2=_walk("max_rounds", 3, 137000)).priors["PE1"] == "refuted"

    def test_pe1_above_ceiling_refutes(self):
        over = int(TROUGH_E2B * 1.10) + 1
        assert _report(w1=_walk("converged", 3, over)).priors["PE1"] == "refuted"

    def test_pe1_below_trough_holds(self):
        assert _report(w1=_walk("converged", 4, 120000),
                       w3=_walk("converged", 4, 120000)).priors["PE1"] == "held"

    def test_pe1_needs_both_walks(self):
        assert _report(w2=_walk("converged", 12, 37917)).priors["PE1"] == "refuted"

    # --- PE2 ---
    def test_pe2_spread_refutes(self):
        r = _report(w3=_walk("converged", 5, 160000))
        assert r.priors["PE2"] == "refuted"

    def test_pe2_uses_naive_costs_of_all_three(self):
        r = _report(w1=_walk("converged", 3, 137000),
                    w2=_walk("converged", 3, 140000),
                    w3=_walk("converged", 3, 143000))
        assert r.priors["PE2"] == "held"      # 143000/137000 = 1.0438 <= 1.10

    # --- PE3 ---
    def test_pe3_interior_halt_refutes(self):
        assert _report(w4=_walk("converged", 6, 60000,
                                arm="incremental")).priors["PE3"] == "refuted"

    def test_pe3_max_rounds_refutes(self):
        assert _report(w4=_walk("max_rounds", 12, 37917,
                                arm="incremental")).priors["PE3"] == "refuted"

    # --- PE4 / PE5 ---
    def test_pe4_refuted_makes_pe5_undetermined(self):
        r = _report(biting=None)
        assert r.priors["PE4"] == "refuted"
        assert r.priors["PE5"] == "undetermined"

    def test_pe5_not_material_refutes(self):
        assert _report(material=False).priors["PE5"] == "refuted"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_west_meta_agon.py -q`
Expected: FAIL — `ImportError: cannot import name 'assemble_e3_report'`

- [ ] **Step 3: Append the implementation**

```python
TROUGH_E2B = 137129     # E2b's measured Arm-N trough (runs/WEST_E2B_LOG.md)


@dataclass
class E3Report:
    """The assembled E3 result and the pre-registered verdicts PE1-PE5
    (spec §6). PE5 is conditional on PE4."""
    priors: Dict[str, str]
    final_costs: Dict[str, int]
    biting_ttl: Optional[int]


def assemble_e3_report(w1: WalkResult, w2: WalkResult, w3: WalkResult,
                       w4: WalkResult, cells, biting_ttl,
                       quality: Optional[BrokerQuality], *, tol: float,
                       trough: int = TROUGH_E2B,
                       sweep_max_n: int = 12) -> E3Report:
    """Decide PE1-PE5 from the walks and the rider (spec §6)."""
    def _interior_ok(w: WalkResult) -> bool:
        return (w.halt == "converged"
                and 1 < w.final_evidence.n < sweep_max_n
                and w.final_evidence.cost_naive <= trough * (1 + tol))

    pe1 = "held" if (_interior_ok(w1) and _interior_ok(w2)) else "refuted"

    finals = [w.final_evidence.cost_naive for w in (w1, w2, w3)]
    pe2 = "held" if max(finals) <= min(finals) * (1 + tol) else "refuted"

    pe3 = "held" if (w4.halt == "converged"
                     and w4.final_evidence.n == sweep_max_n) else "refuted"

    pe4 = "held" if biting_ttl is not None else "refuted"
    if pe4 == "refuted":
        pe5 = "undetermined"
    else:
        pe5 = "held" if (quality is not None and quality.material) else "refuted"

    return E3Report(
        priors={"PE1": pe1, "PE2": pe2, "PE3": pe3, "PE4": pe4, "PE5": pe5},
        final_costs={"W1": w1.final_evidence.cost_naive,
                     "W2": w2.final_evidence.cost_naive,
                     "W3": w3.final_evidence.cost_naive,
                     "W4": w4.final_evidence.cost_incremental},
        biting_ttl=biting_ttl,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_west_meta_agon.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/west_meta_agon.py tests/test_west_meta_agon.py
git commit -m "west-e3: assemble_e3_report — PE1-PE5 verdict layer with per-conjunct killers (Task 6)"
```

---

### Task 7: The numbers-only driver + contract test + gitignore

**Files:**
- Create: `tools/run_west_e3.py`
- Modify: `.gitignore` (append two lines after the `!runs/WEST_E2B_LOG.md` line)
- Test: `tests/test_run_west_e3_driver.py`

**Interfaces:**
- Consumes: everything above. Walk starts (spec §3): W1/W4 `canonical([sorted(manifest.folders)])`; W2 `canonical([[f] for f in manifest.folders])`; W3 the pre-registered unbalanced mid-start — `fs = sorted(manifest.folders)` then buckets `fs[0:6], fs[6:9], fs[9:11], fs[11:12]` (sizes 6/3/2/1). In `--smoke` (4 folders) the mid-start is `fs[0:2], fs[2:3], fs[3:4]` (sizes 2/1/1).
- Produces: stdout contract (each line `flush=True`):
  - header `=== West-in-kytē E3 — endogenous partition (numbers only) ===` + a config line
  - per walk-round: `walk=W1 round=0 n=1 sizes=12 slate=1 refused=0 disposition=accept:split cost=162907 gap=0.5795 wall_s=…`
  - per walk-end: `walk=W1 halt=converged final_n=3 final_sizes=4/4/4 final_cost=… moves=… memo_hits=… memo_misses=…`
  - rider: `rider cell n=2 ttl=60 gap=…` ×6, `rider biting_ttl=…`, `rider quality ttl=… rr_cost=… la_cost=… rr_cut=… la_cut=… rr_routes=… la_routes=… material=…` (or `rider quality skipped (PE4 refuted)`)
  - `priors: {…}`, `determinism_canary: PASS|FAIL`, a `notes:` block (see Step 3)

- [ ] **Step 1: Write the failing contract test**

Create `tests/test_run_west_e3_driver.py`:

```python
"""Driver contract: tools/run_west_e3.py --smoke runs end-to-end, prints the
numbers-only lines, and leaves ledgers that replay clean."""

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def test_smoke_driver_contract(tmp_path):
    proc = subprocess.run(
        [sys.executable, str(REPO / "tools" / "run_west_e3.py"),
         "--smoke", "--dest", str(tmp_path)],
        capture_output=True, text=True, timeout=600)
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout
    assert "West-in-kytē E3" in out
    for w in ("W1", "W2", "W3", "W4"):
        assert f"walk={w} halt=" in out
    assert "rider biting_ttl=" in out
    assert "priors: {" in out
    assert "determinism_canary: PASS" in out
    assert "notes:" in out
    # Ledgers exist and replay clean.
    sys.path.insert(0, str(REPO / "src"))
    from west_meta_agon import replay_walk
    for w in ("W1", "W2", "W3", "W4"):
        led = tmp_path / f"{w}.jsonl"
        assert led.exists()
        assert replay_walk(led)["ok"] is True
    # Numbers-only: no folder name ever printed.
    assert "Folder-" not in out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_run_west_e3_driver.py -q`
Expected: FAIL — driver does not exist.

- [ ] **Step 3: Write the driver**

Create `tools/run_west_e3.py`:

```python
"""West-in-kytē E3 driver — the meta-Agon over folder-bucketings: walks
W1-W4, the rider E2b', the PE1-PE5 verdicts, the determinism canary.

Numbers-only stdout (custody convention): bucketings print as sizes, never
folder names. Spec: docs/superpowers/specs/2026-07-23-west-in-kyte-e3-design.md"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from vault_generator import generate_vault
from west_meta_agon import (MemoEvaluator, assemble_e3_report, bucket_sizes,
                            canonical, find_biting_regime, replay_walk,
                            run_broker_quality, run_meta_walk)

# Pre-registered E3 knobs (spec §2-§6 — fixed).
SEED = 20260721
F0 = 12
N_NOTES = 40
P_BASE = 0.15
JOURNAL = 40
TTL = 120
R_FIXED = 325
THETA = 0.20
TOL = 0.10
MERGE_K = 3
MAX_ROUNDS = 20
RIDER_TTLS = (60, 30, 15)
RIDER_NS = (2, 4)
QUALITY_N = 4

# Smoke — driver contract test only, never a real run.
SMOKE_F0 = 4
SMOKE_NOTES = 3
SMOKE_JOURNAL = 3
SMOKE_R = 12


def _starts(manifest, smoke: bool):
    fs = sorted(manifest.folders)
    w1 = canonical([fs])
    w2 = canonical([[f] for f in fs])
    if smoke:
        w3 = canonical([fs[0:2], fs[2:3], fs[3:4]])          # sizes 2/1/1
    else:
        w3 = canonical([fs[0:6], fs[6:9], fs[9:11], fs[11:12]])  # 6/3/2/1
    return w1, w2, w3


def _run_walk(name, start, arm, manifest, memo, dest, max_rounds):
    t0 = time.time()
    rounds_seen = {"n": 0}
    # Wrap evaluate to print nothing per eval; per-round lines print below.
    res = run_meta_walk(start, name=name, arm=arm, manifest=manifest,
                        evaluate=memo.evaluate, theta=THETA, merge_k=MERGE_K,
                        max_rounds=max_rounds, ledger_path=dest / f"{name}.jsonl")
    for wr in res.rounds:
        print(f"walk={name} round={wr.round_no} n={wr.incumbent_evidence.n} "
              f"sizes={bucket_sizes(canonical(b.split(',') for b in wr.incumbent_key.split(';')))} "
              f"slate={len(wr.slate)} "
              f"refused={sum(1 for e in wr.slate if e.refused)} "
              f"disposition={wr.disposition} "
              f"cost={wr.incumbent_evidence.cost_naive if arm == 'naive' else wr.incumbent_evidence.cost_incremental} "
              f"gap={round(wr.incumbent_evidence.gap, 4)}", flush=True)
    print(f"walk={name} halt={res.halt} final_n={res.final_evidence.n} "
          f"final_sizes={bucket_sizes(res.final)} "
          f"final_cost={res.final_evidence.cost_naive if arm == 'naive' else res.final_evidence.cost_incremental} "
          f"moves={','.join(res.moves) if res.moves else '-'} "
          f"memo_hits={memo.hits} memo_misses={memo.misses} "
          f"wall_s={round(time.time() - t0, 1)}", flush=True)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", default=None)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--no-canary", action="store_true")
    args = ap.parse_args()

    import tempfile
    dest = Path(args.dest) if args.dest else Path(tempfile.mkdtemp(prefix="west_e3_"))
    dest.mkdir(parents=True, exist_ok=True)

    if args.smoke:
        f0, notes, journal, rfix = SMOKE_F0, SMOKE_NOTES, SMOKE_JOURNAL, SMOKE_R
        rider_ttls, max_rounds = (60,), 6
        mode = "smoke"
    else:
        f0, notes, journal, rfix = F0, N_NOTES, JOURNAL, R_FIXED
        rider_ttls, max_rounds = RIDER_TTLS, MAX_ROUNDS
        mode = "full"

    print("=== West-in-kytē E3 — endogenous partition (numbers only) ===", flush=True)
    print(f"mode={mode} seed={SEED} F0={f0} n={notes} p_base={P_BASE} "
          f"J={journal} ttl={TTL} R={rfix} theta={THETA} tol={TOL} "
          f"merge_k={MERGE_K} max_rounds={max_rounds}", flush=True)

    vault = dest / "vault"
    manifest = generate_vault(vault, seed=SEED, folders=f0,
                              notes_per_folder=notes,
                              cross_folder_link_prob=P_BASE,
                              journal_len=journal)
    w1_start, w2_start, w3_start = _starts(manifest, args.smoke)

    memo = MemoEvaluator(vault, manifest, rounds=rfix, ttl=TTL)
    w1 = _run_walk("W1", w1_start, "naive", manifest, memo, dest, max_rounds)
    w2 = _run_walk("W2", w2_start, "naive", manifest, memo, dest, max_rounds)
    w3 = _run_walk("W3", w3_start, "naive", manifest, memo, dest, max_rounds)
    w4 = _run_walk("W4", w1_start, "incremental", manifest, memo, dest, max_rounds)

    # Rider E2b' (spec §5).
    cells, biting = find_biting_regime(vault, manifest, rounds=rfix,
                                       ttls=rider_ttls, ns=RIDER_NS,
                                       theta=THETA)
    for c in cells:
        print(f"rider cell n={c.n} ttl={c.ttl} gap={round(c.gap, 4)}", flush=True)
    print(f"rider biting_ttl={biting}", flush=True)
    quality = None
    if biting is not None:
        quality = run_broker_quality(vault, manifest, n=QUALITY_N,
                                     rounds=rfix, ttl=biting, tol=TOL)
        print(f"rider quality ttl={quality.ttl} rr_cost={quality.rr_cost} "
              f"la_cost={quality.la_cost} rr_cut={quality.rr_cut} "
              f"la_cut={quality.la_cut} rr_routes={quality.rr_routes} "
              f"la_routes={quality.la_routes} material={quality.material}",
              flush=True)
    else:
        print("rider quality skipped (PE4 refuted)", flush=True)

    sweep_max = f0
    rep = assemble_e3_report(w1, w2, w3, w4, cells, biting, quality,
                             tol=TOL, sweep_max_n=sweep_max)
    print(f"priors: {rep.priors}", flush=True)

    canary = "skipped"
    if not args.no_canary:
        fresh = MemoEvaluator(vault, manifest, rounds=rfix, ttl=TTL)
        again = run_meta_walk(w3_start, name="W3c", arm="naive",
                              manifest=manifest, evaluate=fresh.evaluate,
                              theta=THETA, merge_k=MERGE_K,
                              max_rounds=max_rounds,
                              ledger_path=dest / "W3c.jsonl")
        same = (again.moves == w3.moves
                and again.final == w3.final
                and again.final_evidence.cost_naive == w3.final_evidence.cost_naive)
        canary = "PASS" if same else "FAIL"
    print(f"determinism_canary: {canary}", flush=True)

    for name in ("W1", "W2", "W3", "W4"):
        rp = replay_walk(dest / f"{name}.jsonl")
        print(f"replay {name}: ok={rp['ok']} rounds={rp['rounds']}", flush=True)

    print("notes: E3 tests the convergence of THIS walk discipline "
          "(full-slate steepest descent, top-3 link-guided merge shortlist "
          "— proposer attention, disclosed, never adjudication) on the E2b "
          "corpus. PE1 = W1+W2 converge interior within 1.10x the E2b "
          "trough (137,129); PE2 = the three Arm-N walks agree within tol; "
          "PE3 (control) = the Arm-I walk runs to the finest partition — "
          "the interior optimum is the naive coordinator's, not the "
          "walk's; PE4 = decay (ttl) reaches gap>theta at N=4 — the "
          "coherence force via attention-budget saturation, since link "
          "density cannot reach it (E2b PB3); PE5 conditional on PE4 = "
          "link-aware < round-robin under broker-active costing. The "
          "gap-gate refuses candidates, never the incumbent (the N=1 "
          "start is standing-incoherent, gap 0.58, and escapes via its "
          "first accepted split). Broker tax is an end-of-run snapshot "
          "(A3-style lower bound). Arm-N interleaving assumption carries "
          "(verdict-bearing for PE1/PE2). Synthetic corpus, one seed: the "
          "basin structure is the generator's. A meta-Agon is not a "
          "community (THE_COMMENS): this models negotiation inside one "
          "instance. |M|/K2/K3 recorded, never verdict-bearing. K1 = N/A "
          "(raise-only).", flush=True)


if __name__ == "__main__":
    main()
```

Implementer note: the `sizes=` expression in the per-round print reconstructs
a bucketing from the incumbent key — extract that into a tiny helper
(`sizes_from_key(key)`) in the driver for readability. Keep every printed
value numeric or a fixed token; never a folder name.

- [ ] **Step 4: Append the gitignore entries**

In `.gitignore`, directly after the `!runs/WEST_E2B_LOG.md` line, append:

```
# E3 (same pattern: outputs ignored, the tracked run log spared).
runs/west_e3*
!runs/WEST_E3_LOG.md
```

- [ ] **Step 5: Run the contract test**

Run: `uv run pytest tests/test_run_west_e3_driver.py -q`
Expected: PASS (allow up to ~3 min; smoke corpus is tiny)

Also verify ignore + sparing:
`git check-ignore -v runs/west_e3_run1/ ; git check-ignore -v runs/WEST_E3_LOG.md`
Expected: first line matches `runs/west_e3*`; second reports the `!` negation (exit status may be 1 for the negated path — what matters is the `!runs/WEST_E3_LOG.md` rule being the match).

- [ ] **Step 6: Commit**

```bash
git add tools/run_west_e3.py tests/test_run_west_e3_driver.py .gitignore
git commit -m "west-e3: numbers-only driver + smoke contract + gitignore (Task 7)"
```

---

### Task 8: Full-suite gate + byte-freeze audit

**Files:** none created; verification only.

- [ ] **Step 1: Byte-freeze audit of the E1/E2/E2b surface**

Run: `git diff main -- src/west_experiment.py | grep -E "^-" | grep -v "^---"`
Expected: NO deletions (the only change to `west_experiment.py` across the branch is the appended `run_fed_bucketed_broker`).

Run: `git diff main -- src/west_measure.py src/west_coordinator.py src/vault_generator.py tools/run_west_e2b.py tools/run_west_e2.py`
Expected: empty (untouched).

- [ ] **Step 2: Full test suite**

Run: `uv run pytest tests/ -q`
Expected: everything passes (4048+ passed at branch base; new tests add to that; 0 failed). Paste the tail of the output into the task report.

- [ ] **Step 3: Quality gate**

Run: `uv run python tools/quality_gate_system.py`
Expected: passes (also auto-runs on commit).

- [ ] **Step 4: Commit anything outstanding; report ready-to-merge**

```bash
git status --short   # should be clean
```

---

## Execution notes (for the orchestrator)

- Tasks 1→7 are sequential (each appends to the same module/test file).
  Task 2 is independent of Task 1 and may run in parallel with it if using
  subagents (different files) — but Tasks 3+ need both.
- The RUN itself (the ~3–5h full driver invocation, `runs/WEST_E3_LOG.md`,
  CURRENT_PLAN/memory updates) is NOT part of this plan — it follows after
  merge, as with E2b.
- Per-task review should specifically re-derive: the panel rule (Task 4) and
  the verdict layer (Task 6) — verdict layers are where mutations survived in
  both E2 and E2b.
```
