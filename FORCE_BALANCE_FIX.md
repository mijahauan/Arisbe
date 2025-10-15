# d3-force Link Strength Balance Fix

**Date**: 2025-01-10  
**Issue**: Connected elements (like `*x` and `Professor`) appearing on opposite sides of their area  
**Root Cause**: Port link forces (50.0) overwhelming normal link forces (4.0)

---

## Problem Identified

In the professor/student graph, you observed:
- `*x` (generic vertex) and `Professor` (edge label) are **connected** via `(Professor x)`
- They should be **near each other** 
- Instead, they appeared on **opposite sides** of the cut

### Root Cause Analysis

The d3-force link strengths were severely imbalanced:

```javascript
// BEFORE (Broken)
.strength(d => {
    const isPortLink = d.source.type === 'port' || d.target.type === 'port';
    if (isPortLink) {
        return 50.0;  // OVERWHELMINGLY strong
    }
    return 4.0;  // Weak
})
```

**Imbalance**: 50.0 ÷ 4.0 = **12.5:1 ratio**

### What Went Wrong

1. When `*x` has a port connection (strength 50.0)
2. And `Professor` has a port connection (strength 50.0)  
3. But they're connected to each other (strength 4.0)
4. The port forces **dominate** the normal connection
5. Result: They get pulled to **opposite** sides

---

## Solution Implemented

### New Force Balance

```javascript
// AFTER (Fixed)
.strength(d => {
    const isPortLink = d.source.type === 'port' || d.target.type === 'port';
    if (isPortLink) {
        return 8.0;  // Strong but not overwhelming
    }
    return 6.0;  // Increased to be significant
})
```

**New Balance**: 8.0 ÷ 6.0 = **1.33:1 ratio**

### Rationale

1. **Port links (8.0)**: Still strong enough to pull elements toward boundaries
2. **Normal links (6.0)**: Now strong enough to keep connected elements together
3. **Balance**: Port forces no longer completely dominate
4. **Result**: Connected elements stay near each other while respecting ports

---

## Expected Improvements

### What You Should See in Organon

**Before** (Broken):
```
Cut boundary
├─ *x (vertex) ────────┐
│                      │ (Professor x) - weak link (4.0)
│                      │
│  Professor (edge) ◄──┘
│         ▲
│         │ Port link (50.0) - overwhelming
│         │
└─ Port on boundary
```

**After** (Fixed):
```
Cut boundary
├─ *x (vertex) ──┐
│               │ (Professor x) - stronger link (6.0)
│  Professor ◄──┘  <- NOW CLOSE TOGETHER
│      │
│      │ Port link (8.0) - still strong but balanced
│      │
└─ Port on boundary
```

### Specific Graphs to Test

1. **Sowa Professor/Student Graph**:
   - `*x` and `Professor` should be **close together**
   - `*y`, `*z` and their predicates should cluster
   - Port connections still work but don't separate connected elements

2. **Peirce Complex Scope**:
   - `*x`, `*y`, `*z` and `Relation` should form a tight cluster
   - Nested cuts still respect boundaries
   - Better overall spacing

3. **Any Graph with Spanning Ligatures**:
   - Elements connected within same area stay together
   - Port connections pull to boundaries without separating clusters
   - More natural, readable layouts

---

## Technical Details

### Force Parameters After All Fixes

| Force | Configuration | Purpose |
|-------|--------------|---------|
| **Link (Port)** | 8.0 strength, 5px distance | Pull to boundaries (strong but balanced) |
| **Link (Normal)** | 6.0 strength, 30-50px distance | Keep connections together |
| **Charge** | -50 repulsion | Prevent overlap |
| **Collision** | Node dimensions + 5px | Spatial/logical correspondence |
| **Center X/Y** | Adaptive (0-0.6) | Prevent drift |

### Why This Works

1. **Relative Strength**: 8.0 vs 6.0 means port links are only 33% stronger
2. **Cooperation**: Forces work together instead of fighting
3. **Topology Respected**: Normal links preserve graph structure
4. **Ports Still Work**: 8.0 is strong enough for boundary attraction
5. **Natural Clustering**: Connected elements naturally group

---

## Testing Checklist

When you load graphs in Organon, verify:

- [ ] **Connected elements stay together** (main fix)
- [ ] **Port connections still work** (elements reach boundaries)
- [ ] **No excessive separation** (clusters are compact)
- [ ] **Readable layouts** (clean spacing and organization)
- [ ] **Nested cuts render correctly** (bottom-up layout works)
- [ ] **Ligatures route cleanly** (A* pathfinding works)

---

## Files Modified

1. **`src/d3_layout_worker.js`**:
   - Line 183: Port link strength: 50.0 → 8.0
   - Line 187: Normal link strength: 4.0 → 6.0
   - Added comments explaining the balance

---

## Integration with Phases 1-4

This force balance fix **complements** the architectural refactoring:

- **Phase 1**: d3-force starts from clean slate ✅
- **Phase 2**: Bottom-up layout provides correct hierarchy ✅  
- **Phase 3**: Geometric ports calculate boundaries ✅
- **Phase 4**: A* pathfinding routes ligatures ✅
- **Force Balance**: d3-force **discovers good positions** ✅

All five components work together for optimal layouts.

---

## Validation

**Test Before Committing**:
1. Launch Organon: `KMP_DUPLICATE_LIB_OK=TRUE python src/gui_clean/main_application.py`
2. Load graphs from tomos browser
3. Verify `*x` and `Professor` are close together
4. Check other graphs for quality
5. If satisfied, commit all changes

---

**Status**: Ready for testing and validation in Organon ✅
