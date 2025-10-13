# Bottom-Up Engine: Excessive Spreading Fixes

## Issues Identified from Screenshots

1. **Exorbitant spreading**: Elements scattered across huge distances
2. **Cuts not properly contained**: Nested cuts with enormous empty space
3. **Cut sizing doesn't match content**: Huge containers for tiny content
4. **Sibling cuts not separated**: Overlapping or touching cuts

## Root Cause Analysis

### Problem 1: Virtual Box Too Large (800x600)
```python
# OLD: Fixed huge virtual box for all layouts
virtual_width = 800
virtual_height = 600

# Result: Elements spread across entire 800x600 space
# Even with link forces, collision force pushed them apart into this huge area
```

### Problem 2: Weak Link Forces
```javascript
// OLD: Link force not strong enough to counter spreading
.force('link', d3.forceLink(simLinks)
    .distance(30)
    .strength(0.7)  // Too weak!
)
```

### Problem 3: Large Initial Clustering
```javascript
// OLD: Elements started 30px apart
const radius = 30;  // Too spread out from the start
const jitter = 30;  // Added more spreading
```

## Solutions Implemented

### 1. Adaptive Virtual Box Sizing

**Strategy:** Size virtual box based on actual content needs

```python
# ADAPTIVE virtual box based on content
import math
total_elements = len(content_ids) + len(child_cut_ids)

# Calculate child cut total area
child_area = sum(b.width * b.height for b in child_bounds.values())

# Estimate content area (rough square packing)
if total_elements <= 2:
    virtual_width = 200   # Small box for few elements
    virtual_height = 150
elif total_elements <= 5:
    virtual_width = 300
    virtual_height = 250  
else:
    # Scale based on element count
    rows = math.ceil(math.sqrt(total_elements))
    virtual_width = min(600, rows * 80)
    virtual_height = min(500, rows * 70)

# Add space for child cuts
if child_area > 0:
    virtual_width = max(virtual_width, int(math.sqrt(child_area) * 1.5))
    virtual_height = max(virtual_height, int(math.sqrt(child_area) * 1.5))
```

**Results:**
- 2 elements: 200x150 box (was 800x600)
- 5 elements: 300x250 box (was 800x600)
- Cuts properly sized to content

### 2. Stronger Link Forces

**Strategy:** Increase attraction between connected elements

```javascript
// NEW: Much stronger link forces
.force('link', d3.forceLink(simLinks)
    .id(d => d.id)
    .distance(25)      // Even closer (was 30)
    .strength(1.5)     // MUCH stronger (was 0.7)
)
```

**Effect:** Connected elements stay tightly clustered even with collision force

### 3. Tighter Initial Clustering

**Strategy:** Start elements very close together, let forces expand naturally

```javascript
// NEW: Very tight initial clustering
const radius = 10;  // Much tighter (was 30)

// Smaller jitter to prevent over-spreading  
const jitter = 15;  // Reduced (was 30)
```

**Effect:** Elements start packed, collision force separates them minimally

### 4. Slightly Stronger Centering

```javascript
// NEW: Prevent drift to edges
.force('center', d3.forceCenter(bounds.width / 2, bounds.height / 2)
    .strength(0.1)  // Increased from 0.05
)
```

## Expected Improvements

### Before (800x600 virtual box, weak forces)
```
dau_2006_p112_ligature:
  - Elements spread across 600+ pixels
  - Cut in corner, ligatures stretched diagonally
  - Sheet: 651x472 (mostly empty space)

dau_theorem_proving:
  - Nested cuts with huge empty areas
  - Elements scattered wildly
  
mixed_quantifier:
  - Inner cut tiny, outer cut enormous
  - Wasted whitespace everywhere
```

### After (adaptive box, strong forces)
```
dau_2006_p112_ligature:
  - Virtual box: 200x150 (adaptive)
  - Tight box: 112x70 (content-fit)
  - Sheet: 182x173 (proper sizing)
  
dau_theorem_proving:
  - Virtual box: 300x250 (based on content)
  - Elements clustered properly
  - Cuts sized to actual content

mixed_quantifier:
  - Inner cut: properly contained
  - Outer cut: appropriate padding
  - No excessive whitespace
```

## Testing Commands

### Standalone Test
```bash
python test_bottom_up_engine.py
```

Expected output:
```
Laying out c_4c90e760:
  Virtual box: 200x150  ← Adaptive sizing!
  Tight box: (44, 40) 112x70
  
Laying out sheet_708e75e7:
  Virtual box: 300x250  ← Based on content + child!
  Tight box: (24, 20) 182x173
```

### GUI Test
```bash
export KMP_DUPLICATE_LIB_OK=TRUE && python src/gui_clean/main_application.py
```

Load problematic graphs and verify:
- ✅ No excessive spreading
- ✅ Cuts properly sized
- ✅ Connected elements stay together
- ✅ Appropriate padding around content

## Key Parameters Summary

| Parameter | Old Value | New Value | Purpose |
|-----------|-----------|-----------|---------|
| Virtual box | 800x600 | Adaptive (200-600) | Match content needs |
| Link distance | 30px | 25px | Tighter clustering |
| Link strength | 0.7 | 1.5 | Stronger attraction |
| Initial radius | 30px | 10px | Start tight |
| Jitter | 30px | 15px | Less random spread |
| Center strength | 0.05 | 0.1 | Prevent drift |

## Architecture Note

The key insight: **Don't fight the forces, configure them properly from the start**

- Small virtual box → Less room to spread
- Strong link force → Elements stay close
- Tight initial clustering → Start compact, expand minimally
- Collision force → Separates only as needed

This creates **compact, well-proportioned layouts** without post-processing or translation hacks.
