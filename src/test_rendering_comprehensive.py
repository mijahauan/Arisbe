#!/usr/bin/env python3
"""
Comprehensive Rendering Test Suite

Tests various EG structures to verify correct layout and rendering:
- Nested cuts (double cuts, triple cuts)
- Multiple predicates in same area
- Complex identity lines
- Edge cases and stress tests
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from egif_parser_dau import EGIFParser
from layout_engine_clean import CleanLayoutEngine
from diagram_renderer_clean import CleanDiagramRenderer
from canvas_backends.tkinter_backend import TkinterCanvas
import tkinter as tk
from tkinter import ttk

class ComprehensiveRenderingTester:
    def __init__(self):
        self.parser = EGIFParser()
        self.layout_engine = CleanLayoutEngine()
        
    def test_case(self, name: str, egif_string: str, description: str):
        """Test a single EGIF case with detailed output."""
        print(f"\n{'='*60}")
        print(f"TEST CASE: {name}")
        print(f"EGIF: {egif_string}")
        print(f"Description: {description}")
        print('='*60)
        
        try:
            # Parse EGIF
            graph = self.parser.parse(egif_string)
            print(f"✅ Parsing successful")
            
            # Generate layout
            layout_result = self.layout_engine.layout_graph(graph)
            print(f"✅ Layout successful - {len(layout_result.primitives)} primitives")
            
            # Count elements by type and area
            cuts = sum(1 for p in layout_result.primitives.values() if p.element_type == 'cut')
            vertices = sum(1 for p in layout_result.primitives.values() if p.element_type == 'vertex')
            edges = sum(1 for p in layout_result.primitives.values() if p.element_type == 'edge')
            
            print(f"   Cuts: {cuts}, Vertices: {vertices}, Edges: {edges}")
            
            # Analyze area containment
            area_analysis = self._analyze_areas(graph, layout_result)
            for area_info in area_analysis:
                print(f"   {area_info}")
            
            # Create GUI window for visual verification
            self._create_visual_test(name, graph, layout_result)
            
            return True
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _analyze_areas(self, graph, layout_result):
        """Analyze area containment for debugging."""
        analysis = []
        
        # Group primitives by area
        areas = {}
        for primitive in layout_result.primitives.values():
            area = getattr(primitive, 'parent_area', 'unknown')
            if area not in areas:
                areas[area] = []
            areas[area].append(primitive)
        
        for area_id, primitives in areas.items():
            if area_id == graph.sheet:
                area_name = "SHEET"
            else:
                area_name = f"CUT {area_id[-8:]}"
            
            types = {}
            for p in primitives:
                ptype = p.element_type
                if ptype not in types:
                    types[ptype] = 0
                types[ptype] += 1
            
            type_summary = ", ".join(f"{count} {ptype}{'s' if count > 1 else ''}" 
                                   for ptype, count in types.items())
            analysis.append(f"{area_name}: {type_summary}")
        
        return analysis
    
    def _create_visual_test(self, name: str, graph, layout_result):
        """Create a visual test window."""
        window = tk.Toplevel()
        window.title(f"Rendering Test: {name}")
        window.geometry("600x500")
        
        # Create canvas
        canvas_frame = ttk.Frame(window)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        canvas = TkinterCanvas(canvas_frame, width=580, height=400)
        renderer = CleanDiagramRenderer(canvas)
        
        # Render the diagram
        renderer.render_diagram(layout_result, graph)
        
        # Add close button
        close_btn = ttk.Button(window, text="Close", command=window.destroy)
        close_btn.pack(pady=5)
        
        return window

def run_comprehensive_tests():
    """Run all comprehensive rendering tests."""
    tester = ComprehensiveRenderingTester()
    
    # Create main window
    root = tk.Tk()
    root.title("Comprehensive Rendering Tests")
    root.geometry("400x300")
    
    # Test cases
    test_cases = [
        # Basic cases
        ("Simple Predicate", 
         "(Human Socrates)", 
         "Single predicate with constant"),
        
        ("Simple Cut", 
         "~[ (Mortal Socrates) ]", 
         "Single predicate inside cut"),
        
        # Double cuts
        ("Double Cut", 
         "~[ ~[ (Human Socrates) ] ]", 
         "Double negation - should show nested circles"),
        
        ("Triple Cut", 
         "~[ ~[ ~[ (Wise Socrates) ] ] ]", 
         "Triple negation - three nested circles"),
        
        # Multiple predicates
        ("Multiple Predicates Same Area", 
         "(Human Socrates) (Mortal Socrates) (Wise Socrates)", 
         "Three predicates at sheet level - should be well separated"),
        
        ("Multiple Predicates In Cut", 
         "~[ (Human Socrates) (Mortal Socrates) (Wise Socrates) ]", 
         "Three predicates inside cut - should be separated within circle"),
        
        # Mixed areas
        ("Mixed Areas", 
         "(Human Socrates) ~[ (Mortal Socrates) (Wise Socrates) ]", 
         "One predicate outside, two inside cut"),
        
        # Variables and identity
        ("Variable Identity", 
         "*x (Human x) (Mortal x)", 
         "Two predicates sharing variable - connected by line of identity"),
        
        ("Variable In Cut", 
         "*x (Human x) ~[ (Mortal x) ]", 
         "Variable crosses cut boundary - line should cross circle"),
        
        ("Complex Variable", 
         "*x *y (Human x) (Loves x y) (Mortal y)", 
         "Two variables with binary relation"),
        
        # Nested with variables
        ("Nested Variable", 
         "*x (Human x) ~[ ~[ (Mortal x) ] ]", 
         "Variable crosses double cut boundary"),
        
        # Complex structures
        ("Complex Nested", 
         "*x (Human x) ~[ (Mortal x) ~[ (Wise x) ] ]", 
         "Variable crosses multiple cut levels"),
        
        ("Multiple Variables", 
         "*x *y (Human x) (Human y) ~[ (Loves x y) ]", 
         "Two variables, relation inside cut"),
        
        # Stress test
        ("Stress Test", 
         "*x *y *z (Human x) (Human y) (Human z) ~[ (Loves x y) (Loves y z) ~[ (Knows x z) ] ]", 
         "Complex structure with multiple variables and nested cuts"),
    ]
    
    # Run tests
    print("Starting Comprehensive Rendering Tests...")
    print("Each test will open a visual window for inspection.")
    
    passed = 0
    total = len(test_cases)
    
    for name, egif, description in test_cases:
        if tester.test_case(name, egif, description):
            passed += 1
    
    print(f"\n{'='*60}")
    print(f"COMPREHENSIVE TEST RESULTS: {passed}/{total} tests passed")
    print('='*60)
    
    # Keep main window open
    instruction_label = ttk.Label(root, 
        text=f"Comprehensive Rendering Tests\n\n"
             f"Results: {passed}/{total} tests passed\n\n"
             f"Visual test windows have been opened.\n"
             f"Inspect each diagram for correct rendering:\n"
             f"• Cuts should be circular\n"
             f"• Sheet-level predicates outside cuts\n"
             f"• Cut-level predicates inside cuts\n"
             f"• Lines of identity cross boundaries\n"
             f"• Proper spatial separation\n\n"
             f"Close this window when done.",
        justify=tk.CENTER)
    instruction_label.pack(expand=True)
    
    close_btn = ttk.Button(root, text="Close All", command=root.quit)
    close_btn.pack(pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    run_comprehensive_tests()
