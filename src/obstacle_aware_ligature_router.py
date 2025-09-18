"""
Obstacle-Aware Ligature Router using Shapely and A* Pathfinding

Implements spatial routing for ligatures that respects all spatial exclusivity constraints.
"""

from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
import math
import heapq

from shapely.geometry import Polygon, Point, LineString

from egi_core_dau import RelationalGraphWithCuts, ElementID
from containment_hierarchy_engine import ALURect, ALUPoint


@dataclass(frozen=True)
class Obstacle:
    """Represents a spatial obstacle as a shapely Polygon."""
    id: ElementID
    polygon: Polygon


@dataclass
class LigatureRoute:
    """Represents a calculated route for a ligature."""
    start_element: ElementID
    end_element: ElementID
    waypoints: List[ALUPoint]
    total_length: float


class ObstacleAwareLigatureRouter:
    """
    Routes ligatures around spatial obstacles using A* on a visibility graph.
    """

    def __init__(self):
        self.OBSTACLE_CLEARANCE = 0.5  # ALU clearance
        self.FONT_SIZE_TO_ALU_SCALE = 0.5 # Rough estimate

    def calculate_all_routes(self, egi: RelationalGraphWithCuts,
                               element_positions: Dict[ElementID, ALUPoint],
                               element_sizes: Dict[ElementID, ALURect]) -> Dict[Tuple[ElementID, ElementID], LigatureRoute]:
        """
        Calculate obstacle-aware routes for all ligatures.
        """
        all_routes = {}
        all_obstacles = self._create_obstacles(egi, element_positions, element_sizes)

        for edge_id, vertex_sequence in egi.nu.items():
            for vertex_id in vertex_sequence:
                route = self.route_single_ligature(
                    vertex_id, edge_id, egi, element_positions, all_obstacles
                )
                if route:
                    all_routes[(vertex_id, edge_id)] = route
        return all_routes

    def route_single_ligature(self, start_id: ElementID, end_id: ElementID, egi: RelationalGraphWithCuts,
                                element_positions: Dict[ElementID, ALUPoint],
                                all_obstacles: List[Obstacle]) -> Optional[LigatureRoute]:
        """
        Route a single ligature from a vertex to a predicate.
        """
        start_pos = element_positions.get(start_id)
        end_pos = element_positions.get(end_id)
        if not start_pos or not end_pos:
            return None

        start_point = Point(start_pos.x, start_pos.y)
        end_obstacle = next((obs for obs in all_obstacles if obs.id == end_id), None)
        if not end_obstacle:
            return None

        # Filter obstacles to only those in the same area
        area_id = egi.get_context(start_id)
        area_obstacles = [obs for obs in all_obstacles if egi.get_context(obs.id) == area_id and obs.id != start_id and obs.id != end_id]

        # A* Pathfinding
        path_points = self._find_path_astar(start_point, end_obstacle.polygon, area_obstacles)

        if not path_points:
            # Fallback to direct line if pathfinding fails
            path_points = [start_point, self._get_closest_point_on_polygon(start_point, end_obstacle.polygon)]

        waypoints = [ALUPoint(p.x, p.y) for p in path_points]
        length = LineString(path_points).length

        return LigatureRoute(start_id, end_id, waypoints, length)

    def _create_obstacles(self, egi: RelationalGraphWithCuts, 
                          element_positions: Dict[ElementID, ALUPoint],
                          element_sizes: Dict[ElementID, ALURect]) -> List[Obstacle]:
        """Create shapely Polygons for all elements to act as obstacles."""
        obstacles = []
        for element_id, pos in element_positions.items():
            size = element_sizes.get(element_id)
            if not size:
                # Estimate size for vertices if not provided
                size = ALURect(pos.x - 0.5, pos.y - 0.5, 1.0, 1.0)

            # Inflate the obstacle for clearance
            inflated_bounds = (pos.x - size.width / 2 - self.OBSTACLE_CLEARANCE,
                               pos.y - size.height / 2 - self.OBSTACLE_CLEARANCE,
                               pos.x + size.width / 2 + self.OBSTACLE_CLEARANCE,
                               pos.y + size.height / 2 + self.OBSTACLE_CLEARANCE)
            
            poly = Polygon([
                (inflated_bounds[0], inflated_bounds[1]),
                (inflated_bounds[2], inflated_bounds[1]),
                (inflated_bounds[2], inflated_bounds[3]),
                (inflated_bounds[0], inflated_bounds[3])
            ])
            obstacles.append(Obstacle(id=element_id, polygon=poly))
        return obstacles

    def _find_path_astar(self, start_point: Point, end_poly: Polygon, obstacles: List[Obstacle]) -> Optional[List[Point]]:
        """A* pathfinding implementation."""
        # 1. Create Visibility Graph
        visibility_graph = {}
        all_nodes = {Point(coord) for obs in obstacles for coord in obs.polygon.exterior.coords} | {start_point}
        
        # Add nearest points on end_poly to graph
        end_points = {Point(coord) for coord in end_poly.exterior.coords}
        all_nodes.update(end_points)

        for node1 in all_nodes:
            visibility_graph[node1] = {}
            for node2 in all_nodes:
                if node1 == node2: continue
                line = LineString([node1, node2])
                is_visible = not any(line.intersects(obs.polygon) for obs in obstacles)
                if is_visible:
                    visibility_graph[node1][node2] = node1.distance(node2)

        # 2. A* Search
        open_set = [(0, start_point)] # (f_score, node)
        came_from = {}
        g_score = {node: float('inf') for node in all_nodes}
        g_score[start_point] = 0
        f_score = {node: float('inf') for node in all_nodes}
        f_score[start_point] = start_point.distance(end_poly)

        while open_set:
            _, current = heapq.heappop(open_set)

            if end_poly.contains(current) or end_poly.touches(current):
                # Find closest point on boundary and reconstruct path
                final_point = self._get_closest_point_on_polygon(current, end_poly)
                path = [final_point]
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start_point)
                return path[::-1]

            for neighbor, weight in visibility_graph.get(current, {}).items():
                tentative_g_score = g_score[current] + weight
                if tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + neighbor.distance(end_poly)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
        return None

    def _get_closest_point_on_polygon(self, point: Point, poly: Polygon) -> Point:
        """Finds the closest point on the boundary of a polygon to a given point."""
        return poly.exterior.interpolate(poly.exterior.project(point))
