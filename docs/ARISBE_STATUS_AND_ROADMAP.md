# Arisbe: Status and Development Roadmap

**Date**: 2026-03-20  
**Current Phase**: Foundation Consolidated — Next: Transformation Fixes + Endoporeutic Game

---

## Executive Summary

Arisbe implements Frithjof Dau's complete formalization of Peirce's Existential Graphs (EGI) as a rigorous computational system. The mathematical core is complete and thoroughly tested. A housecleaning in March 2026 removed ~100 legacy files, leaving a clean, production-quality `src/` with ~40 modules and 151 passing tests.

**Current focus areas:**
- Fix the IT+ transformation rule (known bugs in attribute copying and preconditions)
- Replace the O(n!) isomorphism engine with NetworkX
- Complete EGIF as a version-controllable proof notation
- Design and implement the Endoporeutic Game as a REPL/CLI engine
- Integrate Z3 for semantic validation

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

All structures are immutable frozen dataclasses. Transformations produce new EGIs via `.with_vertex()`, `.with_edge()` patterns.

### Linear Format Parsers and Generators

All formats tested against 100+ examples from the Arisbe corpus:

| Format | Module | Status |
|--------|--------|--------|
| EGIF | `egif_parser_dau.py`, `egif_generator_dau.py` | ✅ Production |
| CGIF | `cgif_parser_dau.py`, `cgif_generator_dau.py` | ✅ Production |
| CLIF | `clif_parser_dau.py`, `clif_generator_dau.py` | ✅ Production |
| FOPL | `chapter18_fopl_translation.py` | ✅ Production |
| JSON | `egi_io.py` | ✅ Production |

Round-trip fidelity is validated (parse → generate → parse). Variable names are preserved across formats.

### Transformation Rules (`formal_transformation_rules.py`)

All six Dau transformation rules are implemented:

| Rule | Name | Status | Known Issues |
|------|------|--------|--------------|
| DC+ | Double Cut Insertion | ✅ Correct | None |
| DC- | Double Cut Erasure | ✅ Correct | None |
| INS | Insertion | ✅ Correct | None |
| ERA | Erasure | ✅ Correct | None |
| IT+ | Iteration | ⚠️ Bugs | See below |
| IT- | Deiteration | ✅ Correct | None |

**IT+ Known Bugs** (to be fixed):
1. Copied vertex IDs use `_copy` suffix — accumulates across multiple iterations
2. Copied vertices lose label and `is_generic` attributes
3. Cut interiors not fully duplicated
4. Nesting precondition not enforced (iteration must move to a more-enclosed area)

### Graph Isomorphism (`graph_isomorphism_engine.py`)

Implemented but uses O(n!) brute-force permutation enumeration. Correct for small subgraphs but unusable for anything beyond ~5 elements. **Replacement with NetworkX is the immediate priority.**

### Layout Engine (`unified_d3_engine.py`)

Recursive bottom-up D3-force layout engine with hard containment constraints. Production-ready. Used by `diagram_controller.py` and the GUI.

### Style System (`style_loader.py`, `style_specification.py`)

Three built-in styles: Dau (mathematical), Peirce (authentic), Sowa (conceptual graph). JSON-based specification. Polarity-aware rendering (negative areas shaded).

### GUI (`src/gui_clean/`)

Three-tab PySide6 application (Organon, Ergasterion, Agon). Organon is functional for browsing and reading the corpus. Ergasterion and Agon are stubs pending the REPL/CLI game engine.

### Universe of Discourse (`universe_of_discourse.py`, `tomos_service.py`)

DAG-based transformation history. UoD is the fundamental entity — a diachronic reasoning process, not a static EGI. The `TomosService` API manages corpus access.

### Subgraph Closure Validation (`subgraph_closure_validator.py`)

Validates and auto-expands subgraph selections to satisfy Dau's closure requirement for INS and ERA.

### Soundness Evaluation (`chapter17_soundness_evaluation.py`)

Implements the framework for Dau Chapter 17 soundness proofs. **Currently mostly stub** — semantic consistency checks return `True`. Replacement with Z3 is planned.

---

## Test Status

**151 tests passing, 0 failing, 3 skipped** (as of 2026-03-20 after housecleaning).

