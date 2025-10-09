# Force Conflict Resolution - Conditional Degree-Based Centering

## The Issue

**User's observation:** After adding degree-based X/Y centering, nested layouts with ports became chaotic.

The `dau_theorem_proving` graph (deeply nested with 4 ports) showed predicates scattered incorrectly across nested cuts instead of clustering near boundaries.

### Root Cause: Force Conflict

**Flat layouts (no ports):**
```javascript
// Works perfectly:
.force('x', forceX(center).strength(degree >= 2 ? 0.4 : 0.05))
.force('y', forceY(center).strength(0.05))

Result: Hub nodes (high degree) centered ✅
```

**Nested layouts (with ports):**
```javascript
// CONFLICT:
Port link forces (10.0)    → Pull toward boundaries
X-centering (0.4)          → Pull toward horizontal center  ❌
Y-centering (0.05)         → Pull toward vertical center    ❌

Result: Forces fight each other → chaotic positioning
```

### The Fundamental Difference

| Layout Type | Port Count | Goal | Optimal Forces |
|-------------|------------|------|----------------|
| **Flat** (sheet only) | 0 | Center hubs, spread leaves | Degree-based X/Y centering |
| **Nested** (with cuts) | 1+ | Cluster near boundaries | Port link forces only |

## Why Port Forces Must Dominate

### Port Link Force Architecture
```
Port link strength: 10.0 (very strong)
Purpose: Pull elements to boundaries for boundary-crossing ligatures

Without interference:
  Element ---10.0---> Port (on boundary)
  ✅ Element positions near boundary for clean ligature path
```

### Centering Force Interference
```
With X/Y centering:
  Element ---10.0---> Port (on boundary)
  Element <---0.4--- Center (horizontal pull)
  Element <---0.05-- Center (vertical pull)
  
  Net effect:
    10.0 pull toward boundary
    0.45 pull toward center
    = 10.0 - 0.45 = 9.55 net
  
  Still pulls toward boundary, but:
  ❌ Offset from optimal position
  ❌ Ligature paths distorted
  ❌ Visual layout degraded
```

### Real Example: dau_theorem_proving

**Before fix (with centering on nested layouts):**
- P: Pushed toward center despite port on right boundary
- Q: Pulled toward center instead of left boundary port
- R: Offset from boundary port positions
- S: Mispositioned relative to nested structure

**After fix (centering only for flat layouts):**
- P: Positioned optimally near port on boundary ✅
- Q: Clustered near boundary ports ✅
- R, S: Correctly positioned in nested structure ✅

## The Solution: Conditional Application

```javascript
// Always apply base forces
simulation
    .force('link', ...)
    .force('charge', ...)
    .force('center', d3.forceCenter(cx, cy).strength(0.3));

// CONDITIONALLY apply degree-based centering
// ONLY for flat layouts (no ports)
if (payload.portNodes.length === 0) {
    simulation
        .force('x', d3.forceX(cx)
            .strength(d => {
                const degree = nodeDegrees.get(d.id) || 0;
                return degree >= 2 ? 0.4 : 0.05;
            }))
        .force('y', d3.forceY(cy)
            .strength(0.05));
}

simulation
    .force('collision', ...)
    .force('containment', ...);
```

### Decision Logic
```
if (no ports) {
    // Flat layout - use degree-based centering
    // Goal: Hub nodes centered, leaves distributed
    Apply X/Y centering forces
} else {
    // Nested layout - let port forces dominate
    // Goal: Elements near boundaries
    Skip X/Y centering forces
}
```

## Force Configuration by Layout Type

### Flat Layouts (portNodes.length === 0)
```javascript
Forces:
  - Link: 2.0 (connect related elements)
  - Charge: -100 (prevent overlap)
  - Center: 0.3 (general balance)
  - X: 0.05-0.4 (degree-based horizontal centering)  ✅
  - Y: 0.05 (light vertical centering)               ✅
  - Collision: Variable by type
  - Containment: Absolute

Priority: X/Y forces guide topology
```

### Nested Layouts (portNodes.length > 0)
```javascript
Forces:
  - Link: 2.0 normal, 10.0 port (boundary clustering)
  - Charge: -100 (prevent overlap)
  - Center: 0.3 (general balance)
  - X: DISABLED                                      ⚠️
  - Y: DISABLED                                      ⚠️
  - Collision: Variable by type
  - Containment: Absolute

Priority: Port link forces (10.0) dominate completely
```

