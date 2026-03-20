# Arisbe: Existential Graphs, Dau-compliant

A mathematically rigorous implementation of Charles S. Peirce’s Existential Graphs based on Frithjof Dau’s formal framework. Arisbe provides a pipeline and tools to parse linear forms (EGIF/CGIF/CLIF), construct a canonical EGI model, generate EGDF drawings, validate logic–spatial concordance, and render/manipulate EG diagrams interactively.

Updated: 2025-08-30

## Overview

- EGI is the canonical source of truth.
- EGIF/CGIF/CLIF are linear forms that round-trip to/from EGI.
- EGDF is the canonical drawn-form spec for rendering/persistence.
- GUI interactions are meaning-preserving (presentation deltas) unless explicitly invoking EGI operations.
- Ligatures are single continuous lines; same-area ligatures avoid collisions; cross-area ligatures can cross cuts; rendering order: Cuts → Predicates → Vertices → Ligatures.

## Architecture

Layered model:
1. EGI (canonical logic) → 2. Spatial Layout → 3. EGDF/Rendering → 4. Interaction

Key components:
- Logical layer: `src/egi_core_dau.py`, `src/egif_parser_dau.py`, `src/egif_generator_dau.py`, `src/cgif_*`, `src/clif_*`
- Controller/coordination: `src/egi_controller.py`, `src/egi_graph_operations.py`, `src/egi_system.py`
- Spatial layout: `src/networkx_spatial_layout.py` (NetworkX + Graphviz), `src/egi_spatial_correspondence.py`
- Validation: `src/logic_spatial_validator.py`
- EGDF and adapters: `src/egdf_parser.py`, `src/egdf_adapter.py`, `src/egi_export.py`
- Rendering/GUI: `src/qt_egi_gui.py`, `src/arisbe_unified_app.py`, `src/styling/style_manager.py`, `src/routing/visibility_router.py`
- Export: `src/export/tikz_exporter.py`
- Interactive sandbox: `tools/drawing_editor.py`, `tools/drawing_to_egi.py`

Principles:
- Context vs Area: cut size requirements from context; positioning constraints from area bounds.
- Spatial exclusion: child cuts carve forbidden zones from parent areas; enforced via containment and z-order depth.
- Ligature rules (Dau Chapter 16): same-area ligatures avoid collisions; cross-area connections may cross cuts; visual single-curve entity.

## Project structure

- `src/`
  - Canonical logic: `egi_core_dau.py`, `egi_system.py`, `egi_graph_operations.py`, `transformation_rules.py`
  - Linear forms: `egif_parser_dau.py`, `egif_generator_dau.py`, `cgif_parser_dau.py`, `cgif_generator_dau.py`, `clif_parser_dau.py`, `clif_generator_dau.py`
  - Controllers/coordination: `egi_controller.py`, `egi_adapter.py`, `egi_io.py`, `corpus_integration.py`
  - Spatial/layout/validation: `networkx_spatial_layout.py`, `logic_spatial_validator.py`, `egi_spatial_correspondence.py`, `spatial_region_manager.py`, `egi_logical_areas.py`
  - GUI/rendering: `qt_egi_gui.py`, `arisbe_unified_app.py`, `routing/visibility_router.py`, `styling/style_manager.py`, `export/tikz_exporter.py`, `controller/constraint_engine.py`
  - Legacy/demo: `qt_test_minimal.py`, `qt_correspondence_integration.py`, `spatial_logical_alignment.py`, `corpus_egi_test.py`
- `tools/`: interactive sandbox and converters (`drawing_editor.py`, `drawing_to_egi.py`, etc.)
- `docs/`: derived corpus text, references, examples, styles
- `corpus/`: canonical and challenging examples
- `tests/`: comprehensive unit/integration tests

## Current state

