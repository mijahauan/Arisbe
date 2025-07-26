#!/usr/bin/env python3
"""
Test GUI integration logic without the actual GUI.
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from clif_parser import CLIFParser
from egrf_from_graph import convert_graph_to_egrf
from gui.layout_calculator import LayoutCalculator

def test_gui_integration():
    """Test the complete GUI integration pipeline."""
    print("=== Testing GUI Integration Pipeline ===")
    
    # Test with the canonical implication
    clif_text = "(if (Man Socrates) (Mortal Socrates))"
    print(f"Testing CLIF: {clif_text}")
    
    try:
        # Step 1: Parse CLIF (same as GUI)
        parser = CLIFParser()
        parse_result = parser.parse(clif_text)
        
        if not parse_result.graph:
            print("✗ CLIF parsing failed")
            return False
        
        print("✓ CLIF parsing successful")
        
        # Step 2: Convert to EGRF (same as GUI)
        egrf_doc = convert_graph_to_egrf(parse_result.graph, {
            'title': 'canonical_implication',
            'description': 'Test example'
        })
        
        if not egrf_doc:
            print("✗ EGRF conversion failed")
            return False
        
        print("✓ EGRF conversion successful")
        print(f"  Elements: {len(egrf_doc.logical_elements)}")
        
        # Step 3: Calculate layout (same as GUI)
        layout_calculator = LayoutCalculator(1200, 800)
        layout_data = layout_calculator.calculate_layout(egrf_doc)
        
        if not layout_data:
            print("✗ Layout calculation failed")
            return False
        
        print("✓ Layout calculation successful")
        print(f"  Layout elements: {len(layout_data)}")
        
        # Step 4: Simulate graphics item creation (same as GUI)
        graphics_items = {}
        
        # Count items by type
        context_items = 0
        predicate_items = 0
        entity_items = 0
        
        for element_id, layout_info in layout_data.items():
            element_type = layout_info.get('element_type')
            
            if element_type == 'context':
                # Simulate ContextItem creation
                print(f"  Creating ContextItem: {element_id}")
                context_items += 1
                
            elif element_type == 'predicate':
                # Simulate PredicateItem creation
                print(f"  Creating PredicateItem: {element_id}")
                predicate_items += 1
                
            elif element_type == 'entity':
                # Simulate EntityItem creation
                print(f"  Creating EntityItem: {element_id}")
                entity_items += 1
        
        print(f"✓ Graphics items simulation successful")
        print(f"  Context items: {context_items}")
        print(f"  Predicate items: {predicate_items}")
        print(f"  Entity items: {entity_items}")
        
        # Step 5: Simulate statistics calculation (same as GUI)
        elements = egrf_doc.logical_elements
        contexts = sum(1 for elem in elements if elem.logical_type in ['sheet', 'cut'])
        predicates = sum(1 for elem in elements if elem.logical_type == 'relation')
        entities = sum(1 for elem in elements if elem.logical_type in ['line_of_identity', 'individual'])
        
        print(f"✓ Statistics calculation successful")
        print(f"  Total elements: {len(elements)}")
        print(f"  Contexts: {contexts}")
        print(f"  Predicates: {predicates}")
        print(f"  Entities: {entities}")
        
        # Verify expected results
        if contexts >= 2 and predicates == 2 and entities == 1:
            print("✓ Expected results achieved!")
            return True
        else:
            print(f"✗ Unexpected results: contexts={contexts}, predicates={predicates}, entities={entities}")
            return False
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("Testing GUI Integration Logic")
    print("=" * 50)
    
    success = test_gui_integration()
    
    if success:
        print("\n🎉 GUI integration logic is working correctly!")
        print("The issue must be in the actual PySide6 GUI rendering.")
    else:
        print("\n❌ GUI integration logic has issues that need fixing.")

if __name__ == "__main__":
    main()

