"""
Definitive EGI Layout Engine - Three-Step Approach

This engine implements the definitive solution for EGI layout:
1. Unified Force-Directed Layout (neato): Position all content optimally in 2D space
2. Bottom-Up Bounding Box Calculation: Calculate container boundaries around content
3. Area-Aware Ligature Routing (A*): Intelligent pathfinding respecting cut hierarchy
"""

import json
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from pathlib import Path
from collections import defaultdict

try:
    from pathfinding.core.diagonal_movement import DiagonalMovement
    from pathfinding.core.grid import Grid
    from pathfinding.finder.a_star import AStarFinder
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install pathfinding")
    raise

from egi_core_dau import RelationalGraphWithCuts, ElementID
from area_aware_pathfinder import AreaAwareGrid, AreaAwareFinder


# --- DTO Structure ---

@dataclass
class Rect:
    x: float
    y: float
    width: float
    height: float
    
    def union(self, other: 'Rect') -> 'Rect':
        """Return the union (bounding box) of two rectangles"""
        min_x = min(self.x, other.x)
        min_y = min(self.y, other.y)
        max_x = max(self.x + self.width, other.x + other.width)
        max_y = max(self.y + self.height, other.y + other.height)
        return Rect(min_x, min_y, max_x - min_x, max_y - min_y)


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
    pos: Tuple[float, float]


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