What’s working
- Canonical pipeline: EGIF ↔ EGI ↔ EGDF round-trip; CLIF/CGIF support present.
- Spatial layout: NetworkX + Graphviz engine functioning with manual fallback. Positions honor area mappings and nesting.
- Concordance validation: detects containment, overlap, and ligature violations; concordance holds on core demos.
- Ligatures: rendered as single continuous paths; avoid predicate text; collision-aware routing; shortest collision-free path maintained.
- Rendering order: Cuts → Predicates → Vertices → Ligatures.
- Integrity protection: Continuous architectural integrity monitoring (file watchdog, git hooks, import interception, scheduled scans, centralized logging).
- Containment fixes: adaptive padding prevents invalid rectangles; 100% containment compliance on targeted tests.

Known issues / priorities
- Selection pipeline: hit detection priorities, element selection precedence, and graphics-item lookup; fix highlighting for connected elements and cut border-only highlight.
- Qt containment visualization: some diagrams still lack clear nested containment in GUI despite correct bounds; improve mapping/painting.
- Interactive constraints: enforce spatial exclusion and Chapter 16 ligature constraints consistently at edit-time.
- Heavy line spatial units: treat lines of identity as first-class spatial constraints in layout/avoidance.
- EGI ↔ spatial correspondence: continue strengthening bidirectional mapping guarantees under edits.

## Sub-applications

- Organon (Browser): canonical EGDF viewing of EGI, read-only. Status: foundation in place; extend EGDF generator and browser views.
- Ergasterion (Workshop): interactive editor (Bullpen) with Warmup/Practice modes. Status: Qt GUI and sandbox present; constraints and selection system under active work.
- Agon (Endoporeutic Game): gameplay built on formal, legal, meaning-preserving moves. Status: design staged; depends on robust constraints and transformation legality.

## Quick start

Install
```bash
pip install -r requirements.txt
```

Run the interactive sandbox (recommended for quick trials)
```bash
python tools/drawing_editor.py
```

Run the Qt GUI
```bash
python src/arisbe_unified_app.py
# or
python src/qt_egi_gui.py
```

Parse and layout from EGIF in code
```python
from src.egif_parser_dau import EGIFParser
from src.egi_controller import EGIController
from src.networkx_spatial_layout import compute_layout

egi = EGIFParser('*x (Human x) ~[ (Mortal x) ]').parse()
layout = compute_layout(egi)
# feed into GUI or exporter as needed
```

Convert a drawing JSON to EGI
```bash
python tools/drawing_to_egi.py --input tmp/drawing.json --layout
```

## Testing

- Full test suite
```bash
python -m pytest tests/ -v
```

- Targeted GUI/minimal demos
```bash
python src/qt_test_minimal.py
```

## EGDF integrity and style metadata

- EGDF files include a header with:
  - egi_checksum: deterministic hash of normalized EGI
  - style_id: current theme identifier
  - updated: UTC ISO timestamp
- On load, mismatches can be surfaced for user awareness in future iterations.

## Development notes

- EGI as single source of truth; visual edits default to presentation deltas.
- Cuts determine spatial exclusion; child cuts create forbidden zones for parent-level elements.
- Same-area ligatures must avoid collisions; cross-area ligatures may cross cuts per EGI mappings.
- Rendering order is fixed to preserve legibility and correctness.
- Integrity monitoring is always-on to prevent regressions and contamination.

## Roadmap (next steps)

- Selection and highlighting
  - Fix hit detection priority and element precedence in `src/qt_egi_gui.py`
  - Correct cut highlighting to border-only styling
  - Ensure connected element highlighting via robust item lookup map

- Interactive constraints
  - Enforce spatial exclusion and area-aware placement in edit operations
  - Chapter 16-compliant ligature adjustments during interaction

- EGDF/Organon
  - Harden EGDF generation; load+compare with `egi_checksum`
  - Read-only Organon browser with canonical views and corpus integration

- Ergasterion
  - Warmup/Practice mode controllers; real-time legality feedback
  - Transformation palette wired to EGI operations

- Exports and polish
  - Improve `src/export/tikz_exporter.py`, add SVG/PNG
  - Style themes and publication-quality output

## References

- Dau, Frithjof. Mathematical Logic with Diagrams (2003).
- Peirce, C. S. Existential Graphs (Collected Papers).
- Sowa, J. F. Existential Graphs: MS 514 by Charles Sanders Peirce (2007).
