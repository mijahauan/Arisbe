# EG Test Methodology Analysis: From Synthetic to Corpus-Based Testing

## Current Test Approach: Synthetic Examples

### What We're Testing Now:
Our current 53 tests use **synthetic, constructed examples**:

#### **Logical Types Tests (24 tests):**
- Basic dataclass creation and validation
- Factory function behavior
- JSON serialization round-trips
- Constraint consistency checking

#### **Containment Hierarchy Tests (29 tests):**
- Hierarchy management operations
- Validation rule enforcement
- Layout calculation mechanics
- Movement validation logic

### **Strengths of Current Approach:**
✅ **Technical Validation**: Ensures code functions correctly  
✅ **Edge Case Coverage**: Tests error conditions and boundary cases  
✅ **Regression Prevention**: Catches implementation bugs  
✅ **Fast Execution**: Synthetic tests run quickly  

### **Critical Weaknesses:**
❌ **No Domain Validation**: Tests don't verify EG logical correctness  
❌ **Artificial Examples**: May not reflect real EG complexity  
❌ **Missing Semantic Validation**: Can create invalid EG structures (as we just discovered)  
❌ **No Historical Grounding**: Not validated against Peirce's actual examples  

## Proposed Corpus-Based Test Methodology

### **The EG Corpus Approach**

#### **1. Peirce's Original Examples**
Create a curated corpus from Peirce's writings:

**Primary Sources:**
- *Collected Papers* (especially CP 4.394-417)
- *Existential Graphs* manuscripts
- Letters and notebooks with EG examples
- *The Logic of Mathematics* (CP 1.417-520)

**Example Categories:**
```
Peirce_Corpus/
├── basic_assertions/
│   ├── simple_predicates.eg-hg
│   ├── relational_predicates.eg-hg
│   └── identity_statements.eg-hg
├── negations/
│   ├── simple_negations.eg-hg
│   ├── complex_negations.eg-hg
│   └── double_negations.eg-hg
├── implications/
│   ├── simple_conditionals.eg-hg
│   ├── nested_implications.eg-hg
│   └── material_conditionals.eg-hg
├── quantification/
│   ├── existential_quantifiers.eg-hg
│   ├── universal_quantifiers.eg-hg
│   └── mixed_quantification.eg-hg
├── complex_forms/
│   ├── syllogisms.eg-hg
│   ├── modal_logic.eg-hg
│   └── mathematical_proofs.eg-hg
└── transformations/
    ├── iteration_examples.eg-hg
    ├── deiteration_examples.eg-hg
    └── insertion_deletion.eg-hg
```

#### **2. Secondary Literature Examples**
Include examples from EG scholars:

**Sources:**
- Roberts: *The Existential Graphs of Charles S. Peirce*
- Zeman: *The Graphical Logic of C.S. Peirce*
- Shin: *The Iconic Logic of Peirce's Graphs*
- Dau: *The Logic System of Concept Graphs with Negation*

#### **3. Test Structure for Each Corpus Example**

```python
class CorpusEGTest:
    """Test based on historical EG example."""
    
    def __init__(self, source: str, example_id: str):
        self.source = source           # "Peirce_CP_4.394"
        self.example_id = example_id   # "simple_implication_1"
        self.eg_hg = load_eg_hg(f"{source}/{example_id}.eg-hg")
        self.expected_clif = load_clif(f"{source}/{example_id}.clif")
        self.expected_cgif = load_cgif(f"{source}/{example_id}.cgif")
        self.description = load_description(f"{source}/{example_id}.md")
    
    def test_eg_hg_to_clif_direct(self):
        """Test direct EG-HG → CLIF conversion."""
        result_clif = convert_eg_hg_to_clif(self.eg_hg)
        assert semantically_equivalent(result_clif, self.expected_clif)
    
    def test_eg_hg_to_egrf_to_clif_roundtrip(self):
        """Test EG-HG → EGRF → CLIF vs direct conversion."""
        # Direct conversion
        direct_clif = convert_eg_hg_to_clif(self.eg_hg)
        
        # Round-trip conversion
        egrf = convert_eg_hg_to_egrf(self.eg_hg)
        roundtrip_clif = convert_egrf_to_clif(egrf)
        
        assert semantically_equivalent(direct_clif, roundtrip_clif)
    
    def test_egrf_logical_structure(self):
        """Test EGRF preserves logical structure."""
        egrf = convert_eg_hg_to_egrf(self.eg_hg)
        
        # Validate EG-specific patterns
        validator = EGPatternValidator()
        report = validator.validate_eg_patterns(egrf)
        
        assert report.is_valid, f"Invalid EG pattern: {report.errors}"
    
    def test_visual_layout_constraints(self):
        """Test visual layout respects EG conventions."""
        egrf = convert_eg_hg_to_egrf(self.eg_hg)
        
        layout_result = calculate_layout(egrf)
        
        # Check Peirce's visual conventions
        assert_proper_cut_nesting(layout_result)
        assert_ligature_continuity(layout_result)
        assert_predicate_placement(layout_result)
```

### **4. Corpus Test Categories**

