# Arisbe GUI Framework Architecture

## Overview

The Arisbe GUI application framework provides a complete interface for existential graph reasoning built around the proven 100% transformation success core logic. The application implements three sub-applications following the classical division of logical work:

- **Organon**: Graph browsing and exploration
- **Ergasterion**: Graph construction and editing  
- **Agon**: Formal reasoning environment

## Architecture Components

### Core Foundation

**TransformationSequenceEngine Integration**
- 100% transformation success rate with all 6 EG rules
- Complete transformation history tracking
- Immutable EGI transformation pipeline
- Persistent EGI validity at each step

**Dau-Compliant EGI Structure**
- Proper 6+1 component RelationalGraphWithCuts
- Frozen data structures for immutability
- Hierarchical index for efficient operations
- Full compliance with Dau's formal definitions

### Application Structure

```
ArisbeMainWindow
├── MenuBar (File, Help)
├── TabWidget
│   ├── OrganonTab (Browse)
│   ├── ErgasterionTab (Build)  
│   └── AgonTab (Reason)
├── StatusBar
└── ApplicationState (shared context)
```

### Sub-Applications

#### 1. Organon (Browse Tab)

**Purpose**: Explore and browse existing EGI corpus

**Components**:
- `QTreeWidget` for EGI corpus navigation
- `LinearFormDisplay` for EGI structure visualization
- EGI selection and loading system
- Cross-tab communication via signals

**Features**:
- Tree-based corpus browser
- Real-time EGI structure display
- Sample EGI loading (Classical Syllogism, Blank Sheet)
- Linear form representation of graph components

#### 2. Ergasterion (Build Tab)

**Purpose**: Graph construction and editing workspace

**Components**:
- Transformation rule buttons (DC+, INS, IT+, IT-, ERA, DC-)
- `LinearFormDisplay` for workspace state
- `TransformationSequenceEngine` integration
- Blank sheet initialization

**Features**:
- Rule-governed graph construction
- Step-by-step transformation application
- Live workspace state updates
- Complete transformation history tracking

#### 3. Agon (Reason Tab)

**Purpose**: Formal reasoning and proof environment

**Components**:
- Classical syllogism proof demonstration
- `LinearFormDisplay` for proof sequences
- Integration with test framework
- Endoporeutic Game foundation

**Features**:
- 9-step modus ponens demonstration
- 100% transformation success validation
- Complete proof history display
- Foundation for formal game implementation

## Data Flow Architecture

### ApplicationState Management

```python
@dataclass
class ApplicationState:
    current_egi: Optional[RelationalGraphWithCuts] = None
    transformation_engine: Optional[TransformationSequenceEngine] = None
    active_sequence_id: Optional[str] = None
```

**Shared State**:
- Current EGI across all tabs
- Active transformation engine instance
- Sequence tracking for workspace operations

### Linear Form Display System

**LinearFormDisplay Widget**:
- Unified display component across all tabs
- EGI structure visualization in text format
- Transformation sequence history display
- Statistics and validation results

**Display Capabilities**:
- Vertex, edge, and cut counts
- Area containment structure
- Transformation step details
- Success rate statistics

## Integration Points

### Core Logic Integration

**TransformationSequenceEngine**:
- Direct integration with GUI controls
- Real-time transformation application
- Complete history and provenance tracking
- Validation result display

**EGI Structure**:
- Proper Dau 6+1 component handling
- Immutable transformation pipeline
- Hierarchical index integration
- Format synchronization support

### Cross-Tab Communication

**Signal System**:
- `egi_selected` signal from Organon to other tabs
- Shared ApplicationState for context
- Status bar updates across operations
- Menu action coordination

## Progressive Enhancement Path

### Current State: Linear Forms
- Text-based EGI representation
- Complete structural information
- Transformation rule application
- History and validation display

### Future: Interactive Diagrams
- Visual EGI manipulation
- Drag-and-drop transformation
- Real-time diagram updates
- Spatial layout integration

## Technical Implementation

### Dependencies
- PyQt6 for GUI framework
- Core Arisbe transformation engine
- Dau-compliant EGI structures
- frozendict for immutable data

### File Structure
```
src/gui/
├── arisbe_main_app.py          # Main application framework
├── organon/                    # Future: Organon-specific components
├── ergasterion/               # Future: Ergasterion-specific components
└── agon/                      # Future: Agon-specific components
```

### Launch Command
```bash
cd /Users/mjh/Sync/GitHub/Arisbe
python src/gui/arisbe_main_app.py
```

## Design Principles

### Logical Foundation First
- Built around proven 100% transformation success
- Every operation maintains EGI validity
- Complete transformation provenance
- Immutable data pipeline

### Progressive Enhancement
- Start with linear forms (implemented)
- Plan for interactive diagrams (future)
- Maintain logical correctness throughout
- Preserve transformation history

### Three-Application Architecture
- Clear separation of concerns
- Consistent navigation paradigm
- Shared state management
- Cross-application communication

## Usage Patterns

### Graph Browsing (Organon)
1. Select EGI from corpus tree
2. View structure in linear form
3. Examine components and relationships
4. Switch to other tabs with loaded EGI

### Graph Building (Ergasterion)
1. Start with blank sheet
2. Apply transformation rules sequentially
3. View workspace state updates
4. Track complete construction history

### Formal Reasoning (Agon)
1. Run classical syllogism demonstration
2. Observe 100% transformation success
3. Study proof step sequence
4. Prepare for Endoporeutic Game

## Future Enhancements

### Interactive Diagram Support
- Qt graphics scene integration
- Visual transformation wizards
- Drag-and-drop rule application
- Real-time spatial layout

### Corpus Management
- EGI file loading/saving
- Collection organization
- Search and filtering
- Version control integration

### Endoporeutic Game Implementation
- Formal game rules engine
- Player interaction system
- Move validation and scoring
- Tournament and challenge modes

## Conclusion

The Arisbe GUI framework provides a solid foundation for existential graph reasoning with complete integration of the proven transformation core. The three-application architecture supports the full spectrum of logical work while maintaining mathematical rigor and providing clear paths for future enhancement toward interactive diagram manipulation.
