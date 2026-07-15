# Arisbe: Universes of Discourse
**Peirce's "Moving Pictures of Thought" Made Real**

An environment for **doing logic in pictures**, built around Charles S. Peirce's Existential Graphs with Frithjof Dau's formalization as the guarantor of correctness. Arisbe elevates logical diagrams from static notation to **living processes of inquiry** - complete universes of discourse where justification, transformation, and meaning unfold through dialogue and formal rules.

The central engineering and research problem the codebase solves: **inerrant correspondence between an EGI's linear written form and its graphical drawn form**. The contract is stated in [docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md](docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md), tested against the tomos corpus, exposed as a refusal-bearing API in [src/presentation_ops.py](src/presentation_ops.py), and runtime-attested at the web service boundary by [src/correspondence_attestation.py](src/correspondence_attestation.py). When picture and proposition come apart, the system refuses to serve a drawing it can't attest.

**The exact-correspondence engine (complete, June 2026).** That contract is now realized *geometrically*: a cut **is its drawn curve**, every mark is an **extent** (label box, not anchor point), and the whole §3.3 invariant — cut containment, ligature crossing-sequence, label/numeral extents, no improper occlusion, argument order by clockwise placement — is checked as a set of **exact facts about the literal drawn picture**, no proxy shape. A cut can be an arbitrary human-drawn polyline, tested point-in-polygon by both the attestation and the reader and hit-tested in the browser via `isPointInFill`. See [docs/EXACT_CORRESPONDENCE.md](docs/EXACT_CORRESPONDENCE.md). It is the foundation the **freeform composition canvas** (draw logic by hand, read it into a sign on demand — shipped, live in Ergasterion) was built on.

**The validity discipline (July 2026).** The attested corpus now enacts a standing discipline about *where saying happens*: nothing contingent stands at depth 0 — the sheet is the world's level, carrying only what the calculus itself delivers — and a domain model **M** resides as a *supposition* at level 1 of a standing world-scroll `~[ M ~[ ] ]`. Every change to M is an explicit rule-licensed chain step (admission = insertion into the scroll's antecedent; revision = withdrawal of the whole world, the history keeping the old one) and every verdict is a recorded, forever-recomputable peel. See [docs/M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE.md](docs/M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE.md) and the standing gate `tests/test_corpus_polarity_discipline.py`. **The active frontier** is now the *second-order crossing* — logic about the graphs themselves (quotation, `(forces s φ)`) — mapped in [docs/SECOND_ORDER_FRONTIER.md](docs/SECOND_ORDER_FRONTIER.md) and deliberately paused on two author decisions; the "Moses" beta tags the completed first-order territory before that crossing.

---
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/mijahauan/Arisbe)
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

