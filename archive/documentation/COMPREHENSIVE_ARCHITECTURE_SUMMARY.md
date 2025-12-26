# Arisbe Comprehensive Architecture Summary

## Executive Summary

Arisbe is a sophisticated system for creating, editing, and analyzing Existential Graph diagrams following Frithjof Dau's mathematical formalism. The architecture implements a multi-layered approach separating logical meaning (EGI), canonical layout (EGDF), and user presentation customizations through a complex network of coordinated components.

## 1. DTO Model Architecture

### EGI State DTO (`src/egi_dto.py`)
**Purpose**: Canonical data transfer format for all inter-module communication

**Core Components**:
- `EGIStateDTO`: Central data structure containing:
  - `vertices: Dict[str, VertexDTO]` - O(1) lookup by ID
  - `edges: Dict[str, EdgeDTO]` - Predicates/relations
  - `cuts: Dict[str, CutDTO]` - Negation contexts
  - `ligatures: Dict[str, LigatureDTO]` - Lines of identity
  - `nu_mapping: Dict[str, Tuple[str, ...]]` - Edge to vertex sequences
  - `area_mapping: Dict[str, Set[str]]` - Spatial containment

**Element DTOs**:
- `VertexDTO`: ID, spatial info, label, generic/constant flag
- `EdgeDTO`: ID, relation name, incident vertices, text dimensions
- `CutDTO`: ID, parent cut, spatial bounds
- `LigatureDTO`: Edge ID, vertex connections, path geometry

**Validation**: Post-init validation ensures consistency between elements and mappings

### Diagram Data Contract (`src/diagram_data_contract.py`)
**Purpose**: Standardized data structures for diagram elements and positioning

**Key Classes**:
- `ElementPosition`: Canonical x,y positioning with Qt conversion
- `ElementSize`: Width/height with Qt rect conversion
- `VertexElement`, `PredicateElement`, `CutElement`: Typed element representations
- `DiagramState`: Complete diagram state container

## 2. Constraint Model Architecture

### Constraint Engine (`src/controller/constraint_engine.py`)
**Purpose**: Platform-agnostic validation engine operating on DTOs

**Constraint Categories**:

#### Syntactic Constraints (Always Enforced):
- **Cut Nesting**: Cuts must be properly nested or disjoint, no line overlaps
- **Spatial Overlap Prevention**: Element extents cannot traverse each other
- **Ligature Bridge Validation**: Non-planar crossing detection

#### Semantic Constraints (Practice Mode Only):
- **Area Containment**: Vertices/predicates must be within assigned areas
- **Logical Structure Preservation**: EGI relationships maintained
- **Ligature Area Constraints**: Single-area ligatures cannot cross cuts

**Validation Functions**:
- `validate_syntactic_constraints()`: Returns (ok, msg, info)
- `validate_semantic_constraints()`: Returns (ok, msg, info)
- Element bounds calculation with padding
- Path intersection detection

## 3. Style Model Architecture

### Style Manager (`src/styling/style_manager.py`)
**Purpose**: Cross-platform styling system with semantic tokens

**Architecture**:
- JSON theme files with semantic style tokens
- `StyleQuery` class for (type, role, state) lookups
- Platform adapters translate tokens to graphics primitives
- Environment variable support for theme selection

**Style Resolution**:
- Hierarchical token resolution
- Safe defaults for missing themes
- Support for Qt and TikZ rendering backends

## 4. EGI Model Architecture

### EGI Core Dau (`src/egi_core_dau.py`)
**Purpose**: Dau-compliant Existential Graph Instance implementation

