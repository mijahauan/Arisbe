#!/usr/bin/env python3
"""
Fix Predicate ID Error

The predicate_id is a UUID object, not a string, so len() doesn't work.
This script fixes the text width calculation.
"""

import sys
from pathlib import Path

def fix_predicate_id_usage():
    """Fix the predicate_id usage in _calculate_safe_predicate_position."""
    
    egrf_generator_path = Path("/home/ubuntu/EG-CL-Manus2/src/egrf/egrf_generator.py")
    
    # Read current content
    with open(egrf_generator_path, 'r') as f:
        content = f.read()
    
    # Find and fix the text width calculation
    old_calculation = '''        text_width = len(predicate_id) * 8 + 20  # Estimate text width'''
    
    new_calculation = '''        # Get predicate name for text width calculation
        predicate = eg_graph.predicates[predicate_id]
        predicate_name = predicate.name
        text_width = len(predicate_name) * 8 + 20  # Estimate text width'''
    
    if old_calculation in content:
        content = content.replace(old_calculation, new_calculation)
        print("✅ Fixed predicate_id text width calculation")
    else:
        print("❌ Could not find the text width calculation to fix")
        return False
    
    # Also fix the debug output that might have the same issue
    old_debug = '''        print(f"DEBUG: Predicate {predicate_id} positioned at ({safe_x}, {safe_y}) within context bounds")'''
    
    new_debug = '''        print(f"DEBUG: Predicate {predicate_name} positioned at ({safe_x}, {safe_y}) within context bounds")'''
    
    if old_debug in content:
        content = content.replace(old_debug, new_debug)
        print("✅ Fixed debug output predicate reference")
    
    # Write updated content back
    with open(egrf_generator_path, 'w') as f:
        f.write(content)
    
    return True

def main():
    """Fix the predicate ID UUID error."""
    
    print("🔧 FIXING PREDICATE ID UUID ERROR")
    print("=" * 40)
    
    try:
        success = fix_predicate_id_usage()
        
        if success:
            print("✅ Predicate ID usage fixed successfully")
            print("✅ Text width calculation now uses predicate name")
            return True
        else:
            print("❌ Failed to fix predicate ID usage")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

