# Dau-Compliant Diagram Transformation Schema

## Overview

This schema defines the systematic transformation of Graphviz spatial primitives into canonical Existential Graph diagrams following Frithjof Dau's formalization of Peirce's conventions. The transformation ensures faithful representation of the underlying EGI while maintaining consistent, predictable visual presentation.

## Core Principles

1. **Logical Fidelity**: Visual representation must preserve all logical relationships in the EGI
2. **Visual Hierarchy**: Heavy elements (identity) dominate light elements (cuts)  
3. **Consistent Conventions**: Same logical structures always render identically
4. **Readability**: Clear distinction between all visual elements
5. **Mathematical Precision**: Professional diagram quality suitable for formal logic

## Transformation Pipeline

```
Graphviz Spatial Primitives → Dau Compliance Transforms → Canonical Visual Elements
```

## Element-Specific Transformation Rules

### 1. Cuts (Contexts)

**Input**: Graphviz cluster boundaries (rectangular)
**Output**: Dau-compliant cut curves

#### Visual Specifications
- **Line Style**: Fine, continuous curve (0.8pt width)
- **Shape**: Smooth oval/ellipse (never rectangular)
- **Color**: Black (#000000)
- **Fill**: None (transparent interior)

#### Transformation Rules
```python
def transform_cut(graphviz_cluster: ClusterPrimitive) -> CutElement:
    # Convert rectangular cluster to smooth oval
    x1, y1, x2, y2 = graphviz_cluster.bounds
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2
    
    # Add padding for visual breathing room
    width = (x2 - x1) + CUT_PADDING
    height = (y2 - y1) + CUT_PADDING
    
    # Ensure minimum aspect ratio for readability
    if width / height < MIN_CUT_ASPECT_RATIO:
        width = height * MIN_CUT_ASPECT_RATIO
    
    return CutElement(
        center=(center_x, center_y),
        semi_major_axis=width / 2,
        semi_minor_axis=height / 2,
        line_width=FINE_LINE_WIDTH,
        style=CutStyle.SMOOTH_OVAL
    )
```

#### Constants
- `CUT_PADDING = 12.0` (minimum clearance around contents)
- `MIN_CUT_ASPECT_RATIO = 1.2` (prevent overly narrow cuts)
- `FINE_LINE_WIDTH = 0.8` (delicate appearance)

### 2. Predicates (Relations)

**Input**: Graphviz node positions + relation names from κ mapping
**Output**: Text labels with invisible hook attachment points

#### Visual Specifications
- **Font**: Times New Roman, 12pt (mathematical standard)
- **Color**: Black (#000000)
- **Style**: Plain text (no boxes, backgrounds, or decorations)
- **Positioning**: Centered on Graphviz node position

#### Hook Point Calculation
```python
def compute_predicate_hooks(predicate_pos: Point, relation_name: str, 
                           vertex_sequence: List[VertexID]) -> List[Point]:
    """Compute invisible hook points on predicate text boundary."""
    text_bounds = measure_text_bounds(relation_name, PREDICATE_FONT)
    
    if len(vertex_sequence) == 1:
        # Unary: single hook at text center
        return [predicate_pos]
    elif len(vertex_sequence) == 2:
        # Binary: left hook for arg 0, right hook for arg 1 (ν order)
        left_hook = Point(text_bounds.left, predicate_pos.y)
        right_hook = Point(text_bounds.right, predicate_pos.y)
        return [left_hook, right_hook]
    else:
        # N-ary: distribute hooks around text perimeter
        return distribute_hooks_around_perimeter(text_bounds, vertex_sequence)
```

### 3. Vertices (Identity Elements)

**Input**: Graphviz node positions + vertex labels + area assignments
**Output**: Identity spots with optional constant names

#### Visual Specifications
- **Spot**: Filled black circle, 4.0pt radius
- **Constant Names**: Times New Roman, 10pt, positioned adjacent to spot
- **Generic Variables**: Spot only (no text label)

#### Position Correction Rules
```python
def transform_vertex_position(graphviz_pos: Point, vertex: Vertex, 
                             egi: RelationalGraphWithCuts) -> Point:
    """Correct vertex position to respect EGI area assignment."""
    logical_area = egi.get_vertex_area(vertex.id)
    
    if not area_contains_point(logical_area, graphviz_pos):
        # Graphviz placed vertex outside its logical area - correct it
        corrected_pos = project_point_into_area(graphviz_pos, logical_area)
        return corrected_pos
    
    return graphviz_pos
```

### 4. Ligatures (Lines of Identity)

**Input**: ν mapping + corrected vertex positions + predicate hook points
**Output**: Heavy continuous lines connecting identity elements

#### Visual Specifications
- **Line Style**: Heavy, continuous (4.0pt width)
- **Color**: Black (#000000)
- **Routing**: Shortest path avoiding text collisions
- **Branching**: Smooth junctions at multi-way connections

#### Connection Rules
```python
def generate_ligature_paths(nu_mapping: Dict[EdgeID, VertexSequence],
                           vertex_positions: Dict[VertexID, Point],
                           predicate_hooks: Dict[EdgeID, List[Point]]) -> List[LigaturePath]:
    """Generate collision-free ligature paths."""
    paths = []
    
    for edge_id, vertex_seq in nu_mapping.items():
        if len(vertex_seq) == 0:
            continue
            
        # Get predicate hook points for this relation
        hooks = predicate_hooks.get(edge_id, [])
        
        # Connect each vertex to its corresponding hook
        for i, vertex_id in enumerate(vertex_seq):
            if i < len(hooks):
                vertex_pos = vertex_positions[vertex_id]
                hook_pos = hooks[i]
                
                # Generate collision-free path
                path = compute_collision_free_path(vertex_pos, hook_pos, 
                                                 avoid_predicates=True)
                paths.append(LigaturePath(
                    start=vertex_pos,
                    end=hook_pos,
                    waypoints=path,
                    line_width=HEAVY_LINE_WIDTH
                ))
    
    return paths
```

### 5. Annotations and Labels

**Input**: Argument positions from ν mapping + special symbols
**Output**: Positioned annotations following Dau conventions

#### Argument Number Labels
- **Font**: Times New Roman, 8pt
- **Position**: 6pt offset from ligature, following line direction
- **Content**: Argument index (0, 1, 2, ...) when needed for clarity

#### Special Annotations
- **Negation Mark**: "−" symbol at cut entrance points
- **Iteration Marks**: Dotted connection lines for copied subgraphs
- **Constant Equality**: "=" symbol for identity assertions

## Implementation Constants

```python
# Line weights (maintaining 5:1 heavy:fine ratio)
HEAVY_LINE_WIDTH = 4.0      # Identity ligatures
FINE_LINE_WIDTH = 0.8       # Cut boundaries
HOOK_LINE_WIDTH = 0.0       # Invisible (hooks are positions, not lines)

# Sizes
VERTEX_SPOT_RADIUS = 4.0    # Identity spots
TEXT_PADDING = 2.0          # Clearance around text
CUT_PADDING = 12.0          # Clearance around cut contents

# Fonts
PREDICATE_FONT = ("Times New Roman", 12)
CONSTANT_FONT = ("Times New Roman", 10)
ANNOTATION_FONT = ("Times New Roman", 8)

# Colors (all black per EG conventions)
PRIMARY_COLOR = (0, 0, 0)   # Black for all elements
SELECTION_COLOR = (0, 100, 200)  # Blue for interactive selection
```

## Quality Assurance Checklist

### Visual Hierarchy
- [ ] Heavy ligatures (4.0pt) visually dominate fine cuts (0.8pt)
- [ ] Identity spots (4.0pt radius) are prominent and unmistakable
- [ ] Text is crisp and readable at standard zoom levels

### Logical Accuracy
- [ ] All vertices positioned within their correct EGI areas
- [ ] Ligature connections respect ν mapping argument order
- [ ] Cut containment matches EGI area assignments
- [ ] No visual elements contradict logical structure

### Dau Compliance
- [ ] Cuts are smooth curves, never rectangles
- [ ] Hooks are invisible positions, not visible lines
- [ ] Identity spots appear in their logical contexts
- [ ] Professional mathematical diagram appearance

### Interactive Readiness
- [ ] All elements have accurate hit-testing boundaries
- [ ] Hover detection matches visual appearance
- [ ] Selection feedback is clear and consistent
- [ ] Drag operations maintain logical constraints

## Usage in Pipeline

```python
def apply_dau_transformations(graphviz_primitives: List[SpatialPrimitive],
                             egi: RelationalGraphWithCuts) -> DauCompliantLayout:
    """Transform Graphviz output to Dau-compliant visual elements."""
    
    # Phase 1: Correct positions for EGI compliance
    corrected_positions = correct_spatial_positions(graphviz_primitives, egi)
    
    # Phase 2: Transform visual elements
    cuts = [transform_cut(p) for p in corrected_positions if p.element_type == "cut"]
    predicates = [transform_predicate(p, egi) for p in corrected_positions if p.element_type == "predicate"]
    vertices = [transform_vertex(p, egi) for p in corrected_positions if p.element_type == "vertex"]
    
    # Phase 3: Generate ligatures from corrected positions
    ligatures = generate_ligature_paths(egi.nu, vertices, predicates)
    
    # Phase 4: Add annotations
    annotations = generate_annotations(egi, vertices, predicates, ligatures)
    
    return DauCompliantLayout(
        cuts=cuts,
        predicates=predicates,
        vertices=vertices,
        ligatures=ligatures,
        annotations=annotations
    )
```

This schema provides the systematic foundation for transforming any Graphviz spatial primitive layout into a canonical, Dau-compliant Existential Graph diagram while preserving all logical relationships and ensuring consistent visual presentation.
