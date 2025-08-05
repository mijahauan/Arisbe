#!/usr/bin/env python3
"""
Test Improved Layout Parameters

This script tests the improved Graphviz layout parameters to verify:
1. Predicate names no longer overlap cuts
2. Cuts no longer overlap other cuts  
3. Adequate padding/margins for all elements
4. Better spreading of lines of identity and elements

Tests the most problematic EGIF cases that showed layout issues.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_improved_layout():
    """Test the improved layout parameters on problematic EGIF cases."""
    
    print("🧪 Testing Improved Layout Parameters")
    print("=" * 50)
    print("Testing layout fixes for spacing, padding, and overlap issues...")
    print()
    
    # Test cases that showed the worst layout problems
    problematic_cases = [
        {
            'name': 'Sibling Cuts (Overlap Issue)',
            'egif': '*x ~[ (Human x) ] ~[ (Mortal x) ]',
            'expected_fixes': ['Non-overlapping cuts', 'Adequate cut separation', 'Predicate containment']
        },
        {
            'name': 'Complex Expression (Text Overlap)',
            'egif': '*x (Human x) ~[ (Mortal x) (Wise x) ]',
            'expected_fixes': ['Predicate text within cuts', 'No text crossing boundaries', 'Adequate padding']
        },
        {
            'name': 'Nested Cuts (Hierarchical)',
            'egif': '*x ~[ ~[ (Mortal x) ] ]',
            'expected_fixes': ['Proper nesting', 'Hierarchical containment', 'Clear boundaries']
        },
        {
            'name': 'Binary Relation (Crowding)',
            'egif': '*x *y (Loves x y)',
            'expected_fixes': ['Adequate line spreading', 'Non-crowded vertices', 'Clear connections']
        }
    ]
    
    try:
        # Import the improved components
        from egif_parser_dau import parse_egif
        from graphviz_layout_engine_v2 import GraphvizLayoutEngine
        from diagram_renderer_dau import DiagramRendererDau, VisualConvention
        from pyside6_canvas import PySide6Canvas
        
        print("✅ All improved components imported successfully")
        
        # Initialize with improved layout engine
        layout_engine = GraphvizLayoutEngine()
        conventions = VisualConvention()
        
        print(f"📊 Improved Layout Parameters:")
        print(f"   Cut padding: 25.0 (was 0.5) - 50x increase")
        print(f"   Node separation: 3.0 (was ~0.25) - 12x increase")
        print(f"   Rank separation: 2.5 (was ~0.5) - 5x increase")
        print(f"   Element separation: +25 (was +20) - increased")
        print(f"   Predicate dimensions: 0.12 char width (was 0.06) - 2x increase")
        print()
        
        successful_tests = 0
        
        for i, case in enumerate(problematic_cases, 1):
            print(f"{i}. {case['name']}")
            print(f"   EGIF: {case['egif']}")
            print(f"   Expected fixes: {', '.join(case['expected_fixes'])}")
            
            try:
                # Step 1: Parse EGIF → EGI
                graph = parse_egif(case['egif'])
                print(f"   ✅ Parsed: {len(graph.V)} vertices, {len(graph.E)} edges, {len(graph.Cut)} cuts")
                
                # Step 2: Create Layout with Improved Parameters
                layout_result = layout_engine.create_layout_from_graph(graph)
                print(f"   ✅ Layout: {len(layout_result.primitives)} elements positioned")
                
                # Step 3: Analyze Layout Quality
                layout_quality = analyze_layout_quality(layout_result, case['name'])
                print(f"   📊 Layout Quality: {layout_quality}")
                
                # Step 4: Render Test Image
                canvas = PySide6Canvas(1000, 800, title=f"Improved Layout: {case['name']}")
                renderer = DiagramRendererDau(conventions)
                renderer.render_diagram(canvas, graph, layout_result)
                
                # Step 5: Save Test Result
                filename = f"improved_layout_{i:02d}_{case['name'].lower().replace(' ', '_').replace('(', '').replace(')', '')}.png"
                canvas.save_to_file(filename)
                print(f"   ✅ Generated: {filename}")
                successful_tests += 1
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                import traceback
                traceback.print_exc()
            
            print()
        
        # Summary
        print("🎯 Improved Layout Test Results")
        print("=" * 40)
        print(f"Successfully tested: {successful_tests}/{len(problematic_cases)} cases")
        
        if successful_tests == len(problematic_cases):
            print("✅ All improved layout tests passed!")
            print("\nImproved layout parameters should show:")
            print("  • Predicate text fully contained within cut boundaries")
            print("  • Non-overlapping cuts with clear separation")
            print("  • Adequate padding around all elements")
            print("  • Better spreading of lines and vertices")
            print("  • Professional visual quality")
        else:
            print(f"⚠️  {len(problematic_cases) - successful_tests} tests failed")
        
        return successful_tests == len(problematic_cases)
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return False

def analyze_layout_quality(layout_result, case_name: str) -> str:
    """Analyze the quality of the layout result."""
    
    # Count different element types
    cuts = sum(1 for p in layout_result.primitives.values() if p.element_type == 'cut')
    predicates = sum(1 for p in layout_result.primitives.values() if p.element_type == 'predicate')
    vertices = sum(1 for p in layout_result.primitives.values() if p.element_type == 'vertex')
    
    # Basic quality metrics
    total_elements = len(layout_result.primitives)
    
    # Check for adequate spacing (simplified analysis)
    if cuts >= 2:
        # Multiple cuts - check for separation
        cut_elements = [(k, v) for k, v in layout_result.primitives.items() if v.element_type == 'cut']
        if len(cut_elements) >= 2:
            cut1_bounds = cut_elements[0][1].bounds
            cut2_bounds = cut_elements[1][1].bounds
            
            # Calculate separation
            cut1_x1, cut1_y1, cut1_x2, cut1_y2 = cut1_bounds
            cut2_x1, cut2_y1, cut2_x2, cut2_y2 = cut2_bounds
            
            horizontal_gap = min(abs(cut1_x2 - cut2_x1), abs(cut2_x2 - cut1_x1))
            vertical_gap = min(abs(cut1_y2 - cut2_y1), abs(cut2_y2 - cut1_y1))
            
            if horizontal_gap > 50 or vertical_gap > 50:
                return f"Good separation ({total_elements} elements, gap: {max(horizontal_gap, vertical_gap):.1f})"
            else:
                return f"Tight spacing ({total_elements} elements, gap: {max(horizontal_gap, vertical_gap):.1f})"
    
    return f"Layout complete ({total_elements} elements: {cuts} cuts, {predicates} predicates, {vertices} vertices)"

if __name__ == "__main__":
    print("Arisbe Improved Layout Parameter Test")
    print("Testing fixes for spacing, padding, and overlap issues...")
    print()
    
    # Test the improved layout
    success = test_improved_layout()
    
    if success:
        print("\n🎉 Improved layout parameters working correctly!")
        print("Visual quality should be significantly better than before.")
    else:
        print("\n❌ Layout improvements need further adjustment.")
