# D3 Energy Minimization & Graphviz Constraints

## The Question

**"How does d3 reach the 'lowest energy state'? Would some adjustments to the dot output provide more 'wiggle room' for d3 to work with?"**

This is an excellent architectural question about the interaction between Pass 1 (Graphviz) and Pass 2 (d3-force).

---

## Part 1: How D3 Reaches Lowest Energy State

### The Physics Simulation

D3's force-directed layout is a **physical simulation** where nodes are particles with forces acting on them:

```javascript
// 500 iterations of physics simulation
simulation.stop();
for (let i = 0; i < 500; ++i) {
    simulation.tick();  // One step of physics
}
```

Each `tick()`:
1. **Calculate forces** on every node
2. **Update velocities** based on forces
3. **Update positions** based on velocities
4. **Apply damping** (friction) to slow down over time

### Energy Function

The "energy" is the sum of all force potentials:

```
Total Energy = Link Energy + Charge Energy + Centering Energy + ...

Link Energy:   Σ (distance - target_distance)²
Charge Energy: Σ 1/distance²  (repulsion)
Center Energy: Σ (position - center)²
```

**Lowest energy state** = configuration where forces are balanced (equilibrium).

### Convergence Process

```
Iteration 0:   High energy (random positions)
               Large forces → large movements
               
Iteration 100: Medium energy (partially organized)
               Moderate forces → moderate movements
               
Iteration 300: Low energy (nearly converged)
               Small forces → small movements
               
Iteration 500: Minimal energy (equilibrium)
               Tiny forces → tiny adjustments
```

**Key insight**: The simulation naturally finds a **local minimum**, not necessarily the global minimum. Starting positions matter!

---

## Part 2: Current Graphviz Constraints

### What Graphviz Provides

Pass 1 (Graphviz) generates:

1. **Container bounds** (area sizes)
   ```python
   area_bounds = {
       'sheet': Rect(x=0, y=0, width=200, height=150),
       'cut_1': Rect(x=20, y=30, width=160, height=100),
       ...
   }
   ```

2. **Port positions** (fixed points on boundaries)
   ```python
   port_nodes = {
       'port_0': PortNode(position=(100, 30), cut_id='cut_1'),
       ...
   }
   ```

3. **That's it!** Graphviz does NOT pass element positions to d3.

### What D3 Actually Gets

From Python to d3 worker:
```javascript
payload = {
    bounds: { x: 0, y: 0, width: 200, height: 150 },
    nodes: [
        { id: 'v_123', type: 'vertex' },      // NO position
        { id: 'e_456', type: 'edge_label' },  // NO position
    ],
    portNodes: [
        { id: 'port_0', x: 100, y: 30 }       // Fixed position
    ],
    obstacles: [
        { id: 'cut_1', x: 20, y: 30, width: 160, height: 100 }  // Fixed
    ],
    links: [
        { source: 'v_123', target: 'e_456' }
    ]
}
```

### D3's Starting Positions

```javascript
// d3_layout_worker.js lines 50-69
for (const node of nodes) {
    let x, y;
    
    if (node.x !== undefined && node.y !== undefined) {
        // Use provided position (but we don't provide any!)
        x = node.x;
        y = node.y;
    } else {
        // Random initialization around center
        const angle = Math.random() * 2 * Math.PI;
        const radius = Math.random() * Math.min(bounds.width, bounds.height) / 4;
        x = bounds.width / 2 + radius * Math.cos(angle);
        y = bounds.height / 2 + radius * Math.sin(angle);
    }
    
    simNodes.push({ id: node.id, type: node.type, x: x, y: y });
}
```

**Key point**: Elements start in **random positions** near the center. Graphviz element positions are NOT used!

---

## Part 3: The Constraints We Actually Have

### Hard Constraints (Cannot Violate)

