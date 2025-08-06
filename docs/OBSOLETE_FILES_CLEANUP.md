# Obsolete Files Cleanup Analysis

## **CLEANUP OBJECTIVE**
Remove obsolescent, unused, or otherwise irrelevant files to eliminate contamination of future development with the canonical core established.

## **CATEGORIES OF OBSOLETE FILES**

### **1. Debug/Analysis Scripts (Root Level)**
These were temporary debugging tools and should be removed:
- `analyze_layout_problems.py`
- `analyze_visual_output.py`
- `apply_bounds_fix.py`
- `debug_containment_bug.py`
- `debug_containment_bugs.py`
- `debug_containment_detailed.py`
- `debug_cut_hierarchy.py`
- `debug_dot_syntax.py`
- `debug_graphviz_integration.py`
- `debug_gui_containment.py`
- `debug_layout_spacing.py`
- `debug_overlap_test.py`
- `debug_predicate_positioning.py`
- `debug_visual_output.py`
- `diagnose_dau_compliance.py`
- `diagnose_qt_rendering.py`
- `fix_containment_positioning.py`
- `fix_graphviz_layout.py`
- `fix_predicate_positioning.py`
- `generate_sample_egif_visuals.py`
- `generate_visual_examples.py`
- `improve_dau_visual_conventions.py`
- `simple_bounds_fix.py`
- `solidify_graphviz_modeling.py`

**RECOMMENDATION**: DELETE - These were temporary debugging tools

### **2. Experimental/Prototype Files (src/)**
These were experimental implementations that are superseded by canonical core:
- `annotation_system.py` (if not integrated into canonical)
- `arisbe_gui.py` (old GUI implementation)
- `arisbe_gui_integrated.py` (experimental integration)
- `audit_roundtrip.py` (superseded by canonical tests)
- `background_validation_system.py` (if not integrated)
- `canvas_backend.py` (if superseded)
- `canvas_contracts.py` (if superseded by canonical contracts)
- `constraint_layout_engine.py` (if superseded by Graphviz)
- `constraint_layout_integration.py` (if superseded)
- `constraint_layout_prototype.py` (prototype only)
- `containment_contracts.py` (if superseded by canonical contracts)
- `content_driven_layout.py` (if superseded)
- `dau_eg_renderer.py` (if superseded)
- `dau_subgraph_model.py` (if superseded)
- `dau_yaml_serializer.py` (if superseded by EGDF)
- `debug_direct_rendering.py` (debug tool)
- `debug_display_pipeline.py` (debug tool)

**RECOMMENDATION**: EVALUATE - Check if functionality is integrated into canonical core

### **3. Legacy/Deprecated Implementations**
Files that represent old approaches now superseded:
- Multiple `*_old.py`, `*_backup.py`, `*_deprecated.py` files
- Old GUI implementations before canonical standardization
- Experimental layout engines before Graphviz adoption
- Old contract systems before canonical contracts

**RECOMMENDATION**: DELETE - Superseded by canonical implementations

### **4. Test/Validation Files to Keep**
These should be preserved as they validate canonical functionality:
- `tests/minimal_pipeline_test.py` ✅ KEEP
- `tests/bidirectional_pipeline_test.py` ✅ KEEP  
- `tests/canonical_core_validation.py` ✅ KEEP
- Core test files that validate canonical pipeline

### **5. Documentation to Review**
Some documentation may be outdated:
- Old architecture docs that don't reflect canonical core
- Deprecated API documentation
- Experimental design documents

**RECOMMENDATION**: REVIEW - Update to reflect canonical core or remove if obsolete

## **CLEANUP STRATEGY**

### **Phase 1: Safe Removal (High Confidence)**
Remove files that are clearly temporary debugging tools:

```bash
# Debug/analysis scripts (root level)
rm analyze_layout_problems.py
rm analyze_visual_output.py
rm apply_bounds_fix.py
rm debug_*.py
rm diagnose_*.py
rm fix_*.py
rm generate_sample_egif_visuals.py
rm generate_visual_examples.py
rm improve_dau_visual_conventions.py
rm simple_bounds_fix.py
rm solidify_graphviz_modeling.py
```

### **Phase 2: Careful Evaluation (Medium Confidence)**
For each experimental file in src/, check:
1. Is functionality integrated into canonical core?
2. Is it referenced by canonical implementations?
3. Does it provide unique value not in canonical core?

If NO to all three → DELETE
If YES to any → KEEP or REFACTOR into canonical structure

### **Phase 3: Documentation Cleanup**
1. Update documentation to reflect canonical core
2. Remove outdated architecture descriptions
3. Ensure all examples use canonical APIs

## **BEFORE CLEANUP CHECKLIST**

- [ ] Verify canonical core tests pass (minimal_pipeline_test.py, bidirectional_pipeline_test.py, canonical_core_validation.py)
- [ ] Confirm no canonical implementations depend on files to be deleted
- [ ] Create backup branch before deletion
- [ ] Run full test suite after cleanup

## **POST-CLEANUP VALIDATION**

After cleanup, verify:
- [ ] All canonical core tests still pass
- [ ] No import errors in canonical implementations
- [ ] Documentation reflects current state
- [ ] Repository is clean and focused on canonical core

## **FILES TO DEFINITELY KEEP**

### **Core Canonical Implementation**
- `src/canonical/__init__.py` ✅
- `src/canonical/contracts.py` ✅
- `src/egi_core_dau.py` ✅
- `src/egif_parser_dau.py` ✅
- `src/egif_generator_dau.py` ✅
- `src/egdf_parser.py` ✅
- `src/graphviz_layout_engine_v2.py` ✅

### **Working GUI Implementation**
- `phase2_gui_foundation.py` ✅ (if this is the working version)
- `src/arisbe_gui_standard.py` ✅ (if this uses canonical core)

### **Corpus and Utilities**
- `src/corpus_loader.py` ✅
- `src/corpus_egif_generator.py` ✅

### **Tests and Validation**
- `tests/minimal_pipeline_test.py` ✅
- `tests/bidirectional_pipeline_test.py` ✅
- `tests/canonical_core_validation.py` ✅

### **Documentation**
- `docs/CANONICAL_CORE_STANDARDIZATION.md` ✅
- `docs/DISCIPLINED_DEVELOPMENT_FOUNDATION.md` ✅
- Current architecture and specification docs ✅

This cleanup will ensure the repository contains only canonical, tested, and documented implementations that support the standardized mathematical foundation.
