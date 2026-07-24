# WEST-IN-KYTĒ E3 — run log

**What.** Endogenous partition: apportionment made a **licensed, recorded move**. A meta-Agon over
folder-bucketings — split/merge proposals adjudicated by full-slate steepest descent on measured
cost/gap evidence — walked over E2b's fixed corpus to ask **Q-B's second form, made concrete by
E2b's curves**: does self-partitioning *converge* into the measured interior optimum (E2b's Arm-N
trough at N\*=3, 137,129) from both ends of the U-curve and from an unbalanced mid-start, while the
identical machinery under Arm I (the control) runs to the finest partition? A rider (E2b′) tightens
`ttl` to reach the coherence force at N>1 (E2b PB3 showed link density cannot) and gives the broker
and the partition-quality premise (PB4's deferred test) their first real exercise.

**Design (pre-registered, before any code).**
`docs/superpowers/specs/2026-07-23-west-in-kyte-e3-design.md` (priors PE1–PE5 in §6, each with a
pre-committed refutation). Harness-level Agon loop (proposer/panel/JSONL ledger over a plain
partition state; §1 ruling), full-R=325 memoized evaluations, cost + gap-gate fitness with the K
vector recorded never verdict-bearing. 8-task subagent-driven TDD build; the three mutation-prone
layers (walk halt/accept boundaries, rider material/cut-count, PE1–PE5 verdict cost-source/tolerance)
each hardened with bite-verified killer tests after review — the E2/E2b pattern held a third time.
Merged to `main` `bfe9c69` before the run; full suite **4100 passed / 0 failed**; E1/E2/E2b
byte-frozen (the only `west_experiment.py` change is the appended `run_fed_bucketed_broker`).

**Config (pre-registered, fixed).** `seed=20260721, F0=12, n=40/folder, p_base=0.15, J=40, ttl=120,
R=325, θ=0.20, tol=0.10, merge_k=3, max_rounds=20`; rider `ttl ∈ {60,30,15}` at `N ∈ {2,4}`,
quality arm at `N=4`. Run 2026-07-23 17:38–23:27 CDT (**~5h49m**; walks 4h27m, rider ~1h20m),
deterministic, canary PASS. Runner: the assistant, launched via `tools/run_west_e3.py` →
`runs/west_e3_run1/` (numbers-only console: `runs/west_e3_run1_console.txt`; both gitignored).

---

## Result (2026-07-23, `run_west_e3.py`, deterministic, canary PASS)

**The four walks:**

| Walk | Arm | Start | Halt | Final N | Final bucketing (sizes) | Final cost | Rounds | vs E2b trough |
|---|---|---|---|---|---|---|---|---|
| W1 | naive | N=1 (monolith) | converged | **3** | 3/8/1 | **119,935** | 5 | 0.875× |
| W2 | naive | N=12 (singletons) | converged | **3** | 10/1/1 | **101,411** | 10 | 0.739× |
| W3 | naive | N=4 unbalanced 6/3/2/1 | converged | **3** | 10/1/1 | **102,099** | 4 | 0.744× |
| W4 | **incremental** | N=1 (monolith) | converged | **12** | 1×12 (finest) | 37,917 | 12 | — |

W1 path: `split, split, split, merge` (N 1→2→3→4→3). W2 path: nine merges (N 12→3). W3 path:
`merge, split, merge` (N 4→3→4→3). W4 path: eleven splits (N 1→12). All coherent throughout
(gap=0 at every N≥2 under `ttl=120`); K2=1.0, K3=0.0 at every point.

**The rider E2b′ — the coherence regime (fresh vaults, round-robin):**

| N | ttl=60 gap | ttl=30 gap | ttl=15 gap |
|---|---|---|---|
| 2 | 0.6818 | 0.8182 | 0.8977 |
| 4 | **0.4659** | 0.7159 | 0.8750 |

`biting_ttl=60` (the largest ttl with gap > θ at N=4). **Decay reaches the coherence force readily**
— every swept ttl breaches θ at N=4, and even N=2 breaches at all three. The broker fired for the
first time away from the monolith endpoint.

**The rider quality arm (N=4, broker-active, at ttl=60):**

| bucketing | total cost | cut links | routes |
|---|---|---|---|
| round-robin | **145,487** | 71 | 71 |
| link-aware | 146,228 | **64** | 64 |

`material=False` — link-aware cut cross-bucket links 71→64 (−10%) but cost **0.5% more**.

```
priors: {PE1: held, PE2: refuted, PE3: held, PE4: held, PE5: refuted}
determinism_canary: PASS   (W3 re-run with a cleared memo → identical moves/final/cost)
replay W1/W2/W3/W4: ok=True   (every panel disposition recomputed from recorded evidence)
```

## Pre-registered priors — mechanical verdicts

| Prior | Claim | Measured | Verdict |
|---|---|---|---|
| **PE1** (convergence) | W1 **and** W2 halt converged, interior 1<N<12, cost ≤ trough×1.10 (≤150,842) | both interior N=3; W1 119,935, W2 101,411 — both *below* the trough | **held** |
| **PE2** (basin agreement) | the three Arm-N walks' final costs within tol (max/min ≤ 1.10) | 119,935 / 101,411 = **1.183** (W2,W3 agree to 1.007; W1 is the outlier) | **refuted** |
| **PE3** (control — the optimum is the arm's) | W4 (Arm I) halts converged at N=12 | converged, N=12, cost 37,917 (= E2b's F=12 FED Arm-I exactly) | **held** |
| **PE4** (decay reaches coherence at N>1) | some ttl∈{60,30,15} gives gap>θ at N=4 | gap 0.466 at ttl=60 (and larger tighter); biting_ttl=60 | **held** |
| **PE5** (quality has teeth under force), cond. on PE4 | link-aware ≥10% below round-robin at N=4, broker-active | link-aware 0.5% **dearer** despite −10% cut links | **refuted** |

## What E3 establishes

1. **Self-partitioning converges to the interior optimum (PE1).** From both ends of the U-curve the
   licensed split/merge walk halts at an interior N=3 partition at or *below* E2b's measured trough
   (0.88× from the monolith, 0.74× from the singletons). The meta-Agon *finds* the target E2b's
   landscape guaranteed exists — neither endpoint, and cheaper than the round-robin N=3 baseline
   because link-guided merging reaches unbalanced N=3 partitions the balanced baseline never visits.

2. **But it does NOT converge to a *unique* partition — the basin is search-direction-dependent
   (PE2 refuted, the headline finding).** The granularity N=3 is robust across all three Arm-N walks,
   but the *bucketing* and its cost are not: both merge-direction walks (W2 from N=12, W3 from the
   mid-start) settle into the **10/1/1** basin at ~101–102k (agreeing to 0.7%), while the split-direction
   walk (W1 from the monolith) gets caught in a **different 3/8/1** basin at 120k — 18% dearer. Steepest
   descent from the monolith halts in a worse local optimum than the merge walks reach. **The landscape
   has multiple N=3 basins, and which one the walk finds depends on where it starts.** This is not a
   failure — it is the honest structure E2b's single U-curve could not show: "the optimum" is a
   granularity, not a partition.

3. **The interior optimum is the naive coordinator's, confirmed dynamically (PE3, PE4).** Under the
   incremental coordinator the identical walk splits all the way to the finest partition (N=12,
   37,917 — reproducing E2b's F=12 Arm-I value exactly), never settling interior: PE2's E2b lesson
   made a trajectory. And the coherence force that walls off over-splitting is real and reachable —
   tightening ttl to 60 pushes even a 4-bucket federation past θ (gap 0.47), the first coherence
   break in the whole West arc away from the N=1 monolith.

4. **Partition *quality* has no cost teeth in this harness, even under coherence force (PE5 refuted —
   not merely undetermined).** With the broker active, link-aware bucketing did exactly what it is for
   — it cut cross-bucket links 71→64 — yet cost *rose* 0.5%. The mechanism: routing a cross-bucket
   reference costs ~1 unit/link, so link-aware's 7-link saving is negligible, while materialization
   cost dominates and is minimised by **balance**, not link-locality; link-aware's heavily-linked
   groupings make **unbalanced** buckets whose apportioned rounds pile materialization onto the big
   member, outweighing the routing saving. **Balance beats link-locality.** E3's quality-search
   premise — that a meta-Agon should optimise partition *structure*, not just granularity — is
   refuted for this cost model: there is nothing for a quality search to win here.

5. **The gap-gate does real work in the walk — it forbids re-collapse to incoherence.** Every N=2
   round shows `refused=1`: the candidate that merges the two halves back to the N=1 monolith (gap
   0.58 > θ) is refused, while the incumbent N=1 start is itself never gated (so W1/W4 legitimately
   *begin* standing-incoherent and escape on move 1). The coherence gate is not idle scenery — it is
   the wall that keeps the walk from wandering back into the decayed monolith.

6. **The record is earned and re-checkable.** The determinism canary passed (W3 re-run with a cleared
   memo produced an identical move sequence, final bucketing, and cost), and every walk's JSONL ledger
   replays clean — each panel disposition recomputed from the *recorded* evidence, so a doctored
   verdict would be caught. Two E2b values reproduced exactly as free cross-experiment checks: W1/W4's
   N=1 cost (162,907 naive / 160,725 incremental, gap 0.5795) and W4's N=12 Arm-I cost (37,917).

## Honesty ledger (what E3 does NOT establish)

- **Convergence of *one* discipline, not of negotiation in general.** Full-slate steepest descent
  with a top-3 link-guided merge shortlist (proposer attention, disclosed, never adjudication) is
  *a* walk; a different discipline could converge differently. PE2's direction-dependence is itself
  evidence that the discipline, not just the landscape, shapes the outcome.
- **Synthetic, one seed, one topology.** The two N=3 basins, the biting ttl, and the quality null are
  the generator's (`seed=20260721`), not real reasoning corpora. A real-vault corroboration is deferred.
- **The Arm-N interleaving assumption carries over** (members modelled concurrent, harness runs them
  sequentially; ~26% on E2's reference case) — verdict-bearing for PE1, PE2, and every Arm-N
  disposition.
- **The broker tax is an end-of-run snapshot** (A3-style lower bound), not replay-exact — so PE5's
  0.5% margin is within the disclosed coordinator-cost uncertainty; the *direction* (balance beats
  link-locality) is the robust claim, not the exact percentage.
- **No Arisbe-native record.** The move ledger is JSONL, not a UoD chain; lifting the trajectory into
  ink is deferred (the §1 ruling).
- **A meta-Agon is not a community** (THE_COMMENS binds hardest at this rung): E3 *models* partition
  negotiation inside one instance; it does not constitute a society. |M|/K2/K3 recorded, never
  verdict-bearing; K1 = N/A (raise-only).

## Disposition & next (the author's)

Mechanically: **PE1 held, PE3 held, PE4 held; PE2 refuted; PE5 refuted.** Self-partitioning converges
to the interior granularity the naive coordinator rewards, from both directions, at or below the
measured optimum — but not to a unique partition (the basin depends on search direction), and the
partition-*quality* dimension it was built to search has no cost teeth in this harness (balance
dominates link-locality). The author dispositions whether to accept.

Candidates surfaced by this run:
- **The two-basin structure invites a basin map** — enumerate the N=3 local optima and their
  attractor sets, to characterise *how many* viable partitions there are and how direction selects
  among them (the "many viable commens, no unique optimum" reading — cf. the standing open-doubt set
  on the commens rung).
- **A cost model where quality *does* pay** — PE5's null is specific to a cost where routing is cheap
  and balance-driven materialization dominates. A model with expensive cross-bucket coordination (or
  materialization insensitive to balance) would give link-locality teeth; whether that model is more
  faithful is the open question E3's null poses.
- **The commens rung proper** — E3 exhausts what one instance modelling its own partition can show;
  the next change is in *kind* (reciprocal typification, a genuine society), which THE_COMMENS flags
  as un-constitutable inside a single instance. The West program's fractal framing (one anatomy at
  every scale) meets its named skeptical test there.
