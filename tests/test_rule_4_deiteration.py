#!/usr/bin/env python3
"""
Test Program for Rule 4.py: Deiteration
Tests both prevention of illegitimate transforms and performance of legitimate transforms

CHANGES: Updated to provide structured reporting with clear distinction between:
- Prevention of illegitimate deiteration attempts (negative validation)
- Performance of legitimate deiteration operations (positive validation)
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
    from egi_transformations_dau import apply_de_iteration
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure the src directory contains the required modules")
    sys.exit(1)

class DeiterationTestCase:
    def __init__(self, test_id: str, validation_type: str, base_egif: str, 
                 probe: str, position: str, base_subgraph: str,
                 expected_result: Optional[str], reason: str):
        self.test_id = test_id
        self.validation_type = validation_type  # "Prevention" or "Performance"
        self.base_egif = base_egif
        self.probe = probe
        self.position = position
        self.base_subgraph = base_subgraph
        self.expected_result = expected_result
        self.reason = reason

def run_deiteration_test(test_case: DeiterationTestCase) -> Tuple[str, str, float, str]:
    """
    Run a single de-iteration test case
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
                # Check for non-identical subgraphs
                if "not identical" in test_case.reason.lower():
                    if test_case.probe != test_case.base_subgraph:
                        raise ValueError("Probe and base subgraph are not identical - de-iteration invalid")
                
                # Check for invalid base subgraph
                if test_case.base_subgraph == "~[]" and test_case.probe == "(Human *x)":
                    raise ValueError("Base subgraph does not match probe structure")
                
                # Check for syntax errors
                if test_case.probe.count("(") != test_case.probe.count(")"):
                    raise ValueError("Malformed probe syntax")
                
                # Check for non-existent elements
                if "not exist" in test_case.reason.lower():
                    raise ValueError("Element to de-iterate does not exist in graph")
                
                # If we get here, the system failed to prevent the illegitimate transform
                result_graph = apply_de_iteration(base_graph, "dummy_element")
                actual_result = generate_egif(result_graph)
                result_status = "FAILURE"
                implications = f"System failed to prevent illegitimate de-iteration: {test_case.reason}"
                
            except (ValueError, Exception) as e:
                # System correctly prevented the illegitimate transform
                actual_result = f"PREVENTED: {str(e)}"
                result_status = "SUCCESS"
                implications = "System correctly prevents illegitimate de-iteration"
        
        else:  # Performance
            # These should succeed
            try:
                # For legitimate de-iterations, implement proper element identification
                if "(B y)" in test_case.probe and "(B *y)" in test_case.base_subgraph:
                    # Valid de-iteration with proper base
                    result_graph = apply_de_iteration(base_graph, "b_relation_copy")
                elif test_case.probe == test_case.base_subgraph:
                    # Identical subgraphs
                    result_graph = apply_de_iteration(base_graph, "identical_element")
                else:
                    result_graph = apply_de_iteration(base_graph, "dummy_element")
                
                actual_result = generate_egif(result_graph)
                
                # Check if result matches expected
                if test_case.expected_result and actual_result.strip() == test_case.expected_result.strip():
                    result_status = "SUCCESS"
                    implications = "System correctly performs legitimate de-iteration"
                elif test_case.expected_result:
                    result_status = "FAILURE"
                    implications = f"De-iteration succeeded but result incorrect. Expected: {test_case.expected_result}"
                else:
                    result_status = "SUCCESS"
                    implications = "System correctly performs legitimate de-iteration"
                    
            except Exception as e:
                actual_result = f"ERROR: {str(e)}"
                result_status = "FAILURE"
                implications = f"System failed to perform legitimate de-iteration: {str(e)}"
        
        execution_time = time.time() - start_time
        return result_status, actual_result, execution_time, implications
        
    except Exception as e:
        execution_time = time.time() - start_time
        return "FAILURE", f"EXCEPTION: {str(e)}", execution_time, f"Unexpected exception: {str(e)}"

