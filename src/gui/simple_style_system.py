"""
Simplified style system for testing without Qt dependencies in dataclasses.
"""

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class CutStyle:
    """Styling parameters for cuts."""
    line_width: float = 2.0
    color: Tuple[int, int, int] = (0, 0, 0)  # RGB tuple
    fill_color: Optional[Tuple[int, int, int]] = None
    corner_radius: float = 8.0
    padding: float = 10.0
    nesting_margin: float = 15.0
    shape_type: str = "rounded_rectangle"


@dataclass
class LigatureStyle:
    """Styling parameters for ligatures (edges)."""
    line_width: float = 1.5
    color: Tuple[int, int, int] = (0, 0, 0)  # RGB tuple
    line_style: str = "solid"  # "solid", "dashed", "dotted"
    connection_type: str = "straight"  # "straight", "curved", "orthogonal"
    arrow_style: str = "none"  # "none", "arrow", "double_arrow"
    routing_algorithm: str = "direct"  # "direct", "orthogonal", "bezier"


@dataclass
class VertexStyle:
    """Styling parameters for vertices."""
    line_width: float = 2.0
    color: Tuple[int, int, int] = (0, 0, 0)  # RGB tuple
    fill_color: Tuple[int, int, int] = (255, 255, 255)  # RGB tuple
    radius: float = 8.0
    shape_type: str = "circle"  # "circle", "square", "diamond"
    label_offset: float = 15.0


@dataclass
class PredicateStyle:
    """Styling parameters for predicates."""
    line_width: float = 2.0
    color: Tuple[int, int, int] = (0, 0, 0)  # RGB tuple
    length: float = 40.0
    shape_type: str = "line"  # "line", "rectangle", "oval"


@dataclass
class LabelStyle:
    """Styling parameters for text labels."""
    font_family: str = "Arial"
    font_size: int = 12
    font_weight: str = "normal"  # "normal", "bold", "light"
    color: Tuple[int, int, int] = (0, 0, 0)  # RGB tuple


@dataclass
class LayoutStyle:
    """Styling parameters for overall layout."""
    element_spacing: float = 40.0
    diagram_margin: float = 30.0
    sheet_color: Tuple[int, int, int] = (255, 255, 255)  # RGB tuple
    grid_visible: bool = False
    grid_spacing: float = 20.0
    grid_color: Tuple[int, int, int] = (240, 240, 240)  # RGB tuple


class SimpleStyle:
    """Simple style container for testing."""
    
    def __init__(self, name: str = "Test Style"):
        self.name = name
        self.cut_style = CutStyle()
        self.ligature_style = LigatureStyle()
        self.vertex_style = VertexStyle()
        self.predicate_style = PredicateStyle()
        self.label_style = LabelStyle()
        self.layout_style = LayoutStyle()
    
    def get_cut_style(self, nesting_level: int = 0):
        """Get cut style for nesting level."""
        return self.cut_style
    
    def get_ligature_style(self, context: str = "default"):
        """Get ligature style for context."""
        return self.ligature_style
    
    def get_vertex_style(self, vertex_type: str = "generic"):
        """Get vertex style for type."""
        return self.vertex_style
    
    def get_predicate_style(self, relation_name: str = "default"):
        """Get predicate style for relation."""
        return self.predicate_style
    
    def get_label_style(self, label_type: str = "default"):
        """Get label style for type."""
        return self.label_style
    
    def get_layout_style(self):
        """Get layout style."""
        return self.layout_style


# Pre-defined styles for testing
DAU_STYLE = SimpleStyle("Dau Compliant")
PEIRCE_STYLE = SimpleStyle("Peirce Authentic")
LATEX_STYLE = SimpleStyle("LaTeX Inspired")
HANDWRITTEN_STYLE = SimpleStyle("Handwritten")

# Customize styles
PEIRCE_STYLE.cut_style.corner_radius = 15.0
PEIRCE_STYLE.vertex_style.radius = 6.0

LATEX_STYLE.ligature_style.line_width = 1.67
LATEX_STYLE.cut_style.padding = 5.0

HANDWRITTEN_STYLE.cut_style.shape_type = "irregular_oval"
HANDWRITTEN_STYLE.ligature_style.connection_type = "organic_curve"


def get_simple_style(style_name: str = "default") -> SimpleStyle:
    """Get a simple style by name."""
    style_map = {
        "default": DAU_STYLE,
        "dau": DAU_STYLE,
        "peirce": PEIRCE_STYLE,
        "latex": LATEX_STYLE,
        "handwritten": HANDWRITTEN_STYLE
    }
    return style_map.get(style_name, DAU_STYLE)
