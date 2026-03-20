"""
Ligature-Aware Positioning Engine

Implements intelligent vertex positioning that minimizes ligature path lengths
while respecting area boundaries. This replaces the naive positioning in
Phase 2 with connection-aware optimization.

Key Principles:
- Vertices positioned optimally between connected predicates
- Ligature paths calculated as shortest valid routes
- Area boundaries absolutely respected
- Cross-cut connections handled with proper boundary logic
- Path length minimization as primary objective
"""

from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
import math

from egi_core_dau import RelationalGraphWithCuts, ElementID
from containment_hierarchy_engine import ALURect, ALUPoint
from area_spatial_constraint_system import AreaSpatialConstraintSystem


@dataclass
class ConnectionInfo:
    """Information about a vertex's connections."""
    vertex_id: ElementID
    vertex_area: ElementID
    connected_predicates: List[Tuple[ElementID, ElementID]]  # (predicate_id, predicate_area)
    cross_cut_connections: int
    same_area_connections: int


@dataclass
class OptimalPosition:
    """Optimal position calculation for a vertex."""
    vertex_id: ElementID
    optimal_point: ALUPoint
    total_path_length: float
    constrained_point: ALUPoint  # After area boundary constraints
    constraint_applied: bool


class LigatureAwarePositioningEngine:
    """
    Positions vertices optimally to minimize ligature path lengths
    while absolutely respecting area boundaries.
    """
    
    def __init__(self, constraint_system: AreaSpatialConstraintSystem):
        self.constraint_system = constraint_system
        
    def optimize_vertex_positions(self, egi: RelationalGraphWithCuts,
                                 predicate_positions: Dict[ElementID, ALUPoint],
                                 area_bounds: Dict[ElementID, ALURect]) -> Dict[ElementID, ALUPoint]:
        """
        Optimize vertex positions to minimize ligature path lengths.
        
        Args:
            egi: The EGI structure
            predicate_positions: Fixed positions of predicates from Phase 2
            area_bounds: Area bounds from Phase 1
            
        Returns:
            Dictionary of optimized vertex positions
        """
        print("🎯 LIGATURE-AWARE VERTEX POSITIONING")
        print("=" * 50)
        
        # Step 1: Analyze vertex connections
        connection_info = self._analyze_vertex_connections(egi, predicate_positions)
        
        # Step 2: Group vertices by shared predicates to handle multi-vertex connections
        predicate_vertex_groups = self._group_vertices_by_predicates(egi)
        
        # Step 3: Calculate optimal positions for each vertex
        optimal_positions = {}
        
        for vertex_id, info in connection_info.items():
            optimal_pos = self._calculate_optimal_vertex_position(
                info, predicate_positions, egi, predicate_vertex_groups
            )
            optimal_positions[vertex_id] = optimal_pos
            
            print(f"Vertex {vertex_id}:")
            print(f"  Connected to: {len(info.connected_predicates)} predicates")
            print(f"  Cross-cut connections: {info.cross_cut_connections}")
            print(f"  Optimal position: ({optimal_pos.optimal_point.x:.1f}, {optimal_pos.optimal_point.y:.1f})")
            print(f"  Constrained position: ({optimal_pos.constrained_point.x:.1f}, {optimal_pos.constrained_point.y:.1f})")
            print(f"  Constraint applied: {optimal_pos.constraint_applied}")
            print(f"  Total path length: {optimal_pos.total_path_length:.1f} ALU")
        
        # Return constrained positions
        return {vid: pos.constrained_point for vid, pos in optimal_positions.items()}
    
    def _analyze_vertex_connections(self, egi: RelationalGraphWithCuts,
                                   predicate_positions: Dict[ElementID, ALUPoint]) -> Dict[ElementID, ConnectionInfo]:
        """Analyze connection patterns for each vertex."""
        connection_info = {}
        
        for vertex in egi.V:
            vertex_id = vertex.id
            vertex_area = egi.get_context(vertex_id)
            
            # Find all predicates connected to this vertex
            connected_predicates = []
            cross_cut_count = 0
            same_area_count = 0
            
            for edge_id, vertex_sequence in egi.nu.items():
                if vertex_id in vertex_sequence:
                    predicate_area = egi.get_context(edge_id)
                    connected_predicates.append((edge_id, predicate_area))
                    
                    if predicate_area != vertex_area:
                        cross_cut_count += 1
                    else:
                        same_area_count += 1
            
            connection_info[vertex_id] = ConnectionInfo(
                vertex_id=vertex_id,
                vertex_area=vertex_area,
                connected_predicates=connected_predicates,
                cross_cut_connections=cross_cut_count,
                same_area_connections=same_area_count
            )
        
        return connection_info
    
    def _calculate_optimal_vertex_position(self, info: ConnectionInfo,
                                         predicate_positions: Dict[ElementID, ALUPoint],
                                         egi: RelationalGraphWithCuts,
                                         predicate_vertex_groups: Dict[ElementID, List[ElementID]]) -> OptimalPosition:
        """Calculate optimal position for a vertex to minimize ligature path lengths."""
        
        if not info.connected_predicates:
            # No connections - use area center
            area_extent = self.constraint_system.get_area_extent(info.vertex_area)
            if area_extent:
                center_x, center_y = area_extent.available_bounds.center()
                optimal_point = ALUPoint(center_x, center_y)
            else:
                optimal_point = ALUPoint(0, 0)
            
            constrained_point = self.constraint_system.constrain_element_position(
                info.vertex_id, optimal_point, egi
            )
            
            return OptimalPosition(
                vertex_id=info.vertex_id,
                optimal_point=optimal_point,
                total_path_length=0.0,
                constrained_point=constrained_point,
                constraint_applied=(optimal_point.x != constrained_point.x or 
                                  optimal_point.y != constrained_point.y)
            )
        
        # Calculate centroid of connected predicates (weighted by connection strength)
        total_x = 0.0
        total_y = 0.0
        total_weight = 0.0
        
        for predicate_id, predicate_area in info.connected_predicates:
            if predicate_id in predicate_positions:
                pred_pos = predicate_positions[predicate_id]
                
                # Weight: same-area connections get higher weight for clustering
                weight = 2.0 if predicate_area == info.vertex_area else 1.0
                
                total_x += pred_pos.x * weight
                total_y += pred_pos.y * weight
                total_weight += weight
        
        if total_weight > 0:
            # Centroid of connected predicates
            centroid_x = total_x / total_weight
            centroid_y = total_y / total_weight
            
            # CRITICAL: Apply minimum separation from all predicates
            # Never place vertex directly on a predicate
            base_point = self._enforce_minimum_separation(
                ALUPoint(centroid_x, centroid_y), 
                info.connected_predicates, 
                predicate_positions
            )
            
            # CRITICAL: Apply multi-vertex separation for shared predicates
            # If multiple vertices connect to the same predicate, spread them out
            optimal_point = self._apply_multi_vertex_separation(
                base_point, info, predicate_vertex_groups, predicate_positions
            )
        else:
            # Fallback to area center
            area_extent = self.constraint_system.get_area_extent(info.vertex_area)
            if area_extent:
                center_x, center_y = area_extent.available_bounds.center()
                optimal_point = ALUPoint(center_x, center_y)
            else:
                optimal_point = ALUPoint(0, 0)
        
        # Apply area constraints
        constrained_point = self.constraint_system.constrain_element_position(
            info.vertex_id, optimal_point, egi
        )
        
        # Calculate total path length with constrained position
        total_path_length = self._calculate_total_path_length(
            constrained_point, info.connected_predicates, predicate_positions
        )
        
        return OptimalPosition(
            vertex_id=info.vertex_id,
            optimal_point=optimal_point,
            total_path_length=total_path_length,
            constrained_point=constrained_point,
            constraint_applied=(optimal_point.x != constrained_point.x or 
                              optimal_point.y != constrained_point.y)
        )
    
    def _calculate_total_path_length(self, vertex_pos: ALUPoint,
                                   connected_predicates: List[Tuple[ElementID, ElementID]],
                                   predicate_positions: Dict[ElementID, ALUPoint]) -> float:
        """Calculate total ligature path length from vertex to all connected predicates."""
        total_length = 0.0
        
        for predicate_id, _ in connected_predicates:
            if predicate_id in predicate_positions:
                pred_pos = predicate_positions[predicate_id]
                
                # Euclidean distance (simplified - could use more sophisticated path calculation)
                dx = vertex_pos.x - pred_pos.x
                dy = vertex_pos.y - pred_pos.y
                distance = math.sqrt(dx * dx + dy * dy)
                
                total_length += distance
        
        return total_length
    
    def optimize_predicate_positions(self, egi: RelationalGraphWithCuts,
                                   initial_positions: Dict[ElementID, ALUPoint],
                                   area_bounds: Dict[ElementID, ALURect]) -> Dict[ElementID, ALUPoint]:
        """
        Optimize predicate positions within their areas for better ligature routing.
        
        Args:
            egi: The EGI structure
            initial_positions: Initial predicate positions from Phase 2
            area_bounds: Area bounds from Phase 1
            
        Returns:
            Dictionary of optimized predicate positions
        """
        print("🎯 OPTIMIZING PREDICATE POSITIONS")
        print("=" * 40)
        
        optimized_positions = initial_positions.copy()
        
        # For each predicate, try to position it optimally within its area
        for edge_id, initial_pos in initial_positions.items():
            if edge_id not in {e.id for e in egi.E}:
                continue  # Skip non-predicates
                
            predicate_area = egi.get_context(edge_id)
            area_extent = self.constraint_system.get_area_extent(predicate_area)
            
            if not area_extent:
                continue
            
            # Get connected vertices
            connected_vertices = egi.nu.get(edge_id, ())
            
            if not connected_vertices:
                continue
            
            # Calculate optimal position based on vertex positions (if we had them)
            # For now, keep initial position but ensure it's within area bounds
            constrained_pos = self.constraint_system.constrain_element_position(
                edge_id, initial_pos, egi
            )
            
            optimized_positions[edge_id] = constrained_pos
            
            if initial_pos.x != constrained_pos.x or initial_pos.y != constrained_pos.y:
                print(f"Constrained predicate {edge_id}: "
                      f"({initial_pos.x:.1f},{initial_pos.y:.1f}) → "
                      f"({constrained_pos.x:.1f},{constrained_pos.y:.1f})")
        
        return optimized_positions
    
    def _enforce_minimum_separation(self, proposed_point: ALUPoint,
                                   connected_predicates: List[Tuple[ElementID, ElementID]],
                                   predicate_positions: Dict[ElementID, ALUPoint]) -> ALUPoint:
        """
        Enforce minimum separation between vertex and all predicates.
        
        CRITICAL: Prevents vertices from being placed directly on predicates,
        which would violate the exclusive positioning principle.
        """
        MIN_SEPARATION = 1.0  # ALU minimum distance between any two elements
        
        adjusted_x = proposed_point.x
        adjusted_y = proposed_point.y
        
        # Check distance to each connected predicate
        for predicate_id, _ in connected_predicates:
            if predicate_id in predicate_positions:
                pred_pos = predicate_positions[predicate_id]
                
                # Calculate distance
                dx = adjusted_x - pred_pos.x
                dy = adjusted_y - pred_pos.y
                distance = math.sqrt(dx * dx + dy * dy)
                
                # If too close, move vertex away
                if distance < MIN_SEPARATION:
                    if distance > 0.001:  # Avoid division by zero
                        # Move vertex away from predicate
                        scale = MIN_SEPARATION / distance
                        adjusted_x = pred_pos.x + dx * scale
                        adjusted_y = pred_pos.y + dy * scale
                    else:
                        # If exactly on predicate, offset by minimum separation
                        adjusted_x = pred_pos.x + MIN_SEPARATION
                        adjusted_y = pred_pos.y
        
        return ALUPoint(adjusted_x, adjusted_y)
    
    def _group_vertices_by_predicates(self, egi: RelationalGraphWithCuts) -> Dict[ElementID, List[ElementID]]:
        """Group vertices by the predicates they connect to."""
        predicate_vertex_groups = {}
        
        for edge_id, vertex_sequence in egi.nu.items():
            predicate_vertex_groups[edge_id] = list(vertex_sequence)
        
        return predicate_vertex_groups
    
    def _apply_multi_vertex_separation(self, base_point: ALUPoint, 
                                     info: ConnectionInfo,
                                     predicate_vertex_groups: Dict[ElementID, List[ElementID]],
                                     predicate_positions: Dict[ElementID, ALUPoint]) -> ALUPoint:
        """
        Apply separation for vertices that share predicates.
        
        CRITICAL: When multiple vertices connect to the same predicate (like Q connecting to y,z),
        they must be positioned on opposite sides or spread around the predicate.
        """
        # Find predicates that connect to multiple vertices
        for predicate_id, predicate_area in info.connected_predicates:
            if predicate_id in predicate_vertex_groups:
                connected_vertices = predicate_vertex_groups[predicate_id]
                
                if len(connected_vertices) > 1:
                    # Multiple vertices connect to this predicate - need separation
                    vertex_index = connected_vertices.index(info.vertex_id)
                    total_vertices = len(connected_vertices)
                    
                    if predicate_id in predicate_positions:
                        pred_pos = predicate_positions[predicate_id]
                        
                        # Spread vertices around the predicate in a circle
                        angle_step = 2 * math.pi / total_vertices
                        angle = vertex_index * angle_step
                        
                        # Distance from predicate (minimum separation + some spacing)
                        separation_distance = 2.0  # ALU - increased for better separation
                        
                        # Calculate position around predicate
                        offset_x = separation_distance * math.cos(angle)
                        offset_y = separation_distance * math.sin(angle)
                        
                        separated_point = ALUPoint(
                            pred_pos.x + offset_x,
                            pred_pos.y + offset_y
                        )
                        
                        print(f"  Multi-vertex separation: {info.vertex_id} positioned at angle {angle:.1f} "
                              f"around {predicate_id} (vertex {vertex_index+1}/{total_vertices})")
                        
                        return separated_point
        
        # No multi-vertex separation needed
        return base_point
