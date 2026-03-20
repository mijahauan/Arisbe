# AGENTS.md

## 🔒 Core Protection System
- **16 protected core modules** - Cannot be modified without explicit authorization
- **87 core tests** must always pass - These validate the mathematical foundation
- **Qt-dependent tests** excluded from automatic quality gate (run manually to avoid hangs)
- **Check protection status**: `python tools/core_protection_system.py --report`
- **Override protection** (authorized changes only): `touch .core_modification_authorized`

## 📚 Living Documentation System
- **Auto-updating documentation**: Documentation stays current with codebase changes
- **Context awareness system**: `tools/context_awareness_system.py` prevents reinvention
- **Persistent memory integration**: Critical framework awareness stored in memory system
- **Framework amnesia recovery**: `docs/context/FRAMEWORK_AMNESIA_RECOVERY.md` for complete context recovery
- **IDE integration**: VS Code tasks for instant context checks

## 📚 API Discovery Protocol
- **NEVER guess function signatures** - Use `docs/ARISBE_CORE_API_REFERENCE.md` for exact signatures
- **Complete API documentation**: 57 classes, 19 functions fully documented
- **Usage patterns**: See `docs/CORE_API_USAGE_GUIDE.md` for common development patterns
- **Quick function lookup**: `grep -i "function_name" docs/ARISBE_CORE_API_REFERENCE.md`

## 🧪 Testing Requirements
- **Quality check**: `python tools/quality_gate_system.py` (runs automatically on commit)
- **System status**: `python tools/daily_quality_dashboard.py`
- **Core tests**: `python -m pytest tests/` (87/87 passing)
- **Qt-dependent tests**: Run manually (excluded from automatic checks due to collection hangs)
- **GUI Organon tests**: `python tools/test_gui_organon.py` (3/3 passing)
- **Expected results**: 87 core tests passing, 0 failing
- **Timeout protection**: 120s timeout prevents infinite hangs on Qt import issues

### Battle-Tested Import/Export Infrastructure
**Status**: ✅ PRODUCTION - Comprehensive test coverage across corpus
- **EGIF**: Tested on 57+ tomos examples (parse → generate → parse)
- **CGIF**: Tested on 40+ tomos examples (ISO/IEC standard compliance)
- **CLIF**: Tested on 35+ tomos examples (Common Logic standard)
- **FOPL**: Round-trip translation tests (Φ/Ψ bidirectional)
- **Round-trip**: All formats tested for stability and variable preservation
- **Test files**: `test_corpus_parsing.py`, `test_variable_order_alignment.py`, `test_variable_name_consistency.py`

## 🏗️ Build and Development
- **Environment**: `conda activate CGIF` (Python 3.12.10)
- **Dependencies**: See `requirements.txt`
- **Core modules location**: `src/` directory (16 protected modules)
- **Test location**: `tests/` directory (90 core validation tests)

## 📋 Code Style and Conventions
- **Import pattern**: `from module_name import function_name` (not `from src.module_name`)
- **EGI immutability**: Use `.with_vertex()`, `.with_edge()` patterns (not `.add_*()`)
- **Error handling**: Check return values, handle None cases
- **Documentation**: Follow existing docstring patterns

## 🧠 Context Recovery (Framework Amnesia)
- **Forgot the framework?** Read `docs/context/COHERENCE_FRAMEWORK_REMINDER.md` first
- **Complete recovery guide**: `docs/context/FRAMEWORK_AMNESIA_RECOVERY.md`
- **Persistent context system**: `docs/context/PERSISTENT_CONTEXT_SYSTEM.md` for complete workflow
- **Automated reminders**: `python tools/coherence_reminder_system.py`
- **Context awareness check**: `python tools/context_awareness_system.py --check "task"`
- **Quick status**: `python tools/core_protection_system.py --report`

