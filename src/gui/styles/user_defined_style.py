"""
User-Defined Style Implementation

Allows users to create custom diagram styles by modifying parameters
from existing base styles or creating entirely new visual approaches.
"""

from typing import Dict, Any, Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont

from gui.style_manager import (
    DiagramStyle, CutStyle, LigatureStyle, VertexStyle, 
    PredicateStyle, LabelStyle, LayoutStyle
)


class UserDefinedStyle(DiagramStyle):
    """User-customizable diagram style."""
    
    def __init__(self, style_id: str, name: str, description: str):
        super().__init__(style_id, name, description)
        
        # Default parameters (can be overridden)
        self._cut_params = {
            "line_width": 2.0,
            "color": QColor(0, 0, 0),
            "corner_radius": 8.0,
            "padding": 20.0,
            "nesting_margin": 15.0,
            "shape_type": "rounded_rectangle"
        }
        
        self._ligature_params = {
            "line_width": 2.0,
            "color": QColor(0, 0, 0),
            "connection_type": "orthogonal",
            "routing_algorithm": "manhattan"
        }
        
        self._vertex_params = {
            "line_width": 2.0,
            "color": QColor(0, 0, 0),
            "fill_color": QColor(255, 255, 255),
            "radius": 8.0,
            "shape_type": "circle",
            "label_offset": 15.0
        }
        
        self._predicate_params = {
            "line_width": 3.0,
            "color": QColor(0, 0, 0),
            "length": 40.0,
            "shape_type": "line"
        }
        
        self._label_params = {
            "font_family": "Arial",
            "font_size": 12,
            "font_weight": QFont.Weight.Normal,
            "color": QColor(0, 0, 0)
        }
        
        self._layout_params = {
            "element_spacing": 40.0,
            "diagram_margin": 30.0,
            "sheet_color": QColor(255, 255, 255),
            "grid_visible": False,
            "grid_spacing": 20.0,
            "grid_color": QColor(240, 240, 240)
        }
    
    def copy_from_style(self, base_style: DiagramStyle):
        """Copy parameters from another style as starting point."""
        try:
            # Copy cut style
            cut_style = base_style.get_cut_style()
            self._cut_params.update({
                "line_width": cut_style.line_width,
                "color": cut_style.color,
                "corner_radius": cut_style.corner_radius,
                "padding": cut_style.padding,
                "nesting_margin": cut_style.nesting_margin,
                "shape_type": cut_style.shape_type
            })
            
            # Copy ligature style
            ligature_style = base_style.get_ligature_style()
            self._ligature_params.update({
                "line_width": ligature_style.line_width,
                "color": ligature_style.color,
                "connection_type": ligature_style.connection_type,
                "routing_algorithm": ligature_style.routing_algorithm
            })
            
            # Copy vertex style
            vertex_style = base_style.get_vertex_style()
            self._vertex_params.update({
                "line_width": vertex_style.line_width,
                "color": vertex_style.color,
                "fill_color": vertex_style.fill_color,
                "radius": vertex_style.radius,
                "shape_type": vertex_style.shape_type,
                "label_offset": vertex_style.label_offset
            })
            
            # Copy layout style
            layout_style = base_style.get_layout_style()
            self._layout_params.update({
                "element_spacing": layout_style.element_spacing,
                "diagram_margin": layout_style.diagram_margin,
                "sheet_color": layout_style.sheet_color,
                "grid_visible": layout_style.grid_visible,
                "grid_spacing": layout_style.grid_spacing,
                "grid_color": layout_style.grid_color
            })
            
        except Exception as e:
            print(f"Warning: Could not copy all parameters from base style: {e}")
    
    def update_cut_params(self, **kwargs):
        """Update cut styling parameters."""
        self._cut_params.update(kwargs)
    
    def update_ligature_params(self, **kwargs):
        """Update ligature styling parameters."""
        self._ligature_params.update(kwargs)
    
    def update_vertex_params(self, **kwargs):
        """Update vertex styling parameters."""
        self._vertex_params.update(kwargs)
    
    def update_predicate_params(self, **kwargs):
        """Update predicate styling parameters."""
        self._predicate_params.update(kwargs)
    
    def update_label_params(self, **kwargs):
        """Update label styling parameters."""
        self._label_params.update(kwargs)
    
    def update_layout_params(self, **kwargs):
        """Update layout styling parameters."""
        self._layout_params.update(kwargs)
    
    def get_cut_style(self, nesting_level: int = 0) -> CutStyle:
        """Get cut style with user parameters."""
        return CutStyle(
            line_width=self._cut_params["line_width"],
            color=self._cut_params["color"],
            fill_color=self._cut_params.get("fill_color"),
            corner_radius=self._cut_params["corner_radius"],
            padding=self._cut_params["padding"],
            nesting_margin=self._cut_params["nesting_margin"],
            shape_type=self._cut_params["shape_type"]
        )
    
    def get_ligature_style(self, context: str = "default") -> LigatureStyle:
        """Get ligature style with user parameters."""
        return LigatureStyle(
            line_width=self._ligature_params["line_width"],
            color=self._ligature_params["color"],
            line_style=self._ligature_params.get("line_style", Qt.SolidLine),
            connection_type=self._ligature_params["connection_type"],
            arrow_style=self._ligature_params.get("arrow_style", "none"),
            routing_algorithm=self._ligature_params["routing_algorithm"]
        )
    
    def get_vertex_style(self, vertex_type: str = "generic") -> VertexStyle:
        """Get vertex style with user parameters."""
        return VertexStyle(
            line_width=self._vertex_params["line_width"],
            color=self._vertex_params["color"],
            fill_color=self._vertex_params["fill_color"],
            radius=self._vertex_params["radius"],
            shape_type=self._vertex_params["shape_type"],
            label_offset=self._vertex_params["label_offset"]
        )
    
    def get_predicate_style(self, relation_name: str = "default") -> PredicateStyle:
        """Get predicate style with user parameters."""
        return PredicateStyle(
            line_width=self._predicate_params["line_width"],
            color=self._predicate_params["color"],
            length=self._predicate_params["length"],
            shape_type=self._predicate_params["shape_type"]
        )
    
    def get_label_style(self, label_type: str = "default") -> LabelStyle:
        """Get label style with user parameters."""
        return LabelStyle(
            font_family=self._label_params["font_family"],
            font_size=self._label_params["font_size"],
            font_weight=self._label_params["font_weight"],
            color=self._label_params["color"]
        )
    
    def get_layout_style(self) -> LayoutStyle:
        """Get layout style with user parameters."""
        return LayoutStyle(
            element_spacing=self._layout_params["element_spacing"],
            diagram_margin=self._layout_params["diagram_margin"],
            sheet_color=self._layout_params["sheet_color"],
            grid_visible=self._layout_params["grid_visible"],
            grid_spacing=self._layout_params["grid_spacing"],
            grid_color=self._layout_params["grid_color"]
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Export style parameters."""
        base_dict = super().to_dict()
        
        def serialize_color(color):
            if isinstance(color, QColor):
                return {"r": color.red(), "g": color.green(), "b": color.blue(), "a": color.alpha()}
            return color
        
        base_dict.update({
            "cut_params": {k: serialize_color(v) if isinstance(v, QColor) else v 
                          for k, v in self._cut_params.items()},
            "ligature_params": {k: serialize_color(v) if isinstance(v, QColor) else v 
                               for k, v in self._ligature_params.items()},
            "vertex_params": {k: serialize_color(v) if isinstance(v, QColor) else v 
                             for k, v in self._vertex_params.items()},
            "predicate_params": {k: serialize_color(v) if isinstance(v, QColor) else v 
                                for k, v in self._predicate_params.items()},
            "label_params": {k: serialize_color(v) if isinstance(v, QColor) else v 
                            for k, v in self._label_params.items()},
            "layout_params": {k: serialize_color(v) if isinstance(v, QColor) else v 
                             for k, v in self._layout_params.items()}
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserDefinedStyle':
        """Import style from dictionary."""
        def deserialize_color(color_data):
            if isinstance(color_data, dict) and "r" in color_data:
                return QColor(color_data["r"], color_data["g"], color_data["b"], color_data.get("a", 255))
            return color_data
        
        style = cls(data["style_id"], data["name"], data["description"])
        
        # Import parameters if present
        if "cut_params" in data:
            style._cut_params = {k: deserialize_color(v) for k, v in data["cut_params"].items()}
        if "ligature_params" in data:
            style._ligature_params = {k: deserialize_color(v) for k, v in data["ligature_params"].items()}
        if "vertex_params" in data:
            style._vertex_params = {k: deserialize_color(v) for k, v in data["vertex_params"].items()}
        if "predicate_params" in data:
            style._predicate_params = {k: deserialize_color(v) for k, v in data["predicate_params"].items()}
        if "label_params" in data:
            style._label_params = {k: deserialize_color(v) for k, v in data["label_params"].items()}
        if "layout_params" in data:
            style._layout_params = {k: deserialize_color(v) for k, v in data["layout_params"].items()}
        
        return style
