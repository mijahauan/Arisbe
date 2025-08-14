#!/usr/bin/env python3
"""
Phase 2 GUI Foundation - Working EGI Rendering for Parallel Development

This creates a functioning GUI that renders EGI diagrams, providing the foundation
for Phase 2 selection overlays and context-sensitive actions development.

Uses the completed Phase 1d pipeline: EGIF → EGI → Layout → Visual Rendering
"""

import sys
import os
from math import cos, sin
from typing import Dict, List, Optional, Tuple, Set
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Phase 1d Foundation - Complete pipeline
from src.egif_parser_dau import EGIFParser
from src.egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut
from src.graphviz_layout_engine_v2 import GraphvizLayoutEngine
from src.canonical_qt_renderer import CanonicalQtRenderer
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
    from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QMouseEvent, QPainterPath, QFontMetrics, QFontMetricsF, QCursor
    from PySide6.QtCore import Qt, QPointF, QRectF, QTimer
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False
    print("PySide6 not available - install with: pip install PySide6")

if PYSIDE6_AVAILABLE:
    class QtPainterCanvasAdapter:
        """Adapter to provide a PySide6Canvas-like API backed by a QPainter.
        This unifies GUI rendering with the canonical DiagramRendererDau pathway.
        """
        def __init__(self, painter: QPainter, width: int, height: int):
            self._p = painter
            self._w = width
            self._h = height
            # Public attributes expected by DiagramRendererDau._compute_fit_transform
            self.width = width
            self.height = height

        # Utility to set pen/brush from style dict
        def _apply_style(self, style: dict | None):
            if style is None:
                style = {}
            color = style.get('color', (0, 0, 0))
            width = float(style.get('width', 1.0))
            fill_color = style.get('fill_color', None)
            pen = QPen(QColor(*color))
            pen.setWidthF(width)
            self._p.setPen(pen)
            if fill_color is None:
                self._p.setBrush(Qt.NoBrush)
            else:
                self._p.setBrush(QBrush(QColor(*fill_color)))

        def clear(self):
            self._p.fillRect(0, 0, self._w, self._h, QColor(255, 255, 255))

        def draw_line(self, p1, p2, style=None):
            self._apply_style(style)
            self._p.drawLine(p1[0], p1[1], p2[0], p2[1])

        def draw_curve(self, points, style=None, closed=False):
            # Generic polyline; sufficient for selection halos and gentle curves
            self._apply_style(style)
            path = QPainterPath()
            if not points:
                return
            path.moveTo(points[0][0], points[0][1])
            for (x, y) in points[1:]:
                path.lineTo(x, y)
            if closed:
                path.closeSubpath()
            self._p.drawPath(path)

        def draw_text(self, text, position, style=None):
            # Center text at the given (x, y) position (Dau renderer expects centered labels)
            if style is None:
                style = {}
            color = style.get('color', (0, 0, 0))
            font_family = style.get('font_family', 'Times New Roman')
            font_size = int(style.get('font_size', 12))
            bold = bool(style.get('bold', False))
            self._p.setPen(QColor(*color))
            font = QFont(font_family, pointSize=font_size)
            font.setBold(bold)
            self._p.setFont(font)
            fm = QFontMetricsF(font)
            tw = fm.horizontalAdvance(text)
            th = fm.height()
            rect = QRectF(position[0] - tw / 2.0,
                          position[1] - th / 2.0,
                          tw,
                          th)
            self._p.drawText(rect, Qt.AlignCenter, text)

        def draw_circle(self, center, radius, style=None):
            self._apply_style(style)
            cx, cy = center
            r = radius
            self._p.drawEllipse(QRectF(cx - r, cy - r, 2 * r, 2 * r))

        def draw_oval(self, x1, y1, x2, y2, style=None):
            self._apply_style(style)
            self._p.drawEllipse(QRectF(x1, y1, x2 - x1, y2 - y1))

        def save_to_file(self, path: str):
            # Not used during GUI paint; provided for API completeness
            pass

