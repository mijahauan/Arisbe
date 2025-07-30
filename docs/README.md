# Existential Graphs Application

A mathematically rigorous implementation of Existential Graphs based on Frithjof Dau's formalism, featuring all 8 canonical transformation rules, EGIF parsing, EGI property hypergraph representation, and a command-line interface.

## Overview

This application implements a complete pipeline for processing Existential Graphs:

1. **EGIF Parser**: Converts EGIF (Existential Graph Interchange Format) expressions to EGI (Existential Graph Instance) representations
2. **EGI Core**: Property hypergraph model implementing Dau's canonical form
3. **Transformation Rules**: All 8 canonical transformation rules with rigorous validation
4. **YAML Serialization**: Persistent storage and interchange format
5. **EGIF Generator**: Converts EGI back to EGIF expressions
6. **Command-Line Interface**: Interactive tool with markup parsing for rule application

## Architecture

### Core Components

- **`egi_core.py`**: Core EGI data structures (vertices, edges, cuts, contexts)
- **`egif_parser.py`**: EGIF lexer and parser
- **`egif_generator.py`**: EGI to EGIF conversion
- **`egi_yaml.py`**: YAML serialization/deserialization
- **`egi_transformations.py`**: Implementation of 8 canonical transformation rules
- **`egi_cli.py`**: Command-line interface with markup parsing

### Data Model

The application uses a property hypergraph model where:

- **Vertices** represent individuals (variables or constants)
- **Edges** represent relations with incident vertices
- **Cuts** represent negation contexts
- **Contexts** define the scope and polarity (positive/negative)

## Transformation Rules

The application implements all 8 canonical transformation rules from Dau's formalism:

1. **Erasure**: Remove elements from positive contexts
2. **Insertion**: Add elements to negative contexts
3. **Iteration**: Copy vertices from outer to inner contexts
4. **De-iteration**: Remove copied vertices from inner contexts
5. **Double Cut Addition**: Add nested empty cuts
6. **Double Cut Removal**: Remove nested empty cuts
7. **Isolated Vertex Addition**: Add isolated vertices
8. **Isolated Vertex Removal**: Remove isolated vertices

## Usage

### Command Line Interface

#### Basic Usage

```bash
# Start interactive mode
python3 egi_cli.py

# Load and transform in one command
python3 egi_cli.py --egif "(man *x) (human x)" --transform "^(man *x)^ (human x)"

# Load from YAML file
python3 egi_cli.py --yaml example.yaml
```

#### Interactive Commands

```
EG> load (man *x) (human x)          # Load EGIF expression
EG> show                             # Show current EGIF
EG> transform ^(man *x)^ (human x)   # Apply transformation with markup
EG> undo                             # Undo last transformation
EG> yaml                             # Show as YAML
EG> save example.yaml                # Save to YAML file
EG> help                             # Show help
EG> exit                             # Exit application
```

### Markup Syntax

The application supports markup annotations for specifying transformations:

- **`^element^`**: Mark element for erasure
  - Example: `^(man *x)^` erases the relation "(man *x)"
  
- **`^~[[^content]]`**: Mark double cut for removal
  - Example: `^~[[^]]` removes empty double cut

### EGIF Syntax

The application supports the full EGIF syntax:

#### Basic Relations
```
(phoenix *x)                    # Unary relation
(loves *x *y)                   # Binary relation
(between *x *y *z)              # Ternary relation
```

#### Constants
```
(loves "Socrates" "Plato")      # Constants in quotes
(age "John" 25)                 # Mixed constants and numbers
```

#### Variables and Coreference
```
(man *x) (human x)              # Defining and bound variables
[*x *y] (P x) (Q y)             # Explicit coreference
```

#### Negation
```
~[ (mortal *x) ]                # Simple negation
~[ (A *x) ~[ (B x) ] ]          # Nested negation
```

#### Scroll Patterns (If-Then)
```
[If (thunder *x) [Then (lightning *y) ] ]
```

## Examples

### Basic Transformation

