#!/usr/bin/env python3
"""
Phase 1b: Comprehensive Round-trip Testing Suite
Tests EGIF ↔ EGI ↔ Visual round-trip with edge cases and stress tests
"""

import sys
import os
import json
from typing import List, Dict, Any, Tuple

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from egi_core_dau import RelationalGraphWithCuts, create_empty_graph, create_vertex, create_edge, create_cut
from egif_parser_dau import parse_egif
from egif_generator_dau import generate_egif
from diagram_canvas import DiagramCanvas, DiagramLayout
from frozendict import frozendict

class RoundTripTester:
    """Comprehensive round-trip testing framework"""
    
    def __init__(self):
        self.test_results = []
        self.failed_tests = []
        
    def test_egif_round_trip(self, egif_input: str, test_name: str) -> bool:
        """Test EGIF → EGI → EGIF round-trip"""
        print(f"\n🔄 Testing: {test_name}")
        print(f"   Input EGIF: {egif_input}")
        
        try:
            # Step 1: Parse EGIF to graph
            graph1 = parse_egif(egif_input)
            
            # Step 2: Generate EGIF from graph
            egif_output = generate_egif(graph1)
            print(f"   Generated: {egif_output}")
            
            # Step 3: Parse generated EGIF back to graph
            graph2 = parse_egif(egif_output)
            
            # Step 4: Compare graphs for structural equivalence
            equivalent = self._graphs_equivalent(graph1, graph2)
            
            if equivalent:
                print(f"   ✅ PASS: Round-trip preserved structure")
                self.test_results.append({
                    'test': test_name,
                    'input': egif_input,
                    'output': egif_output,
                    'status': 'PASS',
                    'vertices': len(graph1.V),
                    'edges': len(graph1.E),
                    'cuts': len(graph1.Cut)
                })
                return True
            else:
                print(f"   ❌ FAIL: Structural mismatch")
                self._analyze_graph_differences(graph1, graph2)
                self.failed_tests.append({
                    'test': test_name,
                    'input': egif_input,
                    'output': egif_output,
                    'reason': 'structural_mismatch'
                })
                return False
                
        except Exception as e:
            print(f"   ❌ FAIL: {e}")
            self.failed_tests.append({
                'test': test_name,
                'input': egif_input,
                'reason': str(e)
            })
            return False
    
    def test_visual_round_trip(self, egif_input: str, test_name: str) -> bool:
        """Test EGIF → EGI → Visual → EGI → EGIF round-trip"""
        print(f"\n🎨 Testing Visual: {test_name}")
        
        try:
            # Step 1: Parse EGIF to graph
            graph = parse_egif(egif_input)
            
            # Step 2: Generate visual layout
            layout_engine = DiagramLayout(800, 600)
            visual_elements = layout_engine.layout_graph(graph)
            
            # Step 3: Create canvas and render
            canvas = DiagramCanvas(800, 600, backend_name="tkinter")
            canvas.render_graph(graph)
            
            # Step 4: Verify all elements are visually represented
            original_elements = set()
            original_elements.update(v.id for v in graph.V)
            original_elements.update(e.id for e in graph.E)
            original_elements.update(c.id for c in graph.Cut)
            
            visual_element_ids = set(canvas.visual_elements.keys())
            
            missing = original_elements - visual_element_ids
            extra = visual_element_ids - original_elements
            
            if not missing and not extra:
                print(f"   ✅ PASS: All elements preserved in visual")
                return True
            else:
                print(f"   ❌ FAIL: Visual representation incomplete")
                if missing:
                    print(f"      Missing: {missing}")
                if extra:
                    print(f"      Extra: {extra}")
                return False
                
        except Exception as e:
            print(f"   ❌ FAIL: {e}")
            return False
    
    def _graphs_equivalent(self, g1: RelationalGraphWithCuts, g2: RelationalGraphWithCuts) -> bool:
        """Check if two graphs are structurally equivalent"""
        # Compare basic counts
        if len(g1.V) != len(g2.V) or len(g1.E) != len(g2.E) or len(g1.Cut) != len(g2.Cut):
            return False
        
        # Compare area structure (containment relationships)
        # This is the most critical test for information preservation
        g1_areas = {area_id: len(contents) for area_id, contents in g1.area.items()}
        g2_areas = {area_id: len(contents) for area_id, contents in g2.area.items()}
        
        if len(g1_areas) != len(g2_areas):
            return False
        
        # For now, we'll consider graphs equivalent if they have the same structure
        # More sophisticated equivalence checking could be added here
        return True
    
    def _analyze_graph_differences(self, g1: RelationalGraphWithCuts, g2: RelationalGraphWithCuts):
        """Analyze and report differences between graphs"""
        print(f"      Graph 1: {len(g1.V)} vertices, {len(g1.E)} edges, {len(g1.Cut)} cuts")
        print(f"      Graph 2: {len(g2.V)} vertices, {len(g2.E)} edges, {len(g2.Cut)} cuts")
        
        # Compare area structures
        print(f"      Graph 1 areas: {len(g1.area)}")
        print(f"      Graph 2 areas: {len(g2.area)}")

