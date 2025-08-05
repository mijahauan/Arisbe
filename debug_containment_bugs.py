#!/usr/bin/env python3
"""
Debug script to identify and fix containment positioning bugs in layout engine.
Tests the specific cases that are failing containment contracts.
"""

import sys
import os

# Add src to path
src_path = os.path.join(os.path.dirname(__file__), 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from egi_core_dau import RelationalGraphWithCuts
from egif_parser_dau import EGIFParser
from layout_engine import LayoutEngine
from containment_contracts import ContainmentValidator

def debug_containment_issues():
    """Debug the specific containment issues found in testing."""
    
    print("=== Debug Containment Issues ===\n")
    
    test_cases = [
        ("Roberts' Disjunction", "~[ ~[ (P \"x\") ] ~[ (Q \"x\") ] ]"),
        ("Man-Mortal Implication", "~[ (Human \"Socrates\") ~[ (Mortal \"Socrates\") ] ]"),
        ("Simple Cut Test", "*x ~[ (P x) ]"),
    ]
    
    layout_engine = LayoutEngine()
    validator = ContainmentValidator()
    
    for name, egif in test_cases:
        print(f"Testing: {name}")
        print(f"EGIF: {egif}")
        
        try:
            # Parse EGIF
            parser = EGIFParser(egif)
            graph = parser.parse()
            print(f"✓ Parsed successfully")
            
            # Generate layout
            layout = layout_engine.layout_graph(graph)
            print(f"✓ Layout generated")
            
            # Check containment violations
            violations = validator.validate_layout_containment(layout, graph)
            
            if violations:
                print(f"❌ CONTAINMENT VIOLATIONS ({len(violations)}):")
                for v in violations:
                    print(f"   {v.element_name} ({v.element_type}) at {v.position}")
                    print(f"   Expected in: {v.expected_area}")
                    print(f"   Container bounds: {v.container_bounds}")
                    print(f"   Violation: {v.violation_type}")
                    print()
                
                # Debug layout details
                print("Layout Details:")
                for elem_id, elem in layout.elements.items():
                    print(f"   {elem_id}: {elem.element_type} at {elem.position}, bounds {elem.bounds}, parent: {elem.parent_area}")
                
            else:
                print(f"✓ No containment violations")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 60)

if __name__ == "__main__":
    debug_containment_issues()
