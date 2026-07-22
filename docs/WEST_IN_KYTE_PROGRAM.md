# The West-in-kytē program — rationale, E1 result, and the shape of E2/E3

> **What this is.** The program-level design-of-record for the West-in-kytē experiments
> (the author's forward-agenda item #6). It states *why* we run them, records *what E1
> established*, distils *what E1 taught*, and lets those learnings *shape E2 and E3*. The
> per-run numbers live in `runs/WEST_E1_LOG.md`; the E1 protocol was pre-registered in
> `docs/superpowers/specs/2026-07-21-west-in-kyte-experiment-design.md`; the harness plan is
> `docs/superpowers/plans/2026-07-21-west-in-kyte-e1.md`.
>
> **Companions:** [THE_KYTOS.md](THE_KYTOS.md) §4 (the quantitative frontier — West; the S/A
> decomposition; the reliability-not-analogy framing) · [THE_MEASURE_OF_KNOWLEDGE.md](THE_MEASURE_OF_KNOWLEDGE.md)
> (the K1–K4 vector a kytos is scored by) · [THE_COMMENS_AND_THE_COMMUNITY.md](THE_COMMENS_AND_THE_COMMUNITY.md)
> (why the community rung is a change in *kind*).

---

## 1 · Why we run these (the rationale)

Geoffrey West's *Scale* observes that living aggregates that share one anatomy across scales
exhibit **discoverable scaling relations** — metabolism, distribution networks, turnover all
scaling as clean power laws of size. THE_KYTOS §4 makes the claim that Arisbe's *kytos* (the
recurring membrane-and-loop unit of doubt-driven semiosis) is the same *kind* of thing: a kytos
optimising for **reliable reasoning** and an organism optimising for **reliable energy economics**
are both selection-driven reliability-optimisations over associative networks of invariant terminal
units. If that is right, aggregates of kytē should show scaling relations we can *measure*, not
merely analogise.

Three questions carry the program (CURRENT_PLAN item -8; THE_KYTOS §4):

- **Q-B (federation / apportionment).** Does partitioning one big reasoning loop into a federation
  of small folder-bounded loops plus a coordinator *cost less* at equal knowledge quality — i.e. is
  the monolith's already-evidenced super-linear per-round cost avoidable by apportionment?
- **Q-C (terminal-unit invariance).** As the community grows, does per-kytos cost-per-doubt-cycle
  stay *invariant* (West's cell-metabolism-per-unit-mass falling with size — the economy of scale)?
- **Q-E (the vector optimand).** West's clean *scalar* exponent lives at the **supply** layer he
  modelled; the **allocation-toward-purposes** layer is vectorial and niche-constructing. A kytos
  makes that vector explicit (the disposition taxonomy, the K1–K4 measure). Does West's universality
  itself need a vector operand — is the kytos the lens on the structure *beneath* the scalar exponent?

The program is deliberately **conjecture-until-measured** (THE_KYTOS §5 honesty ledger): the
scaling exponents and the whole community rung are flagged as unmeasured. These experiments are the
first data.

**A caution built into the frame** (THE_KYTOS §4; THE_COMMENS): the community rung is a change in
*kind*, not degree — reciprocal typification and genuine institutionalisation *cannot occur in an
individual*. So these experiments **model** a federation of kytē (a good-regulator model of the
institution); they do not *constitute* the commens. E1's "coordinator" is a switchboard, not a
society. That boundary is a permanent honesty flag on every result here.

## 2 · The ladder

- **E1 — paired comparison (DONE, this program's first datum).** MONO (one whole-vault kytos) vs a
  fixed per-folder FED (member kytē + a journal-member + a coordinator) on one generated corpus.
  Delivers the paired cost/quality/coherence comparison **and the reusable measurement harness.**
  Answers Q-B in its paired form. *Two points (N=1, N=F) cannot fit a power law — E1 is not the
  exponent.*
- **E2 — the size sweep (NEXT).** Vary the partition granularity (N = 2, 4, 8, … member kytē) and/or
  corpus size, and fit the scaling relation. The first point at which a West **exponent** is
  estimable. Tests **Q-C**.
- **E3 — endogenous partition (AFTER).** Make apportionment itself a licensed, recorded move —
  split/merge of kytē as proposals in a meta-Agon over partitions, adjudicated by the measured
  cost/K curves. Tests whether self-partitioning converges and whether its exponent beats the
  monolith's at equal K1/K2 (**Q-B's second form**).

## 3 · E1 — what was established

Config (pre-registered, fixed): `seed=20260721, F=6, n=40, p=0.15, J=40, R=300, θ=0.20, tol=0.10`.
Full numbers + the honesty ledger: `runs/WEST_E1_LOG.md`.

| | cost (deterministic) | quality (K2) | coherence |
|---|---|---|---|
| **MONO** | 188,039 (mat 186,185) | 1.0 | — (single M) |
| **FED** (F+1=7 members) | **36,097** (mat 33,584, coord 666) | 1.0 | coverage 1.0, gap 0.0 |

**All four pre-registered priors P1–P4 held.** FED reasons at **~5.2× lower deterministic cost** at
equal K2 stickiness; the **passive registry alone** kept the federation coherent (gap 0 ≤ θ, the
active broker never fired); the six folder-members' costs **cluster within ±0.9%** (the Q-C
terminal-unit-invariance *signal*); the run is byte-deterministic (canary PASS).

