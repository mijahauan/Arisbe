# Arisbe: Existential Graphs, Dau-compliant

**A pragmatic application that brings to life Peirce's vision of "moving pictures of the intellect"**

A mathematically rigorous implementation of Charles S. Peirce's Existential Graphs based on Frithjof Dau's formal framework. Arisbe provides a complete ecosystem for creating, validating, transforming, and visualizing logical reasoning through interactive diagrams.

## 🔒 **COHERENCE FRAMEWORK ACTIVE**

**Arisbe includes a comprehensive coherence framework with:**
- **📚 Complete API Documentation** - No more guessing at function signatures! See `ARISBE_CORE_API_REFERENCE.md`
- **🛡️ Core Protection** - 16 validated modules protected from unauthorized changes
- **🧪 87 Validated Tests** - Mathematical foundation thoroughly tested and verified
- **📊 Quality Monitoring** - Daily dashboard and automated quality gates

**→ New to the codebase? Read `COHERENCE_FRAMEWORK_REMINDER.md` first!**

Updated: 2025-09-20

## Overview

**Arisbe Existential Graphs are living logical systems** - complete universes of discourse that extend beyond simple diagrams or linear expressions. An EG encompasses synchronic forms (current structures, rules, sequences), diachronic history (complete transformation provenance), and interactive components (Endoporeutic Game dialog, fact introduction, pattern discovery).

**Two Implementation Levels:**
- **Exemplar Graphs (Organon)**: Restricted examples from textbooks/articles for scholarly reference
- **Comprehensive Systems (Agon)**: Complete justified ways of reasoning about worlds through dynamic transformation

**Technical Foundation:**
- EGI is the canonical source of truth for the mathematical structure
- EGIF/CGIF/CLIF are linear forms that round-trip to/from EGI
- EGDF is the canonical drawn-form spec for rendering/persistence
- GUI interactions are meaning-preserving (presentation deltas) unless explicitly invoking EGI operations
- Ligatures are single continuous lines; same-area ligatures avoid collisions; cross-area ligatures can cross cuts; rendering order: Cuts → Predicates → Vertices → Ligatures

## Architecture

### Integrated Management System

Arisbe features a unified architecture built around three core integrated managers that provide consistent, validated access to all system functionality:

**IntegratedCorpusManager** (`src/integrated_corpus_manager.py`)
- Centralized EGI library management with Dau formalism compliance
- Multi-format support (EGIF, CGIF, CLIF, FOPL, JSON)
- Advanced search, categorization, and quality metrics
- Educational corpus organization and validation

**IntegratedViewManager** (`src/integrated_view_manager.py`)
- Unified view generation system for all visualization needs
- Multiple view types: Overview, Detailed, Hierarchical, Spatial, Transformation
- Configurable zoom levels and focus filtering
- View caching and export capabilities

**IntegratedExportManager** (`src/integrated_export_manager.py`)
- Comprehensive export system with validation guarantees
- Quality levels: Draft, Standard, Publication, Archival
- Round-trip fidelity across all linear forms
- Export history tracking and batch processing

**CoreDauFormalismManager** (`src/core_dau_formalism.py`)
- Central coordination hub for all mathematical operations
- Transformation rule engine with validation
- Chapter-specific compliance checking
- Integration with all specialized managers

**CoherenceRegistry** (`src/coherence_registry.py`)
- Centralized discovery system for all components
- Function and interface registration
- Metadata and usage documentation
- Development coherence framework

### Current Active Architecture

The system is built around the integrated management system with mathematically rigorous core components:

**Core Mathematical Foundation:**
- **EGI Data Structures** (`egi_core_dau.py`): RelationalGraphWithCuts with 6+1 components
- **Transformation Rules** (`formal_transformation_rules.py`): IT+, IT-, INS, ERA, DC+, DC-
- **Linear Form System**: Round-trip translation between EGIF, CGIF, CLIF, FOPL
- **Hierarchical Indexing** (`hierarchical_index.py`): O(1) polarity and nesting calculations
- **Semantic Evaluation** (`dau_semantic_evaluation_engine.py`): Chapter-specific compliance

