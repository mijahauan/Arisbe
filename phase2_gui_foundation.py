#!/usr/bin/env python3
"""
Phase 2 GUI Foundation - Working EGI Rendering for Parallel Development

This creates a functioning GUI that renders EGI diagrams, providing the foundation
for Phase 2 selection overlays and context-sensitive actions development.

Uses the completed Phase 1d pipeline: EGIF → EGI → Layout → Visual Rendering
"""

import sys
import os
from typing import Dict, List, Optional, Tuple, Set
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Phase 1d Foundation - Complete pipeline
from src.egif_parser_dau import EGIFParser
from src.egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut
from src.graphviz_layout_engine_v2 import GraphvizLayoutEngine
from src.layout_engine_clean import SpatialPrimitive, LayoutResult
from src.egi_diagram_controller import EGIDiagramController
from src.corpus_loader import CorpusLoader
from src.mode_aware_selection import ModeAwareSelectionSystem, Mode, ActionType, SelectionType
from src.annotation_system import (
    AnnotationManager, AnnotationType, AnnotationPrimitive,
    create_arity_numbering_layer, create_argument_labels_layer
)

# GUI Components
try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, 
        QHBoxLayout, QPushButton, QTextEdit, QLabel, 
        QSplitter, QFrame, QComboBox, QCheckBox, QGroupBox, QStatusBar
    )
    from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath
    from PySide6.QtCore import Qt, QPointF, QRectF, QTimer
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False
    print("PySide6 not available - install with: pip install PySide6")