Key test files:
- `tests/test_corpus_parsing.py` — EGIF/CGIF/CLIF round-trip across 100+ tomos examples
- `tests/test_variable_order_alignment.py` — variable name preservation
- `tests/test_variable_name_consistency.py` — semantic variable names across formats
- `tests/test_subgraph_closure_validation.py` — SubgraphClosureValidator
- `tests/test_graph_isomorphism_engine.py` — isomorphism correctness
- `tests/test_it_minus_with_isomorphism.py` — IT- deiteration validation
- `tests/test_chapter15_formal_calculus.py` — Chapter 15 formal calculus
- `tests/test_chapter16_17_ligature_soundness_simplified.py` — ligature soundness
- `tests/test_chapter20_syntactic_equivalence.py` — syntactic equivalence
- `tests/unit/test_egi_transformation_rules_unit.py` — per-rule unit tests

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
formal_transformation_rules.py   # All 6 Dau rules (DC+/-, INS, ERA, IT+/-)
graph_isomorphism_engine.py      # Subgraph isomorphism (⚠️ O(n!), needs NetworkX)
subgraph_closure_validator.py    # Closure checking for INS/ERA
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
chapter17_soundness_evaluation.py  # Soundness proofs (⚠️ mostly stub)
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

### Immediate: Fix IT+ Rule

**File**: `src/formal_transformation_rules.py`, `IterationRule` class

Required fixes:
1. Use `uuid.uuid4()` for copied element IDs (not `_copy` suffix)
2. Copy vertex attributes: `label`, `is_generic`
3. Properly duplicate cut interiors (recursive area copy)
4. Enforce nesting precondition: the destination area must be enclosed by the source area

### Immediate: NetworkX Isomorphism

**File**: `src/graph_isomorphism_engine.py`

Replace the O(n!) permutation loop in `test_subgraph_isomorphism` with NetworkX `vf2userfunc` or `is_isomorphic`. The EGI needs to be converted to a NetworkX DiGraph with node/edge attributes carrying vertex labels, generic status, and relation symbols. Cut nesting must be encoded as edges.

NetworkX 3.5 is already installed in the CGIF conda environment.

### Near-term: EGIF as Proof Notation

Transformation sequences (chains of EGI states + rule applications) should be serializable as annotated EGIF files. Each step is: `(rule_name, selected_subgraph_egif, result_egif)`. This enables version-controllable, text-diffable proof files.

**New module**: `src/proof_notation.py`

### Near-term: Z3 Semantic Validation

Install `z3-solver` and implement real semantic consistency checking in `chapter17_soundness_evaluation.py`. Z3 integration converts EGI structures to Z3 formulas and checks satisfiability/validity, replacing the current `return True` stubs.

**Install**: `conda install -c conda-forge z3-solver`

### Primary Goal: Endoporeutic Game REPL/CLI

Design and implement the Endoporeutic Game as a standalone REPL/CLI engine, independent of the GUI. The game engine will serve as the formal reasoning core that the GUI Agon mode wraps.

**Architecture**:
```
GameState
├── domain_model: EGIF         # The agreed Universe of Discourse
├── assertion: EGIF            # Proposer's current assertion
├── history: List[GameMove]    # Full game transcript
└── turn: Player               # PROPOSER | SKEPTIC

GameMove
├── player: Player
├── rule: TransformationRule
├── context: TransformationContext
└── result_state: GameState

GameEngine (REPL)
├── load_domain(egif_text)     # Set domain model
├── propose(egif_text)         # Proposer makes assertion
├── challenge(area_id)         # Skeptic selects a context
├── respond(rule, subgraph)    # Proposer applies transformation
└── evaluate() → GameOutcome   # WIN | LOSE | DRAW
```

Domain models and assertions are both EGIFs. The REPL loop processes natural-language-style commands against a running `GameState`. The GUI wraps this engine — it does not reimplement it.

**New module**: `src/endoporeutic_game.py`

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

# Run tests
python -m pytest tests/ -q

# Launch GUI
python src/gui_clean/main_application.py

# Use core API
python -c "
from egi_core_dau import create_empty_graph
from egif_parser_dau import parse_egif
from egif_generator_dau import generate_egif

egi = parse_egif('[*x] (Human x) ~[ ~[ (Mortal x) ] ]')
print(generate_egif(egi))
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
