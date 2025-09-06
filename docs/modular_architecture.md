# Arisbe Modular Drawing System Architecture

## Overview

The Arisbe drawing system has been successfully refactored into a modular architecture with clear separation of concerns. This document outlines the new architecture, its components, and future extensibility plans.

## Architecture Layers

### 1. Model Layer (Pure EGI Logic)
**Location**: `src/egi_core_dau.py`, `src/egi_system.py`
- **Purpose**: Pure logical EGI structures without GUI dependencies
- **Components**:
  - `RelationalGraphWithCuts`: Core EGI data structure
  - `AlphabetDAU`: Alphabet definitions for constants, relations, functions
  - `EGISystem`: EGI manipulation and validation logic
- **Characteristics**: No Qt dependencies, purely functional

### 2. Coordination Layer (EGI-Spatial Translation)
**Location**: `src/diagram_coordinator.py`, `src/egi_spatial_correspondence.py`
- **Purpose**: Maintains precise correspondence between logical EGI and spatial diagram
- **Key Components**:
  - `DiagramCoordinator`: Central orchestrator for all diagram operations
  - `SpatialCorrespondenceEngine`: Handles logical↔spatial mappings
  - `drawing_to_egi_adapter`: Converts spatial diagrams to EGI structures
- **Responsibilities**:
  - Logical-spatial correspondence during user interactions
  - Exclusive positioning and containment rules
  - Mode-based validation (Composition vs Practice)
  - EGDF serialization/deserialization

### 3. Interaction Layer (User Input Handling)
**Location**: `src/interaction_handler.py`
- **Purpose**: Clean separation between Qt events and business logic
- **Components**:
  - `InteractionHandler`: Translates Qt events to logical operations
  - Mode management (Select, Create Vertex/Predicate/Cut/Ligature)
  - Drag-and-drop coordination
- **Characteristics**: Delegates all business logic to DiagramCoordinator

### 4. Rendering Layer (Graphics Display)
**Location**: `src/shared_diagram_renderer.py`, `src/styling/style_manager.py`
- **Purpose**: Pure graphics rendering without business logic
- **Components**:
  - `SharedDiagramRenderer`: Renders EGI structures as Qt graphics
  - `StyleManager`: Manages visual themes and styling
- **Characteristics**: Stateless rendering based on EGI data

### 5. UI Wiring Layer (Qt Integration)
**Location**: `tools/drawing_editor_refactored.py`
- **Purpose**: Thin Qt UI coordination layer
- **Components**:
  - `RefactoredDrawingEditor`: Main window and UI setup
  - `ModularDrawingView`: Graphics view with delegated interactions
  - Toolbar, dock widgets, file operations
- **Characteristics**: Minimal business logic, pure UI coordination

## Key Design Principles

### EGI-Centricity
- All operations maintain logical EGI structure as the source of truth
- Spatial representation is derived from logical structure
- Round-trip EGDF serialization preserves logical meaning

### User-Defined Layout
- Users control spatial positioning directly
- No automatic layout algorithms (initially)
- Spatial constraints respect logical requirements

### Mode-Based Validation
- **Composition Mode**: Syntax constraints only
- **Practice Mode**: Syntax + semantic constraints + transformations
- Extensible constraint system via `controller/constraint_engine.py`

### Modular Extensibility
- Clear interfaces between layers
- New features can be added without affecting other layers
- Future capabilities designed into architecture

## Existing Component Integration

### Successfully Integrated
- ✅ `RelationalGraphWithCuts` and `EGISystem` (Model layer)
- ✅ `constraint_engine.py` (Validation)
- ✅ `style_manager.py` (Styling)
- ✅ `SharedDiagramRenderer` (Rendering)
- ✅ `egi_spatial_correspondence.py` (Coordination core)
- ✅ `drawing_to_egi_adapter.py` (Spatial→Logical translation)

### Refactored Components
- ✅ `DrawingEditor` → Thin UI wiring layer
- ✅ Interaction handling → Separate `InteractionHandler`
- ✅ Business logic → `DiagramCoordinator`

## Current Capabilities

### Core Features
- ✅ EGDF loading and rendering
- ✅ Element creation (vertices, predicates, cuts, ligatures)
- ✅ Drag-and-drop movement with logical consistency
- ✅ Mode-based interaction (Select, Create modes)
- ✅ Validation mode switching (Composition/Practice)
- ✅ EGDF save/load operations
- ✅ Real-time EGI structure display

### Logical-Spatial Correspondence
- ✅ Spatial cuts ↔ Logical negation (area containment)
- ✅ Spatial juxtaposition ↔ Logical conjunction
- ✅ Spatial ligatures ↔ Nu mappings (predicate-vertex connections)
- ✅ Exclusive positioning rules
- ✅ Chapter 16 ligature constraints

## Future Roadmap

### Phase 1: Core Stabilization (Current)
- ✅ Modular architecture implementation
- ✅ Basic EGDF round-trip functionality
- 🔄 Ligature geometry integration for user suggestions
- 🔄 Enhanced constraint validation

### Phase 2: Advanced Interaction
- 📋 Sub-graph selection and manipulation
- 📋 Multi-element operations (copy, paste, group)
- 📋 Undo/redo system
- 📋 Enhanced ligature creation (two-click, hand-drawn)

### Phase 3: Export and Rendering
- 📋 PNG/PDF export integration
- 📋 LaTeX/TikZ export for publication
- 📋 Print layout and scaling
- 📋 High-resolution rendering

### Phase 4: Automatic Layout
- 📋 Ligature geometry for automatic suggestions
- 📋 Force-directed layout algorithms
- 📋 Constraint-based positioning
- 📋 Layout optimization

### Phase 5: Practice Mode Extensions
- 📋 Logical transformation rules
- 📋 Step-by-step proof construction
- 📋 Semantic validation and suggestions
- 📋 Educational scaffolding

## Technical Benefits

### Maintainability
- Clear separation of concerns
- Minimal coupling between layers
- Easy to test individual components
- Predictable data flow

### Extensibility
- New interaction modes can be added easily
- Rendering can be enhanced without affecting logic
- Export formats can be added modularly
- Validation rules can be extended

### Robustness
- Changes to one layer don't break others
- Logical consistency is always maintained
- Error handling is localized
- State management is centralized

### Performance
- Efficient rendering through separation
- Minimal redundant calculations
- Optimized ligature geometry handling
- Scalable to large diagrams

## Migration Strategy

### Completed
- ✅ Extracted coordination layer using existing correspondence engine
- ✅ Separated interaction handling from business logic
- ✅ Refactored DrawingEditor to thin UI layer
- ✅ Preserved all existing functionality

### Ongoing
- 🔄 Enhanced ligature geometry integration
- 🔄 Advanced constraint validation
- 🔄 Export system integration

### Future
- 📋 Legacy code removal after full validation
- 📋 Performance optimization
- 📋 Advanced feature development

## Conclusion

The modular architecture successfully preserves all existing functionality while establishing a robust foundation for future development. The clear separation between logical EGI structure and spatial representation ensures that the system can evolve to support advanced features while maintaining the precision required for logical diagram manipulation.

The architecture supports both current needs (diagram authoring and editing) and future capabilities (automatic layout, logical transformations, advanced export) through its extensible design and clean interfaces.
