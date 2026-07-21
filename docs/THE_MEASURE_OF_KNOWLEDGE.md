# The Measure of Knowledge — and Its Ethical and Pedagogical Corollaries

> **What this is.** Design-of-record for three threads the author opened on 2026-07-17,
> the day rung 1 (the attention economy, `attention_economy.py` + `arithmetic_world.py`)
> was built: (§1–§2) a **definition and quantification of knowledge** extracted from the
> machinery, seeded by the author's earlier definition; (§3) the author's intuition that
> knowledge has **components corresponding to a fractal structure**; (§4) the **ethical
> implications** of the doubt-driven system for a just society, with the author's prompt
> naming **John Rawls**; (§5) **pedagogy** — the author's question of "just what parts of
> a knowledge scaffold will bear weight for ongoing learning and guidance of a neophyte
> in dialogue with a teacher."
>
> Assistant-drafted from the author's seeds (each quoted where it enters); every reading
> that is the assistant's is flagged; the decisions are named in §6 and remain the
> author's. Most of this doc is design; two builds have since landed (2026-07-19, under
> the Examination IV docket): the §2 K3 compression ratio and the §2 K1 severity join —
> each carrying, in the table below, exactly what remains open. The tutor loop (§5)
> remains a design-pass candidate, named not authorized.
>
> **Companions:** [BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md](BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md)
> (the loop this doctrine reads from) ·
> [FIDELITY_AND_DEPARTURES.md](FIDELITY_AND_DEPARTURES.md) (the warrant discipline every
> section must respect) · [AUTOMATED_ENDOPOREUTIC_GAME.md](AUTOMATED_ENDOPOREUTIC_GAME.md)
> (the instruments: ledger, stickiness, poise) ·
> [CONTRIBUTION_AND_PRIOR_ART.md](CONTRIBUTION_AND_PRIOR_ART.md) §"Concordances" (the
> neighboring programs) · [GETTING_STARTED.md](GETTING_STARTED.md) (the existing on-ramp
> §5 reads didactically).
>
> *Written 2026-07-17.*

---

## 1 · The definition, revised in Arisbe's vocabulary

**The author's seed** (an earlier effort, quoted from the author's 2026-07-17 message,
lightly normalized): *"Knowledge — a set of situations in which an agent successfully
mediates a nontrivial, polar relationship between entities. In short, knowledge exists
when someone reliably does something (thinks, speaks, acts) that works."*

This is a dispositional, pragmatist definition — knowledge as reliable successful
mediation — and the machinery now running gives each clause a measurable counterpart:

- **"Reliably … works"** → the track record. In the resolving membranes M's knowledge *is*
  its forecast record (`PredictionLedger`: hits, misses, honest abstentions, net);
  `select_best` already compares knowledges by record. RUN 12 began scoring live games
  this way on 2026-07-17.
