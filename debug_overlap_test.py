#!/usr/bin/env python3
"""
Debug test for predicate overlap issues in corpus examples.
Tests the specific cases that show overlap problems.
"""

import sys
import os

# Add src to path
src_path = os.path.join(os.path.dirname(__file__), 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import from the correct API modules
from egi_core_dau import RelationalGraphWithCuts
from egif_parser_dau import EGIFParser
from layout_engine import LayoutEngine

def test_overlap_cases():
    """Test the specific cases showing overlap problems."""
    
    parser = EGIFParser()
    layout_engine = LayoutEngine()
    
    test_cases = [
        ("Dau's Ligature", "*x (P x) ~[ (Q x) (R x) ]"),
        ("Roberts' Disjunction", "~[ ~[ (P \"x\") ] ~[ (Q \"x\") ] ]"),
        ("Simple Multiple Predicates", "*x (A x) (B x) (C x)"),
        ("Nested with Multiple", "*x (P x) ~[ (Q x) (R x) (S x) ]")
    ]
    
    print("=== Debug Test: Predicate Overlap Issues ===\n")
    
    for name, egif in test_cases:
        print(f"Testing: {name}")
        print(f"EGIF: {egif}")
        
        try:
            # Parse EGIF
            graph = parser.parse(egif)
            print(f"✓ Parsed successfully")
            
            # Generate layout
            layout = layout_engine.layout_graph(graph)
            print(f"✓ Layout generated")
            
            # Check for overlaps in layout
            overlaps = check_layout_overlaps(layout)
            if overlaps:
                print(f"❌ OVERLAP DETECTED:")
                for overlap in overlaps:
                    print(f"   {overlap}")
            else:
                print(f"✓ No overlaps detected")
            
            # Generate visual for inspection
            visual_path = f"debug_overlap_{name.lower().replace(' ', '_')}.png"
            try:
                renderer.render_to_file(layout, visual_path)
                print(f"✓ Visual saved: {visual_path}")
            except Exception as e:
                print(f"⚠ Visual generation failed: {e}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 50)

def check_layout_overlaps(layout):
    """Check for overlapping elements in a layout."""
    overlaps = []
    elements = list(layout.elements.values())
    
    for i, elem1 in enumerate(elements):
        for j, elem2 in enumerate(elements[i+1:], i+1):
            if elements_overlap(elem1, elem2):
                overlaps.append(f"{elem1.element_id} ({elem1.element_type}) overlaps {elem2.element_id} ({elem2.element_type})")
    
    return overlaps

def elements_overlap(elem1, elem2):
    """Check if two layout elements overlap."""
    x1_min, y1_min, x1_max, y1_max = elem1.bounds
    x2_min, y2_min, x2_max, y2_max = elem2.bounds
    
    # Check for overlap
    return not (x1_max < x2_min or x2_max < x1_min or y1_max < y2_min or y2_max < y1_min)

if __name__ == "__main__":
    test_overlap_cases()
