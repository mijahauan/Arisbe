"""
Peirce handwritten style for EGI diagrams.

This style captures the organic, irregular characteristics of Peirce's
actual handwritten existential graphs, emphasizing natural curves,
asymmetry, and hand-drawn aesthetics over geometric precision.
"""

from typing import Dict, Any, List, Tuple
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from gui.style_manager import DiagramStyle, CutStyle, LigatureStyle, VertexStyle, PredicateStyle, LabelStyle, LayoutStyle


class PeirceHandwrittenStyle(DiagramStyle):
    """
    Authentic Peirce handwritten style emphasizing organic, irregular shapes.
    
    Based on analysis of Peirce's actual handwritten existential graphs,
    this style prioritizes natural asymmetry and hand-drawn aesthetics.
    """
    
    def __init__(self):
        super().__init__(
            style_id="peirce-handwritten",
            name="Peirce Handwritten",
            description="Authentic handwritten style based on Peirce's original manuscripts"
        )
    
    def get_cut_style(self, nesting_level: int = 0) -> CutStyle:
        """Organic oval cuts with irregular, wavy boundaries."""
        return CutStyle(
            line_width=1.8,  # Slightly varied thickness
            color=QColor(15, 15, 15),  # Ink-like darkness
            fill_color=None,  # Transparent like handwritten
            corner_radius=20.0,  # Very rounded for oval shape
            padding=15.0,  # Natural spacing
            nesting_margin=12.0,
            shape_type="irregular_oval",  # Custom organic shape
            
            # Organic characteristics
            boundary_irregularity=0.12,  # Natural variation in curves
            corner_asymmetry=0.08,       # Uneven corner rounding
            line_waviness=0.05,          # Subtle hand tremor effect
        )
    
    def get_ligature_style(self, context: str = "default") -> LigatureStyle:
        """Natural curved connections with hand-drawn character."""
        base_style = LigatureStyle(
            line_width=1.6,
            color=QColor(15, 15, 15),
            line_style=Qt.SolidLine,
            connection_type="organic_curve",
            arrow_style="none",
            routing_algorithm="natural_spline",
            
            # Hand-drawn characteristics
            curve_irregularity=0.1,      # Natural curve variation
            endpoint_variation=0.05,     # Slight endpoint positioning variation
            line_smoothness=0.8,         # Slightly rough, not perfect
        )
        
        # Context-specific adjustments
        if context == "reflexive":
            base_style.curve_tension = 1.2
            base_style.loop_size = 18.0
        elif context == "s_curve":
            base_style.curve_complexity = 1.5
            base_style.inflection_variation = 0.15
        elif context == "bridge":
            base_style.bridge_height = 4.0
            base_style.bridge_style = "organic_arch"
        elif context == "gap":
            base_style.gap_size = 6.0
            base_style.gap_style = "natural_break"
            
        return base_style
    
    def get_vertex_style(self, vertex_type: str = "generic") -> VertexStyle:
        """Ink-dot style vertices with slight irregularity."""
        return VertexStyle(
            line_width=0.0,  # Filled dots, no outline
            color=QColor(15, 15, 15),
            fill_color=QColor(15, 15, 15),
            radius=4.5,  # Modest size like ink dots
            shape_type="irregular_circle",
            label_offset=16.0,
            
            # Hand-drawn characteristics
            shape_variation=0.08,        # Slight size/shape variation
            position_jitter=0.5,         # Tiny positioning variation
        )
    
    def get_predicate_style(self, relation_name: str = "default") -> PredicateStyle:
        """Hand-drawn predicate lines with natural variation."""
        return PredicateStyle(
            line_width=1.8,
            color=QColor(15, 15, 15),
            length=32.0,
            shape_type="organic_line",
            
            # Natural variation
            length_variation=0.1,        # Slight length differences
            angle_variation=0.05,        # Minor angle adjustments
            thickness_variation=0.15,    # Natural line weight changes
        )
    
    def get_label_style(self, label_type: str = "default") -> LabelStyle:
        """Handwritten-style text with natural flow."""
        return LabelStyle(
            font_family="Bradley Hand",  # Handwriting-style font
            font_size=11,
            font_weight=QFont.Weight.Normal,
            color=QColor(15, 15, 15),
            
            # Handwritten characteristics
            letter_spacing=0.5,          # Slight spacing variation
            baseline_variation=0.3,      # Natural text flow
            rotation_variation=0.02,     # Slight text angle changes
        )
    
    def get_layout_style(self) -> LayoutStyle:
        """Organic layout with natural asymmetry."""
        return LayoutStyle(
            vertex_spacing=35.0,
            cut_margin=18.0,
            ligature_routing="organic",
            
            # Natural layout characteristics
            position_randomness=2.0,     # Slight position variations
            alignment_tolerance=3.0,     # Less rigid alignment
            symmetry_breaking=0.15,      # Intentional asymmetry
            
            # Organic flow parameters
            natural_clustering=True,
            avoid_perfect_angles=True,
            prefer_curves=True,
        )
    
    def get_bridge_gap_styles(self) -> Dict[str, Any]:
        """Specific styles for bridge and gap notation."""
        return {
            'gap': {
                'size': 6.0,
                'style': 'natural_break',
                'taper': True,
                'irregularity': 0.1,
            },
            'bridge_line': {
                'height': 4.0,
                'width': 8.0,
                'style': 'organic_arch',
                'thickness': 1.4,
            },
            'bridge_wedge': {
                'height': 5.0,
                'width': 6.0,
                'angle': 45.0,
                'style': 'hand_drawn_caret',
            },
            'cross': {
                'size': 4.0,
                'style': 'organic_cross',
                'angle_variation': 0.1,
            }
        }
    
    def get_text_flow_parameters(self) -> Dict[str, Any]:
        """Parameters for natural text flow within cuts."""
        return {
            'follow_boundary': True,
            'margin_variation': 0.2,
            'line_spacing_variation': 0.1,
            'word_spacing_variation': 0.15,
            'natural_justification': True,
            'avoid_geometric_alignment': True,
        }
    
    def supports_feature(self, feature: str) -> bool:
        """Check if this style supports specific rendering features."""
        supported_features = {
            'organic_shapes',
            'irregular_boundaries', 
            'natural_curves',
            'handwritten_aesthetics',
            'asymmetric_layout',
            'bridge_gap_notation',
            'text_flow',
            'natural_variation',
            'ink_style_rendering',
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
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PeirceHandwrittenStyle':
        """Create style instance from dictionary data."""
        style = cls()
        # Override defaults with provided data if needed
        return style
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert style to dictionary for serialization."""
        return {
            'type': 'PeirceHandwrittenStyle',
            'name': self.name,
            'description': self.description,
            'organic_parameters': {
                'boundary_irregularity': 0.12,
                'curve_variation': 0.1,
                'position_randomness': 2.0,
                'asymmetry_factor': 0.15,
            },
            'handwritten_features': {
                'ink_style': True,
                'natural_curves': True,
                'organic_shapes': True,
                'text_flow': True,
            }
        }
    
    def get_rendering_hints(self) -> Dict[str, Any]:
        """Provide hints for the renderer about organic characteristics."""
        return {
            'use_anti_aliasing': True,
            'curve_smoothing': 'natural',
            'line_caps': 'round',
            'line_joins': 'round',
            'text_rendering': 'natural',
            'shape_tessellation': 'organic',
            'avoid_pixel_snapping': True,
        }
