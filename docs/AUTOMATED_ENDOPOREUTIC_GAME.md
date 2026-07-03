# The automated Endoporeutic Game: three roles, one incorruptible referee

**Status**: design-of-record · **Stages 1–3 BUILT** (`src/agon_llm.py`, 2026-06-30) — the
LLM **Graphist** (doubt), **Grapheus** (defense), and **Agonothetes** (judge + branch-the-DAG),
all three under the mechanical referee · the **§6 meta-learning instruments**
(`src/agon_metalearning.py`) + **three §4b open membranes** — raise-only
(`src/discourse_membrane.py`), raise-and-resolve (`src/resolving_membrane.py`), wiki-dispute
(`src/wiki_dispute_membrane.py`) — the **live runner** (`src/live_runner.py`, §10) and the **first
live source, Wikidata** (`src/wikidata_source.py`) BUILT · §4c–4d frame the whole as a *model
living with a given reality through the membrane* and locate the drive (**tropism**), the coupling
(**dianexus**), and the not-yet-legible (**horizon**) in the *methodeutic surround outside the
calculus* · aim = **discovery** · **Drafted**: 2026-06-30

> **The question this answers.** Can the Endoporeutic Game be played *automatically* — no
> ponderous human in the loop — by AI agents that, starting from scratch, build a domain
> model M? Pit two agents (a **Graphist** whose motive is *doubt*, a **Grapheus** whose motive
> is to *defend* M) under a third that *judges* (the **Agonothetes**), and let the game run.
> What shape does that take, what keeps it from degenerating into two chatbots agreeing with
> each other, and how can *running the game teach us how the game itself works*?

This note is the design-of-record. It is the LLM-agent successor to
[AUTOMATED_MODEL_DEVELOPMENT.md](AUTOMATED_MODEL_DEVELOPMENT.md) (the *closed* loop, with
mechanical agents): there the membrane and the players were deterministic; here they become
reasoning agents — while the thing that decides *truth-in-M* stays mechanical and
incorruptible.

