#!/usr/bin/env python3
"""
Simplified, working diagram editor for Dau-compliant EGI diagrams.
Focus on core functionality that actually works.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import math
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

# Import our core components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from dau_diagram_correspondence import (
    DauDiagramCorrespondence, DiagramRepresentation, VertexSpot, 
    RelationSign, CutLine, ConstraintViolation
)
from formal_transformation_rules import (
    FormalTransformationRule, TransformationContext, TransformationResult,
    AreaPolarity, IterationRule, DeiterationRule, DoubleCutInsertionRule,
    DoubleCutErasureRule, InsertionRule, ErasureRule
)
from egi_core_dau import RelationalGraphWithCuts


@dataclass
class Element:
    """Simple element representation."""
    element_id: str
    element_type: str
    x: float
    y: float
    canvas_items: List[int]  # All canvas items for this element
    selected: bool = False


class SimpleDiagramEditor:
    """Simplified diagram editor with working core functionality."""
    
    def __init__(self, master):
        self.master = master
        self.master.title("Arisbe - Simple EGI Editor")
        self.master.geometry("1000x700")
        
        # Core state
        self.correspondence = DauDiagramCorrespondence()
        self.elements: Dict[str, Element] = {}
        self.selected_elements: Set[str] = set()
        self.element_counter = 0
        
        # Transformation system
        self.transformation_rules = {
            "IT+": IterationRule(),
            "IT-": DeiterationRule(),
            "DC+": DoubleCutInsertionRule(),
            "DC-": DoubleCutErasureRule(),
            "INS": InsertionRule(),
            "ERA": ErasureRule()
        }
        self.current_egi: Optional[RelationalGraphWithCuts] = None
        
        # Current context
        self.current_context = "sheet"
        self.context_polarity = "positive"
        
        # Tools
        self.current_tool = "vertex"
        
        # Drag state
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.dragging_element = None
        
        # Edge creation state
        self.edge_start_element = None
        self.edge_preview_line = None
        
        # Validation feedback
        self.validation_overlays = []  # Visual indicators for constraint violations
        self.last_validation_result = None
        
        self.setup_ui()
        self.bind_events()
        self.draw_sheet_background()
    
    def setup_ui(self):
        """Create the user interface."""
        # Main container
        main_frame = ttk.Frame(self.master)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Toolbar
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))
        
        # Tool selection
        ttk.Label(toolbar, text="Tool:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.tool_var = tk.StringVar(value="vertex")
        ttk.Radiobutton(toolbar, text="Vertex", variable=self.tool_var, 
                       value="vertex", command=self.on_tool_change).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(toolbar, text="Cut", variable=self.tool_var, 
                       value="cut", command=self.on_tool_change).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(toolbar, text="Edge", variable=self.tool_var, 
                       value="edge", command=self.on_tool_change).pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Actions
        ttk.Button(toolbar, text="Clear All", command=self.clear_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Validate", command=self.validate_diagram).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Sync EGI", command=self.sync_to_egi).pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Transformation buttons
        ttk.Label(toolbar, text="Transformations:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.transform_buttons = {}
        for rule_name in self.transformation_rules.keys():
            btn = ttk.Button(toolbar, text=rule_name, 
                           command=lambda r=rule_name: self.apply_transformation(r),
                           state="disabled")
            btn.pack(side=tk.LEFT, padx=2)
            self.transform_buttons[rule_name] = btn
        
        # Canvas frame
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas
        self.canvas = tk.Canvas(canvas_frame, bg="white", width=800, height=600)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))
        
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Click to add vertices")
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Context indicator
        self.context_var = tk.StringVar()
        self.context_var.set("Context: Sheet of Assertion (Positive)")
        ttk.Label(status_frame, textvariable=self.context_var, 
                 background="lightblue").pack(side=tk.RIGHT, padx=(5, 0))
        
        # Validation indicator
        self.validation_var = tk.StringVar()
        self.validation_var.set("Valid")
        self.validation_label = ttk.Label(status_frame, textvariable=self.validation_var, 
                                        background="lightgreen")
        self.validation_label.pack(side=tk.RIGHT, padx=(5, 0))
    
    def bind_events(self):
        """Bind canvas events."""
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        
        # Keyboard
        self.master.bind("<Delete>", self.delete_selected)
        self.master.bind("<Control-a>", self.select_all)
        self.master.focus_set()
        
        # Bind validation tooltip to validation label
        self.validation_label.bind("<Button-1>", self.show_validation_tooltip)
    
    def on_tool_change(self):
        """Handle tool change."""
        self.current_tool = self.tool_var.get()
        if self.current_tool == "vertex":
            self.status_var.set("Click to add vertices")
        elif self.current_tool == "cut":
            self.status_var.set("Click and drag to create cuts")
        elif self.current_tool == "edge":
            self.status_var.set("Click vertices to connect with edges")
            self.cancel_edge_creation()
    
    def draw_sheet_background(self):
        """Draw the sheet of assertion background."""
        self.canvas.delete("background")
        
        # Sheet boundary
        self.canvas.create_rectangle(
            20, 20, 780, 580,
            outline="darkblue", width=2, dash=(10, 5),
            tags="background"
        )
        
        # Sheet label
        self.canvas.create_text(
            40, 40, text="Sheet of Assertion", 
            font=("Arial", 12, "bold"), fill="darkblue",
            anchor="nw", tags="background"
        )
    
    def on_click(self, event):
        """Handle canvas clicks."""
        x, y = event.x, event.y
        
        # Check if clicking on existing element
        clicked_item = self.canvas.find_closest(x, y)[0]
        clicked_element = self.find_element_by_canvas_item(clicked_item)
        
        if clicked_element:
            if self.current_tool == "edge" and clicked_element.element_type == "vertex":
                # Handle edge creation
                self.handle_edge_click(clicked_element)
            else:
                # Select element and prepare for drag
                self.clear_selection()
                self.select_element(clicked_element.element_id)
                self.dragging_element = clicked_element.element_id
                self.drag_start_x = x
                self.drag_start_y = y
        else:
            # Create new element
            self.clear_selection()
            if self.current_tool == "vertex":
                self.create_vertex(x, y)
            elif self.current_tool == "cut":
                self.start_cut_creation(x, y)
            elif self.current_tool == "edge":
                # Edge tool doesn't create elements on empty space
                self.cancel_edge_creation()
    
    def on_drag(self, event):
        """Handle dragging."""
        if self.dragging_element:
            # Move element
            dx = event.x - self.drag_start_x
            dy = event.y - self.drag_start_y
            
            element = self.elements[self.dragging_element]
            for item_id in element.canvas_items:
                self.canvas.move(item_id, dx, dy)
            
            element.x += dx
            element.y += dy
            
            self.drag_start_x = event.x
            self.drag_start_y = event.y
            
        elif self.current_tool == "cut" and hasattr(self, 'cut_start_x'):
            # Show cut preview
            self.update_cut_preview(event.x, event.y)
        elif self.current_tool == "edge" and self.edge_start_element:
            # Update edge preview
            self.update_edge_preview(event.x, event.y)
    
    def on_release(self, event):
        """Handle mouse release."""
        if self.current_tool == "cut" and hasattr(self, 'cut_start_x'):
            # Complete cut creation
            self.complete_cut_creation(event.x, event.y)
        
        self.dragging_element = None
    
    def create_vertex(self, x: float, y: float) -> str:
        """Create a vertex at the given position."""
        element_id = f"v{self.element_counter}"
        self.element_counter += 1
        
        # Draw vertex circle
        circle = self.canvas.create_oval(
            x - 12, y - 12, x + 12, y + 12,
            fill="lightblue", outline="blue", width=2
        )
        
        # Draw label
        label = self.canvas.create_text(
            x, y + 25, text=element_id, 
            font=("Arial", 10), fill="black"
        )
        
        # Create element
        element = Element(
            element_id=element_id,
            element_type="vertex",
            x=x, y=y,
            canvas_items=[circle, label]
        )
        
        self.elements[element_id] = element
        self.status_var.set(f"Created vertex: {element_id}")
        
        # Validate after creation
        self.validate_diagram_realtime()
        
        return element_id
    
    def start_cut_creation(self, x: float, y: float):
        """Start creating a cut."""
        self.cut_start_x = x
        self.cut_start_y = y
        self.status_var.set("Drag to set cut size")
    
    def update_cut_preview(self, x: float, y: float):
        """Update cut preview during drag."""
        # Remove old preview
        self.canvas.delete("cut_preview")
        
        # Calculate radius
        radius = math.sqrt((x - self.cut_start_x)**2 + (y - self.cut_start_y)**2)
        
        if radius > 10:  # Minimum size
            # Draw preview
            self.canvas.create_oval(
                self.cut_start_x - radius, self.cut_start_y - radius,
                self.cut_start_x + radius, self.cut_start_y + radius,
                outline="red", width=2, dash=(5, 5),
                tags="cut_preview"
            )
    
    def complete_cut_creation(self, x: float, y: float):
        """Complete cut creation."""
        # Remove preview
        self.canvas.delete("cut_preview")
        
        # Calculate final radius
        radius = math.sqrt((x - self.cut_start_x)**2 + (y - self.cut_start_y)**2)
        
        if radius > 20:  # Minimum cut size
            self.create_cut(self.cut_start_x, self.cut_start_y, radius)
        
        # Clean up
        if hasattr(self, 'cut_start_x'):
            delattr(self, 'cut_start_x')
        if hasattr(self, 'cut_start_y'):
            delattr(self, 'cut_start_y')
    
    def create_cut(self, center_x: float, center_y: float, radius: float) -> str:
        """Create a cut with given center and radius."""
        element_id = f"cut{self.element_counter}"
        self.element_counter += 1
        
        # Draw cut circle
        circle = self.canvas.create_oval(
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius,
            outline="red", width=3, fill="lightgray"
        )
        
        # Create element
        element = Element(
            element_id=element_id,
            element_type="cut",
            x=center_x, y=center_y,
            canvas_items=[circle]
        )
        
        self.elements[element_id] = element
        self.status_var.set(f"Created cut: {element_id}")
        
        # Validate after creation
        self.validate_diagram_realtime()
        
        return element_id
    
    def find_element_by_canvas_item(self, canvas_item: int) -> Optional[Element]:
        """Find element that owns the given canvas item."""
        for element in self.elements.values():
            if canvas_item in element.canvas_items:
                return element
        return None
    
    def select_element(self, element_id: str):
        """Select an element."""
        if element_id in self.elements:
            element = self.elements[element_id]
            element.selected = True
            self.selected_elements.add(element_id)
            
            # Visual feedback - thicker outline
            for item_id in element.canvas_items:
                item_type = self.canvas.type(item_id)
                if item_type in ["oval", "rectangle"]:
                    self.canvas.itemconfig(item_id, width=4)
    
    def deselect_element(self, element_id: str):
        """Deselect an element."""
        if element_id in self.selected_elements:
            element = self.elements[element_id]
            element.selected = False
            self.selected_elements.remove(element_id)
            
            # Remove visual feedback
            for item_id in element.canvas_items:
                item_type = self.canvas.type(item_id)
                if item_type in ["oval", "rectangle"]:
                    if element.element_type == "vertex":
                        self.canvas.itemconfig(item_id, width=2)
                    elif element.element_type == "cut":
                        self.canvas.itemconfig(item_id, width=3)
    
    def clear_selection(self):
        """Clear all selections."""
        for element_id in list(self.selected_elements):
            self.deselect_element(element_id)
    
    def delete_selected(self, event=None):
        """Delete selected elements."""
        if not self.selected_elements:
            return
        
        for element_id in list(self.selected_elements):
            element = self.elements[element_id]
            
            # Remove from canvas
            for item_id in element.canvas_items:
                self.canvas.delete(item_id)
            
            # Remove from data
            del self.elements[element_id]
        
        self.selected_elements.clear()
        self.validate_diagram_realtime()
        self.status_var.set("Deleted selected elements")
    
    def select_all(self, event=None):
        """Select all elements."""
        self.clear_selection()
        for element_id in self.elements:
            self.select_element(element_id)
    
    def clear_all(self):
        """Clear all elements."""
        if messagebox.askyesno("Clear All", "Delete all elements?"):
            for element in self.elements.values():
                for item_id in element.canvas_items:
                    self.canvas.delete(item_id)
            
            self.elements.clear()
            self.selected_elements.clear()
            self.element_counter = 0
            self.clear_validation_overlays()
            self.status_var.set("Cleared all elements")
    
    def validate_diagram(self):
        """Validate the current diagram."""
        try:
            diagram = self.build_diagram_representation()
            self.correspondence.validate_diagram_constraints(diagram)
            messagebox.showinfo("Validation", "Diagram is valid!")
            self.status_var.set("Validation passed")
        except ConstraintViolation as e:
            messagebox.showerror("Validation Error", str(e))
            self.status_var.set(f"Validation failed")
        except Exception as e:
            messagebox.showerror("Error", f"Validation error: {e}")
    
    def build_diagram_representation(self) -> DiagramRepresentation:
        """Build diagram representation from current state."""
        vertex_spots = {}
        cut_lines = {}
        containment = {"sheet": set()}
        
        # Process vertices
        for element in self.elements.values():
            if element.element_type == "vertex":
                vertex_spots[element.element_id] = VertexSpot(
                    element_id=element.element_id,
                    label=element.element_id,
                    is_generic=True,
                    containing_cut=self.find_containing_cut(element)
                )
        
        # Process edges (relations)
        relation_signs = {}
        edge_lines = {}
        for element in self.elements.values():
            if element.element_type == "edge":
                # Create relation sign for the edge
                relation_id = f"rel_{element.element_id}"
                relation_signs[relation_id] = RelationSign(
                    element_id=relation_id,
                    label="connects",
                    arity=2,
                    containing_cut=self.find_containing_cut(element)
                )
                
                # Create edge line
                edge_lines[element.element_id] = {
                    "relation_id": relation_id,
                    "start_vertex": element.start_vertex,
                    "end_vertex": element.end_vertex
                }
        
        # Process cuts
        for element in self.elements.values():
            if element.element_type == "cut":
                cut_lines[element.element_id] = CutLine(
                    element_id=element.element_id,
                    containing_cut=self.find_containing_cut(element)
                )
        
        # Build containment
        for element in self.elements.values():
            containing_cut = self.find_containing_cut(element)
            if containing_cut:
                if containing_cut not in containment:
                    containment[containing_cut] = set()
                containment[containing_cut].add(element.element_id)
            else:
                containment["sheet"].add(element.element_id)
        
        return DiagramRepresentation(
            sheet_id="sheet",
            vertex_spots=vertex_spots,
            relation_signs=relation_signs,
            edge_lines=edge_lines,
            cut_lines=cut_lines,
            containment=containment
        )
    
    def find_containing_cut(self, element: Element) -> Optional[str]:
        """Find which cut contains the given element."""
        for cut_element in self.elements.values():
            if (cut_element.element_type == "cut" and 
                cut_element != element):
                
                # Get cut bounds from canvas
                cut_item = cut_element.canvas_items[0]
                coords = self.canvas.coords(cut_item)
                if len(coords) >= 4:
                    x1, y1, x2, y2 = coords
                    center_x = (x1 + x2) / 2
                    center_y = (y1 + y2) / 2
                    radius = (x2 - x1) / 2
                    
                    # Check if element is inside
                    dx = element.x - center_x
                    dy = element.y - center_y
                    distance = math.sqrt(dx*dx + dy*dy)
                    
                    if distance < radius - 15:  # Account for element size
                        return cut_element.element_id
        
        return None
    
    def sync_to_egi(self):
        """Synchronize diagram to EGI representation."""
        try:
            diagram = self.build_diagram_representation()
            self.current_egi = self.correspondence.diagram_to_egi(diagram)
            self.update_transformation_buttons()
            self.status_var.set("Synchronized to EGI - transformations enabled")
        except Exception as e:
            messagebox.showerror("Sync Error", f"Failed to sync to EGI: {e}")
            self.status_var.set("Sync failed")
    
    def update_transformation_buttons(self):
        """Update transformation button states based on current context."""
        if not self.current_egi:
            # Disable all buttons if no EGI
            for btn in self.transform_buttons.values():
                btn.configure(state="disabled")
            return
        
        # Determine current logical context and polarity
        polarity = self.get_current_polarity()
        
        # Enable/disable buttons based on context
        for rule_name, btn in self.transform_buttons.items():
            if rule_name == "IT+":
                # Iteration can always be applied
                btn.configure(state="normal")
            elif rule_name == "IT-":
                # Deiteration requires existing vertices
                btn.configure(state="normal" if len(self.current_egi.V) > 0 else "disabled")
            elif rule_name == "DC+":
                # Double cut insertion can always be applied
                btn.configure(state="normal")
            elif rule_name == "DC-":
                # Double cut erasure requires existing double cuts
                btn.configure(state="normal" if len(self.current_egi.Cut) >= 2 else "disabled")
            elif rule_name == "INS":
                # Insertion only in negative areas
                btn.configure(state="normal" if polarity == AreaPolarity.NEGATIVE else "disabled")
            elif rule_name == "ERA":
                # Erasure only in positive areas with content
                has_content = len(self.current_egi.V) > 0 or len(self.current_egi.E) > 0
                btn.configure(state="normal" if polarity == AreaPolarity.POSITIVE and has_content else "disabled")
    
    def get_current_polarity(self) -> AreaPolarity:
        """Determine the polarity of the current context."""
        # For now, assume sheet is positive
        # In full implementation, this would check the selected area
        if self.current_context == "sheet":
            return AreaPolarity.POSITIVE
        else:
            # Count nesting depth to determine polarity
            # Even depth = positive, odd depth = negative
            depth = self.get_context_depth()
            return AreaPolarity.POSITIVE if depth % 2 == 0 else AreaPolarity.NEGATIVE
    
    def get_context_depth(self) -> int:
        """Get the nesting depth of the current context."""
        # Simplified - just return 0 for sheet, 1 for any cut
        return 0 if self.current_context == "sheet" else 1
    
    def apply_transformation(self, rule_name: str):
        """Apply the specified transformation rule."""
        if not self.current_egi:
            messagebox.showwarning("No EGI", "Please sync to EGI first")
            return
        
        try:
            rule = self.transformation_rules[rule_name]
            
            # Create transformation context
            context = TransformationContext(
                source_egi=self.current_egi,
                target_area=self.current_context,
                polarity=self.get_current_polarity(),
                selected_elements=list(self.selected_elements),
                metadata={"rule_name": rule_name}
            )
            
            # Apply transformation
            result = rule.apply_transformation(context)
            
            if result.success:
                # Update EGI
                self.current_egi = result.transformed_egi
                
                # Reconstruct diagram from EGI
                self.reconstruct_diagram_from_egi()
                
                # Update UI
                self.update_transformation_buttons()
                self.status_var.set(f"Applied {rule_name}: {result.explanation}")
                
                messagebox.showinfo("Transformation Applied", 
                                   f"{rule_name} transformation successful:\n{result.explanation}")
            else:
                messagebox.showerror("Transformation Failed", 
                                    f"Cannot apply {rule_name}:\n{result.error_message}")
                self.status_var.set(f"Transformation {rule_name} failed")
                
        except Exception as e:
            messagebox.showerror("Error", f"Transformation error: {e}")
            self.status_var.set("Transformation error")
    
    def reconstruct_diagram_from_egi(self):
        """Reconstruct the visual diagram from the current EGI."""
        try:
            # Clear current diagram
            for element in list(self.elements.values()):
                for item_id in element.canvas_items:
                    self.canvas.delete(item_id)
            self.elements.clear()
            self.selected_elements.clear()
            
            # Reconstruct from EGI
            diagram = self.correspondence.egi_to_diagram(self.current_egi)
            
            # Recreate visual elements
            self.recreate_visual_elements(diagram)
            
            self.status_var.set("Diagram reconstructed from EGI")
            
        except Exception as e:
            messagebox.showerror("Reconstruction Error", f"Failed to reconstruct diagram: {e}")
    
    def recreate_visual_elements(self, diagram: DiagramRepresentation):
        """Recreate visual elements from diagram representation."""
        # Layout parameters
        base_x, base_y = 400, 300
        vertex_spacing = 80
        cut_radius = 60
        
        # Create vertices
        vertex_positions = {}
        for i, (vertex_id, vertex_spot) in enumerate(diagram.vertex_spots.items()):
            # Simple grid layout
            x = base_x + (i % 4) * vertex_spacing
            y = base_y + (i // 4) * vertex_spacing
            
            self.create_vertex_at_position(vertex_id, x, y)
            vertex_positions[vertex_id] = (x, y)
        
        # Create cuts
        for i, (cut_id, cut_line) in enumerate(diagram.cut_lines.items()):
            # Position cuts around vertices they contain
            contained_vertices = diagram.containment.get(cut_id, set())
            if contained_vertices:
                # Calculate center of contained vertices
                positions = [vertex_positions.get(v) for v in contained_vertices if v in vertex_positions]
                if positions:
                    avg_x = sum(pos[0] for pos in positions) / len(positions)
                    avg_y = sum(pos[1] for pos in positions) / len(positions)
                    self.create_cut_at_position(cut_id, avg_x, avg_y, cut_radius + 20)
                else:
                    # Default position
                    x = base_x + 200 + i * 100
                    y = base_y + 100
                    self.create_cut_at_position(cut_id, x, y, cut_radius)
            else:
                # Default position for empty cuts
                x = base_x + 200 + i * 100
                y = base_y + 100
                self.create_cut_at_position(cut_id, x, y, cut_radius)
        
        # Create edges
        for edge_id, edge_info in diagram.edge_lines.items():
            start_vertex = edge_info["start_vertex"]
            end_vertex = edge_info["end_vertex"]
            
            if start_vertex in vertex_positions and end_vertex in vertex_positions:
                self.create_edge_at_positions(
                    edge_id, 
                    vertex_positions[start_vertex],
                    vertex_positions[end_vertex],
                    start_vertex,
                    end_vertex
                )
    
    def create_vertex_at_position(self, vertex_id: str, x: float, y: float):
        """Create a vertex at a specific position with given ID."""
        # Draw vertex circle
        circle = self.canvas.create_oval(
            x - 12, y - 12, x + 12, y + 12,
            fill="lightblue", outline="blue", width=2
        )
        
        # Draw label
        label = self.canvas.create_text(
            x, y + 25, text=vertex_id, 
            font=("Arial", 10), fill="black"
        )
        
        # Create element
        element = Element(
            element_id=vertex_id,
            element_type="vertex",
            x=x, y=y,
            canvas_items=[circle, label]
        )
        
        self.elements[vertex_id] = element
    
    def create_cut_at_position(self, cut_id: str, center_x: float, center_y: float, radius: float):
        """Create a cut at a specific position with given ID."""
        # Draw cut circle
        circle = self.canvas.create_oval(
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius,
            outline="red", width=3, fill="lightgray"
        )
        
        # Create element
        element = Element(
            element_id=cut_id,
            element_type="cut",
            x=center_x, y=center_y,
            canvas_items=[circle]
        )
        
        self.elements[cut_id] = element
    
    def handle_edge_click(self, clicked_element: Element):
        """Handle clicking on vertices when in edge mode."""
        if not self.edge_start_element:
            # Start edge creation
            self.edge_start_element = clicked_element.element_id
            self.select_element(clicked_element.element_id)
            self.status_var.set(f"Edge started from {clicked_element.element_id}. Click target vertex.")
        else:
            # Complete edge creation
            if clicked_element.element_id != self.edge_start_element:
                self.create_edge(self.edge_start_element, clicked_element.element_id)
            self.cancel_edge_creation()
    
    def update_edge_preview(self, x: float, y: float):
        """Update edge preview line during creation."""
        if self.edge_start_element and self.edge_start_element in self.elements:
            # Remove old preview
            if self.edge_preview_line:
                self.canvas.delete(self.edge_preview_line)
            
            # Get start element position
            start_element = self.elements[self.edge_start_element]
            
            # Draw preview line
            self.edge_preview_line = self.canvas.create_line(
                start_element.x, start_element.y, x, y,
                fill="gray", width=2, dash=(5, 5),
                tags="edge_preview"
            )
    
    def cancel_edge_creation(self):
        """Cancel current edge creation."""
        if self.edge_preview_line:
            self.canvas.delete(self.edge_preview_line)
            self.edge_preview_line = None
        
        if self.edge_start_element:
            self.deselect_element(self.edge_start_element)
            self.edge_start_element = None
        
        if self.current_tool == "edge":
            self.status_var.set("Click vertices to connect with edges")
    
    def create_edge(self, start_vertex_id: str, end_vertex_id: str) -> str:
        """Create an edge between two vertices."""
        edge_id = f"e{self.element_counter}"
        self.element_counter += 1
        
        start_element = self.elements[start_vertex_id]
        end_element = self.elements[end_vertex_id]
        
        # Draw edge line
        line = self.canvas.create_line(
            start_element.x, start_element.y,
            end_element.x, end_element.y,
            fill="black", width=2, arrow=tk.LAST
        )
        
        # Create edge element
        edge = Element(
            element_id=edge_id,
            element_type="edge",
            x=(start_element.x + end_element.x) / 2,
            y=(start_element.y + end_element.y) / 2,
            canvas_items=[line]
        )
        
        # Store edge metadata
        edge.start_vertex = start_vertex_id
        edge.end_vertex = end_vertex_id
        
        self.elements[edge_id] = edge
        self.status_var.set(f"Created edge: {edge_id} from {start_vertex_id} to {end_vertex_id}")
        
        # Validate after creation
        self.validate_diagram_realtime()
        
        return edge_id
    
    def validate_diagram_realtime(self):
        """Perform real-time validation with visual feedback."""
        # Clear previous validation overlays
        self.clear_validation_overlays()
        
        try:
            diagram = self.build_diagram_representation()
            self.correspondence.validate_diagram_constraints(diagram)
            
            # Validation passed
            self.validation_var.set("Valid")
            self.validation_label.configure(background="lightgreen")
            self.last_validation_result = None
            
        except ConstraintViolation as e:
            # Validation failed - show specific feedback
            self.validation_var.set("Invalid")
            self.validation_label.configure(background="lightcoral")
            self.last_validation_result = str(e)
            
            # Add visual indicators for specific violations
            self.highlight_constraint_violations(str(e))
            
        except Exception as e:
            # Other validation errors
            self.validation_var.set("Error")
            self.validation_label.configure(background="orange")
            self.last_validation_result = f"Validation error: {e}"
    
    def clear_validation_overlays(self):
        """Clear all validation overlay graphics."""
        for overlay_id in self.validation_overlays:
            self.canvas.delete(overlay_id)
        self.validation_overlays.clear()
    
    def highlight_constraint_violations(self, error_message: str):
        """Add visual highlights for constraint violations."""
        # Parse error message to identify specific violations
        if "dominating nodes" in error_message.lower():
            self.highlight_dominating_nodes_violations()
        elif "n-ary relation" in error_message.lower():
            self.highlight_nary_relation_violations()
        else:
            # General violation - highlight all elements with warning color
            self.highlight_general_violations()
    
    def highlight_dominating_nodes_violations(self):
        """Highlight elements involved in dominating nodes violations."""
        # Find relations and vertices that violate dominating nodes constraint
        for element in self.elements.values():
            if element.element_type == "edge":
                # Check if this edge violates dominating nodes
                start_vertex = self.elements.get(element.start_vertex)
                end_vertex = self.elements.get(element.end_vertex)
                
                if start_vertex and end_vertex:
                    # Check containment contexts
                    edge_cut = self.find_containing_cut(element)
                    start_cut = self.find_containing_cut(start_vertex)
                    end_cut = self.find_containing_cut(end_vertex)
                    
                    # Simplified check - highlight if vertices are in different contexts
                    if start_cut != end_cut or edge_cut != start_cut:
                        self.add_violation_highlight(element, "red")
                        if start_vertex:
                            self.add_violation_highlight(start_vertex, "orange")
                        if end_vertex:
                            self.add_violation_highlight(end_vertex, "orange")
    
    def highlight_nary_relation_violations(self):
        """Highlight n-ary relation constraint violations."""
        # Count edges per relation and highlight violations
        relation_edge_counts = {}
        
        for element in self.elements.values():
            if element.element_type == "edge":
                # For now, treat each edge as a binary relation
                # In full implementation, would group by actual relation signs
                relation_id = f"rel_{element.element_id}"
                if relation_id not in relation_edge_counts:
                    relation_edge_counts[relation_id] = 0
                relation_edge_counts[relation_id] += 1
        
        # Highlight relations with incorrect arity (simplified check)
        for element in self.elements.values():
            if element.element_type == "edge":
                relation_id = f"rel_{element.element_id}"
                if relation_edge_counts.get(relation_id, 0) != 2:  # Binary relations should have exactly 2 connections
                    self.add_violation_highlight(element, "purple")
    
    def highlight_general_violations(self):
        """Add general violation highlights to all elements."""
        for element in self.elements.values():
            self.add_violation_highlight(element, "yellow")
    
    def add_violation_highlight(self, element: Element, color: str):
        """Add a colored highlight around an element to indicate violation."""
        if element.element_type == "vertex":
            # Add warning circle around vertex
            highlight = self.canvas.create_oval(
                element.x - 18, element.y - 18,
                element.x + 18, element.y + 18,
                outline=color, width=3, dash=(3, 3)
            )
            self.validation_overlays.append(highlight)
            
        elif element.element_type == "cut":
            # Add warning outline around cut
            # Get cut bounds from existing canvas item
            if element.canvas_items:
                coords = self.canvas.coords(element.canvas_items[0])
                if len(coords) >= 4:
                    x1, y1, x2, y2 = coords
                    highlight = self.canvas.create_oval(
                        x1 - 5, y1 - 5, x2 + 5, y2 + 5,
                        outline=color, width=4, dash=(5, 5)
                    )
                    self.validation_overlays.append(highlight)
                    
        elif element.element_type == "edge":
            # Add warning indicators at edge endpoints
            if hasattr(element, 'start_vertex') and hasattr(element, 'end_vertex'):
                start_elem = self.elements.get(element.start_vertex)
                end_elem = self.elements.get(element.end_vertex)
                
                if start_elem:
                    highlight = self.canvas.create_oval(
                        start_elem.x - 8, start_elem.y - 8,
                        start_elem.x + 8, start_elem.y + 8,
                        outline=color, width=2, fill=color
                    )
                    self.validation_overlays.append(highlight)
                    
                if end_elem:
                    highlight = self.canvas.create_oval(
                        end_elem.x - 8, end_elem.y - 8,
                        end_elem.x + 8, end_elem.y + 8,
                        outline=color, width=2, fill=color
                    )
                    self.validation_overlays.append(highlight)
    
    def show_validation_tooltip(self, event):
        """Show detailed validation information on hover."""
        if self.last_validation_result:
            # Create tooltip window
            tooltip = tk.Toplevel(self.master)
            tooltip.wm_overrideredirect(True)
            tooltip.geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
            
            label = tk.Label(tooltip, text=self.last_validation_result,
                           background="lightyellow", relief="solid", borderwidth=1,
                           wraplength=300, justify="left")
            label.pack()
            
            # Auto-hide after 3 seconds
            tooltip.after(3000, tooltip.destroy)


def main():
    """Run the simple diagram editor."""
    root = tk.Tk()
    app = SimpleDiagramEditor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
