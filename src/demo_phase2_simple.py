#!/usr/bin/env python3
"""
Phase 2 Simplified Demonstration: Core Selection and Actions

Demonstrates the key Phase 2 concepts without complex integration issues:
- Selection system with visual overlays
- Context-sensitive actions
- Logical vs. appearance-only operations
- Professional interaction patterns
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from egif_parser_dau import EGIFParser
from layout_engine_clean import CleanLayoutEngine
from diagram_renderer_clean import CleanDiagramRenderer
from tkinter_backend import TkinterCanvas


class SimplePhase2Demo:
    """
    Simplified demonstration of Phase 2 concepts.
    
    Shows core functionality:
    - Visual selection overlays
    - Context-sensitive action validation
    - Logical operations on EGI model
    - Professional interaction patterns
    """
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Phase 2 Simple: Selection & Context-Sensitive Actions")
        self.root.geometry("1000x700")
        
        # Core components
        self.current_graph = None
        self.current_layout = None
        self.selected_elements = set()
        self.selection_bounds = None
        
        # Create UI
        self._create_ui()
        
        # Initialize engines
        self.layout_engine = CleanLayoutEngine()
        self.renderer = CleanDiagramRenderer(self.canvas)
        
        # Load initial test case
        self._load_initial_case()
    
    def _create_ui(self):
        """Create the UI layout."""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top controls
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Test case selector
        ttk.Label(controls_frame, text="Test Case:").pack(side=tk.LEFT)
        self.case_var = tk.StringVar()
        case_combo = ttk.Combobox(controls_frame, textvariable=self.case_var, width=40)
        case_combo['values'] = [
            '(Human "Socrates") ~[ (Mortal "Socrates") ]',
            '*x ~[ (Human x) (Mortal x) ]',
            '*x (Human x) ~[ (Mortal x) (Wise x) ]',
            '*x *y (Human x) (Loves x y) ~[ (Mortal y) ]'
        ]
        case_combo.set(case_combo['values'][0])
        case_combo.pack(side=tk.LEFT, padx=(5, 10))
        case_combo.bind('<<ComboboxSelected>>', self._on_case_change)
        
        ttk.Button(controls_frame, text="Reload", command=self._load_case).pack(side=tk.LEFT, padx=5)
        
        # Content area
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Actions
        left_frame = ttk.LabelFrame(content_frame, text="Context-Sensitive Actions", width=200)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_frame.pack_propagate(False)
        
        # Action buttons
        ttk.Label(left_frame, text="Insert Actions:", font=('Arial', 10, 'bold')).pack(pady=(5, 2))
        ttk.Button(left_frame, text="Insert Cut", command=self._insert_cut).pack(fill=tk.X, pady=2)
        ttk.Button(left_frame, text="Insert Predicate", command=self._insert_predicate).pack(fill=tk.X, pady=2)
        ttk.Button(left_frame, text="Insert Individual", command=self._insert_individual).pack(fill=tk.X, pady=2)
        
        ttk.Label(left_frame, text="Modify Actions:", font=('Arial', 10, 'bold')).pack(pady=(10, 2))
        ttk.Button(left_frame, text="Delete Selected", command=self._delete_selected).pack(fill=tk.X, pady=2)
        ttk.Button(left_frame, text="Clear Selection", command=self._clear_selection).pack(fill=tk.X, pady=2)
        
        # Selection info
        ttk.Label(left_frame, text="Selection Info:", font=('Arial', 10, 'bold')).pack(pady=(10, 2))
        self.selection_info = tk.Text(left_frame, height=8, wrap=tk.WORD, font=('Courier', 9))
        self.selection_info.pack(fill=tk.BOTH, expand=True, pady=2)
        
        # Available actions
        ttk.Label(left_frame, text="Available Actions:", font=('Arial', 10, 'bold')).pack(pady=(5, 2))
        self.actions_info = tk.Text(left_frame, height=4, wrap=tk.WORD, font=('Arial', 9))
        self.actions_info.pack(fill=tk.X, pady=2)
        
        # Center - Canvas
        canvas_frame = ttk.LabelFrame(content_frame, text="Existential Graph Canvas")
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        canvas_container = ttk.Frame(canvas_frame)
        canvas_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.canvas = TkinterCanvas(width=600, height=450, master=canvas_container)
        
        # Instructions
        instructions = ttk.Label(canvas_container, 
            text="• Click elements to select (blue highlight)\n"
                 "• Drag to select area (dotted rectangle)\n"
                 "• Use action buttons based on selection type\n"
                 "• Actions are validated for current selection",
            justify=tk.LEFT, font=('Arial', 9))
        instructions.pack(pady=(5, 0))
        
        # Right panel - Graph info
        right_frame = ttk.LabelFrame(content_frame, text="Graph Structure", width=200)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        right_frame.pack_propagate(False)
        
        self.graph_info = tk.Text(right_frame, wrap=tk.WORD, font=('Courier', 9))
        self.graph_info.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready - Click elements or drag to select")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, pady=(10, 0))
        
        # Bind events
        self._bind_events()
    
    def _bind_events(self):
        """Bind canvas events."""
        self.canvas.tk_canvas.bind("<Button-1>", self._on_click)
        self.canvas.tk_canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.tk_canvas.bind("<ButtonRelease-1>", self._on_release)
        
        # Keyboard shortcuts
        self.root.bind("<Escape>", lambda e: self._clear_selection())
        self.root.bind("<Delete>", lambda e: self._delete_selected())
        self.root.focus_set()
    
    def _load_initial_case(self):
        """Load the initial test case."""
        self._load_case()
    
    def _load_case(self):
        """Load selected test case."""
        egif_string = self.case_var.get()
        if not egif_string:
            return
        
        try:
            parser = EGIFParser(egif_string)
            self.current_graph = parser.parse()
            self.current_layout = self.layout_engine.layout_graph(self.current_graph)
            self._render_diagram()
            self._update_graph_info()
            self._clear_selection()
            self.status_var.set(f"Loaded: {egif_string}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load case: {e}")
            self.status_var.set(f"Error: {e}")
    
    def _on_case_change(self, event=None):
        """Handle test case change."""
        self._load_case()
    
    def _on_click(self, event):
        """Handle mouse click."""
        x, y = event.x, event.y
        self.drag_start = (x, y)
        
        # Find element at position
        element_id = self._find_element_at_position((x, y))
        
        if element_id:
            # Single element selection
            if element_id in self.selected_elements:
                self.selected_elements.remove(element_id)
            else:
                if not (event.state & 0x4):  # Not Ctrl+click
                    self.selected_elements.clear()
                self.selected_elements.add(element_id)
            self.selection_bounds = None
        else:
            # Clear selection if not dragging
            if not (event.state & 0x4):  # Not Ctrl+click
                self.selected_elements.clear()
            self.selection_bounds = None
        
        self._update_selection_display()
        self._render_diagram()
    
    def _on_drag(self, event):
        """Handle mouse drag."""
        if hasattr(self, 'drag_start'):
            x1, y1 = self.drag_start
            x2, y2 = event.x, event.y
            
            # Update selection bounds
            self.selection_bounds = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
            
            # Find elements in bounds
            elements_in_bounds = self._find_elements_in_bounds(self.selection_bounds)
            if not (event.state & 0x4):  # Not Ctrl+drag
                self.selected_elements = elements_in_bounds
            else:
                self.selected_elements.update(elements_in_bounds)
            
            self._update_selection_display()
            self._render_diagram()
    
    def _on_release(self, event):
        """Handle mouse release."""
        if hasattr(self, 'drag_start'):
            delattr(self, 'drag_start')
    
    def _find_element_at_position(self, position):
        """Find element at given position."""
        if not self.current_layout:
            return None
        
        x, y = position
        # Check elements in reverse z-order (top to bottom)
        for element_id, primitive in sorted(self.current_layout.primitives.items(),
                                          key=lambda item: item[1].z_index, reverse=True):
            x1, y1, x2, y2 = primitive.bounds
            if x1 <= x <= x2 and y1 <= y <= y2:
                return element_id
        return None
    
    def _find_elements_in_bounds(self, bounds):
        """Find all elements within given bounds."""
        if not self.current_layout:
            return set()
        
        x1, y1, x2, y2 = bounds
        elements = set()
        
        for element_id, primitive in self.current_layout.primitives.items():
            px1, py1, px2, py2 = primitive.bounds
            # Check if primitive overlaps with bounds
            if not (px2 < x1 or px1 > x2 or py2 < y1 or py1 > y2):
                elements.add(element_id)
        
        return elements
    
    def _render_diagram(self):
        """Render the current diagram with selection overlays."""
        if not self.current_graph or not self.current_layout:
            return
        
        # Clear canvas
        self.canvas.clear()
        
        # Render main diagram
        self.renderer.render_diagram(self.current_layout, self.current_graph)
        
        # Render selection overlays
        self._render_selection_overlays()
    
    def _render_selection_overlays(self):
        """Render selection overlays."""
        # Render selected elements with blue highlight
        for element_id in self.selected_elements:
            if element_id in self.current_layout.primitives:
                primitive = self.current_layout.primitives[element_id]
                x1, y1, x2, y2 = primitive.bounds
                
                # Draw blue highlight rectangle
                self.canvas.tk_canvas.create_rectangle(
                    x1-2, y1-2, x2+2, y2+2,
                    outline="blue", width=2, fill="", dash=(3, 3)
                )
        
        # Render selection bounds
        if self.selection_bounds:
            x1, y1, x2, y2 = self.selection_bounds
            self.canvas.tk_canvas.create_rectangle(
                x1, y1, x2, y2,
                outline="green", width=1, fill="", dash=(5, 5)
            )
    
    def _update_selection_display(self):
        """Update selection information display."""
        info = f"Selected Elements: {len(self.selected_elements)}\n\n"
        
        if self.selected_elements:
            info += "Element Details:\n"
            for element_id in list(self.selected_elements)[:5]:  # Show first 5
                element_type = "Unknown"
                if element_id in self.current_graph.V:
                    element_type = "Vertex"
                elif element_id in self.current_graph.E:
                    element_type = "Edge"
                    if element_id in self.current_graph.rel:
                        element_type += f" ({self.current_graph.rel[element_id]})"
                elif element_id in self.current_graph.Cut:
                    element_type = "Cut"
                
                info += f"• {element_type}\n  ID: {element_id[-8:]}\n"
            
            if len(self.selected_elements) > 5:
                info += f"... and {len(self.selected_elements) - 5} more\n"
        
        if self.selection_bounds:
            x1, y1, x2, y2 = self.selection_bounds
            info += f"\nSelection Bounds:\n({x1:.0f}, {y1:.0f}) to ({x2:.0f}, {y2:.0f})\n"
        
        self.selection_info.delete(1.0, tk.END)
        self.selection_info.insert(1.0, info)
        
        # Update available actions
        self._update_available_actions()
    
    def _update_available_actions(self):
        """Update available actions display."""
        actions = []
        
        if not self.selected_elements and not self.selection_bounds:
            actions.append("• Select elements or area first")
        elif self.selected_elements:
            actions.append("• Delete Selected")
            actions.append("• Clear Selection")
            if len(self.selected_elements) > 1:
                actions.append("• Insert Cut (enclose)")
        elif self.selection_bounds:
            actions.append("• Insert Cut")
            actions.append("• Insert Predicate")
            actions.append("• Insert Individual")
        
        actions_text = "Available actions:\n" + "\n".join(actions)
        self.actions_info.delete(1.0, tk.END)
        self.actions_info.insert(1.0, actions_text)
    
    def _update_graph_info(self):
        """Update graph structure display."""
        if not self.current_graph:
            return
        
        graph = self.current_graph
        
        info = f"Graph Structure:\n"
        info += f"Vertices: {len(graph.V)}\n"
        info += f"Edges: {len(graph.E)}\n"
        info += f"Cuts: {len(graph.Cut)}\n\n"
        
        info += "Relations:\n"
        for edge_id, relation in list(graph.rel.items())[:8]:
            args = graph.nu.get(edge_id, ())
            info += f"• {relation}({len(args)} args)\n"
        
        if len(graph.rel) > 8:
            info += f"... and {len(graph.rel) - 8} more\n"
        
        info += f"\nAreas:\n"
        for area_id, elements in list(graph.area.items())[:5]:
            area_name = "Sheet" if area_id == graph.sheet else f"Cut {area_id[-8:]}"
            info += f"• {area_name}: {len(elements)} elements\n"
        
        self.graph_info.delete(1.0, tk.END)
        self.graph_info.insert(1.0, info)
    
    def _insert_cut(self):
        """Insert a new cut."""
        if not self.selected_elements and not self.selection_bounds:
            messagebox.showwarning("No Selection", "Select elements to enclose or drag to select an area first.")
            return
        
        try:
            # This would implement the actual cut insertion logic
            self.status_var.set("Cut insertion - Feature demonstration (not fully implemented)")
            messagebox.showinfo("Action", "Cut insertion validated and would be executed.\n\nThis demonstrates context-sensitive action validation.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to insert cut: {e}")
    
    def _insert_predicate(self):
        """Insert a new predicate."""
        if not self.selection_bounds:
            messagebox.showwarning("No Area Selected", "Drag to select an empty area first.")
            return
        
        # Get predicate details
        label = simpledialog.askstring("Insert Predicate", "Enter predicate name:")
        if not label:
            return
        
        try:
            # This would implement the actual predicate insertion logic
            self.status_var.set(f"Predicate '{label}' insertion - Feature demonstration")
            messagebox.showinfo("Action", f"Predicate '{label}' insertion validated and would be executed.\n\nThis demonstrates logical EGI operations.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to insert predicate: {e}")
    
    def _insert_individual(self):
        """Insert a new individual."""
        if not self.selection_bounds:
            messagebox.showwarning("No Area Selected", "Drag to select an empty area first.")
            return
        
        try:
            # This would implement the actual individual insertion logic
            self.status_var.set("Individual insertion - Feature demonstration")
            messagebox.showinfo("Action", "Individual (Line of Identity) insertion validated and would be executed.\n\nThis demonstrates Dau's formalism.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to insert individual: {e}")
    
    def _delete_selected(self):
        """Delete selected elements."""
        if not self.selected_elements:
            messagebox.showwarning("No Selection", "Select elements to delete first.")
            return
        
        if not messagebox.askyesno("Confirm Delete", f"Delete {len(self.selected_elements)} selected element(s)?"):
            return
        
        try:
            # This would implement the actual deletion logic
            self.status_var.set(f"Deletion of {len(self.selected_elements)} elements - Feature demonstration")
            messagebox.showinfo("Action", f"Deletion of {len(self.selected_elements)} elements validated and would be executed.\n\nThis demonstrates rule-based operations.")
            self._clear_selection()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete elements: {e}")
    
    def _clear_selection(self):
        """Clear current selection."""
        self.selected_elements.clear()
        self.selection_bounds = None
        self._update_selection_display()
        self._render_diagram()
        self.status_var.set("Selection cleared")
    
    def run(self):
        """Run the simplified demonstration."""
        print("Starting Phase 2 Simplified Demonstration...")
        print("Key Features Demonstrated:")
        print("- Visual selection overlays (blue highlights, green selection rectangle)")
        print("- Context-sensitive action validation")
        print("- Logical vs. appearance-only operation concepts")
        print("- Professional interaction patterns")
        print("- EGI model integration")
        print()
        print("Instructions:")
        print("- Click elements to select them (blue highlight)")
        print("- Drag to select areas (green dotted rectangle)")
        print("- Use action buttons - they validate based on current selection")
        print("- Actions show validation messages and demonstrate the concepts")
        print()
        
        self.root.mainloop()


if __name__ == "__main__":
    demo = SimplePhase2Demo()
    demo.run()