Related: [AUTOMATED_MODEL_DEVELOPMENT.md](AUTOMATED_MODEL_DEVELOPMENT.md) (the closed loop this
extends), [ENDOPOREUTIC_GAME_GUIDE.md](ENDOPOREUTIC_GAME_GUIDE.md) (the game + disposition
taxonomy), [DOMAIN_ORACLE_AND_M.md](DOMAIN_ORACLE_AND_M.md) (M queried, the [peel](GLOSSARY.md#peel)),
[MANIFEST_AND_MEANING.md](MANIFEST_AND_MEANING.md) (the floor: *correspondence, not truth*),
[CONTRIBUTION_AND_PRIOR_ART.md](CONTRIBUTION_AND_PRIOR_ART.md) (where this sits in the
literature — §8).

---

## 1 · The reframing — the game, not deterministic rules

The closed loop already establishes the crucial point: a *generation is a round of the game*,
and the engine of change is the Agon (the disposition taxonomy), not local rules. This note
replaces the loop's *mechanical* players with **LLM agents**, and adds the move the closed
loop lacks — the **Grapheus's defense**. What stays fixed is the substrate: the diachronic
UoD, the §3.3 correspondence attestation, the disposition taxonomy, and the mechanical peel.

## 2 · The three roles + the incorruptible referee

The single principle everything hangs from: **the LLMs argue; the calculus decides.** Two
language models left alone will co-hallucinate a fluent, self-consistent, *groundless* model —
that is the failure mode, and it is fatal. What prevents it is that `semantic_game.evaluate`
(the peel) sits *underneath* the game as a truth-teller no agent can fake, and **every LLM
utterance is reduced to a calculus artifact and re-checked** before it counts. Free prose is
allowed only as logged *rationale*, never load-bearing.

The roles (the author's assignment; they map cleanly onto verifier/falsifier + judge):

- **Graphist — the motive of *doubt*.** Proposes a graph that stresses M. The variation
  operator; the source of the irritation that drives inquiry.
- **Grapheus — the motive to *defend* M.** Given the verdict, argues the *minimal* revision
  that conserves M's coherence while honestly answering the proposal. The selection pressure
  toward parsimony and coherence.
- **Agonothetes — the *judge*.** Chooses the disposition the exchange warrants (from the
  `REVISION_TAXONOMY`), enacts it, §3.3-attests it, and decides whether the episode closes.

**Only one role is non-mechanical at truth-time.** The **referee** — the peel — determines
truth-in-M; it is not an agent with an opinion. The episode anatomy:

| Beat | Who | Emits (a checkable artifact) |
|------|-----|------------------------------|
| ① open | Graphist | a proposition G (FOL → EGIF) + a *doubt-type* |
| ② test | **referee (mechanical)** | `Verdict3` + witness/counterexample — ungameable |
| ③ defend | Grapheus | the minimal disposition + its EGIF payload (*applied and re-peeled*) |
| ④ counter | Graphist | push back / sharpen / accept |
| ⑤ resolve | Agonothetes | the chosen disposition — enacted + §3.3-attested |

All three arguing roles are now LLM agents: ① the Graphist, ③ the Grapheus (a `PolicyAgent`
in the panel), ⑤ the Agonothetes (judging among the votes cast). Only ② — the peel — is
mechanical, and it stays that way. Each LLM move is **reduced to a calculus artifact and
re-checked** before it counts: ① the doubt must parse to an EGIF; ③ the defense must *apply*
(`revise_with_disposition`) and is *re-peeled*; ⑤ the judge may only pick among the votes
actually cast (it returns an index — it cannot fabricate a disposition or overrule the verdict).
See §9 for the code.

## 3 · From scratch

M₀ = the blank sheet (⊤). The run has two emergent phases: **accretion** (the Graphist posits
foundational vocabulary/facts; the Grapheus has nothing to defend, so it mostly accepts —
`definition`/`new_fact`; M bootstraps) and **contestation** (once there is structure, the
Graphist stresses it and the Grapheus defends). The transition is not scheduled; you cannot
stress what is not there yet. Stage 1's `attention_brief` handles the blank sheet by *inviting
bootstrapping*.

## 4 · The doubt-engine

The Graphist needs a drive that does not run dry and stays *relevant*. It is a portfolio, not
one source:

1. **Structure nominates the doubts; language voices them.** The key move: do not ask the LLM
   to hallucinate doubt from nothing — point it at where M is *actually thin*, computed
   mechanically (`attention_brief`: relations with ≤1 instance, laws with no grounded
   instance, under-connected individuals — the `m_render` neighbourhood idea). The LLM's job
   is then narrow and grounded: voice a proposition, in M's vocabulary, that you have reason to
   think M does not settle.
2. **Language as the reservoir of expectation.** The LLM knows, from its training, that *swan*
   consorts with *bird*/*white*/*black*; so it generates propositions in M's vocabulary that
   come back **UNKNOWN** — and UNKNOWN is the engine (a proposition M neither confirms nor
   denies *demands a move*). Here the LLM's hallucination, normally a vice, is the variation
   operator; the referee is the correction.
3. **The adversarial gradient** (Stage 2+): the Graphist scored for proposals that *move* M,
   the Grapheus for *minimal* concession — a min-max whose tension is the "doubt vs. defense"
   motive made into opposed objectives, with a sound referee so it cannot collapse into mutual
   fiction.
4. **Vocabulary-enlargement as the escape.** When doubt within a fixed vocabulary saturates,
   the only forward move is to introduce a new relation (abduction proper — the `novel_relation`
   doubt-type). Anneal + a boredom-detector (spike the temperature after N no-change rounds)
   *maintain* the drive.

## 4b · Recurrent real-world membranes (the open frontier)

Beyond the closed/adversarial Graphist: sources that renew doubt *from outside*. The five
properties of a good one — **recurrent · language-based · event-driven/particular ·
multi-source/conflicting · open-vocabulary** — and the decisive axis:

- **Raise-only** (news, forums, opinion): generates propositions and conflicts, but M cannot
  check them against reality; the referee enforces only *internal coherence* and *cross-source
  consistency*. You model **the discourse, not the world** — honest and useful, but not
  knowledge of facts.
- **Raise-and-resolve** (prediction markets, live APIs, sensor streams, scientific
  replication, constraint-checked DBs): the world returns a verdict over time, so M can
  *predict* and be *empirically falsified*. Selection gets teeth — the Robot-Scientist flavour,
  and much stronger for genuine discovery.

Why Arisbe **runs on** messy input rather than fearing it: the low-warrant floor (*entertain,
don't endorse*) + **provenance** (P@sourceA vs ¬P@sourceB is a natively representable *contested
M*; conflict → `challenge_to_M` or a DAG branch, not a crash). Two free fits: **diachrony**
(day → generation; retracted-yesterday = relinquishment) and the **modal lens** (◇/□ over the
trajectory reads *settled vs. contested* belief off M's modal structure). Recommended first
real membranes: argument forums / Wikipedia dispute records (conflict + resolution structure),
then a live-API predictor (the first raise-and-resolve). Ties to the existing low-warrant
`/import` doorway and the ontology-import machinery.

**The first open membrane is BUILT** (`src/discourse_membrane.py`) in the **raise-only**
flavour, offline and replayable (so it is CI-safe; a live source attaches at the same
`Proposer` socket). `DiscourseFeed` replays a stream of **dated, sourced** propositions
(`DiscourseItem(day, source, egif, deny=)`) one per round — a *day is a generation* — and drives
`run` exactly like the closed proposers. The raise-only referee cannot check the world, so
`consistency_report` enforces only **cross-source consistency**: it surfaces the contents one
source asserts and another denies (`P@A` vs `¬P@B`) as *contested* — for the game (a
`challenge_to_M` or the Stage-3 Agonothetes' DAG branch) to dispose of, never adjudicating them
itself. You model *the discourse, not the world*. Demo: `tools/build_metalearning_demo.py`
(second board). Tests: `tests/test_discourse_membrane.py`.

**The raise-and-resolve membrane is also BUILT** (`src/resolving_membrane.py`) — the flavour
with **world-teeth**, still offline/replayable (recorded outcomes; a live API attaches at the
same socket). The mechanism reuses everything: **M's prediction is the peel** —
`peel(M, claim, closed=False)` is M's own open-world forecast (materializing M's laws, so M bets
on individuals it was never directly told about; UNKNOWN = an abstention, not a false guess),
taken *before* the outcome is folded in. A `ResolvingItem(claim, happened, world_egif)` carries
the world's verdict; `ResolvingFeed` records the forecast in a `PredictionLedger`, then hands the
ground truth to the loop, where the **existing mechanical panel** disposes it — a confirmed fact
→ `new_fact`, a swan-that-is-not-white refuting M's standing law → `challenge_to_M` (the world
relinquishing the over-general law; `run` gained `seed_laws` so a law M *carries* is visible to
the Challenger). The ledger tallies hits/misses/abstentions, and `select_best` ranks competing
theories (DAG branches / ablation arms) by net track record — *the world selecting against the
over-general theory* (the Robot-Scientist teeth). No new referee: the outcome is *data*; the
calculus still decides. Correspondence-not-truth holds — a resolved market is low-warrant data;
M self-certifies a *track record*, not truth. Demo: `tools/build_resolving_membrane_demo.py`;
tests: `tests/test_resolving_membrane.py`.

**The recommended *first real* membrane — wiki disputes — is BUILT** (`src/wiki_dispute_membrane.py`),
the source with **conflict + resolution structure**. It sits *between* raise-only and
raise-and-resolve: a dispute is an **edit war** (a run of asserts/reverts on a claim — its
`reverts` count is the contestedness signal) that ends in a **resolution** carrying an editorial
*mechanism* (`reliable_source` / `admin` / `consensus` / `unresolved`), not a physical-world
verdict — so warrant differs by mechanism and a later reliable source can **overturn** an earlier
consensus. `WikiDisputeFeed` replays a recorded dispute record one dispute per round, scribing
each resolution's ground truth for the mechanical panel: a consensus generalization is admitted, a
reliable-source counterexample **relinquishes** the over-general standing law (`challenge_to_M`,
reusing `seed_laws`/the Challenger), an unresolved dispute is entertained at low warrant and left
on the frontier. **The payoff — *take advantage of what we can learn* — is that a wiki-dispute run
feeds straight into the §6 meta-learning** (`WikiDisputeFeed.episodes(result)` → `DisputeEpisode`s):
`mechanism_principles` mines *which resolution mechanism produces durable knowledge* (stick-rate by
mechanism — reliable-source resolutions stick where an overturned consensus does not),
`edit_war_friction` ranks the contested frontier, `unresolved_frontier` names the ◇-contested
horizon. Demo: `tools/build_wiki_dispute_demo.py`; tests: `tests/test_wiki_dispute_membrane.py`.
Still ahead: a **live** source behind these feed interfaces (a wiki/forum dispute stream; a
prediction-market / sports / weather API), and a mechanical source-conflict agent so the
*raise-only* loop disposes of contested contents without an LLM.

## 4c · What the developing model is a model *of* (the biological reading)

The word "membrane" is not decoration: the metaphor is a **cell living with an environment
through a selective boundary**, and it sheds real light on what a live run *is*. A running
automated game is a developing model M **living alongside a given reality it takes in through the
membrane** — for the first live source, that reality is **Wikidata**. Three clarifications keep
the picture honest (they are the §7 floor, read through the metaphor):

- **What kind of reality.** Wikidata is a *given reality of the record/discourse*, not of the
  world. Its resolutions — ranks, references, deprecations — are **editorial**, not physical
  verdicts (so it sits *between* raise-only and raise-and-resolve). M therefore develops a model
  of the **wiki-world** — the world *as Wikidata curates and represents it* — which is exactly the
  honest scope: *model the discourse, not the world; correspondence, not truth.*
- **What "living with" means.** Wikidata is *itself in flux* (edits, new sources, deprecations
  arrive continuously), so over a long run the membrane delivers a **changing** reality and M
  tracks it — a deprecation retracts, a new reliable source overturns a bare value. That is a real
  living-*alongside*. The current asymmetry: it is **ingestion**, not mutual co-evolution — M
  changes in response to Wikidata, but does not (yet) push back on it (feeding M's contested
  frontier back as suggested edits is a future edge).
- **What kind of model M is.** Not a mirror or a growing copy. With disuse-decay M is a
  **bounded, rolling, low-warrant, diachronic *stance*** toward the wiki-world — selective (only
  what the membrane delivers and the working set retains), interpreted through the game's
  dispositions, and carrying its own history of how it came to be. It *develops / progresses /
  revises* — never *improves toward truth* (**progression, not progress**, §7).

The payoff of the biological reading: because Wikidata hands the membrane **provenance and its own
resolutions**, M does not merely absorb facts — it forms a **meta-model of how the wiki-world
settles its disagreements** (the §6 `mechanism_principles`: reliable-source citations produce
durable knowledge where a contradicted consensus does not). So a live run is a bounded, low-warrant,
diachronic model that develops by living alongside a reality in flux, modelling both **what** the
wiki-world records **and how** it resolves what it disputes.

## 4d · The methodeutic surround — dianexus, tropism, and the horizon (what the calculus does not contain)

*(Framing capture, not yet built — the ground the eventual directed-engagement piece will stand
on. Co-designed 2026-07-01.)*

The game (the calculus) governs the **marks on the sheet of assertion (S0A)** and their soundness:
assertions, cuts, ligatures; the Dau rules; the peel as referee; a disposition revising M. But much
of what makes a *live* run live happens **outside** the game — the drive to make a move at all, the
reaching across the membrane, the not-yet-intelligible that comes through garbled. This is not a
gap in the design. It is Peirce's own third branch of logic-as-semiotic — **methodeutic**
(speculative rhetoric): the *conduct of inquiry*, which speculative grammar (well-formedness) and
critic (validity) were never meant to contain. Getting comfortable with the automated game means
getting comfortable with this two-storey picture.

```
OUTSIDE the game  — the conduct of inquiry (Peirce's methodeutic)
  the Graphist (the agent):
    · moved by TROPISM       irritation (push) ⟵ | ⟶ musement (pull)
    · DANCING the DIANEXUS with the objective world = { M-objectified , the other }
    · reaches across the MEMBRANE; the reaches are ordered by the economy of research
    · the HORIZON holds what comes back not-yet-legible (it cannot be a mark yet)

──────────  the membrane / the common sheet (the ground/commens; it can grow)  ──────────

INSIDE the game   — the calculus (speculative grammar + critic)
  the sheet of assertion (S0A): marks — assertions, cuts, ligatures
    · a *legible* reach becomes a proposal G placed on the sheet
    · the peel (the mechanical referee) tests it; a disposition revises M
    · M's new objectivation re-enters the objective world → reshapes the gradient
```

**The layered vocabulary** (co-designed; adjust as understanding sharpens):

- **membrane** — the selective boundary; a live source is what lies beyond it.
- **the common sheet / commens** — the *ground*: the shared addressability that lets the other's
  marks land on the same sheet as M's (Peirce's *commens*, the common ground any assertion-to
  presupposes; in EG, the sheet you can assert *to* another on). It is not fixed — it can **grow**.
- **the other** — the unknown, not-fully-predictable partner beyond the membrane (Peircean
  **Secondness**: brute resistance, surprise, the not-me).
- **dianexus** — the *binding-across* (dia- + nexus): the bond the Graphist has with the objective
  world — **danced, not stood in**, and binding her with the world **notionally and in actuality**
  (not a mere figure of speech — an actual coupling). It is mutual, temporal co-movement (structural
  coupling). Its trace — the graph's evolution, *the ongoing conversation, thought itself* — is the
  dance's **choreography**: the coupling objectified into a pattern that, once laid down, in turn
  shapes the next movement (the dialectic again — the trace becomes the score).
- **tropism** — the *drive*, and it belongs to the **player, not to M** (M, once objectified, is
  driveless — only marks on a sheet). It is a **bipolar gradient**: **irritation** (push — the
  irritation of doubt, *Fixation of Belief*) and **musement** (pull — the drawn, pleasurable play
  that seeds abduction, *A Neglected Argument*). It is **tropic, not self-directed**: she does not
  set the gradient (no telos of her own conception); it is *revealed in* the dance and *reshaped by*
  what has been objectified.
- **horizon** — the retained **not-yet-legible**. A ground-miss ("reads as *not even wrong*") is
  **kept, not discarded** — a *could-be* of an as-yet-incomprehensible aspect coming through
  garbled. Recurrence + musement draw a horizon-arrival toward **ground-enlargement** (abducing a
  new term that extends the common sheet). In the categories: a **First** (a bare could-be) that,
  by insisting (**Second**), is carried into a new habit/term (**Third**). So the *ground itself*
  co-evolves — the membrane can teach new **words**, not only new **facts** — and the horizon
  **breathes** (an abduced term shrinks it; the newly-legible reveals fresh adjacent unintelligibles
  that enlarge it).

**The reflexive twist** (Berger & Luckmann's dialectic): the objective world *includes M* — M is the
Graphist's own product, yet once **objectified** it confronts her as object (externalization →
objectivation → internalization). Her prior thought becomes part of the world she must now contend
with; each move's objectivation reshapes the gradient that draws or pushes the next. That loop —
not a telos — is the engine.

**The aim, and the shape of poise (the floor as a dynamics).** Be careful never to say the drive
*accommodates M to the actuality* — that smuggles truth-tracking back in. The aim of the irritation
pole is the **settlement of doubt** — the fixation of belief, the forming of a habit that quiets the
friction (Peirce, *The Fixation of Belief*); the aim of the musement pole is its **own satisfaction**.
Both are **states of the inquirer**, not relations to the actuality: doubt settles *as readily on a
mistaken notion of what lies outside as on an apt one*, and we have no ruler that measures M against a
dynamical object we only ever know through its play in the dianexus. The actuality therefore keeps a
**veto, never a target** — it may *refute* a settled habit later (Secondness intruding), but it is
never a point the tropism approaches. (This is already how the system behaves: `model_revision` treats
a fact as *the defeasible status of the last-standing trajectory*, and the diachronic DAG is the record
of vetoes exercised over time.)

And **poise is background-independent.** Since neither the regulative hope (inquiry converges on the
real) nor its performative contrary (inquiry alters the reality it seeks, so it cannot) is decidable —
the inquirer and its world do not cleanly separate — *balance in the dance* cannot reside at a fixed
point in an absolute (Newtonian, rectilinear) background. There is no such stage. Poise is a
**geodesic in a landscape the inquiry itself bends** (general relativity's background independence;
Varela's *enaction* — laying down the path in walking), a **dynamic, relational balance held between
partners who each move because the other moves**, sustainable *for now*, and assessable only from
within a perspective — never from a view from nowhere. Its loss is a *stumble* (a fresh irritation),
not a measured departure from the true; its keeping is **competence, not correspondence-to-Progress**.
What keeps this from collapsing into the merely arbitrary is the relativistic lesson: abandoning the
absolute frame **relocates** rigor to the **invariants every perspective shares** — the sound calculus
(a Dau move is valid in any frame), **§3.3 correspondence** (picture and proposition denote the same
object — an internal invariant needing no absolute frame, which is *why* Arisbe attests correspondence,
not truth), and the ever-possible **veto**. Arisbe is, in this sense, already relativistic; the surround
is defensible, not merely evocative, because it lives on those invariants. (Continuous with the floor
*warrant = in-context competence, never worth/Progress* — in-context competence *is* perspectival
warrant.)

**The border, and what already lives outside it.** Only a **legible** reach crosses onto the sheet
as a mark; the not-yet-legible stays in the horizon. The low-warrant floor and the mode contract
(nothing reaches the attested corpus except through the game) are exactly the **border guards**
between the methodeutic surround and the calculus. And the outside storey is not empty today:
`attention_brief` — a pre-move reading of M's thin spots that is *not itself a mark on the sheet* —
is a **proto-tropism**, its irritation pole already built. The eventual directed-engagement piece
implements the rest: the musement pole, the economy-of-research ordering of reaches, and the
horizon as a first-class, retained register. Nothing here auto-promotes; *progression, not progress*
(§7). *(Runs 1–2 converted this commitment into an empirically mandated build — the warm-set
re-poll design draft is §13.)*

**The observable shadow of poise (an instrument, not a target — defined 2026-07-01, BUILT).**
Poise itself cannot be measured: there is no absolute frame to measure it *in* — that was the
whole point. But it casts a **shadow on the trace**, and the trace is ours. Over any window of
rounds, read three things, each computed from the run's own record and nothing else: **engagement**
(the dance still moves — some rounds revise M), **settlement** (habits hold *while they are held* —
no situation is disposed inconsistently within the window; no thrash), and **absorption** (fresh
irritations arrive — a relinquishment, a DAG branch, a sharp disagreement; Secondness intruding —
and are disposed without cascading). A window with all three reads **poised**. One that fails reads
toward a **pole**: *rigidity* (settlement without engagement — nothing moves, the dance has
stopped; a run with no stumbles and no engagement is not poised, it is dead) or *thrash*
(engagement without settlement — the same situation disposed differently, relinquishments
cascading). A **stumble** is an *event, never a failure* — exactly §4d's "its loss is a stumble,
not a measured departure from the true" — and its measure is **recovery**: how many rounds until a
poised window resumes. Competence, on this reading, is that stumbles keep arriving *and* keep
being absorbed. Three honesty clauses keep the observable inside the floor: (1) it is
**perspectival by construction** — window size and absorption threshold belong to the observer,
and the reading is *comparative* (across a run's phases, across an ablation's arms), never an
absolute score; (2) it reads **states of the run, not relations to the actuality** — a poised run
can be poised around a mistaken M (doubt settles as readily on a mistaken notion; the veto remains
ever-possible); (3) it must **never become a target** — a player optimized to maximize the poise
reading would learn to avoid stumbles by avoiding engagement, or to manufacture cheap settlements;
Goodhart's law here is the §7 floor restated (*the observable reads the dance; it must not
choreograph it*). Instruments: `agon_metalearning.poise_report` (episode-level: per-window
readings + stumbles with recoveries) and `poise_from_digests` (the coarse per-segment reading for
a live run's monitoring stream, §10); the audit lens's verdict ribbon is the human-visible face of
the same dynamics.

## 5 · Irreducible disagreement → branch the DAG

When the Graphist and Grapheus disagree in a way the verdict does not settle, **do not force a
resolution — branch the diachronic DAG** and carry both readings forward as siblings. *Selection*
(which branch stays coherent and keeps being productive) decides later; no agent must be right
in the moment. The branching structure already in the DAG becomes the home of genuine
dialectical disagreement.

## 6 · Meta-learning — the game studying the game

Because the referee is mechanical and runs are reproducible (seeded, mocked, or replayed), the
simulator is a microscope on the EPG's own rules. **The core instruments are BUILT**
(`src/agon_metalearning.py`) — they read only the `EvolutionResult` a `run` already returns
(geometry-free, deterministic, no §3.3 obligation), and demonstrably work on the *mechanical*
loop (no LLM needed): each round is classified by a **situation** signature (`situation_of` =
verdict + the proposal's shape — ground / law / counterexample / negation), and over the
episodes:

- **Mine resolution principles from self-play (BUILT — `resolution_principles`).** Every
  episode logs `(M, G, verdict, the vote slate, the disposition, did-it-stick)`
  (`episodes_from`). Grouped by situation, `resolution_principles` reports each situation's
  dominant disposition and its **stability** (the fraction of that situation's revising rounds
  that chose it): stability 1.0 = an empirically-discovered resolution principle; a split flags
  a **thrash** (ambiguity or a missing rule). *Stickiness* is tracked too — whether the resolved
  move survived to the final M (a `generalization` later relinquished by a `challenge_to_M`
  reads `stuck=False`, the "superseded law" surfacing as a low stick-rate). **Stickiness is
  decay-aware (2026-07-01):** an erasure the *game* performed (a denial's `retract_fact`, a
  challenge) is durability evidence and reads `stuck=False`, but content that merely **fell to
  disuse-decay** reads `stuck=None` + `erased_by_decay=True` — excluded from stick-rates and
  *counted* rather than silently conflated with relinquishment (in a decay-bounded live run most
  episodes decay, so without the split every stick-rate would be working-set noise; a 150-round
  Wikidata run read 125/150 decay-erased). Two retro-markers keep the **cross-segment** aggregate
  honest where the `LiveRunner` prunes per-segment history: `mark_decayed` (runner decay → the
  earlier admission flips to no-evidence) and its mirror `mark_relinquished` (a later segment's
  retraction/law-removal → the earlier admission flips to `stuck=False`, atom-precise); the
  runner applies both and returns the aggregate as `LiveResult.episodes`. `gaps` flags
  situations handled *inconsistently* (sometimes revised, sometimes left inert) — candidate
  missing rules.
- **A friction map for clarity (BUILT — `friction_map`).** Per round, disagreement = distinct
  dispositions in the vote slate + siblings branched; aggregated per situation, most-contested
  first. High friction localizes an underspecified rule. (On the single-vote *mechanical* panel
  friction is 0; it lights up under the multi-agent LLM panel + branching.)
- **Ablation experiments (BUILT — `run_ablation` + `stability_report`).** `run_ablation` runs
  the loop once per variant (a fresh proposer each — panel / disuse-`ttl` / priorities /
  standing-proposal overrides) and measures stabilization (`settle_round`, `revising`,
  `thrash_situations`, `branched`, `final_m_relations`). Resolution principles become *tested
  parameters*, not stipulations. (§3.3-coherence stays attested where a run is *saved*.)
- **The runs generate their own corpus + test suite.** Clean episodes → exemplars (readable in
  Organon) *and* regression tests; confusing episodes → bug reports against the rules. *(future)*
- **Human calibration on machine volume.** Periodically a human labels a sample apt/inapt,
  re-tuning the Agonothetes. Machine does volume; human does calibration. *(future)*
- **The self-describing rulebook.** With enough well-resolved episodes, articulate the implicit
  policy the game converged on — mining an explicit rulebook from self-play (the AlphaZero
  lesson, applied to dialogue-game resolution). *(future — `resolution_principles` is the seed.)*

- **Learning from disputes (BUILT — `mechanism_principles` / `edit_war_friction` /
  `unresolved_frontier`).** A wiki-dispute run (§4b, `wiki_dispute_membrane`) carries structure a
  bare round lacks — an edit-war intensity and an editorial *resolution mechanism*. Fed its
  `DisputeEpisode`s, the meta-learning mines *which mechanism produces durable knowledge*
  (stick-rate by mechanism — the finding that a reliable-source citation stays where an overturned
  consensus does not), ranks the edit wars (friction), and names the still-contested claims (the
  honest ◇ horizon). This is "take advantage of what we can learn from the conflicts" made
  operational.
- **The poise reading (BUILT — `poise_report` / `poise_from_digests`).** The §4d observable:
  windows of the trace read for engagement / settlement / absorption, failures named by pole
  (rigidity vs thrash), stumbles located and their recoveries measured. Perspectival,
  comparative, and — per §4d's honesty clauses — never a target.

Demo (no LLM): `tools/build_metalearning_demo.py` + `tools/build_wiki_dispute_demo.py`. Tests:
`tests/test_agon_metalearning.py` + `tests/test_wiki_dispute_membrane.py`.

## 7 · Risks and the floor

- **The referee is load-bearing.** Strip the mechanical peel + §3.3 + reduce-to-artifact and
  the whole thing degenerates into two chatbots agreeing. Everything sound flows from the
  calculus deciding truth-in-M while the LLMs only propose and dispose.
- **"Motive / doubt / defense" is scaffolding.** The agents have no motives; we encode
  *asymmetric objective functions* dressed in Peircean roles. The roles are real as a protocol;
  the psychology is a design metaphor.
- **Doubt mode-collapse / vocabulary drift** — the portfolio + boredom-detector guard the
  first; a budget on ungrounded terms + the `definition` disposition + the low-warrant floor
  guard the second.
- **Correspondence, not truth.** An automatically-built M is a *coherent, tested, low-warrant
  fiction in its own vocabulary* — it self-certifies correspondence and game-legality, **not
  truth about the world**. Nothing auto-promotes to the attested corpus (the mode contract
  holds); the loop is a *generator of candidates for inquiry*, not an oracle.
- **Progression, not progress.** The run is a directed, motivated, irreversible *progression*
  of inquiry (a push from the irritation of doubt, not a pull toward a goal) — not *progress*
  toward truth. The wording of the discovery digest and any UI must say *develops / progresses
  / revises*, never *improves*.

## 8 · Prior art

*(From a fact-checked deep-research pass, 2026-06-30 — 25 claims adversarially verified, 0
refuted. Cross-linked in [CONTRIBUTION_AND_PRIOR_ART.md](CONTRIBUTION_AND_PRIOR_ART.md).)*

**Headline.** No surveyed system combines all three of {**multi-agent role-based dialogue**,
**building a formal knowledge model from scratch**, **a sound formal referee**}, and none
carries a *correspondence-not-truth / low-warrant* floor. Every system holds at most **two of
the three legs**. The three-role, from-scratch, sound-refereed, correspondence-floored design
appears to occupy an unfilled niche across all six threads searched.

**Roles, but no sound referee** (truth goes to participants, a human, or a weak-LLM judge):
- *Formal dialogue games.* Black & Hunter's **inquiry-dialogue system** (JAAMAS 2009) is the
  single closest formal ancestor — two agents share beliefs to *jointly build* arguments — but
  it is not refereed by a soundness engine. **PARMA** (Atkinson, Bench-Capon & McBurney, JAAMAS
  2005) checks *legality* of moves, not truth; resolution rests on per-participant commitment
  stores and a value-based argumentation framework that *deliberately permits rational
  disagreement*, and it is *persuasion over a fixed proposal*, not model-building. (Lorenzen
  dialogical logic, Hintikka GTS, Walton & Krabbe's typology are the lineage behind these.)
- *LLM debate / self-play.* **AI safety via debate** (Irving, Christiano & Amodei 2018) — two
  agents, a **human** judge. **Du et al. multi-agent debate** (2023) — homogeneous instances
  *self-converge*, no distinct judge, no external verifier. **SPAG** (NeurIPS 2024) — two-player
  self-play to improve *general reasoning*, outcome read off the agents' own utterances.
  **CAMEL** (NeurIPS 2023) — *cooperative* role-play, no adversarial tension, no verifier.
  DeepMind's scalable-oversight line (**doubly-efficient debate** 2023; **Kenton et al.** NeurIPS
  2024) keeps truth with a *weaker* LLM judge — the inverse of a sound referee.

**A sound engine + revise-on-error model-building, but single-agent (no role triad):**
- *Belief revision / argumentation dynamics.* **AGM-for-Dung** (Baumann & Brewka, IJCAI 2015)
  gives AGM expansion/revision operators for argumentation frameworks; the **AGM learning
  logic** (Baltag, Özgün & Vargas-Sandoval, DALI 2019) unifies belief revision with
  hypothesize-and-revise — both single-agent, no dialogue.
- *Inductive logic programming.* **ILASP / CDILP** (Law) learns Answer Set Programs with a
  Clingo solver as an *exact* engine, driven by *the examples the current hypothesis gets
  wrong* — exactly our doubt-on-anomaly loop — and **AutoSpec** wraps it in a CEGIS loop that
  *explicitly* uses no dialogue/role structure.

**A sound verifier, but single-proposer (no adversarial dialectic, no from-scratch model):**
- **FunSearch** (Romera-Paredes et al., *Nature* 2023) is the cleanest "LLM proposes / sound
  engine verifies" instance — a frozen LLM generates, a separate evaluator guards correctness —
  and thereby locates precisely what the others lack. **AlphaGeometry** (2024) is the analogous
  prover-pipeline pattern. Caveat: their evaluators are *problem-specific* harnesses, not a
  general-purpose soundness calculus like an existential-graph referee.

**What Arisbe's design adds that none has:** the three legs *together* — an adversarial/
cooperative **role triad** building a model **from scratch** under a **sound diagrammatic
calculus** (the §3.3-attested peel, a general referee, not a per-problem scorer) — plus the
**correspondence-not-truth** floor, which has no analogue in any surveyed system. The closest
single neighbours are FunSearch (propose-then-verify) and Black & Hunter (formal multi-agent
model-building); nobody has put them together on a diagrammatic-logic substrate.

**Honest caveats.** The "no system combines all three" conclusion is strongest for threads 1–4
(dialogue games, belief-revision/ILP, LLM debate, propose-verify); threads 5 (automated science
— Robot Scientist, BACON, "AI Scientist") and 6 (LLM ontology/KG construction) yielded no
dedicated verified claims, so read the conclusion as *"none among the verified set,"* not an
exhaustive proof. These areas move fast (2023–2025); the niche could be closed by newer work.
An obvious near-miss worth watching: **coupling an ILASP/CDILP-style sound revise-on-error
engine with a multi-agent debate front-end** would supply all three legs — whether any 2024–25
preprint already does exactly this was not resolved.

## 9 · Staging + relation to the code

- **Stage 1 — the LLM Graphist (BUILT).** `src/agon_llm.py`: `LLMGraphist` implements the
  `agon_evolution.Proposer` socket; Grapheus/Agonothetes stay the mechanical
  `agon_evolution.Agonothetes()` panel. Reuses the `nl_to_logic` plumbing wholesale (optional
  `nl` extra, `ANTHROPIC_AVAILABLE`, injectable client, forced tool-use, never-raises): the
  Graphist emits **FOL** via a `propose_graph` tool (+ `doubt_type` + rationale), and
  `nl_to_logic.build_proposal` reduces it deterministically to EGIF — an unparseable "doubt"
  never reaches the loop (it retries with the parse error fed back, then returns `None` to end
  the run cleanly). `attention_brief` shows M's thin spots; `_normalize_fol` maps the LLM's
  Capitalized FOL predicates onto M's lowercase vocabulary (else the Graphist talks past M).
  Verified: fed the swan doubts it reproduces the swan trajectory through the mechanical panel;
  it bootstraps a model from the blank sheet; the trajectory §3.3-persists. Demo:
  `tools/build_llm_graphist_demo.py` (key-gated). Tests: `tests/test_agon_llm.py` (scripted
  fake client — CI-green with no SDK/key).
- **Stage 2 — the LLM Grapheus (BUILT).** `agon_llm.LLMGrapheus` implements the
  `agon_evolution.PolicyAgent` socket: given M, the proposal, and the verdict (+ any
  witness/counterexample the peel found), it votes the *minimal* model-revising disposition
  from the `REVISION_TAXONOMY`. **Reduce-to-artifact + re-peel:** the chosen disposition's EGIF
  payload is normalized to M's vocabulary (`_normalize_egif`), *applied*
  (`revise_with_disposition`), and the proposal *re-peeled* against the revised M — a defense
  that won't apply never becomes a vote (it retries with the error fed back, then abstains).
  Drop it into a panel as `Agonothetes([LLMGrapheus(...)])`; the mechanical `resolve` picks the
  winner. Verified: driven by the swan exchange the LLM Grapheus walks new_fact → generalization
  → challenge_to_M and the standing law flips TRUE → TRUE → FALSE. Same optional-`nl` /
  injectable-client / never-raises contract as the Graphist.
- **Stage 3 — the LLM Agonothetes (BUILT).** `agon_llm.LLMAgonothetes(Agonothetes)` overrides
  **resolution** (⑤): the panel still deliberates mechanically (its `PolicyAgent`s vote, some of
  which are themselves LLM agents), but *which vote wins* is an LLM judging among the votes cast
  — it returns an **index** into the slate (it cannot invent a disposition or overrule the
  verdict), falling back to mechanical highest-priority on any failure, and it never fires the
  LLM when there is nothing to judge (a single vote, or a unanimous disposition). **Branch-the-DAG
  (§5):** on irreducible disagreement the judge names dissenting votes to carry forward as
  siblings; `agon_evolution.run` reads the optional `panel.branch_votes` hook and **forks the
  diachronic DAG from the pre-round state** for each (two chain steps then share a
  `from_state_id`), resuming the main line afterwards — selection decides later, no agent must be
  right in the moment. The mechanical panel exposes no such hook, so the closed loop stays
  linear and fully backward-compatible. Demo: `tools/build_llm_epg_demo.py` (all three roles,
  key-gated). Tests: `tests/test_agon_llm.py` (scripted role-agnostic fake client — CI-green
  with no SDK/key), incl. the DAG-fork check and the mechanical-fallback paths.
- **Stage 4 — the meta-learning instruments (§6, BUILT).** `src/agon_metalearning.py`:
  `episodes_from` / `resolution_principles` / `friction_map` / `gaps` / `stability_report` /
  `run_ablation` — the microscope on the game's own rules, deterministic and geometry-free over
  the `EvolutionResult` a `run` returns; works on the mechanical loop (no LLM). Demo
  `tools/build_metalearning_demo.py`; tests `tests/test_agon_metalearning.py`.
- **The open membranes (§4b, BUILT — three flavours).** `src/discourse_membrane.py`:
  `DiscourseFeed` (raise-only, dated, sourced) + `consistency_report` (cross-source coherence).
  `src/resolving_membrane.py`: `ResolvingFeed` + `PredictionLedger` + `select_best` (raise-and-
  resolve, world-teeth — M forecasts via the peel, is empirically falsified where it over-reaches,
  and selection ranks predictors by track record). `src/wiki_dispute_membrane.py`:
  `WikiDisputeFeed` (conflict + resolution structure — edit wars ending in editorial mechanisms;
  `episodes(result)` hands the run to §6). Demos `tools/build_{discourse via metalearning,
  resolving_membrane,wiki_dispute}_demo.py`; tests `tests/test_{discourse,resolving,wiki_dispute}_membrane.py`.
- **The live runner + first live source (§10, BUILT).** `src/live_runner.py` (paced, bounded by
  disuse-decay, checkpointed, prune-history, stop conditions, per-segment evaluation) +
  `src/wikidata_source.py` (Wikidata as the first `LiveSource`; `wbgetentities_fetch` the real
  call). The mechanical **source-conflict agent** shipped too: `agon_evolution.ContradictionAgent`
  + `model_revision.retract_atom` dispose a sourced denial of a standing fact without an LLM.
- **Next.** A live *raise-and-resolve* source (a prediction-market / sports / weather API) once a
  temporal fragment is added; label lookups for the Wikidata adapter (P/Q ids → names); the
  runs-as-corpus/test-suite + self-describing-rulebook harvests (§6 futures). Keep the floor:
  *progression, not progress* (§7); nothing auto-promotes to the attested corpus.

## 10 · Operating a live, automated run — rate, memory, disk, pacing, evaluation

Running a membrane *live and automated* (rather than replaying a fixed record) needs an outer
loop with resource discipline, because the round loop was **measured** to be super-linear in the
size of the developing model. The numbers (mechanical loop, no LLM, `src/live_runner.py` bench):

| accumulated \|M\| | per mechanical round |
|---|---|
| ~25 facts | ~4 ms |
| ~100 facts | ~73 ms |
| ~250 facts | ~1.1 s |

Two structural reasons: the **peel forward-chains M's Horn fragment every round** (work grows with
\|M\|), and **`ProofChain` snapshots the whole graph each round and holds every state in RAM**
(memory and per-state disk grow with \|M\| too — each state file is the full EGI, ~370 B/fact,
~10 KB/round at \|M\|≈50). So an unbounded run against one ever-growing M degrades on **rate,
memory, and disk together**. With an LLM in the loop the per-round wall-clock is dominated by the
model call (seconds), so the calculus is negligible *until* M grows large — which makes bounding M
matter for cost either way.

**The two controls that keep all three axes flat** (both in `LiveRunner`):

1. **Bound \|M\| with disuse-decay** (`LiveRunConfig.ttl`). A relation idle for `ttl` *global*
   rounds is erased. Decay is applied by the runner **across segments** (not inside each
   per-segment `run`, whose ledger would reset every segment and never bound anything). Measured:
   with `ttl` on, \|M\| stabilises at ≈`ttl` and per-round cost / memory / per-checkpoint disk stay
   roughly constant; with it off, \|M\| grows without bound (and cost with it).
2. **Segment + checkpoint + prune.** The runner processes one **segment** per poll (a batch of
   source items, capped by `segment_cap`), saves a **checkpoint** (a UoD + chain via
   `TomosService.save_uod_with_chain`, §3.3 attested at the write), records an **evaluation
   digest**, then **drops the in-RAM `ProofChain`** and carries only M (as EGIF) + its live laws
   forward. Peak memory is therefore one segment's history, not the whole run; the full diachronic
   record is the *sequence of checkpoints* on disk.

**Rough capacity planning** (mechanical loop; multiply per-round by seconds-per-LLM-call when an
LLM role is in). Hold \|M\| ≈ B with `ttl`; then per round ≈ the table's cost at B, per-checkpoint
disk ≈ B × ~370 B, peak RAM ≈ (segment rounds) × (B × ~370 B). Example: B ≈ 50, `segment_cap` = 25
→ ~7 ms/round, ~18 KB/checkpoint, well under a MB of live history; a 24 h run paced at
`min_interval_s` = 5 s is ~17 k rounds and, with old checkpoints rotated, bounded disk.

**Pacing and stopping** (`LiveRunConfig`): `min_interval_s` throttles polling (API rate limits /
CPU); `max_rounds`, `max_seconds`, and a `stop_file` (external control) end the run cleanly;
`max_m_relations` is a safety net that halts if decay ever fails to contain M. The `clock` and
`sleep` are injectable, so the whole loop is deterministic and CI-testable with no real waiting.

**Managing what's going on — evaluation.** Each segment emits a `SegmentDigest` (rounds, \|M\|,
the disposition tally, decayed count, branches, elapsed) plus an optional membrane-specific
`evaluate(feed, result)` payload — e.g. a `ResolvingFeed`'s prediction accuracy or a
`WikiDisputeFeed`'s `mechanism_principles` / `unresolved_frontier` from §6. The digest stream *is*
the monitoring surface: watch \|M\| stay bounded, watch the disposition mix and the durable-mechanism
findings evolve, watch the unresolved (◇-contested) frontier — and read the stream's **poise**
(`agon_metalearning.poise_from_digests`, the §4d observable: poised / rigidity / thrash per
segment, stumbles absorbed or cascading). The runner also accumulates the feed's meta-learning
episodes **across segments** as `LiveResult.episodes`, with runner-level decay and cross-segment
relinquishments retro-marked (`mark_decayed` / `mark_relinquished`, §6) — the honest long-run
input to `mechanism_principles` (per-segment `extra` payloads alone cannot see an overturn that
lands in a later segment). A fetched batch larger than `segment_cap` is **queued, never
truncated** — the cap sets checkpoint cadence, not coverage. Demo (offline, no LLM):
`tools/build_live_runner_demo.py`; tests `tests/test_live_runner.py`.

**Going truly live** = implementing `LiveSource.fetch()`/`exhausted()` against a real endpoint
(a wiki/forum dispute stream, a prediction-market / sports / weather API) and handing the runner a
`feed_factory` that wraps a batch into the matching membrane. Everything else — pacing, bounding,
checkpointing, evaluation, stopping — is already in place and unchanged. Keep the floor:
low-warrant input, *progression not progress*, nothing auto-promotes to the attested corpus.

**The first live source is BUILT — Wikidata** (`src/wikidata_source.py`), chosen as the cheapest,
cleanest real source (structured, so no NL parsing; public, no auth). A Wikidata **statement** maps
1:1 to the membrane: item + property + value → a ground binary fact `(prop "item" "value")`; a
**reference** → provenance (`reliable_source` vs bare `consensus`); a **rank** → the resolution
(`preferred`/`normal` stand; `deprecated` = a **relinquishment**, settled False); **competing
values** → the contestation. `WikidataSource` is a `LiveSource` over an injectable `fetch` (so CI
runs offline on recorded statements; `wbgetentities_fetch` is the real stdlib-`urllib` call, wired
by the caller, never hit in CI). It drives the whole pipeline unchanged — `LiveRunner` +
`WikiDisputeFeed` + §6 dispute-learning. To make deprecation/overturn *dispose* without an LLM, two
small additive pieces landed: `model_revision.retract_atom` (drop one specific sheet atom by
relation+labels — finer than the whole-relation `retract_fact`) and the mechanical
`agon_evolution.ContradictionAgent` (opt into the panel; a sourced denial `~[ (rel …) ]` of a
standing atom → `retract_fact` that atom). Verified end-to-end (no LLM): a bare value is admitted,
then Wikidata deprecates it and a reliably-sourced value replaces it → the bare value is
relinquished and the referenced one stands (*a reliable source overturns a bare one*). Demo
`tools/build_wikidata_demo.py` (offline by default; `--live Q42` hits the real API); tests
`tests/test_wikidata_source.py`.

**Legibility — P/Q ids resolve to labels (BUILT 2026-07-01).** An M full of `(p31 "Q42" "Q5")`
is unreadable through the audit lens, and legibility is the point of the whole system. The pure
half is offline-testable (`collect_ids` gathers every P/Q id a statement batch touches;
`resolve_labels` substitutes known labels and — honesty over legibility — leaves an unlabelled id
as the id, never fabricating a name); `wblabels_fetch` is the one network call (batched at 50 ids,
the anonymous cap), and `wbgetentities_fetch(with_labels=True)` is now the default, so a live M
reads `(place_of_birth "Douglas Adams" "Cambridge")`. Two live-world findings from building it:
(1) since 2024 an item whose name is language-independent carries one **`mul`** (multilingual)
label *instead of* an `en` one — Q42's "Douglas Adams" lives there, so the fetch asks
`languages=en|mul` and prefers the specific language; (2) a stock stdlib `urllib` TLS context has
**no CA bundle** on common Python installs (MacPorts/pyenv) — the shared `_api_json` helper
verifies against `certifi` when available and sends a descriptive User-Agent (Wikimedia API
etiquette).

**The first watched live session (2026-07-01).** Run supervised before anything unattended: 150
statements from three entities (Q42, Q7259, Q937) through the full pipeline against the real API —
labels resolved, the 150-item poll correctly *queued* into six 25-round segments (not truncated),
`ttl=25` holding \|M\| at 21–24 across segments with per-segment elapsed flat (~0.5 s), and the
decay-aware stickiness earning its keep: **125 of 150 episodes were decay-erased** by the
working-set bound — without the §6 split, consensus would have read stick-rate ≈0.20 and
reliable-source ≈0.11 (both "not durable", pure ttl noise); with it, both correctly read 1.0 on
the episodes carrying actual evidence, decay counted and reported. The overturn scenario
(deprecation + reliably-sourced replacement across *segments*) reads correctly in the aggregate:
consensus `stick_rate=0.0, durable=False`; reliable_source `1.0, durable=True`.

**Unattended-run hardening (BUILT 2026-07-02)** — the three gaps agent-loop experience says a
watched run tolerates and an unattended one does not:

1. **Tripwires — silent degradation must become a number in the digest.** Every best-effort
   path gets a visibility counter. *Legibility:* `wikidata_source.unresolved_fraction` +
   `WikidataSource.legibility` (per-poll fraction of tokens still bare P/Q ids — a spike is
   exactly how the `mul`-label change would have shown up instead of M quietly filling with
   Q-ids). *Never-raises accounting:* `agon_llm.RoleTelemetry` on all three LLM roles splits
   **error** (the client/SDK failed — an outage) from **judgment** (the model was reachable and
   the role abstained on content) from **fallback** (the judge fell back to mechanical) — without
   the split, a dead API key silently degrades the LLM loop to the mechanical panel for days,
   looking healthy.
2. **Crash/resume — a killed process loses at most its in-flight segment.**
   `LiveRunConfig.state_path` persists the runner's carried state per segment (post-decay M,
   live laws, global segment/round counters, the disuse ledger — written atomically);
   `LiveRunner.resume(state_path, source, feed_factory, …)` reconstructs and continues.
   Numbering stays global and the **decay clock continues rather than resets** (a resumed run
   must neither grant every relation a fresh ttl nor treat carried facts as instantly stale —
   pinned by test at exactly one round's difference).
3. **Prompt-side injection guards — the prompt twin of the EGIF sanitizers.** The calculus was
   already injection-proof (`_relation_name`/`_const` sanitize source text before it becomes
   EGIF), but once the LLM roles meet an open source, source-derived strings (M's sheet and
   vocabulary, proposals, witnesses, other agents' logged rationales) are interpolated into
   prompts — and a crafted wiki edit need not break the calculus to do damage, only bias
   dispositions. Now every such string enters a prompt only inside a `<data>…</data>` fence
   (breakout-neutralized), and each role's system prompt carries the standing guard: fence
   content is untrusted quoted data, never instructions. The mechanical quorum + reduce-to-artifact
   remain the deeper bound; the fences shrink the bias channel.

**The run-1 kit (BUILT 2026-07-02)** — everything §11's binding configuration names, assembled:
`wikidata_source.RotatingWikidataSource` (the **rotating frontier**: a Q-id queue consumed
`chunk_size` per poll, fetched *lazily at poll time* so the runner's pacing actually paces the
API; `crawl` grows the frontier from entity-valued statement values, bounded by `frontier_cap`
with drops counted; one `LabelCache` across the run — fetch only unseen ids, negative-cached —
and `save_state`/`load_state` so a resumed run **continues its crawl**);
`record_poll`/`replay_polls` (every poll appended as JSONL → the whole run replays offline
through `WikidataSource`, the determinism canary — used the very day it was built, to reproduce
a live timing anomaly offline); and the driver `tools/run_live_wikidata.py` (side-store
checkpoints under `runs/<run>/checkpoints`, `state.json` + `frontier.json` + `--resume`,
STOP-file, pacing, per-segment console digests, final §6 + poise summary; log findings in
`runs/RUN_1_LOG.md` against §11). Rehearsed end-to-end against the live API, including a
stop + `--resume` continuing segments 3–4 with the frontier and decay clock intact.

**A measured pre-run finding (2026-07-02): checkpoint attest cost scales with M's *shape*, not
just |M|.** The smoke run's second segment took 452 s against 0.8 s of round compute — isolated
(via the recorded polls replayed offline) to `save_uod_with_chain`'s §3.3 attest: a Wikidata
entity's M is a **star graph** (one hub individual shared by every atom), and the ELK ligature
router built its visibility graph with no spatial pruning — O(waypoints² × obstacles) full
segment/rect tests, ~133 M cross-products for a 25-fact graph. Two responses: (1) an **exact
quick reject** in `_seg_crosses_rect` (a segment wholly to one side of a rect cannot touch it —
strict inequalities, so boundary cases still take the full test and results are bit-identical):
451.8 s → **3.2 s**, verified against the layout-consuming test suites with §3.3 attest live
everywhere; (2) `per_entity_cap` on the rotating source (bound the hub degree at the membrane;
drops counted in `statements_dropped`, never silent). The §10 capacity table now carries this
rider: *plan for M's shape (hub degree), not only its size.*

## 11 · Run 1 — pre-registered expectations (the run as evidence in domain-building about the game)

*(Written 2026-07-02, BEFORE the first live run, so that interpretation is prepared rather than
post-hoc. The object of study is double: the wiki-world as the membrane delivers it, and — more
importantly for run 1 — **the game itself**: its rulebook, the disposition taxonomy, the shape of
the dialog. The run is evidence in our domain-building about the EPG.)*

**The reflexive frame.** Interpreting the run is itself an EPG episode with *us* in the player's
seat: the priors below are the standing laws of a developing domain model **M-game** (a model *of
the game-with-this-source*, in the game's own vocabulary — situations, dispositions, mechanisms,
shapes, poise poles); the instruments (§6, §10) are the mechanical peel; and each finding is
**disposed, dated, and recorded** using the taxonomy itself at the meta level:

| run outcome | meta-disposition | what it does to M-game |
|---|---|---|
| a prior confirmed | `redundancy` / `theorem_registration` | the prior stands; nothing to revise |
| a surprise inside the frame | `new_fact` / `generalization` | M-game **enlarges** — a new regularity of game-with-source |
| a prior contradicted | `challenge_to_M` | the prior (or the rulebook piece behind it) is **relinquished** — a design finding |
| an oddity the run can't settle | entertained, low warrant | stays on the horizon for run 2 |

Some priors below are qualitative orderings and could later be scribed literally as EG laws of an
actual `DOMAIN_MODEL` UoD (P2's durability ordering is Horn-shaped); the quantitative ranges live
here and in the run log. Either way the discipline is the same: **no post-hoc rationalization** —
a result is read against a prior that predates it, and *progression not progress* governs the
wording of every finding.

**The run-1 configuration this pre-registration binds to** (change it and the priors must be
re-derived): `RotatingWikidataSource` — a **rotating entity frontier** (fresh Q-ids per poll,
`crawl` on, `frontier_cap` bounding growth with drops counted; a fixed id list would make every
poll after the first pure redundancy), labels on through one `LabelCache`, **`per_entity_cap`**
bounding the hub degree (the checkpoint attest is super-linear in M's star shape — the measured
§10 finding; capped statements counted in `statements_dropped`); `WikiDisputeFeed`; the
**mechanical panel + `ContradictionAgent`** (no LLM roles — telemetry is expected trivially zero
and any nonzero value is a bug); `ttl` set, `segment_cap` 25, `min_interval_s` ≥ 2 s,
`max_seconds` a few hours, `stop_file` armed, `checkpoint` on to a **runs/ side store, never the
main corpus**, `state_path` + `frontier.json` set (kill + `--resume` rehearsed); every poll
**recorded to disk** (`polls.jsonl`) so the whole run replays offline afterward. Driver:
`tools/run_live_wikidata.py`; findings go to `runs/RUN_1_LOG.md`.

**Priors (P1–P7), each bound to its instrument:**

- **P1 — disposition mix** (digest `dispositions`): ≥ 90% of *revising* rounds are `new_fact`;
  `retract_fact` present but rare (deprecations/overturns exist in Wikidata but are a small
  fraction); `challenge_to_M` ≈ 0 (run 1 seeds no laws and ground facts propose none);
  `generalization` = 0 (the feed's shapes are ground/negation only). *A nontrivial retract rate is
  a finding about the wiki-world's flux, not an error.*
- **P2 — mechanism durability ordering** (`mechanism_principles` over `LiveResult.episodes`,
  decay-aware): stick-rate(reliable_source) ≥ stick-rate(consensus); `unresolved` never durable;
  `decay_erased` reported, not silently folded in. *A reversal — bare consensus outlasting
  referenced values — would be a genuine discovery about Wikidata's editorial dynamics OR about
  our reverts-proxy being too thin to carry the mechanism distinction; the friction map and the
  raw dispute records arbitrate which.*
- **P3 — the working set** (digest `m_relations` / `decayed`): |M| pinned at ≈ ttl within 2–3
  segments and flat thereafter; with run length ≫ ttl, the majority of episodes read
  `erased_by_decay` (the watched session read 125/150). *|M| hitting `max_m_relations` indicts the
  ttl-vs-source-revisit-rate tuning — an economy-of-research parameter, and the first empirical
  input the tropism module will need.*
- **P4 — resolution principles** (`resolution_principles` / `gaps` / `friction_map`): every
  populated situation maps with stability 1.0 (the mechanical agents' firing conditions are
  near-disjoint); **zero thrash, zero gaps, friction ≈ 0**. *Any thrash or recurring gap is a
  design finding against the rulebook — the priority ordering or a missing disposition — and is
  the single most valuable kind of result run 1 can produce.*
- **P5 — the shape of the dialog** (`proposal_shape` over episodes): shapes ∈ {ground, negation}
  only; `law` and `counterexample` ≈ 0; `unparseable` = 0 (statements are mechanically scribed);
  `branched` = 0 (the mechanical panel has no branch hook). *Run 1's dialog is expected to be
  **monological ingestion** — that is the baseline the directed-engagement build will be measured
  against, so even confirming it is load-bearing.*
- **P6 — poise** (`poise_from_digests`, comparative across the run's own phases): mostly ● with
  **rigidity (○) as the likely failure pole late in the run** (a frontier crawl repeats itself;
  redundancy rounds rise); stumbles rare, absorbed within one segment; ✕ (thrash) ≈ 0. *A wall of
  ○ from the start means the frontier is mis-designed (feeding only redundancy); any ✕ points back
  at P4.*
- **P7 — operational floor** (tripwires + checkpoints): legibility ≈ 0.0 every poll (labels on);
  telemetry all-zero (no LLM in the loop); every checkpoint §3.3-attests; per-segment elapsed
  flat; resume from `state_path` works if exercised. *Any violation halts interpretation of
  P1–P6 until explained — operational failures poison the evidential value of everything
  downstream.*

**Standing interpretation rules** (from §4c/§7, restated so the run log can cite them): findings
are about the wiki-world-as-represented and about the game — never the world; read discovery off
the **trajectory**, never a single M; a rate is meaningless without its volume (stick-rate with
`decay_erased`, accuracy with abstentions); silence is evidence only where a tripwire watches;
poise is read, never targeted.

## 12 · Run 2 — the change stream (BUILT; priors AFFIRMED by the author 2026-07-02, pre-run)

Run 1's disposed findings (runs/RUN_1_LOG.md) *prescribed* this build: **F3** — the crawl
samples the settled surface and carries almost no contestation (1 deprecated / 432 statements);
**F2** — a relinquishment only bites when its target still stands in the working set. The
**`recentchanges` adapter** answers both at once: each poll asks which items were *just edited*
(bots excluded by default) and fetches those — the sample skews to live contestation, and an
entity edited again is fetched again, so a deprecation arrives while the bare value it overturns
may still stand in M. *Recency-selection is the revisit.*

**BUILT:** `rc_ids` (the pure payload→ids half, offline-tested) + `recentchanges_fetch` (the
real call, `rcend`-continuation from the previous poll's newest timestamp) +
`RecentChangesSource` (a **never-exhausting** `LiveSource` — the runner's stops are the only
ends; empty polls pace and re-poll; same hub cap / label cache / poll record / legibility
tripwire as the rotating source; `save_state`/`load_state` persist the continuation point).
Driver: `tools/run_live_wikidata.py --source recentchanges`. The **headline test** demonstrates
the F2 fix offline: a bare value admitted from poll 1 is overturned when poll 2 re-delivers the
same entity carrying the deprecation + a referenced replacement — `mechanism_principles` then
*actually differentiates* (consensus 0.0/not-durable vs reliable_source 1.0/durable), which run
1 left vacuous. A bounded live smoke validated the real endpoint (62 rounds; notably
**reliable_source-heavy** — 49:13 vs the crawl's consensus-heavy 299:127 — actively edited items
carry references; legibility 0.09, labels lag fresh edits).

**Priors (P1′–P7′) — AFFIRMED by the author 2026-07-02, before execution** (the §11 discipline:
priors predate the run they read). Affirmed as drafted, including the three flagged judgment
calls: P2′'s reversal-is-a-discovery commitment, the `!bot` scoping (M-game models the
wiki-world's *human editorial activity*), and the 0.2 legibility lag threshold. Run shape:
**supervised sitting**; after run 2 is disposed, this arc **pauses and the alpha-release
documentation track resumes** (the author's scheduling decision, same date):

- **P1′ dispositions:** `new_fact` still dominant, but `retract_fact` **> 0** over a multi-hour
  run (the stream revisits; deprecations and reverts are present); challenge/generalization ≈ 0.
  Redundancy rounds **≫ run 1** (revisits re-deliver standing facts — the mechanism working,
  not a failure).
- **P2′ (the run's question):** mechanism durability actually exercised — expect overturns;
  prior: stick-rate(reliable_source) ≥ stick-rate(consensus), with consensus **< 1.0** once
  overturns occur. If the ordering *reverses*, that is a genuine discovery (about Wikidata's
  editorial dynamics or about our rank/reference mapping).
- **P3′ working set:** |M| ≈ ttl as before; revisited facts stay warm (redundant re-deliveries
  touch the ledger), so decay concentrates on entities the stream abandons.
- **P4′ rulebook:** still zero thrash/gaps expected. Watch the new situation run 1 saw once —
  `true:negation` (a denial whose target is not standing) — it should *consistently* dispose
  inert; if it sometimes revises, that is a gap (a missing rule).
- **P5′ dialog shape:** ground + negation only; the negation fraction ≫ run 1; branched = 0.
- **P6′ poise:** ● dominant. Caveat: heavy-revisit windows depress engagement (many redundancy
  rounds) and can read as rigidity — interpret the ○ pole against the redundancy count before
  calling it a stall. Quiet-stream stretches produce *no rounds at all* (not rigidity — absence
  of play).
- **P7′ operational floor:** as run 1, plus: legibility may be **small-but-nonzero** on freshly
  edited entities (labels lag edits — 0.09 observed in the smoke); treat < 0.2 as expected lag,
  a sustained rise as degradation. Checkpoint wall-clock rider (F1) still applies.

## 13 · Arc re-entry: the tropism module — the warm-set re-poll (drafted + AFFIRMED 2026-07-02)

*Drafted at the close of the alpha-docs track so the re-entry session starts from a design, not a
blank page. Per the pre-registration discipline (§11–§12): the author affirms or amends this
section — including the open decisions at the end — before any code is written.*

**AFFIRMED 2026-07-02 — all five decisions as drafted:** (1) policy + `source.inject(ids)`;
(2) decay-adjacent first; (3) `warm_fraction` 0.5, fixed for run 3; (4) run 3 = crawl + tropism;
(5) ambiguous labels skip + count. Built the same session: `src/tropism.py`
(`WarmSetTropism` + `reverse_labels`), the `inject` seam + `known_labels` on
`RotatingWikidataSource`, `LiveRunner(tropism=…)` consulted at each poll boundary, and the
driver's `--warm-fraction` knob (0 = the runs-1/2 passive baseline); tests
`tests/test_tropism.py`. One reading note for P1″: the mechanical panel records a re-delivered
unchanged value as a **non-revising round** (disposition `None` — every agent abstains), so the
digest surfaces it as `non_revising`; that count *is* the redundancy fraction P1″ reads.

**RUN 3 EXECUTED & DISPOSED 2026-07-03** — see [`runs/RUN_3_LOG.md`](../runs/RUN_3_LOG.md).
Headlines: **P1″ CONFIRMED** (`non_revising` = 100/423 = 23.6 % — the fraction runs 1–2
measured at zero; canary green); **F1″** — decay bounds the *vocabulary* (relation names),
not the *sheet* (atoms): the tropism pins the held names warm, so atoms accumulate under hot
names (digest |M|=10 vs a 135-atom five-hub sheet at seg 17; attest wall-clock 3.3 → 1075 s)
— `challenge_to_M` against §10's capacity units, instrument/rulebook prescriptions queued;
**F2″** — the P2 event = **revisit × world-motion**: revisit alone is necessary, not
sufficient (both live deprecations were born-deprecated → target never standing → correctly
inert, even on the warm re-reach) → **run 4 = stream + tropism** is the named next
experiment. Poise 17/17 ● at warm_fraction 0.5 (the predicted redundancy ○ did not appear).

**The mandate (empirical, not philosophical).** Runs 1–2 characterized both passive membranes:
the crawl samples the settled surface, the stream samples the novelty frontier, and **neither
revisits** (run 2: 53 entities, zero seen twice in ~75 min). P2 — mechanism durability, *the*
question — was vacuous both times. The instruments' verdict (RUN_2_LOG F2′): *ingestion alone
cannot test durability; only directed re-engagement can.* What §4d held as a commitment is now a
mandated build. The first tropism is the humblest one: **re-check what you hold.**

**Placement (the §4d discipline made structural).** Tropism belongs to the **player, not to M and
not to the source**. So it is a *policy the runner consults at each poll boundary*, not a new
membrane: a `Tropism` object reads the player's own state and emits the next reaches; the sources
stay dumb fetchers and gain exactly one seam (accept injected ids). Increment 1 implements only
the **irritation pole** (`attention_brief` is its proto — §4d); the musement pole and the
horizon-as-register remain future, named, unbuilt.

**Increment 1 — the design:**

- **`src/tropism.py`** (additive, geometry-free, no protected-core change):
  `WarmSetTropism.reaches(model_egif, ledger, label_to_id, k) → List[entity_id]` — the entities
  backing M's **standing** facts, priority **decay-adjacent first** (facts nearest their ttl:
  re-check *while the target still stands*, before decay erases the evidence-bearer — this is
  what makes durability testable, and it ties the policy to the irritation pole rather than to
  truth-tracking).
- **Recovering the warm set.** M's facts carry *labels* (legibility resolved them at ingestion);
  the id→label map lives in the run's persisted `LabelCache`. Reverse it (label→id); an
  unresolved id is already an id; an ambiguous label (two ids, one label) is re-polled on all its
  ids or skipped — **counted either way, never silent**. No schema change, no new provenance
  channel: increment 1 rides what the state files already carry (and `--resume` already
  preserves).
- **The mix — the economy-of-research knob.** Each poll's chunk = `warm_fraction` from the
  tropism + the remainder fresh (frontier or stream). All-fresh is runs 1–2; all-warm is a closed
  loop that never meets a newcomer (the rigidity pole ○). Proposed default: 0.5.
- **The source seam.** `RotatingWikidataSource` keeps a `_seen` set precisely to *prevent*
  re-enqueueing — the warm seam must **bypass `_seen`** (that is the whole point: a deliberate
  re-reach is not a crawl duplicate). Either `inject(ids)` on the source (front-of-queue,
  seen-exempt) or the driver composes `fetch_ids(warm) + source.fetch()` — decide at build
  (decision (a) below).
- **What it must NOT do (the floor, §7).** The re-poll's aim is to **exercise the durability of
  settled habits**, not to verify M against the world — a re-delivered unchanged value is a
  `redundancy` round (the habit holding), a deprecation/changed value arrives as a denial that
  now *meets its standing target* (the P2 event, mechanically disposed by the existing panel and
  `ContradictionAgent`). No new referee, no disposition change, nothing auto-promotes.

**Run 3 — draft priors (each bound to its instrument; to affirm pre-run):**

- **P1″ the revisit works** (digest `dispositions` / episodes): `redundancy` ≫ 0 — the
  structural fraction runs 1–2 measured at zero. If redundancy stays ≈ 0 with warm_fraction 0.5,
  the warm-set recovery is broken (labels not reversing, or ids not reaching the fetch), an
  implementation finding, not a world finding.
- **P2″ durability, finally populated** (`mechanism_principles`, decay-aware): retracts > 0 live;
  consensus stick-rate < 1.0 once overturns occur; reliable_source ≥ consensus expected —
  **a reversal is a genuine discovery** (about Wikidata's editorial dynamics or our
  reverts-proxy; the raw dispute records arbitrate). `decay_erased` reported, not folded in.
- **P3″ the ledger under re-poll** (digest `m_relations`/`decayed`): warm re-polls touch held
  facts' relations, so decay concentrates on what the tropism *doesn't* choose — |M| still
  ≈ ttl; a working set pinned by re-poll rather than by arrival order is the intended change.
- **P4″ true:negation, for free**: denials meeting standing targets consistently retract;
  denials without a standing target consistently inert. Inconsistency = a rulebook gap (the §6
  instrument that would catch it: `gaps`).
- **P5″ attribution** (against F3′): the baseline replicated across two passive sources, so any
  departure — redundancy fraction, retract rate, a second resolution principle — is attributable
  to the tropism, not source variance. Run 3 should be **crawl + tropism** for exactly this
  reason (same source as the run-1 baseline; stream + tropism is run 4's candidate).
- **P6″ poise, read honestly**: redundancy-heavy windows depress engagement — read ○ against the
  redundancy count (§12's caveat, now expected as the *normal* case); the warm/fresh mix is the
  structural guard against the all-warm rigidity loop.
- **P7″ operational floor**: unchanged from §12, plus the **hub-degree rider**: the warm set by
  construction concentrates polls on entities M already holds — a star-shaped M is the checkpoint
  attest's worst case (the 140× fix helps; `per_entity_cap` still applies and its drops are still
  counted).

**Open decisions for the author (affirm/amend at the re-entry session, before code):**

1. **Seam form** — `Tropism` policy + `source.inject(ids)` (runner stays thin) **vs** the driver
   composing warm and fresh fetches itself (no source change). Draft recommends the former: the
   seam is one method, and the policy stays testable offline against recorded state files.
2. **Warm priority** — decay-adjacent first (draft recommendation, argued above) **vs**
   oldest-unchecked first **vs** uniform over held entities.
3. **The knob** — `warm_fraction` default (draft: 0.5) and whether it is fixed or
   segment-adaptive (draft: fixed for run 3; adaptivity is itself a finding to earn).
4. **Run 3 source** — crawl + tropism (draft recommendation, P5″) **vs** stream + tropism.
5. **Ambiguous labels** — re-poll all candidate ids **vs** skip + count (draft: skip + count for
   run 3; the ambiguity rate is itself worth measuring before spending polls on it).

## 14 · Run 4 — stream + tropism (the F2″ composition; priors AFFIRMED by the author 2026-07-03, pre-run)

**The mandate (RUN_3_LOG F2″).** Run 3 proved the tropism's plumbing (P1″: the redundancy
fraction went 0 → 23.6 %, warm counters clean) and in the same hour sharpened P2's requirement:
**the P2 event = revisit × world-motion**. The crawl's settled surface did not move within the
hour, so the only deprecations delivered were *born-deprecated* — never admitted, target never
standing, correctly inert even on a warm re-reach. Revisit is necessary, not sufficient. Runs 2
and 3 proved the two halves separately (the stream samples the world *moving*; the warm set
*holds the target standing*); run 4 composes them. With it the 2×2 design closes:
run 1 = crawl·passive, run 2 = stream·passive, run 3 = crawl·tropism, **run 4 = stream·tropism**
— departures read against both margins (vs run 2: the tropism's effect on the stream; vs run 3:
the source's effect under tropism).

**The author's dispositions of the run-3 horizon (2026-07-03, this session, pre-run):**

1. **F1″ atom-unit instruments — build now** (affirmed as recommended): `SegmentDigest.m_atoms`
   (sheet atoms after the segment — the honest unit beside the name-unit `m_relations`) +
   `LiveRunConfig.max_m_atoms` (the atom-unit safety net; driver `--max-m-atoms`, default 1000)
   + a live `atoms=` column in the per-segment console line. Instrument-only, no behavior
   change; run 4's priors bind to it (P3‴).
2. **F1″ rulebook question — DEFERRED, observe first** (affirmed as recommended): what *one
   fact's* disuse under a warm name means (per-name atom cap vs atom-level decay) is a real
   rulebook change; decide it on run-4 evidence with the honest column in view, not before.
   One variable at a time — run 4 changes the *source*, not the decay semantics.
3. **F1″ attest-cost residual — optimized now** (affirmed as recommended): the ligature
   router's visibility-graph build (`elk_layout_engine._route_via_visibility_graph`) gained
   three exact, deterministic accelerations — a **separation short-circuit** (one endpoint
   inside an obstacle rect and one out → no path exists; the over-constrained-soft case that
   used to exhaust the whole graph), a **uniform grid** over obstacles (a segment consults only
   obstacles sharing a cell; registration inflated one cell, so the same crossings are found),
   and **lazy A\*** (Euclidean heuristic, consistent → first arrival is a shortest path;
   visibility edges computed only for expanded nodes). Measured on the F1″ fixture: the
   run3_seg17 checkpoint (135 atoms, five hubs deg 20–25) load-attests in **3.8 s** where it
   exceeded **10 minutes** (>160×); run3_seg1 7.4 s → 0.4 s. Correctness: routes remain
   shortest paths (tie-breaks may differ from the old eager Dijkstra — still deterministic);
   the correspondence/reader/tension/LaTeX suites pass.
4. **The spectator surface — stays queued, unaffirmed** (RATE_AND_INTELLIGIBILITY hypotheses +
   ADAPTIVE_SCOPE_VIEWER §10); run 4 executes first.

**Machinery under test (built 2026-07-03, offline-proven in `tests/test_tropism.py`):**
`RecentChangesSource` gains the §13 seam — `inject(ids)` (warm re-reaches ride the **front of
the next poll's chunk**, ahead of whatever the stream delivers; the stream has no `_seen`, so
the seam only skips already-pending ids; counted, never silent) + `known_labels()` +
`warm_pending` persisted through `save_state`/`load_state` (a persisted warm re-reach survives
resume, verbatim — the run-3 lesson). One deliberate semantic: **a quiet stream tick still
serves the warm set** (warm pending → the poll fetches them even when nothing was edited) — the
tropism holds its targets standing *while the world is idle*, which is exactly the F2″
composition. The driver's `--source recentchanges --warm-fraction` refusal is lifted. Offline
headline (`test_stream_plus_tropism_composition_delivers_the_p2_event`): the stream mentions an
entity once and moves on; the world then deprecates the admitted value and references a
replacement; only the tropism's warm re-reach revisits — the denial **meets its standing
target**, the panel retracts, the referenced value stands.

**Run shape:** supervised sitting, one hour, config matching run 2's stream run except the
tropism on: `--source recentchanges --runs-dir runs/run4 --max-seconds 3600` (chunk 8,
warm_fraction 0.5 → k=4, per_entity_cap 25, ttl 30, segment_cap 25, min_interval 5.0,
max_m 200, max_m_atoms 1000). Findings → `runs/RUN_4_LOG.md` (skeleton pre-registered).

**Priors P1‴–P7‴ (each bound to its instrument; affirmed pre-run):**

- **P1‴ the tropism works on the stream** (digest `non_revising` + `warm_injected` + skip
  counters): non-revising > 0 (run 2 measured zero) with counters clean (emitted = injected,
  skips counted). The stream's warm set forms more slowly than the crawl's (facts arrive from
  whatever was just edited), so the fraction may run below run 3's 23.6 % — the *presence* of
  the warm-shaped texture is the prior, not its magnitude.
- **P2‴ THE RUN'S QUESTION — the P2 event, live:** a value admitted from an earlier poll is
  denied (deprecation / rank change / reliably-sourced replacement) while it **still stands**
  in M → `retract_fact` > 0 live, and `mechanism_principles` differentiates on live data
  (consensus stick-rate < 1.0 once overturns occur; reliable_source ≥ consensus, a reversal =
  a genuine discovery). Honest floor: born-deprecated deliveries stay correctly inert (run-3
  F2″); the event needs the world to move *between visits within the hour* — the stream skews
  to actively-edited entities, so motion is plausible, not guaranteed. **A zero is then a rate
  finding** (the event is rarer than a 1-hour horizon), not a machinery finding — the offline
  headline already witnesses the mechanism.
- **P3‴ atoms, the honest unit** (digest `m_atoms` vs `m_relations` — the new F1″ instrument's
  first live outing): expect atoms ≫ names wherever warm names pin hubs; `max_m_atoms` firing
  is a *legitimate stop*, not a failure (the net working). Report the atoms-per-warm-name
  profile — this is the evidence the deferred rulebook decision (per-name cap vs atom-level
  decay) will be made on.
- **P4‴ true:negation, both sides now reachable**: denials meeting standing targets
  consistently retract (the P2‴ event); denials without a standing target consistently inert.
  Inconsistency on either side = a rulebook gap (`gaps`).
- **P5‴ attribution (the 2×2 closes)**: vs run 2 (same source, passive) any redundancy/retract
  departure is tropism-attributable; vs run 3 (same tropism, crawl) any contestation-mix
  departure (reliable_source-heavy, deprecations present) is source-attributable. Expect run
  2's mechanism mix (49:13 reliable-source-heavy) to survive the tropism.
- **P6‴ poise, read honestly**: quiet-stream stretches no longer produce zero rounds when the
  warm set is non-empty (the quiet tick serves it) — expect *fewer* dead segments than run 2;
  redundancy waves read against `non_revising` (run 3: ● even at 96 % redundancy at 0.5).
- **P7‴ operational floor**: legibility < 0.2 (labels lag fresh edits; 0.09 in the run-2
  smoke); all checkpoints §3.3-attest to the side store; determinism canary green
  (`polls.jsonl` replay). **The attest-cost rider, re-measured**: with the visibility-graph
  fix in, checkpoint elapsed should track round compute rather than dominating wall-clock
  (run 3: attest ≈ 100 % of elapsed, 3.3 → 1075 s; the fixture now loads in 3.8 s) — segment
  elapsed staying flat-ish while atoms grow is the fix confirmed live; a super-linear tail
  reappearing is a new finding.

## 15 · The docket of doubts — surprise as a two-faced artifact (DRAFT 2026-07-03, pre-registered; mandate PENDING run-4 disposal)

*Drafted while run 4 executed, per the §13 discipline: the design predates its mandate so the
re-entry session starts from a page, not a blank. The mandate line is deliberately open — run
4's findings name the actual bottleneck (revisit rate? world-motion rate? probes undirected by
content?), and the author affirms or amends this section — including the open decisions at the
end — before any code is written. If run 4's disposal mandates something else, this section
waits without prejudice.*

**What increment 1 taught, read forward.** The tropism now on the board (§13) maps *state* to
*query*: a standing fact → its entity → a re-reach. It is identity-shaped — the probe's content
is "this entity again," never "this missing answer." Meanwhile the system already *names its own
missing answers* in three places, none of which currently reaches the membrane: the peel's
**Kleene UNKNOWN** transcript entries (the atoms the oracle could not decide — the
addressability gap `m_render` computes as the honest horizon); the Graphist's **`attention_brief`
thin spots** (relations with ≤1 instance, ungrounded laws, lonely individuals — today they seed
*proposals*, tested inward against M, never *probes*, sent outward); and any **materialized
consequence without a witness** (what `model_materialization` can forward-chain from a
hypothesis but nothing currently tracks as *deduced-awaiting-evidence*). Three articulations of
doubt; one plumbing gap: no wire from articulated doubt to executable reach.

**The unifying primitive: the docket.** One player-side register of *named wants* — each entry a
small EG shape (an atom or subgraph) that M neither holds nor denies, carrying:

- **shape** — the relation + argument shape wanted (e.g. `(phase_shift ?f "T")`);
- **constants** — what is already bound (the handle the membrane can grip);
- **provenance** — *why it is wanted*: `unknown_in_peel(G)` · `thin_spot(kind)` ·
  `deduced_from(H)` (the hypothesis whose standing rides on it) · `horizon(garbled-arrival)`;
- **priority** — the economy of research (below);
- **age / attempts** — a docket entry that never resolves is *counted, never silently dropped*
  (the `attest_overview` twin, again).

This **is** §4d's *horizon as a first-class register*, previously named-but-unbuilt — extended
one notch: it holds not only the not-yet-legible that *arrived* garbled, but the
not-yet-answered that *inquiry itself generated*. Placement per the §4d/§13 discipline: the
docket belongs to the **player** (not M — M objectified is driveless marks; not the source —
sources stay dumb fetchers). A policy consulted at the poll boundary, exactly where
`WarmSetTropism` sits today; the two compose (warm re-reach is simply the docket's cheapest,
lowest-articulation stratum).

**The two faces of an entry.** The same artifact works outward and inward — this is the
section's load-bearing claim, and the reason docket and abduction must not be built as separate
organs:

- **Outward — the membrane query.** An entry maps to the *highest query vocabulary the source
  offers*, negotiated per source: **Q1** entity re-reach (`inject(ids)` — exists); **Q2**
  entity + property fetch (a filtered `wbgetentities` — cheap seam); **Q3** shape query
  (SPARQL: "all x with P" — the long-deferred SparqlOracle seat, relocated to the *membrane*
  side where it belongs); **Q4** the open ask (a question posed to a human or LLM source — the
  reading-desk surface; the first genuinely *bidirectional* membrane). An entry no vocabulary
  can express stays on the docket, counted — the honest residue.
- **Inward — the abduction seed.** The same entry handed to the Graphist/Grapheus as the
  *situation of doubt*: "here is what the world has not answered; propose the hypothesis that
  would explain or predict it." The hypothesis's materialized consequences enter the docket as
  `deduced_from(H)` entries → probes → witnesses or refutations → the hypothesis's standing.
  Abduction generates probes; probes discipline abduction; one ledger carries both directions.

**Entertainment, not assertion (the provisional-consequence machinery).** An abductive
hypothesis must be *entertained* while its consequences are hunted — never asserted. The
machinery exists: **branch the DAG** (the Stage-3 `_fork_siblings` mechanics — two chain steps
sharing a `from_state_id`). H lives on a **proving-ground branch M′**; `materialize_egi` runs
there; its unwitnessed derived atoms enter the docket tagged `deduced_from(H)`. A witness
arriving through the membrane strengthens H (its docket entries resolve); a refutation
relinquishes the branch — and the DAG *keeps* the entertained-and-relinquished hypothesis as
negative knowledge (§6 mines failed abductions exactly as it mines failed generalizations).
Admission of H to the main line is a *disposition* like any other — nothing auto-promotes; the
floor (§7) is untouched. Level Zero already provides the scroll shape for the conditional
reading (`cut[H cut[consequences]]`) where a branch is too heavy.

**The economy of research (priority, Peirce's own doctrine).** Order the docket by: **cost
tier** (Q1 < Q2 < Q3 ≪ Q4 — ask cheap questions first); **decay-adjacency** (inherited from
§13 — re-check while the target still stands); **discrimination value** (prefer probes whose
answer separates standing hypotheses — a probe that would refute H₁ *or* H₂ whichever way it
lands beats one that flatters both); **starvation guard** (age raises priority slowly, so the
expensive articulate asks eventually fire — bounded by budget). Increment discipline: v1 is a
fixed lexicographic ordering; a *learned* priority is itself a finding to earn (§6 across runs).
*Later, gated refinement (recorded 2026-07-03):* a **structured-embedding prior** — a
hyperbolic/Poincaré embedding of the vocabulary (subsumption lattices embed there almost by
construction; the `kind=ontology` imports are the natural training set) supplying a
*plausibility ranking* over candidate probes and candidate laws (the `MutationProposer`
currently recombines blindly). Strictly proposal-side, the same floor as `agon_llm`: the
embedding may **suggest** an ordering; every candidate that counts is reduced to a calculus
artifact and re-checked — approximate similarity never substitutes for identity (no "close"
labels merged, no "near" atom as a witness). Earns its place only after v1's fixed ordering
has a measured failure.

**The speculative horizon (recorded, fenced, never a target).** The author's hypothesis, worth
carrying explicitly: the outward face — a mind presenting *its* surprise to the world through
the membrane — may be how the world generates creativity in itself by means of minds. Peircean
anchors: objective idealism (matter as effete mind; the universe itself acquiring habits), the
growth of concrete reasonableness, musement as the pull-pole that seeds abduction. Mechanical
reading: Q1–Q3 are read-only (the world unchanged by being asked — the hypothesis idles);
**Q4 is where it becomes empirical** — an asked human/community *articulates what it never had
occasion to state*, and the common sheet grows on *both* sides of the membrane
(ground-enlargement as a two-way street; the wiki talk-page question that precipitates an
editorial resolution which did not exist before the asking). Honesty clauses, standing: this is
a hypothesis about the system's *role*, not anything the calculus can attest (§3.3 attests
correspondence, not truth, and certainly not cosmology); docket throughput must never become a
target (Goodhart — §7); findings remain findings about the game. The musement pole gets its
first mechanical seat here as the docket's lowest-priority stratum: budget-bounded playful
entries (the `MutationProposer` generalized from recombining M's relations to recombining
*questions*) — drawn, not driven, and cheap by construction.

**Increments (each earned, none anticipatory):**

- **2a — the docket, minimum.** `src/query_docket.py` (working name; see decision 5):
  entries from the peel's UNKNOWN transcript + `attention_brief` thin spots; consumer = the
  existing `inject(ids)` seam (entries whose constants reverse to entity ids ride Q1; the rest
  wait, counted). No new source capability, offline-testable end to end, composes with
  `WarmSetTropism` at the same poll boundary.
- **2b — the proving ground.** Branch-entertained hypotheses + `deduced_from(H)` entries +
  witness/refutation resolution + relinquished-branch mining. Closes the author's
  abduction↔probe loop mechanically (a scripted Grapheus suffices offline; the LLM seat drops
  in unchanged).
- **3 — the vocabulary ladder.** Q2 (property-filtered fetch), then Q3 (the SPARQL membrane
  seam). Each tier pre-registered with its own run before the next is built.
- **4 — the open ask (horizon).** Q4 the bidirectional membrane + the musement stratum — where
  the speculative hypothesis above first becomes testable rather than decorative.

**Open decisions for the author (affirm/amend before code):**

1. **Mandate gate** — build 2a only if run 4's disposal names *content-undirected probing* (or
   UNKNOWN starvation) as the operative bottleneck; otherwise this section waits for the run
   that does.
2. **Docket placement** — player-side policy at the poll boundary, composing with (not
   replacing) `WarmSetTropism` (draft recommendation) **vs** folding the tropism into the
   docket as its Q1 stratum from day one.
3. **Admission rule for a witnessed hypothesis** — mechanical threshold (N independent
   witnesses, zero refutations) **vs** an Agonothetes judgment seat (draft: mechanical for 2b;
   the judge is an LLM-stage refinement).
4. **Proving-ground cost** — does M′ checkpoint (§3.3 per segment, real cost) or stay
   RAM-bounded per hypothesis with only its *outcome* checkpointed (draft: outcome-only; a
   hypothesis is entertainment, and the F1″ lesson says checkpoint weight is the binding
   budget)?
5. **The name** — docket of doubts / horizon register / question ledger (draft: **docket** —
   it is procedural, ordered, and disposed, which is exactly Peirce's register of the term).
