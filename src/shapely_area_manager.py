#!/usr/bin/env python3
"""
Shapely-based Area Management System for Existential Graph Diagrams

This module provides precise area boundary management using Shapely's computational
geometry engine. It ensures that all element positioning respects Dau's logical
area constraints while enabling visual optimization within those constraints.

Key Principle: Movement within logical areas is arbitrary to logic, but crossing
area boundaries violates the mathematical structure of Existential Graphs.
"""

from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from shapely.geometry import Polygon, Point, MultiPolygon
from shapely.ops import unary_union
import uuid

# Type aliases
ElementID = str
Coordinate = Tuple[float, float]
Rectangle = Tuple[float, float, float, float]  # (x1, y1, x2, y2)


@dataclass
class AreaInfo:
    """Information about a logical area in the EG diagram."""
    area_id: str
    area_type: str  # 'sheet' or 'cut'
    parent_id: Optional[str]
    children_ids: List[str]
    polygon: Polygon
    elements: Set[ElementID]  # Elements positioned in this area


class ShapelyAreaManager:
    """
    Manages area boundaries and element positioning using Shapely geometry.
    
    Provides exact area boundary management for Existential Graph diagrams,
    ensuring elements stay within their logical areas while enabling
    visual optimization within those constraints.
    """
    
    def __init__(self, canvas_bounds: Rectangle, precision: int = 10):
        """
        Initialize area manager with canvas bounds.
        
        Args:
            canvas_bounds: (x1, y1, x2, y2) bounds of the drawing canvas
            precision: Decimal precision for coordinate rounding
        """
        self.canvas_bounds = canvas_bounds
        self.precision = precision
        self.tolerance = 10 ** (-precision + 2)
        
        # Area hierarchy
        self.areas: Dict[str, AreaInfo] = {}
        self.element_areas: Dict[ElementID, str] = {}
        
        # Create sheet of assertion (level 0)
        self.sheet_id = self._create_sheet_area(canvas_bounds)
    
    def _create_sheet_area(self, bounds: Rectangle) -> str:
        """Create the sheet of assertion area."""
        sheet_id = "sheet"
        x1, y1, x2, y2 = bounds
        
        sheet_polygon = Polygon([
            (x1, y1), (x2, y1), (x2, y2), (x1, y2)
        ])
        
        self.areas[sheet_id] = AreaInfo(
            area_id=sheet_id,
            area_type='sheet',
            parent_id=None,
            children_ids=[],
            polygon=sheet_polygon,
            elements=set()
        )
        
        return sheet_id
    
    def create_cut_area(self, parent_area_id: str, cut_bounds: Rectangle) -> str:
        """
        Create a new cut area within a parent area.
        
        Args:
            parent_area_id: ID of the parent area
            cut_bounds: (x1, y1, x2, y2) bounds of the cut
            
        Returns:
            ID of the created cut area
            
        Raises:
            ValueError: If cut extends outside parent area
        """
        cut_id = f"cut_{uuid.uuid4().hex[:8]}"
        
        # Create cut polygon
        x1, y1, x2, y2 = self._round_bounds(cut_bounds)
        cut_polygon = Polygon([
            (x1, y1), (x2, y1), (x2, y2), (x1, y2)
        ])
        
        # Validate cut is within parent
        parent_area = self.areas[parent_area_id]
        if not parent_area.polygon.contains(cut_polygon):
            # Check if it's just touching the boundary
            if not parent_area.polygon.intersects(cut_polygon):
                raise ValueError(f"Cut {cut_id} does not intersect parent area {parent_area_id}")
            
            # Clip to parent boundary if partially outside
            cut_polygon = parent_area.polygon.intersection(cut_polygon)
            if cut_polygon.is_empty:
                raise ValueError(f"Cut {cut_id} results in empty area after clipping")
        
        # Create area info
        self.areas[cut_id] = AreaInfo(
            area_id=cut_id,
            area_type='cut',
            parent_id=parent_area_id,
            children_ids=[],
            polygon=cut_polygon,
            elements=set()
        )
        
        # Update parent's children list
        parent_area.children_ids.append(cut_id)
        
        return cut_id
    
    def get_available_space(self, area_id: str) -> Polygon:
        """
        Get the available space within an area (area minus child cuts).
        
        Args:
            area_id: ID of the area
            
        Returns:
            Polygon representing available space
        """
        area = self.areas[area_id]
        available = area.polygon
        
        # Subtract all child cut areas
        child_polygons = []
        for child_id in area.children_ids:
            if child_id in self.areas:
                child_polygons.append(self.areas[child_id].polygon)
        
        if child_polygons:
            child_union = unary_union(child_polygons)
            available = available.difference(child_union)
        
        return available
    
    def can_place_element(self, element_id: ElementID, position: Coordinate, 
                         area_id: str) -> bool:
        """
        Check if an element can be placed at a position within an area.
        
        Args:
            element_id: ID of the element
            position: (x, y) position to test
            area_id: ID of the target area
            
        Returns:
            True if position is valid within area constraints
        """
        if area_id not in self.areas:
            return False
        
        point = Point(position)
        available_space = self.get_available_space(area_id)
        
        # Check if point is in available space
        if available_space.contains(point):
            return True
        
        # Check if point is on boundary (within tolerance)
        if available_space.distance(point) <= self.tolerance:
            return True
        
        return False
    
    def place_element(self, element_id: ElementID, position: Coordinate, 
                     area_id: str) -> bool:
        """
        Place an element at a position within an area.
        
        Args:
            element_id: ID of the element
            position: (x, y) position
            area_id: ID of the target area
            
        Returns:
            True if placement successful
        """
        if not self.can_place_element(element_id, position, area_id):
            return False
        
        # Remove from previous area if exists
        if element_id in self.element_areas:
            old_area_id = self.element_areas[element_id]
            self.areas[old_area_id].elements.discard(element_id)
        
        # Add to new area
        self.element_areas[element_id] = area_id
        self.areas[area_id].elements.add(element_id)
        
        return True
    
    def optimize_position_in_area(self, element_id: ElementID, 
                                 desired_position: Coordinate, 
                                 area_id: str) -> Optional[Coordinate]:
        """
        Find the optimal position for an element within area constraints.
        
        Args:
            element_id: ID of the element
            desired_position: Preferred position
            area_id: ID of the target area
            
        Returns:
            Optimized position within area, or None if no valid position
        """
        # If desired position is valid, use it
        if self.can_place_element(element_id, desired_position, area_id):
            return desired_position
        
        # Find nearest valid position
        return self._find_nearest_valid_position(desired_position, area_id)
    
    def _find_nearest_valid_position(self, target: Coordinate, 
                                   area_id: str) -> Optional[Coordinate]:
        """Find the nearest valid position within an area."""
        available_space = self.get_available_space(area_id)
        
        if available_space.is_empty:
            return None
        
        # Find nearest point on available space boundary
        target_point = Point(target)
        
        # If target is inside, return it
        if available_space.contains(target_point):
            return target
        
        # Find nearest point on boundary
        nearest_point = available_space.boundary.interpolate(
            available_space.boundary.project(target_point)
        )
        
        return (nearest_point.x, nearest_point.y)
    
    def _round_bounds(self, bounds: Rectangle) -> Rectangle:
        """Round bounds to specified precision."""
        x1, y1, x2, y2 = bounds
        return (
            round(x1, self.precision),
            round(y1, self.precision),
            round(x2, self.precision),
            round(y2, self.precision)
        )
    
    def get_area_hierarchy(self) -> Dict[str, Dict]:
        """Get the complete area hierarchy for debugging/visualization."""
        hierarchy = {}
        for area_id, area_info in self.areas.items():
            hierarchy[area_id] = {
                'type': area_info.area_type,
                'parent': area_info.parent_id,
                'children': area_info.children_ids,
                'elements': list(area_info.elements),
                'bounds': list(area_info.polygon.bounds)
            }
        return hierarchy
    
    def validate_all_placements(self) -> List[str]:
        """
        Validate all current element placements.
        
        Returns:
            List of validation errors (empty if all valid)
        """
        errors = []
        
        for element_id, area_id in self.element_areas.items():
            if area_id not in self.areas:
                errors.append(f"Element {element_id} assigned to non-existent area {area_id}")
                continue
            
            # Note: We don't store positions here, so this is just structural validation
            if element_id not in self.areas[area_id].elements:
                errors.append(f"Element {element_id} not in area {area_id} element set")
        
        return errors


# Utility functions for integration with existing codebase

def create_area_manager_from_egi(egi, canvas_bounds: Rectangle) -> ShapelyAreaManager:
    """
    Create area manager from EGI structure.
    
    Args:
        egi: RelationalGraphWithCuts instance
        canvas_bounds: Canvas bounds for sheet area
        
    Returns:
        Configured ShapelyAreaManager
    """
    manager = ShapelyAreaManager(canvas_bounds)
    
    # Add cut areas from EGI
    # This will be implemented when we integrate with the EGI structure
    # For now, return basic manager with sheet area
    
    return manager
