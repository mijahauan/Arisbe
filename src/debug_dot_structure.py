#!/usr/bin/env python3
"""
Debug the DOT structure to understand why Graphviz places vertices inside cuts.
"""

from egif_parser_dau import EGIFParser
from graphviz_layout_integration import GraphvizLayoutIntegration

def debug_dot_structure():
    """Debug DOT structure generation."""
    
    print("=== Debugging DOT Structure Generation ===")
    
    # Test the problematic case
    egif_text = '*x (Human x) ~[ (Mortal x) ]'
    
    print(f"EGIF: {egif_text}")
    
    # Parse and analyze
    parser = EGIFParser(egif_text)
    graph = parser.parse()
    
    print(f"\nEGI Structure:")
    print(f"  Sheet: {graph.sheet}")
    print(f"  Area mapping:")
    for area_id, contents in graph.area.items():
        print(f"    {area_id}: {list(contents)}")
    
    # Generate DOT
    integration = GraphvizLayoutIntegration()
    
    # Let's manually trace the DOT generation
    print(f"\n=== Manual DOT Generation Trace ===")
    
    # Reset counters
    integration.node_counter = 0
    integration.cluster_counter = 0
    integration.node_mapping = {}
    integration.cluster_mapping = {}
    
    # Create DOT graph
    dot = integration._create_dot_graph()
    
    # Add vertices
    print(f"\nAdding vertices:")
    for vertex in graph.V:
        node_name = integration._get_node_name(vertex.id)
        print(f"  Vertex {vertex.id} -> {node_name}")
        
        # Check which area this vertex is in
        vertex_area = None
        for area_id, contents in graph.area.items():
            if vertex.id in contents:
                vertex_area = area_id
                break
        print(f"    Area: {vertex_area} (sheet={graph.sheet})")
        
        if vertex_area == graph.sheet:
            print(f"    -> Adding to MAIN GRAPH (sheet level)")
        else:
            print(f"    -> Should be in cluster for area {vertex_area}")
    
    # Add edges
    print(f"\nAdding edges:")
    for edge in graph.E:
        node_name = integration._get_node_name(edge.id)
        print(f"  Edge {edge.id} -> {node_name}")
        
        # Check which area this edge is in
        edge_area = None
        for area_id, contents in graph.area.items():
            if edge.id in contents:
                edge_area = area_id
                break
        print(f"    Area: {edge_area} (sheet={graph.sheet})")
        
        if edge_area == graph.sheet:
            print(f"    -> Adding to MAIN GRAPH (sheet level)")
        else:
            print(f"    -> Should be in cluster for area {edge_area}")
    
    # Add cuts
    print(f"\nAdding cuts:")
    for cut in graph.Cut:
        cluster_name = integration._get_cluster_name(cut.id)
        print(f"  Cut {cut.id} -> {cluster_name}")
        
        # Check what's inside this cut
        cut_contents = graph.area.get(cut.id, frozenset())
        print(f"    Contents: {list(cut_contents)}")
    
    # Generate the actual DOT
    result = integration.calculate_layout(graph)
    
    print(f"\n=== Generated DOT ===")
    print(result.dot_source)
    
    print(f"\n=== PROBLEM ANALYSIS ===")
    
    # The issue might be in the edge connections
    # If we have: v_0 at sheet level, p_1 at sheet level, p_2 in cluster
    # But both p_1 and p_2 connect to v_0
    # Graphviz might be pulling v_0 into the cluster to minimize edge lengths
    
    print(f"Hypothesis: Graphviz is moving the vertex inside the cut")
    print(f"because it has edges connecting to elements inside the cut.")
    print(f"This violates EG semantics where area containment is logical, not spatial.")
    
    print(f"\nPossible solutions:")
    print(f"1. Use invisible/constraint edges to keep vertices in their logical areas")
    print(f"2. Use different Graphviz layout algorithms (neato, fdp, etc.)")
    print(f"3. Add explicit positioning constraints")
    print(f"4. Use subgraph clusters for sheet-level elements too")

def test_simple_vertex_only():
    """Test with just a vertex to see base behavior."""
    
    print(f"\n{'='*60}")
    print("Testing Simple Vertex Only")
    print(f"{'='*60}")
    
    # Create a minimal graph with just a vertex
    from egi_core_dau import RelationalGraphWithCuts, Vertex
    
    # Create empty graph
    graph = RelationalGraphWithCuts.create_empty_graph()
    
    # Add a single vertex at sheet level
    vertex = Vertex(id="test_vertex", label="x", is_generic=True)
    graph = graph.with_vertex(vertex, area_id=graph.sheet)
    
    print(f"Graph with single vertex:")
    print(f"  Sheet: {graph.sheet}")
    print(f"  Area mapping: {dict(graph.area)}")
    
    # Generate DOT
    integration = GraphvizLayoutIntegration()
    result = integration.calculate_layout(graph)
    
    print(f"\nDOT for single vertex:")
    print(result.dot_source)
    
    print(f"\nCoordinates:")
    for element_id, coords in result.node_positions.items():
        print(f"  {element_id}: {coords}")

if __name__ == "__main__":
    debug_dot_structure()
    test_simple_vertex_only()
