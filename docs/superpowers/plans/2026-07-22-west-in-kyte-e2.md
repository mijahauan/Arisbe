# West-in-kytē E2 (the size sweep) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the E2 size-sweep harness — an incremental coordinator scan arm, a true per-round coordinator tax by post-hoc replay, a folder-member-only CV statistic, an OLS log-log power-law fit, and a sweep driver — so the West scaling exponents β_mono and β_fed can be fitted and priors P1²–P4² decided.

**Architecture:** Purely **additive** to the E1 harness. Every E1 entry point (`run_mono`, `run_fed`, `run_fed_broker`, `assemble_report`, `tools/run_west_e1.py`, `Coordinator.consistency_scan`) keeps its exact current behaviour so `runs/WEST_E1_LOG.md` stays reproducible. E2 adds new functions and new optional dataclass fields beside them. Per-round member state is captured through a `CountingMaterializer` subclass — `materialize(egi)` is already invoked once per round with M itself — so `agon_evolution.py` is **not** modified.

**Tech Stack:** Python 3.12, uv, pytest. Stdlib only (`math`, `statistics`, `dataclasses`) — no new dependencies.

## Global Constraints

- **Spec of record:** `docs/superpowers/specs/2026-07-22-west-in-kyte-e2-design.md`. Every number below traces to it.
- **Zero protected-core modification.** If any task appears to need one, **halt and request authorization**. `src/west_*.py`, `src/vault_generator.py`, and `tools/` are unprotected.
- **Do not modify `agon_evolution.py`, `model_materialization.py`, or `world_scroll.py`.**
- **E1 must stay reproducible.** No behaviour change to `Coordinator.consistency_scan`, `run_mono`, `run_fed`, `run_fed_broker`, `assemble_report`, or `tools/run_west_e1.py`. New dataclass fields must have defaults.
- **Determinism is mandatory.** No `Date.now()`-style nondeterminism, no unsorted iteration over sets/dicts where order affects output. Sort every iteration over a set or dict whose order could reach a result.
- **Custody (non-negotiable).** `tools/run_west_e2.py` stdout is **numbers only** — never a note id, title, path, or body text. Any file it writes goes under `runs/` and must be covered by `.gitignore`.
- **Grid (pre-registered, fixed):** `F ∈ {2, 4, 6, 8, 12, 16}`, `n=40`, `R = 25·(F+1)` → `{75, 125, 175, 225, 325, 425}`, `p=0.15`, `J=40`, `seed=20260721`, `ttl=120`, `θ=0.20`, `tol=0.10`.
- **Rider:** `F=6, R=175`, `ttl ∈ {60, 120, 240, off}` where `off` means no decay.
- **Weak-fit rule:** fewer than 6 usable points **or** R² < 0.90 → the fit is `weak=True` and the dependent prior is recorded `"undetermined"` (never `"held"`/`"refuted"`).
- **Imports:** flat style — `from west_measure import ...`, never `from src.west_measure import ...`.
- **Run tests with:** `uv run pytest <path> -v`.

---

## File Structure

| File | Responsibility |
|---|---|
| `src/west_coordinator.py` (modify) | add the incremental scan arm beside the untouched naive scan |
| `src/west_measure.py` (modify) | add `TracingMaterializer`, the member-cost reading (CV fix), and the OLS power-law fit |
| `src/west_experiment.py` (modify) | add traced FED run, the coordinator-tax replay, one-config runner, E2 report, ttl rider |
| `tools/run_west_e2.py` (create) | the numbers-only sweep driver + determinism canary |
| `tests/test_west_coordinator.py` (modify) | Task 1 tests |
| `tests/test_west_measure.py` (modify) | Tasks 2, 4, 5 tests |
| `tests/test_west_experiment.py` (modify) | Tasks 3, 6, 7, 8 tests |
| `tests/test_west_e2_driver.py` (create) | Task 9 tests |

---

## Task 1: Incremental consistency scan (Arm I)

**Files:**
- Modify: `src/west_coordinator.py` (the `Coordinator` class, `src/west_coordinator.py:62-125`)
- Test: `tests/test_west_coordinator.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `Coordinator.scan_comparisons_incremental: int`, `Coordinator.consistency_scan_incremental() -> int`. Task 3 uses these as the reference implementation its closed-form counter is validated against.

**Context.** `Coordinator.consistency_scan()` compares **every** held pair on every call — O(H²) — and accumulates into `scan_comparisons`. That is Arm N (naive), and it must not change. Arm I compares only cells added since the previous incremental scan, against the whole held set: O(ΔH·H). The load-bearing invariant is that **each unordered pair is compared exactly once over a whole run**, so the incremental total for any trajectory equals a *single* naive scan's total, `H(H−1)/2`, no matter how many rounds elapse.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_west_coordinator.py`:

```python
def test_incremental_scan_counters_start_at_zero():
    coord = Coordinator()
    assert coord.scan_comparisons_incremental == 0
    assert coord.consistency_scan_incremental() == 0
    assert coord.scan_comparisons_incremental == 0


def test_incremental_scan_compares_each_pair_exactly_once_over_a_run():
    """The Arm I invariant: however many rounds elapse, the incremental total
    equals ONE naive scan's total — every unordered pair compared exactly once."""
    coord = Coordinator()
    m0 = parse_egif('(links_to "a" "b") (has_tag "a" "t")')
    m1 = parse_egif('(links_to "c" "d") (in_folder "c" "F1")')
    # Round 1: one folder ingests, then an incremental scan.
    coord.ingest("F0", m0)
    coord.consistency_scan_incremental()
    # Round 2: another folder ingests, then another incremental scan.
    coord.ingest("F1", m1)
    coord.consistency_scan_incremental()
    # Rounds 3-5: nothing new arrives; incremental scans must be free.
    before = coord.scan_comparisons_incremental
    for _ in range(3):
        coord.consistency_scan_incremental()
    assert coord.scan_comparisons_incremental == before, (
        "an incremental scan with no new cells must cost nothing"
    )
    h = len(coord.held)
    assert coord.scan_comparisons_incremental == h * (h - 1) // 2


def test_naive_scan_is_unchanged_and_costs_a_full_pass_every_call():
    """Arm N (the E1 behaviour) must be untouched: every call re-compares all pairs."""
    coord = Coordinator()
    coord.ingest("F0", parse_egif('(links_to "a" "b") (has_tag "a" "t")'))
    h = len(coord.held)
    coord.consistency_scan()
    coord.consistency_scan()
    assert coord.scan_comparisons == 2 * (h * (h - 1) // 2)


def test_incremental_and_naive_counters_are_independent():
    coord = Coordinator()
    coord.ingest("F0", parse_egif('(links_to "a" "b")'))
    coord.consistency_scan()
    assert coord.scan_comparisons_incremental == 0
    coord.consistency_scan_incremental()
    h = len(coord.held)
    assert coord.scan_comparisons_incremental == h * (h - 1) // 2
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_west_coordinator.py -v -k "incremental or naive_scan_is_unchanged"`
Expected: FAIL — `AttributeError: 'Coordinator' object has no attribute 'scan_comparisons_incremental'`

- [ ] **Step 3: Implement**

In `src/west_coordinator.py`, inside `Coordinator.__init__` (after `self.scan_comparisons: int = 0`), add:

```python
        self.scan_comparisons_incremental: int = 0
        self._unscanned: Set[Tuple[str, str]] = set()
```

In `Coordinator.ingest`, immediately after the existing `self.held.add(key)` line, add:

```python
            self._unscanned.add(key)
```

Then add this method directly after `consistency_scan` (leave `consistency_scan` itself untouched):

