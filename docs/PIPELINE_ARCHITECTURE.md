# Arisbe Pipeline Architecture Reference

**Version:** 1.0  
**Last Updated:** 2025-08-05  
**Status:** Current Implementation

## Overview

The Arisbe Existential Graph system implements a mathematically rigorous pipeline for converting between textual (EGIF), abstract mathematical (EGI), and visual diagram (EGDF) representations of Existential Graphs, following Dau's formalism and Peirce's conventions.

## Pipeline Structure

```
EGIF ←→ EGI ←→ EGDF ←→ Visual Rendering
 ↑                              ↓
 └── Round-trip Validation ──────┘
```

### Core Components

#### 1. **EGIF (Existential Graph Interchange Format)**
- **Purpose**: Textual representation following Sowa's specification
- **Format**: Linear syntax with cuts as `~[ ... ]`
- **Examples**: 
  - `(Human "Socrates")`
  - `*x (Human x) ~[ (Mortal x) ]`
- **Implementation**: `egif_parser_dau.py`

#### 2. **EGI (Existential Graph Instance)**
- **Purpose**: Abstract mathematical representation (canonical form)
- **Structure**: `RelationalGraphWithCuts` class
- **Components**:
  - Vertices (V): Individual entities
  - Edges (E): Relations/predicates
  - Nu mapping (ν): Argument order preservation
  - Cuts: Negation boundaries
  - Areas (κ): Containment structure
- **Implementation**: `egi_core_dau.py`

#### 3. **EGDF (Existential Graph Diagram Format)**
- **Purpose**: Visual layout preservation with dual format support
- **Formats**: JSON (platform independence) and YAML (human readability)
- **Structure**:
  - `canonical_egi`: Mathematical structure
  - `visual_layout`: Spatial primitives and positioning
  - `metadata`: Documentation and provenance
- **Implementation**: `egdf_parser.py`

## Layer Architecture

Following Dau's formalism, the system maintains strict separation:

### Layer 1: Data (EGI Core)
- **Responsibility**: Pure mathematical structure
- **Immutability**: EGI is the sole source of logical truth
- **Operations**: All user actions map to formal EGI transformations
- **Files**: `egi_core_dau.py`, `egif_parser_dau.py`

### Layer 2: Layout Engine
- **Responsibility**: Spatial positioning and geometric relationships
- **Input**: EGI structure
- **Output**: Layout primitives with coordinates
- **Constraints**: Dau's conventions (non-overlapping cuts, hierarchical containment)
- **Files**: `layout_engine.py`

### Layer 3: Rendering
- **Responsibility**: Visual presentation
- **Input**: Layout primitives
- **Output**: Rendered diagrams
- **Backends**: Tkinter, PySide6 (planned), web (planned)
- **Files**: `diagram_renderer.py`, `clean_diagram_renderer.py`

### Layer 4: Interaction
- **Responsibility**: User interface and event handling
- **Pattern**: Action-first workflow (Add Cut → Select → Execute)
- **Modes**: Warmup (direct manipulation) and Practice (rule-based)
- **Files**: `enhanced_diagram_controller.py`, GUI components

## Data Flow Patterns

### 1. EGIF → EGI → EGDF (Import)
```python
# Parse EGIF to EGI
egif_parser = EGIFParser(egif_text)
egi = egif_parser.parse()

# Generate layout
layout_engine = LayoutEngine()
layout_result = layout_engine.layout_graph(egi)

# Create EGDF
egdf_parser = EGDFParser()
egdf_doc = egdf_parser.create_egdf_from_egi(egi, layout_result)

# Export in desired format
json_output = egdf_parser.export_egdf(egdf_doc, format_type="json")
yaml_output = egdf_parser.export_egdf(egdf_doc, format_type="yaml")
```

### 2. EGDF → EGI → EGIF (Export)
```python
# Parse EGDF (auto-detects JSON/YAML)
egdf_doc = egdf_parser.parse_egdf(egdf_content)

# Extract EGI
egi = egdf_parser.extract_egi_from_egdf(egdf_doc)

# Generate EGIF
egif_generator = EGIFGenerator()
egif_text = egif_generator.generate_egif(egi)
```

### 3. Round-trip Validation
```python
# Ensure mathematical equivalence
original_egi = parse_egif(original_egif_text)
roundtrip_egi = parse_egif(generate_egif(original_egi))
assert graphs_equivalent(original_egi, roundtrip_egi)
```

## Format Support

### EGDF Dual Format Support

#### JSON Format (.egdf)
- **Use Cases**: API integration, automated processing, web applications
- **Advantages**: Universal parser support, no dependencies
- **Structure**: Compact, machine-readable

#### YAML Format (.egdf.yaml)
- **Use Cases**: Manual editing, academic documentation, version control
- **Advantages**: Human-readable, comments support, cleaner diffs
- **Structure**: Hierarchical, with inline documentation

