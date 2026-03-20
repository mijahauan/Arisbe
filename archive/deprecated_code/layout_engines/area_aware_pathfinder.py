"""
Area-Aware Pathfinder for EGI Layout Engine

Implements intelligent A* pathfinding that understands logical area containment
and enforces proper cut boundary crossing rules.
"""

from typing import Set, List
from pathfinding.core.grid import Grid
from pathfinding.core.node import Node
from pathfinding.finder.a_star import AStarFinder
from pathfinding.core.diagonal_movement import DiagonalMovement


class AreaAwareNode(Node):
    """Custom A* node that tracks which area it belongs to"""
    
    def __init__(self, x: int, y: int, walkable: bool = True, area_id: str = None):
        super().__init__()
        self.x = x  # Store coordinates explicitly
        self.y = y
        self.walkable = walkable
        self.area_id = area_id


class AreaAwareGrid(Grid):
    """Custom grid that tracks area membership for each cell"""
    
    def __init__(self, width: int = 0, height: int = 0, matrix: List[List] = None, area_map: List[List[str]] = None):
        super().__init__(width, height, matrix)
        self.area_map = area_map or [[None for _ in range(width)] for _ in range(height)]
    
    def node(self, x: int, y: int) -> AreaAwareNode:
        """Get node with area information"""
        if 0 <= x < self.width and 0 <= y < self.height:
            # Get walkability from parent Grid's nodes array
            parent_node = super().node(x, y)
            walkable = parent_node.walkable if parent_node else False
            area_id = self.area_map[y][x] if self.area_map else None
            return AreaAwareNode(x, y, walkable, area_id)
        return AreaAwareNode(x, y, False)


class AreaAwareFinder(AStarFinder):
    """A* pathfinder that respects area boundaries and legal corridors"""
    
    def __init__(self, legal_areas: Set[str]):
        super().__init__(diagonal_movement=DiagonalMovement.always)
        self.legal_areas = legal_areas
        
    def apply_heuristic(self, node_a: AreaAwareNode, node_b: AreaAwareNode, heuristic=None) -> float:
        """Apply heuristic with area awareness"""
        
        # Base heuristic (Manhattan distance)
        base_cost = super().apply_heuristic(node_a, node_b, heuristic)
        
        # Area penalty: heavily penalize nodes outside legal corridor
        if hasattr(node_a, 'area_id') and node_a.area_id:
            if node_a.area_id not in self.legal_areas:
                # Infinite cost for illegal areas
                return float('inf')
        
        return base_cost
    
    def process_node(self, node: AreaAwareNode, parent: AreaAwareNode, end: AreaAwareNode, 
                    open_list: list, grid: AreaAwareGrid) -> bool:
        """Process node with area-aware cost calculation"""
        
        # Check if node is in legal area
        if hasattr(node, 'area_id') and node.area_id:
            if node.area_id not in self.legal_areas:
                # Skip nodes outside legal corridor
                return False
        
        # Use standard A* processing for legal nodes
        return super().process_node(node, parent, end, open_list, grid)
    
    def find_neighbors(self, grid: AreaAwareGrid, node: AreaAwareNode, diagonal_movement: int = None) -> List[AreaAwareNode]:
        """Find neighbors with area awareness"""
        
        # Get standard neighbors
        neighbors = super().find_neighbors(grid, node, diagonal_movement)
        
        # Filter out neighbors in illegal areas
        legal_neighbors = []
        for neighbor in neighbors:
            if hasattr(neighbor, 'area_id') and neighbor.area_id:
                if neighbor.area_id in self.legal_areas:
                    legal_neighbors.append(neighbor)
            else:
                # Nodes without area assignment are considered legal
                legal_neighbors.append(neighbor)
        
        return legal_neighbors
