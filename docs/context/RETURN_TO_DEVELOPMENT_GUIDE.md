# Return to Arisbe Development Guide
**Coherence Framework Operational - Ready for Development**

**Date**: 2025-10-14  
**Framework Status**: ✅ Fully Operational

---

## Executive Summary

The coherence framework is now complete and operational. This guide explains how to return to Arisbe development with the framework supporting your work.

**What Changed**: Context persistence, documentation automation, and code archaeology detection are now active.

**What You Get**: AI assistants can recover full context in < 5 minutes, documentation stays synchronized, and code quality is automatically monitored.

---

## Quick Start

### For Humans

**When You Return to Work**:
1. Review `.coherence_session_state.json` (2 min) - See recent work
2. Check `CURRENT_PLAN.md` (1 min) - See active priorities
3. Run `python tools/daily_quality_dashboard.py` (30 sec) - See system status

**Daily Workflow**:
```bash
# Morning check
python tools/daily_quality_dashboard.py

# Work on code...

# Before committing
git commit -m "Your message"
# Hook auto-runs: session update, API doc regen, quality checks
```

### For AI Assistants

**On Session Start**:
1. **Read** `.coherence_session_state.json` → Full context
2. **Read** `WHAT_WORKS_NOW.md` → Component status
3. **Read** `CURRENT_PLAN.md` → Active work
4. **Read** `ARISBE_CORE_API_REFERENCE.md` → API signatures

**Total Time**: < 5 minutes

**Result**: Complete understanding of project state, recent work, priorities, and API.

---

## What the Framework Provides

### Automatic (Zero Effort)

**Session State Auto-Updates** (Every Commit):
- Last updated timestamp
- Recent accomplishments from git log
- Git branch and commit hash
- Modified files list

**API Documentation Sync** (Every Commit):
- Regenerates when protected modules change
- AST-based extraction (accurate)
- Auto-stages with commit

**Quality Gates** (Every Commit):
- Core protection (16 protected modules)
- Test validation (90/90 tests)
- Syntax checking
- Session state updates

### On-Demand (Single Command)

**Component Index**:
```bash
python tools/generate_working_code_index.py
# Generates WHAT_WORKS_NOW.md (157 modules analyzed)
```

**Code Archaeology Detection**:
```bash
python tools/detect_code_archaeology.py
# Generates CODE_CLEANUP_CANDIDATES.md (41 candidates found)
```

**Architecture Validation**:
```bash
python tools/validate_architecture_docs.py
# Validates docs against code (found 63 invalid refs)
```

**Coverage Measurement**:
```bash
python tools/integrate_coverage_measurement.py --html
# Generates coverage report (currently 11%)
```

---

## Current System Status

### Test Status
- **Core Tests**: 90/90 passing (100%)
- **Coverage**: 11.0% (baseline established)
- **Protected Modules**: 16 modules validated

### Documentation Status
- **API Docs**: 4 protected modules documented
- **Stable API Docs**: 4 Tier 2 modules documented
- **Architecture Drift**: 63 invalid references identified
- **Fix Plan**: Available in DOCUMENTATION_DRIFT_FIX_PLAN.md

### Code Quality
- **Debug Scripts**: 18 identified for cleanup
- **Orphaned Modules**: 23 detected
- **Deprecated Files**: 1 found
- **Total Analyzed**: 157 modules

---

## Arisbe Development Priorities

### Strategic Focus (From User Memory)

**DEFER UNTIL LATER**:
- GUI components and logic-spatial correspondence
- Larger application structure components (Organon/Ergasterion/Agon)

**IMMEDIATE FOCUS**:

1. **Transformation System Components**:
   - Reliable transformation system for arbitrary graphs of any size
   - Arbitrary subgraph handling capability
   - Proper subgraph isomorphism checking for IT- and Endoporeutic Game
   - Complete formal transformation rules (DC+/DC-, INS/ERA, IT+/IT-)

2. **Data Management Components**:
   - Solidify through thorough testing and iterative improvement
   - EGI-based tomos system
   - YAML serialization
   - Constraint system

**PRIORITY ORDER**:
1. Transformation system reliability
2. Subgraph isomorphism implementation
3. Standard composition contexts
4. Data management solidification
5. Testing and iterative improvement

### Current Implementation Status

**Production Ready** (Tier 1):
- `egi_core_dau.py` - Core EGI data structure (PROTECTED)
- `unified_d3_engine.py` - Layout engine (PROTECTED)
- `formal_transformation_rules.py` - Transformation rules (PROTECTED)
- `egi_io.py` - Serialization (PROTECTED)

**Stable** (Tier 2):
- DiagramController - Command pattern architecture
- Linear format translators (EGIF, CGIF, CLIF)
- Style system
- SVG renderer

**Needs Work**:
- Subgraph isomorphism (21% coverage)
- Graph entity operations (0% coverage)
- Composition contexts (not implemented)

---

## Recommended Development Workflow

### Starting a New Task

1. **Review Context**:
   ```bash
   cat .coherence_session_state.json
   cat CURRENT_PLAN.md
   ```