## 🔧 Essential Tools
- **Daily quality dashboard**: `python tools/daily_quality_dashboard.py`
- **Core protection check**: `python tools/core_protection_system.py`
- **API documentation generator**: `python tools/extract_core_api.py`
- **Coherence reminders**: `python tools/coherence_reminder_system.py`
- **Context awareness system**: `python tools/context_awareness_system.py`
- **Living documentation generator**: `python tools/living_documentation_generator.py`

## 📊 Quality Gates
- **Pre-commit hooks**: Automatically run quality checks
- **Core protection**: Blocks unauthorized changes to protected modules
- **Test validation**: All 87 core tests must pass
- **Syntax checking**: Zero syntax errors required

## 🎯 Common Development Patterns

### Creating EGI
```python
from egi_core_dau import create_empty_graph, create_vertex, create_edge
egi = create_empty_graph()
vertex = create_vertex(label="Human", is_generic=False)
egi = egi.with_vertex(vertex)
```

### Saving/Loading EGI
```python
from egi_io import save_egi_json, load_egi_json
save_egi_json(egi, "filename.json")
loaded_egi = load_egi_json("filename.json")
```

### Unified D3 Recursive Layout Engine (PRODUCTION)
```python
from unified_d3_engine import UnifiedD3Engine
from style_loader import StyleLoader

# Load style
style_loader = StyleLoader()
style = style_loader.load_default_style()

# Generate layout with recursive bottom-up engine
engine = UnifiedD3Engine()
dto = engine.generate_layout(egi, style, layout_deltas=None)

# DTO structure:
# - dto.vertex_positions: Dict[ElementID, Point]
# - dto.predicate_positions: Dict[ElementID, Point]
# - dto.cut_bounds: Dict[ElementID, BoundingBox]
# - dto.ligature_paths: List[LigaturePath]
```

### GUI Style Management
```python
from gui.style_manager import STYLE_MANAGER, get_current_style, DiagramStyle

# Load and use style in GUI
style = STYLE_MANAGER.load_default_style()

# Get current style
current = get_current_style()

# Access style properties
vertex_radius = current.vertex_radius
cut_padding = current.cut_padding
```

### Transformation Rules
```python
from formal_transformation_rules import DeiterationRule, TransformationContext
rule = DeiterationRule()
context = TransformationContext(source_egi=egi, target_area="sheet", ...)
result = rule.apply_transformation(context)
```

### Import/Export - Battle-Tested Production Modules (✅ 57+ tomos examples tested)
**Status**: ✅ PRODUCTION - All parsers/generators validated across extensive tomos  
**Documentation**: `docs/IMPORT_EXPORT_FORMATS.md` for complete reference

**EGIF (Extended Graph Interchange Format)**:
```python
from egif_parser_dau import parse_egif
from egif_generator_dau import generate_egif

# Import
egi = parse_egif(egif_text)

# Export
egif_text = generate_egif(egi)
```

**CGIF (Conceptual Graph Interchange Format - ISO standard)**:
```python
from cgif_parser_dau import parse_cgif
from cgif_generator_dau import generate_cgif

# Import
egi = parse_cgif(cgif_text)

# Export
cgif_text = generate_cgif(egi)
```

**CLIF (Common Logic Interchange Format - ISO standard)**:
```python
from clif_parser_dau import parse_clif
from clif_generator_dau import generate_clif, generate_clif_with_quantification

# Import
egi = parse_clif(clif_text)

# Export
clif_text = generate_clif(egi)
clif_text = generate_clif_with_quantification(egi)  # Explicit quantifiers
```

**FOPL (First-Order Predicate Logic - Dau Chapter 18)**:
```python
from chapter18_fopl_translation import fopl_to_egi, egi_to_fopl

# Import (Ψ translation: FOPL → EGI)
egi = fopl_to_egi(formula_str)

# Export (Φ translation: EGI → FOPL)
fopl_text = egi_to_fopl(egi)
```

