"""
Style-Aware Layout Engine

Extends the iron-clad layout engine with style-aware spatial calculations.
Style specifications affect spatial requirements while maintaining iron-clad
guarantees of spatial-logical correspondence.

ARCHITECTURE:
1. Iron-clad foundation: Guaranteed spatial-logical correspondence
2. Style layer: Style specifications affect spatial requirements
3. Readability layer: Logic-indifferent optimizations for intelligibility
"""

from dataclasses import dataclass
from typing import Dict, Optional, Set, List, Tuple
from abc import ABC, abstractmethod

from layout_engine_ironclad import (
    LayoutEngineIronClad, LayoutDTO, Point, BoundingBox, 
    AreaZone, LigaturePath
)
from egi_core_dau import RelationalGraphWithCuts, ElementID
from style_loader import StyleSpecification, load_default_style


# StyleSpecification is now imported from style_loader


@dataclass(frozen=True)
class ElementDistribution:
    """Specification for how elements should be distributed within an area"""
    
    layout_algorithm: str = "grid"  # "grid", "circular", "linear", "organic"
    alignment: str = "center"  # "left", "center", "right", "justify"
    flow_direction: str = "horizontal"  # "horizontal", "vertical", "radial"
    
    # Grid-specific
    max_columns: int = 3
    row_spacing: float = 30.0
    column_spacing: float = 40.0
    
    # Circular-specific
    radius_base: float = 50.0
    angular_spacing: float = 45.0  # degrees
    
    # Organic-specific
    force_strength: float = 1.0
    repulsion_distance: float = 60.0


@dataclass(frozen=True)
class LigatureRouting:
    """Specification for ligature routing algorithms"""
    
    routing_algorithm: str = "manhattan"  # "manhattan", "orthogonal", "bezier", "direct"
    avoid_overlaps: bool = True
    minimize_crossings: bool = True
    
    # Manhattan/Orthogonal
    corner_radius: float = 5.0
    grid_snap: bool = True
    
    # Bezier
    control_point_distance: float = 30.0
    smoothness: float = 0.8
    
    # Optimization
    max_iterations: int = 100
    convergence_threshold: float = 1.0


