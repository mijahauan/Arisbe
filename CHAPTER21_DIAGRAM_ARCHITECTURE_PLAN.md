# Chapter 21 Diagram Architecture Plan

## Executive Summary

This plan implements Dau's Chapter 21 diagram formalization within Arisbe's three-mode architecture (Organon, Ergasterion, Agon) to realize Peirce's vision of "moving pictures of thought" through dynamic, view-based diagram interaction with full round-trip equivalence across all formats.

## Core Architecture Principles

### 1. EGI-First Transformation Approach
- **All transformations operate on the underlying EGI structure**
- **Display formats (diagrams, EGIF, CGIF, CLIF, FOPL) are views of the EGI**
- **No direct diagram-to-diagram transformations** (avoids syntax/semantic violations)
- **Immediate format synchronization** after EGI modifications

### 2. Dynamic View-Based Rendering
- **Selective rendering** based on user's current focus/activity
- **Hierarchical views** for large EGI structures using R-tree indexing
- **Context-aware display** showing relevant subgraphs for current operation
- **Performance optimization** through lazy loading and viewport culling

### 3. Multi-Modal Subgraph Selection
- **Subgraph-lines** (Dau's dotted rectangles) for topographically contiguous elements
- **Alt-click selection** for non-contiguous logical subgraphs
- **Automatic rearrangement** suggestions when subgraph-lines won't work
- **Visual validation** of subgraph well-formedness in real-time

## Three-Mode Integration

### Organon Mode: Exploration and Organization
**Purpose**: Navigate, search, and organize existing EGI knowledge
**Diagram Features**:
- **Read-only diagram views** with navigation controls
- **Zoom and pan** through large EGI structures
- **Semantic search highlighting** in diagram form
- **Cross-reference visualization** between related EGIs
- **Corpus browsing** with diagram thumbnails

### Ergasterion Mode: Creative Workshop
**Purpose**: Create new facts, hypotheses, abductions, explanations
**Diagram Features**:
- **Interactive diagram construction** with transformation wizards
- **Hypothesis sketching** with visual feedback
- **Abductive reasoning support** through diagram manipulation
- **Template-based creation** for common patterns
- **Real-time validation** of logical well-formedness

### Agon Mode: Formal Evaluation and Testing
**Purpose**: Test hypotheses against domain models, resolve contradictions
**Diagram Features**:
- **Formal proof visualization** with step-by-step transformations
- **Model checking interface** with visual feedback
- **Contradiction detection** and resolution workflows
- **Endoporeutic Game support** with move validation
- **Consensus building tools** for collaborative reasoning

## Technical Implementation Strategy

### Core Components

#### 1. Universal EGI Engine
```python
class UniversalEGIEngine:
    """
    Central engine managing EGI transformations and format synchronization.
    All operations go through this engine to maintain consistency.
    """
    
    def apply_transformation(self, egi: RelationalGraphWithCuts, 
                           rule: TransformationRule, 
                           subgraph: SubgraphSelection) -> TransformationResult
    
    def get_view(self, egi: RelationalGraphWithCuts, 
                view_spec: ViewSpecification) -> ViewResult
    
    def synchronize_formats(self, egi: RelationalGraphWithCuts) -> FormatSyncResult
```

#### 2. Dynamic Diagram Renderer
```python
class DynamicDiagramRenderer:
    """
    Renders EGI views as interactive diagrams with Chapter 21 compliance.
    Supports multiple selection modes and real-time validation.
    """
    
    def render_view(self, view: ViewResult, 
                   interaction_mode: InteractionMode) -> DiagramWidget
    
    def handle_subgraph_selection(self, selection_method: SelectionMethod) -> SubgraphSelection
    
    def validate_transformation_preconditions(self, rule: TransformationRule, 
                                            subgraph: SubgraphSelection) -> ValidationResult
```

#### 3. Transformation Wizard System
```python
class TransformationWizardSystem:
    """
    Step-by-step wizards for each transformation rule across all formats.
    Provides pedagogical support and ensures correct application.
    """
    
    def create_wizard(self, rule: TransformationRule, 
                     format: DisplayFormat) -> TransformationWizard
    
    def execute_guided_transformation(self, wizard: TransformationWizard) -> TransformationResult
```

### Subgraph Selection Implementation

#### Method 1: Subgraph-Lines (Dau Chapter 21)
- **Dotted rectangle drawing** for contiguous element selection
- **Automatic validation** that enclosed elements form valid subgraph
- **Smart snapping** to ensure proper element inclusion
- **Visual feedback** for invalid selections

#### Method 2: Alt-Click Multi-Selection
- **Individual element selection** with modifier keys
- **Logical validation** of selected elements as subgraph
- **Visual highlighting** of selected elements
- **Automatic closure** suggestions for incomplete subgraphs

#### Method 3: Automatic Rearrangement
- **Layout algorithms** to make subgraphs topographically contiguous
- **Preservation of logical structure** during rearrangement
- **User confirmation** before applying layout changes
- **Undo/redo support** for layout modifications

### Transformation Rule Wizards

#### Universal Wizard Framework
Each transformation rule gets format-specific wizards that execute identical underlying EGI operations:

```python
class ERASUREWizard:
    """Erasure rule wizard supporting all formats."""
    
    def diagram_wizard(self) -> DiagramErasureWizard
    def egif_wizard(self) -> EGIFErasureWizard  
    def cgif_wizard(self) -> CGIFErasureWizard
    def clif_wizard(self) -> CLIFErasureWizard
    def fopl_wizard(self) -> FOPLErasureWizard
```

#### Wizard Steps for Complex Rules (e.g., INS)
1. **Precondition Check**: Validate negative context and subgraph closure
2. **Target Selection**: Choose insertion location with visual feedback
3. **Content Specification**: Define what to insert (from templates or construction)
4. **Validation**: Verify resulting EGI will be well-formed
5. **Execution**: Apply transformation to EGI
6. **Format Sync**: Update all display formats
7. **Confirmation**: Show before/after comparison

### Performance and Scalability

#### R-Tree Integration for Large EGIs
- **Spatial indexing** of diagram elements for efficient rendering
- **Level-of-detail rendering** based on zoom level
- **Selective loading** of EGI components based on viewport
- **Background processing** for format synchronization

#### View Management System
```python
class ViewManager:
    """
    Manages dynamic views of large EGI structures.
    Provides context-aware rendering and navigation.
    """
    
    def create_focus_view(self, egi: RelationalGraphWithCuts, 
                         focus_element: ElementID, 
                         context_radius: int) -> FocusView
    
    def create_hierarchical_view(self, egi: RelationalGraphWithCuts, 
                               detail_level: DetailLevel) -> HierarchicalView
    
    def create_transformation_view(self, egi: RelationalGraphWithCuts, 
                                 rule: TransformationRule) -> TransformationView
```

## Round-Trip Equivalence Architecture

### Format Synchronization Engine
```python
class FormatSynchronizer:
    """
    Maintains consistency across all format representations.
    Implements Dau's theoretical equivalence guarantees.
    """
    
    def __init__(self):
        self.egi_engine = UniversalEGIEngine()
        self.translators = {
            'EGIF': EGIFTranslator(),
            'CGIF': CGIFTranslator(), 
            'CLIF': CLIFTranslator(),
            'FOPL': FOPLTranslator(),
            'DIAGRAM': DiagramTranslator()
        }
    
    def synchronize_all_formats(self, source_egi: RelationalGraphWithCuts) -> SyncResult:
        """Update all format views after EGI modification."""
        
    def validate_round_trip_equivalence(self, egi: RelationalGraphWithCuts) -> ValidationResult:
        """Verify theoretical equivalence guarantees are maintained."""
```

### Equivalence Testing Framework
- **Automated round-trip testing** for all format combinations
- **Semantic equivalence verification** using Chapter 19-20 methods
- **Syntactic identity checking** per Theorem 20.4
- **Performance benchmarking** for large EGI structures

## User Interface Design

### Mode-Specific Interfaces

#### Organon Interface
- **EGI Browser** with diagram thumbnails and search
- **Navigation Panel** with hierarchical EGI structure
- **Cross-Reference Viewer** showing related EGIs
- **Format Switcher** for viewing same EGI in different representations

#### Ergasterion Interface  
- **Construction Palette** with EGI building blocks
- **Transformation Toolbar** with rule wizards
- **Hypothesis Workspace** for creative exploration
- **Validation Panel** with real-time feedback

#### Agon Interface
- **Proof Workspace** with step-by-step transformation tracking
- **Model Checker** with visual feedback on satisfiability
- **Game Board** for Endoporeutic Game sessions
- **Consensus Tools** for collaborative reasoning

### Interaction Patterns

#### Subgraph Selection UX
1. **Mode Selection**: Choose between subgraph-line and alt-click selection
2. **Visual Feedback**: Real-time highlighting of valid/invalid selections
3. **Smart Assistance**: Automatic suggestions for completing selections
4. **Validation Display**: Clear indication of subgraph well-formedness

#### Transformation Application UX
1. **Rule Selection**: Visual rule palette with descriptions
2. **Wizard Launch**: Step-by-step guided application
3. **Preview Mode**: Show transformation effects before applying
4. **Confirmation**: Before/after comparison with undo option

## Implementation Phases

### Phase 1: Core EGI Engine (4 weeks)
- Universal EGI transformation engine
- Basic format synchronization
- R-tree integration for performance
- Unit tests for theoretical compliance

### Phase 2: Dynamic Rendering System (6 weeks)  
- View-based diagram renderer
- Subgraph selection methods
- Basic transformation wizards
- Integration with existing GUI framework

### Phase 3: Mode-Specific Features (8 weeks)
- Organon exploration interface
- Ergasterion creation tools
- Agon evaluation interface
- Advanced transformation wizards

### Phase 4: Performance and Polish (4 weeks)
- Large EGI optimization
- User experience refinement
- Comprehensive testing
- Documentation and tutorials

## Success Metrics

### Theoretical Compliance
- **100% round-trip equivalence** across all formats
- **Complete Chapter 21 compliance** for diagram transformations
- **Preservation of Dau's theoretical guarantees**

### User Experience
- **Intuitive subgraph selection** with <2 second learning curve
- **Reliable transformation application** with validation feedback
- **Responsive performance** for EGIs up to 1000+ elements

### Educational Value
- **Step-by-step learning support** through transformation wizards
- **Clear visualization** of logical structure and relationships
- **Pedagogical value** for understanding Peirce's logic

This architecture realizes Peirce's vision of "moving pictures of thought" through a theoretically sound, practically usable system that maintains Dau's formal rigor while providing the intuitive diagram interaction Peirce envisioned.
