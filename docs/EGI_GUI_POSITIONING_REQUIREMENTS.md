# EGI-GUI Positioning Requirements and Operation Sequencing

## Current Positioning Requirements

### Fundamental Spatial Principles

1. **Universal Element Spatial Exclusivity**
   - No two elements can occupy the same spatial location within any area
   - Minimum separation distances: 8pt between elements, 15pt between vertices
   - As fundamental as cut nesting and non-overlap rules

2. **Cut Boundary Integrity**
   - Elements cannot cross cut boundaries (except in composition mode)
   - Cut rectangles cannot overlap with sibling cuts
   - Child elements must remain contained within parent cuts

3. **Dau Visual Conventions**
   - Vertex spots: 2.5pt radius, minimal bounds
   - Heavy lines: 4pt width, rectilinear routing, rounded caps/joins
   - Predicate attachment: Cardinal point hooks (N/S/E/W) based on approach direction
   - Cut sizing: Minimal margins (8pt internal, 2pt external padding)

4. **Connected Element Selection System**
   - Visual highlighting shows logical dependencies between elements
   - Selection reveals all connected vertices, predicates, and ligatures
   - Cut-crossing ligatures highlighted to show identity transcendence
   - Deletion impact preview shows orphaned elements and logical consequences

### Element Positioning Logic

#### Predicates
- **Size Calculation**: Dynamic based on text length (char_width × length + padding)
- **Placement**: Grid-based with collision avoidance
- **Boundaries**: Tight text boundaries with 1pt padding for attachment points
- **Hooks**: Cardinal direction attachment based on ligature approach angle

#### Vertices
- **Optimal Positioning**: Equidistant from connected predicates (2-ary) or centroid (n-ary)
- **Constraint Validation**: Must stay within logical area bounds
- **Exclusion Avoidance**: Cannot overlap with child cuts or other elements
- **Fallback**: Grid positioning when optimal placement conflicts

#### Ligatures (Heavy Lines)
- **Routing**: Rectilinear L-shaped paths with minimal 90-degree turns
- **Attachment**: Cardinal points on predicate boundaries with minimal padding
- **Constraint**: Cannot cross cut boundaries (alters logical meaning)
- **Path Selection**: Horizontal-first or vertical-first based on distance ratios

#### Cuts
- **Sizing**: Liberal initial sizing with 30% width, 20% height overestimate
- **Positioning**: Hierarchical placement respecting parent-child relationships
- **Resizing**: Dynamic with proportional child element repositioning
- **Clearance**: 8pt internal margin, 2pt external boundary padding

## Interactive Operations and Logical Consequences

### Connected Element Selection System (IMPLEMENTED)

#### Selection Highlighting Colors
- **Red**: Primary selected element (thick border, transparent fill)
- **Blue**: Connected elements (vertices/predicates linked via ligatures)
- **Orange**: Affected ligatures (heavy lines showing identity relationships)
- **Yellow**: Cut boundaries crossed by ligatures (identity transcendence)
- **Light Red**: Deletion impact preview (orphaned elements)

#### Selection Behavior by Element Type

##### Predicate Selection
- **Primary Selection**: Highlight selected predicate in red
- **Connected Vertices**: Show all vertices connected via ligatures in blue
- **Connected Predicates**: Show predicates sharing vertices (branching ligatures) in blue
- **Affected Ligatures**: Highlight all heavy lines connected to predicate in orange
- **Cut Crossings**: Show cuts that ligatures cross in yellow
- **Deletion Preview**: Right-click shows orphaned vertices and broken connections

##### Vertex Selection
- **Primary Selection**: Highlight selected vertex in red
- **Connected Predicates**: Show all predicates connected via ligatures in blue
- **Connected Vertices**: Show vertices sharing predicates (identity chains) in blue
- **Affected Ligatures**: Highlight all heavy lines connected to vertex in orange
- **Cut Crossings**: Show cuts that ligatures cross in yellow
- **Deletion Preview**: Right-click shows orphaned predicates and arity changes

##### Ligature Selection
- **Primary Selection**: Highlight selected ligature in red
- **Endpoint Elements**: Show both connected vertex and predicate in blue
- **Related Connections**: Show other ligatures sharing endpoints in orange
- **Cut Crossings**: Show cuts that this ligature crosses in yellow

##### Cut Selection
- **Primary Selection**: Highlight selected cut in red
- **Contained Elements**: Show all predicates and vertices within cut in blue
- **Internal Ligatures**: Show ligatures connecting elements within cut in orange
- **Boundary Crossings**: Show ligatures crossing this cut boundary in yellow