class EGDiagramWidget(QWidget):
    """Widget for rendering EG diagrams with interaction support."""
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(600, 400)
        self.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        
        # Initialize with a simple example
        self.egi = self.create_example_egi()
        self.layout_engine = GraphvizLayoutEngine()
        self.spatial_primitives = []
        self.selection_system = ModeAwareSelectionSystem(Mode.WARMUP)
        self.annotation_manager = AnnotationManager()
        
        # Initialize EGI-diagram controller for proper correspondence
        self.diagram_controller = EGIDiagramController(self.egi)
        
        # Annotation system
        self.annotation_primitives: List[AnnotationPrimitive] = []
        self.show_annotations = False
        
        # Initialize default annotation layers
        self._setup_default_annotations()
        
        # Mode-aware selection system for Phase 2
        self.current_mode = Mode.WARMUP
        
        # Legacy compatibility (will be removed)
        self.selected_elements: Set[str] = set()
        self.hover_element: Optional[str] = None
        
        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)
        
    def create_example_egi(self) -> RelationalGraphWithCuts:
        """Create a simple example EGI for testing"""
        from src.egi_core_dau import create_empty_graph, create_vertex, create_edge
        from frozendict import frozendict
        
        # Create simple example: (Human "Socrates")
        egi = create_empty_graph()
        
        # Create vertex for Socrates
        socrates = create_vertex(label="Socrates", is_generic=False)
        
        # Create edge for Human predicate
        human_edge = create_edge()
        
        # Build the EGI using proper constructor
        egi = RelationalGraphWithCuts(
            V=frozenset([socrates]),
            E=frozenset([human_edge]),
            nu=frozendict({human_edge.id: (socrates.id,)}),
            sheet=egi.sheet,
            Cut=frozenset(),
            area=frozendict({egi.sheet: frozenset([socrates.id, human_edge.id])}),
            rel=frozendict({human_edge.id: "Human"})
        )
        
        return egi
    
    def _setup_default_annotations(self):
        """Initialize default annotation layers."""
        # Add arity numbering layer (disabled by default)
        arity_layer = create_arity_numbering_layer(enabled=False)
        self.annotation_manager.add_layer(arity_layer)
        
        # Add argument labels layer (disabled by default)
        labels_layer = create_argument_labels_layer(enabled=False)
        self.annotation_manager.add_layer(labels_layer)
    
    def toggle_annotations(self, show: bool):
        """Toggle annotation display on/off."""
        self.show_annotations = show
        self._update_annotations()
        self.update()  # Trigger repaint
    
    def toggle_annotation_type(self, annotation_type: AnnotationType, enabled: bool):
        """Enable/disable a specific annotation type."""
        self.annotation_manager.toggle_annotation_type(annotation_type, enabled)
        if self.show_annotations:
            self._update_annotations()
            self.update()  # Trigger repaint
    
    def _update_annotations(self):
        """Update annotation primitives based on current diagram and settings."""
        if self.egi and self.layout_result and self.show_annotations:
            self.annotation_primitives = self.annotation_manager.generate_annotations(
                self.layout_result, self.egi
            )
        else:
            self.annotation_primitives = []
        
    def set_diagram(self, egi: RelationalGraphWithCuts, spatial_primitives: List[SpatialPrimitive]):
        """Set the diagram to render."""
        self.egi = egi
        self.spatial_primitives = spatial_primitives
        
        # Create a simple layout result for annotation system
        # TODO: This should come from the actual layout engine
        self.layout_result = type('LayoutResult', (), {
            'primitives': {p.element_id: p for p in spatial_primitives}
        })()
        
        # Update selection system with new graph
        self.selection_system.set_graph(egi)
        
        # Update annotations if they're enabled
        self._update_annotations()
        
        # Clear selections (both legacy and new system)
        self.selected_elements.clear()
        self.selection_system.clear_selection()
        self.hover_element = None
        self.update()
        
    def clear_diagram(self):
        """Clear the current diagram."""
        self.egi = None
        self.spatial_primitives.clear()
        self.annotation_primitives.clear()
        self.selected_elements.clear()
        self.selection_system.clear_selection()
        self.hover_element = None
        self.update()
    
    def switch_mode(self, new_mode: Mode):
        """Switch between Warmup and Practice modes."""
        if new_mode != self.current_mode:
            self.current_mode = new_mode
            self.selection_system.switch_mode(new_mode)
            
            # Clear legacy selection state
            self.selected_elements.clear()
            self.hover_element = None
            
            # Trigger repaint to update visual indicators
            self.update()
            
            print(f"Switched to {new_mode.value} mode")
    
    def get_current_mode(self) -> Mode:
        """Get the current interaction mode."""
        return self.current_mode
    
    def get_available_actions(self) -> Set[ActionType]:
        """Get available actions for current selection."""
        return self.selection_system.get_available_actions()
        
    def paintEvent(self, event):
        """Render the EG diagram using Dau's conventions."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Clear background
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        
        if not self.spatial_primitives:
            return
        
        # Render context backgrounds for Practice mode (Peircean convention)
        if self.current_mode == Mode.PRACTICE:
            self._render_context_backgrounds(painter)
        
        # Render all spatial primitives
        for primitive in self.spatial_primitives:
            self._render_primitive(painter, primitive)
            
        # Render annotations if enabled
        if self.show_annotations:
            self._render_annotations(painter)
            
        # Render mode-aware selection overlays
        self._render_selection_overlays(painter)
    
    def _render_context_backgrounds(self, painter: QPainter):
        """Render context backgrounds using Peircean convention (Practice mode only)."""
        if not self.egi:
            return
        
        # Render cut interiors with light gray background (negative contexts)
        for primitive in self.spatial_primitives:
            if primitive.element_type == "cut":
                cut_id = primitive.element_id
                
                # Check if this cut represents a negative context
                if self.egi and cut_id in {c.id for c in self.egi.Cut}:
                    try:
                        is_negative = self.egi.is_negative_context(cut_id)
                        if is_negative:
                            # Light gray background for negative contexts
                            x1, y1, x2, y2 = primitive.bounds
                            painter.setPen(Qt.NoPen)
                            painter.setBrush(QBrush(QColor(245, 245, 245)))  # Light gray
                            
                            # Draw filled rectangle for cut interior
                            margin = 5  # Small margin inside cut boundary
                            painter.drawRect(QRectF(x1 + margin, y1 + margin, 
                                                  x2 - x1 - 2*margin, y2 - y1 - 2*margin))
                    except Exception as e:
                        # Skip context polarity check if it fails
                        pass
            
    def _render_primitive(self, painter: QPainter, primitive: SpatialPrimitive):
        """Render a single spatial primitive following Dau's conventions."""
        element_id = primitive.element_id
        element_type = primitive.element_type
        position = primitive.position
        bounds = primitive.bounds
        
        # Check if element is selected or hovered
        is_selected = element_id in self.selected_elements
        is_hovered = element_id == self.hover_element
        
        if element_type == "vertex":
            self._render_vertex(painter, element_id, position, is_selected, is_hovered)
        elif element_type == "predicate":
            self._render_edge(painter, element_id, position, bounds, is_selected, is_hovered)
        elif element_type == "edge":
            self._render_identity_line(painter, element_id, position, bounds, is_selected, is_hovered)
        elif element_type == "cut":
            self._render_cut(painter, element_id, bounds, is_selected, is_hovered)
            
    def _render_vertex(self, painter: QPainter, element_id: str, position: Tuple[float, float], 
                      is_selected: bool, is_hovered: bool):
        """Render vertex as standalone Line of Identity (heavy line segment) per Dau's formalism.
        
        According to Dau's Transformation Rule 6 (Isolated Vertex), vertices can exist
        independently of predicates and should be rendered as heavy line segments
        representing assertions of existence.
        """
        x, y = position
        
        # Get vertex information from EGI
        vertex = None
        if self.egi:
            vertex = next((v for v in self.egi.V if v.id == element_id), None)
        
        # Determine line properties based on vertex type and state
        color = QColor(0, 0, 0) if not is_selected else QColor(0, 100, 200)
        line_width = 4.0 if not is_hovered else 5.0  # Heavy line per Dau's convention
        
        # Calculate line segment dimensions
        # Standalone LoI should be visible but not too long
        line_length = 30  # Standard length for standalone LoI
        
        # Check if this vertex is connected to predicates via nu mappings
        has_predicate_connections = False
        if self.egi:
            for edge_id, vertex_sequence in self.egi.nu.items():
                if element_id in vertex_sequence:
                    has_predicate_connections = True
                    break
        
        # ARCHITECTURAL CORRECTION: Use ligature-aware rendering
        # Check if this vertex is part of a ligature
        ligature_id = self.diagram_controller.get_ligature_for_vertex(element_id)
        
        if ligature_id:
            # This vertex is part of a ligature - render as part of connected identity lines
            ligature = self.diagram_controller.ligatures[ligature_id]
            
            # Draw heavy lines to connected predicates
            painter.setPen(QPen(color, line_width, Qt.SolidLine, Qt.RoundCap))
            
            for predicate_id, hook_position in ligature.connected_predicates.items():
                # Find predicate position
                predicate_primitive = next((p for p in self.spatial_primitives 
                                          if p.element_id == predicate_id), None)
                if predicate_primitive:
                    px, py = predicate_primitive.position
                    
                    # Calculate hook point on predicate periphery
                    # For now, use center - will be refined for proper hook positioning
                    painter.drawLine(QPointF(x, y), QPointF(px, py))
            
            # Draw identity spot at vertex
            spot_radius = 3.0
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPointF(x, y), spot_radius, spot_radius)
            
        else:
            # Standalone vertex - render as isolated identity spot
            spot_radius = 4.0 if not is_hovered else 5.0
            painter.setPen(QPen(color, 2))
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPointF(x, y), spot_radius, spot_radius)
        
        # Render constant name if it exists (for both connected and standalone vertices)
        if vertex and vertex.label and not vertex.is_generic:
            painter.setPen(QPen(color, 1))
            painter.setFont(QFont("Times", 10))
            text_rect = painter.fontMetrics().boundingRect(vertex.label)
            text_x = x - text_rect.width() / 2
            
            if has_predicate_connections:
                # For connected vertices, place text below the spot
                text_y = y + 4.0 + text_rect.height() + 2
            else:
                # For standalone LoI, place text below the line
                text_y = y + line_width/2 + text_rect.height() + 2
            
            painter.drawText(QPointF(text_x, text_y), vertex.label)
        
    def _render_edge(self, painter: QPainter, element_id: str, position: Tuple[float, float],
                    bounds: Tuple[float, float, float, float], is_selected: bool, is_hovered: bool):
        """Render edge as predicate following Dau's conventions."""
        if not self.egi:
            return
            
        x, y = position
        x1, y1, x2, y2 = bounds
        
        # Get relation name
        relation_name = self.egi.rel.get(element_id, f"R{element_id[:4]}")
        
        # Predicate text rendering
        color = QColor(0, 0, 0) if not is_selected else QColor(0, 100, 200)
        painter.setFont(QFont("Times", 11))
        text_rect = painter.fontMetrics().boundingRect(relation_name)
        
        # Minimal padding - ONLY to prevent cuts from running through text
        text_padding = 2  # Minimal padding for cut avoidance only
        
        # Draw predicate text (no decorative background)
        painter.setPen(QPen(color, 1))
        painter.setBrush(QBrush(Qt.NoBrush))
        text_x = x - text_rect.width() / 2
        text_y = y + text_rect.height() / 4  # Adjust for baseline
        painter.drawText(QPointF(text_x, text_y), relation_name)
        
        # Draw hooks at predicate boundary (where LoI can attach)
        # ARCHITECTURAL CORRECTION: Predicates only have hooks, NOT heavy lines
        # Heavy lines (LoI) are independent and attach TO predicates via these hooks
        if element_id in self.egi.nu:
            vertex_sequence = self.egi.nu[element_id]
            for i, vertex_id in enumerate(vertex_sequence):
                # Find vertex position to determine hook direction
                vertex_primitive = next((p for p in self.spatial_primitives 
                                       if p.element_id == vertex_id), None)
                if vertex_primitive:
                    vx, vy = vertex_primitive.position
                    
                    # Calculate hook position on predicate boundary
                    pred_center_x, pred_center_y = x, y
                    dx = vx - pred_center_x
                    dy = vy - pred_center_y
                    distance = (dx*dx + dy*dy)**0.5
                    
                    if distance > 0:
                        # Normalize direction
                        dx_norm = dx / distance
                        dy_norm = dy / distance
                        
                        # Find hook position on predicate text boundary
                        text_half_width = text_rect.width() / 2 + text_padding
                        text_half_height = text_rect.height() / 2 + text_padding
                        
                        # Calculate hook position
                        if abs(dx_norm) > abs(dy_norm):
                            hook_x = pred_center_x + (text_half_width if dx_norm > 0 else -text_half_width)
                            hook_y = pred_center_y + dy_norm * text_half_width / abs(dx_norm)
                        else:
                            hook_x = pred_center_x + dx_norm * text_half_height / abs(dy_norm)
                            hook_y = pred_center_y + (text_half_height if dy_norm > 0 else -text_half_height)
                        
                        # Draw small hook indicator (NOT a heavy line)
                        hook_size = 3
                        hook_color = QColor(0, 0, 0) if not is_selected else QColor(0, 100, 200)
                        painter.setPen(QPen(hook_color, 2))
                        painter.setBrush(QBrush(hook_color))
                        painter.drawEllipse(QPointF(hook_x, hook_y), hook_size, hook_size)
                    
    def _render_identity_line(self, painter: QPainter, element_id: str, position: Tuple[float, float],
                             bounds: Tuple[float, float, float, float], is_selected: bool, is_hovered: bool):
        """Render heavy identity line connecting vertices to predicates (Dau's convention).
        
        NOTE: Currently disabled to prevent duplicate line rendering.
        Heavy identity lines are drawn by _render_edge() method when rendering predicates.
        """
        # DISABLED: Lines are already drawn by _render_edge() method
        # This prevents the double-line rendering issue
        return
        painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
                    
    def _render_cut(self, painter: QPainter, element_id: str, 
                   bounds: Tuple[float, float, float, float], is_selected: bool, is_hovered: bool):
        """Render cut as fine-drawn closed curve (Dau's convention)."""
        x1, y1, x2, y2 = bounds
        
        # Fine cut boundary
        color = QColor(0, 0, 0) if not is_selected else QColor(0, 100, 200)
        line_width = 1.0 if not is_hovered else 1.5
        painter.setPen(QPen(color, line_width))
        painter.setBrush(QBrush(Qt.NoBrush))
        
        # Draw as oval (fine-drawn closed curve)
        painter.drawEllipse(QRectF(x1, y1, x2 - x1, y2 - y1))
    
    def _render_annotations(self, painter: QPainter):
        """Render annotation overlays on top of the base diagram."""
        for annotation in self.annotation_primitives:
            self._render_annotation_primitive(painter, annotation)
    
    def _render_annotation_primitive(self, painter: QPainter, annotation: AnnotationPrimitive):
        """Render a single annotation primitive."""
        x, y = annotation.position
        content = annotation.content
        style = annotation.style
        
        # Set up annotation styling
        font_size = style.get('font_size', 10)
        color = QColor(style.get('color', 'blue'))
        background_color = QColor(style.get('background', 'white'))
        show_border = style.get('border', True)
        
        # Set font
        font = QFont("Arial", font_size)
        painter.setFont(font)
        
        # Calculate text dimensions
        text_rect = painter.fontMetrics().boundingRect(content)
        padding = 2
        
        # Background rectangle
        bg_rect = QRectF(
            x - text_rect.width()/2 - padding,
            y - text_rect.height()/2 - padding,
            text_rect.width() + 2*padding,
            text_rect.height() + 2*padding
        )
        
        # Draw background
        if show_border:
            painter.setPen(QPen(color, 1))
        else:
            painter.setPen(QPen(Qt.NoPen))
        painter.setBrush(QBrush(background_color))
        painter.drawRoundedRect(bg_rect, 2, 2)
        
        # Draw text
        painter.setPen(QPen(color, 1))
        painter.setBrush(QBrush(Qt.NoBrush))
        text_x = x - text_rect.width()/2
        text_y = y + text_rect.height()/4  # Adjust for baseline
        painter.drawText(QPointF(text_x, text_y), content)
        
    def _render_selection_overlays(self, painter: QPainter):
        """Render mode-aware selection overlays and hover effects."""
        # Render hover effect first (underneath selection)
        if self.hover_element and self.hover_element not in self.selected_elements:
            hover_primitive = next((p for p in self.spatial_primitives 
                                  if p.element_id == self.hover_element), None)
            if hover_primitive:
                # Light gray hover effect
                hover_color = QColor(128, 128, 128, 30)
                hover_border = QColor(128, 128, 128, 100)
                
                painter.setPen(QPen(hover_border, 1, Qt.DashLine))
                painter.setBrush(QBrush(hover_color))
                
                x1, y1, x2, y2 = hover_primitive.bounds
                padding = 2
                painter.drawRect(QRectF(x1 - padding, y1 - padding, 
                                      x2 - x1 + 2*padding, y2 - y1 + 2*padding))
        
        # Render selection overlays
        if not self.selected_elements:
            return
        
        # Mode-aware selection colors
        if self.current_mode == Mode.WARMUP:
            # Blue highlights for compositional selections
            selection_color = QColor(0, 122, 255, 80)  # Blue with transparency
            border_color = QColor(0, 122, 255, 200)
        else:  # Practice mode
            # Green for valid transformations
            selection_color = QColor(40, 167, 69, 80)  # Green with transparency
            border_color = QColor(40, 167, 69, 200)
        
        painter.setPen(QPen(border_color, 3, Qt.SolidLine))
        painter.setBrush(QBrush(selection_color))
        
        for element_id in self.selected_elements:
            primitive = next((p for p in self.spatial_primitives 
                            if p.element_id == element_id), None)
            if primitive:
                x1, y1, x2, y2 = primitive.bounds
                element_type = primitive.element_type
                
                if element_type == "vertex":
                    # Enhanced selection for vertices (supports both spots and LoI line segments)
                    center_x = (x1 + x2) / 2
                    center_y = (y1 + y2) / 2
                    
                    # Check if this vertex has predicate connections (determines rendering type)
                    has_predicate_connections = False
                    if self.egi:
                        for edge_id, vertex_sequence in self.egi.nu.items():
                            if element_id in vertex_sequence:
                                has_predicate_connections = True
                                break
                    
                    if has_predicate_connections:
                        # Connected vertex (rendered as spot): circular selection
                        radius = max(8, (x2 - x1) / 2 + 4)
                        painter.drawEllipse(QPointF(center_x, center_y), radius, radius)
                    else:
                        # Standalone LoI (rendered as line segment): line-based selection
                        line_length = 30  # Must match rendering logic
                        line_start_x = center_x - line_length / 2
                        line_end_x = center_x + line_length / 2
                        
                        # Draw selection overlay around the line segment
                        padding = 6
                        painter.drawRect(QRectF(line_start_x - padding, center_y - padding, 
                                              line_length + 2*padding, 2*padding))
                    
                elif element_type == "cut":
                    # Thick border highlight for cuts
                    painter.setPen(QPen(border_color, 4, Qt.SolidLine))
                    painter.setBrush(Qt.NoBrush)  # No fill for cuts
                    padding = 2
                    painter.drawRect(QRectF(x1 - padding, y1 - padding, 
                                          x2 - x1 + 2*padding, y2 - y1 + 2*padding))
                    painter.setBrush(QBrush(selection_color))  # Restore brush
                    
                else:
                    # Rectangular selection for predicates and other elements
                    padding = 4
                    painter.drawRect(QRectF(x1 - padding, y1 - padding, 
                                          x2 - x1 + 2*padding, y2 - y1 + 2*padding))
                
    def mousePressEvent(self, event):
        """Handle mouse clicks for mode-aware selection."""
        if event.button() == Qt.LeftButton:
            # Find element at click position
            clicked_element = self._find_element_at_position(event.position().x(), event.position().y())
            
            if clicked_element:
                # Use mode-aware selection system
                multi_select = bool(event.modifiers() & Qt.ControlModifier)
                result = self.selection_system.select_element(clicked_element, multi_select)
                
                # Update legacy selection state for compatibility
                self.selected_elements = self.selection_system.selection_state.selected_elements.copy()
                
                # Print available actions for debugging
                available_actions = self.get_available_actions()
                print(f"✓ Selected {clicked_element} in {self.current_mode.value} mode")
                print(f"  Available actions: {[action.value for action in available_actions]}")
                
                if not result.is_valid:
                    print(f"⚠ Selection warning: {result.error_message}")
                    
            else:
                # Click on empty area - clear selection
                if self.selected_elements:
                    print(f"✓ Cleared selection in {self.current_mode.value} mode")
                self.selection_system.clear_selection()
                self.selected_elements.clear()
                
            # Update visual display and notify parent
            self.update()
            
            # Notify parent widget to update selection info
            parent = self.parent()
            if parent and hasattr(parent, 'update_selection_info'):
                parent.update_selection_info()
            
    def mouseMoveEvent(self, event):
        """Handle mouse movement for hover effects."""
        hover_element = self._find_element_at_position(event.position().x(), event.position().y())
        
        if hover_element != self.hover_element:
            self.hover_element = hover_element
            self.update()
            
    def _find_element_at_position(self, x: float, y: float) -> Optional[str]:
        """Find element at given position with robust hit-testing."""
        # Check each primitive with appropriate hit-testing for element type
        for primitive in self.spatial_primitives:
            element_type = primitive.element_type
            x1, y1, x2, y2 = primitive.bounds
            
            if element_type == "vertex":
                # Enhanced hit-testing for vertices (supports both spots and LoI line segments)
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                
                # Check if this vertex has predicate connections (determines rendering type)
                has_predicate_connections = False
                if self.egi:
                    for edge_id, vertex_sequence in self.egi.nu.items():
                        if primitive.element_id in vertex_sequence:
                            has_predicate_connections = True
                            break
                
                if has_predicate_connections:
                    # Connected vertex (rendered as spot): use circular hit-testing
                    radius = max(10, (x2 - x1) / 2 + 5)  # Minimum 10px radius for easy clicking
                    distance = ((x - center_x)**2 + (y - center_y)**2)**0.5
                    if distance <= radius:
                        return primitive.element_id
                else:
                    # Standalone LoI (rendered as line segment): use line-based hit-testing
                    line_length = 30  # Must match rendering logic
                    line_start_x = center_x - line_length / 2
                    line_end_x = center_x + line_length / 2
                    
                    # Check if click is near the horizontal line segment
                    if (line_start_x - 5) <= x <= (line_end_x + 5) and abs(y - center_y) <= 8:
                        return primitive.element_id
                    
            elif element_type == "predicate":
                # For predicates (text), use rectangular bounds with padding
                padding = 5
                if (x1 - padding) <= x <= (x2 + padding) and (y1 - padding) <= y <= (y2 + padding):
                    return primitive.element_id
                    
            elif element_type == "cut":
                # For cuts, check if click is on the boundary (not interior)
                # This allows selecting the cut itself vs. clicking inside it
                margin = 10  # Width of selectable boundary
                # Check if point is within outer bounds but not in inner area
                if (x1 <= x <= x2 and y1 <= y <= y2):
                    # Check if we're close to the boundary
                    dist_to_left = abs(x - x1)
                    dist_to_right = abs(x - x2)
                    dist_to_top = abs(y - y1)
                    dist_to_bottom = abs(y - y2)
                    
                    min_dist_to_boundary = min(dist_to_left, dist_to_right, dist_to_top, dist_to_bottom)
                    if min_dist_to_boundary <= margin:
                        return primitive.element_id
                        
            else:
                # Default rectangular hit-testing for other elements
                if x1 <= x <= x2 and y1 <= y <= y2:
                    return primitive.element_id
                    
        return None

