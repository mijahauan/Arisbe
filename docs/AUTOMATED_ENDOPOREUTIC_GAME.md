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
calculus* · aim = **discovery** · **Drafted**: 2026-06-30 · **restructured 2026-07-11** (below)

> **How to read this document (restructured 2026-07-11).** It is now three parts. **Part I
> (§1–§10)** is the design of record — what the automated game *is* and what was built, largely
> as drafted before any live run. **Part II (§11)** is *what running it has taught* — the
> principles eleven live runs established, folded back into the design as run-cited findings
> (before this pass they were scattered across a dozen run appendices). **Part III (§12)** is the
> **run ledger** — a compact chronological table + a findings index, each run linking to its full
> `runs/RUN_N_LOG.md` (where the per-run pre-registration and disposal detail lives; this document
> carries the synthesis, not a second copy). Runs 1–10 are executed and disposed; run 11 (the
> calibrated precip arm) is built and awaiting the author's launch.

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
5. **Content-directed probing — the docket of doubts (BUILT — `query_docket.py`, increment 2a).**
   The tropism (§4d; runs 2–3) maps *state → probe* ("this entity again"); the docket maps *articulated
   doubt → probe* ("this missing answer"). The system already names its own missing answers in
   three places that never reached the membrane — the peel's Kleene **UNKNOWN** transcript
   (the addressability gap), the Graphist's `attention_brief` thin spots, and materialized
   consequences awaiting a witness — so `QueryDocket` registers those *wants* (age/attempts,
   counted never dropped), prioritizes them (Q1 `reaches()` via the same label-reversal as the
   tropism: fewest-attempts → oldest), and settles the answered ones per segment; the honest
   residue is `inexpressible` (a want no probe can currently voice — the Q2/Q3 tiers exist to
   shrink it). It composes with the tropism at the poll boundary. This is the answer to the
   *content-undirected probing* bottleneck run 5b named by elimination (§11 findings, run 5).

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
The mechanical source-conflict agent shipped (`agon_evolution.ContradictionAgent` +
`model_revision.retract_atom`), so the *raise-only* loop disposes contested contents without an
LLM. **The first live raise-and-resolve source is now BUILT too** — NWS weather
(`src/weather_source.py`), run live in runs 7–11 (Part III). Its lesson (Part II, §11.4) is the
one this design most owes to the runs: *whether a refuted theory can re-generalize into a better
one depends on whether its recalibration knob **calibrates** or merely **selects**.*

**Why one source is not enough — branch by source class (established, run 5b → run 7, F3⁷).**
A membrane's *class* determines which dispositions the game can even exercise. Wikidata alone
ran ~100 % `new_fact` (a curated record of settled values has almost no refutation to offer — the
inductive/refutational registers stayed idle, and the final M carried **zero laws**); the weather
resolving membrane, by contrast, made the game *predict and be falsified*, exercising exactly the
`challenge_to_M` / re-generalize registers Wikidata could not. So a finding read off one source is
provisional: **branch sources wherever a finding's disposition would differ by source class**
(the single-source check). This is why the arc deliberately moved Wikidata → weather, and why the
next planned source is a *third* class (sports outcomes — a discrete resolving membrane) rather
than more weather.

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
re-poll tropism, `src/tropism.py`; runs 2–3 in the Part III ledger.)*

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
- **The live raise-and-resolve source is BUILT — NWS weather** (`src/weather_source.py`,
  `weather_recalibration.py`, `tools/run_live_weather.py`): M forecasts (the peel), the world
  resolves, and a refuted seeded law is **re-generalized** (run 8) — the register Wikidata's
  settled record could not exercise. Run live in runs 7–11; the calibrated precip arm (run 11) is
  built and awaiting launch. See Part II §11.3–11.4 for the principle and Part III for the ledger.
- **Next.** A *third* source class (sports outcomes — a discrete resolving membrane, to test
  whether the knob-type law of §11.4 is general or weather-specific); the
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

