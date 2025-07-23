# EGRF v3.0 Developer Guide

## Introduction

This developer guide provides detailed information on how to work with the Existential Graph Rendering Format (EGRF) v3.0. It covers the core components, data structures, and APIs, as well as best practices for implementing and extending the system.

## Getting Started

### Prerequisites

- Python 3.6 or higher
- Basic understanding of Peirce's Existential Graphs
- Familiarity with the EG-HG (Existential Graph Hypergraph) format

### Installation

To use EGRF v3.0 in your project, you need to include the following files:

```
src/egrf/v3/
├── __init__.py
├── logical_types.py
├── containment_hierarchy.py
├── layout_constraints.py
├── converter/
│   ├── __init__.py
│   └── eg_hg_to_egrf.py
└── corpus_validator.py
```

## Core Components

### Logical Types

The logical types module (`logical_types.py`) defines the core data structures for EGRF v3.0:

```python
from src.egrf.v3.logical_types import (
    create_logical_context, create_logical_predicate, create_logical_entity,
    LogicalElement, LogicalContext, LogicalPredicate, LogicalEntity,
    ContainmentRelationship
)
```

#### Creating Elements

```python
# Create a sheet of assertion
sheet = create_logical_context(
    id="sheet",
    name="Sheet of Assertion",
    container="none",
    context_type="sheet_of_assertion",
    is_root=True,
    nesting_level=0
)

# Create a cut
cut = create_logical_context(
    id="cut1",
    name="Cut 1",
    container="sheet",
    context_type="cut",
    is_root=False,
    nesting_level=1
)

# Create a predicate
predicate = create_logical_predicate(
    id="predicate1",
    name="Person",
    container="sheet",
    arity=1
)

# Create an entity
entity = create_logical_entity(
    id="entity1",
    name="Socrates",
    connected_predicates=["predicate1"],
    entity_type="constant"
)
```

### Containment Hierarchy

The containment hierarchy module (`containment_hierarchy.py`) manages the nesting relationships between elements:

```python
from src.egrf.v3.containment_hierarchy import ContainmentHierarchyManager

# Create a hierarchy manager
hierarchy_manager = ContainmentHierarchyManager()

# Add elements to the hierarchy
hierarchy_manager.add_element(sheet)
hierarchy_manager.add_element(cut)
hierarchy_manager.add_element(predicate)
hierarchy_manager.add_element(entity)

# Add containment relationships
relationship1 = ContainmentRelationship(
    container="sheet",
    contained_elements=["cut1", "predicate1"]
)
hierarchy_manager.add_relationship(relationship1)

relationship2 = ContainmentRelationship(
    container="cut1",
    contained_elements=["entity1"]
)
hierarchy_manager.add_relationship(relationship2)

# Validate the hierarchy
validation_report = hierarchy_manager.validate()
if validation_report.is_valid:
    print("Hierarchy is valid")
else:
    print("Hierarchy is invalid:", validation_report.messages)
```

### Layout Constraints

The layout constraints module (`layout_constraints.py`) provides platform-independent positioning:

```python
from src.egrf.v3.layout_constraints import (
    LayoutElement, Viewport, LayoutContext,
    SizeConstraint, PositionConstraint, SpacingConstraint, ContainmentConstraint,
    LayoutManager
)

# Create layout elements
viewport = Viewport(id="viewport", width=800, height=600)
sheet_element = LayoutElement(id="sheet", element_type="context")
cut_element = LayoutElement(id="cut1", element_type="context")
predicate_element = LayoutElement(id="predicate1", element_type="predicate")
entity_element = LayoutElement(id="entity1", element_type="entity")

# Create layout context
layout_context = LayoutContext()
layout_context.add_element(viewport)
layout_context.add_element(sheet_element)
layout_context.add_element(cut_element)
layout_context.add_element(predicate_element)
layout_context.add_element(entity_element)

# Add constraints
layout_context.add_constraint(SizeConstraint(
    element_id="sheet",
    width=800,
    height=600
))

layout_context.add_constraint(PositionConstraint(
    element_id="cut1",
    container="sheet",
    x=0.5,
    y=0.5,
    x_unit="relative",
    y_unit="relative"
))

layout_context.add_constraint(SpacingConstraint(
    element_id="predicate1",
    min_spacing=10,
    preferred_spacing=20
))

layout_context.add_constraint(ContainmentConstraint(
    element_id="entity1",
    container="cut1"
))

# Solve layout
layout_manager = LayoutManager(layout_context)
layout_manager.solve()

# Get element positions
positions = layout_manager.get_element_positions()
for element_id, position in positions.items():
    print(f"{element_id}: ({position.x}, {position.y}) {position.width}x{position.height}")
```

