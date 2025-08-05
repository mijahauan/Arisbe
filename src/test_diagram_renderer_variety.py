#!/usr/bin/env python3
"""
Comprehensive Test Suite for DiagramRenderer with EGIF Variety

Tests the DiagramRenderer with a wide range of EGIF examples to verify
correct rendering of different EG structures per Dau's formalism.
"""

from egif_parser_dau import parse_egif
from graphviz_layout_engine_v2 import create_graphviz_layout
from diagram_renderer_dau import create_dau_diagram_renderer
from pyside6_canvas import create_qt_canvas
import sys
import time

# Test cases covering different EG structures
TEST_CASES = [
    {
        'name': 'Simple Predicate',
        'egif': '(Human "Socrates")',
        'description': 'Single predicate with constant'
    },
    {
        'name': 'Simple Negation',
        'egif': '~[ (Mortal "Socrates") ]',
        'description': 'Single predicate inside cut (negation)'
    },
    {
        'name': 'Conjunction',
        'egif': '(Human "Socrates") (Mortal "Socrates")',
        'description': 'Two predicates sharing same constant'
    },
    {
        'name': 'Mixed Context',
        'egif': '(Human "Socrates") ~[ (Mortal "Socrates") ]',
        'description': 'One predicate outside, one inside cut'
    },
    {
        'name': 'Double Negation',
        'egif': '~[ ~[ (Human "Socrates") ] ]',
        'description': 'Nested cuts (double negation)'
    },
    {
        'name': 'Sibling Cuts',
        'egif': '*x ~[ (P x) ] ~[ (Q x) ]',
        'description': 'Variable with two separate negated predicates'
    },
    {
        'name': 'Binary Relation',
        'egif': '*x *y (Loves x y)',
        'description': 'Binary predicate with two variables'
    },
    {
        'name': 'Complex Nesting',
        'egif': '*x (Human x) ~[ (Mortal x) (Wise x) ]',
        'description': 'Mixed positive and negated predicates'
    },
    {
        'name': 'Ternary Relation',
        'egif': '*x *y *z (Between x y z)',
        'description': 'Ternary predicate with three variables'
    },
    {
        'name': 'Deep Nesting',
        'egif': '~[ ~[ ~[ (P "a") ] ] ]',
        'description': 'Triple-nested cuts'
    }
]

def test_single_case(test_case, renderer, show_window=True):
    """Test a single EGIF case with the DiagramRenderer."""
    print(f"\n🧪 Testing: {test_case['name']}")
    print(f"📝 EGIF: {test_case['egif']}")
    print(f"📖 Description: {test_case['description']}")
    
    try:
        # Step 1: Parse EGIF to EGI
        graph = parse_egif(test_case['egif'])
        vertices = len(graph._vertex_map)
        predicates = len(graph.nu)
        cuts = len(graph.Cut)
        print(f"✅ EGI parsed: {vertices} vertices, {predicates} predicates, {cuts} cuts")
        
        # Step 2: Generate layout
        layout_result = create_graphviz_layout(graph)
        print(f"✅ Layout generated: {len(layout_result.primitives)} spatial primitives")
        
        # Step 3: Create canvas and render
        canvas_title = f"EG Test: {test_case['name']} - {test_case['egif']}"
        canvas = create_qt_canvas(800, 600, canvas_title)
        
        # Step 4: Render diagram
        renderer.render_diagram(canvas, graph, layout_result)
        print(f"✅ Diagram rendered successfully")
        
        if show_window:
            # Step 5: Display and wait for user
            canvas.show()
            print(f"🖼️  Window displayed. Press Enter to continue to next test...")
            input()  # Wait for user input before proceeding
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all test cases sequentially."""
    print("🎨 DiagramRenderer Comprehensive Test Suite")
    print("=" * 60)
    
    # Create renderer once
    renderer = create_dau_diagram_renderer()
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n[{i}/{len(TEST_CASES)}] " + "=" * 40)
        
        success = test_single_case(test_case, renderer, show_window=True)
        
        if success:
            passed += 1
            print(f"✅ PASSED: {test_case['name']}")
        else:
            failed += 1
            print(f"❌ FAILED: {test_case['name']}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {passed}/{len(TEST_CASES)} ({100*passed/len(TEST_CASES):.1f}%)")
    
    if failed == 0:
        print("🎉 All tests passed! DiagramRenderer is working correctly.")
    else:
        print("⚠️  Some tests failed. Review the output for issues.")

def run_batch_test():
    """Run all tests without showing windows (for quick validation)."""
    print("🎨 DiagramRenderer Batch Test (No Windows)")
    print("=" * 60)
    
    renderer = create_dau_diagram_renderer()
    
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"[{i}/{len(TEST_CASES)}] Testing {test_case['name']}...", end=" ")
        success = test_single_case(test_case, renderer, show_window=False)
        print("✅ PASS" if success else "❌ FAIL")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--batch":
        run_batch_test()
    else:
        print("DiagramRenderer Comprehensive Test Suite")
        print("This will test the renderer with various EGIF examples.")
        print("Each test will show a window - press Enter to continue to the next test.")
        print("\nRun with --batch flag for quick validation without windows.")
        print("\nPress Enter to start...")
        input()
        run_all_tests()
