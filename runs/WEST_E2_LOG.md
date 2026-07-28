# WEST-IN-KYTĒ E2 — run log

**What.** The size sweep: the first point at which a West scaling *exponent* is estimable
(E1 gave a paired result at one size — two points cannot fit a power law). Six grid points
`F ∈ {2,4,6,8,12,16}` of monolith (MONO) vs per-folder federation (FED) over one synthetic vault,
fitting `cost ∝ F^β` for MONO and for two federation coordinator cost models, plus a ttl rider
probing E1's FED-retains-more surprise. Answers **Q-C** (terminal-unit invariance) and **Q-B** in
its scaling form.

**Design (pre-registered, before any code).** `docs/superpowers/specs/2026-07-22-west-in-kyte-e2-design.md`.
Harness plan `docs/superpowers/plans/2026-07-22-west-in-kyte-e2.md` (9 TDD tasks, subagent-driven,
fresh implementer + independent review each — the final whole-branch review caught a real P4²
flatness defect + four disclosure gaps, all fixed). Merged to `main` `4c9a07e` before the run; full
suite 4013 passed / 0 failed. Two author rulings mid-build, both in spec §6: **(A)** P3² requires
γ≥2 **and** a crossover; **(B)** P1² is three-valued, `refuted` reserved for the pre-committed
`β_mono ≤ β_fed(I)`.

**Config (pre-registered, fixed).** `seed=20260721, n=40, p=0.15, J=40, ttl=120, θ=0.20, tol=0.10`;
`F ∈ {2,4,6,8,12,16}`, `R = 25·(F+1)` (so every member does exactly 25 rounds at every F); rider
`F=6, ttl ∈ {60,120,240,off}`. Run 2026-07-22 16:32–18:28 (1h56m), deterministic, canary PASS.

---

## Result (2026-07-22, `run_west_e2.py`, deterministic, canary PASS)

| F | R | MONO | FED Arm I (incr) | FED Arm N (naive) | tax β-basis (naive_member) | mean member | \|M\|mono | \|M\|fed |
|---|---|---|---|---|---|---|---|---|
| 2 | 75 | 28,949 | 6,096 | 8,344 | 2,303 | 2955.0 | 502 | 426 |
| 4 | 125 | 76,854 | 12,221 | 31,776 | 19,808 | 2956.2 | 732 | 734 |
| 6 | 175 | 132,584 | 18,454 | 85,486 | 67,593 | 2956.5 | 740 | 1041 |
| 8 | 225 | 188,525 | 24,745 | 181,717 | 157,918 | 2954.4 | 745 | 1345 |
| 12 | 325 | 300,455 | 37,917 | 573,860 | 538,221 | 2954.2 | 748 | 1958 |
| 16 | 425 | 411,595 | 51,371 | 1,308,587 | 1,261,132 | 2952.9 | 741 | 2567 |

```
beta_mono      = 1.2770  (se 0.0346, r2 0.9971, weak=False)
beta_fed_incr  = 1.0246  (se 0.0059, r2 0.9999, weak=False)   ← Arm I
beta_fed_naive = 2.4504  (se 0.1080, r2 0.9923, weak=False)   ← Arm N
beta_tax_naive = 3.0289  (se 0.0144, r2 0.9999, weak=False)
crossover_F = 12.0   crossover_kind = observed
broker_forced = []   tax_clamped_count = 0   gap = 0.0 at every F   conflicts = 0
K1 = N/A (raise-only membrane)   K2 = 1.0 = 1.0 throughout   K3 = 0.0 both (printed, not asserted)
priors: {P1: separation-only, P2: held, P3: held, P4: held}
determinism_canary: PASS
```

