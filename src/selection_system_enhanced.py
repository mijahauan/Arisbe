#!/usr/bin/env python3
"""
Enhanced Selection System with Contextual Overlays

Implements the detailed specification for the bullpen graph editor's interactive layer:
- Selection object storing EGI elements with visual overlays
- Contextual overlays (empty area, single element, subgraph)
- Context-sensitive actions mapped to EGI rules
- Dynamic visual feedback and rule enforcement
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
import tkinter as tk

from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut, ElementID
from layout_engine_clean import LayoutResult, SpatialPrimitive
from canvas_backend import Canvas, Coordinate

# Type alias for bounds (x1, y1, x2, y2)
Bounds = Tuple[float, float, float, float]


class SelectionType(Enum):
    """Types of selection in the EG editor."""
    EMPTY = "empty"                    # No selection
    EMPTY_AREA = "empty_area"          # Click-drag over empty area (subgraph insertion area)
    SINGLE_ELEMENT = "single_element"  # Single click on EGI element
    SUBGRAPH = "subgraph"             # Multiple elements selected as composite unit


class ActionType(Enum):
    """Categories of user actions mapped to EGI rules."""
    # Insert Actions
    INSERT_CUT = "insert_cut"
    INSERT_PREDICATE = "insert_predicate"
    INSERT_LOI = "insert_loi"
    PASTE_SUBGRAPH = "paste_subgraph"
    
    # Modify Actions (appearance-only unless specified)
    MOVE = "move"                      # Layout-only change
    RESIZE = "resize"                  # Layout-only change
    CONNECT_DISCONNECT = "connect_disconnect"  # Logical change to nuMap
    EDIT_PREDICATE = "edit_predicate"  # Logical change to kappaMap/nuMap
    
    # Delete Actions
    DELETE = "delete"                  # Logical change (Erasure/Deiteration)


@dataclass
class Selection:
    """
    Selection object storing EGI elements with visual overlay state.
    
    Corresponds to the logical structure of the EGI model and provides
    context-sensitive visual feedback.
    """
    selection_type: SelectionType
    selected_elements: Set[ElementID]  # EGI elements (Vertex, Edge, Cut)
    selection_bounds: Optional[Bounds]  # Bounding rectangle for area selections
    target_area: Optional[ElementID]   # Area where selection occurred (for insertions)
    
    # Visual overlay state
    overlay_elements: Dict[str, Any]   # Visual overlay components
    is_valid: bool = True              # Whether selection represents valid operation
    validation_message: Optional[str] = None  # Error message for invalid selections


class ContextualOverlay:
    """
    Manages contextual overlays that change based on selection type.
    
    Provides visual feedback corresponding to the logical structure
    and available operations.
    """
    
    def __init__(self, canvas: Canvas):
        self.canvas = canvas
        self.current_overlays: Dict[str, Any] = {}
    
    def show_empty_area_overlay(self, bounds: Bounds) -> Dict[str, Any]:
        """
        Show dotted-line rectangle for empty area selection.
        Represents a potential subgraph insertion area.
        """
        x1, y1, x2, y2 = bounds
        
        # Draw dotted rectangle
        overlay_id = "empty_area_rect"
        self.canvas.draw_rectangle(
            bounds=bounds,
            fill_color=None,
            outline_color="blue",
            outline_width=2,
            dash_pattern=[5, 5]  # Dotted line
        )
        
        # Add corner indicators for insertion points
        corner_size = 8
        corners = [
            (x1, y1), (x2, y1), (x2, y2), (x1, y2)  # TL, TR, BR, BL
        ]
        
        corner_overlays = {}
        for i, (cx, cy) in enumerate(corners):
            corner_id = f"corner_{i}"
            self.canvas.draw_rectangle(
                bounds=(cx - corner_size/2, cy - corner_size/2, 
                       cx + corner_size/2, cy + corner_size/2),
                fill_color="lightblue",
                outline_color="blue",
                outline_width=1
            )
            corner_overlays[corner_id] = (cx, cy)
        
        return {
            overlay_id: bounds,
            "corners": corner_overlays,
            "insertion_area": bounds
        }
    
    def show_single_element_overlay(self, element_id: ElementID, 
                                   primitive: SpatialPrimitive,
                                   graph: RelationalGraphWithCuts) -> Dict[str, Any]:
        """
        Show highlight for single selected element with context-specific handles.
        
        For multi-part elements like LoI, highlights all segments, branches, and endpoints.
        """
        overlays = {}
        
        if primitive.element_type == 'cut':
            overlays.update(self._show_cut_overlay(element_id, primitive))
        elif primitive.element_type == 'vertex':
            overlays.update(self._show_vertex_overlay(element_id, primitive, graph))
        elif primitive.element_type == 'edge':
            overlays.update(self._show_edge_overlay(element_id, primitive, graph))
        
        return overlays
    
    def show_subgraph_overlay(self, selected_elements: Set[ElementID],
                             primitives: Dict[ElementID, SpatialPrimitive],
                             graph: RelationalGraphWithCuts) -> Dict[str, Any]:
        """
        Show composite highlight for subgraph selection.
        Highlights all selected elements and their shared enclosing context.
        """
        overlays = {}
        
        # Calculate bounding box of all selected elements
        if not selected_elements:
            return overlays
        
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        for element_id in selected_elements:
            if element_id in primitives:
                primitive = primitives[element_id]
                x1, y1, x2, y2 = primitive.bounds
                min_x = min(min_x, x1)
                min_y = min(min_y, y1)
                max_x = max(max_x, x2)
                max_y = max(max_y, y2)
        
        # Draw composite bounding box
        padding = 10
        composite_bounds = (min_x - padding, min_y - padding, 
                          max_x + padding, max_y + padding)
        
        self.canvas.draw_rectangle(
            bounds=composite_bounds,
            fill_color="rgba(0, 100, 255, 0.1)",  # Semi-transparent blue
            outline_color="blue",
            outline_width=3,
            dash_pattern=[10, 5]
        )
        
        # Highlight individual elements
        for element_id in selected_elements:
            if element_id in primitives:
                primitive = primitives[element_id]
                element_overlay = self._highlight_element(element_id, primitive)
                overlays[f"element_{element_id}"] = element_overlay
        
        overlays["composite_bounds"] = composite_bounds
        overlays["element_count"] = len(selected_elements)
        
        return overlays
    
    def _show_cut_overlay(self, cut_id: ElementID, primitive: SpatialPrimitive) -> Dict[str, Any]:
        """Show cut-specific overlay with resize handles."""
        x1, y1, x2, y2 = primitive.bounds
        overlays = {}
        
        # Main cut highlight
        self.canvas.draw_curve(
            points=primitive.curve_points if hasattr(primitive, 'curve_points') else [],
            width=3,
            color="blue",
            fill=False
        )
        overlays["cut_highlight"] = primitive.bounds
        
        # Resize handles at cardinal points
        center_x, center_y = (x1 + x2) / 2, (y1 + y2) / 2
        handle_size = 8
        
        handles = [
            ("top", center_x, y1),
            ("right", x2, center_y),
            ("bottom", center_x, y2),
            ("left", x1, center_y),
            ("top_left", x1, y1),
            ("top_right", x2, y1),
            ("bottom_right", x2, y2),
            ("bottom_left", x1, y2)
        ]
        
        for handle_name, hx, hy in handles:
            self.canvas.draw_rectangle(
                bounds=(hx - handle_size/2, hy - handle_size/2,
                       hx + handle_size/2, hy + handle_size/2),
                fill_color="white",
                outline_color="blue",
                outline_width=2
            )
            overlays[f"handle_{handle_name}"] = (hx, hy)
        
        return overlays
    
    def _show_vertex_overlay(self, vertex_id: ElementID, primitive: SpatialPrimitive,
                           graph: RelationalGraphWithCuts) -> Dict[str, Any]:
        """Show vertex-specific overlay with connection points."""
        x, y = primitive.position
        overlays = {}
        
        # Main vertex highlight (larger circle)
        highlight_radius = 15
        self.canvas.draw_circle(
            center=(x, y),
            radius=highlight_radius,
            fill_color=None,
            outline_color="blue",
            outline_width=3
        )
        overlays["vertex_highlight"] = (x - highlight_radius, y - highlight_radius,
                                      x + highlight_radius, y + highlight_radius)
        
        # Connection endpoints for LoI (if this vertex is part of lines of identity)
        # Show potential connection points at 8 cardinal directions
        connection_radius = 20
        angles = [0, 45, 90, 135, 180, 225, 270, 315]
        
        import math
        for i, angle_deg in enumerate(angles):
            angle_rad = math.radians(angle_deg)
            endpoint_x = x + connection_radius * math.cos(angle_rad)
            endpoint_y = y + connection_radius * math.sin(angle_rad)
            
            self.canvas.draw_circle(
                center=(endpoint_x, endpoint_y),
                radius=3,
                fill_color="lightblue",
                outline_color="blue",
                outline_width=1
            )
            overlays[f"connection_point_{i}"] = (endpoint_x, endpoint_y)
        
        return overlays
    
    def _show_edge_overlay(self, edge_id: ElementID, primitive: SpatialPrimitive,
                          graph: RelationalGraphWithCuts) -> Dict[str, Any]:
        """Show edge/predicate-specific overlay with hooks and edit handles."""
        x, y = primitive.position
        overlays = {}
        
        # Main predicate highlight
        padding = 15
        text_width = 80  # Approximate
        text_height = 25
        
        highlight_bounds = (x - text_width/2 - padding, y - text_height/2 - padding,
                          x + text_width/2 + padding, y + text_height/2 + padding)
        
        self.canvas.draw_rectangle(
            bounds=highlight_bounds,
            fill_color="rgba(255, 255, 0, 0.2)",  # Semi-transparent yellow
            outline_color="orange",
            outline_width=2
        )
        overlays["predicate_highlight"] = highlight_bounds
        
        # Edit handle (double-click indicator)
        edit_handle_size = 12
        edit_x = x + text_width/2 + padding - edit_handle_size/2
        edit_y = y - text_height/2 - padding + edit_handle_size/2
        
        self.canvas.draw_rectangle(
            bounds=(edit_x - edit_handle_size/2, edit_y - edit_handle_size/2,
                   edit_x + edit_handle_size/2, edit_y + edit_handle_size/2),
            fill_color="yellow",
            outline_color="orange",
            outline_width=1
        )
        overlays["edit_handle"] = (edit_x, edit_y)
        
        # Hook connection points (based on arity)
        if hasattr(primitive, 'attachment_points') and primitive.attachment_points:
            for i, (vertex_key, vertex_pos) in enumerate(primitive.attachment_points.items()):
                hook_x, hook_y = vertex_pos
                self.canvas.draw_circle(
                    center=(hook_x, hook_y),
                    radius=4,
                    fill_color="red",
                    outline_color="darkred",
                    outline_width=1
                )
                overlays[f"hook_{i}"] = (hook_x, hook_y)
        
        return overlays
    
    def _highlight_element(self, element_id: ElementID, primitive: SpatialPrimitive) -> Dict[str, Any]:
        """Generic element highlighting for subgraph selections."""
        if primitive.element_type == 'cut':
            self.canvas.draw_curve(
                points=primitive.curve_points if hasattr(primitive, 'curve_points') else [],
                width=2,
                color="blue",
                fill=False
            )
        elif primitive.element_type == 'vertex':
            x, y = primitive.position
            self.canvas.draw_circle(
                center=(x, y),
                radius=10,
                fill_color=None,
                outline_color="blue",
                outline_width=2
            )
        elif primitive.element_type == 'edge':
            x1, y1, x2, y2 = primitive.bounds
            self.canvas.draw_rectangle(
                bounds=(x1, y1, x2, y2),
                fill_color=None,
                outline_color="blue",
                outline_width=2
            )
        
        return {"highlighted": True, "bounds": primitive.bounds}
    
    def clear_overlays(self) -> None:
        """Clear all current overlays."""
        self.current_overlays.clear()
        # Note: In a real implementation, we'd track and remove specific overlay elements


class SelectionValidator:
    """
    Validates selections and provides feedback for rule enforcement.
    
    Ensures all operations maintain syntactic validity of the EGI.
    """
    
    def __init__(self, graph: RelationalGraphWithCuts):
        self.graph = graph
    
    def validate_cut_insertion(self, target_area: ElementID, bounds: Bounds) -> Tuple[bool, Optional[str]]:
        """Validate that a new cut can be inserted without violating non-overlapping rule."""
        # Check for overlaps with existing cuts in the same area
        # This would need access to layout information to check spatial overlaps
        return True, None  # Placeholder
    
    def validate_connection(self, from_element: ElementID, to_element: ElementID) -> Tuple[bool, Optional[str]]:
        """Validate that two elements can be connected according to ligature rules."""
        # Check if connection would create valid ligature structure
        return True, None  # Placeholder
    
    def validate_deletion(self, elements: Set[ElementID]) -> Tuple[bool, Optional[str]]:
        """Validate that elements can be deleted (Erasure/Deiteration rules)."""
        # Check if deletion constitutes valid EGI operation
        return True, None  # Placeholder
    
    def validate_predicate_edit(self, edge_id: ElementID, new_label: str, new_arity: int) -> Tuple[bool, Optional[str]]:
        """Validate predicate label and arity changes."""
        if new_arity < 1:
            return False, "Predicate arity must be at least 1"
        if not new_label.strip():
            return False, "Predicate label cannot be empty"
        return True, None


class EnhancedSelectionSystem:
    """
    Enhanced selection system implementing the detailed specification.
    
    Manages Selection objects, contextual overlays, and rule enforcement.
    """
    
    def __init__(self, canvas: Canvas):
        self.canvas = canvas
        self.overlay_manager = ContextualOverlay(canvas)
        self.current_selection = Selection(
            selection_type=SelectionType.EMPTY,
            selected_elements=set(),
            selection_bounds=None,
            target_area=None,
            overlay_elements={}
        )
        self.validator: Optional[SelectionValidator] = None
    
    def set_graph(self, graph: RelationalGraphWithCuts) -> None:
        """Set the current graph for validation."""
        self.validator = SelectionValidator(graph)
    
    def select_empty_area(self, bounds: Bounds, target_area: ElementID) -> Selection:
        """Create empty area selection for subgraph insertion."""
        self.clear_selection()
        
        overlays = self.overlay_manager.show_empty_area_overlay(bounds)
        
        self.current_selection = Selection(
            selection_type=SelectionType.EMPTY_AREA,
            selected_elements=set(),
            selection_bounds=bounds,
            target_area=target_area,
            overlay_elements=overlays
        )
        
        return self.current_selection
    
    def select_single_element(self, element_id: ElementID, primitive: SpatialPrimitive,
                            graph: RelationalGraphWithCuts) -> Selection:
        """Create single element selection with context-specific overlay."""
        self.clear_selection()
        
        overlays = self.overlay_manager.show_single_element_overlay(element_id, primitive, graph)
        
        self.current_selection = Selection(
            selection_type=SelectionType.SINGLE_ELEMENT,
            selected_elements={element_id},
            selection_bounds=primitive.bounds,
            target_area=primitive.parent_area,
            overlay_elements=overlays
        )
        
        return self.current_selection
    
    def select_subgraph(self, elements: Set[ElementID], 
                       primitives: Dict[ElementID, SpatialPrimitive],
                       graph: RelationalGraphWithCuts) -> Selection:
        """Create subgraph selection with composite overlay."""
        self.clear_selection()
        
        overlays = self.overlay_manager.show_subgraph_overlay(elements, primitives, graph)
        
        # Calculate composite bounds
        if elements:
            min_x = min_y = float('inf')
            max_x = max_y = float('-inf')
            for element_id in elements:
                if element_id in primitives:
                    x1, y1, x2, y2 = primitives[element_id].bounds
                    min_x, min_y = min(min_x, x1), min(min_y, y1)
                    max_x, max_y = max(max_x, x2), max(max_y, y2)
            composite_bounds = (min_x, min_y, max_x, max_y)
        else:
            composite_bounds = None
        
        self.current_selection = Selection(
            selection_type=SelectionType.SUBGRAPH,
            selected_elements=elements,
            selection_bounds=composite_bounds,
            target_area=None,  # Multiple areas possible
            overlay_elements=overlays
        )
        
        return self.current_selection
    
    def clear_selection(self) -> None:
        """Clear current selection and overlays."""
        self.overlay_manager.clear_overlays()
        self.current_selection = Selection(
            selection_type=SelectionType.EMPTY,
            selected_elements=set(),
            selection_bounds=None,
            target_area=None,
            overlay_elements={}
        )
    
    def get_available_actions(self) -> List[ActionType]:
        """Get list of available actions based on current selection."""
        if self.current_selection.selection_type == SelectionType.EMPTY_AREA:
            return [ActionType.INSERT_CUT, ActionType.INSERT_PREDICATE, 
                   ActionType.INSERT_LOI, ActionType.PASTE_SUBGRAPH]
        
        elif self.current_selection.selection_type == SelectionType.SINGLE_ELEMENT:
            element_id = next(iter(self.current_selection.selected_elements))
            # Determine element type and return appropriate actions
            return [ActionType.MOVE, ActionType.DELETE, ActionType.EDIT_PREDICATE]
        
        elif self.current_selection.selection_type == SelectionType.SUBGRAPH:
            return [ActionType.MOVE, ActionType.DELETE, ActionType.CONNECT_DISCONNECT]
        
        return []
    
    def validate_action(self, action: ActionType, **kwargs) -> Tuple[bool, Optional[str]]:
        """Validate if an action can be performed on current selection."""
        if not self.validator:
            return True, None
        
        if action == ActionType.INSERT_CUT:
            return self.validator.validate_cut_insertion(
                self.current_selection.target_area,
                self.current_selection.selection_bounds
            )
        elif action == ActionType.DELETE:
            return self.validator.validate_deletion(self.current_selection.selected_elements)
        # Add other validations as needed
        
        return True, None
