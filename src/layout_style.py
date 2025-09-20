"""
Layout Style System - Visual styling that influences spatial layout computation

This module defines how visual styling affects layout calculations.
Style is not just cosmetic - it directly impacts spatial requirements.
"""

from dataclasses import dataclass
from typing import Dict, Optional
from egi_core_dau import ElementID


@dataclass(frozen=True)
class LayoutStyle:
    """Visual styling that influences layout computation"""
    
    # Typography - affects text bounds and spatial requirements
    font_family: str = "Arial"
    font_size: float = 12.0
    font_weight: str = "normal"
    line_height: float = 1.2
    
    # Element sizing - affects positioning and spacing
    vertex_diameter: float = 20.0              # Vertex visual size
    edge_thickness: float = 2.0                # Ligature line thickness
    cut_border_thickness: float = 2.0          # Cut outline thickness
    
    # Spacing rules - affects layout algorithms
    min_element_separation: float = 30.0       # Minimum space between any elements
    preferred_element_separation: float = 50.0  # Preferred space between elements
    cut_internal_padding: float = 20.0         # Space inside cuts around contents
    text_margin: float = 5.0                   # Space around text labels
    
    # Area distribution rules
    distribute_elements_evenly: bool = True     # Equal spacing within areas
    center_single_elements: bool = True         # Center lone elements in areas
    align_elements_to_grid: bool = False        # Snap to grid positions
    
    # Visual hierarchy - affects layout priorities
    emphasize_focus_elements: bool = True       # Give focused elements more space
    collapse_empty_areas: bool = True           # Minimize empty cut areas
    
    def calculate_text_bounds(self, text: str) -> 'TextBounds':
        """Calculate spatial requirements for text with this style"""
        # Simplified text measurement - in real implementation would use font metrics
        char_width = self.font_size * 0.6  # Approximate character width
        char_height = self.font_size * self.line_height
        
        width = len(text) * char_width + 2 * self.text_margin
        height = char_height + 2 * self.text_margin
        
        return TextBounds(width=width, height=height)
    
    def calculate_vertex_bounds(self, has_label: bool = False, label: str = "") -> 'ElementBounds':
        """Calculate spatial requirements for vertex with this style"""
        vertex_bounds = ElementBounds(
            width=self.vertex_diameter,
            height=self.vertex_diameter
        )
        
        if has_label and label:
            text_bounds = self.calculate_text_bounds(label)
            # Vertex + label requires space for both
            total_width = max(vertex_bounds.width, text_bounds.width)
            total_height = vertex_bounds.height + text_bounds.height + self.text_margin
            return ElementBounds(width=total_width, height=total_height)
        
        return vertex_bounds
    
    def calculate_cut_minimum_size(self, content_bounds: 'ElementBounds') -> 'ElementBounds':
        """Calculate minimum cut size to contain content with this style"""
        padding = self.cut_internal_padding
        border = self.cut_border_thickness
        
        return ElementBounds(
            width=content_bounds.width + 2 * (padding + border),
            height=content_bounds.height + 2 * (padding + border)
        )


@dataclass(frozen=True)
class TextBounds:
    """Spatial requirements for text"""
    width: float
    height: float


@dataclass(frozen=True)
class ElementBounds:
    """Spatial requirements for an element"""
    width: float
    height: float


@dataclass(frozen=True)
class StyleConfiguration:
    """Complete styling configuration for layout"""
    default_style: LayoutStyle
    element_styles: Dict[ElementID, LayoutStyle]  # Per-element style overrides
    
    def get_style_for_element(self, element_id: ElementID) -> LayoutStyle:
        """Get effective style for specific element"""
        return self.element_styles.get(element_id, self.default_style)


# Predefined style themes
CLASSIC_STYLE = LayoutStyle(
    font_family="Times New Roman",
    font_size=14.0,
    vertex_diameter=25.0,
    preferred_element_separation=60.0
)

MODERN_STYLE = LayoutStyle(
    font_family="Helvetica",
    font_size=12.0,
    vertex_diameter=18.0,
    preferred_element_separation=45.0,
    cut_border_thickness=1.5
)

COMPACT_STYLE = LayoutStyle(
    font_family="Arial",
    font_size=10.0,
    vertex_diameter=15.0,
    preferred_element_separation=30.0,
    cut_internal_padding=15.0
)
