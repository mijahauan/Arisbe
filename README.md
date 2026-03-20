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

👉 **Complete philosophy**: [UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md](docs/UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md)

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
- **🛡️ Core Protection**: 16 validated modules, 151 passing tests
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
- **ERA / INS**: Erasure and insertion (polarity-controlled)
- **IT+ / IT-**: Iteration and deiteration
- **DC+ / DC-**: Double cut insertion and erasure

---

## 🏗️ Architecture

### Core Source Modules (`src/`)

**EGI Data Model:**
- `egi_core_dau.py` — `RelationalGraphWithCuts` with 6+1 component architecture (V, E, ν, sheet, Cut, area, rel)
- `egi_io.py` — JSON persistence with layout delta preservation
- `egi_transformation_history.py` — DAG-based transformation history with branching

**Transformation Engine:**
- `formal_transformation_rules.py` — All six Dau rules (ERA, INS, IT+, IT-, DC+, DC-) with precondition validation
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
- `subgraph_closure_validator.py` — INS/ERA closure validation

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
src/                  Core logic and engine (38 production modules)
tests/                Pytest test suite (151 passing)
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
from formal_transformation_rules import DoubleCutInsertionRule, TransformationContext, AreaPolarity

egi = parse_egif('*x (Human x) ~[ (Mortal x) ]')

ctx = TransformationContext(
    source_egi=egi,
    target_area=egi.sheet,
    selected_subgraph=frozenset(),
    area_polarity=AreaPolarity.POSITIVE,
    nesting_depth=0,
)
result = DoubleCutInsertionRule().apply_transformation(ctx)
print(generate_egif(result.result_egi))
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
# Full test suite (151 passing)
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
- Round-trip translation: EGIF ↔ CGIF ↔ CLIF ↔ FOPL ↔ EGI (57+ / 40+ / 35+ tomos validated)
- Hierarchical indexing for O(1) polarity and nesting calculations
- Chapter 17 ligature rules (move branches, extend/retract, split/merge vertices)
- Chapter 18 FOPL ↔ EGI (Φ/Ψ translations)
- Chapter 20 syntactic equivalence checking
- NetworkX VF2 graph isomorphism (replaces O(n!) permutation engine)

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
- 151 tests passing (87 core + extended suite)
- Quality gates and core protection active

### 🔧 In Progress / Next

- Ergasterion interactive editor (constraint enforcement, selection system)
- Organon browser completeness (import/export integration)
- GUI integration of Endoporeutic Game (currently REPL only)

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