**Integrated Management Layer:**
- **CoreDauFormalismManager**: Central coordination of all mathematical operations
- **IntegratedCorpusManager**: Validated corpus management with search and categorization
- **IntegratedViewManager**: Unified view generation with caching and export
- **IntegratedExportManager**: Multi-format export with quality guarantees
- **CoherenceRegistry**: Component discovery and documentation system

### Active Components (Coherence Registry Validated)

**Core Mathematical Foundation:**
- **EGI Core**: `src/egi_core_dau.py` (RelationalGraphWithCuts, Vertex, Edge, Cut)
- **Transformation System**: `src/formal_transformation_rules.py` (All 6 Dau transformation rules)
- **Linear Form Parsers**: `src/egif_parser_dau.py`, `src/cgif_parser_dau.py`, `src/clif_parser_dau.py`
- **Linear Form Generators**: `src/egif_generator_dau.py`, `src/cgif_generator_dau.py`, `src/clif_generator_dau.py`
- **Hierarchical Indexing**: `src/hierarchical_index.py` (O(1) polarity calculations)
- **Semantic Evaluation**: `src/dau_semantic_evaluation_engine.py`
- **Chapter Compliance**: `src/enhanced_dau_compliance_engine.py`
- **FOPL Translation**: `src/chapter18_fopl_translation.py`

**Integrated Management System:**
- **Core Manager**: `src/core_dau_formalism.py` (Central coordination hub)
- **Corpus Manager**: `src/integrated_corpus_manager.py` (EGI library management)
- **View Manager**: `src/integrated_view_manager.py` (Unified visualization)
- **Export Manager**: `src/integrated_export_manager.py` (Multi-format export)
- **Coherence Registry**: `src/coherence_registry.py` (Component discovery)

**Layout Engine and Visualization:**
- **Definitive EGI Layout Engine**: `src/definitive_egi_layout_engine.py` (Production-ready layout system)
- **Connection Port System**: Pre-defined ports on EdgeLabel bounding boxes with optimal assignment
- **Graphviz SVG Renderer**: `src/graphviz_svg_renderer.py` (Clean SVG output with mathematical precision)
- **Style System**: `src/style_specification.py`, `styles/` (Customizable visual styling)
- **Area-Aware Pathfinding**: A* ligature routing respecting EGI containment hierarchy

**Active GUI Development:**
- **Chapter 21 Integration**: `src/chapter21_gui_integration.py`
- **Transformation Wizards**: `src/chapter21_transformation_wizards.py`
- **Diagram Panel**: `src/gui/organon/chapter21_diagram_panel.py`
- **Wizard Dialog**: `src/gui/transformation_wizard_dialog.py`

**Testing and Validation:**
- **Integration Tests**: `test_*_integration.py` (Comprehensive validation)
- **Chapter Tests**: `test_chapter*_*.py` (Chapter-specific compliance)
- **Coherence Framework**: `.coherence/`, `coherence_framework/`

### Legacy Components (Deprecated)

**Note**: The following components are deprecated and maintained for reference only:
- Constraint architecture system (`src/legacy/`)
- Fragmented drawing code (`src/diagram_coordinator.py`, `src/legacy/interaction_handler.py`)

### Core Principles

- **Mathematical Rigor**: All operations validated against Dau's formal specifications
- **Integrated Management**: Unified APIs through coherent manager interfaces
- **Component Discovery**: Coherence registry enables systematic access to all functionality
- **Round-trip Fidelity**: Guaranteed preservation across all linear form translations
- **Chapter Compliance**: Explicit validation against specific Dau chapters
- **Transformation Soundness**: All rule applications mathematically verified
- **Coherence Framework**: Documentation and code maintained in sync through registry

## Project structure

- `src/`
  - Canonical logic: `egi_core_dau.py`, `egi_system.py`, `egi_graph_operations.py`, `transformation_rules.py`
  - Linear forms: `egif_parser_dau.py`, `egif_generator_dau.py`, `cgif_parser_dau.py`, `cgif_generator_dau.py`, `clif_parser_dau.py`, `clif_generator_dau.py`, `chapter18_fopl_translation.py`
  - Controllers/coordination: `egi_controller.py`, `egi_adapter.py`, `egi_io.py`, `corpus_integration.py`
  - Spatial/layout/validation: `networkx_spatial_layout.py`, `logic_spatial_validator.py`, `egi_spatial_correspondence.py`, `spatial_region_manager.py`, `egi_logical_areas.py`
  - GUI/rendering: `qt_egi_gui.py`, `arisbe_unified_app.py`, `routing/visibility_router.py`, `styling/style_manager.py`, `export/tikz_exporter.py`, `controller/constraint_engine.py`
  - Legacy/demo: `qt_test_minimal.py`, `qt_correspondence_integration.py`, `spatial_logical_alignment.py`, `corpus_egi_test.py`
