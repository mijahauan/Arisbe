#!/usr/bin/env python3
"""
Detailed debug script to trace exactly why the containment fix isn't working.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from egif_parser_dau import EGIFParser
from layout_engine import LayoutEngine

def debug_detailed_containment():
    """Debug the exact flow of predicate positioning."""
    
    egif_text = '*x (Human x) ~[ (Mortal x) ]'
    print(f"Debugging EGIF: {egif_text}")
    print("=" * 60)
    
    # Parse and get EGI
    parser = EGIFParser(egif_text)
    egi = parser.parse()
    
    # Create layout engine and add debug prints
    layout_engine = LayoutEngine()
    
    # Monkey patch the collision avoidance method to add debug output
    original_method = layout_engine._avoid_element_collisions_within_bounds
    
    def debug_collision_avoidance(position, all_layouts, bounds, exclude_types=None):
        print(f"\n🔍 DEBUG: _avoid_element_collisions_within_bounds called")
        print(f"  Input position: {position}")
        print(f"  Bounds: {bounds}")
        print(f"  Exclude types: {exclude_types}")
        
        result = original_method(position, all_layouts, bounds, exclude_types)
        
        print(f"  Output position: {result}")
        x, y = result
        x1, y1, x2, y2 = bounds
        within_bounds = (x1 <= x <= x2 and y1 <= y <= y2)
        print(f"  Within bounds: {within_bounds}")
        
        return result
    
    layout_engine._avoid_element_collisions_within_bounds = debug_collision_avoidance
    
    # Also debug the main predicate positioning method
    original_calc_method = layout_engine._calculate_predicate_position_in_area
    
    def debug_predicate_calc(vertex_pos, predicate_index, total_predicates, available_bounds, all_layouts):
        print(f"\n🎯 DEBUG: _calculate_predicate_position_in_area called")
        print(f"  Vertex position: {vertex_pos}")
        print(f"  Available bounds: {available_bounds}")
        
        result = original_calc_method(vertex_pos, predicate_index, total_predicates, available_bounds, all_layouts)
        
        print(f"  Final predicate position: {result}")
        return result
    
    layout_engine._calculate_predicate_position_in_area = debug_predicate_calc
    
    # Generate layout with debug output
    print("\n🚀 Starting layout generation...")
    layout_result = layout_engine.layout_graph(egi)
    
    print("\n📊 FINAL RESULTS:")
    
    # Find cut bounds
    cut_bounds = None
    cut_id = None
    for element_id, layout_element in layout_result.elements.items():
        if layout_element.element_type == 'cut':
            cut_bounds = layout_element.bounds
            cut_id = element_id
            print(f"Cut {cut_id}: {cut_bounds}")
            break
    
    # Check each predicate
    for element_id, layout_element in layout_result.elements.items():
        if layout_element.element_type == 'edge':
            relation_name = egi.rel.get(element_id, f"Unknown_{element_id}")
            position = layout_element.position
            expected_area = layout_element.parent_area
            
            print(f"\n{relation_name} predicate:")
            print(f"  Position: {position}")
            print(f"  Expected area: {expected_area}")
            
            if cut_bounds and expected_area == cut_id:
                x, y = position
                x1, y1, x2, y2 = cut_bounds
                inside = (x1 <= x <= x2 and y1 <= y <= y2)
                print(f"  Should be inside cut: YES")
                print(f"  Actually inside cut: {inside}")
                if not inside:
                    print(f"  ❌ CONTAINMENT VIOLATION!")
                    print(f"     Position {x}, {y} not within bounds {x1}, {y1} to {x2}, {y2}")
            else:
                print(f"  Should be inside cut: NO")

if __name__ == "__main__":
    debug_detailed_containment()
