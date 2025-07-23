# EGRF v3.0 Corpus Guide

## Introduction

The EGRF v3.0 Corpus is a collection of Existential Graph examples from authoritative sources, including Peirce's original works, scholarly interpretations, and canonical forms. This guide provides a comprehensive overview of the corpus, its structure, and how to use it for testing and validation.

## Corpus Structure

### Directory Structure

The corpus is organized into the following directory structure:

```
corpus/
├── corpus_index.json
├── peirce/
│   ├── peirce_cp_4_394_man_mortal.json
│   ├── peirce_cp_4_394_man_mortal.clif
│   ├── peirce_cp_4_394_man_mortal.eg-hg
│   └── peirce_cp_4_394_man_mortal.egrf
├── scholars/
│   ├── roberts_1973_p57_disjunction.json
│   ├── roberts_1973_p57_disjunction.clif
│   ├── roberts_1973_p57_disjunction.eg-hg
│   └── roberts_1973_p57_disjunction.egrf
├── canonical/
│   ├── canonical_implication.json
│   ├── canonical_implication.clif
│   ├── canonical_implication.eg-hg
│   └── canonical_implication.egrf
└── epg/
    └── ...
```

### Categories

The corpus is divided into four categories:

1. **Peirce**: Examples from Peirce's original works, primarily the Collected Papers.
2. **Scholars**: Examples from scholarly interpretations of Peirce's work, including Roberts, Sowa, and Dau.
3. **Canonical**: Standard logical forms and patterns in Existential Graphs.
4. **EPG**: Examples specifically designed for the Endoporeutic Game.

### File Types

Each example in the corpus consists of four files:

1. **JSON Metadata** (`.json`): Contains metadata about the example, including source, description, and logical pattern.
2. **CLIF Representation** (`.clif`): The example represented in Common Logic Interchange Format.
3. **EG-HG Representation** (`.eg-hg`): The example represented in Existential Graph Hypergraph format.
4. **EGRF Representation** (`.egrf`): The example represented in Existential Graph Rendering Format v3.0.

### Corpus Index

The `corpus_index.json` file serves as an index for all examples in the corpus:

```json
{
  "peirce": [
    {
      "id": "peirce_cp_4_394_man_mortal",
      "title": "Man-Mortal Implication",
      "source": "Collected Papers 4.394",
      "pattern": "implication",
      "description": "If a man exists, then he is mortal"
    }
  ],
  "scholars": [
    {
      "id": "roberts_1973_p57_disjunction",
      "title": "Disjunction Example",
      "source": "Roberts (1973), p. 57",
      "pattern": "disjunction",
      "description": "P or Q represented as ¬(¬P ∧ ¬Q)"
    },
    {
      "id": "sowa_2011_p356_quantification",
      "title": "Existential Quantification",
      "source": "Sowa (2011), p. 356",
      "pattern": "existential_quantification",
      "description": "There exists an x such that P(x)"
    },
    {
      "id": "dau_2006_p112_ligature",
      "title": "Ligature Example",
      "source": "Dau (2006), p. 112",
      "pattern": "ligature",
      "description": "Ligature crossing cut boundaries"
    }
  ],
  "canonical": [
    {
      "id": "canonical_implication",
      "title": "Canonical Implication",
      "source": "Canonical Form",
      "pattern": "implication",
      "description": "Standard form of implication with double cut"
    }
  ],
  "epg": []
}
```

## Example Formats

### JSON Metadata

The JSON metadata file contains information about the example:

```json
{
  "id": "peirce_cp_4_394_man_mortal",
  "title": "Man-Mortal Implication",
  "source": {
    "author": "Charles Sanders Peirce",
    "work": "Collected Papers",
    "volume": 4,
    "section": "4.394",
    "year": 1903
  },
  "pattern": "implication",
  "description": "If a man exists, then he is mortal",
  "notes": "This is a classic example of implication in Existential Graphs, showing the double-cut structure.",
  "logical_form": "Man(x) → Mortal(x)",
  "test_purpose": "Validates proper double-cut implication structure"
}
```

### CLIF Representation

The CLIF representation file contains the example in Common Logic Interchange Format:

```
(forall (x) (if (Man x) (Mortal x)))
```

### EG-HG Representation

The EG-HG representation file contains the example in Existential Graph Hypergraph format:

```
id: peirce_cp_4_394_man_mortal
description: If a man exists, then he is mortal
graph:
  contexts:
    - id: sheet
      type: sheet
      parent: null
    - id: outer_cut
      type: cut
      parent: sheet
    - id: inner_cut
      type: cut
      parent: outer_cut
  predicates:
    - id: man
      label: Man
      arity: 1
      context: outer_cut
    - id: mortal
      label: Mortal
      arity: 1
      context: inner_cut
  entities:
    - id: x1
      label: x
      type: variable
    - id: x2
      label: x
      type: variable
  connections:
    - predicate: man
      entities: [x1]
      roles: [arg1]
    - predicate: mortal
      entities: [x2]
      roles: [arg1]
    - entity1: x1
      entity2: x2
      type: identity
```

