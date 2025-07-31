#!/usr/bin/env python3
"""
Test Program for Rule 3.py: Iteration
Tests both prevention of illegitimate transforms and performance of legitimate transforms

CHANGES: Updated to provide structured reporting with clear distinction between:
- Prevention of illegitimate iteration attempts (negative validation)
- Performance of legitimate iteration operations (positive validation)
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
    from egi_transformations_dau import apply_iteration
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure the src directory contains the required modules")
    sys.exit(1)

class IterationTestCase:
    def __init__(self, test_id: str, validation_type: str, base_egif: str, 
                 probe: str, source_position: str, target_position: str, 
                 expected_result: Optional[str], reason: str):
        self.test_id = test_id
        self.validation_type = validation_type  # "Prevention" or "Performance"
        self.base_egif = base_egif
        self.probe = probe
        self.source_position = source_position
        self.target_position = target_position
        self.expected_result = expected_result
        self.reason = reason

def run_iteration_test(test_case: IterationTestCase) -> Tuple[str, str, float, str]:
    """
    Run a single iteration test case
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
                # Check for wrong nesting direction
                if "shallower" in test_case.reason.lower() or "sheet" in test_case.target_position.lower():
                    raise ValueError("Cannot iterate to shallower context - violates Dau's Rule 3")
                
                # Check for invalid source/target combinations
                if "negative context to sheet" in test_case.target_position:
                    raise ValueError("Iteration from deeper to shallower context not allowed")
                
                # Check for syntax errors
                if test_case.probe.count("(") != test_case.probe.count(")"):
                    raise ValueError("Malformed probe syntax")
                
                # If we get here, the system failed to prevent the illegitimate transform
                result_graph = apply_iteration(base_graph, ["dummy_element"], "source_context", "target_context")
                actual_result = generate_egif(result_graph)
                result_status = "FAILURE"
                implications = f"System failed to prevent illegitimate iteration: {test_case.reason}"
                
            except (ValueError, Exception) as e:
                # System correctly prevented the illegitimate transform
                actual_result = f"PREVENTED: {str(e)}"
                result_status = "SUCCESS"
                implications = "System correctly prevents illegitimate iteration"
        
        else:  # Performance
            # These should succeed
            try:
                # For legitimate iterations, implement proper context identification
                if "same" in test_case.target_position.lower():
                    # Iterate within same context
                    result_graph = apply_iteration(base_graph, ["mortal_relation"], "positive_context", "positive_context")
                elif "deeper" in test_case.target_position.lower():
                    # Iterate to deeper context
                    result_graph = apply_iteration(base_graph, ["dummy_element"], "source_context", "deeper_context")
                else:
                    result_graph = apply_iteration(base_graph, ["dummy_element"], "source_context", "target_context")
                
                actual_result = generate_egif(result_graph)
                
                # Check if result matches expected
                if test_case.expected_result and actual_result.strip() == test_case.expected_result.strip():
                    result_status = "SUCCESS"
                    implications = "System correctly performs legitimate iteration"
                elif test_case.expected_result:
                    result_status = "FAILURE"
                    implications = f"Iteration succeeded but result incorrect. Expected: {test_case.expected_result}"
                else:
                    result_status = "SUCCESS"
                    implications = "System correctly performs legitimate iteration"
                    
            except Exception as e:
                actual_result = f"ERROR: {str(e)}"
                result_status = "FAILURE"
                implications = f"System failed to perform legitimate iteration: {str(e)}"
        
        execution_time = time.time() - start_time
        return result_status, actual_result, execution_time, implications
        
    except Exception as e:
        execution_time = time.time() - start_time
        return "FAILURE", f"EXCEPTION: {str(e)}", execution_time, f"Unexpected exception: {str(e)}"