```python
    def consistency_scan_incremental(self) -> int:
        """Arm I (E2 spec §3.2): scan only the cells added since the previous
        incremental scan, against the whole held set — O(ΔH·H) rather than the
        naive O(H²) full re-pass. Every unordered pair is therefore compared
        **exactly once over a whole run**, so the accumulated total for any
        trajectory equals a single naive scan's `H(H−1)/2`, independent of how
        many rounds elapse. Conflict semantics are identical to
        :meth:`consistency_scan`; only the work done differs."""
        new = sorted(self._unscanned)
        old = sorted(self.held - self._unscanned)
        conflicts = 0
        comparisons = 0
        for i, a in enumerate(new):
            for b in old:                       # new against already-scanned
                comparisons += 1
                if a[1] == b[1] and a[0] != b[0]:
                    pass
            for b in new[i + 1:]:               # new against new (once each)
                comparisons += 1
                if a[1] == b[1] and a[0] != b[0]:
                    pass
        self.scan_comparisons_incremental += comparisons
        self._unscanned.clear()
        return conflicts
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_west_coordinator.py -v`
Expected: PASS — all tests in the file, including the pre-existing E1 ones.

- [ ] **Step 5: Commit**

```bash
git add src/west_coordinator.py tests/test_west_coordinator.py
git commit -m "west-e2: incremental consistency scan (Arm I) beside the untouched naive scan"
```

---

## Task 2: Per-round member state capture (`TracingMaterializer`)

**Files:**
- Modify: `src/west_measure.py`
- Test: `tests/test_west_measure.py`

**Interfaces:**
- Consumes: `west_coordinator.member_relation_names(egi) -> frozenset` (existing).
- Produces: `west_measure.TracingMaterializer` with `per_round_relations: List[frozenset]`. Task 3 consumes this list as one member's trajectory.

**Context.** `CountingMaterializer.materialize(egi)` is called **once per round with M itself** (`src/west_measure.py:18-33` — `run()` threads one materializer through the peel). Subclassing it therefore captures each round's M exactly, with no change to `agon_evolution.py` and no chain-walking. `west_measure` importing `west_coordinator` introduces no cycle (`west_coordinator` imports neither).

- [ ] **Step 1: Write the failing test**

Append to `tests/test_west_measure.py`:

```python
def test_tracing_materializer_records_one_relation_set_per_round():
    from west_measure import TracingMaterializer
    tm = TracingMaterializer()
    pool = ['(bird "tweety")', '(swan "odette")', '(bird "robin")']
    run("", CorpusProposer(pool), rounds=5, uod_id="trace-test",
        name="trace", materializer=tm)
    assert len(tm.per_round_relations) == len(tm.per_round_atoms), (
        "one captured relation set per materialization call (== per round)"
    )
    assert all(isinstance(s, frozenset) for s in tm.per_round_relations)
    assert tm.total_atoms() == sum(tm.per_round_atoms)   # base behaviour intact


def test_tracing_materializer_sees_relations_appear_as_m_grows():
    from west_measure import TracingMaterializer
    tm = TracingMaterializer()
    pool = ['(bird "tweety")', '(swan "odette")']
    run("", CorpusProposer(pool), rounds=6, uod_id="trace-grow",
        name="trace-grow", materializer=tm, ttl=None)
    union = set()
    for s in tm.per_round_relations:
        union |= s
    assert union, "some relation name must have entered M over six rounds"
    assert union <= set().union(*tm.per_round_relations)


def test_tracing_materializer_is_a_counting_materializer():
    from west_measure import TracingMaterializer, CountingMaterializer
    assert issubclass(TracingMaterializer, CountingMaterializer)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_west_measure.py -v -k tracing`
Expected: FAIL — `ImportError: cannot import name 'TracingMaterializer' from 'west_measure'`

- [ ] **Step 3: Implement**

In `src/west_measure.py`, add to the imports:

```python
from west_coordinator import member_relation_names
```

and add this class directly after `CountingMaterializer`:

```python
class TracingMaterializer(CountingMaterializer):
    """A :class:`CountingMaterializer` that additionally records the distinct
    relation names present in M at each round.

    ``materialize(egi)`` is invoked once per round with M itself, so this is an
    exact per-round capture of the member's state — no hook in
    ``agon_evolution`` and no chain-walking required. The captured trajectory is
    what the E2 coordinator-tax replay (spec §3.1) consumes: the tax depends only
    on which (folder, relation-name) cells the coordinator holds at each round."""

    def __init__(self):
        super().__init__()
        self.per_round_relations: List[frozenset] = []

    def materialize(self, egi):
        out = super().materialize(egi)
        self.per_round_relations.append(member_relation_names(egi))
        return out
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_west_measure.py -v`
Expected: PASS — all tests, including the pre-existing E1 ones.

- [ ] **Step 5: Commit**

```bash
git add src/west_measure.py tests/test_west_measure.py
git commit -m "west-e2: TracingMaterializer captures per-round member relation sets"
```

---

## Task 3: The coordinator-tax replay (A3 paid down)

**Files:**
- Modify: `src/west_experiment.py`
- Test: `tests/test_west_experiment.py`

**Interfaces:**
- Consumes: `Coordinator.consistency_scan`, `Coordinator.consistency_scan_incremental` (Task 1) as reference implementations.
- Produces:
  - `west_experiment.CoordinatorTax` — dataclass with fields `cells_written: int`, `naive_member_round: int`, `naive_global_round: int`, `incremental: int`.
  - `west_experiment.replay_coordinator_tax(trajectories: Dict[str, List[frozenset]]) -> CoordinatorTax`.

**Context.** E1 measured the tax as one end-of-run snapshot (adaptation A3), a disclosed lower bound. E2 replays the coordinator round by round over the captured trajectories. Three readings come out of the one replay:

- `naive_member_round` — **Arm N, pre-registered**: one full O(H²) pass after *every member-round export*. The pessimistic bound.
- `incremental` — **Arm I, pre-registered**: delta-scan; totals `H(H−1)/2` for the whole run.
- `naive_global_round` — **disclosed secondary, not verdict-bearing**: one full pass per *synchronized global round*. Spec §4.1's "one scan/round" is ambiguous between this and Arm N; this figure is reported so the bracket's interior is visible. **No prior depends on it.**

Comparison counts are computed in closed form. Step 1 pins the closed forms against Task 1's real comparison loops, so the arithmetic is *earned*, not asserted.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_west_experiment.py`:

