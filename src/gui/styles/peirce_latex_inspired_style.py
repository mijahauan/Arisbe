"""
Peirce LaTeX-inspired style for EGI diagrams.

This style incorporates insights from the egpeirce.sty LaTeX package
by Jukka Nikulainen, adapting its visual parameters and approaches
for modern GUI rendering while addressing its acknowledged limitations.
"""

from typing import Dict, Any, Tuple
from gui.style_manager import DiagramStyle, CutStyle, LigatureStyle, VertexStyle, PredicateStyle, LabelStyle, LayoutStyle


class PeirceLatexInspiredStyle(DiagramStyle):
    """
    Peirce style inspired by the egpeirce.sty LaTeX package.
    
    Incorporates the visual parameters and rendering approaches from
    the LaTeX package while adapting them for interactive GUI use.
    """
    
    def __init__(self):
        super().__init__(
            style_id="peirce-latex-inspired",
            name="Peirce LaTeX-Inspired", 
            description="Style based on egpeirce.sty LaTeX package parameters"
        )
        
        # Convert LaTeX pt measurements to pixels (assuming 72 DPI)
        # 0.2pt ≈ 0.28px, 1.2pt ≈ 1.67px
        pt_to_px = 1.39  # 100/72 for 100 DPI displays
        
        self.cut_style = CutStyle(
            # Multiple roundness levels like egpeirce.sty
            corner_radius=8.0,  # Equivalent to framearc=1.0
            line_width=0.28 * pt_to_px,  # 0.2pt converted
            color=(0, 0, 0),  # black
            fill_color=(255, 255, 255),  # white default
            
            # Padding equivalent to framesep
            padding=5.0,  # ~0.07 converted to pixels
            nesting_margin=15.0,
            shape_type="rounded_rectangle"
        )
        
        self.ligature_style = LigatureStyle(
            line_width=1.67 * pt_to_px,  # 1.2pt converted
            color=(0, 0, 0),  # black
            line_style="solid",
            connection_type="straight",
            arrow_style="none",
            routing_algorithm="direct"
        )
        
        self.vertex_style = VertexStyle(
            line_width=2.0,
            color=(0, 0, 0),
            fill_color=(255, 255, 255),
            radius=6.0,
            shape_type="circle",
            label_offset=15.0
        )
        
        self.predicate_style = PredicateStyle(
            line_width=2.0,
            color=(0, 0, 0),
            length=40.0,
            shape_type="line"
        )
        
        self.label_style = LabelStyle(
            font_family="Arial",
            font_size=12,
            font_weight="normal",
            color=(0, 0, 0)
        )
        
        self.layout_style = LayoutStyle(
            element_spacing=40.0,
            diagram_margin=30.0,
            sheet_color=(255, 255, 255),
            grid_visible=False,
            grid_spacing=20.0,
            grid_color=(240, 240, 240)
        )
    
    def get_cut_style_for_nesting_level(self, level: int) -> Dict[str, Any]:
        """
        Get cut style parameters for a specific nesting level.
        
        Implements the alternating color scheme from egpeirce.sty
        for colored cuts.
        """
        base_style = self.cut_style.__dict__.copy()
        
        if level > 0:
            # Alternate between colors for nested cuts
            color_index = level % len(self.cut_style.nesting_colors)
            base_style['fill_color'] = self.cut_style.nesting_colors[color_index]
            
            # Slightly adjust border radius for visual distinction
            if level == 1:
                base_style['border_radius'] = self.cut_style.cut_variants['medium']
            elif level == 2:
                base_style['border_radius'] = self.cut_style.cut_variants['slight']
        
        return base_style
    
    def get_ligature_style_for_type(self, ligature_type: str) -> Dict[str, Any]:
        """
        Get ligature style parameters for a specific connection type.
        
        Maps to the various ligature commands from egpeirce.sty.
        """
        base_style = self.ligature_style.__dict__.copy()
        
        # Adjust parameters based on ligature type
        if ligature_type in ['curved_up_right', 'curved_down_right']:
            base_style['curve_tension'] = 0.7
        elif ligature_type in ['reflexive_left', 'reflexive_right']:
            base_style['curve_tension'] = 1.0
        elif ligature_type == 's_shaped':
            base_style['curve_tension'] = 0.8
        
        return base_style
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PeirceLatexInspiredStyle':
        """Create style instance from dictionary data."""
        style = cls()
        # Override defaults with provided data if needed
        return style
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert style to dictionary for serialization."""
        return {
            'type': 'PeirceLatexInspiredStyle',
            'name': self.name,
            'description': self.description,
            'cut_style': self.cut_style.__dict__,
            'ligature_style': self.ligature_style.__dict__,
            'vertex_style': self.vertex_style.__dict__,
            'predicate_style': self.predicate_style.__dict__,
            'label_style': self.label_style.__dict__,
            'layout_style': self.layout_style.__dict__,
        }
    
    def supports_feature(self, feature: str) -> bool:
        """
        Check if this style supports a specific rendering feature.
        """
        supported_features = {
            'nested_cuts',
            'colored_cuts', 
            'curved_ligatures',
            'gap_notation',
            'bridge_notation',
            'debug_numbering',
            'scroll_rendering',
            'multiple_cut_types',
        }
        return feature in supported_features
    
    # Required abstract method implementations
    def get_cut_style(self, nesting_level: int = 0):
        """Get cut styling parameters."""
        return self.cut_style
    
    def get_ligature_style(self, context: str = "default"):
        """Get ligature styling parameters."""
        return self.ligature_style
    
    def get_vertex_style(self, vertex_type: str = "generic"):
        """Get vertex styling parameters."""
        return self.vertex_style
    
    def get_predicate_style(self, relation_name: str = "default"):
        """Get predicate styling parameters."""
        return self.predicate_style
    
    def get_label_style(self, label_type: str = "default"):
        """Get label styling parameters."""
        return self.label_style
    
    def get_layout_style(self):
        """Get layout styling parameters."""
        return self.layout_style
    
    def get_scroll_parameters(self) -> Dict[str, Any]:
        """
        Get parameters for rendering scroll cuts (Peirce's complex cut forms).
        
        Based on the scroll implementation in egpeirce.sty.
        """
        return {
            'curvature': 0.8,
            'tension': 0.5,
            'arc_separation': 10.0,
            'stretch_factor': self.layout_style.scroll_stretch,
            'node_spacing': 5.0,
        }
    
    def get_debug_style(self) -> Dict[str, Any]:
        """
        Get style parameters for debug mode rendering.
        """
        return {
            'show_node_numbers': True,
            'number_color': self.vertex_style.debug_number_color,
            'number_size': self.vertex_style.debug_number_size,
            'number_font': 'monospace',
            'show_boundaries': True,
            'boundary_color': (200, 200, 200),
            'boundary_style': 'dashed',
        }