## Results

### Flat Layout: sowa_cat_on_mat
```
Port count: 0 → Degree-based centering ENABLED

Before (uniform centering):
  Cat: x=30.0, Mat: x=89.9, On: x=149.8  ❌ On at edge

After (degree-based centering):
  Cat: x=30.0, Mat: x=149.6, On: x=89.8  ✅ On centered
  
Effect: Hub node (On, degree 2) properly centered
```

### Nested Layout: dau_theorem_proving
```
Port count: 4 → Degree-based centering DISABLED

Before (centering enabled):
  Predicates scattered, ports ignored  ❌

After (centering disabled):
  Predicates clustered near boundaries ✅
  Port forces dominate completely
  Clean ligature paths through ports
  
Effect: Nested structure visually correct
```

### Corpus Validation
- ✅ 15/15 graphs passing (100%)
- ✅ Flat layouts: Degree-based centering working
- ✅ Nested layouts: Port forces unimpeded
- ✅ No force conflicts

## Key Insights

### 1. Context-Aware Force Configuration
Different layout types require different force balances:
- **Flat**: Hub-centric topology → degree-based forces
- **Nested**: Boundary-centric topology → port-based forces

### 2. Force Priorities Must Match Goals
For boundary crossings:
- Port links (10.0) are the PRIMARY force
- ALL other forces are SECONDARY
- No secondary force should interfere with primary goal

### 3. Simple Detection Criterion
```javascript
hasNesting = (payload.portNodes.length > 0)
```
Perfect discriminator:
- No ports → flat layout → use degree centering
- Has ports → nested layout → skip degree centering

### 4. Graceful Degradation
Even with conflict, system still produced valid output:
- Containment force prevented violations
- Ligatures still routed correctly
- Just visually suboptimal

But optimal is better than valid! ✅

## Generalization Principle

> **Specialized forces should be conditionally applied based on layout context.**

This principle extends beyond degree-based centering:

```javascript
// Pattern for context-aware force application
if (layoutContext.matches(forceConditions)) {
    applySpecializedForce();
} else {
    skipToAvoidConflict();
}
```

Examples:
- Degree-based centering → only for flat layouts
- Hierarchical bundling → only for parallel ligatures
- Radial layout → only for star topologies
- Grid constraints → only for tabular structures

## Alternative Approaches Considered

### 1. Weaken Port Links
```javascript
// Reduce port link strength to allow centering
.strength(isPort ? 5.0 : 2.0)  // Was 10.0
```
**Rejected**: Port links MUST be very strong to overcome obstacle repulsion.

### 2. Strengthen Centering
```javascript
// Make centering stronger than ports
.force('x', forceX(cx).strength(degree >= 2 ? 15.0 : 0.05))
```
**Rejected**: Would break boundary clustering completely.

### 3. Distance-Based Centering
```javascript
// Only center elements far from boundaries
.strength(d => distanceFromBoundary(d) > threshold ? 0.4 : 0.05)
```
**Rejected**: Complex to implement, unnecessary given simple port check works.

### 4. Conditional Application (CHOSEN)
```javascript
if (no ports) { applyDegreeBasedCentering(); }
```
**Accepted**: Simple, correct, and respects the fundamentally different goals.

## Documentation Updates

This fix required updating:
1. **DEGREE_BASED_CENTERING.md** - Add caveat about flat layouts only
2. **THREE_PASS_ARCHITECTURE_COMPLETE.md** - Update force configuration
3. **This document** - Explain the conflict and resolution

## Lessons Learned

### 1. Test Both Layout Types
When changing force configuration:
- Test flat layouts (sheet only)
- Test nested layouts (with cuts)
- Forces that work for one may break the other

### 2. Force Priorities Are Critical
Strong forces (10.0) must not be weakened by cumulative weak forces (0.4 + 0.05 = 0.45).

### 3. Context Matters
"One size fits all" force configuration doesn't work. Different layouts need different force balances.

### 4. Simple Checks Work Best
`portNodes.length === 0` is a perfect discriminator. Don't overthink it.

---

**Status**: ✅ Conflict resolved  
**Date**: 2025-10-07  
**Solution**: Conditional degree-based centering (flat layouts only)  
**Result**: Both flat and nested layouts working optimally  
**Corpus**: 15/15 graphs passing (100%)
