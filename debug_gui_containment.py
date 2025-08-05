#!/usr/bin/env python3
"""
Debug script to trace the GUI containment issue.
This will help identify why predicates are still outside cuts in the GUI.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from egif_parser_dau import EGIFParser
from layout_engine import LayoutEngine

def debug_gui_containment():
    """Debug the exact same process the GUI uses."""
    
    # Test the problematic cases from the screenshots
    test_cases = [
        '*x ~[ ~[ (P x) ] ]',  # Image 1: P should be inside innermost cut
        '(Human "Socrates") ~[ (Mortal "Socrates") ]'  # Image 2: Mortal should be inside cut
    ]
    
    for i, egif_text in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"TEST CASE {i}: {egif_text}")
        print(f"{'='*60}")
        
        # 1. Parse EGIF → EGI (same as GUI)
        parser = EGIFParser(egif_text)
        egi = parser.parse()
        
        # 2. Generate layout using layout engine (same as GUI)
        layout_engine = LayoutEngine()
        layout_result = layout_engine.layout_graph(egi)
        
        # 3. Analyze containment
        print("\nLAYOUT ANALYSIS:")
        
        # Find cuts
        cuts = {}
        for element_id, layout_element in layout_result.elements.items():
            if layout_element.element_type == 'cut':
                cuts[element_id] = layout_element.bounds
                x1, y1, x2, y2 = layout_element.bounds
                print(f"Cut {element_id}: bounds ({x1:.1f}, {y1:.1f}) to ({x2:.1f}, {y2:.1f})")
        
        # Find predicates and check containment
        print("\nPREDICATE CONTAINMENT:")
        for element_id, layout_element in layout_result.elements.items():
            if layout_element.element_type == 'edge':
                relation_name = egi.rel.get(element_id, f"Unknown_{element_id}")
                pred_x, pred_y = layout_element.position
                expected_area = layout_element.parent_area
                
                print(f"\nPredicate '{relation_name}' (ID: {element_id}):")
                print(f"  Position: ({pred_x:.1f}, {pred_y:.1f})")
                print(f"  Expected area: {expected_area}")
                
                # Check if it should be in a cut
                if expected_area in cuts:
                    cut_x1, cut_y1, cut_x2, cut_y2 = cuts[expected_area]
                    inside_cut = (cut_x1 <= pred_x <= cut_x2 and cut_y1 <= pred_y <= cut_y2)
                    
                    print(f"  Should be in cut: YES")
                    print(f"  Cut bounds: ({cut_x1:.1f}, {cut_y1:.1f}) to ({cut_x2:.1f}, {cut_y2:.1f})")
                    print(f"  Actually inside: {inside_cut}")
                    
                    if not inside_cut:
                        print(f"  ❌ CONTAINMENT VIOLATION!")
                        print(f"     Predicate at ({pred_x:.1f}, {pred_y:.1f}) outside cut bounds")
                    else:
                        print(f"  ✅ CONTAINMENT CORRECT!")
                else:
                    print(f"  Should be in cut: NO (in sheet area)")
                    print(f"  ✅ CONTAINMENT CORRECT!")

if __name__ == "__main__":
    debug_gui_containment()
