# EGRF v3.0 User Guide

## Introduction

The Existential Graph Rendering Format (EGRF) v3.0 is a platform-independent format for representing Peirce's Existential Graphs. This user guide provides a comprehensive overview of how to use EGRF v3.0, including creating, editing, and visualizing Existential Graphs.

## Understanding EGRF v3.0

### What is EGRF v3.0?

EGRF v3.0 is a JSON-based format that represents Existential Graphs using a logical containment model. Unlike previous versions that used absolute coordinates, EGRF v3.0 defines elements by their logical relationships, making it platform-independent and more flexible.

### Key Concepts

- **Logical Containment**: Elements are defined by their logical relationships rather than absolute positions.
- **Platform Independence**: The format works across any GUI platform.
- **Peirce Compliance**: The format enforces Peirce's rules for Existential Graphs.
- **User Freedom**: Users can freely move elements within their logical constraints.
- **Auto-Sizing**: Containers size themselves based on their contents.

### EGRF v3.0 Structure

An EGRF v3.0 document has the following structure:

```json
{
  "metadata": {
    "version": "3.0.0",
    "format": "egrf",
    "id": "example_graph",
    "description": "Example graph"
  },
  "elements": {
    "sheet": { ... },
    "cut1": { ... },
    "predicate1": { ... },
    "entity1": { ... }
  },
  "containment": {
    "cut1": "sheet",
    "predicate1": "sheet",
    "entity1": "cut1"
  },
  "connections": [
    {
      "entity_id": "entity1",
      "predicate_id": "predicate1",
      "role": "arg1"
    }
  ],
  "ligatures": [
    {
      "entity1_id": "entity1",
      "entity2_id": "entity2",
      "type": "identity"
    }
  ],
  "layout_constraints": [
    {
      "element_id": "cut1",
      "constraint_type": "size",
      "width": 300,
      "height": 200
    },
    {
      "element_id": "predicate1",
      "constraint_type": "position",
      "container": "sheet",
      "x": 0.5,
      "y": 0.5,
      "x_unit": "relative",
      "y_unit": "relative"
    }
  ]
}
```

## Creating Existential Graphs

### Basic Elements

EGRF v3.0 supports the following basic elements:

- **Contexts**: Sheets and cuts that define the logical boundaries of the graph.
- **Predicates**: Relations with arity and connection points.
- **Entities**: Lines of identity with path constraints.
- **Ligatures**: Connections between entities across contexts.

### Creating a Simple Graph

Here's how to create a simple graph with a sheet, a cut, a predicate, and an entity:

```json
{
  "metadata": {
    "version": "3.0.0",
    "format": "egrf",
    "id": "simple_graph",
    "description": "Simple graph with one cut, one predicate, and one entity"
  },
  "elements": {
    "sheet": {
      "element_type": "context",
      "logical_properties": {
        "context_type": "sheet_of_assertion",
        "container": "none",
        "is_root": true,
        "nesting_level": 0
      },
      "visual_properties": {
        "name": "Sheet of Assertion"
      }
    },
    "cut1": {
      "element_type": "context",
      "logical_properties": {
        "context_type": "cut",
        "container": "sheet",
        "is_root": false,
        "nesting_level": 1
      },
      "visual_properties": {
        "name": "Cut 1"
      }
    },
    "predicate1": {
      "element_type": "predicate",
      "logical_properties": {
        "arity": 1,
        "container": "sheet"
      },
      "visual_properties": {
        "name": "Person"
      }
    },
    "entity1": {
      "element_type": "entity",
      "logical_properties": {
        "entity_type": "constant",
        "connected_predicates": ["predicate1"]
      },
      "visual_properties": {
        "name": "Socrates"
      }
    }
  },
  "containment": {
    "cut1": "sheet",
    "predicate1": "sheet",
    "entity1": "sheet"
  },
  "connections": [
    {
      "entity_id": "entity1",
      "predicate_id": "predicate1",
      "role": "arg1"
    }
  ],
  "ligatures": [],
  "layout_constraints": [
    {
      "element_id": "sheet",
      "constraint_type": "size",
      "width": 800,
      "height": 600
    },
    {
      "element_id": "cut1",
      "constraint_type": "size",
      "width": 300,
      "height": 200
    },
    {
      "element_id": "predicate1",
      "constraint_type": "size",
      "width": 100,
      "height": 50
    },
    {
      "element_id": "entity1",
      "constraint_type": "size",
      "width": 10,
      "height": 10
    },
    {
      "element_id": "cut1",
      "constraint_type": "position",
      "container": "sheet",
      "x": 0.5,
      "y": 0.5,
      "x_unit": "relative",
      "y_unit": "relative"
    },
    {
      "element_id": "predicate1",
      "constraint_type": "position",
      "container": "sheet",
      "x": 0.3,
      "y": 0.3,
      "x_unit": "relative",
      "y_unit": "relative"
    },
    {
      "element_id": "entity1",
      "constraint_type": "position",
      "container": "sheet",
      "x": 0.3,
      "y": 0.4,
      "x_unit": "relative",
      "y_unit": "relative"
    }
  ]
}
```

