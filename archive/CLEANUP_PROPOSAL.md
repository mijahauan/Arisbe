# Repository Cleanup Proposal

## Overview
The repository has accumulated significant documentation, debugging scripts, and test files from various development stages. This proposal organizes files into categories for archival.

## Archive Structure
```
archive/
├── documentation/          # Historical docs, phase reports, session summaries
├── debug_scripts/          # One-off debug scripts from root
├── test_scripts/           # Root-level test scripts (tests/ dir stays)
├── analysis_artifacts/     # Large JSON analysis files
└── deprecated_code/        # Backup files, deprecated implementations
```

## Files to Archive

### 1. Historical Documentation (65+ files) → archive/documentation/

**Phase/Session Reports** (should be archived):
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

**Implementation/Completion Reports** (historical):
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

**Coherence Framework Historical** (superseded by current AGENTS.md):
- COHERENCE_FRAMEWORK_100_PERCENT_COMPLETE.md
- COHERENCE_FRAMEWORK_ANALYSIS_2025.md
- COHERENCE_FRAMEWORK_COMPLETE_EXPLANATION.md
- COHERENCE_FRAMEWORK_IMPLEMENTATION.md
- COHERENCE_FRAMEWORK_MAINTENANCE_GAP_ANALYSIS.md
- COHERENCE_FRAMEWORK_SUCCESS_SUMMARY.md
- COHERENCE_FRAMEWORK_UPDATE_2025-10-18.md
- COHERENCE_FRAMEWORK_UPDATE_CONNECTION_PORTS.md
- COHERENCE_IMPLEMENTATION_SUMMARY.md

**Architecture Evolution** (historical):
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

**Analysis/Planning** (historical):
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

**UoD Model Evolution** (historical):
- DIACHRONIC_SYNCHRONIC_DATA_MODEL_ANALYSIS.md
- UOD_EXECUTIVE_SUMMARY.md
- UOD_MODEL_TEST_RESULTS.md
- UOD_REFACTORING_SUMMARY.md

**Test Reports** (historical):
- FOPL_EGI_TRANSLATION_VERIFICATION_REPORT.md
- PHASE_2_LAYOUT_COMPLETION_REPORT.md

**Miscellaneous** (historical):
- WHAT_WORKS_NOW.md
- QUALITY_REPORT.md
- GIT_RECOVERY_SYSTEM_SUMMARY.md

### 2. Debug Scripts (13 files) → archive/debug_scripts/
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

### 3. Root-Level Test Scripts (46 files) → archive/test_scripts/
**Note**: Keep `tests/` directory intact - only archive root-level test scripts

- test_bottom_up_engine.py
- test_chapter16_compliance.py
- test_chapter18_translation_consistency.py
- test_chapter20_syntactic_equivalence.py
- test_chapter21_comprehensive.py
- test_chapter21_no_qt.py
- test_classical_syllogism_proof.py
- test_clipboard_debug.py
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

### 4. Large Analysis/Generated Files → archive/analysis_artifacts/
- COHERENCE_ANALYSIS_REPORT.md (753KB)
- ARISBE_CORE_API_REFERENCE.json (222KB)
- coherence_analysis.json (1MB)
- function_index.json (1MB)
- semantic_knowledge_graph.json (6.3MB)
- transformation_validation_report.json (7KB)

### 5. Deprecated Code in src/ → archive/deprecated_code/
- src/diagram_coordinator.py.backup (109KB)
- src/unified_d3_engine_recursive.py.bak
- src/unified_d3_worker_ejection.js.bak
- src/unified_d3_worker_recursive.js.bak
- src/definitive_three_pass_engine_backup.py
- src/egi_spatial_correspondence.py (0 bytes - empty file)

### 6. Miscellaneous Root Files → archive/analysis_artifacts/
- analyze_codebase_orphans.py
- cleanup_orphaned_classes.py
- check_all_overlaps.py
- simple_debug.py
- example_transformation_history.py
- integration_demo.py
- working_integration_demo.py
- clean_egi_output.json
- test_exactly_three_things_detailed.svg
- test_output.svg
- transformed_6.egif

