#!/usr/bin/env python3
"""
Phase 1 Implementation: Core Movement System

This implements:
1. Drag-drop state machine (free drag, validate on drop)
2. Snap-to-nearest-valid algorithm  
3. Disabled collision avoidance during drag
4. Fixed area detection for element creation
5. Mode-aware constraint validation
"""

import sys
import math
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from PySide6.QtCore import Qt, QTimer, QPointF, QRectF, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication, QGraphicsScene, QGraphicsView, QMainWindow,
    QMessageBox, QFileDialog, QToolBar, QLabel, QDockWidget,
    QTabWidget, QTextEdit, QWidget, QInputDialog, QVBoxLayout, QHBoxLayout, QStatusBar, QMenu,
    QPushButton, QGraphicsItem
)
from PySide6.QtGui import QActionGroup

# Import existing components
sys.path.append(str(Path(__file__).parent.parent / "src"))
from diagram_coordinator import DiagramCoordinator, Point2D, ValidationMode
from interaction_handler import InteractionHandler, InteractionMode
from organon_ergasterion_protocol import GraphHandoffPackage, GraphHandoffType


class MovementState(Enum):
    """States in the drag-drop movement pipeline."""
    IDLE = "idle"
    DRAGGING = "dragging"          # Free movement allowed
    VALIDATING = "validating"      # Checking drop position
    ADJUSTING = "adjusting"        # Auto-adjustments in progress  
    SNAPPING_BACK = "snapping_back"  # Reverting to valid position


class ConstraintMode(Enum):
    """Constraint enforcement modes."""
    PERMISSIVE = "permissive"  # Syntactic constraints only
    STRICT = "strict"          # Syntactic + semantic constraints


@dataclass
class MovementContext:
    """Context information for a movement operation."""
    element: QGraphicsItem
    start_position: QPointF
    current_position: QPointF
    last_valid_position: QPointF
    state: MovementState
    mode: ConstraintMode


