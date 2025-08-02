"""
Pygame backend implementation for canvas rendering.
Provides high-performance, cross-platform graphics for Existential Graph diagrams.
"""

import sys
import os
import math
from typing import List, Tuple, Optional
import threading
import importlib.util

# Ensure current directory is in path for script execution
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    import pygame
    import pygame.gfxdraw
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    pygame = None

# Handle both package and script imports
if importlib.util.find_spec('canvas_backend') is not None:
    from .canvas_backend import (
        Canvas, CanvasBackend, DrawingStyle, CanvasEvent, EventType, 
        Coordinate, Color
    )
else:
    # Fallback to absolute imports when running as script
    from canvas_backend import (
        Canvas, CanvasBackend, DrawingStyle, CanvasEvent, EventType, 
        Coordinate, Color
    )


class PygameCanvas(Canvas):
    """Pygame implementation of the Canvas interface"""
    
    def __init__(self, width: int, height: int, title: str = "Arisbe Diagram"):
        super().__init__(width, height)
        
        if not PYGAME_AVAILABLE:
            raise RuntimeError("Pygame not available")
        
        pygame.init()
        pygame.font.init()
        
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        pygame.display.set_caption(title)
        
        # Create drawing surface
        self.surface = pygame.Surface((width, height), pygame.SRCALPHA)
        self.surface.fill((255, 255, 255))  # White background
        
        # Font cache
        self._font_cache = {}
        
        # Event handling
        self._running = True
        self._mouse_pressed = False
        self._last_mouse_pos = (0, 0)
    
    def clear(self):
        """Clear the entire canvas"""
        self.surface.fill((255, 255, 255))
    
    def draw_line(self, start: Coordinate, end: Coordinate, style: DrawingStyle):
        """Draw a straight line"""
        color = style.color
        width = max(1, int(style.line_width))
        
        start_pos = (int(start[0]), int(start[1]))
        end_pos = (int(end[0]), int(end[1]))
        
        if style.dash_pattern:
            self._draw_dashed_line(start_pos, end_pos, color, width, style.dash_pattern)
        else:
            pygame.draw.line(self.surface, color, start_pos, end_pos, width)
    
    def draw_curve(self, points: List[Coordinate], style: DrawingStyle, closed: bool = False):
        """Draw a smooth curve through points"""
        if len(points) < 2:
            return
        
        color = style.color
        width = max(1, int(style.line_width))
        
        # Convert to integer coordinates
        int_points = [(int(p[0]), int(p[1])) for p in points]
        
        if len(points) == 2:
            # Just a line
            self.draw_line(points[0], points[1], style)
            return
        
        # For smooth curves, we'll use Bezier approximation
        if len(points) > 2:
            smooth_points = self._smooth_curve(int_points)
            
            if style.dash_pattern:
                for i in range(len(smooth_points) - 1):
                    self._draw_dashed_line(
                        smooth_points[i], smooth_points[i + 1], 
                        color, width, style.dash_pattern
                    )
            else:
                if len(smooth_points) > 1:
                    pygame.draw.lines(self.surface, color, closed, smooth_points, width)
        
        # Fill if specified
        if style.fill_color and closed and len(int_points) >= 3:
            pygame.draw.polygon(self.surface, style.fill_color, int_points)
    
    def draw_circle(self, center: Coordinate, radius: float, style: DrawingStyle):
        """Draw a circle"""
        center_pos = (int(center[0]), int(center[1]))
        radius_int = max(1, int(radius))
        color = style.color
        width = max(1, int(style.line_width))
        
        if style.fill_color:
            pygame.draw.circle(self.surface, style.fill_color, center_pos, radius_int)
        
        pygame.draw.circle(self.surface, color, center_pos, radius_int, width)
    
    def draw_text(self, text: str, position: Coordinate, style: DrawingStyle):
        """Draw text at position"""
        font = self._get_font(style.font_family, style.font_size)
        text_surface = font.render(text, True, style.color)
        
        pos = (int(position[0]), int(position[1]))
        self.surface.blit(text_surface, pos)
    
    def draw_polygon(self, points: List[Coordinate], style: DrawingStyle):
        """Draw a filled polygon"""
        if len(points) < 3:
            return
        
        int_points = [(int(p[0]), int(p[1])) for p in points]
        
        if style.fill_color:
            pygame.draw.polygon(self.surface, style.fill_color, int_points)
        
        if style.line_width > 0:
            width = max(1, int(style.line_width))
            pygame.draw.polygon(self.surface, style.color, int_points, width)
    
    def get_text_bounds(self, text: str, style: DrawingStyle) -> Tuple[float, float]:
        """Get width and height of text when rendered"""
        font = self._get_font(style.font_family, style.font_size)
        return font.size(text)
    
    def update(self):
        """Update/refresh the canvas display"""
        self.screen.blit(self.surface, (0, 0))
        pygame.display.flip()
    
    def save_to_file(self, filename: str, format: str = "png"):
        """Save canvas content to file"""
        pygame.image.save(self.surface, filename)
    
    def handle_events(self):
        """Process pygame events and dispatch to handlers"""
        for event in pygame.event.get():
            canvas_event = None
            
            if event.type == pygame.QUIT:
                self._running = False
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._mouse_pressed = True
                self._last_mouse_pos = event.pos
                canvas_event = CanvasEvent(
                    EventType.MOUSE_CLICK,
                    event.pos,
                    button=event.button
                )
                
            elif event.type == pygame.MOUSEBUTTONUP:
                self._mouse_pressed = False
                canvas_event = CanvasEvent(
                    EventType.MOUSE_RELEASE,
                    event.pos,
                    button=event.button
                )
                
            elif event.type == pygame.MOUSEMOTION:
                if self._mouse_pressed:
                    canvas_event = CanvasEvent(
                        EventType.MOUSE_DRAG,
                        event.pos
                    )
                self._last_mouse_pos = event.pos
                
            elif event.type == pygame.KEYDOWN:
                canvas_event = CanvasEvent(
                    EventType.KEY_PRESS,
                    self._last_mouse_pos,
                    key=pygame.key.name(event.key)
                )
                
            elif event.type == pygame.VIDEORESIZE:
                self.width, self.height = event.size
                self.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                # Resize surface while preserving content
                old_surface = self.surface
                self.surface = pygame.Surface(event.size, pygame.SRCALPHA)
                self.surface.fill((255, 255, 255))
                self.surface.blit(old_surface, (0, 0))
                
                canvas_event = CanvasEvent(
                    EventType.CANVAS_RESIZE,
                    (0, 0)
                )
            
            if canvas_event:
                self._dispatch_event(canvas_event)
    
    def is_running(self) -> bool:
        """Check if the canvas window is still open"""
        return self._running
    
    def _get_font(self, font_family: str, font_size: int) -> pygame.font.Font:
        """Get or create font from cache"""
        key = (font_family, font_size)
        if key not in self._font_cache:
            try:
                # Try to load system font
                font = pygame.font.SysFont(font_family, font_size)
            except:
                # Fallback to default font
                font = pygame.font.Font(None, font_size)
            self._font_cache[key] = font
        return self._font_cache[key]
    
    def _draw_dashed_line(self, start: Tuple[int, int], end: Tuple[int, int], 
                         color: Color, width: int, dash_pattern: List[int]):
        """Draw a dashed line"""
        x1, y1 = start
        x2, y2 = end
        
        # Calculate line length and direction
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx * dx + dy * dy)
        
        if length == 0:
            return
        
        # Normalize direction
        dx /= length
        dy /= length
        
        # Draw dashed segments
        current_pos = 0
        dash_index = 0
        is_drawing = True
        
        while current_pos < length:
            dash_length = min(dash_pattern[dash_index], length - current_pos)
            
            if is_drawing:
                start_x = x1 + int(current_pos * dx)
                start_y = y1 + int(current_pos * dy)
                end_x = x1 + int((current_pos + dash_length) * dx)
                end_y = y1 + int((current_pos + dash_length) * dy)
                
                pygame.draw.line(self.surface, color, (start_x, start_y), (end_x, end_y), width)
            
            current_pos += dash_length
            dash_index = (dash_index + 1) % len(dash_pattern)
            is_drawing = not is_drawing
    
    def _smooth_curve(self, points: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Generate smooth curve points using simple interpolation"""
        if len(points) <= 2:
            return points
        
        smooth_points = [points[0]]
        
        for i in range(len(points) - 1):
            # Add intermediate points for smoothing
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            
            # Simple linear interpolation with multiple points
            steps = 5
            for step in range(1, steps + 1):
                t = step / steps
                x = int(x1 + t * (x2 - x1))
                y = int(y1 + t * (y2 - y1))
                smooth_points.append((x, y))
        
        return smooth_points


class PygameBackend(CanvasBackend):
    """Pygame backend factory"""
    
    def __init__(self):
        self._canvases = []
        self._event_thread = None
        self._running = False
    
    def create_canvas(self, width: int, height: int, title: str = "Arisbe Diagram") -> Canvas:
        """Create a new pygame canvas instance"""
        if not PYGAME_AVAILABLE:
            raise RuntimeError("Pygame not available")
        
        canvas = PygameCanvas(width, height, title)
        self._canvases.append(canvas)
        return canvas
    
    def is_available(self) -> bool:
        """Check if pygame is available"""
        return PYGAME_AVAILABLE
    
    def run_event_loop(self):
        """Start the pygame event loop"""
        if not self._canvases:
            return
        
        self._running = True
        clock = pygame.time.Clock()
        
        while self._running and any(canvas.is_running() for canvas in self._canvases):
            for canvas in self._canvases:
                if isinstance(canvas, PygameCanvas) and canvas.is_running():
                    canvas.handle_events()
                    canvas.update()
            
            clock.tick(60)  # 60 FPS
        
        pygame.quit()
    
    def stop_event_loop(self):
        """Stop the pygame event loop"""
        self._running = False
