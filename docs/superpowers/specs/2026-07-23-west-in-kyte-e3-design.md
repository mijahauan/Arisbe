# West-in-kytē E3 — endogenous partition (design spec, pre-registered)

> **Status:** design spec, committed *before* any E3 code. The Pⁿ/Fⁿ discipline: the priors in §6
> (PE1–PE5) are committed here, in advance, each with a pre-committed refutation.
>
> **Predecessors.** E1 result `runs/WEST_E1_LOG.md` · E2 result `runs/WEST_E2_LOG.md` · E2b design
> `docs/superpowers/specs/2026-07-22-west-in-kyte-e2b-design.md` · E2b result `runs/WEST_E2B_LOG.md`
> · program-level design-of-record `docs/WEST_IN_KYTE_PROGRAM.md` (§6 frames E3).
>
> **Companions.** `docs/THE_KYTOS.md` §4 (the quantitative frontier) ·
> `docs/THE_COMMENS_AND_THE_COMMUNITY.md` (why the community rung is a change in kind).

---

## 0 · What this is, in plain terms

E2b measured E3's fitness landscape on one fixed corpus: the Arm-N cost U-curve over bucketings has
a genuine **interior minimum at N\*=3** (PB1), the interior optimum is a **coordination effect**
(PB2 — under Arm I, finest-is-cheapest), the coherence force **never arrives via link density** at
this scale (PB3 refuted, gap=0 at every p ≤ 0.75) but **does arrive via decay** (the unplanned
finding: gap=0.58 at N=1, 51/88 cross-link targets decayed out of the monolith's M), and partition
*quality* remains **untested, not false** (PB4 undetermined — the force it needs was absent).

E3 makes apportionment itself a **licensed, recorded move**: split/merge of buckets proposed and
adjudicated in a meta-Agon over folder-bucketings, with the measured cost/gap/K evidence as the
disposition currency. It answers **Q-B's second form, made concrete by E2b's curves**: does
self-partitioning *converge* into the measured interior under Arm N — from both ends of the U-curve
and from an unbalanced mid-start — while the identical machinery under Arm I (the control) runs to
the finest partition? A rider (E2b′) finds the regime where coherence bites at N>1 (via ttl, since
link density cannot reach it) and gives the broker and the partition-quality premise (PB4's
deferred test) their first real exercise.

**What this is not.** E3 *models* partition negotiation inside one instance — a meta-Agon is not a
community; reciprocal typification cannot occur in an individual (THE_COMMENS). The honesty flag
binds hardest here, on the rung that most resembles institution-formation. E3 also does not test
any LLM role, any real vault, or note-granular partitions (the unit is the folder, E2b §1).

---

## 1 · Fidelity ruling: a harness-level Agon loop (ruled 2026-07-23)

E3 mirrors `agon_evolution`'s shape — **proposer → evidence → panel → disposition → recorded
round** — over a plain partition-state object. No EGI representation of the partition, no corpus
UoD, no chain steps: the "licensed, recorded move" record is a **replayable JSONL move ledger**
(one per walk) plus the numbers-only run log. Rationale: the partition facts are bookkeeping, not
reasoning content; the Arisbe-native lift (partition-as-M, polarity-gate compliance, a new step
vocabulary) buys no additional science for the convergence question and can be added later from the
ledger if a result warrants it.

---

## 2 · The machinery (`src/west_meta_agon.py`, new, unprotected)

**Corpus.** Identical to E2b Sweep-B: `seed=20260721, F₀=12, n=40, p_base=0.15, J=40`; evaluation
at `ttl=120`, fixed apportioned `R=325`, `θ=0.20`, `tol=0.10`. One generated vault shared by every
walk; E2b's measured trough (137,129 at round-robin N=3) is the pre-registered comparator.

**`Bucketing`** — canonical form of a partition of the 12 folders: sorted tuple of sorted tuples of
folder names; the canonical string is the memo key and the ledger id. Printed only as bucket
*sizes* (numbers-only stdout).

**Moves.**
- `split(bucket)` — deterministic balanced contiguous halves: sort the bucket's folders, first
  ⌈s/2⌉ vs rest. Singletons cannot split.
- `merge(b1, b2)` — union. N=1 cannot merge.

**The slate economy (disclosed).** A full merge slate is C(N,2) — from N=12 that is ~280
evaluations over one walk (~5h/walk; the matrix would exceed 12h). So the proposer's merge slate is
**shortlisted to the top-k=3 bucket-pairs by cross-bucket link count** (read from
`manifest.cross_links`; deterministic canonical tie-break; all pairs if fewer than 3). **All** legal
splits are always tabled (they move toward cheap high-N evaluations). This is *proposer attention*
— a bounded membrane reading a cheap structural signal to shortlist, while the panel adjudicates
only on measured evidence. It is disclosed on every result and is **not** the quality-teeth test
(that is the rider, §5): a link-guided shortlist restricts *which* merges are tabled, never how any
tabled move is judged.

**Evaluator.** `evaluate(bucketing) → MetaEvidence` wrapping the existing E2b bucketed runner
(`run_sweepb_point`-equivalent) at full `R=325`: both arms' costs, gap, coverage, |M|Σ, K2, K3,
cut links, member CV. **Memoized by canonical key, shared across all walks in one driver run**
(deterministic ⇒ a revisited bucketing is free; memo hits counted and printed).

**`PartitionProposer`** (Stage-0 closed membrane) — tables the slate of legal neighbor moves on the
incumbent, in canonical order.

**`MetaPanel`** — disposes the full slate each round (full-slate steepest descent, ruled
2026-07-23):
1. **`refuse:incoherent`** — any candidate with `gap > θ=0.20` is refused outright, regardless of
   cost (E2b's decay-incoherence wall as a licensed refusal, not a price). The gate applies to
   *candidates*; an incumbent's own gap is reported, so a walk may *start* standing-incoherent
   (the N=1 start, gap 0.58) and escape via its first accepted move.
2. **`accept:split` / `accept:merge`** — among survivors strictly cheaper than the incumbent in
   **the walk's arm currency** (Arm-N naive cost for main walks; Arm-I incremental cost for the
   control), accept the cheapest; ties broken by canonical bucketing order.
3. **`halt:converged`** — no admissible strictly-improving move.
|M|Σ / K2 / K3 are recorded every round and are **never verdict-bearing** (the K-measure guard).

**`run_meta_walk(start, arm) → WalkResult`** — rounds until halt or `max_rounds=20` (a
`max_rounds` exit is reported as **non-converged**, never as convergence). Every round appends to
the walk's **JSONL move ledger**: incumbent key, slate (keys + full evidence vectors), refusals,
disposition, chosen move, memo hits. A `replay_walk(ledger)` reader recomputes every panel
disposition from the *recorded* evidence (no re-evaluation) and verifies the walk — the record is
re-checkable, the m_steps discipline at harness level.

---

## 3 · The run matrix (all pre-registered; ruled 2026-07-23)

| Walk | Arm (currency) | Start | Expectation under the priors |
|---|---|---|---|
| W1 | Arm N (naive) | N=1 (all folders, one bucket) | splits its way into the interior; escapes the standing-incoherent monolith on move 1 |
| W2 | Arm N (naive) | N=12 (all singletons) | merges its way into the interior |
| W3 | Arm N (naive) | unbalanced N=4, contiguous sizes 6/3/2/1 (sorted folder order) | settles into the same cost basin (robustness) |
| W4 | Arm I (incremental) | N=1 | the control: runs to the finest partition, N=12 |

Plus the rider E2b′ (§5). The driver runs W1–W4 off one shared memo cache, then the rider, then the
verdict layer and the canary.

---

## 4 · Cost instrument

Unchanged from E2/E2b: `COST = Σ_rounds (materialiser atoms + peel evaluation steps)` per member,
summed over members, plus the coordinator tax per arm (Arm N naive per-member-round replay; Arm I
incremental). K1 = N/A (raise-only membrane, A1). **Wall-clock is secondary, never
verdict-bearing.** Estimated bill for the whole matrix with the shared memo: **~3–5h** (dominated
by low-N evaluations and the W3 canary re-run; every estimate disclosed in the log).

---

## 5 · Rider E2b′ — the coherence regime + the first broker exercise (two cells, no walk)

E2b proved link density cannot force the coherence gap at this scale (PB3 refuted) but decay can
(gap 0.58 at N=1). The rider makes decay the knob:

- **(a) Regime finder.** Fixed round-robin bucketings N ∈ {2,4}, sweep `ttl ∈ {60, 30, 15}` at
  `R=325` (6 cells), read gap. The **biting regime** = the *largest* ttl in the set with
  `gap > θ` at **N=4**. (N=2 gaps are recorded for the mechanism read but do not define the
  regime.) If no ttl bites at N=4, PE4 is refuted (an honest null, PB3-style) and cell (b) is
  undetermined.
- **(b) Broker-active quality re-test (PB4's deferred test, finally under force).** At the biting
  regime, round-robin vs link-aware (`link_aware_buckets`, greedy min-cut — already built in E2b)
  at N=4, with unresolved cross-links actually **routed through the existing
  `Coordinator.route()`** and the routing tax added to the coordinator cost (reusing
  `run_p_sweep`'s broker machinery). The broker tax remains an **end-of-run snapshot** (A3-style
  lower bound, disclosed) — the broker feeds routes back, so it is not replay-exact.

---

## 6 · Pre-registered priors (PE1–PE5 — committed before any run)

- **PE1 (convergence — the headline).** W1 **and** W2 halt `converged` at an **interior** bucketing
  (1 < N < 12) whose Arm-N cost is **at most 1.10 × E2b's measured trough** (≤ 150,842; a walk
  that converges *below* the trough also holds — cheaper than the measured optimum is success,
  not failure). *Refuted if either walk halts at an endpoint, exits at max_rounds, or converges
  above the ceiling.*
- **PE2 (basin agreement — robustness).** The three Arm-N walks (W1, W2, W3) halt at final Arm-N
  costs within `tol`=10% of each other (max/min ≤ 1.10). *Refuted if the spread exceeds tol* —
  the landscape would then have multiple basins the walk discipline cannot escape, and "the"
  optimum would be start-dependent.
- **PE3 (control — the optimum is the arm's, not the walk's).** W4 (Arm I) never settles interior:
  it halts at the all-singletons bucketing N=12. *Refuted if it halts interior* — which would mean
  the interior optimum is produced by the walk machinery rather than by the naive coordinator's
  scan tax, undoing E2b's PB2 reading.
- **PE4 (the rider's premise — decay reaches coherence at N>1).** Some `ttl ∈ {60, 30, 15}` gives
  `gap > θ=0.20` at N=4 on this corpus. *Refuted if none does* — then the coherence force is
  confined to the monolith endpoint at this corpus scale and the quality question needs a larger
  corpus, reported as a finding.
- **PE5 (partition quality has teeth under force), conditional on PE4.** At the biting regime with
  broker-active costing, link-aware bucketing's total cost is at least `tol`=10% below
  round-robin's at N=4. *Refuted if the difference is < tol* (with the force present, quality
  still doesn't matter — E3's quality search would be moot and the program should say so).
  **Undetermined if PE4 refuted** (the force is absent; a null is PE4's consequence, not evidence
  about quality — the PB4 pattern).

**Stated in advance:** E3 tests the convergence of *this* walk discipline (full-slate steepest
descent with the disclosed top-3 merge shortlist) on *this* landscape — not of negotiation in
general, and not of any community process. A convergent E3 licenses "self-partitioning can find the
measured optimum under the naive coordinator on this corpus," nothing stronger.

---

## 7 · Determinism canary

W3 (the mid-start walk, the cheapest expected) is re-run end-to-end with a **cleared memo cache**;
the move sequence, final bucketing, and final costs must match the first run exactly. Reported
PASS/FAIL. The full matrix is not double-run (wall-clock; disclosed, as E2/E2b).

---

## 8 · Honesty ledger — what E3 does NOT establish

- **A model of negotiation, not a community.** The meta-Agon is one instance modelling partition
  moves; no reciprocal typification, no commens (THE_COMMENS binds hardest at this rung).
- **Convergence of one discipline.** Steepest descent with a top-3 link-guided merge shortlist is
  *a* walk, not the space of walks; a different discipline could converge differently. The
  shortlist is proposer attention, disclosed, and never touches how a tabled move is judged.
- **Synthetic, one seed, one topology.** All walks share `seed=20260721`; the basin structure is
  the generator's. A real-vault corroboration is deferred.
- **The Arm-N interleaving assumption carries over** (members modelled concurrent, harness runs
  them sequentially; ~26% on E2's reference case) — verdict-bearing for every Arm-N reading (PE1,
  PE2, and W1–W3's every disposition).
- **The broker tax is a snapshot** (rider cell (b)): an A3-style end-of-run lower bound, not
  replay-exact.
- **No Arisbe-native record.** The move ledger is JSONL, not a UoD chain; lifting the trajectory
  into ink is deferred (the §1 ruling) and would be a separate increment.
- **K-measure guard.** |M|/K2/K3 are reported vectors, never targets, never verdict-bearing.

---

## 9 · Build surface (informational — for the implementation plan)

- `src/west_meta_agon.py` (new, unprotected): `Bucketing` canonicalisation + moves + slate
  (top-3 merge shortlist), `MetaEvidence` + memoized evaluator over the E2b bucketed runner,
  `PartitionProposer`, `MetaPanel` (gate → steepest-descent accept → halt), `run_meta_walk` +
  JSONL ledger + `replay_walk`, the rider cells (regime finder; broker-active quality re-test),
  `assemble_e3_report` (PE1–PE5 verdicts).
- `tools/run_west_e3.py` (new): numbers-only driver — W1–W4 off one shared memo, rider, verdicts,
  canary; `--smoke` mode for the driver contract test. Output under `runs/west_e3*` (gitignored;
  the tracked log will be `runs/WEST_E3_LOG.md`, spared like the E2/E2b logs).
- Tests `tests/test_west_meta_agon.py` (+ driver contract test), mirroring the E2/E2b per-module
  pattern: canonicalisation, move enumeration + tie-breaks, shortlist determinism, gate refusal,
  steepest-descent acceptance + tie-break, halt-on-converged vs max_rounds honesty, memo-hit
  counting, ledger round-trip + `replay_walk` verification, arm-currency selection, rider
  regime-finder branch behaviour, and a **verdict layer with killer fixtures per PE conjunct**
  (the E2/E2b mutation-review lesson: verdict layers are where mutations survive).
- E1/E2/E2b entry points stay **byte-frozen**; zero protected-core change is anticipated. Any need
  for one halts the build for authorization.

---

## 10 · Decisions (ruled by the author, 2026-07-23)

1. **Harness-level Agon loop** (proposer/panel/ledger over a plain partition state), not
   Arisbe-native ink; the JSONL ledger keeps the later lift possible.
2. **Full R=325 evaluations, memoized** — evidence directly comparable to E2b's measured curves.
3. **Fitness = Arm cost + gap-gate; vector reported** — gap>θ refuses; |M|/K2/K3 never
   verdict-bearing.
4. **Run matrix**: two end-starts + unbalanced mid-start (Arm N) + Arm-I control + rider E2b′.
5. **Full-slate steepest descent** with the disclosed top-3 link-guided merge shortlist.
