# New Components API Reference (2025-10-01 to 2025-10-02)

**Purpose**: API documentation for components added after the core 16 protected modules

**Note**: This supplements `ARISBE_CORE_API_REFERENCE.md` which documents the original 16 protected core modules.

---

## 📊 DIAGRAM CONTROL LAYER

### **DiagramController** (`src/diagram_controller.py`)

**Purpose**: Central API for managing EGI state, layout, and transformations in GUI

```python
class DiagramController:
    def __init__(self):
        """Initialize controller with layout engine and command executor."""
    
    def load_egi(
        self, 
        egi: RelationalGraphWithCuts,
        style: Optional[StyleSpecification] = None
    ) -> bool:
        """
        Load an EGI into the controller.
        
        Args:
            egi: The EGI to load
            style: Optional style specification
            
        Returns:
            True if successful
        """
    
    def get_egi_model(self) -> Optional[RelationalGraphWithCuts]:
        """Get the current EGI model."""
    
    def get_renderable_dto(self) -> Optional[LayoutDTO]:
        """
        Get layout DTO for rendering.
        
        Returns:
            LayoutDTO ready for SVG rendering
        """
    
    def apply_formal_rule(
        self,
        rule_name: str,
        selection_ids: List[ElementID],
        target_area: ElementID
    ) -> bool:
        """
        Apply a formal transformation rule.
        
        Args:
            rule_name: 'DC+', 'DC-', 'INS', 'ERA', 'IT+', 'IT-'
            selection_ids: Elements to transform
            target_area: Target area for transformation
            
        Returns:
            True if transformation succeeded
        """
    
    def update_element_position(
        self,
        element_id: ElementID,
        new_position: Tuple[float, float]
    ) -> bool:
        """
        Update element position (aesthetic adjustment).
        
        Args:
            element_id: Element to move
            new_position: (x, y) coordinates
            
        Returns:
            True if position valid and updated
        """
    
    def validate_element_position(
        self,
        element_id: ElementID,
        position: Tuple[float, float]
    ) -> bool:
        """Validate if position is legal for element."""
```

---

### **CommandExecutor** (`src/diagram_controller.py`)

**Purpose**: Undo/redo support for diagram operations

```python
class CommandExecutor:
    def __init__(self, diagram_controller: DiagramController):
        """Initialize with reference to diagram controller."""
    
    def execute(self, command: Command) -> bool:
        """Execute a command and add to history."""
    
    def undo(self) -> bool:
        """Undo last command."""
    
    def redo(self) -> bool:
        """Redo previously undone command."""
    
    def can_undo(self) -> bool:
        """Check if undo is available."""
    
    def can_redo(self) -> bool:
        """Check if redo is available."""
```

---

## 🎨 RENDERING LAYER

### **DefinitiveEGILayoutEngine** (`src/definitive_egi_layout_engine.py`)

**Purpose**: Three-step layout generation (force-directed → bounding boxes → ligature routing)

```python
class DefinitiveEGILayoutEngine:
    def __init__(self, style: Optional[StyleSpecification] = None):
        """Initialize with optional style."""
    
    def generate_layout(
        self,
        egi: RelationalGraphWithCuts,
        layout_deltas: Optional[LayoutDeltas] = None
    ) -> LayoutDTO:
        """
        Generate complete layout for EGI.
        
        Args:
            egi: EGI to layout
            layout_deltas: Optional user aesthetic adjustments
            
        Returns:
            LayoutDTO with positioned elements and routed ligatures
        """
```

---

### **GraphvizSVGRenderer** (`src/graphviz_svg_renderer.py`)

**Purpose**: Render LayoutDTO to SVG

```python
class GraphvizSVGRenderer:
    def render_to_svg(
        self,
        dto: LayoutDTO,
        title: str = "",
        egif: str = ""
    ) -> str:
        """
        Render LayoutDTO to SVG string.
        
        Args:
            dto: Layout information
            title: Optional title
            egif: Optional EGIF for display
            
        Returns:
            SVG as string
        """
    
    def save_svg(
        self,
        dto: LayoutDTO,
        title: str,
        egif: str,
        output_path: str
    ) -> Path:
        """Save SVG to file."""
```

---

### **LayoutDTO** (`src/definitive_egi_layout_engine.py`)

**Purpose**: Data transfer object for rendering information

```python
@dataclass
class LayoutDTO:
    areas: List[RenderableArea]          # Cuts with bounding boxes
    vertices: List[RenderableVertex]     # Vertices with positions
    edge_labels: List[RenderableEdgeLabel]  # Predicates with positions
    ligatures: List[RenderableLigature]  # Routed connection paths
```

