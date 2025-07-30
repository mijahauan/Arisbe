# Existential Graphs Application - Usage Examples

This document provides detailed examples of using the Existential Graphs application.

## Getting Started

### Basic EGIF Loading and Display

```bash
# Start the CLI
python3 egi_cli.py

# Load a simple relation
EG> load (phoenix *x)
Loaded: (phoenix *x)
Parsed: 1 vertices, 1 edges, 0 cuts

# Show current state
EG> show
Current EGIF: (phoenix *x)
Structure: 1 vertices, 1 edges, 0 cuts
```

### Working with Multiple Relations

```bash
# Load multiple relations sharing a variable
EG> load (man *x) (human x) (mortal x)
Loaded: (man *x) (human x) (mortal x)
Parsed: 1 vertices, 3 edges, 0 cuts

# Show as YAML to see internal structure
EG> yaml
Current EGI as YAML:
alphabet:
  constants: []
  relations:
  - human
  - man
  - mortal
  variables: []
vertices:
  vertex_abc123:
    context_id: sheet_def456
    is_constant: false
    properties: {}
edges:
  edge_789xyz:
    context_id: sheet_def456
    incident_vertices:
    - vertex_abc123
    is_identity: false
    properties: {}
    relation_name: man
  # ... more edges
```

## Transformation Examples

### Erasure Transformations

```bash
# Load a graph with multiple relations
EG> load (man *x) (human x) (mortal x)

# Erase the "man" relation using markup
EG> transform ^(man *x)^ (human x) (mortal x)
Clean EGIF: (man *x) (human x) (mortal x)
Found 1 markup instruction(s)
Applying erase...
Erased element: (man *x)
Result: (human *x) (mortal x)

# Show the result
EG> show
Current EGIF: (human *x) (mortal x)
Structure: 1 vertices, 2 edges, 0 cuts
```

### Working with Negation

```bash
# Load a negated statement
EG> load ~[ (mortal *x) ]

# Try to erase from negative context (this will fail)
EG> transform ^(mortal *x)^
Clean EGIF: (mortal *x)
Found 1 markup instruction(s)
Applying erase...
Transformation failed: Cannot erase from negative context

# This is correct behavior - erasure only works in positive contexts
```

### Double Cut Operations

```bash
# Load a simple relation
EG> load (phoenix *x)

# The CLI doesn't yet support double cut addition markup,
# but we can demonstrate it programmatically:
```

```python
from egif_parser import parse_egif
from egi_transformations import EGITransformer, TransformationRule
from egif_generator import generate_egif

# Parse the graph
egi = parse_egif("(phoenix *x)")

# Add double cut
transformer = EGITransformer(egi)
new_egi = transformer.apply_transformation(
    TransformationRule.DOUBLE_CUT_ADDITION,
    target_context_id=egi.sheet_id
)

# Show result
result = generate_egif(new_egi)
print(result)  # Output: (phoenix *x) [If  [Then  ] ]
```

## Advanced Examples

### Constants and Quoted Strings

```bash
# Load relations with constants
EG> load (loves "Socrates" "Plato")
Loaded: (loves "Socrates" "Plato")
Parsed: 2 vertices, 1 edges, 0 cuts

# Constants are preserved in transformations
EG> show
Current EGIF: (loves "Socrates" "Plato")
```

### Complex Nested Structures

```bash
# Load a scroll pattern (If-Then)
EG> load [If (thunder *x) [Then (lightning *y) ] ]
Loaded: [If (thunder *x) [Then (lightning *y) ] ]
Parsed: 2 vertices, 2 edges, 2 cuts

# Show structure
EG> show
Current EGIF: [If (thunder *x) [Then (lightning *y) ] ]
Structure: 2 vertices, 2 edges, 2 cuts
```

### Coreference Patterns

```bash
# Load explicit coreference
EG> load [*x *y] (P x) (Q y)
Loaded: [*x *y] (P x) (Q y)
Parsed: 2 vertices, 3 edges, 0 cuts

# The generator may reorder for clarity
EG> show
Current EGIF: (P *x) (Q *y) [x y]
Structure: 2 vertices, 3 edges, 0 cuts
```

## File Operations

### Saving and Loading YAML

```bash
# Load a graph
EG> load (man *x) (human x) (mortal x)

# Save to file
EG> save example.yaml
Saved to example.yaml

# Exit and restart
EG> exit

# Load from file
python3 egi_cli.py --yaml example.yaml
Loaded from example.yaml
EGIF: (man *x) (human x) (mortal x)
```

### Command Line Processing

```bash
# Process transformations from command line
python3 egi_cli.py \
  --egif "(man *x) (human x) (mortal x)" \
  --transform "^(man *x)^ (human x) (mortal x)"

# Output:
# Loaded: (man *x) (human x) (mortal x)
# Parsed: 1 vertices, 3 edges, 0 cuts
# Clean EGIF: (man *x) (human x) (mortal x)
# Found 1 markup instruction(s)
# Applying erase...
# Erased element: (man *x)
# Result: (human *x) (mortal x)
# Current EGIF: (human *x) (mortal x)
# Structure: 1 vertices, 2 edges, 0 cuts
```

