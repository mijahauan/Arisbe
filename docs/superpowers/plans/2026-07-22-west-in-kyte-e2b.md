# West-in-kytē E2b (the calibration) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the E2b calibration harness — a folder-bucketing-aware FED runner, round-robin + greedy link-aware bucketings, the Sweep-B cost U-curve reader, the p-sweep with the first broker exercise, the partition-quality arm, and the PB1–PB5 verdicts — so E3's fitness landscape is measured before E3 is designed.

**Architecture:** Purely **additive** to the E2/E1 harness. Every existing entry point (`run_fed`, `run_fed_broker`, `run_fed_traced`, `run_e2_config`, `assemble_e2_report`, both drivers) keeps its exact behaviour so `runs/WEST_E1_LOG.md` and `runs/WEST_E2_LOG.md` stay reproducible. E2b adds a bucketing generalisation of `run_fed_traced` (members = folder-buckets, not one-folder-each), pure bucketing/reading helpers, and a new driver. Per-round member state and the coordinator-tax replay are reused unchanged.

**Tech Stack:** Python 3.12, uv, pytest. Stdlib only (`math`, `dataclasses`, `hashlib` already used by the generator) — no new dependencies.

## Global Constraints

- **Spec of record:** `docs/superpowers/specs/2026-07-22-west-in-kyte-e2b-design.md`. Every number below traces to it.
- **Zero protected-core modification.** If any task appears to need one, **halt and request authorization**. `src/west_*.py`, `src/vault_generator.py`, and `tools/` are unprotected.
- **Do not modify `agon_evolution.py`, `model_materialization.py`, `world_scroll.py`, or `vault_world.py`.**
- **E1 and E2 must stay reproducible.** No behaviour change to `run_fed`, `run_fed_broker`, `run_fed_traced`, `run_e2_config`, `assemble_e2_report`, `run_mono`, `_fed_members`, `_run_member`, `_run_member_traced`, `Coordinator.consistency_scan`, `tools/run_west_e1.py`, or `tools/run_west_e2.py`. New behaviour goes in **new** functions beside them.
- **Determinism is mandatory.** Sort every iteration over a set or dict whose order could reach a result. Bucketings are deterministic functions of `(folders, n)` / `(manifest, n)`.
- **Custody (non-negotiable).** `tools/run_west_e2b.py` stdout is **numbers only** — never a note id, title, path, or **folder name**. Folder *counts*, bucket *sizes*, N, p, costs, cut-link *counts* are numbers and fine; a folder *name* string is not. Output under `runs/west_e2b*` (gitignored). The tracked run log is `runs/WEST_E2B_LOG.md` (spared from the glob like `WEST_E2_LOG.md`).
- **The partition unit is the folder** (spec §1). A "bucket" is a `frozenset` of folder-name strings (e.g. `{"Folder-0","Folder-4","Folder-8"}`); a "bucketing" is a `List[frozenset]` partitioning all of `manifest.folders`.
- **Sweep-B grid (fixed):** `seed=20260721`, `F₀=12`, `n=40`, `p=0.15`, `J=40`, `ttl=120`, **fixed `R=325`**, `N ∈ {1,2,3,4,6,12}`, both arms.
- **p-sweep (fixed):** natural one-folder-per-member at `F=6`, `R=175`, `ttl=120`, `p ∈ {0.15,0.30,0.45,0.60,0.75}`, `θ=0.20`.
- **Quality arm (fixed):** `F₀=12`, `N=4`, `R=325`, p at/above the shoulder (else `p=0.75` flagged), `tol=0.10`.
- **Imports:** flat style — `from west_experiment import ...`, never `from src.west_experiment import ...`.
- **Run tests with:** `uv run pytest <path> -v`.

---

## File Structure

| File | Responsibility |
|---|---|
| `src/west_measure.py` (modify) | pure bucketing helpers (`round_robin_buckets`, `link_aware_buckets`, `cut_link_count`) + the U-curve reader (`read_ucurve` / `UCurveReading`) |
| `src/west_experiment.py` (modify) | `run_fed_bucketed` (members = buckets), the Sweep-B point runner, the p-sweep runner, the quality-arm runner, `assemble_e2b_report` (PB1–PB5) |
| `tools/run_west_e2b.py` (create) | the numbers-only driver (3 parts) + PB1–PB5 verdicts + determinism canary |
| `tests/test_west_measure.py` (modify) | Tasks 1, 3 tests |
| `tests/test_west_experiment.py` (modify) | Tasks 2, 3, 4, 5, 6 tests |
| `tests/test_west_e2b_driver.py` (create) | Task 7 tests |

---

## Task 1: Bucketing helpers (round-robin, link-aware, cut-count)

**Files:**
- Modify: `src/west_measure.py`
- Test: `tests/test_west_measure.py`

**Interfaces:**
- Consumes: `vault_generator.VaultManifest` (fields `folders: Tuple[str,...]`, `cross_links: Tuple[CrossLink,...]`; each `CrossLink` has `source_folder`, `target_folder` strings).
- Produces:
  - `round_robin_buckets(folders, n: int) -> List[frozenset]`
  - `link_aware_buckets(manifest, n: int) -> List[frozenset]`
  - `cut_link_count(buckets: List[frozenset], manifest) -> int`

**Context.** A bucketing partitions all `F₀` folders into `n` disjoint buckets. Round-robin is the quality-blind baseline (folder index `k` → bucket `k mod n`). Link-aware greedily groups the most heavily cross-linked folders together, capped at `F₀//n` folders per bucket, to minimise cross-bucket links — the quality-seeking arm. `cut_link_count` scores a bucketing by how many cross-links cross a bucket boundary (the coherence-cost proxy). All three are pure and deterministic.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_west_measure.py`:

```python
def _manifest(folders, links):
    """A minimal VaultManifest for bucketing tests: folders = ("Folder-0",...),
    links = list of (src_folder, tgt_folder) pairs."""
    from vault_generator import VaultManifest, CrossLink
    cls = tuple(
        CrossLink(source_note="x", source_folder=s, target_note="y", target_folder=t)
        for s, t in links
    )
    return VaultManifest(folders=tuple(folders), notes=(), cross_links=cls, journal_len=0)


def test_round_robin_buckets_partitions_all_folders():
    from west_measure import round_robin_buckets
    folders = tuple(f"Folder-{k}" for k in range(12))
    buckets = round_robin_buckets(folders, 4)
    assert len(buckets) == 4
    assert all(len(b) == 3 for b in buckets)             # 12 / 4, balanced
    union = set().union(*buckets)
    assert union == set(folders)                          # every folder placed once
    assert sum(len(b) for b in buckets) == 12             # disjoint


def test_round_robin_n1_is_the_monolith_bucketing():
    from west_measure import round_robin_buckets
    folders = tuple(f"Folder-{k}" for k in range(12))
    buckets = round_robin_buckets(folders, 1)
    assert buckets == [frozenset(folders)]


def test_round_robin_is_deterministic():
    from west_measure import round_robin_buckets
    folders = tuple(f"Folder-{k}" for k in range(6))
    assert round_robin_buckets(folders, 3) == round_robin_buckets(folders, 3)


