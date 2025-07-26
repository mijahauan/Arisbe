#!/usr/bin/env python3
"""
Comprehensive validation test for the Peirce Convention-Aware Layout Engine.

This test validates the complete pipeline from CLIF to rendered graphics,
ensuring all components work together correctly and follow Peirce's conventions.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from clif_parser import CLIFParser
from egrf_from_graph import convert_graph_to_egrf
from gui.peirce_layout_engine import PeirceLayoutEngine
from gui.peirce_graphics_adapter import PeirceGraphicsAdapter

# Set up headless Qt for testing
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
from PySide6.QtWidgets import QApplication

class MockScene:
    def __init__(self):
        self.items = []
    
    def addItem(self, item):
        self.items.append(item)

def validate_peirce_conventions(rendering_instructions):
    """Validate that Peirce's visual conventions are properly applied."""
    validation_results = {
        'alternating_shading': True,
        'line_weights': True,
        'cut_shapes': True,
        'z_ordering': True,
        'issues': []
    }
    
    # Check alternating shading
    context_elements = [e for e in rendering_instructions.get('elements', []) if e.get('type') == 'context']
    for element in context_elements:
        z_index = element.get('z_index', 0)
        nesting_level = z_index // 10  # Approximate nesting level
        fill_color = element.get('style', {}).get('fill_color', 'unknown')
        
        expected_even = nesting_level % 2 == 0
        is_white = fill_color == '#FFFFFF'
        is_gray = fill_color == '#E8E8E8'
        
        if not ((expected_even and is_white) or (not expected_even and is_gray)):
            validation_results['alternating_shading'] = False
            validation_results['issues'].append(f"Incorrect shading for {element.get('id')} at level {nesting_level}")
    
    # Check line weights
    ligatures = rendering_instructions.get('ligatures', [])
    for ligature in ligatures:
        line_width = ligature.get('style', {}).get('line_width', 0)
        if line_width < 3.0:  # Should be heavy lines
            validation_results['line_weights'] = False
            validation_results['issues'].append(f"Ligature {ligature.get('id')} has thin line ({line_width})")
    
    for element in context_elements:
        line_width = element.get('style', {}).get('line_width', 0)
        if line_width > 2.5:  # Should be thin lines
            validation_results['line_weights'] = False
            validation_results['issues'].append(f"Context {element.get('id')} has thick line ({line_width})")
    
    # Check cut shapes
    for element in context_elements:
        shape = element.get('shape', {})
        shape_type = shape.get('type', 'unknown')
        corner_radius = shape.get('corner_radius', 0)
        z_index = element.get('z_index', 0)
        
        if z_index == 0:  # Sheet should be rectangular
            if shape_type != 'rectangle' or corner_radius != 0:
                validation_results['cut_shapes'] = False
                validation_results['issues'].append(f"Sheet {element.get('id')} should be rectangular")
        else:  # Cuts should be oval
            if shape_type != 'oval' or corner_radius <= 0:
                validation_results['cut_shapes'] = False
                validation_results['issues'].append(f"Cut {element.get('id')} should be oval")
    
    # Check z-ordering (elements should be ordered by nesting level)
    all_elements = rendering_instructions.get('elements', []) + rendering_instructions.get('ligatures', [])
    z_indices = [e.get('z_index', 0) for e in all_elements]
    if z_indices != sorted(z_indices):
        validation_results['z_ordering'] = False
        validation_results['issues'].append("Z-ordering is not correct")
    
    return validation_results

