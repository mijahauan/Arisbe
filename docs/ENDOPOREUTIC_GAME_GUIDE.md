# The Endoporeutic Game: Reference Guide

**Date**: 2026-03-28

---

## Overview

The Endoporeutic Game (EPG) is Peirce's dialogical semantics for Existential Graphs.
Two players — the **Graphist** (Proposer) and the **Grapheus** (Skeptic) — engage in a
formal exchange over a proposed graph, given an agreed **Domain Model** (DM).

The game is not merely a proof checker. It is a **model of inquiry**: its outcomes
drive the growth, revision, and correction of knowledge within a Universe of Discourse.

### Prerequisites

| Component | Description |
|-----------|-------------|
| **Domain Model (DM)** | An agreed EGI representing the shared knowledge base |
| **Proposal (G)** | The Graphist's "seed" graph — an assertion to be tested |
| **Rules** | The six Dau transformation rules, polarity-constrained |
| **Umpire** (optional) | Validates moves, oversees post-game negotiation |

### Players and Territories

| Player | Role | Territory | Rules |
|--------|------|-----------|-------|
| **Graphist** (Proposer) | Defends the proposal | NEGATIVE areas (odd depth) | INS, IT+, DC+ |
| **Grapheus** (Skeptic) | Challenges the proposal | POSITIVE areas (even depth) | ERA, IT-, DC- |

DC+ and DC- are meaning-preserving and available to both players in any area.

### Turn Structure

Players alternate. Each turn consists of exactly one rule application in a legal
area. The game proceeds **endoporeutically** — reading the graph from outside in:

- At **positive** (even-depth) areas: the Skeptic chooses
- At **negative** (odd-depth) areas: the Proposer chooses

This reflects the semantic reading: universal claims (negative contexts) are
defended by the Proposer against *any* challenge; existential claims (positive
contexts) are attacked by the Skeptic who must find a *specific* counterexample.

---

## Taxonomy of Game Outcomes

### I. Logical Classification

The game *determines* the logical relationship between G and DM:

| # | Relationship | Formal | Result |
|---|---|---|---|
| 1 | **G is entailed by DM** | DM ⊨ G | Graphist wins — G is a **theorem** |
| 2 | **G contradicts DM** | DM ⊨ ¬G | Grapheus wins — G is **refuted** |
| 3 | **G is independent of DM** | DM ⊭ G ∧ DM ⊭ ¬G | **Stalemate** — neither can force a win |
| 4 | **G is a tautology** | ⊨ G | Graphist wins trivially (DM irrelevant) |
| 5 | **G is self-contradictory** | G unsatisfiable | Grapheus wins trivially (DM irrelevant) |

### II. Pragmatic Outcomes

Each logical outcome opens different pragmatic paths — this is where the game
drives inquiry rather than merely classifying propositions:

#### Case 1 — G Proved (Theorem)

- **1a. Registration**: G is added to DM as a derived theorem with its proof
  transcript. The DM grows by **deduction**.
- **1b. Redundancy**: G was already in DM (or trivially equivalent). The proof
  is still valuable as an alternative derivation or pedagogical exercise.

#### Case 2 — G Refuted (Contradiction with DM)

- **2a. Rejection** (standard): DM is authoritative, G is simply wrong. The
  Graphist concedes. The refutation proof is recorded.
- **2b. Challenge to DM** (revolutionary): The Graphist has external reasons
  to believe G is correct, meaning something in DM is wrong. The refutation
  becomes evidence *against* the DM. This initiates **DM revision** — Peirce's
  "irritation of doubt."
- **2c. Fork**: Both G and ¬G have defensible grounds. The UoD branches into
  alternative domain models (DM₁ with G, DM₂ without). The DAG history
  records both branches.
- **2d. Reductio resource**: The contradiction itself is useful — it establishes
  ¬G as a theorem of DM, constraining future reasoning.

#### Case 3 — G Independent (Stalemate)

This is the richest case — it corresponds to **genuinely new knowledge** that DM
alone cannot adjudicate:

- **3a. New empirical fact**: G describes an observation. Both players agree to
  assert G into DM (INS at the sheet). The DM grows by **induction**.
- **3b. Abductive hypothesis**: G *explains* something puzzling in DM (unifies
  seemingly unrelated theorems). Tentatively accepted as a hypothesis. Peirce's
  abduction — "the only logical operation which introduces any new idea."
