# Current Layout Engine Pipeline

## Overview
The Definitive EGI Layout Engine uses a **three-step approach** with user edit support at multiple stages. This document details the exact order of operations.

---

## Main Pipeline: `generate_layout(egi, style, layout_deltas)`

### **STEP 1: Unified Force-Directed Layout**
**Method**: `_unified_force_directed_layout(egi, style, layout_deltas)`

**Purpose**: Position all vertices and edge labels using Graphviz force-directed algorithm

**Process**:
1. Generate DOT string with:
   - All vertices as point nodes
   - All edge labels as point nodes
   - Ligatures as edges between them
   - Graph-level attributes from style
   
2. **User Position Deltas (First Application)**:
   - Vertices/edges with `layout_deltas` position overrides are marked as **pinned nodes**
   - Graphviz syntax: `pos="x,y!", pin=true`
   - These nodes become **fixed anchor points** in the layout
   - Other nodes arrange around them via force-directed algorithm

3. Execute Graphviz (typically `neato` engine)

4. Parse resulting positions into `content_positions` dict:
   ```python
   {
       'vertices': {
           'v_id': {'x': float, 'y': float, 'parent_area_id': str},
           ...
       },
       'edge_labels': {
           'e_id': {'x': float, 'y': float, 'width': float, 'height': float, 
                    'label': str, 'parent_area_id': str},
           ...
       }
   }
   ```

5. **Area Assignment**: `_find_element_area(egi, element_id)`
   - Looks up which area contains element in `egi.area` mapping
   - Assigns `parent_area_id` to each element
   - **ISSUE**: This is done AFTER positioning, so positions may violate area membership!

**Output**: `content_positions` dict with (x, y) coordinates and area assignments

---

### **STEP 1.5: Apply User Position Overrides**
**Method**: `_apply_user_overrides_to_positions(egi, content_positions, layout_deltas)`

**Purpose**: Apply user-specified position changes that weren't used as pinned nodes

**Process**:
1. For each delta in `layout_deltas.deltas`:
   - If `delta_type == 'vertex_position'` and has `new_position`:
     - Directly update `content_positions['vertices'][element_id]` x, y
   - If `delta_type == 'edge_position'` and has `new_position`:
     - Directly update `content_positions['edge_labels'][element_id]` x, y

2. **NO VALIDATION AT THIS STAGE**
   - Positions are applied regardless of area bounds
   - Comment says: "rely on DTO-level validation to catch invalid positions"
   - **ISSUE**: Validation happens too late to prevent violations

**Output**: Modified `content_positions` with user overrides applied

---

### **STEP 2: Bottom-Up Bounding Box Calculation**
**Method**: `_calculate_bounding_boxes(egi, content_positions, style)`

**Purpose**: Calculate tight-fitting rectangles for all cuts based on their contents

**Process**:
1. Build cut hierarchy from `egi.area` mapping

2. Get padding from style: `style.raw_style_data['geometry']['padding']['area']`

3. Process cuts in **bottom-up order** (innermost first):
   - For each cut, find all elements directly in that area
   - Calculate bounding box that encloses all elements + padding
   - Store in `area_bounds[cut_id]`

4. Calculate sheet bounding box (outermost)

**Key Constraint**: Elements determine area size, not vice versa
- Areas expand to fit their contents
- **No checking** if contents are logically allowed in that area

**Output**: `area_bounds` dict mapping area_id to Rect

---

### **STEP 3: Create DTO from Positions**
**Method**: `_create_dto_from_positions(egi, content_positions, area_bounds)`

**Purpose**: Build LayoutDTO data structure with all positioned elements

**Process**:
1. **Create RenderableArea objects**:
   - For each cut in `egi.Cut`, create RenderableArea with:
     - `id`, `parent_id`, `rect` (from area_bounds), `is_sheet=False`
   - Create RenderableArea for sheet

2. **Create RenderableVertex objects**:
   - For each vertex in positions, create with:
     - `id`, `parent_area_id`, `pos=(x, y)`

3. **Create RenderableEdgeLabel objects**:
   - For each edge in positions, create with:
     - `id`, `parent_area_id`, `rect`, `label`, `connection_ports`
   - Connection ports calculated from nu mapping and vertex positions

**Output**: LayoutDTO with areas, vertices, edge_labels (ligatures added next)

---

### **STEP 3.5: Area-Aware Ligature Routing**
**Method**: `_area_aware_ligature_routing(egi, dto, style, layout_deltas)`

**Purpose**: Route ligatures from vertices to edge labels respecting area boundaries

**Process**:
1. Build area-aware collision grid:
   - Mark area membership in grid cells
   - Mark vertices and edge labels as obstacles

2. For each vertex-edge connection (from nu mapping):
   
   **Check for Custom Path (User Delta)**:
   - Ligature key: `f"{vertex_id}_{edge_id}_{hook_index}"`
   - If `layout_deltas` has custom_path for this ligature:
     - **Validate custom path**: `_validate_custom_path()`
       - Updates start/end to current positions
       - Checks for collisions with obstacles
       - Checks if path stays within legal corridor
     - If valid, use custom path
     - If invalid, fall back to A* pathfinding

   **Or Calculate Path with A***:
   - Calculate **legal corridor**: `_calculate_legal_corridor(vertex_area, edge_area, hierarchy)`
     - Returns set of area IDs that path can traverse
     - Includes vertex area, edge area, and all areas on path between them
   
   - Use `AreaAwareFinder` (custom A* that respects area membership):
     - Path can only go through legal corridor areas
     - Cannot cross into other nested cuts
   
   - Convert grid path to world coordinates
   - Simplify path (reduce waypoints)
   - **Force exact start/end** (critical fix for quantization errors)