**JSON (EGI with Layout Deltas)**:
```python
from egi_io import load_egi_json, save_egi_json

# Import
egi = load_egi_json("filename.json")

# Export (preserves layout_deltas)
save_egi_json(egi, "filename.json")
```

**LaTeX/TikZ (Academic Publication Format)**:
```python
from export.tikz_exporter import generate_tikz

# Export as standalone LaTeX document
latex_content = generate_tikz(render_commands, standalone=True)

# Export as TikZ picture only (for inclusion in documents)
tikz_picture = generate_tikz(render_commands, standalone=False)
```

**Testing**: All formats tested with:
- ✅ Tomos parsing (57+ EGIF, 40+ CGIF, 35+ CLIF examples)
- ✅ Round-trip stability (parse → generate → parse)
- ✅ Variable name preservation
- ✅ Variable order alignment across formats
- ✅ Nested cut handling
- ✅ Mixed constants and variables

### Tomos Management (✅ PRODUCTION - IMPLEMENTED 2025-10-14)
**Current Status**: Unified TomosService API (fully tested and integrated)  
**Documentation**: `docs/UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md`, `docs/UOD_DEVELOPER_GUIDE.md`, `docs/DAG_HISTORY_ARCHITECTURE.md`

**For Organon (Browse & Load UoDs)**:
```python
from tomos_service import TomosService

# Initialize
corpus = TomosService(Path("corpus"))

# Browse UoDs (fast, index-based)
uods = corpus.list_uods(is_static=True)  # Literature
uods = corpus.list_uods(is_dynamic=True) # Active reasoning

# Load UoD with history
uod = corpus.load_uod(uod_id, load_history=True)
```

**For Ergasterion/Agon (With DAG History)**:
```python
from universe_of_discourse import UniverseOfDiscourse, UoDMetadata, UoDType, UoDCategory
from egi_transformation_history import HistoryBranchType

# Create UoD with history support
uod = UniverseOfDiscourse(metadata=metadata, current_egi=egi)
uod.promote_to_historical("Initial state")

# Add transformations (linear or branching)
uod.history.add_transformation(rule_name, context, result)

# Branch from any historical state
branch_id = uod.history.create_branch_from_state(
    source_state_id,
    HistoryBranchType.EXPLORATION,
    "Alternative approach"
)
```

**✅ IMPLEMENTED (2025-10-14)**: 
- **Universe of Discourse**: Fundamental entity is now the UoD (diachronic process), not static EGI
- **DAG-Based History**: Branching transformation history for realistic inquiry workflows
- **TomosService**: Unified API for tomos management (implemented and tested)
- **Organon Integration**: Basic viewing integrated (~40% complete, needs import/export)
- **Ergasterion Integration**: Foundation integrated (untested, needs validation)
- **Backward Compatibility**: `GraphEntity` = `UniverseOfDiscourse` (zero breaking changes)
- **See documentation**: `docs/UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md`, `docs/DAG_HISTORY_ARCHITECTURE.md`

## 🔄 Living Documentation Workflow
- **Before development**: `python tools/context_awareness_system.py --check "task"`
- **Check existing solutions**: `grep -i "function_name" docs/ARISBE_CORE_API_REFERENCE.md`
- **Use IDE integration**: VS Code tasks for instant context checks
- **Weekly maintenance**: `python tools/living_documentation_generator.py`
- **Context preservation**: Critical solutions stored in persistent memory system

## 🚨 Context Drift Prevention
- **Multiple protection layers**: Memory system, keyword triggers, pre-dev checklist
- **Automatic detection**: Context awareness system catches reinvention attempts
- **Persistent reminders**: Always-visible files that can't be ignored
- **IDE integration**: One-click context checks and function lookup
- **Living documentation**: Solution catalog stays current automatically

## ⚠️ Critical Warnings
- **DO NOT** modify files in protected core modules without authorization
- **DO NOT** bypass quality gates unless using "WIP:" commit prefix
- **DO NOT** guess at function signatures - they are documented
- **DO NOT** ignore failing core tests - they indicate real mathematical issues
- **DO NOT** reinvent existing solutions - use context awareness system first

