"""
InteractiveDiagramCanvas - Interactive extension of DiagramCanvas for Ergasterion.

Adds mouse interaction capabilities:
- Element selection (click, multi-select with Ctrl)
- Drag-and-drop repositioning
- Hover feedback
- Selection highlighting
"""

from typing import Optional, Set, List, Tuple
from PySide6.QtCore import Qt, Signal, QPointF, QRect
from PySide6.QtGui import QMouseEvent, QPainter, QColor, QPen
from PySide6.QtWidgets import QWidget

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from gui_clean.common.diagram_canvas import DiagramCanvas
from unified_d3_engine import LayoutDTO
from egi_core_dau import RelationalGraphWithCuts


class InteractiveDiagramCanvas(DiagramCanvas):
    """
    Interactive canvas for Ergasterion mode.
    
    Extends DiagramCanvas with:
    - Element selection via mouse
    - Drag-and-drop repositioning
    - Visual feedback (hover, selection)
    - Coordinate mapping between screen and logical space
    
    Signals:
        element_selected(element_id: str) - Single element selected
        elements_selected(element_ids: List[str]) - Multiple selection
        element_moved(element_id: str, new_pos: Tuple[float, float]) - Element dragged
        selection_cleared() - Selection cleared
    """
    
    # Signals
    element_selected = Signal(str)
    elements_selected = Signal(list)
    element_moved = Signal(str, tuple)
    selection_cleared = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Selection state
        self._selected_elements: Set[str] = set()
        self._hovered_element: Optional[str] = None
        
        # Drag state
        self._dragging = False
        self._drag_element: Optional[str] = None
        self._drag_start_pos: Optional[QPointF] = None
        self._drag_element_start_pos: Optional[Tuple[float, float]] = None
        
        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)
        self._svg_widget.setMouseTracking(True)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press - start selection or drag."""
        if event.button() == Qt.LeftButton:
            if self._handle_mouse_press(event):
                event.accept()
                return
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move - drag or hover."""
        if self._handle_mouse_move(event):
            event.accept()
            return
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release - complete drag."""
        if event.button() == Qt.LeftButton:
            if self._handle_mouse_release(event):
                event.accept()
                return
        super().mouseReleaseEvent(event)
    
    def _handle_mouse_press(self, event: QMouseEvent) -> bool:
        """Handle mouse press - start selection or drag."""
        # Get element at mouse position
        pos = event.position()
        print(f"Mouse press at ({pos.x():.1f}, {pos.y():.1f})")  # Debug
        element_id = self._get_element_at_pos(pos)
        
        if element_id:
            # Check for multi-select (Ctrl/Cmd key)
            multi_select = event.modifiers() & Qt.ControlModifier
            
            if multi_select:
                # Toggle selection
                if element_id in self._selected_elements:
                    self._selected_elements.remove(element_id)
                else:
                    self._selected_elements.add(element_id)
                
                self.elements_selected.emit(list(self._selected_elements))
            else:
                # Single selection + start drag
                self._selected_elements = {element_id}
                self.element_selected.emit(element_id)
                
                # Prepare for drag
                self._dragging = False  # Will become True on move
                self._drag_element = element_id
                self._drag_start_pos = event.position()
                self._drag_element_start_pos = self._get_element_position(element_id)
            
            self._update_display()
            return True
        else:
            # Clicked on empty space - clear selection
            if self._selected_elements:
                self._selected_elements.clear()
                self.selection_cleared.emit()
                self._update_display()
            return False
    
    def _handle_mouse_move(self, event: QMouseEvent) -> bool:
        """Handle mouse move - drag or hover."""
        # Handle drag
        if self._drag_element and self._drag_start_pos:
            # Start dragging after minimum movement
            delta = event.position() - self._drag_start_pos
            if not self._dragging and (abs(delta.x()) > 3 or abs(delta.y()) > 3):
                self._dragging = True
            
            if self._dragging and self._drag_element_start_pos:
                # Calculate new position
                dx = delta.x()
                dy = delta.y()
                
                new_x = self._drag_element_start_pos[0] + dx
                new_y = self._drag_element_start_pos[1] + dy
                
                # TODO: Apply position temporarily for preview
                # For now, we'll apply on mouse release
            
            return True
        
        # Handle hover (when not dragging)
        if not self._dragging:
            element_id = self._get_element_at_pos(event.position())
            if element_id != self._hovered_element:
                self._hovered_element = element_id
                # TODO: Update visual feedback
        
        return False
    
    def _handle_mouse_release(self, event: QMouseEvent) -> bool:
        """Handle mouse release - complete drag."""
        if self._dragging and self._drag_element:
            # Calculate final position
            delta = event.position() - self._drag_start_pos
            dx = delta.x()
            dy = delta.y()
            
            new_x = self._drag_element_start_pos[0] + dx
            new_y = self._drag_element_start_pos[1] + dy
            
            # Emit move signal
            self.element_moved.emit(self._drag_element, (new_x, new_y))
        
        # Reset drag state
        self._dragging = False
        self._drag_element = None
        self._drag_start_pos = None
        self._drag_element_start_pos = None
        
        return self._dragging
    
    def _get_element_at_pos(self, pos: QPointF) -> Optional[str]:
        """
        Get element ID at screen position.
        
        Uses simple hit testing on vertex/predicate positions.
        Returns the closest element within a threshold.
        """
        if not self._current_dto:
            print("  No DTO available")
            return None
        
        # Get widget and SVG dimensions for coordinate mapping
        widget_width = self._svg_widget.width()
        widget_height = self._svg_widget.height()
        
        # Get viewport bounds from DTO
        vb = self._current_dto.viewport_bounds
        svg_width = vb.max_x - vb.min_x
        svg_height = vb.max_y - vb.min_y
        
        # Calculate scale factors
        scale_x = svg_width / widget_width if widget_width > 0 else 1.0
        scale_y = svg_height / widget_height if widget_height > 0 else 1.0
        
        # Transform widget coordinates to SVG coordinates
        svg_x = vb.min_x + pos.x() * scale_x
        svg_y = vb.min_y + pos.y() * scale_y
        
        print(f"  Widget: ({pos.x():.1f}, {pos.y():.1f}) -> SVG: ({svg_x:.1f}, {svg_y:.1f})")
        print(f"  Scale: {scale_x:.2f}x, {scale_y:.2f}x")
        
        # Check vertices (15px radius hit zone in SVG coordinates)
        closest_vertex = None
        min_dist = 15 * max(scale_x, scale_y)  # Hit threshold scaled to SVG space
        
        for vertex_id, point in self._current_dto.vertex_positions.items():
            dx = svg_x - point.x
            dy = svg_y - point.y
            dist = (dx*dx + dy*dy) ** 0.5
            
            if dist < min_dist:
                min_dist = dist
                closest_vertex = vertex_id
        
        if closest_vertex:
            print(f"  Found vertex: {closest_vertex}")
            return closest_vertex
        
        # Check predicates (rectangular hit zone in SVG coordinates)
        for pred_id, point in self._current_dto.predicate_positions.items():
            # Use approximate text bounds (will refine later)
            width = 50 * scale_x  # Scaled to SVG space
            height = 20 * scale_y  # Scaled to SVG space
            
            if (abs(svg_x - point.x) < width/2 and abs(svg_y - point.y) < height/2):
                print(f"  Found predicate: {pred_id}")
                return pred_id
        
        print("  No element found")
        return None
    
    def _get_element_position(self, element_id: str) -> Optional[Tuple[float, float]]:
        """Get current position of an element."""
        if not self._current_dto:
            return None
        
        # Check vertices
        if element_id in self._current_dto.vertex_positions:
            point = self._current_dto.vertex_positions[element_id]
            return (point.x, point.y)
        
        # Check predicates
        if element_id in self._current_dto.predicate_positions:
            point = self._current_dto.predicate_positions[element_id]
            return (point.x, point.y)
        
        return None
    
    def _update_display(self):
        """Refresh display with current selection state."""
        # For now, just trigger a re-render
        # In future: overlay selection indicators
        if self._current_dto and self._current_egi:
            self.display_dto(self._current_dto, self._current_egi)
    
    def get_selected_elements(self) -> List[str]:
        """Get list of currently selected element IDs."""
        return list(self._selected_elements)
    
    def clear_selection(self):
        """Clear current selection."""
        if self._selected_elements:
            self._selected_elements.clear()
            self.selection_cleared.emit()
            self._update_display()
    
    def set_selection(self, element_ids: List[str]):
        """Set selection to specific elements."""
        self._selected_elements = set(element_ids)
        if element_ids:
            if len(element_ids) == 1:
                self.element_selected.emit(element_ids[0])
            else:
                self.elements_selected.emit(element_ids)
        self._update_display()
