"""
Layout Types - Consolidated type definitions for EG layout system

This module provides all the core types needed by the layout pipeline,
extracted from various layout engines to create a clean dependency structure.
"""

from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

# Core coordinate and dimension types
Coordinate = Tuple[float, float]

@dataclass
class Bounds:
    """Rectangular bounds for layout elements."""
    left: float
    top: float
    right: float
    bottom: float
    
    @property
    def width(self) -> float:
        return self.right - self.left
    
    @property
    def height(self) -> float:
        return self.bottom - self.top
    
    @property
    def center(self) -> Coordinate:
        return ((self.left + self.right) / 2, (self.top + self.bottom) / 2)

@dataclass
class LayoutElement:
    """A positioned element in the layout."""
    element_id: str
    element_type: str  # 'vertex', 'predicate', 'cut'
    position: Coordinate
    bounds: Optional[Bounds] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class LayoutResult:
    """Result of a layout operation."""
    elements: List[LayoutElement]
    canvas_bounds: Bounds
    metadata: Optional[Dict[str, Any]] = None
    success: bool = True
    error_message: Optional[str] = None

@dataclass
class LayoutConstraint:
    """Constraint for layout positioning."""
    constraint_type: str
    target_elements: List[str]
    parameters: Dict[str, Any]
