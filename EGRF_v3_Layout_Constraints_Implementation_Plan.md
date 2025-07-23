# EGRF v3.0 Layout Constraints Implementation Plan

## Phase 1: Core Constraint System (Week 1)

### Day 1-2: Base Classes and Core Constraints

#### 1. Base Layout Constraint Class
```python
# src/egrf/v3/layout_constraints.py

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple, ClassVar, Type
import math
import sys
import copy
import json

@dataclass
class LayoutConstraint:
    """Base class for all layout constraints."""
    constraint_id: str
    priority: int = 100  # Higher number = higher priority
    enabled: bool = True
    
    def validate(self, layout_context: 'LayoutContext') -> bool:
        """Validate if this constraint is satisfied in the given context."""
        raise NotImplementedError
    
    def apply(self, layout_context: 'LayoutContext') -> None:
        """Apply this constraint to the layout context."""
        raise NotImplementedError
    
    def to_json(self) -> Dict[str, Any]:
        """Convert constraint to JSON-serializable dictionary."""
        return {
            "constraint_id": self.constraint_id,
            "constraint_type": self.__class__.__name__,
            "priority": self.priority,
            "enabled": self.enabled
        }
    
    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> 'LayoutConstraint':
        """Create constraint from JSON data."""
        constraint_type = data.pop("constraint_type")
        constraint_class = getattr(sys.modules[__name__], constraint_type)
        return constraint_class(**data)
```

#### 2. Layout Element Interface
```python
@dataclass
class LayoutElement:
    """Interface for elements that can be laid out."""
    id: str
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    
    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get element bounds as (x, y, width, height)."""
        return (self.x, self.y, self.width, self.height)
    
    def set_bounds(self, x: float, y: float, width: float, height: float) -> None:
        """Set element bounds."""
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    
    def get_center(self) -> Tuple[float, float]:
        """Get center point of element."""
        return (self.x + self.width / 2, self.y + self.height / 2)
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if element contains point."""
        return (self.x <= x <= self.x + self.width and
                self.y <= y <= self.y + self.height)
    
    def intersects(self, other: 'LayoutElement') -> bool:
        """Check if element intersects with another element."""
        return not (self.x + self.width <= other.x or
                   other.x + other.width <= self.x or
                   self.y + self.height <= other.y or
                   other.y + other.height <= self.y)
```

#### 3. Layout Context
```python
@dataclass
class LayoutContext:
    """Context for layout calculations."""
    elements: Dict[str, LayoutElement]  # Map of element IDs to elements
    containers: Dict[str, str]  # Map of element IDs to container IDs
    viewport: Any  # Viewport information
    constraints: List[LayoutConstraint] = field(default_factory=list)
    
    def get_element(self, element_id: str) -> Optional[LayoutElement]:
        """Get element by ID."""
        return self.elements.get(element_id)
    
    def get_container(self, element_id: str) -> Optional[LayoutElement]:
        """Get container of element."""
        container_id = self.containers.get(element_id)
        if container_id:
            return self.elements.get(container_id)
        return None
    
    def get_constraints_for_element(self, element_id: str) -> List[LayoutConstraint]:
        """Get all constraints affecting an element."""
        return [c for c in self.constraints if hasattr(c, 'element_id') and c.element_id == element_id]
    
    def validate_all_constraints(self) -> Dict[str, bool]:
        """Validate all constraints."""
        results = {}
        for constraint in self.constraints:
            results[constraint.constraint_id] = constraint.validate(self)
        return results
    
    def apply_all_constraints(self) -> None:
        """Apply all constraints."""
        # Sort constraints by priority (higher first)
        sorted_constraints = sorted(self.constraints, key=lambda c: c.priority, reverse=True)
        
        for constraint in sorted_constraints:
            if constraint.enabled:
                constraint.apply(self)
```

#### 4. Size Constraint
```python
@dataclass
class SizeConstraint(LayoutConstraint):
    """Constraint for element size."""
    element_id: str
    min_width: Optional[float] = None
    preferred_width: Optional[float] = None
    max_width: Optional[float] = None
    min_height: Optional[float] = None
    preferred_height: Optional[float] = None
    max_height: Optional[float] = None
    aspect_ratio: Optional[float] = None  # width/height
    maintain_aspect_ratio: bool = False
    
    def validate(self, layout_context: LayoutContext) -> bool:
        """Validate if element size satisfies constraints."""
        element = layout_context.get_element(self.element_id)
        if not element:
            return False
            
        width, height = element.width, element.height
        
        # Check width constraints
        if self.min_width is not None and width < self.min_width:
            return False
        if self.max_width is not None and width > self.max_width:
            return False
            
        # Check height constraints
        if self.min_height is not None and height < self.min_height:
            return False
        if self.max_height is not None and height > self.max_height:
            return False
            
        # Check aspect ratio
        if self.maintain_aspect_ratio and self.aspect_ratio is not None:
            current_ratio = width / height if height != 0 else float('inf')
            if not math.isclose(current_ratio, self.aspect_ratio, rel_tol=0.05):
                return False
                
        return True
    
    def apply(self, layout_context: LayoutContext) -> None:
        """Apply size constraints to element."""
        element = layout_context.get_element(self.element_id)
        if not element:
            return
            
        # Apply width constraints
        if self.preferred_width is not None:
            element.width = self.preferred_width
        elif self.min_width is not None and element.width < self.min_width:
            element.width = self.min_width
        elif self.max_width is not None and element.width > self.max_width:
            element.width = self.max_width
            
        # Apply height constraints
        if self.preferred_height is not None:
            element.height = self.preferred_height
        elif self.min_height is not None and element.height < self.min_height:
            element.height = self.min_height
        elif self.max_height is not None and element.height > self.max_height:
            element.height = self.max_height
            
        # Apply aspect ratio if needed
        if self.maintain_aspect_ratio and self.aspect_ratio is not None:
            current_ratio = element.width / element.height if element.height != 0 else float('inf')
            if not math.isclose(current_ratio, self.aspect_ratio, rel_tol=0.05):
                # Adjust to maintain aspect ratio, preferring to adjust height
                element.height = element.width / self.aspect_ratio
```

