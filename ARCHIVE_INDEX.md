# Archive Index

**Date**: 2025-12-26  
**Purpose**: Repository cleanup to focus on active development files

## Archive Structure

All archived files are preserved in git history and organized into:

```
archive/
├── documentation/          # Historical documentation (65+ files)
├── debug_scripts/          # Debug scripts (13 files)
├── test_scripts/           # Root-level test scripts (46 files)
├── analysis_artifacts/     # Large analysis files (15+ files)
└── deprecated_code/        # Backup/deprecated code (5 files)
```

## What Was Archived

### 1. Historical Documentation (archive/documentation/)

**Phase & Session Reports**:
- ALL_PHASES_COMPLETE.md
- ALL_OPTIONS_COMPLETE_SUMMARY.md
- PHASE_1_COMPLETION_REPORT.md through PHASE_6_COMPLETION_REPORT.md
- PHASE1_COMPLETION_SUMMARY.md, PHASE2_COMPLETION_SUMMARY.md
- PHASES_1_2_3_COMPLETE.md
- SESSION_2025_10_14_SUMMARY.md
- SESSION_SUMMARY_2025_10_12.md
- TESTING_SESSION_2025_10_01_COMPLETE.md
- TESTING_SESSION_COMPLETE.md
- COMMIT_SUMMARY.md, COMMIT_SUMMARY_2025_09_30.md
- STATUS_REPORT_2025_10_15.md

**Implementation Success Reports**:
- BOTTOM_UP_ENGINE_FIXES.md
- BOTTOM_UP_ENGINE_INTEGRATION.md
- BOTTOM_UP_SPREADING_FIXES.md
- CHAPTER18_TRANSLATION_CONSISTENCY_REPORT.md
- CHAPTER20_SYNTACTIC_EQUIVALENCE_REPORT.md
- CHAPTER21_IMPLEMENTATION_SUMMARY.md
- COMPLETE_REFACTORING_SUMMARY.md
- COMPLETE_ROUND_TRIP_REPORT.md
- COMPREHENSIVE_TESTING_FINAL_REPORT.md
- COMPREHENSIVE_TESTING_IMPLEMENTATION_SUMMARY.md
- CONNECTION_PORTS_SUCCESS.md
- ERGASTERION_PHASE1_COMPLETE.md
- FORCE_BALANCE_FIX.md
- HOOK_AND_SIZING_FIXES.md
- IMPLEMENTATION_SUMMARY.md
- LIGATURE_BUG_FOUND.md
- NEAREST_PORT_ASSIGNMENT_SUCCESS.md
- OPTIMAL_PORT_ASSIGNMENT_SUCCESS.md
- SEQUENTIAL_LAYOUT_ENGINE_SUCCESS.md
- STYLED_LAYOUT_ENGINE_SUCCESS.md
- TESTING_FIXES_COMPLETE.md
- USER_EDIT_SYSTEM_SUCCESS.md
- VISUAL_QUALITY_FIXES.md
- WORKFLOW_TEST_FINDINGS.md

**Coherence Framework Evolution**:
- COHERENCE_FRAMEWORK_100_PERCENT_COMPLETE.md
- COHERENCE_FRAMEWORK_ANALYSIS_2025.md
- COHERENCE_FRAMEWORK_COMPLETE_EXPLANATION.md
- COHERENCE_FRAMEWORK_IMPLEMENTATION.md
- COHERENCE_FRAMEWORK_MAINTENANCE_GAP_ANALYSIS.md
- COHERENCE_FRAMEWORK_SUCCESS_SUMMARY.md
- COHERENCE_FRAMEWORK_UPDATE_2025-10-18.md
- COHERENCE_FRAMEWORK_UPDATE_CONNECTION_PORTS.md
- COHERENCE_IMPLEMENTATION_SUMMARY.md

