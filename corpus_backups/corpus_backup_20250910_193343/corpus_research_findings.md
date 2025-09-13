# Corpus Research Findings from References

## Overview
This document captures examples and patterns found in the reference materials for expanding the Arisbe corpus.

## Current Corpus Status
- **Existing entries**: 5 examples
  - 1 canonical (canonical_implication)
  - 1 Peirce primary (peirce_cp_4_394_man_mortal)
  - 3 scholars (dau_2006_p112_ligature, roberts_1973_p57_disjunction, sowa_2011_p356_quantification)

## Reference Analysis

### 1. "Existential Graphs of Peirce" by Roberts (1973)

**Source**: `/home/ubuntu/Arisbe/docs/references/Existential Graphs of Peirce.pdf`
**Total Pages**: 169
**Key Sections**:
- Chapter 3: Alpha (propositional logic) - pages 31-46
- Chapter 4: Beta (predicate logic) - pages 47-63  
- Chapter 5: Gamma (modal/higher-order logic) - pages 64-86
- Chapter 6: Tinctured Existential Graphs - pages 87-109
- Chapter 7: Graphical Analysis - pages 110-128

**Alpha Conventions Found** (pages 31-33):
1. **Sheet of Assertion (SA)**: The fundamental surface representing universe of discourse
2. **Graph Scribing**: Writing on SA asserts truth in that universe
3. **Basic Symbols**: Sheet, cut, and graph are the three fundamental elements

**Key Quote** (p. 32): 
> "Whatever we write upon it [SA] can be thought of as making the representation of the universe more determinate"

**Example Pattern Identified** (p. 32):
- Simple assertion: "A pear is ripe" written on SA
- Meaning: "there is a pear in our universe, and it is ripe"

### 2. Research Strategy for Additional References

**Next Priority References**:
1. **Zeman (1964)**: "The Graphical Logic of C.S. Peirce" - systematic logical analysis
2. **Dau (2003)**: EG-constants and functions - computational applications  
3. **Sowa**: EGIF specification - modern interpretations
4. **Mathematical Logic with Diagrams**: formal system development

## Patterns for Corpus Expansion

### Alpha Level Examples Needed:
1. **Simple Assertions**: Basic predicate statements
2. **Negations**: Single cut examples
3. **Conjunctions**: Multiple statements on sheet
4. **Disjunctions**: Complex cut arrangements
5. **Implications**: Double cut patterns
6. **Biconditionals**: Symmetric double cuts

### Beta Level Examples Needed:
1. **Existential Quantification**: Line of identity patterns
2. **Universal Quantification**: Double cut with existential
3. **Mixed Quantifiers**: Complex nesting
4. **Relational Predicates**: Multi-argument relations
5. **Function Applications**: Functional terms

### Gamma Level Examples Needed:
1. **Modal Operators**: Necessity/possibility
2. **Higher-Order Logic**: Predicates of predicates
3. **Abstractions**: Lambda-like constructs
4. **Graphs of Graphs**: Meta-level representations

## Complexity Levels for Teaching

### Beginner (Alpha):
- Single assertions
- Simple negations  
- Basic conjunctions
- Elementary implications

### Intermediate (Beta):
- Existential statements
- Universal conditionals
- Mixed quantification
- Relational predicates

### Advanced (Gamma):
- Modal logic
- Higher-order constructs
- Complex abstractions
- Meta-logical statements

## Next Steps
1. Extract specific examples from Roberts Chapter 3 (Alpha)
2. Analyze Zeman for systematic logical patterns
3. Review Dau for computational examples
4. Create EGRF entries following existing format



### 3. Dau (2006): "Constants and Functions in Peirce's Existential Graphs"

**Source**: `/home/ubuntu/Arisbe/docs/references/EG-constants and functions-Dau.pdf`
**Total Pages**: 14
**Focus**: Extending EG to handle constants and functions

**Key Insights**:
1. **Standard EG Limitation**: Beta EG corresponds to first-order logic with relations and identity, but WITHOUT constants or functions
2. **Modern Need**: Contemporary FO logic includes constants and functions that EG needs to handle
3. **Formal Approach**: Uses "Existential Graph Instances" (EGIs) as discrete structures

