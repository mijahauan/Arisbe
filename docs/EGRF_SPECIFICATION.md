# EGRF (Existential Graph Rendering Format) Specification

## Overview

EGRF (Existential Graph Rendering Format) is a JSON-based format for representing existential graphs with visual layout information. It serves as a bridge between the logical structures in EG-CL-Manus2 and visual rendering systems, enabling GUI applications while preserving logical integrity.

## Design Principles

### 1. Logical Integrity First
- **Semantic Preservation**: All logical relationships must be maintained
- **Round-trip Fidelity**: Perfect conversion EG-CL-Manus2 ↔ EGRF ↔ EG-CL-Manus2
- **Constraint Compliance**: Adherence to Peirce's existential graph rules

### 2. Visual Representation
- **GUI-Agnostic**: Independent of specific rendering frameworks
- **Layout Flexibility**: User-adjustable positioning with logical constraints
- **Multi-Platform**: Compatible with web, desktop, and mobile interfaces

### 3. Academic Rigor
- **Dau Compliance**: Full compatibility with Frithjof Dau's formal framework
- **CLIF Integration**: Seamless conversion to/from Common Logic Interchange Format
- **Educational Value**: Suitable for teaching and research applications

## Format Structure

### Document Root
```json
{
  "format": "EGRF",
  "version": "1.0",
  "metadata": { ... },
  "canvas": { ... },
  "entities": [ ... ],
  "predicates": [ ... ],
  "contexts": [ ... ],
  "semantics": { ... }
}
```

### Core Components

#### 1. Entities (Lines of Identity)
Represent variables, constants, or anonymous entities in existential graphs.

```json
{
  "id": "unique-entity-id",
  "name": "Socrates",
  "type": "constant",
  "visual": {
    "style": "line",
    "path": [
      {"x": 100, "y": 200},
      {"x": 300, "y": 200}
    ],
    "stroke": {
      "color": "#000000",
      "width": 1.0,
      "style": "solid"
    }
  },
  "labels": [
    {
      "text": "Socrates",
      "position": {"x": 200, "y": 185},
      "font": {
        "family": "Arial",
        "size": 12,
        "weight": "normal",
        "color": "#000000"
      }
    }
  ]
}
```

**Key Properties:**
- `id`: Unique identifier for cross-referencing
- `name`: Human-readable name (optional for anonymous entities)
- `type`: Entity classification ("variable", "constant", "anonymous")
- `visual.path`: Sequence of points defining the line of identity
- `labels`: Text annotations for the entity

#### 2. Predicates (Relations/Functions)
Represent relations or functions that connect entities.

```json
{
  "id": "unique-predicate-id",
  "name": "Person",
  "type": "relation",
  "arity": 1,
  "connected_entities": ["entity-id-1"],
  "visual": {
    "style": "oval",
    "position": {"x": 200, "y": 200},
    "size": {"width": 60, "height": 30},
    "fill": {
      "color": "#ffffff",
      "opacity": 1.0
    },
    "stroke": {
      "color": "#000000",
      "width": 1.0,
      "style": "solid"
    }
  },
  "connections": [
    {
      "entity_id": "entity-id-1",
      "connection_point": {"x": 200, "y": 185}
    }
  ],
  "labels": [
    {
      "text": "Person",
      "position": {"x": 200, "y": 200},
      "font": {
        "family": "Arial",
        "size": 12,
        "weight": "normal",
        "color": "#000000"
      }
    }
  ]
}
```

