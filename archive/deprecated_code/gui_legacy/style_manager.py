"""
GUI Style Manager for Arisbe

Provides GUI-specific style classes and global style management for diagram rendering.
Integrates with the platform-independent StyleSpecification from style_loader.
"""

from dataclasses import dataclass
from typing import Optional
from style_loader import StyleSpecification, StyleLoader


@dataclass
class DiagramStyle:
    """Complete style specification for diagram rendering"""
    
    # Layout parameters
    element_spacing: float
    cut_padding: float
    sibling_spacing: float
    diagram_margin: float
    text_margin: float
    ligature_clearance: float
    
    # Typography
    font_family: str
    font_size: float
    font_weight: str
    
    # Element sizing
    vertex_radius: float
    predicate_char_width: float
    predicate_height: float
    
    # Visual properties
    vertex_fill_color: str
    background_color: str
    cut_shape: str
    cut_corner_radius: float
    cut_line_width: float
    ligature_line_width: float
    
    # Polarity-based fills
    even_polarity_fill: str
    odd_polarity_fill: str
    
    # Optional features
    alternating_shading_enabled: bool
    arity_numbers_enabled: bool
    variable_labels_enabled: bool
    
    # Transformation support
    double_cut_highlight_enabled: bool
    isomorphic_highlight_enabled: bool
    collapsed_context_enabled: bool
    
    @classmethod
    def from_style_specification(cls, spec: StyleSpecification) -> 'DiagramStyle':
        """Create DiagramStyle from StyleSpecification"""
        return cls(
            # Layout parameters
            element_spacing=spec.element_spacing,
            cut_padding=spec.cut_padding,
            sibling_spacing=spec.sibling_spacing,
            diagram_margin=spec.diagram_margin,
            text_margin=spec.text_margin,
            ligature_clearance=spec.ligature_clearance,
            
            # Typography
            font_family=spec.font_family,
            font_size=spec.font_size,
            font_weight=spec.font_weight,
            
            # Element sizing
            vertex_radius=spec.vertex_radius,
            predicate_char_width=spec.predicate_char_width,
            predicate_height=spec.predicate_height,
            
            # Visual properties
            vertex_fill_color=spec.vertex_fill_color,
            background_color=spec.background_color,
            cut_shape=spec.cut_shape,
            cut_corner_radius=spec.cut_corner_radius,
            cut_line_width=spec.cut_line_width,
            ligature_line_width=spec.ligature_line_width,
            
            # Polarity-based fills
            even_polarity_fill=spec.even_polarity_fill,
            odd_polarity_fill=spec.odd_polarity_fill,
            
            # Optional features
            alternating_shading_enabled=spec.alternating_shading_enabled,
            arity_numbers_enabled=spec.arity_numbers_enabled,
            variable_labels_enabled=spec.variable_labels_enabled,
            
            # Transformation support
            double_cut_highlight_enabled=spec.double_cut_highlight_enabled,
            isomorphic_highlight_enabled=spec.isomorphic_highlight_enabled,
            collapsed_context_enabled=spec.collapsed_context_enabled
        )


@dataclass
class CutStyle:
    """Style specification for cut rendering"""
    shape: str
    corner_radius: float
    line_width: float
    even_polarity_fill: str
    odd_polarity_fill: str


@dataclass  
class LigatureStyle:
    """Style specification for ligature rendering"""
    line_width: float
    clearance: float


@dataclass
class VertexStyle:
    """Style specification for vertex rendering"""
    radius: float
    fill_color: str


class StyleManager:
    """Global style manager for GUI components"""
    
    def __init__(self):
        self._current_style: Optional[DiagramStyle] = None
        self._style_loader = StyleLoader()
    
    def load_style(self, style_name: str) -> DiagramStyle:
        """Load a style by name"""
        spec = self._style_loader.load_style(style_name)
        style = DiagramStyle.from_style_specification(spec)
        self._current_style = style
        return style
    
    def load_default_style(self) -> DiagramStyle:
        """Load the default style"""
        spec = self._style_loader.load_default_style()
        style = DiagramStyle.from_style_specification(spec)
        self._current_style = style
        return style
    
    def get_current_style(self) -> DiagramStyle:
        """Get the current active style"""
        if self._current_style is None:
            self._current_style = self.load_default_style()
        return self._current_style
    
    def set_current_style(self, style: DiagramStyle):
        """Set the current active style"""
        self._current_style = style
    
    def get_cut_style(self) -> CutStyle:
        """Get cut style from current style"""
        style = self.get_current_style()
        return CutStyle(
            shape=style.cut_shape,
            corner_radius=style.cut_corner_radius,
            line_width=style.cut_line_width,
            even_polarity_fill=style.even_polarity_fill,
            odd_polarity_fill=style.odd_polarity_fill
        )
    
    def get_ligature_style(self) -> LigatureStyle:
        """Get ligature style from current style"""
        style = self.get_current_style()
        return LigatureStyle(
            line_width=style.ligature_line_width,
            clearance=style.ligature_clearance
        )
    
    def get_vertex_style(self) -> VertexStyle:
        """Get vertex style from current style"""
        style = self.get_current_style()
        return VertexStyle(
            radius=style.vertex_radius,
            fill_color=style.vertex_fill_color
        )


# Global style manager instance
STYLE_MANAGER = StyleManager()


# Convenience functions
def get_current_style() -> DiagramStyle:
    """Get the current global style"""
    return STYLE_MANAGER.get_current_style()


def set_current_style(style: DiagramStyle):
    """Set the current global style"""
    STYLE_MANAGER.set_current_style(style)


def load_style(style_name: str) -> DiagramStyle:
    """Load and set a style by name"""
    return STYLE_MANAGER.load_style(style_name)


def load_default_style() -> DiagramStyle:
    """Load and set the default style"""
    return STYLE_MANAGER.load_default_style()
