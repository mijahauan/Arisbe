# DiagramController & Layout Engine Integration Assessment

**Date**: 2025-10-08  
**Status**: ⚠️ **NOT YET INTEGRATED** - Integration work required

## Executive Summary

The new `DefinitiveThreePassEngine` provides significant improvements over the old `DefinitiveEGILayoutEngine`:
- ✅ Hybrid Graphviz + D3 + A* approach for better quality
- ✅ Port-based cross-cut ligature routing
- ✅ Obstacle-aware element positioning
- ✅ 100% corpus validation (14 graphs passing)

However, **DiagramController is still using the old engine** and requires integration work to adopt the new engine.

## Current State

### DiagramController Configuration
```python
# From src/diagram_controller.py line 68
self.layout_engine = DefinitiveEGILayoutEngine()
```

**Status**: Using OLD layout engine

### Layout Engine Interface Used by Controller
```python
# From src/diagram_controller.py lines 291-295
self.current_dto = self.layout_engine.generate_layout(
    self.egi_model,
    self.current_style,
    deltas_obj  # LayoutDeltas for user position overrides
)
```

## Interface Comparison

### Old Engine: DefinitiveEGILayoutEngine
```python
def generate_layout(
    self,
    egi: RelationalGraphWithCuts,
    style: Optional[StyleSpecification] = None,
    layout_deltas: Optional[LayoutDeltas] = None
) -> LayoutDTO
```

**Key Features:**
- Accepts `layout_deltas` for user position overrides
- Returns compatible `LayoutDTO`
- Supports deterministic seeding
- Handles pinned node positions

### New Engine: DefinitiveThreePassEngine
```python
def generate_layout(
    self,
    egi: RelationalGraphWithCuts,
    style: Optional[StyleSpecification] = None,
    debug_prefix: Optional[str] = None
) -> LayoutDTO
```

**Key Features:**
- **MISSING**: `layout_deltas` parameter
- Returns compatible `LayoutDTO` ✅
- Superior visual quality
- Production-ready with 100% corpus validation

## Critical Integration Gaps

### 🚨 Gap 1: Missing LayoutDeltas Support

**Problem**: The new engine does NOT accept `layout_deltas` parameter for user position overrides.

**Impact**:
- DiagramController cannot pass user-defined positions
- User edits in Ergasterion mode will not work
- Deterministic layouts with pinned nodes not supported

**Required Fix**:
```python
# Add to DefinitiveThreePassEngine
def generate_layout(
    self,
    egi: RelationalGraphWithCuts,
    style: Optional[StyleSpecification] = None,
    layout_deltas: Optional[LayoutDeltas] = None,  # ADD THIS
    debug_prefix: Optional[str] = None
) -> LayoutDTO
```

**Implementation Notes:**
- User position overrides should be applied in Pass 2 (D3 layout)
- Set `fx` and `fy` on D3 nodes for pinned positions
- Apply custom ligature paths in Pass 3 (A* routing) with fallback to auto-routing if invalid

### 🚨 Gap 2: Deterministic Seeding

**Problem**: DiagramController expects deterministic layouts with consistent seeds.

**Current Code** (in DiagramController):
```python
deltas_obj.deterministic_seed = 42  # Consistent layouts
```

**Required Fix**:
- New engine must respect deterministic seed in D3 simulation
- Same EGI + same style + same seed = identical layout

### Gap 3: GUI Integration Points

**Problem**: GUI components may reference old engine-specific behavior.

**Affected Components**:
- `src/gui/interactive_egi_viewer.py`
- `src/gui/diagram_editor.py`
- Any component that directly instantiates layout engines

**Required Review**:
- Audit all GUI files for layout engine imports
- Verify they use DiagramController interface (not direct engine calls)

## LayoutDTO Compatibility

✅ **GOOD NEWS**: Both engines return the same LayoutDTO structure:

```python
@dataclass
class LayoutDTO:
    areas: List[RenderableArea]
    vertices: List[RenderableVertex]
    edge_labels: List[RenderableEdgeLabel]
    ligatures: List[RenderableLigature]
```

**No changes required** for DTO consumers (SVG renderer, GUI components).

## Integration Roadmap

### Phase 1: Add LayoutDeltas Support to New Engine ⚠️ **REQUIRED**

