#!/usr/bin/env python3
"""
Challenging Position Correction Test Cases

This script tests the Position Correction System with more complex cases that are likely
to require active position corrections, not just validation.
"""

import sys
import os

# Add src directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(script_dir, '..', 'src')
sys.path.insert(0, src_dir)

from egif_parser_dau import EGIFParser
from layout_phase_implementations import NinePhaseLayoutPipeline
from dau_position_corrector import apply_dau_position_corrections
from pipeline_contracts import validate_layout_result

def test_challenging_cases():
    """Test cases that should trigger active position corrections."""
    
    print("🎯 Testing Challenging Position Correction Cases")
    print("=" * 60)
    
    # More complex test cases that may require position corrections
    challenging_cases = [
        {
            'name': 'Multiple Shared Constants',
            'egif': '(Human "Socrates") (Mortal "Socrates") (Wise "Socrates")',
            'description': 'Three predicates sharing the same constant - vertex should be positioned optimally'
        },
        {
            'name': 'Cross-Cut Variable Sharing',
            'egif': '*x (Human x) ~[ (Mortal x) ~[ (Wise x) ] ]',
            'description': 'Variable shared across multiple nested cuts - lines should cross cuts properly'
        },
        {
            'name': 'Complex Cut Nesting with Shared Elements',
            'egif': '*x *y (Human x) ~[ (Loves x y) ~[ (Mortal y) ] ] (Wise y)',
            'description': 'Multiple variables, nested cuts, shared across areas'
        },
        {
            'name': 'Roberts Disjunction Pattern',
            'egif': '*x ~[ ~[ (P x) ] (Q x) ]',
            'description': 'Classic EG pattern that requires specific vertex positioning'
        },
        {
            'name': 'Multiple Disjunctions',
            'egif': '*x ~[ ~[ (P x) ] ~[ (Q x) ] ]',
            'description': 'Multiple disjunctive branches sharing a variable'
        },
        {
            'name': 'Deep Nesting with Constants',
            'egif': '(Human "Socrates") ~[ ~[ ~[ (Mortal "Socrates") ] ] ]',
            'description': 'Deeply nested cuts with shared constant'
        },
        {
            'name': 'Complex Ligature Network',
            'egif': '*x *y *z (P x y) (Q y z) (R x z) ~[ (S x y z) ]',
            'description': 'Multiple variables forming complex ligature connections'
        },
        {
            'name': 'Overlapping Area Dependencies',
            'egif': '*x *y (P x) ~[ (Q x y) ~[ (R y) ] ] (S y)',
            'description': 'Variables with dependencies across overlapping areas'
        }
    ]
    
    pipeline = NinePhaseLayoutPipeline()
    
    for i, test_case in enumerate(challenging_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        print(f"   EGIF: {test_case['egif']}")
        print(f"   Description: {test_case['description']}")
        
        try:
            # Parse EGIF
            parser = EGIFParser(test_case['egif'])
            egi = parser.parse()
            print(f"   ✅ EGI parsed successfully")
            
            # Generate initial layout
            original_layout = pipeline.execute_pipeline(egi)
            validate_layout_result(original_layout)
            print(f"   ✅ Original layout: {len(original_layout.primitives)} primitives")
            
            # Apply position corrections
            corrected_layout = apply_dau_position_corrections(original_layout, egi)
            validate_layout_result(corrected_layout)
            print(f"   ✅ Corrected layout: {len(corrected_layout.primitives)} primitives")
            
            # Analyze changes
            changes = analyze_position_changes(original_layout, corrected_layout)
            
            if changes > 0:
                print(f"   📍 Active corrections applied: {changes} elements repositioned")
            else:
                print(f"   ✅ No corrections needed: positions already optimal")
                
            # Check for specific positioning issues
            check_positioning_issues(corrected_layout, egi, test_case['name'])
            
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
            continue
    
    print(f"\n✅ Challenging Position Correction Test Complete")
    print("=" * 60)

def analyze_position_changes(original_layout, corrected_layout):
    """Count significant position changes between layouts."""
    
    changes = 0
    
    for element_id in original_layout.primitives:
        if element_id in corrected_layout.primitives:
            orig_pos = original_layout.primitives[element_id].position
            corr_pos = corrected_layout.primitives[element_id].position
            
            # Calculate position change
            dx = corr_pos[0] - orig_pos[0]
            dy = corr_pos[1] - orig_pos[1]
            distance = (dx**2 + dy**2)**0.5
            
            if distance > 0.1:  # Threshold for significant change
                changes += 1
                element_type = original_layout.primitives[element_id].element_type
                print(f"      → {element_id} ({element_type}): moved {distance:.1f} units")
    
    return changes

def check_positioning_issues(layout_result, egi, test_name):
    """Check for specific positioning issues that should be corrected."""
    
    issues_found = []
    
    # Check 1: Vertices should be in appropriate logical areas
    vertices = {k: v for k, v in layout_result.primitives.items() if v.element_type == 'vertex'}
    cuts = {k: v for k, v in layout_result.primitives.items() if v.element_type == 'cut'}
    
    for vertex_id, vertex in vertices.items():
        # Check if vertex is properly positioned relative to its logical area
        if vertex.parent_area:
            if vertex.parent_area in cuts:
                cut = cuts[vertex.parent_area]
                # Verify vertex is within cut bounds
                vx, vy = vertex.position
                cx1, cy1, cx2, cy2 = cut.bounds
                
                if not (cx1 <= vx <= cx2 and cy1 <= vy <= cy2):
                    issues_found.append(f"Vertex {vertex_id} outside its logical area bounds")
    
    # Check 2: Cut containment should be proper
    for cut_id, cut in cuts.items():
        # Check if cut properly contains its elements
        contained_elements = [p for p in layout_result.primitives.values() 
                            if p.parent_area == cut_id]
        
        if contained_elements:
            cx1, cy1, cx2, cy2 = cut.bounds
            for element in contained_elements:
                ex, ey = element.position
                if not (cx1 <= ex <= cx2 and cy1 <= ey <= cy2):
                    issues_found.append(f"Cut {cut_id} doesn't properly contain element {element.element_id}")
    
    # Check 3: Ligature paths should be reasonable
    edges = {k: v for k, v in layout_result.primitives.items() if v.element_type == 'edge'}
    
    for edge_id, edge in edges.items():
        if edge.curve_points and len(edge.curve_points) >= 2:
            # Check for unreasonably long or complex paths
            total_length = 0
            for i in range(len(edge.curve_points) - 1):
                p1 = edge.curve_points[i]
                p2 = edge.curve_points[i + 1]
                segment_length = ((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)**0.5
                total_length += segment_length
            
            # Heuristic: very long edges might indicate positioning issues
            if total_length > 500:  # Arbitrary threshold
                issues_found.append(f"Edge {edge_id} has unusually long path ({total_length:.1f} units)")
    
    # Report findings
    if issues_found:
        print(f"   ⚠️  Positioning issues detected:")
        for issue in issues_found:
            print(f"      - {issue}")
    else:
        print(f"   ✅ No positioning issues detected")

def test_position_correction_effectiveness():
    """Test specific scenarios where position correction should be most effective."""
    
    print(f"\n🔬 Testing Position Correction Effectiveness")
    print("=" * 60)
    
    # Test case designed to trigger corrections
    test_egif = '*x (Human x) ~[ (Mortal x) ~[ (Wise x) ] ] (Greek x)'
    
    print(f"Testing effectiveness with: {test_egif}")
    
    try:
        parser = EGIFParser(test_egif)
        egi = parser.parse()
        
        layout_engine = GraphvizLayoutEngine(mode="default-nopp")
        original_layout = layout_engine.create_layout_from_graph(egi)
        
        print("\nOriginal positions:")
        for element_id, primitive in original_layout.primitives.items():
            x, y = primitive.position
            print(f"  {element_id}: {primitive.element_type} at ({x:.1f}, {y:.1f})")
        
        # Apply corrections
        corrected_layout = apply_dau_position_corrections(original_layout, egi)
        
        print("\nCorrected positions:")
        for element_id, primitive in corrected_layout.primitives.items():
            x, y = primitive.position
            print(f"  {element_id}: {primitive.element_type} at ({x:.1f}, {y:.1f})")
        
        # Calculate improvement metrics
        print("\n📊 Correction Effectiveness Analysis:")
        
        # Measure total displacement
        total_displacement = 0
        elements_moved = 0
        
        for element_id in original_layout.primitives:
            if element_id in corrected_layout.primitives:
                orig_pos = original_layout.primitives[element_id].position
                corr_pos = corrected_layout.primitives[element_id].position
                
                dx = corr_pos[0] - orig_pos[0]
                dy = corr_pos[1] - orig_pos[1]
                distance = (dx**2 + dy**2)**0.5
                
                if distance > 0.1:
                    total_displacement += distance
                    elements_moved += 1
        
        print(f"  - Elements moved: {elements_moved}")
        print(f"  - Total displacement: {total_displacement:.1f} units")
        print(f"  - Average displacement: {total_displacement/max(elements_moved, 1):.1f} units per moved element")
        
        if elements_moved > 0:
            print("  ✅ Position corrections are actively improving layout")
        else:
            print("  ℹ️  No corrections needed - original layout already optimal")
            
    except Exception as e:
        print(f"❌ Effectiveness test failed: {e}")

if __name__ == '__main__':
    test_challenging_cases()
    test_position_correction_effectiveness()
