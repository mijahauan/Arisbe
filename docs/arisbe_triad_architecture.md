# Arisbe Triad Architecture: Complete System Integration

## Overview

Arisbe implements a complete cycle of inquiry through three interconnected components that model the logical process of knowledge development: corpus management (Organon), diagram workshop (Ergasterion), and productive reasoning (deductive, inductive, abductive) (Agon).

## The Triad Components

### **Organon** (Corpus Management & Graph Creation)
**Purpose**: Knowledge corpus management and graph origination
**Location**: `src/organon/`

**Core Functions**:
- **Linear Form Parsing**: Parse seed linear forms (EGIF, CGIF, CLIF) into canonical EGI
- **Graph Origination**: Create new empty graphs for diagram development
- **Corpus Storage**: Serialize graphs in JSON/YAML formats
- **Metadata Management**: Edit graph information and metadata
- **Read-Only Visualization**: View EG diagrams and linear forms
- **Universe of Discourse Views**: Static and dynamic "moving pictures of thought"

**Data Flow**:
```
Linear Form (EGIF/CGIF/CLIF) → Parser → Canonical EGI → JSON/YAML Storage
Empty Graph → Ergasterion → EGDF → Organon Storage
```

### **Ergasterion** (Workshop for Composition & Practice)
**Purpose**: Interactive diagram authoring and transformation practice
**Location**: `src/diagram_coordinator.py`, `src/interaction_handler.py`, `tools/drawing_editor_refactored.py`

**Core Functions**:
- **Composition Mode**: Diagram authoring with syntax constraints
- **Practice Mode**: Transformation rule application and validation
- **EGI-Spatial Correspondence**: Maintain logical consistency during editing
- **Intelligent Assistance**: Ligature geometry suggestions and optimization
- **EGDF Serialization**: Generate diagrams for storage in Organon

**Data Flow**:
```
Organon Graph → Ergasterion Editor → User Interaction → EGDF → Organon Storage
```

### **Agon** (Deductive Game & Umpire Function)
**Purpose**: Logical evaluation through the Endoporeutic Game
**Location**: Future development

**Core Functions**:
- **Deductive Game Engine**: Model logical reasoning as game play
- **Umpire Function**: Meta-level evaluation of game outcomes
- **Hypothesis Management**: Handle competing hypotheses and contexts
- **Logical Classification**: Identify contradictions, tautologies, contingencies
- **Inquiry Cycle Management**: Connect deduction to abduction and induction

**Umpire Decision Tree**:
```
Game Outcome → Umpire Evaluation:
├── Contradiction → Prompt discard/archive (logically uninformative)
├── Tautology → Prompt discard/archive (logically uninformative)  
└── Contingent → Accept as valid hypothesis → Next steps:
    ├── Form prediction (inductive phase)
    └── Return to Ergasterion (new hypothesis)
```

## Integration Workflows

### **Workflow 1: New Graph Creation**
```
1. Organon: User creates empty graph
2. Organon → Ergasterion: Pass graph for diagram creation
3. Ergasterion: User draws diagram (generates EGI + spatial layout)
4. Ergasterion → Organon: Return EGDF serialization
5. Organon: Store graph with metadata
```

### **Workflow 2: Linear Form Import**
```
1. Organon: User provides linear form (EGIF/CGIF/CLIF)
2. Organon: Parse to canonical EGI
3. Organon: Store as JSON/YAML
4. Optional: Organon → Ergasterion for diagram creation
```

### **Workflow 3: Hypothesis Testing**
```
1. Organon: Provide hypothesis graph
2. Organon → Agon: Submit for deductive evaluation
3. Agon: Execute Endoporeutic Game
4. Agon Umpire: Evaluate outcome
5. Agon → Organon: Return classification + recommendations
6. Based on outcome:
   - Contingent → Continue inquiry cycle
   - Contradiction/Tautology → Archive/discard
```

### **Workflow 4: Practice Session**
```
1. Organon: Provide corpus examples
2. Organon → Ergasterion: Load for practice
3. Ergasterion: Practice Mode transformation rules
4. Ergasterion → Agon: Validate transformations
5. Agon → Ergasterion: Provide feedback
6. Ergasterion → Organon: Store practice results
```

## Technical Integration Points

### **Data Formats**
- **EGI**: Core logical structure (`RelationalGraphWithCuts`)
- **EGDF**: Diagram format with spatial layout
- **JSON/YAML**: Corpus storage formats
- **Linear Forms**: EGIF, CGIF, CLIF for import

### **Shared Components**
- **EGI Core**: `egi_core_dau.py` (used by all components)
- **Spatial Correspondence**: `egi_spatial_correspondence.py` (Organon ↔ Ergasterion)
- **Constraint Engine**: `controller/constraint_engine.py` (validation across components)
- **Renderer**: `shared_diagram_renderer.py` (Organon read-only, Ergasterion interactive)

### **Communication Interfaces**
```python
# Organon → Ergasterion
def launch_ergasterion(graph_data: Dict[str, Any]) -> Optional[Dict[str, Any]]

# Ergasterion → Organon  
def save_to_organon(egdf_data: Dict[str, Any]) -> bool

# Organon → Agon
def submit_for_evaluation(egi: RelationalGraphWithCuts) -> GameResult

# Agon → Organon
def receive_game_result(result: GameResult) -> UmpireDecision
```

## Current Implementation Status

### ✅ **Completed**
- **Ergasterion Core**: Modular architecture with DiagramCoordinator
- **EGI-Spatial Correspondence**: Full logical-spatial translation
- **Intelligent Assistance**: Ligature geometry suggestions
- **Mode Infrastructure**: Composition/Practice mode framework
- **EGDF Serialization**: Round-trip diagram storage

### 🔄 **In Progress**
- **Organon Integration**: Connect existing Organon with new Ergasterion
- **Linear Form Parsing**: EGIF/CGIF/CLIF parser integration
- **Workflow Orchestration**: Inter-component communication

### 📋 **Future Development**
- **Agon Implementation**: Deductive game engine
- **Umpire Function**: Meta-level logical evaluation
- **Universe of Discourse Visualization**: Dynamic knowledge views
- **Complete Inquiry Cycle**: Abduction-Deduction-Induction integration

## Architecture Benefits

### **Separation of Concerns**
- **Organon**: Pure knowledge management
- **Ergasterion**: Pure interaction and authoring
- **Agon**: Pure logical reasoning

### **Flexible Workflows**
- Users can work in any component independently
- Components can be combined for complex workflows
- Each component optimized for its specific purpose

### **Extensible Design**
- New parsers can be added to Organon
- New interaction modes can be added to Ergasterion  
- New reasoning strategies can be added to Agon

### **Knowledge Continuity**
- All work flows through the corpus (Organon)
- Logical consistency maintained across components
- Complete audit trail of inquiry process

## Future Vision: Complete Inquiry Cycle

The Arisbe Triad will eventually support the complete Peircean inquiry cycle:

1. **Abduction** (Organon): Generate hypotheses from observations
2. **Deduction** (Agon): Explore logical consequences  
3. **Induction** (Organon + Agon): Test predictions against experience
4. **Diagram Practice** (Ergasterion): Develop reasoning skills
5. **Knowledge Management** (Organon): Maintain evolving understanding

This creates a complete environment for logical inquiry, combining the precision of formal logic with the intuitive power of diagrammatic reasoning.
