# Corpus Exemplars — proofs and boards that put meat on the bones

> **What this is.** A short catalogue of the worked exemplars seeded into the corpus
> so that Organon has things to read and Agon has somewhere to play: **proof
> exemplars** (§2), **domain-model boards** (§3) and the curated **innings** that
> wire them into the game picker (§4), a **branching-modality** episode (§5), and a
> **model that transforms through dialog** (§6). It is a guide to *what is there and
> why*, not a how-to for authoring more (that pattern lives in the `tools/build_*.py`
> scripts and [CORPUS_AND_IMPORT_MODEL.md](CORPUS_AND_IMPORT_MODEL.md)).
>
> **Companions:** [DOMAIN_ORACLE_AND_M.md](DOMAIN_ORACLE_AND_M.md) (how a board is
> queried as a model M) · [GENERATION_AND_TESTING.md](GENERATION_AND_TESTING.md)
> (the inning *given M, then G*) · [ENDOPOREUTIC_GAME_GUIDE.md](ENDOPOREUTIC_GAME_GUIDE.md).
>
> *Created 2026-06-29.*

---

## 1. Why these exist

Arisbe's machinery is only as legible as the worked examples that exercise it. Two
gaps were filled in one pass:

- **Proofs to read.** Organon is a read-only archive; it wants a spread of *worked
  derivations* a teacher or student can step through. The existing set (Peirce's
  Law, Barbara, Leibniz's *Praeclarum*, the group-identity uniqueness, beta modus
  ponens) leaned toward the harder theorems. The new quartet adds **short, iconic
  propositional laws** — including two that teach an EG-specific insight worth more
  than the theorem.
- **Boards to play on.** The Endoporeutic Game's interpretation register is *given
  M, then G* — and you cannot play without an M. The curated persona models in
  `src/agon_models.py` are inline on-ramps; the corpus wanted **richer,
  browsable domain-model UoDs** that double as game boards. Two were added, a
  closed/open contrast.

Everything below is a real corpus UoD: §3.3-attested at save and load, browsable in
Organon, and (for the boards) selectable as M in the Agon picker.

---

## 2. The proof exemplars (Alpha / propositional)

Built by [`tools/build_propositional_exemplars.py`](../tools/build_propositional_exemplars.py)
as real `ProofChain`s — every step an attestable Dau-rule application that must
land on the stated conclusion. **Together the four exercise all six rules**, so the
set doubles as a tour of the calculus.

