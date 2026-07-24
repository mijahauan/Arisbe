# Arisbe: Universes of Discourse
**Peirce's "Moving Pictures of Thought" Made Real**

An environment for **doing logic in pictures**, built around Charles S. Peirce's Existential Graphs with Frithjof Dau's formalization as the guarantor of correctness. Arisbe elevates logical diagrams from static notation to **living processes of inquiry** - complete universes of discourse where justification, transformation, and meaning unfold through dialogue and formal rules.

The central engineering and research problem the codebase solves: **inerrant correspondence between an EGI's linear written form and its graphical drawn form**. The contract is stated in [docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md](docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md), tested against tomos, exposed as a refusal-bearing API in [src/presentation_ops.py](src/presentation_ops.py), and runtime-attested at the web service boundary by [src/correspondence_attestation.py](src/correspondence_attestation.py). When picture and proposition come apart, the system refuses to serve a drawing it can't attest.

**The exact-correspondence engine (complete, June 2026).** That contract is now realized *geometrically*: a cut **is its drawn curve**, every mark is an **extent** (label box, not anchor point), and the whole §3.3 invariant — cut containment, ligature crossing-sequence, label/numeral extents, no improper occlusion, argument order by clockwise placement — is checked as a set of **exact facts about the literal drawn picture**, no proxy shape. A cut can be an arbitrary human-drawn polyline, tested point-in-polygon by both the attestation and the reader and hit-tested in the browser via `isPointInFill`. See [docs/EXACT_CORRESPONDENCE.md](docs/EXACT_CORRESPONDENCE.md). It is the foundation the **freeform composition canvas** (draw logic by hand, read it into a sign on demand — shipped, live in Ergasterion) was built on.

**The validity discipline (July 2026).** The attested corpus now enacts a standing discipline about *where saying happens*: nothing contingent stands at depth 0 — the sheet is the world's level, carrying only what the calculus itself delivers — and a domain model **M** resides as a *supposition* at level 1 of a standing world-scroll `~[ M ~[ ] ]`. Every change to M is an explicit rule-licensed chain step (admission = insertion into the scroll's antecedent; revision = withdrawal of the whole world, the history keeping the old one) and every verdict is a recorded, forever-recomputable peel. See [docs/M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE.md](docs/M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE.md) and the standing gate `tests/test_corpus_polarity_discipline.py`. **The active frontier** is now **mention-ascent** — logic about the graphs themselves (quotation, `(forces s φ)`) — mapped in [docs/SECOND_ORDER_FRONTIER.md](docs/SECOND_ORDER_FRONTIER.md) and deliberately paused on two author decisions; the "Moses" beta tags the completed first-order territory before that ascent.

