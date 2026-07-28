# The Bootstrap and Directed Engagement

> **What this is.** Design-of-record for the step-back the author took on 2026-07-17, with
> B-min discharging the S3 hinge (the drawn second-order convention reading back, see
> SECOND_ORDER_CORE_OPENING §4): Arisbe considered *as a whole*, against
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
> *Written 2026-07-17. Design only — this doc builds nothing new; everything cited as
> built carries its module name. Where a reading belongs to the assistant, it carries a flag.*

---

## 1 · The Minimal Predictive Automaton, mapped onto what is built

The author sketched a system initialized from outside with a sensor space *S*, an action
space *A*, and an internal transition model *M*; a perception–action cycle (read sign →
generate interpretant-as-prediction → interact → experience); **doubt defined strictly as
prediction error** (the delta between predicted and experienced next state); and remodeling
(abduction) triggered exactly when doubt is nonzero.

**Lineage (attribution, recorded 2026-07-17).** The MPA does not stand as a novel
architecture; it marks the **convergence point of four traditions**, and the doc owes each its credit: **American
pragmatism** — Peirce's *The Fixation of Belief* (1877) formalized the engine (inquiry
driven by the *irritation of doubt*, ending in a settled habit of action), and Dewey's
*The Reflex Arc Concept in Psychology* (1896) dismantled linear stimulus–response in favor
of the continuous perception–action loop (our actions dictate what stimuli we receive);
**cybernetics** — Wiener (1948) made feedback the general mechanism, and Ashby's
**Homeostat** (1948) gave the first *physical* implementation of remodeling driven by
environmental friction (ultrastability: out-of-bounds variables trigger re-randomized
internal wiring until equilibrium returns — doubt as a voltage); **predictive processing**
— Helmholtz's *unconscious inference* (1860s) through Friston's free-energy principle
(2006–): free energy **bounds** surprisal, and minimizing it plays doubt's functional role
— either by updating the model (perceptual inference) or by acting on the world (active
inference — the action arm this doc stages);
**machine learning** — Schmidhuber's artificial curiosity (reward = compression progress,
the agent *seeking* doubt to resolve it) and temporal-difference learning, whose TD error
is the doubt-delta exactly (and expected TD error = 0, the update's fixed point, is Peirce's
settled belief). Full entries in
[CONTRIBUTION_AND_PRIOR_ART.md](CONTRIBUTION_AND_PRIOR_ART.md) §"Concordances".

Against the codebase, the automaton stands about four-fifths built — scattered, under
other names:

