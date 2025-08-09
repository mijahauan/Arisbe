# Guidance Log

This log records the latest, confirmed guidance for EG rendering, layout, and interaction. Each entry may supersede earlier guidance.

## 2025-08-08 Minimal Default Placement Rules (ACTIVE)
- No cut overlap: sibling cuts must not overlap; maintain a small margin.
- Strict containment: all elements (predicates, vertices, ligatures) must stay within their containing cut and not intrude into sibling cuts.
- Center-by-default: gently center contents within each cut; cap the shift to keep Graphviz structure recognizable.
- Compact ligatures:
  - Binary: shortest straight segment between predicate peripheries; vertex spot at the segment midpoint.
  - Unary: short tail from predicate periphery; vertex at the tail end.
- Hook insets: inset hook points toward predicate centers (~4 px) to avoid boundary grazing and ensure containment.
- No text intersections: if a straight ligature would cross predicate text, draw a gentle single-arc fallback.
- Predicate spacing: maintain a small minimum gap between predicate boxes inside a cut; leave room for user edits.
- Sibling cuts: default to side-by-side with modest gaps; avoid heavy reflow.
- Identity spots: draw spots only for unlabeled vertices; labeled constants show the text and omit the spot.
- Render for selection: keep small gaps to aid marquee/hit-testing.

### Parameter Defaults
- Hook inset: 4 px
- Unary tail length: 14 px
- Min predicate gap in a cut: 12 px
- Sibling cut margin: 24 px
- Centering cap per cut: 24 px

## Conflict Handling Policy (ACTIVE)
- Prefer the newest confirmed guidance.
- Confirm with the user when a change may conflict (obviously or subtly) with earlier guidance.
- Record superseded guidance with date and reason.
