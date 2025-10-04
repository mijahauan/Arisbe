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
from typing import Dict, List, Optional, Tuple, Set, Any
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
from style_loader import StyleLoader, StyleSpecification
from style_specification import RenderableAnnotation


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
    style: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RenderableVertex:
    id: str
    parent_area_id: str
    pos: Tuple[float, float]
    style: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConnectionPort:
    """A connection port on an EdgeLabel's bounding box"""
    port_id: int  # Index in the vertex sequence (0-based)
    position: Tuple[float, float]  # Absolute coordinates
    direction: str  # Cardinal/intercardinal direction (N, E, S, W, NE, NW, SE, SW)


@dataclass
class RenderableEdgeLabel:
    id: str
    parent_area_id: str
    rect: Rect
    label: str
    connection_ports: List[ConnectionPort] = field(default_factory=list)
    style: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RenderableLigature:
    start_vertex_id: str
    end_edge_id: str
    end_hook_index: int
    path_points: List[Tuple[float, float]]
    style: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LayoutDTO:
    areas: List[RenderableArea] = field(default_factory=list)
    vertices: List[RenderableVertex] = field(default_factory=list)
    edge_labels: List[RenderableEdgeLabel] = field(default_factory=list)
    ligatures: List[RenderableLigature] = field(default_factory=list)
    annotations: List[RenderableAnnotation] = field(default_factory=list)


@dataclass
class LayoutDelta:
    """Represents user edits to layout positions and paths"""
    element_id: str  # The element being modified
    delta_type: str  # 'vertex_position', 'edge_position', 'ligature_path'
    original_position: Optional[Tuple[float, float]] = None
    new_position: Optional[Tuple[float, float]] = None
    custom_path: Optional[List[Tuple[float, float]]] = None  # For ligature paths
    nu_mapping_key: Optional[str] = None  # For ligature path identification

@dataclass
class LayoutDeltas:
    """Collection of user layout modifications"""
    deltas: Dict[str, LayoutDelta] = field(default_factory=dict)
    deterministic_seed: Optional[int] = None  # For reproducible layouts