### EGRF Representation

The EGRF representation file contains the example in Existential Graph Rendering Format v3.0:

```json
{
  "metadata": {
    "version": "3.0.0",
    "format": "egrf",
    "id": "peirce_cp_4_394_man_mortal",
    "description": "If a man exists, then he is mortal"
  },
  "elements": {
    "sheet": {
      "element_type": "context",
      "logical_properties": {
        "context_type": "sheet_of_assertion",
        "container": "none",
        "is_root": true,
        "nesting_level": 0
      },
      "visual_properties": {
        "name": "Sheet of Assertion"
      }
    },
    "outer_cut": {
      "element_type": "context",
      "logical_properties": {
        "context_type": "cut",
        "container": "sheet",
        "is_root": false,
        "nesting_level": 1
      },
      "visual_properties": {
        "name": "Outer Cut"
      }
    },
    "inner_cut": {
      "element_type": "context",
      "logical_properties": {
        "context_type": "cut",
        "container": "outer_cut",
        "is_root": false,
        "nesting_level": 2
      },
      "visual_properties": {
        "name": "Inner Cut"
      }
    },
    "man_predicate": {
      "element_type": "predicate",
      "logical_properties": {
        "arity": 1,
        "container": "outer_cut"
      },
      "visual_properties": {
        "name": "Man"
      }
    },
    "mortal_predicate": {
      "element_type": "predicate",
      "logical_properties": {
        "arity": 1,
        "container": "inner_cut"
      },
      "visual_properties": {
        "name": "Mortal"
      }
    },
    "x1": {
      "element_type": "entity",
      "logical_properties": {
        "entity_type": "variable",
        "connected_predicates": ["man_predicate"]
      },
      "visual_properties": {
        "name": "x"
      }
    },
    "x2": {
      "element_type": "entity",
      "logical_properties": {
        "entity_type": "variable",
        "connected_predicates": ["mortal_predicate"]
      },
      "visual_properties": {
        "name": "x"
      }
    }
  },
  "containment": {
    "outer_cut": "sheet",
    "inner_cut": "outer_cut",
    "man_predicate": "outer_cut",
    "mortal_predicate": "inner_cut",
    "x1": "outer_cut",
    "x2": "inner_cut"
  },
  "connections": [
    {
      "entity_id": "x1",
      "predicate_id": "man_predicate",
      "role": "arg1"
    },
    {
      "entity_id": "x2",
      "predicate_id": "mortal_predicate",
      "role": "arg1"
    }
  ],
  "ligatures": [
    {
      "entity1_id": "x1",
      "entity2_id": "x2",
      "type": "identity"
    }
  ],
  "layout_constraints": [
    // Layout constraints omitted for brevity
  ]
}
```

## Corpus Examples

### Peirce Examples

#### Man-Mortal Implication (CP 4.394)

This example from Peirce's Collected Papers (4.394) demonstrates the classic implication "If a man exists, then he is mortal" using a double-cut structure.

- **Logical Form**: Man(x) → Mortal(x)
- **EG Structure**: Double-cut with Man predicate in outer cut and Mortal predicate in inner cut
- **Test Purpose**: Validates proper double-cut implication structure

### Scholar Examples

#### Roberts' Disjunction Example (1973, p. 57)

This example from Roberts' "The Existential Graphs of Charles S. Peirce" demonstrates how disjunction is represented in Existential Graphs.

- **Logical Form**: P ∨ Q
- **EG Structure**: ¬(¬P ∧ ¬Q)
- **Test Purpose**: Validates proper representation of disjunction

#### Sowa's Quantification Example (2011, p. 356)

This example from Sowa's "Peirce's Tutorial on Existential Graphs" demonstrates existential quantification.

- **Logical Form**: ∃x P(x)
- **EG Structure**: Line of identity with P predicate
- **Test Purpose**: Validates proper representation of existential quantification

#### Dau's Ligature Example (2006, p. 112)

This example from Dau's "Mathematical Logic with Diagrams" demonstrates ligatures crossing cut boundaries.

- **Logical Form**: ∃x (P(x) ∧ ¬Q(x))
- **EG Structure**: Line of identity connecting P predicate outside cut to Q predicate inside cut
- **Test Purpose**: Validates proper representation of ligatures crossing cut boundaries

### Canonical Examples

#### Canonical Implication

