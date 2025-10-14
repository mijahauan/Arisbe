# Code Archaeology - Cleanup Candidates

**Generated**: 2025-10-14 04:48:33

This report identifies code that may need cleanup or archival.

## 🐛 Debug Scripts (18 found)

These are one-off debugging scripts that may no longer be needed:

- `debug_area_polarity.py` (2KB, last modified 2025-09-10)
- `debug_composition_area.py` (1KB, last modified 2025-09-10)
- `debug_composition_ins.py` (3KB, last modified 2025-09-10)
- `debug_d3_payload.py` (4KB, last modified 2025-10-07)
- `debug_deep_context.py` (1KB, last modified 2025-09-10)
- `debug_egi_structure.py` (3KB, last modified 2025-09-09)
- `debug_egif_corruption.py` (3KB, last modified 2025-09-09)
- `debug_ins_mapping.py` (3KB, last modified 2025-09-09)
- `debug_ins_variables.py` (1KB, last modified 2025-09-09)
- `debug_port_links.py` (2KB, last modified 2025-10-07)
- `debug_theoretical_verification.py` (1KB, last modified 2025-09-12)
- `debug_variable_mapping.py` (2KB, last modified 2025-09-09)
- `debug_vertex_sequence.py` (2KB, last modified 2025-09-09)
- `test_debug_svg.py` (1KB, last modified 2025-10-10)
- `tools/debug_pathfinding.py` (3KB, last modified 2025-10-03)
- `tools/debug_port_assignment.py` (8KB, last modified 2025-09-26)
- `tools/debug_vertex_boundary_issue.py` (3KB, last modified 2025-10-03)
- `tools/debug_vertex_placement.py` (1KB, last modified 2025-10-03)

**Recommendation**: Review and move to `/archive/debug/` or delete if no longer needed.

## 👻 Orphaned Modules (23 found)

These modules are never imported (may be entry points or obsolete):

- `src/bottom_up_d3_engine.py` (18KB)
- `src/chapter18_final_translation.py` (14KB)
- `src/chapter18_improved_translation.py` (14KB)
- `src/chapter21_gui_integration.py` (20KB)
- `src/chapter_15_compliance_test_suite.py` (24KB)
- `src/controller/constraint_engine.py` (23KB)
- `src/dau_formalism_validator.py` (7KB)
- `src/dau_semantic_evaluation_tests.py` (14KB)
- `src/diagram_coordinator.py` (17KB)
- `src/egi_graph_operations.py` (14KB)
- `src/egi_transformation_pipeline.py` (20KB)
- `src/egi_validity_analyzer.py` (22KB)
- `src/gui/agon_interface.py` (15KB)
- `src/gui/enhanced_bullpen_editor.py` (15KB)
- `src/gui/enhanced_diagram_editor.py` (13KB)
- `src/gui/interactive_egi_viewer.py` (31KB)
- `src/gui/organon/chapter21_diagram_panel.py` (16KB)
- `src/gui/organon/corpus_navigator.py` (20KB)
- `src/gui/organon/exports_panel.py` (0KB)
- `src/gui/visual_item_factory.py` (15KB)
- `src/gui_clean/common/interactive_diagram_canvas.py` (10KB)
- `src/gui_clean/main_application.py` (0KB)
- `src/layout_dto_adapter.py` (4KB)

**Note**: Some may be legitimate entry points (CLI scripts, etc.).
Review each to determine if it's needed.

## 📦 Deprecated Files (1 found)

Files with deprecated/legacy indicators in path:

- `src/definitive_three_pass_engine_backup.py` (contains 'backup')

**Recommendation**: Move to `/archive/` directory.

---

## Summary

**Total Cleanup Candidates**: 42

### Cleanup Actions

1. **Review each file** to determine if it's still needed
2. **Archive useful references** to `/archive/` directory
3. **Delete obsolete code** that's no longer relevant
4. **Update imports** if files are moved

### Archive Structure

```
archive/
├── debug/          # One-off debugging scripts
├── deprecated/     # Superseded implementations
├── experiments/    # Failed experiments (keep for reference)
└── tests/          # Old test files
```

---

*Regenerate this report: `python tools/detect_code_archaeology.py`*
