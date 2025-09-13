#!/usr/bin/env python3
"""
Enhanced Diagram Editor with advanced Ergasterion capabilities.
Builds on the simple editor with professional features.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
import json
import os
import sys

# Import core components
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from gui.simple_diagram_editor import SimpleDiagramEditor, Element
from dau_diagram_correspondence import DiagramRepresentation
from formal_transformation_rules import TransformationContext


class EnhancedDiagramEditor(SimpleDiagramEditor):
    """Enhanced diagram editor with professional features."""
    
    def __init__(self, master):
        super().__init__(master)
        self.master.title("Arisbe - Enhanced EGI Editor (Ergasterion)")
        self.master.geometry("1400x900")
        
        # Enhanced features
        self.zoom_level = 1.0
        self.grid_enabled = True
        self.snap_to_grid = True
        self.grid_size = 20
        
        # Multi-selection
        self.selection_rectangle = None
        self.selection_start = None
        
        # Undo/Redo
        self.history_stack = []
        self.history_index = -1
        
        self.setup_enhanced_ui()
    
    def setup_enhanced_ui(self):
        """Add enhanced UI components."""
        # Add menu bar
        self.setup_menu_bar()
        
        # Add side panels
        self.setup_side_panels()
        
        # Add enhanced toolbar
        self.setup_enhanced_toolbar()
        
        # Enable advanced features
        self.enable_advanced_features()
    
    def setup_menu_bar(self):
        """Create menu bar."""
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self.new_diagram)
        file_menu.add_command(label="Open...", command=self.open_diagram)
        file_menu.add_command(label="Save", command=self.save_diagram)
        file_menu.add_command(label="Save As...", command=self.save_diagram_as)
        file_menu.add_separator()
        file_menu.add_command(label="Export SVG...", command=self.export_svg)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Select All", command=self.select_all, accelerator="Ctrl+A")
        edit_menu.add_command(label="Delete", command=self.delete_selected, accelerator="Del")
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Zoom In", command=self.zoom_in, accelerator="Ctrl++")
        view_menu.add_command(label="Zoom Out", command=self.zoom_out, accelerator="Ctrl+-")
        view_menu.add_command(label="Zoom Fit", command=self.zoom_fit, accelerator="Ctrl+0")
        view_menu.add_separator()
        view_menu.add_checkbutton(label="Show Grid", command=self.toggle_grid)
        view_menu.add_checkbutton(label="Snap to Grid", command=self.toggle_snap)
    
    def setup_side_panels(self):
        """Create side panels for properties and layers."""
        # Properties panel (right side)
        self.properties_frame = ttk.LabelFrame(self.master, text="Properties")
        self.properties_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        
        # Layers panel (left side)  
        self.layers_frame = ttk.LabelFrame(self.master, text="Layers")
        self.layers_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
    
    def setup_enhanced_toolbar(self):
        """Add enhanced toolbar features."""
        # Add zoom controls to existing toolbar
        zoom_frame = ttk.Frame(self.master)
        zoom_frame.pack(side=tk.TOP, fill=tk.X, padx=5)
        
        ttk.Label(zoom_frame, text="Zoom:").pack(side=tk.LEFT, padx=5)
        ttk.Button(zoom_frame, text="-", command=self.zoom_out, width=3).pack(side=tk.LEFT)
        
        self.zoom_var = tk.StringVar(value="100%")
        zoom_label = ttk.Label(zoom_frame, textvariable=self.zoom_var)
        zoom_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(zoom_frame, text="+", command=self.zoom_in, width=3).pack(side=tk.LEFT)
        ttk.Button(zoom_frame, text="Fit", command=self.zoom_fit).pack(side=tk.LEFT, padx=5)
    
    def enable_advanced_features(self):
        """Enable advanced editing features."""
        # Bind additional keyboard shortcuts
        self.master.bind("<Control-z>", lambda e: self.undo())
        self.master.bind("<Control-y>", lambda e: self.redo())
        self.master.bind("<Control-s>", lambda e: self.save_diagram())
        self.master.bind("<Control-o>", lambda e: self.open_diagram())
        self.master.bind("<Control-n>", lambda e: self.new_diagram())
        
        # Bind zoom shortcuts
        self.master.bind("<Control-plus>", lambda e: self.zoom_in())
        self.master.bind("<Control-minus>", lambda e: self.zoom_out())
        self.master.bind("<Control-0>", lambda e: self.zoom_fit())
        
        # Enable rectangle selection
        self.canvas.bind("<Button-1>", self.enhanced_click, add="+")
        self.canvas.bind("<B1-Motion>", self.enhanced_drag, add="+")
        self.canvas.bind("<ButtonRelease-1>", self.enhanced_release, add="+")
    
    # File operations
    def new_diagram(self):
        """Create new diagram."""
        if messagebox.askyesno("New Diagram", "Clear current diagram?"):
            self.clear_all()
    
    def open_diagram(self):
        """Open diagram from file."""
        filename = filedialog.askopenfilename(
            title="Open Diagram",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                self.load_diagram_data(data)
                self.status_var.set(f"Opened: {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file: {e}")
    
    def save_diagram(self):
        """Save current diagram."""
        filename = filedialog.asksaveasfilename(
            title="Save Diagram",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                data = self.export_diagram_data()
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)
                self.status_var.set(f"Saved: {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")
    
    def save_diagram_as(self):
        """Save diagram with new name."""
        self.save_diagram()
    
    def export_svg(self):
        """Export diagram as SVG."""
        messagebox.showinfo("Export SVG", "SVG export not yet implemented")
    
    # Zoom operations
    def zoom_in(self):
        """Zoom in."""
        self.zoom_level = min(self.zoom_level * 1.2, 5.0)
        self.update_zoom()
    
    def zoom_out(self):
        """Zoom out."""
        self.zoom_level = max(self.zoom_level / 1.2, 0.2)
        self.update_zoom()
    
    def zoom_fit(self):
        """Fit diagram to window."""
        self.zoom_level = 1.0
        self.update_zoom()
    
    def update_zoom(self):
        """Update zoom display."""
        self.zoom_var.set(f"{int(self.zoom_level * 100)}%")
        # TODO: Apply zoom transformation to canvas
    
    # Grid operations
    def toggle_grid(self):
        """Toggle grid display."""
        self.grid_enabled = not self.grid_enabled
        self.draw_grid()
    
    def toggle_snap(self):
        """Toggle snap to grid."""
        self.snap_to_grid = not self.snap_to_grid
    
    def draw_grid(self):
        """Draw grid on canvas."""
        self.canvas.delete("grid")
        if not self.grid_enabled:
            return
        
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        # Draw vertical lines
        for x in range(0, width, self.grid_size):
            self.canvas.create_line(x, 0, x, height, fill="lightgray", tags="grid")
        
        # Draw horizontal lines
        for y in range(0, height, self.grid_size):
            self.canvas.create_line(0, y, width, y, fill="lightgray", tags="grid")
    
    # Enhanced selection
    def enhanced_click(self, event):
        """Enhanced click handling."""
        if self.current_tool == "select":
            self.selection_start = (event.x, event.y)
    
    def enhanced_drag(self, event):
        """Enhanced drag handling."""
        if self.current_tool == "select" and self.selection_start:
            # Update selection rectangle
            if self.selection_rectangle:
                self.canvas.delete(self.selection_rectangle)
            
            x1, y1 = self.selection_start
            self.selection_rectangle = self.canvas.create_rectangle(
                x1, y1, event.x, event.y,
                outline="blue", dash=(5, 5), tags="selection"
            )
    
    def enhanced_release(self, event):
        """Enhanced release handling."""
        if self.current_tool == "select" and self.selection_start:
            # Select elements in rectangle
            x1, y1 = self.selection_start
            x2, y2 = event.x, event.y
            
            # Ensure x1,y1 is top-left
            if x1 > x2:
                x1, x2 = x2, x1
            if y1 > y2:
                y1, y2 = y2, y1
            
            self.select_elements_in_rectangle(x1, y1, x2, y2)
            
            # Clean up
            if self.selection_rectangle:
                self.canvas.delete(self.selection_rectangle)
                self.selection_rectangle = None
            self.selection_start = None
    
    def select_elements_in_rectangle(self, x1: float, y1: float, x2: float, y2: float):
        """Select all elements within rectangle."""
        self.clear_selection()
        
        for element in self.elements.values():
            if x1 <= element.x <= x2 and y1 <= element.y <= y2:
                self.select_element(element.element_id)
    
    # History operations
    def save_state(self):
        """Save current state to history."""
        state = self.export_diagram_data()
        
        # Remove future history if we're not at the end
        if self.history_index < len(self.history_stack) - 1:
            self.history_stack = self.history_stack[:self.history_index + 1]
        
        self.history_stack.append(state)
        self.history_index += 1
        
        # Limit history size
        if len(self.history_stack) > 50:
            self.history_stack.pop(0)
            self.history_index -= 1
    
    def undo(self):
        """Undo last operation."""
        if self.history_index > 0:
            self.history_index -= 1
            state = self.history_stack[self.history_index]
            self.load_diagram_data(state)
            self.status_var.set("Undone")
    
    def redo(self):
        """Redo last undone operation."""
        if self.history_index < len(self.history_stack) - 1:
            self.history_index += 1
            state = self.history_stack[self.history_index]
            self.load_diagram_data(state)
            self.status_var.set("Redone")
    
    # Data operations
    def export_diagram_data(self) -> dict:
        """Export diagram data."""
        return {
            "elements": {
                eid: {
                    "element_id": elem.element_id,
                    "element_type": elem.element_type,
                    "x": elem.x,
                    "y": elem.y,
                    "start_vertex": getattr(elem, 'start_vertex', None),
                    "end_vertex": getattr(elem, 'end_vertex', None)
                }
                for eid, elem in self.elements.items()
            },
            "zoom_level": self.zoom_level,
            "grid_enabled": self.grid_enabled
        }
    
    def load_diagram_data(self, data: dict):
        """Load diagram from data."""
        # Clear current diagram
        self.clear_all()
        
        # Load elements
        for elem_data in data.get("elements", {}).values():
            if elem_data["element_type"] == "vertex":
                self.create_vertex_at_position(
                    elem_data["element_id"],
                    elem_data["x"],
                    elem_data["y"]
                )
            elif elem_data["element_type"] == "cut":
                self.create_cut_at_position(
                    elem_data["element_id"],
                    elem_data["x"],
                    elem_data["y"],
                    50  # Default radius
                )
            elif elem_data["element_type"] == "edge":
                if elem_data.get("start_vertex") and elem_data.get("end_vertex"):
                    start_pos = (self.elements[elem_data["start_vertex"]].x,
                               self.elements[elem_data["start_vertex"]].y)
                    end_pos = (self.elements[elem_data["end_vertex"]].x,
                             self.elements[elem_data["end_vertex"]].y)
                    self.create_edge_at_positions(
                        elem_data["element_id"],
                        start_pos,
                        end_pos,
                        elem_data["start_vertex"],
                        elem_data["end_vertex"]
                    )
        
        # Load settings
        self.zoom_level = data.get("zoom_level", 1.0)
        self.grid_enabled = data.get("grid_enabled", True)
        self.update_zoom()
        self.draw_grid()


def main():
    """Run the enhanced diagram editor."""
    root = tk.Tk()
    app = EnhancedDiagramEditor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
