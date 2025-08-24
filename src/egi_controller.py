#!/usr/bin/env python3
"""
Platform-Independent EGI Controller

This controller manages the correspondence between logical EGI and spatial representation
without any GUI framework dependencies. It can be used with Qt, web, CLI, or any other
presentation layer.

Key Principles:
1. Platform agnostic - no GUI framework imports
2. Pure business logic coordination
3. Clean separation between model and view
4. Supports multiple presentation layers simultaneously
"""

from typing import Dict, List, Optional, Tuple, Any, Protocol, Set
from dataclasses import dataclass
from abc import ABC, abstractmethod

from egi_system import EGISystem, OperationResult
from egi_spatial_correspondence import (
    create_spatial_correspondence_engine,
    SpatialCorrespondenceEngine,
    SpatialElement,
    SpatialBounds
)
from networkx_spatial_layout import NetworkXEGILayoutEngine
from logic_spatial_validator import create_validator, ValidationResult


class PresentationAdapter(Protocol):
    """Protocol for platform-specific presentation adapters."""
    
    def render_scene(self, render_commands: List[Dict[str, Any]]) -> None:
        """Render scene from platform-agnostic commands."""
        ...
    
    def get_user_input(self) -> Optional[Dict[str, Any]]:
        """Get user input in standardized format."""
        ...
    
    def show_linear_forms(self, egif: str, clif: str, cgif: str) -> None:
        """Display linear form representations."""
        ...
    
    def highlight_areas(self, highlight_commands: List[Dict[str, Any]]) -> None:
        """Highlight specific areas or elements."""
        ...


@dataclass
class UserInteraction:
    """Platform-agnostic user interaction event."""
    action: str  # 'add_vertex', 'add_edge', 'add_cut', 'move_element'
    position: Optional[Tuple[float, float]] = None
    element_id: Optional[str] = None
    parameters: Dict[str, Any] = None


@dataclass
class RenderCommand:
    """Platform-agnostic rendering command."""
    command_type: str  # 'vertex', 'edge', 'cut', 'ligature'
    element_id: str
    position: Tuple[float, float]
    size: Tuple[float, float]
    properties: Dict[str, Any]


