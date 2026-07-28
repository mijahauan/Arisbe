# Scaling economics of bounded reasoning units: a methods note

> **What this is.** A self-contained, ~two-page account of the "E-series"
> experiments (E1–E3c, July 2026) for readers outside the project — written so
> that a physicist can evaluate the design without learning the project's
> vocabulary. The full program is [WEST_IN_KYTE_PROGRAM.md](WEST_IN_KYTE_PROGRAM.md);
> the run logs, with pre-registered priors and verbatim verdicts, are
> `runs/WEST_E1_LOG.md` … `runs/WEST_E3C_LOG.md`.
>
> *Written 2026-07-27 (Sitting B2), assistant-drafted from the run logs.*

---

## 1 · The question

Geoffrey West's *Scale* asks whether aggregated systems obey discoverable
scaling laws — cost exponents, interior optima, an invariant terminal unit.
The E-series asks that question of systems whose metabolism is **knowledge
maintenance** rather than energy: does one large reasoner over a corpus, and
a federation of small reasoners over its parts, differ in lawful, measurable
ways? All headline claims below were **pre-registered as priors before each
run executed**; refuted priors are kept on the record beside the held ones.

## 2 · The unit, operationally

The experimental unit (the project calls it a *kytos*; nothing below depends
on the name) is a bounded inference loop that can be reimplemented from this
paragraph:

- **State.** A revisable set *M* of ground facts (metadata atoms about a
  document corpus). |M| = the number of resident atoms. The machinery also
  supports Horn-style rules; in this series the corpus carried facts only, so
  the rule apparatus was present but inert.
- **One round.** (i) ingest whatever the feed delivers this round; (ii)
  *materialize* — forward-chain M to closure (with no rules this is a
  full-state maintenance pass, and it dominates cost); (iii) *probe/test* —
  evaluate standing queries against M; (iv) *decay* — every atom carries a
  disuse clock, and an atom not re-used within `ttl` rounds is dropped. Decay
  is the load-bearing bound: it keeps |M| sized to the *engaged* slice of the
  corpus, and one attention budget stretched over a large corpus decays out
  more than several bounded budgets do.
- **Determinism.** One fixed seed (20260721) is the sole randomness source;
  every run carries a byte-determinism canary (a re-run of a designated cell
  must reproduce identical output — it passed on every experiment).

**Two arrangements are compared.** *Monolith* (MONO): one unit whose M
ingests the whole corpus. *Federation* (FED): one unit per corpus folder,
each bounded to its folder, plus a journal-member unit (so FED covers exactly
the corpus MONO covers — work parity) and a **coordinator** that reconciles
cross-folder references. The coordinator is a switchboard, not a society; no
claim about real communities is made (§6).

**The workload** is a synthetic note-vault: *F* folders × 40 notes, plus 40
journal notes, with cross-folder links at density *p* = 0.15 (e.g. 47
cross-links at F = 6; 88 at F = 12), generated deterministically from the
seed.

## 3 · The cost meter

