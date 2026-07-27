# West-in-kytē E3b — the basin map (run log)

> **Spec:** `docs/superpowers/specs/2026-07-24-west-in-kyte-e3b-design.md` (priors PM1–PM4
> pre-registered before any code). **Build:** merged `55288ea` (6 tasks, subagent-driven,
> spec-approved). **Run:** `tools/run_west_e3b.py --mode full`, started 2026-07-24 ~21:45,
> finished 2026-07-25 21:10 local — wall 83,788.7 s (~23.3 h), numbers-only output
> `runs/west_e3b_full.txt`. Deterministic; **canary PASS** (mid-start re-run with cleared memo,
> byte-identical). Discovered undisposed and logged 2026-07-26 (the run completed silently
> during the AlternativeSet sittings).
>
> Run facts: seed=20260721, F0=12, R=325, ttl=120, θ=0.2, merge_k=3, comp_parts=(3,4),
> comp_cap=12 → **36 structured starts** on one shared MemoEvaluator (358 hits / 394 misses).

## The map, in one paragraph

Every one of the 36 structured starts — the monolith, all round-robin granularities N=1..12, and
24 contiguous 3-/4-part compositions — **terminates at exactly N=3**. Convergence to the interior
*granularity* is total across the map, a stronger form of E3's PE1 than two walks could show. But
the terminal *bucketings* fragment into **19 distinct local optima** (PM4's ≤5 sparsity prior
refuted), all genuinely terminal (`shadowed=False` on every one — the full neighbourhood offers no
improving move; the shortlist hid nothing). The 19 optima organize into **two cost bands**: a
**cheap family** — 11 distinct 10/1/1-shaped bucketings spanning 101,411–102,826 (a 1.4% band
sitting on E3's W2 floor) that captures **27/36 starts (75% of the attractor mass)** — and a
**dear fringe** — 8 optima across 7 size-shapes (3/8/1 ×3, 8/3/1, 8/1/3, 6/5/1, 7/1/4, 4/4/4)
spanning 118,865–137,129, fed by 9 starts. The cheapest optimum found is **101,411 = E3's W2
terminus exactly** (PM3: no cheaper basin was left on the table).

## Priors → verdicts

| Prior | Claim (pre-registered) | Observed | Verdict |
|-------|------------------------|----------|---------|
| **PM1** (multi-basin) | ≥2 distinct Arm-N N=3 optima | **19** distinct N=3 optima | **held** |
| **PM2** (direction predicts basin) | every merge-direction start (N>3) converging at N=3 lands strictly cheaper than the monolith start's terminus (119,935) | all N>3 starts land 101,411–118,865 < 119,935 (tightest: round-robin 3/3/3/3 → 3/8/1 @ 118,865, a 0.9% margin) | **held** |
| **PM3** (no cheaper basin hides) | cheapest optimum ≥ 101,411 (E3's W2) | cheapest = **101,411** (reached from N=12 and the near-finest 2/1×11 start) | **held** |
| **PM4** (few-basin, ≤5 optima) | ≤5 distinct optima across all starts | **19** | **refuted** — the pre-registration's own words: "the landscape is more fragmented than PE2's two-basin reading suggested (itself a strong result)" |

## Findings

1. **Granularity converges absolutely; bucketing fragments; cost concentrates.** The three-level
   answer to "how many viable commens": at the granularity level, **one** (N=3, from every start);
   at the exact-bucketing level, **nineteen**; at the cost level, **effectively one family plus a
   stranded fringe** (75% of starts reach within 1.4% of the floor; 25% strand 17–35% dear). The
   E3 PE2 "granularity, not a unique partition" reading survives and sharpens: even the winning
   10/1/1 *shape* is not one optimum but eleven, cost-indistinguishable in practice.
2. **Balance strands; asymmetry funnels.** The perfectly balanced round-robin 4/4/4 — E2b's
   measured trough, the "optimal" partition of the calibration — is itself a **terminal local
   optimum 35% dearer than the floor** (137,129 vs 101,411): the walk cannot leave it, and its
   near-balanced neighbours (3/3/3/3, 6/6) merge into the dear 3/8/1 family rather than the cheap
   one. Meanwhile every strongly asymmetric or fine start funnels to the 10/1/1 family (one
   dominant bucket + two singletons). Mechanism sketch (interpretive, not verdict-bearing): the
   link-guided merge shortlist gives a dominant bucket an accretion gradient; balanced
   configurations offer steepest descent no symmetry-breaking single move. **E2b's U-curve trough
   was a stranded optimum** — the calibration's round-robin constraint hid the cheaper asymmetric
   basins E3b exposes.
3. **The dear fringe is start-shape-predictable.** Stranded starts are exactly: the monolith and
   its split descendants (→ 3/8/1 family), the balanced/near-balanced starts, and the 3-part
   compositions whose second part is large (8/3/1, 7/4/1→6/5/1, 6/5/1, 8/1/3, 7/1/4). Every
   4-part composition and every start of N≥5 reaches the cheap family. Direction selects (PM2),
   but the finer selector is **how much symmetry the start carries**.
4. **Driver mislabel (honesty item):** the printed `arm_i_control` line in fact ran
   `arm="naive"` (Arm N) from the finest partition — it duplicates the `start=12` row
   (10/1/1 @ ~101k), and is NOT an Arm-I run. The Arm-I monotone-to-finest control fact rests on
   E3's PE3, unrechecked here. Cosmetic driver fix optional; the map's verdicts don't lean on it.

## Honesty ledger (what E3b does NOT establish)

- **Reachable structure only, under one discipline.** The 19 optima are what *this* walk
  (full-slate steepest descent, top-3 link-guided merge shortlist) reaches from *this* start set;
  `shadowed=False` certifies terminality, not exhaustiveness of the optimum census.
- **One seed, one synthetic topology** (`seed=20260721`); the two-band structure and the
  balance-strands finding are the generator's until a real corpus corroborates.
- **The Arm-N interleaving assumption carries over** (~26% on E2's reference case), verdict-bearing
  for every cost in the map.
- **The composition start set is capped** (12 per part-count, pre-registered) — the N=3/N=4 shape
  space is sampled, not enumerated.
- **A meta-Agon is not a community** (THE_COMMENS binds hardest here): E3b maps one instance's
  partition landscape. "Many viable commens" is an *analogy carried by the map*, not a constituted
  plurality of communities.

## Disposition (author, 2026-07-26)

**PM1 ACCEPTED held. PM2 ACCEPTED held. PM3 ACCEPTED held. PM4 ACCEPTED refuted — and the
refutation is adopted as the finding, per the pre-registration's own words** ("more fragmented
than the two-basin reading… itself a strong result"). The three-level reading (Finding 1) is
adopted as E3b's headline: **granularity converges absolutely (one N), bucketing fragments
(nineteen optima), cost concentrates (one dominant family + a stranded fringe)** — the empirical
input the commens-rung examination was waiting for. Finding 2's re-reading of E2b (the
round-robin trough was itself a stranded optimum) is accepted; Finding 2's mechanism sketch
(balance strands / asymmetry funnels) is **commissioned for a direct test as rider E3c**
(symmetry-breaking: pre-registered as §11 of the E3b design spec, same discipline — prior before
run). The arm_i_control mislabel (Finding 4) is noted; cosmetic, no re-run required, the Arm-I
fact rests on E3's PE3.

## Next

Mechanically: **PM1, PM2, PM3 held; PM4 refuted.** The map answers PE2's question on its own
terms: the landscape has many reachable optima, direction-and-symmetry select among them, nothing
cheaper than E3's W2 was hiding, and the fragmentation exceeds the two-basin reading by an order
of magnitude — while cost, the currency that matters, concentrates in one family.

Candidates surfaced by this run:
- **The commens rung proper, now with its empirical input in hand** — the standing queued-threads
  examination (Graeber-Wengrow no-teleology, fractal-vs-heterarchy, veil/uptake/substrate/
  normativity, ethics-negotiated, free-will/predestination) can read Finding 1's three-level
  answer directly: many viable exact organizations, one dominant cost family, and *which* one you
  inhabit selected by history (start + direction), not by optimality.
- **A symmetry-breaking rider (E3c, cheap):** does a minimal perturbation of the stranded 4/4/4
  (one folder moved) escape to the cheap family? Would pin Finding 2's mechanism sketch with one
  or two walks rather than a new sweep.
- **The cost-model-where-quality-pays candidate** (E3's PE5 null) stands unchanged, orthogonal to
  this map.