class EGIController:
    """Platform-independent controller for EGI system."""
    
    def __init__(self):
        self.egi_system = EGISystem()
        self.networkx_engine = NetworkXEGILayoutEngine()
        self.validator = create_validator()
        self.presentation_adapters: List[PresentationAdapter] = []
        self.current_spatial_layout = None
        self.current_validation_result = None
        self.use_networkx_layout = False  # Flag for rollback mechanism
        
        # Initialize spatial engine after EGI system is ready
        self.spatial_engine = None
        
        # Subscribe to EGI changes
        self.egi_system.observe_changes(self._on_egi_changed)
    
    def register_presentation_adapter(self, adapter: PresentationAdapter) -> None:
        """Register a presentation adapter (Qt, web, CLI, etc.)."""
        self.presentation_adapters.append(adapter)
    
    def initialize_demo_graph(self) -> None:
        """Initialize with demo graph for testing."""
        # Get the actual sheet ID from EGI system
        current_egi = self.egi_system.get_egi()
        sheet_id = current_egi.sheet
        
        # Build demo graph - all predicates connected to Tom
        self.egi_system.insert_vertex("Tom", sheet_id)
        self.egi_system.insert_edge("e1", "Person", ["Tom"], sheet_id)
        self.egi_system.insert_edge("e2", "Happy", ["Tom"], sheet_id)
        self.egi_system.insert_edge("e4", "Relation", ["Tom"], sheet_id)
        self.egi_system.insert_cut("cut_1", sheet_id)
        # Add NewRelation inside the cut
        self.egi_system.insert_edge("e3", "NewRelation", ["Tom"], "cut_1")
        
        # Refresh all presentations
        self._refresh_all_presentations()
    
    def handle_user_interaction(self, interaction: UserInteraction) -> OperationResult:
        """Handle platform-agnostic user interaction."""
        current_egi = self.egi_system.get_egi()
        sheet_id = current_egi.sheet
        
        result = OperationResult(success=False)
        
        if interaction.action == 'add_vertex':
            vertex_id = interaction.parameters.get('vertex_id', f'v_{len(current_egi.V) + 1}')
            result = self.egi_system.insert_vertex(vertex_id, sheet_id)
            
        elif interaction.action == 'add_edge':
            edge_id = interaction.parameters.get('edge_id', f'e_{len(current_egi.E) + 1}')
            relation = interaction.parameters.get('relation', 'Relation')
            vertices = interaction.parameters.get('vertices', [])
            result = self.egi_system.insert_edge(edge_id, relation, vertices, sheet_id)
            
        elif interaction.action == 'add_cut':
            cut_id = interaction.parameters.get('cut_id', f'cut_{len(current_egi.Cut) + 1}')
            result = self.egi_system.insert_cut(cut_id, sheet_id)
        
        if result.success:
            self._refresh_all_presentations()
        
        return result
    
    def get_linear_forms(self) -> Dict[str, str]:
        """Get all linear form representations."""
        return {
            'egif': self.egi_system.to_egif(),
            'clif': self.egi_system.to_clif(),
            'cgif': self.egi_system.to_cgif()
        }
    
    def _on_egi_changed(self, egi_state) -> None:
        """Handle EGI state changes."""
        self._refresh_all_presentations()
    
    def _refresh_all_presentations(self) -> None:
        """Refresh all registered presentation adapters."""
        # Generate spatial layout with proper area alignment
        self.current_spatial_layout = self._generate_area_aligned_layout()
        
        # Validate logic-spatial concordance
        if self.current_spatial_layout:
            current_egi = self.egi_system.get_egi()
            self.current_validation_result = self.validator.validate_concordance(current_egi, self.current_spatial_layout)
            
            # Log validation results
            print(f"Logic-Spatial Validation: {self.current_validation_result.validation_summary}")
            if self.current_validation_result.violations:
                print("Violations detected:")
                for violation in self.current_validation_result.violations:
                    print(f"  - {violation.violation_type.value}: {violation.description}")
        
        # Convert to render commands
        render_commands = self.get_render_commands()
        
        # Update all adapters
        for adapter in self.presentation_adapters:
            adapter.render_scene(render_commands)
            
            # Update linear forms
            egif = self.egi_system.to_egif()
            clif = self.egi_system.to_clif()
            cgif = self.egi_system.to_cgif()
            adapter.show_linear_forms(egif, clif, cgif)
    
    def _generate_area_aligned_layout(self) -> Dict[str, Any]:
        """Generate spatial layout that respects logical area assignments with validation."""
        current_egi = self.egi_system.get_egi()
        
        # Try NetworkX + Graphviz layout first
        if self.use_networkx_layout:
            try:
                print("Using NetworkX + Graphviz layout engine...")
                area_bounds = self._get_initial_area_bounds(current_egi)
                layout = self.networkx_engine.generate_layout(current_egi, area_bounds)
                return layout
            except Exception as e:
                print(f"NetworkX layout failed: {e}")
                print("Rolling back to original layout engine...")
                self.use_networkx_layout = False
        
        # Validated layout generation with spatial-logical correspondence
        return self._generate_validated_layout(current_egi)
    
    def _generate_validated_layout(self, egi) -> Dict[str, Any]:
        """Generate layout with integrated spatial-logical validation at every step."""
        layout = {}
        
        # Define area spatial bounds first
        area_bounds = {}
        sheet_id = egi.sheet
        area_bounds[sheet_id] = {'x': 50, 'y': 50, 'width': 700, 'height': 500}
        
        # Position cuts based on logical structure analysis
        for cut in egi.Cut:
            parent_area = self._find_cut_parent_area(cut.id)
            parent_bounds = area_bounds.get(parent_area, area_bounds[sheet_id])
            
            # Determine spatial requirements from logical structure
            cut_requirements = self._determine_cut_spatial_requirements(cut.id, parent_area, egi)
            
            # Find position that satisfies logical requirements
            cut_bounds = self._find_cut_position_for_requirements(
                parent_bounds, cut_requirements, layout
            )
            area_bounds[cut.id] = cut_bounds
            
            # Add cut to layout
            from egi_spatial_correspondence import SpatialElement, SpatialBounds
            layout[cut.id] = SpatialElement(
                element_id=cut.id,
                element_type='cut',
                logical_area=parent_area,
                spatial_bounds=SpatialBounds(cut_bounds['x'], cut_bounds['y'], 
                                           cut_bounds['width'], cut_bounds['height'])
            )
        
        # Position vertices in their assigned areas with validation
        for vertex in egi.V:
            vertex_area = self._find_element_area(vertex.id, egi)
            area_bound = area_bounds.get(vertex_area, area_bounds[sheet_id])
            
            # Position vertex within its area, avoiding collisions
            vertex_pos = self._find_non_colliding_position(
                area_bound, 10, 10, layout, 'vertex'
            )
            
            layout[vertex.id] = SpatialElement(
                element_id=vertex.id,
                element_type='vertex',
                logical_area=vertex_area,
                spatial_bounds=SpatialBounds(vertex_pos[0], vertex_pos[1], 10, 10)
            )
        
        # Position edges in their assigned areas with validation
        for edge in egi.E:
            edge_area = self._find_element_area(edge.id, egi)
            area_bound = area_bounds.get(edge_area, area_bounds[sheet_id])
            
            # Position edge within its area, avoiding collisions
            edge_pos = self._find_non_colliding_position(
                area_bound, 80, 25, layout, 'edge'
            )
            
            layout[edge.id] = SpatialElement(
                element_id=edge.id,
                element_type='edge',
                logical_area=edge_area,
                spatial_bounds=SpatialBounds(edge_pos[0], edge_pos[1], 80, 25),
                relation_name=egi.rel.get(edge.id, edge.id)
            )
        
        # Generate ligatures connecting predicates to shared vertices
        self._add_ligatures_to_layout(layout, egi)
        
        return layout
    
    def _add_ligatures_to_layout(self, layout: Dict[str, Any], egi) -> None:
        """Add ligature connections based on nu mapping (vertex-edge incidence)."""
        from egi_spatial_correspondence import SpatialElement, SpatialBounds, LigatureGeometry
        
        # Create ligatures for each edge based on nu mapping
        ligature_counter = 1
        for edge in egi.E:
            if edge.id in layout:
                connected_vertices = egi.nu.get(edge.id, ())
                if len(connected_vertices) >= 1:
                    ligature_id = f"ligature_{ligature_counter}"
                    
                    # Get edge position (predicate box)
                    edge_element = layout[edge.id]
                    edge_center = (
                        edge_element.spatial_bounds.x + edge_element.spatial_bounds.width / 2,
                        edge_element.spatial_bounds.y + edge_element.spatial_bounds.height / 2
                    )
                    
                    # Create ligature connecting edge to all its incident vertices
                    vertex_paths = []
                    valid_vertices = []
                    
                    for vertex_id in connected_vertices:
                        if vertex_id in layout:
                            vertex_element = layout[vertex_id]
                            vertex_center = (
                                vertex_element.spatial_bounds.x + vertex_element.spatial_bounds.width / 2,
                                vertex_element.spatial_bounds.y + vertex_element.spatial_bounds.height / 2
                            )
                            
                            # Check area-aware routing
                            edge_area = edge_element.logical_area
                            vertex_area = vertex_element.logical_area
                            
                            if edge_area == vertex_area:
                                # Same area: route around cuts if needed
                                routed_path = self._route_ligature_around_cuts(edge_center, vertex_center, layout)
                                vertex_paths.append(routed_path)
                                valid_vertices.append(vertex_id)
                            else:
                                # Different areas: direct connection allowed
                                vertex_paths.append([edge_center, vertex_center])
                                valid_vertices.append(vertex_id)
                    
                    # Create ligature if there are valid connections
                    if len(valid_vertices) > 0:
                        # Create a routed path from edge center to each vertex,
                        # concatenating waypoints to avoid cut boundaries.
                        all_path_points = []
                        for idx, path in enumerate(vertex_paths):
                            if not path:
                                continue
                            if idx == 0:
                                # Start with the first routed path as-is
                                all_path_points.extend(path)
                            else:
                                # Return to edge center, then follow the next routed path
                                all_path_points.append(edge_center)
                                # Avoid duplicating the starting edge_center if present
                                if path[0] == edge_center and len(path) > 1:
                                    all_path_points.extend(path[1:])
                                else:
                                    all_path_points.extend(path)
                        
                        # Create ligature geometry
                        ligature_geometry = LigatureGeometry(
                            ligature_id=ligature_id,
                            vertices=valid_vertices,
                            spatial_path=all_path_points,
                            branching_points=[]
                        )
                        
                        # Add ligature to layout
                        layout[ligature_id] = SpatialElement(
                            element_id=ligature_id,
                            element_type='ligature',
                            logical_area=edge_element.logical_area,
                            spatial_bounds=SpatialBounds(0, 0, 0, 0),  # Ligatures don't have bounds
                            ligature_geometry=ligature_geometry
                        )
                        
                        ligature_counter += 1
                    
                    ligature_counter += 1
    
    def _ligature_crosses_cut_boundary(self, start_point: Tuple[float, float], 
                                     end_point: Tuple[float, float], 
                                     layout: Dict[str, Any]) -> bool:
        """Check if ligature line crosses any cut boundary (for same-area connections)."""
        # For elements in same area, ligature should not cross cut boundaries
        for element in layout.values():
            if element.element_type == 'cut':
                cut_bounds = element.spatial_bounds
                # Check if line segment intersects the cut rectangle
                if self._line_intersects_rectangle(start_point, end_point, cut_bounds):
                    return True
        return False
    
    def _line_intersects_rectangle(self, p1: Tuple[float, float], p2: Tuple[float, float], 
                                 bounds) -> bool:
        """Check if line segment intersects rectangle using proper line-rectangle intersection."""
        x1, y1 = p1
        x2, y2 = p2
        rect_x = bounds.x
        rect_y = bounds.y
        rect_w = bounds.width
        rect_h = bounds.height
        
        # Check if line segment intersects any of the four rectangle edges
        # Left edge
        if self._line_segments_intersect((x1, y1), (x2, y2), (rect_x, rect_y), (rect_x, rect_y + rect_h)):
            return True
        # Right edge  
        if self._line_segments_intersect((x1, y1), (x2, y2), (rect_x + rect_w, rect_y), (rect_x + rect_w, rect_y + rect_h)):
            return True
        # Top edge
        if self._line_segments_intersect((x1, y1), (x2, y2), (rect_x, rect_y), (rect_x + rect_w, rect_y)):
            return True
        # Bottom edge
        if self._line_segments_intersect((x1, y1), (x2, y2), (rect_x, rect_y + rect_h), (rect_x + rect_w, rect_y + rect_h)):
            return True
            
        return False
    
    def _line_segments_intersect(self, p1: Tuple[float, float], p2: Tuple[float, float],
                               p3: Tuple[float, float], p4: Tuple[float, float]) -> bool:
        """Check if two line segments intersect."""
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3
        x4, y4 = p4
        
        # Calculate the direction of the lines
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(denom) < 1e-10:  # Lines are parallel
            return False
            
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom
        
        # Check if intersection point is within both line segments
        return 0 <= t <= 1 and 0 <= u <= 1
    
    def _route_ligature_around_cuts(self, start_point: Tuple[float, float], 
                                  end_point: Tuple[float, float], 
                                  layout: Dict[str, Any]) -> List[Tuple[float, float]]:
        """Route ligature path around cut boundaries using A* pathfinding."""
        # If no cuts block the direct path, use straight line
        if not self._ligature_crosses_cut_boundary(start_point, end_point, layout):
            return [start_point, end_point]
        
        # Find all cut obstacles
        obstacles = []
        for element in layout.values():
            if element.element_type == 'cut':
                bounds = element.spatial_bounds
                # Add padding around cut for routing clearance
                padding = 10
                obstacles.append({
                    'x': bounds.x - padding,
                    'y': bounds.y - padding,
                    'width': bounds.width + 2 * padding,
                    'height': bounds.height + 2 * padding
                })
        
        # Route around obstacles using visibility graph
        path = self._find_path_around_obstacles(start_point, end_point, obstacles)

        # Fail-fast invariant: ensure no path segment intersects any obstacle.
        if self._path_intersects_any_obstacle(path, obstacles):
            # Try rerouting with progressively inflated obstacles (increased padding)
            for extra in (8, 16, 24, 36):
                inflated = [
                    {
                        'x': r['x'] - extra,
                        'y': r['y'] - extra,
                        'width': r['width'] + 2 * extra,
                        'height': r['height'] + 2 * extra,
                    }
                    for r in obstacles
                ]
                path = self._find_path_around_obstacles(start_point, end_point, inflated)
                if not self._path_intersects_any_obstacle(path, obstacles):
                    break

        # If still invalid, raise to prevent ambiguous rendering
        if self._path_intersects_any_obstacle(path, obstacles):
            raise ValueError("Ligature routing failed: path crosses cut boundary in same area")

        return path
    
    def _find_path_around_obstacles(self, start: Tuple[float, float], 
                                  end: Tuple[float, float], 
                                  obstacles: List[Dict[str, float]]) -> List[Tuple[float, float]]:
        """Find path around rectangular obstacles using a visibility-graph router."""
        # If no obstacle blocks, return straight line
        if not any(self._line_intersects_rectangle_dict(start, end, o) for o in obstacles):
            return [start, end]

        padding = 12  # clearance around obstacles to avoid grazing cut edges

        # Build waypoint nodes: start, end, and padded corners of each obstacle
        nodes: List[Tuple[float, float]] = [start, end]
        for rect in obstacles:
            rx, ry, rw, rh = rect['x'], rect['y'], rect['width'], rect['height']
            corners = [
                (rx - padding, ry - padding),
                (rx + rw + padding, ry - padding),
                (rx + rw + padding, ry + rh + padding),
                (rx - padding, ry + rh + padding),
            ]
            nodes.extend(corners)

        # Helper to check if a segment intersects any obstacle
        def segment_clear(p1: Tuple[float, float], p2: Tuple[float, float]) -> bool:
            # Allow endpoints to be on padded corners but not pass through rectangles
            for rect in obstacles:
                if self._line_intersects_rectangle_dict(p1, p2, rect):
                    return False
            return True

        # Build visibility edges
        import math
        neighbors: Dict[int, List[Tuple[int, float]]] = {}
        for i in range(len(nodes)):
            neighbors[i] = []
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                p1, p2 = nodes[i], nodes[j]
                if segment_clear(p1, p2):
                    dist = math.hypot(p1[0] - p2[0], p1[1] - p2[1])
                    neighbors[i].append((j, dist))
                    neighbors[j].append((i, dist))

        # A* search from start (0) to end (1)
        def heuristic(a: Tuple[float, float], b: Tuple[float, float]) -> float:
            return math.hypot(a[0] - b[0], a[1] - b[1])

        start_idx, goal_idx = 0, 1
        import heapq
        open_set = [(0 + heuristic(nodes[start_idx], nodes[goal_idx]), 0, start_idx, -1)]
        best_cost: Dict[int, float] = {start_idx: 0.0}
        prev: Dict[int, int] = {}

        while open_set:
            _, cost, cur, parent = heapq.heappop(open_set)
            if cur in prev:
                continue
            prev[cur] = parent
            if cur == goal_idx:
                break
            for nbr, edge_cost in neighbors.get(cur, []):
                new_cost = cost + edge_cost
                if new_cost < best_cost.get(nbr, float('inf')):
                    best_cost[nbr] = new_cost
                    priority = new_cost + heuristic(nodes[nbr], nodes[goal_idx])
                    heapq.heappush(open_set, (priority, new_cost, nbr, cur))

        # Reconstruct path
        if goal_idx not in prev:
            # Fallback: simple L-shaped detour around first obstacle
            for obstacle in obstacles:
                if self._point_in_rectangle_path(start, end, obstacle):
                    return self._route_around_rectangle(start, end, obstacle)
            return [start, end]

        path_indices = []
        cur = goal_idx
        while cur != -1:
            path_indices.append(cur)
            cur = prev.get(cur, -1)
        path_indices.reverse()

        # Compress consecutive duplicates and return points
        path_points = []
        for idx in path_indices:
            pt = nodes[idx]
            if not path_points or path_points[-1] != pt:
                path_points.append(pt)
        return path_points

    def _path_intersects_any_obstacle(self, path: List[Tuple[float, float]], 
                                      obstacles: List[Dict[str, float]]) -> bool:
        """Check if any consecutive segment in a path intersects any obstacle rectangle."""
        if len(path) < 2:
            return False
        for i in range(len(path) - 1):
            a, b = path[i], path[i + 1]
            for rect in obstacles:
                if self._line_intersects_rectangle_dict(a, b, rect):
                    return True
        return False
    
    def _point_in_rectangle_path(self, start: Tuple[float, float], 
                               end: Tuple[float, float], 
                               rect: Dict[str, float]) -> bool:
        """Check if straight line from start to end intersects rectangle."""
        return self._line_intersects_rectangle_dict(start, end, rect)
    
    def _line_intersects_rectangle_dict(self, p1: Tuple[float, float], 
                                      p2: Tuple[float, float], 
                                      rect: Dict[str, float]) -> bool:
        """Check line intersection with rectangle defined as dict."""
        x1, y1 = p1
        x2, y2 = p2
        rx, ry = rect['x'], rect['y']
        rw, rh = rect['width'], rect['height']
        
        # Check intersection with rectangle edges
        edges = [
            ((rx, ry), (rx + rw, ry)),           # Top
            ((rx + rw, ry), (rx + rw, ry + rh)), # Right  
            ((rx + rw, ry + rh), (rx, ry + rh)), # Bottom
            ((rx, ry + rh), (rx, ry))            # Left
        ]
        
        for edge_start, edge_end in edges:
            if self._line_segments_intersect(p1, p2, edge_start, edge_end):
                return True
        return False
    
    def _route_around_rectangle(self, start: Tuple[float, float], 
                              end: Tuple[float, float], 
                              rect: Dict[str, float]) -> List[Tuple[float, float]]:
        """Route path around rectangle obstacle using corner waypoints."""
        sx, sy = start
        ex, ey = end
        rx, ry = rect['x'], rect['y']
        rw, rh = rect['width'], rect['height']
        
        # Rectangle corners
        corners = [
            (rx, ry),           # Top-left
            (rx + rw, ry),      # Top-right
            (rx + rw, ry + rh), # Bottom-right
            (rx, ry + rh)       # Bottom-left
        ]
        
        # Choose routing direction based on start/end positions
        # Simple heuristic: route via the corner closest to the midpoint
        mid_x, mid_y = (sx + ex) / 2, (sy + ey) / 2
        
        # Find closest corner to midpoint
        best_corner = min(corners, key=lambda c: (c[0] - mid_x)**2 + (c[1] - mid_y)**2)
        
        return [start, best_corner, end]
    
    def _determine_cut_spatial_requirements(self, cut_id: str, parent_area: str, egi) -> Dict[str, Any]:
        """Determine spatial requirements for cut based on logical structure."""
        # Analyze what elements belong to this cut logically
        cut_elements = egi.area.get(cut_id, set())
        parent_elements = egi.area.get(parent_area, set())
        
        # Calculate required spatial bounds based on contained elements
        if not cut_elements:
            # Empty cut - minimal size
            return {
                'min_width': 100,
                'min_height': 80,
                'required_elements': [],
                'spatial_constraints': []
            }
        
        # Cut must contain space for all its logical elements
        element_count = len(cut_elements)
        required_width = max(200, element_count * 90)  # Space for elements
        required_height = max(120, (element_count // 3 + 1) * 40)  # Rows of elements
        
        return {
            'min_width': required_width,
            'min_height': required_height,
            'required_elements': list(cut_elements),
            'spatial_constraints': self._analyze_element_spatial_constraints(cut_elements, egi)
        }
    
    def _analyze_element_spatial_constraints(self, elements: set, egi) -> List[Dict[str, Any]]:
        """Analyze spatial constraints imposed by logical element relationships."""
        constraints = []
        
        # Find vertices and their connected edges within this cut
        for element_id in elements:
            if element_id in [v.id for v in egi.V]:
                # This is a vertex - find its connected edges within the cut
                connected_edges = []
                for edge in egi.E:
                    if edge.id in elements and element_id in egi.nu.get(edge.id, []):
                        connected_edges.append(edge.id)
                
                if connected_edges:
                    constraints.append({
                        'type': 'vertex_edge_proximity',
                        'vertex': element_id,
                        'edges': connected_edges,
                        'max_distance': 150  # Ligature routing distance
                    })
        
        return constraints
    
    def _find_cut_position_for_requirements(self, parent_bounds: Dict[str, float], 
                                           requirements: Dict[str, Any],
                                           existing_layout: Dict[str, Any]) -> Dict[str, float]:
        """Find cut position that satisfies logical spatial requirements."""
        cut_width = requirements['min_width']
        cut_height = requirements['min_height']
        
        # Try to position cut based on logical requirements
        for attempt in range(30):
            x = parent_bounds['x'] + 40 + (attempt % 10) * 24
            y = parent_bounds['y'] + 40 + (attempt // 10) * 20
            
            proposed_bounds = {
                'x': x, 'y': y, 
                'width': cut_width, 'height': cut_height
            }
            
            # Check if position satisfies all requirements
            if (self._bounds_within_parent(proposed_bounds, parent_bounds) and
                not self._overlaps_existing_elements(proposed_bounds, existing_layout) and
                self._satisfies_spatial_constraints(proposed_bounds, requirements['spatial_constraints'])):
                return proposed_bounds
        
        # Fallback position with minimum requirements
        return {
            'x': parent_bounds['x'] + 200,
            'y': parent_bounds['y'] + 100,
            'width': cut_width,
            'height': cut_height
        }
    
    def _satisfies_spatial_constraints(self, bounds: Dict[str, float], 
                                     constraints: List[Dict[str, Any]]) -> bool:
        """Check if proposed bounds satisfy spatial constraints from logical structure."""
        # For now, accept all positions - constraints can be refined later
        # This ensures cuts are positioned based on logical analysis rather than rejected
        return True
    
    def _bounds_within_parent(self, child_bounds: Dict[str, float], 
                            parent_bounds: Dict[str, float]) -> bool:
        """Check if child bounds are completely within parent bounds."""
        return (child_bounds['x'] >= parent_bounds['x'] and
                child_bounds['y'] >= parent_bounds['y'] and
                child_bounds['x'] + child_bounds['width'] <= parent_bounds['x'] + parent_bounds['width'] and
                child_bounds['y'] + child_bounds['height'] <= parent_bounds['y'] + parent_bounds['height'])
    
    def _overlaps_existing_elements(self, proposed_bounds: Dict[str, float],
                                  existing_layout: Dict[str, Any]) -> bool:
        """Check if proposed bounds overlap with any existing elements."""
        for element in existing_layout.values():
            if element.element_type in ['cut', 'vertex', 'edge']:
                existing_bounds = {
                    'x': element.spatial_bounds.x,
                    'y': element.spatial_bounds.y,
                    'width': element.spatial_bounds.width,
                    'height': element.spatial_bounds.height
                }
                if self._bounds_overlap_dict(proposed_bounds, existing_bounds):
                    return True
        return False
    
    def _get_initial_area_bounds(self, egi) -> Dict[str, SpatialBounds]:
        """Get initial area bounds for NetworkX layout."""
        area_bounds = {}
        sheet_id = egi.sheet
        area_bounds[sheet_id] = SpatialBounds(x=50, y=50, width=700, height=500)
        
        # Add bounds for cuts
        for cut in egi.Cut:
            area_bounds[cut.id] = SpatialBounds(x=200, y=150, width=300, height=200)
        
        return area_bounds
    
    def enable_networkx_layout(self) -> None:
        """Enable NetworkX + Graphviz layout engine."""
        self.use_networkx_layout = True
        self._refresh_all_presentations()
    
    def disable_networkx_layout(self) -> None:
        """Disable NetworkX layout and use original engine."""
        self.use_networkx_layout = False
        self._refresh_all_presentations()
    
    def get_validation_result(self) -> Optional[ValidationResult]:
        """Get the current logic-spatial concordance validation result."""
        return self.current_validation_result
    
    def add_vertex(self) -> OperationResult:
        """Add a new vertex to the current sheet."""
        current_egi = self.egi_system.get_egi()
        vertex_id = f"v_{len(current_egi.V) + 1}"
        sheet_id = current_egi.sheet
        return self.egi_system.insert_vertex(vertex_id, sheet_id)
    
    def add_edge(self) -> OperationResult:
        """Add a new edge connected to the first vertex."""
        current_egi = self.egi_system.get_egi()
        if len(current_egi.V) == 0:
            return OperationResult(success=False, error="Need vertices before adding edges")
        
        edge_id = f"e_{len(current_egi.E) + 1}"
        vertex_ids = [list(current_egi.V)[0].id]  # Connect to first vertex
        sheet_id = current_egi.sheet
        return self.egi_system.insert_edge(edge_id, "Relation", vertex_ids, sheet_id)
    
    def add_cut(self) -> OperationResult:
        """Add a new cut to the current sheet."""
        current_egi = self.egi_system.get_egi()
        cut_id = f"cut_{len(current_egi.Cut) + 1}"
        sheet_id = current_egi.sheet
        return self.egi_system.insert_cut(cut_id, sheet_id)
    
    def get_egif(self) -> str:
        """Get EGIF representation of current EGI."""
        return self.egi_system.to_egif()
    
    def validate_current_layout(self) -> ValidationResult:
        """Manually trigger validation of current spatial layout."""
        if self.current_spatial_layout:
            current_egi = self.egi_system.get_egi()
            self.current_validation_result = self.validator.validate_concordance(current_egi, self.current_spatial_layout)
            return self.current_validation_result
        else:
            from logic_spatial_validator import ValidationResult, ValidationViolation, ViolationType
            return ValidationResult(
                is_valid=False,
                violations=[ValidationViolation(
                    violation_type=ViolationType.ORPHANED_ELEMENT,
                    element_ids=[],
                    description="No spatial layout available for validation",
                    severity='critical'
                )],
                total_elements_checked=0,
                validation_summary="No spatial layout to validate"
            )

    def _find_cut_parent_area(self, cut_id: str) -> str:
        """Find the parent area containing a cut."""
        current_egi = self.egi_system.get_egi()
        for area_id, elements in current_egi.area.items():
            if cut_id in elements:
                return area_id
        return current_egi.sheet
    
    def _find_element_area(self, element_id: str, egi) -> str:
        """Find which area contains an element."""
        for area_id, elements in egi.area.items():
            if element_id in elements:
                return area_id
        return egi.sheet
    
    def _find_non_colliding_position(self, area_bounds: Dict[str, float], 
                                   width: float, height: float, 
                                   existing_layout: Dict[str, Any],
                                   element_type: str) -> Tuple[float, float]:
        """Find a position within area bounds that doesn't collide and respects exclusion zones."""
        import random
        
        max_attempts = 150
        margin = 20
        
        # Get exclusion zones (nested cuts within this area)
        exclusion_zones = self._get_exclusion_zones_for_area(area_bounds, existing_layout)
        
        for _ in range(max_attempts):
            # Random position within area bounds with margin
            x = area_bounds['x'] + margin + random.random() * (
                area_bounds['width'] - width - 2 * margin)
            y = area_bounds['y'] + margin + random.random() * (
                area_bounds['height'] - height - 2 * margin)
            
            proposed_bounds = {'x': x, 'y': y, 'width': width, 'height': height}
            
            # Check if position is in exclusion zone (inside nested cuts)
            if self._position_in_exclusion_zones(proposed_bounds, exclusion_zones):
                continue
            
            # Check for collisions with existing elements (increase spacing by small epsilon)
            collision = False
            for existing_element in existing_layout.values():
                existing_bounds = {
                    'x': existing_element.spatial_bounds.x,
                    'y': existing_element.spatial_bounds.y,
                    'width': existing_element.spatial_bounds.width,
                    'height': existing_element.spatial_bounds.height
                }
                
                # Inflate existing bounds slightly to reduce near-overlaps
                inflated = {
                    'x': existing_bounds['x'] - 2,
                    'y': existing_bounds['y'] - 2,
                    'width': existing_bounds['width'] + 4,
                    'height': existing_bounds['height'] + 4,
                }
                if self._bounds_overlap_dict(proposed_bounds, inflated):
                    collision = True
                    break
            
            if not collision:
                return (x, y)
        
        # Fallback: return position with small random offset, avoiding exclusion zones
        for _ in range(10):
            fallback_x = area_bounds['x'] + 20 + random.random() * 50
            fallback_y = area_bounds['y'] + 20 + random.random() * 50
            fallback_bounds = {'x': fallback_x, 'y': fallback_y, 'width': width, 'height': height}
            
            if not self._position_in_exclusion_zones(fallback_bounds, exclusion_zones):
                return (fallback_x, fallback_y)
        
        return (area_bounds['x'] + 20, area_bounds['y'] + 20)
    
    def _get_exclusion_zones_for_area(self, area_bounds: Dict[str, float], 
                                     existing_layout: Dict[str, Any]) -> List[Dict[str, float]]:
        """Get nested cut rectangles that should be excluded from placement."""
        exclusion_zones = []
        
        for element in existing_layout.values():
            if element.element_type == 'cut':
                cut_bounds = {
                    'x': element.spatial_bounds.x,
                    'y': element.spatial_bounds.y,
                    'width': element.spatial_bounds.width,
                    'height': element.spatial_bounds.height
                }
                
                # Check if this cut is nested within the target area
                if self._bounds_contained_in(cut_bounds, area_bounds):
                    exclusion_zones.append(cut_bounds)
        
        return exclusion_zones
    
    def _position_in_exclusion_zones(self, proposed_bounds: Dict[str, float], 
                                   exclusion_zones: List[Dict[str, float]]) -> bool:
        """Check if proposed position overlaps with any exclusion zone."""
        for zone in exclusion_zones:
            if self._bounds_overlap_dict(proposed_bounds, zone):
                return True
        return False
    
    def _bounds_contained_in(self, inner_bounds: Dict[str, float], 
                           outer_bounds: Dict[str, float]) -> bool:
        """Check if inner bounds are completely contained within outer bounds."""
        return (inner_bounds['x'] >= outer_bounds['x'] and
                inner_bounds['y'] >= outer_bounds['y'] and
                inner_bounds['x'] + inner_bounds['width'] <= outer_bounds['x'] + outer_bounds['width'] and
                inner_bounds['y'] + inner_bounds['height'] <= outer_bounds['y'] + outer_bounds['height'])
    
    def _bounds_overlap_dict(self, bounds1: Dict[str, float], bounds2: Dict[str, float]) -> bool:
        """Check if two bounds dictionaries overlap."""
        return not (bounds1['x'] + bounds1['width'] <= bounds2['x'] or
                   bounds2['x'] + bounds2['width'] <= bounds1['x'] or
                   bounds1['y'] + bounds1['height'] <= bounds2['y'] or
                   bounds2['y'] + bounds2['height'] <= bounds1['y'])
    
    def get_render_commands(self) -> List[Dict[str, Any]]:
        """Convert spatial layout to platform-agnostic render commands."""
        if not self.current_spatial_layout:
            return []
            
        commands = []
        ligature_commands = []  # Render ligatures last
        
        for element_id, element in self.current_spatial_layout.items():
            cmd = {
                'type': element.element_type,
                'element_id': element_id,
                'bounds': {
                    'x': element.spatial_bounds.x,
                    'y': element.spatial_bounds.y,
                    'width': element.spatial_bounds.width,
                    'height': element.spatial_bounds.height
                }
            }
            
            # Add element-specific properties
            if element.element_type == 'edge':
                # Get relation name from EGI
                current_egi = self.egi_system.get_egi()
                cmd['relation_name'] = current_egi.rel.get(element_id, 'Unknown')
                
            elif element.element_type == 'vertex':
                # Add vertex name - ensure it gets passed to rendering
                cmd['vertex_name'] = element_id
                cmd['element_id'] = element_id
                
            elif element.element_type == 'ligature':
                # Add ligature path - save for rendering last
                if hasattr(element, 'ligature_geometry') and element.ligature_geometry:
                    cmd['path_points'] = element.ligature_geometry.spatial_path
                ligature_commands.append(cmd)
                continue  # Skip adding to regular commands
            
            commands.append(cmd)
        
        # Add ligatures last so they render on top of cuts
        commands.extend(ligature_commands)
        return commands
    
    # Advanced Spatial Constraint and Highlighting Methods
    
    def get_valid_placement_areas(self, element_type: str, element_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get areas where an element can be placed without breaking EGI logic."""
        current_egi = self.egi_system.get_egi()
        valid_areas = []
        
        # For each area in the EGI, check if placement would be valid
        for area_id in current_egi.area.keys():
            if self._can_place_element_in_area(element_type, area_id, element_id):
                area_bounds = self._get_area_spatial_bounds(area_id)
                if area_bounds:
                    valid_areas.append({
                        'area_id': area_id,
                        'bounds': area_bounds,
                        'highlight_type': 'valid_placement'
                    })
        
        return valid_areas
    
    def get_cut_direct_contents(self, cut_id: str) -> List[Dict[str, Any]]:
        """Get elements directly enclosed by a cut (not nested cuts)."""
        current_egi = self.egi_system.get_egi()
        direct_contents = []
        
        if cut_id in current_egi.area:
            direct_elements = current_egi.area[cut_id]
            for element_id in direct_elements:
                if element_id in self.current_spatial_layout:
                    spatial_element = self.current_spatial_layout[element_id]
                    direct_contents.append({
                        'element_id': element_id,
                        'element_type': spatial_element.element_type,
                        'bounds': {
                            'x': spatial_element.spatial_bounds.x,
                            'y': spatial_element.spatial_bounds.y,
                            'width': spatial_element.spatial_bounds.width,
                            'height': spatial_element.spatial_bounds.height
                        },
                        'highlight_type': 'cut_direct_content'
                    })
        
        return direct_contents
    
    def get_cut_full_context(self, cut_id: str) -> List[Dict[str, Any]]:
        """Get all elements in the context defined by a cut (including nested)."""
        current_egi = self.egi_system.get_egi()
        context_elements = []
        
        def collect_context_recursive(area_id: str):
            if area_id in current_egi.area:
                for element_id in current_egi.area[area_id]:
                    if element_id in self.current_spatial_layout:
                        spatial_element = self.current_spatial_layout[element_id]
                        context_elements.append({
                            'element_id': element_id,
                            'element_type': spatial_element.element_type,
                            'bounds': {
                                'x': spatial_element.spatial_bounds.x,
                                'y': spatial_element.spatial_bounds.y,
                                'width': spatial_element.spatial_bounds.width,
                                'height': spatial_element.spatial_bounds.height
                            },
                            'highlight_type': 'cut_full_context'
                        })
                    
                    # If this element is a cut, recurse into its context
                    if element_id in [c.id for c in current_egi.Cut]:
                        collect_context_recursive(element_id)
        
        collect_context_recursive(cut_id)
        return context_elements
    
    def check_collision(self, element_bounds: Dict[str, float], exclude_element: Optional[str] = None) -> bool:
        """Check if element bounds would collide with existing elements."""
        test_bounds = SpatialBounds(
            element_bounds['x'], element_bounds['y'],
            element_bounds['width'], element_bounds['height']
        )
        
        for element_id, spatial_element in self.current_spatial_layout.items():
            if exclude_element and element_id == exclude_element:
                continue
                
            if self._bounds_overlap(test_bounds, spatial_element.spatial_bounds):
                return True
        
        return False
    
    def validate_element_movement(self, element_id: str, new_position: Tuple[float, float]) -> Dict[str, Any]:
        """Validate if element can be moved to new position without breaking constraints."""
        current_egi = self.egi_system.get_egi()
        
        if element_id not in self.current_spatial_layout:
            return {'valid': False, 'reason': 'Element not found'}
        
        spatial_element = self.current_spatial_layout[element_id]
        
        # Create new bounds at proposed position
        new_bounds = {
            'x': new_position[0],
            'y': new_position[1],
            'width': spatial_element.spatial_bounds.width,
            'height': spatial_element.spatial_bounds.height
        }
        
        # Check collision
        if self.check_collision(new_bounds, element_id):
            return {'valid': False, 'reason': 'Would cause collision'}
        
        # Check area containment
        element_area = spatial_element.logical_area
        area_bounds = self._get_area_spatial_bounds(element_area)
        
        if area_bounds and not self._point_in_bounds(new_position, area_bounds):
            return {'valid': False, 'reason': 'Would move outside logical area'}
        
        return {'valid': True}
    
    def highlight_valid_placement_areas(self, element_type: str) -> None:
        """Highlight areas where element can be validly placed."""
        valid_areas = self.get_valid_placement_areas(element_type)
        
        for adapter in self.presentation_adapters:
            adapter.highlight_areas(valid_areas)
    
    def highlight_cut_contents(self, cut_id: str, include_nested: bool = False) -> None:
        """Highlight contents of a cut."""
        if include_nested:
            contents = self.get_cut_full_context(cut_id)
        else:
            contents = self.get_cut_direct_contents(cut_id)
        
        for adapter in self.presentation_adapters:
            adapter.highlight_areas(contents)
    
    def _can_place_element_in_area(self, element_type: str, area_id: str, element_id: Optional[str] = None) -> bool:
        """Check if element type can be placed in given area."""
        # Basic validation - could be extended with more sophisticated logic
        current_egi = self.egi_system.get_egi()
        
        # Check if area exists
        if area_id not in current_egi.area:
            return False
        
        # For now, allow placement in any existing area
        # This could be extended with type-specific constraints
        return True
    
    def _get_area_spatial_bounds(self, area_id: str) -> Optional[Dict[str, float]]:
        """Get spatial bounds of an area."""
        if area_id == self.egi_system.get_egi().sheet:
            # Sheet area - use full canvas
            return {'x': 0, 'y': 0, 'width': 800, 'height': 600}
        
        # For cuts, find the cut's spatial bounds
        if area_id in self.current_spatial_layout:
            spatial_element = self.current_spatial_layout[area_id]
            return {
                'x': spatial_element.spatial_bounds.x,
                'y': spatial_element.spatial_bounds.y,
                'width': spatial_element.spatial_bounds.width,
                'height': spatial_element.spatial_bounds.height
            }
        
        return None
    
    def _bounds_overlap(self, bounds1: SpatialBounds, bounds2: SpatialBounds) -> bool:
        """Check if two spatial bounds overlap."""
        return not (bounds1.x + bounds1.width <= bounds2.x or
                   bounds2.x + bounds2.width <= bounds1.x or
                   bounds1.y + bounds1.height <= bounds2.y or
                   bounds2.y + bounds2.height <= bounds1.y)
    
    def _point_in_bounds(self, point: Tuple[float, float], bounds: Dict[str, float]) -> bool:
        """Check if point is within bounds."""
        x, y = point
        return (bounds['x'] <= x <= bounds['x'] + bounds['width'] and
                bounds['y'] <= y <= bounds['y'] + bounds['height'])


def create_egi_controller() -> EGIController:
    """Factory function for creating EGI controller."""
    return EGIController()