## Files to KEEP (Active/Essential)

### Essential Documentation
- **README.md** - Main project documentation
- **AGENTS.md** - Development guidelines (CRITICAL)
- **CURRENT_PLAN.md** - Current development roadmap
- **PRODUCT_VISION.md** - Project vision
- **AI_CONDUCT_GUIDELINES.md** - AI assistant guidelines

### Core Architecture Documentation
- **UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md** - Fundamental philosophy
- **UOD_DEVELOPER_GUIDE.md** - Developer guide for UoD
- **DAG_HISTORY_ARCHITECTURE.md** - DAG history system
- **CORE_DAU_FORMALISM_ARCHITECTURE.md** - Core formalism
- **GRAPH_ENTITY_SCALABILITY_ARCHITECTURE.md** - Scalability design

### API & Usage Documentation
- **ARISBE_CORE_API_REFERENCE.md** - API documentation
- **ARISBE_STABLE_API_REFERENCE.md** - Stable API subset
- **CORE_API_USAGE_GUIDE.md** - Usage patterns
- **CORPUS_API_QUICK_REFERENCE.md** - Corpus API
- **IMPORT_EXPORT_FORMATS.md** - Format documentation

### Active Architecture Documentation
- **CHAPTER21_DIAGRAM_ARCHITECTURE_PLAN.md** - Chapter 21 implementation
- **LAYOUT_ENGINE_ARCHITECTURE_PLAN.md** - Layout engine design
- **GUI_ARCHITECTURE_DESIGN.md** - GUI architecture
- **GUI_IMPLEMENTATION_PLANNING.md** - GUI implementation plan
- **ORGANON_COMPLETE_SPECIFICATION.md** - Organon spec
- **ORGANON_READY.md** - Organon status

### Data Model Documentation
- **EGI_DATA_MODEL_SUMMARY.md** - EGI data model
- **DATA_PERSISTENCE_MODEL_SUMMARY.md** - Persistence model
- **DIACHRONIC_DELTA_WORKFLOW.md** - Delta workflow
- **LAYOUT_DELTA_QUICK_REFERENCE.md** - Layout deltas

### Framework Documentation
- **CODEBASE_COHERENCE_FRAMEWORK.md** - Coherence framework
- **COHERENCE_FRAMEWORK_REMINDER.md** - Quick reminder
- **FRAMEWORK_AMNESIA_RECOVERY.md** - Recovery guide
- **PERSISTENT_CONTEXT_SYSTEM.md** - Context system
- **CONTEXT_AWARENESS_REMINDER.md** - Context awareness
- **RETURN_TO_DEVELOPMENT_GUIDE.md** - Return guide

### Workflow Documentation
- **GIT_WORKFLOW_STRATEGY.md** - Git workflow
- **CORE_PROTECTION_FRAMEWORK.md** - Core protection
- **PATTERN_CATALOG.md** - Design patterns
- **ARISBE_UX_ARCHITECTURE.md** - UX architecture

### Utility Files
- **ARCHITECTURE_MAP.md** - Architecture overview
- **FUNCTION_INDEX_REPORT.md** - Function index
- **NEW_COMPONENTS_API_REFERENCE.md** - New components

## Recommended Actions

1. **Create archive/ directory structure**
2. **Move files systematically** (not delete - preserve history)
3. **Update AGENTS.md** - Remove references to archived docs
4. **Update README.md** - Ensure current state is accurate
5. **Create ARCHIVE_INDEX.md** - Document what's archived and why
6. **Add .gitignore entries** for archive/ if desired (or keep in git for history)

## Benefits

- **Clearer focus**: Active development files are immediately visible
- **Reduced confusion**: No mixing of historical/deprecated with current
- **Preserved history**: Nothing deleted, just organized
- **Easier onboarding**: New developers see current state first
- **Better AI context**: AI assistants won't be distracted by outdated info

## Next Steps

Should I proceed with creating the archive structure and moving files?
