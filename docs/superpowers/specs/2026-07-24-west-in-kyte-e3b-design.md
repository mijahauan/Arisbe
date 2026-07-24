# West-in-kytē E3b — the basin map (design spec, pre-registered)

> **Status:** design spec, committed *before* any E3b code. The Pⁿ/Fⁿ discipline: the priors in §6
> (PM1–PM4) are committed here, in advance, each with a pre-committed refutation.
>
> **Predecessors.** E2b design/result (`.../2026-07-22-west-in-kyte-e2b-design.md`,
> `runs/WEST_E2B_LOG.md`) · E3 design/result (`.../2026-07-23-west-in-kyte-e3-design.md`,
> `runs/WEST_E3_LOG.md`) · program-level `docs/WEST_IN_KYTE_PROGRAM.md`.
>
> **Companions.** `docs/THE_KYTOS.md` §4 · `docs/THE_COMMENS_AND_THE_COMMUNITY.md`.

---

## 0 · What this is, in plain terms

E3 asked whether self-partitioning *converges* to E2b's interior optimum. It found that it does — to
the interior **granularity N=3** — but **PE2 refuted**: the three Arm-N walks reached that granularity
at *different bucketings and costs*, because the landscape has **multiple N=3 basins and the search
direction selects among them** (both merge-direction walks reached 10/1/1 at ~101k; the
split-from-monolith walk was caught in 3/8/1 at ~120k, 18% dearer).

E3b **characterizes that multi-basin structure directly**: how many distinct local optima does the E3
walk discipline reach, what are they, and which start states flow to each? The deliverable is a
**descriptive map** (optima + attractor sets / watersheds), with a few **pre-registered structural
priors** (§6) so prediction stays separable from post-hoc pattern. It answers the question PE2 raised,
on PE2's own terms.

**What this is not.** E3b builds no new adjudication logic, runs no meta-Agon of its own, and tests no
convergence — it *re-uses E3's exact walk* as a black box and maps where it lands from a fixed set of
starts. It is the census E3's single trajectory pair could not be. A meta-Agon is not a community
(THE_COMMENS); this maps one instance's partition landscape, it does not constitute a society.

---

## 1 · Object of interest: Arm N only

The multi-basin structure lives under the **naive coordinator (Arm N)** — that is where E3's interior
optimum and PE2's direction-dependence appeared. Under **Arm I** the walk runs monotonically to the
finest partition (N=12, PE3 held), a trivial single basin; E3b confirms that once as a control and
does not map it. Every "walk", "optimum", "basin", and cost in this spec is Arm-N unless stated.

---

## 2 · What a basin is (the verbatim-E3 definition)

A **local optimum** is a bucketing at which `west_meta_agon.run_meta_walk` (Arm N) halts
`"converged"` — no admissible strictly-improving move in E3's full slate (all legal splits + the
top-3 link-guided merge shortlist, gap-gated). Two starts **share a basin** iff they descend to the
**same** converged bucketing by canonical key (`bucketing_key`). The basin bottom is thus defined by
the *exact discipline that produced PE2* — no re-definition, maximal comparability.

**Disclosed confound + diagnostic (the shortlist).** Because the merge slate is shortlisted (top-3 by
cross-bucket link count — proposer attention, disclosed in E3 §2), a converged bucketing is optimal
*relative to the shortlisted slate*, not necessarily relative to the full neighbourhood. E3b therefore
**reports, per optimum, a `shortlist_shadowed` flag**: whether the optimum's **full** neighbourhood
(every pairwise merge, no shortlist, plus all splits) contains a strict improver in Arm-N cost. This
is a *reported diagnostic*, never an action — the basin definition stays exactly E3's, so the map
describes where the real discipline halts, while the flag honestly surfaces where the shortlist hid a
cheaper merge. A shadowed optimum is still a real basin bottom of the shipped discipline; the flag
tells the reader the landscape has a deeper point the top-3 attention could not see.

---

## 3 · Start states (structured, deterministic — no RNG)

A fixed, reproducible seed set, each run through the Arm-N walk on **one shared `MemoEvaluator`**
(deterministic harness ⇒ every revisited bucketing is free; the low-N evals are computed once and
reused across all starts). No randomness — the map is byte-reproducible and the canary holds.

The set (all on the E3 corpus, folders `Folder-0..Folder-11` in lexicographic `sorted()` order):

1. **The 12 round-robin bucketings** `round_robin_buckets(folders, N)` for `N = 1..12` — the endpoints
   plus E3's baseline granularities.
