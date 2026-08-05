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
- **Q-E (the vector *instrument*).** West's clean *scalar* exponent lives at the **supply** layer he
  modelled; the **allocation-toward-purposes** layer is vectorial and niche-constructing. A kytos
  makes that vector explicit (the disposition taxonomy, the K1–K4 measure). Is the kytos the lens on
  the structure *beneath* the scalar exponent — the layer West's formalism does not represent?
  *(Re-voiced 2026-08-01, Examination VIII, the author's Ruling B. This question formerly asked
  whether West's universality "itself needs a vector operand". It does not, and the question was
  malformed twice over. **Scalarity is not what selects the exponent** — WBE call their derivation
  "essentially a geometric one", and three redoings minimizing three different things, one of them
  minimizing nothing at all, converge on 3/4. And under Ruling B a knowledge measure is an
  **instrument, never an optimand**, so it replaces nothing in West's objective and there is nothing
  to depart from. What remains, and is worth asking, is whether a kytos can make **observable** a
  layer the scaling program brackets.)*

The program is deliberately **conjecture-until-measured** (THE_KYTOS §5 honesty ledger): the
scaling exponents and the whole community rung are flagged as unmeasured. These experiments are the
first data.

**A caution built into the frame** (THE_KYTOS §4; THE_COMMENS): the community rung is a change in
*kind*, not degree — reciprocal typification and genuine institutionalisation *cannot occur in an
individual*. So these experiments **model** a federation of kytē (a good-regulator model of the
institution); they do not *constitute* the commens. E1's "coordinator" is a switchboard, not a
society. That boundary is a permanent honesty flag on every result here.

## 2 · The ladder — **RUN OUT, AND THE ARM IS RETIRED (2026-08-05)**

> **The whole ladder below was climbed, and the series closed at E3c on 2026-07-27.** It is
> kept as written because what each rung predicted is part of the record; the dispositions are
> in `runs/WEST_E1_LOG.md` … `runs/WEST_E3C_LOG.md`.
>
> **The arm is now retired from the live list**, on the
> [tenability assessment](superpowers/specs/2026-08-05-the-tenability-assessment.md) §8(d),
> ruled by the author 2026-08-05. **The frontier is not retired — the *experiments* are.**
> Examination VIII (2026-08-01) priced the entry at nine conditions and found the instrument
> fails condition (3) structurally: on a substrate where every unit reaches every other at
> uniform cost, the borrowed derivation gives **β = 1 exactly**, mortality and selection
> included. §8 records that ninth condition and what would lift it.
>
> **The last hope was met and did not save it.** The C-series stage-4 spec §11.5 held that
> *"the C-series cannot answer the West question until units can die."* D-1 gave them death
> (`runs/RUN_D1_LOG.md`, `P-D1` held at every seed). The mapping closed anyway, for the
> independent reason above — which is the cleanest evidence that mortality was never the
> binding constraint.
>
> **The standing rule this arm bought, at the cost of six runs:** a sealed world whose every
> parameter is calibrated from itself can be asked *existence* questions and *attribution*
> questions, and cannot be asked *magnitude* questions at all
> ([FROM_THERMODYNAMICS_TO_SEMIOSIS](FROM_THERMODYNAMICS_TO_SEMIOSIS.md) §6a). Further West
> work goes through the spine's queued conjectures, not through another rung here.

