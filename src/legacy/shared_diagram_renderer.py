"""
Shared diagram rendering module for both Ergasterion and Organon.
Provides consistent ligature rendering with proper text boundary anchoring.
Uses unified style system for consistent appearance across environments.
"""

from typing import Dict, List, Optional, Tuple
from pathlib import Path

from PySide6.QtCore import Qt, QPointF, QRectF, QLineF, QTimer
from PySide6.QtGui import QPen, QBrush, QColor, QPainter
from PySide6.QtWidgets import QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem, QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsItem
from styling.style_manager import StyleManager
from egdf_parser import EGDFDocument


class ConstraintViolationMessage(QGraphicsTextItem):
    """Temporary message showing constraint violations."""
    
    def __init__(self, message: str, position: QPointF):
        super().__init__(message)
        self.setPos(position)
        
        # Style the message
        self.setDefaultTextColor(QColor(255, 0, 0))  # Red text
        font = self.font()
        font.setBold(True)
        font.setPointSize(12)
        self.setFont(font)
        
        # Set background
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        
        # Auto-remove after 3 seconds
        self.timer = QTimer()
        self.timer.timeout.connect(self._remove_self)
        self.timer.setSingleShot(True)
        self.timer.start(3000)
    
    def _remove_self(self):
        """Remove this message from the scene."""
        if self.scene():
            self.scene().removeItem(self)


class ImprovedResizeHandle(QGraphicsRectItem):
    """Enhanced resize handle that properly resizes parent cuts."""
    
    def __init__(self, x, y, w, h, parent_cut, handle_type="bottom-right"):
        super().__init__(x, y, w, h, parent_cut)
        self.parent_cut = parent_cut
        self.handle_type = handle_type
        
        # Style the handle
        self.setPen(QPen(QColor(100, 100, 100), 1))
        self.setBrush(QBrush(QColor(200, 200, 200, 128)))
        
        # Make it interactive
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setZValue(1000)  # Always on top
        
        # Set cursor
        self.setCursor(Qt.CursorShape.SizeFDiagCursor)
    
    def itemChange(self, change, value):
        """Handle resize by updating parent cut dimensions."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.parent_cut:
            new_pos = value
            parent_rect = self.parent_cut.rect()
            parent_pos = self.parent_cut.pos()
            
            # Calculate new dimensions based on handle position
            if self.handle_type == "bottom-right":
                # Handle position is relative to parent
                handle_scene_pos = parent_pos + new_pos
                
                # Calculate new width and height
                new_width = max(50, handle_scene_pos.x() - parent_pos.x())
                new_height = max(50, handle_scene_pos.y() - parent_pos.y())
                
                # Validate the new size doesn't cause invalid overlaps
                new_rect = QRectF(parent_pos.x(), parent_pos.y(), new_width, new_height)
                if self._validate_resize(new_rect):
                    # Update parent cut rectangle
                    self.parent_cut.setRect(QRectF(0, 0, new_width, new_height))
                    
                    # Update handle position to stay at bottom-right corner
                    return QPointF(new_width - self.rect().width()/2, 
                                 new_height - self.rect().height()/2)
                else:
                    # Reject the resize
                    return self.pos()
        
        return super().itemChange(change, value)
    
    def _validate_resize(self, new_rect):
        """Validate that the new cut size doesn't create invalid overlaps."""
        if not self.scene():
            return True
        
        # Check against all other cuts
        for item in self.scene().items():
            if (hasattr(item, 'cut_id') and 
                item != self.parent_cut and 
                hasattr(item, 'sceneBoundingRect')):
                
                other_rect = item.sceneBoundingRect()
                
                if new_rect.intersects(other_rect):
                    # Check if it's proper nesting (one fully contains the other)
                    margin = 5.0  # Small margin for easier nesting
                    new_rect_expanded = new_rect.adjusted(-margin, -margin, margin, margin)
                    other_rect_expanded = other_rect.adjusted(-margin, -margin, margin, margin)
                    
                    if not (new_rect_expanded.contains(other_rect) or 
                           other_rect_expanded.contains(new_rect)):
                        # Partial overlap - not allowed
                        return False
        
        return True


# Keep the old ResizeHandle for backward compatibility
ResizeHandle = ImprovedResizeHandle


class InteractiveVertex(QGraphicsEllipseItem):
    """Vertex that updates connected ligatures when moved."""
    
    def __init__(self, rect: QRectF, vertex_id: str, renderer):
        super().__init__(rect)
        self.vertex_id = vertex_id
        self.renderer = renderer
        
        # Ensure vertex is movable
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
    
    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # DISABLED: Area containment updates cause element jumping
            # Only log position changes for debugging
            if hasattr(self, '_creation_complete') and self._creation_complete:
                print(f"VERTEX MOVED: {self.vertex_id} to {self.pos()}")
        return super().itemChange(change, value)


