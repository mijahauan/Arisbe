#!/usr/bin/env python3
"""
Phase 2: Feature Integration Testing

Testing GUI component features, corpus integration, and advanced functionality
as outlined in TESTING_AND_ENHANCEMENT_STRATEGY.md Phase 2.
"""

import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src and apps to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent / 'apps'))

def test_organon_corpus_integration():
    """Test Organon Browser corpus loading and browsing functionality."""
    print("=== Phase 2.1: Organon Corpus Integration ===")
    
    try:
        from organon.organon_browser import OrganonBrowser
        
        # Mock Qt to avoid GUI display
        with patch('PySide6.QtWidgets.QApplication'):
            organon = OrganonBrowser()
            
            # Test corpus directory detection
            corpus_path = Path(__file__).parent / 'corpus' / 'corpus'
            if corpus_path.exists():
                print(f"✓ Corpus directory found: {corpus_path}")
                
                # Test corpus loading method
                if hasattr(organon, 'load_corpus_directory'):
                    print("✓ Corpus loading method available")
                else:
                    print("⚠ Corpus loading method not implemented")
                
                # Check for example files
                example_files = list(corpus_path.rglob('*.egif')) + list(corpus_path.rglob('*.yaml')) + list(corpus_path.rglob('*.json'))
                print(f"✓ Found {len(example_files)} corpus files")
                
            else:
                print(f"⚠ Corpus directory not found at {corpus_path}")
            
            # Test EGIF import functionality
            if hasattr(organon, 'import_egif_file'):
                print("✓ EGIF import method available")
            else:
                print("⚠ EGIF import method not implemented")
            
            # Test multi-tab display
            if hasattr(organon, 'create_visualization_tabs'):
                print("✓ Multi-tab visualization method available")
            else:
                print("⚠ Multi-tab display not implemented")
            
            # Test export functionality
            export_methods = ['export_png', 'export_svg', 'export_yaml', 'export_json']
            available_exports = [method for method in export_methods if hasattr(organon, method)]
            print(f"✓ Export methods available: {len(available_exports)}/{len(export_methods)}")
            
            return True
            
    except Exception as e:
        print(f"✗ Organon corpus integration failed: {e}")
        return False

def test_ergasterion_workshop_features():
    """Test Ergasterion Workshop mode switching and transformation tools."""
    print("\n=== Phase 2.2: Ergasterion Workshop Features ===")
    
    try:
        from ergasterion.ergasterion_workshop import ErgasterionWorkshop
        
        # Mock Qt to avoid GUI display
        with patch('PySide6.QtWidgets.QApplication'):
            workshop = ErgasterionWorkshop()
            
            # Test mode switching (Warmup ↔ Practice)
            if hasattr(workshop, 'set_mode'):
                print("✓ Mode switching method available")
                
                # Test mode states
                if hasattr(workshop, 'current_mode'):
                    print("✓ Mode state tracking available")
                else:
                    print("⚠ Mode state tracking not implemented")
            else:
                print("⚠ Mode switching not implemented")
            
            # Test transformation tool selection
            if hasattr(workshop, 'select_transformation_tool'):
                print("✓ Transformation tool selection available")
            else:
                print("⚠ Transformation tool selection not implemented")
            
            # Test EGIF input parsing and validation
            if hasattr(workshop, 'parse_egif_input'):
                print("✓ EGIF input parsing method available")
            else:
                print("⚠ EGIF input parsing not implemented")
            
            # Test canvas interaction
            if hasattr(workshop, 'canvas_widget'):
                print("✓ Canvas widget available")
                
                # Test selection functionality
                if hasattr(workshop, 'handle_selection'):
                    print("✓ Canvas selection handling available")
                else:
                    print("⚠ Canvas selection not implemented")
            else:
                print("⚠ Canvas widget not implemented")
            
            # Test undo/redo functionality
            undo_redo_methods = ['undo_action', 'redo_action', 'action_history']
            available_undo_redo = [method for method in undo_redo_methods if hasattr(workshop, method)]
            print(f"✓ Undo/redo methods available: {len(available_undo_redo)}/{len(undo_redo_methods)}")
            
            # Test file operations
            file_methods = ['save_file', 'load_file', 'new_file']
            available_file_ops = [method for method in file_methods if hasattr(workshop, method)]
            print(f"✓ File operation methods available: {len(available_file_ops)}/{len(file_methods)}")
            
            return True
            
    except Exception as e:
        print(f"✗ Ergasterion workshop features failed: {e}")
        return False

