#!/usr/bin/env python3
"""
Test Program for Rule 1: Erasure
Tests both prevention of illegitimate transforms and performance of legitimate transforms

CHANGES: Updated to use proper element identification and context mapping utilities.
Replaces dummy element IDs with actual graph structure matching and functional
transformation calls that work with the real DAU-compliant implementation.
"""

import sys
import os
import time
from typing import List, Tuple, Optional

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from test_utilities import TransformationTester, run_transformation_test, validate_transformation_constraints
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure the test utilities are available")
    sys.exit(1)

class ErasureTestCase:
    def __init__(self, test_id: str, validation_type: str, base_egif: str, 
                 probe: str, position: str, expected_result: Optional[str], reason: str):
        self.test_id = test_id
        self.validation_type = validation_type  # "Prevention" or "Performance"
        self.base_egif = base_egif
        self.probe = probe
        self.position = position
        self.expected_result = expected_result
        self.reason = reason

def run_erasure_test(test_case: ErasureTestCase) -> Tuple[str, str, float, str]:
    """
    Run a single erasure test case using the new utilities.
    Returns: (result_status, actual_result, execution_time, implications)
    """
    start_time = time.time()
    
    try:
        if test_case.validation_type == "Prevention":
            # These should fail - first check constraints
            is_valid, constraint_reason = validate_transformation_constraints(
                "erasure", test_case.base_egif, test_case.probe, test_case.position
            )
            
            if not is_valid:
                # System correctly prevented the illegitimate transform
                actual_result = f"PREVENTED: {constraint_reason}"
                result_status = "SUCCESS"
                implications = "System correctly prevents illegitimate erasure"
            else:
                # Try the transformation - it should still fail for other reasons
                success, result_desc, result_egif = run_transformation_test(
                    "erasure", test_case.base_egif, test_case.probe, test_case.position
                )
                
                if not success:
                    actual_result = f"PREVENTED: {result_desc}"
                    result_status = "SUCCESS"
                    implications = "System correctly prevents illegitimate erasure"
                else:
                    # System failed to prevent illegitimate transform
                    actual_result = result_egif or "Transformation succeeded unexpectedly"
                    result_status = "FAILURE"
                    implications = f"System failed to prevent illegitimate erasure: {test_case.reason}"
        
        else:  # Performance
            # These should succeed
            success, result_desc, result_egif = run_transformation_test(
                "erasure", test_case.base_egif, test_case.probe, test_case.position
            )
            
            if success:
                actual_result = result_egif or "Transformation succeeded"
                
                # Check if result matches expected
                if test_case.expected_result and result_egif:
                    if result_egif.strip() == test_case.expected_result.strip():
                        result_status = "SUCCESS"
                        implications = "System correctly performs legitimate erasure"
                    else:
                        result_status = "FAILURE"
                        implications = f"Erasure succeeded but result incorrect. Expected: {test_case.expected_result}"
                else:
                    result_status = "SUCCESS"
                    implications = "System correctly performs legitimate erasure"
            else:
                actual_result = f"ERROR: {result_desc}"
                result_status = "FAILURE"
                implications = f"System failed to perform legitimate erasure: {result_desc}"
        
        execution_time = time.time() - start_time
        return result_status, actual_result, execution_time, implications
        
    except Exception as e:
        execution_time = time.time() - start_time
        return "FAILURE", f"EXCEPTION: {str(e)}", execution_time, f"Unexpected exception: {str(e)}"

