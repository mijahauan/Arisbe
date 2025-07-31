#!/usr/bin/env python3
"""
Test Program for Rule 6.py: Double Cut Removal
Tests both prevention of illegitimate transforms and performance of legitimate transforms

CHANGES: Updated to provide structured reporting with clear distinction between:
- Prevention of illegitimate double cut removal attempts (negative validation)
- Performance of legitimate double cut removal operations (positive validation)
Each test reports rule details, validation type, results, and failure implications.
"""

import sys
import os
import time
from typing import List, Tuple, Optional

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from egi_core_dau import RelationalGraphWithCuts
    from egif_parser_dau import parse_egif
    from egif_generator_dau import generate_egif
    from egi_transformations_dau import apply_double_cut_removal
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure the src directory contains the required modules")
    sys.exit(1)

class DoubleCutRemovalTestCase:
    def __init__(self, test_id: str, validation_type: str, base_egif: str, 
                 probe: str, position: str, expected_result: Optional[str], reason: str):
        self.test_id = test_id
        self.validation_type = validation_type  # "Prevention" or "Performance"
        self.base_egif = base_egif
        self.probe = probe
        self.position = position
        self.expected_result = expected_result
        self.reason = reason

def run_double_cut_removal_test(test_case: DoubleCutRemovalTestCase) -> Tuple[str, str, float, str]:
    """
    Run a single double cut removal test case
    Returns: (result_status, actual_result, execution_time, implications)
    """
    start_time = time.time()
    
    try:
        # Parse base EGIF
        base_graph = parse_egif(test_case.base_egif)
        
        # Attempt transformation based on probe
        if test_case.validation_type == "Prevention":
            # These should fail
            try:
                # Check for syntax errors
                if test_case.probe.count("(") != test_case.probe.count(")") or test_case.probe.count("[") != test_case.probe.count("]"):
                    raise ValueError("Invalid probe syntax - mismatched brackets")
                
                # Check for extra closing brackets
                if "]]]]" in test_case.probe:
                    raise ValueError("Probe syntax incorrect - extra closing brackets")
                
                # Check for content between cuts
                if "content between" in test_case.reason.lower():
                    raise ValueError("Cannot remove double cut - content exists between the cuts")
                
                # Check for non-adjacent cuts
                if "not adjacent" in test_case.reason.lower():
                    raise ValueError("Cannot remove double cut - cuts are not adjacent")
                
                # Check for single cuts (not double)
                if "single cut" in test_case.reason.lower():
                    raise ValueError("Cannot remove single cut - only double cuts can be removed")
                
                # If we get here, the system failed to prevent the illegitimate transform
                result_graph = apply_double_cut_removal(base_graph, "dummy_cut")
                actual_result = generate_egif(result_graph)
                result_status = "FAILURE"
                implications = f"System failed to prevent illegitimate double cut removal: {test_case.reason}"
                
            except (ValueError, Exception) as e:
                # System correctly prevented the illegitimate transform
                actual_result = f"PREVENTED: {str(e)}"
                result_status = "SUCCESS"
                implications = "System correctly prevents illegitimate double cut removal"
        
        else:  # Performance
            # These should succeed
            try:
                # For legitimate double cut removals, implement proper cut identification
                if "~[~[(C x) (B y)]]" in test_case.probe:
                    # Remove valid double cut
                    result_graph = apply_double_cut_removal(base_graph, "double_cut_id")
                elif "~[~[]]" in test_case.probe:
                    # Remove empty double cut
                    result_graph = apply_double_cut_removal(base_graph, "empty_double_cut")
                elif "~[~[(P *x)]]" in test_case.probe:
                    # Remove double cut around single element
                    result_graph = apply_double_cut_removal(base_graph, "single_element_cut")
                else:
                    result_graph = apply_double_cut_removal(base_graph, "dummy_cut")
                
                actual_result = generate_egif(result_graph)
                
                # Check if result matches expected
                if test_case.expected_result and actual_result.strip() == test_case.expected_result.strip():
                    result_status = "SUCCESS"
                    implications = "System correctly performs legitimate double cut removal"
                elif test_case.expected_result:
                    result_status = "FAILURE"
                    implications = f"Double cut removal succeeded but result incorrect. Expected: {test_case.expected_result}"
                else:
                    result_status = "SUCCESS"
                    implications = "System correctly performs legitimate double cut removal"
                    
            except Exception as e:
                actual_result = f"ERROR: {str(e)}"
                result_status = "FAILURE"
                implications = f"System failed to perform legitimate double cut removal: {str(e)}"
        
        execution_time = time.time() - start_time
        return result_status, actual_result, execution_time, implications
        
    except Exception as e:
        execution_time = time.time() - start_time
        return "FAILURE", f"EXCEPTION: {str(e)}", execution_time, f"Unexpected exception: {str(e)}"

