# EGDF v0.1 – Existential Graphs Drawing Format

EGDF is a platform-independent document format describing how to draw an Existential Graph Instance (EGI). It separates logical content from presentation.

- Logical truth: EGI (per Dau’s formalism)
- Presentation: layout primitives + styles + user deltas
- Deterministic rendering: Base layout → styles → deltas

## 1. Document structure

Top-level sections:

- **egdf**: versioning and provenance
- **egi_ref**: logical EGI, inline or by reference
- **layout**: device-independent geometry for cuts, vertices, predicates, ligatures
- **styles**: declarative stylesheet (variables, rules, imports)
- **deltas**: ordered user tweaks that do not change logic

```json
{
  "egdf": { "version": "0.1", "generator": "arisbe", "created": "2025-08-27T00:00:00Z" },
  "egi_ref": { "hash": "sha256:...", "inline": { /* EGI content */ } },
  "layout": { /* geometry */ },
  "styles": { /* stylesheet */ },
  "deltas": [ /* tweaks */ ]
}
```

## 9. Authoring model: modular vs bundled

- __Modular (authoring, collaboration)__
  - Canonical EGI per graph: `<graph_id>.egi.json`
  - Reusable styles: `docs/styles/<style_name>@<ver>.json`
  - Per-style, per-user layout deltas: `graphs/<graph_id>/layouts/<graph_id>.layout.<style_name>@<ver>.<user>.json`
  - Pros: reuse, small diffs, clear separation; Cons: consumers must resolve refs

- __Bundled (portable, archival)__
  - Single EGDF file with inline `egi_ref.inline`, inlined style or `style_ref`, and resolved `layout` and/or `deltas`.
  - Path: `graphs/<graph_id>/bundles/<graph_id>.<style_name>@<ver>.<user>.egdf.json`

Include integrity fields where possible: `egi_hash`, `style_hash`, and `layout_hash` (sha256 over normalized JSON with sorted keys).

## 10. Deltas-only document

To support modular workflows, a minimal deltas document is defined:

```json
{
  "egdf_deltas": { "version": "0.1" },
  "style_ref": { "id": "dau-classic@1.0" },
  "deltas": [
    { "op": "set_rect", "id": "c1", "x": 100, "y": 80, "w": 240, "h": 160 },
    { "op": "set_position", "id": "v1", "x": 180, "y": 140 },
    { "op": "set_rect", "id": "e1", "x": 220, "y": 120, "w": 24, "h": 12 }
  ]
}
```

Notes:

- The target EGI is identified externally (by repository location or by `egi_hash` in a companion manifest). Renderers should apply deltas only if the EGI matches.
- Unknown ops must be ignored by validators; renderers may support a subset.
- `set_rect` and `set_position` must not violate area membership; violations are ignored with diagnostics.

## 11. Reader Mode and style mapping

- Users may select a preferred style for viewing the same EGI.
- If a deltas file exists for that style and user, it is applied. Otherwise:
  - Try to map an available deltas file from another style via a style mapping adapter.
  - Fall back to deterministic initial placement.
- Mapping guidelines:
  - Normalize font metrics, stroke widths, symbol boxes.
  - Prefer relative anchors/ratios when projecting positions across styles.

## 12. Naming and versioning guidance

- EGI: `<graph_id>.egi.json` (stable id or content hash derived)
- Style: `<style_name>@<major.minor>.json`
- Deltas: `<graph_id>.layout.<style_name>@<ver>.<user>.json`
- Bundle: `<graph_id>.<style_name>@<ver>.<user>.egdf.json`

All modular artifacts should, when feasible, embed content hashes of their dependencies to enable validation.

## 2. EGI reference (logical layer)

Required keys when inline:

- **sheet**: sheet area id
- **V, E, Cut**: sets of vertices, edges (predicates/relations), cuts
- **nu(e)**: ordered list of vertices for edge e
- **rel(e)**: symbol name of relation/function/constant for edge e
- **area(a)**: elements directly in area a (sheet and cuts)
- **rho(v)**: optional constant label for vertex v
- **alphabet**: Dau’s alphabet
  - **C**: constants
  - **F**: functions
  - **R**: relations
  - **ar**: arity by symbol name (for constants the arity is 0)

A canonical JSON hash (sha256 over sorted keys) is stored at `egi_ref.hash` and must match the inline content.

## 3. Layout (platform-neutral)

- **units**: one of pt|px|mm|cm|in (default: pt)
- **cuts[id]**: { x, y, w, h }
- **vertices[id]**: { x, y, label_anchor? }
- **predicates[edge_id]**: { text, x, y, w, h }
- **ligatures[edge_id]**: { area, path }
  - **path**: { kind: spline|polyline, points: [[x,y], ...] }

Coordinates are abstract floats; no toolkit-specific attributes.

## 4. Styles (declarative)

- **imports**: array of style package identifiers
- **variables**: token map (e.g., colors, sizes)
- **rules**: CSS-like selection on semantic roles
  - **select**: examples: `Cut`, `Vertex`, `Ligature[same_area=true]`, `Predicate[name='Loves']`
  - **stroke/fill/text**: renderer-agnostic properties (width, color, alpha, font)

Style packages are small JSON docs that provide variables and rules. Later imports override earlier ones; document-local `variables`/`rules` override imports.

## 5. Deltas (user tweaks)

Ordered, idempotent operations applied after styles.

- Examples:
  - `translate { id, dx, dy }`
  - `set_position { id, x, y }`
  - `size_override { cut_id, w, h }` (must respect logical containment)
  - `route { edge_id, waypoints }`
  - `pin { id, anchor }`
  - `z_hint { id, priority }`

Validation rules:

- Deltas MUST NOT change logic (no changes to `egi_ref`).
- Deltas MUST NOT violate area membership; invalid deltas are ignored or quarantined with diagnostics.
- Unknown delta ops are allowed and ignored by validators; renderers may support a subset.

## 6. Versioning and compatibility

- **egdf.version** uses semver.
- **egi_ref.hash** guards against misapplication to the wrong EGI.
- Style tokens and delta ops are forward compatible; unknown fields are ignored with warnings.

## 7. Round-trip expectations

- EGIF → EGI → EGDF → EGI must preserve logical structure exactly.
- Applying the same EGDF (styles+deltas) yields deterministic layout.

## 8. Minimal example

```json
{
  "egdf": { "version": "0.1", "generator": "example", "created": "2025-08-27T00:00:00Z" },
  "egi_ref": {
    "inline": {
      "sheet": "S",
      "V": ["v1"],
      "E": ["e1"],
      "Cut": ["c1"],
      "nu": {"e1": ["v1"]},
      "rel": {"e1": "P"},
      "area": {"S": ["c1"], "c1": ["v1", "e1"]},
      "rho": {"v1": null},
      "alphabet": {"C": [], "F": [], "R": ["P"], "ar": {"P": 1}}
    }
  },
  "layout": {
    "units": "pt",
    "cuts": {"c1": {"x": 100, "y": 80, "w": 240, "h": 160}},
    "vertices": {"v1": {"x": 180, "y": 140}},
    "predicates": {"e1": {"text": "P", "x": 220, "y": 120, "w": 24, "h": 12}},
    "ligatures": {"e1": {"area": "c1", "path": {"kind": "spline", "points": [[220,126],[200,135],[180,140]]}}}
  },
  "styles": {"imports": ["dau-classic@1.0"], "variables": {}, "rules": []},
  "deltas": []
}
```