#### 5. Position Constraint
```python
@dataclass
class PositionConstraint(LayoutConstraint):
    """Constraint for element position."""
    element_id: str
    reference_id: str  # ID of reference element or "container" or "viewport"
    reference_point: str = "center"  # center, top-left, top-right, bottom-left, bottom-right
    element_point: str = "center"    # center, top-left, top-right, bottom-left, bottom-right
    offset_x: float = 0.0
    offset_y: float = 0.0
    offset_x_percent: Optional[float] = None  # Percentage of reference width
    offset_y_percent: Optional[float] = None  # Percentage of reference height
    
    def validate(self, layout_context: LayoutContext) -> bool:
        """Validate if element position satisfies constraints."""
        element = layout_context.get_element(self.element_id)
        if not element:
            return False
            
        reference = self._get_reference(layout_context)
        if not reference:
            return False
            
        # Calculate expected position
        expected_x, expected_y = self._calculate_expected_position(element, reference)
        
        # Check if current position matches expected position
        current_x, current_y = self._get_element_point_position(element, self.element_point)
        
        return (math.isclose(current_x, expected_x, abs_tol=0.5) and 
                math.isclose(current_y, expected_y, abs_tol=0.5))
    
    def apply(self, layout_context: LayoutContext) -> None:
        """Apply position constraints to element."""
        element = layout_context.get_element(self.element_id)
        if not element:
            return
            
        reference = self._get_reference(layout_context)
        if not reference:
            return
            
        # Calculate expected position
        expected_x, expected_y = self._calculate_expected_position(element, reference)
        
        # Calculate current point position
        current_x, current_y = self._get_element_point_position(element, self.element_point)
        
        # Calculate adjustment needed
        delta_x = expected_x - current_x
        delta_y = expected_y - current_y
        
        # Apply adjustment to element position
        element.x += delta_x
        element.y += delta_y
    
    def _get_reference(self, layout_context: LayoutContext) -> Any:
        """Get reference element or container."""
        if self.reference_id == "container":
            return layout_context.get_container(self.element_id)
        elif self.reference_id == "viewport":
            return layout_context.viewport
        else:
            return layout_context.get_element(self.reference_id)
    
    def _calculate_expected_position(self, element: Any, reference: Any) -> Tuple[float, float]:
        """Calculate expected position based on reference and offsets."""
        ref_x, ref_y = self._get_element_point_position(reference, self.reference_point)
        
        # Calculate offsets
        offset_x = self.offset_x
        offset_y = self.offset_y
        
        # Apply percentage offsets if specified
        if self.offset_x_percent is not None:
            offset_x += reference.width * self.offset_x_percent / 100.0
        if self.offset_y_percent is not None:
            offset_y += reference.height * self.offset_y_percent / 100.0
            
        return ref_x + offset_x, ref_y + offset_y
    
    def _get_element_point_position(self, element: Any, point: str) -> Tuple[float, float]:
        """Get position of specified point on element."""
        if point == "center":
            return element.x + element.width / 2, element.y + element.height / 2
        elif point == "top-left":
            return element.x, element.y
        elif point == "top-right":
            return element.x + element.width, element.y
        elif point == "bottom-left":
            return element.x, element.y + element.height
        elif point == "bottom-right":
            return element.x + element.width, element.y + element.height
        else:
            raise ValueError(f"Unknown point: {point}")
```

### Day 3-4: Additional Constraints and Viewport

#### 6. Spacing Constraint
```python
@dataclass
class SpacingConstraint(LayoutConstraint):
    """Constraint for spacing between elements or to container edges."""
    element_id: str
    reference_id: Optional[str] = None  # ID of reference element or None for container
    edge: str = "all"  # all, left, right, top, bottom
    min_spacing: float = 0.0
    preferred_spacing: Optional[float] = None
    max_spacing: Optional[float] = None
    
    def validate(self, layout_context: LayoutContext) -> bool:
        """Validate if spacing satisfies constraints."""
        element = layout_context.get_element(self.element_id)
        if not element:
            return False
            
        if self.reference_id is None:
            # Spacing to container edges
            container = layout_context.get_container(self.element_id)
            if not container:
                return False
                
            return self._validate_container_spacing(element, container)
        else:
            # Spacing to another element
            reference = layout_context.get_element(self.reference_id)
            if not reference:
                return False
                
            return self._validate_element_spacing(element, reference)
    
    def apply(self, layout_context: LayoutContext) -> None:
        """Apply spacing constraints to element."""
        element = layout_context.get_element(self.element_id)
        if not element:
            return
            
        if self.reference_id is None:
            # Spacing to container edges
            container = layout_context.get_container(self.element_id)
            if not container:
                return
                
            self._apply_container_spacing(element, container)
        else:
            # Spacing to another element
            reference = layout_context.get_element(self.reference_id)
            if not reference:
                return
                
            self._apply_element_spacing(element, reference)
    
    def _validate_container_spacing(self, element: Any, container: Any) -> bool:
        """Validate spacing between element and container edges."""
        if self.edge in ["all", "left"]:
            spacing = element.x - container.x
            if self.min_spacing is not None and spacing < self.min_spacing:
                return False
            if self.max_spacing is not None and spacing > self.max_spacing:
                return False
                
        if self.edge in ["all", "right"]:
            spacing = (container.x + container.width) - (element.x + element.width)
            if self.min_spacing is not None and spacing < self.min_spacing:
                return False
            if self.max_spacing is not None and spacing > self.max_spacing:
                return False
                
        if self.edge in ["all", "top"]:
            spacing = element.y - container.y
            if self.min_spacing is not None and spacing < self.min_spacing:
                return False
            if self.max_spacing is not None and spacing > self.max_spacing:
                return False
                
        if self.edge in ["all", "bottom"]:
            spacing = (container.y + container.height) - (element.y + element.height)
            if self.min_spacing is not None and spacing < self.min_spacing:
                return False
            if self.max_spacing is not None and spacing > self.max_spacing:
                return False
                
        return True
    
    def _validate_element_spacing(self, element: Any, reference: Any) -> bool:
        """Validate spacing between two elements."""
        # Calculate overlap in x and y directions
        x_overlap = max(0, min(element.x + element.width, reference.x + reference.width) - 
                        max(element.x, reference.x))
        y_overlap = max(0, min(element.y + element.height, reference.y + reference.height) - 
                        max(element.y, reference.y))
        
        # If elements overlap in one direction, check spacing in the other
        if x_overlap > 0:
            if self.edge == "top" and element.y > reference.y:
                spacing = element.y - (reference.y + reference.height)
            elif self.edge == "bottom" and element.y < reference.y:
                spacing = reference.y - (element.y + element.height)
            else:
                return True  # Not applicable for this edge
                
            if self.min_spacing is not None and spacing < self.min_spacing:
                return False
            if self.max_spacing is not None and spacing > self.max_spacing:
                return False
                
        if y_overlap > 0:
            if self.edge == "left" and element.x > reference.x:
                spacing = element.x - (reference.x + reference.width)
            elif self.edge == "right" and element.x < reference.x:
                spacing = reference.x - (element.x + element.width)
            else:
                return True  # Not applicable for this edge
                
            if self.min_spacing is not None and spacing < self.min_spacing:
                return False
            if self.max_spacing is not None and spacing > self.max_spacing:
                return False
                
        return True
    
    def _apply_container_spacing(self, element: Any, container: Any) -> None:
        """Apply spacing constraints between element and container edges."""
        if self.edge in ["all", "left"]:
            spacing = element.x - container.x
            if self.preferred_spacing is not None:
                element.x = container.x + self.preferred_spacing
            elif self.min_spacing is not None and spacing < self.min_spacing:
                element.x = container.x + self.min_spacing
                
        if self.edge in ["all", "right"]:
            spacing = (container.x + container.width) - (element.x + element.width)
            if self.preferred_spacing is not None:
                element.x = (container.x + container.width) - element.width - self.preferred_spacing
            elif self.min_spacing is not None and spacing < self.min_spacing:
                element.x = (container.x + container.width) - element.width - self.min_spacing
                
        if self.edge in ["all", "top"]:
            spacing = element.y - container.y
            if self.preferred_spacing is not None:
                element.y = container.y + self.preferred_spacing
            elif self.min_spacing is not None and spacing < self.min_spacing:
                element.y = container.y + self.min_spacing
                
        if self.edge in ["all", "bottom"]:
            spacing = (container.y + container.height) - (element.y + element.height)
            if self.preferred_spacing is not None:
                element.y = (container.y + container.height) - element.height - self.preferred_spacing
            elif self.min_spacing is not None and spacing < self.min_spacing:
                element.y = (container.y + container.height) - element.height - self.min_spacing
    
    def _apply_element_spacing(self, element: Any, reference: Any) -> None:
        """Apply spacing constraints between two elements."""
        # Calculate overlap in x and y directions
        x_overlap = max(0, min(element.x + element.width, reference.x + reference.width) - 
                        max(element.x, reference.x))
        y_overlap = max(0, min(element.y + element.height, reference.y + reference.height) - 
                        max(element.y, reference.y))
        
        # If elements overlap in one direction, adjust spacing in the other
        if x_overlap > 0:
            if self.edge == "top" and element.y > reference.y:
                spacing = element.y - (reference.y + reference.height)
                if self.preferred_spacing is not None:
                    element.y = reference.y + reference.height + self.preferred_spacing
                elif self.min_spacing is not None and spacing < self.min_spacing:
                    element.y = reference.y + reference.height + self.min_spacing
            elif self.edge == "bottom" and element.y < reference.y:
                spacing = reference.y - (element.y + element.height)
                if self.preferred_spacing is not None:
                    element.y = reference.y - element.height - self.preferred_spacing
                elif self.min_spacing is not None and spacing < self.min_spacing:
                    element.y = reference.y - element.height - self.min_spacing
                
        if y_overlap > 0:
            if self.edge == "left" and element.x > reference.x:
                spacing = element.x - (reference.x + reference.width)
                if self.preferred_spacing is not None:
                    element.x = reference.x + reference.width + self.preferred_spacing
                elif self.min_spacing is not None and spacing < self.min_spacing:
                    element.x = reference.x + reference.width + self.min_spacing
            elif self.edge == "right" and element.x < reference.x:
                spacing = reference.x - (element.x + element.width)
                if self.preferred_spacing is not None:
                    element.x = reference.x - element.width - self.preferred_spacing
                elif self.min_spacing is not None and spacing < self.min_spacing:
                    element.x = reference.x - element.width - self.min_spacing
```

