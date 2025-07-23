#!/usr/bin/env python3
"""
EGRF v3.0 EG-HG to EGRF Converter Demonstration
"""

import json
import os
from pathlib import Path
from src.egrf.v3.converter.eg_hg_to_egrf import (
    EgHgToEgrfConverter, convert_eg_hg_to_egrf, parse_eg_hg_content
)

def main():
    """Run the demonstration."""
    print("\nEGRF v3.0 EG-HG to EGRF Converter Demonstration")
    print("=" * 50)
    
    # Example 1: Convert a simple EG-HG graph
    print("\nExample 1: Convert a simple EG-HG graph")
    print("-" * 50)
    
    simple_eg_hg = {
        "id": "simple_graph",
        "description": "Simple graph with one cut",
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
                },
                {
                    "id": "p2",
                    "label": "Q",
                    "arity": 0,
                    "context": "c1"
                }
            ]
        }
    }
    
    converter = EgHgToEgrfConverter()
    egrf_data = converter.convert(simple_eg_hg)
    
    print(f"Input: EG-HG graph with {len(simple_eg_hg['graph']['contexts'])} contexts and {len(simple_eg_hg['graph']['predicates'])} predicates")
    print(f"Output: EGRF v3.0 with {len(egrf_data['elements'])} elements and {len(egrf_data['layout_constraints'])} layout constraints")
    
    # Save the result
    output_path = "simple_graph.egrf"
    with open(output_path, "w") as f:
        json.dump(egrf_data, f, indent=2)
    
    print(f"Saved to {output_path}")
    
    # Example 2: Convert a complex EG-HG graph with double-cut implication
    print("\nExample 2: Convert a complex EG-HG graph with double-cut implication")
    print("-" * 50)
    
    implication_eg_hg = {
        "id": "implication_graph",
        "description": "If Socrates is a person, then Socrates is mortal",
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
                },
                {
                    "id": "c2",
                    "type": "cut",
                    "parent": "c1",
                    "polarity": "negative"
                }
            ],
            "predicates": [
                {
                    "id": "p1",
                    "label": "Person",
                    "arity": 1,
                    "context": "c1"
                },
                {
                    "id": "p2",
                    "label": "Mortal",
                    "arity": 1,
                    "context": "c2"
                }
            ],
            "entities": [
                {
                    "id": "e1",
                    "label": "Socrates1",
                    "type": "variable"
                },
                {
                    "id": "e2",
                    "label": "Socrates2",
                    "type": "variable"
                }
            ],
            "connections": [
                {
                    "predicate": "p1",
                    "entities": ["e1"],
                    "roles": ["arg1"]
                },
                {
                    "predicate": "p2",
                    "entities": ["e2"],
                    "roles": ["arg1"]
                },
                {
                    "entity1": "e1",
                    "entity2": "e2",
                    "type": "identity"
                }
            ]
        }
    }
    
    egrf_data = converter.convert(implication_eg_hg)
    
    print(f"Input: EG-HG graph with {len(implication_eg_hg['graph']['contexts'])} contexts, {len(implication_eg_hg['graph']['predicates'])} predicates, and {len(implication_eg_hg['graph']['entities'])} entities")
    print(f"Output: EGRF v3.0 with {len(egrf_data['elements'])} elements and {len(egrf_data['layout_constraints'])} layout constraints")
    
    # Save the result
    output_path = "implication_graph.egrf"
    with open(output_path, "w") as f:
        json.dump(egrf_data, f, indent=2)
    
    print(f"Saved to {output_path}")
    
    # Example 3: Parse EG-HG content from file
    print("\nExample 3: Parse EG-HG content from file")
    print("-" * 50)
    
    # Create a sample EG-HG file
    eg_hg_content = """
# EG-HG representation
id: file_graph
description: Graph loaded from file

graph:
  # Contexts
  contexts:
    - id: c0
      type: sheet
      parent: null
      polarity: positive
    - id: c1
      type: cut
      parent: c0
      polarity: negative
  
  # Predicates
  predicates:
    - id: p1
      label: P
      arity: 0
      context: c0
    - id: p2
      label: Q
      arity: 0
      context: c1
"""
    
    # Save the content to a file
    file_path = "sample.eg-hg"
    with open(file_path, "w") as f:
        f.write(eg_hg_content)
    
    # Parse the file
    with open(file_path, "r") as f:
        content = f.read()
    
    eg_hg_data = parse_eg_hg_content(content)
    egrf_data = convert_eg_hg_to_egrf(eg_hg_data)
    
    print(f"Input: EG-HG file with {len(eg_hg_data['graph']['contexts'])} contexts")
    predicates = eg_hg_data['graph'].get('predicates', [])
    print(f"Output: EGRF v3.0 with {len(egrf_data['elements'])} elements and {len(egrf_data['layout_constraints'])} layout constraints")
    
    # Save the result
    output_path = "file_graph.egrf"
    with open(output_path, "w") as f:
        json.dump(egrf_data, f, indent=2)
    
    print(f"Saved to {output_path}")
    
    print("\nDemonstration complete!")
    print("\nKey features demonstrated:")
    print("  1. EG-HG to EGRF v3.0 conversion")
    print("  2. Proper double-cut implication structure")
    print("  3. Entity and connection handling")
    print("  4. Parsing EG-HG content from files")
    print("  5. Logical containment hierarchy")


if __name__ == "__main__":
    main()

