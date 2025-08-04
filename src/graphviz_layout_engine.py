#!/usr/bin/env python3
"""
Graphviz-based Layout Engine for Existential Graphs

This module provides a layout engine that uses Graphviz's DOT algorithm
to handle hierarchical, non-overlapping containment for EG cuts.

Key features:
- Converts EGI graphs to DOT format
- Uses Graphviz subgraphs/clusters for cuts
- Extracts coordinate information from SVG output
- Returns spatial primitives for rendering
"""

import graphviz
import xml.etree.ElementTree as ET
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from egi_core_dau import RelationalGraphWithCuts


@dataclass
class GraphvizLayoutResult:
    """Result of Graphviz layout calculation."""
    primitives: List[Dict]  # Spatial primitives for rendering
    svg_source: str  # Raw SVG output from Graphviz
    dot_source: str  # DOT source code


class GraphvizLayoutEngine:
    """Layout engine using Graphviz for hierarchical cut containment."""
    
    def __init__(self):
        self.node_counter = 0
        self.cluster_counter = 0
    
    def calculate_layout(self, graph: RelationalGraphWithCuts) -> GraphvizLayoutResult:
        """
        Calculate layout for an EGI graph using Graphviz.
        
        Args:
            graph: The EGI graph to layout
            
        Returns:
            GraphvizLayoutResult with spatial primitives
        """
        # Reset counters
        self.node_counter = 0
        self.cluster_counter = 0
        
        # Convert EGI to DOT
        dot = self._convert_egi_to_dot(graph)
        
        # Generate SVG layout
        svg_source = dot.pipe(format='svg', encoding='utf-8')
        
        # Extract coordinates from SVG
        primitives = self._extract_coordinates_from_svg(svg_source, graph)
        
        return GraphvizLayoutResult(
            primitives=primitives,
            svg_source=svg_source,
            dot_source=dot.source
        )
    
    def _convert_egi_to_dot(self, graph: RelationalGraphWithCuts) -> graphviz.Digraph:
        """Convert EGI graph to Graphviz DOT format."""
        dot = graphviz.Digraph(comment='EG Layout')
        dot.attr(rankdir='TB', splines='true', overlap='false')
        
        # Process the sheet (root area)
        self._process_area(dot, graph, graph.sheet, None)
        
        return dot
    
    def _process_area(self, dot: graphviz.Digraph, graph: RelationalGraphWithCuts, 
                     area_id: str, parent_subgraph: Optional[graphviz.Digraph]) -> graphviz.Digraph:
        """Process an area (cut or sheet) recursively."""
        
        if area_id == graph.sheet:
            # Sheet level - no subgraph wrapper
            current_graph = dot
        else:
            # Cut - create a cluster subgraph
            cluster_name = f'cluster_{self.cluster_counter}'
            self.cluster_counter += 1
            
            # Create subgraph with proper context
            with dot.subgraph(name=cluster_name) as current_graph:
                # Style the cut
                current_graph.attr(
                    style='rounded,dashed',
                    color='blue',
                    label='',  # No label for cuts
                    margin='20'  # Padding inside cut
                )
                
                # Process contents within this context
                self._process_area_contents(current_graph, graph, area_id)
                
                # Recursively process child cuts
                for child_area_id in graph.area.get(area_id, frozenset()):
                    if child_area_id != area_id and child_area_id in {c.id for c in graph.Cut}:
                        # This is a child cut
                        self._process_area(dot, graph, child_area_id, current_graph)
            
            return dot  # Return early for cuts
        
        # Add vertices in this area
        for vertex_id in graph.area.get(area_id, frozenset()):
            if vertex_id in {v.id for v in graph.V}:
                vertex = graph.get_vertex(vertex_id)
                node_name = f'v_{self.node_counter}'
                self.node_counter += 1
                
                # Style based on vertex type
                if hasattr(vertex, 'label') and vertex.label:
                    # Constant vertex
                    current_graph.node(node_name, 
                                     label=vertex.label,
                                     shape='circle',
                                     style='filled',
                                     fillcolor='lightblue')
                else:
                    # Variable vertex  
                    current_graph.node(node_name,
                                     label='•',  # Dot for line of identity
                                     shape='circle',
                                     style='filled',
                                     fillcolor='black',
                                     fontcolor='white',
                                     width='0.2',
                                     height='0.2')
        
        # Add edges (predicates) in this area
        for edge_id in graph.area.get(area_id, frozenset()):
            if edge_id in {e.id for e in graph.E}:
                edge = graph.get_edge(edge_id)
                pred_name = f'p_{self.node_counter}'
                self.node_counter += 1
                
                # Create predicate node
                relation_name = graph.get_relation_name(edge_id)
                current_graph.node(pred_name,
                                 label=relation_name,
                                 shape='box',
                                 style='filled',
                                 fillcolor='lightyellow')
                
                # Connect to argument vertices
                incident_vertices = graph.get_incident_vertices(edge_id)
                for i, arg_vertex_id in enumerate(incident_vertices):
                    if arg_vertex_id in {v.id for v in graph.V}:
                        # Find the node name for this vertex
                        # (This is simplified - in practice we'd need to track vertex->node mapping)
                        arg_node = f'v_arg_{arg_vertex_id}'
                        current_graph.edge(pred_name, arg_node, 
                                         label=str(i+1),  # Argument position
                                         style='dashed')
        
        # Recursively process child cuts
        for child_area_id in graph.area.get(area_id, frozenset()):
            if child_area_id != area_id and child_area_id in {c.id for c in graph.Cut}:
                # This is a child cut
                self._process_area(dot, graph, child_area_id, current_graph)
        
        return current_graph
    
    def _extract_coordinates_from_svg(self, svg_source: str, graph: RelationalGraphWithCuts) -> List[Dict]:
        """Extract coordinate information from Graphviz SVG output."""
        primitives = []
        
        try:
            # Parse SVG
            root = ET.fromstring(svg_source)
            
            # Extract clusters (cuts)
            for cluster in root.findall('.//{http://www.w3.org/2000/svg}g[@class="cluster"]'):
                # Extract cluster boundary
                polygon = cluster.find('.//{http://www.w3.org/2000/svg}polygon')
                if polygon is not None:
                    points_str = polygon.get('points', '')
                    if points_str:
                        # Parse polygon points
                        points = self._parse_polygon_points(points_str)
                        if points:
                            primitives.append({
                                'type': 'cut',
                                'points': points,
                                'style': {'stroke': 'blue', 'fill': 'none', 'stroke-width': 2}
                            })
            
            # Extract nodes (vertices and predicates)
            for node in root.findall('.//{http://www.w3.org/2000/svg}g[@class="node"]'):
                # Extract node position
                ellipse = node.find('.//{http://www.w3.org/2000/svg}ellipse')
                rect = node.find('.//{http://www.w3.org/2000/svg}polygon')
                text = node.find('.//{http://www.w3.org/2000/svg}text')
                
                if ellipse is not None:
                    # Circular node (vertex)
                    cx = float(ellipse.get('cx', 0))
                    cy = float(ellipse.get('cy', 0))
                    rx = float(ellipse.get('rx', 5))
                    ry = float(ellipse.get('ry', 5))
                    
                    label = text.text if text is not None else ''
                    
                    primitives.append({
                        'type': 'vertex',
                        'x': cx,
                        'y': cy,
                        'radius': max(rx, ry),
                        'label': label,
                        'style': {'stroke': 'black', 'fill': 'lightblue'}
                    })
                
                elif rect is not None:
                    # Rectangular node (predicate)
                    points_str = rect.get('points', '')
                    if points_str:
                        points = self._parse_polygon_points(points_str)
                        if points and len(points) >= 4:
                            # Calculate center and dimensions
                            xs = [p[0] for p in points]
                            ys = [p[1] for p in points]
                            x = sum(xs) / len(xs)
                            y = sum(ys) / len(ys)
                            width = max(xs) - min(xs)
                            height = max(ys) - min(ys)
                            
                            label = text.text if text is not None else ''
                            
                            primitives.append({
                                'type': 'predicate',
                                'x': x,
                                'y': y,
                                'width': width,
                                'height': height,
                                'label': label,
                                'style': {'stroke': 'black', 'fill': 'lightyellow'}
                            })
            
            # Extract edges (lines of identity)
            for edge in root.findall('.//{http://www.w3.org/2000/svg}g[@class="edge"]'):
                path = edge.find('.//{http://www.w3.org/2000/svg}path')
                if path is not None:
                    d = path.get('d', '')
                    if d:
                        # Parse path data (simplified)
                        points = self._parse_path_data(d)
                        if len(points) >= 2:
                            primitives.append({
                                'type': 'edge',
                                'points': points,
                                'style': {'stroke': 'black', 'stroke-width': 2}
                            })
        
        except ET.ParseError as e:
            print(f"Warning: Could not parse SVG: {e}")
            # Return empty primitives - fallback to basic layout
        
        return primitives
    
    def _parse_polygon_points(self, points_str: str) -> List[Tuple[float, float]]:
        """Parse polygon points string into coordinate pairs."""
        points = []
        coords = points_str.strip().split()
        
        for i in range(0, len(coords), 2):
            if i + 1 < len(coords):
                try:
                    x = float(coords[i])
                    y = float(coords[i + 1])
                    points.append((x, y))
                except ValueError:
                    continue
        
        return points
    
    def _parse_path_data(self, path_data: str) -> List[Tuple[float, float]]:
        """Parse SVG path data into coordinate points (simplified)."""
        points = []
        
        # Extract coordinate pairs using regex
        coord_pattern = r'([+-]?\d*\.?\d+),([+-]?\d*\.?\d+)'
        matches = re.findall(coord_pattern, path_data)
        
        for match in matches:
            try:
                x = float(match[0])
                y = float(match[1])
                points.append((x, y))
            except ValueError:
                continue
        
        return points


