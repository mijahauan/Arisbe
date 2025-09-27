#!/usr/bin/env python3
"""
Debug Port Assignment Issues

Debug why the nearest port assignment isn't working consistently.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from definitive_egi_layout_engine import DefinitiveEGILayoutEngine
from graphviz_svg_renderer import GraphvizSVGRenderer
from style_specification import load_default_dau_style
from egi_io import load_egi_json


def debug_specific_graphs():
    """Debug the specific problematic graphs"""
    
    print("🔍 DEBUGGING PORT ASSIGNMENT ISSUES")
    print("=" * 45)
    
    layout_engine = DefinitiveEGILayoutEngine()
    style = load_default_dau_style()
    
    # Test the problematic graphs
    corpus_dir = Path(__file__).parent.parent / 'corpus' / 'graphs'
    
    test_cases = [
        'sowa_2011_p356_quantification',
        'roberts_1973_p57_disjunction'
    ]
    
    for graph_name in test_cases:
        graph_dir = corpus_dir / graph_name
        if not graph_dir.exists():
            print(f"❌ Graph not found: {graph_name}")
            continue
            
        egi_files = list(graph_dir.glob("*.egi.json"))
        if not egi_files:
            print(f"❌ No EGI file found in: {graph_name}")
            continue
        
        print(f"\n🧪 DEBUGGING: {graph_name}")
        print("-" * 40)
        
        try:
            # Load EGI
            egi = load_egi_json(str(egi_files[0]))
            print(f"   📁 Loaded: {len(egi.V)} vertices, {len(egi.E)} edges")
            
            # Generate layout
            dto = layout_engine.generate_layout(egi, style)
            
            # Debug each edge's port assignments
            for edge_label in dto.edge_labels:
                print(f"\n   🏷️  Edge: '{edge_label.label}'")
                print(f"      Label rect: ({edge_label.rect.x:.1f}, {edge_label.rect.y:.1f}) {edge_label.rect.width:.1f}x{edge_label.rect.height:.1f}")
                
                # Show available ports
                print(f"      Available ports: {len(edge_label.connection_ports)}")
                for port in edge_label.connection_ports:
                    print(f"        Port {port.port_id}: {port.direction} at ({port.position[0]:.1f}, {port.position[1]:.1f})")
                
                # Show vertex positions and their connections
                vertex_sequence = egi.nu.get(edge_label.id, [])
                print(f"      Vertex sequence: {vertex_sequence}")
                
                for vertex_id in vertex_sequence:
                    vertex = next((v for v in dto.vertices if v.id == vertex_id), None)
                    if vertex:
                        print(f"        Vertex {vertex_id}: at ({vertex.pos[0]:.1f}, {vertex.pos[1]:.1f})")
                        
                        # Calculate distances to each port
                        distances = []
                        for port in edge_label.connection_ports:
                            distance = ((vertex.pos[0] - port.position[0]) ** 2 + (vertex.pos[1] - port.position[1]) ** 2) ** 0.5
                            distances.append((port.port_id, port.direction, distance))
                        
                        # Sort by distance
                        distances.sort(key=lambda x: x[2])
                        print(f"          Distances to ports:")
                        for port_id, direction, distance in distances:
                            print(f"            Port {port_id} ({direction}): {distance:.1f}")
                        
                        # Show which port should be nearest
                        nearest_port_id, nearest_direction, nearest_distance = distances[0]
                        print(f"          → Should connect to Port {nearest_port_id} ({nearest_direction}) at distance {nearest_distance:.1f}")
                
                # Show actual ligature connections
                edge_ligatures = [lig for lig in dto.ligatures if lig.end_edge_id == edge_label.id]
                print(f"      Actual ligatures: {len(edge_ligatures)}")
                for ligature in edge_ligatures:
                    if ligature.path_points:
                        start_point = ligature.path_points[0]
                        end_point = ligature.path_points[-1]
                        print(f"        Ligature from {ligature.start_vertex_id}:")
                        print(f"          Start: ({start_point[0]:.1f}, {start_point[1]:.1f})")
                        print(f"          End: ({end_point[0]:.1f}, {end_point[1]:.1f})")
                        
                        # Find which port this end point is closest to
                        closest_port = None
                        closest_distance = float('inf')
                        for port in edge_label.connection_ports:
                            distance = ((end_point[0] - port.position[0]) ** 2 + (end_point[1] - port.position[1]) ** 2) ** 0.5
                            if distance < closest_distance:
                                closest_distance = distance
                                closest_port = port
                        
                        if closest_port:
                            print(f"          → Actually connected to Port {closest_port.port_id} ({closest_port.direction}) at distance {closest_distance:.1f}")
                        
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            import traceback
            traceback.print_exc()


def test_assignment_algorithm_directly():
    """Test the assignment algorithm with known data"""
    
    print("\n🧠 TESTING ASSIGNMENT ALGORITHM DIRECTLY")
    print("=" * 45)
    
    layout_engine = DefinitiveEGILayoutEngine()
    
    # Create a mock scenario
    from definitive_egi_layout_engine import ConnectionPort, Rect
    
    # Mock edge label with ports
    rect = Rect(100, 100, 80, 20)
    ports = layout_engine._calculate_connection_ports(rect, 2)
    
    print(f"📦 Mock edge label: {rect.width}x{rect.height} at ({rect.x}, {rect.y})")
    print(f"   Generated ports:")
    for port in ports:
        print(f"     Port {port.port_id}: {port.direction} at ({port.position[0]:.1f}, {port.position[1]:.1f})")
    
    # Mock vertices at different positions
    class MockVertex:
        def __init__(self, vertex_id, x, y):
            self.id = vertex_id
            self.pos = (x, y)
    
    test_cases = [
        {"vertices": [MockVertex("v1", 50, 110), MockVertex("v2", 200, 110)], "description": "Left and right of label"},
        {"vertices": [MockVertex("v1", 140, 50), MockVertex("v2", 140, 150)], "description": "Above and below label"},
        {"vertices": [MockVertex("v1", 80, 90), MockVertex("v2", 160, 130)], "description": "Diagonal positions"},
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test Case {i}: {test_case['description']}")
        vertices = test_case['vertices']
        vertex_sequence = [v.id for v in vertices]
        
        # Mock edge label
        class MockEdgeLabel:
            def __init__(self):
                self.connection_ports = ports
        
        edge_label = MockEdgeLabel()
        
        # Test assignment
        assignments = layout_engine._assign_nearest_ports(vertex_sequence, edge_label, vertices)
        
        print(f"   Vertex positions:")
        for vertex in vertices:
            print(f"     {vertex.id}: ({vertex.pos[0]:.1f}, {vertex.pos[1]:.1f})")
        
        print(f"   Port assignments:")
        for vertex_id, assigned_port in assignments.items():
            vertex = next(v for v in vertices if v.id == vertex_id)
            distance = layout_engine._calculate_distance(vertex.pos, assigned_port.position)
            print(f"     {vertex_id} → Port {assigned_port.port_id} ({assigned_port.direction}) at distance {distance:.1f}")
        
        # Verify optimality
        print(f"   Optimality check:")
        for vertex_id, assigned_port in assignments.items():
            vertex = next(v for v in vertices if v.id == vertex_id)
            assigned_distance = layout_engine._calculate_distance(vertex.pos, assigned_port.position)
            
            # Check if there's a closer port that's not assigned
            used_ports = set(p.port_id for p in assignments.values())
            for port in ports:
                if port.port_id not in used_ports:
                    distance = layout_engine._calculate_distance(vertex.pos, port.position)
                    if distance < assigned_distance:
                        print(f"     ⚠️  {vertex_id} could be closer to Port {port.port_id} ({port.direction}) at distance {distance:.1f}")
                        break
            else:
                print(f"     ✅ {vertex_id} optimally assigned")


if __name__ == "__main__":
    debug_specific_graphs()
    test_assignment_algorithm_directly()
    
    print("\n🔍 DEBUG COMPLETE!")
    print("   Check the output above to identify assignment issues")
