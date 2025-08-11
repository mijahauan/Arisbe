# Arisbe: Existential Graphs Implementation

A mathematically rigorous implementation of Charles Sanders Peirce's Existential Graphs based on Frithjof Dau's formal mathematical framework. Arisbe provides a complete pipeline for creating, editing, transforming, and visualizing Existential Graph diagrams with strict adherence to logical formalism and Peircean conventions.

## Project Status

**Phase 1: Mathematical Foundation - COMPLETE ✅**
- ✅ **EGIF Compliance**: Full Sowa-compliant EGIF parsing and generation
- ✅ **EGI Core**: Dau's 6+1 component RelationalGraphWithCuts model
- ✅ **Round-trip Pipeline**: EGIF ↔ EGI ↔ EGDF with contract validation
- ✅ **API Contracts**: Strict input/output validation and error handling
- ✅ **Dual Format Support**: JSON (automation) and YAML (academic) EGDF formats
- ✅ **Layout Engine**: Graphviz-based hierarchical layout with Dau's conventions
- ✅ **Mathematical Rigor**: All transformations preserve logical structure

**Phase 2: Interactive GUI - IN DEVELOPMENT 🔄**
- ✅ **Visual Rendering**: EGI → Diagram rendering with PySide6
- ✅ **Basic Interaction**: Selection, hover effects, mouse interaction
- 🔄 **Selection Overlays**: Context-sensitive visual feedback (current focus)
- 🔄 **Context Actions**: Element-specific operations and transformations
- ❌ **Dynamic Effects**: Smooth animations and real-time validation
- ❌ **Mode Switching**: Warmup (compositional) vs Practice (rule-based) modes

**Phase 3: Advanced Features - PLANNED ❌**
- ❌ **Browser**: Universe of Discourse and corpus exploration
- ❌ **Endoporeutic Game**: Formal game implementation
- ❌ **Corpus Integration**: Authoritative examples from Peirce, Dau, Sowa
- ❌ **Advanced Transformations**: Complete rule set with validation

## Canonical Layout Pipeline (Clean, Deterministic)

Arisbe provides a canonical, deterministic pipeline that preserves Graphviz cluster bounding boxes exactly for cut layout. Use this mode for validation, debugging, and any path where strict containment and non-overlap must be guaranteed.

• __Env guard__: set `ARISBE_CANONICAL=1` to force canonical mode globally.

```bash
# macOS/Linux (bash/zsh)
export ARISBE_CANONICAL=1

# Windows (PowerShell)
$env:ARISBE_CANONICAL=1
```

• __Engine mode__: Canonical modes are `default-nopp` (and `default_raw`). In these modes, the layout engine:
  - Parses xdot cluster `_bb` and creates cut primitives strictly from clusters.
  - Skips any post-processing that could mutate bounds.
  - Asserts (fail-fast) that every `cut` primitive `bounds` equals its cluster `_bb`.

• __Renderer__: The minimal renderer applies only uniform scale+translate, with inset strokes and debug overlays:
  - Red dashed hairlines = exact Graphviz `_bb` for each cut (live drift canary)
  - Subtle fills by depth; no root fill; label halos for readability

• __Core scripts__:
  - `scripts/render_minimal_cuts.py` → Renders reference cases to `out_minimal/*.svg`
  - `scripts/print_cut_hierarchy.py` → Verifies parent/child containment from cluster bboxes
  - `scripts/check_rendered_overlap.py` → Asserts no sibling overlap after the exact SVG transform
  - `scripts/assert_strict_cut_containment.py` → Asserts strict containment and invariants

Run the checks:

```bash
python scripts/render_minimal_cuts.py
python scripts/check_rendered_overlap.py
python scripts/assert_strict_cut_containment.py  # if present in your branch
```

These safeguards prevent hidden mutations and ensure the canonical pipeline remains deterministic and auditable.

## Architecture

### Phase 1: Mathematical Foundation (Complete)

**Core Data Model:**
- `egi_core_dau.py` - Dau's 6+1 component RelationalGraphWithCuts model
- `egif_parser_dau.py` - Sowa-compliant EGIF lexer and parser
- `egif_generator_dau.py` - EGI to EGIF conversion with strict label scoping
- `egdf_parser.py` - EGDF format with dual JSON/YAML support and API contracts

**Layout and Rendering Pipeline:**
- `layout_engine.py` - Abstract layout interface with contract validation
- `graphviz_layout_engine_v2.py` - Hierarchical layout using Graphviz clusters
- `pyside6_backend.py` - High-quality vector rendering with Qt
- `clean_diagram_renderer.py` - Dau convention compliance (heavy lines, fine cuts)

**Validation and Contracts:**
- `api_contracts.py` - Comprehensive contract system for all pipeline stages
- `test_*.py` - Extensive test suites for round-trip and structural validation
- Contract enforcement prevents regressions and ensures mathematical rigor

### Phase 2: Interactive GUI (In Development)

**Current GUI Foundation:**
- `phase2_gui_foundation.py` - Working EGI rendering with basic interaction
- `arisbe_gui.py` - Main application framework with tab-based architecture
- Selection system, hover effects, and mouse interaction implemented