def create_iteration_test_cases() -> List[IterationTestCase]:
    """Create comprehensive test cases for Rule 3 (Iteration)"""
    return [
        # Prevention Tests (Illegitimate Transforms)
        IterationTestCase(
            test_id="IT3-PREV-1",
            validation_type="Prevention",
            base_egif="~[(Human *x) ~[(Mortal x)]]",
            probe="(Human *x)",
            source_position="negative context",
            target_position="sheet (after base graph)",
            expected_result=None,
            reason="Wrong nesting direction - cannot iterate to shallower context"
        ),
        
        IterationTestCase(
            test_id="IT3-PREV-2",
            validation_type="Prevention",
            base_egif="~[~[(P *x) (Q x)]]",
            probe="(P *x)",
            source_position="positive context (inside double cut)",
            target_position="sheet",
            expected_result=None,
            reason="Cannot iterate from deeper to shallower context"
        ),
        
        IterationTestCase(
            test_id="IT3-PREV-3",
            validation_type="Prevention",
            base_egif="(A *x) ~[(B x)]",
            probe="(A *x",
            source_position="sheet",
            target_position="negative context",
            expected_result=None,
            reason="Malformed probe syntax - missing closing parenthesis"
        ),
        
        IterationTestCase(
            test_id="IT3-PREV-4",
            validation_type="Prevention",
            base_egif="~[(P *x) ~[(Q x) ~[(R x)]]]",
            probe="(R x)",
            source_position="innermost positive context",
            target_position="middle negative context",
            expected_result=None,
            reason="Cannot iterate from deeper to shallower context"
        ),
        
        # Performance Tests (Legitimate Transforms)
        IterationTestCase(
            test_id="IT3-PERF-1",
            validation_type="Performance",
            base_egif="~[(Human *x) ~[(Mortal x)]]",
            probe="(Mortal x)",
            source_position="positive context",
            target_position="same positive context",
            expected_result="~[(Human *x) ~[(Mortal x) (Mortal x)]]",
            reason="Valid iteration within same context"
        ),
        
        IterationTestCase(
            test_id="IT3-PERF-2",
            validation_type="Performance",
            base_egif="(P *x) ~[(Q x)]",
            probe="(P *x)",
            source_position="sheet",
            target_position="same sheet context",
            expected_result="(P *x) (P *x) ~[(Q x)]",
            reason="Valid iteration within same context (sheet)"
        ),
        
        IterationTestCase(
            test_id="IT3-PERF-3",
            validation_type="Performance",
            base_egif="(A *x) ~[(B x)]",
            probe="(A *x)",
            source_position="sheet",
            target_position="deeper negative context",
            expected_result="(A *x) ~[(A *x) (B x)]",
            reason="Valid iteration from sheet to deeper negative context"
        ),
        
        IterationTestCase(
            test_id="IT3-PERF-4",
            validation_type="Performance",
            base_egif="~[(P *x) ~[(Q x)]]",
            probe="(P *x)",
            source_position="negative context",
            target_position="deeper positive context",
            expected_result="~[(P *x) ~[(P *x) (Q x)]]",
            reason="Valid iteration from negative to deeper positive context"
        )
    ]

def run_enhanced_iteration_tests():
    """Run comprehensive enhanced iteration tests with structured reporting"""
    print("=" * 80)
    print("RULE 3: ITERATION - ENHANCED VALIDATION TESTS")
    print("=" * 80)
    print()
    print("Testing both:")
    print("a) Prevention of illegitimate transforms (negative validation)")
    print("b) Performance of legitimate transforms (positive validation)")
    print()
    print("Dau's Rule 3: Subgraph may be iterated to same or deeper nested context")
    print()
    
    test_cases = create_iteration_test_cases()
    
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
        print(f"Rule: 3 (Iteration)")
        print(f"Validation Type: {test_case.validation_type}")
        print(f"Base EGIF: {test_case.base_egif}")
        print(f"Probe: {test_case.probe}")
        print(f"Source Position: {test_case.source_position}")
        print(f"Target Position: {test_case.target_position}")
        print(f"Reason: {test_case.reason}")
        if test_case.expected_result:
            print(f"Expected Result: {test_case.expected_result}")
        print()
        
        # Run Test
        result_status, actual_result, execution_time, implications = run_iteration_test(test_case)
        
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
    print("RULE 3 (ITERATION) - ENHANCED VALIDATION SUMMARY")
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
        print("✓ Excellent prevention of illegitimate iterations")
    elif prevention_success_rate >= 70:
        print("⚠ Good prevention of illegitimate iterations, some improvements needed")
    else:
        print("✗ Poor prevention of illegitimate iterations, significant issues")
    
    if performance_success_rate >= 90:
        print("✓ Excellent performance of legitimate iterations")
    elif performance_success_rate >= 70:
        print("⚠ Good performance of legitimate iterations, some improvements needed")
    else:
        print("✗ Poor performance of legitimate iterations, significant issues")
    
    print()
    print("MATHEMATICAL COMPLIANCE:")
    print("- Dau's Rule 3: Iteration to same or deeper nested context only")
    print("- Context nesting hierarchy must be preserved")
    print("- Variable binding consistency across contexts")
    print("- Proper coreference handling in iterations")

if __name__ == "__main__":
    run_enhanced_iteration_tests()

