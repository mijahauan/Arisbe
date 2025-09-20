# 🏗️ LAYOUT ENGINE ARCHITECTURE PLAN

**Date:** 2025-09-20  
**Status:** 📋 **ARCHITECTURAL DESIGN**  
**Purpose:** Complete architectural solution for EGI-to-visual rendering with advanced viewing capabilities

---

## 🎯 **EXECUTIVE SUMMARY**

This architecture solves the **fundamental containment and overlapping problem** by introducing a **Layout Engine** as the critical bridge between EGI logical structure and visual representation. The clean separation of concerns enables advanced viewing features (panning, zooming, animation, collapse/expand) while maintaining **perfect logical-visual correspondence**.

---

## 🏛️ **THREE-LAYER ARCHITECTURE**

### **Core Data Flow:**
```
EGI (Logical) → Layout Engine (Spatial Bridge) → Renderer (Visual)
     ↑                                                    ↓
     └── DiagramController (Interaction Bridge) ←─────────┘
```

### **Layer Responsibilities:**

#### **1. EGI Layer (Logical)**
- **Immutable logical structure** - cuts, vertices, edges, containment relationships
- **No spatial information** - pure mathematical relationships
- **Transformation rules** - formal calculus operations only

#### **2. Layout Engine (Spatial Bridge)**
- **Critical missing piece** - translates logical to spatial
- **Enforces containment invariants** - visual must match logical
- **Platform-agnostic output** - works with any renderer
- **Deterministic algorithms** - same EGI always produces same layout

#### **3. Renderer (Visual)**
- **Pure visualization** - no logic, only drawing
- **Platform-specific** - Qt, Web, SVG, etc.
- **Viewport management** - panning, zooming, clipping

#### **4. DiagramController (Interaction Bridge)**
- **Bidirectional translation** - user events ↔ EGI operations
- **Intent interpretation** - visual gestures → logical operations
- **Validation gateway** - ensures all changes are formally valid

---

## 🔒 **CONTAINMENT PROBLEM SOLUTION**

### **How Architecture Prevents Errors:**

#### **Guaranteed Spatial Consistency:**
- **Layout Engine computes cut bounds** that mathematically contain all logical contents
- **No visual element** can appear outside its logical container
- **Overlapping impossible** - algorithm ensures disjoint cuts at same level
- **Spatial arrangement always reflects logical hierarchy**

#### **Validated User Interactions:**
- **DiagramController maps clicks** to exact logical elements
- **All transformations validated** against formal rules before application
- **Invalid operations rejected** - EGI remains unchanged
- **Perfect correspondence** between what user sees and what system knows

#### **Immutable Correctness:**
- **Each EGI change** triggers complete layout recomputation
- **No incremental corruption** - always start from valid logical state
- **Visual always reflects logic** - impossible to diverge
- **Mathematical rigor maintained** throughout interaction cycle

---

## 🎨 **ADVANCED VIEWING CAPABILITIES**

### **Key Principle: Visual Operations Never Touch EGI**

All advanced viewing features are handled by **Layout and Rendering layers** without ever modifying the core EGI model. This ensures **logical integrity** regardless of how user chooses to view the graph.

### **1. Panning and Zooming**

#### **Panning Implementation:**
```python
class DiagramController:
    def handle_pan(self, pan_delta: Vector2D) -> None:
        """
        User pans across canvas - purely visual change
        1. Capture pan event
        2. Send request to Renderer to shift rendering origin
        3. Renderer re-draws with new offset
        4. EGI and Layout remain unchanged
        """
        self.renderer.update_viewport_offset(pan_delta)
```

#### **Zooming Implementation:**
```python
class DiagramController:
    def handle_zoom(self, zoom_factor: float, zoom_center: Point) -> None:
        """
        User zooms in/out - purely visual scaling
        1. Capture zoom event
        2. Adjust renderer scaling factor
        3. Renderer re-draws with new scale
        4. EGI and Layout coordinates unchanged
        """
        self.renderer.update_viewport_scale(zoom_factor, zoom_center)
```

### **2. Transformation Animation**

#### **Diachronic EGI Model:**
```python
@dataclass
class DiachronicEGI:
    """
    EGI as sequence of states - 'moving pictures of thought'
    Each transformation creates new immutable state
    """
    states: List[RelationalGraphWithCuts]
    transformations: List[TransformationRecord]
    current_index: int
    
    def add_transformation(self, rule: TransformationRule, result: RelationalGraphWithCuts) -> 'DiachronicEGI':
        """Add new state via valid transformation"""
        
    def get_current_state(self) -> RelationalGraphWithCuts:
        """Current EGI is last state in sequence"""
        
    def replay_sequence(self, start_index: int = 0, end_index: int = None) -> Iterator[RelationalGraphWithCuts]:
        """Iterate through historical states for animation"""
```

