# EG Corpus Implementation Guide

## Overview

This guide demonstrates how to implement and use the authoritative EG corpus for testing EGRF v3.0 and future EPG development.

## Sample Implementation

### **Example Entry: Peirce's Man-Mortal Implication (CP 4.394)**

This canonical example demonstrates the complete corpus methodology:

#### **1. Complete Metadata Documentation**
```json
{
  "id": "peirce_cp_4_394_man_mortal",
  "metadata": {
    "title": "Universal Conditional: Man-Mortal Implication",
    "source": {
      "type": "primary",
      "author": "Charles Sanders Peirce",
      "work": "Collected Papers",
      "volume": 4,
      "section": "4.394",
      "page": "267",
      "year": 1906,
      "citation": "Peirce, C.S. (1932). Collected Papers, Vol. 4, §4.394. Harvard University Press."
    },
    "test_rationale": "Canonical example of double-cut implication structure; tests proper nesting, quantifier scoping, and ligature continuity across cuts.",
    "epg_potential": "excellent_starting_move"
  }
}
```

#### **2. Logical Content with Multiple Formats**
- **English**: "If anything is a man, then it is mortal."
- **CLIF**: `(forall (x) (if (Man x) (Mortal x)))`
- **CGIF**: `[If: [Man: *x] [Then: [Mortal: *x]]]`
- **Logical Form**: `∀x(Man(x) → Mortal(x))`

#### **3. EG Structure Analysis**
- **Cuts**: 2 (double-cut implication)
- **Nesting Depth**: 2 levels
- **Predicates**: 2 (Man, Mortal)
- **Entities**: 2 (shared variable x)
- **Ligatures**: 1 (connecting x across cuts)

#### **4. Complete EG-HG Representation**
```
Sheet of Assertion
└── Outer Cut (implication body)
    ├── Man(x) [antecedent]
    ├── x entity
    └── Inner Cut (consequent negation)
        ├── Mortal(x) [consequent]
        └── x entity
```

#### **5. Automated Test Cases**
```python
def test_peirce_cp_4_394_man_mortal():
    """Test Peirce's canonical implication example."""
    corpus_entry = load_corpus_example("peirce_cp_4_394_man_mortal")
    
    # Test EG-HG structure
    eg_hg = corpus_entry.load_eg_hg()
    assert_cut_nesting_depth(eg_hg, 2)
    assert_ligature_continuity(eg_hg, "x_identity")
    
    # Test EGRF conversion
    egrf = convert_eg_hg_to_egrf(eg_hg)
    assert_proper_double_cut_implication(egrf)
    
    # Test CLIF round-trip
    clif_direct = convert_eg_hg_to_clif(eg_hg)
    clif_roundtrip = convert_egrf_to_clif(egrf)
    assert_semantically_equivalent(clif_direct, clif_roundtrip)
    
    # Test against expected CLIF
    expected_clif = "(forall (x) (if (Man x) (Mortal x)))"
    assert_semantically_equivalent(clif_direct, expected_clif)
```

## Corpus Integration with EGRF Testing

### **1. Corpus-Based Test Framework**

```python
class CorpusTestFramework:
    """Framework for testing EGRF against authoritative corpus."""
    
    def __init__(self, corpus_path: str):
        self.corpus = load_corpus(corpus_path)
        self.test_results = {}
    
    def run_all_tests(self):
        """Run all corpus examples as tests."""
        for example_id, example in self.corpus.items():
            self.test_results[example_id] = self.test_example(example)
    
    def test_example(self, example: CorpusExample):
        """Test a single corpus example."""
        results = {
            'structure_validation': self.test_structure(example),
            'conversion_accuracy': self.test_conversions(example),
            'round_trip_integrity': self.test_round_trips(example),
            'semantic_equivalence': self.test_semantics(example)
        }
        return results
    
    def test_structure(self, example: CorpusExample):
        """Test EG structure follows Peirce's conventions."""
        eg_hg = example.load_eg_hg()
        egrf = convert_eg_hg_to_egrf(eg_hg)
        
        # Run structure validation tests
        validator = EGStructureValidator()
        return validator.validate(egrf, example.expected_structure)
    
    def test_conversions(self, example: CorpusExample):
        """Test format conversions are accurate."""
        eg_hg = example.load_eg_hg()
        
        # Test all conversion paths
        clif_result = convert_eg_hg_to_clif(eg_hg)
        cgif_result = convert_eg_hg_to_cgif(eg_hg)
        egrf_result = convert_eg_hg_to_egrf(eg_hg)
        
        return {
            'clif_match': semantically_equivalent(clif_result, example.expected_clif),
            'cgif_match': semantically_equivalent(cgif_result, example.expected_cgif),
            'egrf_valid': validate_egrf_structure(egrf_result)
        }
```

### **2. Semantic Validation**

