# Graphviz Spacing Constraints & D3 Available Space

## The Insight

**User's observation**: "If two cuts are close together, the space there may be effectively unavailable to d3. If the dot parameters were relaxed, then positioning a vertex or predicate between them would be available."

This is a **geometric constraint problem** distinct from the initialization/energy minimization issue.

---

## The Problem Illustrated

### Current Situation (Tight Spacing)

```
Graphviz layout with margin=20:
┌─────────┐  ┌─────────┐
│  Cut 1  │  │  Cut 2  │   ← Only 20-40px between cuts
│         │  │         │
└─────────┘  └─────────┘
      ↓   gap  ↓
      [===]     ← Too narrow for d3 to place elements
```

**D3's perspective**:
```javascript
obstacles = [
    {x: 0, y: 0, width: 100, height: 80},    // Cut 1
    {x: 120, y: 0, width: 100, height: 80}   // Cut 2
];

// Gap between cuts: 120 - 100 = 20px
// Element width: ~25-40px (predicate) or 12px (vertex)
// Result: Predicate CANNOT fit in gap!
```

### With Relaxed Spacing

```
Graphviz layout with margin=40:
┌─────────┐         ┌─────────┐
│  Cut 1  │         │  Cut 2  │   ← 40-80px between cuts
│         │         │         │
└─────────┘         └─────────┘
      ↓    gap     ↓
      [========]    ← Room for d3 to place elements
```

**D3's perspective**:
```javascript
obstacles = [
    {x: 0, y: 0, width: 100, height: 80},    // Cut 1
    {x: 180, y: 0, width: 100, height: 80}   // Cut 2
];

// Gap between cuts: 180 - 100 = 80px
// Element width: ~40px (predicate)
// Result: Predicate CAN fit in gap! ✅
```

---

## Current Graphviz Parameters

### DOT Generation Code

```python
# definitive_three_pass_engine.py, line 218
lines.append(f'{indent}  margin={int(self.style.cut_padding)};')
```

### Style Specification

```json
// styles/default.json
"layout": {
    "cut_padding": 20.0,
    "sibling_shift": [40.0, 30.0],
    ...
}
```

**Current margin**: **20 pixels**

### What This Controls

In Graphviz DOT format:
```dot
subgraph "cluster_cut_1" {
    margin = 20;  // Space around content inside the cut
    style = rounded;
    // ... content ...
}
```

**Effect**:
1. **Internal padding**: 20px of space inside the cut boundary
2. **Sibling spacing**: Graphviz uses margin to determine spacing between sibling clusters
3. **Minimum gap**: Sibling cuts will be at least ~20-40px apart (Graphviz adds its own spacing)

---

## How Constraints Propagate to D3

### Pass 1: Graphviz Determines Obstacle Positions

```python
# After Graphviz layout
area_bounds = {
    'cut_1': Rect(x=10, y=10, width=100, height=80),
    'cut_2': Rect(x=130, y=10, width=100, height=80),
                 ↑ Gap = 130 - 110 = 20px
}
```

### Pass 2: D3 Receives Fixed Obstacles

```javascript
// In d3_layout_worker.js
obstacles = [
    {id: 'cut_1', x: 10, y: 10, width: 100, height: 80},
    {id: 'cut_2', x: 130, y: 10, width: 100, height: 80}
];

// D3 containment force: ABSOLUTE prohibition
for (node of movableNodes) {
    for (obs of obstacles) {
        if (overlaps(node, obs)) {
            // EJECT! Cannot be inside obstacle
            ejectToValidSpace(node, obs, bounds);
        }
    }
}
```

**Critical point**: The gap size is **FIXED** by Graphviz. D3 cannot change it.

### Element Sizes vs. Gap Sizes

| Element Type | Width | Current Gap | Can Fit? |
|--------------|-------|-------------|----------|
| Vertex | 12px radius = 24px | 20-40px | ✅ Yes |
| Short predicate (2 chars) | ~25px | 20-40px | ⚠️ Tight |
| Medium predicate (5 chars) | ~40px | 20-40px | ❌ No |
| Long predicate (8+ chars) | 60px+ | 20-40px | ❌ No |

**Verdict**: With current spacing (margin=20), predicates often **cannot** fit between sibling cuts.

---

## Impact on Specific Layouts

### Example 1: Sibling Cuts with Shared Variable

```
EGIF: *x (P x) ~[ (Q x) ]

Layout with margin=20:
┌────────┐  ┌────────┐
│ sheet  │  │        │
│   P    │  │   Q    │
│        │  │  cut   │
│  *x    │  └────────┘
└────────┘
     ↑
  Vertex forced to LEFT of cut
  (not enough room between P and cut boundary)
```