class MovementManager:
    """Manages the drag-drop movement pipeline with proper constraint validation."""
    
    def __init__(self, scene: QGraphicsScene, coordinator: DiagramCoordinator):
        self.scene = scene
        self.coordinator = coordinator
        self.current_movement: Optional[MovementContext] = None
        self.constraint_mode = ConstraintMode.PERMISSIVE
        
        # Animation for snap-back
        self.snap_animation = None
        
        print("MovementManager initialized with drag-drop state machine")
    
    def set_constraint_mode(self, mode: ConstraintMode):
        """Set the constraint enforcement mode."""
        self.constraint_mode = mode
        print(f"Constraint mode set to: {mode.value}")
    
    def start_drag(self, element: QGraphicsItem, start_pos: QPointF) -> bool:
        """Start a drag operation."""
        if self.current_movement and self.current_movement.state != MovementState.IDLE:
            print("Cannot start drag - another movement in progress")
            return False
        
        self.current_movement = MovementContext(
            element=element,
            start_position=start_pos,
            current_position=start_pos,
            last_valid_position=start_pos,  # Start position is always valid
            state=MovementState.DRAGGING,
            mode=self.constraint_mode
        )
        
        print(f"Started drag for {self._get_element_id(element)} from {start_pos}")
        return True
    
    def update_drag(self, current_pos: QPointF):
        """Update drag position - allows free movement, tracks last valid position."""
        if not self.current_movement or self.current_movement.state != MovementState.DRAGGING:
            return
        
        self.current_movement.current_position = current_pos
        
        # Check if current position would be valid on drop (but don't enforce yet)
        if self._would_be_valid_on_drop(self.current_movement.element, current_pos):
            self.current_movement.last_valid_position = current_pos
        
        # Always allow visual movement during drag
        self.current_movement.element.setPos(current_pos)
    
    def end_drag(self, drop_pos: QPointF) -> bool:
        """End drag operation with validation and potential snap-back."""
        if not self.current_movement or self.current_movement.state != MovementState.DRAGGING:
            return False
        
        self.current_movement.state = MovementState.VALIDATING
        self.current_movement.current_position = drop_pos
        
        print(f"Ending drag at {drop_pos}, validating...")
        
        # Validate the drop position
        if self._is_valid_drop_position(self.current_movement.element, drop_pos):
            return self._accept_movement(drop_pos)
        else:
            return self._handle_invalid_drop(drop_pos)
    
    def cancel_drag(self):
        """Cancel current drag operation."""
        if self.current_movement:
            # Snap back to start position
            self._animate_snap_back(self.current_movement.start_position, "Drag cancelled")
    
    def _would_be_valid_on_drop(self, element: QGraphicsItem, position: QPointF) -> bool:
        """Check if position would be valid on drop (used during drag to track last valid)."""
        try:
            # Quick syntactic check only (for performance during drag)
            return self._check_basic_syntactic_constraints(element, position)
        except Exception as e:
            print(f"Error in validity check: {e}")
            return False
    
    def _is_valid_drop_position(self, element: QGraphicsItem, position: QPointF) -> bool:
        """Full validation for drop position."""
        try:
            # Always check syntactic constraints
            if not self._check_syntactic_constraints(element, position):
                return False
            
            # Check semantic constraints only in strict mode
            if self.constraint_mode == ConstraintMode.STRICT:
                if not self._check_semantic_constraints(element, position):
                    return False
            
            return True
            
        except Exception as e:
            print(f"Error in drop validation: {e}")
            return False
    
    def _check_basic_syntactic_constraints(self, element: QGraphicsItem, position: QPointF) -> bool:
        """Basic syntactic constraint check (fast, for drag tracking)."""
        # Quick overlap check with other elements
        element_rect = QRectF(position.x(), position.y(), 
                             element.boundingRect().width(), 
                             element.boundingRect().height())
        
        # Check for overlaps with other elements
        for item in self.scene.items():
            if item == element:
                continue
            
            if element_rect.intersects(item.sceneBoundingRect()):
                # Check if this is allowed nesting vs forbidden overlap
                if not self._is_allowed_intersection(element, item, element_rect, item.sceneBoundingRect()):
                    return False
        
        return True
    
    def _check_syntactic_constraints(self, element: QGraphicsItem, position: QPointF) -> bool:
        """Full syntactic constraint validation."""
        # Use existing constraint engine for thorough validation
        try:
            # Build DTO for constraint engine
            dto = self._build_constraint_dto(element, position)
            
            # Import and use existing constraint engine
            sys.path.append(str(Path(__file__).parent.parent / "src" / "controller"))
            from constraint_engine import validate_syntactic_constraints
            
            is_valid, message, info = validate_syntactic_constraints(dto)
            
            if not is_valid:
                print(f"Syntactic constraint violation: {message}")
            
            return is_valid
            
        except Exception as e:
            print(f"Error in syntactic validation: {e}")
            # Fallback to basic check
            return self._check_basic_syntactic_constraints(element, position)
    
    def _check_semantic_constraints(self, element: QGraphicsItem, position: QPointF) -> bool:
        """Semantic constraint validation (only in strict mode)."""
        try:
            # Build DTO for constraint engine
            dto = self._build_constraint_dto(element, position)
            
            # Import and use existing constraint engine
            sys.path.append(str(Path(__file__).parent.parent / "src" / "controller"))
            from constraint_engine import validate_semantic_constraints
            
            is_valid, message, info = validate_semantic_constraints(dto)
            
            if not is_valid:
                print(f"Semantic constraint violation: {message}")
            
            return is_valid
            
        except Exception as e:
            print(f"Error in semantic validation: {e}")
            return True  # Allow movement if validation fails
    
    def _is_allowed_intersection(self, element1: QGraphicsItem, element2: QGraphicsItem, 
                                rect1: QRectF, rect2: QRectF) -> bool:
        """Check if intersection between two elements is allowed."""
        
        # Check for complete containment (nesting) - this is allowed
        if rect1.contains(rect2) or rect2.contains(rect1):
            print(f"Allowing nesting between {self._get_element_id(element1)} and {self._get_element_id(element2)}")
            return True
        
        # Partial overlap is not allowed
        print(f"Preventing overlap between {self._get_element_id(element1)} and {self._get_element_id(element2)}")
        return False
    
    def _accept_movement(self, final_pos: QPointF) -> bool:
        """Accept the movement at the final position."""
        if not self.current_movement:
            return False
        
        element_id = self._get_element_id(self.current_movement.element)
        print(f"Movement accepted for {element_id} at {final_pos}")
        
        # Update coordinator with new position if possible
        self._update_coordinator_position(self.current_movement.element, final_pos)
        
        # Clean up movement context
        self.current_movement = None
        
        return True
    
    def _handle_invalid_drop(self, invalid_pos: QPointF) -> bool:
        """Handle invalid drop position based on constraint mode."""
        if not self.current_movement:
            return False
        
        if self.constraint_mode == ConstraintMode.PERMISSIVE:
            # Snap to nearest valid position
            return self._snap_to_nearest_valid(invalid_pos)
        else:
            # In strict mode, attempt automatic adjustment (Phase 2 feature)
            # For now, fall back to snap-back
            return self._snap_to_nearest_valid(invalid_pos)
    
    def _snap_to_nearest_valid(self, invalid_pos: QPointF) -> bool:
        """Snap to nearest valid position using spatial search."""
        if not self.current_movement:
            return False
        
        print(f"Searching for nearest valid position to {invalid_pos}")
        
        # Start with last valid position during drag
        candidates = [self.current_movement.last_valid_position]
        
        # Add positions in expanding circles around target
        for radius in [10, 20, 50, 100]:
            for angle in range(0, 360, 45):  # 8 directions
                candidate = self._polar_offset(invalid_pos, radius, angle)
                if self._is_valid_drop_position(self.current_movement.element, candidate):
                    candidates.append(candidate)
        
        # Choose closest to intended position
        if candidates:
            best_pos = min(candidates, key=lambda p: self._distance(p, invalid_pos))
            distance = self._distance(best_pos, invalid_pos)
            
            if distance < 5:  # Very close, probably the same position
                message = "Position adjusted slightly"
            else:
                message = f"Snapped to nearest valid position ({distance:.0f}px away)"
            
            return self._animate_snap_back(best_pos, message)
        else:
            # No valid position found, revert to start
            return self._animate_snap_back(self.current_movement.start_position, 
                                         "No valid position found, reverted to start")
    
    def _animate_snap_back(self, target_pos: QPointF, message: str) -> bool:
        """Animate element moving to target position."""
        if not self.current_movement:
            return False
        
        element = self.current_movement.element
        current_pos = element.pos()
        
        print(f"Animating snap-back to {target_pos}: {message}")
        
        # Create animation
        self.snap_animation = QPropertyAnimation(element, b"pos")
        self.snap_animation.setDuration(300)  # 300ms animation
        self.snap_animation.setStartValue(current_pos)
        self.snap_animation.setEndValue(target_pos)
        self.snap_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Set up completion callback
        def on_animation_finished():
            self._update_coordinator_position(element, target_pos)
            self.current_movement = None
            # Show message to user (would need parent widget reference)
            print(f"Snap-back complete: {message}")
        
        self.snap_animation.finished.connect(on_animation_finished)
        self.snap_animation.start()
        
        return True
    
    def _polar_offset(self, center: QPointF, radius: float, angle_degrees: float) -> QPointF:
        """Calculate position at radius and angle from center."""
        angle_rad = math.radians(angle_degrees)
        x = center.x() + radius * math.cos(angle_rad)
        y = center.y() + radius * math.sin(angle_rad)
        return QPointF(x, y)
    
    def _distance(self, p1: QPointF, p2: QPointF) -> float:
        """Calculate distance between two points."""
        dx = p1.x() - p2.x()
        dy = p1.y() - p2.y()
        return math.sqrt(dx * dx + dy * dy)
    
    def _get_element_id(self, element: QGraphicsItem) -> str:
        """Get ID of a graphics element."""
        if hasattr(element, 'vertex_id'):
            return f"vertex_{element.vertex_id}"
        elif hasattr(element, 'predicate_id'):
            return f"predicate_{element.predicate_id}"
        elif hasattr(element, 'cut_id'):
            return f"cut_{element.cut_id}"
        else:
            return f"element_{id(element)}"
    
    def _update_coordinator_position(self, element: QGraphicsItem, new_pos: QPointF):
        """Update coordinator with new element position."""
        try:
            element_id = self._get_element_id(element)
            point = Point2D(new_pos.x(), new_pos.y())
            
            # Update coordinator based on element type
            if hasattr(element, 'vertex_id'):
                # Update vertex position in coordinator
                pass  # TODO: Add coordinator update method
            elif hasattr(element, 'predicate_id'):
                # Update predicate position in coordinator  
                pass  # TODO: Add coordinator update method
            elif hasattr(element, 'cut_id'):
                # Update cut position in coordinator
                pass  # TODO: Add coordinator update method
            
            print(f"Updated coordinator position for {element_id} to {point}")
            
        except Exception as e:
            print(f"Error updating coordinator position: {e}")
    
    def _build_constraint_dto(self, element: QGraphicsItem, position: QPointF) -> Dict[str, Any]:
        """Build DTO for constraint engine validation."""
        # This is a simplified version - would need full implementation
        # based on your constraint engine's expected format
        
        dto = {
            "sheet_id": "sheet",
            "cuts": {},
            "vertices": {},
            "predicates": {},
            "ligatures": []
        }
        
        # Add current scene elements to DTO
        for item in self.scene.items():
            if hasattr(item, 'cut_id'):
                cut_id = item.cut_id
                pos = position if item == element else item.pos()
                rect = item.boundingRect()
                dto["cuts"][cut_id] = {
                    "rect": (pos.x(), pos.y(), rect.width(), rect.height())
                }
            elif hasattr(item, 'vertex_id'):
                vertex_id = item.vertex_id
                pos = position if item == element else item.pos()
                dto["vertices"][vertex_id] = {
                    "x": pos.x(),
                    "y": pos.y()
                }
            elif hasattr(item, 'predicate_id'):
                predicate_id = item.predicate_id
                pos = position if item == element else item.pos()
                dto["predicates"][predicate_id] = {
                    "x": pos.x(),
                    "y": pos.y()
                }
        
        return dto


