#!/usr/bin/env python3
"""
Complete Integration Demo: Corrected Edge Rendering Architecture

Demonstrates the full pipeline with corrected causality:
1. EGIF Loading: ν mapping → visual elements → rendering
2. Interactive Composition: user actions → visual elements → ν mapping updates → rendering
3. Selection System: operates on primary visual elements

This shows the corrected architecture working end-to-end with actual visual display.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional

from visual_elements_primary import (
    VisualDiagram, LineOfIdentity, PredicateElement, CutElement, 
    Coordinate, ElementState
)
from diagram_controller_corrected import DiagramController
from primary_visual_renderer import PrimaryVisualRenderer, TkinterCanvas, PrimaryVisualTheme
from egi_core_dau import create_empty_graph, create_vertex, create_edge


class CorrectedArchitectureDemo:
    """
    Complete demo of corrected edge rendering architecture with visual display.
    
    Shows both EGIF loading and interactive composition with proper causality.
    """
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Corrected Edge Rendering Architecture Demo")
        self.root.geometry("1000x700")
        
        # Create UI
        self._setup_ui()
        
        # Initialize corrected architecture components
        self.canvas_backend = TkinterCanvas(self.canvas)
        self.renderer = PrimaryVisualRenderer(self.canvas_backend)
        self.renderer.enable_debug_hooks(True)  # Show hook positions for demo
        
        # Start with empty controller
        self.controller = None
        self.current_diagram = None
        
        # Demo state
        self.demo_step = 0
        
        print("🎯 Corrected Architecture Demo initialized")
        print("   Ready to demonstrate proper causality and selection")
    
    def _setup_ui(self):
        """Create the demo UI."""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Control panel
        control_frame = ttk.LabelFrame(main_frame, text="Demo Controls", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Demo buttons
        ttk.Button(control_frame, text="1. Load EGIF Example", 
                  command=self.demo_egif_loading).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="2. Interactive Composition", 
                  command=self.demo_interactive_composition).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="3. User Attachment", 
                  command=self.demo_user_attachment).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="4. Selection Demo", 
                  command=self.demo_selection).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Clear", 
                  command=self.clear_demo).pack(side=tk.LEFT, padx=5)
        
        # Info panel
        info_frame = ttk.LabelFrame(main_frame, text="Architecture Info", padding=10)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.info_text = tk.Text(info_frame, height=4, wrap=tk.WORD)
        self.info_text.pack(fill=tk.X)
        
        # Canvas frame
        canvas_frame = ttk.LabelFrame(main_frame, text="Visual Diagram", padding=10)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas
        self.canvas = tk.Canvas(canvas_frame, bg="white", width=800, height=400)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind canvas events for selection demo
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        
        # Initial info
        self._update_info("🎯 Corrected Edge Rendering Architecture Demo\n" +
                         "Click buttons to see proper causality: Visual Elements → ν mapping updates")
    
    def demo_egif_loading(self):
        """Demo 1: EGIF Loading (ν mapping → visual elements)."""
        print("\n🔍 DEMO 1: EGIF Loading")
        
        # Create EGI with ν mapping (simulates EGIF loading)
        egi = create_empty_graph()
        
        # Human(Socrates)
        socrates = create_vertex(label="Socrates", is_generic=False)
        human_edge = create_edge()
        
        egi = egi.with_vertex(socrates)
        egi = egi.with_edge(human_edge, (socrates.id,), "Human")
        
        # ~[ Mortal(Socrates) ]
        cut = create_cut()
        mortal_edge = create_edge()
        
        egi = egi.with_cut(cut)
        egi = egi.with_edge(mortal_edge, (socrates.id,), "Mortal", context_id=cut.id)
        
        # Create controller and load from EGI
        self.controller = DiagramController(egi)
        
        # Provide layout positions for better visualization
        layout_positions = {
            'predicates': {
                human_edge.id: {'x': 150, 'y': 100},
                mortal_edge.id: {'x': 150, 'y': 200}
            },
            'vertices': {
                socrates.id: {'x': 100, 'y': 150}
            }
        }
        
        self.current_diagram = self.controller.load_from_egi(layout_positions)
        
        # Add a cut for visual containment
        cut_element = CutElement(bounds=(120, 170, 200, 230))
        cut_element.element_id = f"cut_{cut.id}"
        self.current_diagram.add_cut(cut_element)
        
        # Render the diagram
        self.renderer.render_visual_diagram(self.current_diagram)
        
        self._update_info("✅ EGIF Loading Complete\n" +
                         f"Created from ν mapping: {dict(egi.nu)}\n" +
                         "Visual elements created from existing EGI structure\n" +
                         "Heavy lines show predicate connections per Dau's formalism")
        
        print("✅ EGIF loading demo complete")
    
    def demo_interactive_composition(self):
        """Demo 2: Interactive Composition (user creates visual elements first)."""
        print("\n🎨 DEMO 2: Interactive Composition")
        
        if not self.controller:
            # Start with empty EGI
            egi = create_empty_graph()
            self.controller = DiagramController(egi)
            self.current_diagram = self.controller.get_visual_diagram()
        
        # User creates unattached elements (Warmup mode)
        new_line = self.controller.create_unattached_line(
            start_pos=Coordinate(300, 150),
            end_pos=Coordinate(380, 150),
            label="Plato"
        )
        
        new_predicate = self.controller.create_unattached_predicate(
            position=Coordinate(450, 150),
            text="Philosopher"
        )
        
        # Render updated diagram
        self.renderer.render_visual_diagram(self.current_diagram)
        
        self._update_info("✅ Interactive Composition Complete\n" +
                         "User created unattached visual elements first\n" +
                         "Corresponding EGI vertices/edges created automatically\n" +
                         "Gray elements show unattached state (Warmup mode)")
        
        print("✅ Interactive composition demo complete")
    
    def demo_user_attachment(self):
        """Demo 3: User Attachment (visual action → ν mapping update)."""
        print("\n🔗 DEMO 3: User Attachment Action")
        
        if not self.current_diagram:
            self._update_info("❌ Run Interactive Composition first!")
            return
        
        # Find unattached elements
        unattached_lines = [line for line in self.current_diagram.lines_of_identity.values() 
                           if line.state == ElementState.UNATTACHED]
        unattached_predicates = [pred for pred in self.current_diagram.predicates.values() 
                               if pred.state == ElementState.UNATTACHED]
        
        if not unattached_lines or not unattached_predicates:
            self._update_info("❌ No unattached elements found! Run Interactive Composition first.")
            return
        
        # User attaches line to predicate (visual action)
        line = unattached_lines[0]
        predicate = unattached_predicates[0]
        
        print(f"   Attaching {line.element_id} to {predicate.element_id}")
        
        # This is the KEY METHOD: visual action updates ν mapping
        success = self.controller.attach_line_to_predicate(
            line_id=line.element_id,
            predicate_id=predicate.element_id,
            hook_position=0,
            line_end="end"
        )
        
        # Render updated diagram
        self.renderer.render_visual_diagram(self.current_diagram)
        
        # Show updated ν mapping
        nu_mapping = dict(self.controller.egi.nu)
        
        self._update_info("✅ User Attachment Complete\n" +
                         f"Visual action updated ν mapping: {nu_mapping}\n" +
                         "Line changed from gray (unattached) to black (attached)\n" +
                         "EGI automatically synchronized with visual state")
        
        print("✅ User attachment demo complete")
    
    def demo_selection(self):
        """Demo 4: Selection System (operates on primary visual elements)."""
        print("\n🎯 DEMO 4: Selection System")
        
        if not self.current_diagram:
            self._update_info("❌ Run previous demos first!")
            return
        
        # Select various elements to show selection overlays
        elements = self.current_diagram.get_all_elements()
        
        # Clear previous selections
        for elem in elements:
            elem.deselect()
        
        # Select first few elements
        selected_count = 0
        for elem in elements[:3]:  # Select first 3 elements
            elem.select()
            selected_count += 1
        
        # Render with selection overlays
        self.renderer.render_visual_diagram(self.current_diagram)
        
        self._update_info("✅ Selection System Active\n" +
                         f"Selected {selected_count} primary visual elements\n" +
                         "Blue overlays show selected elements\n" +
                         "Selection operates on real visual objects, not ν mapping derivatives")
        
        print("✅ Selection demo complete")
    
    def clear_demo(self):
        """Clear the demo and reset."""
        print("\n🧹 Clearing demo")
        
        self.canvas.delete("all")
        self.controller = None
        self.current_diagram = None
        self.demo_step = 0
        
        self._update_info("🎯 Demo cleared - ready for new demonstration")
    
    def _on_canvas_click(self, event):
        """Handle canvas clicks for interactive selection."""
        if not self.current_diagram:
            return
        
        click_pos = Coordinate(event.x, event.y)
        print(f"Canvas clicked at ({click_pos.x}, {click_pos.y})")
        
        # Simple click-to-select logic (could be enhanced)
        for element in self.current_diagram.get_all_elements():
            if isinstance(element, LineOfIdentity):
                # Check if click is near line
                if self._point_near_line(click_pos, element.start_pos, element.end_pos, threshold=10):
                    element.select() if not element.selected else element.deselect()
                    self.renderer.render_visual_diagram(self.current_diagram)
                    print(f"Toggled selection for line {element.element_id}")
                    break
            elif isinstance(element, PredicateElement):
                # Check if click is near predicate
                if self._point_near_point(click_pos, element.position, threshold=30):
                    element.select() if not element.selected else element.deselect()
                    self.renderer.render_visual_diagram(self.current_diagram)
                    print(f"Toggled selection for predicate {element.element_id}")
                    break
    
    def _point_near_line(self, point: Coordinate, line_start: Coordinate, line_end: Coordinate, threshold: float) -> bool:
        """Check if point is near a line segment."""
        # Simplified distance calculation
        import math
        
        # Distance from point to line segment
        A = point.x - line_start.x
        B = point.y - line_start.y
        C = line_end.x - line_start.x
        D = line_end.y - line_start.y
        
        dot = A * C + B * D
        len_sq = C * C + D * D
        
        if len_sq == 0:
            return math.sqrt(A * A + B * B) <= threshold
        
        param = dot / len_sq
        
        if param < 0:
            xx, yy = line_start.x, line_start.y
        elif param > 1:
            xx, yy = line_end.x, line_end.y
        else:
            xx = line_start.x + param * C
            yy = line_start.y + param * D
        
        dx = point.x - xx
        dy = point.y - yy
        return math.sqrt(dx * dx + dy * dy) <= threshold
    
    def _point_near_point(self, point1: Coordinate, point2: Coordinate, threshold: float) -> bool:
        """Check if two points are within threshold distance."""
        import math
        dx = point1.x - point2.x
        dy = point1.y - point2.y
        return math.sqrt(dx * dx + dy * dy) <= threshold
    
    def _update_info(self, text: str):
        """Update the info panel."""
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, text)
    
    def run(self):
        """Run the demo application."""
        print("🚀 Starting Corrected Architecture Demo")
        print("   Click buttons to see proper causality in action!")
        self.root.mainloop()


def main():
    """Run the complete integration demo."""
    print("=== Corrected Edge Rendering Architecture Demo ===")
    print("This demo shows the complete corrected architecture:")
    print("1. EGIF Loading: ν mapping → visual elements")
    print("2. Interactive Composition: visual elements → ν mapping updates")
    print("3. Selection System: operates on primary visual elements")
    print("4. Proper Dau formalism compliance\n")
    
    demo = CorrectedArchitectureDemo()
    demo.run()


if __name__ == "__main__":
    main()
