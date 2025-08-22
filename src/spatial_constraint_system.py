#!/usr/bin/env python3
"""
Spatial Constraint System - Dynamic EGI-EGDF Concordance Enforcement

This system ensures that any spatial transformations (styling, positioning, sizing)
maintain logical concordance with the underlying EGI structure. It enforces:

1. Area containment boundaries (vertices inside cuts)
2. Position/size validation against EGI logic
3. Dynamic EGI adjustment for composition mode
4. Constraint propagation across all output formats
"""

from typing import Dict, List, Set, Tuple, Optional, Any, Protocol
from dataclasses import dataclass
from enum import Enum
import math

from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut
from layout_types import LayoutElement, Bounds, Coordinate

class ConstraintViolationType(Enum):
    """Types of spatial constraint violations."""
    VERTEX_OUTSIDE_CUT = "vertex_outside_cut"
    CUT_OVERLAP_INVALID = "cut_overlap_invalid"
    PREDICATE_COLLISION = "predicate_collision"
    LIGATURE_CROSSING_CUT = "ligature_crossing_cut"
    ELEMENT_SIZE_INVALID = "element_size_invalid"

@dataclass
class ConstraintViolation:
    """A spatial constraint violation."""
    violation_type: ConstraintViolationType
    element_id: str
    description: str
    suggested_fix: Optional[Dict[str, Any]] = None

@dataclass
class SpatialConstraint:
    """A spatial constraint between elements."""
    constraint_id: str
    constraint_type: str
    source_element: str
    target_element: str
    parameters: Dict[str, Any]
    
