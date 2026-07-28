# Corpus Exemplars — proofs and boards that put meat on the bones

> **What this is.** A short catalogue of the worked exemplars seeded into the corpus,
> so that Organon has things to read and Agon has somewhere to play. It covers the
> **proof exemplars** (§2), the **domain-model boards** (§3), the curated [**episodes**](GLOSSARY.md#episode) that
> wire them into the game picker (§4), a **branching-modality** episode (§5), and a
> **model that transforms through dialog** (§6). It guides you to *what is
> there and why*; it does not teach you to author more (that pattern lives in the
> `tools/build_*.py` scripts and [CORPUS_AND_IMPORT_MODEL.md](CORPUS_AND_IMPORT_MODEL.md)).
>
> **Companions:** [DOMAIN_ORACLE_AND_M.md](DOMAIN_ORACLE_AND_M.md) (how a board is
> queried as a model M) · [GENERATION_AND_TESTING.md](GENERATION_AND_TESTING.md)
> (the episode *given M, then G*) · [ENDOPOREUTIC_GAME_GUIDE.md](ENDOPOREUTIC_GAME_GUIDE.md).
>
> *Created 2026-06-29.*

---

## 1. Why these exist

Arisbe's machinery stays only as legible as the worked examples that exercise it.
One pass filled two gaps:

- **Proofs to read.** Organon serves as a read-only archive; it wants a spread of
  *worked derivations* a teacher or student can step through. The existing set
  (Peirce's Law, Barbara, Leibniz's *Praeclarum*, the group-identity uniqueness,
  beta modus ponens) leaned toward the harder theorems. The new quartet adds short,
  iconic propositional laws, including two that teach an Existential Graph ([EG](GLOSSARY.md#eg))-specific insight worth more
  than the theorem.
- **Boards to play on.** The [Endoporeutic](GLOSSARY.md#endoporeutic) (reading a graph from the outside in) Game's interpretation register reads *given
  M, then G*, and you cannot play without an M. The curated persona models in
  `src/agon_models.py` serve as inline on-ramps; the corpus wanted richer,
  browsable domain-model Universes of Discourse ([UoDs](GLOSSARY.md#uod)) that double as game boards. Two joined it,
  and they contrast closed with open.

Everything below stands as a real corpus UoD: §3.3-attested at save and load,
browsable in Organon, and (for the boards) selectable as M in the Agon picker.

---

## 2. The proof exemplars (Alpha / propositional)

[`tools/build_propositional_exemplars.py`](../tools/build_propositional_exemplars.py)
builds these as real `ProofChain`s. Every step applies a Dau rule attestably and
must land on the stated conclusion. Together the four exercise all six rules, so the
set doubles as a tour of the calculus.

| UoD id | Claim | Moves | The point |
|---|---|---|---|
| `de_morgan` | ¬(P∧Q) ⊢ ¬P∨¬Q | `DC+`, `DC+` | A disjunction `A∨B` is drawn `~[ ~[A] ~[B] ]`, so De Morgan **is** the double-cut law: grow a double cut around each conjunct of `~[ (P)(Q) ]`. |
| `contraposition` | P→Q ⊢ ¬Q→¬P | `DC+` | **One move.** In EG, P→Q and its contrapositive are the *same graph* `¬(P∧¬Q)` up to a double cut — the contrapositive is read off the same picture. |
| `ex_falso_quodlibet` | ¬P ⊢ P→Q | `INS` | From a denied antecedent, anything follows — and the single move is insertion, legal *only* in a negative context (entertain, don't assert). |
| `hypothetical_syllogism` | P→Q, Q→R ⊢ P→R | `IT+`,`IT-`,`DC-`,`ERA`,`ERA` | The substantial one: iterate Q→R into P→Q and deiterate the shared Q — the EG form of "discharge the middle term" — then clear the scaffolding. |

Each stands as an **authored** derivation of a **cited** classical law, admitted at **low
[warrant](GLOSSARY.md#warrant)**: attested for correspondence, never asserted true. Low warrant
marks the manifest [floor](GLOSSARY.md#floor) (the baseline that may not be gone under).
Annotations carry the teaching notes, and a flag at the step level marks the crux of
the syllogism.

---

## 3. The domain-model boards

[`tools/build_domain_model_exemplars.py`](../tools/build_domain_model_exemplars.py)
builds these as `kind=domain_model` UoDs. They form a deliberate closed/open
contrast, the two regimes the open-world [peel](GLOSSARY.md#peel) (reading it from the outside in against the model) turns on.

> **Residence (relocated 2026-07-16, sweep #2 — the second relocation).** Every
> M-bearing exemplar in this catalogue holds its elements in **cells at even
> depth** of a standing world-scroll `~[ ~[cell] … ~[ ] ]`. Nothing contingent
> stands at depth 0, and at least one empty cut (the hold, plus any scars) keeps
> the standing structure vacuous
> ([M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE](M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE.md) §9).
> The boards carry the two-step construction chain that put them there: DC+
> then INS-of-cell from the blank sheet, both real rules, replayable. The
> dialogue exemplars record every M-change as an explicit rule-licensed step —
> `ADMIT_TO_M` performs one INS of a closed cell, `RETRACT_FROM_M` one ERA inside
> a cell, `REVISE_M` the challenge composite of ERA + INS in one step, leaving the
> emptied husk standing as a scar — and every verdict as a recorded `PEEL`
> step. The peel reads the cells' union (`world_scroll.m_view`), so every
> verdict quoted in this document stands unchanged. The standing gate remains
> `tests/test_corpus_polarity_discipline.py`.

### `zoo_world` — a closed taxonomy with Horn rules

Four named animals (Rex the dog, Tom the cat, Moby the whale, Pip the sparrow) stand
beside a subsumption spine authored as [scrolls](GLOSSARY.md#scroll) (a nested double cut, "if … then"): dog/cat/whale ⊑ mammal, sparrow ⊑ bird,
mammal ⊑ warm-blooded, bird ⊑ warm-blooded. **Materialized** (forward-chained to the
least Herbrand model), it derives every animal's kind and warmth. The chain decides
the universals, not a direct statement. As a board:

- *"Every mammal is warm-blooded"* and *"every dog is warm-blooded"* → **TRUE** (the
  second only via the dog→mammal→warm-blooded chain).
- *"Every warm-blooded thing is a mammal"* → **FALSE**, and the peel names **Pip**
  the sparrow (warm-blooded via bird, yet no mammal). This board serves the *holds /
  fails* outcomes and names a counterexample richer than a two-fact model can give.

The closed flag licenses ∀: silence reads as "no," so a refuting individual makes
the over-broad universal definitely false.

### `harbor_town` — an open civic world

Bayside stands as a harbor town; Greyrock, as an island with a lighthouse; a ferry runs
Bayside→Greyrock. Facts only, no closure. The relational ferry gives the peel
something to witness, and in the open world an unrecorded claim reads **UNKNOWN**,
not false:

- *"Bayside hosts a market"* → **UNKNOWN** — a candidate *new fact*, the independent
  outcome the [horizon](GLOSSARY.md#horizon) produces (not a refutation).
- *"The ferry runs Bayside→Greyrock"* → **TRUE** (present in the record).

This board stands as the contrast piece to `zoo_world`. The same kind of universal
reads differently open vs. closed; closing the world turns a sample into a law.

---

## 4. Playing them — the curated episodes

`src/agon_models.py` gains three `ExampleModel` episodes that wire the boards into the
Agon model picker (`GET /agon/models`) with a ready sample proposal each, so a
newcomer can select one and immediately see the peel:

| Episode id | Board | Proposal | Verdict |
|---|---|---|---|
| `zoo-chain` | zoo_world | every dog is warm-blooded | TRUE (via the materialized chain) |
| `zoo-refuted` | zoo_world | every warm-blooded thing is a mammal | FALSE (names Pip) |
| `harbor-open` | harbor_town | Bayside hosts a market | UNKNOWN (independent) |

A reader may *also* select the boards directly by UoD id (the picker lists every
corpus UoD); the curated entries serve as the one-click on-ramp. A test
(`tests/test_new_exemplars.py`) pins each episode's advertised verdict, so the picker
never promises an outcome the peel won't deliver.

---

## 5. Modality as diachronic branching

`possible_and_necessary` ([tools/build_modal_branching.py](../tools/build_modal_branching.py))
gives the diachronic, mark-free reading of ◇ and □
([MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md) §1, the *trajectory reading*).
A modal operator quantifies over a Kripke frame, and the branching history *is*
that frame. Worlds stand as sheets, and accessibility amounts to the legal-transition directed acyclic graph ([DAG](GLOSSARY.md#dag)). So:

> ◇φ = "some legal trajectory [scribes](GLOSSARY.md#scribe) φ" · □φ = "every legal trajectory scribes φ"
> — *possibility is branching, necessity is convergence.*

From a morning `(cloudy) (cold) (calm)`, two legal lines of development each drop a
feature and converge on `(cold)`. Reading off the four reachable sheets: **□ cold**
(on every trajectory — necessary), **◇ cloudy** and **◇ calm** (on some but not all —
possible, not necessary). No broken cut, no [tincture](GLOSSARY.md#tincture) (Peirce's Gamma colourings): the modality amounts to the shape of
the DAG.

[src/modal_query.py](../src/modal_query.py) supplies the thin missing code,
`possibly` / `necessarily` over a chain's reachability (`reachable_states`,
`leaf_states`), with predicate helpers (`scribes_relation`, `equals_graph`,
`is_blank`) and an `over="states"|"leaves"` choice (all reachable worlds, or just the
trajectory endpoints — over endpoints, a *transient* like cloudy isn't even possible).
It reads only DAG structure and Existential Graph Instance ([EGI](GLOSSARY.md#egi)) content, draws no mark, and adds no correspondence-check obligation (§3.3).
(The *alethic* reading — ◇/□ across the corpus's models M — is the inverse pivot,
`/agon/where-it-holds`.)

### 5.1 The Gamma demonstrations — Peirce's own modal drawings

Three further exemplars ([tools/build_gamma_modal_exemplars.py](../tools/build_gamma_modal_exemplars.py))
reconstruct specific modal meanings Peirce attempted to draw with Gamma, each with a
verified citation in its provenance (`theorem_source`); the full account lives in
[GAMMA_DEMONSTRATIONS.md](GAMMA_DEMONSTRATIONS.md).

| UoD id | Peirce figure | The demonstration |
|---|---|---|
| `broken_cut_square` | the broken cut, Lowell 1903 (CP 4.510–4.516; convention C10 at 4.410 — his Fig. 1 is "It rains") | all four modal statuses (◇¬ / □ / ◇ / □¬) as verdicts of one branching derivation; his R6 cut-conversion and □g⊨g, □g⊨◇g as frame facts; the CP 4.519 non-inference exhibited |
| `would_be_de_inesse` | P *de inesse*, *Prolegomena* (CP 4.546, 4.549) | the material conditional on one synchronic sheet — "too easily true"; the modal lens rightly finds no frame |
| `would_be_courses` | the blue-tinted strict implication (Ms 490, end of CP 4.575) | the would-be as a DAG of *courses of experience* (each edge a `new_fact` revision): G = "if Otto fails, Clara suicides" peels TRUE at **every** world — □G — while a contrast proposal is refuted by the ruin course |

On the reading surface, the **modal lens** gained a *proposal reading* (peel any compound G
across the worlds — ◇G/□G with per-world verdicts) and draws each world as a small
thumbnail. Challenge mode gained the `de-inesse` and `would-be-course` targets.
Tests: `tests/test_gamma_demonstrations.py`.

### 5.2 The forcing conditions — Cohen's poset read by the same lenses

`forcing_conditions` ([tools/build_forcing_conditions_demo.py](../tools/build_forcing_conditions_demo.py))
puts Paul Cohen's forcing conditions, the running example of Caterina & Gangle's
paper on forcing in Existential Graphs, into the corpus using only the machinery
above. A *condition* means a finite binary sequence, here a state of a developing
record. From ⟨1⟩ the reveals extend to ⟨1,1⟩, which forks into the incompatible
extensions ⟨1,1,1⟩ and ⟨1,1,0⟩, drawing the splitting property ("every condition is
dominated by two incompatible conditions") as a genuine DAG fork. Each
extension enters as a `new_fact` revision, a game move rather than a deduction. The correct-set
property δ₁ = "no entry is a zero" (`~[ (zero *p) ]`) serves as the standing
`audit-proposal`. It holds along the all-ones branch and falls where the domination
is met: TRUE → TRUE → TRUE → FALSE under the audit lens. That flip gives the
structural reason a correct set discernible in the ground model cannot be generic.
The modal lens reads the **forcing trichotomy** off the same DAG, now named by
`modal_query.settlement`: `one` counts as *settled* (□, "∅ forces it"),
`zero` as *open* (◇ ∧ ¬□, "some condition forces it"), `two` as *excluded* (¬◇).
The dev memo
[FORCING_AND_THE_GAMMA_CROSSING.md](FORCING_AND_THE_GAMMA_CROSSING.md) carries the
full mapping between Cohen's construction and Arisbe's machinery.

## 6. A domain model transforming through dialog

`dialogue_model_revision` ([tools/build_dialog_model_evolution.py](../tools/build_dialog_model_evolution.py))
shows a reference model M revised episode by episode and persisted as **its own
history**. After each revision the standing proposal G = "every patient is insured"
peels against M, and the verdict moves as the dialogue admits evidence and as fresh
evidence unsettles it:

| State | Revision | "every patient is insured" |
|---|---|---|
| M0 | `(patient Ann) (patient Ben) (insured Ann)` | **FALSE** (Ben) |
| M1 | + admit `(insured Ben)` | **TRUE** |
| M2 | + admit `(patient Cal)` | **FALSE** (a new individual unsettles it) |
| M3 | + admit `(insured Cal)` | **TRUE** (settled again, for now) |

Each step carries a model-revising `new_fact` disposition, an independent proposal the
dialogue accepts and admits into the **standing world-scroll** `~[ ~[cell] … ~[ ] ]`.
M's elements reside in cells at even depth, the register of in-context agreement,
never a depth-0 posit (see
[M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE.md](M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE.md)
§9). Admission takes one rule-licensed **INS of a closed cell**, recorded as an
explicit `ADMIT_TO_M` chain step whose warrant rides on the step, not the ink. Each
verdict in the table likewise stands as an explicit, forever-recomputable `PEEL` step
([src/m_steps.py](../src/m_steps.py)). The exemplar
makes the manifest floor operational: **a model is never frozen**, and "fact" names the
defeasible status of the last-standing trajectory
([MANIFEST_AND_MEANING.md](MANIFEST_AND_MEANING.md),
[LEVEL_ZERO_AND_THE_REGISTERS.md](LEVEL_ZERO_AND_THE_REGISTERS.md) §5).

### Across the taxonomy of episode outcomes — `dialogue_swan_revision`

The insurance dialogue walks a single disposition (`new_fact`) four times. The
**taxonomy of game outcomes** ([ENDOPOREUTIC_GAME_GUIDE.md](ENDOPOREUTIC_GAME_GUIDE.md)
§"Taxonomy") reaches further: *each episode ends in a disposition, and the model-revising
ones are different **Peircean modes of inference*** (§IV: deduction / induction /
abduction). `dialogue_swan_revision`
([tools/build_swan_generalization.py](../tools/build_swan_generalization.py)) takes the
guide's own canonical example, **the swans**, and revises it across that taxonomy. G = "every
swan is white":

| State | Revision (disposition · mode) | "every swan is white" |
|---|---|---|
| M0 | swans Alba/Bianca (white), Ciel (colour unrecorded) | **FALSE** (Ciel uncovered) |
| M1 | observe Ciel is white — `new_fact` · induction | **TRUE** |
| M2 | leap to the law *all swans white* — `generalization` · induction | **TRUE** (a law, not a tally) |
| M3 | a new swan, Dover, arrives — `new_fact` · induction | **TRUE** — *the law covers Dover* |
| M4 | a black swan, Nox — `challenge_to_M` · abduction | **FALSE** — the law is relinquished |

Two things the insurance dialogue cannot show. **A law absorbs the newcomer:** at M3 a
new individual arrives with no recorded colour, yet G stays TRUE. The *generalization*
forward-chains and makes Dover white, where insurance's Cal (no rule in M) flipped the
verdict FALSE. Deduction over an inductive law, not a bare tally. **The irritation of
doubt revises M:** the black swan refutes the law, and the episode ends in
*challenge-to-M* (2b). **ONE licensed ERA inside its cell** relinquishes the
over-general law (erasure stays sound at even depth, the fallibilist pole, and the
emptied husk stands as a visible scar), and the anomaly enters as a fresh cell, both in
one explicit `REVISE_M` composite step. The DAG keeps the pre-challenge world.
Abduction corrects M — "the only logical operation which introduces any new idea."

[src/model_revision.py](../src/model_revision.py)'s `REVISION_TAXONOMY` enacts the
taxonomy. It holds the M-revising subset of the disposition taxonomy, each entry
carrying its mode and its structural **kind** (enlargement / relinquishment). Since sweep #2
(the second relocation) corpus and live loops alike perform the kinds as licensed cell
moves recorded by the explicit steps of [src/m_steps.py](../src/m_steps.py):
enlargement = `ADMIT_TO_M` (one INS of a closed cell); retraction = `RETRACT_FROM_M`
(one ERA inside a cell, where disuse-fading and refutation share the move and the
recorded `flavor` splits them); the challenge = `REVISE_M` (the ERA + INS composite);
world-withdrawal (the triple) retired to rare full replacement. The **live loops**
(`agon_evolution`, `live_runner`, the membranes) dispatch through the residence-aware
`revise_with_disposition` and open every chain with genuine DC+ · INS residence steps
(the [M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE](M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE.md)
§8.1 migration, discharged). The same calculus draws every other graph. The
dispositions that *don't* revise M (`redundancy`, `rejection`, `open_conjecture`, …)
stand as recorded judgments, not edits.

### Reading them in Organon — the **audit lens**

The Organon **audit lens** (`web_viewer/js/audit-lens.js`
over `GET /organon/uods/{id}/audit`) surfaces both dialogues. A standing proposal G peels
against every successive model M and draws as the **verdict ribbon**, with each transition
labelled by its disposition · mode and "verdict flips" flagged. Each UoD declares its own
proposal in an `audit-proposal` annotation, and the reader may type another. The companion
**modal lens** (`modal-lens.js` over `/modal`) reads ◇/□ off the branching history (§5).
Both remain read-only navigation projections, never the asserted drawing.

Tests for all of this: [tests/test_modal_and_dialog.py](../tests/test_modal_and_dialog.py)
(the modules + exemplars) and [tests/test_organon_routes.py](../tests/test_organon_routes.py)
/ [tests/test_organon_lenses_e2e.py](../tests/test_organon_lenses_e2e.py) (the lenses).

### The episode discharged in ink — `episode_discharge`

Here the EPG episode runs wholly as licensed rule applications, and its result
reaches M *derived, never inserted*
([tools/build_episode_discharge_demo.py](../tools/build_episode_discharge_demo.py);
M-residence memo §10). **ENTERTAIN** builds the premise "if M then (mammal Rex)"
as ink inside the agreed context: DC+ in M's even area, IT+ of M (the premise
consists of M's own ink), then INS of `~[P]`, with the empty inner cut standing
as the **vacuity rider** so the contingent conditional enters without force. The
DC+ must land in an even context at depth ≥ 2 — the **episode theorem** —
because an odd area gives no arena, and at depth 0 soundness itself puts the
discharge out of reach. A recorded **PEEL** confirms P; the law fires under
materialization. **DISCHARGE_TO_M** draws modus ponens — IT− of the premise
copies, IT− of the rider against the standing hold, DC− — and P lands in the
agreed content. The audited proposal moves **absent → derived-only →
standing**. Before, `(mammal Rex)` held true only through the materializer's
ephemeral forward chaining; after, it stands in M itself, drawn, a
`theorem_registration`. The standing hold amounts to ⊥ in scope (**the ⊥-door**:
four licensed moves could scribe *anything* into M), so the discharge step must
**cite its confirming peel**. That was ruling (b): the calculus stays pure, the
earning rides on the record. The polarity gate re-asserts every citation and
refuses any silent M-change (the m_view tripwire). `proof_character` reads the
chain **theorematic**, since scribing the candidate serves as Peirce's auxiliary
line.

## 7. The second-order quotation exemplars (stages ⓪ and ① of the crossing)

The crossing verdicts of 2026-07-16
([CROSSING_DECISION_BRIEFS.md](CROSSING_DECISION_BRIEFS.md)) took the second-order
frontier *exemplar-first*. Rather than wait for a demonstrated need, the verdicts chose
three fitting cases to illustrate graphs-about-graphs clearly and robustly. Stage ⓪
built the **overlay stratum** with no protected-core change: a quotation stands as a
proposition-sorted *name* whose sort and target live in an overlay record beside the
EGI (`src/quotation_overlay.py`, persisted as `quotations.json`). **Stage ① (B-min,
the authorized core opening, same day)** moved the sort into the core. The data model
carries `sort` and `quotation` maps; each exemplar's scribing takes an explicit `QUOTE`
chain step, neutral, since a mention asserts nothing. The quoted graph gets **drawn in
the host** inside a committed dotted oval, opaque to the calculus: no rule operates
inside, and the peel and materializer skip it. The correspondence check holds the drawn
convention total — dotted stroke, sort badge, attachment tie.

Each quotation attests against the second-order law (`src/second_order_check.py`)
**at build time**. S1 stratification reads off the drawn enclosure. S2 checks
quote-equals-quoted against an independent ground, plus the correspondence check
(§3.3) one level down through the real layout engine. **S3 (read-back one order up)
CHECKED**: the drawing itself recovers the `(sort, quoted)` device through the
second-order reader. S5 runs per state of the referenced trajectory, and S4 names the
horizons. The cross-UoD mention's quoted-half stays an honestly named horizon (an oval
cannot inline another universe), and linear notations show the exemplars' **first-order
projection** with the limit named (no linear sort syntax exists at B-min).
[tools/build_quotation_exemplars.py](../tools/build_quotation_exemplars.py) builds all
three; each houses its claims in a cell of a standing world-scroll (nothing contingent
at depth 0) and exports a `quotation_glyph.svg` showing the dotted-oval convention.

- **`swan_third_tense` — the swan's third tense.** `(superseded "M_swan_law"
  "Nox")` holds the law withdrawn in `dialogue_swan_revision` (§6) before the mind
  as a labeled exhibit, **present without force**. That names the third tense the
  validity discipline exposed: in force, withdrawn-remembered, present-without-force.
  First order cannot do this, since a double cut around the old law still binds. The name
  resolves through the withdrawal step's own record (`REVISE_M`'s `subgraph_egif`),
  and per state as well (S5, Cohen's R_G reading): the drawn law recovers structurally at
  s4–s7 and nowhere else, the horizon named, never silent.
- **`forcing_forces` — `(forces s φ)`.** The imported-exact nominee on the
  forcing-trichotomy exemplar (`forcing_conditions`), under the **Montague rider**.
  `forces` enters only as a defined, grounded, decidable relation — the peel at s,
  `modal_query.settlement` for the trajectory — never as an axiomatized primitive with
  reflection schemas. The trichotomy stands as drawn, state-indexed claims: ∅ forces *one*
  (settled), ⟨1,1,0⟩ forces *zero* (open), and nothing forces *two* (excluded,
  drawn as a genuine negation). Every claim recomputes before it gets scribed, and
  S5 reads the trichotomy as trajectory-relative resolution: φ₁ resolves at every
  state, φ₂ on one branch, φ₃ nowhere.
- **`peirce_law_commentary` — cross-UoD mention.** A commentary naming
  `peirce_law` (§2) as *object*. The quoted graph holds the whole theorem, resolved by
  corpus id without importing one element of it — mention, not use, so no
  co-assertion crosses universes (the reference-node increment-2 fork's mention
  side, exercised overlay-first). It carries the real scholarly citation
  (`scholarly_citation.citation_for` → Peirce 1885, *On the Algebra of Logic*).

Tests: [tests/test_quotation_overlay.py](../tests/test_quotation_overlay.py) (the
mark, the enclosure-off-the-drawing discipline, the impredicative-flat refusal, the
three exemplars re-attested, the glyph's geometry-neutrality) beside
[tests/test_second_order_check.py](../tests/test_second_order_check.py) (the law and
its falsifiers).
