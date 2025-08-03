"""
Test the Clean Layout Engine with area containment examples.
This will verify that the layout engine properly reads EGI area mappings.
"""

from layout_engine_clean import CleanLayoutEngine
from egi_core_dau import RelationalGraphWithCuts, create_empty_graph, create_vertex, create_edge, create_cut
from egif_parser_dau import EGIFParser


def test_area_containment_layout():
    """Test that elements are positioned within their correct areas."""
    
    print("=== Testing Clean Layout Engine Area Containment ===")
    
    # Test case 1: (Human "Socrates") ~[ (Mortal "Socrates") ]
    egif_text = '(Human "Socrates") ~[ (Mortal "Socrates") ]'
    
    print(f"\nTesting EGIF: {egif_text}")
    
    # Parse EGIF to EGI
    parser = EGIFParser(egif_text)
    graph = parser.parse()
    
    print(f"Parsed EGI:")
    print(f"  Vertices: {len(graph.V)}")
    print(f"  Edges: {len(graph.E)}")
    print(f"  Cuts: {len(graph.Cut)}")
    print(f"  Area mapping: {dict(graph.area)}")
    
    # Create clean layout engine
    layout_engine = CleanLayoutEngine(canvas_width=800, canvas_height=600)
    
    # Generate layout
    layout_result = layout_engine.layout_graph(graph)
    
    print(f"\nLayout Results:")
    print(f"  Total primitives: {len(layout_result.primitives)}")
    print(f"  Canvas bounds: {layout_result.canvas_bounds}")
    
    # Analyze spatial primitives
    cuts = {k: v for k, v in layout_result.primitives.items() if v.element_type == 'cut'}
    vertices = {k: v for k, v in layout_result.primitives.items() if v.element_type == 'vertex'}
    edges = {k: v for k, v in layout_result.primitives.items() if v.element_type == 'edge'}
    
    print(f"\nSpatial Primitives Breakdown:")
    print(f"  Cuts: {len(cuts)}")
    print(f"  Vertices: {len(vertices)}")
    print(f"  Edges: {len(edges)}")
    
    # Verify area containment in spatial layout
    print(f"\nArea Containment Verification:")
    
    for element_id, primitive in layout_result.primitives.items():
        print(f"  {primitive.element_type} {element_id[:8]}...")
        print(f"    Position: {primitive.position}")
        print(f"    Bounds: {primitive.bounds}")
        print(f"    Parent area: {primitive.parent_area}")
        
        # Check if element is spatially within its parent
        if primitive.parent_area and primitive.parent_area in layout_result.primitives:
            parent = layout_result.primitives[primitive.parent_area]
            is_contained = _is_spatially_contained(primitive.bounds, parent.bounds)
            print(f"    Spatially contained in parent: {is_contained}")
            
            if not is_contained:
                print(f"    ❌ CONTAINMENT ERROR: Element not within parent bounds!")
                print(f"       Element bounds: {primitive.bounds}")
                print(f"       Parent bounds: {parent.bounds}")
        else:
            print(f"    At sheet level")
    
    # Test case 2: More complex nesting
    print(f"\n" + "="*60)
    egif_text2 = '*x ~[ (Human x) (Mortal x) ]'
    print(f"\nTesting EGIF: {egif_text2}")
    
    parser2 = EGIFParser(egif_text2)
    graph2 = parser2.parse()
    
    print(f"Parsed EGI:")
    print(f"  Vertices: {len(graph2.V)}")
    print(f"  Edges: {len(graph2.E)}")
    print(f"  Cuts: {len(graph2.Cut)}")
    print(f"  Area mapping: {dict(graph2.area)}")
    print(f"  Nu mapping: {dict(graph2.nu)}")
    
    layout_result2 = layout_engine.layout_graph(graph2)
    
    print(f"\nLayout Results:")
    print(f"  Total primitives: {len(layout_result2.primitives)}")
    
    # Verify that vertex and predicates are inside the cut
    for element_id, primitive in layout_result2.primitives.items():
        print(f"  {primitive.element_type} {element_id[:8]}...")
        print(f"    Position: {primitive.position}")
        print(f"    Parent area: {primitive.parent_area}")
        
        if primitive.parent_area and primitive.parent_area in layout_result2.primitives:
            parent = layout_result2.primitives[primitive.parent_area]
            is_contained = _is_spatially_contained(primitive.bounds, parent.bounds)
            containment_status = "✅ CONTAINED" if is_contained else "❌ NOT CONTAINED"
            print(f"    {containment_status}")


def _is_spatially_contained(child_bounds, parent_bounds):
    """Check if child bounds are completely within parent bounds."""
    cx1, cy1, cx2, cy2 = child_bounds
    px1, py1, px2, py2 = parent_bounds
    
    return (px1 <= cx1 and py1 <= cy1 and cx2 <= px2 and cy2 <= py2)


if __name__ == "__main__":
    test_area_containment_layout()