1. **Container bounds** (absolute)
   ```javascript
   // FINAL HARD CLAMP after simulation
   node.x = Math.max(radius, Math.min(bounds.width - radius, node.x));
   node.y = Math.max(radius, Math.min(bounds.height - radius, node.y));
   ```

2. **Obstacle exclusion** (absolute)
   ```javascript
   // Custom containment force runs on EVERY tick
   for (const obs of obstacles) {
       if (overlaps(node, obs)) {
           ejectToNearestValidSpace(node, obs, bounds);
       }
   }
   ```

3. **Port positions** (fixed)
   ```javascript
   portNodes.forEach(port => {
       simNodes.push({
           fx: port.x,  // Fixed x
           fy: port.y,  // Fixed y
           type: 'port'
       });
   });
   ```

### Soft Constraints (Forces)

All other forces are **soft** - they guide but don't absolutely constrain:
- Link forces (4.0 or 10.0)
- Charge forces (-50)
- Centering forces (0.3)
- X/Y forces (0.6/0.08 for flat layouts)
- Collision forces (0.7)

---

## Part 4: How Much Wiggle Room Does D3 Have?

### Container Size = Search Space

The container bounds define the **search space** for d3:

```
Flat layout (sowa_cat_on_mat):
  Bounds from Graphviz: 179px × 60px
  D3 search space: 179px × 60px
  
Nested layout (peirce_modus_ponens):
  Innermost cut: 67px × 102px
  D3 search space (for that cut): 67px × 102px
```

**Current situation**: D3 has the **entire container** as wiggle room.

### Port Positions = Anchor Points

Ports are **fixed** from Graphviz:
- Act as attractors (link force 10.0)
- Cannot move during d3 simulation
- Elements cluster near them

**Current situation**: Port positions are determined by Graphviz's macro-layout.

### Container Sizing Strategy

Graphviz determines container sizes using **padding and nested structure**:

```dot
subgraph "cluster_cut_1" {
    margin = 20;  // Padding around content
    style = rounded;
    // Graphviz calculates size based on content + margin
}
```

**Current situation**: Container sizes are **as small as possible** given the nested structure.

---

## Part 5: Would More Wiggle Room Help?

### Option 1: Larger Containers

**Approach**: Increase Graphviz container padding

```python
# In DOT generation
margin = 40  # Was 20
```

**Effect**:
- ✅ More space for d3 to spread elements
- ✅ Potentially better force convergence
- ❌ Larger overall diagrams (more whitespace)
- ❌ Nested cuts get disproportionately large

**Trade-off**: Space vs. Compactness

### Option 2: Initial Positions from Graphviz

**Approach**: Use Graphviz positions as starting points

```javascript
// Instead of random initialization:
x = node.graphvizX || randomX();
y = node.graphvizY || randomY();
```

**Effect**:
- ✅ Better starting configuration (closer to good layout)
- ✅ Faster convergence (fewer iterations needed)
- ✅ More predictable results
- ❌ Might get stuck in local minimum from Graphviz
- ❌ Tight Graphviz layouts might not give d3 room to improve

**Trade-off**: Consistency vs. Exploration

### Option 3: Expand-Then-Shrink

**Approach**: 
1. Graphviz generates spacious layout
2. D3 optimizes within that space
3. Post-process: Shrink containers to actual content bounds

**Effect**:
- ✅ D3 has maximum wiggle room
- ✅ Final output is compact
- ✅ Best of both worlds
- ❌ More complex pipeline
- ❌ Requires additional shrink-wrap pass

**Trade-off**: Complexity vs. Quality

### Option 4: Relaxed Port Positions

**Approach**: Let d3 adjust port positions slightly

```javascript
// Instead of fx/fy (fixed):
simNodes.push({
    id: port.id,
    x: port.x,
    y: port.y,
    // No fx/fy - port can move!
    weight: 100  // Heavy weight keeps it near boundary
});
```

