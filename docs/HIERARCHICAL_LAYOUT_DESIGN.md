# Hierarchical Per-Area Layout Design

## Principle
**Area membership constrains positioning from the start, not as validation after the fact.**

## Core Architecture

### **Bottom-Up Layout Algorithm**

```
For each area in bottom-up order (innermost first):
  1. Get elements assigned to THIS area from egi.area
  2. Layout elements in LOCAL coordinate space (0,0 to w,h)
  3. Apply user deltas IF valid in local space
  4. Calculate bounding box with padding
  5. Position this area within parent's coordinate space
  6. Transform local coordinates to global
```

### **Guarantees**
- Elements CANNOT be positioned outside their area (local coordinate system bounds them)
- User deltas validated before application (rejected if outside local bounds)
- Areas sized by their contents (bottom-up ensures children already sized)
- Deterministic (same EGI + deltas = same layout)

---

## User Delta Handling

### **Migration Across Transformations**

```python
def migrate_layout_deltas(old_deltas, egi_old, egi_new):
    """
    Migrate user positioning from old EGI to new EGI.
    Principle: Discard any delta that doesn't make logical sense.
    """
    new_deltas = LayoutDeltas()
    
    for element_id, delta in old_deltas.deltas.items():
        # Rule 1: Element must still exist
        if not element_exists(element_id, egi_new):
            continue  # Discard - element removed
        
        # Rule 2: Area membership must be unchanged
        old_area = find_element_area(egi_old, element_id)
        new_area = find_element_area(egi_new, element_id)
        
        if old_area != new_area:
            continue  # Discard - area changed, local coords invalid
        
        # Rule 3: Position deltas must pass validation
        if delta.delta_type in ['vertex_position', 'edge_position']:
            # Will be validated during layout (within local bounds)
            new_deltas.add(delta)
        
        # Rule 4: Ligature paths must still be valid
        elif delta.delta_type == 'ligature_path':
            if validate_ligature_structure(delta, egi_new):
                new_deltas.add(delta)
            # else: discard, will re-route
    
    return new_deltas
```

### **Application During Layout**

```python
def layout_area_with_deltas(area_id, elements, egi, deltas):
    """
    Layout elements within an area, applying user deltas if valid.
    """
    # Generate DOT for this area's elements only
    dot_lines = ["graph Area {"]
    
    for vertex in [v for v in egi.V if v.id in elements]:
        # Check for user position delta
        if vertex.id in deltas and deltas[vertex.id].delta_type == 'vertex_position':
            delta = deltas[vertex.id]
            # Apply as pinned node (Graphviz will respect it)
            x, y = delta.new_position
            dot_lines.append(f'  {vertex.id} [pos="{x},{y}!", pin=true];')
        else:
            # Normal node (Graphviz will position it)
            dot_lines.append(f'  {vertex.id} [shape=point];')
    
    # Similar for edges...
    
    # Run Graphviz in LOCAL space
    result = run_graphviz("\n".join(dot_lines))
    
    # Validate all positions are within reasonable local bounds
    positions = parse_positions(result)
    
    # If any position is extreme, reject ALL user deltas for this area
    # and re-run without pins (fall back to deterministic)
    if any_position_extreme(positions):
        return layout_area_without_deltas(area_id, elements, egi)
    
    return positions
```

---

## Coordinate System Management

### **Local Coordinate Spaces**

Each area has its own local coordinate system:
- Origin (0, 0) at top-left
- Bounded by area's content
- Graphviz operates in this space

### **Transformation to Global**

After bottom-up layout:
```python
def transform_to_global(area_hierarchy, area_positions):
    """
    Transform local coordinates to global coordinate system.
    Bottom-up: children positioned, then transform their coords.
    """
    global_positions = {}
    
    def transform_area(area_id, parent_offset=(0, 0)):
        # Get this area's position within its parent
        area_offset = area_positions[area_id]
        global_offset = (parent_offset[0] + area_offset[0],
                        parent_offset[1] + area_offset[1])
        
        # Transform all elements in this area
        for element in egi.area[area_id]:
            local_pos = local_positions[element]
            global_positions[element] = (
                global_offset[0] + local_pos[0],
                global_offset[1] + local_pos[1]
            )
        
        # Recursively transform children
        for child_id in children_of(area_id):
            transform_area(child_id, global_offset)
    
    transform_area(egi.sheet, (0, 0))
    return global_positions
```

---

## Preserving What Works

### **Keep: Ligature Routing**
✓ Already works perfectly with area awareness
✓ Legal corridor calculation
✓ AreaAwareFinder A* pathfinding
✓ Custom path validation

**Change needed**: Route ligatures AFTER global coordinate transformation

### **Keep: User Delta Types**
✓ `vertex_position` - validated in local space
✓ `edge_position` - validated in local space  
✓ `ligature_path` - validated for structure + collisions

### **Keep: Styling System**
✓ Polarity-based alternation
✓ Style specification
✓ Platform-independent DTO

---

## Implementation Steps

### **Phase 1: Core Hierarchical Layout**
1. ✅ Implement `layout_single_area(area_id, elements, egi, deltas)`
   - Generates DOT for area's elements only
   - Runs Graphviz in local space
   - Returns local positions + bounding box

2. ✅ Implement `layout_bottom_up(egi, deltas)`
   - Processes areas in bottom-up order
   - Calls layout_single_area for each
   - Builds area hierarchy

3. ✅ Implement `transform_to_global(local_positions, area_hierarchy)`
   - Transforms all local coords to global
   - Preserves area containment

### **Phase 2: Delta Migration**
4. ✅ Implement `migrate_layout_deltas(old_deltas, egi_old, egi_new)`
   - Validates element existence
   - Validates area unchanged
   - Validates ligature structure

5. ✅ Implement delta validation in layout
   - Check positions within local bounds
   - Fall back to deterministic if invalid

### **Phase 3: Integration**
6. ✅ Replace `_unified_force_directed_layout` with hierarchical approach
7. ✅ Update `_create_dto_from_positions` to use global positions
8. ✅ Keep `_area_aware_ligature_routing` (no changes needed!)
9. ✅ Update tests to verify area confinement

### **Phase 4: Testing**
10. ✅ Test with corpus graphs
11. ✅ Test with user deltas
12. ✅ Test with transformation sequences
13. ✅ Verify visual quality matches or exceeds current

---

## Expected Benefits

### **Correctness**
- ✅ Area violations architecturally impossible
- ✅ User deltas cannot break EGI logic
- ✅ Deterministic layouts guaranteed

### **Visual Quality**
- ✅ Vertices clearly within their areas (not near boundaries)
- ✅ Predicates grouped with same-area vertices
- ✅ Proper nesting visual hierarchy

### **Maintainability**
- ✅ Simple mental model: area = coordinate space
- ✅ Clear validation rules
- ✅ No circular dependencies

---

## Fallback Strategy

At any point where user delta causes issues:
1. Log warning
2. Discard problematic delta
3. Re-layout with deterministic algorithm
4. Continue successfully

**User sees**: "Position override discarded - violates area constraint"
**System behavior**: Graceful degradation, not failure