2. **A deterministic family of contiguous integer-composition partitions** of the 12 sorted folders
   into **3 and into 4 contiguous parts**, one bucketing per composition, folders assigned in sorted
   order to contiguous blocks. The compositions are enumerated deterministically (lexicographic
   descending by part sizes) and **capped** at a fixed count `COMP_CAP=12` per part-count (24 total)
   to bound cost; the cap and the enumeration order are pre-registered here so the set is fixed. These
   are the interior starts probing whether more N=3/N=4 shapes funnel to new basins.
3. **The three E3 walk starts** verbatim: N=1 (`[all 12]`), N=12 (all singletons), the unbalanced
   mid-start `6/3/2/1` (`fs[0:6], fs[6:9], fs[9:11], fs[11:12]`) — for exact continuity with
   `runs/WEST_E3_LOG.md`.

Duplicates across the three sources are collapsed by canonical key (round-robin N=3 `4/4/4` may also
appear as a composition; it is one start). Total ~30–39 distinct starts. Every start is named in the
log by its **sizes** (numbers-only custody: never a folder name).

The map is `{start → converged optimum}` (per-start terminus), inverted to `{optimum → set of starts
that reach it}` (the attractor sets / watersheds).

---

## 4 · Cost instrument & determinism

Unchanged from E3: `run_meta_walk` on a shared `MemoEvaluator` at full `R=325`, Arm-N cost the
adjudication currency, gap-gate at `θ=0.20`, `merge_k=3`, `max_rounds=20`. The full-neighbourhood
diagnostic (§2) re-uses the same `evaluate` (memoized), so it adds only the un-cached full-merge
evaluations of each optimum's neighbours. **Determinism canary:** one structured start (the E3
mid-start) is re-mapped with a **cleared** memo; its terminus, cost, and move sequence must match.
Wall-clock is secondary. Estimated well under E3's ~6h given the memo overlap across the N=3 shell.

---

## 5 · The deliverable — the descriptive map (numbers-only stdout)

- **Optima table:** each distinct converged bucketing — sizes, Arm-N cost, `shortlist_shadowed` flag,
  watershed count (how many structured starts reach it).
- **Per-start terminus:** `start_sizes → optimum_sizes (cost)` for every structured start.
- **Watershed inversion:** `{optimum_sizes → [start_sizes, ...]}` — each basin's attractor set.
- **PM1–PM4 verdicts** (§6).
- **Consistency check:** E3's two known optima (`3/8/1` @119,935 and `10/1/1` @101,411) re-appear
  among the optima (fail loudly if not — the corpus/discipline drifted).
- **Determinism canary** PASS/FAIL; **the honest note block** (synthetic, one seed; the shortlist
  confound; Arm-N interleaving assumption carries; this is the *discipline's* reachable basin
  structure from a *named* start set, not the landscape's optima in the absolute).

---

## 6 · Pre-registered priors (PM1–PM4 — committed before any run)

- **PM1 (multi-basin confirmed).** The structured start set reaches **≥ 2 distinct Arm-N N=3 optima**.
  *Refuted if all starts that converge at N=3 funnel to a single optimum* — then E3's PE2 was a
  two-walk artifact, not landscape structure.
- **PM2 (direction predicts basin — the mechanism claim).** Every **merge-direction** start (a start
  with N > 3) that converges at N=3 reaches a basin **strictly cheaper** than the **split-from-monolith**
  start's terminus (the N=1 start). *Refuted if any merge-direction N=3-converging start lands at a
  cost ≥ the monolith start's terminus cost* — then direction is not the selector. (Starts at N=2 or
  N=3 are neither merge- nor split-from-monolith and carry no PM2 claim.)
- **PM3 (no cheaper basin hides).** The cheapest optimum the map finds is **≥ 101,411** (E3's W2
  basin). *Refuted if some structured start converges below 101,411* — a genuine finding (the E3
  walks left cost on the table); report the new best bucketing.
- **PM4 (few-basin, not rugged).** The total distinct Arm-N optima reached across all starts (all
  granularities, not only N=3) is **≤ 5**. *Refuted if > 5 distinct optima* — the landscape is more
  fragmented than PE2's two-basin reading suggested (itself a strong result).

**Stated in advance:** E3b maps the basins *this discipline reaches from this named start set* — not
the landscape's optima in the absolute (a different discipline, or unshortlisted merges, could reach
others; the `shortlist_shadowed` flag is exactly the honest surface of that gap). PM1–PM4 are claims
about the reachable structure, falsifiable against the map they precede.

