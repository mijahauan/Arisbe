# EGRF v3.0 EG-HG to EGRF Converter

This package contains the implementation of the EG-HG to EGRF v3.0 converter, which transforms Existential Graph Hypergraph (EG-HG) data into the Existential Graph Rendering Format (EGRF) v3.0 with logical containment architecture.

## Contents

- `src/egrf/v3/converter/` - Core converter implementation
  - `__init__.py` - Module initialization
  - `eg_hg_to_egrf.py` - Main converter implementation
- `eg_hg_to_egrf_demo.py` - Demonstration script
- Example output files:
  - `simple_graph.egrf` - Simple graph with one cut
  - `implication_graph.egrf` - Double-cut implication example
  - `file_graph.egrf` - Example parsed from file

## Key Features

1. **EG-HG to EGRF v3.0 Conversion**
   - Transforms logical structure to rendering format
   - Preserves containment relationships
   - Generates layout constraints

2. **Proper Double-Cut Implication Structure**
   - Correctly implements Peirce's double-cut implication
   - Maintains proper nesting levels
   - Preserves logical semantics

3. **Entity and Connection Handling**
   - Supports predicate-entity connections
   - Handles entity-entity ligatures
   - Maintains proper containment for entities

4. **Parsing EG-HG Content from Files**
   - Parses YAML-like EG-HG format
   - Supports comments and nested structures
   - Handles complex graph definitions

5. **Logical Containment Hierarchy**
   - Platform-independent layout
   - Auto-sizing containers
   - Constraint-based positioning

## Usage

### Basic Usage

```python
from src.egrf.v3.converter.eg_hg_to_egrf import convert_eg_hg_to_egrf

# Create or load EG-HG data
eg_hg_data = {
    "id": "example_graph",
    "description": "Example graph",
    "graph": {
        "contexts": [
            {
                "id": "c0",
                "type": "sheet",
                "parent": None,
                "polarity": "positive"
            },
            {
                "id": "c1",
                "type": "cut",
                "parent": "c0",
                "polarity": "negative"
            }
        ],
        "predicates": [
            {
                "id": "p1",
                "label": "P",
                "arity": 0,
                "context": "c0"
            }
        ]
    }
}

# Convert to EGRF v3.0
egrf_data = convert_eg_hg_to_egrf(eg_hg_data)

# Use the EGRF data
print(f"Generated {len(egrf_data['elements'])} elements")
```

### Parsing from File

```python
from src.egrf.v3.converter.eg_hg_to_egrf import parse_eg_hg_content, convert_eg_hg_to_egrf

# Read EG-HG content from file
with open("example.eg-hg", "r") as f:
    content = f.read()

# Parse the content
eg_hg_data = parse_eg_hg_content(content)

# Convert to EGRF v3.0
egrf_data = convert_eg_hg_to_egrf(eg_hg_data)
```

### Command-Line Usage

```bash
python src/egrf/v3/converter/eg_hg_to_egrf.py input.eg-hg output.egrf
```

## Installation

1. Extract the zip file in your Arisbe repository root
2. Ensure the `src/egrf/v3/converter` directory is in your Python path
3. Run the demo script to verify the installation:
   ```bash
   python eg_hg_to_egrf_demo.py
   ```

## Next Steps

1. **Validate with Corpus Examples**
   - Test against scholarly examples
   - Verify logical correctness
   - Ensure proper visualization

2. **Integrate with GUI**
   - Connect to rendering engine
   - Implement user interaction
   - Support editing operations

3. **Extend for EPG**
   - Support game state representation
   - Implement transformation rules
   - Enable move validation

