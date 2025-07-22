# EG Minimal Viable Corpus: Implementation Plan

## Immediate Goal

Create a **focused, high-quality corpus** of 15-20 essential EG examples to serve as the foundation for EGRF testing and validation.

## Selection Criteria

Each example must:
1. **Demonstrate a key EG pattern** or logical structure
2. **Have clear provenance** from authoritative sources
3. **Test specific EGRF functionality**
4. **Be well-documented** with complete annotations
5. **Have verified logical translations** in CLIF

## Core Example Set

### **Category 1: Peirce Primary Examples (5)**

#### **1. Universal Conditional (CP 4.394)**
```
ID: peirce_cp_4_394_man_mortal
Pattern: Double-cut implication
English: "If anything is a man, then it is mortal."
CLIF: (forall (x) (if (Man x) (Mortal x)))
Structure: Sheet → Cut1 → [Man(x), Cut2 → [Mortal(x)]]
Test Focus: Double-cut implication structure, ligature crossing cuts
```

#### **2. Simple Negation (CP 4.395)**
```
ID: peirce_cp_4_395_not_perfect
Pattern: Single-cut negation
English: "Something is not perfect."
CLIF: (exists (x) (not (Perfect x)))
Structure: Sheet → [Cut → [Perfect(x)]]
Test Focus: Single cut with proper scoping, existential quantification
```

#### **3. Conjunction (CP 4.399)**
```
ID: peirce_cp_4_399_man_mortal
Pattern: Juxtaposition as conjunction
English: "Something is both a man and mortal."
CLIF: (exists (x) (and (Man x) (Mortal x)))
Structure: Sheet → [Man(x), Mortal(x)] with shared ligature
Test Focus: Juxtaposition, ligature connections, entity sharing
```

#### **4. Nested Quantification (CP 4.404)**
```
ID: peirce_cp_4_404_lover_of_something
Pattern: Nested quantification
English: "Everyone loves something."
CLIF: (forall (x) (exists (y) (Loves x y)))
Structure: Sheet → Cut1 → [Person(x), Cut2 → [Cut3 → [Loves(x,y)]]]
Test Focus: Multiple nesting levels, complex ligature routing
```

#### **5. Syllogistic Form (CP 4.415)**
```
ID: peirce_cp_4_415_barbara_syllogism
Pattern: Barbara syllogism
English: "All men are mortal; Socrates is a man; therefore Socrates is mortal."
CLIF: (and (forall (x) (if (Man x) (Mortal x))) (Man Socrates))
Structure: Complex nested structure with multiple cuts
Test Focus: Complex logical form, mixed quantification, constants
```

### **Category 2: Secondary Literature Examples (5)**

#### **1. Roberts' Disjunction (Roberts 1973, p.45)**
```
ID: roberts_1973_p45_disjunction
Pattern: Disjunction via negated conjunction
English: "Either it is raining or it is snowing."
CLIF: (or (Raining) (Snowing))
Structure: Sheet → [Cut → [Cut → [Raining], Cut → [Snowing]]]
Test Focus: Disjunction representation, multiple cuts at same level
```

#### **2. Zeman's Biconditional (Zeman 1964, p.87)**
```
ID: zeman_1964_p87_biconditional
Pattern: Biconditional (if and only if)
English: "A person is rational if and only if they are human."
CLIF: (forall (x) (iff (Person x) (Rational x)))
Structure: Complex double implication structure
Test Focus: Bidirectional implication, complex cut nesting
```

#### **3. Shin's Identity Example (Shin 2002, p.124)**
```
ID: shin_2002_p124_identity
Pattern: Identity relation
English: "Cicero is Tully."
CLIF: (= Cicero Tully)
Structure: Sheet → [Cicero = Tully] with identity line
Test Focus: Identity representation, constants, special relations
```

#### **4. Dau's Relation Composition (Dau 2003, p.156)**
```
ID: dau_2003_p156_relation_composition
Pattern: Relation composition
English: "If x is a parent of y and y is a parent of z, then x is a grandparent of z."
CLIF: (forall (x y z) (if (and (Parent x y) (Parent y z)) (Grandparent x z)))
Structure: Complex nested structure with multiple relations
Test Focus: Relation composition, multiple variables, complex nesting
```

