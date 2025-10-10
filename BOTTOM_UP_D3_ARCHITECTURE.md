# Bottom-Up D3-Only Architecture

## The Problem: Flawed Two-Pass Approach

### What Was Wrong

The original `DefinitiveThreePassEngine` had a fundamental architectural flaw:

**Pass 1 (Graphviz)**: Guessed container sizes using heuristics
```python
# From _build_dot - SIZE GUESSING!
if content_count <= 2:
    est_width = content_count * 1.0  # GUESS
    est_height = 0.75                 # GUESS
else:
    rows = math.ceil(math.sqrt(content_count))
    est_width = cols * 0.8            # GUESS
    est_height = rows * 0.6           # GUESS
```

**Pass 2 (d3-force)**: Tried to fit content into guessed boxes
- If content needed MORE space → Elements escaped or overlapped
- If content needed LESS space → Wasted whitespace
- Containment force fought with link forces → Instability

**The Root Cause**: Container size was determined BEFORE knowing content needs.

## The Solution: Pure Bottom-Up D3

### Core Principle

**Content determines container size, not the other way around.**

### How It Works

#### 1. No More Graphviz (No More Guessing)

Remove Pass 1 entirely. All sizing comes from ACTUAL content positions.

#### 2. Recursive Bottom-Up Layout

```
For each cut (starting with innermost):
  1. Layout children first (recursion)
  2. Run d3-force with GENEROUS virtual box
  3. Calculate TIGHT bounding box from actual positions
  4. Return tight box to parent (becomes obstacle)
```

#### 3. Teaching d3-force About Walls

The custom `forceContainment` teaches d3 about boundaries:

```javascript
function forceContainment(bounds, obstacles) {
    // Applied on EVERY tick
    function force(alpha) {
        for each node:
            // RULE 1: Stay inside virtual box
            if (node.x < 0) {
                node.x = 0;
                node.vx = 0;  // Stop bouncing
            }
            
            // RULE 2: Stay outside child obstacles
            if (inside obstacle) {
                eject to nearest edge
                zero velocity toward obstacle
            }
    }
}
```

This creates a "tug of war" at boundaries:
- Link forces pull elements toward walls
- Containment force immediately pushes them back
- Result: Elements cluster near boundaries but never cross them

#### 4. Tight Bounding Box Calculation

AFTER d3 simulation settles, calculate the minimal box that encloses everything:

```python
def _calculate_tight_bounds(content_ids, child_bounds):
    # Find extremes of actual positions
    min_x = min(all content left edges)
    min_y = min(all content top edges)
    max_x = max(all content right edges)
    max_y = max(all content bottom edges)
    
    # Add padding
    return TightBounds(min_x, min_y, max_x - min_x, max_y - min_y)
```

This tight box becomes the FINAL container size.

## Implementation

### New Engine: `bottom_up_d3_engine.py`

**Key Methods**:

1. **`_layout_recursive(cut_id)`**
   - Bottom-up recursion
   - Returns `TightBounds` from actual content

2. **`_layout_cut(content, child_bounds, virtual_width, virtual_height)`**
   - Provides GENEROUS virtual box for d3
   - Calls d3 worker with containment force
   - Calculates TIGHT box from results

3. **`_calculate_tight_bounds(content_ids, child_bounds)`**
   - Finds minimal enclosing box
   - This is the TRUE container size

### D3 Worker: `d3_layout_worker.js`

**Forces**:
1. **forceLink** (0.7 strength) - Keep connected elements together
2. **forceCollide** (1.0 strength) - Prevent all overlaps
3. **forceCenter** (0.05 strength) - Gently nudge toward center
4. **forceContainment** (custom) - **TAUGHT RULE** - enforce walls

## Advantages

### ✅ No More Size Guessing
- Graphviz removed entirely
- Container sizes come from ACTUAL content positions

### ✅ True Bottom-Up
- Children sized before parents
- Parent uses child's tight bounds as obstacles
- Each level determines its own size needs

### ✅ Stable Equilibrium
- No fighting between forces
- Containment is a TAUGHT RULE, not a competing force
- Link forces find optimal positions within walls

### ✅ Perfect Containment
- Elements can never escape (containment force runs every tick)
- Child cuts are solid obstacles (collision prevents overlap)
- Final tight box perfectly encloses content

## Testing

Run the test:
```bash
cd /Users/mjh/Sync/GitHub/Arisbe
python test_bottom_up_engine.py
```

Expected output:
```
Bottom-up recursive layout (d3-force)...
    Laying out c_inner:
      Content: 2 elements
      Children: 0 cuts
      Virtual box: 800x600
      D3 positioned 2 elements
      Tight box: 120x80
    Laying out c_outer:
      Content: 1 elements
      Children: 1 cuts
      Virtual box: 800x600
      D3 positioned 1 elements
      Tight box: 200x150
  ✅ 3 elements positioned
  ✅ 2 containers sized
```

## Next Steps

If testing is successful:
1. Integrate with Organon (replace DefinitiveThreePassEngine)
2. Add ligature routing (A* pathfinding)
3. Add port calculation for cross-boundary connections

## Key Insight

**The custom containment force is NOT a competing force - it's a TEACHING TOOL.**

D3-force doesn't know about walls. We teach it by writing a function that:
- Runs on every tick
- Forcibly corrects positions outside bounds
- Zeros velocity to prevent bouncing

This allows d3's optimization to work WITHIN the constraints we define,
finding the optimal "low-energy" state while respecting unbreakable rules.

The FINAL container size is then calculated from WHERE the content actually
ended up, not WHERE we guessed it would be.

**Content determines container size. Always.**
