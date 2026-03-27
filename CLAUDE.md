# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

Arisbe implements Frithjof Dau's formal mathematics for Charles Sanders Peirce's Existential Graphs (EGs). The fundamental entity is the **Universe of Discourse (UoD)** — a diachronic (evolving) process of logical reasoning — not a static diagram. A single EG is a synchronic snapshot within that process.

## Environment & Commands

```bash
conda activate CGIF        # Python 3.12.10 — required before running anything

# Testing
python -m pytest tests/ -q          # Full test suite (quiet)
python -m pytest tests/test_foo.py  # Single test file

# Quality assurance
python tools/quality_gate_system.py         # Pre-commit checks (auto-run on commit)
python tools/core_protection_system.py --report  # Check protected module status
python tools/daily_quality_dashboard.py     # Overall system status

# GUI
python arisbe.py                           # Qt-based integrated interface (PySide6)
python src/gui_clean/main_application.py   # Clean GUI entry point

# Interactive game REPL
python -c "import sys; sys.path.insert(0,'src'); from game_repl import ArisbeGameREPL; ArisbeGameREPL().cmdloop()"
```

**Qt-dependent tests hang during collection** — exclude them from automated runs or run manually via `python tools/test_gui_organon.py`.

## Core Protection System

**16 modules in `src/` are protected** and cannot be modified without authorization:

```bash
touch .core_modification_authorized   # Required before modifying protected modules
python tools/core_protection_system.py --report  # Check what's protected
```

The **87 core tests must always pass**. They validate the mathematical foundation. Failing core tests indicate real mathematical correctness issues, not test infrastructure problems.

## Architecture

### Three-Module GUI Architecture

| Module | Greek meaning | Role | Status |
|--------|--------------|------|--------|
| **Organon** | "instrument" | Archive/corpus browser, timeline navigation, read-only | ~40% complete |
| **Ergasterion** | "workshop" | Private editor, transformation practice, draft graphs | Foundation integrated, untested |
| **Agon** | "contest" | Endoporeutic Game engine, formal validation, official record | Future (game engine in `src/` is production) |

### Key `src/` Modules

- `egi_core_dau.py` — `RelationalGraphWithCuts` data model (immutable)
- `formal_transformation_rules.py` — Six Dau rules: ERA, INS, IT+, IT−, DC+, DC−
- `universe_of_discourse.py` — UoD entity (synchronic EGI + diachronic DAG history + layout deltas)
- `egi_transformation_history.py` — DAG-based branching transformation history
- `endoporeutic_game.py` + `game_repl.py` — Two-player dialogical game engine
- `unified_d3_engine.py` — Recursive bottom-up layout engine (shell-and-core D3)
- `simple_svg_renderer.py` — LayoutDTO → SVG
- `tomos_service.py` — Unified corpus API
- `z3_semantic_validator.py` — Z3 SMT-solver semantic validation
- `graph_isomorphism_engine.py` — NetworkX VF2 matching for goal detection

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

## API Discovery

**Never guess function signatures.** The complete API (57 classes, 19 functions) is documented:

```bash
grep -i "function_name" docs/ARISBE_CORE_API_REFERENCE.md
cat docs/CORE_API_USAGE_GUIDE.md     # Common development patterns
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
- `docs/context/FRAMEWORK_AMNESIA_RECOVERY.md` — Full context recovery if disoriented
- `tomos/` — 87+ canonical EG examples with EGIF/CGIF/CLIF/FOPL variants

## Mathematical Foundation

Code chapters correspond to Dau's formal textbook:
- Ch. 14/15 → `formal_transformation_rules.py` (six transformation rules)
- Ch. 16–17 → `ligature_manipulation_rules.py`, `chapter17_soundness_evaluation.py`
- Ch. 18 → `chapter18_fopl_translation.py` (linear format Φ/Ψ translations)
- Ch. 20 → `chapter20_syntactic_equivalence_fixes.py`