def create_erasure_test_cases() -> List[ErasureTestCase]:
    """Create comprehensive test cases for Rule 1 (Erasure)"""
    return [
        # Prevention Tests (Illegitimate Transforms)
        ErasureTestCase(
            test_id="E1-PREV-1",
            validation_type="Prevention",
            base_egif="~[(Human *x) ~[(Mortal x)]]",
            probe="(Human *x)",
            position="only one",
            expected_result=None,
            reason="Erasure only allowed in positive contexts"
        ),
        
        ErasureTestCase(
            test_id="E1-PREV-2", 
            validation_type="Prevention",
            base_egif="~[(Human *x) ~[(Mortal x)]]",
            probe="(Huma",
            position="not applicable",
            expected_result=None,
            reason="Probe has invalid syntax"
        ),
        
        ErasureTestCase(
            test_id="E1-PREV-3",
            validation_type="Prevention", 
            base_egif="(P *x) ~[(Q x)]",
            probe="(P *x)",
            position="on sheet",
            expected_result=None,
            reason="Cannot erase defining vertex that has bound occurrences"
        ),
        
        # Performance Tests (Legitimate Transforms)
        ErasureTestCase(
            test_id="E1-PERF-1",
            validation_type="Performance",
            base_egif="~[(Human *x) ~[(Mortal x)]]",
            probe="(Mortal x)",
            position="only one",
            expected_result="~[(Human *x) ~[]]",
            reason="Valid erasure from positive context (inside double cut)"
        ),
        
        ErasureTestCase(
            test_id="E1-PERF-2",
            validation_type="Performance",
            base_egif="~[(Human *x) ~[(Mortal x)]]",
            probe="~[(Human *x) ~[(Mortal x)]]",
            position="entire graph",
            expected_result="",
            reason="Valid complete graph erasure from sheet (positive context)"
        ),
        
        ErasureTestCase(
            test_id="E1-PERF-3",
            validation_type="Performance",
            base_egif="(P *x) (Q *y) ~[(R x y)]",
            probe="(Q *y)",
            position="on sheet",
            expected_result="(P *x) ~[(R x)]",
            reason="Valid erasure of isolated relation from positive context"
        ),
        
        ErasureTestCase(
            test_id="E1-PERF-4",
            validation_type="Performance",
            base_egif="~[~[(P *x)]]",
            probe="(P *x)",
            position="inside double cut",
            expected_result="~[~[]]",
            reason="Valid erasure from positive context created by double cut"
        )
    ]

def run_erasure_tests():
    """Run comprehensive erasure tests with structured reporting"""
    print("=" * 80)
    print("RULE 1: ERASURE - VALIDATION TESTS")
    print("=" * 80)
    print()
    print("Testing both:")
    print("a) Prevention of illegitimate transforms (negative validation)")
    print("b) Performance of legitimate transforms (positive validation)")
    print()
    
    test_cases = create_erasure_test_cases()
    
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
        print(f"Rule: 1 (Erasure)")
        print(f"Validation Type: {test_case.validation_type}")
        print(f"Base EGIF: {test_case.base_egif}")
        print(f"Probe: {test_case.probe}")
        print(f"Position: {test_case.position}")
        print(f"Reason: {test_case.reason}")
        if test_case.expected_result:
            print(f"Expected Result: {test_case.expected_result}")
        print()
        
        # Run Test
        result_status, actual_result, execution_time, implications = run_erasure_test(test_case)
        
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
    print("RULE 1 (ERASURE) - VALIDATION SUMMARY")
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
        print("✓ Excellent prevention of illegitimate erasures")
    elif prevention_success_rate >= 70:
        print("⚠ Good prevention of illegitimate erasures, some improvements needed")
    else:
        print("✗ Poor prevention of illegitimate erasures, significant issues")
    
    if performance_success_rate >= 90:
        print("✓ Excellent performance of legitimate erasures")
    elif performance_success_rate >= 70:
        print("⚠ Good performance of legitimate erasures, some improvements needed")
    else:
        print("✗ Poor performance of legitimate erasures, significant issues")
    
    print()
    print("MATHEMATICAL COMPLIANCE:")
    print("- Dau's Rule 1: Erasure only allowed in positive contexts")
    print("- Context polarity validation critical for correctness")
    print("- Syntax validation prevents malformed operations")
    print("- Variable binding preservation essential")

if __name__ == "__main__":
    run_erasure_tests()

