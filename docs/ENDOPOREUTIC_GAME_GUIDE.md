# The Endoporeutic Game: Reference Guide

**Date**: 2026-03-28 · **Reviewed**: 2026-06-08 · **Reorganized**: 2026-06-08

This guide is organized in four parts, from machinery to meaning to practice:

- **Part I · The Game** — how it works: the two formal layers, the mechanics of
  play, and the constructive (proof-mode) counterpart.
- **Part II · Outcomes and Interpretation** — what the game produces: the outcome
  taxonomy, the [*Agonothetes*](GLOSSARY.md#agonothetes) (the interpretive function that makes meaning of a
  result), and where the domain model M comes from.
- **Part III · The Philosophy of Inquiry** — why it matters: the Peircean account
  of doubt, situated meaning, and fallibilism that the game formalizes.
- **Part IV · Practice and Reference** — strategy heuristics, worked scripts, the
  implementation, and the literature.

For a non-technical, narrative on-ramp — six everyday scenarios (a vet, a
birdwatcher, a gardener, a town planner, a class, a research group) that show the
same cycle without the formalism — read
[ARISBE_IN_PRACTICE.md](ARISBE_IN_PRACTICE.md) first; each scenario there is a
concrete instance of an outcome in Part II's taxonomy (the mapping is given there).

---

## Implemented today (Agon V1) vs the Frontier