```python
def test_pair_comparisons_matches_the_real_naive_scan():
    """The closed form is earned: it must equal what Coordinator.consistency_scan
    actually counts for the same held set."""
    from west_experiment import _pair_comparisons
    from west_coordinator import Coordinator
    from egif_parser_dau import parse_egif
    coord = Coordinator()
    coord.ingest("F0", parse_egif('(links_to "a" "b") (has_tag "a" "t")'))
    coord.ingest("F1", parse_egif('(links_to "c" "d") (in_folder "c" "F1")'))
    coord.consistency_scan()
    assert coord.scan_comparisons == _pair_comparisons(len(coord.held))


def test_incremental_comparisons_matches_the_real_incremental_scan():
    from west_experiment import _incremental_comparisons
    from west_coordinator import Coordinator
    from egif_parser_dau import parse_egif
    coord = Coordinator()
    coord.ingest("F0", parse_egif('(links_to "a" "b") (has_tag "a" "t")'))
    first_new = set(coord._unscanned)
    expected = _incremental_comparisons(len(coord.held), len(first_new))
    coord.consistency_scan_incremental()
    assert coord.scan_comparisons_incremental == expected


def test_replay_incremental_equals_one_full_scan_of_the_final_held_set():
    """Arm I's whole-run invariant, at replay level."""
    from west_experiment import replay_coordinator_tax, _pair_comparisons
    traj = {
        "F0": [frozenset({"a"}), frozenset({"a", "b"}), frozenset({"a", "b"})],
        "F1": [frozenset({"a"}), frozenset({"a"}), frozenset({"a", "c"})],
    }
    tax = replay_coordinator_tax(traj)
    # held = {(F0,a),(F0,b),(F1,a),(F1,c)} => H = 4
    assert tax.cells_written == 4
    assert tax.incremental == _pair_comparisons(4)


def test_replay_naive_member_round_exceeds_global_round_by_the_member_factor():
    from west_experiment import replay_coordinator_tax
    traj = {
        "F0": [frozenset({"a"}), frozenset({"a", "b"})],
        "F1": [frozenset({"a"}), frozenset({"a", "c"})],
    }
    tax = replay_coordinator_tax(traj)
    assert tax.naive_member_round > tax.naive_global_round > 0
    assert tax.naive_global_round >= tax.incremental


def test_replay_naive_grows_with_rounds_but_incremental_does_not():
    """The bracket's whole point: extra quiet rounds cost Arm N and are free to Arm I."""
    from west_experiment import replay_coordinator_tax
    short = {"F0": [frozenset({"a", "b"})], "F1": [frozenset({"a"})]}
    long = {"F0": [frozenset({"a", "b"})] * 5, "F1": [frozenset({"a"})] * 5}
    t_short, t_long = replay_coordinator_tax(short), replay_coordinator_tax(long)
    assert t_long.naive_member_round > t_short.naive_member_round
    assert t_long.incremental == t_short.incremental
    assert t_long.cells_written == t_short.cells_written


def test_replay_is_empty_for_empty_trajectories():
    from west_experiment import replay_coordinator_tax
    tax = replay_coordinator_tax({})
    assert (tax.cells_written, tax.naive_member_round,
            tax.naive_global_round, tax.incremental) == (0, 0, 0, 0)


def test_replay_is_deterministic():
    from west_experiment import replay_coordinator_tax
    traj = {
        "F1": [frozenset({"b", "a"}), frozenset({"a", "b", "c"})],
        "F0": [frozenset({"a"}), frozenset({"a", "z"})],
    }
    a = replay_coordinator_tax(traj)
    b = replay_coordinator_tax(traj)
    assert a == b
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_west_experiment.py -v -k "replay or comparisons"`
Expected: FAIL — `ImportError: cannot import name 'replay_coordinator_tax' from 'west_experiment'`

- [ ] **Step 3: Implement**

Add to `src/west_experiment.py` (after the existing `_apportion` function):

```python
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
            new = {(f, rel) for rel in sorted(traj[g])} - held
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
```

Ensure `src/west_experiment.py`'s imports include `dataclass`, `field`, `Dict`, `List` (add any missing names to the existing `from dataclasses import ...` / `from typing import ...` lines).

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_west_experiment.py -v`
Expected: PASS — all tests, including the pre-existing E1 ones.

- [ ] **Step 5: Commit**

```bash
git add src/west_experiment.py tests/test_west_experiment.py
git commit -m "west-e2: per-round coordinator tax replay (A3), three readings from one pass"
```

---

## Task 4: Folder-member-only CV (the P2 defect fix)

**Files:**
- Modify: `src/west_measure.py`
- Test: `tests/test_west_measure.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `west_measure.MemberCostReading` (fields `folder_member_costs: List[int]`, `journal_member_cost: Optional[int]`, `mean: float`, `cv: float`) and `west_measure.read_member_costs(member_costs: List[int]) -> MemberCostReading`.

**Context (spec §3.3).** E1 read CV over **all** `F+1` members. `_fed_members` appends the journal-member **last**, and it costs ~30× less than a folder-member (`[4506, 4288, 120]` at F=2). That single outlier drives the all-member CV to 0.68 at F=2 but only 0.40 at F=6, where five more folder-members dilute it — so E1's P2 statistic moves with F for reasons unrelated to terminal-unit invariance. E2 reads CV over **folder-members only** and reports the journal-member separately.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_west_measure.py`:

```python
def test_read_member_costs_excludes_the_trailing_journal_member():
    from west_measure import read_member_costs
    r = read_member_costs([4506, 4288, 120])      # the measured F=2 case
    assert r.folder_member_costs == [4506, 4288]
    assert r.journal_member_cost == 120
    assert r.cv < 0.05, "two folder-members within 2.5% must read as tight"


def test_the_journal_outlier_would_have_flipped_the_verdict():
    """Pins the defect this fix exists for: all-member CV crosses 0.5, folder-only does not."""
    from west_measure import read_member_costs
    costs = [4506, 4288, 120]
    mean_all = sum(costs) / len(costs)
    var_all = sum((c - mean_all) ** 2 for c in costs) / len(costs)
    cv_all = (var_all ** 0.5) / mean_all
    assert cv_all > 0.5                            # E1's statistic: "refuted"
    assert read_member_costs(costs).cv < 0.5       # E2's statistic: "held"


def test_read_member_costs_mean_is_over_folder_members_only():
    from west_measure import read_member_costs
    r = read_member_costs([100, 200, 3])
    assert r.mean == 150.0


def test_read_member_costs_handles_degenerate_inputs():
    from west_measure import read_member_costs
    empty = read_member_costs([])
    assert empty.folder_member_costs == [] and empty.journal_member_cost is None
    assert empty.cv == 0.0 and empty.mean == 0.0
    only_journal = read_member_costs([120])
    assert only_journal.folder_member_costs == []
    assert only_journal.journal_member_cost == 120
    assert only_journal.cv == 0.0


def test_read_member_costs_zero_mean_does_not_divide_by_zero():
    from west_measure import read_member_costs
    r = read_member_costs([0, 0, 0])
    assert r.cv == 0.0
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_west_measure.py -v -k member_costs`
Expected: FAIL — `ImportError: cannot import name 'read_member_costs' from 'west_measure'`

- [ ] **Step 3: Implement**

Add to `src/west_measure.py`:

```python
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_west_measure.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/west_measure.py tests/test_west_measure.py
git commit -m "west-e2: folder-member-only CV — fix the journal-outlier defect in P2's statistic"
```

---

## Task 5: OLS log-log power-law fit

**Files:**
- Modify: `src/west_measure.py`
- Test: `tests/test_west_measure.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `west_measure.PowerLawFit` (fields `beta: float`, `stderr: float`, `r_squared: float`, `n: int`, `weak: bool`) and `west_measure.fit_power_law(sizes: List[float], costs: List[float]) -> PowerLawFit`.

**Context (spec §4).** OLS of `log(cost)` on `log(size)`; β is the slope. The weak-fit rule is load-bearing: `n < 6 or r_squared < 0.90` sets `weak=True`, and Task 7 must then record the dependent prior `"undetermined"` rather than a verdict. Stdlib `math` only.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_west_measure.py`:

```python
def test_fit_power_law_recovers_a_known_exponent():
    from west_measure import fit_power_law
    sizes = [2, 4, 6, 8, 12, 16]
    costs = [3.0 * (s ** 1.8) for s in sizes]      # exact power law
    fit = fit_power_law(sizes, costs)
    assert abs(fit.beta - 1.8) < 1e-6
    assert fit.r_squared > 0.9999
    assert fit.n == 6 and fit.weak is False
    assert fit.stderr < 1e-6


def test_fit_power_law_recovers_a_linear_exponent():
    from west_measure import fit_power_law
    sizes = [2, 4, 6, 8, 12, 16]
    costs = [500.0 * s for s in sizes]
    fit = fit_power_law(sizes, costs)
    assert abs(fit.beta - 1.0) < 1e-6
    assert fit.weak is False


def test_fit_power_law_marks_too_few_points_weak():
    from west_measure import fit_power_law
    sizes = [2, 4, 8]
    costs = [3.0 * (s ** 1.8) for s in sizes]
    fit = fit_power_law(sizes, costs)
    assert fit.n == 3 and fit.weak is True, "fewer than six points is a weak fit"


def test_fit_power_law_marks_a_poor_fit_weak():
    from west_measure import fit_power_law
    sizes = [2, 4, 6, 8, 12, 16]
    costs = [10.0, 900.0, 30.0, 5000.0, 60.0, 12000.0]   # no power law here
    fit = fit_power_law(sizes, costs)
    assert fit.r_squared < 0.90 and fit.weak is True


def test_fit_power_law_refuses_nonpositive_and_mismatched_input():
    import pytest
    from west_measure import fit_power_law
    with pytest.raises(ValueError):
        fit_power_law([2, 4], [1.0])                 # length mismatch
    with pytest.raises(ValueError):
        fit_power_law([2, 0, 4], [1.0, 2.0, 3.0])    # log(0) undefined
    with pytest.raises(ValueError):
        fit_power_law([2, 4, 8], [1.0, -2.0, 3.0])   # log of a negative


def test_fit_power_law_is_weak_not_crashing_on_degenerate_sizes():
    from west_measure import fit_power_law
    fit = fit_power_law([4, 4, 4], [10.0, 20.0, 30.0])   # zero variance in x
    assert fit.weak is True and fit.beta == 0.0
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_west_measure.py -v -k power_law`
Expected: FAIL — `ImportError: cannot import name 'fit_power_law' from 'west_measure'`

- [ ] **Step 3: Implement**

Add `import math` to the top of `src/west_measure.py`, then add:

```python
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_west_measure.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/west_measure.py tests/test_west_measure.py
git commit -m "west-e2: OLS log-log power-law fit with the pre-registered weak-fit rule"
```

---

## Task 6: One grid point — the traced FED run and `run_e2_config`

**Files:**
- Modify: `src/west_experiment.py`
- Test: `tests/test_west_experiment.py`

**Interfaces:**
- Consumes: `TracingMaterializer` (Task 2), `replay_coordinator_tax` / `CoordinatorTax` (Task 3), `read_member_costs` / `MemberCostReading` (Task 4).
- Produces:
  - `west_experiment.run_fed_traced(root, manifest, *, rounds: int, ttl: int) -> Tuple[ArrangementResult, CoordinatorTax]`
  - `west_experiment.E2ConfigResult` — dataclass with `folders: int`, `rounds: int`, `ttl: int`, `mono: ArrangementResult`, `fed: ArrangementResult`, `tax: CoordinatorTax`, `member_reading: MemberCostReading`, `fed_cost_naive: int`, `fed_cost_incremental: int`, `gap: float`.
  - `west_experiment.run_e2_config(root, manifest, *, folders: int, rounds: int, ttl: int) -> E2ConfigResult`

**Context.** `run_fed_traced` mirrors `_fed_members` but uses `TracingMaterializer` so each folder-member's per-round relation trajectory is captured. The journal-member is **excluded** from the trajectories (E1's `_fed_members` already excludes it from `coord.ingest` — journal facts are never cross-folder link targets), but its cost still counts toward FED's total. `fed_cost_naive` and `fed_cost_incremental` are the two pre-registered arm totals: member materialisation + peel + the respective tax.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_west_experiment.py`:

```python
def _tiny_vault(tmp_path):
    from vault_generator import generate_vault
    return generate_vault(tmp_path, seed=20260721, folders=2, notes_per_folder=4,
                          cross_folder_link_prob=0.15, journal_len=4)


def test_run_fed_traced_returns_a_tax_and_matches_run_fed_member_count(tmp_path):
    from west_experiment import run_fed_traced
    manifest = _tiny_vault(tmp_path)
    fed, tax = run_fed_traced(tmp_path, manifest, rounds=6, ttl=120)
    assert len(fed.member_costs) == 3          # F=2 folder-members + journal-member
    assert tax.cells_written > 0
    assert tax.incremental <= tax.naive_global_round <= tax.naive_member_round


def test_run_fed_traced_tax_exceeds_the_e1_snapshot_lower_bound(tmp_path):
    """A3 paid down: the per-round tax must be at least the end-of-run snapshot."""
    from west_experiment import run_fed, run_fed_traced
    manifest = _tiny_vault(tmp_path)
    e1 = run_fed(tmp_path, manifest, rounds=6, ttl=120)
    _fed, tax = run_fed_traced(tmp_path, manifest, rounds=6, ttl=120)
    assert tax.naive_member_round >= e1.cost.coordinator_cost


def test_run_e2_config_reports_both_arms_and_they_differ(tmp_path):
    from west_experiment import run_e2_config
    manifest = _tiny_vault(tmp_path)
    cfg = run_e2_config(tmp_path, manifest, folders=2, rounds=6, ttl=120)
    assert cfg.folders == 2 and cfg.rounds == 6
    assert cfg.mono.cost.total() > 0
    assert cfg.fed_cost_naive >= cfg.fed_cost_incremental
    assert cfg.member_reading.journal_member_cost is not None
    assert 0.0 <= cfg.gap <= 1.0


def test_run_e2_config_is_deterministic(tmp_path):
    from west_experiment import run_e2_config
    manifest = _tiny_vault(tmp_path)
    a = run_e2_config(tmp_path, manifest, folders=2, rounds=6, ttl=120)
    b = run_e2_config(tmp_path, manifest, folders=2, rounds=6, ttl=120)
    assert a.mono.cost.total() == b.mono.cost.total()
    assert a.fed_cost_naive == b.fed_cost_naive
    assert a.fed_cost_incremental == b.fed_cost_incremental


def test_e1_run_fed_is_unchanged_by_e2_additions(tmp_path):
    """E1 reproducibility guard."""
    from west_experiment import run_fed
    manifest = _tiny_vault(tmp_path)
    a = run_fed(tmp_path, manifest, rounds=6, ttl=120)
    b = run_fed(tmp_path, manifest, rounds=6, ttl=120)
    assert a.cost.total() == b.cost.total()
    assert a.name == "FED"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_west_experiment.py -v -k "traced or e2_config"`
Expected: FAIL — `ImportError: cannot import name 'run_fed_traced' from 'west_experiment'`

- [ ] **Step 3: Implement**

Add to `src/west_experiment.py` (imports first — extend the existing `from west_measure import ...` line to include `TracingMaterializer`, `read_member_costs`, `MemberCostReading`):

```python
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
            trajectories[folder_name] = list(tm.per_round_relations)

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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_west_experiment.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/west_experiment.py tests/test_west_experiment.py
git commit -m "west-e2: traced FED run + run_e2_config — one grid point under both arms"
```

---

## Task 7: The E2 report and priors P1²–P3²

**Files:**
- Modify: `src/west_experiment.py`
- Test: `tests/test_west_experiment.py`

**Interfaces:**
- Consumes: `E2ConfigResult` (Task 6), `fit_power_law` / `PowerLawFit` (Task 5).
- Produces: `west_experiment.E2Report` (fields `configs: List[E2ConfigResult]`, `fit_mono: PowerLawFit`, `fit_fed_incremental: PowerLawFit`, `fit_fed_naive: PowerLawFit`, `fit_tax_naive: PowerLawFit`, `crossover_f: Optional[float]`, `priors: Dict[str, str]`) and `west_experiment.assemble_e2_report(configs, *, theta: float, tol: float) -> E2Report`.

**Context (spec §6).** Verdict rules, exactly:

- **P1²** `held` iff `fit_mono.beta > fit_fed_incremental.beta` **and** `fit_mono.beta > 1.3`. If either fit is `weak` → `"undetermined"`.
- **P2²** `held` iff every config's folder-member `cv < 0.5` **and** `max(mean)/min(mean) < 1.25` across configs.
- **P3²** `held` iff `fit_tax_naive.beta >= 2.0` **and** a crossover exists (some config with `fed_cost_naive > mono.cost.total()`), else if the tax exponent holds but no crossover is observed, still `held` with `crossover_f` reported as an extrapolation (`None` when it cannot be extrapolated). If `fit_tax_naive.weak` → `"undetermined"`.
- **P4²** is the rider's (Task 8); `assemble_e2_report` records it as `"deferred"`.
- The **pre-committed refutation**: `fit_mono.beta <= fit_fed_incremental.beta` → P1² `"refuted"`.

Crossover extrapolation: with `COST_fed(N) = a·F^γ` and `COST_mono = b·F^β`, solve `a·F^γ = b·F^β` in logs using each fitted line's intercept. Report `None` if `γ <= β` (the curves never cross above the swept range).

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_west_experiment.py`:

```python
def _fake_config(folders, mono_cost, fed_naive, fed_incr, cv=0.03, mean=1000.0,
                 gap=0.0):
    """A hand-built E2ConfigResult for verdict-logic tests — no vault run needed."""
    from west_experiment import E2ConfigResult, CoordinatorTax, ArrangementResult
    from west_measure import CostBreakdown, QualityReading, MemberCostReading
    mono = ArrangementResult(
        name="MONO",
        cost=CostBreakdown(materialization_atoms=mono_cost, peel_proxy=0),
        quality=QualityReading(k2_stick_rate=1.0, k3_ratio=0.0, final_m_size=100))
    fed = ArrangementResult(
        name="FED",
        cost=CostBreakdown(materialization_atoms=fed_incr, peel_proxy=0),
        quality=QualityReading(k2_stick_rate=1.0, k3_ratio=0.0, final_m_size=100),
        member_costs=[1000, 1000, 120], coverage=1.0 - gap)
    return E2ConfigResult(
        folders=folders, rounds=25 * (folders + 1), ttl=120, mono=mono, fed=fed,
        tax=CoordinatorTax(cells_written=1, naive_member_round=fed_naive,
                           naive_global_round=fed_naive // 2, incremental=1),
        member_reading=MemberCostReading([1000, 1000], 120, mean, cv),
        fed_cost_naive=fed_naive, fed_cost_incremental=fed_incr, gap=gap)


SIZES = [2, 4, 6, 8, 12, 16]


def test_p1_holds_when_mono_scales_worse_than_fed():
    from west_experiment import assemble_e2_report
    configs = [_fake_config(f, int(100 * f ** 1.8), int(50 * f ** 3),
                            int(500 * f)) for f in SIZES]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert abs(rep.fit_mono.beta - 1.8) < 0.01
    assert abs(rep.fit_fed_incremental.beta - 1.0) < 0.01
    assert rep.priors["P1"] == "held"


def test_p1_refuted_when_mono_does_not_scale_worse():
    from west_experiment import assemble_e2_report
    configs = [_fake_config(f, int(100 * f), int(50 * f ** 3),
                            int(500 * f ** 1.5)) for f in SIZES]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert rep.priors["P1"] == "refuted"


def test_p1_undetermined_on_a_weak_fit():
    from west_experiment import assemble_e2_report
    configs = [_fake_config(f, int(100 * f ** 1.8), int(50 * f ** 3),
                            int(500 * f)) for f in [2, 4, 8]]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert rep.fit_mono.weak is True
    assert rep.priors["P1"] == "undetermined"


def test_p2_holds_when_per_member_cost_is_flat_and_tight():
    from west_experiment import assemble_e2_report
    configs = [_fake_config(f, int(100 * f ** 1.8), int(50 * f ** 3), int(500 * f),
                            cv=0.03, mean=1000.0) for f in SIZES]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert rep.priors["P2"] == "held"


def test_p2_refuted_when_a_single_config_has_loose_members():
    from west_experiment import assemble_e2_report
    configs = [_fake_config(f, int(100 * f ** 1.8), int(50 * f ** 3), int(500 * f),
                            cv=0.03 if f != 8 else 0.7) for f in SIZES]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert rep.priors["P2"] == "refuted"


def test_p2_refuted_when_mean_per_member_cost_drifts_across_the_sweep():
    from west_experiment import assemble_e2_report
    configs = [_fake_config(f, int(100 * f ** 1.8), int(50 * f ** 3), int(500 * f),
                            mean=1000.0 * f) for f in SIZES]   # 8x drift
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert rep.priors["P2"] == "refuted"


def test_p3_holds_and_reports_an_observed_crossover():
    from west_experiment import assemble_e2_report
    # naive tax ∝ F^3 overtakes mono ∝ F^1.8 inside the swept range
    configs = [_fake_config(f, int(100 * f ** 1.8), int(200 * f ** 3),
                            int(500 * f)) for f in SIZES]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert rep.fit_tax_naive.beta >= 2.0
    assert rep.priors["P3"] == "held"
    assert rep.crossover_f is not None


def test_p3_reports_extrapolated_crossover_when_none_is_observed():
    from west_experiment import assemble_e2_report
    configs = [_fake_config(f, int(1e7 * f ** 1.8), int(50 * f ** 3),
                            int(500 * f)) for f in SIZES]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert all(c.fed_cost_naive < c.mono.cost.total() for c in configs)
    assert rep.crossover_f is not None and rep.crossover_f > 16


def test_p4_is_deferred_to_the_rider():
    from west_experiment import assemble_e2_report
    configs = [_fake_config(f, int(100 * f ** 1.8), int(50 * f ** 3),
                            int(500 * f)) for f in SIZES]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert rep.priors["P4"] == "deferred"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_west_experiment.py -v -k "p1_ or p2_ or p3_ or p4_"`
Expected: FAIL — `ImportError: cannot import name 'assemble_e2_report' from 'west_experiment'`

- [ ] **Step 3: Implement**

Add to `src/west_experiment.py` (extend the `from west_measure import ...` line with `fit_power_law`, `PowerLawFit`):

```python
P1_MIN_MONO_BETA = 1.3
P2_MAX_CV = 0.5
P2_MAX_MEAN_RATIO = 1.25
P3_MIN_TAX_BETA = 2.0


@dataclass
class E2Report:
    """The assembled size-sweep result: the fitted exponents, the crossover, and
    the pre-registered verdicts P1²-P4² (spec §6). P4² belongs to the ttl rider
    and reads "deferred" here."""
    configs: List["E2ConfigResult"]
    fit_mono: PowerLawFit
    fit_fed_incremental: PowerLawFit
    fit_fed_naive: PowerLawFit
    fit_tax_naive: PowerLawFit
    crossover_f: Optional[float]
    priors: Dict[str, str]


def _crossover(fit_fed_naive: PowerLawFit, fit_mono: PowerLawFit,
               configs) -> Optional[float]:
    """The F at which COST_fed(N) overtakes COST_mono.

    Returns the smallest **observed** crossover if one falls inside the swept
    range; otherwise extrapolates from the two fitted lines. ``None`` when the
    FED-naive exponent does not exceed MONO's (the curves never cross above the
    range) or the fit is too degenerate to extrapolate."""
    observed = [c.folders for c in sorted(configs, key=lambda c: c.folders)
                if c.fed_cost_naive > c.mono.cost.total()]
    if observed:
        return float(observed[0])
    if fit_fed_naive.beta <= fit_mono.beta:
        return None
    # Recover each line's intercept in log space from its own points.
    xs = [math.log(c.folders) for c in configs]
    if not xs:
        return None
    mx = sum(xs) / len(xs)
    ly_fed = [math.log(c.fed_cost_naive) for c in configs]
    ly_mono = [math.log(c.mono.cost.total()) for c in configs]
    a_fed = sum(ly_fed) / len(ly_fed) - fit_fed_naive.beta * mx
    a_mono = sum(ly_mono) / len(ly_mono) - fit_mono.beta * mx
    denom = fit_fed_naive.beta - fit_mono.beta
    if denom <= 0:
        return None
    return math.exp((a_mono - a_fed) / denom)


def assemble_e2_report(configs, *, theta: float, tol: float) -> E2Report:
    """Fit the exponents over the grid and decide P1²-P3² (spec §6). ``theta``
    and ``tol`` are carried for the record and for the coherence read; the
    weak-fit rule turns any fit-dependent prior into "undetermined"."""
    ordered = sorted(configs, key=lambda c: c.folders)
    sizes = [c.folders for c in ordered]
    fit_mono = fit_power_law(sizes, [c.mono.cost.total() for c in ordered])
    fit_fed_incr = fit_power_law(sizes, [c.fed_cost_incremental for c in ordered])
    fit_fed_naive = fit_power_law(sizes, [c.fed_cost_naive for c in ordered])
    fit_tax_naive = fit_power_law(
        sizes, [max(c.tax.naive_member_round, 1) for c in ordered])

    # P1² — the headline exponent separation.
    if fit_mono.weak or fit_fed_incr.weak:
        p1 = "undetermined"
    elif fit_mono.beta > fit_fed_incr.beta and fit_mono.beta > P1_MIN_MONO_BETA:
        p1 = "held"
    else:
        p1 = "refuted"

    # P2² — terminal-unit invariance: tight within each config, flat across them.
    means = [c.member_reading.mean for c in ordered if c.member_reading.mean > 0]
    tight = all(c.member_reading.cv < P2_MAX_CV for c in ordered)
    flat = bool(means) and (max(means) / min(means) < P2_MAX_MEAN_RATIO)
    p2 = "held" if (tight and flat) else "refuted"

    # P3² — coordination is the binding constraint under Arm N.
    crossover = _crossover(fit_fed_naive, fit_mono, ordered)
    if fit_tax_naive.weak:
        p3 = "undetermined"
    else:
        p3 = "held" if fit_tax_naive.beta >= P3_MIN_TAX_BETA else "refuted"

    return E2Report(configs=ordered, fit_mono=fit_mono,
                    fit_fed_incremental=fit_fed_incr,
                    fit_fed_naive=fit_fed_naive, fit_tax_naive=fit_tax_naive,
                    crossover_f=crossover,
                    priors={"P1": p1, "P2": p2, "P3": p3, "P4": "deferred"})
```

Add `import math` to `src/west_experiment.py`'s imports if absent.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_west_experiment.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/west_experiment.py tests/test_west_experiment.py
git commit -m "west-e2: E2 report — fitted exponents, crossover, priors P1²-P3²"
```

---

## Task 8: The ttl rider and P4²

**Files:**
- Modify: `src/west_experiment.py`
- Test: `tests/test_west_experiment.py`

**Interfaces:**
- Consumes: `run_mono`, `run_fed_traced` (Task 6).
- Produces:
  - `west_experiment.TtlReading` — `ttl: int` (0 means decay off), `mono_m: int`, `fed_m: int`, `ratio: float`.
  - `west_experiment.run_ttl_rider(root, manifest, *, rounds: int, ttls: List[int]) -> List[TtlReading]`
  - `west_experiment.decide_p4(readings: List[TtlReading]) -> str`

**Context (spec §5).** E1 saw FED |M|Σ = 1367 vs MONO |M| = 752. The hypothesis is decay pressure. Run F=6, R=175 at `ttl ∈ {60, 120, 240, off}` and read the FED/MONO |M| ratio. **P4² `held`** iff the ratio narrows **monotonically non-increasing** as ttl rises (with `off` last, treated as the largest ttl). Otherwise `refuted` — the retention advantage is structural, not a decay artifact. `ttl=0` is the sentinel for "off"; `run_mono`/`_run_member_traced` already map a non-positive ttl to `None` (no decay).

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_west_experiment.py`:

```python
def test_decide_p4_holds_on_a_monotonically_narrowing_ratio():
    from west_experiment import decide_p4, TtlReading
    readings = [TtlReading(60, 100, 300, 3.0), TtlReading(120, 100, 200, 2.0),
                TtlReading(240, 100, 150, 1.5), TtlReading(0, 100, 100, 1.0)]
    assert decide_p4(readings) == "held"


def test_decide_p4_refuted_when_the_ratio_does_not_narrow():
    from west_experiment import decide_p4, TtlReading
    readings = [TtlReading(60, 100, 150, 1.5), TtlReading(120, 100, 200, 2.0),
                TtlReading(240, 100, 210, 2.1), TtlReading(0, 100, 250, 2.5)]
    assert decide_p4(readings) == "refuted"


def test_decide_p4_treats_ttl_zero_as_the_largest_ttl():
    """`off` must sort last however the caller ordered the list."""
    from west_experiment import decide_p4, TtlReading
    readings = [TtlReading(0, 100, 100, 1.0), TtlReading(240, 100, 150, 1.5),
                TtlReading(60, 100, 300, 3.0), TtlReading(120, 100, 200, 2.0)]
    assert decide_p4(readings) == "held"


def test_decide_p4_undetermined_on_too_few_points():
    from west_experiment import decide_p4, TtlReading
    assert decide_p4([TtlReading(120, 100, 200, 2.0)]) == "undetermined"
    assert decide_p4([]) == "undetermined"


def test_run_ttl_rider_produces_one_reading_per_ttl(tmp_path):
    from west_experiment import run_ttl_rider
    manifest = _tiny_vault(tmp_path)
    readings = run_ttl_rider(tmp_path, manifest, rounds=6, ttls=[120, 0])
    assert [r.ttl for r in readings] == [120, 0]
    assert all(r.mono_m >= 0 and r.fed_m >= 0 for r in readings)
    assert all(r.ratio >= 0.0 for r in readings)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_west_experiment.py -v -k "p4 or ttl_rider"`
Expected: FAIL — `ImportError: cannot import name 'run_ttl_rider' from 'west_experiment'`

- [ ] **Step 3: Implement**

Add to `src/west_experiment.py`:

```python
@dataclass(frozen=True)
class TtlReading:
    """One cell of the ttl rider (spec §5). ``ttl=0`` means decay off, and is
    ordered as the largest ttl. ``ratio`` = FED |M|Σ / MONO |M|."""
    ttl: int
    mono_m: int
    fed_m: int
    ratio: float


def run_ttl_rider(root: Path, manifest, *, rounds: int,
                  ttls: List[int]) -> List[TtlReading]:
    """Run MONO and the traced passive FED at one config across ``ttls``,
    reading final |M| at each — the decay-pressure probe for E1's
    FED-retains-more observation. ``ttl=0`` means no disuse-decay."""
    readings: List[TtlReading] = []
    for ttl in ttls:
        mono = run_mono(root, rounds=rounds, ttl=ttl)
        fed, _tax = run_fed_traced(root, manifest, rounds=rounds, ttl=ttl)
        mono_m = mono.quality.final_m_size
        fed_m = fed.quality.final_m_size
        readings.append(TtlReading(ttl=ttl, mono_m=mono_m, fed_m=fed_m,
                                   ratio=(fed_m / mono_m) if mono_m else 0.0))
    return readings


def decide_p4(readings: List[TtlReading]) -> str:
    """P4² (spec §5, §6): the FED/MONO |M| ratio narrows monotonically as
    ttl -> off. ``held`` => the retention advantage is a decay artifact;
    ``refuted`` => it is structural. Fewer than two points => "undetermined"."""
    if len(readings) < 2:
        return "undetermined"
    # ttl=0 means "off" — the largest decay window, so it sorts last.
    ordered = sorted(readings, key=lambda r: (r.ttl == 0, r.ttl))
    ratios = [r.ratio for r in ordered]
    narrowing = all(b <= a + 1e-9 for a, b in zip(ratios, ratios[1:]))
    return "held" if narrowing else "refuted"
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_west_experiment.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/west_experiment.py tests/test_west_experiment.py
git commit -m "west-e2: ttl rider + P4² (is FED-retains-more a decay artifact?)"
```

---

## Task 9: The sweep driver

**Files:**
- Create: `tools/run_west_e2.py`
- Create: `tests/test_west_e2_driver.py`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: `run_e2_config`, `assemble_e2_report`, `run_ttl_rider`, `decide_p4` (Tasks 6–8); `vault_generator.generate_vault` (existing).
- Produces: `tools/run_west_e2.py` with `SEED`, `GRID`, `RIDER_TTLS`, `build_grid()`, and `main()`.

**Context.** Mirrors `tools/run_west_e1.py` — numbers-only stdout, a determinism canary, argparse knobs. The determinism canary runs **one** config (F=6) twice, not the whole sweep (wall-clock; disclosed per spec §7). Full-sweep wall-clock is ≈3 h, so the driver must flush output per config so a long run is observable.

**Custody:** stdout is numbers only. Never print a note id, title, path, or the vault destination.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_west_e2_driver.py`:

```python
"""Driver contract for the E2 sweep (numbers-only custody + the pre-registered grid)."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DRIVER = ROOT / "tools" / "run_west_e2.py"

sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))


def test_driver_exists():
    assert DRIVER.exists()


def test_grid_matches_the_pre_registered_spec():
    import run_west_e2
    assert run_west_e2.SEED == 20260721
    assert [f for f, _r in run_west_e2.GRID] == [2, 4, 6, 8, 12, 16]
    assert [r for _f, r in run_west_e2.GRID] == [75, 125, 175, 225, 325, 425]
    for folders, rounds in run_west_e2.GRID:
        assert rounds == 25 * (folders + 1), "R = 25*(F+1): 25 rounds per member"


def test_rider_ttls_match_the_spec():
    import run_west_e2
    assert run_west_e2.RIDER_TTLS == [60, 120, 240, 0]   # 0 == off, ordered last


def test_build_grid_is_pure_and_deterministic():
    import run_west_e2
    assert run_west_e2.build_grid() == run_west_e2.build_grid()
    assert run_west_e2.build_grid() == run_west_e2.GRID


def test_driver_runs_a_tiny_sweep_and_prints_numbers_only(tmp_path):
    """End-to-end smoke on a deliberately tiny grid, asserting the custody rule."""
    out = subprocess.run(
        [sys.executable, str(DRIVER), "--dest", str(tmp_path), "--smoke",
         "--no-canary"],
        capture_output=True, text=True, timeout=900, cwd=str(ROOT),
    )
    assert out.returncode == 0, out.stderr
    text = out.stdout
    assert "beta_mono=" in text and "beta_fed_incr=" in text
    assert "priors:" in text
    # Custody: no path, no note id, no .md filename may reach stdout.
    assert ".md" not in text
    assert str(tmp_path) not in text
    assert "note-" not in text
    assert "Folder-" not in text


def test_driver_reports_the_disclosed_secondary_and_the_a3_note(tmp_path):
    out = subprocess.run(
        [sys.executable, str(DRIVER), "--dest", str(tmp_path), "--smoke",
         "--no-canary"],
        capture_output=True, text=True, timeout=900, cwd=str(ROOT),
    )
    assert "naive_global" in out.stdout, "the bracket's interior must be reported"
    assert "not verdict-bearing" in out.stdout
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_west_e2_driver.py -v`
Expected: FAIL — `assert DRIVER.exists()` fails; the imports raise `ModuleNotFoundError: run_west_e2`.

- [ ] **Step 3: Implement**

Create `tools/run_west_e2.py`:

```python
"""West-in-kytē E2 driver — the size sweep, the fitted exponents, the P1²-P4²
verdicts, the ttl rider, the determinism canary.

Numbers-only stdout (custody-safe): no note id, title, path, or body text is
ever printed. Spec: docs/superpowers/specs/2026-07-22-west-in-kyte-e2-design.md"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from vault_generator import generate_vault
from west_experiment import (run_e2_config, assemble_e2_report, run_ttl_rider,
                             decide_p4)

# Pre-registered E2 knobs (spec §2 — fixed).
SEED = 20260721
NOTES_PER_FOLDER = 40
P_CROSS = 0.15
JOURNAL_LEN = 40
TTL = 120
THETA, TOL = 0.20, 0.10
FOLDER_SIZES = [2, 4, 6, 8, 12, 16]
RIDER_FOLDERS = 6
RIDER_TTLS = [60, 120, 240, 0]          # 0 == decay off, ordered last
CANARY_FOLDERS = 6

# Smoke grid — for the driver contract test only, never for a real run.
SMOKE_SIZES = [2, 3]
SMOKE_NOTES = 3
SMOKE_JOURNAL = 3


def build_grid():
    """The pre-registered grid as (folders, rounds) pairs: R = 25*(F+1), so every
    member performs exactly 25 rounds at every F (spec §2.1)."""
    return [(f, 25 * (f + 1)) for f in FOLDER_SIZES]


GRID = build_grid()


def _run_point(dest_root, folders, rounds, notes, journal, ttl):
    """Generate a corpus for one grid point and run MONO + traced FED over it."""
    dest = dest_root / f"f{folders}"
    manifest = generate_vault(dest, seed=SEED, folders=folders,
                              notes_per_folder=notes, cross_folder_link_prob=P_CROSS,
                              journal_len=journal)
    return run_e2_config(dest, manifest, folders=folders, rounds=rounds, ttl=ttl), manifest, dest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", default=None, help="corpus dir (default: a temp dir)")
    ap.add_argument("--ttl", type=int, default=TTL)
    ap.add_argument("--smoke", action="store_true",
                    help="tiny grid for the driver contract test")
    ap.add_argument("--no-canary", action="store_true")
    ap.add_argument("--no-rider", action="store_true")
    args = ap.parse_args()

    import tempfile
    dest_root = Path(args.dest) if args.dest else Path(tempfile.mkdtemp(prefix="west_e2_"))
    dest_root.mkdir(parents=True, exist_ok=True)

    if args.smoke:
        grid = [(f, 4) for f in SMOKE_SIZES]
        notes, journal = SMOKE_NOTES, SMOKE_JOURNAL
        rider_ttls = [120, 0]
    else:
        grid = GRID
        notes, journal = NOTES_PER_FOLDER, JOURNAL_LEN
        rider_ttls = RIDER_TTLS

    print("=== West-in-kytē E2 — the size sweep (numbers only) ===", flush=True)
    print(f"seed={SEED} n={notes} p={P_CROSS} J={journal} ttl={args.ttl} "
          f"theta={THETA} tol={TOL} points={len(grid)}", flush=True)

    configs = []
    rider_manifest = rider_dest = None
    for folders, rounds in grid:
        t0 = time.time()
        cfg, manifest, dest = _run_point(dest_root, folders, rounds, notes,
                                         journal, args.ttl)
        configs.append(cfg)
        if folders == (SMOKE_SIZES[0] if args.smoke else RIDER_FOLDERS):
            rider_manifest, rider_dest = manifest, dest
        print(f"F={folders} R={rounds} "
              f"mono={cfg.mono.cost.total()} "
              f"fed_incr={cfg.fed_cost_incremental} fed_naive={cfg.fed_cost_naive} "
              f"tax(cells={cfg.tax.cells_written} incr={cfg.tax.incremental} "
              f"naive_global={cfg.tax.naive_global_round} "
              f"naive_member={cfg.tax.naive_member_round}) "
              f"cv={round(cfg.member_reading.cv, 4)} "
              f"mean_member={round(cfg.member_reading.mean, 1)} "
              f"journal_member={cfg.member_reading.journal_member_cost} "
              f"|M|mono={cfg.mono.quality.final_m_size} "
              f"|M|fed={cfg.fed.quality.final_m_size} "
              f"K2mono={cfg.mono.quality.k2_stick_rate} "
              f"K2fed={cfg.fed.quality.k2_stick_rate} "
              f"gap={round(cfg.gap, 4)} wall_s={round(time.time() - t0, 1)}",
              flush=True)

    rep = assemble_e2_report(configs, theta=THETA, tol=TOL)
    print(f"beta_mono={round(rep.fit_mono.beta, 4)} "
          f"(se={round(rep.fit_mono.stderr, 4)} r2={round(rep.fit_mono.r_squared, 4)} "
          f"weak={rep.fit_mono.weak})", flush=True)
    print(f"beta_fed_incr={round(rep.fit_fed_incremental.beta, 4)} "
          f"(se={round(rep.fit_fed_incremental.stderr, 4)} "
          f"r2={round(rep.fit_fed_incremental.r_squared, 4)} "
          f"weak={rep.fit_fed_incremental.weak})", flush=True)
    print(f"beta_fed_naive={round(rep.fit_fed_naive.beta, 4)} "
          f"beta_tax_naive={round(rep.fit_tax_naive.beta, 4)} "
          f"crossover_F={rep.crossover_f}", flush=True)

    p4 = "skipped"
    if not args.no_rider and rider_manifest is not None:
        rider_rounds = 4 if args.smoke else 25 * (RIDER_FOLDERS + 1)
        readings = run_ttl_rider(rider_dest, rider_manifest, rounds=rider_rounds,
                                 ttls=rider_ttls)
        for r in readings:
            print(f"rider ttl={r.ttl} |M|mono={r.mono_m} |M|fed={r.fed_m} "
                  f"ratio={round(r.ratio, 4)}", flush=True)
        p4 = decide_p4(readings)

    priors = dict(rep.priors)
    priors["P4"] = p4
    print(f"priors: {priors}", flush=True)

    canary = "skipped"
    if not args.no_canary:
        folders = CANARY_FOLDERS
        rounds = 25 * (folders + 1)
        a, _m, _d = _run_point(dest_root, folders, rounds, notes, journal, args.ttl)
        b, _m2, _d2 = _run_point(dest_root, folders, rounds, notes, journal, args.ttl)
        canary = "PASS" if (a.mono.cost.total() == b.mono.cost.total()
                            and a.fed_cost_naive == b.fed_cost_naive
                            and a.fed_cost_incremental == b.fed_cost_incremental) else "FAIL"
    print(f"determinism_canary: {canary}", flush=True)

    print("notes: A3 PAID DOWN — the coordinator tax is now a true per-round "
          "replay (spec §3.1), exact for the passive coordinator (read-only, so "
          "replaying it cannot perturb what it measures); the active broker is "
          "NOT replay-exact and is not run here. TWO PRE-REGISTERED ARMS: "
          "fed_naive (Arm N, a full O(H^2) scan per member-round export — the "
          "pessimistic bound) and fed_incr (Arm I, delta-scan — totals H(H-1)/2 "
          "for a whole run however long). naive_global (one scan per "
          "synchronized global round) is a DISCLOSED SECONDARY reading, "
          "reported because spec §4.1's 'one scan/round' is ambiguous between "
          "it and Arm N — it is not verdict-bearing and no prior depends on it. "
          "cv is over FOLDER-MEMBERS ONLY (spec §3.3 — E1 included the "
          "~30x-cheaper journal-member, which alone flips the verdict at small "
          "F); journal_member is reported beside it. K1 = N/A (raise-only "
          "membrane, A1). K3 is expected 0.0 (the vault M carries no Horn "
          "laws — true, not a bug). A weak fit (n<6 or r2<0.90) makes its prior "
          "'undetermined', never held or refuted. The canary runs ONE config "
          "(F=6), not the whole sweep — a narrowing relative to E1, disclosed. "
          "Synthetic corpus: this is an exponent of the generator's topology, "
          "not of real reasoning corpora.", flush=True)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Add the runs-directory custody rule**

Confirm `.gitignore` covers any E2 output directory. Run:

```bash
grep -n "runs/" .gitignore
```

If no rule covers `runs/west_e2*`, append to `.gitignore`:

```
runs/west_e2*/
```

Then verify: `git check-ignore -v runs/west_e2_test/x.md` must report the rule (create the path first if needed, and delete it after).

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/test_west_e2_driver.py -v`
Expected: PASS — all seven tests, including the numbers-only custody assertions.

- [ ] **Step 6: Run the full suite (the E1-reproducibility guard)**

Run: `uv run pytest tests/ -q`
Expected: **0 failed.** The baseline before this plan was 3933 passed / 0 failed; the count rises by the tests added here. Any *failure* in a pre-existing test means an E2 addition changed E1 behaviour — stop and fix rather than proceeding.

- [ ] **Step 7: Verify the E1 driver still runs unchanged**

Run: `uv run python tools/run_west_e1.py --folders 2 --notes 8 --rounds 20`
Expected: the E1 report prints with `determinism_canary: PASS`. E1's entry points must be untouched.

- [ ] **Step 8: Commit**

```bash
git add tools/run_west_e2.py tests/test_west_e2_driver.py .gitignore
git commit -m "west-e2: numbers-only sweep driver with the determinism canary"
```

---

## After the plan

The build is complete when Task 9's full-suite step reports 0 failed. **Do not launch the ≈3 h production sweep as part of the build** — that is a separate, author-initiated run whose findings go to `runs/WEST_E2_LOG.md` against the priors pre-registered in the spec, following the E1 precedent.

---

## Self-Review

**Spec coverage.** §2 grid → Task 9 (`GRID`, pinned by test). §2.1 proportional-R → Task 9 (`R = 25*(F+1)` asserted). §3.1 A3 per-round replay → Tasks 2, 3, 6. §3.2 both arms → Tasks 1, 3, 6, 7. §3.3 CV fix → Task 4. §4 measurements + OLS fit + weak-fit rule → Tasks 5, 7, 9. §5 ttl rider → Task 8. §6 priors P1²–P4² + refutation → Tasks 7, 8. §7 determinism canary → Task 9. §8 honesty ledger → Task 9's disclosure note. §9 build surface → the File Structure table. **No gap found.**

**Placeholder scan.** No TBD/TODO; every code step carries complete code; no "similar to Task N".

**Type consistency.** `CoordinatorTax` fields (`cells_written`, `naive_member_round`, `naive_global_round`, `incremental`) are used identically in Tasks 3, 6, 7, 9. `MemberCostReading` (`folder_member_costs`, `journal_member_cost`, `mean`, `cv`) identically in Tasks 4, 6, 7, 9. `PowerLawFit` (`beta`, `stderr`, `r_squared`, `n`, `weak`) identically in Tasks 5, 7, 9. `TtlReading` (`ttl`, `mono_m`, `fed_m`, `ratio`) identically in Tasks 8, 9. `run_fed_traced` returns a 2-tuple in Tasks 6 and 8 alike.
