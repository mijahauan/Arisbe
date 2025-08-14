#!/usr/bin/env python3
"""
Interactive Canvas with Selection System

Implements Milestone 2: Selection Overlays and Interactive Controls
- Selection-driven interaction model per Dau/Arisbe requirements
- Element-specific overlays (cut resize handles, LoI endpoints, etc.)
- Context-sensitive action menus
- Professional graph editor interaction patterns
"""

from typing import Dict, List, Tuple, Optional, Set, Any
from dataclasses import dataclass
from enum import Enum
from PySide6.QtWidgets import (
    QWidget, QMenu, QApplication
)
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QPainterPath, 
    QCursor, QMouseEvent, QKeyEvent, QContextMenuEvent
)
from PySide6.QtCore import Qt, QPointF, QRectF, Signal, QTimer
import math

from egdf_canvas_renderer import EGDFCanvasRenderer, DauVisualStyle


class SelectionMode(Enum):
    """Selection interaction modes."""
    SINGLE = "single"           # Single element selection
    MULTI = "multi"            # Multi-element selection (Ctrl+click)
    AREA = "area"              # Area selection (drag rectangle)
    SUBGRAPH = "subgraph"      # Logical subgraph selection


class ElementType(Enum):
    """Types of selectable elements."""
    VERTEX = "vertex"
    PREDICATE = "predicate"
    CUT = "cut"
    IDENTITY_LINE = "identity_line"
    EMPTY_AREA = "empty_area"


@dataclass
class SelectionOverlay:
    """Visual overlay for selected elements."""
    element_id: str
    element_type: ElementType
    bounds: QRectF
    handles: List[QRectF]  # Resize/manipulation handles
    highlight_path: QPainterPath  # Selection highlight


@dataclass
class InteractionState:
    """Current interaction state."""
    mode: SelectionMode
    selected_elements: Set[str]
    hover_element: Optional[str]
    drag_start: Optional[QPointF]
    drag_current: Optional[QPointF]
    is_dragging: bool
    context_menu_element: Optional[str]


