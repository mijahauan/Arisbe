# Arisbe Corpus Expansion Installation

## Overview
This package contains 7 new Existential Graph examples for the Arisbe corpus, expanding from 5 to 17 total examples with comprehensive coverage of Alpha and Beta level patterns.

## Installation Instructions

### 1. Extract Package
Extract this zip file from your Arisbe project root directory:
```bash
cd /path/to/your/arisbe/project
unzip arisbe_corpus_expansion.zip
```

### 2. Verify Installation
The following files will be added:

**New Corpus Entries:**
- `corpus/corpus/alpha/simple_assertion_pear.egrf`
- `corpus/corpus/alpha/simple_negation_phoenix.egrf`
- `corpus/corpus/alpha/conjunction_pear_orange.egrf`
- `corpus/corpus/beta/thunder_lightning_implication.egrf`
- `corpus/corpus/beta/male_african_human.egrf`
- `corpus/corpus/beta/existential_with_negation.egrf`
- `corpus/corpus/beta/thunder_without_lightning.egrf`

**Documentation:**
- `corpus/corpus/README.md` (updated)
- `CORPUS_EXPANSION_SUMMARY.md`
- `corpus_research_findings.md`

**Testing:**
- `test_new_corpus_entries.py`

### 3. Test Installation
Run the validation test to ensure all new corpus entries work correctly:
```bash
python3 test_new_corpus_entries.py
```

Expected output: "🎉 All corpus entries are valid!"

### 4. Verify in Application
1. Start the Arisbe application
2. Check the corpus dropdown - you should now see 17 examples instead of 5
3. Try loading the new examples:
   - "Simple Assertion: A pear is ripe" (Alpha level)
   - "Universal Conditional: If it thunders, it lightens" (Beta level)
   - "Complex Identity: There is a male African human" (Beta level)

## What's New

### Alpha Level Examples (Beginner)
- **Simple Assertion**: Basic existential statements
- **Simple Negation**: Single cut usage
- **Basic Conjunction**: Multiple statements on sheet

### Beta Level Examples (Intermediate)  
- **Universal Conditional**: Double cut (scroll) patterns
- **Complex Identity**: Multiple predicates with ligatures
- **Existential with Negation**: Scope interactions
- **Conjunction with Negation**: Mixed assertions

### Sources
- Roberts (1973): "The Existential Graphs of Charles S. Peirce"
- Sowa (2011): "Existential Graphs and EGIF"
- Dau (2006): "Constants and Functions in Peirce's Existential Graphs"

## Troubleshooting

### If tests fail:
1. Ensure you're running from the Arisbe root directory
2. Check that the `src/` directory is accessible
3. Verify Python path includes Arisbe modules

### If examples don't appear:
1. Restart the Arisbe application
2. Check that corpus files are in correct directories
3. Verify EGRF format is valid

### For support:
- See `CORPUS_EXPANSION_SUMMARY.md` for detailed documentation
- Check `corpus_research_findings.md` for source analysis
- Review `corpus/corpus/README.md` for corpus structure

## Future Expansions
The corpus is designed for continued expansion with:
- Gamma level examples (modal logic, higher-order constructs)
- Constants and functions (from Dau's work)
- Endoporeutic game examples
- Additional primary source material

Enjoy the expanded corpus!

