# Partition economics in a bounded-maintenance harness: an internal methods record

> **What this is.** An internal record of the "E-series" experiments (E1–E3c,
> July 2026): what the harness measured, what the design got wrong, and what a
> corrected test would require. An earlier version of this note served as the
> methods appendix to a letter to Geoffrey West. A code-level audit on
> 2026-07-28 found a design error that voids the letter's central comparison,
> the author held the letter, and this note now records the experiment rather
> than defends it.
>
> Written so a reader outside the project can follow it without the project's
> vocabulary. Program document: [WEST_IN_KYTE_PROGRAM.md](WEST_IN_KYTE_PROGRAM.md)
> (§8 carries the audit in full). Run logs, with pre-registered priors and
> verbatim verdicts: `runs/WEST_E1_LOG.md` … `runs/WEST_E3C_LOG.md`.
>
> *Drafted 2026-07-27; rewritten 2026-07-28 after the audit.*

---

## 1 · The question we set out to ask

Geoffrey West's *Scale* argues that aggregated living systems obey discoverable
scaling laws — cost exponents, interior optima, and an **invariant terminal
unit** (the capillary stays capillary-sized however large the organism grows).
We asked whether systems whose upkeep consists of **knowledge maintenance**
rather than energy show anything similar: does one large reasoner over a
corpus, and a federation of small reasoners over its parts, differ in lawful,
measurable ways?

Every headline below carried a **pre-registered prior**, recorded before the run
executed. Refuted priors stay on the record beside the held ones, and several of
the sharpest results below are refutations.

## 2 · The design error

The harness never tested the question. Four defects, each verified in code and
two of them by instrumented probe:

1. **Nothing reasoned.** The corpus carried ground metadata and no rules. Every
   round therefore derived zero facts and applied zero rules. The machinery that
   would derive — a forward-chainer and a query evaluator — ran, but had nothing
   to work on, and no part of the loop read the evaluator's verdict. The units
   **stored, re-scanned, and forgot**. They metabolized nothing.
2. **The federation never communicated.** Members ran sequentially, each in full
   isolation, each finishing before the next began. Afterwards the coordinator
   *read* the finished models and copied out their distinct relation **names** —
   at four folders, twenty-two cells: six names crossed with four folders. No
   fact crossed between members, nothing returned to a member, and every caller
   discarded the broker's routing result. The reconciliation scan's loop body
   reads `pass`; from E2 onward the coordinator's cost enters as a closed-form
   replay rather than an executed scan. A switchboard that carries a vocabulary
   census carries no community to scale.
3. **The parity clause carried no weight.** The earlier note claimed the
   federation won "at equal durability," with durability *measured* equal rather
   than assumed. On this harness the durability score can read only 1.0 or
   undefined: the erasures that would lower it require adversarial agents that
   cannot fire on a raise-only feed, and decay-erased items leave the score by
   construction. In probe, 40% of admissions were erased and did not count. A
   false reading was structurally unreachable, so 1.0-against-1.0 asserts
   nothing.
4. **Terminal-unit invariance was imposed, not discovered.** E2 fixed each unit's
   slice at 40 notes and set the round budget to 25·(F+1), so every member
   performed exactly 25 rounds at every size. Each unit therefore held a fixed
   slice and spent a fixed budget across the whole sweep. The measured 1.0012
   max/min spread confirms the harness runs deterministically; it does not
   observe an invariant terminal unit. West's invariance is an empirical
   surprise — the network reorganizes as mass grows, yet the capillaries stay
   the same size. Ours was an assumption reported back.

The run logs stated all of this straight. The overstatement accumulated above
them, in interpretive prose and worst of all in the letter draft.

## 3 · The unit and the two arrangements, operationally

The experimental unit reimplements from this paragraph:

- **State.** A revisable set *M* of ground facts (metadata atoms about a
  document corpus). |M| counts the resident atoms. The machinery also accepts
  Horn-style rules; this corpus carried none, so the rule apparatus sat inert
  throughout.
- **One round.** (i) ingest whatever the feed delivers; (ii) run the
  materialization pass over the whole of *M* — with no rules present this
  traverses the fact set and derives nothing, and it dominates cost; (iii)
  evaluate standing queries against *M*, and discard the verdict; (iv) decay —
  every atom carries a disuse clock, and an atom not re-delivered within `ttl`
  rounds drops out. Decay does the real bounding work: it holds |M| to the
  *engaged* slice of the corpus, and one attention budget stretched over a large
  corpus forgets more than several bounded budgets do.