**Architecture Evolution**:
- BOTTOM_UP_DETERMINISM_AND_CUTS.md
- BOTTOM_UP_FINAL_ARCHITECTURE.md
- COMPREHENSIVE_ARCHITECTURE_SUMMARY.md
- CRITICAL_ARCHITECTURE_FIX.md
- D3_FORCE_REFACTORING_SUMMARY.md
- D3_WORKER_SIMPLIFICATION.md
- DIAGRAM_CONTROLLER_IMPLEMENTATION.md
- DIAGRAM_CONTROLLER_LAYERED_ARCHITECTURE.md
- DIAGRAM_CONTROLLER_TEST_RESULTS.md
- FINAL_ARCHITECTURE_SUMMARY.md
- LAYOUT_ENGINE_REFACTORING_STATUS.md
- UNIFIED_D3_ARCHITECTURE.md
- UNIFIED_SIMULATION_ARCHITECTURE.md

**Planning & Analysis**:
- ANNOTATION_SYSTEM_TEST_GUIDE.md
- CODE_CLEANUP_CANDIDATES.md
- COMPREHENSIVE_TEST_COVERAGE_PLAN.md
- CORE_CAPABILITIES_AND_COHERENCE_ANALYSIS.md
- CORE_CAPABILITIES_AND_TESTING_ANALYSIS.md
- COVERAGE_BASELINE_REPORT.md
- DOCUMENTATION_DRIFT_FIX_PLAN.md
- DOCUMENTATION_REVIEW_2025_10_12.md
- EXISTING_GUI_REVIEW_AND_FRESH_START_PLAN.md
- FOUNDATION_ASSESSMENT.md
- FOUNDATION_REPAIR_PLAN.md
- FOUNDATION_STATUS_UPDATE.md
- GOLDEN_MASTER_FINDINGS.md
- INTEGRATION_PLAN.md
- PASS_0_TOPOLOGICAL_ANALYSIS.md
- REALISTIC_COMPREHENSIVE_TESTING_ROADMAP.md
- REFACTORING_PLAN.md
- TESTING_ENHANCEMENT_PLAN.md
- TESTING_ENHANCEMENT_PROGRESS.md

**Data Model Evolution**:
- DIACHRONIC_SYNCHRONIC_DATA_MODEL_ANALYSIS.md
- UOD_EXECUTIVE_SUMMARY.md
- UOD_MODEL_TEST_RESULTS.md
- UOD_REFACTORING_SUMMARY.md

**Miscellaneous**:
- FOPL_EGI_TRANSLATION_VERIFICATION_REPORT.md
- PHASE_2_LAYOUT_COMPLETION_REPORT.md
- WHAT_WORKS_NOW.md
- QUALITY_REPORT.md
- GIT_RECOVERY_SYSTEM_SUMMARY.md

### 2. Debug Scripts (archive/debug_scripts/)

All one-off debugging scripts from root directory:
- debug_area_polarity.py
- debug_composition_area.py
- debug_composition_ins.py
- debug_d3_payload.py
- debug_deep_context.py
- debug_egi_structure.py
- debug_egif_corruption.py
- debug_ins_mapping.py
- debug_ins_variables.py
- debug_port_links.py
- debug_theoretical_verification.py
- debug_variable_mapping.py
- debug_vertex_sequence.py

### 3. Root-Level Test Scripts (archive/test_scripts/)

