# Automated model development: the Agon as the engine of change

**Status**: design-of-record · fixes the *shape* of the idea and the first build, not a
full implementation · **first membrane = closed / internal** (de-risk the loop before
opening it) · aim = **discovery** · **Drafted**: 2026-06-30

> **The question this answers.** Conway's Game of Life takes simple *local rules*, iterates
> them over *generations*, and yields *emergent* global behaviour. Is there an analogue for
> letting a domain model **M** *develop itself* in Arisbe — run it and see what emerges,
> rather than hand-authoring M? And if so, what is the "tick", what are the "rules", and
> where does the novelty come from?

This note is the design-of-record for that question. The short answer reframes the seed:
**the engine of change is not a set of deterministic local rules — it is the Agon (the
[Endoporeutic](GLOSSARY.md#endoporeutic) Game).** A generation is a *round of the game*. The
emergence lives in how rounds are *disposed*, and the open research question — the rub on
whether the open-ended version is even possible — is the **membrane**: where each round's
fresh input comes from.

Related: [ENDOPOREUTIC_GAME_GUIDE.md](ENDOPOREUTIC_GAME_GUIDE.md) (the game, the disposition
taxonomy), [DOMAIN_ORACLE_AND_M.md](DOMAIN_ORACLE_AND_M.md) (M queried, the [peel](GLOSSARY.md#peel)),
[GENERATION_AND_TESTING.md](GENERATION_AND_TESTING.md) (given M, then G — choose, peel,
decide), [EXEMPLARS.md](EXEMPLARS.md) §6 (the swan revision walk — *one hand-played round
sequence of exactly this loop*), [MANIFEST_AND_MEANING.md](MANIFEST_AND_MEANING.md) (the
[warrant](GLOSSARY.md#warrant) floor: attest correspondence, not truth),
[BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md](BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md) (2026-07-17:
the loop mapped against the author's Minimal Predictive Automaton; design-of-record for the
missing **action arm** — the staged path to directed engagement).

> **One regime (updated 2026-07-16, sweep #2 — the second relocation).** The **live loop this
> document designs** (`agon_evolution.run` and everything downstream) now plays over M resident
> in **cells at even depth** of the standing world-scroll `~[ ~[cell] … ~[ ] ]`, same as the
> corpus: the chain opens with genuine DC+ · INS residence steps (the seed as one closed cell),
> every disposition lands as a licensed INS-of-cell / ERA-in-cell with its executed derivation
> recorded (`revise_with_disposition` is residence-aware), and disuse-decay is the *same*
> licensed ERA as refutation, distinguished by the recorded `flavor` (`pruned:disuse` — the
> *faded* tense). Every reader goes through `m_view` (identity for a bare sheet-level fixture).
> `src/world_scroll.py` + `src/m_steps.py`, gated by
> `tests/test_corpus_polarity_discipline.py`; see
> [M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE.md](M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE.md) §9 —
> the §8.1 loop migration is discharged. Where this document says "on M's sheet", read *in M's
> cells*.

---

## 1 · The reframing — why it isn't a cellular automaton

The tempting first reading is a logical Game of Life: cells are facts, local rules fire each
tick, patterns emerge. It breaks on two points, and the break is instructive.

- **Materialization is monotonic; Life is not.** The closest existing "tick" —
  `model_materialization.materialize_egi`, which forward-chains M's Horn fragment — only ever
  **adds** facts and runs to a fixpoint (the least Herbrand model). Life's whole character
  comes from cells **dying**. Growth-to-saturation is not emergence; it's closure.
- **The interesting dynamics aren't local at all.** What makes a model *develop* in Peirce's
  sense is not a neighbour-count rule but **inquiry**: a proposition is put forward, tested
  against the world, and the community *disposes* of the outcome — admitting a fact,
  leaping to a law, relinquishing a refuted law, registering a theorem. That is the Agon, and
  its outcomes are **negotiable**, not determined.

So the analogy survives only at the level of *structure*: simple repeated step → iterated
over generations → emergent global behaviour nobody scripted. The **step** is a game round;
the **rule that fires** is a disposition chosen by agents; the **death** is relinquishment
(retraction), driven by disuse and by better explanations.

**The decisive structural difference is not the plane but the closure of the dynamics.**
Conway's Life is canonically defined on the *infinite* lattice ℤ² — as unbounded as the
sheet of assertion; bounded or toroidal grids are implementation approximations, not the
object. Life advances by a *fixed* local rule whose outcome is determined by a
neighbour-count, so its growth, though spatially unbounded, is bounded *by the rule*. The
Agon's sheet of assertion has no such fixed rule: it can always grow, and its growth is
bounded only by **selection from outside** — the test (②), the disposition (③), and
disuse-decay (⑤). In Life the constraint is an *internal, fixed rule*; in the Agon it is
*internal rules + outside selection*. Life is a closed determinism; the Agon loop is an
open negotiation — which is precisely why the **membrane** (§5) is the crux, the place
where the outside, which does all the bounding, makes contact.

## 2 · A generation is a round of the game

One generation = one round, with five beats. Each already has a home in the codebase; the
loop that *strings them together automatically* is what's new.

| Beat | What happens | Existing code |
|------|--------------|---------------|
| **① Produce** | A candidate graph **G** is scribed (the *membrane* — §5). | new `Proposer` (closed: corpus/mutation) |
| **② Test** | G is peeled against the *current* M, closed- or open-world. | `semantic_game.evaluate(G, oracle)` → `Verdict3` + witness/counterexample; `model_materialization.materialize_egi` first so laws cover new individuals |
| **③ Negotiate** | Several agents argue for a *disposition* of the outcome; one resolves. | `model_revision.REVISION_TAXONOMY` (9 dispositions, each mode × kind) — §3 |
| **④ Inject** | The chosen disposition revises M into M′, a new diachronic state. | `model_revision.revise_with_disposition(...)` |
| **⑤ Decay** | Usage is updated; stale elements fall from use and are erased. | new decay pass → `retract_relation` / `retract_subgraph` — §4 |

Run K rounds and the M-states form a [diachronic](GLOSSARY.md#uod) chain — exactly the shape
`tools/build_swan_generalization.py` builds **by hand** today (`ProofChain` of `REVISE_M`
steps → a `DOMAIN_MODEL` UoD). The audit lens already draws that chain as a verdict ribbon
labelled by disposition·mode, so an *evolved* trajectory is visualised for free.

> **The swan exemplar is the unit test for this whole design.** Its four innings — observe
> Ciel (`new_fact`, induction) → leap to "all swans white" (`generalization`, induction) →
> the law covers newcomer Dover (`new_fact`, deduction) → meet black swan Nox and relinquish
> the law (`challenge_to_M`, abduction) — are one trajectory of beats ①–④, played by a human
> author. Automating the *player* is the work.

## 3 · The agents — and where the emergence lives

Three roles, of which exactly one is non-mechanical. This separation is the crux of keeping
the system sound while letting it surprise us.

- **The Proposer(s) — the membrane (①).** Source of candidate graphs. Pluggable; §5.
- **The Skeptic — mechanical (②).** *Not* an agent with an opinion. M decides, via
  `semantic_game`. The verdict is truth-in-the-current-model, three-valued and sound
  open-world. No negotiation here — this is the Agon's incorruptible referee.
- **The Agonothetes panel — the negotiation (③).** Given the verdict + witness/counterexample
  + the structure of G, **several agents argue for different dispositions of the same
  outcome**, and one resolves. *This is where trajectories diverge and emergence lives.* A
  FALSE-with-counterexample anomaly can be disposed as `challenge_to_M` (relinquish the
  impugned law — the black-swan move) **or** `abductive_hypothesis` (admit an explanation
  that saves it) — and which agent wins reshapes everything downstream. A TRUE-and-entailed G
  is `theorem_registration`; a TRUE-but-independent G is `new_fact`; an UNKNOWN gap invites
  `definition` or `conditional_acceptance`. The panel is *plural by design*: with one policy
  the system is deterministic; with several it branches (and the branches are first-class in
  the DAG).
- **The clerk — mechanical (④⑤).** Applies the resolved disposition, records the new
  diachronic state, runs the decay pass.

In the **closed first build** the panel is a set of deterministic *policy-agents* (heuristics
keyed on verdict + structure) that vote — reproducible, no external dependency, yet still
exercising the negotiation structure. In the **open** build the same socket takes reasoning
agents (LLM / human).

## 4 · Selection by use — the death pressure

"Elements of the model will fall from use and be erased when new facts or better explanations
emerge." That is two distinct death triggers, and only the second exists today:

- **Supersession (have it).** A *better explanation* relinquishes the one it beats — the
  over-general law dropped when the black swan arrives. This is the `challenge_to_M` /
  `reductio` dispositions, enacted by `retract_subgraph` (a genuine Dau **ERA** over a
  sheet-level cut, reconstruction-verified). Already in `model_revision`.
- **Disuse-decay (new).** An element *not invoked* across rounds loses salience and is
  eventually erased — relinquishment by *attrition*, not by refutation. This needs a small
  **usage ledger** over the trajectory: each round, the elements G *touches* (its relations,
  its individuals, the laws that fired in ②) are reinforced; untouched elements decay; below a
  threshold an element is dropped via `retract_relation` / `retract_subgraph`. Geometry-free,
  additive, reading only sheet facts + the chain.

The ledger is what makes this *selection* rather than mere accretion: M is bounded, so growth
forces pruning, and what survives is what keeps earning its place in the dialogue. (Decay must
never erase the *only* support for a standing-TRUE proposal without a verdict flip — the
audit lens makes such flips visible, which is the honest signal that the model changed.)

## 5 · The membrane — the open question, staged

The membrane is "regular input from somewhere." Whether the *open* membrane is feasible is
the genuine viability question, so the build is **staged** — closed first, exactly the
"harness before the leap" pattern the rest of this codebase uses.

- **Stage 0 — closed / internal (the first build).** Proposals are drawn or structurally
  mutated from the *existing corpus*: a `CorpusProposer` (replays/perturbs corpus G's) or a
  `MutationProposer` (Dau-legal structural mutation of corpus graphs, seeded → reproducible).
  A closed membrane cannot invent genuinely new facts, so what it *discovers* is **tensions
  and consequences latent in the corpus** — which laws the corpus already commits to, which
  proposals it cannot settle, which over-generalizations a later proposal refutes. That is
  real discovery, and it proves the loop, the negotiation, and the decay are sound **before**
  we answer the hard question. No external dependency; fully reproducible.
- **Stage 1 — open (the frontier).** The same `Proposer` socket takes an external source of
  *novelty*: an **LLM proposer** (the "LLM proposes / Agon disposes" pattern — genuine new
  facts and laws, tested and pruned by the incorruptible referee), a **human** proposing each
  round through the UI, or an **online reference** (pull facts from an imported ontology /
  external source as the input stream). This is where open-ended discovery — and the
  viability risk — actually lives. Built only once Stage 0 shows the loop is worth feeding.

## 6 · What counts as a discovery

The aim is discovery, so the loop must *surface* its finds rather than just churn:

- **A survivor law** — a `generalization` admitted in some round that is still standing after
  K rounds (reinforced, never relinquished). A regularity the corpus implied but no one
  wrote.
- **A registered theorem** — a `theorem_registration`: G was entailed by M and is now an
  earned, derived fact.
- **An attractor / oscillation** — a sub-model that re-forms after perturbation, or a
  proposal whose verdict cycles as the membrane feeds related G's. The Game-of-Life echo,
  read off the verdict ribbon.
- **A productive anomaly** — a `challenge_to_M` that relinquished a law and reshaped the
  trajectory (the black-swan moment), flagged for human review.

Discovery output is a **ranked digest over the trajectory UoD** (survivors, theorems,
anomalies), drawn with the existing audit/modal lenses. Nothing is asserted into the corpus
automatically.

## 7 · The correspondence floor stays put

Automation changes nothing about the contract. Every scribed M-state still **attests §3.3**
at save/load (the trajectory is a real diachronic UoD through `tomos_service`). Every
admitted fact/law is **low warrant** — a posit, not a proof — until tested through the Agon;
the audit ribbon shows exactly when a verdict turned. And a developed M reaches the **attested
corpus only by the mode contract** (tested through Agon, or a style-only reprojection) — there
is no auto-promotion. The loop is a *generator of candidates for inquiry*, not an oracle of
truth.

## 8 · First build (the concrete next step)

`src/agon_evolution.py` — additive, geometry-free, **not** core-protected (it composes
`semantic_game`, `model_materialization`, `model_revision`, and the diachronic UoD; it touches
no protected module):

- a `Proposer` Protocol + a closed `CorpusProposer` / `MutationProposer` (Stage 0);
- an `Agonothetes` panel of deterministic policy-agents that vote a disposition from
  `REVISION_TAXONOMY` given (`Verdict3`, witness/counterexample, G's structure);
- a `UsageLedger` + decay pass (§4);
- a `run(model, proposer, rounds=K) → TransformationChain` driver that strings beats ①–⑤ and
  emits a `DOMAIN_MODEL` UoD (the same shape `build_swan_generalization.py` produces by hand);
- a `discoveries(chain) → digest` pass (§6).

A `tools/build_agon_evolution_demo.py` then runs K automated rounds on an existing corpus
model (e.g. `zoo_world` or the swan model) and saves the emergent trajectory, viewable through
the audit lens. Tests (`test_agon_evolution.py`): each beat in isolation; a closed run is
reproducible under a fixed seed; decay erases a stale element and never silently drops the
sole support of a standing-TRUE proposal; the swan trajectory is *reproducible by the loop*
when fed its own proposals (the loop generalises the hand-played exemplar).

## 9 · Deferred / open

- The **open membrane** (Stage 1) and its viability — the real research question.
- **Negotiation among reasoning agents** (LLM panel) vs deterministic policy-agents; how to
  record a genuine *disagreement* in the DAG (branch per dissenting disposition?).
- **Decay calibration** — what counts as "use", the threshold, and proving the floor (never
  erase the last support of a standing claim without a visible flip).
- Whether **Conway's Life itself** is worth encoding as a closed object-level CA-in-EG demo,
  separately, purely for the "moving pictures of thought" pedagogy — a sibling idea, not this
  loop.