#### Format Detection
```python
# Auto-detection based on content
egdf_doc = parser.parse_egdf(content, format_hint="auto")

# Explicit format specification
egdf_doc = parser.parse_egdf(content, format_hint="yaml")
```

## Validation and Contracts

### API Contract System
- **Input Validation**: All methods validate input parameters
- **Output Guarantees**: Contracts ensure output meets specifications
- **Structural Integrity**: Graph structure validation at each stage
- **Implementation**: `@enforce_contracts` decorators

### Round-trip Guarantees
1. **Logical Equivalence**: `EGIF → EGI → EGIF` preserves meaning
2. **Argument Order**: ν mapping order strictly preserved
3. **Structural Integrity**: Area containment and cut nesting maintained
4. **Visual Fidelity**: EGDF preserves both logic and spatial arrangements

## Dau Convention Compliance

### Visual Rendering Rules
- **Heavy Lines**: Lines of identity are thick, continuous
- **Fine Cuts**: Cut boundaries are thin, closed curves
- **No Overlaps**: Strict non-overlapping for sibling cuts
- **Hierarchical Containment**: Nested cuts respect logical structure
- **Predicate Attachment**: Relations attach to line endpoints via hooks

### Layout Constraints
- **Spatial Units**: Heavy lines occupy space and participate in collision avoidance
- **Containment Hierarchy**: Visual nesting reflects logical nesting
- **Arbitrary Deformation**: Shape flexibility while preserving topology
- **Clear Separation**: Adequate spacing for selection and manipulation

## Extension Points

### Backend Support
- **Current**: Tkinter (cross-platform)
- **Planned**: PySide6 (native), web canvas (browser)
- **Architecture**: Abstract renderer interface enables easy backend swapping

### Export Formats
- **Current**: JSON, YAML, EGIF
- **Planned**: LaTeX (egpeirce.sty), SVG, PNG
- **Extensibility**: Plugin architecture for additional formats

### Transformation Rules
- **Current**: Basic EG operations (erasure, insertion)
- **Planned**: Full Peirce rule set (double cut, iteration, etc.)
- **Integration**: Rules map directly to EGI operations

## Performance Characteristics

### Scalability
- **Small Graphs** (< 20 elements): Real-time interaction
- **Medium Graphs** (20-100 elements): Sub-second layout
- **Large Graphs** (> 100 elements): Optimized layout algorithms

### Memory Usage
- **EGI Storage**: Minimal overhead, immutable structures
- **Layout Caching**: Spatial primitives cached for reuse
- **Rendering**: On-demand generation, no persistent canvas state

## Development Status

### Completed ✅
- [x] EGIF ↔ EGI round-trip pipeline
- [x] Dual JSON/YAML EGDF format support
- [x] Clean layer architecture (Data/Layout/Rendering/Interaction)
- [x] Dau convention compliance validation
- [x] API contract system
- [x] Basic layout engine with collision avoidance
- [x] Structural integrity validation

### In Progress 🚧
- [ ] Enhanced selection overlays and context actions
- [ ] Background validation and transformation logic
- [ ] Practice mode rule enforcement
- [ ] Advanced layout optimization

### Planned 📋
- [ ] LaTeX export with egpeirce.sty improvements
- [ ] Web-based rendering backend
- [ ] Complete Peirce transformation rule set
- [ ] Performance optimization for large graphs

## Usage Examples

### Basic Pipeline Usage
```python
from egif_parser_dau import EGIFParser
from egdf_parser import EGDFParser
from layout_engine import LayoutEngine

# Parse EGIF
egif_text = '(Human "Socrates") ~[ (Mortal "Socrates") ]'
parser = EGIFParser(egif_text)
egi = parser.parse()

# Generate layout
layout_engine = LayoutEngine()
layout_result = layout_engine.layout_graph(egi)

# Create and export EGDF
egdf_parser = EGDFParser()
egdf_doc = egdf_parser.create_egdf_from_egi(egi, layout_result)

# Export in both formats
json_output = egdf_parser.export_egdf(egdf_doc, format_type="json")
yaml_output = egdf_parser.export_egdf(egdf_doc, format_type="yaml")
```

### Round-trip Validation
```python
# Validate round-trip integrity
original_egif = '(Human "Socrates") ~[ (Mortal "Socrates") ]'
egdf_doc = create_egdf_from_egif(original_egif)
recovered_egi = egdf_parser.extract_egi_from_egdf(egdf_doc)
recovered_egif = generate_egif(recovered_egi)

# Should be logically equivalent
assert validate_round_trip(original_egif, recovered_egif)
```

## References

- **Dau, F.** *Mathematical Logic with Diagrams* - Visual convention specifications
- **Sowa, J.F.** *EGIF Specification* - Textual format definition  
- **Peirce, C.S.** *Existential Graphs* - Original logical system
- **Arisbe Project** - Implementation of rigorous EG system

---

*This document serves as the definitive reference for the Arisbe pipeline architecture and should be updated as the system evolves.*
