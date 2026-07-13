# AGENTS.md

## Core Protection System
- **14 protected core modules** — cannot be modified without explicit authorization (`tools/core_protection_system.py` is the source of truth; the EGIF/CGIF/CLIF parsers were *removed* from the set on 2026-06-27 as application-level I/O, and the correspondence enforcers `correspondence_attestation` / `presentation_ops` / `natural_layout` were added)
- **The mathematical core suite must always pass** — the subset covering `egi_core_dau`, `formal_transformation_rules`, `rule_interaction`, `subgraph_closure_validator`, `graph_isomorphism_engine`, and the Beta/logical proof exercises. A failing core test is a real correctness problem, never test infrastructure.
- **Commit gate runs the core math subset** (~150 headless tests, < 30 s); the full suite is for CI / manual runs (`uv run pytest tests/ -q`, ~12 min — see Testing Requirements)
- **Check protection status**: `python tools/core_protection_system.py --report`
- **Override protection** (authorized changes only): `touch .core_modification_authorized`

## 📚 Documentation System
- **Documentation does NOT auto-update.** The generators below refresh *derived* artifacts (the
  API reference from the protected-module set); everything else — this file included — goes
  stale unless a change updates it. Treat a doc claim as a *hypothesis about the code*, and
  check it against the code when it matters. (This section was itself ~9 months stale until
  2026-07-13, when it still taught an import for an engine archived in May 2026.)
- **Which doc is authoritative when they disagree**: the **code** > `CLAUDE.md` (the module map)
  > `CURRENT_PLAN.md` (▶ NEXT SESSION, the live status) > everything else. `AGENTS.md` is a
  patterns cheat-sheet, not a source of truth.
- **API reference (derived, regenerate it)**: `uv run python tools/extract_core_api.py`
- **Context awareness system**: `tools/context_awareness_system.py` prevents reinvention
- **Return-to-development guide**: `docs/RETURN_TO_DEVELOPMENT.md` for context recovery after a break
- **IDE integration**: VS Code tasks (`.vscode/tasks.json`) for instant context checks

## 📚 API Discovery Protocol
- **NEVER guess function signatures** - Use `docs/ARISBE_CORE_API_REFERENCE.md` for exact signatures
- **Regenerate**: `uv run python tools/extract_core_api.py` (reads the protected-modules set from `tools/core_protection_system.py`)
- **Usage patterns**: See `docs/CORE_API_USAGE_GUIDE.md` for common development patterns
- **Quick function lookup**: `grep -i "function_name" docs/ARISBE_CORE_API_REFERENCE.md`

## 🧪 Testing Requirements
- **Quality check**: `python tools/quality_gate_system.py` (runs automatically on commit)
- **System status**: `python tools/daily_quality_dashboard.py`
- **Full suite**: `uv run pytest tests/ -q` — 148 test files, ~3,100 tests, ~16 min. Measured
  2026-07-13: **3,018 passed · 96 skipped · 1 xfailed**.
- **Core math subset**: what the commit gate runs (~150 headless tests, < 30 s). **This is the
  one that must always be green** — a failure here is a real correctness problem, never test
  infrastructure.
- **Two known non-regressions** (don't be alarmed; don't "fix" them blindly):
  - The `eg_reader` **clockwise trio** (`test_clockwise_*`, `test_round_trip[peirce-style1]`)
    is a *seed-dependent* flake — its root cause is argument-order recovery from ELK geometry.
    Pre-existing, documented in `CURRENT_PLAN.md`, and it does not gate the core suite.
  - The **e2e tests error without Chromium** (`test_primer_e2e`, `test_*_e2e`). Run
    `uv run playwright install chromium` to enable them; otherwise they are expected to
    skip/error and are not a code problem.

