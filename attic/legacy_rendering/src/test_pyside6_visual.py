#!/usr/bin/env python3
"""
PySide6 Visual Tests for Existential Graph Rendering

This test creates visual demonstrations of EG diagrams using the PySide6 backend
to showcase the professional rendering quality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pyside6_backend import PySide6Backend
from canvas_backend import DrawingStyle
import math


def test_basic_eg_elements():
    """Test basic EG elements with PySide6 rendering."""
    
    print("🎨 Testing Basic EG Elements with PySide6")
    
    backend = PySide6Backend()
    if not backend.is_available():
        print("❌ PySide6 not available")
        return False
    
    canvas = backend.create_canvas(800, 600, "Basic EG Elements - PySide6")
    canvas.clear()
    
    # Title
    canvas.draw_text("Basic Existential Graph Elements", (250, 30), 
                    DrawingStyle(color=(0, 0, 0), font_size=18, font_family="Arial"))
    
    # 1. Individual (vertex/dot)
    canvas.draw_text("Individual:", (50, 80), DrawingStyle(font_size=14))
    canvas.draw_circle((150, 85), 3, DrawingStyle(color=(0, 0, 0), fill_color=(0, 0, 0)))
    
    # 2. Line of Identity (heavy line)
    canvas.draw_text("Line of Identity:", (50, 120), DrawingStyle(font_size=14))
    canvas.draw_line((180, 125), (280, 125), DrawingStyle(color=(0, 0, 0), line_width=3))
    
    # 3. Predicate
    canvas.draw_text("Predicate:", (50, 160), DrawingStyle(font_size=14))
    canvas.draw_text("Human", (150, 165), DrawingStyle(font_size=12))
    # Hook line to connect predicate to line of identity
    canvas.draw_line((185, 165), (220, 165), DrawingStyle(color=(0, 0, 0), line_width=1))
    canvas.draw_line((220, 160), (220, 170), DrawingStyle(color=(0, 0, 0), line_width=3))
    
    # 4. Cut (negation)
    canvas.draw_text("Cut (Negation):", (50, 220), DrawingStyle(font_size=14))
    # Draw an oval cut
    cut_points = []
    center_x, center_y = 200, 250
    for i in range(36):
        angle = i * 10 * math.pi / 180
        x = center_x + 60 * math.cos(angle)
        y = center_y + 30 * math.sin(angle)
        cut_points.append((x, y))
    canvas.draw_curve(cut_points, DrawingStyle(color=(0, 0, 0), line_width=1), closed=True)
    canvas.draw_text("Mortal", (175, 245), DrawingStyle(font_size=12))
    
    # 5. Complex example: (Human "Socrates") ~[ (Mortal "Socrates") ]
    canvas.draw_text("Example: (Human \"Socrates\") ~[ (Mortal \"Socrates\") ]", (50, 320), 
                    DrawingStyle(font_size=14, color=(0, 0, 128)))
    
    # Socrates line of identity
    canvas.draw_line((100, 360), (300, 360), DrawingStyle(color=(0, 0, 0), line_width=3))
    
    # Human predicate (outside cut)
    canvas.draw_text("Human", (80, 340), DrawingStyle(font_size=12))
    canvas.draw_line((115, 345), (115, 355), DrawingStyle(color=(0, 0, 0), line_width=1))
    
    # Cut around Mortal
    cut_points2 = []
    center_x2, center_y2 = 250, 360
    for i in range(36):
        angle = i * 10 * math.pi / 180
        x = center_x2 + 50 * math.cos(angle)
        y = center_y2 + 25 * math.sin(angle)
        cut_points2.append((x, y))
    canvas.draw_curve(cut_points2, DrawingStyle(color=(0, 0, 0), line_width=1), closed=True)
    
    # Mortal predicate (inside cut)
    canvas.draw_text("Mortal", (225, 355), DrawingStyle(font_size=12))
    canvas.draw_line((260, 350), (260, 365), DrawingStyle(color=(0, 0, 0), line_width=1))
    
    # Explanation
    canvas.draw_text("This reads: \"Socrates is Human, and it's not the case that Socrates is Mortal\"", 
                    (50, 420), DrawingStyle(font_size=11, color=(64, 64, 64)))
    
    canvas.show()
    
    # Run the Qt event loop to display the window
    print("   Window should now be visible - close it to continue...")
    canvas.run()
    return True


def test_complex_eg_diagram():
    """Test a more complex EG diagram."""
    
    print("🎨 Testing Complex EG Diagram with PySide6")
    
    backend = PySide6Backend()
    canvas = backend.create_canvas(900, 700, "Complex EG Diagram - PySide6")
    canvas.clear()
    
    # Title
    canvas.draw_text("Complex Existential Graph", (300, 30), 
                    DrawingStyle(color=(0, 0, 0), font_size=20, font_family="Arial"))
    
    # Example: *x *y (Human x) (Human y) ~[ (Loves x y) ]
    canvas.draw_text("*x *y (Human x) (Human y) ~[ (Loves x y) ]", (50, 70), 
                    DrawingStyle(font_size=14, color=(0, 0, 128)))
    
    # Variable x line
    canvas.draw_line((100, 120), (300, 120), DrawingStyle(color=(0, 0, 0), line_width=3))
    canvas.draw_text("x", (90, 115), DrawingStyle(font_size=12, color=(128, 0, 0)))
    
    # Variable y line  
    canvas.draw_line((100, 180), (300, 180), DrawingStyle(color=(0, 0, 0), line_width=3))
    canvas.draw_text("y", (90, 175), DrawingStyle(font_size=12, color=(128, 0, 0)))
    
    # Human x predicate
    canvas.draw_text("Human", (120, 100), DrawingStyle(font_size=12))
    canvas.draw_line((155, 105), (155, 115), DrawingStyle(color=(0, 0, 0), line_width=1))
    
    # Human y predicate
    canvas.draw_text("Human", (120, 200), DrawingStyle(font_size=12))
    canvas.draw_line((155, 195), (155, 185), DrawingStyle(color=(0, 0, 0), line_width=1))
    
    # Cut around Loves relation
    cut_points = []
    center_x, center_y = 500, 150
    for i in range(36):
        angle = i * 10 * math.pi / 180
        x = center_x + 120 * math.cos(angle)
        y = center_y + 60 * math.sin(angle)
        cut_points.append((x, y))
    canvas.draw_curve(cut_points, DrawingStyle(color=(0, 0, 0), line_width=1), closed=True)
    
    # Loves predicate (inside cut)
    canvas.draw_text("Loves", (470, 145), DrawingStyle(font_size=12))
    
    # Connection lines from x and y to Loves (crossing cut boundary)
    canvas.draw_line((300, 120), (450, 140), DrawingStyle(color=(0, 0, 0), line_width=1))
    canvas.draw_line((300, 180), (450, 160), DrawingStyle(color=(0, 0, 0), line_width=1))
    
    # Argument labels for binary relation
    canvas.draw_text("1", (440, 135), DrawingStyle(font_size=10, color=(128, 128, 128)))
    canvas.draw_text("2", (440, 165), DrawingStyle(font_size=10, color=(128, 128, 128)))
    
    # Explanation
    canvas.draw_text("This reads: \"There exist x and y such that x is Human and y is Human,\"", 
                    (50, 300), DrawingStyle(font_size=12, color=(64, 64, 64)))
    canvas.draw_text("\"and it's not the case that x Loves y\"", 
                    (50, 320), DrawingStyle(font_size=12, color=(64, 64, 64)))
    
    # Visual conventions note
    canvas.draw_text("Visual Conventions (following Dau):", (50, 380), 
                    DrawingStyle(font_size=14, color=(0, 0, 128)))
    canvas.draw_text("• Heavy lines = Lines of Identity (individuals)", (70, 410), 
                    DrawingStyle(font_size=11))
    canvas.draw_text("• Fine lines = Hooks connecting predicates to arguments", (70, 430), 
                    DrawingStyle(font_size=11))
    canvas.draw_text("• Closed curves = Cuts (negation boundaries)", (70, 450), 
                    DrawingStyle(font_size=11))
    canvas.draw_text("• Numbers = Argument positions for n-ary relations", (70, 470), 
                    DrawingStyle(font_size=11))
    
    canvas.show()
    
    # Run the Qt event loop to display the window
    print("   Window should now be visible - close it to continue...")
    canvas.run()
    return True


def test_rendering_quality():
    """Test rendering quality features of PySide6."""
    
    print("🎨 Testing PySide6 Rendering Quality")
    
    backend = PySide6Backend()
    canvas = backend.create_canvas(600, 500, "PySide6 Rendering Quality Test")
    canvas.clear()
    
    # Title
    canvas.draw_text("PySide6 Professional Rendering Quality", (120, 30), 
                    DrawingStyle(color=(0, 0, 0), font_size=16, font_family="Arial"))
    
    # Anti-aliased curves
    canvas.draw_text("Anti-aliased Curves:", (50, 80), DrawingStyle(font_size=14))
    
    # Smooth curves
    curve1 = [(100, 120), (150, 100), (200, 120), (250, 100), (300, 120)]
    canvas.draw_curve(curve1, DrawingStyle(color=(255, 0, 0), line_width=2))
    
    curve2 = [(100, 140), (150, 160), (200, 140), (250, 160), (300, 140)]
    canvas.draw_curve(curve2, DrawingStyle(color=(0, 128, 255), line_width=3))
    
    # Precise circles
    canvas.draw_text("Precise Circles:", (50, 200), DrawingStyle(font_size=14))
    
    for i, radius in enumerate([10, 15, 20, 25]):
        x = 120 + i * 60
        canvas.draw_circle((x, 240), radius, 
                          DrawingStyle(color=(0, 128, 0), line_width=2))
    
    # Typography quality
    canvas.draw_text("High-Quality Typography:", (50, 320), DrawingStyle(font_size=14))
    
    fonts_and_sizes = [
        ("Arial", 12), ("Arial", 16), ("Times", 14), ("Courier", 12)
    ]
    
    for i, (font, size) in enumerate(fonts_and_sizes):
        y = 350 + i * 25
        canvas.draw_text(f"{font} {size}pt: Existential Graphs", (70, y), 
                        DrawingStyle(font_family=font, font_size=size))
    
    canvas.show()
    
    # Run the Qt event loop to display the window
    print("   Window should now be visible - close it to continue...")
    canvas.run()
    return True


if __name__ == "__main__":
    print("🚀 PySide6 Visual Tests for Existential Graphs")
    print("=" * 60)
    
    tests = [
        ("Basic EG Elements", test_basic_eg_elements),
        ("Complex EG Diagram", test_complex_eg_diagram),
        ("Rendering Quality", test_rendering_quality)
    ]
    
    for test_name, test_func in tests:
        print(f"\n🎯 Running: {test_name}")
        try:
            success = test_func()
            if success:
                print(f"✓ {test_name} completed successfully")
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} error: {e}")
    
    print(f"\n🎉 Visual tests completed!")
    print("Close the windows when you're done viewing the diagrams.")