#### **A. Logical Correctness Tests**
```python
def test_peirce_implication_cp_4_394():
    """Test Peirce's standard implication example."""
    # Load: "If anything is a man, then it is mortal"
    eg_hg = load_corpus_example("Peirce_CP_4.394", "man_mortal_implication")
    
    # Verify double-cut structure
    egrf = convert_eg_hg_to_egrf(eg_hg)
    assert has_double_cut_implication(egrf)
    
    # Verify logical equivalence
    clif = convert_egrf_to_clif(egrf)
    expected = "(forall (x) (if (Man x) (Mortal x)))"
    assert semantically_equivalent(clif, expected)

def test_peirce_syllogism_cp_4_415():
    """Test Peirce's syllogistic reasoning example."""
    # Barbara syllogism in EG form
    eg_hg = load_corpus_example("Peirce_CP_4.415", "barbara_syllogism")
    
    # Verify structure and inference validity
    egrf = convert_eg_hg_to_egrf(eg_hg)
    assert valid_syllogistic_form(egrf)
```

#### **B. Transformation Tests**
```python
def test_iteration_rule_examples():
    """Test Peirce's iteration transformation examples."""
    for example in load_corpus_category("transformations/iteration"):
        before_eg = example.before_state
        after_eg = example.after_state
        
        # Apply iteration transformation
        result = apply_iteration_rule(before_eg)
        assert logically_equivalent(result, after_eg)

def test_deiteration_rule_examples():
    """Test Peirce's deiteration transformation examples."""
    for example in load_corpus_category("transformations/deiteration"):
        before_eg = example.before_state
        after_eg = example.after_state
        
        # Apply deiteration transformation
        result = apply_deiteration_rule(before_eg)
        assert logically_equivalent(result, after_eg)
```

#### **C. Cross-Format Consistency Tests**
```python
def test_format_consistency_corpus():
    """Test consistency across all supported formats."""
    for example in load_entire_corpus():
        eg_hg = example.eg_hg
        
        # Convert to all formats
        egrf = convert_eg_hg_to_egrf(eg_hg)
        clif = convert_eg_hg_to_clif(eg_hg)
        cgif = convert_eg_hg_to_cgif(eg_hg)
        
        # Test round-trips
        assert round_trip_preserves_semantics(eg_hg, egrf)
        assert round_trip_preserves_semantics(eg_hg, clif)
        assert round_trip_preserves_semantics(eg_hg, cgif)
        
        # Test cross-format equivalence
        assert semantically_equivalent(
            convert_egrf_to_clif(egrf),
            convert_eg_hg_to_clif(eg_hg)
        )
```

## Implementation Strategy

### **Phase 1: Corpus Creation**
1. **Digitize Peirce's Examples**
   - Extract EGs from Collected Papers
   - Convert to EG-HG format
   - Add metadata (source, page, context)

2. **Create Reference Translations**
   - Manual CLIF translations by EG experts
   - CGIF translations where applicable
   - Validation by multiple scholars

3. **Build Corpus Infrastructure**
   - File organization system
   - Metadata schema
   - Loading utilities

### **Phase 2: Test Framework Enhancement**
1. **Corpus Test Runner**
   - Automatic test generation from corpus
   - Parameterized tests for each example
   - Detailed failure reporting

2. **Semantic Equivalence Checking**
   - Logic-based comparison utilities
   - Handling of equivalent but syntactically different forms
   - Proof verification capabilities

3. **EG Pattern Validation**
   - Rules for valid EG structures
   - Peirce convention checking
   - Visual layout validation

### **Phase 3: Continuous Validation**
1. **Regression Testing**
   - All corpus examples as regression tests
   - Performance benchmarking
   - Cross-platform validation

2. **Corpus Expansion**
   - Add examples from secondary literature
   - Include edge cases and complex forms
   - Community contribution system

## Benefits of Corpus-Based Testing

### **1. Historical Accuracy**
- Ensures implementation matches Peirce's intentions
- Validates against established EG scholarship
- Prevents drift from authentic EG practice

### **2. Comprehensive Coverage**
- Tests real-world complexity
- Covers patterns we might not think to test
- Includes edge cases from actual usage

### **3. Scholarly Validation**
- Provides confidence to EG researchers
- Enables academic use and citation
- Supports reproducible research

### **4. Quality Assurance**
- Catches semantic errors (like our implication mistake)
- Validates logical transformations
- Ensures cross-format consistency

## Current Gap Analysis

### **What We're Missing:**
❌ **No corpus of authentic EG examples**  
❌ **No semantic equivalence testing**  
❌ **No EG pattern validation rules**  
❌ **No cross-format consistency verification**  
❌ **No transformation rule testing**  

### **What We Need to Build:**
✅ **EG corpus creation tools**  
✅ **Semantic equivalence checker**  
✅ **EG pattern validator**  
✅ **Cross-format test framework**  
✅ **Transformation rule engine**  

## Recommendation

**Before proceeding to Phase 3 (Logical Generator):**

1. **Create a minimal EG corpus** with 10-15 key Peirce examples
2. **Implement basic semantic equivalence checking**
3. **Add EG pattern validation** to the hierarchy system
4. **Test current implementation** against corpus examples
5. **Fix any issues discovered** before building the generator

This corpus-based approach will ensure that EGRF v3.0 is not just technically sound, but **logically authentic** to Peirce's Existential Graphs.