**What**: A reasoning environment for doing logic *in* pictures (Peirce's aim), with Dau's formalization as guarantor and inerrant linear↔graphical correspondence as the central testable contract
**Who**: Researchers, logicians, and students working with diagrammatic reasoning
**Why**: First modern implementation that treats correspondence as a stated, tested, and runtime-attested invariant — not an emergent property maintained by careful code

👉 **Full vision**: [VISION_AND_SCOPE.md](docs/VISION_AND_SCOPE.md)
👉 **Correspondence spec**: [LINEAR_GRAPHICAL_CORRESPONDENCE.md](docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md)
👉 **AI assistance**: [AI_CONDUCT_GUIDELINES.md](AI_CONDUCT_GUIDELINES.md)

---

## 🔒 **Development Guidelines**

- **📚 API Documentation**: `docs/ARISBE_CORE_API_REFERENCE.md`
- **🛡️ Core Protection**: 17 validated modules; ~1000 passing tests across the suite
- **📊 Quality Monitoring**: Automated quality gates and daily dashboard
- **🧠 Context Recovery**: `docs/RETURN_TO_DEVELOPMENT.md`

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

- `natural_layout.py` — coordinate-free, projection-independent layout (containment tree + per-ligature required crossing-sequence); imports no geometry ("own the dimensionality")
- `elk_layout_engine.py` (+ `elk_worker.js`) — cut-aware ELK layout, the default projection; label-aware two-tier ligature router (cuts hard, label boxes soft)
- `tension_engine.py` / `tension_layout.py` — opt-in `?engine=tension` projection (a relation drawn *between* its arguments, the Peircean single-line reading)
- `clockwise_placement.py` — Peirce's writing convention: hooks drawn clockwise around the spot in ν-order (argument order in the geometry)
- `simple_svg_renderer.py` — LayoutDTO → SVG; draws the exact label boxes and cut curves the §3.3 test reads
- `layout_dto.py` — platform-independent layout DTO (carries cut boundary polylines for human-drawn cuts)
- `presentation_ops.py` — regime-3 algebra + the exact-correspondence geometry (`point_in_cut`, `cut_boundary`, `point_in_polygon`, label-box extents)
- `style_loader.py` — declarative visual style system (Dau / Peirce / Sowa)

> The Qt GUI and the old `unified_d3` engine were archived to `archive/qt-gui-2025/` in May 2026; the web app (`src/web_api/` + `src/web_viewer/`) is the canonical UI.

**Utilities:**

- `insertion_clipboard.py` — Persistent INS workflow clipboard
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
src/                  Core logic and engine (35+ production modules)
tests/                Pytest test suite (~960 passing, 45+ test files)
tools/                Quality tools, demos, and utilities
docs/                 Architecture documentation
docs/RETURN_TO_DEVELOPMENT.md  Context recovery guide for returning authors
tomos/                Canonical example corpus (87 items)
corpus/               Active working corpus
archive/              Archived legacy components
styles/               Visual style specifications (JSON)
```

---

## 🚀 Quick Start

### Install

```bash
git clone https://github.com/mijahauan/Arisbe.git
cd Arisbe
uv sync --extra dev --extra web   # Python 3.12; the `web` extra carries FastAPI/uvicorn
```

`uv sync` is exact — install **both** extras (`web` for the viewer/route tests, `dev` for the
test/quality tooling) or they get pruned.

### Launch the web viewer (canonical UI)

```bash
uv run uvicorn --app-dir src web_api.main:app --reload --port 8000
# Open http://localhost:8000/ in a browser.
```

The home page links the three live modes: **Organon** (`/organon`, the read-only archive),
**Ergasterion** (`/ergasterion`, the workshop), and **Agon** (`/agon`, the contest/interpretation
arena).

The Qt-based GUI (`arisbe.py`, `src/gui_clean/`) was archived to
`archive/qt-gui-2025/` in May 2026. The web viewer
(`src/web_api/` + `src/web_viewer/`) is the active surface.

### 📖 Documentation — the book / help

The full documentation is a single-source **book** (also served as browseable in-app help),
built with [Quarto](https://quarto.org) from the docs themselves (`docs/_quarto.yml`):

```bash
quarto render docs          # → docs/_book/ (HTML site)
```

Once rendered, the running app serves it at **http://localhost:8000/book/**. See
[docs/install.qmd](docs/install.qmd) for PDF/epub builds, and
[docs/ALPHA_RELEASE_PLAN.md](docs/ALPHA_RELEASE_PLAN.md) for the consolidation plan.

### Play the Endoporeutic Game (REPL)

```bash
uv run python -c "
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
# Full test suite
uv run pytest tests/ -q

# With verbose output
uv run pytest tests/ -v
```

### Quality and protection

```bash
# Quality gate
uv run python tools/quality_gate_system.py

# Core protection status
uv run python tools/core_protection_system.py --report

# Daily dashboard
uv run python tools/daily_quality_dashboard.py
```

### Demos and integration scripts

```bash
# Syllogism proof demo
uv run python tools/demo_syllogism_proof.py

# Round-trip translation demo
uv run python tools/demo_round_trip_translations.py
```

---

## 🗺️ Sub-application Status

The three modes are now best understood as **routes within the web app**;
the Qt implementation was archived in May 2026.

| Module | Status | Notes |
|---|---|---|
| **Organon** (Archive/browser) | ✅ **Live** | `web_api/routes/organon.py` + `web_viewer/organon.html` — read-only corpus archive at `/organon`. Both load and render boundaries §3.3-attested per request. |
| **Ergasterion** (Workshop) | ✅ **Live** | `web_api/routes/ergasterion.py` + `web_viewer/ergasterion.html` — composition route at `/ergasterion`. Regime-1 drafts (correspondence invariant suspended); promotion is the regime-1 → regime-2 boundary at which §3.3 attestation fires. Chain of rule applications persisted via `TomosService.save_uod_with_chain` (V1 linear chains, JSONL + per-state snapshots). |
| **Agon** (Endoporeutic Game) | ✅ **Live** | `web_api/routes/agon.py` + `web_viewer/agon.html` at `/agon` — the contest (hot-seat transformation game) and the interpretation register (choose a model M, peel G against it → verdict + witness/counterexample, the inverse pivot). REPL also available (`game_repl.py`); Z3-validated. |
| **Correspondence attestation** | ✅ **Live** | `correspondence_attestation.py` + hook in `web_api/services/layout_service.py` |

---

## 📊 Current State (June 2026)

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

**Linear-Graphical Correspondence (the central contract):**

- Specification: `docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md` (§3 properties,
  §4 three-regime scoping, §5 hard cases, §7 testable shapes)
- Property tests: `tests/test_correspondence_invariant.py` covers all
  six §7 shapes against every UoD in the tomos corpus
- Regime-3 production API: `src/presentation_ops.py` — vertex
  translation, cut reshape, ligature reroute, each raising
  `Regime3Violation` on attempted boundary crossings
- Runtime attestation: `src/correspondence_attestation.py`, hooked into
  `web_api/services/layout_service.py` so every (EGI, drawing) pair
  the user sees has been verified before leaving the service

**The exact-correspondence engine (Phases 1–4, June 2026):**

- The correspondence contract realized *geometrically* — every §3.3 property is an
  exact fact about the literal drawn picture, no proxy shape
  (`docs/EXACT_CORRESPONDENCE.md`)
- **Phase 1–2**: cut containment + ligature crossing tested on the rounded
  rectangle / inscribed ellipse the renderer actually draws (no corner void)
- **Phase 3**: every mark is an **extent** — predicate/constant **label boxes**
  (not anchor points) wholly within their area; no improper occlusion (text-on-text,
  cut-line straddle, line through a non-incident label, with **label-aware ligature
  routing** as the constructive partner); **argument order by clockwise placement**
  (Peirce's writing convention) with a single start anchor and a numeral toggle
- **Phase 4**: a cut can be carried as its **literal drawn polyline** — the
  foundation for human-drawn cuts — tested point-in-polygon by §3.3 and the reader,
  and hit-tested in the browser via `isPointInFill` (`areaAtPoint`)

**The three web modes (live):**

- **Organon** (`/organon`) — read-only corpus archive, load + render boundaries
  §3.3-attested per request
- **Ergasterion** (`/ergasterion`) — workshop / composition; regime-1 drafts; a graph
  reaches the corpus only via Agon or as a style-only reprojection
- **Agon** (`/agon`) — Endoporeutic Game arena (hot-seat V1)

**Testing:**

- **~960 tests passing**, ~35 skipped, across 45+ test files
- Quality gates and core protection active (17 protected modules)
- Comprehensive coverage: core data model, all six transformation rules,
  import/export round-trips, isomorphism engine, proof exercises
  (Alpha + Beta), rule interaction protocol, subgraph closure
  validation, §3.3 correspondence properties, regime-3 contract

### 🔧 In Progress / Next

- **The second-order crossing** *(the active frontier — deliberately paused)* —
  logic *about* the graphs themselves: quotation (a graph as an object, mention
  without force), `(forces s φ)`, `(superseded ⌜M⌝ …)`. The landscape is mapped
  ([docs/SECOND_ORDER_FRONTIER.md](docs/SECOND_ORDER_FRONTIER.md),
  [docs/SECOND_ORDER_LANDSCAPE_AND_POSITIONING.md](docs/SECOND_ORDER_LANDSCAPE_AND_POSITIONING.md)),
  the validation harness built (`second_order_check`), and the advance gates on two
  author decisions (the comprehension floor; how much to open the core). The
  **"Moses" beta** tags the completed first-order territory before this crossing.
- **Freeform composition canvas** *(shipped, including challenge mode)* — composition
  is draw-then-read: place/drag/erase typed marks (cut / relation / line-of-identity)
  at free positions, with no live EGI; the picture is read into a sign only at gate
  ① (`read_drawing` → validity → build EGI → "what it says"). **Live** in Ergasterion
  (`web_viewer/js/freeform-canvas.js` + `read-drawing`/`fix-drawing` routes), with a
  **Graph↔Argument** two-mode workspace, draw-time snapping, a fix-time validity pass
  (`drawing_validity`), the drawing→EGI builder (`drawing_to_egi`), the legible EGI
  diff (`egi_diff`), and **challenge mode** (draw a target freehand, graded by
  `same_graph` + the diff; `docs/FREEFORM_COMPOSITION_AND_LEARNING.md`).
- **Agon web arena** — surface the Endoporeutic Game engine (live as a REPL) as a
  web route
- **Math horizon** — the ∀x scaffold tactic (`derived_rules.py`) and selection-driven
  `fold` (`definitions.py`); corpus-import the math theories (ZFC + Peirce 1881)

---

## 📖 Development Notes

- EGI is the single source of truth; visual edits are presentation deltas (`LayoutDeltas`)
- Cuts determine spatial exclusion; child cuts create forbidden zones for parent-level elements
- Same-area ligatures must avoid cut collisions; cross-area ligatures may cross cut boundaries per EGI mappings
- Rendering order is fixed: Cuts → Predicates → Vertices → Ligatures
- Import pattern: `from module_name import ...` (not `from src.module_name import ...`)

---

## 👥 What Users Can Do with Arisbe

> **New to Arisbe?** [docs/ARISBE_IN_PRACTICE.md](docs/ARISBE_IN_PRACTICE.md) tells
> the story through the people who use it — teacher, student, researcher, logician,
> physician, and the editor preparing Peirce's manuscripts for publication — with a
> *what you can do now / when complete* split for each, plus six plain-language
> walkthroughs of the Know → Make → Contest cycle.

### For Logic Researchers & Academics

- Apply all six formal transformation rules with mathematical validation and Z3 soundness verification
- Verify logical equivalences across EGIF, CGIF, CLIF, FOPL representations
- Play the Endoporeutic Game as a formal proof procedure
- Serialize transformation sequences as proof notation (JSON)
- Export to academic formats (LaTeX/TikZ, SVG)

### For Students & Educators

- **Freeform composition** (Ergasterion `/ergasterion`): draw an existential graph by
  hand — cuts, relations, lines of identity — then ask "what does it say?" to read it
  into a determinate sign and see its linear form (or why it isn't yet well-formed),
  before fixing it and reasoning with the rules
- **Challenge mode**: pick a target linear form, draw it freehand, and get graded with
  `same_graph` + the legible diff — correspondence learned by doing
- **Test a graph against a world** (Agon `/agon`): choose a reference model M and ask
  "does G hold?" — the peel evaluates it outside-in to *holds / fails / independent*,
  names the witness or counterexample, and (with "Use rules") forward-chains M's rules
  so the syllogism works
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

### Current Focus (mid-2026)
- **Freeform composition canvas** *(built)*: draw logic by hand, read it into a
  determinate sign on demand (gate ①). Live in Ergasterion with a Graph↔Argument
  two-mode workspace, draw-time snapping, a fix-time validity pass, the drawing→EGI
  builder, the legible EGI diff, and **challenge mode** *(built)* — grade a freehand
  attempt against a tomos target
- **Agon interpretation register** *(built)*: the inning *given M, then G* — choose a
  reference model M (curated scenarios or corpus UoDs, optionally **materialized** so
  facts + Horn rules become testable), peel G against it to a three-valued verdict
  with witness/counterexample, and the **inverse pivot** ("in what domain does G
  hold?"). See `docs/GENERATION_AND_TESTING.md`, `docs/DOMAIN_ORACLE_AND_M.md`
- **Next**: **ontology-as-M** (materialize a T-box, peel/search against it) and the
  oracle's scale steps (demand-driven cache → horizon params → a remote SPARQL backing)

### Medium-term
- **Hypothesis-driven exhaustive transformation testing**: extend
  per-rule property tests from one deterministic site to full
  enumeration of applicable sites
- **The dialogical contest, in full**: an automated Grapheus (the peel supplies the
  model-respecting reply) and the warrant lifecycle (low → tested by surviving Agon)
- **Advanced visualization**: animated transformation sequences;
  alternative projections (3-D viewer, accessibility renderings)

### Long-term
- **Stylus drawing input** parsed back to a canonical EGI under the
  named projection conventions (would activate the parse direction of
  the correspondence map)
- **Educational platform**: learning management system for EG theory
- **Theorem prover bridge**: integration with Coq/Lean via CLIF

---

## 📚 References

- Dau, Frithjof. *Mathematical Logic with Diagrams* (2003).
- Peirce, C. S. *Existential Graphs* (Collected Papers).
- Sowa, J. F. *Existential Graphs: MS 514 by Charles Sanders Peirce* (2007).