- **E1 — paired comparison (DONE, this program's first datum).** MONO (one whole-vault kytos) vs a
  fixed per-folder FED (member kytē + a journal-member + a coordinator) on one generated corpus.
  Delivers the paired cost/quality/coherence comparison **and the reusable measurement harness.**
  Answers Q-B in its paired form. *Two points (N=1, N=F) cannot fit a power law — E1 is not the
  exponent.*
- **E2 — the size sweep (DONE; E2b calibrated it).** Vary the partition granularity (N = 2, 4,
  8, … member kytē) and/or corpus size, and fit the scaling relation. Was to be the first point
  at which a West **exponent** is estimable. Tests **Q-C**. *What it measured instead:
  β_mono 1.277 against β_fed 1.025, and a 25× spread attributable to the coordinator's scan
  discipline rather than to the partition — E2's own finding, in its own words.*
- **E3 — endogenous partition (DONE; E3b, E3c closed it).** Make apportionment itself a licensed,
  recorded move — split/merge of kytē as proposals in a meta-Agon over partitions, adjudicated by
  the measured cost/K curves. Tests whether self-partitioning converges and whether its exponent
  beats the monolith's at equal K1/K2 (**Q-B's second form**). *It converged on N=3 granularity
  across 36 starts and 19 local optima — and Examination VIII's VIII.26 records that a
  multi-basin landscape is evidence **against** the mapping, not for it: West's minimization is
  over smooth constraints with a closed-form unique optimum.*

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

> **Superseded in part by §8 (2026-07-28).** The audit recorded there found an **error in the
> experimental design**, and several entries below read more confidently than the harness
> supports. Read §8 first; it governs.

- **Built + evidenced:** the E1 paired comparison and its reusable, deterministic, custody-safe
  harness; the ~5.2× cost result and the P2 clustering signal at one N. *(§8: the ~5.2× measures
  upkeep under partition against a meter that charges model size per round — the ratio tracks
  member count — and the "at equal quality" clause carries no weight.)*
- **Conjectured, not yet measured:** every scaling *exponent* (E2); terminal-unit invariance across
  community sizes (E2); whether FED-retains-more is a decay artefact or a real advantage (E2 ttl
  sweep); where the passive registry breaks (the p crossover); whether self-partitioning converges
  (E3).
- **Standing caveats:** synthetic ≠ real corpus topology (a deferred real-vault check); the community
  rung is modelled, never constituted (THE_COMMENS); "one ledger shape suffices at every level" is a
  flagged conjecture the community rung is precisely where a skeptic should attack (THE_KYTOS §5).

---

## 8 · An error in experimental design (recorded 2026-07-28)

*(Written after a code-level audit run while drafting the West letter, at the
author's challenge, and folded into the graded documents by his ruling the same
day: record it properly as a design error, keep it out of any letter or overall
description of what we build, repair the documents that outran the instrument
now — and hold open the prospect that a properly designed experiment still has
much to teach. This section records what the instrument actually did, so no
later reader inherits a claim the floor will not carry.)*

The run logs reported straight. The overstatement accumulated **above** them —
in the interpretive language of E2's finding 5, in THE_KYTOS §4, in the
concordance-map row, and worst in the letter draft. Four findings, each
verified in code and two of them by instrumented probe:

1. **The federation never communicates.** Members run sequentially, each in
   full isolation, and each finishes before the next begins. Afterwards the
   coordinator *reads* the finished models and copies out their distinct
   relation **names** — at F=4, twenty-two cells, six names crossed with four
   folders. No facts cross, nothing returns to a member, and the broker's
   routing result is discarded by every caller. `consistency_scan`'s loop body
   is `pass`; from E2 onward the coordinator tax is a closed-form replay rather
   than an executed scan.
2. **Nothing reasons.** The corpus carries ground metadata and no laws, so
   every round measures `rules_applied = 0`, `derived_facts = 0`. The peel runs
   and its verdict is never read by any panel agent. K3 = 0.0 records the
   absence of anything to derive, not a property of an arrangement.
3. **"At equal durability" carries no weight.** K2 can only read 1.0 or
   undefined on this harness: the non-decay erasures require agents that cannot
   fire on this feed, and decay-erased episodes are excluded from the
   stick-rate by construction. In probe, 40% of admissions were erased and did
   not count. The parity gate compares 1.0 against 1.0.