The rider (F=6, same corpus as the grid's F=6 point):

| ttl | \|M\|mono | \|M\|fed | ratio FED/MONO |
|---|---|---|---|
| 60 | 431 | 1041 | 2.4153 |
| 120 | 740 | 1041 | 1.4068 |
| 240 | 1127 | 1041 | 0.9237 |
| off | 1127 | 1041 | 0.9237 |

*Free consistency check passed:* the rider's `ttl=120` cell reproduced the grid's F=6
`|M|mono=740, |M|fed=1041` **exactly** — the run is internally deterministic.

## Pre-registered priors — mechanical verdicts

| Prior | Claim | Measured | Verdict |
|---|---|---|---|
| **P1²** (Q-C headline exponent) | β_mono > β_fed(I) **and** β_mono > 1.3 | 1.277 > 1.025 (**separation holds**) but 1.277 < 1.3 (magnitude bar missed by 0.023) | **separation-only** |
| **P2²** (terminal-unit invariance) | folder-member CV < 0.5 at every F **and** mean max/min < 1.25 | CV ≈ 0.002 everywhere; mean max/min = **1.0012** | **held** |
| **P3²** (coordination is the binding constraint) | γ ≥ 2 **and** a crossover exists | β_tax(N) = 3.03 ≥ 2; **observed** in-range crossover at F=12 (FED-naive below MONO at F≤8, above at F≥12) | **held** |
| **P4²** (FED-retains-more is a decay artifact) | FED/MONO \|M\| ratio narrows monotonically as ttl → off | 2.42 → 1.41 → 0.92 → 0.92 (strict net decrease, non-increasing) | **held** |
| **Pre-committed refutation** | β_mono ≤ β_fed(I) refutes the scaling hypothesis | 1.277 > 1.025 — **not triggered** | **not refuted** |

## What E2 establishes

1. **Apportionment's advantage is a scaling property, not a fixed-size artifact (Q-B).** β_mono
   (1.28) > β_fed(I) (1.02): the monolith's cost grows faster than the federation's as the system
   grows, so E1's paired win *survives growth*. The pre-committed refutation (β_mono ≤ β_fed(I)) was
   not triggered. Under the incremental coordinator, FED is ~8× cheaper than MONO at F=16 and the gap
   widens with F.

2. **But the separation is weaker than predicted, and the pre-registration caught it honestly.**
   β_mono came in at 1.28, not the design-probe's ≈1.8, so P1² reads **separation-only** — the
   federation hypothesis holds in its scaling *direction* but misses the 1.3 magnitude bar. **Ruling
   B earned itself on the first run:** had P1² stayed two-valued this would have printed `refuted`
   and read as the hypothesis *failing*, when in truth only a design estimate was too high. *Why
   β_mono is low:* under proportional-R with `ttl=120`, decay caps MONO's working set (|M|mono flat
   at ~745 across the whole sweep), so MONO's per-round materialisation stops climbing once decay
   saturates — it scales gentler than the fixed-R probe suggested.

3. **Coordination is the binding constraint under naive rescanning — an observed crossover (Q-B's
   teeth).** β_tax(N) = 3.03 (the predicted ∝F³), and the naive-coordinator federation's total
   *overtakes the monolith within the swept range* — cheaper at F≤8, dearer at F≥12 (1.9× over at
   F=12, 3.2× at F=16). This is an **observed** crossover (read off pointwise data, not a fitted
   line — it bypasses the weak-fit gate), the strongest evidence class the design produces.

4. **The two-arm ruling paid off decisively.** The *same* federation on the *same* corpus at F=16
   costs **51,371 (Arm I) or 1,308,587 (Arm N)** — a **25× spread** — depending only on whether the
   coordinator rescans from scratch each round or scans incrementally. Choosing one model in advance
   (as spec §3.2 records we were tempted to) would have reported either "federation wins decisively"
   or "federation collapses at modest scale" as a fact about *federation*, when it is a fact about
   the *coordinator's scan discipline*. Whether apportionment pays at scale is not a property of the
   partition — it is a property of how the coordinator is built.

5. **Terminal-unit invariance is emphatic (Q-C).** Per-folder-member cost held to **1.0012 max/min**
   across an 8× range of community size (F=2→16), with per-member CV ≈ 0.002 at every point. E1
   could only foreshadow this on six members of one size; E2 shows it surviving the sweep. This is
   the West economy-of-scale signature at the terminal unit: the per-kytos cost-per-doubt-cycle does
   not drift as the community grows.

6. **E1's FED-retains-more surprise is a decay artifact, not a structural advantage (P4²).** The
   FED/MONO |M| ratio narrows monotonically as decay is relaxed (2.42 → 0.92) and MONO's |M| *passes*
   FED's once decay stops biting (MONO 1127 vs FED's fixed 1041 at ttl≥240). The mechanism is exactly
   the hypothesised one: MONO's single attention budget over R rounds decays more of its working set
   than each folder-bounded member's does. FED's |M| is *ttl-invariant* here (1041 at every ttl) —
   each member's working set is small enough that `ttl=60` never bites — while MONO's is
   decay-limited. So the retention gap is **not** a Q-E vector effect that outlives the scalar
   exponent; it is the decay pressure, and it disappears when decay does.