**Tasks:**
1. Add `layout_deltas` parameter to `generate_layout()` signature
2. Implement pinned node support in Pass 2 (D3 layout):
   ```javascript
   // In d3_layout_worker.js
   if (pinnedPositions[node.id]) {
       node.fx = pinnedPositions[node.id].x;
       node.fy = pinnedPositions[node.id].y;
   }
   ```
3. Implement custom ligature paths in Pass 3 with validation
4. Add deterministic seeding to D3 simulation

**Test Coverage:**
- Unit tests for pinned positions
- Integration tests with LayoutDeltas
- Regression tests against old engine behavior

### Phase 2: Update DiagramController 🔄

**Tasks:**
1. Replace old engine import:
   ```python
   # OLD
   from definitive_egi_layout_engine import DefinitiveEGILayoutEngine
   
   # NEW
   from definitive_three_pass_engine import DefinitiveThreePassEngine
   ```

2. Update controller initialization:
   ```python
   self.layout_engine = DefinitiveThreePassEngine()
   ```

3. Update `_trigger_full_relayout()` if needed for new interface

**Verification:**
- All 11 DiagramController tests must pass
- All 8 workflow simulation tests must pass
- GUI Organon mode must render correctly

### Phase 3: GUI Integration Testing 🎨

**Tasks:**
1. Test Organon mode (read-only visualization)
2. Test Ergasterion mode (interactive editing with position overrides)
3. Test Agon mode (gameplay with transformations)
4. Verify all 15 corpus graphs render correctly
5. Test user position overrides in interactive mode

**Success Criteria:**
- No visual regressions
- User edits persist correctly
- Deterministic layouts work
- All transformation rules preserve aesthetics

### Phase 4: Cleanup & Documentation 📚

**Tasks:**
1. Archive old `DefinitiveEGILayoutEngine` (move to `archive/`)
2. Update AGENTS.md with integration notes
3. Add migration guide for external code
4. Update API documentation

## Compatibility Matrix

| Feature | Old Engine | New Engine | Status |
|---------|-----------|-----------|--------|
| Basic layout | ✅ | ✅ | Compatible |
| LayoutDTO output | ✅ | ✅ | Compatible |
| StyleSpecification input | ✅ | ✅ | Compatible |
| LayoutDeltas support | ✅ | ❌ | **MISSING** |
| Deterministic seeding | ✅ | ❌ | **MISSING** |
| Port-based routing | ❌ | ✅ | New feature |
| D3 force layout | ❌ | ✅ | New feature |
| Visual quality | 🟡 | ✅ | Improved |

## Risk Assessment

### Low Risk
- LayoutDTO compatibility ensures renderer works without changes
- New engine has 100% corpus validation
- Architecture supports both engines during transition

### Medium Risk
- LayoutDeltas implementation requires careful D3 integration
- Deterministic seeding may affect visual consistency
- GUI testing across three modes needed

### High Risk
- User position overrides are CRITICAL for Ergasterion mode
- Any breakage blocks interactive editing
- Must maintain backward compatibility with existing saved states

## Recommendations

### Immediate Actions (Priority 1)
1. ✅ **Add LayoutDeltas parameter** to new engine signature
2. ✅ **Implement pinned positions** in D3 worker
3. ✅ **Add deterministic seeding** to D3 simulation
4. ⚠️ **Test with DiagramController** before switching

### Near-term Actions (Priority 2)
1. Create feature branch for integration work
2. Run full test suite (core + GUI + workflow)
3. Document any breaking changes
4. Create migration path for saved user edits

### Long-term Actions (Priority 3)
1. Archive old engine after successful migration
2. Optimize D3 force parameters (balance port vs normal links)
3. Add visual regression tests
4. Performance benchmarking

## Force Balance Issue

**Note**: The new engine has a known issue where port link forces (50.0) overwhelm normal link forces (4.0), causing elements with mixed connections to drift apart (see `roberts_domain_modeling` example where Professor and vertex *x end up far apart).

**Impact on DiagramController**: User position overrides will help mitigate this by allowing users to manually adjust problematic layouts.

**Future Work**: Implement adaptive force balancing that considers connection types.

## Conclusion

The new `DefinitiveThreePassEngine` represents a significant quality improvement, but **requires LayoutDeltas integration** before it can replace the old engine in DiagramController. 

**Estimated Integration Time**: 2-3 days
- Day 1: Add LayoutDeltas support to new engine
- Day 2: Switch DiagramController and run tests
- Day 3: GUI integration testing and bug fixes

**Go/No-Go Decision**: Integration should proceed after LayoutDeltas implementation is complete and tested.
