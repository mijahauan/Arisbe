# Visual Space Allocation and Entity Conventions

## Overview
This document defines canonical visual conventions for each EG entity type to enable exclusive 2D space assignment and systematic collision avoidance. With well-defined space requirements, z-ordering becomes less complicated and layout management more robust.

## Entity Types and Space Requirements

### 1. **Cuts (Negation Contexts)**
**Visual Convention:**
- Rendered as closed curves (circles, ovals, or rounded rectangles)
- Boundary thickness: 2-3px
- Color: Black outline, transparent interior

**Space Requirements:**
- **Exclusive Area**: Entire interior and boundary region
- **Boundary Buffer**: 10px minimum clearance around outer edge
- **Interior Constraints**: Must contain all assigned elements with padding
- **Collision Rules**: Cannot overlap with other cuts; must maintain hierarchical nesting

**Layout Priority**: Highest (determines overall diagram structure)

### 2. **Ligatures/Lines of Identity (with Constant Names)**
**Visual Convention:**
- Heavy continuous lines (3px thickness)
- Can be straight or curved for flexibility
- Constant names (e.g., "Socrates") rendered directly on the line
- Branching points where >2 connections meet

**Space Requirements:**
- **Line Corridor**: 8px width centered on the line path
- **Branching Point Area**: 12px radius circle at branch points
- **Constant Name Space**: Text bounding box + 4px padding on all sides
- **Collision Rules**: Cannot intersect other ligatures without explicit branching; must respect cut boundaries

**Layout Priority**: Medium (connects predicates, determines connectivity)

### 3. **Predicates (Relation Names)**
**Visual Convention:**
- Text labels (11pt Times font)
- Black text on transparent background
- Optional invisible boundary for hook attachment points

**Space Requirements:**
- **Text Bounding Box**: Exact font metrics + 3px padding
- **Hook Zone**: 5px radius around text boundary for ligature attachment
- **Collision Rules**: Cannot overlap with other predicates or constant names; must maintain readability

**Layout Priority**: Medium-Low (positioned to connect with ligatures)

## Space Allocation Algorithm

### Phase 1: Cut Layout
1. Determine cut hierarchy and nesting requirements
2. Allocate exclusive areas for each cut with proper containment
3. Ensure minimum boundary buffers between sibling cuts

### Phase 2: Ligature Routing
1. Plan ligature paths between predicates and through cuts
2. Reserve line corridors and branching point areas
3. Position constant names on ligature paths with exclusive text space

### Phase 3: Predicate Placement
1. Position predicates to connect with planned ligatures
2. Ensure text bounding boxes don't overlap
3. Verify hook zones are accessible for ligature attachment

### Phase 4: Collision Detection and Resolution
1. Check for any remaining overlaps between entity spaces
2. Adjust positions while maintaining logical constraints
3. Optimize for visual clarity and Dau convention compliance

## Benefits of Exclusive Space Allocation

1. **Predictable Layout**: Each entity has well-defined space requirements
2. **Collision Avoidance**: Systematic prevention of visual overlaps
3. **Scalable Management**: Easy to add new entity types with defined conventions
4. **Publication Quality**: Consistent spacing and appearance for LaTeX/PDF export
5. **Interactive Editing**: Clear hit-testing boundaries for selection and manipulation

## Implementation Notes

- Layout engine should implement space reservation system
- Each entity gets exclusive 2D region during layout phase
- Z-ordering only needed for selection highlights and annotations
- Curved ligatures enable better space utilization than straight lines
- Branching points provide flexible connection topology

## Future Extensions

- **Annotation Overlays**: Temporary visual elements (arity numbers, etc.)
- **Selection Indicators**: Highlight boundaries that don't affect layout
- **Dynamic Resizing**: Entities can expand/contract their space as needed
- **Grid Alignment**: Optional snap-to-grid for precise positioning