- **"Nontrivial"** → **severity**, the term rung 1 added. A reliable success that risked
  nothing (predicting tautologies — epistemology's noisy TV) earns nothing; knowledge
  accrues in proportion to the *refutability survived*. The Fermat exemplar is the
  worked case: five confirmations deep, the law was never knowledge, because it had not
  been tested where it could fail — and at F5 it died. Popperian corroboration, made a
  line item.
- **"Mediates a … polar relationship"** → the sign-relation, and in an existential graph
  the polarity is *drawn*: a law `~[ P ~[ Q ] ]` mediates antecedent and consequent
  across evenly and oddly enclosed areas. The peel is the mediation act; the verdict is
  its success or failure.
- **"A set of situations"** → the clause the seed got most right: knowledge is **indexed
  to the horizon within which its record was earned** — the Umwelt clause. This is
  exactly the standing floor (*warrant = in-context competence, never worth*,
  FIDELITY_AND_DEPARTURES): the "set of situations" was context-indexing before Arisbe
  enforced it structurally.

**The revision** (assistant's formulation, for the author to amend): **knowledge is the
resident content of M whose habits reliably mediate the membrane's deliverances —
quantified by severity-weighted track record, durability under revision, compression of
the deliverance stream, and continued use — always indexed to the horizon within which
the record was earned.** The correspondence-not-truth discipline survives intact: this
quantifies *warranted reliability in context*, never truth.

*Prior-art anchors* (see CONTRIBUTION_AND_PRIOR_ART §"Concordances" for the fuller
survey): Peirce's belief-as-habit; Ramsey's success semantics; Ryle's knowing-how;
Sosa's apt performance (accurate *because* adroit — the ledger measures aptness over
repetition, so luck washes out, which is why Gettier-style luck cases lose their grip on
a record-based measure). *(Assistant's readings, flagged.)*

## 2 · The measure — four components, all instrumented

| # | Component | What it measures | The instrument |
|---|---|---|---|
| K1 | **Severity-weighted track record** | Reliable success on tests that could have refuted | `PredictionLedger.k1_score` (`Σ severity of hits − Σ severity of misses`, `resolving_membrane`) — the ledger + severity join BUILT 2026-07-19 with **declared linear weights** (`w(sev)=sev`), ordering-invariant under positive rescaling of severity. Still a design in one respect: the anchors' operational definition (severity = measured refutation-power) is an OPEN obligation, and the S1 result validated severity as an *attention* heuristic only, not as a scoring weight |
| K2 | **Durability** | Survival under continued revision pressure | `agon_metalearning` stickiness / `mechanism_principles` (decay-aware: a faded item reads `stuck=None`, not refuted) — BUILT |
| K3 | **Compression** | What fraction of the deliverance stream the laws derive | The **materialization ratio** (`materialization_ratio` → `KnowledgeCompression.ratio` = derived ÷ (explicit + derived), bounded [0,1], extent-invariant), read off `model_materialization`'s closure — BUILT 2026-07-19. The old mean-derivational-yield number survives as `yield_per_law` (derived ÷ laws), which is *not* extent-invariant and is not K3 |
| K4 | **Use** | The habit exercised — re-delivery | `UsageLedger` (atom-level); disuse-decay is the operational form of "knowledge exists only while it works" — the *faded* tense — BUILT |

**Three guards, each already doctrine elsewhere, restated here as conditions on the
measure:**

1. **Never truth.** The measure self-certifies warranted reliability in context — the
   record, not the world's verdict on the record (the §3.3 posture: attest
   correspondence, not truth).
2. **Never a target.** Any knowledge-score is an instrument; optimized directly it
   Goodharts (the standing poise rule: *an instrument, never a target*).
3. **Never a scalar over agents.** The four components stay a **vector over
   knowledge-items and models**; they are never aggregated into a single number ranking
   *inquirers*. An aggregate scalar would reinvent the worth-ladder the Fidelity
   examinations dissolved — competence ≠ worth is a category-fact. *(Assistant's
   proposed guard, §6 decision 3.)* The ground of this guard is the commens: there is
   **no commens-scaled denominator** to normalize K across agents, because no agent
   possesses the commens (a participation-sustained social construct, not a God's-eye
   given) — so an aggregate scalar has nothing to be a fraction *of*. See
   [THE_COMMENS_AND_THE_COMMUNITY.md](THE_COMMENS_AND_THE_COMMUNITY.md) §2.

**Sufficiency is not claimed:** the four components cover the *assertoric* fragment of
the seed definition; "acts that work" awaits the action arm (BOOTSTRAP), and
calibration, coherence, coverage, and evidential independence are named
**non-components** until argued in or out. *(Examination IV, D1.4.)*

## 3 · The fractal structure

**The author's seed:** *"I think it has components corresponding to a fractal
structure."*

The reading that cashes this out (assistant's, flagged): the same
doubt → test → dispose → decay cycle operates **self-similarly at every level**, and each
level's knowledge is measured by the *same ledger shape* (K1–K4 transport across
scales):

1. **Atom** — a fact's re-delivery record (the usage ledger);
2. **Law** — a generalization tested against instances (the peel; stickiness);
3. **Model M** — the residence, revised through dispositions, bounded by decay;
4. **Mechanism** — the meta-learning layer: knowledge *about knowledge-formation* (which
   resolution mechanisms produce durable knowledge), with its own stick-rates;
5. **Project** — the wider Endoporeutic Game: the pre-registered priors and findings
   (the `Pⁿ`/`Fⁿ` run-log discipline), the author as Graphist against the world's
   Grapheus.

Each level is a compressed re-instance of the one below — a self-similar generative
cycle with a **scale-transportable measure**, which is a reasonable formal cash-out of
"fractal." The *syntax* mirrors it: recursively nested cuts, cells within the standing
world-scroll, quotation ovals within cells at B-min — graphs about graphs is knowledge
about knowledge — with the A3 conservativity gate (the standing crossing invariant) as
the guarantee that no level corrupts the one beneath it. The recursion has a floor and a
discipline, which natural fractals lack.

**Three further senses (the author's, 2026-07-18).** The author extended the reading in
three directions the level-ladder alone doesn't capture:

1. **The Endoporeutic Game is itself recursive** — the peel plays *sub-EPGs* as it
   traverses the proposed graph, one game per nested context, outside-in: the syntax
   recursion (cuts within cuts) and the game recursion (games within games) are the
   same descent. The fractal is not only *between* levels; it is *inside* a single
   evaluation.
2. **The diachronic DAG's branches are parallel chains of semiosis** — each root→leaf
   path a self-similar trajectory of the same doubt-cycle, diverging where dispositions
   disagreed (the branch-on-disagreement machinery) and sometimes reconverging: the
   fractal in *time*, not just in scale. **Modal K2 BUILT 2026-07-19:**
   `modal_query.durability_modality` reads K2 along this branching sense —
   "necessary" (K2□, durable on every reachable trajectory), "possible" (K2◇,
   durable on some but not all), or "absent" — composing the module's existing
   `possibly`/`necessarily` over the diachronic DAG rather than a single line.
3. **Communities of Arisbes** — the horizontal dimension: multiple instances
   collaborating in modeling each other and the world around them, each an
   author-according-to-the-other at the system grain, playing the same game between
   themselves that each plays with its membranes. Unbuilt; named here as the fractal's
   social axis.

And the closure condition, in the author's words: *"When Arisbe models its own modeling,
rather than you and I doing so, the semiotic loop may truly close."* Today levels 4–5
(the mechanism findings, the run-log discipline) are held **outside** the system — by the
author and the assistant, in docs and logs. The loop closes when that model becomes an
**M inside Arisbe** — doubt-driven, peeled, revised, and decayed like any other — which
is the strongest standing argument for eventually operationalizing the deferred
reflexive Universe of Discourse (BOOTSTRAP_AND_DIRECTED_ENGAGEMENT §4). The author also
notes the evidence is already on hand: *the history of Arisbe's own development — the
documentation and commits — carries the author's hand, interests, values, and
directives*, a dated, disposed, membrane-ready record of both the project and its
author.

## 4 · Ethical corollaries — the doubt-driven system and a just society

**The author's prompt:** explore *"the broader ethical implications of Doubt 4 and what
the resultant system means for a just society, perhaps corresponding to John Rawls."*
**The referent (resolved by the author, 2026-07-17): Doubt 4 of
[FIDELITY_A_PLAIN_ACCOUNT.md](FIDELITY_A_PLAIN_ACCOUNT.md) — "Ladders of worth: who gets
to play, and who plays well."** That doubt's surviving position is the ground this whole
section stands on: *gate the claim by the method, on its content — never the agent by
identity or worth; ranking people by worth-as-inquirers swaps a method-gate (which tracks
the truth) for an identity-gate (which tracks who's in the club); and every claim is owed
its uptake.* The question this section answers is therefore: **what does a society built
on Doubt 4's resolution look like, and how far does Rawls map onto it?**

**Where the system and Rawls genuinely concord** *(assistant's readings, flagged)*:

1. **Reflective equilibrium is a doubt-driven revision loop.** Rawls's method — adjust
   principles against considered judgments until they cohere — is structurally the
   M-revision cycle, and the disposition taxonomy names its moves (a judgment admitted;
   a principle generalized; an over-general principle relinquished against an anomaly).
   Arisbe mechanizes, for empirical models, the method Rawls prescribed for normative
   ones.
2. **The method-gate is veil-shaped.** The peel judges a claim's *content*, never its
   author — the re-grounded Fidelity residue (*"the only legitimate gate is the method
   applied to a claim, judged by content, never by the author's identity"*,
   FIDELITY_AND_DEPARTURES, Examination III update) is an original-position symmetry
   constraint on epistemic goods: behind the gate, no proposer knows whether being
   themselves will help.
3. **The record is public reason.** Every admission carries its warrant, act, and
   derivation, auditable by anyone — justification addressed to all, not to insiders.
4. **Correspondence-not-truth is pure procedural justice.** Rawls's category for
   outcomes with no independent criterion — where the fairness of the procedure is what
   legitimates the result — is exactly the posture: the record certifies that the moves
   were licensed, not that the outcome is true.
5. **The docket is maximin-flavored.** The register of doubts is *counted, never
   silently dropped* (`inexpressible` is a named residue; the tie-break serves the
   oldest, least-attempted wants first; every cap's drops are counted). A standing floor
   against the permanent, invisible exclusion of any doubt is a distributive principle
   about attention — the system's scarcest good.

**The honest tensions** — where the concordance must not be oversold:

- **Fair access is not derivable, and the record already ruled on it.** Examination III
  (FIDELITY_AND_DEPARTURES) found "fair access to the Game" *falls as a derivation*:
  every real inquiry is a method-gated forum, and it is submission to the method, not
  universal access, that lets convergence track the real. What the discipline yields is
  **procedural epistemic fairness** — claims judged by content, the anti-*ad hominem*
  duty of uptake, no worth-ranking of agents, no founder exemption. It does **not**
  yield the difference principle, primary goods, or distributive justice; Rawls needs
  premises this system does not supply, and importing them silently would be the exact
  smuggling the examinations forbid.
- **The load-bearing bridge is Fricker, not Rawls — and it is Doubt 4's own.** The duty
  of uptake — test a claim on its content before dismissing it by its author — is the
  corrective to testimonial injustice (Fricker's *Epistemic Injustice*, 2007), and
  FIDELITY_A_PLAIN_ACCOUNT's Doubt 4 already names it: refusing uptake *is* epistemic
  injustice, "the wrong of not even hearing someone out because of who they are."
  Identity-gating claims is the paradigm case, and the method-gate is its structural
  remedy. That is the ethical content the system actually carries, and it is strong.
- **Level 4 is where the politics lives.** The mechanism level (§3) learns *which
  resolution mechanisms produce durable knowledge* — and any deployment of that learning
  (whose sources count as reliable, whose consensus is discounted) allocates epistemic
  authority. The guard is the same vector-not-scalar rule of §2: mechanism findings
  describe *mechanisms' records in context*, never persons' worth.
- **Rung 2 inherits all of this.** Pushing back on a shared world (the deferred
  mutual-co-evolution rung, BOOTSTRAP_AND_DIRECTED_ENGAGEMENT §3) is the point where
  the system stops merely knowing and starts *doing to others* — its ethics pass should
  take this section as its floor: consent, provenance, counted interventions, no
  identity-gating, uptake owed.

## 5 · Pedagogical corollaries — which parts of the scaffold bear weight

**The author's prompt:** *"pedagogy and a consideration and analysis of just what parts
of a knowledge scaffold will bear weight for ongoing learning and guidance of a neophyte
in dialogue with a teacher."*

**The claim** (assistant's, flagged): **weight-bearing = the measure of §2, read
didactically.** A scaffold element bears weight for ongoing learning exactly insofar as:

- **K1 — it has survived severe tests.** Teach what has been tested where it could fail,
  not what is merely believed; and let the *learner* test it where it could fail —
  "desirable difficulties" (Bjork) is severity in pedagogy.
- **K2 — it is durable under revision.** The mechanism by which the learner acquired it
  predicts whether it sticks: `mechanism_principles` is literally a curriculum-ordering
  instrument (what is earned against resistance outlasts what is accepted on consensus).
- **K3 — it compresses.** The laws that derive many facts are the load-bearing beams;
  teach generative rules over enumerations, and measure a lesson by its materialization
  ratio (`ratio` = derived ÷ (explicit + derived), the extent-invariant form — so a
  lesson about a *small* domain compresses no worse than the identical lesson about a
  big one; the old size-confounded yield lives on only as `yield_per_law`).
- **K4 — it stays in use.** Re-delivery is retention: the testing effect (retrieval
  practice) is the decay clock run deliberately; what the learner never re-derives,
  fades — and *should* be allowed to, if it bears no weight.

**The teacher is an attention economy pointed at the learner.** Choosing the next
question is the economy-of-research problem over the *learner's* model: expected
learning progress per unit cost, probed in the zone where severity is affordable —
Vygotsky's zone of proximal development, stated as a scoring rule. The guards transfer
whole: the noisy-TV guard (don't feed unfalsifiable or patternless material — maximal
confusion is not maximal learning), the musement pole (budget genuine play), the boredom
detector (when nothing yields, change register).

**The dialogue shape already exists: the Endoporeutic Game is a tutorial protocol.**
Teacher as Graphist — posing doubts scaled to the learner's M; learner as Grapheus —
defending and revising their model; and the calculus as the incorruptible referee, which
is what lets the teacher be *fallible safely* (the learner can win). Two consequences
worth stating:

- **A teacher's model of the learner is level-4 knowledge** (§3): a model of how this
  learner's model forms and revises — with its own record, its own durability.
- **Scaffold removal is decay by design.** Warrant is in-context competence and does not
  transfer by testimony: what the teacher's authority temporarily supplied must be
  re-earned as the learner's own record, and the scaffold element that cannot be let
  fade was never load-bearing — it was load-*carrying*, a dependency.

**Machinery already on the shelf** for this: the role-aware on-ramp
([GETTING_STARTED.md](GETTING_STARTED.md)) · the primer's live-drawn first graphs · the
challenge bank's difficulty gradient with `same_graph` grading · `legible_diff` — the
*how-they-differ* report is formative feedback delivered in the learner's own sign
vocabulary · the dragons · the English gloss (`eg_to_english`). **The missing piece is
the learner-ledger**: a Universe of Discourse recording a learner's demonstrated
competences (their K1–K4 over the exemplar space), driving challenge selection through
the same `AttentionEconomy` socket rung 1 built — the **tutor loop**, named here as the
pedagogy build candidate, not authorized (§6 decision 5).

*Prior-art anchors:* Vygotsky (*Mind in Society*, 1978; ZPD); Wood, Bruner & Ross
(1976 — the origin of "scaffolding," with fading built into the concept); Bloom (1984,
the two-sigma problem — what the tutor loop would chase); Corbett & Anderson (1995,
Bayesian knowledge tracing — the machine-learning cousin of the learner-ledger);
Roediger & Karpicke (2006, the testing effect); Bjork (desirable difficulties); and the
Socratic elenchus — doubt-induction as the oldest teaching method on record.

## 6 · Named decisions (the author's)

1. **"Doubt 4"** — ✅ RESOLVED 2026-07-17: Doubt 4 of
   [FIDELITY_A_PLAIN_ACCOUNT.md](FIDELITY_A_PLAIN_ACCOUNT.md) ("Ladders of worth").
   §4 is re-grounded on it. A consequence for decision 3: the vector-not-scalar guard
   is now literally **Doubt 4's enforcement clause inside the measure** — an aggregate
   knowledge-score over agents would be the worth-ladder rebuilt by arithmetic.
2. **The four-component measure** (§2) — ✅ RATIFIED 2026-07-17, K3 authorized +
   **BUILT same day**, then **re-derived 2026-07-19** (Examination IV, D1.3) to remove
   a domain-size confound: `model_materialization.materialization_ratio` →
   `KnowledgeCompression.ratio` = derived ÷ (explicit + derived), bounded [0,1] and
   extent-invariant (a lawless M reads 0.0, never an error). The earlier
   derived-÷-all-laws number — the *mean derivational yield*, which scales with domain
   size — survives as `yield_per_law`, not as K3. K1's severity join was **built the
   same day** (`PredictionLedger.k1_score`), with the anchors' operational definition
   carried as an open obligation (§2). Tests in `tests/test_model_materialization.py` and
   `tests/test_resolving_membrane.py`. All four components now instrumented.
3. **The vector-not-scalar guard** (§2, guard 3) — ✅ RATIFIED 2026-07-17 as doctrine:
   components are never aggregated into a single ranking of inquirers (Doubt 4's
   enforcement clause inside the measure).
4. **The Rawls thread's shape** (§4) — ✅ RULED 2026-07-17: (a) the
   procedural-epistemic-fairness reading with the Fricker/uptake bridge ADOPTED;
   (b) the maximin-docket gloss ACCEPTED (a modest structural fact about attention,
   not a grand claim).
5. **The tutor loop** (§5) — ✅ DESIGN AUTHORIZED 2026-07-17; the design pass is
   [TUTOR_LOOP.md](TUTOR_LOOP.md) (design-of-record; nothing built — the build is a
   separate authorization).
6. **Placement** — ✅ RULED 2026-07-19: **§§1–3 graduate to the book** (a "From
   concordance to measure" section extending CONTRIBUTION_AND_PRIOR_ART, executed same
   day); **§5 awaits machinery** — the pedagogy section graduates only once the tutor
   loop is at least T0-built. Also ruled the same sitting: **Umwelt stays a
   well-described concordance**, not a glossary loanword — the native naming effort
   for the membrane-and-loop unit is its own thread (candidates under review).
