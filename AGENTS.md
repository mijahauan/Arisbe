# AGENTS.md

## 🔒 Core Protection System
- **16 protected core modules** - Cannot be modified without explicit authorization
- **87 core tests** must always pass - These validate the mathematical foundation
- **Check protection status**: `python tools/core_protection_system.py --report`
- **Override protection** (authorized changes only): `export ARISBE_CORE_OVERRIDE=true`

## 📚 API Discovery Protocol
- **NEVER guess function signatures** - Use `ARISBE_CORE_API_REFERENCE.md` for exact signatures
- **Complete API documentation**: 57 classes, 19 functions fully documented
- **Usage patterns**: See `CORE_API_USAGE_GUIDE.md` for common development patterns
- **Quick function lookup**: `grep -i "function_name" ARISBE_CORE_API_REFERENCE.md`

## 🧪 Testing Requirements
- **Quality check**: `python tools/quality_gate_system.py` (runs automatically on commit)
- **System status**: `python tools/daily_quality_dashboard.py`
- **Core tests**: `python -m pytest tests/test_*_comprehensive.py tests/test_*_working.py`
- **Layout engine tests**: `python -m pytest tests/test_layout_engine_ironclad.py tests/test_layout_engine_styled.py`
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
- **Automated reminders**: `python tools/coherence_reminder_system.py`
- **Quick status**: `python tools/core_protection_system.py --report`

## 🔧 Essential Tools
- **Daily quality dashboard**: `python tools/daily_quality_dashboard.py`
- **Core protection check**: `python tools/core_protection_system.py`
- **API documentation generator**: `python tools/extract_core_api.py`
- **Coherence reminders**: `python tools/coherence_reminder_system.py`

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

### Transformation Rules
```python
from formal_transformation_rules import DeiterationRule, TransformationContext
rule = DeiterationRule()
context = TransformationContext(source_egi=egi, target_area="sheet", ...)
result = rule.apply_transformation(context)
```

## ⚠️ Critical Warnings
- **DO NOT** modify files in protected core modules without authorization
- **DO NOT** bypass quality gates unless using "WIP:" commit prefix
- **DO NOT** guess at function signatures - they are documented
- **DO NOT** ignore failing core tests - they indicate real mathematical issues

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
- **Iron-clad layout engine**: `src/layout_engine_ironclad.py` - Production-ready with guaranteed spatial-logical correspondence
- **Style-aware layout engine**: `src/layout_engine_styled.py` - Extends iron-clad with style-aware spatial calculations
- **Readability optimizer**: `src/readability_optimizer.py` - Logic-indifferent optimizations for visual clarity
- **No break points**: Spatial arrangement exactly matches EGI area mapping with mathematical precision
- **Sibling cut handling**: Properly separates cuts that share the same parent area (no superimposition)
- **Complete corpus validation**: Handles 14/15 Arisbe corpus graphs with 93.3% success rate
- **Platform-independent DTO**: Clean separation between layout logic and rendering technology
- **Five-layer architecture**: EGI → Style-Aware Layout Engine → Readability Optimizer → LayoutDTO → Renderer

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