**Planned Interactive Components:**
- Selection overlays with context-sensitive visual feedback
- Context-sensitive action menus and transformation operations
- Warmup mode (compositional editing) vs Practice mode (rule-based)
- Dynamic effects and real-time validation

### Mathematical Foundation

**Dau's 6+1 Component Model:**
Arisbe implements Dau's formal definition of Relational Graphs with Cuts:

1. **V** - Finite set of vertices (individuals: variables `*x` or constants `"Socrates"`)
2. **E** - Finite set of edges (relations with specified arity)
3. **ν** - Nu mapping from edges to vertex sequences (argument order preservation)
4. **⊤** - Sheet of assertion (outermost positive context)
5. **Cut** - Finite set of cuts (negation contexts, fine-drawn closed curves)
6. **area** - Containment mapping (strict hierarchical nesting)
7. **rel** - Relation names mapping (predicate labels)

**Key Mathematical Properties:**
- **Structural Integrity**: All transformations preserve logical equivalence
- **Argument Order**: ν mapping strictly preserves predicate argument sequences
- **Area Containment**: Hierarchical nesting with no overlapping cuts
- **Round-trip Guarantee**: EGIF ↔ EGI ↔ EGDF conversions are lossless

**Visual Conventions (Dau/Peirce):**
- **Heavy Lines of Identity**: Connect individuals to predicates (4.0pt width)
- **Fine Cut Boundaries**: Negation contexts as closed curves (1.0pt width)
- **Identity Spots**: Prominent vertex markers (3.5pt radius)
- **Hook Connections**: Predicates connect directly to line periphery (1.5pt width)

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

## Quick Start

### Phase 2 GUI Foundation (Current)

```bash
# Launch interactive GUI with EGI rendering
python phase2_gui_foundation.py
```

Features:
- **Visual EGIF Rendering**: Enter EGIF expressions and see diagrams
- **Interactive Selection**: Click elements, Ctrl+click for multi-select
- **Real-time Updates**: EGI structure and selection info
- **Sample Library**: Dropdown with test cases

### Command Line Tools

```bash
# Parse and validate EGIF
python src/egif_parser_dau.py

# Test round-trip pipeline
python test_phase1d_comprehensive.py

# Validate Dau conventions
python test_dau_convention_validation.py
```

## Development and Testing

```bash
# Run comprehensive test suite
python -m pytest tests/ -v

# Test Phase 1d pipeline
python test_phase1d_comprehensive.py

# Validate visual rendering
python validate_qt_dau_rendering.py

# Test API contracts
python test_api_contracts.py
```

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

### Phase 1: Mathematical Foundation (Complete)

**EGIF Processing:**
- ✅ Sowa-compliant EGIF parsing with comprehensive syntax validation
- ✅ Robust error handling and informative error messages
- ✅ Support for variables (`*x`), constants (`"Socrates"`), and nested cuts
- ✅ Proper label scoping and variable binding

**EGI Data Model:**
- ✅ Dau's 6+1 component RelationalGraphWithCuts implementation
- ✅ Strict argument order preservation in ν mapping
- ✅ Hierarchical area containment with validation
- ✅ Contract-enforced structural integrity

**EGDF Format:**
- ✅ Dual JSON/YAML format support for different use cases
- ✅ Auto-detection and unified parsing interface
- ✅ Complete round-trip validation (EGIF ↔ EGI ↔ EGDF)
- ✅ API contracts prevent data loss and corruption

**Visual Rendering:**
- ✅ Graphviz-based hierarchical layout engine
- ✅ Dau/Peirce convention compliance (heavy lines, fine cuts)
- ✅ Professional-quality PySide6 rendering
- ✅ Non-overlapping cuts with proper containment

### Phase 2: Interactive GUI (In Development)

**Current Capabilities:**
- ✅ Real-time EGIF → Diagram rendering
- ✅ Interactive element selection and hover effects
- ✅ Multi-select with Ctrl+click
- ✅ EGI structure inspection and selection feedback
- 🔄 Selection overlays and context-sensitive actions (in progress)

**Planned Features:**
- ❌ Warmup mode: Compositional editing with direct EGI manipulation
- ❌ Practice mode: Rule-based transformations with formal validation
- ❌ Dynamic effects: Smooth animations and real-time feedback
- ❌ Undo/redo system with action history

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

### 🔄 Development Roadmap

**Phase 2: Interactive GUI (Current Focus)**
- Selection overlays with context-sensitive visual feedback
- Context-sensitive action menus and transformation operations
- Warmup mode: Direct manipulation and compositional editing
- Practice mode: Rule-based transformations with formal validation
- Dynamic effects and smooth animations

**Phase 3: Advanced Features**
- Browser: Universe of Discourse and corpus exploration
- Endoporeutic Game: Complete formal game implementation
- Corpus Integration: Authoritative examples from Peirce, Dau, Sowa
- Advanced transformation validation and proof tracking

**Phase 4: Platform and Integration**
- Web-based interface for broader accessibility
- Import/export to other logical formats (CLIF, FOPL, LaTeX)
- Integration with theorem provers and proof assistants
- Performance optimizations for large graphs
- Educational modules and guided tutorials

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

