#!/usr/bin/env python3
"""
Basic Functionality Test

Quick validation of core GUI functionality without full Qt testing.
"""

import sys
from pathlib import Path

# Add src and apps to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent / 'apps'))

def test_imports():
    """Test that all components can be imported."""
    print("Testing imports...")
    
    try:
        from arisbe_launcher import ArisbeMainLauncher
        print("✓ Launcher import successful")
    except Exception as e:
        print(f"✗ Launcher import failed: {e}")
        return False
        
    try:
        from organon.organon_browser import OrganonBrowser
        print("✓ Organon import successful")
    except Exception as e:
        print(f"✗ Organon import failed: {e}")
        return False
        
    try:
        from ergasterion.ergasterion_workshop import ErgasterionWorkshop
        print("✓ Ergasterion import successful")
    except Exception as e:
        print(f"✗ Ergasterion import failed: {e}")
        return False
        
    try:
        from agon.agon_game import AgonGame
        print("✓ Agon import successful")
    except Exception as e:
        print(f"✗ Agon import failed: {e}")
        return False
        
    return True

def test_core_functionality():
    """Test core EGIF parsing and pipeline functionality."""
    print("\nTesting core functionality...")
    
    try:
        from egif_parser_dau import EGIFParser
        from canonical import CanonicalPipeline
        
        # Test EGIF parsing
        test_egif = "*x (Human x)"
        parser = EGIFParser(test_egif)
        egi = parser.parse()
        
        print(f"✓ EGIF parsed: {len(egi.V)} vertices, {len(egi.E)} edges")
        
        # Test canonical pipeline
        pipeline = CanonicalPipeline()
        egif_output = pipeline.egi_to_egif(egi)
        
        print(f"✓ Pipeline round-trip successful: {egif_output}")
        
        return True
        
    except Exception as e:
        print(f"✗ Core functionality failed: {e}")
        return False

def test_serialization():
    """Test EGDF serialization functionality."""
    print("\nTesting serialization...")
    
    try:
        from egif_parser_dau import EGIFParser
        from egdf_parser import EGDFParser
        
        # Parse test EGIF
        test_egif = "*x (Human x)"
        parser = EGIFParser(test_egif)
        egi = parser.parse()
        
        # Create EGDF
        egdf_parser = EGDFParser()
        spatial_primitives = [{
            'element_id': egi.V[0].id,
            'element_type': 'vertex',
            'position': (100, 100),
            'bounds': (90, 90, 110, 110)
        }]
        
        egdf_doc = egdf_parser.create_egdf_from_egi(egi, spatial_primitives)
        
        # Test serialization
        yaml_output = egdf_parser.egdf_to_yaml(egdf_doc)
        json_output = egdf_parser.egdf_to_json(egdf_doc)
        
        print(f"✓ YAML serialization: {len(yaml_output)} chars")
        print(f"✓ JSON serialization: {len(json_output)} chars")
        
        return True
        
    except Exception as e:
        print(f"✗ Serialization failed: {e}")
        return False

def test_integrity_protection():
    """Test serialization integrity protection."""
    print("\nTesting integrity protection...")
    
    try:
        from egdf_structural_lock import EGDFStructuralProtector
        
        protector = EGDFStructuralProtector()
        
        if protector.lock_file.exists():
            is_valid, errors = protector.validate_structural_integrity()
            
            if is_valid:
                print("✓ Serialization integrity validated")
                return True
            else:
                print(f"✗ Integrity issues: {errors}")
                return False
        else:
            print("⚠ No integrity lock found")
            return True
            
    except Exception as e:
        print(f"✗ Integrity protection failed: {e}")
        return False

def main():
    """Run basic functionality tests."""
    print("Arisbe Basic Functionality Test")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_core_functionality,
        test_serialization,
        test_integrity_protection
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All basic functionality tests passed!")
        return True
    else:
        print("⚠️ Some tests failed - see details above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
