"""
Clean Layout Engine (Layer 2) - Pure Spatial Reasoning
Translates EGI logical structure to complete spatial primitives.

This is the bridge between abstract EGI data (Layer 1) and visual rendering (Layer 3).
All spatial calculations and positioning logic belongs here.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Set
from egi_core_dau import RelationalGraphWithCuts, ElementID
import math


# Type aliases
Coordinate = Tuple[float, float]
Bounds = Tuple[float, float, float, float]  # (x1, y1, x2, y2)


@dataclass(frozen=True)
class SpatialPrimitive:
    """Complete spatial information for one EGI element."""
    element_id: ElementID
    element_type: str  # 'vertex', 'edge', 'cut'
    position: Coordinate  # Center point
    bounds: Bounds  # (x1, y1, x2, y2) for collision/selection
    z_index: int  # Rendering order (cuts=0, vertices=1, edges=2)
    curve_points: Optional[List[Coordinate]] = None  # For cuts and edge hooks
    attachment_points: Optional[Dict[str, Coordinate]] = None  # For edge connections
    parent_area: Optional[ElementID] = None  # Which area contains this element
    display_name: Optional[str] = None  # Actual display text (predicate name, vertex label)


@dataclass(frozen=True)
class LayoutResult:
    """Complete spatial layout for an entire EGI."""
    primitives: Dict[ElementID, SpatialPrimitive]
    canvas_bounds: Bounds  # Overall diagram bounds
    containment_hierarchy: Dict[ElementID, Set[ElementID]]  # For debugging


class CleanLayoutEngine:
    """
    Pure Layout Engine - translates EGI logical structure to spatial primitives.
    
    Key Principles:
    1. Reads EGI area mapping to determine logical containment
    2. Translates containment to spatial nesting (cuts contain their elements)
    3. Produces complete spatial primitives for rendering
    4. No rendering logic - pure spatial calculations only
    """
    
    def __init__(self, canvas_width: float = 800, canvas_height: float = 600):
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        
        # Dau visual convention parameters
        self.margin = 50.0
        self.vertex_radius = 6.0
        self.min_vertex_spacing = 80.0
        self.cut_padding = 40.0
        self.predicate_offset = 60.0
        self.min_cut_size = 100.0
        
        # Z-index layers for proper rendering order
        self.z_cuts = 0
        self.z_vertices = 1
        self.z_edges = 2
    
    def layout_graph(self, graph: RelationalGraphWithCuts) -> LayoutResult:
        """
        Main entry point: translate EGI to complete spatial primitives.
        
        Process:
        1. Analyze EGI area mapping to build containment hierarchy
        2. Layout cuts with proper nesting (parents contain children)
        3. Layout vertices within their assigned areas
        4. Layout edges within their assigned areas with proper attachment
        5. Return complete spatial primitives
        """
        # Step 1: Build containment hierarchy from EGI area mapping
        containment_hierarchy = self._build_containment_hierarchy(graph)
        
        # Step 2: Layout cuts with hierarchical nesting
        cut_primitives = self._layout_cuts_hierarchical(graph, containment_hierarchy)
        
        # Step 3: Layout vertices within their correct areas
        vertex_primitives = self._layout_vertices_in_areas(graph, cut_primitives)
        
        # Step 4: Layout edges within their correct areas
        edge_primitives = self._layout_edges_in_areas(graph, cut_primitives, vertex_primitives)
        
        # Step 5: Combine all primitives
        all_primitives = {}
        all_primitives.update(cut_primitives)
        all_primitives.update(vertex_primitives)
        all_primitives.update(edge_primitives)
        
        # Calculate overall canvas bounds
        canvas_bounds = self._calculate_canvas_bounds(all_primitives)
        
        return LayoutResult(
            primitives=all_primitives,
            canvas_bounds=canvas_bounds,
            containment_hierarchy=containment_hierarchy
        )
    
    def _build_containment_hierarchy(self, graph: RelationalGraphWithCuts) -> Dict[ElementID, Set[ElementID]]:
        """Build containment hierarchy from EGI area mapping."""
        hierarchy = {}
        
        # Sheet contains its area
        sheet_area = graph.area.get(graph.sheet, frozenset())
        hierarchy[graph.sheet] = set(sheet_area)
        
        # Each cut contains its area
        for cut in graph.Cut:
            cut_area = graph.area.get(cut.id, frozenset())
            hierarchy[cut.id] = set(cut_area)
        
        return hierarchy
    
    def _layout_cuts_hierarchical(self, graph: RelationalGraphWithCuts, 
                                 hierarchy: Dict[ElementID, Set[ElementID]]) -> Dict[ElementID, SpatialPrimitive]:
        """Layout cuts with proper hierarchical nesting."""
        cut_primitives = {}
        
        # Calculate nesting levels
        nesting_levels = self._calculate_nesting_levels(graph, hierarchy)
        
        # Layout cuts level by level (outermost first)
        for level in sorted(nesting_levels.keys()):
            cuts_at_level = nesting_levels[level]
            
            for cut in cuts_at_level:
                parent_area = self._find_parent_area(cut.id, graph)
                cut_primitive = self._layout_single_cut(cut, parent_area, hierarchy, cut_primitives)
                cut_primitives[cut.id] = cut_primitive
        
        return cut_primitives
    
    def _calculate_nesting_levels(self, graph: RelationalGraphWithCuts, 
                                 hierarchy: Dict[ElementID, Set[ElementID]]) -> Dict[int, List]:
        """Calculate nesting depth for each cut."""
        levels = {}
        
        for cut in graph.Cut:
            depth = graph.get_nesting_depth(cut.id)
            if depth not in levels:
                levels[depth] = []
            levels[depth].append(cut)
        
        return levels
    
    def _find_parent_area(self, element_id: ElementID, graph: RelationalGraphWithCuts) -> Optional[ElementID]:
        """Find which area directly contains this element."""
        # Check sheet first
        if element_id in graph.area.get(graph.sheet, frozenset()):
            return graph.sheet
        
        # Check each cut
        for cut in graph.Cut:
            if element_id in graph.area.get(cut.id, frozenset()):
                return cut.id
        
        return None
    
    def _layout_single_cut(self, cut, parent_area: Optional[ElementID], 
                          hierarchy: Dict[ElementID, Set[ElementID]],
                          existing_cuts: Dict[ElementID, SpatialPrimitive]) -> SpatialPrimitive:
        """Layout a single cut within its parent area."""
        
        # Determine available space
        if parent_area and parent_area in existing_cuts:
            # Cut is nested inside another cut
            parent_bounds = existing_cuts[parent_area].bounds
            x1, y1, x2, y2 = parent_bounds
            available_bounds = (
                x1 + self.cut_padding,
                y1 + self.cut_padding,
                x2 - self.cut_padding,
                y2 - self.cut_padding
            )
        else:
            # Cut is at sheet level
            available_bounds = (
                self.margin,
                self.margin,
                self.canvas_width - self.margin,
                self.canvas_height - self.margin
            )
        
        # Calculate cut size based on contents
        contents = hierarchy.get(cut.id, set())
        cut_width, cut_height = self._calculate_cut_size(contents)
        
        # Position cut within available space
        position = self._find_non_overlapping_position(
            cut_width, cut_height, available_bounds, existing_cuts, parent_area
        )
        
        # Create cut bounds
        x, y = position
        bounds = (x - cut_width/2, y - cut_height/2, x + cut_width/2, y + cut_height/2)
        
        # Generate curve points for cut boundary (following Dau's fine-drawn curve convention)
        curve_points = self._generate_cut_curve(bounds)
        
        return SpatialPrimitive(
            element_id=cut.id,
            element_type='cut',
            position=position,
            bounds=bounds,
            z_index=self.z_cuts,
            curve_points=curve_points,
            parent_area=parent_area
        )
    
    def _calculate_cut_size(self, contents: Set[ElementID]) -> Tuple[float, float]:
        """Calculate appropriate size for a cut based on its contents."""
        # Base size
        width = self.min_cut_size
        height = self.min_cut_size
        
        # Expand based on number of contents
        content_count = len(contents)
        if content_count > 0:
            # Rough estimate - will be refined in actual layout
            width += content_count * 30
            height += content_count * 20
        
        return width, height
    
    def _find_non_overlapping_position(self, width: float, height: float, 
                                      available_bounds: Bounds,
                                      existing_cuts: Dict[ElementID, SpatialPrimitive],
                                      parent_area: Optional[ElementID]) -> Coordinate:
        """Find position that doesn't overlap with sibling cuts."""
        x1, y1, x2, y2 = available_bounds
        
        # Simple grid-based positioning
        grid_size = 120
        for grid_y in range(int(y1 + height/2), int(y2 - height/2), grid_size):
            for grid_x in range(int(x1 + width/2), int(x2 - width/2), grid_size):
                test_bounds = (grid_x - width/2, grid_y - height/2, 
                              grid_x + width/2, grid_y + height/2)
                
                # Check for overlaps with siblings
                overlaps = False
                for cut_primitive in existing_cuts.values():
                    if cut_primitive.parent_area == parent_area:
                        if self._bounds_overlap(test_bounds, cut_primitive.bounds):
                            overlaps = True
                            break
                
                if not overlaps:
                    return (grid_x, grid_y)
        
        # Fallback to center of available space
        return ((x1 + x2) / 2, (y1 + y2) / 2)
    
    def _bounds_overlap(self, bounds1: Bounds, bounds2: Bounds) -> bool:
        """Check if two bounding boxes overlap."""
        x1a, y1a, x2a, y2a = bounds1
        x1b, y1b, x2b, y2b = bounds2
        return not (x2a <= x1b or x2b <= x1a or y2a <= y1b or y2b <= y1a)
    
    def _generate_cut_curve(self, bounds: Bounds) -> List[Coordinate]:
        """Generate curve points for cut boundary (Dau's circular convention)."""
        x1, y1, x2, y2 = bounds
        
        # Calculate center and radii for ellipse
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        radius_x = (x2 - x1) / 2
        radius_y = (y2 - y1) / 2
        
        # Generate elliptical curve points
        import math
        points = []
        num_points = 32  # Smooth circle with 32 points
        
        for i in range(num_points + 1):  # +1 to close the curve
            angle = 2 * math.pi * i / num_points
            x = center_x + radius_x * math.cos(angle)
            y = center_y + radius_y * math.sin(angle)
            points.append((x, y))
        
        return points
    
    def _layout_vertices_in_areas(self, graph: RelationalGraphWithCuts,
                                 cut_primitives: Dict[ElementID, SpatialPrimitive]) -> Dict[ElementID, SpatialPrimitive]:
        """Layout vertices within their assigned areas from EGI."""
        vertex_primitives = {}
        
        for vertex in graph.V:
            # CRITICAL: Use EGI area mapping to find containing area
            containing_area = self._find_parent_area(vertex.id, graph)
            
            # Get available space within containing area
            if containing_area and containing_area in cut_primitives:
                container_bounds = cut_primitives[containing_area].bounds
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
            position = self._find_vertex_position(vertex, available_bounds, vertex_primitives)
            
            # Create vertex primitive
            bounds = (
                position[0] - self.vertex_radius,
                position[1] - self.vertex_radius,
                position[0] + self.vertex_radius,
                position[1] + self.vertex_radius
            )
            
            vertex_primitives[vertex.id] = SpatialPrimitive(
                element_id=vertex.id,
                element_type='vertex',
                position=position,
                bounds=bounds,
                z_index=self.z_vertices,
                parent_area=containing_area
            )
        
        return vertex_primitives
    
    def _find_vertex_position(self, vertex, available_bounds: Bounds,
                             existing_vertices: Dict[ElementID, SpatialPrimitive]) -> Coordinate:
        """Find position for vertex within available space, avoiding cut line crossings."""
        x1, y1, x2, y2 = available_bounds
        
        # For vertices at sheet level, prefer positions that minimize cut crossings
        # Position vertices towards edges of available space to avoid crossing cuts
        if self._is_sheet_level_vertex(vertex, available_bounds):
            # Try edge positions first (left, right, top, bottom of available space)
            edge_positions = [
                (x1 + 20, (y1 + y2) / 2),  # Left edge
                (x2 - 20, (y1 + y2) / 2),  # Right edge  
                ((x1 + x2) / 2, y1 + 20),  # Top edge
                ((x1 + x2) / 2, y2 - 20),  # Bottom edge
            ]
            
            for pos_x, pos_y in edge_positions:
                if self._is_position_valid(pos_x, pos_y, existing_vertices):
                    return (pos_x, pos_y)
        
        # Fallback to grid positioning
        grid_size = int(self.min_vertex_spacing)
        for grid_y in range(int(y1), int(y2), grid_size):
            for grid_x in range(int(x1), int(x2), grid_size):
                # Check minimum distance from existing vertices
                too_close = False
                for existing in existing_vertices.values():
                    if existing.parent_area == vertex.id:  # Same area
                        dist = math.sqrt((grid_x - existing.position[0])**2 + 
                                       (grid_y - existing.position[1])**2)
                        if dist < self.min_vertex_spacing:
                            too_close = True
                            break
                
                if not too_close:
                    return (grid_x, grid_y)
        
        # Fallback
        return ((x1 + x2) / 2, (y1 + y2) / 2)
    
    def _layout_edges_in_areas(self, graph: RelationalGraphWithCuts,
                              cut_primitives: Dict[ElementID, SpatialPrimitive],
                              vertex_primitives: Dict[ElementID, SpatialPrimitive]) -> Dict[ElementID, SpatialPrimitive]:
        """Layout edges within their assigned areas from EGI."""
        edge_primitives = {}
        
        # Group edges by their containing area for better spatial separation
        edges_by_area = {}
        for edge in graph.E:
            containing_area = self._find_parent_area(edge.id, graph)
            if containing_area not in edges_by_area:
                edges_by_area[containing_area] = []
            edges_by_area[containing_area].append(edge)
        
        # Layout edges area by area
        for containing_area, edges_in_area in edges_by_area.items():
            # Get available space within containing area
            if containing_area and containing_area in cut_primitives:
                # Edge is inside a cut
                container_bounds = cut_primitives[containing_area].bounds
                x1, y1, x2, y2 = container_bounds
                available_bounds = (
                    x1 + self.cut_padding/2,
                    y1 + self.cut_padding/2,
                    x2 - self.cut_padding/2,
                    y2 - self.cut_padding/2
                )
            else:
                # Edge is at sheet level - must be positioned OUTSIDE all cuts
                available_bounds = self._get_sheet_level_bounds(cut_primitives)
            
            # Layout edges in this area with proper separation
            for i, edge in enumerate(edges_in_area):
                # Get incident vertices
                vertex_sequence = graph.nu.get(edge.id, ())
                vertex_positions = []
                for vertex_id in vertex_sequence:
                    if vertex_id in vertex_primitives:
                        vertex_positions.append(vertex_primitives[vertex_id].position)
                
                if not vertex_positions:
                    continue  # Skip edges with no positioned vertices
                
                # Calculate predicate position with collision avoidance
                if len(vertex_positions) == 1:
                    # Unary predicate - avoid line overlaps
                    position = self._calculate_collision_free_predicate_position(
                        vertex_positions[0], available_bounds, edge_primitives,
                        cut_primitives, vertex_primitives, containing_area
                    )
                else:
                    # Multi-ary predicate
                    position = self._calculate_multiary_predicate_position_with_separation(
                        vertex_positions, available_bounds, edge_primitives,
                        containing_area, i, len(edges_in_area)
                    )
                
                # Create edge primitive
                bounds = (
                    position[0] - 40, position[1] - 15,
                    position[0] + 40, position[1] + 15
                )
                
                # Create attachment points for hooks
                attachment_points = {}
                for j, vertex_pos in enumerate(vertex_positions):
                    attachment_points[f"vertex_{j}"] = vertex_pos
                
                edge_primitives[edge.id] = SpatialPrimitive(
                    element_id=edge.id,
                    element_type='edge',
                    position=position,
                    bounds=bounds,
                    z_index=self.z_edges,
                    attachment_points=attachment_points,
                    curve_points=vertex_positions,  # For hook rendering
                    parent_area=containing_area
                )
        
        return edge_primitives
    
    def _calculate_unary_predicate_position_with_separation(self, vertex_pos: Coordinate, 
                                                           available_bounds: Bounds,
                                                           existing_edges: Dict[ElementID, SpatialPrimitive],
                                                           containing_area: Optional[ElementID],
                                                           predicate_index: int,
                                                           total_predicates: int) -> Coordinate:
        """Calculate position for unary predicate with separation from other predicates in same area."""
        vertex_x, vertex_y = vertex_pos
        x1, y1, x2, y2 = available_bounds
        
        if total_predicates == 1:
            # Single predicate - position to the right of vertex
            pred_x = min(vertex_x + self.predicate_offset, x2 - 50)
            pred_y = vertex_y
        else:
            # Multiple predicates - arrange in a fan pattern with good separation
            import math
            angle_step = 2 * math.pi / max(total_predicates, 3)  # Minimum 3 positions for good spread
            angle = predicate_index * angle_step
            
            # Use larger offset for better separation
            separation_distance = self.predicate_offset * 1.5
            pred_x = vertex_x + separation_distance * math.cos(angle)
            pred_y = vertex_y + separation_distance * math.sin(angle)
        
        # Clamp to area bounds
        pred_x = max(x1 + 50, min(x2 - 50, pred_x))
        pred_y = max(y1 + 20, min(y2 - 20, pred_y))
        
        # Avoid collisions with existing predicates in same area
        pred_x, pred_y = self._avoid_predicate_collisions(
            (pred_x, pred_y), existing_edges, containing_area, available_bounds
        )
        
        return (pred_x, pred_y)
    
    def _calculate_multiary_predicate_position_with_separation(self, vertex_positions: List[Coordinate],
                                                              available_bounds: Bounds,
                                                              existing_edges: Dict[ElementID, SpatialPrimitive],
                                                              containing_area: Optional[ElementID],
                                                              predicate_index: int,
                                                              total_predicates: int) -> Coordinate:
        """Calculate position for multi-ary predicate with separation from other predicates."""
        # Center between vertices
        center_x = sum(pos[0] for pos in vertex_positions) / len(vertex_positions)
        center_y = sum(pos[1] for pos in vertex_positions) / len(vertex_positions)
        
        # Add offset for separation if multiple predicates in same area
        if total_predicates > 1:
            offset_distance = 40 * predicate_index  # Stagger predicates
            center_y += offset_distance
        
        # Clamp to area bounds
        x1, y1, x2, y2 = available_bounds
        pred_x = max(x1 + 50, min(x2 - 50, center_x))
        pred_y = max(y1 + 20, min(y2 - 20, center_y))
        
        # Avoid collisions
        pred_x, pred_y = self._avoid_predicate_collisions(
            (pred_x, pred_y), existing_edges, containing_area, available_bounds
        )
        
        return (pred_x, pred_y)
    
    def _avoid_predicate_collisions(self, position: Coordinate,
                                   existing_edges: Dict[ElementID, SpatialPrimitive],
                                   containing_area: Optional[ElementID],
                                   available_bounds: Bounds) -> Coordinate:
        """Avoid collisions with existing predicates in the same area."""
        pred_x, pred_y = position
        x1, y1, x2, y2 = available_bounds
        
        # Check for collisions with predicates in same area
        min_distance = 80  # Minimum distance between predicates
        max_attempts = 10  # Prevent infinite loops
        
        for attempt in range(max_attempts):
            collision_found = False
            
            for existing_edge in existing_edges.values():
                if existing_edge.parent_area == containing_area:
                    ex_x, ex_y = existing_edge.position
                    distance = math.sqrt((pred_x - ex_x)**2 + (pred_y - ex_y)**2)
                    
                    if distance < min_distance:
                        collision_found = True
                        # Move away from collision with more aggressive adjustment
                        dx = pred_x - ex_x
                        dy = pred_y - ex_y
                        
                        if abs(dx) < 1 and abs(dy) < 1:
                            # If positions are nearly identical, use a default offset
                            pred_x += min_distance
                            pred_y += 30
                        else:
                            # Normalize and scale the displacement vector
                            length = math.sqrt(dx*dx + dy*dy)
                            if length > 0:
                                dx /= length
                                dy /= length
                                pred_x = ex_x + dx * min_distance
                                pred_y = ex_y + dy * min_distance
                        
                        # Clamp to bounds
                        pred_x = max(x1 + 50, min(x2 - 50, pred_x))
                        pred_y = max(y1 + 20, min(y2 - 20, pred_y))
                        break
            
            if not collision_found:
                break
        
        return (pred_x, pred_y)
    
    def _is_sheet_level_vertex(self, vertex, available_bounds: Bounds) -> bool:
        """Check if vertex is at sheet level (not inside a cut)."""
        # If available_bounds spans most of the canvas, it's likely sheet level
        x1, y1, x2, y2 = available_bounds
        canvas_area = self.canvas_width * self.canvas_height
        bounds_area = (x2 - x1) * (y2 - y1)
        return bounds_area > 0.5 * canvas_area  # More than 50% of canvas = sheet level
    
    def _is_position_valid(self, x: float, y: float, existing_vertices: Dict[ElementID, SpatialPrimitive]) -> bool:
        """Check if position is valid (not too close to existing vertices)."""
        for existing_primitive in existing_vertices.values():
            ex_x, ex_y = existing_primitive.position
            distance = ((x - ex_x) ** 2 + (y - ex_y) ** 2) ** 0.5
            if distance < self.min_vertex_spacing:
                return False
        return True
    
    def _calculate_collision_free_predicate_position(self, vertex_pos: Coordinate, 
                                                   available_bounds: Bounds,
                                                   existing_edges: Dict[ElementID, SpatialPrimitive],
                                                   cut_primitives: Dict[ElementID, SpatialPrimitive],
                                                   vertex_primitives: Dict[ElementID, SpatialPrimitive],
                                                   containing_area: ElementID) -> Coordinate:
        """Calculate predicate position that avoids line overlaps with other elements."""
        x1, y1, x2, y2 = available_bounds
        vertex_x, vertex_y = vertex_pos
        
        # IMPROVED: Better separation strategy for multiple predicates on same vertex
        import math
        
        # Filter existing edges to only those in the same area
        same_area_edges = {
            eid: primitive for eid, primitive in existing_edges.items()
            if primitive.parent_area == containing_area
        }
        
        # Start with larger minimum distance for better separation
        min_distance = 80  # Increased from 40
        max_distance = 120
        angle_step = 45  # Try every 45 degrees for good spread
        
        # Try positions in a systematic pattern
        for distance in range(min_distance, max_distance + 1, 20):
            for angle_deg in range(0, 360, angle_step):
                angle_rad = math.radians(angle_deg)
                pred_x = vertex_x + distance * math.cos(angle_rad)
                pred_y = vertex_y + distance * math.sin(angle_rad)
                
                # Check if position is within bounds with margin
                margin = 20
                if not (x1 + margin <= pred_x <= x2 - margin and y1 + margin <= pred_y <= y2 - margin):
                    continue
                
                # Check minimum distance to existing predicates in same area
                min_dist_ok = True
                for existing_primitive in same_area_edges.values():
                    dist = math.sqrt((pred_x - existing_primitive.position[0])**2 + 
                                   (pred_y - existing_primitive.position[1])**2)
                    if dist < 80:  # Minimum 80 pixels between predicates
                        min_dist_ok = False
                        break
                
                if min_dist_ok:
                    # Check if the line from vertex to predicate would overlap other elements
                    if self._is_line_collision_free(vertex_pos, (pred_x, pred_y), 
                                                  existing_edges, cut_primitives, vertex_primitives):
                        return (pred_x, pred_y)
        
        # IMPROVED FALLBACK: If strict collision-free fails, try with relaxed constraints
        print(f"DEBUG: Strict collision-free failed, trying relaxed constraints")
        
        # Try again with smaller minimum distance
        for distance in range(60, 100, 10):  # Smaller distances
            for angle_deg in range(0, 360, 30):  # More angles
                angle_rad = math.radians(angle_deg)
                pred_x = vertex_x + distance * math.cos(angle_rad)
                pred_y = vertex_y + distance * math.sin(angle_rad)
                
                # Check bounds with smaller margin
                margin = 10
                if not (x1 + margin <= pred_x <= x2 - margin and y1 + margin <= pred_y <= y2 - margin):
                    continue
                
                # Check relaxed minimum distance (50 pixels instead of 80)
                min_dist_ok = True
                for existing_primitive in same_area_edges.values():
                    dist = math.sqrt((pred_x - existing_primitive.position[0])**2 + 
                                   (pred_y - existing_primitive.position[1])**2)
                    if dist < 50:  # Relaxed minimum
                        min_dist_ok = False
                        break
                
                if min_dist_ok:
                    return (pred_x, pred_y)
        
        # Final fallback: ensure at least some separation
        print(f"DEBUG: All collision-free attempts failed, using guaranteed separation")
        num_existing = len(same_area_edges)
        angle_offset = (num_existing * 90) % 360  # Spread predicates by 90 degrees for better separation
        angle_rad = math.radians(angle_offset)
        distance = 90  # Increased guaranteed minimum distance
        
        pred_x = vertex_x + distance * math.cos(angle_rad)
        pred_y = vertex_y + distance * math.sin(angle_rad)
        
        # Clamp to bounds
        pred_x = max(x1 + 10, min(x2 - 10, pred_x))
        pred_y = max(y1 + 10, min(y2 - 10, pred_y))
        
        return (pred_x, pred_y)
    
    def _is_line_collision_free(self, start: Coordinate, end: Coordinate,
                               existing_edges: Dict[ElementID, SpatialPrimitive],
                               cut_primitives: Dict[ElementID, SpatialPrimitive],
                               vertex_primitives: Dict[ElementID, SpatialPrimitive]) -> bool:
        """Check if a line from start to end would collide with other elements."""
        # Check collision with existing predicate positions
        for edge_primitive in existing_edges.values():
            if self._line_intersects_point(start, end, edge_primitive.position, radius=15):
                return False
        
        # Check collision with cut boundaries (simplified - check if line crosses cut center)
        for cut_primitive in cut_primitives.values():
            cut_center = (
                (cut_primitive.bounds[0] + cut_primitive.bounds[2]) / 2,
                (cut_primitive.bounds[1] + cut_primitive.bounds[3]) / 2
            )
            if self._line_intersects_point(start, end, cut_center, radius=20):
                return False
        
        # Check collision with other vertices (avoid lines crossing through vertices)
        for vertex_primitive in vertex_primitives.values():
            if vertex_primitive.position != start:  # Don't check against the starting vertex
                if self._line_intersects_point(start, end, vertex_primitive.position, radius=10):
                    return False
        
        return True
    
    def _line_intersects_point(self, line_start: Coordinate, line_end: Coordinate, 
                              point: Coordinate, radius: float) -> bool:
        """Check if a line segment comes too close to a point (within radius)."""
        x1, y1 = line_start
        x2, y2 = line_end
        px, py = point
        
        # Calculate distance from point to line segment
        # Vector from line start to end
        dx = x2 - x1
        dy = y2 - y1
        
        if dx == 0 and dy == 0:
            # Line is just a point
            distance = ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
        else:
            # Parameter t for closest point on line
            t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
            
            # Closest point on line segment
            closest_x = x1 + t * dx
            closest_y = y1 + t * dy
            
            # Distance from point to closest point on line
            distance = ((px - closest_x) ** 2 + (py - closest_y) ** 2) ** 0.5
        
        return distance < radius
    
    def _get_sheet_level_bounds(self, cut_primitives: Dict[ElementID, SpatialPrimitive]) -> Bounds:
        """Calculate available bounds for sheet-level elements, avoiding all cuts."""
        # Start with full canvas bounds
        sheet_bounds = (
            self.margin,
            self.margin,
            self.canvas_width - self.margin,
            self.canvas_height - self.margin
        )
        
        if not cut_primitives:
            return sheet_bounds
        
        # Find the rightmost cut boundary
        max_cut_right = 0
        max_cut_bottom = 0
        
        for cut_primitive in cut_primitives.values():
            x1, y1, x2, y2 = cut_primitive.bounds
            max_cut_right = max(max_cut_right, x2)
            max_cut_bottom = max(max_cut_bottom, y2)
        
        # Position sheet-level elements to the right of all cuts
        sheet_x_start = max_cut_right + self.cut_padding
        
        # If there's not enough space to the right, use area above cuts
        if sheet_x_start + 100 > self.canvas_width - self.margin:
            # Use area above cuts
            min_cut_top = min(cut_primitive.bounds[1] for cut_primitive in cut_primitives.values())
            sheet_bounds = (
                self.margin,
                self.margin,
                self.canvas_width - self.margin,
                min_cut_top - self.cut_padding
            )
        else:
            # Use area to the right of cuts
            sheet_bounds = (
                sheet_x_start,
                self.margin,
                self.canvas_width - self.margin,
                self.canvas_height - self.margin
            )
        
        return sheet_bounds
    
    # Legacy methods for backward compatibility
    def _calculate_unary_predicate_position(self, vertex_pos: Coordinate, 
                                           available_bounds: Bounds,
                                           existing_edges: Dict[ElementID, SpatialPrimitive]) -> Coordinate:
        """Legacy method - use the new separation method instead."""
        return self._calculate_unary_predicate_position_with_separation(
            vertex_pos, available_bounds, existing_edges, None, 0, 1
        )
    
    def _calculate_multiary_predicate_position(self, vertex_positions: List[Coordinate],
                                              available_bounds: Bounds) -> Coordinate:
        """Legacy method - use the new separation method instead."""
        return self._calculate_multiary_predicate_position_with_separation(
            vertex_positions, available_bounds, {}, None, 0, 1
        )
    
    def _calculate_canvas_bounds(self, primitives: Dict[ElementID, SpatialPrimitive]) -> Bounds:
        """Calculate overall canvas bounds containing all primitives."""
        if not primitives:
            return (0, 0, self.canvas_width, self.canvas_height)
        
        min_x = min(p.bounds[0] for p in primitives.values())
        min_y = min(p.bounds[1] for p in primitives.values())
        max_x = max(p.bounds[2] for p in primitives.values())
        max_y = max(p.bounds[3] for p in primitives.values())
        
        # Add margin
        return (min_x - self.margin, min_y - self.margin, 
                max_x + self.margin, max_y + self.margin)
