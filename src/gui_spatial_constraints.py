"""
GUI-level spatial constraint validation for interactive editing.

This module provides geometric validation for element movements, cut resizing,
and area boundary crossings without requiring EGI logic knowledge.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

@dataclass
class Rectangle:
    """Simple rectangle for geometric calculations."""
    x: float
    y: float
    width: float
    height: float
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if point is inside rectangle."""
        return (self.x <= x <= self.x + self.width and 
                self.y <= y <= self.y + self.height)
    
    def overlaps(self, other: 'Rectangle', buffer: float = 0) -> bool:
        """Check if this rectangle overlaps with another."""
        return (self.x - buffer < other.x + other.width + buffer and 
                self.x + self.width + buffer > other.x - buffer and
                self.y - buffer < other.y + other.height + buffer and 
                self.y + self.height + buffer > other.y - buffer)
    
    def intersects_line(self, x1: float, y1: float, x2: float, y2: float) -> bool:
        """Check if rectangle boundary intersects with line segment."""
        # Check if line crosses any of the four rectangle edges
        edges = [
            (self.x, self.y, self.x + self.width, self.y),  # Top
            (self.x + self.width, self.y, self.x + self.width, self.y + self.height),  # Right
            (self.x + self.width, self.y + self.height, self.x, self.y + self.height),  # Bottom
            (self.x, self.y + self.height, self.x, self.y)  # Left
        ]
        
        for edge_x1, edge_y1, edge_x2, edge_y2 in edges:
            if self._lines_intersect(x1, y1, x2, y2, edge_x1, edge_y1, edge_x2, edge_y2):
                return True
        return False
    
    def _lines_intersect(self, x1: float, y1: float, x2: float, y2: float,
                        x3: float, y3: float, x4: float, y4: float) -> bool:
        """Check if two line segments intersect."""
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(denom) < 1e-10:
            return False  # Lines are parallel
        
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom
        
        return 0 <= t <= 1 and 0 <= u <= 1

class EditMode(Enum):
    """Editing modes that affect constraint validation."""
    NORMAL = "normal"
    COMPOSITION = "composition"  # Relaxed cut boundary constraints

@dataclass
class ElementInfo:
    """Information about a GUI element for constraint validation."""
    element_id: str
    element_type: str  # "predicate", "vertex", "cut", "ligature"
    bounds: Rectangle
    parent_area: Optional[str] = None