def test_link_aware_groups_heavily_linked_folders_together():
    from west_measure import link_aware_buckets, cut_link_count, round_robin_buckets
    folders = [f"Folder-{k}" for k in range(6)]
    # Two tight clusters {0,1,2} and {3,4,5}, each internally linked, no cross-cluster links.
    links = [("Folder-0","Folder-1"),("Folder-1","Folder-2"),("Folder-0","Folder-2"),
             ("Folder-3","Folder-4"),("Folder-4","Folder-5"),("Folder-3","Folder-5")]
    m = _manifest(folders, links)
    la = link_aware_buckets(m, 2)                          # cap 3 per bucket
    assert len(la) == 2 and all(len(b) == 3 for b in la)
    assert frozenset({"Folder-0","Folder-1","Folder-2"}) in la
    assert frozenset({"Folder-3","Folder-4","Folder-5"}) in la
    # link-aware cuts 0 of these links; round-robin (0,2,4 | 1,3,5) cuts all 6.
    assert cut_link_count(la, m) == 0
    assert cut_link_count(round_robin_buckets(folders, 2), m) == 6


def test_cut_link_count_counts_cross_bucket_links():
    from west_measure import cut_link_count
    folders = [f"Folder-{k}" for k in range(4)]
    m = _manifest(folders, [("Folder-0","Folder-1"), ("Folder-2","Folder-3")])
    same = [frozenset({"Folder-0","Folder-1"}), frozenset({"Folder-2","Folder-3"})]
    split = [frozenset({"Folder-0","Folder-2"}), frozenset({"Folder-1","Folder-3"})]
    assert cut_link_count(same, m) == 0
    assert cut_link_count(split, m) == 2


def test_link_aware_is_deterministic_and_partitions():
    from west_measure import link_aware_buckets
    folders = [f"Folder-{k}" for k in range(12)]
    links = [("Folder-0","Folder-1")] * 3 + [("Folder-6","Folder-7")] * 2
    m = _manifest(folders, links)
    a = link_aware_buckets(m, 4)
    b = link_aware_buckets(m, 4)
    assert a == b
    assert set().union(*a) == set(folders) and sum(len(x) for x in a) == 12
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_west_measure.py -v -k "buckets or cut_link"`
Expected: FAIL — `ImportError: cannot import name 'round_robin_buckets' from 'west_measure'`

- [ ] **Step 3: Implement**

Add to `src/west_measure.py` (near the other pure readers):

```python
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
```

Ensure `List` is imported from `typing` in `src/west_measure.py` (it already is — the module uses `List` elsewhere).

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_west_measure.py -v`
Expected: PASS — all tests, including the pre-existing ones.

- [ ] **Step 5: Commit**

```bash
git add src/west_measure.py tests/test_west_measure.py
git commit -m "west-e2b: bucketing helpers — round-robin, greedy link-aware, cut-link count"
```

---

## Task 2: The bucketing-aware FED runner

**Files:**
- Modify: `src/west_experiment.py`
- Test: `tests/test_west_experiment.py`

**Interfaces:**
- Consumes: `_run_member_traced` (existing), `Coordinator` / `member_relation_names` (existing), `replay_coordinator_tax` / `CoordinatorTax` (existing), `peel_proxy` / `read_quality` (existing), `CostBreakdown` / `QualityReading` / `ArrangementResult` (existing).
- Produces: `run_fed_bucketed(root, manifest, *, buckets: List[frozenset], rounds: int, ttl: int) -> Tuple[ArrangementResult, CoordinatorTax]`.

**Context.** This generalises `run_fed_traced` from "one folder per member" to "one **bucket** (a folder-set) per member", plus the journal-member (A2). Read `run_fed_traced` (`src/west_experiment.py`, the `_run_member_traced` loop with the trajectory-shift correction) first — this mirrors it. **Two things must differ from the singleton case and must be exact:**

1. **Coverage keying.** `Coordinator.coverage` resolves each cross-link against `member_ms[target_folder]`. A bucket member covers *several* folders, so populate `member_ms[f] = bucket_M` for **every** folder `f` in the bucket — not just one. Missing this silently under-reports coverage (over-reports gap).
2. **The one-round trajectory-shift correction** (drop `per_round_relations[0]`, append `member_relation_names(final M)`) is load-bearing for the tax and must be applied per bucket exactly as `run_fed_traced` applies it per folder. Do not omit it.

The coordinator ingests once per bucket under a distinct synthetic key `f"bucket-{i}"` (the digest key is a label for `cells_written`/`consistency_scan`; it does not feed coverage, which uses the real folder names in `member_ms`). Trajectories are keyed by `f"bucket-{i}"`. The tax comes from `replay_coordinator_tax(trajectories)`, exactly as in E2.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_west_experiment.py`:

```python
def _bucket_vault(tmp_path, folders=6, notes=4, p=0.15, journal=4):
    from vault_generator import generate_vault
    return generate_vault(tmp_path, seed=20260721, folders=folders,
                          notes_per_folder=notes, cross_folder_link_prob=p,
                          journal_len=journal)


def test_run_fed_bucketed_one_member_per_bucket_plus_journal(tmp_path):
    from west_experiment import run_fed_bucketed
    from west_measure import round_robin_buckets
    manifest = _bucket_vault(tmp_path, folders=6, notes=4)
    buckets = round_robin_buckets(manifest.folders, 3)     # 3 buckets of 2 folders
    fed, tax = run_fed_bucketed(tmp_path, manifest, buckets=buckets, rounds=24, ttl=120)
    assert len(fed.member_costs) == 4                       # 3 buckets + journal
    assert fed.coverage is not None and 0.0 <= fed.coverage <= 1.0
    assert tax.incremental <= tax.naive_global_round <= tax.naive_member_round


def test_run_fed_bucketed_n1_covers_every_cross_link(tmp_path):
    """A single bucket holds every folder, so coverage must be 1.0 (gap 0) —
    every cross-link's target folder is in the one member's folder set."""
    from west_experiment import run_fed_bucketed
    from west_measure import round_robin_buckets
    manifest = _bucket_vault(tmp_path, folders=6, notes=4, p=0.6)  # dense links
    buckets = round_robin_buckets(manifest.folders, 1)
    fed, _tax = run_fed_bucketed(tmp_path, manifest, buckets=buckets, rounds=24, ttl=120)
    assert len(fed.member_costs) == 2                       # 1 bucket + journal
    assert fed.coverage == 1.0


def test_run_fed_bucketed_matches_run_fed_traced_at_singletons(tmp_path):
    """One-folder-per-bucket must reproduce run_fed_traced's cost exactly —
    the bucketed runner is a faithful generalisation, not a new measurement."""
    from west_experiment import run_fed_bucketed, run_fed_traced
    manifest = _bucket_vault(tmp_path, folders=6, notes=4)
    singletons = [frozenset({f}) for f in manifest.folders]
    fedb, taxb = run_fed_bucketed(tmp_path, manifest, buckets=singletons,
                                  rounds=24, ttl=120)
    fedt, taxt = run_fed_traced(tmp_path, manifest, rounds=24, ttl=120)
    assert fedb.cost.materialization_atoms == fedt.cost.materialization_atoms
    assert fedb.cost.peel_proxy == fedt.cost.peel_proxy
    assert taxb == taxt
    assert fedb.coverage == fedt.coverage


