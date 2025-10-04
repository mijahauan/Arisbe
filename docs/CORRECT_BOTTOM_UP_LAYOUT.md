# Correct Bottom-Up Layout Architecture

## Problem Statement

**Current Issue**: Vertices appear near cut boundaries because:
1. Graphviz positions all elements globally without area knowledge
2. Cut boundaries calculated AFTER positioning to fit around contents
3. No way to enforce clearance from boundaries that don't exist yet

**Root Cause**: Cut boundaries are **derived** from element positions, not **positioned** as elements themselves.

## Solution: Cuts as First-Class Positioned Elements

### Core Principle

> A cut is a rectangular container whose SIZE is determined by its contents (bottom-up),
> but whose POSITION is determined by layout within its parent area (alongside siblings).

### Bottom-Up Algorithm

```
For each area (innermost cuts first, then parents, finally sheet):

  STEP 1: COLLECT Direct Elements
  ├─ Vertices: {v1, v2, ...} - points to position
  ├─ Edges: {e1, e2, ...} - labeled boxes to position  
  └─ Child Cuts: {cut1, cut2, ...} - rectangles with KNOWN dimensions
  
  STEP 2: LAYOUT in Local Coordinate Space
  ├─ Create Graphviz graph with:
  │  ├─ Vertex nodes (shape=point)
  │  ├─ Edge label nodes (shape=box, label="...")
  │  ├─ Cut nodes (shape=box, width=W, height=H, fixedsize=true)
  │  └─ Ligatures connecting them
  ├─ Run Graphviz layout engine (neato)
  └─ Parse positions for ALL elements (including cut rectangles)
  
  STEP 3: SIZE this Area
  ├─ Calculate bounding box around all positioned elements
  └─ This area now has known dimensions for its parent
  
  STEP 4: RECURSE to Parent
  └─ This area becomes a rectangular element in parent's layout
```

### Example: `(Human "Socrates") ~[ ~[ (Mortal "Socrates") ] ]`

```
ITERATION 1: Layout innermost cut (c_inner)
  Elements: [Mortal edge]
  Graphviz: Positions Mortal at local (10, 10)
  Size: 50x30 (edge box + padding)
  Result: c_inner is 50x30 rectangle

ITERATION 2: Layout middle cut (c_middle)  
  Elements: [c_inner (50x30 rectangle)]
  Graphviz: Positions c_inner rectangle at local (15, 15)
  Size: 80x60 (rectangle + padding)
  Result: c_middle is 80x60 rectangle

ITERATION 3: Layout sheet
  Elements: [Socrates vertex, Human edge, c_middle (80x60 rectangle)]
  Graphviz: Positions:
    - Socrates at (30, 40)
    - Human at (25, 15)  
    - c_middle rectangle at (70, 50)
  Size: 170x100 (union + padding)
  
  ✅ Socrates clearly separated from c_middle rectangle!
  ✅ c_middle boundary is at positioned location, not derived
```

## Architectural Guarantees

### ✅ **Area Confinement by Construction**
- Elements laid out within their area's local coordinate space
- Cut boundaries positioned explicitly by Graphviz
- Parent areas sized to contain all elements + child cuts

### ✅ **Boundary Clarity**
- Cuts are positioned rectangles, not derived boundaries
- Graphviz ensures spacing between elements (including cut rectangles)
- Natural clearance from cut boundaries

### ✅ **Hierarchical Integrity**
- Child cuts sized before parent layout
- Nesting preserved through coordinate transformation
- No circular dependencies (size bottom-up, position top-down)

## Implementation Strategy

### Phase 1: Core Bottom-Up Layout
```python
def _bottom_up_layout(egi, style):
    # Build hierarchy
    hierarchy = _build_area_hierarchy(egi)
    
    # Process bottom-up
    area_layouts = {}
    for area_id in _bottom_up_order(hierarchy):
        area_layouts[area_id] = _layout_area_with_cuts(
            area_id, egi, hierarchy, area_layouts, style
        )
    
    return area_layouts

def _layout_area_with_cuts(area_id, egi, hierarchy, child_layouts, style):
    """Layout area treating child cuts as rectangular elements"""
    
    # Collect direct elements
    vertices = [v for v in egi.V if v.id in egi.area[area_id]]
    edges = [e for e in egi.E if e.id in egi.area[area_id]]
    child_cuts = [c for c in egi.Cut if c.id in egi.area[area_id]]
    
    # Generate DOT with cuts as rectangles
    dot = ["graph Area {"]
    
    # Add vertices
    for v in vertices:
        dot.append(f'  {v.id} [shape=point];')
    
    # Add edges  
    for e in edges:
        rel = egi.rel[e.id]
        dot.append(f'  {e.id} [shape=box, label="{rel}"];')
    
    # Add child cuts as RECTANGLES with known dimensions
    for cut in child_cuts:
        child_layout = child_layouts[cut.id]
        width_inches = child_layout['width'] / 72  # Convert to inches
        height_inches = child_layout['height'] / 72
        dot.append(f'  {cut.id} [shape=box, width={width_inches}, '
                  f'height={height_inches}, fixedsize=true, label=""];')
    
    # Add ligatures
    for e in edges:
        for v_id in egi.nu[e.id]:
            dot.append(f'  {v_id} -- {e.id};')
    
    dot.append("}")
    
    # Run Graphviz
    positions = _execute_graphviz(dot)
    
    # Calculate bounding box
    bbox = _calculate_bbox(positions)
    
    return {
        'positions': positions,  # Includes cut rectangle positions!
        'width': bbox.width,
        'height': bbox.height
    }
```

### Phase 2: Coordinate Transformation
After bottom-up layout, transform local coordinates to global:
- Cuts have positions in parent's coordinate space
- Elements inside cuts get cut's position as offset
- Recursive transformation preserves nesting

### Phase 3: DTO Creation
```python
def _create_dto(egi, area_layouts):
    dto = LayoutDTO()
    
    # Create RenderableAreas using positioned cut rectangles
    for cut in egi.Cut:
        layout = area_layouts[cut.id]
        parent_layout = area_layouts[get_parent(cut.id)]
        cut_pos = parent_layout['positions'][cut.id]
        
        area = RenderableArea(
            id=cut.id,
            rect=Rect(cut_pos.x, cut_pos.y, layout['width'], layout['height'])
        )
        dto.areas.append(area)
    
    # Create vertices/edges at their transformed global positions
    # ...
```

## Benefits

1. **Correctness**: Area confinement architecturally enforced
2. **Clarity**: Elements clearly separated from cut boundaries
3. **Simplicity**: Single unified algorithm, no special cases
4. **User Edits**: Pinned positions work naturally in local space
5. **Determinism**: Same EGI always produces same layout

## Migration Path

1. Implement new layout algorithm alongside existing
2. Test on corpus graphs
3. Compare visual quality
4. Switch over when validated
5. Remove old unified layout code

## Testing Checklist

- [ ] All corpus graphs render correctly
- [ ] No area violations (elements outside their areas)
- [ ] Clear visual separation (elements away from cut boundaries)
- [ ] Proper nesting (cuts inside their parents)
- [ ] User position deltas work correctly
- [ ] Ligatures route correctly across boundaries
- [ ] Performance acceptable for complex graphs