2. **Check Component Status**:
   ```bash
   cat WHAT_WORKS_NOW.md
   ```

3. **Review API**:
   ```bash
   grep -i "your_function" ARISBE_CORE_API_REFERENCE.md
   ```

4. **Check for Existing Work**:
   ```bash
   python tools/context_awareness_system.py --check "your task"
   ```

### During Development

**Write Tests First**:
- Current coverage only 11%
- Focus on transformation system
- Use core tests as examples

**Follow Patterns**:
- EGI immutability: `.with_vertex()`, `.with_edge()`
- Import style: `from module import function` (not `from src.module`)
- Error handling: Always check return values

**Run Quality Checks**:
```bash
# Before committing
python tools/quality_gate_system.py
```

### Committing Changes

```bash
git add your_files
git commit -m "Description"

# Hook automatically:
# - Updates session state
# - Regenerates API docs if needed
# - Runs quality gates (90 tests)
# - Verifies core protection
```

---

## Common Tasks

### Adding a New Module

1. **Choose Tier**:
   - Tier 1 (Production): Protected core only
   - Tier 2 (Stable): Production-ready features
   - Tier 3 (Experimental): Prototype/research

2. **Update Session State**:
   Add to `.coherence_session_state.json` under appropriate tier

3. **Write Tests**:
   Create `tests/test_your_module.py`

4. **Document**:
   API docs auto-generate if in protected core

### Modifying Protected Core

**Protected Modules** (Require Authorization):
- `egi_core_dau.py`
- `unified_d3_engine.py`
- `formal_transformation_rules.py`
- `egi_io.py`

**To Modify**:
```bash
export ARISBE_CORE_OVERRIDE=true
# Make changes
# Write tests
# Verify all 90 tests pass
git commit
```

### Implementing Transformation Rules

**Reference**:
- See `formal_transformation_rules.py`
- Dau Chapter 14/15 compliance
- 90 core tests validate correctness

**Pattern**:
```python
from formal_transformation_rules import DeiterationRule, TransformationContext

rule = DeiterationRule()
context = TransformationContext(
    source_egi=egi,
    target_area="sheet",
    ...
)
result = rule.apply_transformation(context)
```

### Working with EGI

**Creation**:
```python
from egi_core_dau import create_empty_graph, create_vertex, create_edge

egi = create_empty_graph()
vertex = create_vertex(label="Human", is_generic=False)
egi = egi.with_vertex(vertex)  # Immutable pattern
```

**Serialization**:
```python
from egi_io import save_egi_json, load_egi_json

save_egi_json(egi, "filename.json")
loaded_egi = load_egi_json("filename.json")
```

**Layout**:
```python
from unified_d3_engine import UnifiedD3Engine
from style_loader import StyleLoader

engine = UnifiedD3Engine()
style = StyleLoader().load_default_style()
dto = engine.generate_layout(egi, style)
```

---

## Integration Points

### GUI Development (Deferred)

**When Ready**:
- DiagramController provides command layer
- UnifiedD3Engine handles layout
- SVG renderer for display

**Current Status**:
- GUI components in `src/gui_clean/` (0% coverage)
- Deferred per strategic focus

### Tomos System

**Current**:
- `integrated_corpus_manager.py` (20% coverage)
- EGI-based storage
- YAML serialization

**Needs**:
- More tests
- Validation of diachronic workflow
- Stress testing on 51 tomos graphs

### Transformation System

**Current**:
- `formal_transformation_rules.py` (17% coverage)
- DC+/DC-, INS/ERA, IT+/IT- implemented
- 90 core tests passing

**Needs**:
- Subgraph isomorphism (21% coverage → target 80%)
- Arbitrary subgraph handling
- More integration tests

---

## Monitoring Progress

### Daily Dashboard

```bash
python tools/daily_quality_dashboard.py
```

**Shows**:
- Core tests status (90/90 target)
- Protected modules status
- Code quality metrics
- Recent accomplishments

### Coverage Tracking

```bash
python tools/integrate_coverage_measurement.py --html
```

**Current Baseline**: 11.0%
**Near-Term Target**: 20%
**Long-Term Target**: 70%

### Plan Staleness

**Automatic**: Pre-commit hook checks plan age
**Manual**: Review `CURRENT_PLAN.md` weekly
**Recommended**: Update after major milestones

---

## Troubleshooting

### "API docs not regenerating"

**Check**:
```bash
python tools/auto_regenerate_api_docs.py --force
```

### "Session state out of date"

**Update**:
```bash
python tools/update_session_state.py
```

### "Quality gates failing"

**Diagnose**:
```bash
python tools/quality_gate_system.py
```

**Common Causes**:
- Core tests failing (check `pytest tests/`)
- Syntax errors (check `python -m py_compile src/*.py`)
- Protected module modified without override

### "Context lost after AI session"

**Recover**:
1. Read `.coherence_session_state.json`
2. Read `WHAT_WORKS_NOW.md`
3. Read `CURRENT_PLAN.md`
4. Read `FRAMEWORK_AMNESIA_RECOVERY.md` (if needed)

