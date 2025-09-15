#!/usr/bin/env python3
"""
Basic diagram editor prototype for Dau-compliant EGI diagrams.
Implements core canvas functionality with constraint validation.
"""

import json
import math
import os

# Import our core components
import sys
import tkinter as tk
from dataclasses import dataclass
from enum import Enum
from tkinter import filedialog, messagebox, ttk
from typing import Dict, List, Optional, Set, Tuple

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from dau_diagram_correspondence import (
    ConstraintViolation,
    CutLine,
    DauDiagramCorrespondence,
    DiagramRepresentation,
    EdgeLine,
    RelationSign,
    VertexSpot,
)
from egi_core_dau import RelationalGraphWithCuts
from interactive_transformer_with_history import InteractiveTransformerWithHistory


class ElementType(Enum):
    VERTEX = "vertex"
    RELATION = "relation"
    CUT = "cut"
    EDGE = "edge"


@dataclass
class CanvasElement:
    """Visual element on the canvas."""

    element_id: str
    element_type: ElementType
    x: float
    y: float
    width: float = 20
    height: float = 20
    selected: bool = False
    canvas_id: Optional[int] = None  # Tkinter canvas object ID


@dataclass
class VertexElement(CanvasElement):
    """Visual vertex element."""

    label: str = ""
    is_generic: bool = True

    def __post_init__(self):
        self.element_type = ElementType.VERTEX


@dataclass
class RelationElement(CanvasElement):
    """Visual relation element."""

    relation_name: str = ""
    arity: int = 1

    def __post_init__(self):
        self.element_type = ElementType.RELATION


@dataclass
class EdgeElement(CanvasElement):
    """Visual edge element."""

    relation_id: str = ""
    vertex_id: str = ""
    position_number: int = 1

    def __post_init__(self):
        self.element_type = ElementType.EDGE


@dataclass
class CutElement(CanvasElement):
    """Visual cut element."""

    radius: float = 50

    def __post_init__(self):
        self.element_type = ElementType.CUT


