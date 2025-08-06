# Disciplined Development Foundation

## **ARCHITECTURAL DISCIPLINE REQUIREMENTS**

Based on user requirements, all development must now adhere to these non-negotiable principles:

### **1. Complete Pipeline Compliance**
- **EGIF→EGI→EGDF pipeline** with API contract validation
- **No shortcuts or bypasses** - every component uses the complete pipeline
- **Contract validation** at every handoff point
- **Round-trip integrity** guaranteed

### **2. PySide6/QPainter Standard**
- **PySide6/QPainter exclusively** for all GUI rendering
- **No Tkinter** in core modules or new development
- **Consistent backend** across all components
- **Professional rendering quality**

### **3. Corpus Integration Mandatory**
- **All GUIs must integrate corpus** for examples and testing
- **Corpus-driven development** - validate against authoritative examples
- **Educational support** - users can access validated examples
- **Testing foundation** - corpus examples validate functionality

### **4. Clean Codebase**
- **No deprecated code references** (hook_line, obsolete patterns)
- **No placeholder implementations** (TODO/FIXME must be resolved)
- **No API confusion** - clear contracts at all boundaries
- **Systematic cleanup** before any new development

### **5. Core Test Suite**
- **Pipeline validation tests** must pass before any development
- **Regression prevention** - tests catch breaking changes immediately
- **Contract enforcement** - API violations detected automatically
- **Continuous validation** - run tests at every development stage

## **IMPLEMENTATION STATUS**

### ✅ **Working Foundation Confirmed**
- Minimal pipeline test passes completely
- EGIF→EGI→Layout pipeline functional
- Corpus integration working (5 examples)
- PySide6 available and importable
- GraphvizLayoutEngine producing spatial primitives

### 🎯 **Immediate Priorities**

1. **Complete EGDF Integration**
   - Fix EGDFParser API to match actual implementation
   - Ensure EGIF→EGI→EGDF→EGI round-trip works
   - Add contract validation for EGDF handoffs

2. **Systematic Code Cleanup**
   - Remove all hook_line references (25+ found)
   - Remove obsolete validation files
   - Resolve all TODO/FIXME comments
   - Standardize on working APIs

3. **Standard GUI Implementation**
   - Build on phase2_gui_foundation.py (proven working)
   - Enforce complete pipeline with contracts
   - Integrate corpus throughout
   - Use PySide6/QPainter exclusively

4. **Core Test Suite Enhancement**
   - Fix core_pipeline_tests.py to use actual APIs
   - Add comprehensive contract validation
   - Ensure all corpus examples work through pipeline
   - Prevent regressions with automated testing

## **DEVELOPMENT WORKFLOW**

### **Before Any New Development:**
1. Run `python tests/minimal_pipeline_test.py` - must pass
2. Run code cleanup script - remove deprecated references
3. Verify PySide6/QPainter usage only
4. Ensure corpus integration present

### **During Development:**
1. Use complete EGIF→EGI→EGDF pipeline with contracts
2. Validate against corpus examples
3. Run tests continuously
4. No shortcuts or experimental abstractions

### **After Development:**
1. Run full core test suite - must pass
2. Verify no regressions in pipeline
3. Confirm corpus examples still work
4. Document any API changes

## **ARCHITECTURAL PRINCIPLES**

### **From Memories - Critical Requirements:**

1. **NO HOOK LINES** - Hooks are invisible positions, not drawn lines
2. **Heavy Lines of Identity** - Primary visual elements, 4.0pt width
3. **Area-Centric Positioning** - Predicates positioned by logical area, not vertex proximity
4. **Complete Containment** - Elements entirely within designated areas
5. **Action-Driven Selection** - User chooses action first, then selects appropriate elements
6. **EGI as Canonical** - All operations map to formal EGI transformations

### **Pipeline Architecture:**
```
EGIF → EGIFParser → RelationalGraphWithCuts → GraphvizLayoutEngine → 
SpatialPrimitives → EGDFGenerator → EGDFDocument → PySide6/QPainter
```

### **Contract Validation:**
- Every handoff point has explicit contracts
- Runtime validation catches API mismatches
- No "what object am I receiving?" confusion
- Automatic error detection and reporting

## **SUCCESS CRITERIA**

Development is successful when:
- ✅ All core tests pass
- ✅ Complete pipeline works with contracts
- ✅ Corpus examples render correctly
- ✅ PySide6/QPainter rendering quality
- ✅ No deprecated code references
- ✅ Clean, maintainable architecture

## **FAILURE PREVENTION**

Development fails when:
- ❌ Core tests don't pass
- ❌ Pipeline shortcuts or bypasses
- ❌ Mixed backends (Tkinter + PySide6)
- ❌ Deprecated code references remain
- ❌ API confusion between components
- ❌ Corpus integration missing

This foundation ensures disciplined, sustainable development that builds on proven working components while maintaining mathematical rigor and professional quality.