#### 7. Alignment Constraint
```python
@dataclass
class AlignmentConstraint(LayoutConstraint):
    """Constraint for aligning elements."""
    element_id: str
    reference_id: str  # ID of reference element or "container"
    alignment: str  # center, left, right, top, bottom, center-horizontal, center-vertical
    offset: float = 0.0
    
    def validate(self, layout_context: LayoutContext) -> bool:
        """Validate if element alignment satisfies constraints."""
        element = layout_context.get_element(self.element_id)
        if not element:
            return False
            
        if self.reference_id == "container":
            reference = layout_context.get_container(self.element_id)
        else:
            reference = layout_context.get_element(self.reference_id)
            
        if not reference:
            return False
            
        # Check alignment
        if self.alignment == "center":
            element_center_x = element.x + element.width / 2
            element_center_y = element.y + element.height / 2
            reference_center_x = reference.x + reference.width / 2
            reference_center_y = reference.y + reference.height / 2
            
            return (math.isclose(element_center_x, reference_center_x + self.offset, abs_tol=0.5) and
                    math.isclose(element_center_y, reference_center_y + self.offset, abs_tol=0.5))
                    
        elif self.alignment == "center-horizontal":
            element_center_x = element.x + element.width / 2
            reference_center_x = reference.x + reference.width / 2
            
            return math.isclose(element_center_x, reference_center_x + self.offset, abs_tol=0.5)
            
        elif self.alignment == "center-vertical":
            element_center_y = element.y + element.height / 2
            reference_center_y = reference.y + reference.height / 2
            
            return math.isclose(element_center_y, reference_center_y + self.offset, abs_tol=0.5)
            
        elif self.alignment == "left":
            return math.isclose(element.x, reference.x + self.offset, abs_tol=0.5)
            
        elif self.alignment == "right":
            return math.isclose(element.x + element.width, 
                               reference.x + reference.width + self.offset, abs_tol=0.5)
                               
        elif self.alignment == "top":
            return math.isclose(element.y, reference.y + self.offset, abs_tol=0.5)
            
        elif self.alignment == "bottom":
            return math.isclose(element.y + element.height, 
                               reference.y + reference.height + self.offset, abs_tol=0.5)
                               
        return False
    
    def apply(self, layout_context: LayoutContext) -> None:
        """Apply alignment constraints to element."""
        element = layout_context.get_element(self.element_id)
        if not element:
            return
            
        if self.reference_id == "container":
            reference = layout_context.get_container(self.element_id)
        else:
            reference = layout_context.get_element(self.reference_id)
            
        if not reference:
            return
            
        # Apply alignment
        if self.alignment == "center":
            reference_center_x = reference.x + reference.width / 2
            reference_center_y = reference.y + reference.height / 2
            
            element.x = reference_center_x - element.width / 2 + self.offset
            element.y = reference_center_y - element.height / 2 + self.offset
            
        elif self.alignment == "center-horizontal":
            reference_center_x = reference.x + reference.width / 2
            element.x = reference_center_x - element.width / 2 + self.offset
            
        elif self.alignment == "center-vertical":
            reference_center_y = reference.y + reference.height / 2
            element.y = reference_center_y - element.height / 2 + self.offset
            
        elif self.alignment == "left":
            element.x = reference.x + self.offset
            
        elif self.alignment == "right":
            element.x = reference.x + reference.width - element.width + self.offset
            
        elif self.alignment == "top":
            element.y = reference.y + self.offset
            
        elif self.alignment == "bottom":
            element.y = reference.y + reference.height - element.height + self.offset
```

#### 8. Viewport
```python
@dataclass
class Viewport(LayoutElement):
    """Represents the viewport for rendering."""
    scale_factor: float = 1.0
    
    def __init__(self, id: str = "viewport", x: float = 0.0, y: float = 0.0, 
                width: float = 800.0, height: float = 600.0, scale_factor: float = 1.0):
        super().__init__(id=id, x=x, y=y, width=width, height=height)
        self.scale_factor = scale_factor
    
    def scale_to_device(self, value: float) -> float:
        """Scale value to device pixels."""
        return value * self.scale_factor
    
    def scale_from_device(self, value: float) -> float:
        """Scale value from device pixels to logical units."""
        return value / self.scale_factor
```

### Day 5: Constraint Solver and Integration