- **Determinism.** One fixed seed (20260721) supplies all randomness. Every run
  carries a byte-determinism canary — a designated cell re-run must reproduce
  identical output. It passed on every experiment.

**Two arrangements.** *Monolith* (MONO): one unit whose *M* ingests the whole
corpus. *Federation* (FED): one unit per corpus folder, each bounded to its
folder, plus a journal-member so FED covers exactly the corpus MONO covers, plus
a **coordinator** that afterwards reads the finished members and reconciles
cross-folder references by name. Per §2.2, the members never meet.

**The workload:** a synthetic note-vault of *F* folders × 40 notes plus 40
journal notes, with cross-folder links at density *p* = 0.15 (47 cross-links at
F = 6; 88 at F = 12), generated deterministically from the seed.

## 4 · The cost meter, and what it charges

Cost counts atom-operations performed by the materialization step — an
instrumented counter, never wall-clock, never tokens (wall-clock is logged and
never verdict-bearing). It decomposes into `mat` (the materialization pass,
~99% of the monolith's total), `peel` (query evaluation, small and near-identical
across arrangements), and `coord` (the coordinator's reconciliation, federation
only).

**The meter charges the size of the fact set per round, not work done.** A round
pays |M| whether or not anything derives, and a cache hit that does no work
still pays. That fixes the headline arithmetically: a monolith running *R*
rounds against one accumulating *M* pays ≈ c·R²/2, while a federation splitting
those rounds across *F+1* members pays ≈ c·R²/2(F+1). The observed ratios track
the member count — 3.96 against 5 in probe, 5.2 against 7 in E1 — with decay
blunting the quadratic. The "~5.2× cheaper" result reports the member count.

The coordinator ran under **two disciplines**, and that distinction carried most
of the surviving phenomenon: *incremental* (Arm I — account only for what
changed each round) versus *naive* (Arm N — re-account for the whole digest each
round, an O(H²) tax in the number of buckets H).

## 5 · What survives

| Exp | Design | Result that stands |
|---|---|---|
| **E1** | MONO vs FED, F = 6, 300 rounds, ttl = 120 | FED cost 36,097 vs MONO 188,039. The ratio tracks F+1 = 7 under a size-charging meter (§4). FED also **retained more** (Σ\|M\| 1,367 across members vs 752) — the monolith's single attention budget decays out most of its working set. |
| **E2** | Size sweep F ∈ {2…16}, rounds ∝ F+1; fit cost ∝ F^β | **β_mono = 1.277** (r² 0.997) vs **β_fed = 1.025** (incremental coordinator) — the shape of the size-charge under two arrangements. Naive coordinator: β = 2.45, tax ∝ F³; the *same federation* at F = 16 costs 51,371 incremental vs 1,308,587 naive — a **25× spread from scan discipline alone**. Prior P1²'s magnitude bar (β_mono > 1.3) missed; held as separation-only. Per-member invariance (1.0012) does **not** stand — §2.4. |
| **E2b** | Imposed partitions, F₀ = 12, fixed total effort, buckets N ∈ {1…12} | Naive-coordination cost traces a U-curve with an **interior optimum at N\* = 3** (137,129; 16% below the single-bucket cost, 4.2× below finest-possible). Control: under incremental coordination the curve runs monotone — **the optimum belongs to coordination, not to the units**. A link-density prior (PB3) **refuted**: coherence never broke via density; it broke via decay saturation at N = 1. |
| **E3** | Endogenous repartition: split/merge adjudicated on measured cost, four walks from different starts | Every walk converged to **the same granularity (N = 3) but a different partition** — the optimum names a granularity, not a partition. Basin-agreement prior PE2 **refuted** (final costs differ by 18%): the landscape runs multi-basin and direction-dependent. |
| **E3b** | Basin map: 36 structured starts | All 36 → N = 3; **19 distinct local optima**. A cheap asymmetric family (11 optima shaped ~10/1/1) captures **27/36 starts — 75% of attractor mass — within 1.4% of the cost floor** (101,411–102,826); a dear fringe of 8 optima sits 17–35% above floor. The perfectly balanced 4/4/4 partition, which E2b's imposed sweep had named optimal, sits **stranded** at 137,129: *balance strands; asymmetry funnels*. Few-basin prior PM4 (≤5 optima) **refuted**. |
| **E3c** | Symmetry-breaking rider: three pre-registered single-folder perturbations of the stranded 4/4/4 | Knife-edge prior PS1 **refuted**: 1 of 3 perturbations escaped to the cheap family; the other two descended to *new* dear optima (19 known optima → 21). Stranding occupies a **positive-measure dear basin**, not a knife edge. Floor prior PS2 held — nothing landed below 101,411. |

