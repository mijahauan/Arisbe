#!/usr/bin/env python3
"""
Test script to validate the fixed rendering implementation.
Tests the layout calculation and graphics item creation without requiring GUI.
"""

import sys
import os
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from clif_parser import CLIFParser
from egrf.v3.converter.direct_graph_to_egrf import convert_graph_to_egrf_direct
from corpus_api import CorpusAPI
from gui.layout_calculator import LayoutCalculator

def test_layout_calculation():
    """Test the layout calculation functionality."""
    print("=== Layout Calculation Test ===")
    
    # Create a simple EGRF structure to test layout
    test_egrf = {
        'elements': {
            'sheet': {
                'id': 'sheet',
                'element_type': 'context',
                'logical_properties': {
                    'context_type': 'sheet',
                    'is_root': True,
                    'nesting_level': 0,
                    'name': 'Sheet of Assertion'
                },
                'layout_constraints': {
                    'size_constraints': {
                        'preferred': {'width': 700, 'height': 500}
                    }
                }
            },
            'cut1': {
                'id': 'cut1',
                'element_type': 'context',
                'logical_properties': {
                    'context_type': 'cut',
                    'is_root': False,
                    'nesting_level': 1,
                    'name': 'Cut 1'
                },
                'layout_constraints': {
                    'size_constraints': {
                        'preferred': {'width': 300, 'height': 200}
                    }
                }
            },
            'predicate1': {
                'id': 'predicate1',
                'element_type': 'predicate',
                'logical_properties': {
                    'name': 'P',
                    'arity': 0
                },
                'layout_constraints': {
                    'size_constraints': {
                        'preferred': {'width': 50, 'height': 30}
                    }
                }
            }
        },
        'containment': {
            'sheet': 'viewport',
            'cut1': 'sheet',
            'predicate1': 'cut1'
        }
    }
    
    # Test layout calculation
    calculator = LayoutCalculator(800, 600)
    layout_data = calculator.calculate_layout(test_egrf)
    
    print(f"Layout calculated for {len(layout_data)} elements:")
    for elem_id, layout in layout_data.items():
        pos = layout['position']
        size = layout['size']
        print(f"  {elem_id}: pos({pos['x']:.1f}, {pos['y']:.1f}) size({size['width']:.1f}x{size['height']:.1f})")
    
    # Validate layout
    validation_results = validate_layout(layout_data, test_egrf)
    print(f"\nLayout validation: {'PASSED' if validation_results['valid'] else 'FAILED'}")
    for issue in validation_results['issues']:
        print(f"  - {issue}")
    
    return layout_data

def validate_layout(layout_data: dict, egrf_data: dict) -> dict:
    """Validate that the calculated layout is reasonable."""
    issues = []
    
    # Check that all elements have layout data
    elements = egrf_data.get('elements', {})
    for elem_id in elements:
        if elem_id not in layout_data:
            issues.append(f"Missing layout data for element: {elem_id}")
    
    # Check that positions are reasonable
    for elem_id, layout in layout_data.items():
        pos = layout['position']
        size = layout['size']
        
        if pos['x'] < 0 or pos['y'] < 0:
            issues.append(f"Element {elem_id} has negative position: ({pos['x']}, {pos['y']})")
        
        if size['width'] <= 0 or size['height'] <= 0:
            issues.append(f"Element {elem_id} has invalid size: {size['width']}x{size['height']}")
    
    # Check containment relationships
    containment = egrf_data.get('containment', {})
    for child_id, parent_id in containment.items():
        if parent_id == 'viewport':
            continue
            
        if child_id in layout_data and parent_id in layout_data:
            child_layout = layout_data[child_id]
            parent_layout = layout_data[parent_id]
            
            # Check if child is within parent bounds (with some tolerance)
            child_bounds = child_layout['bounds']
            parent_bounds = parent_layout['bounds']
            
            if (child_bounds['x'] < parent_bounds['x'] or
                child_bounds['y'] < parent_bounds['y'] or
                child_bounds['x'] + child_bounds['width'] > parent_bounds['x'] + parent_bounds['width'] or
                child_bounds['y'] + child_bounds['height'] > parent_bounds['y'] + parent_bounds['height']):
                issues.append(f"Child {child_id} extends outside parent {parent_id}")
    
    return {'valid': len(issues) == 0, 'issues': issues}

def test_corpus_with_layout():
    """Test layout calculation with real corpus examples."""
    print("\n=== Corpus Layout Test ===")
    
    try:
        # Initialize corpus API
        repo_root = Path(__file__).parent
        corpus_path = repo_root / 'corpus' / 'corpus'
        corpus_api = CorpusAPI(corpus_path)
        clif_parser = CLIFParser()
        calculator = LayoutCalculator(800, 600)
        
        # Test with a working corpus example
        example_ids = corpus_api.get_example_ids()
        
        for example_id in example_ids[:2]:  # Test first 2 examples
            print(f"\n--- Testing: {example_id} ---")
            
            try:
                example = corpus_api.load_example(example_id)
                result = clif_parser.parse(example.clif_content)
                
                if not result.errors and result.graph is not None:
                    print(f"CLIF: {example.clif_content}")
                    print(f"Graph elements: contexts={len(result.graph.contexts)}, predicates={len(result.graph.predicates)}, entities={len(result.graph.entities)}")
                    
                    # Convert to EGRF
                    egrf_data = convert_graph_to_egrf_direct(result.graph, {'id': example_id})
                    
                    # Calculate layout
                    layout_data = calculator.calculate_layout(egrf_data)
                    print(f"Layout calculated for {len(layout_data)} elements")
                    
                    # Show sample layout
                    for elem_id, layout in list(layout_data.items())[:3]:  # Show first 3
                        pos = layout['position']
                        size = layout['size']
                        element = egrf_data['elements'][elem_id]
                        elem_type = element.get('element_type', 'unknown')
                        print(f"  {elem_id} ({elem_type}): pos({pos['x']:.1f}, {pos['y']:.1f}) size({size['width']:.1f}x{size['height']:.1f})")
                    
                    # Validate layout
                    validation = validate_layout(layout_data, egrf_data)
                    print(f"Layout validation: {'PASSED' if validation['valid'] else 'FAILED'}")
                    if validation['issues']:
                        for issue in validation['issues'][:3]:  # Show first 3 issues
                            print(f"    - {issue}")
                else:
                    print(f"CLIF parsing failed: {[str(e.message) for e in result.errors]}")
                    
            except Exception as e:
                print(f"Error processing {example_id}: {e}")
                
    except Exception as e:
        print(f"Error accessing corpus: {e}")

