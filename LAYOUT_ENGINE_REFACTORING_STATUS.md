# Layout Engine Refactoring Status

**Date**: 2025-01-10  
**Goal**: Fix critical architectural flaws in definitive_three_pass_engine.py

---

## ✅ Phase 1 Complete: Remove Graphviz Hints

### Changes Made
1. **Removed** `_extract_graphviz_positions()` call from Pass 1
2. **Removed** `_extract_graphviz_positions()` method entirely  
3. **Removed** Graphviz hint usage in `_layout_cut()` (lines 664-673)
4. **Updated** docstring with corrected architecture status

### Impact
- ✅ d3-force now starts from scratch (no bias from dot layout)
- ✅ Eliminates "chaining" problem
- ✅ Allows force simulation to find true low-energy states
- ✅ Proper separation: Pass 1 sizes, Pass 2 positions

### Test Results
- ✅ Engine still functional
- ✅ Generates valid DTOs
- ✅ No regressions in basic functionality
- ⏳ Visual quality needs corpus validation

---

## ⏳ Phase 2 Remaining: Recursive Bottom-Up

### What's Needed
1. **Rewrite `_pass2_content()`** to be truly recursive
2. **Layout order**: Innermost (leaf) cuts first
3. **Child propagation**: Child final sizes inform parent layout
4. **Fixed nodes**: Treat child cuts as large fixed obstacles in parent

### Current vs. Target

**Current** (Independent):
```python
def _pass2_content():
    for cut in all_cuts:
        layout_cut(cut)  # Each independent
```

**Target** (Recursive Bottom-Up):
```python
def _pass2_content():
    def layout_recursive(cut):
        for child in cut.children:
            child_box = layout_recursive(child)  # Children first
        
        # Layout this cut WITH children as fixed nodes
        return layout_cut(cut, child_boxes)
    
    layout_recursive(sheet)
```

---

## ⏳ Phase 3 Remaining: Geometric Ports

### What's Needed
1. **Remove** port nodes from dot input (_build_dot)
2. **Add** geometric calculation AFTER Pass 1 completes
3. **Calculate** intersection points between area centers and boundaries
4. **Use** these ports in Pass 2 d3-force and Pass 3 routing

### Algorithm
```python
def calculate_ports_geometrically():
    for each spanning ligature:
        from_center = get_area_center(from_area)
        to_center = get_area_center(to_area)
        
        # Find which boundary is crossed
        boundary_rect = determine_crossed_boundary()
        
        # Calculate intersection
        port_pos = line_rect_intersection(
            from_center, to_center, boundary_rect
        )
```

---

## ⏳ Phase 4 Remaining: Area-Aware A*

### What's Needed
1. **Implement** full area-aware A* pathfinding
2. **Add** validation logic for legal corridors
3. **Handle** obstacle avoidance properly
4. **Support** multi-segment paths through hierarchy

---

## 📊 Progress Summary

| Phase | Status | Complexity | Time Estimate |
|-------|--------|------------|---------------|
| Phase 1: Remove Hints | ✅ DONE | Low | ~30 min |
| Phase 2: Recursive Bottom-Up | ⏳ TODO | High | ~3-4 hrs |
| Phase 3: Geometric Ports | ⏳ TODO | Medium | ~2-3 hrs |
| Phase 4: Area-Aware A* | ⏳ TODO | Medium | ~1-2 hrs |

**Total Remaining**: ~6-9 hours of focused work

---

## 🎯 Recommendations

### Option A: Continue Immediately
- **Pro**: Momentum, architectural clarity
- **Con**: Large time investment now
- **Best if**: You have 6-9 hours available soon

### Option B: Test & Defer
- **Pro**: Validate Phase 1 impact first
- **Con**: Leaves architecture partially fixed
- **Best if**: Want to measure improvement before continuing

### Option C: Incremental Approach
- **Phase 1**: ✅ Done (test with corpus)
- **Phase 2**: Next session (recursive layout)
- **Phase 3**: Future session (geometric ports)
- **Phase 4**: Future session (A* pathfinding)
- **Best if**: Prefer smaller, testable increments

---

## 📈 Next Steps

### Immediate (Test Phase 1)
1. Run full corpus test suite
2. Compare visual output with backup engine
3. Measure quality improvement
4. Document any regressions

### Short Term (Decide on Phases 2-4)
- Review test results
- Assess priority (Organon vs. Layout)
- Schedule remaining phases
- Consider pausing for other work

### Long Term (Complete Refactoring)
- Finish all 4 phases
- Achieve fully correct three-pass architecture
- Validate against entire corpus
- Update documentation

---

## �� Technical Debt

**Current State**: Partially corrected architecture
- ✅ No position chaining
- ⏳ Ports still in dot (should be geometric)
- ⏳ Layout not yet recursive
- ⏳ Pathfinding still basic

**Future State**: Fully correct architecture
- ✅ Container sizing only (Pass 1)
- ✅ Geometric ports (post-Pass 1)
- ✅ Recursive bottom-up (Pass 2)
- ✅ Area-aware A* (Pass 3)

