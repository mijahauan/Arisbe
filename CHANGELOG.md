# Changelog: Arisbe Existential Graphs System

## Version 2.0.1 - Variable Scoping Fix (Current)

### 🎯 **Critical Bug Fix**

#### **FIXED: Variable Scoping in EGIF Generator**
- **Issue**: Variables defined in cuts were not marked as defining (`*x`) vs bound (`x`) correctly
- **Impact**: Round-trip conversion failed for nested structures like `~[ (mortal *x) ]`
- **Solution**: Implemented proper coreference handling across cut boundaries
- **Result**: 100% round-trip conversion success rate

#### **Technical Details**
- **Root Cause**: Generator treated each context independently for variable scoping
- **Fix**: Context hierarchy traversal to check parent contexts for variable definitions
- **Validation**: All previously failing test cases now pass:
  - `~[ (mortal *x) ]` → `~[ (mortal *x) ]` ✅
  - `~[ (man *x) ~[ (mortal x) ] ]` → `~[ (man *x) ~[ (mortal x) ] ]` ✅

#### **Test Results**
```
Before Fix:
✗ Round-trip failed for '~[ (mortal *x) ]': Undefined variable x

After Fix:
✓ Parser tests passed
✓ Generator tests passed
✓ Transformation tests passed
✓ CLI tests passed
✓ Round-trip conversion: 100% success rate
```

### 🔧 **Additional Improvements**

#### **Enhanced Test Suite**
- **ADDED**: `test_comprehensive_dau_fixed.py` with complete validation
- **ADDED**: Specific tests for variable scoping edge cases
- **ADDED**: Round-trip conversion verification for all EGIF constructs
- **IMPROVED**: Error reporting and test coverage

#### **Documentation Updates**
- **UPDATED**: README with current system status
- **ADDED**: Fix documentation in CHANGELOG
- **VERIFIED**: All usage examples work correctly

---

## Version 2.0.0 - Dau-Compliant Implementation

### 🎯 **Major Architectural Overhaul**

#### **New: Dau's 6+1 Component Model**
- **ADDED**: Exact implementation of Dau's formal specification
- **ADDED**: `RelationalGraphWithCuts` class with 6+1 components (V, E, ν, ⊤, Cut, area, rel)
- **ADDED**: Proper area/context distinction for diagram generation vs semantics
- **CHANGED**: Replaced "Context" concept with Dau's formal "Cut" and "area" mapping

#### **New: Isolated Vertex Support**
- **ADDED**: Full support for Dau's "heavy dot" rule (isolated vertices)
- **ADDED**: Generic isolated vertices (`*x`) and constant isolated vertices (`"Socrates"`)
- **ADDED**: Isolated vertex addition/removal transformation rules
- **ADDED**: Parser support for bare isolated vertices in EGIF

#### **Enhanced: Transformation Rules**
- **ADDED**: All 8 canonical transformation rules implemented
- **ADDED**: Proper context polarity validation (positive/negative contexts)
- **ADDED**: Immutable transformations (return new graph instances)
- **ADDED**: Comprehensive error handling with mathematical validation

#### **Enhanced: EGIF Processing**
- **FIXED**: Nested cut generation bug using area/context distinction
- **ADDED**: Comprehensive syntax validation before parsing
- **ADDED**: Support for all EGIF constructs including isolated vertices
- **IMPROVED**: Round-trip conversion accuracy

#### **New: Comprehensive CLI**
- **ADDED**: Interactive mode with full command set
- **ADDED**: All 8 transformation rules accessible via commands
- **ADDED**: History and undo functionality
- **ADDED**: Command-line mode for scripting
- **ADDED**: Comprehensive help system

#### **New: Test Framework**
- **ADDED**: Comprehensive test suite with pytest framework
- **ADDED**: Test case collection with 16+ EGIF expressions across 4 complexity levels
- **ADDED**: Performance testing for large graphs
- **ADDED**: Round-trip conversion validation
- **ADDED**: Immutability verification tests

### 🔧 **Technical Improvements**

#### **Architecture**
- **CHANGED**: Complete rewrite with immutability from ground up
- **ADDED**: Structural sharing for memory efficiency
- **ADDED**: Frozen data structures (`@dataclass(frozen=True)`)
- **ADDED**: Type hints throughout codebase

#### **Performance**
- **ADDED**: O(1) element lookup with pre-computed maps
- **ADDED**: Efficient area/context computation
- **ADDED**: Optimized graph traversal algorithms

