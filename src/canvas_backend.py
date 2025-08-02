"""
Platform-independent canvas abstraction for Existential Graph diagram rendering.
Provides base classes and factory functions for different rendering backends.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Callable, Dict, Any
from dataclasses import dataclass
from enum import Enum
import sys
import os
import uuid

# Ensure current directory is in path for script execution
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Type aliases
Coordinate = Tuple[float, float]
Color = Tuple[int, int, int]  # RGB values 0-255
EventCallback = Callable[[Any], None]


class EventType(Enum):
    """Types of canvas events"""
    MOUSE_CLICK = "mouse_click"
    MOUSE_DRAG = "mouse_drag"
    MOUSE_RELEASE = "mouse_release"
    KEY_PRESS = "key_press"
    CANVAS_RESIZE = "canvas_resize"


@dataclass(frozen=True)
class DrawingStyle:
    """Immutable drawing style specification"""
    color: Color = (0, 0, 0)  # Black
    line_width: float = 1.0
    fill_color: Optional[Color] = None
    dash_pattern: Optional[List[int]] = None
    font_size: int = 12
    font_family: str = "Arial"


@dataclass(frozen=True)
class CanvasEvent:
    """Immutable event data"""
    event_type: EventType
    position: Coordinate
    button: Optional[int] = None
    key: Optional[str] = None
    modifiers: Optional[List[str]] = None


class Canvas(ABC):
    """Abstract canvas interface for drawing operations"""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self._event_handlers: Dict[EventType, List[EventCallback]] = {}
    
    @abstractmethod
    def clear(self):
        """Clear the entire canvas"""
        pass
    
    @abstractmethod
    def draw_line(self, start: Coordinate, end: Coordinate, style: DrawingStyle):
        """Draw a straight line"""
        pass
    
    @abstractmethod
    def draw_curve(self, points: List[Coordinate], style: DrawingStyle, closed: bool = False):
        """Draw a smooth curve through points"""
        pass
    
    @abstractmethod
    def draw_circle(self, center: Coordinate, radius: float, style: DrawingStyle):
        """Draw a circle"""
        pass
    
    @abstractmethod
    def draw_text(self, text: str, position: Coordinate, style: DrawingStyle):
        """Draw text at position"""
        pass
    
    @abstractmethod
    def draw_polygon(self, points: List[Coordinate], style: DrawingStyle):
        """Draw a filled polygon"""
        pass
    
    @abstractmethod
    def get_text_bounds(self, text: str, style: DrawingStyle) -> Tuple[float, float]:
        """Get width and height of text when rendered"""
        pass
    
    def add_event_handler(self, event_type: EventType, callback: EventCallback):
        """Add event handler for specific event type"""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(callback)
    
    def remove_event_handler(self, event_type: EventType, callback: EventCallback):
        """Remove event handler"""
        if event_type in self._event_handlers:
            self._event_handlers[event_type].remove(callback)
    
    def _dispatch_event(self, event: CanvasEvent):
        """Dispatch event to registered handlers"""
        if event.event_type in self._event_handlers:
            for handler in self._event_handlers[event.event_type]:
                handler(event)
    
    @abstractmethod
    def bind_event(self, event_name: str, callback: Callable):
        """Bind a callback function to a canvas event (e.g., '<ButtonRelease-1>')."""
        pass

    @abstractmethod
    def update(self):
        """Update/refresh the canvas display"""
        pass
    
    @abstractmethod
    def save_to_file(self, filename: str, format: str = "png"):
        """Save canvas content to file"""
        pass


class CanvasBackend(ABC):
    """Abstract backend factory for creating canvas instances"""
    
    @abstractmethod
    def create_canvas(self, width: int, height: int, title: str = "Arisbe Diagram") -> Canvas:
        """Create a new canvas instance"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this backend is available on current system"""
        pass
    
    @abstractmethod
    def run_event_loop(self):
        """Start the backend's event loop (if applicable)"""
        pass
    
    @abstractmethod
    def stop_event_loop(self):
        """Stop the backend's event loop"""
        pass


# Predefined drawing styles for Existential Graph elements
class EGDrawingStyles:
    """Standard drawing styles for EG diagram elements"""
    
    # Highlighting style for selected elements
    HIGHLIGHT = DrawingStyle(
        color=(255, 0, 0),
        line_width=3.0,
        fill_color=None
    )
    
    # Selection rectangle while dragging
    SELECTION_RECTANGLE = DrawingStyle(
        color=(0, 100, 255),  # Blue
        line_width=1.0,
        fill_color=None,
        dash_pattern=[5, 5]  # Dashed line
    )
    
    # Selected area rectangle
    SELECTION_AREA = DrawingStyle(
        color=(0, 200, 100),  # Green
        line_width=2.0,
        fill_color=(200, 255, 200),  # Light green fill (RGB only)
        dash_pattern=[3, 3]  # Dashed line
    )
    
    # Identity lines - heavily drawn lines
    IDENTITY_LINE = DrawingStyle(
        color=(0, 0, 0),
        line_width=3.0
    )
    
    # Cut lines - fine-drawn, closed curves
    CUT_LINE = DrawingStyle(
        color=(0, 0, 0),
        line_width=1.0,
        fill_color=None
    )
    
    # Vertex spots - bold spots
    VERTEX_SPOT = DrawingStyle(
        color=(0, 0, 0),
        line_width=2.0,
        fill_color=(0, 0, 0)
    )
    
    # Relation signs - text labels
    RELATION_SIGN = DrawingStyle(
        color=(0, 0, 0),
        font_size=12,
        font_family="Arial"
    )
    
    # Subgraph lines - dotted curves
    SUBGRAPH_LINE = DrawingStyle(
        color=(128, 128, 128),
        line_width=1.0,
        dash_pattern=[5, 5]
    )
    
    # Edge lines connecting relations to vertices
    EDGE_LINE = DrawingStyle(
        color=(0, 0, 0),
        line_width=1.0
    )
    
    # Highlighted elements (for selection/interaction)
    HIGHLIGHT = DrawingStyle(
        color=(255, 0, 0),
        line_width=2.0
    )


def get_available_backends() -> List[str]:
    """Get list of available canvas backends"""
    backends = []
    
    # Test tkinter (should always be available)
    try:
        import tkinter
        backends.append("tkinter")
    except ImportError:
        pass
    
    # Test pygame
    try:
        import pygame
        backends.append("pygame")
    except ImportError:
        pass
    
    return backends


def create_backend(backend_name: str, **kwargs) -> Canvas:
    """Factory function to create a canvas backend."""
    if backend_name == "tkinter":
        from tkinter_backend import TkinterCanvas
        return TkinterCanvas(**kwargs)
    elif backend_name == "pygame":
        from pygame_backend import PygameCanvas
        return PygameCanvas(**kwargs)
    # Add other backends here
    else:
        raise ValueError(f"Unknown backend: {backend_name}")


def get_optimal_backend() -> CanvasBackend:
    """Get the best available backend for current platform"""
    available = get_available_backends()
    
    # Prefer pygame for performance
    if "pygame" in available:
        return create_backend("pygame")
    elif "tkinter" in available:
        return create_backend("tkinter")
    else:
        raise RuntimeError("No canvas backend available")
