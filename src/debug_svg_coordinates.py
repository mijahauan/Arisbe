#!/usr/bin/env python3
"""
Debug SVG coordinate extraction to find why vertices appear in wrong visual positions.
"""

from egif_parser_dau import EGIFParser
from graphviz_layout_integration import GraphvizLayoutIntegration

def debug_svg_coordinates():
    """Debug SVG coordinate extraction for problematic case."""
    
    print("=== Debugging SVG Coordinate Extraction ===")
    
    # Test the problematic case
    egif_text = '*x (Human x) ~[ (Mortal x) ]'
    
    print(f"EGIF: {egif_text}")
    print("Expected: *x should be OUTSIDE the cut visually")
    
    # Parse and analyze
    parser = EGIFParser(egif_text)
    graph = parser.parse()
    
    # Generate layout
    integration = GraphvizLayoutIntegration()
    result = integration.calculate_layout(graph)
    
    print(f"\n=== DOT Source ===")
    print(result.dot_source)
    
    print(f"\n=== Raw SVG Output ===")
    print(result.svg_content[:2000] + "..." if len(result.svg_content) > 2000 else result.svg_content)
    
    print(f"\n=== Coordinate Extraction Analysis ===")
    
    # Manually extract coordinates to see what's happening
    import re
    
    # Find all vertex positions
    vertex_pattern = r'<ellipse[^>]*cx="([^"]*)"[^>]*cy="([^"]*)"[^>]*>'
    vertices = re.findall(vertex_pattern, result.svg_content)
    print(f"Vertices found: {vertices}")
    
    # Find all text elements (predicates)
    text_pattern = r'<text[^>]*x="([^"]*)"[^>]*y="([^"]*)"[^>]*>([^<]*)</text>'
    texts = re.findall(text_pattern, result.svg_content)
    print(f"Text elements found: {texts}")
    
    # Find all polygons (predicate boxes)
    polygon_pattern = r'<polygon[^>]*points="([^"]*)"[^>]*>'
    polygons = re.findall(polygon_pattern, result.svg_content)
    print(f"Polygons found: {len(polygons)} polygons")
    for i, points in enumerate(polygons):
        print(f"  Polygon {i}: {points}")
    
    # Find all cluster boundaries
    cluster_pattern = r'<g id="cluster_[^"]*".*?<polygon[^>]*points="([^"]*)"'
    clusters = re.findall(cluster_pattern, result.svg_content, re.DOTALL)
    print(f"Clusters found: {len(clusters)} clusters")
    for i, points in enumerate(clusters):
        print(f"  Cluster {i}: {points}")
    
    print(f"\n=== Layout Result Coordinates ===")
    for element_id, coords in result.coordinates.items():
        element_type = "Unknown"
        if element_id.startswith('v_'):
            element_type = "Vertex"
        elif element_id.startswith('p_'):
            element_type = "Predicate"
        elif element_id.startswith('cluster_'):
            element_type = "Cut"
        
        print(f"  {element_type} {element_id}: {coords}")
    
    print(f"\n=== Spatial Analysis ===")
    
    # Check if vertex is inside cut boundary
    vertex_coords = None
    cut_bounds = None
    
    for element_id, coords in result.coordinates.items():
        if element_id.startswith('v_'):
            vertex_coords = coords
        elif element_id.startswith('cluster_'):
            cut_bounds = coords
    
    if vertex_coords and cut_bounds:
        vx, vy = vertex_coords
        
        if isinstance(cut_bounds, list) and len(cut_bounds) > 0:
            # Get bounding box of cut
            xs = [p[0] for p in cut_bounds]
            ys = [p[1] for p in cut_bounds]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            
            print(f"  Vertex position: ({vx}, {vy})")
            print(f"  Cut bounds: x=[{min_x}, {max_x}], y=[{min_y}, {max_y}]")
            
            if min_x <= vx <= max_x and min_y <= vy <= max_y:
                print(f"  ❌ BUG: Vertex is INSIDE cut bounds!")
            else:
                print(f"  ✅ Vertex is OUTSIDE cut bounds")
    
    print(f"\n=== Node Mapping Check ===")
    print(f"Node mapping: {integration.node_mapping}")
    print(f"Cluster mapping: {integration.cluster_mapping}")

def test_simple_case():
    """Test an even simpler case to isolate the issue."""
    
    print(f"\n{'='*60}")
    print("Testing Simple Case: Just a vertex and predicate")
    print(f"{'='*60}")
    
    egif_text = '(Human "Socrates")'
    
    print(f"EGIF: {egif_text}")
    
    # Parse and analyze
    parser = EGIFParser(egif_text)
    graph = parser.parse()
    
    # Generate layout
    integration = GraphvizLayoutIntegration()
    result = integration.calculate_layout(graph)
    
    print(f"\nDOT Source:")
    print(result.dot_source)
    
    print(f"\nCoordinates:")
    for element_id, coords in result.coordinates.items():
        print(f"  {element_id}: {coords}")

if __name__ == "__main__":
    debug_svg_coordinates()
    test_simple_case()
