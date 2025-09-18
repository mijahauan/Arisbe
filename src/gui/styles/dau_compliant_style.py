"""
Dau-Compliant Style Implementation

Based on authentic visual examples from Dau's treatise.
Implements mathematical precision with clean, formal appearance.
"""

from typing import Dict, Any
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont

from gui.style_manager import (
    DiagramStyle, CutStyle, LigatureStyle, VertexStyle, 
    PredicateStyle, LabelStyle, LayoutStyle
)


class DauCompliantStyle(DiagramStyle):
    """Dau-compliant diagram style based on authentic visual examples."""
    
    def __init__(self):
        super().__init__(
            style_id="dau-compliant@1.0",
            name="Dau Compliant",
            description="Authentic style based on Dau's treatise examples"
        )
    
    def get_cut_style(self, nesting_level: int = 0) -> CutStyle:
        """Rounded rectangles with generous padding."""
        return CutStyle(
            line_width=2.0,
            color=QColor(0, 0, 0),  # Pure black
            fill_color=None,  # Transparent
            corner_radius=8.0,
            padding=20.0,
            nesting_margin=15.0,
            shape_type="rounded_rectangle"
        )
    
    def get_ligature_style(self, context: str = "default") -> LigatureStyle:
        """Clean straight lines with orthogonal routing."""
        return LigatureStyle(
            line_width=2.0,
            color=QColor(0, 0, 0),  # Pure black
            line_style=Qt.SolidLine,
            connection_type="orthogonal",
            arrow_style="none",
            routing_algorithm="manhattan"
        )
    
    def get_vertex_style(self, vertex_type: str = "generic") -> VertexStyle:
        """Simple black circles with white fill."""
        return VertexStyle(
            line_width=2.0,
            color=QColor(0, 0, 0),  # Pure black outline
            fill_color=QColor(255, 255, 255),  # White fill
            radius=8.0,
            shape_type="circle",
            label_offset=15.0
        )
    
    def get_predicate_style(self, relation_name: str = "default") -> PredicateStyle:
        """Horizontal lines for predicates."""
        return PredicateStyle(
            line_width=3.0,
            color=QColor(0, 0, 0),  # Pure black
            length=40.0,
            shape_type="line"
        )
    
    def get_label_style(self, label_type: str = "default") -> LabelStyle:
        """Clean sans-serif labels."""
        return LabelStyle(
            font_family="Arial",
            font_size=12,
            font_weight=QFont.Weight.Normal,
            color=(0, 0, 0)  # Pure black
        )
    
    def get_layout_style(self) -> LayoutStyle:
        """Generous whitespace and clean layout."""
        return LayoutStyle(
            element_spacing=40.0,
            diagram_margin=30.0,
            sheet_color=QColor(255, 255, 255),  # Pure white
            grid_visible=False,
            grid_spacing=20.0,
            grid_color=QColor(240, 240, 240)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Export style parameters."""
        base_dict = super().to_dict()
        base_dict.update({
            "cut_style": {
                "line_width": 2.0,
                "color": {"r": 0, "g": 0, "b": 0, "a": 255},
                "corner_radius": 8.0,
                "padding": 20.0,
                "nesting_margin": 15.0,
                "shape_type": "rounded_rectangle"
            },
            "ligature_style": {
                "line_width": 2.0,
                "color": {"r": 0, "g": 0, "b": 0, "a": 255},
                "connection_type": "orthogonal",
                "routing_algorithm": "manhattan"
            },
            "vertex_style": {
                "line_width": 2.0,
                "color": {"r": 0, "g": 0, "b": 0, "a": 255},
                "fill_color": {"r": 255, "g": 255, "b": 255, "a": 255},
                "radius": 8.0,
                "shape_type": "circle"
            },
            "layout_style": {
                "element_spacing": 40.0,
                "diagram_margin": 30.0,
                "sheet_color": {"r": 255, "g": 255, "b": 255, "a": 255}
            }
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DauCompliantStyle':
        """Import style from dictionary."""
        return cls()  # Parameters are hardcoded for authentic Dau compliance