The [Endoporeutic](GLOSSARY.md#endoporeutic) (reading a graph from the outside in) Game is Arisbe's **end game** — the part of the arc that is
deliberately *not finished*. This guide describes the full framework; most of
it is theory and design-ahead. To keep the reader honest about what is wired
today, here is the split. Banners further down mark design-only material in
place.

**Built today — Agon V1 (shipped 2026-06-01):**

- The game engine `src/endoporeutic_game.py` — `GameState`, turn alternation,
  `apply_move`, `legal_areas`, win/`concede` detection, polarity-constrained
  legality.
- The six Dau rules (Beta-aware) via `formal_transformation_rules.py` and the
  headless `rule_interaction.py` protocol.
- The **Agon arena** at `/agon` (`web_api/routes/agon.py` +
  `web_viewer/agon.html`) — interactive **hot-seat** play (one user drives both
  roles); the engine enforces each role's territory.
- The post-game **open disposition taxonomy** (`web_api/services/agonothetes.py`):
  nothing auto-asserts — the user, *as Agonothetes*, chooses the outcome's
  meaning, and only an asserting disposition writes to the corpus.
- §3.3 correspondence attestation on every framed graph before play.
- 16 exemplar scenarios in `tests/test_epg_exemplar_scripts.py`.

**Built since (2026-06-11):** the inner **semantic game** is now a first-class API
(`src/semantic_game.py`) and is wired into Agon as the **interpretation register** —
the [episode](GLOSSARY.md#episode) *given M, then G* (choose M → [peel](GLOSSARY.md#peel) (reading it from the outside in against the model) G against M → decide). The
*constructive* direction (INS/IT+/DC+) is now located as **making in Ergasterion**,
not an Agon mode: the eliminative peel is the game, additive construction is the
workshop. See [GENERATION_AND_TESTING.md](GENERATION_AND_TESTING.md).

**The Frontier — as first mapped here (2026-06-11). Since then most of it has been built:**

- The **inverse pivot** — "in what domain does G hold?" — **shipped** as
  `/agon/where-it-holds` (ranks candidate M: holds / partial / independent /
  contradicts). See `DOMAIN_ORACLE_AND_M.md` §7.
- An **automated Grapheus** opponent — **shipped** (`src/grapheus.py`, minimax over
  the peel). Beyond it, the game now plays **fully autonomously**: three LLM roles
  (Graphist·doubt / Grapheus·defense / Agonothetes·judge) argue under the
  incorruptible mechanical peel — *the LLM argues, the calculus decides*
  (`src/agon_llm.py`; design of record
  [AUTOMATED_ENDOPOREUTIC_GAME.md](AUTOMATED_ENDOPOREUTIC_GAME.md)).
- A **dynamically-learned model M** — **shipped**: M revises through play
  (`src/model_revision.py`, `src/agon_evolution.py`) and **live external sources**
  feed it (Wikidata — a rotating crawl and the recent-changes stream,
  `src/wikidata_source.py`, run bounded/paced/checkpointed by `src/live_runner.py`).
  **Ontology import** (Web Ontology Language ([OWL](GLOSSARY.md#owl))→CLIF→EGI) is
  also shipped; WordNet/SNOMED remain unwired.
- **Automated doubt detection** and guided **M-revision** — **shipped** as the
  attention brief (the LLM Graphist reads M's thin spots and voices one doubt) plus
  the disposition-driven revision loop, with meta-learning over the game's own
  resolutions (`src/agon_metalearning.py`).
- A **frontend** for the interpretation register — **shipped** (the Agon model
  picker, render-M, and the verdict reading strip).

Still open: the **tropism** module — M's own state directing *which* sources to
re-engage (warm-set re-poll). The two executed live runs (`runs/RUN_1_LOG.md`,
`runs/RUN_2_LOG.md`) found that passive ingestion never revisits, so only directed
re-engagement can test the durability of what the game settles; tropism is mandated
but not yet built. The browser arena itself also remains hot-seat (the autonomous
game runs headless).

---

# Part I · The Game

*How the game works — its two formal layers, the mechanics of play, and the constructive counterpart.*

## Overview

The Endoporeutic Game ([EPG](GLOSSARY.md#epg)) is Peirce's dialogical **interpretation** of
Existential Graphs — a paraphrasing of "unwrapping game" or "outside-in game."
It is not a proof procedure. Proof and interpretation are related but serve
different purposes and follow different procedures. The EPG provides the
interpretive method: given a proposed graph G and a domain model M, the game
determines whether G holds in M by systematically unwrapping G using only the
eliminative rules IT- and DC- until the graph either disappears entirely or
cannot be reduced further.

> "The interpretation of existential graphs is *endoporeutic*, that is, proceeds
> inwardly; so that a nest sucks the meaning from without inwards unto its
> centre, as a sponge absorbs water..."  — Ms 650, pp. 18–19

Two players — the **Graphist** (Proposer) and the **Grapheus** (Skeptic) —
engage in a formal exchange over a proposed graph, given an agreed **Domain
Model** (M). A third function, the **Agonothetes** (ἀγωνοθέτης, "organizer
of the contest"), is the interpretive dimension of the game — the purpose
for which the contest exists and the understanding it produces.

The game is not merely a proof checker. It is a **model of inquiry**: its
outcomes drive the growth, revision, and correction of knowledge within a
Universe of Discourse. Both players reference a model **M** consisting of a
set of individuals **D** and a set of relations **R** over **D**. New graphs
need not originate from M — M develops as the Graphist and Grapheus consider
new graphs and how or whether they fit with M. A model has to start somewhere:
it may be pre-existing or it may begin as an empty sheet (the assertion of a
double negative providing the initial context).

### Prerequisites

| Component | Description |
|-----------|-------------|
| **Domain Model (M)** | An agreed Existential Graph Instance ([EGI](GLOSSARY.md#egi)) on the Sheet of Assertion — the shared knowledge base |
| **Proposal (G)** | The Graphist's "seed" graph — an assertion to be tested |
| **Rules** | IT- (de-iteration) and DC- (double cut elimination) — the two eliminative rules used by the EPG |
| **Agonothetes** | The interpretive function of the game: provides context, validates moves, produces understanding from the outcome |

### Players and Territories

| Player | Also known as | Role | Territory | Rules |
|--------|---------------|------|-----------|-------|
| **Graphist** | Proposer, Utterer, Encoder, Speaker | Defends the proposal | NEGATIVE areas (odd depth) | IT-, DC-; hosts erase-a-negative INS step |
| **Grapheus** | Skeptic, Interpreter, Decoder, Listener | Challenges the proposal | POSITIVE areas (even depth) | IT-, DC-; initiates erase-a-negative |

The EPG uses three canonical operations — IT-, DC-, and a compound move called
**erase-a-negative** — all strictly in the service of unwinding structure.
No arbitrary insertion, no iteration-in to strengthen premises, no erasure of
arbitrary subgraphs. Each operation reduces or simplifies; none adds new
propositional content. One person can play both roles, as when playing oneself
in chess.

### Turn Structure

Players alternate. Each turn consists of exactly one rule application in a legal
area. The game proceeds **endoporeutically** — reading the graph from outside in:

- At **positive** (even-depth) areas: the Skeptic chooses
- At **negative** (odd-depth) areas: the Proposer chooses

This reflects the semantic reading: universal claims (negative contexts) are
defended by the Proposer against *any* challenge; existential claims (positive
contexts) are attacked by the Skeptic who must find a *specific* counterexample.

### The Outside-In Process

In EGs one makes a cut in a place and thereby creates an area of opposite
valence. Given `{ }` and applying +DN produces `{ (()) }`. One makes the
first cut of the DN at level 0 (on the blank SoA) and creates an area at
level 1. One makes the second cut at a place in level 1 (the area created
by the first cut), and creates an area at level 2. In considering the elements
juxtaposed in an area you can effectively ignore the details in nested areas.

The game proceeds by this outside-in reduction:

1. If an outermost part *g* of the contested EG **contains no negations**,
   the Proposer must show a mapping (graph homomorphism) between *g* and
   the objects and relations in M. If *g* maps onto M, the Proposer fixes
   all mapped lines of identity from *g* into the remaining EG and erases
   *g*. This leaves either an empty sheet (Proposer wins) or one or more
   negations (continue below).

2. If the contested EG **contains negations**, the Grapheus can remove
   the cut enclosing any subgraph at the current level — **erasing a
   negative**. This is the core EPG move. The canonical mechanism is:

   a. Enter the negative context (the interior of the cut to be erased).
      By INS — which is always permitted in a negative area — draw a new cut
      around the subgraph inside, producing a double cut `~[ ~[ H ] ]` in
      place of the original `~[ H ]`.
   b. Apply DC- to remove the double cut, leaving H at the current level.

   Net effect: the enclosing cut is gone and H is promoted one level outward,
   changing the polarity of every element inside H. What was in a positive
   context (even depth) is now in a negative context (odd depth), and vice
   versa. This **reverses the roles** of Graphist and Grapheus for the
   subgame that follows within H.

   The reversal is local: as the game continues back outward through the
   surrounding structure, the original role assignments are restored. Role
   switching occurs exactly once per cut traversed; each traversal flips
   the polarity and the players, resolving back to the original orientation
   as the game ascends out of each nested level.

3. If the outermost graph consists of **two or more negations** (a double
   cut or multiple adjacent cuts), the current Skeptic can apply DC- to
   remove a double cut in a single step, bypassing the INS intermediate
   where the two-cut structure is already in place.

These steps gradually reduce the proposed graph either to emptiness (Graphist
wins, G holds in M) or to a residue having no possible mapping in M (Grapheus
wins, G does not hold in M).

### Game Termination

The EPG terminates in exactly one of two ways:

1. **Graph disappears** — every element has been unwound through IT-,
   DC-, and erase-a-negative operations, and each exposed atomic portion
   mapped successfully onto M. The Graphist wins: G holds in M.

2. **Graph cannot be reduced further** — some subgraph remains that none of
   the three EPG operations can eliminate, or an atomic portion fails to map
   onto M. The Grapheus wins: G does not hold in M.

There is no draw in the formal sense: the game either runs to empty or
terminates at an irreducible remainder. Stalemate in the *logical* taxonomy
(§Taxonomy of Game Outcomes) refers to the pragmatic situation where G is
independent of M — neither provable nor refutable — which appears formally as
a failure to map, not as a failure to terminate.

---

## Two Layers of the Game

Before the mechanics of play, one distinction clears up most confusion about the
EPG — including why the Overview above speaks of "two eliminative rules" (IT-,
DC-) while Arisbe ships all six. The EPG unifies **two formalisms** that are
often treated separately, and they answer different questions. Understanding
their relationship is the key to the rest of this guide.

### The Semantic Evaluation Game (Inner Layer)

Pietarinen (2006, Ch. 4–7) formalizes Peirce's endoporeutic interpretation as
a **semantic game** with four rules:

1. **Juxtaposition** — At a positive node (conjunction), the Grapheus chooses
   which conjunct to examine. At a negative node, the Graphist chooses.
2. **Ligatures** — The polarity of a ligature's outermost extremity determines
   who picks an individual from the domain: the Graphist on positive areas
   (existential quantification), the Grapheus on negative areas (universal).
3. **Atomic spot** — When an atomic predicate is reached, its truth-value in
   the model determines the winner: true = Graphist wins, false = Grapheus wins.
4. **Winning strategy** — The graph is true in the model if and only if the
   Graphist has a winning strategy.

This game is **recursive**, **boolean** (true/false), and **always terminates**
(the graph is finite, so the descent bottoms out at atomic spots). It is purely
evaluative — no transformation rules appear. It answers the question: *is this
graph true in this model?*

### The Transformation Game (Strategic Layer)

Dau's six rules — INS, ERA, IT+, IT-, DC+, DC- — constitute a separate
**proof-theoretic** system. Players use these rules to manipulate the graph
structure: the Graphist strengthens and propagates; the Grapheus simplifies
and erases.

The transformation rules are not moves *in* the semantic game; they are the
**strategic reasoning** by which a player constructs or demonstrates a winning
(or losing) position. They answer the question: *can we show that the Graphist
has (or lacks) a winning strategy?*

### The Bridge: IT- as Semantic Mapping

The connection between the two layers is **deiteration (IT-)**. In the
semantic game, reaching an atomic spot and checking its truth-value against
the model is the termination condition. In the transformation game, the
corresponding operation is IT-: if a subgraph at the current level is
identical to something in M at an ancestor level, IT- deiterates it —
removing it as "already accounted for." This is the proof-theoretic way of
saying "this content is true in M."

The Graphist wins when all positive content has been deiterated (mapped to M)
or shown to be structurally tautological. The Grapheus wins when some positive
content cannot be mapped and cannot be resolved.

### The Interpretive Layer (Agonothetes)

The semantic game yields a boolean. The transformation game demonstrates
*why* that boolean holds. But neither layer, alone, produces *understanding*.
The Agonothetes — the interpretive function — takes the boolean result
together with the traversal path and the game transcript and maps them to
the outcome taxonomy (Part II):

```
Semantic game result (true/false)
  + traversal path (which sub-games, which choices)
  + game transcript (which rules, which failures)
  ────────────────────────────────
  → taxonomic outcome (theorem, new fact, revision, ...)
  → disposition (accept, reject, revise M, hold as hypothesis, ...)
  → integration into UoD
```

This is why the Agonothetes is not reducible to either player's perspective:
it operates at a meta-level, interpreting the *significance* of the game's
mechanical result.

### Design Implications

This two-layer structure resolves several architectural concerns:

- **Non-boolean outcomes**: The semantic game IS boolean. The taxonomy of
  outcomes is a higher-level interpretation applied by the Agonothetes after
  the game completes. The boolean result determines the *logical* status;
  the Agonothetes determines what it *means* in context.

- **Termination**: The semantic game always terminates because graphs are
  finite. Pietarinen: "the graphs are finite... the interaction will come to
  a halt in a finite number of steps." The transformation game may involve
  strategic choices about when to stop, but the underlying evaluation is
  guaranteed to bottom out.

- **When to descend**: In the semantic game, descent is immediate — each
  step peels off one layer of the nest. In the transformation game, players
  may prepare before descending (DC+, INS to set up structures). The
  preparation IS the strategic reasoning; the descent IS the evaluation.

- **Beta graphs**: Ligatures introduce quantifier binding. The semantic
  game handles this via rule 2 (who picks the individual from the domain).
  The transformation game handles it via the subgraph closure rules that
  govern which ligature-connected elements can be iterated or deiterated
  together.

---

## The Game as Tree Traversal

The same mechanics, stated formally as a data-structure walk — the framing the
implementation actually uses. The game is, in effect, a **tree traversal** of the
EGI's hierarchical structure. The `HierarchicalIndex` (sheet → cuts → nested cuts
→ ...) defines the tree. The game reads it **outside-in, depth-first**.

At each node in the traversal:

- **The polarity** (even depth = positive, odd depth = negative) determines
  who has initiative
- **The content** (edges and vertices juxtaposed in that area) is what the
  current player must address
- **The children** (nested cuts) are sub-trees to be traversed when reached

### Role Reversal as Descent

"Removing a negation to reverse roles" is not a separate operation and not a
rule application — it is simply **descending one level in the tree**. When the
traversal crosses a cut boundary, the depth increments, the polarity flips,
and the player with initiative changes. That *is* the role reversal.

### Sub-Games

A complicated graph involves **sub-games** as the tree is traversed.
Each sub-game corresponds to a sub-tree rooted at some cut:

- The Agonothetes opens a sub-game when the traversal descends into a cut
- Within the sub-game, the players apply transformation rules in their
  respective territories (polarity-constrained)
- The sub-game resolves to one of the taxonomic outcomes (Part II)
- Control returns to the parent level with the sub-game's result

The Agonothetes tracks the **traversal path** and the **outcome of each
sub-game** until the process unwraps the whole graph.

### The ∀/∃ Alternation

The asymmetry of the game is the ∀/∃ alternation in the game tree:

- **Positive node** (Grapheus has initiative): The content is *asserted*
  (conjunction of juxtaposed elements). The Grapheus can challenge **any**
  element. The Graphist must defend **all** of them.

- **Negative node** (Graphist has initiative): The content is inside a cut
  (negated). The Graphist chooses **which path** to pursue — they select the
  defense most favorable to their position.

The burden lies more heavily on the Graphist than on the Grapheus. The
Graphist must show that *every* part of the graph makes sense with respect
to M. The Grapheus needs only identify a part that does not map directly.

However, a failure to map does not necessarily doom the graph. It means
that the proposed graph does not map *simply* onto M — but the taxonomy
of outcomes (Part II) tells us what this can signify:

- If the unmapped content **internally contradicts** itself, the graph
  is in genuine trouble (Case 5).
- If it **contradicts M**, the game enters the refutation/revision space
  (Cases 2a–2d).
- If it is merely **independent of M**, the failure to map may signal a
  **new fact** (Case 3a), a **new abductive explanation** (Case 3b), an
  **open conjecture** (Case 3c), or a **generalization** that would
  enhance the UoD (Case 8).

The game *sorts* the graph into the appropriate taxonomic category. A
"failure" at a sub-game level is not necessarily a failure of the whole
proposal — it is information about how the proposal relates to M.

### Where M Lives

M resides in the game context (iterated there by the Agonothetes during
setup) so that the deiteration rule (IT-) permits showing content "maps
to M": if a subgraph in the current area is identical to something in M at
an ancestor level, IT- can deiterate it — demonstrating the mapping. The
Graphist wins a sub-game when all positive content has been resolved this
way: everything either maps to M or is structurally tautological.

---

## Proof: The Constructive Method

> **⚠️ Frontier (design-only).** The Agon V1 engine implements the *interpretive*
> game (outside-in unwrapping with IT-/DC-). The *constructive* proof mode
> described in this section — building toward a target with INS/IT+/DC+ — is not
> a separate wired mode today; it is described here as the symmetric design. The
> six rules themselves are implemented (`formal_transformation_rules.py`); what
> is not yet wired is a proof-direction game loop with its own role assignment.

Proof and interpretation share the same six Dau transformation rules and the
same polarity system, but their purposes and procedures are opposite in
direction. The EPG unwraps a graph to test whether it holds in M. Proof
*constructs* a derivation showing that G must follow from M — it builds toward
a target rather than eliminating toward emptiness.

### Purpose

Given a domain model M and a proposed graph G, a **proof** is a finite
sequence of EGIs, each following from the previous by exactly one rule
application, that derives G from M (or derives a tautology from the blank
sheet). The proof demonstrates that G is *necessarily* true whenever M is
true — it cannot be otherwise.

This is a stronger claim than the EPG result. The EPG answers: "Does G hold
in M?" Proof answers: "Must G hold in every model that satisfies M?" Both
questions are important; they are not the same question.

### Rules and Polarity

Proof uses all six Dau transformation rules, partitioned by polarity:

| Operation | Rule | Permitted in |
|-----------|------|-------------|
| Erasure | ERA | Positive areas (even depth) |
| Insertion | INS | Negative areas (odd depth) |
| Iteration | IT+ | Any area → a nested area of same or deeper depth |
| De-iteration | IT- | Any area, removing a copy |
| Double Cut introduction | DC+ | Any area |
| Double Cut elimination | DC- | Any area |

The **constructive rules** — INS, IT+, DC+ — add structure. The **eliminative
rules** — ERA, IT-, DC- — remove structure. Both directions are available
because proof must be able to move in either direction to find a path from the
premises to the conclusion.

### Player Roles in Proof

In a proof-mode game, the polarity-based role assignment reflects the
direction of derivation:

| Player | Territory | Rules |
|--------|-----------|-------|
| **Graphist** | Negative areas (odd depth) | INS, IT+, DC+ |
| **Grapheus** | Positive areas (even depth) | ERA, IT-, DC- |

The Graphist works in negative areas because that is where universal
conditions and antecedents reside — strengthening premises and propagating
information inward. The Grapheus works in positive areas because that is where
existential claims and consequents reside — simplifying structure and exposing
what the Graphist must actually deliver.

DC+ and DC- are available to both players in any area as meaning-preserving
structural operations.

### The Proof Frame and Termination

A proof that G follows from M is typically structured as a demonstration that
`~[ M ~[ G ] ]` reduces to the blank sheet. This reads as ¬(M ∧ ¬G) = M → G.
If the game from this starting position reaches the empty sheet, the proof is
complete: G is a theorem of M.

A proof terminates when:

1. **Success** — the graph reaches the target (empty sheet for a theorem; a
   specific goal graph for a derivation step). The Graphist has a winning
   strategy.
2. **Failure** — no sequence of rule applications can reach the target. The
   Grapheus has a winning strategy — there exists a model satisfying M in
   which G is false.

Unlike the EPG, a proof may require many steps in either direction before
terminating, and the path is not necessarily monotonically simplifying. The
Graphist may introduce structure (DC+, IT+, INS) to set up a later
elimination.

### Relationship to the EPG

The two methods address the same logical territory from opposite directions:

| | EPG (Interpretation) | Proof (Construction) |
|---|---|---|
| **Question** | Does G hold in M? | Must G hold given M? |
| **Direction** | Outside-in elimination | Constructive derivation |
| **Rules** | IT-, DC- only | All six (ERA, INS, IT+, IT-, DC+, DC-) |
| **Termination** | Empty (yes) or stuck (no) | Target reached (yes) or unreachable (no) |
| **Graphist moves** | IT-, DC- in negative areas | INS, IT+, DC+ in negative areas |
| **Grapheus moves** | IT-, DC- in positive areas | ERA, IT-, DC- in positive areas |
| **Result** | Semantic: G holds (or not) in *this* M | Logical: G holds in *every* M satisfying the premises |

The EPG outcome informs whether a proof is worth attempting: if the EPG
returns a win for the Graphist in the given M, there is evidence that a proof
may exist. If the EPG returns a stalemate, G is independent of M and no proof
is possible. The EPG is the interpretive gate; proof is the formal
certification.

---

# Part II · Outcomes and Interpretation

*What the game produces — the outcome taxonomy, the interpretive function that makes meaning of it, and where the model M comes from.*

## Taxonomy of Game Outcomes

### I. Logical Classification

The game *determines* the logical relationship between G and M:

| # | Relationship | Formal | Result |
|---|---|---|---|
| 1 | **G is entailed by M** | M ⊨ G | Graphist wins — G is a **theorem** |
| 2 | **G contradicts M** | M ⊨ ¬G | Grapheus wins — G is **refuted** |
| 3 | **G is independent of M** | M ⊭ G ∧ M ⊭ ¬G | **Stalemate** — neither can force a win |
| 4 | **G is a tautology** | ⊨ G | Graphist wins trivially (M irrelevant) |
| 5 | **G is self-contradictory** | G unsatisfiable | Grapheus wins trivially (M irrelevant) |

### II. Pragmatic Outcomes

Each logical outcome opens different pragmatic paths — this is where the game
drives inquiry rather than merely classifying propositions. The Agonothetes
presides over the post-game negotiation that determines which path is taken.

#### Case 1 — G Proved (Theorem)

- **1a. Registration**: G is added to M as a derived theorem with its proof
  transcript. M grows by **deduction**.
- **1b. Redundancy**: G was already in M (or trivially equivalent). The proof
  is still valuable as an alternative derivation or pedagogical exercise.

#### Case 2 — G Refuted (Contradiction with M)

- **2a. Rejection** (standard): M is authoritative, G is simply wrong. The
  Graphist concedes. The refutation proof is recorded.
- **2b. Challenge to M** (revolutionary): The Graphist has external reasons
  to believe G is correct, meaning something in M is wrong. The refutation
  becomes evidence *against* M. This initiates **M revision** — Peirce's
  "irritation of doubt." Under what conditions might G supplant what
  contradicted it in M?
- **2c. Fork**: Both G and ¬G have defensible grounds. The UoD branches into
  alternative domain models (M₁ with G, M₂ without). The directed acyclic graph ([DAG](GLOSSARY.md#dag)) history
  records both branches.
- **2d. Reductio resource**: The contradiction itself is useful — it establishes
  ¬G as a theorem of M, constraining future reasoning.

#### Case 3 — G Independent (Stalemate)

This is the richest case — it corresponds to **genuinely new knowledge** that M
alone cannot adjudicate:

- **3a. New empirical fact**: G describes an observation. Both players agree to
  assert G into M (INS at the sheet). M grows by **induction**. The Skeptic
  decides whether to accept G into M — the Agonothetes facilitates this decision.
- **3b. Abductive hypothesis**: G *explains* something puzzling in M (unifies
  seemingly unrelated theorems). Tentatively accepted as a hypothesis. Peirce's
  abduction — "the only logical operation which introduces any new idea."
- **3c. Open conjecture**: G is interesting but unverified. Recorded in the UoD
  history as a conjecture, neither asserted nor denied.
- **3d. Definition or convention**: G introduces new terminology or conceptual
  structure. Accepted by mutual agreement, not by proof.
- **3e. Conditional acceptance**: G is accepted under an additional premise P.
  The result P → G is added to M.

#### Case 4 — G is Tautological

Trivially true, adds no information. The proof structure may be pedagogically
valuable. Also serves as a **soundness check** on the game mechanics.

#### Case 5 — G is Self-Contradictory

Trivially false. May signal a **formalization error** rather than a logical
one — the Graphist intended a different graph. The Agonothetes may allow
reformulation.

### III. Composite Cases

Real-world proposals are often complex:

- **Case 6 — Partial overlap**: Parts of G are theorems, parts are independent,
  parts may conflict. The game decomposes G and adjudicates each component.
- **Case 7 — Refinement**: G adds more specific claims consistent with M
  (specialization). Accepted as a strengthening.
- **Case 8 — Generalization**: G proposes a broader principle subsuming existing
  M content. An **inductive leap** — the most characteristically Peircean move.
  (Consider the swan example: observations 1–20 all note white color; at some
  point the Proposer generalizes to "all swans are white." Nothing in M
  contradicts this so the Skeptic allows it — until a black swan appears and
  forces M revision via Case 2b.)

### IV. Connection to Peirce's Three Modes of Inference

| Mode | EPG Outcome | Character |
|------|-------------|-----------|
| **Deduction** | Case 1 (theorem) | G follows necessarily from M |
| **Induction** | Case 3a (new fact) | G is supported by evidence |
| **Abduction** | Case 3b (hypothesis) | G explains something in M |

### V. The Taxonomy in the Practical Scenarios

The six everyday scenarios in [ARISBE_IN_PRACTICE.md](ARISBE_IN_PRACTICE.md) are
not separate examples — each is a concrete play that lands on one of the cases
above. The narrative version drops the formalism; this table is the bridge back
to it:

| Scenario (practice doc) | Outcome | Mode |
|---|---|---|
| 1 · the veterinarian (Biscuit needs temperature regulation) | Case 1 — theorem | Deduction |
| 2 · the birdwatcher (a new species, consistent + independent) | Case 3a — new fact | Induction |
| 3 · the gardener (tomatoes in the shade) | Case 2b — challenge to M / revision | (M-revision) |
| 4 · the town planner (a mixed argument) | Case 6 — partial overlap (theorem + extension + conjecture) | Composite |
| 5 · the zoology course (proposing, testing, revising) | Cases 1, 2b, 3a across episodes | The full cycle |
| 6 · ecology ↔ economics (a bridging argument) | Case 1 — theorem of the *merged* model | Deduction |

A reader who wants the intuition first should read those scenarios, then return
here for the formal account.

---

## The Agonothetes (ἀγωνοθέτης)

### Semiotic Grounding

Peirce's semiotics holds that a sign is irreducibly **triadic**: it consists
of a *representamen* (the sign-vehicle), an *object* (what the sign stands
for), and an *interpretant* (the understanding the sign produces). No dyad
suffices. A representamen without an object is empty form; a representamen
confronting an object without an interpretant is a mark checked against the
world but producing no understanding. The triad is the minimal structure of
meaning.

The Endoporeutic Game recapitulates this triad:

| Sign element | Game function | Role |
|---|---|---|
| **Representamen** | **Graphist** | Produces the sign — the proposed graph, the representation to be tested |
| **Object** | **Grapheus** | The domain, the world-as-known, what the sign is tested against |
| **Interpretant** | **Agonothetes** | The understanding that the contest produces — how the proposal relates to the known |

Without the Agonothetes, the game is formally complete but semiotically
barren: it yields true or false, but no growth of understanding. Without
the Grapheus, the Graphist produces signs that are never tested — unchecked
speculation. Without the Graphist, there is a domain with interpretive
capacity but nothing proposed — knowledge that never grows.

The term **Agonothetes** — literally "organizer of the contest" — comes from
the ancient Greek title for those who organized athletic games, festivals,
and competitions. The agonothetes did not compete; they established the
conditions under which the contest could take place, ensured the rules were
followed, and declared what the outcome meant. In the EPG, the Agonothetes
is not a third *player* but the **telic function** of the game: the purpose
for which the contest exists and the understanding it produces.

Peirce himself did not name this third function in his game — he was working
at the level of formal semantics, where the boolean outcome (true/false) is
the relevant output. But his own semiotic framework demands it. A sign
process that terminates at a dyad is degenerate in Peircean terms. The
Agonothetes names what Peirce left implicit: the interpretant of the
game-as-semiosis.

Note that the user of Arisbe straddles *both* player roles — the same person
proposes (Graphist) and challenges (Grapheus), as when playing chess against
oneself. The Agonothetes is therefore not the user-as-observer but the
**meaning-making function** that the game serves: it is what transforms the
mechanical contest into an act of inquiry.

### What the Agonothetes Does

The Agonothetes manifests in three phases of the game:

**Before the game — providing context:**

Everything happens within one **Universe of Discourse** ([UoD](GLOSSARY.md#uod)), where more
than one domain model may exist. The Graphist and Grapheus agree on a
particular reference model M and a proposed graph G to interpret against it.

The interpretive frame — the structure the game will unwind — is:

```
~[ M  ~[ G ] ]
```

This reads as ¬(M ∧ ¬G) = **M → G**. Constructing this frame may require
proof-mode operations (DC+, IT+, INS) that are outside the EPG procedure
itself; the Agonothetes oversees that construction before the interpretive
game begins. Once the frame is in place, the EPG proceeds using only IT- and
DC- from the outside in.

The game will determine whether G holds in M, contradicts M, is independent
of M, or falls into one of the other taxonomic categories (§Taxonomy of Game
Outcomes).

**During the game — maintaining rigour:**

1. **Move validation**: Every step must conform to Dau's formal definitions
   for EGIs, proper subgraphs, and transformation rules. If a move is
   invalid (incorrect syntax, improper subgraph selection, non-existent
   mapping), the Agonothetes states the reason for invalidity.
2. **Mapping validation**: When the Proposer maps exposed elements to M,
   the Agonothetes validates the mapping. If the Proposer legitimately claims
   a **new entity** not present in M, and the mapping is otherwise valid, the
   Agonothetes prompts for its formal addition to the domain's ontology.
3. **Traversal tracking**: The Agonothetes tracks the path through the tree
   (which areas have been resolved, which sub-games are in progress) and
   records the outcome of each sub-game in the transcript.
4. **Record-keeping**: The official game transcript is maintained via
   `ProofSerializer`, including the traversal path, each sub-game's outcome,
   and the final disposition.

**After the game — producing understanding:**

This is the Agonothetes' most essential function — the one that makes it
the Interpretant. The game has produced a boolean result: the Graphist has
a winning strategy, or the Grapheus does. But what does this *mean* for
the knowledge base? The Agonothetes interprets the result in context:

| Disposition | When | Effect on M |
|-------------|------|-------------|
| **Accepted as Consistent** | G mapped successfully, aligns with M | G added to SoA, expanding UoD |
| **Provisionally Accepted** | G is plausible but requires further evidence | G added with hypothesis marker, pending confirmation or refutation by further evidence |
| **Accepted, Implies M Change** | G is valid but conflicts with existing M | The inconsistency is identified; participants decide whether to revise G, revise M, or hold both as alternatives |
| **Rejected** | G is invalid or inconsistent | G not added to M; optionally saved in a "Rejected Graphs" folio with the reason for rejection |

A sub-graph might include a new fact or a new explanation that throws the
whole into doubt without frankly contradicting M. Or it might contradict M
outright, yet the participants might agree to hold the graph as a hypothesis
or alternative pending confirmation or refutation by further evidence. The
taxonomy of outcomes (Part II) covers these possibilities; the Agonothetes
is the function by which the game result is interpreted and acted upon.

The replay function (side-by-side or step-by-step) allows participants to
review the sequence of transformations, both for successful derivations and
for instances of illustrative errors.

---

## The Three Roles: Situational and Functional Definitions

The semiotic grounding (above) establishes *what* the three roles correspond
to in Peirce's sign-triad.  This section asks the complementary questions:
*where* does each role sit within the Universe of Discourse as a diachronic
process, and *what* does each role do — not just mechanically but as a
function of inquiry?

### Situational Definitions

The UoD architecture document establishes that the fundamental entity in
Arisbe is not a static graph but the **diachronic process** of evolving
logical discourse — the film, not the photograph.  Within this process, the
three game roles occupy distinct temporal positions:

**Grapheus — the past.**  The Grapheus is the domain model M: everything
that has been established through prior inquiry, every Agonothetes judgment
that has been rendered and accepted, every fact imported and every theorem
proved.  M is the *sediment* of previous understanding.  It is not passive
— it actively resists proposals that contradict it, and it actively supports
proposals that align with it — but it is, by the time any particular game
begins, already settled.  In the UoD's diachronic process, the Grapheus is
what *was*: the world-as-already-known.

**Graphist — the present.**  The Graphist is the active moment of inquiry:
the point at which something new is introduced into the discourse.  The
Graphist exists at the boundary between the known and the not-yet-known.
Every proposal G is an act of semiosis — the creation of a sign that may or
may not find its object in M.  In the UoD's diachronic process, the Graphist
is what *is happening*: the inquiry in progress, the hypothesis ventured,
the claim put forward.

**Agonothetes — the future.**  Not in a predictive sense, but in a telic
one: the Agonothetes is what the game is *for*.  It is the understanding
that the process aims to produce.  Each Agonothetes judgment, once rendered,
becomes part of M (the Grapheus) for subsequent inquiry.  The Agonothetes is
therefore the pivot between one cycle of inquiry and the next — the point
at which the diachronic process turns.  In the UoD's diachronic process, the
Agonothetes is what *comes to be*: the growth of understanding that feeds
forward into the next round.

This temporal mapping is not metaphorical.  It corresponds directly to the
UoD's architecture:

| Role | Temporal position | UoD component | Peirce's categories |
|------|-------------------|---------------|---------------------|
| Grapheus | Past | Transformation history + current M | Secondness — brute resistance of fact |
| Graphist | Present | The in-forming event (new proposal) | Firstness — quality of possibility |
| Agonothetes | Future | The next state of M (after judgment) | Thirdness — mediation, law, habit |

### Functional Definitions

**Graphist — the assertive function.**

The Graphist embodies the *creative* dimension of inquiry: the capacity to
produce new signs, to propose what has not yet been tested.  Functionally:

- Constructs representations (graphs) — translating intuitions, observations,
  or hypotheses into formal structure (before the game; proof-mode operations)
- Defends the unwinding — operates in negative areas, choosing which IT-
  or DC- moves to apply at each negative-context step; also the territory
  within which the erase-a-negative INS step is executed (the Grapheus
  enters this territory to draw the enclosing cut, then DC- completes the
  erasure from the outside)
- Bears the burden of *completeness* — must show that every exposed atomic
  portion of G maps onto M; a single unmapped element means the game fails
- Embodies the assertive function: *putting claims forward* so they can be
  tested

Without the Graphist, the UoD is a closed archive — knowledge that never
grows, a Grapheus with nothing to test.

**Grapheus — the critical function.**

The Grapheus embodies the *constraining* dimension of inquiry: the resistance
of reality-as-known to unchecked assertion.  Functionally:

- Tests signs against the domain — M is not an inert database but an active
  participant whose structure determines what follows and what does not
- Challenges proposals — operates in positive areas, choosing which IT-,
  DC-, or erase-a-negative moves to apply; the erase-a-negative move
  temporarily enters a negative context (using INS to create a double cut)
  before DC- completes the erasure — this is the canonical implementation
  of role switching across a cut boundary
- Bears the burden of *specificity* — needs only one failure, one unmapped
  element, to block the Graphist's claim
- Embodies the critical function: *checking, constraining, pruning* so that
  only warranted assertions survive

Without the Grapheus, the UoD is unchecked speculation — a Graphist producing
signs that are never tested, assertion without resistance.

**Agonothetes — the interpretive function.**

The Agonothetes embodies the *telic* dimension of inquiry: the purpose for
which the contest exists.  Functionally:

- Before the game: establishes the conditions of inquiry — what M is, what G
  is, how the game space is structured (DC+, IT+, INS)
- During the game: maintains rigour — validates moves, tracks traversal,
  records the transcript
- After the game: produces understanding — interprets the boolean result
  together with the traversal path and transcript, maps them to the outcome
  taxonomy, facilitates the disposition that integrates the result into M
- Embodies the interpretive function: *making meaning* from the mechanical
  contest, transforming a formal result into an act of understanding

Without the Agonothetes, the game yields true or false but no growth of
understanding — a contest with a winner but no significance.

### The Cycle

The three functions form a cycle that is the engine of inquiry:

```
  Grapheus (past)           Graphist (present)
       M ──────────────────────── G
       │                          │
       │    Endoporeutic Game     │
       │    (the contest)         │
       │                          │
       └──────── Agonothetes ─────┘
                 (future)
                    │
                    ▼
              M' = M + judgment
              (new Grapheus for
               the next game)
```

Each Agonothetes judgment enriches or revises M, producing M' — which
becomes the Grapheus for the next inquiry.  The UoD's diachronic process
*is* this iteration: the repeated application of the Graphist–Grapheus–
Agonothetes cycle, each round building on the last.

---

## Bootstrapping M: From Scratch and From Import

The cycle diagram (§The Cycle) raises an immediate practical question: where
does M come from in the first place?  There are two fundamental pathways,
and each illuminates something different about the framework.

### From Scratch: Emergence from the Empty Sheet

Can one imagine this starting from nothing — like Conway's Game of Life —
and watching it grow?

Yes.  Start with **M = the empty sheet**: no facts, no implications, no
structure.  The first game is trivial:

1. The Graphist proposes G₁ (say, "Birds fly").
2. The Grapheus has nothing — M is empty.  There is nothing for IT- to map
   to, nothing for the Grapheus to challenge.  The game is an immediate
   stalemate.
3. The Agonothetes interprets: G₁ is independent of M (Case 3a — new fact).
   Disposition: accept as empirical assertion, pending future evidence.
4. M₁ = {G₁}.

The second game is slightly richer:

1. The Graphist proposes G₂ ("Penguins are birds").
2. M₁ contains "Birds fly."  G₂ is independent — it says nothing about
   flying.  Stalemate again, but this time the Agonothetes can observe that
   G₂ is *related* to M₁ (it shares the concept "bird"), even though M₁
   does not entail it.
3. M₂ = {G₁, G₂}.

The third game:

1. The Graphist proposes G₃ ("Penguins fly").
2. Now M₂ contains "Birds fly" and "Penguins are birds."  Via IT+ and IT-
   inside a `~[ M ~[ G₃ ] ]` structure, the Graphist can derive: Penguins
   are birds → birds fly → penguins fly.  G₃ is a **theorem** (Case 1a).
3. M₃ = M₂ (no new content; G₃ was already entailed).

The fourth game:

1. The Graphist proposes G₄ ("Penguins do not fly").
2. G₄ contradicts G₃ (which is derivable from M₃).  The Grapheus wins.
3. The Agonothetes interprets: **contradiction** — but a productive one.
   The conflict is between the general rule "birds fly" and the specific
   case "penguins do not fly."  This is the Agonothetes at its most
   essential: it must distinguish between rejecting G₄ and revising M.
4. If the participants decide to revise M (adding an exception: "birds fly,
   except penguins"), then M₄ ≠ M₃ — a genuine restructuring.

**The analogy to Conway's Game of Life holds in structure but differs in
agency.**  In GoL, the rules are applied mechanically to initial conditions;
patterns emerge without choice.  In the EPG, the Graphist *chooses* what to
propose and the Agonothetes *interprets* the result.  But the structural
parallel is real:

- **Simple local rules** (the six transformation rules, the polarity-based
  turn system) produce **complex global behavior** (a growing, self-
  correcting knowledge base).
- **Emergence** happens: M develops structure that no single proposal
  contained — implications, chains of inference, exceptions, taxonomies.
- **The richness of the game scales with M**: early games are trivial;
  later games involve deep tree traversals and multi-step proofs.  This
  is the novice-to-expert trajectory viewed diachronically.

The from-scratch pathway is the *pedagogical* mode — ideal for building
understanding of a domain by constructing it piece by piece, seeing each
implication and contradiction as it arises.  Scenario 5 in the practical
exemplars (Amara's zoology course) illustrates this: each lesson adds to M,
and the class's understanding grows through the iterated cycle.

### From Import: External Ontologies as Domain Models

> **Since built.** A model M is **chosen** for a contest (hand-authored facts, or a
> [tomos](GLOSSARY.md#tomos) UoD), **queried** through a `DomainOracle`, and
> **materialized** — facts + Horn rules forward-chain to the least Herbrand model
> (`docs/DOMAIN_ORACLE_AND_M.md` §6.1), which is exactly what a T-box needs to
> become testable. The *automated* OWL→CLIF→EGI import pipeline has also shipped
> (`tools/owl_to_clif.py` + `domain_model_importer.py`), and **Wikidata is live** as
> the first external source — feeding the automated game, not just a one-time import
> ([AUTOMATED_ENDOPOREUTIC_GAME.md](AUTOMATED_ENDOPOREUTIC_GAME.md) §10). WordNet and
> SNOMED remain unwired. (Arisbe's `/import` route admits linear forms at *low
> [warrant](GLOSSARY.md#warrant)* — `docs/MANIFEST_AND_MEANING.md` — distinct from
> this pipeline.)

But one need not start from an empty sheet.  Published ontologies represent
the crystallized results of extensive prior inquiry — someone else's M,
refined over decades.  Importing such an ontology is like transplanting a
mature root system rather than growing from seed.

**What exists to import:**

- **WordNet** — ~117,000 synsets organized by semantic relations (hypernymy,
  meronymy, antonymy).  A lexical Grapheus for natural language reasoning.
- **SNOMED CT** — ~350,000 medical concepts with relationships.  A clinical
  Grapheus for medical reasoning.
- **Gene Ontology** — biological processes, molecular functions, cellular
  components.  A biological Grapheus.
- **Wikidata** — ~100 million items with structured properties.  A general-
  purpose Grapheus.
- **Domain-specific OWL ontologies** — thousands published via BioPortal,
  LOV, and similar registries.

**How import works — the existing infrastructure:**

The key observation is that Arisbe already has production-tested parsers for
standard interchange formats:

```
External ontology (OWL/RDF)
    │
    ▼  (external tooling: OWL → CLIF translation)
CLIF (Common Logic Interchange Format)
    │
    ▼  parse_clif()     ← Arisbe, tested on 35+ examples
EGI (Existential Graph Instance)
    │
    ▼  UoD.promote_to_historical("Imported from WordNet v3.1")
M in a Universe of Discourse
```

Common Logic Interchange Format ([CLIF](GLOSSARY.md#clif)) is an ISO standard (ISO/IEC 24707) for Common Logic, and Sowa's work
explicitly establishes the correspondence between Conceptual Graphs, Common
Logic, and Existential Graphs.  Translation from OWL to CLIF (or a close
approximation) is a studied problem with existing tooling.

**Partial import is natural.**  One need not import all of WordNet or all of
SNOMED.  The Agonothetes' "providing context" function includes *selecting*
what to import — a subtree, a domain slice, a set of relations relevant to
the current inquiry.  This selection is itself an act of inquiry: "which
parts of this external knowledge are relevant to our UoD?"

**The semiotic implications are significant.**  An imported ontology is not
merely data; it is the residue of another triadic process — another
community's iterated Graphist–Grapheus–Agonothetes cycles, crystallized into
a formal structure.  Importing it is a cross-cultural encounter (§Cross-
Cultural Interaction): the external ontology is a Graphist-function (it
proposes claims); our existing M is the Grapheus-function (it tests those
claims); the Agonothetes determines what fits, what conflicts, and what
requires revision.

This means import is not a passive operation.  Each imported assertion
should, in principle, pass through the game — does it align with our
existing M?  Contradict it?  Extend it?  In practice, a bulk import may
accept the external ontology wholesale as a starting M (trusting the source),
with individual claims tested as they become relevant.  This is the
difference between "I accept this textbook" (bulk import) and "Let me check
whether this specific claim holds" (individual game).

### The Two Pathways Converge

The from-scratch pathway and the import pathway are not alternatives but
endpoints of a spectrum:

```
Empty sheet ◄──────────────────────────────► Full ontology import
(pure emergence)                              (bootstrapped M)
     │                                              │
     │  Every assertion passes through the game     │
     │  (slow, pedagogical, deep understanding)     │
     │                                              │
     │         Partial import sits here:            │
     │         some structure inherited,            │
     │         the rest built through inquiry       │
     │                                              │
     ▼                                              ▼
  M grows through iterated cycles              M starts rich,
  (novice trajectory)                          refined through use
                                               (expert trajectory)
```

In both cases, the cycle is the same: Graphist proposes, Grapheus resists,
Agonothetes interprets, M evolves.  The import pathway merely shifts the
starting point further along the novice-to-expert spectrum.

The pedagogical implications are clear:

- **From scratch** is best for learning — building understanding by
  constructing it, seeing each consequence as it emerges.
- **Partial import** is best for applied work — importing established
  knowledge and focusing inquiry on the frontier.
- **Full import** is best for integration — bringing an existing knowledge
  base into Arisbe's formal reasoning environment so it can be tested,
  extended, and combined with other M's.

All three are valid uses of the same triadic engine.

---

# Part III · The Philosophy of Inquiry

*Why the game matters — the Peircean account of inquiry, meaning, and fallibilism that the game formalizes.*

## The Drive of Inquiry: Doubt as Prime Mover

The cycle diagram shows *how* M evolves.  But what makes it turn?  What
drives the Graphist to propose G in the first place?  The bootstrapping
section demonstrates growth *given* proposals — but where do the proposals
come from?

Peirce's answer, in "The Fixation of Belief" (1877), is unequivocal:
**doubt**.  Belief is a settled habit of action — a state in which we know
how to go on.  Doubt is the irritation that disrupts the habit: something
does not fit, something surprises, something resists.  Inquiry is the
struggle to pass from the irritation of doubt to the settlement of belief.
The sole purpose of inquiry is the fixation of belief; the sole cause of
inquiry is the disruption of doubt.

### Sources of Doubt

In the EPG framework, doubt manifests in several distinct ways:

**1. Experience — the world talks back.**

The most fundamental source.  The user observes something that M does not
predict, encounters a case M does not cover, or witnesses an outcome M
says should not happen.  This is *external* to the formal system — it comes
from the user's engagement with the world.  The formal system cannot
generate it; it can only receive it when the user translates the experience
into a proposal G.

In Peircean terms: this is Secondness — the brute resistance of the real,
the dyadic encounter between expectation and fact.  The Grapheus (M)
predicted one thing; the world delivered another.  The gap is doubt.

Example: Dr. Melo's M says cats are obligate carnivores.  Then Biscuit eats
grass.  The experience generates doubt; the doubt motivates the proposal
("Biscuit sometimes eats grass"); the game tests it against M.

**2. Internal inconsistency — M contradicts itself.**

A sufficiently rich M may harbor contradictions that are not immediately
apparent.  Two individually plausible assertions may jointly imply something
false.  This form of doubt is *discoverable through the game itself* — it
emerges when the game traversal encounters a contradiction during a proof
attempt.

In Peircean terms: this is the self-correcting nature of inquiry.  M is
not a static monument but a living structure that can expose its own flaws
when pressed.  The game is the pressing.

Example: M contains "all birds fly" and "penguins are birds."  No
contradiction is visible until someone proposes "penguins do not fly" and the
Agonothetes must confront the conflict.

**3. Encounter with another M — the other talks back.**

Another person, culture, text, or one's own past self presents claims that
conflict with one's current M.  This is the cross-cultural case and the
temporal-self case from the validity checks.  The doubt arises not from the
world directly but from discovering that another coherent perspective
disagrees with one's own.

In Peircean terms: this is the community of inquiry.  No individual M is
privileged; the long-run convergence of inquiry depends on exposure to
alternative perspectives.

Example: importing a medical ontology that models illness differently from
one's own framework.  The disagreement is itself a form of doubt — not "I
am wrong" but "we cannot both be right in the same way."

**4. Formal incompleteness — M has gaps.**

M may be consistent but *incomplete*: there are well-formed questions it
cannot answer.  The game terminates in stalemate (independence), and the
Agonothetes must decide whether the gap matters.  Some gaps are benign
(M has no opinion on matters outside its domain); others are significant
(M should have an answer but does not).

In Peircean terms: this is the abductive moment — the recognition that
something needs explaining, that M is missing a piece.

### The Inversion: Doubt Is the Default

The question "what guarantees doubt?" contains a hidden assumption — that
belief is the natural state and doubt the exception requiring explanation.
Peirce inverts this.  Any finite M in contact with an inexhaustible world
is *necessarily* incomplete and *probably* inconsistent in ways not yet
exposed.  Doubt is not something to be artificially generated; it is the
**natural condition** of any inquirer who has not stopped paying attention.

What needs explaining is not doubt but its temporary absence — the
settlement of belief, the moments when M feels adequate and the cycle
pauses.  The game provides exactly this: when the Graphist cannot find a
proposal that M does not already handle, when no experience contradicts
expectations, when no alternative M creates tension, then the cycle rests.
But it rests *in readiness*, not in finality.  Peirce:

> "The irritation of doubt causes a struggle to attain a state of belief.
> I shall term this struggle *inquiry*." (W 3:247)

The struggle ends when belief is fixed — until the next doubt.

### What This Means for Arisbe

The architectural implication is that the system does not need a mechanism
to *create* doubt.  Doubt comes from the user's engagement with the world,
from the internal tensions of a growing M, and from encounter with external
M's (imported ontologies, other users, literature).  What the system needs
is:

1. **Receptivity** — the ability to accept new proposals at any time
   (the Graphist function is always available).

2. **Honesty** — the game must faithfully report contradictions,
   independence, and failures, not paper over them.  A system that always
   says "consistent" is Peirce's method of tenacity: fixing belief by
   refusing to acknowledge doubt.

3. **Memory** — the UoD's transformation history must preserve the record
   of past doubts and their resolutions, so that the community of inquiry
   (even a community of one across time) can revisit and re-evaluate.

4. **Openness** — the import pathway (§From Import) keeps the system in
   contact with external M's, ensuring that the inquirer is not sealed
   inside their own settled beliefs.

There is, however, one further possibility: **automated doubt detection**.
The system could scan M for formal markers of potential doubt:

- Assertions that are logically independent but semantically related
  (sharing concepts but making no claims about each other — a gap)
- Imported assertions that have not yet been tested against existing M
  (untested imports — latent doubt)
- Long chains of inference whose intermediate steps have never been
  independently verified (fragile derivations)
- Subgraphs that were accepted provisionally but never confirmed

Such a mechanism would not *create* doubt — Peirce is clear that artificial
doubt is sterile — but it would *surface* doubts that are genuinely present
in M's structure but not yet noticed by the user.  This is the system as
a kind of intellectual conscience: not inventing problems but pointing out
the ones that are already there.

### The Fixation of Belief in Arisbe

Peirce distinguishes four methods of fixing belief: tenacity, authority,
the *a priori* method, and the method of science.  Only the last is self-
correcting.  The EPG, if implemented honestly, embodies the method of
science:

- **Tenacity** (holding fast regardless of evidence) is blocked by the
  Grapheus: M resists proposals that contradict it, and the game will
  expose the contradiction.
- **Authority** (accepting belief because an authority dictates it) is
  blocked by the game's transparency: every step is recorded, every
  derivation is inspectable, no assertion is immune from challenge.
- **The *a priori* method** (accepting what seems "agreeable to reason")
  is blocked by the Grapheus's indifference to elegance: M does not care
  whether G is beautiful, only whether it maps.
- **The method of science** (fixing belief by submitting it to something
  independent of what we think about it) is what the game *is*: the
  Graphist proposes, the Grapheus — standing for the world-as-known, not
  for the Graphist's preferences — tests, and the Agonothetes interprets
  honestly.

The guarantee of doubt, then, is not a mechanism within the system but a
condition of its use: that the user remains in contact with the world, with
other inquirers, and with their own evolving experience.  The system's job
is to make the cycle as faithful, transparent, and productive as possible
when doubt arrives — and to not pretend it isn't there when it does.

---

## Situated Meaning: One Sign, Many Games

The preceding sections establish that meaning is produced by the triadic
cycle: the Graphist proposes, the Grapheus resists, the Agonothetes
interprets.  But there is a stronger claim implicit in the framework: **a
single play of the EPG — one "episode" — situates the meaning of every term
it touches in a way that is simultaneously context-dependent and formally
precise.**

Consider the word "cat."

### Six Games, Six Meanings

**1. A Mandarin-speaking person learning English.**

M contains a rich conceptual structure organized around 猫 (māo) — the
Mandarin category for feline animals — plus the learner's general world
knowledge.  The Graphist proposes: "(Cat *x)".  The game tests whether this
English sign maps to anything in M.  IT- finds the mapping: "cat" deiterates
onto 猫.  The Agonothetes produces a *cross-linguistic* Interpretant: "cat"
means what 猫 means, plus whatever English-specific connotations the game
exposes (and minus whatever Mandarin connotations fail to map).

The game does not merely translate.  If M also contains knowledge about
English idiom ("cat got your tongue," "it's raining cats and dogs"), the game
will encounter propositions where "cat" does *not* map to 猫 — stalemates
and contradictions that reveal the boundaries of the cross-linguistic
correspondence.  Each such failure is itself a meaning: the places where
the mapping breaks are as informative as the places where it holds.

**2. A student learning conceptual graphs via "the cat is on the mat."**

M is the formal apparatus of Conceptual Graph theory — type hierarchies,
relation definitions, the syntax of Conceptual Graph Interchange Format ([CGIF](GLOSSARY.md#cgif)).  "Cat" enters the game not as an
animal but as a *type label*: a node in a type lattice, an exemplar concept
used to illustrate the machinery.  The Graphist proposes:
`[Cat: #]→(On)→[Mat: #]`.  The game tests whether this is well-formed
against M (the CG formalism), not whether there is an actual cat on an
actual mat.

The Agonothetes produces a *metalinguistic* Interpretant: "cat" means
"a convenient concept node that illustrates how types, referents, and
relations interact in the formalism."  The feline content is almost
irrelevant; what matters is the formal structure.

**3. A person whose beloved pet cat has just died.**

M is dense with particulars: this cat's name, habits, personality, the years
of companionship, the specific textures of grief.  "Cat" in this M is not a
type but an *individual* — saturated with affect, irreducible to a category.
The Graphist proposes something — perhaps "(Alive *x)" with respect to this
individual — and the game fails.  The Grapheus wins: M no longer supports
the proposition.

The Agonothetes produces an Interpretant shaped by loss.  The meaning of
"cat" here is not a definition but a weight — the significance of what the
sign used to map to and no longer does.  The game's formal machinery
captures this: the failure of IT- (the element no longer maps to M) *is* the
formal expression of absence.

**4. A person whose pet parakeet was eaten by the neighbor's cat.**

M includes: "neighbor's cat killed my parakeet," emotional attachment to the
bird, anger at the cat and perhaps the neighbor.  "Cat" is understood as
predator, threat, instrument of loss.  The Graphist proposes
"(Dangerous *x)" where *x* is bound to Cat.  Against this M, the game
succeeds — IT- maps the proposition to the killing event.

The Agonothetes produces an Interpretant colored by adversarial experience.
"Cat" means something very different here than in case 3, even though both
involve grief and a specific animal.  The difference is entirely in M — the
Grapheus — and therefore entirely in what the game can derive.

**5. A parasitologist studying toxoplasmosis.**

M is the domain of parasitology: *Toxoplasma gondii*, the feline definitive
host, oocyst shedding in cat feces, the parasite's lifecycle, zoonotic
transmission pathways, seroprevalence data.  "Cat" is understood as a
*biological vector* — the only definitive host in which the parasite
completes its sexual reproduction cycle.

The Graphist proposes: "(DefinitiveHost Cat Toxoplasma)".  The game
succeeds — M contains exactly this relationship, and IT- maps it cleanly.
The Agonothetes produces a *technical* Interpretant: "cat" means "the
organism *Felis catus* in its epidemiological role as *T. gondii* definitive
host."  No affect, no companionship, no threat — pure functional
classification.

**6. Us, using "cat" as an example to define and describe the EPG.**

M is the EPG framework itself — the sections above, the triadic structure,
the game mechanics.  "Cat" enters as a *pedagogical device*: a familiar
concept used to illustrate how meaning is situated by the game.  The
Graphist proposes: "the word 'cat' demonstrates situated meaning."  The game
tests this against M (the EPG formalism).

The Agonothetes produces a *reflexive* Interpretant: "cat" means "a
convenient example that shows how the same sign-vehicle produces different
Interpretants depending on M."  The meaning of "cat" in this game is
*about meaning itself* — a meta-level use that the framework accommodates
without special machinery.

### What the Six Games Show

The sign-vehicle is identical in every case: "cat," three letters, one
syllable.  What changes is **M** — the Grapheus, the domain against which
the sign is tested.  And because M changes, everything downstream changes:

- The **game tree** differs: different depths, different branches, different
  points where IT- succeeds or fails.
- The **Agonothetes judgment** differs: theorem, new fact, contradiction,
  stalemate — each M produces its own outcome.
- The **Interpretant** differs: cross-linguistic mapping, formal type label,
  weight of grief, predatory threat, epidemiological function, reflexive
  meta-example.

Yet each meaning is **formally precise** within its game.  The parasitologist's
"cat" is not vague; it is exactly what M (the parasitology domain) entails
under the game's rules.  The bereaved owner's "cat" is not vague; it is
exactly what M (the personal history with this animal) entails and fails to
entail.  The precision is not reduced by the context-dependence; it is
*produced* by it.

### The Pragmatic Maxim

This is Peirce's **pragmatic maxim** made operational:

> "Consider what effects, that might conceivably have practical bearings,
> we conceive the object of our conception to have.  Then, our conception
> of these effects is the whole of our conception of the object."
> (W 3:266)

Each play of the EPG reveals *some* of the practical effects of "cat" —
the ones that are relevant to the particular M and the particular inquiry.
The parasitologist's game reveals the epidemiological effects.  The
bereaved owner's game reveals the effects of absence.  The student's game
reveals the formal-structural effects.

No single game captures the *whole* meaning of "cat" — that would require
playing the game against every possible M, which is Peirce's ideal limit.
But each game captures a **legitimate, precise, situated** portion of the
meaning.

Peirce would say that the totality of games that *could* be played — across
all possible M's, all possible inquirers, all possible times — converges on
what he calls the **final interpretant**: the meaning the sign would have at
the ideal end of inquiry.  But does it?

### Against Convergence: Inquiry Changes the World

The final interpretant, as Peirce conceived it, assumes that inquiry
asymptotically approaches a fixed reality — that there is a stable target
toward which the community of inquiry converges given sufficient time and
honesty.  This is structurally identical to Teilhard de Chardin's **Omega
Point**: the idea that evolution converges on an ultimate state of
consciousness.  Both posit a teleological attractor: a fixed point toward
which the process tends.

The difficulty is this: **our interpretations change the reality in which
we make them and that supports the very effort of interpretation.**

The parasitologist's game does not merely *discover* that cats are
*T. gondii* definitive hosts; it produces knowledge that leads to public
health interventions, vaccination research, altered animal husbandry
practices — all of which change the epidemiological reality that the next
parasitologist's M must model.  The bereaved owner's game does not merely
register grief; the understanding produced changes how that person relates
to animals, to loss, to future companionship — altering the M against which
the next "cat" game will be played.

At every scale, interpretation feeds back into reality:

- A **scientific community** interprets evidence → publishes findings →
  changes research priorities → changes what evidence is gathered → changes
  the world it is studying (new drugs, new technologies, new environmental
  pressures).
- A **culture** interprets its situation → develops practices → transforms
  its environment → must now interpret the transformed environment.
- An **individual** interprets experience → forms beliefs → acts on them →
  encounters a world shaped by those actions.

The target moves because the inquirer is *in* the world, not observing it
from outside.  Every Agonothetes judgment that enriches M also enriches (or
disturbs) the reality that M models.  M' is not a better approximation of a
fixed world; M' is an adequate-for-now model of a world that M' itself has
helped to change.

### Stability and Transformation

This is not chaos.  There is genuine stability — without it, no game could
be played, no M could be relied upon, no IT- could succeed.  The
transformation rules work because the formal structure is stable: the six
rules, the polarity system, the cut semantics.  The biological world is
stable enough that "cats are definitive hosts" remains true across many
games.  The laws of physics are stable enough to ground engineering.

But the stability that enables transformation is itself subject to
transformation.  This is the mechanism of **evolution** — biological,
cultural, conceptual:

1. A certain stability of underlying function enables inquiry
   (M is settled enough to support a game).
2. The game produces a transformation — a new understanding, a new
   practice, a new intervention (the Agonothetes judgment feeds back).
3. That transformation alters the stability — the world is now different
   in some respect, perhaps subtly, perhaps profoundly.
4. The altered world presents new doubts, new experiences, new proposals
   (the cycle turns again, but on different ground).

We have no reason to believe that, upon sufficient reflection and
interaction, any part of the stability of the world is immune from
transformation.  The "laws" of physics are stable across human timescales
but may not be fundamental.  The biological categories ("cat," "bird,"
"parasite") are stable across ecological timescales but shift across
evolutionary ones.  Even formal systems — M itself — evolve as the concepts
and relations within them are revised through inquiry.

### What Replaces the Final Interpretant?

If there is no fixed point of convergence, what does the EPG aim at?

Not *truth as correspondence to a static reality*, but **adequacy for the
ongoing inquiry** — belief that is warranted *now*, that enables action
*now*, that is held *in readiness for revision* when the next doubt arrives.
This is closer to Peirce's own **fallibilism** than the final interpretant
is:

> "Do not block the way of inquiry." (CP 1.135)

The final interpretant blocks the way of inquiry by implying that inquiry
has an endpoint — even an ideal one.  Fallibilism, taken seriously, says:
there is no endpoint.  There is only the next game, played on ground that
the last game helped to shape.

What the EPG provides is not convergence but **accountability**: every move
is recorded, every derivation is inspectable, every judgment is situated in
a specific M and a specific inquiry.  When the ground shifts — when new
experience, new encounters, or the consequences of our own actions create
new doubts — the record is there.  The UoD's transformation history is not
a path converging on truth; it is a **trail through an evolving landscape**,
honest about where it has been and open about where it might go next.

### The Pragmatic Corrective

This position — adequacy without finality, knowledge without omniscience —
provides a useful corrective to two pathologies of thought that recur
whenever inquiry confronts its own limits.

**The pathology of cynicism: "You never really know anything."**

This is the nihilistic misreading of fallibilism.  If no M is final, if
every belief is subject to revision, if the ground itself shifts — then
(the argument goes) nothing is genuinely known.  All knowledge is merely
provisional, merely approximate, merely contingent.  The word "merely" does
all the damage.

The EPG answers: M is real.  The games we have played have produced genuine
understanding — theorems derived, contradictions exposed, predictions
confirmed, practices refined.  The parasitologist's M enables real public
health interventions.  The engineer's M enables real bridges.  The
bereaved owner's M enables real grief and real healing.  That M may be
revised tomorrow does not mean it is worthless today.  A map that is
adequate for the current journey is not defective because the landscape may
change.  The cynical move — discounting all knowledge because no knowledge
is absolute — confuses *revisability* with *unreliability*.  They are not
the same.

In EPG terms: the Graphist's proposals succeed or fail against a real
Grapheus.  IT- maps or it does not.  The game's honesty is not diminished
by the fact that M will evolve.  What was proved in this game was genuinely
proved, given this M, using these rules, recorded in this transcript.

**The pathology of absolutism: "This is the one Truth."**

This is the dogmatic response to the desire for certainty.  If fallibilism
is uncomfortable, one can escape the discomfort by declaring some M to be
final — the one true God, the one true philosophy, the one true political
system, the one true leader.  The move is always the same: elevate a
particular M to the status of unquestionable ground, and block inquiry into
that ground itself.

The EPG answers: no M is immune from challenge.  The Grapheus resists
proposals that contradict it, but the Grapheus is itself the product of
prior Agonothetes judgments — each of which was situated, each of which was
adequate-for-then, none of which was final.  To declare an M absolute is to
block the way of inquiry (CP 1.135) — it is Peirce's method of authority
dressed in metaphysical clothing.

In EPG terms: absolutism is the refusal to let the Graphist propose
anything that challenges M.  But the framework's integrity depends on the
Graphist's freedom to propose *anything* — including proposals that
contradict the deepest commitments of M.  The game may reject the proposal
(M may win), but the game must be *played*.  The moment certain propositions
are declared unquestionable, the system ceases to be inquiry and becomes
dogma.

**The middle ground: we know something, but we will never know everything.**

Between the cynic who says knowledge is impossible and the absolutist who
says knowledge is complete, the pragmatic position is simply this: **we do
know something, and we will never know everything.**

- We know something because M is real, the games are honest, and the
  understanding the Agonothetes produces is genuinely adequate for the
  ongoing inquiry.
- We will never know everything because the world is inexhaustible, our
  interpretations change it, and the stability that grounds our knowledge
  is itself subject to transformation.

This is not a compromise or a hedge.  It is the only position consistent
with both the reality of knowledge and the reality of change.  The
relationship between reliability and revision is not antagonistic but
*enabling*:

- **Reliability enables revision** — it does not block it.  You can only
  revise what you have genuinely established; you can only identify a
  contradiction against a background of stable knowledge.  The fear that
  reliable knowledge becomes rigid knowledge — that M, once settled,
  resists all change — mistakes the Grapheus's *resistance* (which is
  essential to the game) for *immovability* (which is not).  M resists
  poorly warranted proposals; it yields to well-demonstrated ones.  That
  is what honesty means.

- **Revision builds new foundations to rely on** — it does not merely
  destroy.  Every successful revision produces M', which is not a gap
  where M used to be but a *new settlement* — richer, better adapted,
  ready to support the next round of inquiry.  The fear that revision
  undermines all foundations — that questioning M leaves nothing to stand
  on — mistakes the *transformation* of the ground for the *removal* of
  the ground.  The ground changes; it does not vanish.

The EPG formalizes this: every game produces genuine results (not "merely"
provisional ones); every result is held in readiness for revision (not
enshrined as absolute).  The transformation history records both the
knowledge gained and the openness to what comes next.

### The Axiomatics as Epistemology

Existential Graphs capture this entire philosophical position — simply,
elegantly, and in three moves.

**The Sheet of Assertion.**  The blank sheet is the axiom.  It asserts the
unspeakable Truth of the world: the totality that is, prior to and
independent of anything we say about it.  The sheet is *true* — not
because we have verified it, but because it is the ground on which
verification becomes possible.  It commits to the world's reality without
claiming to articulate any of its content.  It is the ultimate reliability:
the ground that enables everything that follows.

This is the **stability** of the preceding discussion.  The world is there.
It is real.  It is not our construction.  The sheet says so, silently, by
being blank.

**DC+ — the only initial move.**  On a blank sheet, the only legitimate
transformation is DC+: the introduction of a double cut.  This creates a
negative context enclosed within a positive one:

```
  ┌─────────────────────────────┐
  │  Sheet (positive, true)     │
  │                             │
  │   ╭───────────────────╮     │
  │   │  outer cut (neg)  │     │
  │   │  ╭─────────────╮  │     │
  │   │  │ inner (pos)  │  │     │
  │   │  │             │  │     │
  │   │  ╰─────────────╯  │     │
  │   ╰───────────────────╯     │
  │                             │
  └─────────────────────────────┘
```

DC+ does not assert anything about the world.  It creates **the space in
which assertion becomes possible**.  The double cut is logically
transparent (it contributes nothing to truth value) but epistemologically
decisive: it situates all future speech within a structure that makes that
speech *contestable*.

This is the moment where inquiry begins.  Not with a claim, but with the
creation of a context for claims.

**INS — confined to negative contexts.**  Insertion is permitted only in
negative areas (odd depth).  Everything we can legitimately say about the
world must be said *under negation*.  The outer cut of the double cut
provides exactly this: a negative area in which the Graphist may inscribe
propositions.

What does it mean that our assertions live in negative contexts?  It means
that, formally, the sum of what we assert is *false* — or more precisely,
it is *falsifiable*.  The negative context is the formal expression of
fallibilism.  Nothing [scribed](GLOSSARY.md#scribe) within it is sheltered from challenge.  The
Grapheus (M, the domain, the world-as-known) will test every inscription
through the game, and the game may refute it.

But falsifiable does not mean useless.  The content of the negative
context, tested against M and found adequate, produces genuine
understanding — theorems, new facts, refined models.  The negation does
not destroy the value of what is inscribed; it **guarantees the epistemic
honesty** of the inscription.  What survives the game has earned its place
in M', precisely because it was never sheltered from challenge.

**The structure as a whole.**

```
  Sheet          = The world is real         (stability)
  DC+            = The space for speech      (the opening of inquiry)
  INS in ~[ ]    = What we say is falsifiable (revision is always possible)
  The game       = Testing against M         (reliability through challenge)
  Agonothetes    = Understanding produced    (knowledge, adequate for now)
```

The entire epistemological arc — from the reality of the world, through the
opening of inquiry, through the falsifiability of our claims, through the
testing of those claims, to the understanding that results — is encoded in
the axiomatics of Existential Graphs.  Peirce did not need to argue for
this position philosophically and then build a notation that illustrates it.
The notation *is* the position.  The philosophy is in the mathematics.

The cynic cannot get started: the sheet commits to the reality of the
world before any speech begins.  The absolutist cannot survive: everything
said is said under negation and must face the game.  The pragmatist finds
the entire structure already prepared: reliable ground (the sheet), the
opening of inquiry (DC+), honest speech (INS under negation), rigorous
testing (the game), and genuine understanding (the Agonothetes) — all
within a single, minimal, formally precise framework.

### Unlimited Semiosis, Without a Terminus

Peirce's doctrine of **unlimited semiosis** — the idea that every
Interpretant becomes a new sign capable of generating further Interpretants
— finds its formal expression in the cycle diagram (§The Cycle).  Each
Agonothetes judgment enriches M, producing M'.  But M' is now a richer
Grapheus, capable of producing richer games, capable of producing richer
Interpretants — and, crucially, **situated in a world that M' itself has
helped to change**.

The parasitologist who runs the "cat = definitive host" game and integrates
the result into M now has a richer M against which to test the next
proposition — perhaps about vaccine development, or about the behavioral
effects of *T. gondii* on intermediate hosts.  But the vaccine, once
developed, changes the epidemiological landscape.  The next game is played
on different ground.

Semiosis does not terminate, and it does not converge.  It *turns* — and
each turn is a play of the game, on ground that the previous turns have
shaped.

This is what it means to say the EPG situates meaning in a "more precise,
richer, and functional way."  The precision comes from the formal game
mechanics (IT-, DC-, the transformation rules).  The richness comes from M
(the Grapheus — the accumulated past of the UoD).  The functionality comes
from the Agonothetes (the Interpretant — the understanding that the game
produces and that feeds forward into both the next inquiry and the world
that inquiry inhabits).

The sign "cat" is simple.  The games it can play are inexhaustible — not
because the meaning is infinitely deep, but because the world in which the
sign operates is inexhaustibly responsive to what we make of it.

---

## The Triad Beyond the Game: Speculative Validity Checks

If the triadic framework (Graphist / Grapheus / Agonothetes = Representamen /
Object / Interpretant) is genuinely grounded in Peirce's architectonic, it
should not be limited to the formal game.  It should illuminate sign-processes
wherever they occur.  The following sections explore — speculatively, as rough
validity checks — whether the framework fits other domains of inquiry.

### Quasi-Minds

Peirce held that semiosis does not require biological minds.  Any entity
capable of determining an interpretant — a book, a law, an institution, a
tradition — functions as a **quasi-mind** (CP 4.536).  The sign-process
operates between quasi-minds, not within a single consciousness.

The triadic framework maps directly:

- A **book** communicates.  The author's text is the Graphist-function
  (producing signs).  The reader's existing knowledge is the Grapheus-function
  (the domain against which the text is tested).  The understanding the reader
  produces — which is *not* identical to the author's intention — is the
  Agonothetes-function.  A book read by a novice and the same book read by an
  expert produce different Agonothetes-judgments because the Grapheus differs.

- A **law** operates.  The legislature's enactment is the Graphist-function.
  The facts of a particular case are the Grapheus-function.  The judge's
  interpretation — which may establish precedent, overturn prior readings,
  or identify ambiguity — is the Agonothetes-function.  The law's meaning
  is not fixed at enactment; it grows through the iterated application of
  the triadic cycle across cases.

- A **scientific paper** proposes.  The paper's claims are the Graphist-
  function.  The existing literature and experimental evidence are the
  Grapheus-function.  The community's response — acceptance, replication,
  critique, revision — is the Agonothetes-function.  Peer review is a
  formalized Endoporeutic Game.

The framework fits because it *is* Peirce's sign-triad applied to inquiry.
Quasi-minds are precisely the entities between which the triadic process
operates.  The Endoporeutic Game is a formalization of the process; the
quasi-mind interactions are the process in the wild.

### Simple Understanding and Expert Understanding

Consider the same proposal G tested against two different domain models:
a novice's M_n and an expert's M_e.

**The novice's game:**

- M_n is sparse — few facts, few implications, shallow structure.
- Many proposals are **independent** of M_n (stalemate → new fact).  The
  game terminates quickly because there is little for the Grapheus to
  challenge and little for IT- to map.
- The Agonothetes-function is coarse: the novice can distinguish "yes,"
  "no," and "I don't know" but has few intermediate categories.
- The game tree is shallow and narrow.

**The expert's game:**

- M_e is rich — many facts, deep implication chains, extensive cross-
  references.
- The same proposal G may be a **theorem** (derivable through a long chain
  of IT- and DC- steps), a **refinement** of an existing result, or a subtle
  **contradiction** that the novice's M_n could not detect.
- The Agonothetes-function is nuanced: the expert can distinguish refinement
  from generalization, conditional acceptance from provisional hypothesis,
  a genuine contribution from a rediscovery of known results.
- The game tree is deep and richly branched.

**Learning is the iterated growth of M through successive games.**  The
novice's M_n becomes the expert's M_e through thousands of Agonothetes
judgments, each enriching the Grapheus for the next round.  The expert is
not someone who has a *different* process of understanding but someone whose
Grapheus is deep enough that the Agonothetes can produce fine-grained
distinctions.

This suggests a testable prediction: the quality of understanding scales with
the *richness of M*, not with any special faculty of the inquirer.  An expert
in domain A is a novice in domain B precisely because their M is rich in one
and sparse in the other.

### Cross-Cultural Interaction

When cultures interact, each brings its own M — its own Grapheus, the
accumulated knowledge and conceptual structure of that tradition.  A proposal
from culture A, tested against culture B's M, may produce outcomes that
neither culture anticipated.

**Scenario: complementary domains.**  Culture A has deep knowledge of
navigation; culture B has deep knowledge of agriculture.  A navigational
claim from A tested against B's M produces stalemate (independence) — not
because the claim is wrong but because B's M has no basis to evaluate it.
The Agonothetes-function here is: accept as new fact on A's authority, or
hold as hypothesis pending B's own investigation.  This is Case 3a in the
taxonomy — empirical enlargement.

**Scenario: overlapping but different frameworks.**  Culture A models illness
as imbalance of humors; culture B models illness as microbial infection.
A claim from A ("this patient's illness is caused by excess bile") tested
against B's M produces a **contradiction** — not because A is wrong in all
respects but because the frameworks are structurally incompatible.  The
Agonothetes-function must distinguish:

- Is the contradiction fundamental (the frameworks are irreconcilable)?
- Is it terminological (the same phenomena described in different vocabularies)?
- Is it partial (each framework captures aspects the other misses)?

This is precisely where the taxonomy of outcomes (revision, fork, conditional
acceptance) earns its keep.  The Agonothetes does not simply accept or
reject; it *interprets* the nature of the disagreement and facilitates a
disposition that may involve revising either M, holding both as alternatives,
or constructing a third framework that subsumes both.

Cross-cultural understanding is the case where the Agonothetes must operate
at its most sophisticated — and where a purely boolean game (true/false)
would be most impoverished.

### The Temporal Self

Perhaps the most intimate instance of the triad: the relationship between
a person's past, present, and future understanding.

- **Past self = Grapheus.**  The knowledge base M as it was: the beliefs,
  commitments, and conceptual structures one held at an earlier time.
- **Present self = Graphist.**  The active inquirer, bringing new experience,
  new reading, new encounters to bear on the old M.
- **Agonothetes = the growth of understanding over time.**  The judgment
  that "I used to think X, now I think Y" is an Agonothetes verdict: the
  present Graphist proposed Y, the past Grapheus resisted (M included X),
  and the Agonothetes interpreted the outcome as warranting revision.

This framing illuminates several familiar phenomena:

- **Diary-keeping and journaling** are forms of the Endoporeutic Game played
  across time.  The journal entry is the Graphist's proposal; re-reading it
  years later tests it against a changed M; the insight produced is the
  Agonothetes-function.

- **Education** (as in Scenario 5 of the practical exemplars) is the
  *guided* application of the cycle: the teacher structures the Graphist's
  proposals and scaffolds the Agonothetes-function until the student's M
  is rich enough to sustain the cycle independently.

- **Self-contradiction across time** ("How could I have believed that?") is
  a game in which the present self's enriched M exposes a claim the past
  self held as a theorem but which the present self can refute.  The
  discomfort is the Agonothetes registering a genuine conflict between
  temporal selves.

Peirce himself anticipated this with his notion of the **community of
inquiry** — even a single inquirer participates in this community
diachronically, through the conversation between past, present, and future
selves.  The triadic framework makes this precise: the community of inquiry
is the iterated Graphist–Grapheus–Agonothetes cycle applied across time.

### What These Checks Suggest

The framework appears to fit — not as a loose analogy but as a structural
correspondence.  In every case examined, the three functions (assertive,
critical, interpretive) are present and irreducible.  Removing any one
collapses the process:

- Without the Graphist: no proposals, no growth — a static archive.
- Without the Grapheus: no resistance, no testing — unchecked speculation.
- Without the Agonothetes: no interpretation, no significance — a contest
  with a winner but no understanding.

This structural necessity is exactly what Peirce's semiotic predicts.  The
sign-triad is irreducible because meaning-making is irreducibly triadic.
The Endoporeutic Game is one formalization of this process; the quasi-mind
interactions, the novice-to-expert trajectory, the cross-cultural encounter,
and the temporal self are other instances of the same triadic engine.

These observations remain speculative and would benefit from more rigorous
treatment.  But as rough validity checks, they suggest that the triadic
framework is not an *ad hoc* addition to the game mechanics but a genuine
reflection of the structure of inquiry — which is what we should expect if
Peirce's architectonic is sound.

---

# Part IV · Practice and Reference

*Playing and building — strategy heuristics, worked scripts, the implementation, and the literature.*

## Role-Switching and Strategic Considerations

### Graphist (Proposer) Strategies

The Proposer defends G by operating in negative (odd-depth) areas:

- **INS** (Insertion): Add content to negative areas. This strengthens the
  conditional structure — adding to the antecedent of an implication makes it
  harder for the Skeptic to satisfy.
- **IT+** (Iteration): Copy subgraphs to more deeply enclosed areas. This
  propagates information inward, extending the reach of premises.
- **DC+** (Double Cut Insertion): Introduce `~[ ~[ ... ] ]` around content.
  Meaning-preserving but creates new negative areas for future INS moves.
  A **preparatory** move that expands the Proposer's territory.

**Key insight**: The Proposer's power lies in *strengthening conditions* and
*extending information*. The Proposer cannot erase anything — they can only
add structure and propagate existing content.

### Grapheus (Skeptic) Strategies

The Skeptic attacks G by operating in positive (even-depth) areas:

- **ERA** (Erasure): Remove content from positive areas. This weakens the
  graph — erasing a predicate from the sheet removes an assertion.
- **IT-** (Deiteration): Remove content that could have been produced by
  iteration. This "undoes" the Proposer's propagation moves.
- **DC-** (Double Cut Erasure): Remove `~[ ~[ ... ] ]` pairs. Simplifies
  structure and may expose content for further erasure.

**Key insight**: The Skeptic's power lies in *weakening assertions* and
*simplifying structure*. The Skeptic cannot add anything — they can only
remove and simplify.

### Reasoning across a role reversal

Removing a negation reverses the roles — its mechanism is *The Outside-In
Process* and *Role Reversal as Descent* in Part I. Strategically, this means
both players must reason about
the consequences of a move not just for the current position but for the
position they may find themselves defending *after* a role switch — the former
Skeptic becomes the Proposer who must defend the contrary graph.

### Turn-by-Turn Dynamics

The alternation creates a dialectical rhythm:

1. **Opening**: Graphist may use DC+ to create negative territory for future
   INS moves. Grapheus may use ERA to simplify obvious targets.
2. **Middle game**: IT+ and IT- create a push-pull dynamic — the Proposer
   copies information inward, the Skeptic removes copies.
3. **Endgame**: One player runs out of productive moves and must either
   concede or make neutral (DC+/DC-) moves that don't advance their position.

### When to Concede

A player should concede when:

- They have no moves that improve their position
- Continuing would only allow the opponent to strengthen theirs
- The logical conclusion is clear and further play is pointless

The Agonothetes may suggest concession when the outcome is logically
determined but the players have not yet reached a terminal state.

---

## Exemplar Scripts

See `tests/test_epg_exemplar_scripts.py` for executable implementations
of the following scenarios:

### Simple Outcome Examples

| Script | M (Domain Model) | Proposal G | Outcome | Demonstrates |
|--------|-------------------|------------|---------|--------------|
| **A** | ∀x(Human(x)→Mortal(x)), Human(Socrates) | Mortal(Socrates) | 1a: Theorem | Deductive proof (Barbara) |
| **B** | ∀x(Cat(x)→Mammal(x)), ¬∃(Mammal∧Fish) | ∃x(Cat(x)∧Fish(x)) | 2a: Refuted | Standard refutation |
| **C** | P | ¬P | 2d: Reductio | Contradiction as resource |
| **D** | ∀x(Human(x)→Mortal(x)) | Human(Socrates) | 3a: New fact | Empirical enlargement |
| **E** | Human(Socrates), Mortal(Socrates) | ∀x(Human(x)→Mortal(x)) | 3b: Abduction | Inductive generalization |
| **F** | ∀x(Swan(x)→White(x)) | ∃x(Swan(x)∧Black(x)) | 2b: M revision | Revolutionary challenge |
| **G** | (empty sheet) | P → P | 4: Tautology | Soundness check |
| **H** | P | P∧¬P | 5: Self-contradictory | Formalization error |

### Advanced Strategy Examples

| Script | Scenario | Key Feature |
|--------|----------|-------------|
| **I** | Multi-move deduction with IT+ chain | Proposer propagation strategy |
| **J** | Skeptic simplification via ERA+DC- | Skeptic reduction strategy |
| **K** | Territory expansion via DC+ | Preparatory moves |
| **L** | DC+/DC- push-pull exchange | Dialectical middle game |
| **M** | Concession after exhausting moves | Endgame recognition |
| **N** | Full game engine integration | Turn alternation, legality, goals |

---

## Implementation

### Core Modules

| Module | Purpose |
|--------|---------|
| `endoporeutic_game.py` | Game engine: state, moves, win detection |
| `web_api/routes/agon.py` + `web_viewer/agon.html` | The live **Agon arena** — interactive hot-seat play in the browser (the V1 surface) |
| `web_api/services/agonothetes.py` | The post-game disposition taxonomy |
| `proof_serializer.py` | Save/load proofs as JSON or text |
| `formal_transformation_rules.py` | The six Dau rules (Beta-aware) |
| `rule_interaction.py` | Headless stepwise protocol |
| `agon_evolution.py` / `agon_llm.py` / `live_runner.py` | The **automated** game: the loop that plays it autonomously, the three LLM roles, and bounded live runs against external sources — see [AUTOMATED_ENDOPOREUTIC_GAME.md](AUTOMATED_ENDOPOREUTIC_GAME.md) |

### Starting a Game

```python
from endoporeutic_game import EndoporeuticGame, Player

game = EndoporeuticGame()
state = game.new_game(
    initial_egif="(Human *a) ~[ (Human *b) ~[ (Mortal *c) ] ]",
    goal_egif="(Mortal *x)",
)
```

### Making Moves

```python
# Skeptic erases from positive area (sheet)
state, msg = game.apply_move(state, "ERA", frozenset([edge_id]), sheet_id)

# Proposer inserts into negative area
state, msg = game.apply_move(state, "INS", frozenset(), cut_area_id,
                              insert_egif="(Mortal *x)")

# Either player: double cut
state, msg = game.apply_move(state, "DC+", frozenset(), area_id)
```

### Interactive play (the Agon arena)

Interactive play happens in the browser, not a terminal REPL. Start the web
app and open the Agon arena:

```bash
uv run uvicorn --app-dir src web_api.main:app --reload --port 8000
# then open http://localhost:8000/agon
```

The arena drives the same `EndoporeuticGame` engine shown above over the
`/agon` routes (`new_game` / `apply_move` / `concede` / `legal_areas`), with
hot-seat play (one user drives both roles) and a post-game disposition
selector. *(An earlier `src/game_repl.py` terminal REPL was removed; the engine
API above is the headless entry point if you want to script a game.)* The game
also plays with no one at the keyboard — the autonomous loop in
`src/agon_evolution.py` / `src/agon_llm.py` runs whole campaigns headless
([AUTOMATED_ENDOPOREUTIC_GAME.md](AUTOMATED_ENDOPOREUTIC_GAME.md)).

### Saving and Loading Proofs

```python
from proof_serializer import ProofSerializer

# Save
json_str = ProofSerializer.to_json(state.history)

# Load
history = ProofSerializer.from_json(json_str)

# Human-readable
print(ProofSerializer.to_text(state.history))
```

---

## Theoretical Foundations

### Peirce's Game Semantics

The Endoporeutic Game formalizes Peirce's insight that the *meaning* of a logical
graph is given by the *strategies available to the players*. A graph is **true** if
the Graphist has a winning strategy; **false** if the Grapheus has one; **undetermined**
if neither can force a win.

Peirce also used the term "endogenous" (Ms L 477, 1913) for this inside-out
process. The game models interpretation as proceeding from the outermost context
inward — each nested area "sucks the meaning from without inwards unto its
centre."

This dialogical interpretation makes EG a precursor to:

- **Game-theoretic semantics** (Hintikka, 1973)
- **Dialogical logic** (Lorenz, 1961; Lorenzen & Lorenz, 1978)
- **Linear logic** (Girard, 1987) — resource-sensitive reasoning

### Dau's Formalization

Dau (2006) provides the mathematical foundation in Chapter 21 of
*The Logic System of Concept Graphs with Negations*. The key insight is that
the six transformation rules, constrained by polarity, create a complete
proof system: any semantically valid entailment can be demonstrated through
game play.

### The Pragmatic Turn

What distinguishes the EPG from a standard proof system is its **pragmatic**
character. The post-game negotiation (Part II) connects the formal
game to Peirce's broader theory of inquiry:

- **Belief fixation**: The game outcome fixes or disturbs belief
- **Community of inquiry**: The Agonothetes represents the community's standards
  (the Commens — the community that realizes interpretation)
- **Fallibilism**: Even "proven" results may be revised (case 2b)
- **Growth of knowledge**: Independent proposals (case 3) are the engine of
  discovery — M develops as Graphist and Grapheus consider new graphs
- **Self-correction**: The game is a model of inquiry as a self-correcting
  process within a rational community
