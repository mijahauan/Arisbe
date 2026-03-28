# Arisbe: Status and Development Roadmap

**Date**: 2026-03-27  
**Current Phase**: Beta Graph Support Complete — Next: GUI Integration

---

## Executive Summary

Arisbe implements Frithjof Dau's complete formalization of Peirce's Existential Graphs (EGI) as a rigorous computational system. The mathematical core — including full **Beta graph support** (first-order logic with lines of identity crossing cut boundaries) — is complete and thoroughly tested. The codebase comprises 39 production modules in `src/` with **254 passing tests** across 26 test files.

**Completed since last major update (March 2026):**

- ✅ IT+ rule fully fixed (UUID-based IDs, attribute copying, recursive cut duplication, nesting precondition)
- ✅ NetworkX VF2 isomorphism engine (replaced O(n!) brute force)
- ✅ Z3 SMT-solver semantic validation
- ✅ Endoporeutic Game engine + REPL
- ✅ Headless RuleInteraction protocol for stepwise proof construction
- ✅ Beta graph support (lines of identity, Beta-aware closure, Beta-aware IT+)
- ✅ Logical proof exercises (propositional tautologies + FOL Beta proofs)
- ✅ Proof serialization as JSON notation

**Current focus areas:**

- GUI integration of the RuleInteraction protocol
- Ergasterion interactive editor completion
- Organon browser import/export integration
- Advanced Beta proofs (Barbara/Celarent syllogisms)

---

## What Arisbe Is

Arisbe is an implementation environment for Peirce's Existential Graphs following Dau's 2006 mathematical formalization. It is grounded in the conviction that **doing logic in pictures** — Peirce's "moving pictures of thought" — is not merely a notational variant of symbolic logic but a qualitatively different cognitive and expressive act.

The system provides three modes of engagement:

- **Organon**: Explore the corpus of EGI graphs (read-only, annotation, curation)
- **Ergasterion**: Build and transform graphs (practice, composition, derivation)
- **Agon**: Formal dialogical reasoning via the Endoporeutic Game

Domain models — Universes of Discourse — are represented as EGIF graphs, not as external data structures. The graphical interface functions as a facilitator of aesthetic, expressive, and interpretive skills, not merely a renderer.

---

## Production Core: What Is Working

### EGI Data Model (`egi_core_dau.py`)

Immutable implementation of Dau's 6+1 component definition:

- **V**: set of vertices (constants and generic/logical)
- **E**: set of edges (n-ary relations/predicates)
- **Cut**: set of cuts (logical negation contexts)
- **ν (nu)**: vertex sequence for each edge
- **κ (kappa)**: relation symbol for each edge
- **area**: containment mapping (area → frozenset of elements)
- **sheet**: the outermost area (sheet of assertion)

All structures are immutable frozen dataclasses. Transformations produce new EGIs via `.with_vertex()`, `.with_edge()` patterns. Canonical `area_polarity()` method provides O(1) polarity and nesting-depth lookup via `HierarchicalIndex`.

### Linear Format Parsers and Generators

All formats tested against 100+ examples from the Arisbe corpus:

| Format | Module | Status |
|--------|--------|--------|
| EGIF | `egif_parser_dau.py`, `egif_generator_dau.py` | ✅ Production (57+ tomos) |
| CGIF | `cgif_parser_dau.py`, `cgif_generator_dau.py` | ✅ Production (40+ tomos) |
| CLIF | `clif_parser_dau.py`, `clif_generator_dau.py` | ✅ Production (35+ tomos) |
| FOPL | `chapter18_fopl_translation.py` | ✅ Production (Φ/Ψ bidirectional) |
| JSON | `egi_io.py` | ✅ Production (with layout deltas) |

Round-trip fidelity is validated (parse → generate → parse). Variable names are preserved across formats. Beta graph structure (shared vertices across cut boundaries) is preserved through round-trips.

### Transformation Rules (`formal_transformation_rules.py`)

All six Dau transformation rules are implemented and Beta-aware:

| Rule | Name | Status |
|------|------|--------|
| DC+ | Double Cut Insertion | ✅ Correct |
| DC- | Double Cut Erasure | ✅ Correct |
| INS | Insertion | ✅ Correct (Beta-aware closure) |
| ERA | Erasure | ✅ Correct (Beta-aware closure) |
| IT+ | Iteration | ✅ Correct (Beta: extends lines of identity) |
| IT- | Deiteration | ✅ Correct (VF2 isomorphism) |