#### **Animation Engine:**
```python
class TransformationAnimationEngine:
    """
    Animates transitions between EGI states
    """
    
    def animate_transformation_sequence(self, diachronic_egi: DiachronicEGI, 
                                      start_index: int, end_index: int) -> Animation:
        """
        1. Get sequence of EGI states
        2. Compute layout for each state
        3. Generate intermediate frames for smooth transitions
        4. Return animation sequence for renderer
        """
        
    def interpolate_layouts(self, layout_from: LayoutResult, 
                          layout_to: LayoutResult, 
                          frame_count: int) -> List[LayoutResult]:
        """Create smooth visual transitions between layouts"""
```

#### **Advantages of Diachronic Model:**
- **Logical Traceability** - Complete record of every transformation
- **Reversibility** - Travel back to any previous state without data loss
- **Consistency** - New states only added via valid transformations
- **Inquiry Modeling** - Perfect reflection of abduction → deduction → induction cycle

### **3. Hierarchical Collapse/Expand**

#### **Visual Hierarchy Management:**
```python
class HierarchicalLayoutEngine(LayoutEngine):
    """
    Extended layout engine supporting collapse/expand
    """
    
    def compute_collapsed_layout(self, egi: RelationalGraphWithCuts, 
                               collapsed_cuts: Set[CutID]) -> LayoutResult:
        """
        1. Identify cuts marked for collapse
        2. Calculate minimal representation (icon, bounding box)
        3. Compute layout with collapsed sections hidden
        4. EGI remains unchanged - purely visual transformation
        """
        
    def expand_collapsed_section(self, layout: LayoutResult, 
                               cut_to_expand: CutID) -> LayoutResult:
        """
        1. Recalculate full layout for expanded section
        2. Integrate with existing layout
        3. Return updated spatial arrangement
        4. EGI unchanged - visual expansion only
        """
```

#### **Collapse/Expand Workflow:**
1. **User Request** - Click collapse/expand control on cut
2. **DiagramController** - Interprets as visual hierarchy change
3. **Layout Engine** - Recalculates spatial arrangement with collapsed/expanded sections
4. **Renderer** - Draws updated layout
5. **EGI Unchanged** - Logical structure preserved throughout

---

## 🔧 **IMPLEMENTATION ARCHITECTURE**

### **Core Components:**

#### **1. Layout Engine Core**
```python
class ArisbeLayoutEngine:
    """
    Core layout algorithms for EGI spatial arrangement
    """
    
    def compute_layout(self, egi: RelationalGraphWithCuts, 
                      view_options: ViewOptions = None) -> LayoutResult:
        """
        Main entry point - translate EGI to spatial primitives
        INVARIANTS ENFORCED:
        - Cut bounds strictly contain all logical contents
        - No overlapping cuts at same nesting level
        - Ligatures respect cut boundaries
        - Spatial reflects logical hierarchy
        """
        
    def compute_cut_hierarchy(self, egi: RelationalGraphWithCuts) -> CutHierarchy:
        """Build nesting tree from EGI area relationships"""
        
    def calculate_cut_bounds(self, hierarchy: CutHierarchy, 
                           content_positions: Dict) -> Dict[CutID, BoundingBox]:
        """Compute minimal bounding boxes guaranteeing containment"""
        
    def route_ligatures(self, egi: RelationalGraphWithCuts, 
                       cut_bounds: Dict) -> Dict[EdgeID, Path]:
        """Route ligature paths respecting cut boundaries"""
        
    def validate_layout(self, layout: LayoutResult, 
                       egi: RelationalGraphWithCuts) -> ValidationResult:
        """Verify spatial arrangement matches logical structure"""
```

#### **2. Layout Result Structure**
```python
@dataclass
class LayoutResult:
    """
    Platform-agnostic spatial arrangement
    Complete spatial information for rendering
    """
    cut_bounds: Dict[CutID, BoundingBox]      # Strict containment boxes
    vertex_positions: Dict[VertexID, Point]   # Predicate/concept positions  
    edge_paths: Dict[EdgeID, Path]            # Ligature routing paths
    nesting_hierarchy: Dict[CutID, List[CutID]]  # Visual nesting order
    viewport_bounds: BoundingBox              # Total diagram bounds
    
    def get_element_at_position(self, position: Point) -> Optional[ElementID]:
        """Map screen coordinates to logical elements"""
        
    def validate_containment(self) -> bool:
        """Verify spatial arrangement matches EGI logical structure"""
```

