"""
EGRF v3.0 Layout Constraints System.

This module provides a platform-independent layout system for Existential Graph Rendering Format (EGRF).
It implements constraint-based positioning that enforces Peirce's logical containment rules while
giving users freedom to move elements within their logical containers.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union, Any
import json
import math


class LayoutElement:
    """Base class for all visual elements in the layout."""
    
    def __init__(self, id: str, x: float = 0, y: float = 0, 
                 width: float = 0, height: float = 0):
        """Initialize a layout element.
        
        Args:
            id: Unique identifier for the element.
            x: X-coordinate of the element's top-left corner.
            y: Y-coordinate of the element's top-left corner.
            width: Width of the element.
            height: Height of the element.
        """
        self.id = id
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    
    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get the bounds of the element.
        
        Returns:
            Tuple of (x, y, width, height).
        """
        return (self.x, self.y, self.width, self.height)
    
    def get_center(self) -> Tuple[float, float]:
        """Get the center point of the element.
        
        Returns:
            Tuple of (center_x, center_y).
        """
        return (self.x + self.width / 2, self.y + self.height / 2)
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if the element contains a point.
        
        Args:
            x: X-coordinate of the point.
            y: Y-coordinate of the point.
            
        Returns:
            True if the element contains the point, False otherwise.
        """
        return (self.x <= x <= self.x + self.width and
                self.y <= y <= self.y + self.height)
    
    def intersects(self, other: 'LayoutElement') -> bool:
        """Check if the element intersects with another element.
        
        Args:
            other: Another layout element.
            
        Returns:
            True if the elements intersect, False otherwise.
        """
        return not (self.x + self.width <= other.x or
                    other.x + other.width <= self.x or
                    self.y + self.height <= other.y or
                    other.y + other.height <= self.y)
    
    def contains_element(self, other: 'LayoutElement') -> bool:
        """Check if the element contains another element.
        
        Args:
            other: Another layout element.
            
        Returns:
            True if the element contains the other element, False otherwise.
        """
        return (self.x <= other.x and
                self.y <= other.y and
                self.x + self.width >= other.x + other.width and
                self.y + self.height >= other.y + other.height)
    
    def to_json(self) -> Dict[str, Any]:
        """Convert the element to a JSON-serializable dictionary.
        
        Returns:
            Dictionary representation of the element.
        """
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height
        }
    
    @classmethod
    def from_json(cls, json_data: Dict[str, Any]) -> 'LayoutElement':
        """Create an element from a JSON-serializable dictionary.
        
        Args:
            json_data: Dictionary representation of the element.
            
        Returns:
            New layout element.
        """
        return cls(
            id=json_data["id"],
            x=json_data.get("x", 0),
            y=json_data.get("y", 0),
            width=json_data.get("width", 0),
            height=json_data.get("height", 0)
        )


class Viewport(LayoutElement):
    """Container for the entire diagram."""
    
    def __init__(self, id: str, width: float = 800, height: float = 600, 
                 scale_factor: float = 1.0):
        """Initialize a viewport.
        
        Args:
            id: Unique identifier for the viewport.
            width: Width of the viewport.
            height: Height of the viewport.
            scale_factor: Scale factor for device pixels.
        """
        super().__init__(id=id, x=0, y=0, width=width, height=height)
        self.scale_factor = scale_factor
    
    def scale_to_device(self, value: float) -> float:
        """Scale a logical value to device pixels.
        
        Args:
            value: Logical value.
            
        Returns:
            Device pixel value.
        """
        return value * self.scale_factor
    
    def scale_from_device(self, value: float) -> float:
        """Scale a device pixel value to logical units.
        
        Args:
            value: Device pixel value.
            
        Returns:
            Logical value.
        """
        return value / self.scale_factor
    
    def to_json(self) -> Dict[str, Any]:
        """Convert the viewport to a JSON-serializable dictionary.
        
        Returns:
            Dictionary representation of the viewport.
        """
        json_data = super().to_json()
        json_data["scale_factor"] = self.scale_factor
        return json_data
    
    @classmethod
    def from_json(cls, json_data: Dict[str, Any]) -> 'Viewport':
        """Create a viewport from a JSON-serializable dictionary.
        
        Args:
            json_data: Dictionary representation of the viewport.
            
        Returns:
            New viewport.
        """
        return cls(
            id=json_data["id"],
            width=json_data.get("width", 800),
            height=json_data.get("height", 600),
            scale_factor=json_data.get("scale_factor", 1.0)
        )


class LayoutContext:
    """Manages relationships between elements."""
    
    def __init__(self, elements: Dict[str, LayoutElement], 
                 containers: Dict[str, str], 
                 viewport: Viewport):
        """Initialize a layout context.
        
        Args:
            elements: Dictionary of elements by ID.
            containers: Dictionary mapping element IDs to container IDs.
            viewport: Viewport for the layout.
        """
        self.elements = elements
        self.containers = containers
        self.viewport = viewport
        self.constraints = []
    
    def get_element(self, element_id: str) -> Optional[LayoutElement]:
        """Get an element by ID.
        
        Args:
            element_id: ID of the element.
            
        Returns:
            Layout element, or None if not found.
        """
        return self.elements.get(element_id)
    
    def get_container(self, element_id: str) -> Optional[LayoutElement]:
        """Get the container of an element.
        
        Args:
            element_id: ID of the element.
            
        Returns:
            Container element, or None if not found.
        """
        container_id = self.containers.get(element_id)
        if container_id:
            return self.elements.get(container_id)
        return None
    
    def get_contained_elements(self, container_id: str) -> List[LayoutElement]:
        """Get elements contained in a container.
        
        Args:
            container_id: ID of the container.
            
        Returns:
            List of contained elements.
        """
        contained = []
        for element_id, container in self.containers.items():
            if container == container_id:
                element = self.elements.get(element_id)
                if element:
                    contained.append(element)
        return contained
    
    def to_json(self) -> Dict[str, Any]:
        """Convert the context to a JSON-serializable dictionary.
        
        Returns:
            Dictionary representation of the context.
        """
        elements_json = {}
        for element_id, element in self.elements.items():
            elements_json[element_id] = element.to_json()
        
        constraints_json = []
        for constraint in self.constraints:
            constraints_json.append(constraint.to_json())
        
        return {
            "elements": elements_json,
            "containers": self.containers,
            "viewport": self.viewport.to_json(),
            "constraints": constraints_json
        }
    
    @classmethod
    def from_json(cls, json_data: Dict[str, Any]) -> 'LayoutContext':
        """Create a context from a JSON-serializable dictionary.
        
        Args:
            json_data: Dictionary representation of the context.
            
        Returns:
            New layout context.
        """
        elements = {}
        for element_id, element_data in json_data["elements"].items():
            if element_id == "viewport":
                elements[element_id] = Viewport.from_json(element_data)
            else:
                elements[element_id] = LayoutElement.from_json(element_data)
        
        viewport = Viewport.from_json(json_data["viewport"])
        
        context = cls(
            elements=elements,
            containers=json_data["containers"],
            viewport=viewport
        )
        
        # Add constraints if present
        if "constraints" in json_data:
            for constraint_data in json_data["constraints"]:
                constraint_type = constraint_data.get("type")
                if constraint_type == "SizeConstraint":
                    constraint = SizeConstraint.from_json(constraint_data)
                elif constraint_type == "PositionConstraint":
                    constraint = PositionConstraint.from_json(constraint_data)
                elif constraint_type == "SpacingConstraint":
                    constraint = SpacingConstraint.from_json(constraint_data)
                elif constraint_type == "AlignmentConstraint":
                    constraint = AlignmentConstraint.from_json(constraint_data)
                elif constraint_type == "ContainmentConstraint":
                    constraint = ContainmentConstraint.from_json(constraint_data)
                else:
                    continue
                
                context.constraints.append(constraint)
        
        return context


class LayoutConstraint:
    """Base class for all layout constraints."""
    
    def __init__(self, constraint_id: str, element_id: str, priority: int = 100):
        """Initialize a layout constraint.
        
        Args:
            constraint_id: Unique identifier for the constraint.
            element_id: ID of the element to constrain.
            priority: Priority of the constraint (higher values take precedence).
        """
        self.constraint_id = constraint_id
        self.element_id = element_id
        self.priority = priority
    
    def validate(self, context: LayoutContext) -> bool:
        """Validate if the constraint is satisfied.
        
        Args:
            context: Layout context.
            
        Returns:
            True if the constraint is satisfied, False otherwise.
        """
        raise NotImplementedError("Subclasses must implement validate()")
    
    def apply(self, context: LayoutContext) -> None:
        """Apply the constraint to the layout.
        
        Args:
            context: Layout context.
        """
        raise NotImplementedError("Subclasses must implement apply()")
    
    def to_json(self) -> Dict[str, Any]:
        """Convert the constraint to a JSON-serializable dictionary.
        
        Returns:
            Dictionary representation of the constraint.
        """
        return {
            "constraint_id": self.constraint_id,
            "element_id": self.element_id,
            "priority": self.priority,
            "type": self.__class__.__name__
        }
    
    @classmethod
    def from_json(cls, json_data: Dict[str, Any]) -> 'LayoutConstraint':
        """Create a constraint from a JSON-serializable dictionary.
        
        Args:
            json_data: Dictionary representation of the constraint.
            
        Returns:
            New layout constraint.
        """
        return cls(
            constraint_id=json_data["constraint_id"],
            element_id=json_data["element_id"],
            priority=json_data.get("priority", 100)
        )


class SizeConstraint(LayoutConstraint):
    """Controls element dimensions."""
    
    def __init__(self, constraint_id: str, element_id: str, 
                 min_width: float = 0, min_height: float = 0,
                 max_width: float = float('inf'), max_height: float = float('inf'),
                 preferred_width: Optional[float] = None, 
                 preferred_height: Optional[float] = None,
                 aspect_ratio: Optional[float] = None,
                 maintain_aspect_ratio: bool = False,
                 priority: int = 100):
        """Initialize a size constraint.
        
        Args:
            constraint_id: Unique identifier for the constraint.
            element_id: ID of the element to constrain.
            min_width: Minimum width of the element.
            min_height: Minimum height of the element.
            max_width: Maximum width of the element.
            max_height: Maximum height of the element.
            preferred_width: Preferred width of the element.
            preferred_height: Preferred height of the element.
            aspect_ratio: Aspect ratio (width/height) to maintain.
            maintain_aspect_ratio: Whether to maintain the aspect ratio.
            priority: Priority of the constraint.
        """
        super().__init__(constraint_id, element_id, priority)
        self.min_width = min_width
        self.min_height = min_height
        self.max_width = max_width
        self.max_height = max_height
        self.preferred_width = preferred_width
        self.preferred_height = preferred_height
        self.aspect_ratio = aspect_ratio
        self.maintain_aspect_ratio = maintain_aspect_ratio
    
    def validate(self, context: LayoutContext) -> bool:
        """Validate if the size constraint is satisfied.
        
        Args:
            context: Layout context.
            
        Returns:
            True if the constraint is satisfied, False otherwise.
        """
        element = context.get_element(self.element_id)
        if not element:
            return False
        
        # Check minimum size
        if element.width < self.min_width or element.height < self.min_height:
            return False
        
        # Check maximum size
        if element.width > self.max_width or element.height > self.max_height:
            return False
        
        # Check aspect ratio
        if self.maintain_aspect_ratio and self.aspect_ratio is not None:
            current_ratio = element.width / element.height if element.height != 0 else float('inf')
            if abs(current_ratio - self.aspect_ratio) > 0.01:  # Allow small tolerance
                return False
        
        return True
    
    def apply(self, context: LayoutContext) -> None:
        """Apply the size constraint to the layout.
        
        Args:
            context: Layout context.
        """
        element = context.get_element(self.element_id)
        if not element:
            return
        
        # Apply preferred size if specified
        if self.preferred_width is not None:
            element.width = self.preferred_width
        
        if self.preferred_height is not None:
            element.height = self.preferred_height
        
        # Apply minimum size
        element.width = max(element.width, self.min_width)
        element.height = max(element.height, self.min_height)
        
        # Apply maximum size
        element.width = min(element.width, self.max_width)
        element.height = min(element.height, self.max_height)
        
        # Apply aspect ratio
        if self.maintain_aspect_ratio and self.aspect_ratio is not None:
            current_ratio = element.width / element.height if element.height != 0 else float('inf')
            if abs(current_ratio - self.aspect_ratio) > 0.01:  # Allow small tolerance
                # Adjust width or height to match aspect ratio
                if element.width / self.aspect_ratio <= self.max_height:
                    # Adjust height based on width
                    element.height = element.width / self.aspect_ratio
                else:
                    # Adjust width based on height
                    element.width = element.height * self.aspect_ratio
    
    def to_json(self) -> Dict[str, Any]:
        """Convert the size constraint to a JSON-serializable dictionary.
        
        Returns:
            Dictionary representation of the constraint.
        """
        json_data = super().to_json()
        json_data.update({
            "min_width": self.min_width,
            "min_height": self.min_height,
            "max_width": self.max_width if self.max_width != float('inf') else None,
            "max_height": self.max_height if self.max_height != float('inf') else None,
            "preferred_width": self.preferred_width,
            "preferred_height": self.preferred_height,
            "aspect_ratio": self.aspect_ratio,
            "maintain_aspect_ratio": self.maintain_aspect_ratio
        })
        return json_data
    
    @classmethod
    def from_json(cls, json_data: Dict[str, Any]) -> 'SizeConstraint':
        """Create a size constraint from a JSON-serializable dictionary.
        
        Args:
            json_data: Dictionary representation of the constraint.
            
        Returns:
            New size constraint.
        """
        max_width = json_data.get("max_width")
        if max_width is None:
            max_width = float('inf')
        
        max_height = json_data.get("max_height")
        if max_height is None:
            max_height = float('inf')
        
        return cls(
            constraint_id=json_data["constraint_id"],
            element_id=json_data["element_id"],
            min_width=json_data.get("min_width", 0),
            min_height=json_data.get("min_height", 0),
            max_width=max_width,
            max_height=max_height,
            preferred_width=json_data.get("preferred_width"),
            preferred_height=json_data.get("preferred_height"),
            aspect_ratio=json_data.get("aspect_ratio"),
            maintain_aspect_ratio=json_data.get("maintain_aspect_ratio", False),
            priority=json_data.get("priority", 100)
        )


class PositionConstraint(LayoutConstraint):
    """Positions elements relative to others."""
    
    def __init__(self, constraint_id: str, element_id: str, reference_id: str,
                 reference_point: str = "center", element_point: str = "center",
                 offset_x: float = 0, offset_y: float = 0, priority: int = 100):
        """Initialize a position constraint.
        
        Args:
            constraint_id: Unique identifier for the constraint.
            element_id: ID of the element to constrain.
            reference_id: ID of the reference element.
            reference_point: Point on the reference element ("center", "top-left", etc.).
            element_point: Point on the element to position.
            offset_x: X-offset from the reference point.
            offset_y: Y-offset from the reference point.
            priority: Priority of the constraint.
        """
        super().__init__(constraint_id, element_id, priority)
        self.reference_id = reference_id
        self.reference_point = reference_point
        self.element_point = element_point
        self.offset_x = offset_x
        self.offset_y = offset_y
    
    def _get_point_coordinates(self, element: LayoutElement, point: str) -> Tuple[float, float]:
        """Get coordinates of a point on an element.
        
        Args:
            element: Layout element.
            point: Point name ("center", "top-left", etc.).
            
        Returns:
            Tuple of (x, y) coordinates.
        """
        if point == "center":
            return element.get_center()
        elif point == "top-left":
            return (element.x, element.y)
        elif point == "top-right":
            return (element.x + element.width, element.y)
        elif point == "bottom-left":
            return (element.x, element.y + element.height)
        elif point == "bottom-right":
            return (element.x + element.width, element.y + element.height)
        elif point == "top-center":
            return (element.x + element.width / 2, element.y)
        elif point == "bottom-center":
            return (element.x + element.width / 2, element.y + element.height)
        elif point == "left-center":
            return (element.x, element.y + element.height / 2)
        elif point == "right-center":
            return (element.x + element.width, element.y + element.height / 2)
        else:
            return element.get_center()
    
    def validate(self, context: LayoutContext) -> bool:
        """Validate if the position constraint is satisfied.
        
        Args:
            context: Layout context.
            
        Returns:
            True if the constraint is satisfied, False otherwise.
        """
        element = context.get_element(self.element_id)
        reference = context.get_element(self.reference_id)
        if not element or not reference:
            return False
        
        # Get reference point coordinates
        ref_x, ref_y = self._get_point_coordinates(reference, self.reference_point)
        
        # Get element point coordinates
        elem_x, elem_y = self._get_point_coordinates(element, self.element_point)
        
        # Check if the positions match with the offset
        return (abs(elem_x - (ref_x + self.offset_x)) < 0.1 and
                abs(elem_y - (ref_y + self.offset_y)) < 0.1)
    
    def apply(self, context: LayoutContext) -> None:
        """Apply the position constraint to the layout.
        
        Args:
            context: Layout context.
        """
        element = context.get_element(self.element_id)
        reference = context.get_element(self.reference_id)
        if not element or not reference:
            return
        
        # Get reference point coordinates
        ref_x, ref_y = self._get_point_coordinates(reference, self.reference_point)
        
        # Calculate target position for element point
        target_x = ref_x + self.offset_x
        target_y = ref_y + self.offset_y
        
        # Calculate element position based on the element point
        if self.element_point == "center":
            element.x = target_x - element.width / 2
            element.y = target_y - element.height / 2
        elif self.element_point == "top-left":
            element.x = target_x
            element.y = target_y
        elif self.element_point == "top-right":
            element.x = target_x - element.width
            element.y = target_y
        elif self.element_point == "bottom-left":
            element.x = target_x
            element.y = target_y - element.height
        elif self.element_point == "bottom-right":
            element.x = target_x - element.width
            element.y = target_y - element.height
        elif self.element_point == "top-center":
            element.x = target_x - element.width / 2
            element.y = target_y
        elif self.element_point == "bottom-center":
            element.x = target_x - element.width / 2
            element.y = target_y - element.height
        elif self.element_point == "left-center":
            element.x = target_x
            element.y = target_y - element.height / 2
        elif self.element_point == "right-center":
            element.x = target_x - element.width
            element.y = target_y - element.height / 2
    
    def to_json(self) -> Dict[str, Any]:
        """Convert the position constraint to a JSON-serializable dictionary.
        
        Returns:
            Dictionary representation of the constraint.
        """
        json_data = super().to_json()
        json_data.update({
            "reference_id": self.reference_id,
            "reference_point": self.reference_point,
            "element_point": self.element_point,
            "offset_x": self.offset_x,
            "offset_y": self.offset_y
        })
        return json_data
    
    @classmethod
    def from_json(cls, json_data: Dict[str, Any]) -> 'PositionConstraint':
        """Create a position constraint from a JSON-serializable dictionary.
        
        Args:
            json_data: Dictionary representation of the constraint.
            
        Returns:
            New position constraint.
        """
        return cls(
            constraint_id=json_data["constraint_id"],
            element_id=json_data["element_id"],
            reference_id=json_data["reference_id"],
            reference_point=json_data.get("reference_point", "center"),
            element_point=json_data.get("element_point", "center"),
            offset_x=json_data.get("offset_x", 0),
            offset_y=json_data.get("offset_y", 0),
            priority=json_data.get("priority", 100)
        )


class SpacingConstraint(LayoutConstraint):
    """Maintains spacing between elements."""
    
    def __init__(self, constraint_id: str, element_id: str, min_spacing: float,
                 reference_id: str = "", max_spacing: Optional[float] = None,
                 preferred_spacing: Optional[float] = None, 
                 edge: Optional[str] = None, priority: int = 100):
        """Initialize a spacing constraint.
        
        Args:
            constraint_id: Unique identifier for the constraint.
            element_id: ID of the element to constrain.
            min_spacing: Minimum spacing to maintain.
            reference_id: ID of the reference element (empty for container).
            max_spacing: Maximum spacing to maintain.
            preferred_spacing: Preferred spacing to maintain.
            edge: Edge to constrain ("left", "right", "top", "bottom", None for all).
            priority: Priority of the constraint.
        """
        super().__init__(constraint_id, element_id, priority)
        self.min_spacing = min_spacing
        self.reference_id = reference_id
        self.max_spacing = max_spacing
        self.preferred_spacing = preferred_spacing
        self.edge = edge
    
    def _get_spacing_to_container(self, element: LayoutElement, 
                                 container: LayoutElement, 
                                 edge: Optional[str]) -> float:
        """Get spacing from element to container edge.
        
        Args:
            element: Layout element.
            container: Container element.
            edge: Edge to check ("left", "right", "top", "bottom", None for minimum).
            
        Returns:
            Spacing value.
        """
        if edge == "left":
            return element.x - container.x
        elif edge == "right":
            return (container.x + container.width) - (element.x + element.width)
        elif edge == "top":
            return element.y - container.y
        elif edge == "bottom":
            return (container.y + container.height) - (element.y + element.height)
        else:
            # Return minimum spacing to any edge
            left = element.x - container.x
            right = (container.x + container.width) - (element.x + element.width)
            top = element.y - container.y
            bottom = (container.y + container.height) - (element.y + element.height)
            return min(left, right, top, bottom)
    
    def _get_spacing_to_element(self, element: LayoutElement, 
                               other: LayoutElement, 
                               edge: Optional[str]) -> float:
        """Get spacing from element to another element.
        
        Args:
            element: Layout element.
            other: Other element.
            edge: Edge to check ("left", "right", "top", "bottom", None for minimum).
            
        Returns:
            Spacing value.
        """
        if edge == "left":
            return element.x - (other.x + other.width)
        elif edge == "right":
            return other.x - (element.x + element.width)
        elif edge == "top":
            return element.y - (other.y + other.height)
        elif edge == "bottom":
            return other.y - (element.y + element.height)
        else:
            # Calculate minimum distance between elements
            if element.intersects(other):
                return 0
            
            # Calculate distances between edges
            left = element.x - (other.x + other.width)
            right = other.x - (element.x + element.width)
            top = element.y - (other.y + other.height)
            bottom = other.y - (element.y + element.height)
            
            # Return minimum positive distance
            distances = [d for d in [left, right, top, bottom] if d > 0]
            return min(distances) if distances else 0
    
    def validate(self, context: LayoutContext) -> bool:
        """Validate if the spacing constraint is satisfied.
        
        Args:
            context: Layout context.
            
        Returns:
            True if the constraint is satisfied, False otherwise.
        """
        element = context.get_element(self.element_id)
        if not element:
            return False
        
        if not self.reference_id:
            # Spacing to container
            container = context.get_container(self.element_id)
            if not container:
                return True  # No container, constraint doesn't apply
            
            spacing = self._get_spacing_to_container(element, container, self.edge)
        else:
            # Spacing to another element
            other = context.get_element(self.reference_id)
            if not other:
                return True  # Reference doesn't exist, constraint doesn't apply
            
            spacing = self._get_spacing_to_element(element, other, self.edge)
        
        # Check minimum spacing
        if spacing < self.min_spacing:
            return False
        
        # Check maximum spacing if specified
        if self.max_spacing is not None and spacing > self.max_spacing:
            return False
        
        return True
    
    def apply(self, context: LayoutContext) -> None:
        """Apply the spacing constraint to the layout.
        
        Args:
            context: Layout context.
        """
        element = context.get_element(self.element_id)
        if not element:
            return
        
        if not self.reference_id:
            # Spacing to container
            container = context.get_container(self.element_id)
            if not container:
                return  # No container, constraint doesn't apply
            
            spacing = self._get_spacing_to_container(element, container, self.edge)
            
            # Apply preferred spacing if specified
            target_spacing = self.preferred_spacing if self.preferred_spacing is not None else self.min_spacing
            
            if spacing < target_spacing:
                # Move element to satisfy spacing
                if self.edge == "left":
                    element.x = container.x + target_spacing
                elif self.edge == "right":
                    element.x = container.x + container.width - element.width - target_spacing
                elif self.edge == "top":
                    element.y = container.y + target_spacing
                elif self.edge == "bottom":
                    element.y = container.y + container.height - element.height - target_spacing
                elif self.edge is None:
                    # Apply spacing to all edges - move element to ensure minimum spacing from all edges
                    element.x = container.x + target_spacing
                    element.y = container.y + target_spacing
        else:
            # Spacing to another element
            other = context.get_element(self.reference_id)
            if not other:
                return  # Reference doesn't exist, constraint doesn't apply
            
            spacing = self._get_spacing_to_element(element, other, self.edge)
            
            # Apply preferred spacing if specified
            target_spacing = self.preferred_spacing if self.preferred_spacing is not None else self.min_spacing
            
            if spacing < target_spacing:
                # Move element to satisfy spacing
                if self.edge == "left":
                    element.x = other.x + other.width + target_spacing
                elif self.edge == "right":
                    element.x = other.x - element.width - target_spacing
                elif self.edge == "top":
                    element.y = other.y + other.height + target_spacing
                elif self.edge == "bottom":
                    element.y = other.y - element.height - target_spacing
                elif self.edge is None:
                    # Move in direction of minimum distance
                    left = element.x - (other.x + other.width)
                    right = other.x - (element.x + element.width)
                    top = element.y - (other.y + other.height)
                    bottom = other.y - (element.y + element.height)
                    
                    min_dist = min(abs(left), abs(right), abs(top), abs(bottom))
                    
                    if abs(left) == min_dist:
                        element.x = other.x + other.width + target_spacing
                    elif abs(right) == min_dist:
                        element.x = other.x - element.width - target_spacing
                    elif abs(top) == min_dist:
                        element.y = other.y + other.height + target_spacing
                    elif abs(bottom) == min_dist:
                        element.y = other.y - element.height - target_spacing
    
    def to_json(self) -> Dict[str, Any]:
        """Convert the spacing constraint to a JSON-serializable dictionary.
        
        Returns:
            Dictionary representation of the constraint.
        """
        json_data = super().to_json()
        json_data.update({
            "min_spacing": self.min_spacing,
            "reference_id": self.reference_id,
            "max_spacing": self.max_spacing,
            "preferred_spacing": self.preferred_spacing,
            "edge": self.edge
        })
        return json_data
    
    @classmethod
    def from_json(cls, json_data: Dict[str, Any]) -> 'SpacingConstraint':
        """Create a spacing constraint from a JSON-serializable dictionary.
        
        Args:
            json_data: Dictionary representation of the constraint.
            
        Returns:
            New spacing constraint.
        """
        return cls(
            constraint_id=json_data["constraint_id"],
            element_id=json_data["element_id"],
            min_spacing=json_data["min_spacing"],
            reference_id=json_data.get("reference_id", ""),
            max_spacing=json_data.get("max_spacing"),
            preferred_spacing=json_data.get("preferred_spacing"),
            edge=json_data.get("edge"),
            priority=json_data.get("priority", 100)
        )


class AlignmentConstraint(LayoutConstraint):
    """Aligns elements with each other."""
    
    def __init__(self, constraint_id: str, element_id: str, reference_id: str,
                 alignment: str = "center", offset: float = 0, priority: int = 100):
        """Initialize an alignment constraint.
        
        Args:
            constraint_id: Unique identifier for the constraint.
            element_id: ID of the element to constrain.
            reference_id: ID of the reference element.
            alignment: Alignment type ("center", "left", "right", "top", "bottom").
            offset: Offset from the alignment position.
            priority: Priority of the constraint.
        """
        super().__init__(constraint_id, element_id, priority)
        self.reference_id = reference_id
        self.alignment = alignment
        self.offset = offset
    
    def validate(self, context: LayoutContext) -> bool:
        """Validate if the alignment constraint is satisfied.
        
        Args:
            context: Layout context.
            
        Returns:
            True if the constraint is satisfied, False otherwise.
        """
        element = context.get_element(self.element_id)
        reference = context.get_element(self.reference_id)
        if not element or not reference:
            return False
        
        if self.alignment == "center":
            element_center_x, element_center_y = element.get_center()
            reference_center_x, reference_center_y = reference.get_center()
            return (abs(element_center_x - reference_center_x - self.offset) < 0.1 and
                    abs(element_center_y - reference_center_y) < 0.1)
        elif self.alignment == "left":
            return abs(element.x - reference.x - self.offset) < 0.1
        elif self.alignment == "right":
            return abs((element.x + element.width) - (reference.x + reference.width) - self.offset) < 0.1
        elif self.alignment == "top":
            return abs(element.y - reference.y - self.offset) < 0.1
        elif self.alignment == "bottom":
            return abs((element.y + element.height) - (reference.y + reference.height) - self.offset) < 0.1
        elif self.alignment == "horizontal":
            element_center_y = element.y + element.height / 2
            reference_center_y = reference.y + reference.height / 2
            return abs(element_center_y - reference_center_y - self.offset) < 0.1
        elif self.alignment == "vertical":
            element_center_x = element.x + element.width / 2
            reference_center_x = reference.x + reference.width / 2
            return abs(element_center_x - reference_center_x - self.offset) < 0.1
        else:
            return False
    
    def apply(self, context: LayoutContext) -> None:
        """Apply the alignment constraint to the layout.
        
        Args:
            context: Layout context.
        """
        element = context.get_element(self.element_id)
        reference = context.get_element(self.reference_id)
        if not element or not reference:
            return
        
        if self.alignment == "center":
            reference_center_x, reference_center_y = reference.get_center()
            element.x = reference_center_x - element.width / 2 + self.offset
            element.y = reference_center_y - element.height / 2
        elif self.alignment == "left":
            element.x = reference.x + self.offset
        elif self.alignment == "right":
            element.x = reference.x + reference.width - element.width + self.offset
        elif self.alignment == "top":
            element.y = reference.y + self.offset
        elif self.alignment == "bottom":
            element.y = reference.y + reference.height - element.height + self.offset
        elif self.alignment == "horizontal":
            reference_center_y = reference.y + reference.height / 2
            element.y = reference_center_y - element.height / 2 + self.offset
        elif self.alignment == "vertical":
            reference_center_x = reference.x + reference.width / 2
            element.x = reference_center_x - element.width / 2 + self.offset
    
    def to_json(self) -> Dict[str, Any]:
        """Convert the alignment constraint to a JSON-serializable dictionary.
        
        Returns:
            Dictionary representation of the constraint.
        """
        json_data = super().to_json()
        json_data.update({
            "reference_id": self.reference_id,
            "alignment": self.alignment,
            "offset": self.offset
        })
        return json_data
    
    @classmethod
    def from_json(cls, json_data: Dict[str, Any]) -> 'AlignmentConstraint':
        """Create an alignment constraint from a JSON-serializable dictionary.
        
        Args:
            json_data: Dictionary representation of the constraint.
            
        Returns:
            New alignment constraint.
        """
        return cls(
            constraint_id=json_data["constraint_id"],
            element_id=json_data["element_id"],
            reference_id=json_data["reference_id"],
            alignment=json_data.get("alignment", "center"),
            offset=json_data.get("offset", 0),
            priority=json_data.get("priority", 100)
        )


class ContainmentConstraint(LayoutConstraint):
    """Ensures elements stay within containers."""
    
    def __init__(self, constraint_id: str, element_id: str, 
                 padding: float = 0, priority: int = 100):
        """Initialize a containment constraint.
        
        Args:
            constraint_id: Unique identifier for the constraint.
            element_id: ID of the element to constrain.
            padding: Padding from container edges.
            priority: Priority of the constraint.
        """
        super().__init__(constraint_id, element_id, priority)
        self.padding = padding
    
    def validate(self, context: LayoutContext) -> bool:
        """Validate if the containment constraint is satisfied.
        
        Args:
            context: Layout context.
            
        Returns:
            True if the constraint is satisfied, False otherwise.
        """
        element = context.get_element(self.element_id)
        container = context.get_container(self.element_id)
        if not element or not container:
            return True  # No container, constraint doesn't apply
        
        # Check if element is within container with padding
        return (element.x >= container.x + self.padding and
                element.y >= container.y + self.padding and
                element.x + element.width <= container.x + container.width - self.padding and
                element.y + element.height <= container.y + container.height - self.padding)
    
    def apply(self, context: LayoutContext) -> None:
        """Apply the containment constraint to the layout.
        
        Args:
            context: Layout context.
        """
        element = context.get_element(self.element_id)
        container = context.get_container(self.element_id)
        if not element or not container:
            return  # No container, constraint doesn't apply
        
        # Adjust element position to stay within container with padding
        if element.x < container.x + self.padding:
            element.x = container.x + self.padding
        
        if element.y < container.y + self.padding:
            element.y = container.y + self.padding
        
        if element.x + element.width > container.x + container.width - self.padding:
            element.x = container.x + container.width - element.width - self.padding
        
        if element.y + element.height > container.y + container.height - self.padding:
            element.y = container.y + container.height - element.height - self.padding
    
    def to_json(self) -> Dict[str, Any]:
        """Convert the containment constraint to a JSON-serializable dictionary.
        
        Returns:
            Dictionary representation of the constraint.
        """
        json_data = super().to_json()
        json_data.update({
            "padding": self.padding
        })
        return json_data
    
    @classmethod
    def from_json(cls, json_data: Dict[str, Any]) -> 'ContainmentConstraint':
        """Create a containment constraint from a JSON-serializable dictionary.
        
        Args:
            json_data: Dictionary representation of the constraint.
            
        Returns:
            New containment constraint.
        """
        return cls(
            constraint_id=json_data["constraint_id"],
            element_id=json_data["element_id"],
            padding=json_data.get("padding", 0),
            priority=json_data.get("priority", 100)
        )


class CollisionDetector:
    """Prevents element overlap."""
    
    def detect_collisions(self, context: LayoutContext) -> List[Tuple[str, str]]:
        """Detect collisions between elements.
        
        Args:
            context: Layout context.
            
        Returns:
            List of tuples of colliding element IDs.
        """
        collisions = []
        
        # Get all elements
        elements = list(context.elements.items())
        
        # Check each pair of elements
        for i in range(len(elements)):
            id1, elem1 = elements[i]
            
            for j in range(i + 1, len(elements)):
                id2, elem2 = elements[j]
                
                # Skip if one element is the container of the other
                if context.containers.get(id1) == id2 or context.containers.get(id2) == id1:
                    continue
                
                # Check for collision
                if elem1.intersects(elem2):
                    collisions.append((id1, id2))
        
        return collisions
    
    def resolve_collisions(self, context: LayoutContext) -> None:
        """Resolve collisions between elements.
        
        Args:
            context: Layout context.
        """
        collisions = self.detect_collisions(context)
        
        for id1, id2 in collisions:
            elem1 = context.elements[id1]
            elem2 = context.elements[id2]
            
            # Calculate centers
            center1_x, center1_y = elem1.get_center()
            center2_x, center2_y = elem2.get_center()
            
            # Calculate vector from elem1 to elem2
            dx = center2_x - center1_x
            dy = center2_y - center1_y
            
            # Calculate distance
            distance = math.sqrt(dx * dx + dy * dy)
            if distance < 0.1:
                # Elements are at the same position, move in random direction
                dx, dy = 1, 0
                distance = 1
            
            # Calculate minimum distance needed
            min_distance = (elem1.width + elem2.width) / 2 + (elem1.height + elem2.height) / 2
            
            if distance < min_distance:
                # Calculate movement needed
                move_distance = min_distance - distance
                move_x = dx * move_distance / distance / 2
                move_y = dy * move_distance / distance / 2
                
                # Move elements apart
                elem1.x -= move_x
                elem1.y -= move_y
                elem2.x += move_x
                elem2.y += move_y


class ConstraintSolver:
    """Resolves all constraints."""
    
    def solve(self, context: LayoutContext) -> None:
        """Solve all constraints in the layout.
        
        Args:
            context: Layout context.
        """
        # Sort constraints by priority (higher first)
        constraints = sorted(context.constraints, key=lambda c: c.priority, reverse=True)
        
        # Apply constraints
        for constraint in constraints:
            constraint.apply(context)
        
        # Resolve collisions
        detector = CollisionDetector()
        detector.resolve_collisions(context)


class VisualRuleEnforcer:
    """Enforces Peirce's visual conventions."""
    
    def enforce_rules(self, context: LayoutContext) -> None:
        """Enforce visual rules in the layout.
        
        Args:
            context: Layout context.
        """
        # Enforce containment
        for element_id, container_id in context.containers.items():
            element = context.elements.get(element_id)
            container = context.elements.get(container_id)
            
            if element and container and not container.contains_element(element):
                # Move element inside container
                if element.x < container.x:
                    element.x = container.x
                
                if element.y < container.y:
                    element.y = container.y
                
                if element.x + element.width > container.x + container.width:
                    element.x = container.x + container.width - element.width
                
                if element.y + element.height > container.y + container.height:
                    element.y = container.y + container.height - element.height


