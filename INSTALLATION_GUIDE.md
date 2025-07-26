# Enhanced Corpus Selector Installation Guide

## Overview

This package enhances the Arisbe Existential Graph Editor with an improved corpus selector featuring:

- **Categorized browsing** (Alpha, Beta, Gamma, etc.)
- **Complexity level filtering** (Beginner, Intermediate, Advanced)
- **Enhanced metadata display** with descriptions and sources
- **Improved user experience** with organized dropdown menus

## Files Included

### New Files
- `src/gui/corpus_manager.py` - Core corpus management system
- `test_enhanced_corpus_selector.py` - Comprehensive test suite

### Updated Files
- `src/gui/graph_editor.py` - Enhanced with new corpus selector UI

## Installation Instructions

1. **Extract** this package from your Arisbe project root directory:
   ```bash
   cd /path/to/your/arisbe/project
   unzip arisbe_enhanced_corpus_selector.zip
   ```

2. **Backup** your existing graph editor (optional but recommended):
   ```bash
   cp src/gui/graph_editor.py src/gui/graph_editor.py.backup
   ```

3. **Install** the enhanced files:
   - The zip extraction will automatically place files in the correct locations
   - `src/gui/corpus_manager.py` (new)
   - `src/gui/graph_editor.py` (updated)

4. **Test** the installation:
   ```bash
   python3 test_enhanced_corpus_selector.py
   ```

## New Features

### 1. Category Filtering
- **Alpha**: Basic propositional logic examples
- **Beta**: Predicate logic with quantification
- **Gamma**: Modal and higher-order logic
- **Canonical**: Standard reference examples
- **Peirce**: Primary source examples from Peirce's writings
- **Scholars**: Modern scholarly interpretations

### 2. Complexity Level Filtering
- **Beginner**: Simple, introductory examples
- **Intermediate**: Standard logical patterns
- **Advanced**: Complex nested structures
- **Expert**: Specialized applications

### 3. Enhanced Display
- **Rich descriptions** instead of just filenames
- **Source attribution** with academic references
- **Complexity indicators** in dropdown
- **Category separators** for better organization

### 4. Improved User Experience
- **Dual filtering** by category and complexity
- **Smart defaults** (loads beginner examples first)
- **Better error handling** for missing CLIF statements
- **Comprehensive validation** with helpful warnings

## Usage

### Basic Usage
1. **Start Arisbe** as usual
2. **Use the Category dropdown** to filter by logical system (Alpha, Beta, etc.)
3. **Use the Level dropdown** to filter by complexity
4. **Select an example** from the enhanced dropdown
5. **Click "Load Example"** to render the graph

### Advanced Features
- **All Categories/All Levels**: Show all available examples
- **Category separators**: Visual dividers in the dropdown
- **Complexity indicators**: Examples show their difficulty level
- **Rich tooltips**: Hover for additional information (if implemented)

## Troubleshooting

### Common Issues

1. **"No examples found"**
   - Ensure the corpus directory exists: `corpus/corpus/`
   - Check that EGRF files are present in subdirectories
   - Run the test suite to validate corpus structure

2. **"No CLIF Available" warnings**
   - Some older corpus entries may not have CLIF statements
   - These are typically legacy examples that need updating
   - Use the validation test to identify which examples need attention

3. **Import errors**
   - Ensure you're running from the Arisbe project root
   - Check that all Python dependencies are installed
   - Verify the src/ directory is in your Python path

### Validation
Run the comprehensive test suite:
```bash
python3 test_enhanced_corpus_selector.py
```

This will:
- ✅ Test corpus manager functionality
- ✅ Validate filtering and categorization
- ✅ Test graph editor integration
- ✅ Report any issues found

## Technical Details

### Architecture
- **CorpusManager**: Handles discovery, categorization, and filtering
- **Enhanced GraphEditor**: Integrates corpus manager with improved UI
- **Backward Compatibility**: Falls back gracefully if corpus is unavailable

### Performance
- **Lazy loading**: Examples loaded only when needed
- **Efficient filtering**: In-memory operations for fast response
- **Caching**: Corpus discovery results cached for session

### Extensibility
- **Plugin-ready**: Easy to add new categories or complexity levels
- **Metadata-driven**: Rich information extracted from EGRF files
- **Search-enabled**: Built-in search functionality for future features

## Support

If you encounter issues:

1. **Run the test suite** to identify specific problems
2. **Check the console output** for detailed error messages
3. **Verify corpus structure** matches expected format
4. **Ensure all dependencies** are properly installed

## Future Enhancements

Planned improvements include:
- **Search functionality** in the UI
- **Favorite examples** bookmarking
- **Custom categories** for user-defined collections
- **Export/import** of corpus collections
- **Collaborative corpus** sharing features

---

**Version**: 1.0  
**Compatibility**: Arisbe Existential Graph Editor  
**Requirements**: PySide6, Python 3.8+

