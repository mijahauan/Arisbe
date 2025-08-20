# Area-Based EGDF Architecture Design
## Removing Graphviz Dependency While Preserving Hierarchical Containment

### Core Requirement
Every logical cut `~[ ]` in EGI must correspond to an **exclusive 2D region** on the canvas, with proper hierarchical containment from innermost cuts to the sheet of assertion (level 0).

## 1. EGDF Area Specification

### Canonical Area Model
```python
@dataclass(frozen=True)
class EGDFArea:
    """Canonical 2D area specification for a cut or sheet."""
    id: str                           # Maps to EGI cut ID
    level: int                        # Containment depth (0 = sheet)
    parent_id: Optional[str]          # Parent area ID (None for sheet)
    bounds: Bounds                    # (x_min, y_min, x_max, y_max)
    shape: AreaShape                  # Canonical geometry
    available_space: Polygon          # Shapely polygon for element placement
    reserved_space: List[Polygon]     # Space occupied by child cuts
    
@dataclass(frozen=True)
class AreaShape:
    """Geometric specification for area boundary."""
    type: str                         # "rectangle", "oval", "rounded_rect", "freeform"
    parameters: Dict[str, float]      # Shape-specific parameters
    boundary_points: List[Coordinate] # Exact boundary for rendering
```

### Hierarchical Containment Invariants
1. **Exclusive Space**: `available_space ∩ reserved_space = ∅` for each area
2. **Proper Containment**: Child areas must be fully contained within parent
3. **Non-Overlap**: Sibling areas must not overlap
4. **Complete Coverage**: Union of all areas = total canvas space

## 2. EGI → EGDF Area Generation

### Area Layout Algorithm (No Graphviz)
```python
class AreaBasedLayoutEngine:
    """Generate hierarchical 2D areas from EGI cut structure."""
    
    def generate_areas_from_egi(self, egi: RelationalGraphWithCuts) -> List[EGDFArea]:
        """
        Core algorithm:
        1. Build containment tree from EGI cuts
        2. Assign 2D space using recursive subdivision
        3. Generate Shapely polygons for each area
        4. Validate containment invariants
        """
        
        # Step 1: Extract containment hierarchy
        containment_tree = self._build_containment_tree(egi)
        
        # Step 2: Assign canvas space recursively
        canvas_bounds = (0, 0, 800, 600)  # Default canvas
        sheet_area = self._create_sheet_area(canvas_bounds)
        
        areas = [sheet_area]
        self._assign_child_areas(containment_tree.root, sheet_area, areas)
        
        # Step 3: Validate invariants
        self._validate_area_hierarchy(areas)
        
        return areas
    
    def _assign_child_areas(self, node: CutNode, parent_area: EGDFArea, areas: List[EGDFArea]):
        """Recursively assign 2D space to child cuts."""
        if not node.children:
            return
            
        # Calculate space needed for child cuts
        child_space_requirements = self._calculate_space_requirements(node.children)
        
        # Use packing algorithm to position children within parent
        child_positions = self._pack_rectangles_in_area(
            parent_area.available_space, 
            child_space_requirements
        )
        
        # Create child areas
        for child_node, position in zip(node.children, child_positions):
            child_area = self._create_child_area(child_node, parent_area, position)
            areas.append(child_area)
            
            # Recurse for grandchildren
            self._assign_child_areas(child_node, child_area, areas)
```

### Space Allocation Strategy
1. **Top-Down**: Start with sheet (level 0), recursively subdivide
2. **Rectangle Packing**: Use 2D bin packing for optimal space utilization
3. **Margin Preservation**: Ensure visual separation between cuts
4. **Content-Aware**: Size areas based on contained elements

## 3. Element Placement Within Areas

### Area-Constrained Positioning
```python
class AreaConstrainedPlacer:
    """Place vertices and predicates within their assigned areas."""
    
    def place_elements_in_areas(self, egi: RelationalGraphWithCuts, areas: List[EGDFArea]) -> List[SpatialPrimitive]:
        """
        For each element in EGI:
        1. Determine containing area from EGI containment
        2. Find optimal position within area.available_space
        3. Update area.reserved_space with element bounds
        4. Generate ligatures respecting area boundaries
        """
        
        primitives = []
        area_map = {area.id: area for area in areas}
        
        # Place vertices first
        for vertex in egi.vertices:
            containing_area = self._find_containing_area(vertex, egi, area_map)
            position = self._find_optimal_vertex_position(vertex, containing_area, egi)
            vertex_primitive = VertexPrimitive(vertex.id, position)
            primitives.append(vertex_primitive)
            
        # Place predicates
        for predicate in egi.predicates:
            containing_area = self._find_containing_area(predicate, egi, area_map)
            position = self._find_optimal_predicate_position(predicate, containing_area, egi)
            predicate_primitive = PredicatePrimitive(predicate.id, position, predicate.name)
            primitives.append(predicate_primitive)
            
        # Generate ligatures (identity lines)
        ligature_primitives = self._generate_area_aware_ligatures(egi, primitives, areas)
        primitives.extend(ligature_primitives)
        
        return primitives
```