#### 9. Constraint Solver
```python
class ConstraintSolver:
    """Solves layout constraints to find optimal element positions and sizes."""
    
    def __init__(self, max_iterations: int = 100, convergence_threshold: float = 0.5):
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold
        self.previous_positions = {}  # For convergence checking
    
    def solve(self, layout_context: LayoutContext) -> bool:
        """Solve constraints to find optimal layout."""
        # Initial validation
        initial_results = layout_context.validate_all_constraints()
        if all(initial_results.values()):
            return True  # All constraints already satisfied
        
        # Save initial positions for convergence checking
        self._save_positions(layout_context)
        
        # Iterative constraint solving
        for iteration in range(self.max_iterations):
            # Apply all constraints
            layout_context.apply_all_constraints()
            
            # Check if all constraints are satisfied
            results = layout_context.validate_all_constraints()
            if all(results.values()):
                return True
            
            # Check for convergence
            if iteration > 0 and self._check_convergence(layout_context):
                break
            
            # Save positions for next iteration
            self._save_positions(layout_context)
        
        # Final validation
        final_results = layout_context.validate_all_constraints()
        return all(final_results.values())
    
    def _save_positions(self, layout_context: LayoutContext) -> None:
        """Save current positions of all elements."""
        self.previous_positions = {}
        for element_id, element in layout_context.elements.items():
            self.previous_positions[element_id] = (element.x, element.y, element.width, element.height)
    
    def _check_convergence(self, layout_context: LayoutContext) -> bool:
        """Check if layout has converged (changes are below threshold)."""
        if not self.previous_positions:
            return False
            
        for element_id, element in layout_context.elements.items():
            if element_id not in self.previous_positions:
                return False
                
            prev_x, prev_y, prev_width, prev_height = self.previous_positions[element_id]
            
            # Check if position and size have changed significantly
            if (abs(element.x - prev_x) > self.convergence_threshold or
                abs(element.y - prev_y) > self.convergence_threshold or
                abs(element.width - prev_width) > self.convergence_threshold or
                abs(element.height - prev_height) > self.convergence_threshold):
                return False
                
        return True  # No significant changes, converged
```

#### 10. Collision Detector
```python
class CollisionDetector:
    """Detects and resolves collisions between elements."""
    
    def detect_collisions(self, layout_context: LayoutContext) -> List[Tuple[str, str]]:
        """Detect collisions between elements."""
        collisions = []
        elements = layout_context.elements
        
        # Check all pairs of elements
        element_ids = list(elements.keys())
        for i in range(len(element_ids)):
            for j in range(i + 1, len(element_ids)):
                id1, id2 = element_ids[i], element_ids[j]
                
                # Skip if elements are in different containers
                container1 = layout_context.containers.get(id1)
                container2 = layout_context.containers.get(id2)
                if container1 != container2:
                    continue
                
                # Check for collision
                if elements[id1].intersects(elements[id2]):
                    collisions.append((id1, id2))
        
        return collisions
    
    def resolve_collisions(self, layout_context: LayoutContext) -> bool:
        """Resolve collisions between elements."""
        collisions = self.detect_collisions(layout_context)
        if not collisions:
            return True
        
        # Resolve each collision
        for id1, id2 in collisions:
            self._resolve_collision(layout_context, id1, id2)
        
        # Check if all collisions resolved
        remaining_collisions = self.detect_collisions(layout_context)
        return len(remaining_collisions) == 0
    
    def _resolve_collision(self, layout_context: LayoutContext, id1: str, id2: str) -> None:
        """Resolve collision between two elements."""
        element1 = layout_context.elements[id1]
        element2 = layout_context.elements[id2]
        
        # Calculate overlap in each direction
        x_overlap = min(element1.x + element1.width, element2.x + element2.width) - max(element1.x, element2.x)
        y_overlap = min(element1.y + element1.height, element2.y + element2.height) - max(element1.y, element2.y)
        
        # Resolve by moving in direction of smallest overlap
        if x_overlap < y_overlap:
            # Move horizontally
            if element1.x < element2.x:
                element1.x -= x_overlap / 2
                element2.x += x_overlap / 2
            else:
                element1.x += x_overlap / 2
                element2.x -= x_overlap / 2
        else:
            # Move vertically
            if element1.y < element2.y:
                element1.y -= y_overlap / 2
                element2.y += y_overlap / 2
            else:
                element1.y += y_overlap / 2
                element2.y -= y_overlap / 2
```

#### 11. Integration with Logical Types
```python
# src/egrf/v3/logical_types.py

# Add to LogicalPredicate
layout_constraints: Optional[LogicalElementLayoutConstraints] = None
visual_position: Optional[Tuple[float, float]] = None
visual_size: Optional[Tuple[float, float]] = None

# Add to LogicalEntity
layout_constraints: Optional[LogicalElementLayoutConstraints] = None
path_points: List[Tuple[float, float]] = field(default_factory=list)

# Add to LogicalContext
layout_constraints: Optional[LogicalElementLayoutConstraints] = None
visual_position: Optional[Tuple[float, float]] = None
visual_size: Optional[Tuple[float, float]] = None
padding: float = 10.0  # Padding inside context
```

#### 12. Layout Constraints for Logical Elements
```python
@dataclass
class LogicalElementLayoutConstraints:
    """Layout constraints for logical elements."""
    min_width: Optional[float] = None
    preferred_width: Optional[float] = None
    max_width: Optional[float] = None
    min_height: Optional[float] = None
    preferred_height: Optional[float] = None
    max_height: Optional[float] = None
    min_spacing: Optional[float] = None
    preferred_spacing: Optional[float] = None
    aspect_ratio: Optional[float] = None
    maintain_aspect_ratio: bool = False
    
    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "min_width": self.min_width,
            "preferred_width": self.preferred_width,
            "max_width": self.max_width,
            "min_height": self.min_height,
            "preferred_height": self.preferred_height,
            "max_height": self.max_height,
            "min_spacing": self.min_spacing,
            "preferred_spacing": self.preferred_spacing,
            "aspect_ratio": self.aspect_ratio,
            "maintain_aspect_ratio": self.maintain_aspect_ratio
        }
    
    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> 'LogicalElementLayoutConstraints':
        """Create from JSON data."""
        return cls(**data)
```

## Phase 2: Containment Layout Bridge (Week 2)

### Day 1-2: Bridge Implementation

