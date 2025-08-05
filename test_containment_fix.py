#!/usr/bin/env python3
"""
Test script to verify the containment fix works correctly.
This will test both the layout engine and visual rendering.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from egif_parser_dau import EGIFParser
from layout_engine import LayoutEngine

def test_containment_fix():
    """Test that predicates are positioned within their correct areas."""
    
    # Test case: Human should be outside cut, Mortal should be inside cut
    egif_text = '*x (Human x) ~[ (Mortal x) ]'
    print(f"Testing EGIF: {egif_text}")
    print("=" * 60)
    
    # Parse and layout
    parser = EGIFParser(egif_text)
    egi = parser.parse()
    layout_engine = LayoutEngine()
    layout_result = layout_engine.layout_graph(egi)
    
    # Find the cut bounds
    cut_bounds = None
    cut_id = None
    for element_id, layout_element in layout_result.elements.items():
        if layout_element.element_type == 'cut':
            cut_bounds = layout_element.bounds
            cut_id = element_id
            break
    
    if not cut_bounds:
        print("❌ ERROR: No cut found in layout")
        return
    
    cut_x1, cut_y1, cut_x2, cut_y2 = cut_bounds
    print(f"Cut {cut_id} bounds: ({cut_x1}, {cut_y1}) to ({cut_x2}, {cut_y2})")
    print()
    
    # Check each predicate's position relative to cut bounds
    print("PREDICATE POSITION ANALYSIS:")
    for element_id, layout_element in layout_result.elements.items():
        if layout_element.element_type == 'edge':
            relation_name = egi.rel.get(element_id, f"Unknown_{element_id}")
            pred_x, pred_y = layout_element.position
            
            # Check if predicate is inside or outside the cut
            inside_cut = (cut_x1 <= pred_x <= cut_x2 and cut_y1 <= pred_y <= cut_y2)
            
            # Check what area it should be in according to EGI
            expected_area = layout_element.parent_area
            should_be_in_cut = (expected_area == cut_id)
            
            print(f"  {relation_name} ({element_id}):")
            print(f"    Position: ({pred_x:.1f}, {pred_y:.1f})")
            print(f"    Expected area: {expected_area}")
            print(f"    Should be in cut: {should_be_in_cut}")
            print(f"    Actually inside cut bounds: {inside_cut}")
            
            # Verify correctness
            if should_be_in_cut == inside_cut:
                print(f"    ✅ CORRECT: Position matches expected containment")
            else:
                print(f"    ❌ ERROR: Position does not match expected containment!")
                if should_be_in_cut:
                    print(f"      Expected inside cut bounds, but positioned outside")
                else:
                    print(f"      Expected outside cut bounds, but positioned inside")
            print()
    
    print("SUMMARY:")
    print(f"Cut bounds: ({cut_x1:.1f}, {cut_y1:.1f}) to ({cut_x2:.1f}, {cut_y2:.1f})")
    
    # Expected behavior for this EGIF:
    # Human should be outside cut (on sheet)
    # Mortal should be inside cut
    human_edge = None
    mortal_edge = None
    
    for element_id, layout_element in layout_result.elements.items():
        if layout_element.element_type == 'edge':
            relation_name = egi.rel.get(element_id, f"Unknown_{element_id}")
            if relation_name == 'Human':
                human_edge = layout_element
            elif relation_name == 'Mortal':
                mortal_edge = layout_element
    
    if human_edge and mortal_edge:
        human_x, human_y = human_edge.position
        mortal_x, mortal_y = mortal_edge.position
        
        human_inside = (cut_x1 <= human_x <= cut_x2 and cut_y1 <= human_y <= cut_y2)
        mortal_inside = (cut_x1 <= mortal_x <= cut_x2 and cut_y1 <= mortal_y <= cut_y2)
        
        print(f"Human at ({human_x:.1f}, {human_y:.1f}) - Inside cut: {human_inside}")
        print(f"Mortal at ({mortal_x:.1f}, {mortal_y:.1f}) - Inside cut: {mortal_inside}")
        
        if not human_inside and mortal_inside:
            print("✅ CONTAINMENT CORRECT: Human outside, Mortal inside")
        else:
            print("❌ CONTAINMENT ERROR: Incorrect positioning")

if __name__ == "__main__":
    test_containment_fix()