**Adaptations (author-ratified / disclosed).** A1 — the vault membrane is raise-only (no world
teeth), so K1 (a severity-weighted track record) is N/A and parity is judged on **K2**. A2 — FED
adds a **journal-member** so it covers the same corpus as MONO (work-parity). A3 — the coordinator
tax is measured as one **end-of-run snapshot**, a *lower bound* on the pre-registered per-round tax,
so it under-counts FED and biases *toward* P1 (magnitude negligible; disclosed on every run).

## 4 · What E1 taught (the learnings that shape the next rungs)

1. **The cost gap is a materialisation gap, exactly as the monolith-pain hypothesis predicted.**
   99% of MONO's cost is forward-chaining its single growing M every round (186,185 of 188,039);
   FED's members stay folder-bounded and cheap. This means **the scaling law E2 should fit is a law
   of |M|-driven per-round materialisation cost**, not of peel or coordination (both negligible).
   E2's cost instrument can lean on the same `CountingMaterializer` per-round atom counts.

2. **The clustering signal is real but is *not* the invariance test.** ±0.9% across six same-size
   members is a strong Q-C signal, but all six are the *same size* — genuine terminal-unit invariance
   is about cost-per-cycle holding as the *community* grows. **E2 must vary N (and folder size) and
   read whether per-kytos cost-per-cycle stays flat**, i.e. the clustering has to survive a size
   sweep, not just a single N.

3. **A surprise worth its own probe: the federation retains *more* total knowledge.** FED |M|Σ = 1367
   vs MONO |M| = 752 (~1.8×) at equal K2. The working hypothesis is decay pressure — MONO's *single*
   attention budget over R rounds decays more of its working set (ttl=120) than each folder-member's
   smaller, less-contended M does. If true, apportionment buys *both* lower cost *and* more retained
   knowledge — a double advantage the scalar cost-exponent alone would miss, and precisely the kind
   of **vector effect Q-E predicts sits beneath the exponent.** **E2/E3 should measure |M| retention
   as a first-class outcome, not a footnote**, and vary ttl to test the decay-pressure explanation.

4. **The coherence tax stayed trivial at p=0.15 — so we haven't found the federation's breaking
   point.** The passive registry resolved all 47 cross-folder references (gap 0); the broker never
   fired. We therefore learned nothing yet about *where* federation stops being free. **E2 (or a cheap
   E1-rider) should sweep p upward until gap > θ forces E1b (the broker)** — that crossover is where
   the coordination cost starts to matter and where the Q-B trade-off actually has teeth.