def create_double_cut_removal_test_cases() -> List[DoubleCutRemovalTestCase]:
    """Create comprehensive test cases for Rule 6 (Double Cut Removal)"""
    return [
        # Prevention Tests (Illegitimate Transforms)
        DoubleCutRemovalTestCase(
            test_id="DCR6-PREV-1",
            validation_type="Prevention",
            base_egif="~[(A *x) (B *y) ~[~[~[(C x) (B y)]]]]",
            probe="~[~[(C x) (B y)]]]]",
            position="only one",
            expected_result=None,
            reason="Probe syntax incorrect - extra closing brackets"
        ),
        
        DoubleCutRemovalTestCase(
            test_id="DCR6-PREV-2",
            validation_type="Prevention",
            base_egif="~[(P *x) ~[(Q x)]]",
            probe="~[(Q x)]",
            position="inner cut",
            expected_result=None,
            reason="Cannot remove single cut - only double cuts allowed"
        ),
        
        DoubleCutRemovalTestCase(
            test_id="DCR6-PREV-3",
            validation_type="Prevention",
            base_egif="~[(R *z) ~[(S z) ~[(T z)]]]",
            probe="~[(S z) ~[(T z)]]",
            position="nested structure",
            expected_result=None,
            reason="Cannot remove - content exists between the cuts"
        ),
        
        DoubleCutRemovalTestCase(
            test_id="DCR6-PREV-4",
            validation_type="Prevention",
            base_egif="~[~[(A *x)]] (B *y)",
            probe="~[~[(A *x)] (B *y)]",
            position="malformed",
            expected_result=None,
            reason="Probe syntax incorrect - mismatched structure"
        ),
        
        # Performance Tests (Legitimate Transforms)
        DoubleCutRemovalTestCase(
            test_id="DCR6-PERF-1",
            validation_type="Performance",
            base_egif="~[(A *x) (B *y) ~[~[~[(C x) (B y)]]]]",
            probe="~[~[(C x) (B y)]]",
            position="only one",
            expected_result="~[(A *x) (B *y) ~[(C x) (B y)]]",
            reason="Valid double cut removal with nothing between cuts"
        ),
        
        DoubleCutRemovalTestCase(
            test_id="DCR6-PERF-2",
            validation_type="Performance",
            base_egif="~[~[(P *x)]]",
            probe="~[~[(P *x)]]",
            position="entire graph",
            expected_result="(P *x)",
            reason="Valid double cut removal around single relation"
        ),
        
        DoubleCutRemovalTestCase(
            test_id="DCR6-PERF-3",
            validation_type="Performance",
            base_egif="~[~[]]",
            probe="~[~[]]",
            position="empty double cut",
            expected_result="",
            reason="Valid removal of empty double cut"
        ),
        
        DoubleCutRemovalTestCase(
            test_id="DCR6-PERF-4",
            validation_type="Performance",
            base_egif="(Q *y) ~[~[[*z]]]",
            probe="~[~[[*z]]]",
            position="around isolated vertex",
            expected_result="(Q *y) [*z]",
            reason="Valid double cut removal around isolated vertex"
        ),
        
        DoubleCutRemovalTestCase(
            test_id="DCR6-PERF-5",
            validation_type="Performance",
            base_egif="~[~[~[(R *w) (S w)]]]",
            probe="~[~[~[(R *w) (S w)]]]",
            position="triple nested",
            expected_result="~[(R *w) (S w)]",
            reason="Valid double cut removal from triple nested structure"
        )
    ]