1. **Bound \|M\| with disuse-decay** (`LiveRunConfig.ttl`). An **atom** idle for `ttl` *global*
   rounds is erased (atom-level since 2026-07-03 — the rulebook decision, Part II §11.2; before that the
   unit was the relation *name*, which RUN_3 F1″ showed a warm hub name defeats: tropism kept
   the name touched while its atoms accumulated unboundedly). Use = **re-delivery**; erasure by
   `retract_atom`, so name-siblings and standing law cuts survive. Decay is applied by the
   runner **across segments** (not inside each per-segment `run`, whose ledger would reset
   every segment and never bound anything). Measured: with `ttl` on, \|M\| stabilises at ≈`ttl`
   **in atom units too** and per-round cost / memory / per-checkpoint disk stay roughly
   constant; with it off, \|M\| grows without bound (and cost with it).
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

**The run-1 kit (BUILT 2026-07-02)** — everything the run-1 pre-registration names, assembled:
`wikidata_source.RotatingWikidataSource` (the **rotating frontier**: a Q-id queue consumed
`chunk_size` per poll, fetched *lazily at poll time* so the runner's pacing actually paces the
API; `crawl` grows the frontier from entity-valued statement values, bounded by `frontier_cap`
with drops counted; one `LabelCache` across the run — fetch only unseen ids, negative-cached —
and `save_state`/`load_state` so a resumed run **continues its crawl**);
`record_poll`/`replay_polls` (every poll appended as JSONL → the whole run replays offline
through `WikidataSource`, the determinism canary — used the very day it was built, to reproduce
a live timing anomaly offline); and the driver `tools/run_live_wikidata.py` (side-store
checkpoints under `runs/<run>/checkpoints`, `state.json` + `frontier.json` + `--resume`,
STOP-file, pacing, per-segment console digests, final §6 + poise summary; findings logged in
`runs/RUN_1_LOG.md`). Rehearsed end-to-end against the live API, including a
stop + `--resume` continuing segments 3–4 with the frontier and decay clock intact.

**Cost scales with M's *shape*, not just |M|** — the operating consequence of Part II §11.1. The
capacity table above is a size table; a *hub-shaped* M (a Wikidata entity's star graph) makes the
§3.3 attest and the ligature router super-linear in hub degree, not fact count. The controls: the
exact quick-reject / hash-cons / incremental-materializer fixes (§11.1, each bit-identical or
same-closure) and `per_entity_cap` on the rotating source (bound the hub degree at the membrane,
drops counted). **Plan for M's shape (hub degree), not only its size.**

# Part II — what running it has taught

## 11 · The principles eleven live runs established

*Part I is the design as drafted (mostly 2026-06-30, before any live run). This part folds the
run-derived learnings back into it as principles — each stated once, run-cited, with the full
per-run pre-registration and disposal in the Part III ledger and its `runs/RUN_N_LOG.md`. Six
principles; the seventh is the floor, confirmed at scale. Read this as: the design, corrected and
sharpened by contact with the world.*

**11.1 · Cost scales with M's *shape*, not its size (runs 1–4).** The round loop and the §3.3
attest are super-linear in M, but the driver of a blow-up is M's *topology*, not its fact count.
A Wikidata entity's M is a **star graph** (one hub individual shared by every atom), and three
shape-sensitive costs surfaced and were fixed **exactly** (never approximated): the ELK ligature
router's visibility graph (452 s → 3.2 s via an exact bbox quick-reject, bit-identical routes),
`canonical_signature`'s WL colour refinement (15.7 s → 3.3 ms at a 200-atom hub via hash-consed
colours + stop-at-partition-stabilization), and the peel's re-materialization each round
(O(\|M\|²) → O(\|Δ\|·\|M\|) via the semi-naive `IncrementalMaterializer`, same closure). The
operating rule (Part I §10): **plan for M's hub degree, not only its fact count**; bound the
degree at the membrane (`per_entity_cap`) and every exactness-preserving fix pays off.

**11.2 · Disuse-decay bounds the *vocabulary*, and the habit is the atom, not the name (run 3,
F1″ → the atom-level rulebook).** The bound that keeps an unbounded sheet finite is disuse-decay,
but run 3 showed that decaying *relation names* fails: a warm hub name (kept alive by the tropism)
lets its atoms pile up unboundedly under it (attest wall-clock climbed 3.3 → 1075 s). The fix
(the rulebook decision, built 2026-07-03): **decay is atom-level** — the unit of habit is the
fact `(rel a b)`, not the name; **use = re-delivery** (a redelivered atom is the habit holding);
erasure is the *structural* `retract_atom` (`without_element` + orphan-vertex prune), so
name-siblings and standing law-cuts survive an atom's decay. |M| is now bounded in the honest
unit, and the meta-learning stickiness reads decay-erasure apart from game-erasure (§6) so a
decay-bounded live run's stick-rates are not working-set noise.

