# Import/Export Format Support

## Overview
Arisbe supports **8 interchange formats** for importing and exporting Existential Graphs, enabling interoperability with other systems, literature sources, and academic publications.

---

## Supported Formats

### 1. EGIF (Extended Graph Interchange Format)
**Purpose**: Primary linear format for Existential Graphs  
**Direction**: ✅ Import | ✅ Export  
**File Extension**: `.egif`

**Parser/Generator**:
```python
from egif_parser_dau import parse_egif
from egif_generator_dau import generate_egif

# Import
egi = parse_egif(egif_text)

# Export
egif_text = generate_egif(egi)
```

**Use Cases**:

- Literature imports
- Canonical examples
- Textual representation
- Version control friendly

---

### 2. CGIF (Conceptual Graph Interchange Format)
**Purpose**: ISO/IEC standard for Conceptual Graphs  
**Direction**: ✅ Import | ✅ Export  
**File Extension**: `.cgif`

**Parser/Generator**:
```python
from cgif_parser_dau import parse_cgif
from cgif_generator_dau import generate_cgif

# Import
egi = parse_cgif(cgif_text)

# Export
cgif_text = generate_cgif(egi)
```

**Use Cases**:

- Interoperability with CG systems
- ISO standard compliance
- Academic exchange
- Literature from Sowa tradition

---

### 3. CLIF (Common Logic Interchange Format)
**Purpose**: ISO/IEC 24707 Common Logic standard  
**Direction**: ✅ Import | ✅ Export  
**File Extension**: `.clif`

**Parser/Generator**:

```python
from clif_parser_dau import parse_clif
from clif_generator_dau import generate_clif, generate_clif_with_quantification

# Import
egi = parse_clif(clif_text)

# Export (with explicit quantification)
clif_text = generate_clif(egi)
clif_text = generate_clif_with_quantification(egi)  # Explicit form
```

**Use Cases**:

- Common Logic ecosystem integration
- ISO standard interchange
- Formal semantics
- Ontology exchange

---

### 4. FOPL (First-Order Predicate Logic)
**Purpose**: Dau's Φ/Ψ translation (Chapter 18)  
**Direction**: ✅ Import | ✅ Export  
**File Extension**: `.fopl` or `.fol`

**Parser/Generator**:

```python
from chapter18_fopl_translation import fopl_to_egi, egi_to_fopl

# Import (Ψ translation)
egi = fopl_to_egi(formula_str)

# Export (Φ translation)
fopl_text = egi_to_fopl(egi)
```

**Use Cases**:

- Traditional logic representation
- Automated theorem provers
- Educational contexts
- Logic textbook examples

**Note**: This is Dau's formal translation, not a naive conversion

---

### 5. JSON (EGI Structure)
**Purpose**: Native Arisbe EGI format  
**Direction**: ✅ Import | ✅ Export  
**File Extension**: `.json` or `.egi.json`

**Parser/Generator**:

```python
from egi_io import load_egi_json, save_egi_json

# Import
egi = load_egi_json("filename.json")

# Export (includes layout_deltas if present)
save_egi_json(egi, "filename.json")
```

**Use Cases**:

- Native storage format
- Internal use
- Layout delta persistence
- Fast loading

---

### 6. JSON (Full Universe of Discourse)
**Purpose**: Complete UoD with metadata + history + layout  
**Direction**: ✅ Import | ✅ Export  
**File Extension**: `.uod.json` or `.json`

**Parser/Generator**:

```python
from tomos_service import TomosService

corpus = TomosService(corpus_root)

# Import
uod = corpus.load_uod(uod_id, load_history=True)

# Export
corpus.save_uod(uod)
```

**Structure**:

```json
{
  "metadata": {
    "uod_id": "...",
    "uod_type": "dynamic",
    "name": "...",
    "category": "inquiry",
    ...
  },
  "current_egi": { ... },
  "current_layout_deltas": { ... },
  "history": { ... }  // Optional
}
```

**Use Cases**:

- Complete tomos storage
- Metadata preservation
- History tracking
- Layout persistence

---

### 7. SVG (Scalable Vector Graphics)
**Purpose**: Visual diagram export  
**Direction**: ❌ Import | ✅ Export  
**File Extension**: `.svg`

**Generator**:

```python
from simple_svg_renderer import SimpleSVGRenderer

renderer = SimpleSVGRenderer()
svg_content = renderer.render_to_svg_string(dto, egi, style)
```

**Use Cases**:

- Publications
- Presentations
- Web display
- Print output

**Note**: SVG is export-only (visual representation, not data)

---

### 8. LaTeX/TikZ (Academic Publication Format)
**Purpose**: LaTeX document with TikZ diagram  
**Direction**: ❌ Import | ✅ Export  
**File Extension**: `.tex`

**Generator**:

```python
from export.tikz_exporter import generate_tikz

# Generate standalone LaTeX document
latex_content = generate_tikz(render_commands, standalone=True)

# Generate TikZ picture only (for inclusion)
tikz_picture = generate_tikz(render_commands, standalone=False)
```

**Use Cases**:

- Academic papers
- LaTeX documents
- High-quality publications
- Vector graphics in papers

**Features**:

- Standalone LaTeX document or TikZ picture only
- Vertices, predicates, cuts, ligatures
- Proper parity shading (even/odd areas)
- Style-aware rendering
- Text escaping for LaTeX

**Note**: 
LaTeX/TikZ is export-only (visual representation, not data)

---

