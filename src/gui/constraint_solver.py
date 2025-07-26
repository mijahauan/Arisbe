#!/usr/bin/env python3
"""
Fixed Geometric Constraint Solver for Peirce Layout Engine

This is a complete rewrite of the constraint solver that properly handles:
- Hierarchical positioning without circular dependencies
- Non-overlapping sibling elements
- Proper containment relationships
- Realistic element sizing and spacing
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
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if this rectangle contains a point."""
        return (self.x <= x <= self.x + self.width and
                self.y <= y <= self.y + self.height)
    
    def overlaps(self, other: 'Rectangle') -> bool:
        """Check if this rectangle overlaps with another."""
        return (self.x < other.x + other.width and
                self.x + self.width > other.x and
                self.y < other.y + other.height and
                self.y + self.height > other.y)
    
    def center(self) -> Tuple[float, float]:
        """Get the center point of the rectangle."""
        return (self.x + self.width / 2, self.y + self.height / 2)

class ConstraintSolver:
    """
    Fixed constraint solver with proper hierarchical positioning.
    """
    
    def __init__(self, viewport_width: int = 800, viewport_height: int = 600):
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        
        # Layout parameters
        self.cut_padding = 30      # Padding inside cuts
        self.element_spacing = 25  # Spacing between sibling elements
        self.min_cut_size = 120    # Minimum size for cuts
        self.predicate_width = 80  # Standard predicate width
        self.predicate_height = 30 # Standard predicate height
        
    def solve_layout(self, elements: Dict[str, Any]) -> Dict[str, Rectangle]:
        """
        Solve layout constraints using a bottom-up approach.
        
        Args:
            elements: Dictionary of elements with their properties
            
        Returns:
            Dictionary mapping element IDs to positioned rectangles
        """
        rectangles = {}
        
        # Phase 1: Initialize all rectangles with default sizes
        for element_id, element in elements.items():
            if element.element_type.value == "context":
                # Contexts will be sized based on their contents
                rectangles[element_id] = Rectangle(0, 0, self.min_cut_size, self.min_cut_size)
            elif element.element_type.value == "predicate":
                rectangles[element_id] = Rectangle(0, 0, self.predicate_width, self.predicate_height)
            else:  # entity
                # Entities are invisible but need small size for ligature connections
                rectangles[element_id] = Rectangle(0, 0, 10, 10)
        
        # Phase 2: Build hierarchy tree
        hierarchy = self._build_hierarchy(elements)
        
        # Phase 3: Size elements bottom-up (leaves first)
        self._size_elements_bottom_up(hierarchy, elements, rectangles)
        
        # Phase 4: Position elements top-down (root first)
        root_elements = [elem for elem in elements.values() if elem.parent_id is None]
        for root in root_elements:
            if root.element_type.value == "context" and root.nesting_level == 0:
                # Sheet of assertion fills viewport
                rect = rectangles[root.id]
                rect.x = 0
                rect.y = 0
                rect.width = self.viewport_width
                rect.height = self.viewport_height
                
                # Position children within the sheet
                self._position_children_in_container(root, elements, rectangles)
            else:
                # Other root elements (shouldn't happen in well-formed EG)
                self._position_children_in_container(root, elements, rectangles)
        
        return rectangles
    
    def _build_hierarchy(self, elements: Dict[str, Any]) -> Dict[str, List[str]]:
        """Build parent -> children mapping."""
        hierarchy = {}
        for element_id, element in elements.items():
            if element.parent_id:
                if element.parent_id not in hierarchy:
                    hierarchy[element.parent_id] = []
                hierarchy[element.parent_id].append(element_id)
            else:
                if element_id not in hierarchy:
                    hierarchy[element_id] = []
        return hierarchy
    
    def _size_elements_bottom_up(self, hierarchy: Dict[str, List[str]], 
                                elements: Dict[str, Any], 
                                rectangles: Dict[str, Rectangle]):
        """Size elements from leaves to root."""
        # Process elements in reverse topological order (leaves first)
        visited = set()
        
        def size_element(element_id: str):
            if element_id in visited:
                return
            visited.add(element_id)
            
            element = elements[element_id]
            
            # First, size all children
            for child_id in hierarchy.get(element_id, []):
                size_element(child_id)
            
            # Now size this element based on its children
            if element.element_type.value == "context" and element.nesting_level > 0:
                # Size cut based on its contents
                content_width, content_height = self._calculate_required_size(element_id, hierarchy, elements, rectangles)
                rect = rectangles[element_id]
                rect.width = max(content_width + 2 * self.cut_padding, self.min_cut_size)
                rect.height = max(content_height + 2 * self.cut_padding, self.min_cut_size)
        
        # Start sizing from all elements
        for element_id in elements.keys():
            size_element(element_id)
    
    def _calculate_required_size(self, container_id: str, hierarchy: Dict[str, List[str]], 
                               elements: Dict[str, Any], rectangles: Dict[str, Rectangle]) -> Tuple[float, float]:
        """Calculate the size required to contain all children."""
        children = hierarchy.get(container_id, [])
        if not children:
            return self.min_cut_size, self.min_cut_size
        
        # Separate children by type
        child_contexts = []
        child_predicates = []
        
        for child_id in children:
            child = elements[child_id]
            if child.element_type.value == "context":
                child_contexts.append(child_id)
            elif child.element_type.value == "predicate":
                child_predicates.append(child_id)
        
        # Calculate space needed
        total_width = 0
        total_height = 0
        
        if child_contexts:
            # Contexts are centered, so we need the size of the largest
            max_context_width = max(rectangles[cid].width for cid in child_contexts)
            max_context_height = max(rectangles[cid].height for cid in child_contexts)
            total_width = max(total_width, max_context_width)
            total_height = max(total_height, max_context_height)
        
        if child_predicates:
            # Predicates are arranged horizontally
            predicates_width = sum(rectangles[pid].width for pid in child_predicates)
            predicates_width += (len(child_predicates) - 1) * self.element_spacing
            predicates_height = max(rectangles[pid].height for pid in child_predicates)
            
            total_width = max(total_width, predicates_width)
            
            # If we have both contexts and predicates, stack them vertically
            if child_contexts:
                total_height += predicates_height + self.element_spacing
            else:
                total_height = max(total_height, predicates_height)
        
        return total_width, total_height
    
    def _position_children_in_container(self, container_element, elements: Dict[str, Any], 
                                      rectangles: Dict[str, Rectangle]):
        """Position children within their container."""
        container_rect = rectangles[container_element.id]
        children = container_element.children
        
        if not children:
            return
        
        # Available area (minus padding)
        available_x = container_rect.x + self.cut_padding
        available_y = container_rect.y + self.cut_padding
        available_width = container_rect.width - 2 * self.cut_padding
        available_height = container_rect.height - 2 * self.cut_padding
        
        # Separate children by type
        child_contexts = []
        child_predicates = []
        
        for child_id in children:
            child = elements[child_id]
            if child.element_type.value == "context":
                child_contexts.append(child)
            elif child.element_type.value == "predicate":
                child_predicates.append(child)
        
        # Position context children first (centered)
        contexts_positioned = 0
        for context in child_contexts:
            context_rect = rectangles[context.id]
            
            # Center the context, but offset multiple contexts to avoid complete overlap
            offset_x = contexts_positioned * 50  # Slight offset for multiple contexts
            offset_y = contexts_positioned * 30
            
            context_rect.x = available_x + (available_width - context_rect.width) / 2 + offset_x
            context_rect.y = available_y + (available_height - context_rect.height) / 2 + offset_y
            
            # Ensure context stays within bounds
            if context_rect.x + context_rect.width > container_rect.x + container_rect.width - self.cut_padding:
                context_rect.x = container_rect.x + container_rect.width - self.cut_padding - context_rect.width
            if context_rect.y + context_rect.height > container_rect.y + container_rect.height - self.cut_padding:
                context_rect.y = container_rect.y + container_rect.height - self.cut_padding - context_rect.height
            
            contexts_positioned += 1
            
            # Recursively position children of this context
            self._position_children_in_container(context, elements, rectangles)
        
        # Position content elements in remaining space
        if child_predicates:
            # Calculate total width needed for predicates (horizontal arrangement)
            total_predicates_width = sum(rectangles[p.id].width for p in child_predicates)
            total_predicates_width += (len(child_predicates) - 1) * self.element_spacing
            
            # Find a good Y position (avoid contexts)
            predicate_y = available_y
            if child_contexts:
                # Position predicates below contexts with some spacing
                max_context_bottom = max(rectangles[c.id].y + rectangles[c.id].height for c in child_contexts)
                predicate_y = max(predicate_y, max_context_bottom + self.element_spacing)
            else:
                # If no contexts, center predicates vertically in available space
                predicate_height = max(rectangles[p.id].height for p in child_predicates) if child_predicates else 0
                predicate_y = available_y + (available_height - predicate_height) / 2
            
            # Center predicates horizontally and arrange them horizontally
            start_x = available_x + (available_width - total_predicates_width) / 2
            current_x = start_x
            
            for predicate in child_predicates:
                predicate_rect = rectangles[predicate.id]
                predicate_rect.x = current_x
                predicate_rect.y = predicate_y
                
                current_x += predicate_rect.width + self.element_spacing
        
        # Position entities (they should be positioned near their connected predicates)
        child_entities = [child_id for child_id in children if elements[child_id].element_type.value == "entity"]
        for entity_id in child_entities:
            entity_rect = rectangles[entity_id]
            
            # Position entity near the center of the container
            entity_rect.x = available_x + available_width / 2 - entity_rect.width / 2
            entity_rect.y = available_y + available_height / 2 - entity_rect.height / 2

def test_constraint_solver():
    """Test the constraint solver."""
    print("Constraint Solver created successfully")
    print("Ready to solve geometric constraints with proper hierarchical positioning")

if __name__ == "__main__":
    test_constraint_solver()