Test files that were in root (tests/ directory remains active):
- test_bottom_up_engine.py
- test_chapter16_compliance.py
- test_chapter18_translation_consistency.py
- test_chapter20_syntactic_equivalence.py
- test_chapter21_comprehensive.py
- test_chapter21_no_qt.py
- test_classical_syllogism_proof.py
- test_coherence_integration.py
- test_coherence_registry_complete.py
- test_complete_round_trip_translations.py
- test_comprehensive_integration.py
- test_core_architecture.py
- test_cut_layout_complex.py
- test_dau_chapter19_theoretical_verification.py
- test_dau_correspondence.py
- test_dau_theoretical_compliance.py
- test_debug_svg.py
- test_dto_handoff.py
- test_dynamic_transformations.py
- test_final_integration.py
- test_fixed_ins_transformation.py
- test_force_balance.py
- test_full_svg_pipeline.py
- test_hierarchical_areas.py
- test_ins_wizard_cut_flow.py
- test_integrated_managers.py
- test_interactive_viewer.py
- test_linear_forms.py
- test_nu_mapping_preservation.py
- test_organon_display.py
- test_organon_integration.py
- test_pass0_topology.py
- test_polarity_fix.py
- test_real_egi_data.py
- test_refactored_corpus.py
- test_simple_viewer.py
- test_simplified_integration.py
- test_simplified_round_trip_demo.py
- test_svg_rendering.py
- test_transformation_sequences_comprehensive.py
- test_transformation_validation.py
- test_unified_engine.py
- test_unified_engine_full.py
- test_unified_with_cuts.py
- test_unified_worker.py
- test_working_integration.py

### 4. Large Analysis Artifacts (archive/analysis_artifacts/)

**Large JSON Files**:
- COHERENCE_ANALYSIS_REPORT.md (753KB)
- ARISBE_CORE_API_REFERENCE.json (222KB)
- coherence_analysis.json (1MB)
- function_index.json (1MB)
- semantic_knowledge_graph.json (6.3MB)
- transformation_validation_report.json (7KB)

**Analysis Scripts**:
- analyze_codebase_orphans.py
- cleanup_orphaned_classes.py
- check_all_overlaps.py
- simple_debug.py
- example_transformation_history.py
- integration_demo.py
- working_integration_demo.py

**Miscellaneous Artifacts**:
- clean_egi_output.json
- test_clipboard_debug.py
- test_exactly_three_things_detailed.svg
- test_output.svg
- transformed_6.egif

### 5. Deprecated Code (archive/deprecated_code/)

**Backup Files from src/**:
- diagram_coordinator.py.backup (109KB)
- unified_d3_engine_recursive.py.bak
- unified_d3_worker_ejection.js.bak
- unified_d3_worker_recursive.js.bak
- definitive_three_pass_engine_backup.py

**Removed**:
- src/egi_spatial_correspondence.py (empty file - deleted)

## What Remains Active

### Essential Documentation (30+ files)
- README.md, AGENTS.md, CURRENT_PLAN.md
- PRODUCT_VISION.md, AI_CONDUCT_GUIDELINES.md
- Architecture docs (UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md, etc.)
- API docs (ARISBE_CORE_API_REFERENCE.md, etc.)
- Framework docs (COHERENCE_FRAMEWORK_REMINDER.md, etc.)

### Active Directories
- **src/** - All production code (177 files)
- **tests/** - Active test suite (58 files)
- **tools/** - Development tools (88 files)
- **corpus/** - Example graphs
- **tomos/** - Graph library (87 files)
- **docs/** - Reference documentation (62 files)
- **styles/** - Visual styles (8 files)

## Benefits of This Cleanup

1. **Clearer Focus**: Active development files immediately visible
2. **Reduced Confusion**: No mixing of historical with current state
3. **Preserved History**: All files remain in git history
4. **Better Navigation**: Easier to find current documentation
5. **Improved AI Context**: AI assistants focus on current architecture

## Accessing Archived Files

All archived files remain in git history and can be accessed:

```bash
# View archived file
git show HEAD:archive/documentation/PHASE_1_COMPLETION_REPORT.md

# Restore archived file if needed
git checkout HEAD -- archive/documentation/PHASE_1_COMPLETION_REPORT.md
```

## Notes

- The `tests/` directory remains fully active with 58 test files
- All production code in `src/` is untouched
- Development tools in `tools/` remain available
- Corpus and tomos directories are preserved
- Only root-level clutter was archived

---

**Last Updated**: 2025-12-26  
**Archived Files**: ~145 files  
**Total Space Organized**: ~10MB of documentation and artifacts
