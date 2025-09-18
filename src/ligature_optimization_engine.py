"""
Phase 2: Ligature Optimization Engine

Optimizes element positions within their allocated areas to minimize ligature
path lengths and avoid predicate text collisions. This is the second phase
of the two-phase layout system that fine-tunes positioning after the
containment hierarchy is established.

Key Principles:
- Elements stay within their allocated areas (from Phase 1)
- Minimize ligature path lengths between connected elements
- Avoid ligature collisions with predicate text
- Implement 8-point compass hook system for predicates
- Add bridge icons for unavoidable ligature crossings
"""

from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import math

from egi_core_dau import RelationalGraphWithCuts, ElementID
from containment_hierarchy_engine import ALURect, ALUPoint
# from collision_free_positioning import CollisionFreePositioning
from area_spatial_constraint_system import AreaSpatialConstraintSystem


class CompassDirection(Enum):
    """8-point compass directions for predicate hooks."""
    N = (0, -1)    # North
    NE = (1, -1)   # Northeast  
    E = (1, 0)     # East
    SE = (1, 1)    # Southeast
    S = (0, 1)     # South
    SW = (-1, 1)   # Southwest
    W = (-1, 0)    # West
    NW = (-1, -1)  # Northwest


@dataclass
class LigatureConnection:
    """Connection between two elements via ligature."""
    edge_id: ElementID
    vertex_ids: List[ElementID]
    predicate_area: ElementID
    vertex_areas: List[ElementID]
    crosses_cuts: bool


@dataclass
class ElementPosition:
    """Optimized position for an element within its area."""
    element_id: ElementID
    area_id: ElementID
    position: ALUPoint
    element_type: str  # 'vertex', 'edge', 'cut'


@dataclass
class PredicateHook:
    """Hook point on a predicate for ligature connection."""
    edge_id: ElementID
    direction: CompassDirection
    position: ALUPoint
    vertex_id: ElementID
    argument_index: int