class EGDiagramWidget(QWidget):
    """Widget for rendering EG diagrams with interaction support."""
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(600, 400)
        self.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        
        # Initialize with a simple example
        self.egi = self.create_example_egi()
        # Use canonical mode throughout the GUI (mode parameter removed in refactoring)
        self.layout_engine = GraphvizLayoutEngine()
        self.spatial_primitives = []
        self.selection_system = ModeAwareSelectionSystem(Mode.WARMUP)
        self.annotation_manager = AnnotationManager()
        # Keep latest layout_result for overlays/annotations
        self.layout_result = None
        
        # Initialize EGI-diagram controller for proper correspondence
        self.diagram_controller = EGIDiagramController(self.egi)
        
        # Annotation system
        self.annotation_primitives: List[AnnotationPrimitive] = []
        self.show_annotations = False
        # Optional renderer markers at predicate boundary (annotation-controlled)
        self._draw_argument_markers: bool = False
        
        # Initialize default annotation layers
        self._setup_default_annotations()
        
        # Mode-aware selection system for Phase 2
        self.current_mode = Mode.WARMUP
        
        # Selection/hover state is managed by ModeAwareSelectionSystem
        # Legacy fields removed in favor of selection_system.selection_state
        
        # Branching point tracking for interactive selection
        self.branching_points = {}  # vertex_id -> (x, y, vertex_name)
        self.selected_branching_points = set()
        self.hover_branching_point = None
        
        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)

        # Cache of predicate text bounds used for precise periphery hooks
        self._predicate_text_bounds: Dict[str, QRectF] = {}

        # Marquee selection state
        self._marquee_active = False
        self._marquee_start: Optional[Tuple[float, float]] = None
        self._marquee_end: Optional[Tuple[float, float]] = None

        # Alt-click cycling state
        self._alt_cycle_candidates: List[str] = []
        self._alt_cycle_index: int = 0
        self._alt_cycle_anchor: Optional[Tuple[int, int]] = None
        
    def create_example_egi(self) -> RelationalGraphWithCuts:
        """Create Socrates example EGI for testing branching point positioning"""
        from src.egi_core_dau import create_empty_graph, create_vertex, create_edge
        from frozendict import frozendict
        
        # Create vertices - one constant "Socrates", shared between predicates
        socrates = create_vertex(label="Socrates", is_generic=False)  # Constant vertex
        
        # Create edges (predicates)
        human_edge = create_edge()    # Human predicate
        mortal_edge = create_edge()   # Mortal predicate
        
        # Create empty graph and add elements
        graph = create_empty_graph()
        
        # Add vertices and edges
        new_V = graph.V | {socrates}
        new_E = graph.E | {human_edge, mortal_edge}
        
        # Create nu mapping (edge to vertex sequences)
        # Both predicates connect to the same Socrates vertex
        nu_mapping = {
            human_edge.id: (socrates.id,),   # Human(Socrates)
            mortal_edge.id: (socrates.id,)   # Mortal(Socrates)
        }
        
        # Create rel mapping (edge to relation names)
        rel_mapping = {
            human_edge.id: "Human",
            mortal_edge.id: "Mortal"
        }
        
        # Create area mapping (all elements in sheet)
        area_mapping = {
            graph.sheet: frozenset({socrates.id, human_edge.id, mortal_edge.id})
        }
        
        # Create new graph with all components
        from src.egi_core_dau import RelationalGraphWithCuts
        return RelationalGraphWithCuts(
            V=new_V,
            E=new_E,
            nu=frozendict(nu_mapping),
            sheet=graph.sheet,
            Cut=graph.Cut,
            area=frozendict(area_mapping),
            rel=frozendict(rel_mapping)
        )
    
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
        # Tie predicate-boundary argument markers to arity numbering toggle
        if annotation_type == AnnotationType.ARITY_NUMBERING:
            self._draw_argument_markers = bool(enabled)
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
        
        # Clear selections via selection system
        self.selection_system.clear_selection()
        self.update()
        
    def clear_diagram(self):
        """Clear the current diagram."""
        self.egi = None
        self.spatial_primitives.clear()
        self.annotation_primitives.clear()
        self.selection_system.clear_selection()
        self.update()
    
    def switch_mode(self, new_mode: Mode):
        """Switch between Warmup and Practice modes."""
        if new_mode != self.current_mode:
            self.current_mode = new_mode
            self.selection_system.switch_mode(new_mode)
            
            # Clear drag state
            self.drag_state = None
            
            # Trigger repaint to update visual indicators
            self.update()
            
            print(f"Switched to {new_mode.value} mode")
    
    def get_current_mode(self) -> Mode:
        """Get the current interaction mode."""
        return self.current_mode
    
    def get_available_actions(self) -> Set[ActionType]:
        """Get available actions for current selection."""
        return self.selection_system.get_available_actions()
    
    # --- Coordinate transforms between layout canvas and widget ---
    def _compute_transform(self) -> Tuple[float, float, float, float]:
        """Return (s, s, ox, oy) that maps canvas -> widget with uniform scale and centering.
        Formula: wx = s*cx + ox, wy = s*cy + oy. Inverse uses (wx-ox)/s.
        Matches CanonicalQtRenderer's uniform transform so overlays align exactly.
        """
        try:
            cb = getattr(self, 'layout_result', None).canvas_bounds  # type: ignore
            x1, y1, x2, y2 = cb
            cw = max(x2 - x1, 1.0)
            ch = max(y2 - y1, 1.0)
            W = max(self.width(), 1)
            H = max(self.height(), 1)
            s = min(W / cw, H / ch)
            # world to widget: first translate world so min is at 0, then scale, then center
            content_w = s * cw
            content_h = s * ch
            ox = 0.5 * (W - content_w) - s * x1
            oy = 0.5 * (H - content_h) - s * y1
            return s, s, ox, oy
        except Exception:
            return 1.0, 1.0, 0.0, 0.0
    
    def _canvas_to_widget_pt(self, cx: float, cy: float) -> Tuple[float, float]:
        sx, sy, tx, ty = self._compute_transform()
        return sx * cx + tx, sy * cy + ty
    
    def _widget_to_canvas_pt(self, wx: float, wy: float) -> Tuple[float, float]:
        sx, sy, tx, ty = self._compute_transform()
        # avoid division by zero
        if sx == 0:
            sx = 1.0
        if sy == 0:
            sy = 1.0
        return (wx - tx) / sx, (wy - ty) / sy
    
    def _canvas_rect_to_widget(self, r: QRectF) -> QRectF:
        sx, sy, tx, ty = self._compute_transform()
        wx1 = sx * (r.left() - tx)
        wy1 = sy * (r.top() - ty)
        wx2 = sx * (r.right() - tx)
        wy2 = sy * (r.bottom() - ty)
        return QRectF(min(wx1, wx2), min(wy1, wy2), abs(wx2 - wx1), abs(wy2 - wy1))
        
    def paintEvent(self, event):
        """Render via comprehensive Dau-compliant EGDF specification."""
        if not PYSIDE6_AVAILABLE or self.egi is None:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        try:
            # Compute canonical layout using GraphvizLayoutEngine
            layout_engine = GraphvizLayoutEngine()
            layout_result = layout_engine.create_layout_from_graph(self.egi)
            
            # Use comprehensive Dau-compliant rendering via DiagramRendererDau
            self._render_with_dau_compliant_specification(painter, layout_result)

            # Sync spatial primitives and layout cache for overlays/hit-testing
            try:
                self.spatial_primitives = list(layout_result.primitives.values())
            except Exception:
                self.spatial_primitives = []
            self.layout_result = layout_result

            # Optional: render annotations after core diagram
            if self.show_annotations:
                # Ensure annotation primitives are based on latest layout_result
                self._update_annotations()
                # Draw simple overlays for annotations using painter directly
                self._render_annotations(painter)

            # Draw selection overlays on top of base diagram/annotations
            self._render_selection_overlays(painter)

            # Draw marquee rectangle if active (UI overlay)
            if self._marquee_active and self._marquee_start and self._marquee_end:
                x1, y1 = self._marquee_start
                x2, y2 = self._marquee_end
                left, top = min(x1, x2), min(y1, y2)
                w, h = abs(x2 - x1), abs(y2 - y1)
                painter.setPen(QPen(QColor(30,144,255), 1, Qt.DashLine))
                painter.setBrush(QBrush(QColor(30,144,255,40)))
                painter.drawRect(QRectF(left, top, w, h))
        finally:
            painter.end()
    
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
        
        # Check if element is selected or hovered (via selection system)
        sel_state = self.selection_system.selection_state
        is_selected = element_id in sel_state.selected_elements
        is_hovered = (sel_state.hover_element == element_id)
        
        if element_type == "vertex":
            self._render_vertex(painter, element_id, position, is_selected, is_hovered)
        elif element_type == "predicate":
            self._render_edge(painter, element_id, position, bounds, is_selected, is_hovered)
        elif element_type == "edge":
            # Edge/ligature rendering is now handled by _render_all_ligatures
            pass
        elif element_type == "cut":
            self._render_cut(painter, element_id, bounds, is_selected, is_hovered)
            
    def _render_vertex(self, painter: QPainter, element_id: str, position: Tuple[float, float], 
                      is_selected: bool, is_hovered: bool):
        """Render vertex label near branching point (constant names like "Socrates").
        The heavy ligature path itself is rendered in _render_simple_working_ligatures().
        """
        if not self.egi:
            return
        # Find vertex label from EGI
        vlabel = None
        try:
            for v in self.egi.V:
                if getattr(v, 'id', None) == element_id:
                    vlabel = getattr(v, 'label', None)
                    break
        except Exception:
            vlabel = None
        if not vlabel:
            return
        # Tangent/normal-based placement near branching point
        bx, by = position
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.setBrush(Qt.NoBrush)
        font = QFont("Times New Roman", 10)
        painter.setFont(font)
        fm = QFontMetricsF(font)
        text = f'"{vlabel}"'
        tw = fm.horizontalAdvance(text)
        th = fm.height()

        hooks = self._collect_vertex_hooks_for_label(element_id, position)
        # Compute tangent as average of directions to hooks; fallback to horizontal
        tx_vec, ty_vec = 1.0, 0.0
        if hooks:
            sx, sy = 0.0, 0.0
            for h in hooks:
                dx = h.x() - bx
                dy = h.y() - by
                L = (dx*dx + dy*dy) ** 0.5
                if L > 0:
                    sx += dx / L
                    sy += dy / L
            if sx != 0 or sy != 0:
                Ls = (sx*sx + sy*sy) ** 0.5
                tx_vec, ty_vec = sx / Ls, sy / Ls
        # Normal to the right of the tangent
        nx_vec, ny_vec = -ty_vec, tx_vec

        # Initial placement parameters
        along = 16.0
        away = 8.0
        # Compute initial top-left of centered rect
        center_x = bx + tx_vec * along + nx_vec * away
        center_y = by + ty_vec * along + ny_vec * away
        label_rect = QRectF(center_x - tw/2.0, center_y - th/2.0, tw, th)

        # Collision-aware nudging against predicate text bounds
        max_steps = 8
        step = 4.0
        steps = 0
        while self._rect_intersects_any_predicate(label_rect) and steps < max_steps:
            # Nudge further along normal
            center_x += nx_vec * step
            center_y += ny_vec * step
            label_rect.moveTo(center_x - tw/2.0, center_y - th/2.0)
            steps += 1

        painter.drawText(label_rect, Qt.AlignCenter, text)
        # Optional: subtle hover indicator
        if is_hovered:
            painter.setPen(QPen(QColor(30,144,255), 1, Qt.DashLine))
            painter.drawRect(label_rect.adjusted(-2, -2, 2, 2))

    def _collect_vertex_hooks_for_label(self, vertex_id: str, vertex_pos: Tuple[float, float]) -> List[QPointF]:
        """Recompute per-vertex predicate periphery hooks for label placement.
        Honors ν-order bias for binary predicates.
        """
        hooks: List[QPointF] = []
        vx, vy = vertex_pos
        # Find predicates connected to this vertex
        for edge_id, vertex_seq in self.egi.nu.items():
            if vertex_id not in vertex_seq:
                continue
            rect = self._predicate_text_bounds.get(edge_id)
            if rect is None:
                # Approximate if missing
                pred_prim = next((p for p in self.spatial_primitives if p.element_type == "predicate" and p.element_id == edge_id), None)
                if not pred_prim:
                    continue
                cx, cy = pred_prim.position
                rect = QRectF(cx - 30.0, cy - 10.0, 60.0, 20.0)
            cx, cy = rect.center().x(), rect.center().y()
            num_args = len(vertex_seq)
            # Argument index for ν-order
            try:
                idx = vertex_seq.index(vertex_id)
            except ValueError:
                idx = 0
            if num_args == 2:
                hook = QPointF(rect.left(), cy) if idx == 0 else QPointF(rect.right(), cy)
            else:
                hook = self._intersect_rect_periphery(rect, QPointF(cx, cy), QPointF(vx, vy))
                if hook is None:
                    continue
            hooks.append(hook)
        return hooks

    def _rect_intersects_any_predicate(self, r: QRectF) -> bool:
        for prect in self._predicate_text_bounds.values():
            if r.intersects(prect):
                return True
        return False
        
    def _predicate_label_rect(self, edge_id: str, primitive: SpatialPrimitive) -> QRectF:
        """Return the QRectF of the predicate label for the given edge.
        Uses cached bounds from rendering when available; otherwise computes
        a fallback rectangle using the same font metrics as rendering.
        """
        # Cached from `_render_edge`
        rect = self._predicate_text_bounds.get(edge_id)
        if rect is not None:
            return rect
        # Fallback computation
        if not self.egi or primitive is None or primitive.position is None:
            return QRectF()
        relation_name = self.egi.rel.get(edge_id, f"R{edge_id[:4]}")
        # Match CanonicalQtRenderer defaults (pred_font_family/size and padding)
        font = QFont("Times New Roman", 12)
        fm = QFontMetricsF(font)
        padding_x = 6.0
        padding_y = 4.0
        x, y = primitive.position
        tw = fm.horizontalAdvance(relation_name)
        th = fm.height()
        rect = QRectF(x - tw / 2.0 - padding_x,
                      y - th / 2.0 - padding_y,
                      tw + 2.0 * padding_x,
                      th + 2.0 * padding_y)
        # Store for next time to keep consistency across frame
        self._predicate_text_bounds[edge_id] = rect
        return rect
        
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
        font = QFont("Times New Roman", 11)
        painter.setFont(font)
        fm = QFontMetricsF(font)
        # Minimal padding to protect text from cut lines; also used for periphery hooks
        text_padding = 2.0
        tw = fm.horizontalAdvance(relation_name)
        th = fm.height()
        rect = QRectF(x - tw / 2.0 - text_padding,
                      y - th / 2.0 - text_padding,
                      tw + 2.0 * text_padding,
                      th + 2.0 * text_padding)
        # Cache bounds for ligature periphery intersection
        self._predicate_text_bounds[element_id] = rect
        # Draw centered without a background so rect matches actual drawing
        painter.setPen(QPen(color, 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawText(rect, Qt.AlignCenter, relation_name)
        
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
                        text_half_width = rect.width() / 2
                        text_half_height = rect.height() / 2
                        
                        # Calculate hook position
                        if abs(dx_norm) > abs(dy_norm):
                            hook_x = pred_center_x + (text_half_width if dx_norm > 0 else -text_half_width)
                            hook_y = pred_center_y + dy_norm * text_half_width / abs(dx_norm)
                        else:
                            hook_x = pred_center_x + dx_norm * text_half_height / abs(dy_norm)
                            hook_y = pred_center_y + (text_half_height if dy_norm > 0 else -text_half_height)
                        
                        # REMOVED: Hook indicator ellipses (spots) - violate Dau/Peircean conventions
                        # These small dots were creating unwanted visual artifacts in all diagrams
                        # Per Dau's conventions, ligatures should connect directly to predicate boundaries
                        # without additional hook indicators or spots
                    
    # OBSOLETE METHOD REMOVED: _render_identity_line
    # This method has been replaced by the ligature rendering system in _render_single_object_ligature
    
    def _render_simple_working_ligatures(self, painter: QPainter):
        """Render ligatures as heavy lines clipped to predicate text periphery with ν-ordered bias.
        This ignores Graphviz edge polylines and computes precise periphery hooks instead.
        """
        if not self.egi or not self.spatial_primitives:
            return

        # Heavy line style (Dau convention)
        painter.setPen(QPen(QColor(0, 0, 0), 4))

        # Collect positions
        vertex_positions: Dict[str, Tuple[float, float]] = {}
        for p in self.spatial_primitives:
            if p.element_type == "vertex":
                vertex_positions[p.element_id] = p.position

        # Build mapping vertex -> list of hook points on connected predicates
        vertex_hooks: Dict[str, List[QPointF]] = {}

        for edge_id, vertex_seq in self.egi.nu.items():
            # Determine argument ordering for this predicate
            num_args = len(vertex_seq)
            # Fetch predicate rect from cache (created in _render_edge)
            rect = self._predicate_text_bounds.get(edge_id)
            # Fallback: if rect missing, approximate a small box around predicate center
            if rect is None:
                # Try to find predicate primitive to approximate
                pred_pos = next((p.position for p in self.spatial_primitives if p.element_type == "predicate" and p.element_id == edge_id), None)
                if pred_pos is None:
                    continue
                cx, cy = pred_pos
                rect = QRectF(cx - 30.0, cy - 10.0, 60.0, 20.0)

            cx = rect.center().x()
            cy = rect.center().y()

            for idx, v_id in enumerate(vertex_seq):
                vpos = vertex_positions.get(v_id)
                if not vpos:
                    continue

                # Compute periphery point with bias for 2-ary predicates
                if num_args == 2:
                    # Left midpoint for arg 0, right midpoint for arg 1 (ν order)
                    if idx == 0:
                        hook = QPointF(rect.left(), cy)
                    else:
                        hook = QPointF(rect.right(), cy)
                else:
                    # General case: intersect ray center->vertex with rect border
                    hook = self._intersect_rect_periphery(rect, QPointF(cx, cy), QPointF(vpos[0], vpos[1]))

                if hook is None:
                    continue

                if v_id not in vertex_hooks:
                    vertex_hooks[v_id] = []
                vertex_hooks[v_id].append(hook)

        # Draw a continuous heavy path per vertex: from vertex to each hook
        for v_id, hooks in vertex_hooks.items():
            vx, vy = vertex_positions.get(v_id, (None, None))
            if vx is None:
                continue
            vpt = QPointF(vx, vy)
            # Draw each branch as a heavy segment from vertex to periphery hook
            for hook in hooks:
                painter.drawLine(vpt, hook)

            # Draw identity spot at branching point
            self._draw_vertex_spot_only(painter, vpt)

    def _intersect_rect_periphery(self, rect: QRectF, center: QPointF, target: QPointF) -> Optional[QPointF]:
        """Return intersection point of ray (center->target) with rectangle border.
        If ray is axis-aligned or nearly so, uses the matching side.
        """
        cx, cy = center.x(), center.y()
        tx, ty = target.x(), target.y()
        dx = tx - cx
        dy = ty - cy
        if dx == 0 and dy == 0:
            return None

        # Parametric intersection with each side; choose smallest positive t
        t_candidates: List[Tuple[float, float, float]] = []  # (t, ix, iy)

        # Avoid division by zero
        if dx != 0:
            # Left side x = rect.left()
            t = (rect.left() - cx) / dx
            iy = cy + t * dy
            if t > 0 and rect.top() <= iy <= rect.bottom():
                t_candidates.append((t, rect.left(), iy))
            # Right side x = rect.right()
            t = (rect.right() - cx) / dx
            iy = cy + t * dy
            if t > 0 and rect.top() <= iy <= rect.bottom():
                t_candidates.append((t, rect.right(), iy))

        if dy != 0:
            # Top side y = rect.top()
            t = (rect.top() - cy) / dy
            ix = cx + t * dx
            if t > 0 and rect.left() <= ix <= rect.right():
                t_candidates.append((t, ix, rect.top()))
            # Bottom side y = rect.bottom()
            t = (rect.bottom() - cy) / dy
            ix = cx + t * dx
            if t > 0 and rect.left() <= ix <= rect.right():
                t_candidates.append((t, ix, rect.bottom()))

        if not t_candidates:
            return None

        t_min, ix, iy = min(t_candidates, key=lambda a: a[0])
        return QPointF(ix, iy)

    def _draw_vertex_spot_only(self, painter: QPainter, vpt: QPointF):
        # Prominent identity spot (radius per Dau)
        r = 3.5
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(vpt.x(), vpt.y()), r, r)
        painter.setPen(QPen(QColor(0, 0, 0), 4))  # restore heavy line pen
    
    def _debug_test_ligature_rendering(self, painter: QPainter):
        """Simple debug test to verify basic ligature rendering works."""
        print("DEBUG: _debug_test_ligature_rendering called")
        
        if not self.egi or not self.spatial_primitives:
            print("DEBUG: No EGI or spatial primitives - cannot render test ligatures")
            return
            
        # Set heavy line style
        painter.setPen(QPen(QColor(255, 0, 0), 6))  # Thick red line for visibility
        
        # Find any two elements and draw a test line between them
        positions = []
        for primitive in self.spatial_primitives:
            if primitive.element_type in ["vertex", "predicate"]:
                positions.append(primitive.position)
                if len(positions) >= 2:
                    break
        
        if len(positions) >= 2:
            # Draw test line between first two elements
            x1, y1 = positions[0]
            x2, y2 = positions[1]
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
            print(f"DEBUG: Drew test line from ({x1},{y1}) to ({x2},{y2})")
        else:
            print(f"DEBUG: Not enough elements found for test line (found {len(positions)})")
    
    def _render_ligatures_from_primitives(self, painter: QPainter):
        """Render ligatures using Graphviz spline data and advanced features."""
        if not self.egi or not self.spatial_primitives:
            print("DEBUG: No EGI or spatial primitives available for ligature rendering")
            return
            
        print(f"DEBUG: Starting ligature rendering with {len(self.spatial_primitives)} spatial primitives")
        print(f"DEBUG: EGI nu mapping: {dict(self.egi.nu)}")
            
        # Set heavy line style for all ligatures (Dau convention)
        painter.setPen(QPen(QColor(0, 0, 0), 4))
        
        # Get vertex, predicate, and edge primitives
        vertex_positions = {}
        predicate_positions = {}
        edge_primitives = {}
        
        # Debug: Show all primitive types
        primitive_types = {}
        for primitive in self.spatial_primitives:
            ptype = primitive.element_type
            if ptype not in primitive_types:
                primitive_types[ptype] = 0
            primitive_types[ptype] += 1
            
            if primitive.element_type == "vertex":
                vertex_positions[primitive.element_id] = primitive.position
            elif primitive.element_type == "predicate":
                predicate_positions[primitive.element_id] = primitive.position
            elif primitive.element_type == "edge":
                edge_primitives[primitive.element_id] = primitive
        
        print(f"DEBUG: Primitive types found: {primitive_types}")
        print(f"DEBUG: Vertices: {list(vertex_positions.keys())}")
        print(f"DEBUG: Predicates: {list(predicate_positions.keys())}")
        print(f"DEBUG: Edges: {list(edge_primitives.keys())}")
        
        # Render ligatures using Graphviz spline data when available
        for edge_id, vertex_sequence in self.egi.nu.items():
            if edge_id in edge_primitives:
                edge_primitive = edge_primitives[edge_id]
                
                # Use Graphviz spline curve points if available (collision-free routing)
                if edge_primitive.curve_points and len(edge_primitive.curve_points) > 1:
                    self._render_spline_ligature(painter, edge_primitive.curve_points)
                else:
                    # Fallback: render with separated hooks for n-ary predicates
                    self._render_ligature_with_hooks(painter, edge_id, vertex_sequence, 
                                                   vertex_positions, predicate_positions)
    
    def _render_spline_ligature(self, painter: QPainter, curve_points):
        """Render ligature using Graphviz spline curve points (collision-free)."""
        if len(curve_points) < 2:
            return
            
        # Draw smooth curve through all spline points
        for i in range(len(curve_points) - 1):
            start_point = curve_points[i]
            end_point = curve_points[i + 1]
            painter.drawLine(
                int(start_point[0]), int(start_point[1]),
                int(end_point[0]), int(end_point[1])
            )
    
    def _render_ligature_with_hooks(self, painter: QPainter, edge_id, vertex_sequence,
                                  vertex_positions, predicate_positions):
        """Render ligature with separated hooks for n-ary predicates."""
        if edge_id not in predicate_positions:
            return
            
        pred_pos = predicate_positions[edge_id]
        
        # For n-ary predicates, calculate separated hook positions
        num_args = len(vertex_sequence)
        
        for i, vertex_id in enumerate(vertex_sequence):
            if vertex_id in vertex_positions:
                vertex_pos = vertex_positions[vertex_id]
                
                # Calculate hook position with separation for n-ary predicates
                hook_pos = self._calculate_separated_hook_position(
                    pred_pos, vertex_pos, i, num_args
                )
                
                # Draw heavy line from vertex to separated hook position
                painter.drawLine(
                    int(vertex_pos[0]), int(vertex_pos[1]),
                    int(hook_pos[0]), int(hook_pos[1])
                )
    
    def _calculate_separated_hook_position(self, pred_pos, vertex_pos, arg_index, num_args):
        """Calculate separated hook position on predicate boundary for argument clarity."""
        pred_x, pred_y = pred_pos
        
        if num_args == 1:
            # Single argument: hook at predicate center
            return pred_pos
        
        # Multiple arguments: separate hooks around predicate boundary
        # Calculate offset based on argument index for maximum separation
        hook_offset = 20  # Distance from predicate center
        angle_step = 2 * 3.14159 / num_args  # Distribute evenly around circle
        angle = arg_index * angle_step
        
        hook_x = pred_x + hook_offset * cos(angle)
        hook_y = pred_y + hook_offset * sin(angle)
        
        return (hook_x, hook_y)
    
    # REMOVED: _post_process_ligature_layout() - conflicts with canonical mode
    # All ligature rendering is now handled by DiagramRendererDau in canonical mode
    
    def _render_with_dau_compliant_specification(self, painter: QPainter, layout_result):
        """
        Render using comprehensive Dau-compliant EGDF specification.
        
        This method replaces all piecemeal post-processing logic with a single
        delegation to DiagramRendererDau, which implements the complete canonical
        mode specification with exact Graphviz position preservation.
        """
        # Create a Qt-compatible canvas adapter for DiagramRendererDau
        canvas_adapter = QtCanvasAdapter(painter, self.width(), self.height())
        
        # Delegate to DiagramRendererDau - comprehensive Dau-compliant implementation
        from src.diagram_renderer_dau import DiagramRendererDau
        renderer = DiagramRendererDau()
        renderer.render_diagram(canvas_adapter, self.egi, layout_result)


class QtCanvasAdapter:
        """
        Adapter to make DiagramRendererDau work with QPainter.
        
        This adapter translates DiagramRendererDau's canvas interface calls
        to QPainter operations, enabling the comprehensive Dau-compliant
        specification to work within the Qt GUI.
        """
        
        def __init__(self, painter: QPainter, width: int, height: int):
            self.painter = painter
            self.width_val = width
            self.height_val = height
        
        def clear(self):
            """Clear the canvas (no-op for Qt since we're painting over existing content)."""
            pass
        
        def width(self) -> int:
            return self.width_val
        
        def height(self) -> int:
            return self.height_val
        
        def draw_line(self, start, end, style):
            """Draw a line using QPainter."""
            pen = QPen(QColor(*style['color']), style['width'])
            self.painter.setPen(pen)
            self.painter.drawLine(QPointF(*start), QPointF(*end))
        
        def draw_curve(self, points, style, closed=False):
            """Draw a curve using QPainter."""
            if len(points) < 2:
                return
            
            pen = QPen(QColor(*style['color']), style['width'])
            self.painter.setPen(pen)
            
            path = QPainterPath()
            path.moveTo(QPointF(*points[0]))
            
            if len(points) == 2:
                # Simple line
                path.lineTo(QPointF(*points[1]))
            else:
                # Smooth curve through points
                for i in range(1, len(points)):
                    path.lineTo(QPointF(*points[i]))
            
            if closed:
                path.closeSubpath()
            
            self.painter.drawPath(path)
        
        def draw_circle(self, center, radius, style):
            """Draw a circle using QPainter."""
            pen = QPen(QColor(*style['color']), style['width'])
            self.painter.setPen(pen)
            
            if 'fill_color' in style and style['fill_color']:
                brush = QBrush(QColor(*style['fill_color']))
                self.painter.setBrush(brush)
            else:
                self.painter.setBrush(Qt.NoBrush)
            
            cx, cy = center
            self.painter.drawEllipse(QPointF(cx, cy), radius, radius)
        
        def draw_text(self, text, position, style):
            """Draw text using QPainter."""
            font = QFont(style.get('font_family', 'Arial'), style.get('font_size', 12))
            self.painter.setFont(font)
            
            pen = QPen(QColor(*style['color']))
            self.painter.setPen(pen)
            
            self.painter.drawText(QPointF(*position), text)
        
        def save_to_file(self, filename):
            """No-op for Qt adapter (saving handled elsewhere)."""
            pass
    
    # REMOVED: All obsolete post-processing methods - replaced by comprehensive DiagramRendererDau
    
    # REMOVED: All obsolete post-processing methods - replaced by comprehensive DiagramRendererDau
    
    def mousePressEvent(self, event):
        """Start drag gestures, including attach-from-vertex."""
        if event.button() == Qt.LeftButton:
            pos = event.position() if hasattr(event, 'position') else event.localPos()
            wx, wy = float(pos.x()), float(pos.y())
            cx, cy = self._widget_to_canvas_pt(wx, wy)
            hit_id = self._find_element_at_position(cx, cy)
            if hit_id:
                # If clicked a vertex, start attach drag from that vertex
                prim = next((p for p in self.spatial_primitives if p.element_id == hit_id), None)
                if prim and prim.element_type == 'vertex':
                    self.drag_state = {'type': 'attach_from_vertex', 'vertex_id': hit_id}
                    self._last_mouse_widget_pos = (wx, wy)
                    self.update()
                    return
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Calculate the boundary position where ligature should connect to predicate.
        
        Implements two key principles:
        1. Parsimony: Minimize total line length while respecting EGI structure
        2. Tangency: Position hooks at tangent points with maximum separation
        """
        center_x, center_y = predicate_primitive.position
        
        # Get predicate text to calculate boundary
        predicate_name = None
        if self.egi:
            predicate_name = self.egi.rel.get(predicate_primitive.element_id)
        
        if not predicate_name:
            return (center_x, center_y)
        
        # Calculate text bounds
        font = QFont("Arial", 12)
        font_metrics = QFontMetrics(font)
        text_rect = font_metrics.boundingRect(predicate_name)
        
        text_width = text_rect.width()
        text_height = text_rect.height()
        padding = 5
        
        # For n-ary predicates, implement maximum separation with tangency
        if argument_index is not None:
            predicate_arity = self._get_predicate_arity(predicate_primitive.element_id)
            
            if predicate_arity > 1:
                return self._calculate_optimal_hook_position(
                    center_x, center_y, text_width, text_height, padding,
                    predicate_arity, argument_index, vertex_position
                )
        
        # Single hook case - use parsimony principle (shortest path to boundary)
        if vertex_position:
            return self._calculate_parsimonious_boundary_point(
                center_x, center_y, text_width, text_height, padding, vertex_position
            )
        
        # Default fallback
        return (center_x - text_width / 2 - padding, center_y)
    
    def _get_predicate_arity(self, predicate_id: str) -> int:
        """Get the arity (number of arguments) of a predicate from the EGI nu mapping."""
        if not self.egi:
            return 1
        
        # Count how many vertices this predicate connects to in the nu mapping
        arity = 0
        for edge_id, vertex_sequence in self.egi.nu.items():
            if edge_id == predicate_id:
                arity = len(vertex_sequence)
                break
        
        return max(1, arity)  # Minimum arity is 1
    
    def _calculate_optimal_hook_position(self, center_x: float, center_y: float, 
                                       text_width: float, text_height: float, padding: float,
                                       predicate_arity: int, argument_index: int, vertex_position=None):
        """Calculate optimal hook position implementing maximum separation and tangency.
        
        For n-ary predicates, hooks should be:
        1. Maximally separated on the predicate boundary
        2. Positioned at tangent points to the incident lines of identity
        """
        import math
        
        # Calculate predicate boundary rectangle
        left = center_x - text_width / 2 - padding
        right = center_x + text_width / 2 + padding
        top = center_y - text_height / 2 - padding
        bottom = center_y + text_height / 2 + padding
        
        # For maximum separation, distribute hooks around the perimeter
        # Use the full perimeter for optimal spacing
        perimeter_points = self._calculate_perimeter_points(left, right, top, bottom, predicate_arity)
        
        if argument_index < len(perimeter_points):
            hook_x, hook_y = perimeter_points[argument_index]
            
            # If vertex position is available, adjust for tangency
            if vertex_position:
                hook_x, hook_y = self._adjust_for_tangency(
                    hook_x, hook_y, vertex_position, left, right, top, bottom
                )
            
            print(f"DEBUG: Optimal hook for predicate, arg {argument_index}: ({hook_x:.1f}, {hook_y:.1f})")
            return (hook_x, hook_y)
        
        # Fallback to left side if index out of range
        return (left, center_y)
    
    def _calculate_parsimonious_boundary_point(self, center_x: float, center_y: float,
                                             text_width: float, text_height: float, 
                                             padding: float, vertex_position):
        """Calculate boundary point that minimizes line length (parsimony principle).
        
        Find the point on the predicate boundary that is closest to the vertex.
        """
        vx, vy = vertex_position
        
        # Define predicate boundary rectangle
        left = center_x - text_width / 2 - padding
        right = center_x + text_width / 2 + padding
        top = center_y - text_height / 2 - padding
        bottom = center_y + text_height / 2 + padding
        
        # Find closest point on rectangle boundary to vertex
        # Clamp vertex coordinates to rectangle bounds
        closest_x = max(left, min(right, vx))
        closest_y = max(top, min(bottom, vy))
        
        # If vertex is inside rectangle, find closest edge
        if left < vx < right and top < vy < bottom:
            # Calculate distances to each edge
            dist_left = vx - left
            dist_right = right - vx
            dist_top = vy - top
            dist_bottom = bottom - vy
            
            min_dist = min(dist_left, dist_right, dist_top, dist_bottom)
            
            if min_dist == dist_left:
                closest_x, closest_y = left, vy
            elif min_dist == dist_right:
                closest_x, closest_y = right, vy
            elif min_dist == dist_top:
                closest_x, closest_y = vx, top
            else:
                closest_x, closest_y = vx, bottom
        
        print(f"DEBUG: Parsimonious boundary point: ({closest_x:.1f}, {closest_y:.1f}) for vertex at ({vx}, {vy})")
        return (closest_x, closest_y)
    
    def _calculate_perimeter_points(self, left: float, right: float, top: float, bottom: float, count: int):
        """Calculate evenly distributed points around rectangle perimeter for maximum hook separation."""
        import math
        
        # Calculate perimeter segments
        width = right - left
        height = bottom - top
        perimeter = 2 * (width + height)
        
        points = []
        for i in range(count):
            # Position along perimeter (0 to 1)
            t = i / count
            distance = t * perimeter
            
            # Determine which side of rectangle and position
            if distance <= width:  # Top edge
                x = left + distance
                y = top
            elif distance <= width + height:  # Right edge
                x = right
                y = top + (distance - width)
            elif distance <= 2 * width + height:  # Bottom edge
                x = right - (distance - width - height)
                y = bottom
            else:  # Left edge
                x = left
                y = bottom - (distance - 2 * width - height)
            
            points.append((x, y))
        
        return points
    
    def _adjust_for_tangency(self, hook_x: float, hook_y: float, vertex_position, 
                           left: float, right: float, top: float, bottom: float):
        """Adjust hook position for tangency to the incident line of identity."""
        vx, vy = vertex_position
        
        # Calculate direction vector from vertex to current hook position
        dx = hook_x - vx
        dy = hook_y - vy
        
        # Determine which edge the hook is on and adjust for tangency
        if abs(hook_y - top) < 1:  # Top edge
            # For tangency on horizontal edge, keep y constant, adjust x slightly
            return (hook_x, top)
        elif abs(hook_y - bottom) < 1:  # Bottom edge
            return (hook_x, bottom)
        elif abs(hook_x - left) < 1:  # Left edge
            # For tangency on vertical edge, keep x constant, adjust y slightly
            return (left, hook_y)
        elif abs(hook_x - right) < 1:  # Right edge
            return (right, hook_y)
        
        # Default: return original position
        return (hook_x, hook_y)
    
    def _get_vertex_argument_index(self, vertex_id: str, predicate_id: str) -> int:
        """Get the argument index (0-based) of a vertex within a predicate's argument list.
        
        This is used for separated hook positioning in n-ary predicates.
        """
        if not self.egi:
            return 0
        
        # Find the vertex sequence for this predicate in the nu mapping
        for edge_id, vertex_sequence in self.egi.nu.items():
            if edge_id == predicate_id:
                try:
                    return vertex_sequence.index(vertex_id)
                except ValueError:
                    # Vertex not found in this predicate's sequence
                    return 0
        
        return 0  # Default to first argument
    
    # OBSOLETE METHOD REMOVED: _draw_curved_ligature
    # This method was used for the old curved ligature system and is no longer needed
    # Future curved/bendable ligature support will be implemented with external libraries
                    
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
        sel_state = self.selection_system.selection_state
        # Render hover effect first (underneath selection), using per-type halos
        if sel_state.hover_element and sel_state.hover_element not in sel_state.selected_elements:
            hover_primitive = next((p for p in self.spatial_primitives if p.element_id == sel_state.hover_element), None)
            if hover_primitive:
                hover_fill = QColor(128, 128, 128, 30)
                hover_border = QColor(128, 128, 128, 120)
                painter.setBrush(QBrush(hover_fill))
                painter.setPen(QPen(hover_border, 1, Qt.DashLine))

                et = hover_primitive.element_type
                if et == 'edge':
                    return  # ignore edges for hover visuals
                if et == 'vertex':
                    cx, cy = hover_primitive.position
                    wx, wy = self._canvas_to_widget_pt(cx, cy)
                    painter.drawEllipse(QPointF(wx, wy), 12, 12)
                elif et == 'predicate':
                    rect = self._predicate_label_rect(hover_primitive.element_id, hover_primitive)
                    if rect:
                        pad = 3
                        wrect = self._canvas_rect_to_widget(rect).adjusted(-pad, -pad, pad, pad)
                        painter.drawRoundedRect(wrect, 4, 4)
                elif et == 'edge' and getattr(hover_primitive, 'curve_points', None):
                    pts = [self._canvas_to_widget_pt(px, py) for (px, py) in hover_primitive.curve_points]
                    if len(pts) >= 2:
                        path = QPainterPath(QPointF(pts[0][0], pts[0][1]))
                        for (px, py) in pts[1:]:
                            path.lineTo(QPointF(px, py))
                        painter.setPen(QPen(QColor(255, 165, 0, 200), 8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                        painter.setBrush(Qt.NoBrush)
                        painter.drawPath(path)
                elif et == 'cut':
                    x1, y1, x2, y2 = hover_primitive.bounds
                    (wx1, wy1) = self._canvas_to_widget_pt(x1, y1)
                    (wx2, wy2) = self._canvas_to_widget_pt(x2, y2)
                    pad = 2
                    painter.drawEllipse(QRectF(min(wx1, wx2) - pad, min(wy1, wy2) - pad,
                                               abs(wx2 - wx1) + 2*pad, abs(wy2 - wy1) + 2*pad))
                # Ignore all other primitive types for hover visuals
        
        # Render selection overlays
        if not sel_state.selected_elements:
            return
        
        # Mode-aware selection colors
        if self.current_mode == Mode.WARMUP:
            selection_color = QColor(0, 122, 255, 80)  # Blue with transparency
            border_color = QColor(0, 122, 255, 200)
        else:
            selection_color = QColor(40, 167, 69, 80)  # Green with transparency
            border_color = QColor(40, 167, 69, 200)

        painter.setPen(QPen(border_color, 3, Qt.SolidLine))
        painter.setBrush(QBrush(selection_color))

        for element_id in sel_state.selected_elements:
            primitive = next((p for p in self.spatial_primitives if p.element_id == element_id), None)
            if not primitive:
                continue
            et = primitive.element_type
            if et == 'edge':
                continue  # ignore edges for selection visuals
            x1, y1, x2, y2 = primitive.bounds
            if et == 'vertex':
                cx, cy = primitive.position
                wx, wy = self._canvas_to_widget_pt(cx, cy)
                painter.drawEllipse(QPointF(wx, wy), 14, 14)
            elif et == 'predicate':
                rect = self._predicate_label_rect(element_id, primitive)
                if rect:
                    pad = 4
                    wrect = self._canvas_rect_to_widget(rect).adjusted(-pad, -pad, pad, pad)
                    painter.drawRoundedRect(wrect, 4, 4)
            elif et == 'cut':
                painter.setPen(QPen(border_color, 4, Qt.SolidLine))
                painter.setBrush(Qt.NoBrush)
                pad = 3
                (wx1, wy1) = self._canvas_to_widget_pt(x1, y1)
                (wx2, wy2) = self._canvas_to_widget_pt(x2, y2)
                painter.drawEllipse(QRectF(min(wx1, wx2) - pad, min(wy1, wy2) - pad,
                                           abs(wx2 - wx1) + 2*pad, abs(wy2 - wy1) + 2*pad))
                painter.setPen(QPen(border_color, 3, Qt.SolidLine))
                painter.setBrush(QBrush(selection_color))
            elif et == 'edge' and getattr(primitive, 'curve_points', None):
                pts = [self._canvas_to_widget_pt(px, py) for (px, py) in primitive.curve_points]
                if len(pts) >= 2:
                    path = QPainterPath(QPointF(pts[0][0], pts[0][1]))
                    for (px, py) in pts[1:]:
                        path.lineTo(QPointF(px, py))
                    painter.setPen(QPen(border_color, 8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                    painter.setBrush(Qt.NoBrush)
                    painter.drawPath(path)
            # Ignore all other primitive types for selection visuals

        # Draw ghost line during attach-from-vertex drag
        if isinstance(getattr(self, 'drag_state', None), dict) and self.drag_state.get('type') == 'attach_from_vertex':
            vertex_id = self.drag_state.get('vertex_id')
            vprim = next((p for p in self.spatial_primitives if p.element_id == vertex_id), None)
            if vprim and vprim.position and getattr(self, '_last_mouse_widget_pos', None):
                vx, vy = vprim.position
                mwx, mwy = self._last_mouse_widget_pos
                mcx, mcy = self._widget_to_canvas_pt(mwx, mwy)
                (wvx, wvy) = self._canvas_to_widget_pt(vx, vy)
                # If hovering a predicate, snap to periphery point for preview
                drop_id = self._find_element_at_position(mcx, mcy)
                snap_wx, snap_wy = mwx, mwy
                if drop_id:
                    pred_prim = next((p for p in self.spatial_primitives if p.element_id == drop_id and p.element_type == 'predicate'), None)
                    if pred_prim:
                        rect = self._predicate_label_rect(pred_prim.element_id, pred_prim)
                        # Compute intersection of segment (vx,vy)->(rect center) with rect periphery
                        cx, cy = rect.center().x(), rect.center().y()
                        rx1, ry1, rx2, ry2 = rect.left(), rect.top(), rect.right(), rect.bottom()
                        ix, iy = cx, cy
                        dx, dy = cx - vx, cy - vy
                        # Avoid zero
                        if abs(dx) < 1e-6 and abs(dy) < 1e-6:
                            dx = 1e-6
                        t_candidates = []
                        # Intersect with vertical sides
                        if abs(dx) > 1e-6:
                            t = (rx1 - vx) / dx
                            yint = vy + t * dy
                            if 0.0 <= t <= 1.0 and ry1 <= yint <= ry2:
                                t_candidates.append((t, rx1, yint))
                            t = (rx2 - vx) / dx
                            yint = vy + t * dy
                            if 0.0 <= t <= 1.0 and ry1 <= yint <= ry2:
                                t_candidates.append((t, rx2, yint))
                        # Intersect with horizontal sides
                        if abs(dy) > 1e-6:
                            t = (ry1 - vy) / dy
                            xint = vx + t * dx
                            if 0.0 <= t <= 1.0 and rx1 <= xint <= rx2:
                                t_candidates.append((t, xint, ry1))
                            t = (ry2 - vy) / dy
                            xint = vx + t * dx
                            if 0.0 <= t <= 1.0 and rx1 <= xint <= rx2:
                                t_candidates.append((t, xint, ry2))
                        if t_candidates:
                            t_candidates.sort(key=lambda v: v[0])
                            ix, iy = t_candidates[0][1], t_candidates[0][2]
                            snap_wx, snap_wy = self._canvas_to_widget_pt(ix, iy)
                            # Draw snap marker
                            painter.setPen(QPen(QColor(0, 128, 255, 200), 2))
                            painter.setBrush(QBrush(QColor(0, 128, 255, 120)))
                            painter.drawEllipse(QPointF(snap_wx, snap_wy), 5, 5)
                painter.setPen(QPen(QColor(255, 165, 0, 180), 3, Qt.DashLine, Qt.RoundCap, Qt.RoundJoin))
                painter.setBrush(Qt.NoBrush)
                painter.drawLine(QPointF(wvx, wvy), QPointF(snap_wx, snap_wy))

    def mousePressEvent(self, event):
        """Start drag gestures, including attach-from-vertex."""
        if event.button() == Qt.LeftButton:
            pos = event.position() if hasattr(event, 'position') else event.localPos()
            wx, wy = float(pos.x()), float(pos.y())
            cx, cy = self._widget_to_canvas_pt(wx, wy)
            hit_id = self._find_element_at_position(cx, cy)
            if hit_id:
                # If clicked a vertex, start attach drag from that vertex
                prim = next((p for p in self.spatial_primitives if p.element_id == hit_id), None)
                if prim and prim.element_type == 'vertex':
                    self.drag_state = {'type': 'attach_from_vertex', 'vertex_id': hit_id}
                    self._last_mouse_widget_pos = (wx, wy)
                    self.update()
                    return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse movement for hover effects and marquee updates."""
        # Track last mouse widget pos for ghost previews
        pos = event.position() if hasattr(event, 'position') else event.localPos()
        self._last_mouse_widget_pos = (float(pos.x()), float(pos.y()))
        if self._marquee_active and self._marquee_start:
            self._marquee_end = (float(pos.x()), float(pos.y()))
            self.update()
            return
        # If dragging a vertex for attachment, update cursor feedback only
        if isinstance(getattr(self, 'drag_state', None), dict) and self.drag_state.get('type') == 'attach_from_vertex':
            # Convert to canvas coords for hit-testing
            wx, wy = float(pos.x()), float(pos.y())
            x, y = self._widget_to_canvas_pt(wx, wy)
            hovered_element = self._find_element_at_position(x, y)
            if hovered_element and hovered_element in getattr(self.egi, 'nu', {}):
                self.setCursor(QCursor(Qt.CrossCursor))
            else:
                self.setCursor(QCursor(Qt.PointingHandCursor))
            return
        # Update hover states when not marquee-selecting
        wx, wy = float(pos.x()), float(pos.y())
        x, y = self._widget_to_canvas_pt(wx, wy)
        # Branching point hover (higher priority)
        hovered_bp = self._find_branching_point_at_position(x, y)
        self.hover_branching_point = hovered_bp
        # Element hover via hit-test
        hovered_element = self._find_element_at_position(x, y)
        prev_hover = self.selection_system.selection_state.hover_element
        if hovered_element != prev_hover:
            self.selection_system.selection_state.hover_element = hovered_element
            self.update()
        # Cursor feedback
        if hovered_bp or hovered_element:
            self.setCursor(QCursor(Qt.PointingHandCursor))
        else:
            self.setCursor(QCursor(Qt.ArrowCursor))
        
        super().mouseMoveEvent(event)
    
    def _find_branching_point_at_position(self, x: float, y: float) -> Optional[str]:
        """Find branching point at given position for selection.
        x,y are in canvas coordinates. Hit radius is scaled from 8 screen px to canvas units."""
        sx, sy, _, _ = self._compute_transform()
        s = max((sx + sy) * 0.5, 1e-6)
        hit_radius = 8.0 / s  # convert 8px to canvas units
        
        for vertex_id, (bp_x, bp_y, vertex_name) in self.branching_points.items():
            distance = ((x - bp_x) ** 2 + (y - bp_y) ** 2) ** 0.5
            if distance <= hit_radius:
                return vertex_id
        
        return None

    def _find_candidates_at_position(self, x: float, y: float) -> List[str]:
        """Return all selectable element IDs under point (x,y) in priority order.
        Priority: branching point > vertex > predicate (label bounds) > cut boundary > other.
        """
        candidates: List[Tuple[int, str]] = []  # (priority, element_id)
        # 0) Branching point first
        bp = self._find_branching_point_at_position(x, y)
        if bp:
            candidates.append((0, bp))
        # 1) Iterate primitives to test
        for p in self.spatial_primitives:
            x1, y1, x2, y2 = p.bounds
            et = p.element_type
            # Vertex: near small radius around position
            if et == 'vertex':
                bx, by = p.position
                dist = ((x - bx) ** 2 + (y - by) ** 2) ** 0.5
                if dist <= 8.0:
                    candidates.append((1, p.element_id))
                continue
            # Predicate: prefer label bounds if available
            if et == 'predicate':
                rect = self._predicate_text_bounds.get(p.element_id)
                if rect and rect.adjusted(-3, -3, 3, 3).contains(x, y):
                    candidates.append((2, p.element_id))
                    continue
                # fallback to primitive bounds
                if x1 <= x <= x2 and y1 <= y <= y2:
                    candidates.append((3, p.element_id))
                continue
            # Cut: boundary proximity only
            if et == 'cut':
                if (x1 <= x <= x2 and y1 <= y <= y2):
                    sx, sy, _, _ = self._compute_transform()
                    s = max((sx + sy) * 0.5, 1e-6)
                    margin = 10 / s
                    d = min(abs(x - x1), abs(x - x2), abs(y - y1), abs(y - y2))
                    if d <= margin:
                        candidates.append((4, p.element_id))
                continue
            # Other types: rectangular hit-test
            if x1 <= x <= x2 and y1 <= y <= y2:
                candidates.append((5, p.element_id))
        # Sort by priority and return IDs
        candidates.sort(key=lambda t: t[0])
        return [eid for _, eid in candidates]
            
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release to finalize marquee selection."""
        if event.button() == Qt.LeftButton and self._marquee_active and self._marquee_start and self._marquee_end:
            x1, y1 = self._marquee_start
            x2, y2 = self._marquee_end
            left, top = min(x1, x2), min(y1, y2)
            right, bottom = max(x1, x2), max(y1, y2)
            # Add all primitives whose bounds are fully inside the marquee
            added: List[str] = []
            for p in self.spatial_primitives:
                bx1, by1, bx2, by2 = p.bounds
                if bx1 >= left and by1 >= top and bx2 <= right and by2 <= bottom:
                    # Add without toggling existing ones
                    self.selection_system.selection_state.selected_elements.add(p.element_id)
                    added.append(p.element_id)
            if added:
                print(f"✓ Marquee added {len(added)} elements")
            # Reset marquee
            self._marquee_active = False
            self._marquee_start = None
            self._marquee_end = None
            self.update()
            return
        # Handle drop for attach-from-vertex gesture
        if event.button() == Qt.LeftButton and isinstance(getattr(self, 'drag_state', None), dict):
            if self.drag_state.get('type') == 'attach_from_vertex':
                pos = event.position() if hasattr(event, 'position') else event.localPos()
                wx, wy = float(pos.x()), float(pos.y())
                cx, cy = self._widget_to_canvas_pt(wx, wy)
                drop_id = self._find_element_at_position(cx, cy)
                vertex_id = self.drag_state.get('vertex_id')
                self.drag_state = None
                if drop_id and vertex_id:
                    # If dropped on a predicate, attach via controller and update EGI
                    # Recognize predicate by presence in rel mapping or by primitive type
                    is_pred = False
                    try:
                        is_pred = (drop_id in self.egi.rel)
                    except Exception:
                        is_pred = False
                    if not is_pred:
                        prim = next((p for p in self.spatial_primitives if p.element_id == drop_id), None)
                        is_pred = bool(prim and prim.element_type == 'predicate')
                    if is_pred:
                        # Choose hook_position: prefer first empty slot in ν, else append at end
                        current = list(self.egi.nu.get(drop_id, ()))
                        try:
                            empty_index = current.index(None)
                            hook_pos = empty_index
                        except ValueError:
                            hook_pos = len(current)
                        # Map UI mode to controller mode string
                        mode_str = "practice" if getattr(self, 'current_mode', None) and self.current_mode.name.upper() == "PRACTICE" else "playground"
                        ok, errs = self.diagram_controller.attach_loi_endpoint_transactional(vertex_id, drop_id, hook_pos, mode=mode_str)
                        if ok:
                            self.egi = self.diagram_controller.egi
                            print(f"✓ Attached vertex {vertex_id} to predicate {drop_id} at hook {hook_pos} [{mode_str}]")
                            self.update()
                        else:
                            print(f"✗ Attach failed for vertex {vertex_id} → {drop_id}: {'; '.join(errs) if errs else 'unknown error'}")
                return

    def keyPressEvent(self, event):
        """Keyboard shortcuts for selection (Cmd/Ctrl+A selects all in current area)."""
        # Delete selected identity edges (lines of identity) transactionally
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            selected_ids = set(self.selection_system.selection_state.selected_elements)
            if not selected_ids:
                return
            # Filter identity edges only
            to_delete = []
            for eid in selected_ids:
                try:
                    if self.egi.rel.get(eid) == "=":
                        to_delete.append(eid)
                except Exception:
                    continue
            if to_delete:
                mode_str = "practice" if getattr(self, 'current_mode', None) and self.current_mode.name.upper() == "PRACTICE" else "playground"
                success = 0
                for edge_id in to_delete:
                    ok, errs = self.diagram_controller.delete_identity_edge_transactional(edge_id, mode=mode_str)
                    if ok:
                        success += 1
                    else:
                        print(f"✗ Delete failed for identity edge {edge_id}: {'; '.join(errs) if errs else 'unknown error'}")
                if success:
                    self.egi = self.diagram_controller.egi
                    # Remove deleted ids from selection
                    self.selection_system.selection_state.selected_elements.difference_update(to_delete)
                    print(f"✓ Deleted {success} identity edge(s) [{mode_str}]")
                    self.update()
            return
        if (event.key() == Qt.Key_A) and ((event.modifiers() & Qt.ControlModifier) or (event.modifiers() & Qt.MetaModifier)):
            # Determine current area: if mouse is inside a cut, select all inside innermost cut; else select all on sheet
            cursor_pos = self.mapFromGlobal(QCursor.pos())
            x, y = float(cursor_pos.x()), float(cursor_pos.y())
            area_cut_id = self._innermost_cut_at(x, y)
            count = 0
            for p in self.spatial_primitives:
                if area_cut_id:
                    if self._element_inside_cut(p, area_cut_id):
                        self.selection_system.selection_state.selected_elements.add(p.element_id)
                        count += 1
                else:
                    # Sheet elements = not inside any cut
                    if not self._element_inside_any_cut(p):
                        self.selection_system.selection_state.selected_elements.add(p.element_id)
                        count += 1
            print(f"✓ Selected {count} elements in current area")
            self.update()
        else:
            super().keyPressEvent(event)

    def _element_inside_cut(self, primitive: SpatialPrimitive, cut_id: str) -> bool:
        cut_prim = next((c for c in self.spatial_primitives if c.element_id == cut_id), None)
        if not cut_prim or not cut_prim.bounds:
            return False
        x1, y1, x2, y2 = cut_prim.bounds
        bx1, by1, bx2, by2 = primitive.bounds
        return bx1 >= x1 and by1 >= y1 and bx2 <= x2 and by2 <= y2

    def _element_inside_any_cut(self, primitive: SpatialPrimitive) -> bool:
        for c in self.spatial_primitives:
            if c.element_type == "cut" and c.bounds:
                if self._element_inside_cut(primitive, c.element_id):
                    return True
        return False

    def _innermost_cut_at(self, x: float, y: float) -> Optional[str]:
        """Return the innermost cut whose bounds contain the point (x, y)."""
        containing: List[Tuple[str, float]] = []  # (id, area)
        for c in self.spatial_primitives:
            if c.element_type != "cut" or not c.bounds:
                continue
            x1, y1, x2, y2 = c.bounds
            if x1 <= x <= x2 and y1 <= y <= y2:
                containing.append((c.element_id, (x2-x1)*(y2-y1)))
        if not containing:
            return None
        containing.sort(key=lambda t: t[1])
        return containing[0][0]

    def _dist_point_to_seg(self, px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
        """Distance from point P to segment AB in canvas coords."""
        vx, vy = bx - ax, by - ay
        wx, wy = px - ax, py - ay
        denom = vx*vx + vy*vy
        if denom <= 1e-12:
            # Degenerate segment
            dx, dy = px - ax, py - ay
            return (dx*dx + dy*dy) ** 0.5
        t = max(0.0, min(1.0, (wx*vx + wy*vy) / denom))
        cx, cy = ax + t * vx, ay + t * vy
        dx, dy = px - cx, py - cy
        return (dx*dx + dy*dy) ** 0.5

    def _edge_hit(self, primitive, x: float, y: float) -> bool:
        """Return True if (x,y) is within threshold of an edge polyline in canvas coords."""
        pts = getattr(primitive, 'curve_points', None)
        if not pts or len(pts) < 2:
            return False
        # Convert a 8px screen threshold to canvas units
        sx, sy, _, _ = self._compute_transform()
        s = max((sx + sy) * 0.5, 1e-6)
        thresh = 8.0 / s
        for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
            if self._dist_point_to_seg(x, y, ax, ay, bx, by) <= thresh:
                return True
        return False

    def _find_element_at_position(self, x: float, y: float) -> Optional[str]:
        """Find best element under (x,y) using actual rendered positions.
        This fixes the issue where spatial primitives have incorrect positions.
        """
        # Add occasional debug output
        if hasattr(self, '_hover_debug_counter'):
            self._hover_debug_counter += 1
        else:
            self._hover_debug_counter = 0
        
        debug_this = (self._hover_debug_counter % 50 == 0)  # Every 50th call
        if debug_this:
            print(f"DEBUG: Hover test at ({x:.1f}, {y:.1f})")
        
        candidates: List[Tuple[float, str]] = []  # (distance, element_id)
        
        # Build actual rendered positions (same as renderer uses)
        vertex_positions: Dict[str, Tuple[float, float]] = {}
        predicate_positions: Dict[str, Tuple[float, float]] = {}
        
        for p in self.spatial_primitives:
            if p.element_type == "vertex":
                vertex_positions[p.element_id] = p.position
            elif p.element_type == "predicate":
                predicate_positions[p.element_id] = p.position
        
        if debug_this:
            print(f"DEBUG: Found {len(vertex_positions)} vertices, {len(predicate_positions)} predicates")
        
        # Test predicates using their label rectangles
        for p in self.spatial_primitives:
            if p.element_type == 'predicate':
                # This is a predicate primitive - use text label rectangle
                rect = self._predicate_text_bounds.get(p.element_id)
                if rect is None:
                    rect = self._predicate_label_rect(p.element_id, p)
                if rect:
                    expanded = rect.adjusted(-8, -8, 8, 8)
                    if expanded.contains(x, y):
                        relation = self.egi.rel.get(p.element_id, "UNKNOWN")
                        candidates.append((0.0, p.element_id))
                        print(f"DEBUG: Found predicate {p.element_id} ({relation})")
                elif debug_this:
                    print(f"DEBUG: Predicate {p.element_id} has no rect")
        
        # Test ligatures using actual rendered paths (from branching points)
        for edge_id, vertex_sequence in self.egi.nu.items():
            if edge_id in predicate_positions:
                # This is a predicate edge - compute actual ligature paths
                pred_rect = self._predicate_text_bounds.get(edge_id)
                if not pred_rect:
                    continue
                
                # Test each vertex-to-predicate connection
                for vertex_id in vertex_sequence:
                    # Use actual branching point position, not spatial primitive position
                    if vertex_id in self.branching_points:
                        vx, vy, _ = self.branching_points[vertex_id]
                        
                        # Compute hook point (same as renderer)
                        cx, cy = pred_rect.center().x(), pred_rect.center().y()
                        num_args = len(vertex_sequence)
                        
                        if num_args == 2:
                            idx = list(vertex_sequence).index(vertex_id)
                            if idx == 0:
                                hook_x, hook_y = pred_rect.left(), cy
                            else:
                                hook_x, hook_y = pred_rect.right(), cy
                        else:
                            hook_pt = self._intersect_rect_periphery(pred_rect, QPointF(cx, cy), QPointF(vx, vy))
                            if hook_pt is None:
                                continue
                            hook_x, hook_y = hook_pt.x(), hook_pt.y()
                        
                        # Test distance to line segment
                        d = self._dist_point_to_seg(x, y, vx, vy, hook_x, hook_y)
                        if d <= 8.0:  # 8px threshold
                            ligature_id = f"ligature_{vertex_id}_{edge_id}"
                            candidates.append((d, ligature_id))
                            print(f"DEBUG: Found ligature {vertex_id}->{edge_id}, distance={d:.1f}")
                    elif debug_this:
                        print(f"DEBUG: No branching point for vertex {vertex_id}")
        
        # Test cuts
        sx, sy, _, _ = self._compute_transform()
        s = max((sx + sy) * 0.5, 1e-6)
        for p in self.spatial_primitives:
            if p.element_type == 'cut' and p.bounds:
                x1, y1, x2, y2 = p.bounds
                if x1 <= x <= x2 and y1 <= y <= y2:
                    d_canvas = min(abs(x - x1), abs(x - x2), abs(y - y1), abs(y - y2))
                    d_px = d_canvas * s
                    if d_px <= 14.0:
                        candidates.append((d_px + 100.0, p.element_id))  # Lower priority
        
        if candidates:
            candidates.sort(key=lambda t: t[0])
            return candidates[0][1]
        return None

    def _reconstruct_ligature_path(self, ligature_id: str) -> List[Tuple[float, float]]:
        """Reconstruct the actual ligature path that matches rendering.
        For synthetic ligature edges like 'edge_v_xxx_e_yyy', extract vertex and predicate
        and compute the same vertex-to-hook path that the renderer draws.
        """
        if not ligature_id.startswith('edge_'):
            return []
        
        # Parse synthetic ligature ID: 'edge_v_xxx_e_yyy' -> vertex_id='v_xxx', predicate_id='e_yyy'
        parts = ligature_id.split('_')
        if len(parts) < 4:
            return []
        
        try:
            vertex_id = f"{parts[1]}_{parts[2]}"  # 'v_xxx'
            predicate_id = f"{parts[3]}_{parts[4]}"  # 'e_yyy'
        except IndexError:
            return []
        
        # Debug output (remove after testing)
        if hasattr(self, '_debug_ligature_counter'):
            self._debug_ligature_counter += 1
        else:
            self._debug_ligature_counter = 0
        if self._debug_ligature_counter < 3:  # Only first few calls
            print(f"DEBUG: Reconstructing {ligature_id} -> {vertex_id} to {predicate_id}")
        
        # Find vertex position
        vertex_prim = next((p for p in self.spatial_primitives if p.element_id == vertex_id), None)
        if not vertex_prim or not vertex_prim.position:
            return []
        vx, vy = vertex_prim.position
        
        # Find predicate position and compute hook point (same logic as renderer)
        predicate_prim = next((p for p in self.spatial_primitives if p.element_id == predicate_id), None)
        if not predicate_prim or not predicate_prim.position:
            return []
        
        # Get predicate label rect (same as renderer)
        rect = self._predicate_label_rect(predicate_id, predicate_prim)
        if not rect:
            return []
        
        # Get vertex sequence for this predicate to determine hook position
        vertex_seq = self.egi.nu.get(predicate_id, ())
        if vertex_id not in vertex_seq:
            return []
        
        cx, cy = rect.center().x(), rect.center().y()
        num_args = len(vertex_seq)
        
        # Compute hook point (same logic as renderer)
        if num_args == 2:
            # Left midpoint for arg 0, right midpoint for arg 1 (ν order)
            idx = vertex_seq.index(vertex_id)
            if idx == 0:
                hook_x, hook_y = rect.left(), cy
            else:
                hook_x, hook_y = rect.right(), cy
        else:
            # General case: intersect ray center->vertex with rect border
            hook_pt = self._intersect_rect_periphery(rect, QPointF(cx, cy), QPointF(vx, vy))
            if hook_pt is None:
                return []
            hook_x, hook_y = hook_pt.x(), hook_pt.y()
        
        # Return path from vertex to hook (matches renderer)
        return [(vx, vy), (hook_x, hook_y)]

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
        
        # Unified examples dropdown (corpus + built-in) and EGIF editor field
        controls_layout.addWidget(QLabel("Examples:"))
        self.examples_combo = QComboBox()
        self.examples_combo.addItem("Select an example EGIF...")
        self._populate_examples_dropdown()
        self.examples_combo.currentIndexChanged.connect(self.on_example_selected)
        controls_layout.addWidget(self.examples_combo)

        # Separator
        controls_layout.addWidget(QLabel("|"))

        # EGIF text field (distinct display of the expression to render)
        controls_layout.addWidget(QLabel("EGIF:"))
        self.egif_text = QTextEdit()
        self.egif_text.setPlaceholderText("Enter or edit EGIF here…")
        self.egif_text.setFixedHeight(60)
        controls_layout.addWidget(self.egif_text)
        
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
        
    def on_example_selected(self, index: int):
        """When the user picks an example, load its EGIF into the text field."""
        if index <= 0:
            return
        egif = self.examples_combo.currentData()
        if isinstance(egif, str) and egif.strip():
            self.egif_text.setPlainText(egif)
            
    def render_diagram(self):
        """Render diagram from current EGIF using Phase 1d pipeline."""
        egif_text = self.egif_text.toPlainText().strip()
        
        if not egif_text:
            self.status_bar.showMessage("Enter EGIF to render")
            return
            
        try:
            # Phase 1d Pipeline: EGIF → EGI → Layout → Visual
            
            # 1. Parse EGIF to EGI
            egif_parser = EGIFParser(egif_text)
            egi = egif_parser.parse()
            
            # 2. Generate canonical layout for deterministic rendering
            layout_engine = GraphvizLayoutEngine()
            layout_result = layout_engine.create_layout_from_graph(egi)
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
        sel_state = self.diagram_widget.selection_system.selection_state
        selected = sel_state.selected_elements
        hover = sel_state.hover_element
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
        
    def _populate_examples_dropdown(self):
        """Populate the unified examples dropdown from corpus and built-ins."""
        # Add corpus examples first (only those with valid EGIF)
        if self.corpus_loader:
            # Sort by category then title
            examples = sorted(self.corpus_loader.examples.values(), key=lambda e: (e.category, e.title))
            for ex in examples:
                if ex.egif_content and ex.egif_content.strip():
                    display_text = f"[{ex.category}] {ex.title}"
                    self.examples_combo.addItem(display_text, ex.egif_content)
        
        # Add built-in sample EGIFs (if any) under a label prefix
        if self.sample_egifs:
            for s in self.sample_egifs:
                display_text = f"[Samples] {s[:40]}"  # preview
                self.examples_combo.addItem(display_text, s)
    
    # import_corpus_example is no longer needed; examples are unified
    
    def load_sample_diagram(self):
        """Load the Socrates sample diagram on startup for branching point testing."""
        if self.sample_egifs:
            # Preload a default example into the EGIF field (no auto-render)
            socrates_egif = '(Human "Socrates") (Mortal "Socrates")'
            self.egif_text.setPlainText(socrates_egif)

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
