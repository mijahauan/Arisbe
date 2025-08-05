# Arisbe: Existential Graphs Implementation

A research implementation of Charles Sanders Peirce's Existential Graphs based on Frithjof Dau's mathematical formalism. This project provides tools for parsing, manipulating, and visualizing Existential Graph diagrams with a focus on mathematical rigor and educational applications.

## Project Status

**Core Foundation: Functional**
- ✅ EGIF (Existential Graph Interchange Format) parsing and generation
- ✅ EGI (Existential Graph Instance) data structures following Dau's 6+1 component model
- ✅ Round-trip conversion between EGIF text and EGI structures
- ✅ Graphviz-based layout engine for diagram visualization
- ✅ PySide6-based rendering pipeline

**GUI Application: In Development**
- 🔄 Interactive diagram editor ("Bullpen") with Warmup and Practice modes
- 🔄 Transformation rule implementation and validation
- ❌ Endoporeutic Game framework (planned)
- ❌ Complete integrated application

## Architecture

### Core Components

**Mathematical Foundation:**
- `egi_core_dau.py` - Dau's 6+1 component RelationalGraphWithCuts model
- `egif_parser_dau.py` - EGIF lexer and parser with syntax validation
- `egif_generator_dau.py` - EGI to EGIF conversion with proper formatting

**Visualization Pipeline:**
- `graphviz_layout_engine_v2.py` - Layout engine using Graphviz DOT with cluster support
- `pyside6_backend.py` - Professional-quality rendering using PySide6/Qt
- `diagram_renderer_dau.py` - Diagram rendering with Dau's visual conventions

**Interactive Editor:**
- `eg_editor_integrated.py` - Main editor interface
- `warmup_mode_controller.py` - Warmup mode for free-form diagram creation
- `arisbe_gui.py` - GUI framework and application shell

### Data Model

Follows Dau's formal definition of Relational Graphs with Cuts:

1. **V** - Finite set of vertices (individuals: variables `*x` or constants `"Socrates"`)
2. **E** - Finite set of edges (relations with specified arity)
3. **ν** - Nu mapping from edges to vertex sequences (argument structure)
4. **⊤** - Sheet of assertion (outermost context)
5. **Cut** - Finite set of cuts (negation contexts)
6. **area** - Containment mapping (which elements are in which contexts)
7. **rel** - Relation names mapping (edge labels)

## Current Capabilities

### EGIF Parsing and Generation

**Parse EGIF expressions into EGI structures:**
```python
from egif_parser_dau import parse_egif

# Parse basic relations
graph = parse_egif('(Human "Socrates")')

# Parse with cuts (negation)
graph = parse_egif('*x ~[ (Mortal x) ]')

# Parse complex nested structures
graph = parse_egif('*x (Human x) ~[ (Mortal x) ~[ (Wise x) ] ]')
```

**Generate EGIF from EGI structures:**
```python
from egif_generator_dau import generate_egif

egif_text = generate_egif(graph)
print(egif_text)  # Output: *x (Human x) ~[ (Mortal x) ]
```

### Diagram Visualization

**Create visual diagrams from EGIF:**
```python
from egif_parser_dau import parse_egif
from graphviz_layout_engine_v2 import GraphvizLayoutEngine
from pyside6_backend import PySide6Renderer

# Parse and layout
graph = parse_egif('*x ~[ (Human x) ] ~[ (Mortal x) ]')
engine = GraphvizLayoutEngine()
layout = engine.create_layout_from_graph(graph)

# Render to file
renderer = PySide6Renderer()
renderer.render_to_file(layout, 'diagram.png')
```

### Interactive Editor (In Development)

**Bullpen Editor with two modes:**

1. **Warmup Mode**: Free-form diagram creation and editing
   - Direct manipulation of cuts, predicates, and lines of identity
   - Real-time syntax validation
   - Visual feedback for logical correctness

2. **Practice Mode**: Rule-based transformations (planned)
   - Step-by-step application of Peirce's transformation rules
   - Proof validation and tracking
   - Educational scaffolding

### EGIF Syntax Reference

**Supported Elements:**

```
# Relations (predicates)
(Human "Socrates")              # Unary relation with constant
(Loves *x *y)                   # Binary relation with variables
(Between *x *y *z)              # Ternary relation

# Variables
*x                              # Defining variable (existential quantification)
x                               # Bound variable (reference to *x)

# Constants
"Socrates"                      # String constant

# Cuts (negation contexts)
~[ (Mortal *x) ]                # Simple cut
~[ (A *x) ~[ (B x) ] ]          # Nested cuts

# Isolated vertices (heavy dots)
*x                              # Isolated defining variable
"Socrates"                      # Isolated constant
```

