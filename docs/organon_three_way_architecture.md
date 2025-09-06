# Organon: Three-Way Interface Architecture

## Overview

Organon serves as the central hub of Arisbe, facing three distinct directions with specialized interfaces for each:

```
                    Outside World
                   (Seeding, Exports)
                          ↑
                          |
    Ergasterion ←── ORGANON ──→ Agon
  (Individual        (Hub)    (Universe of
   Graphs)                    Discourse)
```

## Three Interface Directions

### 1. Organon ↔ Outside World
**Purpose**: Import/Export and external integration
**Functions**:
- **Seeding New Graphs**: Import linear forms (EGIF, CGIF, CLIF) from literature
- **Corpus Export**: Export collections in various formats (JSON, YAML, PDF)
- **Publication Export**: Generate LaTeX/TikZ for academic papers
- **Data Import**: Load graphs from external sources
- **Backup/Archive**: Full corpus backup and restoration

### 2. Organon ↔ Ergasterion  
**Purpose**: Individual graph editing and composition
**Functions**:
- **New Graph Creation**: Send empty graphs to Ergasterion
- **Diagram Creation**: Send EGI-only graphs for diagram drawing
- **Graph Editing**: Send complete EGI+EGDF for adjustments/practice
- **Return Processing**: Receive completed work back from Ergasterion
- **Version Management**: Track graph evolution through editing sessions

### 3. Organon ↔ Agon (Future)
**Purpose**: Universe of Discourse development and logical evaluation
**Functions**:
- **UoD Visualization**: Display Universes of Discourse developed in Agon
- **Hypothesis Management**: Send graphs to Agon for logical evaluation
- **Result Integration**: Receive logical classifications (tautology/contradiction/contingent)
- **Knowledge Evolution**: Track how individual graphs contribute to larger UoDs
- **Consistency Checking**: Validate corpus consistency against UoD constraints

## Organon Internal Architecture

### Core Components
- **Corpus Manager**: Central repository for all graphs
- **Graph Browser**: Navigate and search individual graphs
- **UoD Viewer**: Display Universe of Discourse structures
- **Import/Export Engine**: Handle external data formats
- **Workflow Coordinator**: Manage handoffs to Ergasterion/Agon

### Data Flow Management
```
External Sources → Import Engine → Corpus Manager
                                       ↓
                   Graph Browser ←→ Individual Graphs
                                       ↓
                   Workflow Coordinator → Ergasterion (editing)
                                       ↓
                   UoD Viewer ←→ Agon (evaluation)
                                       ↓
                   Export Engine → External Outputs
```

## Interface Specifications

### Outside World Interface
```python
class ExternalInterface:
    def import_linear_form(self, content: str, format: str) -> GraphData
    def export_corpus(self, format: str, selection: List[str]) -> bytes
    def seed_from_literature(self, source: str) -> List[GraphData]
    def generate_publication_export(self, graphs: List[str]) -> LaTeXDocument
```

### Ergasterion Interface  
```python
class ErgasterionInterface:
    def create_new_graph(self, metadata: Dict) -> GraphHandoffPackage
    def edit_existing_graph(self, graph_id: str) -> GraphHandoffPackage
    def practice_with_graph(self, graph_id: str) -> GraphHandoffPackage
    def receive_completed_work(self, return_package: GraphReturnPackage) -> bool
```

### Agon Interface (Future)
```python
class AgonInterface:
    def view_universe_of_discourse(self, uod_id: str) -> UoDVisualization
    def submit_for_evaluation(self, graph_id: str) -> EvaluationRequest
    def receive_logical_classification(self, result: LogicalResult) -> bool
    def check_corpus_consistency(self, uod_id: str) -> ConsistencyReport
```

## User Workflows

### Workflow 1: External Seeding
```
1. User imports CGIF from literature
2. Organon parses to canonical EGI
3. User reviews in Graph Browser
4. Optional: Send to Ergasterion for diagram creation
5. Store in Corpus
```

### Workflow 2: Graph Development
```
1. User browses Corpus
2. Select graph for editing
3. Organon determines handoff type (Case 1/2/3)
4. Launch Ergasterion with appropriate package
5. Receive completed work back
6. Update Corpus with new version
```

### Workflow 3: Knowledge Integration (Future)
```
1. User views Universe of Discourse
2. Select graphs for logical evaluation
3. Send to Agon for consistency checking
4. Receive logical classifications
5. Update UoD structure based on results
```

## Implementation Strategy

### Phase 1: Enhanced Corpus Management
- Robust graph storage and retrieval
- Advanced search and filtering
- Version history tracking
- Metadata management

### Phase 2: External Integration
- Linear form parsers (EGIF/CGIF/CLIF)
- Export engines (JSON/YAML/LaTeX)
- Import validation and error handling
- Publication-ready output generation

### Phase 3: Agon Integration (Future)
- Universe of Discourse visualization
- Logical evaluation workflows
- Consistency checking algorithms
- Knowledge evolution tracking

## Benefits of Three-Way Architecture

### Separation of Concerns
- **External**: Data import/export without internal complexity
- **Ergasterion**: Individual graph focus without corpus overhead
- **Agon**: Logical evaluation without editing concerns

### Scalability
- Each interface can evolve independently
- New external formats easily added
- Ergasterion enhancements don't affect other interfaces
- Agon development doesn't disrupt existing workflows

### User Experience
- Single entry point (Organon) for all activities
- Context-appropriate interfaces for each task
- Seamless transitions between components
- Unified corpus management across all workflows

This architecture positions Organon as the true "organizer" of knowledge, coordinating between external sources, individual graph work, and logical evaluation while maintaining clean separation between these distinct concerns.
