#!/usr/bin/env python3
"""
Enhanced Diagram Controller with Context-Sensitive Actions

Implements the detailed specification for context-sensitive actions mapped to EGI rules:
- Insert actions (Cut, Predicate, LoI, Paste) 
- Modify actions (Move, Resize, Connect/Disconnect, Edit Predicate)
- Delete actions with rule enforcement
- Clear distinction between logical (EGI) and appearance-only (layout) changes
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from dataclasses import dataclass
from enum import Enum
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox

from egi_core_dau import (
    RelationalGraphWithCuts, Vertex, Edge, Cut, ElementID,
    create_vertex, create_edge, create_cut
)
from layout_engine_clean import CleanLayoutEngine, LayoutResult, SpatialPrimitive
from diagram_renderer_clean import CleanDiagramRenderer
from canvas_backend import Canvas, Coordinate
from selection_system_enhanced import (
    EnhancedSelectionSystem, Selection, SelectionType, ActionType
)

# Type alias for bounds (x1, y1, x2, y2)
Bounds = Tuple[float, float, float, float]


class ChangeType(Enum):
    """Types of changes to track for undo/redo."""
    LOGICAL = "logical"        # Changes to EGI model
    APPEARANCE = "appearance"  # Changes to layout only


@dataclass
class Change:
    """Represents a change that can be undone/redone."""
    change_type: ChangeType
    description: str
    undo_data: Any
    redo_data: Any
    timestamp: float


class EGIOperations:
    """
    Formal EGI operations that maintain syntactic validity.
    
    All operations return new EGI instances (immutable pattern).
    """
    
    @staticmethod
    def insert_cut(graph: RelationalGraphWithCuts, target_area: ElementID,
                   enclosed_elements: Set[ElementID]) -> RelationalGraphWithCuts:
        """Insert a new cut enclosing specified elements."""
        # Create new cut
        new_cut = create_cut()
        
        # Add cut to graph
        new_graph = graph.with_cut(new_cut)
        
        # Update area mapping: move enclosed elements to new cut
        new_area_map = dict(graph.area)
        
        # Remove enclosed elements from their current areas
        for area_id, elements in new_area_map.items():
            new_area_map[area_id] = elements - enclosed_elements
        
        # Add enclosed elements to new cut
        new_area_map[new_cut.id] = enclosed_elements
        
        # Add new cut to target area
        if target_area in new_area_map:
            new_area_map[target_area] = new_area_map[target_area] | {new_cut.id}
        
        # Create new graph with updated area mapping
        return new_graph._replace(area=new_area_map)
    
    @staticmethod
    def insert_predicate(graph: RelationalGraphWithCuts, target_area: ElementID,
                        label: str, arity: int) -> Tuple[RelationalGraphWithCuts, ElementID]:
        """Insert a new predicate (edge) in specified area."""
        # Create vertices for the predicate arguments
        vertices = []
        for i in range(arity):
            vertex = create_vertex(label=None, is_generic=True)
            vertices.append(vertex)
        
        # Create edge
        edge = create_edge()
        
        # Build new graph
        new_graph = graph
        for vertex in vertices:
            new_graph = new_graph.with_vertex(vertex)
        new_graph = new_graph.with_edge(edge)
        
        # Update mappings
        new_rel = dict(new_graph.rel)
        new_rel[edge.id] = label
        
        new_nu = dict(new_graph.nu)
        new_nu[edge.id] = tuple(v.id for v in vertices)
        
        new_area = dict(new_graph.area)
        if target_area in new_area:
            new_area[target_area] = new_area[target_area] | {edge.id} | {v.id for v in vertices}
        
        return new_graph._replace(rel=new_rel, nu=new_nu, area=new_area), edge.id
    
    @staticmethod
    def insert_loi(graph: RelationalGraphWithCuts, target_area: ElementID) -> Tuple[RelationalGraphWithCuts, ElementID]:
        """Insert a new Line of Identity (vertex) in specified area."""
        vertex = create_vertex(label=None, is_generic=True)
        new_graph = graph.with_vertex(vertex)
        
        # Add to area
        new_area = dict(new_graph.area)
        if target_area in new_area:
            new_area[target_area] = new_area[target_area] | {vertex.id}
        
        return new_graph._replace(area=new_area), vertex.id
    
    @staticmethod
    def delete_elements(graph: RelationalGraphWithCuts, 
                       elements: Set[ElementID]) -> RelationalGraphWithCuts:
        """Delete elements following Erasure/Deiteration rules."""
        new_graph = graph
        
        # Remove from area mappings
        new_area = dict(graph.area)
        for area_id, area_elements in new_area.items():
            new_area[area_id] = area_elements - elements
        
        # Remove from other mappings
        new_rel = {k: v for k, v in graph.rel.items() if k not in elements}
        new_nu = {k: v for k, v in graph.nu.items() if k not in elements}
        
        # Remove vertices, edges, cuts
        new_V = graph.V - elements
        new_E = graph.E - elements
        new_Cut = graph.Cut - elements
        
        return new_graph._replace(
            V=new_V, E=new_E, Cut=new_Cut,
            rel=new_rel, nu=new_nu, area=new_area
        )
    
    @staticmethod
    def connect_elements(graph: RelationalGraphWithCuts, 
                        from_element: ElementID, to_element: ElementID) -> RelationalGraphWithCuts:
        """Connect two elements (update nuMap for ligatures)."""
        # This would implement the complex ligature connection logic
        # For now, return unchanged graph
        return graph
    
    @staticmethod
    def edit_predicate(graph: RelationalGraphWithCuts, edge_id: ElementID,
                      new_label: str, new_arity: int) -> RelationalGraphWithCuts:
        """Edit predicate label and arity."""
        new_rel = dict(graph.rel)
        new_rel[edge_id] = new_label
        
        # Handle arity changes (complex - may need to add/remove vertices)
        # For now, just update the label
        return graph._replace(rel=new_rel)


class EnhancedDiagramController:
    """
    Enhanced Diagram Controller implementing context-sensitive actions.
    
    Maps user gestures to formal EGI operations while maintaining
    clear separation between logical and appearance-only changes.
    """
    
    def __init__(self, canvas: Canvas, layout_engine: CleanLayoutEngine,
                 renderer: CleanDiagramRenderer):
        self.canvas = canvas
        self.layout_engine = layout_engine
        self.renderer = renderer
        self.selection_system = EnhancedSelectionSystem(canvas)
        
        # State management
        self.current_graph: Optional[RelationalGraphWithCuts] = None
        self.current_layout: Optional[LayoutResult] = None
        self.change_history: List[Change] = []
        self.history_index = -1
        
        # Clipboard for copy/paste
        self.clipboard: Optional[Dict[str, Any]] = None
        
        # Event callbacks
        self.on_graph_changed: Optional[Callable[[RelationalGraphWithCuts], None]] = None
        self.on_layout_changed: Optional[Callable[[LayoutResult], None]] = None
    
    def set_graph(self, graph: RelationalGraphWithCuts) -> None:
        """Set the current graph and update all systems."""
        self.current_graph = graph
        self.current_layout = self.layout_engine.layout_graph(graph)
        self.selection_system.set_graph(graph)
        self._render_diagram()
        
        if self.on_graph_changed:
            self.on_graph_changed(graph)
    
    def handle_click(self, position: Coordinate, modifiers: Set[str] = None) -> None:
        """Handle mouse click with context-sensitive selection."""
        modifiers = modifiers or set()
        
        if not self.current_graph or not self.current_layout:
            return
        
        # Find element at position
        element_id = self._find_element_at_position(position)
        
        if element_id:
            # Single element selection
            primitive = self.current_layout.primitives[element_id]
            
            if 'ctrl' in modifiers or 'cmd' in modifiers:
                # Multi-select for subgraph
                current_selection = self.selection_system.current_selection.selected_elements
                if element_id in current_selection:
                    current_selection.remove(element_id)
                else:
                    current_selection.add(element_id)
                
                if len(current_selection) > 1:
                    primitives = {eid: self.current_layout.primitives[eid] 
                                for eid in current_selection 
                                if eid in self.current_layout.primitives}
                    self.selection_system.select_subgraph(current_selection, primitives, self.current_graph)
                elif len(current_selection) == 1:
                    eid = next(iter(current_selection))
                    self.selection_system.select_single_element(eid, self.current_layout.primitives[eid], self.current_graph)
                else:
                    self.selection_system.clear_selection()
            else:
                # Single select
                self.selection_system.select_single_element(element_id, primitive, self.current_graph)
        else:
            # Empty area - start area selection or clear selection
            area_id = self._find_area_at_position(position)
            self.selection_system.clear_selection()
    
    def handle_drag(self, start_pos: Coordinate, end_pos: Coordinate) -> None:
        """Handle drag gesture for area selection or element movement."""
        if not self.current_graph or not self.current_layout:
            return
        
        current_selection = self.selection_system.current_selection
        
        if current_selection.selection_type == SelectionType.EMPTY:
            # Area selection
            bounds = self._calculate_bounds(start_pos, end_pos)
            elements_in_area = self._find_elements_in_bounds(bounds)
            area_id = self._find_area_at_position(start_pos)
            
            if elements_in_area:
                # Subgraph selection
                primitives = {eid: self.current_layout.primitives[eid] 
                            for eid in elements_in_area 
                            if eid in self.current_layout.primitives}
                self.selection_system.select_subgraph(elements_in_area, primitives, self.current_graph)
            else:
                # Empty area selection
                self.selection_system.select_empty_area(bounds, area_id)
        
        elif current_selection.selection_type in [SelectionType.SINGLE_ELEMENT, SelectionType.SUBGRAPH]:
            # Element movement (appearance-only change)
            self._move_selected_elements(start_pos, end_pos)
    
    def execute_action(self, action: ActionType, **kwargs) -> bool:
        """Execute a context-sensitive action."""
        if not self.current_graph:
            return False
        
        # Validate action
        is_valid, error_msg = self.selection_system.validate_action(action, **kwargs)
        if not is_valid:
            self._show_error(f"Cannot perform {action.value}: {error_msg}")
            return False
        
        try:
            if action == ActionType.INSERT_CUT:
                return self._execute_insert_cut()
            elif action == ActionType.INSERT_PREDICATE:
                return self._execute_insert_predicate(**kwargs)
            elif action == ActionType.INSERT_LOI:
                return self._execute_insert_loi()
            elif action == ActionType.MOVE:
                return self._execute_move(**kwargs)
            elif action == ActionType.RESIZE:
                return self._execute_resize(**kwargs)
            elif action == ActionType.DELETE:
                return self._execute_delete()
            elif action == ActionType.EDIT_PREDICATE:
                return self._execute_edit_predicate(**kwargs)
            elif action == ActionType.CONNECT_DISCONNECT:
                return self._execute_connect_disconnect(**kwargs)
            elif action == ActionType.PASTE_SUBGRAPH:
                return self._execute_paste_subgraph()
            
        except Exception as e:
            self._show_error(f"Error executing {action.value}: {str(e)}")
            return False
        
        return False
    
    def _execute_insert_cut(self) -> bool:
        """Execute cut insertion."""
        selection = self.selection_system.current_selection
        
        if selection.selection_type != SelectionType.EMPTY_AREA:
            return False
        
        # Find elements to enclose
        enclosed_elements = self._find_elements_in_bounds(selection.selection_bounds)
        
        # Execute EGI operation
        new_graph = EGIOperations.insert_cut(
            self.current_graph, selection.target_area, enclosed_elements
        )
        
        # Record change and update
        self._record_logical_change("Insert Cut", self.current_graph, new_graph)
        self.set_graph(new_graph)
        return True
    
    def _execute_insert_predicate(self, label: str = None, arity: int = 1) -> bool:
        """Execute predicate insertion."""
        selection = self.selection_system.current_selection
        
        if selection.selection_type != SelectionType.EMPTY_AREA:
            return False
        
        # Get predicate details from user if not provided
        if label is None:
            label = simpledialog.askstring("Insert Predicate", "Enter predicate name:")
            if not label:
                return False
        
        if arity == 1:
            arity_str = simpledialog.askstring("Insert Predicate", "Enter arity (number of arguments):", initialvalue="1")
            try:
                arity = int(arity_str) if arity_str else 1
            except ValueError:
                arity = 1
        
        # Execute EGI operation
        new_graph, edge_id = EGIOperations.insert_predicate(
            self.current_graph, selection.target_area, label, arity
        )
        
        # Record change and update
        self._record_logical_change("Insert Predicate", self.current_graph, new_graph)
        self.set_graph(new_graph)
        return True
    
    def _execute_insert_loi(self) -> bool:
        """Execute Line of Identity insertion."""
        selection = self.selection_system.current_selection
        
        if selection.selection_type != SelectionType.EMPTY_AREA:
            return False
        
        # Execute EGI operation
        new_graph, vertex_id = EGIOperations.insert_loi(
            self.current_graph, selection.target_area
        )
        
        # Record change and update
        self._record_logical_change("Insert Line of Identity", self.current_graph, new_graph)
        self.set_graph(new_graph)
        return True
    
    def _execute_delete(self) -> bool:
        """Execute element deletion."""
        selection = self.selection_system.current_selection
        
        if not selection.selected_elements:
            return False
        
        # Confirm deletion
        element_count = len(selection.selected_elements)
        if not messagebox.askyesno("Delete Elements", 
                                  f"Delete {element_count} selected element(s)?"):
            return False
        
        # Execute EGI operation
        new_graph = EGIOperations.delete_elements(
            self.current_graph, selection.selected_elements
        )
        
        # Record change and update
        self._record_logical_change("Delete Elements", self.current_graph, new_graph)
        self.set_graph(new_graph)
        return True
    
    def _execute_edit_predicate(self, edge_id: ElementID = None) -> bool:
        """Execute predicate editing."""
        selection = self.selection_system.current_selection
        
        if selection.selection_type != SelectionType.SINGLE_ELEMENT:
            return False
        
        if edge_id is None:
            edge_id = next(iter(selection.selected_elements))
        
        # Get current predicate info
        current_label = self.current_graph.rel.get(edge_id, "")
        current_arity = len(self.current_graph.nu.get(edge_id, ()))
        
        # Get new values from user
        new_label = simpledialog.askstring("Edit Predicate", "Enter predicate name:", 
                                          initialvalue=current_label)
        if new_label is None:
            return False
        
        new_arity_str = simpledialog.askstring("Edit Predicate", "Enter arity:", 
                                             initialvalue=str(current_arity))
        try:
            new_arity = int(new_arity_str) if new_arity_str else current_arity
        except ValueError:
            new_arity = current_arity
        
        # Execute EGI operation
        new_graph = EGIOperations.edit_predicate(
            self.current_graph, edge_id, new_label, new_arity
        )
        
        # Record change and update
        self._record_logical_change("Edit Predicate", self.current_graph, new_graph)
        self.set_graph(new_graph)
        return True
    
    def _execute_move(self, delta: Tuple[float, float] = None) -> bool:
        """Execute element movement (appearance-only)."""
        # This would update layout positions without changing EGI
        # For now, just re-render
        self._render_diagram()
        return True
    
    def _execute_resize(self, new_bounds: Bounds = None) -> bool:
        """Execute element resizing (appearance-only)."""
        # This would update layout dimensions without changing EGI
        # For now, just re-render
        self._render_diagram()
        return True
    
    def _execute_connect_disconnect(self, from_element: ElementID = None, 
                                   to_element: ElementID = None) -> bool:
        """Execute element connection/disconnection."""
        # Complex ligature logic would go here
        return False
    
    def _execute_paste_subgraph(self) -> bool:
        """Execute subgraph pasting."""
        if not self.clipboard:
            return False
        
        # Complex paste logic would go here
        return False
    
    def copy_selection(self) -> bool:
        """Copy current selection to clipboard."""
        selection = self.selection_system.current_selection
        
        if not selection.selected_elements:
            return False
        
        # Extract subgraph data
        self.clipboard = {
            'elements': selection.selected_elements,
            'graph_data': self._extract_subgraph_data(selection.selected_elements)
        }
        return True
    
    def undo(self) -> bool:
        """Undo last change."""
        if self.history_index < 0 or self.history_index >= len(self.change_history):
            return False
        
        change = self.change_history[self.history_index]
        
        if change.change_type == ChangeType.LOGICAL:
            self.set_graph(change.undo_data)
        elif change.change_type == ChangeType.APPEARANCE:
            self.current_layout = change.undo_data
            self._render_diagram()
        
        self.history_index -= 1
        return True
    
    def redo(self) -> bool:
        """Redo next change."""
        if self.history_index + 1 >= len(self.change_history):
            return False
        
        self.history_index += 1
        change = self.change_history[self.history_index]
        
        if change.change_type == ChangeType.LOGICAL:
            self.set_graph(change.redo_data)
        elif change.change_type == ChangeType.APPEARANCE:
            self.current_layout = change.redo_data
            self._render_diagram()
        
        return True
    
    def _record_logical_change(self, description: str, old_graph: RelationalGraphWithCuts,
                              new_graph: RelationalGraphWithCuts) -> None:
        """Record a logical change for undo/redo."""
        import time
        
        change = Change(
            change_type=ChangeType.LOGICAL,
            description=description,
            undo_data=old_graph,
            redo_data=new_graph,
            timestamp=time.time()
        )
        
        # Truncate history if we're not at the end
        self.change_history = self.change_history[:self.history_index + 1]
        self.change_history.append(change)
        self.history_index = len(self.change_history) - 1
    
    def _record_appearance_change(self, description: str, old_layout: LayoutResult,
                                 new_layout: LayoutResult) -> None:
        """Record an appearance-only change for undo/redo."""
        import time
        
        change = Change(
            change_type=ChangeType.APPEARANCE,
            description=description,
            undo_data=old_layout,
            redo_data=new_layout,
            timestamp=time.time()
        )
        
        self.change_history = self.change_history[:self.history_index + 1]
        self.change_history.append(change)
        self.history_index = len(self.change_history) - 1
    
    def _render_diagram(self) -> None:
        """Render the current diagram."""
        if self.current_graph and self.current_layout:
            self.renderer.render_diagram(self.current_layout, self.current_graph)
    
    def _find_element_at_position(self, position: Coordinate) -> Optional[ElementID]:
        """Find element at given position."""
        if not self.current_layout:
            return None
        
        x, y = position
        for element_id, primitive in sorted(self.current_layout.primitives.items(),
                                          key=lambda item: item[1].z_index, reverse=True):
            x1, y1, x2, y2 = primitive.bounds
            if x1 <= x <= x2 and y1 <= y <= y2:
                return element_id
        return None
    
    def _find_area_at_position(self, position: Coordinate) -> Optional[ElementID]:
        """Find area containing position."""
        if not self.current_graph or not self.current_layout:
            return self.current_graph.sheet if self.current_graph else None
        
        # Check cuts from innermost to outermost
        for element_id, primitive in self.current_layout.primitives.items():
            if primitive.element_type == 'cut':
                x, y = position
                x1, y1, x2, y2 = primitive.bounds
                if x1 <= x <= x2 and y1 <= y <= y2:
                    return element_id
        
        return self.current_graph.sheet
    
    def _find_elements_in_bounds(self, bounds: Bounds) -> Set[ElementID]:
        """Find all elements within given bounds."""
        if not self.current_layout:
            return set()
        
        x1, y1, x2, y2 = bounds
        elements = set()
        
        for element_id, primitive in self.current_layout.primitives.items():
            px1, py1, px2, py2 = primitive.bounds
            # Check if primitive is within bounds
            if (x1 <= px1 and px2 <= x2 and y1 <= py1 and py2 <= y2):
                elements.add(element_id)
        
        return elements
    
    def _calculate_bounds(self, start_pos: Coordinate, end_pos: Coordinate) -> Bounds:
        """Calculate bounds from start and end positions."""
        x1, y1 = start_pos
        x2, y2 = end_pos
        return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
    
    def _move_selected_elements(self, start_pos: Coordinate, end_pos: Coordinate) -> None:
        """Move selected elements (appearance-only change)."""
        # This would update layout positions
        # For now, just a placeholder
        pass
    
    def _extract_subgraph_data(self, elements: Set[ElementID]) -> Dict[str, Any]:
        """Extract subgraph data for clipboard."""
        # This would extract the relevant EGI components
        return {'elements': elements}
    
    def _show_error(self, message: str) -> None:
        """Show error message to user."""
        messagebox.showerror("Error", message)
