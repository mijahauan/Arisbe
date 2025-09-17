"""
Peirce-Authentic Style Implementation

Recreates the historical appearance of Peirce's original existential graphs
with traditional pen-and-ink aesthetic and classical proportions.
"""

from typing import Dict, Any
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont

from gui.style_manager import (
    DiagramStyle, CutStyle, LigatureStyle, VertexStyle, 
    PredicateStyle, LabelStyle, LayoutStyle
)


class PeirceAuthenticStyle(DiagramStyle):
    """Historical Peirce-authentic diagram style."""
    
    def __init__(self):
        super().__init__(
            style_id="peirce-authentic@1.0",
            name="Peirce Authentic",
            description="Historical style matching Peirce's original hand-drawn diagrams"
        )
    
    def get_cut_style(self, nesting_level: int = 0) -> CutStyle:
        """Traditional ovals with classical proportions."""
        return CutStyle(
            line_width=1.5,
            color=QColor(20, 20, 20),  # Slightly softer black
            fill_color=None,  # Transparent
            corner_radius=25.0,  # More oval-like
            padding=25.0,  # More generous classical spacing
            nesting_margin=20.0,
            shape_type="oval"
        )
    
    def get_ligature_style(self, context: str = "default") -> LigatureStyle:
        """Flowing curved lines like hand-drawn connections."""
        return LigatureStyle(
            line_width=1.5,
            color=QColor(20, 20, 20),
            line_style=Qt.SolidLine,
            connection_type="curved",
            arrow_style="none",
            routing_algorithm="bezier"
        )
    
    def get_vertex_style(self, vertex_type: str = "generic") -> VertexStyle:
        """Classical dots with serif-style presence."""
        return VertexStyle(
            line_width=2.5,
            color=QColor(20, 20, 20),
            fill_color=QColor(20, 20, 20),  # Solid fill like ink dots
            radius=6.0,  # Slightly smaller, more classical
            shape_type="circle",
            label_offset=18.0
        )
    
    def get_predicate_style(self, relation_name: str = "default") -> PredicateStyle:
        """Classical predicate representation."""
        return PredicateStyle(
            line_width=2.0,
            color=QColor(20, 20, 20),
            length=35.0,  # Slightly shorter, more classical
            shape_type="line"
        )
    
    def get_label_style(self, label_type: str = "default") -> LabelStyle:
        """Classical serif typography."""
        return LabelStyle(
            font_family="Times New Roman",  # Classical serif
            font_size=11,
            font_weight=QFont.Weight.Normal,
            color=QColor(20, 20, 20)
        )
    
    def get_layout_style(self) -> LayoutStyle:
        """Classical proportions with parchment background."""
        return LayoutStyle(
            element_spacing=45.0,  # More spacious classical layout
            diagram_margin=40.0,
            sheet_color=QColor(252, 248, 240),  # Warm parchment color
            grid_visible=False,
            grid_spacing=25.0,
            grid_color=QColor(230, 220, 200)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Export style parameters."""
        base_dict = super().to_dict()
        base_dict.update({
            "cut_style": {
                "line_width": 1.5,
                "color": {"r": 20, "g": 20, "b": 20, "a": 255},
                "corner_radius": 25.0,
                "padding": 25.0,
                "nesting_margin": 20.0,
                "shape_type": "oval"
            },
            "ligature_style": {
                "line_width": 1.5,
                "color": {"r": 20, "g": 20, "b": 20, "a": 255},
                "connection_type": "curved",
                "routing_algorithm": "bezier"
            },
            "vertex_style": {
                "line_width": 2.5,
                "color": {"r": 20, "g": 20, "b": 20, "a": 255},
                "fill_color": {"r": 20, "g": 20, "b": 20, "a": 255},
                "radius": 6.0,
                "shape_type": "circle"
            },
            "layout_style": {
                "element_spacing": 45.0,
                "diagram_margin": 40.0,
                "sheet_color": {"r": 252, "g": 248, "b": 240, "a": 255}
            }
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PeirceAuthenticStyle':
        """Import style from dictionary."""
        return cls()  # Parameters are hardcoded for historical authenticity
