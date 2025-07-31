# Arisbe: Dau-Compliant Existential Graphs System

A mathematically rigorous implementation of Peirce's Existential Graphs based on Frithjof Dau's formal specification.

## 🎯 **Key Features**

### **Mathematical Rigor**
- ✅ **Dau's 6+1 Component Model**: Exact implementation of formal specification
- ✅ **Area/Context Distinction**: Proper handling for diagram generation vs semantic evaluation
- ✅ **Isolated Vertices**: Full support for Dau's "heavy dot" rule
- ✅ **All 8 Canonical Rules**: Complete transformation rule implementation
- ✅ **Immutable Architecture**: Transformations return new instances

### **Core Components**
- **`egi_core_dau.py`**: Dau's 6+1 component model (V, E, ν, ⊤, Cut, area, rel)
- **`egif_parser_dau.py`**: EGIF parser with syntax validation and isolated vertex support
- **`egif_generator_dau.py`**: EGIF generator using proper area/context distinction
- **`egi_transformations_dau.py`**: All 8 canonical transformation rules
- **`egi_cli_dau.py`**: Comprehensive command-line interface

## 🚀 **Quick Start**

### **Installation**
```bash
# Install dependencies
pip install frozendict

# Extract package to your project directory
unzip arisbe_dau_compliant.zip
```

### **Basic Usage**

#### **Command Line**
```bash
# Load and display graph
python src/egi_cli_dau.py --egif "(man *x)"

# Apply transformation
python src/egi_cli_dau.py --egif "*x" --transform addvertex
```

#### **Interactive Mode**
```bash
python src/egi_cli_dau.py

EG> load (man *x)
EG> addvertex
EG> show
EG> help
```

#### **Python API**
```python
from src.egif_parser_dau import parse_egif
from src.egif_generator_dau import generate_egif
from src.egi_transformations_dau import apply_erasure

# Parse EGIF
graph = parse_egif("(man *x) (human x)")

# Apply transformation
new_graph = apply_erasure(graph, edge_id)

# Generate EGIF
result = generate_egif(new_graph)
```

## 📋 **Dau's 6+1 Component Model**

This implementation follows Dau's formal definition exactly:

### **The 6 Core Components**
1. **V**: Finite set of vertices (generic and constant)
2. **E**: Finite set of edges (relations)
3. **ν**: Mapping from edges to vertex sequences
4. **⊤**: Sheet of assertion (single element)
5. **Cut**: Finite set of cuts (negation contexts)
6. **area**: Mapping defining direct containment

### **The 7th Component**
7. **rel**: Mapping from edges to relation names

### **Critical Distinctions**
- **Area**: Direct contents of a context (for diagram generation)
- **Context**: Recursive contents of a context (for semantic evaluation)
- **Positive/Negative**: Context polarity for transformation validation

## 🔧 **Transformation Rules**

All 8 canonical transformation rules are implemented:

### **1. Erasure** - `erase <element>`
Remove element from positive context only.

### **2. Insertion** - `insert <type> <context>`
Add element to negative context only.

### **3. Iteration** - `iterate <subgraph> <source> <target>`
Copy subgraph to same or deeper context.

### **4. De-iteration** - `deiterate <element>`
Remove iterated element.

### **5. Double Cut Addition** - `addcut <elements>`
Add double cut around elements.

### **6. Double Cut Removal** - `removecut <cut>`
Remove empty double cut.

### **7. Isolated Vertex Addition** - `addvertex [label]`
Add isolated vertex (heavy dot) to any context.

### **8. Isolated Vertex Removal** - `removevertex <vertex>`
Remove isolated vertex from any context.

## 📚 **EGIF Syntax Support**

### **Relations**
```
(man *x)              # Generic variable
(loves "Socrates" *x) # Constants and variables
```

### **Isolated Vertices**
```
*x                    # Generic isolated vertex
"Socrates"            # Constant isolated vertex
```

### **Cuts (Negation)**
```
~[ (mortal *x) ]      # Simple cut
~[ ~[ (P *x) ] ]      # Nested cuts
```

### **Coreference**
```
(man *x) (human x)    # Variable binding
[*x] (man x)          # Scroll notation
```

### **Complex Examples**
```
~[ (Human *x) ~[ (Mortal x) ] ]
(human "Socrates") ~[ (mortal "Socrates") ] *x
~[ (P *x) (Q x) ~[ (R x) ] ]
```

## 🧪 **Testing**

### **Run Comprehensive Tests**
```bash
python tests/test_comprehensive_dau.py
```

### **Test Categories**
- **Core Implementation**: 6+1 component model validation
- **Parser**: EGIF syntax parsing with all features
- **Generator**: Round-trip conversion testing
- **Transformations**: All 8 canonical rules
- **CLI Integration**: Command-line interface
- **Performance**: Large graph handling

## 📖 **Documentation**

### **Architecture Documents**
- **`docs/dau_formalism_analysis.md`**: Analysis of Dau's formal specification
- **`docs/egi_data_model_specification.md`**: Data model design decisions
- **`docs/immutable_architecture_design.md`**: Immutability implementation

### **API Reference**
Each module contains comprehensive docstrings with usage examples.

## 🔍 **Known Issues**

### **Variable Scoping in Generator**
- **Issue**: Variables defined in cuts may not generate with proper `*` marking
- **Impact**: Some round-trip conversions fail on complex nested structures
- **Workaround**: Manual verification of generated EGIF
- **Status**: Under investigation

### **Isolated Vertex Detection**
- **Issue**: Complex nested structures may not correctly identify all isolated vertices
- **Impact**: Some test cases fail isolation detection
- **Workaround**: Use simpler structures for isolated vertex operations
- **Status**: Refinement needed

## 🏗️ **Architecture Highlights**

### **Immutable Design**
```python
# All transformations return new instances
new_graph = apply_erasure(original_graph, element_id)
assert original_graph is not new_graph  # Original unchanged
```

### **Area/Context Distinction**
```python
# Area: direct contents (for diagrams)
area = graph.get_area(cut_id)

# Context: recursive contents (for semantics)
context = graph.get_full_context(cut_id)
```

### **Context Polarity**
```python
# Validate transformation rules
if graph.is_positive_context(context_id):
    # Can erase
    new_graph = apply_erasure(graph, element_id)
else:
    # Can insert
    new_graph = apply_insertion(graph, "vertex", context_id)
```

## 🎓 **Educational Use**

This implementation is designed for:
- **Research**: Formal study of Existential Graphs
- **Education**: Teaching Peirce's graphical logic
- **Development**: Building EG-based applications
- **Validation**: Testing logical reasoning systems

## 📄 **License**

This implementation follows academic research principles and is intended for educational and research use.

## 🤝 **Contributing**

When contributing:
1. Follow Dau's formal specification exactly
2. Maintain mathematical rigor in all implementations
3. Ensure comprehensive test coverage
4. Document architectural decisions clearly

## 📞 **Support**

For questions about:
- **Dau's formalism**: Refer to `docs/dau_formalism_analysis.md`
- **Implementation details**: Check module docstrings
- **Usage examples**: See test files and CLI help

---

**Built with mathematical rigor following Frithjof Dau's formal specification of Existential Graphs.**

