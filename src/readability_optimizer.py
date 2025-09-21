"""
Advanced Readability Optimizer for EG Diagrams

Implements "logic-indifferent" optimizations that improve diagram intelligibility
while maintaining iron-clad spatial-logical correspondence guarantees.

OPTIMIZATION CATEGORIES:
1. Collision avoidance - Prevent element overlaps
2. Overlap minimization - Reduce visual clutter
3. Spacing optimization - Improve visual hierarchy
4. Ligature crossing minimization - Reduce visual complexity
5. Label positioning - Optimize text readability
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple, Optional, Any
from enum import Enum

from layout_engine_ironclad import Point, BoundingBox, LayoutDTO
from egi_core_dau import RelationalGraphWithCuts, ElementID


class OptimizationLevel(Enum):
    """Optimization intensity levels"""
    MINIMAL = "minimal"      # Basic collision avoidance only
    STANDARD = "standard"    # Balanced optimization
    AGGRESSIVE = "aggressive" # Maximum readability optimization


@dataclass(frozen=True)
class CollisionInfo:
    """Information about element collisions"""
    element1_id: ElementID
    element2_id: ElementID
    element1_bounds: BoundingBox
    element2_bounds: BoundingBox
    overlap_area: float
    severity: float  # 0.0 = touching, 1.0 = complete overlap
    
    @property
    def collision_center(self) -> Point:
        """Center point of the collision area"""
        x1, y1 = max(self.element1_bounds.min_x, self.element2_bounds.min_x), max(self.element1_bounds.min_y, self.element2_bounds.min_y)
        x2, y2 = min(self.element1_bounds.max_x, self.element2_bounds.max_x), min(self.element1_bounds.max_y, self.element2_bounds.max_y)
        return Point((x1 + x2) / 2, (y1 + y2) / 2)


@dataclass(frozen=True)
class OptimizationConstraints:
    """Constraints for readability optimization"""
    
    # Collision avoidance
    min_element_spacing: float = 5.0
    min_label_spacing: float = 3.0
    collision_penalty_weight: float = 10.0
    
    # Overlap minimization  
    overlap_threshold: float = 0.1  # Minimum overlap to trigger optimization
    overlap_penalty_weight: float = 5.0
    
    # Spacing optimization
    preferred_element_spacing: float = 20.0
    spacing_variance_penalty: float = 2.0
    
    # Ligature optimization
    crossing_penalty_weight: float = 3.0
    ligature_length_penalty: float = 1.0
    
    # Label positioning
    label_readability_weight: float = 4.0
    label_occlusion_penalty: float = 8.0
    
    # Optimization limits
    max_iterations: int = 100
    convergence_threshold: float = 0.01
    max_displacement: float = 50.0  # Maximum element movement per iteration


class ReadabilityOptimizer:
    """
    Advanced readability optimizer for EG diagrams.
    
    Applies logic-indifferent optimizations to improve visual clarity while
    maintaining all iron-clad spatial-logical correspondence guarantees.
    """
    
    def __init__(self, constraints: Optional[OptimizationConstraints] = None):
        self.constraints = constraints or OptimizationConstraints()
        self._optimization_history = []
    
    def optimize_layout(self, layout: LayoutDTO, egi: RelationalGraphWithCuts,
                       level: OptimizationLevel = OptimizationLevel.STANDARD) -> LayoutDTO:
        """
        Optimize layout for maximum readability while preserving logical structure.
        
        Args:
            layout: Input layout from style-aware engine
            egi: EGI structure for validation
            level: Optimization intensity
            
        Returns:
            Optimized layout with improved readability
        """
        
        # Create working copy
        optimized_layout = self._create_working_copy(layout)
        
        # Apply optimization sequence based on level
        if level == OptimizationLevel.MINIMAL:
            optimized_layout = self._apply_minimal_optimization(optimized_layout, egi)
        elif level == OptimizationLevel.STANDARD:
            optimized_layout = self._apply_standard_optimization(optimized_layout, egi)
        else:  # AGGRESSIVE
            optimized_layout = self._apply_aggressive_optimization(optimized_layout, egi)
        
        # Validate that iron-clad guarantees are maintained
        self._validate_optimization(layout, optimized_layout, egi)
        
        return optimized_layout
    
    def _create_working_copy(self, layout: LayoutDTO) -> LayoutDTO:
        """Create a working copy of the layout for optimization"""
        return LayoutDTO(
            vertex_positions=layout.vertex_positions.copy(),
            predicate_positions=layout.predicate_positions.copy(),
            cut_bounds=layout.cut_bounds.copy(),
            ligature_paths=layout.ligature_paths.copy(),
            area_hierarchy=layout.area_hierarchy.copy(),
            containment_depth=layout.containment_depth.copy(),
            viewport_bounds=layout.viewport_bounds,
            style_hints=layout.style_hints.copy()
        )
    
    def _apply_minimal_optimization(self, layout: LayoutDTO, egi: RelationalGraphWithCuts) -> LayoutDTO:
        """Apply minimal optimization - basic collision avoidance only"""
        
        # Step 1: Detect and resolve critical collisions
        collisions = self._detect_collisions(layout)
        critical_collisions = [c for c in collisions if c.severity > 0.5]
        
        if critical_collisions:
            layout = self._resolve_collisions(layout, critical_collisions, egi)
        
        return layout
    
    def _apply_standard_optimization(self, layout: LayoutDTO, egi: RelationalGraphWithCuts) -> LayoutDTO:
        """Apply standard optimization - balanced approach"""
        
        for iteration in range(self.constraints.max_iterations):
            previous_score = self._calculate_readability_score(layout)
            
            # Step 1: Collision avoidance
            collisions = self._detect_collisions(layout)
            if collisions:
                layout = self._resolve_collisions(layout, collisions, egi)
            
            # Step 2: Spacing optimization
            layout = self._optimize_spacing(layout, egi)
            
            # Step 3: Label positioning
            layout = self._optimize_label_positions(layout, egi)
            
            # Step 4: Basic ligature optimization
            layout = self._optimize_ligature_routing(layout, egi)
            
            # Check convergence
            current_score = self._calculate_readability_score(layout)
            if abs(current_score - previous_score) < self.constraints.convergence_threshold:
                break
        
        return layout
    
    def _apply_aggressive_optimization(self, layout: LayoutDTO, egi: RelationalGraphWithCuts) -> LayoutDTO:
        """Apply aggressive optimization - maximum readability"""
        
        for iteration in range(self.constraints.max_iterations * 2):  # More iterations
            previous_score = self._calculate_readability_score(layout)
            
            # Step 1: Advanced collision avoidance
            collisions = self._detect_collisions(layout)
            if collisions:
                layout = self._resolve_collisions_advanced(layout, collisions, egi)
            
            # Step 2: Force-directed spacing optimization
            layout = self._apply_force_directed_optimization(layout, egi)
            
            # Step 3: Advanced label positioning
            layout = self._optimize_label_positions_advanced(layout, egi)
            
            # Step 4: Ligature crossing minimization
            layout = self._minimize_ligature_crossings(layout, egi)
            
            # Step 5: Visual hierarchy optimization
            layout = self._optimize_visual_hierarchy(layout, egi)
            
            # Check convergence
            current_score = self._calculate_readability_score(layout)
            if abs(current_score - previous_score) < self.constraints.convergence_threshold:
                break
        
        return layout
    
    def _detect_collisions(self, layout: LayoutDTO) -> List[CollisionInfo]:
        """Detect all element collisions in the layout"""
        
        collisions = []
        
        # Get all element bounds
        element_bounds = {}
        
        # Add vertex bounds
        for vertex_id, position in layout.vertex_positions.items():
            radius = 6.0  # Default vertex radius - should come from style
            bounds = BoundingBox(
                position.x - radius, position.y - radius,
                position.x + radius, position.y + radius
            )
            element_bounds[vertex_id] = bounds
        
        # Add predicate bounds
        for predicate_id, position in layout.predicate_positions.items():
            width, height = 50.0, 20.0  # Default predicate size - should come from style
            bounds = BoundingBox(
                position.x - width/2, position.y - height/2,
                position.x + width/2, position.y + height/2
            )
            element_bounds[predicate_id] = bounds
        
        # Check all pairs for collisions
        element_ids = list(element_bounds.keys())
        for i in range(len(element_ids)):
            for j in range(i + 1, len(element_ids)):
                id1, id2 = element_ids[i], element_ids[j]
                bounds1, bounds2 = element_bounds[id1], element_bounds[id2]
                
                if self._bounds_overlap(bounds1, bounds2):
                    overlap_area = self._calculate_overlap_area(bounds1, bounds2)
                    severity = self._calculate_collision_severity(bounds1, bounds2, overlap_area)
                    
                    collision = CollisionInfo(
                        element1_id=id1,
                        element2_id=id2,
                        element1_bounds=bounds1,
                        element2_bounds=bounds2,
                        overlap_area=overlap_area,
                        severity=severity
                    )
                    collisions.append(collision)
        
        return collisions
    
    def _bounds_overlap(self, bounds1: BoundingBox, bounds2: BoundingBox) -> bool:
        """Check if two bounding boxes overlap"""
        return not (bounds1.max_x < bounds2.min_x or bounds2.max_x < bounds1.min_x or
                   bounds1.max_y < bounds2.min_y or bounds2.max_y < bounds1.min_y)
    
    def _calculate_overlap_area(self, bounds1: BoundingBox, bounds2: BoundingBox) -> float:
        """Calculate the area of overlap between two bounding boxes"""
        if not self._bounds_overlap(bounds1, bounds2):
            return 0.0
        
        overlap_width = min(bounds1.max_x, bounds2.max_x) - max(bounds1.min_x, bounds2.min_x)
        overlap_height = min(bounds1.max_y, bounds2.max_y) - max(bounds1.min_y, bounds2.min_y)
        
        return overlap_width * overlap_height
    
    def _calculate_collision_severity(self, bounds1: BoundingBox, bounds2: BoundingBox, overlap_area: float) -> float:
        """Calculate collision severity (0.0 = touching, 1.0 = complete overlap)"""
        area1 = bounds1.width * bounds1.height
        area2 = bounds2.width * bounds2.height
        min_area = min(area1, area2)
        
        if min_area == 0:
            return 0.0
        
        return min(1.0, overlap_area / min_area)
    
    def _resolve_collisions(self, layout: LayoutDTO, collisions: List[CollisionInfo], 
                           egi: RelationalGraphWithCuts) -> LayoutDTO:
        """Resolve collisions by adjusting element positions"""
        
        # Sort collisions by severity (most severe first)
        collisions.sort(key=lambda c: c.severity, reverse=True)
        
        for collision in collisions:
            layout = self._resolve_single_collision(layout, collision, egi)
        
        return layout
    
    def _resolve_single_collision(self, layout: LayoutDTO, collision: CollisionInfo,
                                 egi: RelationalGraphWithCuts) -> LayoutDTO:
        """Resolve a single collision by moving elements apart"""
        
        # Calculate separation vector
        center1 = collision.element1_bounds.center
        center2 = collision.element2_bounds.center
        
        # If centers are identical, use random separation
        if center1.x == center2.x and center1.y == center2.y:
            separation_vector = Point(10.0, 0.0)  # Arbitrary separation
        else:
            dx = center2.x - center1.x
            dy = center2.y - center1.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance == 0:
                separation_vector = Point(10.0, 0.0)
            else:
                # Normalize and scale
                required_separation = self.constraints.min_element_spacing + collision.severity * 10.0
                scale = required_separation / distance
                separation_vector = Point(dx * scale, dy * scale)
        
        # Move elements apart (each moves half the required distance)
        half_separation = Point(separation_vector.x / 2, separation_vector.y / 2)
        
        # Update positions while respecting area constraints
        if collision.element1_id in layout.vertex_positions:
            old_pos = layout.vertex_positions[collision.element1_id]
            new_pos = Point(old_pos.x - half_separation.x, old_pos.y - half_separation.y)
            if self._position_respects_constraints(collision.element1_id, new_pos, layout, egi):
                layout.vertex_positions[collision.element1_id] = new_pos
        
        if collision.element2_id in layout.vertex_positions:
            old_pos = layout.vertex_positions[collision.element2_id]
            new_pos = Point(old_pos.x + half_separation.x, old_pos.y + half_separation.y)
            if self._position_respects_constraints(collision.element2_id, new_pos, layout, egi):
                layout.vertex_positions[collision.element2_id] = new_pos
        
        if collision.element1_id in layout.predicate_positions:
            old_pos = layout.predicate_positions[collision.element1_id]
            new_pos = Point(old_pos.x - half_separation.x, old_pos.y - half_separation.y)
            if self._position_respects_constraints(collision.element1_id, new_pos, layout, egi):
                layout.predicate_positions[collision.element1_id] = new_pos
        
        if collision.element2_id in layout.predicate_positions:
            old_pos = layout.predicate_positions[collision.element2_id]
            new_pos = Point(old_pos.x + half_separation.x, old_pos.y + half_separation.y)
            if self._position_respects_constraints(collision.element2_id, new_pos, layout, egi):
                layout.predicate_positions[collision.element2_id] = new_pos
        
        return layout
    
    def _position_respects_constraints(self, element_id: ElementID, new_position: Point,
                                     layout: LayoutDTO, egi: RelationalGraphWithCuts) -> bool:
        """Check if a new position respects area containment constraints"""
        
        # Find which area this element belongs to
        element_area = None
        for area_id, elements in layout.area_hierarchy.items():
            if element_id in elements:
                element_area = area_id
                break
        
        if element_area is None:
            return True  # No constraints
        
        # Check if new position is within area bounds
        if element_area in layout.cut_bounds:
            area_bounds = layout.cut_bounds[element_area]
            margin = 5.0  # Small margin for safety
            
            return (area_bounds.min_x + margin <= new_position.x <= area_bounds.max_x - margin and
                   area_bounds.min_y + margin <= new_position.y <= area_bounds.max_y - margin)
        
        return True  # No area bounds (e.g., sheet level)
    
    def _optimize_spacing(self, layout: LayoutDTO, egi: RelationalGraphWithCuts) -> LayoutDTO:
        """Optimize element spacing for better visual hierarchy"""
        
        # Apply gentle force-directed adjustment to improve spacing uniformity
        for area_id, elements in layout.area_hierarchy.items():
            area_elements = list(elements)
            
            if len(area_elements) < 2:
                continue
            
            # Calculate current spacing variance
            positions = []
            for elem_id in area_elements:
                if elem_id in layout.vertex_positions:
                    positions.append(layout.vertex_positions[elem_id])
                elif elem_id in layout.predicate_positions:
                    positions.append(layout.predicate_positions[elem_id])
            
            if len(positions) < 2:
                continue
            
            # Apply spacing optimization within area bounds
            layout = self._apply_spacing_forces(layout, area_elements, positions, area_id, egi)
        
        return layout
    
    def _apply_spacing_forces(self, layout: LayoutDTO, elements: List[ElementID], 
                             positions: List[Point], area_id: ElementID, egi: RelationalGraphWithCuts) -> LayoutDTO:
        """Apply force-directed spacing optimization within an area"""
        
        # Simple repulsion forces to improve spacing uniformity
        force_strength = 0.1  # Gentle adjustment
        
        for i, elem_id in enumerate(elements):
            if i >= len(positions):
                continue
                
            current_pos = positions[i]
            total_force = Point(0.0, 0.0)
            
            # Calculate repulsion from other elements
            for j, other_pos in enumerate(positions):
                if i == j:
                    continue
                
                dx = current_pos.x - other_pos.x
                dy = current_pos.y - other_pos.y
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance > 0 and distance < self.constraints.preferred_element_spacing:
                    # Apply repulsion force
                    force_magnitude = force_strength * (self.constraints.preferred_element_spacing - distance) / distance
                    total_force = Point(
                        total_force.x + dx * force_magnitude,
                        total_force.y + dy * force_magnitude
                    )
            
            # Apply force to position
            new_position = Point(
                current_pos.x + total_force.x,
                current_pos.y + total_force.y
            )
            
            # Update position if it respects constraints
            if self._position_respects_constraints(elem_id, new_position, layout, egi):
                if elem_id in layout.vertex_positions:
                    layout.vertex_positions[elem_id] = new_position
                elif elem_id in layout.predicate_positions:
                    layout.predicate_positions[elem_id] = new_position
        
        return layout
    
    def _optimize_label_positions(self, layout: LayoutDTO, egi: RelationalGraphWithCuts) -> LayoutDTO:
        """Optimize label positions for maximum readability"""
        
        # For now, this is a placeholder - label positioning would be handled
        # by the renderer based on style specifications
        return layout
    
    def _optimize_ligature_routing(self, layout: LayoutDTO, egi: RelationalGraphWithCuts) -> LayoutDTO:
        """Basic ligature routing optimization"""
        
        # This would implement improved ligature routing to minimize crossings
        # For now, return unchanged - advanced routing is a separate feature
        return layout
    
    def _calculate_readability_score(self, layout: LayoutDTO) -> float:
        """Calculate overall readability score for the layout"""
        
        score = 0.0
        
        # Collision penalty
        collisions = self._detect_collisions(layout)
        collision_penalty = sum(c.severity * self.constraints.collision_penalty_weight for c in collisions)
        score -= collision_penalty
        
        # Spacing uniformity bonus
        spacing_score = self._calculate_spacing_score(layout)
        score += spacing_score
        
        # Ligature complexity penalty (placeholder)
        ligature_penalty = len(layout.ligature_paths) * 0.1  # Simple metric
        score -= ligature_penalty
        
        return score
    
    def _calculate_spacing_score(self, layout: LayoutDTO) -> float:
        """Calculate spacing uniformity score"""
        
        total_score = 0.0
        
        for area_id, elements in layout.area_hierarchy.items():
            positions = []
            for elem_id in elements:
                if elem_id in layout.vertex_positions:
                    positions.append(layout.vertex_positions[elem_id])
                elif elem_id in layout.predicate_positions:
                    positions.append(layout.predicate_positions[elem_id])
            
            if len(positions) < 2:
                continue
            
            # Calculate spacing variance
            distances = []
            for i in range(len(positions)):
                for j in range(i + 1, len(positions)):
                    dx = positions[i].x - positions[j].x
                    dy = positions[i].y - positions[j].y
                    distance = math.sqrt(dx*dx + dy*dy)
                    distances.append(distance)
            
            if distances:
                mean_distance = sum(distances) / len(distances)
                variance = sum((d - mean_distance)**2 for d in distances) / len(distances)
                # Lower variance = higher score
                area_score = max(0, 100 - variance)
                total_score += area_score
        
        return total_score
    
    def _validate_optimization(self, original: LayoutDTO, optimized: LayoutDTO, 
                              egi: RelationalGraphWithCuts) -> None:
        """Validate that optimization preserves iron-clad guarantees"""
        
        # Check that all elements are still positioned
        assert len(optimized.vertex_positions) == len(original.vertex_positions)
        assert len(optimized.predicate_positions) == len(original.predicate_positions)
        assert len(optimized.cut_bounds) == len(original.cut_bounds)
        
        # Check that area hierarchy is preserved
        assert optimized.area_hierarchy == original.area_hierarchy
        assert optimized.containment_depth == original.containment_depth
        
        # Check that elements remain within their designated areas
        for area_id, elements in optimized.area_hierarchy.items():
            if area_id in optimized.cut_bounds:
                area_bounds = optimized.cut_bounds[area_id]
                
                for elem_id in elements:
                    if elem_id in optimized.vertex_positions:
                        pos = optimized.vertex_positions[elem_id]
                        assert area_bounds.contains_point(pos, margin=10.0), \
                            f"Vertex {elem_id} moved outside area {area_id}"
                    
                    if elem_id in optimized.predicate_positions:
                        pos = optimized.predicate_positions[elem_id]
                        assert area_bounds.contains_point(pos, margin=10.0), \
                            f"Predicate {elem_id} moved outside area {area_id}"
    
    # Placeholder methods for advanced optimization features
    def _resolve_collisions_advanced(self, layout: LayoutDTO, collisions: List[CollisionInfo], 
                                    egi: RelationalGraphWithCuts) -> LayoutDTO:
        """Advanced collision resolution with multi-element optimization"""
        return self._resolve_collisions(layout, collisions, egi)
    
    def _apply_force_directed_optimization(self, layout: LayoutDTO, egi: RelationalGraphWithCuts) -> LayoutDTO:
        """Apply force-directed layout optimization"""
        return self._optimize_spacing(layout, egi)
    
    def _optimize_label_positions_advanced(self, layout: LayoutDTO, egi: RelationalGraphWithCuts) -> LayoutDTO:
        """Advanced label positioning with occlusion avoidance"""
        return self._optimize_label_positions(layout, egi)
    
    def _minimize_ligature_crossings(self, layout: LayoutDTO, egi: RelationalGraphWithCuts) -> LayoutDTO:
        """Minimize ligature crossings through routing optimization"""
        return self._optimize_ligature_routing(layout, egi)
    
    def _optimize_visual_hierarchy(self, layout: LayoutDTO, egi: RelationalGraphWithCuts) -> LayoutDTO:
        """Optimize visual hierarchy and emphasis"""
        return layout


# Convenience function for easy integration
def optimize_layout_readability(layout: LayoutDTO, egi: RelationalGraphWithCuts,
                               level: OptimizationLevel = OptimizationLevel.STANDARD,
                               constraints: Optional[OptimizationConstraints] = None) -> LayoutDTO:
    """
    Optimize layout for maximum readability.
    
    Args:
        layout: Input layout from style-aware engine
        egi: EGI structure for validation
        level: Optimization intensity
        constraints: Custom optimization constraints
        
    Returns:
        Optimized layout with improved readability
    """
    optimizer = ReadabilityOptimizer(constraints)
    return optimizer.optimize_layout(layout, egi, level)
