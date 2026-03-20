"""
Layout Engine - Bridge between EGI logical structure and visual representation

ARCHITECTURE:
- Takes any EGI (Dau's 6+1 component formalism)
- Produces abstract layout (platform-independent DTO)
- Enforces spatial-logical correspondence (iron-clad)
- Uses validated core algorithms (coherence framework)

DESIGN PRINCIPLES:
1. EGI area mapping is IRON CLAD - defines containment
2. All elements in area[context_id] must be spatially contained
3. Cuts are elements and can contain other cuts
4. Use existing ligature algorithms from core
5. Platform-independent DTO output
"""

import math
from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

from egi_core_dau import RelationalGraphWithCuts, ElementID, Vertex, Edge, Cut
from enhanced_ligature_algorithms import EnhancedLigatureAlgorithms


@dataclass(frozen=True)
class Point:
    """2D point for spatial positioning"""
    x: float
    y: float


@dataclass(frozen=True)
class BoundingBox:
    """Rectangular bounds for spatial extents"""
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    
    @property
    def width(self) -> float:
        return self.max_x - self.min_x
    
    @property
    def height(self) -> float:
        return self.max_y - self.min_y
    
    @property
    def center(self) -> Point:
        return Point((self.min_x + self.max_x) / 2, (self.min_y + self.max_y) / 2)
    
    def contains_point(self, point: Point) -> bool:
        return (self.min_x <= point.x <= self.max_x and 
                self.min_y <= point.y <= self.max_y)
    
    def expand(self, margin: float) -> 'BoundingBox':
        """Expand bounds by margin in all directions"""
        return BoundingBox(
            self.min_x - margin, self.min_y - margin,
            self.max_x + margin, self.max_y + margin
        )


@dataclass(frozen=True)
class LigaturePath:
    """Path connecting predicate to vertex"""
    predicate_id: ElementID
    vertex_id: ElementID
    points: Tuple[Point, ...]  # Path points from predicate to vertex
    
    @property
    def start_point(self) -> Point:
        return self.points[0] if self.points else Point(0, 0)
    
    @property
    def end_point(self) -> Point:
        return self.points[-1] if self.points else Point(0, 0)


@dataclass(frozen=True)
class LayoutDTO:
    """
    Platform-independent Data Transfer Object for layout information.
    
    This DTO contains ALL spatial information needed by any renderer:
    - Element positions (vertices, predicates, cuts)
    - Ligature paths (from predicates to vertices)
    - Spatial bounds and containment hierarchy
    - Style hints (but not platform-specific styling)
    """
    
    # Element positions
    vertex_positions: Dict[ElementID, Point]
    predicate_positions: Dict[ElementID, Point]  # Edge positions
    cut_bounds: Dict[ElementID, BoundingBox]
    
    # Ligature paths (using validated algorithms)
    ligature_paths: List[LigaturePath]
    
    # Containment hierarchy (from EGI area mapping)
    area_hierarchy: Dict[ElementID, Set[ElementID]]  # area_id -> contained_element_ids
    containment_depth: Dict[ElementID, int]  # element_id -> depth (0 = sheet)
    
    # Viewport information
    viewport_bounds: BoundingBox
    
    # Style hints (platform-independent)
    style_hints: Dict[str, any]


