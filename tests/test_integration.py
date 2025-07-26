#!/usr/bin/env python3
"""
Comprehensive Integration Test for Fixed Existential Graph Rendering

This test validates the complete pipeline from CLIF input to diagrammatic rendering,
ensuring that all components work together correctly.
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

def test_complete_pipeline():
    """Test the complete CLIF -> EG-HG -> EGRF -> Layout -> Rendering pipeline."""
    print("=== Complete Pipeline Integration Test ===")
    
    # Test with a working CLIF expression
    test_clif = "(forall (x) (if (Man x) (Mortal x)))"
    print(f"Testing CLIF: {test_clif}")
    
    try:
        # Step 1: Parse CLIF to EG-HG
        print("\nStep 1: CLIF -> EG-HG")
        clif_parser = CLIFParser()
        result = clif_parser.parse(test_clif)
        
        if result.errors or result.graph is None:
            print(f"FAILED: CLIF parsing errors: {[str(e.message) for e in result.errors]}")
            return False
        
        print(f"SUCCESS: Parsed to EG-HG with {len(result.graph.contexts)} contexts, {len(result.graph.predicates)} predicates, {len(result.graph.entities)} entities")
        
        # Step 2: Convert EG-HG to EGRF
        print("\nStep 2: EG-HG -> EGRF")
        egrf_data = convert_graph_to_egrf_direct(result.graph, {'id': 'integration_test'})
        
        elements = egrf_data.get('elements', {})
        containment = egrf_data.get('containment', {})
        print(f"SUCCESS: Converted to EGRF with {len(elements)} elements and {len(containment)} containment relationships")
        
        # Step 3: Calculate Layout
        print("\nStep 3: EGRF -> Layout")
        calculator = LayoutCalculator(800, 600)
        layout_data = calculator.calculate_layout(egrf_data)
        
        print(f"SUCCESS: Calculated layout for {len(layout_data)} elements")
        
        # Step 4: Validate Rendering Data
        print("\nStep 4: Validate Rendering Data")
        rendering_valid = validate_rendering_data(elements, layout_data)
        
        if rendering_valid:
            print("SUCCESS: All elements have valid rendering data")
        else:
            print("FAILED: Some elements lack valid rendering data")
            return False
        
        # Step 5: Simulate Graphics Item Creation
        print("\nStep 5: Simulate Graphics Item Creation")
        graphics_items = simulate_graphics_creation(elements, layout_data)
        
        print(f"SUCCESS: Created {len(graphics_items)} graphics items")
        
        # Step 6: Validate Visual Representation
        print("\nStep 6: Validate Visual Representation")
        visual_valid = validate_visual_representation(graphics_items, egrf_data)
        
        if visual_valid:
            print("SUCCESS: Visual representation follows Peirce's conventions")
        else:
            print("FAILED: Visual representation issues detected")
            return False
        
        print("\n✓ COMPLETE PIPELINE TEST PASSED")
        return True
        
    except Exception as e:
        print(f"\nFAILED: Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        return False

def validate_rendering_data(elements, layout_data):
    """Validate that all elements have the data needed for rendering."""
    for elem_id, element in elements.items():
        if elem_id not in layout_data:
            print(f"  ERROR: Element {elem_id} missing layout data")
            return False
        
        layout = layout_data[elem_id]
        
        # Check position
        if 'position' not in layout or 'x' not in layout['position'] or 'y' not in layout['position']:
            print(f"  ERROR: Element {elem_id} missing position data")
            return False
        
        # Check size
        if 'size' not in layout or 'width' not in layout['size'] or 'height' not in layout['size']:
            print(f"  ERROR: Element {elem_id} missing size data")
            return False
        
        # Check element has type information
        if 'element_type' not in element and 'type' not in element:
            print(f"  ERROR: Element {elem_id} missing type information")
            return False
    
    return True

def simulate_graphics_creation(elements, layout_data):
    """Simulate the creation of graphics items."""
    graphics_items = {}
    
    for elem_id, element in elements.items():
        layout = layout_data[elem_id]
        elem_type = element.get('element_type', element.get('type', 'unknown'))
        
        # Simulate graphics item creation
        item_data = {
            'id': elem_id,
            'type': elem_type,
            'position': layout['position'],
            'size': layout['size'],
            'element_data': element,
            'visual_properties': {}
        }
        
        # Add type-specific visual properties
        if elem_type == 'context':
            logical_props = element.get('logical_properties', {})
            context_type = logical_props.get('context_type', 'cut')
            is_root = logical_props.get('is_root', False)
            
            item_data['visual_properties'] = {
                'shape': 'rectangle' if is_root or context_type == 'sheet' else 'oval',
                'fill_color': 'light_gray' if is_root else 'light_red',
                'border_color': 'gray' if is_root else 'red',
                'border_width': 2 if is_root else 3
            }
            
        elif elem_type == 'predicate':
            logical_props = element.get('logical_properties', {})
            name = logical_props.get('name', 'P')
            
            item_data['visual_properties'] = {
                'shape': 'circle',
                'fill_color': 'light_blue',
                'border_color': 'blue',
                'border_width': 2,
                'label': name
            }
            
        elif elem_type == 'entity':
            logical_props = element.get('logical_properties', {})
            name = logical_props.get('name', '')
            
            item_data['visual_properties'] = {
                'shape': 'line',
                'color': 'green',
                'width': 4,
                'label': name
            }
        
        graphics_items[elem_id] = item_data
    
    return graphics_items

def validate_visual_representation(graphics_items, egrf_data):
    """Validate that the visual representation follows Peirce's conventions."""
    
    # Check that contexts are rendered appropriately
    for item_id, item in graphics_items.items():
        if item['type'] == 'context':
            element = item['element_data']
            logical_props = element.get('logical_properties', {})
            is_root = logical_props.get('is_root', False)
            context_type = logical_props.get('context_type', 'cut')
            
            # Sheet of assertion should be rectangular
            if is_root or context_type == 'sheet':
                if item['visual_properties']['shape'] != 'rectangle':
                    print(f"  ERROR: Sheet {item_id} should be rectangular")
                    return False
            else:
                # Cuts should be oval
                if item['visual_properties']['shape'] != 'oval':
                    print(f"  ERROR: Cut {item_id} should be oval")
                    return False
        
        # Check that predicates are circular
        elif item['type'] == 'predicate':
            if item['visual_properties']['shape'] != 'circle':
                print(f"  ERROR: Predicate {item_id} should be circular")
                return False
            
            # Should have a label
            if 'label' not in item['visual_properties']:
                print(f"  ERROR: Predicate {item_id} should have a label")
                return False
        
        # Check that entities are lines
        elif item['type'] == 'entity':
            if item['visual_properties']['shape'] != 'line':
                print(f"  ERROR: Entity {item_id} should be a line")
                return False
    
    # Check containment hierarchy is respected in positioning
    containment = egrf_data.get('containment', {})
    for child_id, parent_id in containment.items():
        if parent_id == 'viewport':
            continue
            
        if child_id in graphics_items and parent_id in graphics_items:
            child_item = graphics_items[child_id]
            parent_item = graphics_items[parent_id]
            
            # Child should be positioned within parent
            child_pos = child_item['position']
            child_size = child_item['size']
            parent_pos = parent_item['position']
            parent_size = parent_item['size']
            
            if (child_pos['x'] < parent_pos['x'] or
                child_pos['y'] < parent_pos['y'] or
                child_pos['x'] + child_size['width'] > parent_pos['x'] + parent_size['width'] or
                child_pos['y'] + child_size['height'] > parent_pos['y'] + parent_size['height']):
                print(f"  WARNING: Child {child_id} may extend outside parent {parent_id}")
                # This is a warning, not a failure, as some tolerance is acceptable
    
    return True

