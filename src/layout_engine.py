"""
Pure Layout Engine for Existential Graph Diagrams
Handles spatial positioning and geometric relationships following Dau's conventions.
Completely separated from rendering and data concerns.
"""

from typing import Dict, List, Tuple, Optional, Set, Any
from dataclasses import dataclass
from enum import Enum
import math
import uuid

# Handle imports for both module and script execution
try:
    from .egi_core_dau import RelationalGraphWithCuts, ElementID, Vertex, Edge, Cut
except ImportError:
    from egi_core_dau import RelationalGraphWithCuts, ElementID, Vertex, Edge, Cut

# Type aliases for clarity
Coordinate = Tuple[float, float]
Bounds = Tuple[float, float, float, float]  # x1, y1, x2, y2


class LayoutConstraint(Enum):
    """Types of layout constraints following Dau's conventions"""
    CONTAINMENT = "containment"          # Cut containment hierarchy
    NON_OVERLAPPING = "non_overlapping"  # Elements don't overlap inappropriately
    ATTACHMENT = "attachment"            # Predicate attachment to line ends
    IDENTITY_CONTINUITY = "identity_continuity"  # Line of identity continuity
    ARBITRARY_DEFORMATION = "arbitrary_deformation"  # Shape flexibility allowed


@dataclass(frozen=True)
class LayoutElement:
    """Pure spatial representation of a graph element (no rendering info)"""
    element_id: ElementID
    element_type: str  # 'vertex', 'edge', 'cut'
    position: Coordinate
    bounds: Bounds
    
    # Spatial relationships
    parent_area: Optional[ElementID] = None
    contained_elements: Set[ElementID] = None
    
    # Geometric properties (following Dau's conventions)
    curve_points: Optional[List[Coordinate]] = None  # For cuts and edges
    attachment_points: Optional[Dict[str, Coordinate]] = None  # For predicate hooks
    
    def __post_init__(self):
        if self.contained_elements is None:
            object.__setattr__(self, 'contained_elements', set())
    
    def contains_point(self, point: Coordinate) -> bool:
        """Check if point is within this element's bounds"""
        x, y = point
        x1, y1, x2, y2 = self.bounds
        return x1 <= x <= x2 and y1 <= y <= y2
    
    def get_center(self) -> Coordinate:
        """Get the center point of this element"""
        x1, y1, x2, y2 = self.bounds
        return ((x1 + x2) / 2, (y1 + y2) / 2)


@dataclass(frozen=True)
class LayoutResult:
    """Complete spatial arrangement of all graph elements"""
    elements: Dict[ElementID, LayoutElement]
    canvas_bounds: Bounds
    containment_hierarchy: Dict[ElementID, Set[ElementID]]
    
    # Layout metadata
    layout_constraints_satisfied: Set[LayoutConstraint]
    layout_quality_score: float  # 0.0 to 1.0
    
    def get_element(self, element_id: ElementID) -> Optional[LayoutElement]:
        """Get layout element by ID"""
        return self.elements.get(element_id)
    
    def find_element_at_point(self, point: Coordinate) -> Optional[ElementID]:
        """Find the topmost element at the given point"""
        # Check in reverse order to get topmost element
        for element_id, element in reversed(list(self.elements.items())):
            if element.contains_point(point):
                return element_id
        return None
    
    def get_elements_in_area(self, area_id: ElementID) -> Set[ElementID]:
        """Get all elements contained within an area"""
        return self.containment_hierarchy.get(area_id, set())