```
Layout with margin=40:
┌────────┐       ┌────────┐
│ sheet  │       │        │
│   P    │  *x   │   Q    │
│        │   ↑   │  cut   │
│        │ Fits! └────────┘
└────────┘
```

### Example 2: Roberts 1973 Disjunction

```
EGIF: *x ~[ (P x) ] ~[ (Q x) ]

With tight spacing (margin=20):
┌──────┐┌──────┐  ← Cuts close together
│  P   ││  Q   │
│ cut1 ││ cut2 │
└──────┘└──────┘
    *x            ← Forced outside or far away

With relaxed spacing (margin=40):
┌──────┐   ┌──────┐  ← Cuts further apart
│  P   │   │  Q   │
│ cut1 │ *x│ cut2 │  ← Fits naturally in gap
└──────┘   └──────┘
```

---

## Proposed Adjustments

### Option 1: Increase Base Margin (Conservative)

```python
# Increase cut_padding from 20 to 30
"layout": {
    "cut_padding": 30.0,  // Was 20.0
    ...
}
```

**Effect**:
- Gap between sibling cuts: ~30-60px (50% larger)
- Can fit short-to-medium predicates
- ~50% increase in diagram size

**Pros**: Simple, safe, moderate improvement  
**Cons**: Larger diagrams, may still be tight for long predicates

---

### Option 2: Increase Margin Substantially (Aggressive)

```python
"layout": {
    "cut_padding": 50.0,  // Was 20.0
    ...
}
```

**Effect**:
- Gap between sibling cuts: ~50-100px (150% larger)
- Can fit even long predicates comfortably
- ~150% increase in diagram size

**Pros**: Maximum wiggle room for d3  
**Cons**: Much larger diagrams, excessive whitespace

---

### Option 3: Adaptive Margin Based on Content (Smart)

```python
def calculate_adaptive_margin(cut_id, egi):
    """Calculate margin based on content complexity."""
    content = egi.area.get(cut_id, [])
    
    # Base margin
    base_margin = 20
    
    # Increase if many sibling cuts (needs gap space)
    siblings = get_sibling_cuts(cut_id, egi)
    if len(siblings) > 1:
        base_margin += 15  # Extra space for elements between siblings
    
    # Increase if parent has many elements (crowded)
    parent_content = get_parent_content_count(cut_id, egi)
    if parent_content > 5:
        base_margin += 10
    
    return base_margin
```

**Effect**:
- Simple cuts: margin=20 (compact)
- Sibling cuts: margin=35 (more gap space)
- Complex layouts: margin=45 (maximum flexibility)

**Pros**: Optimizes space usage, addresses specific problem cases  
**Cons**: More complex implementation

---

### Option 4: Two-Pass Margin Adjustment (Experimental)

```python
# Pass 1a: Generate with generous margins
margin_pass1 = 50

# Pass 1b: After Graphviz, analyze actual element positions

# Pass 1c: Regenerate with adjusted margins
# - If elements ended up far from boundaries: reduce margins
# - If elements crowded near boundaries: keep generous margins
```

**Pros**: Optimal balance between space and compactness  
**Cons**: Complex, requires multiple Graphviz runs

---

## Recommendation: Option 1 + Option 3 Hybrid

### Immediate (Option 1)

Increase base margin moderately:
```json
"layout": {
    "cut_padding": 30.0,  // Increase from 20.0
    ...
}
```

**Justification**:
- 50% more gap space
- Allows short-medium predicates between cuts
- Modest size increase
- **Quick win with minimal risk**

### Future Enhancement (Option 3)

Implement adaptive margins:
```python
def get_cut_margin(cut_id, egi, hierarchy):
    base = 30  # New base
    
    # Check for sibling cuts
    parent = hierarchy[cut_id]['parent']
    if parent:
        siblings = hierarchy[parent]['children']
        if len(siblings) > 1:
            # Multiple siblings → need gap space
            return base + 20  # Total: 50
    
    return base  # Default: 30
```

**Benefits**:
- Compact for simple layouts
- Generous for sibling cut layouts
- Optimal space usage

---

## Testing Strategy

### 1. Baseline Test

Run corpus with current margin (20):
```bash
python tools/test_definitive_corpus.py
```

Save results as baseline.

### 2. Test with margin=30

Update `styles/default.json`:
```json
"cut_padding": 30.0
```

Run corpus again:
```bash
python tools/test_definitive_corpus.py
```

Compare:
- Layout sizes (expect ~50% increase)
- Visual quality (expect better element distribution)
- Success rate (expect maintained 100%)

### 3. Test with margin=40

```json
"cut_padding": 40.0
```

Compare:
- Layout sizes (expect ~100% increase)
- Visual quality (expect maximum flexibility)
- Success rate (expect maintained 100%)

### 4. Measure Gap Utilization

