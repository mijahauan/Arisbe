"""
Balanced Position Exchange Optimizer

Implements the revised approach where elements are positioned in balanced patterns
within their areas, with optimization achieved through position exchange rather
than arbitrary movement.

Key principles:
- Single elements: centered in their area
- Multiple elements: equidistant from each other and boundaries
- Optimization: swap elements between balanced positions to improve ligature paths
"""

from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
import math
import itertools

from egi_core_dau import RelationalGraphWithCuts, ElementID
from containment_hierarchy_engine import ALURect, ALUPoint
from area_spatial_constraint_system import AreaSpatialConstraintSystem


@dataclass
class BalancedPosition:
    """Represents a balanced position within an area."""
    position: ALUPoint
    area_id: ElementID
    position_index: int  # Index within the balanced arrangement


@dataclass
class LigatureConnection:
    """Represents a ligature connection for optimization."""
    vertex_id: ElementID
    predicate_id: ElementID
    legitimate_crossings: Set[ElementID]


class BalancedPositionOptimizer:
    """
    Optimizes EGI layout using balanced position exchange strategy.
    
    Elements are first positioned in balanced patterns, then optimization
    is achieved by exchanging elements between these balanced positions.
    """
    
    def __init__(self, constraint_system: AreaSpatialConstraintSystem):
        self.constraint_system = constraint_system
        self.BOUNDARY_MARGIN = 1.0  # ALU margin from area boundaries
        
    def optimize_layout(self, egi: RelationalGraphWithCuts, 
                       area_bounds: Dict[ElementID, ALURect]) -> Dict[ElementID, ALUPoint]:
        """
        Optimize layout using balanced position exchange.
        
        Returns:
            Dictionary mapping element IDs to optimized positions
        """
        print("🔄 BALANCED POSITION EXCHANGE OPTIMIZATION")
        print("=" * 55)
        
        # Step 1: Calculate balanced positions for each area
        balanced_arrangements = self._calculate_balanced_arrangements(egi, area_bounds)
        
        # Step 2: Create initial assignment (elements to balanced positions)
        initial_assignment = self._create_initial_assignment(egi, balanced_arrangements)
        
        # Step 3: Analyze ligature connections
        connections = self._analyze_ligature_connections(egi)
        
        # Step 4: Optimize through position exchange
        optimized_assignment = self._optimize_via_position_exchange(
            initial_assignment, connections, balanced_arrangements, egi
        )
        
        # Step 5: Convert to final positions
        final_positions = self._assignment_to_positions(optimized_assignment, balanced_arrangements)
        
        print(f"✅ Optimized {len(final_positions)} element positions via balanced exchange")
        return final_positions
    
    def _calculate_balanced_arrangements(self, egi: RelationalGraphWithCuts, 
                                       area_bounds: Dict[ElementID, ALURect]) -> Dict[ElementID, List[BalancedPosition]]:
        """Calculate balanced position arrangements for each area."""
        arrangements = {}
        
        for area_id, bounds in area_bounds.items():
            area_contents = egi.area.get(area_id, set())
            
            # Get elements that need positioning (vertices and edges, not cuts)
            elements_to_position = []
            for element_id in area_contents:
                if element_id in {v.id for v in egi.V} or element_id in {e.id for e in egi.E}:
                    elements_to_position.append(element_id)
            
            if elements_to_position:
                balanced_positions = self._create_balanced_pattern(elements_to_position, bounds, area_id)
                arrangements[area_id] = balanced_positions
                
                print(f"Area {area_id}: {len(balanced_positions)} balanced positions")
                for i, pos in enumerate(balanced_positions):
                    print(f"  Position {i}: ({pos.position.x:.1f}, {pos.position.y:.1f})")
        
        return arrangements
    
    def _create_balanced_pattern(self, elements: List[ElementID], bounds: ALURect, 
                               area_id: ElementID) -> List[BalancedPosition]:
        """Create balanced positioning pattern for elements in an area."""
        num_elements = len(elements)
        
        if num_elements == 1:
            # Single element: centered
            center_x, center_y = bounds.center()
            return [BalancedPosition(
                position=ALUPoint(center_x, center_y),
                area_id=area_id,
                position_index=0
            )]
        
        elif num_elements == 2:
            # Two elements: positioned symmetrically
            return self._create_symmetric_pair(bounds, area_id)
        
        elif num_elements <= 6:
            # Small groups: circular arrangement
            return self._create_circular_arrangement(num_elements, bounds, area_id)
        
        else:
            # Larger groups: grid arrangement
            return self._create_grid_arrangement(num_elements, bounds, area_id)
    
    def _create_symmetric_pair(self, bounds: ALURect, area_id: ElementID) -> List[BalancedPosition]:
        """Create symmetric positioning for two elements."""
        center_x, center_y = bounds.center()
        
        # Position elements horizontally separated
        available_width = bounds.width - 2 * self.BOUNDARY_MARGIN
        separation = min(available_width * 0.4, 2.0)  # Max 2 ALU separation
        
        return [
            BalancedPosition(
                position=ALUPoint(center_x - separation/2, center_y),
                area_id=area_id,
                position_index=0
            ),
            BalancedPosition(
                position=ALUPoint(center_x + separation/2, center_y),
                area_id=area_id,
                position_index=1
            )
        ]
    
    def _create_circular_arrangement(self, num_elements: int, bounds: ALURect, 
                                   area_id: ElementID) -> List[BalancedPosition]:
        """Create circular arrangement for small groups of elements."""
        center_x, center_y = bounds.center()
        
        # Calculate radius to fit within bounds with margin
        available_width = bounds.width - 2 * self.BOUNDARY_MARGIN
        available_height = bounds.height - 2 * self.BOUNDARY_MARGIN
        max_radius = min(available_width, available_height) * 0.3
        
        positions = []
        for i in range(num_elements):
            angle = 2 * math.pi * i / num_elements
            x = center_x + max_radius * math.cos(angle)
            y = center_y + max_radius * math.sin(angle)
            
            positions.append(BalancedPosition(
                position=ALUPoint(x, y),
                area_id=area_id,
                position_index=i
            ))
        
        return positions
    
    def _create_grid_arrangement(self, num_elements: int, bounds: ALURect, 
                               area_id: ElementID) -> List[BalancedPosition]:
        """Create grid arrangement for larger groups of elements."""
        available_width = bounds.width - 2 * self.BOUNDARY_MARGIN
        available_height = bounds.height - 2 * self.BOUNDARY_MARGIN
        
        # Calculate grid dimensions
        cols = math.ceil(math.sqrt(num_elements))
        rows = math.ceil(num_elements / cols)
        
        cell_width = available_width / cols
        cell_height = available_height / rows
        
        positions = []
        for i in range(num_elements):
            row = i // cols
            col = i % cols
            
            x = bounds.x + self.BOUNDARY_MARGIN + (col + 0.5) * cell_width
            y = bounds.y + self.BOUNDARY_MARGIN + (row + 0.5) * cell_height
            
            positions.append(BalancedPosition(
                position=ALUPoint(x, y),
                area_id=area_id,
                position_index=i
            ))
        
        return positions
    
    def _create_initial_assignment(self, egi: RelationalGraphWithCuts, 
                                 balanced_arrangements: Dict[ElementID, List[BalancedPosition]]) -> Dict[ElementID, BalancedPosition]:
        """Create initial assignment of elements to balanced positions."""
        assignment = {}
        
        for area_id, positions in balanced_arrangements.items():
            area_contents = egi.area.get(area_id, set())
            
            # Get elements that need positioning
            elements_to_assign = []
            for element_id in area_contents:
                if element_id in {v.id for v in egi.V} or element_id in {e.id for e in egi.E}:
                    elements_to_assign.append(element_id)
            
            # Assign elements to positions in order
            for i, element_id in enumerate(elements_to_assign):
                if i < len(positions):
                    assignment[element_id] = positions[i]
        
        return assignment
    
    def _analyze_ligature_connections(self, egi: RelationalGraphWithCuts) -> List[LigatureConnection]:
        """Analyze ligature connections for optimization."""
        connections = []
        
        for edge_id, vertex_sequence in egi.nu.items():
            for vertex_id in vertex_sequence:
                legitimate_crossings = self._calculate_legitimate_crossings(vertex_id, edge_id, egi)
                
                connection = LigatureConnection(
                    vertex_id=vertex_id,
                    predicate_id=edge_id,
                    legitimate_crossings=legitimate_crossings
                )
                connections.append(connection)
        
        return connections
    
    def _calculate_legitimate_crossings(self, vertex_id: ElementID, predicate_id: ElementID, 
                                      egi: RelationalGraphWithCuts) -> Set[ElementID]:
        """Calculate legitimate cut crossings for a ligature."""
        vertex_area = egi.get_context(vertex_id)
        predicate_area = egi.get_context(predicate_id)
        
        if vertex_area == predicate_area:
            return set()  # Same area - no crossings needed
        
        # For now, simplified: if different areas, can cross their boundary
        # More sophisticated path analysis could be added here
        return {vertex_area, predicate_area}
    
    def _optimize_via_position_exchange(self, initial_assignment: Dict[ElementID, BalancedPosition],
                                      connections: List[LigatureConnection],
                                      balanced_arrangements: Dict[ElementID, List[BalancedPosition]],
                                      egi: RelationalGraphWithCuts) -> Dict[ElementID, BalancedPosition]:
        """Optimize ligature paths by exchanging elements between balanced positions."""
        print("\n🔄 Optimizing via position exchange...")
        
        best_assignment = dict(initial_assignment)
        best_total_length = self._calculate_total_ligature_length(best_assignment, connections)
        
        print(f"Initial total ligature length: {best_total_length:.2f} ALU")
        
        # Try position exchanges within each area
        for area_id, positions in balanced_arrangements.items():
            if len(positions) <= 1:
                continue  # No exchanges possible
            
            # Get elements in this area
            area_elements = [elem_id for elem_id, pos in initial_assignment.items() 
                           if pos.area_id == area_id]
            
            if len(area_elements) <= 1:
                continue
            
            # Try all permutations of elements within this area
            best_area_assignment = {elem_id: initial_assignment[elem_id] for elem_id in area_elements}
            
            for permutation in itertools.permutations(area_elements):
                # Create assignment for this permutation
                test_assignment = dict(best_assignment)
                for i, element_id in enumerate(permutation):
                    test_assignment[element_id] = positions[i]
                
                # Calculate total ligature length
                total_length = self._calculate_total_ligature_length(test_assignment, connections)
                
                if total_length < best_total_length:
                    best_total_length = total_length
                    best_assignment = test_assignment
                    print(f"  Improved arrangement in area {area_id}: {total_length:.2f} ALU")
        
        print(f"Final total ligature length: {best_total_length:.2f} ALU")
        return best_assignment
    
    def _calculate_total_ligature_length(self, assignment: Dict[ElementID, BalancedPosition],
                                       connections: List[LigatureConnection]) -> float:
        """Calculate total length of all ligature paths."""
        total_length = 0.0
        
        for connection in connections:
            if connection.vertex_id in assignment and connection.predicate_id in assignment:
                vertex_pos = assignment[connection.vertex_id].position
                predicate_pos = assignment[connection.predicate_id].position
                
                dx = vertex_pos.x - predicate_pos.x
                dy = vertex_pos.y - predicate_pos.y
                length = math.sqrt(dx * dx + dy * dy)
                total_length += length
        
        return total_length
    
    def _assignment_to_positions(self, assignment: Dict[ElementID, BalancedPosition],
                               balanced_arrangements: Dict[ElementID, List[BalancedPosition]]) -> Dict[ElementID, ALUPoint]:
        """Convert assignment to final position mapping."""
        positions = {}
        
        for element_id, balanced_pos in assignment.items():
            positions[element_id] = balanced_pos.position
        
        return positions