def test_run_fed_bucketed_is_deterministic(tmp_path):
    from west_experiment import run_fed_bucketed
    from west_measure import round_robin_buckets
    manifest = _bucket_vault(tmp_path, folders=6, notes=4)
    buckets = round_robin_buckets(manifest.folders, 2)
    a, ta = run_fed_bucketed(tmp_path, manifest, buckets=buckets, rounds=24, ttl=120)
    b, tb = run_fed_bucketed(tmp_path, manifest, buckets=buckets, rounds=24, ttl=120)
    assert a.cost.total() == b.cost.total() and ta == tb
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_west_experiment.py -v -k bucketed`
Expected: FAIL — `ImportError: cannot import name 'run_fed_bucketed' from 'west_experiment'`

- [ ] **Step 3: Implement**

Add to `src/west_experiment.py` (extend the `from west_measure import ...` line if needed — this task adds no new west_measure imports). Place after `run_fed_traced`:

```python
def run_fed_bucketed(root: Path, manifest, *, buckets: List[frozenset],
                     rounds: int, ttl: int):
    """Run the passive FED arrangement with members = folder-BUCKETS (spec §1,
    §2), plus the journal-member (A2), capturing each bucket's per-round
    relation trajectory and replaying the coordinator over it.

    Generalises :func:`run_fed_traced` (one folder per member) to one bucket
    (a folder-set) per member. Returns ``(ArrangementResult, CoordinatorTax)``.
    ``buckets`` must partition ``manifest.folders``. Passive only — the broker
    is not replay-exact (spec §3.1, §8)."""
    member_specs = [(frozenset(b), False, f"e2b_bucket_{i}")
                    for i, b in enumerate(buckets)]
    member_specs.append((frozenset(), True, "e2b_journal"))
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
        if folder_set:                       # a content bucket (journal's is empty)
            bucket_m = res.uod.current_egi
            # Coverage keys on the TARGET folder, and a bucket covers several
            # folders — so map EVERY folder in the bucket to this member's M.
            for f in folder_set:
                member_ms[f] = bucket_m
            # Ingest once per bucket under a distinct synthetic key (the digest
            # key labels cells_written/consistency_scan; it does not feed
            # coverage, which uses the real folder names in member_ms above).
            coord.ingest(uid, bucket_m)
            # Same one-round trajectory-shift correction as run_fed_traced:
            # per_round_relations[0] is the pre-round-1 seed and the final
            # round's own growth is never captured, so drop the leading seed
            # and append the true final M. Do not omit — the tax depends on it.
            raw = list(tm.per_round_relations)
            trajectories[uid] = (
                raw[1:] + [member_relation_names(bucket_m)] if raw else []
            )

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
    arrangement = ArrangementResult(name="FED-bucketed", cost=cost, quality=quality,
                                    member_costs=member_costs, coverage=cov,
                                    conflicts=conflicts)
    return arrangement, replay_coordinator_tax(trajectories)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_west_experiment.py -v -k "bucketed or e2_config or traced"`
Expected: PASS. The `matches_run_fed_traced_at_singletons` test proves the generalisation is faithful.

- [ ] **Step 5: Commit**

```bash
git add src/west_experiment.py tests/test_west_experiment.py
git commit -m "west-e2b: run_fed_bucketed — members are folder-buckets, coverage keyed per-folder"
```

---

## Task 3: The Sweep-B point runner and the U-curve reader

**Files:**
- Modify: `src/west_experiment.py` (the point runner)
- Modify: `src/west_measure.py` (the pure U-curve reader)
- Test: `tests/test_west_experiment.py` (point runner) + `tests/test_west_measure.py` (reader)

**Interfaces:**
- Consumes: `run_fed_bucketed` (Task 2), `round_robin_buckets` / `link_aware_buckets` (Task 1), `read_member_costs` / `MemberCostReading` (existing).
- Produces:
  - `west_experiment.SweepBPoint` — dataclass `n: int`, `fed_cost_naive: int`, `fed_cost_incremental: int`, `member_reading: MemberCostReading`, `m_fed: int`, `k2_fed: Optional[float]`, `k3_fed: float`, `gap: float`, `cut_links: int`.
  - `west_experiment.run_sweepb_point(root, manifest, *, n: int, rounds: int, ttl: int, bucketing: str = "round_robin") -> SweepBPoint`.
  - `west_measure.UCurveReading` — dataclass `argmin_n: int`, `argmin_cost: int`, `interior: bool`, `monotone_nonincreasing: bool`, `costs_by_n: dict`.
  - `west_measure.read_ucurve(points, which: str) -> UCurveReading` where `which ∈ {"naive","incremental"}` and `points` is an iterable of objects with `.n`, `.fed_cost_naive`, `.fed_cost_incremental`.

**Context.** One Sweep-B point runs the bucketed FED at granularity `n` and records both arm totals. The reader turns the six points into the U-curve verdict inputs: `argmin_n` (the cost-minimising granularity), `interior` (`1 < argmin_n < max_n` — PB1's condition), and `monotone_nonincreasing` (PB2's condition for Arm I). The arm totals are assembled exactly as E2's `run_e2_config`: `base = materialization + peel`, `naive = base + tax.cells_written + tax.naive_member_round`, `incremental = base + tax.cells_written + tax.incremental`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_west_measure.py`:

```python
def test_read_ucurve_finds_an_interior_minimum():
    from west_measure import read_ucurve
    class P:
        def __init__(s, n, cn, ci): s.n, s.fed_cost_naive, s.fed_cost_incremental = n, cn, ci
    # naive: U-shaped with min at n=4; incremental: monotone down.
    pts = [P(1, 1000, 900), P(2, 600, 500), P(4, 400, 300),
           P(6, 700, 250), P(12, 1500, 200)]
    naive = read_ucurve(pts, "naive")
    assert naive.argmin_n == 4 and naive.interior is True
    assert naive.monotone_nonincreasing is False
    incr = read_ucurve(pts, "incremental")
    assert incr.argmin_n == 12 and incr.interior is False
    assert incr.monotone_nonincreasing is True


def test_read_ucurve_endpoint_minimum_is_not_interior():
    from west_measure import read_ucurve
    class P:
        def __init__(s, n, c): s.n, s.fed_cost_naive, s.fed_cost_incremental = n, c, c
    pts = [P(1, 100), P(2, 200), P(4, 300)]            # min at the left endpoint
    r = read_ucurve(pts, "naive")
    assert r.argmin_n == 1 and r.interior is False
```

Append to `tests/test_west_experiment.py`:

```python
def test_run_sweepb_point_reports_both_arms_and_cut(tmp_path):
    from west_experiment import run_sweepb_point
    manifest = _bucket_vault(tmp_path, folders=6, notes=4)
    pt = run_sweepb_point(tmp_path, manifest, n=3, rounds=24, ttl=120)
    assert pt.n == 3
    assert pt.fed_cost_naive >= pt.fed_cost_incremental
    assert pt.member_reading.journal_member_cost is not None
    assert pt.cut_links >= 0
    assert 0.0 <= pt.gap <= 1.0


def test_run_sweepb_point_link_aware_cuts_no_more_than_round_robin(tmp_path):
    from west_experiment import run_sweepb_point
    manifest = _bucket_vault(tmp_path, folders=6, notes=4, p=0.6)
    rr = run_sweepb_point(tmp_path, manifest, n=2, rounds=24, ttl=120,
                          bucketing="round_robin")
    la = run_sweepb_point(tmp_path, manifest, n=2, rounds=24, ttl=120,
                          bucketing="link_aware")
    assert la.cut_links <= rr.cut_links
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_west_measure.py -v -k ucurve` then `uv run pytest tests/test_west_experiment.py -v -k sweepb_point`
Expected: FAIL — `ImportError` on `read_ucurve` / `run_sweepb_point`.

