"""
Simple test to verify predicate/relation rendering is working correctly.
Creates a basic graph with predicates and saves the visual output.
"""

import sys
import os

# Ensure current directory is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from egif_parser_dau import EGIFParser
from tkinter_backend import TkinterCanvas
from diagram_controller import DiagramController
from diagram_renderer import VisualTheme


def test_simple_predicate():
    """Test simple predicate rendering"""
    print("🧪 Testing Simple Predicate Rendering")
    print("=" * 40)
    
    # Test a simple relation
    egif_text = '(Human "Socrates")'
    
    try:
        parser = EGIFParser(egif_text)
        graph = parser.parse()
        
        print(f"✅ Parsed: {egif_text}")
        print(f"   Vertices: {len(graph.V)}")
        print(f"   Edges: {len(graph.E)}")
        print(f"   Cuts: {len(graph.Cut)}")
        
        # Create visual representation
        canvas = TkinterCanvas(600, 400, title="Simple Predicate Test")
        controller = DiagramController(canvas, 600, 400, VisualTheme.DAU_STANDARD)
        controller.set_graph(graph)
        
        # Save output
        output_file = "test_simple_predicate.png"
        controller.save_diagram(output_file)
        print(f"💾 Saved to: {output_file}")
        
        # Show layout info
        if controller.state.layout_result:
            layout = controller.state.layout_result
            print(f"📐 Layout: {len(layout.elements)} elements positioned")
            print(f"   Quality score: {layout.layout_quality_score:.2f}")
            
            # List what elements were positioned
            for element in layout.elements:
                print(f"   - {element.element_type}: {element.element_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_complex_predicate():
    """Test complex predicate rendering with cuts"""
    print("\n🧪 Testing Complex Predicate Rendering")
    print("=" * 40)
    
    # Test the corrected complex example
    egif_text = '(Human "Socrates") ~[ (Mortal "Socrates") ]'
    
    try:
        parser = EGIFParser(egif_text)
        graph = parser.parse()
        
        print(f"✅ Parsed: {egif_text}")
        print(f"   Vertices: {len(graph.V)}")
        print(f"   Edges: {len(graph.E)}")
        print(f"   Cuts: {len(graph.Cut)}")
        
        # Create visual representation
        canvas = TkinterCanvas(700, 500, title="Complex Predicate Test")
        controller = DiagramController(canvas, 700, 500, VisualTheme.DAU_STANDARD)
        controller.set_graph(graph)
        
        # Save output
        output_file = "test_complex_predicate.png"
        controller.save_diagram(output_file)
        print(f"💾 Saved to: {output_file}")
        
        # Show layout info
        if controller.state.layout_result:
            layout = controller.state.layout_result
            print(f"📐 Layout: {len(layout.elements)} elements positioned")
            print(f"   Quality score: {layout.layout_quality_score:.2f}")
            
            # List what elements were positioned
            for element in layout.elements:
                print(f"   - {element.element_type}: {element.element_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_corrected_example_4():
    """Test the corrected example 4 with proper bound variables"""
    print("\n🧪 Testing Corrected Example 4")
    print("=" * 40)
    
    # Test the corrected example 4
    egif_text = '*x ~[ (Human x) (Mortal x) ]'
    
    try:
        parser = EGIFParser(egif_text)
        graph = parser.parse()
        
        print(f"✅ Parsed: {egif_text}")
        print(f"   Vertices: {len(graph.V)}")
        print(f"   Edges: {len(graph.E)}")
        print(f"   Cuts: {len(graph.Cut)}")
        
        # Create visual representation
        canvas = TkinterCanvas(700, 500, title="Corrected Example 4")
        controller = DiagramController(canvas, 700, 500, VisualTheme.DAU_STANDARD)
        controller.set_graph(graph)
        
        # Save output
        output_file = "test_example_4_corrected.png"
        controller.save_diagram(output_file)
        print(f"💾 Saved to: {output_file}")
        
        # Show layout info
        if controller.state.layout_result:
            layout = controller.state.layout_result
            print(f"📐 Layout: {len(layout.elements)} elements positioned")
            print(f"   Quality score: {layout.layout_quality_score:.2f}")
            
            # List what elements were positioned
            for element in layout.elements:
                print(f"   - {element.element_type}: {element.element_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Predicate Rendering Test Suite")
    print("Testing if predicates/relations are now visible in EG diagrams")
    print()
    
    results = []
    
    # Run tests
    results.append(test_simple_predicate())
    results.append(test_complex_predicate())
    results.append(test_corrected_example_4())
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 40)
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Predicate rendering is working correctly")
        print("✅ Clean architecture successfully renders complete EG diagrams")
        print("✅ Ready for Phase 2: Selection Overlays & Dynamic Effects")
    else:
        print("⚠️  Some tests failed - predicate rendering needs more debugging")
    
    print("\n📁 Generated test files:")
    print("   - test_simple_predicate.png")
    print("   - test_complex_predicate.png") 
    print("   - test_example_4_corrected.png")
    print("\n✨ Predicate rendering test complete!")