#### 1. Containment Layout Bridge
```python
class ContainmentLayoutBridge:
    """Bridge between containment hierarchy and layout system."""
    
    def create_layout_context_from_hierarchy(self, 
                                            hierarchy_manager: 'ContainmentHierarchyManager',
                                            viewport: Viewport) -> LayoutContext:
        """Create layout context from containment hierarchy."""
        # Create elements dictionary
        elements = {}
        containers = {}
        constraints = []
        
        # Process all elements in hierarchy
        for element_id, element in hierarchy_manager.get_all_elements().items():
            # Create layout element
            layout_element = self._create_layout_element(element)
            elements[element_id] = layout_element
            
            # Record container relationship
            container = hierarchy_manager.get_container(element_id)
            if container:
                containers[element_id] = container.id
            
            # Create constraints for element
            element_constraints = self._create_constraints_for_element(element, hierarchy_manager)
            constraints.extend(element_constraints)
        
        # Create layout context
        return LayoutContext(
            elements=elements,
            containers=containers,
            viewport=viewport,
            constraints=constraints
        )
    
    def apply_layout_to_hierarchy(self, 
                                 layout_context: LayoutContext,
                                 hierarchy_manager: 'ContainmentHierarchyManager') -> None:
        """Apply layout results back to containment hierarchy."""
        for element_id, layout_element in layout_context.elements.items():
            hierarchy_element = hierarchy_manager.get_element(element_id)
            if hierarchy_element:
                # Update element with layout information
                self._update_element_from_layout(hierarchy_element, layout_element)
    
    def _create_layout_element(self, hierarchy_element: Any) -> LayoutElement:
        """Create layout element from hierarchy element."""
        # Get position and size from hierarchy element
        x, y = 0.0, 0.0
        width, height = 50.0, 30.0  # Default size
        
        if hasattr(hierarchy_element, 'visual_position') and hierarchy_element.visual_position:
            x, y = hierarchy_element.visual_position
            
        if hasattr(hierarchy_element, 'visual_size') and hierarchy_element.visual_size:
            width, height = hierarchy_element.visual_size
        
        # Create layout element
        return LayoutElement(
            id=hierarchy_element.id,
            x=x,
            y=y,
            width=width,
            height=height
        )
    
    def _create_constraints_for_element(self, 
                                       element: Any, 
                                       hierarchy_manager: 'ContainmentHierarchyManager') -> List[LayoutConstraint]:
        """Create layout constraints for an element."""
        constraints = []
        
        # Size constraints
        if hasattr(element, 'layout_constraints') and element.layout_constraints:
            size_constraint = SizeConstraint(
                constraint_id=f"size_{element.id}",
                element_id=element.id,
                min_width=element.layout_constraints.min_width,
                preferred_width=element.layout_constraints.preferred_width,
                max_width=element.layout_constraints.max_width,
                min_height=element.layout_constraints.min_height,
                preferred_height=element.layout_constraints.preferred_height,
                max_height=element.layout_constraints.max_height
            )
            constraints.append(size_constraint)
        
        # Container constraints
        container = hierarchy_manager.get_container(element.id)
        if container:
            # Ensure element stays within container
            spacing_constraint = SpacingConstraint(
                constraint_id=f"container_spacing_{element.id}",
                element_id=element.id,
                min_spacing=5.0  # Minimum spacing to container edges
            )
            constraints.append(spacing_constraint)
        
        # Add more constraints based on element type and relationships
        
        return constraints
    
    def _update_element_from_layout(self, hierarchy_element: Any, layout_element: LayoutElement) -> None:
        """Update hierarchy element with layout information."""
        # Update position and size
        if hasattr(hierarchy_element, 'visual_position'):
            hierarchy_element.visual_position = (layout_element.x, layout_element.y)
            
        if hasattr(hierarchy_element, 'visual_size'):
            hierarchy_element.visual_size = (layout_element.width, layout_element.height)
```

### Day 3-4: Layout Manager and Visual Rule Enforcer

#### 2. Visual Rule Enforcer
```python
class VisualRuleEnforcer:
    """Enforces Peirce's visual rules for Existential Graphs."""
    
    def enforce_rules(self, layout_context: LayoutContext) -> bool:
        """Enforce visual rules on layout."""
        # Enforce all rules
        nesting_valid = self._enforce_nesting_rules(layout_context)
        predicate_valid = self._enforce_predicate_rules(layout_context)
        entity_valid = self._enforce_entity_rules(layout_context)
        ligature_valid = self._enforce_ligature_rules(layout_context)
        
        return nesting_valid and predicate_valid and entity_valid and ligature_valid
    
    def _enforce_nesting_rules(self, layout_context: LayoutContext) -> bool:
        """Enforce rules for nested contexts."""
        # Check that nested contexts are fully contained within their parent
        for element_id, container_id in layout_context.containers.items():
            element = layout_context.get_element(element_id)
            container = layout_context.get_element(container_id)
            
            if not element or not container:
                continue
                
            # Check if element is fully contained within container
            if (element.x < container.x or
                element.y < container.y or
                element.x + element.width > container.x + container.width or
                element.y + element.height > container.y + container.height):
                
                # Adjust element to fit within container
                element.x = max(element.x, container.x + 5)  # 5px padding
                element.y = max(element.y, container.y + 5)
                
                max_width = container.x + container.width - element.x - 5
                max_height = container.y + container.height - element.y - 5
                
                element.width = min(element.width, max_width)
                element.height = min(element.height, max_height)
                
        return True
    
    def _enforce_predicate_rules(self, layout_context: LayoutContext) -> bool:
        """Enforce rules for predicates."""
        # Implementation for predicate rules
        return True
    
    def _enforce_entity_rules(self, layout_context: LayoutContext) -> bool:
        """Enforce rules for entities."""
        # Implementation for entity rules
        return True
    
    def _enforce_ligature_rules(self, layout_context: LayoutContext) -> bool:
        """Enforce rules for ligatures."""
        # Implementation for ligature rules
        return True
```

#### 3. Layout Manager
```python
class LayoutManager:
    """Main entry point for layout management."""
    
    def __init__(self):
        self.constraint_solver = ConstraintSolver()
        self.collision_detector = CollisionDetector()
        self.visual_rule_enforcer = VisualRuleEnforcer()
    
    def calculate_layout(self, 
                        hierarchy_manager: 'ContainmentHierarchyManager',
                        viewport: Viewport) -> LayoutContext:
        """Calculate layout for containment hierarchy."""
        # Create layout context from hierarchy
        bridge = ContainmentLayoutBridge()
        layout_context = bridge.create_layout_context_from_hierarchy(hierarchy_manager, viewport)
        
        # Solve constraints
        self.constraint_solver.solve(layout_context)
        
        # Enforce visual rules
        self.visual_rule_enforcer.enforce_rules(layout_context)
        
        # Resolve any remaining collisions
        self.collision_detector.resolve_collisions(layout_context)
        
        # Apply layout back to hierarchy
        bridge.apply_layout_to_hierarchy(layout_context, hierarchy_manager)
        
        return layout_context
    
    def validate_user_interaction(self, 
                                layout_context: LayoutContext, 
                                interaction_type: str, 
                                element_id: str, 
                                **params) -> bool:
        """Validate user interaction with layout."""
        if interaction_type == "move":
            return self._validate_move(layout_context, element_id, params["new_x"], params["new_y"])
        elif interaction_type == "resize":
            return self._validate_resize(layout_context, element_id, params["new_width"], params["new_height"])
        else:
            return False
    
    def _validate_move(self, layout_context: LayoutContext, element_id: str, new_x: float, new_y: float) -> bool:
        """Validate if element can be moved to new position."""
        element = layout_context.get_element(element_id)
        if not element:
            return False
        
        # Save original position
        original_x, original_y = element.x, element.y
        
        # Try moving element
        element.x, element.y = new_x, new_y
        
        # Check if move violates any constraints
        constraints = layout_context.get_constraints_for_element(element_id)
        for constraint in constraints:
            if not constraint.validate(layout_context):
                # Restore original position
                element.x, element.y = original_x, original_y
                return False
        
        # Check for collisions
        collisions = self.collision_detector.detect_collisions(layout_context)
        if any(element_id in collision for collision in collisions):
            # Restore original position
            element.x, element.y = original_x, original_y
            return False
        
        # Move is valid
        return True
    
    def _validate_resize(self, layout_context: LayoutContext, element_id: str, new_width: float, new_height: float) -> bool:
        """Validate if element can be resized."""
        element = layout_context.get_element(element_id)
        if not element:
            return False
        
        # Save original size
        original_width, original_height = element.width, element.height
        
        # Try resizing element
        element.width, element.height = new_width, new_height
        
        # Check if resize violates any constraints
        constraints = layout_context.get_constraints_for_element(element_id)
        for constraint in constraints:
            if not constraint.validate(layout_context):
                # Restore original size
                element.width, element.height = original_width, original_height
                return False
        
        # Check for collisions
        collisions = self.collision_detector.detect_collisions(layout_context)
        if any(element_id in collision for collision in collisions):
            # Restore original size
            element.width, element.height = original_width, original_height
            return False
        
        # Resize is valid
        return True
```