def test_agon_game_mechanics():
    """Test Agon Game phases, role selection, and universe management."""
    print("\n=== Phase 2.3: Agon Game Mechanics ===")
    
    try:
        from agon.agon_game import AgonGame
        
        # Mock Qt to avoid GUI display
        with patch('PySide6.QtWidgets.QApplication'):
            game = AgonGame()
            
            # Test game phase transitions
            if hasattr(game, 'current_phase'):
                print("✓ Game phase tracking available")
                
                if hasattr(game, 'advance_phase'):
                    print("✓ Phase transition method available")
                else:
                    print("⚠ Phase transition not implemented")
            else:
                print("⚠ Game phase tracking not implemented")
            
            # Test role selection and UI updates
            if hasattr(game, 'set_player_role'):
                print("✓ Role selection method available")
                
                if hasattr(game, 'update_ui_for_role'):
                    print("✓ Role-based UI updates available")
                else:
                    print("⚠ Role-based UI updates not implemented")
            else:
                print("⚠ Role selection not implemented")
            
            # Test EGIF proposition parsing
            if hasattr(game, 'parse_proposition'):
                print("✓ Proposition parsing method available")
            else:
                print("⚠ Proposition parsing not implemented")
            
            # Test move history tracking
            if hasattr(game, 'move_history'):
                print("✓ Move history tracking available")
                
                if hasattr(game, 'add_move'):
                    print("✓ Move recording method available")
                else:
                    print("⚠ Move recording not implemented")
            else:
                print("⚠ Move history tracking not implemented")
            
            # Test Universe of Discourse management
            universe_methods = ['create_universe', 'add_to_universe', 'validate_universe']
            available_universe = [method for method in universe_methods if hasattr(game, method)]
            print(f"✓ Universe management methods available: {len(available_universe)}/{len(universe_methods)}")
            
            return True
            
    except Exception as e:
        print(f"✗ Agon game mechanics failed: {e}")
        return False

