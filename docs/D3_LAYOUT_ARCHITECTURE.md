# D3.js Force Layout with Hard Containment

**Date**: 2025-10-05  
**Status**: Implementing

## Two-Phase Optimization

### Phase 1: Hard Containment (Pre-computation)
**Problem**: Establish feasible space that respects EGI formal logic

**Solution**: Bottom-up size calculation + top-down positioning
1. Calculate area sizes recursively (leaves to root)
   - Leaf areas: Based on content count
   - Parent areas: `size = children + own_content + margins`
2. Position areas hierarchically (root to leaves)
   - Sheet at origin
   - Child cuts positioned inside parents with margins
   - **Guarantee**: Every area has sufficient space for its content

**Output**: Area bounds dictionary - the "hard walls" that cannot be crossed

### Phase 2: Optimal Positioning (D3 Force Simulation)
**Problem**: Minimize ligature lengths while respecting containment

**Solution**: D3.js force simulation with custom constraint forces

**Forces Applied**:
1. **Link Force** (soft): Attracts connected elements (ligatures)
   - `distance = 30`, `strength = 0.3`
   - Pulls vertex and edge labels together

2. **Charge Force** (soft): Repulsion between elements
   - `strength = -100`, `distanceMax = 100`
   - Prevents overlap and clustering

3. **Collision Force** (soft): Prevents overlap
   - `radius = element.radius + 5`
   - Maintains minimum spacing

4. **Containment Force** (HARD): Clips elements to parent area
   - **NOT a soft force** - hard position clipping
   - `if (x < area.x + padding) { x = area.x + padding; vx = 0; }`
   - Kills velocity at boundary
   - Padding = 15px from edges

5. **Exclusion Force** (HARD): Pushes elements out of child cuts
   - Hard repositioning when element enters exclusion zone
   - Margin = 15px around child cuts
   - Moves to nearest safe position and kills velocity

**Key Insight**: Hard constraints are implemented as **position clipping**, not soft forces. This guarantees they can never be violated, no matter how strong the link forces are.

## Why This Works

### Containment is Inviolable
- Hard clipping happens AFTER all soft forces are applied
- Element positions are directly overwritten if they violate constraints
- Velocity is killed at boundaries to prevent oscillation
- **Cannot fail** - it's geometric clipping, not force equilibrium

### Optimal Positioning Within Constraints
- Link forces pull elements together (minimize ligature length)
- Charge/collision forces prevent overlap (readability)
- Elements can move freely within their area to find optimal layout
- Converges to local minimum of total edge length

### Exclusive Containment
- Sheet elements must stay OUT of child cuts
- Exclusion force creates "keep out" zones around cuts
- Hard push to nearest safe position when violated
- Maintains visual and logical separation

## Implementation

### Input Format (Python → JSON)
```json
{
  "nodes": [
    {
      "id": "v_12345",
      "type": "vertex",
      "area_id": "sheet_abc",
      "x": 50, 
      "y": 50
    },
    {
      "id": "e_67890",
      "type": "edge_label",
      "label": "Person",
      "area_id": "c_def123",
      "x": 100,
      "y": 100
    }
  ],
  "links": [
    {
      "source": "e_67890",
      "target": "v_12345"
    }
  ],
  "areas": {
    "sheet_abc": {"x": 0, "y": 0, "width": 300, "height": 200},
    "c_def123": {"x": 20, "y": 20, "width": 150, "height": 120}
  },
  "hierarchy": {
    "sheet_abc": {"children": ["c_def123"]},
    "c_def123": {"children": []}
  },
  "iterations": 300
}
```

### Output Format (JSON → Python)
```json
{
  "nodes": [
    {
      "id": "v_12345",
      "x": 75.3,
      "y": 62.8,
      "area_id": "sheet_abc"
    }
  ],
  "areas": { /* unchanged from input */ }
}
```

### Python Bridge
```python
d3_engine = D3LayoutEngine()
global_positions, area_bounds = d3_engine.generate_layout(
    egi, hierarchy, area_bounds, iterations=300
)
```

### Node.js Script
```bash
node src/d3_layout_bridge.js input.json > output.json
```

## Advantages Over Pure Python

1. **Mature Force Simulation**: D3's force engine is battle-tested with 10+ years of development
2. **Better Convergence**: Sophisticated velocity decay and alpha cooling
3. **Custom Forces**: Easy to add domain-specific constraints
4. **Performance**: Optimized C++ bindings (via Node.js V8)
5. **Community**: Extensive documentation and examples

## Installation

**Requirements**:
- Node.js (v14+)
- npm package: `d3-force`

**Setup**:
```bash
npm install
```

This installs `d3-force` as specified in `package.json`.

## Fallback Behavior

If Node.js is not available:
- Python implementation (`ConstrainedForceLayout`) is used as fallback
- Same constraints (containment + exclusion) implemented in Python
- Slightly less sophisticated force simulation
- Still produces valid layouts

## Comparison with Graphviz

| Aspect | Graphviz | D3 Force Layout |
|--------|----------|-----------------|
| **Containment** | Not guaranteed | ✅ Hard constraint |
| **Custom forces** | No | ✅ Yes (containment, exclusion) |
| **Ligature optimization** | No | ✅ Link forces |
| **Area awareness** | Clusters only | ✅ Full hierarchy |
| **Exclusive containment** | No | ✅ Exclusion zones |
| **Control** | Black box | ✅ Full transparency |

## Next Steps

1. ✅ Implement D3 bridge script
2. ✅ Add hard containment force
3. ✅ Add hard exclusion force  
4. **TODO**: Test on corpus
5. **TODO**: Fix ligature pathfinding (A* issues)
6. **TODO**: Tune force parameters for aesthetics
7. **TODO**: Add deterministic seeding for reproducibility

## Known Limitations

1. **Ligature routing**: Still needs area-aware A* pathfinder fix
2. **Determinism**: Random initialization - need to add seeding
3. **Aesthetics**: May need parameter tuning per graph type
4. **Performance**: Node.js subprocess overhead (~50-100ms)

## References

- D3 Force Documentation: https://github.com/d3/d3-force
- Force Simulation Guide: https://observablehq.com/@d3/force-directed-graph
- Custom Forces: https://observablehq.com/@d3/custom-forces
