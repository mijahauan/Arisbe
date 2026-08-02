# The D-series — building the stake

**Design sitting, opened by the author 2026-08-02.** His ruling: *we should attempt to
build the stake — we've come close to a good idea of what the autonomous system lacks;
we just need to provide it*, seeking **a minimal set of outside parameters that will
provide what's needed for the semiotic exploration of kytē to do the rest.**

Nothing here is built. The four-parameter proposal in §3 is the assistant's, for the
author's amendment; the framing in §1–2 is his.

Companions: [Examination VIII](2026-08-01-examination-viii-the-west-mapping-on-trial.md)
(what the autonomous form lacks, measured) ·
[the received-world sitting](2026-08-01-the-received-world-boundary-controls-and-socialization.md)
(environment-first) · [FROM_THERMODYNAMICS_TO_SEMIOSIS](../../FROM_THERMODYNAMICS_TO_SEMIOSIS.md)
(Secondness → Thirdness) · [THE_MEASURE_OF_KNOWLEDGE](../../THE_MEASURE_OF_KNOWLEDGE.md) §1
(the definition this is meant to make instrumentable).

---

## 1 · The framing: the user was the environment

**The author's observation, and it unifies most of what Examination VIII found.** Arisbe
in its basic incarnation relied entirely on the motivation and interest of the **user**.
Extending the kytos model toward autonomy removed that person and **replaced nothing**:

| What the autonomous form lacks | Who supplied it before |
|---|---|
| genuine doubt | the user was actually in doubt |
| severity | the user actually cared, and differentially |
| a situation | the user was in one |
| stake | the user bore the cost of being wrong |
| a moving threshold | the user's interest rose and fell |

Every null of the West program traces to that single removal: units with nothing at
stake, doubt as a scheduling signal rather than an irritation, typification inert, no
exponent, and an attention economy that can only damp because nothing outside ever
insists.

So **the environment is not scenery to add behind the units. It is the replacement for
what the user was doing** — a far more demanding specification than "clock, capacities,
contested source", because it says what those must accomplish: supply doubt that is
genuine and stakes that are real.

**The verdict this passes on the two branches.** Under §1's ruled definition — knowledge
is a *situation* in which mediation brought the doubt that motivated it to rest, not
confined to one kytos — **interactive Arisbe already produces knowledge**: the user's
doubt, the calculus's mediation, resolved between them across two kytē. The autonomous
form does not yet, because no doubt in it is anything's doubt. That inverts the usual
reading: the interactive form is the **richer** system and the autonomous one its
impoverished derivative, impoverished in exactly the component that makes knowledge
possible. (The oracle-notes loop, `oracle_notes.py`, is the branch that went the other
way deliberately — the human re-installed as the environment on purpose.)

## 2 · The axis that was conflated

**Autonomy and stake are different axes, and the program bought the first while assuming
the second came with it.** Conway's Life is perfectly autonomous and epistemically dead:
no doubt, no stake, nothing at issue for anything. Moving toward self-running dynamics
buys independence from the user *and* silently discards what the user was providing. The
West program then measured a system that was autonomous and stakeless, and found nothing
— which is what such a system must yield.

The option to refuse is the third one, which is where the project has been: **an
autonomous form that looks independent while quietly depending on stakes nobody
supplied.**

## 3 · The proposal: four numbers and one rule, all outside

*Assistant's, for the author's amendment.*

**The conversion that makes this cheap.** The E-series already has a meter charging
`Σ|M|` per round; `MembraneLedger` already scores hits and misses; `Field.deliver`
already delivers and `anticipate` already anticipates. All of it is an **observer's
scorecard** — computed beside the system, read by us, affecting nothing. *Make the meter
a subtraction instead of a reading and it stops being an instrument and becomes a
world.* Stake, metabolism, and West's β follow from code already written. Nothing was
ever subtracted from anything; that is the whole omission.

| | Parameter | What it is |
|---|---|---|
| **E1** | source quantity + replenishment rate | how much sustenance exists per round, bounded |
| **E2** | maintenance tariff | price per unit of model held, per round |
| **E3** | reach tariff | price per mark read |
| **E4** | allocation rule | how E1 is divided among claimants — **the world's, not ours** |

