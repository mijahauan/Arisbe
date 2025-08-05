#!/usr/bin/env python3
"""
Test the constraint-based rendering integration with a variety of EGIF expressions.
This validates the complete pipeline across different structural patterns using the Cassowary constraint solver.
"""

import tkinter as tk
from egif_parser_dau import EGIFParser
from constraint_layout_engine import create_constraint_based_layout
from diagram_renderer_clean import CleanDiagramRenderer, TkinterCanvas

def test_egif_expression(egif_text, description, window_title):
    """Test a single EGIF expression with visual rendering."""
    
    print(f"\n=== Testing: {description} ===")
    print(f"EGIF: {egif_text}")
    
    try:
        # Parse EGIF → EGI
        parser = EGIFParser(egif_text)
        graph = parser.parse()
        
        print(f"✓ Parsed EGI: {len(graph.V)} vertices, {len(graph.E)} edges, {len(graph.Cut)} cuts")
        
        # Create window
        root = tk.Tk()
        root.title(window_title)
        root.geometry("900x700")
        
        tk_canvas = tk.Canvas(root, width=900, height=700, bg='white')
        tk_canvas.pack(expand=True, fill='both')
        canvas = TkinterCanvas(tk_canvas)
        
        # Set up rendering pipeline with constraint-based layout
        renderer = CleanDiagramRenderer(canvas)
        
        # Generate layout using constraint solver
        layout_result = create_constraint_based_layout(graph)
        
        # Render the result
        renderer.render(layout_result.primitives)
        
        # Display the result
        renderer.canvas.show()
        
        # Add title and description
        tk_canvas.create_text(450, 30, text=f"✓ {description}", 
                            font=("Arial", 16, "bold"), fill="darkgreen")
        tk_canvas.create_text(450, 55, text=f"EGIF: {egif_text}", 
                            font=("Arial", 11), fill="blue")
        tk_canvas.create_text(450, 75, text=f"Structure: {len(graph.V)} vertices, {len(graph.E)} predicates, {len(graph.Cut)} cuts", 
                            font=("Arial", 10), fill="gray")
        tk_canvas.create_text(450, 670, text="Close window to continue to next test", 
                            font=("Arial", 10), fill="darkblue")
        
        print(f"✓ Rendering successful - showing window")
        root.mainloop()
        return True
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_egif_test_suite():
    """Run comprehensive test suite with various EGIF patterns using constraint-based layout."""
    
    print("🚀 Testing Constraint-Based Layout with Variety of EGIF Expressions")
    
    test_cases = [
        {
            'egif': '(Human "Socrates")',
            'description': 'Simple Predicate',
            'title': 'Test 1: Simple Predicate - Human(Socrates)'
        },
        {
            'egif': '*x (Human x) (Mortal x)',
            'description': 'Shared Variable',
            'title': 'Test 2: Shared Variable - Human(x) ∧ Mortal(x)'
        },
        {
            'egif': '~[ (Human "Socrates") ]',
            'description': 'Single Cut',
            'title': 'Test 3: Single Cut - ¬Human(Socrates)'
        },
        {
            'egif': '~[ ~[ (Human "Socrates") ] ]',
            'description': 'Double Negation',
            'title': 'Test 4: Double Negation - ¬¬Human(Socrates)'
        },
        {
            'egif': '~[ ~[ (Human "Socrates") ] ~[ (Mortal "Plato") ] ]',
            'description': 'Non-overlapping Sibling Cuts',
            'title': 'Test 5: Sibling Cuts - ¬(¬Human(Socrates) ∧ ¬Mortal(Plato))'
        },
        {
            'egif': '*x (Human x) ~[ (Mortal x) ]',
            'description': 'Mixed Cut and Sheet',
            'title': 'Test 6: Mixed - Human(x) ∧ ¬Mortal(x)'
        },
        {
            'egif': '*x ~[ (Human x) ~[ (Mortal x) ] ]',
            'description': 'Nested Cuts',
            'title': 'Test 7: Nested Cuts - ¬(Human(x) ∧ ¬Mortal(x))'
        },
        {
            'egif': '*x *y (Loves x y) ~[ (Human x) ] ~[ (Human y) ]',
            'description': 'Binary Relation with Cuts',
            'title': 'Test 8: Binary Relation - Loves(x,y) ∧ ¬Human(x) ∧ ¬Human(y)'
        },
        {
            'egif': '(Human "Socrates") ~[ (Mortal "Socrates") ~[ (Wise "Socrates") ] ]',
            'description': 'Deeply Nested with Shared Constant',
            'title': 'Test 9: Deep Nesting - Human(Socrates) ∧ ¬(Mortal(Socrates) ∧ ¬Wise(Socrates))'
        },
        {
            'egif': '*x *y *z (Triangle x y z) ~[ ~[ (Equal x y) ] ~[ (Equal y z) ] ~[ (Equal x z) ] ]',
            'description': 'Complex Ternary with Multiple Cuts',
            'title': 'Test 10: Complex Ternary - Triangle(x,y,z) ∧ ¬(¬Equal(x,y) ∧ ¬Equal(y,z) ∧ ¬Equal(x,z))'
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"Running Test {i}/{len(test_cases)}")
        
        success = test_egif_expression(
            test_case['egif'],
            test_case['description'], 
            test_case['title']
        )
        
        results.append({
            'test': i,
            'description': test_case['description'],
            'egif': test_case['egif'],
            'success': success
        })
    
    # Summary
    print(f"\n{'='*60}")
    print(f"🎯 TEST SUITE SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for r in results if r['success'])
    total = len(results)
    
    print(f"Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"Test {result['test']:2d}: {status} - {result['description']}")
    
    if passed == total:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"Constraint-based layout is robust across diverse EGIF patterns")
        print(f"✅ Ready for Step 2: Main Application Integration")
    else:
        print(f"\n⚠️  Some tests failed - need investigation")
        print(f"Failed tests:")
        for result in results:
            if not result['success']:
                print(f"  - {result['description']}: {result['egif']}")
    
    return passed, total

if __name__ == "__main__":
    passed, total = run_egif_test_suite()
    
    print(f"\n🔬 Constraint-Based Layout Testing Complete")
    print(f"   {passed} out of {total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("✅ All constraint-based layout tests passed successfully!")
    else:
        print(f"❌ {total - passed} tests failed - check the output for issues")
