"""
Abstract Layout Unit (ALU) Engine for Existential Graph Instances

This engine follows Dau's formalization exactly, producing geometric layout data
for GUI rendering. The engine implements the 4-step process:
1. Build Spatial Hierarchy
2. Bottom-Up Layout Calculation  
3. Ligature Path Routing
4. Absolute Coordinate Finalization
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict, deque

from egi_core_dau import RelationalGraphWithCuts, ElementID, Vertex, Edge, Cut
from style_loader import StyleSpecification


@dataclass
class Point:
    """2D point for geometric calculations"""
    x: float
    y: float
    
    def __add__(self, other: 'Point') -> 'Point':
        return Point(self.x + other.x, self.y + other.y)
    
    def distance_to(self, other: 'Point') -> float:
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)


@dataclass
class Area:
    """ALU primitive: Spatial area (cut or sheet)"""
    id: ElementID
    parent_id: Optional[ElementID]
    x: float
    y: float
    width: float
    height: float
    type: str  # 'cut' or 'sheet'


@dataclass
class VertexALU:
    """ALU primitive: Vertex with geometric properties"""
    id: ElementID
    parent_area_id: ElementID
    x: float
    y: float
    radius: float


@dataclass
class EdgeLabel:
    """ALU primitive: Edge label with geometric properties"""
    id: ElementID
    parent_area_id: ElementID
    text: str
    x: float
    y: float
    width: float
    height: float


@dataclass
class Ligature:
    """ALU primitive: Connection path between vertex and edge"""
    id: str  # Unique identifier for this ligature
    start_vertex_id: ElementID
    end_edge_id: ElementID
    end_hook_index: int  # Which hook on the edge (0-based)
    path: List[Point]  # Ordered points defining the path


@dataclass
class AbstractLayoutUnit:
    """Complete ALU containing all geometric primitives"""
    areas: List[Area]
    vertices: List[VertexALU]
    edge_labels: List[EdgeLabel]
    ligatures: List[Ligature]
    total_width: float
    total_height: float


class SpatialHierarchyBuilder:
    """Step 1: Build spatial hierarchy tree from EGI area mapping"""
    
    def __init__(self, egi: RelationalGraphWithCuts):
        self.egi = egi
        
    def build_hierarchy(self) -> Dict[ElementID, Dict[str, Any]]:
        """Build tree representing nesting hierarchy of contexts"""
        
        # Initialize hierarchy structure
        hierarchy = {}
        
        # Add sheet (root)
        sheet_contents = self.egi.area.get(self.egi.sheet, frozenset())
        hierarchy[self.egi.sheet] = {
            'parent': None,
            'children': set(),
            'direct_vertices': set(),
            'direct_edges': set(),
            'type': 'sheet'
        }
        
        # Add all cuts
        for cut in self.egi.Cut:
            cut_contents = self.egi.area.get(cut.id, frozenset())
            hierarchy[cut.id] = {
                'parent': None,  # Will be determined
                'children': set(),
                'direct_vertices': set(),
                'direct_edges': set(),
                'type': 'cut'
            }
        
        # Determine parent-child relationships and direct contents
        all_contexts = {self.egi.sheet} | {cut.id for cut in self.egi.Cut}
        
        for context_id in all_contexts:
            contents = self.egi.area.get(context_id, frozenset())
            
            for element_id in contents:
                # Check if element is a context (cut)
                if element_id in all_contexts and element_id != context_id:
                    # This is a child context
                    hierarchy[element_id]['parent'] = context_id
                    hierarchy[context_id]['children'].add(element_id)
                else:
                    # This is a vertex or edge
                    if any(v.id == element_id for v in self.egi.V):
                        hierarchy[context_id]['direct_vertices'].add(element_id)
                    elif any(e.id == element_id for e in self.egi.E):
                        hierarchy[context_id]['direct_edges'].add(element_id)
        
        return hierarchy


class BottomUpLayoutCalculator:
    """Step 2: Calculate layout using bottom-up approach"""
    
    def __init__(self, egi: RelationalGraphWithCuts, hierarchy: Dict[ElementID, Dict[str, Any]], 
                 style: StyleSpecification):
        self.egi = egi
        self.hierarchy = hierarchy
        self.style = style
        self.area_layouts = {}  # context_id -> layout info
        
    def calculate_layouts(self) -> Dict[ElementID, Dict[str, Any]]:
        """Perform bottom-up layout calculation"""
        
        # Get contexts sorted by depth (deepest first)
        contexts_by_depth = self._get_contexts_by_depth()
        
        # Process contexts from leaves to root
        for depth_contexts in reversed(contexts_by_depth):
            for context_id in depth_contexts:
                self._layout_context(context_id)
        
        return self.area_layouts
    
    def _get_contexts_by_depth(self) -> List[List[ElementID]]:
        """Get contexts grouped by depth (0 = sheet, 1 = direct children, etc.)"""
        depths = defaultdict(list)
        
        # BFS to assign depths
        queue = deque([(self.egi.sheet, 0)])
        visited = {self.egi.sheet}
        
        while queue:
            context_id, depth = queue.popleft()
            depths[depth].append(context_id)
            
            for child_id in self.hierarchy[context_id]['children']:
                if child_id not in visited:
                    visited.add(child_id)
                    queue.append((child_id, depth + 1))
        
        return [depths[d] for d in sorted(depths.keys())]
    
    def _layout_context(self, context_id: ElementID):
        """Layout a single context (area)"""
        
        context_info = self.hierarchy[context_id]
        
        # Get direct elements
        vertices = list(context_info['direct_vertices'])
        edges = list(context_info['direct_edges'])
        child_areas = list(context_info['children'])
        
        # Layout atomic elements (vertices and edges)
        element_positions = self._layout_atomic_elements(vertices, edges)
        
        # Get child area dimensions and add positioning info
        child_area_layouts = []
        for child_id in child_areas:
            if child_id in self.area_layouts:
                child_layout = self.area_layouts[child_id].copy()
                child_layout['id'] = child_id
                child_layout['x'] = 0  # Will be positioned later
                child_layout['y'] = 0  # Will be positioned later
                child_area_layouts.append(child_layout)
        
        # Arrange all elements (atomic + child areas)
        area_layout = self._arrange_elements(
            element_positions, child_area_layouts, context_info['type']
        )
        
        self.area_layouts[context_id] = area_layout
    
    def _layout_atomic_elements(self, vertices: List[ElementID], edges: List[ElementID]) -> Dict[ElementID, Dict[str, Any]]:
        """Layout vertices and edges in a non-overlapping arrangement"""
        
        positions = {}
        all_elements = vertices + edges
        
        if not all_elements:
            return positions
        
        # Simple grid arrangement
        element_spacing = self.style.element_spacing
        element_size = max(self.style.vertex_radius * 4, self.style.predicate_height)
        
        # Calculate grid dimensions
        count = len(all_elements)
        cols = math.ceil(math.sqrt(count))
        rows = math.ceil(count / cols)
        
        # Position elements
        for i, element_id in enumerate(all_elements):
            row = i // cols
            col = i % cols
            
            x = col * (element_size + element_spacing) + element_size / 2
            y = row * (element_size + element_spacing) + element_size / 2
            
            if element_id in vertices:
                positions[element_id] = {
                    'type': 'vertex',
                    'x': x,
                    'y': y,
                    'radius': self.style.vertex_radius
                }
            else:  # edge
                relation_name = self.egi.rel.get(element_id, "?")
                text_width = len(relation_name) * self.style.predicate_char_width
                positions[element_id] = {
                    'type': 'edge',
                    'x': x,
                    'y': y,
                    'text': relation_name,
                    'width': text_width,
                    'height': self.style.predicate_height
                }
        
        return positions
    
    def _arrange_elements(self, element_positions: Dict[ElementID, Dict[str, Any]], 
                         child_areas: List[Dict[str, Any]], area_type: str) -> Dict[str, Any]:
        """Arrange atomic elements and child areas within this area"""
        
        padding = self.style.cut_padding
        
        # Calculate bounding box for atomic elements
        element_bounds = self._calculate_element_bounds(element_positions)
        
        # Calculate bounding box for child areas
        child_bounds = self._calculate_child_area_bounds(child_areas)
        
        # Combine bounds
        if element_bounds and child_bounds:
            # Arrange side by side
            total_width = element_bounds['width'] + child_bounds['width'] + padding
            total_height = max(element_bounds['height'], child_bounds['height'])
            
            # Adjust child area positions
            offset_x = element_bounds['width'] + padding
            for child in child_areas:
                child['x'] += offset_x
                
        elif element_bounds:
            total_width = element_bounds['width']
            total_height = element_bounds['height']
        elif child_bounds:
            total_width = child_bounds['width']
            total_height = child_bounds['height']
        else:
            # Empty area
            total_width = 100
            total_height = 100
        
        # Add padding
        total_width += 2 * padding
        total_height += 2 * padding
        
        # Adjust element positions for padding
        for element_info in element_positions.values():
            element_info['x'] += padding
            element_info['y'] += padding
        
        for child in child_areas:
            child['x'] += padding
            child['y'] += padding
        
        return {
            'width': total_width,
            'height': total_height,
            'element_positions': element_positions,
            'child_areas': child_areas,
            'type': area_type
        }
    
    def _calculate_element_bounds(self, element_positions: Dict[ElementID, Dict[str, Any]]) -> Optional[Dict[str, float]]:
        """Calculate bounding box for atomic elements"""
        
        if not element_positions:
            return None
        
        positions = list(element_positions.values())
        min_x = min(pos['x'] - (pos.get('width', pos.get('radius', 0)) / 2) for pos in positions)
        max_x = max(pos['x'] + (pos.get('width', pos.get('radius', 0)) / 2) for pos in positions)
        min_y = min(pos['y'] - (pos.get('height', pos.get('radius', 0)) / 2) for pos in positions)
        max_y = max(pos['y'] + (pos.get('height', pos.get('radius', 0)) / 2) for pos in positions)
        
        return {
            'width': max_x - min_x,
            'height': max_y - min_y
        }
    
    def _calculate_child_area_bounds(self, child_areas: List[Dict[str, Any]]) -> Optional[Dict[str, float]]:
        """Calculate bounding box for child areas"""
        
        if not child_areas:
            return None
        
        min_x = min(child['x'] for child in child_areas)
        max_x = max(child['x'] + child['width'] for child in child_areas)
        min_y = min(child['y'] for child in child_areas)
        max_y = max(child['y'] + child['height'] for child in child_areas)
        
        return {
            'width': max_x - min_x,
            'height': max_y - min_y
        }


class LigaturePathRouter:
    """Step 3: Calculate ligature paths with proper routing"""
    
    def __init__(self, egi: RelationalGraphWithCuts, area_layouts: Dict[ElementID, Dict[str, Any]]):
        self.egi = egi
        self.area_layouts = area_layouts
        
    def route_ligatures(self) -> List[Ligature]:
        """Calculate all ligature paths"""
        
        ligatures = []
        
        # Process each edge and its connections
        for edge_id, vertex_sequence in self.egi.nu.items():
            if not vertex_sequence:
                continue
                
            # Find edge position
            edge_pos = self._find_element_position(edge_id)
            if not edge_pos:
                continue
            
            # Create ligature to each connected vertex
            for hook_index, vertex_id in enumerate(vertex_sequence):
                vertex_pos = self._find_element_position(vertex_id)
                if not vertex_pos:
                    continue
                
                # Calculate path
                path = self._calculate_ligature_path(
                    vertex_pos, edge_pos, vertex_id, edge_id
                )
                
                ligature = Ligature(
                    id=f"{edge_id}_{vertex_id}_{hook_index}",
                    start_vertex_id=vertex_id,
                    end_edge_id=edge_id,
                    end_hook_index=hook_index,
                    path=path
                )
                ligatures.append(ligature)
        
        return ligatures
    
    def _find_element_position(self, element_id: ElementID) -> Optional[Dict[str, Any]]:
        """Find the position of an element in the layout"""
        
        for area_id, area_layout in self.area_layouts.items():
            element_positions = area_layout.get('element_positions', {})
            if element_id in element_positions:
                pos = element_positions[element_id].copy()
                pos['area_id'] = area_id
                return pos
        
        return None
    
    def _calculate_ligature_path(self, vertex_pos: Dict[str, Any], edge_pos: Dict[str, Any],
                               vertex_id: ElementID, edge_id: ElementID) -> List[Point]:
        """Calculate path between vertex and edge"""
        
        # For now, simple straight line
        # TODO: Implement proper routing with cut crossing rules
        
        start_point = Point(vertex_pos['x'], vertex_pos['y'])
        end_point = Point(edge_pos['x'], edge_pos['y'])
        
        return [start_point, end_point]


class AbsoluteCoordinateFinalizer:
    """Step 4: Convert relative coordinates to absolute coordinates"""
    
    def __init__(self, egi: RelationalGraphWithCuts, hierarchy: Dict[ElementID, Dict[str, Any]], 
                 area_layouts: Dict[ElementID, Dict[str, Any]]):
        self.egi = egi
        self.hierarchy = hierarchy
        self.area_layouts = area_layouts
        
    def finalize_coordinates(self) -> AbstractLayoutUnit:
        """Convert all coordinates to absolute and create final ALU"""
        
        # Calculate absolute positions for all areas
        area_absolute_positions = self._calculate_absolute_area_positions()
        
        # Create ALU primitives
        areas = []
        vertices = []
        edge_labels = []
        
        for area_id, area_layout in self.area_layouts.items():
            abs_pos = area_absolute_positions[area_id]
            
            # Create Area primitive
            area_type = 'sheet' if area_id == self.egi.sheet else 'cut'
            parent_id = self.hierarchy[area_id]['parent']
            
            area = Area(
                id=area_id,
                parent_id=parent_id,
                x=abs_pos['x'],
                y=abs_pos['y'],
                width=area_layout['width'],
                height=area_layout['height'],
                type=area_type
            )
            areas.append(area)
            
            # Create element primitives
            element_positions = area_layout.get('element_positions', {})
            for element_id, element_info in element_positions.items():
                abs_x = abs_pos['x'] + element_info['x']
                abs_y = abs_pos['y'] + element_info['y']
                
                if element_info['type'] == 'vertex':
                    vertex = VertexALU(
                        id=element_id,
                        parent_area_id=area_id,
                        x=abs_x,
                        y=abs_y,
                        radius=element_info['radius']
                    )
                    vertices.append(vertex)
                else:  # edge
                    edge_label = EdgeLabel(
                        id=element_id,
                        parent_area_id=area_id,
                        text=element_info['text'],
                        x=abs_x,
                        y=abs_y,
                        width=element_info['width'],
                        height=element_info['height']
                    )
                    edge_labels.append(edge_label)
        
        # Route ligatures (will be updated with absolute coordinates)
        router = LigaturePathRouter(self.egi, self.area_layouts)
        ligatures = router.route_ligatures()
        
        # Update ligature paths to absolute coordinates
        self._update_ligature_absolute_coordinates(ligatures, area_absolute_positions)
        
        # Calculate total dimensions
        sheet_layout = self.area_layouts[self.egi.sheet]
        total_width = sheet_layout['width']
        total_height = sheet_layout['height']
        
        return AbstractLayoutUnit(
            areas=areas,
            vertices=vertices,
            edge_labels=edge_labels,
            ligatures=ligatures,
            total_width=total_width,
            total_height=total_height
        )
    
    def _calculate_absolute_area_positions(self) -> Dict[ElementID, Dict[str, float]]:
        """Calculate absolute positions for all areas"""
        
        positions = {}
        
        # Start with sheet at origin
        positions[self.egi.sheet] = {'x': 0, 'y': 0}
        
        # BFS to calculate positions
        queue = deque([self.egi.sheet])
        
        while queue:
            current_id = queue.popleft()
            current_pos = positions[current_id]
            current_layout = self.area_layouts[current_id]
            
            # Position child areas
            for child_area in current_layout.get('child_areas', []):
                child_id = child_area['id'] if 'id' in child_area else None
                if child_id and child_id not in positions:
                    positions[child_id] = {
                        'x': current_pos['x'] + child_area['x'],
                        'y': current_pos['y'] + child_area['y']
                    }
                    queue.append(child_id)
        
        return positions
    
    def _update_ligature_absolute_coordinates(self, ligatures: List[Ligature], 
                                            area_positions: Dict[ElementID, Dict[str, float]]):
        """Update ligature paths to use absolute coordinates"""
        
        for ligature in ligatures:
            # Find the areas containing the vertex and edge
            vertex_area = None
            edge_area = None
            
            for area_id, area_layout in self.area_layouts.items():
                element_positions = area_layout.get('element_positions', {})
                if ligature.start_vertex_id in element_positions:
                    vertex_area = area_id
                if ligature.end_edge_id in element_positions:
                    edge_area = area_id
            
            if vertex_area and edge_area:
                vertex_area_pos = area_positions[vertex_area]
                edge_area_pos = area_positions[edge_area]
                
                # Update path points to absolute coordinates
                updated_path = []
                for i, point in enumerate(ligature.path):
                    if i == 0:  # Start point (vertex)
                        abs_point = Point(
                            vertex_area_pos['x'] + point.x,
                            vertex_area_pos['y'] + point.y
                        )
                    else:  # End point (edge)
                        abs_point = Point(
                            edge_area_pos['x'] + point.x,
                            edge_area_pos['y'] + point.y
                        )
                    updated_path.append(abs_point)
                
                ligature.path = updated_path


class AbstractLayoutEngine:
    """Main engine orchestrating the 4-step ALU generation process"""
    
    def __init__(self, style: StyleSpecification):
        self.style = style
        
    def generate_layout(self, egi: RelationalGraphWithCuts) -> AbstractLayoutUnit:
        """Generate Abstract Layout Unit from EGI"""
        
        # Step 1: Build Spatial Hierarchy
        hierarchy_builder = SpatialHierarchyBuilder(egi)
        hierarchy = hierarchy_builder.build_hierarchy()
        
        # Step 2: Bottom-Up Layout Calculation
        layout_calculator = BottomUpLayoutCalculator(egi, hierarchy, self.style)
        area_layouts = layout_calculator.calculate_layouts()
        
        # Step 3 & 4: Ligature Routing and Absolute Coordinate Finalization
        finalizer = AbsoluteCoordinateFinalizer(egi, hierarchy, area_layouts)
        alu = finalizer.finalize_coordinates()
        
        return alu
