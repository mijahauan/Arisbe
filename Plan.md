# Arisbe: Working Plan

Last updated: 2025-08-26 (local)

## Purpose
Re-establish a concise, actionable plan that aligns code, tests, and docs to the layered architecture for Existential Graphs (EG) based on Dau’s formalism. This plan is for day-to-day execution and progress tracking.

## One-paragraph summary
Arisbe implements an immutable EGI core (V, E, ν, ⊤, Cut, area, rel) with deterministic EGDF projection and an interaction layer. Rendering follows Dau/Peirce conventions: heavy lines of identity, fine cuts, and proper ligature handling. The current focus is a lighter sandbox GUI (`tools/drawing_editor.py`) backed by a clean EGI↔Spatial correspondence layer that enforces area membership, cut nesting, and collision-safe single-curve ligatures. The broader app targets three sub‑apps: Organon (Browser), Ergasterion (Workshop), and Agon (Endoporeutic Game).

## Architecture (from README + docs)
- EGI (canonical logic, immutable) → Layout/Spatial → Rendering → Interaction.
- Meaning-preserving edits are presentation deltas; meaning-changing edits are explicit EGI operations.
- Files of interest:
  - `src/egi_core_dau.py`, `src/egif_parser_dau.py`, `src/egif_generator_dau.py`
  - `src/egi_spatial_correspondence.py`, `src/spatial_region_manager.py`
  - `src/routing/visibility_router.py`, `src/styling/style_manager.py`
  - `src/export/tikz_exporter.py`
  - Sandbox GUI: `tools/drawing_editor.py`
- Key docs: `docs/EGI_SPATIAL_CORRESPONDENCE.md`, `docs/CHAPTER16_COMPLIANCE_CHECKLIST.md`, corpus under `corpus/`.

## Guiding principles (operational)
- Ligatures are a single continuous curve; branch points and labels lie on the line.
- Same-area ligatures must avoid collisions with cuts and predicate text; cross-area ligatures may cross cut boundaries when logic requires it.
- Cuts are nested or disjoint; child cuts carve forbidden zones from parent areas (spatial exclusion). Positioning must respect area membership and excluded holes.
- Context-based sizing: cut size driven by its logical context; positioning constrained by the parent area bounds.

## Current status (observed)
- README describes full EGIF↔EGI↔EGDF pipeline and Qt rendering with Dau-compliant styling.
- Interaction sandbox exists: `tools/drawing_editor.py` (add/edit cuts, vertices, predicates, ligatures; resize/drag with constraints; deletion; throttled interactions).
- Spatial correspondence design documented in `docs/EGI_SPATIAL_CORRESPONDENCE.md`.
- Rich test suite under `tests/` for ligature routing, spatial exclusion, Chapter 16 compliance, and adapters.

## Objectives (near-term)
1. Solidify EGI↔Spatial Correspondence API with validations and deterministic outputs.
2. Enforce ligature path rules: single-curve, same-area collision avoidance, cross-area legality.
3. Establish canonical EGDF projection and wire to a read-only Organon pane.
4. Add selection overlays and context-sensitive actions in sandbox GUI.
5. Begin Chapter 16 transformation palette with legality checks (Practice mode groundwork).

## Milestones
- Milestone 1: Robust EGIF↔EGI↔EGDF round‑trip and canonicalization
  - Validate round-trip on corpus and ensure deterministic EGDF docs.
  - Files: `src/egdf_parser.py`, projection in `src/egi_system.py`.
- Milestone 2: Selection overlays + context actions (Ergasterion)
  - Overlays for cuts, predicates, ligatures; selection-driven operations.
  - File: `tools/drawing_editor.py` (UI), hooks into correspondence layer.
- Milestone 3: Background validation + transformation legality
  - Syntactic constraints, Chapter 16 ligature ops, real-time checks.
  - Files: `src/egi_graph_operations.py`, `src/egi_spatial_correspondence.py`.
- Milestone 4: Semantic mode toggle and presentation deltas
  - Meaning-preserving visual edits stored as deltas; canonical layout preserved.

## Immediate action plan (1–2 days)
- EGI↔Spatial API pass:
  - Review `src/egi_spatial_correspondence.py` and `src/spatial_region_manager.py` and add validations for:
    - Area membership enforcement and child‑cut exclusion holes.
    - Predicate text collision detection for ligature routing.
  - Add tests if missing: path avoidance over predicate bounds and cut interiors.
- Ligature routing tightening:
  - Ensure single path per ligature with obstacle avoidance (predicate text, cut boundaries) in `src/routing/visibility_router.py`.
  - Add stress tests around `tests/test_ligature_routing_*` to cover multi-branch and cross-area cases.
- Canonical EGDF projection:
  - Confirm `src/egdf_parser.py` dual JSON/YAML paths and write a simple `EGDFProjection` wrapper in `src/egi_system.py` if not present or incomplete.
  - Add a micro Organon preview (read-only) using the projection, or verify documented path works.
- GUI overlays (scaffolding):
  - In `tools/drawing_editor.py`, add minimal selection overlay boxes around predicates and cut handles; connect to correspondence IDs.

## Testing and validation
- Core: `pytest -q` or `python -m pytest tests/ -v`.
- Focus suites to keep green:
  - `tests/test_chapter16_compliance.py`
  - `tests/test_spatial_exclusion_complex.py`
  - `tests/test_ligature_routing_rules.py` and friends
  - `tests/test_headless_adapter_spatial.py`, `tests/test_drawing_to_egi_adapter.py`
- Use env flags (per README): `ARISBE_DEBUG_EGI=1`, `ARISBE_DEBUG_ROUTING=1` during debugging.

## Runbook (quick)
- Install deps: `pip install -r requirements.txt`
- Launch sandbox GUI: `python tools/drawing_editor.py`
- Headless drawing→EGI check: `python tools/drawing_to_egi.py --input tmp/drawing.json --layout`
- Validate corpus linear forms: `python tools/validate_corpus_linear_forms.py`

## Risks/assumptions
- Graphviz availability and PySide6 environment; fallbacks should not regress correctness.
- Legacy references in README may overstate certain GUI features; treat sandbox as source of truth for interaction work.
- Keep selection-driven operation model strict to maintain mathematical rigor.

## Appendix: file map (working set)
- Logical core: `src/egi_core_dau.py`, `src/egif_parser_dau.py`, `src/egif_generator_dau.py`
- Correspondence + spatial: `src/egi_spatial_correspondence.py`, `src/spatial_region_manager.py`, `src/routing/visibility_router.py`
- Projection: `src/egdf_parser.py`, `src/egi_system.py`
- GUI sandbox: `tools/drawing_editor.py`
- Docs: `docs/EGI_SPATIAL_CORRESPONDENCE.md`, `docs/CHAPTER16_COMPLIANCE_CHECKLIST.md`
- Tests: `tests/` (ligature routing, spatial exclusion, Chapter 16, adapters)
