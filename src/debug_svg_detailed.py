#!/usr/bin/env python3
"""
Detailed debugging of SVG coordinate extraction to find why predicates and cuts aren't being found.
"""

import xml.etree.ElementTree as ET
from egif_parser_dau import EGIFParser
from graphviz_layout_integration import GraphvizLayoutIntegration

def debug_svg_structure():
    """Debug the actual SVG structure to understand what elements exist."""
    
    print("=== Debugging SVG Structure in Detail ===")
    
    # Use perfect demo case
    egif_text = '~[ ~[ (Human "Socrates") ] ~[ (Mortal "Plato") ] ]'
    parser = EGIFParser(egif_text)
    graph = parser.parse()
    
    integration = GraphvizLayoutIntegration()
    result = integration.calculate_layout(graph)
    
    print(f"Expected elements in SVG:")
    print(f"  Vertices: v_0 (Plato), v_2 (Socrates)")
    print(f"  Predicates: p_1 (Mortal), p_3 (Human)")
    print(f"  Clusters: cluster_0 (outer), cluster_1 (Mortal), cluster_2 (Human)")
    
    # Parse SVG
    try:
        root = ET.fromstring(result.svg_source)
        
        print(f"\n=== SVG Element Analysis ===")
        
        # Find all g elements with class attributes
        all_g_elements = root.findall('.//{http://www.w3.org/2000/svg}g')
        print(f"Total <g> elements: {len(all_g_elements)}")
        
        # Analyze class attributes
        class_counts = {}
        for g in all_g_elements:
            class_attr = g.get('class', 'no-class')
            class_counts[class_attr] = class_counts.get(class_attr, 0) + 1
        
        print(f"Class distribution: {class_counts}")
        
        # Find nodes specifically
        nodes = root.findall('.//{http://www.w3.org/2000/svg}g[@class="node"]')
        print(f"\nFound {len(nodes)} node elements:")
        
        for i, node in enumerate(nodes):
            title = node.find('.//{http://www.w3.org/2000/svg}title')
            node_name = title.text if title is not None else "no-title"
            
            # Check for ellipse (vertex)
            ellipse = node.find('.//{http://www.w3.org/2000/svg}ellipse')
            # Check for polygon (predicate)
            polygon = node.find('.//{http://www.w3.org/2000/svg}polygon')
            
            shape_type = "ellipse" if ellipse is not None else ("polygon" if polygon is not None else "unknown")
            
            print(f"  Node {i}: {node_name} ({shape_type})")
            
            if ellipse is not None:
                cx = ellipse.get('cx', 'no-cx')
                cy = ellipse.get('cy', 'no-cy')
                print(f"    Ellipse at ({cx}, {cy})")
            
            if polygon is not None:
                points = polygon.get('points', 'no-points')
                print(f"    Polygon points: {points[:50]}...")
        
        # Find clusters specifically
        clusters = root.findall('.//{http://www.w3.org/2000/svg}g[@class="cluster"]')
        print(f"\nFound {len(clusters)} cluster elements:")
        
        for i, cluster in enumerate(clusters):
            title = cluster.find('.//{http://www.w3.org/2000/svg}title')
            cluster_name = title.text if title is not None else "no-title"
            print(f"  Cluster {i}: {cluster_name}")
        
        # Test the actual extraction method
        print(f"\n=== Testing Extraction Method ===")
        node_positions, cluster_bounds = integration._extract_coordinates_from_svg(result.svg_source)
        
        print(f"Extracted node positions: {node_positions}")
        print(f"Extracted cluster bounds: {cluster_bounds}")
        
        # Save SVG for manual inspection
        with open('/tmp/debug_detailed.svg', 'w') as f:
            f.write(result.svg_source)
        print(f"\n✓ SVG saved to /tmp/debug_detailed.svg")
        
        return len(nodes), len(clusters), node_positions, cluster_bounds
        
    except Exception as e:
        print(f"❌ SVG parsing failed: {e}")
        import traceback
        traceback.print_exc()
        return 0, 0, {}, {}

def test_manual_svg_extraction():
    """Test manual SVG extraction with simpler approach."""
    
    print(f"\n=== Testing Manual SVG Extraction ===")
    
    # Generate SVG
    egif_text = '~[ ~[ (Human "Socrates") ] ~[ (Mortal "Plato") ] ]'
    parser = EGIFParser(egif_text)
    graph = parser.parse()
    
    integration = GraphvizLayoutIntegration()
    result = integration.calculate_layout(graph)
    
    # Manual extraction approach
    svg_lines = result.svg_source.split('\n')
    
    print(f"Looking for key SVG patterns:")
    
    # Find lines with node information
    node_lines = [line for line in svg_lines if 'title>' in line and ('v_' in line or 'p_' in line)]
    print(f"Node title lines: {node_lines}")
    
    # Find lines with ellipse (vertices)
    ellipse_lines = [line for line in svg_lines if 'ellipse' in line]
    print(f"Ellipse lines: {ellipse_lines}")
    
    # Find lines with polygon (predicates and clusters)
    polygon_lines = [line for line in svg_lines if 'polygon' in line]
    print(f"Polygon lines: {polygon_lines}")
    
    # Find cluster information
    cluster_lines = [line for line in svg_lines if 'cluster' in line]
    print(f"Cluster lines: {cluster_lines}")

if __name__ == "__main__":
    print("🔍 Detailed SVG Structure Debugging")
    
    # Debug SVG structure
    node_count, cluster_count, positions, bounds = debug_svg_structure()
    
    # Test manual extraction
    test_manual_svg_extraction()
    
    print(f"\n📊 Summary:")
    print(f"  Nodes in SVG: {node_count}")
    print(f"  Clusters in SVG: {cluster_count}")
    print(f"  Extracted positions: {len(positions)}")
    print(f"  Extracted bounds: {len(bounds)}")
    
    if node_count > len(positions):
        print(f"❌ Missing {node_count - len(positions)} node positions!")
    if cluster_count > len(bounds):
        print(f"❌ Missing {cluster_count - len(bounds)} cluster bounds!")
    
    print(f"\n🔧 Next: Fix extraction method to find all elements")