### EG-HG to EGRF Converter

The converter module (`converter/eg_hg_to_egrf.py`) transforms EG-HG data to EGRF v3.0:

```python
from src.egrf.v3.converter.eg_hg_to_egrf import EgHgToEgrfConverter, parse_eg_hg_content

# Parse EG-HG content
with open("example.eg-hg", "r") as f:
    eg_hg_content = f.read()

eg_hg_data = parse_eg_hg_content(eg_hg_content)

# Convert to EGRF v3.0
converter = EgHgToEgrfConverter()
egrf_data = converter.convert(eg_hg_data)

# Save EGRF v3.0 data
import json
with open("example.egrf", "w") as f:
    json.dump(egrf_data, f, indent=2)
```

### Corpus Validation

The corpus validation module (`corpus_validator.py`) ensures the correctness of EGRF v3.0 implementations:

```python
from src.egrf.v3.corpus_validator import load_corpus_index, load_example, validate_egrf_structure

# Load corpus index
corpus_index = load_corpus_index("corpus/corpus_index.json")

# Load example
example = load_example(corpus_index, "peirce", "peirce_cp_4_394_man_mortal")

# Validate EGRF structure
is_valid, messages = validate_egrf_structure(example["egrf"])
if is_valid:
    print("EGRF structure is valid")
else:
    print("EGRF structure is invalid:", messages)
```

## Working with EGRF v3.0

### Creating a New Graph

To create a new graph in EGRF v3.0:

1. Create the logical elements (contexts, predicates, entities).
2. Establish the containment relationships.
3. Add layout constraints.
4. Validate the graph structure.

```python
# Create elements
sheet = create_logical_context(
    id="sheet",
    name="Sheet of Assertion",
    container="none",
    context_type="sheet_of_assertion",
    is_root=True,
    nesting_level=0
)

outer_cut = create_logical_context(
    id="outer_cut",
    name="Outer Cut",
    container="sheet",
    context_type="cut",
    is_root=False,
    nesting_level=1
)

inner_cut = create_logical_context(
    id="inner_cut",
    name="Inner Cut",
    container="outer_cut",
    context_type="cut",
    is_root=False,
    nesting_level=2
)

person_predicate = create_logical_predicate(
    id="person_predicate",
    name="Person",
    container="outer_cut",
    arity=1
)

mortal_predicate = create_logical_predicate(
    id="mortal_predicate",
    name="Mortal",
    container="inner_cut",
    arity=1
)

socrates1 = create_logical_entity(
    id="socrates1",
    name="Socrates",
    connected_predicates=["person_predicate"],
    entity_type="constant"
)

socrates2 = create_logical_entity(
    id="socrates2",
    name="Socrates",
    connected_predicates=["mortal_predicate"],
    entity_type="constant"
)

# Create EGRF data
egrf_data = {
    "metadata": {
        "version": "3.0.0",
        "format": "egrf",
        "id": "peirce_implication",
        "description": "If Socrates is a person, then Socrates is mortal"
    },
    "elements": {
        "sheet": sheet.to_dict(),
        "outer_cut": outer_cut.to_dict(),
        "inner_cut": inner_cut.to_dict(),
        "person_predicate": person_predicate.to_dict(),
        "mortal_predicate": mortal_predicate.to_dict(),
        "socrates1": socrates1.to_dict(),
        "socrates2": socrates2.to_dict()
    },
    "containment": {
        "outer_cut": "sheet",
        "inner_cut": "outer_cut",
        "person_predicate": "outer_cut",
        "mortal_predicate": "inner_cut",
        "socrates1": "outer_cut",
        "socrates2": "inner_cut"
    },
    "connections": [
        {
            "entity_id": "socrates1",
            "predicate_id": "person_predicate",
            "role": "arg1"
        },
        {
            "entity_id": "socrates2",
            "predicate_id": "mortal_predicate",
            "role": "arg1"
        }
    ],
    "ligatures": [
        {
            "entity1_id": "socrates1",
            "entity2_id": "socrates2",
            "type": "identity"
        }
    ],
    "layout_constraints": [
        # Add layout constraints here
    ]
}
```

### Converting from EG-HG