- [ ] **Step 3: Implement the reader (`west_measure.py`)**

```python
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
```

- [ ] **Step 4: Implement the point runner (`west_experiment.py`)**

Extend the `from west_measure import ...` line to add `round_robin_buckets`, `link_aware_buckets`, `cut_link_count`. Then add:

```python
@dataclass
class SweepBPoint:
    """One Sweep-B granularity point (spec §2): the bucketed FED at ``n``
    buckets on the fixed corpus, both arm totals."""
    n: int
    fed_cost_naive: int
    fed_cost_incremental: int
    member_reading: MemberCostReading
    m_fed: int
    k2_fed: Optional[float]
    k3_fed: float
    gap: float
    cut_links: int


def run_sweepb_point(root: Path, manifest, *, n: int, rounds: int, ttl: int,
                     bucketing: str = "round_robin") -> SweepBPoint:
    """Run one fixed-corpus Sweep-B point at granularity ``n`` (spec §2).
    ``bucketing`` selects the folder-bucketing: 'round_robin' (baseline) or
    'link_aware' (quality-seeking). Arm totals are assembled exactly as
    run_e2_config."""
    if bucketing == "round_robin":
        buckets = round_robin_buckets(manifest.folders, n)
    elif bucketing == "link_aware":
        buckets = link_aware_buckets(manifest, n)
    else:
        raise ValueError("bucketing must be 'round_robin' or 'link_aware'")
    fed, tax = run_fed_bucketed(root, manifest, buckets=buckets, rounds=rounds, ttl=ttl)
    base = fed.cost.materialization_atoms + fed.cost.peel_proxy
    return SweepBPoint(
        n=n,
        fed_cost_naive=base + tax.cells_written + tax.naive_member_round,
        fed_cost_incremental=base + tax.cells_written + tax.incremental,
        member_reading=read_member_costs(fed.member_costs),
        m_fed=fed.quality.final_m_size,
        k2_fed=fed.quality.k2_stick_rate,
        k3_fed=fed.quality.k3_ratio,
        gap=1.0 - (fed.coverage if fed.coverage is not None else 1.0),
        cut_links=cut_link_count(buckets, manifest),
    )
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/test_west_measure.py tests/test_west_experiment.py -v -k "ucurve or sweepb"`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/west_measure.py src/west_experiment.py tests/test_west_measure.py tests/test_west_experiment.py
git commit -m "west-e2b: Sweep-B point runner + U-curve reader (argmin / interior / monotone)"
```

---

## Task 4: The p-sweep and the broker exercise

**Files:**
- Modify: `src/west_experiment.py`
- Test: `tests/test_west_experiment.py`

**Interfaces:**
- Consumes: `vault_generator.generate_vault` (existing), `run_fed_traced` / `run_fed_broker` (existing).
- Produces:
  - `west_experiment.PSweepPoint` — dataclass `p: float`, `gap: float`, `coverage: float`, `coordinator_cost: int`.
  - `west_experiment.PSweepResult` — dataclass `points: List[PSweepPoint]`, `shoulder_p: Optional[float]`, `broker_routes: Optional[int]`, `broker_coord_cost: Optional[int]`.
  - `west_experiment.run_p_sweep(dest_root, *, folders: int, notes: int, journal: int, rounds: int, ttl: int, seed: int, ps: List[float], theta: float) -> PSweepResult`.

**Context (spec §3).** Regenerate the vault at each p (the natural one-folder-per-member partition, via `run_fed_traced`), read `gap = 1 − coverage`. The shoulder is the smallest p with `gap > θ`. At that p — and only there — additionally run `run_fed_broker` (the first broker exercise) and record its `routes` and coordinator cost. If no p breaches θ, `shoulder_p` is `None` and the broker figures are `None`. Each p gets its own vault subdir under `dest_root` so runs don't collide.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_west_experiment.py`:

```python
def test_run_p_sweep_produces_one_point_per_p_ordered(tmp_path):
    from west_experiment import run_p_sweep
    res = run_p_sweep(tmp_path, folders=4, notes=4, journal=4, rounds=16,
                      ttl=120, seed=20260721, ps=[0.15, 0.45], theta=0.20)
    assert [round(pt.p, 2) for pt in res.points] == [0.15, 0.45]
    assert all(0.0 <= pt.gap <= 1.0 for pt in res.points)
    assert all(pt.coverage == 1.0 - pt.gap for pt in res.points)


def test_run_p_sweep_records_shoulder_and_fires_broker_once(tmp_path):
    """A synthetic threshold: force theta so low that even p=0.15's gap can breach
    it, and confirm the broker fires (routes recorded) at the first breaching p."""
    from west_experiment import run_p_sweep
    res = run_p_sweep(tmp_path, folders=4, notes=4, journal=4, rounds=8,
                      ttl=120, seed=20260721, ps=[0.15, 0.45, 0.75], theta=-1.0)
    # theta=-1 => every gap (>= 0) breaches, so the shoulder is the first p.
    assert res.shoulder_p == 0.15
    assert res.broker_routes is not None and res.broker_routes >= 0
    assert res.broker_coord_cost is not None


def test_run_p_sweep_no_shoulder_leaves_broker_none(tmp_path):
    """theta=2.0 can never be breached (gap <= 1), so no broker run."""
    from west_experiment import run_p_sweep
    res = run_p_sweep(tmp_path, folders=4, notes=4, journal=4, rounds=8,
                      ttl=120, seed=20260721, ps=[0.15, 0.45], theta=2.0)
    assert res.shoulder_p is None
    assert res.broker_routes is None and res.broker_coord_cost is None
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_west_experiment.py -v -k p_sweep`
Expected: FAIL — `ImportError: cannot import name 'run_p_sweep' from 'west_experiment'`

- [ ] **Step 3: Implement**

Add to `src/west_experiment.py` (the module already imports `generate_vault`? check — it imports from `vault_world`, not `vault_generator`; add `from vault_generator import generate_vault` to the imports):

