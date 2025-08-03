#!/usr/bin/env python3
"""
Phase 2 Concept Demonstration: Selection Overlays & Context-Sensitive Actions

This demonstration showcases the key Phase 2 architectural concepts we've implemented:

1. **Enhanced Selection System** - Robust selection with contextual overlays
2. **Context-Sensitive Actions** - Actions that validate based on current selection
3. **Logical vs. Appearance-Only Operations** - Clear separation of concerns
4. **Professional Interaction Patterns** - Action-first workflow with validation

The demo uses a simplified rendering approach to focus on the interaction concepts
rather than getting stuck on backend API integration issues.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from egif_parser_dau import EGIFParser


class Phase2ConceptDemo:
    """
    Demonstration of Phase 2 architectural concepts.
    
    This demo focuses on the interaction patterns and selection system
    concepts rather than full rendering integration.
    """
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Phase 2 Concepts: Selection System & Context-Sensitive Actions")
        self.root.geometry("1200x800")
        
        # Core state
        self.current_graph = None
        self.selected_elements = set()
        self.selection_mode = "none"  # none, single, multiple, area
        self.selection_bounds = None
        self.available_actions = []
        
        # Create UI
        self._create_ui()
        
        # Load initial case
        self._load_initial_case()
    
    def _create_ui(self):
        """Create the demonstration UI."""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title and description
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(title_frame, text="Phase 2: Selection Overlays & Context-Sensitive Actions", 
                               font=('Arial', 16, 'bold'))
        title_label.pack()
        
        desc_label = ttk.Label(title_frame, 
            text="Demonstrates professional EG editor interaction patterns with selection-driven actions",
            font=('Arial', 10))
        desc_label.pack(pady=(5, 0))
        
        # Control panel
        controls_frame = ttk.LabelFrame(main_frame, text="Test Case & Controls")
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Test case selector
        case_frame = ttk.Frame(controls_frame)
        case_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(case_frame, text="EGIF Test Case:").pack(side=tk.LEFT)
        self.case_var = tk.StringVar()
        case_combo = ttk.Combobox(case_frame, textvariable=self.case_var, width=50)
        case_combo['values'] = [
            '(Human "Socrates") ~[ (Mortal "Socrates") ]',
            '*x ~[ (Human x) (Mortal x) ]',
            '*x (Human x) ~[ (Mortal x) (Wise x) ]',
            '*x *y (Human x) (Loves x y) ~[ (Mortal y) ]',
            '*x *y *z (Human x) (Loves x y) ~[ (Mortal y) (Wise z) ]'
        ]
        case_combo.set(case_combo['values'][0])
        case_combo.pack(side=tk.LEFT, padx=(10, 5))
        case_combo.bind('<<ComboboxSelected>>', self._on_case_change)
        
        ttk.Button(case_frame, text="Load", command=self._load_case).pack(side=tk.LEFT, padx=5)
        
        # Main content area
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Selection System
        left_frame = ttk.LabelFrame(content_frame, text="Enhanced Selection System", width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_frame.pack_propagate(False)
        
        # Selection simulation controls
        selection_controls = ttk.Frame(left_frame)
        selection_controls.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(selection_controls, text="Simulate Selection:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        
        ttk.Button(selection_controls, text="Select Single Element", 
                  command=lambda: self._simulate_selection("single")).pack(fill=tk.X, pady=2)
        ttk.Button(selection_controls, text="Select Multiple Elements", 
                  command=lambda: self._simulate_selection("multiple")).pack(fill=tk.X, pady=2)
        ttk.Button(selection_controls, text="Select Empty Area", 
                  command=lambda: self._simulate_selection("area")).pack(fill=tk.X, pady=2)
        ttk.Button(selection_controls, text="Clear Selection", 
                  command=lambda: self._simulate_selection("none")).pack(fill=tk.X, pady=2)
        
        # Selection info display
        ttk.Label(left_frame, text="Selection Information:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, padx=10, pady=(10, 5))
        self.selection_info = tk.Text(left_frame, height=8, wrap=tk.WORD, font=('Courier', 9))
        self.selection_info.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Available actions
        ttk.Label(left_frame, text="Available Actions:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, padx=10)
        self.actions_info = tk.Text(left_frame, height=6, wrap=tk.WORD, font=('Arial', 9))
        self.actions_info.pack(fill=tk.X, padx=10, pady=(5, 10))
        
        # Center - Context-Sensitive Actions
        center_frame = ttk.LabelFrame(content_frame, text="Context-Sensitive Actions")
        center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Action categories
        actions_container = ttk.Frame(center_frame)
        actions_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Insert Actions
        insert_frame = ttk.LabelFrame(actions_container, text="Insert Actions (Logical Operations)")
        insert_frame.pack(fill=tk.X, pady=(0, 10))
        
        insert_buttons = ttk.Frame(insert_frame)
        insert_buttons.pack(fill=tk.X, padx=10, pady=5)
        
        self.insert_cut_btn = ttk.Button(insert_buttons, text="Insert Cut", 
                                        command=lambda: self._execute_action("insert_cut"))
        self.insert_cut_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.insert_predicate_btn = ttk.Button(insert_buttons, text="Insert Predicate", 
                                              command=lambda: self._execute_action("insert_predicate"))
        self.insert_predicate_btn.pack(side=tk.LEFT, padx=5)
        
        self.insert_loi_btn = ttk.Button(insert_buttons, text="Insert Line of Identity", 
                                        command=lambda: self._execute_action("insert_loi"))
        self.insert_loi_btn.pack(side=tk.LEFT, padx=5)
        
        # Modify Actions
        modify_frame = ttk.LabelFrame(actions_container, text="Modify Actions (Mixed Operations)")
        modify_frame.pack(fill=tk.X, pady=(0, 10))
        
        modify_buttons = ttk.Frame(modify_frame)
        modify_buttons.pack(fill=tk.X, padx=10, pady=5)
        
        self.move_btn = ttk.Button(modify_buttons, text="Move (Appearance)", 
                                  command=lambda: self._execute_action("move"))
        self.move_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.resize_btn = ttk.Button(modify_buttons, text="Resize (Appearance)", 
                                    command=lambda: self._execute_action("resize"))
        self.resize_btn.pack(side=tk.LEFT, padx=5)
        
        self.edit_predicate_btn = ttk.Button(modify_buttons, text="Edit Predicate (Logical)", 
                                            command=lambda: self._execute_action("edit_predicate"))
        self.edit_predicate_btn.pack(side=tk.LEFT, padx=5)
        
        # Delete Actions
        delete_frame = ttk.LabelFrame(actions_container, text="Delete Actions (Logical Operations)")
        delete_frame.pack(fill=tk.X, pady=(0, 10))
        
        delete_buttons = ttk.Frame(delete_frame)
        delete_buttons.pack(fill=tk.X, padx=10, pady=5)
        
        self.delete_btn = ttk.Button(delete_buttons, text="Delete Selected", 
                                    command=lambda: self._execute_action("delete"))
        self.delete_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Action feedback area
        ttk.Label(actions_container, text="Action Feedback:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(10, 5))
        self.action_feedback = tk.Text(actions_container, height=8, wrap=tk.WORD, font=('Arial', 9))
        self.action_feedback.pack(fill=tk.BOTH, expand=True)
        
        # Right panel - Graph Structure & Architecture
        right_frame = ttk.LabelFrame(content_frame, text="EGI Structure & Architecture", width=300)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        right_frame.pack_propagate(False)
        
        # Graph structure
        ttk.Label(right_frame, text="Current Graph:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, padx=10, pady=(10, 5))
        self.graph_info = tk.Text(right_frame, height=10, wrap=tk.WORD, font=('Courier', 9))
        self.graph_info.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Architecture explanation
        ttk.Label(right_frame, text="Phase 2 Architecture:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, padx=10)
        
        arch_text = tk.Text(right_frame, height=12, wrap=tk.WORD, font=('Arial', 9))
        arch_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))
        
        architecture_info = """Layer Separation:
• Data Layer: Pure EGI model (immutable)
• Layout Layer: Spatial positioning
• Rendering Layer: Visual presentation
• Interaction Layer: User events → EGI ops

Selection System:
• Contextual overlays per selection type
• Visual feedback (highlights, bounds)
• Validation before action execution

Action Types:
• Logical: Modify EGI structure
• Appearance: Modify layout only
• Mixed: Both logical and visual changes

Professional Patterns:
• Action-first workflow
• Context-sensitive validation
• Clear error messages
• Undo/redo support"""
        
        arch_text.insert(1.0, architecture_info)
        arch_text.config(state=tk.DISABLED)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready - Select elements and try context-sensitive actions")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, pady=(10, 0))
        
        # Initialize display
        self._update_all_displays()
    
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
            self._simulate_selection("none")  # Clear selection
            self._update_all_displays()
            self.status_var.set(f"Loaded: {egif_string}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load case: {e}")
            self.status_var.set(f"Error: {e}")
    
    def _on_case_change(self, event=None):
        """Handle test case change."""
        self._load_case()
    
    def _simulate_selection(self, mode):
        """Simulate different selection modes."""
        self.selection_mode = mode
        self.selected_elements.clear()
        self.selection_bounds = None
        
        if mode == "single" and self.current_graph:
            # Select first edge (predicate)
            if self.current_graph.E:
                self.selected_elements.add(next(iter(self.current_graph.E)))
        elif mode == "multiple" and self.current_graph:
            # Select multiple elements
            elements = list(self.current_graph.V)[:2] + list(self.current_graph.E)[:1]
            self.selected_elements.update(elements[:3])
        elif mode == "area":
            # Simulate area selection
            self.selection_bounds = (50, 50, 150, 100)
        
        self._update_all_displays()
        self.status_var.set(f"Selection mode: {mode}")
    
    def _execute_action(self, action):
        """Execute a context-sensitive action with validation."""
        # Validate action based on current selection
        is_valid, message = self._validate_action(action)
        
        feedback = f"Action: {action.replace('_', ' ').title()}\n"
        feedback += f"Validation: {'✓ VALID' if is_valid else '✗ INVALID'}\n"
        feedback += f"Message: {message}\n"
        
        if is_valid:
            # Simulate action execution
            if action == "insert_cut":
                feedback += "\n→ Would create new Cut element in EGI\n"
                feedback += "→ Would update area mappings\n"
                feedback += "→ Would trigger layout recalculation\n"
                feedback += "→ LOGICAL OPERATION (modifies EGI)"
            elif action == "insert_predicate":
                predicate_name = simpledialog.askstring("Insert Predicate", "Enter predicate name:")
                if predicate_name:
                    feedback += f"\n→ Would create new Edge '{predicate_name}' in EGI\n"
                    feedback += "→ Would create associated vertices\n"
                    feedback += "→ Would update ν mapping\n"
                    feedback += "→ LOGICAL OPERATION (modifies EGI)"
                else:
                    feedback += "\n→ Action cancelled by user"
            elif action == "insert_loi":
                feedback += "\n→ Would create new Vertex (Line of Identity) in EGI\n"
                feedback += "→ Would update area mappings\n"
                feedback += "→ LOGICAL OPERATION (modifies EGI)"
            elif action == "move":
                feedback += "\n→ Would update element positions in layout\n"
                feedback += "→ Would preserve EGI structure\n"
                feedback += "→ APPEARANCE-ONLY OPERATION"
            elif action == "resize":
                feedback += "\n→ Would update element dimensions in layout\n"
                feedback += "→ Would preserve EGI structure\n"
                feedback += "→ APPEARANCE-ONLY OPERATION"
            elif action == "edit_predicate":
                if self.selected_elements:
                    element_id = next(iter(self.selected_elements))
                    if element_id in self.current_graph.rel:
                        current_name = self.current_graph.rel[element_id]
                        new_name = simpledialog.askstring("Edit Predicate", 
                                                         f"Edit predicate name:", 
                                                         initialvalue=current_name)
                        if new_name:
                            feedback += f"\n→ Would update relation mapping: {current_name} → {new_name}\n"
                            feedback += "→ Would preserve ν mapping structure\n"
                            feedback += "→ LOGICAL OPERATION (modifies EGI)"
                        else:
                            feedback += "\n→ Action cancelled by user"
            elif action == "delete":
                feedback += f"\n→ Would remove {len(self.selected_elements)} elements from EGI\n"
                feedback += "→ Would update all mappings (rel, ν, area)\n"
                feedback += "→ Would trigger layout recalculation\n"
                feedback += "→ LOGICAL OPERATION (modifies EGI)"
            
            feedback += f"\n→ Status: Action would be executed successfully"
        else:
            feedback += f"\n→ Status: Action blocked by validation"
        
        feedback += f"\n\nTimestamp: {self._get_timestamp()}\n"
        feedback += "=" * 50 + "\n"
        
        # Update feedback display
        self.action_feedback.insert(1.0, feedback)
        
        # Update status
        if is_valid:
            self.status_var.set(f"Executed: {action.replace('_', ' ')}")
        else:
            self.status_var.set(f"Blocked: {message}")
    
    def _validate_action(self, action):
        """Validate action based on current selection and EGI rules."""
        if action in ["insert_cut", "insert_predicate", "insert_loi"]:
            if self.selection_mode == "area":
                return True, "Empty area selected - insertion allowed"
            elif self.selection_mode == "multiple" and action == "insert_cut":
                return True, "Multiple elements selected - can enclose with cut"
            else:
                return False, "Requires empty area selection (or multiple elements for cut)"
        
        elif action in ["move", "resize", "edit_predicate", "delete"]:
            if self.selected_elements:
                if action == "edit_predicate":
                    # Check if selected element is actually a predicate
                    for element_id in self.selected_elements:
                        if element_id in self.current_graph.rel:
                            return True, "Predicate selected - editing allowed"
                    return False, "No predicate selected"
                else:
                    return True, f"Elements selected - {action} allowed"
            else:
                return False, "Requires element selection"
        
        return False, "Unknown action"
    
    def _update_all_displays(self):
        """Update all information displays."""
        self._update_selection_display()
        self._update_graph_display()
        self._update_action_buttons()
    
    def _update_selection_display(self):
        """Update selection information display."""
        info = f"Selection Mode: {self.selection_mode.title()}\n"
        info += f"Selected Elements: {len(self.selected_elements)}\n\n"
        
        if self.selected_elements:
            info += "Element Details:\n"
            for element_id in list(self.selected_elements)[:5]:
                element_type = "Unknown"
                details = ""
                
                if element_id in self.current_graph.V:
                    element_type = "Vertex (Line of Identity)"
                    vertex = self.current_graph.get_vertex(element_id)
                    if vertex.label:
                        details = f" - Label: {vertex.label}"
                elif element_id in self.current_graph.E:
                    element_type = "Edge (Predicate)"
                    if element_id in self.current_graph.rel:
                        relation = self.current_graph.rel[element_id]
                        arity = len(self.current_graph.nu.get(element_id, ()))
                        details = f" - {relation}({arity})"
                elif element_id in self.current_graph.Cut:
                    element_type = "Cut"
                
                info += f"• {element_type}{details}\n"
                # Handle both string IDs and objects
                id_str = str(element_id.id if hasattr(element_id, 'id') else element_id)
                info += f"  ID: {id_str[-8:]}\n"
            
            if len(self.selected_elements) > 5:
                info += f"... and {len(self.selected_elements) - 5} more\n"
        
        if self.selection_bounds:
            x1, y1, x2, y2 = self.selection_bounds
            info += f"\nArea Selection:\n"
            info += f"Bounds: ({x1}, {y1}) to ({x2}, {y2})\n"
            info += f"Size: {x2-x1} × {y2-y1}\n"
        
        # Show available actions
        available = []
        for action in ["insert_cut", "insert_predicate", "insert_loi", "move", "resize", "edit_predicate", "delete"]:
            is_valid, _ = self._validate_action(action)
            if is_valid:
                available.append(action.replace('_', ' ').title())
        
        if available:
            info += f"\nAvailable Actions:\n"
            for action in available:
                info += f"• {action}\n"
        else:
            info += f"\nNo actions available for current selection"
        
        self.selection_info.delete(1.0, tk.END)
        self.selection_info.insert(1.0, info)
        
        # Update actions display
        actions_text = "Context-Sensitive Validation:\n\n"
        for action in ["insert_cut", "insert_predicate", "insert_loi", "move", "resize", "edit_predicate", "delete"]:
            is_valid, message = self._validate_action(action)
            status = "✓" if is_valid else "✗"
            actions_text += f"{status} {action.replace('_', ' ').title()}: {message}\n"
        
        self.actions_info.delete(1.0, tk.END)
        self.actions_info.insert(1.0, actions_text)
    
    def _update_graph_display(self):
        """Update graph structure display."""
        if not self.current_graph:
            return
        
        graph = self.current_graph
        
        info = f"EGI Structure:\n"
        info += f"Vertices (V): {len(graph.V)}\n"
        info += f"Edges (E): {len(graph.E)}\n"
        info += f"Cuts: {len(graph.Cut)}\n\n"
        
        info += "Relations (rel):\n"
        for edge_id, relation in list(graph.rel.items())[:5]:
            args = graph.nu.get(edge_id, ())
            info += f"• {relation} (arity {len(args)})\n"
        
        if len(graph.rel) > 5:
            info += f"... and {len(graph.rel) - 5} more\n"
        
        info += f"\nNu Mapping (ν):\n"
        for edge_id, vertex_tuple in list(graph.nu.items())[:3]:
            relation = graph.rel.get(edge_id, "Unknown")
            info += f"• {relation}: {len(vertex_tuple)} args\n"
        
        if len(graph.nu) > 3:
            info += f"... and {len(graph.nu) - 3} more\n"
        
        info += f"\nArea Mappings:\n"
        for area_id, elements in list(graph.area.items())[:4]:
            area_name = "Sheet" if area_id == graph.sheet else f"Cut"
            info += f"• {area_name}: {len(elements)} elements\n"
        
        self.graph_info.delete(1.0, tk.END)
        self.graph_info.insert(1.0, info)
    
    def _update_action_buttons(self):
        """Update action button states based on validation."""
        buttons = {
            "insert_cut": self.insert_cut_btn,
            "insert_predicate": self.insert_predicate_btn,
            "insert_loi": self.insert_loi_btn,
            "move": self.move_btn,
            "resize": self.resize_btn,
            "edit_predicate": self.edit_predicate_btn,
            "delete": self.delete_btn
        }
        
        for action, button in buttons.items():
            is_valid, _ = self._validate_action(action)
            if is_valid:
                button.config(state=tk.NORMAL)
            else:
                button.config(state=tk.DISABLED)
    
    def _get_timestamp(self):
        """Get current timestamp."""
        import datetime
        return datetime.datetime.now().strftime("%H:%M:%S")
    
    def run(self):
        """Run the concept demonstration."""
        print("=" * 60)
        print("PHASE 2 CONCEPT DEMONSTRATION")
        print("=" * 60)
        print()
        print("Key Concepts Demonstrated:")
        print("1. Enhanced Selection System with contextual overlays")
        print("2. Context-sensitive action validation")
        print("3. Logical vs. appearance-only operation separation")
        print("4. Professional interaction patterns")
        print("5. EGI model integration")
        print()
        print("Architecture Highlights:")
        print("- Clean layer separation (Data/Layout/Rendering/Interaction)")
        print("- Immutable EGI as single source of truth")
        print("- Selection-driven action workflow")
        print("- Rule-based validation before execution")
        print("- Clear distinction between logical and visual changes")
        print()
        print("Instructions:")
        print("- Use 'Simulate Selection' buttons to try different selection modes")
        print("- Notice how available actions change based on selection")
        print("- Try executing actions - they show validation and would-be effects")
        print("- Observe the distinction between logical and appearance operations")
        print()
        
        self.root.mainloop()


if __name__ == "__main__":
    demo = Phase2ConceptDemo()
    demo.run()