#### **Error Handling**
- **ADDED**: `TransformationError` for invalid operations
- **ADDED**: Comprehensive validation of Dau's constraints
- **ADDED**: Clear error messages with context information

### 📚 **Documentation**

#### **New Documentation**
- **ADDED**: `dau_formalism_analysis.md` - Analysis of Dau's formal specification
- **ADDED**: `immutable_architecture_design.md` - Architecture design decisions
- **ADDED**: Comprehensive README with usage examples
- **ADDED**: API documentation in module docstrings

#### **Examples**
- **ADDED**: CLI usage examples
- **ADDED**: Python API examples
- **ADDED**: Transformation rule examples
- **ADDED**: Complex EGIF structure examples

### 🐛 **Known Issues**

#### **Variable Scoping**
- **ISSUE**: Generator may not mark variables as defining (`*x`) vs bound (`x`) correctly in cuts
- **IMPACT**: Some round-trip conversions fail on nested structures
- **STATUS**: Under investigation

#### **Isolated Vertex Detection**
- **ISSUE**: Complex nested structures may not identify all isolated vertices
- **IMPACT**: Some test cases fail isolation detection
- **STATUS**: Refinement needed

---

## Version 1.0.0 - Initial Mutable Implementation (Archived)

### 🎯 **Initial Features**

#### **Basic EGI Implementation**
- **ADDED**: Basic EGI data model with mutable operations
- **ADDED**: EGIF parser for basic syntax
- **ADDED**: EGIF generator with basic functionality
- **ADDED**: Limited transformation rules (erasure, double cut removal)

#### **CLI Interface**
- **ADDED**: Basic command-line interface
- **ADDED**: Markup parsing with `^` notation
- **ADDED**: Interactive mode

#### **Testing**
- **ADDED**: Basic test coverage
- **ADDED**: Round-trip conversion tests

### 🔧 **Technical Details**

#### **Architecture**
- **USED**: Mutable EGI objects with in-place modifications
- **USED**: "Context" concept instead of Dau's area/context distinction
- **USED**: Basic Python data structures

#### **Limitations**
- **MISSING**: Isolated vertex support
- **MISSING**: Proper area/context distinction
- **MISSING**: Complete transformation rule set
- **MISSING**: Mathematical rigor of Dau's specification
- **BUG**: Nested cut generation created element duplication

---

## Migration Guide: v1.0.0 → v2.0.0

### 🔄 **Breaking Changes**

#### **API Changes**
```python
# v1.0.0 (Mutable)
transformer = EGITransformer(egi)
transformer._apply_erasure(element_id)  # Mutates original
result = transformer.egi

# v2.0.0 (Immutable)
new_egi = apply_erasure(egi, element_id)  # Returns new instance
```

#### **Data Model Changes**
```python
# v1.0.0
class EGI:
    contexts: FrozenSet[Context]  # Used "Context" concept

# v2.0.0
class RelationalGraphWithCuts:
    Cut: FrozenSet[Cut]           # Dau's formal "Cut"
    area: frozendict              # Dau's area mapping
```

#### **Import Changes**
```python
# v1.0.0
from egi_core import EGI
from egif_parser import parse_egif

# v2.0.0
from egi_core_dau import RelationalGraphWithCuts
from egif_parser_dau import parse_egif
```

### 🎯 **New Capabilities**

#### **Isolated Vertices**
```python
# Now supported
graph = parse_egif("*x")  # Generic isolated vertex
graph = parse_egif('"Socrates"')  # Constant isolated vertex
```

#### **All Transformation Rules**
```python
# All 8 rules now available
apply_erasure(graph, element_id)
apply_insertion(graph, "vertex", context_id)
apply_isolated_vertex_addition(graph, context_id)
# ... and 5 more
```

#### **Proper Area/Context**
```python
# Correct distinction for diagram generation
area = graph.get_area(cut_id)      # Direct contents
context = graph.get_full_context(cut_id)  # Recursive contents
```

### 📋 **Upgrade Recommendations**

1. **Update imports** to use `*_dau` modules
2. **Replace mutable operations** with immutable transformations
3. **Use new CLI commands** for all 8 transformation rules
4. **Leverage isolated vertex support** for complete EG modeling
5. **Update tests** to use new comprehensive test framework

---

**For detailed technical information, see the documentation in the `docs/` directory.**

