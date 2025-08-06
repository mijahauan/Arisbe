#!/usr/bin/env python3
"""
Core Pipeline Validation Test Suite

This test suite validates the complete EGIF→EGI→EGDF pipeline and API contracts
at every development stage to prevent regressions and ensure architectural compliance.

CRITICAL: All development must pass these tests before integration.
"""

import sys
import os
import unittest
from typing import Dict, List, Optional

# Ensure src directory is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Core pipeline imports
from egif_parser_dau import EGIFParser
from egi_core_dau import RelationalGraphWithCuts
from egdf_parser import EGDFParser, EGDFLayoutGenerator
from graphviz_layout_engine_v2 import GraphvizLayoutEngine
from corpus_loader import get_corpus_loader
from pipeline_contracts import (
    validate_relational_graph_with_cuts,
    validate_layout_result,
    validate_spatial_primitive,
    validate_full_pipeline,
    ContractViolationError
)

class CorePipelineTests(unittest.TestCase):
    """Core tests that must pass for any valid development."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_egifs = [
            '(Human "Socrates")',
            '(Human "Socrates") (Mortal "Socrates")',
            '*x (Human x) ~[ (Mortal x) ]',
            '(Human "Socrates") ~[ (Mortal "Socrates") ]',
            '*x *y (Loves x y) ~[ (Happy x) ]',
            '*x ~[ ~[ (P x) ] ]',  # Double cut
        ]
        
        self.layout_engine = GraphvizLayoutEngine()
        
        # Load corpus for testing
        try:
            self.corpus_loader = get_corpus_loader()
            self.corpus_available = True
        except Exception as e:
            print(f"Warning: Corpus not available for testing: {e}")
            self.corpus_available = False
    
    def test_egif_to_egi_pipeline(self):
        """Test EGIF → EGI conversion with API contract validation."""
        for egif_text in self.test_egifs:
            with self.subTest(egif=egif_text):
                # Parse EGIF to EGI
                parser = EGIFParser(egif_text)
                egi = parser.parse()
                
                # Validate EGI structure
                self.assertIsInstance(egi, RelationalGraphWithCuts)
                self.assertIsNotNone(egi.V)  # Vertices
                self.assertIsNotNone(egi.E)  # Edges
                self.assertIsNotNone(egi.nu)  # Nu mapping
                self.assertIsNotNone(egi.area)  # Area assignment
                self.assertIsNotNone(egi.rel)  # Relation labels
                
                # Validate API contract compliance
                try:
                    validate_relational_graph_with_cuts(egi)
                except ContractViolationError as e:
                    self.fail(f"EGI contract violation for '{egif_text}': {e}")
    
    def test_egi_to_egdf_pipeline(self):
        """Test EGI → EGDF conversion with API contract validation."""
        for egif_text in self.test_egifs:
            with self.subTest(egif=egif_text):
                # Parse EGIF to EGI
                parser = EGIFParser(egif_text)
                egi = parser.parse()
                
                # Generate layout
                layout_result = self.layout_engine.create_layout_from_graph(egi)
                
                # Convert to EGDF
                egdf_generator = EGDFLayoutGenerator()
                layout_primitives = list(layout_result.primitives.values())
                egdf_doc = egdf_generator.create_egdf_from_egi(egi, layout_primitives)
                
                # Validate EGDF structure
                self.assertIsNotNone(egdf_doc)
                self.assertTrue(hasattr(egdf_doc, 'metadata'))
                self.assertTrue(hasattr(egdf_doc, 'canonical_egi'))
                self.assertTrue(hasattr(egdf_doc, 'visual_layout'))
                
                # Validate API contract compliance
                # EGDF contract validation will be implemented
                # as part of complete pipeline enforcement
                pass
    
    def test_full_round_trip_pipeline(self):
        """Test complete EGIF → EGI → EGDF → EGI → EGIF round-trip."""
        for egif_text in self.test_egifs:
            with self.subTest(egif=egif_text):
                # Forward: EGIF → EGI → EGDF
                parser = EGIFParser(egif_text)
                original_egi = parser.parse()
                
                layout_result = self.layout_engine.create_layout_from_graph(original_egi)
                
                egdf_generator = EGDFLayoutGenerator()
                layout_primitives = list(layout_result.primitives.values())
                egdf_doc = egdf_generator.create_egdf_from_egi(original_egi, layout_primitives)
                
                # Backward: EGDF → EGI → EGIF
                egdf_parser = EGDFParser()
                reconstructed_egi = egdf_parser.extract_egi_from_egdf(egdf_doc)
                
                # Validate structural equivalence
                self.assertEqual(len(original_egi.V), len(reconstructed_egi.V))
                self.assertEqual(len(original_egi.E), len(reconstructed_egi.E))
                self.assertEqual(len(original_egi.Cut), len(reconstructed_egi.Cut))
                
                # Validate nu mapping preservation
                self.assertEqual(original_egi.nu, reconstructed_egi.nu)
    
    def test_layout_engine_contract_compliance(self):
        """Test layout engine API contract compliance."""
        for egif_text in self.test_egifs:
            with self.subTest(egif=egif_text):
                parser = EGIFParser(egif_text)
                egi = parser.parse()
                
                # Generate layout
                layout_result = self.layout_engine.create_layout_from_graph(egi)
                
                # Validate layout result structure
                self.assertTrue(hasattr(layout_result, 'primitives'))
                self.assertIsInstance(layout_result.primitives, dict)
                
                # Validate spatial primitives
                for element_id, primitive in layout_result.primitives.items():
                    self.assertTrue(hasattr(primitive, 'element_id'))
                    self.assertTrue(hasattr(primitive, 'element_type'))
                    self.assertTrue(hasattr(primitive, 'position'))
                    self.assertTrue(hasattr(primitive, 'bounds'))
                    
                    # Validate API contract compliance
                    try:
                        validate_spatial_primitive(primitive)
                    except ContractViolationError as e:
                        self.fail(f"Spatial primitive contract violation: {e}")
    
    def test_corpus_integration(self):
        """Test corpus integration and example loading."""
        if not self.corpus_available:
            self.skipTest("Corpus not available")
        
        # Validate corpus loader
        self.assertIsNotNone(self.corpus_loader)
        self.assertGreater(len(self.corpus_loader.examples), 0)
        
        # Test corpus examples through pipeline
        for example_id, example in list(self.corpus_loader.examples.items())[:5]:  # Test first 5
            with self.subTest(example_id=example_id):
                if not example.egif_expression:
                    continue
                
                # Test pipeline with corpus example
                parser = EGIFParser(example.egif_expression)
                egi = parser.parse()
                
                # Validate EGI structure
                self.assertIsInstance(egi, RelationalGraphWithCuts)
                
                # Test layout generation
                layout_result = self.layout_engine.create_layout_from_graph(egi)
                self.assertTrue(hasattr(layout_result, 'primitives'))
    
    def test_no_deprecated_references(self):
        """Test that no deprecated code references exist in core modules."""
        deprecated_patterns = [
            'hook_line',
            'HookLine',
            'add_hook_line',
            '_render_hook_line'
        ]
        
        core_modules = [
            'src/egi_core_dau.py',
            'src/egif_parser_dau.py',
            'src/egdf_parser.py',
            'src/graphviz_layout_engine_v2.py',
            'src/corpus_loader.py'
        ]
        
        for module_path in core_modules:
            full_path = os.path.join(os.path.dirname(__file__), '..', module_path)
            if os.path.exists(full_path):
                with open(full_path, 'r') as f:
                    content = f.read()
                    
                for pattern in deprecated_patterns:
                    self.assertNotIn(pattern, content, 
                                   f"Deprecated pattern '{pattern}' found in {module_path}")

class PySide6BackendTests(unittest.TestCase):
    """Tests to ensure PySide6/QPainter backend compliance."""
    
    def test_pyside6_availability(self):
        """Test that PySide6 is available and properly configured."""
        try:
            from PySide6.QtWidgets import QApplication, QWidget
            from PySide6.QtGui import QPainter, QPen, QBrush
            from PySide6.QtCore import Qt
        except ImportError as e:
            self.fail(f"PySide6 not available: {e}")
    
    def test_no_tkinter_in_core(self):
        """Test that core modules don't use Tkinter."""
        core_modules = [
            'src/egi_core_dau.py',
            'src/egif_parser_dau.py',
            'src/egdf_parser.py',
            'src/graphviz_layout_engine_v2.py'
        ]
        
        for module_path in core_modules:
            full_path = os.path.join(os.path.dirname(__file__), '..', module_path)
            if os.path.exists(full_path):
                with open(full_path, 'r') as f:
                    content = f.read()
                    self.assertNotIn('import tkinter', content,
                                   f"Tkinter import found in core module {module_path}")
                    self.assertNotIn('from tkinter', content,
                                   f"Tkinter import found in core module {module_path}")

def run_core_tests():
    """Run core pipeline tests and return results."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add core test classes
    suite.addTests(loader.loadTestsFromTestCase(CorePipelineTests))
    suite.addTests(loader.loadTestsFromTestCase(PySide6BackendTests))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    print("=" * 60)
    print("ARISBE CORE PIPELINE VALIDATION TESTS")
    print("=" * 60)
    print("Testing EGIF→EGI→EGDF pipeline, API contracts, and architectural compliance")
    print()
    
    success = run_core_tests()
    
    if success:
        print("\n✅ ALL CORE TESTS PASSED - Pipeline is functioning correctly")
        sys.exit(0)
    else:
        print("\n❌ CORE TESTS FAILED - Pipeline has regressions")
        sys.exit(1)