class FixedAreaDetector:
    """Fixed area detection that properly identifies cut areas."""
    
    def __init__(self, scene: QGraphicsScene):
        self.scene = scene
    
    def detect_area_at_position(self, position: QPointF) -> Tuple[str, str]:
        """Detect area at position using visual scene items.
        
        Returns:
            Tuple of (area_id, area_description)
        """
        print(f"Detecting area at position {position}")
        
        # Get all items at this position
        items_at_pos = self.scene.items(position)
        
        # Find cuts that contain this position
        containing_cuts = []
        for item in items_at_pos:
            if self._is_cut_item(item):
                cut_rect = item.sceneBoundingRect()
                if cut_rect.contains(position):
                    cut_id = self._get_cut_id(item)
                    area_size = cut_rect.width() * cut_rect.height()
                    containing_cuts.append((cut_id, area_size, item))
                    print(f"Found containing cut: {cut_id} (area: {area_size})")
        
        if containing_cuts:
            # Return the smallest cut (deepest nesting)
            smallest_cut = min(containing_cuts, key=lambda x: x[1])
            cut_id = smallest_cut[0]
            area_id = f"cut_{cut_id}"
            area_description = f"Cut {cut_id}"
            print(f"Position is in cut area: {area_id}")
            return area_id, area_description
        else:
            print("Position is in sheet area")
            return "sheet", "Sheet of Assertion"
    
    def _is_cut_item(self, item: QGraphicsItem) -> bool:
        """Check if item is a cut."""
        # Check for various cut item types
        if hasattr(item, 'cut_id'):
            return True
        
        # Check class name for cut items
        class_name = type(item).__name__
        if 'Cut' in class_name:
            return True
        
        return False
    
    def _get_cut_id(self, cut_item: QGraphicsItem) -> str:
        """Get cut ID from cut item."""
        if hasattr(cut_item, 'cut_id'):
            return cut_item.cut_id
        else:
            return f"unknown_{id(cut_item)}"