**Formal Structure** (Dau's 6+1 Components):
1. `V`: Finite set of vertices (generic/constant)
2. `E`: Finite set of edges (relations)
3. `ν`: Mapping from edges to vertex sequences
4. `⊤`: Sheet of assertion (single element)
5. `Cut`: Finite set of cuts (negation contexts)
6. `area`: Mapping defining containment
7. `rel`: Mapping from edges to relation names

**Additional Components**:
- `AlphabetDAU`: Optional alphabet (C, F, R, ar)
- `rho`: Vertex to constant name mapping
- Derived mappings for efficiency

**Validation**: Post-init validation of Dau's formal constraints

## 5. Coordination Model Architecture

### Diagram Coordinator (`src/diagram_coordinator.py`)
**Purpose**: Central coordination layer for EGI-Spatial correspondence

**Key Responsibilities**:
- Maintain logical-spatial correspondence during interactions
- Enforce exclusive positioning and containment rules
- Coordinate between EGI model, spatial renderer, and constraint validation
- Support Composition Mode (syntax only) and Practice Mode (syntax + semantics)

**Core State Management**:
- `egi_state: EGIStateDTO` - Single source of truth
- `diagram_state: DiagramDataContract` - Visual representation
- `current_drawing_schema` - Compatibility layer
- `region_manager` - Spatial region management
- `coordinate_negotiator` - Platform-independent positioning

**Element Creation Methods**:
- `create_vertex(position, area_id)` - Logical-spatial vertex creation
- `create_predicate(name, position, area_id)` - Predicate with correspondence
- `create_cut(position, width, height)` - Cut with containment

## 6. Serialization Model Architecture

### EGDF Specification (`docs/egdf_spec_v0.md`)
**Purpose**: Platform-independent document format separating logic from presentation

**Document Structure**:
```json
{
  "egdf": { "version": "0.1", "generator": "arisbe", "created": "..." },
  "egi_ref": { "hash": "sha256:...", "inline": { /* EGI content */ } },
  "layout": { /* device-independent geometry */ },
  "styles": { /* declarative stylesheet */ },
  "deltas": [ /* ordered user tweaks */ ]
}
```

**Authoring Models**:
- **Modular**: Separate EGI, styles, per-user layout deltas
- **Bundled**: Single file with inlined content for portability

**Key Features**:
- Content hashing for integrity validation
- Style mapping between different presentations
- Delta-only documents for collaborative workflows

### EGDF Parser (`src/egdf_parser.py`)
**Purpose**: Parse and validate EGDF documents

## 7. Interaction Model Architecture

### Interaction Handler (`src/interaction_handler.py`)
**Purpose**: User input handling layer delegating to DiagramCoordinator

**Key Features**:
- Clean separation between Qt events and business logic
- Drag state tracking for element movement
- Callback system for UI updates
- Graphics item to element ID mapping

**Event Handling**:
- Mouse press/move/release delegation
- Keyboard event processing
- Context menu coordination

## 8. GUI Model Architecture

### Arisbe Triad Architecture (Classical Greek Terminology)

#### 1. ORGANON (Ὄργανον) - "Tool/Instrument"
**Location**: `src/organon/main_window.py`
**Purpose**: Knowledge tomos management and graph origination

**Core Functions**:
- Linear form parsing (EGIF, CGIF, CLIF) into canonical EGI
- Graph origination for new diagram development
- Tomos storage in JSON/YAML formats
- Metadata management and editing
- Read-only visualization of EG diagrams
- Universe of Discourse views ("moving pictures of thought")

**Components**:
- `CorpusPanel`: Navigate graph collections
- `InfoPanel`: Display graph metadata
- `LinearFormsPanel`: Show EGIF/CLIF representations
- `DiagramViewer`: Visual graph rendering

#### 2. ERGASTERION (Ἐργαστήριον) - "Workshop/Laboratory"
**Location**: `tools/drawing_editor_refactored.py`, `src/diagram_coordinator.py`
**Purpose**: Interactive diagram authoring and transformation practice

**Core Functions**:
- **Composition Mode**: Diagram authoring with syntax constraints only
- **Practice Mode**: Transformation rule application with semantic validation
- EGI-Spatial correspondence maintenance
- Intelligent ligature geometry suggestions
- EGDF serialization for Organon storage

**Architecture**:
- `RefactoredDrawingEditor`: Main workshop interface
- `ModularDrawingView`: Graphics view delegating to InteractionHandler
- Integration with DiagramCoordinator for logical consistency
- Toolbar with mode controls and validation toggles

#### 3. AGON (Ἀγών) - "Contest/Struggle"
**Location**: Future development
**Purpose**: Logical evaluation through the Endoporeutic Game

**Core Functions**:
- Deductive game engine modeling logical reasoning
- Umpire function for meta-level evaluation
- Hypothesis management and competing contexts
- Formal validation of logical transformations

### Shared Diagram Renderer (`src/shared_diagram_renderer.py`)
**Purpose**: Consistent rendering across Ergasterion and Organon

**Key Features**:
- Unified ligature rendering with text boundary anchoring
- Interactive elements with proper event handling
- Constraint violation messaging
- Annotation system support
- Scene management with incremental updates

## 9. User Workflow: Diagram Composition Process

### Starting a New Diagram

1. **Application Launch**: User opens Arisbe main window
2. **Mode Selection**: Choose between Bullpen, Browser, or Game tabs
3. **Bullpen Entry**: Select Warmup (with EGI target) or Practice (free-form)
4. **Canvas Initialization**: 
   - DiagramCoordinator creates empty EGI state
   - SharedDiagramRenderer prepares Qt scene
   - InteractionHandler enables user input
   - Constraint engine set to Composition mode (syntactic only)

### Diagram Composition Process

#### Element Creation:
1. **User Action**: Right-click on canvas
2. **Context Menu**: System shows "Add Vertex/Predicate/Cut" options
3. **Coordinate Negotiation**: View coordinates → Scene coordinates → Logical coordinates
4. **Element Creation**: DiagramCoordinator.create_*() methods:
   - Generate unique ID
   - Validate position (if Practice mode)
   - Update EGI state and drawing schema
   - Update diagram state for rendering
5. **Visual Update**: SharedDiagramRenderer creates Qt graphics items
6. **Constraint Validation**: Engine validates syntactic constraints

#### Element Interaction:
1. **Selection**: User clicks element, InteractionHandler tracks selection
2. **Movement**: Drag operations update both logical and visual positions
3. **Editing**: Context menus allow text editing, property changes
4. **Constraint Checking**: Real-time validation during operations

#### Mode Transitions:
- **Composition → Practice**: Enable semantic constraints, area containment
- **Practice → Composition**: Disable semantic validation, allow free positioning

### Completing the Diagram

#### Saving Process:
1. **User Action**: File → Save or Save to Corpus
2. **EGDF Generation**: DiagramCoordinator.save_to_egdf():
   - Serialize current EGI state
   - Capture layout information
   - Include style references
   - Generate content hashes
3. **File Output**: Write modular or bundled EGDF format
4. **Tomos Integration**: Update tomos index if saving to collection

#### Handoff to Organon:
1. **Export Package**: Create GraphHandoffPackage with EGDF data
2. **Browser Launch**: Switch to Organon tab with loaded graph
3. **Verification**: Display linear forms (EGIF/CLIF) for validation

## 10. Key Architectural Principles

### Separation of Concerns:
- **Logical Layer**: EGI mathematical relationships
- **Spatial Layer**: Visual positioning and layout
- **Presentation Layer**: User customizations and styling

### Data Flow Architecture:
- **Single Source of Truth**: EGI state in DiagramCoordinator
- **Unidirectional Updates**: EGI → Diagram State → Visual Rendering
- **Event Delegation**: UI Events → InteractionHandler → DiagramCoordinator

### Platform Independence:
- **DTO-based Communication**: No GUI dependencies in core logic
- **Coordinate Negotiation**: Abstract positioning system
- **Style Abstraction**: Platform-agnostic styling tokens

### Extensibility:
- **Plugin Architecture**: Style managers, constraint engines
- **Modular Components**: Independent, testable modules
- **Format Evolution**: Versioned EGDF specification

## 11. Spatial-Logical Correspondence Principles

### Core Correspondence Rules
**The spatial representation of a graph corresponds precisely with the logic of a graph:**

- **Negation ↔ Cut Areas**: Graph logic asserts negation through areas enclosed by cuts. Every pixel resides either unenclosed (level 0) or enclosed by cuts in particular areas. Cuts can be juxtaposed or nested but cannot overlap.

- **Conjunction ↔ Juxtaposition**: Graph logic asserts conjunction through juxtaposition in an area. Positions are exclusive (visually and syntactically distinct) but arbitrary to the logic.

- **Existence ↔ Vertices**: Graph logic asserts existence through vertices. Ligatures can connect vertices to predicates in any area (ligatures can cross cuts).

- **Quantification ↔ Area Nesting**: Graph logic quantifies entity existence by vertex's outermost area:
  - **Universal quantification** ("for all x"): Outermost position in oddly-enclosed area
  - **Individual quantification** ("there exists x"): Outermost position in evenly-enclosed area

### Z-Order and Spatial Exclusion
- **Z-order depth = cut nesting level = spatial exclusion hierarchy**
- Deeper cuts (higher z-order) carve out forbidden zones from shallower cuts
- Child cut boundaries define areas where parent elements cannot appear
- Layout engine must treat child cuts as "holes" in parent positioning space

## 12. Selection Schemes and Interaction Models

### Composition Mode (Semantic Constraints OFF)
**Purpose**: Compose graphs matching target meaning through free element manipulation

**Selection Behaviors**:
- **Predicates**: Highlight + repositioning, right-click for name editing, arity assignment, copy, delete
- **Vertices**: Highlight + repositioning, extend ligature from spot/branch points (iteration), right-click for name editing, ligature deletion, vertex+ligature deletion
- **Cuts**: Highlight with resize handles, right-click for deletion
- **Empty Areas**: Right-click to add predicate, vertex, or cut

**Constraints**: Syntactic only (cut nesting, spatial overlap prevention)

### Practice Mode (Semantic Constraints ON)
**Purpose**: Apply EG transformation rules while preserving meaning

**Selection Behaviors**:
- **Empty Sites in Odd Areas**: Insert new subgraph (INS rule)
- **Subgraphs in Even Areas**: Erase selected subgraph (ERA rule)
- **Any Subgraph**: Iterate into same/nested areas (IT+ rule)
- **Duplicate Subgraphs**: De-iterate if identical exists in same/enclosing areas (IT- rule)
- **Any Area/Subgraph**: Surround with double cut (DC+ rule)
- **Double Cuts**: Remove double negation (DC- rule)

**Multi-Selection**: Click-drag dashed selection or alt/cmd-click for proper subgraph groups

### Proper Subgraph Definition (Per Dau)
- Any individual element
- Cut + complete context (everything nested within)
- Connected components respecting area boundaries
- Groups satisfying logical closure properties

## 13. Transformation Workflow Architecture

### Logical Transformation Rules
**All transformations create new diagrams, preserving original:**

- **DC+ (Double Cut Addition)**: Enclose subgraph/empty area with double cut anywhere
- **DC- (Double Cut Removal)**: Remove double cut anywhere, adjust enclosure levels
- **INS (Insertion)**: Insert subgraph in negatively-enclosed area
- **ERA (Erasure)**: Erase subgraph from positively-enclosed area
- **IT+ (Iteration)**: Copy subgraph into same area or nested areas
- **IT- (De-iteration)**: Remove subgraph if identical exists in same/enclosing areas

### Workflow Implementation Requirements
1. **Subgraph Selection**: User selects elements forming proper subgraph
2. **Rule Application**: System validates rule applicability for current context
3. **Diagram Creation**: Generate new diagram with transformation applied
4. **Layout Adjustment**: Resize areas and reposition elements as needed
5. **Enclosure Level Update**: Recalculate nesting levels for affected elements

## 14. Ligature System Architecture

### Connection Rules (Per Dau Chapter 16)
- **Ligatures as Single Entities**: Each ligature represents one continuous line, not segments
- **Branch Points**: Features ON the line, not connection points between segments
- **Vertex Extensions**: Ligatures are extensions of vertex spots
- **Predicate Connections**: Connect through padding to unique "hook" positions
- **Area Rules**: 
  - Same-area ligatures CANNOT collide with cuts (must curve around)
  - Cross-area ligatures CAN cross cut boundaries

### Bridge System
- **Ligature-Ligature Crossings**: Bridges needed for non-planar graphs (K5+)
- **Cut Crossings**: NO bridge needed (cuts are boundaries, not spatial objects)
- **Visual Indication**: Bridge shows one ligature passes "over" another

### Transformation Principles
- **Meaning-Preserving Operations**: Rearrange, extend, retract to vertex, split vertex
- **Identity Preservation**: Shape/length changes don't affect meaning
- **Breaking Rules**: Breaking ligature creates new vertex for separated segment

## 15. Current Implementation Status

### Working Components:
- EGI core data structures and validation
- EGDF parsing and serialization
- Style management system
- Constraint validation engine
- Basic Qt rendering pipeline

### Integration Issues:
- DiagramCoordinator element creation not producing visible results
- SharedDiagramRenderer missing render_current_state method
- Coordinate negotiation system not fully connected
- Complex architecture with too many integration points

### Architectural Debt:
- Multiple overlapping data schemas (drawing_schema, diagram_state, egi_state)
- Incomplete separation between logical and visual layers
- Missing error handling and recovery mechanisms
- Performance concerns with complex validation pipeline

This architecture represents a sophisticated attempt to create a mathematically rigorous diagram editor while maintaining separation of concerns and platform independence. However, the complexity has led to integration challenges that prevent the system from functioning as intended.
