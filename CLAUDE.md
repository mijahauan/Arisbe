# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

Arisbe implements Frithjof Dau's formal mathematics for Charles Sanders Peirce's Existential Graphs (EGs). The fundamental entity is the **Universe of Discourse (UoD)** — a diachronic (evolving) process of logical reasoning — not a static diagram. A single EG is a synchronic snapshot within that process.

## Environment & Commands

Dependencies are managed by **uv** (Python 3.12). One-time setup: `uv sync --extra dev`. Run commands via `uv run` (no manual activation needed), or `source .venv/bin/activate` first.

```bash
# Testing
uv run pytest tests/ -q          # Full test suite (quiet)
uv run pytest tests/test_foo.py  # Single test file

# Quality assurance
uv run python tools/quality_gate_system.py         # Pre-commit checks (auto-run on commit)
uv run python tools/core_protection_system.py --report  # Check protected module status
uv run python tools/daily_quality_dashboard.py     # Overall system status

# Web viewer (canonical UI as of May 2026)
uv run uvicorn web_api.main:app --reload --port 8000   # API + static viewer at /
```

The Qt-based GUI (`arisbe.py`, `src/gui_clean/`) and its `unified_d3` layout
engine were archived to `archive/qt-gui-2025/` in May 2026 — see that
directory's README for context. They remain in git history if needed.

## Core Protection System

**17 modules in `src/` are protected** and cannot be modified without authorization:

```bash
touch .core_modification_authorized   # Required before modifying protected modules
python tools/core_protection_system.py --report  # Check what's protected
```

**The mathematical core test suite must always pass.** The core suite is the subset of `tests/` that covers `egi_core_dau`, `formal_transformation_rules`, `rule_interaction`, `subgraph_closure_validator`, `graph_isomorphism_engine`, and the Beta/logical proof exercises (~118 tests today). Failing core tests indicate real mathematical correctness issues, not test infrastructure problems.

## Architecture

### Three-Mode Conceptual Architecture

| Mode | Greek meaning | Role |
|------|--------------|------|
| **Organon** | "instrument" | Archive/corpus browser, timeline navigation, read-only |
| **Ergasterion** | "workshop" | Private editor, transformation practice, draft graphs |
| **Agon** | "contest" | Endoporeutic Game engine, formal validation, official record |

These are *conceptual modes*. The original Qt implementation (`src/gui_clean/`)
that mirrored them as separate windows was archived in May 2026. The current
plan is to surface them as routes within the web app (`src/web_api/`,
`src/web_viewer/`); that mapping is still ahead.

### Key `src/` Modules

- `egi_core_dau.py` — `RelationalGraphWithCuts` data model (immutable)
- `formal_transformation_rules.py` — Six Dau rules: ERA, INS, IT+, IT−, DC+, DC− (Beta-aware)
- `rule_interaction.py` — Headless RuleInteraction protocol for stepwise proof construction
- `subgraph_closure_validator.py` — Closure validation (Beta-aware: free outer-area vertices)
- `universe_of_discourse.py` — UoD entity (synchronic EGI + diachronic DAG history + layout deltas)
- `egi_transformation_history.py` — DAG-based branching transformation history
- `endoporeutic_game.py` — Two-player dialogical game engine
- `elk_layout_engine.py` (+ `elk_worker.js`) — Cut-aware ELK-based layout, the canonical layout path
- `simple_svg_renderer.py` — LayoutDTO → SVG
- `layout_dto.py` — Platform-independent layout DTO shared by layout engines and renderers
- `tomos_service.py` — Unified corpus API
- `z3_semantic_validator.py` — Z3 SMT-solver semantic validation
- `graph_isomorphism_engine.py` — NetworkX VF2 matching for goal detection
- `web_api/` (FastAPI) + `web_viewer/` (static HTML/JS) — the canonical user interface

### Linear Format Support (all production, round-trip tested)