### Day 5: User Interaction Validator and Tests

#### 4. User Interaction Validator
```python
class UserInteractionValidator:
    """Validates user interactions with the layout."""
    
    def validate_move(self, 
                     layout_context: LayoutContext, 
                     element_id: str, 
                     new_x: float, 
                     new_y: float) -> bool:
        """Validate if element can be moved to new position."""
        element = layout_context.get_element(element_id)
        if not element:
            return False
        
        # Save original position
        original_x, original_y = element.x, element.y
        
        # Try moving element
        element.x, element.y = new_x, new_y
        
        # Check if move violates any constraints
        constraints = layout_context.get_constraints_for_element(element_id)
        for constraint in constraints:
            if not constraint.validate(layout_context):
                # Restore original position
                element.x, element.y = original_x, original_y
                return False
        
        # Check for collisions
        collision_detector = CollisionDetector()
        collisions = collision_detector.detect_collisions(layout_context)
        if any(element_id in collision for collision in collisions):
            # Restore original position
            element.x, element.y = original_x, original_y
            return False
        
        # Check containment
        container_id = layout_context.containers.get(element_id)
        if container_id:
            container = layout_context.get_element(container_id)
            if container:
                # Check if element is still fully contained within container
                if (element.x < container.x or
                    element.y < container.y or
                    element.x + element.width > container.x + container.width or
                    element.y + element.height > container.y + container.height):
                    # Restore original position
                    element.x, element.y = original_x, original_y
                    return False
        
        # Move is valid
        return True
    
    def validate_resize(self, 
                       layout_context: LayoutContext, 
                       element_id: str, 
                       new_width: float, 
                       new_height: float) -> bool:
        """Validate if element can be resized."""
        element = layout_context.get_element(element_id)
        if not element:
            return False
        
        # Save original size
        original_width, original_height = element.width, element.height
        
        # Try resizing element
        element.width, element.height = new_width, new_height
        
        # Check if resize violates any constraints
        constraints = layout_context.get_constraints_for_element(element_id)
        for constraint in constraints:
            if not constraint.validate(layout_context):
                # Restore original size
                element.width, element.height = original_width, original_height
                return False
        
        # Check for collisions
        collision_detector = CollisionDetector()
        collisions = collision_detector.detect_collisions(layout_context)
        if any(element_id in collision for collision in collisions):
            # Restore original size
            element.width, element.height = original_width, original_height
            return False
        
        # Check containment
        container_id = layout_context.containers.get(element_id)
        if container_id:
            container = layout_context.get_element(container_id)
            if container:
                # Check if element is still fully contained within container
                if (element.x + new_width > container.x + container.width or
                    element.y + new_height > container.y + container.height):
                    # Restore original size
                    element.width, element.height = original_width, original_height
                    return False
        
        # Resize is valid
        return True
```

#### 5. Unit Tests
```python
# tests/egrf/v3/test_layout_constraints.py

import pytest
import math
from src.egrf.v3.layout_constraints import *

class TestLayoutConstraints:
    """Tests for layout constraints."""
    
    def test_layout_element(self):
        """Test LayoutElement class."""
        element = LayoutElement(id="test", x=10, y=20, width=30, height=40)
        
        # Test getters
        assert element.id == "test"
        assert element.x == 10
        assert element.y == 20
        assert element.width == 30
        assert element.height == 40
        
        # Test bounds
        bounds = element.get_bounds()
        assert bounds == (10, 20, 30, 40)
        
        # Test center
        center = element.get_center()
        assert center == (25, 40)
        
        # Test contains_point
        assert element.contains_point(15, 25) is True
        assert element.contains_point(5, 25) is False
        assert element.contains_point(15, 15) is False
        
        # Test intersects
        other = LayoutElement(id="other", x=20, y=30, width=30, height=40)
        assert element.intersects(other) is True
        
        non_intersecting = LayoutElement(id="non", x=100, y=100, width=10, height=10)
        assert element.intersects(non_intersecting) is False
    
    def test_size_constraint(self):
        """Test SizeConstraint class."""
        # Create element
        element = LayoutElement(id="test", x=0, y=0, width=50, height=30)
        
        # Create constraint
        constraint = SizeConstraint(
            constraint_id="test_size",
            element_id="test",
            min_width=40,
            max_width=60,
            min_height=20,
            max_height=40
        )
        
        # Create context
        context = LayoutContext(
            elements={"test": element},
            containers={},
            viewport=Viewport(id="viewport", width=800, height=600),
            constraints=[constraint]
        )
        
        # Test validation
        assert constraint.validate(context) is True
        
        # Test with invalid size
        element.width = 30  # Below min_width
        assert constraint.validate(context) is False
        
        # Test applying constraint
        constraint.apply(context)
        assert element.width == 40  # Should be adjusted to min_width
        assert constraint.validate(context) is True
    
    def test_position_constraint(self):
        """Test PositionConstraint class."""
        # Create elements
        element1 = LayoutElement(id="element1", x=100, y=100, width=50, height=30)
        element2 = LayoutElement(id="element2", x=200, y=200, width=40, height=20)
        
        # Create constraint
        constraint = PositionConstraint(
            constraint_id="test_position",
            element_id="element1",
            reference_id="element2",
            reference_point="center",
            element_point="center",
            offset_x=-50,
            offset_y=-50
        )
        
        # Create context
        context = LayoutContext(
            elements={"element1": element1, "element2": element2},
            containers={},
            viewport=Viewport(id="viewport", width=800, height=600),
            constraints=[constraint]
        )
        
        # Test validation
        assert constraint.validate(context) is False  # Not at correct position
        
        # Test applying constraint
        constraint.apply(context)
        
        # Calculate expected position
        expected_x = 200 + 40/2 - 50/2 - 50  # element2.x + element2.width/2 - element1.width/2 + offset_x
        expected_y = 200 + 20/2 - 30/2 - 50  # element2.y + element2.height/2 - element1.height/2 + offset_y
        
        assert math.isclose(element1.x, expected_x, abs_tol=0.5)
        assert math.isclose(element1.y, expected_y, abs_tol=0.5)
        assert constraint.validate(context) is True
    
    def test_spacing_constraint(self):
        """Test SpacingConstraint class."""
        # Create elements
        container = LayoutElement(id="container", x=0, y=0, width=200, height=200)
        element = LayoutElement(id="element", x=10, y=10, width=50, height=30)
        
        # Create constraint
        constraint = SpacingConstraint(
            constraint_id="test_spacing",
            element_id="element",
            min_spacing=20.0
        )
        
        # Create context
        context = LayoutContext(
            elements={"container": container, "element": element},
            containers={"element": "container"},
            viewport=Viewport(id="viewport", width=800, height=600),
            constraints=[constraint]
        )
        
        # Test validation
        assert constraint.validate(context) is False  # Spacing is less than min_spacing
        
        # Test applying constraint
        constraint.apply(context)
        
        # Check that element has been moved to satisfy constraint
        assert element.x >= container.x + 20.0
        assert element.y >= container.y + 20.0
        assert constraint.validate(context) is True
    
    def test_alignment_constraint(self):
        """Test AlignmentConstraint class."""
        # Create elements
        container = LayoutElement(id="container", x=0, y=0, width=200, height=200)
        element = LayoutElement(id="element", x=10, y=10, width=50, height=30)
        
        # Create constraint
        constraint = AlignmentConstraint(
            constraint_id="test_alignment",
            element_id="element",
            reference_id="container",
            alignment="center"
        )
        
        # Create context
        context = LayoutContext(
            elements={"container": container, "element": element},
            containers={"element": "container"},
            viewport=Viewport(id="viewport", width=800, height=600),
            constraints=[constraint]
        )
        
        # Test validation
        assert constraint.validate(context) is False  # Not centered
        
        # Test applying constraint
        constraint.apply(context)
        
        # Check that element has been centered
        assert math.isclose(element.x + element.width/2, container.x + container.width/2, abs_tol=0.5)
        assert math.isclose(element.y + element.height/2, container.y + container.height/2, abs_tol=0.5)
        assert constraint.validate(context) is True
    
    def test_constraint_solver(self):
        """Test ConstraintSolver class."""
        # Create elements
        container = LayoutElement(id="container", x=0, y=0, width=200, height=200)
        element1 = LayoutElement(id="element1", x=10, y=10, width=50, height=30)
        element2 = LayoutElement(id="element2", x=10, y=50, width=50, height=30)
        
        # Create constraints
        constraints = [
            SpacingConstraint(
                constraint_id="spacing1",
                element_id="element1",
                min_spacing=20.0
            ),
            SpacingConstraint(
                constraint_id="spacing2",
                element_id="element2",
                min_spacing=20.0
            ),
            AlignmentConstraint(
                constraint_id="alignment1",
                element_id="element1",
                reference_id="container",
                alignment="center-horizontal"
            ),
            AlignmentConstraint(
                constraint_id="alignment2",
                element_id="element2",
                reference_id="container",
                alignment="center-horizontal"
            )
        ]
        
        # Create context
        context = LayoutContext(
            elements={"container": container, "element1": element1, "element2": element2},
            containers={"element1": "container", "element2": "container"},
            viewport=Viewport(id="viewport", width=800, height=600),
            constraints=constraints
        )
        
        # Solve constraints
        solver = ConstraintSolver()
        result = solver.solve(context)
        
        # Check that all constraints are satisfied
        assert result is True
        
        # Check specific results
        assert element1.x >= container.x + 20.0
        assert element2.x >= container.x + 20.0
        assert math.isclose(element1.x + element1.width/2, container.x + container.width/2, abs_tol=0.5)
        assert math.isclose(element2.x + element2.width/2, container.x + container.width/2, abs_tol=0.5)
```

