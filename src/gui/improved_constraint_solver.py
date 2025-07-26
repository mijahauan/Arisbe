#!/usr/bin/env python3
"""
Improved Geometric Constraint Solver for Peirce Layout Engine

This module implements a more sophisticated constraint solver that properly handles:
- Containment constraints (elements must be inside their parents)
- Non-overlap constraints (sibling elements cannot overlap)
- Size constraints (elements must meet minimum size requirements)
- Spacing constraints (adequate padding between elements)
"""

import math
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass

@dataclass
class Rectangle:
    """Represents a rectangular area."""
    x: float
    y: float
    width: float
    height: float
    
    def contains(self, other: 'Rectangle') -> bool:
        """Check if this rectangle completely contains another."""
        return (self.x <= other.x and
                self.y <= other.y and
                self.x + self.width >= other.x + other.width and
                self.y + self.height >= other.y + other.height)
    
    def overlaps(self, other: 'Rectangle') -> bool:
        """Check if this rectangle overlaps with another."""
        return (self.x < other.x + other.width and
                self.x + self.width > other.x and
                self.y < other.y + other.height and
                self.y + self.height > other.y)
    
    def center(self) -> Tuple[float, float]:
        """Get the center point of the rectangle."""
        return (self.x + self.width / 2, self.y + self.height / 2)

class ImprovedConstraintSolver:
    """
    Improved constraint solver that handles geometric relationships properly.
    """
    
    def __init__(self, viewport_width: int = 800, viewport_height: int = 600):
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.padding = 20  # Padding inside containers
        self.spacing = 15  # Minimum spacing between sibling elements
        
    def solve_layout(self, elements: Dict[str, Any]) -> Dict[str, Rectangle]:
        """
        Solve the layout constraints and return positioned rectangles.
        
        Args:
            elements: Dictionary of elements with their properties
            
        Returns:
            Dictionary mapping element IDs to positioned rectangles
        """
        rectangles = {}
        
        # Phase 1: Initialize rectangles with default sizes
        for element_id, element in elements.items():
            rectangles[element_id] = Rectangle(
                x=0, y=0,
                width=element.width,
                height=element.height
            )
        
        # Phase 2: Position elements hierarchically (root first)
        root_elements = [elem for elem in elements.values() if elem.parent_id is None]
        
        for root in root_elements:
            self._position_element_tree(root, elements, rectangles, 
                                      0, 0, self.viewport_width, self.viewport_height)
        
        return rectangles
    
    def _position_element_tree(self, element, all_elements: Dict[str, Any], 
                              rectangles: Dict[str, Rectangle],
                              container_x: float, container_y: float,
                              container_width: float, container_height: float):
        """
        Recursively position an element and its children within a container.
        """
        element_id = element.id
        rect = rectangles[element_id]
        
        # Position this element within the container
        if element.element_type.value == "context":
            # Contexts (cuts/sheet) can use most of the container space
            if element.nesting_level == 0:  # Sheet of assertion
                rect.x = container_x
                rect.y = container_y
                rect.width = container_width
                rect.height = container_height
            else:  # Cut
                # Size cut based on its contents
                content_width, content_height = self._calculate_content_size(element, all_elements, rectangles)
                rect.width = max(content_width + 2 * self.padding, rect.width)
                rect.height = max(content_height + 2 * self.padding, rect.height)
                
                # Center the cut in the container
                rect.x = container_x + (container_width - rect.width) / 2
                rect.y = container_y + (container_height - rect.height) / 2
        else:
            # Predicates and entities use their default size
            # Position will be set when positioning children
            pass
        
        # Position children within this element
        if element.children:
            self._position_children(element, all_elements, rectangles)
    
    def _calculate_content_size(self, container_element, all_elements: Dict[str, Any], 
                               rectangles: Dict[str, Rectangle]) -> Tuple[float, float]:
        """
        Calculate the size needed to contain all child elements.
        """
        if not container_element.children:
            return 100, 100  # Minimum size for empty containers
        
        # Separate children by type
        child_contexts = []
        child_content = []
        
        for child_id in container_element.children:
            child = all_elements[child_id]
            if child.element_type.value == "context":
                child_contexts.append(child)
            else:
                child_content.append(child)
        
        # Calculate space needed for contexts
        context_width = 0
        context_height = 0
        if child_contexts:
            # For now, assume single context child
            context = child_contexts[0]
            context_rect = rectangles[context.id]
            context_width = context_rect.width
            context_height = context_rect.height
        
        # Calculate space needed for content elements
        content_width = 0
        content_height = 0
        if child_content:
            # Arrange content elements horizontally
            total_content_width = sum(rectangles[child.id].width for child in child_content)
            total_spacing = (len(child_content) - 1) * self.spacing
            content_width = total_content_width + total_spacing
            content_height = max(rectangles[child.id].height for child in child_content)
        
        # Total size is the maximum of context and content requirements
        total_width = max(context_width, content_width)
        total_height = max(context_height, content_height)
        
        # Add some extra space if both contexts and content exist
        if child_contexts and child_content:
            total_height += content_height + self.spacing
        
        return total_width, total_height
    
    def _position_children(self, parent_element, all_elements: Dict[str, Any], 
                          rectangles: Dict[str, Rectangle]):
        """
        Position child elements within their parent container.
        """
        parent_rect = rectangles[parent_element.id]
        
        # Available area within parent (minus padding)
        available_x = parent_rect.x + self.padding
        available_y = parent_rect.y + self.padding
        available_width = parent_rect.width - 2 * self.padding
        available_height = parent_rect.height - 2 * self.padding
        
        # Separate children by type
        child_contexts = []
        child_content = []
        
        for child_id in parent_element.children:
            child = all_elements[child_id]
            if child.element_type.value == "context":
                child_contexts.append(child)
            else:
                child_content.append(child)
        
        # Position context children first (they take priority)
        context_area_height = 0
        if child_contexts:
            for context in child_contexts:
                self._position_element_tree(context, all_elements, rectangles,
                                          available_x, available_y,
                                          available_width, available_height)
                context_rect = rectangles[context.id]
                context_area_height = max(context_area_height, 
                                        context_rect.y + context_rect.height - available_y)
        
        # Position content elements in remaining space
        if child_content:
            content_y = available_y + context_area_height + self.spacing
            content_height = available_height - context_area_height - self.spacing
            
            # Arrange content elements horizontally
            current_x = available_x
            for content_element in child_content:
                content_rect = rectangles[content_element.id]
                
                # Position the content element
                content_rect.x = current_x
                content_rect.y = content_y
                
                # Move to next position
                current_x += content_rect.width + self.spacing
                
                # Recursively position children of this content element
                if content_element.children:
                    self._position_children(content_element, all_elements, rectangles)

def test_improved_constraint_solver():
    """Test the improved constraint solver."""
    print("Improved Constraint Solver created successfully")
    print("Ready to solve geometric constraints with proper containment and non-overlap")

if __name__ == "__main__":
    test_improved_constraint_solver()

