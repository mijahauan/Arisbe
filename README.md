# Arisbe: Universes of Discourse
**Peirce's "Moving Pictures of Thought" Made Real**

A formal reasoning environment implementing Charles S. Peirce's Existential Graphs through Frithjof Dau's rigorous framework. Arisbe elevates logical diagrams from static notation to **living processes of inquiry** - complete universes of discourse where justification, transformation, and meaning unfold through dialogue and formal rules.

---

## 🎯 **Philosophical Foundation** (Read First)

### The Paradigm Shift

**Traditional View**: An Existential Graph (EG) is a **static diagram** to be edited and analyzed.

**Arisbe's View**: The fundamental entity is the **Universe of Discourse (UoD)** - the complete **diachronic process** of logical reasoning. A single EG diagram is merely a **synchronic snapshot** within this larger evolution.

**Analogy**:
- **EGI** = A photograph (one frame)
- **Universe of Discourse** = The entire film (coherent sequence)

👉 **Complete philosophy**: [UNIVERSE\_OF\_DISCOURSE\_ARCHITECTURE.md](docs/UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md)

### What is a Universe of Discourse?

A **UoD** is the complete logical environment consisting of:

1. **The Transformation History** (the recorded log)
   - Sequence of valid rule applications
   - Complete provenance tracking
   - Branching and exploration paths (DAG-based)

2. **The Synchronic States** (the frames)
   - `(EGI_Model, LayoutDeltas)` at each point in time
   - Complete logical structure + visual presentation

3. **The In-forming Events** (what drives evolution)
   - **Assertions**: Introducing new facts
   - **Abductions**: Proposing explanatory hypotheses
   - **Deductions**: Applying formal transformation rules
   - **User edits**: Visual presentation refinements

**Result**: Arisbe is not a diagram editor, but a **logical reasoning environment** where inquiry, justification, and transformation are first-class citizens.

---

## 🏛️ **Three-Module Architecture**

Arisbe mirrors the process of scientific inquiry through three integrated modules:

### Organon 🏛️ (The Archive)
**Greek**: ὄργανον - "tool" or "instrument"

The **library and archives** for universes of discourse.

**Capabilities**:
- Navigate transformation history (timeline, undo/redo)
- Explore any historical state
- Import literature examples
- Export proofs, diagrams, sequences
- Search and browse corpus

**Metaphor**: The published proceedings and library - read, cite, export

### Ergasterion 🔬 (The Workshop)
**Greek**: ἐργαστήριον - "workshop"

The **private sandbox** for creation and practice.

**Capabilities**:
- Draft new graphs from scratch
- Practice transformation rules safely
- Experiment without affecting main UoD
- Promote completed work to Agon for validation

**Metaphor**: Researcher's private lab - run experiments, refine ideas

### Agon ⚔️ (The Arena)
**Greek**: ἀγών - "contest" or "struggle"

The **core reasoning engine** and referee.

**Capabilities**:

- Validate logical changes through **Endoporeutic Game**
- Record transformations in UoD history
- Advance the diachronic process
- Enforce Dau formalism compliance

**Metaphor**: Conference room - formal presentation, justification, official record

**The Endoporeutic Game** *(implemented)*: New facts are defended in a two-player dialogical contest:

- **Proposer**: Defends the graph; moves in negative (odd-depth) areas using INS, IT+, DC±
- **Skeptic**: Challenges the assertion; moves in positive (even-depth) areas using ERA, IT-, DC±
- Reading proceeds **outside-in** (endoporeutic method)
- Skeptic conceding, or Proposer reaching the goal graph, ends the game

---

## 🌟 **Project Status**

**What**: Complete implementation of Dau's formalism for Peirce's Existential Graphs  
**Who**: Researchers, logicians, and students working with diagrammatic reasoning  
**Why**: First modern, rigorous implementation of EG as a **process-oriented logic system**

