#!/usr/bin/env python3
"""
Debug the critical area assignment bug where vertices are placed in wrong areas.
"""

from egif_parser_dau import EGIFParser
from graphviz_layout_integration import GraphvizLayoutIntegration

def debug_area_assignment():
    """Debug area assignment for problematic EGIF cases."""
    
    print("=== Debugging Critical Area Assignment Bug ===")
    
    # Test the problematic case
    egif_text = '*x (Human x) ~[ (Mortal x) ]'
    
    print(f"EGIF: {egif_text}")
    print("Expected structure:")
    print("  Sheet level: *x, (Human x)")
    print("  Cut level: (Mortal x)")
    print("  *x should be OUTSIDE all cuts!")
    
    # Parse and analyze
    parser = EGIFParser(egif_text)
    graph = parser.parse()
    
    print(f"\nEGI Analysis:")
    print(f"  Vertices: {[(v.id, v.label, v.is_generic) for v in graph.V]}")
    print(f"  Edges: {[(e.id, graph.get_relation_name(e.id)) for e in graph.E]}")
    print(f"  Cuts: {[c.id for c in graph.Cut]}")
    print(f"  Sheet: {graph.sheet}")
    
    print(f"\nArea Mapping:")
    for area_id, contents in graph.area.items():
        print(f"  {area_id}: {list(contents)}")
    
    # Check which area each element is in
    print(f"\nElement Area Assignment:")
    for vertex in graph.V:
        area = None
        for area_id, contents in graph.area.items():
            if vertex.id in contents:
                area = area_id
                break
        print(f"  Vertex {vertex.id} ({vertex.label}): in area {area}")
    
    for edge in graph.E:
        area = None
        for area_id, contents in graph.area.items():
            if edge.id in contents:
                area = area_id
                break
        print(f"  Edge {edge.id} ({graph.get_relation_name(edge.id)}): in area {area}")
    
    # Test Graphviz DOT generation
    integration = GraphvizLayoutIntegration()
    result = integration.calculate_layout(graph)
    
    print(f"\nGraphviz DOT Structure:")
    print(result.dot_source)
    
    print(f"\nNode Mapping:")
    print(f"  {integration.node_mapping}")
    
    print(f"\nCluster Mapping:")
    print(f"  {integration.cluster_mapping}")
    
    # Analyze the DOT structure
    dot_lines = result.dot_source.split('\n')
    print(f"\nDOT Analysis:")
    
    sheet_elements = []
    cut_elements = {}
    
    current_cluster = None
    for line in dot_lines:
        line = line.strip()
        if 'subgraph cluster_' in line:
            current_cluster = line.split()[1].rstrip(' {')
            cut_elements[current_cluster] = []
        elif '[label=' in line and current_cluster:
            # Element inside a cluster
            node_name = line.split()[0]
            cut_elements[current_cluster].append(node_name)
        elif '[label=' in line and not current_cluster:
            # Element at sheet level
            node_name = line.split()[0]
            sheet_elements.append(node_name)
        elif line == '}' and current_cluster:
            current_cluster = None
    
    print(f"  Sheet level elements: {sheet_elements}")
    for cluster, elements in cut_elements.items():
        print(f"  {cluster} elements: {elements}")
    
    # Check if vertex is wrongly placed
    vertex_node = None
    for element_id, node_name in integration.node_mapping.items():
        if element_id in {v.id for v in graph.V}:
            vertex_node = node_name
            break
    
    if vertex_node:
        if vertex_node in sheet_elements:
            print(f"\n✅ Vertex {vertex_node} correctly placed at sheet level")
        else:
            print(f"\n❌ BUG: Vertex {vertex_node} incorrectly placed inside a cut!")
            for cluster, elements in cut_elements.items():
                if vertex_node in elements:
                    print(f"    Found in {cluster} - this is WRONG!")

def test_multiple_cases():
    """Test multiple problematic cases."""
    
    print(f"\n{'='*60}")
    print("Testing Multiple Problematic Cases")
    print(f"{'='*60}")
    
    test_cases = [
        '*x (Human x) ~[ (Mortal x) ]',
        '*x *y (Loves x y) ~[ (Human x) ] ~[ (Human y) ]',
        '(Human "Socrates") ~[ (Mortal "Socrates") ]',
        '*x *y *z (Triangle x y z) ~[ ~[ (Equal x y) ] ]'
    ]
    
    for egif in test_cases:
        print(f"\n--- Testing: {egif} ---")
        
        try:
            parser = EGIFParser(egif)
            graph = parser.parse()
            
            # Find sheet-level elements
            sheet_contents = graph.area.get(graph.sheet, frozenset())
            print(f"Sheet contents: {list(sheet_contents)}")
            
            # Find elements in cuts
            for cut in graph.Cut:
                cut_contents = graph.area.get(cut.id, frozenset())
                print(f"Cut {cut.id} contents: {list(cut_contents)}")
            
            # Quick DOT check
            integration = GraphvizLayoutIntegration()
            result = integration.calculate_layout(graph)
            
            # Count elements at each level
            dot_lines = result.dot_source.split('\n')
            sheet_count = sum(1 for line in dot_lines if '[label=' in line and 'subgraph' not in line and not any('cluster_' in prev for prev in dot_lines[:dot_lines.index(line)]))
            
            print(f"Elements at sheet level in DOT: {sheet_count}")
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    debug_area_assignment()
    test_multiple_cases()
    
    print(f"\n🔍 CONCLUSION:")
    print(f"If vertices defined at sheet level are appearing inside cuts,")
    print(f"the bug is in the Graphviz DOT generation area assignment logic.")
