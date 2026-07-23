# West-in-kytē E2b — the calibration (design spec, pre-registered)

> **Status:** design spec, committed *before* any E2b code. The Pⁿ/Fⁿ discipline: the priors in §6
> (PB1–PB5) are committed here, in advance, each with a pre-committed refutation.
>
> **Predecessors.** E1 result `runs/WEST_E1_LOG.md` · E2 design
> `docs/superpowers/specs/2026-07-22-west-in-kyte-e2-design.md` · E2 result `runs/WEST_E2_LOG.md` ·
> program-level design-of-record `docs/WEST_IN_KYTE_PROGRAM.md`.
>
> **Companions.** `docs/THE_KYTOS.md` §4 (the quantitative frontier) · `docs/THE_COMMENS_AND_THE_COMMUNITY.md`
> (why the community rung is a change in kind).

---

## 0 · What this is, in plain terms

E2 fitted the scaling *exponents* by growing the corpus with the partition (Sweep-A). It found
apportionment's advantage is a scaling property (β_mono 1.28 > β_fed(I) 1.02), that coordination is
the binding constraint under a naive coordinator (an observed crossover at F=12, a 25× cost spread
from scan discipline alone), and that E1's retention surprise is a decay artifact. It left two
things unmeasured that the **next rung, E3 (endogenous partition), depends on**:

1. **E3's actual fitness landscape.** E3 optimizes partitions of *one fixed corpus* — the **Sweep-B**
   U-curve (fixed corpus, vary partition granularity), which E2 never traced. Whether E3's target
   (a non-trivial interior optimum) even *exists* depends on the coordinator model, and that is a
   fixed-corpus question E2's growing-corpus exponents cannot answer.
2. **Whether partition *quality* has teeth.** E2 ran at `p=0.15` with `gap=0` throughout — the passive
   registry resolved every cross-folder reference and the broker never fired. So the **coherence
   force** — the only cost term that distinguishes a *good* partition (few cut links) from a *bad*
   one of the same granularity — was absent. Without it, self-partitioning could optimize granularity
   (a scalar E2 already reads by hand) but never partition structure (E3's actual question).

E2b measures both, cheaply, so E3 can be pre-registered against grounded curves rather than guesses.
**E2b characterizes E3's landscape; it does not test convergence** — that is E3.

**What this is not.** E2b builds no meta-Agon, tests no self-partitioning, uses no real vault, and —
per `docs/THE_COMMENS_AND_THE_COMMUNITY.md` — *models* a federation without constituting a community.

---

## 1 · The load-bearing constraint: the partition unit is the folder

`VaultFeed(folders=…)` scopes a member kytos to a set of **top-level folders**, and
`vault_generator`'s cross-links are folder→folder. So a "partition" here is a **bucketing of folders**:
each bucket is one member (its `folders=` set), and E3 (later) proposes folder re-bucketings
(merge/split). This is a real limit — E3 optimizes folder-bucketings, not arbitrary note-sets — and
it is disclosed on every result. It is also a gift: the cross-link structure is already
folder-granular, so partition quality (cross-*bucket* links) is directly measurable with the existing
`Coordinator.coverage` / `gap` machinery, at bucket granularity, with no new corpus model.

A **bucketing** of `F₀` folders into `N` buckets assigns each folder to one bucket; the members are
the `N` buckets plus the journal-member (adaptation A2, as in E1/E2). `N=1` (all folders in one
bucket, one M) is the monolith-equivalent — so the U-curve's left endpoint *is* the monolith, and no
separate big-MONO run is needed anywhere in E2b.

---

## 2 · Part 1 — Sweep-B: the fixed-corpus cost U-curve

**The question.** On one fixed corpus, how does total federation cost vary with partition granularity
N, and does an *interior* optimum exist?

**Config (pre-registered, fixed).** `seed=20260721`, `F₀=12` folders, `n=40` notes/folder (480 notes),
`p=0.15`, `J=40`, `ttl=120`, `θ=0.20`, `tol=0.10`. **Fixed total `R=325`**, apportioned round-robin
across the `N+1` members (`west_experiment._apportion`) — this holds *total doubt-cycles constant*
while granularity varies, the honest fixed-corpus setup (contrast E2's proportional-R, which grew R
with the corpus). Granularity `N ∈ {1, 2, 3, 4, 6, 12}` (the divisors of 12, so round-robin bucketing
is balanced). Both coordinator arms (Arm N naive, Arm I incremental) at every N.

**Bucketing (Part 1).** Round-robin: folder `k` → bucket `k mod N`. Balanced by construction for
every N in the grid (12 is divisible by each). Deterministic.

**The N=1 endpoint (disclosed).** N=1 is *one content bucket (all 12 folders) + the journal-member*
sharing the fixed R=325 (`_apportion(325, 2)` ≈ 163/162), **not** E2's `run_mono` (which folds the
journal into a single M with 325 dedicated rounds). The journal-member is a constant addend (~120)
at *every* N, so the U-curve's **shape** — the interior-vs-endpoint reading PB1/PB2 turn on — is
unaffected by it; but the absolute N=1 cost is at shared-325-rounds and is **not** directly
comparable to E2's F=12 MONO. The U-curve's left endpoint is the *content-monolith at constant total
effort*, which is the right reference for a fixed-corpus sweep.

