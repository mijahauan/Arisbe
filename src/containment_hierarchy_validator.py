#!/usr/bin/env python3
"""
Containment Hierarchy Validator - Ensures Graphviz layout respects EGI area mappings

This module validates that the spatial positioning produced by Graphviz corresponds
to the logical containment hierarchy defined in the EGI area mapping.
"""

from typing import Dict, Set, Tuple, Optional, Any, List
from dataclasses import dataclass
from src.egi_core_dau import RelationalGraphWithCuts

# Type aliases
Bounds = Tuple[float, float, float, float]  # x1, y1, x2, y2
Position = Tuple[float, float]

@dataclass
class ContainmentViolation:
    """Represents a violation of containment hierarchy."""
    violation_type: str
    element_id: str
    container_id: Optional[str]
    message: str
    severity: str  # 'error', 'warning'

class ContainmentHierarchyValidator:
    """Validates that spatial layout respects EGI area containment."""
    
    def __init__(self, egi: RelationalGraphWithCuts):
        self.egi = egi
        self.violations = []
    
    def validate_layout(self, element_positions: Dict[str, Position], 
                       cut_bounds: Dict[str, Bounds]) -> List[ContainmentViolation]:
        """Validate that layout respects EGI containment hierarchy."""
        self.violations = []
        
        # Validate area mapping consistency
        self._validate_area_mapping_consistency()
        
        # Validate spatial containment
        self._validate_spatial_containment(element_positions, cut_bounds)
        
        # Validate non-overlapping elements
        self._validate_non_overlapping_elements(element_positions)
        
        # Validate nested cuts
        self._validate_nested_cuts(cut_bounds)
        
        return self.violations
    
    def _validate_area_mapping_consistency(self):
        """Validate EGI area mapping follows Dau's constraints."""
        try:
            # This will raise ValueError if constraints are violated
            self.egi._validate_area_constraints()
        except ValueError as e:
            self.violations.append(ContainmentViolation(
                violation_type="area_mapping_inconsistency",
                element_id="",
                container_id=None,
                message=f"EGI area mapping violation: {e}",
                severity="error"
            ))
    
    def _validate_spatial_containment(self, element_positions: Dict[str, Position], 
                                    cut_bounds: Dict[str, Bounds]):
        """Validate elements are spatially contained within their logical containers."""
        for cut_id, contained_elements in self.egi.area.items():
            if cut_id == self.egi.sheet:
                continue  # Sheet contains everything, skip spatial check
            
            if cut_id not in cut_bounds:
                self.violations.append(ContainmentViolation(
                    violation_type="missing_cut_bounds",
                    element_id=cut_id,
                    container_id=None,
                    message=f"Cut {cut_id} has no spatial bounds",
                    severity="error"
                ))
                continue
            
            cut_boundary = cut_bounds[cut_id]
            
            for element_id in contained_elements:
                if element_id not in element_positions:
                    self.violations.append(ContainmentViolation(
                        violation_type="missing_element_position",
                        element_id=element_id,
                        container_id=cut_id,
                        message=f"Element {element_id} has no spatial position",
                        severity="error"
                    ))
                    continue
                
                element_pos = element_positions[element_id]
                if not self._point_in_bounds(element_pos, cut_boundary):
                    self.violations.append(ContainmentViolation(
                        violation_type="spatial_containment_violation",
                        element_id=element_id,
                        container_id=cut_id,
                        message=f"Element {element_id} at {element_pos} not contained in cut {cut_id} bounds {cut_boundary}",
                        severity="error"
                    ))
    
    def _validate_non_overlapping_elements(self, element_positions: Dict[str, Position]):
        """Validate elements within same area don't overlap."""
        for area_id, elements in self.egi.area.items():
            element_list = list(elements)
            for i, elem1 in enumerate(element_list):
                for elem2 in element_list[i+1:]:
                    if elem1 in element_positions and elem2 in element_positions:
                        pos1 = element_positions[elem1]
                        pos2 = element_positions[elem2]
                        distance = ((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)**0.5
                        
                        # Minimum separation (adjust based on element sizes)
                        min_separation = 20.0  # pixels
                        if distance < min_separation:
                            self.violations.append(ContainmentViolation(
                                violation_type="element_overlap",
                                element_id=elem1,
                                container_id=area_id,
                                message=f"Elements {elem1} and {elem2} too close ({distance:.1f} < {min_separation})",
                                severity="warning"
                            ))
    
    def _validate_nested_cuts(self, cut_bounds: Dict[str, Bounds]):
        """Validate cuts are properly nested, not overlapping."""
        cut_ids = list(cut_bounds.keys())
        
        for i, cut1 in enumerate(cut_ids):
            for cut2 in cut_ids[i+1:]:
                bounds1 = cut_bounds[cut1]
                bounds2 = cut_bounds[cut2]
                
                # Check if cuts overlap but neither contains the other
                if self._bounds_overlap(bounds1, bounds2):
                    if not (self._bounds_contains(bounds1, bounds2) or self._bounds_contains(bounds2, bounds1)):
                        self.violations.append(ContainmentViolation(
                            violation_type="cut_overlap",
                            element_id=cut1,
                            container_id=cut2,
                            message=f"Cuts {cut1} and {cut2} overlap but neither contains the other",
                            severity="error"
                        ))
    
    def _point_in_bounds(self, point: Position, bounds: Bounds) -> bool:
        """Check if point is within bounds."""
        x, y = point
        x1, y1, x2, y2 = bounds
        return x1 <= x <= x2 and y1 <= y <= y2
    
    def _bounds_overlap(self, bounds1: Bounds, bounds2: Bounds) -> bool:
        """Check if two bounds overlap."""
        x1a, y1a, x2a, y2a = bounds1
        x1b, y1b, x2b, y2b = bounds2
        return not (x2a < x1b or x2b < x1a or y2a < y1b or y2b < y1a)
    
    def _bounds_contains(self, outer: Bounds, inner: Bounds) -> bool:
        """Check if outer bounds completely contain inner bounds."""
        x1o, y1o, x2o, y2o = outer
        x1i, y1i, x2i, y2i = inner
        return x1o <= x1i and y1o <= y1i and x2i <= x2o and y2i <= y2o
    
    def get_error_summary(self) -> Dict[str, int]:
        """Get summary of violations by type."""
        summary = {}
        for violation in self.violations:
            violation_type = violation.violation_type
            summary[violation_type] = summary.get(violation_type, 0) + 1
        return summary
    
    def has_errors(self) -> bool:
        """Check if there are any error-level violations."""
        return any(v.severity == "error" for v in self.violations)
    
    def print_violations(self):
        """Print all violations to console."""
        if not self.violations:
            print("✓ No containment hierarchy violations found")
            return
        
        print(f"⚠️  Found {len(self.violations)} containment violations:")
        for violation in self.violations:
            severity_symbol = "❌" if violation.severity == "error" else "⚠️ "
            print(f"{severity_symbol} {violation.violation_type}: {violation.message}")
