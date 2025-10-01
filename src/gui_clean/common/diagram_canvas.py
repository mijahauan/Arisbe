"""
DiagramCanvas - Core widget for displaying EGI diagrams.

Displays LayoutDTO as SVG using the tested GraphvizSVGRenderer.
All rendering goes through the production-ready pipeline:
    DiagramController → LayoutDTO → GraphvizSVGRenderer → SVG
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import QVBoxLayout, QWidget

# Production-ready imports only
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from definitive_egi_layout_engine import LayoutDTO
from graphviz_svg_renderer import GraphvizSVGRenderer
from egif_generator_dau import generate_egif
from egi_core_dau import RelationalGraphWithCuts


class DiagramCanvas(QWidget):
    """
    Canvas widget for displaying EGI diagrams as SVG.
    
    Uses the tested production pipeline:
    - LayoutDTO provides rendering information
    - GraphvizSVGRenderer generates correct SVG
    - QSvgWidget displays the result
    
    This is a read-only display widget. Subclasses add interaction.
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # SVG renderer (production-ready)
        self._renderer = GraphvizSVGRenderer()
        
        # SVG display widget
        self._svg_widget = QSvgWidget()
        self._svg_widget.setMinimumSize(400, 300)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._svg_widget)
        
        # Current state
        self._current_dto: Optional[LayoutDTO] = None
        self._current_egi: Optional[RelationalGraphWithCuts] = None
    
    def display_dto(self, dto: LayoutDTO, egi: Optional[RelationalGraphWithCuts] = None):
        """
        Display a LayoutDTO as SVG.
        
        Args:
            dto: The layout to display
            egi: Optional EGI for EGIF generation in title
        """
        self._current_dto = dto
        self._current_egi = egi
        
        # Generate EGIF for display (if EGI provided)
        egif = ""
        if egi:
            try:
                egif = generate_egif(egi)
            except Exception as e:
                egif = f"[EGIF generation failed: {e}]"
        
        # Render to SVG using production pipeline
        svg_content = self._renderer.render_to_svg(
            dto,
            title="Existential Graph",
            egif=egif
        )
        
        # Display
        self._svg_widget.load(svg_content.encode('utf-8'))
    
    def clear(self):
        """Clear the canvas."""
        self._current_dto = None
        self._current_egi = None
        self._svg_widget.load(b'<svg></svg>')
    
    def get_current_dto(self) -> Optional[LayoutDTO]:
        """Get the currently displayed LayoutDTO."""
        return self._current_dto
    
    def get_current_egi(self) -> Optional[RelationalGraphWithCuts]:
        """Get the currently displayed EGI."""
        return self._current_egi
