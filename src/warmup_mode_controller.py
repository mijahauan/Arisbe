#!/usr/bin/env python3
"""
Warmup Mode Controller

Enhanced direct manipulation interface for compositional EG editing.
Provides relaxed, creative editing with syntactic validation only.

Features:
- Direct element manipulation (drag, resize, edit)
- Intuitive interaction patterns
- Real-time syntactic validation
- User-invoked semantic feedback
- Undo/redo with state preservation
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
from typing import Optional, Set, Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from egi_core_dau import (
    RelationalGraphWithCuts, Vertex, Edge, Cut,
    create_empty_graph, create_vertex, create_edge, create_cut,
    ElementID, VertexSequence, RelationName
)
from egif_parser_dau import EGIFParser
from egif_generator_dau import EGIFGenerator
from layout_engine import LayoutEngine
from diagram_renderer_clean import CleanDiagramRenderer
from tkinter_backend import TkinterCanvas


class InteractionMode(Enum):
    """Current interaction mode."""
    SELECT = "select"
    ADD_PREDICATE = "add_predicate"
    ADD_VERTEX = "add_vertex"
    ADD_CUT = "add_cut"
    CONNECT = "connect"


@dataclass
class ElementLayout:
    """Layout information for a graph element."""
    element_id: ElementID
    x: float
    y: float
    width: float
    height: float
    element_type: str  # 'vertex', 'edge', 'cut'


class WarmupModeController:
    """
    Enhanced controller for Warmup mode editing.
    
    Provides direct manipulation interface with:
    - Click to select elements
    - Drag to move elements
    - Right-click for context menus
    - Keyboard shortcuts for actions
    - Real-time visual feedback
    """
    
    def __init__(self, canvas: TkinterCanvas, layout_engine: LayoutEngine):
        """Initialize warmup mode controller."""
        self.canvas = canvas
        self.layout_engine = layout_engine
        self.renderer = CleanDiagramRenderer(canvas)
        
        # Graph state
        self.graph: Optional[RelationalGraphWithCuts] = None
        self.element_layouts: Dict[ElementID, ElementLayout] = {}
        
        # Interaction state
        self.mode = InteractionMode.SELECT
        self.selected_elements: Set[ElementID] = set()
        self.drag_start: Optional[Tuple[float, float]] = None
        self.drag_element: Optional[ElementID] = None
        
        # Undo/redo
        self.undo_stack: List[RelationalGraphWithCuts] = []
        self.redo_stack: List[RelationalGraphWithCuts] = []
        
        # Callbacks
        self.on_graph_changed: Optional[callable] = None
        self.on_selection_changed: Optional[callable] = None
        self.on_status_update: Optional[callable] = None
        
        # Bind canvas events
        self._bind_events()
    
    def _bind_events(self):
        """Bind canvas interaction events."""
        # Use standard Tkinter canvas event binding
        if hasattr(self.canvas, 'tk_canvas'):
            tk_canvas = self.canvas.tk_canvas
            
            # Mouse events
            tk_canvas.bind('<Button-1>', self._on_tk_click)
            tk_canvas.bind('<B1-Motion>', self._on_tk_drag)
            tk_canvas.bind('<ButtonRelease-1>', self._on_tk_release)
            tk_canvas.bind('<Button-3>', self._on_tk_right_click)  # Right click
            tk_canvas.bind('<Double-Button-1>', self._on_tk_double_click)
            
            # Keyboard events
            tk_canvas.bind('<Delete>', self._on_tk_delete_key)
            tk_canvas.bind('<Control-z>', self._on_tk_undo_key)
            tk_canvas.bind('<Control-y>', self._on_tk_redo_key)
            tk_canvas.bind('<Control-a>', self._on_tk_select_all_key)
            
            # Make canvas focusable for keyboard events
            tk_canvas.focus_set()
    
    def set_graph(self, graph: RelationalGraphWithCuts):
        """Set the current graph and update display."""
        self.graph = graph
        self._update_layout()
        self._render_graph()
        
        if self.on_graph_changed:
            self.on_graph_changed(graph)
    
    def _update_layout(self):
        """Update element layout information."""
        if not self.graph:
            return
        
        # Use layout engine
        layout_result = self.layout_engine.layout_graph(self.graph)
        
        # Store layout information for interaction
        self.element_layouts.clear()
        
        # Add vertices
        for vertex in self.graph.V:
            vertex_id = vertex.id
            if vertex_id in layout_result.primitives:
                layout_elem = layout_result.primitives[vertex_id]
                self.element_layouts[vertex_id] = ElementLayout(
                    element_id=vertex_id,
                    x=layout_elem.position[0], y=layout_elem.position[1],
                    width=20, height=20,  # Default vertex size
                    element_type='vertex'
                )
        
        # Add edges
        for edge in self.graph.E:
            edge_id = edge.id
            if edge_id in layout_result.primitives:
                layout_elem = layout_result.primitives[edge_id]
                self.element_layouts[edge_id] = ElementLayout(
                    element_id=edge_id,
                    x=layout_elem.position[0], y=layout_elem.position[1],
                    width=80, height=30,  # Default predicate size
                    element_type='edge'
                )
        
        # Add cuts
        for cut in self.graph.Cut:
            cut_id = cut.id
            if cut_id in layout_result.primitives:
                layout_elem = layout_result.primitives[cut_id]
                self.element_layouts[cut_id] = ElementLayout(
                    element_id=cut_id,
                    x=layout_elem.position[0], y=layout_elem.position[1],
                    width=layout_elem.bounds[2] - layout_elem.bounds[0], height=layout_elem.bounds[3] - layout_elem.bounds[1],
                    element_type='cut'
                )
    
    def _render_graph(self):
        """Render the current graph to canvas."""
        if not self.graph:
            return
        
        # Clear canvas
        self.canvas.clear()
        
        # Generate layout first
        layout_result = self.layout_engine.layout_graph(self.graph)
        
        # Use renderer to draw graph with correct parameters
        self.renderer.render_diagram(layout_result, self.graph)
        
        # Highlight selected elements
        self._highlight_selection()
    
    def _highlight_selection(self):
        """Highlight selected elements."""
        for element_id in self.selected_elements:
            if element_id in self.element_layouts:
                layout = self.element_layouts[element_id]
                # Draw selection highlight
                self.canvas.draw_rectangle(
                    layout.x - 2, layout.y - 2,
                    layout.width + 4, layout.height + 4,
                    outline_color="blue", outline_width=2, fill_color=None
                )
    
    def _find_element_at_position(self, x: float, y: float) -> Optional[ElementID]:
        """Find element at given canvas position."""
        for element_id, layout in self.element_layouts.items():
            if (layout.x <= x <= layout.x + layout.width and
                layout.y <= y <= layout.y + layout.height):
                return element_id
        return None
    
    def _save_state(self):
        """Save current graph state for undo."""
        if self.graph:
            # Deep copy the graph for undo stack
            self.undo_stack.append(self.graph)
            self.redo_stack.clear()  # Clear redo stack on new action
            
            # Limit undo stack size
            if len(self.undo_stack) > 50:
                self.undo_stack.pop(0)
    
    # Event handlers
    def _on_click(self, x: float, y: float):
        """Handle canvas click."""
        element_id = self._find_element_at_position(x, y)
        
        if self.mode == InteractionMode.SELECT:
            if element_id:
                # Select element
                self.selected_elements = {element_id}
                self.drag_element = element_id
                self.drag_start = (x, y)
            else:
                # Clear selection on empty click
                self.selected_elements.clear()
                self.drag_element = None
            
            self._update_selection()
            self._render_graph()
        
        elif self.mode == InteractionMode.ADD_PREDICATE:
            self._add_predicate_at_position(x, y)
        
        elif self.mode == InteractionMode.ADD_VERTEX:
            self._add_vertex_at_position(x, y)
        
        elif self.mode == InteractionMode.ADD_CUT:
            self._add_cut_at_position(x, y)
    
    def _on_drag(self, x: float, y: float):
        """Handle canvas drag."""
        if self.mode == InteractionMode.SELECT and self.drag_element and self.drag_start:
            # Move selected element
            dx = x - self.drag_start[0]
            dy = y - self.drag_start[1]
            
            # Update element position (this would need layout engine integration)
            if self.drag_element in self.element_layouts:
                layout = self.element_layouts[self.drag_element]
                layout.x += dx
                layout.y += dy
                
                self.drag_start = (x, y)
                self._render_graph()
    
    def _on_release(self, x: float, y: float):
        """Handle canvas release."""
        if self.drag_element:
            # Finalize element move
            self._save_state()
            self.drag_element = None
            self.drag_start = None
    
    def _on_right_click(self, x: float, y: float):
        """Handle right-click for context menu."""
        element_id = self._find_element_at_position(x, y)
        
        if element_id:
            self._show_element_context_menu(element_id, x, y)
        else:
            self._show_canvas_context_menu(x, y)
    
    def _on_double_click(self, x: float, y: float):
        """Handle double-click for element editing."""
        element_id = self._find_element_at_position(x, y)
        
        if element_id:
            self._edit_element(element_id)
    
    def _on_delete_key(self):
        """Handle delete key."""
        if self.selected_elements:
            self._delete_selected()
    
    def _on_undo_key(self):
        """Handle undo key."""
        self.undo()
    
    def _on_redo_key(self):
        """Handle redo key."""
        self.redo()
    
    def _on_select_all_key(self):
        """Handle select all key."""
        self.select_all()
    
    # Tkinter event handler wrappers
    def _on_tk_click(self, event):
        """Handle Tkinter click event."""
        self._on_click(event.x, event.y)
    
    def _on_tk_drag(self, event):
        """Handle Tkinter drag event."""
        self._on_drag(event.x, event.y)
    
    def _on_tk_release(self, event):
        """Handle Tkinter release event."""
        self._on_release(event.x, event.y)
    
    def _on_tk_right_click(self, event):
        """Handle Tkinter right click event."""
        self._on_right_click(event.x, event.y)
    
    def _on_tk_double_click(self, event):
        """Handle Tkinter double click event."""
        self._on_double_click(event.x, event.y)
    
    def _on_tk_delete_key(self, event):
        """Handle Tkinter delete key event."""
        self._on_delete_key()
    
    def _on_tk_undo_key(self, event):
        """Handle Tkinter undo key event."""
        self._on_undo_key()
    
    def _on_tk_redo_key(self, event):
        """Handle Tkinter redo key event."""
        self._on_redo_key()
    
    def _on_tk_select_all_key(self, event):
        """Handle Tkinter select all key event."""
        self._on_select_all_key()
    
    # Action methods
    def _add_predicate_at_position(self, x: float, y: float):
        """Add predicate at given position."""
        if not self.graph:
            return
        
        name = simpledialog.askstring("Add Predicate", "Predicate name:")
        if name:
            self._save_state()
            
            # Create new predicate (edge)
            vertex_id = create_vertex(self.graph)
            edge_id = create_edge(self.graph, name, [vertex_id])
            
            # Update layout and render
            self._update_layout()
            self._render_graph()
            
            if self.on_status_update:
                self.on_status_update(f"Added predicate: {name}")
    
    def _add_vertex_at_position(self, x: float, y: float):
        """Add vertex at given position."""
        if not self.graph:
            return
        
        self._save_state()
        
        # Create new vertex
        vertex_id = create_vertex(self.graph)
        
        # Update layout and render
        self._update_layout()
        self._render_graph()
        
        if self.on_status_update:
            self.on_status_update("Added vertex")
    
    def _add_cut_at_position(self, x: float, y: float):
        """Add cut at given position."""
        if not self.graph:
            return
        
        self._save_state()
        
        # Create new cut
        cut_id = create_cut(self.graph)
        
        # Update layout and render
        self._update_layout()
        self._render_graph()
        
        if self.on_status_update:
            self.on_status_update("Added cut")
    
    def _delete_selected(self):
        """Delete selected elements."""
        if not self.selected_elements or not self.graph:
            return
        
        self._save_state()
        
        # Delete selected elements from graph
        for element_id in self.selected_elements:
            if element_id in {v.id for v in self.graph.V}:
                # Note: RelationalGraphWithCuts is immutable, use without_element instead
                self.graph = self.graph.without_element(element_id)
            elif element_id in {e.id for e in self.graph.E}:
                self.graph = self.graph.without_element(element_id)
            elif element_id in {c.id for c in self.graph.Cut}:
                self.graph = self.graph.without_element(element_id)
        
        self.selected_elements.clear()
        
        # Update layout and render
        self._update_layout()
        self._render_graph()
        self._update_selection()
        
        if self.on_status_update:
            self.on_status_update("Deleted selected elements")
    
    def _edit_element(self, element_id: ElementID):
        """Edit element properties."""
        if not self.graph:
            return
        
        if element_id in self.graph.edges:
            # Edit predicate name
            edge = self.graph.edges[element_id]
            current_name = edge.relation_name
            new_name = simpledialog.askstring("Edit Predicate", 
                                             f"Predicate name:", 
                                             initialvalue=current_name)
            if new_name and new_name != current_name:
                self._save_state()
                edge.relation_name = new_name
                self._render_graph()
                
                if self.on_status_update:
                    self.on_status_update(f"Renamed predicate to: {new_name}")
    
    def _show_element_context_menu(self, element_id: ElementID, x: float, y: float):
        """Show context menu for element."""
        # This would show a popup menu with element-specific actions
        # For now, just select the element
        self.selected_elements = {element_id}
        self._update_selection()
        self._render_graph()
    
    def _show_canvas_context_menu(self, x: float, y: float):
        """Show context menu for empty canvas area."""
        # This would show a popup menu with canvas actions
        pass
    
    def _update_selection(self):
        """Update selection and notify callbacks."""
        if self.on_selection_changed:
            self.on_selection_changed(self.selected_elements)
    
    # Public interface methods
    def set_mode(self, mode: InteractionMode):
        """Set interaction mode."""
        self.mode = mode
        
        if self.on_status_update:
            mode_names = {
                InteractionMode.SELECT: "Select mode",
                InteractionMode.ADD_PREDICATE: "Add predicate mode",
                InteractionMode.ADD_VERTEX: "Add vertex mode", 
                InteractionMode.ADD_CUT: "Add cut mode",
                InteractionMode.CONNECT: "Connect mode"
            }
            self.on_status_update(mode_names.get(mode, "Unknown mode"))
    
    def select_all(self):
        """Select all elements."""
        if self.graph:
            self.selected_elements = {v.id for v in self.graph.V}
            self.selected_elements.update({e.id for e in self.graph.E})
            self.selected_elements.update({c.id for c in self.graph.Cut})
            
            self._update_selection()
            self._render_graph()
    
    def clear_selection(self):
        """Clear selection."""
        self.selected_elements.clear()
        self._update_selection()
        self._render_graph()
    
    def undo(self):
        """Undo last action."""
        if self.undo_stack:
            # Save current state to redo stack
            if self.graph:
                self.redo_stack.append(self.graph)
            
            # Restore previous state
            self.graph = self.undo_stack.pop()
            self._update_layout()
            self._render_graph()
            
            if self.on_graph_changed:
                self.on_graph_changed(self.graph)
            
            if self.on_status_update:
                self.on_status_update("Undone")
    
    def redo(self):
        """Redo last undone action."""
        if self.redo_stack:
            # Save current state to undo stack
            if self.graph:
                self.undo_stack.append(self.graph)
            
            # Restore next state
            self.graph = self.redo_stack.pop()
            self._update_layout()
            self._render_graph()
            
            if self.on_graph_changed:
                self.on_graph_changed(self.graph)
            
            if self.on_status_update:
                self.on_status_update("Redone")
    
    def get_selected_elements(self) -> Set[ElementID]:
        """Get currently selected elements."""
        return self.selected_elements.copy()
    
    def validate_syntax(self) -> List[str]:
        """Validate current graph syntax using the Dau API."""
        if not self.graph:
            return ["No graph loaded"]

        issues = []
        all_vertex_ids = {v.id for v in self.graph.V}

        # Check for isolated (orphaned) vertices.
        # Note: In Dau's formalism, isolated vertices are syntactically valid.
        # We flag them here as a potential user-level issue.
        referenced_vertices = {v_id for v_seq in self.graph.nu.values() for v_id in v_seq}
        isolated_vertices = all_vertex_ids - referenced_vertices
        for vertex_id in isolated_vertices:
            issues.append(f"Syntactic Warning: Isolated vertex found: {vertex_id}")

        # Check for edges referencing non-existent vertices
        for edge_id, vertex_sequence in self.graph.nu.items():
            for vertex_id in vertex_sequence:
                if vertex_id not in all_vertex_ids:
                    issues.append(f"Syntax Error: Edge {edge_id} references non-existent vertex {vertex_id}")
        
        return issues


if __name__ == "__main__":
    # Test the warmup mode controller
    print("=== Testing Warmup Mode Controller ===")
    
    # This would normally be integrated with the main application
    print("Warmup mode controller ready for integration")
