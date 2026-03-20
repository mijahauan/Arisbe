# Tulip Layout Architecture for EGI

**Date**: 2025-10-05  
**Status**: Implementing

## The Standard Workaround: N-ary Relations as Predicate Nodes

### Problem
Tulip (and most graph layout libraries) only support **binary edges** connecting two nodes. EGI has **n-ary relations** where one edge label connects to multiple vertices.

### Solution
**Model edge labels as nodes**, connected to vertices via binary edges:

```
EGI Model:
  Edge "Between" connects to (v_x, v_y, v_z)  // 3-ary relation

Tulip Model:
  Node: predicate_Between
  Binary Edge: predicate_Between → v_x (hook_index=1)
  Binary Edge: predicate_Between → v_y (hook_index=2)  
  Binary Edge: predicate_Between → v_z (hook_index=3)
```

## Translation: EGI → Tulip Compound Graph

### Node Types

**1. Vertex Nodes** (`is_predicate=False`)
- Represent EGI vertices
- Small circles in visualization
- Size: 6x6

**2. Predicate Nodes** (`is_predicate=True`)
- Represent EGI edge labels
- Text labels in visualization
- Size: variable based on label length

**3. Meta-Nodes** (Tulip compound graph feature)
- Represent EGI cuts
- Contain other nodes (hierarchical containment)
- Not rendered as nodes themselves

### Edge Properties

**Binary Edges**: Connect predicate nodes to vertex nodes

**hook_index Property**: Integer (1, 2, 3, ..., n)
- Preserves the ν mapping order
- Essential for reconstructing n-ary relations
- Used during ligature rendering

### Area Containment

**Tulip Meta-Nodes** = **EGI Cuts**

```python
# Sheet elements not in cuts
for elem in egi.area[sheet]:
    node = create_node(elem)
    # Node stays at graph root

# Cut elements
for elem in egi.area[cut_id]:
    node = create_node(elem)
    graph.createMetaNode([node], meta_node_for_cut)
    # Node becomes child of meta-node
```

**Key Benefit**: Tulip's layout algorithms **natively respect** meta-node containment. Elements inside a meta-node cannot position outside it.

## Why This Works

### 1. Excellent Node Positioning
Force-directed algorithms naturally cluster related nodes:
- Binary edges act as springs
- Predicate node pulled toward all its connected vertices
- Result: Optimal placement that minimizes total edge length

### 2. Hard Containment Guaranteed
Tulip's meta-nodes provide:
- Native hierarchical graph support
- Automatic containment enforcement
- No "soft forces" that can be violated

### 3. High Performance
- C++ core implementation
- Optimized for large graphs
- Much faster than Python/Node.js subprocess approaches

### 4. Simplicity
- Standard graph modeling pattern
- Leverages mature, battle-tested algorithms
- Clean separation: Tulip for positioning, custom code for rendering

## Two-Phase Architecture

### Phase 1: Tulip Compound Graph Layout

**Input**: EGI (vertices, edges, nu mapping, areas)

**Process**:
1. Create vertex nodes
2. Create predicate nodes (one per edge label)
3. Create binary edges (predicate → vertices)
4. Assign nodes to meta-nodes (containment)
5. Run Tulip layout algorithm (FM³, GEM, or hierarchical)

**Output**: Optimized (x, y) positions for all nodes

### Phase 2: Area-Aware Ligature Pathfinding

**Input**: Fixed node positions from Tulip

**Process**:
1. For each n-ary relation (edge label + vertices):
2. Retrieve hook indices to determine order
3. Run Area-Aware A* pathfinding for each ligature
4. Find path from predicate node to each vertex
5. Respect cut boundaries (legal crossings only)
6. Avoid collisions with other elements

**Output**: RenderableLigature paths (series of waypoints)

**Why Necessary**: Tulip's binary edges are just straight lines. We need smart paths that:
- Route around obstacles
- Respect cut boundaries (logical correctness)
- Create visually clean diagrams

## Algorithm Details

### Tulip Layout Algorithms

**FM³ (Fast Multipole Method)** - Recommended
- Force-directed with multilevel approach
- Excellent for medium graphs (10-1000 nodes)
- Fast convergence

**GEM (Frick)** - Fallback
- Simple force-directed
- Works on all graphs
- Slightly slower convergence

**Hierarchical** - For deeply nested cuts
- Explicitly optimizes hierarchical structure
- Best for graphs with many nested cuts

### Configuration

```python
tulip_engine = TulipLayoutEngine()
positions, bounds = tulip_engine.generate_layout(
    egi, 
    hierarchy,
    area_bounds,
    algorithm="FM^3 (OGDF)"  # or "GEM (Frick)" or "Hierarchical"
)
```

## Advantages Over Previous Approaches

| Approach | Containment | Performance | N-ary Support | Deterministic |
|----------|-------------|-------------|---------------|---------------|
| **Graphviz (dot)** | ❌ Soft clusters | ✅ Fast | ❌ Not well | ✅ Yes |
| **Force Sim (Python)** | ❌ Soft forces | ❌ Slow | ✅ Yes | ❌ Random |
| **D3 (Node.js)** | ❌ Soft forces | ⚠️ Medium | ✅ Yes | ❌ Random |
| **Tulip** | ✅ Hard meta-nodes | ✅ Fast (C++) | ✅ Predicate nodes | ✅ Yes |

## Installation

```bash
# Via pip
pip install tulip-python

# Via conda
conda install -c conda-forge tulip-python
```

## Limitations

1. **Ligature routing still required**: Tulip only positions nodes, not intelligent paths
2. **Learning curve**: Tulip API is complex (but we hide it)
3. **Dependency**: Requires external library (but provides fallbacks)

## Fallback Strategy

```
Try Tulip (optimal)
  ↓ fails
Try D3.js (good)
  ↓ fails  
Try Python force sim (acceptable)
```

All three use the same interface, so switching is seamless.

## References

- Tulip Framework: https://tulip.labri.fr/
- Tulip Python Docs: https://tulip.labri.fr/Documentation/current/tulip-python/html/
- FM³ Paper: Hachul & Jünger (2005)
- Compound Graph Visualization: Sugiyama & Misue (1991)
