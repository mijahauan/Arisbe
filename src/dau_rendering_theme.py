#!/usr/bin/env python3
"""
Dau-Compliant Rendering Theme System

Implements professional visual conventions following Dau's formalism:
- Heavy lines of identity (4.0pt)
- Fine cut boundaries (1.0pt)
- Prominent vertices as identity spots
- Clear predicate typography
- Professional spacing and layout
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple
from enum import Enum

try:
    from PySide6.QtGui import QColor, QFont, QPen, QBrush
    from PySide6.QtCore import Qt
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False


class RenderingQuality(Enum):
    """Rendering quality levels."""
    DRAFT = "draft"          # Fast rendering for interaction
    STANDARD = "standard"    # Normal quality for editing
    PUBLICATION = "publication"  # High quality for export


@dataclass
class DauVisualConventions:
    """Visual conventions following Dau's formalism."""
    
    # Line Widths (in points)
    HEAVY_LINE_WIDTH: float = 4.0      # Heavy lines of identity
    FINE_CUT_WIDTH: float = 1.0        # Fine cut boundaries
    SELECTION_WIDTH: float = 2.0       # Selection highlights
    HOVER_WIDTH: float = 1.5           # Hover feedback
    
    # Vertex Properties - Only slightly larger than heavy line width
    VERTEX_RADIUS: float = 2.5         # Identity spots (slightly larger than 4.0pt heavy line)
    VERTEX_SELECTION_RADIUS: float = 5.0  # Selection feedback
    
    # Typography
    PREDICATE_FONT_SIZE: int = 12      # Clear predicate text
    PREDICATE_FONT_FAMILY: str = "Times"  # Academic serif font
    ARGUMENT_LABEL_FONT_SIZE: int = 10    # Argument numbering
    
    # Spacing and Layout
    SPACING_FACTOR: float = 1.5        # Professional spacing
    MIN_PREDICATE_SPACING: float = 40.0  # Minimum space between predicates
    MIN_CUT_MARGIN: float = 8.0        # Proper margin inside cuts for element clearance
    CUT_BOUNDARY_PADDING: float = 2.0  # Small padding around cut boundaries for visual clarity
    
    # Predicate Attachment Boundaries - Minimal padding to avoid text overlap
    PREDICATE_PADDING_X: float = 3.0   # Minimal horizontal padding around predicate text
    PREDICATE_PADDING_Y: float = 2.0   # Minimal vertical padding around predicate text
    
    # Colors (Academic/Professional Palette)
    IDENTITY_LINE_COLOR: str = "#000000"    # Black heavy lines
    CUT_LINE_COLOR: str = "#000000"         # Black cut boundaries
    PREDICATE_TEXT_COLOR: str = "#000000"   # Black text
    VERTEX_COLOR: str = "#000000"           # Black identity spots
    
    # Selection and Interaction Colors
    SELECTION_COLOR: str = "#0066CC"        # Blue selection
    HOVER_COLOR: str = "#FF6600"            # Orange hover
    ERROR_COLOR: str = "#CC0000"            # Red errors
    WARNING_COLOR: str = "#FF9900"          # Orange warnings
    
    # Context Colors (Practice Mode)
    POSITIVE_CONTEXT_BG: str = "#FFFFFF"    # White (sheet of assertion)
    NEGATIVE_CONTEXT_BG: str = "#F5F5F5"    # Light gray (cut interiors)
    
    # Canvas Properties
    CANVAS_BACKGROUND: str = "#FFFFFF"      # White background
    GRID_COLOR: str = "#E0E0E0"            # Light gray grid
    MARGIN: float = 50.0                   # Canvas margins


