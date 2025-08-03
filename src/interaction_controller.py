#!/usr/bin/env python3
"""
Interaction Controller (Layer 4)

Handles user interactions, selection overlays, and dynamic visual effects.
Maps user actions to formal EGI operations while maintaining clean architecture.

Key Features:
- Selection system with visual overlays
- Context-sensitive action menus
- Dynamic resize handles and endpoints
- Professional interaction patterns
- Action-first workflow (Add Cut → Select → Execute)
"""

from typing import Dict, List, Optional, Set, Tuple, Callable, Any
from dataclasses import dataclass
from enum import Enum
import tkinter as tk
from tkinter import ttk

from egi_core_dau import RelationalGraphWithCuts, ElementID
from layout_engine_clean import CleanLayoutEngine, LayoutResult, SpatialPrimitive
from diagram_renderer_clean import CleanDiagramRenderer
from canvas_backends.canvas_protocol import CanvasProtocol, Coordinate, Bounds


class SelectionType(Enum):
    """Types of selection in the EG editor."""
    NONE = "none"
    SINGLE_ELEMENT = "single_element"
    MULTIPLE_ELEMENTS = "multiple_elements"
    AREA_SELECTION = "area_selection"
    EMPTY_AREA = "empty_area"


class ActionMode(Enum):
    """Current action mode in the editor."""
    NORMAL = "normal"
    ADD_CUT = "add_cut"
    ADD_INDIVIDUAL = "add_individual"
    ADD_PREDICATE = "add_predicate"
    MOVE = "move"
    DELETE = "delete"
    RESIZE = "resize"


@dataclass
class SelectionState:
    """Current selection state."""
    selection_type: SelectionType
    selected_elements: Set[ElementID]
    selection_bounds: Optional[Bounds]
    selection_area: Optional[ElementID]  # Area where selection occurred


@dataclass
class InteractionEvent:
    """User interaction event."""
    event_type: str  # 'click', 'drag', 'key', etc.
    position: Coordinate
    modifiers: Set[str]  # 'ctrl', 'shift', 'alt', etc.
    element_id: Optional[ElementID] = None


