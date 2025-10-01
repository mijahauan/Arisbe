"""
EGI Layout Engine - Two-Pass Approach

This engine uses a sophisticated two-pass process:
1. Hierarchical Layout (dot): Position containers and edge labels
2. Force-Directed Layout (neato): Position vertices optimally with fixed anchors  
3. Final Path Routing: A* pathfinding for collision-free ligature paths

Dependencies:
- graphviz (pip install graphviz)
- pathfinding (pip install pathfinding)
"""

import json
import math
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set, Union
from pathlib import Path
from collections import defaultdict

try:
    import graphviz
    from pathfinding.core.diagonal_movement import DiagonalMovement
    from pathfinding.core.grid import Grid
    from pathfinding.finder.a_star import AStarFinder
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install graphviz pathfinding")
    raise

from egi_core_dau import RelationalGraphWithCuts, ElementID


# --- DTO Structure (same as before) ---

@dataclass
class Rect:
    x: float
    y: float
    width: float
    height: float
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if point is within this rectangle"""
        return (self.x <= x <= self.x + self.width and 
                self.y <= y <= self.y + self.height)


@dataclass
class RenderableArea:
    id: str
    parent_id: Optional[str]
    rect: Rect
    is_sheet: bool = False


@dataclass
class RenderableVertex:
    id: str
    parent_area_id: str
    pos: Tuple[float, float]  # (cx, cy)


@dataclass
class RenderableEdgeLabel:
    id: str
    parent_area_id: str
    rect: Rect
    label: str


@dataclass
class RenderableLigature:
    start_vertex_id: str
    end_edge_id: str
    end_hook_index: int
    path_points: List[Tuple[float, float]]


@dataclass
class LayoutDTO:
    areas: List[RenderableArea] = field(default_factory=list)
    vertices: List[RenderableVertex] = field(default_factory=list)
    edge_labels: List[RenderableEdgeLabel] = field(default_factory=list)
    ligatures: List[RenderableLigature] = field(default_factory=list)


@dataclass
class LigatureSubgraph:
    """Represents a connected component of vertices and edges for force-directed layout"""
    vertices: Set[ElementID]
    edges: Set[ElementID]
    connections: List[Tuple[ElementID, ElementID]]  # (vertex_id, edge_id) pairs


class EGI_LayoutEngine:
    """Two-pass layout engine for optimal EGI visualization"""
    
    def __init__(self):
        self.grid_resolution = 2  # Grid cells per unit for pathfinding
        
    def generate_layout(self, egi: RelationalGraphWithCuts) -> LayoutDTO:
        """Main orchestration method for two-pass layout"""
        
        # Pass 1: Hierarchical Layout of Containers and Anchors
        layout_data = self._layout_containers_and_anchors(egi)
        
        # Pass 2: Force-Directed Layout of Ligatures  
        self._layout_ligatures(egi, layout_data)
        
        # Create DTO from layout data
        dto = self._create_dto_from_layout_data(egi, layout_data)
        
        # Pass 3: Final Path Routing
        self._route_final_paths(egi, dto)
        
        return dto
    
    def _layout_containers_and_anchors(self, egi: RelationalGraphWithCuts) -> Dict:
        """Pass 1: Use dot to position containers and edge labels only"""
        
        # Build containment hierarchy
        hierarchy = self._build_containment_hierarchy(egi)
        
        # Generate DOT string (containers and edge labels only, NO vertices)
        dot_string = self._generate_containers_dot(egi, hierarchy)
        
        # Execute dot layout engine
        layout_data = self._execute_graphviz_layout(dot_string, engine='dot')
        
        # Parse and store container/anchor positions
        parsed_data = self._parse_containers_layout(egi, layout_data, hierarchy)
        
        return parsed_data
    
    def _generate_containers_dot(self, egi: RelationalGraphWithCuts, hierarchy: Dict) -> str:
        """Generate DOT string for containers and edge labels only"""
        
        lines = ["digraph EGI {"]
        lines.append("  rankdir=TB;")
        lines.append("  node [fontname=\"Arial\"];")
        lines.append("  edge [style=invis];")  # No visible edges
        
        # Generate clusters and edge labels (NO vertices)
        self._generate_clusters_and_labels(egi, hierarchy, egi.sheet, lines, indent="  ")
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def _generate_clusters_and_labels(self, egi: RelationalGraphWithCuts, hierarchy: Dict, 
                                    container_id: ElementID, lines: List[str], indent: str):
        """Recursively generate clusters and edge labels (excluding vertices)"""
        
        container_info = hierarchy[container_id]
        
        if container_info['is_sheet']:
            # Sheet is the root - no cluster wrapper
            cluster_indent = indent
        else:
            # Create cluster for cut
            cluster_name = f"cluster_{container_id.replace('-', '_')}"
            lines.append(f"{indent}subgraph {cluster_name} {{")
            lines.append(f"{indent}  label=\"\";")
            lines.append(f"{indent}  style=rounded;")
            lines.append(f"{indent}  color=black;")
            cluster_indent = indent + "  "
        
        # Add edge labels (predicates) in this container - NO vertices
        for edge_id in container_info['edges']:
            edge_name = edge_id.replace('-', '_')
            relation_name = egi.rel.get(edge_id, "?")
            lines.append(f"{cluster_indent}{edge_name} [shape=plaintext, label=\"{relation_name}\"];")
        
        # Recursively add child clusters
        for child_id in container_info['children']:
            self._generate_clusters_and_labels(egi, hierarchy, child_id, lines, cluster_indent)
        
        if not container_info['is_sheet']:
            lines.append(f"{indent}}}")
    
    def _layout_ligatures(self, egi: RelationalGraphWithCuts, layout_data: Dict):
        """Pass 2: Use neato for force-directed vertex positioning"""
        
        # Identify ligature subgraphs (connected components)
        ligature_subgraphs = self._identify_ligature_subgraphs(egi)
        
        # Debug: Uncomment for debugging
        # print(f"DEBUG: Found {len(ligature_subgraphs)} ligature subgraphs")
        
        # Layout each ligature subgraph separately
        for subgraph in ligature_subgraphs:
            self._layout_single_ligature_subgraph(egi, subgraph, layout_data)
    
    def _identify_ligature_subgraphs(self, egi: RelationalGraphWithCuts) -> List[LigatureSubgraph]:
        """Find connected components of vertices and edges"""
        
        # Build adjacency graph
        vertex_to_edges = defaultdict(set)
        edge_to_vertices = defaultdict(set)
        
        for edge_id, vertex_sequence in egi.nu.items():
            for vertex_id in vertex_sequence:
                vertex_to_edges[vertex_id].add(edge_id)
                edge_to_vertices[edge_id].add(vertex_id)
        
        # Find connected components using DFS
        visited_vertices = set()
        visited_edges = set()
        subgraphs = []
        
        for vertex_id in egi.V:
            if vertex_id.id not in visited_vertices:
                # Start new component
                component_vertices = set()
                component_edges = set()
                connections = []
                
                # DFS to find all connected elements
                stack = [('vertex', vertex_id.id)]
                
                while stack:
                    element_type, element_id = stack.pop()
                    
                    if element_type == 'vertex':
                        if element_id in visited_vertices:
                            continue
                        visited_vertices.add(element_id)
                        component_vertices.add(element_id)
                        
                        # Add connected edges
                        for edge_id in vertex_to_edges[element_id]:
                            connections.append((element_id, edge_id))
                            if edge_id not in visited_edges:
                                stack.append(('edge', edge_id))
                    
                    elif element_type == 'edge':
                        if element_id in visited_edges:
                            continue
                        visited_edges.add(element_id)
                        component_edges.add(element_id)
                        
                        # Add connected vertices
                        for vertex_id in edge_to_vertices[element_id]:
                            if vertex_id not in visited_vertices:
                                stack.append(('vertex', vertex_id))
                
                if component_vertices:  # Only create subgraph if it has vertices
                    subgraph = LigatureSubgraph(
                        vertices=component_vertices,
                        edges=component_edges,
                        connections=connections
                    )
                    subgraphs.append(subgraph)
        
        return subgraphs
    
    def _layout_single_ligature_subgraph(self, egi: RelationalGraphWithCuts, 
                                       subgraph: LigatureSubgraph, layout_data: Dict):
        """Layout one ligature subgraph using neato with fixed anchors"""
        
        # Create DOT string for this subgraph
        dot_string = self._generate_ligature_dot(egi, subgraph, layout_data)
        
        # Debug: Uncomment for debugging
        # print(f"DEBUG: Generated ligature DOT ({len(dot_string)} chars)")
        
        # Execute neato layout engine
        neato_result = self._execute_graphviz_layout(dot_string, engine='neato')
        
        # Parse vertex positions and validate they're within correct areas
        self._parse_and_validate_vertex_positions(egi, subgraph, neato_result, layout_data)
    
    def _generate_ligature_dot(self, egi: RelationalGraphWithCuts, 
                             subgraph: LigatureSubgraph, layout_data: Dict) -> str:
        """Generate DOT string for ligature subgraph with fixed anchors"""
        
        lines = ["graph LigatureSubgraph {"]
        lines.append("  overlap=false;")
        lines.append("  splines=true;")
        
        # Add fixed anchor nodes (edge labels from Pass 1)
        for edge_id in subgraph.edges:
            if edge_id in layout_data['edge_positions']:
                pos = layout_data['edge_positions'][edge_id]
                edge_name = edge_id.replace('-', '_')
                # Pin the anchor at its position from Pass 1
                lines.append(f"  {edge_name} [pos=\"{pos['x']},{pos['y']}!\", pin=true, shape=plaintext];")
        
        # Add free vertex nodes
        for vertex_id in subgraph.vertices:
            vertex_name = vertex_id.replace('-', '_')
            lines.append(f"  {vertex_name} [shape=point, width=0.1, height=0.1];")
        
        # Add edges (connections)
        for vertex_id, edge_id in subgraph.connections:
            vertex_name = vertex_id.replace('-', '_')
            edge_name = edge_id.replace('-', '_')
            lines.append(f"  {vertex_name} -- {edge_name};")
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def _parse_and_validate_vertex_positions(self, egi: RelationalGraphWithCuts,
                                           subgraph: LigatureSubgraph, 
                                           neato_result: Dict, layout_data: Dict):
        """Parse vertex positions and ensure they're within correct areas"""
        
        for obj in neato_result.get('objects', []):
            name = obj.get('name', '')
            
            if 'pos' not in obj:
                continue
            
            # Check if this is a vertex from our subgraph
            vertex_id = name  # Keep original name with underscores
            
            if vertex_id in subgraph.vertices:
                # Parse position
                pos_str = obj.get('pos', '0,0')
                pos_parts = pos_str.split(',')
                x = float(pos_parts[0])
                y = float(pos_parts[1])
                
                # Find the correct area for this vertex
                parent_area_id = self._find_element_area(egi, vertex_id)
                
                # Validate position is within area bounds
                if parent_area_id in layout_data['area_bounds']:
                    area_rect = layout_data['area_bounds'][parent_area_id]
                    if not area_rect.contains_point(x, y):
                        # Clamp to area bounds
                        x = max(area_rect.x, min(x, area_rect.x + area_rect.width))
                        y = max(area_rect.y, min(y, area_rect.y + area_rect.height))
                
                # Store vertex position
                if 'vertex_positions' not in layout_data:
                    layout_data['vertex_positions'] = {}
                
                layout_data['vertex_positions'][vertex_id] = {
                    'x': x,
                    'y': y,
                    'parent_area_id': parent_area_id
                }
    
    def _route_final_paths(self, egi: RelationalGraphWithCuts, dto: LayoutDTO):
        """Pass 3: Route collision-free ligature paths using A*"""
        
        # Build collision map
        collision_grid, grid_bounds = self._build_collision_map(dto)
        
        # Route each ligature
        for edge_id, vertex_sequence in egi.nu.items():
            if not vertex_sequence:
                continue
            
            # Find edge label
            edge_label = None
            for label in dto.edge_labels:
                if label.id == edge_id:
                    edge_label = label
                    break
            
            if not edge_label:
                continue
            
            # Route to each connected vertex
            for hook_index, vertex_id in enumerate(vertex_sequence):
                # Find vertex
                vertex = None
                for v in dto.vertices:
                    if v.id == vertex_id:
                        vertex = v
                        break
                
                if not vertex:
                    continue
                
                # Calculate collision-free path
                path_points = self._calculate_collision_free_path(
                    vertex, edge_label, collision_grid, grid_bounds
                )
                
                if path_points:
                    ligature = RenderableLigature(
                        start_vertex_id=vertex_id,
                        end_edge_id=edge_id,
                        end_hook_index=hook_index,
                        path_points=path_points
                    )
                    dto.ligatures.append(ligature)
    
    def _build_collision_map(self, dto: LayoutDTO) -> Tuple[Grid, Rect]:
        """Create collision map marking all obstacles"""
        
        # Calculate overall bounds
        all_rects = []
        
        # Add area rectangles (cuts)
        for area in dto.areas:
            if not area.is_sheet:
                all_rects.append(area.rect)
        
        # Add edge label rectangles
        for label in dto.edge_labels:
            all_rects.append(label.rect)
        
        if not all_rects:
            return Grid(100, 100), Rect(0, 0, 100, 100)
        
        # Calculate bounds
        min_x = min(r.x for r in all_rects)
        min_y = min(r.y for r in all_rects)
        max_x = max(r.x + r.width for r in all_rects)
        max_y = max(r.y + r.height for r in all_rects)
        
        # Add padding
        padding = 20
        bounds = Rect(min_x - padding, min_y - padding, 
                     max_x - min_x + 2*padding, max_y - min_y + 2*padding)
        
        # Create grid
        grid_width = int(bounds.width * self.grid_resolution)
        grid_height = int(bounds.height * self.grid_resolution)
        
        # Initialize grid (1 = walkable, 0 = obstacle)
        matrix = [[1 for _ in range(grid_width)] for _ in range(grid_height)]
        
        # Mark obstacles
        for label in dto.edge_labels:
            self._mark_rect_as_obstacle(matrix, label.rect, bounds)
        
        # Mark vertices as small obstacles
        for vertex in dto.vertices:
            vertex_rect = Rect(vertex.pos[0] - 2, vertex.pos[1] - 2, 4, 4)
            self._mark_rect_as_obstacle(matrix, vertex_rect, bounds)
        
        grid = Grid(matrix=matrix)
        return grid, bounds
    
    def _mark_rect_as_obstacle(self, matrix: List[List[int]], rect: Rect, bounds: Rect):
        """Mark rectangle as impassable in collision grid"""
        
        # Convert to grid coordinates
        start_x = int((rect.x - bounds.x) * self.grid_resolution)
        start_y = int((rect.y - bounds.y) * self.grid_resolution)
        end_x = int((rect.x + rect.width - bounds.x) * self.grid_resolution)
        end_y = int((rect.y + rect.height - bounds.y) * self.grid_resolution)
        
        # Clamp to grid bounds
        start_x = max(0, min(start_x, len(matrix[0]) - 1))
        start_y = max(0, min(start_y, len(matrix) - 1))
        end_x = max(0, min(end_x, len(matrix[0]) - 1))
        end_y = max(0, min(end_y, len(matrix) - 1))
        
        # Mark as obstacle
        for y in range(start_y, end_y + 1):
            for x in range(start_x, end_x + 1):
                if 0 <= y < len(matrix) and 0 <= x < len(matrix[0]):
                    matrix[y][x] = 0
    
    def _calculate_collision_free_path(self, vertex: RenderableVertex, 
                                     edge_label: RenderableEdgeLabel,
                                     collision_grid: Grid, grid_bounds: Rect) -> List[Tuple[float, float]]:
        """Calculate A* path avoiding collisions"""
        
        # Convert positions to grid coordinates
        start_x = int((vertex.pos[0] - grid_bounds.x) * self.grid_resolution)
        start_y = int((vertex.pos[1] - grid_bounds.y) * self.grid_resolution)
        
        # Target is center of edge label
        target_x = int((edge_label.rect.x + edge_label.rect.width/2 - grid_bounds.x) * self.grid_resolution)
        target_y = int((edge_label.rect.y + edge_label.rect.height/2 - grid_bounds.y) * self.grid_resolution)
        
        # Clamp to grid bounds
        start_x = max(0, min(start_x, collision_grid.width - 1))
        start_y = max(0, min(start_y, collision_grid.height - 1))
        target_x = max(0, min(target_x, collision_grid.width - 1))
        target_y = max(0, min(target_y, collision_grid.height - 1))
        
        # Find path using A*
        finder = AStarFinder(diagonal_movement=DiagonalMovement.always)
        
        try:
            start_node = collision_grid.node(start_x, start_y)
            end_node = collision_grid.node(target_x, target_y)
            
            path, runs = finder.find_path(start_node, end_node, collision_grid)
            
            if not path:
                # Fallback to straight line
                return [vertex.pos, (edge_label.rect.x + edge_label.rect.width/2, 
                                   edge_label.rect.y + edge_label.rect.height/2)]
            
            # Convert path back to world coordinates and simplify
            world_path = []
            for i in range(0, len(path), max(1, len(path)//8)):  # Simplify path
                node = path[i]
                world_x = node.x / self.grid_resolution + grid_bounds.x
                world_y = node.y / self.grid_resolution + grid_bounds.y
                world_path.append((world_x, world_y))
            
            # Ensure we end at the exact target
            target_world = (edge_label.rect.x + edge_label.rect.width/2, 
                          edge_label.rect.y + edge_label.rect.height/2)
            if world_path[-1] != target_world:
                world_path.append(target_world)
            
            return world_path
            
        except Exception as e:
            # Fallback to straight line
            return [vertex.pos, (edge_label.rect.x + edge_label.rect.width/2, 
                               edge_label.rect.y + edge_label.rect.height/2)]
    
    # Helper methods (same as before with minor adaptations)
    
    def _build_containment_hierarchy(self, egi: RelationalGraphWithCuts) -> Dict:
        """Build hierarchy from EGI area mapping"""
        
        hierarchy = {}
        all_containers = {egi.sheet} | {cut.id for cut in egi.Cut}
        
        # Initialize all containers
        for container_id in all_containers:
            hierarchy[container_id] = {
                'parent': None,
                'children': set(),
                'vertices': set(),
                'edges': set(),
                'is_sheet': container_id == egi.sheet
            }
        
        # Process area mapping
        for container_id, elements in egi.area.items():
            if container_id not in hierarchy:
                continue
                
            for element_id in elements:
                # Check if element is a container (nested cut)
                if element_id in all_containers and element_id != container_id:
                    hierarchy[element_id]['parent'] = container_id
                    hierarchy[container_id]['children'].add(element_id)
                else:
                    # Element is vertex or edge
                    if any(v.id == element_id for v in egi.V):
                        hierarchy[container_id]['vertices'].add(element_id)
                    elif any(e.id == element_id for e in egi.E):
                        hierarchy[container_id]['edges'].add(element_id)
        
        return hierarchy
    
    def _execute_graphviz_layout(self, dot_string: str, engine: str = 'dot') -> Dict:
        """Execute Graphviz layout engine and return JSON"""
        
        try:
            # Create temporary DOT file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as f:
                f.write(dot_string)
                dot_file = f.name
            
            # Run Graphviz command
            result = subprocess.run([
                engine, '-Tjson', dot_file
            ], capture_output=True, text=True, check=True)
            
            # Clean up temp file
            Path(dot_file).unlink()
            
            # Parse JSON output
            layout_data = json.loads(result.stdout)
            return layout_data
            
        except subprocess.CalledProcessError as e:
            print(f"Graphviz {engine} error: {e}")
            print(f"DOT content:\n{dot_string}")
            raise
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Graphviz output:\n{result.stdout}")
            raise
    
    def _parse_containers_layout(self, egi: RelationalGraphWithCuts, 
                                layout_data: Dict, hierarchy: Dict) -> Dict:
        """Parse container and edge label positions from Pass 1"""
        
        parsed_data = {
            'area_bounds': {},
            'edge_positions': {},
            'hierarchy': hierarchy
        }
        
        # Parse overall bounding box for sheet
        bb = layout_data.get('bb', '0,0,100,100').split(',')
        total_width = float(bb[2]) - float(bb[0])
        total_height = float(bb[3]) - float(bb[1])
        
        parsed_data['area_bounds'][egi.sheet] = Rect(0, 0, total_width, total_height)
        
        # Process objects
        for obj in layout_data.get('objects', []):
            if 'nodes' in obj:
                # This is a subgraph (cut)
                self._parse_cut_bounds(obj, parsed_data)
            else:
                # This is a node (edge label)
                self._parse_edge_position(egi, obj, parsed_data)
        
        return parsed_data
    
    def _parse_cut_bounds(self, subgraph: Dict, parsed_data: Dict):
        """Parse cut boundary from subgraph"""
        
        name = subgraph.get('name', '')
        if not name.startswith('cluster_'):
            return
        
        cut_id = name.replace('cluster_', '')
        
        # Parse bounding box
        bb = subgraph.get('bb', '0,0,100,100').split(',')
        x = float(bb[0])
        y = float(bb[1])
        width = float(bb[2]) - x
        height = float(bb[3]) - y
        
        parsed_data['area_bounds'][cut_id] = Rect(x, y, width, height)
    
    def _parse_edge_position(self, egi: RelationalGraphWithCuts, node: Dict, parsed_data: Dict):
        """Parse edge label position"""
        
        name = node.get('name', '')
        pos_str = node.get('pos', '0,0')
        
        # Parse position
        pos_parts = pos_str.split(',')
        x = float(pos_parts[0])
        y = float(pos_parts[1])
        
        # Store edge position
        parsed_data['edge_positions'][name] = {
            'x': x,
            'y': y,
            'parent_area_id': self._find_element_area(egi, name)
        }
    
    def _find_element_area(self, egi: RelationalGraphWithCuts, element_id: ElementID) -> str:
        """Find which area directly contains an element"""
        
        for container_id, elements in egi.area.items():
            if element_id in elements:
                return container_id
        
        return egi.sheet  # Default to sheet
    
    def _create_dto_from_layout_data(self, egi: RelationalGraphWithCuts, layout_data: Dict) -> LayoutDTO:
        """Create final DTO from all layout data"""
        
        dto = LayoutDTO()
        
        # Create areas
        for area_id, rect in layout_data['area_bounds'].items():
            parent_id = None
            if area_id != egi.sheet:
                # Find parent from hierarchy
                for container_id, container_info in layout_data['hierarchy'].items():
                    if area_id in container_info['children']:
                        parent_id = container_id
                        break
            
            area = RenderableArea(
                id=area_id,
                parent_id=parent_id,
                rect=rect,
                is_sheet=(area_id == egi.sheet)
            )
            dto.areas.append(area)
        
        # Create vertices
        for vertex_id, pos_data in layout_data.get('vertex_positions', {}).items():
            vertex = RenderableVertex(
                id=vertex_id,
                parent_area_id=pos_data['parent_area_id'],
                pos=(pos_data['x'], pos_data['y'])
            )
            dto.vertices.append(vertex)
        
        # Create edge labels
        for edge_id, pos_data in layout_data['edge_positions'].items():
            relation_name = egi.rel.get(edge_id, "?")
            
            # Estimate text dimensions
            char_width = 8
            char_height = 12
            text_width = len(relation_name) * char_width
            text_height = char_height
            
            edge_label = RenderableEdgeLabel(
                id=edge_id,
                parent_area_id=pos_data['parent_area_id'],
                rect=Rect(pos_data['x'] - text_width/2, pos_data['y'] - text_height/2, 
                         text_width, text_height),
                label=relation_name
            )
            dto.edge_labels.append(edge_label)
        
        return dto
