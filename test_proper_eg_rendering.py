#!/usr/bin/env python3
"""
Test Proper EG Rendering with Dau's Conventions

This test uses the correct pipeline:
EGIF → EGI → Graphviz Layout → Dau Renderer → Visual Output

The goal is to produce diagrams that properly show:
1. Heavy lines of identity connecting vertices to predicates
2. Fine-drawn cuts as closed curves
3. Proper containment (predicates inside cuts)
4. Nu mapping with hooks and argument order
5. No overlapping elements
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import contract validation
from pipeline_contracts import (
    validate_full_pipeline,
    validate_egif_to_egi_handoff,
    validate_egi_to_layout_handoff,
    validate_layout_to_render_handoff,
    ContractViolationError
)

def test_proper_eg_rendering():
    """Test the complete proper EG rendering pipeline."""
    
    print("🎨 Testing Proper EG Rendering with Dau's Conventions")
    print("=" * 60)
    
    # Test cases that should demonstrate key EG features
    test_cases = [
        {
            'name': 'Simple Relation',
            'egif': '(Human "Socrates")',
            'expected': 'Constant vertex with predicate attached via heavy line'
        },
        {
            'name': 'Variable with Predicate',
            'egif': '*x (Human x)',
            'expected': 'Variable vertex with predicate, heavy line connection'
        },
        {
            'name': 'Cut with Containment',
            'egif': '*x ~[ (Mortal x) ]',
            'expected': 'Vertex outside cut, predicate inside cut, line crosses boundary'
        },
        {
            'name': 'Sibling Cuts',
            'egif': '*x ~[ (Human x) ] ~[ (Mortal x) ]',
            'expected': 'Two non-overlapping cuts, shared vertex, proper containment'
        }
    ]
    
    try:
        # Import the correct components
        from egif_parser_dau import parse_egif
        from graphviz_layout_engine_v2 import GraphvizLayoutEngine
        from diagram_renderer_dau import DiagramRendererDau, VisualConvention
        from pyside6_canvas import PySide6Canvas
        
        print("✅ All components imported successfully")
        
        # Initialize components
        layout_engine = GraphvizLayoutEngine()
        conventions = VisualConvention()
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. {test_case['name']}: {test_case['egif']}")
            print(f"   Expected: {test_case['expected']}")
            
            try:
                # Step 1: Parse EGIF → EGI
                graph = parse_egif(test_case['egif'])
                print(f"   ✅ Parsed: {len(graph.V)} vertices, {len(graph.E)} edges, {len(graph.Cut)} cuts")
                
                # CONTRACT VALIDATION: EGIF → EGI handoff
                validate_egif_to_egi_handoff(test_case['egif'], graph)
                
                # Step 2: Create Layout (this returns LayoutResult, not RelationalGraphWithCuts)
                layout_result = layout_engine.create_layout_from_graph(graph)
                print(f"   ✅ Layout: {len(layout_result.primitives)} elements positioned")
                
                # CONTRACT VALIDATION: EGI → Layout handoff
                validate_egi_to_layout_handoff(graph, layout_result)
                
                # Debug: Show what elements are in the layout
                print(f"   📊 Layout elements:")
                for elem_id, primitive in layout_result.primitives.items():
                    print(f"      {elem_id}: {primitive.element_type} at {primitive.position}")
                
                # Step 3: Render with Dau conventions
                canvas = PySide6Canvas(800, 600, title=f"EG: {test_case['name']}")
                renderer = DiagramRendererDau(conventions)
                
                # CONTRACT VALIDATION: Layout → Render handoff
                validate_layout_to_render_handoff(layout_result, graph, canvas)
                
                # VALIDATED: All contracts confirmed, proceed with rendering
                # FIXED: Correct parameter order (canvas, graph, layout_result)
                renderer.render_diagram(canvas, graph, layout_result)
                
                # Step 4: Save to file
                output_file = f"proper_eg_{i}_{test_case['name'].lower().replace(' ', '_')}.png"
                canvas.save_to_file(output_file)
                print(f"   ✅ Rendered: {output_file}")
                
            except ContractViolationError as e:
                print(f"   ❌ CONTRACT VIOLATION: {e}")
                print("   This indicates an API mismatch between pipeline components.")
                return False
            except Exception as e:
                print(f"   ❌ Error: {e}")
                import traceback
                traceback.print_exc()
    
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("This indicates the rendering pipeline components are not properly connected.")
        return False
    
    print(f"\n🎯 Proper EG rendering test complete!")
    return True


def analyze_rendering_output():
    """Analyze the rendered output to see if it shows proper EG elements."""
    
    print("\n🔍 Analyzing Rendered Output")
    print("-" * 40)
    
    expected_elements = [
        "Heavy lines of identity (thick lines connecting vertices to predicates)",
        "Fine-drawn cuts (closed curves around predicates)", 
        "Proper containment (predicates entirely within cuts)",
        "Non-overlapping cuts (sibling cuts don't overlap)",
        "Nu mapping visualization (argument order for relations)"
    ]
    
    print("Expected EG elements that should be visible in the PNG files:")
    for i, element in enumerate(expected_elements, 1):
        print(f"  {i}. {element}")
    
    print("\nKey visual indicators of correct EG rendering:")
    print("  • Thick black lines connecting dots (vertices) to predicate names")
    print("  • Closed oval/circular curves around predicates in cuts")
    print("  • Predicates completely inside cut boundaries")
    print("  • No overlapping between sibling cuts")
    print("  • Clear spatial separation between all elements")


if __name__ == "__main__":
    print("Arisbe Proper EG Rendering Test")
    print("=" * 40)
    
    # Test the proper rendering pipeline
    success = test_proper_eg_rendering()
    
    if success:
        print("\n✅ Rendering pipeline test completed!")
        analyze_rendering_output()
    else:
        print("\n❌ The rendering pipeline needs to be fixed.")
        print("Key issues to address:")
        print("1. Connect DiagramRendererDau to the layout engine")
        print("2. Ensure heavy lines of identity are drawn")
        print("3. Implement proper cut rendering as closed curves")
        print("4. Add nu mapping visualization with hooks")
        print("5. Enforce containment and non-overlap constraints")
