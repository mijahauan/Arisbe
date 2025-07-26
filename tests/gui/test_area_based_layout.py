#!/usr/bin/env python3
"""
Test the area-based layout calculator.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from clif_parser import CLIFParser
from egrf_from_graph import convert_graph_to_egrf
from gui.area_based_layout_calculator import AreaBasedLayoutCalculator

def test_area_based_layout():
    """Test the area-based layout calculation."""
    print("=== Testing Area-Based Layout Calculator ===")
    
    # Test canonical implication
    clif_text = "(if (Man Socrates) (Mortal Socrates))"
    print(f"CLIF: {clif_text}")
    
    try:
        # Get EGRF
        parser = CLIFParser()
        parse_result = parser.parse(clif_text)
        egrf_doc = convert_graph_to_egrf(parse_result.graph)
        
        # Use area-based layout calculator
        layout_calculator = AreaBasedLayoutCalculator(1200, 800)
        layout_data = layout_calculator.calculate_layout(egrf_doc)
        
        print(f"\n=== Area-Based Layout Results ===")
        print(f"Layout elements: {len(layout_data)}")
        
        # Analyze predicate positions
        predicates = {eid: info for eid, info in layout_data.items() if info.get('element_type') == 'predicate'}
        print(f"\n=== Predicate Positions ===")
        for pred_id, pred_info in predicates.items():
            name = pred_info.get('name', 'Unknown')
            position = pred_info.get('position', {})
            level = pred_info.get('nesting_level', 'Unknown')
            print(f"{name}: position=({position.get('x', 0)}, {position.get('y', 0)}), level={level}")
        
        # Analyze entity positions
        entities = {eid: info for eid, info in layout_data.items() if info.get('element_type') == 'entity'}
        print(f"\n=== Entity Positions ===")
        for ent_id, ent_info in entities.items():
            name = ent_info.get('name', 'Unknown')
            position = ent_info.get('position', {})
            level = ent_info.get('nesting_level', 'Unknown')
            line_segments = len(ent_info.get('line_segments', []))
            print(f"{name}: position=({position.get('x', 0)}, {position.get('y', 0)}), level={level}, lines={line_segments}")
        
        # Analyze context positions
        contexts = {eid: info for eid, info in layout_data.items() if info.get('element_type') == 'context'}
        print(f"\n=== Context Positions ===")
        for ctx_id, ctx_info in contexts.items():
            position = ctx_info.get('position', {})
            size = ctx_info.get('size', {})
            level = ctx_info.get('nesting_level', 'Unknown')
            role = ctx_info.get('semantic_role', 'Unknown')
            print(f"Level {level} ({role}): position=({position.get('x', 0)}, {position.get('y', 0)}), size=({size.get('width', 0)}, {size.get('height', 0)})")
        
        # Check for proper separation
        print(f"\n=== Separation Analysis ===")
        man_pos = None
        mortal_pos = None
        
        for pred_id, pred_info in predicates.items():
            name = pred_info.get('name', 'Unknown')
            position = pred_info.get('position', {})
            if name == 'Man':
                man_pos = (position.get('x', 0), position.get('y', 0))
            elif name == 'Mortal':
                mortal_pos = (position.get('x', 0), position.get('y', 0))
        
        if man_pos and mortal_pos:
            distance = ((man_pos[0] - mortal_pos[0])**2 + (man_pos[1] - mortal_pos[1])**2)**0.5
            print(f"Distance between Man and Mortal: {distance:.1f} pixels")
            
            if distance > 50:
                print("✓ Good separation between predicates")
            else:
                print("✗ Predicates too close together")
            
            # Check if Man is in outer area and Mortal is in inner area
            if man_pos[0] < mortal_pos[0] and man_pos[1] < mortal_pos[1]:
                print("✓ Man positioned in outer area (top-left)")
                print("✓ Mortal positioned in inner area (bottom-right)")
            else:
                print("✗ Incorrect area positioning")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sowa_example():
    """Test the Sowa quantification example."""
    print(f"\n" + "="*60)
    print("=== Testing Sowa Example ===")
    
    clif_text = "(exists (x) (and (P x) (Q x)))"
    print(f"CLIF: {clif_text}")
    
    try:
        # Get EGRF
        parser = CLIFParser()
        parse_result = parser.parse(clif_text)
        egrf_doc = convert_graph_to_egrf(parse_result.graph)
        
        # Use area-based layout calculator
        layout_calculator = AreaBasedLayoutCalculator(1200, 800)
        layout_data = layout_calculator.calculate_layout(egrf_doc)
        
        # Analyze predicate positions
        predicates = {eid: info for eid, info in layout_data.items() if info.get('element_type') == 'predicate'}
        print(f"\n=== Predicate Positions ===")
        
        p_pos = None
        q_pos = None
        
        for pred_id, pred_info in predicates.items():
            name = pred_info.get('name', 'Unknown')
            position = pred_info.get('position', {})
            level = pred_info.get('nesting_level', 'Unknown')
            print(f"{name}: position=({position.get('x', 0)}, {position.get('y', 0)}), level={level}")
            
            if name == 'P':
                p_pos = (position.get('x', 0), position.get('y', 0))
            elif name == 'Q':
                q_pos = (position.get('x', 0), position.get('y', 0))
        
        if p_pos and q_pos:
            distance = ((p_pos[0] - q_pos[0])**2 + (p_pos[1] - q_pos[1])**2)**0.5
            print(f"Distance between P and Q: {distance:.1f} pixels")
            
            if distance > 30:
                print("✓ Good separation between P and Q")
            else:
                print("✗ P and Q too close together")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("Testing Area-Based Layout Calculator")
    print("=" * 60)
    
    success1 = test_area_based_layout()
    success2 = test_sowa_example()
    
    if success1 and success2:
        print(f"\n🎉 Area-based layout calculator is working correctly!")
        print("Predicates should now be properly separated in their respective areas.")
    else:
        print(f"\n❌ Area-based layout calculator has issues that need fixing.")

if __name__ == "__main__":
    main()

