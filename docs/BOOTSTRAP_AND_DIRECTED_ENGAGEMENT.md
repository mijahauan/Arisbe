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
> [CHAIN_OF_SEMIOSIS.md](CHAIN_OF_SEMIOSIS.md) (the grounding).
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
| **Action space *A*** | **Missing.** Arisbe predicts, probes, and revises — but it never *intervenes*: no reach is chosen by expected yield, and nothing pushes back on the source | NOT BUILT |

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
  kept and re-attempted as legibility improves) rather than a per-poll report field.

**Rung 2 — mutual co-evolution (pushing back).** The full functional circle: M's contested
frontier surfaced *to the source* — e.g. suggested edits / flagged inconsistencies offered
back to the wiki-world — so the world and the model shape each other. Named in
AUTOMATED_ENDOPOREUTIC_GAME §4c as the future edge. This rung has real outward-facing
consequences (Arisbe would be *acting* on a shared world) and therefore needs its own
ethics-and-etiquette design before any build; nothing below rung 2 acts outside Arisbe's
own polls.

**What rung 1 is *not*:** it is not a new membrane, a new referee, or a change to the
calculus. The mode contract and the low-warrant floor (the "border guards" of
AUTOMATED_ENDOPOREUTIC_GAME §4d) are untouched; only the *conduct* of inquiry — Peirce's
methodeutic, explicitly outside the game — gains machinery. Nothing auto-promotes;
progression, not progress.

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
