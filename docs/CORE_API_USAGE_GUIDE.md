# 🔒 ARISBE CORE API USAGE GUIDE

**Date:** 2025-01-19
**Last verified:** 2026-07-21 (protected-module set, constructor signatures, `HierarchicalIndex`
accessors checked directly against `tools/core_protection_system.py` and `src/egi_core_dau.py` /
`src/hierarchical_index.py`)
**Status:** ✅ **COMPREHENSIVE REFERENCE**
**Purpose:** Eliminate guesswork in core API usage

---

## 🎯 **PURPOSE**

This guide provides **definitive, tested API signatures** for the 14 protected core modules. No more guessing at function names, parameters, or return types!

---

## 📚 **QUICK REFERENCE INDEX**

The 14 modules below are the live `protected_modules` set in
`tools/core_protection_system.py` (verified 2026-07-21) — the genuine calculus core: the data
model + IO, diachronic state, the Dau rules + validators, the ligature machinery, and the three
correspondence enforcers. **The EGIF/CGIF/CLIF parsers/generators are *not* protected-core** —
they were removed from the set on 2026-06-27 as application-level I/O guarded by corpus
round-trip tests instead (see CLAUDE.md's Core Protection System section).

### **🔧 CORE DATA MODEL + IO**
- **`egi_core_dau`** - Create graphs, vertices, edges, cuts (immutable `RelationalGraphWithCuts`)
- **`egi_io`** - Save/load EGI files (JSON/YAML)
- **`hierarchical_index`** - Cut nesting and polarity

### **🕰️ DIACHRONIC STATE**
- **`universe_of_discourse`** - UoD entity (synchronic EGI + diachronic DAG history)
- **`egi_transformation_history`** - DAG-based branching transformation history

### **🔄 TRANSFORMATIONS + VALIDATION**
- **`formal_transformation_rules`** - Dau Chapter 14/15 rules (ERA, INS, IT+, IT−, DC+, DC−)
- **`rule_interaction`** - Headless stepwise protocol for all rules
- **`subgraph_closure_validator`** - Closure validation (Beta-aware)
- **`graph_isomorphism_engine`** - VF2 isomorphism matching

### **🔗 CORRESPONDENCE ENFORCERS** (added 2026-06-27)
- **`correspondence_attestation`** - Runtime §3.3 check (EGI ↔ LayoutDTO)
- **`presentation_ops`** - Regime-3 algebra (move/reshape/reroute, area-topology helpers)
- **`natural_layout`** - Coordinate-free projection-independent layout

### **🔗 LIGATURE PROCESSING**
- **`ligature_manipulation_rules`** - Rule-based ligature processing
- **`single_object_ligature_detector`** - Detection algorithms

### **📝 PARSING & GENERATION** (application-level I/O — NOT protected-core)
- **`cgif_parser_dau`** / **`cgif_generator_dau`** - CGIF format
- **`egif_parser_dau`** / **`egif_generator_dau`** - EGIF format
- **`clif_parser_dau`** / **`clif_generator_dau`** - CLIF format

### **🔍 OTHER CORE-ADJACENT UTILITIES** (not protected-core)
- **`syntactic_equivalence_checker`** - Dau Chapter 20 equivalence checking

---

## 🚀 **COMMON USAGE PATTERNS**

### **Pattern 1: Creating a Basic EGI**
```python
from egi_core_dau import create_empty_graph, create_vertex, create_edge

# Create empty graph
egi = create_empty_graph()

# Create vertices
# Signature: create_vertex(label: str = None, is_generic: bool = True) -> Vertex
human_vertex = create_vertex(label="Human", is_generic=False)
socrates_vertex = create_vertex(label="Socrates", is_generic=False)

# Create edge — the constructor itself is zero-arg; the relation name + argument
# order (nu) are supplied when the edge is attached via with_edge, not at creation.
# Signature: create_edge() -> Edge
human_edge = create_edge()

# Add to graph
# Signature: with_edge(self, edge: Edge, vertex_sequence: Tuple[str, ...],
#                       relation_name: str, context_id: str = None) -> RelationalGraphWithCuts
egi = (egi
       .with_vertex(human_vertex)
       .with_vertex(socrates_vertex)
       .with_edge(human_edge, (human_vertex.id, socrates_vertex.id), relation_name="Human"))
```

### **Pattern 2: Saving and Loading EGI**
```python
from egi_io import save_egi_json, load_egi_json, save_egi_yaml, load_egi_yaml

# Save EGI
# Signature: save_egi_json(egi: RelationalGraphWithCuts, filepath: str) -> bool
success = save_egi_json(egi, "my_graph.json")

# Load EGI
# Signature: load_egi_json(filepath: str) -> RelationalGraphWithCuts
loaded_egi = load_egi_json("my_graph.json")

# YAML format also available
save_egi_yaml(egi, "my_graph.yaml")
loaded_egi = load_egi_yaml("my_graph.yaml")
```

### **Pattern 3: Parsing Linear Formats**
```python
from cgif_parser_dau import parse_cgif
from egif_parser_dau import parse_egif

# Parse CGIF
# Signature: parse_cgif(cgif_string: str) -> RelationalGraphWithCuts
cgif_text = "[Human: Socrates]"
egi_from_cgif = parse_cgif(cgif_text)

# Parse EGIF  
# Signature: parse_egif(egif_string: str) -> RelationalGraphWithCuts
egif_text = "Human(Socrates)"
egi_from_egif = parse_egif(egif_text)
```

### **Pattern 4: Generating Linear Formats**
```python
from cgif_generator_dau import generate_cgif
from egif_generator_dau import generate_egif

# Generate CGIF
# Signature: generate_cgif(egi: RelationalGraphWithCuts) -> str
cgif_output = generate_cgif(egi)

# Generate EGIF
# Signature: generate_egif(egi: RelationalGraphWithCuts) -> str
egif_output = generate_egif(egi)
```

### **Pattern 5: Checking Syntactic Equivalence**
```python
from syntactic_equivalence_checker import SyntacticEquivalenceChecker

# Create checker
checker = SyntacticEquivalenceChecker()

# Check equivalence
# Signature: check_equivalence(egi1: RelationalGraphWithCuts, egi2: RelationalGraphWithCuts) -> bool
are_equivalent = checker.check_equivalence(egi1, egi2)
```

### **Pattern 6: Working with Cuts and Nesting**
```python
from egi_core_dau import create_cut
from hierarchical_index import HierarchicalIndex

# Create cut — the constructor is zero-arg; it gets its own generated id
# Signature: create_cut() -> Cut
cut = create_cut()

# Add cut to graph
# Signature: with_cut(self, cut: Cut, context_id: str = None) -> RelationalGraphWithCuts
egi = egi.with_cut(cut)  # context_id=None attaches at the sheet

# Work with hierarchical index
index = HierarchicalIndex()
index.add_area(cut.id, parent_area=None)  # Top-level cut

# Get nesting info — there is no get_nesting_info(); use the direct O(1) accessors
# Signatures: get_nesting_level / get_polarity / get_parent / get_children / get_ancestors
nesting_level = index.get_nesting_level(cut.id)
polarity = index.get_polarity(cut.id)  # "positive" or "negative"
```

---

## ⚠️ **CRITICAL API RULES**

### **1. ALWAYS Use Exact Signatures**
```python
# ✅ CORRECT - matches documented signature
vertex = create_vertex(label="Human", is_generic=False)

# ❌ WRONG - parameter names matter
vertex = create_vertex("Human", False)  # Positional args may break
```

### **2. Check Return Types**
```python
# ✅ CORRECT - handle return types properly
egi = load_egi_json("file.json")
if egi is not None:
    # Process EGI
    pass

# ❌ WRONG - assuming success without checking
egi = load_egi_json("file.json")
vertices = egi.V  # May crash if load failed
```

### **3. Use Immutable Patterns**
```python
# ✅ CORRECT - EGI operations return new instances
egi = create_empty_graph()
egi = egi.with_vertex(vertex1)
egi = egi.with_vertex(vertex2)

# ❌ WRONG - EGI is immutable, this won't work
egi = create_empty_graph()
egi.add_vertex(vertex1)  # Method doesn't exist
```

---

## 🔍 **API DISCOVERY WORKFLOW**

### **Step 1: Find the Right Module**
1. Check **ARISBE_CORE_API_REFERENCE.md** module index
2. Look for functionality keywords (parse, generate, create, check)
3. Identify the module containing your needed functionality

### **Step 2: Find the Right Function/Class**
1. Look in the detailed documentation for your module
2. Check class methods vs standalone functions
3. Verify the functionality matches your need

### **Step 3: Use Exact Signature**
1. Copy the exact function signature from documentation
2. Use named parameters for clarity
3. Check return type expectations

### **Step 4: Test and Validate**
1. Write a small test to verify behavior
2. Check that core tests still pass if modifying anything
3. Refer back to documentation if behavior is unexpected

---

## 📋 **COMMON ERRORS & SOLUTIONS**

### **Error: "Module not found"**
```python
# ❌ WRONG
from src.egi_core_dau import create_vertex

# ✅ CORRECT - modules are in src/ directory
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "src"))
from egi_core_dau import create_vertex
```

### **Error: "Function takes X arguments but Y given"**
```python
# ❌ WRONG - missing required parameters
vertex = create_vertex()

# ✅ CORRECT - provide required parameters or use defaults
vertex = create_vertex(label="Human")  # Uses default is_generic=True
```

### **Error: "AttributeError: object has no attribute"**
```python
# ❌ WRONG - EGI is immutable
egi.add_vertex(vertex)

# ✅ CORRECT - use immutable pattern
egi = egi.with_vertex(vertex)
```

---

## 🧪 **TESTING YOUR CODE**

### **Always Test Against Core**
```python
# Test your code doesn't break core functionality
def test_my_functionality():
    # Your test code here
    pass

# Run core tests to ensure no regression
# python -m pytest tests/test_egi_core_comprehensive.py -v
```

### **Use Core Patterns**
```python
# Follow patterns from working core tests
# See tests/test_egi_core_comprehensive.py for examples
```

---

## 🔒 **CORE PROTECTION AWARENESS**

### **What's Protected**
- **14 core modules** with 67 classes and 49 functions (per `tools/extract_core_api.py`,
  re-run 2026-07-21 — see `ARISBE_CORE_API_REFERENCE.md`)
- **The mathematical core test suite** (~118 tests covering egi_core_dau, formal_transformation_rules, rule_interaction, subgraph_closure_validator, graph_isomorphism_engine, and Beta/logical proof exercises) that must always pass
- **API signatures** that cannot change without authorization

### **What Requires Authorization**
- Modifying any of the 14 protected modules
- Changing function signatures
- Adding/removing public methods or classes

### **How to Get Authorization**
```bash
# For authorized core changes only:
export ARISBE_CORE_OVERRIDE=true
git commit -m "CORE_AUTHORIZED: Mathematical correction for [specific issue]"
```

---

## 🎯 **BEST PRACTICES**

### **1. Always Refer to Documentation**
- Use **ARISBE_CORE_API_REFERENCE.md** as single source of truth
- Don't guess at function signatures
- Check parameter types and defaults

### **2. Use Descriptive Variable Names**
```python
# ✅ GOOD
human_vertex = create_vertex(label="Human", is_generic=False)
socrates_vertex = create_vertex(label="Socrates", is_generic=False)

# ❌ BAD
v1 = create_vertex("Human", False)
v2 = create_vertex("Socrates", False)
```

### **3. Handle Errors Gracefully**
```python
# ✅ GOOD
try:
    egi = load_egi_json(filepath)
    if egi is None:
        print(f"Failed to load EGI from {filepath}")
        return None
except Exception as e:
    print(f"Error loading EGI: {e}")
    return None
```

### **4. Write Self-Documenting Code**
```python
# ✅ GOOD - clear intent
def create_socrates_human_egi():
    """Create EGI representing 'Socrates is Human'."""
    egi = create_empty_graph()
    
    # Create concept vertices
    human_vertex = create_vertex(label="Human", is_generic=False)
    socrates_vertex = create_vertex(label="Socrates", is_generic=False)
    
    # Create relation edge — zero-arg constructor; relation name + argument
    # order are supplied to with_edge, not create_edge (see Pattern 1 above)
    human_relation = create_edge()
    
    # Assemble graph
    return (egi
            .with_vertex(human_vertex)
            .with_vertex(socrates_vertex)
            .with_edge(human_relation, (human_vertex.id, socrates_vertex.id), relation_name="Human"))
```

---

**This guide eliminates guesswork and provides definitive patterns for using Arisbe's validated core API. Always refer to the comprehensive API reference for detailed signatures and behavior.**
