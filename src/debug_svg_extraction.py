#!/usr/bin/env python3
"""
Debug SVG coordinate extraction from Graphviz output.
This investigates why we're not getting all the visual elements.
"""

from egif_parser_dau import EGIFParser
from graphviz_layout_integration import GraphvizLayoutIntegration

def debug_svg_extraction():
    """Debug the SVG coordinate extraction process."""
    
    print("=== Debugging SVG Coordinate Extraction ===")
    
    # Create test case
    egif_text = '~[ ~[ (P "x") ] ~[ (Q "x") ] ]'
    parser = EGIFParser(egif_text)
    graph = parser.parse()
    
    print(f"EGI structure:")
    print(f"  Vertices: {[(v.id, v.label) for v in graph.V]}")
    print(f"  Edges: {[(e.id, graph.get_relation_name(e.id)) for e in graph.E]}")
    print(f"  Cuts: {[c.id for c in graph.Cut]}")
    print(f"  Area mapping: {dict(graph.area)}")
    
    # Test Graphviz integration
    integration = GraphvizLayoutIntegration()
    result = integration.calculate_layout(graph)
    
    print(f"\nGraphviz results:")
    print(f"  Primitives: {len(result.primitives)}")
    print(f"  Node positions: {len(result.node_positions)}")
    print(f"  Cluster bounds: {len(result.cluster_bounds)}")
    
    print(f"\nDOT source:")
    print(result.dot_source)
    
    print(f"\nNode mapping: {integration.node_mapping}")
    print(f"Cluster mapping: {integration.cluster_mapping}")
    
    # Save SVG for inspection
    print(f"\nSVG output (first 1000 chars):")
    print(result.svg_source[:1000])
    print("...")
    
    # Save SVG to file for inspection
    with open('/tmp/debug_graphviz.svg', 'w') as f:
        f.write(result.svg_source)
    print(f"✓ Full SVG saved to /tmp/debug_graphviz.svg")
    
    # Debug coordinate extraction
    print(f"\nExtracting coordinates...")
    node_positions, cluster_bounds = integration._extract_coordinates_from_svg(result.svg_source)
    
    print(f"Extracted node positions: {node_positions}")
    print(f"Extracted cluster bounds: {cluster_bounds}")
    
    # Debug primitive creation
    print(f"\nPrimitive details:")
    for i, primitive in enumerate(result.primitives):
        print(f"  {i}: {primitive}")
    
    return result

def test_simple_graphviz():
    """Test simple Graphviz generation without EGI complexity."""
    
    print(f"\n=== Testing Simple Graphviz Generation ===")
    
    import graphviz
    
    # Create simple test DOT
    dot = graphviz.Digraph(comment='Simple Test')
    dot.attr(rankdir='TB')
    
    with dot.subgraph(name='cluster_0') as outer:
        outer.attr(style='rounded', color='blue', label='Outer')
        
        with outer.subgraph(name='cluster_1') as inner1:
            inner1.attr(style='rounded', color='red', label='Inner1')
            inner1.node('A', 'A')
            inner1.node('B', 'B')
            inner1.edge('A', 'B')
        
        with outer.subgraph(name='cluster_2') as inner2:
            inner2.attr(style='rounded', color='red', label='Inner2')
            inner2.node('C', 'C')
            inner2.node('D', 'D')
            inner2.edge('C', 'D')
    
    print(f"Simple DOT:")
    print(dot.source)
    
    # Generate SVG
    svg_output = dot.pipe(format='svg', encoding='utf-8')
    
    # Save for inspection
    with open('/tmp/simple_test.svg', 'w') as f:
        f.write(svg_output)
    print(f"✓ Simple SVG saved to /tmp/simple_test.svg")
    
    print(f"Simple SVG (first 500 chars):")
    print(svg_output[:500])
    
    return svg_output

if __name__ == "__main__":
    # Debug the full pipeline
    debug_svg_extraction()
    
    # Test simple case
    test_simple_graphviz()
    
    print(f"\n🔍 Debug complete. Check /tmp/debug_graphviz.svg and /tmp/simple_test.svg")
