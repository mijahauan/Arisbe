# Arisbe Existential Graphs Corpus

This corpus contains examples of Peirce's Existential Graphs in EGRF format, organized by complexity level and logical pattern for testing and teaching purposes.

## Structure

### Alpha Level (Propositional Logic)
- **simple_assertion_pear.egrf**: Basic existential assertion with conjunction
- **simple_negation_phoenix.egrf**: Simple negation using single cut
- **conjunction_pear_orange.egrf**: Multiple assertions on sheet (conjunction)

### Beta Level (Predicate Logic)
- **thunder_lightning_implication.egrf**: Universal conditional using double cut
- **male_african_human.egrf**: Complex identity with multiple predicates
- **existential_with_negation.egrf**: Existential quantification with negation
- **thunder_without_lightning.egrf**: Conjunction with negation

### Canonical Examples
- **canonical_implication.egrf**: Standard implication pattern

### Peirce Primary Sources
- **peirce_cp_4_394_man_mortal.egrf**: From Collected Papers 4.394

### Scholars Examples
- **dau_2006_p112_ligature.egrf**: Ligature example from Dau
- **sowa_2011_p356_quantification.egrf**: Quantification from Sowa

## Complexity Levels

### Beginner (Alpha)
- Simple assertions and negations
- Basic conjunction patterns
- Single cut usage
- **Purpose**: Introduce fundamental EG concepts

### Intermediate (Beta)
- Existential and universal quantification
- Line of identity patterns
- Mixed assertion/negation
- Cut boundary crossing
- **Purpose**: Develop predicate logic understanding

### Advanced (Gamma)
- Modal operators
- Higher-order constructs
- Complex abstractions
- **Purpose**: Master advanced EG features

## Sources

### Primary References
1. **Roberts (1973)**: "The Existential Graphs of Charles S. Peirce"
   - Alpha examples: pp. 32-37
   - Beta examples: pp. 47-63
   - Gamma examples: pp. 64-86

2. **Sowa (2011)**: "Existential Graphs and EGIF"
   - Modern interpretations with EGIF notation
   - Clear predicate calculus mappings

3. **Dau (2006)**: "Constants and Functions in Peirce's Existential Graphs"
   - Extensions for constants and functions
   - Formal mathematical treatment

## EGRF Format

Each corpus entry follows the EGRF 3.0 format with:

### Required Fields
- **metadata**: Source, description, complexity, teaching purpose
- **elements**: All logical elements with properties and constraints
- **containment**: Parent-child relationships
- **connections**: Entity-predicate connections
- **ligatures**: Lines of identity
- **logical_content**: CLIF, EGIF, and natural language forms

### Element Types
- **context**: sheet, cut
- **predicate**: relation with arity and connected entities
- **entity**: variable, constant, or functional term

## Testing

All corpus entries are validated for:
- ✅ JSON format correctness
- ✅ Required field presence
- ✅ CLIF parsing compatibility
- ✅ EGRF conversion compatibility
- ✅ Element structure validity
- ✅ Connection integrity

Run tests with:
```bash
python3 test_new_corpus_entries.py
```

## Teaching Applications

### Progressive Learning Path
1. **Alpha**: Start with simple assertions and negations
2. **Beta**: Progress to quantification and ligatures
3. **Gamma**: Advance to modal and higher-order logic

### Test Coverage
- **Parsing**: CLIF → EG-HG → EGRF pipeline
- **Layout**: Constraint solving and visual conventions
- **Rendering**: Graphics generation and display
- **Interaction**: Graph editing and transformation

### Research Applications
- **Logical Analysis**: Formal system validation
- **Computational Implementation**: Algorithm testing
- **Educational Tools**: Interactive learning systems
- **Historical Studies**: Peirce's logical development

## Future Expansions

### Planned Additions
1. **Constants and Functions**: From Dau's extensions
2. **Modal Logic**: From Roberts Chapter 5
3. **Tinctured Graphs**: From Roberts Chapter 6
4. **Higher-Order Logic**: From Roberts Chapter 7
5. **Endoporeutic Examples**: Game-theoretic applications

### Additional Sources
- **Zeman (1964)**: "The Graphical Logic of C.S. Peirce"
- **Mathematical Logic with Diagrams**: Formal system development
- **Ligatures Semiotica**: Line of identity analysis

## Citation

When using this corpus, please cite:

```
Arisbe Existential Graphs Corpus (2025). Expanded from primary sources:
Roberts, D.D. (1973). The Existential Graphs of Charles S. Peirce. Mouton.
Sowa, J.F. (2011). Existential Graphs and EGIF. EGIF Specification.
Dau, F. (2006). Constants and Functions in Peirce's Existential Graphs.
```