class InteractiveCanvas(EGDFCanvasRenderer):
    """
    Interactive canvas with selection system and context actions.
    
    Implements selection-driven interaction model:
    1. User selects elements (single, multi, area, subgraph)
    2. System provides context-appropriate actions
    3. User performs operations on selected elements
    """
    
    # Signals for interaction events
    selection_changed = Signal(list)  # List of selected element IDs
    element_double_clicked = Signal(str)  # Element ID
    context_action_requested = Signal(str, str)  # Action name, element ID
    drag_completed = Signal(list, QPointF)  # Element IDs, new position
    
    def __init__(self, width: int = 800, height: int = 600):
        super().__init__(width, height)
        
        # CRITICAL FIX: Connect to our own renderer capabilities
        # The InteractiveCanvas IS the renderer, so self.renderer = self
        self.renderer = self
        
        # Selection system
        self.interaction_state = InteractionState(
            mode=SelectionMode.SINGLE,
            selected_elements=set(),
            hover_element=None,
            drag_start=None,
            drag_current=None,
            is_dragging=False,
            context_menu_element=None
        )
        
        # Selection overlays
        self.selection_overlays: Dict[str, SelectionOverlay] = {}
        
        # Selection visual style
        self.selection_style = self._create_selection_style()
        
        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)
        
        # Context menu
        self.context_menu = None
        
        print("🎯 Interactive Canvas with Selection System initialized (renderer connected)")
    
    def _create_selection_style(self) -> Dict[str, Any]:
        """Create visual style for selection overlays."""
        return {
            'selection_color': QColor(0, 120, 215, 100),  # Blue with transparency
            'selection_border': QColor(0, 120, 215, 200),  # Solid blue border
            'handle_color': QColor(255, 255, 255, 200),    # White handles
            'handle_border': QColor(0, 120, 215, 255),     # Blue handle borders
            'hover_color': QColor(0, 120, 215, 50),        # Light blue hover
            'handle_size': 8.0,                            # Handle size in pixels
            'selection_width': 2.0                         # Selection border width
        }
    
    def set_selection_mode(self, mode: SelectionMode):
        """Set the current selection mode."""
        self.interaction_state.mode = mode
        self.update()
    
    def get_selected_elements(self) -> List[str]:
        """Get list of currently selected element IDs."""
        return list(self.interaction_state.selected_elements)
    
    def select_element(self, element_id: str, multi_select: bool = False):
        """Select an element by ID."""
        if not multi_select:
            self.clear_selection()
        
        self.interaction_state.selected_elements.add(element_id)
        self._create_selection_overlay(element_id)
        self.selection_changed.emit(self.get_selected_elements())
        self.update()
    
    def deselect_element(self, element_id: str):
        """Deselect an element by ID."""
        self.interaction_state.selected_elements.discard(element_id)
        if element_id in self.selection_overlays:
            del self.selection_overlays[element_id]
        self.selection_changed.emit(self.get_selected_elements())
        self.update()
    
    def clear_selection(self):
        """Clear all selections."""
        self.interaction_state.selected_elements.clear()
        self.selection_overlays.clear()
        self.selection_changed.emit([])
        self.update()
    
    def _create_selection_overlay(self, element_id: str):
        """Create selection overlay for an element using renderer's authoritative bounds."""
        if not hasattr(self, 'renderer') or not self.renderer:
            print(f"❌ No renderer available for selection overlay: {element_id}")
            return
        
        # Get authoritative visual bounds from renderer
        visual_bounds = self.renderer.get_element_visual_bounds(element_id)
        if not visual_bounds:
            print(f"❌ No visual bounds found for element: {element_id}")
            return
        
        left, top, right, bottom = visual_bounds
        bounds_rect = QRectF(left, top, right - left, bottom - top)
        
        print(f"✅ Creating selection overlay for {element_id}: bounds ({left:.1f}, {top:.1f}, {right:.1f}, {bottom:.1f})")
        
        # Determine element type from spatial primitives
        element_type_str = 'unknown'
        for primitive in self.spatial_primitives:
            if isinstance(primitive, dict) and primitive.get('element_id') == element_id:
                element_type_str = primitive.get('element_type', 'unknown')
                break
        
        element_type = self._map_element_type(element_type_str)
        
        # Create manipulation handles based on element type
        handles = self._create_element_handles(element_type, bounds_rect)
        
        # Create highlight path
        highlight_path = self._create_highlight_path(element_type, bounds_rect)
        
        # Store overlay
        self.selection_overlays[element_id] = SelectionOverlay(
            element_id=element_id,
            element_type=element_type,
            bounds=bounds_rect,
            handles=handles,
            highlight_path=highlight_path
        )
    
    def _map_element_type(self, element_type_str: str) -> ElementType:
        """Map string element type to enum."""
        mapping = {
            'vertex': ElementType.VERTEX,
            'predicate': ElementType.PREDICATE,
            'cut': ElementType.CUT,
            'identity_line': ElementType.IDENTITY_LINE
        }
        return mapping.get(element_type_str, ElementType.VERTEX)
    
    def _create_element_handles(self, element_type: ElementType, bounds: QRectF) -> List[QRectF]:
        """Create manipulation handles for different element types."""
        handles = []
        handle_size = self.selection_style['handle_size']
        
        if element_type == ElementType.CUT:
            # Cut resize handles at corners and midpoints
            handles.extend([
                # Corners
                QRectF(bounds.left() - handle_size/2, bounds.top() - handle_size/2, handle_size, handle_size),
                QRectF(bounds.right() - handle_size/2, bounds.top() - handle_size/2, handle_size, handle_size),
                QRectF(bounds.left() - handle_size/2, bounds.bottom() - handle_size/2, handle_size, handle_size),
                QRectF(bounds.right() - handle_size/2, bounds.bottom() - handle_size/2, handle_size, handle_size),
                # Midpoints
                QRectF(bounds.center().x() - handle_size/2, bounds.top() - handle_size/2, handle_size, handle_size),
                QRectF(bounds.center().x() - handle_size/2, bounds.bottom() - handle_size/2, handle_size, handle_size),
                QRectF(bounds.left() - handle_size/2, bounds.center().y() - handle_size/2, handle_size, handle_size),
                QRectF(bounds.right() - handle_size/2, bounds.center().y() - handle_size/2, handle_size, handle_size),
            ])
        elif element_type == ElementType.IDENTITY_LINE:
            # Line endpoint handles
            handles.extend([
                QRectF(bounds.left() - handle_size/2, bounds.center().y() - handle_size/2, handle_size, handle_size),
                QRectF(bounds.right() - handle_size/2, bounds.center().y() - handle_size/2, handle_size, handle_size),
            ])
        else:
            # Default: single center handle for move
            handles.append(
                QRectF(bounds.center().x() - handle_size/2, bounds.center().y() - handle_size/2, handle_size, handle_size)
            )
        
        return handles
    
    def _create_highlight_path(self, element_type: ElementType, bounds: QRectF) -> QPainterPath:
        """Create highlight path for element type."""
        path = QPainterPath()
        
        if element_type == ElementType.CUT:
            # Rounded rectangle for cuts
            path.addRoundedRect(bounds, 8.0, 8.0)
        elif element_type == ElementType.IDENTITY_LINE:
            # Line with thickness
            path.addRect(bounds)
        else:
            # Default rectangle
            path.addRect(bounds)
        
        return path
    
    def _find_element_at_point(self, point: QPointF) -> Optional[str]:
        """Find element at the given point using renderer's authoritative knowledge."""
        # Use renderer's authoritative hit detection if available
        if hasattr(self, 'renderer') and self.renderer:
            element_id = self.renderer.find_element_at_point(point.x(), point.y())
            if element_id:
                print(f"✅ Renderer found element: {element_id} at ({point.x():.1f}, {point.y():.1f})")
                return element_id
        
        # Fallback to spatial primitives bounds check
        for primitive in self.spatial_primitives:
            if not isinstance(primitive, dict):
                continue
            
            bounds = primitive.get('bounds')
            if bounds:
                left, top, right, bottom = bounds
                if left <= point.x() <= right and top <= point.y() <= bottom:
                    element_id = primitive.get('element_id')
                    print(f"✅ Fallback found element: {element_id} at ({point.x():.1f}, {point.y():.1f})")
                    return element_id
        
        print(f"❌ No element found at ({point.x():.1f}, {point.y():.1f})")
        return None
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press for selection and interaction."""
        point = QPointF(event.position().x(), event.position().y())
        element_id = self._find_element_at_point(point)
        
        print(f"🖱️ Mouse press at ({point.x():.1f}, {point.y():.1f}), found element: {element_id}")
        
        if event.button() == Qt.LeftButton:
            multi_select = event.modifiers() & Qt.ControlModifier
            
            if element_id:
                if element_id in self.interaction_state.selected_elements:
                    # Already selected - prepare for drag
                    print(f"🎯 Element {element_id} already selected, preparing for drag")
                    self.interaction_state.drag_start = point
                else:
                    # Select element
                    print(f"🎯 Selecting element {element_id}")
                    self.select_element(element_id, multi_select)
                    self.interaction_state.drag_start = point
            else:
                # Clicked empty area
                if not multi_select:
                    self.clear_selection()
                # Start area selection
                self.interaction_state.drag_start = point
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move for hover and drag."""
        point = QPointF(event.position().x(), event.position().y())
        
        # Update hover element
        hover_element = self._find_element_at_point(point)
        if hover_element != self.interaction_state.hover_element:
            self.interaction_state.hover_element = hover_element
            self.update()
        
        # Handle dragging
        if self.interaction_state.drag_start and event.buttons() & Qt.LeftButton:
            if not self.interaction_state.is_dragging:
                # Start dragging
                self.interaction_state.is_dragging = True
                self.setCursor(Qt.ClosedHandCursor)
            
            self.interaction_state.drag_current = point
            self.update()
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release to complete interactions."""
        if event.button() == Qt.LeftButton:
            if self.interaction_state.is_dragging:
                # Complete drag operation
                if self.interaction_state.drag_current:
                    delta = self.interaction_state.drag_current - self.interaction_state.drag_start
                    selected_elements = self.get_selected_elements()
                    print(f"🚚 Emitting drag_completed: {selected_elements}, delta: ({delta.x():.1f}, {delta.y():.1f})")
                    self.drag_completed.emit(selected_elements, delta)
                else:
                    print("❌ No drag_current position for drag completion")
                
                self.interaction_state.is_dragging = False
                self.setCursor(Qt.ArrowCursor)
            else:
                print("🖱️ Mouse release but not dragging")
            
            # Reset drag state
            self.interaction_state.drag_start = None
            self.interaction_state.drag_current = None
        
        super().mouseReleaseEvent(event)
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Handle double-click for element-specific actions."""
        point = QPointF(event.position().x(), event.position().y())
        element_id = self._find_element_at_point(point)
        
        if element_id:
            self.element_double_clicked.emit(element_id)
        
        super().mouseDoubleClickEvent(event)
    
    def contextMenuEvent(self, event: QContextMenuEvent):
        """Handle right-click context menu."""
        point = QPointF(event.pos().x(), event.pos().y())
        element_id = self._find_element_at_point(point)
        
        self.interaction_state.context_menu_element = element_id
        self._show_context_menu(event.globalPos(), element_id)
    
    def _show_context_menu(self, global_pos, element_id: Optional[str]):
        """Show context menu with appropriate actions."""
        menu = QMenu(self)
        
        if element_id:
            # Element-specific actions
            element_type = self._get_element_type(element_id)
            
            if element_type == ElementType.CUT:
                menu.addAction("Resize Cut", lambda: self._emit_context_action("resize_cut", element_id))
                menu.addAction("Delete Cut", lambda: self._emit_context_action("delete_cut", element_id))
                menu.addSeparator()
                menu.addAction("Add Element to Cut", lambda: self._emit_context_action("add_to_cut", element_id))
            elif element_type == ElementType.PREDICATE:
                menu.addAction("Edit Predicate", lambda: self._emit_context_action("edit_predicate", element_id))
                menu.addAction("Delete Predicate", lambda: self._emit_context_action("delete_predicate", element_id))
            elif element_type == ElementType.VERTEX:
                menu.addAction("Edit Vertex", lambda: self._emit_context_action("edit_vertex", element_id))
                menu.addAction("Delete Vertex", lambda: self._emit_context_action("delete_vertex", element_id))
            elif element_type == ElementType.IDENTITY_LINE:
                menu.addAction("Edit Identity Line", lambda: self._emit_context_action("edit_identity_line", element_id))
                menu.addAction("Delete Identity Line", lambda: self._emit_context_action("delete_identity_line", element_id))
            
            menu.addSeparator()
            menu.addAction("Select Connected", lambda: self._emit_context_action("select_connected", element_id))
        else:
            # Empty area actions
            menu.addAction("Add Vertex", lambda: self._emit_context_action("add_vertex", None))
            menu.addAction("Add Predicate", lambda: self._emit_context_action("add_predicate", None))
            menu.addAction("Add Cut", lambda: self._emit_context_action("add_cut", None))
        
        menu.addSeparator()
        menu.addAction("Clear Selection", self.clear_selection)
        
        menu.exec(global_pos)
    
    def _get_element_type(self, element_id: str) -> ElementType:
        """Get element type for an element ID."""
        if element_id in self.selection_overlays:
            return self.selection_overlays[element_id].element_type
        
        # Fallback: analyze element from spatial primitives
        for primitive in self.spatial_primitives:
            if isinstance(primitive, dict) and primitive.get('element_id') == element_id:
                return self._map_element_type(primitive.get('element_type', 'vertex'))
        
        return ElementType.VERTEX
    
    def _emit_context_action(self, action: str, element_id: Optional[str]):
        """Emit context action signal."""
        self.context_action_requested.emit(action, element_id or "")
    
    def paintEvent(self, event):
        """Paint the canvas with selection overlays."""
        # Paint base canvas first
        super().paintEvent(event)
        
        # Paint selection overlays
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        try:
            self._paint_selection_overlays(painter)
        finally:
            painter.end()
    
    def _paint_selection_overlays(self, painter: QPainter):
        """Paint selection overlays and handles."""
        # Paint hover highlight
        if self.interaction_state.hover_element and self.interaction_state.hover_element not in self.interaction_state.selected_elements:
            self._paint_hover_highlight(painter, self.interaction_state.hover_element)
        
        # Paint selection highlights
        for overlay in self.selection_overlays.values():
            self._paint_selection_highlight(painter, overlay)
        
        # Paint drag preview
        if self.interaction_state.is_dragging and self.interaction_state.drag_current:
            self._paint_drag_preview(painter)
    
    def _paint_hover_highlight(self, painter: QPainter, element_id: str):
        """Paint hover highlight for an element."""
        # Find element bounds
        for primitive in self.spatial_primitives:
            if isinstance(primitive, dict) and primitive.get('element_id') == element_id:
                bounds = primitive.get('bounds')
                if bounds:
                    left, top, right, bottom = bounds
                    rect = QRectF(left, top, right - left, bottom - top)
                    
                    # Paint hover highlight
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QBrush(self.selection_style['hover_color']))
                    painter.drawRoundedRect(rect, 4.0, 4.0)
                break
    
    def _paint_selection_highlight(self, painter: QPainter, overlay: SelectionOverlay):
        """Paint selection highlight and handles."""
        # Paint selection highlight
        painter.setPen(QPen(self.selection_style['selection_border'], self.selection_style['selection_width']))
        painter.setBrush(QBrush(self.selection_style['selection_color']))
        painter.drawPath(overlay.highlight_path)
        
        # Paint manipulation handles
        painter.setPen(QPen(self.selection_style['handle_border'], 1.0))
        painter.setBrush(QBrush(self.selection_style['handle_color']))
        
        for handle in overlay.handles:
            painter.drawEllipse(handle)
    
    def _paint_drag_preview(self, painter: QPainter):
        """Paint drag preview for selected elements."""
        if not self.interaction_state.drag_start or not self.interaction_state.drag_current:
            return
        
        delta = self.interaction_state.drag_current - self.interaction_state.drag_start
        
        # Paint preview of dragged elements
        painter.setPen(QPen(self.selection_style['selection_border'], 1.0, Qt.DashLine))
        painter.setBrush(Qt.NoBrush)
        
        for overlay in self.selection_overlays.values():
            preview_bounds = overlay.bounds.translated(delta)
            painter.drawRect(preview_bounds)


def create_interactive_canvas(width: int = 800, height: int = 600) -> InteractiveCanvas:
    """Factory function to create an interactive canvas."""
    return InteractiveCanvas(width, height)


if __name__ == "__main__":
    # Test the interactive canvas
    app = QApplication([])
    
    canvas = create_interactive_canvas()
    canvas.show()
    
    print("🎯 Interactive Canvas Test")
    print("- Click to select elements")
    print("- Ctrl+Click for multi-select")
    print("- Right-click for context menu")
    print("- Drag to move elements")
    
    app.exec()