👉 **Full vision**: [PRODUCT_VISION.md](docs/PRODUCT_VISION.md)  
👉 **AI assistance**: [AI_CONDUCT_GUIDELINES.md](AI_CONDUCT_GUIDELINES.md)

---

## 🔒 **Development Guidelines**

- **📚 API Documentation**: `docs/ARISBE_CORE_API_REFERENCE.md`
- **🛡️ Core Protection**: 16 validated modules, 254 passing tests
- **📊 Quality Monitoring**: Automated quality gates and daily dashboard
- **🧠 Context Recovery**: `docs/context/COHERENCE_FRAMEWORK_REMINDER.md`

**→ New to the codebase? Read `AGENTS.md` for complete development guidelines.**

---

## 📐 **Technical Foundation**

**Data Model**:

- **UoD**: Universe of Discourse (the fundamental entity)
- **EGI**: Existential Graph Instance (synchronic snapshot)
- **State**: `(EGI_Model, LayoutDeltas)` pair (structure + presentation)
- **History**: DAG-based transformation log with branching and provenance

**Linear Forms** (all round-trip to/from EGI):

- **EGIF**: Dau's existential graph interchange format
- **CGIF**: Conceptual graph interchange format
- **CLIF**: Common logic interchange format
- **FOPL**: First-order predicate logic (Dau Chapter 18 Φ/Ψ translations)

**Visual System**:

- Cuts (negation boundaries)
- Predicates (relations)
- Vertices (individuals, constants, variables)
- Ligatures (identity lines connecting vertices)

**Transformation Rules** (Dau formalism, all implemented):

- **ERA / INS**: Erasure and insertion (polarity-controlled, Beta-aware closure)
- **IT+ / IT-**: Iteration and deiteration (Beta: extends lines of identity)
- **DC+ / DC-**: Double cut insertion and erasure

**Beta Graph Support** (full first-order logic):

- Lines of identity crossing cut boundaries (shared vertices across areas)
- Beta-aware subgraph closure validation (free outer-area vertices)
- IT+ extends lines of identity instead of copying vertices
- Headless RuleInteraction protocol for stepwise proof construction

---

## 🏗️ Architecture

### Core Source Modules (`src/`)

**EGI Data Model:**

- `egi_core_dau.py` — `RelationalGraphWithCuts` with 6+1 component architecture (V, E, ν, sheet, Cut, area, rel)
- `egi_io.py` — JSON persistence with layout delta preservation
- `egi_transformation_history.py` — DAG-based transformation history with branching

**Transformation Engine:**

- `formal_transformation_rules.py` — All six Dau rules (ERA, INS, IT+, IT-, DC+, DC-) with Beta-aware precondition validation
- `rule_interaction.py` — Headless RuleInteraction protocol for stepwise rule application (DC+, DC-, ERA, INS, IT+, IT-)
- `hierarchical_index.py` — O(1) polarity and nesting-depth lookup
- `chapter17_soundness_evaluation.py` — Soundness evaluation framework (Z3-backed)
- `ligature_manipulation_rules.py` — Chapter 16/17 ligature rules
- `vertex_splitting_merging_rules.py` — Vertex split/merge operations
- `enhanced_ligature_algorithms.py` — Ligature detection and manipulation

**Linear Forms:**

- `egif_parser_dau.py` / `egif_generator_dau.py` — EGIF (57+ tomos examples validated)
- `cgif_parser_dau.py` / `cgif_generator_dau.py` — CGIF ISO/IEC standard (40+ examples)
- `clif_parser_dau.py` / `clif_generator_dau.py` — CLIF Common Logic standard (35+ examples)
- `chapter18_fopl_translation.py` — FOPL ↔ EGI (Φ/Ψ translations, Dau Chapter 18)

**Semantic Validation:**