This example demonstrates the standard form of implication in Existential Graphs.

- **Logical Form**: P → Q
- **EG Structure**: Double-cut with P predicate in outer cut and Q predicate in inner cut
- **Test Purpose**: Validates proper double-cut implication structure

## Using the Corpus

### Loading the Corpus

To load the corpus in Python:

```python
import json
import os

def load_corpus_index(index_path):
    """Load the corpus index."""
    with open(index_path, "r") as f:
        return json.load(f)

def load_example(corpus_index, category, example_id):
    """Load a specific example from the corpus."""
    # Find the example in the index
    example_metadata = None
    for example in corpus_index.get(category, []):
        if example["id"] == example_id:
            example_metadata = example
            break
    
    if not example_metadata:
        raise ValueError(f"Example {example_id} not found in category {category}")
    
    # Determine paths
    corpus_dir = os.path.dirname(index_path)
    json_path = os.path.join(corpus_dir, category, f"{example_id}.json")
    clif_path = os.path.join(corpus_dir, category, f"{example_id}.clif")
    eg_hg_path = os.path.join(corpus_dir, category, f"{example_id}.eg-hg")
    egrf_path = os.path.join(corpus_dir, category, f"{example_id}.egrf")
    
    # Load files
    with open(json_path, "r") as f:
        metadata = json.load(f)
    
    with open(clif_path, "r") as f:
        clif = f.read()
    
    with open(eg_hg_path, "r") as f:
        eg_hg = f.read()
    
    with open(egrf_path, "r") as f:
        egrf = json.load(f)
    
    return {
        "metadata": metadata,
        "clif": clif,
        "eg_hg": eg_hg,
        "egrf": egrf
    }

# Usage
corpus_index = load_corpus_index("corpus/corpus_index.json")
example = load_example(corpus_index, "peirce", "peirce_cp_4_394_man_mortal")
```

### Validating EGRF v3.0

To validate an EGRF v3.0 document against the corpus:

```python
def validate_egrf_structure(egrf_data):
    """Validate the structure of an EGRF v3.0 document."""
    messages = []
    
    # Check metadata
    if "metadata" not in egrf_data:
        messages.append("Missing metadata section")
        return False, messages
    
    metadata = egrf_data["metadata"]
    if "version" not in metadata or metadata["version"] != "3.0.0":
        messages.append(f"Invalid version: {metadata.get('version', 'missing')}")
        return False, messages
    
    if "format" not in metadata or metadata["format"] != "egrf":
        messages.append(f"Invalid format: {metadata.get('format', 'missing')}")
        return False, messages
    
    # Check elements
    if "elements" not in egrf_data:
        messages.append("Missing elements section")
        return False, messages
    
    elements = egrf_data["elements"]
    if not elements:
        messages.append("Empty elements section")
        return False, messages
    
    # Check containment
    if "containment" not in egrf_data:
        messages.append("Missing containment section")
        return False, messages
    
    # Check each element
    for element_id, element in elements.items():
        if "element_type" not in element:
            messages.append(f"Element {element_id} missing element_type")
            return False, messages
        
        element_type = element["element_type"]
        if element_type not in ["context", "predicate", "entity"]:
            messages.append(f"Invalid element_type for {element_id}: {element_type}")
            return False, messages
        
        if "logical_properties" not in element:
            messages.append(f"Element {element_id} missing logical_properties")
            return False, messages
        
        logical_properties = element["logical_properties"]
        
        if element_type == "context":
            if "context_type" not in logical_properties:
                messages.append(f"Context {element_id} missing context_type")
                return False, messages
            
            context_type = logical_properties["context_type"]
            if context_type not in ["sheet", "cut", "sheet_of_assertion"]:
                messages.append(f"Invalid context_type for {element_id}: {context_type}")
                return False, messages
        
        elif element_type == "predicate":
            if "arity" not in logical_properties:
                messages.append(f"Predicate {element_id} missing arity")
                return False, messages
        
        elif element_type == "entity":
            if "entity_type" not in logical_properties:
                messages.append(f"Entity {element_id} missing entity_type")
                return False, messages
            
            entity_type = logical_properties["entity_type"]
            if entity_type not in ["constant", "variable"]:
                messages.append(f"Invalid entity_type for {element_id}: {entity_type}")
                return False, messages
    
    return True, messages
```

### Converting EG-HG to EGRF

To convert an EG-HG document to EGRF v3.0:

```python
from src.egrf.v3.converter.eg_hg_to_egrf import EgHgToEgrfConverter, parse_eg_hg_content

def convert_eg_hg_to_egrf(eg_hg_content):
    """Convert EG-HG content to EGRF v3.0."""
    # Parse EG-HG content
    eg_hg_data = parse_eg_hg_content(eg_hg_content)
    
    # Convert to EGRF v3.0
    converter = EgHgToEgrfConverter()
    egrf_data = converter.convert(eg_hg_data)
    
    return egrf_data

# Usage
with open("corpus/peirce/peirce_cp_4_394_man_mortal.eg-hg", "r") as f:
    eg_hg_content = f.read()

egrf_data = convert_eg_hg_to_egrf(eg_hg_content)
```

### Validating Converter with Corpus

To validate the EG-HG to EGRF converter against the corpus:

```python
def validate_converter_with_corpus(corpus_dir, corpus_index):
    """Validate the EG-HG to EGRF converter against the corpus."""
    results = {}
    
    for category, examples in corpus_index.items():
        for example in examples:
            example_id = example["id"]
            
            try:
                # Load example files
                eg_hg_path = os.path.join(corpus_dir, category, f"{example_id}.eg-hg")
                expected_egrf_path = os.path.join(corpus_dir, category, f"{example_id}.egrf")
                generated_egrf_path = os.path.join(corpus_dir, category, f"{example_id}.generated.egrf")
                
                # Convert EG-HG to EGRF
                with open(eg_hg_path, "r") as f:
                    eg_hg_content = f.read()
                
                generated_egrf = convert_eg_hg_to_egrf(eg_hg_content)
                
                # Save generated EGRF
                with open(generated_egrf_path, "w") as f:
                    json.dump(generated_egrf, f, indent=2)
                
                # Load expected EGRF
                with open(expected_egrf_path, "r") as f:
                    expected_egrf = json.load(f)
                
                # Validate generated EGRF
                is_valid, messages = validate_egrf_structure(generated_egrf)
                
                if not is_valid:
                    results[example_id] = {
                        "status": "error",
                        "message": "Generated EGRF structure is invalid",
                        "details": messages
                    }
                    continue
                
                # Compare element counts
                expected_count = len(expected_egrf["elements"])
                generated_count = len(generated_egrf["elements"])
                
                if expected_count != generated_count:
                    results[example_id] = {
                        "status": "error",
                        "message": f"Element count mismatch - generated: {generated_count}, expected: {expected_count}"
                    }
                    continue
                
                # If we get here, the conversion is valid
                results[example_id] = {
                    "status": "success",
                    "message": "Conversion successful"
                }
            
            except Exception as e:
                results[example_id] = {
                    "status": "error",
                    "message": f"Error - {str(e)}"
                }
    
    return results
```

## Extending the Corpus

### Adding New Examples

To add a new example to the corpus:

1. Create the JSON metadata file.
2. Create the CLIF representation file.
3. Create the EG-HG representation file.
4. Create the EGRF representation file.
5. Update the corpus index.

```python
def add_example_to_corpus(corpus_dir, category, example_id, metadata, clif, eg_hg, egrf):
    """Add a new example to the corpus."""
    # Create category directory if it doesn't exist
    category_dir = os.path.join(corpus_dir, category)
    os.makedirs(category_dir, exist_ok=True)
    
    # Write files
    with open(os.path.join(category_dir, f"{example_id}.json"), "w") as f:
        json.dump(metadata, f, indent=2)
    
    with open(os.path.join(category_dir, f"{example_id}.clif"), "w") as f:
        f.write(clif)
    
    with open(os.path.join(category_dir, f"{example_id}.eg-hg"), "w") as f:
        f.write(eg_hg)
    
    with open(os.path.join(category_dir, f"{example_id}.egrf"), "w") as f:
        json.dump(egrf, f, indent=2)
    
    # Update corpus index
    index_path = os.path.join(corpus_dir, "corpus_index.json")
    with open(index_path, "r") as f:
        corpus_index = json.load(f)
    
    if category not in corpus_index:
        corpus_index[category] = []
    
    # Add example to index
    corpus_index[category].append({
        "id": example_id,
        "title": metadata["title"],
        "source": metadata["source"]["work"] if "source" in metadata and "work" in metadata["source"] else "Unknown",
        "pattern": metadata["pattern"],
        "description": metadata["description"]
    })
    
    # Write updated index
    with open(index_path, "w") as f:
        json.dump(corpus_index, f, indent=2)
```

### Creating a Minimal Viable Corpus

To create a minimal viable corpus for testing:

1. Include at least one example from each category.
2. Ensure each example tests a different logical pattern.
3. Include examples with varying complexity.
4. Include examples with different types of elements (contexts, predicates, entities, ligatures).

## Conclusion

The EGRF v3.0 Corpus provides a comprehensive collection of Existential Graph examples for testing and validation. By following the guidelines in this corpus guide, you can effectively use and extend the corpus to ensure the correctness of your EGRF v3.0 implementation.

