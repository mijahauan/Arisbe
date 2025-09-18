# Arisbe Foundation Repair Plan

## Critical Issue Analysis

Based on examination of the Common Logic specifications and Dau's formalization, our foundation has a fundamental misunderstanding of variable/constant representation that cascades through all translation components.

### Core Problem: Variable/Constant Representation Confusion

**Current Broken Logic:**
- CLIF parser creates vertices with `label="x"` AND `is_generic=True` 
- This violates the core constraint: "Constant vertex cannot be generic"
- Root cause: Confusion between syntactic representation and semantic meaning

**Correct Logic (per Common Logic spec):**
- In CLIF: `(Human x)` - `x` is a **name** that denotes a variable
- In EGI: Generic vertices have `label=None, is_generic=True`
- The variable name `x` should be tracked separately in variable mappings

## Phase 1: Core Data Model Repair (CRITICAL)

### 1.1 Fix Vertex Creation Logic
**Files:** `src/clif_parser_dau.py`, `src/cgif_parser_dau.py`, `src/egif_parser_dau.py`

**Current (BROKEN):**
```python
# CLIF parser line 360
vertex = Vertex(id=vertex_id, label=arg_node.value, is_generic=True)
```

**Should be:**
```python
# Generic vertices have no label
vertex = Vertex(id=vertex_id, label=None, is_generic=True)
# Track variable name separately in parser state
self.variable_names[vertex_id] = arg_node.value
```

### 1.2 Establish Clear Variable/Constant Protocol

**Variable Representation:**
- **EGI Core:** `Vertex(id="v_x", label=None, is_generic=True)`
- **EGIF:** `[*x]` (defining), `?x` (bound reference)
- **CGIF:** `[*x]` (defining), `?x` (bound reference)  
- **CLIF:** `x` (bare name in atomic formulas)
- **FOPL:** `x` (bare name in atomic formulas)

**Constant Representation:**
- **EGI Core:** `Vertex(id="v_John", label="John", is_generic=False)`
- **EGIF:** `[: John]` or `John` in relations
- **CGIF:** `[: John]` or `John` in relations
- **CLIF:** `"John"` (quoted) or `John` (unquoted simple identifier)
- **FOPL:** `John` (constant symbol)

### 1.3 Variable Name Tracking System

Each parser needs to maintain:
```python
class ParserState:
    variable_names: Dict[ElementID, str]  # vertex_id -> variable_name
    constant_names: Dict[ElementID, str]  # vertex_id -> constant_name
    next_var_counter: int
```

## Phase 2: Translation Fidelity Restoration

### 2.1 Fix All Parser Variable Handling
- **CLIF Parser:** Variables are bare names, create generic vertices
- **CGIF Parser:** Variables are `?x` or `*x`, create generic vertices  
- **EGIF Parser:** Variables are `?x` or `*x`, create generic vertices

### 2.2 Fix All Generator Variable Handling
- **CLIF Generator:** Output bare names for variables
- **CGIF Generator:** Output `?x`/`*x` based on context
- **EGIF Generator:** Output `?x`/`*x` based on context

### 2.3 Consistent Variable Mapping
All parsers/generators must use consistent variable name assignment:
```python
def get_variable_name(self, vertex_id: ElementID) -> str:
    """Get consistent variable name for vertex across all formats"""
    if vertex_id in self.variable_names:
        return self.variable_names[vertex_id]
    # Generate new name following x, y, z, u, v, w, x1, x2, ... pattern
    return self._generate_next_variable_name()
```

## Phase 3: Foundation Component Verification

### 3.1 Core EGI Model (`src/egi_core_dau.py`)
- ✅ Data model constraints are correct
- ❌ Need better validation in constructors
- ❌ Need comprehensive test coverage

### 3.2 Graph Isomorphism Engine (`src/graph_isomorphism_engine.py`)
- ✅ Engine logic is sound (tests passing)
- ❌ Integration with translation fidelity needs work

### 3.3 Formal Transformation Rules (`src/formal_transformation_rules.py`)
- ✅ Recently updated, looks comprehensive
- ❌ Needs integration testing with fixed parsers

### 3.4 Persistence Model (`src/history_persistence.py`)
- ⚠️ Basic implementation exists
- ❌ Needs synchronic/diachronic integration testing

### 3.5 Serialization (`src/gui/organon/serialization_panel.py`)
- ⚠️ Implementation exists
- ❌ Needs comprehensive JSON/YAML testing

## Phase 4: Missing Foundation Components

### 4.1 Ligature Algorithms (Chapters 16-17)
**Status:** ❌ MISSING - Need to locate/implement
**Priority:** HIGH - Required for Dau compliance

### 4.2 Syntactic Equivalence (Chapter 20)
**Status:** ⚠️ IN PROGRESS
**File:** `src/chapter20_syntactic_equivalence_fixes.py`
**Priority:** HIGH - Required before GUI

### 4.3 Chapter 15 Formal Calculus Compliance
**Status:** ⚠️ PARTIAL
**File:** `src/chapter_15_compliance_test_suite.py`
**Priority:** MEDIUM - Verification needed

## Implementation Priority

### IMMEDIATE (Block all other work)
1. **Fix vertex creation constraint violations** - All parsers
2. **Establish variable/constant protocol** - Clear specification
3. **Fix CLIF round-trip failures** - RT002, RT004 tests

### HIGH PRIORITY (Before GUI development)
4. **Complete syntactic equivalence** - Chapter 20
5. **Locate/implement ligature algorithms** - Chapters 16-17
6. **Achieve >95% test pass rate** - Foundation stability

### MEDIUM PRIORITY (Parallel with GUI)
7. **Enhance serialization testing** - JSON/YAML
8. **Complete persistence integration** - Synchronic/diachronic
9. **Chapter 15 verification** - Formal calculus compliance

## Success Criteria

**Foundation Ready for GUI Development:**
- [ ] All core tests passing (>95% pass rate)
- [ ] Translation fidelity verified (RT tests passing)
- [ ] Variable/constant handling consistent across all formats
- [ ] Syntactic equivalence complete (Chapter 20)
- [ ] Ligature algorithms implemented (Chapters 16-17)
- [ ] Formal calculus compliance verified (Chapter 15)

**Estimated Timeline:**
- Phase 1 (Critical): 2-3 days
- Phase 2 (Translation): 3-4 days  
- Phase 3 (Verification): 2-3 days
- Phase 4 (Missing components): 5-7 days
- **Total: 12-17 days for solid foundation**

This foundation work is essential before GUI development to avoid building on unstable ground.
