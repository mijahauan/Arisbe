# EGI Ligature-Position Co-Optimization Specification

**Document ID**: `egi_ligature_position_cooptimization_spec`  
**Version**: 1.0  
**Date**: 2025-09-17  
**Status**: Implementation Required

## Overview

This specification defines the co-optimization approach for EGI spatial layout where element positions and ligature paths are jointly optimized to achieve minimal path lengths while maintaining all logical and spatial constraints.

## Core Principle

**Element positions within areas follow balanced spatial distribution by default**, with optimization achieved through **position exchange** rather than arbitrary movement. Single elements remain centered; multiple elements maintain equidistant spacing while exchanging positions to optimize ligature paths.

## Key Requirements

### 1. Legitimate Cut Crossings Analysis
- **Pre-routing step**: For each ligature, calculate exactly which cuts it's entitled to cross
- **Rule**: A ligature can cross a cut boundary if and only if the vertex and predicate are in different areas and the cut lies on the containment path between their areas
- **Everything else becomes a spatial obstacle** to avoid

### 2. Balanced Position Strategy
- **Default positioning**: Elements arranged in balanced patterns within areas (centered for single, equidistant for multiple)
- **Position exchange optimization**: Elements can swap between balanced positions to optimize ligature paths
- **Constraint**: Elements never move to arbitrary positions, only to other balanced positions within their area

### 3. Multi-Predicate Ligature Architecture
- **Trunk-and-branch strategy**: For vertices connected to multiple predicates
- **Most-removed predicate**: Route trunk ligature to predicate requiring most complex path (most cut crossings)
- **Branch connections**: Other predicates connect to optimal points on trunk ligature
- **Minimal total path length**: Achieved through coordinated vertex positioning

### 4. Spatial Constraint Enforcement
- **Area containment**: Elements must remain within their designated areas
- **Boundary clearance**: Elements positioned INSIDE area boundaries, never ON them
- **Spatial exclusivity**: No overlapping elements within same area
- **Obstacle avoidance**: Ligatures avoid all unconnected elements and illegitimate cut crossings

## Implementation Phases

### Phase 1: Containment Hierarchy Layout
- Build containment tree from EGI area mappings
- Calculate space requirements bottom-up
- Allocate spatial bounds top-down with guaranteed sibling separation

### Phase 2: Joint Position-Path Optimization
- Initialize element positions within areas (can be random)
- For each iteration:
  1. Calculate legitimate cut crossings for all ligatures
  2. Route all ligature paths given current positions
  3. Optimize element positions to reduce total path length
  4. Apply area and exclusivity constraints
  5. Check convergence

### Phase 3: Final Path Routing
- Route final ligature paths with optimized element positions
- Apply trunk-and-branch strategy for multi-predicate connections
- Ensure all paths respect legitimate crossings only

### Phase 4: Coordinate Conversion
- Convert ALU coordinates to device pixels
- Maintain all spatial relationships and constraints

## Success Criteria

1. **No overlapping elements** - exclusive spatial positioning maintained
2. **No boundary violations** - elements clearly inside areas with clearance
3. **Legitimate cut crossings only** - ligatures cross only entitled boundaries
4. **Minimal path complexity** - shortest valid paths through co-optimization
5. **Logical correspondence** - visual layout reflects EGI logical structure
6. **Convergent optimization** - algorithm reaches stable solution

## Key Algorithms

### Legitimate Crossings Calculation
```python
def calculate_legitimate_crossings(vertex_id: ElementID, predicate_id: ElementID, egi: EGI) -> Set[ElementID]:
    """Calculate which cuts this ligature is legitimately allowed to cross."""
    vertex_area = egi.get_context(vertex_id)
    predicate_area = egi.get_context(predicate_id)
    
    if vertex_area == predicate_area:
        return set()  # Same area - no crossings needed
    
    # Find containment path between areas
    path = find_containment_path(vertex_area, predicate_area, egi)
    return extract_boundary_cuts(path, egi)
```

### Position-Path Co-Optimization
```python
def optimize_positions_and_paths(egi: EGI, area_bounds: Dict[ElementID, ALURect]) -> Tuple[Dict[ElementID, ALUPoint], Dict[LigatureID, Path]]:
    """Co-optimize element positions and ligature paths iteratively."""
    element_positions = initialize_positions_in_areas(egi, area_bounds)
    
    for iteration in range(MAX_ITERATIONS):
        ligature_paths = route_all_ligatures(element_positions, egi)
        improved_positions = optimize_element_positions(element_positions, ligature_paths, area_bounds, egi)
        
        if converged(element_positions, improved_positions):
            break
            
        element_positions = improved_positions
    
    return element_positions, ligature_paths
```

## Integration Points

- **Containment Hierarchy Engine**: Provides area bounds and spatial constraints
- **Area Spatial Constraint System**: Enforces boundary clearance and containment
- **Ligature Optimization Engine**: Replaced with co-optimization approach
- **Two-Phase Layout Controller**: Orchestrates the complete process

## Testing Requirements

- **Roberts Disjunction**: Shared vertex positioned for optimal routing, ligatures avoid sibling cuts
- **Complex Nested Structures**: Multi-level optimization with legitimate crossings
- **Multi-Predicate Vertices**: Trunk-and-branch routing with minimal total path length
- **Boundary Violations**: No elements on cut boundaries, all properly contained
- **Convergence**: Algorithm reaches stable solution within reasonable iterations

---

**Implementation Priority**: High  
**Dependencies**: Containment Hierarchy Engine, Area Spatial Constraint System  
**Next Steps**: Implement co-optimization algorithm in new `LigaturePositionCoOptimizer` class
