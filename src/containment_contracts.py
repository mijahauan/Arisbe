#!/usr/bin/env python3
"""
API Containment Contracts for Existential Graph Layout Engine

Provides strict API-level validation of containment guarantees to ensure
all layout results comply with Dau's formalism before reaching rendering.
"""

from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from pipeline_contracts import ContractViolationError, enforce_contracts
from egi_core_dau import ElementID, RelationalGraphWithCuts
from layout_engine import LayoutElement, LayoutResult


@dataclass
class ContainmentViolation:
    """Details of a specific containment violation."""
    element_id: ElementID
    element_type: str
    element_name: str
    position: Tuple[float, float]
    expected_area: ElementID
    container_bounds: Tuple[float, float, float, float]
    violation_type: str  # "outside_bounds", "invalid_bounds", "missing_container"


class ContainmentValidator:
    """Validates containment contracts for layout results."""
    
    def __init__(self, tolerance: float = 0.1):
        """Initialize with optional tolerance for floating-point precision."""
        self.tolerance = tolerance
    
    def validate_layout_containment(self, 
                                   layout_result: LayoutResult,
                                   graph: RelationalGraphWithCuts) -> List[ContainmentViolation]:
        """
        Validate that all elements in layout result respect containment boundaries.
        
        Returns list of violations (empty list = perfect containment).
        """
        violations = []
        
        # Build container lookup
        containers = {}
        for element_id, layout_element in layout_result.elements.items():
            if layout_element.element_type == 'cut':
                containers[element_id] = layout_element
        
        # Validate each positioned element
        for element_id, layout_element in layout_result.elements.items():
            if layout_element.element_type in ['vertex', 'edge']:
                violation = self._check_element_containment(
                    element_id, layout_element, containers, graph
                )
                if violation:
                    violations.append(violation)
        
        return violations
    
    def _check_element_containment(self,
                                  element_id: ElementID,
                                  layout_element: LayoutElement,
                                  containers: Dict[ElementID, LayoutElement],
                                  graph: RelationalGraphWithCuts) -> Optional[ContainmentViolation]:
        """Check containment for a single element."""
        
        expected_area = layout_element.parent_area
        element_pos = layout_element.position
        element_name = self._get_element_name(element_id, graph)
        
        # If element should be in sheet area, no containment check needed
        if not expected_area or expected_area.startswith('sheet_'):
            return None
        
        # Find container
        if expected_area not in containers:
            return ContainmentViolation(
                element_id=element_id,
                element_type=layout_element.element_type,
                element_name=element_name,
                position=element_pos,
                expected_area=expected_area,
                container_bounds=(0, 0, 0, 0),
                violation_type="missing_container"
            )
        
        container = containers[expected_area]
        container_bounds = container.bounds
        
        # Check for invalid container bounds
        x1, y1, x2, y2 = container_bounds
        if x2 <= x1 or y2 <= y1:
            return ContainmentViolation(
                element_id=element_id,
                element_type=layout_element.element_type,
                element_name=element_name,
                position=element_pos,
                expected_area=expected_area,
                container_bounds=container_bounds,
                violation_type="invalid_bounds"
            )
        
        # Check if element is within container bounds (with tolerance)
        x, y = element_pos
        if not (x1 - self.tolerance <= x <= x2 + self.tolerance and 
                y1 - self.tolerance <= y <= y2 + self.tolerance):
            return ContainmentViolation(
                element_id=element_id,
                element_type=layout_element.element_type,
                element_name=element_name,
                position=element_pos,
                expected_area=expected_area,
                container_bounds=container_bounds,
                violation_type="outside_bounds"
            )
        
        return None
    
    def _get_element_name(self, element_id: ElementID, graph: RelationalGraphWithCuts) -> str:
        """Get human-readable name for element."""
        if element_id in graph.rel:
            return graph.rel[element_id]
        
        # Try to find vertex label
        for vertex in graph.V:
            if vertex.id == element_id and vertex.label:
                return vertex.label
        
        return f"Element_{element_id[:8]}"


def validate_containment_contract(layout_result: LayoutResult, 
                                graph: RelationalGraphWithCuts) -> bool:
    """
    API contract validator for containment compliance.
    
    Raises ContractViolationError if any containment violations are found.
    Used with @enforce_contracts decorator.
    """
    validator = ContainmentValidator()
    violations = validator.validate_layout_containment(layout_result, graph)
    
    if violations:
        violation_details = []
        for v in violations:
            if v.violation_type == "outside_bounds":
                detail = (f"{v.element_name} at ({v.position[0]:.1f}, {v.position[1]:.1f}) "
                         f"outside container bounds {v.container_bounds}")
            elif v.violation_type == "invalid_bounds":
                detail = f"{v.element_name} assigned to container with invalid bounds {v.container_bounds}"
            else:
                detail = f"{v.element_name} assigned to missing container {v.expected_area}"
            violation_details.append(detail)
        
        raise ContractViolationError(
            f"Containment contract violations found:\n" + "\n".join(violation_details)
        )
    
    return True


def validate_layout_result_contract(layout_result: LayoutResult) -> bool:
    """
    API contract validator for layout result structure.
    
    Validates that LayoutResult has proper structure and valid bounds.
    """
    if not isinstance(layout_result, LayoutResult):
        raise ContractViolationError(f"Expected LayoutResult, got {type(layout_result)}")
    
    if not layout_result.elements:
        raise ContractViolationError("LayoutResult must contain at least one element")
    
    # Validate each element has valid bounds
    for element_id, layout_element in layout_result.elements.items():
        if not isinstance(layout_element, LayoutElement):
            raise ContractViolationError(f"Element {element_id} is not a LayoutElement")
        
        # Check bounds validity for cuts
        if layout_element.element_type == 'cut':
            x1, y1, x2, y2 = layout_element.bounds
            if x2 <= x1 or y2 <= y1:
                raise ContractViolationError(
                    f"Cut {element_id} has invalid bounds: {layout_element.bounds}"
                )
    
    return True


# Decorator for layout engine methods
def enforce_containment_contracts(func):
    """
    Decorator that enforces containment contracts on layout engine methods.
    
    Usage:
    @enforce_containment_contracts
    def layout_graph(self, graph: RelationalGraphWithCuts) -> LayoutResult:
        # ... implementation
        return layout_result
    """
    return enforce_contracts(
        input_contracts={'graph': lambda g: isinstance(g, RelationalGraphWithCuts)},
        output_contract=validate_layout_result_contract
    )(func)


# Contract validation functions for specific scenarios
def validate_practice_mode_containment(layout_result: LayoutResult,
                                     graph: RelationalGraphWithCuts) -> bool:
    """Strict containment validation for Practice mode."""
    validator = ContainmentValidator(tolerance=0.0)  # Zero tolerance for Practice mode
    violations = validator.validate_layout_containment(layout_result, graph)
    
    if violations:
        raise ContractViolationError(
            f"Practice mode requires perfect containment. Found {len(violations)} violations."
        )
    
    return True


def validate_warmup_mode_containment(layout_result: LayoutResult,
                                   graph: RelationalGraphWithCuts) -> bool:
    """Relaxed containment validation for Warmup mode."""
    # In Warmup mode, we only check for structural validity, not strict containment
    return validate_layout_result_contract(layout_result)
