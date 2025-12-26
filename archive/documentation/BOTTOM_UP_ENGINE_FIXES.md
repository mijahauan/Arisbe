# Bottom-Up Engine Bug Fixes

## Issues Reported

1. **State Accumulation**: Areas from previous graphs appearing in new layouts
2. **Wild Element Placement**: Elements positioned in virtual coordinates without normalization
3. **Viewport Sizing**: Diagrams not fitting the view properly
4. **Missing Ligatures**: No ligatures being rendered

## Root Causes

### 1. State Accumulation Bug

**Problem:** Engine reused across multiple layouts without clearing state
```python
# OLD: State persisted between calls
def generate_layout(self, egi, style, deltas=None):
    # element_positions still has old data!
    self._calculate_element_sizes(egi, style)
```

**Fix:** Clear all state dictionaries at start of each layout
```python
# NEW: Fresh state for each layout
def generate_layout(self, egi, style, deltas=None):
    # CRITICAL: Clear state from previous runs
    self.element_positions.clear()
    self.area_bounds.clear()
    self.element_sizes.clear()
```

### 2. Coordinate Normalization Bug

**Problem:** D3 positions elements in virtual 800x600 box, but tight bounds has arbitrary min_x/min_y

Example:
```
Virtual box: 800x600
Elements positioned at: (350, 280), (420, 310), etc.
Tight box calculated: x=330, y=260, w=120, h=80
```

But positions were NEVER translated! So renderer got:
- Element at (350, 280) - expects (0-120, 0-80)  
- Container at x=330 - expects x=0

**Fix:** Translate ALL positions to (0,0) origin after calculating tight box
```python
# Calculate tight box
tight = self._calculate_tight_bounds(content_ids, child_bounds)

# TRANSLATE all positions to (0,0) origin
offset_x = tight.x
offset_y = tight.y

for elem_id in content_ids:
    x, y = self.element_positions[elem_id]
    self.element_positions[elem_id] = (x - offset_x, y - offset_y)

# Also translate child cut bounds
for child_id, child_tight in child_bounds.items():
    translated_bounds = TightBounds(
        x=child_tight.x - offset_x,
        y=child_tight.y - offset_y,
        width=child_tight.width,
        height=child_tight.height
    )
    self.area_bounds[child_id] = Rect(...)

# Return normalized bounds starting at (0,0)
return TightBounds(x=0, y=0, width=tight.width, height=tight.height)
```

### 3. Missing Ligatures

**Problem:** DTO had no ligatures, so SVG renderer couldn't draw complete diagrams

**Fix:** Added simple straight-line ligature routing
```python
def _add_ligatures(self, egi, dto, style):
    for edge_id in [e.id for e in egi.E]:
        vertex_ids = egi.get_incident_vertices(edge_id)
        edge_pos = self.element_positions[edge_id]
        
        for hook_idx, v_id in enumerate(vertex_ids):
            v_pos = self.element_positions[v_id]
            dto.ligatures.append(RenderableLigature(
                start_vertex_id=v_id,
                end_edge_id=edge_id,
                end_hook_index=hook_idx,
                path_points=[v_pos, edge_pos]
            ))
```

## Expected Results After Fixes

### dau_2006_p112_ligature
- **Before**: Ghost cuts from previous graphs, elements positioned wildly
- **After**: 1 cut (c_4c90e760), 1 vertex, 3 edges, properly positioned
- **Coordinates**: All normalized to (0,0) origin

### dau_theorem_proving  
- **Before**: Correct cut count but wild positioning
- **After**: Elements positioned correctly within their containers
- **Viewport**: Diagram fits the view

### mixed_quantifier_complex
- **Before**: 5 cuts appearing (accumulation), overlaps
- **After**: Correct number of cuts (2), no overlaps
- **Nesting**: Inner cut properly contained within outer

## Testing

Run standalone test:
```bash
python test_bottom_up_engine.py
```

Expected output:
```
Laying out c_4c90e760:
  D3 positioned 2 elements
  Tight box: 79x119 (normalized to origin)  ← Note: normalized!
  
Laying out sheet_708e75e7:
  D3 positioned 2 elements
  Tight box: 651x472 (normalized to origin)  ← Always starts at 0,0
  
✅ Complete: 1V, 3E, 3L  ← Ligatures present!
```

## Next Steps

1. **Test in Organon GUI**: Load problematic graphs and verify fixes
2. **Improve ligature routing**: Replace straight lines with area-aware A* pathfinding
3. **Add port calculation**: For cross-boundary ligatures
4. **Implement user deltas**: Respect pinned positions and custom paths
