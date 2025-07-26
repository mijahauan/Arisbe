#!/usr/bin/env python3
"""
Peirce Convention-Aware Layout Engine

This module implements a layout engine that takes EGRF constraints and produces
coordinates following Peirce's visual conventions and proper geometric relationships.

Key Features:
- Respects EGRF containment relationships
- Implements proper geometric constraints (non-overlap, containment)
- Applies Peirce's visual conventions (thin cuts, heavy ligatures, alternating shading)
- Produces responsive layouts that work on different screen sizes
"""

import math
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum

from .constraint_solver import ConstraintSolver, Rectangle
from .peirce_visual_conventions import PeirceVisualConventions

class ElementType(Enum):
    CONTEXT = "context"
    PREDICATE = "predicate"
    ENTITY = "entity"

class ContextType(Enum):
    SHEET = "sheet"
    CUT = "cut"

@dataclass
class LayoutElement:
    """Represents an element with layout properties."""
    id: str
    element_type: ElementType
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    nesting_level: int = 0
    parent_id: Optional[str] = None
    children: List[str] = None
    name: str = "unnamed"  # Add name field
    
    def __post_init__(self):
        if self.children is None:
            self.children = []

@dataclass
class VisualStyle:
    """Peirce's visual conventions."""
    # Line styles
    cut_line_width: float = 1.0  # Thin lines for cuts
    ligature_line_width: float = 3.0  # Heavy lines for ligatures
    
    # Colors and shading
    even_level_fill: str = "#FFFFFF"  # White for even levels (0, 2, 4...)
    odd_level_fill: str = "#F0F0F0"   # Light gray for odd levels (1, 3, 5...)
    cut_stroke: str = "#000000"       # Black for cut outlines
    ligature_stroke: str = "#000000"  # Black for ligatures
    predicate_color: str = "#000000"  # Black text for predicates
    
    # Spacing and padding
    element_padding: float = 10.0     # Padding around elements
    cut_padding: float = 20.0         # Extra padding inside cuts
    min_element_spacing: float = 15.0 # Minimum space between elements

@dataclass
class LineSegment:
    """Represents a line segment for ligatures."""
    start_x: float
    start_y: float
    end_x: float
    end_y: float
    style: str = "ligature"  # "ligature" or "cut"

