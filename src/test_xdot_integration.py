#!/usr/bin/env python3
"""
Comprehensive test suite for Graphviz xdot integration.
Tests the new xdot-based layout engine with various EGIF examples.
"""

from egif_parser_dau import parse_egif
from graphviz_layout_engine_v2 import create_graphviz_layout

def test_case(name, egif, expected_cuts=None, expected_nodes=None):
    """Test a single EGIF case and report results."""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"EGIF: {egif}")
    print(f"{'='*60}")
    
    try:
        # Parse EGIF
        graph = parse_egif(egif)
        print(f"✅ EGIF parsed: {len(graph._vertex_map)} vertices, {len(graph.nu)} predicates, {len(graph.Cut)} cuts")
        
        # Generate layout
        layout = create_graphviz_layout(graph)
        print(f"✅ Layout generated: {len(layout.primitives)} primitives")
        
        # Analyze results
        cuts = {pid: p for pid, p in layout.primitives.items() if p.element_type == 'cut'}
        nodes = {pid: p for pid, p in layout.primitives.items() if p.element_type in ['vertex', 'predicate']}
        edges = {pid: p for pid, p in layout.primitives.items() if p.element_type == 'edge'}
        
        print(f"\nRESULTS:")
        print(f"  Cuts: {len(cuts)}")
        for cut_id, cut in cuts.items():
            x1, y1, x2, y2 = cut.bounds
            print(f"    {cut_id}: bounds=({x1:.1f}, {y1:.1f}, {x2:.1f}, {y2:.1f}) center=({cut.position[0]:.1f}, {cut.position[1]:.1f})")
        
        print(f"  Nodes: {len(nodes)}")
        for node_id, node in nodes.items():
            print(f"    {node_id}: {node.element_type} at ({node.position[0]:.1f}, {node.position[1]:.1f})")
        
        print(f"  Edges: {len(edges)}")
        for edge_id, edge in edges.items():
            print(f"    {edge_id}: at ({edge.position[0]:.1f}, {edge.position[1]:.1f})")
        
        # Validate expectations
        if expected_cuts is not None and len(cuts) != expected_cuts:
            print(f"❌ EXPECTED {expected_cuts} cuts, got {len(cuts)}")
            return False
        
        if expected_nodes is not None and len(nodes) != expected_nodes:
            print(f"❌ EXPECTED {expected_nodes} nodes, got {len(nodes)}")
            return False
        
        # Check containment for nested cuts
        if len(cuts) > 1:
            print(f"\nCONTAINMENT ANALYSIS:")
            cut_list = list(cuts.values())
            for i, cut1 in enumerate(cut_list):
                for j, cut2 in enumerate(cut_list):
                    if i != j:
                        x1_1, y1_1, x2_1, y2_1 = cut1.bounds
                        x1_2, y1_2, x2_2, y2_2 = cut2.bounds
                        
                        # Check if cut2 is inside cut1
                        if x1_1 <= x1_2 and y1_1 <= y1_2 and x2_2 <= x2_1 and y2_2 <= y2_1:
                            print(f"    {cut2.element_id} is contained within {cut1.element_id} ✅")
                        # Check if cuts overlap (bad)
                        elif not (x2_1 < x1_2 or x2_2 < x1_1 or y2_1 < y1_2 or y2_2 < y1_1):
                            print(f"    {cut1.element_id} and {cut2.element_id} OVERLAP ❌")
        
        print(f"✅ TEST PASSED: {name}")
        return True
        
    except Exception as e:
        print(f"❌ TEST FAILED: {name} - {e}")
        import traceback
        traceback.print_exc()
        return False

def run_comprehensive_tests():
    """Run comprehensive test suite for xdot integration."""
    print("🚀 COMPREHENSIVE XDOT INTEGRATION TEST SUITE")
    print("Testing Graphviz native cluster boundary calculations...")
    
    test_results = []
    
    # Test 1: Simple negation
    test_results.append(test_case(
        "Simple Negation",
        '~[ (Mortal "Socrates") ]',
        expected_cuts=1,
        expected_nodes=2  # vertex + predicate
    ))
    
    # Test 2: Double negation
    test_results.append(test_case(
        "Double Negation", 
        '~[ ~[ (P "x") ] ]',
        expected_cuts=2,
        expected_nodes=2
    ))
    
    # Test 3: Triple negation
    test_results.append(test_case(
        "Triple Negation",
        '~[ ~[ ~[ (Q "y") ] ] ]',
        expected_cuts=3,
        expected_nodes=2
    ))
    
    # Test 4: Sibling cuts
    test_results.append(test_case(
        "Sibling Cuts",
        '*x ~[ (Human x) ] ~[ (Mortal x) ]',
        expected_cuts=2,
        expected_nodes=3  # vertex + 2 predicates
    ))
    
    # Test 5: Mixed sheet and cut
    test_results.append(test_case(
        "Mixed Sheet and Cut",
        '(Human "Socrates") ~[ (Mortal "Socrates") ]',
        expected_cuts=1,
        expected_nodes=3  # vertex + 2 predicates
    ))
    
    # Test 6: Complex nested with siblings
    test_results.append(test_case(
        "Complex Nested with Siblings",
        '*x ~[ (P x) ~[ (Q x) ] (R x) ]',
        expected_cuts=2,
        expected_nodes=4  # vertex + 3 predicates
    ))
    
    # Test 7: Binary relation
    test_results.append(test_case(
        "Binary Relation",
        '*x *y (Loves x y)',
        expected_cuts=0,
        expected_nodes=3  # 2 vertices + 1 predicate
    ))
    
    # Test 8: Binary relation in cut
    test_results.append(test_case(
        "Binary Relation in Cut",
        '*x *y ~[ (Loves x y) ]',
        expected_cuts=1,
        expected_nodes=3
    ))
    
    # Test 9: Complex existential
    test_results.append(test_case(
        "Complex Existential",
        '*x (Human x) ~[ *y (Loves x y) ~[ (Happy y) ] ]',
        expected_cuts=2,
        expected_nodes=5  # 2 vertices + 3 predicates
    ))
    
    # Test 10: Very deep nesting
    test_results.append(test_case(
        "Very Deep Nesting",
        '~[ ~[ ~[ ~[ (Deep "test") ] ] ] ]',
        expected_cuts=4,
        expected_nodes=2
    ))
    
    # Summary
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Xdot integration is working perfectly!")
    else:
        print(f"❌ {total-passed} tests failed. Need investigation.")
    
    return passed == total

if __name__ == "__main__":
    run_comprehensive_tests()
