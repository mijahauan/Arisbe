#!/usr/bin/env python3
"""
Minimal Pipeline Test - Validate What Actually Works

This establishes the baseline of what's actually working in the pipeline
before we enforce the complete architectural discipline.

CRITICAL: This must pass before any new development.
"""

import sys
import os
import unittest

# Ensure src directory is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Test what we actually have
from egif_parser_dau import EGIFParser
from egi_core_dau import RelationalGraphWithCuts
from graphviz_layout_engine_v2 import GraphvizLayoutEngine

class MinimalPipelineTest(unittest.TestCase):
    """Test the minimal working pipeline we actually have."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_egifs = [
            '(Human "Socrates")',
            '(Human "Socrates") ~[ (Mortal "Socrates") ]'
        ]
        self.layout_engine = GraphvizLayoutEngine()
    
    def test_egif_to_egi_works(self):
        """Test that EGIF → EGI actually works."""
        for egif_text in self.test_egifs:
            with self.subTest(egif=egif_text):
                # Parse EGIF to EGI
                parser = EGIFParser(egif_text)
                egi = parser.parse()
                
                # Validate basic EGI structure
                self.assertIsInstance(egi, RelationalGraphWithCuts)
                self.assertIsNotNone(egi.V)  # Vertices
                self.assertIsNotNone(egi.E)  # Edges
                self.assertIsNotNone(egi.nu)  # Nu mapping
                
                print(f"✅ EGIF→EGI works: {egif_text}")
    
    def test_egi_to_layout_works(self):
        """Test that EGI → Layout actually works."""
        for egif_text in self.test_egifs:
            with self.subTest(egif=egif_text):
                # Parse EGIF to EGI
                parser = EGIFParser(egif_text)
                egi = parser.parse()
                
                # Generate layout
                layout_result = self.layout_engine.create_layout_from_graph(egi)
                
                # Validate layout result
                self.assertIsNotNone(layout_result)
                self.assertTrue(hasattr(layout_result, 'primitives'))
                self.assertIsInstance(layout_result.primitives, dict)
                self.assertGreater(len(layout_result.primitives), 0)
                
                print(f"✅ EGI→Layout works: {len(layout_result.primitives)} primitives")
    
    def test_corpus_availability(self):
        """Test that corpus is available."""
        try:
            from corpus_loader import get_corpus_loader
            corpus_loader = get_corpus_loader()
            self.assertIsNotNone(corpus_loader)
            self.assertGreater(len(corpus_loader.examples), 0)
            print(f"✅ Corpus available: {len(corpus_loader.examples)} examples")
        except Exception as e:
            self.fail(f"Corpus not available: {e}")
    
    def test_pyside6_availability(self):
        """Test that PySide6 is available."""
        try:
            from PySide6.QtWidgets import QApplication, QWidget
            from PySide6.QtGui import QPainter, QPen, QBrush
            from PySide6.QtCore import Qt
            print("✅ PySide6 available and importable")
        except ImportError as e:
            self.fail(f"PySide6 not available: {e}")

def main():
    """Run minimal pipeline tests."""
    print("🎯 MINIMAL PIPELINE VALIDATION")
    print("=" * 50)
    print("Testing what actually works before enforcing discipline...")
    print()
    
    # Run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(MinimalPipelineTest)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("\n✅ MINIMAL PIPELINE WORKS")
        print("Ready to enforce architectural discipline")
        return True
    else:
        print("\n❌ MINIMAL PIPELINE BROKEN")
        print("Must fix basic functionality before proceeding")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
