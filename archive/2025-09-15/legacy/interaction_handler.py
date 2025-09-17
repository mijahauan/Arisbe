#!/usr/bin/env python3
"""
InteractionHandler - User input handling layer for diagram editing.

This module handles all user interactions and delegates to the DiagramCoordinator
for maintaining logical-spatial correspondence. It provides a clean separation
between Qt event handling and business logic.
"""

from enum import Enum
from typing import Any, Callable, Dict, Optional

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QKeyEvent, QMouseEvent
from PySide6.QtWidgets import QGraphicsItem

from diagram_coordinator import DiagramCoordinator, InteractionMode, Point2D
from egi_spatial_correspondence import SpatialBounds


class DragState:
    """Tracks current drag operation state."""

    def __init__(self):
        self.is_dragging = False
        self.drag_element_id: Optional[str] = None
        self.drag_start_pos: Optional[QPointF] = None
        self.drag_current_pos: Optional[QPointF] = None


class InteractionHandler:
    """
    Handles user interactions and delegates to DiagramCoordinator.

    This layer translates Qt events into logical operations while maintaining
    clean separation from the coordination logic.
    """

    def __init__(self, coordinator: DiagramCoordinator):
        self.coordinator = coordinator
        self.drag_state = DragState()

        # Callbacks for UI updates
        self.on_mode_change: Optional[Callable[[str], None]] = None
        self.on_status_update: Optional[Callable[[str], None]] = None

        # Element ID tracking for graphics items
        self.graphics_to_element_id: Dict[QGraphicsItem, str] = {}

    # --- Mouse Event Handling ---

    def handle_mouse_press(
        self,
        event: QMouseEvent,
        scene_pos: QPointF,
        item: Optional[QGraphicsItem] = None,
    ) -> bool:
        """Handle mouse press events."""
        pos = Point2D.from_qpointf(scene_pos)

        if event.button() == Qt.LeftButton:
            return self._handle_left_click(pos, item)
        elif event.button() == Qt.RightButton:
            return self._handle_right_click(pos, item)

        return False

    def handle_mouse_move(self, event: QMouseEvent, scene_pos: QPointF) -> bool:
        """Handle mouse move events."""
        pos = Point2D.from_qpointf(scene_pos)

        if self.drag_state.is_dragging:
            return self._handle_drag_move(pos)

        return False

    def handle_mouse_release(self, event: QMouseEvent, scene_pos: QPointF) -> bool:
        """Handle mouse release events."""
        pos = Point2D.from_qpointf(scene_pos)

        if event.button() == Qt.LeftButton and self.drag_state.is_dragging:
            return self._handle_drag_end(pos)

        return False

    # --- Keyboard Event Handling ---

    def handle_key_press(self, event: QKeyEvent) -> bool:
        """Handle keyboard events."""
        key = event.key()
        modifiers = event.modifiers()

        # Mode switching
        if key == Qt.Key_V:
            self.set_interaction_mode(InteractionMode.CREATE_VERTEX)
            return True
        elif key == Qt.Key_P:
            self.set_interaction_mode(InteractionMode.CREATE_PREDICATE)
            return True
        elif key == Qt.Key_C:
            self.set_interaction_mode(InteractionMode.CREATE_CUT)
            return True
        elif key == Qt.Key_L:
            self.set_interaction_mode(InteractionMode.CREATE_LIGATURE)
            return True
        elif key == Qt.Key_Escape:
            self.set_interaction_mode(InteractionMode.SELECT)
            return True

        # Delete selected elements
        elif key == Qt.Key_Delete or key == Qt.Key_Backspace:
            return self._handle_delete_selected()

        return False

    # --- Mode Management ---

    def set_interaction_mode(self, mode: str) -> None:
        """Set interaction mode and notify coordinator."""
        self.coordinator.set_interaction_mode(mode)
        if self.on_mode_change:
            self.on_mode_change(mode)

        # Update status
        mode_names = {
            InteractionMode.SELECT: "Select",
            InteractionMode.CREATE_VERTEX: "Create Vertex",
            InteractionMode.CREATE_PREDICATE: "Create Predicate",
            InteractionMode.CREATE_CUT: "Create Cut",
            InteractionMode.CREATE_LIGATURE: "Create Ligature",
        }
        status = f"Mode: {mode_names.get(mode, mode)}"
        if self.on_status_update:
            self.on_status_update(status)

    def set_validation_mode(self, mode: str) -> None:
        """Set validation mode (composition/practice)."""
        self.coordinator.set_validation_mode(mode)
        if self.on_status_update:
            self.on_status_update(f"Validation: {mode.title()}")

    # --- Element Management ---

    def register_graphics_item(self, item: QGraphicsItem, element_id: str) -> None:
        """Register graphics item with its element ID."""
        self.graphics_to_element_id[item] = element_id

    def unregister_graphics_item(self, item: QGraphicsItem) -> None:
        """Unregister graphics item."""
        self.graphics_to_element_id.pop(item, None)

    def get_element_id(self, item: QGraphicsItem) -> Optional[str]:
        """Get element ID for graphics item."""
        return self.graphics_to_element_id.get(item)

    # --- Internal Event Handlers ---

    def _handle_left_click(self, pos: Point2D, item: Optional[QGraphicsItem]) -> bool:
        """Handle left mouse button press."""
        mode = self.coordinator.interaction_mode

        if mode == InteractionMode.SELECT:
            if item:
                # Always use our constraint-aware drag logic instead of Qt's
                element_id = self.get_element_id(item)
                if element_id:
                    self._start_drag(element_id, pos)
                    return True
            return False

        elif mode == InteractionMode.CREATE_VERTEX:
            # Create vertex at clicked position
            vertex_id = self.coordinator.create_vertex(pos)
            if vertex_id and self.on_status_update:
                self.on_status_update(f"Created vertex: {vertex_id}")
            return vertex_id is not None

        elif mode == InteractionMode.CREATE_PREDICATE:
            # Create predicate at clicked position
            # For now, use default name - could show dialog
            predicate_id = self.coordinator.create_predicate("Pred", pos)
            if predicate_id and self.on_status_update:
                self.on_status_update(f"Created predicate: {predicate_id}")
            return predicate_id is not None

        elif mode == InteractionMode.CREATE_CUT:
            # Start cut creation - would need drag to define bounds
            # For now, create default sized cut
            bounds = SpatialBounds(pos.x - 50, pos.y - 50, 100, 100)
            cut_id = self.coordinator.create_cut(bounds)
            if cut_id and self.on_status_update:
                self.on_status_update(f"Created cut: {cut_id}")
            return cut_id is not None

        elif mode == InteractionMode.CREATE_LIGATURE:
            # Handle ligature creation - needs two clicks
            if item:
                element_id = self.get_element_id(item)
                if element_id:
                    return self._handle_ligature_creation(element_id)
            return False

        return False

    def _handle_right_click(self, pos: Point2D, item: Optional[QGraphicsItem]) -> bool:
        """Handle right mouse button press (context menu)."""
        if item:
            element_id = self.get_element_id(item)
            if element_id:
                # Could show context menu here
                if self.on_status_update:
                    self.on_status_update(f"Context menu for: {element_id}")
                return True
        return False

    def _start_drag(self, element_id: str, pos: Point2D) -> None:
        """Start dragging an element."""
        self.drag_state.is_dragging = True
        self.drag_state.drag_element_id = element_id
        self.drag_state.drag_start_pos = pos.to_qpointf()
        self.drag_state.drag_current_pos = pos.to_qpointf()

        if self.on_status_update:
            self.on_status_update(f"Dragging: {element_id}")

    def _handle_drag_move(self, pos: Point2D) -> bool:
        """Handle drag movement."""
        if not self.drag_state.is_dragging or not self.drag_state.drag_element_id:
            return False

        self.drag_state.drag_current_pos = pos.to_qpointf()

        # Update element position through coordinator
        success = self.coordinator.move_element(self.drag_state.drag_element_id, pos)

        return success

    def _handle_drag_end(self, pos: Point2D) -> bool:
        """Handle end of drag operation."""
        if not self.drag_state.is_dragging:
            return False

        element_id = self.drag_state.drag_element_id

        # Final position update
        success = False
        if element_id:
            success = self.coordinator.move_element(element_id, pos)

            if self.on_status_update:
                status = (
                    f"Moved {element_id}" if success else f"Failed to move {element_id}"
                )
                self.on_status_update(status)

        # Reset drag state
        self.drag_state.is_dragging = False
        self.drag_state.drag_element_id = None
        self.drag_state.drag_start_pos = None
        self.drag_state.drag_current_pos = None

        return success

    def _handle_ligature_creation(self, element_id: str) -> bool:
        """Handle ligature creation between elements."""
        # This would need state tracking for two-click ligature creation
        # For now, simplified implementation
        if self.on_status_update:
            self.on_status_update(f"Ligature creation with: {element_id}")
        return True

    def _handle_delete_selected(self) -> bool:
        """Handle deletion of selected elements."""
        # Would need selection tracking
        if self.on_status_update:
            self.on_status_update("Delete selected elements")
        return True

    # --- Utility Methods ---

    def get_current_mode(self) -> str:
        """Get current interaction mode."""
        return self.coordinator.interaction_mode

    def get_validation_mode(self) -> str:
        """Get current validation mode."""
        return self.coordinator.validation_mode

    def is_dragging(self) -> bool:
        """Check if currently dragging."""
        return self.drag_state.is_dragging