| UoD id | Claim | Moves | The point |
|---|---|---|---|
| `de_morgan` | ¬(P∧Q) ⊢ ¬P∨¬Q | `DC+`, `DC+` | A disjunction `A∨B` is drawn `~[ ~[A] ~[B] ]`, so De Morgan **is** the double-cut law: grow a double cut around each conjunct of `~[ (P)(Q) ]`. |
| `contraposition` | P→Q ⊢ ¬Q→¬P | `DC+` | **One move.** In EG, P→Q and its contrapositive are the *same graph* `¬(P∧¬Q)` up to a double cut — the contrapositive is read off the same picture. |
| `ex_falso_quodlibet` | ¬P ⊢ P→Q | `INS` | From a denied antecedent, anything follows — and the single move is insertion, legal *only* in a negative context (entertain, don't assert). |
| `hypothetical_syllogism` | P→Q, Q→R ⊢ P→R | `IT+`,`IT-`,`DC-`,`ERA`,`ERA` | The substantial one: iterate Q→R into P→Q and deiterate the shared Q — the EG form of "discharge the middle term" — then clear the scaffolding. |

Each is an **authored** derivation of a **cited** classical law, admitted at **low
warrant** (attested for correspondence, never asserted true — the manifest floor).
Annotations carry the teaching notes; the crux of the syllogism is flagged at the
step level.

---

## 3. The domain-model boards

Built by [`tools/build_domain_model_exemplars.py`](../tools/build_domain_model_exemplars.py)
as `kind=domain_model` standalone UoDs. They are a deliberate **closed/open
contrast**, the two regimes the open-world peel turns on.

### `zoo_world` — a closed taxonomy with Horn rules

Four named animals (Rex the dog, Tom the cat, Moby the whale, Pip the sparrow) plus
a subsumption spine authored as scrolls: dog/cat/whale ⊑ mammal, sparrow ⊑ bird,
mammal ⊑ warm-blooded, bird ⊑ warm-blooded. **Materialized** (forward-chained to the
least Herbrand model), it derives every animal's kind and warmth — so universals are
decided *through the chain*, not stated directly. As a board:

- *"Every mammal is warm-blooded"* and *"every dog is warm-blooded"* → **TRUE** (the
  second only via the dog→mammal→warm-blooded chain).
- *"Every warm-blooded thing is a mammal"* → **FALSE**, and the peel names **Pip**
  the sparrow (warm-blooded via bird, yet no mammal). The board for the *holds /
  fails* outcomes, with a named counterexample richer than a two-fact model can give.

The closed flag is what licenses ∀: a silence is read as "no," so a refuting
individual makes the over-broad universal definitely false.

### `harbor_town` — an open civic world

Bayside is a harbor town; Greyrock is an island with a lighthouse; a ferry runs
Bayside→Greyrock. Facts only, **no closure**. The relational ferry gives the peel
something to witness, and the open world means an unrecorded claim is **UNKNOWN**,
not false:

- *"Bayside hosts a market"* → **UNKNOWN** — a candidate *new fact*, the independent
  outcome the horizon produces (not a refutation).
- *"The ferry runs Bayside→Greyrock"* → **TRUE** (present in the record).

The contrast piece to `zoo_world`: the same kind of universal reads differently open
vs. closed — closing the world is what turns a sample into a law.

---

## 4. Playing them — the curated innings

`src/agon_models.py` gains three `ExampleModel` innings that wire the boards into the
Agon model picker (`GET /agon/models`) with a ready sample proposal each, so a
newcomer can select one and immediately see the peel:

| Inning id | Board | Proposal | Verdict |
|---|---|---|---|
| `zoo-chain` | zoo_world | every dog is warm-blooded | TRUE (via the materialized chain) |
| `zoo-refuted` | zoo_world | every warm-blooded thing is a mammal | FALSE (names Pip) |
| `harbor-open` | harbor_town | Bayside hosts a market | UNKNOWN (independent) |

The boards are *also* selectable directly by UoD id (the picker lists every corpus
UoD), with the curated entries being the one-click on-ramp. A test
(`tests/test_new_exemplars.py`) pins each inning's advertised verdict, so the picker
never promises an outcome the peel won't deliver.

---

## 5. Modality as diachronic branching

`possible_and_necessary` ([tools/build_modal_branching.py](../tools/build_modal_branching.py))
is the diachronic, **mark-free** reading of ◇ and □
([MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md) §1, the *trajectory reading*).
A modal operator is a quantifier over a Kripke frame, and the branching history *is*
that frame — worlds are sheets, accessibility is the legal-transition DAG. So:

> ◇φ = "some legal trajectory scribes φ" · □φ = "every legal trajectory scribes φ"
> — *possibility is branching, necessity is convergence.*

From a morning `(cloudy) (cold) (calm)`, two legal lines of development each drop a
feature and converge on `(cold)`. Reading off the four reachable sheets: **□ cold**
(on every trajectory — necessary), **◇ cloudy** and **◇ calm** (on some but not all —
possible, not necessary). No broken cut, no tincture: the modality is the shape of
the DAG.

The thin missing code is [src/modal_query.py](../src/modal_query.py) —
`possibly` / `necessarily` over a chain's reachability (`reachable_states`,
`leaf_states`), with predicate helpers (`scribes_relation`, `equals_graph`,
`is_blank`) and an `over="states"|"leaves"` choice (all reachable worlds, or just the
trajectory endpoints — over endpoints, a *transient* like cloudy isn't even possible).
It reads only DAG structure + EGI content, draws no mark, and adds no §3.3 obligation.
(The *alethic* reading — ◇/□ across the corpus's models M — is the inverse pivot,
`/agon/where-it-holds`.)

## 6. A domain model transforming through dialog

`dialogue_model_revision` ([tools/build_dialog_model_evolution.py](../tools/build_dialog_model_evolution.py))
shows a reference model M revised inning by inning and persisted as **its own
history**. The standing proposal G = "every patient is insured" is peeled against M
after each revision, and the verdict moves as the dialogue admits — and is unsettled
by — evidence:

| State | Revision | "every patient is insured" |
|---|---|---|
| M0 | `(patient Ann) (patient Ben) (insured Ann)` | **FALSE** (Ben) |
| M1 | + admit `(insured Ben)` | **TRUE** |
| M2 | + admit `(patient Cal)` | **FALSE** (a new individual unsettles it) |
| M3 | + admit `(insured Cal)` | **TRUE** (settled again, for now) |

Each step is a model-revising `new_fact` disposition — an independent proposal the
dialogue accepts, juxtaposed onto M's sheet as a new posit at low warrant. The thin
missing code is [src/model_revision.py](../src/model_revision.py): `assert_fact`
(enlargement) and `retract_relation` (relinquishment — *free to demote*, the ERA
dual), dispatched by `revise_with_disposition`. The exemplar makes the manifest floor
operational: **a model is never frozen**, and "fact" is the defeasible status of the
last-standing trajectory ([MANIFEST_AND_MEANING.md](MANIFEST_AND_MEANING.md),
[LEVEL_ZERO_AND_THE_REGISTERS.md](LEVEL_ZERO_AND_THE_REGISTERS.md) §5).

Tests for both: [tests/test_modal_and_dialog.py](../tests/test_modal_and_dialog.py).
