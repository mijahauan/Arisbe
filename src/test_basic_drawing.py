#!/usr/bin/env python3
"""
Simple test to verify basic drawing operations and diagnose PNG rendering issues.
"""

import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from canvas_backend import create_backend, EGDrawingStyles

def test_basic_drawing():
    """Test basic drawing operations"""
    print("🧪 TESTING BASIC DRAWING OPERATIONS")
    print("=" * 50)
    
    try:
        # Create tkinter backend
        print("1. Creating tkinter backend...")
        backend = create_backend("tkinter")
        canvas = backend.create_canvas(400, 300, "Test Canvas")
        
        print("2. Testing basic drawing operations...")
        
        # Draw a circle (vertex)
        canvas.draw_circle((100, 100), 10, EGDrawingStyles.VERTEX_SPOT)
        print("   ✓ Drew circle")
        
        # Draw a line (edge)
        canvas.draw_line((100, 100), (200, 150), EGDrawingStyles.EDGE_LINE)
        print("   ✓ Drew line")
        
        # Draw a curve (cut)
        curve_points = [(50, 50), (150, 50), (200, 100), (150, 150), (50, 150), (50, 50)]
        canvas.draw_curve(curve_points, EGDrawingStyles.CUT_LINE, closed=True)
        print("   ✓ Drew curve")
        
        # Draw text (relation)
        canvas.draw_text("test", (120, 120), EGDrawingStyles.RELATION_SIGN)
        print("   ✓ Drew text")
        
        # Update canvas
        canvas.update()
        
        # Check objects
        if hasattr(canvas, '_objects'):
            print(f"3. Canvas has {len(canvas._objects)} objects")
        
        # Test save
        print("4. Testing PNG save...")
        canvas.save_to_file("basic_test.png")
        
        # Check file
        if os.path.exists("basic_test.png"):
            size = os.path.getsize("basic_test.png")
            print(f"   ✅ PNG saved: {size} bytes")
            if size < 1000:
                print("   ⚠ File is small - may have minimal content")
            else:
                print("   ✅ File has substantial content")
        else:
            print("   ❌ PNG file not created")
        
        print("\n✅ Basic drawing test completed")
        return True
        
    except Exception as e:
        print(f"❌ Basic drawing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_basic_drawing()
