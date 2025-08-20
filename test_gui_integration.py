#!/usr/bin/env python3
"""
GUI Integration Testing Suite

Comprehensive testing for the Arisbe GUI components to validate
functionality, integration, and user workflows.
"""

import sys
import os
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

# Add src and apps to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent / 'apps'))

try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtTest import QTest
    from PySide6.QtCore import Qt
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False

class TestGUIIntegration(unittest.TestCase):
    """Test GUI component integration."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        if PYSIDE6_AVAILABLE:
            cls.app = QApplication.instance()
            if cls.app is None:
                cls.app = QApplication([])
    
    def setUp(self):
        """Set up each test."""
        self.test_egif = "*x (Human x)"
        self.test_complex_egif = "*x (Human x) ~[ (Mortal x) ]"
        
    def test_launcher_import(self):
        """Test that launcher can be imported."""
        try:
            from arisbe_launcher import ArisbeMainLauncher
            self.assertTrue(True, "Launcher imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import launcher: {e}")
            
    def test_organon_import(self):
        """Test that Organon can be imported."""
        try:
            from organon.organon_browser import OrganonBrowser
            self.assertTrue(True, "Organon imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import Organon: {e}")
            
    def test_ergasterion_import(self):
        """Test that Ergasterion can be imported."""
        try:
            from ergasterion.ergasterion_workshop import ErgasterionWorkshop
            self.assertTrue(True, "Ergasterion imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import Ergasterion: {e}")
            
    def test_agon_import(self):
        """Test that Agon can be imported."""
        try:
            from agon.agon_game import AgonGame
            self.assertTrue(True, "Agon imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import Agon: {e}")
            
    @unittest.skipUnless(PYSIDE6_AVAILABLE, "PySide6 not available")
    def test_launcher_creation(self):
        """Test launcher window creation."""
        try:
            from arisbe_launcher import ArisbeMainLauncher
            launcher = ArisbeMainLauncher()
            self.assertIsNotNone(launcher)
            launcher.close()
        except Exception as e:
            self.fail(f"Failed to create launcher: {e}")
            
    @unittest.skipUnless(PYSIDE6_AVAILABLE, "PySide6 not available")
    def test_organon_creation(self):
        """Test Organon window creation."""
        try:
            from organon.organon_browser import OrganonBrowser
            organon = OrganonBrowser()
            self.assertIsNotNone(organon)
            organon.close()
        except Exception as e:
            self.fail(f"Failed to create Organon: {e}")
            
    def test_egif_parsing_integration(self):
        """Test EGIF parsing integration."""
        try:
            from egif_parser_dau import EGIFParser
            parser = EGIFParser(self.test_egif)
            egi = parser.parse()
            self.assertIsNotNone(egi)
            self.assertEqual(len(egi.V), 1)
            self.assertEqual(len(egi.E), 1)
        except Exception as e:
            self.fail(f"EGIF parsing failed: {e}")
            
    def test_pipeline_integration(self):
        """Test canonical pipeline integration."""
        try:
            from egif_parser_dau import EGIFParser
            from canonical import CanonicalPipeline
            
            parser = EGIFParser(self.test_egif)
            egi = parser.parse()
            
            pipeline = CanonicalPipeline()
            # Test basic pipeline functionality
            egif_output = pipeline.egi_to_egif(egi)
            
            self.assertIsNotNone(egif_output)
            self.assertIsInstance(egif_output, str)
        except Exception as e:
            self.fail(f"Pipeline integration failed: {e}")
            
    def test_egdf_serialization_integration(self):
        """Test EGDF serialization integration."""
        try:
            from egif_parser_dau import EGIFParser
            from egdf_parser import EGDFParser
            from canonical import CanonicalPipeline
            
            # Parse EGIF to EGI
            parser = EGIFParser(self.test_egif)
            egi = parser.parse()
            
            # Create minimal layout for testing
            pipeline = CanonicalPipeline()
            layout_result = type('LayoutResult', (), {
                'vertex_positions': {v.id: (100 + i * 50, 100) for i, v in enumerate(egi.V)},
                'edge_positions': {e.id: (200 + i * 50, 150) for i, e in enumerate(egi.E)},
                'cut_bounds': {c.id: (50 + i * 100, 50, 150 + i * 100, 150) for i, c in enumerate(egi.Cut)}
            })()
            
            # Create EGDF
            egdf_parser = EGDFParser()
            spatial_primitives = []
            
            # Create minimal spatial primitives
            for i, vertex in enumerate(egi.V):
                spatial_primitives.append({
                    'element_id': vertex.id,
                    'element_type': 'vertex',
                    'position': (100 + i * 50, 100),
                    'bounds': (90 + i * 50, 90, 110 + i * 50, 110)
                })
            
            egdf_doc = egdf_parser.create_egdf_from_egi(egi, spatial_primitives)
            self.assertIsNotNone(egdf_doc)
            
            # Test serialization
            yaml_output = egdf_parser.egdf_to_yaml(egdf_doc)
            json_output = egdf_parser.egdf_to_json(egdf_doc)
            
            self.assertIsInstance(yaml_output, str)
            self.assertIsInstance(json_output, str)
            self.assertGreater(len(yaml_output), 0)
            self.assertGreater(len(json_output), 0)
            
        except Exception as e:
            self.fail(f"EGDF serialization integration failed: {e}")

class TestCorpusIntegration(unittest.TestCase):
    """Test corpus loading and integration."""
    
    def test_corpus_directory_exists(self):
        """Test that corpus directory exists."""
        corpus_path = Path(__file__).parent / 'corpus' / 'corpus'
        self.assertTrue(corpus_path.exists(), f"Corpus directory not found: {corpus_path}")
        
    def test_corpus_examples_exist(self):
        """Test that corpus contains examples."""
        corpus_path = Path(__file__).parent / 'corpus' / 'corpus'
        if corpus_path.exists():
            egif_files = list(corpus_path.rglob("*.egif"))
            self.assertGreater(len(egif_files), 0, "No EGIF examples found in corpus")

class TestSerializationProtection(unittest.TestCase):
    """Test serialization protection integration."""
    
    def test_structural_lock_exists(self):
        """Test that structural lock exists."""
        lock_path = Path(__file__).parent / 'src' / 'egdf_structural.lock'
        self.assertTrue(lock_path.exists(), "Structural lock file not found")
        
    def test_serialization_integrity(self):
        """Test serialization integrity validation."""
        try:
            from egdf_structural_lock import EGDFStructuralProtector
            
            protector = EGDFStructuralProtector()
            is_valid, errors = protector.validate_structural_integrity()
            
            self.assertTrue(is_valid, f"Serialization integrity failed: {errors}")
            
        except Exception as e:
            self.fail(f"Serialization integrity test failed: {e}")

def run_basic_tests():
    """Run basic integration tests."""
    print("Running Arisbe GUI Integration Tests")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestGUIIntegration))
    suite.addTest(unittest.makeSuite(TestCorpusIntegration))
    suite.addTest(unittest.makeSuite(TestSerializationProtection))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
            
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
            
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_basic_tests()
    sys.exit(0 if success else 1)