#### **3. Diagram Controller**
```python
class ArisbeDigramController:
    """
    Bidirectional bridge between user interaction and EGI logic
    """
    
    def __init__(self, layout_engine: LayoutEngine, renderer: Renderer):
        self.layout_engine = layout_engine
        self.renderer = renderer
        self.current_egi: RelationalGraphWithCuts = None
        self.current_layout: LayoutResult = None
    
    def handle_user_event(self, event: UserEvent) -> ControllerResult:
        """
        Main event handling pipeline:
        1. SPATIAL IDENTIFICATION: What visual element was interacted with?
        2. LOGICAL MAPPING: What EGI element does this correspond to?
        3. INTENT INFERENCE: What logical operation is intended?
        4. VALIDATION: Is this operation formally valid?
        5. EGI TRANSFORMATION: Create new EGI if valid
        6. LAYOUT UPDATE: Recompute spatial arrangement
        7. RENDER UPDATE: Display new state
        """
        
    def identify_element_at_position(self, position: Point) -> Optional[ElementID]:
        """Map screen coordinates to logical elements using layout"""
        
    def interpret_user_intent(self, event: UserEvent, element: ElementID) -> OperationIntent:
        """Infer logical operation from user gesture"""
        
    def validate_transformation(self, intent: OperationIntent) -> ValidationResult:
        """Check if intended operation is formally valid"""
        
    def apply_visual_change(self, change: VisualChange) -> None:
        """Handle appearance-only changes (pan, zoom, collapse)"""
        
    def apply_logical_change(self, transformation: TransformationRule) -> None:
        """Handle EGI transformations with full layout recomputation"""
```

#### **4. Platform Renderers**
```python
# Abstract base
class Renderer:
    """Platform-agnostic rendering interface"""
    
    def render_layout(self, layout: LayoutResult, viewport: Viewport) -> RenderedDiagram:
        """Take LayoutResult spatial primitives and draw them"""
        
    def update_viewport(self, pan_offset: Vector2D, zoom_factor: float) -> None:
        """Handle panning and zooming without layout changes"""

# Platform implementations
class QtRenderer(Renderer):
    def render_layout(self, layout: LayoutResult, viewport: Viewport) -> QWidget:
        """Qt-specific rendering implementation"""

class WebRenderer(Renderer):
    def render_layout(self, layout: LayoutResult, viewport: Viewport) -> HTMLElement:
        """Web/Canvas-specific rendering implementation"""

class SVGRenderer(Renderer):
    def render_layout(self, layout: LayoutResult, viewport: Viewport) -> SVGDocument:
        """SVG export rendering implementation"""
```

---

## 🎯 **KEY ARCHITECTURAL BENEFITS**

### **1. Perfect Logical-Visual Correspondence**
- **Impossible** for visual containment to contradict logical containment
- **Guaranteed** that what user sees matches what EGI represents
- **Mathematical rigor** maintained throughout all interactions

### **2. Advanced Viewing Without Logical Corruption**
- **Panning/zooming** handled by renderer - EGI untouched
- **Animation** shows transformation sequences - each state valid
- **Collapse/expand** modifies layout only - logical structure preserved
- **All visual operations** maintain EGI integrity

### **3. Platform Independence**
- **LayoutResult** works with any rendering technology
- **Same layout logic** for Qt, Web, SVG, print, etc.
- **Consistent behavior** across all platforms
- **Future-proof** for new rendering technologies

### **4. Formal Validation**
- **All user interactions** validated against Dau's formal rules
- **No invalid states** possible - system maintains mathematical rigor
- **Complete transformation history** for logical traceability
- **Reversible operations** for exploration and proof development

### **5. Performance Optimization**
- **Layout computation** separate from rendering
- **Incremental updates** possible for appearance-only changes
- **Caching strategies** for complex layouts
- **Viewport culling** for large diagrams

---

## 🚀 **IMPLEMENTATION PHASES**

### **Phase 1: Layout Engine Foundation (4 weeks)**
- Core layout algorithms
- Cut hierarchy computation
- Containment validation
- Basic ligature routing

### **Phase 2: Diagram Controller (3 weeks)**
- Event handling pipeline
- Intent interpretation
- Validation integration
- Visual/logical operation separation

### **Phase 3: Platform Renderers (4 weeks)**
- Qt renderer implementation
- Web renderer implementation
- SVG export renderer
- Viewport management

### **Phase 4: Advanced Viewing Features (6 weeks)**
- Panning and zooming
- Transformation animation
- Hierarchical collapse/expand
- Performance optimization

### **Phase 5: Integration and Testing (3 weeks)**
- Full system integration
- Comprehensive testing
- Performance benchmarking
- Documentation

---

## 🏆 **SUCCESS CRITERIA**

### **Theoretical Compliance:**
- **100% containment accuracy** - visual always matches logical
- **Zero overlapping errors** - impossible by construction
- **Perfect transformation validity** - all operations formally sound
- **Complete diachronic modeling** - full transformation history

### **User Experience:**
- **Intuitive interaction** - natural diagram manipulation
- **Responsive performance** - smooth panning, zooming, animation
- **Clear visual feedback** - immediate validation indicators
- **Reliable operation** - no visual-logical inconsistencies

### **Technical Excellence:**
- **Platform independence** - consistent across all renderers
- **Extensible architecture** - easy to add new viewing features
- **Performance scalability** - handles large, complex EGIs
- **Maintainable code** - clean separation of concerns

---

**This architecture solves the fundamental containment problem while enabling Peirce's vision of "moving pictures of thought" through mathematically rigorous, visually intuitive diagram interaction.**

---

*Saved to coherence framework for recovery and reference during implementation.*