#### Cut-Crossing Ligature Deletion Rules (IMPLEMENTED)
- **Identity Transcendence**: Ligatures represent identity across logical contexts
- **Vertex Deletion**: Connected predicates become 0-ary or reduce arity
- **Predicate Deletion**: Connected vertices become free-standing identity lines
- **Logical Coherence**: All operations preserve valid EGI structure
- **Impact Analysis**: Preview shows all affected elements before deletion

### Operation Categories

#### 1. Purely Geometric Operations (No EGI Logic Impact)
- **Element repositioning** within same logical area
- **Cut resizing** without boundary crossings
- **Visual styling** changes (colors, line weights)
- **Annotation** positioning and visibility

#### 2. Logically Neutral Operations (Spatial Impact Only)
- **Area expansion** to accommodate new elements
- **Element spacing** adjustments for clarity
- **Ligature rerouting** around obstacles (same endpoints)

#### 3. Logically Significant Operations (EGI Model Changes)
- **Predicate deletion** (affects connected vertices and ligature meaning)
- **Element movement** across cut boundaries (changes logical scope)
- **Cut creation/deletion** (changes logical structure)
- **Ligature endpoint** changes (changes relational connections)

## Operation Sequencing Requirements

### Pre-Operation Validation Sequence
1. **Spatial Constraint Check**: Validate against geometric constraints
2. **Logical Constraint Check**: Validate against EGI rules (if applicable)
3. **Mode Validation**: Check if operation is allowed in current mode
4. **Impact Analysis**: Identify all affected elements

### Operation Execution Sequence
1. **Area Dimension Updates**: Resize areas first if needed
2. **Element Position Updates**: Reposition elements within updated areas
3. **Ligature Rerouting**: Update heavy line paths after positions are set
4. **Visual Feedback**: Update selection indicators and visual cues
5. **EGI Model Sync**: Update underlying logical model (if changed)

### Post-Operation Validation Sequence
1. **Constraint Verification**: Ensure all constraints remain satisfied
2. **Visual Consistency**: Verify GUI accurately represents EGI state
3. **Undo State**: Capture state for potential rollback

## Mode-Dependent Behavior

### Normal Mode
- **Strict Boundaries**: Elements cannot cross cut boundaries
- **Conservative Validation**: All spatial and logical constraints enforced
- **Visual Feedback**: Clear indication of constraint violations

### Composition Mode
- **Relaxed Boundaries**: Elements can cross cuts (with logical consequences)
- **Permissive Movement**: Allow operations that change EGI meaning
- **Enhanced Feedback**: Show logical impact of boundary crossings

## Critical Operation Sequences

### Predicate Deletion
1. **Selection Phase**: Show predicate + connected vertices + ligatures
2. **Impact Analysis**: Determine effect on remaining vertices and EGI structure
3. **Validation**: Check if deletion creates invalid EGI state
4. **Area Adjustment**: Calculate new area dimensions without predicate
5. **Element Repositioning**: Reposition remaining elements in smaller area
6. **Ligature Updates**: Remove or reroute affected heavy lines
7. **EGI Model Update**: Update logical structure

### Predicate Movement
1. **Selection Phase**: Show predicate + connected elements
2. **Path Validation**: Check new position against spatial constraints
3. **Boundary Check**: Validate cut boundary crossings based on mode
4. **Ligature Planning**: Calculate new heavy line paths
5. **Collision Detection**: Ensure new ligature paths don't cross cuts
6. **Position Update**: Move predicate to validated position
7. **Ligature Rerouting**: Update all connected heavy lines
8. **EGI Model Update**: Update logical structure if boundaries crossed

### Cut Resizing
1. **Selection Phase**: Show cut + all contained elements
2. **Constraint Validation**: Ensure resize doesn't violate sibling cut boundaries
3. **Child Element Analysis**: Identify all elements requiring repositioning
4. **Proportional Repositioning**: Maintain relative positions of child elements
5. **Ligature Impact**: Identify ligatures requiring rerouting
6. **Boundary Validation**: Ensure no ligatures cross new cut boundaries
7. **Visual Update**: Render new cut size and element positions

## Drawing Action Priority

### Rendering Order
1. **Cut Areas**: Draw cut rectangles first (background)
2. **Element Positioning**: Position all elements within areas
3. **Ligature Routing**: Draw heavy lines after positions are finalized
4. **Annotations**: Add arity markers and labels last (overlay)
5. **Selection Indicators**: Apply selection highlighting (top layer)

### Update Triggers
- **Area changes** → Trigger element repositioning → Trigger ligature rerouting
- **Element movement** → Trigger ligature rerouting → Trigger visual updates
- **Selection changes** → Trigger connected element highlighting
- **Mode changes** → Trigger constraint validation updates

This sequencing ensures the GUI maintains an accurate replica of the EGI while providing intuitive interactive editing capabilities.
