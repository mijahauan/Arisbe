#!/usr/bin/env python3
"""
Phase 2 Enhanced Demonstration: Professional EG Editor

Comprehensive demonstration of the enhanced interactive layer:
- Selection object with contextual overlays
- Context-sensitive actions mapped to EGI rules
- Dynamic visual feedback and rule enforcement
- Clear distinction between logical and appearance-only changes
- Professional interaction patterns
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from tkinter import ttk, messagebox
from egif_parser_dau import EGIFParser
from layout_engine_clean import CleanLayoutEngine
from diagram_renderer_clean import CleanDiagramRenderer
from tkinter_backend import TkinterCanvas
from diagram_controller_enhanced import EnhancedDiagramController, ActionType
from selection_system_enhanced import SelectionType


class Phase2EnhancedDemo:
    """
    Comprehensive demonstration of Phase 2 enhanced features.
    
    Shows professional-grade EG editor with:
    - Contextual selection overlays
    - Action-first workflow with validation
    - Logical vs. appearance-only operations
    - Undo/redo functionality
    - Rule enforcement and error feedback
    """
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Phase 2 Enhanced: Professional EG Editor")
        self.root.geometry("1200x800")
        
        # Create UI
        self._create_ui()
        
        # Initialize enhanced controller
        self.layout_engine = CleanLayoutEngine()
        self.renderer = CleanDiagramRenderer(self.canvas)
        self.controller = EnhancedDiagramController(self.canvas, self.layout_engine, self.renderer)
        
        # Set up callbacks
        self.controller.on_graph_changed = self._on_graph_changed
        self.controller.on_layout_changed = self._on_layout_changed
        
        # Bind events
        self._bind_events()
        
        # Load initial case
        self._load_test_case()
    
    def _create_ui(self):
        """Create the professional UI layout."""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top toolbar
        self._create_toolbar(main_frame)
        
        # Main content area
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Left panel - Actions and Properties
        self._create_left_panel(content_frame)
        
        # Center - Canvas
        self._create_canvas_area(content_frame)
        
        # Right panel - History and Info
        self._create_right_panel(content_frame)
        
        # Bottom status bar
        self._create_status_bar(main_frame)
    
    def _create_toolbar(self, parent):
        """Create the main toolbar."""
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X)
        
        # File operations
        file_frame = ttk.LabelFrame(toolbar, text="File")
        file_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(file_frame, text="New", command=self._new_graph).pack(side=tk.LEFT, padx=2)
        ttk.Button(file_frame, text="Open", command=self._open_graph).pack(side=tk.LEFT, padx=2)
        ttk.Button(file_frame, text="Save", command=self._save_graph).pack(side=tk.LEFT, padx=2)
        
        # Edit operations
        edit_frame = ttk.LabelFrame(toolbar, text="Edit")
        edit_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        self.undo_btn = ttk.Button(edit_frame, text="Undo", command=self._undo, state=tk.DISABLED)
        self.undo_btn.pack(side=tk.LEFT, padx=2)
        
        self.redo_btn = ttk.Button(edit_frame, text="Redo", command=self._redo, state=tk.DISABLED)
        self.redo_btn.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(edit_frame, text="Copy", command=self._copy).pack(side=tk.LEFT, padx=2)
        ttk.Button(edit_frame, text="Paste", command=self._paste).pack(side=tk.LEFT, padx=2)
        
        # Test cases
        test_frame = ttk.LabelFrame(toolbar, text="Test Cases")
        test_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        self.case_var = tk.StringVar()
        case_combo = ttk.Combobox(test_frame, textvariable=self.case_var, width=35)
        case_combo['values'] = [
            '(Human "Socrates") ~[ (Mortal "Socrates") ]',
            '*x ~[ (Human x) (Mortal x) ]',
            '*x (Human x) ~[ (Mortal x) (Wise x) ]',
            '*x *y (Human x) (Loves x y) ~[ (Mortal y) ]',
            '*x *y *z (Human x) (Loves x y) ~[ (Mortal y) (Wise z) ]'
        ]
        case_combo.set(case_combo['values'][0])
        case_combo.pack(padx=5, pady=2)
        case_combo.bind('<<ComboboxSelected>>', self._on_case_change)
    
    def _create_left_panel(self, parent):
        """Create the left action panel."""
        left_frame = ttk.Frame(parent, width=200)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_frame.pack_propagate(False)
        
        # Insert Actions
        insert_frame = ttk.LabelFrame(left_frame, text="Insert Actions")
        insert_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(insert_frame, text="Insert Cut", 
                  command=lambda: self._execute_action(ActionType.INSERT_CUT)).pack(fill=tk.X, pady=2)
        ttk.Button(insert_frame, text="Insert Predicate", 
                  command=lambda: self._execute_action(ActionType.INSERT_PREDICATE)).pack(fill=tk.X, pady=2)
        ttk.Button(insert_frame, text="Insert LoI", 
                  command=lambda: self._execute_action(ActionType.INSERT_LOI)).pack(fill=tk.X, pady=2)
        
        # Modify Actions
        modify_frame = ttk.LabelFrame(left_frame, text="Modify Actions")
        modify_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(modify_frame, text="Move", 
                  command=lambda: self._execute_action(ActionType.MOVE)).pack(fill=tk.X, pady=2)
        ttk.Button(modify_frame, text="Resize", 
                  command=lambda: self._execute_action(ActionType.RESIZE)).pack(fill=tk.X, pady=2)
        ttk.Button(modify_frame, text="Edit Predicate", 
                  command=lambda: self._execute_action(ActionType.EDIT_PREDICATE)).pack(fill=tk.X, pady=2)
        ttk.Button(modify_frame, text="Connect/Disconnect", 
                  command=lambda: self._execute_action(ActionType.CONNECT_DISCONNECT)).pack(fill=tk.X, pady=2)
        
        # Delete Actions
        delete_frame = ttk.LabelFrame(left_frame, text="Delete Actions")
        delete_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(delete_frame, text="Delete Selection", 
                  command=lambda: self._execute_action(ActionType.DELETE)).pack(fill=tk.X, pady=2)
        
        # Selection Info
        self.selection_frame = ttk.LabelFrame(left_frame, text="Selection Info")
        self.selection_frame.pack(fill=tk.BOTH, expand=True)
        
        self.selection_info = tk.Text(self.selection_frame, height=8, wrap=tk.WORD)
        self.selection_info.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Available Actions
        self.actions_frame = ttk.LabelFrame(left_frame, text="Available Actions")
        self.actions_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.actions_text = tk.Text(self.actions_frame, height=4, wrap=tk.WORD)
        self.actions_text.pack(fill=tk.X, padx=5, pady=5)
    
    def _create_canvas_area(self, parent):
        """Create the main canvas area."""
        canvas_frame = ttk.LabelFrame(parent, text="Existential Graph Canvas")
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Canvas with scrollbars
        canvas_container = ttk.Frame(canvas_frame)
        canvas_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.canvas = TkinterCanvas(width=700, height=500, master=canvas_container)
        
        # Instructions overlay
        instructions = ttk.Label(canvas_container, 
            text="• Click elements to select (Ctrl+click for multi-select)\n"
                 "• Drag empty areas for area selection\n"
                 "• Use action buttons on left to perform operations\n"
                 "• Blue overlays show selection with context handles",
            justify=tk.LEFT, font=('Arial', 9))
        instructions.pack(pady=(5, 0))
    
    def _create_right_panel(self, parent):
        """Create the right info panel."""
        right_frame = ttk.Frame(parent, width=200)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        right_frame.pack_propagate(False)
        
        # Graph Structure
        structure_frame = ttk.LabelFrame(right_frame, text="Graph Structure")
        structure_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.structure_text = tk.Text(structure_frame, height=8, wrap=tk.WORD, font=('Courier', 9))
        self.structure_text.pack(fill=tk.X, padx=5, pady=5)
        
        # Change History
        history_frame = ttk.LabelFrame(right_frame, text="Change History")
        history_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.history_listbox = tk.Listbox(history_frame, font=('Arial', 9))
        self.history_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Validation Messages
        validation_frame = ttk.LabelFrame(right_frame, text="Validation")
        validation_frame.pack(fill=tk.X)
        
        self.validation_text = tk.Text(validation_frame, height=4, wrap=tk.WORD, font=('Arial', 9))
        self.validation_text.pack(fill=tk.X, padx=5, pady=5)
    
    def _create_status_bar(self, parent):
        """Create the status bar."""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_var = tk.StringVar(value="Ready - Professional EG Editor")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.pack(side=tk.LEFT)
        
        # Mode indicator
        self.mode_var = tk.StringVar(value="Syntactic Mode")
        mode_label = ttk.Label(status_frame, textvariable=self.mode_var, font=('Arial', 9, 'bold'))
        mode_label.pack(side=tk.RIGHT)
    
    def _bind_events(self):
        """Bind canvas events."""
        self.canvas.tk_canvas.bind("<Button-1>", self._on_click)
        self.canvas.tk_canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.tk_canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.tk_canvas.bind("<Motion>", self._on_hover)
        self.canvas.tk_canvas.bind("<Double-Button-1>", self._on_double_click)
        
        # Keyboard shortcuts
        self.root.bind("<Control-z>", lambda e: self._undo())
        self.root.bind("<Control-y>", lambda e: self._redo())
        self.root.bind("<Control-c>", lambda e: self._copy())
        self.root.bind("<Control-v>", lambda e: self._paste())
        self.root.bind("<Delete>", lambda e: self._execute_action(ActionType.DELETE))
        self.root.bind("<Escape>", lambda e: self._clear_selection())
        
        self.root.focus_set()
    
    def _on_click(self, event):
        """Handle mouse click."""
        position = (event.x, event.y)
        modifiers = set()
        if event.state & 0x4:  # Control
            modifiers.add('ctrl')
        if event.state & 0x8:  # Alt
            modifiers.add('alt')
        if event.state & 0x1:  # Shift
            modifiers.add('shift')
        
        self.drag_start = position
        self.controller.handle_click(position, modifiers)
        self._update_ui()
    
    def _on_drag(self, event):
        """Handle mouse drag."""
        if hasattr(self, 'drag_start'):
            end_position = (event.x, event.y)
            self.controller.handle_drag(self.drag_start, end_position)
            self._update_ui()
    
    def _on_release(self, event):
        """Handle mouse release."""
        if hasattr(self, 'drag_start'):
            delattr(self, 'drag_start')
    
    def _on_hover(self, event):
        """Handle mouse hover."""
        # Could add hover effects here
        pass
    
    def _on_double_click(self, event):
        """Handle double-click for quick actions."""
        position = (event.x, event.y)
        # Could trigger edit actions for double-clicked elements
        pass
    
    def _execute_action(self, action: ActionType):
        """Execute an action with validation."""
        success = self.controller.execute_action(action)
        if success:
            self.status_var.set(f"Executed: {action.value}")
        else:
            self.status_var.set(f"Failed: {action.value}")
        self._update_ui()
    
    def _load_test_case(self):
        """Load selected test case."""
        egif_string = self.case_var.get()
        if not egif_string:
            return
        
        try:
            parser = EGIFParser(egif_string)
            graph = parser.parse()
            self.controller.set_graph(graph)
            self.status_var.set(f"Loaded: {egif_string}")
            self._update_ui()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load case: {e}")
    
    def _on_case_change(self, event=None):
        """Handle test case change."""
        self._load_test_case()
    
    def _on_graph_changed(self, graph):
        """Handle graph changes."""
        self._update_structure_display()
        self._update_history_display()
    
    def _on_layout_changed(self, layout):
        """Handle layout changes."""
        pass
    
    def _update_ui(self):
        """Update all UI components."""
        self._update_selection_info()
        self._update_available_actions()
        self._update_validation_display()
        self._update_undo_redo_buttons()
    
    def _update_selection_info(self):
        """Update selection information display."""
        selection = self.controller.selection_system.current_selection
        
        info = f"Type: {selection.selection_type.value}\n"
        info += f"Elements: {len(selection.selected_elements)}\n"
        
        if selection.selected_elements:
            info += "Selected IDs:\n"
            for element_id in list(selection.selected_elements)[:5]:  # Show first 5
                info += f"  {element_id[-8:]}\n"
            if len(selection.selected_elements) > 5:
                info += f"  ... and {len(selection.selected_elements) - 5} more\n"
        
        if selection.selection_bounds:
            x1, y1, x2, y2 = selection.selection_bounds
            info += f"Bounds: ({x1:.0f}, {y1:.0f}) to ({x2:.0f}, {y2:.0f})\n"
        
        if selection.target_area:
            info += f"Target Area: {selection.target_area[-8:]}\n"
        
        self.selection_info.delete(1.0, tk.END)
        self.selection_info.insert(1.0, info)
    
    def _update_available_actions(self):
        """Update available actions display."""
        actions = self.controller.selection_system.get_available_actions()
        
        if actions:
            actions_text = "Available actions:\n"
            for action in actions:
                actions_text += f"• {action.value.replace('_', ' ').title()}\n"
        else:
            actions_text = "No actions available\nSelect elements or empty area"
        
        self.actions_text.delete(1.0, tk.END)
        self.actions_text.insert(1.0, actions_text)
    
    def _update_structure_display(self):
        """Update graph structure display."""
        if not self.controller.current_graph:
            return
        
        graph = self.controller.current_graph
        
        structure = f"Vertices: {len(graph.V)}\n"
        structure += f"Edges: {len(graph.E)}\n"
        structure += f"Cuts: {len(graph.Cut)}\n\n"
        
        structure += "Relations:\n"
        for edge_id, relation in list(graph.rel.items())[:5]:
            structure += f"  {relation}\n"
        
        if len(graph.rel) > 5:
            structure += f"  ... and {len(graph.rel) - 5} more\n"
        
        self.structure_text.delete(1.0, tk.END)
        self.structure_text.insert(1.0, structure)
    
    def _update_history_display(self):
        """Update change history display."""
        self.history_listbox.delete(0, tk.END)
        
        for i, change in enumerate(self.controller.change_history):
            marker = "→" if i == self.controller.history_index else " "
            entry = f"{marker} {change.description} ({change.change_type.value})"
            self.history_listbox.insert(tk.END, entry)
    
    def _update_validation_display(self):
        """Update validation messages."""
        selection = self.controller.selection_system.current_selection
        
        if selection.is_valid:
            message = "✓ Selection is valid"
        else:
            message = f"✗ {selection.validation_message or 'Invalid selection'}"
        
        self.validation_text.delete(1.0, tk.END)
        self.validation_text.insert(1.0, message)
    
    def _update_undo_redo_buttons(self):
        """Update undo/redo button states."""
        can_undo = self.controller.history_index >= 0
        can_redo = self.controller.history_index + 1 < len(self.controller.change_history)
        
        self.undo_btn.config(state=tk.NORMAL if can_undo else tk.DISABLED)
        self.redo_btn.config(state=tk.NORMAL if can_redo else tk.DISABLED)
    
    def _undo(self):
        """Undo last change."""
        if self.controller.undo():
            self.status_var.set("Undone")
            self._update_ui()
    
    def _redo(self):
        """Redo next change."""
        if self.controller.redo():
            self.status_var.set("Redone")
            self._update_ui()
    
    def _copy(self):
        """Copy selection."""
        if self.controller.copy_selection():
            self.status_var.set("Copied to clipboard")
    
    def _paste(self):
        """Paste from clipboard."""
        self._execute_action(ActionType.PASTE_SUBGRAPH)
    
    def _clear_selection(self):
        """Clear current selection."""
        self.controller.selection_system.clear_selection()
        self._update_ui()
    
    # Placeholder methods for file operations
    def _new_graph(self): pass
    def _open_graph(self): pass
    def _save_graph(self): pass
    
    def run(self):
        """Run the enhanced demonstration."""
        print("Starting Phase 2 Enhanced Demonstration...")
        print("Features:")
        print("- Professional EG editor interface")
        print("- Contextual selection overlays")
        print("- Context-sensitive actions with validation")
        print("- Logical vs. appearance-only operations")
        print("- Undo/redo functionality")
        print("- Rule enforcement and error feedback")
        print("- Real-time graph structure display")
        print()
        
        self.root.mainloop()


if __name__ == "__main__":
    demo = Phase2EnhancedDemo()
    demo.run()
