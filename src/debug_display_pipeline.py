#!/usr/bin/env python3
"""
Debug script to test the exact display pipeline used in _update_display().
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from egif_parser_dau import EGIFParser
from content_driven_layout import ContentDrivenLayoutEngine
from diagram_renderer_clean import CleanDiagramRenderer
from tkinter_backend import TkinterCanvas

def test_display_pipeline():
    """Test the exact sequence used in _update_display()."""
    
    print("=== TESTING DISPLAY PIPELINE ===")
    
    # Step 1: Parse the same EGIF used in _load_example()
    egif_text = '(Human "Socrates") ~[ (Mortal "Socrates") ]'
    print(f"1. Parsing EGIF: {egif_text}")
    
    try:
        parser = EGIFParser(egif_text)
        graph = parser.parse()
        print(f"   ✓ Graph parsed: {len(graph.V)} vertices, {len(graph.E)} edges, {len(graph.Cut)} cuts")
    except Exception as e:
        print(f"   ✗ Parse failed: {e}")
        return
    
    # Step 2: Create layout engine (same as in IntegratedEGEditor)
    print("\n2. Creating ContentDrivenLayoutEngine...")
    try:
        layout_engine = ContentDrivenLayoutEngine()
        print(f"   ✓ Layout engine created")
    except Exception as e:
        print(f"   ✗ Layout engine creation failed: {e}")
        return
    
    # Step 3: Generate layout
    print("\n3. Generating layout...")
    try:
        layout_result = layout_engine.layout_graph(graph)
        print(f"   ✓ Layout generated")
        print(f"   - Type: {type(layout_result)}")
        print(f"   - Primitives count: {len(layout_result.primitives)}")
        print(f"   - Canvas bounds: {layout_result.canvas_bounds}")
        
        # List all primitives
        for element_id, primitive in layout_result.primitives.items():
            print(f"   - {primitive.element_type} {element_id[-8:]}: pos={primitive.position}, bounds={primitive.bounds}")
            
    except Exception as e:
        print(f"   ✗ Layout generation failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 4: Create canvas and renderer (same as in IntegratedEGEditor)
    print("\n4. Creating canvas and renderer...")
    try:
        root = tk.Tk()
        root.title("Debug Display Pipeline")
        root.geometry("800x600")
        
        canvas = TkinterCanvas(800, 600, title="Debug Canvas", master=root)
        canvas.tk_canvas.pack(fill=tk.BOTH, expand=True)
        
        renderer = CleanDiagramRenderer(canvas)
        print(f"   ✓ Canvas and renderer created")
    except Exception as e:
        print(f"   ✗ Canvas/renderer creation failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 5: Render diagram (exact same call as _update_display)
    print("\n5. Rendering diagram...")
    try:
        canvas.clear()
        renderer.render_diagram(layout_result, graph)
        print(f"   ✓ Diagram rendered successfully")
        
        # Keep window open for inspection
        print("\n=== SUCCESS: Window should show the rendered diagram ===")
        print("Close the window to exit.")
        root.mainloop()
        
    except Exception as e:
        print(f"   ✗ Rendering failed: {e}")
        import traceback
        traceback.print_exc()
        root.destroy()
        return

if __name__ == "__main__":
    test_display_pipeline()