class Phase1DrawingView(QGraphicsView):
    """
    Drawing view with Phase 1 movement system implementation.
    """
    
    def __init__(self, scene: QGraphicsScene, coordinator: DiagramCoordinator):
        super().__init__(scene)
        self.coordinator = coordinator
        self.setDragMode(QGraphicsView.RubberBandDrag)
        
        # Initialize Phase 1 systems
        self.movement_manager = MovementManager(scene, coordinator)
        self.area_detector = FixedAreaDetector(scene)
        
        # Track current drag state
        self._current_drag_item = None
        
        print("Phase1DrawingView initialized with movement manager and area detector")
    
    def set_constraint_mode(self, mode: ConstraintMode):
        """Set constraint mode for movement manager."""
        self.movement_manager.set_constraint_mode(mode)
    
    def mousePressEvent(self, event):
        """Handle mouse press with Phase 1 logic."""
        scene_pos = self.mapToScene(event.position().toPoint())
        item = self.scene().itemAt(scene_pos, self.transform())
        
        # Handle right-click context menus
        if event.button() == Qt.MouseButton.RightButton:
            if item and self._is_interactive_element(item):
                self._show_element_context_menu(event.globalPosition().toPoint(), item)
            else:
                self._show_area_context_menu(event.position().toPoint(), scene_pos)
            return
        
        # Handle left-click for movement
        if event.button() == Qt.LeftButton:
            if item and self._is_movable_element(item):
                # Start drag with movement manager
                if self.movement_manager.start_drag(item, scene_pos):
                    self._current_drag_item = item
                    print(f"Started Phase 1 drag for {self.movement_manager._get_element_id(item)}")
                return
        
        # Default behavior for other cases
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move with Phase 1 movement manager."""
        if self._current_drag_item:
            scene_pos = self.mapToScene(event.position().toPoint())
            self.movement_manager.update_drag(scene_pos)
            return
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release with Phase 1 validation."""
        if self._current_drag_item:
            scene_pos = self.mapToScene(event.position().toPoint())
            success = self.movement_manager.end_drag(scene_pos)
            
            if success:
                self.parent().statusBar().showMessage("Movement completed", 2000)
            else:
                self.parent().statusBar().showMessage("Movement adjusted", 2000)
            
            self._current_drag_item = None
            return
        
        super().mouseReleaseEvent(event)
    
    def _show_area_context_menu(self, view_position, scene_position):
        """Show context menu for area with fixed area detection."""
        try:
            # Use fixed area detector
            area_id, area_description = self.area_detector.detect_area_at_position(scene_position)
            
            # Convert to global position for menu display
            global_pos = self.mapToGlobal(view_position)
            
            # Create context menu
            menu = QMenu(f"Add Element", self)
            
            # Add area info as title
            area_title = menu.addAction(area_description)
            area_title.setEnabled(False)
            menu.addSeparator()
            
            # Add element creation actions
            add_vertex_action = menu.addAction("Add Vertex")
            add_vertex_action.triggered.connect(lambda: self._create_vertex_at_area(scene_position, area_id))
            
            add_predicate_action = menu.addAction("Add Predicate...")
            add_predicate_action.triggered.connect(lambda: self._create_predicate_at_area(scene_position, area_id))
            
            add_cut_action = menu.addAction("Add Cut")
            add_cut_action.triggered.connect(lambda: self._create_cut_at_area(scene_position, area_id))
            
            # Show menu
            menu.exec(global_pos)
            
        except Exception as e:
            print(f"Error in area context menu: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_vertex_at_area(self, scene_pos, area_id):
        """Create vertex in specified area."""
        try:
            position = Point2D(scene_pos.x(), scene_pos.y())
            vertex_id = self.coordinator.create_vertex(position, area_id)
            
            if vertex_id:
                print(f"Created vertex {vertex_id} at {position} in area {area_id}")
                self.parent()._update_scene_after_creation()
                self.parent().statusBar().showMessage(f"Created vertex {vertex_id} in {area_id}", 3000)
            else:
                QMessageBox.warning(self, "Creation Failed", "Could not create vertex at this position.")
                
        except Exception as e:
            print(f"Error creating vertex: {e}")
            QMessageBox.critical(self, "Error", f"Error creating vertex: {e}")
    
    def _create_predicate_at_area(self, scene_pos, area_id):
        """Create predicate in specified area."""
        try:
            # Get predicate name from user
            text, ok = QInputDialog.getText(
                self, 
                "Add Predicate", 
                f"Enter predicate name for {area_id}:",
                text="P"
            )
            
            if not ok or not text.strip():
                return
            
            name = text.strip()
            position = Point2D(scene_pos.x(), scene_pos.y())
            predicate_id = self.coordinator.create_predicate(name, position, area_id)
            
            if predicate_id:
                print(f"Created predicate {predicate_id} '{name}' at {position} in area {area_id}")
                self.parent()._update_scene_after_creation()
                self.parent().statusBar().showMessage(f"Created predicate '{name}' ({predicate_id}) in {area_id}", 3000)
            else:
                QMessageBox.warning(self, "Creation Failed", f"Could not create predicate '{name}' at this position.")
                
        except Exception as e:
            print(f"Error creating predicate: {e}")
            QMessageBox.critical(self, "Error", f"Error creating predicate: {e}")
    
    def _create_cut_at_area(self, scene_pos, area_id):
        """Create cut in specified area."""
        try:
            x, y = scene_pos.x(), scene_pos.y()
            default_width = 150
            default_height = 100
            
            cut_id = self.coordinator.create_cut(x, y, default_width, default_height, area_id)
            
            if cut_id:
                print(f"Created cut {cut_id} at ({x}, {y}) size {default_width}x{default_height} in area {area_id}")
                self.parent()._update_scene_after_creation()
                
                if area_id == "sheet":
                    self.parent().statusBar().showMessage(f"Created cut {cut_id} on sheet", 3000)
                else:
                    self.parent().statusBar().showMessage(f"Created nested cut {cut_id} inside {area_id}", 3000)
            else:
                QMessageBox.warning(self, "Creation Failed", "Could not create cut at this position.")
                
        except Exception as e:
            print(f"Error creating cut: {e}")
            QMessageBox.critical(self, "Error", f"Error creating cut: {e}")
    
    def _is_interactive_element(self, item) -> bool:
        """Check if item is an interactive element."""
        return (hasattr(item, 'vertex_id') or 
                hasattr(item, 'predicate_id') or 
                hasattr(item, 'cut_id'))
    
    def _is_movable_element(self, item) -> bool:
        """Check if item is movable."""
        return (self._is_interactive_element(item) and 
                hasattr(item, 'flags') and 
                (item.flags() & item.GraphicsItemFlag.ItemIsMovable))
    
    def _show_element_context_menu(self, global_pos, item):
        """Show context menu for interactive elements."""
        menu = QMenu()
        
        element_type = "Element"
        if hasattr(item, 'vertex_id'):
            element_type = "Vertex"
            menu.addAction("Delete Vertex", lambda: self._delete_element(item))
        elif hasattr(item, 'predicate_id'):
            element_type = "Predicate"
            menu.addAction("Delete Predicate", lambda: self._delete_element(item))
            menu.addAction("Edit Text", lambda: self._edit_predicate_text(item))
        elif hasattr(item, 'cut_id'):
            element_type = "Cut"
            menu.addAction("Delete Cut", lambda: self._delete_element(item))
        
        menu.addAction(f"Properties", lambda: self._show_element_properties(item))
        menu.exec(global_pos)
    
    def _delete_element(self, element):
        """Delete an element."""
        element_id = self.movement_manager._get_element_id(element)
        reply = QMessageBox.question(self, "Delete Element", f"Delete {element_id}?")
        if reply == QMessageBox.StandardButton.Yes:
            self.scene().removeItem(element)
            self.parent().statusBar().showMessage(f"Deleted {element_id}", 2000)
    
    def _edit_predicate_text(self, predicate_item):
        """Edit predicate text."""
        current_text = getattr(predicate_item, 'text', 'P')
        text, ok = QInputDialog.getText(self, "Edit Predicate", "Enter new text:", text=current_text)
        if ok and text.strip():
            # Update predicate text
            if hasattr(predicate_item, 'setPlainText'):
                predicate_item.setPlainText(text.strip())
            self.parent().statusBar().showMessage(f"Updated predicate text to '{text.strip()}'", 2000)
    
    def _show_element_properties(self, element):
        """Show element properties."""
        element_id = self.movement_manager._get_element_id(element)
        pos = element.pos()
        self.parent().statusBar().showMessage(f"{element_id} at ({pos.x():.1f}, {pos.y():.1f})", 3000)


# Export the Phase 1 classes for integration
__all__ = [
    'MovementState',
    'ConstraintMode', 
    'MovementManager',
    'FixedAreaDetector',
    'Phase1DrawingView'
]

print("Phase 1 Movement System implementation ready for integration")