| Format | Module | Corpus tested |
|--------|--------|--------------|
| EGIF | `egif_parser_dau.py` / `egif_generator_dau.py` | 57+ examples |
| CGIF (ISO/IEC) | `cgif_parser_dau.py` / `cgif_generator_dau.py` | 40+ examples |
| CLIF (Common Logic) | `clif_parser_dau.py` / `clif_generator_dau.py` | 35+ examples |
| FOPL | `chapter18_fopl_translation.py` | Φ/Ψ bidirectional |
| JSON | `egi_io.py` | With layout deltas |

### Data Model Invariants

- **EGI is immutable**: use `.with_vertex()`, `.with_edge()` — never `.add_*()`
- **Import pattern**: `from module_name import Foo` (not `from src.module_name`)
- **UoD state**: `State_n = (EGI_n, LayoutDeltas_n)` — deltas persist through transformations

### Beta Graph Support (FOL)

- **Beta graphs** use shared vertices across cut boundaries (lines of identity)
- EGIF: `*x` = defining label (new vertex), `x` = bound label (existing vertex in enclosing scope)
- `~[ (P *x) ~[ (Q x) ] ]` = ∀x(P(x) → Q(x)) — one shared vertex
- `SubgraphClosureValidator` with `context_area` treats ancestor-area vertices as free
- `IterationRule` extends lines of identity (reuses source-area vertices, no copy)
- `RuleInteraction` protocol: `begin_interaction` → `advance_interaction` → `apply_interaction`

## API Discovery

**Never guess function signatures.** The complete API is documented in
`docs/ARISBE_CORE_API_REFERENCE.md` (regenerated from
`tools/core_protection_system.py`'s protected-modules set):

```bash
grep -i "function_name" docs/ARISBE_CORE_API_REFERENCE.md
cat docs/CORE_API_USAGE_GUIDE.md          # Common development patterns
uv run python tools/extract_core_api.py   # Regenerate the reference
```

Before starting any implementation task, check whether a solution already exists:
```bash
python tools/context_awareness_system.py --check "task description"
```

## Key Documentation

- `AGENTS.md` — Developer guidelines with code patterns and usage examples
- `docs/UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md` — Core paradigm (read before touching UoD/history)
- `docs/DAG_HISTORY_ARCHITECTURE.md` — Branching transformation history
- `docs/ARISBE_CORE_API_REFERENCE.md` — Auto-generated API reference
- `docs/RETURN_TO_DEVELOPMENT.md` — 5-minute context recovery for the returning author
- `tomos/` — 87+ canonical EG examples with EGIF/CGIF/CLIF/FOPL variants

## Mathematical Foundation

Code chapters correspond to Dau's formal textbook:
- Ch. 14/15 → `formal_transformation_rules.py` (six transformation rules, Beta-aware)
- Ch. 14/15 → `rule_interaction.py` (headless stepwise protocol for all rules)
- Ch. 16–17 → `ligature_manipulation_rules.py`, `chapter17_soundness_evaluation.py`
- Ch. 18 → `chapter18_fopl_translation.py` (linear format Φ/Ψ translations)
- Ch. 20 → `syntactic_equivalence_checker.py`, `chapter20_syntactic_equivalence_fixes.py`

## Testing (406 passing, 3 skipped, 35 test files)

Key test files:
- `test_epg_exemplar_scripts.py` — 16 Endoporeutic Game scenarios (outcomes, strategies, engine integration)
- `test_beta_proof_exercises.py` — 20 Beta graph tests (FOL, shared vertices, EGIF round-trips)
- `test_logical_proof_exercises.py` — Propositional tautology derivations (modus ponens, etc.)
- `test_rule_interaction.py` — Headless RuleInteraction protocol integration tests
- `test_subgraph_closure_validation.py` — Closure validator including Beta-aware checks
- `test_graph_isomorphism_engine.py` — VF2 isomorphism for IT- validation
- `test_tomos_parsing.py` — EGIF/CGIF/CLIF round-trip across 87+ tomos examples