Cost is a **deterministic count of atom-operations** performed by the
materialization step (an instrumented counter, not wall-clock, not tokens;
wall-clock is logged but never verdict-bearing). It decomposes into:
`mat` (forward-chaining work — in the monolith ~99% of total), `peel`
(probe/test work — small and near-identical across arrangements), and
`coord` (the coordinator's reconciliation scans — federation only).

The coordinator was run under **two disciplines**, and the distinction turned
out to carry most of the phenomenon: *incremental* (Arm I — scan only what
changed each round) versus *naive* (Arm N — rescan the whole digest each
round, an O(H²) tax in the number of buckets H).

**Quality parity.** The corpus feed only raises claims; it never adversarially
refutes, so predictive track record is not measurable here (declared N/A, not
smuggled). Parity between arrangements is instead judged on **durability**:
same `ttl`, same number of rounds, work-parity coverage — and the durability
score then *measured* equal (1.0 vs 1.0) rather than assumed. Cost
comparisons are therefore same-quality comparisons.

## 4 · The experiments and what they found

| Exp | Design | Headline result |
|---|---|---|
| **E1** | MONO vs FED, F = 6, 300 rounds, ttl = 120 | FED **~5.2× cheaper** (36,097 vs 188,039 ops) at equal durability, and retained more (Σ|M| 1,367 across members vs 752) — the monolith's single attention budget decays out most of its working set. All four priors held. |
| **E2** | Size sweep F ∈ {2…16}, rounds ∝ F+1; fit cost ∝ F^β | **β_mono = 1.277** (r² 0.997) vs **β_fed = 1.025** (incremental coordinator). Naive coordinator: β = 2.45, tax ∝ F³; the *same federation* at F = 16 costs 51,371 (incremental) vs 1,308,587 (naive) — a **25× spread from scan discipline alone**. Per-member cost invariant to max/min = 1.0012 across the 8× range (West's invariant terminal unit, observed). Prior P1²'s magnitude bar (β_mono > 1.3) was missed — held as *separation-only*. |
| **E2b** | Imposed partitions, F₀ = 12, fixed total effort, bucket count N ∈ {1…12} | Naive-coordination cost is a U-curve with an **interior optimum N\* = 3** (137,129; 16% below the monolith bucket, 4.2× below finest-possible). Control: with incremental coordination the curve is monotone — the optimum belongs to coordination, not to inference. A link-density prior (PB3) was **refuted**: coherence never broke via density; it broke via decay saturation at N = 1. |
| **E3** | Endogenous repartition: split/merge moves adjudicated on measured cost, four walks from different starts | Every walk converged to **the same granularity (N = 3) but different partitions** — "the optimum is a granularity, not a partition." Basin agreement prior PE2 **refuted** (final costs differ by 18%): the landscape is multi-basin and direction-dependent. |
| **E3b** | Basin map: 36 structured starts | All 36 → N = 3; **19 distinct local optima**. A cheap asymmetric family (11 optima shaped ~10/1/1) captures **27/36 starts (75% of attractor mass) within 1.4% of the cost floor** (101,411–102,826); a dear fringe of 8 optima sits 17–35% above floor. The perfectly balanced 4/4/4 partition — E2b's own imposed-sweep optimum — is itself **stranded** at 137,129: *balance strands; asymmetry funnels*. Few-basin prior PM4 (≤5 optima) **refuted**. |
| **E3c** | Symmetry-breaking rider: three pre-registered single-folder perturbations of the stranded 4/4/4 | Knife-edge prior PS1 **refuted**: only 1 of 3 perturbations escaped to the cheap family; the other two descended to *new* dear optima (known optima 19 → 21). Stranding is a **positive-measure dear basin**, not a knife-edge. Floor prior PS2 held (nothing landed below 101,411). |

**Summary shape.** Federation avoids a real diseconomy (β 1.28 → 1.02), the
avoidance lives almost entirely in coordinator scan discipline, the
self-organized optimum is an interior *granularity* over a fragmented
multi-basin landscape, and the balanced partition is measurably dear and
hard to escape by small perturbations.

## 5 · What this does *not* claim

- **No economy of scale.** Both arrangements are super-linear; a federation
  of independent units is linear-plus-coordination *by construction*. E2
  establishes a diseconomy avoided and the crossover where naive coordination
  stops avoiding it — not West's sublinear β < 1.
- **One landscape.** All numbers are exponents and basins *of the generator's
  topology*: one synthetic corpus family, one seed, one link density, one
  decay model. A real-corpus corroboration is deferred and named as such.
- **A summary slope.** β_mono = 1.277 fits well (r² 0.997) but the log-log
  curve bends where decay saturates |M|; it is a summary slope, not a clean
  power law.
- **Modeled concurrency.** The naive-coordinator tax models members exporting
  concurrently within a synchronized round; the harness executes them
  sequentially. This assumption is verdict-bearing for every naive-arm
  result and is flagged in each log.
- **No social arrow.** The exponents characterize one imposed fitness
  landscape within one level of organization — never a developmental ladder.
  And a simulated federation is not a community: the units share one process
  and one clock, so the series measures the *economics of association*, not
  association itself.

## 6 · Replicability

Everything is deterministic given the seed: identical grids re-run
byte-identically (canary PASS on every experiment); independently-built
drivers reproduce each other's shared cells exactly (E2b's N = 12 point
equals E2's F = 12 row to the atom); the endogenous walks keep JSONL move
ledgers that replay clean, so a doctored verdict would be caught. The
conjecture offered back to the scaling program — that the allocation layer of
such units is vectorial (a multi-component knowledge measure) rather than
scalar, so the right object may be a scaling *manifold* whose frozen-landscape
shadow is the observed exponent — is stated as a conjecture with its deciding
measurement invited, in the program document.
