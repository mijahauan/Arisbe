#!/usr/bin/env python3
"""
Visual Test Suite for Corrected Graphviz DOT Generation Pipeline

This script tests the corrected pipeline that now properly places predicates
inside cuts using the EGI core's get_area() method.
"""

import tkinter as tk
from tkinter import ttk
from egif_parser_dau import parse_egif
from graphviz_layout_engine_v2 import GraphvizLayoutEngine
from diagram_renderer_clean import CleanDiagramRenderer
from tkinter_backend import TkinterBackend
import time

class VisualTestSuite:
    """Visual test suite for the corrected pipeline."""
    
    def __init__(self):
        self.test_cases = [
            ("Sibling Cuts (Previously Failing)", "*x ~[ (Human x) ] ~[ (Mortal x) ]"),
            ("Mixed Cut and Sheet", "(Human \"Socrates\") ~[ (Mortal \"Socrates\") ]"),
            ("Nested Cuts", "~[ ~[ (P \"x\") ] ]"),
            ("Double Negation", "~[ ~[ *x ] ]"),
            ("Binary Relation", "*x *y (Loves x y)"),
            ("Complex Example", "*x (Human x) ~[ (Mortal x) (Wise x) ]")
        ]
        
        self.engine = GraphvizLayoutEngine()
        self.backend = TkinterBackend()
        
    def run_visual_tests(self):
        """Run all visual tests in sequence."""
        print("🎨 VISUAL TEST SUITE - Corrected Pipeline")
        print("=" * 60)
        
        for i, (test_name, egif) in enumerate(self.test_cases, 1):
            print(f"\n📋 Test {i}: {test_name}")
            print(f"EGIF: {egif}")
            print("-" * 40)
            
            try:
                # Parse and layout
                graph = parse_egif(egif)
                layout_result = self.engine.create_layout_from_graph(graph)
                
                # Count elements
                vertices = sum(1 for p in layout_result.primitives.values() if p.element_type == 'vertex')
                predicates = sum(1 for p in layout_result.primitives.values() if p.element_type == 'predicate')
                cuts = sum(1 for p in layout_result.primitives.values() if p.element_type == 'cut')
                
                print(f"✓ Layout: {vertices} vertices, {predicates} predicates, {cuts} cuts")
                
                # Create visual window
                canvas = self.backend.create_canvas(
                    800, 600, 
                    f"Test {i}: {test_name}"
                )
                renderer = CleanDiagramRenderer(canvas)
                
                # Render diagram (requires both layout_result and graph)
                renderer.render_diagram(layout_result, graph)
                
                print(f"✓ Visual rendering complete")
                print(f"🖼️  Window opened: {test_name}")
                
                # Brief pause between tests
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Test {i} failed: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n🎯 All {len(self.test_cases)} visual tests launched!")
        print("📝 Check each window to verify:")
        print("   • Predicates appear inside their correct cuts")
        print("   • Cuts are properly separated and non-overlapping")
        print("   • Vertices connect to predicates correctly")
        print("   • Overall diagram structure matches EGIF logic")
        
        # Keep all windows open
        print("\n⏳ Keeping windows open for inspection...")
        self.backend.run_event_loop()

def main():
    """Main entry point for visual tests."""
    suite = VisualTestSuite()
    suite.run_visual_tests()

if __name__ == "__main__":
    main()
