#!/usr/bin/env python3
"""
Fix Final Test Validation

There's still one more section using .get() on PredicateVisual objects.
This script fixes the final validation section.
"""

import sys
from pathlib import Path

def fix_final_validation():
    """Fix the final validation section in the test."""
    
    test_file_path = Path("/home/ubuntu/test_critical_fixes.py")
    
    # Read current content
    with open(test_file_path, 'r') as f:
        content = f.read()
    
    # Find and fix the artifacts validation
    old_validation = '''        # Check visual artifacts elimination
        artifacts_eliminated = all(
            pred.visual.get("artifacts") == "none" and
            pred.visual.get("center_dot") == "none" and
            pred.visual.get("stroke", {}).get("width", 0) == 0.0
            for pred in egrf_doc.predicates
        )'''
    
    new_validation = '''        # Check visual artifacts elimination (PredicateVisual objects)
        artifacts_eliminated = all(
            pred.visual.style == "none" and
            pred.visual.size.width == 0 and
            pred.visual.size.height == 0 and
            pred.visual.stroke.width == 0.0 and
            pred.visual.fill.opacity == 0.0
            for pred in egrf_doc.predicates
        )'''
    
    if old_validation in content:
        content = content.replace(old_validation, new_validation)
        print("✅ Fixed artifacts validation section")
    
    # Also fix the shading consistency check
    old_shading_check = '''        for context in egrf_doc.contexts:
            level = context.visual.get("peirce_level", "unknown")
            fill = context.visual.get("fill", {})
            
            if level == 0:
                level_0_fill = fill
            elif level != "unknown" and level % 2 == 0:
                even_fills.append(fill)'''
    
    new_shading_check = '''        for context in egrf_doc.contexts:
            # Get level from context attributes (may need to be added to context)
            level = getattr(context, "peirce_level", None)
            fill = getattr(context.visual, "fill", None) if hasattr(context, "visual") else None
            
            if level == 0:
                level_0_fill = fill
            elif level is not None and level % 2 == 0:
                even_fills.append(fill)'''
    
    if old_shading_check in content:
        content = content.replace(old_shading_check, new_shading_check)
        print("✅ Fixed shading consistency check")
    
    # Write updated content back
    with open(test_file_path, 'w') as f:
        f.write(content)
    
    return True

def main():
    """Fix the final test validation."""
    
    print("🔧 FIXING FINAL TEST VALIDATION")
    print("=" * 40)
    
    try:
        success = fix_final_validation()
        
        if success:
            print("✅ Final test validation fixed")
            print("✅ Updated to use PredicateVisual object attributes")
            return True
        else:
            print("❌ Failed to fix final validation")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

