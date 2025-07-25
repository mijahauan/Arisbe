# Authoritative EG Corpus Construction Plan

## Project Overview

**Goal**: Build a scholarly, authoritative corpus of Existential Graphs from the literature to serve as the foundation for testing, validation, and future Endoporeutic Game development.

**Dual Purpose**:
1. **Immediate**: Test rendering capacity (EG-HG ↔ CLIF/CGIF/EGIF ↔ diagrams)
2. **Future**: Support EPG with transformation rules and Proposer/Skeptic dialog

## Corpus Architecture

### **Directory Structure**
```
Arisbe_EG_Corpus/
├── metadata/
│   ├── corpus_schema.json          # Data structure definitions
│   ├── source_bibliography.json    # Complete source references
│   └── validation_log.json         # Quality assurance records
├── examples/
│   ├── peirce_primary/             # Peirce's original examples
│   │   ├── collected_papers/       # CP examples by volume/section
│   │   ├── manuscripts/            # Unpublished manuscript examples
│   │   └── correspondence/         # Examples from letters
│   ├── secondary_literature/       # Scholar interpretations/extensions
│   │   ├── roberts/               # Roberts' examples
│   │   ├── zeman/                 # Zeman's examples
│   │   ├── shin/                  # Shin's examples
│   │   └── dau/                   # Dau's examples
│   └── synthetic_canonical/        # Constructed canonical forms
│       ├── basic_patterns/         # Standard logical patterns
│       ├── transformation_pairs/   # Before/after transformation examples
│       └── epg_starting_positions/ # EPG game starting moves
├── formats/
│   ├── eg_hg/                     # EG-HG representations
│   ├── clif/                      # CLIF translations
│   ├── cgif/                      # CGIF translations (when applicable)
│   └── egif/                      # EGIF translations (when applicable)
└── documentation/
    ├── corpus_guide.md            # Usage and interpretation guide
    ├── source_analysis.md         # Analysis of source materials
    └── transformation_rules.md    # EPG transformation documentation
```