**Reported per N:** total FED cost under each arm (materialisation + peel + coordinator tax), the
cost split, per-member costs + folder-member CV (P B5), |M|Σ, K2, K3, gap, conflicts, wall-clock.

**Expected shapes (the priors' basis).** Total materialisation *falls* with N (each member's M is a
smaller slice of the fixed corpus; the monolith at N=1 pays the super-linear single-M cost E2
measured). The Arm-N scan tax *rises* with N (cubic in bucket count — E2's γ=3). Their sum is a
**U-curve with an interior minimum under Arm N** (PB1). Under Arm I the scan tax is ~free (O(H²) once
per run), so the sum is **monotonic non-increasing in N** — no interior minimum (PB2). The contrast is
the point: the optimum is a *coordination* effect, not a materialisation one.

---

## 3 · Part 2 — the p-sweep: the coherence shoulder

**The question.** At what cross-link density does the passive registry break (`gap > θ`), forcing the
broker, and what does the broker then cost?

**Config (pre-registered, fixed).** The natural one-folder-per-member partition at `F=6`, `n=40`,
`R=175`, `J=40`, `ttl=120`, `θ=0.20`, `seed=20260721` — the E2 F=6 anchor. Sweep
`p ∈ {0.15, 0.30, 0.45, 0.60, 0.75}` (`cross_folder_link_prob`). Passive registry at every p.

**The mechanism (disclosed).** `gap = 1 − coverage`, where coverage is the fraction of cross-folder
links whose target note-id surfaced in the target member's M. A member with bounded rounds does not
surface every note, so **more cross-links (higher p) probe that incomplete self-surfacing and raise
gap** — the shoulder is genuine but couples p to the rounds/notes budget (held fixed here so p alone
moves). Reported per p: gap, coverage, coordinator cost, per-member cost.

**The broker exercise.** At the *first* p where `gap > θ`, additionally run `run_fed_broker` and
report its routing tax (`routes` + the added coordinator cost) — the **first real exercise of the
broker path** (built for E1, never fired). Broker cost is an **end-of-run snapshot** (A3-style,
**not** replay-exact — disclosed, as E2 disclosed A3), so it is a lower bound reported honestly, not a
per-round replay.

---

## 4 · Part 3 — the quality arm: does partition structure have teeth?

**The question.** At fixed granularity and a coherence-active p, does *which* folders share a bucket
change the cost?

**Config (pre-registered, fixed).** `F₀=12`, `N=4`, `R=325`, `ttl=120`, `seed=20260721`, and a p **at
or above the Part-2 shoulder** (so the coherence force is live). If Part 2 finds a shoulder at `p*`,
use `p*`; if Part 2 finds no shoulder in range (PB3 refuted), use the top of the range `p=0.75` and
report the arm as *coherence-force-weak*. Two bucketings of the 12 folders into 4 buckets, both arms:

- **round-robin** (quality-blind baseline): folder `k` → bucket `k mod 4`.
- **link-aware** (quality-seeking): a deterministic greedy grouping that minimises cross-*bucket*
  links, read from `manifest.cross_links` (agglomerate the most heavily-linked folder pairs into the
  same bucket first, capacity `F₀/N = 3` folders per bucket, ties broken by folder index).

**Reported:** total cost, coordinator/coherence cost, and cut-link count for each bucketing at equal N.
If link-aware costs materially less (PB4), partition quality has teeth and E3's quality search is
grounded.

---

## 5 · Measurements

**Primary (deterministic), unchanged from E2 §4:** `COST = Σ_rounds (materialiser atoms + peel
visits)` + the coordinator tax, reported per arm. Coordinator tax uses the same per-round replay as
E2 (`replay_coordinator_tax`) for the **passive** arms (exact, read-only); the **broker** tax (Part 2
only) is the end-of-run snapshot, flagged not-replay-exact.

**The U-curve reading (Part 1).** For each arm, report the cost at every N and the **argmin N\*** with
its cost. "Interior optimum" means `1 < N* < 12` (a strict interior point). A monotone series (argmin
at an endpoint) is reported as *no interior optimum* — that is PB1's refutation for Arm N and PB2's
confirmation for Arm I.

**The shoulder reading (Part 2).** The smallest swept p with `gap > θ`, or "none-in-range" if every p
holds `gap ≤ θ`.

**The quality reading (Part 3).** `round_robin_cost − link_aware_cost` at equal N, and the cut-link
counts. "Material" = link-aware total cost at least `tol`=10% below round-robin.

**K1 = N/A** (raise-only membrane, A1). K2 parity within `tol`; K3 printed per config (expected 0.0,
checkable not asserted — the E2 review's finding). **Wall-clock is secondary, never verdict-bearing.**

---

## 6 · Pre-registered priors (PB1–PB5 — committed before any run)

- **PB1 (E3's target exists).** The Sweep-B total-cost U-curve under **Arm N** has an **interior
  minimum** `1 < N* < 12`. *Refuted if the Arm-N series is monotone in N* (argmin at an endpoint) —
  then E3 has no non-trivial convergence target under the naive coordinator.
- **PB2 (control — the optimum is coordination, not materialisation).** Under **Arm I** the same
  series is **monotone non-increasing** in N (no interior minimum). *Refuted if Arm I shows an
  interior minimum* — which would mean materialisation alone produces the optimum and the two-arm
  story is wrong.
- **PB3 (the coherence force is reachable).** There is a `p* ∈ (0.15, 0.75]` at which passive
  `gap > θ=0.20`, forcing the broker. *Refuted if `gap ≤ θ` across the whole p-range* — then the
  passive registry never breaks at this corpus scale and E3 must run coarser or at higher p (a
  reported finding, and Part 3 falls back to `p=0.75` flagged coherence-force-weak).
- **PB4 (partition quality has teeth), conditional on PB3.** At `N=4` and a coherence-active p,
  **link-aware** bucketing's total cost is at least `tol`=10% below **round-robin's**. *Refuted if the
  difference is < tol* — then partition structure does not affect cost in this harness and E3's
  quality search is moot. **But PB4 is meaningful only if PB3 held:** if no coherence-active p exists
  (PB3 refuted), the force PB4 tests is absent, so PB4 is reported **undetermined** (run at `p=0.75`,
  flagged coherence-force-weak), never refuted — a null difference there is PB3's consequence, not
  evidence about partition quality.
- **PB5 (terminal-unit invariance persists — sanity).** Folder-member cost stays flat across the
  Sweep-B N range: per-N folder-member CV < 0.5, and mean per-folder-member cost max/min across N
  < 1.25. *Refuted if it drifts* — which would undercut the E2 P2² result under re-bucketing.

**Stated in advance (as in E2):** E2b measures a *landscape*, not a *trajectory*. Nothing here tests
whether a meta-Agon converges to N\* or discovers the link-aware bucketing — that is E3, and its priors
will be pre-registered against these measured curves, not before them.

---

## 7 · Determinism canary

One config (Part 1 at `N=4`) is run twice end-to-end; total cost under both arms must match exactly.
Reported PASS/FAIL. The full sweep is not double-run (wall-clock; disclosed, as E2).

---

## 8 · Honesty ledger — what E2b does NOT establish

- **Folder-granular partition.** The partition unit is the folder, not the note (§1). E2b (and E3)
  optimise folder-bucketings; a note-granular partition is a different, unbuilt question.
- **No convergence test.** E2b characterises E3's fitness landscape. Whether self-partitioning
  *reaches* N\* or the link-aware bucketing is E3, unbuilt here.
- **Broker cost is a snapshot.** Part 2's broker tax is an end-of-run lower bound (A3-style), not the
  per-round replay the passive arms get — the broker feeds routes back to members, so it is not
  replay-exact (E2 §3.1). Flagged on the result.
- **Synthetic, one seed, one topology.** All parts share `seed=20260721`; the U-curve, the shoulder,
  and the quality gap are the generator's, not real reasoning corpora. A real-vault corroboration is
  deferred.
- **The interleaving assumption carries over.** Arm N models members as concurrent while the harness
  runs them sequentially (~26% on a reference case, E2 §8) — verdict-bearing for every Arm-N reading
  here too.
- **The community rung is modelled, never constituted** (THE_COMMENS). E2b's coordinator is a
  switchboard; E3's meta-Agon will *model* partition negotiation inside one instance, not enact a
  society.

---

## 9 · Build surface (informational — for the implementation plan)

E2b is chiefly a **driver plus a bucketing helper and a curve reader**, reusing the E2 harness.

- `src/west_experiment.py` — a bucketing-aware FED runner: generalise `run_fed_traced` /
  `run_e2_config` from "one folder per member" to "one **bucket** (a folder-set) per member" (the
  round-robin and link-aware bucketings both produce a `List[frozenset]` of folder-sets); the journal
  member and both arms are unchanged. Keep the E2 entry points behaviourally frozen.
- `src/west_measure.py` — the U-curve reader (argmin N\* + interior-vs-endpoint), the shoulder reader,
  and the quality-gap reader; plus the deterministic bucketing functions (round-robin, greedy
  link-aware min-cut over `manifest.cross_links`).
- `tools/run_west_e2b.py` — the numbers-only driver: Part 1 (Sweep-B, both arms), Part 2 (p-sweep +
  the first broker exercise), Part 3 (the quality arm), the PB1–PB5 verdicts, the determinism canary.
  **Numbers-only stdout** (custody: never a note id/title/path/folder name — folder *counts* and
  bucket *sizes* are numbers and fine; a folder *name* is not). Output under `runs/west_e2b*`
  (gitignored; the tracked run log is `runs/WEST_E2B_LOG.md`, spared as `WEST_E2_LOG.md` is).
- Tests mirror E2's per-module files.

Zero protected-core modification is anticipated. Any need for one halts the build for authorization.

---

## 10 · Decisions (ruled by the author, 2026-07-22)

1. **Decompose: E2b now, E3 shaped by E2b's data.** E2b is its own pre-registered spec → plan → build
   → run; E3 gets its own brainstorm→spec cycle afterward, with these curves in hand (mirrors E1→E2).
2. **Include the Part-3 link-aware quality arm** — demonstrate partition quality has teeth before
   building the meta-Agon, rather than leaving E3's premise untested.
3. **Fixed corpus `F₀=12`, fixed `R=325`, `N ∈ {1,2,3,4,6,12}`; p-sweep at the F=6 anchor.**