## Phase 3: Integration and Testing (Week 3)

### Day 1-2: Integration with Containment Hierarchy

#### 1. Containment Layout Bridge Integration
```python
# Integration with ContainmentHierarchyManager

def test_containment_layout_bridge():
    """Test integration with containment hierarchy."""
    # Create hierarchy manager
    from src.egrf.v3.containment_hierarchy import ContainmentHierarchyManager
    from src.egrf.v3.logical_types import (
        create_logical_context, create_logical_predicate, create_logical_entity
    )
    
    hierarchy_manager = ContainmentHierarchyManager()
    
    # Add elements to hierarchy
    context = create_logical_context(id="context", nesting_level=0)
    predicate1 = create_logical_predicate(id="predicate1", name="Person")
    predicate2 = create_logical_predicate(id="predicate2", name="Mortal")
    entity = create_logical_entity(id="entity", name="Socrates")
    
    hierarchy_manager.add_element(context)
    hierarchy_manager.add_element(predicate1)
    hierarchy_manager.add_element(predicate2)
    hierarchy_manager.add_element(entity)
    
    hierarchy_manager.set_container(predicate1, context)
    hierarchy_manager.set_container(predicate2, context)
    hierarchy_manager.set_container(entity, context)
    
    # Create layout manager
    layout_manager = LayoutManager()
    
    # Calculate layout
    layout_context = layout_manager.calculate_layout(
        hierarchy_manager, 
        Viewport(id="viewport", width=800, height=600)
    )
    
    # Verify layout
    assert "context" in layout_context.elements
    assert "predicate1" in layout_context.elements
    assert "predicate2" in layout_context.elements
    assert "entity" in layout_context.elements
    
    # Check containment
    assert layout_context.containers["predicate1"] == "context"
    assert layout_context.containers["predicate2"] == "context"
    assert layout_context.containers["entity"] == "context"
    
    # Check positions
    context_elem = layout_context.elements["context"]
    predicate1_elem = layout_context.elements["predicate1"]
    predicate2_elem = layout_context.elements["predicate2"]
    entity_elem = layout_context.elements["entity"]
    
    # Predicates should be inside context
    assert predicate1_elem.x >= context_elem.x
    assert predicate1_elem.y >= context_elem.y
    assert predicate1_elem.x + predicate1_elem.width <= context_elem.x + context_elem.width
    assert predicate1_elem.y + predicate1_elem.height <= context_elem.y + context_elem.height
    
    assert predicate2_elem.x >= context_elem.x
    assert predicate2_elem.y >= context_elem.y
    assert predicate2_elem.x + predicate2_elem.width <= context_elem.x + context_elem.width
    assert predicate2_elem.y + predicate2_elem.height <= context_elem.y + context_elem.height
    
    # Entity should be inside context
    assert entity_elem.x >= context_elem.x
    assert entity_elem.y >= context_elem.y
    assert entity_elem.x + entity_elem.width <= context_elem.x + context_elem.width
    assert entity_elem.y + entity_elem.height <= context_elem.y + context_elem.height
    
    # No collisions
    collision_detector = CollisionDetector()
    collisions = collision_detector.detect_collisions(layout_context)
    assert len(collisions) == 0
```

### Day 3-4: Corpus-Based Testing

