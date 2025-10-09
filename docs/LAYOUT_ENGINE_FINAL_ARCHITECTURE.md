# Layout Engine Final Architecture

**Date**: 2025-10-05  
**Status**: Production Ready

## Production Architecture

### Three-Tier Fallback System

```
1. D3 Force Layout (Primary)
   ↓ Node.js unavailable
2. Tulip Hierarchical (Fallback)  
   ↓ tulip-python unavailable
3. Python Force Sim (Emergency)
```

## Component Overview

### 1. DefinitiveEGILayoutEngine (Orchestrator)

**File**: `src/definitive_egi_layout_engine.py`

**Responsibilities**:
- Area hierarchy construction
- Initial area sizing (bottom-up)
- Engine selection and fallback handling
- DTO construction from positions
- Ligature routing coordination

**Pipeline**:
```python
1. Build hierarchy: _build_area_hierarchy_v2()
2. Calculate sizes: _calculate_area_sizes_bottom_up()
3. Position nodes: D3/Tulip/Python engine
4. Inflate areas: _inflate_containers_for_routing()
5. Create DTO: _create_dto_from_positions()
6. Route ligatures: _area_aware_ligature_routing()
7. Apply deltas: User overrides
```

### 2. D3LayoutEngine (Primary - Hard Containment)

**Files**: 
- `src/d3_layout_engine.py` (Python bridge)
- `src/d3_layout_bridge.js` (Node.js simulation)

**Why Primary**: Only engine with 100% correct containment

**Key Features**:
- **Hard containment force**: Clips nodes to area boundaries
- **Hard exclusion force**: Pushes nodes out of child cuts
- **N-ary relations**: Edge labels as nodes, nu mapping as binary links
- **Deterministic**: Same input → same output

**Custom Forces** (JavaScript):
```javascript
// Run on EVERY tick - not soft forces!
forceContainment(): HARD clip to area bounds
forceExclusion(): HARD push out of child cuts

// Standard D3 forces (aesthetic)
forceLink(): Pull connected nodes together
forceManyBody(): Repel all nodes
forceCollide(): Prevent overlap
```

**Performance**: 4-8s per graph (acceptable for interactive use)

**Dependencies**: Node.js, d3-force npm package

### 3. TulipLayoutEngine (Fallback - Fast but Imperfect)

**File**: `src/tulip_layout_engine.py`

**Why Fallback**: 75% correct (acceptable for drafts), fast (0.3s)

**Architecture**:
- **Hierarchical subgraphs**: Cuts as subgraphs
- **Predicate nodes**: Edge labels as nodes  
- **Binary edges**: Nu mapping with hook indices
- **Hierarchical Graph algorithm**: Respects graph structure

**Limitations**:
- ❌ Subgraphs are logical, not spatial containers
- ❌ Force optimization can violate boundaries
- ❌ Python API missing key features (handle clusters, setOwnership)
- ⚠️ ~25% violation rate (1-2 elements per graph)

**When to use**: 
- Node.js unavailable
- Draft/preview mode
- Speed critical, correctness flexible

**Dependencies**: tulip-python (pip install tulip-python)

### 4. ConstrainedForceLayout (Emergency Fallback)

**File**: `src/constrained_force_layout.py`

**Why Emergency**: Pure Python, no dependencies, but slow and imperfect

**Architecture**:
- Naive Python force simulation
- Soft boundary forces (not hard constraints)
- Per-area simulation with exclusion zones

**Performance**: 10s+ per graph

**When to use**: Both D3 and Tulip unavailable

### 5. AreaAwarePathfinder (Ligature Routing)

**File**: `src/area_aware_pathfinder.py`

**Used by**: All engines (final pass after node positioning)

**Algorithm**: Area-aware A* pathfinding

**Features**:
- **Legal corridor navigation**: Only paths through proper cuts
- **Collision avoidance**: Routes around vertices, edges, cut boundaries
- **Grid-based**: Discrete grid for efficient pathfinding
- **Waypoint optimization**: Removes unnecessary intermediate points

**Why necessary**: 
- Layout engines position nodes, not paths
- Straight lines would violate cuts or collide with obstacles
- A* finds optimal legal path between positioned endpoints

## Data Flow

### Input: EGI
```python
egi.vertices()     # Set of vertex IDs
egi.nu            # Dict: edge_id → [vertex_id, ...]
egi.rel           # Dict: edge_id → label string
egi.area          # Dict: area_id → [element_ids]
```

### Intermediate: Hierarchy + Positions
```python
hierarchy = {
    area_id: {
        'parent': parent_id,
        'children': [child_ids],
        'vertices': [vertex_ids],
        'edges': [edge_ids]
    }
}

global_positions = {
    'vertices': {
        vertex_id: {'x': float, 'y': float, 'parent_area_id': str}
    },
    'edge_labels': {
        edge_id: {'x': float, 'y': float, 'width': float, 
                  'height': float, 'label': str, 'parent_area_id': str}
    }
}
```

### Output: LayoutDTO
```python
LayoutDTO(
    areas: [RenderableArea],        # Rectangles for cuts + sheet
    vertices: [RenderableVertex],   # Positioned vertex circles
    edge_labels: [RenderableEdge],  # Positioned text labels
    ligatures: [RenderableLigature] # Routed paths
)
```

