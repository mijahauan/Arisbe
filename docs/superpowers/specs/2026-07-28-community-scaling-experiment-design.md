# The C-series: communities of kytē under selection — design

**Status:** design, author-ruled section by section on 2026-07-28. **Stages 1–2
built 2026-07-29** (both gates pass; see §9a for what the build found and what
it binds stage 3 to). Stages 3–5 not built.
Supersedes the E-series design (E1–E3c) as the vehicle for the West question;
does not supersede its harness, which largely transfers.

**Why a new series.** The E-series measured the upkeep cost of a partitioned
fact-store and could not bear on its headline question. A code-level audit
(`docs/WEST_IN_KYTE_PROGRAM.md` §8) found that its units never communicated and
never reasoned, its cost meter charged model size rather than work, its
durability metric could not read *false*, and its terminal-unit invariance was
imposed by fixing each unit's slice and round budget. Beneath all of it lay a
mis-mapping the author named: **a monolith has no counterpart as a terminal
unit** — it is a single unit made big, which West's networks never do. A MONO
correlate lives at the level of a whole community, plausibly competing with
another for a niche. This design starts there.

---

## 1 · The three premises (ruled 2026-07-28, recorded in WEST_IN_KYTE_PROGRAM §8)

These are semiotic commitments, not implementation details. Each forbids a
specific error the previous series committed or invited.

1. **Reality resides inside the kytos, and nothing is scored against a view from
   outside it.** A kytos's UoD *is* its reality. The generated field's structure
   is the **field's regime** — the law by which deliverances arrive at membranes
   — never "ground truth." Fitness is scored **at the membrane**: did this
   community's model reliably anticipate what actually arrived? Our knowledge of
   the regime is a labelled modeler's diagnostic and never enters fitness.