class UserInteractionValidator:
    """Validates user interactions."""
    
    def validate_move(self, context: LayoutContext, element_id: str, 
                     new_x: float, new_y: float) -> bool:
        """Validate a move interaction.
        
        Args:
            context: Layout context.
            element_id: ID of the element to move.
            new_x: New X-coordinate.
            new_y: New Y-coordinate.
            
        Returns:
            True if the move is valid, False otherwise.
        """
        element = context.get_element(element_id)
        if not element:
            return False
        
        # Save original position
        original_x = element.x
        original_y = element.y
        
        # Try the move
        element.x = new_x
        element.y = new_y
        
        # Check containment
        container = context.get_container(element_id)
        if container and not container.contains_element(element):
            # Restore original position
            element.x = original_x
            element.y = original_y
            return False
        
        # Check collisions
        detector = CollisionDetector()
        collisions = detector.detect_collisions(context)
        
        # Restore original position
        element.x = original_x
        element.y = original_y
        
        return len(collisions) == 0
    
    def validate_resize(self, context: LayoutContext, element_id: str, 
                       new_width: float, new_height: float) -> bool:
        """Validate a resize interaction.
        
        Args:
            context: Layout context.
            element_id: ID of the element to resize.
            new_width: New width.
            new_height: New height.
            
        Returns:
            True if the resize is valid, False otherwise.
        """
        element = context.get_element(element_id)
        if not element:
            return False
        
        # Save original size
        original_width = element.width
        original_height = element.height
        
        # Try the resize
        element.width = new_width
        element.height = new_height
        
        # Check containment
        container = context.get_container(element_id)
        if container and not container.contains_element(element):
            # Restore original size
            element.width = original_width
            element.height = original_height
            return False
        
        # Check collisions
        detector = CollisionDetector()
        collisions = detector.detect_collisions(context)
        
        # Restore original size
        element.width = original_width
        element.height = original_height
        
        return len(collisions) == 0