## Why This Architecture?

### Separation of Concerns

1. **Node positioning**: Layout engines (D3/Tulip/Python)
   - Optimize: aesthetic quality, containment
   - Output: (x, y) coordinates

2. **Path routing**: AreaAwarePathfinder
   - Input: Fixed node positions
   - Optimize: Shortest legal path
   - Output: Waypoint sequences

**Why separate?**: Different optimization problems with different algorithms

### Fallback Chain Philosophy

**Each tier trades off**:
- D3: Best correctness, medium speed, external dependency
- Tulip: Good speed, acceptable quality, external dependency  
- Python: Always available, slow, lower quality

**User experience**: "Just works" - automatic graceful degradation

### N-ary Relations → Binary Edges Pattern

**All engines** use the same transformation:
```
EGI: (Teaches prof course)  [3-ary relation]
     ν(Teaches) = [prof, course]

Graph Model:
  Node: "Teaches" (predicate node)
  Edge: "Teaches" → prof (hook_index=1)
  Edge: "Teaches" → course (hook_index=2)
```

**Why universal**: Layout libraries only handle binary edges

## Performance Profile

**Measured on M-series Mac, ~5 elements, 1-2 cuts**:

| Engine | Time | Correctness | Availability |
|--------|------|-------------|--------------|
| D3 | 4-8s | 100% | Node.js required |
| Tulip | 0.3s | 75% | tulip-python required |
| Python | 10s+ | 60-70% | Always available |

**Bottlenecks**:
- D3: Subprocess + JSON serialization (~2s overhead)
- Tulip: Layout algorithm (~0.3s, fast!)
- Python: Naive simulation (10s+ for convergence)

## Testing Strategy

### Unit Tests
- Each engine tested independently
- Verify containment correctness
- Measure performance

### Integration Tests
- Full pipeline: EGI → LayoutDTO → SVG
- Corpus validation (15 graphs)
- Visual inspection of output

### Containment Verification
```python
def verify_containment(svg_path, expected):
    """Parse SVG and verify element positions vs. cut boundaries"""
    violations = []
    
    for element in parse_elements(svg):
        area = element.parent_area
        if not inside_bounds(element.pos, area.bounds):
            violations.append(f"{element.id} outside {area.id}")
        
        for child_cut in area.children:
            if inside_bounds(element.pos, child_cut.bounds):
                violations.append(f"{element.id} inside child {child_cut.id}")
    
    return violations
```

## Future Enhancements

### Short-term
1. **Persistent D3 process**: Reduce overhead 2s → 0.5s
2. **Tune force parameters**: EGI-specific aesthetics
3. **Post-process Tulip**: Fix violations to reach 100%

### Medium-term
1. **Port D3 forces to Python**: Eliminate subprocess
2. **Magnetic grid**: Snap to alignment for cleaner diagrams
3. **Layout caching**: Avoid re-layout on style changes

### Long-term
1. **OR-Tools solver**: Constraint optimization for provably optimal layouts
2. **Machine learning**: Learn good layouts from corpus
3. **Interactive refinement**: User feedback → better defaults

## Dependencies Matrix

| Engine | Required | Optional | Fallback |
|--------|----------|----------|----------|
| **D3** | Node.js (≥14), d3-force npm | - | Tulip |
| **Tulip** | tulip-python | - | Python |
| **Python** | *(built-in)* | - | None |
| **Pathfinder** | pathfinding pip | - | None |

**Installation commands**:
```bash
# Node.js + D3
brew install node          # or: https://nodejs.org
npm install d3-force

# Tulip
pip uninstall tulip        # Remove temporal logic package if present
pip install tulip-python

# Python force sim (already included)
# No additional deps
```

## Lessons Learned

### What Didn't Work

1. **Graphviz clusters**: Soft containers, 30-40% violations
2. **Tulip meta-nodes**: API too complex, couldn't configure
3. **Tulip handle_clusters**: Doesn't exist in Python API
4. **Tulip bottom-up layout**: Can't set subgraph sizes
5. **Soft containment forces**: Always violated under edge pressure

### What Worked

1. **Hard containment forces**: Clip and kill velocity
2. **Custom D3 forces**: Run every tick, override aesthetics
3. **Two-pass architecture**: Position then route separately
4. **Fallback chain**: Graceful degradation
5. **N-ary → binary pattern**: Universal transformation

### Key Insight

**Aesthetic optimization and logical constraints are fundamentally different problems.**

Layout libraries optimize for beauty. EGI requires correctness. The only solution is to **explicitly override aesthetic forces** with hard logical constraints.

D3's custom force API is the only tool we found that allows this.

## Conclusion

**Production System**: D3-force with hard containment forces

**Why it works**:
- ✅ 100% containment correctness
- ✅ Aesthetic quality from D3's mature simulation
- ✅ Fallback chain for robustness
- ✅ Proven on full corpus

**Trade-offs accepted**:
- ⚠️ 4-8s per graph (acceptable for interactive use)
- ⚠️ Node.js dependency (standard dev tool)
- ⚠️ Subprocess overhead (can be optimized)

The months-long search through Graphviz, Python, and Tulip was necessary to prove that **custom hard forces are the only solution** to EGI's unique containment requirements.