---

## 📦 ENTITY STORAGE LAYER

### **GraphEntity** (`src/graph_entity.py`)

**Purpose**: Unified synchronic + diachronic entity model

```python
@dataclass
class GraphEntity:
    metadata: EntityMetadata
    current_egi: RelationalGraphWithCuts
    history: Optional[EGITransformationHistory] = None
    
    @property
    def is_standalone(self) -> bool:
        """Check if entity has no history."""
    
    @property
    def is_historical(self) -> bool:
        """Check if entity has transformation history."""
    
    def get_current_egif(self) -> str:
        """Get EGIF for current state."""
    
    def get_state(self, state_id: str) -> StateSnapshot:
        """Get specific historical state."""
    
    def promote_to_historical(self, description: str = "Initial state"):
        """Convert standalone to historical."""
```

---

### **EntityMetadata** (`src/graph_entity.py`)

**Purpose**: Metadata for graph entities

```python
@dataclass
class EntityMetadata:
    entity_id: str
    entity_type: EntityType  # STANDALONE or HISTORICAL
    name: str
    description: str
    category: EntityCategory  # PEIRCE, SCHOLARS, CANONICAL, etc.
    created: datetime
    last_modified: datetime
    current_state_id: Optional[str]
    total_states: int
    total_transformations: int
    authors: List[str]
    tags: Set[str]
    source_citation: Optional[str]
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
    
    @staticmethod
    def from_dict(data: dict) -> 'EntityMetadata':
        """Deserialize from dictionary."""
```

---

### **EntityStorageManager** (`src/entity_storage.py`)

**Purpose**: Scalable storage with hybrid snapshots + deltas

```python
class EntityStorageManager:
    def __init__(
        self, 
        corpus_root: Path,
        snapshot_interval: int = 10
    ):
        """
        Initialize storage manager.
        
        Args:
            corpus_root: Root directory (e.g., corpus/graphs/)
            snapshot_interval: Full snapshot every N states
        """
    
    def save_entity(self, entity: GraphEntity) -> Path:
        """Save entity to corpus."""
    
    def load_entity(
        self,
        entity_name: str,
        load_full_history: bool = False
    ) -> GraphEntity:
        """
        Load entity from corpus.
        
        Args:
            entity_name: Name of entity
            load_full_history: If True, load all states (default: lazy)
            
        Returns:
            Loaded entity
        """
    
    def list_entities(
        self,
        category: Optional[EntityCategory] = None
    ) -> List[str]:
        """List entities, optionally filtered by category."""
    
    def load_entity_metadata(self, entity_name: str) -> EntityMetadata:
        """Load only metadata (fast for browsing)."""
    
    def create_standalone_entity(
        self,
        name: str,
        egi: RelationalGraphWithCuts,
        description: str = "",
        category: EntityCategory = EntityCategory.USER_CREATED
    ) -> GraphEntity:
        """Create new standalone entity."""
```

---

## 🎨 STYLE SYSTEM

### **StyleLoader** (`src/style_loader.py`)

**Purpose**: Load and manage visual styles

```python
class StyleLoader:
    def load_style(self, style_path: Path) -> StyleSpecification:
        """Load style from JSON file."""
    
    def get_builtin_style(self, style_name: str) -> StyleSpecification:
        """Get built-in style (dau_compliant, peirce_authentic, sowa_compliant)."""
```

---

### **StyleSpecification** (`src/style_loader.py`)

**Purpose**: Complete style definition

```python
@dataclass
class StyleSpecification:
    name: str
    vertex_style: dict       # Fill, stroke, size
    edge_label_style: dict   # Fill, stroke, font
    cut_style: dict          # Stroke, fill, width
    ligature_style: dict     # Stroke, width
    polarity_convention: str # "even_positive" or "dau_standard"
    # ... additional style properties
```

---

## 🖥️ GUI COMPONENTS

### **OrganonMode** (`src/gui_clean/organon/organon_mode.py`)

**Purpose**: Exploration and corpus management mode

```python
class OrganonMode(QWidget):
    edit_in_ergasterion = Signal(object)  # Signal for edit requests
    
    def __init__(
        self,
        diagram_controller: DiagramController,
        parent: Optional[QWidget] = None
    ):
        """Initialize Organon mode with diagram controller."""
```

---

### **CorpusBrowserWidget** (`src/gui_clean/organon/corpus_browser.py`)

**Purpose**: Browse and select entities from corpus