5. **A3 is a real fidelity debt to pay down at scale.** The end-of-run coordinator snapshot was fine
   for E1 (tax ≪ MONO cost), but a per-round tax grows with both R and the digest, and E2's larger
   N/R will make it less negligible. **E2 should implement the true per-round tax** (run members in a
   round-by-round lockstep, or accumulate the scan per member-round) so the coordination cost is
   honestly on the curve when it starts to matter.

6. **The harness is reusable and the review loop paid.** The measurement layer (`west_measure`,
   `west_coordinator`, `west_experiment`, the numbers-only driver) is parameterised on F/n/p/R/ttl
   and is the substrate E2 sweeps over — E2 is mostly a *driver that loops the existing harness over
   N and corpus size and fits a curve*, not a new build. Three generator/measurement defects that
   the per-task review caught (bare journal date-lines; globally-unique note stems; exact-membership
   coverage) are now regression-pinned, so the synthetic corpus can be trusted as we scale it.

## 5 · How the learnings shape E2

E2 = **the size sweep, to estimate a scaling exponent.** Shaped by §4:

- **Sweep dimension:** N ∈ {2, 4, 8, …} member kytē (partition granularity) and/or corpus size
  (folders × notes). Multiple points → fit `cost ∝ size^β`; report β with its fit quality. (Learning 2.)
- **Primary outcome:** per-kytos cost-per-doubt-cycle vs community size — does it stay flat
  (economy of scale, Q-C) or drift? Read the same `CountingMaterializer` cost. (Learnings 1, 2.)
- **Second outcome, promoted from footnote:** |M| retention per config, swept against ttl, to test
  the decay-pressure explanation of FED-retains-more. (Learning 3.)
- **Pay down A3:** implement the true per-round coordinator tax so coordination sits honestly on the
  cost curve as N grows. (Learning 5.)
- **Find the crossover:** sweep p until gap > θ forces the broker; report the p at which passive
  federation breaks and the tax the broker then adds. (Learning 4.) *This can run as a cheap E1-rider
  before the full E2 if we want the crossover first.*
- **Pre-register E2's priors** before running (the Pⁿ/Fⁿ discipline), including a pre-committed
  refutation: e.g. β indistinguishable from the monolith's, or per-kytos cost-per-cycle rising with N.

*Honesty flag E2 inherits:* an exponent from a *synthetic* corpus is an exponent of our generator's
topology, not of real reasoning corpora — a real-vault corroboration remains the deferred check.

## 6 · How the learnings shape E3

E3 = **endogenous partition** — apportionment becomes a licensed, recorded move rather than a fixed
design knob. Shaped by §4 and by whatever E2's curves show:

- Split/merge of kytē proposed and adjudicated in a **meta-Agon over partitions**, with the measured
  cost/K curves (from E1/E2's harness) as the disposition evidence.
- Tests **Q-B's second form:** does self-partitioning *converge*, and does its exponent beat the
  monolith's at equal K1/K2? The |M|-retention and decay-pressure findings (learning 3) become part
  of the fitness the meta-Agon optimises — the vector, not just the scalar cost.
- E3 is where the program brushes against the **commens boundary** (THE_COMMENS): a meta-Agon that
  negotiates partitions starts to look like reciprocal typification. E3 must stay explicit that it
  *models* that negotiation inside one instance — it does not constitute a community. The honesty
  flag of §1 binds hardest here.

## 7 · Honesty ledger (program-level)

- **Built + evidenced:** the E1 paired comparison and its reusable, deterministic, custody-safe
  harness; the ~5.2× cost result and the P2 clustering signal at one N.
- **Conjectured, not yet measured:** every scaling *exponent* (E2); terminal-unit invariance across
  community sizes (E2); whether FED-retains-more is a decay artefact or a real advantage (E2 ttl
  sweep); where the passive registry breaks (the p crossover); whether self-partitioning converges
  (E3).
- **Standing caveats:** synthetic ≠ real corpus topology (a deferred real-vault check); the community
  rung is modelled, never constituted (THE_COMMENS); "one ledger shape suffices at every level" is a
  flagged conjecture the community rung is precisely where a skeptic should attack (THE_KYTOS §5).
