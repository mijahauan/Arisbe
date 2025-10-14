# AGENTS.md

## 🔒 Core Protection System
- **16 protected core modules** - Cannot be modified without explicit authorization
- **90 core tests** must always pass - These validate the mathematical foundation
- **Check protection status**: `python tools/core_protection_system.py --report`
- **Override protection** (authorized changes only): `export ARISBE_CORE_OVERRIDE=true`

## 📚 Living Documentation System
- **Auto-updating documentation**: Documentation stays current with codebase changes
- **Context awareness system**: `tools/context_awareness_system.py` prevents reinvention
- **Persistent memory integration**: Critical framework awareness stored in memory system
- **Framework amnesia recovery**: `FRAMEWORK_AMNESIA_RECOVERY.md` for complete context recovery
- **Pre-development checklist**: `.arisbe_context_check` mandatory before development
- **IDE integration**: VS Code tasks for instant context checks

## 📚 API Discovery Protocol
- **NEVER guess function signatures** - Use `ARISBE_CORE_API_REFERENCE.md` for exact signatures
- **Complete API documentation**: 57 classes, 19 functions fully documented
- **Usage patterns**: See `CORE_API_USAGE_GUIDE.md` for common development patterns
- **Quick function lookup**: `grep -i "function_name" ARISBE_CORE_API_REFERENCE.md`

## 🧪 Testing Requirements
- **Quality check**: `python tools/quality_gate_system.py` (runs automatically on commit)
- **System status**: `python tools/daily_quality_dashboard.py`
- **Core tests**: `python -m pytest tests/` (90/90 passing)
- **GUI Organon tests**: `python tools/test_gui_organon.py` (3/3 passing)
- **Expected results**: 90 core tests passing, 0 failing

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
- **Forgot the framework?** Read `COHERENCE_FRAMEWORK_REMINDER.md` first
- **Complete recovery guide**: `FRAMEWORK_AMNESIA_RECOVERY.md`
- **Persistent context system**: `PERSISTENT_CONTEXT_SYSTEM.md` for complete workflow
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

### Corpus Management (⚠️ INTERIM - CONSOLIDATION PENDING)
**Current Status**: Multiple overlapping systems (see `DATA_PERSISTENCE_MODEL_SUMMARY.md`)  
**Quick Reference**: `CORPUS_API_QUICK_REFERENCE.md`

**For Organon (Read-Only)**:
```python
from corpus_index import load_index, graph_paths
from egi_io import load_egi_json

# Browse corpus
index = load_index()
graph_id = index['entries'][0]['id']

# Load EGI
gdir = Path(f"corpus/graphs/{graph_id}")
paths = graph_paths(gdir)
egi = load_egi_json(paths['egi'])
```

**For Ergasterion/Agon (With History)**:
```python
from graph_entity import GraphEntity, EntityMetadata, EntityType, EntityCategory

# Create entity with history support
entity = GraphEntity(metadata=metadata, current_egi=egi)
entity.promote_to_historical("Initial state")

# Access history
entity.history.add_transformation(...)
```

**⚠️ IMPORTANT**: 
- **Current corpus**: Uses `corpus_index.py` (15 graphs, directory-per-graph)
- **Recommended model**: `GraphEntity` (unified diachronic-synchronic)
- **Future**: `CorpusService` consolidation (1 week estimated)
- **See documentation**: `DATA_PERSISTENCE_MODEL_SUMMARY.md` for complete analysis

## 🔄 Living Documentation Workflow
- **Before development**: `python tools/context_awareness_system.py --check "task"`
- **Check existing solutions**: `grep -i "function_name" ARISBE_CORE_API_REFERENCE.md`
- **Verify no duplication**: Review `.arisbe_context_check` checklist
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
- **Testing**: Validated on 15-graph corpus with stable, correct results
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

### Unified Entity Model
- **GraphEntity**: Synchronic (current state) + Diachronic (transformation history)
- **EntityStorage**: Hybrid snapshots + deltas, JSONL streaming, LRU caching
- **Categories**: Peirce, Scholars, Canonical, EPG, Theorem Proving, Domain Modeling, User Created
- **Scalability**: Designed for 1000+ states, currently handles 15 corpus graphs

### Organon Mode (✅ Functional)
- **Purpose**: Exploration and corpus management (read-only)
- **Corpus Browser**: Category filtering, real-time search, metadata display
- **Diagram Display**: SVG rendering via DiagramController
- **EGIF Panel**: Linear form display
- **Export**: SVG output
- **Theme Support**: Light/Dark/System modes
- **Corpus**: 15 graphs (3 Peirce, 6 Scholars, 6 User/Test)
- **Test**: `python tools/test_gui_organon.py` (3/3 passing)

### Ergasterion Mode (✅ Phase 1 Complete, 🔄 Phase 2 In Progress)
- **Purpose**: Interactive editing and transformation practice
- **Phase 1 Complete** (2025-10-13):
  - Interactive canvas with mouse interaction
  - Element selection (single and multi-select with Ctrl)
  - Drag-and-drop repositioning with validation
  - Transformation toolbar (DC+/-, INS, ERA, IT+/-)
  - File operations (New, Load, Save)
  - Organon ↔ Ergasterion handoff
- **Phase 2 Planned**: Visual selection indicators, hover feedback, undo/redo UI
- **Phase 3 Planned**: Element palette, cut creation, practice mode tutorials
- **Status**: `ERGASTERION_PHASE1_COMPLETE.md` for details

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
- **GUI Status**:
  - ✅ **Organon**: Functional and production-ready (corpus browser, visualization, export)
  - ✅ **Ergasterion Phase 1**: Interactive canvas complete (selection, drag-drop, transformations)
  - 🔄 **Ergasterion Phase 2-3**: Visual feedback and element creation (planned)
  - ⏳ **Agon**: Future development

---

**Remember**: The coherence framework exists to eliminate guesswork. When in doubt, check the documentation rather than guessing!
