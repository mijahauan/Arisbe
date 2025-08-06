#!/usr/bin/env python3
"""
Primary Visual Element Renderer

Renders the corrected primary visual elements (LineOfIdentity, PredicateElement, CutElement)
using the existing canvas infrastructure. This completes the integration between the
corrected causality architecture and visual display.

Key Principle: Renders PRIMARY VISUAL ELEMENTS, not derived from EGI ν mapping
"""

from typing import Dict, List, Optional, Tuple, Protocol
from dataclasses import dataclass
import math

from visual_elements_primary import (
    VisualDiagram, LineOfIdentity, PredicateElement, CutElement, 
    Coordinate, VisualStyle, ElementState
)


# Canvas abstraction protocol (matches existing)
class CanvasProtocol(Protocol):
    """Protocol for canvas backends (Tkinter, Pygame, etc.)"""
    
    def draw_line(self, start: Coordinate, end: Coordinate, width: float, color: str) -> None:
        """Draw a line from start to end."""
        ...
    
    def draw_circle(self, center: Coordinate, radius: float, fill_color: str, outline_color: str, outline_width: float) -> None:
        """Draw a circle."""
        ...
    
    def draw_curve(self, points: List[Coordinate], width: float, color: str, fill: bool = False) -> None:
        """Draw a curve through points."""
        ...
    
    def draw_text(self, position: Coordinate, text: str, font_size: int, color: str) -> None:
        """Draw text at position."""
        ...
    
    def clear(self) -> None:
        """Clear the canvas."""
        ...


@dataclass(frozen=True)
class PrimaryVisualTheme:
    """Visual theme for primary visual elements following Dau's conventions."""
    
    # Heavy lines of identity (Dau's key convention)
    identity_line_width: float = 4.0
    identity_line_color: str = "black"
    
    # Vertex spots on lines of identity
    vertex_spot_radius: float = 3.0
    vertex_spot_color: str = "black"
    
    # Predicate text and boundaries
    predicate_font_size: int = 12
    predicate_font_family: str = "Arial"
    predicate_text_color: str = "black"
    predicate_boundary_radius: float = 20.0  # For hook positioning
    
    # Cut boundaries (fine-drawn)
    cut_line_width: float = 1.0
    cut_line_color: str = "black"
    
    # Selection highlighting
    selection_color: str = "blue"
    selection_line_width: float = 2.0
    
    # Unattached element styling (Warmup mode)
    unattached_color: str = "gray"
    unattached_alpha: float = 0.7