**11.3 · A live run is predict → refute → *re-generalize*, not predict → refute → *silence*
(run 7 F2⁷ → run 8).** Against a raise-and-resolve membrane M *forecasts* (the peel) and is
*empirically falsified* where it over-reaches — the world relinquishes the over-general law via
`challenge_to_M`. Run 7 found the failure mode this exposes: after both seeded weather laws fell,
the game went **silent** (a relinquished law was never replaced, so the second act was pure
abstention). The fix (run 8) closes the loop: `weather_recalibration.recalibrate` **induces a
better-calibrated law from the prediction ledger and re-seeds it** (the runner re-scribes it onto
M's sheet), so refutation is followed by a *better bet*, not silence. The live calibration payoff
(a law climbing 0.00 → 0.70 accuracy as its discretization is tuned to fresh observations) is
something an offline replay structurally cannot show — the resolution items are frozen at their
recorded discretization — so it is a genuinely *live* finding.

**11.4 · Whether re-generalization *recovers* depends on the *knob type* — a calibration knob
can, a selectivity knob cannot (run 10, F1¹⁰; **confirmed by run 11, F1¹¹**).** This is the principle
the design most owes to the runs. Re-generalization moves a knob; but not all knobs are equal.
The temperature arm's knob is **band width** — a *calibration* knob: widening the band reaches a
regime where the observed value usually falls in-band, so the law earns hits (run 10: net +18).
The precip arm's knob was the **PoP gate** — a *selectivity* knob: raising it makes the arm bet
*less often*, never *more correctly*, so a structurally-mismatched law cannot recover (run 10:
net −5, accuracy 0.14, and it ratcheted the gate to the cap and stayed refuted — P2¹⁰'s "third
outcome," neither converging nor limit-cycling). The general statement: **a refuted theory
re-generalizes into a better one only if its recalibration knob calibrates (moves it toward being
right), not merely selects (moves it toward betting less).** Run 11 was the direct test — it gave
the precip arm a real calibration knob (a two-direction bet around a learned cutpoint, betting the
*majority* outcome via a dry companion law) — and **confirmed the principle decisively (F1¹¹)**:
over 60 resolutions (vs run 10's N = 9) the calibrated arm recovered to **net +58 / accuracy
0.983**, the run's best arm, with the cut moving only on evidence and settling at 70 rather than
ratcheting to its cap (F3¹¹ — the digest signature that distinguishes the two knob types). The
law is now twice-evidenced within weather; whether it is a law of the *game* or a fact about
*weather* is run 12's question (sports — a discrete resolving membrane with no natural width knob).

**11.5 · A re-generalized law's steady state is a positive-net limit cycle *or* a fixed point,
set by domain-noise × discretization (run 8 F2⁸, run 9 F1⁹, run 10 F2¹⁰).** A law that keeps
being felled and re-seeded does not necessarily converge to a fixed point; run 8 found it settles
into a **positive-net limit cycle** — the knob pins at its cap, the law is refelled ~once per
segment and reseeded, yet net climbs (a better dynamic steady state than a frozen guess, since it
keeps earning calibration live). Run 9 showed part of that cycle was an *artifact*: forecast-**centered**
bins (centring the band on the forecast, not a fixed grid) converted the temperature cycle toward
a fixed point — so the cycle **decomposes** into a **grid-edge-fragility** component (removed by
centring) and a **genuine domain-noise** component (which survives it; run 10 saw the centered
temp arm still limit-cycle on noisier convective stations). The honest reading: centring removes
the artifactual wobble; a noisy discretized domain retains a positive-net cycle as its true steady
state — F2⁸ and F1⁹ are each *partly* right.

**11.6 · One source is not enough — branch by source class (run 5b → run 7, F3⁷).** Stated as a
membrane principle in Part I §4b: a source's *class* fixes which dispositions the game can
exercise, so a finding read off one source is provisional and sources must be branched wherever a
finding's disposition would differ by class. Wikidata (settled record) ran ~100 % `new_fact` with
zero laws; weather (resolving) exercised the refutation/re-generalize registers; the next source
is deliberately a third class (sports). See §4b for the full statement.

**11.7 · The floor held at scale — correspondence-not-truth, and warrant by mechanism (runs 5b–6,
the §6 payoff).** Nothing in the run arc dislodged the floor; the runs *confirmed* it operationally.
A live M is a bounded, rolling, low-warrant, diachronic *stance*, never an oracle — and the
meta-learning's `mechanism_principles` gave the floor teeth at scale: a reliable-source citation
produces **durable** knowledge where a contradicted consensus does not (consensus stick-rate 0.0,
reliable_source 1.0 in the first watched session's overturn scenario). Warrant differs by
resolution mechanism, and the game *measures* that difference rather than assuming it —
*progression, not progress*, made observable.

---

# Part III — the run ledger

## 12 · The eleven runs — the evidence trail

*Each run pre-registered a prior and disposed it; the full pre-registration, totals, and
finding-by-finding disposal live in the linked `runs/RUN_N_LOG.md` (this document carries the
synthesis in Part II, not a second copy). Runs 1–10 are executed and disposed; run 11 is built and
awaiting the author's launch. Note the section-vs-run offset in earlier drafts is gone — the runs
are simply 1–11.*

**The design memos that used to sit among these appendices have moved into the design proper:** the
docket of doubts (content-directed probing) is now Part I §4 (item 5); the atom-level decay rulebook and
the round-compute fixes are Part I §10 + Part II §11.1–11.2; the docket-gate re-examination (which
named *content-undirected probing* as the operative bottleneck by elimination across runs 1–5b)
is recorded in `runs/RUN_5_LOG.md`. What remains here is the chronological record and the findings
index.

| # | Membrane / source | The one variable (vs the prior run) | Status | Headline | Log |
|---|---|---|---|---|---|
| 1 | Wikidata rotating crawl | first live run — the passive baseline | disposed | F2¹ a relinquishment bites only if its target still stands; F3¹ the crawl samples the *settled surface* (≈1 contested / 432) | [RUN_1](../runs/RUN_1_LOG.md) |
| 2 | Wikidata `recentchanges` stream | crawl → recency change-stream (revisit-via-recency) | disposed | F2′ ingestion alone can't test durability — only *directed re-engagement* can; stream is reliable-source-heavy | [RUN_2](../runs/RUN_2_LOG.md) |
| 3 | Wikidata crawl **+ tropism** | add the warm-set re-poll (directed re-engagement) | disposed | **F1″** decay bounds the *vocabulary*, not the sheet (warm names let atoms pile up); F2″ the durability event = **revisit × world-motion** | [RUN_3](../runs/RUN_3_LOG.md) |
| 4 | Wikidata stream **+ tropism** | compose stream × tropism (the 2×2 closer) | disposed | F1⁴ mandated **atom-level decay**; F2⁴ named **round-compute** as the new super-linear wall | [RUN_4](../runs/RUN_4_LOG.md) |
| 5 | Wikidata stream + tropism, **14 h unattended** (decay + compute fixes in) | duration (the cheapest lever) | disposed | **P1⁵ null** — 0 rank transitions in 14 h (a measured rate ceiling); 100 % `new_fact`, final M carries **zero laws** | [RUN_5](../runs/RUN_5_LOG.md) |
| 6 | Wikidata stream + tropism **+ docket** | arm content-directed asks (`query_docket`) | run (launch-delegated) | second rate-ceiling sample; docket resolved-wants + `inexpressible` sizing the Q2 tier | [RUN_6](../runs/RUN_6_LOG.md) |
| 7 | **NWS weather** resolving membrane | swap membrane *class*: Wikidata → weather (seeded naive laws) | disposed | **F2⁷** predict→refute→**silence** (both laws fell, no replacement); discretization = the falsifiability knob | [RUN_7](../runs/RUN_7_LOG.md) |
| 8 | NWS weather **+ re-generalization** | add predict→refute→**re-generalize** (`--regenerate`) | disposed | live calibration payoff (net +17, acc 0.70); **F2⁸** positive-net **limit cycle**; F3⁸ precip dormant; F1⁸ ERA-crash fix | [RUN_8](../runs/RUN_8_LOG.md) |
| 9 | NWS weather, **forecast-centered bins** + per-arm counters | centre the temperature bin on the forecast | disposed | **F1⁹** centred bins convert the cycle → fixed point (F2⁸ was grid-edge-fragility); F2⁹ precip raised **zero** (disposes F3⁸); F3⁹ console tee | [RUN_9](../runs/RUN_9_LOG.md) |
| 10 | NWS weather, **live precip arm** (wet stations, low gate) | activate the non-binned precip control | disposed | **F1¹⁰** the *knob-type*, not binning, gates recovery (calibration vs selectivity); P2¹⁰ a third outcome; **F2¹⁰** the cycle decomposes | [RUN_10](../runs/RUN_10_LOG.md) |
| 11 | NWS weather, **calibrated precip arm** | `--precip-mode calibrated` (two-direction cutpoint bet) | disposed | **F1¹¹** F1¹⁰ CONFIRMED — the calibrated arm recovers to **net +58 / acc 0.983** over 60 resolutions (the run-10 gate arm: −5 / 0.14 over 9); **F3¹¹** the cut settles at 70, not the cap (a calibration knob's digest signature vs the gate's ratchet) | [RUN_11](../runs/RUN_11_LOG.md) |
| 12 | **Sports outcomes** (MLB, discrete resolving membrane) | swap domain class: continuous→**discrete** (no natural width knob); four arms — A no-knob null · B manufactured cut on win-pct differential · C **rival theories over the same claims, `select_best` live** (first time) · D optional induction-from-blank | **built 2026-07-12; launch pending** (`sports_source` / `sports_recalibration` / `run_live_sports`; 32 offline tests incl. the P1¹²/P2¹² causal pair; play resumes 07-16) | P2¹² (headline) — does a *manufactured* calibration knob recover in a domain that donates no width? Is the knob-type law the game's or the weather's? + P4¹² the first external-literature check (home advantage ≈53–54 %) | [RUN_12](../runs/RUN_12_LOG.md) |

### Findings index — what each established, and where it now lives

| finding | run | what it established | now lives in / disposed by |
|---|---|---|---|
| F2¹ · F3¹ | 1 | a relinquishment bites only while its target stands; the crawl samples the settled surface (little contestation) | → mandated the change-stream (run 2) |
| F2′ | 2 | ingestion ≠ a durability test; only *directed re-engagement* revisits | → mandated the tropism (run 3) |
| **F1″** | 3 | disuse-decay bounds the **vocabulary**, not the sheet — the atom is the habit, not the name | **Part II §11.2** (the atom-level rulebook) |
| F2″ | 3 | the durability event = **revisit × world-motion** (revisit necessary, not sufficient) | `RUN_3_LOG.md`; base rate under the 1-h horizon |
| F1⁴ · F2⁴ | 4 | mandated atom-level decay + named **round-compute** as the wall | **§11.1–11.2**, Part I §10 (exact fixes) |
| P1⁵ | 5 | a **measured rate ceiling** — 0 rank transitions / 14 h; Wikidata's inductive register idle | → the single-source check → weather (**§11.6**) |
| **F2⁷** | 7 | predict → refute → **silence** is the failure mode of a raise-and-resolve membrane | **§11.3** (re-generalization is the fix) |
| **F2⁸** | 8 | a re-generalized law settles into a **positive-net limit cycle** | **§11.5** |
| F3⁸ · F1⁸ | 8 | precip arm dormant; a `retract_subgraph` ERA-crash found + fixed (structural) | F3⁸ disposed by F2⁹; F1⁸ in `model_revision` |
| **F1⁹** | 9 | forecast-centred bins convert the cycle → a **fixed point** (F2⁸ was largely a grid artifact) | **§11.5**; disposes F2⁸ (partly) & F3⁸ |
| **F1¹⁰** | 10 | the **knob-type** (calibration vs selectivity), not binning, gates recovery | **§11.4** |
| **F2¹⁰** | 10 | the F2⁸ cycle **decomposes** (grid-edge-fragility + genuine domain-noise) | **§11.5**; tempers F1⁹ |
| **F1¹¹** | 11 | a calibration knob DOES recover the precip arm (net +58 / acc 0.983 vs the gate's −5 / 0.14) — the knob-type law twice-evidenced | **§11.4** confirmed; detail `RUN_11_LOG.md`. Next test: run 12 = sports (discrete outcomes — is the law the game's or the weather's?) |
