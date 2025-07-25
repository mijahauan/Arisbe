# EGRF v3.0 Corpus Implementation

This package contains the implementation of the corpus-based testing approach for EGRF v3.0. It includes a minimal viable corpus with examples from Peirce's writings and canonical logical patterns, as well as a comprehensive validation framework to ensure logical correctness.

## Contents

- `corpus/` - Directory containing the corpus examples
  - `peirce/` - Examples from Peirce's writings
  - `scholars/` - Examples from secondary literature
  - `canonical/` - Synthetic examples of standard logical patterns
  - `epg/` - Examples suitable as starting positions for the Endoporeutic Game
  - `corpus_index.json` - Index of all examples in the corpus
  - `README.md` - Documentation for the corpus structure

- `src/egrf/v3/corpus_validator.py` - Implementation of the corpus validator
- `tests/egrf/v3/test_corpus_validator.py` - Tests for the corpus validator
- `validate_corpus.py` - Script to validate the corpus examples

## Installation

1. Extract the zip file in your Arisbe repository root:
   ```bash
   unzip egrf_v3_corpus_implementation.zip
   ```

2. Run the tests to verify the implementation:
   ```bash
   PYTHONPATH=/path/to/arisbe python -m unittest tests/egrf/v3/test_corpus_validator.py
   ```

3. Validate the corpus examples:
   ```bash
   PYTHONPATH=/path/to/arisbe ./validate_corpus.py
   ```

## Current Status

The minimal viable corpus currently includes:
- Peirce's man-mortal example (CP 4.394)
- Canonical implication example

Additional examples will be added as part of the full corpus implementation.

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

## Next Steps

1. Complete the minimal viable corpus with all 20 examples
2. Implement the EG-HG to EGRF v3.0 converter
3. Validate the converter with the corpus examples
4. Create comprehensive documentation and examples

