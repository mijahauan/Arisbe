# The Bootstrap and Directed Engagement

> **What this is.** Design-of-record for the step-back the author took on 2026-07-17, with
> the S3 hinge (the drawn second-order convention reading back, see
> SECOND_ORDER_CORE_OPENING §4) discharged at B-min: Arisbe considered *as a whole*, against
> the author's premise that **thought bootstraps** — set up from the outside, a chain of
> semiosis unfolds that models the world through interaction, and **doubt** (an experienced
> difference between experience and the modeling) drives the chain forward, re-modeling and
> re-interacting as it goes. The author sketched the simplest setup that would get the
> bootstrap rolling — a **Minimal Predictive Automaton** — and proposed treating **Arisbe
> itself as a proposition in a wider Endoporeutic Game (EPG)**.
>
> This doc records (§1) how much of that automaton is already built and where it lives;
> (§2) what is genuinely missing, and the *Peircean* warrant for building it; (§3) the
> staged path to the missing piece — **directed engagement**, the action arm; (§4) the
> reflexive move and its licence; (§5) the named decisions. The reader-facing concordance
> survey (active inference, cybernetics, evolutionary epistemology, biosemiotics, belief
> revision) lives in the book: [CONTRIBUTION_AND_PRIOR_ART.md](CONTRIBUTION_AND_PRIOR_ART.md)
> §"Concordances".
>
> **Companions:** [AUTOMATED_MODEL_DEVELOPMENT.md](AUTOMATED_MODEL_DEVELOPMENT.md) (the loop)
> · [AUTOMATED_ENDOPOREUTIC_GAME.md](AUTOMATED_ENDOPOREUTIC_GAME.md) (the roles, the
> membranes, and §4d — the methodeutic surround this doc extends) ·
> [CHAIN_OF_SEMIOSIS.md](CHAIN_OF_SEMIOSIS.md) (the grounding) ·
> [THE_MEASURE_OF_KNOWLEDGE.md](THE_MEASURE_OF_KNOWLEDGE.md) (2026-07-17: the doctrine
> read *off* this machinery — knowledge defined and measured, its fractal levels, the
> ethical and pedagogical corollaries).
>
> *Written 2026-07-17. Design only — nothing new is built by this doc; everything cited as
> built carries its module name. Readings that are the assistant's are flagged as such.*

---

## 1 · The Minimal Predictive Automaton, mapped onto what is built

The author's sketch: a system initialized from outside with a sensor space *S*, an action
space *A*, and an internal transition model *M*; a perception–action cycle (read sign →
generate interpretant-as-prediction → interact → experience); **doubt defined strictly as
prediction error** (the delta between predicted and experienced next state); and remodeling
(abduction) triggered exactly when doubt is nonzero.