#### **5. Hammer's Quantifier Scope (Hammer 1998, p.73)**
```
ID: hammer_1998_p73_quantifier_scope
Pattern: Quantifier scope distinction
English: "There is someone who loves everyone" vs "Everyone is loved by someone"
CLIF: (exists (x) (forall (y) (Loves x y))) vs (forall (y) (exists (x) (Loves x y)))
Structure: Two contrasting structures with different nesting
Test Focus: Quantifier scope, nesting order importance, semantic distinction
```

### **Category 3: Synthetic Canonical Forms (5)**

#### **1. Triple Negation**
```
ID: synthetic_triple_negation
Pattern: Triple nested cuts
English: "It is not the case that it is not the case that it is not raining."
CLIF: (not (not (not (Raining))))
Structure: Sheet → [Cut → [Cut → [Cut → [Raining]]]]
Test Focus: Deep nesting, triple negation, cut rendering
```

#### **2. Complex Conjunction**
```
ID: synthetic_complex_conjunction
Pattern: Multi-element conjunction
English: "Socrates is wise, old, Greek, and a philosopher."
CLIF: (and (Wise Socrates) (Old Socrates) (Greek Socrates) (Philosopher Socrates))
Structure: Sheet → [Wise(s), Old(s), Greek(s), Philosopher(s)] with shared ligature
Test Focus: Multiple predicates sharing entity, layout optimization
```

#### **3. Nested Relations**
```
ID: synthetic_nested_relations
Pattern: Nested relational predicates
English: "John believes that Mary knows that Bill loves Sue."
CLIF: (Believes John (Knows Mary (Loves Bill Sue)))
Structure: Complex nesting with multiple relations
Test Focus: Nested propositional attitudes, relation embedding
```

#### **4. Quantifier Alternation**
```
ID: synthetic_quantifier_alternation
Pattern: Alternating quantifiers
English: "For every x, there exists a y, such that for every z, there exists a w, such that R(x,y,z,w)."
CLIF: (forall (x) (exists (y) (forall (z) (exists (w) (R x y z w)))))
Structure: Deep alternating nesting structure
Test Focus: Complex quantification, deep nesting, multiple variables
```

#### **5. Mixed Logical Operators**
```
ID: synthetic_mixed_operators
Pattern: Multiple logical operators
English: "If it's not raining, then either it's sunny or it's cloudy but not windy."
CLIF: (if (not (Raining)) (or (Sunny) (and (Cloudy) (not (Windy)))))
Structure: Complex combination of cuts and juxtapositions
Test Focus: Mixed logical operators, complex structure rendering
```

### **Category 4: EPG Starting Positions (5)**

#### **1. Simple Contradiction**
```
ID: epg_simple_contradiction
Pattern: Contradictory assertions
English: "Socrates is both mortal and not mortal."
CLIF: (and (Mortal Socrates) (not (Mortal Socrates)))
Structure: Sheet → [Mortal(s), Cut → [Mortal(s)]]
Test Focus: Contradiction detection, transformation opportunities
EPG Value: Basic erasure demonstration
```

#### **2. Provable Implication**
```
ID: epg_provable_implication
Pattern: Provable conditional
English: "If A and B, then A."
CLIF: (if (and A B) A)
Structure: Sheet → [Cut → [A, B, Cut → [A]]]
Test Focus: Logical tautology structure
EPG Value: Demonstrates deiteration transformation
```

#### **3. Quantifier Challenge**
```
ID: epg_quantifier_challenge
Pattern: Quantifier manipulation
English: "There exists an x such that P(x) and Q(x)" to be transformed to "There exists an x such that P(x) and there exists an x such that Q(x)"
CLIF: (exists (x) (and (P x) (Q x))) vs (and (exists (x) (P x)) (exists (x) (Q x)))
Structure: Transformation pair with different quantifier scopes
Test Focus: Quantifier scope changes, transformation validity
EPG Value: Demonstrates quantifier transformation rules
```