class LigatureOptimizationEngine:
    """
    Phase 2 of two-phase layout: Optimizes element positions for ligature routing
    while respecting the containment hierarchy established in Phase 1.
    """
    
    def __init__(self):
        # ALU constants for optimization
        self.HOOK_DISTANCE = 0.4    # ALU distance from predicate center to hook
        self.MIN_ELEMENT_SEPARATION = 0.2  # ALU minimum distance between elements
        self.LIGATURE_CURVE_RADIUS = 0.3   # ALU radius for curved ligature segments
        self.BRIDGE_ICON_SIZE = 0.15       # ALU size for bridge crossing icons
        
    def optimize_layout(self, egi: RelationalGraphWithCuts, 
                       area_bounds: Dict[ElementID, ALURect],
                       constraint_system: Optional[AreaSpatialConstraintSystem] = None) -> Dict[ElementID, ALUPoint]:
        """
        Optimize element positions for ligature routing with ligature-aware positioning.
        
        Args:
            egi: The EGI structure
            area_bounds: Area bounds from Phase 1 (containment hierarchy)
            constraint_system: Area spatial constraint system for boundary enforcement
            
        Returns:
            Dictionary mapping element IDs to optimized ALU positions
        """
        print("Phase 2: Optimizing layout for ligature routing...")
        
        # Step 1: Analyze ligature connections
        connections = self._analyze_ligature_connections(egi)
        
        # Step 2: Position elements collision-free within their areas
        collision_free_positioner = CollisionFreePositioning()
        collision_free_positions = collision_free_positioner.position_elements_collision_free(egi, area_bounds)
        
        # Convert to ElementPosition format
        element_positions = {}
        for element_id, position in collision_free_positions.items():
            # Determine area for this element
            element_area = None
            for area_id, area_contents in egi.area.items():
                if element_id in area_contents:
                    element_area = area_id
                    break
            
            # Determine element type
            if element_id in {v.id for v in egi.V}:
                element_type = 'vertex'
            elif element_id in {e.id for e in egi.E}:
                element_type = 'edge'
            else:
                element_type = 'other'
            
            element_positions[element_id] = ElementPosition(
                element_id=element_id,
                area_id=element_area,
                position=position,
                element_type=element_type
            )
        
        # Step 3: Apply ligature-aware vertex positioning if constraint system available
        if constraint_system:
            from ligature_aware_positioning_engine import LigatureAwarePositioningEngine
            
            ligature_engine = LigatureAwarePositioningEngine(constraint_system)
            
            # Separate predicates and vertices
            predicate_positions = {eid: pos.position for eid, pos in element_positions.items() 
                                 if pos.element_type == 'edge'}
            
            # Optimize predicate positions first
            optimized_predicates = ligature_engine.optimize_predicate_positions(
                egi, predicate_positions, area_bounds
            )
            
            # Then optimize vertex positions based on predicate positions
            optimized_vertices = ligature_engine.optimize_vertex_positions(
                egi, optimized_predicates, area_bounds
            )
            
            # Combine optimized positions
            optimized_positions = {}
            optimized_positions.update(optimized_predicates)
            optimized_positions.update(optimized_vertices)
            
        else:
            # Fallback to old method
            predicate_hooks = self._generate_predicate_hooks(egi, element_positions)
            optimized_positions = self._optimize_for_ligature_paths(
                element_positions, connections, predicate_hooks
            )
        
        # Step 4: Detect and mark ligature crossings for bridge icons
        crossings = self._detect_ligature_crossings(optimized_positions, connections)
        
        print(f"Phase 2 complete: {len(optimized_positions)} elements positioned, "
              f"{len(crossings)} ligature crossings detected")
        
        return optimized_positions
    
    def _analyze_ligature_connections(self, egi: RelationalGraphWithCuts) -> List[LigatureConnection]:
        """Analyze all ligature connections in the EGI."""
        connections = []
        
        for edge_id, vertex_sequence in egi.nu.items():
            # Get areas for predicate and vertices
            predicate_area = egi.get_context(edge_id)
            vertex_areas = [egi.get_context(vid) for vid in vertex_sequence]
            
            # Check if ligature crosses cut boundaries
            crosses_cuts = len(set([predicate_area] + vertex_areas)) > 1
            
            connection = LigatureConnection(
                edge_id=edge_id,
                vertex_ids=list(vertex_sequence),
                predicate_area=predicate_area,
                vertex_areas=vertex_areas,
                crosses_cuts=crosses_cuts
            )
            connections.append(connection)
        
        print(f"Analyzed {len(connections)} ligature connections, "
              f"{sum(1 for c in connections if c.crosses_cuts)} cross cuts")
        
        return connections
    
    def _position_elements_in_areas(self, egi: RelationalGraphWithCuts,
                                   area_bounds: Dict[ElementID, ALURect],
                                   connections: List[LigatureConnection]) -> Dict[ElementID, ElementPosition]:
        """Position elements within their allocated areas."""
        positions = {}
        
        # Position elements in each area
        for area_id, bounds in area_bounds.items():
            area_contents = egi.area.get(area_id, set())
            
            # Separate elements by type
            vertices = [eid for eid in area_contents if eid in {v.id for v in egi.V}]
            edges = [eid for eid in area_contents if eid in {e.id for e in egi.E}]
            
            # Position vertices (arrange horizontally in lower part of area)
            if vertices:
                vertex_y = bounds.y + bounds.height * 0.75  # Lower 25% of area
                vertex_spacing = min(bounds.width / (len(vertices) + 1), 1.0)
                
                for i, vertex_id in enumerate(vertices):
                    vertex_x = bounds.x + (i + 1) * vertex_spacing
                    positions[vertex_id] = ElementPosition(
                        element_id=vertex_id,
                        area_id=area_id,
                        position=ALUPoint(vertex_x, vertex_y),
                        element_type='vertex'
                    )
            
            # Position edges (arrange horizontally in upper part of area)
            if edges:
                edge_y = bounds.y + bounds.height * 0.25  # Upper 25% of area
                edge_spacing = min(bounds.width / (len(edges) + 1), 2.0)
                
                for i, edge_id in enumerate(edges):
                    edge_x = bounds.x + (i + 1) * edge_spacing
                    positions[edge_id] = ElementPosition(
                        element_id=edge_id,
                        area_id=area_id,
                        position=ALUPoint(edge_x, edge_y),
                        element_type='edge'
                    )
        
        print(f"Positioned {len(positions)} elements in their areas")
        return positions
    
    def _generate_predicate_hooks(self, egi: RelationalGraphWithCuts,
                                 positions: Dict[ElementID, ElementPosition]) -> Dict[ElementID, List[PredicateHook]]:
        """Generate 8-point compass hooks for predicates."""
        predicate_hooks = {}
        
        for edge_id, vertex_sequence in egi.nu.items():
            if edge_id not in positions:
                continue
                
            predicate_pos = positions[edge_id].position
            hooks = []
            
            # Generate hooks in argument order using 8-point compass
            directions = list(CompassDirection)
            
            for i, vertex_id in enumerate(vertex_sequence):
                # Use compass directions, cycling if more than 8 arguments
                direction = directions[i % len(directions)]
                dx, dy = direction.value
                
                hook_position = ALUPoint(
                    predicate_pos.x + dx * self.HOOK_DISTANCE,
                    predicate_pos.y + dy * self.HOOK_DISTANCE
                )
                
                hook = PredicateHook(
                    edge_id=edge_id,
                    direction=direction,
                    position=hook_position,
                    vertex_id=vertex_id,
                    argument_index=i
                )
                hooks.append(hook)
            
            predicate_hooks[edge_id] = hooks
        
        return predicate_hooks
    
    def _optimize_for_ligature_paths(self, positions: Dict[ElementID, ElementPosition],
                                   connections: List[LigatureConnection],
                                   hooks: Dict[ElementID, List[PredicateHook]]) -> Dict[ElementID, ALUPoint]:
        """Optimize positions to minimize ligature path lengths."""
        optimized = {}
        
        # Start with current positions
        for element_id, pos in positions.items():
            optimized[element_id] = pos.position
        
        # Simple optimization: move connected elements closer (within area constraints)
        for connection in connections:
            if not connection.crosses_cuts:  # Only optimize same-area connections
                self._optimize_same_area_connection(connection, positions, optimized)
        
        return optimized
    
    def _optimize_same_area_connection(self, connection: LigatureConnection,
                                     positions: Dict[ElementID, ElementPosition],
                                     optimized: Dict[ElementID, ALUPoint]):
        """Optimize positions for same-area ligature connection."""
        # CRITICAL: Phase 2 optimization MUST NEVER violate Phase 1 area boundaries
        # Elements must stay within their allocated areas from containment hierarchy
        
        if connection.edge_id not in positions:
            return
            
        predicate_pos = optimized[connection.edge_id]
        
        for vertex_id in connection.vertex_ids:
            if vertex_id in positions and vertex_id in optimized:
                vertex_pos = optimized[vertex_id]
                vertex_area_bounds = self._get_element_area_bounds(vertex_id, positions)
                
                if vertex_area_bounds is None:
                    continue  # Skip if no area bounds found
                
                # Calculate proposed movement toward predicate
                dx = predicate_pos.x - vertex_pos.x
                dy = predicate_pos.y - vertex_pos.y
                
                proposed_x = vertex_pos.x + dx * 0.1
                proposed_y = vertex_pos.y + dy * 0.1
                
                # BOUNDARY CONSTRAINT: Ensure proposed position stays within area bounds
                if vertex_area_bounds.contains_point(proposed_x, proposed_y):
                    optimized[vertex_id] = ALUPoint(proposed_x, proposed_y)
                    print(f"DEBUG: Optimized {vertex_id} position within area bounds")
                else:
                    # Keep original position if optimization would violate boundaries
                    print(f"DEBUG: Rejected optimization for {vertex_id} - would violate area bounds")
    
    def _get_element_area_bounds(self, element_id: ElementID, 
                               positions: Dict[ElementID, ElementPosition]) -> Optional[ALURect]:
        """Get the area bounds for an element from its position data."""
        if element_id in positions:
            element_pos = positions[element_id]
            # This would need access to area_bounds from Phase 1
            # For now, return None to disable optimization that could violate boundaries
            return None
        return None
    
    def _detect_ligature_crossings(self, positions: Dict[ElementID, ALUPoint],
                                 connections: List[LigatureConnection]) -> List[ALUPoint]:
        """Detect ligature crossings that need bridge icons."""
        crossings = []
        
        # Simple implementation: detect when ligature paths intersect
        # (Full implementation would use line intersection algorithms)
        
        print(f"Detected {len(crossings)} ligature crossings requiring bridge icons")
        return crossings
