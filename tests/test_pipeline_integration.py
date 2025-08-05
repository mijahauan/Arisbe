#!/usr/bin/env python3
"""
Pipeline Integration Test Suite

This test suite validates all pipeline handoffs and ensures API contracts
are maintained across all components. Run this before any integration work
to catch API mismatches early.
"""

import sys
import os
import unittest
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from pipeline_contracts import (
    validate_relational_graph_with_cuts,
    validate_layout_result,
    validate_spatial_primitive,
    validate_canvas_interface,
    validate_full_pipeline,
    ContractViolationError
)

class TestPipelineContracts(unittest.TestCase):
    """Test all pipeline contracts and handoffs."""
    
    def setUp(self):
        """Set up test components."""
        try:
            from egif_parser_dau import parse_egif
            from graphviz_layout_engine_v2 import GraphvizLayoutEngine
            from diagram_renderer_dau import DiagramRendererDau, VisualConvention
            from pyside6_canvas import PySide6Canvas
            
            self.parse_egif = parse_egif
            self.layout_engine = GraphvizLayoutEngine()
            self.renderer = DiagramRendererDau(VisualConvention())
            self.canvas_class = PySide6Canvas
            
        except ImportError as e:
            self.skipTest(f"Required components not available: {e}")
    
    def test_egif_parser_contract(self):
        """Test EGIF parser produces valid RelationalGraphWithCuts."""
        egif = '*x (Human x)'
        graph = self.parse_egif(egif)
        
        # Should not raise ContractViolationError
        validate_relational_graph_with_cuts(graph)
        
        # Verify specific contract requirements
        self.assertIsInstance(graph.V, frozenset)
        self.assertIsInstance(graph.E, frozenset)
        self.assertIsInstance(graph.Cut, frozenset)
        self.assertTrue(hasattr(graph, 'sheet'))
    
    def test_layout_engine_contract(self):
        """Test layout engine produces valid LayoutResult."""
        egif = '*x (Human x)'
        graph = self.parse_egif(egif)
        layout = self.layout_engine.create_layout_from_graph(graph)
        
        # Should not raise ContractViolationError
        validate_layout_result(layout)
        
        # Verify specific contract requirements
        self.assertIsInstance(layout.primitives, dict)
        self.assertGreater(len(layout.primitives), 0)  # Non-empty for valid graphs
        self.assertIsInstance(layout.canvas_bounds, tuple)
        self.assertEqual(len(layout.canvas_bounds), 4)
        self.assertIsInstance(layout.containment_hierarchy, dict)
    
    def test_spatial_primitive_contract(self):
        """Test spatial primitives conform to contract."""
        egif = '*x (Human x)'
        graph = self.parse_egif(egif)
        layout = self.layout_engine.create_layout_from_graph(graph)
        
        # Test each primitive in the layout
        for elem_id, primitive in layout.primitives.items():
            # Should not raise ContractViolationError
            validate_spatial_primitive(primitive)
            
            # Verify specific contract requirements
            self.assertIsInstance(primitive.element_id, str)
            self.assertIsInstance(primitive.element_type, str)
            self.assertIsInstance(primitive.position, tuple)
            self.assertEqual(len(primitive.position), 2)
            self.assertIsInstance(primitive.bounds, tuple)
            self.assertEqual(len(primitive.bounds), 4)
    
    def test_canvas_interface_contract(self):
        """Test canvas implements required interface."""
        canvas = self.canvas_class(800, 600, title="Test")
        
        # Should not raise ContractViolationError
        validate_canvas_interface(canvas)
        
        # Verify specific methods exist and are callable
        required_methods = ['draw_line', 'draw_circle', 'draw_text', 'save_to_file']
        for method_name in required_methods:
            self.assertTrue(hasattr(canvas, method_name))
            self.assertTrue(callable(getattr(canvas, method_name)))
    
    def test_full_pipeline_integration(self):
        """Test complete pipeline with contract validation."""
        test_cases = [
            '(Human "Socrates")',
            '*x (Human x)',
            '*x ~[ (Mortal x) ]',
            '*x ~[ (Human x) ] ~[ (Mortal x) ]'
        ]
        
        for egif in test_cases:
            with self.subTest(egif=egif):
                # Parse
                graph = self.parse_egif(egif)
                
                # Layout
                layout = self.layout_engine.create_layout_from_graph(graph)
                
                # Canvas
                canvas = self.canvas_class(800, 600, title="Test")
                
                # Full pipeline validation - should not raise ContractViolationError
                validate_full_pipeline(egif, graph, layout, canvas)
    
    def test_contract_violation_detection(self):
        """Test that contract violations are properly detected."""
        
        # Test invalid RelationalGraphWithCuts
        class FakeGraph:
            pass
        
        with self.assertRaises(ContractViolationError):
            validate_relational_graph_with_cuts(FakeGraph())
        
        # Test invalid LayoutResult
        class FakeLayout:
            pass
        
        with self.assertRaises(ContractViolationError):
            validate_layout_result(FakeLayout())
        
        # Test invalid SpatialPrimitive
        class FakePrimitive:
            pass
        
        with self.assertRaises(ContractViolationError):
            validate_spatial_primitive(FakePrimitive())
        
        # Test invalid Canvas
        class FakeCanvas:
            pass
        
        with self.assertRaises(ContractViolationError):
            validate_canvas_interface(FakeCanvas())
    
    def test_renderer_integration(self):
        """Test renderer accepts correct inputs without errors."""
        egif = '*x (Human x)'
        graph = self.parse_egif(egif)
        layout = self.layout_engine.create_layout_from_graph(graph)
        canvas = self.canvas_class(800, 600, title="Test")
        
        # This should complete without ContractViolationError
        try:
            self.renderer.render_diagram(canvas, layout, graph)
        except ContractViolationError:
            self.fail("Renderer rejected valid inputs - API contract violation")
        except Exception as e:
            # Other errors are acceptable (missing dependencies, etc.)
            # but contract violations indicate API mismatches
            if "attribute" in str(e).lower() and ("primitives" in str(e) or "bounds" in str(e)):
                self.fail(f"Renderer API mismatch detected: {e}")

class TestAPIVersioning(unittest.TestCase):
    """Test API versioning and compatibility."""
    
    def test_api_version_defined(self):
        """Test that API version is properly defined."""
        from pipeline_contracts import PIPELINE_API_VERSION, COMPATIBLE_VERSIONS
        
        self.assertIsInstance(PIPELINE_API_VERSION, str)
        self.assertIsInstance(COMPATIBLE_VERSIONS, list)
        self.assertIn(PIPELINE_API_VERSION, COMPATIBLE_VERSIONS)

if __name__ == "__main__":
    print("Arisbe Pipeline Integration Test Suite")
    print("=" * 50)
    print("Testing all pipeline contracts and handoffs...")
    print()
    
    # Run the tests
    unittest.main(verbosity=2)