**Effect**:
- ✅ Ports can adjust to element clustering
- ✅ More natural force balance
- ❌ Ports might drift from boundary
- ❌ Ligature routing expects ports on boundary
- ❌ Breaks assumption of Pass 3

**Trade-off**: Flexibility vs. Correctness

---

## Part 6: Current Design Rationale

### Why Random Initialization?

**Advantages**:
1. **Independence**: D3 is not biased by Graphviz layout
2. **Exploration**: Can find configurations Graphviz wouldn't
3. **Simplicity**: No need to pass positions between passes

**Disadvantages**:
1. **Non-determinism**: Different runs can give different results
2. **Slow convergence**: Starting from scratch every time
3. **Local minima**: Might not find global optimum

### Why Tight Containers?

**Advantages**:
1. **Compact output**: No wasted whitespace
2. **Nested clarity**: Clear visual hierarchy
3. **Efficient use of space**: Better for large graphs

**Disadvantages**:
1. **Less wiggle room**: D3 has limited search space
2. **Forced clustering**: Elements might be too tightly packed
3. **Force conflicts**: Containment force fights other forces

---

## Part 7: Recommended Improvements

### Immediate: Graphviz-Seeded Initialization

**Change**: Use Graphviz positions as starting points (but let d3 adjust)

```python
# In definitive_three_pass_engine.py
# After Pass 1, extract element positions from Graphviz SVG
graphviz_positions = self._extract_graphviz_positions()

# Pass to d3
payload['nodes'] = [
    {
        'id': elem_id,
        'type': elem_type,
        'x': graphviz_positions.get(elem_id, {}).get('x'),
        'y': graphviz_positions.get(elem_id, {}).get('y')
    }
    for elem_id, elem_type in ...
]
```

**Benefits**:
- Better starting configuration → faster convergence
- More predictable results → deterministic layouts
- Still allows d3 to improve upon Graphviz

**Implementation complexity**: Medium (need to parse Graphviz SVG)

### Medium-Term: Adaptive Container Sizing

**Change**: Give d3 10-20% extra space, then shrink

```python
# Pass 1: Generate with extra padding
margin = 30  # Generous space

# Pass 2: D3 optimizes within generous space

# Pass 2.5: Shrink containers to actual content bounds
def shrink_wrap_containers(element_positions, cuts):
    for cut_id in cuts:
        elements_in_cut = [pos for elem, pos in element_positions.items()
                          if element_to_cut[elem] == cut_id]
        min_x = min(x for x, y in elements_in_cut) - padding
        max_x = max(x for x, y in elements_in_cut) + padding
        # Update cut bounds
        ...
```

**Benefits**:
- D3 has room to work
- Final output is compact
- Best quality layouts

**Implementation complexity**: High (new pass, coordinate transform)

### Long-Term: Deterministic Seeding

**Change**: Use seed based on graph structure for reproducibility

```javascript
// d3_layout_worker.js
const seed = payload.seed || 12345;
const random = seededRandom(seed);

// Use seeded random for initialization
const angle = random() * 2 * Math.PI;
const radius = random() * Math.min(bounds.width, bounds.height) / 4;
```

**Benefits**:
- Deterministic output (same input → same output)
- Can compare layouts across runs
- Easier testing and debugging

**Implementation complexity**: Low (just change random source)

---

## Part 8: The Current Balance

### What's Working

1. **Independence**: D3 not constrained by Graphviz element layout
2. **Flexibility**: Random start allows exploration of solution space
3. **Simplicity**: Clean separation between passes

### What's Challenging

1. **Non-determinism**: Different runs give different results
2. **Tight spaces**: Nested cuts can be cramped
3. **Force conflicts**: Strong containment vs. other forces

### The Trade-Off

```
More Graphviz Control          More D3 Freedom
(predictable, consistent)      (exploratory, adaptive)
<─────────────┼─────────────>
              ↑
        Current position

Recommended move:
<─────────────┼─────────────>
         ↑
   Use Graphviz positions as seeds
   (best of both worlds)
```

