#!/usr/bin/env python3
"""
Debug Context Issue
Investigates the "Element not found in any context" error

The simplified implementation is failing because of a context lookup issue.
This debug script will examine the graph structure and context mappings
to understand what's going wrong.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut, ElementID
    from egif_parser_dau import parse_egif
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all required modules are available")
    sys.exit(1)


def debug_graph_structure(egif: str):
    """Debug the structure of a parsed graph."""
    
    print(f"Debugging EGIF: {egif}")
    print("=" * 50)
    
    try:
        graph = parse_egif(egif)
        
        print(f"Graph components:")
        print(f"  Vertices: {len(graph.V)}")
        print(f"  Edges: {len(graph.E)}")
        print(f"  Cuts: {len(graph.Cut)}")
        print(f"  Sheet: {graph.sheet}")
        print()
        
        # Examine vertices
        print("VERTICES:")
        for i, vertex in enumerate(graph.V):
            print(f"  {i+1}. {vertex}")
            
            # Try to get context
            try:
                context = graph.get_context(vertex.id)
                print(f"     Context: {context}")
                
                # Check if context is positive
                try:
                    is_positive = graph.is_positive_context(context)
                    print(f"     Positive: {is_positive}")
                except Exception as e:
                    print(f"     Positive check failed: {e}")
                
            except Exception as e:
                print(f"     Context lookup failed: {e}")
        
        print()
        
        # Examine edges
        print("EDGES:")
        for i, edge in enumerate(graph.E):
            print(f"  {i+1}. {edge}")
            
            # Try to get context
            try:
                context = graph.get_context(edge.id)
                print(f"     Context: {context}")
                
                # Check if context is positive
                try:
                    is_positive = graph.is_positive_context(context)
                    print(f"     Positive: {is_positive}")
                except Exception as e:
                    print(f"     Positive check failed: {e}")
                
                # Try to get incident vertices
                try:
                    incident = graph.get_incident_vertices(edge.id)
                    print(f"     Incident vertices: {incident}")
                except Exception as e:
                    print(f"     Incident vertices failed: {e}")
                
            except Exception as e:
                print(f"     Context lookup failed: {e}")
        
        print()
        
        # Examine cuts
        print("CUTS:")
        for i, cut in enumerate(graph.Cut):
            print(f"  {i+1}. {cut}")
            
            # Try to get context
            try:
                context = graph.get_context(cut.id)
                print(f"     Context: {context}")
                
                # Check if context is positive
                try:
                    is_positive = graph.is_positive_context(cut.id)
                    print(f"     Positive: {is_positive}")
                except Exception as e:
                    print(f"     Positive check failed: {e}")
                
            except Exception as e:
                print(f"     Context lookup failed: {e}")
        
        print()
        
        # Examine area mappings
        print("AREA MAPPINGS:")
        try:
            # Check sheet area
            sheet_area = graph.area.get(graph.sheet, set())
            print(f"  Sheet area: {sheet_area}")
            
            # Check cut areas
            for cut in graph.Cut:
                cut_area = graph.area.get(cut.id, set())
                print(f"  Cut {cut.id} area: {cut_area}")
        
        except Exception as e:
            print(f"  Area mapping examination failed: {e}")
        
        print()
        
        # Try to understand the context mapping issue
        print("CONTEXT MAPPING ANALYSIS:")
        
        # Check if get_context method exists and works
        if hasattr(graph, 'get_context'):
            print("  get_context method exists")
            
            # Test with each element
            all_elements = [v.id for v in graph.V] + [e.id for e in graph.E] + [c.id for c in graph.Cut]
            
            for element_id in all_elements:
                try:
                    context = graph.get_context(element_id)
                    print(f"    {element_id} → {context}")
                except Exception as e:
                    print(f"    {element_id} → ERROR: {e}")
        else:
            print("  get_context method missing!")
        
        print()
        
        # Check context attribute
        if hasattr(graph, 'context'):
            print("CONTEXT ATTRIBUTE:")
            print(f"  Type: {type(graph.context)}")
            print(f"  Content: {graph.context}")
        else:
            print("  No context attribute found")
        
        print()
        
    except Exception as e:
        print(f"Failed to parse EGIF: {e}")
        import traceback
        traceback.print_exc()


def test_context_debugging():
    """Test context debugging on various EGIFs."""
    
    print("Context Issue Debugging")
    print("Investigating 'Element not found in any context' error")
    print()
    
    test_egifs = [
        "~[(Human *x) ~[(Mortal x)]]",
        "(Simple *x)",
        "~[~[(Bad *x)]]"
    ]
    
    for egif in test_egifs:
        debug_graph_structure(egif)
        print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    test_context_debugging()

