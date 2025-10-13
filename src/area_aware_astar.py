#!/usr/bin/env python3
"""
Area-Aware A* Pathfinding for EGI Ligatures

Phase 4: Implements intelligent ligature routing that:
1. Respects area boundaries and hierarchies
2. Avoids obstacles (vertices, edges, cuts)
3. Finds optimal paths through legal corridors
4. Handles cross-area spanning ligatures

Based on Dau's ligature rules:
- Same-area ligatures: Must avoid collisions with cuts
- Cross-area ligatures: Can cross cut boundaries
"""

from typing import List, Tuple, Set, Optional, Dict
from dataclasses import dataclass
from heapq import heappush, heappop
import math

from constrained_force_layout import Rect


@dataclass
class PathNode:
    """Node in the A* search space."""
    x: float
    y: float
    g_cost: float  # Cost from start
    h_cost: float  # Heuristic to goal
    parent: Optional['PathNode'] = None
    
    @property
    def f_cost(self) -> float:
        """Total cost (g + h)."""
        return self.g_cost + self.h_cost
    
    def __lt__(self, other):
        """For heap ordering."""
        return self.f_cost < other.f_cost
    
    def __hash__(self):
        """For set membership."""
        return hash((round(self.x, 2), round(self.y, 2)))
    
    def __eq__(self, other):
        """For set membership."""
        return abs(self.x - other.x) < 0.01 and abs(self.y - other.y) < 0.01


@dataclass
class Obstacle:
    """An obstacle that ligatures must avoid."""
    rect: Rect
    type: str  # 'vertex', 'edge', 'cut_boundary'
    area_id: str  # Which area this obstacle belongs to