To convert an EG-HG graph to EGRF v3.0:

```python
# Parse EG-HG content
eg_hg_content = """
id: peirce_implication
description: If Socrates is a person, then Socrates is mortal
graph:
  contexts:
    - id: sheet
      type: sheet
      parent: null
    - id: outer_cut
      type: cut
      parent: sheet
    - id: inner_cut
      type: cut
      parent: outer_cut
  predicates:
    - id: person
      label: Person
      arity: 1
      context: outer_cut
    - id: mortal
      label: Mortal
      arity: 1
      context: inner_cut
  entities:
    - id: socrates1
      label: Socrates
      type: constant
    - id: socrates2
      label: Socrates
      type: constant
  connections:
    - predicate: person
      entities: [socrates1]
      roles: [arg1]
    - predicate: mortal
      entities: [socrates2]
      roles: [arg1]
    - entity1: socrates1
      entity2: socrates2
      type: identity
"""

eg_hg_data = parse_eg_hg_content(eg_hg_content)

# Convert to EGRF v3.0
converter = EgHgToEgrfConverter()
egrf_data = converter.convert(eg_hg_data)
```

### Validating EGRF v3.0

To validate an EGRF v3.0 graph:

```python
# Validate EGRF structure
is_valid, messages = validate_egrf_structure(egrf_data)
if is_valid:
    print("EGRF structure is valid")
else:
    print("EGRF structure is invalid:", messages)

# Validate containment hierarchy
hierarchy_manager = ContainmentHierarchyManager()
for element_id, element_data in egrf_data["elements"].items():
    element_type = element_data["element_type"]
    if element_type == "context":
        element = LogicalContext.from_dict(element_id, element_data)
    elif element_type == "predicate":
        element = LogicalPredicate.from_dict(element_id, element_data)
    elif element_type == "entity":
        element = LogicalEntity.from_dict(element_id, element_data)
    hierarchy_manager.add_element(element)

for element_id, container_id in egrf_data["containment"].items():
    relationship = ContainmentRelationship(
        container=container_id,
        contained_elements=[element_id]
    )
    hierarchy_manager.add_relationship(relationship)

validation_report = hierarchy_manager.validate()
if validation_report.is_valid:
    print("Containment hierarchy is valid")
else:
    print("Containment hierarchy is invalid:", validation_report.messages)
```

## Best Practices

### Logical Structure

- **Use Double Cuts for Implication**: Implication requires two cuts, not one.
- **Maintain Proper Nesting**: Ensure contexts are properly nested.
- **Connect Entities to Predicates**: Entities should be connected to predicates.
- **Use Ligatures for Identity**: Connect entities with ligatures to represent identity.

### Layout Constraints

- **Use Relative Positioning**: Position elements relative to their containers.
- **Set Minimum Spacing**: Ensure elements have enough space between them.
- **Auto-Size Containers**: Let containers size themselves based on their contents.
- **Enforce Containment**: Ensure elements stay within their logical containers.

### Platform Independence

- **Avoid Absolute Coordinates**: Use logical containment instead of absolute coordinates.
- **Use Platform Adapters**: Implement adapters for specific GUI platforms.
- **Test on Multiple Platforms**: Ensure your implementation works across platforms.
- **Handle Different Screen Sizes**: Design for responsiveness.

### Testing

- **Use Corpus Examples**: Test against the corpus of examples.
- **Validate Logical Structure**: Ensure the logical structure is correct.
- **Check Containment Hierarchy**: Validate the containment hierarchy.
- **Test Layout Constraints**: Ensure layout constraints are properly applied.

## Troubleshooting

### Common Issues

- **Element Count Mismatch**: The converter is not generating all expected elements.
- **Context Type Compatibility**: Inconsistency in context types.
- **Parser Issues**: The parser is not correctly parsing the EG-HG files.
- **Containment Hierarchy Validation**: The containment hierarchy is invalid.

### Debugging Tips

- **Check Parser Output**: Verify the parser is correctly parsing the EG-HG files.
- **Validate Containment Hierarchy**: Ensure the containment hierarchy is valid.
- **Test with Simple Examples**: Start with simple examples and gradually increase complexity.
- **Use Detailed Logging**: Add detailed logging to help diagnose issues.

## Conclusion

EGRF v3.0 provides a powerful, platform-independent rendering format for Peirce's Existential Graphs. By following the guidelines in this developer guide, you can effectively work with EGRF v3.0 to create, convert, and validate Existential Graphs.

