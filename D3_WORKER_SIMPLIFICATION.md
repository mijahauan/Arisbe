# D3 Worker Simplification: One Force, One Job

## The Problem: Competing Forces

The previous `d3_layout_worker.js` had **three competing containment mechanisms**:

1. **forceCollide()** on obstacles → trying to push nodes away from child cuts
2. **Custom forceContainment()** ejecting nodes from obstacles → also pushing away
3. **Custom forceContainment()** clamping to bounds → also constraining position

**Result:** Chaotic tug-of-war preventing stable equilibrium.

## The Solution: Radical Simplification

Applied the "**one force, one job**" principle:

### Four Non-Competing Forces

#### 1. **forceLink** - Attraction Only
```javascript
.force('link', d3.forceLink(simLinks)
    .id(d => d.id)
    .distance(25)
    .strength(1.5)
)
```
**Job:** Keep connected elements (ν relationships) together.

#### 2. **forceCollide** - ALL Repulsion
```javascript
.force('collision', d3.forceCollide()
    .radius(d => {
        if (d.type === 'obstacle') return Math.max(d.width, d.height) / 2 + 5;
        if (d.type === 'port') return 3;
        if (d.width && d.height) return Math.max(d.width, d.height) / 2 + 5;
        return d.type === 'vertex' ? 15 : 30;
    })
    .strength(1.0)
    .iterations(3)  // Stronger collision resolution
)
```
**Job:** Prevent ALL overlaps (nodes with nodes, nodes with obstacles).
**Key insight:** Obstacles are just nodes with large radii - forceCollide handles them automatically.

#### 3. **forceCenter** - Prevent Drift
```javascript
.force('center', d3.forceCenter(bounds.width / 2, bounds.height / 2)
    .strength(0.05)  // Very weak
)
```
**Job:** Gently nudge toward center to prevent the entire layout from drifting away.

#### 4. **forceContainment** - Outer Walls ONLY
```javascript
.force('containment', forceContainment(bounds))
```
**Job:** Clamp nodes to outer boundary. Does NOT handle obstacles (forceCollide does that).

```javascript
function forceContainment(bounds) {
    let nodes;
    
    function force(alpha) {
        for (const node of nodes) {
            if (node.fx !== undefined || node.fy !== undefined) continue;
            if (node.type === 'obstacle' || node.type === 'port') continue;
            
            let halfWidth, halfHeight;
            if (node.width && node.height) {
                halfWidth = node.width / 2;
                halfHeight = node.height / 2;
            } else {
                const radius = node.type === 'vertex' ? 15 : 30;
                halfWidth = halfHeight = radius;
            }
            
            // Clamp to bounds
            if (node.x - halfWidth < 0) {
                node.x = halfWidth;
                node.vx = 0;  // Stop bouncing
            } else if (node.x + halfWidth > bounds.width) {
                node.x = bounds.width - halfWidth;
                node.vx = 0;
            }
            
            if (node.y - halfHeight < 0) {
                node.y = halfHeight;
                node.vy = 0;
            } else if (node.y + halfHeight > bounds.height) {
                node.y = bounds.height - halfHeight;
                node.vy = 0;
            }
        }
    }
    
    force.initialize = function(_) { nodes = _; };
    return force;
}
```

**What was removed:** All obstacle ejection logic (60+ lines of complex coordinate math).

## Simple Initial Positioning

**Old approach:** Complex clustering with jitter, clamping, and radius calculations (40+ lines).

**New approach:** Start everything at center, let forces spread naturally (5 lines).

```javascript
// SIMPLE: All nodes start at center
const centerX = bounds.width / 2;
const centerY = bounds.height / 2;

for (let i = 0; i < nodes.length; i++) {
    const node = nodes[i];
    let x = centerX;
    let y = centerY;
    
    // Tiny jitter to break symmetry
    const jitter = 5;
    x += (seededRandom() - 0.5) * jitter;
    y += (seededRandom() - 0.5) * jitter;
    
    simNodes.push({
        id: node.id,
        type: node.type,
        x: x,
        y: y,
        width: node.width,
        height: node.height
    });
}
```

**Why this works:** Collision force will push nodes apart from the center. Link force will keep connected elements close. Simple and predictable.

## Benefits

### ✅ No Force Competition
Each force has a single, well-defined job. No fighting.

### ✅ Stable Equilibrium
Forces can settle into a low-energy state without constant interference.

### ✅ Simpler = Fewer Bugs
- Removed ~100 lines of complex logic
- Removed obstacle ejection code (forceCollide handles it)
- Removed complex initial positioning

### ✅ Predictable Behavior
- Start at center → collision spreads → link attracts → containment bounds
- Clear causal chain

### ✅ Still Deterministic
- Seeded random for jitter
- Sorted iterations in Python
- Same graph → same layout

## What forceCollide Actually Does

**Key insight:** `forceCollide` treats ALL nodes (including obstacles) as circles and prevents overlaps.

When we add obstacles with large radii:
```javascript
if (d.type === 'obstacle') return Math.max(d.width, d.height) / 2 + 5;
```

forceCollide **automatically pushes other nodes away** from these large circles. No custom ejection logic needed!

## The Rectangle Problem

**Acknowledged limitation:** forceCollide uses circles, not rectangles. Using `Math.max(width, height) / 2` as radius means:
- Two rectangles oriented perpendicularly might still overlap slightly at corners
- This is acceptable for our use case (cuts are independent anyway)
- Alternative would be custom rectangle collision (much more complex)

## Testing Results

**Before simplification:**
- ❌ Non-deterministic layouts
- ❌ Elements in wrong areas
- ❌ Chaotic behavior from competing forces

**After simplification:**
- ✅ Deterministic (same graph → same layout)
- ✅ Stable simulation (reaches equilibrium)
- ✅ ~100 lines removed
- ✅ Simpler mental model

## Code Comparison

### Before: ~260 lines with competing forces
- Complex initial positioning (40 lines)
- Three containment mechanisms
- Custom obstacle ejection logic (60 lines)
- Unpredictable interactions

### After: ~160 lines with clean separation
- Simple initial positioning (5 lines)
- Four non-competing forces
- No custom obstacle logic
- Predictable physics

## Next Steps

1. ✅ Test in GUI with simplified forces
2. ⏳ Verify stable layouts for complex nested cuts
3. ⏳ Measure if equilibrium is reached faster
4. ⏳ Consider adjusting force parameters for better aesthetics

## Key Takeaway

**D3-force is a physics engine.** Treat it like one:
- Define clear, non-competing forces
- Let the simulation find equilibrium naturally
- Don't fight the physics with manual corrections (unless absolutely necessary)
- Simple initial state + clear forces = predictable results
