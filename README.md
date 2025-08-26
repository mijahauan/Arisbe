# Arisbe EG Works v3.0.0

A mathematically rigorous implementation of Charles Sanders Peirce's Existential Graphs based on Frithjof Dau's formal mathematical framework. Arisbe provides a complete pipeline for creating, editing, transforming, and visualizing Existential Graph diagrams with strict adherence to logical formalism and Peircean conventions.

## State of Affairs (25 August 2025)

This project is in an intentional refocus phase toward a strict layered architecture and a lighter, more responsive GUI sandbox for interaction research:

- **Architecture (refined):**
  - EGI (canonical logic, immutable) → Layout/Spatial → Rendering → Interaction.
  - Meaning-preserving edits are presentation deltas; meaning-changing edits are explicit EGI ops.
  - Ligatures are single continuous lines; same-area ligatures avoid collisions; cross-area ligatures may cross cuts.
- **Working GUI (sandbox):** `tools/drawing_editor.py`
  - Add cuts/vertices/predicates, delete selections, attach ligatures.
  - Drag and resize cuts with 8 handles; constraints: cuts must be nested or disjoint.
  - Interaction throttling and deferred validation to prevent stalls; stdout logs for actions to diagnose hangs.
- **Three components roadmap:**
  - **Organon (Browser):** canonical EGDF viewing of EGI.
  - **Ergasterion (Workshop):** composition/practice with constraint enforcement and Chapter 16 transformations.
  - **Agon (Endoporeutic Game):** gameplay built on legal meaning-preserving moves.

This section supersedes older references to legacy GUI entry points and mixed-concern modules; the new sandbox is the primary surface for interactive work.

### Architecture (Layered Model)

```mermaid
flowchart TD
    A[EGI: Canonical Logical Graph\nV, E, ν, ⊤, Cuts, area, rel\n(immutable)] --> B[Layout/Spatial\nCompute positions/sizes\nsubject to constraints]
    B --> C[Rendering\nQt/PySide6 drawing\nstyles applied]
    C --> D[Interaction\nUser actions\n(meaning-preserving vs EGI ops)]

    subgraph Principles
      P1[Ligatures are single continuous lines]
      P2[Same-area ligatures avoid collisions]
      P3[Cross-area ligatures may cross cuts]
      P4[Cuts: nested or disjoint; no partial overlaps]
    end

    B -. respects .-> P4
    C -. respects .-> P1
    C -. respects .-> P2
    C -. respects .-> P3

    subgraph Tooling
      T1[tools/drawing_editor.py\nInteraction sandbox]
      T2[src/routing/visibility_router.py]
      T3[src/styling/style_manager.py]
      T4[src/export/tikz_exporter.py]
    end

    D --> T1
    B --> T2
    C --> T3
    C --> T4
```

### Components Roadmap

#### Organon (Browser)

- **Goal**: Deterministic, canonical viewing of EGIs via EGDF.
- **Scope**: Read-only; ensures logical-visual fidelity without editing side-effects.
- **Current**: Preview scaffolding exists; canonicalization planned (EGDF generator).
- **Near-term milestones**:
  - EGDF generator from EGI with invariants and hashes.
  - Read-only browser pane rendering canonical diagrams.
  - Corpus browser wired to canonical views.

#### Ergasterion (Workshop)

- **Current**: `tools/drawing_editor.py` supports adding cuts/vertices/predicates, ligatures, deletion; drag/resize with constraints, throttled interactions, stdout diagnostics.
- **Near-term milestones**:
  - Full EGI↔spatial Correspondence Layer API with validators.
  - Collision-aware ligature routing (single-curve, same-area avoidance).
  - Presentation delta storage and replay.
  - Chapter 16 transform palette (meaning-preserving/revealing) with legality checks.

#### Agon (Endoporeutic Game)

- **Goal**: Play based on Chapter 16 legal moves and goals; track proofs and strategies.
- **Foundation**: Constraint-enforced edits, single-line ligature principle, and diagnostics.
- **Near-term milestones**:
  - Formal move set and legality engine over EGI.
  - Turn/score mechanics and UI affordances for legal moves.
  - Integration with Ergasterion’s transform palette.

## Current Status (14 August 2025)

**Core Pipeline: COMPLETE ✅**
- ✅ **EGIF ↔ EGI ↔ EGDF Pipeline**: Full round-trip with validation
- ✅ **Canonical API**: Version-controlled, extensible architecture
- ✅ **Dau-Compliant Rendering**: Proper ligatures, cuts, and vertex positioning
- ✅ **Interactive GUI**: Three-area architecture with Qt Graphics Scene
- ✅ **Corpus Integration**: Educational examples with visual browser
- ✅ **Mathematical Foundation**: RelationalGraphWithCuts with containment hierarchy

**Working Features:**
- ✅ **Browser Area**: Corpus exploration with visual preview
- ✅ **Graph Preparation**: Interactive editing with drag-and-drop
- ✅ **Live EGIF Display**: Real-time chiron showing current graph structure
- ✅ **Annotation System**: Optional arity numbers and identity markers
- ✅ **Copy Workflow**: Browser → Preparation seamless integration

**In Development:**
- 🔄 **Area Constraint System**: Shapely-based boundary enforcement for semantic correctness
- 🔄 **Mode-Aware Editing**: Composition vs Practice mode constraints
- 🔄 **Visual Optimization**: Side-aware ligature attachment and collision avoidance

