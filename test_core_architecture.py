#!/usr/bin/env python3
"""
Test core architecture without GUI dependencies.
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_style_system():
    """Test the style system."""
    print("Testing style system...")
    
    try:
        from gui.simple_style_system import (
            CutStyle, LigatureStyle, VertexStyle, SimpleStyle,
            DAU_STYLE, PEIRCE_STYLE, LATEX_STYLE, HANDWRITTEN_STYLE
        )
        
        # Test basic style creation
        cut_style = CutStyle()
        print(f"✓ CutStyle created: line_width={cut_style.line_width}, color={cut_style.color}")
        
        ligature_style = LigatureStyle()
        print(f"✓ LigatureStyle created: connection_type={ligature_style.connection_type}")
        
        vertex_style = VertexStyle()
        print(f"✓ VertexStyle created: radius={vertex_style.radius}, shape={vertex_style.shape_type}")
        
        # Test complete style
        test_style = SimpleStyle("Test Style")
        print(f"✓ SimpleStyle created: {test_style.name}")
        
        # Test pre-defined styles
        print(f"✓ Dau style: {DAU_STYLE.name}")
        print(f"✓ Peirce style: {PEIRCE_STYLE.name}, corner_radius={PEIRCE_STYLE.cut_style.corner_radius}")
        print(f"✓ LaTeX style: {LATEX_STYLE.name}, ligature_width={LATEX_STYLE.ligature_style.line_width}")
        print(f"✓ Handwritten style: {HANDWRITTEN_STYLE.name}, cut_shape={HANDWRITTEN_STYLE.cut_style.shape_type}")
        
        return True
        
    except Exception as e:
        print(f"✗ Style system error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_egi_core():
    """Test EGI core functionality."""
    print("\nTesting EGI core...")
    
    try:
        from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut, ElementID
        from frozendict import frozendict
        
        # Create vertices
        v1 = ElementID("v1")
        v2 = ElementID("v2") 
        v3 = ElementID("v3")
        
        vertices = frozenset([
            Vertex(id=v1, label="A", is_generic=False),
            Vertex(id=v2, label="B", is_generic=False),
            Vertex(id=v3, label="C", is_generic=False)
        ])
        
        # Create edges
        e1 = ElementID("e1")
        e2 = ElementID("e2")
        
        edges = frozenset([
            Edge(id=e1),
            Edge(id=e2)
        ])
        
        # Create nu mapping
        nu_mapping = frozendict({
            e1: (v1, v2),
            e2: (v2, v3)
        })
        
        # Create cuts
        c1 = ElementID("c1")
        cuts = frozenset([Cut(id=c1)])
        
        # Create area mapping - all elements must be covered
        sheet_id = "sheet_1"
        area_mapping = frozendict({
            sheet_id: frozenset([v1, v2, e1, c1]),  # Elements on sheet (including cut)
            c1: frozenset([v3, e2])  # Elements in cut
        })
        
        # Create relation mapping
        rel_mapping = frozendict({
            e1: "loves",
            e2: "knows"
        })
        
        # Create EGI with all required components
        egi = RelationalGraphWithCuts(
            V=vertices,
            E=edges,
            nu=nu_mapping,
            sheet=sheet_id,
            Cut=cuts,
            area=area_mapping,
            rel=rel_mapping
        )
        
        print(f"✓ Created EGI with {len(egi.V)} vertices")
        print(f"✓ EGI has {len(egi.E)} edges with nu mappings")
        print(f"✓ EGI has {len(egi.Cut)} cuts with area mappings")
        
        return True
        
    except Exception as e:
        print(f"✗ EGI core error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_chapter21_engine():
    """Test Chapter 21 diagram engine."""
    print("\nTesting Chapter 21 engine...")
    
    try:
        from chapter21_diagram_engine import UniversalEGIEngine, InteractionMode, ViewSpecification
        
        # Create engine
        engine = UniversalEGIEngine()
        print("✓ UniversalEGIEngine created")
        
        # Test interaction modes
        modes = [InteractionMode.ORGANON, InteractionMode.ERGASTERION, InteractionMode.AGON]
        print(f"✓ Interaction modes available: {[mode.value for mode in modes]}")
        
        # Create view specification
        view_spec = ViewSpecification(
            focus_elements=set(),
            context_radius=100.0,
            detail_level=1.0,
            interaction_mode=InteractionMode.ORGANON,
            show_subgraph_hints=True
        )
        print("✓ ViewSpecification created")
        
        return True
        
    except Exception as e:
        print(f"✗ Chapter 21 engine error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_corpus_loading():
    """Test loading corpus examples."""
    print("\nTesting corpus loading...")
    
    try:
        # Test file existence
        corpus_files = [
            "/Users/mjh/Sync/GitHub/Arisbe/corpus/graphs/dau_2006_p112_ligature/dau_2006_p112_ligature.egi.json",
            "/Users/mjh/Sync/GitHub/Arisbe/corpus/graphs/peirce_modus_ponens/peirce_modus_ponens.egi.json",
            "/Users/mjh/Sync/GitHub/Arisbe/corpus/graphs/mixed_quantifier_complex/mixed_quantifier_complex.egi.json"
        ]
        
        available_files = []
        for file_path in corpus_files:
            if os.path.exists(file_path):
                available_files.append(file_path)
                print(f"✓ Found: {os.path.basename(file_path)}")
            else:
                print(f"✗ Missing: {os.path.basename(file_path)}")
        
        # Try loading one file
        if available_files:
            test_file = available_files[0]
            with open(test_file, 'r') as f:
                data = json.load(f)
            
            print(f"✓ Loaded JSON from {os.path.basename(test_file)}")
            
            # Check structure
            if 'V' in data:
                print(f"  - Vertices: {len(data['V'])}")
            if 'E' in data:
                print(f"  - Edges: {len(data['E'])}")
            if 'Cut' in data:
                print(f"  - Cuts: {len(data['Cut'])}")
                
        return len(available_files) > 0
        
    except Exception as e:
        print(f"✗ Corpus loading error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_architecture_integration():
    """Test integration between components."""
    print("\nTesting architecture integration...")
    
    try:
        # Test imports
        from gui.simple_style_system import SimpleStyle
        from egi_core_dau import RelationalGraphWithCuts, Vertex, ElementID
        from chapter21_diagram_engine import UniversalEGIEngine
        
        # Create components
        style = SimpleStyle("Integration Test")
        engine = UniversalEGIEngine()
        
        # Create minimal EGI for testing
        from frozendict import frozendict
        
        v1 = ElementID("test_vertex")
        vertices = frozenset([Vertex(id=v1, label="Test", is_generic=False)])
        sheet_id = "test_sheet"
        
        egi = RelationalGraphWithCuts(
            V=vertices,
            E=frozenset(),
            nu=frozendict(),
            sheet=sheet_id,
            Cut=frozenset(),
            area=frozendict({sheet_id: frozenset([v1])}),  # Cover vertex on sheet
            rel=frozendict()
        )
        
        print("✓ All components integrate successfully")
        print(f"  - Style: {style.name}")
        print(f"  - EGI vertices: {len(egi.V)}")
        print(f"  - Engine: {type(engine).__name__}")
        
        return True
        
    except Exception as e:
        print(f"✗ Integration error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=== Arisbe Core Architecture Test ===\n")
    
    tests = [
        ("Style System", test_style_system),
        ("EGI Core", test_egi_core),
        ("Chapter 21 Engine", test_chapter21_engine),
        ("Corpus Loading", test_corpus_loading),
        ("Architecture Integration", test_architecture_integration)
    ]
    
    results = {}
    for test_name, test_func in tests:
        results[test_name] = test_func()
    
    print("\n=== Test Results ===")
    passed = 0
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\n🎉 All core architecture tests passed!")
        print("The system is ready for GUI integration when environment issues are resolved.")
    else:
        print(f"\n⚠️  {len(tests) - passed} tests failed. Check errors above.")


if __name__ == "__main__":
    main()