class InteractivePredicate(QGraphicsTextItem):
    """Interactive predicate text with selection and movement tracking."""
    
    def __init__(self, x, y, text, predicate_id, style_manager):
        super().__init__(text)
        self.predicate_id = predicate_id
        self.style_manager = style_manager
        
        # Apply styling
        style = style_manager.resolve(type="predicate", role="box")
        font_size = int(style.get("font_size", 12))
        
        font = self.font()
        font.setPointSize(font_size)
        self.setFont(font)
        self.setDefaultTextColor(QColor("#000000"))
        
        # Position
        self.setPos(x, y)
        
        # Make interactive
        self.setFlag(self.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(self.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(self.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setZValue(50)  # Above cuts but below ligatures
    
    def paint(self, painter, option, widget):
        """Custom paint method with selection feedback."""
        # Draw the text
        super().paint(painter, option, widget)
        
        # Draw selection outline if selected
        if self.isSelected():
            selection_pen = QPen(QColor("#1E88E5"), 2)
            selection_pen.setStyle(selection_pen.PenStyle.DashLine)
            painter.setPen(selection_pen)
            painter.setBrush(QBrush())
            # Draw rectangle around text
            rect = self.boundingRect().adjusted(-2, -2, 2, 2)
            painter.drawRect(rect)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            # Validate position before allowing move
            new_pos = value
            if not self._validate_position(new_pos):
                return self.pos()  # Reject the move
        elif change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Update area containment in drawing schema only - no rendering needed
            self.renderer._update_element_area_containment(self.predicate_id, self.pos())
        return super().itemChange(change, value)
    
    def _validate_position(self, new_pos):
        """Validate predicate position against syntactic and semantic constraints."""
        if not hasattr(self, 'scene') or not self.scene():
            return True
            
        # Get proposed new rectangle
        new_rect = QRectF(new_pos.x(), new_pos.y(), self.boundingRect().width(), self.boundingRect().height())
        
        # Check for overlaps with other predicates (syntactic constraint)
        for item in self.scene().items():
            if isinstance(item, InteractivePredicate) and item != self:
                other_pos = item.pos()
                other_rect = QRectF(other_pos.x(), other_pos.y(), item.boundingRect().width(), item.boundingRect().height())
                if new_rect.intersects(other_rect):
                    self._show_violation_message(f"SYNTACTIC VIOLATION: Predicate {self.predicate_id} not permitted to overlap with Predicate {item.predicate_id}", new_pos)
                    return False
        
        # Check semantic constraints - predicate must stay within its containing cut
        current_pos = self.pos()
        current_rect = QRectF(current_pos.x(), current_pos.y(), self.boundingRect().width(), self.boundingRect().height())
        
        
        # Find the cut that currently contains this predicate
        containing_cut = None
        for item in self.scene().items():
            if isinstance(item, StyledCutItem):
                cut_pos = item.pos()
                cut_rect = QRectF(cut_pos.x(), cut_pos.y(), item.rect().width(), item.rect().height())
                if cut_rect.contains(current_rect):
                    containing_cut = item
                    break
        
        # If predicate is in a cut, ensure it stays in that cut
        if containing_cut:
            cut_pos = containing_cut.pos()
            cut_rect = QRectF(cut_pos.x(), cut_pos.y(), containing_cut.rect().width(), containing_cut.rect().height())
            if not cut_rect.contains(new_rect):
                self._show_violation_message(f"SEMANTIC VIOLATION: Predicate {self.predicate_id} not permitted to move outside containing Cut {containing_cut.cut_id}", new_pos)
                return False
        
        return True
    
    def _show_violation_message(self, message: str, position: QPointF):
        """Show a temporary violation message in the GUI."""
        if self.scene():
            violation_msg = ConstraintViolationMessage(message, position)
            self.scene().addItem(violation_msg)


class StyledCutItem(QGraphicsRectItem):
    """Cut item with unified styling and interactive capabilities."""
    
    def __init__(self, rect: QRectF, cut_id: str, style_manager: StyleManager, interactive: bool = True, validation_mode: str = "composition", nesting_depth: int = 0):
        super().__init__(rect)
        self.cut_id = cut_id
        self.style_manager = style_manager
        self.interactive = interactive
        self.validation_mode = validation_mode  # "composition" or "practice"
        self.nesting_depth = nesting_depth
        
        # Apply nesting-aware styling
        self._apply_nesting_style()
        
        if interactive:
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
            self.setAcceptHoverEvents(True)
            
        self.resize_mode = False
        print(f"DEBUG: Created enhanced StyledCutItem {cut_id} with interactive={interactive}, validation_mode={validation_mode}, depth={nesting_depth}")
        
        # Enhanced resize handles
        self.resize_handles = []
        
        # Track last position for moving contained elements
        self._last_position = self.pos()
    
    def _apply_nesting_style(self):
        """Apply visual styling based on nesting depth."""
        # Different colors/styles for different nesting levels
        colors = [
            QColor(0, 0, 0),      # Level 0: Black
            QColor(100, 0, 0),    # Level 1: Dark red
            QColor(0, 100, 0),    # Level 2: Dark green
            QColor(0, 0, 100),    # Level 3: Dark blue
            QColor(100, 100, 0),  # Level 4: Dark yellow
        ]
        
        color_index = self.nesting_depth % len(colors)
        pen_color = colors[color_index]
        
        # Thicker lines for deeper nesting
        line_width = 1 + self.nesting_depth
        
        self.setPen(QPen(pen_color, line_width))
        self.setBrush(QBrush(QColor("transparent")))
    
    def hoverEnterEvent(self, event):
        """Show resize handles when hovering."""
        print(f"DEBUG: Cut {self.cut_id} hoverEnterEvent - interactive={self.interactive}")
        if self.interactive:
            self._show_resize_handles()
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Hide resize handles when not hovering."""
        if self.interactive:
            self._hide_resize_handles()
        super().hoverLeaveEvent(event)
    
    def _show_resize_handles(self):
        """Show resize handles at corners."""
        if self.resize_handles:
            return  # Already showing
        
        rect = self.rect()
        handle_size = 8
        
        # Bottom-right handle
        handle = ImprovedResizeHandle(
            rect.right() - handle_size/2,
            rect.bottom() - handle_size/2,
            handle_size, handle_size,
            self, "bottom-right"
        )
        
        self.resize_handles.append(handle)
        if self.scene():
            self.scene().addItem(handle)
    
    def _hide_resize_handles(self):
        """Hide resize handles."""
        for handle in self.resize_handles:
            if self.scene():
                self.scene().removeItem(handle)
        self.resize_handles.clear()
    
    def itemChange(self, change, value):
        """Enhanced position validation with proper nesting support."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            new_pos = value
            if not self._validate_position(new_pos):
                return self.pos()  # Reject the move
        elif change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._move_contained_elements()
            self._update_nesting_depth()
        elif change == QGraphicsItem.GraphicsItemChange.ItemSceneHasChanged:
            # Scene changed
            pass
        
        return super().itemChange(change, value)
    
    def _update_nesting_depth(self):
        """Update nesting depth based on current position."""
        if not self.scene():
            return
        
        depth = 0
        current_rect = self.sceneBoundingRect()
        
        # Count how many cuts contain this one
        for item in self.scene().items():
            if (hasattr(item, 'cut_id') and 
                item != self and 
                hasattr(item, 'sceneBoundingRect')):
                
                other_rect = item.sceneBoundingRect()
                if other_rect.contains(current_rect):
                    depth += 1
        
        if depth != self.nesting_depth:
            self.nesting_depth = depth
            self._apply_nesting_style()
    
    def _validate_position(self, new_pos):
        """Validate cut position against syntactic and semantic constraints."""
        if not hasattr(self, 'scene') or not self.scene():
            return True
            
        # Get proposed new rectangle
        new_rect = QRectF(new_pos.x(), new_pos.y(), self.rect().width(), self.rect().height())
        
        # Check for overlaps with other cuts (syntactic constraint)
        # Allow containment (one cut fully inside another) but not partial overlaps
        for item in self.scene().items():
            if isinstance(item, StyledCutItem) and item != self:
                other_pos = item.pos()
                other_rect = QRectF(other_pos.x(), other_pos.y(), item.rect().width(), item.rect().height())
                if new_rect.intersects(other_rect):
                    # Check if one cut is fully contained within the other (allowed)
                    # Use a larger margin to make nesting easier
                    margin = 20.0
                    new_rect_expanded = new_rect.adjusted(-margin, -margin, margin, margin)
                    other_rect_expanded = other_rect.adjusted(-margin, -margin, margin, margin)
                    
                    if new_rect_expanded.contains(other_rect) or other_rect_expanded.contains(new_rect):
                        print(f"DEBUG: Allowing cut containment: {self.cut_id} and {item.cut_id}")
                        continue  # Containment is allowed
                    
                    # Partial overlap - try collision avoidance first
                    if self._attempt_collision_avoidance(new_pos):
                        return True  # Avoidance successful, allow move
                    else:
                        self._show_violation_message(f"SYNTACTIC VIOLATION: Cut {self.cut_id} not permitted to partially overlap with Cut {item.cut_id}", new_pos)
                        return False
        
        # Only check semantic constraints in practice mode, not composition mode
        if self.validation_mode == "practice":
            # Check semantic constraints - cut must still contain its predicates
            current_pos = self.pos()
            current_rect = QRectF(current_pos.x(), current_pos.y(), self.rect().width(), self.rect().height())
            
            # Find predicates currently inside this cut
            contained_predicates = []
            for item in self.scene().items():
                if isinstance(item, InteractivePredicate):
                    pred_pos = item.pos()
                    pred_rect = QRectF(pred_pos.x(), pred_pos.y(), item.boundingRect().width(), item.boundingRect().height())
                    if current_rect.contains(pred_rect):
                        contained_predicates.append(item)
            
            # Ensure new position still contains all predicates
            for pred in contained_predicates:
                pred_pos = pred.pos()
                pred_rect = QRectF(pred_pos.x(), pred_pos.y(), pred.boundingRect().width(), pred.boundingRect().height())
                if not new_rect.contains(pred_rect):
                    self._show_violation_message(f"SEMANTIC VIOLATION: Cut {self.cut_id} not permitted to move away from enclosed Predicate {pred.predicate_id}", new_pos)
                    return False
        
        return True
    
    def _move_contained_elements(self):
        """Move all elements contained within this cut when the cut moves."""
        if not hasattr(self, 'scene') or not self.scene():
            return
            
        # Get the movement delta
        if not hasattr(self, '_last_position'):
            self._last_position = self.pos()
            return
            
        current_pos = self.pos()
        delta = current_pos - self._last_position
        self._last_position = current_pos
        
        # If no movement, return
        if delta.x() == 0 and delta.y() == 0:
            return
        
        # Get current cut bounds (before movement)
        cut_rect = QRectF((current_pos - delta).x(), (current_pos - delta).y(), self.rect().width(), self.rect().height())
        
        # Move all contained predicates and vertices
        for item in self.scene().items():
            if item == self:
                continue
                
            # Check if item is contained within this cut
            if isinstance(item, (InteractivePredicate, InteractiveVertex)):
                item_pos = item.pos()
                item_rect = QRectF(item_pos.x(), item_pos.y(), item.boundingRect().width(), item.boundingRect().height())
                
                # Check if item was inside this cut before movement
                if cut_rect.contains(item_rect.center()):
                    # Move the item by the same delta
                    new_item_pos = item_pos + delta
                    item.setPos(new_item_pos)
                    
                    # Update ligatures if it's a predicate or vertex
                    if hasattr(item, 'renderer'):
                        if isinstance(item, InteractivePredicate):
                            item.renderer.update_ligatures_for_predicate(item.predicate_id)
                        elif isinstance(item, InteractiveVertex):
                            item.renderer.update_ligatures_for_vertex(item.vertex_id)
    
    def _show_violation_message(self, message: str, position: QPointF):
        """Show a temporary violation message in the GUI."""
        if self.scene():
            violation_msg = ConstraintViolationMessage(message, position)
            self.scene().addItem(violation_msg)
    
    def _attempt_collision_avoidance(self, new_pos):
        """Try to move overlapping elements out of the way instead of blocking the move."""
        if not hasattr(self, 'scene') or not self.scene():
            return False
            
        new_rect = QRectF(new_pos.x(), new_pos.y(), self.rect().width(), self.rect().height())
        moved_items = []
        
        # Find all overlapping cuts
        for item in self.scene().items():
            if isinstance(item, StyledCutItem) and item != self:
                other_pos = item.pos()
                other_rect = QRectF(other_pos.x(), other_pos.y(), item.rect().width(), item.rect().height())
                
                if new_rect.intersects(other_rect):
                    # Calculate avoidance direction - push away from center of moving cut
                    center_diff = other_rect.center() - new_rect.center()
                    
                    # Determine primary direction (horizontal or vertical)
                    if abs(center_diff.x()) > abs(center_diff.y()):
                        # Move horizontally
                        avoid_x = other_pos.x() + (50 if center_diff.x() > 0 else -50)
                        avoid_pos = QPointF(avoid_x, other_pos.y())
                    else:
                        # Move vertically  
                        avoid_y = other_pos.y() + (50 if center_diff.y() > 0 else -50)
                        avoid_pos = QPointF(other_pos.x(), avoid_y)
                    
                    # Check if avoidance position is valid
                    if self._is_valid_avoidance_position(item, avoid_pos):
                        item.setPos(avoid_pos)
                        moved_items.append((item, other_pos))  # Store original position for rollback
                    else:
                        # Rollback any moves we made
                        for moved_item, orig_pos in moved_items:
                            moved_item.setPos(orig_pos)
                        return False
        
        return True
    
    def _is_valid_avoidance_position(self, item, new_pos):
        """Check if an avoidance position is valid (doesn't create new overlaps)."""
        if not item.scene():
            return True
            
        new_rect = QRectF(new_pos.x(), new_pos.y(), item.rect().width(), item.rect().height())
        
        # Check against all other cuts
        for other_item in item.scene().items():
            if isinstance(other_item, StyledCutItem) and other_item != item and other_item != self:
                other_pos = other_item.pos()
                other_rect = QRectF(other_pos.x(), other_pos.y(), other_item.rect().width(), other_item.rect().height())
                if new_rect.intersects(other_rect):
                    return False
        
        return True
    
    def _validate_resize(self, new_rect):
        """Validate cut resize doesn't cause overlaps."""
        if not hasattr(self, 'scene') or not self.scene():
            return True
            
        # Convert rect to scene coordinates using current position
        current_pos = self.pos()
        scene_rect = QRectF(
            current_pos.x() + new_rect.x(),
            current_pos.y() + new_rect.y(), 
            new_rect.width(),
            new_rect.height()
        )
        
        # Check for overlaps with other cuts
        for item in self.scene().items():
            if isinstance(item, StyledCutItem) and item != self:
                other_pos = item.pos()
                other_rect = QRectF(other_pos.x(), other_pos.y(), item.rect().width(), item.rect().height())
                if scene_rect.intersects(other_rect):
                    # Show violation message but allow resize (less strict than movement)
                    self._show_violation_message(f"RESIZE WARNING: Cut {self.cut_id} overlapping with Cut {item.cut_id}", current_pos)
                    # Allow resize but warn user
                    return True
        
        return True
    
    def mousePressEvent(self, event):
        """Handle mouse press for resize or move operations."""
        print(f"DEBUG: Cut {self.cut_id} mousePressEvent - interactive={self.interactive}, button={event.button()}")
        if not self.interactive:
            return super().mousePressEvent(event)
            
        if event.button() == Qt.LeftButton:
            if self.resize_mode:
                # Start resize operation
                self.resize_start_pos = event.pos()
                self.resize_start_rect = self.rect()
                event.accept()
                print(f"DEBUG: Cut {self.cut_id} starting resize")
            else:
                # Start move operation
                print(f"DEBUG: Cut {self.cut_id} starting move")
                super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move for resize or move operations."""
        if not self.interactive:
            return super().mouseMoveEvent(event)
            
        if self.resize_mode and hasattr(self, 'resize_start_pos'):
            # Perform resize operation
            delta = event.pos() - self.resize_start_pos
            new_width = max(50, self.resize_start_rect.width() + delta.x())
            new_height = max(50, self.resize_start_rect.height() + delta.y())
            
            new_rect = QRectF(
                self.resize_start_rect.x(),
                self.resize_start_rect.y(),
                new_width,
                new_height
            )
            
            # Validate resize doesn't cause overlaps
            if self._validate_resize(new_rect):
                self.setRect(new_rect)
            event.accept()
        else:
            # Normal move operation
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release to end resize operation."""
        if not self.interactive:
            return super().mouseReleaseEvent(event)
            
        if hasattr(self, 'resize_start_pos'):
            delattr(self, 'resize_start_pos')
            delattr(self, 'resize_start_rect')
        
        super().mouseReleaseEvent(event)
    
    def paint(self, painter, _option, widget=None):
        """Draw cut using unified style system with annotation support."""
        r = self.rect()
        
        # Check for annotation state
        annotation_state = self.data(0) or "normal"
        
        # Resolve style from unified system
        if annotation_state == "double_cut":
            # Use red color for double cut annotation
            style = {"radius": 10, "line_color": "#FF0000", "line_width": 2, "fill_color": "transparent"}
        else:
            style = self.style_manager.resolve(type="cut", role="border")
        
        radius = float(style.get("radius", 10))
        line_color = style.get("line_color", "#000000")
        line_width = int(style.get("line_width", 1))
        
        # Resolve fill style
        fill_style = self.style_manager.resolve(type="cut", role="fill", state="even")
        fill_color = fill_style.get("fill_color", "transparent")
        
        # Clamp radius so corners meet smoothly even when tiny
        max_rx = max(0.0, min(radius, r.width() / 2.0))
        max_ry = max(0.0, min(radius, r.height() / 2.0))
        
        # Apply styling
        pen = QPen(QColor(line_color), line_width)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        
        if fill_color == "transparent":
            painter.setBrush(QBrush(QColor(0, 0, 0, 0)))
        else:
            painter.setBrush(QBrush(QColor(fill_color)))
        
        painter.drawRoundedRect(r, max_rx, max_ry)


class SharedDiagramRenderer:
    """Unified diagram renderer with cross-platform styling support."""
    
    def __init__(self, scene: QGraphicsScene, style_manager: StyleManager):
        self.scene = scene
        self.style_manager = style_manager
        self.cut_items = {}  # Track cut items for updates
        self.vertex_items = {}  # Track vertex items
        self.predicate_items = {}  # Track predicate items
        self.ligature_map = {}  # Map edge_id to list of ligature lines
        self.element_positions = {}  # Track element positions for ligature updates
        
        # Annotation system
        self.annotations_enabled = {
            'arity': False,
            'variable': False,
            'cut_id': False,
            'predicate_id': False,
            'vertex_id': False
        }
    
    def calculate_nesting_depth(self, position: QPointF) -> int:
        """Calculate the nesting depth at a given position based on containing cuts."""
        depth = 0
        for item in self.scene.items():
            if isinstance(item, StyledCutItem):
                item_pos = item.pos()
                item_rect = QRectF(item_pos.x(), item_pos.y(), item.rect().width(), item.rect().height())
                if item_rect.contains(position):
                    depth += 1
        return depth
    
    def render_egdf(self, doc: EGDFDocument, interactive: bool = True) -> None:
        """Render EGDF document with proper ligature anchoring."""
        print(f"SharedDiagramRenderer.render_egdf called")
        
        # DISABLED: Scene clearing causes element jumping during interactive editing
        # Only clear scene if starting fresh, otherwise update incrementally
        # if not hasattr(self, '_incremental_mode') or not self._incremental_mode:
        #     self.scene.clear()
        #     # Clear annotation tracking only when clearing scene
        #     self.cut_items.clear()
        #     self.predicate_items.clear()
        #     self.vertex_items.clear()
        
        layout = doc.layout or {}
        egi_inline = doc.egi_ref.get("inline", {}) if isinstance(doc.egi_ref, dict) else {}
        
        print(f"Layout keys: {list(layout.keys())}")
        
        # Store interactive mode for use in rendering
        self.interactive_mode = interactive
        
        # Store EGI data for annotations
        self.current_egi_inline = egi_inline
        
        # Draw cuts first (lowest z-order)
        cuts = layout.get("cuts", {})
        print(f"Drawing {len(cuts)} cuts")
        for cut_id, cut_data in cuts.items():
            self.render_cut(cut_data, interactive)
        
        # Draw vertices
        vertices = layout.get("vertices", {})
        print(f"Drawing {len(vertices)} vertices")
        for vertex_id, vertex_data in vertices.items():
            print(f"Drawing vertex {vertex_id} at ({vertex_data.get('x')}, {vertex_data.get('y')})")
            # Ensure vertex_data has the ID
            vertex_data_with_id = dict(vertex_data)
            vertex_data_with_id["id"] = vertex_id
            self._draw_vertex(vertex_data_with_id)
        
        # Draw predicates and collect their scene rectangles
        predicates = layout.get("predicates", {})
        predicate_rects = {}
        print(f"Drawing {len(predicates)} predicates")
        for pred_id, pred_data in predicates.items():
            print(f"Drawing predicate {pred_id}: '{pred_data.get('text')}' at ({pred_data.get('x')}, {pred_data.get('y')})")
            # Ensure pred_data has the ID
            pred_data_with_id = dict(pred_data)
            pred_data_with_id["id"] = pred_id
            text_item = self._draw_predicate(pred_data_with_id)
            predicate_rects[pred_id] = text_item.sceneBoundingRect()
        
        # Draw ligatures with proper boundary anchoring
        nu_map = egi_inline.get("nu", {})
        print(f"Drawing ligatures for {len(nu_map)} edges")
        self._draw_ligatures(nu_map, predicate_rects, vertices)
        
        print(f"Rendering complete. Scene has {len(self.scene.items())} items")
        
        # Update annotations after all items are rendered
        self._update_annotations()
        
        # Always show vertex names when defined (not part of annotations)
        self._render_vertex_names()
    
    def update_ligatures_for_vertex(self, vertex_id: str) -> None:
        """Update ligatures connected to a vertex when it moves."""
        print(f"Updating ligatures for vertex {vertex_id}")
        
        # Get current vertex position
        vertex_item = None
        for item in self.scene.items():
            if isinstance(item, InteractiveVertex) and item.vertex_id == vertex_id:
                vertex_item = item
                break
        
        if not vertex_item:
            print(f"Could not find vertex item for {vertex_id}")
            return
        
        vertex_pos = vertex_item.sceneBoundingRect().center()
        print(f"Vertex {vertex_id} new position: {vertex_pos}")
        
        # Find ligatures that connect to this vertex by checking the stored positions
        old_vertex_pos = self.element_positions.get(vertex_id)
        if not old_vertex_pos:
            print(f"No stored position for vertex {vertex_id}")
            return
            
        print(f"Old vertex position: {old_vertex_pos}")
        
        # Update all ligature lines that connect to this vertex
        updated_count = 0
        for edge_id, lines in self.ligature_map.items():
            for line in lines:
                old_line = line.line()
                
                # Check if this line's p2 (vertex end) matches the old vertex position
                p2_match = (abs(old_line.p2().x() - old_vertex_pos.x()) < 2 and 
                           abs(old_line.p2().y() - old_vertex_pos.y()) < 2)
                p1_match = (abs(old_line.p1().x() - old_vertex_pos.x()) < 2 and 
                           abs(old_line.p1().y() - old_vertex_pos.y()) < 2)
                
                if p2_match:
                    # Update the vertex end of the line to new position
                    line.setLine(QLineF(old_line.p1(), vertex_pos))
                    updated_count += 1
                elif p1_match:
                    # Update the vertex end of the line to new position
                    line.setLine(QLineF(vertex_pos, old_line.p2()))
                    updated_count += 1
        
        print(f"Updated {updated_count} ligature lines for vertex {vertex_id}")
        
        # Update stored position
        self.element_positions[vertex_id] = vertex_pos
    
    def update_ligatures_for_predicate(self, predicate_id: str) -> None:
        """Update ligatures connected to a predicate when it moves."""
        # Find ligatures for this predicate and update their anchor points
        if predicate_id in self.ligature_map:
            lines = self.ligature_map[predicate_id]
            # Get current predicate position
            for item in self.scene.items():
                if isinstance(item, InteractivePredicate) and item.predicate_id == predicate_id:
                    new_rect = item.sceneBoundingRect()
                    # Update all ligature lines for this predicate
                    for line in lines:
                        old_line = line.line()
                        # Update anchor point but keep vertex end
                        vertex_pos = old_line.p2()
                        new_anchor = self._rect_border_anchor(new_rect, vertex_pos)
                        line.setLine(QLineF(new_anchor, vertex_pos))
                    break
    
    def render_cut(self, cut_dto, interactive: bool = True) -> StyledCutItem:
        """Render a cut directly from EGI DTO."""
        # Handle both DTO and dict for backward compatibility
        if hasattr(cut_dto, 'spatial'):
            x = cut_dto.spatial.x
            y = cut_dto.spatial.y
            width = cut_dto.spatial.width
            height = cut_dto.spatial.height
            cut_id = cut_dto.id
        else:
            # Legacy dict format
            x = float(cut_dto.get('x', 0))
            y = float(cut_dto.get('y', 0))
            width = float(cut_dto.get('width', 100))
            height = float(cut_dto.get('height', 100))
            cut_id = cut_dto.get('id', 'unknown_cut')
        
        # Create rect at origin, then position the item
        rect = QRectF(0, 0, width, height)
        # Calculate nesting depth for this cut
        cut_center = QPointF(x + width/2, y + height/2)
        depth = self.calculate_nesting_depth(cut_center)
        
        cut_item = StyledCutItem(rect, cut_id, self.style_manager, interactive, validation_mode="composition", nesting_depth=depth)
        cut_item.setPos(x, y)  # Set position separately for proper coordinate handling
        cut_item.setZValue(depth * 100 - 10)  # Cut z-order based on nesting depth
        
        # Ensure interactivity is properly set
        if interactive:
            cut_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
            cut_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
            cut_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
            cut_item.setAcceptHoverEvents(True)
            print(f"DEBUG: Cut {cut_id} configured as interactive with flags: movable={cut_item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable}, selectable={cut_item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable}")
        
        self.scene.addItem(cut_item)
        self.cut_items[cut_id] = cut_item
        
        return cut_item
    
    def toggle_annotation(self, annotation_type: str, enabled: bool) -> None:
        """Toggle annotation display for specific type."""
        if annotation_type in self.annotations_enabled:
            self.annotations_enabled[annotation_type] = enabled
            self._update_annotations()
    
    def identify_double_cuts(self) -> List[Tuple[str, str]]:
        """Identify double cuts - nested cuts with only ligatures between them."""
        double_cuts = []
        
        # Look for nested cuts with nothing between them except traversing ligatures
        for outer_id, outer_item in self.cut_items.items():
            outer_rect = outer_item.rect()
            
            for inner_id, inner_item in self.cut_items.items():
                if outer_id == inner_id:
                    continue
                    
                inner_rect = inner_item.rect()
                
                # Check if inner is contained within outer
                if outer_rect.contains(inner_rect):
                    # Check if the area between cuts contains only ligatures
                    if self._is_valid_double_cut(outer_rect, inner_rect, outer_id, inner_id):
                        double_cuts.append((outer_id, inner_id))
        
        return double_cuts
    
    def _is_valid_double_cut(self, outer_rect: QRectF, inner_rect: QRectF, outer_id: str, inner_id: str) -> bool:
        """Check if the area between two cuts contains only ligatures (valid double cut)."""
        # Get all scene items in the area between the cuts
        between_area = outer_rect.intersected(outer_rect)  # Start with outer rect
        
        # Check all scene items
        for item in self.scene.items():
            item_rect = item.sceneBoundingRect()
            
            # Skip the cuts themselves
            if (hasattr(item, 'cut_id') and 
                (getattr(item, 'cut_id', None) == outer_id or getattr(item, 'cut_id', None) == inner_id)):
                continue
            
            # Check if item is in the area between cuts
            if (outer_rect.intersects(item_rect) and not inner_rect.contains(item_rect)):
                # Item is between the cuts
                
                # Allow ligatures (lines) that traverse through both cuts
                if isinstance(item, QGraphicsLineItem):
                    line = item.line()
                    start_in_outer = outer_rect.contains(line.p1())
                    end_in_outer = outer_rect.contains(line.p2())
                    start_in_inner = inner_rect.contains(line.p1())
                    end_in_inner = inner_rect.contains(line.p2())
                    
                    # Allow if ligature traverses through both cuts or connects across them
                    if ((start_in_outer and not start_in_inner) or 
                        (end_in_outer and not end_in_inner) or
                        (start_in_inner and end_in_outer) or
                        (end_in_inner and start_in_outer)):
                        continue
                
                # Disallow vertices, predicates, or other cuts between the double cut
                if (isinstance(item, QGraphicsTextItem) or  # Predicates
                    isinstance(item, QGraphicsEllipseItem) or  # Vertices  
                    (hasattr(item, 'cut_id') and getattr(item, 'cut_id', None) not in [outer_id, inner_id])):  # Other cuts
                    return False
        
        return True
    
    def _update_annotations(self) -> None:
        """Update all annotation displays based on current settings."""
        self._update_double_cut_annotations()
        self._update_predicate_arity_annotations()
        self._update_vertex_variable_annotations()
    
    def _update_double_cut_annotations(self) -> None:
        """Update double cut color annotations."""
        if self.annotations_enabled['double_cuts']:
            double_cuts = self.identify_double_cuts()
            
            # Reset all cuts to normal color
            for cut_item in self.cut_items.values():
                cut_item.setData(0, "normal")  # Store annotation state
            
            # Highlight double cuts in red
            for outer_id, inner_id in double_cuts:
                if outer_id in self.cut_items:
                    self.cut_items[outer_id].setData(0, "double_cut")
                if inner_id in self.cut_items:
                    self.cut_items[inner_id].setData(0, "double_cut")
        else:
            # Reset all cuts to normal
            for cut_item in self.cut_items.values():
                cut_item.setData(0, "normal")
        
        # Trigger repaint
        for cut_item in self.cut_items.values():
            cut_item.update()
    
    def _update_predicate_arity_annotations(self) -> None:
        """Update predicate arity number annotations."""
        # Remove existing arity annotations
        for item in self.scene.items():
            if hasattr(item, 'annotation_type') and item.annotation_type == 'arity':
                self.scene.removeItem(item)
        
        if self.annotations_enabled['predicate_arity']:
            for pred_id, pred_item in self.predicate_items.items():
                # Get arity from EGI data if available
                arity = self._get_predicate_arity(pred_id)
                if arity is not None:
                    self._add_arity_annotation(pred_item, arity)
    
    def _update_vertex_variable_annotations(self) -> None:
        """Update vertex variable name annotations."""
        # Remove existing variable annotations
        for item in self.scene.items():
            if hasattr(item, 'annotation_type') and item.annotation_type == 'variable':
                self.scene.removeItem(item)
        
        if self.annotations_enabled['vertex_variables']:
            for vertex_id, vertex_item in self.vertex_items.items():
                # Get variable name from EGI data if available
                var_name = self._get_vertex_variable_name(vertex_id)
                if var_name:
                    self._add_variable_annotation(vertex_item, var_name)
    
    def _get_predicate_arity(self, predicate_id: str) -> Optional[int]:
        """Get arity for predicate from EGI data."""
        if not hasattr(self, 'current_egi_inline') or not self.current_egi_inline:
            return None
            
        # Get nu mapping (edges to vertices)
        nu_map = self.current_egi_inline.get("nu", {})
        if predicate_id in nu_map:
            # Arity is the number of connected vertices
            return len(nu_map[predicate_id])
        
        return None
    
    def _get_vertex_variable_name(self, vertex_id: str) -> Optional[str]:
        """Get variable name for vertex from EGI data (for annotation only)."""
        if not hasattr(self, 'current_egi_inline') or not self.current_egi_inline:
            return None
            
        # Get rho mapping (vertices to variable names)
        rho_map = self.current_egi_inline.get("rho", {})
        if vertex_id in rho_map:
            name = rho_map[vertex_id]
            if name is None:
                return None
            # Only show variables (*x, *y) for annotation, not actual names
            if len(name) == 1 and name.islower():
                return f"*{name}"
        
        return None
    
    def _get_vertex_name(self, vertex_id: str) -> Optional[str]:
        """Get actual name for vertex from EGI data (always displayed when defined)."""
        if not hasattr(self, 'current_egi_inline') or not self.current_egi_inline:
            return None
            
        # Get rho mapping (vertices to names)
        rho_map = self.current_egi_inline.get("rho", {})
        if vertex_id in rho_map:
            name = rho_map[vertex_id]
            if name is None:
                return None
            # Only show actual names (Socrates, John, etc.), not variables
            if len(name) > 1 or not name.islower():
                return name
        
        return None
    
    def _render_vertex_names(self) -> None:
        """Render vertex names that are always visible (not part of annotations)."""
        # Remove existing vertex name displays
        for item in self.scene.items():
            if hasattr(item, 'display_type') and item.display_type == 'vertex_name':
                self.scene.removeItem(item)
        
        # Add vertex names for all vertices that have defined names
        for vertex_id, vertex_item in self.vertex_items.items():
            vertex_name = self._get_vertex_name(vertex_id)
            if vertex_name:
                self._add_vertex_name_display(vertex_item, vertex_name)
    
    def _add_arity_annotation(self, predicate_item: QGraphicsTextItem, arity: int) -> None:
        """Add small arity number annotation to predicate."""
        from PySide6.QtWidgets import QGraphicsTextItem
        from PySide6.QtGui import QFont
        
        annotation = QGraphicsTextItem(str(arity))
        annotation.annotation_type = 'arity'
        
        # Small font for annotation
        font = QFont()
        font.setPointSize(8)
        annotation.setFont(font)
        
        # Position near predicate (top-right corner)
        pred_rect = predicate_item.boundingRect()
        annotation.setPos(
            predicate_item.x() + pred_rect.width() + 2,
            predicate_item.y() - 2
        )
        
        self.scene.addItem(annotation)
    
    def _add_variable_annotation(self, vertex_item: QGraphicsItem, var_name: str) -> None:
        """Add variable name annotation to vertex."""
        from PySide6.QtWidgets import QGraphicsTextItem
        from PySide6.QtGui import QFont
        
        annotation = QGraphicsTextItem(var_name)
        annotation.annotation_type = 'variable'
        
        # Small font for annotation
        font = QFont()
        font.setPointSize(8)
        annotation.setFont(font)
        
        # Position near vertex (below and to the right)
        vertex_rect = vertex_item.boundingRect()
        # Use rect coordinates since vertex position is baked into boundingRect
        annotation.setPos(
            vertex_rect.x() + vertex_rect.width() + 2,
            vertex_rect.y() + vertex_rect.height() + 2
        )
        
        self.scene.addItem(annotation)
    
    def _add_vertex_name_display(self, vertex_item: QGraphicsItem, vertex_name: str) -> None:
        """Add vertex name display that's always visible (not an annotation)."""
        from PySide6.QtWidgets import QGraphicsTextItem
        from PySide6.QtGui import QFont
        
        name_display = QGraphicsTextItem(vertex_name)
        name_display.display_type = 'vertex_name'  # Mark as permanent display
        
        # Normal font for vertex names (larger than annotations)
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        name_display.setFont(font)
        
        # Position near vertex (below and to the right)
        vertex_rect = vertex_item.boundingRect()
        # Use rect coordinates since vertex position is baked into boundingRect
        name_display.setPos(
            vertex_rect.x() + vertex_rect.width() + 5,
            vertex_rect.y() + vertex_rect.height() + 5
        )
        
        self.scene.addItem(name_display)
    
    def _draw_cut(self, cut_data: Dict, interactive: bool = True, validation_mode: str = "composition", depth: int = 0) -> None:
        """Draw a cut (rectangle) at the specified coordinates."""
        x = cut_data.get("x", 0)
        y = cut_data.get("y", 0)
        w = cut_data.get("w", 100)
        h = cut_data.get("h", 100)
        cut_id = cut_data.get("id", "")
        
        # Check if cut already exists
        if cut_id in self.cut_items:
            existing_cut = self.cut_items[cut_id]
            try:
                # Update position and size if needed
                existing_cut.setPos(x, y)
                existing_cut.setRect(QRectF(0, 0, w, h))  # Rect is relative to item position
                return
            except RuntimeError:
                # Object was deleted, remove from tracking
                del self.cut_items[cut_id]
        
        rect = StyledCutItem(QRectF(x, y, w, h), cut_id, self.style_manager, interactive=interactive, validation_mode=validation_mode, nesting_depth=depth)
        rect.setZValue(depth * 100 - 10)  # Cut z-order based on nesting depth
        # Configure cut interaction - allow all mouse events but with lower priority  
        rect.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        rect.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        # Don't restrict mouse buttons - let all events pass through when not directly on cut border
        self.scene.addItem(rect)
        self.cut_items[cut_id] = rect  # Track the cut item
    
    def render_vertex(self, vertex_dto, gui_x: float = None, gui_y: float = None) -> InteractiveVertex:
        """Draw a vertex (dot) at the specified coordinates."""
        # Use GUI coordinates if provided, otherwise extract from DTO
        if gui_x is not None and gui_y is not None:
            x = gui_x
            y = gui_y
            print(f"RENDER VERTEX: Using GUI coordinates ({x}, {y})")
        elif hasattr(vertex_dto, 'spatial'):
            x = vertex_dto.spatial.x
            y = vertex_dto.spatial.y
            print(f"RENDER VERTEX: Using DTO coordinates ({x}, {y})")
        else:
            # Legacy dict format
            x = vertex_dto.get("x", 0)
            y = vertex_dto.get("y", 0)
            print(f"RENDER VERTEX: Using legacy coordinates ({x}, {y})")
        
        if hasattr(vertex_dto, 'id'):
            vertex_id = vertex_dto.id
        else:
            vertex_id = vertex_dto.get("id", "")
        
        # Check if vertex already exists - don't move it if it does
        if vertex_id in self.vertex_items:
            existing_vertex = self.vertex_items[vertex_id]
            try:
                print(f"RENDER VERTEX: Vertex {vertex_id} already exists, returning existing")
                return existing_vertex
            except RuntimeError:
                # Object was deleted, remove from tracking
                del self.vertex_items[vertex_id]
        
        # Get styling
        style = self.style_manager.resolve(type="vertex", role="dot")
        radius = float(style.get("radius", 8))
        
        # Calculate depth for z-ordering
        depth = self.calculate_nesting_depth(QPointF(x, y))
        
        # Create interactive vertex with correct constructor
        from PySide6.QtCore import QRectF
        # Create rect at origin, then position the item
        rect = QRectF(-radius, -radius, 2 * radius, 2 * radius)
        dot = InteractiveVertex(rect, vertex_id, self)
        
        print(f"RENDER VERTEX: Setting position to ({x}, {y})")
        dot.setPos(x, y)  # Set position in scene coordinates
        dot.setZValue(depth * 100 + 10)  # Vertices above cuts
        print(f"RENDER VERTEX: Position after setPos: {dot.pos()}")
        
        # Set coordinator reference for area updates
        dot.coordinator = getattr(self, 'coordinator', None)
        
        # Apply styling
        from PySide6.QtGui import QPen, QBrush, QColor
        dot.setPen(QPen(QColor(style.get("border_color", "#000000")), float(style.get("border_width", 1))))
        dot.setBrush(QBrush(QColor(style.get("fill_color", "#ffffff"))))
        
        # Make interactive - ensure flags are set correctly
        dot.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        dot.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        dot.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        
        # DISABLE creation flag to prevent any automatic repositioning
        dot._creation_complete = False
        
        self.scene.addItem(dot)
        self.vertex_items[vertex_id] = dot
        
        print(f"RENDER VERTEX: Added to scene at position {dot.pos()}")
        
        # Mark creation as complete AFTER adding to scene
        dot._creation_complete = True
        
        # Add vertex label if present
        label = vertex_dto.get("label") if hasattr(vertex_dto, 'get') else getattr(vertex_dto, 'label', None)
        if label:
            from PySide6.QtWidgets import QGraphicsTextItem
            from PySide6.QtGui import QFont
            
            label_style = self.style_manager.resolve(type="vertex", role="label_text")
            font_size = int(label_style.get("font_size", 9))
            
            label_item = QGraphicsTextItem(label)
            label_item.setFont(QFont("Arial", font_size))
            label_item.setDefaultTextColor(QColor("#000000"))
            
            # Position label below the vertex dot
            label_rect = label_item.boundingRect()
            label_x = x - label_rect.width() / 2
            label_y = y + radius + 2  # Just below the dot
            label_item.setPos(label_x, label_y)
            label_item.setZValue(depth * 100 + 11)  # Above the vertex dot
            
            self.scene.addItem(label_item)
        
        # Track the vertex
        self.vertex_items[vertex_id] = dot
        self.element_positions[vertex_id] = QPointF(x, y)
        
        # Track vertex for annotations
        self.vertex_items[vertex_id] = dot
    
    def _draw_predicate(self, pred_data: Dict) -> QGraphicsTextItem:
        """Draw a predicate (text) at the specified coordinates."""
        x = pred_data.get("x", 0)
        y = pred_data.get("y", 0)
        text = pred_data.get("text", "")
        pred_id = pred_data.get("id", "")
        
        # Check if predicate already exists - don't move it if it does
        if pred_id in self.predicate_items:
            existing_predicate = self.predicate_items[pred_id]
            try:
                # Don't update position - user controls positioning
                return existing_predicate
            except RuntimeError:
                # Object was deleted, remove from tracking
                del self.predicate_items[pred_id]
        
        # Create interactive predicate that updates ligatures on move
        text_item = InteractivePredicate(text, pred_id, self)
        text_item.setPos(x, y)
        
        # Set coordinator reference for area updates
        text_item.coordinator = getattr(self, 'coordinator', None)
        # Calculate nesting depth for this predicate
        pred_pos = QPointF(x, y)
        depth = self.calculate_nesting_depth(pred_pos)
        text_item.setZValue(depth * 100 + 5)  # Predicate z-order based on nesting depth
        
        # Flags are set in InteractivePredicate constructor
        
        self.scene.addItem(text_item)
        self.element_positions[pred_id] = QPointF(x, y)
        
        # Track predicate for annotations
        self.predicate_items[pred_id] = text_item
        
        return text_item
    
    def _draw_ligature(self, ligature_data: Dict) -> None:
        """Draw a single ligature from path data."""
        path = ligature_data.get("path", [])
        if len(path) < 2:
            return
        
        # Get ligature styling
        style = self.style_manager.resolve(type="ligature", role="arm")
        line_color = style.get("line_color", "#000000")
        line_width = int(style.get("line_width", 3))
        
        # Draw line segments for the path
        for i in range(len(path) - 1):
            start_point = path[i]
            end_point = path[i + 1]
            
            line = QGraphicsLineItem(QLineF(
                start_point["x"], start_point["y"],
                end_point["x"], end_point["y"]
            ))
            pen = QPen(QColor(line_color), line_width)
            pen.setCapStyle(Qt.RoundCap)
            line.setPen(pen)
            
            # Ligatures get highest z-order to traverse all nesting levels
            max_depth = max([getattr(item, 'nesting_depth', 0) for item in self.scene.items() if isinstance(item, StyledCutItem)] + [0])
            line.setZValue(max_depth * 100 + 50)  # Ligatures above all elements
            
            self.scene.addItem(line)
    
    def _draw_ligatures(self, nu_map: Dict, predicate_rects: Dict[str, QRectF], vertices: Dict) -> None:
        """Draw ligatures with proper boundary anchoring."""
        for edge_id, connected_vertices in nu_map.items():
            if edge_id not in predicate_rects:
                continue
                
            pred_rect = predicate_rects[edge_id]
            
            for vertex_id in connected_vertices:
                if vertex_id not in vertices:
                    continue
                    
                vertex_data = vertices[vertex_id]
                vertex_pos = QPointF(vertex_data.get("x", 0), vertex_data.get("y", 0))
                
                # Use Ergasterion's boundary anchoring logic
                anchor_point = self._rect_border_anchor(pred_rect, vertex_pos)
                
                # Create ligature line using unified style system
                style = self.style_manager.resolve(type="ligature", role="arm")
                line_color = style.get("line_color", "#000000")
                line_width = int(style.get("line_width", 3))
                
                line = QGraphicsLineItem(QLineF(anchor_point, vertex_pos))
                pen = QPen(QColor(line_color), line_width)
                pen.setCapStyle(Qt.RoundCap)
                line.setPen(pen)
                # Ligatures get highest z-order to traverse all nesting levels
                max_depth = max([getattr(item, 'nesting_depth', 0) for item in self.scene.items() if isinstance(item, StyledCutItem)] + [0])
                line.setZValue(max_depth * 100 + 50)  # Ligatures above all elements
                
                # Enable interaction for editing
                line.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
                
                self.scene.addItem(line)
                
                # Track ligature for updates
                if edge_id not in self.ligature_map:
                    self.ligature_map[edge_id] = []
                self.ligature_map[edge_id].append(line)
    
    def _rect_border_anchor(self, scene_rect: QRectF, from_point: QPointF) -> QPointF:
        """
        Return the intersection point of the line from from_point to the rect center 
        with the rect border. This is Ergasterion's proven boundary anchoring logic.
        """
        center = scene_rect.center()
        ray = QLineF(from_point, center)
        
        # Construct scene-space edges
        tl = scene_rect.topLeft()
        tr = scene_rect.topRight()
        bl = scene_rect.bottomLeft()
        br = scene_rect.bottomRight()
        
        edges = [
            QLineF(tl, tr),  # top
            QLineF(tr, br),  # right
            QLineF(br, bl),  # bottom
            QLineF(bl, tl),  # left
        ]
        
        best_pt: Optional[QPointF] = None
        for edge in edges:
            res = ray.intersects(edge)
            try:
                itype, ipt = res
            except Exception:
                continue
            if itype == QLineF.IntersectionType.BoundedIntersection:
                best_pt = ipt
                break
        
        return best_pt if best_pt is not None else center
    
    def _update_element_area_containment(self, element_id: str, position):
        """Update element's area_id using iron-clad spatial-logical correspondence."""
        try:
            print(f"DEBUG: Movement detection for {element_id} at {position}")
            
            # DISABLED: Skip all automatic repositioning systems
            return
                        
        except Exception as e:
            print(f"Error updating element area containment: {e}")
            import traceback
            traceback.print_exc()
    
    def _detect_containing_area_for_position(self, position):
        """Detect which area/cut contains the given position using correct coordinate mapping."""
        print(f"DEBUG: Movement area detection for position {position}")
        
        # Check cuts in the coordinator's drawing schema for accurate positions
        if hasattr(self, 'coordinator') and self.coordinator:
            print(f"DEBUG: Found coordinator with {len(self.coordinator.egi_state.cuts)} cuts")
            
            for cut_id, cut_dto in self.coordinator.egi_state.cuts.items():
                cut_x = cut_dto.spatial.x
                cut_y = cut_dto.spatial.y
                cut_width = cut_dto.spatial.width
                cut_height = cut_dto.spatial.height
                
                print(f"DEBUG: Checking cut {cut_id} at pos ({cut_x}, {cut_y}), size {cut_width}x{cut_height}")
                
                # Check if position is within this cut's bounds
                if (cut_x <= position.x() <= cut_x + cut_width and 
                    cut_y <= position.y() <= cut_y + cut_height):
                    # COORDINATE FIX: Get actual Qt graphics item bounds instead of calculated bounds
                    actual_cut_item = None
                    for item in self.scene.items():
                        if hasattr(item, 'cut_id') and item.cut_id == cut_id:
                            actual_cut_item = item
                            break
                    
                    if actual_cut_item:
                        # Use actual Qt graphics item bounds
                        rect = actual_cut_item.rect()
                        pos = actual_cut_item.pos()
                        cut_left = pos.x() + rect.left()
                        cut_right = pos.x() + rect.right()
                        cut_top = pos.y() + rect.top()
                        cut_bottom = pos.y() + rect.bottom()
                        print(f"DEBUG: Using ACTUAL Qt item bounds for {cut_id}")
                    else:
                        # Fallback to calculated bounds
                        cut_left = cut_pos.x - cut_width/2
                        cut_right = cut_pos.x + cut_width/2
                        cut_top = cut_pos.y - cut_height/2
                        cut_bottom = cut_pos.y + cut_height/2
                        print(f"DEBUG: Using CALCULATED bounds for {cut_id} (no Qt item found)")
                    
                    print(f"DEBUG: Cut {cut_id} bounds: left={cut_left}, right={cut_right}, top={cut_top}, bottom={cut_bottom}")
                    print(f"DEBUG: Movement at x={position.x()}, y={position.y()}")
                    
                    # Check if scene position is inside cut bounds
                    if (cut_left <= position.x() <= cut_right and 
                        cut_top <= position.y() <= cut_bottom):
                        print(f"DEBUG: Position {position} IS INSIDE cut {cut_id}")
                        return cut_id
                    else:
                        print(f"DEBUG: Position {position} is outside cut {cut_id}")
                        print(f"DEBUG: COORDINATE MISMATCH - Visual vs Logical bounds don't align")
        else:
            print(f"DEBUG: No coordinator found for movement detection")
        
        print(f"DEBUG: Movement position not inside any cut, returning 'sheet'")
        return "sheet"
    
    def _regenerate_egi_from_drawing_schema(self):
        """Regenerate EGI structure from updated drawing schema to maintain spatial-logical correspondence."""
        try:
            if hasattr(self, 'coordinator') and self.coordinator:
                print(f"DEBUG: Regenerating EGI from drawing schema after area change")
                
                # Use the coordinator's existing method to convert drawing schema to EGI
                if hasattr(self.coordinator, 'generate_egi_from_diagram'):
                    new_egi = self.coordinator.generate_egi_from_diagram()
                    if new_egi:
                        self.coordinator.egi = new_egi
                        print(f"DEBUG: Successfully regenerated EGI with updated area assignments")
                    else:
                        print(f"DEBUG: Failed to generate EGI from diagram")
                else:
                    print(f"DEBUG: Coordinator missing generate_egi_from_diagram method")
            else:
                print(f"DEBUG: No coordinator available for EGI regeneration")
                
        except Exception as e:
            print(f"Error regenerating EGI from drawing schema: {e}")
            import traceback
            traceback.print_exc()

    def _refresh_egif(self):
        """Refresh the EGIF display after area changes."""
        # Find the drawing editor and trigger EGIF update
        for widget in self.scene.views():
            if hasattr(widget, 'parent') and hasattr(widget.parent(), '_update_current_egif_display'):
                widget.parent()._update_current_egif_display()
                break