class StyleAwareLayoutEngine(LayoutEngineIronClad):
    """
    Layout engine that considers style specifications in spatial calculations.
    
    Maintains iron-clad guarantees while allowing style to affect:
    1. Element spatial requirements
    2. Spacing and padding calculations  
    3. Area size computations
    4. Ligature routing preferences
    """
    
    def __init__(self, style_spec: Optional[StyleSpecification] = None):
        super().__init__()
        self.style_spec = style_spec or load_default_style()
        
        # Override base parameters with style-aware values
        self.element_spacing = self.style_spec.element_spacing
        self.cut_margin = self.style_spec.cut_padding
        self.cut_nesting_margin = self.style_spec.cut_padding  # Use cut_padding for nesting
        self.text_width = self.style_spec.predicate_char_width
        self.text_height = self.style_spec.predicate_height
        self.vertex_size = self.style_spec.vertex_radius
    
    def compute_layout(self, egi: RelationalGraphWithCuts, 
                      distribution: Optional[ElementDistribution] = None,
                      ligature_routing: Optional[LigatureRouting] = None) -> LayoutDTO:
        """
        Compute style-aware layout with optional distribution and routing specs.
        
        IRON-CLAD GUARANTEE: Spatial-logical correspondence maintained regardless of style.
        """
        
        # Step 1: Build area hierarchy (iron-clad - unchanged)
        area_hierarchy, containment_depth = self._build_area_hierarchy(egi)
        
        # Step 2: Allocate spatial zones with style-aware sizing
        area_zones = self._allocate_style_aware_zones(egi, area_hierarchy, containment_depth)
        
        # Step 3: Position elements with distribution algorithms
        vertex_positions, predicate_positions = self._position_elements_with_distribution(
            egi, area_hierarchy, area_zones, distribution or ElementDistribution()
        )
        
        # Step 4: Compute cut bounds (iron-clad - style affects sizing only)
        cut_bounds = self._compute_cut_bounds_from_positions(
            egi, vertex_positions, predicate_positions, area_zones
        )
        
        # Step 5: Generate ligature paths with routing algorithms
        ligature_paths = self._compute_styled_ligature_paths(
            egi, vertex_positions, predicate_positions, 
            ligature_routing or LigatureRouting()
        )
        
        # Step 6: Calculate viewport
        viewport_bounds = self._calculate_viewport(vertex_positions, predicate_positions, cut_bounds)
        
        # Step 7: Validate (iron-clad guarantee)
        self._validate_layout(egi, vertex_positions, predicate_positions, cut_bounds, area_hierarchy)
        
        return LayoutDTO(
            vertex_positions=vertex_positions,
            predicate_positions=predicate_positions,
            cut_bounds=cut_bounds,
            ligature_paths=ligature_paths,
            area_hierarchy=area_hierarchy,
            containment_depth=containment_depth,
            viewport_bounds=viewport_bounds,
            style_hints=self._generate_style_aware_hints(egi)
        )
    
    def _allocate_style_aware_zones(self, egi: RelationalGraphWithCuts,
                                   area_hierarchy: Dict[ElementID, Set[ElementID]],
                                   containment_depth: Dict[ElementID, int]) -> Dict[ElementID, AreaZone]:
        """Allocate spatial zones considering style requirements"""
        
        area_zones = {}
        
        # Group areas by depth
        areas_by_depth = {}
        for area_id, depth in containment_depth.items():
            if depth not in areas_by_depth:
                areas_by_depth[depth] = []
            areas_by_depth[depth].append(area_id)
        
        # Allocate zones from deepest to shallowest
        for depth in sorted(areas_by_depth.keys(), reverse=True):
            for area_id in areas_by_depth[depth]:
                zone = self._allocate_style_aware_zone_for_area(
                    area_id, egi, area_hierarchy, containment_depth, area_zones
                )
                area_zones[area_id] = zone
        
        return area_zones
    
    def _allocate_style_aware_zone_for_area(self, area_id: ElementID, egi: RelationalGraphWithCuts,
                                           area_hierarchy: Dict[ElementID, Set[ElementID]],
                                           containment_depth: Dict[ElementID, int],
                                           existing_zones: Dict[ElementID, AreaZone]) -> AreaZone:
        """Allocate zone considering style-specific element sizing"""
        
        area_elements = area_hierarchy.get(area_id, set())
        depth = containment_depth.get(area_id, 0)
        
        # Calculate style-aware element requirements
        total_vertex_width = 0
        total_predicate_width = 0
        max_element_height = 0
        
        for elem_id in area_elements:
            # Vertices
            vertex = next((v for v in egi.V if v.id == elem_id), None)
            if vertex:
                width, height = self.style_spec.get_element_bounds("vertex")
                total_vertex_width += width + self.style_spec.element_spacing
                max_element_height = max(max_element_height, height)
            
            # Predicates
            edge = next((e for e in egi.E if e.id == elem_id), None)
            if edge:
                relation_name = egi.rel.get(elem_id, "")
                width, height = self.style_spec.get_element_bounds("predicate", relation_name)
                total_predicate_width += width + self.style_spec.element_spacing
                max_element_height = max(max_element_height, height)
        
        # Calculate child cut requirements
        child_cuts_width = 0
        child_cuts_height = 0
        child_cut_ids = [elem_id for elem_id in area_elements if any(c.id == elem_id for c in egi.Cut)]
        
        if child_cut_ids:
            for elem_id in child_cut_ids:
                if elem_id in existing_zones:
                    child_zone = existing_zones[elem_id]
                    child_cuts_width += child_zone.bounds.width + self.style_spec.element_spacing
                    child_cuts_height = max(child_cuts_height, child_zone.bounds.height)
            
            if child_cuts_width > 0:
                child_cuts_width -= self.style_spec.element_spacing  # Remove extra spacing
        
        # Calculate total zone requirements
        elements_width = max(total_vertex_width, total_predicate_width)
        elements_height = max_element_height * 2 + self.style_spec.element_spacing  # Predicates above vertices
        
        zone_width = max(elements_width, child_cuts_width) + 2 * self.style_spec.cut_padding
        zone_height = elements_height + child_cuts_height + 2 * self.style_spec.cut_padding
        
        # Position with sibling awareness (unchanged from iron-clad)
        base_x = depth * 50.0
        base_y = depth * 50.0
        
        if any(c.id == area_id for c in egi.Cut):
            sibling_index = 0
            for parent_area_id, parent_elements in area_hierarchy.items():
                if area_id in parent_elements and parent_area_id != area_id:
                    sibling_cuts = [e for e in parent_elements if any(c.id == e for c in egi.Cut)]
                    sibling_cuts.sort()
                    if area_id in sibling_cuts:
                        sibling_index = sibling_cuts.index(area_id)
                    break
            
            sibling_offset_x = sibling_index * (zone_width + self.style_spec.element_spacing)
            base_x += sibling_offset_x
        
        zone_bounds = BoundingBox(base_x, base_y, base_x + zone_width, base_y + zone_height)
        
        # Find parent and children
        parent_area = None
        child_areas = []
        
        for other_area_id, other_elements in area_hierarchy.items():
            if area_id in other_elements and other_area_id != area_id:
                parent_area = other_area_id
            
            if other_area_id in area_elements and other_area_id != area_id:
                child_areas.append(other_area_id)
        
        return AreaZone(
            area_id=area_id,
            bounds=zone_bounds,
            depth=depth,
            parent_area=parent_area,
            child_areas=child_areas
        )
    
    def _position_elements_with_distribution(self, egi: RelationalGraphWithCuts,
                                           area_hierarchy: Dict[ElementID, Set[ElementID]],
                                           area_zones: Dict[ElementID, AreaZone],
                                           distribution: ElementDistribution) -> Tuple[Dict[ElementID, Point], Dict[ElementID, Point]]:
        """Position elements using specified distribution algorithm"""
        
        vertex_positions = {}
        predicate_positions = {}
        
        for area_id, zone in area_zones.items():
            area_elements = area_hierarchy.get(area_id, set())
            
            # Separate elements by type
            area_vertices = [elem_id for elem_id in area_elements if any(v.id == elem_id for v in egi.V)]
            area_predicates = [elem_id for elem_id in area_elements if any(e.id == elem_id for e in egi.E)]
            
            # Apply distribution algorithm
            if distribution.layout_algorithm == "grid":
                v_positions, p_positions = self._distribute_grid(
                    area_vertices, area_predicates, zone, distribution
                )
            elif distribution.layout_algorithm == "circular":
                v_positions, p_positions = self._distribute_circular(
                    area_vertices, area_predicates, zone, distribution
                )
            elif distribution.layout_algorithm == "linear":
                v_positions, p_positions = self._distribute_linear(
                    area_vertices, area_predicates, zone, distribution
                )
            else:  # organic
                v_positions, p_positions = self._distribute_organic(
                    area_vertices, area_predicates, zone, distribution
                )
            
            vertex_positions.update(v_positions)
            predicate_positions.update(p_positions)
        
        return vertex_positions, predicate_positions
    
    def _distribute_grid(self, vertices: List[ElementID], predicates: List[ElementID],
                        zone: AreaZone, distribution: ElementDistribution) -> Tuple[Dict[ElementID, Point], Dict[ElementID, Point]]:
        """Distribute elements in a grid pattern"""
        
        vertex_positions = {}
        predicate_positions = {}
        
        # Position predicates in upper part of zone
        predicate_y = zone.bounds.min_y + self.style_spec.cut_padding
        predicate_start_x = zone.bounds.min_x + self.style_spec.cut_padding
        
        for i, pred_id in enumerate(predicates):
            col = i % distribution.max_columns
            row = i // distribution.max_columns
            
            x = predicate_start_x + col * (self.style_spec.predicate_char_width * 8 + distribution.column_spacing)
            y = predicate_y + row * (self.style_spec.predicate_height + distribution.row_spacing)
            
            if x + self.style_spec.predicate_char_width * 8 <= zone.bounds.max_x - self.style_spec.cut_padding:
                predicate_positions[pred_id] = Point(x, y)
            else:
                # Wrap to next row
                predicate_positions[pred_id] = Point(predicate_start_x, y + self.style_spec.predicate_height + distribution.row_spacing)
        
        # Position vertices in lower part of zone
        vertex_y = zone.bounds.min_y + self.style_spec.cut_padding + self.style_spec.predicate_height + self.style_spec.element_spacing
        vertex_start_x = zone.bounds.min_x + self.style_spec.cut_padding
        
        for i, vertex_id in enumerate(vertices):
            col = i % distribution.max_columns
            row = i // distribution.max_columns
            
            x = vertex_start_x + col * (self.style_spec.vertex_radius * 2 + distribution.column_spacing)
            y = vertex_y + row * (self.style_spec.vertex_radius * 2 + distribution.row_spacing)
            
            if x + self.style_spec.vertex_radius * 2 <= zone.bounds.max_x - self.style_spec.cut_padding:
                vertex_positions[vertex_id] = Point(x + self.style_spec.vertex_radius, y + self.style_spec.vertex_radius)
            else:
                # Wrap to next row
                vertex_positions[vertex_id] = Point(vertex_start_x + self.style_spec.vertex_radius, y + self.style_spec.vertex_radius * 2 + distribution.row_spacing)
        
        return vertex_positions, predicate_positions
    
    def _distribute_circular(self, vertices: List[ElementID], predicates: List[ElementID],
                           zone: AreaZone, distribution: ElementDistribution) -> Tuple[Dict[ElementID, Point], Dict[ElementID, Point]]:
        """Distribute elements in circular patterns"""
        
        import math
        
        vertex_positions = {}
        predicate_positions = {}
        
        center_x = zone.bounds.center.x
        center_y = zone.bounds.center.y
        
        # Predicates in inner circle
        if predicates:
            pred_radius = distribution.radius_base * 0.7
            angle_step = 2 * math.pi / len(predicates)
            
            for i, pred_id in enumerate(predicates):
                angle = i * angle_step
                x = center_x + pred_radius * math.cos(angle)
                y = center_y + pred_radius * math.sin(angle)
                predicate_positions[pred_id] = Point(x, y)
        
        # Vertices in outer circle
        if vertices:
            vertex_radius = distribution.radius_base
            angle_step = 2 * math.pi / len(vertices)
            
            for i, vertex_id in enumerate(vertices):
                angle = i * angle_step
                x = center_x + vertex_radius * math.cos(angle)
                y = center_y + vertex_radius * math.sin(angle)
                vertex_positions[vertex_id] = Point(x, y)
        
        return vertex_positions, predicate_positions
    
    def _distribute_linear(self, vertices: List[ElementID], predicates: List[ElementID],
                          zone: AreaZone, distribution: ElementDistribution) -> Tuple[Dict[ElementID, Point], Dict[ElementID, Point]]:
        """Distribute elements linearly"""
        
        vertex_positions = {}
        predicate_positions = {}
        
        if distribution.flow_direction == "horizontal":
            # Predicates in upper row
            if predicates:
                total_width = len(predicates) * self.style_spec.predicate_char_width * 8 + (len(predicates) - 1) * distribution.column_spacing
                start_x = zone.bounds.center.x - total_width / 2
                y = zone.bounds.min_y + self.style_spec.cut_padding
                
                for i, pred_id in enumerate(predicates):
                    x = start_x + i * (self.style_spec.predicate_char_width * 8 + distribution.column_spacing)
                    predicate_positions[pred_id] = Point(x, y)
            
            # Vertices in lower row
            if vertices:
                total_width = len(vertices) * self.style_spec.vertex_radius * 2 + (len(vertices) - 1) * distribution.column_spacing
                start_x = zone.bounds.center.x - total_width / 2
                y = zone.bounds.max_y - self.style_spec.cut_padding - self.style_spec.vertex_radius
                
                for i, vertex_id in enumerate(vertices):
                    x = start_x + i * (self.style_spec.vertex_radius * 2 + distribution.column_spacing) + self.style_spec.vertex_radius
                    vertex_positions[vertex_id] = Point(x, y)
        
        else:  # vertical
            # Similar logic for vertical layout
            pass
        
        return vertex_positions, predicate_positions
    
    def _distribute_organic(self, vertices: List[ElementID], predicates: List[ElementID],
                           zone: AreaZone, distribution: ElementDistribution) -> Tuple[Dict[ElementID, Point], Dict[ElementID, Point]]:
        """Distribute elements using organic (pseudo-random) algorithm"""
        
        import random
        
        vertex_positions = {}
        predicate_positions = {}
        
        # Use a fixed seed for reproducible "organic" layout
        random.seed(hash(str(sorted(vertices + predicates))) % 1000)
        
        # Available area within zone
        available_width = zone.bounds.width - 2 * self.style_spec.cut_padding
        available_height = zone.bounds.height - 2 * self.style_spec.cut_padding
        
        # Position predicates with some randomness
        for i, pred_id in enumerate(predicates):
            # Add some organic variation to grid positions
            base_x = zone.bounds.min_x + self.style_spec.cut_padding + (i * 60) % available_width
            base_y = zone.bounds.min_y + self.style_spec.cut_padding + 20
            
            # Add organic offset
            offset_x = random.uniform(-15, 15)
            offset_y = random.uniform(-10, 10)
            
            x = max(zone.bounds.min_x + self.style_spec.cut_padding, 
                   min(base_x + offset_x, zone.bounds.max_x - self.style_spec.cut_padding - self.style_spec.predicate_char_width * 8))
            y = max(zone.bounds.min_y + self.style_spec.cut_padding,
                   min(base_y + offset_y, zone.bounds.max_y - self.style_spec.cut_padding - self.style_spec.predicate_height))
            
            predicate_positions[pred_id] = Point(x, y)
        
        # Position vertices with organic variation
        for i, vertex_id in enumerate(vertices):
            base_x = zone.bounds.min_x + self.style_spec.cut_padding + (i * 70) % available_width
            base_y = zone.bounds.max_y - self.style_spec.cut_padding - self.style_spec.vertex_radius * 2 - 20
            
            # Add organic offset
            offset_x = random.uniform(-20, 20)
            offset_y = random.uniform(-15, 15)
            
            x = max(zone.bounds.min_x + self.style_spec.cut_padding + self.style_spec.vertex_radius,
                   min(base_x + offset_x, zone.bounds.max_x - self.style_spec.cut_padding - self.style_spec.vertex_radius))
            y = max(zone.bounds.min_y + self.style_spec.cut_padding + self.style_spec.vertex_radius,
                   min(base_y + offset_y, zone.bounds.max_y - self.style_spec.cut_padding - self.style_spec.vertex_radius))
            
            vertex_positions[vertex_id] = Point(x, y)
        
        return vertex_positions, predicate_positions
    
    def _compute_styled_ligature_paths(self, egi: RelationalGraphWithCuts,
                                      vertex_positions: Dict[ElementID, Point],
                                      predicate_positions: Dict[ElementID, Point],
                                      routing: LigatureRouting) -> List[LigaturePath]:
        """Compute ligature paths using specified routing algorithm"""
        
        ligature_paths = []
        
        for edge in egi.E:
            predicate_pos = predicate_positions.get(edge.id)
            if not predicate_pos:
                continue
            
            connected_vertices = egi.nu.get(edge.id, ())
            for vertex_id in connected_vertices:
                vertex_pos = vertex_positions.get(vertex_id)
                if vertex_pos:
                    if routing.routing_algorithm == "manhattan":
                        path_points = self._route_manhattan(predicate_pos, vertex_pos, routing)
                    elif routing.routing_algorithm == "bezier":
                        path_points = self._route_bezier(predicate_pos, vertex_pos, routing)
                    elif routing.routing_algorithm == "orthogonal":
                        path_points = self._route_orthogonal(predicate_pos, vertex_pos, routing)
                    else:  # direct
                        path_points = (predicate_pos, vertex_pos)
                    
                    path = LigaturePath(
                        predicate_id=edge.id,
                        vertex_id=vertex_id,
                        points=path_points
                    )
                    ligature_paths.append(path)
        
        return ligature_paths
    
    def _route_manhattan(self, start: Point, end: Point, routing: LigatureRouting) -> Tuple[Point, ...]:
        """Route ligature using Manhattan (L-shaped) algorithm"""
        
        # Simple L-shaped routing
        if abs(start.x - end.x) > abs(start.y - end.y):
            # Horizontal then vertical
            mid_point = Point(end.x, start.y)
        else:
            # Vertical then horizontal
            mid_point = Point(start.x, end.y)
        
        return (start, mid_point, end)
    
    def _route_bezier(self, start: Point, end: Point, routing: LigatureRouting) -> Tuple[Point, ...]:
        """Route ligature using Bezier curves"""
        
        # Calculate control points
        dx = end.x - start.x
        dy = end.y - start.y
        
        control1 = Point(
            start.x + dx * 0.3,
            start.y + routing.control_point_distance
        )
        control2 = Point(
            end.x - dx * 0.3,
            end.y - routing.control_point_distance
        )
        
        # Generate curve points (simplified)
        return (start, control1, control2, end)
    
    def _route_orthogonal(self, start: Point, end: Point, routing: LigatureRouting) -> Tuple[Point, ...]:
        """Route ligature using orthogonal algorithm"""
        
        # Multi-segment orthogonal routing
        mid_x = (start.x + end.x) / 2
        
        return (
            start,
            Point(mid_x, start.y),
            Point(mid_x, end.y),
            end
        )
    
    def _generate_style_aware_hints(self, egi: RelationalGraphWithCuts) -> Dict[str, any]:
        """Generate style hints for rendering"""
        
        base_hints = super()._generate_style_hints(egi)
        base_hints.update({
            'style_specification': {
                'vertex_radius': self.style_spec.vertex_radius,
                'predicate_width': self.style_spec.predicate_char_width,
                'predicate_height': self.style_spec.predicate_height,
                'element_spacing': self.style_spec.element_spacing,
                'cut_padding': self.style_spec.cut_padding,
                'font_size': self.style_spec.font_size,
                'ligature_width': self.style_spec.ligature_line_width
            },
            'layout_engine': 'style-aware',
            'style_aware': True
        })
        
        return base_hints