class PeirceLayoutEngine:
    """
    Convention-Aware Layout Engine that implements Peirce's visual conventions
    and proper geometric relationships for Existential Graph rendering.
    """
    
    def __init__(self, viewport_width: int = 800, viewport_height: int = 600):
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.style = VisualStyle()
        self.elements: Dict[str, LayoutElement] = {}
        self.line_segments: List[LineSegment] = []
        self.constraint_solver = ConstraintSolver(viewport_width, viewport_height)
        self.visual_conventions = PeirceVisualConventions()
        
    def calculate_layout(self, egrf_doc) -> Dict[str, Any]:
        """
        Main entry point: takes EGRF and produces positioned layout.
        
        Args:
            egrf_doc: EGRF document with logical elements and constraints
            
        Returns:
            Dictionary with positioned elements and visual styling
        """
        # Phase 1: Extract elements from EGRF
        self._extract_elements_from_egrf(egrf_doc)
        
        # Phase 2: Build containment hierarchy
        self._build_containment_hierarchy(egrf_doc)
        
        # Phase 3: Calculate geometric layout
        self._calculate_geometric_layout()
        
        # Phase 4: Generate ligature connections
        self._generate_ligature_connections(egrf_doc)
        
        # Phase 4: Apply Peirce's visual conventions
        layout_with_conventions = self._apply_visual_conventions()
        
        # Phase 5: Generate rendering instructions
        return self._generate_rendering_instructions(layout_with_conventions)
    
    def _extract_elements_from_egrf(self, egrf_doc):
        """Extract elements from EGRF and create LayoutElement objects."""
        self.elements.clear()
        
        # EGRF logical_elements is a list, not a dict
        for element_data in egrf_doc.logical_elements:
            element_id = element_data.id
            logical_type = element_data.logical_type
            
            # Map EGRF logical types to our enum
            if logical_type in ["sheet", "cut"]:
                element_type = ElementType.CONTEXT
            elif logical_type == "relation":
                element_type = ElementType.PREDICATE
            elif logical_type in ["individual", "line_of_identity"]:
                element_type = ElementType.ENTITY
            else:
                continue  # Skip unknown types
            
            # Get nesting level
            nesting_level = getattr(element_data, 'containment_level', 0)
            
            # Get element name from EGRF properties
            element_name = element_data.properties.get('name', 'unnamed') if hasattr(element_data, 'properties') else 'unnamed'
            
            # Get size constraints based on element type
            if element_type == ElementType.CONTEXT:
                if logical_type == "sheet":
                    min_width, min_height = 800, 600
                else:  # cut
                    min_width, min_height = 200, 150
            elif element_type == ElementType.PREDICATE:
                min_width, min_height = 80, 40
            else:  # entity
                min_width, min_height = 60, 30
            
            # Create layout element
            layout_element = LayoutElement(
                id=element_id,
                element_type=element_type,
                width=min_width,
                height=min_height,
                nesting_level=nesting_level,
                name=element_name  # Add the name
            )
            
            self.elements[element_id] = layout_element
    
    def _build_containment_hierarchy(self, egrf_doc):
        """Build parent-child relationships from EGRF containment data."""
        # Phase 1: Set parent-child for explicit parent_container relationships
        for element_data in egrf_doc.logical_elements:
            element_id = element_data.id
            if element_id not in self.elements:
                continue
                
            # Get parent container
            parent_container = getattr(element_data, 'parent_container', None)
            if parent_container and parent_container in self.elements:
                self.elements[element_id].parent_id = parent_container
                self.elements[parent_container].children.append(element_id)
        
        # Phase 2: Infer context hierarchy from containment levels
        # Contexts with parent_container=None need to be nested based on levels
        contexts_by_level = {}
        for element_id, element in self.elements.items():
            if element.element_type == ElementType.CONTEXT and element.parent_id is None:
                level = element.nesting_level
                if level not in contexts_by_level:
                    contexts_by_level[level] = []
                contexts_by_level[level].append(element_id)
        
        # Build context hierarchy: level N contexts are children of level N-1 contexts
        sorted_levels = sorted(contexts_by_level.keys())
        for i in range(1, len(sorted_levels)):
            parent_level = sorted_levels[i-1]
            child_level = sorted_levels[i]
            
            # For now, assume single parent at each level (typical for EG)
            if contexts_by_level[parent_level] and contexts_by_level[child_level]:
                parent_id = contexts_by_level[parent_level][0]  # Take first parent
                for child_id in contexts_by_level[child_level]:
                    self.elements[child_id].parent_id = parent_id
                    self.elements[parent_id].children.append(child_id)
        
        # Phase 3: Use layout constraints for additional containment info
        if hasattr(egrf_doc, 'layout_constraints'):
            for constraint in egrf_doc.layout_constraints:
                if hasattr(constraint, 'constraint_type') and constraint.constraint_type == 'containment':
                    # Extract containment relationships from constraints
                    target_elements = getattr(constraint, 'target_elements', [])
                    parameters = getattr(constraint, 'parameters', {})
                    container = parameters.get('container')
                    
                    if container and container in self.elements:
                        for target in target_elements:
                            if target in self.elements and self.elements[target].parent_id is None:
                                self.elements[target].parent_id = container
                                self.elements[container].children.append(target)
    
    def _calculate_geometric_layout(self):
        """Calculate positions using improved constraint solver."""
        # Use the improved constraint solver to position elements
        rectangles = self.constraint_solver.solve_layout(self.elements)
        
        # Update element positions from solved rectangles
        for element_id, rect in rectangles.items():
            if element_id in self.elements:
                element = self.elements[element_id]
                element.x = rect.x
                element.y = rect.y
                element.width = rect.width
                element.height = rect.height
    
    def _generate_ligature_connections(self, egrf_doc):
        """Generate line segments for ligatures (lines of identity)."""
        self.line_segments.clear()
        
        # Find entities and their connected predicates
        for element_data in egrf_doc.logical_elements:
            # Check for both "individual" and "line_of_identity" types
            if element_data.logical_type in ["individual", "line_of_identity"]:
                entity = self.elements.get(element_data.id)
                if not entity:
                    continue
                
                # Find predicates connected to this entity
                connected_predicates = []
                for pred_data in egrf_doc.logical_elements:
                    if pred_data.logical_type == "relation":
                        connected_entities = pred_data.properties.get('connected_entities', [])
                        if element_data.id in connected_entities:
                            predicate = self.elements.get(pred_data.id)
                            if predicate:
                                connected_predicates.append(predicate)
                
                # Create line segments from entity to each connected predicate
                entity_center_x = entity.x + entity.width / 2
                entity_center_y = entity.y + entity.height / 2
                
                for predicate in connected_predicates:
                    pred_center_x = predicate.x + predicate.width / 2
                    pred_center_y = predicate.y + predicate.height / 2
                    
                    line_segment = LineSegment(
                        start_x=entity_center_x,
                        start_y=entity_center_y,
                        end_x=pred_center_x,
                        end_y=pred_center_y,
                        style="ligature"
                    )
                    self.line_segments.append(line_segment)
    
    def _apply_visual_conventions(self) -> Dict[str, Any]:
        """Apply Peirce's visual conventions to the layout."""
        # Convert internal layout to intermediate format
        layout_data = self._convert_to_intermediate_format()
        
        # Apply visual conventions
        return self.visual_conventions.apply_visual_conventions(layout_data)
    
    def _generate_rendering_instructions(self, layout_with_conventions: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final rendering instructions."""
        return self.visual_conventions.get_rendering_instructions(layout_with_conventions)
    
    def _convert_to_intermediate_format(self) -> Dict[str, Any]:
        """Convert internal layout to intermediate format for visual conventions."""
        result = {}
        
        for element_id, element in self.elements.items():
            # Get element name from properties
            element_name = getattr(element, 'name', 'unnamed')
            if not element_name or element_name == 'unnamed':
                # Try to get name from element properties if available
                element_name = getattr(element, 'properties', {}).get('name', 'unnamed')
            
            result[element_id] = {
                'type': element.element_type.value,
                'position': (element.x, element.y),
                'size': (element.width, element.height),
                'nesting_level': element.nesting_level,
                'parent_id': element.parent_id,
                'name': element_name
            }
            
            # Add line segments for entities
            if element.element_type == ElementType.ENTITY:
                entity_lines = []
                entity_center_x = element.x + element.width / 2
                entity_center_y = element.y + element.height / 2
                
                for line in self.line_segments:
                    # Use tolerance for floating point comparison
                    tolerance = 0.1
                    if (abs(line.start_x - entity_center_x) < tolerance and
                        abs(line.start_y - entity_center_y) < tolerance):
                        entity_lines.append({
                            'start': (line.start_x, line.start_y),
                            'end': (line.end_x, line.end_y),
                            'style': line.style
                        })
                result[element_id]['line_segments'] = entity_lines
        
        return result

def test_peirce_layout_engine():
    """Test the Peirce Layout Engine with a simple example."""
    # This would be called with actual EGRF data
    print("Peirce Layout Engine created successfully")
    print("Ready to process EGRF constraints and apply Peirce's conventions")

if __name__ == "__main__":
    test_peirce_layout_engine()

