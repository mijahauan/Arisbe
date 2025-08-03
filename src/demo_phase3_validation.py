#!/usr/bin/env python3
"""
Phase 3 Demonstration: Background Validation and Transformation Logic

Demonstrates the integration of formal EG transformation rules with
real-time validation and the existing Phase 2 selection/action architecture.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from typing import Set, Dict, List
import tkinter as tk
from tkinter import ttk, messagebox

from egi_core_dau import RelationalGraphWithCuts, ElementID
from egif_parser_dau import EGIFParser
from layout_engine_clean import CleanLayoutEngine
from diagram_renderer_clean import CleanDiagramRenderer
from tkinter_backend import TkinterCanvas
from eg_transformation_rules import EGTransformationEngine, TransformationRule
from background_validation_system import (
    create_validation_system, ValidationLevel, ValidationFeedback
)


class Phase3ValidationDemo:
    """
    Comprehensive demonstration of Phase 3 validation and transformation features.
    
    Shows:
    1. Real-time validation of user actions
    2. Formal EG transformation rules
    3. Background validation feedback
    4. Integration with selection-driven workflow
    """
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Phase 3: EG Validation & Transformation Demo")
        self.root.geometry("1200x800")
        
        # Initialize core systems
        self.parser = None  # Will be created when needed
        self.layout_engine = CleanLayoutEngine()
        self.transformation_engine = EGTransformationEngine()
        self.validation_system = create_validation_system(ValidationLevel.STANDARD)
        
        # Current state
        self.current_graph: RelationalGraphWithCuts = None
        self.selected_elements: Set[ElementID] = set()
        self.current_feedback: ValidationFeedback = None
        
        # Set up validation callbacks
        self.validation_system.add_ui_callback(self._on_validation_update)
        
        # Create UI
        self._create_ui()
        
        # Load initial example
        self._load_example_graph()
    
    def _create_ui(self):
        """Create the demonstration UI."""
        
        # Main layout
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel: Controls and validation
        left_panel = ttk.Frame(main_frame, width=400)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # Right panel: Canvas
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # === LEFT PANEL CONTENTS ===
        
        # Graph input section
        input_frame = ttk.LabelFrame(left_panel, text="EG Input", padding=10)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.egif_text = tk.Text(input_frame, height=6, width=45)
        self.egif_text.pack(fill=tk.X)
        
        ttk.Button(input_frame, text="Parse & Display", 
                  command=self._parse_and_display).pack(pady=(5, 0))
        
        # Selection section
        selection_frame = ttk.LabelFrame(left_panel, text="Selection", padding=10)
        selection_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.selection_listbox = tk.Listbox(selection_frame, height=4)
        self.selection_listbox.pack(fill=tk.X)
        
        selection_buttons = ttk.Frame(selection_frame)
        selection_buttons.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(selection_buttons, text="Select All", 
                  command=self._select_all).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(selection_buttons, text="Clear", 
                  command=self._clear_selection).pack(side=tk.LEFT)
        
        # Actions section
        actions_frame = ttk.LabelFrame(left_panel, text="Actions", padding=10)
        actions_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Action buttons
        action_buttons = [
            ("Insert Cut", self._action_insert_cut),
            ("Insert Predicate", self._action_insert_predicate),
            ("Insert LoI", self._action_insert_loi),
            ("Delete Selection", self._action_delete),
            ("Edit Predicate", self._action_edit_predicate)
        ]
        
        for text, command in action_buttons:
            ttk.Button(actions_frame, text=text, command=command).pack(fill=tk.X, pady=2)
        
        # Transformation rules section
        transform_frame = ttk.LabelFrame(left_panel, text="Transformation Rules", padding=10)
        transform_frame.pack(fill=tk.X, pady=(0, 10))
        
        transform_buttons = [
            ("Double Cut Insert", lambda: self._apply_transformation(TransformationRule.DOUBLE_CUT_INSERT)),
            ("Double Cut Delete", lambda: self._apply_transformation(TransformationRule.DOUBLE_CUT_DELETE)),
            ("Erasure Rule", lambda: self._apply_transformation(TransformationRule.ERASURE)),
            ("Cut Insert", lambda: self._apply_transformation(TransformationRule.CUT_INSERT)),
            ("Cut Delete", lambda: self._apply_transformation(TransformationRule.CUT_DELETE))
        ]
        
        for text, command in transform_buttons:
            ttk.Button(transform_frame, text=text, command=command).pack(fill=tk.X, pady=2)
        
        # Validation feedback section
        feedback_frame = ttk.LabelFrame(left_panel, text="Validation Feedback", padding=10)
        feedback_frame.pack(fill=tk.BOTH, expand=True)
        
        # Feedback text area
        self.feedback_text = tk.Text(feedback_frame, height=8, wrap=tk.WORD)
        feedback_scroll = ttk.Scrollbar(feedback_frame, orient=tk.VERTICAL, command=self.feedback_text.yview)
        self.feedback_text.configure(yscrollcommand=feedback_scroll.set)
        
        self.feedback_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        feedback_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # === RIGHT PANEL CONTENTS ===
        
        # Canvas for diagram display
        canvas_frame = ttk.LabelFrame(right_panel, text="EG Diagram", padding=10)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = TkinterCanvas(600, 500, title="Phase 3 Demo", master=canvas_frame)
        self.canvas.tk_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind canvas events for selection
        self.canvas.tk_canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.tk_canvas.bind("<Control-Button-1>", self._on_canvas_ctrl_click)
        
        self.renderer = CleanDiagramRenderer(self.canvas)
    
    def _load_example_graph(self):
        """Load an example EG for demonstration."""
        
        example_egif = '''*x (Human x) ~[ (Mortal x) (Wise x) ]'''
        
        self.egif_text.delete(1.0, tk.END)
        self.egif_text.insert(1.0, example_egif)
        
        self._parse_and_display()
    
    def _parse_and_display(self):
        """Parse EGIF input and display the graph."""
        
        try:
            egif_text = self.egif_text.get(1.0, tk.END).strip()
            if not egif_text:
                return
            
            # Parse EGIF
            parser = EGIFParser(egif_text)
            self.current_graph = parser.parse()
            
            # Generate layout
            layout = self.layout_engine.layout_graph(self.current_graph)
            
            # Render diagram
            self.canvas.clear()
            self.renderer.render_diagram(self.current_graph, layout)
            
            # Update selection display
            self._update_selection_display()
            
            # Validate current state
            self._validate_current_state()
            
            self._log_feedback("Graph parsed and displayed successfully")
            
        except Exception as e:
            messagebox.showerror("Parse Error", f"Failed to parse EGIF: {str(e)}")
            self._log_feedback(f"Parse error: {str(e)}", "ERROR")
    
    def _update_selection_display(self):
        """Update the selection listbox."""
        
        self.selection_listbox.delete(0, tk.END)
        
        if not self.current_graph:
            return
        
        # Add all elements to selection list
        for vertex_id in self.current_graph.V:
            label = f"Vertex: {vertex_id[-8:]}"
            self.selection_listbox.insert(tk.END, label)
        
        for edge_id in self.current_graph.E:
            predicate_name = self.current_graph.rel.get(edge_id, "Unknown")
            label = f"Predicate: {predicate_name} ({edge_id[-8:]})"
            self.selection_listbox.insert(tk.END, label)
        
        for cut_id in self.current_graph.Cut:
            label = f"Cut: {cut_id[-8:]}"
            self.selection_listbox.insert(tk.END, label)
    
    def _validate_current_state(self):
        """Validate the current graph state."""
        
        if not self.current_graph:
            return
        
        # Perform comprehensive validation
        validation_results = self.validation_system.validator.background_validator.validate_graph_structure(
            self.current_graph
        )
        
        # Display results
        feedback_text = "=== GRAPH VALIDATION ===\n"
        
        if validation_results['is_valid']:
            feedback_text += "✓ Graph structure is valid\n\n"
        else:
            feedback_text += "✗ Graph structure has issues\n\n"
        
        if validation_results['errors']:
            feedback_text += "ERRORS:\n"
            for error in validation_results['errors']:
                feedback_text += f"  • {error}\n"
            feedback_text += "\n"
        
        if validation_results['warnings']:
            feedback_text += "WARNINGS:\n"
            for warning in validation_results['warnings']:
                feedback_text += f"  • {warning}\n"
            feedback_text += "\n"
        
        if validation_results['suggestions']:
            feedback_text += "SUGGESTIONS:\n"
            for suggestion in validation_results['suggestions']:
                feedback_text += f"  • {suggestion}\n"
            feedback_text += "\n"
        
        # Get available transformations
        transformations = self.validation_system.get_transformation_opportunities(self.current_graph)
        if transformations:
            feedback_text += "AVAILABLE TRANSFORMATIONS:\n"
            for transform in transformations[:5]:  # Show first 5
                feedback_text += f"  • {transform['description']}\n"
            feedback_text += "\n"
        
        self._display_feedback(feedback_text)
    
    def _select_all(self):
        """Select all elements."""
        
        if not self.current_graph:
            return
        
        self.selected_elements = self.current_graph.V | self.current_graph.E | self.current_graph.Cut
        self._log_feedback(f"Selected {len(self.selected_elements)} elements")
    
    def _clear_selection(self):
        """Clear selection."""
        
        self.selected_elements.clear()
        self._log_feedback("Selection cleared")
    
    def _on_canvas_click(self, event):
        """Handle canvas click for element selection."""
        
        if not self.current_graph:
            return
        
        # Simulate element selection based on click position
        # In a real implementation, this would use spatial layout to determine clicked element
        x, y = event.x, event.y
        
        # Simple simulation: select different elements based on click position
        elements = list(self.current_graph.V | self.current_graph.E | self.current_graph.Cut)
        if elements:
            # Cycle through elements based on click position
            index = (x + y) % len(elements)
            selected_element = elements[index]
            
            # Toggle selection
            if selected_element in self.selected_elements:
                self.selected_elements.remove(selected_element)
                self._log_feedback(f"Deselected: {self._get_element_description(selected_element)}")
            else:
                self.selected_elements.add(selected_element)
                self._log_feedback(f"Selected: {self._get_element_description(selected_element)}")
            
            # Trigger real-time validation
            self._validate_current_selection()
        else:
            self._log_feedback("No elements available for selection")
    
    def _on_canvas_ctrl_click(self, event):
        """Handle Ctrl+click for multi-selection."""
        
        # Same as regular click but don't clear existing selection
        self._on_canvas_click(event)
    
    def _get_element_description(self, element_id: ElementID) -> str:
        """Get human-readable description of an element."""
        
        if not self.current_graph:
            return f"Element {element_id[-8:]}"
        
        if element_id in self.current_graph.V:
            return f"Vertex {element_id[-8:]}"
        elif element_id in self.current_graph.E:
            predicate_name = self.current_graph.rel.get(element_id, "Unknown")
            return f"Predicate '{predicate_name}' ({element_id[-8:]})"
        elif element_id in self.current_graph.Cut:
            return f"Cut {element_id[-8:]}"
        else:
            return f"Unknown element {element_id[-8:]}"
    
    def _validate_current_selection(self):
        """Validate current selection and provide real-time feedback."""
        
        if not self.current_graph:
            return
        
        feedback_text = "=== REAL-TIME VALIDATION ===\n"
        
        if not self.selected_elements:
            feedback_text += "No elements selected\n\n"
            feedback_text += "AVAILABLE ACTIONS:\n"
            feedback_text += "  • Click canvas to select elements\n"
            feedback_text += "  • Insert new elements (Cut, Predicate, LoI)\n"
            feedback_text += "  • Apply transformation rules\n\n"
        else:
            feedback_text += f"Selected: {len(self.selected_elements)} elements\n"
            for element_id in list(self.selected_elements)[:3]:  # Show first 3
                feedback_text += f"  • {self._get_element_description(element_id)}\n"
            if len(self.selected_elements) > 3:
                feedback_text += f"  • ... and {len(self.selected_elements) - 3} more\n"
            feedback_text += "\n"
            
            # Validate specific actions with current selection
            self._validate_selection_actions(feedback_text)
        
        # Get available transformations
        transformations = self.validation_system.get_transformation_opportunities(self.current_graph)
        if transformations:
            feedback_text += "AVAILABLE TRANSFORMATIONS:\n"
            for transform in transformations[:3]:  # Show first 3
                feedback_text += f"  • {transform['description']}\n"
            feedback_text += "\n"
        
        self._display_feedback(feedback_text)
    
    def _refresh_display(self):
        """Refresh the diagram display after changes."""
        
        if not self.current_graph:
            return
        
        try:
            # Generate new layout
            layout = self.layout_engine.layout_graph(self.current_graph)
            
            # Re-render diagram
            self.canvas.clear()
            self.renderer.render_diagram(layout, self.current_graph)
            
            # Update selection display
            self._update_selection_display()
            
            # Validate current state
            self._validate_current_state()
            
        except Exception as e:
            self._log_feedback(f"Display refresh failed: {str(e)}", "ERROR")
    
    def _validate_selection_actions(self, feedback_text: str) -> str:
        """Validate actions with current selection and add to feedback."""
        
        # Test deletion
        delete_feedback = self.validation_system.validate_selection_action(
            self.current_graph, "delete", self.selected_elements
        )
        
        if delete_feedback.is_valid:
            feedback_text += "✓ DELETE: Valid - can erase selected elements\n"
        else:
            feedback_text += f"✗ DELETE: {delete_feedback.message}\n"
        
        # Test cut insertion around selection
        cut_feedback = self.validation_system.validate_selection_action(
            self.current_graph, "insert_cut", self.selected_elements,
            target_area=self.current_graph.sheet, enclosed_elements=self.selected_elements
        )
        
        if cut_feedback.is_valid:
            feedback_text += "✓ ENCLOSE WITH CUT: Valid - can create cut around selection\n"
        else:
            feedback_text += f"✗ ENCLOSE WITH CUT: {cut_feedback.message}\n"
        
        # Show suggestions
        suggestions = self.validation_system.get_action_suggestions(self.current_graph, self.selected_elements)
        if suggestions:
            feedback_text += "\nSUGGESTIONS:\n"
            for suggestion in suggestions[:3]:  # Show first 3
                feedback_text += f"  • {suggestion}\n"
        
        feedback_text += "\n"
        return feedback_text
    
    # Action handlers
    def _action_insert_cut(self):
        """Handle cut insertion action."""
        
        if not self.current_graph:
            self._log_feedback("No graph loaded", "ERROR")
            return
        
        # Use sheet as target area for demo
        target_area = self.current_graph.sheet
        
        # Validate the action
        feedback = self.validation_system.validate_selection_action(
            self.current_graph, "insert_cut", self.selected_elements,
            target_area=target_area, enclosed_elements=self.selected_elements
        )
        
        self._display_action_feedback("Insert Cut", feedback)
        
        # If valid, actually apply the transformation
        if feedback.is_valid:
            result = self.transformation_engine.apply_transformation(
                self.current_graph, TransformationRule.CUT_INSERT,
                target_area=target_area, enclosed_elements=self.selected_elements
            )
            
            if result.success:
                self.current_graph = result.new_graph
                self.selected_elements.clear()
                self._refresh_display()
                self._log_feedback(f"✓ Cut inserted: {result.description}", "SUCCESS")
            else:
                self._log_feedback(f"✗ Cut insertion failed: {result.error_message}", "ERROR")
    
    def _action_insert_predicate(self):
        """Handle predicate insertion action."""
        
        if not self.current_graph:
            return
        
        target_area = self.current_graph.sheet
        
        feedback = self.validation_system.validate_selection_action(
            self.current_graph, "insert_predicate", self.selected_elements,
            target_area=target_area, predicate_name="NewPred", arity=2
        )
        
        self._display_action_feedback("Insert Predicate", feedback)
    
    def _action_insert_loi(self):
        """Handle Line of Identity insertion action."""
        
        if not self.current_graph:
            return
        
        target_area = self.current_graph.sheet
        
        feedback = self.validation_system.validate_selection_action(
            self.current_graph, "insert_loi", self.selected_elements,
            target_area=target_area
        )
        
        self._display_action_feedback("Insert Line of Identity", feedback)
    
    def _action_delete(self):
        """Handle deletion action."""
        
        if not self.current_graph:
            return
        
        feedback = self.validation_system.validate_selection_action(
            self.current_graph, "delete", self.selected_elements
        )
        
        self._display_action_feedback("Delete", feedback)
        
        # If valid, actually apply the deletion
        if feedback.is_valid and self.selected_elements:
            result = self.transformation_engine.apply_transformation(
                self.current_graph, TransformationRule.ERASURE,
                elements_to_erase=self.selected_elements
            )
            
            if result.success:
                self.current_graph = result.new_graph
                self.selected_elements.clear()
                self._parse_and_display()  # Refresh display
                self._log_feedback(f"Successfully deleted elements: {result.description}")
            else:
                self._log_feedback(f"Deletion failed: {result.error_message}", "ERROR")
    
    def _action_edit_predicate(self):
        """Handle predicate editing action."""
        
        if not self.current_graph:
            return
        
        feedback = self.validation_system.validate_selection_action(
            self.current_graph, "edit_predicate", self.selected_elements,
            new_name="EditedPred", new_arity=3
        )
        
        self._display_action_feedback("Edit Predicate", feedback)
    
    def _apply_transformation(self, rule: TransformationRule):
        """Apply a transformation rule."""
        
        if not self.current_graph:
            return
        
        try:
            # Get parameters based on rule type
            if rule == TransformationRule.DOUBLE_CUT_INSERT:
                result = self.transformation_engine.apply_transformation(
                    self.current_graph, rule, target_area=self.current_graph.sheet
                )
            
            elif rule == TransformationRule.DOUBLE_CUT_DELETE:
                # Find a suitable double cut to delete
                cuts = list(self.current_graph.Cut)
                if cuts:
                    result = self.transformation_engine.apply_transformation(
                        self.current_graph, rule, outer_cut_id=cuts[0]
                    )
                else:
                    self._log_feedback("No cuts available for double cut deletion", "WARNING")
                    return
            
            elif rule == TransformationRule.ERASURE:
                if self.selected_elements:
                    result = self.transformation_engine.apply_transformation(
                        self.current_graph, rule, elements_to_erase=self.selected_elements
                    )
                else:
                    self._log_feedback("No elements selected for erasure", "WARNING")
                    return
            
            elif rule == TransformationRule.CUT_INSERT:
                result = self.transformation_engine.apply_transformation(
                    self.current_graph, rule, 
                    target_area=self.current_graph.sheet,
                    enclosed_elements=self.selected_elements
                )
            
            elif rule == TransformationRule.CUT_DELETE:
                cuts = list(self.current_graph.Cut)
                if cuts:
                    result = self.transformation_engine.apply_transformation(
                        self.current_graph, rule, cut_id=cuts[0]
                    )
                else:
                    self._log_feedback("No cuts available for deletion", "WARNING")
                    return
            
            else:
                self._log_feedback(f"Transformation {rule.value} not implemented in demo", "WARNING")
                return
            
            # Apply result if successful
            if result.success:
                self.current_graph = result.new_graph
                self.selected_elements.clear()
                self._parse_and_display()  # Refresh display
                self._log_feedback(f"Transformation applied: {result.description}")
            else:
                self._log_feedback(f"Transformation failed: {result.error_message}", "ERROR")
        
        except Exception as e:
            self._log_feedback(f"Transformation error: {str(e)}", "ERROR")
    
    def _display_action_feedback(self, action_name: str, feedback: ValidationFeedback):
        """Display feedback for an action."""
        
        feedback_text = f"=== {action_name.upper()} VALIDATION ===\n"
        
        if feedback.is_valid:
            feedback_text += "✓ Action is valid\n\n"
        else:
            feedback_text += "✗ Action is invalid\n\n"
        
        feedback_text += f"Message: {feedback.message}\n\n"
        
        if feedback.suggestions:
            feedback_text += "SUGGESTIONS:\n"
            for suggestion in feedback.suggestions:
                feedback_text += f"  • {suggestion}\n"
            feedback_text += "\n"
        
        if feedback.warnings:
            feedback_text += "WARNINGS:\n"
            for warning in feedback.warnings:
                feedback_text += f"  • {warning}\n"
            feedback_text += "\n"
        
        if feedback.available_transformations:
            feedback_text += "AVAILABLE TRANSFORMATIONS:\n"
            for transform in feedback.available_transformations[:3]:  # Show first 3
                feedback_text += f"  • {transform['description']}\n"
            feedback_text += "\n"
        
        self._display_feedback(feedback_text)
    
    def _display_feedback(self, text: str):
        """Display feedback in the feedback text area."""
        
        self.feedback_text.delete(1.0, tk.END)
        self.feedback_text.insert(1.0, text)
    
    def _log_feedback(self, message: str, level: str = "INFO"):
        """Log a feedback message."""
        
        current_text = self.feedback_text.get(1.0, tk.END)
        new_text = f"[{level}] {message}\n\n{current_text}"
        
        self.feedback_text.delete(1.0, tk.END)
        self.feedback_text.insert(1.0, new_text)
    
    def _on_validation_update(self, feedback: ValidationFeedback):
        """Handle validation system updates."""
        
        self.current_feedback = feedback
        # Could update UI elements based on real-time feedback
    
    def run(self):
        """Run the demonstration."""
        
        self.root.mainloop()


def main():
    """Main function to run the Phase 3 demonstration."""
    
    print("Starting Phase 3 Validation & Transformation Demo...")
    print("This demo shows:")
    print("1. Real-time validation of EG operations")
    print("2. Formal transformation rules (Double Cut, Erasure, etc.)")
    print("3. Background validation feedback")
    print("4. Integration with selection-driven workflow")
    print()
    
    try:
        demo = Phase3ValidationDemo()
        demo.run()
    except Exception as e:
        print(f"Demo failed to start: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
