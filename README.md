# Arisbe - Immutable Existential Graphs Implementation

A mathematically rigorous, completely immutable implementation of Existential Graphs based on Frithjof Dau's formalism.

## Installation

1. Unzip this package into your project root directory
2. Install dependencies: `pip install frozendict`

## Usage

### Command Line Interface

```bash
# Interactive mode
python src/egi_cli.py

# Direct transformation
python src/egi_cli.py --egif "(man *x) (human x)" --transform "^(man *x)^ (human x)"

# Load from file
python src/egi_cli.py --yaml example.yaml
```

### Python API

```python
# Add src to path if needed
import sys
sys.path.append('src')

from egif_parser import parse_egif
from egif_generator import generate_egif
from egi_transformations import apply_erasure

# Parse EGIF to immutable EGI
egi = parse_egif("(man *x) (human x)")

# Apply transformation (returns new EGI)
edge_id = next(iter(egi._edge_map.keys()))
new_egi = apply_erasure(egi, edge_id)

# Original is unchanged
assert len(egi.edges) == 2
assert len(new_egi.edges) == 1

# Generate EGIF from EGI
result = generate_egif(new_egi)
```

## Testing

```bash
# Run comprehensive tests
python tests/test_complete_pipeline.py
```

## Key Features

### ✅ **Complete Immutability**
- All data structures are immutable after creation
- Transformations return new EGI instances
- Original graphs are never modified
- Mathematical soundness guaranteed

### ✅ **Pure Functional Transformations**
- All 8 canonical transformation rules implemented as pure functions
- `transform(egi) -> new_egi` pattern throughout
- No side effects or mutations
- Clear separation between original and transformed graphs

### ✅ **Flexible Import System**
- CLI works when run directly: `python src/egi_cli.py`
- Modules work when imported: `from src.egif_parser import parse_egif`
- Tests work from project root: `python tests/test_complete_pipeline.py`

## File Structure

```
src/
├── egi_core.py              # Immutable core data structures
├── egif_parser.py           # EGIF parser (builds immutable EGI)
├── egif_generator.py        # EGI to EGIF generator
├── egi_transformations.py   # Pure transformation functions
└── egi_cli.py              # Command-line interface

tests/
└── test_complete_pipeline.py  # Comprehensive test suite
```

## CLI Commands

```
load (man *x) (human x)          # Load EGIF expression
show                             # Show current EGIF
transform ^(man *x)^ (human x)   # Apply transformation with markup
undo                             # Undo last transformation
yaml                             # Show EGI structure
help                             # Show help
exit                             # Exit application
```

## Markup Syntax

- `^(relation args)^` - Mark relation for erasure
- `^~[[^]]` - Mark double cut for removal

## Transformation Rules

1. **Erasure**: Remove elements from positive contexts
2. **Insertion**: Add elements to negative contexts
3. **Iteration**: Copy vertices to inner contexts
4. **De-iteration**: Remove vertex copies
5. **Double Cut Addition**: Add nested empty cuts
6. **Double Cut Removal**: Remove nested empty cuts
7. **Isolated Vertex Addition**: Add isolated vertices
8. **Isolated Vertex Removal**: Remove isolated vertices

## Dependencies

- Python 3.8+
- `frozendict` for immutable dictionaries

## Benefits of Immutable Design

- **Mathematical Clarity**: Transformations clearly return new instances
- **Thread Safety**: Immutable objects are inherently thread-safe
- **Debugging**: State changes are explicit and traceable
- **Performance**: Structural sharing minimizes copying
- **Correctness**: No hidden mutations or side effects