```bash
# Load a graph
python3 egi_cli.py --egif "(man *x) (mortal x) (human x)"

# Erase the "man" relation
python3 egi_cli.py --egif "(man *x) (mortal x) (human x)" --transform "^(man *x)^ (mortal x) (human x)"
# Result: (mortal *x) (human x)
```

### Working with Negation

```bash
# Load a negated graph
EG> load ~[ (phoenix *x) ]

# Cannot erase from negative context (will show error)
EG> transform ^(phoenix *x)^
```

### Complex Structures

```bash
# Load a scroll pattern
EG> load [If (thunder *x) [Then (lightning *y) ] ]

# Show structure
EG> show
# Current EGIF: [If (thunder *x) [Then (lightning *y) ] ]
# Structure: 2 vertices, 2 edges, 2 cuts
```

## API Usage

### Programmatic Access

```python
from egif_parser import parse_egif
from egif_generator import generate_egif
from egi_transformations import EGITransformer, TransformationRule

# Parse EGIF
egi = parse_egif("(man *x) (human x)")

# Apply transformation
transformer = EGITransformer(egi)
new_egi = transformer.apply_transformation(
    TransformationRule.ERASURE, 
    element_id=edge_id
)

# Generate EGIF
result = generate_egif(new_egi)
```

### YAML Serialization

```python
from egi_yaml import serialize_egi_to_yaml, deserialize_egi_from_yaml

# Serialize to YAML
yaml_str = serialize_egi_to_yaml(egi)

# Deserialize from YAML
egi = deserialize_egi_from_yaml(yaml_str)
```

## Testing

The application includes comprehensive test suites:

```bash
# Test individual components
python3 test_egif_parser.py
python3 test_egi_yaml.py
python3 test_egif_generator.py
python3 test_egi_transformations.py

# Test CLI functionality
python3 test_cli.py

# Test complete pipeline
python3 test_complete_pipeline.py
```

## File Structure

```
├── egi_core.py                 # Core EGI data structures
├── egif_parser.py              # EGIF parser implementation
├── egif_generator.py           # EGI to EGIF generator
├── egi_yaml.py                 # YAML serialization
├── egi_transformations.py      # Transformation rules
├── egi_cli.py                  # Command-line interface
├── test_*.py                   # Test suites
├── dau_formalism_analysis.md   # Analysis of Dau's formalism
├── egi_data_model_specification.md  # Data model specification
└── README.md                   # This file
```

## Mathematical Foundation

This implementation is based on Frithjof Dau's rigorous mathematical formalization of Existential Graphs, which provides:

- Precise definitions of EG and EGI structures
- Formal specification of the 8 canonical transformation rules
- Mathematical validation conditions for each transformation
- Support for constants and function-like relations
- Property hypergraph representation for computational efficiency

## Features

### ✅ Implemented Features

- Complete EGIF parser with error handling
- EGI property hypergraph representation
- All 8 canonical transformation rules
- YAML serialization/deserialization
- EGIF generator with proper label scoping
- Command-line interface with markup parsing
- Comprehensive test suites
- Support for constants and functions
- Nested cuts and scroll patterns
- Transformation validation
- Undo functionality

### 🔄 Future Enhancements

- Graphical visualization of EGI structures
- Additional markup syntax for other transformation rules
- Performance optimizations for large graphs
- Integration with theorem provers
- Web-based interface
- Import/export to other logical formats (CLIF, FOPL)

## Error Handling

The application provides informative error messages for:

- Invalid EGIF syntax
- Malformed expressions
- Invalid transformations (e.g., erasing from negative context)
- Missing elements in markup
- File I/O errors

## Performance

The application is designed for efficiency:

- Property hypergraph representation for fast lookups
- Incremental transformation application
- Memory-efficient YAML serialization
- Optimized parsing with proper error recovery

## Contributing

The codebase is well-documented and modular, making it easy to extend:

- Add new transformation rules in `egi_transformations.py`
- Extend EGIF syntax in `egif_parser.py`
- Add new output formats by following the `egif_generator.py` pattern
- Enhance the CLI with new commands in `egi_cli.py`

## License

This implementation is provided for educational and research purposes, based on the mathematical foundations established by Frithjof Dau and the Existential Graphs tradition initiated by Charles Sanders Peirce.