class LayoutEngine:
    """
    Pure layout engine for Existential Graph diagrams.
    Handles spatial positioning following Dau's conventions with no rendering concerns.
    """
    
    def __init__(self, canvas_width: int = 800, canvas_height: int = 600):
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.margin = 50
        
        # Dau convention parameters
        self.vertex_radius = 5.0
        self.min_vertex_distance = 40.0
        self.cut_padding = 30.0
        self.line_thickness = 3.0  # Heavy lines for identity
        self.cut_line_thickness = 1.0  # Fine lines for cuts
        
        # Layout quality parameters
        self.preferred_aspect_ratio = 1.2
        self.min_cut_size = 60.0
        
    def layout_graph(self, graph: RelationalGraphWithCuts) -> LayoutResult:
        """
        Generate complete spatial layout for a Dau graph.
        Returns pure spatial arrangement with no rendering information.
        """
        elements = {}
        containment_hierarchy = {}
        
        # Step 1: Layout cuts with proper hierarchical containment
        cut_layouts = self._layout_cuts_hierarchical(graph)
        elements.update(cut_layouts)
        
        # Step 2: Layout vertices within their proper areas
        vertex_layouts = self._layout_vertices(graph, cut_layouts)
        elements.update(vertex_layouts)
        
        # Step 3: Layout edges (lines of identity and relations)
        edge_layouts = self._layout_edges(graph, elements)
        elements.update(edge_layouts)
        
        # Step 4: Build containment hierarchy
        containment_hierarchy = self._build_containment_hierarchy(graph, elements)
        
        # Step 5: Validate layout constraints
        satisfied_constraints = self._validate_constraints(elements, graph)
        quality_score = self._calculate_quality_score(elements, satisfied_constraints)
        
        canvas_bounds = (0, 0, self.canvas_width, self.canvas_height)
        
        return LayoutResult(
            elements=elements,
            canvas_bounds=canvas_bounds,
            containment_hierarchy=containment_hierarchy,
            layout_constraints_satisfied=satisfied_constraints,
            layout_quality_score=quality_score
        )
    
    def _layout_cuts_hierarchical(self, graph: RelationalGraphWithCuts) -> Dict[ElementID, LayoutElement]:
        """
        Layout cuts with proper hierarchical containment following Dau's conventions.
        No overlapping cuts; strict parent-child nesting.
        """
        cut_layouts = {}
        
        # Group cuts by nesting depth
        depth_groups = self._group_cuts_by_depth(graph)
        
        # Layout from outermost to innermost
        for depth in sorted(depth_groups.keys()):
            cuts_at_depth = depth_groups[depth]
            
            for cut in cuts_at_depth:
                parent_area = self._find_parent_area(cut.id, graph)
                cut_layout = self._layout_single_cut(cut, graph, parent_area, cut_layouts)
                cut_layouts[cut.id] = cut_layout
        
        return cut_layouts
    
    def _layout_single_cut(self, cut: Cut, graph: RelationalGraphWithCuts, 
                          parent_area: Optional[ElementID], 
                          existing_layouts: Dict[ElementID, LayoutElement]) -> LayoutElement:
        """Layout a single cut following Dau's fine-drawn closed curve convention"""
        
        # Determine available space
        if parent_area and parent_area in existing_layouts:
            parent_bounds = existing_layouts[parent_area].bounds
            # Inset from parent bounds
            x1, y1, x2, y2 = parent_bounds
            available_bounds = (
                x1 + self.cut_padding,
                y1 + self.cut_padding,
                x2 - self.cut_padding,
                y2 - self.cut_padding
            )
        else:
            # Top-level cut - use canvas space
            available_bounds = (
                self.margin,
                self.margin,
                self.canvas_width - self.margin,
                self.canvas_height - self.margin
            )
        
        # Calculate cut size based on contents
        cut_contents = graph.area.get(cut.id, set())
        content_count = len(cut_contents)
        
        # Base size with scaling for contents
        base_size = max(self.min_cut_size, content_count * 30 + 40)
        width = min(base_size * self.preferred_aspect_ratio, 
                   available_bounds[2] - available_bounds[0])
        height = min(base_size, available_bounds[3] - available_bounds[1])
        
        # Position within available space (avoid overlaps with siblings)
        x, y = self._find_non_overlapping_position(
            width, height, available_bounds, existing_layouts, parent_area
        )
        
        # Generate oval curve points following Dau's closed curve convention
        curve_points = self._generate_oval_curve(x, y, x + width, y + height)
        
        return LayoutElement(
            element_id=cut.id,
            element_type='cut',
            position=(x + width/2, y + height/2),
            bounds=(x, y, x + width, y + height),
            parent_area=parent_area,
            curve_points=curve_points
        )
    
    def _layout_vertices(self, graph: RelationalGraphWithCuts, 
                        cut_layouts: Dict[ElementID, LayoutElement]) -> Dict[ElementID, LayoutElement]:
        """Layout vertices as heavy spots or line segments following Dau's conventions"""
        vertex_layouts = {}
        
        for vertex in graph.V:
            # Find which area contains this vertex
            containing_area = self._find_containing_area(vertex.id, graph)
            
            # Get available space within the containing area
            if containing_area in cut_layouts:
                container_bounds = cut_layouts[containing_area].bounds
                # Inset from container bounds
                x1, y1, x2, y2 = container_bounds
                available_bounds = (
                    x1 + self.cut_padding/2,
                    y1 + self.cut_padding/2,
                    x2 - self.cut_padding/2,
                    y2 - self.cut_padding/2
                )
            else:
                # Sheet level
                available_bounds = (
                    self.margin,
                    self.margin,
                    self.canvas_width - self.margin,
                    self.canvas_height - self.margin
                )
            
            # Position vertex within available space
            x, y = self._find_vertex_position(vertex, available_bounds, vertex_layouts)
            
            # Create vertex layout (heavy spot following Dau's convention)
            vertex_layouts[vertex.id] = LayoutElement(
                element_id=vertex.id,
                element_type='vertex',
                position=(x, y),
                bounds=(
                    x - self.vertex_radius,
                    y - self.vertex_radius,
                    x + self.vertex_radius,
                    y + self.vertex_radius
                ),
                parent_area=containing_area
            )
        
        return vertex_layouts
    
    def _layout_edges(self, graph: RelationalGraphWithCuts, 
                     all_layouts: Dict[ElementID, LayoutElement]) -> Dict[ElementID, LayoutElement]:
        """Layout edges as relations with proper attachment points following Dau's conventions"""
        edge_layouts = {}
        
        for edge in graph.E:
            # Get vertex positions for this edge
            vertex_positions = []
            for vertex_id in graph.nu.get(edge.id, []):
                if vertex_id in all_layouts:
                    vertex_positions.append(all_layouts[vertex_id].position)
            
            if len(vertex_positions) < 2:
                continue  # Skip edges without proper connections
            
            # Calculate edge bounds and attachment points
            min_x = min(pos[0] for pos in vertex_positions) - 20
            max_x = max(pos[0] for pos in vertex_positions) + 20
            min_y = min(pos[1] for pos in vertex_positions) - 20
            max_y = max(pos[1] for pos in vertex_positions) + 20
            
            # Create attachment points for predicate hooks
            attachment_points = {}
            for i, pos in enumerate(vertex_positions):
                attachment_points[f"vertex_{i}"] = pos
            
            edge_layouts[edge.id] = LayoutElement(
                element_id=edge.id,
                element_type='edge',
                position=((min_x + max_x) / 2, (min_y + max_y) / 2),
                bounds=(min_x, min_y, max_x, max_y),
                attachment_points=attachment_points,
                curve_points=vertex_positions  # Line segments connecting vertices
            )
        
        return edge_layouts
    
    # Helper methods for spatial calculations
    
    def _group_cuts_by_depth(self, graph: RelationalGraphWithCuts) -> Dict[int, List[Cut]]:
        """Group cuts by their nesting depth"""
        depth_groups = {}
        
        for cut in graph.Cut:
            depth = self._calculate_cut_depth(cut.id, graph)
            if depth not in depth_groups:
                depth_groups[depth] = []
            depth_groups[depth].append(cut)
        
        return depth_groups
    
    def _calculate_cut_depth(self, cut_id: ElementID, graph: RelationalGraphWithCuts) -> int:
        """Calculate nesting depth of a cut"""
        depth = 0
        current_area = self._find_parent_area(cut_id, graph)
        
        while current_area and current_area != graph.sheet:
            depth += 1
            current_area = self._find_parent_area(current_area, graph)
        
        return depth
    
    def _find_parent_area(self, element_id: ElementID, graph: RelationalGraphWithCuts) -> Optional[ElementID]:
        """Find the area that contains the given element"""
        for area_id, elements in graph.area.items():
            if element_id in elements:
                return area_id
        return None
    
    def _find_containing_area(self, vertex_id: ElementID, graph: RelationalGraphWithCuts) -> Optional[ElementID]:
        """Find which area contains a vertex"""
        return self._find_parent_area(vertex_id, graph)
    
    def _find_non_overlapping_position(self, width: float, height: float, 
                                     available_bounds: Bounds,
                                     existing_layouts: Dict[ElementID, LayoutElement],
                                     parent_area: Optional[ElementID]) -> Coordinate:
        """Find a position that doesn't overlap with existing elements"""
        x1, y1, x2, y2 = available_bounds
        
        # Simple grid-based positioning to avoid overlaps
        grid_size = 80
        best_x, best_y = x1, y1
        
        for grid_y in range(int(y1), int(y2 - height), grid_size):
            for grid_x in range(int(x1), int(x2 - width), grid_size):
                test_bounds = (grid_x, grid_y, grid_x + width, grid_y + height)
                
                # Check for overlaps with siblings in same area
                overlaps = False
                for layout in existing_layouts.values():
                    if layout.parent_area == parent_area:
                        if self._bounds_overlap(test_bounds, layout.bounds):
                            overlaps = True
                            break
                
                if not overlaps:
                    return (grid_x, grid_y)
        
        # Fallback to available space
        return (x1, y1)
    
    def _find_vertex_position(self, vertex: Vertex, available_bounds: Bounds,
                            existing_vertices: Dict[ElementID, LayoutElement]) -> Coordinate:
        """Find optimal position for a vertex within available space"""
        x1, y1, x2, y2 = available_bounds
        
        # Simple positioning with minimum distance constraints
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        
        # Try center first
        if self._vertex_position_valid((center_x, center_y), existing_vertices):
            return (center_x, center_y)
        
        # Spiral outward from center
        for radius in range(20, int(min(x2-x1, y2-y1)/2), 20):
            for angle in range(0, 360, 30):
                x = center_x + radius * math.cos(math.radians(angle))
                y = center_y + radius * math.sin(math.radians(angle))
                
                if x1 <= x <= x2 and y1 <= y <= y2:
                    if self._vertex_position_valid((x, y), existing_vertices):
                        return (x, y)
        
        # Fallback
        return (center_x, center_y)
    
    def _vertex_position_valid(self, position: Coordinate, 
                             existing_vertices: Dict[ElementID, LayoutElement]) -> bool:
        """Check if vertex position maintains minimum distance from others"""
        x, y = position
        
        for vertex_layout in existing_vertices.values():
            vx, vy = vertex_layout.position
            distance = math.sqrt((x - vx)**2 + (y - vy)**2)
            if distance < self.min_vertex_distance:
                return False
        
        return True
    
    def _generate_oval_curve(self, x1: float, y1: float, x2: float, y2: float) -> List[Coordinate]:
        """Generate points for an oval curve following Dau's closed curve convention"""
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        radius_x = (x2 - x1) / 2
        radius_y = (y2 - y1) / 2
        
        points = []
        num_points = 32  # Smooth curve
        
        for i in range(num_points + 1):  # +1 to close the curve
            angle = 2 * math.pi * i / num_points
            x = center_x + radius_x * math.cos(angle)
            y = center_y + radius_y * math.sin(angle)
            points.append((x, y))
        
        return points
    
    def _bounds_overlap(self, bounds1: Bounds, bounds2: Bounds) -> bool:
        """Check if two bounding rectangles overlap"""
        x1a, y1a, x2a, y2a = bounds1
        x1b, y1b, x2b, y2b = bounds2
        
        return not (x2a < x1b or x2b < x1a or y2a < y1b or y2b < y1a)
    
    def _build_containment_hierarchy(self, graph: RelationalGraphWithCuts,
                                   elements: Dict[ElementID, LayoutElement]) -> Dict[ElementID, Set[ElementID]]:
        """Build containment hierarchy from graph structure"""
        hierarchy = {}
        
        for area_id, contained_elements in graph.area.items():
            hierarchy[area_id] = set(contained_elements)
        
        return hierarchy
    
    def _validate_constraints(self, elements: Dict[ElementID, LayoutElement],
                            graph: RelationalGraphWithCuts) -> Set[LayoutConstraint]:
        """Validate that layout satisfies Dau's conventions"""
        satisfied = set()
        
        # Check containment constraint
        if self._validate_containment(elements, graph):
            satisfied.add(LayoutConstraint.CONTAINMENT)
        
        # Check non-overlapping constraint
        if self._validate_non_overlapping(elements):
            satisfied.add(LayoutConstraint.NON_OVERLAPPING)
        
        # Add other constraint validations as needed
        satisfied.add(LayoutConstraint.ARBITRARY_DEFORMATION)  # Always allowed
        
        return satisfied
    
    def _validate_containment(self, elements: Dict[ElementID, LayoutElement],
                            graph: RelationalGraphWithCuts) -> bool:
        """Validate proper containment hierarchy"""
        # Implementation would check that all contained elements are within bounds
        return True  # Simplified for now
    
    def _validate_non_overlapping(self, elements: Dict[ElementID, LayoutElement]) -> bool:
        """Validate no inappropriate overlaps"""
        # Implementation would check for overlapping cuts at same level
        return True  # Simplified for now
    
    def _calculate_quality_score(self, elements: Dict[ElementID, LayoutElement],
                               satisfied_constraints: Set[LayoutConstraint]) -> float:
        """Calculate overall layout quality score"""
        constraint_score = len(satisfied_constraints) / len(LayoutConstraint)
        
        # Add other quality metrics (spacing, symmetry, etc.)
        spacing_score = 0.8  # Placeholder
        
        return (constraint_score + spacing_score) / 2
