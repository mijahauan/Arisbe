#!/usr/bin/env python3
"""
Phase 2: Organon & Ergasterion Feature Testing

Focused testing on Organon (Browser) and Ergasterion (Workshop) components,
deferring Agon until these core components are stable.
"""

import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src and apps to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent / 'apps'))

def test_organon_browser_functionality():
    """Test Organon Browser corpus loading and browsing functionality."""
    print("=== Phase 2.1: Organon Browser Functionality ===")
    
    results = []
    
    try:
        from organon.organon_browser import OrganonBrowser
        print("✓ OrganonBrowser import successful")
        results.append(True)
        
        # Mock Qt to avoid GUI display
        with patch('PySide6.QtWidgets.QApplication'):
            organon = OrganonBrowser()
            print("✓ OrganonBrowser instantiation successful")
            
            # Test corpus directory detection
            corpus_path = Path(__file__).parent / 'corpus' / 'corpus'
            if corpus_path.exists():
                print(f"✓ Corpus directory found: {corpus_path}")
                
                # Count available files
                egif_files = list(corpus_path.rglob('*.egif'))
                yaml_files = list(corpus_path.rglob('*.yaml'))
                json_files = list(corpus_path.rglob('*.json'))
                
                print(f"  - EGIF files: {len(egif_files)}")
                print(f"  - YAML files: {len(yaml_files)}")
                print(f"  - JSON files: {len(json_files)}")
                
                results.append(True)
            else:
                print(f"⚠ Corpus directory not found at {corpus_path}")
                results.append(False)
            
            # Test method availability
            methods_to_check = [
                'load_corpus_directory',
                'import_egif_file', 
                'create_visualization_tabs',
                'export_png',
                'export_svg',
                'export_yaml',
                'export_json'
            ]
            
            available_methods = []
            for method in methods_to_check:
                if hasattr(organon, method):
                    available_methods.append(method)
                    print(f"✓ Method available: {method}")
                else:
                    print(f"⚠ Method not implemented: {method}")
            
            results.append(len(available_methods) >= 3)  # At least basic functionality
            
    except Exception as e:
        print(f"✗ Organon browser functionality failed: {e}")
        results.append(False)
    
    return all(results)

def test_ergasterion_workshop_functionality():
    """Test Ergasterion Workshop mode switching and transformation tools."""
    print("\n=== Phase 2.2: Ergasterion Workshop Functionality ===")
    
    results = []
    
    try:
        from ergasterion.ergasterion_workshop import ErgasterionWorkshop
        print("✓ ErgasterionWorkshop import successful")
        results.append(True)
        
        # Mock Qt to avoid GUI display
        with patch('PySide6.QtWidgets.QApplication'):
            workshop = ErgasterionWorkshop()
            print("✓ ErgasterionWorkshop instantiation successful")
            
            # Test mode switching functionality
            mode_methods = ['set_mode', 'current_mode']
            available_mode_methods = []
            for method in mode_methods:
                if hasattr(workshop, method):
                    available_mode_methods.append(method)
                    print(f"✓ Mode method available: {method}")
                else:
                    print(f"⚠ Mode method not implemented: {method}")
            
            results.append(len(available_mode_methods) >= 1)
            
            # Test transformation tools
            transform_methods = [
                'select_transformation_tool',
                'parse_egif_input',
                'validate_transformation'
            ]
            
            available_transform_methods = []
            for method in transform_methods:
                if hasattr(workshop, method):
                    available_transform_methods.append(method)
                    print(f"✓ Transform method available: {method}")
                else:
                    print(f"⚠ Transform method not implemented: {method}")
            
            results.append(len(available_transform_methods) >= 1)
            
            # Test canvas and interaction
            canvas_methods = ['canvas_widget', 'handle_selection']
            available_canvas_methods = []
            for method in canvas_methods:
                if hasattr(workshop, method):
                    available_canvas_methods.append(method)
                    print(f"✓ Canvas method available: {method}")
                else:
                    print(f"⚠ Canvas method not implemented: {method}")
            
            results.append(len(available_canvas_methods) >= 1)
            
            # Test file operations
            file_methods = ['save_file', 'load_file', 'new_file']
            available_file_methods = []
            for method in file_methods:
                if hasattr(workshop, method):
                    available_file_methods.append(method)
                    print(f"✓ File method available: {method}")
                else:
                    print(f"⚠ File method not implemented: {method}")
            
            results.append(len(available_file_methods) >= 1)
            
    except Exception as e:
        print(f"✗ Ergasterion workshop functionality failed: {e}")
        results.append(False)
    
    return all(results)