## 🏆 Success Indicators
- All 90 core tests passing
- Quality dashboard shows "EXCELLENT" status
- Core protection system shows "CLEAN" status
- Zero syntax errors across all source files

## 📖 Mathematical Foundation
- **Dau Chapter 14/15**: Formal transformation rules
- **Dau Chapter 16-17**: Ligature algorithms and soundness
- **Dau Chapter 18**: Linear format parsing/generation
- **Dau Chapter 20**: Syntactic equivalence checking
- **Dau Chapter 21**: Diagram interaction architecture (see BOTTOM_UP_D3_ARCHITECTURE.md)
- **Complete validation**: 100% comprehensive coverage achieved

## 🏗️ Layout Engine Architecture
- **Unified D3 Recursive Engine**: `src/unified_d3_engine.py` - **PRODUCTION ENGINE** (integrated 2025-10-12, refined 2025-10-12)
- **DiagramController Integration**: DiagramController now uses UnifiedD3Engine
- **Architecture**: Pure recursive bottom-up with shell-and-core D3 worker
  - **Python Orchestrator**: Recursive traversal of cut hierarchy (leaf-first)
  - **D3 Worker**: `src/unified_d3_worker.js` - Two-phase shell-and-core simulation with force optimization
  - **SVG Renderer**: `src/simple_svg_renderer.py` - Direct LayoutDTO to SVG with Dau-compliant styling
- **Shell-and-Core Model**: TWO simulations per cut with balanced force hierarchy
  - **SHELL Simulation**: Layout obstacles (child cuts) using collision + center forces
  - **CORE Simulation**: Position content with obstacles as exponential repellers
  - **Force Balance**: Exponential obstacle avoidance > charge repulsion > link/collision forces
  - **Area Correctness**: Hard boundaries prevent elements from escaping proper cuts
- **Key Features**:
  - **Iron-clad EGI.area compliance**: Recursive coordinate translation ensures correctness
  - **No overlapping cuts**: Shell simulation with obstacle collision prevents sibling overlap
  - **No escaped elements**: Per-cut coordinate system with recursive translation
  - **Cache clearing**: Fresh state for each layout prevents ghost elements
  - **Deterministic layouts**: Seeded random for reproducible results
  - **Dau compliance**: Sheet is invisible, proper cut nesting
- **LayoutDTO Structure**:
  - `vertex_positions`: Dict[ElementID, Point]
  - `predicate_positions`: Dict[ElementID, Point]
  - `cut_bounds`: Dict[ElementID, BoundingBox]
  - `ligature_paths`: List[LigaturePath]
  - `area_hierarchy`: Dict[ElementID, Set[ElementID]]
- **Testing**: Validated on 15-graph tomos with stable, correct results
- **References**: See `BOTTOM_UP_D3_ARCHITECTURE.md` for complete architectural details

## 🎯 User Edit System & Deterministic Layouts
- **Layout Deltas**: Support for user modifications to vertex/edge positions (planned)
- **Deterministic seeding**: Fixed seed values ensure identical layouts for same EGI input
- **Pinned nodes**: User-specified positions can be fixed in D3 simulation (supported via fx/fy)
- **Extensible architecture**: LayoutDTO structure ready for future interactive editing features

## 🎮 DiagramController - Layered Command Architecture
- **Production Status**: Using UnifiedD3Engine (integrated 2025-10-12)
- **Layered Architecture**: Clean separation between "what" (use case logic) and "how" (diagram manipulation)
- **Command Pattern**: High-level commands in Organon/Ergasterion/Agon orchestrate low-level controller operations
- **Layout Engine**: UnifiedD3Engine with recursive bottom-up and shell-and-core physics
- **State Management**: Immutable EGI transformations with persistent user constraints across operations
- **Validation System**: Multi-layer validation for positions, paths, and formal rule preconditions
- **Undo/Redo Support**: Complete command history management with CommandExecutor
- **Three Use Cases**:
  - **Organon**: Visualization & exploration (read-only view operations)
  - **Ergasterion**: Learning & practice (rule-based EGI modifications)
  - **Agon**: Formal interaction & gameplay (Endoporeutic Game mechanics)