class Phase2GUIFoundation(QMainWindow):
    """Main window for Phase 2 GUI foundation with working EGI rendering."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arisbe Phase 2 GUI Foundation - EGI Rendering")
        self.setGeometry(100, 100, 1000, 700)
        
        # Initialize components
        self.layout_engine = GraphvizLayoutEngine()
        
        # Initialize corpus loader
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
            from src.corpus_loader import get_corpus_loader
            self.corpus_loader = get_corpus_loader()
            print(f"✓ Corpus loaded with {len(self.corpus_loader.examples)} examples")
        except Exception as e:
            print(f"Warning: Could not load corpus: {e}")
            self.corpus_loader = None
        
        # Sample EGIF expressions for testing
        self.sample_egifs = [
            '(Human "Socrates")',
            '(Human "Socrates") (Mortal "Socrates")',
            '*x (Human x) ~[ (Mortal x) ]',
            '(Human "Socrates") ~[ (Mortal "Socrates") ]',
            '*x *y (Loves x y) ~[ (Happy x) ]',
            '*x ~[ ~[ (P x) ] ]',  # Double cut
        ]
        
        self.setup_ui()
        self.load_sample_diagram()
        
    def setup_ui(self):
        """Set up the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Top controls
        controls_layout = QHBoxLayout()
        
        # Corpus browser section
        if self.corpus_loader:
            controls_layout.addWidget(QLabel("Corpus:"))
            self.corpus_combo = QComboBox()
            self.corpus_combo.addItem("Select from corpus...")
            self._populate_corpus_dropdown()
            controls_layout.addWidget(self.corpus_combo)
            
            import_btn = QPushButton("Import")
            import_btn.clicked.connect(self.import_corpus_example)
            controls_layout.addWidget(import_btn)
            
            # Separator
            controls_layout.addWidget(QLabel("|"))
        
        # Manual EGIF input
        controls_layout.addWidget(QLabel("EGIF:"))
        self.egif_combo = QComboBox()
        self.egif_combo.setEditable(True)
        self.egif_combo.addItems(self.sample_egifs)
        self.egif_combo.currentTextChanged.connect(self.on_egif_changed)
        controls_layout.addWidget(self.egif_combo)
        
        # Render button
        render_btn = QPushButton("Render Diagram")
        render_btn.clicked.connect(self.render_diagram)
        controls_layout.addWidget(render_btn)
        
        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_diagram)
        controls_layout.addWidget(clear_btn)
        
        # Mode switching controls
        controls_layout.addWidget(QLabel("|"))  # Separator
        controls_layout.addWidget(QLabel("Mode:"))
        
        self.mode_warmup_btn = QPushButton("Warmup")
        self.mode_warmup_btn.setCheckable(True)
        self.mode_warmup_btn.setChecked(True)  # Default to Warmup
        self.mode_warmup_btn.clicked.connect(lambda: self.switch_mode(Mode.WARMUP))
        controls_layout.addWidget(self.mode_warmup_btn)
        
        self.mode_practice_btn = QPushButton("Practice")
        self.mode_practice_btn.setCheckable(True)
        self.mode_practice_btn.clicked.connect(lambda: self.switch_mode(Mode.PRACTICE))
        controls_layout.addWidget(self.mode_practice_btn)
        
        main_layout.addLayout(controls_layout)
        
        # Splitter for diagram and info
        splitter = QSplitter(Qt.Horizontal)
        
        # Diagram widget
        self.diagram_widget = EGDiagramWidget()
        splitter.addWidget(self.diagram_widget)
        
        # Info panel
        info_frame = QFrame()
        info_frame.setMaximumWidth(300)
        info_layout = QVBoxLayout(info_frame)
        
        info_layout.addWidget(QLabel("EGI Structure:"))
        self.egi_info = QTextEdit()
        self.egi_info.setMaximumHeight(150)
        self.egi_info.setReadOnly(True)
        info_layout.addWidget(self.egi_info)
        
        info_layout.addWidget(QLabel("Selection Info:"))
        self.selection_info = QTextEdit()
        self.selection_info.setMaximumHeight(100)
        self.selection_info.setReadOnly(True)
        info_layout.addWidget(self.selection_info)
        
        # Annotation Controls section
        annotation_group = QGroupBox("Display Annotations:")
        annotation_layout = QVBoxLayout()
        
        # Master annotation toggle
        self.annotations_checkbox = QCheckBox("Show Annotations")
        self.annotations_checkbox.toggled.connect(self.on_annotations_toggled)
        annotation_layout.addWidget(self.annotations_checkbox)
        
        # Individual annotation type controls
        self.arity_checkbox = QCheckBox("Arity Numbering")
        self.arity_checkbox.toggled.connect(self.on_arity_toggled)
        self.arity_checkbox.setEnabled(False)  # Disabled until master is enabled
        annotation_layout.addWidget(self.arity_checkbox)
        
        self.labels_checkbox = QCheckBox("Argument Labels")
        self.labels_checkbox.toggled.connect(self.on_labels_toggled)
        self.labels_checkbox.setEnabled(False)  # Disabled until master is enabled
        annotation_layout.addWidget(self.labels_checkbox)
        
        annotation_group.setLayout(annotation_layout)
        info_layout.addWidget(annotation_group)
        
        # Phase 2 Development section
        phase2_group = QGroupBox("Phase 2 Development:")
        phase2_layout = QVBoxLayout()
        
        # Foundation status
        foundation_label = QLabel("Foundation Ready:")
        foundation_items = [
            "✓ EGI → Visual rendering",
            "✓ Basic selection system", 
            "✓ Hover effects",
            "✓ Mouse interaction",
            "✓ Annotation system integrated"
        ]
        for item in foundation_items:
            phase2_layout.addWidget(QLabel(item))
        
        phase2_layout.addWidget(QLabel(""))
        next_label = QLabel("Next: Selection overlays")
        phase2_layout.addWidget(next_label)
        phase2_layout.addWidget(QLabel("Context-sensitive actions"))
        phase2_layout.addWidget(QLabel("Dynamic effects"))
        
        phase2_group.setLayout(phase2_layout)
        info_layout.addWidget(phase2_group)
        
        splitter.addWidget(info_frame)
        main_layout.addWidget(splitter)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Phase 2 GUI Foundation Ready")
        
        # Timer for updating selection info
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_selection_info)
        self.update_timer.start(500)  # Update every 500ms
        
    def on_egif_changed(self, text):
        """Handle EGIF input change."""
        if text.strip():
            self.render_diagram()
            
    def render_diagram(self):
        """Render diagram from current EGIF using Phase 1d pipeline."""
        egif_text = self.egif_combo.currentText().strip()
        
        if not egif_text:
            self.status_bar.showMessage("Enter EGIF to render")
            return
            
        try:
            # Phase 1d Pipeline: EGIF → EGI → Layout → Visual
            
            # 1. Parse EGIF to EGI
            egif_parser = EGIFParser(egif_text)
            egi = egif_parser.parse()
            
            # 2. Generate layout using the proper layout engine
            layout_result = self.layout_engine.create_layout_from_graph(egi)
            print(f"DEBUG: Layout result type: {type(layout_result)}")
            print(f"DEBUG: Layout result attributes: {dir(layout_result)}")
            
            # 3. Convert layout result to spatial primitives list
            # GraphvizLayoutEngine returns LayoutResult with primitives dict
            if hasattr(layout_result, 'primitives'):
                spatial_primitives = list(layout_result.primitives.values())
                print(f"DEBUG: Found {len(spatial_primitives)} spatial primitives")
                for i, prim in enumerate(spatial_primitives[:3]):  # Show first 3
                    print(f"DEBUG: Primitive {i}: {prim.element_id} ({prim.element_type}) at {prim.position}")
            else:
                print(f"DEBUG: No 'primitives' attribute found in layout_result")
                spatial_primitives = []
            
            # 4. Render in GUI
            self.diagram_widget.set_diagram(egi, spatial_primitives)
            
            # Update info panel
            self.update_egi_info(egi)
            
            self.status_bar.showMessage(f"Rendered: {len(egi.V)} vertices, {len(egi.E)} edges, {len(egi.Cut)} cuts")
            
        except Exception as e:
            self.status_bar.showMessage(f"Error: {str(e)}")
            print(f"Rendering error: {e}")
            
    def clear_diagram(self):
        """Clear the current diagram."""
        self.diagram_widget.clear_diagram()
        self.update_egi_info(None)
        self.update_selection_info()
        self.status_bar.showMessage("Diagram cleared")
    
    def switch_mode(self, new_mode: Mode):
        """Switch between Warmup and Practice modes."""
        # Update button states
        self.mode_warmup_btn.setChecked(new_mode == Mode.WARMUP)
        self.mode_practice_btn.setChecked(new_mode == Mode.PRACTICE)
        
        # Switch mode in diagram widget
        self.diagram_widget.switch_mode(new_mode)
        
        # Update status bar
        mode_name = "Warmup" if new_mode == Mode.WARMUP else "Practice"
        self.status_bar.showMessage(f"Switched to {mode_name} mode")
        
        # Update selection info to show available actions
        self.update_selection_info()
        
    def load_egi(self, egi: RelationalGraphWithCuts):
        """Load a new EGI and update the display"""
        self.egi = egi
        # Update the diagram controller with the new EGI
        self.diagram_controller = EGIDiagramController(self.egi)
        self._render_diagram()
        self.update()
        
    def update_egi_info(self, egi: RelationalGraphWithCuts):
        """Update EGI structure information."""
        info_text = f"Vertices: {len(egi.V)}\n"
        info_text += f"Edges: {len(egi.E)}\n"
        info_text += f"Cuts: {len(egi.Cut)}\n\n"
        
        info_text += "Relations:\n"
        for edge_id, relation_name in egi.rel.items():
            vertex_seq = egi.nu.get(edge_id, ())
            info_text += f"  {relation_name}: {vertex_seq}\n"
            
        self.egi_info.setPlainText(info_text)
        
    def update_selection_info(self):
        """Update selection information with mode-aware details."""
        selected = self.diagram_widget.selected_elements
        hover = self.diagram_widget.hover_element
        current_mode = self.diagram_widget.get_current_mode()
        
        info_text = f"Mode: {current_mode.value.title()}\n"
        info_text += f"Selected: {len(selected)} elements\n"
        
        if selected:
            info_text += f"  {', '.join(list(selected)[:3])}\n"
            if len(selected) > 3:
                info_text += f"  ... and {len(selected) - 3} more\n"
                
        # Show available actions for current selection
        available_actions = self.diagram_widget.get_available_actions()
        if available_actions:
            info_text += f"\nAvailable Actions:\n"
            for action in sorted(available_actions, key=lambda x: x.value):
                action_name = action.value.replace('_', ' ').title()
                info_text += f"  • {action_name}\n"
                
        if hover:
            info_text += f"\nHover: {hover}"
            
        self.selection_info.setPlainText(info_text)
        
    def _populate_corpus_dropdown(self):
        """Populate the corpus dropdown with available examples."""
        if not self.corpus_loader:
            return
        
        # Group examples by category
        categories = {}
        for example in self.corpus_loader.examples.values():
            category = example.category
            if category not in categories:
                categories[category] = []
            categories[category].append(example)
        
        # Add examples organized by category
        for category, examples in sorted(categories.items()):
            for example in examples:
                display_text = f"[{category}] {example.title}"
                self.corpus_combo.addItem(display_text, example.id)
    
    def import_corpus_example(self):
        """Import the selected corpus example into the EGIF input."""
        if not self.corpus_loader or self.corpus_combo.currentIndex() == 0:
            return
        
        example_id = self.corpus_combo.currentData()
        if not example_id:
            return
        
        example = self.corpus_loader.get_example(example_id)
        if example and example.egif_content:
            self.egif_combo.setCurrentText(example.egif_content)
            # Auto-render the imported example
            self.render_diagram()
            
            print(f"✓ Imported corpus example: {example.title}")
            print(f"  EGIF: {example.egif_content}")
            print(f"  Description: {example.description}")
        else:
            print(f"Warning: No EGIF content found for {example_id}")
    
    def load_sample_diagram(self):
        """Load the first sample diagram on startup."""
        if self.sample_egifs:
            self.egif_combo.setCurrentText(self.sample_egifs[4])  # Load Loves x y example for arity testing
            self.render_diagram()

    # Annotation control event handlers
    def on_annotations_toggled(self, checked: bool):
        """Handle master annotation toggle."""
        # Enable/disable individual annotation controls
        self.arity_checkbox.setEnabled(checked)
        self.labels_checkbox.setEnabled(checked)
        
        # Toggle annotation display in diagram widget
        self.diagram_widget.toggle_annotations(checked)
        
        # Update status
        print(f"Annotations {'enabled' if checked else 'disabled'}")
    
    def on_arity_toggled(self, checked: bool):
        """Handle arity numbering toggle."""
        self.diagram_widget.toggle_annotation_type(AnnotationType.ARITY_NUMBERING, checked)
        print(f"Arity numbering {'enabled' if checked else 'disabled'}")
    
    def on_labels_toggled(self, checked: bool):
        """Handle argument labels toggle."""
        self.diagram_widget.toggle_annotation_type(AnnotationType.ARGUMENT_LABELS, checked)
        print(f"Argument labels {'enabled' if checked else 'disabled'}")

def main():
    """Run the Phase 2 GUI foundation."""
    if not PYSIDE6_AVAILABLE:
        print("PySide6 is required for the GUI. Install with: pip install PySide6")
        return
        
    app = QApplication(sys.argv)
    
    # Create and show main window
    window = Phase2GUIFoundation()
    window.show()
    
    print("Phase 2 GUI Foundation Running:")
    print("✓ EGI → Visual rendering pipeline working")
    print("✓ Basic selection and interaction implemented")
    print("✓ Foundation ready for Phase 2 development")
    print("✓ Try different EGIF expressions from the dropdown")
    print("✓ Corpus integration with import functionality")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