For each test, measure:
```python
def analyze_gap_usage(layout_dto, area_bounds):
    """Check if elements actually use the gaps."""
    gaps = find_gaps_between_obstacles(area_bounds)
    elements_in_gaps = [
        elem for elem in layout_dto.vertices + layout_dto.edges
        if is_in_gap(elem.position, gaps)
    ]
    
    print(f"Gaps found: {len(gaps)}")
    print(f"Elements utilizing gaps: {len(elements_in_gaps)}")
    print(f"Gap utilization: {len(elements_in_gaps) / len(gaps) * 100:.1f}%")
```

**Goal**: Find minimum margin that achieves good gap utilization (>50%).

---

## Expected Results

### Margin = 20 (Current)

```
Gap sizes: 20-40px
Predicate fit rate: ~30%
Vertex fit rate: ~80%
Diagram size: 100% (baseline)
Gap utilization: ~20%
```

### Margin = 30 (Recommended)

```
Gap sizes: 30-60px
Predicate fit rate: ~60%
Vertex fit rate: ~95%
Diagram size: ~150%
Gap utilization: ~50%
```

### Margin = 40 (Generous)

```
Gap sizes: 40-80px
Predicate fit rate: ~90%
Vertex fit rate: ~100%
Diagram size: ~200%
Gap utilization: ~70%
```

### Margin = 50 (Maximum)

```
Gap sizes: 50-100px
Predicate fit rate: ~100%
Vertex fit rate: ~100%
Diagram size: ~250%
Gap utilization: ~80%
```

---

## Implementation Plan

### Phase 1: Immediate (Simple Increase)

1. Update `styles/default.json`:
   ```json
   "cut_padding": 30.0
   ```

2. Test on corpus:
   ```bash
   python tools/test_definitive_corpus.py
   ```

3. Visually inspect:
   - Sibling cut layouts
   - Element distribution
   - Gap utilization

**Expected time**: 30 minutes  
**Expected benefit**: 50% more wiggle room

---

### Phase 2: Short-Term (Adaptive Margins)

1. Add `get_adaptive_margin()` method to `DefinitiveThreePassEngine`

2. Modify DOT generation to use adaptive margins:
   ```python
   margin = self._get_adaptive_margin(child_cut_id, egi, hierarchy)
   lines.append(f'{indent}  margin={margin};')
   ```

3. Test on corpus and fine-tune thresholds

**Expected time**: 2-3 hours  
**Expected benefit**: Optimal space usage per layout

---

### Phase 3: Future (Smart Analysis)

1. Add gap analysis tool:
   ```python
   def analyze_layout_quality(dto, area_bounds):
       gaps = find_gaps(area_bounds)
       utilization = measure_gap_utilization(dto, gaps)
       crowding = measure_element_crowding(dto)
       return LayoutQualityReport(utilization, crowding)
   ```

2. Use analysis to auto-tune margins per-graph

3. Learn optimal parameters from user feedback

**Expected time**: 1 week  
**Expected benefit**: Machine-learned optimal spacing

---

## Key Insights

### 1. Fixed Obstacles = Fixed Constraints

Once Graphviz runs, obstacle positions are **fixed**. D3 cannot move cuts, only place elements around them.

**Implication**: Graphviz spacing DIRECTLY controls d3's available space.

### 2. Gap Size Matters for Element Type

- **Vertices** (24px): Fit in current gaps ✅
- **Short predicates** (25-40px): Tight fit ⚠️
- **Long predicates** (60px+): Don't fit ❌

**Implication**: Margin should be ≥40px for reliable predicate placement.

### 3. Trade-Off: Space vs. Compactness

More margin = more wiggle room = larger diagrams

**Sweet spot**: margin=30-40 (enough room, not excessive)

### 4. Adaptive is Better Than Fixed

Different layouts have different needs:
- Simple flat layouts: Small margin OK
- Sibling cut layouts: Large margin needed

**Implication**: Adaptive margins optimize space usage.

---

## Answering The Question

> "If the dot parameters were relaxed, then positioning a vertex or predicate between them would be available."

**Answer**: **Absolutely correct!**

**Current constraint**:
- `margin=20` → gaps of 20-40px
- Predicates (~40px) often don't fit

**With relaxed parameters**:
- `margin=30` → gaps of 30-60px
- Most predicates fit ✅

**With generous parameters**:
- `margin=40-50` → gaps of 40-100px
- All elements fit comfortably ✅

**Recommendation**: Start with `margin=30` (50% increase), test, then adjust based on results.

---

**Status**: Analysis complete  
**Recommendation**: Increase `cut_padding` from 20 to 30-40  
**Expected impact**: 50-100% more gap space for element placement  
**Trade-off**: ~50-100% larger diagrams  
**Next step**: Test with `margin=30` on full corpus
