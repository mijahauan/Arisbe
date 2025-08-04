#!/usr/bin/env python3
"""
Debug script to investigate Graphviz integration issues.
"""

from egi_core_dau import create_empty_graph, create_vertex, create_edge, create_cut
from graphviz_layout_integration import GraphvizLayoutIntegration

def debug_egi_structure():
    """Debug the EGI graph structure to understand area mapping."""
    
    print("=== Debugging EGI Graph Structure ===")
    
    # Create test graph: ~[ ~[ (P "x") ] ~[ (Q "x") ] ]
    graph = create_empty_graph()
    print(f"Empty graph sheet: {graph.sheet}")
    print(f"Empty graph area mapping: {dict(graph.area)}")
    
    # Add outer cut
    outer_cut = create_cut()
    graph = graph.with_cut(outer_cut)
    print(f"\nAfter adding outer cut {outer_cut.id}:")
    print(f"  Cuts: {[c.id for c in graph.Cut]}")
    print(f"  Area mapping: {dict(graph.area)}")
    
    # Add first inner cut
    inner_cut1 = create_cut()
    graph = graph.with_cut(inner_cut1, outer_cut.id)
    print(f"\nAfter adding inner cut 1 {inner_cut1.id}:")
    print(f"  Cuts: {[c.id for c in graph.Cut]}")
    print(f"  Area mapping: {dict(graph.area)}")
    
    # Add vertex to inner cut 1
    x_vertex1 = create_vertex("x", is_generic=False)
    graph = graph.with_vertex_in_context(x_vertex1, inner_cut1.id)
    print(f"\nAfter adding vertex {x_vertex1.id} to inner cut 1:")
    print(f"  Vertices: {[(v.id, v.label) for v in graph.V]}")
    print(f"  Area mapping: {dict(graph.area)}")
    
    # Add predicate to inner cut 1
    p_edge = create_edge()
    graph = graph.with_edge(p_edge, (x_vertex1.id,), "P", inner_cut1.id)
    print(f"\nAfter adding predicate P {p_edge.id} to inner cut 1:")
    print(f"  Edges: {[e.id for e in graph.E]}")
    print(f"  Relations: {dict(graph.rel)}")
    print(f"  Nu mapping: {dict(graph.nu)}")
    print(f"  Area mapping: {dict(graph.area)}")
    
    # Add second inner cut
    inner_cut2 = create_cut()
    graph = graph.with_cut(inner_cut2, outer_cut.id)
    print(f"\nAfter adding inner cut 2 {inner_cut2.id}:")
    print(f"  Cuts: {[c.id for c in graph.Cut]}")
    print(f"  Area mapping: {dict(graph.area)}")
    
    # Add vertex to inner cut 2
    x_vertex2 = create_vertex("x", is_generic=False)
    graph = graph.with_vertex_in_context(x_vertex2, inner_cut2.id)
    print(f"\nAfter adding vertex {x_vertex2.id} to inner cut 2:")
    print(f"  Vertices: {[(v.id, v.label) for v in graph.V]}")
    print(f"  Area mapping: {dict(graph.area)}")
    
    # Add predicate to inner cut 2
    q_edge = create_edge()
    graph = graph.with_edge(q_edge, (x_vertex2.id,), "Q", inner_cut2.id)
    print(f"\nFinal graph after adding predicate Q {q_edge.id}:")
    print(f"  Edges: {[e.id for e in graph.E]}")
    print(f"  Relations: {dict(graph.rel)}")
    print(f"  Nu mapping: {dict(graph.nu)}")
    print(f"  Area mapping: {dict(graph.area)}")
    
    return graph

def debug_graphviz_conversion():
    """Debug the Graphviz DOT conversion process."""
    
    print("\n=== Debugging Graphviz Conversion ===")
    
    # Create the graph
    graph = debug_egi_structure()
    
    # Test the integration
    integration = GraphvizLayoutIntegration()
    
    # Convert to DOT
    dot = integration._convert_egi_to_dot(graph)
    print(f"\nGenerated DOT source:")
    print(dot.source)
    
    # Test layout
    result = integration.calculate_layout(graph)
    print(f"\nLayout result:")
    print(f"  Primitives: {len(result.primitives)}")
    print(f"  Node positions: {len(result.node_positions)}")
    print(f"  Cluster bounds: {len(result.cluster_bounds)}")
    
    print(f"\nNode mapping: {integration.node_mapping}")
    print(f"Cluster mapping: {integration.cluster_mapping}")
    
    print(f"\nPrimitives details:")
    for i, primitive in enumerate(result.primitives):
        print(f"  {i}: {primitive}")
    
    return result

if __name__ == "__main__":
    debug_graphviz_conversion()
