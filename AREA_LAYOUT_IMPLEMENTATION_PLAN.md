# Area-Based Layout Implementation Plan
## Removing Graphviz Dependency - Incremental Approach

## Phase 1: Core Area Layout Engine (Week 1)

### 1.1 Extend Existing Data Structures
```python
# Add to existing egdf_dau_canonical.py
@dataclass
class AreaInfo:
    """Temporary area structure for initial implementation."""
    cut_id: str
    level: int
    parent_id: Optional[str]
    bounds: Bounds
    available_polygon: Polygon  # From Shapely
    
class AreaBasedLayoutEngine:
    """New layout engine that generates areas from EGI cuts."""
    
    def __init__(self):
        from shapely_area_manager import ShapelyAreaManager
        self.area_manager = ShapelyAreaManager()
    
    def generate_layout_from_egi(self, egi: RelationalGraphWithCuts) -> List[SpatialPrimitive]:
        """Main entry point - replaces Graphviz layout."""
        # 1. Build area hierarchy from EGI cuts
        areas = self._build_area_hierarchy(egi)
        
        # 2. Place elements within areas
        primitives = self._place_elements_in_areas(egi, areas)
        
        return primitives
```

### 1.2 Integration Points
- **Modify `egdf_dau_canonical.py`**: Add `AreaBasedLayoutEngine` class
- **Update `arisbe_eg_clean.py`**: Switch from Graphviz to area-based layout
- **Leverage `shapely_area_manager.py`**: Use existing Shapely integration

### 1.3 Test Cases
- **Simple relation**: `[Human Socrates]` (no cuts)
- **Single cut**: `~[Human Socrates]` (one negation)
- **Nested cuts**: `~~[Human Socrates]` (double negation)
- **Sibling cuts**: `~[Human Socrates] ~[Mortal Plato]` (parallel negations)

## Phase 2: Element Placement Algorithm (Week 2)

### 2.1 Area-Constrained Positioning
```python
class AreaConstrainedPlacer:
    """Place vertices and predicates within their assigned areas."""
    
    def place_elements_in_areas(self, egi: RelationalGraphWithCuts, areas: List[AreaInfo]) -> List[SpatialPrimitive]:
        """Core placement algorithm."""
        primitives = []
        
        # Group elements by containing area
        element_groups = self._group_elements_by_area(egi, areas)
        
        # Place each group within its area
        for area, elements in element_groups.items():
            area_primitives = self._place_elements_in_single_area(area, elements, egi)
            primitives.extend(area_primitives)
        
        # Generate ligatures that respect area boundaries
        ligatures = self._generate_area_aware_ligatures(egi, primitives, areas)
        primitives.extend(ligatures)
        
        return primitives
```

### 2.2 Placement Strategies
- **Force-directed within areas**: Use simplified physics simulation
- **Grid-based placement**: Systematic positioning for predictable results
- **Centroid-based**: Place elements near area centers, spread outward

## Phase 3: EGDF Integration (Week 3)

### 3.1 Extend Existing EGDF Format
```python
# Modify existing EGDFDocument in egdf_parser.py
@dataclass
class EGDFDocument:
    metadata: EGDFMetadata
    canonical_egi: Dict[str, Any]
    visual_layout: Dict[str, Any]  # Add 'area_hierarchy' field here
    format: str = "EGDF"
    version: str = "1.1.0"  # Increment version
    export_settings: Optional[Dict[str, Any]] = None
    
# visual_layout structure:
visual_layout = {
    "spatial_primitives": [...],  # Existing
    "area_hierarchy": [           # New
        {
            "cut_id": "sheet",
            "level": 0,
            "parent_id": None,
            "bounds": [0, 0, 800, 600],
            "available_space": [[50, 50], [750, 50], [750, 550], [50, 550]]
        },
        # ... more areas
    ]
}
```

### 3.2 Serialization Updates
- **JSON**: Existing `egdf_to_json()` handles new fields automatically
- **YAML**: Existing `egdf_to_yaml()` handles new fields automatically
- **Validation**: Update schema to include `area_hierarchy` field

## Phase 4: Qt Renderer Integration (Week 4)

### 4.1 Update Graphics Scene Renderer
```python
# Modify eg_graphics_scene_renderer.py
class EGGraphicsSceneRenderer:
    def render_egdf(self, egdf_primitives: List[SpatialPrimitive]) -> QGraphicsScene:
        """Updated to use area information if available."""
        scene = QGraphicsScene()
        
        # Check if EGDF includes area hierarchy
        if hasattr(egdf_primitives, 'area_hierarchy'):
            # Use area-aware rendering
            self._render_with_areas(scene, egdf_primitives)
        else:
            # Fallback to existing rendering
            self._render_without_areas(scene, egdf_primitives)
        
        return scene
```

### 4.2 Area Visualization (Optional)
- **Debug mode**: Show area boundaries as dashed lines
- **Interactive mode**: Highlight areas on hover
- **Constraint visualization**: Show available vs reserved space

## Implementation Priority

### **Start Here**: Core Area Layout Engine
1. **Create `AreaBasedLayoutEngine`** in `src/egdf_dau_canonical.py`
2. **Implement basic area hierarchy** from EGI cuts
3. **Test with simple examples** (no cuts, single cut, nested cuts)
4. **Integrate into main application** (`arisbe_eg_clean.py`)

### **Success Criteria for Phase 1**
- ✅ Application runs without Graphviz dependency
- ✅ Simple EGI examples render correctly
- ✅ Cut boundaries are properly defined
- ✅ Elements stay within their logical areas

### **Deferred Until Later**
- **Complete EGDF specification**: Wait for implementation learnings
- **Advanced serialization**: Current JSON/YAML support is sufficient
- **Style deltas**: Focus on canonical rendering first
- **Complex area shapes**: Start with rectangles, add ovals later

## Benefits of This Approach

1. **Incremental progress**: Working system at each phase
2. **Risk mitigation**: Test area model before finalizing specification
3. **Leverage existing code**: Build on `ShapelyAreaManager` and current EGDF
4. **Clear validation**: Real examples prove the approach works
5. **Flexible architecture**: Can refine EGDF based on implementation experience

This plan gets you to a working area-based layout system quickly while keeping options open for EGDF refinement based on real-world usage.