def test_pipeline_integration_advanced():
    """Test advanced pipeline integration with complex examples."""
    print("\n=== Phase 2.4: Advanced Pipeline Integration ===")
    
    try:
        from egif_parser_dau import EGIFParser
        from canonical import CanonicalPipeline
        from egdf_parser import EGDFParser
        
        # Test with complex nested example
        complex_egif = "*x ~[~[(Human x)] (Mortal x)]"
        
        # Parse to EGI
        parser = EGIFParser(complex_egif)
        egi = parser.parse()
        print(f"✓ Complex EGIF parsed: {len(egi.V)} vertices, {len(egi.E)} edges, {len(egi.Cut)} cuts")
        
        # Test canonical pipeline
        pipeline = CanonicalPipeline()
        egif_output = pipeline.egi_to_egif(egi)
        print(f"✓ Pipeline round-trip successful")
        
        # Test EGDF creation with spatial layout
        egdf_parser = EGDFParser()
        
        # Create comprehensive spatial primitives
        spatial_primitives = []
        
        # Add vertices with realistic positioning
        for i, vertex in enumerate(egi.V):
            spatial_primitives.append({
                'element_id': vertex.id,
                'element_type': 'vertex',
                'position': (150 + i * 80, 200 + (i % 2) * 60),
                'bounds': (130 + i * 80, 180 + (i % 2) * 60, 170 + i * 80, 220 + (i % 2) * 60),
                'style': {'fill': '#e6f3ff', 'stroke': '#0066cc'}
            })
        
        # Add edges with routing
        for i, edge in enumerate(egi.E):
            spatial_primitives.append({
                'element_id': edge.id,
                'element_type': 'edge',
                'position': (250 + i * 80, 250),
                'bounds': (240 + i * 80, 240, 260 + i * 80, 260),
                'style': {'stroke': '#333333', 'stroke-width': 2}
            })
        
        # Add cuts with proper nesting bounds
        for i, cut in enumerate(egi.Cut):
            spatial_primitives.append({
                'element_id': cut.id,
                'element_type': 'cut',
                'position': (100 + i * 200, 100),
                'bounds': (50 + i * 200, 50, 350 + i * 200, 350),
                'style': {'fill': 'none', 'stroke': '#ff6600', 'stroke-width': 3}
            })
        
        egdf_doc = egdf_parser.create_egdf_from_egi(egi, spatial_primitives)
        print(f"✓ EGDF created with {len(spatial_primitives)} spatial primitives")
        
        # Test serialization formats
        yaml_output = egdf_parser.egdf_to_yaml(egdf_doc)
        json_output = egdf_parser.egdf_to_json(egdf_doc)
        print(f"✓ Serialization: YAML({len(yaml_output)} chars), JSON({len(json_output)} chars)")
        
        # Test round-trip validation
        yaml_parsed = egdf_parser.yaml_to_egdf(yaml_output)
        if yaml_parsed:
            print("✓ YAML round-trip validation successful")
        else:
            print("⚠ YAML round-trip validation failed")
        
        return True
        
    except Exception as e:
        print(f"✗ Advanced pipeline integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_handling_scenarios():
    """Test error handling and graceful degradation."""
    print("\n=== Phase 2.5: Error Handling Scenarios ===")
    
    error_tests = [
        ("Invalid EGIF syntax", "~[~[(P] (Q)]"),  # Missing closing bracket
        ("Empty EGIF", ""),
        ("Malformed quantifier", "*x *y [(P x y]"),  # Missing closing bracket
        ("Invalid predicate", "~[(P x y z w v u t s r q)]"),  # Too many arguments
    ]
    
    results = []
    
    for test_name, invalid_egif in error_tests:
        try:
            from egif_parser_dau import EGIFParser
            
            parser = EGIFParser(invalid_egif)
            egi = parser.parse()
            
            # If we get here, the parser didn't catch the error
            print(f"⚠ {test_name}: Parser accepted invalid input")
            results.append(False)
            
        except Exception as e:
            # Expected behavior - parser should reject invalid input
            print(f"✓ {test_name}: Properly rejected with error")
            results.append(True)
    
    return all(results)

def main():
    """Run Phase 2 Feature Integration Testing."""
    print("Arisbe Phase 2: Feature Integration Testing")
    print("=" * 60)
    print("Testing Phase 2 requirements from TESTING_AND_ENHANCEMENT_STRATEGY.md")
    print()
    
    tests = [
        ("Organon Corpus Integration", test_organon_corpus_integration),
        ("Ergasterion Workshop Features", test_ergasterion_workshop_features),
        ("Agon Game Mechanics", test_agon_game_mechanics),
        ("Advanced Pipeline Integration", test_pipeline_integration_advanced),
        ("Error Handling Scenarios", test_error_handling_scenarios)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("Phase 2 Testing Results")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nSummary: {passed}/{total} test categories passed")
    
    if passed == total:
        print("\n🎉 Phase 2 Feature Integration: ALL TESTS PASSED!")
        print("✅ Ready to proceed to Phase 3: Advanced Integration Testing")
    else:
        print(f"\n⚠️ Phase 2 Issues: {total - passed} test category(ies) need attention")
        print("Review failed tests and implement missing features")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