## Installation and Setup

### Requirements

```bash
# Install dependencies
pip install -r requirements.txt
```

**Core dependencies:**
- `PyYAML>=6.0` - YAML serialization
- `frozendict>=2.3.0` - Immutable dictionaries for EGI structures
- `PySide6>=6.5.0` - GUI framework and rendering
- `graphviz` - Layout engine (system package)

### System Requirements

**Graphviz Installation:**
```bash
# macOS
brew install graphviz

# Ubuntu/Debian
sudo apt-get install graphviz

# Windows
# Download from https://graphviz.org/download/
```

## Usage Examples

### Basic Parsing and Visualization

```python
#!/usr/bin/env python3
from egif_parser_dau import parse_egif
from graphviz_layout_engine_v2 import GraphvizLayoutEngine

# Parse an EGIF expression
egif_text = '*x (Human x) ~[ (Mortal x) ]'
graph = parse_egif(egif_text)

# Create layout
engine = GraphvizLayoutEngine()
layout = engine.create_layout_from_graph(graph)

# Print layout information
print(f"Generated layout with {len(layout.primitives)} elements")
for elem_id, primitive in layout.primitives.items():
    print(f"  {elem_id}: {primitive.element_type} at {primitive.position}")
```

### Round-trip Conversion

```python
from egif_parser_dau import parse_egif
from egif_generator_dau import generate_egif

# Original EGIF
original = '*x ~[ (Human x) ] ~[ (Mortal x) ]'

# Parse to EGI
graph = parse_egif(original)

# Generate back to EGIF
regenerated = generate_egif(graph)

print(f"Original:    {original}")
print(f"Regenerated: {regenerated}")
# Should be logically equivalent
## Development Status and Roadmap

### Completed Components ✅
- **Core EGI Model**: Dau's 6+1 component RelationalGraphWithCuts implementation
- **EGIF Parser**: Robust parsing with syntax validation and error reporting
- **EGIF Generator**: Round-trip conversion maintaining logical equivalence
- **Layout Engine**: Graphviz-based layout with proper cut containment
- **Rendering Pipeline**: PySide6-based professional diagram output
- **Test Coverage**: Comprehensive test suites for core functionality

### In Progress 🔄
- **Interactive Editor**: Bullpen interface with Warmup mode partially implemented
- **GUI Integration**: Application shell and mode switching framework
- **Validation System**: Real-time syntax and semantic validation

### Planned Features 📋
- **Practice Mode**: Rule-based transformation interface
- **Endoporeutic Game**: Educational game framework
- **Transformation Rules**: Integration of Peirce's canonical rules
- **Export/Import**: Enhanced file format support

## Project Structure

```
src/
├── egi_core_dau.py                    # Core EGI data structures (Dau's model)
├── egif_parser_dau.py                 # EGIF parser with validation
├── egif_generator_dau.py              # EGI to EGIF conversion
├── graphviz_layout_engine_v2.py       # Layout engine using Graphviz
├── pyside6_backend.py                 # PySide6 rendering backend
├── eg_editor_integrated.py            # Main editor interface
├── warmup_mode_controller.py          # Warmup mode implementation
├── arisbe_gui.py                      # Application framework
└── test_*.py                          # Test suites

corpus/
├── corpus/                            # Example EG expressions
└── README.md                          # Corpus documentation

docs/
├── references/                        # Academic references
└── specifications/                    # Technical specifications
```

## Mathematical Foundation

This implementation follows Frithjof Dau's mathematical formalization from "Mathematical Logic with Diagrams" (2003), providing:

- **Formal EGI Definition**: 6+1 component model (V, E, ν, ⊤, Cut, area, rel)
- **Rigorous Constraints**: All formal constraints from Definition 12.1
- **Area Containment**: Proper hierarchical context management
- **Nu Mapping**: Precise argument structure for relations
- **Cut Semantics**: Mathematically sound negation contexts

## Contributing

This is a research project focused on mathematical rigor and educational applications. The codebase emphasizes:

- **Mathematical Correctness**: All implementations follow formal specifications
- **Educational Value**: Clear documentation and pedagogical design
- **Code Quality**: Comprehensive testing and clean architecture
- **Academic Standards**: Proper attribution and reference to source materials

## License

MIT License - See LICENSE file for details.

## References

- Dau, Frithjof. "Mathematical Logic with Diagrams." 2003.
- Peirce, Charles Sanders. "Existential Graphs." Collected Papers.
- Sowa, John F. "Existential Graphs: MS 514 by Charles Sanders Peirce." 2007.

## Contact

This project is part of ongoing research in diagrammatic reasoning and logic education.

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

