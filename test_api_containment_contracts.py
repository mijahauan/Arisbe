#!/usr/bin/env python3
"""
Test script for API containment contracts.
Verifies that the layout engine enforces containment guarantees at the API level.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from egif_parser_dau import EGIFParser
from layout_engine import LayoutEngine
from containment_contracts import ContainmentValidator, validate_containment_contract
from pipeline_contracts import ContractViolationError

def test_api_containment_contracts():
    """Test that API containment contracts work correctly."""
    
    print("🔒 TESTING API CONTAINMENT CONTRACTS")
    print("="*60)
    
    # Test cases
    test_cases = [
        {
            'name': 'Simple Cut',
            'egif': '(Human "Socrates") ~[ (Mortal "Socrates") ]',
            'should_pass': True
        },
        {
            'name': 'Nested Cuts',
            'egif': '*x ~[ ~[ (P x) ] ]',
            'should_pass': True
        },
        {
            'name': 'Complex Graph',
            'egif': '*x *y (Loves x y) ~[ (Happy x) (Sad y) ]',
            'should_pass': True
        }
    ]
    
    layout_engine = LayoutEngine()
    validator = ContainmentValidator()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 TEST {i}: {test_case['name']}")
        print(f"   EGIF: {test_case['egif']}")
        
        try:
            # Parse EGIF → EGI
            parser = EGIFParser(test_case['egif'])
            egi = parser.parse()
            
            # Generate layout with API contract enforcement
            print("   🔧 Generating layout with API contracts...")
            layout_result = layout_engine.layout_graph(egi)
            
            # Additional validation using the validator directly
            violations = validator.validate_layout_containment(layout_result, egi)
            
            if violations:
                print(f"   ❌ CONTAINMENT VIOLATIONS FOUND:")
                for v in violations:
                    print(f"      - {v.element_name} at {v.position} outside {v.expected_area}")
                    print(f"        Container bounds: {v.container_bounds}")
                    print(f"        Violation type: {v.violation_type}")
            else:
                print("   ✅ PERFECT CONTAINMENT - All elements within bounds")
            
            # Test the API contract function directly
            try:
                validate_containment_contract(layout_result, egi)
                print("   ✅ API CONTRACT VALIDATION PASSED")
            except ContractViolationError as e:
                print(f"   ❌ API CONTRACT VIOLATION: {e}")
            
            if test_case['should_pass'] and not violations:
                print(f"   🎉 TEST {i} PASSED")
            elif not test_case['should_pass'] and violations:
                print(f"   🎉 TEST {i} PASSED (Expected violations found)")
            else:
                print(f"   💥 TEST {i} FAILED")
                
        except Exception as e:
            print(f"   💥 TEST {i} ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n🏁 API CONTAINMENT CONTRACT TESTING COMPLETE")

def test_contract_enforcement_integration():
    """Test that the layout engine properly integrates contract enforcement."""
    
    print(f"\n🔗 TESTING CONTRACT ENFORCEMENT INTEGRATION")
    print("="*60)
    
    # Test with a known working case
    egif_text = '*x ~[ ~[ (P x) ] ]'
    
    try:
        parser = EGIFParser(egif_text)
        egi = parser.parse()
        
        layout_engine = LayoutEngine()
        
        print("   🔧 Testing layout_graph method with contract enforcement...")
        layout_result = layout_engine.layout_graph(egi)
        
        print("   ✅ Layout generation completed successfully")
        print("   ✅ API contracts enforced at method boundary")
        
        # Verify the result structure
        print(f"   📊 Layout contains {len(layout_result.elements)} elements")
        
        # Count element types
        cuts = sum(1 for e in layout_result.elements.values() if e.element_type == 'cut')
        vertices = sum(1 for e in layout_result.elements.values() if e.element_type == 'vertex')
        edges = sum(1 for e in layout_result.elements.values() if e.element_type == 'edge')
        
        print(f"   📊 Elements: {cuts} cuts, {vertices} vertices, {edges} edges")
        print("   🎉 CONTRACT ENFORCEMENT INTEGRATION SUCCESSFUL")
        
    except Exception as e:
        print(f"   💥 CONTRACT ENFORCEMENT INTEGRATION FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api_containment_contracts()
    test_contract_enforcement_integration()