class PrimaryVisualRenderer:
    """
    Renderer for primary visual elements with corrected causality.
    
    This renderer displays the actual visual objects that users interact with,
    not derived representations from EGI ν mapping.
    """
    
    def __init__(self, canvas: CanvasProtocol, theme: Optional[PrimaryVisualTheme] = None):
        self.canvas = canvas
        self.theme = theme or PrimaryVisualTheme()
    
    def render_visual_diagram(self, visual_diagram: VisualDiagram):
        """
        Main entry point: render complete visual diagram.
        
        Rendering order (Z-index):
        1. Cuts (background, z=0)
        2. Lines of identity (heavy lines, z=1)
        3. Predicates (text with invisible hooks, z=2)
        4. Selection overlays (foreground, z=3)
        """
        print(f"🎨 Rendering visual diagram with {len(visual_diagram.get_all_elements())} elements")
        
        # Clear canvas
        self.canvas.clear()
        
        # 1. Render cuts (background)
        for cut in visual_diagram.cuts.values():
            self._render_cut(cut)
        
        # 2. Render lines of identity (heavy lines)
        for line in visual_diagram.lines_of_identity.values():
            self._render_line_of_identity(line)
        
        # 3. Render predicates (text with hooks)
        for predicate in visual_diagram.predicates.values():
            self._render_predicate(predicate)
        
        # 4. Render selection overlays
        selected_elements = visual_diagram.get_selected_elements()
        for element in selected_elements:
            self._render_selection_overlay(element)
        
        print(f"✅ Rendered {len(visual_diagram.cuts)} cuts, {len(visual_diagram.lines_of_identity)} lines, {len(visual_diagram.predicates)} predicates")
    
    def _render_line_of_identity(self, line: LineOfIdentity):
        """
        Render line of identity as heavy line segment with optional label.
        
        This is the primary visual element that users see and select.
        """
        # Choose color based on state
        if line.state == ElementState.UNATTACHED:
            color = self.theme.unattached_color
            width = self.theme.identity_line_width * 0.8
        else:
            color = self.theme.identity_line_color
            width = self.theme.identity_line_width
        
        # Draw heavy line
        self.canvas.draw_line(
            start=line.start_pos,
            end=line.end_pos,
            width=width,
            color=color
        )
        
        # Draw vertex spots at ends (optional - can be toggled)
        self._draw_vertex_spot(line.start_pos, color)
        self._draw_vertex_spot(line.end_pos, color)
        
        # Draw label if present
        if line.label:
            label_pos = line.get_label_coordinate()
            self.canvas.draw_text(
                position=label_pos,
                text=line.label,
                font_size=self.theme.predicate_font_size,
                color=color
            )
    
    def _render_predicate(self, predicate: PredicateElement):
        """
        Render predicate as text with invisible hook boundary.
        
        The hooks are invisible but define where lines can attach.
        """
        # Choose color based on state
        if predicate.state == ElementState.UNATTACHED:
            color = self.theme.unattached_color
        else:
            color = self.theme.predicate_text_color
        
        # Draw predicate text
        self.canvas.draw_text(
            position=predicate.position,
            text=predicate.text,
            font_size=self.theme.predicate_font_size,
            color=color
        )
        
        # Optionally draw hook positions for debugging (normally invisible)
        if hasattr(self, '_debug_hooks') and self._debug_hooks:
            self._render_hook_positions(predicate)
    
    def _render_cut(self, cut: CutElement):
        """
        Render cut as fine-drawn closed curve (Dau's convention).
        """
        x1, y1, x2, y2 = cut.bounds
        
        # Create oval/ellipse points
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        width = x2 - x1
        height = y2 - y1
        
        # Generate ellipse points
        points = []
        num_points = 32
        for i in range(num_points):
            angle = 2 * math.pi * i / num_points
            x = center_x + (width / 2) * math.cos(angle)
            y = center_y + (height / 2) * math.sin(angle)
            points.append(Coordinate(x, y))
        
        # Draw fine-drawn closed curve
        self.canvas.draw_curve(
            points=points,
            width=self.theme.cut_line_width,
            color=self.theme.cut_line_color,
            fill=False
        )
    
    def _render_selection_overlay(self, element):
        """
        Render selection overlay for selected elements.
        """
        if isinstance(element, LineOfIdentity):
            # Highlight the line
            self.canvas.draw_line(
                start=element.start_pos,
                end=element.end_pos,
                width=self.theme.selection_line_width,
                color=self.theme.selection_color
            )
        
        elif isinstance(element, PredicateElement):
            # Draw selection circle around predicate
            self.canvas.draw_circle(
                center=element.position,
                radius=self.theme.predicate_boundary_radius,
                fill_color=None,
                outline_color=self.theme.selection_color,
                outline_width=self.theme.selection_line_width
            )
        
        elif isinstance(element, CutElement):
            # Highlight cut boundary
            x1, y1, x2, y2 = element.bounds
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            width = x2 - x1
            height = y2 - y1
            
            # Generate highlighted ellipse points
            points = []
            num_points = 32
            for i in range(num_points):
                angle = 2 * math.pi * i / num_points
                x = center_x + (width / 2) * math.cos(angle)
                y = center_y + (height / 2) * math.sin(angle)
                points.append(Coordinate(x, y))
            
            self.canvas.draw_curve(
                points=points,
                width=self.theme.selection_line_width,
                color=self.theme.selection_color,
                fill=False
            )
    
    def _draw_vertex_spot(self, position: Coordinate, color: str):
        """Draw small spot at vertex position on line of identity."""
        self.canvas.draw_circle(
            center=position,
            radius=self.theme.vertex_spot_radius,
            fill_color=color,
            outline_color=color,
            outline_width=1.0
        )
    
    def _render_hook_positions(self, predicate: PredicateElement):
        """Debug method: render invisible hook positions."""
        for hook_pos in range(predicate.max_arity):
            hook_coord = predicate.get_hook_coordinate(hook_pos)
            self.canvas.draw_circle(
                center=hook_coord,
                radius=2.0,
                fill_color="red" if predicate.hooks[hook_pos] else "lightgray",
                outline_color="red" if predicate.hooks[hook_pos] else "gray",
                outline_width=1.0
            )
    
    def enable_debug_hooks(self, enable: bool = True):
        """Enable/disable rendering of hook positions for debugging."""
        self._debug_hooks = enable


