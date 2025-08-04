#!/usr/bin/env python3
"""
Direct rendering test to debug why nothing displays on canvas.
This bypasses the complex pipeline and directly draws elements.
"""

import tkinter as tk
from diagram_renderer_clean import TkinterCanvas

def test_direct_canvas_drawing():
    """Test direct drawing on Tkinter canvas to verify basic functionality."""
    
    print("=== Testing Direct Canvas Drawing ===")
    
    # Create window and canvas
    root = tk.Tk()
    root.title("Direct Canvas Drawing Test")
    root.geometry("800x600")
    
    tk_canvas = tk.Canvas(root, width=800, height=600, bg='white')
    tk_canvas.pack(expand=True, fill='both')
    
    # Test direct Tkinter drawing
    print("Drawing directly with Tkinter...")
    tk_canvas.create_text(400, 50, text="Direct Tkinter Drawing Test", font=("Arial", 16), fill="blue")
    tk_canvas.create_circle = lambda x1, y1, x2, y2, **kwargs: tk_canvas.create_oval(x1, y1, x2, y2, **kwargs)
    
    # Draw some basic shapes
    tk_canvas.create_circle(200, 200, 250, 250, fill="lightblue", outline="black", width=2)  # Circle
    tk_canvas.create_rectangle(500, 200, 600, 300, fill="lightyellow", outline="black", width=2)  # Rectangle
    tk_canvas.create_line(250, 225, 500, 250, width=3, fill="red")  # Line
    
    tk_canvas.create_text(225, 225, text="Vertex", font=("Arial", 12), fill="black")
    tk_canvas.create_text(550, 250, text="Predicate", font=("Arial", 12), fill="black")
    
    print("✓ Direct Tkinter drawing completed")
    
    # Test TkinterCanvas wrapper
    print("\nTesting TkinterCanvas wrapper...")
    canvas = TkinterCanvas(tk_canvas)
    
    # Draw using our wrapper
    canvas.draw_circle(center=(300, 400), radius=25, fill_color="lightgreen", outline_color="darkgreen", outline_width=2)
    canvas.draw_text(position=(300, 450), text="TkinterCanvas", font_size=12, color="darkgreen")
    canvas.draw_line(start=(100, 400), end=(200, 400), width=3, color="purple")
    
    print("✓ TkinterCanvas wrapper drawing completed")
    
    # Show result
    print("\nShowing test window...")
    print("You should see:")
    print("  - Blue title text")
    print("  - Light blue circle with 'Vertex' label")
    print("  - Light yellow rectangle with 'Predicate' label") 
    print("  - Red line connecting them")
    print("  - Light green circle with 'TkinterCanvas' label")
    print("  - Purple line")
    
    root.mainloop()

def test_coordinate_transformation():
    """Test if coordinate transformation is the issue."""
    
    print("\n=== Testing Coordinate Transformation ===")
    
    # The extracted coordinates from our debug output
    extracted_coords = {
        'v_0': (65.0, -73.46),      # Plato vertex
        'p_1': (70.4, -166.52),     # Mortal predicate  
        'v_2': (172.0, -73.46),     # Socrates vertex
        'p_3': (177.4, -166.52)     # Human predicate
    }
    
    print("Extracted coordinates from SVG:")
    for name, (x, y) in extracted_coords.items():
        print(f"  {name}: ({x}, {y})")
    
    print("\nIssue analysis:")
    print("  - Y coordinates are NEGATIVE (SVG coordinate system)")
    print("  - Tkinter expects POSITIVE Y coordinates")
    print("  - Need coordinate transformation: SVG → Tkinter")
    
    # Create window to test coordinate transformation
    root = tk.Tk()
    root.title("Coordinate Transformation Test")
    root.geometry("800x600")
    
    tk_canvas = tk.Canvas(root, width=800, height=600, bg='white')
    tk_canvas.pack(expand=True, fill='both')
    
    tk_canvas.create_text(400, 30, text="Coordinate Transformation Test", font=("Arial", 16), fill="blue")
    
    # Transform coordinates: flip Y and offset to center
    canvas_width, canvas_height = 800, 600
    svg_min_y = -200  # Approximate from our data
    svg_max_y = 0
    
    def transform_coords(svg_x, svg_y):
        # Center horizontally, flip Y vertically
        tkinter_x = svg_x + 300  # Offset to center
        tkinter_y = canvas_height - (svg_y - svg_min_y + 50)  # Flip Y and offset
        return tkinter_x, tkinter_y
    
    print("\nTransformed coordinates:")
    colors = ['red', 'blue', 'green', 'orange']
    for i, (name, (svg_x, svg_y)) in enumerate(extracted_coords.items()):
        tk_x, tk_y = transform_coords(svg_x, svg_y)
        print(f"  {name}: SVG({svg_x}, {svg_y}) → Tkinter({tk_x}, {tk_y})")
        
        # Draw at transformed position
        color = colors[i % len(colors)]
        if name.startswith('v_'):
            # Vertex - circle
            tk_canvas.create_oval(tk_x-15, tk_y-15, tk_x+15, tk_y+15, 
                                fill="lightblue", outline=color, width=2)
            tk_canvas.create_text(tk_x, tk_y+25, text=name, font=("Arial", 10), fill=color)
        else:
            # Predicate - rectangle
            tk_canvas.create_rectangle(tk_x-20, tk_y-10, tk_x+20, tk_y+10, 
                                     fill="lightyellow", outline=color, width=2)
            tk_canvas.create_text(tk_x, tk_y+20, text=name, font=("Arial", 10), fill=color)
    
    tk_canvas.create_text(400, 550, text="If you see colored shapes, coordinate transformation works!", 
                        font=("Arial", 12), fill="darkgreen")
    
    print("\nShowing coordinate transformation test...")
    root.mainloop()

if __name__ == "__main__":
    print("🔍 Debugging Display Issue")
    
    # Test direct canvas drawing
    test_direct_canvas_drawing()
    
    # Test coordinate transformation
    test_coordinate_transformation()
    
    print("\n📊 Analysis:")
    print("If direct drawing works but our pipeline doesn't, the issue is in:")
    print("  1. Coordinate transformation (SVG → Tkinter)")
    print("  2. Primitive rendering logic")
    print("  3. Canvas method calls")
