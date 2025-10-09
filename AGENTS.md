# AGENTS.md

## 🔒 Core Protection System
- **16 protected core modules** - Cannot be modified without explicit authorization
- **87 core tests** must always pass - These validate the mathematical foundation
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
- **Core tests**: `python -m pytest tests/test_*_comprehensive.py tests/test_*_working.py`
- **DiagramController tests**: `python tools/test_diagram_controller.py` (11/11 passing)
- **Workflow simulation tests**: `python tests/end_to_end/test_user_workflows.py` (4/8 passing, position persistence edge cases)
- **Golden master tests**: `python tests/end_to_end/test_golden_masters.py` (4-6/6, 67-100%)
- **Layout engine tests**: `python tools/test_definitive_egi_layout_engine.py` (synthetic tests)
- **Corpus validation**: `python tools/test_definitive_corpus_graphs.py` (real-world graphs)
- **Style system tests**: `python -m pytest tests/test_style_integration.py`
- **Readability optimization tests**: `python -m pytest tests/test_readability_optimizer.py`
- **Connection port tests**: `python tools/test_connection_ports.py` (port configuration validation)
- **Corpus connection port tests**: `python tools/test_corpus_connection_ports.py` (full corpus validation)
- **GUI Organon tests**: `python tools/test_gui_organon.py` (GUI smoke tests, 3/3 passing)
- **Expected results**: 190+ passing, 0 failing, 62 properly skipped

## 🏗️ Build and Development
- **Environment**: `conda activate CGIF` (Python 3.12.10)
- **Dependencies**: See `requirements.txt`
- **Core modules location**: `src/` directory (16 protected modules)
- **Test location**: `tests/` directory (87 core validation tests)

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

