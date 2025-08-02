"""
Tkinter backend implementation for canvas rendering.
Provides a fallback option when Pygame is not available, ensuring broad compatibility.
"""

import sys
import os
import math
import tkinter as tk
from tkinter import Canvas as TkCanvas
from typing import List, Tuple, Optional, Dict, Callable
import threading

# Ensure current directory is in path for script execution
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Optional PIL support for saving
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Handle both package and script imports - COMPLETE FIX
try:
    from .canvas_backend import (
        Canvas, CanvasBackend, DrawingStyle, CanvasEvent, EventType, 
        Coordinate, Color
    )
except (ImportError, ValueError):
    # Fallback to absolute imports when running as script
    from canvas_backend import (
        Canvas, CanvasBackend, DrawingStyle, CanvasEvent, EventType, 
        Coordinate, Color
    )


class TkinterCanvas(Canvas):
    """Tkinter implementation of the Canvas interface"""
    
    def __init__(self, width: int, height: int, title: str = "Arisbe Diagram", master=None):
        super().__init__(width, height)
        
        # Initialize required attributes
        self.width = width
        self.height = height
        self._event_handlers = {}
        self._objects = []  # Track canvas objects for clearing
        self._running = True
        
        if master is None:
            self.root = tk.Tk()
            self.root.title(title)
            self.root.geometry(f"{width}x{height}")
            self.tk_canvas = TkCanvas(self.root, width=width, height=height, bg='white', highlightthickness=0)
        else:
            self.root = master
            self.tk_canvas = TkCanvas(master, width=width, height=height, bg='white', highlightthickness=0)
        
        self.tk_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Set up automatic event mapping from Tkinter to DiagramCanvas
        self._setup_event_mapping()
    
    def _setup_event_mapping(self):
        """Set up direct event mapping from Tkinter to DiagramCanvas events"""
        # Bind Tkinter events and map them to DiagramCanvas events
        self.tk_canvas.bind('<Button-1>', self._on_tk_click)
        self.tk_canvas.bind('<B1-Motion>', self._on_tk_drag)
        self.tk_canvas.bind('<ButtonRelease-1>', self._on_tk_release)
        self.tk_canvas.bind('<Key>', self._on_tk_key)
        self.tk_canvas.focus_set()  # Allow keyboard events
    
    def _on_tk_click(self, event):
        """Handle Tkinter click events and dispatch to DiagramCanvas"""
        from canvas_backend import CanvasEvent, EventType
        canvas_event = CanvasEvent(
            event_type=EventType.MOUSE_CLICK,
            position=(event.x, event.y),
            button='left',
            modifiers=self._get_modifiers(event)
        )
        self._dispatch_event(canvas_event)
    
    def _on_tk_drag(self, event):
        """Handle Tkinter drag events and dispatch to DiagramCanvas"""
        from canvas_backend import CanvasEvent, EventType
        canvas_event = CanvasEvent(
            event_type=EventType.MOUSE_DRAG,
            position=(event.x, event.y),
            button='left',
            modifiers=self._get_modifiers(event)
        )
        self._dispatch_event(canvas_event)
    
    def _on_tk_release(self, event):
        """Handle Tkinter release events and dispatch to DiagramCanvas"""
        from canvas_backend import CanvasEvent, EventType
        canvas_event = CanvasEvent(
            event_type=EventType.MOUSE_RELEASE,
            position=(event.x, event.y),
            button='left',
            modifiers=self._get_modifiers(event)
        )
        self._dispatch_event(canvas_event)
    
    def _on_tk_key(self, event):
        """Handle Tkinter key events and dispatch to DiagramCanvas"""
        from canvas_backend import CanvasEvent, EventType
        canvas_event = CanvasEvent(
            event_type=EventType.KEY_PRESS,
            position=(0, 0),  # Not relevant for key events
            key=event.keysym,
            modifiers=self._get_modifiers(event)
        )
        self._dispatch_event(canvas_event)
    
    def _get_modifiers(self, event):
        """Extract modifier keys from Tkinter event"""
        modifiers = []
        if event.state & 0x4:  # Control
            modifiers.append('ctrl')
        if event.state & 0x8:  # Alt
            modifiers.append('alt')
        if event.state & 0x1:  # Shift
            modifiers.append('shift')
        if event.state & 0x20000:  # Command (Mac)
            modifiers.append('cmd')
        return modifiers
    
    def clear(self):
        """Clear the entire canvas"""
        self.tk_canvas.delete("all")
        if hasattr(self, '_objects'):
            self._objects.clear()
        else:
            self._objects = []
    
    def draw_line(self, start: Coordinate, end: Coordinate, style: DrawingStyle):
        """Draw a straight line"""
        color = self._color_to_hex(style.color)
        width = max(1, int(style.line_width))
        
        if style.dash_pattern:
            dash = tuple(style.dash_pattern)
            obj = self.tk_canvas.create_line(
                start[0], start[1], end[0], end[1],
                fill=color, width=width, dash=dash
            )
        else:
            obj = self.tk_canvas.create_line(
                start[0], start[1], end[0], end[1],
                fill=color, width=width
            )
        
        if not hasattr(self, '_objects'):
            self._objects = []
        self._objects.append(obj)
    
    def draw_curve(self, points: List[Coordinate], style: DrawingStyle, closed: bool = False):
        """Draw a smooth curve through points"""
        if len(points) < 2:
            return
        
        color = self._color_to_hex(style.color)
        width = max(1, int(style.line_width))
        
        # Flatten points for Tkinter
        flat_points = []
        for point in points:
            flat_points.extend([point[0], point[1]])
        
        kwargs = {
            'outline': color,
            'width': width,
            'fill': '',
            'smooth': True
        }
        
        if style.dash_pattern:
            kwargs['dash'] = tuple(style.dash_pattern)
        
        if style.fill_color and closed:
            kwargs['fill'] = self._color_to_hex(style.fill_color)
        
        if closed:
            obj = self.tk_canvas.create_polygon(flat_points, **kwargs)
        else:
            obj = self.tk_canvas.create_line(flat_points, **kwargs)
        
        if not hasattr(self, '_objects'):
            self._objects = []
        self._objects.append(obj)
    
    def draw_circle(self, center: Coordinate, radius: float, style: DrawingStyle):
        """Draw a circle"""
        x, y = center
        color = self._color_to_hex(style.color)
        width = max(1, int(style.line_width))
        
        # Tkinter uses bounding box for ovals
        x1 = x - radius
        y1 = y - radius
        x2 = x + radius
        y2 = y + radius
        
        kwargs = {
            'outline': color,
            'width': width
        }
        
        if style.fill_color:
            kwargs['fill'] = self._color_to_hex(style.fill_color)
        else:
            kwargs['fill'] = ''
        
        obj = self.tk_canvas.create_oval(x1, y1, x2, y2, **kwargs)
        if not hasattr(self, '_objects'):
            self._objects = []
        self._objects.append(obj)
    
    def draw_text(self, text: str, position: Coordinate, style: DrawingStyle):
        """Draw text at position"""
        color = self._color_to_hex(style.color)
        font = (style.font_family, style.font_size)
        
        obj = self.tk_canvas.create_text(
            position[0], position[1],
            text=text, fill=color, font=font,
            anchor='nw'
        )
        if not hasattr(self, '_objects'):
            self._objects = []
        self._objects.append(obj)
    
    def draw_polygon(self, points: List[Coordinate], style: DrawingStyle):
        """Draw a filled polygon"""
        if len(points) < 3:
            return
        
        color = self._color_to_hex(style.color)
        width = max(1, int(style.line_width))
        
        # Flatten points for Tkinter
        flat_points = []
        for point in points:
            flat_points.extend([point[0], point[1]])
        
        kwargs = {
            'outline': color,
            'width': width
        }
        
        if style.fill_color:
            kwargs['fill'] = self._color_to_hex(style.fill_color)
        else:
            kwargs['fill'] = ''
        
        obj = self.tk_canvas.create_polygon(flat_points, **kwargs)
        if not hasattr(self, '_objects'):
            self._objects = []
        self._objects.append(obj)
    
    def get_text_bounds(self, text: str, style: DrawingStyle) -> Tuple[float, float]:
        """Get width and height of text when rendered"""
        font = (style.font_family, style.font_size)
        
        # Create temporary text to measure
        temp_obj = self.tk_canvas.create_text(
            0, 0, text=text, font=font, anchor='nw'
        )
        
        bbox = self.tk_canvas.bbox(temp_obj)
        self.tk_canvas.delete(temp_obj)
        
        if bbox:
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            return (width, height)
        else:
            return (0, 0)
    
    def get_text_dimensions(self, text: str, style: DrawingStyle) -> tuple[int, int]:
        """Get width and height of a text string given a style"""
        font = (style.font_family, style.font_size)
        
        # Create temporary text to measure
        temp_obj = self.tk_canvas.create_text(
            0, 0, text=text, font=font, anchor='nw'
        )
        
        bbox = self.tk_canvas.bbox(temp_obj)
        self.tk_canvas.delete(temp_obj)
        
        if bbox:
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            return (width, height)
        else:
            return (0, 0)

    def bind_event(self, event_name: str, callback: Callable):
        """Bind a callback function to a canvas event."""
        print(f"Binding event '{event_name}' to canvas")
        self.tk_canvas.bind(event_name, callback)
        # Ensure canvas can receive focus and events
        self.tk_canvas.focus_set()
        # Test binding with a simple debug callback
        def debug_callback(e):
            print(f"DEBUG: Event {event_name} triggered at ({e.x}, {e.y})")
            return callback(e)
        self.tk_canvas.bind(event_name, debug_callback)
    
    def update(self):
        """Update/refresh the canvas display"""
        if self.root:
            self.root.update_idletasks()
            self.root.update()
    
    def save_to_file(self, filename: str, format: str = "png"):
        """Save canvas content to a file using PIL/Pillow, recreating objects."""
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            print("Error: Pillow library is required to save images.")
            print("Please install it using: pip install Pillow")
            return

        width = self.tk_canvas.winfo_width()
        height = self.tk_canvas.winfo_height()
        
        # Create a new image with a white background
        image = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(image)

        # Re-draw all canvas objects onto the PIL image
        for item_id in self.tk_canvas.find_all():
            try:
                coords = self.tk_canvas.coords(item_id)
                obj_type = self.tk_canvas.type(item_id)
                config = self.tk_canvas.itemconfigure(item_id)

                if coords and config:
                    outline_color = config.get('outline', ['black'])[-1] or 'black'
                    fill_color = config.get('fill', [''])[-1]
                    width_str = config.get('width', ['1.0'])[-1]
                    line_width = int(float(width_str))

                    if obj_type in ['line', 'polygon']:
                        points = [(coords[i], coords[i+1]) for i in range(0, len(coords), 2)]
                        if len(points) > 1:
                            # For polygons, close the loop by connecting the last and first points
                            if obj_type == 'polygon':
                                draw.line(points + [points[0]], fill=outline_color, width=line_width, joint='curve')
                            else: # For lines/curves
                                draw.line(points, fill=outline_color, width=line_width, joint='curve')

                    elif obj_type == 'oval':
                        if len(coords) >= 4:
                            bbox = (coords[0], coords[1], coords[2], coords[3])
                            # Use width parameter directly, requires modern Pillow
                            draw.ellipse(bbox, outline=outline_color, fill=fill_color if fill_color else None, width=line_width)

                    elif obj_type == 'text':
                        if len(coords) >= 2:
                            text = self.tk_canvas.itemcget(item_id, 'text')
                            if text:
                                try:
                                    font_size = 12 # Default, consider making this configurable
                                    font = ImageFont.load_default(size=font_size)
                                    draw.text((coords[0], coords[1]), text, fill=outline_color, font=font, anchor='nw')
                                except Exception as e:
                                    # Fallback for font loading errors
                                    draw.text((coords[0], coords[1]), text, fill=outline_color)
            except Exception as e:
                # This helps debug issues with specific items
                # print(f"Skipping item {item_id} due to error: {e}")
                pass

        image.save(filename, format.upper())

    def is_running(self) -> bool:
        """Check if the canvas window is still open"""
        return self._running
    
    def _setup_event_handlers(self):
        """Setup Tkinter event handlers"""
        self.tk_canvas.bind("<Button-1>", self._on_mouse_click)
        self.tk_canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.tk_canvas.bind("<ButtonRelease-1>", self._on_mouse_release)
        self.tk_canvas.bind("<Key>", self._on_key_press)
        self.tk_canvas.bind("<Configure>", self._on_canvas_resize)
        
        # Make canvas focusable for key events
        self.tk_canvas.focus_set()
        
        # Handle window close
        if self.root:
            self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)
    
    def _on_mouse_click(self, event):
        """Handle mouse click events"""
        canvas_event = CanvasEvent(
            EventType.MOUSE_CLICK,
            (event.x, event.y),
            button=1
        )
        self._dispatch_event(canvas_event)
    
    def _on_mouse_drag(self, event):
        """Handle mouse drag events"""
        canvas_event = CanvasEvent(
            EventType.MOUSE_DRAG,
            (event.x, event.y)
        )
        self._dispatch_event(canvas_event)
    
    def _on_mouse_release(self, event):
        """Handle mouse release events"""
        canvas_event = CanvasEvent(
            EventType.MOUSE_RELEASE,
            (event.x, event.y),
            button=1
        )
        self._dispatch_event(canvas_event)
    
    def _on_key_press(self, event):
        """Handle key press events"""
        canvas_event = CanvasEvent(
            EventType.KEY_PRESS,
            (0, 0),  # No mouse position for key events
            key=event.keysym
        )
        self._dispatch_event(canvas_event)
    
    def _on_canvas_resize(self, event):
        """Handle canvas resize events"""
        if event.widget == self.tk_canvas:
            self.width = event.width
            self.height = event.height
            
            canvas_event = CanvasEvent(
                EventType.CANVAS_RESIZE,
                (0, 0)
            )
            self._dispatch_event(canvas_event)
    
    def _on_window_close(self):
        """Handle window close event"""
        self._running = False
        self.root.quit()
    
    def _color_to_hex(self, color: Color) -> str:
        """Convert RGB color tuple to hex string"""
        r, g, b = color
        return f"#{r:02x}{g:02x}{b:02x}"


class TkinterBackend(CanvasBackend):
    """Tkinter backend factory"""
    
    def __init__(self):
        self._canvases = []
        self._running = False
    
    def create_canvas(self, width: int, height: int, title: str = "Arisbe Diagram", **kwargs) -> Canvas:
        """Create a new tkinter canvas instance"""
        canvas = TkinterCanvas(width, height, title, **kwargs)
        self._canvases.append(canvas)
        return canvas
    
    def is_available(self) -> bool:
        """Check if tkinter is available"""
        try:
            import tkinter
            return True
        except ImportError:
            return False
    
    def run_event_loop(self):
        """Start the tkinter event loop"""
        if not self._canvases:
            return
        
        self._running = True
        
        # Run mainloop for the first canvas's root window
        # (Tkinter typically uses one main window)
        if self._canvases:
            main_canvas = self._canvases[0]
            if isinstance(main_canvas, TkinterCanvas):
                try:
                    main_canvas.root.mainloop()
                except tk.TclError:
                    # Window was closed
                    pass
    
    def stop_event_loop(self):
        """Stop the tkinter event loop"""
        self._running = False
        for canvas in self._canvases:
            if isinstance(canvas, TkinterCanvas) and canvas.is_running():
                canvas.root.quit()
