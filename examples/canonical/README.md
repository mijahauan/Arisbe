# Canonical Examples for EG-CL-Manus2

This directory contains canonical examples from the existential graphs literature, implemented and validated in the EG-CL-Manus2 system. These examples serve as both validation tests and educational resources.

## 📚 **Overview**

The canonical examples are based on authoritative sources:
- **Charles Sanders Peirce**: Original existential graph examples and transformation rules
- **John Sowa**: "Peirce's Tutorial on Existential Graphs" - comprehensive modern treatment
- **Frithjof Dau**: Mathematical formalization and formal logic foundations

## 📁 **Directory Structure**

```
examples/canonical/
├── README.md                           # This file
├── canonical_examples_phase1_summary.json  # Implementation summary
├── egrf/                              # Generated EGRF files
│   ├── simple-man.egrf               # Example 1: Basic existential
│   ├── socrates-mortal.egrf          # Example 2: Named individual
│   ├── every-man-mortal.egrf         # Example 3: Universal quantification
│   ├── thunder-lightning.egrf        # Example 4: Basic implication
│   └── african-man.egrf              # Example 5: Conjunction
├── documentation/                     # Research and specifications
│   ├── PHASE_1_CANONICAL_EXAMPLES.md # Complete example specifications
│   └── canonical_examples_research.md # Literature research notes
└── scripts/                          # Implementation scripts
    └── implement_canonical_examples.py # Phase 1 implementation
```

## 🎯 **Phase 1: Foundational Examples (Completed)**

### **Example 1: Simple Man**
- **Description**: "There is a man" - Basic existential quantification
- **Formula**: `∃x man(x)`
- **EGIF**: `[*x] (man ?x)`
- **File**: `egrf/simple-man.egrf`

### **Example 2: Socrates is Mortal**
- **Description**: Named individual with multiple predicates
- **Formula**: `Person(Socrates) ∧ Mortal(Socrates)`
- **EGIF**: `(Person Socrates) (Mortal Socrates)`
- **File**: `egrf/socrates-mortal.egrf`

### **Example 3: Every Man is Mortal**
- **Description**: Universal quantification using nested cuts
- **Formula**: `∀x (man(x) → mortal(x))`
- **EGIF**: `~[[*x] (man ?x) ~[(mortal ?x)]]`
- **File**: `egrf/every-man-mortal.egrf`

### **Example 4: Thunder and Lightning**
- **Description**: Basic implication structure
- **Formula**: `thunder → lightning`
- **EGIF**: `~[(thunder) ~[(lightning)]]`
- **File**: `egrf/thunder-lightning.egrf`

### **Example 5: African Man**
- **Description**: Conjunction via shared line of identity
- **Formula**: `∃x (man(x) ∧ African(x))`
- **EGIF**: `[*x] (man ?x) (African ?x)`
- **File**: `egrf/african-man.egrf`

## 📊 **Implementation Statistics**

- **Examples implemented**: 5/5 (100%)
- **EGRF files generated**: 5/5 (100%)
- **Total entities**: 4 (variables and constants)
- **Total predicates**: 9 (including nested contexts)
- **Total contexts**: 9 (including cuts and root contexts)

## 🧪 **Testing and Validation**

All examples have been:
- ✅ **Implemented** in EG-CL-Manus2 data structures
- ✅ **Generated** as valid EGRF representations
- ✅ **Validated** against literature specifications
- ✅ **Tested** for round-trip conversion integrity

## 🚀 **Usage**

### **Running the Implementation Script**
```bash
cd examples/canonical/scripts
python3 implement_canonical_examples.py
```

### **Loading EGRF Files**
```python
from egrf import EGRFSerializer, EGRFParser

# Load an example
serializer = EGRFSerializer()
with open('egrf/simple-man.egrf', 'r') as f:
    egrf_doc = serializer.from_json(f.read())

# Parse back to EG-CL-Manus2
parser = EGRFParser()
result = parser.parse(egrf_doc)
if result.is_successful:
    graph = result.graph
```

### **Viewing in EGRF Viewer**
The EGRF files can be loaded into the web-based EGRF viewer for visual inspection and validation.

## 📖 **Educational Value**

These examples demonstrate:
- **Basic EG concepts**: Lines of identity, predicates, contexts
- **Logical operators**: Conjunction, implication, quantification
- **Peirce's notation**: Authentic representation of original examples
- **Modern formalization**: EGIF and first-order logic equivalents

## 🔄 **Future Phases**

- **Phase 2**: Cardinality and complex examples (6-10)
- **Phase 3**: Educational and ligature examples (11-14)
- **Phase 4**: Dau's mathematical examples
- **Phase 5**: Sowa's practical examples

## 📚 **References**

1. Peirce, C.S. (1906). "Prolegomena to an Apology for Pragmaticism"
2. Sowa, J.F. (2000). "Peirce's Tutorial on Existential Graphs"
3. Dau, F. (2003). "Mathematical Logic with Diagrams"
4. Roberts, D.D. (1973). "The Existential Graphs of Charles S. Peirce"

## 🎯 **Validation Criteria**

Each example meets these criteria:
- ✅ **Historical authenticity**: Based on Peirce's original work
- ✅ **Logical integrity**: Preserves semantic meaning
- ✅ **Visual clarity**: Clear graphical representation
- ✅ **Transformation capability**: Can be modified using Peirce's rules
- ✅ **Educational value**: Suitable for teaching EG concepts
- ✅ **Implementation completeness**: Full EG-CL-Manus2 integration