### Battle-Tested Import/Export Infrastructure
**Status**: ✅ PRODUCTION - Comprehensive test coverage across corpus
- **EGIF**: Tested on 57+ tomos examples (parse → generate → parse)
- **CGIF**: Tested on 40+ tomos examples (ISO/IEC standard compliance)
- **CLIF**: Tested on 35+ tomos examples (Common Logic standard)
- **FOPL**: Round-trip translation tests (Φ/Ψ bidirectional)
- **Round-trip**: All formats tested for stability and variable preservation
- **Test files**: `test_tomos_parsing.py`, `test_corpus_conformance.py`, `test_variable_order_alignment.py`, `test_variable_name_consistency.py`

## 🏗️ Build and Development
- **Environment**: managed by `uv` (Python 3.12). Run `uv sync --extra dev` once, then use `uv run <cmd>` (or `source .venv/bin/activate`).
- **Dependencies**: See `pyproject.toml`
- **Core modules location**: `src/` (14 protected modules)
- **Test location**: `tests/` (148 test files)

## 📋 Code Style and Conventions
- **Import pattern**: `from module_name import function_name` (not `from src.module_name`)
- **EGI immutability**: Use `.with_vertex()`, `.with_edge()` patterns (not `.add_*()`)
- **Error handling**: Check return values, handle None cases
- **Documentation**: Follow existing docstring patterns
- **Doc shorthand**: expand on first use in book chapters (write "the correspondence check
  (§3.3)", not bare "§3.3"); a bare "§N" means *this* doc's section — name the doc for cross-refs;
  reserve `Gx`/`Rx`/`Fⁿ`/`Pⁿ` tags for the dev docs that own them. Decoder:
  [docs/GLOSSARY.md](docs/GLOSSARY.md#notation--reference-numbers).

## 🧠 Context Recovery
- **Returning after a break?** Read `docs/RETURN_TO_DEVELOPMENT.md` — the 5-minute checklist for re-anchoring on the code, the state of the suite, and the known follow-ups.
- **Quick status**: `python tools/core_protection_system.py --report`

## 🔧 Essential Tools
- **Daily quality dashboard**: `python tools/daily_quality_dashboard.py`
- **Core protection check**: `python tools/core_protection_system.py`
- **API documentation generator**: `python tools/extract_core_api.py`
- **Coherence reminders**: `python tools/coherence_reminder_system.py`
- **Context awareness system**: `python tools/context_awareness_system.py`
- **Living documentation generator**: `python tools/living_documentation_generator.py`

## 📊 Quality Gates
- **Pre-commit hooks**: Automatically run quality checks
- **Core protection**: Blocks unauthorized changes to protected modules
- **Test validation**: the core math subset must pass (the commit gate enforces it)
- **Syntax checking**: Zero syntax errors required

## 🗺️ Subsystem map — where to look

**`CLAUDE.md` carries the authoritative, per-module map** (and `docs/CAPABILITY_MAP.md` says
what works, where, and what guards it). Do not duplicate that list here — it drifts. The
coarse geography:

- **The calculus** (mostly protected): `egi_core_dau` · `formal_transformation_rules` (the six
  Dau rules) · `rule_interaction` · `subgraph_closure_validator` · `ligature_manipulation_rules`
  · `graph_isomorphism_engine`.
- **Correspondence** (the project's central problem): `natural_layout` (coordinate-free ground
  truth) · `correspondence_attestation` (the runtime §3.3 check) · `presentation_ops` (the
  regime-3 algebra) · `elk_layout_engine` + `simple_svg_renderer` (the projection) ·
  `eg_reader` (drawn → EG, the inverse) · `drawing_validity` + `drawing_to_egi` (freeform
  fix = read) · `egi_diff` + `challenge_mode` (grading a drawing in EG vocabulary).
- **Diachrony**: `universe_of_discourse` · `egi_transformation_history` (the branching DAG) ·
  `proof_authoring` (`ProofChain`) · `tomos_service` (the corpus boundary) · `modal_query`
  (◇/□ and `settlement` read off the DAG).
- **The Agon / model side**: `semantic_game` (the peel; three-valued verdicts) ·
  `domain_oracle` (M is queried, not held) · `model_materialization` · `theory_query` ·
  `model_revision` (how M changes through dialogue) · `agon_evolution` (the automated loop) ·
  `agon_llm` (three LLM roles under the mechanical referee) · `agon_metalearning` · the
  membranes (`discourse_` / `resolving_` / `wiki_dispute_`) · `live_runner` +
  `wikidata_source` / `weather_source` / `sports_source` (the live runs; see `runs/`).
- **I/O and export**: the four linear formats (EGIF / CGIF / CLIF / FOPL) ·
  `domain_model_importer` (OWL/RDF/CLIF → UoD) · `peirce_latex` (authentic-Peirce TikZ) ·
  `eg_to_english` (an English *gloss*, never a fifth form).
- **The frontier** (de-risked, not crossed): `second_order_check` · `reference_node` ·
  `schema.py` (the φ-hole).

## 🎯 Common Development Patterns

### Creating EGI
```python
from egi_core_dau import create_empty_graph, create_vertex, create_edge
egi = create_empty_graph()
vertex = create_vertex(label="Human", is_generic=False)
egi = egi.with_vertex(vertex)
```

### Saving/Loading EGI
```python
from egi_io import save_egi_json, load_egi_json
save_egi_json(egi, "filename.json")
loaded_egi = load_egi_json("filename.json")
```

### ELK Layout Engine (PRODUCTION)
```python
from elk_layout_engine import ELKLayoutEngine
from style_loader import load_default_style

# Load style
style = load_default_style()

# Generate the layout DTO (cut-aware ELK; the default layout path)
engine = ELKLayoutEngine()
dto = engine.generate_layout(egi, style)

# DTO structure:
# - dto.vertex_positions: Dict[ElementID, Point]
# - dto.predicate_positions: Dict[ElementID, Point]
# - dto.cut_bounds: Dict[ElementID, BoundingBox]
# - dto.ligature_paths: List[LigaturePath]
```

### Style Management
```python
from style_loader import load_default_style, load_style, list_available_styles

# The default style, or a named one
style = load_default_style()
style = load_style("dau-classic@1.0")      # see list_available_styles()

# Styles are data (StyleSpecification), consumed by the layout engine + renderer.
# The web layer resolves the name for you: GET /diagrams/…?style=<name>
```

### Transformation Rules (Direct API)
```python
from formal_transformation_rules import DeiterationRule, TransformationContext
rule = DeiterationRule()
context = TransformationContext(source_egi=egi, target_area="sheet", ...)
result = rule.apply_transformation(context)
```

### RuleInteraction Protocol (Headless Stepwise Proofs)
```python
from rule_interaction import begin_interaction, advance_interaction, apply_interaction

# IT+: iterate subgraph from source area into destination area
state = begin_interaction("IT+", egi)
r1 = advance_interaction(state, [edge_id])      # select source
r2 = advance_interaction(state, dest_area_id)    # select destination
result = apply_interaction(state)
new_egi = result.result_egi

# ERA: erase subgraph from positive area
state = begin_interaction("ERA", egi)
r = advance_interaction(state, [edge_id])        # select elements
result = apply_interaction(state)
```

### Beta Graphs (Lines of Identity / FOL)
```python
from egif_parser_dau import parse_egif

# ∀x(Human(x) → Mortal(x)) — one shared vertex across cut boundary
egi = parse_egif("~[ (Human *x) ~[ (Mortal x) ] ]")
assert len(egi.V) == 1  # Single shared vertex

# Closure validation with Beta awareness
from subgraph_closure_validator import SubgraphClosureValidator
validator = SubgraphClosureValidator(egi)
analysis = validator.analyze_closure(
    selection, allow_expansion=True,
    context_area=inner_cut_id)  # vertices in ancestor areas are free
```

### Import/Export - Battle-Tested Production Modules (✅ 57+ tomos examples tested)
**Status**: ✅ PRODUCTION - All parsers/generators validated across extensive tomos  
**Documentation**: `docs/IMPORT_EXPORT_FORMATS.md` for complete reference

**EGIF (Extended Graph Interchange Format)**:
```python
from egif_parser_dau import parse_egif
from egif_generator_dau import generate_egif

# Import
egi = parse_egif(egif_text)

# Export
egif_text = generate_egif(egi)
```

**CGIF (Conceptual Graph Interchange Format - ISO standard)**:
```python
from cgif_parser_dau import parse_cgif
from cgif_generator_dau import generate_cgif

# Import
egi = parse_cgif(cgif_text)

# Export
cgif_text = generate_cgif(egi)
```

**CLIF (Common Logic Interchange Format - ISO standard)**:
```python
from clif_parser_dau import parse_clif
from clif_generator_dau import generate_clif, generate_clif_with_quantification

# Import
egi = parse_clif(clif_text)

# Export
clif_text = generate_clif(egi)
clif_text = generate_clif_with_quantification(egi)  # Explicit quantifiers
```

**FOPL (First-Order Predicate Logic - Dau Chapter 18)**:
```python
from chapter18_fopl_translation import fopl_to_egi, egi_to_fopl

# Import (Ψ translation: FOPL → EGI)
egi = fopl_to_egi(formula_str)

# Export (Φ translation: EGI → FOPL)
fopl_text = egi_to_fopl(egi)
```

**JSON (EGI with Layout Deltas)**:
```python
from egi_io import load_egi_json, save_egi_json

# Import
egi = load_egi_json("filename.json")

# Export (preserves layout_deltas)
save_egi_json(egi, "filename.json")
```

**LaTeX/TikZ (Academic Publication Format)**:
```python
from export.tikz_exporter import generate_tikz

# Export as standalone LaTeX document
latex_content = generate_tikz(render_commands, standalone=True)

# Export as TikZ picture only (for inclusion in documents)
tikz_picture = generate_tikz(render_commands, standalone=False)
```

**Testing**: All formats tested with:
- ✅ Tomos parsing (57+ EGIF, 40+ CGIF, 35+ CLIF examples)
- ✅ Round-trip stability (parse → generate → parse)
- ✅ Variable name preservation
- ✅ Variable order alignment across formats
- ✅ Nested cut handling
- ✅ Mixed constants and variables

### Tomos Management (the corpus API)
**Documentation**: `docs/UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md`, `docs/CORE_API_USAGE_GUIDE.md`, `docs/DAG_HISTORY_ARCHITECTURE.md`

The canonical corpus lives in **`tomos/`** (28 UoDs). `TomosService` is the single API, and it
**attests the correspondence check (§3.3) at the save and load boundaries** — a refusal aborts
before any disk write, so there is never a half-saved or unattested record.

**Browse & load (Organon)**:
```python
from pathlib import Path
from tomos_service import TomosService

service = TomosService(Path("tomos"))          # the corpus root

uods = service.list_uods()                     # index-based, fast
uod = service.load_uod(uod_id, load_history=True)   # attests on load
chain = service.load_chain(uod_id)             # the worked TransformationChain, if any
```

**Persist a worked chain (the boundary that attests)**:
```python
service.save_uod_with_chain(uod, chain, provenance=prov)   # §3.3 fires inside save_uod
service.save_annotations(uod, annotations)
```

**Author a chain by locator (the readable path — see `proof_authoring.py`)**:
```python
from proof_authoring import ProofChain
from universe_of_discourse import UoDCategory

pc = ProofChain.from_egif('(cloudy) (cold)')
pc.apply("ERA", select=lambda g: nav.child_edges(g, g.sheet)[0])   # a rule by locator
pc.at("s0")                                    # rewind → the next apply FORKS the DAG
chain, uod = pc.to_uod(uod_id="…", name="…", description="…",
                       category=UoDCategory.DOMAIN_MODEL)
```

**Key invariants**:
- The UoD — not a static EGI — is the fundamental entity: a **diachronic** process
  (`State_n = (EGI_n, LayoutDeltas_n)`) carrying its own branching DAG history.
- History is a **DAG, not a sequence**: two chain steps sharing a `from_state_id` are a fork;
  `modal_query` reads ◇/□ (and `settlement`) straight off that shape.

## 🚨 Before you write code — avoid reinventing

- **Check what exists first**: `uv run python tools/context_awareness_system.py --check "task description"`
- **Look up the real signature** (never guess): `grep -i "function_name" docs/ARISBE_CORE_API_REFERENCE.md`,
  patterns in `docs/CORE_API_USAGE_GUIDE.md`
- **Check the plan**: `CURRENT_PLAN.md` (▶ NEXT SESSION) — the work may already be queued, or done
- **When a doc and the code disagree, the code wins** — and then *fix the doc* (see the
  documentation section above; that is how this file rotted)

## ⚠️ Critical Warnings
- **DO NOT** modify files in protected core modules without authorization
- **DO NOT** bypass quality gates unless using "WIP:" commit prefix
- **DO NOT** guess at function signatures - they are documented
- **DO NOT** ignore failing core tests - they indicate real mathematical issues
- **DO NOT** reinvent existing solutions - use context awareness system first
- **DO NOT** serve or persist an (EGI, drawing) pair without the correspondence check — the
  attestation hooks in `layout_service` and `tomos_service` exist precisely so that a picture
  and its proposition can never silently diverge. Read
  `docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md` before touching anything that produces or consumes
  that pair.
- **DO NOT** route a graph from the workshop into the corpus directly — the mode contract
  says it earns the corpus through Agon, or as a style-only reprojection of an already-attested
  graph. §3.3 attests *correspondence, not truth*.

## 🏆 Success Indicators
- The core math suite green; the full suite green in CI
- Quality dashboard shows "EXCELLENT" status
- Core protection system shows "CLEAN" status
- Zero syntax errors across all source files

## 📖 Mathematical Foundation
- **Dau Chapter 14/15**: Formal transformation rules
- **Dau Chapter 16-17**: Ligature algorithms and soundness
- **Dau Chapter 18**: Linear format parsing/generation
- **Dau Chapter 20**: Syntactic equivalence checking
- **Dau Chapter 21**: Diagram interaction — see `docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md` (the central contract) and `docs/EXACT_CORRESPONDENCE.md`

## 🏗️ Layout Engine Architecture
- **ELK Layout Engine**: `src/elk_layout_engine.py` (+ `src/elk_worker.js`) — **THE PRODUCTION ENGINE**, the default layout path. Cut-aware ELK; also `rebuild_ligature_anchors` (re-derive ligature endpoints after a regime-3 move).
- **Alternative projection (opt-in)**: `src/tension_engine.py` — `TensionLayoutEngine` (`?engine=tension`), hierarchical constrained stress placing a relation *between* its arguments (the Peircean single-line reading). §3.3-gated with ELK fallback.
- **SVG Renderer**: `src/simple_svg_renderer.py` — LayoutDTO → SVG with Dau-compliant styling.
- **The web boundary**: `web_api/services/layout_service.py` wraps the engine + renderer and **attests §3.3 on every served (EGI, drawing) pair** (`correspondence_attestation.attest_correspondence`). Never bypass it when serving a layout.
- **LayoutDTO Structure** (`src/layout_dto.py` — platform-independent, shared by engines and renderers):
  - `vertex_positions`: Dict[ElementID, Point]
  - `predicate_positions`: Dict[ElementID, Point]
  - `cut_bounds`: Dict[ElementID, BoundingBox]
  - `ligature_paths`: List[LigaturePath]
  - `area_hierarchy`: Dict[ElementID, Set[ElementID]]
- **Coordinate-free ground truth**: `src/natural_layout.py` — the containment tree + per-ligature crossing-sequence the drawing is a *projection* of. A renderer is pluggable; this layer imports no geometry.
- **ARCHIVED (do not import)**: the Qt-era `unified_d3_engine.py` / `unified_d3_worker.js` were archived to `archive/qt-gui-2025/` (May 2026) together with the Qt GUI. They are **not** in `src/` — code or docs referencing `UnifiedD3Engine` are stale (its design notes went to the archive with it).

## 🎮 The three modes — how they reach the calculus (web)

The Qt-era `DiagramController` was archived with the GUI (`archive/qt-gui-2025/`); the web
app is the canonical UI. The layering that replaced it:

- **The engine stays headless.** `endoporeutic_game.py` (Agon), `rule_interaction.py` /
  `formal_transformation_rules.py` (the six Dau rules), `proof_authoring.py` — none of them
  know about HTTP, sessions, or drawings.
- **A session manager owns the state.** `web_api/services/agon_session_manager.py` holds one
  stateless engine instance + per-game `GameState`; `ergasterion_session_manager.py` does the
  same for workshop sessions. This is the *only* layer that may hold engine state.
- **Routes are the boundary.** `web_api/routes/{organon,ergasterion,agon}.py` serve the pages
  and mediate every call into the calculus. `layout_service.py` attests §3.3 on every served
  (EGI, drawing) pair.
- **The pages are views.** `web_viewer/*.html` + `js/` speak only HTTP; they hold no logical
  state and never import a Python object. `diagram-viewer.js` is the one shared pan/zoom
  component all three modes use.
- **The invariant**: nothing in `web_viewer/` — and nothing in `routes/` — may hold engine
  state. It goes through a session manager, or it does not happen.
- **The three modes** (conceptual, per CLAUDE.md): **Organon** (read-only archive),
  **Ergasterion** (workshop / composition, regime-1 drafts), **Agon** (the contest + the
  interpretation register). A graph reaches the attested corpus only through Agon or as a
  style-only reprojection — there is no direct workshop→corpus route.

## 🔄 The three regimes, and regime-3 (presentation) editing

The correspondence invariant is **scoped, not monolithic** (`docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md`):

| Regime | Where | The invariant |
|---|---|---|
| **1 · composition** | Ergasterion drafts, the freeform canvas before gate ① | suspended (there is no EGI yet) |
| **2 · asserted / canonical** | Agon, Organon, every rule application | **mandatory**, attested at runtime |
| **3 · presentation-only** | any appearance nudge | **always free** — preserved by construction |

**Regime 3 is an algebra, not a free-for-all.** `presentation_ops` exposes the only legal
appearance moves, each of which *refuses* (raises `Regime3Violation`) rather than let a mark
cross a boundary it must not:

```python
from presentation_ops import (move_vertex, move_predicate, reshape_cut,
                              move_cut, reroute_ligature, Regime3Violation)

dto = move_vertex(egi, dto, vertex_id, (250.5, 180.3))   # refuses if it leaves its area
dto = move_cut(egi, dto, cut_id, dx, dy)                 # rigid translate of a cut + contents
```

- **The EGI never changes** under a regime-3 move — only the drawing. Meaning is untouched by
  construction, which is *why* the moves are free.
- **Persistence**: a nudge is recorded as a `PresentationDelta` (`presentation_deltas.record_delta`),
  replayed with `apply_deltas`, inherited across transformations (`merge_inherited`), and
  crystallised onto untouched siblings by `extrapolate_deltas` (the style ladder). Saved
  arrangements ride along with the UoD.
- **State_n = (EGI_n, LayoutDeltas_n)** — the diachronic state pair. Deltas survive
  transformations and save/reload cycles.
- **After a regime-3 move**, ligature endpoints are re-derived by
  `elk_layout_engine.rebuild_ligature_anchors` — the drawn line follows the marks.

## 🎨 Style System Architecture
- **JSON-based styles**: Platform-independent style definitions in `styles/` directory
- **Style loader**: `src/style_loader.py` - Loads and validates style definitions
- **Schema validation**: `styles/style_schema.json` - Ensures style consistency
- **Built-in styles**: DAU-compliant (default), Peirce-authentic, Sowa-compliant
- **Polarity convention**: Even polarity (positive) unshaded, odd polarity (negative) shaded
- **Optional features**: Arity numbers, variable labels, alternating shading
- **Transformation support**: Double cut highlighting, isomorphic matching, collapsed contexts
- **Complete documentation**: `docs/STYLE_SYSTEM_GUIDE.md` - User and developer guide

## 🖥️ UI - Three-Mode Architecture (web)
- **Status**: All three mode routes live in the web app (`/organon`, `/ergasterion`, `/agon`)
- **Launch**: `uv run uvicorn --app-dir src web_api.main:app --reload --port 8000`
- **Note**: The earlier Qt/PySide6 GUI (`src/gui_clean/`) was archived to `archive/qt-gui-2025/` (May 2026)

### Universe of Discourse Model (PRODUCTION)
- **UniverseOfDiscourse**: Synchronic (current state) + Diachronic (DAG history) + LayoutDeltas
- **DAG-Based History**: Branching transformation history (not linear sequences)
- **TomosService**: Unified API with index-based browsing, lazy loading, efficient storage
- **Categories**: Static (Literature, Canonical) vs Dynamic (Inquiry, Theorem Proof, EPG Session, Practice)
- **Backward Compatibility**: `GraphEntity` = `UniverseOfDiscourse` (all old code works unchanged)
- **Documentation**: `docs/UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md`, `docs/CORE_API_USAGE_GUIDE.md`, `docs/DAG_HISTORY_ARCHITECTURE.md`
- **Scalability**: Designed for 1000+ states, DAG supports branching exploration

### DAG-Based Transformation History (PRODUCTION)
**Current Status**: Fully implemented and tested  
**Documentation**: `docs/DAG_HISTORY_ARCHITECTURE.md`

**Key Features**:
- Branch from any historical state (not just linear sequences)
- Multiple transformation paths in single UoD
- Branch point detection and tracking
- Path finding (BFS for shortest, DFS for all paths)
- DAG statistics and analysis
- 100% backward compatible with linear history

**API Patterns**:
```python
from egi_transformation_history import EGITransformationHistory, HistoryBranchType

# Create history (backward compatible)
history = EGITransformationHistory(initial_egi, "Initial state")

# Add transformations (works linearly or with branching)
history.add_transformation(rule_name, context, result)

# Branch from any state
branch_id = history.create_branch_from_state(
    source_state_id,
    HistoryBranchType.EXPLORATION,
    "Try alternative approach"
)

# Query DAG structure
paths = history.get_all_paths_from_root(target_state_id)
children = history.get_child_states(state_id)
is_branch = history.is_branch_point(state_id)
stats = history.get_dag_statistics()

# Find paths between states
sequence = history.get_transformation_sequence(from_state, to_state)
```

**Use Cases**:
- **Theorem Proving**: Explore multiple proof strategies
- **Learning**: Try "what if?" without losing original work
- **Collaboration**: Multiple researchers, shared UoD
- **Real Inquiry**: Branching reflects actual reasoning

**Performance**:
- Add transformation: O(1)
- Create branch: O(1)
- Find shortest path: O(V + E)
- Efficient for 10-1000 states

**Testing**: `tools/test_history_dag.py` (5/5 tests passing)

### Organon Mode — the archive (LIVE)
- **Route**: `/organon` · `web_api/routes/organon.py` + `web_viewer/organon.html`
- **Read-only** browse of the corpus (28 UoDs in `tomos/`): EGI + metadata + provenance +
  annotations, worked chains with move-by-move navigation, saved regime-3 arrangements.
- Both the load **and** render boundaries attest the correspondence check (§3.3) per request.
- **Lenses**: modal (◇/□ off the branching DAG), audit (a standing proposal peeled against
  every successive M), storyboard, negation well, accessible (non-visual) projection.
- **Export**: EGIF / CGIF / CLIF / JSON / SVG / TikZ / authentic-Peirce LaTeX, plus a
  scholarly citation block. **Import** is live too (`/import`: OWL / RDF / CLIF files →
  `kind=ontology` UoDs, at the low-warrant floor).

### Ergasterion Mode — the workshop (LIVE)
- **Route**: `/ergasterion` · `web_api/routes/ergasterion.py` + `web_viewer/ergasterion.html`
- **Composition is freeform draw-then-read** (`js/freeform-canvas.js`): typed marks on a free
  canvas with no live EGI, read into a sign only at gate ① (`read-drawing` preview /
  `fix-drawing` commit), backed by `drawing_validity` + `drawing_to_egi`.
- A **Graph↔Argument** switch makes fixed/unfixed unmistakable: no rules on an unfixed graph,
  no meaning-change on a fixed one. Sessions hold a forest of branches with move-by-move
  navigation; a rule applied from an earlier state forks the DAG.
- **Challenge mode**: pick a target linear form, draw it freehand, get graded by `same_graph`
  + the legible diff (`egi_diff`).
- **Output goes to a regime-1 scratch store or is sent to Agon — never straight to the
  corpus.** There is no direct workshop→corpus route (the mode contract).

### Agon Mode — the contest (LIVE)
- **Route**: `/agon` · `web_api/routes/agon.py` + `web_viewer/agon.html`
- **Contest register**: the hot-seat Endoporeutic Game over the headless engine
  (`endoporeutic_game.py`), mediated by `agon_session_manager` (see the three-modes section).
- **Interpretation register**: the episode *given M, then G* — choose a reference model M
  (curated scenarios or corpus UoDs, optionally materialized), `/agon/interpret` peels G
  against it (`semantic_game.evaluate` → three-valued verdict + transcript + witness /
  counterexample), and `/agon/where-it-holds` runs the inverse pivot ("in what domain does G
  hold?").
- **The mode contract**: a graph reaches the attested corpus only by being tested through
  Agon, or as a style-only reprojection of an already-attested graph. §3.3 attests
  *correspondence, not truth*.

### Key Documentation
- **Start here**: `CURRENT_PLAN.md` (▶ NEXT SESSION), then `docs/VISION_AND_SCOPE.md`,
  `docs/CAPABILITY_MAP.md`, `docs/ROADMAP.md`, `docs/GLOSSARY.md`.
- **The central contract**: `docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md` — read before touching
  anything that produces or consumes an (EGI, LayoutDTO) pair.
- **Data models**: `docs/UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md`, `docs/DAG_HISTORY_ARCHITECTURE.md`.
- **API**: `docs/ARISBE_CORE_API_REFERENCE.md` (auto-generated), `docs/CORE_API_USAGE_GUIDE.md`.

## 🚀 Where the project actually stands

- **The calculus is the mature part.** The data model, the six Dau rules (Beta-aware), the
  ligature machinery, the correspondence enforcers, and the four linear formats are all
  production and corpus-tested. `docs/SOUNDNESS_BOUNDARY.md` gives the honest four-tier map of
  what is *proven* (Dau) vs *machine-verified* (tests) vs *attested at runtime* (§3.3) vs
  merely *argued* (prose).
- **All three web modes are live** (see the mode sections above), with the mode contract
  enforced: the corpus is reachable only through Agon or a style-only reprojection.
- **The frontier is second-order** (`docs/SECOND_ORDER_FRONTIER.md` + the two crossing memos):
  graphs about graphs. It is *mapped and de-risked* (`src/second_order_check.py` proves the law
  S1–S5 on candidates) but **not crossed** — two author decisions gate it.
- **Scope, honestly**: single-user, single-process. No auth, no tenancy, in-memory sessions,
  unlocked corpus writes. `docs/DEPLOYMENT_AND_MULTIUSER.md` names the gap and the path.
- **Performance**: `docs/PERFORMANCE_ENVELOPE.md` — the measured envelope, the four
  walls-and-exact-fixes, and the known-heavy shapes. Costs scale with graph *shape*, and every
  fix is exact, never approximate.
- **Current work**: `CURRENT_PLAN.md` (▶ NEXT SESSION) is always the authoritative status;
  `docs/CAPABILITY_MAP.md` says what works, where, and what guards it.

---

**Remember**: The coherence framework exists to eliminate guesswork. When in doubt, check the documentation rather than guessing!