---

## Part 9: Answering The Question

### "How does d3 reach the lowest energy state?"

**Answer**: 500 iterations of physics simulation where forces balance:
- Starts: Random positions (high energy)
- Iterates: Forces move nodes, damping slows them down
- Ends: Forces balanced (local minimum energy)

**Key limitation**: Finds **local** minimum, not global. Starting position matters!

### "Would more wiggle room help?"

**Short answer**: Yes, but with trade-offs.

**Long answer**:

| Approach | Wiggle Room | Compactness | Complexity |
|----------|-------------|-------------|------------|
| **Current** (random init, tight containers) | ⭐⭐ | ⭐⭐⭐⭐ | ⭐ |
| **Graphviz-seeded** (use Graphviz positions) | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| **Expand-shrink** (spacious → optimize → compact) | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Larger containers** (just increase margins) | ⭐⭐⭐⭐ | ⭐⭐ | ⭐ |

**Recommended**: Graphviz-seeded initialization (best balance)

---

## Part 10: Proposed Implementation

### Step 1: Extract Graphviz Positions

```python
# In definitive_three_pass_engine.py, after Graphviz layout

def _extract_graphviz_positions(self, svg_output: str) -> Dict[str, Tuple[float, float]]:
    """Extract element positions from Graphviz SVG output."""
    import xml.etree.ElementTree as ET
    
    positions = {}
    root = ET.fromstring(svg_output)
    
    # Find text elements with IDs (vertices, edges)
    for text in root.findall('.//{http://www.w3.org/2000/svg}text'):
        elem_id = text.get('id')
        if elem_id and elem_id.startswith(('v_', 'e_')):
            x = float(text.get('x', 0))
            y = float(text.get('y', 0))
            positions[elem_id] = (x, y)
    
    return positions
```

### Step 2: Pass to D3

```python
# In _layout_cut()
graphviz_positions = self.graphviz_element_positions  # Stored from Pass 1

payload['nodes'] = []
for elem_id in egi.area[cut_id]:
    if elem_id.startswith(('v_', 'e_')):
        node = {'id': elem_id, 'type': ...}
        
        # Add Graphviz position as hint (if available)
        if elem_id in graphviz_positions:
            gv_x, gv_y = graphviz_positions[elem_id]
            # Transform to cut-local coordinates
            node['x'] = gv_x - bounds.x
            node['y'] = gv_y - bounds.y
        
        payload['nodes'].append(node)
```

### Step 3: Use in D3 Worker

```javascript
// d3_layout_worker.js - ALREADY IMPLEMENTED!
for (const node of nodes) {
    let x, y;
    
    if (node.x !== undefined && node.y !== undefined) {
        // Use provided position (from Graphviz)
        x = node.x;
        y = node.y;
    } else {
        // Fallback: random
        const angle = Math.random() * 2 * Math.PI;
        const radius = Math.random() * Math.min(bounds.width, bounds.height) / 4;
        x = bounds.width / 2 + radius * Math.cos(angle);
        y = bounds.height / 2 + radius * Math.sin(angle);
    }
    
    simNodes.push({...node, x, y});
}
```

**The d3 worker ALREADY supports this!** We just need to extract and pass Graphviz positions.

---

## Conclusion

**Current state**: D3 has plenty of wiggle room (entire container), but starts from random positions.

**Opportunity**: Use Graphviz positions as **warm start** for d3 simulation.

**Expected benefit**: 
- Better convergence (start closer to good solution)
- More predictable results (deterministic from Graphviz)
- Still allows d3 to optimize (forces can move nodes)

**Next step**: Implement Graphviz position extraction and pass to d3 worker.

---

**Status**: Analysis complete  
**Recommendation**: Implement Graphviz-seeded initialization  
**Expected impact**: Better layouts without sacrificing exploration  
**Complexity**: Medium (need SVG parsing)
