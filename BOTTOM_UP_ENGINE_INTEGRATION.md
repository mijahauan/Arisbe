# Bottom-Up D3 Engine Integration with Organon

## Integration Status: ✅ COMPLETE

**Date:** 2025-01-11  
**Engine:** `BottomUpD3Engine` (pure d3-force, no Graphviz)  
**Replaced:** `DefinitiveThreePassEngine`  

---

## Changes Made

### 1. Created New Engine: `src/bottom_up_d3_engine.py`

**Key Features:**
- ✅ No Graphviz Pass 1 (removed size guessing)
- ✅ True bottom-up recursion
- ✅ Content determines container size
- ✅ Tight bounding boxes calculated from actual positions
- ✅ Custom containment force teaches d3 about walls
- ✅ API-compliant (uses `egi.get_relation_name()`, `egi.get_incident_vertices()`)

**Interface:**
```python
def generate_layout(egi, style, deltas=None) -> LayoutDTO:
    """
    Generate layout using pure bottom-up d3-force.
    
    Args:
        egi: RelationalGraphWithCuts model
        style: StyleSpecification
        deltas: Optional user position overrides (placeholder for future)
    
    Returns:
        LayoutDTO with positioned elements and dynamically-sized areas
    """
```

### 2. Updated D3 Worker: `src/d3_layout_worker.js`

**Simplified Force Strategy:**
```javascript
// 4 forces that cooperate (not compete):
1. forceLink (0.7 strength, 30px distance) - Keep connected elements together
2. forceCollide (1.0 strength) - Prevent all overlaps
3. forceCenter (0.05 strength) - Gentle nudge toward center
4. forceContainment (custom) - TAUGHT RULE - enforce walls every tick
```

**Key Improvement:**
- Elements start clustered (30px radius from center)
- Initial positions clamped to bounds (prevents starting outside)
- Containment force zeros ALL velocity when violation occurs
- 500 iterations for stable equilibrium

### 3. Integrated with GUI: `src/diagram_controller.py`

**Changes:**
```python
# OLD:
from definitive_three_pass_engine import DefinitiveThreePassEngine
self.layout_engine = DefinitiveThreePassEngine()

# NEW:
from bottom_up_d3_engine import BottomUpD3Engine
self.layout_engine = BottomUpD3Engine()
```

**Compatibility:**
- ✅ Same interface as old engine
- ✅ Accepts `deltas` parameter (reserved for future user overrides)
- ✅ Returns compatible `LayoutDTO`

---

## Architecture Comparison

### Old: Flawed Two-Pass

```
Pass 1 (Graphviz):
  - GUESS container sizes using heuristics
  - est_width = content_count * 1.0  # WRONG!
  
Pass 2 (d3-force):
  - Try to fit content into guessed boxes
  - If content too big → escape/overlap
  - If content too small → wasted space
```

### New: True Bottom-Up

```
Single Recursive Pass (d3-force):

For each cut (innermost first):
  1. Provide GENEROUS virtual box (800x600)
  2. Run d3-force (containment teaches it walls)
  3. Calculate TIGHT bounding box from actual positions
  4. Return tight box to parent (becomes obstacle)

Result: Content determines container size
```

---

## Test Results

### Standalone Tests (`test_bottom_up_engine.py`)

All corpus graphs passed:

**Graph 1: `dau_2006_p112_ligature`**
```
✅ Leaf cut: 98 x 107 (content-determined)
✅ Sheet: 149 x 247 (tight fit)
```

**Graph 2: `mixed_quantifier_complex`**
```
✅ Inner cut: 83 x 98
✅ Outer cut: 205 x 165 (child as obstacle)
✅ Sheet: 245 x 205
```

**Graph 3: `peirce_complex_scope`**
```
✅ Deep nesting working
✅ Innermost: 141 x 145
✅ Middle: 181 x 185
✅ Sheet: 221 x 225
```

### GUI Integration (`src/gui_clean/main_application.py`)

**Status:** Testing in progress

**Command:**
```bash
export KMP_DUPLICATE_LIB_OK=TRUE && \
cd /Users/mjh/Sync/GitHub/Arisbe && \
python src/gui_clean/main_application.py
```

**Expected Improvements:**
- ✅ No more elements escaping their containers
- ✅ No more extreme spacing issues
- ✅ Container sizes fit content perfectly
- ✅ Connected elements stay near each other
- ✅ Stable, predictable layouts

---

## Known Limitations

### Not Yet Implemented

1. **User Position Overrides (deltas)**
   - Parameter accepted but ignored
   - Future: Pinned nodes, custom ligature paths

2. **Ligature Routing**
   - Currently no ligatures in DTO
   - Future: Area-aware A* pathfinding integration

3. **Port Calculation**
   - No geometric port nodes yet
   - Future: Calculate from tight boundaries

### Architecture Decisions

**Generous Virtual Box (800x600)**
- Large enough for any reasonable content
- Allows forces to settle naturally
- Final size comes from tight bounding box

**Small Initial Clustering (30px radius)**
- Prevents extreme starting separations
- Connected elements start near each other
- Forces maintain proximity

**Containment Force Priority**
- Runs EVERY tick (unbreakable rule)
- Zeros velocity on violation
- Link forces work WITHIN boundaries

---

## Rollback Instructions

If issues arise, revert to old engine:

```python
# In src/diagram_controller.py:

# Comment out:
# from bottom_up_d3_engine import BottomUpD3Engine
# self.layout_engine = BottomUpD3Engine()

# Restore:
from definitive_three_pass_engine import DefinitiveThreePassEngine
self.layout_engine = DefinitiveThreePassEngine()
```

---

## Next Steps

### Short Term
1. ✅ Standalone testing (COMPLETE)
2. ✅ GUI integration (COMPLETE)
3. 🔄 GUI validation (IN PROGRESS)
4. ⏳ Load problematic corpus graphs in Organon

### Medium Term
1. Implement ligature routing (A* pathfinding)
2. Add port calculation from boundaries
3. Support user position overrides (deltas)

### Long Term
1. Performance optimization for large graphs
2. Animated transitions between layouts
3. Interactive force parameter tuning

---

## Key Insight

**The custom containment force is a TEACHING TOOL, not a competing force.**

D3-force doesn't know about walls by default. The containment force teaches it this rule by:
1. Running on every tick
2. Forcibly correcting positions outside bounds
3. Zeroing velocity to prevent bouncing

This allows d3's optimization to find the best layout WITHIN the constraints we define, while the final container size is determined by WHERE content actually ends up, not WHERE we guessed it would be.

**Content determines container size. Always.**