class LayoutManager:
    """Orchestrates the entire layout process."""
    
    def __init__(self):
        """Initialize a layout manager."""
        self.solver = ConstraintSolver()
        self.enforcer = VisualRuleEnforcer()
        self.validator = UserInteractionValidator()
    
    def solve_layout(self, context: LayoutContext) -> None:
        """Solve the layout.
        
        Args:
            context: Layout context.
        """
        # Solve constraints
        self.solver.solve(context)
        
        # Enforce visual rules
        self.enforcer.enforce_rules(context)
    
    def auto_layout(self, context: LayoutContext) -> None:
        """Automatically layout elements.
        
        Args:
            context: Layout context.
        """
        # Group elements by container
        container_elements = {}
        for element_id, container_id in context.containers.items():
            if container_id not in container_elements:
                container_elements[container_id] = []
            container_elements[container_id].append(element_id)
        
        # Layout elements in each container
        for container_id, element_ids in container_elements.items():
            container = context.elements.get(container_id)
            if not container:
                continue
            
            # Calculate grid dimensions
            count = len(element_ids)
            cols = int(math.sqrt(count))
            rows = (count + cols - 1) // cols
            
            # Calculate cell size
            padding = 10
            cell_width = (container.width - padding * 2) / cols
            cell_height = (container.height - padding * 2) / rows
            
            # Position elements in grid
            for i, element_id in enumerate(element_ids):
                element = context.elements.get(element_id)
                if not element:
                    continue
                
                row = i // cols
                col = i % cols
                
                element.x = container.x + padding + col * cell_width + (cell_width - element.width) / 2
                element.y = container.y + padding + row * cell_height + (cell_height - element.height) / 2
        
        # Solve layout to apply constraints
        self.solve_layout(context)
    
    def validate_user_interaction(self, context: LayoutContext, interaction_type: str, 
                                element_id: str, **kwargs) -> bool:
        """Validate a user interaction.
        
        Args:
            context: Layout context.
            interaction_type: Type of interaction ("move", "resize").
            element_id: ID of the element to interact with.
            **kwargs: Additional parameters for the interaction.
            
        Returns:
            True if the interaction is valid, False otherwise.
        """
        if interaction_type == "move":
            return self.validator.validate_move(
                context, element_id, kwargs.get("new_x", 0), kwargs.get("new_y", 0)
            )
        elif interaction_type == "resize":
            return self.validator.validate_resize(
                context, element_id, kwargs.get("new_width", 0), kwargs.get("new_height", 0)
            )
        else:
            return False