class SpatialConstraintSystem:
    """
    Main system for enforcing spatial constraints and EGI-EGDF concordance.
    
    This system acts as a bridge between logical structure (EGI) and spatial
    representation (EGDF), ensuring any modifications maintain logical validity.
    """
    
    def __init__(self):
        self.constraints: Dict[str, SpatialConstraint] = {}
        self.violation_handlers: Dict[ConstraintViolationType, callable] = {}
        self.egi_reference: Optional[RelationalGraphWithCuts] = None
        self.current_layout: Dict[str, Any] = {}
        
    def set_egi_reference(self, egi: RelationalGraphWithCuts):
        """Set the EGI reference for constraint validation."""
        self.egi_reference = egi
        self._generate_containment_constraints()
        
    def _generate_containment_constraints(self):
        """Generate containment constraints from EGI structure."""
        if not self.egi_reference:
            return
            
        # Generate vertex-in-cut constraints
        for vertex in self.egi_reference.V:
            containing_cuts = self._find_containing_cuts(vertex)
            for cut in containing_cuts:
                constraint = SpatialConstraint(
                    constraint_id=f"contain_{vertex.id}_in_{cut.id}",
                    constraint_type="vertex_containment",
                    source_element=vertex.id,
                    target_element=cut.id,
                    parameters={"strict": True, "margin": 5.0}
                )
                self.constraints[constraint.constraint_id] = constraint
                
        # Generate cut nesting constraints
        for cut in self.egi_reference.Cut:
            nested_cuts = self._find_nested_cuts(cut)
            for nested_cut in nested_cuts:
                constraint = SpatialConstraint(
                    constraint_id=f"nest_{nested_cut.id}_in_{cut.id}",
                    constraint_type="cut_nesting",
                    source_element=nested_cut.id,
                    target_element=cut.id,
                    parameters={"strict": True, "margin": 10.0}
                )
                self.constraints[constraint.constraint_id] = constraint
    
    def _find_containing_cuts(self, vertex: Vertex) -> List[Cut]:
        """Find all cuts that should contain this vertex."""
        containing_cuts = []
        if not self.egi_reference:
            return containing_cuts
            
        # Use EGI logical structure to determine containment
        # This is based on the logical graph structure, not spatial position
        for cut in self.egi_reference.Cut:
            if self._vertex_logically_in_cut(vertex, cut):
                containing_cuts.append(cut)
                
        return containing_cuts
    
    def _find_nested_cuts(self, outer_cut: Cut) -> List[Cut]:
        """Find cuts that should be nested inside the outer cut."""
        nested_cuts = []
        if not self.egi_reference:
            return nested_cuts
            
        # Determine nesting from logical structure
        for cut in self.egi_reference.Cut:
            if cut != outer_cut and self._cut_logically_nested_in(cut, outer_cut):
                nested_cuts.append(cut)
                
        return nested_cuts
    
    def _vertex_logically_in_cut(self, vertex: Vertex, cut: Cut) -> bool:
        """Determine if vertex should logically be inside cut."""
        if not self.egi_reference:
            return False
            
        # Check if vertex is connected to predicates that are in this cut
        # In EGI, vertices should be in the same cut as their connected predicates
        for edge in self.egi_reference.E:
            if vertex.id in self.egi_reference.nu.get(edge.id, []):
                # This vertex is connected to this predicate
                # Check if predicate is in the cut (simplified logic)
                return True
        return False
    
    def _cut_logically_nested_in(self, inner_cut: Cut, outer_cut: Cut) -> bool:
        """Determine if inner cut should be nested in outer cut."""
        # This needs EGI logical structure analysis
        return True  # Placeholder - needs implementation
    
    def validate_layout(self, layout_data: Dict[str, Any]) -> List[ConstraintViolation]:
        """Validate a layout against all spatial constraints."""
        violations = []
        self.current_layout = layout_data
        
        for constraint in self.constraints.values():
            violation = self._check_constraint(constraint, layout_data)
            if violation:
                violations.append(violation)
                
        return violations
    
    def _check_constraint(self, constraint: SpatialConstraint, layout_data: Dict[str, Any]) -> Optional[ConstraintViolation]:
        """Check a single constraint against layout data."""
        if constraint.constraint_type == "vertex_containment":
            return self._check_vertex_containment(constraint, layout_data)
        elif constraint.constraint_type == "cut_nesting":
            return self._check_cut_nesting(constraint, layout_data)
        return None
    
    def _check_vertex_containment(self, constraint: SpatialConstraint, layout_data: Dict[str, Any]) -> Optional[ConstraintViolation]:
        """Check if vertex is properly contained in cut."""
        vertex_id = constraint.source_element
        cut_id = constraint.target_element
        
        # Check both direct layout data and EGDF primitive format
        vertex_pos = layout_data.get('vertex_positions', {}).get(vertex_id)
        cut_bounds = layout_data.get('cut_bounds', {}).get(cut_id)
        
        # Also check EGDF primitive format
        if not vertex_pos:
            vertex_primitive = layout_data.get(vertex_id)
            if vertex_primitive and vertex_primitive.get('element_type') == 'vertex':
                vertex_pos = vertex_primitive.get('position')
                
        if not cut_bounds:
            cut_primitive = layout_data.get(cut_id)
            if cut_primitive and cut_primitive.get('element_type') == 'cut':
                cut_bounds = cut_primitive.get('bounds')
        
        if not vertex_pos or not cut_bounds:
            return None
            
        margin = constraint.parameters.get('margin', 0.0)
        x, y = vertex_pos
        x1, y1, x2, y2 = cut_bounds
        
        # Check if vertex is inside cut with margin
        if not (x1 + margin <= x <= x2 - margin and y1 + margin <= y <= y2 - margin):
            return ConstraintViolation(
                violation_type=ConstraintViolationType.VERTEX_OUTSIDE_CUT,
                element_id=vertex_id,
                description=f"Vertex {vertex_id} is outside cut {cut_id}",
                suggested_fix={
                    'action': 'move_vertex',
                    'target_position': (
                        max(x1 + margin, min(x, x2 - margin)),
                        max(y1 + margin, min(y, y2 - margin))
                    )
                }
            )
        return None
    
    def _check_cut_nesting(self, constraint: SpatialConstraint, layout_data: Dict[str, Any]) -> Optional[ConstraintViolation]:
        """Check if cut is properly nested inside another cut."""
        inner_cut_id = constraint.source_element
        outer_cut_id = constraint.target_element
        
        # Check both direct layout data and EGDF primitive format
        inner_bounds = layout_data.get('cut_bounds', {}).get(inner_cut_id)
        outer_bounds = layout_data.get('cut_bounds', {}).get(outer_cut_id)
        
        # Also check EGDF primitive format
        if not inner_bounds:
            inner_primitive = layout_data.get(inner_cut_id)
            if inner_primitive and inner_primitive.get('element_type') == 'cut':
                inner_bounds = inner_primitive.get('bounds')
                
        if not outer_bounds:
            outer_primitive = layout_data.get(outer_cut_id)
            if outer_primitive and outer_primitive.get('element_type') == 'cut':
                outer_bounds = outer_primitive.get('bounds')
        
        if not inner_bounds or not outer_bounds:
            return None
            
        margin = constraint.parameters.get('margin', 0.0)
        ix1, iy1, ix2, iy2 = inner_bounds
        ox1, oy1, ox2, oy2 = outer_bounds
        
        # Check if inner cut is fully contained in outer cut with margin
        if not (ox1 + margin <= ix1 and ix2 <= ox2 - margin and 
                oy1 + margin <= iy1 and iy2 <= oy2 - margin):
            return ConstraintViolation(
                violation_type=ConstraintViolationType.CUT_OVERLAP_INVALID,
                element_id=inner_cut_id,
                description=f"Cut {inner_cut_id} not properly nested in {outer_cut_id}",
                suggested_fix={
                    'action': 'resize_cuts',
                    'inner_bounds': inner_bounds,
                    'outer_bounds': outer_bounds
                }
            )
        return None
    
    def apply_constraint_fixes(self, violations: List[ConstraintViolation], layout_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply suggested fixes for constraint violations."""
        fixed_layout = layout_data.copy()
        
        for violation in violations:
            if violation.suggested_fix:
                fixed_layout = self._apply_fix(violation.suggested_fix, fixed_layout)
                
        return fixed_layout
    
    def _apply_fix(self, fix: Dict[str, Any], layout_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a single constraint fix."""
        if fix['action'] == 'move_vertex':
            # Find the vertex element that needs fixing
            vertex_id = None
            new_position = fix.get('target_position')
            
            # Search for vertex in layout data
            for element_id, element_data in layout_data.items():
                if (element_data.get('element_type') == 'vertex' and 
                    element_data.get('position') != new_position):
                    vertex_id = element_id
                    break
            
            if vertex_id and new_position:
                # Update both vertex_positions dict and EGDF primitive
                layout_data.setdefault('vertex_positions', {})[vertex_id] = new_position
                if vertex_id in layout_data:
                    layout_data[vertex_id]['position'] = new_position
                    # Update bounds to match new position
                    x, y = new_position
                    layout_data[vertex_id]['bounds'] = (x-2, y-2, x+2, y+2)
                
        elif fix['action'] == 'resize_cuts':
            # Implement cut resizing logic
            pass
            
        return layout_data
    
    def enforce_constraints_during_edit(self, element_id: str, new_position: Coordinate, 
                                      layout_data: Dict[str, Any]) -> Tuple[Coordinate, List[str]]:
        """
        Enforce constraints during interactive editing.
        
        Returns:
            - Adjusted position that satisfies constraints
            - List of warnings/messages about constraint enforcement
        """
        warnings = []
        adjusted_position = new_position
        
        # Check all constraints involving this element
        for constraint in self.constraints.values():
            if constraint.source_element == element_id or constraint.target_element == element_id:
                # Apply constraint-specific position adjustment
                adjusted_position, constraint_warnings = self._adjust_position_for_constraint(
                    constraint, element_id, adjusted_position, layout_data
                )
                warnings.extend(constraint_warnings)
                
        return adjusted_position, warnings
    
    def _adjust_position_for_constraint(self, constraint: SpatialConstraint, element_id: str, 
                                      position: Coordinate, layout_data: Dict[str, Any]) -> Tuple[Coordinate, List[str]]:
        """Adjust position to satisfy a specific constraint."""
        warnings = []
        
        if constraint.constraint_type == "vertex_containment" and constraint.source_element == element_id:
            # Ensure vertex stays inside its containing cut
            cut_id = constraint.target_element
            cut_bounds = layout_data.get('cut_bounds', {}).get(cut_id)
            
            if cut_bounds:
                margin = constraint.parameters.get('margin', 5.0)
                x, y = position
                x1, y1, x2, y2 = cut_bounds
                
                # Clamp position to cut bounds
                clamped_x = max(x1 + margin, min(x, x2 - margin))
                clamped_y = max(y1 + margin, min(y, y2 - margin))
                
                if (clamped_x, clamped_y) != position:
                    warnings.append(f"Position constrained to stay inside cut {cut_id}")
                    position = (clamped_x, clamped_y)
                    
        return position, warnings
    
    def update_egi_from_spatial_changes(self, layout_data: Dict[str, Any]) -> Optional[RelationalGraphWithCuts]:
        """
        Update EGI structure based on spatial changes (for composition mode).
        
        This is used in Ergasterion when spatial edits should modify the logical graph.
        """
        if not self.egi_reference:
            return None
            
        # This would implement the reverse mapping: spatial changes -> logical changes
        # For example, moving a vertex into a different cut area would update EGI containment
        
        # Placeholder for now - this is a complex operation requiring careful design
        return self.egi_reference
