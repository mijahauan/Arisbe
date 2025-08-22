"""
Rendering style system for Arisbe EG visualization.

Implements the EGDF → Style Delta → Output architecture where:
- EGDF contains logical spatial primitives from canonical pipeline
- Style classes transform primitives for different visual presentations
- Output renderers (Qt, LaTeX, PNG) consume styled primitives
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Tuple, Optional
from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt


@dataclass
class StyledPrimitive:
    """A spatial primitive with applied visual styling."""
    primitive_type: str  # 'cut', 'ligature', 'predicate', 'vertex'
    geometry: Dict[str, Any]  # Position, bounds, path data
    visual_properties: Dict[str, Any]  # Colors, line widths, fonts, etc.
    interaction_data: Optional[Dict[str, Any]] = None  # For Qt interaction


class RenderingStyle(ABC):
    """Abstract base class for EG rendering styles."""
    
    @abstractmethod
    def transform_cut(self, cut_primitive: Dict[str, Any]) -> StyledPrimitive:
        """Transform a cut primitive with style-specific visual properties."""
        pass
    
    @abstractmethod
    def transform_ligature(self, ligature_primitive: Dict[str, Any]) -> StyledPrimitive:
        """Transform a ligature primitive with style-specific visual properties."""
        pass
    
    @abstractmethod
    def transform_predicate(self, predicate_primitive: Dict[str, Any]) -> StyledPrimitive:
        """Transform a predicate primitive with style-specific visual properties."""
        pass
    
    @abstractmethod
    def transform_vertex(self, vertex_primitive: Dict[str, Any]) -> StyledPrimitive:
        """Transform a vertex primitive with style-specific visual properties."""
        pass
    
    def apply_style(self, egdf_primitives: Dict[str, Dict[str, Any]], egi_reference=None) -> Dict[str, StyledPrimitive]:
        """Apply this style to all EGDF primitives with constraint enforcement."""
        # Apply spatial constraints during styling
        if egi_reference and hasattr(self, 'constraint_system'):
            # Validate and fix spatial constraints
            violations = self.constraint_system.validate_layout(egdf_primitives)
            if violations:
                egdf_primitives = self.constraint_system.apply_constraint_fixes(violations, egdf_primitives)
        
        styled_primitives = {}
        
        for primitive_id, primitive in egdf_primitives.items():
            primitive_type = primitive.get('element_type', 'unknown')
            
            if primitive_type == 'cut':
                styled_primitives[primitive_id] = self.transform_cut(primitive)
            elif primitive_type == 'ligature':
                styled_primitives[primitive_id] = self.transform_ligature(primitive)
            elif primitive_type == 'predicate':
                styled_primitives[primitive_id] = self.transform_predicate(primitive)
            elif primitive_type == 'vertex':
                styled_primitives[primitive_id] = self.transform_vertex(primitive)
        
        return styled_primitives


class DauStyle(RenderingStyle):
    """
    Canonical Dau style - consolidated from all fragments across the codebase.
    
    Implements Dau's formalization of Peircean conventions:
    - Heavy lines of identity (distinguishing from fine cuts)
    - Fine cut boundaries 
    - Prominent vertex spots as identity markers
    - High contrast black-on-white for mathematical precision
    - Geometric, non-ornamental presentation
    
    Consolidates values from:
    - egdf_canvas_renderer.py: DauVisualStyle
    - egdf_parser.py: StyleTheme 
    - canonical_qt_renderer.py: default parameters
    - pyside6_rendering_contracts.py: PySide6RenderingStyle
    """
    
    def __init__(self):
        # LIGATURES (formerly "heavy lines of identity") - discernably thicker than cuts but only just so
        self.ligature_width = 2.0
        
        # CUT BOUNDARIES - fine lines, basis for ligature thickness
        self.cut_line_width = 1.5
        
        # VERTEX SPOTS - discernably wider than ligatures but only just so
        self.vertex_radius = 2.5  # Creates 5.0pt diameter, just wider than 2.0pt ligature
        
        # COLORS - high contrast black-on-white for mathematical precision
        self.ligature_color = QColor(0, 0, 0)       # Pure black
        self.cut_color = QColor(0, 0, 0)            # Pure black  
        self.vertex_color = QColor(0, 0, 0)         # Pure black
        self.text_color = QColor(0, 0, 0)           # Pure black
        self.background_color = QColor(255, 255, 255)  # Pure white
        
        # Initialize spatial constraint system for style application
        from spatial_constraint_system import SpatialConstraintSystem
        self.constraint_system = SpatialConstraintSystem()
        
        # PREDICATE STYLING
        self.predicate_font_family = "Times New Roman"
        self.predicate_font_size = 12
        self.font_family = "Times New Roman"  # Add for compatibility
        self.predicate_boundary_visible = False     # Invisible boundaries
        self.predicate_padding_x = 2.0              # Tight around text
        self.predicate_padding_y = 1.0              # Tight around text
        self.predicate_background_inherit = True    # Same as containing area
        
    def set_egi_reference(self, egi):
        """Set EGI reference for constraint validation during styling."""
        self.constraint_system.set_egi_reference(egi)
        
        # PREDICATE STYLING
        self.predicate_font_family = "Times New Roman"
        self.predicate_font_size = 12
        self.font_family = "Times New Roman"  # Add for compatibility
        self.predicate_boundary_visible = False     # Invisible boundaries
        self.predicate_padding_x = 2.0              # Tight around text
        self.predicate_padding_y = 1.0              # Tight around text
        self.predicate_background_inherit = True    # Same as containing area
        
        # CUT STYLING - rounded corners that look circular around single letters
        self.cut_corner_radius_ratio = 0.8  # Ratio of height/width for roundness calculation
        
        # ANNOTATION DISPLAY SETTINGS
        self.show_predicate_arity = False           # Hidden by default
        self.show_vertex_variables = False          # Hidden by default
        self.show_vertex_names = True               # Shown by default near vertex spots
        
        # LIGATURE BEHAVIOR
        self.ligature_attachment_points = ['north', 'south', 'east', 'west']  # Cardinal points preferred
        self.ligature_style = 'rectilinear'         # Minimal corners
        self.ligature_bridge_crossings = True       # Use bridges when crossing unavoidable
        self.ligature_branch_spots = True           # Allow branch spots to minimize length
        
        # VERTEX POSITIONING
        self.vertex_minimum_distance_from_predicates = True  # Position at minimum distance between connected predicates
    
    def transform_cut(self, cut_primitive: Dict[str, Any]) -> StyledPrimitive:
        return StyledPrimitive(
            primitive_type='cut',
            geometry=cut_primitive.get('bounds', {}),
            visual_properties={
                'line_width': self.cut_line_width,
                'line_color': self.cut_color,
                'fill_color': None,
                'corner_radius': 2.0,
                'line_style': Qt.PenStyle.SolidLine
            }
        )
    
    def transform_ligature(self, ligature_primitive: Dict[str, Any]) -> StyledPrimitive:
        return StyledPrimitive(
            primitive_type='ligature',
            geometry=ligature_primitive.get('path', {}),
            visual_properties={
                'line_width': self.ligature_width,
                'line_color': self.ligature_color,
                'line_style': Qt.PenStyle.SolidLine,
                'end_cap': Qt.PenCapStyle.RoundCap,
                'attachment_points': self.ligature_attachment_points,
                'routing_style': self.ligature_style,
                'bridge_crossings': self.ligature_bridge_crossings,
                'branch_spots': self.ligature_branch_spots
            }
        )
    
    def transform_predicate(self, predicate_primitive: Dict[str, Any]) -> StyledPrimitive:
        return StyledPrimitive(
            primitive_type='predicate',
            geometry=predicate_primitive.get('bounds', {}),
            visual_properties={
                'font_family': self.predicate_font_family,
                'font_size': self.predicate_font_size,
                'text_color': self.text_color,
                'boundary_visible': self.predicate_boundary_visible,
                'background_inherit': self.predicate_background_inherit,
                'padding_x': self.predicate_padding_x,
                'padding_y': self.predicate_padding_y,
                'show_arity': self.show_predicate_arity,
                'attachment_points': self.ligature_attachment_points
            }
        )
    
    def transform_vertex(self, vertex_primitive: Dict[str, Any]) -> StyledPrimitive:
        return StyledPrimitive(
            primitive_type='vertex',
            geometry=vertex_primitive.get('position', {}),
            visual_properties={
                'radius': self.vertex_radius,
                'fill_color': self.vertex_color,
                'border_width': 0,
                'shape': 'circle',
                'show_variables': self.show_vertex_variables,
                'show_names': self.show_vertex_names,
                'minimum_distance_positioning': self.vertex_minimum_distance_from_predicates
            }
        )


class PeirceStyle(RenderingStyle):
    """Classical Peircean style - organic, flowing, hand-drawn aesthetic."""
    
    def __init__(self):
        # Softer, more organic styling
        self.identity_line_width = 3.0
        self.cut_line_width = 1.5
        self.vertex_radius = 3.0
        # hook_line_width removed - no hooks in EGI formalism
        
        # Warmer colors
        self.line_color = QColor(44, 62, 80)     # Dark blue-gray
        self.cut_color = QColor(44, 62, 80)      # Dark blue-gray
        self.vertex_color = QColor(192, 57, 43)  # Warm red
        self.text_color = QColor(44, 62, 80)     # Dark blue-gray
        self.background_color = QColor(253, 253, 250)  # Warm white
        
        # Typography - more classical
        self.font_family = "Times New Roman"
        self.font_size = 12
    
    def transform_cut(self, cut_primitive: Dict[str, Any]) -> StyledPrimitive:
        return StyledPrimitive(
            primitive_type='cut',
            geometry=cut_primitive.get('bounds', {}),
            visual_properties={
                'line_width': self.cut_line_width,
                'line_color': self.cut_color,
                'fill_color': None,
                'corner_radius': 8.0,  # More rounded
                'line_style': Qt.PenStyle.SolidLine
            }
        )
    
    def transform_ligature(self, ligature_primitive: Dict[str, Any]) -> StyledPrimitive:
        return StyledPrimitive(
            primitive_type='ligature',
            geometry=ligature_primitive.get('path', {}),
            visual_properties={
                'line_width': self.identity_line_width,
                'line_color': self.line_color,
                'line_style': Qt.PenStyle.SolidLine,
                'end_cap': Qt.PenCapStyle.RoundCap,
                'curve_style': 'smooth'  # Flowing curves
            }
        )
    
    def transform_predicate(self, predicate_primitive: Dict[str, Any]) -> StyledPrimitive:
        return StyledPrimitive(
            primitive_type='predicate',
            geometry=predicate_primitive.get('bounds', {}),
            visual_properties={
                'font_family': self.font_family,
                'font_size': self.font_size,
                'text_color': self.text_color,
                'background_color': None,
                'padding': (8.0, 6.0),  # More generous padding
                'font_style': 'italic'
            }
        )
    
    def transform_vertex(self, vertex_primitive: Dict[str, Any]) -> StyledPrimitive:
        return StyledPrimitive(
            primitive_type='vertex',
            geometry=vertex_primitive.get('position', {}),
            visual_properties={
                'radius': self.vertex_radius,
                'fill_color': self.vertex_color,
                'border_width': 1,
                'border_color': self.line_color,
                'shape': 'circle'
            }
        )


class ModernStyle(RenderingStyle):
    """Modern minimalist style - clean, subtle, contemporary."""
    
    def __init__(self):
        # Clean, minimal styling
        self.identity_line_width = 2.5
        self.cut_line_width = 1.0
        self.vertex_radius = 2.5
        # hook_line_width removed - no hooks in EGI formalism
        
        # Modern color palette
        self.line_color = QColor(52, 73, 94)     # Modern dark gray
        self.cut_color = QColor(149, 165, 166)   # Light gray
        self.vertex_color = QColor(52, 152, 219) # Modern blue
        self.text_color = QColor(52, 73, 94)     # Modern dark gray
        self.background_color = QColor(248, 249, 250)  # Very light gray
        
        # Typography - modern sans-serif
        self.font_family = "Helvetica"
        self.font_size = 11
    
    def transform_cut(self, cut_primitive: Dict[str, Any]) -> StyledPrimitive:
        return StyledPrimitive(
            primitive_type='cut',
            geometry=cut_primitive.get('bounds', {}),
            visual_properties={
                'line_width': self.cut_line_width,
                'line_color': self.cut_color,
                'fill_color': QColor(255, 255, 255, 128),  # Subtle fill
                'corner_radius': 4.0,
                'line_style': Qt.PenStyle.SolidLine,
                'shadow': True
            }
        )
    
    def transform_ligature(self, ligature_primitive: Dict[str, Any]) -> StyledPrimitive:
        return StyledPrimitive(
            primitive_type='ligature',
            geometry=ligature_primitive.get('path', {}),
            visual_properties={
                'line_width': self.identity_line_width,
                'line_color': self.line_color,
                'line_style': Qt.PenStyle.SolidLine,
                'end_cap': Qt.PenCapStyle.RoundCap,
                'opacity': 0.9
            }
        )
    
    def transform_predicate(self, predicate_primitive: Dict[str, Any]) -> StyledPrimitive:
        return StyledPrimitive(
            primitive_type='predicate',
            geometry=predicate_primitive.get('bounds', {}),
            visual_properties={
                'font_family': self.font_family,
                'font_size': self.font_size,
                'text_color': self.text_color,
                'background_color': None,
                'padding': (5.0, 3.0),
                'font_weight': 'normal'
            }
        )
    
    def transform_vertex(self, vertex_primitive: Dict[str, Any]) -> StyledPrimitive:
        return StyledPrimitive(
            primitive_type='vertex',
            geometry=vertex_primitive.get('position', {}),
            visual_properties={
                'radius': self.vertex_radius,
                'fill_color': self.vertex_color,
                'border_width': 0,
                'shape': 'circle',
                'opacity': 0.8
            }
        )


# Style registry for easy access
AVAILABLE_STYLES = {
    'dau': DauStyle,
    'peirce': PeirceStyle,
    'modern': ModernStyle
}


def get_style(style_name: str) -> RenderingStyle:
    """Get a style instance by name."""
    style_class = AVAILABLE_STYLES.get(style_name.lower())
    if style_class:
        return style_class()
    else:
        # Default to Dau style
        return DauStyle()