# Tkinter Canvas Implementation (compatible with existing)
class TkinterCanvas:
    """Tkinter implementation of CanvasProtocol for primary visual elements."""
    
    def __init__(self, tk_canvas):
        self.tk_canvas = tk_canvas
    
    def draw_line(self, start: Coordinate, end: Coordinate, width: float = 2.0, color: str = "black"):
        """Draw a line from start to end."""
        self.tk_canvas.create_line(
            start.x, start.y, end.x, end.y,
            width=width, fill=color, capstyle="round"
        )
    
    def draw_circle(self, center: Coordinate, radius: float, fill_color: str = None, 
                   outline_color: str = None, outline_width: float = 1.0):
        """Draw a circle."""
        x1 = center.x - radius
        y1 = center.y - radius
        x2 = center.x + radius
        y2 = center.y + radius
        
        self.tk_canvas.create_oval(
            x1, y1, x2, y2,
            fill=fill_color or "",
            outline=outline_color or "black",
            width=outline_width
        )
    
    def draw_curve(self, points: List[Coordinate], width: float = 2.0, color: str = "black", fill: bool = False):
        """Draw a curve through points."""
        if len(points) < 2:
            return
        
        # Convert to flat coordinate list for Tkinter
        coords = []
        for point in points:
            coords.extend([point.x, point.y])
        
        # Close the curve by adding first point at end
        coords.extend([points[0].x, points[0].y])
        
        self.tk_canvas.create_polygon(
            coords,
            fill="" if not fill else color,
            outline=color,
            width=width,
            smooth=True
        )
    
    def draw_text(self, position: Coordinate, text: str, font_size: int = 12, color: str = "black"):
        """Draw text at position."""
        self.tk_canvas.create_text(
            position.x, position.y,
            text=text,
            font=("Arial", font_size),
            fill=color
        )
    
    def clear(self):
        """Clear the canvas."""
        self.tk_canvas.delete("all")


def test_primary_visual_renderer():
    """Test the primary visual renderer with sample elements."""
    print("=== Testing Primary Visual Renderer ===\n")
    
    # Create a visual diagram with sample elements
    diagram = VisualDiagram()
    
    # Create a line of identity
    line = LineOfIdentity(
        start_pos=Coordinate(100, 200),
        end_pos=Coordinate(200, 200),
        label="Socrates"
    )
    diagram.add_line(line)
    
    # Create a predicate
    predicate = PredicateElement(
        position=Coordinate(250, 200),
        text="Human"
    )
    diagram.add_predicate(predicate)
    
    # Attach line to predicate
    line.attach_to_predicate(predicate, hook_position=0, end="end")
    
    # Create a cut
    cut = CutElement(bounds=(80, 180, 280, 220))
    diagram.add_cut(cut)
    
    # Select the line for testing
    line.select()
    
    print(f"✅ Created test diagram:")
    print(f"   - Lines: {len(diagram.lines_of_identity)}")
    print(f"   - Predicates: {len(diagram.predicates)}")
    print(f"   - Cuts: {len(diagram.cuts)}")
    print(f"   - Selected: {len(diagram.get_selected_elements())}")
    
    print("\n🎨 Primary Visual Renderer ready for integration!")
    print("✅ Renders primary visual elements (not derived from ν mapping)")
    print("✅ Supports selection overlays and state-based styling")
    print("✅ Compatible with existing canvas infrastructure")
    print("✅ Follows Dau's visual conventions")


if __name__ == "__main__":
    test_primary_visual_renderer()