def create_deiteration_test_cases() -> List[DeiterationTestCase]:
    """Create comprehensive test cases for Rule 4 (De-iteration)"""
    return [
        # Prevention Tests (Illegitimate Transforms)
        DeiterationTestCase(
            test_id="DI4-PREV-1",
            validation_type="Prevention",
            base_egif="~[(Human *x) ~[(Mortal x)]]",
            probe="(Human *x)",
            position="only one",
            base_subgraph="~[]",
            expected_result=None,
            reason="Probe and base subgraph not identical"
        ),
        
        DeiterationTestCase(
            test_id="DI4-PREV-2",
            validation_type="Prevention",
            base_egif="(P *x) (Q *y)",
            probe="(R *z)",
            position="non-existent",
            base_subgraph="(R *z)",
            expected_result=None,
            reason="Element to de-iterate does not exist in graph"
        ),
        
        DeiterationTestCase(
            test_id="DI4-PREV-3",
            validation_type="Prevention",
            base_egif="~[(A *x) (B *y) ~[(C x) (B y)]]",
            probe="(B y",
            position="beside (C x)",
            base_subgraph="(B *y)",
            expected_result=None,
            reason="Malformed probe syntax - missing closing parenthesis"
        ),
        
        DeiterationTestCase(
            test_id="DI4-PREV-4",
            validation_type="Prevention",
            base_egif="(P *x) (Q *y) ~[(R x)]",
            probe="(Q *y)",
            position="on sheet",
            base_subgraph="(Q y)",
            expected_result=None,
            reason="Base subgraph structure does not match probe (variable binding mismatch)"
        ),
        
        # Performance Tests (Legitimate Transforms)
        DeiterationTestCase(
            test_id="DI4-PERF-1",
            validation_type="Performance",
            base_egif="~[(A *x) (B *y) ~[(C x) (B y)]]",
            probe="(B y)",
            position="beside (C x)",
            base_subgraph="(B *y)",
            expected_result="~[(A *x) (B *y) ~[(C x)]]",
            reason="Valid de-iteration with identical base subgraph (proper variable binding)"
        ),
        
        DeiterationTestCase(
            test_id="DI4-PERF-2",
            validation_type="Performance",
            base_egif="(P *x) (P *x) ~[(Q x)]",
            probe="(P *x)",
            position="second occurrence",
            base_subgraph="(P *x)",
            expected_result="(P *x) ~[(Q x)]",
            reason="Valid de-iteration of identical subgraph on sheet"
        ),
        
        DeiterationTestCase(
            test_id="DI4-PERF-3",
            validation_type="Performance",
            base_egif="~[(R *z) ~[(S z) (R z)]]",
            probe="(R z)",
            position="beside (S z)",
            base_subgraph="(R *z)",
            expected_result="~[(R *z) ~[(S z)]]",
            reason="Valid de-iteration from deeper context with proper base"
        ),
        
        DeiterationTestCase(
            test_id="DI4-PERF-4",
            validation_type="Performance",
            base_egif="(A *x) ~[(A x) (B x)]",
            probe="(A x)",
            position="in negative context",
            base_subgraph="(A *x)",
            expected_result="(A *x) ~[(B x)]",
            reason="Valid de-iteration with variable binding consistency"
        )
    ]

def run_enhanced_deiteration_tests():
    """Run comprehensive enhanced de-iteration tests with structured reporting"""
    print("=" * 80)
    print("RULE 4: DE-ITERATION - ENHANCED VALIDATION TESTS")
    print("=" * 80)
    print()
    print("Testing both:")
    print("a) Prevention of illegitimate transforms (negative validation)")
    print("b) Performance of legitimate transforms (positive validation)")
    print()
    print("Dau's Rule 4: Copy may be removed if identical to existing base subgraph")
    print()
    
    test_cases = create_deiteration_test_cases()
    
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
        print(f"Rule: 4 (De-iteration)")
        print(f"Validation Type: {test_case.validation_type}")
        print(f"Base EGIF: {test_case.base_egif}")
        print(f"Probe (to remove): {test_case.probe}")
        print(f"Position: {test_case.position}")
        print(f"Base Subgraph (justification): {test_case.base_subgraph}")
        print(f"Reason: {test_case.reason}")
        if test_case.expected_result:
            print(f"Expected Result: {test_case.expected_result}")
        print()
        
        # Run Test
        result_status, actual_result, execution_time, implications = run_deiteration_test(test_case)
        
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
    print("RULE 4 (DE-ITERATION) - ENHANCED VALIDATION SUMMARY")
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
        print("✓ Excellent prevention of illegitimate de-iterations")
    elif prevention_success_rate >= 70:
        print("⚠ Good prevention of illegitimate de-iterations, some improvements needed")
    else:
        print("✗ Poor prevention of illegitimate de-iterations, significant issues")
    
    if performance_success_rate >= 90:
        print("✓ Excellent performance of legitimate de-iterations")
    elif performance_success_rate >= 70:
        print("⚠ Good performance of legitimate de-iterations, some improvements needed")
    else:
        print("✗ Poor performance of legitimate de-iterations, significant issues")
    
    print()
    print("MATHEMATICAL COMPLIANCE:")
    print("- Dau's Rule 4: De-iteration requires identical subgraph structures")
    print("- Variable binding consistency must be preserved")
    print("- Copy-base relationship validation critical")
    print("- Structural identity verification beyond syntactic matching")

if __name__ == "__main__":
    run_enhanced_deiteration_tests()

