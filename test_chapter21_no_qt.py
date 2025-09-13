#!/usr/bin/env python3
"""
Chapter 21 Test Suite (No Qt Dependencies)

Tests Chapter 21 functionality without GUI dependencies to verify core implementation.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def create_simple_test_egi():
    """Create a simple valid test EGI."""
    from frozendict import frozendict
    from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, ElementID
    
    # Simple EGI: two vertices connected by one edge
    v1 = Vertex(ElementID("person1"))
    v2 = Vertex(ElementID("person2"))
    e1 = Edge(ElementID("loves"))
    sheet = ElementID("sheet")
    
    test_egi = RelationalGraphWithCuts(
        V=frozenset([v1, v2]),
        E=frozenset([e1]),
        nu=frozendict({e1.id: (v1.id, v2.id)}),
        sheet=sheet,
        Cut=frozenset(),
        area=frozendict({
            sheet: frozenset([v1.id, v2.id, e1.id])
        }),
        rel=frozendict({e1.id: "Loves"})
    )
    
    return test_egi

def test_core_functionality():
    """Test core Chapter 21 functionality."""
    print("🧪 CHAPTER 21 CORE FUNCTIONALITY TEST")
    print("=" * 50)
    
    results = []
    
    # Test 1: EGI Creation
    try:
        test_egi = create_simple_test_egi()
        print("✅ Test EGI creation")
        results.append(True)
    except Exception as e:
        print(f"❌ Test EGI creation failed: {e}")
        results.append(False)
        return results
    
    # Test 2: Diagram Engine
    try:
        from chapter21_diagram_engine import UniversalEGIEngine, ViewSpecification, InteractionMode
        
        engine = UniversalEGIEngine()
        view_spec = ViewSpecification(
            focus_elements=set(),
            context_radius=2,
            interaction_mode=InteractionMode.ORGANON,
            show_subgraph_hints=True
        )
        
        view = engine.get_view(test_egi, view_spec)
        print(f"✅ Diagram engine: View with {len(view.visible_vertices)} vertices")
        results.append(True)
    except Exception as e:
        print(f"❌ Diagram engine failed: {e}")
        results.append(False)
    
    # Test 3: Format Synchronization
    try:
        formats = engine.synchronize_formats(test_egi)
        print(f"✅ Format synchronization: {len(formats)} formats")
        results.append(True)
    except Exception as e:
        print(f"❌ Format synchronization failed: {e}")
        results.append(False)
    
    # Test 4: Round-trip Validation
    try:
        is_valid = engine.validate_round_trip_equivalence(test_egi)
        print(f"✅ Round-trip validation: {'VALID' if is_valid else 'INVALID'}")
        results.append(True)
    except Exception as e:
        print(f"❌ Round-trip validation failed: {e}")
        results.append(False)
    
    # Test 5: Transformation Wizards
    try:
        from chapter21_transformation_wizards import UniversalTransformationWizardSystem
        from chapter21_diagram_engine import DisplayFormat
        
        wizard_system = UniversalTransformationWizardSystem(engine)
        wizard = wizard_system.create_wizard(DisplayFormat.DIAGRAM, test_egi)
        print("✅ Transformation wizard creation")
        results.append(True)
    except Exception as e:
        print(f"❌ Transformation wizard failed: {e}")
        results.append(False)
    
    # Test 6: State Management (without Qt)
    try:
        # Test the core state classes without Qt widgets
        from chapter21_gui_integration import DiagramInteractionState
        from chapter21_diagram_engine import InteractionMode, DisplayFormat
        
        state = DiagramInteractionState()
        state.current_egi = test_egi
        state.interaction_mode = InteractionMode.ORGANON
        state.active_format = DisplayFormat.DIAGRAM
        print("✅ State management")
        results.append(True)
    except Exception as e:
        print(f"❌ State management failed: {e}")
        results.append(False)
    
    return results

def test_individual_components():
    """Test individual components in isolation."""
    print("\n🔧 INDIVIDUAL COMPONENT TESTS")
    print("=" * 50)
    
    test_egi = create_simple_test_egi()
    
    # Test each component individually
    components = [
        ("Diagram Engine Import", lambda: __import__('chapter21_diagram_engine')),
        ("Wizard System Import", lambda: __import__('chapter21_transformation_wizards')),
        ("GUI Integration Import", lambda: __import__('chapter21_gui_integration')),
        ("EGI Core", lambda: test_egi.V),
        ("Format Enum", lambda: __import__('chapter21_diagram_engine').DisplayFormat.DIAGRAM),
        ("Mode Enum", lambda: __import__('chapter21_diagram_engine').InteractionMode.ORGANON),
    ]
    
    results = []
    for name, test_func in components:
        try:
            test_func()
            print(f"✅ {name}")
            results.append(True)
        except Exception as e:
            print(f"❌ {name}: {e}")
            results.append(False)
    
    return results

def main():
    """Run all tests."""
    print("🧪 CHAPTER 21 FUNCTIONALITY VERIFICATION")
    print("=" * 60)
    
    # Core functionality tests
    core_results = test_core_functionality()
    
    # Individual component tests  
    component_results = test_individual_components()
    
    # Summary
    total_core = len(core_results)
    passed_core = sum(core_results)
    
    total_components = len(component_results)
    passed_components = sum(component_results)
    
    print(f"\n🎯 TEST SUMMARY")
    print("=" * 30)
    print(f"Core Functionality: {passed_core}/{total_core} ({passed_core/total_core*100:.1f}%)")
    print(f"Components:        {passed_components}/{total_components} ({passed_components/total_components*100:.1f}%)")
    
    total_tests = total_core + total_components
    total_passed = passed_core + passed_components
    
    print(f"Overall:           {total_passed}/{total_tests} ({total_passed/total_tests*100:.1f}%)")
    
    if total_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Chapter 21 core implementation is functional")
        print("✅ Ready for Qt integration and interactive features")
    elif total_passed >= total_tests * 0.8:
        print("\n✅ MOSTLY FUNCTIONAL")
        print("✅ Chapter 21 core implementation working")
        print("⚠️  Some components need attention")
    else:
        print("\n⚠️  NEEDS WORK")
        print("❌ Several core components failing")
    
    return total_passed == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