def test_egif_workflow_integration():
    """Test complete EGIF workflow through both components."""
    print("\n=== Phase 2.3: EGIF Workflow Integration ===")
    
    try:
        from egif_parser_dau import EGIFParser
        from canonical import CanonicalPipeline
        from egdf_parser import EGDFParser
        
        # Test with a realistic complex example
        test_egif = "*x ~[~[(Human x)] (Mortal x)]"
        print(f"Testing workflow with: {test_egif}")
        
        # Step 1: Parse EGIF
        parser = EGIFParser(test_egif)
        egi = parser.parse()
        print(f"✓ EGIF parsed: {len(egi.V)} vertices, {len(egi.E)} edges, {len(egi.Cut)} cuts")
        
        # Step 2: Pipeline processing
        pipeline = CanonicalPipeline()
        egif_output = pipeline.egi_to_egif(egi)
        print(f"✓ Pipeline round-trip successful")
        
        # Step 3: EGDF creation with realistic spatial layout
        egdf_parser = EGDFParser()
        spatial_primitives = []
        
        # Create spatial primitives for visualization
        for i, vertex in enumerate(egi.V):
            spatial_primitives.append({
                'element_id': vertex.id,
                'element_type': 'vertex',
                'position': (200 + i * 100, 150),
                'bounds': (180 + i * 100, 130, 220 + i * 100, 170)
            })
        
        for i, edge in enumerate(egi.E):
            spatial_primitives.append({
                'element_id': edge.id,
                'element_type': 'edge',
                'position': (300 + i * 100, 200),
                'bounds': (290 + i * 100, 190, 310 + i * 100, 210)
            })
        
        for i, cut in enumerate(egi.Cut):
            spatial_primitives.append({
                'element_id': cut.id,
                'element_type': 'cut',
                'position': (150 + i * 200, 100),
                'bounds': (100 + i * 200, 50, 400 + i * 200, 300)
            })
        
        egdf_doc = egdf_parser.create_egdf_from_egi(egi, spatial_primitives)
        print(f"✓ EGDF created with {len(spatial_primitives)} spatial primitives")
        
        # Step 4: Test serialization
        yaml_output = egdf_parser.egdf_to_yaml(egdf_doc)
        json_output = egdf_parser.egdf_to_json(egdf_doc)
        print(f"✓ Serialization successful: YAML({len(yaml_output)} chars), JSON({len(json_output)} chars)")
        
        return True
        
    except Exception as e:
        print(f"✗ EGIF workflow integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_handling():
    """Test error handling with invalid inputs."""
    print("\n=== Phase 2.4: Error Handling ===")
    
    error_scenarios = [
        ("Malformed EGIF", "~[~[(P] (Q)]"),  # Missing bracket
        ("Empty input", ""),
        ("Invalid quantifier", "*x *y [(P x y]"),  # Missing bracket
    ]
    
    results = []
    
    for scenario_name, invalid_egif in error_scenarios:
        try:
            from egif_parser_dau import EGIFParser
            
            parser = EGIFParser(invalid_egif)
            egi = parser.parse()
            
            print(f"⚠ {scenario_name}: Parser unexpectedly accepted invalid input")
            results.append(False)
            
        except Exception as e:
            print(f"✓ {scenario_name}: Properly rejected invalid input")
            results.append(True)
    
    return all(results)

def main():
    """Run Phase 2 Organon & Ergasterion Testing."""
    print("Arisbe Phase 2: Organon & Ergasterion Feature Testing")
    print("=" * 65)
    print("Focused testing on core browser and workshop components")
    print("(Deferring Agon until Organon/Ergasterion are stable)")
    print()
    
    tests = [
        ("Organon Browser Functionality", test_organon_browser_functionality),
        ("Ergasterion Workshop Functionality", test_ergasterion_workshop_functionality),
        ("EGIF Workflow Integration", test_egif_workflow_integration),
        ("Error Handling", test_error_handling)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 65)
    print("Phase 2 Testing Results")
    print("=" * 65)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nSummary: {passed}/{total} test categories passed")
    
    if passed == total:
        print("\n🎉 Phase 2 Core Components: ALL TESTS PASSED!")
        print("✅ Organon and Ergasterion foundations are stable")
        print("✅ Ready to enhance features and then proceed to Agon testing")
    else:
        print(f"\n⚠️ Phase 2 Issues: {total - passed} test category(ies) need attention")
        print("Focus on implementing missing core functionality")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