**Lineage (attribution, recorded 2026-07-17).** The MPA is not a novel architecture but the
**convergence point of four traditions**, and the doc owes each its credit: **American
pragmatism** — Peirce's *The Fixation of Belief* (1877) formalized the engine (inquiry
driven by the *irritation of doubt*, ending in a settled habit of action), and Dewey's
*The Reflex Arc Concept in Psychology* (1896) dismantled linear stimulus–response in favor
of the continuous perception–action loop (our actions dictate what stimuli we receive);
**cybernetics** — Wiener (1948) made feedback the general mechanism, and Ashby's
**Homeostat** (1948) was the first *physical* implementation of remodeling driven by
environmental friction (ultrastability: out-of-bounds variables trigger re-randomized
internal wiring until equilibrium returns — doubt as a voltage); **predictive processing**
— Helmholtz's *unconscious inference* (1860s) through Friston's free-energy principle
(2006–): free energy *is* doubt, minimized either by updating the model (perceptual
inference) or by acting on the world (active inference — the action arm this doc stages);
**machine learning** — Schmidhuber's artificial curiosity (reward = compression progress,
the agent *seeking* doubt to resolve it) and temporal-difference learning, whose TD error
is the doubt-delta exactly (and TD error = 0 is Peirce's settled belief). Full entries in
[CONTRIBUTION_AND_PRIOR_ART.md](CONTRIBUTION_AND_PRIOR_ART.md) §"Concordances".

Laid against the codebase, the automaton is about four-fifths built — scattered, under
other names:

| MPA element | Arisbe realization | Status |
|---|---|---|
| Sensor space *S* | Membrane items — `LiveSource.fetch` delivering `DiscourseItem` / `ResolvingItem` / `WikidataStatement` per poll | BUILT |
| Model *M* | The resident M (world-scroll cells at even depth, read via `world_scroll.m_view`); its laws are the theory | BUILT |
| Interpretant as prediction | The peel — `semantic_game.evaluate`; and literally in `resolving_membrane.py`: `ResolvingFeed` records M's forecast in the `PredictionLedger` **before** the outcome is folded in | BUILT |
| Doubt *D* > 0 | A FALSE verdict, a prediction miss, a counterexample. Kleene UNKNOWN is an honest *abstention*, not doubt — a distinction the MPA's arithmetic delta lacks | BUILT |
| Remodeling (abduction) | `revise_with_disposition` — and the disposition taxonomy is a *structured, recorded, warranted* update rule, richer than a matrix overwrite: each revision carries its Peircean mode (induction/deduction/abduction/convention) and its executed derivation | BUILT |
| Forgetting | Disuse-decay (`UsageLedger`, atom-level) — the MPA has no analogue; in Arisbe it is the only bound on the unbounded sheet (AUTOMATED_MODEL_DEVELOPMENT §"bounded only by selection-from-outside") | BUILT |
| Doubt-directed attention | The irritation pole: `attention_brief` (M's thin spots), the warm-set tropism (`tropism.py`, runs 2–3), and the docket of doubts (`query_docket.py` — articulated doubt → probe) | BUILT (partially — see §2) |
| **Growth of *S* and *A* themselves** | *S* grows: open-vocabulary membranes, label resolution turning opaque ids legible, the horizon promoting the not-yet-legible; *A* grows: the crawl growing its own frontier, the docket's Q-tiers shrinking `inexpressible`; the **sign-space** grows: the alphabet widening under INS, hypostatic abstraction at B-min | PARTIAL (see §1.1) |
| **Action space *A* (exercised)** | **Missing.** Arisbe predicts, probes, and revises — but it never *intervenes*: no reach is chosen by expected yield, and nothing pushes back on the source | NOT BUILT |

Three places where Arisbe's shape is *deliberately richer* than the automaton, worth
keeping: the three-valued verdict (UNKNOWN ≠ doubt — an open-world abstention the
delta-arithmetic collapses); the disposition taxonomy (remodeling that *records what kind
of move it was*, so the chain of semiosis stays legible — the whole point of "moving
pictures of thought" over a weight update); and the update rule itself — the MPA, like
Conway's Life, updates by a **fixed rule**, where Arisbe's remodeling is a **negotiated
disposition** ("outcomes are negotiable, not determined" —
AUTOMATED_MODEL_DEVELOPMENT §1, which carries the full Game-of-Life correspondence and
its instructive breaks: death = relinquishment/decay, and the bounded plane vs. the
unbounded sheet bounded only by selection from outside).

### 1.1 · Finite, not fixed — action changes the spaces themselves

The author's clarification (2026-07-17, second sitting): the MPA's *S* and *A* are finite
for practical sense, but **finite need not mean fixed** — and the interesting part of the
bootstrap centers exactly there: **the automaton's action results in a change in both
spaces.** A sketch whose *S* and *A* are frozen a-priori architecture can converge but
cannot *develop*; a system whose acting wins it new distinctions to sense and new probes
to make is the one whose chain of semiosis actually unfolds. This is the reflexive loop
predictive processing calls **structure learning** (model *expansion*, not parameter
update) — and it is Peirce before it is Friston: *symbols grow* — "they come into being
by development out of other signs" (CP 2.302). A new sign is simultaneously a new sensor
(a distinction the system can now register) and a new actuator (a probe it can now voice).

Arisbe already grows all three spaces, each by a named mechanism, each **bounded by
selection** rather than frozen:

- ***S* grows** — the membranes are open-vocabulary by design (a required property of a
  good membrane, AUTOMATED_ENDOPOREUTIC_GAME §4b); label resolution turns opaque ids into
  legible names; and the **horizon** is precisely the staging area for sensor-space
  growth — what came back not-yet-legible, retained until legibility improves (which is
  why rung 1 makes it a first-class register: it is where tomorrow's *S* waits).
- ***A* grows** — the crawl grows its own frontier from what it finds
  (`RotatingWikidataSource.crawl`: entity-valued answers become new probeable entities);
  the docket's Q2/Q3 tiers exist to shrink `inexpressible`, i.e. to make previously
  unvoiceable wants voiceable — action-space growth as an explicit design goal.
- **The sign-space grows** — the alphabet widens under lawful INS (a rule application can
  introduce vocabulary); and the second-order crossing at B-min is sign-space growth in
  its strongest form: **hypostatic abstraction turns yesterday's predicate into today's
  subject** — a thing the system could only *say* becomes a thing it can *address, probe,
  and quote*. The crossing is not a separate research thread from the bootstrap; it is
  the bootstrap's third axis.

**The guard, one level up.** Growing spaces re-create the unbounded-sheet problem for the
spaces themselves, and the same answer applies: growth must be **selected, not merely
accreted** — the frontier caps with drops *counted* (`frontier_cap`, `per_entity_cap`),
the negative label cache, and disuse-decay are to *S* and *A* what decay is to M. A
directed-engagement design (§3) that lets action enlarge the spaces must inherit this
discipline: every growth channel carries a bound, and everything dropped at a bound is
counted, never silently truncated.

## 2 · What the bootstrap still lacks — and the Peircean warrant for building it

**(a) The action arm.** The automaton's step 3 ("Interact: execute action A") has no full
counterpart. AUTOMATED_ENDOPOREUTIC_GAME §4c states it plainly: the relation to the live
source is "*ingestion, not mutual co-evolution* — M changes in response to Wikidata, but
does not (yet) push back on it." And §4d already stakes out the ground: the
"eventual directed-engagement piece implements the rest: the musement pole, the
economy-of-research ordering of reaches, and the horizon as a first-class, retained
register." This doc's §3 is the staged path onto that ground.

**(b) Action selection is Peirce's own economy of research.** Choosing *which* reach to
make next — which entity to re-poll, which want on the docket to voice, which experiment
to run — is the problem Peirce solved in outline in "Note on the Theory of the Economy of
Research" (1879): allocate inquiry by **cost against expected reduction of doubt**. This
is the 19th-century statement of what the machine-learning literature now calls active
learning / optimal experiment design. The warrant for building the action arm is therefore
*native to Peirce*, not imported from the predictive-processing neighbors — the neighbors
corroborate; Peirce mandates. *(Assistant's reading, flagged; the author should ratify the
framing before it hardens into the doc spine — see §5.)*

**(c) The noisy-TV guard.** Once actions are chosen by expected doubt-reduction, the
target must be **learning progress** (the *rate of improvement* of prediction), never raw
prediction error: a pure-noise source generates maximal error forever and would trap an
error-seeking prober (the "noisy-TV problem" of the artificial-curiosity literature —
Schmidhuber, Oudeyer). Arisbe already half-guards this: Kleene UNKNOWN abstains rather
than mis-predicting, decay expels what never re-delivers, and the standing rule that
**poise must never become a target** (AUTOMATED_ENDOPOREUTIC_GAME §4d) is the same
Goodhart instinct stated for the run as a whole. The design rule for §3: *order reaches by
expected learning progress per unit cost, and let a want that never yields settle into the
docket's `inexpressible` residue rather than being re-probed forever.*

**(d) Against the blank slate.** The MPA seeds M "randomly or blank." That is the one
un-Peircean element of the sketch: critical common-sensism denies the tabula rasa — we
begin laden with instinct and un-criticized background belief, and inquiry starts *in
medias res*. Arisbe's actual bootstrap is the more faithful one: **the low-warrant import
floor** (corpus seeds, ontology imports, curated pools — see
[EXTERNAL_SOURCES_AND_IMPORT.md](EXTERNAL_SOURCES_AND_IMPORT.md)) *is* the "outside
setup," and the blank sheet's first act is already ruled (DC+ — see
[MATHEMATICS_FROM_THE_SHEET.md](MATHEMATICS_FROM_THE_SHEET.md)). Conclusion: do not chase
the blank automaton; the bootstrap problem Arisbe should own is not "start from nothing"
but "start from low warrant and *earn*."

## 3 · The staged path to directed engagement

Design only; each rung is a separate authorization. Rung 0 is the standing base.

**Rung 0 — built (the irritation pole).** `attention_brief` (proto-tropism), the warm-set
re-poll tropism (`tropism.py`; runs 2–3 showed re-poll alone cannot bound the sheet —
the RUN_3 findings F1″/F2″, Part III ledger of AUTOMATED_ENDOPOREUTIC_GAME), and the
docket of doubts (`query_docket.py` — UNKNOWN transcript, thin spots, and unwitnessed
consequences registered as *wants*, prioritized fewest-attempts → oldest, settled per
segment, with the honest `inexpressible` residue).

**Rung 1 — the economy of research (ordering the reaches).** Replace the docket's
mechanical priority with a cost/yield ordering, and widen what feeds it:

- Feed the meta-learning instruments back into the docket: `unresolved_frontier` and
  `friction_map` (`agon_metalearning.py`) name exactly the claims where engagement is
  likely fertile — today they are read by humans in run logs, never by the prober. This
  is the cheap, loop-closing edge: **the game studying the game, then steering it.**
- Score each want by expected learning progress per unit cost (a probe that has repeatedly
  yielded nothing decays in priority — the noisy-TV guard of §2c), rather than
  fewest-attempts → oldest.
- Add the **musement pole** (the pull, complementing irritation's push — Peirce's *A
  Neglected Argument*): a bounded fraction of reaches allocated off-docket, at low cost,
  to keep variation alive (the annealing/boredom-detector idea of
  AUTOMATED_ENDOPOREUTIC_GAME Part I §4 item 4).
- Make the **horizon** a first-class, retained register (what came back not-yet-legible,
  kept and re-attempted as legibility improves — the sensor-space growth register of
  §1.1) rather than a per-poll report field.

**Rung 2 — mutual co-evolution (pushing back).** The full functional circle: M's contested
frontier surfaced *to the source* — e.g. suggested edits / flagged inconsistencies offered
back to the wiki-world — so the world and the model shape each other. Named in
AUTOMATED_ENDOPOREUTIC_GAME §4c as the future edge. This rung has real outward-facing
consequences (Arisbe would be *acting* on a shared world) and therefore needs its own
ethics-and-etiquette design before any build; nothing below rung 2 acts outside Arisbe's
own polls.

**Rung 1 — AUTHORIZED 2026-07-17 (the arithmetic stage), with pre-registered criteria.**
The author chose the staging **arithmetic → vault → author-as-oracle** (each field a
separate cycle; the horizon register deliberately waits for the vault, where illegibility
genuinely exists) and the architecture **attention socket + world #1**: a world-agnostic
`AttentionEconomy` + `ProbeDirectedFeed` pair, with a computed-arithmetic world
(`arithmetic_world.py`) as the first field — deterministic, CI-safe, zero NL, and with a
real cost model (probing *n* costs what primality testing costs). The headline trajectory:
**Fermat's 1640 conjecture** (every 2^2^n + 1 is prime) proposed, confirmed at F0–F4,
**refuted at F5 = 641 × 6 700 417** (Euler 1732) — reachable under budget only if
attention spends on severity rather than cheap re-confirmation. Criteria registered
*before* the build, in the run-log discipline:

- **S1 (economy).** Under a fixed probe budget, the economy-ordered arm reaches the
  Fermat refutation in strictly fewer probes than FIFO and random arms
  (`run_ablation`, fresh feeds per arm).
- **S2 (noisy TV).** The planted patternless predicate's probe-kind decays below every
  productive kind's priority within the run — the noise never captures attention.
- **S3 (musement).** A planted regularity unreachable from the docket's wants is found
  with the musement pole on and not found (same budget) with it off.
- **S4 (determinism).** Identical configurations yield identical trajectories, and the
  probe journal replays offline — the determinism canary.
- **S5 (discipline).** Zero protected-module changes; the produced UoD passes the
  polarity gate; every growth channel bounded with drops counted.

**What rung 1 is *not*:** it is not a new membrane, a new referee, or a change to the
calculus. The mode contract and the low-warrant floor (the "border guards" of
AUTOMATED_ENDOPOREUTIC_GAME §4d) are untouched; only the *conduct* of inquiry — Peirce's
methodeutic, explicitly outside the game — gains machinery. Nothing auto-promotes;
progression, not progress.

**Build record (2026-07-17).** All five pre-registered criteria HELD. **S1 HELD**: under
identical 90-round budgets (`probe_budget=1`), the economy arm refuted Fermat's conjecture
at **round 6**; the FIFO arm **never refuted within 90 rounds**; the scatter arm **never
within 90** either (an extended 300-round probe showed scatter refuting at round 127, FIFO
still never) — the strict ordering economy < scatter < FIFO holds via the None-branch on the
two slower arms. (The FIFO arm is degenerate by construction — it re-probes `("confirm", 0)`
every round, so "never refuted" is a priori for that arm; the meaningful S1 margin is
economy's 6 against scatter's 127-in-300.) **S2 HELD**, with an honest mechanism
disclosure: as built there is no separate `coin` probe-kind — coin atoms ride inside every
probe's atom conjunction (`atoms_for`), and a coin *law* is structurally unproposable in
this feed (nothing ever proposes `coin` as a subsumption head), so the noisy-TV guard is
evidenced instead by the cheap-trap `confirm` kind's yield decaying to ≈0.019 against the
productive `hunt` kind's ≈2.60 — the barren kind decayed far below the productive one, and
the same decay holds strictly for every other non-hunt kind in the final snapshot (`extend`,
`musement`).
**S3 HELD, with one honest mechanism repair**: the off-arm's original `peel`-based assertion
was unsatisfiable by construction (`fermat_number → odd` is a domain tautology — `peel`
model-checks against M's facts and reads TRUE whether or not the law was ever admitted), so
"found" is tested instead by **admission into `known_laws`** (a structural `same_graph`
match) — the law enters M only via the musement pathway; with musement off it never does.
Verified by the task reviewer as a repair, not a weakening of the criterion. **S4 HELD**:
identical configs yield identical journals (`replay_choices`), identical disposition
sequences, and identical refutation rounds; scatter's ordering is golden-pinned to the sha1
digest (a revert to salted `hash()` fails the golden across processes). **S5 HELD**:
`git diff --stat` against the pre-build commit shows only two new files touched —
`src/attention_economy.py` (+167) and `src/arithmetic_world.py` (+247), pure additions, zero
existing files touched; the persistence test round-trips through `TomosService.
save_uod_with_chain` with the correspondence check (LINEAR_GRAPHICAL_CORRESPONDENCE §3.3)
gating the disk write, and the produced trajectory passes the polarity-gate checks
(world-scroll residence, ligature closure, acknowledged acts with derivations on every
M-changing step), asserted in `TestPersistence`; the full
suite passed 3691 / skipped 137 / xfailed 1 / failed 0. Modules: `src/attention_economy.py`
(the socket), `src/arithmetic_world.py` (world #1 + `ProbeDirectedFeed`). Next: the vault as
world #2 (a separate cycle).

**Carried to the vault cycle:** unused imports in `attention_economy.py`; the `re.fullmatch`
tightening + hoisted `import re` in `ArithmeticWorld.test_law_instance`; the docket/frontier
dispatch branch in `ProbeDirectedFeed.propose` must count-or-refuse (never silently discard)
an unrecognized want kind; extracting the feed-seeding logic (`_seed_wants`) into a reusable
helper the vault world can share; and yield attribution at `probe_budget` > 1 (currently the
whole round's model delta is credited to every chosen want — correct at budget 1, but it
double-counts once several wants are chosen per round).

## 4 · Arisbe itself as a proposition in the wider EPG

The author's proposal: consider Arisbe a proposition in a wider Endoporeutic Game that we
develop and refine against the resistance of a more generic Grapheus — the world in which
Arisbe resides.

**The licence, and its conditions.** This walks through a door the Fidelity examinations
deliberately left open. The corollary to
[FIDELITY_AND_DEPARTURES.md](FIDELITY_AND_DEPARTURES.md) (§"Corollary — the larger game
and the common sheet") dissolved the *larger game* as an independent perspective but in
doing so **licensed exactly this move**: a context-free end is "a legitimate low-warrant
posit, fully sayable, not malformed (admitted at import, exposed to the Agon, never
*derived*)." The conditions that come with the licence:

- **Low warrant, admitted not derived.** "Arisbe is an effective instrument for
  modeling-under-doubt" enters as a posit and is *tested*, never concluded from within.
- **Never scored against a terminus.** The game is not played toward a surveyable summit
  (Departure I's non-locution); what is comparable is the **efficacy-vector** — a later
  Arisbe may be *a better instrument*, an ordinal fact with no top.
- **Competence, never worth.** Warrant = in-context competence; no worth-ranking of
  agents, ours included (the no-founder-exemption: the non-locution ranges over Arisbe
  exactly as it ranges over Omega and the Final Opinion).

**The observation that changes nothing mechanical: the wider EPG already runs.** The
run-log discipline — pre-registered priors (Pⁿ), findings (Fⁿ), dispositions, the
determinism canaries — *is* this game being played: the author scribes a proposal (a run
design with its priors), the world resists (the All-Star break, the `mul`-label failure,
the decay-vs-durability confounds), the record disposes. RUNS 1–12 are its innings, and
`runs/` is its corpus. Naming this does not add machinery; it makes the project
**self-describing under its own discipline** — the development process held to the same
posture (correspondence with the record, not truth-claims about the method) that M is
held to inside the loop. In Rorty's vocabulary (see
[CONTRIBUTION_AND_PRIOR_ART.md](CONTRIBUTION_AND_PRIOR_ART.md) §"Concordances"): this is
the **ironist's posture applied to the project itself** — radical, continuing doubt about
one's own final vocabulary, held without paralysis because commitment never required the
vocabulary to be final; with the one amendment Arisbe insists on throughout, that the
doubt is played out before a sound referee rather than settled by conversation alone.

**Deferred, named:** whether to *operationalize* the posit as a corpus Universe of
Discourse whose diachronic audit trail is the run verdicts — Arisbe drawn on its own
sheet. Doc-level for now (the author's decision, 2026-07-17); operationalize later if an
exemplar earns it.

## 5 · Named decisions for the author

1. **Ratify or amend the economy-of-research framing** (§2b) as the design spine for
   action selection — it is the assistant's reading of how Peirce 1879 maps onto active
   learning, and it will steer rung 1's scoring rule.
2. **Rung-1 authorization** — after RUN 12 disposes (the frontier-feedback edge would
   naturally be evidenced by a run; a RUN 13 candidate).
3. **Rung 2's outward-facing ethics** — pushing back on a shared source needs its own
   design pass before any build; decide when (if ever) to open that file.
4. **Glossary loanwords** — whether Umwelt / functional circle (the biosemiotic reading
   of the membrane and the loop, see
   [CONTRIBUTION_AND_PRIOR_ART.md](CONTRIBUTION_AND_PRIOR_ART.md) §"Concordances") enter
   [GLOSSARY.md](GLOSSARY.md), or stay confined to the concordance chapter.
5. **The reflexive UoD** (§4, deferred) — revisit once rung 1 or the next run gives the
   posit something new to be tested against.
