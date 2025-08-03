"""
Debug area assignment to identify why predicates are in wrong areas.
"""

from layout_engine_clean import CleanLayoutEngine
from egi_core_dau import RelationalGraphWithCuts
from egif_parser_dau import EGIFParser


def debug_area_assignment():
    """Debug the exact area assignment process."""
    
    print("=== Debugging Area Assignment ===")
    
    # Test case 1: (Human "Socrates") ~[ (Mortal "Socrates") ]
    egif_text = '(Human "Socrates") ~[ (Mortal "Socrates") ]'
    print(f"\nDebugging: {egif_text}")
    
    # Parse EGIF to EGI
    parser = EGIFParser(egif_text)
    graph = parser.parse()
    
    print(f"\nEGI Structure:")
    print(f"  Sheet ID: {graph.sheet}")
    print(f"  Area mapping: {dict(graph.area)}")
    print(f"  Relation mapping: {dict(graph.rel)}")
    print(f"  Nu mapping: {dict(graph.nu)}")
    
    # Manually trace area assignment for each edge
    print(f"\nManual Area Assignment Trace:")
    for edge in graph.E:
        relation_name = graph.rel.get(edge.id, "UNKNOWN")
        print(f"  Edge {edge.id} ({relation_name}):")
        
        # Check which area contains this edge
        containing_area = None
        for area_id, elements in graph.area.items():
            if edge.id in elements:
                containing_area = area_id
                break
        
        print(f"    Found in area: {containing_area}")
        if containing_area == graph.sheet:
            print(f"    -> Should be at SHEET LEVEL")
        else:
            print(f"    -> Should be INSIDE CUT {containing_area}")
    
    # Now test the layout engine
    layout_engine = CleanLayoutEngine()
    layout_result = layout_engine.layout_graph(graph)
    
    print(f"\nLayout Engine Results:")
    for element_id, primitive in layout_result.primitives.items():
        if primitive.element_type == 'edge':
            relation_name = graph.rel.get(element_id, "UNKNOWN")
            print(f"  Edge {element_id} ({relation_name}):")
            print(f"    Layout parent_area: {primitive.parent_area}")
            print(f"    Position: {primitive.position}")
            
            # Check if layout matches EGI
            expected_area = None
            for area_id, elements in graph.area.items():
                if element_id in elements:
                    expected_area = area_id
                    break
            
            if primitive.parent_area == expected_area:
                print(f"    ✅ CORRECT: Layout matches EGI area assignment")
            else:
                print(f"    ❌ ERROR: Layout parent_area={primitive.parent_area}, EGI area={expected_area}")
    
    # Test case 3: *x (Human x) ~[ (Mortal x) (Wise x) ]
    print(f"\n" + "="*60)
    egif_text3 = '*x (Human x) ~[ (Mortal x) (Wise x) ]'
    print(f"\nDebugging: {egif_text3}")
    
    parser3 = EGIFParser(egif_text3)
    graph3 = parser3.parse()
    
    print(f"\nEGI Structure:")
    print(f"  Sheet ID: {graph3.sheet}")
    print(f"  Area mapping: {dict(graph3.area)}")
    print(f"  Relation mapping: {dict(graph3.rel)}")
    
    print(f"\nManual Area Assignment Trace:")
    for edge in graph3.E:
        relation_name = graph3.rel.get(edge.id, "UNKNOWN")
        print(f"  Edge {edge.id} ({relation_name}):")
        
        containing_area = None
        for area_id, elements in graph3.area.items():
            if edge.id in elements:
                containing_area = area_id
                break
        
        print(f"    Found in area: {containing_area}")
        if containing_area == graph3.sheet:
            print(f"    -> Should be at SHEET LEVEL")
        else:
            print(f"    -> Should be INSIDE CUT {containing_area}")
    
    layout_result3 = layout_engine.layout_graph(graph3)
    
    print(f"\nLayout Engine Results:")
    for element_id, primitive in layout_result3.primitives.items():
        if primitive.element_type == 'edge':
            relation_name = graph3.rel.get(element_id, "UNKNOWN")
            print(f"  Edge {element_id} ({relation_name}):")
            print(f"    Layout parent_area: {primitive.parent_area}")
            
            expected_area = None
            for area_id, elements in graph3.area.items():
                if element_id in elements:
                    expected_area = area_id
                    break
            
            if primitive.parent_area == expected_area:
                print(f"    ✅ CORRECT: Layout matches EGI area assignment")
            else:
                print(f"    ❌ ERROR: Layout parent_area={primitive.parent_area}, EGI area={expected_area}")


if __name__ == "__main__":
    debug_area_assignment()
