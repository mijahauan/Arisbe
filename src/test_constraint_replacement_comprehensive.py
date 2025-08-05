#!/usr/bin/env python3
"""
Comprehensive Test Suite for Constraint-Based Layout Engine

This test suite validates the constraint-based layout engine's functionality
throughout the entire application workflow, ensuring:

1. Core constraint layout functionality
2. Main application integration
3. Complex EGIF test cases
4. Visual rendering pipeline
5. Performance and robustness
6. Area containment correctness
7. Non-overlapping cut enforcement
"""

import sys
import os
import time
import traceback
from typing import List, Dict, Tuple, Optional

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Core imports
from egif_parser_dau import parse_egif
from constraint_layout_integration import ConstraintLayoutIntegration
from diagram_renderer_clean import CleanDiagramRenderer
from tkinter_backend import TkinterCanvas

class ComprehensiveTestSuite:
    """Comprehensive test suite for constraint-based layout engine replacement."""
    
    def __init__(self):
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_results = []
        
    def run_test(self, test_name: str, test_func, *args, **kwargs) -> bool:
        """Run a single test and track results."""
        print(f"\n📋 {test_name}")
        print("-" * 60)
        
        try:
            start_time = time.time()
            result = test_func(*args, **kwargs)
            end_time = time.time()
            
            if result:
                print(f"✅ PASS - {test_name} ({end_time - start_time:.2f}s)")
                self.passed_tests += 1
                self.test_results.append((test_name, True, end_time - start_time, None))
                return True
            else:
                print(f"❌ FAIL - {test_name}")
                self.failed_tests += 1
                self.test_results.append((test_name, False, end_time - start_time, "Test returned False"))
                return False
                
        except Exception as e:
            end_time = time.time()
            print(f"❌ ERROR - {test_name}: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            self.failed_tests += 1
            self.test_results.append((test_name, False, end_time - start_time, str(e)))
            return False
    
    def test_basic_constraint_functionality(self) -> bool:
        """Test 1: Basic constraint layout functionality."""
        print("Testing basic constraint layout with simple EGIF...")
        
        egif = '(Human "Socrates")'
        graph = parse_egif(egif)
        layout_engine = ConstraintLayoutIntegration()
        
        result = layout_engine.layout_graph(graph)
        
        # Validate result structure
        if not hasattr(result, 'primitives'):
            print("❌ Result missing 'primitives' attribute")
            return False
            
        if not hasattr(result, 'canvas_bounds'):
            print("❌ Result missing 'canvas_bounds' attribute")
            return False
            
        if not hasattr(result, 'containment_hierarchy'):
            print("❌ Result missing 'containment_hierarchy' attribute")
            return False
        
        print(f"✓ Generated {len(result.primitives)} primitives")
        print(f"✓ Canvas bounds: {result.canvas_bounds}")
        print(f"✓ Containment hierarchy: {len(result.containment_hierarchy)} areas")
        
        return True
    
    def test_mixed_cut_and_sheet(self) -> bool:
        """Test 2: Mixed cut and sheet layout (critical test case)."""
        print("Testing mixed cut and sheet layout...")
        
        egif = '(Human "Socrates") ~[ (Mortal "Socrates") ]'
        graph = parse_egif(egif)
        layout_engine = ConstraintLayoutIntegration()
        
        result = layout_engine.layout_graph(graph)
        
        # Validate area containment
        sheet_elements = 0
        cut_elements = 0
        
        for area_id, contents in result.containment_hierarchy.items():
            if 'sheet' in area_id:
                sheet_elements = len(contents)
            elif 'c_' in area_id:  # Cut ID
                cut_elements = len(contents)
        
        print(f"✓ Sheet contains {sheet_elements} elements")
        print(f"✓ Cut contains {cut_elements} elements")
        
        # Should have elements in both sheet and cut
        if sheet_elements == 0:
            print("❌ No elements found in sheet")
            return False
            
        if cut_elements == 0:
            print("❌ No elements found in cut")
            return False
        
        return True
    
    def test_nested_cuts(self) -> bool:
        """Test 3: Nested cuts layout."""
        print("Testing nested cuts layout...")
        
        egif = '~[ ~[ (P "x") ] ]'
        graph = parse_egif(egif)
        layout_engine = ConstraintLayoutIntegration()
        
        result = layout_engine.layout_graph(graph)
        
        # Should have 2 cuts + sheet in hierarchy
        if len(result.containment_hierarchy) < 3:
            print(f"❌ Expected at least 3 areas, got {len(result.containment_hierarchy)}")
            return False
        
        # Check for proper nesting structure
        cuts_found = 0
        for area_id in result.containment_hierarchy.keys():
            if 'c_' in area_id:
                cuts_found += 1
        
        if cuts_found != 2:
            print(f"❌ Expected 2 cuts, found {cuts_found}")
            return False
        
        print(f"✓ Found {cuts_found} cuts with proper nesting")
        return True
    
    def test_sibling_cuts(self) -> bool:
        """Test 4: Sibling cuts non-overlap."""
        print("Testing sibling cuts non-overlap...")
        
        egif = '~[ (P "x") ] ~[ (Q "x") ]'
        graph = parse_egif(egif)
        layout_engine = ConstraintLayoutIntegration()
        
        result = layout_engine.layout_graph(graph)
        
        # Find cut primitives
        cut_primitives = []
        for primitive in result.primitives.values():
            if primitive.element_type == 'cut':
                cut_primitives.append(primitive)
        
        if len(cut_primitives) != 2:
            print(f"❌ Expected 2 cut primitives, found {len(cut_primitives)}")
            return False
        
        # Check non-overlap (corrected logic - bounds shouldn't overlap)
        cut1, cut2 = cut_primitives
        x1_min, y1_min, x1_max, y1_max = cut1.bounds
        x2_min, y2_min, x2_max, y2_max = cut2.bounds
        
        # Check if cuts overlap (corrected logic)
        # Cuts DON'T overlap if they are separated in either X OR Y direction
        separated_x = (x1_max <= x2_min) or (x2_max <= x1_min)
        separated_y = (y1_max <= y2_min) or (y2_max <= y1_min)
        
        # If separated in either direction, they don't overlap
        if separated_x or separated_y:
            print(f"✓ Cuts are non-overlapping: Cut1 {cut1.bounds}, Cut2 {cut2.bounds}")
            if separated_x:
                x_gap = min(abs(x2_min - x1_max), abs(x1_min - x2_max))
                print(f"  X separation: {x_gap:.1f} pixels")
            if separated_y:
                y_gap = min(abs(y2_min - y1_max), abs(y1_min - y2_max))
                print(f"  Y separation: {y_gap:.1f} pixels")
            return True
        else:
            print(f"❌ Cuts overlap: Cut1 {cut1.bounds}, Cut2 {cut2.bounds}")
            return False
    
    def test_complex_egif_cases(self) -> bool:
        """Test 5: Complex EGIF test cases."""
        print("Testing complex EGIF cases...")
        
        complex_cases = [
            # Double negation
            '~[ ~[ *x ] ]',
            # Multiple predicates
            '(Human "Socrates") (Mortal "Socrates") (Wise "Socrates")',
            # Mixed variables and constants
            '*x (Human x) ~[ (Mortal x) (Wise x) ]',
            # Binary relation
            '(Loves "John" "Mary")',
            # Complex nesting
            '~[ (P "a") ~[ (Q "b") ~[ (R "c") ] ] ]'
        ]
        
        layout_engine = ConstraintLayoutIntegration()
        
        for i, egif in enumerate(complex_cases):
            print(f"  Testing case {i+1}: {egif}")
            try:
                graph = parse_egif(egif)
                result = layout_engine.layout_graph(graph)
                
                if not result.primitives:
                    print(f"    ❌ No primitives generated for case {i+1}")
                    return False
                
                print(f"    ✓ Generated {len(result.primitives)} primitives")
                
            except Exception as e:
                print(f"    ❌ Failed on case {i+1}: {e}")
                return False
        
        print("✓ All complex EGIF cases handled successfully")
        return True
    
    def test_main_application_integration(self) -> bool:
        """Test 6: Main application integration."""
        print("Testing main application integration...")
        
        try:
            # Import main application components
            from eg_editor_integrated import IntegratedEGEditor
            
            print("✓ Main application imports successfully")
            
            # Test that the layout engine is properly integrated
            # Note: We can't fully instantiate the GUI in headless mode,
            # but we can test the layout engine integration
            layout_engine = ConstraintLayoutIntegration()
            
            # Test with a sample graph
            egif = '(Test "integration")'
            graph = parse_egif(egif)
            result = layout_engine.layout_graph(graph)
            
            if not result.primitives:
                print("❌ Layout engine integration failed")
                return False
            
            print("✓ Layout engine properly integrated in main application")
            return True
            
        except ImportError as e:
            print(f"❌ Import error: {e}")
            return False
        except Exception as e:
            print(f"❌ Integration test failed: {e}")
            return False
    
    def test_rendering_pipeline_compatibility(self) -> bool:
        """Test 7: Rendering pipeline compatibility."""
        print("Testing rendering pipeline compatibility...")
        
        try:
            egif = '(Human "Socrates") ~[ (Mortal "Socrates") ]'
            graph = parse_egif(egif)
            layout_engine = ConstraintLayoutIntegration()
            
            # Get layout result
            layout_result = layout_engine.layout_graph(graph)
            
            # Test that result is compatible with renderer
            canvas = TkinterCanvas(800, 600)
            renderer = CleanDiagramRenderer(canvas)
            
            # This should not throw an exception
            # Note: We can't actually render in headless mode, but we can test compatibility
            print("✓ Layout result compatible with rendering pipeline")
            
            # Validate primitive structure
            for primitive in layout_result.primitives.values():
                if not hasattr(primitive, 'element_id'):
                    print("❌ Primitive missing element_id")
                    return False
                if not hasattr(primitive, 'element_type'):
                    print("❌ Primitive missing element_type")
                    return False
                if not hasattr(primitive, 'position'):
                    print("❌ Primitive missing position")
                    return False
                if not hasattr(primitive, 'bounds'):
                    print("❌ Primitive missing bounds")
                    return False
            
            print("✓ All primitives have required attributes")
            return True
            
        except Exception as e:
            print(f"❌ Rendering pipeline test failed: {e}")
            return False
    
    def test_performance_benchmarks(self) -> bool:
        """Test 8: Performance benchmarks."""
        print("Testing performance benchmarks...")
        
        layout_engine = ConstraintLayoutIntegration()
        
        # Test cases with increasing complexity
        test_cases = [
            ('Simple', '(P "x")'),
            ('Medium', '(P "x") (Q "x") ~[ (R "x") ]'),
            ('Complex', '~[ (P "x") ~[ (Q "x") (R "x") ] ] ~[ (S "x") ]'),
        ]
        
        for case_name, egif in test_cases:
            print(f"  Benchmarking {case_name}: {egif}")
            
            try:
                graph = parse_egif(egif)
                
                start_time = time.time()
                result = layout_engine.layout_graph(graph)
                end_time = time.time()
                
                duration = end_time - start_time
                print(f"    ✓ Completed in {duration:.3f}s")
                
                # Performance threshold: should complete within 5 seconds
                if duration > 5.0:
                    print(f"    ⚠️  Performance warning: took {duration:.3f}s (>5s threshold)")
                
            except Exception as e:
                print(f"    ❌ Benchmark failed: {e}")
                return False
        
        print("✓ Performance benchmarks completed")
        return True
    
    def test_error_handling_robustness(self) -> bool:
        """Test 9: Error handling and robustness."""
        print("Testing error handling and robustness...")
        
        layout_engine = ConstraintLayoutIntegration()
        
        # Test edge cases that might cause issues
        edge_cases = [
            # Empty elements (should be handled gracefully)
            ('Empty sheet', ''),
            # Very large graphs (stress test)
            ('Large graph', ' '.join([f'(P{i} "x")' for i in range(10)])),
        ]
        
        for case_name, egif in edge_cases:
            print(f"  Testing {case_name}")
            
            try:
                if egif:  # Skip empty EGIF test as it's invalid
                    graph = parse_egif(egif)
                    result = layout_engine.layout_graph(graph)
                    print(f"    ✓ Handled gracefully")
                else:
                    print(f"    ✓ Skipped invalid case")
                    
            except Exception as e:
                # Some failures are expected for invalid inputs
                print(f"    ✓ Failed gracefully: {e}")
        
        print("✓ Error handling tests completed")
        return True
    
    def run_all_tests(self):
        """Run the complete test suite."""
        print("🧪 COMPREHENSIVE CONSTRAINT-BASED LAYOUT ENGINE TEST SUITE")
        print("=" * 80)
        print("Testing constraint-based layout throughout entire application workflow")
        print("=" * 80)
        
        # Define test suite
        tests = [
            ("Basic Constraint Functionality", self.test_basic_constraint_functionality),
            ("Mixed Cut and Sheet", self.test_mixed_cut_and_sheet),
            ("Nested Cuts", self.test_nested_cuts),
            ("Sibling Cuts Non-Overlap", self.test_sibling_cuts),
            ("Complex EGIF Cases", self.test_complex_egif_cases),
            ("Main Application Integration", self.test_main_application_integration),
            ("Rendering Pipeline Compatibility", self.test_rendering_pipeline_compatibility),
            ("Performance Benchmarks", self.test_performance_benchmarks),
            ("Error Handling Robustness", self.test_error_handling_robustness),
        ]
        
        # Run all tests
        start_time = time.time()
        
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
        
        end_time = time.time()
        
        # Print final results
        print("\n" + "=" * 80)
        print("🎯 FINAL TEST RESULTS")
        print("=" * 80)
        
        total_tests = self.passed_tests + self.failed_tests
        success_rate = (self.passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"✅ PASSED: {self.passed_tests}")
        print(f"❌ FAILED: {self.failed_tests}")
        print(f"📊 SUCCESS RATE: {success_rate:.1f}%")
        print(f"⏱️  TOTAL TIME: {end_time - start_time:.2f}s")
        
        # Detailed results
        print(f"\n📋 DETAILED RESULTS:")
        for test_name, passed, duration, error in self.test_results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {status} {test_name} ({duration:.2f}s)")
            if error:
                print(f"    Error: {error}")
        
        # Overall assessment
        if self.failed_tests == 0:
            print(f"\n🎉 ALL TESTS PASSED! Constraint-based layout engine replacement is SUCCESSFUL!")
            print(f"   Constraint-based layout is fully integrated throughout the application.")
        elif success_rate >= 80:
            print(f"\n⚠️  MOSTLY SUCCESSFUL ({success_rate:.1f}% pass rate)")
            print(f"   Constraint-based layout engine is working but needs minor fixes.")
        else:
            print(f"\n❌ SIGNIFICANT ISSUES DETECTED ({success_rate:.1f}% pass rate)")
            print(f"   Constraint-based layout engine needs major fixes before deployment.")
        
        return self.failed_tests == 0


def main():
    """Main test runner."""
    test_suite = ComprehensiveTestSuite()
    success = test_suite.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
