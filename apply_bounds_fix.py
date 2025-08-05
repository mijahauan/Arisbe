#!/usr/bin/env python3
"""
Apply the bounds fix directly to the layout engine source code.
This will fix the containment bug by ensuring valid bounds calculations.
"""

import sys
import os

def apply_bounds_fix():
    """Apply the bounds fix to the layout engine source file."""
    
    layout_engine_path = os.path.join(os.path.dirname(__file__), 'src', 'layout_engine.py')
    
    # Read the current file
    with open(layout_engine_path, 'r') as f:
        content = f.read()
    
    # Find and replace the problematic bounds calculation
    old_bounds_calc = """                    available_bounds = (
                        x1 + self.cut_padding,
                        y1 + self.cut_padding,
                        x2 - self.cut_padding,
                        y2 - self.cut_padding
                    )"""
    
    new_bounds_calc = """                    # CRITICAL FIX: Ensure padding doesn't create invalid bounds
                    width = x2 - x1
                    height = y2 - y1
                    max_padding = min(width / 3, height / 3, self.cut_padding)
                    
                    available_bounds = (
                        x1 + max_padding,
                        y1 + max_padding,
                        x2 - max_padding,
                        y2 - max_padding
                    )"""
    
    if old_bounds_calc in content:
        # Apply the fix
        fixed_content = content.replace(old_bounds_calc, new_bounds_calc)
        
        # Write back the fixed file
        with open(layout_engine_path, 'w') as f:
            f.write(fixed_content)
        
        print("✅ Applied bounds fix to layout_engine.py")
        print("   Fixed invalid bounds calculation that was causing containment violations")
        return True
    else:
        print("❌ Could not find the target bounds calculation to fix")
        print("   The layout engine may have been modified")
        return False

def test_fix():
    """Test that the fix resolves the containment issue."""
    
    # Import after applying the fix
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
    from egif_parser_dau import EGIFParser
    from layout_engine import LayoutEngine
    
    # Test the problematic case
    egif_text = '*x (Human x) ~[ (Mortal x) ]'
    parser = EGIFParser(egif_text)
    egi = parser.parse()
    
    layout_engine = LayoutEngine()
    layout_result = layout_engine.layout_graph(egi)
    
    # Find cut bounds
    cut_bounds = None
    cut_id = None
    for element_id, layout_element in layout_result.elements.items():
        if layout_element.element_type == 'cut':
            cut_bounds = layout_element.bounds
            cut_id = element_id
            break
    
    if not cut_bounds:
        print("❌ No cut found in layout")
        return False
    
    cut_x1, cut_y1, cut_x2, cut_y2 = cut_bounds
    print(f"Cut bounds: ({cut_x1}, {cut_y1}) to ({cut_x2}, {cut_y2})")
    
    # Check containment
    containment_correct = True
    for element_id, layout_element in layout_result.elements.items():
        if layout_element.element_type == 'edge':
            relation_name = egi.rel.get(element_id, f"Unknown_{element_id}")
            pred_x, pred_y = layout_element.position
            expected_area = layout_element.parent_area
            
            should_be_in_cut = (expected_area == cut_id)
            inside_cut = (cut_x1 <= pred_x <= cut_x2 and cut_y1 <= pred_y <= cut_y2)
            
            print(f"{relation_name}: position ({pred_x:.1f}, {pred_y:.1f})")
            print(f"  Should be in cut: {should_be_in_cut}")
            print(f"  Actually in cut: {inside_cut}")
            
            if should_be_in_cut != inside_cut:
                print(f"  ❌ CONTAINMENT ERROR!")
                containment_correct = False
            else:
                print(f"  ✅ CONTAINMENT CORRECT!")
    
    return containment_correct

if __name__ == "__main__":
    print("Applying bounds fix to layout engine...")
    
    if apply_bounds_fix():
        print("\nTesting the fix...")
        if test_fix():
            print("\n🎉 SUCCESS: Containment bug fixed!")
        else:
            print("\n❌ FAILURE: Containment issues remain")
    else:
        print("\n❌ Could not apply the fix")