## Honesty ledger (what E2 does NOT establish)

- **Synthetic, one seed, one topology.** These are exponents of the generator's topology (all six
  points share `seed=20260721`, `p=0.15`), not of real reasoning corpora. A real-vault corroboration
  is deferred. The affine `R = 25·(F+1)` also gives MONO's cost slight curvature at small F (spec
  §2.1); β is the large-F reading.
- **No West sublinear β<1 — as pre-stated.** Both arrangements are super-linear; a federation of
  independent kytē is linear-plus-coordination by construction. E2 establishes **diseconomy
  avoided** (β_mono > β_fed) and **the crossover where it stops being avoided** (Arm N), not an
  economy of scale.
- **Arm N assumes concurrent members.** `replay_coordinator_tax` models members exporting
  concurrently within a synchronized global round; the harness executes them sequentially (~26% apart
  on a reference case). Arm N is the sole basis for γ and the crossover — i.e. all of P3². The
  concurrent (pessimistic) reading is deliberate: a real federation runs its members concurrently.
- **β_mono's curvature.** r²=0.997 is strong but below the fed fits; MONO's decay-saturation means
  its log-log curve bends, so 1.277 is a summary slope, not a clean power law.
- **The p-sweep crossover (where the passive registry breaks) is deferred to E2b** — gap was 0 at
  every F here (broker never needed), so E2 learned nothing about where federation stops being free
  for coherence reasons. The community rung is *modelled*, never constituted (THE_COMMENS).

## Disposition & next (the author's)

Mechanically: **P2², P3², P4² held; P1² separation-only; the scaling hypothesis not refuted.** The
federation reasons at a lower exponent than the monolith (apportionment's advantage is a scaling
property), coordination is the binding constraint under naive rescanning with an observed crossover
at F=12, terminal-unit cost is invariant to three sig-figs, and E1's retention surprise is settled
as a decay artifact. The author dispositions whether to accept.

Candidates surfaced by this run: **E2b** — the p-sweep crossover (force gap > θ, exercise the
broker); a **per-round A3** on the sequential-vs-concurrent question (measure both orderings rather
than modelling one); **E3** — endogenous partition (split/merge as licensed moves in a meta-Agon
over partitions, with these cost/K curves as the disposition evidence). Program frame:
`docs/WEST_IN_KYTE_PROGRAM.md`.

---

## Retrospective correction (2026-07-28) — an error in experimental design

*Appended, not rewritten. The mechanical verdicts stand as recorded; the
**reading** of two of them does not. Full account:
`docs/WEST_IN_KYTE_PROGRAM.md` §8.*

- **Finding 5 ("terminal-unit invariance is emphatic") is withdrawn as a
  finding.** The design fixes `NOTES_PER_FOLDER = 40` and sets `R = 25·(F+1)`
  precisely "so every member performs exactly 25 rounds at every F." Each unit
  therefore holds a fixed slice and spends a fixed budget across the whole
  sweep. Measuring per-member cost invariant at max/min 1.0012 confirms the
  harness runs deterministically; it does not discover an invariance. West's
  invariant terminal unit is an empirical surprise — the network reorganizes as
  mass grows while capillaries stay the same size — whereas P2² imposed the
  invariance and then observed it. The phrase "the West economy-of-scale
  signature at the terminal unit" overstated the result and is retracted.
- **Deeper, the comparison cannot bear on terminal units at all.** A monolith
  has no counterpart as a terminal unit: it is a single unit made big, which
  West's networks never do. A MONO correlate would live at the level of a whole
  community, plausibly competing with another community for an ecological niche
  — which is also where the selection pressure his exponents depend on would
  come from, and these runs contain no selection.
- **β as a summary.** Already conceded in the honesty ledger above (the MONO
  curve bends where decay caps |M|); worth restating beside the corrected
  reading, since cost sums |M| per round and both exponents follow largely from
  that meter's arithmetic — β_fed ≈ 1 because per-member cost stays fixed and
  members add linearly.

**What still stands, and it is the durable finding:** coordination binds.
The 25× spread between coordinator scan disciplines at the largest size, and the
crossover at F=12, say that whether apportionment pays at scale turns on **how
the coordinator gets built** — this log's own words: "not a property of the
partition — it is a property of how the coordinator is built."
