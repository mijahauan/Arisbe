# The Endoporeutic Game: Reference Guide

**Date**: 2026-03-28

---

## Overview

The Endoporeutic Game (EPG) is Peirce's dialogical semantics for Existential
Graphs — a paraphrasing of "unwrapping game" or "outside-in game."

> "The interpretation of existential graphs is *endoporeutic*, that is, proceeds
> inwardly; so that a nest sucks the meaning from without inwards unto its
> centre, as a sponge absorbs water..."  — Ms 650, pp. 18–19

Two players — the **Graphist** (Proposer) and the **Grapheus** (Skeptic) —
engage in a formal exchange over a proposed graph, given an agreed **Domain
Model** (M). A third role, the **Agonothetes** (ἀγωνοθέτης, "organizer of
the contest"), presides over the game, validates moves, and manages the
post-game negotiation that determines how M evolves.

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
| **Domain Model (M)** | An agreed EGI on the Sheet of Assertion — the shared knowledge base |
| **Proposal (G)** | The Graphist's "seed" graph — an assertion to be tested |
| **Rules** | The six Dau transformation rules, polarity-constrained |
| **Agonothetes** | Organizer of the contest: validates moves, oversees outcome negotiation |

### Players and Territories

| Player | Also known as | Role | Territory | Rules |
|--------|---------------|------|-----------|-------|
| **Graphist** | Proposer, Utterer, Encoder, Speaker | Defends the proposal | NEGATIVE areas (odd depth) | INS, IT+, DC+ |
| **Grapheus** | Skeptic, Interpreter, Decoder, Listener | Challenges the proposal | POSITIVE areas (even depth) | ERA, IT-, DC- |

DC+ and DC- are meaning-preserving and available to both players in any area.
One person can play both roles, as when playing oneself in chess.

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

2. If the contested EG **contains negations**, the process removes them
   one-by-one. Removing a single negation changes the valence of nested
   elements and **reverses the roles** of Proposer and Skeptic.

3. If the outermost graph consists of **two or more negations**, the current
   Skeptic can remove all but one of them.

These steps gradually reduce the proposed graph either to emptiness (Proposer
wins, G is true in M) or to a graph having no possible mapping in M (Skeptic
wins, G is false in M).

### Contextualizing a Proposed Graph

The Proposer scribes the contested EG into a context per these rules:

1. `{ }` — Sheet of Assertion (depth 0)
2. `{ (()) }` — Add double cut: outer at depth 1, inner at depth 2
3. `{ ((())) () }` — Add another double cut inside the first (depth 1)
4. `{ (((G))) () }` — Insert G at depth 3 (negative/odd context, per INS rule)
5. `{ (()) () }` — Erase `((G))` from depth 2 (positive/even, per ERA rule)
6. `{ (()) }` — De-iterate the redundant empty cut (per IT- rule)
7. `{ }` — Erase the double cut (per DC- rule)

This demonstrates a valid procedure for introducing G into a specific context
and then removing it, using only the formal transformation rules.

---

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
  alternative domain models (M₁ with G, M₂ without). The DAG history
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

---

## The Agonothetes (ἀγωνοθέτης)

The **Agonothetes** — literally "organizer of the contest" — is the official
who presides over the game. The term comes from the ancient Greek title for
those who organized and judged games, festivals, and competitions. In the
EPG, the Agonothetes is not merely a referee but the **guardian of the
inquiry process** and the central agent for managing the evolution and
integrity of the Sheet of Assertion.

### Game Setup

Everything happens within one **Universe of Discourse** (UoD), where more
than one domain model may exist. The three participants — Graphist, Grapheus,
and Agonothetes — agree on a particular reference DM (M). The Agonothetes
then prepares the game space using the transformation rules themselves:

1. **DC+** — The Agonothetes creates a context (double cut) in which the
   contest takes place. This provides a fresh negative area (depth 1) and
   a positive area (depth 2) nested within.

2. **IT+** — A copy of M (or reference thereto) is iterated into the
   game context. M now resides at depth 1 (negative area) alongside the
   inner cut.

3. **INS** — The Graphist inserts the proposed graph G in a negative
   sub-context within the game area, in effect asserting: *"if or given
   this M, then G follows."*

The resulting structure on the sheet is:

```
~[ M  ~[ G ] ]
```

This reads as ¬(M ∧ ¬G) = **M → G**. The game will determine whether this
implication holds — whether G follows from M, contradicts M, is independent
of M, or falls into one of the other taxonomic categories.

### During the Game

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

### Post-Game Outcome Negotiation

The Agonothetes' most critical function occurs at the conclusion of each
game (or sub-game). Based on the outcome, the Agonothetes presents options
for the proposed graph's fate:

| Disposition | When | Effect on M |
|-------------|------|-------------|
| **Accepted as Consistent** | G mapped successfully, aligns with M | G added to SoA, expanding UoD |
| **Provisionally Accepted** | G is plausible but requires further evidence | G added with hypothesis marker, pending confirmation or refutation by further evidence |
| **Accepted, Implies M Change** | G is valid but conflicts with existing M | Agonothetes flags the inconsistency; participants decide whether to revise G, revise M, or hold both as alternatives |
| **Rejected** | G is invalid or inconsistent | G not added to M; optionally saved in a "Rejected Graphs" folio with the reason for rejection |

A sub-graph might include a new fact or a new explanation that throws the
whole into doubt without frankly contradicting M. Or it might contradict M
outright, yet the three participants might agree to hold the graph as a
hypothesis or alternative pending confirmation or refutation by further
evidence. The taxonomy of outcomes (Section II) covers these possibilities;
the Agonothetes facilitates the decision among them.

### Record-Keeping and Replay

The Agonothetes maintains the official game transcript via `ProofSerializer`.
This includes the traversal path, each sub-game's outcome, and the final
disposition. The replay function (side-by-side or step-by-step) allows
participants to review the sequence of transformations, both for successful
derivations and for instances of illustrative errors.

---

## The Game as Tree Traversal

The game is, in effect, a **tree traversal** of the EGI's hierarchical
structure. The `HierarchicalIndex` (sheet → cuts → nested cuts → ...) defines
the tree. The game reads it **outside-in, depth-first**.

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
- The sub-game resolves to one of the taxonomic outcomes (Section II)
- Control returns to the parent level with the sub-game's result

The Agonothetes tracks the **traversal path** and the **outcome of each
sub-game** until the process unwraps the whole graph.

### The ∀/∃ Alternation

The asymmetry of the game is the ∀/∃ alternation in the game tree:

- **Positive node** (Grapheus has initiative): The content is *asserted*
  (conjunction of juxtaposed elements). The Grapheus can challenge **any**
  element — if any one fails to map to M, the whole conjunction fails.
  The Graphist must defend **all** of them.

- **Negative node** (Graphist has initiative): The content is inside a cut
  (negated). The Graphist chooses **which path** to pursue — they select the
  defense most favorable to their position.

The burden lies more heavily on the Graphist than on the Grapheus. The
Graphist must show that *every* part of the graph makes sense with respect
to M. The Grapheus needs only show that *any one* part fails.

### Where M Lives

M resides in the game context (iterated there by the Agonothetes during
setup) so that the deiteration rule (IT-) permits showing content "maps
to M": if a subgraph in the current area is identical to something in M at
an ancestor level, IT- can deiterate it — demonstrating the mapping. The
Graphist wins a sub-game when all positive content has been resolved this
way: everything either maps to M or is structurally tautological.

---

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

### Role Reversal

A defining feature of the EPG is that **removing a negation reverses the
roles**. When the outermost graph consists of a single negation, the next
step removes it — changing the valence of all nested elements and making the
former Skeptic into the new Proposer, who must now defend the contrary graph.

This means both players must reason about the consequences of their moves
not just for the current position but for the position they may find
themselves defending after a role switch.

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
| `game_repl.py` | Interactive REPL for human play |
| `proof_serializer.py` | Save/load proofs as JSON or text |
| `formal_transformation_rules.py` | The six Dau rules (Beta-aware) |
| `rule_interaction.py` | Headless stepwise protocol |

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

### Interactive REPL

```bash
python src/game_repl.py "~[ (Human *x) ~[ (Mortal x) ] ]" --goal "(Mortal *y)"
```

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
character. The post-game negotiation (Section II above) connects the formal
game to Peirce's broader theory of inquiry:

- **Belief fixation**: The game outcome fixes or disturbs belief
- **Community of inquiry**: The Agonothetes represents the community's standards
  (the Commens — the community that realizes interpretation)
- **Fallibilism**: Even "proven" results may be revised (case 2b)
- **Growth of knowledge**: Independent proposals (case 3) are the engine of
  discovery — M develops as Graphist and Grapheus consider new graphs
- **Self-correction**: The game is a model of inquiry as a self-correcting
  process within a rational community
