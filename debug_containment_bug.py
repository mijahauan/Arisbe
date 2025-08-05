#!/usr/bin/env python3
"""
Debug script to investigate the containment rendering bug.

The issue: In '*x (Human x) ~[ (Mortal x) ]', the Human predicate appears 
outside the cut when it should be inside according to the EGIF structure.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from egif_parser_dau import EGIFParser
from layout_engine import LayoutEngine

def debug_containment_issue():
    """Debug the specific containment issue with predicate placement."""
    
    # The problematic EGIF case
    egif_text = '*x (Human x) ~[ (Mortal x) ]'
    print(f"Debugging EGIF: {egif_text}")
    print("=" * 50)
    
    # 1. Parse EGIF to EGI
    parser = EGIFParser(egif_text)
    egi = parser.parse()
    
    print("EGI Structure:")
    print(f"Vertices: {egi.V}")
    print(f"Edges: {egi.E}")
    print(f"Cuts: {egi.Cut}")
    print(f"Relations: {egi.rel}")
    print(f"Nu mapping: {egi.nu}")
    print()
    
    print("CRITICAL - Area containment mapping:")
    for area_id, elements in egi.area.items():
        print(f"  Area {area_id}: {elements}")
    print()
    
    # 2. Analyze which area each edge should be in
    print("Edge area analysis:")
    for edge in egi.E:
        edge_id = edge.id
        containing_area = None
        for area_id, elements in egi.area.items():
            if edge_id in elements:
                containing_area = area_id
                break
        
        relation_name = egi.rel.get(edge_id, f"Unknown_{edge_id}")
        print(f"  Edge {edge_id} ({relation_name}): should be in area {containing_area}")
    print()
    
    # 3. Generate layout and check area assignments
    layout_engine = LayoutEngine()
    layout_result = layout_engine.layout_graph(egi)
    
    print("Layout area assignments:")
    for element_id, layout_element in layout_result.elements.items():
        if layout_element.element_type == 'edge':
            relation_name = egi.rel.get(element_id, f"Unknown_{element_id}")
            print(f"  Edge {element_id} ({relation_name}): layout assigned to area {layout_element.parent_area}")
    print()
    
    # 4. Check if there's a mismatch
    print("CONTAINMENT VERIFICATION:")
    for edge in egi.E:
        edge_id = edge.id
        # Expected area from EGI
        expected_area = None
        for area_id, elements in egi.area.items():
            if edge_id in elements:
                expected_area = area_id
                break
        
        # Actual area from layout
        layout_element = layout_result.elements.get(edge_id)
        actual_area = layout_element.parent_area if layout_element else None
        
        relation_name = egi.rel.get(edge_id, f"Unknown_{edge_id}")
        
        if expected_area != actual_area:
            print(f"  ❌ MISMATCH: {relation_name} expected in {expected_area}, but layout assigned to {actual_area}")
        else:
            print(f"  ✅ CORRECT: {relation_name} correctly assigned to area {expected_area}")
    
    print()
    print("Cut bounds for reference:")
    for element_id, layout_element in layout_result.elements.items():
        if layout_element.element_type == 'cut':
            print(f"  Cut {element_id}: bounds {layout_element.bounds}")

if __name__ == "__main__":
    debug_containment_issue()
