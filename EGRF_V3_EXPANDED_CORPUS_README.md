# EGRF v3.0 Expanded Corpus

This package contains the expanded corpus for EGRF v3.0, including examples from Peirce's writings and scholarly works by Roberts, Sowa, and Dau. These examples provide a comprehensive test suite for validating the EGRF v3.0 implementation against authoritative sources.

## Contents

### Peirce's Original Examples
- **peirce_cp_4_394_man_mortal** - Peirce's classic example of implication: "If a man, then mortal"

### Scholarly Examples
- **roberts_1973_p57_disjunction** - Roberts' example of disjunction using Peirce's double-cut method
- **sowa_2011_p356_quantification** - Sowa's example of existential quantification in Beta graphs
- **dau_2006_p112_ligature** - Dau's example of complex ligature handling with lines crossing cut boundaries

### Canonical Examples
- **canonical_implication** - Standard logical pattern for implication using double cuts

## Key Features Tested

### 1. Logical Structures
- **Double-cut implication** - Proper nesting of cuts to represent "if-then" statements
- **Disjunction** - Representation of "or" using double cuts and negation
- **Existential quantification** - Use of lines of identity to represent existentially quantified variables
- **Negation** - Use of cuts to represent negation

### 2. Visual Conventions
- **Odd/even area shading** - Alternating shading based on nesting level
- **Predicate placement** - Proper placement of predicates within containing contexts
- **Line of identity** - Representation of entities with lines connecting predicates
- **Ligatures crossing cuts** - Proper handling of lines that cross cut boundaries

### 3. Containment Hierarchy
- **Proper nesting** - Correct containment relationships between contexts
- **Auto-sizing** - Containers sized based on their contents
- **Layout constraints** - Platform-independent positioning rules

## Usage

### Validating the Corpus

```bash
./validate_corpus.py
```

### Adding New Examples

1. Create the necessary files in the appropriate directory:
   - `example_id.json` - Metadata
   - `example_id.eg-hg` - EG-HG representation
   - `example_id.clif` - CLIF representation
   - `example_id.egrf` - EGRF v3.0 representation

2. Add the example to `corpus_index.json`

3. Validate the example:
   ```bash
   ./validate_corpus.py
   ```

## Scholarly Sources

1. Roberts, Don D. *The Existential Graphs of Charles S. Peirce*. The Hague: Mouton, 1973.
2. Sowa, John F. "Peirce's Tutorial on Existential Graphs." *Semiotica*, vol. 186, no. 1-4, 2011, pp. 345-394.
3. Dau, Frithjof. *Mathematical Logic with Diagrams*. Habilitation thesis, Technische Universität Darmstadt, 2006.

## Next Steps

1. Implement the EG-HG to EGRF v3.0 converter
2. Validate the converter with the corpus examples
3. Create comprehensive documentation and examples

