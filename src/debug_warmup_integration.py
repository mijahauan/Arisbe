#!/usr/bin/env python3
"""
Debug script to test the exact integration between WarmupModeController and the main application.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from tkinter import ttk
from egif_parser_dau import EGIFParser
from content_driven_layout import ContentDrivenLayoutEngine
from diagram_renderer_clean import CleanDiagramRenderer
from tkinter_backend import TkinterCanvas
from warmup_mode_controller import WarmupModeController

def test_warmup_integration():
    """Test the exact integration used in IntegratedEGEditor."""
    
    print("=== TESTING WARMUP CONTROLLER INTEGRATION ===")
    
    # Create the same UI structure as IntegratedEGEditor
    root = tk.Tk()
    root.title("Debug Warmup Integration")
    root.geometry("1000x700")
    
    # Create a frame similar to the right panel in IntegratedEGEditor
    canvas_frame = ttk.LabelFrame(root, text="Diagram", padding=10)
    canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Create canvas exactly like in IntegratedEGEditor
    print("1. Creating canvas and renderer...")
    try:
        canvas = TkinterCanvas(800, 600, title="EG Diagram", master=canvas_frame)
        canvas.tk_canvas.pack(fill=tk.BOTH, expand=True)
        
        renderer = CleanDiagramRenderer(canvas)
        print("   ✓ Canvas and renderer created")
    except Exception as e:
        print(f"   ✗ Canvas/renderer creation failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Create layout engine exactly like in IntegratedEGEditor
    print("\n2. Creating layout engine...")
    try:
        layout_engine = ContentDrivenLayoutEngine()
        print("   ✓ Layout engine created")
    except Exception as e:
        print(f"   ✗ Layout engine creation failed: {e}")
        return
    
    # Create warmup controller exactly like in IntegratedEGEditor
    print("\n3. Creating WarmupModeController...")
    try:
        warmup_controller = WarmupModeController(canvas, layout_engine)
        print("   ✓ WarmupModeController created")
    except Exception as e:
        print(f"   ✗ WarmupModeController creation failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Parse the same EGIF as _load_example()
    print("\n4. Parsing EGIF...")
    egif_text = '(Human "Socrates") ~[ (Mortal "Socrates") ]'
    try:
        parser = EGIFParser(egif_text)
        graph = parser.parse()
        print(f"   ✓ Graph parsed: {len(graph.V)} vertices, {len(graph.E)} edges, {len(graph.Cut)} cuts")
    except Exception as e:
        print(f"   ✗ Parse failed: {e}")
        return
    
    # Set graph in warmup controller (same as _load_example())
    print("\n5. Setting graph in WarmupModeController...")
    try:
        warmup_controller.set_graph(graph)
        print("   ✓ Graph set in controller")
    except Exception as e:
        print(f"   ✗ Setting graph failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Add some debug info
    print("\n6. Debug information:")
    print(f"   - Canvas size: {canvas.width}x{canvas.height}")
    print(f"   - Canvas backend: {type(canvas).__name__}")
    print(f"   - Renderer: {type(renderer).__name__}")
    print(f"   - Controller: {type(warmup_controller).__name__}")
    
    # Test direct rendering (bypass controller)
    print("\n7. Testing direct rendering...")
    try:
        layout_result = layout_engine.layout_graph(graph)
        canvas.clear()
        renderer.render_diagram(layout_result, graph)
        print("   ✓ Direct rendering successful")
    except Exception as e:
        print(f"   ✗ Direct rendering failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== Integration test complete ===")
    print("If you see a diagram, the integration works.")
    print("If canvas is blank, there's an issue with the controller or rendering.")
    print("Close window to exit.")
    
    root.mainloop()

if __name__ == "__main__":
    test_warmup_integration()
