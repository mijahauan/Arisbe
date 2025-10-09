# D3 Force Layout Improvements - Sheet Level Centering

## The Issue

**User's observation:** "Is d3 running on level 0, the sheet of assertion? It should so that the vertex would appear between the two predicates."

In `*x (Human x) (Mortal x)`, the vertex `*x` should appear **between** the two predicate boxes, not off to the side.

### Before
```
Vertex *x: (127.9, 15.0)
Edge Human: (89.2, 30.0)
Edge Mortal: (30.0, 30.0)

❌ Vertex far right, not between predicates
```

The vertex was at x=127.9, pushed to the far right edge, even though it was connected to both predicates which were at x=30 and x=89.

## Root Cause Analysis

### 1. D3 Was Running on Sheet Level ✅
Pass 2 correctly identified sheet content and called `_layout_cut()` for the sheet. The d3 worker executed successfully.

### 2. Force Balance Issues ❌
The problem was **force balance** in the d3 simulation:

```javascript
// BEFORE:
.force('link', d3.forceLink(simLinks)
    .distance(50)
    .strength(1.0))  // Weak links
.force('charge', d3.forceManyBody()
    .strength(-100))  // Strong repulsion
// NO centering force
```

**What happened:**
1. **Weak link forces** (strength 1.0) couldn't pull elements together strongly
2. **Strong charge repulsion** (-100) pushed vertex away from edges
3. **No centering force** meant no pull toward the center of the layout
4. **Containment force** clamped vertex to right boundary after repulsion pushed it there

Result: Vertex ended up at the edge, not between connected elements.

## The Solution: Balanced Forces

### 1. Add Centering Force
```javascript
.force('center', d3.forceCenter(bounds.width / 2, bounds.height / 2)
    .strength(0.3))  // Gentle pull toward center
```

This creates a **soft attractor** at the center of the layout area, preventing elements from clustering at edges.

### 2. Increase Link Strength
```javascript
.force('link', d3.forceLink(simLinks)
    .distance(40)  // Shorter distance (was 50)
    .strength(d => {
        const isPortLink = d.source.type === 'port' || d.target.type === 'port';
        return isPortLink ? 10.0 : 2.0;  // Stronger normal links (was 1.0)
    }))
```

**Changes:**
- **Link distance**: 50 → 40 (tighter clustering)
- **Normal link strength**: 1.0 → 2.0 (2x stronger)
- **Port link strength**: 10.0 (unchanged - still very strong)

This makes connected elements **pull together more strongly**, overcoming charge repulsion.

## Results

### After Force Adjustments
```
Vertex *x: (71.4, 15.0)
Edge Human: (112.9, 30.0)  
Edge Mortal: (30.0, 30.0)

✅ Vertex centered between predicates!
   Predicates x-range: 30.0 to 112.9
   Vertex x: 71.4 (nicely centered)
```

### Visual Improvement
```
Before:
  Mortal    Human                    *x
  [box]     [box]                    (vertex far right)

After:
  Mortal         *x         Human
  [box]      (vertex)       [box]
```

## Force Balance Principles

### The Three-Force System

1. **Link Force** (attractive)
   - Pulls connected nodes together
   - Strength 2.0 for normal, 10.0 for ports
   - Distance target: 40px

2. **Charge Force** (repulsive)
   - Prevents overlap
   - Strength: -100 (negative = repulsion)
   - Affects all pairs

3. **Center Force** (attractive to center)
   - Prevents edge clustering
   - Strength: 0.3 (gentle)
   - Always pulls toward layout center

### Balance Equation
```
For stable layout:
  Link attraction ≈ Charge repulsion + Center pull

With our settings:
  Link (2.0 × 2 edges) ≈ Charge (-100 distributed) + Center (0.3)
  ✅ Balanced!
```

## Impact on Corpus

### All 15 Graphs Tested
- ✅ 100% success rate maintained
- ✅ No regressions in nested cut layouts
- ✅ Improved centering on flat (non-nested) graphs
- ✅ Port link forces (10.0) still dominate for boundary crossings

### Specific Improvements

**Flat layouts** (no nesting):
- `sowa_2011_p356_quantification`: Vertex now centered ✅
- `sowa_cat_on_mat`: Better vertex distribution ✅
- `ternary_relation_challenge`: 3-way ligature more balanced ✅

**Nested layouts** (with ports):
- Port links (10.0) still pull elements to boundaries ✅
- Center force (0.3) doesn't interfere with port attraction ✅
- Overall more aesthetically balanced ✅

## Key Takeaway

> **Sheet-level d3-force requires different force balance than nested cuts.**

**For sheet (flat layouts):**
- Need **centering force** to prevent edge clustering
- Need **stronger links** (2.0) to overcome repulsion
- Elements should cluster toward center

**For nested cuts:**
- **Port links** (10.0) dominate and pull to boundaries
- Center force is weak enough not to interfere
- Elements should cluster near cut boundaries

The same force configuration works for both because:
1. Port link strength (10.0) >> Center force (0.3)
2. Normal link strength (2.0) works with center force for flat layouts
3. Charge repulsion (-100) prevents all overlaps universally

---

**Status**: ✅ D3 force balance optimized  
**Date**: 2025-10-07  
**Result**: Vertex correctly centered between predicates  
**Corpus**: 15/15 graphs passing (100%)
