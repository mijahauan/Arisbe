#!/usr/bin/env python3
"""
Graphviz Layout Integration for Existential Graphs

This module integrates Graphviz-based hierarchical layout into the main
EG rendering pipeline, replacing the custom layout engine for cuts.
"""

import graphviz
import xml.etree.ElementTree as ET
import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

from egi_core_dau import RelationalGraphWithCuts


@dataclass
class GraphvizLayoutResult:
    """Result of Graphviz layout calculation with spatial primitives."""
    primitives: List[Dict[str, Any]]  # Spatial primitives for rendering
    svg_source: str  # Raw SVG output from Graphviz
    dot_source: str  # DOT source code
    node_positions: Dict[str, Tuple[float, float]]  # Node ID -> (x, y)
    cluster_bounds: Dict[str, List[Tuple[float, float]]]  # Cluster ID -> polygon points


class GraphvizLayoutIntegration:
    """
    Integration layer between EGI graphs and Graphviz layout engine.
    
    This class handles:
    1. EGI → DOT conversion with proper hierarchical structure
    2. Graphviz layout calculation
    3. SVG coordinate extraction
    4. Spatial primitive generation for rendering
    """
    
    def __init__(self):
        self.node_counter = 0
        self.cluster_counter = 0
        self.node_mapping = {}  # EGI element ID -> DOT node name
        self.cluster_mapping = {}  # EGI cut ID -> DOT cluster name
    
    def calculate_layout(self, graph: RelationalGraphWithCuts) -> GraphvizLayoutResult:
        """
        Calculate layout for an EGI graph using Graphviz.
        
        Args:
            graph: The EGI graph to layout
            
        Returns:
            GraphvizLayoutResult with spatial primitives for rendering
        """
        # Reset state
        self.node_counter = 0
        self.cluster_counter = 0
        self.node_mapping = {}
        self.cluster_mapping = {}
        
        # Convert EGI to DOT
        dot = self._convert_egi_to_dot(graph)
        
        # Generate SVG layout
        svg_source = dot.pipe(format='svg', encoding='utf-8')
        
        # Extract coordinates and create primitives
        node_positions, cluster_bounds = self._extract_coordinates_from_svg(svg_source)
        primitives = self._create_spatial_primitives(graph, node_positions, cluster_bounds)
        
        return GraphvizLayoutResult(
            primitives=primitives,
            svg_source=svg_source,
            dot_source=dot.source,
            node_positions=node_positions,
            cluster_bounds=cluster_bounds
        )
    
    def _convert_egi_to_dot(self, graph: RelationalGraphWithCuts) -> graphviz.Digraph:
        """Convert EGI graph to Graphviz DOT format with hierarchical structure."""
        dot = graphviz.Digraph(comment='EG Layout')
        dot.attr(
            rankdir='TB',
            splines='true', 
            overlap='false',
            sep='0.5',  # Separation between nodes
            esep='0.3'  # Separation between edges
        )
        
        # Process the sheet (root area) and all cuts
        self._process_area_hierarchical(dot, graph, graph.sheet)
        
        return dot
    
    def _process_area_hierarchical(self, dot: graphviz.Digraph, 
                                 graph: RelationalGraphWithCuts, 
                                 area_id: str) -> None:
        """Process an area and its contents hierarchically."""
        
        if area_id == graph.sheet:
            # Sheet level - process contents directly
            self._add_area_contents(dot, graph, area_id)
            
            # Process child cuts
            for child_id in graph.area.get(area_id, frozenset()):
                if child_id in {c.id for c in graph.Cut}:
                    self._process_cut_as_cluster(dot, graph, child_id)
        else:
            # This should be handled by _process_cut_as_cluster
            pass
    
    def _process_cut_as_cluster(self, dot: graphviz.Digraph,
                              graph: RelationalGraphWithCuts,
                              cut_id: str) -> None:
        """Process a cut as a Graphviz cluster subgraph."""
        
        cluster_name = f'cluster_{self.cluster_counter}'
        self.cluster_counter += 1
        self.cluster_mapping[cut_id] = cluster_name
        
        with dot.subgraph(name=cluster_name) as cluster:
            # Style the cut
            cluster.attr(
                style='rounded',
                color='blue',
                label='',  # No visible label for cuts
                margin='15',
                penwidth='2'
            )
            
            # Add contents of this cut
            self._add_area_contents(cluster, graph, cut_id)
            
            # Process child cuts recursively
            for child_id in graph.area.get(cut_id, frozenset()):
                if child_id in {c.id for c in graph.Cut}:
                    self._process_cut_as_cluster(cluster, graph, child_id)
    
    def _add_area_contents(self, target_graph: graphviz.Digraph,
                          graph: RelationalGraphWithCuts,
                          area_id: str) -> None:
        """Add vertices and edges that belong directly to this area."""
        
        # Add vertices in this area
        for element_id in graph.area.get(area_id, frozenset()):
            if element_id in {v.id for v in graph.V}:
                vertex = graph.get_vertex(element_id)
                node_name = f'v_{self.node_counter}'
                self.node_counter += 1
                self.node_mapping[element_id] = node_name
                
                # Style based on vertex type
                if vertex.label:
                    # Constant vertex
                    target_graph.node(node_name,
                                    label=vertex.label,
                                    shape='circle',
                                    style='filled',
                                    fillcolor='lightblue',
                                    fontsize='12')
                else:
                    # Variable vertex (line of identity)
                    target_graph.node(node_name,
                                    label='•',
                                    shape='circle',
                                    style='filled',
                                    fillcolor='black',
                                    fontcolor='white',
                                    width='0.3',
                                    height='0.3',
                                    fontsize='16')
        
        # Add edges (predicates) in this area
        for element_id in graph.area.get(area_id, frozenset()):
            if element_id in {e.id for e in graph.E}:
                edge = graph.get_edge(element_id)
                relation_name = graph.get_relation_name(element_id)
                pred_name = f'p_{self.node_counter}'
                self.node_counter += 1
                self.node_mapping[element_id] = pred_name
                
                # Create predicate node
                target_graph.node(pred_name,
                                label=relation_name,
                                shape='box',
                                style='filled',
                                fillcolor='lightyellow',
                                fontsize='12')
                
                # Connect to incident vertices
                incident_vertices = graph.get_incident_vertices(element_id)
                for i, vertex_id in enumerate(incident_vertices):
                    if vertex_id in self.node_mapping:
                        vertex_node = self.node_mapping[vertex_id]
                        target_graph.edge(pred_name, vertex_node,
                                        style='dashed',
                                        arrowhead='none',
                                        len='1.0')
    
    def _extract_coordinates_from_svg(self, svg_source: str) -> Tuple[Dict[str, Tuple[float, float]], 
                                                                   Dict[str, List[Tuple[float, float]]]]:
        """Extract node positions and cluster bounds from Graphviz SVG output."""
        node_positions = {}
        cluster_bounds = {}
        
        try:
            # Parse SVG
            root = ET.fromstring(svg_source)
            
            # Extract node positions
            for node in root.findall('.//{http://www.w3.org/2000/svg}g[@class="node"]'):
                # Get node title (contains node name)
                title = node.find('.//{http://www.w3.org/2000/svg}title')
                if title is not None:
                    node_name = title.text
                    
                    # Find ellipse for circular nodes (vertices)
                    ellipse = node.find('.//{http://www.w3.org/2000/svg}ellipse')
                    if ellipse is not None:
                        cx = float(ellipse.get('cx', 0))
                        cy = float(ellipse.get('cy', 0))
                        node_positions[node_name] = (cx, cy)
                        print(f"DEBUG: Found vertex {node_name} at ({cx}, {cy})")
                    else:
                        # Find polygon for rectangular nodes (predicates)
                        polygon = node.find('.//{http://www.w3.org/2000/svg}polygon')
                        if polygon is not None:
                            points_str = polygon.get('points', '')
                            print(f"DEBUG: Found predicate {node_name} with points: {points_str}")
                            if points_str:
                                points = self._parse_polygon_points(points_str)
                                if points:
                                    # Calculate center of polygon
                                    xs = [p[0] for p in points]
                                    ys = [p[1] for p in points]
                                    cx = sum(xs) / len(xs)
                                    cy = sum(ys) / len(ys)
                                    node_positions[node_name] = (cx, cy)
                                    print(f"DEBUG: Calculated predicate {node_name} center at ({cx}, {cy})")
                                else:
                                    print(f"DEBUG: Failed to parse points for {node_name}")
                            else:
                                print(f"DEBUG: No points string for {node_name}")
                        else:
                            print(f"DEBUG: No ellipse or polygon found for node {node_name}")
            
            # Extract cluster bounds
            for cluster in root.findall('.//{http://www.w3.org/2000/svg}g[@class="cluster"]'):
                # Get cluster title
                title = cluster.find('.//{http://www.w3.org/2000/svg}title')
                if title is not None:
                    cluster_name = title.text
                    print(f"DEBUG: Processing cluster {cluster_name}")
                    
                    # Find path element for cluster boundary (Graphviz uses path, not polygon for clusters)
                    path = cluster.find('.//{http://www.w3.org/2000/svg}path')
                    if path is not None:
                        d_attr = path.get('d', '')
                        print(f"DEBUG: Found cluster {cluster_name} path: {d_attr[:100]}...")
                        if d_attr:
                            # Parse path to get boundary points
                            bounds = self._parse_path_to_bounds(d_attr)
                            if bounds:
                                cluster_bounds[cluster_name] = bounds
                                print(f"DEBUG: Extracted cluster {cluster_name} bounds: {bounds}")
                            else:
                                print(f"DEBUG: Failed to parse path bounds for {cluster_name}")
                        else:
                            print(f"DEBUG: No path data for cluster {cluster_name}")
                    else:
                        # Try polygon as fallback
                        polygon = cluster.find('.//{http://www.w3.org/2000/svg}polygon')
                        if polygon is not None:
                            points_str = polygon.get('points', '')
                            print(f"DEBUG: Found cluster {cluster_name} polygon: {points_str[:100]}...")
                            if points_str:
                                points = self._parse_polygon_points(points_str)
                                if points:
                                    cluster_bounds[cluster_name] = points
                                    print(f"DEBUG: Extracted cluster {cluster_name} polygon bounds: {points}")
                        else:
                            print(f"DEBUG: No path or polygon found for cluster {cluster_name}")
                            cluster_bounds[cluster_name] = points
        
        except ET.ParseError as e:
            print(f"Warning: Could not parse SVG: {e}")
        
        return node_positions, cluster_bounds
    
    def _parse_polygon_points(self, points_str: str) -> List[Tuple[float, float]]:
        """Parse polygon points string into list of coordinate tuples."""
        try:
            coords = []
            # Handle both space-separated and comma-separated formats
            # Graphviz uses format like: "92,-180.92 38,-180.92 38,-144.92 92,-144.92 92,-180.92"
            parts = points_str.strip().split()
            
            for part in parts:
                if ',' in part:
                    # Split on comma for x,y pairs
                    x_str, y_str = part.split(',', 1)
                    x = float(x_str)
                    y = float(y_str)
                    coords.append((x, y))
            
            print(f"DEBUG: Parsed {len(coords)} coordinate pairs from: {points_str[:50]}...")
            return coords
        except (ValueError, IndexError) as e:
            print(f"DEBUG: Failed to parse polygon points: {e}")
            return []
    
    def _parse_path_to_bounds(self, path_data: str) -> List[Tuple[float, float]]:
        """Parse SVG path data to extract boundary points for cluster bounds."""
        try:
            # Simple path parser for Graphviz cluster boundaries
            # Graphviz typically uses M (moveto) and L (lineto) commands for cluster boundaries
            coords = []
            
            # Split path into commands
            import re
            # Find all coordinate pairs in the path
            coord_pattern = r'[-+]?\d*\.?\d+'
            numbers = re.findall(coord_pattern, path_data)
            
            # Group numbers into coordinate pairs
            for i in range(0, len(numbers) - 1, 2):
                try:
                    x = float(numbers[i])
                    y = float(numbers[i + 1])
                    coords.append((x, y))
                except (ValueError, IndexError):
                    continue
            
            return coords
        except Exception:
            return []
    
    def _create_spatial_primitives(self, graph: RelationalGraphWithCuts,
                                 node_positions: Dict[str, Tuple[float, float]],
                                 cluster_bounds: Dict[str, List[Tuple[float, float]]]) -> List[Dict[str, Any]]:
        """Create spatial primitives from Graphviz layout results."""
        primitives = []
        
        # Transform coordinates from SVG space to Tkinter space
        def transform_coordinates(svg_x: float, svg_y: float) -> Tuple[float, float]:
            """Transform SVG coordinates to Tkinter coordinates."""
            # SVG has negative Y values, Tkinter needs positive Y values
            # Center the diagram and flip Y axis
            tkinter_x = svg_x + 400  # Offset to center horizontally
            tkinter_y = -svg_y + 300  # Flip Y axis and offset to center vertically
            return tkinter_x, tkinter_y
        
        # Add cut primitives
        for cut_id, cluster_name in self.cluster_mapping.items():
            if cluster_name in cluster_bounds:
                svg_points = cluster_bounds[cluster_name]
                if svg_points:
                    # Transform all points
                    transformed_points = [transform_coordinates(x, y) for x, y in svg_points]
                    primitives.append({
                        'type': 'cut',
                        'element_id': cut_id,
                        'points': transformed_points,
                        'style': {
                            'stroke': 'blue',
                            'fill': 'none',
                            'stroke-width': 2,
                            'stroke-dasharray': '5,5'
                        }
                    })
        
        # Add vertex primitives
        for element_id, node_name in self.node_mapping.items():
            if element_id in {v.id for v in graph.V} and node_name in node_positions:
                vertex = graph.get_vertex(element_id)
                svg_x, svg_y = node_positions[node_name]
                x, y = transform_coordinates(svg_x, svg_y)
                
                if vertex.label:
                    # Constant vertex
                    primitives.append({
                        'type': 'vertex',
                        'element_id': element_id,
                        'x': x,
                        'y': y,
                        'radius': 15,
                        'label': vertex.label,
                        'style': {
                            'stroke': 'black',
                            'fill': 'lightblue',
                            'stroke-width': 1
                        }
                    })
                else:
                    # Variable vertex (line of identity)
                    primitives.append({
                        'type': 'vertex',
                        'element_id': element_id,
                        'x': x,
                        'y': y,
                        'radius': 8,
                        'label': '•',
                        'style': {
                            'stroke': 'black',
                            'fill': 'black',
                            'stroke-width': 2
                        }
                    })
        
        # Add predicate primitives
        for element_id, node_name in self.node_mapping.items():
            if element_id in {e.id for e in graph.E} and node_name in node_positions:
                relation_name = graph.get_relation_name(element_id)
                svg_x, svg_y = node_positions[node_name]
                x, y = transform_coordinates(svg_x, svg_y)
                
                primitives.append({
                    'type': 'predicate',
                    'element_id': element_id,
                    'x': x,
                    'y': y,
                    'width': len(relation_name) * 8 + 10,
                    'height': 20,
                    'label': relation_name,
                    'style': {
                        'stroke': 'black',
                        'fill': 'lightyellow',
                        'stroke-width': 1
                    }
                })
        
        # Add edge connections (simplified for now)
        for element_id in {e.id for e in graph.E}:
            if element_id in self.node_mapping:
                pred_node = self.node_mapping[element_id]
                if pred_node in node_positions:
                    svg_pred_x, svg_pred_y = node_positions[pred_node]
                    pred_x, pred_y = transform_coordinates(svg_pred_x, svg_pred_y)
                    
                    # Connect to incident vertices
                    incident_vertices = graph.get_incident_vertices(element_id)
                    for vertex_id in incident_vertices:
                        if vertex_id in self.node_mapping:
                            vertex_node = self.node_mapping[vertex_id]
                            if vertex_node in node_positions:
                                svg_vertex_x, svg_vertex_y = node_positions[vertex_node]
                                vertex_x, vertex_y = transform_coordinates(svg_vertex_x, svg_vertex_y)
                                
                                primitives.append({
                                    'type': 'edge',
                                    'from_element': element_id,
                                    'to_element': vertex_id,
                                    'points': [(pred_x, pred_y), (vertex_x, vertex_y)],
                                    'style': {
                                        'stroke': 'black',
                                        'stroke-width': 1,
                                        'stroke-dasharray': '3,3'
                                    }
                                })
        
        return primitives


