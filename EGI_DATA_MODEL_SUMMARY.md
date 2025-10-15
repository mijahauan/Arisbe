# EGI Data Model & Management System Summary

**Date**: 2025-10-01  
**Purpose**: Document how Arisbe manages Existential Graph Instances (EGIs)

---

## 🎯 CORE DATA STRUCTURE

### **RelationalGraphWithCuts** (Dau-Compliant)

EGIs are represented using Frithjof Dau's exact **6+1 component** definition:

```python
@dataclass(frozen=True)
class RelationalGraphWithCuts:
    # Core 6 components (Dau Definition 12.1)
    V: FrozenSet[Vertex]              # Component 1: Vertices
    E: FrozenSet[Edge]                # Component 2: Edges
    nu: frozendict[ElementID, VertexSequence]  # Component 3: ν mapping
    sheet: ElementID                  # Component 4: ⊤ sheet of assertion
    Cut: FrozenSet[Cut]               # Component 5: Cuts
    area: frozendict[ElementID, FrozenSet[ElementID]]  # Component 6: area mapping
    
    # 7th component
    rel: frozendict[ElementID, RelationName]  # Component 7: relation names
    
    # Optional components
    alphabet: Optional[AlphabetDAU]   # (C, F, R, ar) - constants, functions, relations, arity
    rho: frozendict[ElementID, Optional[str]]  # vertex_id → constant name
    variable_names: frozendict[ElementID, str]  # vertex_id → variable name ("x", "y", etc.)
    hierarchical_index: Optional[HierarchicalIndex]  # For efficient nesting operations
```

**Key Properties**:
- **Immutable**: All collections are frozen (frozensets, frozendicts)
- **Type-safe**: Strong typing for all components
- **Dau-compliant**: Exact mathematical definition
- **Self-contained**: No external dependencies in the data structure

---

## 📦 SERIALIZATION & STORAGE

### **JSON Format** (Primary Storage)

**Location**: `tomos/graphs/[graph_name]/[graph_name].egi.json`

**Schema**:
```json
{
  "sheet": "sheet_id",
  "V": [
    {"id": "v_id", "label": null, "is_generic": true},  // Generic vertex
    {"id": "v_id2", "label": "Socrates", "is_generic": false}  // Constant
  ],
  "E": [
    {"id": "e_id"}
  ],
  "Cut": [
    {"id": "c_id"}
  ],
  "nu": {
    "e_id": ["v_id", "v_id2"]  // Edge-to-vertex-sequence mapping
  },
  "rel": {
    "e_id": "Human"  // Edge-to-relation-name mapping
  },
  "area": {
    "sheet_id": ["c_id", "e_id2", ...],  // Sheet contains cuts/edges/vertices
    "c_id": ["e_id", "v_id", ...]        // Cut contains edges/vertices
  },
  "alphabet": {
    "C": ["Socrates"],          // Constants
    "F": [],                    // Functions
    "R": ["Human", "Mortal"],   // Relations
    "ar": {"Human": 1, "Mortal": 1, "Socrates": 1}  // Arities
  },
  "rho": {
    "v_id2": "Socrates"  // Vertex-to-constant mapping
  }
}
```

**I/O Functions**:
```python
# Save EGI to JSON
from egi_io import save_egi_json, load_egi_json

save_egi_json(egi, "path/to/file.json")

# Load EGI from JSON
egi = load_egi_json("path/to/file.json")
```

---

## 📚 CORPUS ORGANIZATION

### **Directory Structure**

```
tomos/
├── index.json                    # Corpus-wide metadata index
├── README.md                     # Tomos documentation
└── graphs/                       # Individual graph directories
    ├── peirce_cp_4_394_man_mortal/
    │   ├── peirce_cp_4_394_man_mortal.egi.json  # EGI data
    │   ├── EGDF/                                # Diagram layouts
    │   └── EXPORTS/                             # SVG, PDF, LaTeX exports
    ├── dau_2006_p112_ligature/
    ├── graph_new_1/
    └── ...
```

### **Graph Categories**

1. **Peirce Examples** - Direct from Peirce's writings
2. **Scholar Examples** - From secondary literature
3. **Canonical Examples** - Synthetic standard patterns
4. **EPG Examples** - Endoporeutic Game starting positions
5. **Theorem Proving** - Complex mathematical proofs
6. **Domain Modeling** - Real-world application examples

### **Current Tomos Size**

- **~30+ graphs** in various stages of development
- Each graph has:
  - `.egi.json` - Core EGI data
  - `EGDF/` subdirectory - Diagram layouts (optional)
  - `EXPORTS/` subdirectory - Generated outputs (optional)