4. **The cost meter charges size, not work.** Cost = Σ over rounds of |M|,
   charged even where a cache hit does no work. A monolith running R rounds
   against one accumulating model pays ≈ c·R²/2; a federation splitting those
   rounds across F+1 members pays ≈ c·R²/2(F+1). The observed ratios track F+1
   (3.96 against 5 in probe; 5.2 against 7 in E1), decay blunting the
   quadratic.

**Terminal-unit invariance was imposed, not discovered.** E2 fixes
`NOTES_PER_FOLDER = 40` and sets `R = 25·(F+1)` "so every member performs
exactly 25 rounds at every F." Each unit therefore holds a fixed slice and
spends a fixed budget across the whole sweep, and the measured 1.0012 max/min
confirms the harness is deterministic. West's invariant terminal unit is an
empirical surprise — the network reorganizes as mass grows, yet capillaries
stay the same size. Ours is an assumption confirmed.

### The mis-mapping (the author's diagnosis, 2026-07-28)

The deeper fault sits in the comparison itself. **MONO has no counterpart as a
terminal unit.** In West's framework the terminal unit is the capillary and the
organism is the network that feeds it; the scaling law relates an
organism-level rate to organism size. A monolith is not a larger organism — it
is a single unit made big, which is the one thing West's networks never do.
Comparing FED to MONO therefore compares an organism to an inflated cell, and
answers no question about terminal units.

If a MONO correlate exists, it lives **at the level of the community as a
whole** — one community measured against another, plausibly competing for an
ecological niche. That relocation matters twice over. It puts the scaling
question where West asks it (how does a *community's* rate scale with its
size?), and it supplies the selection pressure his exponents depend on:
biological and urban exponents arise from optimization under constraint, and
nothing in these runs selects between arrangements at all.

### What the metabolized stuff actually is

Also the author's, and it names what the harness omitted. The metabolism of
interest consists of **what the kytē communicate and jointly maintain as an
objective reality between them**, together with **what each retains, reasons
on, and forgets internally** — M and its facts, the standing questions
(AlternativeSets), deductions, inductions, abductions, generalizations,
specifications. The E-series exercised the storing and the forgetting. It
exercised none of the reasoning, and none of the between.

### Three premises the corrected experiment must state and obey

*(Ruled by the author, 2026-07-28, during the design brainstorm — recorded here
for the build. They are semiotic commitments, not implementation details, and
each of them forbids a specific error the previous series committed or invited.)*

1. **Reality resides inside the kytos, and nothing is ever scored against a view
   from outside it.** A kytos's UoD *is* its reality — the attested internal
   model behind its membrane, indexed to the history by which it came to hold it.
   The generated field's structure therefore carries no privileged standing: it
   names the **field's regime**, the law by which deliverances arrive at
   membranes, and never "ground truth." Fitness gets scored **at the membrane** —
   did this community's model reliably anticipate what actually arrived? — which
   keeps the correspondence-not-truth floor intact and matches the project's own
   definition of knowledge (reliably doing something that works). Our knowledge of
   the regime stays a *modeler's diagnostic*, labelled as such, permitted to ask
   whether a planted law was recovered and how fast, and forbidden from entering
   the fitness.
2. **What the community shares are marks — and the marks are not the commens.**
   Three terms, kept apart. The **UoD** is what a kytos thinks with, inside its
   membrane. The **objectivated marks** are what a kytos externalizes: published,
   attributable, inspectable inscriptions — Berger and Luckmann's objectivation,
   subjective meaning hardened into available facticity. These the protocol moves
   and the instruments count. The **commens** is neither: following Peirce's
   Communicational Interpretant (the 1908 Welby correspondence — *that mind into
   which the minds of utterer and interpreter have to be fused in order that any
   communication should take place*, consisting of all that must be well
   understood between them **at the outset** for the sign to fulfill its
   function), it names the prior, enabling mutual understanding that makes a mark
   legible at all. It belongs to no participant, and per
   [THE_COMMENS_AND_THE_COMMUNITY.md](THE_COMMENS_AND_THE_COMMUNITY.md) §1 **no
   data structure may carry its name**. What crosses between kytē is never content
   but a sign: kytos-5 encounters kytos-3's inscription and forms its own
   interpretant of it, out of a different history.

   *(Recorded correction, same sitting: an earlier draft of this premise defined
   the commens **as** the marks. That commits the exact category mistake §1 of
   THE_COMMENS warns against most loudly — identifying the commens with a
   deposit. The author caught it. The measurable object is the marks and their
   uptake; the commens stays regulative.)*

   **The commens is measurable only at its contour, by failure.** When a mark
   passes between two kytē and gets taken up as its utterer meant it, the commens
   held there silently and unobservably. When uptake miscarries — a term read
   differently, a mark needing repair or renegotiation before it can function —
   an edge has been found, and edges are countable. Breakdown-and-repair episodes
   are therefore the instrument: they map what was *not* held in common, which is
   the only honest access to what was.