---
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/mijahauan/Arisbe)
[![Release](https://img.shields.io/badge/release-v2.0.0--beta.1%20%22Moses%22-blue)](https://github.com/mijahauan/Arisbe/releases/tag/v2.0.0-beta.1)
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
- Search and browse the archive

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

👉 **New user? Start here**: [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) — a role-aware
on-ramp (no logic background assumed) that branches by reader: newcomer / ontologist / logician /
mathematician / Peirce scholar
👉 **Full vision**: [VISION_AND_SCOPE.md](docs/VISION_AND_SCOPE.md)
👉 **What actually works, today**: [CAPABILITY_MAP.md](docs/CAPABILITY_MAP.md) — the living
capability/maturity table this README summarizes; it is the source of truth when the two disagree
👉 **What's next**: [ROADMAP.md](docs/ROADMAP.md)
👉 **Correspondence spec**: [LINEAR_GRAPHICAL_CORRESPONDENCE.md](docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md)
👉 **For scholars & Peirce researchers**: [ARISBE_FOR_SCHOLARS.md](docs/ARISBE_FOR_SCHOLARS.md)
👉 **AI assistance**: [AI_CONDUCT_GUIDELINES.md](AI_CONDUCT_GUIDELINES.md)

---

## 🔒 **Development Guidelines**

- **📚 API Documentation**: `docs/ARISBE_CORE_API_REFERENCE.md`
- **🛡️ Core Protection**: 14 protected modules (the genuine calculus core — see
  `tools/core_protection_system.py --report`); 4,100+ passing tests across the suite
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

`src/` now holds 120+ modules; the list below is a curated tour of the bedrock, not the full
inventory. For the complete, current module ↔ test map, see
[docs/CAPABILITY_MAP.md](docs/CAPABILITY_MAP.md) or [CLAUDE.md](CLAUDE.md).

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

**Tomos and UoD Management:**

- `universe_of_discourse.py` — `UniverseOfDiscourse` entity (synchronic + diachronic + layout)
- `tomos_service.py` — Unified API for browsing and loading tomos
- `tomos_index.py` — Index-based fast tomos navigation

**Layout and Visualization:**

- `natural_layout.py` — coordinate-free, projection-independent layout (containment tree + per-ligature required crossing-sequence); imports no geometry ("own the dimensionality")
- `elk_layout_engine.py` (+ `elk_worker.js`) — cut-aware ELK layout, the default projection; label-aware two-tier ligature router (cuts hard, label boxes soft)
- `tension_engine.py` / `tension_layout.py` — opt-in `?engine=tension` projection (a relation drawn *between* its arguments, the Peircean single-line reading)
- `clockwise_placement.py` — Peirce's writing convention: hooks drawn clockwise around the spot in ν-order (argument order in the geometry)
- `simple_svg_renderer.py` — LayoutDTO → SVG; draws the exact label boxes and cut curves the §3.3 test reads
- `layout_dto.py` — platform-independent layout DTO (carries cut boundary polylines for human-drawn cuts)
- `presentation_ops.py` — regime-3 algebra + the exact-correspondence geometry (`point_in_cut`, `cut_boundary`, `point_in_polygon`, label-box extents)
- `style_loader.py` — declarative visual style system (Dau / Peirce / Sowa)

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
src/                  Core logic and engine (120+ production modules)
tests/                Pytest test suite (4,100+ passing, 144 skipped)
tools/                Quality tools, demos, and utilities
docs/                 Architecture documentation (see CAPABILITY_MAP.md for what's live)
docs/RETURN_TO_DEVELOPMENT.md  Context recovery guide for returning authors
tomos/                The canonical example set (87 items)
corpus/               Imported ontologies, domain models, and working graphs
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

### 📖 Documentation — the book / help

The full documentation is a single-source **book** (also served as browseable in-app help),
built with [Quarto](https://quarto.org) from the docs themselves (`docs/_quarto.yml`):

```bash
quarto render docs          # → docs/_book/ (HTML site)
```

Once rendered, the running app serves it at **http://localhost:8000/book/**. See
[docs/install.qmd](docs/install.qmd) for PDF/epub builds. The consolidation plan
([docs/ALPHA_RELEASE_PLAN.md](docs/ALPHA_RELEASE_PLAN.md)) shipped as the **v2.0.0-beta.1 "Moses"
release** (first full-suite CI pass) — see [docs/ROADMAP.md](docs/ROADMAP.md) for what's current now.

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

**4,125 passed, 144 skipped, 0 failed** as of this writing (`uv run pytest tests/ -q`, ~23 min).
The mathematical core subset (`egi_core_dau`, `formal_transformation_rules`, `rule_interaction`,
`subgraph_closure_validator`, `graph_isomorphism_engine`, the Beta/logical proof exercises) must
always pass — a failing core test is a real correctness defect, never test noise.

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

The three modes are routes within the web app.

| Module | Status | Notes |
|---|---|---|
| **Organon** (Archive/browser) | ✅ **Live** | `web_api/routes/organon.py` + `web_viewer/organon.html` — read-only archive at `/organon`. Both load and render boundaries §3.3-attested per request. |
| **Ergasterion** (Workshop) | ✅ **Live** | `web_api/routes/ergasterion.py` + `web_viewer/ergasterion.html` — composition route at `/ergasterion`. Regime-1 drafts (correspondence invariant suspended); promotion is the regime-1 → regime-2 boundary at which §3.3 attestation fires. Chain of rule applications persisted via `TomosService.save_uod_with_chain` (V1 linear chains, JSONL + per-state snapshots). |
| **Agon** (Endoporeutic Game) | ✅ **Live** | `web_api/routes/agon.py` + `web_viewer/agon.html` at `/agon` — the contest (hot-seat transformation game) and the interpretation register (choose a model M, peel G against it → verdict + witness/counterexample, the inverse pivot). REPL also available (`game_repl.py`); Z3-validated. |
| **Correspondence attestation** | ✅ **Live** | `correspondence_attestation.py` + hook in `web_api/services/layout_service.py` |

---

## 📊 Capabilities Snapshot

Arisbe is under active development. The **v2.0.0-beta.1 "Moses" release** (2026-07) tags the
completed first-order territory — the full Dau calculus, all three web modes, the exact
correspondence engine, and the validity discipline described below — ahead of the project's
active frontier: **mention-ascent**, logic *about* the graphs themselves (quotation,
`(forces s φ)`). That crossing is deliberately paused pending two author decisions; see
[docs/SECOND_ORDER_FRONTIER.md](docs/SECOND_ORDER_FRONTIER.md).

**This section is a summary, not the record.** [docs/CAPABILITY_MAP.md](docs/CAPABILITY_MAP.md) is
the living, per-capability table (status + module + test home for everything below and more) —
treat it as the source of truth where the two disagree. [docs/ROADMAP.md](docs/ROADMAP.md) is
what's next, organized as four workstreams (Understand · Share · Run · Use).

### The bedrock (shipped)

- **Complete Dau formalism**: 6+1 component `RelationalGraphWithCuts`, all six transformation
  rules (ERA, INS, IT±, DC±), Beta-aware (lines of identity crossing cut boundaries), a headless
  `RuleInteraction` protocol, Z3-backed soundness checking
- **Round-trip linear forms**: EGIF ↔ CGIF ↔ CLIF ↔ FOPL ↔ EGI (57+ / 40+ / 35+ tomos examples)
- **Linear↔graphical correspondence** — the project's central contract — stated
  ([docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md](docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md)), tested
  tomos-wide, and runtime-attested at the web boundary; realized *geometrically* — cuts as drawn
  polylines, label-box extents, clockwise argument order, no proxy shape
  ([docs/EXACT_CORRESPONDENCE.md](docs/EXACT_CORRESPONDENCE.md))
- **Freeform composition & challenge mode** — draw an EG by hand (cut / relation /
  line-of-identity), read it into a sign on demand, get graded against a target
  ([docs/FREEFORM_COMPOSITION_AND_LEARNING.md](docs/FREEFORM_COMPOSITION_AND_LEARNING.md))
- **The three web modes** — Organon (read-only archive), Ergasterion (workshop, incl. freeform
  composition), Agon (Endoporeutic Game — hot-seat contest + the interpretation register: peel a
  graph against a chosen model M to a three-valued verdict with witness/counterexample)
- **The validity discipline & M-residence** — a standing discipline for where contingent claims
  may live, every change to a model an explicit rule-licensed step, every verdict a recomputable
  peel ([docs/M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE.md](docs/M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE.md))
- **Ontology import**: OWL/RDF/CLIF → EGI, with T-box subsumption decided by `theory_query.entails`

### Beyond the core calculus

More recent work extends the project past reasoning with one graph at a time:

- **The automated Endoporeutic Game** — the game played *autonomously*: a proposer voices a claim,
  the peel tests it against a developing model, a panel negotiates how the model should change, and
  disuse decays what's no longer used. Runs against real, live sources (Wikidata's edit stream,
  weather forecasts, wiki edit-war disputes), bounded and checkpointed for continuous operation.
  See [docs/AUTOMATED_MODEL_DEVELOPMENT.md](docs/AUTOMATED_MODEL_DEVELOPMENT.md) and
  [docs/AUTOMATED_ENDOPOREUTIC_GAME.md](docs/AUTOMATED_ENDOPOREUTIC_GAME.md).
- **A knowledge measure** — a four-part, fractal measure of a model's track record, durability,
  compression, and use/decay, read the same way from a single fact up to a whole reasoning
  community (never a scalar ranking, never truth itself). See
  [docs/THE_MEASURE_OF_KNOWLEDGE.md](docs/THE_MEASURE_OF_KNOWLEDGE.md).
- **MCP verifier** — Arisbe's mechanical referee exposed as [Model Context Protocol](https://modelcontextprotocol.io)
  tools (`check_egif`, `peel`, `apply_rule`, `attest`) so other AI agents can call it directly —
  *the LLM argues, the calculus decides*. See [docs/MCP_VERIFIER.md](docs/MCP_VERIFIER.md).
- **Accessible (non-visual) projection** — a genuine ARIA tree reading of a graph with an
  outside-in spoken reading; the repo's first accessibility surface.

### The active frontier

**Mention-ascent** — logic about the graphs themselves, rather than logic within one — is mapped
in [docs/SECOND_ORDER_FRONTIER.md](docs/SECOND_ORDER_FRONTIER.md) and deliberately paused pending
two author decisions (how much comprehension to allow; how much of the protected core to open).
See [🧪 Testing](#-testing) below for the current test-suite figures.

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

- Large-scale tomos management with `TomosService`
- DAG-based transformation history for branching inquiry workflows
- Bridge between diagrammatic (EGI) and symbolic (FOPL/CLIF) reasoning

---

## 🗓️ Development Roadmap

The program is organized as four workstreams, named by verb — see
[docs/ROADMAP.md](docs/ROADMAP.md) for the full, current picture (each item there carries either
an **(author decision)** tag or a concrete next action):

- **Understand** — keep the doctrine that grounds everything else legible and ratified.
- **Share** — push the project's own boundary outward: the documentation sweep and a first
  publication choice (candidate theses include the §3.3 correspondence discipline, modality
  without Gamma, and the automated Endoporeutic Game as a live model-development architecture).
- **Run** — strengthen the mechanism itself: import/export unified, the interaction layer
  instrumented to match the interior.
- **Use** — the people-facing edge: UX fixes gated by
  [docs/UI_TRANSPARENCY_CHARTER.md](docs/UI_TRANSPARENCY_CHARTER.md)'s seven testable principles.

Longer-term directions not yet scheduled into a workstream: stylus drawing input parsed back to a
canonical EGI, an educational platform / learning-management integration, and a theorem-prover
bridge (Coq/Lean via CLIF).

---

## 📚 References

- Dau, Frithjof. *Mathematical Logic with Diagrams* (2003).
- Peirce, C. S. *Existential Graphs* (Collected Papers).
- Sowa, J. F. *Existential Graphs: MS 514 by Charles Sanders Peirce* (2007).
