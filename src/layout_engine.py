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
        self.min_vertex_distance = 70.0  # Increased for clear separation
        self.cut_padding = 50.0  # Increased for clear boundaries
        self.line_thickness = 3.0  # Heavy lines for identity
        self.cut_line_thickness = 1.0  # Fine lines for cuts
        
        # Significantly increased spacing for clear selection and manipulation
        self.predicate_offset_distance = 80.0  # Distance from vertex to predicate
        self.predicate_spacing = 60.0  # Spacing between multiple predicates
        self.min_element_separation = 50.0  # Minimum distance between any elements
        
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
        
        # Group edges by their incident vertices to handle multiple predicates per vertex
        vertex_edge_groups = {}
        for edge in graph.E:
            vertex_ids = graph.nu.get(edge.id, [])
            if len(vertex_ids) == 1:
                # Unary predicate
                vertex_id = vertex_ids[0]
                if vertex_id not in vertex_edge_groups:
                    vertex_edge_groups[vertex_id] = []
                vertex_edge_groups[vertex_id].append(edge)
        
        for edge in graph.E:
            # Get vertex positions for this edge
            vertex_positions = []
            vertex_ids = graph.nu.get(edge.id, [])
            for vertex_id in vertex_ids:
                if vertex_id in all_layouts:
                    vertex_positions.append(all_layouts[vertex_id].position)
            
            if len(vertex_positions) < 1:
                continue  # Skip edges without any vertex connections
            
            if len(vertex_positions) == 1:
                # UNARY PREDICATE - AREA-CENTRIC POSITIONING FIX
                # Position predicate based on its logical area assignment, not vertex proximity
                vertex_pos = vertex_positions[0]
                vertex_id = vertex_ids[0]
                
                # Find which area contains this edge
                edge_containing_area = self._find_parent_area(edge.id, graph)
                
                # CRITICAL: Position predicate within its assigned area bounds
                predicate_position = self._position_predicate_by_area(
                    edge, edge_containing_area, all_layouts
                )
                
                # Create bounds around predicate position (not vertex)
                pred_x, pred_y = predicate_position
                min_x, max_x = pred_x - 40, pred_x + 40  # Wider for text and selection
                min_y, max_y = pred_y - 15, pred_y + 15  # Taller for text and selection
                
                # Create attachment points for hooks
                attachment_points = {"vertex_0": vertex_pos}
                
                edge_layouts[edge.id] = LayoutElement(
                    element_id=edge.id,
                    element_type='edge',
                    position=predicate_position,
                    bounds=(min_x, min_y, max_x, max_y),
                    parent_area=edge_containing_area,  # CRITICAL: Set correct parent area
                    attachment_points=attachment_points,
                    curve_points=[vertex_pos]  # For hook rendering
                )
            else:
                # Multi-ary predicate - position between vertices within correct area
                # CRITICAL FIX: Find which area contains this edge
                edge_containing_area = self._find_parent_area(edge.id, graph)
                
                # Get available space within the edge's containing area
                if edge_containing_area and edge_containing_area in all_layouts:
                    container_bounds = all_layouts[edge_containing_area].bounds
                    # Inset from container bounds
                    x1, y1, x2, y2 = container_bounds
                    available_bounds = (
                        x1 + self.cut_padding,
                        y1 + self.cut_padding,
                        x2 - self.cut_padding,
                        y2 - self.cut_padding
                    )
                else:
                    # Sheet level - use full canvas
                    available_bounds = (
                        self.margin,
                        self.margin,
                        self.canvas_width - self.margin,
                        self.canvas_height - self.margin
                    )
                
                # Calculate center position between vertices
                center_x = sum(pos[0] for pos in vertex_positions) / len(vertex_positions)
                center_y = sum(pos[1] for pos in vertex_positions) / len(vertex_positions)
                
                # Offset slightly to avoid overlap with vertices, within area bounds
                x1, y1, x2, y2 = available_bounds
                offset_x = max(x1 + 50, min(x2 - 50, center_x))
                offset_y = max(y1 + 20, min(y2 - 20, center_y - self.predicate_offset_distance / 2))
                
                # Create bounds around predicate position
                min_x = offset_x - 40
                max_x = offset_x + 40
                min_y = offset_y - 15
                max_y = offset_y + 15
                
                # Create attachment points for hooks
                attachment_points = {}
                for i, pos in enumerate(vertex_positions):
                    attachment_points[f"vertex_{i}"] = pos
                
                edge_layouts[edge.id] = LayoutElement(
                    element_id=edge.id,
                    element_type='edge',
                    position=(offset_x, offset_y),
                    bounds=(min_x, min_y, max_x, max_y),
                    parent_area=edge_containing_area,  # CRITICAL: Set correct parent area
                    attachment_points=attachment_points,
                    curve_points=vertex_positions  # Line segments connecting vertices
                )
        
        return edge_layouts
    
    def _calculate_predicate_position(self, vertex_pos: Coordinate, predicate_index: int, 
                                     total_predicates: int, all_layouts: Dict[ElementID, LayoutElement]) -> Coordinate:
        """Calculate optimal position for a predicate to avoid overlap with vertex and other elements"""
        vertex_x, vertex_y = vertex_pos
        
        if total_predicates == 1:
            # Single predicate - position to the right of vertex
            pred_x = vertex_x + self.predicate_offset_distance
            pred_y = vertex_y
        else:
            # Multiple predicates - arrange in a fan pattern around vertex
            angle_step = 2 * 3.14159 / total_predicates  # Distribute around circle
            angle = predicate_index * angle_step
            
            # Position at offset distance from vertex
            import math
            pred_x = vertex_x + self.predicate_offset_distance * math.cos(angle)
            pred_y = vertex_y + self.predicate_offset_distance * math.sin(angle)
        
        # Check for collisions with existing elements and adjust if necessary
        pred_x, pred_y = self._avoid_element_collisions(
            (pred_x, pred_y), all_layouts, exclude_types={'vertex'}
        )
        
        return (pred_x, pred_y)
    
    def _position_predicate_by_area(self, edge, edge_containing_area, all_layouts: Dict[ElementID, LayoutElement]) -> Coordinate:
        """Position predicate based on its logical area assignment (area-centric approach)"""
        
        # Get available space for this area
        if edge_containing_area and edge_containing_area in all_layouts:
            container_bounds = all_layouts[edge_containing_area].bounds
            x1, y1, x2, y2 = container_bounds
            
            # Validate and fix container bounds
            if x2 <= x1 or y2 <= y1:
                print(f"FIXING: Invalid container bounds for area {edge_containing_area}: {container_bounds}")
                # Fix invalid bounds by ensuring minimum dimensions
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                min_width = 60  # Minimum cut width
                min_height = 40  # Minimum cut height
                
                x1 = center_x - min_width / 2
                x2 = center_x + min_width / 2
                y1 = center_y - min_height / 2
                y2 = center_y + min_height / 2
                
                container_bounds = (x1, y1, x2, y2)
                print(f"FIXED: Container bounds now: {container_bounds}")
            
            # Calculate safe area for predicate placement (for both fixed and valid bounds)
            width = x2 - x1
            height = y2 - y1
            safe_padding = min(width / 6, height / 6, 10)
            
            available_bounds = (
                x1 + safe_padding,
                y1 + safe_padding,
                x2 - safe_padding,
                y2 - safe_padding
            )
        else:
            # Sheet level - use full canvas
            available_bounds = (
                self.margin,
                self.margin,
                self.canvas_width - self.margin,
                self.canvas_height - self.margin
            )
        
        # Position predicate within the area bounds
        ax1, ay1, ax2, ay2 = available_bounds
        
        # Validate available bounds
        if ax2 <= ax1 or ay2 <= ay1:
            # Use center as fallback
            return ((ax1 + ax2) / 2, (ay1 + ay2) / 2)
        
        # ENHANCED COLLISION AVOIDANCE: Better spacing and separation
        # Calculate available space for proper spacing
        available_width = ax2 - ax1
        available_height = ay2 - ay1
        
        # Use larger spacing to prevent overlapping
        min_predicate_spacing = 60  # Minimum distance between predicates
        
        # Position predicate with improved spacing logic
        if available_width > min_predicate_spacing and available_height > min_predicate_spacing:
            # Use grid-based positioning for better collision avoidance
            area_hash = hash(str(edge_containing_area)) if edge_containing_area else hash(str(edge.id))
            
            # Create multiple positioning slots within the area
            slots_x = max(2, int(available_width // min_predicate_spacing))
            slots_y = max(2, int(available_height // min_predicate_spacing))
            
            slot_x = (area_hash % slots_x)
            slot_y = ((area_hash // slots_x) % slots_y)
            
            pred_x = ax1 + (slot_x + 0.5) * (available_width / slots_x)
            pred_y = ay1 + (slot_y + 0.5) * (available_height / slots_y)
        else:
            # Fallback for small areas - use center with small offset
            pred_x = ax1 + available_width * 0.5
            pred_y = ay1 + available_height * 0.5
            
            # Small random offset to avoid exact overlap
            area_hash = hash(str(edge_containing_area)) if edge_containing_area else hash(str(edge.id))
            offset_x = (area_hash % 20) - 10
            offset_y = ((area_hash // 20) % 20) - 10
            
            pred_x += offset_x
            pred_y += offset_y
        
        # Ensure final position is within bounds
        pred_x = max(ax1 + 5, min(ax2 - 5, pred_x))
        pred_y = max(ay1 + 5, min(ay2 - 5, pred_y))
        
        return (pred_x, pred_y)
    
    def _calculate_predicate_position_in_area(self, vertex_pos: Coordinate, predicate_index: int,
                                             total_predicates: int, available_bounds: Bounds,
                                             all_layouts: Dict[ElementID, LayoutElement]) -> Coordinate:
        """Calculate predicate position within a specific area (cut or sheet)"""
        vertex_x, vertex_y = vertex_pos
        x1, y1, x2, y2 = available_bounds
        
        # Ensure vertex is within available bounds (it should be if area containment is correct)
        if not (x1 <= vertex_x <= x2 and y1 <= vertex_y <= y2):
            # Vertex is outside the area - this indicates a structural problem
            # For now, clamp vertex to area bounds
            vertex_x = max(x1, min(x2, vertex_x))
            vertex_y = max(y1, min(y2, vertex_y))
        
        if total_predicates == 1:
            # Single predicate - position to the right of vertex, within bounds
            pred_x = min(vertex_x + self.predicate_offset_distance, x2 - 50)
            pred_y = vertex_y
            
            # Ensure predicate is within area bounds
            pred_x = max(x1 + 50, min(x2 - 50, pred_x))
            pred_y = max(y1 + 20, min(y2 - 20, pred_y))
        else:
            # Multiple predicates - arrange in a fan pattern around vertex, within bounds
            angle_step = 2 * 3.14159 / total_predicates
            angle = predicate_index * angle_step
            
            # Calculate initial position
            import math
            offset_x = self.predicate_offset_distance * math.cos(angle)
            offset_y = self.predicate_offset_distance * math.sin(angle)
            
            pred_x = vertex_x + offset_x
            pred_y = vertex_y + offset_y
            
            # Clamp to area bounds
            pred_x = max(x1 + 50, min(x2 - 50, pred_x))
            pred_y = max(y1 + 20, min(y2 - 20, pred_y))
        
        # Check for collisions and adjust if necessary
        pred_x, pred_y = self._avoid_element_collisions(
            (pred_x, pred_y), all_layouts, exclude_types={'vertex'}
        )
        
        # Final bounds check after collision avoidance
        pred_x = max(x1 + 50, min(x2 - 50, pred_x))
        pred_y = max(y1 + 20, min(y2 - 20, pred_y))
        
        return (pred_x, pred_y)
    
    def _avoid_element_collisions(self, position: Coordinate, 
                                 all_layouts: Dict[ElementID, LayoutElement],
                                 exclude_types: set = None) -> Coordinate:
        """Adjust position to avoid collisions with existing elements"""
        if exclude_types is None:
            exclude_types = set()
        
        x, y = position
        max_attempts = 20
        attempt = 0
        
        while attempt < max_attempts:
            collision = False
            
            # Check for collisions with existing elements
            for element in all_layouts.values():
                if element.element_type in exclude_types:
                    continue
                    
                # Calculate distance to element center
                elem_x, elem_y = element.position
                distance = ((x - elem_x) ** 2 + (y - elem_y) ** 2) ** 0.5
                
                if distance < self.min_element_separation:
                    collision = True
                    # Move away from collision
                    if distance > 0:
                        # Move in opposite direction
                        move_x = (x - elem_x) / distance * self.min_element_separation
                        move_y = (y - elem_y) / distance * self.min_element_separation
                        x = elem_x + move_x
                        y = elem_y + move_y
                    else:
                        # Same position - move arbitrarily
                        x += self.min_element_separation
                    break
            
            if not collision:
                break
                
            attempt += 1
        
        return (x, y)
    
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