| MPA element | Arisbe realization | Status |
|---|---|---|
| Sensor space *S* | Membrane items — `LiveSource.fetch` delivering `DiscourseItem` / `ResolvingItem` / `WikidataStatement` per poll | BUILT |
| Model *M* | The resident M (world-scroll cells at even depth, read via `world_scroll.m_view`); its laws are the theory | BUILT |
| Interpretant as prediction | The peel — `semantic_game.evaluate`; and literally in `resolving_membrane.py`: `ResolvingFeed` records M's forecast in the `PredictionLedger` **before** the loop folds the outcome in | BUILT |
| Doubt *D* > 0 | A FALSE verdict, a prediction miss, a counterexample. Kleene UNKNOWN is an honest *abstention*, not doubt — a distinction the MPA's arithmetic delta lacks | BUILT |
| Remodeling (abduction) | `revise_with_disposition` — and the disposition taxonomy is a *structured, recorded, warranted* update rule, richer than a matrix overwrite: each revision carries its Peircean mode (induction/deduction/abduction/convention) and its executed derivation | BUILT |
| Forgetting | Disuse-decay (`UsageLedger`, atom-level) — the MPA has no analogue; in Arisbe it is the only bound on the unbounded sheet (AUTOMATED_MODEL_DEVELOPMENT §"bounded only by selection-from-outside") | BUILT |
| Doubt-directed attention | The irritation pole: `attention_brief` (M's thin spots), the warm-set tropism (`tropism.py`, runs 2–3), and the docket of doubts (`query_docket.py` — articulated doubt → probe) | BUILT (partially — see §2) |
| **Growth of *S* and *A* themselves** | *S* grows: open-vocabulary membranes, label resolution turning opaque ids legible, the horizon promoting the not-yet-legible; *A* grows: the crawl growing its own frontier, the docket's Q-tiers shrinking `inexpressible`; the **sign-space** grows: the alphabet widening under INS, hypostatic abstraction at B-min | PARTIAL (see §1.1) |
| **Action space *A* (exercised)** | **Missing.** Arisbe predicts, probes, and revises — but it never *intervenes*: nothing chooses a reach by expected yield, and nothing pushes back on the source | NOT BUILT |

In three places Arisbe's shape runs *deliberately richer* than the automaton, each worth
keeping. First, the three-valued verdict: UNKNOWN ≠ doubt — an open-world abstention the
delta-arithmetic collapses. Second, the disposition taxonomy: remodeling that *records what
kind of move it was*, so the chain of semiosis stays legible — the whole point of "moving
pictures of thought" over a weight update. Third, the update rule itself. The MPA, like
Conway's Life, updates by a **fixed rule**; Arisbe remodels by a **negotiated
disposition** ("outcomes are negotiable, not determined" —
AUTOMATED_MODEL_DEVELOPMENT §1, which carries the full Game-of-Life correspondence and
its instructive breaks: death = relinquishment/decay, and closed dynamics on Life's
infinite lattice vs. the open sheet bounded only by selection from outside).

### 1.1 · Finite, not fixed — action changes the spaces themselves

The author clarified this at the second sitting (2026-07-17): the MPA's *S* and *A* are
finite for practical sense, but **finite need not mean fixed** — and the interesting part
of the bootstrap centers exactly there: **the automaton's action results in a change in
both spaces.** A sketch whose *S* and *A* stand frozen as a-priori architecture can
converge but cannot *develop*. A system whose acting wins it new distinctions to sense and
new probes to make is the one whose chain of semiosis actually unfolds. Predictive
processing calls this reflexive loop **structure learning** — model *expansion*, not
parameter update — and the thought belongs to Peirce before Friston: *symbols grow* —
"they come into being by development out of other signs" (CP 2.302). A new sign serves at
once as a new sensor (a distinction the system can now register) and a new actuator (a
probe it can now voice).

Arisbe already grows all three spaces, each by a named mechanism, each **bounded by
selection** rather than frozen:

- ***S* grows** — the membranes stay open-vocabulary by design (a required property of a
  good membrane, AUTOMATED_ENDOPOREUTIC_GAME §4b); label resolution turns opaque ids into
  legible names; and the **horizon** serves precisely as the staging area for sensor-space
  growth — what came back not-yet-legible, retained until legibility improves. That is
  why rung 1 makes it a first-class register: tomorrow's *S* waits there.
- ***A* grows** — the crawl grows its own frontier from what it finds
  (`RotatingWikidataSource.crawl`: entity-valued answers become new probeable entities);
  the docket's Q2/Q3 tiers exist to shrink `inexpressible`, i.e. to make previously
  unvoiceable wants voiceable — which makes growth of the action space an explicit
  design goal.
- **The sign-space grows** — the alphabet widens under lawful INS (a rule application can
  introduce vocabulary); and mention-ascent at B-min grows the sign-space in
  its strongest form: **hypostatic abstraction turns yesterday's predicate into today's
  subject** — a thing the system could only *say* becomes a thing it can *address, probe,
  and quote*. The crossing does not run as a research thread separate from the bootstrap;
  it forms the bootstrap's third axis.

**The guard, one level up.** Growing spaces re-create the unbounded-sheet problem for the
spaces themselves, and the same answer applies: growth must come **selected, not merely
accreted**. The frontier caps with drops *counted* (`frontier_cap`, `per_entity_cap`),
the negative label cache, and disuse-decay serve *S* and *A* as decay serves M. A
directed-engagement design (§3) that lets action enlarge the spaces must inherit this
discipline: every growth channel carries a bound, and everything dropped at a bound gets
counted, never silently truncated.

## 2 · What the bootstrap still lacks — and the Peircean warrant for building it

**(a) The action arm.** The automaton's step 3 ("Interact: execute action A") has no full
counterpart. AUTOMATED_ENDOPOREUTIC_GAME §4c states it plainly: the relation to the live
source is "*ingestion, not mutual co-evolution* — M changes in response to Wikidata, but
does not (yet) push back on it." And §4d already stakes out the ground: the
"eventual directed-engagement piece implements the rest: the musement pole, the
economy-of-research ordering of reaches, and the horizon as a first-class, retained
register." This doc's §3 lays the staged path onto that ground.

**(b) Action selection is Peirce's own economy of research.** Which reach to make next —
which entity to re-poll, which want on the docket to voice, which experiment to run?
Peirce solved that problem in outline in "Note on the Theory of the Economy of
Research" (1879): allocate inquiry by **cost against expected reduction of doubt**. His
paper gives the 19th-century statement of what statistics and machine learning now call
**optimal experiment design and the value of information** (Lindley 1956), of which
pool-based active learning is one modern instance. The warrant for building the action arm
therefore comes *native to Peirce*, not imported from the predictive-processing neighbors —
the neighbors corroborate; Peirce mandates. *(Assistant's reading, flagged; the author
should ratify the framing before it hardens into the doc spine — see §5.)*

**(c) The noisy-TV guard.** Once the prober chooses actions by expected doubt-reduction, the
target must be **learning progress** (the *rate of improvement* of prediction), never raw
prediction error: a pure-noise source generates maximal error forever and would trap an
error-seeking prober (the learning-progress concept belongs to Schmidhuber and Oudeyer;
Burda et al. 2018 popularized the "noisy-TV" *term*). Arisbe already half-guards this:
Kleene UNKNOWN abstains rather than mis-predicting, decay expels what never re-delivers,
and the standing rule that **poise must never become a target**
(AUTOMATED_ENDOPOREUTIC_GAME §4d) states the same Goodhart instinct for the run as a
whole. The design rule for §3 reads: *order reaches by expected learning progress per
unit cost, and let a want that never yields settle into the docket's `inexpressible`
residue rather than being re-probed forever.*

**(d) Against the blank slate.** The MPA seeds M "randomly or blank." That stands as the
one un-Peircean element of the sketch. Critical common-sensism denies the tabula rasa —
we begin laden with instinct and un-criticized background belief, and inquiry starts *in
medias res*. Arisbe's actual bootstrap keeps the closer faith: **the low-warrant import
floor** (corpus seeds, ontology imports, curated pools — see
[EXTERNAL_SOURCES_AND_IMPORT.md](EXTERNAL_SOURCES_AND_IMPORT.md)) *is* the "outside
setup," and [MATHEMATICS_FROM_THE_SHEET.md](MATHEMATICS_FROM_THE_SHEET.md) already
rules the blank sheet's first act (DC+). So do not chase
the blank automaton; the bootstrap problem Arisbe should own is not "start from nothing"
but "start from low warrant and *earn*."

## 3 · The staged path to directed engagement

Design only; each rung takes a separate authorization. Rung 0 stands as the base.

**Rung 0 — built (the irritation pole).** `attention_brief` (proto-tropism), the warm-set
re-poll tropism (`tropism.py`; runs 2–3 showed re-poll alone cannot bound the sheet —
the RUN_3 findings F1″/F2″, Part III ledger of AUTOMATED_ENDOPOREUTIC_GAME), and the
docket of doubts (`query_docket.py` — UNKNOWN transcript, thin spots, and unwitnessed
consequences registered as *wants*, prioritized fewest-attempts → oldest, settled per
segment, with the honest `inexpressible` residue).

**Rung 1 — the economy of research (ordering the reaches).** Replace the docket's
mechanical priority with a cost/yield ordering, and widen what feeds it:

- Feed the meta-learning instruments back into the docket: `unresolved_frontier` and
  `friction_map` (`agon_metalearning.py`) name exactly the claims where engagement will
  likely prove fertile — today humans read them in run logs; the prober never does. This
  edge comes cheap and closes the loop: **the game studying the game, then steering it.**
- Score each want by expected learning progress per unit cost (a probe that has repeatedly
  yielded nothing decays in priority — the noisy-TV guard of §2c), rather than
  fewest-attempts → oldest.
- Add the **musement pole** (the pull, complementing irritation's push — Peirce's *A
  Neglected Argument*): a bounded fraction of reaches allocated off-docket, at low cost,
  to keep variation alive (the annealing/boredom-detector idea of
  AUTOMATED_ENDOPOREUTIC_GAME Part I §4 item 4).
- Make the **horizon** a first-class, retained register (what came back not-yet-legible,
  kept and re-attempted as legibility improves — the sensor-space growth register of
  §1.1) rather than a per-poll report field. Built 2026-07-18 at the vault stage
  (`attention_economy.Horizon`), as designed.

**Rung 2 — mutual co-evolution (pushing back).** Here the functional circle closes: M's
contested frontier surfaces *to the source* — suggested edits, say, or flagged
inconsistencies offered back to the wiki-world — so the world and the model shape each
other. AUTOMATED_ENDOPOREUTIC_GAME §4c names it as the future edge. This rung carries real
outward-facing consequences (Arisbe would be *acting* on a shared world) and therefore
needs its own ethics-and-etiquette design before any build; nothing below rung 2 acts
outside Arisbe's own polls.

**Rung 1 — AUTHORIZED 2026-07-17 (the arithmetic stage), with pre-registered criteria.**
The author chose the staging **arithmetic → vault → author-as-oracle** (each field a
separate cycle; the horizon register deliberately waits for the vault, where illegibility
genuinely exists) and the architecture **attention socket + world #1**: a world-agnostic
`AttentionEconomy` + `ProbeDirectedFeed` pair, with a computed-arithmetic world
(`arithmetic_world.py`) as the first field — deterministic, CI-safe, zero NL, and with a
real cost model (probing *n* costs what primality testing costs). The headline trajectory
runs: **Fermat's 1640 conjecture** (every 2^2^n + 1 is prime) proposed, confirmed at F0–F4,
**refuted at F5 = 641 × 6 700 417** (Euler 1732) — reachable under budget only if
attention spends on severity rather than cheap re-confirmation. The criteria went on
record *before* the build, in the run-log discipline:

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

**What rung 1 is *not*:** not a new membrane, not a new referee, not a change to the
calculus. The mode contract and the low-warrant floor (the "border guards" of
AUTOMATED_ENDOPOREUTIC_GAME §4d) stay untouched; only the *conduct* of inquiry — Peirce's
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
this feed (nothing ever proposes `coin` as a subsumption head), so the evidence for the
noisy-TV guard comes instead from the cheap-trap `confirm` kind's yield decaying to ≈0.019
against the productive `hunt` kind's ≈2.60 — the barren kind decayed far below the productive one, and
the same decay holds strictly for every other non-hunt kind in the final snapshot (`extend`,
`musement`).
**S3 HELD, with one honest mechanism repair**: the off-arm's original `peel`-based assertion
was unsatisfiable by construction (`fermat_number → odd` is a domain tautology — `peel`
model-checks against M's facts and reads TRUE whether or not the law was ever admitted), so
"found" is tested instead by **admission into `known_laws`** (a structural `same_graph`
match) — the law enters M only via the musement pathway; with musement off it never does.
The task reviewer verified this as a repair, not a weakening of the criterion. **S4 HELD**:
identical configs yield identical journals (`replay_choices`), identical disposition
sequences, and identical refutation rounds; the golden test pins scatter's ordering to the
sha1 digest (a revert to salted `hash()` fails the golden across processes). **S5 HELD**:
`git diff --stat` against the pre-build commit shows only two new files touched —
`src/attention_economy.py` (+167) and `src/arithmetic_world.py` (+247), pure additions, zero
existing files touched; the persistence test round-trips through `TomosService.
save_uod_with_chain` with the correspondence check (LINEAR_GRAPHICAL_CORRESPONDENCE §3.3)
gating the disk write, and the produced trajectory passes the polarity-gate checks
(world-scroll residence, ligature closure, acknowledged acts with derivations on every
M-changing step), as `TestPersistence` asserts; the full
suite passed 3691 / skipped 137 / xfailed 1 / failed 0. Modules: `src/attention_economy.py`
(the socket), `src/arithmetic_world.py` (world #1 + `ProbeDirectedFeed`). Next comes the
vault as world #2 (a separate cycle).

**Carried to the vault cycle:** unused imports in `attention_economy.py`; the `re.fullmatch`
tightening + hoisted `import re` in `ArithmeticWorld.test_law_instance`; the docket/frontier
dispatch branch in `ProbeDirectedFeed.propose` must count-or-refuse (never silently discard)
an unrecognized want kind; extracting the feed-seeding logic (`_seed_wants`) into a reusable
helper the vault world can share; and yield attribution at `probe_budget` > 1 (currently the
feed credits the whole round's model delta to every chosen want — correct at budget 1, but it
double-counts once several wants are chosen per round).

## 4 · Arisbe itself as a proposition in the wider EPG

The author put the proposal this way: consider Arisbe a proposition in a wider
Endoporeutic Game that we develop and refine against the resistance of a more generic
Grapheus — the world in which Arisbe resides.

> **Reconciliation + ✅ RULED (the author, 2026-07-21)
> ([THE_COMMENS_AND_THE_COMMUNITY.md](THE_COMMENS_AND_THE_COMMUNITY.md) §3, §1, §6).** Read this
> project-scale "more generic Grapheus" as **model-of, never instance-of** (§3): the outer framing
> borrows the two-player picture (Arisbe as proposal-side, the world as the standing Model-M-side) as a
> *model* of inquiry carried within the project's own process — it does not make the project an instance
> of the institution of inquiry, which is a community-level emergent (§6). **The ruling: the outer game
> does NOT lack a judge — but the project does not own or make that judgment.** A judging function
> beyond the membrane genuinely *exists*: real judge roles and judiciary institutions, umpires,
> elections, markets. What an individual — or this project — does is **watch these judgments occur, as
> if removed: participate but never own, never entirely comprehending**, for the reason already held as
> doctrine (the commens is un-possessed and participation-sustained, §1). **Even occupying the
> judge-seat does not change this** (the author, sharpening): an individual may sit as judge, the world
> waiting "with bated breath" for the decision — yet **the licence to judge does not reside in that
> individual, and neither does the rationale**, any more than being asked to *judge the meaning of a
> word* makes the meaning one's own. One may provide a response; but **how that response functions
> beyond the membrane belongs to the objectivated institutionalizations** (Berger & Luckmann's
> objectivation, [THE_COMMENS_AND_THE_COMMUNITY.md](THE_COMMENS_AND_THE_COMMUNITY.md) §1; lifted to
> general doctrine there as **§2(c) — judgment itself is objectivated**), not to the responder. So the
> project's internal model of external judgment — "the
> record disposes," the run-log Pⁿ/Fⁿ discipline — **does not make the judgment; only the community
> does** — and the same holds of any lone judge, whose seat, licence, and reasons are themselves
> objectivated, participated-in-never-owned. The Agonothetes/fate-selector the project carries at this
> scale is, exactly, a *model of* a judging function whose instance lives in the community beyond the
> membrane — which is why connecting outward (publication, workstream B) is not optional decoration but
> the only route to a judgment the project cannot make for itself (§10).

**The licence, and its conditions.** This walks through a door the Fidelity examinations
deliberately left open. The corollary to
[FIDELITY_AND_DEPARTURES.md](FIDELITY_AND_DEPARTURES.md) (§"Corollary — the larger game
and the common sheet") dissolved the *larger game* as an independent perspective but in
doing so **licensed exactly this move**: a context-free end is "a legitimate low-warrant
posit, fully sayable, not malformed (admitted at import, exposed to the Agon, never
*derived*)." The conditions that come with the licence:

- **Low warrant, admitted not derived.** "Arisbe is an effective instrument for
  modeling-under-doubt" enters as a posit and gets *tested*, never concluded from within.
- **Never scored against a terminus.** No one plays the game toward a surveyable summit
  (Departure I's non-locution); what admits comparison is the **efficacy-vector** — a
  later Arisbe may prove *a better instrument*, an ordinal fact with no top.
- **Competence, never worth.** Warrant = in-context competence; no worth-ranking of
  agents, ours included (the no-founder-exemption: the non-locution ranges over Arisbe
  exactly as it ranges over Omega and the Final Opinion).

**The observation that changes nothing mechanical: the wider EPG already runs.** The
run-log discipline — pre-registered priors (Pⁿ), findings (Fⁿ), dispositions, the
determinism canaries — *is* the project playing this game. The author scribes a proposal (a run
design with its priors); the world resists (the All-Star break, the `mul`-label failure,
the decay-vs-durability confounds); the record disposes. RUNS 1–12 form its innings, and
`runs/` its corpus. Naming this adds no machinery; it makes the project
**self-describing under its own discipline** — the development process held to the same
posture (correspondence with the record, not truth-claims about the method) that M
answers to inside the loop. In Rorty's vocabulary (see
[CONTRIBUTION_AND_PRIOR_ART.md](CONTRIBUTION_AND_PRIOR_ART.md) §"Concordances"), this
amounts to the **ironist's posture applied to the project itself** — radical, continuing
doubt about one's own final vocabulary, held without paralysis because commitment never
required the vocabulary to be final; with the one amendment Arisbe insists on throughout,
that the doubt plays out before a sound referee rather than settling by conversation alone.

**Deferred, named:** whether to *operationalize* the posit as a corpus Universe of
Discourse whose diachronic audit trail consists of the run verdicts — Arisbe drawn on its
own sheet. It stays doc-level for now (the author's decision, 2026-07-17); operationalize
later if an exemplar earns it.

## 5 · Named decisions for the author

1. **The economy-of-research framing** (§2b) — ✅ RATIFIED 2026-07-19 (and evidenced:
   rung 1's S1 result shows the framing doing its work — severity bought the Fermat
   refutation).
2. **Rung-1 authorization** — after RUN 12 disposes (a run would naturally evidence the
   frontier-feedback edge; a RUN 13 candidate).
3. **Rung 2's outward-facing ethics** — pushing back on a shared source needs its own
   design pass before any build; decide when (if ever) to open that file.
4. **Glossary loanwords** — ✅ RULED 2026-07-19: Umwelt / functional circle stay
   well-described **concordances** (light-shedding, not house vocabulary). Instead,
   the membrane-and-loop unit gets a **native name and description carrying the
   fractal understanding** (it recurs in semiotic processes at many levels) — the
   naming thread stays open, candidates under the author's review.
5. **The reflexive UoD** (§4, deferred) — revisit once rung 1 or the next run gives the
   posit something new to be tested against.