## Programmatic Usage

### Basic Pipeline

```python
from egif_parser import parse_egif
from egif_generator import generate_egif
from egi_yaml import serialize_egi_to_yaml, deserialize_egi_from_yaml

# Parse EGIF
egi = parse_egif("(man *x) (human x)")

# Convert to YAML
yaml_str = serialize_egi_to_yaml(egi)
print(yaml_str)

# Convert back
egi2 = deserialize_egi_from_yaml(yaml_str)

# Generate EGIF
egif = generate_egif(egi2)
print(egif)  # Output: (man *x) (human x)
```

### Applying Transformations

```python
from egi_transformations import EGITransformer, TransformationRule

# Parse graph
egi = parse_egif("(man *x) (human x) (mortal x)")

# Create transformer
transformer = EGITransformer(egi)

# Get first edge to erase
edge_id = next(iter(egi.edges.keys()))

# Apply erasure
new_egi = transformer.apply_transformation(
    TransformationRule.ERASURE,
    element_id=edge_id
)

# Show result
result = generate_egif(new_egi)
print(result)  # Output: (human *x) (mortal x) or similar
```

### Validation

```python
# Check if transformation is valid before applying
is_valid = transformer.validate_transformation(
    TransformationRule.ERASURE,
    element_id=edge_id
)

if is_valid:
    new_egi = transformer.apply_transformation(
        TransformationRule.ERASURE,
        element_id=edge_id
    )
else:
    print("Transformation not valid")
```

## Error Handling Examples

### Invalid EGIF Syntax

```bash
EG> load (invalid syntax
Failed to load EGIF: Unexpected token at position 15: expected ')' but found end of input
```

### Invalid Transformations

```bash
# Try to erase from negative context
EG> load ~[ (man *x) ]
EG> transform ^(man *x)^
Transformation failed: Cannot erase from negative context
```

### Missing Elements

```bash
EG> load (phoenix *x)
EG> transform ^(nonexistent *y)^
Element not found: (nonexistent *y)
```

## Testing Examples

### Running Tests

```bash
# Test the complete pipeline
python3 test_complete_pipeline.py

# Output:
# Running comprehensive Existential Graphs pipeline tests...
# Testing basic pipeline...
#   ✓ (phoenix *x) -> (phoenix *x)
#   ✓ ~[ (phoenix *x) ] -> ~[ (phoenix *x) ]
#   ... more tests ...
# 🎉 All comprehensive pipeline tests passed!
```

### Custom Test Cases

```python
# Create custom test
from egif_parser import parse_egif
from egif_generator import generate_egif

def test_my_case():
    egif = "(my_relation *x *y)"
    egi = parse_egif(egif)
    generated = generate_egif(egi)
    assert egif == generated
    print("✓ My test passed")

test_my_case()
```

## Performance Examples

### Large Graphs

```python
# Create a larger graph
relations = [f"(R{i} *x{i})" for i in range(100)]
egif = " ".join(relations)

# Parse and process
egi = parse_egif(egif)
print(f"Parsed {len(egi.edges)} edges and {len(egi.vertices)} vertices")

# Generate back
generated = generate_egif(egi)
print(f"Generated EGIF with {len(generated.split())} tokens")
```

### Batch Processing

```python
# Process multiple graphs
test_cases = [
    "(phoenix *x)",
    "(man *x) (human x)",
    "~[ (mortal *x) ]",
    '[If (A *x) [Then (B x) ] ]'
]

for egif in test_cases:
    egi = parse_egif(egif)
    generated = generate_egif(egi)
    print(f"{egif} -> {generated}")
```

## Integration Examples

### With Other Systems

```python
# Convert to different formats (conceptual)
def egi_to_prolog(egi):
    """Convert EGI to Prolog-like format."""
    clauses = []
    for edge in egi.edges.values():
        if not edge.is_identity:
            args = [f"X{i}" for i in range(len(edge.incident_vertices))]
            clause = f"{edge.relation_name}({', '.join(args)})"
            clauses.append(clause)
    return clauses

# Usage
egi = parse_egif("(man *x) (human x)")
prolog_clauses = egi_to_prolog(egi)
print(prolog_clauses)  # ['man(X0)', 'human(X0)']
```

### Workflow Automation

```python
# Automated transformation workflow
def apply_workflow(egif, transformations):
    """Apply a series of transformations."""
    egi = parse_egif(egif)
    
    for transform in transformations:
        transformer = EGITransformer(egi)
        egi = transformer.apply_transformation(**transform)
    
    return generate_egif(egi)

# Usage
workflow = [
    {'rule': TransformationRule.DOUBLE_CUT_ADDITION, 'target_context_id': 'sheet_id'},
    {'rule': TransformationRule.ISOLATED_VERTEX_ADDITION, 'target_context_id': 'sheet_id'}
]

result = apply_workflow("(phoenix *x)", workflow)
print(result)
```

This completes the usage examples. The application provides a robust foundation for working with Existential Graphs in both interactive and programmatic contexts.