### **Example Entry Structure**
Each corpus example follows this schema:

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
      "editor": "Charles Hartshorne and Paul Weiss",
      "publisher": "Harvard University Press",
      "citation": "Peirce, C.S. (1932). Collected Papers, Vol. 4, §4.394. Harvard University Press."
    },
    "logical_pattern": "universal_conditional",
    "complexity_level": "intermediate",
    "peirce_system": "alpha",
    "test_rationale": "Canonical example of double-cut implication structure; tests proper nesting, quantifier scoping, and ligature continuity across cuts.",
    "epg_potential": "excellent_starting_move",
    "transformation_opportunities": ["iteration", "deiteration", "insertion", "erasure"]
  },
  "logical_content": {
    "english": "If anything is a man, then it is mortal.",
    "clif": "(forall (x) (if (Man x) (Mortal x)))",
    "cgif": "[If: [Man: *x] [Then: [Mortal: *x]]]",
    "logical_form": "∀x(Man(x) → Mortal(x))",
    "semantic_notes": "Standard universal conditional with existential import questions typical of Peirce's period."
  },
  "eg_structure": {
    "cuts": 2,
    "nesting_depth": 2,
    "predicates": 2,
    "entities": 2,
    "ligatures": 1,
    "quantification": "universal_implicit",
    "structural_notes": "Double-cut implication with ligature crossing cut boundaries."
  },
  "files": {
    "eg_hg": "peirce_cp_4_394_man_mortal.eg-hg",
    "clif": "peirce_cp_4_394_man_mortal.clif",
    "cgif": "peirce_cp_4_394_man_mortal.cgif",
    "diagram": "peirce_cp_4_394_man_mortal.svg",
    "source_image": "peirce_cp_4_394_original.png"
  },
  "validation": {
    "verified_by": ["expert_1", "expert_2"],
    "verification_date": "2025-07-22",
    "logical_consistency": "verified",
    "source_fidelity": "high",
    "notes": "Verified against original CP text and multiple scholarly interpretations."
  }
}
```

## Source Prioritization

### **Tier 1: Peirce Primary Sources (Essential)**

#### **A. Collected Papers (CP)**
**Priority Examples:**
- **CP 4.394-417**: Core EG theory and examples
  - Man-Mortal implication (4.394)
  - Syllogistic forms (4.415)
  - Quantification examples (4.404-407)
  - Transformation demonstrations (4.416-417)

- **CP 1.417-520**: Mathematical logic applications
  - Set theory examples
  - Arithmetic in EG form
  - Proof structures

#### **B. Manuscripts (MS)**
**Robin Catalog Priority:**
- **MS 514**: "Existential Graphs" (1903)
- **MS 515**: "Prolegomena to an Apology for Pragmaticism" EG sections
- **MS 516**: Advanced EG theory

#### **C. Correspondence**
**Key Letters:**
- Letters to Lady Welby (EG explanations)
- Correspondence with students (pedagogical examples)

### **Tier 2: Secondary Literature (Interpretive)**

#### **A. Roberts (1973): *The Existential Graphs of Charles S. Peirce***
**Priority Examples:**
- Canonical form interpretations
- Transformation rule demonstrations
- Complex nested structures

#### **B. Zeman (1964): *The Graphical Logic of C.S. Peirce***
**Priority Examples:**
- Systematic logical analysis
- Comparison with standard logic
- Proof theory applications

#### **C. Shin (2002): *The Iconic Logic of Peirce's Graphs***
**Priority Examples:**
- Diagrammatic reasoning analysis
- Cognitive aspects of EG
- Modern logical interpretations

#### **D. Dau (2003): *The Logic System of Concept Graphs with Negation***
**Priority Examples:**
- Formal system development
- Computational applications
- Extended EG forms

### **Tier 3: Synthetic Canonical (Constructed)**

#### **A. Basic Pattern Library**
**Standard Forms:**
- Simple assertions: `Person(Socrates)`
- Simple negations: `¬Person(Socrates)`
- Conjunctions: `Person(Socrates) ∧ Mortal(Socrates)`
- Disjunctions: `Person(Socrates) ∨ God(Socrates)`
- Implications: `Person(Socrates) → Mortal(Socrates)`
- Biconditionals: `Person(x) ↔ Rational(x)`

#### **B. Quantification Patterns**
- Existential: `∃x Person(x)`
- Universal: `∀x (Person(x) → Mortal(x))`
- Mixed: `∀x ∃y Loves(x,y)`
- Nested: `∀x (Person(x) → ∃y (Parent(y,x) ∧ Person(y)))`

#### **C. EPG Starting Positions**
**Proposer Opening Moves:**
- Simple assertions for Skeptic to challenge
- Complex forms inviting transformation
- Ambiguous structures requiring clarification
- Proof sketches for completion

## Corpus Construction Methodology

### **Phase 1: Source Analysis and Digitization (4-6 weeks)**

#### **Week 1-2: Primary Source Survey**
1. **Systematic CP Review**
   - Identify all EG examples in CP 4.394-417
   - Catalog by logical pattern and complexity
   - Photograph/scan original diagrams

2. **Manuscript Analysis**
   - Access Robin catalog manuscripts
   - Identify unique examples not in CP
   - Document context and development

#### **Week 3-4: Secondary Literature Review**
1. **Scholar Example Extraction**
   - Roberts: Extract and categorize examples
   - Zeman: Focus on logical analysis examples
   - Shin: Collect diagrammatic reasoning cases
   - Dau: Gather computational applications

2. **Cross-Reference Analysis**
   - Identify overlapping examples
   - Note interpretive differences
   - Document scholarly consensus/disputes

#### **Week 5-6: Quality Assessment**
1. **Source Fidelity Verification**
   - Compare secondary sources to Peirce originals
   - Identify transcription errors or interpretive liberties
   - Document provenance chain

2. **Logical Consistency Check**
   - Verify CLIF translations
   - Check for semantic accuracy
   - Validate transformation claims

### **Phase 2: EG-HG Conversion (3-4 weeks)**

#### **Conversion Methodology**
1. **Expert Review Process**
   - Multiple EG scholars independently convert each example
   - Compare conversions and resolve differences
   - Document conversion rationale

2. **Validation Protocol**
   - Round-trip testing: EG-HG → CLIF → EG-HG
   - Semantic equivalence verification
   - Structural consistency checking

#### **Quality Assurance**
- **Double-blind conversion**: Two experts convert independently
- **Consensus building**: Resolve differences through discussion
- **Documentation**: Record all conversion decisions and rationale

### **Phase 3: CLIF Translation and Validation (2-3 weeks)**

#### **Translation Standards**
1. **CLIF Dialect Selection**
   - Use Common Logic standard
   - Document any extensions needed
   - Maintain consistency across corpus

2. **Semantic Fidelity**
   - Preserve Peirce's intended meaning
   - Handle existential import questions
   - Document interpretive choices

#### **Validation Process**
1. **Logical Consistency**
   - Automated consistency checking
   - Proof verification where applicable
   - Semantic equivalence testing

2. **Expert Review**
   - Logic specialists review translations
   - EG experts verify fidelity to originals
   - Document approval process

### **Phase 4: Annotation and Documentation (2 weeks)**

#### **Metadata Creation**
1. **Source Documentation**
   - Complete bibliographic information
   - Provenance chain documentation
   - Copyright and usage permissions

2. **Analytical Annotations**
   - Logical pattern classification
   - Complexity assessment
   - Test rationale documentation
   - EPG potential evaluation

#### **Documentation Standards**
- **Scholarly citations**: Full academic format
- **Rationale documentation**: Why each example is valuable
- **Usage guidelines**: How to interpret and use examples
- **Transformation notes**: EPG development potential

## EPG Integration Planning

### **Transformation Rule Documentation**
For each corpus example, document:

#### **A. Available Transformations**
- **Iteration**: Where can elements be duplicated?
- **Deiteration**: Where can duplicates be removed?
- **Insertion**: What can be added without changing meaning?
- **Erasure**: What can be removed without changing meaning?
- **Double Cut**: Where can double cuts be inserted/removed?

#### **B. Game Potential Assessment**
- **Starting Move Quality**: How interesting as EPG opening?
- **Transformation Richness**: How many moves are possible?
- **Educational Value**: What does it teach about EG logic?
- **Difficulty Level**: Appropriate for beginners/experts?

#### **C. Dialog Scenarios**
- **Proposer Strategies**: Effective opening approaches
- **Skeptic Challenges**: Natural points of attack
- **Resolution Paths**: How games typically develop
- **Learning Outcomes**: What players discover

### **EPG Corpus Subset**
Create specialized subset for EPG development:

```
epg_starting_positions/
├── beginner/
│   ├── simple_assertions/      # Basic Proposer claims
│   ├── obvious_contradictions/ # Easy Skeptic targets
│   └── single_transformations/ # One-move solutions
├── intermediate/
│   ├── multi_step_proofs/      # Require several moves
│   ├── strategic_choices/      # Multiple valid approaches
│   └── transformation_chains/  # Complex sequences
└── advanced/
    ├── deep_proofs/           # Many moves required
    ├── subtle_errors/         # Hard-to-spot mistakes
    └── creative_constructions/ # Open-ended exploration