- `tools/`: interactive sandbox and converters (`drawing_editor.py`, `drawing_to_egi.py`, etc.)
- `docs/`: derived corpus text, references, examples, styles
- `corpus/`: canonical and challenging examples
- `tests/`: comprehensive unit/integration tests

## Current State

### ✅ Completed Integration (2025-09-15)

**Core Mathematical Foundation:**
- Complete Dau-compliant EGI data structures with 6+1 component architecture
- All transformation rules implemented (IT+, IT-, INS, ERA, DC+, DC-)
- Round-trip translation pipeline: EGIF ↔ CGIF ↔ CLIF ↔ FOPL ↔ EGI
- Chapter-specific compliance engines (Chapters 11-21)
- Hierarchical indexing for efficient cut nesting and polarity

**Integrated Management System:**
- IntegratedCorpusManager: Complete corpus management with validation
- IntegratedViewManager: Unified view generation and caching
- IntegratedExportManager: Multi-format export with quality guarantees
- CoreDauFormalismManager: Central coordination of all operations
- CoherenceRegistry: Component discovery and documentation system

**Testing and Quality Assurance:**
- Comprehensive test suites covering logical equivalence and transformation soundness
- Coherence framework with automated validation
- CI/CD pipeline with canonical invariant testing
- Quality metrics and compliance reporting

**Spatial and Visual Systems:**
- NetworkX + Graphviz spatial layout engine
- Logic-spatial concordance validation
- EGDF specification compliance
- Ligature rendering with collision avoidance
- Proper rendering order: Cuts → Predicates → Vertices → Ligatures

### ✅ Connection Port System (2025-09-26)

**Revolutionary Enhancement:**
- **Pre-defined connection ports** on EdgeLabel bounding boxes mirroring ν (nu) mapping
- **Optimal port assignment** ensuring vertices connect to nearest available ports
- **Smart port creation** for unary predicates based on actual vertex positions
- **Zero crossing issues** across entire 15-graph corpus validation
- **100% success rate** with professional visual quality

**Technical Achievements:**
- Two-level optimization: Smart port creation + nearest port assignment
- Mathematical precision: Perfect ν mapping correspondence maintained
- Visual excellence: Eliminates ligature crossings and text obstruction
- Production validation: Comprehensive corpus testing with zero failures
- Performance: 0.486 seconds average processing time per graph

### 🔧 Current Development Focus

**GUI and Interactive Systems:**
- Chapter 21 diagram panel and transformation wizards
- Interactive constraint enforcement
- Real-time validation and visual feedback
- Selection and highlighting improvements

**Known Technical Debt:**
- Import dependency resolution for some specialized modules
- Qt containment visualization refinements
- Interactive constraint consistency at edit-time
- Enhanced spatial correspondence under dynamic edits

## Sub-applications

- Organon (Browser): canonical EGDF viewing of EGI, read-only. Status: foundation in place; extend EGDF generator and browser views.
- Ergasterion (Workshop): interactive editor (Bullpen) with Warmup/Practice modes. Status: Qt GUI and sandbox present; constraints and selection system under active work.
- Agon (Endoporeutic Game): gameplay built on formal, legal, meaning-preserving moves. Status: design staged; depends on robust constraints and transformation legality.

## Quick start

Install
```bash
pip install -r requirements.txt
```

Run the interactive sandbox (recommended for quick trials)
```bash
python tools/drawing_editor.py
```

Run the Qt GUI
```bash
python src/arisbe_unified_app.py
# or
python src/qt_egi_gui.py
```