```python
class SemanticValidator:
    """Validates semantic equivalence across formats."""
    
    def validate_logical_equivalence(self, expr1: str, expr2: str) -> bool:
        """Check if two logical expressions are equivalent."""
        # Use theorem prover or model checker
        return self.theorem_prover.equivalent(expr1, expr2)
    
    def validate_eg_pattern(self, egrf: EGRF, pattern_type: str) -> bool:
        """Validate EG follows proper pattern conventions."""
        pattern_validator = self.get_pattern_validator(pattern_type)
        return pattern_validator.validate(egrf)
    
    def get_pattern_validator(self, pattern_type: str):
        """Get validator for specific EG pattern."""
        validators = {
            'universal_conditional': DoubleImplicationValidator(),
            'simple_negation': SingleCutValidator(),
            'conjunction': JuxtapositionValidator(),
            'nested_quantification': NestedQuantifierValidator()
        }
        return validators.get(pattern_type, GenericValidator())
```

### **3. EPG Integration**

```python
class EPGCorpusIntegration:
    """Integration between corpus and EPG development."""
    
    def identify_transformation_opportunities(self, example: CorpusExample):
        """Identify possible EPG transformations for an example."""
        eg_hg = example.load_eg_hg()
        
        opportunities = []
        
        # Check for iteration opportunities
        if self.can_iterate(eg_hg):
            opportunities.append('iteration')
        
        # Check for deiteration opportunities
        if self.can_deiterate(eg_hg):
            opportunities.append('deiteration')
        
        # Check for double-cut elimination
        if self.has_double_cuts(eg_hg):
            opportunities.append('double_cut_elimination')
        
        return opportunities
    
    def generate_epg_starting_position(self, example: CorpusExample):
        """Generate EPG starting position from corpus example."""
        return {
            'initial_graph': example.load_eg_hg(),
            'proposer_goal': example.metadata.get('proposer_goal'),
            'skeptic_challenges': self.identify_skeptic_challenges(example),
            'transformation_hints': self.get_transformation_hints(example)
        }
```

## Usage Examples

### **Testing EGRF Implementation**

```python
# Load corpus and test EGRF
corpus = EGCorpus("./corpus_examples/")
test_framework = CorpusTestFramework(corpus)

# Run all tests
test_framework.run_all_tests()

# Check results
for example_id, results in test_framework.test_results.items():
    if not results['all_passed']:
        print(f"FAILED: {example_id}")
        print(f"Issues: {results['failures']}")
```

### **Validating New EGRF Features**

```python
# Test specific feature against corpus
def test_auto_sizing_against_corpus():
    """Test auto-sizing feature against all corpus examples."""
    for example in corpus.all_examples():
        egrf = convert_eg_hg_to_egrf(example.load_eg_hg())
        layout = calculate_layout(egrf)
        
        # Validate layout follows EG conventions
        assert_proper_cut_nesting(layout)
        assert_ligature_continuity(layout)
        assert_no_overlapping_elements(layout)
```

### **EPG Development**

```python
# Use corpus for EPG development
epg_integration = EPGCorpusIntegration(corpus)

# Find good starting positions
starting_positions = []
for example in corpus.examples_with_epg_potential():
    position = epg_integration.generate_epg_starting_position(example)
    starting_positions.append(position)

# Create EPG scenarios
for position in starting_positions:
    scenario = EPGScenario(
        initial_graph=position['initial_graph'],
        transformation_rules=get_transformation_rules(),
        victory_conditions=position.get('victory_conditions')
    )
```

## Quality Assurance

### **Validation Checklist**

For each corpus entry:

1. **Source Verification**
   - [ ] Original source confirmed and accessible
   - [ ] Citation complete and accurate
   - [ ] Context properly documented

2. **Logical Accuracy**
   - [ ] EG-HG conversion verified by experts
   - [ ] CLIF translation semantically equivalent
   - [ ] Structure follows Peirce's conventions

3. **Technical Integration**
   - [ ] Files load correctly in test framework
   - [ ] All format conversions work
   - [ ] Automated tests pass

4. **Documentation Quality**
   - [ ] Test rationale clearly explained
   - [ ] EPG potential assessed
   - [ ] Transformation opportunities identified

### **Continuous Validation**

```python
# Automated corpus validation
def validate_corpus_integrity():
    """Validate entire corpus for consistency and accuracy."""
    validator = CorpusValidator()
    
    for example in corpus.all_examples():
        # Validate metadata completeness
        validator.check_metadata(example)
        
        # Validate file integrity
        validator.check_files(example)
        
        # Validate logical consistency
        validator.check_logic(example)
        
        # Validate test coverage
        validator.check_tests(example)
    
    return validator.generate_report()
```

## Benefits Realized

### **Immediate Testing Benefits**
- **Historical Accuracy**: Tests against authentic Peirce examples
- **Comprehensive Coverage**: Tests real-world EG complexity
- **Error Detection**: Catches semantic mistakes like our implication error
- **Regression Prevention**: Prevents future logical errors

### **Long-term EPG Benefits**
- **Rich Starting Positions**: Authentic examples for game scenarios
- **Transformation Opportunities**: Real examples with multiple valid moves
- **Educational Value**: Historical context enhances learning
- **Scholarly Credibility**: Grounded in established EG literature

### **Research Platform Benefits**
- **Reproducible Research**: Standard corpus for EG computational research
- **Community Resource**: Shared foundation for EG tool development
- **Preservation**: Digital preservation of EG heritage
- **Extension Framework**: Clear methodology for corpus expansion

This corpus-based approach transforms EGRF from a technical implementation into a **scholarly instrument** that authentically represents Peirce's Existential Graphs while providing the foundation for sophisticated EPG development.