- **Formal Rules**: Complete implementation of DC+/-, INS/ERA, IT+/- with Dau compliance
- **Production Ready**: Comprehensive test suite with 90 passing tests
- **Critical Fixes Applied** (2025-10-01):
  - ✅ Ligatures now connect perfectly to vertices (no quantization errors)
  - ✅ Logical area validation ensures vertices stay within proper cuts
  - ✅ User position overrides applied before ligature routing
  - ✅ Invalid positions gracefully rejected to preserve EG correctness
- **Integration Complete** (2025-10-12):
  - ✅ DiagramController switched to UnifiedD3Engine
  - ✅ Shell-and-core model eliminates force-fighting
  - ✅ Recursive bottom-up respects EGI.area mapping
  - ✅ LayoutDTO standardized (vertex_positions, predicate_positions, cut_bounds)
- **Dau-Compliant Styling** (2025-10-12):
  - ✅ Proper line weight hierarchy: cut (1.5px) < ligature (2.5px) < vertex diameter (7px)
  - ✅ Transparent predicate backgrounds with minimal padding
  - ✅ Ligatures connect at predicate boundaries and vertex centers
  - ✅ Vertex spots continuous with ligatures (no boundary hook)
  - ✅ Vertex labels positioned beside spots to avoid collisions
  - ✅ Boundary calculations in LayoutDTO (not renderer)
  - ✅ Exponential obstacle forces enforce hard cut boundaries
  - ✅ Charge forces improve geometric distribution
- **Known Limitations**: Layout not always optimal for complex graphs, but functional for MVP
- **Test Results**: 90/90 core tests passing, 3/3 GUI Organon tests passing

## 🔄 Diachronic Delta Workflow (PRODUCTION)
- **Architecture**: State_n = (EGI_n, LayoutDeltas_n) - Complete diachronic state representation
- **Status**: Fully implemented and tested (2025-10-13)
- **Documentation**: See `DIACHRONIC_DELTA_WORKFLOW.md` and `LAYOUT_DELTA_QUICK_REFERENCE.md`

### Core Components
- **Fast Path Updates**: Logic-indifferent element movements (~5ms, no D3 simulation)
- **Delta Reconciliation**: Intelligent preservation/discarding after EGI transformations
- **File Persistence**: Layout deltas saved/loaded in JSON format alongside EGI
- **Area Validation**: Enforces Dau's iron-clad principle - elements cannot escape logical areas

### Workflow Steps
1. **User Drags Element**: 
   - Fast path → DTO updated directly → Ligatures rerouted → Display refreshed
   - Delta stored: `{element_id: {type: 'vertex_position', position: [x, y]}}`
   
2. **Apply Transformation Rule**:
   - State_n captured (EGI_n, Deltas_n)
   - EGI transformed (EGI_n → EGI_n+1)
   - Delta reconciliation (Deltas_n → Deltas_n+1)
   - Full relayout with inherited deltas
   
3. **Save File**:
   - EGI serialized to JSON
   - Layout deltas appended: `{"layout_deltas": {...}}`
   - Status: "Saved: file.json (N position overrides)"
   
4. **Load File**:
   - EGI loaded from JSON
   - Layout deltas restored
   - Fast path applied → Exact layout recreated

### Area Containment Validation
- **Vertices**: Point must stay within area bounds (EGI.area mapping)
- **Predicates**: Entire text box must fit within area bounds
- **Validation Feedback**: Clear error messages with suggestions
- **Iron-Clad Enforcement**: Elements cannot violate logical containment