#### **4. Double Negation**
```
ID: epg_double_negation
Pattern: Double negation elimination
English: "It is not the case that it is not raining."
CLIF: (not (not (Raining)))
Structure: Sheet → [Cut → [Cut → [Raining]]]
Test Focus: Double cut elimination
EPG Value: Demonstrates double-cut rule
```

#### **5. Complex Transformation Chain**
```
ID: epg_transformation_chain
Pattern: Multi-step transformation
English: Complex logical form requiring multiple transformation steps
CLIF: (Complex form with multiple transformation opportunities)
Structure: Strategically designed for multiple valid moves
Test Focus: Multiple transformation paths
EPG Value: Demonstrates strategic thinking in EPG
```

## Implementation Steps

### **Step 1: Schema Development (1 week)**
1. **Create JSON Schema**
   - Define metadata structure
   - Establish file naming conventions
   - Document annotation requirements

2. **Set Up Repository Structure**
   - Create directory hierarchy
   - Implement version control
   - Document contribution guidelines

### **Step 2: Source Extraction (2 weeks)**
1. **Primary Source Work**
   - Extract Peirce examples from CP
   - Scan/photograph original diagrams
   - Document context and interpretation

2. **Secondary Literature Review**
   - Extract key examples from scholars
   - Document interpretive differences
   - Verify against primary sources where possible

### **Step 3: EG-HG Conversion (2 weeks)**
1. **Conversion Protocol**
   - Establish consistent conversion methodology
   - Document conversion decisions
   - Implement quality checks

2. **Expert Review**
   - Multiple experts review each conversion
   - Resolve discrepancies
   - Document consensus process

### **Step 4: CLIF Translation (1 week)**
1. **Translation Standards**
   - Establish CLIF dialect and conventions
   - Document translation choices
   - Ensure semantic fidelity

2. **Validation Process**
   - Verify logical equivalence
   - Check for translation errors
   - Document validation results

### **Step 5: Annotation and Documentation (1 week)**
1. **Complete Metadata**
   - Fill all required fields
   - Document test rationale
   - Add EPG potential assessment

2. **Create Usage Documentation**
   - How to use corpus for testing
   - How to interpret examples
   - How to extend corpus

### **Step 6: Integration with EGRF Testing (1 week)**
1. **Test Framework Integration**
   - Create corpus-based test suite
   - Implement automated validation
   - Document test coverage

2. **Validation Report**
   - Test EGRF against corpus
   - Document results
   - Identify improvement areas

## Quality Assurance

### **Validation Checklist**
For each corpus example:

- [ ] **Source Verification**: Original source confirmed and documented
- [ ] **EG-HG Accuracy**: Conversion verified by multiple experts
- [ ] **CLIF Correctness**: Translation semantically equivalent to original
- [ ] **Structural Validation**: EG structure follows Peirce's conventions
- [ ] **Metadata Completeness**: All required fields populated
- [ ] **Test Coverage**: Specific EGRF functionality tested
- [ ] **Documentation Quality**: Clear, complete annotations

### **Review Process**
1. **Initial Creation**: Primary contributor creates example
2. **Expert Review**: 2+ EG experts review for accuracy
3. **Technical Validation**: Automated checks for format compliance
4. **Integration Testing**: Verify works with EGRF test suite
5. **Final Approval**: Corpus maintainer approves addition

## Deliverables

### **Week 1-2**
- Schema definition
- Repository structure
- Initial 5 examples (1 from each category)

### **Week 3-4**
- 10 additional examples
- Initial validation results
- Draft documentation

### **Week 5-6**
- Complete 20-example MVP corpus
- Full documentation
- Integration with EGRF test suite
- Validation report

### **Week 7-8**
- Refinements based on testing
- Extended documentation
- Future expansion plan

## Success Criteria

The Minimal Viable Corpus will be considered successful when:

1. **All 20 examples** are fully implemented with complete metadata
2. **EGRF tests** successfully run against all corpus examples
3. **Documentation** is clear and comprehensive
4. **Validation** confirms logical correctness of all examples
5. **EPG potential** is documented for future development

This focused approach will deliver a high-quality foundation corpus in 6-8 weeks, providing immediate value for EGRF testing while establishing the methodology for future corpus expansion.

