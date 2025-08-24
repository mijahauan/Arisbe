"""
NetworkX + Graphviz-based spatial layout system for EGI.
Provides hierarchical containment and optimized ligature routing.
"""

import networkx as nx
from networkx.drawing import nx_agraph
import math
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass

from egi_spatial_correspondence import SpatialElement, SpatialBounds, LigatureGeometry


@dataclass
class GraphvizLayoutResult:
    """Result from Graphviz layout with extracted coordinates and bounds."""
    node_positions: Dict[str, Tuple[float, float]]
    cluster_bounds: Dict[str, SpatialBounds]
    edge_paths: Dict[str, List[Tuple[float, float]]]


class NetworkXEGILayoutEngine:
    """
    EGI spatial layout engine using NetworkX + Graphviz backend.
    Converts EGI to NetworkX graph with hierarchical clusters, 
    uses Graphviz for layout, then extracts coordinates back.
    """
    
    def __init__(self):
        self.graph = None
        self.layout_result = None
    
    def generate_layout(self, egi, area_bounds: Dict[str, SpatialBounds]) -> Dict[str, SpatialElement]:
        """
        Generate spatial layout using NetworkX + Graphviz.
        
        Args:
            egi: EGI system with vertices, edges, cuts, areas
            area_bounds: Initial area bounds (can be overridden by Graphviz)
            
        Returns:
            Dict mapping element IDs to SpatialElement objects
        """
        # Step 1: Convert EGI to NetworkX graph with clusters
        self.graph = self._create_networkx_graph(egi)
        
        # Step 2: Use Graphviz for layout with hierarchical clusters
        self.layout_result = self._compute_graphviz_layout(self.graph)
        
        # Step 3: Convert back to SpatialElement format
        spatial_layout = self._extract_spatial_elements(egi, self.layout_result)
        
        # Step 4: Generate ligatures using optimized paths
        spatial_layout = self._add_networkx_ligatures(egi, spatial_layout)
        
        return spatial_layout
    
    def _create_networkx_graph(self, egi) -> nx.DiGraph:
        """Convert EGI to NetworkX graph with subgraph clusters for areas."""
        G = nx.DiGraph()
        
        # Add vertices as nodes
        for vertex in egi.V:
            G.add_node(vertex.id, 
                      node_type='vertex', 
                      label=getattr(vertex, 'name', vertex.id),
                      area=self._find_element_area(vertex.id, egi))
        
        # Add edges as nodes (predicates)
        for edge in egi.E:
            G.add_node(edge.id, 
                      node_type='edge', 
                      label=getattr(edge, 'relation', edge.id),
                      area=self._find_element_area(edge.id, egi))
        
        # Add ligature edges (vertex -> connected edges)
        for edge in egi.E:
            connected_vertices = egi.nu.get(edge.id, ())
            for vertex_id in connected_vertices:
                # Add edge from vertex to predicate (ligature)
                G.add_edge(vertex_id, edge.id, edge_type='ligature')
        
        # Add cluster information for hierarchical layout
        self._add_cluster_attributes(G, egi)
        
        return G
    
    def _add_cluster_attributes(self, G: nx.DiGraph, egi):
        """Add cluster/subgraph attributes for Graphviz hierarchical layout."""
        # Group nodes by their logical areas
        area_to_nodes = {}
        for node_id in G.nodes():
            area = G.nodes[node_id]['area']
            if area not in area_to_nodes:
                area_to_nodes[area] = []
            area_to_nodes[area].append(node_id)
        
        # Set cluster attributes for each area
        for area_id, node_list in area_to_nodes.items():
            for node_id in node_list:
                G.nodes[node_id]['cluster'] = f'cluster_{area_id}'
    
    def _compute_graphviz_layout(self, G: nx.DiGraph) -> GraphvizLayoutResult:
        """Use Graphviz to compute hierarchical layout with clusters."""
        try:
            # Use NetworkX's Graphviz interface for layout with proper area separation
            pos = nx_agraph.graphviz_layout(G, prog='dot')
            
            # Scale and separate positions to avoid overlaps
            pos = self._scale_and_separate_positions(pos, G)
            
            # Extract cluster bounds with proper containment
            cluster_bounds = self._compute_proper_cluster_bounds(G, pos)
            
            # Generate edge paths
            edge_paths = self._generate_edge_paths(G, pos)
            
            return GraphvizLayoutResult(
                node_positions=pos,
                cluster_bounds=cluster_bounds,
                edge_paths=edge_paths
            )
            
        except Exception as e:
            print(f"Graphviz layout failed: {e}, using manual layout")
            # Fallback to manual area-aware layout
            pos = self._create_manual_area_layout(G)
            cluster_bounds = self._compute_proper_cluster_bounds(G, pos)
            edge_paths = self._generate_edge_paths(G, pos)
            
            return GraphvizLayoutResult(
                node_positions=pos,
                cluster_bounds=cluster_bounds,
                edge_paths=edge_paths
            )
    
    def _generate_dot_with_clusters(self, G: nx.DiGraph) -> str:
        """Generate DOT format string with cluster subgraphs."""
        dot_lines = ["digraph EGI {"]
        dot_lines.append("  rankdir=TB;")
        dot_lines.append("  compound=true;")
        
        # Group nodes by clusters
        clusters = {}
        for node_id, node_data in G.nodes(data=True):
            cluster = node_data.get('cluster', 'cluster_sheet')
            if cluster not in clusters:
                clusters[cluster] = []
            clusters[cluster].append((node_id, node_data))
        
        # Generate cluster subgraphs
        for cluster_id, nodes in clusters.items():
            dot_lines.append(f"  subgraph {cluster_id} {{")
            dot_lines.append(f"    label=\"{cluster_id.replace('cluster_', '')}\";")
            dot_lines.append("    style=dashed;")
            
            for node_id, node_data in nodes:
                label = node_data.get('label', node_id)
                node_type = node_data.get('node_type', 'unknown')
                shape = 'ellipse' if node_type == 'vertex' else 'box'
                dot_lines.append(f"    {node_id} [label=\"{label}\", shape={shape}];")
            
            dot_lines.append("  }")
        
        # Add edges
        for source, target, edge_data in G.edges(data=True):
            dot_lines.append(f"  {source} -> {target};")
        
        dot_lines.append("}")
        return "\n".join(dot_lines)
    
    def _estimate_cluster_bounds(self, G: nx.DiGraph, pos: Dict[str, Tuple[float, float]]) -> Dict[str, SpatialBounds]:
        """Estimate cluster bounds from node positions."""
        cluster_bounds = {}
        
        # Group positions by cluster
        cluster_positions = {}
        for node_id, node_data in G.nodes(data=True):
            cluster = node_data.get('cluster', 'cluster_sheet')
            if cluster not in cluster_positions:
                cluster_positions[cluster] = []
            if node_id in pos:
                cluster_positions[cluster].append(pos[node_id])
        
        # Calculate bounding boxes for each cluster
        for cluster_id, positions in cluster_positions.items():
            if positions:
                xs = [p[0] for p in positions]
                ys = [p[1] for p in positions]
                
                min_x, max_x = min(xs) - 50, max(xs) + 50
                min_y, max_y = min(ys) - 30, max(ys) + 30
                
                cluster_bounds[cluster_id] = SpatialBounds(
                    x=min_x, y=min_y,
                    width=max_x - min_x,
                    height=max_y - min_y
                )
        
        return cluster_bounds
    
    def _generate_edge_paths(self, G: nx.DiGraph, pos: Dict[str, Tuple[float, float]]) -> Dict[str, List[Tuple[float, float]]]:
        """Generate edge paths for ligatures."""
        edge_paths = {}
        
        for source, target, edge_data in G.edges(data=True):
            if source in pos and target in pos:
                edge_id = f"{source}_{target}"
                edge_paths[edge_id] = [pos[source], pos[target]]
        
        return edge_paths
    
    def _scale_and_separate_positions(self, pos: Dict[str, Tuple[float, float]], G: nx.DiGraph) -> Dict[str, Tuple[float, float]]:
        """Scale positions and separate by logical areas to avoid overlaps."""
        scaled_pos = {}
        
        # Group positions by cluster/area
        area_positions = {}
        for node_id, (x, y) in pos.items():
            cluster = G.nodes[node_id].get('cluster', 'cluster_sheet')
            if cluster not in area_positions:
                area_positions[cluster] = []
            area_positions[cluster].append((node_id, x, y))
        
        # Separate areas spatially
        area_offset = 0
        for cluster, positions in area_positions.items():
            if 'cut' in cluster:
                # Position cuts in separate area with offset
                for node_id, x, y in positions:
                    scaled_pos[node_id] = (x + 300, y + 150)  # Offset cut elements
            else:
                # Sheet elements in main area
                for node_id, x, y in positions:
                    scaled_pos[node_id] = (x + 100, y + 100)  # Base offset
        
        return scaled_pos
    
    def _create_manual_area_layout(self, G: nx.DiGraph) -> Dict[str, Tuple[float, float]]:
        """Create manual layout respecting logical areas."""
        pos = {}
        
        # Separate elements by area
        sheet_elements = []
        cut_elements = []
        
        for node_id, node_data in G.nodes(data=True):
            cluster = node_data.get('cluster', 'cluster_sheet')
            if 'cut' in cluster:
                cut_elements.append(node_id)
            else:
                sheet_elements.append(node_id)
        
        # Position sheet elements
        for i, node_id in enumerate(sheet_elements):
            angle = (2 * math.pi * i) / max(len(sheet_elements), 1)
            radius = 80
            x = 200 + radius * math.cos(angle)
            y = 200 + radius * math.sin(angle)
            pos[node_id] = (x, y)
        
        # Position cut elements inside cut area
        for i, node_id in enumerate(cut_elements):
            x = 350 + i * 60
            y = 180
            pos[node_id] = (x, y)
        
        return pos
    
    def _compute_proper_cluster_bounds(self, G: nx.DiGraph, pos: Dict[str, Tuple[float, float]]) -> Dict[str, SpatialBounds]:
        """Compute cluster bounds ensuring proper containment."""
        cluster_bounds = {}
        
        # Group positions by cluster
        cluster_positions = {}
        for node_id, node_data in G.nodes(data=True):
            cluster = node_data.get('cluster', 'cluster_sheet')
            if cluster not in cluster_positions:
                cluster_positions[cluster] = []
            if node_id in pos:
                cluster_positions[cluster].append(pos[node_id])
        
        # Calculate bounds for each cluster
        for cluster_id, positions in cluster_positions.items():
            if positions:
                xs = [p[0] for p in positions]
                ys = [p[1] for p in positions]
                
                # Add padding around elements
                padding = 60 if 'cut' in cluster_id else 80
                min_x, max_x = min(xs) - padding, max(xs) + padding
                min_y, max_y = min(ys) - padding, max(ys) + padding
                
                cluster_bounds[cluster_id] = SpatialBounds(
                    x=min_x, y=min_y,
                    width=max_x - min_x,
                    height=max_y - min_y
                )
        
        return cluster_bounds
    
    def _extract_spatial_elements(self, egi, layout_result: GraphvizLayoutResult) -> Dict[str, SpatialElement]:
        """Convert Graphviz layout back to SpatialElement format."""
        spatial_layout = {}
        
        # Convert vertices
        for vertex in egi.V:
            if vertex.id in layout_result.node_positions:
                x, y = layout_result.node_positions[vertex.id]
                spatial_layout[vertex.id] = SpatialElement(
                    element_id=vertex.id,
                    element_type='vertex',
                    logical_area=self._find_element_area(vertex.id, egi),
                    spatial_bounds=SpatialBounds(x=x-15, y=y-10, width=30, height=20),
                    ligature_geometry=None
                )
        
        # Convert edges (predicates)
        for edge in egi.E:
            if edge.id in layout_result.node_positions:
                x, y = layout_result.node_positions[edge.id]
                spatial_layout[edge.id] = SpatialElement(
                    element_id=edge.id,
                    element_type='edge',
                    logical_area=self._find_element_area(edge.id, egi),
                    spatial_bounds=SpatialBounds(x=x-25, y=y-12, width=50, height=24),
                    ligature_geometry=None
                )
        
        # Convert cuts (from cluster bounds)
        for cut in egi.Cut:
            cluster_id = f'cluster_{cut.id}'
            if cluster_id in layout_result.cluster_bounds:
                bounds = layout_result.cluster_bounds[cluster_id]
                spatial_layout[cut.id] = SpatialElement(
                    element_id=cut.id,
                    element_type='cut',
                    logical_area=self._find_cut_parent_area(cut.id, egi),
                    spatial_bounds=bounds,
                    ligature_geometry=None
                )
        
        return spatial_layout
    
    def _add_networkx_ligatures(self, egi, layout: Dict[str, SpatialElement]) -> Dict[str, SpatialElement]:
        """Add ligatures using NetworkX edge paths."""
        if not self.layout_result:
            return layout
        
        # Group vertices by their connected edges
        vertex_to_edges = {}
        for edge in egi.E:
            connected_vertices = egi.nu.get(edge.id, ())
            for vertex_id in connected_vertices:
                if vertex_id not in vertex_to_edges:
                    vertex_to_edges[vertex_id] = []
                vertex_to_edges[vertex_id].append(edge.id)
        
        # Create ligatures for vertices with multiple connections
        ligature_counter = 1
        for vertex_id, connected_edges in vertex_to_edges.items():
            if len(connected_edges) > 1 and vertex_id in layout:
                ligature_id = f"ligature_{ligature_counter}"
                
                # Get vertex position
                vertex_element = layout[vertex_id]
                vertex_center = (
                    vertex_element.spatial_bounds.x + vertex_element.spatial_bounds.width / 2,
                    vertex_element.spatial_bounds.y + vertex_element.spatial_bounds.height / 2
                )
                
                # Build path using NetworkX edge paths
                path_points = [vertex_center]
                for edge_id in connected_edges:
                    if edge_id in layout:
                        edge_element = layout[edge_id]
                        edge_center = (
                            edge_element.spatial_bounds.x + edge_element.spatial_bounds.width / 2,
                            edge_element.spatial_bounds.y + edge_element.spatial_bounds.height / 2
                        )
                        path_points.append(edge_center)
                
                # Create ligature geometry
                ligature_geometry = LigatureGeometry(
                    ligature_id=ligature_id,
                    vertices=[vertex_id],
                    spatial_path=path_points,
                    branching_points=[]
                )
                
                # Add ligature to layout
                layout[ligature_id] = SpatialElement(
                    element_id=ligature_id,
                    element_type='ligature',
                    logical_area=vertex_element.logical_area,
                    spatial_bounds=SpatialBounds(0, 0, 0, 0),
                    ligature_geometry=ligature_geometry
                )
                
                ligature_counter += 1
        
        return layout
    
    def _find_element_area(self, element_id: str, egi) -> str:
        """Find which area contains an element."""
        for area_id, elements in egi.area.items():
            if element_id in elements:
                return area_id
        return egi.sheet
    
    def _find_cut_parent_area(self, cut_id: str, egi) -> str:
        """Find the parent area containing a cut."""
        for area_id, elements in egi.area.items():
            if cut_id in elements:
                return area_id
        return egi.sheet