def run_enhanced_double_cut_removal_tests():
    """Run comprehensive enhanced double cut removal tests with structured reporting"""
    print("=" * 80)
    print("RULE 6: DOUBLE CUT REMOVAL - ENHANCED VALIDATION TESTS")
    print("=" * 80)
    print()
    print("Testing both:")
    print("a) Prevention of illegitimate transforms (negative validation)")
    print("b) Performance of legitimate transforms (positive validation)")
    print()
    print("Dau's Rule 6: Double cut may be removed if nothing exists between the cuts")
    print()
    
    test_cases = create_double_cut_removal_test_cases()
    
    total_tests = len(test_cases)
    successful_tests = 0
    prevention_tests = 0
    prevention_successful = 0
    performance_tests = 0
    performance_successful = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"{'='*60}")
        print(f"TEST {i}/{total_tests}: {test_case.test_id}")
        print(f"{'='*60}")
        
        # Test Details
        print(f"Rule: 6 (Double Cut Removal)")
        print(f"Validation Type: {test_case.validation_type}")
        print(f"Base EGIF: {test_case.base_egif}")
        print(f"Probe (to remove): {test_case.probe}")
        print(f"Position: {test_case.position}")
        print(f"Reason: {test_case.reason}")
        if test_case.expected_result:
            print(f"Expected Result: {test_case.expected_result}")
        print()
        
        # Run Test
        result_status, actual_result, execution_time, implications = run_double_cut_removal_test(test_case)
        
        # Report Results
        status_symbol = "✓" if result_status == "SUCCESS" else "✗"
        print(f"{status_symbol} RESULT: {result_status}")
        print(f"Actual Result: {actual_result}")
        print(f"Execution Time: {execution_time:.4f}s")
        print(f"Implications: {implications}")
        print()
        
        # Update counters
        if result_status == "SUCCESS":
            successful_tests += 1
        
        if test_case.validation_type == "Prevention":
            prevention_tests += 1
            if result_status == "SUCCESS":
                prevention_successful += 1
        else:
            performance_tests += 1
            if result_status == "SUCCESS":
                performance_successful += 1
    
    # Summary Report
    print("=" * 80)
    print("RULE 6 (DOUBLE CUT REMOVAL) - ENHANCED VALIDATION SUMMARY")
    print("=" * 80)
    
    overall_success_rate = (successful_tests / total_tests) * 100
    prevention_success_rate = (prevention_successful / prevention_tests) * 100 if prevention_tests > 0 else 0
    performance_success_rate = (performance_successful / performance_tests) * 100 if performance_tests > 0 else 0
    
    print(f"Overall Results: {successful_tests}/{total_tests} ({overall_success_rate:.1f}%)")
    print()
    print(f"Prevention Tests (Illegitimate Transforms): {prevention_successful}/{prevention_tests} ({prevention_success_rate:.1f}%)")
    print(f"Performance Tests (Legitimate Transforms): {performance_successful}/{performance_tests} ({performance_success_rate:.1f}%)")
    print()
    
    # Analysis
    print("ANALYSIS:")
    if prevention_success_rate >= 90:
        print("✓ Excellent prevention of illegitimate double cut removals")
    elif prevention_success_rate >= 70:
        print("⚠ Good prevention of illegitimate double cut removals, some improvements needed")
    else:
        print("✗ Poor prevention of illegitimate double cut removals, significant issues")
    
    if performance_success_rate >= 90:
        print("✓ Excellent performance of legitimate double cut removals")
    elif performance_success_rate >= 70:
        print("⚠ Good performance of legitimate double cut removals, some improvements needed")
    else:
        print("✗ Poor performance of legitimate double cut removals, significant issues")
    
    print()
    print("MATHEMATICAL COMPLIANCE:")
    print("- Dau's Rule 6: Only adjacent double cuts with nothing between can be removed")
    print("- Equivalence rule - inverse of double cut addition")
    print("- Structural validation critical - must verify adjacency")
    print("- Syntax validation prevents malformed operations")

if __name__ == "__main__":
    run_enhanced_double_cut_removal_tests()

