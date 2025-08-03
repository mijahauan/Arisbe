"""
Test to clearly display the two problematic cases for visual inspection.
This will show exactly where predicates are positioned relative to cuts.
"""

import tkinter as tk
from layout_engine_clean import CleanLayoutEngine
from diagram_renderer_clean import CleanDiagramRenderer, TkinterCanvas, RenderingTheme
from egi_core_dau import RelationalGraphWithCuts
from egif_parser_dau import EGIFParser


def test_problematic_cases():
    """Display the two problematic cases with detailed annotations."""
    
    # Case 1: (Human "Socrates") ~[ (Mortal "Socrates") ]
    print("=== Case 1: (Human 'Socrates') ~[ (Mortal 'Socrates') ] ===")
    
    egif_text1 = '(Human "Socrates") ~[ (Mortal "Socrates") ]'
    parser1 = EGIFParser(egif_text1)
    graph1 = parser1.parse()
    
    print(f"EGI Area Mapping: {dict(graph1.area)}")
    print(f"Relation Mapping: {dict(graph1.rel)}")
    
    # Generate layout
    layout_engine = CleanLayoutEngine(canvas_width=500, canvas_height=400)
    layout_result1 = layout_engine.layout_graph(graph1)
    
    print(f"\nLayout Results:")
    for element_id, primitive in layout_result1.primitives.items():
        if primitive.element_type == 'edge':
            relation_name = graph1.rel.get(element_id, "UNKNOWN")
            print(f"  {relation_name}: parent_area={primitive.parent_area}, position={primitive.position}")
        elif primitive.element_type == 'cut':
            print(f"  Cut: bounds={primitive.bounds}")
    
    # Create GUI for Case 1
    root1 = tk.Tk()
    root1.title("Case 1: (Human 'Socrates') ~[ (Mortal 'Socrates') ]")
    root1.geometry("550x500")
    
    # Add detailed analysis text
    analysis_frame1 = tk.Frame(root1)
    analysis_frame1.pack(fill=tk.X, padx=10, pady=5)
    
    analysis_text1 = f"""CASE 1 ANALYSIS:
EGIF: {egif_text1}
Expected: Human at SHEET level, Mortal INSIDE cut
EGI Area Mapping: {dict(graph1.area)}
Relation Mapping: {dict(graph1.rel)}
"""
    
    analysis_label1 = tk.Label(analysis_frame1, text=analysis_text1, 
                              justify=tk.LEFT, font=("Courier", 10), bg="lightyellow")
    analysis_label1.pack(fill=tk.X)
    
    # Add layout details
    layout_details1 = ""
    for element_id, primitive in layout_result1.primitives.items():
        if primitive.element_type == 'edge':
            relation_name = graph1.rel.get(element_id, "UNKNOWN")
            area_type = "SHEET" if primitive.parent_area == graph1.sheet else "CUT"
            layout_details1 += f"{relation_name}: {area_type} at {primitive.position}\n"
        elif primitive.element_type == 'cut':
            layout_details1 += f"Cut bounds: {primitive.bounds}\n"
    
    layout_label1 = tk.Label(analysis_frame1, text=layout_details1, 
                            justify=tk.LEFT, font=("Courier", 9), bg="lightblue")
    layout_label1.pack(fill=tk.X)
    
    # Canvas for Case 1
    canvas_widget1 = tk.Canvas(root1, width=500, height=350, bg="white", relief=tk.SUNKEN, bd=2)
    canvas_widget1.pack(padx=10, pady=5)
    
    # Render Case 1
    tkinter_canvas1 = TkinterCanvas(canvas_widget1)
    theme1 = RenderingTheme()
    renderer1 = CleanDiagramRenderer(tkinter_canvas1, theme1)
    renderer1.render_diagram(layout_result1, graph1)
    
    # Add visual annotations to show areas clearly
    # Draw cut area with colored background for clarity
    for element_id, primitive in layout_result1.primitives.items():
        if primitive.element_type == 'cut':
            x1, y1, x2, y2 = primitive.bounds
            canvas_widget1.create_rectangle(x1, y1, x2, y2, outline="red", width=2, fill="", dash=(5, 5))
            canvas_widget1.create_text(x1+5, y1+5, text="CUT AREA", anchor="nw", fill="red", font=("Arial", 8, "bold"))
    
    # Annotate predicates with their area assignments
    for element_id, primitive in layout_result1.primitives.items():
        if primitive.element_type == 'edge':
            relation_name = graph1.rel.get(element_id, "UNKNOWN")
            area_type = "SHEET" if primitive.parent_area == graph1.sheet else "CUT"
            color = "green" if area_type == "SHEET" else "blue"
            x, y = primitive.position
            canvas_widget1.create_text(x, y-25, text=f"{relation_name}\n({area_type})", 
                                     anchor="center", fill=color, font=("Arial", 8, "bold"))
    
    # Case 3: *x (Human x) ~[ (Mortal x) (Wise x) ]
    print(f"\n=== Case 3: *x (Human x) ~[ (Mortal x) (Wise x) ] ===")
    
    egif_text3 = '*x (Human x) ~[ (Mortal x) (Wise x) ]'
    parser3 = EGIFParser(egif_text3)
    graph3 = parser3.parse()
    
    print(f"EGI Area Mapping: {dict(graph3.area)}")
    print(f"Relation Mapping: {dict(graph3.rel)}")
    
    layout_result3 = layout_engine.layout_graph(graph3)
    
    print(f"\nLayout Results:")
    for element_id, primitive in layout_result3.primitives.items():
        if primitive.element_type == 'edge':
            relation_name = graph3.rel.get(element_id, "UNKNOWN")
            print(f"  {relation_name}: parent_area={primitive.parent_area}, position={primitive.position}")
        elif primitive.element_type == 'cut':
            print(f"  Cut: bounds={primitive.bounds}")
    
    # Create GUI for Case 3
    root3 = tk.Tk()
    root3.title("Case 3: *x (Human x) ~[ (Mortal x) (Wise x) ]")
    root3.geometry("550x500")
    
    # Add detailed analysis text
    analysis_frame3 = tk.Frame(root3)
    analysis_frame3.pack(fill=tk.X, padx=10, pady=5)
    
    analysis_text3 = f"""CASE 3 ANALYSIS:
EGIF: {egif_text3}
Expected: Human at SHEET level, Mortal and Wise INSIDE cut
EGI Area Mapping: {dict(graph3.area)}
Relation Mapping: {dict(graph3.rel)}
"""
    
    analysis_label3 = tk.Label(analysis_frame3, text=analysis_text3, 
                              justify=tk.LEFT, font=("Courier", 10), bg="lightyellow")
    analysis_label3.pack(fill=tk.X)
    
    # Add layout details
    layout_details3 = ""
    for element_id, primitive in layout_result3.primitives.items():
        if primitive.element_type == 'edge':
            relation_name = graph3.rel.get(element_id, "UNKNOWN")
            area_type = "SHEET" if primitive.parent_area == graph3.sheet else "CUT"
            layout_details3 += f"{relation_name}: {area_type} at {primitive.position}\n"
        elif primitive.element_type == 'cut':
            layout_details3 += f"Cut bounds: {primitive.bounds}\n"
    
    layout_label3 = tk.Label(analysis_frame3, text=layout_details3, 
                            justify=tk.LEFT, font=("Courier", 9), bg="lightblue")
    layout_label3.pack(fill=tk.X)
    
    # Canvas for Case 3
    canvas_widget3 = tk.Canvas(root3, width=500, height=350, bg="white", relief=tk.SUNKEN, bd=2)
    canvas_widget3.pack(padx=10, pady=5)
    
    # Render Case 3
    tkinter_canvas3 = TkinterCanvas(canvas_widget3)
    renderer3 = CleanDiagramRenderer(tkinter_canvas3, theme1)
    renderer3.render_diagram(layout_result3, graph3)
    
    # Add visual annotations for Case 3
    for element_id, primitive in layout_result3.primitives.items():
        if primitive.element_type == 'cut':
            x1, y1, x2, y2 = primitive.bounds
            canvas_widget3.create_rectangle(x1, y1, x2, y2, outline="red", width=2, fill="", dash=(5, 5))
            canvas_widget3.create_text(x1+5, y1+5, text="CUT AREA", anchor="nw", fill="red", font=("Arial", 8, "bold"))
    
    # Annotate predicates
    for element_id, primitive in layout_result3.primitives.items():
        if primitive.element_type == 'edge':
            relation_name = graph3.rel.get(element_id, "UNKNOWN")
            area_type = "SHEET" if primitive.parent_area == graph3.sheet else "CUT"
            color = "green" if area_type == "SHEET" else "blue"
            x, y = primitive.position
            canvas_widget3.create_text(x, y-25, text=f"{relation_name}\n({area_type})", 
                                     anchor="center", fill=color, font=("Arial", 8, "bold"))
    
    print(f"\nGUI windows created. Please examine the visual positioning.")
    print(f"- GREEN text = Should be at SHEET level")
    print(f"- BLUE text = Should be INSIDE cut")
    print(f"- RED dashed box = Cut boundary")
    
    # Start the GUI event loops
    root1.mainloop()
    root3.mainloop()


if __name__ == "__main__":
    test_problematic_cases()