3. Create RenderableLigature with path_points

**Key Constraints**:
- Ligatures MUST stay within legal corridor
- Custom paths validated for area confinement
- **This is where area confinement is ENFORCED for ligatures**

**Output**: DTO with ligatures added

---

### **STEP 4: Apply Aesthetic Styles**
**Method**: `_apply_aesthetic_styles(dto, egi, style)`

**Purpose**: Apply visual styling that doesn't affect layout

**Process**:
1. **Apply Cut Styles**: `_apply_cut_styles(dto, egi, style)`
   - Calculate nesting depths
   - Apply polarity-based fills (even=transparent, odd=shaded)
   - Apply stroke widths, shapes, corner radii
   - Highlight double cuts if enabled

2. **Apply Ligature Styles**: `_apply_ligature_styles(dto, style)`
   - Set line width from style
   - Set color (always black)

3. **Apply Label Styles**: `_apply_label_styles(dto, style)`
   - Set font family, size, color

4. **Generate Annotations**: `_generate_annotations(dto, egi, style)`
   - Vertex variable labels if enabled
   - Double cut highlights if enabled

**Output**: DTO with complete styling information

---

## LayoutDeltas: User Edit Support

### Data Structure
```python
@dataclass
class LayoutDelta:
    element_id: str
    delta_type: str  # 'vertex_position', 'edge_position', 'ligature_path'
    original_position: Optional[Tuple[float, float]]
    new_position: Optional[Tuple[float, float]]
    custom_path: Optional[List[Tuple[float, float]]]  # For ligatures
    nu_mapping_key: Optional[str]  # For ligature identification

@dataclass
class LayoutDeltas:
    deltas: Dict[str, LayoutDelta]
```

### Application Points

#### **Point 1: Graphviz Input (Step 1)**
- Used to create **pinned nodes** in DOT graph
- Syntax: `node_id [pos="x,y!", pin=true]`
- Forces Graphviz to keep node at specified position
- Other nodes arrange around pinned nodes

#### **Point 2: Position Override (Step 1.5)**
- Applied after Graphviz layout
- Directly overwrites x, y coordinates
- **No validation** at this stage

#### **Point 3: Custom Ligature Paths (Step 3.5)**
- Applied during ligature routing
- **Validated** for:
  - Collision with obstacles
  - Area confinement (must stay in legal corridor)
- Invalid paths rejected, fall back to A*

---

## Critical Issues Identified

### **Issue 1: Area Assignment After Positioning**
**Current**: 
- Graphviz positions elements globally
- Area assignment happens after positioning
- Elements can end up positioned outside their logical area

**Problem**: Backwards! Area membership should CONSTRAIN positioning, not be assigned post-facto.

### **Issue 2: No Validation of User Position Deltas**
**Current**:
- User position overrides applied without checking area bounds
- Comment says "rely on DTO-level validation" but that's too late
- Bounding boxes calculated FROM positions, so violations get "locked in"

**Problem**: User edits can violate area confinement

### **Issue 3: Graphviz Sees No Area Boundaries**
**Current**:
- All vertices and edges laid out in single global coordinate space
- No constraints to keep elements within their areas
- Force-directed algorithm optimizes aesthetics, not logical correctness

**Problem**: Fundamental architecture doesn't respect area membership

### **Issue 4: Validation Happens Too Late**
**Current**:
- Area bounds calculated AFTER element positioning
- Bounds expand to fit whatever positions elements have
- No rejection of invalid positions

**Problem**: Can't validate area confinement until areas are sized, but areas are sized by element positions!

---

## What Works Well

### ✅ Ligature Area Confinement
- Legal corridor calculation works correctly
- AreaAwareFinder enforces area boundaries for paths
- Custom path validation ensures user edits respect areas
- This is the ONLY part that properly enforces area confinement!

### ✅ User Edit Support
- Three types of edits supported (vertex, edge, ligature path)
- Pinned nodes create stable anchor points
- Custom paths preserve user aesthetic preferences
- Just needs validation layer for positions

### ✅ Bottom-Up Bounding Boxes
- Correct algorithm for nested area sizing
- Proper padding application
- Handles arbitrary nesting depths

### ✅ Styling System
- Clean separation of layout vs aesthetics
- Polarity-based alternation
- Platform-independent DTO

---

## Required Changes for Area Confinement

### **Principle**: Area Membership Must Be Inviolable

1. **Hierarchical Layout (per-area)**:
   - Run Graphviz WITHIN each area's coordinate space
   - Elements physically cannot escape area bounds
   - Transform local coordinates to global after layout

2. **Validation Layer for User Edits**:
   - Check position deltas against area bounds BEFORE applying
   - Reject positions outside logical parent area
   - Provide feedback to user about constraints

3. **Architectural Guarantee**:
   - Make it IMPOSSIBLE for element to be positioned outside area
   - Not caught and corrected - PREVENTED from happening
   - Type system and architecture enforce correctness

---

## Next Steps

### Option A: Comprehensive Refactoring (Recommended)
- Implement hierarchical per-area layout
- Fixes root cause
- Makes violations architecturally impossible

### Option B: Add Validation Layer (Interim)
- Validate all position changes against area bounds
- Reject invalid positions
- Doesn't fix root cause but prevents violations

### Option C: Both (Safest)
- Add validation immediately
- Refactor to hierarchical layout over time
- Incremental improvement while maintaining safety