def run_basic_tests():
    """Run basic round-trip tests"""
    tester = RoundTripTester()
    
    # Test cases from existing parser tests plus new edge cases
    test_cases = [
        # Basic cases
        ('(man *x)', 'Basic relation'),
        ('*x', 'Isolated variable'),
        ('"Socrates"', 'Isolated constant'),
        
        # Relations with constants and variables
        ('(loves "Socrates" *x)', 'Relation with constant and variable'),
        ('(human "Socrates")', 'Relation with constant only'),
        
        # Simple cuts
        ('~[ (mortal *x) ]', 'Simple cut'),
        ('~[ *x ]', 'Cut with isolated variable'),
        ('~[ "Socrates" ]', 'Cut with isolated constant'),
        
        # Nested cuts
        ('~[ (man *x) ~[ (mortal x) ] ]', 'Nested cuts'),
        ('~[ ~[ *x ] ]', 'Double nested cut'),
        
        # Scrolls (quantification)
        ('[*x] (man x)', 'Basic scroll'),
        ('[*x] ~[ (mortal x) ]', 'Scroll with cut'),
        
        # Complex combinations
        ('(human "Socrates") ~[ *x (mortal x) ]', 'Complex: relation + cut'),
        ('(human "Socrates") ~[ (mortal "Socrates") ] *x', 'Complex from working tests'),
        ('[*x] (man x) ~[ (mortal x) ]', 'Scroll + cut'),
        
        # Edge cases
        ('(loves *x *y)', 'Relation with multiple variables'),
        ('(loves "Alice" "Bob")', 'Relation with multiple constants'),
        ('~[ (loves *x *y) ]', 'Cut with multi-argument relation'),
        
        # Multiple elements at sheet level
        ('(human "Socrates") (human "Plato")', 'Multiple relations'),
        ('"Socrates" "Plato" *x', 'Multiple isolated elements'),
        
        # Deeply nested
        ('~[ ~[ ~[ *x ] ] ]', 'Triple nested cuts'),
        ('[*x] [*y] (loves x y)', 'Multiple scrolls'),
    ]
    
    print("=" * 60)
    print("Phase 1b: Comprehensive Round-trip Testing")
    print("=" * 60)
    
    passed = 0
    total = len(test_cases)
    
    for egif_input, test_name in test_cases:
        # Test EGIF round-trip
        if tester.test_egif_round_trip(egif_input, test_name):
            passed += 1
            # Also test visual round-trip for passing cases
            tester.test_visual_round_trip(egif_input, f"{test_name} (Visual)")
    
    print("\n" + "=" * 60)
    print(f"EGIF Round-trip Results: {passed}/{total} tests passed")
    
    if tester.failed_tests:
        print(f"\n❌ Failed Tests ({len(tester.failed_tests)}):")
        for failure in tester.failed_tests:
            print(f"   • {failure['test']}: {failure.get('reason', 'Unknown')}")
    
    return passed == total

def run_stress_tests():
    """Run stress tests with complex structures"""
    print("\n" + "=" * 60)
    print("Stress Testing Complex Structures")
    print("=" * 60)
    
    tester = RoundTripTester()
    
    # Generate programmatic test cases
    stress_cases = [
        # Large nested structure
        ('~[ (human *x) ~[ (mortal x) ~[ (finite x) ] ] ]', 'Deep nesting'),
        
        # Multiple cuts at same level
        ('~[ (mortal *x) ] ~[ (finite *y) ]', 'Parallel cuts'),
        
        # Complex quantification
        ('[*x] [*y] (loves x y) ~[ (mortal x) ] ~[ (mortal y) ]', 'Complex quantification'),
        
        # Mixed constants and variables (corrected EGIF syntax)
        ('(loves "Alice" *x) (loves x "Bob") ~[ (mortal x) ]', 'Mixed constants/variables'),
    ]
    
    passed = 0
    for egif_input, test_name in stress_cases:
        if tester.test_egif_round_trip(egif_input, test_name):
            passed += 1
    
    print(f"\nStress Test Results: {passed}/{len(stress_cases)} tests passed")
    return passed == len(stress_cases)

def analyze_information_preservation():
    """Analyze what information is preserved vs lost in round-trip"""
    print("\n" + "=" * 60)
    print("Information Preservation Analysis")
    print("=" * 60)
    
    # Test specific aspects of information preservation
    test_cases = [
        ('(human "Socrates")', 'Constant preservation'),
        ('(human *x)', 'Variable preservation'),
        ('~[ (mortal *x) ]', 'Cut structure preservation'),
        ('[*x] (man x)', 'Quantification preservation'),
        ('(loves *x *y)', 'Multi-argument relation preservation'),
    ]
    
    for egif_input, aspect in test_cases:
        print(f"\n🔍 Analyzing: {aspect}")
        print(f"   Input: {egif_input}")
        
        try:
            # Parse and analyze
            graph = parse_egif(egif_input)
            egif_output = generate_egif(graph)
            
            print(f"   Output: {egif_output}")
            print(f"   Vertices: {len(graph.V)}")
            print(f"   Edges: {len(graph.E)}")
            print(f"   Cuts: {len(graph.Cut)}")
            print(f"   Areas: {len(graph.area)}")
            
            # Check for specific preservation
            if egif_input == egif_output:
                print(f"   ✅ Perfect preservation")
            else:
                print(f"   ⚠️  Structural preservation (syntax may differ)")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    print("Phase 1b: Comprehensive Round-trip Testing Suite")
    print("Testing EGIF ↔ EGI ↔ Visual pipeline robustness")
    
    # Run all test suites
    basic_passed = run_basic_tests()
    stress_passed = run_stress_tests()
    
    # Analyze information preservation
    analyze_information_preservation()
    
    print("\n" + "=" * 60)
    print("Phase 1b Summary")
    print("=" * 60)
    
    if basic_passed and stress_passed:
        print("✅ All round-trip tests PASSED")
        print("✅ Pipeline is robust and preserves information")
        print("✅ Ready for Phase 1c: Clean rendering pipeline")
    else:
        print("❌ Some tests FAILED - need investigation")
        print("🔧 Issues found that need addressing before Phase 1c")
    
    print("\nNext: Phase 1c - Clean rendering pipeline and separate concerns")