class AreaAwareAStarPathfinder:
    """
    Area-aware A* pathfinder for EGI ligatures.
    
    Key features:
    - Respects area hierarchy
    - Avoids obstacles within same area
    - Allows crossing between areas at designated ports
    - Finds shortest valid path
    """
    
    def __init__(self, 
                 area_bounds: Dict[str, Rect],
                 area_hierarchy: Dict[str, Dict],
                 grid_resolution: float = 5.0):
        """
        Initialize pathfinder.
        
        Args:
            area_bounds: Map of area IDs to their bounding rectangles
            area_hierarchy: Hierarchy of areas (parent/children relationships)
            grid_resolution: Grid spacing for search (pixels)
        """
        self.area_bounds = area_bounds
        self.area_hierarchy = area_hierarchy
        self.grid_resolution = grid_resolution
        self.obstacles: List[Obstacle] = []
    
    def add_obstacle(self, rect: Rect, obstacle_type: str, area_id: str):
        """Add an obstacle to avoid."""
        self.obstacles.append(Obstacle(rect, obstacle_type, area_id))
    
    def find_path(self,
                  start: Tuple[float, float],
                  goal: Tuple[float, float],
                  start_area: str,
                  goal_area: str,
                  ports: Optional[List[Tuple[float, float]]] = None) -> List[Tuple[float, float]]:
        """
        Find optimal path from start to goal using A*.
        
        Args:
            start: Starting position (x, y)
            goal: Goal position (x, y)
            start_area: Area ID containing start
            goal_area: Area ID containing goal
            ports: Optional list of port positions for cross-area paths
        
        Returns:
            List of waypoints forming the path
        """
        # Same area: Direct path if no obstacles
        if start_area == goal_area:
            return self._find_same_area_path(start, goal, start_area)
        
        # Cross-area: Use ports if provided
        if ports:
            return self._find_cross_area_path(start, goal, start_area, goal_area, ports)
        
        # Fallback: Simple straight line
        return [start, goal]
    
    def _find_same_area_path(self,
                             start: Tuple[float, float],
                             goal: Tuple[float, float],
                             area_id: str) -> List[Tuple[float, float]]:
        """
        Find path within same area (must avoid obstacles).
        
        Uses A* with obstacle avoidance.
        """
        # Get relevant obstacles in this area
        area_obstacles = [obs for obs in self.obstacles if obs.area_id == area_id]
        
        # Check if direct path is clear
        if self._is_path_clear(start, goal, area_obstacles):
            return [start, goal]
        
        # Run A* search
        start_node = PathNode(start[0], start[1], 0, self._heuristic(start, goal))
        goal_pos = goal
        
        open_set = [start_node]
        closed_set: Set[PathNode] = set()
        
        while open_set:
            current = heappop(open_set)
            
            # Goal reached?
            if self._distance(current, goal_pos) < self.grid_resolution:
                return self._reconstruct_path(current)
            
            closed_set.add(current)
            
            # Explore neighbors
            for neighbor in self._get_neighbors(current, area_id):
                if neighbor in closed_set:
                    continue
                
                # Check if neighbor position is valid (not in obstacle)
                if self._is_in_obstacle((neighbor.x, neighbor.y), area_obstacles):
                    continue
                
                # Calculate costs
                tentative_g = current.g_cost + self._distance(current, (neighbor.x, neighbor.y))
                
                # Check if this path is better
                existing = next((n for n in open_set if n == neighbor), None)
                if existing and tentative_g >= existing.g_cost:
                    continue
                
                # Update neighbor
                neighbor.g_cost = tentative_g
                neighbor.h_cost = self._heuristic((neighbor.x, neighbor.y), goal_pos)
                neighbor.parent = current
                
                if not existing:
                    heappush(open_set, neighbor)
        
        # No path found - return direct line as fallback
        return [start, goal]
    
    def _find_cross_area_path(self,
                              start: Tuple[float, float],
                              goal: Tuple[float, float],
                              start_area: str,
                              goal_area: str,
                              ports: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        Find path across areas using ports.
        
        Path segments:
        1. Start → first port (within start_area)
        2. Port → port (crossing boundaries)
        3. Last port → goal (within goal_area)
        """
        path = [start]
        
        # Add path segments through ports
        current_pos = start
        current_area = start_area
        
        for port in ports:
            # Find path to this port
            segment = self._find_same_area_path(current_pos, port, current_area)
            path.extend(segment[1:])  # Skip duplicate start point
            current_pos = port
            # Area changes at port
            current_area = goal_area  # Simplified - would need proper area tracking
        
        # Final segment to goal
        segment = self._find_same_area_path(current_pos, goal, goal_area)
        path.extend(segment[1:])
        
        return path
    
    def _get_neighbors(self, node: PathNode, area_id: str) -> List[PathNode]:
        """Get valid neighbor positions for A* search."""
        neighbors = []
        area_rect = self.area_bounds.get(area_id)
        
        if not area_rect:
            return neighbors
        
        # 8 directions
        directions = [
            (self.grid_resolution, 0),
            (-self.grid_resolution, 0),
            (0, self.grid_resolution),
            (0, -self.grid_resolution),
            (self.grid_resolution, self.grid_resolution),
            (self.grid_resolution, -self.grid_resolution),
            (-self.grid_resolution, self.grid_resolution),
            (-self.grid_resolution, -self.grid_resolution)
        ]
        
        for dx, dy in directions:
            nx = node.x + dx
            ny = node.y + dy
            
            # Check if within area bounds
            if (area_rect.x <= nx <= area_rect.x + area_rect.width and
                area_rect.y <= ny <= area_rect.y + area_rect.height):
                neighbors.append(PathNode(nx, ny, 0, 0, node))
        
        return neighbors
    
    def _is_path_clear(self,
                       start: Tuple[float, float],
                       end: Tuple[float, float],
                       obstacles: List[Obstacle]) -> bool:
        """Check if straight line path intersects any obstacles."""
        for obs in obstacles:
            if self._line_intersects_rect(start, end, obs.rect):
                return False
        return True
    
    def _is_in_obstacle(self, pos: Tuple[float, float], obstacles: List[Obstacle]) -> bool:
        """Check if position is inside an obstacle."""
        x, y = pos
        for obs in obstacles:
            if (obs.rect.x <= x <= obs.rect.x + obs.rect.width and
                obs.rect.y <= y <= obs.rect.y + obs.rect.height):
                return True
        return False
    
    def _line_intersects_rect(self,
                              start: Tuple[float, float],
                              end: Tuple[float, float],
                              rect: Rect) -> bool:
        """Check if line segment intersects rectangle."""
        # Simple bounding box check
        min_x = min(start[0], end[0])
        max_x = max(start[0], end[0])
        min_y = min(start[1], end[1])
        max_y = max(start[1], end[1])
        
        # Check if bounding boxes overlap
        if (max_x < rect.x or min_x > rect.x + rect.width or
            max_y < rect.y or min_y > rect.y + rect.height):
            return False
        
        # More detailed intersection check would go here
        # For now, conservative check
        return True
    
    def _heuristic(self, pos: Tuple[float, float], goal: Tuple[float, float]) -> float:
        """Euclidean distance heuristic."""
        return math.sqrt((pos[0] - goal[0])**2 + (pos[1] - goal[1])**2)
    
    def _distance(self, node_or_pos, goal: Tuple[float, float]) -> float:
        """Distance between node/position and goal."""
        if isinstance(node_or_pos, PathNode):
            return math.sqrt((node_or_pos.x - goal[0])**2 + (node_or_pos.y - goal[1])**2)
        else:
            return math.sqrt((node_or_pos[0] - goal[0])**2 + (node_or_pos[1] - goal[1])**2)
    
    def _reconstruct_path(self, node: PathNode) -> List[Tuple[float, float]]:
        """Reconstruct path from goal node by following parents."""
        path = []
        current = node
        while current:
            path.append((current.x, current.y))
            current = current.parent
        return list(reversed(path))
    
    def smooth_path(self, path: List[Tuple[float, float]], tolerance: float = 5.0) -> List[Tuple[float, float]]:
        """
        Smooth path by removing unnecessary waypoints using Ramer-Douglas-Peucker.
        
        Args:
            path: Original path with potentially many waypoints
            tolerance: Maximum distance a point can be from the simplified line (pixels)
            
        Returns:
            Simplified path with fewer waypoints
        """
        if len(path) <= 2:
            return path
        
        # Apply Ramer-Douglas-Peucker algorithm iteratively
        smoothed = self._ramer_douglas_peucker(path, tolerance)
        
        # Additional pass: Remove nearly collinear points
        final = [smoothed[0]]
        for i in range(1, len(smoothed) - 1):
            prev = smoothed[i - 1]
            curr = smoothed[i]
            next_pt = smoothed[i + 1]
            
            # Keep points that create significant turns (not nearly collinear)
            if not self._is_collinear(prev, curr, next_pt, tolerance=tolerance):
                final.append(curr)
        
        final.append(smoothed[-1])
        return final
    
    def _ramer_douglas_peucker(self, points: List[Tuple[float, float]], tolerance: float) -> List[Tuple[float, float]]:
        """
        Ramer-Douglas-Peucker path simplification algorithm.
        
        Recursively simplifies a path by removing points that don't deviate
        significantly from a straight line.
        """
        if len(points) <= 2:
            return points
        
        # Find the point with maximum distance from line between start and end
        start = points[0]
        end = points[-1]
        max_dist = 0.0
        max_index = 0
        
        for i in range(1, len(points) - 1):
            dist = self._perpendicular_distance(points[i], start, end)
            if dist > max_dist:
                max_dist = dist
                max_index = i
        
        # If max distance is greater than tolerance, recursively simplify
        if max_dist > tolerance:
            # Recursively simplify both segments
            left = self._ramer_douglas_peucker(points[:max_index + 1], tolerance)
            right = self._ramer_douglas_peucker(points[max_index:], tolerance)
            
            # Combine results (remove duplicate middle point)
            return left[:-1] + right
        else:
            # All points are within tolerance - just keep start and end
            return [start, end]
    
    def _perpendicular_distance(self, point: Tuple[float, float], 
                                line_start: Tuple[float, float], 
                                line_end: Tuple[float, float]) -> float:
        """Calculate perpendicular distance from point to line segment."""
        px, py = point
        x1, y1 = line_start
        x2, y2 = line_end
        
        # Calculate line length squared
        line_len_sq = (x2 - x1)**2 + (y2 - y1)**2
        
        if line_len_sq == 0:
            # Line start and end are the same point
            return math.sqrt((px - x1)**2 + (py - y1)**2)
        
        # Calculate projection parameter t
        t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / line_len_sq))
        
        # Calculate projection point
        proj_x = x1 + t * (x2 - x1)
        proj_y = y1 + t * (y2 - y1)
        
        # Calculate distance from point to projection
        return math.sqrt((px - proj_x)**2 + (py - proj_y)**2)
    
    def _is_collinear(self, p1: Tuple[float, float], 
                     p2: Tuple[float, float],
                     p3: Tuple[float, float],
                     tolerance: float = 5.0) -> bool:
        """Check if three points are collinear within tolerance."""
        # Cross product
        cross = ((p2[1] - p1[1]) * (p3[0] - p2[0]) - 
                 (p2[0] - p1[0]) * (p3[1] - p2[1]))
        return abs(cross) < tolerance * 10  # More lenient for smoothness