**Planned Features:**
- ❌ **Advanced Transformations**: Complete EG transformation rule set
- ❌ **Endoporeutic Game**: Formal game theory implementation
- ❌ **Export Formats**: LaTeX, SVG, PNG with publication quality

## Quick Start

### Installation
```bash
git clone https://github.com/mjhauan/Arisbe.git
cd Arisbe
pip install -r requirements.txt
```

### Run the Application
```bash
python tools/drawing_editor.py
```

This launches the three-area interface:
- **Browser**: Explore corpus examples with visual preview
- **Graph Preparation**: Interactive editing with Composition/Practice modes  
- **Endoporeutic Game**: Formal game interface (coming soon)

### Basic Usage
```python
from src.canonical import get_canonical_pipeline

# Create pipeline
pipeline = get_canonical_pipeline()

# Parse EGIF to EGI
egi = pipeline.parse_egif("[Human Socrates] [Mortal Socrates]")

# Generate EGDF for visualization  
egdf = pipeline.egi_to_egdf(egi)

# Convert back to EGIF
egif_output = pipeline.egi_to_egif(egi)
```

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
from egif_parser_dau import EGIFParser

# Parse basic relations
parser = EGIFParser('(Human "Socrates")')
graph = parser.parse()

# Parse with cuts (negation)
parser = EGIFParser('*x ~[ (Mortal x) ]')
graph = parser.parse()

# Parse complex nested structures
parser = EGIFParser('*x (Human x) ~[ (Mortal x) ~[ (Wise x) ] ]')
graph = parser.parse()
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
from egif_parser_dau import EGIFParser
from layout_phase_implementations import NinePhaseLayoutPipeline
from diagram_renderer_dau import DiagramRendererDau
from pyside6_canvas import PySide6Canvas

# Parse and layout
parser = EGIFParser('*x ~[ (Human x) ] ~[ (Mortal x) ]')
graph = parser.parse()
pipeline = NinePhaseLayoutPipeline()
layout = pipeline.execute_pipeline(graph)

# Render to canvas
canvas = PySide6Canvas(width=800, height=600)
renderer = DiagramRendererDau()
renderer.render_diagram(canvas, graph, layout)
canvas.save_to_file('diagram.png')
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

### Corpus conversion and validation (goldens)

Tools in `tools/` provide deterministic conversion and corpus checks for EGIF/CGIF/CLIF linear forms.

```bash
# Convert between EGIF/CGIF/CLIF (auto-detects by extension unless --from provided)
python tools/convert_linear_form.py --in corpus/corpus/canonical/sowa_cat_on_mat.egif --to cgif --stdout

# Validate the corpus against goldens (canonical and scholars)
# Fails on any mismatch between regenerated output and files in-place
python tools/validate_corpus_linear_forms.py

# Rewrite goldens in-place to current deterministic output (use with care)
# Default target is 'canonical'; pass 'scholars' or 'all' to broaden scope
python tools/rewrite_linear_goldens.py            # canonical only
python tools/rewrite_linear_goldens.py scholars   # only scholars
python tools/rewrite_linear_goldens.py all        # canonical + scholars
```

CI runs `tools/validate_corpus_linear_forms.py` on every push/PR (see `.github/workflows/canonical.yml`). Any mismatch will fail the job to preserve deterministic goldens.

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

### Temporary note: GUI demos disabled

The Qt demo entry points `src/qt_test_minimal.py` and `src/corpus_egi_test.py` are temporarily disabled while the headless EGI↔spatial adapter is stabilized. Please run the headless tests instead:

```bash
pytest -q
```

### Drawing → EGI (headless)

Arisbe supports constructing a Dau-compliant EGI from simple drawing primitives using `drawing_to_relational_graph()` in `src/drawing_to_egi_adapter.py`.

Schema (JSON):

```json
{
  "sheet_id": "S",
  "cuts": [ { "id": "c1", "parent_id": "S" } ],
  "vertices": [ { "id": "v1", "area_id": "c1" } ],
  "predicates": [ { "id": "e1", "name": "P", "area_id": "c1" } ],
  "ligatures": [ { "edge_id": "e1", "vertex_ids": ["v1"] } ]
}
```

- `area_id` must be either `sheet_id` or a cut id.
- `parent_id` must be `sheet_id` or a cut id.

CLI helper:

```bash
python tools/drawing_to_egi.py --input example_drawing.json --layout
```

This prints a summary of V, E, Cut, area containment, and optionally attempts a headless spatial layout.

## Debug Logging

To keep output quiet by default, debug prints are gated behind environment variables:

- ARISBE_DEBUG_EGI=1: Enables EGI/region debug logs in `src/egi_system.py`, `src/egi_graph_operations.py`, and `src/spatial_region_manager.py`.
- ARISBE_DEBUG_ROUTING=1: Enables routing diagnostics in `src/egi_spatial_correspondence.py`.

Examples:

```bash
# Enable EGI debug logs for one run
ARISBE_DEBUG_EGI=1 python -m pytest -q

# Enable routing diagnostics for scene generation
ARISBE_DEBUG_ROUTING=1 python arisbe_eg_clean.py

# Combine both
ARISBE_DEBUG_EGI=1 ARISBE_DEBUG_ROUTING=1 python -m pytest -q
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