3. **Divergence holds by construction, not by hope.** No participant comprehends
   the commens — it belongs to none of them — and no two kytos realities ever
   perfectly coincide, having different histories and different identities. The
   design must *guarantee* the second: units meet the field through different
   apertures (regions, sampling orders, budgets), or they converge on
   near-identical models, communication degrades into redundancy, and the
   apparatus measures nothing. Divergent history is a precondition of there being
   anything to communicate, not a nuisance parameter to be minimized. It follows
   that a *shared* aperture across all units would not produce a stronger
   community but a vacuous one.

A corollary binds the modeler too: any bird's-eye account of the whole — this
document included — exists as a simplification inside *our* membrane. It hints at
what happens outside it and cannot substitute for it. That is not a caveat about
this experiment; it is how semiosis works, and the experiment should be built so
that it never needs the bird's-eye view to reach a verdict.

### What a proper terminal-unit test requires

Named here so the next attempt starts honest, not so it starts soon.

**Written environment-side, on the author's ruling of 2026-08-01** (Examination
VIII, Q3). The earlier draft of this list enumerated what *units* must be — able
to die, holding a fixed quantum — and five of its eight conditions were mis-voiced
that way. That is the cart before the horse inside the document that diagnoses it:
mortality and a fixed quantum are **consequences** of a world in which maintenance
costs something and the source depletes, not properties a modeller installs. The
design rule that follows is **the environment must carry structure the unit does not
already encode**, and the practical test applied to each item below was *would
building to the environment-side version produce a different implementation?* For
every one of the five, it would.

- **A source split across apertures**, such that the facts confirming a law are
  never all delivered to one unit — so that a unit ignoring another's mark
  forecasts measurably worse, and communication carrying content becomes a
  *finding* rather than a channel we build and then hope gets used. (Was:
  "communication between units".) Otherwise no community exists to scale, per
  THE_COMMENS.
- **Laws in the corpus**, so units derive rather than only accumulate; K3 above
  zero is the signal that anything is being metabolized at all. *(Already
  environment-side — a property of the field.)*
- **A world that charges for holding and pays for anticipating**, so that *use*
  means an atom that entered a derivation which met an arrival, not an atom
  re-delivered. (Was: "provenance in the materializer" — instrument-side.)
  Today's `delivered_atom_keys` defines use as re-delivery and says in its own
  docstring that inference-use was "deliberately not taken here."
- **A live K2**, which needs a membrane with world-teeth: some way for a
  standing item to be defeated by something other than the decay clock.
  *(Already environment-side — a charge the world levies.)*
- **A source of fixed quantity and replenishment rate, independent of N**, so
  that adding units divides a fixed supply rather than regenerating a field per
  N — the size swept being the number of communicating units, and the terminal
  unit's invariance left free to emerge or fail. *(Method-side as written; the
  environment-side version is what makes the invariance measurable rather than
  assigned. `c_field.deliver` today has no global budget, which is exactly how
  the E-series came to impose per-unit invariance.)*
