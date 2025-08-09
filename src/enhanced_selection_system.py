#!/usr/bin/env python3
"""
Enhanced Selection System with Professional Visual Feedback

Provides professional-grade selection feedback, context menus, and interaction
patterns for the Existential Graphs editor.
"""

import sys
import os
from typing import Dict, List, Optional, Tuple, Set, Any, Callable
from dataclasses import dataclass
from enum import Enum

# Add src to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from egi_core_dau import RelationalGraphWithCuts, ElementID
from layout_engine_clean import SpatialPrimitive
from mode_aware_selection import Mode, SelectionState, ActionType, ModeAwareSelectionSystem
from dau_rendering_theme import get_current_theme

try:
    from PySide6.QtWidgets import (
        QWidget, QMenu, QAction, QActionGroup, QApplication
    )
    from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QCursor, QPainterPath
    from PySide6.QtCore import Qt, QPointF, QRectF, QTimer
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False
    # Create dummy classes for type hints when PySide6 not available
    class QPainter: pass
    class QPen: pass
    class QBrush: pass
    class QColor: pass
    class QWidget: pass
    class QMenu: pass
    class QAction: pass


class SelectionMode(Enum):
    """Selection interaction modes."""
    SINGLE = "single"           # Single element selection
    MULTI = "multi"            # Multiple element selection
    AREA = "area"              # Area/rectangle selection
    SUBGRAPH = "subgraph"      # Logical subgraph selection


@dataclass
class SelectionFeedback:
    """Visual feedback configuration for selections."""
    show_handles: bool = True           # Show resize/move handles
    show_bounds: bool = True            # Show selection bounds
    show_connections: bool = True       # Show logical connections
    show_context_hints: bool = True     # Show context information
    animate_selection: bool = True      # Animate selection changes


@dataclass
class InteractionState:
    """Current interaction state."""
    is_dragging: bool = False
    drag_start_pos: Optional[Tuple[float, float]] = None
    drag_current_pos: Optional[Tuple[float, float]] = None
    hover_element: Optional[ElementID] = None
    hover_position: Optional[Tuple[float, float]] = None
    context_menu_visible: bool = False


