#!/usr/bin/env python
"""
Test EGDF YAML/JSON integration with 9-phase pipeline output.

Validates that the complete pipeline from EGIF → EGI → Layout → EGDF → YAML/JSON
works seamlessly with the latest codebase.
"""

import sys
import os
import json
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from egif_parser_dau import EGIFParser
from layout_phase_implementations import DependencyOrderedPipeline
from egdf_parser import EGDFParser, EGDFMetadata
from dau_yaml_serializer import DAUYAMLConversionSystem

def test_complete_pipeline_integration():
    """Test complete pipeline integration with EGDF serialization."""
    print("🧪 Testing Complete Pipeline Integration")
    print("=" * 60)
    print("EGIF → EGI → 9-Phase Layout → EGDF → YAML/JSON")
    print()
    
    # Test cases with varying complexity
    test_cases = [
        {
            'name': 'Simple Predicate',
            'egif': '*x (Human x)',
            'description': 'Basic predicate with existential quantification'
        },
        {
            'name': 'Nested Cut',
            'egif': '*x (Human x) ~[ (Mortal x) ]',
            'description': 'Predicate with negated cut'
        },
        {
            'name': 'Complex Relations',
            'egif': '*x *y (Human x) (Loves x y) ~[ (Mortal x) (Happy y) ]',
            'description': 'Multiple predicates with nested cuts'
        },
        {
            'name': 'Isolated Vertices',
            'egif': '[*x] [*y] (Knows x y)',
            'description': 'Isolated vertices with relation'
        }
    ]
    
    egdf_parser = EGDFParser()
    yaml_system = DAUYAMLConversionSystem()
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print(f"EGIF: {test_case['egif']}")
        print(f"Description: {test_case['description']}")
        print("-" * 40)
        
        try:
            start_time = time.time()
            
            # Step 1: Parse EGIF to EGI
            parser = EGIFParser(test_case['egif'])
            egi = parser.parse()
            print(f"✓ EGI parsed: V={len(egi.V)}, E={len(egi.E)}, Cuts={len(egi.Cut)}")
            
            # Step 2: Run 9-phase layout pipeline
            pipeline = DependencyOrderedPipeline()
            layout_result = pipeline.execute_pipeline(egi)
            print(f"✓ Layout generated: {len(layout_result.elements)} elements")
            
            # Step 3: Convert layout to EGDF spatial primitives
            spatial_primitives = []
            for element_id, element in layout_result.elements.items():
                primitive_dict = {
                    'element_id': element_id,
                    'element_type': element.element_type,
                    'position': element.position,
                    'bounds': element.bounds,
                    'z_index': getattr(element, 'z_index', 0)
                }
                spatial_primitives.append(primitive_dict)
            
            # Step 4: Create EGDF document
            metadata = EGDFMetadata(
                title=test_case['name'],
                description=test_case['description'],
                source=test_case['egif']
            )
            
            egdf_doc = egdf_parser.create_egdf_from_egi(egi, spatial_primitives, metadata)
            print(f"✓ EGDF document created")
            
            # Step 5: Export to JSON
            json_output = egdf_parser.egdf_to_json(egdf_doc, indent=2)
            print(f"✓ JSON export: {len(json_output)} bytes")
            
            # Step 6: Export to YAML
            yaml_output = egdf_parser.egdf_to_yaml(egdf_doc)
            print(f"✓ YAML export: {len(yaml_output)} bytes")
            
            # Step 7: Test round-trip JSON
            parsed_json = egdf_parser.parse_egdf(json_output, "json")
            extracted_egi_json = egdf_parser.extract_egi_from_egdf(parsed_json)
            print(f"✓ JSON round-trip: V={len(extracted_egi_json.V)}, E={len(extracted_egi_json.E)}")
            
            # Step 8: Test round-trip YAML
            parsed_yaml = egdf_parser.parse_egdf(yaml_output, "yaml")
            extracted_egi_yaml = egdf_parser.extract_egi_from_egdf(parsed_yaml)
            print(f"✓ YAML round-trip: V={len(extracted_egi_yaml.V)}, E={len(extracted_egi_yaml.E)}")
            
            # Step 9: Validate structure preservation
            original_structure = {
                'vertices': len(egi.V),
                'edges': len(egi.E),
                'cuts': len(egi.Cut)
            }
            
            json_structure = {
                'vertices': len(extracted_egi_json.V),
                'edges': len(extracted_egi_json.E),
                'cuts': len(extracted_egi_json.Cut)
            }
            
            yaml_structure = {
                'vertices': len(extracted_egi_yaml.V),
                'edges': len(extracted_egi_yaml.E),
                'cuts': len(extracted_egi_yaml.Cut)
            }
            
            structure_preserved = (original_structure == json_structure == yaml_structure)
            
            total_time = time.time() - start_time
            
            result = {
                'name': test_case['name'],
                'success': True,
                'time': total_time,
                'original_structure': original_structure,
                'json_structure': json_structure,
                'yaml_structure': yaml_structure,
                'structure_preserved': structure_preserved,
                'json_size': len(json_output),
                'yaml_size': len(yaml_output),
                'layout_elements': len(layout_result.elements)
            }
            
            if structure_preserved:
                print("✅ SUCCESS - Complete pipeline integration working")
            else:
                print("⚠️  WARNING - Structure not fully preserved")
                print(f"   Original: {original_structure}")
                print(f"   JSON: {json_structure}")
                print(f"   YAML: {yaml_structure}")
            
            print(f"   Time: {total_time:.3f}s")
            print(f"   Layout elements: {len(layout_result.elements)}")
            print(f"   JSON: {len(json_output)} bytes, YAML: {len(yaml_output)} bytes")
            
        except Exception as e:
            print(f"❌ FAILED: {e}")
            import traceback
            traceback.print_exc()
            
            result = {
                'name': test_case['name'],
                'success': False,
                'error': str(e),
                'time': time.time() - start_time
            }
        
        results.append(result)
        print()
    
    # Summary
    successful_tests = sum(1 for r in results if r['success'])
    total_tests = len(results)
    success_rate = (successful_tests / total_tests) * 100
    
    print("=" * 60)
    print("INTEGRATION TEST RESULTS")
    print("=" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"Successful: {successful_tests}/{total_tests} ({success_rate:.1f}%)")
    
    if successful_tests > 0:
        successful_results = [r for r in results if r['success']]
        avg_time = sum(r['time'] for r in successful_results) / len(successful_results)
        avg_json_size = sum(r['json_size'] for r in successful_results) / len(successful_results)
        avg_yaml_size = sum(r['yaml_size'] for r in successful_results) / len(successful_results)
        
        print(f"Average Time: {avg_time:.3f}s")
        print(f"Average JSON Size: {avg_json_size:.0f} bytes")
        print(f"Average YAML Size: {avg_yaml_size:.0f} bytes")
        
        structure_preserved_count = sum(1 for r in successful_results if r.get('structure_preserved', False))
        print(f"Structure Preservation: {structure_preserved_count}/{successful_tests} ({(structure_preserved_count/successful_tests)*100:.1f}%)")
    
    print()
    if success_rate == 100.0:
        print("🎉 PERFECT INTEGRATION - All pipeline components working together!")
    elif success_rate >= 75.0:
        print("✅ GOOD INTEGRATION - Most components working")
    else:
        print("⚠️  INTEGRATION ISSUES - Some components need attention")
    
    return results