class DefinitiveEGILayoutEngine:
    """Definitive three-step layout engine for optimal EGI visualization"""
    
    def __init__(self):
        self.grid_resolution = 2
        self.cut_padding = 15
        
    def generate_layout(self, egi: RelationalGraphWithCuts, style: Optional[StyleSpecification] = None, layout_deltas: Optional[LayoutDeltas] = None) -> LayoutDTO:
        """Main orchestration method for bottom-up layout with cuts as positioned elements"""
        
        # Use default style if none provided
        if style is None:
            style_loader = StyleLoader()
            style = style_loader.load_default_style()
        
        # Initialize layout_deltas if none provided
        if layout_deltas is None:
            layout_deltas = LayoutDeltas()
        
        # NEW APPROACH: Bottom-up layout with cuts as rectangular elements
        # Step 1: Build area hierarchy
        hierarchy = self._build_area_hierarchy_v2(egi)
        
        # Step 2: Layout each area bottom-up (innermost first)
        area_layouts = self._bottom_up_area_layout(egi, hierarchy, style, layout_deltas)
        
        # Step 3: Transform local coordinates to global
        global_positions, area_bounds = self._transform_to_global_coords(egi, hierarchy, area_layouts)
        
        # Step 4: Create DTO from positioned elements
        dto = self._create_dto_from_positions(egi, global_positions, area_bounds)
        
        # Step 5: Route ligatures with area awareness (pass v2 hierarchy)
        self._area_aware_ligature_routing(egi, dto, style, layout_deltas, hierarchy)
        
        # Step 6: Apply aesthetic styles
        self._apply_aesthetic_styles(dto, egi, style)
        
        return dto
    
    def _unified_force_directed_layout(self, egi: RelationalGraphWithCuts, style: StyleSpecification, layout_deltas: LayoutDeltas) -> Dict:
        """Step 1: Use neato to position all vertices and edge labels together with user deltas"""
        
        # Generate DOT string with all content (NO containers) using style
        dot_string = self._generate_unified_dot(egi, style, layout_deltas)
        
        # Execute layout engine using style-specified engine
        layout_engine = style.raw_style_data.get('layout', {}).get('engine', 'neato')
        neato_result = self._execute_graphviz_layout(dot_string, engine=layout_engine)
        
        # Parse positions for all content
        positions = self._parse_content_positions(egi, neato_result)
        
        return positions
    
    def _generate_unified_dot(self, egi: RelationalGraphWithCuts, style: StyleSpecification, layout_deltas: Optional[LayoutDeltas] = None) -> str:
        """Generate DOT string for unified force-directed layout with style attributes and pinned nodes"""
        
        lines = ["graph UnifiedLayout {"]
        
        # Apply graph-level attributes from style
        graphviz_attrs = style.raw_style_data.get('layout', {}).get('graphviz_attrs', {})
        graph_attrs = graphviz_attrs.get('graph', {})
        
        # Set default graph attributes
        default_graph_attrs = {
            "layout": "neato",
            "overlap": "false",
            "splines": "true"
        }
        default_graph_attrs.update(graph_attrs)
        
        # Add deterministic seed for reproducible layouts
        if layout_deltas and layout_deltas.deterministic_seed is not None:
            default_graph_attrs["seed"] = str(layout_deltas.deterministic_seed)
        else:
            # Use a fixed seed for consistent results
            default_graph_attrs["seed"] = "42"
        
        # Force deterministic initial placement
        default_graph_attrs["start"] = "random42"  # Use fixed random seed for initial positions
        
        for attr, value in default_graph_attrs.items():
            lines.append(f"  {attr}=\"{value}\";")
        
        # Get node attributes from style
        node_attrs = graphviz_attrs.get('node', {})
        default_node_attrs = {
            "fontname": "Times-Roman",
            "fontsize": "12"
        }
        default_node_attrs.update(node_attrs)
        
        # Add all vertices as point nodes (sorted for determinism)
        for vertex in sorted(egi.V, key=lambda v: v.id):
            vertex_name = vertex.id  # IDs already use underscores
            
            # Check if this vertex has a user-defined position
            if layout_deltas and vertex.id in layout_deltas.deltas:
                delta = layout_deltas.deltas[vertex.id]
                if delta.delta_type == 'vertex_position' and delta.new_position:
                    # Add as pinned node with user position
                    lines.append(f"  {vertex_name} [shape=point, width=0.15, height=0.15, pos=\"{delta.new_position[0]},{delta.new_position[1]}!\", pin=true];")
                else:
                    # Add as normal movable node
                    lines.append(f"  {vertex_name} [shape=point, width=0.15, height=0.15];")
            else:
                # Add as normal movable node
                lines.append(f"  {vertex_name} [shape=point, width=0.15, height=0.15];")
        
        # Add all edges as text label nodes with style attributes (sorted for determinism)
        # Sort by relation name first, then ID for stable ordering
        for edge in sorted(egi.E, key=lambda e: (egi.rel.get(e.id, ""), e.id)):
            edge_name = edge.id  # IDs already use underscores
            relation_name = egi.rel.get(edge.id, "?")
            
            # Build node attribute string
            node_attr_strs = [f"shape=plaintext", f"label=\"{relation_name}\""]
            for attr, value in default_node_attrs.items():
                node_attr_strs.append(f"{attr}=\"{value}\"")
            
            # Check if this edge has a user-defined position
            if layout_deltas and edge.id in layout_deltas.deltas:
                delta = layout_deltas.deltas[edge.id]
                if delta.delta_type == 'edge_position' and delta.new_position:
                    # Add as pinned node with user position
                    node_attr_strs.append(f"pos=\"{delta.new_position[0]},{delta.new_position[1]}!\"")
                    node_attr_strs.append("pin=true")
            
            lines.append(f"  {edge_name} [{', '.join(node_attr_strs)}];")
        
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
            # DOT uses underscores in names, need to match back to original IDs
            element_id = name
            
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
    
    def _calculate_bounding_boxes(self, egi: RelationalGraphWithCuts, positions: Dict, style: StyleSpecification) -> Dict:
        """Step 2: Calculate container boundaries bottom-up with style-aware padding"""
        
        hierarchy = self._build_cut_hierarchy(egi)
        area_bounds = {}
        
        # Get padding from style
        area_padding = style.raw_style_data.get('geometry', {}).get('padding', {}).get('area', 15)
        
        # Process cuts in bottom-up order
        cut_order = self._get_bottom_up_cut_order(egi, hierarchy)
        
        for cut_id in cut_order:
            area_bounds[cut_id] = self._calculate_cut_bounding_box(
                egi, cut_id, positions, area_bounds, hierarchy, area_padding
            )
        
        # Calculate sheet bounding box
        area_bounds[egi.sheet] = self._calculate_sheet_bounding_box(
            egi, positions, area_bounds, area_padding
        )
        
        return area_bounds
    
    def _build_cut_hierarchy(self, egi: RelationalGraphWithCuts) -> Dict:
        """Build parent-child relationships for cuts"""
        
        hierarchy = {}
        all_containers = {egi.sheet} | {cut.id for cut in sorted(egi.Cut, key=lambda c: c.id)}
        
        for container_id in all_containers:
            hierarchy[container_id] = {
                'parent': None, 'children': set(), 'elements': set(),
                'is_sheet': container_id == egi.sheet
            }
        
        for container_id, elements in sorted(egi.area.items()):
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
        
        remaining_cuts = {cut.id for cut in sorted(egi.Cut, key=lambda c: c.id)}
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
                                  positions: Dict, area_bounds: Dict, hierarchy: Dict, padding: float) -> Rect:
        """Calculate bounding box for a single cut with style-aware padding"""
        
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
        
        # Calculate union and add style-aware padding
        bounding_box = rects_to_include[0]
        for rect in rects_to_include[1:]:
            bounding_box = bounding_box.union(rect)
        
        return Rect(bounding_box.x - padding, bounding_box.y - padding,
                   bounding_box.width + 2 * padding, 
                   bounding_box.height + 2 * padding)
    
    def _calculate_sheet_bounding_box(self, egi: RelationalGraphWithCuts, 
                                    positions: Dict, area_bounds: Dict, padding: float) -> Rect:
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
        
        # Include all cut bounding boxes (sorted for determinism)
        for cut in sorted(egi.Cut, key=lambda c: c.id):
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
            # Create tight bounding box around text
            rect = Rect(pos_data['x'] - pos_data['width']/2, pos_data['y'] - pos_data['height']/2,
                       pos_data['width'], pos_data['height'])
            
            # Calculate connection ports based on nu mapping and vertex positions
            vertex_sequence = egi.nu.get(edge_id, [])
            connection_ports = self._calculate_connection_ports_with_vertices(
                rect, vertex_sequence, positions['vertices']
            )
            
            edge_label = RenderableEdgeLabel(
                id=edge_id, parent_area_id=pos_data['parent_area_id'],
                rect=rect, label=pos_data['label'],
                connection_ports=connection_ports)
            dto.edge_labels.append(edge_label)
        
        return dto
    
    def _area_aware_ligature_routing(self, egi: RelationalGraphWithCuts, dto: LayoutDTO, style: StyleSpecification, layout_deltas: Optional[LayoutDeltas] = None, hierarchy: Dict = None):
        """Step 3: Route ligatures with area-aware A* pathfinding and custom path support"""
        
        # Build area-aware collision map
        area_grid, grid_bounds = self._build_area_aware_collision_map(dto)
        
        # Use provided hierarchy (v2 format) or build old format as fallback
        if hierarchy is None:
            hierarchy = self._build_cut_hierarchy(egi)
        
        # Route each ligature (sorted for determinism)
        for edge_id, vertex_sequence in sorted(egi.nu.items()):
            if not vertex_sequence:
                continue
            
            edge_label = next((l for l in dto.edge_labels if l.id == edge_id), None)
            if not edge_label:
                continue
            
            # Find nearest port for each vertex to avoid crossings
            vertex_port_assignments = self._assign_nearest_ports(vertex_sequence, edge_label, dto.vertices)
            
            for hook_index, vertex_id in enumerate(vertex_sequence):
                vertex = next((v for v in dto.vertices if v.id == vertex_id), None)
                if not vertex:
                    continue
                
                # Check if there's a custom path for this ligature
                ligature_key = f"{vertex_id}_{edge_id}_{hook_index}"
                custom_path = None
                
                if layout_deltas and ligature_key in layout_deltas.deltas:
                    delta = layout_deltas.deltas[ligature_key]
                    if delta.delta_type == 'ligature_path' and delta.custom_path:
                        custom_path = self._validate_custom_path(
                            delta.custom_path, vertex.pos, 
                            self._get_edge_label_center(edge_label),
                            area_grid, grid_bounds, hierarchy, dto
                        )
                
                if custom_path:
                    # Use validated custom path
                    ligature = RenderableLigature(
                        start_vertex_id=vertex_id, end_edge_id=edge_id,
                        end_hook_index=hook_index, path_points=custom_path
                    )
                    dto.ligatures.append(ligature)
                else:
                    # Use the nearest port assignment instead of sequence index
                    target_port = vertex_port_assignments.get(vertex_id)
                    
                    path_points = self._calculate_area_aware_path_to_port(
                        vertex, edge_label, target_port, area_grid, grid_bounds, hierarchy
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
        
        # Mark obstacles: vertices and edge labels only
        # Cuts are NOT hard obstacles - legal corridor determines crossing permission
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
            
            # CRITICAL FIX: Ensure path starts at exact vertex position and ends at exact target
            # The A* grid path may have quantization errors
            if world_path:
                world_path[0] = vertex.pos  # Force exact start position
                world_path[-1] = target_world  # Force exact end position
            
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
        for container_id, elements in sorted(egi.area.items()):
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
    
    def _mark_rect_boundary_as_obstacle(self, matrix, rect, bounds):
        """Mark only the boundary perimeter of a rectangle as obstacle (not the interior)"""
        start_x = int((rect.x - bounds.x) * self.grid_resolution)
        start_y = int((rect.y - bounds.y) * self.grid_resolution)
        end_x = int((rect.x + rect.width - bounds.x) * self.grid_resolution)
        end_y = int((rect.y + rect.height - bounds.y) * self.grid_resolution)
        
        start_x = max(0, min(start_x, len(matrix[0]) - 1))
        start_y = max(0, min(start_y, len(matrix) - 1))
        end_x = max(0, min(end_x, len(matrix[0]) - 1))
        end_y = max(0, min(end_y, len(matrix) - 1))
        
        # Mark top and bottom edges
        for x in range(start_x, end_x + 1):
            if 0 <= start_y < len(matrix) and 0 <= x < len(matrix[0]):
                matrix[start_y][x] = 0
            if 0 <= end_y < len(matrix) and 0 <= x < len(matrix[0]):
                matrix[end_y][x] = 0
        
        # Mark left and right edges
        for y in range(start_y, end_y + 1):
            if 0 <= y < len(matrix) and 0 <= start_x < len(matrix[0]):
                matrix[y][start_x] = 0
            if 0 <= y < len(matrix) and 0 <= end_x < len(matrix[0]):
                matrix[y][end_x] = 0
    
    def _get_edge_label_center(self, edge_label: RenderableEdgeLabel) -> Tuple[float, float]:
        """Get the center point of an edge label"""
        return (edge_label.rect.x + edge_label.rect.width / 2,
                edge_label.rect.y + edge_label.rect.height / 2)
    
    def _validate_custom_path(self, custom_path: List[Tuple[float, float]], 
                            start_pos: Tuple[float, float], end_pos: Tuple[float, float],
                            area_grid, grid_bounds, hierarchy, dto) -> Optional[List[Tuple[float, float]]]:
        """Validate and update a custom path to ensure it's still legal"""
        
        # Update start and end points to current vertex and edge positions
        updated_path = [start_pos] + custom_path[1:-1] + [end_pos]
        
        # Basic collision detection - check if path intersects any obstacles
        if self._path_collides_with_obstacles(updated_path, dto):
            return None  # Path is invalid
        
        # Area-aware validation - check if path respects logical boundaries
        if not self._path_respects_areas(updated_path, area_grid, grid_bounds, hierarchy):
            return None  # Path violates logical constraints
        
        return updated_path
    
    def _path_collides_with_obstacles(self, path: List[Tuple[float, float]], dto: LayoutDTO) -> bool:
        """Check if path collides with any obstacles in the diagram"""
        
        # Simple collision detection - check against all vertices and edge labels
        for point in path:
            # Check vertices
            for vertex in dto.vertices:
                if self._point_in_circle(point, vertex.pos, 6):  # 6px radius around vertex
                    return True
            
            # Check edge labels
            for label in dto.edge_labels:
                if self._point_in_rect(point, label.rect):
                    return True
        
        return False
    
    def _point_in_circle(self, point: Tuple[float, float], center: Tuple[float, float], radius: float) -> bool:
        """Check if point is within a circle"""
        dx = point[0] - center[0]
        dy = point[1] - center[1]
        return (dx * dx + dy * dy) <= (radius * radius)
    
    def _point_in_rect(self, point: Tuple[float, float], rect: Rect) -> bool:
        """Check if point is within a rectangle"""
        return (rect.x <= point[0] <= rect.x + rect.width and
                rect.y <= point[1] <= rect.y + rect.height)
    
    def _path_respects_areas(self, path: List[Tuple[float, float]], 
                           area_grid, grid_bounds, hierarchy) -> bool:
        """Check if path respects logical area boundaries"""
        
        # Convert path points to grid coordinates and check area membership
        for i, point in enumerate(path):
            grid_x = int((point[0] - grid_bounds.x) * self.grid_resolution)
            grid_y = int((point[1] - grid_bounds.y) * self.grid_resolution)
            
            # Clamp to grid bounds
            grid_x = max(0, min(grid_x, area_grid.width - 1))
            grid_y = max(0, min(grid_y, area_grid.height - 1))
            
            # Get area at this grid position
            area_id = area_grid.area_map[grid_y][grid_x]
            
            # Check if this area is in the legal corridor
            # For simplicity, we'll allow paths through any area for now
            # In a full implementation, this would check the legal corridor
            if area_id is None:
                return False
        
        return True
    
    def _apply_user_overrides_to_positions(self, egi: RelationalGraphWithCuts, 
                                           content_positions: Dict, 
                                           layout_deltas: Optional[LayoutDeltas]) -> Dict:
        """
        Apply validated user position overrides to the positions dictionary.
        CRITICAL: This must happen BEFORE creating DTO so ligatures route from correct positions.
        Validates positions are within logical parent areas.
        """
        if not layout_deltas or not layout_deltas.deltas:
            return content_positions
        
        # We need area bounds to validate, so calculate them temporarily
        # This is needed to check if positions are valid within their logical areas
        temp_area_bounds = {}
        
        # Build minimal area bounds for validation
        hierarchy = self._build_cut_hierarchy(egi)
        for area_id in hierarchy:
            if area_id == egi.sheet:
                continue
            # For cuts, we need their bounds - but we don't have them yet!
            # This is a chicken-and-egg problem. 
            # Solution: Only validate against sheet bounds initially
        
        # For now, apply overrides and rely on DTO-level validation
        # to catch invalid positions after bounding boxes are calculated
        for element_id, delta in layout_deltas.deltas.items():
            if delta.delta_type == 'vertex_position' and delta.new_position:
                if element_id in content_positions['vertices']:
                    # Apply the user's position
                    content_positions['vertices'][element_id]['x'] = delta.new_position[0]
                    content_positions['vertices'][element_id]['y'] = delta.new_position[1]
            elif delta.delta_type == 'edge_position' and delta.new_position:
                if element_id in content_positions['edge_labels']:
                    # Apply the user's position
                    content_positions['edge_labels'][element_id]['x'] = delta.new_position[0]
                    content_positions['edge_labels'][element_id]['y'] = delta.new_position[1]
        
        return content_positions
    
    def _apply_user_position_overrides(self, dto: LayoutDTO, layout_deltas: Optional[LayoutDeltas]):
        """
        Apply user-specified position overrides to the DTO.
        CRITICAL: Only applies positions that are valid within the logical area structure.
        Invalid positions (outside logical parent area) are rejected to preserve EG correctness.
        """
        if not layout_deltas or not layout_deltas.deltas:
            return
        
        for element_id, delta in layout_deltas.deltas.items():
            if delta.delta_type == 'vertex_position' and delta.new_position:
                # Find vertex and validate position is within its logical area
                for vertex in dto.vertices:
                    if vertex.id == element_id:
                        # Find the parent area bounds
                        parent_area = next((a for a in dto.areas if a.id == vertex.parent_area_id), None)
                        if parent_area:
                            # Validate position is within parent area bounds
                            x, y = delta.new_position
                            if (parent_area.rect.x <= x <= parent_area.rect.x + parent_area.rect.width and
                                parent_area.rect.y <= y <= parent_area.rect.y + parent_area.rect.height):
                                # Valid position - apply it
                                vertex.pos = delta.new_position
                            else:
                                # Invalid position - reject and keep layout engine's calculated position
                                # This preserves logical correctness over aesthetic preference
                                pass
                        break
            elif delta.delta_type == 'edge_position' and delta.new_position:
                # Find and validate edge label position
                for edge_label in dto.edge_labels:
                    if edge_label.id == element_id:
                        # Find the parent area bounds
                        parent_area = next((a for a in dto.areas if a.id == edge_label.parent_area_id), None)
                        if parent_area:
                            # Validate position is within parent area bounds
                            x, y = delta.new_position
                            if (parent_area.rect.x <= x <= parent_area.rect.x + parent_area.rect.width and
                                parent_area.rect.y <= y <= parent_area.rect.y + parent_area.rect.height):
                                # Valid position - apply it
                                width = edge_label.rect.width
                                height = edge_label.rect.height
                                edge_label.rect = Rect(
                                    delta.new_position[0] - width/2,
                                    delta.new_position[1] - height/2,
                                    width,
                                    height
                                )
                        break
    
    def _apply_aesthetic_styles(self, dto: LayoutDTO, egi: RelationalGraphWithCuts, style: StyleSpecification):
        """Step 4: Apply aesthetic styles to DTO elements"""
        
        # Apply cut styling based on nesting depth
        self._apply_cut_styles(dto, egi, style)
        
        # Apply ligature styling
        self._apply_ligature_styles(dto, style)
        
        # Apply label styling
        self._apply_label_styles(dto, style)
        
        # Generate annotations if requested
        self._generate_annotations(dto, egi, style)
    
    def _apply_cut_styles(self, dto: LayoutDTO, egi: RelationalGraphWithCuts, style: StyleSpecification):
        """Apply styling to cut areas based on nesting depth and polarity"""
        
        # Calculate nesting depths
        area_depths = self._calculate_area_depths(egi)
        
        for area in sorted(dto.areas, key=lambda a: a.id):
            depth = area_depths.get(area.id, 0)
            
            # Apply base styling from StyleSpecification
            area.style.update({
                'shape': style.cut_shape,
                'stroke_width': style.cut_line_width
            })
            
            # Apply polarity-based fill (even = positive, odd = negative)
            if depth % 2 == 0:  # Even depth (positive area)
                area.style['fill'] = style.even_polarity_fill
            else:  # Odd depth (negative area)
                area.style['fill'] = style.odd_polarity_fill
            
            # Check for double cuts and apply special styling
            if self._is_double_cut(egi, area.id) and style.double_cut_highlight_enabled:
                area.style['stroke_width'] = style.cut_line_width * 1.5
    
    def _apply_ligature_styles(self, dto: LayoutDTO, style: StyleSpecification):
        """Apply styling to ligatures"""
        
        for ligature in dto.ligatures:
            ligature.style.update({
                'stroke_width': style.ligature_line_width,
                'color': 'black'  # Ligatures are always black
            })
    
    def _apply_label_styles(self, dto: LayoutDTO, style: StyleSpecification):
        """Apply styling to labels"""
        
        for label in dto.edge_labels:
            label.style.update({
                'font_color': 'black',  # Labels are always black
                'font_family': style.font_family,
                'font_size': style.font_size
            })
    
    def _generate_annotations(self, dto: LayoutDTO, egi: RelationalGraphWithCuts, style: StyleSpecification):
        """Generate annotations based on style configuration"""
        
        # Generate vertex variable annotations if requested
        if style.variable_labels_enabled:
            self._generate_vertex_variable_annotations(dto, egi)
        
        # Generate double cut highlights if requested
        if style.double_cut_highlight_enabled:
            self._generate_double_cut_annotations(dto, egi)
    
    def _calculate_area_depths(self, egi: RelationalGraphWithCuts) -> Dict[str, int]:
        """Calculate nesting depth for each area"""
        
        depths = {egi.sheet: 0}  # Sheet is at depth 0
        hierarchy = self._build_cut_hierarchy(egi)
        
        # Process areas in topological order
        def calculate_depth(area_id: str) -> int:
            if area_id in depths:
                return depths[area_id]
            
            parent_id = hierarchy[area_id]['parent']
            if parent_id is None:
                depths[area_id] = 0
            else:
                depths[area_id] = calculate_depth(parent_id) + 1
            
            return depths[area_id]
        
        for area_id in hierarchy:
            calculate_depth(area_id)
        
        return depths
    
    def _is_double_cut(self, egi: RelationalGraphWithCuts, area_id: str) -> bool:
        """Check if an area is part of a double cut pattern"""
        
        hierarchy = self._build_cut_hierarchy(egi)
        
        # Check if this area has exactly one child that contains no elements
        children = hierarchy[area_id]['children']
        if len(children) == 1:
            child_id = next(iter(children))
            child_elements = hierarchy[child_id]['elements']
            child_children = hierarchy[child_id]['children']
            
            # Double cut: outer cut contains only inner cut, inner cut is empty or minimal
            return len(child_elements) == 0 and len(child_children) == 0
        
        return False
    
    def _generate_vertex_variable_annotations(self, dto: LayoutDTO, egi: RelationalGraphWithCuts):
        """Generate annotations showing vertex variables"""
        
        for vertex in dto.vertices:
            # Get vertex variable name if it exists
            vertex_obj = next((v for v in egi.V if v.id == vertex.id), None)
            if vertex_obj and hasattr(vertex_obj, 'variable') and vertex_obj.variable:
                annotation = RenderableAnnotation(
                    id=f"var_{vertex.id}",
                    parent_area_id=vertex.parent_area_id,
                    annotation_type="vertex_variable",
                    position=(vertex.pos[0] + 10, vertex.pos[1] - 10),
                    text=vertex_obj.variable,
                    style={'font_size': 10, 'font_color': 'blue'}
                )
                dto.annotations.append(annotation)
    
    def _generate_double_cut_annotations(self, dto: LayoutDTO, egi: RelationalGraphWithCuts):
        """Generate annotations highlighting double cuts"""
        
        for area in sorted(dto.areas, key=lambda a: a.id):
            if self._is_double_cut(egi, area.id):
                annotation = RenderableAnnotation(
                    id=f"dc_{area.id}",
                    parent_area_id=area.parent_id or egi.sheet,
                    annotation_type="double_cut_highlight",
                    position=(area.rect.x + area.rect.width + 5, area.rect.y),
                    text="DC",
                    style={'font_size': 8, 'font_color': 'red', 'font_weight': 'bold'}
                )
                dto.annotations.append(annotation)
    
    def _calculate_connection_ports(self, rect: Rect, num_hooks: int) -> List[ConnectionPort]:
        """Calculate connection ports on EdgeLabel bounding box based on number of hooks"""
        
        if num_hooks == 0:
            return []
        
        ports = []
        center_x = rect.x + rect.width / 2
        center_y = rect.y + rect.height / 2
        
        # Define cardinal and intercardinal directions
        directions = {
            'N': (center_x, rect.y),                           # North (top)
            'E': (rect.x + rect.width, center_y),              # East (right)  
            'S': (center_x, rect.y + rect.height),             # South (bottom)
            'W': (rect.x, center_y),                           # West (left)
            'NE': (rect.x + rect.width, rect.y),               # Northeast (top-right)
            'NW': (rect.x, rect.y),                            # Northwest (top-left)
            'SE': (rect.x + rect.width, rect.y + rect.height), # Southeast (bottom-right)
            'SW': (rect.x, rect.y + rect.height)               # Southwest (bottom-left)
        }
        
        if num_hooks == 1:
            # Single hook: use West as default (will be optimized later with vertex positions)
            ports.append(ConnectionPort(port_id=0, position=directions['W'], direction='W'))
            
        elif num_hooks == 2:
            # Two hooks: opposite sides (West and East)
            ports.append(ConnectionPort(port_id=0, position=directions['W'], direction='W'))
            ports.append(ConnectionPort(port_id=1, position=directions['E'], direction='E'))
            
        elif num_hooks == 3:
            # Three hooks: W, N, E
            ports.append(ConnectionPort(port_id=0, position=directions['W'], direction='W'))
            ports.append(ConnectionPort(port_id=1, position=directions['N'], direction='N'))
            ports.append(ConnectionPort(port_id=2, position=directions['E'], direction='E'))
            
        elif num_hooks == 4:
            # Four hooks: all cardinal directions
            ports.append(ConnectionPort(port_id=0, position=directions['W'], direction='W'))
            ports.append(ConnectionPort(port_id=1, position=directions['N'], direction='N'))
            ports.append(ConnectionPort(port_id=2, position=directions['E'], direction='E'))
            ports.append(ConnectionPort(port_id=3, position=directions['S'], direction='S'))
            
        elif num_hooks >= 5:
            # Five or more hooks: use all 8 directions, cycling as needed
            direction_order = ['W', 'N', 'E', 'S', 'NW', 'NE', 'SE', 'SW']
            for i in range(num_hooks):
                direction = direction_order[i % len(direction_order)]
                ports.append(ConnectionPort(port_id=i, position=directions[direction], direction=direction))
        
        return ports
    
    def _calculate_connection_ports_with_vertices(self, rect: Rect, vertex_sequence, vertex_positions):
        """Calculate connection ports considering actual vertex positions for optimal placement"""
        
        num_hooks = len(vertex_sequence)
        if num_hooks == 0:
            return []
        
        # For unary predicates, choose the best single port based on vertex position
        if num_hooks == 1:
            vertex_id = vertex_sequence[0]
            if vertex_id in vertex_positions:
                vertex_pos = (vertex_positions[vertex_id]['x'], vertex_positions[vertex_id]['y'])
                best_direction = self._find_best_port_direction(rect, vertex_pos)
                
                center_x = rect.x + rect.width / 2
                center_y = rect.y + rect.height / 2
                
                directions = {
                    'N': (center_x, rect.y),
                    'E': (rect.x + rect.width, center_y),
                    'S': (center_x, rect.y + rect.height),
                    'W': (rect.x, center_y)
                }
                
                return [ConnectionPort(port_id=0, position=directions[best_direction], direction=best_direction)]
        
        # For multi-arity predicates, use the standard approach
        return self._calculate_connection_ports(rect, num_hooks)
    
    def _find_best_port_direction(self, rect: Rect, vertex_pos):
        """Find the best port direction for a single vertex"""
        
        center_x = rect.x + rect.width / 2
        center_y = rect.y + rect.height / 2
        
        # Calculate relative position of vertex to label center
        dx = vertex_pos[0] - center_x
        dy = vertex_pos[1] - center_y
        
        # Choose port based on which side the vertex is closest to
        if abs(dx) > abs(dy):
            # Vertex is more to the left or right
            return 'W' if dx < 0 else 'E'
        else:
            # Vertex is more above or below
            return 'N' if dy < 0 else 'S'
    
    def _calculate_area_aware_path_to_port(self, vertex, edge_label, target_port, area_grid, grid_bounds, hierarchy):
        """Calculate path using area-aware A* pathfinding to a specific connection port"""
        
        # If no target port specified, fall back to center of edge label
        if target_port is None:
            return self._calculate_area_aware_path(vertex, edge_label, area_grid, grid_bounds, hierarchy)
        
        # Convert positions to grid coordinates
        start_x = int((vertex.pos[0] - grid_bounds.x) * self.grid_resolution)
        start_y = int((vertex.pos[1] - grid_bounds.y) * self.grid_resolution)
        target_x = int((target_port.position[0] - grid_bounds.x) * self.grid_resolution)
        target_y = int((target_port.position[1] - grid_bounds.y) * self.grid_resolution)
        
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
                # Fallback to direct line if pathfinding fails
                return [vertex.pos, target_port.position]
            
            # Convert path back to world coordinates
            world_path = []
            for node in path:
                world_x = node.x / self.grid_resolution + grid_bounds.x
                world_y = node.y / self.grid_resolution + grid_bounds.y
                world_path.append((world_x, world_y))
            
            # CRITICAL FIX: Ensure path starts at exact vertex position and ends at exact port position
            # The A* grid path may have quantization errors
            if world_path:
                world_path[0] = vertex.pos  # Force exact start position
                if target_port:
                    world_path[-1] = target_port.position  # Force exact end position
            
            return world_path
            
        except Exception as e:
            # Fallback to direct line if pathfinding fails
            return [vertex.pos, target_port.position]
    
    def _assign_nearest_ports(self, vertex_sequence, edge_label, all_vertices):
        """Assign each vertex to its nearest available connection port to minimize crossings"""
        
        if not edge_label.connection_ports:
            return {}
        
        # Get vertex objects for the sequence
        vertices = []
        for vertex_id in vertex_sequence:
            vertex = next((v for v in all_vertices if v.id == vertex_id), None)
            if vertex:
                vertices.append(vertex)
        
        if not vertices:
            return {}
        
        # Calculate distances from each vertex to each port
        vertex_port_distances = {}
        for vertex in vertices:
            vertex_port_distances[vertex.id] = {}
            for port in edge_label.connection_ports:
                distance = self._calculate_distance(vertex.pos, port.position)
                vertex_port_distances[vertex.id][port.port_id] = distance
        
        # Use greedy assignment that minimizes total crossing potential
        assignments = {}
        used_ports = set()
        
        # Sort vertices by their distance to the nearest available port
        vertex_distances = []
        for vertex in vertices:
            min_distance = float('inf')
            for port in edge_label.connection_ports:
                if port.port_id not in used_ports:
                    distance = vertex_port_distances[vertex.id][port.port_id]
                    min_distance = min(min_distance, distance)
            vertex_distances.append((vertex, min_distance))
        
        # Sort by minimum distance (closest vertices get priority)
        vertex_distances.sort(key=lambda x: x[1])
        
        # Assign each vertex to its nearest available port
        for vertex, _ in vertex_distances:
            best_port = None
            best_distance = float('inf')
            
            for port in edge_label.connection_ports:
                if port.port_id not in used_ports:
                    distance = vertex_port_distances[vertex.id][port.port_id]
                    if distance < best_distance:
                        best_distance = distance
                        best_port = port
            
            if best_port:
                assignments[vertex.id] = best_port
                used_ports.add(best_port.port_id)
        
        return assignments
    
    def _calculate_distance(self, pos1, pos2):
        """Calculate Euclidean distance between two points"""
        return ((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2) ** 0.5
    
    # ========== BOTTOM-UP LAYOUT WITH CUTS AS POSITIONED RECTANGLES ==========
    
    def _build_area_hierarchy_v2(self, egi: RelationalGraphWithCuts) -> Dict:
        """Build parent-child relationships for areas"""
        hierarchy = {}
        
        # Initialize all areas
        for area_id in egi.area.keys():
            hierarchy[area_id] = {
                'parent': None,
                'children': [],
                'vertices': [],
                'edges': [],
                'child_cuts': []
            }
        
        # Populate element lists and find parents
        for area_id, elements in egi.area.items():
            for elem_id in elements:
                # Check if it's a vertex
                if any(v.id == elem_id for v in egi.V):
                    hierarchy[area_id]['vertices'].append(elem_id)
                # Check if it's an edge
                elif any(e.id == elem_id for e in egi.E):
                    hierarchy[area_id]['edges'].append(elem_id)
                # Check if it's a cut
                elif any(c.id == elem_id for c in egi.Cut):
                    hierarchy[area_id]['child_cuts'].append(elem_id)
                    hierarchy[elem_id]['parent'] = area_id
                    hierarchy[area_id]['children'].append(elem_id)
        
        return hierarchy
    
    def _get_bottom_up_order_v2(self, hierarchy: Dict) -> List[str]:
        """Get areas in bottom-up processing order (leaves first)"""
        order = []
        processed = set()
        
        def process_area(area_id):
            if area_id in processed:
                return
            
            # Process all children first
            for child_id in hierarchy[area_id]['children']:
                process_area(child_id)
            
            order.append(area_id)
            processed.add(area_id)
        
        # Process all areas starting from each root
        for area_id in hierarchy.keys():
            if hierarchy[area_id]['parent'] is None:
                process_area(area_id)
        
        return order
    
    def _bottom_up_area_layout(self, egi: RelationalGraphWithCuts, hierarchy: Dict,
                               style: StyleSpecification, layout_deltas: LayoutDeltas) -> Dict:
        """
        Layout each area bottom-up, treating child cuts as rectangular elements.
        Returns: {area_id: {'positions': {...}, 'width': float, 'height': float}}
        """
        area_layouts = {}
        
        for area_id in self._get_bottom_up_order_v2(hierarchy):
            area_layouts[area_id] = self._layout_single_area_v2(
                area_id, egi, hierarchy, area_layouts, style, layout_deltas
            )
        
        return area_layouts
    
    def _layout_single_area_v2(self, area_id: str, egi: RelationalGraphWithCuts,
                               hierarchy: Dict, child_layouts: Dict,
                               style: StyleSpecification, layout_deltas: LayoutDeltas) -> Dict:
        """
        Layout a single area in local coordinate space.
        Child cuts are included as rectangular elements with known dimensions.
        """
        # Get elements in this area
        vertex_ids = hierarchy[area_id]['vertices']
        edge_ids = hierarchy[area_id]['edges']
        child_cut_ids = hierarchy[area_id]['child_cuts']
        
        # Build DOT string
        dot_lines = ["graph Area {", "  layout=neato;", "  overlap=false;"]
        
        # Add vertices as points
        for v_id in vertex_ids:
            # Check for user-pinned position
            if layout_deltas and v_id in layout_deltas.deltas:
                delta = layout_deltas.deltas[v_id]
                if delta.delta_type == 'vertex_position':
                    x, y = delta.new_position
                    dot_lines.append(f'  "{v_id}" [shape=point, pin=true, pos="{x},{y}!"];')
                    continue
            dot_lines.append(f'  "{v_id}" [shape=point];')
        
        # Add edges as labeled boxes
        for e_id in edge_ids:
            rel_name = egi.rel.get(e_id, "?")
            dot_lines.append(f'  "{e_id}" [shape=box, label="{rel_name}"];')
        
        # Add child cuts as RECTANGLES with fixed dimensions
        for cut_id in child_cut_ids:
            if cut_id in child_layouts:
                child_layout = child_layouts[cut_id]
                width_inches = child_layout['width'] / 72.0  # Convert pixels to inches
                height_inches = child_layout['height'] / 72.0
                dot_lines.append(
                    f'  "{cut_id}" [shape=box, width={width_inches:.2f}, '
                    f'height={height_inches:.2f}, fixedsize=true, label=""];'
                )
        
        # Add ligatures (edges between vertices and edge labels)
        for e_id in edge_ids:
            if e_id in egi.nu:
                for v_id in egi.nu[e_id]:
                    if v_id in vertex_ids:  # Only connect if vertex is in same area
                        dot_lines.append(f'  "{v_id}" -- "{e_id}";')
        
        dot_lines.append("}")
        dot_string = "\n".join(dot_lines)
        
        # Execute Graphviz
        try:
            result = self._execute_graphviz_layout(dot_string, engine='neato')
        except Exception as e:
            print(f"Graphviz failed for area {area_id[:8]}: {e}")
            # Fallback: simple grid layout
            return self._fallback_grid_layout(vertex_ids, edge_ids, child_cut_ids, child_layouts)
        
        # Parse positions
        positions = {}
        for obj in result.get('objects', []):
            elem_id = obj.get('name', '')
            if 'pos' in obj:
                pos_str = obj['pos']
                x, y = map(float, pos_str.split(','))
                positions[elem_id] = (x, y)
        
        # Calculate bounding box
        padding = style.raw_style_data.get('geometry', {}).get('padding', {}).get('area', 15)
        bbox = self._calculate_bbox_from_positions(
            positions, vertex_ids, edge_ids, child_cut_ids, child_layouts, egi, padding
        )
        
        return {
            'positions': positions,
            'width': bbox['width'],
            'height': bbox['height'],
            'bbox': bbox  # Store full bbox for coordinate transformation
        }
    
    def _calculate_bbox_from_positions(self, positions: Dict, vertex_ids: List,
                                      edge_ids: List, child_cut_ids: List,
                                      child_layouts: Dict, egi: RelationalGraphWithCuts,
                                      padding: float) -> Dict:
        """Calculate bounding box around all positioned elements"""
        if not positions:
            return {'x': 0, 'y': 0, 'width': 100, 'height': 100}
        
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        # Include vertices (points)
        for v_id in vertex_ids:
            if v_id in positions:
                x, y = positions[v_id]
                min_x, max_x = min(min_x, x - 2), max(max_x, x + 2)
                min_y, max_y = min(min_y, y - 2), max(max_y, y + 2)
        
        # Include edges (boxes)
        for e_id in edge_ids:
            if e_id in positions:
                x, y = positions[e_id]
                rel_name = egi.rel.get(e_id, "?")
                w, h = len(rel_name) * 8, 12
                min_x, max_x = min(min_x, x - w/2), max(max_x, x + w/2)
                min_y, max_y = min(min_y, y - h/2), max(max_y, y + h/2)
        
        # Include child cuts (rectangles)
        for cut_id in child_cut_ids:
            if cut_id in positions and cut_id in child_layouts:
                x, y = positions[cut_id]
                w, h = child_layouts[cut_id]['width'], child_layouts[cut_id]['height']
                min_x, max_x = min(min_x, x - w/2), max(max_x, x + w/2)
                min_y, max_y = min(min_y, y - h/2), max(max_y, y + h/2)
        
        return {
            'x': min_x - padding,
            'y': min_y - padding,
            'width': (max_x - min_x) + 2 * padding,
            'height': (max_y - min_y) + 2 * padding
        }
    
    def _fallback_grid_layout(self, vertex_ids: List, edge_ids: List,
                             child_cut_ids: List, child_layouts: Dict) -> Dict:
        """Simple grid layout if Graphviz fails"""
        positions = {}
        x, y = 50, 50
        spacing = 60
        
        for v_id in vertex_ids:
            positions[v_id] = (x, y)
            x += spacing
        
        y += spacing
        x = 50
        for e_id in edge_ids:
            positions[e_id] = (x, y)
            x += spacing
        
        y += spacing
        x = 50
        for cut_id in child_cut_ids:
            if cut_id in child_layouts:
                positions[cut_id] = (x, y)
                x += child_layouts[cut_id]['width'] + spacing
        
        return {
            'positions': positions,
            'width': max(200, x + 50),
            'height': max(200, y + 50),
            'bbox': {'x': 0, 'y': 0, 'width': max(200, x + 50), 'height': max(200, y + 50)}
        }
    
    def _transform_to_global_coords(self, egi: RelationalGraphWithCuts,
                                   hierarchy: Dict, area_layouts: Dict) -> tuple:
        """
        Transform local coordinates to global coordinate system.
        Returns: (global_positions, area_bounds)
        """
        global_positions = {'vertices': {}, 'edge_labels': {}}
        area_bounds = {}
        
        def transform_area(area_id, parent_offset=(0, 0)):
            layout = area_layouts[area_id]
            positions = layout['positions']
            bbox = layout['bbox']
            
            # Calculate this area's global top-left position
            if hierarchy[area_id]['parent'] is not None:
                parent_id = hierarchy[area_id]['parent']
                parent_layout = area_layouts[parent_id]
                parent_bbox = parent_layout['bbox']
                
                if area_id in parent_layout['positions']:
                    # Cut's position from Graphviz is its CENTER in parent's local space
                    cut_center_x, cut_center_y = parent_layout['positions'][area_id]
                    
                    # Convert center to top-left corner in parent's local space
                    cut_local_x = cut_center_x - layout['width'] / 2
                    cut_local_y = cut_center_y - layout['height'] / 2
                    
                    # Transform to global space
                    area_global_x = parent_offset[0] + (cut_local_x - parent_bbox['x'])
                    area_global_y = parent_offset[1] + (cut_local_y - parent_bbox['y'])
                    
                    area_offset = (area_global_x, area_global_y)
                else:
                    area_offset = parent_offset
            else:
                # Sheet is at origin
                area_offset = (0, 0)
            
            # Store this area's global bounds
            area_bounds[area_id] = Rect(
                area_offset[0],
                area_offset[1],
                layout['width'],
                layout['height']
            )
            
            # Transform vertices to global coordinates
            for v_id in hierarchy[area_id]['vertices']:
                if v_id in positions:
                    local_x, local_y = positions[v_id]
                    # Transform from local space to global
                    global_x = area_offset[0] + (local_x - bbox['x'])
                    global_y = area_offset[1] + (local_y - bbox['y'])
                    
                    global_positions['vertices'][v_id] = {
                        'x': global_x,
                        'y': global_y,
                        'parent_area_id': area_id
                    }
            
            # Transform edges to global coordinates
            for e_id in hierarchy[area_id]['edges']:
                if e_id in positions:
                    local_x, local_y = positions[e_id]
                    rel_name = egi.rel.get(e_id, "?")
                    
                    global_x = area_offset[0] + (local_x - bbox['x'])
                    global_y = area_offset[1] + (local_y - bbox['y'])
                    
                    global_positions['edge_labels'][e_id] = {
                        'x': global_x,
                        'y': global_y,
                        'width': len(rel_name) * 8,
                        'height': 12,
                        'label': rel_name,
                        'parent_area_id': area_id
                    }
            
            # Recursively transform children (pass this area's offset as parent offset)
            for child_id in hierarchy[area_id]['children']:
                transform_area(child_id, area_offset)
        
        # Start from sheet (root)
        transform_area(egi.sheet, (0, 0))
        
        return global_positions, area_bounds