@dataclass
class RenderingTheme:
    """Complete rendering theme with quality settings."""
    
    name: str
    conventions: DauVisualConventions
    quality: RenderingQuality
    antialiasing: bool = True
    
    def __post_init__(self):
        """Initialize Qt objects if available."""
        if PYSIDE6_AVAILABLE:
            self._create_qt_objects()
    
    def _create_qt_objects(self):
        """Create Qt objects for efficient rendering."""
        conv = self.conventions
        
        # Pens for different line types
        self.identity_line_pen = QPen(
            QColor(conv.IDENTITY_LINE_COLOR),
            conv.HEAVY_LINE_WIDTH,
            Qt.SolidLine,
            Qt.RoundCap,
            Qt.RoundJoin
        )
        
        self.cut_line_pen = QPen(
            QColor(conv.CUT_LINE_COLOR),
            conv.FINE_CUT_WIDTH,
            Qt.SolidLine,
            Qt.RoundCap,
            Qt.RoundJoin
        )
        
        self.selection_pen = QPen(
            QColor(conv.SELECTION_COLOR),
            conv.SELECTION_WIDTH,
            Qt.DashLine,
            Qt.RoundCap,
            Qt.RoundJoin
        )
        
        self.hover_pen = QPen(
            QColor(conv.HOVER_COLOR),
            conv.HOVER_WIDTH,
            Qt.SolidLine,
            Qt.RoundCap,
            Qt.RoundJoin
        )
        
        # Brushes for fills
        self.vertex_brush = QBrush(QColor(conv.VERTEX_COLOR))
        self.positive_context_brush = QBrush(QColor(conv.POSITIVE_CONTEXT_BG))
        self.negative_context_brush = QBrush(QColor(conv.NEGATIVE_CONTEXT_BG))
        
        # Fonts
        self.predicate_font = QFont(
            conv.PREDICATE_FONT_FAMILY,
            conv.PREDICATE_FONT_SIZE
        )
        self.predicate_font.setStyleHint(QFont.Serif)
        
        self.argument_font = QFont(
            conv.PREDICATE_FONT_FAMILY,
            conv.ARGUMENT_LABEL_FONT_SIZE
        )
        self.argument_font.setStyleHint(QFont.Serif)
    
    def get_pen_for_element(self, element_type: str, is_selected: bool = False, 
                           is_hovered: bool = False) -> 'QPen':
        """Get appropriate pen for element type and state."""
        if not PYSIDE6_AVAILABLE:
            return None
            
        if is_selected:
            return self.selection_pen
        elif is_hovered:
            return self.hover_pen
        elif element_type in ["edge", "identity_line", "vertex"]:
            return self.identity_line_pen
        elif element_type == "cut":
            return self.cut_line_pen
        else:
            return self.identity_line_pen
    
    def get_brush_for_context(self, is_negative_context: bool) -> 'QBrush':
        """Get appropriate brush for context background."""
        if not PYSIDE6_AVAILABLE:
            return None
            
        return self.negative_context_brush if is_negative_context else self.positive_context_brush
    
    def get_font_for_element(self, element_type: str) -> 'QFont':
        """Get appropriate font for element type."""
        if not PYSIDE6_AVAILABLE:
            return None
            
        if element_type == "argument_label":
            return self.argument_font
        else:
            return self.predicate_font


class ThemeManager:
    """Manages rendering themes and quality settings."""
    
    def __init__(self):
        self.themes: Dict[str, RenderingTheme] = {}
        self.current_theme_name: str = "dau_standard"
        self._create_default_themes()
    
    def _create_default_themes(self):
        """Create default rendering themes."""
        
        # Standard Dau theme
        standard_conventions = DauVisualConventions()
        self.themes["dau_standard"] = RenderingTheme(
            name="Dau Standard",
            conventions=standard_conventions,
            quality=RenderingQuality.STANDARD
        )
        
        # High-quality publication theme
        publication_conventions = DauVisualConventions()
        publication_conventions.HEAVY_LINE_WIDTH = 5.0  # Slightly heavier for print
        publication_conventions.PREDICATE_FONT_SIZE = 14  # Larger for readability
        
        self.themes["dau_publication"] = RenderingTheme(
            name="Dau Publication",
            conventions=publication_conventions,
            quality=RenderingQuality.PUBLICATION
        )
        
        # Draft theme for fast interaction
        draft_conventions = DauVisualConventions()
        draft_conventions.HEAVY_LINE_WIDTH = 3.0  # Lighter for speed
        draft_conventions.PREDICATE_FONT_SIZE = 11  # Smaller for speed
        
        self.themes["dau_draft"] = RenderingTheme(
            name="Dau Draft",
            conventions=draft_conventions,
            quality=RenderingQuality.DRAFT,
            antialiasing=False  # Faster rendering
        )
    
    def get_current_theme(self) -> RenderingTheme:
        """Get the currently active theme."""
        return self.themes[self.current_theme_name]
    
    def set_theme(self, theme_name: str) -> bool:
        """Set the active theme."""
        if theme_name in self.themes:
            self.current_theme_name = theme_name
            return True
        return False
    
    def get_available_themes(self) -> Dict[str, str]:
        """Get available themes with their display names."""
        return {name: theme.name for name, theme in self.themes.items()}
    
    def create_custom_theme(self, name: str, conventions: DauVisualConventions,
                           quality: RenderingQuality = RenderingQuality.STANDARD) -> RenderingTheme:
        """Create a custom theme."""
        theme = RenderingTheme(
            name=name,
            conventions=conventions,
            quality=quality
        )
        self.themes[name.lower().replace(" ", "_")] = theme
        return theme


# Global theme manager instance
_theme_manager = None

def get_theme_manager() -> ThemeManager:
    """Get the global theme manager instance."""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager


def get_current_theme() -> RenderingTheme:
    """Get the currently active rendering theme."""
    return get_theme_manager().get_current_theme()


if __name__ == "__main__":
    # Test the theme system
    print("=== Testing Dau Rendering Theme System ===")
    
    theme_manager = get_theme_manager()
    print(f"Available themes: {theme_manager.get_available_themes()}")
    
    current_theme = theme_manager.get_current_theme()
    print(f"Current theme: {current_theme.name}")
    print(f"Heavy line width: {current_theme.conventions.HEAVY_LINE_WIDTH}")
    print(f"Quality: {current_theme.quality.value}")
    
    # Test theme switching
    theme_manager.set_theme("dau_publication")
    pub_theme = theme_manager.get_current_theme()
    print(f"Switched to: {pub_theme.name}")
    print(f"Publication font size: {pub_theme.conventions.PREDICATE_FONT_SIZE}")
