# Arisbe Repository Cleanup Plan

## Files to DELETE (Test/Debug/Demo/Obsolete)

### Root Directory Test Files
- `test_*.py` (all test files in root - move to tests/ if needed)
- `debug_*.py` (all debug files)
- `validate_*.py` (all validation files)
- `trace_*.py` (all trace files)
- `api_contract_review.py`
- `phase2_gui_foundation.py`
- `*.dot` files (debug output)
- `*.png` files (test output)
- `*.txt` files (debug output)

### src/ Directory Cleanup
- `test_*.py` (all test files in src/)
- `debug_*.py` (all debug files in src/)
- `demo_*.py` (all demo files in src/)
- `validate_*.py` (all validation files in src/)

### Obsolete Implementation Files
- `arisbe_gui_standard.py` (replaced by arisbe_eg_clean.py)
- `arisbe_eg_works.py` (replaced by arisbe_eg_clean.py)
- `diagram_*.py` (old diagram implementations)
- `layout_engine_clean.py` (duplicate of layout_engine.py)
- `*_enhanced.py` (experimental versions)
- `*_corrected.py` (experimental versions)
- `*_integrated.py` (experimental versions)

### Experimental/Unused Components
- `background_validation_system.py`
- `content_driven_layout.py`
- `dual_mode_layout_engine.py`
- `eg_transformation_*.py`
- `enhanced_*.py`
- `interaction_controller.py`
- `mode_aware_selection.py`
- `selection_system*.py`
- `warmup_mode_controller.py`

## Files to ARCHIVE (Move to attic/)

### Analysis and Planning Documents
- `dau_compliance_analysis.md`
- `dau_transformation_schema.md`
- `dau_yaml_system_documentation.md`
- `frontend_assessment.md`
- `Front_End_description.md`
- `todo.md`

### Output Directories
- `out_cli_demo/`
- `out_logical_baseline/`
- `test_egdf_output/`
- `test_gui_debug/`
- `reports/` (move to attic/reports/)

## Files to KEEP (Core Functionality)

### Main Application
- `arisbe_eg_clean.py` (main application)

### Core Pipeline
- `src/canonical/` (entire directory - canonical API)
- `src/egi_core_dau.py` (core EGI data structures)
- `src/egif_parser_dau.py` (EGIF parsing)
- `src/egif_generator_dau.py` (EGIF generation)
- `src/egdf_dau_canonical.py` (EGDF generation)
- `src/egdf_parser.py` (EGDF parsing)

### Layout and Rendering
- `src/graphviz_layout_engine_v2.py` (Graphviz integration)
- `src/layout_engine.py` (pure layout engine)
- `src/eg_graphics_scene_renderer.py` (Qt rendering)
- `src/eg_graphics_items.py` (Qt graphics items)

### Corpus and Browser
- `src/corpus_loader.py` (corpus access)
- `src/corpus_browser.py` (browser UI)
- `corpus/` (entire directory - examples)

### Utilities
- `src/shapely_area_manager.py` (area management)
- `src/annotation_system.py` (annotation toggles)

### Configuration
- `requirements.txt`
- `setup.py`
- `LICENSE`
- `CHANGELOG.md`

## Directories to KEEP
- `src/` (cleaned up)
- `corpus/` (examples)
- `docs/` (documentation)
- `tests/` (organized tests)
- `.github/` (CI/CD)

## Directories to CREATE
- `attic/` (archived files)
- `attic/analysis/` (analysis documents)
- `attic/experimental/` (experimental code)
- `attic/reports/` (old reports)
