# EGI ↔ Spatial Correspondence System

## Overview

This document describes the core correspondence architecture that solves the fundamental challenge of correlating EGI logical structure with spatial visual representation, incorporating Dau's Chapter 16 ligature handling principles.

## Architecture Components

### 1. Logical Layer (EGI)
- **Vertices**: Mathematical points with identity relationships
- **Edges**: Predicates connecting vertices via ν mapping
- **Cuts**: Negation boundaries defining areas
- **Relations**: Mapping from edges to relation names
- **Areas**: Containment structure defining logical positioning

### 2. Correspondence Layer
- **Bidirectional Mapping**: EGI ↔ Spatial element correspondence
- **Chapter 16 Constraints**: Mathematical validation of ligature transformations
- **Ligature Geometry**: Spatial representation of identity networks
- **Branching Points**: Interactive connection points with positioning freedom

### 3. Spatial Layer
- **Bounds**: Rectangular spatial positioning for all elements
- **Containment**: Spatial enforcement of logical area membership
- **Routing**: Connection paths between related elements
- **Collision Avoidance**: Non-overlapping element positioning

### 4. Styling Integration Point
- **Reserved Location**: `_apply_styling_system()` method in correspondence engine
- **Future Expansion**: Line thickness, colors, fonts, cut borders
- **Separation of Concerns**: Visual styling independent of logical correspondence

## Chapter 16 Integration

### Lemma 16.1: Moving Branches Along Ligatures
```python
# Branching points can move freely along ligature without changing meaning
success = correspondence_engine.handle_branching_point_drag(
    ligature_id="ligature_1", 
    branch_point_index=0, 
    new_position=0.8  # 0.0 to 1.0 along ligature path
)
```

### Lemma 16.2: Extending/Restricting Ligatures
```python
# Add vertices to ligature with identity links
correspondence_engine.apply_ligature_transformation(
    LigatureTransformationType.EXTEND_LIGATURE,
    ligature_id="ligature_1",
    new_vertex_id="v_new"
)

# Remove vertices from ligature
correspondence_engine.apply_ligature_transformation(
    LigatureTransformationType.RESTRICT_LIGATURE,
    ligature_id="ligature_1", 
    remove_vertex_id="v_old"
)
```

### Lemma 16.3: Ligature Retraction
```python
# Retract ligature to single vertex when all vertices have same label
correspondence_engine.apply_ligature_transformation(
    LigatureTransformationType.RETRACT_LIGATURE,
    ligature_id="ligature_1",
    target_vertex="v_target"
)
```

### Definition 16.4: General Ligature Rearrangement
```python
# Rearrange ligature topology while preserving meaning
correspondence_engine.apply_ligature_transformation(
    LigatureTransformationType.REARRANGE_LIGATURE,
    ligature_id="ligature_1",
    new_geometry=new_ligature_geometry
)
```

## Key Data Structures

### SpatialElement
```python
@dataclass
class SpatialElement:
    element_id: str
    element_type: str  # 'vertex', 'edge', 'cut', 'ligature'
    logical_area: str
    spatial_bounds: SpatialBounds
    ligature_geometry: Optional[LigatureGeometry] = None
    is_branching_point: bool = False
    parent_ligature: Optional[str] = None
```

### LigatureGeometry
```python
@dataclass 
class LigatureGeometry:
    ligature_id: str
    vertices: List[str]  # Vertex IDs in this ligature
    spatial_path: List[Tuple[float, float]]  # Continuous path waypoints
    branching_points: List[BranchingPoint]
```

### BranchingPoint
```python
@dataclass
class BranchingPoint:
    ligature_id: str
    position_on_ligature: float  # 0.0 to 1.0 along ligature path
    spatial_position: Tuple[float, float]
    connected_predicates: List[str] = field(default_factory=list)
    constant_label: Optional[str] = None
```

## EGDF Integration

The correspondence system integrates with the EGDF projection to produce complete visual documents:

```python
egdf_document = {
    'egi_structure': {
        'vertices': [...],
        'edges': [...], 
        'cuts': [...],
        'relations': {...},
        'connections': {...},
        'areas': {...}
    },
    'visual_layout': {
        'spatial_primitives': [...],
        'ligature_data': [...],
        'styling_integration_point': 'RESERVED_FOR_FUTURE_STYLING',
        'chapter16_compliant': True
    },
    'correspondence_mapping': {
        'egi_to_spatial': {...},
        'spatial_to_egi': {...},
        'ligature_mappings': {...},
        'area_mappings': {...}
    },
    'interaction_capabilities': {
        'branching_point_dragging': True,
        'ligature_rearrangement': True,
        'chapter16_transformations': [...]
    }
}
```

## Validation Results

### Test Coverage
- ✅ Basic EGI → spatial correspondence generation
- ✅ Chapter 16 Lemma 16.1: Branch movement validation
- ✅ Chapter 16 ligature transformations (extend, restrict, retract, rearrange)
- ✅ Styling integration point reservation
- ✅ EGDF projection integration
- ✅ Bidirectional correspondence mapping

### Performance Characteristics
- **Ligature Generation**: O(V + E) where V=vertices, E=edges
- **Spatial Layout**: O(n²) constraint satisfaction with n=elements
- **Chapter 16 Validation**: O(1) for individual transformations
- **Correspondence Lookup**: O(1) bidirectional mapping

## Usage Examples

### Creating Correspondence Engine
```python
from egi_spatial_correspondence import create_spatial_correspondence_engine

# Create from existing EGI
correspondence_engine = create_spatial_correspondence_engine(egi)

# Generate spatial layout
layout = correspondence_engine.generate_spatial_layout()
```

### Interactive Manipulation
```python
# Move branching point along ligature
success = correspondence_engine.handle_branching_point_drag(
    ligature_id="ligature_1",
    branch_point_index=0, 
    new_position=0.5
)

# Apply Chapter 16 transformation
success = correspondence_engine.apply_ligature_transformation(
    LigatureTransformationType.MOVE_BRANCH,
    ligature_id="ligature_1",
    branch_index=0,
    new_position=0.7
)
```

### EGDF Document Generation
```python
from egi_system import EGDFProjection

projection = EGDFProjection()
egdf_doc = projection.generate(egi)

# Access Chapter 16 features
ligature_data = egdf_doc['visual_layout']['ligature_data']
interaction_caps = egdf_doc['interaction_capabilities']
```

## Future Development

### Styling System Integration
The styling integration point is reserved at:
- **Location**: `SpatialCorrespondenceEngine._apply_styling_system()`
- **Purpose**: Apply visual styling without affecting logical correspondence
- **Scope**: Line thickness, colors, fonts, cut borders, ligature rendering

### Advanced Features
- **Curved Ligatures**: Smooth path generation with obstacle avoidance
- **Dynamic Layout**: Real-time constraint satisfaction during interaction
- **Multi-user Collaboration**: Separate logical content from visual preferences
- **Performance Optimization**: Spatial indexing for large diagrams

## Mathematical Foundation

This system implements the formal correspondence between:

1. **Dau's EGI Definition 12.1**: 6+1 component relational graphs with cuts
2. **Chapter 16 Ligature Theory**: Formal transformations preserving meaning
3. **Spatial Constraint System**: Visual representation with mathematical rigor

The correspondence maintains **bidirectional consistency** where:
- Every EGI logical relationship has a spatial representation
- Every spatial manipulation preserves EGI mathematical constraints
- Chapter 16 transformations are validated before application

This achieves the core goal of **reliable EGI → graph-replica mapping** with the same mathematical rigor as EGIF linear forms, enabling interactive visual manipulation while preserving formal correctness.
