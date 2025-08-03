#!/usr/bin/env python3
"""
Phase 2 Demonstration: Selection Overlays and Interactive Effects

Demonstrates the new Interaction Controller with:
- Element selection with visual overlays
- Cut resize handles
- Vertex and predicate highlighting
- Action-first workflow
- Professional interaction patterns
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from tkinter import ttk
from egif_parser_dau import EGIFParser
from layout_engine_clean import CleanLayoutEngine
from diagram_renderer_clean import CleanDiagramRenderer
from canvas_backends.tkinter_backend import TkinterCanvas
from interaction_controller import InteractionController, ActionMode


class Phase2Demo:
    """Demonstration of Phase 2 selection and interaction features."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Phase 2: Selection Overlays & Interactive Effects")
        self.root.geometry("1000x700")
        
        # Create main layout
        self._create_ui()
        
        # Initialize components
        self.layout_engine = CleanLayoutEngine()
        self.renderer = CleanDiagramRenderer(self.canvas)
        self.controller = InteractionController(self.canvas, self.layout_engine, self.renderer)
        
        # Bind events
        self._bind_events()
        
        # Load initial test case
        self._load_test_case()
    
    def _create_ui(self):
        """Create the user interface."""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Toolbar
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        # Action mode buttons
        ttk.Label(toolbar, text="Action Mode:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.mode_var = tk.StringVar(value="normal")
        modes = [
            ("Normal", "normal"),
            ("Add Cut", "add_cut"),
            ("Add Individual", "add_individual"),
            ("Add Predicate", "add_predicate"),
            ("Move", "move"),
            ("Delete", "delete")
        ]
        
        for text, mode in modes:
            btn = ttk.Radiobutton(toolbar, text=text, variable=self.mode_var, 
                                value=mode, command=self._on_mode_change)
            btn.pack(side=tk.LEFT, padx=5)
        
        # Test case selector
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
        ttk.Label(toolbar, text="Test Case:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.case_var = tk.StringVar()
        case_combo = ttk.Combobox(toolbar, textvariable=self.case_var, width=30)
        case_combo['values'] = [
            '(Human "Socrates") ~[ (Mortal "Socrates") ]',
            '*x ~[ (Human x) (Mortal x) ]',
            '*x (Human x) ~[ (Mortal x) (Wise x) ]',
            '*x *y (Human x) (Loves x y) ~[ (Mortal y) ]'
        ]
        case_combo.set(case_combo['values'][0])
        case_combo.pack(side=tk.LEFT, padx=5)
        case_combo.bind('<<ComboboxSelected>>', self._on_case_change)
        
        # Canvas frame
        canvas_frame = ttk.LabelFrame(main_frame, text="Existential Graph Canvas")
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas
        self.canvas = TkinterCanvas(canvas_frame, width=950, height=500)
        
        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_var = tk.StringVar(value="Ready - Click elements to select, drag to area-select")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.pack(side=tk.LEFT)
        
        # Instructions
        instructions = ttk.LabelFrame(main_frame, text="Instructions")
        instructions.pack(fill=tk.X, pady=(10, 0))
        
        instruction_text = """
• Normal Mode: Click elements to select (Ctrl/Cmd+click for multi-select), drag for area selection
• Selection shows visual overlays: cuts get resize handles, vertices/predicates get highlights
• Try different action modes to see how the workflow changes
• Hover over elements to see hover effects
• Use Escape to cancel actions, Delete key for deletion
        """.strip()
        
        ttk.Label(instructions, text=instruction_text, justify=tk.LEFT).pack(padx=10, pady=5)
    
    def _bind_events(self):
        """Bind canvas events to the interaction controller."""
        # Mouse events
        self.canvas.canvas.bind("<Button-1>", self._on_click)
        self.canvas.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.canvas.bind("<Motion>", self._on_hover)
        
        # Keyboard events
        self.root.bind("<Key>", self._on_key)
        self.root.focus_set()  # Enable keyboard events
    
    def _on_click(self, event):
        """Handle mouse click."""
        position = (event.x, event.y)
        modifiers = set()
        if event.state & 0x4:  # Control key
            modifiers.add('ctrl')
        if event.state & 0x8:  # Alt key
            modifiers.add('alt')
        if event.state & 0x1:  # Shift key
            modifiers.add('shift')
        
        self.drag_start = position
        self.controller.handle_click(position, modifiers)
        self._update_status()
    
    def _on_drag(self, event):
        """Handle mouse drag."""
        if hasattr(self, 'drag_start'):
            end_position = (event.x, event.y)
            modifiers = set()
            if event.state & 0x4:
                modifiers.add('ctrl')
            
            self.controller.handle_drag(self.drag_start, end_position, modifiers)
            self._update_status()
    
    def _on_release(self, event):
        """Handle mouse release."""
        if hasattr(self, 'drag_start'):
            delattr(self, 'drag_start')
    
    def _on_hover(self, event):
        """Handle mouse hover."""
        position = (event.x, event.y)
        self.controller.handle_hover(position)
    
    def _on_key(self, event):
        """Handle keyboard events."""
        modifiers = set()
        if event.state & 0x4:
            modifiers.add('ctrl')
        if event.state & 0x8:
            modifiers.add('alt')
        if event.state & 0x1:
            modifiers.add('shift')
        
        self.controller.handle_key(event.keysym, modifiers)
        self._update_status()
    
    def _on_mode_change(self):
        """Handle action mode change."""
        mode_map = {
            "normal": ActionMode.NORMAL,
            "add_cut": ActionMode.ADD_CUT,
            "add_individual": ActionMode.ADD_INDIVIDUAL,
            "add_predicate": ActionMode.ADD_PREDICATE,
            "move": ActionMode.MOVE,
            "delete": ActionMode.DELETE
        }
        
        mode = mode_map.get(self.mode_var.get(), ActionMode.NORMAL)
        self.controller.set_action_mode(mode)
        self._update_status()
    
    def _on_case_change(self, event=None):
        """Handle test case change."""
        self._load_test_case()
    
    def _load_test_case(self):
        """Load the selected test case."""
        egif_string = self.case_var.get()
        if not egif_string:
            return
        
        try:
            # Parse EGIF
            parser = EGIFParser(egif_string)
            graph = parser.parse()
            
            # Set graph in controller
            self.controller.set_graph(graph)
            
            self.status_var.set(f"Loaded: {egif_string}")
            
        except Exception as e:
            self.status_var.set(f"Error loading case: {e}")
    
    def _update_status(self):
        """Update status bar with current state."""
        mode = self.mode_var.get().replace('_', ' ').title()
        selection_count = len(self.controller.selection_state.selected_elements)
        selection_type = self.controller.selection_state.selection_type.value.replace('_', ' ').title()
        
        if selection_count > 0:
            status = f"Mode: {mode} | Selection: {selection_count} elements ({selection_type})"
        else:
            status = f"Mode: {mode} | No selection"
        
        self.status_var.set(status)
    
    def run(self):
        """Run the demonstration."""
        print("Starting Phase 2 Demonstration...")
        print("Features:")
        print("- Element selection with visual overlays")
        print("- Cut resize handles")
        print("- Vertex and predicate highlighting") 
        print("- Action-first workflow")
        print("- Professional interaction patterns")
        print()
        
        self.root.mainloop()


if __name__ == "__main__":
    demo = Phase2Demo()
    demo.run()
