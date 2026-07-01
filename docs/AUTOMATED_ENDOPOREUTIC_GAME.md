# The automated Endoporeutic Game: three roles, one incorruptible referee

**Status**: design-of-record · **Stages 1–3 BUILT** (`src/agon_llm.py`, 2026-06-30) — the
LLM **Graphist** (doubt), **Grapheus** (defense), and **Agonothetes** (judge + branch-the-DAG),
all three under the mechanical referee · the **§6 meta-learning instruments**
(`src/agon_metalearning.py`) + **both §4b open membranes** — raise-only
(`src/discourse_membrane.py`) and raise-and-resolve (`src/resolving_membrane.py`) — BUILT ·
aim = **discovery** · **Drafted**: 2026-06-30

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
tests: `tests/test_resolving_membrane.py`. Still ahead: a **live** source behind the
`ResolvingFeed` interface (a prediction-market / sports / weather API), and a mechanical
source-conflict agent so the *raise-only* loop disposes of contested contents without an LLM.

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
  reads `stuck=False`, the "superseded law" surfacing as a low stick-rate). `gaps` flags
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

Demo (no LLM): `tools/build_metalearning_demo.py`. Tests: `tests/test_agon_metalearning.py`.

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
- **The open membranes (§4b, BUILT).** `src/discourse_membrane.py`: `DiscourseFeed` (a
  raise-only, dated, sourced `Proposer`) + `consistency_report` (cross-source coherence); tests
  `tests/test_discourse_membrane.py`. `src/resolving_membrane.py`: `ResolvingFeed` +
  `PredictionLedger` + `select_best` (the raise-and-resolve flavour with world-teeth — M
  forecasts via the peel, is empirically falsified where it over-reaches, and selection ranks
  predictors by track record); demo `tools/build_resolving_membrane_demo.py`, tests
  `tests/test_resolving_membrane.py`.
- **Next.** A **live** raise-and-resolve source behind the `ResolvingFeed` interface (a
  prediction-market / sports / weather API — the first with a real world on the other end); a
  mechanical source-conflict agent (dispose of *raise-only* contested contents without an LLM);
  the runs-as-corpus/test-suite + self-describing-rulebook harvests (§6 futures). Keep the floor:
  *progression, not progress* (§7); nothing auto-promotes to the attested corpus.