class DefinitiveEGILayoutEngine:
    """Definitive three-step layout engine for optimal EGI visualization"""
    
    def __init__(self):
        self.grid_resolution = 2
        self.cut_padding = 15
        
    def generate_layout(self, egi: RelationalGraphWithCuts) -> LayoutDTO:
        """Main orchestration method for three-step layout"""
        
        # Step 1: Unified Force-Directed Layout (neato)
        content_positions = self._unified_force_directed_layout(egi)
        
        # Step 2: Bottom-Up Bounding Box Calculation
        area_bounds = self._calculate_bounding_boxes(egi, content_positions)
        
        # Step 3: Area-Aware Ligature Routing (A*)
        dto = self._create_dto_from_positions(egi, content_positions, area_bounds)
        self._area_aware_ligature_routing(egi, dto)
        
        return dto
    
    def _unified_force_directed_layout(self, egi: RelationalGraphWithCuts) -> Dict:
        """Step 1: Use neato to position all vertices and edge labels together"""
        
        # Generate DOT string with all content (NO containers)
        dot_string = self._generate_unified_dot(egi)
        
        # Execute neato layout engine
        neato_result = self._execute_graphviz_layout(dot_string, engine='neato')
        
        # Parse positions for all content
        positions = self._parse_content_positions(egi, neato_result)
        
        return positions
    
    def _generate_unified_dot(self, egi: RelationalGraphWithCuts) -> str:
        """Generate DOT string for unified force-directed layout"""
        
        lines = ["graph UnifiedLayout {"]
        lines.append("  overlap=false;")
        lines.append("  splines=true;")
        lines.append("  sep=\"+20\";")
        lines.append("  esep=\"+10\";")
        
        # Add all vertices as point nodes
        for vertex in egi.V:
            vertex_name = vertex.id.replace('-', '_')
            lines.append(f"  {vertex_name} [shape=point, width=0.15, height=0.15];")
        
        # Add all edges as text label nodes
        for edge in egi.E:
            edge_name = edge.id.replace('-', '_')
            relation_name = egi.rel.get(edge.id, "?")
            lines.append(f"  {edge_name} [shape=plaintext, label=\"{relation_name}\"];")
        
        # Add connections (ligatures)
        for edge_id, vertex_sequence in egi.nu.items():
            edge_name = edge_id.replace('-', '_')
            for vertex_id in vertex_sequence:
                vertex_name = vertex_id.replace('-', '_')
                lines.append(f"  {vertex_name} -- {edge_name};")
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def _parse_content_positions(self, egi: RelationalGraphWithCuts, neato_result: Dict) -> Dict:
        """Parse positions for all vertices and edge labels"""
        
        positions = {'vertices': {}, 'edge_labels': {}}
        
        for obj in neato_result.get('objects', []):
            name = obj.get('name', '')
            if 'pos' not in obj:
                continue
            
            # Parse position
            pos_str = obj.get('pos', '0,0')
            pos_parts = pos_str.split(',')
            x = float(pos_parts[0])
            y = float(pos_parts[1])
            
            # Determine if this is a vertex or edge
            element_id = name  # Keep original name with underscores
            
            if any(v.id == element_id for v in egi.V):
                # This is a vertex
                positions['vertices'][element_id] = {
                    'x': x, 'y': y,
                    'parent_area_id': self._find_element_area(egi, element_id)
                }
            elif any(e.id == element_id for e in egi.E):
                # This is an edge label
                relation_name = egi.rel.get(element_id, "?")
                char_width, char_height = 8, 12
                text_width = len(relation_name) * char_width
                text_height = char_height
                
                positions['edge_labels'][element_id] = {
                    'x': x, 'y': y, 'width': text_width, 'height': text_height,
                    'label': relation_name,
                    'parent_area_id': self._find_element_area(egi, element_id)
                }
        
        return positions
    
    def _calculate_bounding_boxes(self, egi: RelationalGraphWithCuts, positions: Dict) -> Dict:
        """Step 2: Calculate container boundaries bottom-up"""
        
        hierarchy = self._build_cut_hierarchy(egi)
        area_bounds = {}
        
        # Process cuts in bottom-up order
        cut_order = self._get_bottom_up_cut_order(egi, hierarchy)
        
        for cut_id in cut_order:
            area_bounds[cut_id] = self._calculate_cut_bounding_box(
                egi, cut_id, positions, area_bounds, hierarchy
            )
        
        # Calculate sheet bounding box
        area_bounds[egi.sheet] = self._calculate_sheet_bounding_box(
            egi, positions, area_bounds
        )
        
        return area_bounds
    
    def _build_cut_hierarchy(self, egi: RelationalGraphWithCuts) -> Dict:
        """Build parent-child relationships for cuts"""
        
        hierarchy = {}
        all_containers = {egi.sheet} | {cut.id for cut in egi.Cut}
        
        for container_id in all_containers:
            hierarchy[container_id] = {
                'parent': None, 'children': set(), 'elements': set(),
                'is_sheet': container_id == egi.sheet
            }
        
        for container_id, elements in egi.area.items():
            if container_id not in hierarchy:
                continue
                
            for element_id in elements:
                if element_id in all_containers and element_id != container_id:
                    hierarchy[element_id]['parent'] = container_id
                    hierarchy[container_id]['children'].add(element_id)
                else:
                    hierarchy[container_id]['elements'].add(element_id)
        
        return hierarchy
    
    def _get_bottom_up_cut_order(self, egi: RelationalGraphWithCuts, hierarchy: Dict) -> List[str]:
        """Get cuts in bottom-up processing order"""
        
        remaining_cuts = {cut.id for cut in egi.Cut}
        processed = set()
        order = []
        
        while remaining_cuts:
            ready_cuts = []
            for cut_id in remaining_cuts:
                children = hierarchy[cut_id]['children']
                if all(child in processed or child == egi.sheet for child in children):
                    ready_cuts.append(cut_id)
            
            if not ready_cuts:
                ready_cuts = [next(iter(remaining_cuts))]
            
            for cut_id in ready_cuts:
                order.append(cut_id)
                processed.add(cut_id)
                remaining_cuts.remove(cut_id)
        
        return order
    
    def _calculate_cut_bounding_box(self, egi: RelationalGraphWithCuts, cut_id: str, 
                                  positions: Dict, area_bounds: Dict, hierarchy: Dict) -> Rect:
        """Calculate bounding box for a single cut"""
        
        rects_to_include = []
        
        # Include directly contained elements
        for element_id in hierarchy[cut_id]['elements']:
            if element_id in positions['vertices']:
                pos = positions['vertices'][element_id]
                vertex_rect = Rect(pos['x'] - 2, pos['y'] - 2, 4, 4)
                rects_to_include.append(vertex_rect)
            elif element_id in positions['edge_labels']:
                pos = positions['edge_labels'][element_id]
                label_rect = Rect(pos['x'] - pos['width']/2, pos['y'] - pos['height']/2,
                                pos['width'], pos['height'])
                rects_to_include.append(label_rect)
        
        # Include child cut bounding boxes
        for child_id in hierarchy[cut_id]['children']:
            if child_id in area_bounds:
                rects_to_include.append(area_bounds[child_id])
        
        if not rects_to_include:
            return Rect(0, 0, 50, 30)
        
        # Calculate union and add padding
        bounding_box = rects_to_include[0]
        for rect in rects_to_include[1:]:
            bounding_box = bounding_box.union(rect)
        
        return Rect(bounding_box.x - self.cut_padding, bounding_box.y - self.cut_padding,
                   bounding_box.width + 2 * self.cut_padding, 
                   bounding_box.height + 2 * self.cut_padding)
    
    def _calculate_sheet_bounding_box(self, egi: RelationalGraphWithCuts, 
                                    positions: Dict, area_bounds: Dict) -> Rect:
        """Calculate bounding box for the sheet"""
        
        rects_to_include = []
        
        # Include all positioned content
        for pos in positions['vertices'].values():
            vertex_rect = Rect(pos['x'] - 2, pos['y'] - 2, 4, 4)
            rects_to_include.append(vertex_rect)
        
        for pos in positions['edge_labels'].values():
            label_rect = Rect(pos['x'] - pos['width']/2, pos['y'] - pos['height']/2,
                            pos['width'], pos['height'])
            rects_to_include.append(label_rect)
        
        # Include all cut bounding boxes
        for cut in egi.Cut:
            if cut.id in area_bounds:
                rects_to_include.append(area_bounds[cut.id])
        
        if not rects_to_include:
            return Rect(0, 0, 200, 150)
        
        bounding_box = rects_to_include[0]
        for rect in rects_to_include[1:]:
            bounding_box = bounding_box.union(rect)
        
        sheet_padding = 20
        return Rect(bounding_box.x - sheet_padding, bounding_box.y - sheet_padding,
                   bounding_box.width + 2 * sheet_padding, 
                   bounding_box.height + 2 * sheet_padding)
    
    def _create_dto_from_positions(self, egi: RelationalGraphWithCuts, 
                                 positions: Dict, area_bounds: Dict) -> LayoutDTO:
        """Create DTO from calculated positions and bounds"""
        
        dto = LayoutDTO()
        hierarchy = self._build_cut_hierarchy(egi)
        
        # Create areas
        for area_id, rect in area_bounds.items():
            parent_id = hierarchy[area_id]['parent'] if area_id != egi.sheet else None
            area = RenderableArea(id=area_id, parent_id=parent_id, rect=rect,
                                is_sheet=(area_id == egi.sheet))
            dto.areas.append(area)
        
        # Create vertices
        for vertex_id, pos_data in positions['vertices'].items():
            vertex = RenderableVertex(id=vertex_id, parent_area_id=pos_data['parent_area_id'],
                                    pos=(pos_data['x'], pos_data['y']))
            dto.vertices.append(vertex)
        
        # Create edge labels
        for edge_id, pos_data in positions['edge_labels'].items():
            edge_label = RenderableEdgeLabel(
                id=edge_id, parent_area_id=pos_data['parent_area_id'],
                rect=Rect(pos_data['x'] - pos_data['width']/2, pos_data['y'] - pos_data['height']/2,
                         pos_data['width'], pos_data['height']),
                label=pos_data['label'])
            dto.edge_labels.append(edge_label)
        
        return dto
    
    def _area_aware_ligature_routing(self, egi: RelationalGraphWithCuts, dto: LayoutDTO):
        """Step 3: Route ligatures with area-aware A* pathfinding"""
        
        # Build area-aware collision map
        area_grid, grid_bounds = self._build_area_aware_collision_map(dto)
        hierarchy = self._build_cut_hierarchy(egi)
        
        # Route each ligature
        for edge_id, vertex_sequence in egi.nu.items():
            if not vertex_sequence:
                continue
            
            edge_label = next((l for l in dto.edge_labels if l.id == edge_id), None)
            if not edge_label:
                continue
            
            for hook_index, vertex_id in enumerate(vertex_sequence):
                vertex = next((v for v in dto.vertices if v.id == vertex_id), None)
                if not vertex:
                    continue
                
                path_points = self._calculate_area_aware_path(
                    vertex, edge_label, area_grid, grid_bounds, hierarchy
                )
                
                if path_points:
                    ligature = RenderableLigature(
                        start_vertex_id=vertex_id, end_edge_id=edge_id,
                        end_hook_index=hook_index, path_points=path_points
                    )
                    dto.ligatures.append(ligature)
    
    def _build_area_aware_collision_map(self, dto: LayoutDTO) -> Tuple:
        """Build collision map with area membership tracking"""
        
        all_rects = [area.rect for area in dto.areas]
        if not all_rects:
            return AreaAwareGrid(100, 100), Rect(0, 0, 100, 100)
        
        bounds = all_rects[0]
        for rect in all_rects[1:]:
            bounds = bounds.union(rect)
        
        padding = 20
        grid_bounds = Rect(bounds.x - padding, bounds.y - padding,
                          bounds.width + 2*padding, bounds.height + 2*padding)
        
        grid_width = int(grid_bounds.width * self.grid_resolution)
        grid_height = int(grid_bounds.height * self.grid_resolution)
        
        walkable_matrix = [[1 for _ in range(grid_width)] for _ in range(grid_height)]
        area_map = [[None for _ in range(grid_width)] for _ in range(grid_height)]
        
        # Mark area membership (largest to smallest for proper nesting)
        sorted_areas = sorted(dto.areas, key=lambda a: a.rect.width * a.rect.height, reverse=True)
        for area in sorted_areas:
            self._mark_area_in_grid(area_map, area, grid_bounds)
        
        # Mark obstacles
        for vertex in dto.vertices:
            vertex_rect = Rect(vertex.pos[0] - 3, vertex.pos[1] - 3, 6, 6)
            self._mark_rect_as_obstacle(walkable_matrix, vertex_rect, grid_bounds)
        
        for label in dto.edge_labels:
            self._mark_rect_as_obstacle(walkable_matrix, label.rect, grid_bounds)
        
        return AreaAwareGrid(grid_width, grid_height, walkable_matrix, area_map), grid_bounds
    
    def _calculate_area_aware_path(self, vertex, edge_label, area_grid, grid_bounds, hierarchy):
        """Calculate path using area-aware A* pathfinding"""
        
        # Convert positions to grid coordinates
        start_x = int((vertex.pos[0] - grid_bounds.x) * self.grid_resolution)
        start_y = int((vertex.pos[1] - grid_bounds.y) * self.grid_resolution)
        target_x = int((edge_label.rect.x + edge_label.rect.width/2 - grid_bounds.x) * self.grid_resolution)
        target_y = int((edge_label.rect.y + edge_label.rect.height/2 - grid_bounds.y) * self.grid_resolution)
        
        # Clamp to grid bounds
        start_x = max(0, min(start_x, area_grid.width - 1))
        start_y = max(0, min(start_y, area_grid.height - 1))
        target_x = max(0, min(target_x, area_grid.width - 1))
        target_y = max(0, min(target_y, area_grid.height - 1))
        
        # Calculate legal corridor
        legal_areas = self._calculate_legal_corridor(
            vertex.parent_area_id, edge_label.parent_area_id, hierarchy
        )
        
        # Use area-aware finder
        finder = AreaAwareFinder(legal_areas)
        
        try:
            start_node = area_grid.node(start_x, start_y)
            end_node = area_grid.node(target_x, target_y)
            path, runs = finder.find_path(start_node, end_node, area_grid)
            
            if not path:
                return [vertex.pos, (edge_label.rect.x + edge_label.rect.width/2,
                                   edge_label.rect.y + edge_label.rect.height/2)]
            
            # Convert to world coordinates and simplify
            world_path = []
            for i in range(0, len(path), max(1, len(path)//8)):
                node = path[i]
                world_x = node.x / self.grid_resolution + grid_bounds.x
                world_y = node.y / self.grid_resolution + grid_bounds.y
                world_path.append((world_x, world_y))
            
            target_world = (edge_label.rect.x + edge_label.rect.width/2,
                          edge_label.rect.y + edge_label.rect.height/2)
            if world_path[-1] != target_world:
                world_path.append(target_world)
            
            return world_path
            
        except Exception:
            return [vertex.pos, (edge_label.rect.x + edge_label.rect.width/2,
                               edge_label.rect.y + edge_label.rect.height/2)]
    
    def _calculate_legal_corridor(self, area_a: str, area_b: str, hierarchy: Dict) -> Set[str]:
        """Calculate legal corridor for path between two areas"""
        
        if area_a == area_b:
            return {area_a}
        
        path_a = self._get_path_to_root(area_a, hierarchy)
        path_b = self._get_path_to_root(area_b, hierarchy)
        
        common_ancestors = set(path_a) & set(path_b)
        if not common_ancestors:
            return set(hierarchy.keys())
        
        lca = min(common_ancestors, key=lambda x: len(self._get_path_to_root(x, hierarchy)))
        
        corridor = set()
        
        # Add paths to LCA
        current = area_a
        while current and current != lca:
            corridor.add(current)
            current = hierarchy[current]['parent']
        
        current = area_b
        while current and current != lca:
            corridor.add(current)
            current = hierarchy[current]['parent']
        
        corridor.add(lca)
        return corridor
    
    def _get_path_to_root(self, area_id: str, hierarchy: Dict) -> List[str]:
        """Get path from area to root"""
        path = []
        current = area_id
        while current:
            path.append(current)
            current = hierarchy[current]['parent']
        return path
    
    # Helper methods
    
    def _execute_graphviz_layout(self, dot_string: str, engine: str = 'neato') -> Dict:
        """Execute Graphviz and return JSON"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as f:
                f.write(dot_string)
                dot_file = f.name
            
            result = subprocess.run([engine, '-Tjson', dot_file], 
                                  capture_output=True, text=True, check=True)
            Path(dot_file).unlink()
            return json.loads(result.stdout)
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            print(f"Graphviz error: {e}")
            raise
    
    def _find_element_area(self, egi: RelationalGraphWithCuts, element_id: str) -> str:
        """Find which area contains an element"""
        for container_id, elements in egi.area.items():
            if element_id in elements:
                return container_id
        return egi.sheet
    
    def _mark_area_in_grid(self, area_map, area, grid_bounds):
        """Mark area membership in grid"""
        start_x = int((area.rect.x - grid_bounds.x) * self.grid_resolution)
        start_y = int((area.rect.y - grid_bounds.y) * self.grid_resolution)
        end_x = int((area.rect.x + area.rect.width - grid_bounds.x) * self.grid_resolution)
        end_y = int((area.rect.y + area.rect.height - grid_bounds.y) * self.grid_resolution)
        
        start_x = max(0, min(start_x, len(area_map[0]) - 1))
        start_y = max(0, min(start_y, len(area_map) - 1))
        end_x = max(0, min(end_x, len(area_map[0]) - 1))
        end_y = max(0, min(end_y, len(area_map) - 1))
        
        for y in range(start_y, end_y + 1):
            for x in range(start_x, end_x + 1):
                if 0 <= y < len(area_map) and 0 <= x < len(area_map[0]):
                    area_map[y][x] = area.id
    
    def _mark_rect_as_obstacle(self, matrix, rect, bounds):
        """Mark rectangle as obstacle in grid"""
        start_x = int((rect.x - bounds.x) * self.grid_resolution)
        start_y = int((rect.y - bounds.y) * self.grid_resolution)
        end_x = int((rect.x + rect.width - bounds.x) * self.grid_resolution)
        end_y = int((rect.y + rect.height - bounds.y) * self.grid_resolution)
        
        start_x = max(0, min(start_x, len(matrix[0]) - 1))
        start_y = max(0, min(start_y, len(matrix) - 1))
        end_x = max(0, min(end_x, len(matrix[0]) - 1))
        end_y = max(0, min(end_y, len(matrix) - 1))
        
        for y in range(start_y, end_y + 1):
            for x in range(start_x, end_x + 1):
                if 0 <= y < len(matrix) and 0 <= x < len(matrix[0]):
                    matrix[y][x] = 0
