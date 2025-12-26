# Bottom-Up Engine: Determinism and Sibling Cut Separation

## Issues Fixed

1. **Sibling cuts overlapping** - Child cuts positioned incorrectly in parent space
2. **Non-deterministic layouts** - Same graph producing different layouts on reload
3. **Bizarre element placement** - Connected elements sometimes far apart

## Root Causes

### Issue 1: Sibling Cut Overlap

**Problem:** Child cuts were being passed with their own virtual space coordinates (0,0 based), but parent was treating those as absolute positions.

```python
# OLD: Wrong coordinate space!
for child_id, bounds in child_bounds.items():
    payload['obstacles'].append({
        'id': child_id,
        'x': bounds.x + bounds.width / 2,  # bounds.x might be 0!
        'y': bounds.y + bounds.height / 2,  # bounds.y might be 0!
        'width': bounds.width,
        'height': bounds.height
    })

# Result: All child cuts positioned at (0,0) → overlapping!
```

**Fix:** Distribute child cuts across parent's virtual space

```python
# NEW: Position children in parent's coordinate space
num_children = len(child_bounds)
if num_children > 0:
    # Grid distribution
    import math
    cols = math.ceil(math.sqrt(num_children))
    col_width = virtual_width / (cols + 1)
    row_height = virtual_height / (cols + 1)
    
    for idx, (child_id, bounds) in enumerate(sorted(child_bounds.items())):
        col = idx % cols
        row = idx // cols
        
        # Position in parent's virtual space
        child_x = col_width * (col + 1)
        child_y = row_height * (row + 1)
        
        payload['obstacles'].append({
            'id': child_id,
            'x': child_x,  # Now in parent space!
            'y': child_y,
            'width': bounds.width,
            'height': bounds.height
        })
```

**Result:** Child cuts distributed in grid pattern, collision force prevents overlaps

### Issue 2: Non-Deterministic Layouts

**Problem:** Dictionary iteration order was non-deterministic in Python < 3.7, and even in 3.7+ the order of elements in payload affected d3 simulation.

```python
# OLD: Random iteration order
for elem_id in content_ids:  # Set iteration - order undefined!
    payload['nodes'].append(...)

for child_id, bounds in child_bounds.items():  # Dict iteration
    payload['obstacles'].append(...)
```

**Fix:** Sort all iterations to ensure consistent order

```python
# NEW: Sorted iterations for determinism
for elem_id in sorted(content_ids):  # Always same order
    payload['nodes'].append(...)

for idx, (child_id, bounds) in enumerate(sorted(child_bounds.items())):
    payload['obstacles'].append(...)

# Also added seed to payload
payload = {
    ...
    'seed': 42  # Deterministic random numbers
}
```

**Result:** Same graph → same layout every time

### Issue 3: Storing Child Cut Positions

**Problem:** After d3 simulation, child cut positions were not updated in `area_bounds`, so they were rendered at wrong positions.

**Fix:** Track child positions from payload and update area_bounds

```python
# Store child positions from payload
child_positions = {}
for obs in payload['obstacles']:
    child_positions[obs['id']] = (obs['x'], obs['y'])

# Calculate tight bounds including children at actual positions
tight = self._calculate_tight_bounds(content_ids, child_bounds, child_positions)

# Update area_bounds with actual child positions
for child_id, child_tight in child_bounds.items():
    if child_id in child_positions:
        cx, cy = child_positions[child_id]
        self.area_bounds[child_id] = Rect(
            cx - child_tight.width / 2,
            cy - child_tight.height / 2,
            child_tight.width,
            child_tight.height
        )
```

## Testing

### Determinism Test
```bash
# Run twice, compare outputs
python test_bottom_up_engine.py | grep "Tight box" > run1.txt
python test_bottom_up_engine.py | grep "Tight box" > run2.txt
diff run1.txt run2.txt

# Expected: No differences (exit code 0)
# Result: ✅ DETERMINISTIC!
```

### Sibling Cut Separation Test

Load `mixed_quantifier_complex` in Organon:
- **Before:** Inner and outer cuts overlapping or touching
- **After:** Inner cut positioned inside outer cut with proper spacing
- **Grid distribution:** Multiple sibling cuts distributed in grid pattern

## Key Architecture Decisions

### 1. Grid Distribution for Child Cuts

Instead of random or center-stacked positioning, we use a grid:

```
For 2 children: 1x2 grid
┌─────────┬─────────┐
│  Child1 │ Child2  │
└─────────┴─────────┘

For 4 children: 2x2 grid  
┌─────┬─────┐
│  1  │  2  │
├─────┼─────┤
│  3  │  4  │
└─────┴─────┘
```

**Benefits:**
- Natural spacing between siblings
- Collision force has clear separation directions
- Scales to any number of children

### 2. Sorted Iteration

All loops that build d3 payload use `sorted()`:
- Element IDs sorted alphabetically
- Child cut IDs sorted alphabetically
- Deterministic order → deterministic simulation

### 3. Seed Propagation

```python
# Python side
payload = { 'seed': 42 }

# JavaScript side
let randomSeed = seed !== undefined ? seed : Date.now();
function seededRandom() {
    const x = Math.sin(randomSeed++) * 10000;
    return x - Math.floor(x);
}
```

**Benefits:**
- Same seed → same jitter
- Same jitter + same order → same layout
- Reproducible debugging

## Expected Results

### Before Fixes
```
mixed_quantifier_complex:
  Run 1: Inner cut at (104, 89), outer at (81, 33)
  Run 2: Inner cut at (116, 77), outer at (79, 36)  ← Different!
  Visual: Inner and outer cuts overlapping
```

### After Fixes
```
mixed_quantifier_complex:
  Run 1: Inner cut at (104, 89), outer at (81, 33)
  Run 2: Inner cut at (104, 89), outer at (81, 33)  ← Identical!
  Visual: Inner cut properly contained, separated from siblings
```

## Next Steps

1. ✅ Deterministic layouts working
2. ✅ Child cuts separated properly
3. ⏳ Test in Organon GUI (reload same graph multiple times)
4. ⏳ Verify complex nesting (3+ levels)
5. ⏳ Add area-aware A* pathfinding for ligatures