### Definitive Three-Pass Layout Engine
```python
from definitive_three_pass_engine import DefinitiveThreePassEngine
from style_loader import StyleLoader

# Load style
style_loader = StyleLoader()
style = style_loader.load_default_style()

# Generate layout with three-pass engine
engine = DefinitiveThreePassEngine()
dto = engine.generate_layout(egi, style, output_path_prefix)
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
- All 87 core tests passing
- Quality dashboard shows "EXCELLENT" status
- Core protection system shows "CLEAN" status
- Zero syntax errors across all source files

## 📖 Mathematical Foundation
- **Dau Chapter 14/15**: Formal transformation rules
- **Dau Chapter 16-17**: Ligature algorithms and soundness
- **Dau Chapter 18**: Linear format parsing/generation
- **Dau Chapter 20**: Syntactic equivalence checking
- **Dau Chapter 21**: Diagram interaction architecture (see LAYOUT_ENGINE_ARCHITECTURE_PLAN.md)
- **Complete validation**: 100% comprehensive coverage achieved

## 🏗️ Layout Engine Architecture
- **Definitive Three-Pass Engine**: `src/definitive_three_pass_engine.py` - **PRODUCTION ENGINE** (integrated 2025-10-09)
- **DiagramController Integration**: DiagramController now uses DefinitiveThreePassEngine
- **Three-step pipeline**: Graphviz containers → D3 force content → A* ligature routing
  - **Pass 1**: Graphviz neato for cut hierarchy and boundaries (with ports)
  - **Pass 2**: D3 force simulation for element positioning within cuts
  - **Pass 3**: Area-aware A* pathfinding for ligature routing
- **D3 Layout Worker**: `src/d3_layout_worker.js` - Node.js worker for force simulation
  - Port link detection via ID pattern matching
  - Adaptive centering (disabled for port-connected nodes)
  - Obstacle ejection for spatial/logical correspondence
  - Force parameters: port links (50.0 strength, 5px dist), normal links (4.0, 30/50px)
  - **Pinned positions**: User overrides via `pinned` flag + `fx`/`fy`
  - **Deterministic seeding**: Reproducible layouts with seed parameter
- **LayoutDeltas Support**: User position overrides, custom ligature paths, deterministic layouts
- **Area-Aware Pathfinder**: `src/area_aware_pathfinder.py` - Legal corridor A* pathfinding for ligatures
- **Graphviz SVG Renderer**: `src/graphviz_svg_renderer.py` - Clean SVG output with mathematical precision
- **Test corpus**: `python tools/test_definitive_corpus.py` - Validates all 14 graphs
- **Known issues**:
  - Port link force (50.0) too strong vs normal links (4.0) - causes elements to drift apart
  - Elements with both port and normal links prioritize ports over same-cut relationships
  - Some position updates may not fully persist across relayouts (4/8 workflow tests passing)
  - Needs force balancing in future iteration

## 🔌 Connection Port System
- **Pre-defined connection ports**: EdgeLabel bounding boxes have numbered ports mirroring ν mapping
- **Optimal port assignment**: Vertices connect to nearest available ports to minimize crossings
- **Smart port creation**: Unary predicates choose optimal direction (N/S/E/W) based on vertex position
- **Mathematical precision**: Perfect ν mapping correspondence with visual optimization
- **Production validation**: 100% success rate across entire 15-graph corpus with zero crossing issues
- **Port placement logic**: Systematic cardinal/intercardinal directions based on predicate arity
- **Visual quality**: Eliminates ligature crossings and text obstruction for professional diagrams
- **Two-level optimization**: Smart port creation + nearest port assignment for maximum effectiveness
- **Context-aware algorithms**: Uses actual vertex positions for optimal port direction selection
- **Comprehensive testing**: `python tools/test_corpus_connection_ports.py` validates entire corpus

## 🎯 User Edit System & Deterministic Layouts
- **Layout Deltas**: `LayoutDeltas` data structure for user modifications to vertex/edge positions and ligature paths
- **Deterministic seeding**: Fixed seed values ensure identical layouts for same EGI input
- **Pinned nodes**: User-specified positions become fixed points in neato layout simulation
- **Custom ligature paths**: User-defined paths with collision and logical constraint validation
- **Constrained layout**: neato arranges free nodes around pinned user positions
- **Path validation**: Custom paths validated for collisions and area-aware logical constraints
- **Fallback mechanism**: Invalid custom paths automatically fall back to A* pathfinding
- **GUI preparation**: Data structures ready for diagram controller and interactive editing

## 🎮 DiagramController - Layered Command Architecture
- **Production Status**: Using DefinitiveThreePassEngine (integrated 2025-10-09)
- **Layered Architecture**: Clean separation between "what" (use case logic) and "how" (diagram manipulation)
- **Command Pattern**: High-level commands in Organon/Ergasterion/Agon orchestrate low-level controller operations
- **State Management**: Immutable EGI transformations with persistent user constraints across operations
- **Validation System**: Multi-layer validation for positions, paths, and formal rule preconditions
- **Undo/Redo Support**: Complete command history management with CommandExecutor
- **Three Use Cases**:
  - **Organon**: Visualization & exploration (read-only view operations)
  - **Ergasterion**: Learning & practice (rule-based EGI modifications)
  - **Agon**: Formal interaction & gameplay (Endoporeutic Game mechanics)
- **Formal Rules**: Complete implementation of DC+/-, INS/ERA, IT+/- with Dau compliance
- **Production Ready**: Comprehensive test suite with 100% validation coverage
- **Critical Fixes Applied** (2025-10-01):
  - ✅ Ligatures now connect perfectly to vertices (no quantization errors)
  - ✅ Logical area validation ensures vertices stay within proper cuts
  - ✅ User position overrides applied before ligature routing
  - ✅ Invalid positions gracefully rejected to preserve EG correctness
- **Integration Complete** (2025-10-09):
  - ✅ DiagramController switched to DefinitiveThreePassEngine
  - ✅ LayoutDeltas support fully implemented (pinned positions, custom paths, deterministic seeding)
  - ✅ DTO compatibility maintained (style attributes, annotations)
- **Test Results**: 11/11 DiagramController tests, 4/8 workflow tests (position persistence edge cases), 3/3 GUI Organon tests

## 🎨 Style System Architecture
- **JSON-based styles**: Platform-independent style definitions in `styles/` directory
- **Style loader**: `src/style_loader.py` - Loads and validates style definitions
- **Schema validation**: `styles/style_schema.json` - Ensures style consistency
- **Built-in styles**: DAU-compliant (default), Peirce-authentic, Sowa-compliant
- **Polarity convention**: Even polarity (positive) unshaded, odd polarity (negative) shaded
- **Optional features**: Arity numbers, variable labels, alternating shading
- **Transformation support**: Double cut highlighting, isomorphic matching, collapsed contexts
- **Complete documentation**: `docs/STYLE_SYSTEM_GUIDE.md` - User and developer guide

## 🔧 Readability Optimization System
- **Logic-indifferent optimizations**: Improve visual clarity without affecting logical structure
- **Collision avoidance**: Automatic detection and resolution of element overlaps
- **Spacing optimization**: Force-directed adjustment for uniform element distribution
- **Three optimization levels**: Minimal, Standard, Aggressive with configurable constraints
- **Iron-clad preservation**: All optimizations maintain spatial-logical correspondence
- **Style-aware constraints**: Optimization parameters derived from active style specification
- **Comprehensive testing**: `tests/test_readability_optimizer.py` - Full test coverage

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

### Ergasterion Mode (⏳ Phase 2)
- **Purpose**: Interactive editing and transformation practice
- **Planned**: Element palette, transformation panel, undo/redo, session management

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
- **GUI Phase 1**: Organon functional and production-ready

---

**Remember**: The coherence framework exists to eliminate guesswork. When in doubt, check the documentation rather than guessing!