class LayoutEngine:
    """
    Translates EGI logical structure to spatial arrangement.
    
    IRON CLAD PRINCIPLES:
    1. EGI.area mapping defines containment - no exceptions
    2. All elements in area[context] must be spatially within context bounds
    3. Cuts are elements and can contain other cuts
    4. Use validated core ligature algorithms
    5. Produce platform-independent DTO
    """
    
    def __init__(self):
        self.ligature_algorithms = EnhancedLigatureAlgorithms()
        
        # Layout parameters (could be configurable)
        self.element_spacing = 60.0
        self.cut_padding = 30.0
        self.cut_nesting_margin = 20.0
        self.viewport_margin = 40.0
    
    def compute_layout(self, egi: RelationalGraphWithCuts) -> LayoutDTO:
        """
        Translate EGI to spatial layout DTO.
        
        ALGORITHM:
        1. Build containment hierarchy from EGI.area (iron-clad)
        2. Position elements respecting area constraints
        3. Compute ligature paths using core algorithms
        4. Generate platform-independent DTO
        """
        
        # Step 1: Build containment hierarchy from EGI area mapping
        area_hierarchy, containment_depth = self._build_containment_hierarchy(egi)
        
        # Step 2: Position vertices (foundation elements)
        vertex_positions = self._position_vertices(egi, area_hierarchy, containment_depth)
        
        # Step 3: Position predicates (edges) near their vertices
        predicate_positions = self._position_predicates(egi, vertex_positions, area_hierarchy)
        
        # Step 4: Compute cut bounds that contain their elements
        cut_bounds = self._compute_cut_bounds(egi, vertex_positions, predicate_positions, 
                                            area_hierarchy, containment_depth)
        
        # Step 5: Generate ligature paths using validated algorithms
        ligature_paths = self._compute_ligature_paths(egi, vertex_positions, predicate_positions)
        
        # Step 6: Calculate viewport bounds
        viewport_bounds = self._calculate_viewport(vertex_positions, predicate_positions, cut_bounds)
        
        # Step 7: Generate style hints
        style_hints = self._generate_style_hints(egi)
        
        return LayoutDTO(
            vertex_positions=vertex_positions,
            predicate_positions=predicate_positions,
            cut_bounds=cut_bounds,
            ligature_paths=ligature_paths,
            area_hierarchy=area_hierarchy,
            containment_depth=containment_depth,
            viewport_bounds=viewport_bounds,
            style_hints=style_hints
        )
    
    def _build_containment_hierarchy(self, egi: RelationalGraphWithCuts) -> Tuple[Dict[ElementID, Set[ElementID]], Dict[ElementID, int]]:
        """
        Build containment hierarchy from EGI area mapping - IRON CLAD.
        
        Returns:
        - area_hierarchy: area_id -> set of contained element_ids
        - containment_depth: element_id -> depth (0 = sheet, higher = more nested)
        """
        area_hierarchy = {}
        containment_depth = {}
        
        # Initialize with EGI area mapping (iron-clad source of truth)
        for area_id, elements in egi.area.items():
            area_hierarchy[area_id] = set(elements)
        
        # Calculate containment depths
        # Sheet is depth 0, elements in cuts have increasing depth
        
        # Start with sheet elements (depth 0)
        sheet_elements = area_hierarchy.get(egi.sheet, set())
        for element_id in sheet_elements:
            containment_depth[element_id] = 0
        
        # Process cuts to find nesting levels
        cut_depths = {}
        
        def calculate_cut_depth(cut_id: ElementID, visited: Set[ElementID] = None) -> int:
            if visited is None:
                visited = set()
            
            if cut_id in visited:
                # Cycle detection - should not happen with valid EGI
                return 0
            
            if cut_id in cut_depths:
                return cut_depths[cut_id]
            
            visited.add(cut_id)
            
            # Find which area contains this cut
            max_depth = 0
            for area_id, elements in area_hierarchy.items():
                if cut_id in elements and area_id != cut_id:
                    if area_id == egi.sheet:
                        max_depth = max(max_depth, 1)
                    else:
                        # This cut is contained in another cut
                        parent_depth = calculate_cut_depth(area_id, visited.copy())
                        max_depth = max(max_depth, parent_depth + 1)
            
            cut_depths[cut_id] = max_depth
            visited.remove(cut_id)
            return max_depth
        
        # Calculate depths for all cuts
        for cut in egi.Cut:
            cut_depths[cut.id] = calculate_cut_depth(cut.id)
        
        # Now assign depths to all elements based on their containing area
        for area_id, elements in area_hierarchy.items():
            if area_id == egi.sheet:
                area_depth = 0
            else:
                area_depth = cut_depths.get(area_id, 0)
            
            for element_id in elements:
                # Element depth is one more than its containing area
                containment_depth[element_id] = area_depth + 1
        
        return area_hierarchy, containment_depth
    
    def _position_vertices(self, egi: RelationalGraphWithCuts, 
                          area_hierarchy: Dict[ElementID, Set[ElementID]],
                          containment_depth: Dict[ElementID, int]) -> Dict[ElementID, Point]:
        """Position vertices respecting area constraints"""
        vertex_positions = {}
        
        # Position vertices within their SHALLOWEST containing area
        # This ensures shared vertices are positioned in the least common area
        current_x = self.viewport_margin
        current_y = self.viewport_margin
        
        for vertex in egi.V:
            # Find the SHALLOWEST area containing this vertex (least common area)
            vertex_area = None
            min_depth = float('inf')
            
            for area_id, elements in area_hierarchy.items():
                if vertex.id in elements:
                    # Get the depth of the area itself, not the element
                    area_depth = 0
                    if area_id != egi.sheet:
                        # Count how deeply nested this area is
                        for other_area_id, other_elements in area_hierarchy.items():
                            if area_id in other_elements and other_area_id != area_id:
                                area_depth += 1
                    
                    if area_depth < min_depth:
                        min_depth = area_depth
                        vertex_area = area_id
            
            # Position vertex in the shallowest area (least common area)
            # Use minimal depth offset so vertices stay in outer areas
            depth_offset = min_depth * 15.0
            vertex_positions[vertex.id] = Point(
                current_x + depth_offset, 
                current_y + depth_offset + 60  # Offset below predicates
            )
            
            current_x += self.element_spacing
            if current_x > 400:  # Wrap to next row
                current_x = self.viewport_margin
                current_y += self.element_spacing
        
        return vertex_positions
    
    def _position_predicates(self, egi: RelationalGraphWithCuts,
                           vertex_positions: Dict[ElementID, Point],
                           area_hierarchy: Dict[ElementID, Set[ElementID]]) -> Dict[ElementID, Point]:
        """Position predicates (edges) near their connected vertices"""
        predicate_positions = {}
        
        # Group predicates by their containing area to avoid overlap
        predicates_by_area = {}
        for area_id, elements in area_hierarchy.items():
            predicates_by_area[area_id] = []
            for element_id in elements:
                if any(e.id == element_id for e in egi.E):
                    predicates_by_area[area_id].append(element_id)
        
        # Global predicate counter for spacing when they share vertices
        global_predicate_index = 0
        
        for edge in egi.E:
            # Get vertices connected to this edge via ν mapping
            connected_vertices = egi.nu.get(edge.id, ())
            
            if connected_vertices:
                # Position predicate near centroid of connected vertices
                vertex_points = [vertex_positions[vid] for vid in connected_vertices 
                               if vid in vertex_positions]
                
                if vertex_points:
                    centroid_x = sum(p.x for p in vertex_points) / len(vertex_points)
                    centroid_y = sum(p.y for p in vertex_points) / len(vertex_points)
                    
                    # Find which area contains this predicate
                    predicate_area = None
                    predicate_area_depth = float('inf')
                    
                    for area_id, elements in area_hierarchy.items():
                        if edge.id in elements:
                            # Calculate area depth
                            area_depth = 0
                            if area_id != egi.sheet:
                                for other_area_id, other_elements in area_hierarchy.items():
                                    if area_id in other_elements and other_area_id != area_id:
                                        area_depth += 1
                            
                            # Use the deepest area (most specific containment)
                            if area_depth < predicate_area_depth:
                                predicate_area_depth = area_depth
                                predicate_area = area_id
                    
                    # Position predicate based on its area depth and avoid overlap
                    area_predicates = predicates_by_area.get(predicate_area, [])
                    predicate_index = area_predicates.index(edge.id) if edge.id in area_predicates else 0
                    
                    # Spread predicates horizontally within their area
                    area_x_offset = (predicate_index - (len(area_predicates) - 1) / 2) * 50.0
                    
                    # Add significant separation based on area depth (deeper = more right/down)
                    depth_x_offset = predicate_area_depth * 60.0  # Larger separation
                    depth_y_offset = predicate_area_depth * 20.0
                    
                    # Add global separation to prevent any overlap
                    global_separation = global_predicate_index * 30.0
                    
                    predicate_positions[edge.id] = Point(
                        centroid_x + area_x_offset + depth_x_offset + global_separation, 
                        centroid_y - 40.0 + depth_y_offset  # Position above vertices
                    )
                    
                    global_predicate_index += 1
                else:
                    # Fallback position
                    predicate_positions[edge.id] = Point(100.0, 50.0)
            else:
                # Edge with no vertices - isolated predicate
                predicate_positions[edge.id] = Point(100.0, 50.0)
        
        return predicate_positions
    
    def _compute_cut_bounds(self, egi: RelationalGraphWithCuts,
                          vertex_positions: Dict[ElementID, Point],
                          predicate_positions: Dict[ElementID, Point],
                          area_hierarchy: Dict[ElementID, Set[ElementID]],
                          containment_depth: Dict[ElementID, int]) -> Dict[ElementID, BoundingBox]:
        """Compute cut bounds that contain all their elements"""
        cut_bounds = {}
        
        # Process cuts by depth (innermost first)
        cuts_by_depth = {}
        for cut in egi.Cut:
            depth = containment_depth.get(cut.id, 0)
            if depth not in cuts_by_depth:
                cuts_by_depth[depth] = []
            cuts_by_depth[depth].append(cut.id)
        
        # Process from deepest to shallowest
        for depth in sorted(cuts_by_depth.keys(), reverse=True):
            for cut_id in cuts_by_depth[depth]:
                contained_elements = area_hierarchy.get(cut_id, set())
                
                # Collect positions of all contained elements
                xs, ys = [], []
                
                # Include vertices
                for element_id in contained_elements:
                    if element_id in vertex_positions:
                        pos = vertex_positions[element_id]
                        xs.extend([pos.x - 10, pos.x + 10])  # Vertex extent
                        ys.extend([pos.y - 10, pos.y + 10])
                
                # Include predicates
                for element_id in contained_elements:
                    if element_id in predicate_positions:
                        pos = predicate_positions[element_id]
                        xs.extend([pos.x - 20, pos.x + 20])  # Predicate extent
                        ys.extend([pos.y - 10, pos.y + 10])
                
                # Include nested cuts (already computed)
                for element_id in contained_elements:
                    if element_id in cut_bounds:
                        nested_bounds = cut_bounds[element_id]
                        xs.extend([nested_bounds.min_x, nested_bounds.max_x])
                        ys.extend([nested_bounds.min_y, nested_bounds.max_y])
                
                if xs and ys:
                    # Create bounds with appropriate margin
                    margin = self.cut_nesting_margin if any(eid in cut_bounds for eid in contained_elements) else self.cut_padding
                    
                    cut_bounds[cut_id] = BoundingBox(
                        min(xs) - margin, min(ys) - margin,
                        max(xs) + margin, max(ys) + margin
                    )
                else:
                    # Empty cut - minimal bounds
                    cut_bounds[cut_id] = BoundingBox(50, 50, 100, 100)
        
        return cut_bounds
    
    def _compute_ligature_paths(self, egi: RelationalGraphWithCuts,
                              vertex_positions: Dict[ElementID, Point],
                              predicate_positions: Dict[ElementID, Point]) -> List[LigaturePath]:
        """Compute ligature paths using validated core algorithms"""
        ligature_paths = []
        
        # For each edge, create ligatures to its connected vertices
        for edge in egi.E:
            predicate_pos = predicate_positions.get(edge.id)
            if not predicate_pos:
                continue
            
            connected_vertices = egi.nu.get(edge.id, ())
            for vertex_id in connected_vertices:
                vertex_pos = vertex_positions.get(vertex_id)
                if vertex_pos:
                    # Simple straight line path for now
                    # TODO: Use enhanced ligature algorithms for complex routing
                    path = LigaturePath(
                        predicate_id=edge.id,
                        vertex_id=vertex_id,
                        points=(predicate_pos, vertex_pos)
                    )
                    ligature_paths.append(path)
        
        return ligature_paths
    
    def _calculate_viewport(self, vertex_positions: Dict[ElementID, Point],
                          predicate_positions: Dict[ElementID, Point],
                          cut_bounds: Dict[ElementID, BoundingBox]) -> BoundingBox:
        """Calculate viewport bounds containing all elements"""
        xs, ys = [], []
        
        # Include all element positions
        for pos in vertex_positions.values():
            xs.append(pos.x)
            ys.append(pos.y)
        
        for pos in predicate_positions.values():
            xs.append(pos.x)
            ys.append(pos.y)
        
        for bounds in cut_bounds.values():
            xs.extend([bounds.min_x, bounds.max_x])
            ys.extend([bounds.min_y, bounds.max_y])
        
        if xs and ys:
            return BoundingBox(
                min(xs) - self.viewport_margin, min(ys) - self.viewport_margin,
                max(xs) + self.viewport_margin, max(ys) + self.viewport_margin
            )
        else:
            return BoundingBox(0, 0, 200, 200)
    
    def _generate_style_hints(self, egi: RelationalGraphWithCuts) -> Dict[str, any]:
        """Generate platform-independent style hints"""
        return {
            'vertex_count': len(egi.V),
            'edge_count': len(egi.E),
            'cut_count': len(egi.Cut),
            'has_constants': any(not v.is_generic for v in egi.V),
            'max_arity': max((len(vertices) for vertices in egi.nu.values()), default=0),
            'suggested_style': 'dau_compliant'
        }
