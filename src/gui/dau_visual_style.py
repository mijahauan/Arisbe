"""
Dau Visual Style Specifications

Based on analysis of authentic diagrams from Dau's treatise.
Defines precise styling parameters for Chapter 21 compliant rendering.
"""

from dataclasses import dataclass
from typing import Tuple
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPen, QBrush, QFont


@dataclass
class DauVisualStyle:
    """Visual style parameters extracted from Dau's authentic diagrams."""
    
    # Cut styling (rounded rectangles)
    cut_line_width: float = 2.0
    cut_color: QColor = QColor(0, 0, 0)  # Pure black
    cut_corner_radius: float = 8.0
    cut_padding: float = 20.0  # Generous padding around contents
    cut_nesting_margin: float = 15.0  # Space between nested cuts
    
    # Ligature styling (connection lines)
    ligature_line_width: float = 2.0
    ligature_color: QColor = QColor(0, 0, 0)  # Pure black
    ligature_style: Qt.PenStyle = Qt.SolidLine
    ligature_connection_type: str = "orthogonal"  # Right-angle connections
    
    # Vertex styling (circles)
    vertex_radius: float = 8.0
    vertex_line_width: float = 2.0
    vertex_color: QColor = QColor(0, 0, 0)  # Pure black outline
    vertex_fill: QColor = QColor(255, 255, 255)  # White fill
    
    # Predicate styling (horizontal lines)
    predicate_line_width: float = 3.0
    predicate_length: float = 40.0
    predicate_color: QColor = QColor(0, 0, 0)  # Pure black
    
    # Label styling
    label_font_family: str = "Arial"
    label_font_size: int = 12
    label_font_weight: int = QFont.Weight.Normal
    label_color: QColor = QColor(0, 0, 0)  # Pure black
    label_offset: float = 15.0  # Distance from element
    
    # Branch point styling (star pattern with arity)
    branch_center_radius: float = 4.0
    branch_line_length: float = 25.0
    branch_line_width: float = 2.0
    branch_arity_font_size: int = 10
    
    # Layout parameters
    element_spacing: float = 40.0  # Minimum space between elements
    diagram_margin: float = 30.0  # Margin around entire diagram
    
    # Sheet/background
    sheet_color: QColor = QColor(255, 255, 255)  # Pure white
    
    def get_cut_pen(self) -> QPen:
        """Get QPen for drawing cuts."""
        pen = QPen(self.cut_color)
        pen.setWidthF(self.cut_line_width)
        pen.setStyle(Qt.SolidLine)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        return pen
    
    def get_cut_brush(self) -> QBrush:
        """Get QBrush for cut fill (transparent)."""
        return QBrush(Qt.NoBrush)
    
    def get_ligature_pen(self) -> QPen:
        """Get QPen for drawing ligatures."""
        pen = QPen(self.ligature_color)
        pen.setWidthF(self.ligature_line_width)
        pen.setStyle(self.ligature_style)
        pen.setCapStyle(Qt.RoundCap)
        return pen
    
    def get_vertex_pen(self) -> QPen:
        """Get QPen for vertex outlines."""
        pen = QPen(self.vertex_color)
        pen.setWidthF(self.vertex_line_width)
        pen.setStyle(Qt.SolidLine)
        return pen
    
    def get_vertex_brush(self) -> QBrush:
        """Get QBrush for vertex fill."""
        return QBrush(self.vertex_fill)
    
    def get_predicate_pen(self) -> QPen:
        """Get QPen for drawing predicates."""
        pen = QPen(self.predicate_color)
        pen.setWidthF(self.predicate_line_width)
        pen.setStyle(Qt.SolidLine)
        pen.setCapStyle(Qt.RoundCap)
        return pen
    
    def get_label_font(self) -> QFont:
        """Get QFont for labels."""
        font = QFont(self.label_font_family, self.label_font_size)
        font.setWeight(self.label_font_weight)
        return font
    
    def get_arity_font(self) -> QFont:
        """Get QFont for arity annotations."""
        font = QFont(self.label_font_family, self.branch_arity_font_size)
        font.setWeight(QFont.Weight.Normal)
        return font


# Global style instance
DAU_STYLE = DauVisualStyle()


class DauLayoutPrinciples:
    """Layout principles extracted from Dau's diagrams."""
    
    @staticmethod
    def calculate_cut_bounds(content_bounds: Tuple[float, float, float, float], 
                           padding: float = None) -> Tuple[float, float, float, float]:
        """Calculate cut bounds with proper padding around contents."""
        if padding is None:
            padding = DAU_STYLE.cut_padding
        
        x, y, width, height = content_bounds
        return (
            x - padding,
            y - padding, 
            width + 2 * padding,
            height + 2 * padding
        )
    
    @staticmethod
    def route_ligature_orthogonal(start_point: Tuple[float, float], 
                                end_point: Tuple[float, float]) -> list:
        """Route ligature with right-angle connections like Dau's style."""
        x1, y1 = start_point
        x2, y2 = end_point
        
        # Simple L-shaped routing
        if abs(x2 - x1) > abs(y2 - y1):
            # Horizontal then vertical
            mid_point = (x2, y1)
        else:
            # Vertical then horizontal  
            mid_point = (x1, y2)
        
        return [start_point, mid_point, end_point]
    
    @staticmethod
    def position_branch_points(center: Tuple[float, float], 
                             arity: int) -> list:
        """Position branch points in star pattern with arity labels."""
        import math
        
        cx, cy = center
        points = []
        
        for i in range(arity):
            angle = (2 * math.pi * i) / arity
            x = cx + DAU_STYLE.branch_line_length * math.cos(angle)
            y = cy + DAU_STYLE.branch_line_length * math.sin(angle)
            points.append((x, y, str(i + 1)))  # Include arity label
        
        return points