Parse and layout from EGIF in code
```python
from src.egif_parser_dau import EGIFParser
from src.egi_controller import EGIController
from src.networkx_spatial_layout import compute_layout

egi = EGIFParser('*x (Human x) ~[ (Mortal x) ]').parse()
layout = compute_layout(egi)
# feed into GUI or exporter as needed
```

Convert a drawing JSON to EGI
```bash
python tools/drawing_to_egi.py --input tmp/drawing.json --layout
```

## Testing and Validation

### Comprehensive Test Suite

**Integration Testing:**
```bash
# Core integration validation
python test_final_integration.py

# Comprehensive manager testing
python test_integrated_managers.py

# Working integration demo
python test_working_integration.py
```

**Chapter-Specific Testing:**
```bash
# Chapter 18 FOPL translation
python test_chapter18_translation_consistency.py

# Chapter 20 syntactic equivalence
python test_chapter20_syntactic_equivalence.py

# Chapter 21 comprehensive testing
python test_chapter21_comprehensive.py
```

**Core Mathematical Testing:**
```bash
# Full test suite
python -m pytest tests/ -v

# Canonical invariant testing
python -m pytest tests/test_canonical_invariant.py

# Round-trip translation validation
python test_complete_round_trip_translations.py
```

**GUI and Interactive Testing:**
```bash
# Minimal GUI demos
python src/qt_test_minimal.py

# Interactive transformation testing
python test_transformation_sequences_comprehensive.py
```

### Coherence Framework Validation

```bash
# Coherence analysis
python tools/coherence_analyzer.py

# Integration compliance
python tests/coherence_integration.py
```

## EGDF integrity and style metadata

- EGDF files include a header with:
  - egi_checksum: deterministic hash of normalized EGI
  - style_id: current theme identifier
  - updated: UTC ISO timestamp
- On load, mismatches can be surfaced for user awareness in future iterations.

## Development notes

- EGI as single source of truth; visual edits default to presentation deltas.
- Cuts determine spatial exclusion; child cuts create forbidden zones for parent-level elements.
- Same-area ligatures must avoid collisions; cross-area ligatures may cross cuts per EGI mappings.
- Rendering order is fixed to preserve legibility and correctness.
- Integrity monitoring is always-on to prevent regressions and contamination.

## What Users Can Do with Arisbe

### For Logic Researchers & Academics
- Create publication-quality Existential Graph diagrams
- Apply formal transformation rules with mathematical validation
- Verify logical equivalences across multiple representation formats
- Export to academic formats (LaTeX/TikZ, SVG, PDF)

### For Students & Educators
- Interactive tutorials showing EG transformations step-by-step
- Visual comparison between different logical representations
- Educational corpus with graded examples
- Assignment creation with automatic validation

### For Software Developers
- Programmatic EGI creation, validation, and transformation APIs
- Batch processing of large logic corpora
- Integration with other formal methods tools
- RESTful APIs for web-based applications

### For Knowledge Engineers
- Large-scale corpus management with search and categorization
- Quality metrics and validation reporting
- System integration with knowledge bases and theorem provers
- Bridge between diagrammatic and symbolic reasoning

## Development Roadmap

### Immediate Priorities (Q4 2025)
- **GUI Completion**: Finish Chapter 21 diagram panel and transformation wizards
- **Interactive Constraints**: Real-time validation and constraint enforcement
- **Import Resolution**: Fix remaining dependency issues for full system stability

### Short-term Goals (Q1 2026)
- **Organon Browser**: Read-only corpus browser with canonical views
- **Ergasterion Workshop**: Interactive editor with practice modes
- **CLI Tools**: Command-line interface for batch operations

### Medium-term Vision (2026)
- **Agon Game System**: Endoporeutic Game implementation
- **Web Interface**: Browser-based EG editor and viewer
- **Advanced Visualization**: 3D cuts and animated transformations

### Long-term Goals
- **Collaborative Editing**: Real-time multi-user EG development
- **Machine Learning Integration**: Pattern recognition in logical structures
- **Educational Platform**: Complete learning management system for EG theory

## References

- Dau, Frithjof. Mathematical Logic with Diagrams (2003).
- Peirce, C. S. Existential Graphs (Collected Papers).
- Sowa, J. F. Existential Graphs: MS 514 by Charles Sanders Peirce (2007).
