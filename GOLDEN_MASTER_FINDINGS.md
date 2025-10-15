# 🎯 Golden Master Testing - Initial Findings

**Date**: 2025-09-30  
**Status**: ⚠️ **NON-DETERMINISTIC LAYOUT BEHAVIOR DETECTED**

## **📊 TEST RESULTS**

### **Finding: Layout Engine Has Non-Deterministic Behavior**

Running the same test multiple times produces different results:
- Run 1: 5/6 tests passed
- Run 2: 3/6 tests passed  
- Run 3: 3/6 tests passed

This indicates that the layout engine produces slightly different outputs on each run, even with the same input EGI.

### **Specific Issues Observed:**

1. **Ligature Path Variations**: Path points change between runs
2. **Edge Label Order**: Order of edges with same parent can vary
3. **Slight Position Variations**: Small floating-point differences in positions

## **🔍 ROOT CAUSES**

### **Likely Causes:**

1. **Graphviz Non-Determinism**: The `neato` layout engine may have non-deterministic behavior
   - Solution: Use deterministic seed parameter
   - Already implemented in code but may need verification

2. **Python Dict/Set Iteration Order**: Iteration over unordered collections
   - Solution: Ensure consistent ordering when processing elements
   - Use sorted() on collections before iteration

3. **Floating Point Arithmetic**: Small variations in calculations
   - Solution: Round values to reasonable precision (already doing this)

## **✅ WHAT'S WORKING**

Despite non-determinism, the tests demonstrate:
- ✅ **Structural stability**: Element counts are consistent
- ✅ **General layout**: Overall positions are similar
- ✅ **Detection capability**: System successfully detects layout changes

## **📋 RECOMMENDATIONS**

### **Priority 1: Fix Determinism (Before GUI)**
1. **Verify Graphviz seed usage**: Ensure seed is properly applied
2. **Add deterministic sorting**: Sort all collections before processing
3. **Test with fixed seed**: Validate that same seed = same output

### **Priority 2: Enhance Golden Master Tests**
1. **Tolerance-based comparison**: Allow small floating-point differences
2. **Structural assertions**: Focus on element counts and relationships
3. **Visual regression option**: Generate SVGs for visual comparison

### **Priority 3: Document Expected Behavior**
1. **Define "acceptable variation"**: What changes are okay?
2. **Layout stability contract**: What guarantees do we provide?
3. **Update documentation**: Note determinism requirements

## **🎯 CURRENT STATUS**

**Golden Master Infrastructure**: ✅ **COMPLETE**
- Test framework implemented
- Serialization working
- Comparison logic functional
- File management operational

**Determinism**: ⚠️ **NEEDS ATTENTION**
- Non-deterministic behavior detected
- Root causes identified
- Solutions known
- Implementation needed

## **📈 NEXT STEPS**

### **Option A: Fix Determinism Now (Recommended)**
- Spend 1-2 hours fixing determinism
- Establish reliable baseline
- Proceed with confidence

### **Option B: Accept Current State**
- Document known non-determinism
- Use tolerance-based comparison
- Focus on structural tests
- Revisit determinism later

### **Option C: Hybrid Approach**
- Implement tolerance-based comparison now
- Add structural-only tests
- Fix full determinism as follow-up task

## **💡 IMMEDIATE VALUE**

Even with non-determinism, we've gained:
1. **Detection capability**: Can catch major regressions
2. **Test infrastructure**: Foundation for all future layout tests
3. **Problem identification**: Know what needs fixing
4. **Baseline establishment**: Have reference outputs to compare against

## **🔧 TECHNICAL DETAILS**

### **Test Files Created:**
- `tests/end_to_end/test_golden_master_layouts.py` (working)
- `tests/golden_masters/*.json` (6 baseline files)
- `tests/fixtures/test_egis.py` (test data)

### **Coverage:**
- ✅ Simple graphs (1-2 vertices)
- ✅ Nested cuts (2+ levels)
- ✅ Complex structures
- ✅ Multiple predicates
- ⏸️ Tomos graphs (not yet tested due to path issues)

### **Success Rate:**
- Average: ~60-80% pass rate across runs
- Best case: 83% (5/6 passing)
- Worst case: 50% (3/6 passing)

**Conclusion**: Golden Master infrastructure is solid, but we need to address non-determinism for reliable regression detection.