- **A niche too small for all** — a finite source that a better-anticipating
  community retains more of, so a worse one starves. (Was: "selection between
  communities", which as an *operator* needs an external fitness scorer that this
  document forbids three paragraphs above: *reality resides inside the kytos, and
  nothing is ever scored against a view from outside it.* **Extinction is running
  out**, and it needs no scorer.) Required if the exponents are to mean what they
  mean in *Scale*.
- **Maintenance that costs, against a source that depletes**, so that a unit whose
  intake falls below its standing upkeep stops. West's β measures the maintenance
  cost of keeping terminal units alive, so with immortal units there is no cost and
  no exponent. **Death is failure to meet a charge, not a capability** — the
  environment-side build is the *smaller* one, since the E-series already has a
  meter charging model size each round and needs only finite income, where the
  unit-side version needs a lifespan parameter somebody picks. *(Added 2026-07-30
  from the C-series' stage-4 examination; re-voiced 2026-08-01.)*
- **A fixed price per slot, levied by the world against an exogenous income**, so
  that slot count is determined outside the unit and cannot be enlarged from
  inside — the unit has no lever on price. A scaling law gets its exponent by
  counting an invariant unit, so capacity and rate must not vary with the unit's
  own state. *(As a unit-side prohibition this was **vacuous**: it is already
  satisfied by construction, since `AttentionEconomy.choose(k, round_idx)` takes
  `k` from the caller and severity only reorders the pool. Building to it required
  no code. Added 2026-07-31, see ADVERSARIAL_EXAMINATION Examination VII, VII.8;
  re-voiced 2026-08-01.)*
- **A reach structure in which the cost of reaching grows with the community's
  extent.** *(Added 2026-08-01, Examination VIII, and derived rather than
  enumerated — by the panel mandated to **defend** the mapping.)* Every West
  derivation, biological and urban alike, gets its exponent from a graded
  accessibility structure: WBE from space-filling fractal branching, Bettencourt
  from `δ = H/(D(D+H))`. A flat board where every unit reaches every other at
  uniform cost is the `H → 0` limit — equivalently `D → ∞` — and Bettencourt's own
  Table 1 says *agglomeration effects vanish as H → 0*. Then δ = 0, α = 1, and
  `Y = GN²/A_n ∝ N`: **linear, no exponent, however well the other eight are met.**
  Two blind panels reached this from opposite limits of the one equation. Note the
  bar this sets: the accessibility structure must be **measurable from the
  substrate before the run**, so the exponent is *predicted* rather than fitted —
  no non-spatial derivation in the literature predicts a value, and a fitted θ is
  a free parameter wearing a law's clothes.

**Two contradictions the old voicing carried, both dissolved above.** The
community-scaling condition asked for invariance *left free to emerge*, while the
fixed-quantum condition demanded it *pinned by construction*; environment-first
reconciles them exactly — **fix the price, let the quantum fall out**, and
invariance becomes measurable rather than stipulated. And selection-as-operator
required the external scorer premise 1 forbids; only the niche reading is
consistent with this document's own commitments.

Until then the honest statement of the E-series is narrow and still worth
something: *partitioning a maintenance workload across bounded units lowers
total upkeep under a size-charging meter, and how much depends overwhelmingly
on the coordinator's scan discipline rather than on the partition* — E2's own
finding, in its own words.

### The prospect (the author's ruling closes on this, and so should the section)

A design error found before publication costs a draft; found after, it costs a
reputation. This one cost a draft. What it leaves behind matters more than what
it withdrew: the question the program set out to ask **remains open and now has
a shape**. Nobody yet knows how the upkeep of a community of reasoning units
scales with the number of units that genuinely communicate, whether a
terminal-unit invariance would *emerge* once nothing pins it, whether the
allocation layer really behaves as a vector once more than one component can
move, or what selection between rival communities would do to any of it. The
harness, the determinism discipline, the pre-registration habit, and the
custody-safe corpus generator all survive intact and transfer directly. What the
next attempt needs is not a better instrument but a better experiment.