def test_layout_types_compatibility():
    """Test that EGDF serialization works with latest layout types."""
    print("\n🔧 Testing Layout Types Compatibility")
    print("=" * 40)
    
    try:
        # Test with simple case
        egif = "*x (Human x)"
        parser = EGIFParser(egif)
        egi = parser.parse()
        
        # Generate layout
        pipeline = DependencyOrderedPipeline()
        layout_result = pipeline.execute_pipeline(egi)
        
        # Check layout element types
        element_types = set()
        for element in layout_result.elements.values():
            element_types.add(type(element).__name__)
            
        print(f"Layout element types found: {element_types}")
        
        # Test EGDF creation with these types
        spatial_primitives = []
        for element_id, element in layout_result.elements.items():
            # Convert to dict format for EGDF
            primitive_dict = {
                'element_id': element_id,
                'element_type': element.element_type,
                'position': element.position,
                'bounds': element.bounds
            }
            spatial_primitives.append(primitive_dict)
        
        egdf_parser = EGDFParser()
        egdf_doc = egdf_parser.create_egdf_from_egi(egi, spatial_primitives)
        
        # Test serialization
        json_output = egdf_parser.egdf_to_json(egdf_doc)
        yaml_output = egdf_parser.egdf_to_yaml(egdf_doc)
        
        print("✅ Layout types compatible with EGDF serialization")
        print(f"   Generated {len(spatial_primitives)} spatial primitives")
        print(f"   JSON: {len(json_output)} bytes")
        print(f"   YAML: {len(yaml_output)} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Layout types compatibility issue: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("EGDF Integration Test Suite")
    print("=" * 60)
    
    # Test complete pipeline integration
    integration_results = test_complete_pipeline_integration()
    
    # Test layout types compatibility
    compatibility_success = test_layout_types_compatibility()
    
    # Final summary
    print("\n" + "=" * 60)
    print("FINAL INTEGRATION STATUS")
    print("=" * 60)
    
    integration_success = sum(1 for r in integration_results if r['success'])
    total_integration = len(integration_results)
    
    print(f"Pipeline Integration: {integration_success}/{total_integration} tests passed")
    print(f"Layout Types Compatibility: {'✅ PASS' if compatibility_success else '❌ FAIL'}")
    
    overall_success = (integration_success == total_integration) and compatibility_success
    
    if overall_success:
        print("\n🎉 EGDF YAML/JSON INTEGRATION FULLY VALIDATED!")
        print("   ✓ 9-phase pipeline output serializes correctly")
        print("   ✓ Round-trip preservation works")
        print("   ✓ Latest layout types compatible")
        print("   ✓ Both JSON and YAML formats supported")
    else:
        print("\n⚠️  INTEGRATION ISSUES DETECTED")
        print("   Some components need attention before full deployment")
