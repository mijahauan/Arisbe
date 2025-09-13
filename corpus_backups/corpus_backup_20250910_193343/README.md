# Existential Graphs Corpus

This directory contains a curated corpus of Existential Graphs (EG) examples for testing and validation of the EGRF v3.0 implementation.

## Corpus Structure

Each example in the corpus consists of multiple files with the same base name but different extensions:

- `.json` - Metadata and annotations about the example
- `.eg-hg` - EG-HG (Existential Graph Hypergraph) representation
- `.clif` - Common Logic Interchange Format representation
- `.egrf` - Existential Graph Rendering Format (v3.0) representation

## Corpus Categories

The corpus is organized into four categories:

1. **peirce/** - Examples directly from Peirce's writings
2. **scholars/** - Examples from secondary literature by EG scholars
3. **canonical/** - Synthetic examples of standard logical patterns
4. **epg/** - Examples suitable as starting positions for the Endoporeutic Game

## Minimal Viable Corpus

The initial minimal viable corpus consists of 20 examples:

- 5 examples from Peirce's writings
- 5 examples from secondary literature
- 5 synthetic canonical examples
- 5 EPG starting positions

## Metadata Format

Each `.json` metadata file contains:

```json
{
  "id": "unique_identifier",
  "category": "peirce|scholars|canonical|epg",
  "source": {
    "author": "Author name",
    "work": "Title of work",
    "year": 1900,
    "page": "Page number or reference",
    "url": "URL if available"
  },
  "description": "Brief description of the example",
  "logical_form": "Formal logical expression",
  "natural_language": "Natural language expression",
  "complexity": {
    "nesting_depth": 2,
    "entity_count": 3,
    "predicate_count": 2,
    "cut_count": 2
  },
  "test_rationale": "Why this example is valuable for testing",
  "epg_features": {
    "is_starting_position": true,
    "valid_transformations": ["insertion", "deletion", "iteration"],
    "invalid_transformations": ["deiteration"]
  }
}
```

## Usage

The corpus is used for:

1. Testing the EGRF v3.0 implementation
2. Validating the EG-HG to EGRF converter
3. Ensuring logical correctness of the implementation
4. Providing examples for documentation
5. Supporting EPG development

## Contributing

To add a new example to the corpus:

1. Create a new `.json` metadata file
2. Create the corresponding `.eg-hg`, `.clif`, and `.egrf` files
3. Ensure all files follow the established formats
4. Update the corpus index in `corpus_index.json`

## References

- Peirce, C.S. (1931-1958). Collected Papers of Charles Sanders Peirce. Cambridge, MA: Harvard University Press.
- Roberts, D.D. (1973). The Existential Graphs of Charles S. Peirce. The Hague: Mouton.
- Zeman, J.J. (1964). The Graphical Logic of C.S. Peirce. Chicago: University of Chicago.
- Shin, S.J. (2002). The Iconic Logic of Peirce's Graphs. Cambridge, MA: MIT Press.
- Dau, F. (2006). Mathematical Logic with Diagrams. Berlin: Logos Verlag.

