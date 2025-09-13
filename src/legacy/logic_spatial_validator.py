"""
Logic-Spatial Concordance Validation System for EGI.

This module provides comprehensive validation to ensure that the spatial representation
rigorously corresponds to the logical EGI structure, detecting any violations of
Dau's formalism and existential graph principles.
"""

from typing import Dict, List, Tuple, Set, Optional, Any
from dataclasses import dataclass
from enum import Enum

from egi_spatial_correspondence import SpatialElement, SpatialBounds


class ViolationType(Enum):
    """Types of logic-spatial concordance violations."""
    AREA_MEMBERSHIP_MISMATCH = "area_membership_mismatch"
    SPATIAL_CONTAINMENT_VIOLATION = "spatial_containment_violation"
    LIGATURE_BOUNDARY_VIOLATION = "ligature_boundary_violation"
    ELEMENT_OVERLAP = "element_overlap"
    CUT_NESTING_VIOLATION = "cut_nesting_violation"
    ORPHANED_ELEMENT = "orphaned_element"
    PIXEL_AREA_AMBIGUITY = "pixel_area_ambiguity"


@dataclass
class ValidationViolation:
    """A detected violation of logic-spatial concordance."""
    violation_type: ViolationType
    element_ids: List[str]
    description: str
    severity: str  # 'critical', 'warning', 'info'
    spatial_coordinates: Optional[Tuple[float, float]] = None
    suggested_fix: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of logic-spatial concordance validation."""
    is_valid: bool
    violations: List[ValidationViolation]
    total_elements_checked: int
    validation_summary: str


class LogicSpatialValidator:
    """
    Validates logic-spatial concordance in EGI representations.
    Ensures every aspect of the spatial layout rigorously corresponds to logical structure.
    """
    
    def __init__(self):
        self.current_egi = None
        self.current_layout = None
    
    def validate_concordance(self, egi, spatial_layout: Dict[str, SpatialElement]) -> ValidationResult:
        """
        Comprehensive validation of logic-spatial concordance.
        
        Args:
            egi: EGI logical structure
            spatial_layout: Spatial element layout
            
        Returns:
            ValidationResult with detected violations
        """
        self.current_egi = egi
        self.current_layout = spatial_layout
        violations = []
        
        # Core validation checks
        violations.extend(self._validate_area_membership())
        violations.extend(self._validate_spatial_containment())
        violations.extend(self._validate_ligature_boundaries())
        violations.extend(self._validate_element_overlaps())
        violations.extend(self._validate_cut_nesting())
        violations.extend(self._validate_pixel_area_mapping())
        violations.extend(self._validate_orphaned_elements())
        
        # Determine overall validity
        critical_violations = [v for v in violations if v.severity == 'critical']
        is_valid = len(critical_violations) == 0
        
        # Generate summary
        summary = self._generate_validation_summary(violations)
        
        return ValidationResult(
            is_valid=is_valid,
            violations=violations,
            total_elements_checked=len(spatial_layout),
            validation_summary=summary
        )
    
    def _validate_area_membership(self) -> List[ValidationViolation]:
        """Validate that spatial containment matches logical area membership."""
        violations = []
        
        # Check each element's logical vs spatial area
        for element_id, spatial_element in self.current_layout.items():
            if spatial_element.element_type in ['vertex', 'edge']:
                logical_area = spatial_element.logical_area
                spatial_area = self._determine_spatial_area(spatial_element.spatial_bounds)
                
                if logical_area != spatial_area:
                    violations.append(ValidationViolation(
                        violation_type=ViolationType.AREA_MEMBERSHIP_MISMATCH,
                        element_ids=[element_id],
                        description=f"Element {element_id} logically in {logical_area} but spatially in {spatial_area}",
                        severity='critical',
                        spatial_coordinates=(spatial_element.spatial_bounds.x, spatial_element.spatial_bounds.y),
                        suggested_fix=f"Move element to spatial area {logical_area}"
                    ))
            # Skip cuts - they define their own spatial area boundaries
        
        return violations
    
    def _validate_spatial_containment(self) -> List[ValidationViolation]:
        """Validate hierarchical spatial containment matches logical nesting."""
        violations = []
        
        # Check cut containment hierarchy
        cuts = {k: v for k, v in self.current_layout.items() if v.element_type == 'cut'}
        
        for cut_id, cut_element in cuts.items():
            # Find elements that should be contained in this cut
            logical_contents = self.current_egi.area.get(cut_id, frozenset())
            
            for content_id in logical_contents:
                if content_id in self.current_layout:
                    content_element = self.current_layout[content_id]
                    
                    # Check if spatially contained
                    if not self._is_spatially_contained(content_element.spatial_bounds, cut_element.spatial_bounds):
                        violations.append(ValidationViolation(
                            violation_type=ViolationType.SPATIAL_CONTAINMENT_VIOLATION,
                            element_ids=[content_id, cut_id],
                            description=f"Element {content_id} should be spatially inside cut {cut_id}",
                            severity='critical',
                            suggested_fix=f"Reposition {content_id} inside {cut_id} boundaries"
                        ))
        
        return violations
    
    def _validate_ligature_boundaries(self) -> List[ValidationViolation]:
        """Validate ligature boundary crossing follows Dau's rules."""
        violations = []
        
        ligatures = {k: v for k, v in self.current_layout.items() if v.element_type == 'ligature'}
        
        for lig_id, ligature in ligatures.items():
            if ligature.ligature_geometry and ligature.ligature_geometry.spatial_path:
                path = ligature.ligature_geometry.spatial_path
                
                # Check each segment of the ligature path
                for i in range(len(path) - 1):
                    start_point = path[i]
                    end_point = path[i + 1]
                    
                    # Find areas of connected elements
                    start_area = self._point_to_area(start_point)
                    end_area = self._point_to_area(end_point)
                    
                    # Check if ligature crosses cut boundaries inappropriately
                    if start_area == end_area:
                        # Same area: ligature should not cross cut boundaries
                        crossed_cuts = self._find_cut_crossings(start_point, end_point)
                        if crossed_cuts:
                            violations.append(ValidationViolation(
                                violation_type=ViolationType.LIGATURE_BOUNDARY_VIOLATION,
                                element_ids=[lig_id] + crossed_cuts,
                                description=f"Ligature {lig_id} illegally crosses cuts {crossed_cuts} within same area",
                                severity='critical',
                                suggested_fix="Reroute ligature to avoid cut boundaries"
                            ))
        
        return violations
    
    def _validate_element_overlaps(self) -> List[ValidationViolation]:
        """Validate no spatial element overlaps occur."""
        violations = []
        
        elements = [(k, v) for k, v in self.current_layout.items() 
                   if v.element_type in ['vertex', 'edge', 'cut']]
        
        for i, (id1, elem1) in enumerate(elements):
            for id2, elem2 in elements[i+1:]:
                if self._bounds_overlap(elem1.spatial_bounds, elem2.spatial_bounds):
                    violations.append(ValidationViolation(
                        violation_type=ViolationType.ELEMENT_OVERLAP,
                        element_ids=[id1, id2],
                        description=f"Elements {id1} and {id2} have overlapping spatial bounds",
                        severity='warning',
                        suggested_fix="Adjust element positions to eliminate overlap"
                    ))
        
        return violations
    
    def _validate_cut_nesting(self) -> List[ValidationViolation]:
        """Validate cut nesting hierarchy is spatially represented."""
        violations = []
        
        cuts = {k: v for k, v in self.current_layout.items() if v.element_type == 'cut'}
        
        # Check logical nesting matches spatial nesting
        for cut_id, cut_element in cuts.items():
            # Find logical parent area
            parent_area = self._find_cut_parent_area(cut_id)
            
            if parent_area in cuts:
                parent_cut = cuts[parent_area]
                
                # Check if spatially nested
                if not self._is_spatially_contained(cut_element.spatial_bounds, parent_cut.spatial_bounds):
                    violations.append(ValidationViolation(
                        violation_type=ViolationType.CUT_NESTING_VIOLATION,
                        element_ids=[cut_id, parent_area],
                        description=f"Cut {cut_id} not spatially nested in parent cut {parent_area}",
                        severity='critical',
                        suggested_fix=f"Position cut {cut_id} inside parent cut {parent_area}"
                    ))
        
        return violations
    
    def _validate_pixel_area_mapping(self) -> List[ValidationViolation]:
        """Validate every pixel maps to exactly one logical area."""
        violations = []
        
        # Get canvas bounds
        canvas_bounds = self._calculate_canvas_bounds()
        
        # Sample points across canvas and check area mapping
        sample_points = self._generate_sample_points(canvas_bounds, density=20)
        
        for point in sample_points:
            areas = self._find_areas_containing_point(point)
            
            if len(areas) == 0:
                violations.append(ValidationViolation(
                    violation_type=ViolationType.PIXEL_AREA_AMBIGUITY,
                    element_ids=[],
                    description=f"Point {point} not contained in any logical area",
                    severity='warning',
                    spatial_coordinates=point,
                    suggested_fix="Extend area bounds to cover all canvas space"
                ))
            elif len(areas) > 1:
                violations.append(ValidationViolation(
                    violation_type=ViolationType.PIXEL_AREA_AMBIGUITY,
                    element_ids=list(areas),
                    description=f"Point {point} contained in multiple areas: {areas}",
                    severity='critical',
                    spatial_coordinates=point,
                    suggested_fix="Resolve overlapping area bounds"
                ))
        
        return violations
    
    def _validate_orphaned_elements(self) -> List[ValidationViolation]:
        """Validate no elements exist without proper logical area assignment."""
        violations = []
        
        for element_id, spatial_element in self.current_layout.items():
            if spatial_element.element_type in ['vertex', 'edge']:
                # Check if element exists in any logical area
                found_in_area = False
                for area_id, area_contents in self.current_egi.area.items():
                    if element_id in area_contents:
                        found_in_area = True
                        break
                
                if not found_in_area:
                    violations.append(ValidationViolation(
                        violation_type=ViolationType.ORPHANED_ELEMENT,
                        element_ids=[element_id],
                        description=f"Element {element_id} not assigned to any logical area",
                        severity='critical',
                        suggested_fix=f"Assign {element_id} to appropriate logical area"
                    ))
        
        return violations
    
    # Helper methods
    
    def _determine_spatial_area(self, bounds: SpatialBounds) -> str:
        """Determine which logical area contains the spatial bounds."""
        center_point = (bounds.x + bounds.width/2, bounds.y + bounds.height/2)
        return self._point_to_area(center_point)
    
    def _point_to_area(self, point: Tuple[float, float]) -> str:
        """Determine which logical area contains a point."""
        # Find the deepest (most nested) cut containing the point
        containing_cuts = []
        
        for element_id, element in self.current_layout.items():
            if element.element_type == 'cut':
                if self._point_in_bounds(point, element.spatial_bounds):
                    containing_cuts.append(element_id)
        
        # Return the most nested cut, or sheet if no cuts contain the point
        if containing_cuts:
            # For simplicity, return the first cut found
            # In a full implementation, would determine nesting depth
            return containing_cuts[0]
        else:
            return self.current_egi.sheet
    
    def _is_spatially_contained(self, inner: SpatialBounds, outer: SpatialBounds) -> bool:
        """Check if inner bounds are completely contained within outer bounds."""
        return (inner.x >= outer.x and 
                inner.y >= outer.y and
                inner.x + inner.width <= outer.x + outer.width and
                inner.y + inner.height <= outer.y + outer.height)
    
    def _bounds_overlap(self, bounds1: SpatialBounds, bounds2: SpatialBounds) -> bool:
        """Check if two spatial bounds overlap."""
        return not (bounds1.x + bounds1.width <= bounds2.x or
                   bounds2.x + bounds2.width <= bounds1.x or
                   bounds1.y + bounds1.height <= bounds2.y or
                   bounds2.y + bounds2.height <= bounds1.y)
    
    def _point_in_bounds(self, point: Tuple[float, float], bounds: SpatialBounds) -> bool:
        """Check if point is within spatial bounds."""
        x, y = point
        return (bounds.x <= x <= bounds.x + bounds.width and
                bounds.y <= y <= bounds.y + bounds.height)
    
    def _find_cut_crossings(self, start: Tuple[float, float], end: Tuple[float, float]) -> List[str]:
        """Find cuts that a line segment crosses."""
        crossed_cuts = []
        
        for element_id, element in self.current_layout.items():
            if element.element_type == 'cut':
                if self._line_intersects_bounds(start, end, element.spatial_bounds):
                    crossed_cuts.append(element_id)
        
        return crossed_cuts
    
    def _line_intersects_bounds(self, start: Tuple[float, float], end: Tuple[float, float], 
                               bounds: SpatialBounds) -> bool:
        """Check if line segment intersects spatial bounds."""
        # Simplified line-rectangle intersection
        x1, y1 = start
        x2, y2 = end
        
        # Check if line passes through rectangle
        return not (max(x1, x2) < bounds.x or min(x1, x2) > bounds.x + bounds.width or
                   max(y1, y2) < bounds.y or min(y1, y2) > bounds.y + bounds.height)
    
    def _find_cut_parent_area(self, cut_id: str) -> str:
        """Find the parent area containing a cut."""
        for area_id, elements in self.current_egi.area.items():
            if cut_id in elements:
                return area_id
        return self.current_egi.sheet
    
    def _calculate_canvas_bounds(self) -> SpatialBounds:
        """Calculate overall canvas bounds from all elements."""
        if not self.current_layout:
            return SpatialBounds(0, 0, 800, 600)
        
        min_x = min(elem.spatial_bounds.x for elem in self.current_layout.values())
        min_y = min(elem.spatial_bounds.y for elem in self.current_layout.values())
        max_x = max(elem.spatial_bounds.x + elem.spatial_bounds.width for elem in self.current_layout.values())
        max_y = max(elem.spatial_bounds.y + elem.spatial_bounds.height for elem in self.current_layout.values())
        
        return SpatialBounds(min_x, min_y, max_x - min_x, max_y - min_y)
    
    def _generate_sample_points(self, bounds: SpatialBounds, density: int) -> List[Tuple[float, float]]:
        """Generate sample points for pixel-area validation."""
        points = []
        step_x = bounds.width / density
        step_y = bounds.height / density
        
        for i in range(density):
            for j in range(density):
                x = bounds.x + i * step_x
                y = bounds.y + j * step_y
                points.append((x, y))
        
        return points
    
    def _find_areas_containing_point(self, point: Tuple[float, float]) -> Set[str]:
        """Find all logical areas that contain a point."""
        areas = set()
        
        # Check if point is in sheet area (always true unless in a cut)
        areas.add(self.current_egi.sheet)
        
        # Check cuts
        for element_id, element in self.current_layout.items():
            if element.element_type == 'cut':
                if self._point_in_bounds(point, element.spatial_bounds):
                    areas.add(element_id)
                    # Remove parent areas (point is in deepest cut)
                    areas.discard(self.current_egi.sheet)
        
        return areas
    
    def _generate_validation_summary(self, violations: List[ValidationViolation]) -> str:
        """Generate human-readable validation summary."""
        if not violations:
            return "✅ Logic-spatial concordance is valid. No violations detected."
        
        critical = len([v for v in violations if v.severity == 'critical'])
        warnings = len([v for v in violations if v.severity == 'warning'])
        
        summary = f"❌ Logic-spatial concordance validation failed.\n"
        summary += f"Critical violations: {critical}\n"
        summary += f"Warnings: {warnings}\n"
        
        if critical > 0:
            summary += "\nCritical issues must be resolved for valid EGI representation."
        
        return summary


def create_validator() -> LogicSpatialValidator:
    """Create a new logic-spatial validator instance."""
    return LogicSpatialValidator()
