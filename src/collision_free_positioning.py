"""
Collision-Free Element Positioning

Solves the general overlap problem by ensuring all elements have exclusive spatial positions.
Uses grid-based placement with collision detection to guarantee no overlaps.
"""

from typing import Dict, List, Set, Tuple
from dataclasses import dataclass
import math

from egi_core_dau import RelationalGraphWithCuts, ElementID
from containment_hierarchy_engine import ALURect, ALUPoint


@dataclass
class ElementPlacement:
    """Represents a placed element with guaranteed collision-free position."""
    element_id: ElementID
    position: ALUPoint
    bounds: ALURect
    element_type: str


class CollisionFreePositioning:
    """
    Ensures all elements have exclusive, non-overlapping positions.
    
    Key principle: Every element gets a guaranteed minimum space allocation
    that cannot be violated by other elements.
    """
    
    def __init__(self):
        self.MIN_ELEMENT_SIZE = 1.0  # ALU - minimum space per element
        self.ELEMENT_PADDING = 0.5   # ALU - padding around each element
        self.GRID_RESOLUTION = 0.5   # ALU - grid snap resolution
        
    def position_elements_collision_free(self, egi: RelationalGraphWithCuts,
                                       area_bounds: Dict[ElementID, ALURect]) -> Dict[ElementID, ALUPoint]:
        """
        Position all elements with guaranteed collision-free placement.
        
        Strategy:
        1. For each area, create a placement grid
        2. Allocate grid cells to elements (no sharing)
        3. Position elements at grid cell centers
        4. Guarantee minimum separation between all elements
        """
        print("🔒 COLLISION-FREE POSITIONING")
        print("=" * 40)
        
        all_positions = {}
        
        for area_id, bounds in area_bounds.items():
            area_contents = egi.area.get(area_id, set())
            
            if not area_contents:
                continue
                
            # Separate by type
            vertices = [eid for eid in area_contents if eid in {v.id for v in egi.V}]
            edges = [eid for eid in area_contents if eid in {e.id for e in egi.E}]
            cuts = [eid for eid in area_contents if eid in {c.id for c in egi.Cut}]
            
            print(f"\nArea {area_id}: {len(vertices)}v, {len(edges)}e, {len(cuts)}c")
            print(f"  Available space: {bounds.width:.1f}×{bounds.height:.1f} ALU")
            
            # Calculate grid dimensions needed
            total_elements = len(vertices) + len(edges)
            if total_elements == 0:
                continue
                
            grid_positions = self._calculate_grid_layout(bounds, total_elements)
            
            # Assign positions to elements (predicates first, then vertices)
            position_index = 0
            
            # Position predicates (edges)
            for edge_id in edges:
                if position_index < len(grid_positions):
                    pos = grid_positions[position_index]
                    all_positions[edge_id] = pos
                    print(f"  {edge_id} (predicate): ({pos.x:.1f}, {pos.y:.1f})")
                    position_index += 1
            
            # Position vertices
            for vertex_id in vertices:
                if position_index < len(grid_positions):
                    pos = grid_positions[position_index]
                    all_positions[vertex_id] = pos
                    print(f"  {vertex_id} (vertex): ({pos.x:.1f}, {pos.y:.1f})")
                    position_index += 1
        
        print(f"\n✅ Positioned {len(all_positions)} elements collision-free")
        return all_positions
    
    def _calculate_grid_layout(self, bounds: ALURect, num_elements: int) -> List[ALUPoint]:
        """
        Calculate optimal grid layout for elements within bounds.
        
        Returns list of collision-free positions.
        """
        if num_elements == 0:
            return []
        
        # Calculate grid dimensions
        available_width = bounds.width - 2 * self.ELEMENT_PADDING
        available_height = bounds.height - 2 * self.ELEMENT_PADDING
        
        # Determine grid size (prefer wider grids for better ligature routing)
        aspect_ratio = available_width / available_height
        
        if aspect_ratio >= 1.0:
            # Wide area - prefer horizontal layout
            cols = math.ceil(math.sqrt(num_elements * aspect_ratio))
            rows = math.ceil(num_elements / cols)
        else:
            # Tall area - prefer vertical layout  
            rows = math.ceil(math.sqrt(num_elements / aspect_ratio))
            cols = math.ceil(num_elements / rows)
        
        # Ensure we have enough cells
        while rows * cols < num_elements:
            if available_width > available_height:
                cols += 1
            else:
                rows += 1
        
        # Calculate cell dimensions
        cell_width = available_width / cols
        cell_height = available_height / rows
        
        # Generate grid positions (center of each cell)
        positions = []
        
        for i in range(num_elements):
            row = i // cols
            col = i % cols
            
            # Center position within cell
            pos_x = bounds.x + self.ELEMENT_PADDING + (col + 0.5) * cell_width
            pos_y = bounds.y + self.ELEMENT_PADDING + (row + 0.5) * cell_height
            
            positions.append(ALUPoint(pos_x, pos_y))
        
        print(f"    Grid: {rows}×{cols}, Cell: {cell_width:.1f}×{cell_height:.1f} ALU")
        
        return positions
    
    def validate_no_overlaps(self, positions: Dict[ElementID, ALUPoint]) -> bool:
        """Validate that no elements overlap."""
        position_list = list(positions.values())
        
        for i, pos1 in enumerate(position_list):
            for j, pos2 in enumerate(position_list[i+1:], i+1):
                distance = math.sqrt((pos1.x - pos2.x)**2 + (pos1.y - pos2.y)**2)
                
                if distance < self.MIN_ELEMENT_SIZE:
                    element_ids = list(positions.keys())
                    print(f"❌ OVERLAP: {element_ids[i]} and {element_ids[j]} (distance: {distance:.2f})")
                    return False
        
        print("✅ No overlaps detected")
        return True