## 4. EGDF Canonical Representation

### Complete EGDF Document Structure
```python
@dataclass
class EGDFDocument:
    """Complete EGDF with area-based containment."""
    metadata: EGDFMetadata
    canonical_egi: Dict[str, Any]           # Preserved EGI structure
    area_hierarchy: List[EGDFArea]          # 2D containment specification
    spatial_primitives: List[SpatialPrimitive]  # Positioned elements
    style_theme: StyleTheme                 # Rendering parameters
    canvas_settings: CanvasSettings         # Canvas dimensions
    
    # Validation methods
    def validate_containment_invariants(self) -> bool:
        """Ensure all containment invariants are satisfied."""
        
    def validate_egi_correspondence(self) -> bool:
        """Ensure 1:1 correspondence between EGI cuts and EGDF areas."""
```

### Area Boundary Encoding
```python
# Example: Nested cuts with precise boundaries
area_hierarchy = [
    EGDFArea(
        id="sheet",
        level=0,
        parent_id=None,
        bounds=(0, 0, 800, 600),
        shape=AreaShape(type="rectangle", parameters={}, boundary_points=[(0,0), (800,0), (800,600), (0,600)]),
        available_space=Polygon([(50, 50), (750, 50), (750, 550), (50, 550)]),  # Margin from canvas edge
        reserved_space=[Polygon(...)]  # Space for child cuts
    ),
    EGDFArea(
        id="cut_1",
        level=1,
        parent_id="sheet",
        bounds=(100, 100, 300, 200),
        shape=AreaShape(type="oval", parameters={"rx": 100, "ry": 50}, boundary_points=[...]),
        available_space=Polygon([...]),  # Interior space for elements
        reserved_space=[]  # No child cuts
    )
]
```

## 5. Stylistic Deltas for Rendering Variants

### Canonical + Delta Architecture
```python
@dataclass
class StyleDelta:
    """Modifications to canonical rendering for different visual styles."""
    name: str                           # "peirce_handdrawn", "modern_clean", "academic"
    area_style_overrides: Dict[str, Any]    # Cut rendering modifications
    element_style_overrides: Dict[str, Any] # Vertex/predicate modifications
    ligature_style_overrides: Dict[str, Any] # Identity line modifications
    
# Example: Peirce hand-drawn style
peirce_style = StyleDelta(
    name="peirce_handdrawn",
    area_style_overrides={
        "cut_line_style": "hand_drawn_wobble",
        "cut_line_width": 2.0,
        "cut_fill": "none",
        "corner_rounding": 0.0  # Sharp corners like Peirce
    },
    element_style_overrides={
        "vertex_style": "small_dot",
        "predicate_font": "serif_handwritten",
        "predicate_size": 14
    },
    ligature_style_overrides={
        "line_style": "thick_hand_drawn",
        "line_width": 3.0,
        "connection_style": "organic_curves"  # Not rectilinear
    }
)
```

### Renderer Architecture
```python
class EGDFRenderer:
    """Base renderer that respects canonical areas + applies style deltas."""
    
    def render(self, egdf_doc: EGDFDocument, style_delta: Optional[StyleDelta] = None):
        """
        1. Use egdf_doc.area_hierarchy for exact containment
        2. Apply style_delta modifications for visual appearance
        3. Ensure logical structure is preserved regardless of style
        """
        
        # Canonical areas define WHERE things go
        areas = egdf_doc.area_hierarchy
        
        # Style delta defines HOW things look
        style = self._merge_style(egdf_doc.style_theme, style_delta)
        
        # Render with guaranteed containment
        return self._render_with_areas_and_style(areas, egdf_doc.spatial_primitives, style)
```

## 6. Implementation Strategy

### Phase 1: Core Area Engine
1. **Implement `AreaBasedLayoutEngine`** - Generate areas from EGI cuts
2. **Implement `AreaConstrainedPlacer`** - Position elements within areas
3. **Integrate with existing Shapely** - Use `ShapelyAreaManager` for geometry

### Phase 2: EGDF Integration
1. **Extend `EGDFDocument`** - Add `area_hierarchy` field
2. **Update `EGDFParser`** - Parse/serialize area specifications
3. **Validate round-trip** - Ensure EGI ↔ EGDF ↔ EGI preserves containment

### Phase 3: Qt Renderer Update
1. **Update `EGGraphicsSceneRenderer`** - Use areas for positioning
2. **Remove Graphviz dependency** - Pure area-based layout
3. **Add style delta support** - Multiple rendering styles

## Benefits of This Architecture

1. **Platform Independence**: No Graphviz dependency
2. **Precise Containment**: Guaranteed hierarchical 2D regions
3. **Style Flexibility**: Canonical geometry + visual deltas
4. **Mathematical Rigor**: Shapely-based geometric validation
5. **Extensibility**: Support for custom area shapes and styles

This design ensures that every `~[ ]` in the logic has an unambiguous 2D representation while allowing for diverse visual styles from modern clean to Peirce's hand-drawn aesthetic.