class InteractionController:
    """
    Layer 4: Interaction Controller
    
    Handles all user interactions and maps them to EGI operations.
    Provides selection overlays and dynamic visual effects.
    """
    
    def __init__(self, canvas: CanvasProtocol, layout_engine: CleanLayoutEngine, 
                 renderer: CleanDiagramRenderer):
        self.canvas = canvas
        self.layout_engine = layout_engine
        self.renderer = renderer
        
        # Current state
        self.graph: Optional[RelationalGraphWithCuts] = None
        self.layout_result: Optional[LayoutResult] = None
        self.action_mode = ActionMode.NORMAL
        self.selection_state = SelectionState(
            selection_type=SelectionType.NONE,
            selected_elements=set(),
            selection_bounds=None,
            selection_area=None
        )
        
        # Visual overlay state
        self.overlay_elements: Dict[str, Any] = {}
        self.hover_element: Optional[ElementID] = None
        
        # Action callbacks
        self.action_callbacks: Dict[str, Callable] = {}
        
    def set_graph(self, graph: RelationalGraphWithCuts) -> None:
        """Set the current graph and update layout."""
        self.graph = graph
        self.layout_result = self.layout_engine.layout_graph(graph)
        self._clear_selection()
        self._render_complete_diagram()
    
    def set_action_mode(self, mode: ActionMode) -> None:
        """Set the current action mode."""
        self.action_mode = mode
        self._clear_selection()
        self._update_cursor()
        self._show_mode_indicator()
    
    def handle_click(self, position: Coordinate, modifiers: Set[str] = None) -> None:
        """Handle mouse click event."""
        modifiers = modifiers or set()
        
        # Find element at position
        element_id = self._find_element_at_position(position)
        
        if self.action_mode == ActionMode.NORMAL:
            self._handle_normal_click(position, element_id, modifiers)
        elif self.action_mode == ActionMode.ADD_CUT:
            self._handle_add_cut_click(position, element_id, modifiers)
        elif self.action_mode == ActionMode.ADD_INDIVIDUAL:
            self._handle_add_individual_click(position, element_id, modifiers)
        elif self.action_mode == ActionMode.ADD_PREDICATE:
            self._handle_add_predicate_click(position, element_id, modifiers)
        elif self.action_mode == ActionMode.MOVE:
            self._handle_move_click(position, element_id, modifiers)
        elif self.action_mode == ActionMode.DELETE:
            self._handle_delete_click(position, element_id, modifiers)
    
    def handle_drag(self, start_pos: Coordinate, end_pos: Coordinate, 
                   modifiers: Set[str] = None) -> None:
        """Handle mouse drag event."""
        modifiers = modifiers or set()
        
        if self.action_mode == ActionMode.NORMAL:
            # Area selection
            self._handle_area_selection(start_pos, end_pos)
        elif self.action_mode == ActionMode.MOVE:
            # Move selected elements
            self._handle_element_move(start_pos, end_pos)
        elif self.action_mode == ActionMode.RESIZE:
            # Resize selected element
            self._handle_element_resize(start_pos, end_pos)
    
    def handle_hover(self, position: Coordinate) -> None:
        """Handle mouse hover event."""
        element_id = self._find_element_at_position(position)
        
        if element_id != self.hover_element:
            self._clear_hover_effects()
            self.hover_element = element_id
            if element_id:
                self._show_hover_effects(element_id)
    
    def handle_key(self, key: str, modifiers: Set[str] = None) -> None:
        """Handle keyboard event."""
        modifiers = modifiers or set()
        
        if key == 'Escape':
            self._cancel_current_action()
        elif key == 'Delete' and self.selection_state.selected_elements:
            self.set_action_mode(ActionMode.DELETE)
            self._execute_delete_action()
        elif key == 'Enter' and self.action_mode != ActionMode.NORMAL:
            self._execute_current_action()
    
    def _handle_normal_click(self, position: Coordinate, element_id: Optional[ElementID], 
                           modifiers: Set[str]) -> None:
        """Handle click in normal mode (selection)."""
        if 'ctrl' in modifiers or 'cmd' in modifiers:
            # Multi-select
            if element_id:
                if element_id in self.selection_state.selected_elements:
                    self.selection_state.selected_elements.remove(element_id)
                else:
                    self.selection_state.selected_elements.add(element_id)
                self._update_selection_overlays()
        else:
            # Single select
            if element_id:
                self._select_single_element(element_id)
            else:
                self._select_empty_area(position)
    
    def _select_single_element(self, element_id: ElementID) -> None:
        """Select a single element."""
        self.selection_state.selection_type = SelectionType.SINGLE_ELEMENT
        self.selection_state.selected_elements = {element_id}
        self.selection_state.selection_bounds = None
        self._update_selection_overlays()
        self._show_context_actions(element_id)
    
    def _select_empty_area(self, position: Coordinate) -> None:
        """Select an empty area."""
        area_id = self._find_area_at_position(position)
        self.selection_state.selection_type = SelectionType.EMPTY_AREA
        self.selection_state.selected_elements = set()
        self.selection_state.selection_area = area_id
        self._show_empty_area_overlay(position)
        self._show_empty_area_actions(position, area_id)
    
    def _handle_area_selection(self, start_pos: Coordinate, end_pos: Coordinate) -> None:
        """Handle drag-to-select area selection."""
        # Create selection rectangle
        x1, y1 = start_pos
        x2, y2 = end_pos
        selection_bounds = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        
        # Find elements within selection bounds
        selected_elements = self._find_elements_in_bounds(selection_bounds)
        
        if selected_elements:
            self.selection_state.selection_type = SelectionType.MULTIPLE_ELEMENTS
            self.selection_state.selected_elements = selected_elements
        else:
            self.selection_state.selection_type = SelectionType.AREA_SELECTION
        
        self.selection_state.selection_bounds = selection_bounds
        self._update_selection_overlays()
    
    def _update_selection_overlays(self) -> None:
        """Update visual selection overlays."""
        self._clear_selection_overlays()
        
        if self.selection_state.selection_type == SelectionType.SINGLE_ELEMENT:
            element_id = next(iter(self.selection_state.selected_elements))
            self._show_single_element_overlay(element_id)
        
        elif self.selection_state.selection_type == SelectionType.MULTIPLE_ELEMENTS:
            self._show_multiple_elements_overlay()
        
        elif self.selection_state.selection_type == SelectionType.AREA_SELECTION:
            self._show_area_selection_overlay()
    
    def _show_single_element_overlay(self, element_id: ElementID) -> None:
        """Show overlay for single selected element."""
        if not self.layout_result or element_id not in self.layout_result.primitives:
            return
        
        primitive = self.layout_result.primitives[element_id]
        
        if primitive.element_type == 'cut':
            self._show_cut_resize_handles(primitive)
        elif primitive.element_type == 'vertex':
            self._show_vertex_selection_highlight(primitive)
        elif primitive.element_type == 'edge':
            self._show_predicate_selection_highlight(primitive)
    
    def _show_cut_resize_handles(self, cut_primitive: SpatialPrimitive) -> None:
        """Show resize handles for selected cut."""
        x1, y1, x2, y2 = cut_primitive.bounds
        handle_size = 8
        
        # Corner handles
        handles = [
            (x1 - handle_size/2, y1 - handle_size/2),  # Top-left
            (x2 - handle_size/2, y1 - handle_size/2),  # Top-right
            (x2 - handle_size/2, y2 - handle_size/2),  # Bottom-right
            (x1 - handle_size/2, y2 - handle_size/2),  # Bottom-left
        ]
        
        for i, (hx, hy) in enumerate(handles):
            handle_id = f"cut_handle_{i}"
            self.canvas.draw_rectangle(
                bounds=(hx, hy, hx + handle_size, hy + handle_size),
                fill_color="blue",
                outline_color="darkblue",
                outline_width=1
            )
            self.overlay_elements[handle_id] = (hx, hy, hx + handle_size, hy + handle_size)
    
    def _show_vertex_selection_highlight(self, vertex_primitive: SpatialPrimitive) -> None:
        """Show selection highlight for vertex."""
        x, y = vertex_primitive.position
        radius = 12  # Slightly larger than vertex
        
        self.canvas.draw_circle(
            center=(x, y),
            radius=radius,
            fill_color=None,
            outline_color="blue",
            outline_width=2
        )
        self.overlay_elements["vertex_highlight"] = (x - radius, y - radius, 
                                                   x + radius, y + radius)
    
    def _show_predicate_selection_highlight(self, predicate_primitive: SpatialPrimitive) -> None:
        """Show selection highlight for predicate."""
        x, y = predicate_primitive.position
        padding = 10
        
        # Estimate text bounds (simplified)
        text_width = 60  # Approximate
        text_height = 20
        
        bounds = (x - text_width/2 - padding, y - text_height/2 - padding,
                 x + text_width/2 + padding, y + text_height/2 + padding)
        
        self.canvas.draw_rectangle(
            bounds=bounds,
            fill_color=None,
            outline_color="blue",
            outline_width=2
        )
        self.overlay_elements["predicate_highlight"] = bounds
    
    def _clear_selection_overlays(self) -> None:
        """Clear all selection overlays."""
        self.overlay_elements.clear()
        # Note: In a real implementation, we'd need to track and remove overlay elements
        # from the canvas. For now, we'll re-render the entire diagram.
        self._render_complete_diagram()
    
    def _render_complete_diagram(self) -> None:
        """Render the complete diagram with current overlays."""
        if self.graph and self.layout_result:
            self.renderer.render_diagram(self.layout_result, self.graph)
            # Overlays would be rendered on top
    
    def _find_element_at_position(self, position: Coordinate) -> Optional[ElementID]:
        """Find element at given position."""
        if not self.layout_result:
            return None
        
        x, y = position
        
        # Check elements in reverse z-order (top to bottom)
        for element_id, primitive in sorted(self.layout_result.primitives.items(),
                                          key=lambda item: item[1].z_index, reverse=True):
            if self._point_in_primitive(position, primitive):
                return element_id
        
        return None
    
    def _point_in_primitive(self, position: Coordinate, primitive: SpatialPrimitive) -> bool:
        """Check if point is within primitive bounds."""
        x, y = position
        x1, y1, x2, y2 = primitive.bounds
        return x1 <= x <= x2 and y1 <= y <= y2
    
    def _find_area_at_position(self, position: Coordinate) -> Optional[ElementID]:
        """Find which area contains the given position."""
        if not self.graph or not self.layout_result:
            return self.graph.sheet if self.graph else None
        
        # Check cuts from innermost to outermost
        for element_id, primitive in self.layout_result.primitives.items():
            if (primitive.element_type == 'cut' and 
                self._point_in_primitive(position, primitive)):
                return element_id
        
        # Default to sheet level
        return self.graph.sheet
    
    def _clear_selection(self) -> None:
        """Clear current selection."""
        self.selection_state = SelectionState(
            selection_type=SelectionType.NONE,
            selected_elements=set(),
            selection_bounds=None,
            selection_area=None
        )
        self._clear_selection_overlays()
    
    # Placeholder methods for additional functionality
    def _handle_add_cut_click(self, position, element_id, modifiers): pass
    def _handle_add_individual_click(self, position, element_id, modifiers): pass
    def _handle_add_predicate_click(self, position, element_id, modifiers): pass
    def _handle_move_click(self, position, element_id, modifiers): pass
    def _handle_delete_click(self, position, element_id, modifiers): pass
    def _handle_element_move(self, start_pos, end_pos): pass
    def _handle_element_resize(self, start_pos, end_pos): pass
    def _show_hover_effects(self, element_id): pass
    def _clear_hover_effects(self): pass
    def _show_context_actions(self, element_id): pass
    def _show_empty_area_overlay(self, position): pass
    def _show_empty_area_actions(self, position, area_id): pass
    def _show_multiple_elements_overlay(self): pass
    def _show_area_selection_overlay(self): pass
    def _find_elements_in_bounds(self, bounds): return set()
    def _update_cursor(self): pass
    def _show_mode_indicator(self): pass
    def _cancel_current_action(self): pass
    def _execute_delete_action(self): pass
    def _execute_current_action(self): pass