**Technical Contribution**:
- **Relational Graphs with Cuts**: Formal structure (V,E,ν,>,Cut,area)
- **Vertices, Edges, Cuts**: Basic elements with sheet of assertion (>)
- **Area mapping**: Defines containment relationships

**Examples Needed for Corpus**:
1. **Constants**: Individual objects (e.g., "Socrates", "7", "π")
2. **Functions**: Mappings (e.g., "father-of", "square-of", "capital-of")
3. **Complex Relations**: Multi-argument predicates with constants/functions

### 4. Roberts (1973) - Continued Analysis

**Alpha Examples Found** (pages 34-37):

#### Example 1: Simple Assertions
- **Pattern**: "A pear is ripe" on sheet of assertion
- **Meaning**: Existential assertion with predicate
- **CLIF**: `(exists (x) (and (Pear x) (Ripe x)))`
- **Complexity**: Beginner

#### Example 2: Conjunction
- **Pattern**: Multiple statements on sheet
  - "A pear is ripe"
  - "The pulp of some oranges is red"
- **Meaning**: Both statements true in universe
- **CLIF**: `(and (exists (x) (and (Pear x) (Ripe x))) (exists (y) (and (Orange y) (Red (pulp-of y)))))`
- **Complexity**: Beginner

#### Example 3: Material Implication (Double Cut)
- **Pattern**: "If P then Q" using scroll (double cut)
- **Structure**: P in outer area, Q in inner cut
- **Meaning**: Either P is false or Q is true
- **CLIF**: `(if P Q)`
- **Complexity**: Intermediate

#### Example 4: Negation (Single Cut)
- **Pattern**: Single cut around proposition
- **Example**: "It is false that it rains" 
- **Structure**: "It rains" inside single cut
- **CLIF**: `(not (Rains))`
- **Complexity**: Beginner

#### Example 5: Complex Conditional
- **Pattern**: "If some oranges have red pulp then naturalness is the last perfection of style"
- **Structure**: Double cut with complex antecedent and consequent
- **Complexity**: Advanced

### 5. Additional References Analysis

#### EGIF-Sowa.pdf
**Status**: Need to examine for modern EG interpretations and examples

#### Mathematical Logic with Diagrams
**Status**: Need to examine for formal system examples

#### Ligatures Semiotica v2.pdf  
**Status**: Need to examine for line of identity examples

## Priority Examples for Corpus Expansion

### Immediate Additions (Alpha Level):
1. **Simple Assertion**: "A pear is ripe"
2. **Simple Negation**: "It is not raining"
3. **Basic Conjunction**: Two assertions on sheet
4. **Material Implication**: "If P then Q" double cut
5. **Complex Conditional**: Real-world example from Roberts

### Next Phase (Beta Level):
1. **Existential with Line of Identity**: Connected predicates
2. **Universal Quantification**: Double cut pattern
3. **Constants**: Named individuals (from Dau)
4. **Functions**: Functional terms (from Dau)
5. **Relational Predicates**: Multi-argument relations

### Advanced (Gamma Level):
1. **Modal Operators**: From Roberts Chapter 5
2. **Higher-Order**: Predicates of predicates
3. **Abstractions**: Lambda-like constructs
4. **Tinctured Graphs**: From Roberts Chapter 6

## Corpus Entry Format Requirements

Based on existing `peirce_cp_4_394_man_mortal.egrf`:

### Required Fields:
1. **metadata**: format, version, source, description
2. **elements**: All logical elements with properties and constraints
3. **containment**: Parent-child relationships
4. **connections**: Entity-predicate connections
5. **ligatures**: Lines of identity

### Element Types:
- **context**: sheet, cut
- **predicate**: relation with arity and connected entities
- **entity**: variable, constant, or functional term

### Layout Constraints:
- **size**: min/preferred width/height for each element
- **positioning**: implicit through containment hierarchy


### 6. Sowa (2011): "Existential Graphs and EGIF"

**Source**: `/home/ubuntu/Arisbe/docs/references/EGIF-Sowa.pdf`
**Total Pages**: 11
**Focus**: Modern interpretation and linear notation for EG

**Key Contributions**:
1. **EGIF Format**: Linear notation with full Common Logic expressiveness
2. **Modern Examples**: Clear mappings to predicate calculus
3. **Practical Syntax**: Simplified notation for implementation