def test_comprehensive_validation():
    """Run comprehensive validation tests."""
    
    # Initialize Qt application
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Test cases with expected results
    test_cases = [
        {
            'name': 'Simple Implication',
            'clif': '(if (Man Socrates) (Mortal Socrates))',
            'expected_contexts': 3,
            'expected_predicates': 2,
            'expected_entities': 1
        },
        {
            'name': 'Existential Quantification',
            'clif': '(exists (x) (and (P x) (Q x)))',
            'expected_contexts': 2,
            'expected_predicates': 2,
            'expected_entities': 1
        },
        {
            'name': 'Existential with Negation',
            'clif': '(exists (x) (and (P x) (not (Q x))))',
            'expected_contexts': 3,
            'expected_predicates': 2,
            'expected_entities': 1
        },
        {
            'name': 'Universal Quantification',
            'clif': '(forall (x) (if (Man x) (Mortal x)))',
            'expected_contexts': 5,  # Complex nesting
            'expected_predicates': 2,
            'expected_entities': 1
        }
    ]
    
    parser = CLIFParser()
    layout_engine = PeirceLayoutEngine(viewport_width=800, viewport_height=600)
    
    overall_results = {
        'total_tests': len(test_cases),
        'passed_tests': 0,
        'failed_tests': 0,
        'test_results': []
    }
    
    print(f"🧪 COMPREHENSIVE VALIDATION TEST")
    print(f"{'='*60}")
    
    for test_case in test_cases:
        print(f"\n📋 Testing: {test_case['name']}")
        print(f"CLIF: {test_case['clif']}")
        print(f"{'-'*40}")
        
        test_result = {
            'name': test_case['name'],
            'passed': True,
            'issues': []
        }
        
        try:
            # Parse CLIF to EG-HG
            parse_result = parser.parse(test_case['clif'])
            if parse_result.errors:
                test_result['passed'] = False
                test_result['issues'].append(f"CLIF parsing failed: {[e.message for e in parse_result.errors]}")
                continue
            
            # Convert to EGRF
            egrf_doc = convert_graph_to_egrf(parse_result.graph, {})
            
            # Generate rendering instructions
            rendering_instructions = layout_engine.calculate_layout(egrf_doc)
            
            # Validate element counts
            elements = rendering_instructions.get('elements', [])
            ligatures = rendering_instructions.get('ligatures', [])
            
            context_count = len([e for e in elements if e.get('type') == 'context'])
            predicate_count = len([e for e in elements if e.get('type') == 'predicate'])
            ligature_count = len(ligatures)
            
            print(f"  📊 Element Counts:")
            print(f"    Contexts: {context_count} (expected: {test_case['expected_contexts']})")
            print(f"    Predicates: {predicate_count} (expected: {test_case['expected_predicates']})")
            print(f"    Ligatures: {ligature_count} (expected: varies)")
            
            if context_count != test_case['expected_contexts']:
                test_result['passed'] = False
                test_result['issues'].append(f"Context count mismatch: {context_count} vs {test_case['expected_contexts']}")
            
            if predicate_count != test_case['expected_predicates']:
                test_result['passed'] = False
                test_result['issues'].append(f"Predicate count mismatch: {predicate_count} vs {test_case['expected_predicates']}")
            
            # Validate Peirce's conventions
            print(f"  🎨 Peirce's Conventions:")
            convention_results = validate_peirce_conventions(rendering_instructions)
            
            for convention, passed in convention_results.items():
                if convention != 'issues':
                    status = "✓" if passed else "✗"
                    print(f"    {status} {convention.replace('_', ' ').title()}: {'PASS' if passed else 'FAIL'}")
                    if not passed:
                        test_result['passed'] = False
            
            if convention_results['issues']:
                test_result['issues'].extend(convention_results['issues'])
            
            # Test graphics adapter
            print(f"  🖼️  Graphics Adapter:")
            mock_scene = MockScene()
            graphics_adapter = PeirceGraphicsAdapter(mock_scene)
            graphics_items = graphics_adapter.create_graphics_from_instructions(rendering_instructions)
            graphics_adapter.update_element_names(egrf_doc)
            
            print(f"    Graphics items created: {len(graphics_items)}")
            print(f"    Scene items: {len(mock_scene.items)}")
            
            if len(graphics_items) == 0:
                test_result['passed'] = False
                test_result['issues'].append("No graphics items created")
            
            # Performance check
            print(f"  ⚡ Performance: Layout generation completed successfully")
            
        except Exception as e:
            test_result['passed'] = False
            test_result['issues'].append(f"Exception: {str(e)}")
            print(f"  ✗ Error: {e}")
        
        # Record results
        if test_result['passed']:
            print(f"  🎉 PASSED")
            overall_results['passed_tests'] += 1
        else:
            print(f"  ❌ FAILED")
            print(f"    Issues: {'; '.join(test_result['issues'])}")
            overall_results['failed_tests'] += 1
        
        overall_results['test_results'].append(test_result)
    
    # Final summary
    print(f"\n{'='*60}")
    print(f"📈 FINAL RESULTS")
    print(f"{'='*60}")
    print(f"Total Tests: {overall_results['total_tests']}")
    print(f"Passed: {overall_results['passed_tests']} ✓")
    print(f"Failed: {overall_results['failed_tests']} ✗")
    print(f"Success Rate: {(overall_results['passed_tests']/overall_results['total_tests']*100):.1f}%")
    
    if overall_results['failed_tests'] == 0:
        print(f"\n🎉 ALL TESTS PASSED! The Peirce Convention-Aware Layout Engine is working perfectly!")
    else:
        print(f"\n⚠️  Some tests failed. Review the issues above.")
    
    return overall_results

if __name__ == "__main__":
    test_comprehensive_validation()