---

## 🔄 EGI LIFECYCLE

### **1. Creation**

**From Scratch**:
```python
from egi_core_dau import create_empty_graph, create_vertex, create_edge

egi = create_empty_graph()
vertex = create_vertex(label="Socrates", is_generic=False)
egi = egi.with_vertex(vertex)
edge = create_edge(relation_name="Human", incident_vertices=[vertex.id])
egi = egi.with_edge(edge)
```

**From Linear Form** (EGIF, CGIF, CLIF):
```python
from egif_parser_dau import parse_egif

egif = "[Human: Socrates]"
egi = parse_egif(egif)
```

**From JSON File**:
```python
from egi_io import load_egi_json

egi = load_egi_json("tomos/graphs/example/example.egi.json")
```

### **2. Manipulation**

**Adding Elements** (returns new immutable EGI):
```python
# Add vertex
new_egi = egi.with_vertex(new_vertex)

# Add edge
new_egi = egi.with_edge(new_edge)

# Add cut
new_egi = egi.with_cut(new_cut)
```

**Transformations** (formal rules):
```python
from formal_transformation_rules import DoubleNegationInsertionRule

rule = DoubleNegationInsertionRule()
result_egi = rule.apply_transformation(context)
```

### **3. Querying**

**Access Components**:
```python
vertices = egi.V                    # All vertices
edges = egi.E                       # All edges
cuts = egi.Cut                      # All cuts
vertex_seq = egi.nu[edge_id]        # Vertices incident to edge
relation = egi.rel[edge_id]         # Relation name for edge
contents = egi.area[cut_id]         # Contents of cut/sheet
```

**Linear Forms**:
```python
from egif_generator_dau import generate_egif
from cgif_generator import generate_cgif
from clif_generator import generate_clif

egif = generate_egif(egi)           # Linear form
cgif = generate_cgif(egi)           # Conceptual Graphs format
clif = generate_clif(egi)           # Common Logic format
```

### **4. Visualization**

**Through DiagramController**:
```python
from diagram_controller import DiagramController

controller = DiagramController()
controller.load_egi(egi)
dto = controller.get_renderable_dto()  # Get layout for display
```

**Direct SVG Generation**:
```python
from definitive_egi_layout_engine import DefinitiveEGILayoutEngine
from graphviz_svg_renderer import GraphvizSVGRenderer

layout_engine = DefinitiveEGILayoutEngine()
dto = layout_engine.generate_layout(egi)

renderer = GraphvizSVGRenderer()
svg_content = renderer.render_to_svg(dto)
```

### **5. Persistence**

**Save to JSON**:
```python
from egi_io import save_egi_json

save_egi_json(egi, "tomos/graphs/my_graph/my_graph.egi.json")
```

**Tomos Integration**:
1. Create graph directory: `tomos/graphs/my_graph/`
2. Save EGI: `my_graph.egi.json`
3. Create subdirectories: `EGDF/`, `EXPORTS/`
4. Update `tomos/index.json` with metadata

---

## 🎮 DIAGRAMCONTROLLER INTEGRATION

### **Purpose**

`DiagramController` is the **single source of truth** for EGI state in the GUI.

**Key Responsibilities**:
1. Load/store current EGI
2. Generate LayoutDTO for visualization
3. Apply transformations (formal rules)
4. Manage user aesthetic adjustments (LayoutDeltas)
5. Validate operations
6. Support undo/redo (via CommandExecutor)

### **API**

```python
controller = DiagramController()

# Load EGI
controller.load_egi(egi, style=None)

# Get current state
current_egi = controller.get_egi_model()
dto = controller.get_renderable_dto()

# Apply formal transformation
success = controller.apply_formal_rule(
    rule_name='DC+',
    selection_ids=['v_id', 'e_id'],
    target_area='sheet_id'
)

# Update aesthetic (position)
success = controller.update_element_position(
    element_id='v_id',
    new_position=(100.0, 200.0)
)

# Validation
is_valid = controller.validate_element_position(
    element_id='v_id',
    position=(100.0, 200.0)
)
```

### **State Management**

```python
class DiagramController:
    egi_model: Optional[RelationalGraphWithCuts]  # Current EGI
    layout_engine: DefinitiveEGILayoutEngine      # For layout generation
    layout_deltas: LayoutDeltas                   # User aesthetic adjustments
    current_style: Optional[StyleSpecification]   # Visual theme
```