---

## Best Practices

### For Humans

1. **Commit Regularly**: Session state tracks progress
2. **Update Plan**: Keep `CURRENT_PLAN.md` current
3. **Write Tests**: Target 20% coverage near-term
4. **Check Dashboard**: Run daily quality check

### For AI Assistants

1. **Read Session State First**: Full context in 5 minutes
2. **Check API Docs**: Don't guess function signatures
3. **Verify Existence**: Use grep before claiming functions exist
4. **Update Session State**: Add accomplishments
5. **Follow Patterns**: Use existing code as examples

### For Both

1. **Test Before Commit**: 90/90 tests must pass
2. **Follow Conventions**: EGI immutability, import patterns
3. **Document Changes**: Update CURRENT_PLAN.md
4. **Use Tools**: Don't manually update what tools handle

---

## Known Issues

### Documentation Drift (63 Invalid References)

**Status**: Identified by validator
**Fix Plan**: Available in DOCUMENTATION_DRIFT_FIX_PLAN.md
**Priority**: Low (doesn't block development)

**Action**: Review and fix when time permits

### Low Coverage (11%)

**Status**: Baseline established
**Target**: 20% near-term, 70% long-term
**Focus**: Transformation system and core modules

**Action**: Write tests as you develop

### Orphaned Modules (23 Detected)

**Status**: Identified by archaeology detector
**Candidates**: Available in CODE_CLEANUP_CANDIDATES.md
**Priority**: Low (doesn't block development)

**Action**: Review and archive/delete when convenient

---

## Success Metrics

### Framework is Working When...

✅ AI sessions start with full context (< 5 minutes)
✅ Documentation stays synchronized (auto-updates)
✅ Quality gates catch regressions (90/90 tests)
✅ Code archaeology visible (41 candidates found)
✅ Session state persists (survives restarts)

### Development is Progressing When...

🎯 Coverage increasing (11% → 20% → 40% → 70%)
🎯 Transformation system tests growing
🎯 Subgraph isomorphism implemented
🎯 Composition contexts working
🎯 Tomos validation passing

---

## Next Immediate Steps

Based on strategic priorities:

### Week 1: Subgraph Isomorphism

**Goal**: Implement proper subgraph isomorphism checking

**Files**:
- `src/graph_isomorphism_engine.py` (currently 21% coverage)
- `tests/test_graph_isomorphism.py` (needs expansion)

**Success**: IT- rule and Endoporeutic Game foundation

### Week 2: Transformation System Tests

**Goal**: Increase transformation system coverage to 50%

**Files**:
- `src/formal_transformation_rules.py` (currently 17% coverage)
- Add integration tests for rule sequences

**Success**: Reliable transformation for arbitrary graphs

### Week 3: Composition Contexts

**Goal**: Implement standard composition contexts

**Requirements**:
- Double cut on sheet (negatively enclosed area)
- Standard practice environment

**Success**: Graph composition and practice possible

### Week 4: Data Management

**Goal**: Solidify tomos system and YAML serialization

**Files**:
- `src/integrated_corpus_manager.py` (currently 20% coverage)
- Test diachronic workflow on tomos graphs

**Success**: Reliable data persistence and tomos validation

---

## Resources

### Key Documents

- `.coherence_session_state.json` - Current context
- `CURRENT_PLAN.md` - Active work plan
- `WHAT_WORKS_NOW.md` - Component index
- `ARISBE_CORE_API_REFERENCE.md` - Core API docs
- `AGENTS.md` - AI assistant guidelines

### Tools

- `tools/daily_quality_dashboard.py` - System status
- `tools/update_session_state.py` - Session management
- `tools/integrate_coverage_measurement.py` - Coverage tracking
- `tools/validate_architecture_docs.py` - Doc validation

### Architecture Documents

- `BOTTOM_UP_D3_ARCHITECTURE.md` - Layout engine
- `DIAGRAM_CONTROLLER_LAYERED_ARCHITECTURE.md` - Command pattern
- `CORE_DAU_FORMALISM_ARCHITECTURE.md` - Formal rules

---

## Conclusion

The coherence framework is **fully operational** and ready to support Arisbe development.

**What You Have**:
- ✅ Context persistence (session state auto-updates)
- ✅ Documentation automation (API docs sync)
- ✅ Code quality monitoring (archaeology detection)
- ✅ Test validation (90/90 tests passing)
- ✅ Coverage baseline (11%, growing to 70%)

**What's Next**:
- Focus on transformation system (strategic priority #1)
- Implement subgraph isomorphism (foundation for IT- and Agon)
- Write tests to increase coverage (11% → 20%)
- Solidify data management (corpus system)

**The framework works for you now.** AI assistants recover context instantly. Documentation stays synchronized. Quality is monitored automatically.

**Time to build Arisbe.**

---

**Last Updated**: 2025-10-14  
**Framework Status**: ✅ Operational  
**Ready**: True