### Creating an Implication

Implication in Existential Graphs requires a double-cut structure. Here's how to create an implication "If Socrates is a person, then Socrates is mortal":

```json
{
  "metadata": {
    "version": "3.0.0",
    "format": "egrf",
    "id": "implication_graph",
    "description": "If Socrates is a person, then Socrates is mortal"
  },
  "elements": {
    "sheet": {
      "element_type": "context",
      "logical_properties": {
        "context_type": "sheet_of_assertion",
        "container": "none",
        "is_root": true,
        "nesting_level": 0
      },
      "visual_properties": {
        "name": "Sheet of Assertion"
      }
    },
    "outer_cut": {
      "element_type": "context",
      "logical_properties": {
        "context_type": "cut",
        "container": "sheet",
        "is_root": false,
        "nesting_level": 1
      },
      "visual_properties": {
        "name": "Outer Cut"
      }
    },
    "inner_cut": {
      "element_type": "context",
      "logical_properties": {
        "context_type": "cut",
        "container": "outer_cut",
        "is_root": false,
        "nesting_level": 2
      },
      "visual_properties": {
        "name": "Inner Cut"
      }
    },
    "person_predicate": {
      "element_type": "predicate",
      "logical_properties": {
        "arity": 1,
        "container": "outer_cut"
      },
      "visual_properties": {
        "name": "Person"
      }
    },
    "mortal_predicate": {
      "element_type": "predicate",
      "logical_properties": {
        "arity": 1,
        "container": "inner_cut"
      },
      "visual_properties": {
        "name": "Mortal"
      }
    },
    "socrates1": {
      "element_type": "entity",
      "logical_properties": {
        "entity_type": "constant",
        "connected_predicates": ["person_predicate"]
      },
      "visual_properties": {
        "name": "Socrates"
      }
    },
    "socrates2": {
      "element_type": "entity",
      "logical_properties": {
        "entity_type": "constant",
        "connected_predicates": ["mortal_predicate"]
      },
      "visual_properties": {
        "name": "Socrates"
      }
    }
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
    // Layout constraints omitted for brevity
  ]
}
```

## Editing Existential Graphs

### Moving Elements

In EGRF v3.0, elements can be moved freely within their logical containers. This is achieved by updating the position constraints:

```json
{
  "element_id": "predicate1",
  "constraint_type": "position",
  "container": "sheet",
  "x": 0.4,  // Updated x position
  "y": 0.5,  // Updated y position
  "x_unit": "relative",
  "y_unit": "relative"
}
```

### Resizing Elements

Elements can be resized by updating the size constraints:

```json
{
  "element_id": "cut1",
  "constraint_type": "size",
  "width": 400,  // Updated width
  "height": 300,  // Updated height
  "min_width": 100,
  "min_height": 100,
  "max_width": 1000,
  "max_height": 1000,
  "auto_size": true
}
```

### Adding Elements

To add a new element to an existing graph:

1. Add the element to the `elements` section.
2. Add the containment relationship to the `containment` section.
3. Add any connections to the `connections` section.
4. Add any ligatures to the `ligatures` section.
5. Add layout constraints to the `layout_constraints` section.

```json
// Add a new predicate
"predicate2": {
  "element_type": "predicate",
  "logical_properties": {
    "arity": 1,
    "container": "sheet"
  },
  "visual_properties": {
    "name": "Teacher"
  }
}

// Add containment relationship
"predicate2": "sheet"

// Add connection
{
  "entity_id": "entity1",
  "predicate_id": "predicate2",
  "role": "arg1"
}

// Add layout constraints
{
  "element_id": "predicate2",
  "constraint_type": "size",
  "width": 100,
  "height": 50
},
{
  "element_id": "predicate2",
  "constraint_type": "position",
  "container": "sheet",
  "x": 0.7,
  "y": 0.3,
  "x_unit": "relative",
  "y_unit": "relative"
}
```

### Removing Elements

To remove an element from an existing graph:

1. Remove the element from the `elements` section.
2. Remove the containment relationship from the `containment` section.
3. Remove any connections from the `connections` section.
4. Remove any ligatures from the `ligatures` section.
5. Remove layout constraints from the `layout_constraints` section.

## Visualizing Existential Graphs

### Platform-Independent Visualization

EGRF v3.0 is designed to be platform-independent, meaning it can be visualized on any GUI platform. The layout constraints provide guidance on how to position and size elements, but the actual rendering is left to the platform.

### Layout Constraints

Layout constraints provide guidance on how to position and size elements:

- **Size Constraints**: Control the dimensions of elements.
- **Position Constraints**: Position elements relative to their containers.
- **Spacing Constraints**: Maintain spacing between elements.
- **Alignment Constraints**: Align elements with each other.
- **Containment Constraints**: Ensure elements stay within their logical containers.

### Auto-Sizing

Containers can auto-size themselves based on their contents:

```json
{
  "element_id": "cut1",
  "constraint_type": "size",
  "width": 300,
  "height": 200,
  "min_width": 100,
  "min_height": 100,
  "max_width": 1000,
  "max_height": 1000,
  "auto_size": true
}
```

### User Interaction

Users can interact with the graph by:

- **Moving Elements**: Elements can be moved freely within their logical containers.
- **Resizing Elements**: Elements can be resized within their constraints.
- **Adding Elements**: New elements can be added to the graph.
- **Removing Elements**: Elements can be removed from the graph.

## Best Practices

### Logical Structure

- **Use Double Cuts for Implication**: Implication requires two cuts, not one.
- **Maintain Proper Nesting**: Ensure contexts are properly nested.
- **Connect Entities to Predicates**: Entities should be connected to predicates.
- **Use Ligatures for Identity**: Connect entities with ligatures to represent identity.

### Layout

- **Use Relative Positioning**: Position elements relative to their containers.
- **Set Minimum Spacing**: Ensure elements have enough space between them.
- **Auto-Size Containers**: Let containers size themselves based on their contents.
- **Enforce Containment**: Ensure elements stay within their logical containers.

### Platform Independence

- **Avoid Absolute Coordinates**: Use logical containment instead of absolute coordinates.
- **Use Platform Adapters**: Implement adapters for specific GUI platforms.
- **Test on Multiple Platforms**: Ensure your implementation works across platforms.
- **Handle Different Screen Sizes**: Design for responsiveness.

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

EGRF v3.0 provides a powerful, platform-independent rendering format for Peirce's Existential Graphs. By following the guidelines in this user guide, you can effectively create, edit, and visualize Existential Graphs using EGRF v3.0.