class GuiSpatialConstraints:
    """Validates spatial constraints for GUI element operations."""
    
    def __init__(self):
        self.elements: Dict[str, ElementInfo] = {}
        self.cut_hierarchy: Dict[str, str] = {}  # child_id -> parent_id
        self.edit_mode = EditMode.NORMAL
        self.min_element_separation = 8.0
        self.cut_boundary_buffer = 5.0
    
    def set_edit_mode(self, mode: EditMode):
        """Set the current editing mode."""
        self.edit_mode = mode
    
    def register_element(self, element_info: ElementInfo):
        """Register an element for constraint tracking."""
        self.elements[element_info.element_id] = element_info
    
    def update_element_bounds(self, element_id: str, new_bounds: Rectangle):
        """Update element bounds for constraint validation."""
        if element_id in self.elements:
            self.elements[element_id].bounds = new_bounds
    
    def register_cut_hierarchy(self, child_id: str, parent_id: str):
        """Register parent-child relationship between cuts."""
        self.cut_hierarchy[child_id] = parent_id
    
    def validate_element_move(self, element_id: str, new_x: float, new_y: float) -> Tuple[bool, str]:
        """
        Validate if element can be moved to new position.
        Returns (is_valid, reason_if_invalid).
        """
        if element_id not in self.elements:
            return False, "Element not found"
        
        element = self.elements[element_id]
        new_bounds = Rectangle(
            x=new_x, 
            y=new_y, 
            width=element.bounds.width, 
            height=element.bounds.height
        )
        
        # Check collision with other elements
        for other_id, other_element in self.elements.items():
            if other_id == element_id:
                continue
            
            if new_bounds.overlaps(other_element.bounds, self.min_element_separation):
                return False, f"Would overlap with {other_element.element_type} {other_id}"
        
        # Check cut boundary constraints (unless in composition mode)
        if self.edit_mode != EditMode.COMPOSITION:
            boundary_violation = self._check_cut_boundary_violation(element, new_bounds)
            if boundary_violation:
                return False, boundary_violation
        
        return True, ""
    
    def validate_cut_resize(self, cut_id: str, new_bounds: Rectangle) -> Tuple[bool, str]:
        """
        Validate if cut can be resized to new bounds.
        Returns (is_valid, reason_if_invalid).
        """
        if cut_id not in self.elements:
            return False, "Cut not found"
        
        # Check that cut doesn't overlap with sibling cuts
        parent_id = self.cut_hierarchy.get(cut_id)
        for other_id, other_element in self.elements.items():
            if (other_id != cut_id and 
                other_element.element_type == "cut" and 
                self.cut_hierarchy.get(other_id) == parent_id):
                
                if new_bounds.overlaps(other_element.bounds, self.cut_boundary_buffer):
                    return False, f"Would overlap with sibling cut {other_id}"
        
        # Check that all child elements remain inside
        child_elements = self._get_child_elements(cut_id)
        for child in child_elements:
            if not new_bounds.contains_point(child.bounds.x, child.bounds.y):
                return False, f"Child element {child.element_id} would be outside cut"
            if not new_bounds.contains_point(
                child.bounds.x + child.bounds.width, 
                child.bounds.y + child.bounds.height
            ):
                return False, f"Child element {child.element_id} would be outside cut"
        
        return True, ""
    
    def validate_ligature_path(self, start_x: float, start_y: float, 
                             end_x: float, end_y: float) -> Tuple[bool, str]:
        """
        Validate if ligature path crosses cut boundaries illegally.
        Returns (is_valid, reason_if_invalid).
        """
        # Check if ligature crosses any cut boundaries
        for cut_id, cut_element in self.elements.items():
            if cut_element.element_type == "cut":
                if cut_element.bounds.intersects_line(start_x, start_y, end_x, end_y):
                    return False, f"Ligature would cross cut boundary {cut_id}"
        
        return True, ""
    
    def get_repositioning_suggestions(self, area_id: str, new_area_bounds: Rectangle) -> List[Tuple[str, Rectangle]]:
        """
        Get suggested new positions for elements when area is resized.
        Returns list of (element_id, suggested_bounds) tuples.
        """
        suggestions = []
        child_elements = self._get_child_elements(area_id)
        
        # Simple repositioning: maintain relative positions within area
        for element in child_elements:
            # Calculate relative position within old area bounds
            old_area_bounds = self.elements[area_id].bounds if area_id in self.elements else None
            if not old_area_bounds:
                continue
            
            rel_x = (element.bounds.x - old_area_bounds.x) / old_area_bounds.width
            rel_y = (element.bounds.y - old_area_bounds.y) / old_area_bounds.height
            
            # Apply to new area bounds
            new_x = new_area_bounds.x + rel_x * new_area_bounds.width
            new_y = new_area_bounds.y + rel_y * new_area_bounds.height
            
            # Ensure element stays within bounds
            new_x = max(new_area_bounds.x + self.cut_boundary_buffer,
                       min(new_x, new_area_bounds.x + new_area_bounds.width - element.bounds.width - self.cut_boundary_buffer))
            new_y = max(new_area_bounds.y + self.cut_boundary_buffer,
                       min(new_y, new_area_bounds.y + new_area_bounds.height - element.bounds.height - self.cut_boundary_buffer))
            
            suggested_bounds = Rectangle(
                x=new_x, y=new_y, 
                width=element.bounds.width, 
                height=element.bounds.height
            )
            suggestions.append((element.element_id, suggested_bounds))
        
        return suggestions
    
    def _check_cut_boundary_violation(self, element: ElementInfo, new_bounds: Rectangle) -> Optional[str]:
        """Check if element movement would violate cut boundaries."""
        # Find which cut area the element should be in
        current_area = element.parent_area
        if not current_area:
            return None
        
        # Check if element would leave its current area
        if current_area in self.elements:
            area_bounds = self.elements[current_area].bounds
            if not area_bounds.contains_point(new_bounds.x, new_bounds.y):
                return f"Would move outside parent area {current_area}"
            if not area_bounds.contains_point(
                new_bounds.x + new_bounds.width, 
                new_bounds.y + new_bounds.height
            ):
                return f"Would move outside parent area {current_area}"
        
        return None
    
    def _get_child_elements(self, area_id: str) -> List[ElementInfo]:
        """Get all elements that are children of the given area."""
        children = []
        for element in self.elements.values():
            if element.parent_area == area_id:
                children.append(element)
        return children
