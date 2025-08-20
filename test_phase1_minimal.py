#!/usr/bin/env python3
"""
Phase 1 Minimal Testing - Direct functionality validation without Qt mocking
"""

import sys
from pathlib import Path

# Add src and apps to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent / 'apps'))

def test_component_imports():
    """Test 1: Component Import Tests"""
    print("=== Test 1: Component Imports ===")
    
    results = []
    
    # Test core imports first
    try:
        from egif_parser_dau import EGIFParser
        print("✓ EGIFParser import successful")
        results.append(True)
    except Exception as e:
        print(f"✗ EGIFParser import failed: {e}")
        results.append(False)
        
    try:
        from canonical import CanonicalPipeline
        print("✓ CanonicalPipeline import successful")
        results.append(True)
    except Exception as e:
        print(f"✗ CanonicalPipeline import failed: {e}")
        results.append(False)
        
    try:
        from egdf_parser import EGDFParser
        print("✓ EGDFParser import successful")
        results.append(True)
    except Exception as e:
        print(f"✗ EGDFParser import failed: {e}")
        results.append(False)
    
    # Test GUI component imports
    try:
        from organon.organon_browser import OrganonBrowser
        print("✓ OrganonBrowser import successful")
        results.append(True)
    except Exception as e:
        print(f"✗ OrganonBrowser import failed: {e}")
        results.append(False)
        
    try:
        from ergasterion.ergasterion_workshop import ErgasterionWorkshop
        print("✓ ErgasterionWorkshop import successful")
        results.append(True)
    except Exception as e:
        print(f"✗ ErgasterionWorkshop import failed: {e}")
        results.append(False)
        
    try:
        from agon.agon_game import AgonGame
        print("✓ AgonGame import successful")
        results.append(True)
    except Exception as e:
        print(f"✗ AgonGame import failed: {e}")
        results.append(False)
        
    try:
        from arisbe_launcher import ArisbeMainLauncher
        print("✓ ArisbeMainLauncher import successful")
        results.append(True)
    except Exception as e:
        print(f"✗ ArisbeMainLauncher import failed: {e}")
        results.append(False)
    
    return all(results)

def test_egif_parsing():
    """Test 2a: EGIF Parsing"""
    print("\n=== Test 2a: EGIF Parsing ===")
    
    try:
        from egif_parser_dau import EGIFParser
        
        test_egif = "*x (Human x)"
        parser = EGIFParser(test_egif)
        egi = parser.parse()
        
        if egi is None:
            print("✗ EGIF parsing returned None")
            return False
            
        print(f"✓ EGIF parsed: {len(egi.V)} vertices, {len(egi.E)} edges, {len(egi.Cut)} cuts")
        
        if len(egi.V) == 0:
            print("⚠ Warning: No vertices found in parsed EGI")
            
        return True
        
    except Exception as e:
        print(f"✗ EGIF parsing failed: {e}")
        return False

def test_canonical_pipeline():
    """Test 2b: Canonical Pipeline"""
    print("\n=== Test 2b: Canonical Pipeline ===")
    
    try:
        from egif_parser_dau import EGIFParser
        from canonical import CanonicalPipeline
        
        # Parse test EGIF
        test_egif = "*x (Human x)"
        parser = EGIFParser(test_egif)
        egi = parser.parse()
        
        # Test pipeline
        pipeline = CanonicalPipeline()
        egif_output = pipeline.egi_to_egif(egi)
        
        if not isinstance(egif_output, str):
            print(f"✗ Pipeline output not string: {type(egif_output)}")
            return False
            
        print(f"✓ Pipeline conversion successful")
        print(f"  Input:  '{test_egif}'")
        print(f"  Output: '{egif_output}'")
        
        return True
        
    except Exception as e:
        print(f"✗ Canonical pipeline failed: {e}")
        return False

def test_egdf_serialization():
    """Test 2c: EGDF Serialization"""
    print("\n=== Test 2c: EGDF Serialization ===")
    
    try:
        from egif_parser_dau import EGIFParser
        from egdf_parser import EGDFParser
        
        # Parse test EGIF
        test_egif = "*x (Human x)"
        parser = EGIFParser(test_egif)
        egi = parser.parse()
        
        # Create EGDF
        egdf_parser = EGDFParser()
        
        # Create minimal spatial primitives
        spatial_primitives = []
        for i, vertex in enumerate(egi.V):
            spatial_primitives.append({
                'element_id': vertex.id,
                'element_type': 'vertex',
                'position': (100 + i * 50, 100),
                'bounds': (90 + i * 50, 90, 110 + i * 50, 110)
            })
            
        egdf_doc = egdf_parser.create_egdf_from_egi(egi, spatial_primitives)
        
        if egdf_doc is None:
            print("✗ EGDF creation returned None")
            return False
            
        # Test serialization
        yaml_output = egdf_parser.egdf_to_yaml(egdf_doc)
        json_output = egdf_parser.egdf_to_json(egdf_doc)
        
        print(f"✓ EGDF serialization successful")
        print(f"  YAML: {len(yaml_output)} characters")
        print(f"  JSON: {len(json_output)} characters")
        
        return True
        
    except Exception as e:
        print(f"✗ EGDF serialization failed: {e}")
        return False

def test_serialization_integrity():
    """Test 2d: Serialization Integrity"""
    print("\n=== Test 2d: Serialization Integrity ===")
    
    try:
        from egdf_structural_lock import EGDFStructuralProtector
        
        protector = EGDFStructuralProtector()
        
        if protector.lock_file.exists():
            is_valid, errors = protector.validate_structural_integrity()
            
            if is_valid:
                print("✓ Serialization integrity validation passed")
                return True
            else:
                print(f"⚠ Integrity validation issues found: {len(errors)} errors")
                for error in errors[:3]:  # Show first 3 errors
                    print(f"  - {error}")
                return False
        else:
            print("⚠ No serialization integrity lock found")
            print("  This is acceptable for initial setup")
            return True
            
    except Exception as e:
        print(f"✗ Serialization integrity check failed: {e}")
        return False

def main():
    """Run Phase 1 minimal testing."""
    print("Arisbe Phase 1 Basic Functionality Testing")
    print("=" * 50)
    
    tests = [
        ("Component Imports", test_component_imports),
        ("EGIF Parsing", test_egif_parsing),
        ("Canonical Pipeline", test_canonical_pipeline),
        ("EGDF Serialization", test_egdf_serialization),
        ("Serialization Integrity", test_serialization_integrity)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("Phase 1 Testing Results")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nSummary: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 Phase 1 Basic Functionality: ALL TESTS PASSED!")
        print("✅ Ready to proceed to Phase 2: Feature Integration Testing")
        return True
    else:
        print(f"\n⚠️ Phase 1 Issues: {total - passed} test(s) failed")
        print("Need to resolve issues before proceeding to Phase 2")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