**Important**: 
- EGI is immutable - transformations return new EGI
- LayoutDeltas persist aesthetic adjustments across transformations
- Invalid positions are rejected to preserve logical correctness

---

## 📊 METADATA & INDEXING

### **Tomos Index** (`tomos/index.json`)

```json
{
  "version": "1.0",
  "graphs": [
    {
      "id": "peirce_cp_4_394_man_mortal",
      "path": "graphs/peirce_cp_4_394_man_mortal/peirce_cp_4_394_man_mortal.egi.json",
      "category": "peirce",
      "description": "Socrates is human, all humans are mortal",
      "complexity": {
        "vertices": 1,
        "edges": 2,
        "cuts": 2,
        "nesting_depth": 2
      }
    }
  ]
}
```

### **Individual Graph Metadata**

Could be extended with `.metadata.json` files:
- Source citations
- Natural language descriptions
- Complexity metrics
- Test rationale
- Transformation history

---

## 🔑 KEY DESIGN PRINCIPLES

### **1. Immutability**

**All EGI operations return new instances**:
```python
# ❌ WRONG (mutation)
egi.vertices.add(new_vertex)

# ✅ CORRECT (immutable update)
new_egi = egi.with_vertex(new_vertex)
```

**Benefits**:
- Thread-safe
- Undo/redo trivial (just keep old instances)
- No accidental state corruption
- Perfect for functional transformations

### **2. Mathematical Correctness**

- Exact Dau formalism compliance
- All formal constraints validated
- Type-safe operations
- No "partially valid" states

### **3. Separation of Concerns**

**EGI (logical)** vs **Layout (spatial)**:
- EGI knows nothing about positions
- LayoutDTO knows nothing about logic
- DiagramController bridges the two
- User aesthetics preserved when valid, rejected when invalid

### **4. Round-Trip Fidelity**

```
EGI → JSON → EGI  (perfect round-trip)
EGI → EGIF → EGI  (perfect round-trip)
EGI → CGIF → EGI  (perfect round-trip)
EGI → Layout → Display  (deterministic)
```

---

## 🚀 USAGE IN GUI

### **Organon Mode** (Exploration)

```python
# Load from corpus
egi = load_egi_json("tomos/graphs/example/example.egi.json")

# Display via DiagramController
controller.load_egi(egi)
dto = controller.get_renderable_dto()
canvas.display_dto(dto, egi)

# Export
save_egi_json(egi, "exports/example.json")
renderer.save_svg(dto, "exports/example.svg")
```

### **Ergasterion Mode** (Workshop)

```python
# Load for editing
controller.load_egi(egi)

# User repositions element
success = controller.update_element_position(v_id, new_pos)

# User applies transformation
success = controller.apply_formal_rule('DC+', [v_id, e_id], area_id)

# Save modified EGI
modified_egi = controller.get_egi_model()
save_egi_json(modified_egi, "tomos/graphs/modified/modified.egi.json")
```

### **Agon Mode** (Game)

```python
# Load hypothesis
controller.load_egi(hypothesis_egi)

# Game moves (transformations)
success = controller.apply_formal_rule('INS', [e_id], target_area)

# Umpire evaluation
outcome = analyze_egi(controller.get_egi_model())  # Contingent/Tautology/Contradiction

# Archive result
if outcome == "contingent":
    save_egi_json(controller.get_egi_model(), f"tomos/hypotheses/{id}.egi.json")
```

---

## 📋 SUMMARY

### **What is an EGI?**
- Immutable data structure representing an Existential Graph
- Dau-compliant 6+1 component definition
- Self-contained, no external dependencies

### **How is it stored?**
- Primary: JSON files in `tomos/graphs/`
- Structure: Nested directories per graph
- Metadata: `tomos/index.json` for corpus-wide indexing

### **How is it manipulated?**
- Immutable operations (`.with_*()` methods)
- Formal transformation rules
- Never direct mutation

### **How is it displayed?**
- DiagramController generates LayoutDTO
- LayoutDTO rendered to SVG via GraphvizSVGRenderer
- User aesthetics managed via LayoutDeltas

### **How does GUI interact?**
- **Organon**: Load, view, export
- **Ergasterion**: Load, edit, transform, save
- **Agon**: Load, apply game moves, evaluate, archive

### **Key Modules**:
- `egi_core_dau.py` - Data structures
- `egi_io.py` - JSON serialization
- `diagram_controller.py` - State management
- `definitive_egi_layout_engine.py` - Layout generation
- `graphviz_svg_renderer.py` - SVG rendering

---

**This data model provides the foundation for all GUI operations!**
