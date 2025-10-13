# Bottom-Up D3 Engine: Final Architecture

## Core Principle: **Complete Independence**

Each cut layouts its content **completely independently** in its own virtual space. The SVG renderer handles the hierarchical positioning based on the EGI's `area` mapping.

## Architecture

### 1. **Recursive Bottom-Up Layout**

```python
def _layout_cut_recursive(egi, cut_id, child_bounds):
    # Get elements directly in this cut
    content_ids = [elem for elem in egi.area.get(cut_id, []) 
                   if elem.startswith(('v_', 'e_'))]
    
    # Layout content in virtual space
    tight_bounds = _layout_cut(egi, cut_id, content_ids, child_bounds,
                                virtual_width, virtual_height)
    
    return tight_bounds
```

### 2. **Independent D3 Layout**

Each cut's content is laid out in a **fresh virtual box** with:
- **Adaptive sizing**: Virtual box sized based on element count
- **Link forces**: Connected elements stay together (strength 1.5, distance 25px)
- **Collision forces**: Elements don't overlap
- **Containment force**: Elements stay inside virtual box
- **NO child cuts as obstacles**: Children are NOT part of parent simulation

```python
payload = {
    'bounds': {'x': 0, 'y': 0, 'width': virtual_width, 'height': virtual_height},
    'nodes': [content elements only],
    'links': [ν connections],
    'obstacles': [],  # EMPTY - no child cuts
    'seed': 42  # Deterministic
}
```

### 3. **Coordinate Normalization**

After d3 simulation, all positions are normalized to (0,0) origin:

```python
# Calculate tight box from actual positions
tight = _calculate_tight_bounds(content_ids)

# Translate all positions to (0,0) origin
offset_x = tight.x
offset_y = tight.y

for elem_id in content_ids:
    x, y = self.element_positions[elem_id]
    self.element_positions[elem_id] = (x - offset_x, y - offset_y)

# Return normalized bounds
return TightBounds(x=0, y=0, width=tight.width, height=tight.height)
```

### 4. **Renderer Responsibility**

The SVG renderer (or diagram controller) handles:
- **Positioning cuts** within their parents based on EGI's `area` hierarchy
- **Translating child coordinates** when rendering nested cuts
- **Drawing ligatures** across cut boundaries

## Why This Works

### ✅ **Separation of Concerns**
- **Layout engine**: Sizes each cut's content independently
- **Renderer**: Positions cuts hierarchically

### ✅ **No Coordinate Confusion**
- Each cut has its own (0,0)-based system
- No mixing of virtual spaces
- No complex coordinate transformations

### ✅ **Deterministic**
- Sorted iterations ensure consistent order
- Seed ensures reproducible random jitter
- Same graph → same layout every time

### ✅ **Scalable**
- Works for any nesting depth
- Each cut is independently simple
- No exponential complexity

## What We DON'T Do

### ❌ **Position child cuts in parent space**
- Tried: Grid distribution, centered stacking
- Problem: Coordinates from different virtual spaces mixed together
- Solution: Renderer positions cuts, not layout engine

### ❌ **Add child cuts as obstacles**
- Tried: Child cuts as fixed obstacles in parent's d3 simulation
- Problem: All children at same position, elements escape
- Solution: Each cut is independent, no cross-cut obstacles

### ❌ **Calculate parent size from child positions**
- Tried: Include child obstacle positions in tight bounds
- Problem: Child positions are in parent's virtual space, not normalized
- Solution: Parent size only from parent's own content

## Custom Containment Force

The `forceContainment` function in `d3_layout_worker.js` **teaches d3 about walls**:

```javascript
function forceContainment(bounds, obstacles) {
    function force(alpha) {
        for (const node of nodes) {
            // RULE 1: Clamp to container bounds
            if (node.x - halfWidth < 0) {
                node.x = halfWidth;
                node.vx = 0;  // Stop bouncing
            }
            // ... (similar for all 4 walls)
            
            // RULE 2: Eject from obstacles
            // (Currently empty obstacles array)
        }
    }
    return force;
}
```

**Applied every tick** to maintain containment as an unbreakable law.

## Data Flow

```
EGI with nested cuts
    ↓
Recursive layout (bottom-up)
    ↓
For each cut:
    1. Get content elements (vertices/edges in this cut)
    2. Layout in adaptive virtual box (d3-force + containment)
    3. Calculate tight bounds from actual positions
    4. Normalize to (0,0) origin
    5. Store in element_positions dict
    ↓
All cuts laid out independently
    ↓
Build LayoutDTO:
    - Vertices with positions (in their cut's coordinates)
    - Edge labels with positions (in their cut's coordinates)
    - Areas with sizes (width x height only)
    - Ligatures (straight lines for now)
    ↓
Renderer positions cuts hierarchically based on EGI.area
```

## Test Results

**Determinism**: ✅ Same graph → same layout  
**State management**: ✅ No accumulation across layouts  
**Sizing**: ✅ Adaptive virtual boxes prevent over-spreading  
**Containment**: ⏳ Each cut independent, renderer handles nesting

## Known Limitations

1. **No cross-cut ligature routing**: Ligatures are straight lines, may cross cut boundaries
2. **Renderer must handle nesting**: Layout engine only provides sizes, not positions
3. **Empty cuts with children**: Size estimated from child sizes (sum of widths)

## Next Steps

1. **Test in Organon**: Verify renderer handles independent coordinate systems
2. **Add A* pathfinding**: Area-aware ligature routing for clean diagrams
3. **Improve empty cut sizing**: Better heuristic for cuts with only children
4. **Connection ports**: Pre-defined attachment points for ligatures