**The load-bearing constraint: no unit parameter is set at all.** Not capacity, not rate,
not aperture width, not lifespan. They fall out of what a unit can afford at prevailing
prices. This is the author's own ruling of 2026-08-01, made to resolve the condition
list's A5 ⟂ A8 contradiction — **fix the price, let the quantum fall out** — and that the
condition-list repair and the D-series design principle turn out to be the same rule is
some evidence both are right.

## 4 · Pre-registered: what must FOLLOW, not be built

"Install the problem, never the solution" gets its teeth here. Each item below is
currently a hand-built mechanism that should instead be a **consequence**, and each is
therefore a prediction that can fail.

- **Mortality** — a reserve reaching zero. No `die()`, no TTL, no lifespan parameter.
- **Selection between communities** — a bounded source is a niche too small for all.
  *Extinction is running out*; no external fitness scorer, which premise 1 forbids.
- **Sensitization / obsession.** The measured gap (`_score` damps by
  `attempt_decay ** attempts`; nothing rises with repeated non-resolution) should need no
  new term: as reserves fall, an unresolved doubt is income not earned, so urgency rises
  on its own. **If sensitization must be added by hand, this prediction failed** — and
  the gap was independent after all, rather than a symptom of the stake absence.
- **Typification** — with reading priced and budgets bounded, a unit cannot read
  everyone; it must choose whom, and the pattern of whom-it-reads-often *is* a proximity
  structure.
- **The reach gradient (condition 9)** — the conjecture most worth testing. If
  typification emerges from priced reading, the accessibility structure is **grown rather
  than installed**, and its dimension is measurable from the realized topology. That
  satisfies the falsifiability bar honestly: measure `H` from the substrate at time *t*,
  **predict** β, then check — two independent measurements rather than a fitted
  parameter. A fitted θ is a free parameter wearing a law's clothes.

## 5 · Why this is the Secondness → Thirdness transition, not a simulation of it

**E2 and E3 are pure Secondness.** The tariff takes, regardless of what any unit believes
about it — brute reaction, no options, indifferent to interpretation. The author's
**Intent 0**.

**E4 is where Thirdness must earn its keep.** If income arrives only when an anticipation
meets an arrival, a sign that mediates well pays and one that mediates badly costs. That
answers Bickhard's question — *when does an indication acquire a truth condition for the
system itself* — minimally: **when acting on it wrongly shortens your life.** The truth
condition becomes the system's own because the system, not an observer, bears the
outcome.

**And the standing falsifier finally bites.** *Ablate the putative sign* — occlude the
marks and see whether units survive as well. Today that test is unrunnable because
nothing survives or fails. With a reserve, survival is the measurement.

## 6 · Where a designer could cheat — stated before building, not after

- **E4 is the dangerous parameter.** Whoever writes the allocation rule can smuggle in
  the answer: reward the behaviour we hoped to see and call it emergent. The discipline
  is that the world scores **matches between anticipation and delivery and nothing else**
  — no credit for communicating, corroborating, or typifying. If those pay, they must pay
  only by producing better anticipations.
- **"Success" must not be our standard.** That is the trepanning problem one level up
  (THE_MEASURE_OF_KNOWLEDGE §1(d)): the field delivers, a match is a match, and we get no
  vote.
- **Pre-register.** Four numbers is a small enough space to tune until something appears.
  Priors first, as in every prior run.

## 7 · Sequencing

1. This sitting → a full design spec, the author amending §3 and §4.
2. **Step 3 (seed by DC+ · INS · IT+) falls out naturally** and should be written into
   the same design: under a priced world, a unit's initial model needs a **price and a
   provenance** rather than an assignment. The earlier sketch that routed communication
   through aperture overlap is superseded — the author's Berger & Luckmann point supplies
   a better-grounded structure, *typification rising and influence waning with social
   distance*, which is the graded accessibility condition 9 needs, arriving from a
   tributary already graded `ratified-doctrine`.
3. **Step 4 (retire `Unit.peers`)** — independent of the above, with its own before/after
   measurement, on the standing rule that a moved figure has exactly one cause.
