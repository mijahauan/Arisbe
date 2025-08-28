# Arisbe Use Cases and EGI-Centric Lifecycle

This guide connects concrete user workflows to Arisbe’s architecture, showing how the EGI remains the single source of truth while different replicas (linear forms, drawn forms, bundles) serve distinct purposes.

- Core truth: EGI (Existential Graph Instance)
- Replicas: Linear forms (EGIF/CLIF/CGIF/FOPL), Drawn EGDF (Style + Deltas), Portable EGDF bundle
- Modes: Composer (Ergasterion), Practice, Agon (Endoporeutic game), Organon (visualization)

## 1) Ingest: From external representations to EGI

Goal: Convert any external expression (textual or graphical) into a canonical EGI.

- Inputs
  - Linear forms: EGIF, CLIF, CGIF (supported in `corpus/` tools)
  - FOPL/First-order logic statements (via CLIF where possible)
  - Drawn EG or other notations (future importers; may require manual mapping)
  - Natural language (future research; out of scope here)
- Process
  - Parse external form → normalize to EGI using existing parsers/translators
  - Validate (structure and serialization locks) to ensure integrity
- Outputs
  - `<graph_id>.egi.json` (canonical, immutable logical structure)

Why EGI? It unifies all forms, enabling reliable round-trips and consistent downstream usage.

## 2) Puzzle Mode: EGI → EGDF (Style + Deltas)

Goal: Produce a readable drawn form by applying a style and arranging elements via user deltas.

- Inputs
  - EGI: `<graph_id>.egi.json`
  - Style package: `docs/styles/<style>@<ver>.json` (e.g., Dau-Classic, Peirce-Notebook)
- Process
  - Load EGI into the drawing editor (`tools/drawing_editor.py`)
  - Select style (toolbar: Select Style)
  - Manually arrange cuts, predicates, vertices (guardrails enforce nested-or-disjoint cuts)
  - Save layout deltas (toolbar: Save Layout Deltas)
- Outputs
  - Deltas file: `graphs/<graph_id>/layouts/<graph_id>.layout.<style>@<ver>.<user>.json`
  - Optional portable bundle: `graphs/<graph_id>/bundles/<graph_id>.<style>@<ver>.<user>.egdf.json` (inline EGI + style snapshot + deltas)

Result is a “fully-formed” EGDF for that style/user, while preserving EGI as the truth.

## 3) Compose from scratch (Ergasterion Composer/Editor)

Goal: Create a new graph when no prior EGI exists.

- Process
  - Use the drawing editor to place vertices/predicates/cuts and wire ligatures
  - Export EGI from the constructed schema (ensures a valid logical instance)
  - From there, proceed as in Puzzle Mode to style and save deltas
- Outputs
  - New `<graph_id>.egi.json` + deltas and optional EGDF bundle

## 4) Practice Mode: Transformation rules on drawn forms

Goal: Train with EG rules and develop fluency in endoporeutic reasoning.

- Inputs
  - EGI + EGDF (any style/user)
- Process
  - Apply validated transformation rules (operate on EGI contexts)
  - Visualize steps on the drawn form (deltas update reflect moves)
- Outputs
  - Move transcripts (style-agnostic), reproducible on any style
  - Updated EGDF snapshots if desired

## 5) Agon: Endoporeutic Game on a shared sheet

Goal: Collaboratively construct a universe of discourse (UoD) by combining graphs and playing rule-based moves.

- Inputs
  - A set of EGIs (user’s collection + externally ingested)
  - Agreed ruleset and initial sheet of assertion
- Process
  - Players perform moves that transform or combine EGIs on the sheet
  - Under the hood, moves are EGI transformations with provenance and timestamps
  - Each user may view the same evolving EGI set in their preferred style (Reader Mode)
- Outputs
  - A connected EGI representing the UoD + move history
  - Optional EGDF bundles capturing notable states

## 6) Organon: Visualizing growth of the UoD

Goal: Make large, evolving structures comprehensible.

- Views
  - Sheet view: current connected EGI rendered as EGDF in chosen style
  - Timeline view: sequence of moves and snapshots
  - Dependency view: how subgraphs combine and transform
- Techniques
  - Style mapping (project deltas from one style to another when needed)
  - Semantic filtering (focus on specific contexts, ligatures, predicates)
  - Multi-scale navigation (cuts as nested domains)

## Roles of artifacts in every mode

- EGI (`<graph_id>.egi.json`)
  - Canonical logic; diff/merge; CI structural checks
- Style (`docs/styles/<style>@<ver>.json`)
  - Reusable visual rules; team coordination
- Deltas (`<graph_id>.layout.<style>@<ver>.<user>.json`)
  - Personal or team layout choices; reviewable and shareable
- EGDF bundle (`<graph_id>.<style>@<ver>.<user>.egdf.json`)
  - Portable all-in-one for publishing and long-term storage

## Integrity and collaboration

- Hashes (`egi_hash`, `style_hash`, `layout_hash`) ensure alignment across artifacts
- Reference vs inline forms:
  - Authoring: modular references (EGI, style, deltas separate)
  - Sharing/archival: single inline bundle
- Reader Mode:
  - Pick a preferred style; if no matching deltas, adapt from another style or use a deterministic initial placement

## Tying to the codebase

- Editor: `tools/drawing_editor.py`
  - Load EGI/EGIF; select style; save deltas; export EGDF (bundle)
  - Bidirectional selection between canvas and JSON preview
  - Initial hierarchical placement and guardrails (nested-or-disjoint cuts)
- EGDF adapter: `src/egdf_adapter.py`
  - Build EGDF documents from schema + layout; validate
- Tests: `tests/` (e.g., `test_egdf_adapter.py`)
  - Structural/serialization locks, round-trip expectations

This lifecycle keeps the EGI central while enabling multiple readable drawn replicas and collaborative growth from practice to the Agon and Organon.