---

## 7 · Architecture (small, additive)

Everything re-uses `src/west_meta_agon.py` **unchanged** (byte-frozen, like E2/E2b before E3).

- `src/west_basin_map.py` (new, unprotected):
  - `structured_starts(manifest) -> List[Bucketing]` — the deterministic seed set (§3): round-robin
    N=1..12, the capped contiguous 3- and 4-part compositions, the three E3 starts; deduped by
    canonical key; deterministic order.
  - `contiguous_compositions(folders, parts, cap) -> List[Bucketing]` — the composition family
    (helper, pure, testable in isolation).
  - `map_basins(root, manifest, starts, *, rounds, ttl, theta, merge_k) -> BasinMap` — run each start
    through `run_meta_walk` (Arm N) on one shared `MemoEvaluator`; collect `{start_key → terminus}`;
    invert to watersheds; carry the shared evaluator for the diagnostic.
  - `full_neighbourhood_improver(bucketing, manifest, evaluate, *, theta) -> bool` — the
    `shortlist_shadowed` diagnostic (§2): all pairwise merges (no shortlist) + all splits, is there a
    gap-admissible strict Arm-N improver?
  - `assemble_basin_report(basin_map, *, e3_w1_cost, e3_w2_cost, e3_known_sizes) -> BasinReport` —
    the optima table, watershed inversion, the E3-consistency check, and PM1–PM4 verdicts.
  - dataclasses `BasinMap` (`terminus_by_start`, `watersheds`, shared eval handle) and `BasinReport`
    (`optima` list with sizes/cost/shadowed/watershed_count, `priors`, `consistency_ok`,
    `cheapest_cost`, `distinct_optima`).
- `tools/run_west_e3b.py` (new): numbers-only driver — build corpus (E3 config), structured starts,
  `map_basins`, the diagnostic per optimum, the tables, PM1–PM4, the canary; `--smoke` mode. Output
  under `runs/west_e3b*` (gitignored; tracked log `runs/WEST_E3B_LOG.md`, spared like the others).
- Tests `tests/test_west_basin_map.py` mirroring E3's per-module pattern: deterministic start set
  (exact members + dedup), `contiguous_compositions` shapes + cap, basin grouping by canonical key,
  watershed inversion, the full-neighbourhood diagnostic (killer fixture where the shortlist hides an
  improving merge → `shadowed=True`), and **PM1–PM4 verdict killers per conjunct** (the standing
  West lesson: verdict layers are where mutations survive).

E3/E2/E2b entry points stay **byte-frozen**; zero protected-core change anticipated. Any need for one
halts the build for authorization.

---

## 8 · Honesty ledger — what E3b does NOT establish

- **The discipline's reachable basins from a named start set**, not the landscape's optima in the
  absolute. A different walk discipline, or unshortlisted merges, could reach optima E3b never visits;
  `shortlist_shadowed` is the honest surface of that gap, not its closure.
- **Structured starts, not a random sample** — the watershed *counts* are over the fixed seed set, not
  an unbiased estimate of attractor-set *measure* over the whole (combinatorially huge) partition
  space. "Basin A caught 8 of 30 starts" is a fact about the seed set, not a probability.
- **Synthetic, one seed, one topology** (`seed=20260721`) — the basin structure is the generator's.
- **The Arm-N interleaving assumption carries over** (members concurrent, harness sequential; ~26% on
  E2's reference) — verdict-bearing for every Arm-N cost and thus every PM.
- **No convergence, no community.** E3b is a static census of a landscape, not a dynamic; and the
  commens rung (a change in *kind*) is unbuilt (THE_COMMENS binds hardest there).

---

## 9 · Decisions (ruled by the author, 2026-07-24)

1. **Scope = the N=3 shell + descent basins** — enumerate the optima the walk discipline reaches from
   a structured start set and map their watersheds; do not census the (huge) full N=3 space.
2. **Structured, deterministic starts** — round-robin N=1..12 + capped contiguous 3/4-part
   compositions + the three E3 starts; no RNG.
3. **Optimum = descent terminus** — verbatim E3 walk halts; two starts share a basin iff same
   canonical key; the full-neighbourhood check is a disclosed `shortlist_shadowed` diagnostic, not a
   redefinition.
4. **Pre-register structural priors (PM1–PM4) + emit the descriptive map** — keep the Pⁿ/Fⁿ
   discipline while the map is the deliverable.
