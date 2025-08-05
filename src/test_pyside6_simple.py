#!/usr/bin/env python3
"""
Simple PySide6 Backend Test

Tests the PySide6 backend implementation without external dependencies.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pyside6_backend import PySide6Backend, PySide6Canvas
from canvas_backend import DrawingStyle


def test_pyside6_basic():
    """Test basic PySide6 backend functionality."""
    
    print("🧪 Testing PySide6 Backend - Basic Functionality")
    print("=" * 50)
    
    try:
        # Check if PySide6 is available
        backend = PySide6Backend()
        if not backend.is_available():
            print("❌ PySide6 not available - skipping test")
            return False
        
        print("✓ PySide6 backend available")
        
        # Create canvas
        canvas = backend.create_canvas(600, 400, "PySide6 Simple Test")
        print("✓ Canvas created successfully")
        
        # Test drawing operations
        canvas.clear()
        print("✓ Canvas cleared")
        
        # Draw test elements
        canvas.draw_line((50, 50), (550, 350), 
                        DrawingStyle(color=(0, 0, 255), line_width=3))
        print("✓ Line drawn")
        
        canvas.draw_circle((300, 200), 60, 
                          DrawingStyle(color=(255, 0, 0), fill_color=(255, 255, 0)))
        print("✓ Circle drawn")
        
        canvas.draw_text("PySide6 Backend Working!", (150, 100), 
                        DrawingStyle(color=(0, 128, 0), font_size=18, font_family="Arial"))
        print("✓ Text drawn")
        
        # Test curve
        curve_points = [(100, 300), (200, 250), (300, 300), (400, 250), (500, 300)]
        canvas.draw_curve(curve_points, DrawingStyle(color=(128, 0, 128), line_width=2))
        print("✓ Curve drawn")
        
        # Test polygon
        triangle_points = [(450, 100), (500, 50), (550, 100)]
        canvas.draw_polygon(triangle_points, 
                           DrawingStyle(color=(255, 128, 0), fill_color=(255, 200, 100)))
        print("✓ Polygon drawn")
        
        # Test text bounds
        bounds = canvas.get_text_bounds("Test", DrawingStyle(font_size=12))
        print(f"✓ Text bounds: {bounds}")
        
        # Update canvas
        canvas.update()
        print("✓ Canvas updated")
        
        # Show the window
        canvas.show()
        print("✓ Window displayed")
        
        print("\n🎉 All basic PySide6 tests passed!")
        print("   Close the window to continue...")
        
        # Run briefly to show the window
        # Note: In a real application, this would be canvas.run()
        return True
        
    except Exception as e:
        print(f"❌ PySide6 test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pyside6_protocol_compliance():
    """Test Canvas protocol compliance."""
    
    print("\n🔍 Testing Canvas Protocol Compliance")
    print("=" * 40)
    
    try:
        backend = PySide6Backend()
        canvas = backend.create_canvas(200, 200, "Protocol Test")
        
        # Test required methods
        methods_to_test = [
            ('clear', lambda: canvas.clear()),
            ('draw_line', lambda: canvas.draw_line((0, 0), (100, 100), DrawingStyle())),
            ('draw_circle', lambda: canvas.draw_circle((50, 50), 25, DrawingStyle())),
            ('draw_text', lambda: canvas.draw_text("Test", (10, 10), DrawingStyle())),
            ('update', lambda: canvas.update()),
            ('bind_event', lambda: canvas.bind_event('<Button-1>', lambda e: None)),
        ]
        
        for method_name, test_func in methods_to_test:
            try:
                test_func()
                print(f"✓ {method_name} works correctly")
            except Exception as e:
                print(f"❌ {method_name} failed: {e}")
                return False
        
        print("✓ All protocol methods working")
        return True
        
    except Exception as e:
        print(f"❌ Protocol test failed: {e}")
        return False


if __name__ == "__main__":
    print("🚀 PySide6 Backend Simple Tests")
    print("=" * 40)
    
    # Test protocol compliance first
    protocol_ok = test_pyside6_protocol_compliance()
    
    # Test basic functionality
    basic_ok = test_pyside6_basic()
    
    print(f"\n📊 Results:")
    print(f"Protocol: {'✓ PASS' if protocol_ok else '❌ FAIL'}")
    print(f"Basic:    {'✓ PASS' if basic_ok else '❌ FAIL'}")
    
    if protocol_ok and basic_ok:
        print("\n🎉 PySide6 backend is working correctly!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)