### RuleInteraction Protocol (`rule_interaction.py`)

Headless, platform-independent protocol for stepwise rule application:

- `begin_interaction(rule_name, egi)` → `InteractionState`
- `advance_interaction(state, user_input)` → `StepResult`
- `apply_interaction(state)` → `TransformationResult`

Guided multi-step workflows with automatic subgraph closure expansion and Beta-aware validation. Used by programmatic proof construction and future GUI integration.

### Beta Graph Support (First-Order Logic)

- **Beta-aware `SubgraphClosureValidator`**: `context_area` parameter treats vertices in ancestor areas as free
- **Beta-aware `IterationRule`**: extends lines of identity instead of copying source-area vertices
- **Beta-aware `ErasureRule` / `InsertionRule`**: operate on edges with free outer-area vertices
- **EGIF round-trip**: shared vertex structure preserved across cut boundaries
- **20 dedicated Beta proof exercises** validating all rules on FOL graphs

### Graph Isomorphism (`graph_isomorphism_engine.py`)

✅ **NetworkX VF2** (`MultiDiGraphMatcher`) — polynomial-time subgraph isomorphism. EGI subgraphs encoded as NetworkX MultiDiGraphs with structural attributes. Used for IT- deiteration validation and Endoporeutic Game goal detection.

### Z3 Semantic Validation (`z3_semantic_validator.py`)

