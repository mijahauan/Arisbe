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
    from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QMouseEvent, QPainterPath, QFontMetrics, QFontMetricsF
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
            self.selected_elements = set()
            self.hover_element = None
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
        
        # LAYER 1: Render cuts first (background)
        for primitive in self.spatial_primitives:
            if primitive.element_type == "cut":
                self._render_primitive(painter, primitive)
        
        # LAYER 2: Render heavy ligatures (middle layer)
        self._render_simple_working_ligatures(painter)
        
        # LAYER 3: Render predicates and vertices on top (foreground)
        for primitive in self.spatial_primitives:
            if primitive.element_type in ["predicate", "vertex"]:
                self._render_primitive(painter, primitive)
            
        # Render annotations on top
        if self.show_annotations:
            self._render_annotations(painter)
            
        # Render mode-aware selection overlays
        self._render_selection_overlays(painter)

        # Draw marquee rectangle if active
        if self._marquee_active and self._marquee_start and self._marquee_end:
            x1, y1 = self._marquee_start
            x2, y2 = self._marquee_end
            left, top = min(x1, x2), min(y1, y2)
            w, h = abs(x2 - x1), abs(y2 - y1)
            painter.setPen(QPen(QColor(30,144,255), 1, Qt.DashLine))
            painter.setBrush(QBrush(QColor(30,144,255,40)))
            painter.drawRect(QRectF(left, top, w, h))
    
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
    
    def _post_process_ligature_layout(self):
        """Post-process Graphviz layout to handle EG-specific ligature requirements."""
        ligature_layout = {
            'ligatures': {},
            'reserved_spaces': []  # Track reserved space for collision avoidance
        }
        
        # Build vertex-to-predicates mapping
        vertex_connections = {}
        for predicate_id, vertex_sequence in self.egi.nu.items():
            for vertex_id in vertex_sequence:
                if vertex_id not in vertex_connections:
                    vertex_connections[vertex_id] = []
                vertex_connections[vertex_id].append(predicate_id)
        
        print(f"DEBUG: Post-processing ligatures from nu mapping: {dict(self.egi.nu)}")
        print(f"DEBUG: Vertex connections: {vertex_connections}")
        
        # Debug: Check all vertices in EGI
        print(f"DEBUG: All vertices in EGI: {[(v.id, v.label, v.is_generic) for v in self.egi.V]}")
        
        # Debug: Check spatial primitives for vertices
        vertex_primitives = [p for p in self.spatial_primitives if p.element_type == 'vertex']
        print(f"DEBUG: Vertex spatial primitives: {[(p.element_id, p.position) for p in vertex_primitives]}")
        
        # Debug: Check if we have the expected 2 vertices for Loves example
        if len(self.egi.V) == 2 and len(vertex_connections) < 2:
            print(f"DEBUG: MISSING VERTEX BUG - EGI has {len(self.egi.V)} vertices but only {len(vertex_connections)} in connection mapping!")
            missing_vertices = [v.id for v in self.egi.V if v.id not in vertex_connections]
            print(f"DEBUG: Missing vertices from connection mapping: {missing_vertices}")
        
        # Process each ligature for EG-specific requirements
        for vertex_id, connected_predicates in vertex_connections.items():
            print(f"DEBUG: Processing vertex {vertex_id} with connections: {connected_predicates}")
            ligature_info = self._calculate_eg_ligature_layout(
                vertex_id, connected_predicates, ligature_layout['reserved_spaces']
            )
            
            if ligature_info:
                ligature_layout['ligatures'][vertex_id] = ligature_info
                
                # Reserve space to prevent collisions
                if ligature_info.get('reserved_space'):
                    ligature_layout['reserved_spaces'].append(ligature_info['reserved_space'])
        
        return ligature_layout
    
    def _calculate_eg_ligature_layout(self, vertex_id: str, connected_predicates: list, existing_spaces: list):
        """Calculate EG-specific ligature layout with collision avoidance."""
        # Get vertex position from spatial primitives
        vertex_pos = None
        for primitive in self.spatial_primitives:
            if primitive.element_id == vertex_id:
                vertex_pos = primitive.position
                break
        
        if not vertex_pos:
            print(f"DEBUG: Could not find position for vertex {vertex_id}")
            return None
        
        vx, vy = vertex_pos
        num_connections = len(connected_predicates)
        
        # Get vertex constant name if present
        vertex_name = None
        if self.egi:
            vertex = next((v for v in self.egi.V if v.id == vertex_id), None)
            if vertex and vertex.label and not vertex.is_generic:
                vertex_name = vertex.label
        
        ligature_info = {
            'vertex_id': vertex_id,
            'vertex_pos': vertex_pos,
            'connections': connected_predicates,
            'vertex_name': vertex_name,
            'render_type': None,
            'branch_point': None,
            'predicate_positions': [],
            'reserved_space': None
        }
        
        # Get all predicate positions for this vertex with argument indices for separated hooks
        pred_positions = []
        for pred_id in connected_predicates:
            # Determine argument index for this vertex in this predicate
            argument_index = self._get_vertex_argument_index(vertex_id, pred_id)
            pred_pos = self._get_predicate_position(pred_id, vertex_pos, argument_index)
            if pred_pos:
                pred_positions.append(pred_pos)
                print(f"DEBUG: Predicate {pred_id} hook for vertex {vertex_id} (arg {argument_index}): {pred_pos}")
            else:
                print(f"DEBUG: Could not find position for predicate {pred_id}")
        
        ligature_info['predicate_positions'] = pred_positions
        
        # Reserve space for constant name if present
        if vertex_name:
            font = QFont("Times", 12, QFont.Bold)
            font_metrics = QFontMetrics(font)
            text_rect = font_metrics.boundingRect(vertex_name)
            
            ligature_info['reserved_space'] = {
                'type': 'constant_name',
                'center': vertex_pos,
                'width': text_rect.width() + 8,
                'height': text_rect.height() + 8,
                'element_id': vertex_id
            }
        
        print(f"DEBUG: Ligature layout for {vertex_id}: {num_connections} connections, {len(pred_positions)} predicate positions")
        
        return ligature_info
    
    # OBSOLETE METHODS REMOVED: _calculate_collision_free_branch_point and _check_space_collision
    # These methods were used for the old curved ligature system and are no longer needed
    # The new ligature rendering system uses vertex positions directly per Dau's formalism
    
    def _render_processed_ligatures(self, painter: QPainter, ligature_layout):
        """Render ligatures using Dau's single-object ligature model."""
        # Set heavy line style for all ligatures
        painter.setPen(QPen(QColor(0, 0, 0), 4))  # Heavy line (Dau convention)
        
        for vertex_id, ligature_info in ligature_layout['ligatures'].items():
            self._render_single_object_ligature(painter, ligature_info)
    
    def _render_single_object_ligature(self, painter: QPainter, ligature_info):
        """Render a single-object ligature as one continuous line according to Dau's model.
        
        KEY PRINCIPLE: Each line of identity is ONE continuous geometric entity.
        Branch points and constant labels are features ON the line, not separate segments.
        """
        vertex_id = ligature_info['vertex_id']
        vertex_pos = ligature_info['vertex_pos']
        connected_predicates = ligature_info['connections']
        vertex_name = ligature_info['vertex_name']
        predicate_positions = ligature_info['predicate_positions']
        
        vx, vy = vertex_pos
        num_connections = len(connected_predicates)
        
        # CRITICAL: Ensure ALL ligatures use heavy line style
        painter.setPen(QPen(QColor(0, 0, 0), 4))  # Heavy line (Dau convention)
        
        print(f"DEBUG: Rendering single continuous ligature for vertex {vertex_id} at ({vx},{vy}) with {num_connections} connections")
        
        # Generate the continuous ligature path based on connection pattern
        ligature_path = self._generate_continuous_ligature_path(vertex_pos, predicate_positions, num_connections)
        
        # Render the single continuous line
        self._draw_continuous_ligature_path(painter, ligature_path)
        
        # Render vertex spot and label as features ON the line
        self._render_vertex_spot(painter, vx, vy, vertex_name, vertex_id)
        
        print(f"DEBUG: Rendered continuous ligature with {len(ligature_path)} path points")
    
    def _generate_continuous_ligature_path(self, vertex_pos, predicate_positions, num_connections):
        """Generate a continuous path for the ligature based on connection pattern.
        
        Returns a list of points that define the single continuous line of identity.
        The vertex position is a point ON this line, not a connection between segments.
        """
        vx, vy = vertex_pos
        
        if num_connections == 0:
            # Standalone vertex - horizontal line centered on vertex
            line_length = 40
            return [(vx - line_length/2, vy), (vx, vy), (vx + line_length/2, vy)]
            
        elif num_connections == 1:
            # Single connection - line from predicate through vertex and extending
            if predicate_positions:
                pred_x, pred_y = predicate_positions[0]
                # Extend line beyond vertex for visual completeness
                dx = vx - pred_x
                dy = vy - pred_y
                length = (dx*dx + dy*dy)**0.5
                if length > 0:
                    # Normalize and extend
                    dx_norm = dx / length
                    dy_norm = dy / length
                    extension = 20  # Extension beyond vertex
                    end_x = vx + dx_norm * extension
                    end_y = vy + dy_norm * extension
                    return [(pred_x, pred_y), (vx, vy), (end_x, end_y)]
                else:
                    return [(pred_x, pred_y), (vx, vy)]
            return [(vx, vy)]
            
        elif num_connections == 2:
            # Two connections - use Graphviz-computed spline path for collision-free routing
            if len(predicate_positions) >= 2:
                pred1_pos = predicate_positions[0]
                pred2_pos = predicate_positions[1]
                
                # Try to get Graphviz spline path for this ligature
                spline_path = self._get_graphviz_spline_path(vertex_pos, predicate_positions)
                if spline_path:
                    print(f"DEBUG: Using Graphviz spline path with {len(spline_path)} points")
                    return spline_path
                else:
                    # Fallback to direct path if no spline available
                    print("DEBUG: No Graphviz spline found, using direct path")
                    return [pred1_pos, (vx, vy), pred2_pos]
            return [(vx, vy)]
            
        else:
            # 3+ connections - star pattern with vertex as central branching point
            # Create a path that visits all predicates through the central vertex
            path = []
            if predicate_positions:
                # Start from first predicate, go to vertex, then to each other predicate
                path.append(predicate_positions[0])
                path.append((vx, vy))
                for pred_pos in predicate_positions[1:]:
                    path.append(pred_pos)
                    path.append((vx, vy))  # Return to vertex between branches
            return path
    
    def _draw_continuous_ligature_path(self, painter: QPainter, path_points):
        """Draw a single continuous ligature path.
        
        The path represents one geometric entity - a line of identity.
        """
        if len(path_points) < 2:
            return
            
        # Draw the continuous path as connected line segments
        # In the future, this could be enhanced with smooth curves
        for i in range(len(path_points) - 1):
            start_point = QPointF(path_points[i][0], path_points[i][1])
            end_point = QPointF(path_points[i + 1][0], path_points[i + 1][1])
            painter.drawLine(start_point, end_point)
            
        print(f"DEBUG: Drew continuous ligature path with {len(path_points)} points")
    
    def _order_path_for_parsimony(self, points):
        """Order path points to minimize total line length (parsimony principle).
        
        For a 3-point path (pred1, vertex, pred2), determine the optimal order.
        """
        if len(points) != 3:
            return points
            
        pred1, vertex, pred2 = points
        
        # Calculate distances for both possible orderings
        # Order 1: pred1 -> vertex -> pred2
        dist1 = self._calculate_distance(pred1, vertex) + self._calculate_distance(vertex, pred2)
        
        # Order 2: pred2 -> vertex -> pred1  
        dist2 = self._calculate_distance(pred2, vertex) + self._calculate_distance(vertex, pred1)
        
        # Choose the order with minimum total distance
        if dist1 <= dist2:
            return [pred1, vertex, pred2]
        else:
            return [pred2, vertex, pred1]
    
    def _calculate_distance(self, point1, point2):
        """Calculate Euclidean distance between two points."""
        dx = point1[0] - point2[0]
        dy = point1[1] - point2[1]
        return (dx*dx + dy*dy)**0.5
    
    def _get_graphviz_spline_path(self, vertex_pos, predicate_positions):
        """Extract Graphviz-computed spline path for ligature routing.
        
        Leverages existing Graphviz spline routing instead of custom collision detection.
        Returns the spline path points if available, None otherwise.
        """
        # Check if we have spatial primitives with curve_points from Graphviz
        if not hasattr(self, 'spatial_primitives') or not self.spatial_primitives:
            return None
            
        # Look for edges that connect to this vertex position
        vertex_tolerance = 15.0  # Tolerance for matching vertex positions
        
        for primitive in self.spatial_primitives:
            if primitive.element_type == 'edge' and primitive.curve_points:
                # Check if this edge's curve passes near our vertex
                for i, curve_point in enumerate(primitive.curve_points):
                    vx, vy = vertex_pos
                    cx, cy = curve_point
                    
                    # If curve point is near vertex position, this might be our ligature
                    distance = ((vx - cx)**2 + (vy - cy)**2)**0.5
                    if distance <= vertex_tolerance:
                        print(f"DEBUG: Found Graphviz spline for vertex at {vertex_pos}, {len(primitive.curve_points)} points")
                        return primitive.curve_points
                        
        # Alternative: Look for edges that connect the predicates this vertex connects to
        if len(predicate_positions) >= 2:
            pred1_pos, pred2_pos = predicate_positions[0], predicate_positions[1]
            
            for primitive in self.spatial_primitives:
                if primitive.element_type == 'edge' and primitive.curve_points:
                    curve_points = primitive.curve_points
                    if len(curve_points) >= 2:
                        # Check if curve endpoints are near our predicate positions
                        start_point, end_point = curve_points[0], curve_points[-1]
                        
                        start_near_pred1 = self._points_near(start_point, pred1_pos, 20.0)
                        end_near_pred2 = self._points_near(end_point, pred2_pos, 20.0)
                        start_near_pred2 = self._points_near(start_point, pred2_pos, 20.0)
                        end_near_pred1 = self._points_near(end_point, pred1_pos, 20.0)
                        
                        if (start_near_pred1 and end_near_pred2) or (start_near_pred2 and end_near_pred1):
                            print(f"DEBUG: Found Graphviz spline connecting predicates, {len(curve_points)} points")
                            return curve_points
                            
        return None
    
    def _points_near(self, point1, point2, tolerance):
        """Check if two points are within tolerance distance."""
        dx = point1[0] - point2[0]
        dy = point1[1] - point2[1]
        return (dx*dx + dy*dy)**0.5 <= tolerance
    
    def _generate_collision_free_path(self, start_pos, end_pos, vertex_pos):
        """Generate a collision-free continuous path that avoids predicate text.
        
        Creates a single smooth curve from start to end, with vertex as a point ON the curve,
        ensuring the path never intersects predicate text boundaries.
        """
        sx, sy = start_pos
        ex, ey = end_pos
        vx, vy = vertex_pos
        
        print(f"DEBUG: Collision check for path from {start_pos} to {end_pos} through vertex {vertex_pos}")
        
        # Check if direct line from start to end would intersect any predicate text
        collision_detected = self._path_intersects_predicates(start_pos, end_pos)
        print(f"DEBUG: Collision detected: {collision_detected}")
        
        if collision_detected:
            # Generate curved path that avoids predicate text
            print("DEBUG: Generating curved avoidance path")
            return self._generate_curved_avoidance_path(start_pos, end_pos, vertex_pos)
        else:
            # Direct path is clear - use straight line through vertex if vertex is on the line
            vertex_on_line = self._point_on_line_segment(vertex_pos, start_pos, end_pos, tolerance=10)
            print(f"DEBUG: Vertex on direct line: {vertex_on_line}")
            
            if vertex_on_line:
                print("DEBUG: Using direct path through vertex")
                return [start_pos, vertex_pos, end_pos]
            else:
                # Vertex is not on direct path - create minimal deviation
                print("DEBUG: Using minimal deviation path")
                return self._generate_minimal_deviation_path(start_pos, end_pos, vertex_pos)
    
    def _path_intersects_predicates(self, start_pos, end_pos):
        """Check if a direct line path intersects any predicate text boundaries."""
        if not self.egi:
            print("DEBUG: No EGI available for collision detection")
            return False
            
        print(f"DEBUG: Checking {len(self.spatial_primitives)} spatial primitives for collision")
        
        # Check intersection with all predicate text rectangles
        for primitive in self.spatial_primitives:
            if primitive.element_type == 'edge':  # Predicates are stored as edges
                predicate_name = self.egi.rel.get(primitive.element_id)
                print(f"DEBUG: Checking predicate {primitive.element_id} = '{predicate_name}' at {primitive.position}")
                if predicate_name:
                    intersection = self._line_intersects_text_rectangle(start_pos, end_pos, primitive, predicate_name)
                    print(f"DEBUG: Line intersects '{predicate_name}': {intersection}")
                    if intersection:
                        return True
        print("DEBUG: No collisions detected")
        return False
    
    def _line_intersects_text_rectangle(self, start_pos, end_pos, predicate_primitive, predicate_name):
        """Check if a line segment intersects a predicate's text rectangle."""
        center_x, center_y = predicate_primitive.position
        
        # Calculate text bounds
        font = QFont("Arial", 12)
        font_metrics = QFontMetrics(font)
        text_rect = font_metrics.boundingRect(predicate_name)
        
        text_width = text_rect.width()
        text_height = text_rect.height()
        padding = 8  # Extra padding to ensure clear separation
        
        # Define rectangle bounds
        left = center_x - text_width / 2 - padding
        right = center_x + text_width / 2 + padding
        top = center_y - text_height / 2 - padding
        bottom = center_y + text_height / 2 + padding
        
        # Check line-rectangle intersection using standard algorithm
        return self._line_segment_intersects_rectangle(start_pos, end_pos, left, right, top, bottom)
    
    def _line_segment_intersects_rectangle(self, start_pos, end_pos, left, right, top, bottom):
        """Check if a line segment intersects a rectangle."""
        x1, y1 = start_pos
        x2, y2 = end_pos
        
        # Check if either endpoint is inside rectangle
        if (left <= x1 <= right and top <= y1 <= bottom) or (left <= x2 <= right and top <= y2 <= bottom):
            return True
            
        # Check intersection with rectangle edges using parametric line equation
        # Line: P = start + t * (end - start), where 0 <= t <= 1
        dx = x2 - x1
        dy = y2 - y1
        
        # Check intersection with each rectangle edge
        edges = [
            (left, top, left, bottom),    # Left edge
            (right, top, right, bottom),  # Right edge
            (left, top, right, top),      # Top edge
            (left, bottom, right, bottom) # Bottom edge
        ]
        
        for edge_x1, edge_y1, edge_x2, edge_y2 in edges:
            if self._line_segments_intersect((x1, y1), (x2, y2), (edge_x1, edge_y1), (edge_x2, edge_y2)):
                return True
                
        return False
    
    def _line_segments_intersect(self, line1_start, line1_end, line2_start, line2_end):
        """Check if two line segments intersect."""
        x1, y1 = line1_start
        x2, y2 = line1_end
        x3, y3 = line2_start
        x4, y4 = line2_end
        
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(denom) < 1e-10:  # Lines are parallel
            return False
            
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom
        
        return 0 <= t <= 1 and 0 <= u <= 1
    
    def _point_on_line_segment(self, point, line_start, line_end, tolerance=5):
        """Check if a point is approximately on a line segment within tolerance."""
        px, py = point
        x1, y1 = line_start
        x2, y2 = line_end
        
        # Calculate distance from point to line segment
        line_length_sq = (x2 - x1)**2 + (y2 - y1)**2
        if line_length_sq < 1e-10:
            return self._calculate_distance(point, line_start) <= tolerance
            
        t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / line_length_sq))
        closest_x = x1 + t * (x2 - x1)
        closest_y = y1 + t * (y2 - y1)
        
        distance = self._calculate_distance(point, (closest_x, closest_y))
        return distance <= tolerance
    
    def _generate_curved_avoidance_path(self, start_pos, end_pos, vertex_pos):
        """Generate a curved path that avoids predicate text collisions."""
        # For now, create a simple arc that goes around obstacles
        # This can be enhanced with more sophisticated path planning
        
        # Calculate midpoint and create an arc
        mid_x = (start_pos[0] + end_pos[0]) / 2
        mid_y = (start_pos[1] + end_pos[1]) / 2
        
        # Create arc points that avoid collision
        # Offset perpendicular to the direct line
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        length = (dx*dx + dy*dy)**0.5
        
        if length > 0:
            # Perpendicular offset
            perp_x = -dy / length
            perp_y = dx / length
            
            # Create arc with sufficient offset to avoid collision
            offset = 30  # Offset distance
            arc_point1 = (mid_x + perp_x * offset, mid_y + perp_y * offset)
            
            # Include vertex position if it's reasonable
            vx, vy = vertex_pos
            if abs(vx - mid_x) < 50 and abs(vy - mid_y) < 50:
                return [start_pos, arc_point1, vertex_pos, end_pos]
            else:
                return [start_pos, arc_point1, end_pos]
        
        return [start_pos, vertex_pos, end_pos]
    
    def _generate_minimal_deviation_path(self, start_pos, end_pos, vertex_pos):
        """Generate path with minimal deviation to include vertex position."""
        # Create a path that includes the vertex with minimal total length
        return [start_pos, vertex_pos, end_pos]
    
    def _render_vertex_spot(self, painter: QPainter, x: float, y: float, vertex_name: str, vertex_id: str = None):
        """Render vertex spot with constant name according to Dau's conventions.
        
        Vertices are mathematically significant points on ligatures where:
        - Constants names appear (like 'Socrates')
        - Branching occurs for 3+ connections
        - Identity assertions are made
        """
        # Track vertex position for interactive selection
        if vertex_id:
            self.branching_points[vertex_id] = (x, y, vertex_name)
        
        # Check if this vertex is selected or hovered
        is_selected = vertex_id in self.selected_branching_points if vertex_id else False
        is_hovered = vertex_id == self.hover_branching_point if vertex_id else False
        
        # Render constant name if present
        if vertex_name:
            text_color = QColor(0, 100, 200) if is_selected else QColor(0, 0, 0)
            painter.setPen(QPen(text_color, 1))
            painter.setFont(QFont("Times", 12, QFont.Bold))
            text_rect = painter.fontMetrics().boundingRect(vertex_name)
            
            # Position text near the vertex spot
            text_x = x - text_rect.width() / 2
            text_y = y - 8  # Above the vertex spot
            
            # Draw white background for text readability
            bg_margin = 2
            bg_rect = QRectF(text_x - bg_margin, text_y - text_rect.height() - bg_margin,
                           text_rect.width() + 2*bg_margin, text_rect.height() + 2*bg_margin)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(255, 255, 255, 200)))
            painter.drawRect(bg_rect)
            
            # Draw the constant name text
            painter.setPen(QPen(text_color, 1))
            painter.setBrush(Qt.NoBrush)
            painter.drawText(QPointF(text_x, text_y), vertex_name)
            
            print(f"DEBUG: Rendered constant name '{vertex_name}' at vertex ({x:.1f},{y:.1f})")
        
        # Render selection highlight if selected
        if is_selected or is_hovered:
            highlight_color = QColor(0, 150, 255, 100) if is_selected else QColor(100, 100, 100, 50)
            painter.setPen(QPen(highlight_color, 2))
            painter.setBrush(QBrush(highlight_color))
            painter.drawEllipse(QPointF(x, y), 8, 8)
        
        # Render mathematically significant vertex spot (Dau convention)
        # Vertices are always significant points on ligatures
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        painter.drawEllipse(QPointF(x, y), 3, 3)  # Prominent vertex spot
        
        print(f"DEBUG: Rendered vertex spot for {vertex_id} at ({x:.1f},{y:.1f})")
    
    def _get_predicate_position(self, predicate_id: str, vertex_position=None, argument_index=None):
        """Get boundary position of a predicate where ligature should connect (hook position).
        
        For n-ary predicates, argument_index determines which hook position to use,
        ensuring separated connection points for each argument per Dau's conventions.
        """
        for primitive in self.spatial_primitives:
            if primitive.element_id == predicate_id:
                # Return boundary position with argument-specific hook separation
                return self._calculate_predicate_boundary_position(primitive, vertex_position, argument_index)
        return None
    
    def _calculate_predicate_boundary_position(self, predicate_primitive, vertex_position=None, argument_index=None):
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
                
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events for selection and interaction."""
        if event.button() == Qt.LeftButton:
            # Convert to float coordinates
            pos = event.position() if hasattr(event, 'position') else event.localPos()
            x, y = float(pos.x()), float(pos.y())

            # Shift-drag marquee start
            if event.modifiers() & Qt.ShiftModifier:
                self._marquee_active = True
                self._marquee_start = (x, y)
                self._marquee_end = (x, y)
                self.update()
                return
            
            # First check for branching point selection (higher priority)
            clicked_branching_point = self._find_branching_point_at_position(x, y)
            
            if clicked_branching_point:
                # Handle branching point selection
                if event.modifiers() & Qt.ControlModifier:
                    # Multi-select with Ctrl
                    if clicked_branching_point in self.selected_branching_points:
                        self.selected_branching_points.remove(clicked_branching_point)
                    else:
                        self.selected_branching_points.add(clicked_branching_point)
                else:
                    # Single select
                    self.selected_branching_points = {clicked_branching_point}
                    self.selected_elements.clear()  # Clear element selection
                
                # Start drag state for branching point
                self.drag_state = {
                    'type': 'branching_point',
                    'vertex_id': clicked_branching_point,
                    'start_pos': (x, y)
                }
                print(f"✓ Selected branching point {clicked_branching_point}")
            else:
                # Check for element selection
                # Alt-click cycles overlapping candidates deterministically
                if event.modifiers() & Qt.AltModifier:
                    px, py = int(x), int(y)
                    if self._alt_cycle_anchor != (px, py):
                        # New anchor; recompute candidates and reset index
                        self._alt_cycle_candidates = self._find_candidates_at_position(x, y)
                        self._alt_cycle_index = 0
                        self._alt_cycle_anchor = (px, py)
                    if self._alt_cycle_candidates:
                        clicked_element = self._alt_cycle_candidates[self._alt_cycle_index % len(self._alt_cycle_candidates)]
                        self._alt_cycle_index += 1
                    else:
                        clicked_element = None
                else:
                    self._alt_cycle_candidates = []
                    self._alt_cycle_index = 0
                    self._alt_cycle_anchor = None
                    clicked_element = self._find_element_at_position(x, y)
                
                if clicked_element:
                    # Support Cmd (Meta) and Ctrl for toggle-add/remove
                    if (event.modifiers() & Qt.ControlModifier) or (event.modifiers() & Qt.MetaModifier):
                        # Multi-select with Ctrl
                        if clicked_element in self.selected_elements:
                            self.selected_elements.remove(clicked_element)
                        else:
                            self.selected_elements.add(clicked_element)
                    else:
                        # Single select
                        self.selected_elements = {clicked_element}
                        self.selected_branching_points.clear()  # Clear branching point selection
                    print(f"✓ Selected element {clicked_element}")
                else:
                    # Clear all selections if clicking empty space
                    if self.selected_elements or self.selected_branching_points:
                        print(f"✓ Cleared selection in {self.current_mode.value} mode")
                    self.selected_elements.clear()
                    self.selected_branching_points.clear()
                    self.drag_state = None
            
            # Update visual display
            self.update()
        elif event.button() == Qt.RightButton:
            # TODO: context menu for actions (Milestone 2)
            pass

    def mouseMoveEvent(self, event):
        """Handle mouse movement for hover effects and marquee updates."""
        if self._marquee_active and self._marquee_start:
            pos = event.position() if hasattr(event, 'position') else event.localPos()
            self._marquee_end = (float(pos.x()), float(pos.y()))
            self.update()
            return
        super().mouseMoveEvent(event)
    
    def _find_branching_point_at_position(self, x: float, y: float) -> Optional[str]:
        """Find branching point at given position for selection."""
        hit_radius = 8.0  # Slightly larger than visual radius for easier selection
        
        for vertex_id, (bp_x, bp_y, vertex_name) in self.branching_points.items():
            distance = ((x - bp_x) ** 2 + (y - bp_y) ** 2) ** 0.5
            if distance <= hit_radius:
                return vertex_id
        
        return None
            
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
                    self.selected_elements.add(p.element_id)
                    added.append(p.element_id)
            if added:
                print(f"✓ Marquee added {len(added)} elements")
            # Reset marquee
            self._marquee_active = False
            self._marquee_start = None
            self._marquee_end = None
            self.update()

    def keyPressEvent(self, event):
        """Keyboard shortcuts for selection (Cmd/Ctrl+A selects all in current area)."""
        if (event.key() == Qt.Key_A) and ((event.modifiers() & Qt.ControlModifier) or (event.modifiers() & Qt.MetaModifier)):
            # Determine current area: if mouse is inside a cut, select all inside innermost cut; else select all on sheet
            cursor_pos = self.mapFromGlobal(QCursor.pos())
            x, y = float(cursor_pos.x()), float(cursor_pos.y())
            area_cut_id = self._innermost_cut_at(x, y)
            count = 0
            for p in self.spatial_primitives:
                if area_cut_id:
                    if self._element_inside_cut(p, area_cut_id):
                        self.selected_elements.add(p.element_id)
                        count += 1
                else:
                    # Sheet elements = not inside any cut
                    if not self._element_inside_any_cut(p):
                        self.selected_elements.add(p.element_id)
                        count += 1
            print(f"✓ Select-all added {count} elements")
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

    def _find_candidates_at_position(self, x: float, y: float) -> List[str]:
        """Return all candidate element IDs under cursor, ordered by z-index (cuts < edges < vertices/predicates)."""
        candidates: List[Tuple[int, str]] = []
        for p in self.spatial_primitives:
            x1, y1, x2, y2 = p.bounds
            if x1 - 3 <= x <= x2 + 3 and y1 - 3 <= y <= y2 + 3:
                z = 0 if p.element_type == "cut" else (1 if p.element_type == "edge" else 2)
                candidates.append((z, p.element_id))
        candidates.sort(key=lambda t: (-t[0]))
        return [eid for _, eid in candidates]
            
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
                # For predicates (text), calculate precise text bounds for selection
                # Get the actual relation name to calculate exact text dimensions
                relation_name = self.egi.rel.get(primitive.element_id, f"R{primitive.element_id[:4]}")
                
                # Use same font as rendering to get exact text bounds
                font = QFont("Times", 11)
                font_metrics = QFontMetrics(font)
                text_rect = font_metrics.boundingRect(relation_name)
                
                # Calculate actual text position (same as rendering logic)
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                text_x = center_x - text_rect.width() / 2
                text_y = center_y + text_rect.height() / 4
                
                # Create precise selection bounds around the actual text
                text_left = text_x
                text_right = text_x + text_rect.width()
                text_top = text_y - text_rect.height()
                text_bottom = text_y
                
                # Small padding for easier selection
                padding = 3
                if (text_left - padding) <= x <= (text_right + padding) and (text_top - padding) <= y <= (text_bottom + padding):
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
        """Load the Socrates sample diagram on startup for branching point testing."""
        if self.sample_egifs:
            # Load Socrates example for branching point testing
            socrates_egif = '(Human "Socrates") (Mortal "Socrates")'
            self.egif_combo.setCurrentText(socrates_egif)
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