- **3c. Open conjecture**: G is interesting but unverified. Recorded in the UoD
  history as a conjecture, neither asserted nor denied.
- **3d. Definition or convention**: G introduces new terminology or conceptual
  structure. Accepted by mutual agreement, not by proof.
- **3e. Conditional acceptance**: G is accepted under an additional premise P.
  The result P → G is added to DM.

#### Case 4 — G is Tautological

Trivially true, adds no information. The proof structure may be pedagogically
valuable. Also serves as a **soundness check** on the game mechanics.

#### Case 5 — G is Self-Contradictory

Trivially false. May signal a **formalization error** rather than a logical
one — the Graphist intended a different graph. The Umpire may allow reformulation.

### III. Composite Cases

Real-world proposals are often complex:

- **Case 6 — Partial overlap**: Parts of G are theorems, parts are independent,
  parts may conflict. The game decomposes G and adjudicates each component.
- **Case 7 — Refinement**: G adds more specific claims consistent with DM
  (specialization). Accepted as a strengthening.
- **Case 8 — Generalization**: G proposes a broader principle subsuming existing
  DM content. An **inductive leap** — the most characteristically Peircean move.

### IV. Connection to Peirce's Three Modes of Inference

| Mode | EPG Outcome | Character |
|------|-------------|-----------|
| **Deduction** | Case 1 (theorem) | G follows necessarily from DM |
| **Induction** | Case 3a (new fact) | G is supported by evidence |
| **Abduction** | Case 3b (hypothesis) | G explains something in DM |

---

## The Umpire's Role

The Umpire is not merely a referee but the **guardian of the inquiry process**:

1. **Pre-game**: Confirms DM is well-formed and mutually agreed upon
2. **During game**: Validates move legality, enforces turn order and polarity rules
3. **Post-game**: Oversees the **negotiation of pragmatic outcome** — this is where
   cases 2b–2c and 3a–3e are decided by the players
4. **Record-keeping**: Maintains the official transcript via `ProofSerializer`
5. **Meta-adjudication**: When players disagree on whether G should revise DM
   (case 2b vs 2a), the Umpire facilitates resolution

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

The Umpire may suggest concession when the outcome is logically determined
but the players have not yet reached a terminal state.

---

## Exemplar Scripts

See `tests/test_epg_exemplar_scripts.py` for executable implementations
of the following scenarios:

### Simple Outcome Examples

| Script | DM | Proposal G | Outcome | Demonstrates |
|--------|-----|------------|---------|--------------|
| **A** | ∀x(Human(x)→Mortal(x)), Human(Socrates) | Mortal(Socrates) | 1a: Theorem | Deductive proof (Barbara) |
| **B** | ∀x(Cat(x)→Mammal(x)) | ∃x(Cat(x)∧Fish(x)) | 2a: Refuted | Standard refutation |
| **C** | P | ¬P | 2d: Reductio | Contradiction as resource |
| **D** | ∀x(Human(x)→Mortal(x)) | Human(Socrates) | 3a: New fact | Empirical enlargement |
| **E** | Human(Socrates), Mortal(Socrates) | ∀x(Human(x)→Mortal(x)) | 3b: Abduction | Inductive generalization |
| **F** | ∀x(Swan(x)→White(x)) | ∃x(Swan(x)∧Black(x)) | 2b: DM revision | Revolutionary challenge |
| **G** | (empty sheet) | ¬¬P→P (double negation) | 4: Tautology | Soundness check |
| **H** | P | P∧¬P | 5: Self-contradictory | Formalization error |

### Advanced Strategy Examples

| Script | Scenario | Key Feature |
|--------|----------|-------------|
| **I** | Multi-move deduction with IT+ chain | Proposer propagation strategy |
| **J** | Skeptic simplification via ERA+DC- | Skeptic reduction strategy |
| **K** | Territory expansion via DC+ | Preparatory moves |
| **L** | IT+/IT- push-pull exchange | Dialectical middle game |
| **M** | Concession after exhausting moves | Endgame recognition |
| **N** | Fork into alternative DMs | DM revision negotiation |

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
- **Community of inquiry**: The Umpire represents the community's standards
- **Fallibilism**: Even "proven" results may be revised (case 2b)
- **Growth of knowledge**: Independent proposals (case 3) are the engine of discovery