✅ **Z3 SMT-solver integration** for semantic equivalence checking:
- `are_semantically_equivalent(G, G')` — UNSAT of ¬(G ↔ G')
- `is_satisfiable(G)`, `is_tautology(G)`
- DC+ soundness confirmed: ∃x.Human(x) ≡ ¬¬∃x.Human(x)
- `chapter17_soundness_evaluation.py` backed by real Z3 calls

### Endoporeutic Game (`endoporeutic_game.py`, `game_repl.py`)

✅ **Fully implemented** two-player dialogical game engine:
- `Player.PROPOSER` / `Player.SKEPTIC` role model
- Polarity-based move permissions enforced
- EGIF-based insertion with fresh-UUID element merging
- Goal detection via graph isomorphism
- Interactive REPL with save/load via `ProofSerializer`
- Transformation history as serializable proof notation

### Logical Proof Exercises

✅ **Propositional tautologies** (`test_logical_proof_exercises.py`):
- Modus ponens, modus tollens, hypothetical syllogism, double negation, contraposition, weakening

✅ **Beta graph proofs** (`test_beta_proof_exercises.py`):
- Universal strengthening, weakening via ERA, IT+/IT- round-trips
- Multi-predicate and multi-variable Beta graphs
- EGIF round-trip verification for Beta structure preservation

### Layout Engine (`unified_d3_engine.py`)

Recursive bottom-up D3-force layout engine with hard containment constraints. Production-ready. Used by `diagram_controller.py` and the GUI.

### Style System (`style_loader.py`, `style_specification.py`)

Three built-in styles: Dau (mathematical), Peirce (authentic), Sowa (conceptual graph). JSON-based specification. Polarity-aware rendering (negative areas shaded).

### GUI (`src/gui_clean/`)

Three-tab PySide6 application (Organon, Ergasterion, Agon). Organon is functional for browsing and reading the corpus. Ergasterion has foundation integrated. Agon pending GUI wrapping of the production game engine.

### Universe of Discourse (`universe_of_discourse.py`, `tomos_service.py`)

DAG-based transformation history. UoD is the fundamental entity — a diachronic reasoning process, not a static EGI. The `TomosService` API manages corpus access.

### Subgraph Closure Validation (`subgraph_closure_validator.py`)

Validates and auto-expands subgraph selections to satisfy Dau's closure requirement for INS and ERA. **Beta-aware**: `context_area` parameter treats vertices in ancestor areas as free, enabling operations on edges whose vertices live in enclosing scopes.

---

## Test Status

**254 tests passing, 0 failing, 3 skipped** (as of 2026-03-27). 26 test files.

Key test files:

- `test_beta_proof_exercises.py` — 20 Beta graph FOL tests (shared vertices, EGIF round-trips)
- `test_logical_proof_exercises.py` — Propositional tautology derivations via RuleInteraction
- `test_rule_interaction.py` — Headless RuleInteraction protocol integration tests
- `test_subgraph_closure_validation.py` — SubgraphClosureValidator (including Beta-aware)
- `test_graph_isomorphism_engine.py` — VF2 isomorphism correctness
- `test_it_minus_with_isomorphism.py` — IT- deiteration validation
- `test_it_minus_dau_compliance.py` — IT- Dau compliance
- `test_tomos_parsing.py` — EGIF/CGIF/CLIF round-trip across tomos corpus
- `test_variable_order_alignment.py` — variable name preservation
- `test_variable_name_consistency.py` — semantic variable names across formats
- `test_chapter15_formal_calculus.py` — Chapter 15 formal calculus
- `test_chapter16_17_ligature_soundness_simplified.py` — ligature soundness
- `test_chapter20_syntactic_equivalence.py` — syntactic equivalence
- `test_egi_core_comprehensive.py` — comprehensive EGI data model tests

---

## `src/` Module Map (Production Only)

### EGI Core and Linear Formats
```
egi_core_dau.py                  # Dau 6+1 component EGI (immutable)
egif_parser_dau.py               # EGIF → EGI
egif_generator_dau.py            # EGI → EGIF
cgif_parser_dau.py               # CGIF → EGI
cgif_generator_dau.py            # EGI → CGIF
clif_parser_dau.py               # CLIF → EGI
clif_generator_dau.py            # EGI → CLIF
chapter18_fopl_translation.py    # FOPL ↔ EGI (Dau Chapter 18)
egi_io.py                        # JSON load/save with layout_deltas
hierarchical_index.py            # Internal indexing for egi_core_dau
```

### Transformation System
```
formal_transformation_rules.py   # All 6 Dau rules (DC+/-, INS, ERA, IT+/-) — Beta-aware
rule_interaction.py              # Headless stepwise RuleInteraction protocol
graph_isomorphism_engine.py      # NetworkX VF2 subgraph isomorphism (polynomial)
subgraph_closure_validator.py    # Closure checking for INS/ERA (Beta-aware)
insertion_clipboard.py           # Insertion graph management
```

### Ligature and Soundness
```
ligature_manipulation_rules.py   # Ligature-specific transformation rules
vertex_splitting_merging_rules.py
single_object_ligature_detector.py
nary_identity_relations.py
theta_relation.py
enhanced_ligature_algorithms.py
chapter17_soundness_evaluation.py  # Soundness proofs (Z3-backed)
syntactic_equivalence_checker.py
chapter20_syntactic_equivalence_fixes.py
egi_validity_analyzer.py
dau_formalism_validator.py
```

### Data Model and Corpus
```
universe_of_discourse.py         # UoD: diachronic reasoning process
egi_transformation_history.py    # DAG-based transformation history
tomos_service.py                 # Corpus management API
tomos_index.py                   # Fast index for corpus browsing
```

### Layout and Rendering
```
unified_d3_engine.py             # Recursive bottom-up D3 layout (production)
unified_d3_worker.js             # JS worker for D3 simulation
style_loader.py                  # Style loading and validation
style_specification.py           # Style dataclass definitions
simple_svg_renderer.py           # Platform-independent SVG renderer
```

### Controller and Export
```
diagram_controller.py            # Central coordinator (GUI ↔ EGI ↔ layout)
controller/constraint_engine.py  # Platform-agnostic constraint system
export/tikz_exporter.py          # LaTeX/TikZ export
export/dto_to_tikz_adapter.py    # LayoutDTO → TikZ adapter
```

### GUI
```
gui_clean/main_application.py    # Entry point: python src/gui_clean/main_application.py
gui_clean/main_window.py         # Three-tab window (Organon, Ergasterion, Agon)
gui_clean/organon/               # Corpus browser (functional)
gui_clean/ergasterion/           # Graph editor (stub, pending game engine)
gui_clean/agon/                  # Game interface (stub, pending game engine)
```

---

## Development Roadmap

### ✅ Completed (March 2026)

- **IT+ rule fully fixed**: UUID-based IDs, attribute copying, recursive cut duplication, nesting precondition, Beta-aware line-of-identity extension
- **NetworkX VF2 isomorphism**: Polynomial-time `MultiDiGraphMatcher` replaces O(n!) brute force
- **Z3 semantic validation**: `z3_semantic_validator.py` with `are_semantically_equivalent`, `is_satisfiable`, `is_tautology`
- **Endoporeutic Game**: `endoporeutic_game.py` + `game_repl.py` — full two-player dialogical engine
- **RuleInteraction protocol**: `rule_interaction.py` — headless stepwise proof construction
- **Beta graph support**: Lines of identity, Beta-aware closure, Beta-aware IT+/ERA/INS
- **Proof exercises**: Propositional tautologies + FOL Beta graph proofs (254 tests)
- **Proof serialization**: JSON notation via `proof_serializer.py`
- **Logical core unification**: Canonical `area_polarity()` method, elimination of ad-hoc polarity calculations

### Current Focus (Q2 2026)

- **GUI integration of RuleInteraction protocol**: Wire the headless protocol into the Ergasterion editor
- **Ergasterion interactive editor**: Constraint enforcement, selection system, real-time feedback
- **Organon browser completion**: Import/export integration, full corpus navigation
- **Advanced Beta proofs**: Barbara/Celarent syllogisms with full FOL quantification

### Medium-term (2026)

- **GUI Agon mode**: Qt-based Endoporeutic Game interface (wrapping the production REPL engine)
- **Web interface**: Browser-based EG editor and viewer
- **Collaborative editing**: Shared UoD sessions
- **Advanced visualization**: Animated transformation sequences

### Long-term

- **Educational platform**: Complete learning management system for EG theory
- **Machine learning integration**: Pattern recognition in logical transformation sequences
- **Theorem prover bridge**: Integration with Coq/Lean via CLIF

---

## Theoretical Foundation

### Peirce's Existential Graphs

Peirce's EG system (ca. 1896–1913) represents first-order logic diagrammatically using:

- **Sheet of Assertion**: the base context, everything on it is asserted
- **Cuts** (closed curves): negation contexts
- **Ligatures** (lines of identity): existential quantification
- **Spots** (predicates): relational assertions

The Alpha system handles propositional logic; Beta adds ligatures for predicate logic; Gamma extends to modal and higher-order logic. Arisbe implements the Beta system.

### Dau's Formalization

Frithjof Dau (2006) provides the canonical mathematical formalization in *The Logic System of Concept Graphs with Negations*. Key chapters:

- **Chapter 14**: Relational Graphs with Cuts (the EGI data model)
- **Chapter 15**: Formal Calculus (the six transformation rules)
- **Chapter 16**: Ligature manipulation rules
- **Chapter 17**: Soundness proofs
- **Chapter 18**: Linear form translations (EGIF/CGIF/CLIF/FOPL)
- **Chapter 20**: Syntactic equivalence
- **Chapter 21**: Diagram interaction architecture

### The Endoporeutic Game

Peirce's game semantics for EG: the Proposer (Graphist) asserts a graph is true; the Skeptic (Grapheus) attempts to disprove it through challenge and counter-moves. The game proceeds by alternating rule applications:

- In positive contexts: Skeptic chooses which rule to apply
- In negative contexts: Proposer chooses
- Winner is determined by whether the final state is a tautology, contradiction, or contingent

This dialogical interpretation makes EG a precursor to modern game-theoretic semantics (Hintikka, Lorenz).

---

## Quick Start

```bash
# Environment
conda activate CGIF

# Run tests (254 passing)
python -m pytest tests/ -q

# Launch GUI
python arisbe.py

# Use core API
python -c "
import sys; sys.path.insert(0, 'src')
from egif_parser_dau import parse_egif
from egif_generator_dau import generate_egif

# Beta graph: ∀x(Human(x) → Mortal(x))
egi = parse_egif('~[ (Human *x) ~[ (Mortal x) ] ]')
print(generate_egif(egi))
"

# Headless proof construction
python -c "
import sys; sys.path.insert(0, 'src')
from egif_parser_dau import parse_egif
from rule_interaction import begin_interaction, advance_interaction, apply_interaction

egi = parse_egif('(P *a) ~[ (P *b) ~[ (Q *c) ] ]')  # P, P→Q
# Modus ponens via IT- then DC-
print('Try: test_logical_proof_exercises.py for full examples')
"
```

---

## Key Files for Orientation

| Need | File |
|------|------|
| Core API reference | `ARISBE_CORE_API_REFERENCE.md` |
| Protection system | `tools/core_protection_system.py` |
| This roadmap | `docs/ARISBE_STATUS_AND_ROADMAP.md` |
| Triad architecture | `docs/arisbe_triad_architecture.md` |
| UoD architecture | `UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md` |
| Import/export guide | `IMPORT_EXPORT_FORMATS.md` |
| Layout engine design | `BOTTOM_UP_D3_ARCHITECTURE.md` |