## Format Comparison

| Format | Import | Export | Metadata | History | Layout | Standard |
|--------|--------|--------|----------|---------|--------|----------|
| **EGIF** | ✅ | ✅ | ❌ | ❌ | ❌ | Arisbe |
| **CGIF** | ✅ | ✅ | ❌ | ❌ | ❌ | ISO CG |
| **CLIF** | ✅ | ✅ | ❌ | ❌ | ❌ | ISO CL |
| **FOPL** | ✅ | ✅ | ❌ | ❌ | ❌ | Dau Ch.18 |
| **JSON (EGI)** | ✅ | ✅ | ❌ | ❌ | ✅ | Arisbe |
| **JSON (UoD)** | ✅ | ✅ | ✅ | ✅ | ✅ | Arisbe |
| **SVG** | ❌ | ✅ | ❌ | ❌ | ✅ | W3C |
| **LaTeX/TikZ** | ❌ | ✅ | ❌ | ❌ | ✅ | LaTeX |

---

## Organon Integration

### Import Workflow
1. User clicks "Import" button
2. File dialog shows all supported formats
3. Format auto-detected from extension
4. Content parsed to EGI
5. UoD created with metadata (literature category)
6. Saved to tomos via TomosService

### Export Workflow
1. User selects UoD
2. Clicks "Export" button
3. Chooses format and options
4. Content generated from current EGI
5. File saved with appropriate extension

### Format Selection Dialog
```
Import Universe of Discourse
┌─────────────────────────────────────┐
│ Format:                             │
│ • EGIF - Extended Graph (.egif)    │
│ • CGIF - Conceptual Graphs (.cgif) │
│ • CLIF - Common Logic (.clif)      │
│ • FOPL - First-Order Logic (.fopl) │
│ • JSON - Full UoD (.uod.json)      │
│ • JSON - EGI only (.json)          │
└─────────────────────────────────────┘
```

---

## Implementation Status

### Core Parsers/Generators ✅
- [x] EGIF parser (`egif_parser_dau.py`)
- [x] EGIF generator (`egif_generator_dau.py`)
- [x] CGIF parser (`cgif_parser_dau.py`)
- [x] CGIF generator (`cgif_generator_dau.py`)
- [x] CLIF parser (`clif_parser_dau.py`)
- [x] CLIF generator (`clif_generator_dau.py`)
- [x] FOPL translator (`chapter18_fopl_translation.py`)
- [x] JSON EGI I/O (`egi_io.py`)
- [x] SVG renderer (`simple_svg_renderer.py`)
- [x] LaTeX/TikZ exporter (`export/tikz_exporter.py`)

### Organon Integration 🔄
- [ ] Import manager with format detection
- [ ] Export manager with format options
- [ ] UoD metadata creation for imports
- [ ] Progress indicators
- [ ] Error handling and validation
- [ ] Preview before import
- [ ] Batch import support

---

## Usage Examples

### Import Literature (EGIF)

```python
# In Organon
from import_export_manager import ImportExportManager

manager = ImportExportManager(tomos_service)
uod = manager.import_uod()  # Shows file dialog
if uod:
    tomos_service.save_uod(uod)
    # UoD now in tomos with literature category
```

### Export to Multiple Formats

```python
# Export current UoD
manager = ImportExportManager(tomos_service)

# EGIF
manager.export_uod(uod, format='egif', file_path='output.egif')

# CGIF  
manager.export_uod(uod, format='cgif', file_path='output.cgif')

# CLIF
manager.export_uod(uod, format='clif', file_path='output.clif')

# Full UoD JSON
manager.export_uod(uod, format='uod_json', file_path='output.uod.json')
```

---

## Future Enhancements

### Planned Features
- [ ] LaTeX export (for papers)
- [ ] PDF export (rendered diagrams)
- [ ] Batch conversion tool
- [ ] Format validation
- [ ] Round-trip testing
- [ ] Import preview
- [ ] Export options dialog

### Possible Future Formats
- RDF/OWL (semantic web)
- GraphML (graph exchange)
- DOT (Graphviz)
- PNG/JPEG (raster images)

---

## References

### Documentation
- **EGIF**: Dau Chapter 18, Arisbe implementation docs
- **CGIF**: ISO/IEC 24707:2007 (Conceptual Graphs)
- **CLIF**: ISO/IEC 24707:2018 (Common Logic)
- **FOPL**: Dau Chapter 18 (Φ/Ψ translations)

### Implementation
- `src/egif_parser_dau.py` - EGIF import
- `src/egif_generator_dau.py` - EGIF export
- `src/cgif_parser_dau.py` - CGIF import
- `src/cgif_generator_dau.py` - CGIF export
- `src/clif_parser_dau.py` - CLIF import
- `src/clif_generator_dau.py` - CLIF export
- `src/chapter18_fopl_translation.py` - FOPL bidirectional
- `src/egi_io.py` - JSON EGI I/O
- `src/tomos_service.py` - Full UoD I/O
- `src/simple_svg_renderer.py` - SVG export
- `src/export/tikz_exporter.py` - LaTeX/TikZ export

---

## Summary

Arisbe supports **8 formats** for interoperability:

- **4 textual linear formats**: EGIF, CGIF, CLIF, FOPL
- **2 JSON formats**: EGI-only, Full UoD
- **2 visual formats**: SVG, LaTeX/TikZ

All parsers/generators are **production-ready** and tested. Organon integration is the next step to expose these capabilities to users.