def test_graphviz_layout():
    """Test the Graphviz layout engine with a simple EG."""
    from egi_core_dau import RelationalGraphWithCuts, create_empty_graph, create_vertex, create_edge, create_cut
    
    # Create a simple test graph: ~[ ~[ (P "x") ] ~[ (Q "x") ] ]
    graph = create_empty_graph()
    
    # Add outer cut
    outer_cut_obj = create_cut()
    graph = graph.with_cut(outer_cut_obj)
    
    # Add first inner cut with P(x)
    inner_cut1_obj = create_cut()
    graph = graph.with_cut(inner_cut1_obj, outer_cut_obj.id)
    
    # Add vertex x to first inner cut
    x_vertex1 = create_vertex("x", is_generic=False)
    graph = graph.with_vertex_in_context(x_vertex1, inner_cut1_obj.id)
    
    # Add predicate P to first inner cut
    p_edge = create_edge()
    graph = graph.with_edge(p_edge, (x_vertex1.id,), "P", inner_cut1_obj.id)
    
    # Add second inner cut with Q(x)
    inner_cut2_obj = create_cut()
    graph = graph.with_cut(inner_cut2_obj, outer_cut_obj.id)
    
    # Add vertex x to second inner cut (shared with first)
    x_vertex2 = create_vertex("x", is_generic=False)
    graph = graph.with_vertex_in_context(x_vertex2, inner_cut2_obj.id)
    
    # Add predicate Q to second inner cut
    q_edge = create_edge()
    graph = graph.with_edge(q_edge, (x_vertex2.id,), "Q", inner_cut2_obj.id)
    
    # Test layout
    engine = GraphvizLayoutEngine()
    result = engine.calculate_layout(graph)
    
    print("DOT Source:")
    print(result.dot_source)
    print(f"\nExtracted {len(result.primitives)} primitives:")
    for primitive in result.primitives:
        print(f"  {primitive['type']}: {primitive}")
    
    return result


if __name__ == "__main__":
    test_graphviz_layout()