def test_graphviz_integration():
    """Test the Graphviz integration with a real EGI graph."""
    from egi_core_dau import create_empty_graph, create_vertex, create_edge, create_cut
    
    print("=== Testing Graphviz Layout Integration ===")
    
    # Create test graph: ~[ ~[ (P "x") ] ~[ (Q "x") ] ]
    graph = create_empty_graph()
    
    # Add outer cut
    outer_cut = create_cut()
    graph = graph.with_cut(outer_cut)
    
    # Add first inner cut with P(x)
    inner_cut1 = create_cut()
    graph = graph.with_cut(inner_cut1, outer_cut.id)
    
    x_vertex1 = create_vertex("x", is_generic=False)
    graph = graph.with_vertex_in_context(x_vertex1, inner_cut1.id)
    
    p_edge = create_edge()
    graph = graph.with_edge(p_edge, (x_vertex1.id,), "P", inner_cut1.id)
    
    # Add second inner cut with Q(x)
    inner_cut2 = create_cut()
    graph = graph.with_cut(inner_cut2, outer_cut.id)
    
    x_vertex2 = create_vertex("x", is_generic=False)
    graph = graph.with_vertex_in_context(x_vertex2, inner_cut2.id)
    
    q_edge = create_edge()
    graph = graph.with_edge(q_edge, (x_vertex2.id,), "Q", inner_cut2.id)
    
    # Test layout
    integration = GraphvizLayoutIntegration()
    result = integration.calculate_layout(graph)
    
    print(f"✓ Layout calculated successfully")
    print(f"  - Generated {len(result.primitives)} spatial primitives")
    print(f"  - Found {len(result.node_positions)} node positions")
    print(f"  - Found {len(result.cluster_bounds)} cluster boundaries")
    
    # Show primitive types
    primitive_types = {}
    for primitive in result.primitives:
        ptype = primitive['type']
        primitive_types[ptype] = primitive_types.get(ptype, 0) + 1
    
    print("  - Primitive breakdown:")
    for ptype, count in primitive_types.items():
        print(f"    {ptype}: {count}")
    
    print("\n🎉 Graphviz integration test completed successfully!")
    return result


if __name__ == "__main__":
    test_graphviz_integration()