```python
@dataclass
class PSweepPoint:
    """One p-sweep cell (spec §3): the passive gap at a cross-link density."""
    p: float
    gap: float
    coverage: float
    coordinator_cost: int


@dataclass
class PSweepResult:
    """The p-sweep + the first broker exercise (spec §3). ``shoulder_p`` is the
    smallest p with gap > theta (None if none breaches); the broker figures are
    populated only at that p."""
    points: List[PSweepPoint]
    shoulder_p: Optional[float]
    broker_routes: Optional[int]
    broker_coord_cost: Optional[int]


def run_p_sweep(dest_root: Path, *, folders: int, notes: int, journal: int,
                rounds: int, ttl: int, seed: int, ps: List[float],
                theta: float) -> PSweepResult:
    """Sweep cross-link density p at the natural one-folder-per-member partition,
    reading the passive gap at each p; at the first p with gap > theta, also run
    the active broker and record its tax (spec §3). Each p uses its own vault
    subdir so runs do not collide."""
    points: List[PSweepPoint] = []
    shoulder_p = None
    broker_routes = None
    broker_coord_cost = None
    for i, p in enumerate(ps):
        dest = dest_root / f"p{i}"
        manifest = generate_vault(dest, seed=seed, folders=folders,
                                  notes_per_folder=notes, cross_folder_link_prob=p,
                                  journal_len=journal)
        fed, _tax = run_fed_traced(dest, manifest, rounds=rounds, ttl=ttl)
        cov = fed.coverage if fed.coverage is not None else 1.0
        gap = 1.0 - cov
        points.append(PSweepPoint(p=p, gap=gap, coverage=cov,
                                  coordinator_cost=fed.cost.coordinator_cost))
        if shoulder_p is None and gap > theta:
            shoulder_p = p
            broker = run_fed_broker(dest, manifest, rounds=rounds, ttl=ttl)
            broker_routes = broker.routes
            broker_coord_cost = broker.cost.coordinator_cost
    return PSweepResult(points=points, shoulder_p=shoulder_p,
                        broker_routes=broker_routes,
                        broker_coord_cost=broker_coord_cost)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_west_experiment.py -v -k p_sweep`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/west_experiment.py tests/test_west_experiment.py
git commit -m "west-e2b: p-sweep + the first broker exercise (shoulder at gap > theta)"
```

---

## Task 5: The quality arm

**Files:**
- Modify: `src/west_experiment.py`
- Test: `tests/test_west_experiment.py`

**Interfaces:**
- Consumes: `run_sweepb_point` (Task 3).
- Produces:
  - `west_experiment.QualityArmResult` — dataclass `n: int`, `round_robin_cost: int`, `link_aware_cost: int`, `round_robin_cut: int`, `link_aware_cut: int`, `material: bool`.
  - `west_experiment.run_quality_arm(root, manifest, *, n: int, rounds: int, ttl: int, tol: float, arm: str = "naive") -> QualityArmResult`.

**Context (spec §4).** At fixed `n`, compare round-robin vs link-aware bucketing on the *same corpus*. `material` = link-aware total cost is at least `tol` (=10%) below round-robin's. Uses the naive-arm cost by default (Arm N is where coordination — and thus partition quality — bites; the coherence/cut cost rides in the scan tax). Both points come from `run_sweepb_point` with the two bucketings.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_west_experiment.py`:

```python
def test_run_quality_arm_reports_both_bucketings(tmp_path):
    from west_experiment import run_quality_arm
    manifest = _bucket_vault(tmp_path, folders=6, notes=4, p=0.6)
    r = run_quality_arm(tmp_path, manifest, n=2, rounds=24, ttl=120, tol=0.10)
    assert r.n == 2
    assert r.link_aware_cut <= r.round_robin_cut       # link-aware cuts no more
    assert r.round_robin_cost > 0 and r.link_aware_cost > 0
    assert isinstance(r.material, bool)


def test_run_quality_arm_material_flag_follows_the_tol_threshold(tmp_path):
    from west_experiment import run_quality_arm
    manifest = _bucket_vault(tmp_path, folders=6, notes=4, p=0.6)
    r = run_quality_arm(tmp_path, manifest, n=2, rounds=24, ttl=120, tol=0.10)
    expected = r.link_aware_cost <= r.round_robin_cost * (1 - 0.10)
    assert r.material == expected
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_west_experiment.py -v -k quality_arm`
Expected: FAIL — `ImportError: cannot import name 'run_quality_arm' from 'west_experiment'`

- [ ] **Step 3: Implement**

```python
@dataclass
class QualityArmResult:
    """The partition-quality arm (spec §4): round-robin vs link-aware bucketing
    at fixed n on the same corpus. ``material`` = link-aware cost is at least tol
    below round-robin (partition quality has teeth)."""
    n: int
    round_robin_cost: int
    link_aware_cost: int
    round_robin_cut: int
    link_aware_cut: int
    material: bool


def run_quality_arm(root: Path, manifest, *, n: int, rounds: int, ttl: int,
                    tol: float, arm: str = "naive") -> QualityArmResult:
    """Compare round-robin vs link-aware bucketing at fixed ``n`` on the same
    corpus (spec §4). ``arm`` selects which cost total to compare ('naive' —
    the default, where coordination and thus partition quality bite — or
    'incremental')."""
    attr = "fed_cost_naive" if arm == "naive" else "fed_cost_incremental"
    rr = run_sweepb_point(root, manifest, n=n, rounds=rounds, ttl=ttl,
                          bucketing="round_robin")
    la = run_sweepb_point(root, manifest, n=n, rounds=rounds, ttl=ttl,
                          bucketing="link_aware")
    rr_cost = getattr(rr, attr)
    la_cost = getattr(la, attr)
    return QualityArmResult(
        n=n, round_robin_cost=rr_cost, link_aware_cost=la_cost,
        round_robin_cut=rr.cut_links, link_aware_cut=la.cut_links,
        material=(la_cost <= rr_cost * (1 - tol)),
    )
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_west_experiment.py -v -k quality_arm`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/west_experiment.py tests/test_west_experiment.py
git commit -m "west-e2b: quality arm — round-robin vs link-aware at fixed n"
```

---

## Task 6: The E2b report and priors PB1–PB5

**Files:**
- Modify: `src/west_experiment.py`
- Test: `tests/test_west_experiment.py`

**Interfaces:**
- Consumes: `SweepBPoint` (Task 3), `read_ucurve` (Task 3), `PSweepResult` (Task 4), `QualityArmResult` (Task 5).
- Produces: `west_experiment.E2bReport` (fields `ucurve_naive: UCurveReading`, `ucurve_incremental: UCurveReading`, `shoulder_p: Optional[float]`, `quality: QualityArmResult`, `priors: Dict[str, str]`) and `west_experiment.assemble_e2b_report(sweepb_points, p_result, quality, *, tol) -> E2bReport`.

**Context (spec §6).** Verdict rules, exactly:

- **PB1** `held` iff the **naive** U-curve has an interior minimum (`ucurve_naive.interior`), else `refuted`.
- **PB2** `held` iff the **incremental** U-curve is monotone non-increasing (`ucurve_incremental.monotone_nonincreasing`) **and not** interior, else `refuted`.
- **PB3** `held` iff `p_result.shoulder_p is not None`, else `refuted`.
- **PB4** — *conditional on PB3*: if PB3 refuted → `"undetermined"`; else `held` iff `quality.material`, else `refuted`.
- **PB5** `held` iff every Sweep-B point's folder-member CV < 0.5 **and** the mean per-folder-member cost's max/min across points < 1.25, else `refuted`.

`read_ucurve` is imported from `west_measure`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_west_experiment.py`:

```python
def _sbpoint(n, cn, ci, cv=0.02, mean=1000.0):
    from west_experiment import SweepBPoint
    from west_measure import MemberCostReading
    return SweepBPoint(
        n=n, fed_cost_naive=cn, fed_cost_incremental=ci,
        member_reading=MemberCostReading([int(mean)] * max(n, 1), 120, mean, cv),
        m_fed=100, k2_fed=1.0, k3_fed=0.0, gap=0.0, cut_links=0)


def _presult(shoulder):
    from west_experiment import PSweepResult
    return PSweepResult(points=[], shoulder_p=shoulder,
                        broker_routes=(0 if shoulder is not None else None),
                        broker_coord_cost=(0 if shoulder is not None else None))


def _quality(material):
    from west_experiment import QualityArmResult
    return QualityArmResult(n=4, round_robin_cost=1000,
                            link_aware_cost=(800 if material else 990),
                            round_robin_cut=10, link_aware_cut=2, material=material)


NS = [1, 2, 3, 4, 6, 12]


def test_pb1_held_on_interior_naive_minimum():
    from west_experiment import assemble_e2b_report
    # naive U with min at n=4; incremental monotone down.
    naive = {1: 1000, 2: 600, 3: 450, 4: 400, 6: 700, 12: 1500}
    incr = {1: 900, 2: 500, 3: 350, 4: 300, 6: 250, 12: 200}
    pts = [_sbpoint(n, naive[n], incr[n]) for n in NS]
    rep = assemble_e2b_report(pts, _presult(0.45), _quality(True), tol=0.10)
    assert rep.priors["PB1"] == "held"
    assert rep.priors["PB2"] == "held"


def test_pb1_refuted_when_naive_minimum_is_at_an_endpoint():
    from west_experiment import assemble_e2b_report
    naive = {n: 100 * n for n in NS}                    # monotone up -> min at n=1
    pts = [_sbpoint(n, naive[n], naive[n]) for n in NS]
    rep = assemble_e2b_report(pts, _presult(0.45), _quality(True), tol=0.10)
    assert rep.priors["PB1"] == "refuted"


def test_pb2_refuted_when_incremental_has_an_interior_dip():
    from west_experiment import assemble_e2b_report
    naive = {n: 100 * n for n in NS}
    incr = {1: 500, 2: 400, 3: 300, 4: 200, 6: 350, 12: 600}   # interior min at 4
    pts = [_sbpoint(n, naive[n], incr[n]) for n in NS]
    rep = assemble_e2b_report(pts, _presult(0.45), _quality(True), tol=0.10)
    assert rep.priors["PB2"] == "refuted"


def test_pb3_and_pb4_held_with_a_shoulder():
    from west_experiment import assemble_e2b_report
    pts = [_sbpoint(n, 100, 100) for n in NS]
    rep = assemble_e2b_report(pts, _presult(0.60), _quality(True), tol=0.10)
    assert rep.priors["PB3"] == "held" and rep.priors["PB4"] == "held"


def test_pb4_undetermined_when_no_shoulder():
    from west_experiment import assemble_e2b_report
    pts = [_sbpoint(n, 100, 100) for n in NS]
    rep = assemble_e2b_report(pts, _presult(None), _quality(False), tol=0.10)
    assert rep.priors["PB3"] == "refuted"
    assert rep.priors["PB4"] == "undetermined"          # conditional on PB3


def test_pb4_refuted_when_shoulder_but_quality_immaterial():
    from west_experiment import assemble_e2b_report
    pts = [_sbpoint(n, 100, 100) for n in NS]
    rep = assemble_e2b_report(pts, _presult(0.60), _quality(False), tol=0.10)
    assert rep.priors["PB4"] == "refuted"


def test_pb5_refuted_when_member_cost_drifts_across_n():
    from west_experiment import assemble_e2b_report
    pts = [_sbpoint(n, 100, 100, mean=1000.0 * n) for n in NS]   # 12x drift
    rep = assemble_e2b_report(pts, _presult(0.45), _quality(True), tol=0.10)
    assert rep.priors["PB5"] == "refuted"


def test_pb5_held_when_member_cost_is_flat():
    from west_experiment import assemble_e2b_report
    pts = [_sbpoint(n, 100, 100, cv=0.02, mean=1000.0) for n in NS]
    rep = assemble_e2b_report(pts, _presult(0.45), _quality(True), tol=0.10)
    assert rep.priors["PB5"] == "held"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_west_experiment.py -v -k "pb1 or pb2 or pb3 or pb4 or pb5"`
Expected: FAIL — `ImportError: cannot import name 'assemble_e2b_report' from 'west_experiment'`

- [ ] **Step 3: Implement**

Extend the `from west_measure import ...` line to add `read_ucurve`, `UCurveReading`. Then add:

```python
PB5_MAX_CV = 0.5
PB5_MAX_MEAN_RATIO = 1.25


@dataclass
class E2bReport:
    """The assembled calibration result and the pre-registered verdicts PB1-PB5
    (spec §6). PB4 is conditional on PB3."""
    ucurve_naive: UCurveReading
    ucurve_incremental: UCurveReading
    shoulder_p: Optional[float]
    quality: "QualityArmResult"
    priors: Dict[str, str]


def assemble_e2b_report(sweepb_points, p_result, quality, *, tol: float) -> E2bReport:
    """Decide PB1-PB5 from the three parts' readings (spec §6)."""
    un = read_ucurve(sweepb_points, "naive")
    ui = read_ucurve(sweepb_points, "incremental")

    # PB1 — E3's target exists: the naive U-curve has an interior minimum.
    pb1 = "held" if un.interior else "refuted"
    # PB2 — control: the incremental curve is monotone non-increasing (no interior min).
    pb2 = "held" if (ui.monotone_nonincreasing and not ui.interior) else "refuted"
    # PB3 — a coherence shoulder exists.
    pb3 = "held" if p_result.shoulder_p is not None else "refuted"
    # PB4 — partition quality has teeth, CONDITIONAL on PB3.
    if pb3 == "refuted":
        pb4 = "undetermined"
    else:
        pb4 = "held" if quality.material else "refuted"
    # PB5 — terminal-unit invariance persists across the n sweep.
    means = [p.member_reading.mean for p in sweepb_points if p.member_reading.mean > 0]
    tight = all(p.member_reading.cv < PB5_MAX_CV for p in sweepb_points)
    flat = bool(means) and (max(means) / min(means) < PB5_MAX_MEAN_RATIO)
    pb5 = "held" if (tight and flat) else "refuted"

    return E2bReport(ucurve_naive=un, ucurve_incremental=ui,
                     shoulder_p=p_result.shoulder_p, quality=quality,
                     priors={"PB1": pb1, "PB2": pb2, "PB3": pb3,
                             "PB4": pb4, "PB5": pb5})
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_west_experiment.py -v -k "pb1 or pb2 or pb3 or pb4 or pb5"`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/west_experiment.py tests/test_west_experiment.py
git commit -m "west-e2b: assemble_e2b_report — PB1-PB5 verdicts (PB4 conditional on PB3)"
```

---

## Task 7: The E2b driver

**Files:**
- Create: `tools/run_west_e2b.py`
- Create: `tests/test_west_e2b_driver.py`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: `run_sweepb_point`, `run_p_sweep`, `run_quality_arm`, `assemble_e2b_report` (Tasks 3–6); `generate_vault` (existing).
- Produces: `tools/run_west_e2b.py` with `SEED`, `F0`, `SWEEP_N`, `R_FIXED`, `P_LIST`, `THETA`, `build_config()`, and `main()`.

**Context.** Mirrors `tools/run_west_e2.py` — numbers-only stdout, a determinism canary, argparse knobs. Runs the three parts in order (Sweep-B over `N ∈ {1,2,3,4,6,12}`, the p-sweep, the quality arm at the shoulder p), prints PB1–PB5, and a canary (Part-1 `N=4` twice). Flush per line so a long run is observable.

**Custody:** stdout is numbers only. Never print a note id, title, path, or **folder name**. Cut-link counts, bucket sizes, N, p, costs are numbers and fine.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_west_e2b_driver.py`:

```python
"""Driver contract for the E2b calibration (numbers-only custody + the grid)."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DRIVER = ROOT / "tools" / "run_west_e2b.py"

sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))


def test_driver_exists():
    assert DRIVER.exists()


def test_grid_matches_the_pre_registered_spec():
    import run_west_e2b
    assert run_west_e2b.SEED == 20260721
    assert run_west_e2b.F0 == 12
    assert run_west_e2b.SWEEP_N == [1, 2, 3, 4, 6, 12]
    assert run_west_e2b.R_FIXED == 325
    assert run_west_e2b.P_LIST == [0.15, 0.30, 0.45, 0.60, 0.75]
    assert run_west_e2b.THETA == 0.20


def test_build_config_is_pure_and_deterministic():
    import run_west_e2b
    assert run_west_e2b.build_config() == run_west_e2b.build_config()


def test_driver_runs_a_tiny_sweep_numbers_only(tmp_path):
    out = subprocess.run(
        [sys.executable, str(DRIVER), "--dest", str(tmp_path), "--smoke",
         "--no-canary"],
        capture_output=True, text=True, timeout=1200, cwd=str(ROOT),
    )
    assert out.returncode == 0, out.stderr
    text = out.stdout
    assert "priors:" in text
    assert "PB1" in text and "PB4" in text
    # Custody: no path, note id, .md filename, or folder name may reach stdout.
    assert ".md" not in text
    assert str(tmp_path) not in text
    assert "note-" not in text
    assert "Folder-" not in text


def test_driver_reports_ucurve_and_shoulder(tmp_path):
    out = subprocess.run(
        [sys.executable, str(DRIVER), "--dest", str(tmp_path), "--smoke",
         "--no-canary"],
        capture_output=True, text=True, timeout=1200, cwd=str(ROOT),
    )
    assert "argmin_n" in out.stdout
    assert "shoulder" in out.stdout
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_west_e2b_driver.py -v`
Expected: FAIL — `assert DRIVER.exists()` fails; imports raise `ModuleNotFoundError: run_west_e2b`.

- [ ] **Step 3: Implement**

Create `tools/run_west_e2b.py`:

