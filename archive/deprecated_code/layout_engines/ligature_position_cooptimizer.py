"""
Ligature Position Co-Optimizer

Refines element positions based on topological connections to improve layout clarity.
"""

from typing import Dict
from egi_core_dau import RelationalGraphWithCuts, ElementID
from containment_hierarchy_engine import ALURect, ALUPoint
from area_spatial_constraint_system import AreaSpatialConstraintSystem

class LigaturePositionCoOptimizer:
    """
    Applies a set of heuristics to refine element positions, specifically focusing
    on the placement of vertices relative to the predicates they are connected to.
    This directly implements the user's specified layout rules.
    """

    def __init__(self, constraint_system: AreaSpatialConstraintSystem):
        self.constraint_system = constraint_system

    def optimize_positions(self,
                           egi: RelationalGraphWithCuts,
                           initial_positions: Dict[ElementID, ALUPoint],
                           area_bounds: Dict[ElementID, ALURect]) -> Dict[ElementID, ALUPoint]:
        """
        Refines element positions using vertex-centric heuristics as specified by the user.

        - A vertex connected to 2 predicates is moved to their midpoint.
        - A vertex connected to >2 predicates is moved to their centroid.
        """
        optimized_positions = dict(initial_positions)

        for vertex in egi.V:
            vertex_area = egi.get_context(vertex.id)
            
            # Find all predicates connected to this vertex within the same area
            connected_predicates = []
            for edge_id, vertex_sequence in egi.nu.items():
                if vertex.id in vertex_sequence and egi.get_context(edge_id) == vertex_area:
                    connected_predicates.append(edge_id)

            num_connections = len(connected_predicates)

            if num_connections == 2:
                # Midpoint Rule: Place vertex at the midpoint of the two predicates.
                p1_pos = optimized_positions.get(connected_predicates[0])
                p2_pos = optimized_positions.get(connected_predicates[1])
                if p1_pos and p2_pos:
                    midpoint_x = (p1_pos.x + p2_pos.x) / 2
                    midpoint_y = (p1_pos.y + p2_pos.y) / 2
                    optimized_positions[vertex.id] = ALUPoint(midpoint_x, midpoint_y)
                    print(f"  ✨ Midpoint-optimized vertex {vertex.id}")

            elif num_connections > 2:
                # Centroid Rule: Place vertex at the centroid of all connected predicates.
                centroid_x, centroid_y = 0, 0
                count = 0
                for pred_id in connected_predicates:
                    pred_pos = optimized_positions.get(pred_id)
                    if pred_pos:
                        centroid_x += pred_pos.x
                        centroid_y += pred_pos.y
                        count += 1
                if count > 0:
                    optimized_positions[vertex.id] = ALUPoint(centroid_x / count, centroid_y / count)
                    print(f"  ✨ Centroid-optimized vertex {vertex.id}")

        return optimized_positions
