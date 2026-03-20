"""
Graphviz-based Layout Engine for EGI Visualization

This engine uses a three-stage pipeline:
1. Hierarchical Layout: Graphviz for positioning nodes and clusters
2. Ligature Routing: A* pathfinding for connection paths
3. DTO Assembly: Package into renderable primitives

Dependencies:
- graphviz (pip install graphviz)
- pathfinding (pip install pathfinding)
"""

import json
import math
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from pathlib import Path

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


# --- Required Output DTO Structure ---

@dataclass
class Rect:
    x: float
    y: float
    width: float
    height: float


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


class GraphvizLayoutEngine:
    """Three-stage layout engine using Graphviz + A* pathfinding"""
    
    def __init__(self):
        self.grid_resolution = 2  # Grid cells per unit
        self.cut_crossing_penalty = 1000  # Heavy penalty for crossing cuts
        
    def generate_layout(self, egi: RelationalGraphWithCuts) -> LayoutDTO:
        """Main public method - orchestrates the entire pipeline"""
        
        # Stage 1: Generate Graphviz DOT description
        dot_string = self._generate_dot(egi)
        
        # Stage 2: Compute layout using Graphviz
        layout_data = self._compute_initial_layout(dot_string)
        
        # Create initial DTO from layout data
        dto = self._create_dto_from_layout(egi, layout_data)
        
        # Stage 3: Route ligatures using A* pathfinding
        self._route_ligatures(egi, dto)
        
        return dto
    
    def _generate_dot(self, egi: RelationalGraphWithCuts) -> str:
        """Stage 1: Generate Graphviz DOT description with hierarchical clusters"""
        
        # Build containment hierarchy
        hierarchy = self._build_containment_hierarchy(egi)
        
        lines = ["digraph EGI {"]
        lines.append("  rankdir=TB;")
        lines.append("  node [fontname=\"Arial\"];")
        lines.append("  edge [style=invis];")  # No visible edges - we'll route ligatures separately
        
        # Generate clusters for cuts (recursive)
        self._generate_clusters(egi, hierarchy, egi.sheet, lines, indent="  ")
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def _build_containment_hierarchy(self, egi: RelationalGraphWithCuts) -> Dict[ElementID, Dict]:
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
    
    def _generate_clusters(self, egi: RelationalGraphWithCuts, hierarchy: Dict, 
                          container_id: ElementID, lines: List[str], indent: str):
        """Recursively generate Graphviz clusters"""
        
        container_info = hierarchy[container_id]
        
        if container_info['is_sheet']:
            # Sheet is the root - no cluster wrapper needed
            cluster_indent = indent
        else:
            # Create cluster for cut
            cluster_name = f"cluster_{container_id.replace('-', '_')}"
            lines.append(f"{indent}subgraph {cluster_name} {{")
            lines.append(f"{indent}  label=\"\";")
            lines.append(f"{indent}  style=rounded;")
            lines.append(f"{indent}  color=black;")
            cluster_indent = indent + "  "
        
        # Add vertices in this container
        for vertex_id in container_info['vertices']:
            vertex_name = vertex_id.replace('-', '_')
            lines.append(f"{cluster_indent}{vertex_name} [shape=point, width=0.1, height=0.1];")
        
        # Add edges (as label nodes) in this container
        for edge_id in container_info['edges']:
            edge_name = edge_id.replace('-', '_')
            relation_name = egi.rel.get(edge_id, "?")
            lines.append(f"{cluster_indent}{edge_name} [shape=plaintext, label=\"{relation_name}\"];")
        
        # Recursively add child clusters
        for child_id in container_info['children']:
            self._generate_clusters(egi, hierarchy, child_id, lines, cluster_indent)
        
        if not container_info['is_sheet']:
            lines.append(f"{indent}}}")
    
    def _compute_initial_layout(self, dot_string: str) -> Dict:
        """Stage 2: Use Graphviz to compute layout and parse JSON output"""
        
        try:
            # Create temporary DOT file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as f:
                f.write(dot_string)
                dot_file = f.name
            
            # Run Graphviz dot command to get JSON output
            result = subprocess.run([
                'dot', '-Tjson', dot_file
            ], capture_output=True, text=True, check=True)
            
            # Clean up temp file
            Path(dot_file).unlink()
            
            # Parse JSON output
            layout_data = json.loads(result.stdout)
            
            # Debug: Uncomment for debugging
            # print(f"DEBUG: Graphviz JSON keys: {list(layout_data.keys())}")
            # if 'objects' in layout_data:
            #     print(f"DEBUG: Found {len(layout_data['objects'])} objects")
            
            return layout_data
            
        except subprocess.CalledProcessError as e:
            print(f"Graphviz error: {e}")
            print(f"DOT content:\n{dot_string}")
            raise
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Graphviz output:\n{result.stdout}")
            raise
    
    def _create_dto_from_layout(self, egi: RelationalGraphWithCuts, layout_data: Dict) -> LayoutDTO:
        """Create DTO objects from Graphviz layout data"""
        
        dto = LayoutDTO()
        
        # Parse overall bounding box
        bb = layout_data.get('bb', '0,0,100,100').split(',')
        total_width = float(bb[2]) - float(bb[0])
        total_height = float(bb[3]) - float(bb[1])
        
        # Create sheet area
        sheet_area = RenderableArea(
            id=egi.sheet,
            parent_id=None,
            rect=Rect(0, 0, total_width, total_height),
            is_sheet=True
        )
        dto.areas.append(sheet_area)
        
        # Process objects (both subgraphs and nodes are in objects array)
        for obj in layout_data.get('objects', []):
            if 'nodes' in obj:
                # This is a subgraph (cluster)
                self._process_subgraph(egi, obj, dto)
            else:
                # This is a node (vertex or edge label)
                self._process_node(egi, obj, dto)
        
        return dto
    
    def _process_subgraph(self, egi: RelationalGraphWithCuts, subgraph: Dict, dto: LayoutDTO):
        """Process a Graphviz subgraph (cut) into RenderableArea"""
        
        name = subgraph.get('name', '')
        if not name.startswith('cluster_'):
            return
        
        # Extract cut ID from cluster name
        cut_id = name.replace('cluster_', '')  # Keep original underscores
        
        # Parse bounding box
        bb = subgraph.get('bb', '0,0,100,100').split(',')
        x = float(bb[0])
        y = float(bb[1])
        width = float(bb[2]) - x
        height = float(bb[3]) - y
        
        # Find parent area
        parent_id = self._find_parent_area(egi, cut_id)
        
        area = RenderableArea(
            id=cut_id,
            parent_id=parent_id,
            rect=Rect(x, y, width, height),
            is_sheet=False
        )
        dto.areas.append(area)
    
    def _process_node(self, egi: RelationalGraphWithCuts, node: Dict, dto: LayoutDTO):
        """Process a Graphviz node into RenderableVertex or RenderableEdgeLabel"""
        
        name = node.get('name', '')  # Keep original name with underscores
        pos_str = node.get('pos', '0,0')
        
        # Parse position
        pos_parts = pos_str.split(',')
        x = float(pos_parts[0])
        y = float(pos_parts[1])
        
        # Find which area contains this element
        parent_area_id = self._find_element_area(egi, name)
        
        # Check if this is a vertex or edge
        if any(v.id == name for v in egi.V):
            # This is a vertex
            vertex = RenderableVertex(
                id=name,
                parent_area_id=parent_area_id,
                pos=(x, y)
            )
            dto.vertices.append(vertex)
            
        elif any(e.id == name for e in egi.E):
            # This is an edge label
            relation_name = egi.rel.get(name, "?")
            
            # Estimate text dimensions
            char_width = 8
            char_height = 12
            text_width = len(relation_name) * char_width
            text_height = char_height
            
            edge_label = RenderableEdgeLabel(
                id=name,
                parent_area_id=parent_area_id,
                rect=Rect(x - text_width/2, y - text_height/2, text_width, text_height),
                label=relation_name
            )
            dto.edge_labels.append(edge_label)
    
    def _find_parent_area(self, egi: RelationalGraphWithCuts, cut_id: ElementID) -> Optional[str]:
        """Find the parent area of a cut"""
        
        for container_id, elements in egi.area.items():
            if cut_id in elements:
                return container_id
        
        return egi.sheet  # Default to sheet
    
    def _find_element_area(self, egi: RelationalGraphWithCuts, element_id: ElementID) -> str:
        """Find which area directly contains an element"""
        
        for container_id, elements in egi.area.items():
            if element_id in elements:
                return container_id
        
        return egi.sheet  # Default to sheet
    
    def _route_ligatures(self, egi: RelationalGraphWithCuts, dto: LayoutDTO):
        """Stage 3: Route ligatures using A* pathfinding"""
        
        # Create pathfinding grid
        grid, grid_bounds = self._create_pathfinding_grid(dto)
        
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
                
                # Calculate path
                path_points = self._calculate_ligature_path(
                    vertex, edge_label, grid, grid_bounds, egi, dto
                )
                
                if path_points:
                    ligature = RenderableLigature(
                        start_vertex_id=vertex_id,
                        end_edge_id=edge_id,
                        end_hook_index=hook_index,
                        path_points=path_points
                    )
                    dto.ligatures.append(ligature)
    
    def _create_pathfinding_grid(self, dto: LayoutDTO) -> Tuple[Grid, Rect]:
        """Create a 2D grid for pathfinding with obstacles marked"""
        
        # Calculate overall bounds
        all_rects = [area.rect for area in dto.areas if not area.is_sheet]
        all_rects.extend([label.rect for label in dto.edge_labels])
        
        if not all_rects:
            return Grid(100, 100), Rect(0, 0, 100, 100)
        
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
        
        # Mark obstacles (edge labels and area boundaries)
        for label in dto.edge_labels:
            self._mark_rect_as_obstacle(matrix, label.rect, bounds)
        
        # Mark cut boundaries as high-cost (not completely blocked)
        for area in dto.areas:
            if not area.is_sheet:
                self._mark_boundary_as_costly(matrix, area.rect, bounds)
        
        grid = Grid(matrix=matrix)
        return grid, bounds
    
    def _mark_rect_as_obstacle(self, matrix: List[List[int]], rect: Rect, bounds: Rect):
        """Mark a rectangle as impassable in the grid"""
        
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
    
    def _mark_boundary_as_costly(self, matrix: List[List[int]], rect: Rect, bounds: Rect):
        """Mark area boundary as costly but not impassable"""
        # For now, keep boundaries passable - we'll handle cut crossing in path cost
        pass
    
    def _calculate_ligature_path(self, vertex: RenderableVertex, edge_label: RenderableEdgeLabel,
                               grid: Grid, grid_bounds: Rect, egi: RelationalGraphWithCuts,
                               dto: LayoutDTO) -> List[Tuple[float, float]]:
        """Calculate A* path between vertex and edge label"""
        
        # Convert positions to grid coordinates
        start_x = int((vertex.pos[0] - grid_bounds.x) * self.grid_resolution)
        start_y = int((vertex.pos[1] - grid_bounds.y) * self.grid_resolution)
        
        # Target is center of edge label
        target_x = int((edge_label.rect.x + edge_label.rect.width/2 - grid_bounds.x) * self.grid_resolution)
        target_y = int((edge_label.rect.y + edge_label.rect.height/2 - grid_bounds.y) * self.grid_resolution)
        
        # Clamp to grid bounds
        start_x = max(0, min(start_x, grid.width - 1))
        start_y = max(0, min(start_y, grid.height - 1))
        target_x = max(0, min(target_x, grid.width - 1))
        target_y = max(0, min(target_y, grid.height - 1))
        
        # Find path using A*
        finder = AStarFinder(diagonal_movement=DiagonalMovement.always)
        
        try:
            start_node = grid.node(start_x, start_y)
            end_node = grid.node(target_x, target_y)
            
            path, runs = finder.find_path(start_node, end_node, grid)
            
            if not path:
                # Fallback to straight line if no path found
                return [(vertex.pos[0], vertex.pos[1]), 
                       (edge_label.rect.x + edge_label.rect.width/2, 
                        edge_label.rect.y + edge_label.rect.height/2)]
            
            # Convert path back to world coordinates
            world_path = []
            for node in path[::max(1, len(path)//10)]:  # Simplify path
                world_x = node.x / self.grid_resolution + grid_bounds.x
                world_y = node.y / self.grid_resolution + grid_bounds.y
                world_path.append((world_x, world_y))
            
            return world_path
            
        except Exception as e:
            print(f"Pathfinding error: {e}")
            # Fallback to straight line
            return [(vertex.pos[0], vertex.pos[1]), 
                   (edge_label.rect.x + edge_label.rect.width/2, 
                    edge_label.rect.y + edge_label.rect.height/2)]