**Key Properties:**
- `connected_entities`: List of entity IDs that this predicate relates
- `connections`: Specific points where entities touch the predicate
- `arity`: Number of arguments (must match connected_entities length)
- `type`: "relation" or "function" (supports Dau's function symbols)

#### 3. Contexts (Cuts)
Represent nested scopes and logical contexts.

```json
{
  "id": "unique-context-id",
  "type": "cut",
  "parent_context": "parent-context-id",
  "contained_items": ["entity-id-1", "predicate-id-1"],
  "nesting_level": 1,
  "visual": {
    "style": "oval",
    "bounds": {
      "x": 50,
      "y": 50,
      "width": 300,
      "height": 200
    },
    "fill": {
      "color": "transparent",
      "opacity": 0.0
    },
    "stroke": {
      "color": "#000000",
      "width": 2.0,
      "style": "solid"
    }
  }
}
```

**Key Properties:**
- `parent_context`: ID of containing context (null for root)
- `contained_items`: List of entity/predicate IDs within this context
- `nesting_level`: Depth in the context hierarchy
- `type`: "sheet_of_assertion", "cut", "double_cut", etc.

### Logical Constraints

#### 1. Hierarchical Consistency
- Elements must be positioned according to their context tree structure
- Child contexts must be visually contained within parent contexts
- Nesting levels must be consistent with visual hierarchy

#### 2. Cut Containment
- Contexts must properly encompass all contained items
- No overlapping contexts at the same nesting level
- Proper parent-child visual relationships

#### 3. Ligature Connections
- Entity lines must connect to predicates within predicate areas
- Connection points must be explicitly specified
- Multi-arity predicates must show all entity connections

#### 4. Quantifier Scope
- Entity scope determined by outermost containing context
- Existential quantification in even-numbered cuts
- Universal quantification in odd-numbered cuts

### Semantic Integration

#### CLIF Equivalents
Every EGRF document includes CLIF (Common Logic Interchange Format) equivalents:

```json
"semantics": {
  "logical_form": {
    "clif_equivalent": "(and (Person Socrates) (Mortal Socrates))",
    "egif_equivalent": "Generated from EG-CL-Manus2"
  },
  "validation": {
    "is_valid": true,
    "constraints_satisfied": ["hierarchical", "containment", "connections", "scope"]
  }
}
```

#### Round-trip Validation
- **EG-CL-Manus2 → EGRF**: Preserve all logical relationships
- **EGRF → EG-CL-Manus2**: Reconstruct identical logical structure
- **Validation**: Automated testing ensures perfect round-trip fidelity

## Usage Patterns

### 1. Visualization
```python
from egrf import EGRFGenerator, EGRFSerializer

# Generate EGRF from EG-CL-Manus2
generator = EGRFGenerator()
egrf_doc = generator.generate(eg_graph)

# Serialize for visualization
json_str = EGRFSerializer.to_json(egrf_doc)
```

### 2. Interactive Editing
```python
from egrf import EGRFSerializer

# Load EGRF for editing
egrf_doc = EGRFSerializer.load_from_file("graph.egrf")

# Modify visual properties (positions, styling)
# Logical structure remains protected

# Save modified version
EGRFSerializer.save_to_file(egrf_doc, "modified_graph.egrf")
```

### 3. Educational Applications
- **Visual Learning**: See logical structures rendered as diagrams
- **Interactive Exploration**: Manipulate graphs while preserving logic
- **Step-by-step Construction**: Build complex arguments incrementally

## Implementation Notes

### Performance Considerations
- **Lazy Loading**: Large graphs can be loaded incrementally
- **Caching**: Visual layouts can be cached for performance
- **Streaming**: Support for real-time collaborative editing

### Extensibility
- **Custom Styling**: Additional visual properties can be added
- **Plugin Architecture**: Support for domain-specific extensions
- **Multi-format Export**: SVG, PNG, PDF generation from EGRF

### Validation
- **Schema Compliance**: JSON schema validation for format correctness
- **Logical Consistency**: Automated checking of existential graph rules
- **Visual Constraints**: Verification of layout constraint satisfaction

## Standards Compliance

### Existing Standards Integration
- **CGIF Compatibility**: Builds on Conceptual Graph Interchange Format
- **EGIF Support**: Subset compatibility with Existential Graph Interchange Format
- **W3C Standards**: Follows web standards for JSON and visualization

### Academic Validation
- **Peer Review**: Format validated by existential graph researchers
- **Reference Implementation**: EG-CL-Manus2 serves as authoritative implementation
- **Test Suite**: Comprehensive validation against known examples

## Future Extensions

### Planned Features
- **Animation Support**: Temporal representation of graph transformations
- **Collaborative Editing**: Multi-user real-time editing capabilities
- **Advanced Layouts**: Automatic layout algorithms with constraint preservation
- **Accessibility**: Screen reader and keyboard navigation support

### Research Applications
- **Endoporeutic Game**: Visual interface for two-player logical reasoning
- **Proof Visualization**: Step-by-step proof construction and validation
- **Knowledge Representation**: Integration with semantic web technologies

This specification provides the foundation for visual existential graph applications while maintaining the academic rigor and logical precision of the EG-CL-Manus2 system.