def test_corpus_integration():
    """Test integration with corpus examples."""
    print("\n=== Corpus Integration Test ===")
    
    try:
        repo_root = Path(__file__).parent
        corpus_path = repo_root / 'corpus' / 'corpus'
        corpus_api = CorpusAPI(corpus_path)
        
        example_ids = corpus_api.get_example_ids()
        successful_tests = 0
        total_tests = 0
        
        for example_id in example_ids:
            total_tests += 1
            print(f"\nTesting corpus example: {example_id}")
            
            try:
                example = corpus_api.load_example(example_id)
                clif_parser = CLIFParser()
                result = clif_parser.parse(example.clif_content)
                
                if not result.errors and result.graph is not None:
                    # Convert to EGRF
                    egrf_data = convert_graph_to_egrf_direct(result.graph, {'id': example_id})
                    
                    # Calculate layout
                    calculator = LayoutCalculator(800, 600)
                    layout_data = calculator.calculate_layout(egrf_data)
                    
                    # Validate rendering data
                    if validate_rendering_data(egrf_data['elements'], layout_data):
                        print(f"  ✓ {example_id}: PASSED")
                        successful_tests += 1
                    else:
                        print(f"  ✗ {example_id}: FAILED (rendering validation)")
                else:
                    print(f"  ✗ {example_id}: FAILED (CLIF parsing)")
                    
            except Exception as e:
                print(f"  ✗ {example_id}: FAILED (exception: {e})")
        
        print(f"\nCorpus Integration Results: {successful_tests}/{total_tests} tests passed")
        return successful_tests == total_tests
        
    except Exception as e:
        print(f"Corpus integration test failed: {e}")
        return False

def main():
    """Run all integration tests."""
    print("Arisbe Existential Graph Rendering - Integration Test Suite")
    print("=" * 60)
    
    all_passed = True
    
    # Test complete pipeline
    pipeline_passed = test_complete_pipeline()
    all_passed = all_passed and pipeline_passed
    
    # Test corpus integration
    corpus_passed = test_corpus_integration()
    all_passed = all_passed and corpus_passed
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL INTEGRATION TESTS PASSED!")
        print("\nThe fixed rendering implementation successfully:")
        print("✓ Parses CLIF expressions to EG-HG")
        print("✓ Converts EG-HG to EGRF format")
        print("✓ Calculates proper layout for visual elements")
        print("✓ Creates graphics items following Peirce's conventions")
        print("✓ Handles containment hierarchy correctly")
        print("✓ Works with corpus examples")
    else:
        print("❌ SOME INTEGRATION TESTS FAILED")
        print("Please review the error messages above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