class DiagramEditor:
    """Main diagram editor interface."""

    def __init__(self, master):
        self.master = master
        self.master.title("Arisbe - EGI Diagram Editor")
        self.master.geometry("1200x800")

        # Core components
        self.correspondence = DauDiagramCorrespondence()
        self.transformer = InteractiveTransformerWithHistory()

        # Canvas state
        self.elements: Dict[str, CanvasElement] = {}
        self.selected_elements: Set[str] = set()
        self.current_tool = ElementType.VERTEX
        self.element_counter = 0
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0

        # Logical context - make explicit what we're viewing
        self.current_context = "sheet"  # "sheet" or cut_id
        self.context_polarity = "positive"  # "positive" or "negative"
        self.context_nesting_depth = 0

        # UI state
        self.drag_data = {"x": 0, "y": 0, "item": None}

        self.setup_ui()
        self.bind_events()
        self.draw_context_background()
        self.update_transformation_buttons()

    def setup_ui(self):
        """Create the user interface."""
        # Main frame
        main_frame = ttk.Frame(self.master)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Toolbar
        self.create_toolbar(main_frame)

        # Canvas frame
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        # Canvas with scrollbars
        self.canvas = tk.Canvas(
            canvas_frame, bg="white", scrollregion=(0, 0, 2000, 2000)
        )

        h_scrollbar = ttk.Scrollbar(
            canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview
        )
        v_scrollbar = ttk.Scrollbar(
            canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview
        )

        self.canvas.configure(
            xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set
        )

        # Pack scrollbars and canvas
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Status bar with context indicator
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Click to add vertices")
        status_bar = ttk.Label(
            status_frame, textvariable=self.status_var, relief=tk.SUNKEN
        )
        status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Context indicator
        self.context_var = tk.StringVar()
        self.update_context_display()
        context_label = ttk.Label(
            status_frame,
            textvariable=self.context_var,
            relief=tk.SUNKEN,
            background="lightblue",
        )
        context_label.pack(side=tk.RIGHT, padx=(5, 0))

        # Properties panel
        self.create_properties_panel(main_frame)

    def create_toolbar(self, parent):
        """Create the toolbar with tools and actions."""
        toolbar = ttk.Frame(parent)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # Tool selection
        ttk.Label(toolbar, text="Tool:").pack(side=tk.LEFT, padx=(0, 5))

        self.tool_var = tk.StringVar(value=ElementType.VERTEX.value)
        tools = [
            (ElementType.VERTEX.value, "Vertex"),
            (ElementType.RELATION.value, "Relation"),
            (ElementType.CUT.value, "Cut"),
            (ElementType.EDGE.value, "Edge"),
        ]

        for value, text in tools:
            ttk.Radiobutton(
                toolbar,
                text=text,
                variable=self.tool_var,
                value=value,
                command=self.on_tool_changed,
            ).pack(side=tk.LEFT, padx=5)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(
            side=tk.LEFT, fill=tk.Y, padx=10
        )

        # Actions
        ttk.Button(toolbar, text="Validate", command=self.validate_diagram).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(toolbar, text="Clear", command=self.clear_canvas).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(toolbar, text="Export", command=self.export_diagram).pack(
            side=tk.LEFT, padx=5
        )

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(
            side=tk.LEFT, fill=tk.Y, padx=10
        )

        # Transformations - dynamically enabled based on context
        ttk.Label(toolbar, text="Transform:").pack(side=tk.LEFT, padx=(0, 5))
        self.transform_buttons = {}

        self.transform_buttons["IT+"] = ttk.Button(
            toolbar, text="IT+", command=lambda: self.apply_transformation("IT+")
        )
        self.transform_buttons["IT+"].pack(side=tk.LEFT, padx=2)

        self.transform_buttons["IT-"] = ttk.Button(
            toolbar, text="IT-", command=lambda: self.apply_transformation("IT-")
        )
        self.transform_buttons["IT-"].pack(side=tk.LEFT, padx=2)

        self.transform_buttons["DC+"] = ttk.Button(
            toolbar, text="DC+", command=lambda: self.apply_transformation("DC+")
        )
        self.transform_buttons["DC+"].pack(side=tk.LEFT, padx=2)

        self.transform_buttons["DC-"] = ttk.Button(
            toolbar, text="DC-", command=lambda: self.apply_transformation("DC-")
        )
        self.transform_buttons["DC-"].pack(side=tk.LEFT, padx=2)

        self.transform_buttons["INS"] = ttk.Button(
            toolbar, text="INS", command=lambda: self.apply_transformation("INS")
        )
        self.transform_buttons["INS"].pack(side=tk.LEFT, padx=2)

        self.transform_buttons["ERA"] = ttk.Button(
            toolbar, text="ERA", command=lambda: self.apply_transformation("ERA")
        )
        self.transform_buttons["ERA"].pack(side=tk.LEFT, padx=2)

        # Update button states based on context
        self.update_transformation_buttons()

    def create_properties_panel(self, parent):
        """Create properties panel for selected elements."""
        self.properties_frame = ttk.LabelFrame(parent, text="Properties")
        self.properties_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

        # Will be populated based on selection
        self.properties_widgets = {}

    def bind_events(self):
        """Bind canvas events."""
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        # self.canvas.bind("<Button-3>", self.on_canvas_right_click)  # Right click for context menu - TODO

        # Keyboard shortcuts
        self.master.bind("<Delete>", self.delete_selected)
        self.master.bind("<Control-a>", self.select_all)
        self.master.bind("<Control-z>", lambda e: self.undo())
        self.master.bind("<Control-y>", lambda e: self.redo())

        self.master.focus_set()  # Enable keyboard events

    def on_tool_changed(self):
        """Handle tool selection change."""
        self.current_tool = ElementType(self.tool_var.get())
        tool_messages = {
            ElementType.VERTEX: "Click to add vertices",
            ElementType.RELATION: "Click to add relations",
            ElementType.CUT: "Click and drag to draw cuts",
            ElementType.EDGE: "Click relation, then vertex to connect",
        }
        self.status_var.set(
            f"Tool: {self.current_tool.value.title()} - {tool_messages[self.current_tool]}"
        )

    def on_canvas_click(self, event):
        """Handle canvas click events."""
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)

        # Check if clicking on existing element
        closest_items = self.canvas.find_closest(x, y)
        clicked_element = None
        if closest_items:
            clicked_item = closest_items[0]
            clicked_element = self.find_element_by_canvas_id(clicked_item)

        if clicked_element:
            self.handle_element_click(clicked_element, event)
        else:
            self.handle_empty_click(x, y, event)

    def handle_element_click(self, element: CanvasElement, event):
        """Handle clicking on an existing element."""
        if event.state & 0x4:  # Ctrl key held
            # Multi-select
            if element.element_id in self.selected_elements:
                self.deselect_element(element.element_id)
            else:
                self.select_element(element.element_id)
        else:
            # Single select
            self.clear_selection()
            self.select_element(element.element_id)

        # Start drag
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        self.drag_data["item"] = element.element_id

    def handle_empty_click(self, x: float, y: float, event):
        """Handle clicking on empty canvas."""
        if not (event.state & 0x4):  # Ctrl not held
            self.clear_selection()

        # Create new element based on current tool
        if self.current_tool == ElementType.VERTEX:
            self.create_vertex(x, y)
        elif self.current_tool == ElementType.RELATION:
            self.create_relation(x, y)
        elif self.current_tool == ElementType.CUT:
            self.start_cut_creation(x, y)

    def create_vertex(self, x: float, y: float) -> str:
        """Create a new vertex at the given position."""
        element_id = f"vertex_{self.element_counter}"
        self.element_counter += 1

        vertex = VertexElement(
            element_id=element_id,
            element_type=ElementType.VERTEX,
            x=x,
            y=y,
            label=f"v{len([e for e in self.elements.values() if e.element_type == ElementType.VERTEX])}",
        )

        # Draw on canvas - create as a group
        canvas_id = self.canvas.create_oval(
            x - 10,
            y - 10,
            x + 10,
            y + 10,
            fill="lightblue",
            outline="blue",
            width=2,
            tags=f"element_{element_id}",
        )

        # Add label - same tag for grouping
        label_id = self.canvas.create_text(
            x,
            y + 25,
            text=vertex.label,
            font=("Arial", 10),
            tags=f"element_{element_id}",
        )

        vertex.canvas_id = canvas_id
        vertex.label_id = label_id
        self.elements[element_id] = vertex

        self.status_var.set(f"Created vertex: {vertex.label}")
        return element_id

    def create_relation(self, x: float, y: float) -> str:
        """Create a new relation at the given position."""
        element_id = f"relation_{self.element_counter}"
        self.element_counter += 1

        relation = RelationElement(
            element_id=element_id,
            element_type=ElementType.RELATION,
            x=x,
            y=y,
            relation_name="R",
            arity=2,
        )

        # Draw on canvas
        canvas_id = self.canvas.create_rectangle(
            x - 15,
            y - 10,
            x + 15,
            y + 10,
            fill="lightgreen",
            outline="darkgreen",
            width=2,
        )

        # Add label
        label_id = self.canvas.create_text(
            x, y, text=relation.relation_name, font=("Arial", 10, "bold")
        )

        relation.canvas_id = canvas_id
        self.elements[element_id] = relation

        self.status_var.set(f"Created relation: {relation.relation_name}")
        return element_id

    def start_cut_creation(self, x: float, y: float):
        """Start creating a cut (will be completed on drag)."""
        self.cut_start_x = x
        self.cut_start_y = y
        self.status_var.set("Drag to create cut boundary")

    def on_canvas_drag(self, event):
        """Handle canvas drag events."""
        if self.drag_data["item"]:
            # Dragging existing element
            dx = event.x - self.drag_data["x"]
            dy = event.y - self.drag_data["y"]

            element = self.elements[self.drag_data["item"]]

            # Move all canvas items with this element's tag (vertex + label together)
            self.canvas.move(f"element_{element.element_id}", dx, dy)

            element.x += dx
            element.y += dy

            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y
        elif self.current_tool == ElementType.CUT and hasattr(self, "cut_start_x"):
            # Creating cut - show preview
            x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
            radius = math.sqrt(
                (x - self.cut_start_x) ** 2 + (y - self.cut_start_y) ** 2
            )

            # Remove previous preview
            if hasattr(self, "cut_preview_id"):
                self.canvas.delete(self.cut_preview_id)

            # Draw preview
            self.cut_preview_id = self.canvas.create_oval(
                self.cut_start_x - radius,
                self.cut_start_y - radius,
                self.cut_start_x + radius,
                self.cut_start_y + radius,
                outline="red",
                width=2,
                fill="",
                dash=(5, 5),
            )

    def on_canvas_release(self, event):
        """Handle canvas release events."""
        if self.current_tool == ElementType.CUT and hasattr(self, "cut_start_x"):
            # Complete cut creation
            x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
            radius = math.sqrt(
                (x - self.cut_start_x) ** 2 + (y - self.cut_start_y) ** 2
            )

            if radius > 20:  # Minimum cut size
                self.create_cut(self.cut_start_x, self.cut_start_y, radius)

            # Clean up
            if hasattr(self, "cut_preview_id"):
                self.canvas.delete(self.cut_preview_id)
                delattr(self, "cut_preview_id")
            delattr(self, "cut_start_x")
            delattr(self, "cut_start_y")

        # Reset drag data
        self.drag_data = {"x": 0, "y": 0, "item": None}

    def create_cut(self, center_x: float, center_y: float, radius: float) -> str:
        """Create a cut with the given center and radius."""
        element_id = f"cut_{self.element_counter}"
        self.element_counter += 1

        cut = CutElement(
            element_id=element_id,
            element_type=ElementType.CUT,
            x=center_x,
            y=center_y,
            radius=radius,
        )

        # Draw on canvas
        canvas_id = self.canvas.create_oval(
            center_x - radius,
            center_y - radius,
            center_x + radius,
            center_y + radius,
            outline="red",
            width=3,
            fill="",
        )

        cut.canvas_id = canvas_id
        self.elements[element_id] = cut

        self.status_var.set(f"Created cut with radius {radius:.1f}")
        return element_id

    def find_element_by_canvas_id(self, canvas_id: int) -> Optional[CanvasElement]:
        """Find element by its canvas ID."""
        for element in self.elements.values():
            if element.canvas_id == canvas_id:
                return element
        return None

    def select_element(self, element_id: str):
        """Select an element."""
        if element_id in self.elements:
            self.selected_elements.add(element_id)
            element = self.elements[element_id]
            element.selected = True

            # Visual feedback
            self.canvas.itemconfig(element.canvas_id, width=4)

            self.update_properties_panel()

    def deselect_element(self, element_id: str):
        """Deselect an element."""
        if element_id in self.selected_elements:
            self.selected_elements.remove(element_id)
            element = self.elements[element_id]
            element.selected = False

            # Remove visual feedback
            self.canvas.itemconfig(element.canvas_id, width=2)

            self.update_properties_panel()

    def clear_selection(self):
        """Clear all selections."""
        for element_id in list(self.selected_elements):
            self.deselect_element(element_id)

    def update_properties_panel(self):
        """Update the properties panel based on selection."""
        # Clear existing widgets
        for widget in self.properties_widgets.values():
            if hasattr(widget, "destroy"):
                widget.destroy()
        self.properties_widgets.clear()

        if not self.selected_elements:
            ttk.Label(self.properties_frame, text="No selection").pack(pady=10)
            return

        if len(self.selected_elements) == 1:
            element_id = next(iter(self.selected_elements))
            element = self.elements[element_id]
            self.create_element_properties(element)
        else:
            ttk.Label(
                self.properties_frame,
                text=f"{len(self.selected_elements)} elements selected",
            ).pack(pady=10)

    def create_element_properties(self, element: CanvasElement):
        """Create property widgets for a single element."""
        ttk.Label(
            self.properties_frame,
            text=f"{element.element_type.value.title()}: {element.element_id}",
        ).pack(pady=5)

        if isinstance(element, VertexElement):
            # Label entry
            ttk.Label(self.properties_frame, text="Label:").pack()
            label_var = tk.StringVar(value=element.label)
            label_entry = ttk.Entry(self.properties_frame, textvariable=label_var)
            label_entry.pack(pady=2)

            # Generic checkbox
            generic_var = tk.BooleanVar(value=element.is_generic)
            ttk.Checkbutton(
                self.properties_frame, text="Generic", variable=generic_var
            ).pack(pady=2)

            self.properties_widgets["label"] = label_entry
            self.properties_widgets["generic"] = generic_var

        elif isinstance(element, RelationElement):
            # Relation name
            ttk.Label(self.properties_frame, text="Relation:").pack()
            name_var = tk.StringVar(value=element.relation_name)
            name_entry = ttk.Entry(self.properties_frame, textvariable=name_var)
            name_entry.pack(pady=2)

            # Arity
            ttk.Label(self.properties_frame, text="Arity:").pack()
            arity_var = tk.IntVar(value=element.arity)
            arity_spin = ttk.Spinbox(
                self.properties_frame, from_=1, to=10, textvariable=arity_var, width=10
            )
            arity_spin.pack(pady=2)

            self.properties_widgets["name"] = name_entry
            self.properties_widgets["arity"] = arity_var

    def validate_diagram(self):
        """Validate the current diagram against Dau constraints."""
        try:
            diagram = self.build_diagram_representation()
            self.correspondence.validate_diagram_constraints(diagram)
            messagebox.showinfo("Validation", "Diagram is valid!")
            self.status_var.set("Validation passed")
        except ConstraintViolation as e:
            messagebox.showerror("Validation Error", str(e))
            self.status_var.set(f"Validation failed: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Validation error: {e}")
            self.status_var.set(f"Error: {e}")

    def build_diagram_representation(self) -> DiagramRepresentation:
        """Build DiagramRepresentation from current canvas state."""
        vertex_spots = {}
        relation_signs = {}
        edge_lines = {}
        cut_lines = {}
        containment = {"sheet": set()}

        # Process vertices
        for element in self.elements.values():
            if isinstance(element, VertexElement):
                vertex_spots[element.element_id] = VertexSpot(
                    element_id=element.element_id,
                    label=element.label if not element.is_generic else None,
                    is_generic=element.is_generic,
                    containing_cut=self.find_containing_cut(element),
                )

        # Process relations
        for element in self.elements.values():
            if isinstance(element, RelationElement):
                relation_signs[element.element_id] = RelationSign(
                    element_id=element.element_id,
                    relation_name=element.relation_name,
                    arity=element.arity,
                    containing_cut=self.find_containing_cut(element),
                )

        # Process cuts
        for element in self.elements.values():
            if isinstance(element, CutElement):
                cut_lines[element.element_id] = CutLine(
                    element_id=element.element_id,
                    containing_cut=self.find_containing_cut(element),
                )

        # Build containment relationships
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
            containment=containment,
        )

    def find_containing_cut(self, element: CanvasElement) -> Optional[str]:
        """Find which cut contains the given element."""
        for cut_element in self.elements.values():
            if isinstance(cut_element, CutElement) and cut_element != element:
                # Check if element is inside cut
                dx = element.x - cut_element.x
                dy = element.y - cut_element.y
                distance = math.sqrt(dx * dx + dy * dy)

                if distance < cut_element.radius:
                    return cut_element.element_id

        return None

    def apply_transformation(self, transformation_type: str):
        """Apply a transformation to the selected elements."""
        if not self.selected_elements:
            messagebox.showwarning(
                "No Selection", "Please select elements to transform"
            )
            return

        try:
            # Convert current state to EGI
            diagram = self.build_diagram_representation()
            egi = self.correspondence.diagram_to_egi(diagram)

            # Apply transformation (simplified - would need proper transformation logic)
            self.status_var.set(f"Applied {transformation_type} transformation")

        except Exception as e:
            messagebox.showerror("Transformation Error", str(e))

    def clear_canvas(self):
        """Clear all elements from the canvas."""
        if messagebox.askyesno(
            "Clear Canvas", "Are you sure you want to clear all elements?"
        ):
            self.canvas.delete("all")
            self.elements.clear()
            self.selected_elements.clear()
            self.element_counter = 0
            self.status_var.set("Canvas cleared")

    def export_diagram(self):
        """Export the current diagram."""
        try:
            diagram = self.build_diagram_representation()

            # Export as JSON
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            )

            if filename:
                # Convert to exportable format
                export_data = {
                    "elements": {
                        eid: {
                            "type": elem.element_type.value,
                            "x": elem.x,
                            "y": elem.y,
                            **self.get_element_properties(elem),
                        }
                        for eid, elem in self.elements.items()
                    },
                    "diagram": self.diagram_to_dict(diagram),
                }

                with open(filename, "w") as f:
                    json.dump(export_data, f, indent=2)

                self.status_var.set(f"Exported to {filename}")

        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def get_element_properties(self, element: CanvasElement) -> dict:
        """Get element-specific properties for export."""
        if isinstance(element, VertexElement):
            return {"label": element.label, "is_generic": element.is_generic}
        elif isinstance(element, RelationElement):
            return {"relation_name": element.relation_name, "arity": element.arity}
        elif isinstance(element, CutElement):
            return {"radius": element.radius}
        return {}

    def diagram_to_dict(self, diagram: DiagramRepresentation) -> dict:
        """Convert diagram to dictionary for export."""
        return {
            "sheet_id": diagram.sheet_id,
            "vertex_spots": {
                k: {
                    "element_id": v.element_id,
                    "label": v.label,
                    "is_generic": v.is_generic,
                    "containing_cut": v.containing_cut,
                }
                for k, v in diagram.vertex_spots.items()
            },
            "relation_signs": {
                k: {
                    "element_id": v.element_id,
                    "relation_name": v.relation_name,
                    "arity": v.arity,
                    "containing_cut": v.containing_cut,
                }
                for k, v in diagram.relation_signs.items()
            },
            "containment": {k: list(v) for k, v in diagram.containment.items()},
        }

    def delete_selected(self, event=None):
        """Delete selected elements."""
        if self.selected_elements:
            for element_id in list(self.selected_elements):
                element = self.elements[element_id]
                self.canvas.delete(element.canvas_id)
                del self.elements[element_id]

            self.selected_elements.clear()
            self.update_properties_panel()
            self.status_var.set("Deleted selected elements")

    def select_all(self, event=None):
        """Select all elements."""
        self.clear_selection()
        for element_id in self.elements:
            self.select_element(element_id)

    def undo(self):
        """Undo last operation."""
        # TODO: Implement undo functionality
        self.status_var.set("Undo not yet implemented")

    def redo(self):
        """Redo last undone operation."""
        # TODO: Implement redo functionality
        self.status_var.set("Redo not yet implemented")

    def update_context_display(self):
        """Update the context indicator to show current logical area."""
        if self.current_context == "sheet":
            context_text = f"Sheet of Assertion (Positive, Depth 0)"
        else:
            context_text = f"Cut {self.current_context} ({self.context_polarity.title()}, Depth {self.context_nesting_depth})"

        self.context_var.set(f"Context: {context_text}")

    def draw_context_background(self):
        """Draw visual indicators for the current logical context."""
        # Clear any existing background
        self.canvas.delete("context_bg")

        if self.current_context == "sheet":
            # Sheet of assertion - unshaded per Peirce's convention (positive/even area)
            self.canvas.create_rectangle(
                10,
                10,
                1990,
                1990,
                outline="darkblue",
                width=2,
                fill="",
                dash=(10, 5),
                tags="context_bg",
            )
            # Add corner label
            self.canvas.create_text(
                30,
                30,
                text="Sheet of Assertion (Positive)",
                font=("Arial", 12, "bold"),
                fill="darkblue",
                anchor="nw",
                tags="context_bg",
            )
        else:
            # Cut area - follow Peirce's shading convention
            if self.context_polarity == "positive":
                # Even-enclosed areas: unshaded
                bg_color = ""
                border_color = "blue"
            else:
                # Odd-enclosed areas: light gray shading per Peirce
                bg_color = "lightgray"
                border_color = "red"

            # Draw cut boundary
            self.canvas.create_oval(
                50,
                50,
                1950,
                1950,
                outline=border_color,
                width=3,
                fill=bg_color,
                tags="context_bg",
            )
            # Add context label
            self.canvas.create_text(
                100,
                100,
                text=f"Cut {self.current_context}\n{self.context_polarity.title()} Area\nDepth {self.context_nesting_depth}",
                font=("Arial", 10, "bold"),
                fill=border_color,
                anchor="nw",
                tags="context_bg",
            )

    def update_transformation_buttons(self):
        """Update transformation button states based on current context and constraints."""
        # Sheet of assertion rules: only vertex addition (IT+) and double cut (DC+)
        if self.current_context == "sheet":
            # Enable only IT+ (vertex addition) and DC+ (double cut insertion)
            self.transform_buttons["IT+"].configure(state="normal")
            self.transform_buttons["DC+"].configure(state="normal")

            # Disable all others on sheet
            self.transform_buttons["IT-"].configure(state="disabled")
            self.transform_buttons["DC-"].configure(state="disabled")
            self.transform_buttons["INS"].configure(state="disabled")
            self.transform_buttons["ERA"].configure(state="disabled")

        else:
            # In cut areas - enable based on polarity
            if self.context_polarity == "positive":
                # Positive areas: allow ERA (erasure), IT+, IT-, DC+, DC-
                self.transform_buttons["ERA"].configure(state="normal")
                self.transform_buttons["IT+"].configure(state="normal")
                self.transform_buttons["IT-"].configure(state="normal")
                self.transform_buttons["DC+"].configure(state="normal")
                self.transform_buttons["DC-"].configure(state="normal")

                # Disable INS in positive areas
                self.transform_buttons["INS"].configure(state="disabled")

            else:  # negative areas
                # Negative areas: allow INS (insertion), IT+, IT-, DC+, DC-
                self.transform_buttons["INS"].configure(state="normal")
                self.transform_buttons["IT+"].configure(state="normal")
                self.transform_buttons["IT-"].configure(state="normal")
                self.transform_buttons["DC+"].configure(state="normal")
                self.transform_buttons["DC-"].configure(state="normal")

                # Disable ERA in negative areas
                self.transform_buttons["ERA"].configure(state="disabled")


def main():
    """Run the diagram editor."""
    root = tk.Tk()
    app = DiagramEditor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
