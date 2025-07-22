"""
EGRF v3.0 Containment Hierarchy

Manages nesting relationships, validates containment constraints,
and calculates layout from logical structure.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple, Any
from enum import Enum
import json

from .logical_types import (
    LogicalElement, LogicalPredicate, LogicalEntity, LogicalContext,
    ContainmentRelationship, LayoutConstraints, LogicalSize, LogicalBounds,
    SpacingConstraint, PositioningType
)


# ============================================================================
# Hierarchy Validation Types
# ============================================================================

class ValidationResult(Enum):
    """Results of hierarchy validation."""
    VALID = "valid"
    INVALID_NESTING = "invalid_nesting"
    CIRCULAR_REFERENCE = "circular_reference"
    MISSING_CONTAINER = "missing_container"
    ORPHANED_ELEMENT = "orphaned_element"
    CONSTRAINT_VIOLATION = "constraint_violation"


@dataclass
class ValidationError:
    """Details of a validation error."""
    error_type: ValidationResult
    element_id: str
    message: str
    suggested_fix: Optional[str] = None


@dataclass
class HierarchyValidationReport:
    """Complete validation report for a containment hierarchy."""
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    nesting_levels: Dict[str, int] = field(default_factory=dict)
    containment_tree: Dict[str, List[str]] = field(default_factory=dict)


# ============================================================================
# Layout Calculation Types
# ============================================================================

@dataclass
class CalculatedSize:
    """Calculated size for an element."""
    width: float
    height: float
    min_width: float
    min_height: float
    max_width: Optional[float] = None
    max_height: Optional[float] = None
    calculation_method: str = "content_driven"


@dataclass
class CalculatedPosition:
    """Calculated position for an element."""
    x: float
    y: float
    positioning_method: str = "constraint_based"
    container_relative: bool = True


@dataclass
class LayoutCalculationResult:
    """Result of layout calculation for all elements."""
    element_sizes: Dict[str, CalculatedSize] = field(default_factory=dict)
    element_positions: Dict[str, CalculatedPosition] = field(default_factory=dict)
    container_bounds: Dict[str, LogicalBounds] = field(default_factory=dict)
    calculation_order: List[str] = field(default_factory=list)
    total_canvas_size: Optional[LogicalSize] = None


# ============================================================================
# Containment Hierarchy Manager
# ============================================================================

class ContainmentHierarchyManager:
    """Manages containment relationships and validates hierarchy constraints."""
    
    def __init__(self):
        self.elements: Dict[str, LogicalElement] = {}
        self.relationships: Dict[str, ContainmentRelationship] = {}
        self.hierarchy_cache: Optional[Dict[str, Any]] = None
        self._validation_cache: Optional[HierarchyValidationReport] = None
    
    def add_element(self, element: LogicalElement) -> None:
        """Add an element to the hierarchy."""
        self.elements[element.id] = element
        self._invalidate_caches()
    
    def add_relationship(self, relationship: ContainmentRelationship) -> None:
        """Add a containment relationship."""
        self.relationships[relationship.container] = relationship
        self._invalidate_caches()
    
    def remove_element(self, element_id: str) -> None:
        """Remove an element and update relationships."""
        if element_id in self.elements:
            del self.elements[element_id]
        
        # Remove from relationships
        if element_id in self.relationships:
            del self.relationships[element_id]
        
        # Remove from contained elements in other relationships
        for relationship in self.relationships.values():
            if element_id in relationship.contained_elements:
                relationship.contained_elements.remove(element_id)
        
        self._invalidate_caches()
    
    def get_container(self, element_id: str) -> Optional[str]:
        """Get the container of an element."""
        element = self.elements.get(element_id)
        if element:
            return element.layout_constraints.container
        return None
    
    def get_contained_elements(self, container_id: str) -> List[str]:
        """Get all elements contained by a container."""
        relationship = self.relationships.get(container_id)
        if relationship:
            return relationship.contained_elements.copy()
        return []
    
    def get_nesting_level(self, element_id: str) -> int:
        """Get the nesting level of an element."""
        if element_id not in self.elements:
            return -1
        
        level = 0
        current = element_id
        visited = set()
        
        while current and current not in visited:
            visited.add(current)
            container = self.get_container(current)
            if container and container != "viewport" and container in self.elements:
                level += 1
                current = container
            else:
                break
        
        return level
    
    def get_root_elements(self) -> List[str]:
        """Get all root elements (elements with no container or viewport container)."""
        roots = []
        for element_id, element in self.elements.items():
            container = element.layout_constraints.container
            if not container or container == "viewport" or container not in self.elements:
                roots.append(element_id)
        return roots
    
    def get_descendants(self, container_id: str) -> List[str]:
        """Get all descendants of a container (recursive)."""
        descendants = []
        to_visit = [container_id]
        visited = set()
        
        while to_visit:
            current = to_visit.pop(0)
            if current in visited:
                continue
            visited.add(current)
            
            contained = self.get_contained_elements(current)
            descendants.extend(contained)
            to_visit.extend(contained)
        
        return descendants
    
    def get_ancestors(self, element_id: str) -> List[str]:
        """Get all ancestors of an element."""
        ancestors = []
        current = element_id
        visited = set()
        
        while current and current not in visited:
            visited.add(current)
            container = self.get_container(current)
            if container and container in self.elements:
                ancestors.append(container)
                current = container
            else:
                break
        
        return ancestors
    
    def is_ancestor(self, ancestor_id: str, descendant_id: str) -> bool:
        """Check if ancestor_id is an ancestor of descendant_id."""
        return ancestor_id in self.get_ancestors(descendant_id)
    
    def is_sibling(self, element1_id: str, element2_id: str) -> bool:
        """Check if two elements are siblings (same container)."""
        container1 = self.get_container(element1_id)
        container2 = self.get_container(element2_id)
        return container1 == container2 and container1 is not None
    
    def _invalidate_caches(self) -> None:
        """Invalidate cached data when hierarchy changes."""
        self.hierarchy_cache = None
        self._validation_cache = None


# ============================================================================
# Hierarchy Validator
# ============================================================================

class HierarchyValidator:
    """Validates containment hierarchy constraints."""
    
    def __init__(self, manager: ContainmentHierarchyManager):
        self.manager = manager
    
    def validate(self) -> HierarchyValidationReport:
        """Perform complete hierarchy validation."""
        if self.manager._validation_cache:
            return self.manager._validation_cache
        
        report = HierarchyValidationReport(is_valid=True)
        
        # Check for circular references
        self._check_circular_references(report)
        
        # Check for missing containers
        self._check_missing_containers(report)
        
        # Check for orphaned elements
        self._check_orphaned_elements(report)
        
        # Check nesting level consistency
        self._check_nesting_levels(report)
        
        # Check constraint violations
        self._check_constraint_violations(report)
        
        # Build containment tree
        self._build_containment_tree(report)
        
        # Set overall validity
        report.is_valid = len(report.errors) == 0
        
        # Cache the result
        self.manager._validation_cache = report
        
        return report
    
    def _check_circular_references(self, report: HierarchyValidationReport) -> None:
        """Check for circular containment references."""
        for element_id in self.manager.elements:
            visited = set()
            current = element_id
            
            while current:
                if current in visited:
                    # Found circular reference
                    report.errors.append(ValidationError(
                        error_type=ValidationResult.CIRCULAR_REFERENCE,
                        element_id=element_id,
                        message=f"Circular containment reference detected involving {element_id}",
                        suggested_fix="Remove circular reference by changing container relationships"
                    ))
                    break
                
                visited.add(current)
                current = self.manager.get_container(current)
                
                # Stop if we reach a non-existent container
                if current and current not in self.manager.elements:
                    break
    
    def _check_missing_containers(self, report: HierarchyValidationReport) -> None:
        """Check for references to non-existent containers."""
        for element_id, element in self.manager.elements.items():
            container = element.layout_constraints.container
            if container and container != "viewport" and container not in self.manager.elements:
                report.errors.append(ValidationError(
                    error_type=ValidationResult.MISSING_CONTAINER,
                    element_id=element_id,
                    message=f"Element {element_id} references non-existent container {container}",
                    suggested_fix=f"Create container {container} or change container reference"
                ))
    
    def _check_orphaned_elements(self, report: HierarchyValidationReport) -> None:
        """Check for elements not properly contained."""
        # Get all elements that should be contained
        contained_elements = set()
        for relationship in self.manager.relationships.values():
            contained_elements.update(relationship.contained_elements)
        
        # Check for elements with containers but not in any relationship
        for element_id, element in self.manager.elements.items():
            container = element.layout_constraints.container
            if container and container != "viewport" and container in self.manager.elements:
                if element_id not in contained_elements:
                    report.warnings.append(ValidationError(
                        error_type=ValidationResult.ORPHANED_ELEMENT,
                        element_id=element_id,
                        message=f"Element {element_id} has container {container} but is not in containment relationship",
                        suggested_fix=f"Add {element_id} to containment relationship for {container}"
                    ))
    
    def _check_nesting_levels(self, report: HierarchyValidationReport) -> None:
        """Check nesting level consistency."""
        for element_id in self.manager.elements:
            calculated_level = self.manager.get_nesting_level(element_id)
            report.nesting_levels[element_id] = calculated_level
            
            # Check if element's stated nesting level matches calculated
            element = self.manager.elements[element_id]
            if hasattr(element.logical_properties, 'nesting_level'):
                stated_level = element.logical_properties.nesting_level
                if stated_level != calculated_level:
                    report.warnings.append(ValidationError(
                        error_type=ValidationResult.CONSTRAINT_VIOLATION,
                        element_id=element_id,
                        message=f"Element {element_id} stated nesting level {stated_level} doesn't match calculated level {calculated_level}",
                        suggested_fix=f"Update nesting level to {calculated_level}"
                    ))
    
    def _check_constraint_violations(self, report: HierarchyValidationReport) -> None:
        """Check for constraint violations."""
        for element_id, element in self.manager.elements.items():
            # Check if entities are properly connected
            if isinstance(element, LogicalEntity):
                for connection_point in element.connection_points:
                    target = connection_point.connects_to
                    if target not in self.manager.elements:
                        report.errors.append(ValidationError(
                            error_type=ValidationResult.CONSTRAINT_VIOLATION,
                            element_id=element_id,
                            message=f"Entity {element_id} connects to non-existent element {target}",
                            suggested_fix=f"Create element {target} or remove connection"
                        ))
            
            # Check if predicates have valid entity connections
            if isinstance(element, LogicalPredicate):
                for entity_id in element.logical_properties.connected_entities:
                    if entity_id not in self.manager.elements:
                        report.errors.append(ValidationError(
                            error_type=ValidationResult.CONSTRAINT_VIOLATION,
                            element_id=element_id,
                            message=f"Predicate {element_id} connects to non-existent entity {entity_id}",
                            suggested_fix=f"Create entity {entity_id} or remove connection"
                        ))
    
    def _build_containment_tree(self, report: HierarchyValidationReport) -> None:
        """Build the containment tree structure."""
        for container_id in self.manager.relationships:
            contained = self.manager.get_contained_elements(container_id)
            report.containment_tree[container_id] = contained


# ============================================================================
# Layout Calculator
# ============================================================================

class LayoutCalculator:
    """Calculates layout from logical containment hierarchy."""
    
    def __init__(self, manager: ContainmentHierarchyManager):
        self.manager = manager
        self.validator = HierarchyValidator(manager)
    
    def calculate_layout(self, viewport_size: Optional[LogicalSize] = None) -> LayoutCalculationResult:
        """Calculate layout for all elements."""
        # Validate hierarchy first
        validation_report = self.validator.validate()
        if not validation_report.is_valid:
            raise ValueError(f"Cannot calculate layout: hierarchy validation failed with {len(validation_report.errors)} errors")
        
        result = LayoutCalculationResult()
        
        # Calculate sizes from deepest to shallowest (bottom-up)
        self._calculate_sizes(result, validation_report)
        
        # Calculate positions from shallowest to deepest (top-down)
        self._calculate_positions(result, validation_report, viewport_size)
        
        # Calculate container bounds
        self._calculate_container_bounds(result)
        
        return result
    
    def _calculate_sizes(self, result: LayoutCalculationResult, validation_report: HierarchyValidationReport) -> None:
        """Calculate sizes for all elements, deepest first."""
        # Sort elements by nesting level (deepest first)
        elements_by_level = {}
        for element_id, level in validation_report.nesting_levels.items():
            if level not in elements_by_level:
                elements_by_level[level] = []
            elements_by_level[level].append(element_id)
        
        # Process from deepest to shallowest
        for level in sorted(elements_by_level.keys(), reverse=True):
            for element_id in elements_by_level[level]:
                self._calculate_element_size(element_id, result)
                result.calculation_order.append(element_id)
    
    def _calculate_element_size(self, element_id: str, result: LayoutCalculationResult) -> None:
        """Calculate size for a specific element."""
        element = self.manager.elements[element_id]
        
        if isinstance(element, LogicalContext) and element.logical_properties.auto_size:
            # Auto-size context from its contents
            size = self._calculate_context_auto_size(element_id, result)
        elif isinstance(element, LogicalEntity):
            # Entities are sized based on their path
            size = self._calculate_entity_size(element_id, result)
        else:
            # Use specified size constraints
            size = self._calculate_constrained_size(element_id)
        
        result.element_sizes[element_id] = size
    
    def _calculate_context_auto_size(self, context_id: str, result: LayoutCalculationResult) -> CalculatedSize:
        """Calculate auto-size for a context based on its contents."""
        context = self.manager.elements[context_id]
        contained_elements = self.manager.get_contained_elements(context_id)
        
        if not contained_elements:
            # Empty context - use minimum size
            return CalculatedSize(
                width=60.0, height=40.0,
                min_width=60.0, min_height=40.0,
                calculation_method="empty_context"
            )
        
        # Calculate total size needed for contained elements
        total_content_width = 0.0
        max_content_height = 0.0
        
        for contained_id in contained_elements:
            if contained_id in result.element_sizes:
                contained_size = result.element_sizes[contained_id]
                total_content_width += contained_size.width
                max_content_height = max(max_content_height, contained_size.height)
        
        # Add spacing between elements
        if len(contained_elements) > 1:
            total_content_width += (len(contained_elements) - 1) * 20.0  # 20px spacing between elements
        
        # Ensure minimum content size
        content_width = max(total_content_width, 60.0)
        content_height = max(max_content_height, 40.0)
        
        # Add padding
        padding = context.logical_properties.padding.preferred if context.logical_properties.padding else 25.0
        
        total_width = content_width + (padding * 2)
        total_height = content_height + (padding * 2)
        
        return CalculatedSize(
            width=total_width,
            height=total_height,
            min_width=total_width * 0.8,
            min_height=total_height * 0.8,
            max_width=total_width * 1.5,
            max_height=total_height * 1.5,
            calculation_method="content_plus_padding"
        )
    
    def _calculate_entity_size(self, entity_id: str, result: LayoutCalculationResult) -> CalculatedSize:
        """Calculate size for an entity (line of identity)."""
        entity = self.manager.elements[entity_id]
        
        # Entities are lines - their size depends on connection points
        min_length = entity.path_constraints.min_length if entity.path_constraints else 10.0
        
        # Simplified calculation - real path calculation would be more complex
        estimated_length = max(min_length, 30.0)
        line_thickness = 2.0
        
        return CalculatedSize(
            width=estimated_length,
            height=line_thickness,
            min_width=min_length,
            min_height=line_thickness,
            calculation_method="path_based"
        )
    
    def _calculate_constrained_size(self, element_id: str) -> CalculatedSize:
        """Calculate size based on size constraints."""
        element = self.manager.elements[element_id]
        constraints = element.layout_constraints.size_constraints
        
        if not constraints:
            # Default size for elements without constraints
            return CalculatedSize(
                width=60.0, height=30.0,
                min_width=40.0, min_height=20.0,
                max_width=120.0, max_height=60.0,
                calculation_method="default"
            )
        
        # Use preferred size if available, otherwise min size
        if constraints.preferred:
            width = constraints.preferred.width
            height = constraints.preferred.height
        elif constraints.min:
            width = constraints.min.width
            height = constraints.min.height
        else:
            width, height = 60.0, 30.0
        
        min_width = constraints.min.width if constraints.min else width * 0.8
        min_height = constraints.min.height if constraints.min else height * 0.8
        max_width = constraints.max.width if constraints.max else width * 2.0
        max_height = constraints.max.height if constraints.max else height * 2.0
        
        return CalculatedSize(
            width=width, height=height,
            min_width=min_width, min_height=min_height,
            max_width=max_width, max_height=max_height,
            calculation_method="constraint_based"
        )
    
    def _calculate_positions(self, result: LayoutCalculationResult, validation_report: HierarchyValidationReport, viewport_size: Optional[LogicalSize]) -> None:
        """Calculate positions for all elements."""
        # Start with root elements
        root_elements = self.manager.get_root_elements()
        
        # Position root elements in viewport
        viewport_width = viewport_size.width if viewport_size else 800.0
        viewport_height = viewport_size.height if viewport_size else 600.0
        
        current_x, current_y = 20.0, 20.0
        
        for root_id in root_elements:
            if root_id in result.element_sizes:
                root_size = result.element_sizes[root_id]
                
                # Position root element
                result.element_positions[root_id] = CalculatedPosition(
                    x=current_x, y=current_y,
                    positioning_method="viewport_relative",
                    container_relative=False
                )
                
                # Position contained elements recursively
                self._position_contained_elements(root_id, result)
                
                # Move to next position for next root element
                current_x += root_size.width + 40.0
                if current_x > viewport_width - 100:
                    current_x = 20.0
                    current_y += root_size.height + 40.0
    
    def _position_contained_elements(self, container_id: str, result: LayoutCalculationResult) -> None:
        """Position elements contained within a container."""
        contained_elements = self.manager.get_contained_elements(container_id)
        
        if not contained_elements:
            return
        
        container_pos = result.element_positions.get(container_id)
        if not container_pos:
            return
        
        container_size = result.element_sizes.get(container_id)
        if not container_size:
            return
        
        # Get container padding
        container_element = self.manager.elements[container_id]
        if isinstance(container_element, LogicalContext) and container_element.logical_properties.padding:
            padding = container_element.logical_properties.padding.preferred
        else:
            padding = 15.0
        
        # Position contained elements with simple layout
        current_x = container_pos.x + padding
        current_y = container_pos.y + padding
        
        for contained_id in contained_elements:
            if contained_id in result.element_sizes:
                contained_size = result.element_sizes[contained_id]
                
                # Position element
                result.element_positions[contained_id] = CalculatedPosition(
                    x=current_x, y=current_y,
                    positioning_method="container_relative",
                    container_relative=True
                )
                
                # Recursively position its contained elements
                self._position_contained_elements(contained_id, result)
                
                # Move to next position (simple horizontal layout)
                current_x += contained_size.width + 20.0
                
                # Wrap to next line if needed
                container_right = container_pos.x + container_size.width - padding
                if current_x + contained_size.width > container_right:
                    current_x = container_pos.x + padding
                    current_y += contained_size.height + 15.0
    
    def _calculate_container_bounds(self, result: LayoutCalculationResult) -> None:
        """Calculate bounds for all containers."""
        for element_id, element in self.manager.elements.items():
            if isinstance(element, LogicalContext):
                pos = result.element_positions.get(element_id)
                size = result.element_sizes.get(element_id)
                
                if pos and size:
                    result.container_bounds[element_id] = LogicalBounds(
                        x=pos.x, y=pos.y,
                        width=size.width, height=size.height,
                        bounds_type="calculated"
                    )


# ============================================================================
# Movement Validator
# ============================================================================

class MovementValidator:
    """Validates element movement within containment constraints."""
    
    def __init__(self, manager: ContainmentHierarchyManager, calculator: LayoutCalculator):
        self.manager = manager
        self.calculator = calculator
    
    def validate_movement(self, element_id: str, new_x: float, new_y: float, 
                         current_layout: LayoutCalculationResult) -> Tuple[bool, Optional[str]]:
        """Validate if an element can be moved to a new position."""
        element = self.manager.elements.get(element_id)
        if not element:
            return False, f"Element {element_id} not found"
        
        # Check if element is moveable
        if not element.layout_constraints.movement_constraints.moveable:
            return False, f"Element {element_id} is not moveable"
        
        # Get container bounds
        container_id = element.layout_constraints.container
        if container_id and container_id != "viewport":
            container_bounds = current_layout.container_bounds.get(container_id)
            if not container_bounds:
                return False, f"Container {container_id} bounds not found"
            
            # Check if new position is within container
            element_size = current_layout.element_sizes.get(element_id)
            if element_size:
                # Get container padding
                container_element = self.manager.elements.get(container_id)
                padding = 15.0  # Default padding
                if isinstance(container_element, LogicalContext) and container_element.logical_properties.padding:
                    padding = container_element.logical_properties.padding.min
                
                # Check bounds
                min_x = container_bounds.x + padding
                min_y = container_bounds.y + padding
                max_x = container_bounds.x + container_bounds.width - element_size.width - padding
                max_y = container_bounds.y + container_bounds.height - element_size.height - padding
                
                if new_x < min_x or new_x > max_x or new_y < min_y or new_y > max_y:
                    return False, f"Position ({new_x}, {new_y}) is outside container bounds"
        
        # Check collision avoidance
        if element.layout_constraints.collision_avoidance:
            collision_element = self._check_collisions(element_id, new_x, new_y, current_layout)
            if collision_element:
                return False, f"Position would collide with element {collision_element}"
        
        # Check spacing constraints
        spacing_violation = self._check_spacing_constraints(element_id, new_x, new_y, current_layout)
        if spacing_violation:
            return False, spacing_violation
        
        return True, None
    
    def _check_collisions(self, element_id: str, new_x: float, new_y: float, 
                         current_layout: LayoutCalculationResult) -> Optional[str]:
        """Check for collisions with other elements."""
        element_size = current_layout.element_sizes.get(element_id)
        if not element_size:
            return None
        
        element_right = new_x + element_size.width
        element_bottom = new_y + element_size.height
        
        # Check against sibling elements
        container_id = self.manager.get_container(element_id)
        if container_id:
            siblings = self.manager.get_contained_elements(container_id)
            for sibling_id in siblings:
                if sibling_id == element_id:
                    continue
                
                sibling_pos = current_layout.element_positions.get(sibling_id)
                sibling_size = current_layout.element_sizes.get(sibling_id)
                
                if sibling_pos and sibling_size:
                    sibling_right = sibling_pos.x + sibling_size.width
                    sibling_bottom = sibling_pos.y + sibling_size.height
                    
                    # Check for overlap
                    if (new_x < sibling_right and element_right > sibling_pos.x and
                        new_y < sibling_bottom and element_bottom > sibling_pos.y):
                        return sibling_id
        
        return None
    
    def _check_spacing_constraints(self, element_id: str, new_x: float, new_y: float,
                                  current_layout: LayoutCalculationResult) -> Optional[str]:
        """Check spacing constraints."""
        element = self.manager.elements[element_id]
        spacing_constraints = element.layout_constraints.spacing_constraints
        
        if not spacing_constraints:
            return None
        
        element_size = current_layout.element_sizes.get(element_id)
        if not element_size:
            return None
        
        # Check spacing to siblings
        if spacing_constraints.to_siblings:
            min_spacing = spacing_constraints.to_siblings.min
            container_id = self.manager.get_container(element_id)
            
            if container_id:
                siblings = self.manager.get_contained_elements(container_id)
                for sibling_id in siblings:
                    if sibling_id == element_id:
                        continue
                    
                    sibling_pos = current_layout.element_positions.get(sibling_id)
                    sibling_size = current_layout.element_sizes.get(sibling_id)
                    
                    if sibling_pos and sibling_size:
                        # Calculate distance between elements
                        distance = self._calculate_element_distance(
                            new_x, new_y, element_size.width, element_size.height,
                            sibling_pos.x, sibling_pos.y, sibling_size.width, sibling_size.height
                        )
                        
                        if distance < min_spacing:
                            return f"Too close to sibling {sibling_id} (distance: {distance:.1f}, min: {min_spacing})"
        
        return None
    
    def _calculate_element_distance(self, x1: float, y1: float, w1: float, h1: float,
                                   x2: float, y2: float, w2: float, h2: float) -> float:
        """Calculate minimum distance between two rectangular elements."""
        # Calculate center points
        center1_x, center1_y = x1 + w1/2, y1 + h1/2
        center2_x, center2_y = x2 + w2/2, y2 + h2/2
        
        # Calculate edge-to-edge distance
        dx = max(0, abs(center1_x - center2_x) - (w1 + w2)/2)
        dy = max(0, abs(center1_y - center2_y) - (h1 + h2)/2)
        
        return (dx**2 + dy**2)**0.5


# ============================================================================
# Factory Functions
# ============================================================================

def create_containment_hierarchy(elements: List[LogicalElement], 
                                relationships: List[ContainmentRelationship]) -> ContainmentHierarchyManager:
    """Create a containment hierarchy from elements and relationships."""
    manager = ContainmentHierarchyManager()
    
    # Add all elements
    for element in elements:
        manager.add_element(element)
    
    # Add all relationships
    for relationship in relationships:
        manager.add_relationship(relationship)
    
    return manager


def validate_and_calculate_layout(manager: ContainmentHierarchyManager, 
                                 viewport_size: Optional[LogicalSize] = None) -> Tuple[HierarchyValidationReport, LayoutCalculationResult]:
    """Validate hierarchy and calculate layout in one step."""
    validator = HierarchyValidator(manager)
    calculator = LayoutCalculator(manager)
    
    validation_report = validator.validate()
    
    if validation_report.is_valid:
        layout_result = calculator.calculate_layout(viewport_size)
        return validation_report, layout_result
    else:
        # Return empty layout result if validation fails
        return validation_report, LayoutCalculationResult()

