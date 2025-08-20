"""
Interactive graphics controller for Qt Graphics items with spatial constraint validation.

Handles drag operations, resize operations, and real-time constraint validation
for predicates, vertices, and cuts in the EG GUI.
"""

from typing import Optional, Tuple, Dict, Any
from PySide6.QtCore import QObject, Signal, QPointF, QRectF
from PySide6.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsTextItem
from PySide6.QtGui import QPen, QColor

from gui_spatial_constraints import GuiSpatialConstraints, Rectangle, ElementInfo, EditMode

class InteractiveGraphicsController(QObject):
    """Controller for interactive graphics operations with spatial validation."""
    
    # Signals for communicating with the main application
    element_moved = Signal(str, float, float)  # element_id, new_x, new_y
    cut_resized = Signal(str, QRectF)  # cut_id, new_bounds
    operation_blocked = Signal(str, str)  # operation_type, reason
    
    def __init__(self):
        super().__init__()
        self.constraints = GuiSpatialConstraints()
        self.dragging_item: Optional[QGraphicsItem] = None
        self.drag_start_pos: Optional[QPointF] = None
        self.resizing_cut: Optional[QGraphicsRectItem] = None
        self.resize_handle_pos: Optional[str] = None  # "top", "bottom", "left", "right", etc.
        
        # Track graphics items to element IDs
        self.item_to_element: Dict[QGraphicsItem, str] = {}
        self.element_to_item: Dict[str, QGraphicsItem] = {}
    
    def set_edit_mode(self, mode: EditMode):
        """Set the editing mode (normal or composition)."""
        self.constraints.set_edit_mode(mode)
    
    def register_graphics_element(self, graphics_item: QGraphicsItem, element_id: str, 
                                element_type: str, parent_area: Optional[str] = None):
        """Register a graphics item for interactive editing."""
        # Get bounds from graphics item
        bounds_rect = graphics_item.boundingRect()
        pos = graphics_item.pos()
        bounds = Rectangle(
            x=pos.x() + bounds_rect.x(),
            y=pos.y() + bounds_rect.y(),
            width=bounds_rect.width(),
            height=bounds_rect.height()
        )
        
        # Register with constraint system
        element_info = ElementInfo(
            element_id=element_id,
            element_type=element_type,
            bounds=bounds,
            parent_area=parent_area
        )
        self.constraints.register_element(element_info)
        
        # Track graphics item mapping
        self.item_to_element[graphics_item] = element_id
        self.element_to_item[element_id] = graphics_item
        
        # Make item interactive
        graphics_item.setFlag(QGraphicsItem.ItemIsMovable, True)
        graphics_item.setFlag(QGraphicsItem.ItemIsSelectable, True)
        
        # Enable custom drag handling for constraint validation
        if element_type in ["predicate", "vertex"]:
            graphics_item.setFlag(QGraphicsItem.ItemIsMovable, False)  # We'll handle movement manually
    
    def register_cut_hierarchy(self, child_id: str, parent_id: str):
        """Register parent-child relationship between cuts."""
        self.constraints.register_cut_hierarchy(child_id, parent_id)
    
    def handle_item_drag_start(self, graphics_item: QGraphicsItem, start_pos: QPointF):
        """Handle start of item drag operation."""
        if graphics_item not in self.item_to_element:
            return False
        
        self.dragging_item = graphics_item
        self.drag_start_pos = start_pos
        return True
    
    def handle_item_drag_move(self, graphics_item: QGraphicsItem, new_pos: QPointF) -> bool:
        """
        Handle item drag movement with constraint validation.
        Returns True if move is allowed, False if blocked.
        """
        if graphics_item != self.dragging_item or graphics_item not in self.item_to_element:
            return False
        
        element_id = self.item_to_element[graphics_item]
        
        # Validate the move
        is_valid, reason = self.constraints.validate_element_move(element_id, new_pos.x(), new_pos.y())
        
        if is_valid:
            # Update constraint system with new position
            bounds_rect = graphics_item.boundingRect()
            new_bounds = Rectangle(
                x=new_pos.x() + bounds_rect.x(),
                y=new_pos.y() + bounds_rect.y(),
                width=bounds_rect.width(),
                height=bounds_rect.height()
            )
            self.constraints.update_element_bounds(element_id, new_bounds)
            
            # Allow the move
            graphics_item.setPos(new_pos)
            return True
        else:
            # Block the move and provide feedback
            self.operation_blocked.emit("move", reason)
            self._provide_visual_feedback(graphics_item, False)
            return False
    
    def handle_item_drag_end(self, graphics_item: QGraphicsItem, final_pos: QPointF):
        """Handle end of item drag operation."""
        if graphics_item == self.dragging_item and graphics_item in self.item_to_element:
            element_id = self.item_to_element[graphics_item]
            
            # Emit signal for application to update underlying data
            self.element_moved.emit(element_id, final_pos.x(), final_pos.y())
            
            self._clear_visual_feedback(graphics_item)
        
        self.dragging_item = None
        self.drag_start_pos = None
    
    def handle_cut_resize_start(self, cut_item: QGraphicsRectItem, handle_position: str):
        """Handle start of cut resize operation."""
        if cut_item not in self.item_to_element:
            return False
        
        self.resizing_cut = cut_item
        self.resize_handle_pos = handle_position
        return True
    
    def handle_cut_resize_move(self, cut_item: QGraphicsRectItem, new_rect: QRectF) -> bool:
        """
        Handle cut resize with constraint validation.
        Returns True if resize is allowed, False if blocked.
        """
        if cut_item != self.resizing_cut or cut_item not in self.item_to_element:
            return False
        
        element_id = self.item_to_element[cut_item]
        new_bounds = Rectangle(
            x=new_rect.x(),
            y=new_rect.y(),
            width=new_rect.width(),
            height=new_rect.height()
        )
        
        # Validate the resize
        is_valid, reason = self.constraints.validate_cut_resize(element_id, new_bounds)
        
        if is_valid:
            # Update constraint system
            self.constraints.update_element_bounds(element_id, new_bounds)
            
            # Get repositioning suggestions for child elements
            suggestions = self.constraints.get_repositioning_suggestions(element_id, new_bounds)
            
            # Apply repositioning suggestions
            for child_element_id, suggested_bounds in suggestions:
                if child_element_id in self.element_to_item:
                    child_item = self.element_to_item[child_element_id]
                    child_item.setPos(suggested_bounds.x, suggested_bounds.y)
                    self.constraints.update_element_bounds(child_element_id, suggested_bounds)
            
            # Allow the resize
            cut_item.setRect(new_rect)
            return True
        else:
            # Block the resize
            self.operation_blocked.emit("resize", reason)
            self._provide_visual_feedback(cut_item, False)
            return False
    
    def handle_cut_resize_end(self, cut_item: QGraphicsRectItem, final_rect: QRectF):
        """Handle end of cut resize operation."""
        if cut_item == self.resizing_cut and cut_item in self.item_to_element:
            element_id = self.item_to_element[cut_item]
            
            # Emit signal for application to update underlying data
            self.cut_resized.emit(element_id, final_rect)
            
            self._clear_visual_feedback(cut_item)
        
        self.resizing_cut = None
        self.resize_handle_pos = None
    
    def validate_ligature_routing(self, start_element_id: str, end_element_id: str) -> Tuple[bool, str]:
        """Validate if ligature can be routed between two elements."""
        if start_element_id not in self.constraints.elements or end_element_id not in self.constraints.elements:
            return False, "Element not found"
        
        start_element = self.constraints.elements[start_element_id]
        end_element = self.constraints.elements[end_element_id]
        
        # Get center points for ligature routing
        start_x = start_element.bounds.x + start_element.bounds.width / 2
        start_y = start_element.bounds.y + start_element.bounds.height / 2
        end_x = end_element.bounds.x + end_element.bounds.width / 2
        end_y = end_element.bounds.y + end_element.bounds.height / 2
        
        return self.constraints.validate_ligature_path(start_x, start_y, end_x, end_y)
    
    def _provide_visual_feedback(self, graphics_item: QGraphicsItem, is_valid: bool):
        """Provide visual feedback for constraint validation."""
        if isinstance(graphics_item, (QGraphicsRectItem, QGraphicsEllipseItem)):
            # Change outline color to indicate validation state
            pen = graphics_item.pen()
            if is_valid:
                pen.setColor(QColor(0, 255, 0))  # Green for valid
            else:
                pen.setColor(QColor(255, 0, 0))  # Red for invalid
            pen.setWidth(2)
            graphics_item.setPen(pen)
    
    def _clear_visual_feedback(self, graphics_item: QGraphicsItem):
        """Clear visual feedback after operation completes."""
        if isinstance(graphics_item, (QGraphicsRectItem, QGraphicsEllipseItem)):
            # Restore original outline
            pen = graphics_item.pen()
            pen.setColor(QColor(0, 0, 0))  # Black
            pen.setWidth(1)
            graphics_item.setPen(pen)
    
    def update_element_position(self, element_id: str, new_x: float, new_y: float):
        """Update element position in constraint system (called from external updates)."""
        if element_id in self.constraints.elements:
            element = self.constraints.elements[element_id]
            new_bounds = Rectangle(
                x=new_x, y=new_y,
                width=element.bounds.width,
                height=element.bounds.height
            )
            self.constraints.update_element_bounds(element_id, new_bounds)
            
            # Update graphics item position if it exists
            if element_id in self.element_to_item:
                graphics_item = self.element_to_item[element_id]
                graphics_item.setPos(new_x, new_y)
