#!/usr/bin/env python3
"""
Debug script to test the initialization sequence and identify why no default graph is displayed.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from egif_parser_dau import EGIFParser
from content_driven_layout import ContentDrivenLayoutEngine
from diagram_renderer_clean import CleanDiagramRenderer
from tkinter_backend import TkinterCanvas
from warmup_mode_controller import WarmupModeController

def test_initialization():
    """Test the initialization sequence step by step."""
    
    print("=== DEBUGGING INITIALIZATION SEQUENCE ===")
    
    # Step 1: Test EGIF parsing
    print("\n1. Testing EGIF parsing...")
    egif_text = '(Human "Socrates") ~[ (Mortal "Socrates") ]'
    print(f"   EGIF: {egif_text}")
    
    try:
        parser = EGIFParser(egif_text)
        graph = parser.parse()
        print(f"   ✓ Parsed successfully")
        print(f"   - Vertices: {len(graph.V)}")
        print(f"   - Edges: {len(graph.E)}")
        print(f"   - Cuts: {len(graph.Cut)}")
        print(f"   - Relations: {list(graph.rel.values())}")
    except Exception as e:
        print(f"   ✗ Parse failed: {e}")
        return
    
    # Step 2: Test layout engine
    print("\n2. Testing layout engine...")
    try:
        layout_engine = ContentDrivenLayoutEngine()
        layout = layout_engine.layout_graph(graph)
        print(f"   ✓ Layout generated successfully")
        print(f"   - Layout keys: {list(layout.keys())}")
        
        # Check if all graph elements have layout positions
        for vertex in graph.V:
            if vertex.id in layout:
                pos = layout[vertex.id]
                print(f"   - Vertex {vertex.id[-8:]}: ({pos.x:.1f}, {pos.y:.1f})")
            else:
                print(f"   - Missing layout for vertex {vertex.id[-8:]}")
                
        for edge in graph.E:
            if edge.id in layout:
                pos = layout[edge.id]
                print(f"   - Edge {edge.id[-8:]}: ({pos.x:.1f}, {pos.y:.1f})")
            else:
                print(f"   - Missing layout for edge {edge.id[-8:]}")
                
        for cut in graph.Cut:
            if cut.id in layout:
                pos = layout[cut.id]
                print(f"   - Cut {cut.id[-8:]}: ({pos.x:.1f}, {pos.y:.1f})")
            else:
                print(f"   - Missing layout for cut {cut.id[-8:]}")
                
    except Exception as e:
        print(f"   ✗ Layout failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 3: Test canvas and renderer creation
    print("\n3. Testing canvas and renderer...")
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # Hide the test window
        
        canvas = TkinterCanvas(400, 300, title="Test Canvas", master=root)
        renderer = CleanDiagramRenderer(canvas)
        print(f"   ✓ Canvas and renderer created successfully")
        
        # Test rendering
        canvas.clear()
        renderer.render_diagram(layout, graph)
        print(f"   ✓ Diagram rendered successfully")
        
        root.destroy()
        
    except Exception as e:
        print(f"   ✗ Canvas/renderer failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 4: Test WarmupModeController
    print("\n4. Testing WarmupModeController...")
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # Hide the test window
        
        canvas = TkinterCanvas(400, 300, title="Test Canvas", master=root)
        layout_engine = ContentDrivenLayoutEngine()
        controller = WarmupModeController(canvas, layout_engine)
        
        print(f"   ✓ WarmupModeController created successfully")
        
        # Test setting graph
        controller.set_graph(graph)
        print(f"   ✓ Graph set in controller successfully")
        
        root.destroy()
        
    except Exception as e:
        print(f"   ✗ WarmupModeController failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n=== ALL INITIALIZATION TESTS PASSED ===")
    print("The issue may be in the integration or timing of these components.")

if __name__ == "__main__":
    test_initialization()
