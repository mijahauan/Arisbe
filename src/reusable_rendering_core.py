"""
Reusable rendering core extracted from shared_diagram_renderer.py.
Contains essential rendering logic without complex constraint validation.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import math


@dataclass
class RenderingStyle:
    """Style configuration for rendering elements."""
    color: str = "black"
    stroke_width: float = 1.0
    fill_color: str = "none"
    opacity: float = 1.0
    font_family: str = "serif"
    font_size: int = 12


class BoundaryAnchor:
    """Handles proper text boundary anchoring for ligatures."""
    
    @staticmethod
    def rect_border_anchor(rect_x: float, rect_y: float, rect_width: float, rect_height: float,
                          from_x: float, from_y: float) -> Tuple[float, float]:
        """
        Return the intersection point of the line from from_point to the rect center 
        with the rect border. This is Ergasterion's proven boundary anchoring logic.
        """
        # Calculate rectangle center
        center_x = rect_x + rect_width / 2
        center_y = rect_y + rect_height / 2
        
        # Calculate direction vector from external point to center
        dx = center_x - from_x
        dy = center_y - from_y
        
        # Handle edge case where point is at center
        if abs(dx) < 0.001 and abs(dy) < 0.001:
            return (center_x, center_y)
        
        # Calculate intersection with rectangle edges
        # Normalize direction
        length = math.sqrt(dx * dx + dy * dy)
        if length == 0:
            return (center_x, center_y)
        
        dx_norm = dx / length
        dy_norm = dy / length
        
        # Calculate intersections with each edge
        intersections = []
        
        # Top edge (y = rect_y)
        if dy_norm != 0:
            t = (rect_y - from_y) / dy_norm
            if t > 0:
                x_intersect = from_x + t * dx_norm
                if rect_x <= x_intersect <= rect_x + rect_width:
                    intersections.append((x_intersect, rect_y, t))
        
        # Bottom edge (y = rect_y + rect_height)
        if dy_norm != 0:
            t = (rect_y + rect_height - from_y) / dy_norm
            if t > 0:
                x_intersect = from_x + t * dx_norm
                if rect_x <= x_intersect <= rect_x + rect_width:
                    intersections.append((x_intersect, rect_y + rect_height, t))
        
        # Left edge (x = rect_x)
        if dx_norm != 0:
            t = (rect_x - from_x) / dx_norm
            if t > 0:
                y_intersect = from_y + t * dy_norm
                if rect_y <= y_intersect <= rect_y + rect_height:
                    intersections.append((rect_x, y_intersect, t))
        
        # Right edge (x = rect_x + rect_width)
        if dx_norm != 0:
            t = (rect_x + rect_width - from_x) / dx_norm
            if t > 0:
                y_intersect = from_y + t * dy_norm
                if rect_y <= y_intersect <= rect_y + rect_height:
                    intersections.append((rect_x + rect_width, y_intersect, t))
        
        # Find closest intersection (smallest t)
        if intersections:
            intersections.sort(key=lambda x: x[2])  # Sort by t value
            return (intersections[0][0], intersections[0][1])
        
        # Fallback to center if no intersection found
        return (center_x, center_y)


class CutRenderer:
    """Handles cut rendering with nesting depth styling."""
    
    def __init__(self):
        self.depth_colors = [
            "rgba(173, 216, 230, 0.3)",  # Light blue - depth 0
            "rgba(144, 238, 144, 0.3)",  # Light green - depth 1
            "rgba(255, 182, 193, 0.3)",  # Light pink - depth 2
            "rgba(221, 160, 221, 0.3)",  # Light plum - depth 3+
        ]
    
    def get_cut_style(self, nesting_depth: int) -> RenderingStyle:
        """Get style for cut based on nesting depth."""
        color_index = min(nesting_depth, len(self.depth_colors) - 1)
        stroke_width = max(1, 3 - nesting_depth)  # Thinner strokes for deeper nesting
        opacity = max(0.3, 1.0 - nesting_depth * 0.15)  # More transparent for deeper nesting
        
        return RenderingStyle(
            color="black",
            stroke_width=stroke_width,
            fill_color=self.depth_colors[color_index],
            opacity=opacity
        )


class LigatureRenderer:
    """Handles ligature rendering with proper anchoring."""
    
    def __init__(self):
        self.anchor = BoundaryAnchor()
    
    def render_identity_ligature(self, vertex_positions: List[Tuple[float, float]]) -> List[str]:
        """Render identity ligature connecting vertices."""
        if len(vertex_positions) < 2:
            return []
        
        elements = []
        
        if len(vertex_positions) == 2:
            # Simple two-vertex identity ligature
            x1, y1 = vertex_positions[0]
            x2, y2 = vertex_positions[1]
            
            # Check if ligature crosses significant distance (potential cut boundary)
            distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            
            if distance > 100:  # Cross-area ligature - use curved path
                mid_x = (x1 + x2) / 2
                mid_y = (y1 + y2) / 2
                control_offset = 20
                control_x = mid_x + control_offset
                control_y = mid_y - control_offset
                
                path = f"M {x1} {y1} Q {control_x} {control_y} {x2} {y2}"
                elements.append(f'<path d="{path}" stroke="black" stroke-width="2" fill="none"/>')
            else:
                # Direct line connection
                elements.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="black" stroke-width="2"/>')
        
        else:
            # Multi-vertex identity (branch point ligature)
            # Calculate centroid as branch point
            total_x = sum(pos[0] for pos in vertex_positions)
            total_y = sum(pos[1] for pos in vertex_positions)
            branch_x = total_x / len(vertex_positions)
            branch_y = total_y / len(vertex_positions)
            
            # Draw lines from branch point to each vertex
            for x, y in vertex_positions:
                elements.append(f'<line x1="{branch_x}" y1="{branch_y}" x2="{x}" y2="{y}" stroke="black" stroke-width="2"/>')
            
            # Mark branch point
            elements.append(f'<circle cx="{branch_x}" cy="{branch_y}" r="2" fill="black"/>')
        
        return elements
    
    def render_predicate_ligature(self, predicate_rect: Tuple[float, float, float, float],
                                 vertex_positions: List[Tuple[float, float]]) -> List[str]:
        """Render ligature from predicate to vertices with proper anchoring."""
        elements = []
        pred_x, pred_y, pred_width, pred_height = predicate_rect
        
        for vertex_x, vertex_y in vertex_positions:
            # Calculate anchor point on predicate boundary
            anchor_x, anchor_y = self.anchor.rect_border_anchor(
                pred_x, pred_y, pred_width, pred_height, vertex_x, vertex_y
            )
            
            # Create ligature line
            elements.append(
                f'<line x1="{anchor_x}" y1="{anchor_y}" x2="{vertex_x}" y2="{vertex_y}" '
                f'stroke="black" stroke-width="1.5"/>'
            )
        
        return elements


class VertexRenderer:
    """Handles vertex rendering as Dau-compliant spots."""
    
    @staticmethod
    def render_vertex_spot(x: float, y: float, radius: float = 3, 
                          name: str = "", is_universal: bool = False) -> List[str]:
        """Render vertex as spot with optional name text."""
        elements = []
        
        # Vertex spot (circle)
        spot_color = "blue" if is_universal else "black"
        elements.append(
            f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{spot_color}" stroke="{spot_color}"/>'
        )
        
        # Optional name text
        if name:
            text_x = x + radius + 5  # Position text to right of spot
            text_y = y + 4  # Slight vertical offset for alignment
            elements.append(
                f'<text x="{text_x}" y="{text_y}" font-family="serif" font-size="12" fill="{spot_color}">{name}</text>'
            )
        
        return elements