#### 2. Corpus-Based Tests
```python
def test_corpus_layout():
    """Test layout with corpus examples."""
    # Load corpus example
    from src.egrf.v3.corpus_loader import load_corpus_example
    from src.egrf.v3.eg_hg_converter import convert_eg_hg_to_hierarchy
    
    corpus_example = load_corpus_example("peirce_cp_4_394_man_mortal")
    eg_hg = corpus_example.load_eg_hg()
    
    # Convert to containment hierarchy
    hierarchy_manager = convert_eg_hg_to_hierarchy(eg_hg)
    
    # Create layout manager
    layout_manager = LayoutManager()
    
    # Calculate layout
    layout_context = layout_manager.calculate_layout(
        hierarchy_manager, 
        Viewport(id="viewport", width=800, height=600)
    )
    
    # Verify layout follows Peirce's conventions
    visual_rule_enforcer = VisualRuleEnforcer()
    assert visual_rule_enforcer.enforce_rules(layout_context) is True
    
    # Verify no collisions
    collision_detector = CollisionDetector()
    collisions = collision_detector.detect_collisions(layout_context)
    assert len(collisions) == 0
    
    # Verify double-cut structure
    # Outer cut should contain inner cut
    outer_cut = layout_context.elements["cut-outer"]
    inner_cut = layout_context.elements["cut-inner"]
    
    assert inner_cut.x >= outer_cut.x
    assert inner_cut.y >= outer_cut.y
    assert inner_cut.x + inner_cut.width <= outer_cut.x + outer_cut.width
    assert inner_cut.y + inner_cut.height <= outer_cut.y + outer_cut.height
    
    # Verify predicates are in correct cuts
    man_predicate = layout_context.elements["predicate-man"]
    mortal_predicate = layout_context.elements["predicate-mortal"]
    
    assert man_predicate.x >= outer_cut.x
    assert man_predicate.y >= outer_cut.y
    assert man_predicate.x + man_predicate.width <= outer_cut.x + outer_cut.width
    assert man_predicate.y + man_predicate.height <= outer_cut.y + outer_cut.height
    
    assert mortal_predicate.x >= inner_cut.x
    assert mortal_predicate.y >= inner_cut.y
    assert mortal_predicate.x + mortal_predicate.width <= inner_cut.x + inner_cut.width
    assert mortal_predicate.y + mortal_predicate.height <= inner_cut.y + inner_cut.height
```

### Day 5: Documentation and Demo

#### 3. Layout Constraints Demo
```python
# layout_constraints_demo.py

from src.egrf.v3.layout_constraints import *
from src.egrf.v3.containment_hierarchy import ContainmentHierarchyManager
from src.egrf.v3.logical_types import (
    create_logical_context, create_logical_predicate, create_logical_entity
)

def main():
    """Demonstrate layout constraints system."""
    # Create hierarchy manager
    hierarchy_manager = ContainmentHierarchyManager()
    
    # Create elements
    sheet = create_logical_context(id="sheet", nesting_level=0)
    outer_cut = create_logical_context(id="outer_cut", nesting_level=1)
    inner_cut = create_logical_context(id="inner_cut", nesting_level=2)
    
    man_predicate = create_logical_predicate(id="man_predicate", name="Man")
    mortal_predicate = create_logical_predicate(id="mortal_predicate", name="Mortal")
    
    entity1 = create_logical_entity(id="entity1", name="x")
    entity2 = create_logical_entity(id="entity2", name="x")
    
    # Add elements to hierarchy
    hierarchy_manager.add_element(sheet)
    hierarchy_manager.add_element(outer_cut)
    hierarchy_manager.add_element(inner_cut)
    hierarchy_manager.add_element(man_predicate)
    hierarchy_manager.add_element(mortal_predicate)
    hierarchy_manager.add_element(entity1)
    hierarchy_manager.add_element(entity2)
    
    # Set containment relationships
    hierarchy_manager.set_container(outer_cut, sheet)
    hierarchy_manager.set_container(inner_cut, outer_cut)
    hierarchy_manager.set_container(man_predicate, outer_cut)
    hierarchy_manager.set_container(mortal_predicate, inner_cut)
    hierarchy_manager.set_container(entity1, outer_cut)
    hierarchy_manager.set_container(entity2, inner_cut)
    
    # Set layout constraints
    sheet.layout_constraints = LogicalElementLayoutConstraints(
        min_width=400,
        min_height=300,
        preferred_width=600,
        preferred_height=400
    )
    
    outer_cut.layout_constraints = LogicalElementLayoutConstraints(
        min_width=300,
        min_height=200,
        preferred_width=400,
        preferred_height=300
    )
    
    inner_cut.layout_constraints = LogicalElementLayoutConstraints(
        min_width=200,
        min_height=100,
        preferred_width=250,
        preferred_height=150
    )
    
    man_predicate.layout_constraints = LogicalElementLayoutConstraints(
        min_width=80,
        min_height=30,
        preferred_width=100,
        preferred_height=40
    )
    
    mortal_predicate.layout_constraints = LogicalElementLayoutConstraints(
        min_width=80,
        min_height=30,
        preferred_width=100,
        preferred_height=40
    )
    
    # Create layout manager
    layout_manager = LayoutManager()
    
    # Calculate layout
    viewport = Viewport(id="viewport", width=800, height=600)
    layout_context = layout_manager.calculate_layout(hierarchy_manager, viewport)
    
    # Print layout results
    print("Layout Results:")
    for element_id, element in layout_context.elements.items():
        print(f"{element_id}: x={element.x}, y={element.y}, width={element.width}, height={element.height}")
    
    # Validate user interaction
    print("\nUser Interaction Validation:")
    
    # Try moving man_predicate outside its container
    valid_move = layout_manager.validate_user_interaction(
        layout_context,
        "move",
        "man_predicate",
        new_x=10,
        new_y=10
    )
    print(f"Move man_predicate outside container: {'Valid' if valid_move else 'Invalid'}")
    
    # Try moving man_predicate within its container
    outer_cut_elem = layout_context.elements["outer_cut"]
    valid_move = layout_manager.validate_user_interaction(
        layout_context,
        "move",
        "man_predicate",
        new_x=outer_cut_elem.x + 20,
        new_y=outer_cut_elem.y + 20
    )
    print(f"Move man_predicate within container: {'Valid' if valid_move else 'Invalid'}")
    
    # Try resizing inner_cut too large
    valid_resize = layout_manager.validate_user_interaction(
        layout_context,
        "resize",
        "inner_cut",
        new_width=500,
        new_height=400
    )
    print(f"Resize inner_cut too large: {'Valid' if valid_resize else 'Invalid'}")
    
    # Try resizing inner_cut within constraints
    valid_resize = layout_manager.validate_user_interaction(
        layout_context,
        "resize",
        "inner_cut",
        new_width=220,
        new_height=120
    )
    print(f"Resize inner_cut within constraints: {'Valid' if valid_resize else 'Invalid'}")

if __name__ == "__main__":
    main()
```

## Conclusion

This implementation plan provides a detailed roadmap for implementing the layout constraints system for EGRF v3.0. The system is designed to provide platform-independent layout rules that enforce Peirce's visual conventions while allowing flexibility for different GUI frameworks.

The implementation is divided into three phases:

1. **Core Constraint System**: Implementing the base constraint classes and layout context
2. **Containment Layout Bridge**: Integrating with the containment hierarchy system
3. **Integration and Testing**: Testing with corpus examples and creating demos

By following this plan, we will create a robust layout constraints system that completes the EGRF v3.0 architecture by adding the layout layer on top of the logical types and containment hierarchy.