class SelectionRenderer:
    """Renders selection overlays and visual feedback."""
    
    def __init__(self):
        self.theme = get_current_theme()
        self.feedback_config = SelectionFeedback()
    
    def render_selection_overlays(self, painter: QPainter, selection_state: SelectionState,
                                 spatial_primitives: List[SpatialPrimitive],
                                 interaction_state: InteractionState):
        """Render all selection overlays and feedback."""
        if not PYSIDE6_AVAILABLE:
            return
            
        # Render hover feedback
        if interaction_state.hover_element:
            self._render_hover_feedback(painter, interaction_state.hover_element, 
                                      spatial_primitives)
        
        # Render selection highlights
        for element_id in selection_state.selected_elements:
            primitive = self._find_primitive_by_id(element_id, spatial_primitives)
            if primitive:
                self._render_selection_highlight(painter, primitive)
                
                if self.feedback_config.show_handles:
                    self._render_selection_handles(painter, primitive)
        
        # Render selection bounds
        if (self.feedback_config.show_bounds and 
            len(selection_state.selected_elements) > 1):
            self._render_selection_bounds(painter, selection_state.selected_elements,
                                        spatial_primitives)
        
        # Render drag feedback
        if interaction_state.is_dragging:
            self._render_drag_feedback(painter, interaction_state)
    
    def _render_hover_feedback(self, painter: QPainter, element_id: ElementID,
                              spatial_primitives: List[SpatialPrimitive]):
        """Render hover feedback for an element."""
        primitive = self._find_primitive_by_id(element_id, spatial_primitives)
        if not primitive:
            return
            
        # Use hover pen from theme
        pen = self.theme.hover_pen
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        
        # Draw hover outline
        self._draw_element_outline(painter, primitive, margin=3)
    
    def _render_selection_highlight(self, painter: QPainter, primitive: SpatialPrimitive):
        """Render selection highlight for a primitive."""
        pen = self.theme.selection_pen
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        
        # Draw selection outline
        self._draw_element_outline(painter, primitive, margin=5)
    
    def _render_selection_handles(self, painter: QPainter, primitive: SpatialPrimitive):
        """Render selection handles for resizing/moving."""
        if primitive.element_type == "cut":
            self._render_cut_handles(painter, primitive)
        elif primitive.element_type in ["vertex", "predicate"]:
            self._render_element_handles(painter, primitive)
    
    def _render_cut_handles(self, painter: QPainter, primitive: SpatialPrimitive):
        """Render resize handles for cuts."""
        if not hasattr(primitive, 'bounds'):
            return
            
        x1, y1, x2, y2 = primitive.bounds
        handle_size = 8
        
        # Handle positions (corners and midpoints)
        handles = [
            (x1, y1),           # Top-left
            ((x1+x2)/2, y1),    # Top-center
            (x2, y1),           # Top-right
            (x2, (y1+y2)/2),    # Right-center
            (x2, y2),           # Bottom-right
            ((x1+x2)/2, y2),    # Bottom-center
            (x1, y2),           # Bottom-left
            (x1, (y1+y2)/2),    # Left-center
        ]
        
        # Draw handles
        painter.setPen(QPen(QColor(self.theme.conventions.SELECTION_COLOR), 1))
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        
        for hx, hy in handles:
            painter.drawRect(QRectF(
                hx - handle_size/2, hy - handle_size/2,
                handle_size, handle_size
            ))
    
    def _render_element_handles(self, painter: QPainter, primitive: SpatialPrimitive):
        """Render move handle for vertices and predicates."""
        if not hasattr(primitive, 'position'):
            return
            
        x, y = primitive.position
        handle_size = 6
        
        # Draw single move handle
        painter.setPen(QPen(QColor(self.theme.conventions.SELECTION_COLOR), 2))
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        
        painter.drawEllipse(QPointF(x, y), handle_size, handle_size)
    
    def _render_selection_bounds(self, painter: QPainter, selected_elements: Set[ElementID],
                                spatial_primitives: List[SpatialPrimitive]):
        """Render bounding box around multiple selected elements."""
        # Calculate overall bounds
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        for element_id in selected_elements:
            primitive = self._find_primitive_by_id(element_id, spatial_primitives)
            if primitive:
                if hasattr(primitive, 'bounds'):
                    x1, y1, x2, y2 = primitive.bounds
                    min_x, min_y = min(min_x, x1), min(min_y, y1)
                    max_x, max_y = max(max_x, x2), max(max_y, y2)
                elif hasattr(primitive, 'position'):
                    x, y = primitive.position
                    margin = 10
                    min_x, min_y = min(min_x, x-margin), min(min_y, y-margin)
                    max_x, max_y = max(max_x, x+margin), max(max_y, y+margin)
        
        if min_x != float('inf'):
            # Draw selection bounds
            painter.setPen(QPen(QColor(self.theme.conventions.SELECTION_COLOR), 2, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            
            margin = 10
            painter.drawRect(QRectF(
                min_x - margin, min_y - margin,
                max_x - min_x + 2*margin, max_y - min_y + 2*margin
            ))
    
    def _render_drag_feedback(self, painter: QPainter, interaction_state: InteractionState):
        """Render drag operation feedback."""
        if not interaction_state.drag_start_pos or not interaction_state.drag_current_pos:
            return
            
        start_x, start_y = interaction_state.drag_start_pos
        curr_x, curr_y = interaction_state.drag_current_pos
        
        # Draw drag vector
        painter.setPen(QPen(QColor(self.theme.conventions.HOVER_COLOR), 2, Qt.DashLine))
        painter.drawLine(QPointF(start_x, start_y), QPointF(curr_x, curr_y))
        
        # Draw drag target indicator
        painter.setBrush(QBrush(QColor(self.theme.conventions.HOVER_COLOR)))
        painter.drawEllipse(QPointF(curr_x, curr_y), 4, 4)
    
    def _draw_element_outline(self, painter: QPainter, primitive: SpatialPrimitive, margin: int):
        """Draw outline around an element."""
        if hasattr(primitive, 'bounds'):
            x1, y1, x2, y2 = primitive.bounds
            painter.drawRect(QRectF(
                x1 - margin, y1 - margin,
                x2 - x1 + 2*margin, y2 - y1 + 2*margin
            ))
        elif hasattr(primitive, 'position'):
            x, y = primitive.position
            size = 20  # Default size for point elements
            painter.drawRect(QRectF(
                x - size/2 - margin, y - size/2 - margin,
                size + 2*margin, size + 2*margin
            ))
    
    def _find_primitive_by_id(self, element_id: ElementID, 
                             spatial_primitives: List[SpatialPrimitive]) -> Optional[SpatialPrimitive]:
        """Find spatial primitive by element ID."""
        for primitive in spatial_primitives:
            if primitive.element_id == element_id:
                return primitive
        return None


class ContextMenuManager:
    """Manages context menus for different selection types."""
    
    def __init__(self):
        self.mode_aware_selection: Optional[ModeAwareSelectionSystem] = None
    
    def set_selection_system(self, selection_system: ModeAwareSelectionSystem):
        """Set the mode-aware selection system."""
        self.mode_aware_selection = selection_system
    
    def create_context_menu(self, parent: QWidget, element_id: Optional[ElementID] = None) -> Optional['QMenu']:
        """Create context menu for current selection."""
        if not PYSIDE6_AVAILABLE or not self.mode_aware_selection:
            return None
            
        menu = QMenu(parent)
        
        # Get available actions from selection system
        available_actions = self.mode_aware_selection.get_available_actions()
        
        if not available_actions:
            # No actions available
            no_action = QAction("No actions available", menu)
            no_action.setEnabled(False)
            menu.addAction(no_action)
            return menu
        
        # Group actions by category
        compositional_actions = []
        transformation_actions = []
        
        for action in available_actions:
            if action.value.startswith("add_") or action.value.startswith("delete_") or action.value.startswith("connect_"):
                compositional_actions.append(action)
            elif action.value.startswith("apply_"):
                transformation_actions.append(action)
            else:
                compositional_actions.append(action)
        
        # Add compositional actions
        if compositional_actions:
            if self.mode_aware_selection.mode == Mode.WARMUP:
                menu.addSection("Composition Actions")
            else:
                menu.addSection("Basic Actions")
                
            for action in compositional_actions:
                self._add_action_to_menu(menu, action)
        
        # Add transformation actions
        if transformation_actions:
            menu.addSection("Transformation Rules")
            for action in transformation_actions:
                self._add_action_to_menu(menu, action)
        
        return menu
    
    def _add_action_to_menu(self, menu: 'QMenu', action_type: ActionType):
        """Add an action to the context menu."""
        # Convert action type to human-readable name
        action_name = self._format_action_name(action_type)
        
        action = QAction(action_name, menu)
        action.setData(action_type)  # Store action type for handling
        menu.addAction(action)
    
    def _format_action_name(self, action_type: ActionType) -> str:
        """Format action type as human-readable name."""
        name_map = {
            ActionType.ADD_VERTEX: "Add Vertex",
            ActionType.ADD_PREDICATE: "Add Predicate",
            ActionType.ADD_CUT: "Add Cut",
            ActionType.DELETE_ELEMENT: "Delete Element",
            ActionType.CONNECT_ELEMENTS: "Connect Elements",
            ActionType.DISCONNECT_ELEMENTS: "Disconnect Elements",
            ActionType.MOVE_ELEMENT: "Move Element",
            ActionType.EDIT_PROPERTIES: "Edit Properties",
            ActionType.APPLY_ERASURE: "Apply Erasure Rule",
            ActionType.APPLY_INSERTION: "Apply Insertion Rule",
            ActionType.APPLY_ITERATION: "Apply Iteration Rule",
            ActionType.APPLY_DE_ITERATION: "Apply De-iteration Rule",
            ActionType.APPLY_DOUBLE_CUT_ADDITION: "Add Double Cut",
            ActionType.APPLY_DOUBLE_CUT_REMOVAL: "Remove Double Cut",
            ActionType.APPLY_ISOLATED_VERTEX_ADDITION: "Add Isolated Vertex",
        }
        
        return name_map.get(action_type, action_type.value.replace("_", " ").title())


class EnhancedSelectionSystem:
    """Enhanced selection system with professional interaction patterns."""
    
    def __init__(self):
        self.mode_aware_selection = ModeAwareSelectionSystem()
        self.selection_renderer = SelectionRenderer()
        self.context_menu_manager = ContextMenuManager()
        self.interaction_state = InteractionState()
        
        self.context_menu_manager.set_selection_system(self.mode_aware_selection)
        
        # Callbacks for actions
        self.action_callbacks: Dict[ActionType, Callable] = {}
    
    def set_graph(self, graph: RelationalGraphWithCuts):
        """Set the current graph."""
        self.mode_aware_selection.set_graph(graph)
    
    def switch_mode(self, new_mode: Mode):
        """Switch between Warmup and Practice modes."""
        self.mode_aware_selection.switch_mode(new_mode)
    
    def handle_mouse_press(self, pos: Tuple[float, float], element_id: Optional[ElementID],
                          modifiers: int) -> bool:
        """Handle mouse press event."""
        x, y = pos
        
        # Check for multi-select modifier (Ctrl/Cmd)
        multi_select = bool(modifiers & Qt.ControlModifier)
        
        if element_id:
            # Select element
            self.mode_aware_selection.select_element(element_id, multi_select)
            
            # Start potential drag operation
            self.interaction_state.is_dragging = False  # Will be set to True on mouse move
            self.interaction_state.drag_start_pos = pos
            
            return True
        else:
            # Click on empty area
            if not multi_select:
                self.mode_aware_selection.clear_selection()
            
            # Start area selection
            self.interaction_state.drag_start_pos = pos
            return False
    
    def handle_mouse_move(self, pos: Tuple[float, float], element_id: Optional[ElementID]) -> bool:
        """Handle mouse move event."""
        # Update hover state
        self.interaction_state.hover_element = element_id
        self.interaction_state.hover_position = pos
        
        # Update drag state
        if self.interaction_state.drag_start_pos:
            self.interaction_state.is_dragging = True
            self.interaction_state.drag_current_pos = pos
            return True
        
        return False
    
    def handle_mouse_release(self, pos: Tuple[float, float]) -> bool:
        """Handle mouse release event."""
        was_dragging = self.interaction_state.is_dragging
        
        # Clear drag state
        self.interaction_state.is_dragging = False
        self.interaction_state.drag_start_pos = None
        self.interaction_state.drag_current_pos = None
        
        return was_dragging
    
    def handle_context_menu(self, parent: QWidget, pos: Tuple[float, float],
                           element_id: Optional[ElementID]) -> Optional['QMenu']:
        """Handle context menu request."""
        return self.context_menu_manager.create_context_menu(parent, element_id)
    
    def register_action_callback(self, action_type: ActionType, callback: Callable):
        """Register callback for action execution."""
        self.action_callbacks[action_type] = callback
    
    def execute_action(self, action_type: ActionType) -> bool:
        """Execute an action."""
        if action_type in self.action_callbacks:
            try:
                self.action_callbacks[action_type]()
                return True
            except Exception as e:
                print(f"Error executing action {action_type}: {e}")
                return False
        return False
    
    def render_selection_feedback(self, painter: QPainter, spatial_primitives: List[SpatialPrimitive]):
        """Render all selection feedback."""
        self.selection_renderer.render_selection_overlays(
            painter,
            self.mode_aware_selection.selection_state,
            spatial_primitives,
            self.interaction_state
        )
    
    def get_selection_state(self) -> SelectionState:
        """Get current selection state."""
        return self.mode_aware_selection.selection_state
    
    def get_available_actions(self) -> List[ActionType]:
        """Get available actions for current selection."""
        return self.mode_aware_selection.get_available_actions()


if __name__ == "__main__":
    print("=== Enhanced Selection System ===")
    print("Professional selection feedback and interaction patterns")
    
    # Test the enhanced selection system
    selection_system = EnhancedSelectionSystem()
    print(f"Current mode: {selection_system.mode_aware_selection.mode.value}")
    print(f"Available actions: {len(selection_system.get_available_actions())}")