### Integration
- **Organon Mode**: Save/Load with layout deltas via "💾 Save EGI..." button
- **Ergasterion Mode**: Save/Load with layout deltas via "💾 Save..." button
- **Both Modes**: Deltas persist through transformations, survive save/reload cycles

### Usage Example
```python
# In DiagramController
controller.update_element_position("v_abc123", (250.5, 180.3))
# → Validates area containment
# → Updates layout_deltas
# → Triggers fast path update
# → Ligatures reroute automatically

# Save with deltas
save_egi_json(egi, "my_diagram.json")  # Includes layout_deltas

# Load with deltas
egi = load_egi_json("my_diagram.json")  # Deltas restored automatically
```

### Benefits
- **Performance**: Fast path is 40x faster than full relayout
- **Persistence**: User layouts survive sessions
- **Intelligence**: Deltas reconcile correctly after transformations
- **Correctness**: Area validation maintains mathematical rigor

## 🎨 Style System Architecture
- **JSON-based styles**: Platform-independent style definitions in `styles/` directory
- **Style loader**: `src/style_loader.py` - Loads and validates style definitions
- **Schema validation**: `styles/style_schema.json` - Ensures style consistency
- **Built-in styles**: DAU-compliant (default), Peirce-authentic, Sowa-compliant
- **Polarity convention**: Even polarity (positive) unshaded, odd polarity (negative) shaded
- **Optional features**: Arity numbers, variable labels, alternating shading
- **Transformation support**: Double cut highlighting, isomorphic matching, collapsed contexts
- **Complete documentation**: `docs/STYLE_SYSTEM_GUIDE.md` - User and developer guide

## 🖥️ GUI Implementation - Three-Mode Architecture
- **Status**: Phase 1 Complete - Organon Functional (2025-10-02)
- **Framework**: PySide6 (Qt6)
- **Launch**: `python src/gui_clean/main_application.py`
- **Architecture**: Clean implementation, zero legacy dependencies

### Universe of Discourse Model (✅ PRODUCTION 2025-10-14)
- **UniverseOfDiscourse**: Synchronic (current state) + Diachronic (DAG history) + LayoutDeltas
- **DAG-Based History**: Branching transformation history (not linear sequences)
- **TomosService**: Unified API with index-based browsing, lazy loading, efficient storage
- **Categories**: Static (Literature, Canonical) vs Dynamic (Inquiry, Theorem Proof, EPG Session, Practice)
- **Backward Compatibility**: `GraphEntity` = `UniverseOfDiscourse` (all old code works unchanged)
- **Documentation**: `docs/UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md`, `docs/UOD_DEVELOPER_GUIDE.md`, `docs/DAG_HISTORY_ARCHITECTURE.md`
- **Scalability**: Designed for 1000+ states, DAG supports branching exploration

### DAG-Based Transformation History (✅ PRODUCTION 2025-10-14)
**Current Status**: Fully implemented and tested  
**Documentation**: `docs/DAG_HISTORY_ARCHITECTURE.md`

**Key Features**:
- Branch from any historical state (not just linear sequences)
- Multiple transformation paths in single UoD
- Branch point detection and tracking
- Path finding (BFS for shortest, DFS for all paths)
- DAG statistics and analysis
- 100% backward compatible with linear history

**API Patterns**:
```python
from egi_transformation_history import EGITransformationHistory, HistoryBranchType

# Create history (backward compatible)
history = EGITransformationHistory(initial_egi, "Initial state")

# Add transformations (works linearly or with branching)
history.add_transformation(rule_name, context, result)

# Branch from any state
branch_id = history.create_branch_from_state(
    source_state_id,
    HistoryBranchType.EXPLORATION,
    "Try alternative approach"
)

# Query DAG structure
paths = history.get_all_paths_from_root(target_state_id)
children = history.get_child_states(state_id)
is_branch = history.is_branch_point(state_id)
stats = history.get_dag_statistics()

# Find paths between states
sequence = history.get_transformation_sequence(from_state, to_state)
```

