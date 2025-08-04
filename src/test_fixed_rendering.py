#!/usr/bin/env python3
"""
Test complete rendering with the correct EGIF that shows non-overlapping cuts clearly.
"""

import tkinter as tk
from egif_parser_dau import EGIFParser
from graphviz_renderer_integration import GraphvizRendererIntegration
from diagram_renderer_clean import CleanDiagramRenderer, TkinterCanvas

def test_perfect_demo_case():
    """Test the perfect demo case with proper visual rendering."""
    
    print("=== Testing Perfect Demo Case ===")
    
    # Use the perfect demo case: 2 vertices, 2 predicates, 3 cuts
    egif_text = '~[ ~[ (Human "Socrates") ] ~[ (Mortal "Plato") ] ]'
    
    print(f"Perfect Demo EGIF: {egif_text}")
    print("Expected: 2 vertices (Socrates, Plato), 2 predicates (Human, Mortal), 3 cuts")
    print("This should clearly demonstrate non-overlapping sibling cuts!")
    
    # Parse EGIF → EGI
    parser = EGIFParser(egif_text)
    graph = parser.parse()
    
    print(f"✓ EGI Structure:")
    print(f"  Vertices: {[(v.id, v.label) for v in graph.V]}")
    print(f"  Edges: {[(e.id, graph.get_relation_name(e.id)) for e in graph.E]}")
    print(f"  Cuts: {len(graph.Cut)}")
    
    # Create Tkinter window
    root = tk.Tk()
    root.title("PERFECT DEMO: Non-overlapping Cuts with Graphviz")
    root.geometry("900x700")
    
    # Create canvas
    tk_canvas = tk.Canvas(root, width=900, height=700, bg='white')
    tk_canvas.pack(expand=True, fill='both')
    canvas = TkinterCanvas(tk_canvas)
    
    # Create integration
    integration = GraphvizRendererIntegration()
    
    try:
        # Debug layout info
        layout_info = integration.get_layout_info(graph)
        print(f"\n✓ Layout Analysis:")
        print(f"  Primitives: {layout_info['primitives_count']}")
        print(f"  Types: {layout_info['primitive_types']}")
        
        print(f"\n✓ DOT Structure (should show all elements):")
        print(layout_info['dot_source'])
        
        # Attempt rendering
        print(f"\n✓ Attempting rendering...")
        success = integration.render_graph(graph, canvas)
        
        if success:
            # Add title and description
            tk_canvas.create_text(450, 30, text="🎉 SUCCESS: Perfect Non-overlapping Cuts Demo", 
                                font=("Arial", 18, "bold"), fill="darkgreen")
            tk_canvas.create_text(450, 60, text=f"EGIF: {egif_text}", 
                                font=("Arial", 12), fill="blue")
            tk_canvas.create_text(450, 80, text="Socrates (Human) and Plato (Mortal) in separate, non-overlapping cuts", 
                                font=("Arial", 11), fill="gray")
            tk_canvas.create_text(450, 670, text="✓ Graphviz clusters guarantee no overlapping sibling cuts", 
                                font=("Arial", 10, "bold"), fill="darkblue")
            
            print(f"🎉 PERFECT DEMO SUCCESSFUL!")
            print(f"Visual rendering complete - showing non-overlapping cuts with distinct elements")
            
            # Show window
            print(f"\nShowing perfect demo window...")
            print(f"You should see: Socrates and Plato in separate cuts that don't overlap")
            root.mainloop()
            
            return True
            
        else:
            print(f"❌ Rendering failed - need to debug SVG coordinate extraction")
            
            # Show debug info anyway
            tk_canvas.create_text(450, 350, text="❌ Rendering Failed", 
                                font=("Arial", 16, "bold"), fill="red")
            tk_canvas.create_text(450, 380, text="Issue: SVG coordinate extraction not working", 
                                font=("Arial", 12), fill="red")
            tk_canvas.create_text(450, 400, text="DOT generation is perfect, but coordinates not extracted", 
                                font=("Arial", 10), fill="gray")
            
            root.mainloop()
            return False
            
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Show error in window
        tk_canvas.create_text(450, 350, text=f"❌ Error: {str(e)}", 
                            font=("Arial", 12), fill="red")
        root.mainloop()
        return False

def analyze_svg_extraction_issue():
    """Analyze why SVG coordinate extraction is failing."""
    
    print(f"\n=== Analyzing SVG Extraction Issue ===")
    
    egif_text = '~[ ~[ (Human "Socrates") ] ~[ (Mortal "Plato") ] ]'
    parser = EGIFParser(egif_text)
    graph = parser.parse()
    
    integration = GraphvizLayoutIntegration()
    result = integration.calculate_layout(graph)
    
    print(f"DOT has these elements:")
    dot_lines = result.dot_source.split('\n')
    for line in dot_lines:
        if '[label=' in line or 'subgraph cluster' in line:
            print(f"  {line.strip()}")
    
    print(f"\nBut we only extract these coordinates:")
    print(f"  Node positions: {result.node_positions}")
    print(f"  Cluster bounds: {result.cluster_bounds}")
    
    print(f"\nSVG content (first 2000 chars):")
    print(result.svg_source[:2000])
    
    # Save SVG for manual inspection
    with open('/tmp/perfect_demo.svg', 'w') as f:
        f.write(result.svg_source)
    print(f"\n✓ SVG saved to /tmp/perfect_demo.svg for manual inspection")

if __name__ == "__main__":
    print("🚀 Testing Perfect Demo Case for Non-overlapping Cuts")
    
    # Test the perfect demo
    success = test_perfect_demo_case()
    
    if not success:
        # Analyze the SVG extraction issue
        analyze_svg_extraction_issue()
        print(f"\n🔧 Next step: Fix SVG coordinate extraction to get all elements rendering")
