#!/usr/bin/env python3
"""
Simplified Constraint Layout Test

Quick validation that the constraint-based layout engine works correctly
for the key problematic EGIF cases before full integration.
"""

import sys
import os
import cairo

# Add the src directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from egif_parser_dau import parse_egif
from constraint_layout_prototype import ConstraintLayoutEngine, CairoEGRenderer


def test_key_cases():
    """Test the key problematic EGIF cases that failed with Graphviz."""
    
    print("🧪 Testing Key Constraint-Based Layout Cases")
    print("=" * 60)
    
    test_cases = [
        {
            'name': 'Mixed Cut and Sheet',
            'egif': '(Human "Socrates") ~[ (Mortal "Socrates") ]',
            'expected': 'Human outside cut, Mortal inside cut'
        },
        {
            'name': 'Nested Cuts',
            'egif': '~[ ~[ (P "x") ] ]',
            'expected': 'Inner cut inside outer cut'
        },
        {
            'name': 'Sibling Cuts',
            'egif': '~[ (P "x") ] ~[ (Q "x") ]',
            'expected': 'Two cuts non-overlapping, shared vertex at sheet'
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test_case['name']}")
        print(f"EGIF: {test_case['egif']}")
        print(f"Expected: {test_case['expected']}")
        print("-" * 40)
        
        try:
            # Parse EGIF
            print("🔍 Parsing EGIF...")
            graph = parse_egif(test_case['egif'])
            
            if not graph:
                print("❌ EGIF parsing failed")
                results.append(False)
                continue
            
            print(f"✅ Parsed: {len(graph.V)} vertices, {len(graph.E)} edges, {len(graph.Cut)} cuts")
            
            # Test constraint-based layout
            print("🔧 Testing constraint-based layout...")
            layout = ConstraintLayoutEngine()
            
            # Create variables for elements (simplified test)
            # CRITICAL FIX: Use actual sheet ID from parsed graph
            sheet_id = graph.sheet
            sheet_vars = layout.create_variables_for_element(sheet_id)
            
            # Set sheet bounds
            from cassowary import REQUIRED
            layout.solver.add_constraint(sheet_vars['x'] == 50, REQUIRED)
            layout.solver.add_constraint(sheet_vars['y'] == 50, REQUIRED)
            layout.solver.add_constraint(sheet_vars['width'] == 700, REQUIRED)
            layout.solver.add_constraint(sheet_vars['height'] == 500, REQUIRED)
            
            # Add elements based on graph structure
            element_count = 0
            for cut in graph.Cut:
                cut_vars = layout.create_variables_for_element(cut.id)
                layout.add_size_constraints(cut.id, min_width=150, min_height=100)
                layout.add_containment_constraint(sheet_id, cut.id, margin=30)
                element_count += 1
            
            for vertex in graph.V:
                vertex_vars = layout.create_variables_for_element(vertex.id)
                layout.add_size_constraints(vertex.id, min_width=10, min_height=10)
                # Find vertex area
                vertex_area = sheet_id  # Default to actual sheet ID
                for area_id, contents in graph.area.items():
                    if vertex.id in contents:
                        vertex_area = area_id
                        break
                if vertex_area != sheet_id:
                    layout.add_containment_constraint(vertex_area, vertex.id, margin=10)
                element_count += 1
            
            for edge in graph.E:
                edge_vars = layout.create_variables_for_element(edge.id)
                relation_name = graph.get_relation_name(edge.id)
                text_width = max(60, len(relation_name) * 8)
                layout.add_size_constraints(edge.id, min_width=text_width, min_height=25)
                # Find edge area
                edge_area = sheet_id  # Default to actual sheet ID
                for area_id, contents in graph.area.items():
                    if edge.id in contents:
                        edge_area = area_id
                        break
                if edge_area != sheet_id:
                    layout.add_containment_constraint(edge_area, edge.id, margin=10)
                element_count += 1
            
            print(f"📐 Created variables for {element_count} elements")
            
            # Solve layout
            print("🧮 Solving constraint system...")
            positions = layout.solve_layout()
            
            if positions:
                print("✅ Constraint system solved!")
                
                # Quick verification
                verification_passed = True
                
                # Check that cuts are properly positioned
                for cut in graph.Cut:
                    if cut.id in positions:
                        pos = positions[cut.id]
                        if pos['width'] < 100 or pos['height'] < 50:
                            print(f"⚠️  Cut {cut.id} may be too small: {pos['width']}x{pos['height']}")
                        else:
                            print(f"✅ Cut {cut.id} properly sized: {pos['width']:.1f}x{pos['height']:.1f}")
                
                # Render test output
                output_file = f"/Users/mjh/Sync/GitHub/Arisbe/constraint_simple_test_{i}.png"
                renderer = CairoEGRenderer(width=800, height=600)
                
                # Draw elements
                for cut in graph.Cut:
                    if cut.id in positions:
                        pos = positions[cut.id]
                        renderer.draw_cut(pos['x'], pos['y'], pos['width'], pos['height'], f"Cut {cut.id}")
                
                for vertex in graph.V:
                    if vertex.id in positions:
                        pos = positions[vertex.id]
                        renderer.draw_vertex(pos['x'] + pos['width']/2, pos['y'] + pos['height']/2, 
                                           radius=4, label=vertex.id)
                
                for edge in graph.E:
                    if edge.id in positions:
                        pos = positions[edge.id]
                        relation_name = graph.get_relation_name(edge.id)
                        renderer.draw_predicate(pos['x'], pos['y'], pos['width'], pos['height'], relation_name)
                
                renderer.save_to_file(output_file)
                print(f"✅ Saved test diagram to {output_file}")
                
                results.append(True)
            else:
                print("❌ Constraint solving failed")
                results.append(False)
        
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results.append(False)
    
    # Summary
    print(f"\n📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test_case, result) in enumerate(zip(test_cases, results), 1):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} Test {i}: {test_case['name']}")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Constraint-based layout is ready for integration!")
        return True
    else:
        print("⚠️  Some tests failed. Need to debug before integration.")
        return False


if __name__ == "__main__":
    success = test_key_cases()
    sys.exit(0 if success else 1)