```python
class CorpusBrowserWidget(QWidget):
    entity_selected = Signal(str)  # Emits entity_name
    
    def __init__(self, corpus_path: Path, parent: Optional[QWidget] = None):
        """Initialize browser with corpus path."""
    
    def get_selected_entity_name(self) -> Optional[str]:
        """Get currently selected entity name."""
```

---

### **DiagramCanvas** (`src/gui_clean/common/diagram_canvas.py`)

**Purpose**: Display LayoutDTO as SVG

```python
class DiagramCanvas(QWidget):
    def display_dto(
        self,
        dto: LayoutDTO,
        egi: Optional[RelationalGraphWithCuts] = None
    ):
        """Display a LayoutDTO as SVG."""
    
    def clear(self):
        """Clear the canvas."""
    
    def get_current_dto(self) -> Optional[LayoutDTO]:
        """Get currently displayed LayoutDTO."""
```

---

## 📊 ENUMS AND CONSTANTS

### **EntityType** (`src/graph_entity.py`)

```python
class EntityType(Enum):
    STANDALONE = "standalone"  # Single EGI, no history
    HISTORICAL = "historical"  # Transformation sequence
```

---

### **EntityCategory** (`src/graph_entity.py`)

```python
class EntityCategory(Enum):
    PEIRCE = "peirce"
    SCHOLARS = "scholars"
    CANONICAL = "canonical"
    EPG = "epg"
    THEOREM_PROVING = "theorem_proving"
    DOMAIN_MODELING = "domain_modeling"
    USER_CREATED = "user_created"
    UNIVERSE = "universe"
```

---

## 🧪 TESTING

### **Test Files Added**

**DiagramController Tests** (`tests/test_diagram_controller.py`):
- 11 tests validating controller operations
- Run: `python -m pytest tests/test_diagram_controller.py`

**User Workflow Tests** (`tests/end_to_end/test_user_workflows.py`):
- 8 tests simulating complete user workflows
- Run: `python tests/end_to_end/test_user_workflows.py`

**GUI Smoke Tests** (`tools/test_gui_organon.py`):
- 3 tests validating GUI integration
- Run: `python tools/test_gui_organon.py`

**Total New Tests**: 22 tests (all passing)

---

## 🔗 INTEGRATION POINTS

### **DiagramController ↔ Layout Engine**
```python
controller = DiagramController()
controller.load_egi(egi)
dto = controller.get_renderable_dto()  # Uses DefinitiveEGILayoutEngine
```

### **Layout Engine ↔ Renderer**
```python
layout_engine = DefinitiveEGILayoutEngine()
dto = layout_engine.generate_layout(egi)
renderer = GraphvizSVGRenderer()
svg = renderer.render_to_svg(dto)
```

### **EntityStorage ↔ GUI**
```python
storage = EntityStorageManager("corpus/graphs")
entity = storage.load_entity("graph_name")
controller.load_egi(entity.current_egi)
```

---

## 📝 USAGE PATTERNS

### **Load and Display EGI**
```python
# Load from corpus
storage = EntityStorageManager("corpus/graphs")
entity = storage.load_entity("peirce_cp_4_394_man_mortal")

# Display via controller
controller = DiagramController()
controller.load_egi(entity.current_egi)
dto = controller.get_renderable_dto()

# Render to SVG
renderer = GraphvizSVGRenderer()
svg = renderer.render_to_svg(dto, title=entity.name, egif=entity.get_current_egif())
```

### **Apply Transformation**
```python
# Apply double cut insertion
success = controller.apply_formal_rule(
    rule_name='DC+',
    selection_ids=['v_001', 'e_002'],
    target_area='sheet'
)

# Get updated layout
if success:
    dto = controller.get_renderable_dto()
```

### **Create New Entity**
```python
from egi_core_dau import create_empty_graph, create_vertex

# Create EGI
egi = create_empty_graph()
vertex = create_vertex(label="Socrates", is_generic=False)
egi = egi.with_vertex(vertex)

# Store as entity
storage = EntityStorageManager("corpus/graphs")
entity = storage.create_standalone_entity(
    name="my_graph",
    egi=egi,
    description="Example graph",
    category=EntityCategory.USER_CREATED
)
storage.save_entity(entity)
```

---

## 🎯 SUMMARY

**New Components**: 11 major classes
**New Tests**: 22 tests (all passing)
**Integration**: Full pipeline from storage → controller → layout → rendering → GUI
**Status**: Production-ready (Phase 1 - Organon complete)

**See also**: `ARISBE_CORE_API_REFERENCE.md` for the original 16 protected core modules
