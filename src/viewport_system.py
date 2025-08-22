"""
Viewport System for Zoom/Pan Operations on Extensible Domain of Discourse

This system separates logical coordinates (unbounded EGI positioning) from 
viewport coordinates (current visible portion mapped to canvas).
"""

from typing import Tuple, Dict, Any, Optional
from dataclasses import dataclass
import math


@dataclass
class LogicalBounds:
    """Bounds in logical coordinate space (unbounded)."""
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
    def center(self) -> Tuple[float, float]:
        return (self.left + self.width / 2, self.top + self.height / 2)


@dataclass
class ViewportState:
    """Current viewport state for zoom/pan operations."""
    # Logical coordinates of viewport center
    center_x: float = 0.0
    center_y: float = 0.0
    
    # Zoom level (1.0 = normal, >1.0 = zoomed in, <1.0 = zoomed out)
    zoom: float = 1.0
    
    # Canvas dimensions in pixels
    canvas_width: int = 800
    canvas_height: int = 600
    
    def logical_to_screen(self, logical_x: float, logical_y: float) -> Tuple[int, int]:
        """Convert logical coordinates to screen pixel coordinates."""
        # Translate to viewport-relative coordinates
        rel_x = (logical_x - self.center_x) * self.zoom
        rel_y = (logical_y - self.center_y) * self.zoom
        
        # Convert to screen coordinates (center of canvas is origin)
        screen_x = int(self.canvas_width / 2 + rel_x)
        screen_y = int(self.canvas_height / 2 + rel_y)
        
        return screen_x, screen_y
    
    def screen_to_logical(self, screen_x: int, screen_y: int) -> Tuple[float, float]:
        """Convert screen pixel coordinates to logical coordinates."""
        # Convert to viewport-relative coordinates
        rel_x = screen_x - self.canvas_width / 2
        rel_y = screen_y - self.canvas_height / 2
        
        # Scale by zoom and translate to logical coordinates
        logical_x = self.center_x + rel_x / self.zoom
        logical_y = self.center_y + rel_y / self.zoom
        
        return logical_x, logical_y
    
    def get_visible_logical_bounds(self) -> LogicalBounds:
        """Get the logical coordinate bounds currently visible in viewport."""
        # Calculate half-dimensions in logical space
        half_width = (self.canvas_width / 2) / self.zoom
        half_height = (self.canvas_height / 2) / self.zoom
        
        return LogicalBounds(
            left=self.center_x - half_width,
            top=self.center_y - half_height,
            right=self.center_x + half_width,
            bottom=self.center_y + half_height
        )
    
    def pan(self, delta_x: float, delta_y: float):
        """Pan the viewport by delta in logical coordinates."""
        self.center_x += delta_x
        self.center_y += delta_y
    
    def zoom_at_point(self, zoom_factor: float, screen_x: int, screen_y: int):
        """Zoom in/out while keeping the specified screen point fixed."""
        # Convert screen point to logical coordinates before zoom
        logical_x, logical_y = self.screen_to_logical(screen_x, screen_y)
        
        # Apply zoom
        self.zoom *= zoom_factor
        
        # Convert the same logical point back to screen coordinates after zoom
        new_screen_x, new_screen_y = self.logical_to_screen(logical_x, logical_y)
        
        # Adjust center to keep the point fixed
        screen_delta_x = screen_x - new_screen_x
        screen_delta_y = screen_y - new_screen_y
        
        # Convert screen delta to logical delta and adjust center
        logical_delta_x = screen_delta_x / self.zoom
        logical_delta_y = screen_delta_y / self.zoom
        
        self.center_x += logical_delta_x
        self.center_y += logical_delta_y


class LogicalCoordinateSystem:
    """
    Manages logical coordinate space for unbounded EGI positioning.
    
    This system works independently of any viewport or canvas constraints,
    allowing elements to be positioned in mathematical space that can extend
    infinitely in any direction.
    """
    
    def __init__(self):
        self.element_positions: Dict[str, Tuple[float, float]] = {}
        self.element_bounds: Dict[str, LogicalBounds] = {}
        
    def set_element_position(self, element_id: str, x: float, y: float):
        """Set element position in logical coordinates."""
        self.element_positions[element_id] = (x, y)
    
    def get_element_position(self, element_id: str) -> Optional[Tuple[float, float]]:
        """Get element position in logical coordinates."""
        return self.element_positions.get(element_id)
    
    def set_element_bounds(self, element_id: str, bounds: LogicalBounds):
        """Set element bounds in logical coordinates."""
        self.element_bounds[element_id] = bounds
    
    def get_element_bounds(self, element_id: str) -> Optional[LogicalBounds]:
        """Get element bounds in logical coordinates."""
        return self.element_bounds.get(element_id)
    
    def get_overall_bounds(self) -> Optional[LogicalBounds]:
        """Get the overall bounds containing all elements."""
        if not self.element_bounds:
            return None
        
        min_left = min(bounds.left for bounds in self.element_bounds.values())
        min_top = min(bounds.top for bounds in self.element_bounds.values())
        max_right = max(bounds.right for bounds in self.element_bounds.values())
        max_bottom = max(bounds.bottom for bounds in self.element_bounds.values())
        
        return LogicalBounds(min_left, min_top, max_right, max_bottom)
    
    def fit_viewport_to_content(self, viewport: ViewportState, margin: float = 0.1):
        """Adjust viewport to show all content with specified margin."""
        overall_bounds = self.get_overall_bounds()
        if not overall_bounds:
            return
        
        # Add margin
        margin_x = overall_bounds.width * margin
        margin_y = overall_bounds.height * margin
        
        content_width = overall_bounds.width + 2 * margin_x
        content_height = overall_bounds.height + 2 * margin_y
        
        # Calculate zoom to fit content
        zoom_x = viewport.canvas_width / content_width
        zoom_y = viewport.canvas_height / content_height
        viewport.zoom = min(zoom_x, zoom_y)
        
        # Center on content
        viewport.center_x, viewport.center_y = overall_bounds.center


class ViewportRenderer:
    """
    Renders logical coordinates to screen coordinates using viewport transformation.
    
    This bridges the gap between the unbounded logical coordinate system and
    the bounded screen/canvas coordinate system.
    """
    
    def __init__(self, logical_system: LogicalCoordinateSystem):
        self.logical_system = logical_system
    
    def render_element_to_screen(self, element_id: str, viewport: ViewportState) -> Optional[Tuple[int, int, int, int]]:
        """
        Render element bounds to screen coordinates.
        Returns (screen_left, screen_top, screen_right, screen_bottom) or None if not visible.
        """
        logical_bounds = self.logical_system.get_element_bounds(element_id)
        if not logical_bounds:
            return None
        
        # Convert logical bounds to screen coordinates
        left, top = viewport.logical_to_screen(logical_bounds.left, logical_bounds.top)
        right, bottom = viewport.logical_to_screen(logical_bounds.right, logical_bounds.bottom)
        
        # Check if element is visible in viewport
        if (right < 0 or left > viewport.canvas_width or 
            bottom < 0 or top > viewport.canvas_height):
            return None
        
        return left, top, right, bottom
    
    def is_element_visible(self, element_id: str, viewport: ViewportState) -> bool:
        """Check if element is visible in current viewport."""
        return self.render_element_to_screen(element_id, viewport) is not None
    
    def get_visible_elements(self, viewport: ViewportState) -> list[str]:
        """Get list of element IDs visible in current viewport."""
        visible = []
        for element_id in self.logical_system.element_bounds:
            if self.is_element_visible(element_id, viewport):
                visible.append(element_id)
        return visible