```python
"""West-in-kytē E2b driver — the calibration: the Sweep-B cost U-curve, the
p-sweep coherence shoulder + the first broker exercise, the partition-quality
arm, and the PB1-PB5 verdicts.

Numbers-only stdout (custody-safe): no note id, title, path, or folder name is
ever printed. Spec: docs/superpowers/specs/2026-07-22-west-in-kyte-e2b-design.md"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from vault_generator import generate_vault
from west_experiment import (run_sweepb_point, run_p_sweep, run_quality_arm,
                             assemble_e2b_report)

# Pre-registered E2b knobs (spec §2-§4 — fixed).
SEED = 20260721
F0 = 12
N_NOTES = 40
P_BASE = 0.15
JOURNAL = 40
TTL = 120
R_FIXED = 325
SWEEP_N = [1, 2, 3, 4, 6, 12]
P_SWEEP_F = 6
P_SWEEP_R = 175
P_LIST = [0.15, 0.30, 0.45, 0.60, 0.75]
THETA = 0.20
TOL = 0.10
QUALITY_N = 4
CANARY_N = 4

# Smoke — for the driver contract test only, never a real run.
SMOKE_N = [1, 2, 4]
SMOKE_NOTES = 3
SMOKE_JOURNAL = 3
SMOKE_R = 12


def build_config():
    """The pre-registered config as a dict (spec §2-§4). Pure."""
    return {"seed": SEED, "F0": F0, "sweep_n": list(SWEEP_N), "R": R_FIXED,
            "p_list": list(P_LIST), "theta": THETA, "quality_n": QUALITY_N}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", default=None)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--no-canary", action="store_true")
    args = ap.parse_args()

    import tempfile
    dest_root = Path(args.dest) if args.dest else Path(tempfile.mkdtemp(prefix="west_e2b_"))
    dest_root.mkdir(parents=True, exist_ok=True)

    if args.smoke:
        sweep_n, notes, journal, rfix = SMOKE_N, SMOKE_NOTES, SMOKE_JOURNAL, SMOKE_R
        p_list, psweep_f, psweep_r, quality_n = [0.15, 0.6], 4, SMOKE_R, 2
        mode = "smoke"
    else:
        sweep_n, notes, journal, rfix = SWEEP_N, N_NOTES, JOURNAL, R_FIXED
        p_list, psweep_f, psweep_r, quality_n = P_LIST, P_SWEEP_F, P_SWEEP_R, QUALITY_N
        mode = "full"

    print("=== West-in-kytē E2b — the calibration (numbers only) ===", flush=True)
    print(f"mode={mode} seed={SEED} F0={F0} n={notes} p_base={P_BASE} J={journal} "
          f"ttl={TTL} R={rfix} theta={THETA} tol={TOL}", flush=True)

    # Part 1 — Sweep-B (fixed corpus, vary N, round-robin, both arms).
    sb_dest = dest_root / "sweepb"
    manifest = generate_vault(sb_dest, seed=SEED, folders=F0, notes_per_folder=notes,
                              cross_folder_link_prob=P_BASE, journal_len=journal)
    sweepb = []
    for n in sweep_n:
        t0 = time.time()
        pt = run_sweepb_point(sb_dest, manifest, n=n, rounds=rfix, ttl=TTL)
        sweepb.append(pt)
        print(f"sweepb N={n} fed_naive={pt.fed_cost_naive} "
              f"fed_incr={pt.fed_cost_incremental} cut={pt.cut_links} "
              f"cv={round(pt.member_reading.cv, 4)} "
              f"mean_member={round(pt.member_reading.mean, 1)} "
              f"|M|fed={pt.m_fed} K2={pt.k2_fed} K3={round(pt.k3_fed, 4)} "
              f"gap={round(pt.gap, 4)} wall_s={round(time.time() - t0, 1)}",
              flush=True)

    # Part 2 — the p-sweep + the first broker exercise.
    ps = run_p_sweep(dest_root / "psweep", folders=psweep_f, notes=notes,
                     journal=journal, rounds=psweep_r, ttl=TTL, seed=SEED,
                     ps=p_list, theta=THETA)
    for pt in ps.points:
        print(f"psweep p={pt.p} gap={round(pt.gap, 4)} "
              f"coverage={round(pt.coverage, 4)} coord={pt.coordinator_cost}",
              flush=True)
    print(f"shoulder_p={ps.shoulder_p} broker_routes={ps.broker_routes} "
          f"broker_coord={ps.broker_coord_cost}", flush=True)

    # Part 3 — the quality arm, at the shoulder p (else 0.75, flagged).
    q_p = ps.shoulder_p if ps.shoulder_p is not None else p_list[-1]
    q_flag = "at-shoulder" if ps.shoulder_p is not None else "coherence-force-weak(p=max)"
    q_dest = dest_root / "quality"
    q_manifest = generate_vault(q_dest, seed=SEED, folders=F0, notes_per_folder=notes,
                                cross_folder_link_prob=q_p, journal_len=journal)
    quality = run_quality_arm(q_dest, q_manifest, n=quality_n, rounds=rfix, ttl=TTL,
                              tol=TOL)
    print(f"quality N={quality_n} p={q_p} ({q_flag}) "
          f"round_robin_cost={quality.round_robin_cost} "
          f"link_aware_cost={quality.link_aware_cost} "
          f"round_robin_cut={quality.round_robin_cut} "
          f"link_aware_cut={quality.link_aware_cut} material={quality.material}",
          flush=True)

    rep = assemble_e2b_report(sweepb, ps, quality, tol=TOL)
    print(f"ucurve_naive argmin_n={rep.ucurve_naive.argmin_n} "
          f"interior={rep.ucurve_naive.interior}", flush=True)
    print(f"ucurve_incr argmin_n={rep.ucurve_incremental.argmin_n} "
          f"monotone={rep.ucurve_incremental.monotone_nonincreasing} "
          f"interior={rep.ucurve_incremental.interior}", flush=True)
    print(f"priors: {rep.priors}", flush=True)

    canary = "skipped"
    if not args.no_canary:
        a = run_sweepb_point(sb_dest, manifest, n=CANARY_N if not args.smoke else 2,
                             rounds=rfix, ttl=TTL)
        b = run_sweepb_point(sb_dest, manifest, n=CANARY_N if not args.smoke else 2,
                             rounds=rfix, ttl=TTL)
        canary = "PASS" if (a.fed_cost_naive == b.fed_cost_naive
                            and a.fed_cost_incremental == b.fed_cost_incremental) else "FAIL"
    print(f"determinism_canary: {canary}", flush=True)

    print("notes: E2b CHARACTERIZES E3's fitness landscape; it does NOT test "
          "convergence (that is E3). PB1 = the naive-arm Sweep-B U-curve has an "
          "INTERIOR cost minimum (1 < argmin_n < 12) — E3's target exists; PB2 "
          "(control) = the incremental-arm curve is monotone non-increasing (no "
          "interior min), so the optimum is a COORDINATION effect not a "
          "materialization one. PB3 = a coherence shoulder (gap > theta) exists "
          "in the p-sweep, forcing the broker (its first exercise; broker cost "
          "is an END-OF-RUN SNAPSHOT, A3-style, NOT replay-exact — a lower "
          "bound, disclosed). PB4 (partition quality has teeth: link-aware "
          "cheaper than round-robin at equal N) is CONDITIONAL on PB3 — "
          "'undetermined' if no shoulder exists (the force it tests is absent), "
          "never refuted. PB5 = terminal-unit invariance persists across the N "
          "sweep. The partition unit is the FOLDER, not the note (spec §1). N=1 "
          "shares R with the journal member, so it is the content-monolith at "
          "constant total effort, NOT E2's dedicated-R mono. The Arm-N "
          "interleaving assumption (concurrent members) carries over from E2 "
          "and is verdict-bearing for every naive-arm reading. Synthetic "
          "corpus, one seed: these are the generator's curves, not real "
          "reasoning corpora. K1 = N/A (raise-only). K3 printed per point "
          "(expected 0.0, checkable not asserted).", flush=True)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Add the runs-directory custody rule**

The E2 rule `runs/west_e2*` (with the `!runs/WEST_E2_LOG.md` negation) **already matches** `runs/west_e2b_*` directories (prefix). But add the tracked-log negation for E2b. Run:

```bash
grep -n "west_e2" .gitignore
```

Append after the existing E2 negation line:

```
# ...and the E2b run log too (same case-insensitive-glob reasoning).
!runs/WEST_E2B_LOG.md
```

Then verify: `git check-ignore -v runs/west_e2b_probe/x.md` reports the rule, and `git check-ignore runs/WEST_E2B_LOG.md` reports it is **not** ignored (create/remove the probe path as needed).

- [ ] **Step 5: Run the driver contract tests**

Run: `uv run pytest tests/test_west_e2b_driver.py -v`
Expected: PASS — all five, including the numbers-only custody assertions (`Folder-` absent).

- [ ] **Step 6: Run the full suite (the E1/E2-reproducibility guard)**

Run: `uv run pytest tests/ -q`
Expected: **0 failed.** The baseline before this plan was 4013 passed / 0 failed; the count rises by the tests added here. Any *failure* in a pre-existing test means an E2b addition changed E1/E2 behaviour — stop and fix rather than proceeding.

- [ ] **Step 7: Verify the E1 and E2 drivers still run unchanged**

Run: `uv run python tools/run_west_e1.py --folders 2 --notes 6 --rounds 15`
Expected: the E1 report prints with `determinism_canary: PASS`.
Run: `uv run python tools/run_west_e2.py --smoke --no-canary --dest /tmp/e2smoke`
Expected: the E2 smoke report prints its `priors:` line. E1/E2 entry points must be untouched.

- [ ] **Step 8: Commit**

```bash
git add tools/run_west_e2b.py tests/test_west_e2b_driver.py .gitignore
git commit -m "west-e2b: numbers-only calibration driver (Sweep-B + p-sweep + quality arm) + canary"
```

---

## After the plan

The build is complete when Task 7's full-suite step reports 0 failed. **Do not launch the production calibration run as part of the build** — that is a separate, author-initiated run (est. ~1.5–2h; only N=1 is expensive) whose findings go to `runs/WEST_E2B_LOG.md` against PB1–PB5, following the E1/E2 precedent. E3 gets its own brainstorm→spec cycle afterward, shaped by these curves.

---

## Self-Review

**Spec coverage.** §1 folder-partition constraint → Task 1 (bucketings) + Task 2 (`run_fed_bucketed` coverage keying). §2 Sweep-B grid + N=1 disclosure → Tasks 3, 7. §3 p-sweep + broker snapshot → Task 4. §4 quality arm (round-robin vs link-aware, cut-count) → Tasks 1, 5. §5 measurements (arm totals, U-curve reading, shoulder reading, quality reading) → Tasks 3, 6. §6 priors PB1–PB5 + PB4-conditional-on-PB3 → Task 6. §7 canary → Task 7. §8 honesty ledger → Task 7's disclosure note. §9 build surface → the File Structure table. §10 decisions → the grid constants. **No gap found.**

**Placeholder scan.** No TBD/TODO; every code step carries complete code; no "similar to Task N".

**Type consistency.** `run_fed_bucketed` returns `(ArrangementResult, CoordinatorTax)` — consumed as a 2-tuple in Tasks 3. `SweepBPoint` fields (`n`, `fed_cost_naive`, `fed_cost_incremental`, `member_reading`, `m_fed`, `k2_fed`, `k3_fed`, `gap`, `cut_links`) are used identically in Tasks 3, 5, 6, 7. `UCurveReading` fields (`argmin_n`, `argmin_cost`, `interior`, `monotone_nonincreasing`, `costs_by_n`) identically in Tasks 3, 6, 7. `PSweepResult` (`points`, `shoulder_p`, `broker_routes`, `broker_coord_cost`) identically in Tasks 4, 6, 7. `QualityArmResult` (`n`, `round_robin_cost`, `link_aware_cost`, `round_robin_cut`, `link_aware_cut`, `material`) identically in Tasks 5, 6, 7. `read_ucurve(points, which)` signature consistent between Task 3 (definition) and Task 6 (use). Bucketings are `List[frozenset]` throughout.