2. **What the community shares are marks — and the marks are not the commens.**
   Three terms stay apart. The **UoD** is what a kytos thinks with. The
   **objectivated marks** are published, attributable inscriptions (Berger &
   Luckmann's objectivation); the protocol moves these and the instruments count
   them. The **commens** is Peirce's Communicational Interpretant — the prior,
   enabling mutual understanding that makes a mark legible at all. It belongs to
   no participant and **no data structure may carry its name**
   (THE_COMMENS_AND_THE_COMMUNITY §1). It is measurable only **at its contour, by
   failure**: breakdown-and-repair episodes map what was *not* held in common.
3. **Divergence holds by construction.** Units meet the field through different
   apertures, or they converge on near-identical models and the apparatus
   measures nothing. Divergent history is a precondition of there being anything
   to communicate.

**Corollary binding the modeler:** any bird's-eye account of the whole exists as
a simplification inside *our* membrane. The experiment must never need the
bird's-eye view to reach a verdict.

---

## 2 · Decision log (this brainstorm, author-ruled)

| Question | Ruling |
|---|---|
| What counts as a community's output? | Predictive success at the membrane (primary rate) **+** the objectivated marks and their uptake (structural). Coverage-vs-regime is a diagnostic only; cost is a denominator, not an output. |
| What is the field? | A synthetic generated world with regional structure — deterministic, seeded, replayable. Four partially overlapping domains to start. |
| Communication protocol destination | Full ladder: assert · ask · challenge · typify. |
| Unit heterogeneity | **Identical units**; heterogeneity emerges. Faithful to West (terminal units are identical) and to B&L (types come from habitualization, not essence). |
| Series shape | **Emergence first** — fixed size, full protocol, minimal presets, watch. Fall back to a capability ladder only if nothing emerges. "This should grow organically, not by design." |
| Selection | **Present from the start.** |
| Communities | **Four.** Marks **sealed** between communities initially; permeable later. |
| Lifecycle | In scope: birth, socialization, death — with **time-to-socialize** as a headline observable. |

---

## 3 · The field

A seeded generator over **four partially overlapping domains** (pinned for the
first runs; domain count becomes a swept parameter only after C reports). Each
domain carries hidden regularities of its own; some regularities are shared
across domains — findable by any unit, and wasteful to find twice. The generator
emits observations at membranes and holds out a stream for prediction scoring.

Overlap is the load-bearing parameter. Disjoint domains make specialists win
trivially and reduce communication to routing; heavy overlap makes everyone
rediscover everything and specialization buys nothing. The interesting regime is
partial overlap.

**Correspondence to West, stated honestly.** West's networks are *homogeneous* —
one conserved resource delivered everywhere — so domain heterogeneity has **no
counterpart in his model**. It enters from B&L and the division of labour, because
without differing regions there is nothing for typification to typify. What the
domains *do* correspond to is **space-filling**, WBE's first pillar: the field
defines the volume a community's apertures must collectively cover, and the
**overlap fraction** governs whether an added unit adds coverage or duplicates
it — hence whether returns increase or diminish.

**Two honest breaks from West's model**, recorded so no later reader re-inherits
the E-series' optimism:

- **Signs are non-rival; blood is not.** A mark taken up by one unit remains
  available to all. West's organisms scale *sub*linearly because a conserved
  resource must traverse a constrained network. If our system resembles anything
  in his corpus it resembles the **city** (Bettencourt & West: superlinear
  socioeconomic output over sublinear infrastructure), not the organism.
- **WBE's third pillar is dissipation minimisation under selection.** Without
  selection the derivation does not go through, and any exponent describes the
  mechanics we chose rather than a law. This is why selection is present from the
  first run rather than added as a terminal rung.

---

## 4 · The unit

One instance of the existing loop — bounded interior model, attention economy,
decay clock — with three changes from the E-series:

- **Laws in the corpus**, so inference has something to do and derivation costs
  something real (K3 can leave zero).
- **Provenance in the materializer**: a derived atom's support set is
  recoverable. This makes *use* mean participating in work rather than arriving
  again, and it does double duty (see §7, repair detection).
- **An aperture**: the slice of the field this unit meets, distinct from every
  other unit's — premise 3 made structural.

**Every unit is constructed identically.** Nothing distinguishes them at birth
except where they stand. This is the repair of the original sin: E2 fixed each
unit's *workload* (slice size and round budget), making cost invariance
arithmetic. Here we fix each unit's *construction* and leave workload, history,
and role entirely free — so if per-unit cost or required capacity comes out
invariant anyway, that is a **finding** rather than a restatement of the setup.

**Sizing.** Start near **twelve units per community, each able to consult two or
three peers per round.** The floor is principled: a unit only needs to learn
*whom to ask* when it cannot afford to ask everyone, so N must exceed what a unit
can poll within budget or typification has no reason to appear. The ceiling is
our ability to read a full run by hand. The author's rider stands: the functional
quantity may need finding by trial, and **the relationship between community size
and required individual capacity is itself one of the interesting questions** —
indeed it is the honest form of the terminal-unit question (§8).

---

## 5 · The protocol

Four channels, all carrying **marks** — attributed, mention-not-use inscriptions
of the form `(asserts "kytos-3" ⌜P⌝)`, whose primitive already exists in the
quotation machinery:

1. **Assert** — publish a mark others may encounter and take up.
2. **Ask** — publish a standing question (the unit's own UNKNOWN), which others
   may answer. This makes the attention economy *social*: a unit now chooses
   between probing the field and answering a peer, which is the first genuine
   division of labour.
3. **Challenge** — refute another's claim, disposed by the calculus. This is what
   lets K2 finally read *false*: a standing item can be defeated by something
   other than the decay clock — the exact degeneracy that voided the E-series'
   "at equal durability."
4. **Typify** — each unit maintains a model *of the other units*: who has
   answered well about what. It learns whom to ask. This is B&L's reciprocal
   typification, and it cannot exist in an individual.

What crosses is always a sign, never content: the receiver forms its own
interpretant out of its own history. Marks are **sealed between communities** in
the first runs; permeability is a later switch.

---

## 6 · Communities and selection

**Four communities**, competing from the first run. Selection falls out of the
**budget** rather than from a fitness function we write:

- The field emits deliverances per domain each round.
- A finite **total budget per round is shared across all communities**, allocated
  **per domain** in proportion to recent predictive success in that domain.
- Budget buys the three things a community needs: **probes** (meeting the field),
  **communication**, and **socializing a newcomer**.
- Units that cannot be funded starve and die. A community that cannot fund
  socialization faster than it loses members shrinks, and can fail.

Nothing about roles, specialization, or niches is installed. Several things become
*possible* without being required: two communities crowding one domain split its
yield and both do worse, so differentiation pays without design; a community
whose coverage of a domain lapses stops earning there and feels it.

**Per-domain allocation is load-bearing**, not cosmetic: a global zero-sum pool
risks rich-get-richer collapse into a single winner within the first rounds.
Per-domain allocation means dominating one domain does not capture the others.

**The lifecycle acquires teeth here.** Socialization is paid out of the *same*
budget as inquiry, so a community faces a genuine trade-off between meeting the
field and training its young — arguably the central constraint on any real
institution, arriving from the accounting rather than from us.

---

## 7 · Instruments, control, and the null

C is exploratory. The discipline lives here: instruments and null are fixed
**before** the first run. We do **not** pre-register expectations — that would
defeat the point — but we do pre-register what we will measure and what *nothing*
looks like.

**Measured:**

- **Primary rate** — predictive success scored at each unit's own membrane,
  aggregated per community and per domain. (K1, finally live.)
- **Cost** (denominator) — probing, inference, communication, socialization,
  tracked separately, so we can see what a community spends its life on.
- **Marks** — count published and by whom; **uptake** (which are relied on, by how
  many); **durability** (how long they stand before challenge or decay); the
  attribution graph of who relies on whom.
- **Typification** — the who-asks-whom matrix, its departure from uniform and its
  stability; and each unit's model-composition drift from its community mean
  (specialization measured, not assumed).
- **Commens contour** — repair episodes, where a mark miscarries and needs
  renegotiation; and for newcomers, the decay of that repair rate toward the
  resident baseline: **the socialization clock**.
- **Capacity** — the capacity a unit *requires* to function, measured rather than
  fixed.

**Repair detection** rides on provenance: a mark taken up, appearing in the
support of a failed prediction, has demonstrably miscarried. No separate
mechanism needed.

**Modeler's diagnostic, labelled and fitness-excluded:** whether planted laws were
recovered, and how fast.

**The control is not a monolith.** It is the same four-community world, same
seed, run twice — once with the protocol live, once mute. Paired and
deterministic, it isolates communication as the variable.

**The null, written in advance.** Nothing emerged if:

- consultation stays indistinguishable from uniform (no unit becomes
  preferentially asked);
- uptake of marks is indistinguishable from random (publishing buys no reliance);
- the live world's predictive score is indistinguishable from its mute twin
  (communication buys nothing);
- newcomers show a flat repair curve (there is no commens to acquire);
- communities' domain shares stay undifferentiated (no niche forms).

Any of these is a result worth having. The last especially: four communities under
budget pressure failing to differentiate would say the selection mechanism is too
weak — a finding about the design we could act on.

---

## 8 · What comes after C, and what promotes a conjecture

**Everything C surfaces stays queued-conjecture.** Promotion requires a later rung
with priors registered *before* it runs. That rung is the **size sweep**, and its
question is the author's:

> Does the capacity a kytos *requires* stay invariant as the community grows?

Three outcomes, all informative. If specialization dominates, each unit needs
*less* as N grows (its niche narrows). If coordination dominates, each needs
*more* (it must model more peers). If the requirement holds flat across an order
of magnitude of N — **that is West's invariant terminal unit, discovered rather
than imposed**, which is what the E-series could not produce and what would make a
letter to West worth writing.

**The sensitivity discipline** (author, 2026-07-28) has a counterpart in West's own
theory and should be pre-registered in that form: in the WBE derivation the
**exponent** comes from network geometry while the **prefactor** carries
unit-level detail. So structural parameters (topology, overlap, how communication
grows with N) should move the exponent; unit-level parameters (capacity, decay
rate, budget) should move only the constant. Testing whether that split survives in
this substrate is itself a finding — and it is how we learn which presets can be
removed and which must be tuned.

Later rungs, unscheduled: permeable marks between communities; seeded
heterogeneity as a contrast arm (does innate difference produce types faster or
more durably than position alone?); a real-corpus corroboration.

---

## 9 · Build shape

**Reuse:** the round loop (`agon_evolution.run`); the attention economy
(`attention_economy.py`) including the temperament dial; world-scroll residence
and licensed M-moves (`world_scroll.py`, `m_steps.py`); the standing-question
register (`alternative_index.py`, `alternative_survey.py`) for the *ask* channel;
the mark primitive (`quotation_overlay.quote_existing_name` — attributed,
mention-not-use); forecast-before-outcome scoring (`resolving_membrane`'s
`PredictionLedger`); episode mining and stickiness (`agon_metalearning.py`); and
the E-series harness pattern — deterministic, seeded, custody-safe, canary-checked
(`west_experiment.py`).

**New:**

1. **Field generator** — domained, law-bearing, seeded, with a held-out stream.
2. **Provenance in materialization** — support sets for derived atoms.
   `model_materialization.py` is **not** in the protected set (verified
   2026-07-28), so this needs no authorization.
3. **Communication layer** — the four channels, the mark ledger, the
   who-asks-whom register.
4. **Community harness** — budget pool, per-domain allocation, lifecycle
   (birth · socialization · death).
5. **Instrument suite** — the measures of §7 plus the null tests.

**Deleted rather than extended:** `west_coordinator.py` — the switchboard this
design replaces with real communication.

**Disciplines carried forward from the E-series, which got these right:** one
fixed seed; a byte-determinism canary per run; custody-safe outputs; numbers-only
consoles; move ledgers that replay clean.

---

## 9a · What stages 1–2 actually found (build record, 2026-07-29)

*Stages 1 and 2 are built (11 commits; both gates pass). The build produced
findings that change what stage 3 must do first. They are recorded here because
they were earned, and because the next builder will otherwise repeat them.*

**Both gates pass, and one is thinner than it looks.** Stage 1: a unit induced
both reachable planted laws (at rounds 3 and 8) and outscored rivals. Stage 2:
support is recoverable, and the work clock and arrival clock retain **disjoint**
sets — each keeps exactly the atom the other discards.

**Four findings that bind stage 3:**

1. **The field saturates, and that is the real fragility.** A unit accumulates
   every atom of its aperture by roughly round 18; since anticipation excludes
   already-held facts, it then places only about **7 bets across 60 rounds** —
   42 rounds silent. The Stage 1 gate's ordering consequently flips at 2–3 of 10
   sampled seeds. **Fix the field before building the protocol:** more
   individuals per domain, or churn, so anticipation stays live.
2. **Accuracy is the wrong statistic at these bet volumes.** A rival winning 1 of
   1 outranks a learner winning 5 of 7. `resolving_membrane.PredictionLedger`
   already carries better instruments — `net_score`, a severity-weighted
   `k1_score` (which is §7's K1 as specified), and `accuracy → None` when no bets
   were placed, which is what makes an abstaining arm's fabricated 0.0 go away.
   **`c_membrane.MembraneLedger` should reuse it rather than fork it.**
3. **`shared` is shared in name only.** The domains have disjoint individuals, so
   there is *zero cross-domain atom overlap*; `shared` functions purely as the
   noise source that manufactures accidental laws. §3's "partial overlap" was
   therefore not achieved. **Overlap must become content** — shared individuals,
   or shared body/head relations — or the marks stage 3 introduces will have
   nothing transferable to carry.
4. **The two halves of stage 1–2 have no integration point.** The unit's
   inference is hand-rolled tuple matching; it never calls `materialize_egi`, so
   the provenance built in stage 2 is unused by the unit, and the unit shares no
   representation with the `world_scroll` / `agon_evolution` machinery §9 promises
   to reuse. **Left unfixed, this reproduces the E-series' "units never reasoned"
   failure in new clothes.** Wiring the unit to derive through
   `materialize_egi(provenance=…)` should be **stage 3's task 1, before the four
   channels.**

**Also fixed during the build, worth knowing:** `apertures_for` cycles with
period *k*, so 12 units over 4 domains yields only 4 distinct apertures —
violating premise 3 at the size §4 calls for. A guard now raises rather than
silently colliding; widening the scheme is a stage-3 decision.

---

## 9a-bis · The repairs (2026-07-29) — what changed, and what they taught

All four §9a findings are repaired, plus one regression the repairs themselves
introduced. Commits `44e3d84..6c77e3e` (eight).

- **The unit now reasons for real.** `Unit.anticipate()` renders held facts and
  laws as an EGI (laws as Horn cuts, the `model_revision.add_rule` idiom) and
  derives through `materialize_egi(provenance=…)`. Behaviour was *unchanged* at
  the time of the change — verified round-by-round over 120 rounds and two seeds
  — because the induced law set was already transitively closed at that field
  size. The wiring was honest before it was consequential.
- **Saturation is gone.** 40 individuals per domain; a unit that placed 0 bets
  after round 40 now keeps betting. A side effect worth noting: widening also
  *collapsed spurious induction*, because an accidental law now needs far more
  coincidence to survive.
- **Overlap carries content — after a correction.** The first attempt gave the
  field a *separate* shared namespace (`s1…s20`), disjoint from domain
  individuals. That was a specification error, and it silently reintroduced the
  exact defect an earlier fix wave had removed: a law of the form *domain-relation
  → shared* became structurally unsatisfiable, so the gate's wrong-law rival had a
  hit ceiling of zero again. The correction puts the overlap in the domains' **own
  individual lists** — a core `s1…s10` every domain knows, plus 30 private each.
  The rival now hits at 14/14 seeds (7–15 hits against 239–516 misses), and alpha
  and beta genuinely mention the same individuals.
- **A stable statistic exists** (`net_score`), and an abstainer no longer receives
  a fabricated `0.0` — `accuracy` returns `None` with no bets. Honest finding:
  across 14 seeds `net_score` and `accuracy` now agree 14/14, because repairs 2–3
  removed the low-volume regime that broke the ratio. So `net_score` did not
  *rescue* the gate; it was nonetheless required, since comparing against `None`
  would raise.

**What remains open** (final whole-set review, 2026-07-29, which independently
recomputed every figure below rather than trusting the build reports):

1. **The learner never misses** (0 misses at 14/14 seeds) — and the first
   diagnosis of this was half-wrong. It is not only `induce(max_pending=1)`'s
   strictness: it needs **both** that strictness *and* the field's
   exception-free determinism, since in a world without noise a true law can
   never miss. Worse, `max_pending` is an absolute count measured against a
   monotonically growing fact set, so it silently *tightens* over a run.
   Measured sensitivity: at `max_pending` 1 / 3 / 5 / 10 the learner's net score
   runs +55 / +4 / −167 / −2063, and **at 10 the gate fails outright** — so the
   gate's verdict currently turns on one knob, with a much thinner margin than a
   raw net-score comparison suggests. **The minimal honest fix is field noise
   (a fraction of consequents withheld or spurious) plus making the tolerance a
   *rate* rather than a count.** Loosening `max_pending` alone would manufacture
   failure by admitting laws already known to be refuted — degrading the learner
   instead of testing it.
2. **Overlap density is not yet a swept parameter** — the shared core is fixed
   at ten. It *is* reachable without editing the module (a caller can pass custom
   `Domain` lists), so this is a harness convenience rather than a design
   blocker, but §9b's conjecture wants this quantity as its x-axis.
3. **There is no retraction path.** `induce` only ever adds; nothing un-holds a
   law. Stage 3's *challenge* channel — the thing §5 says will finally let
   durability read *false* — currently has nothing to dispose into.
4. **The unit has no decay, no bounded model, and no attention economy**, though
   §4 promises all three, and `c_use` has no consumer outside its own test. Facts
   grow monotonically forever, which is the shared root of the saturation we
   fixed by widening and of induction's creeping strictness above.

**The review's single recommendation for stage 3, and it should be heeded
first:** replace the per-round EGIF serialize → parse → materialize cycle with a
persistent, incrementally-materialized unit model **before** building §7's cost
instrument. Today 58% of inference time is string round-tripping (22.2 ms parsing
against 15.7 ms materializing at end-of-run state). If the cost meter is built on
top of that, it will charge parsing and model size rather than reasoning —
*precisely the meter defect that invalidated the E-series, arriving in new
clothes at 48 units.*

---

## 9b · Conversation as the maintenance vehicle (author, 2026-07-29, reading B&L)

*The author, reading further in Berger & Luckmann, reports that they place
**conversation between individuals** at the centre of reality construction **and
maintenance**. That has a design consequence for §5's protocol, recorded here
before stage 3 is planned.*

B&L's claim is not that reality gets built by occasional dramatic acts of
legitimation. It is that the *continuous, unremarkable flow of everyday talk*
sustains it — and that most of what such talk confirms, it confirms **tacitly**,
by presupposing rather than asserting. Reality persists only while the
conversation that carries it continues. THE_COMMENS already holds the matching
half of this: the commens stands "sustained only by participation — if we do not
participate, it disappears."

**Where §5's ladder falls short.** Assert · ask · challenge · typify are all
**transactional** — discrete moves that *change* something. They model reality
*construction* well and reality *maintenance* not at all. A community whose
protocol carries only these has no way to represent the hum: the re-mention that
adds no fact but keeps a shared item alive.

**What follows for stage 3.** Two candidate consequences, neither yet ruled:

1. **A maintenance channel distinct from the revision channels** — a cheap
   re-mention that asserts nothing new but refreshes a mark's standing. Note this
   is not a new mechanism so much as a *social* reading of one we already have:
   the difference between work-use and arrival-use (§9a finding 2, and
   `c_use.py`) is exactly the difference between an item doing inferential labour
   and an item merely being kept in circulation. B&L suggest circulation is not
   idle — it is maintenance.
2. **Decay is what gives it teeth.** If marks decay, then a community that stops
   talking about something loses it, and *that* is B&L's thesis rendered
   operational rather than illustrated. It also predicts something measurable:
   the socialization clock (§2) should lengthen as the maintained body grows,
   because a newcomer must be talked into more.

**The honest caution.** This is a doctrinal reading, not a measured claim, and it
must not be smuggled into the instruments as though the experiment had shown it.
It belongs in stage 3's *design* rulings.

### RESOLVED (author, 2026-07-30): maintenance needs no separate channel

The question above — whether the protocol needs a maintenance channel distinct
from the revision channels — is **answered by the mechanism the challenge ruling
produced**, and answered in the negative.

The author's two rulings compose. First: *doubt moving to inquiry means both an
internal assessment and an external one*, so a challenged law provokes the author
to re-run its **own induction criterion** against its **current** record, not
merely to look up one disputed individual. Then: *this provides a mechanism for
maintenance and revision, too.*

It does, and the two turn out to be one act read by its outcome:

- **Maintenance** is a re-assessment that **confirms**. A law that keeps meeting
  its criterion as the record grows has been actively re-affirmed, not merely left
  standing by inertia — which is precisely B&L's point that reality persists by
  continuous re-affirmation rather than by momentum.
- **Revision** is the same re-assessment when it **disconfirms**. The unit's own
  accumulated experience has turned against a law it once held, and it corrects.

So there is no third channel to build. What the design *does* still need is for
re-assessment to run **spontaneously and not only under provocation**: if a law is
re-tested only when a peer challenges it, maintenance is purely reactive, and
nothing is maintained that nobody happens to dispute. **Periodic self-re-assessment
— a unit re-testing its held laws against its grown record at intervals — is the
internal arm of maintenance**, and it is cheap, since the criterion already exists.

Two consequences worth carrying. It closes the gap flagged during the build that
`induce` only ever *adds* and never re-tests an admitted law. And it gives
disuse-decay a principled sibling: a law fades not only when nothing re-delivers
it, but when the record it accumulated stops supporting it — which is nearer the
project's own doctrine that knowledge exists only while it works.

### The join: conversation density is the variable both frameworks name

*The author, same sitting: "in West, one important consequence of closer physical
proximity was the increased density of conversation."*

That observation joins the two halves of this design at their mechanism, and it
is the sharpest thing said about the program so far. Bettencourt and West
attribute cities' **superlinear** socioeconomic output not to infrastructure — which
scales *sub*linearly — but to **interaction density**: packing people closer
multiplies the opportunities for exchange faster than population grows. B&L,
arriving from sociology, say the exchange itself is what constructs and maintains
reality. So the two traditions are not merely compatible; **they name the same
variable from opposite ends.** West measures its consequence; B&L describes its
function.

**What this fixes in the design.** §3 treated the field's domains as the "volume
to be filled" and took *space-filling* as the correspondence to West's first
pillar. That was right but shallow. The deeper correspondence is now available:
**aperture overlap is our proximity.** Two units whose apertures share a domain
have shared referents and can therefore say something to each other that lands;
two units with disjoint apertures have nothing to converse *about*, however
freely the protocol lets them talk. Overlap density is conversation density is
West's proximity.

Three consequences, all for stage 3's rulings rather than for any instrument yet:

1. **The scaling sweep should vary overlap density, not only N.** If interaction
   density is the mechanism, then community size alone is the wrong x-axis —
   the same twelve units at different overlap densities should scale differently,
   and *that* comparison is the one West's framework predicts something about.
2. **Bounded attention is what makes it non-trivial.** §4 gives each unit only
   two or three consultations per round. Overlap raises what a unit *could*
   discuss; the budget caps what it *does*. The interesting regime is where those
   two conflict — which is also where "whom to ask" (typification) starts to pay.
3. **§9a finding 3 is more load-bearing than it looked.** "`shared` is shared in
   name only" was recorded as a defect about marks having nothing to carry. Read
   through this join, it is worse and better than that: with disjoint individuals
   there is no *proximity at all*, so the design as built could not have produced
   an interaction-density effect even in principle. The repair that gives domains
   a shared individual pool is therefore not housekeeping — it builds the
   substrate the central conjecture needs.

**Still a conjecture.** Nothing here has been measured, and the honest caution
above applies with full force: a mechanism named by two traditions is a good
place to look, not evidence of what will be found.

---

## 9c · Memory has tiers, and the lost leaves residue (author, 2026-07-30)

Two rulings about memory, both of which bear on what "retract" and "decay" may
mean. They generalize beyond this experiment; recorded here because the challenge
lifecycle needed them immediately.

### (i) Knowing-about is not holding-in-use — so retraction must archive, not erase

The author: *"I could say I know about trepanning because I've looked it up, but
not because I perform it or have had it performed on me. The arcane, out-of-use,
formerly in practice but now obsolete, deprecated, frankly wrong must remain in
some form to inform history, recoverable for study and admonition — but it cannot
consume much in the way of active resources. So: libraries, archives, museums."*

This forbids the erasure semantics the build has been using. A defeated law, a
decayed atom, a superseded generalization must remain **recoverable**, while
costing nothing to hold. Two tiers, distinguished by what they cost and what they
license:

- **Active** — held, licensing inference, charged for.
- **Archival** — recoverable and inspectable, licensing nothing, costing nothing.

**The project already has the archival tier, and it already has the cost
property.** Arisbe's quotation apparatus is *mention, never use*: a quoted law is
"present without force," which is exactly the third tense the `swan_third_tense`
exemplar demonstrates — a withdrawn law standing on the sheet as exhibit. And
under B-min the interpreters are **opaque to a quotation area**: no rule operates
inside the oval, and the peel and the materializer skip it. So an archived item is
structurally excluded from inference rather than merely flagged, which is precisely
"cannot consume much in the way of active resources," enforced rather than
promised.

**The consequence for this build:** retraction (by corroborated challenge, by
internal re-assessment, or by decay) should **demote a law to mention** rather than
delete it. Nothing in the record is destroyed; it stops having force. That also
makes the honesty ledger better — a run can report what a community *stopped*
believing, which erasure loses.

### (ii) Residue permits reconstruction

The author: *"the simple fact that a pattern of thinking was once in use leaves
something like a genetic residue that permits reconstruction of a sort even if
direct observation or evidence is missing"* — with proto-Indo-European and the
reconstruction of population history from gene analysis as the exemplars.

This names the **comparative method**: no one ever observed PIE, yet regular
correspondences among its daughters license reconstructing it. The analogue here is
concrete, and the machinery for it exists as of stage 2. **Provenance records the
support behind every derived fact.** A law that has been retracted therefore leaves
its fingerprints: the atoms it derived remain in the record, each carrying the
premises it was derived from. The law is gone; its effects and their supports are
not.

Two consequences, one immediate and one a genuine research question:

- **Immediate:** this is a second argument against erasure. Even if an archived law
  were discarded, its residue in the derived record would remain — so the record is
  already partly reconstructible, and pretending a retraction is clean would be
  false to what the data holds.
- **The research question, and it is a good one:** *can a community reconstruct a
  law that no member still holds, from the systematic correspondences among what
  its members derived while holding it?* That is the comparative method applied to
  a population of reasoners rather than to daughter languages, and this design —
  several units, overlapping apertures, provenance-carrying records, laws that can
  die — is nearly the right instrument for asking it. Queued as a conjecture, not
  a claim; it would need a stage of its own.

---

## 9d · Corroboration takes two independent witnesses (author, 2026-07-30)

Task 5e measured elimination-by-corroboration firing **0 of 66** times in the
bounded-attention arm and **0** in the induce arm, and found a unit corroborating
its own doubt with its own inscription — `challenge` scans by content, so a unit
publishes challenges against laws it also holds, and that mark was taking the
challenger's slot *and* counting as the corroborating voice. It sat in the live
set of 8 of 8 corroborations at seed 1 and eliminated 64 of 64 true laws at an
age of exactly one round.

The author ruled:

> Corroboration exists largely to generate and build confidence in the
> independent views that build a socially available, objectified reality.
> Repeating one's own observation does not do this. So, 2 needs at least 2
> independent witnesses.

The ground is Berger & Luckmann's, not arithmetic. Corroboration earns its place
in this design because it builds a **socially available, objectified** reality,
and a record that repeats itself contributes nothing to that. A unit's own
inscription therefore never counts as a corroborating voice.

**The consequence falls on the field, not on the disposition rule.**
`apertures_for` assigns unit *i* domains *i* and *i+1* (mod k), so every domain
is witnessed by exactly two units at any community size, and two independent
witnesses beyond the holder are arithmetically unreachable. The rule was right
and the community was too small to satisfy it.

**The repair adds units, never aperture width.** Task 5b-fix measured
three-domain apertures as degenerate — all 168 true and 56 converse laws lost,
both arms net 0. Assigning each unit a distinct 2-domain *combination* keeps
per-unit load fixed and raises the witness count instead:

| domains | distinct 2-domain apertures | units witnessing each domain |
|---|---|---|
| 4 | 6 | 3 |
| 5 | 10 | 4 |
| 6 | 15 | 5 |

At this spec's four domains that fixes the community at **six units**, with every
domain witnessed by exactly three — the holder, the challenger, and one
independent corroborator, with nothing to spare.

Which makes community size a *derived* quantity rather than a guess, and answers
§10's open question in one direction the design did not anticipate: **the minimum
viable community is set by what corroboration requires.** With aperture width
*w*, domain count *D*, and a demand of three witnesses per domain, the floor sits
at *U = 3D/w*. A community below it cannot objectivate anything, however well its
units reason.

Two readings stay open and reversible. The controller reads the **challenger as
one of the two witnesses** — preserving Task 5b's rule that its evidence must not
count *twice*, since it counts once and still cannot close its own doubt alone —
which is what puts the floor at three witnesses rather than four. And Task 5e's
`corroboration_window` of 5 rounds became load-bearing (it decides 41 to 66 of
every 66 doubts, every disposal falling at age exactly 5) while remaining
unmeasured; 3, 5 and 8 are under measurement, and the default stays the author's
to set.

## 10 · Scale, decomposition, and open questions

**Scale, stated plainly.** Four communities × ~12 units = ~48 loop instances per
world, doubled by the mute-twin control, per configuration. This is an order of
magnitude beyond the E-series' per-run cost, and the round loop is known
super-linear in |M|. Two consequences the plan must face: the per-unit models
must stay small (decay does that work), and a smoke configuration — two
communities × four units, few rounds — should exist and be the default for
development, with full runs reserved and launched deliberately.

**This design exceeds one implementation plan.** It decomposes into stages that
can be built and gated independently, and the first plan should cover only the
first two:

1. **Field + unit** — the domained law-bearing generator, apertures, and a single
   unit that predicts and is scored at its membrane. Gate: one unit measurably
   learns a planted law and its prediction score rises.
2. **Provenance** — support sets in materialization, and *use* redefined as
   participation in work. Gate: an atom's support is recoverable; a decay clock
   driven by work rather than arrival changes what survives.
3. **Communication** — the four channels, the mark ledger, the who-asks-whom
   register. Gate: the live world diverges measurably from its mute twin.
4. **Community + selection** — budget pool, per-domain allocation, lifecycle.
   Gate: four communities run to completion deterministically; a community can
   fail.
5. **Instruments + null** — the measures and the null tests.

**Open questions for the plan:**

- The exact form of a "prediction" a unit emits, and how a domain's deliverance
  stream is partitioned into scored and held-out.
- **How "required capacity" is measured** (§8's headline). Two candidates: sweep
  the capacity bound and locate where predictive performance degrades, or measure
  realized utilization of an over-provisioned register. The first answers the
  question posed but multiplies runs; the second is cheap but measures what a unit
  *used*, not what it *needed*. Resolve before the size sweep, not before C.
- How a newcomer is initialized (empty M? a starter aperture? sponsored by a
  resident?) — this materially affects the socialization clock.
- Mortality's exact trigger (budget starvation only, or also decay exhaustion).
- Whether challenge outcomes feed typification directly, or only through
  subsequent uptake.
- Run length: how many rounds before "nothing emerged" may honestly be declared.

*Design ruled section by section, 2026-07-28. Assistant-drafted from the
author's rulings; the premises, the series shape, the selection ruling, the
lifecycle addition, and the capacity question are his.*