**Use Cases**:
- **Theorem Proving**: Explore multiple proof strategies
- **Learning**: Try "what if?" without losing original work
- **Collaboration**: Multiple researchers, shared UoD
- **Real Inquiry**: Branching reflects actual reasoning

**Performance**:
- Add transformation: O(1)
- Create branch: O(1)
- Find shortest path: O(V + E)
- Efficient for 10-1000 states

**Testing**: `tools/test_history_dag.py` (5/5 tests passing)

### Organon Mode (⚠️ ~40% Complete - 2025-10-14)
- **Purpose**: Exploration and tomos management
- **Status**: Basic viewing works, needs import/export and metadata editing
- **Documentation**: `ORGANON_COMPLETE_SPECIFICATION.md` (full feature list)

**✅ Implemented**:
- Tomos browser with static/dynamic filtering
- Load and display UoDs (EGI + metadata + history)
- Metadata panel (read-only)
- History timeline with time-travel navigation
- SVG export only
- Theme support (Light/Dark/System)

**❌ Missing Critical Features**:
- Import system (EGIF, CGIF, JSON) - 0% done
- Export system (EGIF, CGIF, full JSON) - need all formats
- Metadata editing - read-only only
- State comparison across history - not implemented
- Tomos search/filter - basic only
- UoD operations (delete, duplicate, rename) - not implemented

**Priority Next Steps**:
1. EGIF import (for literature)
2. Full export (EGIF, CGIF, JSON with metadata)
3. Metadata edit dialog
4. State comparison views

### Ergasterion Mode (⚠️ Foundation Integrated, Untested - 2025-10-14)
- **Purpose**: Interactive editing and transformation practice
- **Status**: UoD integration complete, needs testing and refinement

**✅ Implemented**:
- Interactive canvas with mouse interaction
- Element selection (single and multi-select with Ctrl)
- Drag-and-drop repositioning with validation
- Transformation toolbar (DC+/-, INS, ERA, IT+/-)
- File operations (New, Load, Save)
- UoD integration (creates practice sessions)
- Save to Tomos with promotion to historical
- Organon → Ergasterion handoff with source UoD tracking

**⚠️ Needs Testing**:
- Transformation rule application
- History tracking in practice sessions
- Save/load workflow
- Layout delta preservation
- Error handling

**🔄 Future Enhancements**:
- Visual selection indicators, hover feedback
- Undo/redo UI (CommandExecutor integration)
- Element palette, cut creation
- Practice mode tutorials
- DAG branching UI ("Branch from here" button)

### Agon Mode (⏳ Phase 3)
- **Purpose**: Formal reasoning and Endoporeutic Game
- **Planned**: Game board, move validation, umpire evaluation, game history

### Key Documentation
- **Data Models**: `EGI_DATA_MODEL_SUMMARY.md`, `DIACHRONIC_SYNCHRONIC_DATA_MODEL_ANALYSIS.md`
- **Architecture**: `GRAPH_ENTITY_SCALABILITY_ARCHITECTURE.md`
- **User Guide**: `ORGANON_READY.md`
- **Migration**: `tools/migrate_corpus_to_entities.py`

## 🚀 Production Readiness
- **Enterprise-grade**: All performance benchmarks passing
- **Mathematical correctness**: Comprehensive validation complete
- **API stability**: Protected core ensures no breaking changes
- **Quality assurance**: Automated monitoring and enforcement
- **Core Architecture**: UoD model + DAG history + TomosService (✅ Production)
- **GUI Status** (2025-10-14):
  - ⚠️ **Organon**: ~40% complete (viewing works, needs import/export/metadata editing)
  - ⚠️ **Ergasterion**: Foundation integrated (needs testing and refinement)
  - ⏳ **Agon**: Future development
- **Test Coverage**: 106/106 tests passing (90 core + 8 UoD + 8 TomosService)

---

**Remember**: The coherence framework exists to eliminate guesswork. When in doubt, check the documentation rather than guessing!