- `z3_semantic_validator.py` — Z3 SMT-solver based semantic equivalence checking
  - `are_semantically_equivalent(G, G')`: UNSAT of ¬(G ↔ G')
  - `is_satisfiable(G)`, `is_tautology(G)`
  - `Z3Result` with True/False/None (timeout) values

**Endoporeutic Game (Agon):**

- `endoporeutic_game.py` — Game engine with `Player` enum, `GameState`, polarity-based move validation
- `game_repl.py` — Interactive REPL (`cmd.Cmd`) for two-player play
- `proof_serializer.py` — Transformation history serialized as JSON proof notation

**Graph Operations:**

- `graph_isomorphism_engine.py` — NetworkX VF2 `MultiDiGraphMatcher` for goal detection
- `syntactic_equivalence_checker.py` — Chapter 20 syntactic equivalence
- `chapter20_syntactic_equivalence_fixes.py` — Equivalence edge cases
- `subgraph_closure_validator.py` — INS/ERA closure validation (Beta-aware: free outer-area vertices)

**Corpus and UoD Management:**

- `universe_of_discourse.py` — `UniverseOfDiscourse` entity (synchronic + diachronic + layout)
- `tomos_service.py` — Unified API for corpus browsing and UoD loading
- `tomos_index.py` — Index-based fast corpus navigation

**Layout and Visualization:**

- `unified_d3_engine.py` — Recursive bottom-up D3 layout engine (production)
- `simple_svg_renderer.py` — Direct LayoutDTO → SVG rendering
- `style_specification.py` / `style_loader.py` — Declarative visual style system
- `diagram_controller.py` — GUI coordination layer

**Utilities:**

- `dau_formalism_validator.py` — Cross-chapter Dau compliance checking
- `insertion_clipboard.py` — Persistent INS workflow clipboard
- `egi_validity_analyzer.py` — Structural EGI integrity checking
- `nary_identity_relations.py` — N-ary identity/ligature relations
- `theta_relation.py` — Θ-relation for ligature equivalence classes
- `single_object_ligature_detector.py` — Single-object ligature detection

### Core Principles

- **EGI as single source of truth**: All visual changes are presentation deltas
- **Immutable transformations**: All EGI operations produce new immutable instances
- **Round-trip fidelity**: Guaranteed across all linear format translations
- **Mathematical rigor**: All rules validated against Dau's formal specifications
- **Semantic grounding**: Z3-verified equivalence for transformation soundness

---

## 📁 Project Structure

```
src/                  Core logic and engine (39 production modules)
tests/                Pytest test suite (270 passing, 27 test files)
tools/                Quality tools, demos, and utilities
docs/                 Architecture documentation
docs/context/         AI-assist context and recovery guides
tomos/                Canonical example corpus (87 items)
corpus/               Active working corpus
archive/              Archived legacy components
styles/               Visual style specifications (JSON)
```

---

## 🚀 Quick Start

### Install

```bash
conda activate CGIF   # Python 3.12; see requirements.txt
pip install -r requirements.txt
```

### Launch the Qt GUI

```bash
python arisbe.py
```

### Play the Endoporeutic Game (REPL)

```bash
conda run -n CGIF python -c "
import sys; sys.path.insert(0, 'src')
from game_repl import ArisbeGameREPL
ArisbeGameREPL().cmdloop()
"
```

### Parse and work with EGI in code

```python
import sys; sys.path.insert(0, 'src')
from egif_parser_dau import parse_egif
from egif_generator_dau import generate_egif

# Beta graph: ∀x(Human(x) → Mortal(x))
egi = parse_egif('~[ (Human *x) ~[ (Mortal x) ] ]')
print(generate_egif(egi))  # ~[ *x (Human x) ~[ (Mortal x) ] ]
```

### Apply transformation rules (headless RuleInteraction protocol)

```python
from rule_interaction import begin_interaction, advance_interaction, apply_interaction

# IT+: iterate (Human x) from outer cut into inner cut
state = begin_interaction("IT+", egi)
result1 = advance_interaction(state, [human_edge_id])  # select source
result2 = advance_interaction(state, inner_cut_id)      # select destination
result = apply_interaction(state)
print(generate_egif(result.result_egi))  # ~[ *x (Human x) ~[ (Human x) (Mortal x) ] ]
```

### Z3 semantic validation

```python
from z3_semantic_validator import are_semantically_equivalent
from egif_parser_dau import parse_egif

g1 = parse_egif('*x (Human x)')
g2 = parse_egif('~[~[*x (Human x)]]')   # double-cut equivalent
r = are_semantically_equivalent(g1, g2)
print(r)   # Z3Result(YES: ...)
```

---

## 🧪 Testing

### Core suite

```bash
# Full test suite (254 passing)
conda run -n CGIF python -m pytest tests/ -q

# With verbose output
conda run -n CGIF python -m pytest tests/ -v
```

### Quality and protection

```bash
# Quality gate
conda run -n CGIF python tools/quality_gate_system.py

# Core protection status
conda run -n CGIF python tools/core_protection_system.py --report

# Daily dashboard
conda run -n CGIF python tools/daily_quality_dashboard.py
```

### Demos and integration scripts

```bash
# Syllogism proof demo
conda run -n CGIF python tools/demo_syllogism_proof.py

# Round-trip translation demo
conda run -n CGIF python tools/demo_round_trip_translations.py
```

---

## 🗺️ Sub-application Status

| Module | Status | Notes |
|---|---|---|
| **Organon** (Archive/browser) | Foundation in place | Qt GUI entry; corpus browsing via `TomosService` |
| **Ergasterion** (Workshop) | Foundation in place | Interactive editor; constraint system under development |
| **Agon** (Endoporeutic Game) | ✅ **Implemented** | `endoporeutic_game.py` + `game_repl.py`; Z3-validated |

---

## 📊 Current State (March 2026)

### ✅ Completed

**Mathematical Core:**

- Complete Dau-compliant EGI data structures (6+1 component `RelationalGraphWithCuts`)
- All six transformation rules (ERA, INS, IT+, IT-, DC+, DC-) with precondition validation
- **Full Beta graph support**: lines of identity crossing cut boundaries (first-order logic)
- **Headless RuleInteraction protocol** for stepwise proof construction (all six rules)
- Round-trip translation: EGIF ↔ CGIF ↔ CLIF ↔ FOPL ↔ EGI (57+ / 40+ / 35+ tomos validated)
- Hierarchical indexing for O(1) polarity and nesting calculations
- Chapter 17 ligature rules (move branches, extend/retract, split/merge vertices)
- Chapter 18 FOPL ↔ EGI (Φ/Ψ translations)
- Chapter 20 syntactic equivalence checking
- NetworkX VF2 graph isomorphism (replaces O(n!) permutation engine)

**Beta Graph Support (FOL):**

- Beta-aware `SubgraphClosureValidator` — vertices in ancestor areas are free
- Beta-aware `IterationRule` — extends lines of identity, does not copy source-area vertices
- Beta-aware `ErasureRule` / `InsertionRule` — operate on edges with free outer-area vertices
- EGIF round-trip preservation of shared vertex structure across cut boundaries
- 20 dedicated Beta proof exercises validating all rules on FOL graphs

**RuleInteraction Protocol:**

- Platform-independent, headless protocol for stepwise rule application
- Guided multi-step workflows: source selection → destination → apply
- Automatic subgraph closure expansion with user feedback
- Beta-aware closure validation throughout
- Used by both programmatic proof construction and future GUI integration

**Logical Proof Exercises:**

- Propositional tautologies: modus ponens, modus tollens, hypothetical syllogism, double negation, contraposition, weakening
- Beta graph proofs: universal strengthening, weakening via ERA, IT+/IT- round-trips
- Multi-predicate and multi-variable Beta graphs
- EGIF round-trip verification for Beta structure preservation

**Semantic Validation:**

- Z3 SMT-solver integration (`z3_semantic_validator.py`)
- Semantic equivalence verified: DC+ soundness confirmed (∃x.Human(x) ≡ ¬¬∃x.Human(x))
- `chapter17_soundness_evaluation.py` backed by real Z3 calls

**Endoporeutic Game (Agon):**

- Full game engine with `Player.PROPOSER` / `Player.SKEPTIC` role model
- Polarity-based move permissions enforced
- EGIF-based insertion with fresh-UUID element merging
- Goal detection via graph isomorphism
- Interactive REPL with save/load via `ProofSerializer`
- Transformation history as serializable proof notation

**UoD and Corpus:**

- `UniverseOfDiscourse` as fundamental entity (synchronic + DAG history + layout)
- `TomosService` unified corpus API
- DAG-based transformation history with branching

**Testing:**

- **270 tests passing** (27 test files), 3 skipped (Qt-dependent)
- Quality gates and core protection active
- Comprehensive test coverage: core data model, all six transformation rules,
  import/export round-trips, isomorphism engine, proof exercises (Alpha + Beta),
  rule interaction protocol, subgraph closure validation

### 🔧 In Progress / Next

- Ergasterion interactive editor (constraint enforcement, selection system)
- Organon browser completeness (import/export integration)
- GUI integration of RuleInteraction protocol and Endoporeutic Game
- Advanced Beta proofs: Barbara/Celarent syllogisms with full FOL quantification

---

## 📖 Development Notes

- EGI is the single source of truth; visual edits are presentation deltas (`LayoutDeltas`)
- Cuts determine spatial exclusion; child cuts create forbidden zones for parent-level elements
- Same-area ligatures must avoid cut collisions; cross-area ligatures may cross cut boundaries per EGI mappings
- Rendering order is fixed: Cuts → Predicates → Vertices → Ligatures
- Import pattern: `from module_name import ...` (not `from src.module_name import ...`)

---

## 👥 What Users Can Do with Arisbe

### For Logic Researchers & Academics

- Apply all six formal transformation rules with mathematical validation and Z3 soundness verification
- Verify logical equivalences across EGIF, CGIF, CLIF, FOPL representations
- Play the Endoporeutic Game as a formal proof procedure
- Serialize transformation sequences as proof notation (JSON)
- Export to academic formats (LaTeX/TikZ, SVG)

### For Students & Educators

- Interactive REPL for step-by-step EG transformation practice
- Visual comparison between logical representation formats
- Educational tomos with 87+ canonical examples
- Game-based proof exploration through the Endoporeutic Game

### For Software Developers

- Programmatic EGI creation, validation, and transformation APIs
- Z3-backed semantic validation for transformation soundness
- Batch processing of logic corpora via `TomosService`
- Round-trip translation pipeline between all supported linear forms

### For Knowledge Engineers

- Large-scale corpus management with `TomosService`
- DAG-based transformation history for branching inquiry workflows
- Bridge between diagrammatic (EGI) and symbolic (FOPL/CLIF) reasoning

---

## 🗓️ Development Roadmap

### Current Focus (Q1–Q2 2026)
- **Ergasterion completion**: Full interactive editor with real-time constraint enforcement
- **Organon browser**: Complete import/export integration, full corpus navigation
- **GUI for Agon**: Qt-based Endoporeutic Game interface (REPL currently available)

### Medium-term (2026)
- **Web interface**: Browser-based EG editor and viewer
- **Collaborative editing**: Shared UoD sessions
- **Advanced visualization**: Animated transformation sequences

### Long-term
- **Educational platform**: Complete learning management system for EG theory
- **Machine learning integration**: Pattern recognition in logical transformation sequences
- **Theorem prover bridge**: Integration with Coq/Lean via CLIF

---

## 📚 References

- Dau, Frithjof. *Mathematical Logic with Diagrams* (2003).
- Peirce, C. S. *Existential Graphs* (Collected Papers).
- Sowa, J. F. *Existential Graphs: MS 514 by Charles Sanders Peirce* (2007).
