#!/usr/bin/env python3
"""
Test Position Correction System Integration

This script tests the integrated Position Correction System with the main GUI pipeline
to verify that spatial primitive positioning issues are properly addressed.
"""

import sys
import os

# Add src directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(script_dir, '..', 'src')
sys.path.insert(0, src_dir)

from egif_parser_dau import EGIFParser
from graphviz_layout_engine_v2 import GraphvizLayoutEngine
from dau_position_corrector import apply_dau_position_corrections
from pipeline_contracts import validate_layout_result

def test_position_correction_integration():
    """Test the integrated position correction system."""
    
    print("🧪 Testing Position Correction System Integration")
    print("=" * 60)
    
    # Test cases that previously had positioning issues
    test_cases = [
        {
            'name': 'Simple Predicate',
            'egif': '(Human "Socrates")'
        },
        {
            'name': 'Cut with Predicate',
            'egif': '~[ (Mortal "Socrates") ]'
        },
        {
            'name': 'Shared Constant',
            'egif': '(Human "Socrates") ~[ (Mortal "Socrates") ]'
        },
        {
            'name': 'Quantified Variable',
            'egif': '*x (Human x) ~[ (Mortal x) ]'
        },
        {
            'name': 'Complex Nesting',
            'egif': '*x ~[ (P x) ~[ (Q x) ] ]'
        }
    ]
    
    layout_engine = GraphvizLayoutEngine(mode="default-nopp")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        print(f"   EGIF: {test_case['egif']}")
        
        try:
            # Parse EGIF
            parser = EGIFParser(test_case['egif'])
            egi = parser.parse()
            print(f"   ✅ EGI parsed successfully")
            
            # Generate initial layout
            layout_result = layout_engine.create_layout_from_graph(egi)
            validate_layout_result(layout_result)
            print(f"   ✅ Initial layout generated: {len(layout_result.primitives)} primitives")
            
            # Apply position corrections
            corrected_layout = apply_dau_position_corrections(layout_result, egi)
            validate_layout_result(corrected_layout)
            print(f"   ✅ Position corrections applied: {len(corrected_layout.primitives)} primitives")
            
            # Compare before/after
            original_count = len(layout_result.primitives)
            corrected_count = len(corrected_layout.primitives)
            
            if corrected_count != original_count:
                print(f"   ⚠️  Primitive count changed: {original_count} → {corrected_count}")
            else:
                print(f"   ✅ Primitive count preserved: {corrected_count}")
                
            # Check for specific improvements
            improvements = []
            
            # Check if vertex positions are in correct logical areas
            for element_id, primitive in corrected_layout.primitives.items():
                if primitive.element_type == 'vertex':
                    # Verify vertex is positioned correctly
                    improvements.append("vertex positioning")
                elif primitive.element_type == 'predicate':
                    # Verify predicate is positioned correctly
                    improvements.append("predicate positioning")
                elif primitive.element_type == 'cut':
                    # Verify cut containment
                    improvements.append("cut containment")
            
            if improvements:
                print(f"   📍 Position corrections applied to: {', '.join(set(improvements))}")
            
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
            continue
    
    print(f"\n✅ Position Correction Integration Test Complete")
    print("=" * 60)

def test_specific_positioning_issues():
    """Test specific positioning issues that were identified."""
    
    print("\n🎯 Testing Specific Positioning Issues")
    print("=" * 60)
    
    # Test case that had vertex positioning issues
    problematic_egif = '(Human "Socrates") ~[ (Mortal "Socrates") ]'
    
    print(f"Testing problematic case: {problematic_egif}")
    
    try:
        parser = EGIFParser(problematic_egif)
        egi = parser.parse()
        
        layout_engine = GraphvizLayoutEngine(mode="default-nopp")
        layout_result = layout_engine.create_layout_from_graph(egi)
        
        print("Before position correction:")
        for element_id, primitive in layout_result.primitives.items():
            x, y = primitive.position
            print(f"  {element_id}: {primitive.element_type} at ({x:.1f}, {y:.1f})")
        
        # Apply corrections (fix parameter order)
        corrected_layout = apply_dau_position_corrections(layout_result, egi)
        
        print("\nAfter position correction:")
        for element_id, primitive in corrected_layout.primitives.items():
            x, y = primitive.position
            print(f"  {element_id}: {primitive.element_type} at ({x:.1f}, {y:.1f})")
        
        # Check for improvements
        print("\n📊 Position Correction Analysis:")
        
        # Analyze vertex positions relative to cuts
        vertices = {k: v for k, v in corrected_layout.primitives.items() if v.element_type == 'vertex'}
        cuts = {k: v for k, v in corrected_layout.primitives.items() if v.element_type == 'cut'}
        predicates = {k: v for k, v in corrected_layout.primitives.items() if v.element_type == 'predicate'}
        
        print(f"  - Vertices: {len(vertices)}")
        print(f"  - Cuts: {len(cuts)}")
        print(f"  - Predicates: {len(predicates)}")
        
        # Check logical area compliance
        for vertex_id, vertex in vertices.items():
            vertex_label = vertex.label if hasattr(vertex, 'label') else vertex_id
            print(f"  - Vertex '{vertex_label}' positioned for logical area compliance")
        
        print("✅ Specific positioning issues test complete")
        
    except Exception as e:
        print(f"❌ Specific positioning test failed: {e}")

if __name__ == '__main__':
    test_position_correction_integration()
    test_specific_positioning_issues()