Stated narrowly and honestly: **partitioning a maintenance workload across
bounded units lowers total upkeep under a size-charging meter, and how much
depends overwhelmingly on the coordinator's scan discipline rather than on the
partition.** The partition landscape over that meter has real and unobvious
structure — an interior granularity optimum, many basins, and a dear balanced
point that resists small perturbations. Both claims concern the arithmetic of a
maintenance meter over one synthetic corpus family. Neither concerns reasoning,
and neither concerns terminal units.

## 6 · The mis-mapping (the author's diagnosis)

The deeper fault sits in the comparison itself. **A monolith has no counterpart
as a terminal unit.** In West's framework the terminal unit is the capillary and
the organism is the network that feeds it; the scaling law relates an
organism-level rate to organism size. A monolith does not constitute a larger
organism — it constitutes a single unit made big, the one thing West's networks
never do. Comparing FED to MONO therefore compares an organism to an inflated
cell, and answers no question about terminal units.

If a MONO correlate exists, it lives **at the level of a whole community** — one
community measured against another, plausibly competing for an ecological niche.
That relocation matters twice. It puts the scaling question where West asks it
(how does a *community's* rate scale with its size?), and it supplies the
**selection pressure** his exponents depend on: biological and urban exponents
arise from optimization under constraint, and nothing in these runs selects
between arrangements at all.

It also names what the harness left out. The metabolism of interest consists of
**what the units communicate and jointly maintain as an objective reality
between them**, together with **what each retains, reasons on, and forgets
internally** — the facts, the standing questions, and the deductions,
inductions, abductions, generalizations and specifications that move them. The
E-series exercised the storing and the forgetting. It exercised none of the
reasoning, and none of the *between*.

## 7 · What a corrected test requires

Named so the next attempt starts honest, not so it starts soon. Six conditions,
set out at length in WEST_IN_KYTE_PROGRAM §8:

1. **Communication between units** carrying content, not a vocabulary census —
   otherwise no community exists to scale.
2. **Rules in the corpus**, so units derive rather than only accumulate; a
   non-zero derivation ratio signals that anything gets metabolized at all.
3. **Provenance in the materializer** — the support set behind a derived atom —
   so *use* can mean an atom doing work rather than an atom arriving again.
   Today's disuse clock defines use as re-delivery, and says so in its own
   docstring.
4. **A live durability score**, which needs a feed with world-teeth: some way
   for a standing item to be defeated by something other than the decay clock.
5. **Community-level scaling** — sweep the number of *communicating* units, and
   leave the terminal unit's invariance free to emerge or fail rather than
   pinning it by construction.
6. **Selection between communities**, if the exponents are to mean what they
   mean in *Scale*.

## 8 · Replicability, and one conjecture left untouched

The harness reproduces. Identical grids re-run byte-identically (canary PASS on
every experiment); independently-built drivers reproduce each other's shared
cells exactly (E2b's N = 12 point equals E2's F = 12 row to the atom); the
endogenous walks keep move ledgers that replay clean, so a doctored verdict gets
caught. Determinism and custody hold; the design error sits upstream of them.

The conjecture the program hoped to offer back to the scaling program — that the
allocation layer of such units runs **vectorial** (a multi-component knowledge
measure) rather than scalar, so the right object may be a scaling *manifold*
whose frozen-landscape shadow shows up as the observed exponent — **these runs
leave untouched**. Of the four components of that vector, one went uncomputed
(the predictive track record: declared N/A, since the feed never refutes), and
the other three held constants across every cell — durability pinned at 1.0 by
construction, derivation at 0.0 for want of rules, and use tracking nothing but
the decay clock the design fixed. A vector whose components do not vary cannot
show a manifold. The conjecture stands where it stood before the runs.
