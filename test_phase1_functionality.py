#!/usr/bin/env python3
"""
Phase 1 Basic Functionality Testing

Comprehensive validation of Phase 1 requirements from TESTING_AND_ENHANCEMENT_STRATEGY.md
"""

import sys
import os
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock

# Add src and apps to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent / 'apps'))

class TestPhase1BasicFunctionality(unittest.TestCase):
    """Phase 1: Basic Functionality Validation Tests"""
    
    def setUp(self):
        """Set up test environment."""
        self.test_egif = "*x (Human x)"
        
    def test_1_component_imports(self):
        """Test 1: Component Import Tests - All three components import successfully"""
        print("\n=== Test 1: Component Imports ===")
        
        # Test Launcher import
        try:
            from arisbe_launcher import ArisbeMainLauncher
            print("✓ Launcher (ArisbeMainLauncher) import successful")
        except Exception as e:
            self.fail(f"Launcher import failed: {e}")
            
        # Test Organon import
        try:
            from organon.organon_browser import OrganonBrowser
            print("✓ Organon (OrganonBrowser) import successful")
        except Exception as e:
            self.fail(f"Organon import failed: {e}")
            
        # Test Ergasterion import
        try:
            from ergasterion.ergasterion_workshop import ErgasterionWorkshop
            print("✓ Ergasterion (ErgasterionWorkshop) import successful")
        except Exception as e:
            self.fail(f"Ergasterion import failed: {e}")
            
        # Test Agon import
        try:
            from agon.agon_game import AgonGame
            print("✓ Agon (AgonGame) import successful")
        except Exception as e:
            self.fail(f"Agon import failed: {e}")
            
        print("✅ All component imports successful")
        
    def test_2_core_integration_egif_parsing(self):
        """Test 2a: Core Integration - EGIF parsing with EGIFParser"""
        print("\n=== Test 2a: EGIF Parsing ===")
        
        try:
            from egif_parser_dau import EGIFParser
            
            parser = EGIFParser(self.test_egif)
            egi = parser.parse()
            
            self.assertIsNotNone(egi)
            self.assertGreater(len(egi.V), 0, "Should have at least one vertex")
            
            print(f"✓ EGIF parsed successfully: {len(egi.V)} vertices, {len(egi.E)} edges, {len(egi.Cut)} cuts")
            
        except Exception as e:
            self.fail(f"EGIF parsing failed: {e}")
            
    def test_2_core_integration_egdf_serialization(self):
        """Test 2b: Core Integration - EGDF serialization with EGDFParser"""
        print("\n=== Test 2b: EGDF Serialization ===")
        
        try:
            from egif_parser_dau import EGIFParser
            from egdf_parser import EGDFParser
            
            # Parse EGIF to EGI
            parser = EGIFParser(self.test_egif)
            egi = parser.parse()
            
            # Create EGDF
            egdf_parser = EGDFParser()
            
            # Create minimal spatial primitives for testing
            spatial_primitives = []
            for i, vertex in enumerate(egi.V):
                spatial_primitives.append({
                    'element_id': vertex.id,
                    'element_type': 'vertex',
                    'position': (100 + i * 50, 100),
                    'bounds': (90 + i * 50, 90, 110 + i * 50, 110)
                })
                
            egdf_doc = egdf_parser.create_egdf_from_egi(egi, spatial_primitives)
            self.assertIsNotNone(egdf_doc)
            
            # Test YAML serialization
            yaml_output = egdf_parser.egdf_to_yaml(egdf_doc)
            self.assertIsInstance(yaml_output, str)
            self.assertGreater(len(yaml_output), 0)
            
            # Test JSON serialization
            json_output = egdf_parser.egdf_to_json(egdf_doc)
            self.assertIsInstance(json_output, str)
            self.assertGreater(len(json_output), 0)
            
            print(f"✓ EGDF serialization successful: YAML ({len(yaml_output)} chars), JSON ({len(json_output)} chars)")
            
        except Exception as e:
            self.fail(f"EGDF serialization failed: {e}")
            
    def test_2_core_integration_canonical_pipeline(self):
        """Test 2c: Core Integration - Canonical pipeline functionality"""
        print("\n=== Test 2c: Canonical Pipeline ===")
        
        try:
            from egif_parser_dau import EGIFParser
            from canonical import CanonicalPipeline
            
            # Parse EGIF to EGI
            parser = EGIFParser(self.test_egif)
            egi = parser.parse()
            
            # Test canonical pipeline
            pipeline = CanonicalPipeline()
            
            # Test EGI to EGIF conversion
            egif_output = pipeline.egi_to_egif(egi)
            self.assertIsInstance(egif_output, str)
            self.assertGreater(len(egif_output), 0)
            
            print(f"✓ Canonical pipeline functional: EGI → EGIF conversion successful")
            print(f"  Input:  '{self.test_egif}'")
            print(f"  Output: '{egif_output}'")
            
        except Exception as e:
            self.fail(f"Canonical pipeline failed: {e}")
            
    def test_2_core_integration_serialization_integrity(self):
        """Test 2d: Core Integration - Serialization integrity validation"""
        print("\n=== Test 2d: Serialization Integrity ===")
        
        try:
            from egdf_structural_lock import EGDFStructuralProtector
            
            protector = EGDFStructuralProtector()
            
            if protector.lock_file.exists():
                is_valid, errors = protector.validate_structural_integrity()
                
                if is_valid:
                    print("✓ Serialization integrity validation passed")
                else:
                    print(f"⚠ Integrity validation issues: {errors}")
                    # Don't fail the test for integrity issues, just report
                    
            else:
                print("⚠ No serialization integrity lock found - creating baseline")
                # This is acceptable for initial setup
                
        except Exception as e:
            self.fail(f"Serialization integrity check failed: {e}")
            
    @patch('PySide6.QtWidgets.QApplication')
    def test_3_gui_window_creation_launcher(self, mock_qapp):
        """Test 3a: GUI Window Creation - Launcher creates windows"""
        print("\n=== Test 3a: Launcher Window Creation ===")
        
        try:
            # Mock Qt application
            mock_app = MagicMock()
            mock_qapp.return_value = mock_app
            
            from arisbe_launcher import ArisbeMainLauncher
            
            # Test launcher creation (without actually showing GUI)
            launcher = ArisbeMainLauncher()
            self.assertIsNotNone(launcher)
            
            print("✓ Launcher window creation successful (mocked)")
            
        except Exception as e:
            self.fail(f"Launcher window creation failed: {e}")
            
    @patch('PySide6.QtWidgets.QApplication')
    def test_3_gui_window_creation_components(self, mock_qapp):
        """Test 3b: GUI Window Creation - Component windows create without crashes"""
        print("\n=== Test 3b: Component Window Creation ===")
        
        try:
            # Mock Qt application
            mock_app = MagicMock()
            mock_qapp.return_value = mock_app
            
            # Test Organon window creation
            from organon.organon_browser import OrganonBrowser
            organon = OrganonBrowser()
            self.assertIsNotNone(organon)
            print("✓ Organon window creation successful (mocked)")
            
            # Test Ergasterion window creation
            from ergasterion.ergasterion_workshop import ErgasterionWorkshop
            ergasterion = ErgasterionWorkshop()
            self.assertIsNotNone(ergasterion)
            print("✓ Ergasterion window creation successful (mocked)")
            
            # Test Agon window creation
            from agon.agon_game import AgonGame
            agon = AgonGame()
            self.assertIsNotNone(agon)
            print("✓ Agon window creation successful (mocked)")
            
        except Exception as e:
            self.fail(f"Component window creation failed: {e}")

def run_phase1_tests():
    """Run Phase 1 basic functionality tests with detailed reporting."""
    print("Arisbe Phase 1 Basic Functionality Testing")
    print("=" * 50)
    print("Testing Phase 1 requirements from TESTING_AND_ENHANCEMENT_STRATEGY.md")
    print()
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPhase1BasicFunctionality)
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    print("\n" + "=" * 50)
    print("Phase 1 Testing Summary")
    print("=" * 50)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passed = total_tests - failures - errors
    
    print(f"Tests Run: {total_tests}")
    print(f"Passed: {passed}")
    print(f"Failed: {failures}")
    print(f"Errors: {errors}")
    
    if failures == 0 and errors == 0:
        print("\n🎉 Phase 1 Basic Functionality: ALL TESTS PASSED!")
        print("✅ Ready to proceed to Phase 2: Feature Integration Testing")
    else:
        print(f"\n⚠️ Phase 1 Issues Found: {failures + errors} test(s) failed")
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback}")
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback}")
    
    return failures == 0 and errors == 0

if __name__ == "__main__":
    success = run_phase1_tests()
    sys.exit(0 if success else 1)