**Examples Extracted**:

#### Example 1: Simple Existence
- **EG**: Line of identity with "phoenix"
- **EGIF**: `(phoenix *x)`
- **Predicate Calculus**: `∃x phoenix(x)`
- **English**: "There is a phoenix"
- **Complexity**: Beginner

#### Example 2: Simple Negation
- **EG**: "phoenix" inside shaded cut
- **EGIF**: `~[ (phoenix *x) ]`
- **Predicate Calculus**: `~∃x phoenix(x)`
- **English**: "There is no phoenix"
- **Complexity**: Beginner

#### Example 3: Existential with Negation
- **EG**: Line outside cut, "phoenix" inside cut
- **EGIF**: `[*x] ~[ (phoenix x) ]`
- **Predicate Calculus**: `∃x ~phoenix(x)`
- **English**: "There is something that is not a phoenix"
- **Complexity**: Intermediate

#### Example 4: Conjunction
- **EG**: "thunder" and negated "lightning"
- **EGIF**: `(thunder *x) ~[ (lightning x) ]`
- **Predicate Calculus**: `∃x (thunder(x) ∧ ~lightning(x))`
- **English**: "It thunders without lightning"
- **Complexity**: Intermediate

#### Example 5: Implication (Double Cut)
- **EG**: Double nested cuts for if-then
- **EGIF**: `~[ (thunder *x) ~[ (lightning x) ] ]`
- **Alternative**: `[If (thunder *x) [Then (lightning x) ] ]`
- **Predicate Calculus**: `∀x (thunder(x) ⊃ lightning(x))`
- **English**: "If it thunders, it lightens"
- **Complexity**: Intermediate

#### Example 6: Complex Identity (Ligature)
- **EG**: Three predicates connected by line of identity
- **EGIF**: `(male *x) (human x) (African x)`
- **Predicate Calculus**: `∃x (male(x) ∧ human(x) ∧ African(x))`
- **English**: "There is a male African human"
- **Complexity**: Intermediate

#### Example 7: Identity Relations
- **EG**: Explicit identity dyads
- **EGIF**: `(man *x) (is x *y) (is y *z) (African z)`
- **Simplified**: `(man *x) (African x)`
- **Predicate Calculus**: `∃x (man(x) ∧ African(x))`
- **English**: "There is an African man"
- **Complexity**: Advanced

## Summary of Research Findings

### Total Examples Identified: 15+

#### Beginner Level (Alpha):
1. Simple assertion: "A pear is ripe" (Roberts)
2. Simple existence: "There is a phoenix" (Sowa)
3. Simple negation: "There is no phoenix" (Sowa)
4. Basic conjunction: Multiple statements on sheet (Roberts)
5. Single cut negation: "It is not raining" (Roberts)

#### Intermediate Level (Beta):
6. Material implication: "If P then Q" double cut (Roberts)
7. Existential with negation: "Something is not a phoenix" (Sowa)
8. Conjunction with negation: "Thunder without lightning" (Sowa)
9. Universal conditional: "If thunder then lightning" (Sowa)
10. Complex identity: "Male African human" (Sowa)

#### Advanced Level (Beta/Gamma):
11. Complex conditional: Orange pulp example (Roberts)
12. Identity relations: Explicit identity dyads (Sowa)
13. Constants and functions: From Dau's extensions
14. Modal operators: From Roberts Chapter 5
15. Higher-order constructs: From Roberts Chapter 7

### Reference Coverage:
- **Roberts (1973)**: ✅ Alpha examples extracted, Beta/Gamma identified
- **Sowa (2011)**: ✅ Modern examples with EGIF mappings
- **Dau (2006)**: ✅ Constants/functions extensions identified
- **Zeman (1964)**: ❌ PDF access issues, need alternative approach
- **Mathematical Logic**: ❌ Not yet examined
- **Ligatures Semiotica**: ❌ Not yet examined

### Next Phase Requirements:
1. Create EGRF entries for identified examples
2. Follow existing format from `peirce_cp_4_394_man_mortal.egrf`
3. Include proper metadata with source citations
4. Add complexity levels and teaching rationale
5. Ensure CLIF translations are correct
6. Test with existing EGRF system

