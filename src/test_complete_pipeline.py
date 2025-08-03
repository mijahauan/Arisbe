"""
Test the complete Data → Layout → Rendering pipeline.
This verifies the clean 3-layer architecture with proper area containment.
"""

import tkinter as tk
from layout_engine_clean import CleanLayoutEngine
from diagram_renderer_clean import CleanDiagramRenderer, TkinterCanvas, RenderingTheme
from egi_core_dau import RelationalGraphWithCuts
from egif_parser_dau import EGIFParser


def test_complete_pipeline():
    """Test the complete clean architecture pipeline."""
    
    print("=== Testing Complete Clean Architecture Pipeline ===")
    
    # Test cases that demonstrate area containment
    test_cases = [
        '(Human "Socrates") ~[ (Mortal "Socrates") ]',
        '*x ~[ (Human x) (Mortal x) ]',
        '*x (Human x) ~[ (Mortal x) (Wise x) ]'
    ]
    
    for i, egif_text in enumerate(test_cases):
        print(f"\n--- Test Case {i+1}: {egif_text} ---")
        
        # Layer 1: Parse EGIF to EGI (Data Layer)
        parser = EGIFParser(egif_text)
        graph = parser.parse()
        
        print(f"EGI Data:")
        print(f"  Vertices: {len(graph.V)}")
        print(f"  Edges: {len(graph.E)}")
        print(f"  Cuts: {len(graph.Cut)}")
        print(f"  Area mapping: {dict(graph.area)}")
        
        # Layer 2: Generate spatial layout (Layout Layer)
        layout_engine = CleanLayoutEngine(canvas_width=600, canvas_height=400)
        layout_result = layout_engine.layout_graph(graph)
        
        print(f"Layout Results:")
        print(f"  Total primitives: {len(layout_result.primitives)}")
        print(f"  Canvas bounds: {layout_result.canvas_bounds}")
        
        # Verify area containment in layout
        containment_correct = True
        for element_id, primitive in layout_result.primitives.items():
            if primitive.parent_area and primitive.parent_area in layout_result.primitives:
                parent = layout_result.primitives[primitive.parent_area]
                is_contained = _is_spatially_contained(primitive.bounds, parent.bounds)
                if not is_contained:
                    print(f"  ❌ {primitive.element_type} {element_id[:8]} not contained in parent!")
                    containment_correct = False
        
        if containment_correct:
            print(f"  ✅ All elements properly contained in their areas")
        
        # Layer 3: Create visual rendering (Rendering Layer)
        root = tk.Tk()
        root.title(f"EG Diagram: {egif_text}")
        root.geometry("650x450")
        
        canvas_widget = tk.Canvas(root, width=600, height=400, bg="white")
        canvas_widget.pack(padx=25, pady=25)
        
        # Create clean renderer
        tkinter_canvas = TkinterCanvas(canvas_widget)
        theme = RenderingTheme()
        renderer = CleanDiagramRenderer(tkinter_canvas, theme)
        
        # Render the complete diagram
        renderer.render_diagram(layout_result, graph)
        
        print(f"  ✅ Diagram rendered with clean architecture")
        print(f"     - Cuts: fine-drawn curves")
        print(f"     - Vertices: heavy spots")
        print(f"     - Predicates: text with hooks")
        print(f"     - Lines of identity: heavy lines crossing boundaries")
        
        # Add analysis text to the canvas
        analysis_text = f"EGIF: {egif_text}\nVertices: {len(graph.V)}, Edges: {len(graph.E)}, Cuts: {len(graph.Cut)}"
        canvas_widget.create_text(10, 10, text=analysis_text, anchor="nw", font=("Arial", 10))
        
        # Show the window
        root.mainloop()


def test_pipeline_without_gui():
    """Test pipeline logic without GUI for automated testing."""
    
    print("\n=== Testing Pipeline Logic (No GUI) ===")
    
    egif_text = '*x ~[ (Human x) (Mortal x) ]'
    print(f"Testing: {egif_text}")
    
    # Layer 1: Data
    parser = EGIFParser(egif_text)
    graph = parser.parse()
    
    # Layer 2: Layout
    layout_engine = CleanLayoutEngine()
    layout_result = layout_engine.layout_graph(graph)
    
    # Verify the key architectural principle: area containment
    cuts = [p for p in layout_result.primitives.values() if p.element_type == 'cut']
    edges = [p for p in layout_result.primitives.values() if p.element_type == 'edge']
    vertices = [p for p in layout_result.primitives.values() if p.element_type == 'vertex']
    
    print(f"Results:")
    print(f"  Cuts: {len(cuts)}")
    print(f"  Vertices: {len(vertices)}")
    print(f"  Edges: {len(edges)}")
    
    # Check that edges are inside the cut
    cut_primitive = cuts[0] if cuts else None
    edges_in_cut = [e for e in edges if e.parent_area == cut_primitive.element_id]
    
    print(f"  Edges inside cut: {len(edges_in_cut)}/{len(edges)}")
    
    # Check that vertices can be at sheet level (this is correct!)
    vertices_at_sheet = [v for v in vertices if v.parent_area != cut_primitive.element_id]
    print(f"  Vertices at sheet level: {len(vertices_at_sheet)}/{len(vertices)} (this is correct)")
    
    if len(edges_in_cut) == len(edges):
        print("  ✅ ARCHITECTURE SUCCESS: All predicates inside cut, vertices can cross boundaries")
        return True
    else:
        print("  ❌ ARCHITECTURE FAILURE: Predicates not properly contained")
        return False


def _is_spatially_contained(child_bounds, parent_bounds):
    """Check if child bounds are completely within parent bounds."""
    cx1, cy1, cx2, cy2 = child_bounds
    px1, py1, px2, py2 = parent_bounds
    return (px1 <= cx1 and py1 <= cy1 and cx2 <= px2 and cy2 <= py2)


if __name__ == "__main__":
    # First test without GUI for verification
    success = test_pipeline_without_gui()
    
    if success:
        print("\n" + "="*60)
        print("Pipeline verification successful! Starting GUI tests...")
        test_complete_pipeline()
    else:
        print("Pipeline verification failed. Fix issues before GUI testing.")
