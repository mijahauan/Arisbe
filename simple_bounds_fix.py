#!/usr/bin/env python3
"""
Simple fix for the bounds validation issue.
Patches the layout engine to ensure valid bounds.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def fix_bounds_calculation(x1, y1, x2, y2, padding):
    """Fix bounds calculation to ensure valid results."""
    width = x2 - x1
    height = y2 - y1
    
    # If padding would create invalid bounds, reduce it
    if padding * 2 >= width or padding * 2 >= height:
        padding = min(width / 3, height / 3)
    
    new_x1 = x1 + padding
    new_y1 = y1 + padding
    new_x2 = x2 - padding
    new_y2 = y2 - padding
    
    # Final validation
    if new_x2 <= new_x1:
        new_x2 = new_x1 + 20  # Minimum 20px width
    if new_y2 <= new_y1:
        new_y2 = new_y1 + 20  # Minimum 20px height
    
    return (new_x1, new_y1, new_x2, new_y2)

def test_bounds_fix():
    """Test the bounds fix with the problematic case."""
    
    # The problematic case from debug output
    cut_bounds = (50, 50, 134.0, 120)
    padding = 50.0
    
    print(f"Original cut bounds: {cut_bounds}")
    print(f"Padding: {padding}")
    
    # Old calculation (broken)
    x1, y1, x2, y2 = cut_bounds
    old_bounds = (x1 + padding, y1 + padding, x2 - padding, y2 - padding)
    print(f"Old available bounds: {old_bounds}")
    print(f"Old bounds valid: {old_bounds[2] > old_bounds[0] and old_bounds[3] > old_bounds[1]}")
    
    # New calculation (fixed)
    new_bounds = fix_bounds_calculation(x1, y1, x2, y2, padding)
    print(f"New available bounds: {new_bounds}")
    print(f"New bounds valid: {new_bounds[2] > new_bounds[0] and new_bounds[3] > new_bounds[1]}")

if __name__ == "__main__":
    test_bounds_fix()