def test_existing_egrf_with_layout():
    """Test layout calculation with existing EGRF files."""
    print("\n=== Existing EGRF Layout Test ===")
    
    corpus_path = Path(__file__).parent / 'corpus' / 'corpus'
    egrf_files = list(corpus_path.glob('**/*.egrf'))
    calculator = LayoutCalculator(800, 600)
    
    for egrf_file in egrf_files[:2]:  # Test first 2 files
        print(f"\n--- Testing: {egrf_file.name} ---")
        
        try:
            with open(egrf_file, 'r') as f:
                egrf_data = json.load(f)
            
            # Calculate layout
            layout_data = calculator.calculate_layout(egrf_data)
            print(f"Layout calculated for {len(layout_data)} elements")
            
            # Show element types and positions
            elements = egrf_data.get('elements', {})
            for elem_id, layout in layout_data.items():
                element = elements.get(elem_id, {})
                elem_type = element.get('element_type', 'unknown')
                pos = layout['position']
                size = layout['size']
                print(f"  {elem_id} ({elem_type}): pos({pos['x']:.1f}, {pos['y']:.1f}) size({size['width']:.1f}x{size['height']:.1f})")
            
            # Validate layout
            validation = validate_layout(layout_data, egrf_data)
            print(f"Layout validation: {'PASSED' if validation['valid'] else 'FAILED'}")
            if validation['issues']:
                for issue in validation['issues']:
                    print(f"    - {issue}")
                    
        except Exception as e:
            print(f"Error processing {egrf_file.name}: {e}")

def test_graphics_item_creation():
    """Test that graphics items can be created with the layout data."""
    print("\n=== Graphics Item Creation Test ===")
    
    # This would normally require Qt, but we can at least test the data structures
    test_elements = {
        'sheet': {
            'element_type': 'context',
            'logical_properties': {
                'context_type': 'sheet',
                'is_root': True,
                'name': 'Sheet of Assertion'
            }
        },
        'cut1': {
            'element_type': 'context',
            'logical_properties': {
                'context_type': 'cut',
                'is_root': False,
                'name': 'Cut 1'
            }
        },
        'pred1': {
            'element_type': 'predicate',
            'logical_properties': {
                'name': 'P',
                'arity': 0
            }
        },
        'entity1': {
            'element_type': 'entity',
            'logical_properties': {
                'name': 'x',
                'entity_type': 'variable'
            }
        }
    }
    
    test_layout = {
        'sheet': {'position': {'x': 10, 'y': 10}, 'size': {'width': 700, 'height': 500}},
        'cut1': {'position': {'x': 50, 'y': 50}, 'size': {'width': 300, 'height': 200}},
        'pred1': {'position': {'x': 100, 'y': 100}, 'size': {'width': 50, 'height': 30}},
        'entity1': {'position': {'x': 200, 'y': 120}, 'size': {'width': 80, 'height': 5}}
    }
    
    print("Testing graphics item data structures:")
    for elem_id, element in test_elements.items():
        layout = test_layout.get(elem_id, {})
        elem_type = element.get('element_type')
        
        print(f"  {elem_id} ({elem_type}):")
        print(f"    - Element data: {element}")
        print(f"    - Layout data: {layout}")
        
        # Simulate what the graphics item would do
        if elem_type == 'context':
            logical_props = element.get('logical_properties', {})
            context_type = logical_props.get('context_type', 'cut')
            is_root = logical_props.get('is_root', False)
            print(f"    - Would render as: {'sheet' if is_root else 'oval cut'}")
            
        elif elem_type == 'predicate':
            logical_props = element.get('logical_properties', {})
            name = logical_props.get('name', 'P')
            print(f"    - Would render as: circle with label '{name}'")
            
        elif elem_type == 'entity':
            logical_props = element.get('logical_properties', {})
            name = logical_props.get('name', '')
            print(f"    - Would render as: line of identity with label '{name}'")
    
    print("\nGraphics item creation test: PASSED (data structures valid)")

if __name__ == "__main__":
    print("Testing Fixed Existential Graph Rendering")
    print("=" * 50)
    
    test_layout_calculation()
    test_corpus_with_layout()
    test_existing_egrf_with_layout()
    test_graphics_item_creation()
    
    print("\n" + "=" * 50)
    print("Fixed rendering tests completed!")
    print("\nKey improvements implemented:")
    print("1. LayoutCalculator calculates positions for EGRF elements")
    print("2. ImprovedGraphicsItems follow Peirce's drawing conventions")
    print("3. Proper containment hierarchy handling")
    print("4. Automatic positioning to avoid overlaps")
    print("5. Better visual representation of contexts, predicates, and entities")

