#!/usr/bin/env python3
"""
Targeted fix for containment positioning bug in layout engine.
Specifically addresses Roberts' Disjunction issue where predicates are positioned outside container bounds.
"""

import sys
import os

# Add src to path
src_path = os.path.join(os.path.dirname(__file__), 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

def fix_layout_engine_containment():
    """Apply targeted fix to layout engine containment positioning."""
    
    layout_engine_path = os.path.join(src_path, 'layout_engine.py')
    
    # Read current content
    with open(layout_engine_path, 'r') as f:
        content = f.read()
    
    # Find and replace the problematic bounds calculation for unary predicates
    old_bounds_calc = '''                # Get available space within the edge's containing area
                if edge_containing_area and edge_containing_area in all_layouts:
                    container_bounds = all_layouts[edge_containing_area].bounds
                    # Inset from container bounds
                    x1, y1, x2, y2 = container_bounds
                    # CRITICAL FIX: Ensure padding doesn't create invalid bounds
                    width = x2 - x1
                    height = y2 - y1
                    max_padding = min(width / 3, height / 3, self.cut_padding)
                    
                    available_bounds = (
                        x1 + max_padding,
                        y1 + max_padding,
                        x2 - max_padding,
                        y2 - max_padding
                    )'''
    
    new_bounds_calc = '''                # CRITICAL FIX: Get available space within the edge's specific containing area
                if edge_containing_area and edge_containing_area in all_layouts:
                    container_bounds = all_layouts[edge_containing_area].bounds
                    x1, y1, x2, y2 = container_bounds
                    
                    # Validate container bounds first
                    if x2 <= x1 or y2 <= y1:
                        print(f"ERROR: Invalid container bounds for {edge.id} in {edge_containing_area}: {container_bounds}")
                        # Fallback to sheet bounds
                        available_bounds = (
                            self.margin,
                            self.margin,
                            self.canvas_width - self.margin,
                            self.canvas_height - self.margin
                        )
                    else:
                        # Calculate safe padding that ensures predicates stay within bounds
                        width = x2 - x1
                        height = y2 - y1
                        # Use more conservative padding to ensure containment
                        safe_padding = min(width / 6, height / 6, 10)
                        
                        available_bounds = (
                            x1 + safe_padding,
                            y1 + safe_padding,
                            x2 - safe_padding,
                            y2 - safe_padding
                        )
                        
                        # Final validation to ensure bounds are valid
                        ax1, ay1, ax2, ay2 = available_bounds
                        if ax2 <= ax1 or ay2 <= ay1:
                            # Use minimal padding as absolute last resort
                            available_bounds = (x1 + 1, y1 + 1, x2 - 1, y2 - 1)'''
    
    if old_bounds_calc in content:
        content = content.replace(old_bounds_calc, new_bounds_calc)
        
        # Write back the fixed content
        with open(layout_engine_path, 'w') as f:
            f.write(content)
        
        print("✅ Applied containment positioning fix to layout engine")
        return True
    else:
        print("❌ Could not find target code section to fix")
        return False

if __name__ == "__main__":
    if fix_layout_engine_containment():
        print("🔧 Containment fix applied - test with debug script")
    else:
        print("❌ Fix failed - manual intervention required")
