#!/usr/bin/env python3
"""
Main Graphical User Interface for the Arisbe Existential Graphs application.

This application provides a GUI for creating, editing, and transforming
Existential Graphs, based on the detailed design in Front_End_description.md.
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# Ensure the src directory is in the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Local imports
from canvas_backend import create_backend
from diagram_canvas import DiagramCanvas
from egi_core_dau import RelationalGraphWithCuts, create_empty_graph, create_cut, create_vertex

class ArisbeGUI(tk.Tk):
    """Main application class for the Arisbe GUI."""

    def __init__(self):
        super().__init__()
        self.title("Arisbe - Existential Graphs")
        self.geometry("1200x800")
        
        # Initialize action-first workflow state
        self.current_action = None
        
        # Bind keyboard events for action execution
        self.bind('<Key>', self.on_key_press)
        self.focus_set()  # Allow root to receive key events

        # Drag-and-drop state
        self.drag_data = {"item": None, "x": 0, "y": 0}

        # Main container frame
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create the tabbed notebook
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Create the three main workspaces as tabs
        self.bullpen_tab = ttk.Frame(self.notebook)
        self.browser_tab = ttk.Frame(self.notebook)
        self.epg_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.bullpen_tab, text="The Bullpen / Practice Field")
        self.notebook.add(self.browser_tab, text="The Browser")
        self.notebook.add(self.epg_tab, text="The EPG Workspace")

        # Setup each tab
        self.setup_bullpen_tab()
        self.setup_browser_tab()
        self.setup_epg_tab()

        # Status Bar
        self.status_bar = tk.Label(self, text="Welcome to Arisbe.", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def setup_bullpen_tab(self):
        """Sets up the Bullpen/Practice Field workspace."""
        bullpen_frame = ttk.Frame(self.bullpen_tab)
        bullpen_frame.pack(fill=tk.BOTH, expand=True)

        # Element Palette
        palette_frame = ttk.LabelFrame(bullpen_frame, text="Element Palette", padding="10")
        palette_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # Action-First Workflow Instructions
        instructions_frame = ttk.LabelFrame(palette_frame, text="Action-First Workflow", padding="5")
        instructions_frame.pack(fill=tk.X, pady=5)
        
        instruction_text = ttk.Label(instructions_frame, text="1. Choose action\n2. Select as prompted", 
                                   font=('TkDefaultFont', 9), foreground='blue')
        instruction_text.pack()
        
        # Action Buttons (always enabled)
        actions_frame = ttk.LabelFrame(palette_frame, text="Actions", padding="5")
        actions_frame.pack(fill=tk.X, pady=5)
        
        self.cut_button = ttk.Button(actions_frame, text="Add Cut", command=self.start_add_cut_action)
        self.cut_button.pack(fill=tk.X, pady=2)
        
        self.individual_button = ttk.Button(actions_frame, text="Add Individual", command=self.start_add_individual_action)
        self.individual_button.pack(fill=tk.X, pady=2)

        self.predicate_button = ttk.Button(actions_frame, text="Add Predicate", command=self.start_add_predicate_action)
        self.predicate_button.pack(fill=tk.X, pady=2)
        
        self.delete_button = ttk.Button(actions_frame, text="Delete Elements", command=self.start_delete_action)
        self.delete_button.pack(fill=tk.X, pady=2)
        
        # Cancel Action button
        ttk.Button(actions_frame, text="Cancel Action", command=self.cancel_current_action).pack(fill=tk.X, pady=5)

        # Selection Status Display
        self.status_frame = ttk.LabelFrame(palette_frame, text="Selection Status", padding="5")
        self.status_frame.pack(pady=10, fill=tk.X)
        
        self.status_label = ttk.Label(self.status_frame, text="Ready", foreground="green")
        self.status_label.pack()
        
        self.instructions_label = ttk.Label(self.status_frame, text="", font=("TkDefaultFont", 8), wraplength=150)
        self.instructions_label.pack()

        # Note: Line of Identity is the same as Individual in Dau's formalism
        # Branching/connection happens when individuals are placed near each other

        # Main canvas area
        canvas_area = ttk.Frame(bullpen_frame)
        canvas_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Chiron (Linear Form Display) (placeholder)
        chiron_frame = ttk.Frame(canvas_area, height=100)
        chiron_frame.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Label(chiron_frame, text="Linear Form (EGIF/CLIF) will appear here.").pack()

        # Diagram Canvas
        # Use a sub-frame to ensure the canvas packs correctly before the chiron
        diagram_frame = ttk.Frame(canvas_area)
        diagram_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        # Initialize a backend and embed the DiagramCanvas
        try:
            print("Starting canvas initialization...")
            # Define canvas dimensions
            canvas_width = 1000
            canvas_height = 700
            print(f"Creating backend with dimensions {canvas_width}x{canvas_height}")
            # Create a simple example graph to display
            from egi_core_dau import create_empty_graph, create_cut, create_vertex
            example_graph = create_empty_graph()
            # Add a cut and a vertex to demonstrate the system
            cut = create_cut()
            example_graph = example_graph.with_cut(cut, example_graph.sheet)
            vertex = create_vertex()
            example_graph = example_graph.with_vertex(vertex)
            # Move the vertex into the cut
            new_area = dict(example_graph.area)
            # Remove vertex from sheet
            sheet_area = new_area[example_graph.sheet] - {vertex.id}
            new_area[example_graph.sheet] = sheet_area
            # Add vertex to cut
            cut_area = new_area[cut.id] | {vertex.id}
            new_area[cut.id] = cut_area
            # Create updated graph
            from frozendict import frozendict
            example_graph = RelationalGraphWithCuts(
                V=example_graph.V,
                E=example_graph.E,
                nu=example_graph.nu,
                sheet=example_graph.sheet,
                Cut=example_graph.Cut,
                area=frozendict(new_area),
                rel=example_graph.rel
            )
            print("Example graph created")
            # Create the canvas with embedded backend
            canvas_backend = create_backend("tkinter", width=canvas_width, height=canvas_height, master=diagram_frame)
            # Create DiagramCanvas with the embedded canvas
            self.diagram_canvas = DiagramCanvas(width=canvas_width, height=canvas_height, canvas=canvas_backend)
            print("DiagramCanvas created")
            # Set the graph and render it
            self.diagram_canvas.render_graph(example_graph)
            print("Canvas drawn")
            # DiagramCanvas handles its own events for selection - no need to override
            print("DiagramCanvas event handlers are set up automatically")
            
            # Connect canvas selection events to status display
            if hasattr(self.diagram_canvas, 'selection_manager') and self.diagram_canvas.selection_manager:
                self.diagram_canvas.selection_manager.on_selection_changed = self.update_selection_status
            
            print("Canvas events bound successfully")
        except Exception as e:
            print(f"Exception during canvas initialization: {e}")
            import traceback
            traceback.print_exc()
            error_label = ttk.Label(diagram_frame, text=f"Error initializing canvas: {e}")
            error_label.pack(pady=20)
    
    def update_selection_status(self, selection_state):
        """Update the GUI status display based on selection state"""
        try:
            if selection_state.context.value == "enclosing":
                self.status_label.config(text="SELECTION MODE", foreground="red")
                selected_count = len(selection_state.selected_elements)
                if selected_count == 0:
                    self.instructions_label.config(text="⌘-click elements to select them for enclosure. Press Enter to confirm or Escape to cancel.")
                else:
                    self.instructions_label.config(text=f"Selected: {selected_count} elements. ⌘-click more or press Enter to create enclosing cut.")
            else:
                self.status_label.config(text="Ready", foreground="green")
                self.instructions_label.config(text="")
        except Exception as e:
            print(f"Error updating selection status: {e}")
    
    def cancel_selection(self):
        """Cancel current selection mode and return to normal operation"""
        try:
            if hasattr(self.diagram_canvas, 'selection_manager') and self.diagram_canvas.selection_manager:
                self.diagram_canvas.exit_selection_mode()
                print("Selection mode canceled")
                # Update status display
                self.status_label.config(text="Ready", foreground="green")
                self.instructions_label.config(text="")
        except Exception as e:
            print(f"Error canceling selection: {e}")
    
    # Action-First Workflow Methods
    def start_add_cut_action(self):
        """Start the Add Cut action - prompts user to select elements to enclose"""
        try:
            self.current_action = "add_cut"
            if hasattr(self.diagram_canvas, 'selection_manager') and self.diagram_canvas.selection_manager:
                from selection_system import SelectionContext, SelectionMode
                self.diagram_canvas.selection_manager.set_context(SelectionContext.ENCLOSING, SelectionMode.MULTI)
                self.status_label.config(text="ADD CUT", foreground="red")
                self.instructions_label.config(text="⌘-click elements to enclose with cut, or drag to select area. Press Enter to create cut.")
                print("Started Add Cut action - select elements to enclose")
        except Exception as e:
            print(f"Error starting add cut action: {e}")
    
    def start_add_individual_action(self):
        """Start the Add Individual action - prompts user to select empty area"""
        try:
            self.current_action = "add_individual"
            if hasattr(self.diagram_canvas, 'selection_manager') and self.diagram_canvas.selection_manager:
                from selection_system import SelectionContext, SelectionMode
                self.diagram_canvas.selection_manager.set_context(SelectionContext.COMPOSITION, SelectionMode.SPATIAL)
                self.status_label.config(text="ADD INDIVIDUAL", foreground="green")
                self.instructions_label.config(text="Click and drag to select empty area for individual placement.")
                print("Started Add Individual action - select empty area")
        except Exception as e:
            print(f"Error starting add individual action: {e}")
    
    def start_add_predicate_action(self):
        """Start the Add Predicate action - prompts user to select empty area"""
        try:
            self.current_action = "add_predicate"
            if hasattr(self.diagram_canvas, 'selection_manager') and self.diagram_canvas.selection_manager:
                from selection_system import SelectionContext, SelectionMode
                self.diagram_canvas.selection_manager.set_context(SelectionContext.COMPOSITION, SelectionMode.SPATIAL)
                self.status_label.config(text="ADD PREDICATE", foreground="blue")
                self.instructions_label.config(text="Click and drag to select empty area for predicate placement.")
                print("Started Add Predicate action - select empty area")
        except Exception as e:
            print(f"Error starting add predicate action: {e}")
    
    def start_delete_action(self):
        """Start the Delete action - prompts user to select elements to delete"""
        try:
            self.current_action = "delete"
            if hasattr(self.diagram_canvas, 'selection_manager') and self.diagram_canvas.selection_manager:
                from selection_system import SelectionContext, SelectionMode
                self.diagram_canvas.selection_manager.set_context(SelectionContext.EDITING, SelectionMode.MULTI)
                self.status_label.config(text="DELETE ELEMENTS", foreground="red")
                self.instructions_label.config(text="⌘-click elements to delete. Press Enter to confirm deletion.")
                print("Started Delete action - select elements to delete")
        except Exception as e:
            print(f"Error starting delete action: {e}")
    
    def cancel_current_action(self):
        """Cancel the current action and return to ready state"""
        try:
            self.current_action = None
            if hasattr(self.diagram_canvas, 'selection_manager') and self.diagram_canvas.selection_manager:
                self.diagram_canvas.selection_manager.clear_selection()
            self.status_label.config(text="READY", foreground="black")
            self.instructions_label.config(text="Choose an action to begin.")
            print("Cancelled current action")
        except Exception as e:
            print(f"Error cancelling action: {e}")
    
    def clear_selection(self):
        """Clear current selection and return to ready state"""
        try:
            # Clear selection manager state
            if hasattr(self.diagram_canvas, 'selection_manager') and self.diagram_canvas.selection_manager:
                self.diagram_canvas.selection_manager.clear_selection()
            
            # Clear all visual selection indicators
            if hasattr(self.diagram_canvas, 'selection_rectangle'):
                self.diagram_canvas.selection_rectangle = None
            if hasattr(self.diagram_canvas, 'selected_element'):
                self.diagram_canvas.selected_element = None
            if hasattr(self.diagram_canvas, 'is_dragging_selection'):
                self.diagram_canvas.is_dragging_selection = False
            if hasattr(self.diagram_canvas, 'selection_start'):
                self.diagram_canvas.selection_start = None
            if hasattr(self.diagram_canvas, 'selection_current'):
                self.diagram_canvas.selection_current = None
            
            # Reset current action state
            self.current_action = None
            
            # Force complete visual refresh to remove all highlights/colors
            self.diagram_canvas._render_diagram()
            
            # Update GUI to ready state
            self.status_label.config(text="READY", foreground="black")
            self.instructions_label.config(text="Choose an action to begin.")
            
            print("Selection cleared and returned to ready state")
        except Exception as e:
            print(f"Error clearing selection: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_action_buttons(self, enabled: bool):
        """Enable or disable action buttons based on selection state"""
        state = 'normal' if enabled else 'disabled'
        self.cut_button.config(state=state)
        self.individual_button.config(state=state)
        self.predicate_button.config(state=state)
        self.delete_button.config(state=state)
    
    # Action Methods (operate on current selection)
    def add_cut_to_selection(self):
        """Add a cut around the currently selected elements"""
        try:
            if hasattr(self.diagram_canvas, 'selection_manager') and self.diagram_canvas.selection_manager:
                selected = self.diagram_canvas.selection_manager.state.selected_elements
                if selected:
                    print(f"Creating cut around {len(selected)} selected elements: {selected}")
                    # Calculate bounds around selected elements
                    bounds = self._calculate_selection_bounds(selected)
                    if bounds:
                        # Create cut with proper bounds around selection
                        self.diagram_canvas.add_enclosing_cut(selected, bounds)
                        print(f"Successfully added cut around selected elements")
                    else:
                        print("Could not calculate bounds for selected elements")
                    print(f"Successfully added cut around selected elements")
                    self.clear_selection()  # Clear selection after successful cut creation
                else:
                    print("No elements selected for cut creation")
        except Exception as e:
            print(f"Error adding cut to selection: {e}")
            import traceback
            traceback.print_exc()
    
    def add_individual_to_selection(self):
        """Add an individual to the selected area"""
        try:
            # Use selected area coordinates if available
            if hasattr(self.diagram_canvas, 'selection_rectangle') and self.diagram_canvas.selection_rectangle:
                x1, y1, x2, y2 = self.diagram_canvas.selection_rectangle
                # Place at center of selected area
                position = ((x1 + x2) / 2, (y1 + y2) / 2)
                print(f"Placing individual at selected area center: {position}")
            else:
                # Fallback to canvas center
                position = (self.diagram_canvas.width / 2, self.diagram_canvas.height / 2)
                print(f"No area selected, placing at canvas center: {position}")
            
            self.diagram_canvas.add_element("individual", position)
            print("Added individual to selected area")
        except Exception as e:
            print(f"Error adding individual to selection: {e}")
            import traceback
            traceback.print_exc()
    
    def add_predicate_to_selection(self):
        """Add a predicate to the selected area"""
        try:
            # Use selected area coordinates if available
            if hasattr(self.diagram_canvas, 'selection_rectangle') and self.diagram_canvas.selection_rectangle:
                x1, y1, x2, y2 = self.diagram_canvas.selection_rectangle
                # Place at center of selected area
                position = ((x1 + x2) / 2, (y1 + y2) / 2)
                print(f"Placing predicate at selected area center: {position}")
            else:
                # Fallback to canvas center
                position = (self.diagram_canvas.width / 2, self.diagram_canvas.height / 2)
                print(f"No area selected, placing at canvas center: {position}")
            
            self.diagram_canvas.add_element("predicate", position)
            print("Added predicate to selected area")
        except Exception as e:
            print(f"Error adding predicate to selection: {e}")
            import traceback
            traceback.print_exc()
    
    def delete_selection(self):
        """Delete the currently selected elements"""
        try:
            if hasattr(self.diagram_canvas, 'selection_manager') and self.diagram_canvas.selection_manager:
                selected = self.diagram_canvas.selection_manager.state.selected_elements
                if selected:
                    print(f"Deleting {len(selected)} selected elements: {selected}")
                    # Use proper deletion method that updates graph data structure
                    if hasattr(self.diagram_canvas, 'delete_elements'):
                        self.diagram_canvas.delete_elements(selected)
                    else:
                        # Fallback: call individual delete for each element
                        for element_id in selected:
                            if hasattr(self.diagram_canvas, 'delete_element'):
                                self.diagram_canvas.delete_element(element_id)
                            else:
                                print(f"Warning: No delete method available for element {element_id}")
                    
                    print(f"Successfully deleted {len(selected)} elements")
                else:
                    print("No elements selected for deletion")
        except Exception as e:
            print(f"Error deleting selection: {e}")
            import traceback
            traceback.print_exc()
    
    # Execute Methods for Action-First Workflow
    def execute_add_cut(self):
        """Execute the Add Cut action with current selection"""
        try:
            if hasattr(self.diagram_canvas, 'selection_manager') and self.diagram_canvas.selection_manager:
                selected = self.diagram_canvas.selection_manager.state.selected_elements
                if selected:
                    print(f"Creating cut around {len(selected)} selected elements: {selected}")
                    # Use existing add_cut_to_selection logic
                    self.add_cut_to_selection()
                else:
                    print("No elements selected for cut enclosure")
            self.clear_selection()  # Complete cleanup and return to ready state
        except Exception as e:
            print(f"Error executing add cut: {e}")
    
    def execute_add_individual(self):
        """Execute the Add Individual action with current area selection"""
        try:
            if hasattr(self.diagram_canvas, 'selection_rectangle') and self.diagram_canvas.selection_rectangle:
                # Use existing add_individual_to_selection logic
                self.add_individual_to_selection()
            else:
                print("No area selected for individual placement")
            self.clear_selection()  # Complete cleanup and return to ready state
        except Exception as e:
            print(f"Error executing add individual: {e}")
    
    def execute_add_predicate(self):
        """Execute the Add Predicate action with current area selection"""
        try:
            if hasattr(self.diagram_canvas, 'selection_rectangle') and self.diagram_canvas.selection_rectangle:
                # Use existing add_predicate_to_selection logic
                self.add_predicate_to_selection()
            else:
                print("No area selected for predicate placement")
            self.clear_selection()  # Complete cleanup and return to ready state
        except Exception as e:
            print(f"Error executing add predicate: {e}")
    
    def execute_delete(self):
        """Execute the Delete action with current element selection"""
        try:
            # Use existing delete_selection logic
            self.delete_selection()
            self.clear_selection()  # Complete cleanup and return to ready state
        except Exception as e:
            print(f"Error executing delete: {e}")
    
    def on_key_press(self, event):
        """Handle keyboard events for action execution"""
        try:
            if event.keysym == 'Return':  # Enter key
                print(f"Enter pressed - executing action: {getattr(self, 'current_action', None)}")
                if hasattr(self, 'current_action') and self.current_action:
                    if self.current_action == 'add_cut':
                        self.execute_add_cut()
                    elif self.current_action == 'add_individual':
                        self.execute_add_individual()
                    elif self.current_action == 'add_predicate':
                        self.execute_add_predicate()
                    elif self.current_action == 'delete':
                        self.execute_delete()
                else:
                    print("No current action to execute")
            elif event.keysym == 'Escape':
                print("Escape pressed - canceling action")
                self.cancel_current_action()
        except Exception as e:
            print(f"Error handling key press: {e}")
    
    def _calculate_selection_bounds(self, selected_elements):
        """Calculate bounding box around selected elements with padding for cut placement"""
        try:
            if not selected_elements or not hasattr(self.diagram_canvas, 'visual_elements'):
                return None
            
            # Find bounds of all selected elements
            min_x = min_y = float('inf')
            max_x = max_y = float('-inf')
            
            for element_id in selected_elements:
                if element_id in self.diagram_canvas.visual_elements:
                    visual_elem = self.diagram_canvas.visual_elements[element_id]
                    x, y = visual_elem.position
                    
                    # Add element-specific bounds
                    if hasattr(visual_elem, 'radius'):  # Vertex
                        radius = visual_elem.radius
                        min_x = min(min_x, x - radius)
                        max_x = max(max_x, x + radius)
                        min_y = min(min_y, y - radius)
                        max_y = max(max_y, y + radius)
                    elif hasattr(visual_elem, 'bounds'):  # Cut
                        bounds = visual_elem.bounds
                        min_x = min(min_x, bounds[0])
                        max_x = max(max_x, bounds[2])
                        min_y = min(min_y, bounds[1])
                        max_y = max(max_y, bounds[3])
                    else:  # Edge or other element
                        min_x = min(min_x, x - 10)
                        max_x = max(max_x, x + 10)
                        min_y = min(min_y, y - 10)
                        max_y = max(max_y, y + 10)
            
            # Add padding around selection for cut placement
            padding = 30
            return {
                'min_x': min_x - padding,
                'max_x': max_x + padding,
                'min_y': min_y - padding,
                'max_y': max_y + padding,
                'center_x': (min_x + max_x) / 2,
                'center_y': (min_y + max_y) / 2,
                'width': (max_x - min_x) + 2 * padding,
                'height': (max_y - min_y) + 2 * padding
            }
        except Exception as e:
            print(f"Error calculating selection bounds: {e}")
            return None

    def on_canvas_click(self, event):
        """Handle canvas click events - for testing"""
        print(f"Canvas clicked at ({event.x}, {event.y})")
        print(f"Current drag data: {self.drag_data}")

    def on_drop(self, event):
        """Handles the drop part of a drag-and-drop operation."""
        print(f"Drop event detected at ({event.x}, {event.y})")
        print(f"Current drag data: {self.drag_data}")
        
        if self.drag_data["item"] is None:
            print("No item being dragged - ignoring drop")
            return  # Nothing is being dragged

        item_type = self.drag_data["item"]
        # The event coordinates are relative to the widget that received the event
        drop_position = (event.x, event.y)

        print(f"Dropped '{item_type}' at canvas coordinates: {drop_position}")

        # Add the element to the diagram canvas
        if self.diagram_canvas:
            if item_type == "cut":
                # Pass the selected cut placement mode for cuts
                placement_mode = self.cut_mode.get()
                self.diagram_canvas.add_element(item_type, drop_position, placement_mode)
                print(f"Cut placement mode: {placement_mode}")
            else:
                # For non-cut elements, use default behavior
                self.diagram_canvas.add_element(item_type, drop_position)
        else:
            print("No diagram canvas available!")

        # Reset the drag state
        self.drag_data["item"] = None

    def start_drag(self, item_type):
        """Begins a drag-and-drop operation for a new graph element."""
        self.drag_data["item"] = item_type
        print(f"Starting drag for: {item_type}") # For debugging

    def setup_browser_tab(self):
        """Sets up the Browser/Sheet of Assertion Explorer workspace."""
        ttk.Label(self.browser_tab, text="Browser Workspace - Coming Soon").pack(pady=50)

    def setup_epg_tab(self):
        """Sets up the Endoporeutic Game workspace."""
        ttk.Label(self.epg_tab, text="EPG Workspace - Coming Soon").pack(pady=50)

def main():
    """Main function to run the application."""
    app = ArisbeGUI()
    app.mainloop()

if __name__ == "__main__":
    main()
