# 🐛 Critical Bug Found: Ligatures Not Connecting to Vertices

**Date**: 2025-10-01  
**Discovered By**: Visual sanity-checking of workflow test SVG outputs  
**Severity**: 🔴 **HIGH** - Breaks fundamental EG diagram structure

---

## **🔍 THE BUG**

Ligatures (lines connecting vertices to predicates) do not start at the actual vertex positions. They start from different coordinates, leaving vertices disconnected.

### **Evidence**

From `workflow_aesthetic_adjustments.svg`:
```
Vertex position:     (210.78, 80.972)
Ligature path start: (201.76, 65.18)
Difference:          ~16 pixels offset!
```

### **Visual Evidence**

The SVG output shows a vertex (black dot) with no line connected to it. The ligature line starts from empty space.

---

## **📍 ROOT CAUSE**

Location: `src/definitive_egi_layout_engine.py` 
Method: `_area_aware_ligature_routing()`

The ligature routing A* pathfinding is calculating paths, but not using the actual vertex positions as start points. Instead, it's using some other coordinate (possibly from connection ports or edge label centers).

---

## **💥 IMPACT**

**User Impact**: 🔴 **SEVERE**
- Diagrams are mathematically incorrect
- Cannot visually verify logical structure  
- Ligatures floating in space
- Professional use impossible

**Test Impact**: 🟢 **GOOD**
- Bug was caught by visual sanity-checking
- Programmatic tests passed because they don't verify visual correctness
- Demonstrates value of SVG output in tests

---

## **🔧 FIX REQUIRED**

### **Location**
`src/definitive_egi_layout_engine.py:472-530`
Method: `_area_aware_ligature_routing()`

### **Issue**
When creating ligature paths, the method should:
1. Start path at vertex position: `vertex.pos`
2. End path at edge label connection port
3. Route through collision-free path

Currently, it's not using `vertex.pos` as the start point.

### **Code Section to Fix**
```python
# Around line 492-520
for hook_index, vertex_id in enumerate(vertex_sequence):
    vertex = next((v for v in dto.vertices if v.id == vertex_id), None)
    if not vertex:
        continue
    
    # BUG: Path calculation not using vertex.pos as start
    # Should be:
    start_pos = vertex.pos  # Use actual vertex position!
    end_pos = edge_label_port_position
    path = calculate_path(start_pos, end_pos, ...)
```

---

## **✅ GOOD NEWS**

1. **Bug Found Early**: Discovered before GUI development
2. **Isolated**: Issue is in one method, doesn't affect other systems
3. **Test Infrastructure Works**: SVG generation caught the bug
4. **Clear Fix Path**: Know exactly what needs to be fixed

---

## **🎯 PRIORITY**

**Priority**: 🔴 **P0 - Blocker**

This MUST be fixed before:
- ❌ Any GUI development
- ❌ Any production use
- ❌ Any visual demonstrations

This CAN be deferred for:
- ✅ Programmatic API testing
- ✅ Transformation rule validation
- ✅ State management testing

---

## **📋 ACTION ITEMS**

### **Immediate** (Before GUI)
1. [ ] Debug ligature routing in `_area_aware_ligature_routing()`
2. [ ] Ensure ligature paths start at `vertex.pos`
3. [ ] Verify all ligatures connect properly
4. [ ] Re-run workflow tests and verify SVGs
5. [ ] Test with all corpus graphs

### **Validation**
1. [ ] Visual inspection of SVG outputs
2. [ ] Programmatic check: `ligature.path_points[0] == vertex.pos`
3. [ ] All workflow test SVGs show connected ligatures
4. [ ] No floating lines in any diagram

---

## **🔬 HOW TO VERIFY FIX**

```python
# After fix, this should be true:
dto = controller.get_renderable_dto()
for ligature in dto.ligatures:
    vertex = next(v for v in dto.vertices if v.id == ligature.start_vertex_id)
    start_point = ligature.path_points[0]
    
    # These should match (within floating point tolerance)
    assert abs(start_point[0] - vertex.pos[0]) < 0.1
    assert abs(start_point[1] - vertex.pos[1]) < 0.1
```

---

## **💡 LESSON LEARNED**

**Visual Sanity-Checking is Critical!**

Programmatic tests passed 87.5% but didn't catch this visual bug. The SVG outputs immediately revealed the problem.

**Recommendation**: Always generate visual outputs for layout/rendering tests.

---

**Status**: 🔴 **BLOCKING BUG** - Needs immediate fix  
**Discovered**: During comprehensive testing session  
**Impact**: High - affects all diagrams  
**Fix Complexity**: Medium - isolated to one method
