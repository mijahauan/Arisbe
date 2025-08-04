#!/usr/bin/env python3
"""
Deep analysis of DOT structure generation to find the root cause of area assignment bugs.
"""

from egif_parser_dau import EGIFParser
from graphviz_layout_integration import GraphvizLayoutIntegration

def analyze_problematic_cases():
    """Analyze the specific problematic cases in detail."""
    
    print("=== DEEP DOT STRUCTURE ANALYSIS ===")
    
    # Test cases that are failing
    test_cases = [
        ("Mixed Cut/Sheet", '*x (Human x) ~[ (Mortal x) ]'),
        ("Double Negation", '~[ ~[ (Human "Socrates") ] ]'),
        ("Sibling Cuts", '*x ~[ (P x) ] ~[ (Q x) ]'),
        ("Nested Cuts", '*x ~[ *y (P x) ~[ (Q y) ] ]')
    ]
    
    for name, egif in test_cases:
        print(f"\n{'='*60}")
        print(f"ANALYZING: {name}")
        print(f"EGIF: {egif}")
        print(f"{'='*60}")
        
        # Parse EGIF
        parser = EGIFParser(egif)
        graph = parser.parse()
        
        print(f"\n--- EGI STRUCTURE ---")
        print(f"Sheet: {graph.sheet}")
        print(f"Vertices: {[(v.id, v.label, v.is_generic) for v in graph.V]}")
        print(f"Edges: {[(e.id, graph.get_relation_name(e.id)) for e in graph.E]}")
        print(f"Cuts: {[c.id for c in graph.Cut]}")
        
        print(f"\n--- AREA MAPPING ---")
        for area_id, contents in graph.area.items():
            area_type = "SHEET" if area_id == graph.sheet else "CUT"
            print(f"  {area_type} {area_id}: {list(contents)}")
        
        # Generate DOT and analyze
        integration = GraphvizLayoutIntegration()
        result = integration.calculate_layout(graph)
        
        print(f"\n--- GENERATED DOT ---")
        print(result.dot_source)
        
        print(f"\n--- NODE MAPPING ---")
        for egi_id, dot_name in integration.node_mapping.items():
            element_type = "VERTEX" if egi_id in {v.id for v in graph.V} else "EDGE"
            print(f"  {element_type} {egi_id} -> {dot_name}")
        
        print(f"\n--- CLUSTER MAPPING ---")
        for cut_id, cluster_name in integration.cluster_mapping.items():
            print(f"  CUT {cut_id} -> {cluster_name}")
        
        # Analyze DOT structure manually
        print(f"\n--- DOT STRUCTURE ANALYSIS ---")
        dot_lines = result.dot_source.split('\n')
        
        # Track what's at each level
        main_level = []
        clusters = {}
        current_cluster = None
        cluster_depth = 0
        
        for line in dot_lines:
            line = line.strip()
            
            if 'subgraph cluster_' in line:
                current_cluster = line.split()[1].rstrip(' {')
                clusters[current_cluster] = []
                cluster_depth += 1
                print(f"    ENTERING CLUSTER: {current_cluster} (depth {cluster_depth})")
                
            elif line == '}' and current_cluster:
                print(f"    EXITING CLUSTER: {current_cluster}")
                current_cluster = None
                cluster_depth -= 1
                
            elif '[label=' in line and not line.startswith('//'):
                node_name = line.split()[0]
                if current_cluster:
                    clusters[current_cluster].append(node_name)
                    print(f"      IN CLUSTER {current_cluster}: {node_name}")
                else:
                    main_level.append(node_name)
                    print(f"      AT MAIN LEVEL: {node_name}")
        
        print(f"\n--- FINAL STRUCTURE ---")
        print(f"  Main level: {main_level}")
        for cluster, nodes in clusters.items():
            print(f"  {cluster}: {nodes}")
        
        # Check for logical errors
        print(f"\n--- LOGICAL VALIDATION ---")
        
        # Check if sheet-level vertices are correctly placed
        sheet_vertices = []
        for element_id in graph.area.get(graph.sheet, frozenset()):
            if element_id in {v.id for v in graph.V}:
                sheet_vertices.append(element_id)
        
        print(f"  Sheet vertices (should be at main level): {sheet_vertices}")
        
        for vertex_id in sheet_vertices:
            if vertex_id in integration.node_mapping:
                dot_name = integration.node_mapping[vertex_id]
                if dot_name in main_level:
                    print(f"    ✅ {vertex_id} -> {dot_name} correctly at main level")
                else:
                    print(f"    ❌ {vertex_id} -> {dot_name} INCORRECTLY in cluster!")
                    # Find which cluster
                    for cluster, nodes in clusters.items():
                        if dot_name in nodes:
                            print(f"        Found in {cluster}")
        
        # Check cut nesting
        print(f"\n  Cut nesting validation:")
        for cut in graph.Cut:
            cut_contents = graph.area.get(cut.id, frozenset())
            child_cuts = [c for c in cut_contents if c in {cut.id for cut in graph.Cut}]
            if child_cuts:
                print(f"    Cut {cut.id} should contain child cuts: {child_cuts}")
                # Check if DOT reflects this nesting
                if cut.id in integration.cluster_mapping:
                    parent_cluster = integration.cluster_mapping[cut.id]
                    print(f"    Parent cluster: {parent_cluster}")
                    for child_cut_id in child_cuts:
                        if child_cut_id in integration.cluster_mapping:
                            child_cluster = integration.cluster_mapping[child_cut_id]
                            print(f"    Child cluster: {child_cluster}")
                            # This is where we need to check if child is inside parent in DOT

def check_graphviz_nesting():
    """Check if Graphviz is properly handling nested subgraphs."""
    
    print(f"\n{'='*60}")
    print("TESTING GRAPHVIZ NESTING CAPABILITY")
    print(f"{'='*60}")
    
    # Create a simple nested DOT to test Graphviz behavior
    import graphviz
    
    test_dot = graphviz.Digraph('test_nesting')
    test_dot.attr(rankdir='TB')
    
    # Main level node
    test_dot.node('main_node', label='Main', shape='circle')
    
    # Outer cluster
    with test_dot.subgraph(name='cluster_outer') as outer:
        outer.attr(style='rounded', color='blue', label='Outer')
        outer.node('outer_node', label='Outer', shape='box')
        
        # Inner cluster
        with outer.subgraph(name='cluster_inner') as inner:
            inner.attr(style='rounded', color='red', label='Inner')
            inner.node('inner_node', label='Inner', shape='box')
    
    print("Generated test DOT:")
    print(test_dot.source)
    
    # Try to render and see coordinates
    try:
        svg = test_dot.pipe(format='svg', encoding='utf-8')
        print(f"\nSVG generated successfully ({len(svg)} chars)")
        
        # Quick coordinate check
        import re
        vertices = re.findall(r'<ellipse[^>]*cx="([^"]*)"[^>]*cy="([^"]*)"', svg)
        boxes = re.findall(r'<polygon[^>]*points="([^"]*)"', svg)
        
        print(f"Found {len(vertices)} vertices, {len(boxes)} boxes")
        
    except Exception as e:
        print(f"Error rendering test DOT: {e}")

if __name__ == "__main__":
    analyze_problematic_cases()
    check_graphviz_nesting()
