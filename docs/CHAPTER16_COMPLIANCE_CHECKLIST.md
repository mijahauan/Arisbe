# Chapter 16 Compliance Checklist

This checklist verifies core Dau Chapter 16-aligned behaviors in Arisbe's rendering pipeline (Qt and TikZ) and spatial correspondence engine.

- [x] No predicate label intersection by any ligature path
  - Test: `tests/test_chapter16_compliance.py::test_chapter16_no_ligature_cross_label_rects`
  - Source of label rects: `edge` render command `bounds` emitted by `src/qt_correspondence_integration.py`

- [x] No vertex label/name intersection by any ligature path
  - Test: `tests/test_chapter16_compliance.py::test_chapter16_no_ligature_cross_label_rects`
  - Vertex label bounds estimated from `styles/default.json` tokens under `vertex.label_text` (char width, height, padding, offset)

- [x] Hooks attach on predicate label borders (not centers)
  - Verified in spatial engine hook computation (`src/egi_spatial_correspondence.py`), used by Qt/TikZ paths

- [x] Minimal arm length and border overlap enforced for ligatures
  - Tokens: `ligature.arm.min_length`, `ligature.arm.border_overlap` in `styles/default.json`
  - Applied in spatial correspondence routing

- [x] Continuous ligature geometry
  - Qt/TikZ renderers consume a single `path_points` polyline per ligature; no segmented rendering

- [x] Area parity shading for cuts and predicate label backgrounds
  - `area_parity` provided by `src/qt_correspondence_integration.py` for each element
  - Qt and TikZ apply parity-based fill to improve legibility

## Notes on Chapter 16 Themes

- Moving branches along a ligature (Chapter 16 derived rules) is represented by branch points on a continuous path. UI affordances for drag are planned.
- Extend/restrict and retraction transformations are architectural priorities but not yet user operations; geometry supports them.

## References in Code

- Spatial engine: `src/egi_spatial_correspondence.py`
- Qt integration: `src/qt_correspondence_integration.py`
- Qt GUI: `src/qt_egi_gui.py`
- TikZ export: `src/export/tikz_exporter.py`
- Style tokens: `styles/default.json`
- Tests: `tests/test_chapter16_compliance.py`

## Future Additions

- Extract and quote Chapter 16 sections from `dau_mathematical_logic_extracted.txt` into this document once precise segment offsets are located.
- Add tests for hook-on-border epsilon, minimal-arm-length enforcement, and parity fill checks.
