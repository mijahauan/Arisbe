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
- **Layout engine tests**: `python tools/test_definitive_egi_layout_engine.py` (synthetic tests)
- **Corpus validation**: `python tools/test_definitive_corpus_graphs.py` (real-world graphs)
- **Style system tests**: `python -m pytest tests/test_style_integration.py`
- **Readability optimization tests**: `python -m pytest tests/test_readability_optimizer.py`
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

### Definitive Layout Engine
```python
from definitive_egi_layout_engine import DefinitiveEGILayoutEngine
from graphviz_svg_renderer import GraphvizSVGRenderer

layout_engine = DefinitiveEGILayoutEngine()
svg_renderer = GraphvizSVGRenderer()

# Generate layout DTO
dto = layout_engine.generate_layout(egi)

# Render to SVG
svg_path = svg_renderer.save_svg(dto, "Graph Title", "Description", "filename")
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
- **Definitive EGI Layout Engine**: `src/definitive_egi_layout_engine.py` - Production-ready three-step approach
- **Area-Aware Pathfinder**: `src/area_aware_pathfinder.py` - Legal corridor A* pathfinding for ligatures
- **Graphviz SVG Renderer**: `src/graphviz_svg_renderer.py` - Clean SVG output with mathematical precision
- **Three-step pipeline**: Unified force-directed layout → Bottom-up bounding boxes → Area-aware ligature routing
- **Revolutionary positioning**: ALL content positioned together using neato (eliminates linear layouts)
- **Smart container sizing**: Cut boundaries calculated AFTER content positioning (bottom-up approach)
- **Legal corridor pathfinding**: A* respects EGI logical containment hierarchy with custom cost functions
- **Complete corpus validation**: Handles 14/15 Arisbe corpus graphs with 93.3% success rate
- **Excellent quality metrics**: 97.6% overall layout quality, 100% 2D space utilization, 2.0 avg ligature complexity
- **Platform-independent DTO**: Clean separation between layout logic and rendering technology
- **Production-ready**: Validated on real research examples from Peirce, Dau, Sowa, Roberts literature

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

## 🚀 Production Readiness
- **Enterprise-grade**: All performance benchmarks passing
- **Mathematical correctness**: Comprehensive validation complete
- **API stability**: Protected core ensures no breaking changes
- **Quality assurance**: Automated monitoring and enforcement

---

**Remember**: The coherence framework exists to eliminate guesswork. When in doubt, check the documentation rather than guessing!
