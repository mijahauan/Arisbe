#!/usr/bin/env python3
"""
Debug script to test the overlapping cuts issue with EGIF: ~[ ~[ (P "x") ] ~[ (Q "x") ] ]
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from egif_parser_dau import EGIFParser
from content_driven_layout import ContentDrivenLayoutEngine
from diagram_renderer_clean import CleanDiagramRenderer
from tkinter_backend import TkinterCanvas

def test_overlapping_cuts():
    """Test the specific EGIF that causes overlapping cuts."""
    
    print("=== TESTING OVERLAPPING CUTS ISSUE ===")
    
    # The problematic EGIF
    egif_text = '~[ ~[ (P "x") ] ~[ (Q "x") ] ]'
    print(f"Testing EGIF: {egif_text}")
    
    # Parse the EGIF
    try:
        parser = EGIFParser(egif_text)
        graph = parser.parse()
        print(f"✓ Graph parsed: {len(graph.V)} vertices, {len(graph.E)} edges, {len(graph.Cut)} cuts")
        
        # Print graph structure for debugging
        print("\nGraph structure:")
        print(f"  Vertices: {[v.id[-8:] for v in graph.V]}")
        print(f"  Edges: {[e.id[-8:] for e in graph.E]}")
        print(f"  Cuts: {[c.id[-8:] for c in graph.Cut]}")
        print(f"  Relations: {list(graph.rel.values())}")
        
        # Print area containment
        print("\nArea containment:")
        for area_id, elements in graph.area.items():
            area_name = "sheet" if area_id == graph.sheet else area_id[-8:]
            element_types = []
            for elem_id in elements:
                if elem_id in [v.id for v in graph.V]:
                    element_types.append(f"vertex-{elem_id[-8:]}")
                elif elem_id in [e.id for e in graph.E]:
                    element_types.append(f"edge-{elem_id[-8:]}")
                elif elem_id in [c.id for c in graph.Cut]:
                    element_types.append(f"cut-{elem_id[-8:]}")
            print(f"  {area_name}: {element_types}")
            
    except Exception as e:
        print(f"✗ Parse failed: {e}")
        return
    
    # Generate layout
    try:
        layout_engine = ContentDrivenLayoutEngine()
        layout_result = layout_engine.layout_graph(graph)
        print(f"\n✓ Layout generated with {len(layout_result.primitives)} primitives")
        
        # Analyze cut positions
        cuts = [(elem_id, primitive) for elem_id, primitive in layout_result.primitives.items() 
                if primitive.element_type == 'cut']
        
        print(f"\nCut positions:")
        for i, (cut_id, primitive) in enumerate(cuts):
            x, y = primitive.position
            x1, y1, x2, y2 = primitive.bounds
            print(f"  Cut {i+1} ({cut_id[-8:]}): center=({x:.1f}, {y:.1f}), bounds=({x1:.1f}, {y1:.1f}, {x2:.1f}, {y2:.1f})")
        
        # Check for overlaps
        print(f"\nOverlap analysis:")
        for i, (cut_id1, prim1) in enumerate(cuts):
            for j, (cut_id2, prim2) in enumerate(cuts):
                if i >= j:
                    continue
                
                x1_1, y1_1, x2_1, y2_1 = prim1.bounds
                x1_2, y1_2, x2_2, y2_2 = prim2.bounds
                
                # Check if bounds overlap
                overlap = not (x2_1 < x1_2 or x1_1 > x2_2 or y2_1 < y1_2 or y1_1 > y2_2)
                
                if overlap:
                    print(f"  ⚠️  OVERLAP: Cut {i+1} and Cut {j+1} overlap!")
                else:
                    print(f"  ✓ Cut {i+1} and Cut {j+1} do not overlap")
        
    except Exception as e:
        print(f"✗ Layout failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Create visual test
    try:
        root = tk.Tk()
        root.title("Debug Overlapping Cuts")
        root.geometry("800x600")
        
        canvas = TkinterCanvas(800, 600, title="Overlapping Cuts Test", master=root)
        canvas.tk_canvas.pack(fill=tk.BOTH, expand=True)
        
        renderer = CleanDiagramRenderer(canvas)
        
        # Render the diagram
        canvas.clear()
        renderer.render_diagram(layout_result, graph)
        
        print(f"\n✓ Diagram rendered")
        print("Check the visual output for overlapping cuts.")
        print("Close window to exit.")
        
        root.mainloop()
        
    except Exception as e:
        print(f"✗ Rendering failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_overlapping_cuts()
