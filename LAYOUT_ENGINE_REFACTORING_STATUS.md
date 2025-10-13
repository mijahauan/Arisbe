# Layout Engine Refactoring Status

**Date**: 2025-01-10  
**Goal**: Fix critical architectural flaws in definitive_three_pass_engine.py

**STATUS**: ✅ **PHASES 1-3 COMPLETE** (Phase 4 deferred)

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

## ✅ Phase 2 Complete: Recursive Bottom-Up Layout

### Changes Made
1. **Rewrote** `_pass2_content()` for true recursion
2. **Implemented** bottom-up traversal (innermost cuts first)
3. **Changed** `_layout_cut()` signature to accept `child_boxes` parameter
4. **Updated** obstacle handling to use `child_boxes` instead of hierarchy lookup
5. **Added** return value to `layout_recursive()` for bounding box propagation

### Impact
- ✅ True bottom-up: children laid out before parents
- ✅ Child cuts explicitly treated as large fixed obstacles
- ✅ Foundation for dynamic container sizing (future)
- ✅ Clean separation between layout order and spatial constraints

### Test Results
- ✅ Simple graphs: Working
- ✅ Nested structures: Working
- ✅ Output message: "(bottom-up)" confirms new algorithm

---

## ✅ Phase 3 Complete: Geometric Port Calculation

### Changes Made
1. **Removed** port nodes from dot input (`_build_dot`)
2. **Removed** port extraction from `_parse_dot_output`
3. **Renamed** `_calculate_ports()` → `_calculate_ports_geometrically()`
4. **Added** geometric port calculation call after Pass 1
5. **Simplified** edge addition (no port routing in dot)
6. **Updated** all docstrings to reflect geometric calculation

### Architecture
```python
# OLD (incorrect): Ports in dot input
dot_content = build_dot_with_port_nodes()
ports = extract_from_dot_output()

# NEW (correct): Ports calculated geometrically
dot_content = build_dot_without_ports()  # Sizing only
area_bounds = extract_cluster_geometry()  # KEEP
# node_positions DISCARDED
ports = calculate_geometrically(area_bounds)  # After Pass 1
```

### Impact
- ✅ Ports NO LONGER in dot input
- ✅ Calculated from fixed container boundaries
- ✅ Line-rectangle intersection for boundary crossings
- ✅ True separation: Pass 1 sizes, post-processing calculates ports

---

## ⏳ Phase 4 Deferred: Area-Aware A* Pathfinding

### Current State
- Simple straight-line ligature routing
- Basic path generation

### What's Needed (Future Work)
1. **Implement** full area-aware A* pathfinding algorithm
2. **Add** validation logic for legal corridors
3. **Handle** obstacle avoidance (vertices, edges, cuts)
4. **Support** multi-segment curved paths
5. **Enforce** ligature rules (same-area avoid cuts, cross-area can cross)

### Deferral Reason
- Phases 1-3 provide substantial improvement
- Current routing functional for Organon display
- A* pathfinding is complex enhancement (separate effort)
- Focus on getting Organon working with improved layout

---

## 📊 Progress Summary

| Phase | Status | Complexity | Time Spent |
|-------|--------|------------|------------|
| Phase 1: Remove Hints | ✅ DONE | Low | ~30 min |
| Phase 2: Recursive Bottom-Up | ✅ DONE | High | ~45 min |
| Phase 3: Geometric Ports | ✅ DONE | Medium | ~30 min |
| Phase 4: Area-Aware A* | ⏳ DEFERRED | High | Future |

**Total Completed**: Phases 1-3 (~1.75 hours)
**Deferred**: Phase 4 (future enhancement)

---

## 🎉 **PHASES 1-3 COMPLETE!**

### What We Achieved

**✅ Correct Three-Pass Architecture Implemented**:
1. **Pass 1**: Graphviz sizes containers only (node positions discarded)
2. **Post-Pass 1**: Ports calculated geometrically from boundaries
3. **Pass 2**: d3-force in true recursive bottom-up order
4. **Pass 3**: Ligature routing (simple, with A* deferred)

**✅ Architectural Flaws Fixed**:
- ❌ Graphviz position chaining → ✅ d3 discovers positions
- ❌ Independent cut layouts → ✅ Recursive bottom-up
- ❌ Ports in dot input → ✅ Geometric calculation

### Next Steps

**Immediate**:
1. Test with full corpus
2. Compare visual quality with backup
3. Validate in Organon

**Future** (Phase 4):
- Add ligature validation
- Support curved paths

---

## 🔍 Technical Debt Status

**Before Refactoring**:
- ❌ Graphviz positions used as d3 hints (chaining problem)
- ❌ Independent per-cut layouts (not bottom-up)
- ❌ Ports embedded in dot input (not geometric)
- ❌ Simple straight-line routing

**After Phases 1-3** (Current):
- ✅ No position chaining (d3 discovers optimal layout)
- ✅ True recursive bottom-up layout
- ✅ Geometric port calculation
- ⏳ Simple routing (A* deferred)

**Remaining Technical Debt**:
- Area-aware A* pathfinding (Phase 4 - future)
- Dynamic container sizing based on content
- Curved ligature paths
- Obstacle avoidance optimization