```

## Implementation Timeline

### **Immediate Phase (Next 2-3 months)**
1. **Minimal Viable Corpus**: 15-20 key examples
   - 5 Peirce primary examples (CP 4.394-417)
   - 5 secondary literature examples
   - 5 synthetic canonical forms
   - 5 EPG starting positions

2. **Core Infrastructure**
   - Corpus schema implementation
   - Validation framework
   - Basic annotation system

### **Full Corpus Phase (6-12 months)**
1. **Complete Primary Sources**: All identifiable Peirce examples
2. **Comprehensive Secondary**: Major scholarly works covered
3. **Rich EPG Collection**: Full game scenario library
4. **Advanced Tooling**: Automated validation, search, analysis

## Quality Assurance Standards

### **Scholarly Rigor**
- **Multiple Expert Review**: Each example verified by 2+ EG specialists
- **Source Fidelity**: Faithful to original author's intent
- **Logical Accuracy**: Semantically correct translations
- **Documentation**: Complete provenance and rationale

### **Technical Standards**
- **Format Consistency**: Standardized file formats and naming
- **Validation**: Automated consistency checking
- **Version Control**: Complete change history
- **Accessibility**: Clear usage documentation

### **Community Standards**
- **Open Access**: Available to EG research community
- **Attribution**: Proper credit to all contributors
- **Extensibility**: Framework for community additions
- **Maintenance**: Long-term curation commitment

## Expected Outcomes

### **Immediate Benefits**
- **Authoritative Test Suite**: Validates EGRF implementation against historical examples
- **Scholarly Credibility**: Grounded in established EG literature
- **Error Prevention**: Catches semantic mistakes like our implication error
- **Educational Resource**: Supports EG learning and research

### **Long-term Impact**
- **EPG Foundation**: Enables sophisticated game development
- **Research Platform**: Supports computational EG research
- **Preservation**: Digital preservation of EG heritage
- **Community Building**: Focal point for EG scholarship

This corpus will transform EGRF from a technical implementation into a **scholarly instrument** worthy of serious EG research and EPG development.

