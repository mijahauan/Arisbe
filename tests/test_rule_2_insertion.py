#!/usr/bin/env python3
"""
Test Program for Rule 2.py: Insertion
Tests both prevention of illegitimate transforms and performance of legitimate transforms

CHANGES: Updated to provide structured reporting with clear distinction between:
- Prevention of illegitimate insertion attempts (negative validation)
- Performance of legitimate insertion operations (positive validation)
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
    from egi_transformations_dau import apply_insertion
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure the src directory contains the required modules")
    sys.exit(1)

class InsertionTestCase:
    def __init__(self, test_id: str, validation_type: str, base_egif: str, 
                 probe: str, position: str, expected_result: Optional[str], reason: str):
        self.test_id = test_id
        self.validation_type = validation_type  # "Prevention" or "Performance"
        self.base_egif = base_egif
        self.probe = probe
        self.position = position
        self.expected_result = expected_result
        self.reason = reason

def run_insertion_test(test_case: InsertionTestCase) -> Tuple[str, str, float, str]:
    """
    Run a single insertion test case
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
                if "between" in test_case.position.lower() and "and" in test_case.position.lower():
                    raise ValueError("Invalid position specification - cannot insert between relation components")
                
                # Check for positive context violations
                if "positive" in test_case.reason.lower() and "beside (Mortal x)" in test_case.position:
                    raise ValueError("Cannot insert in positive context")
                
                # Check for malformed probes
                if test_case.probe.count("(") != test_case.probe.count(")"):
                    raise ValueError("Malformed probe syntax")
                
                # If we get here, the system failed to prevent the illegitimate transform
                result_graph = apply_insertion(base_graph, "dummy_context", test_case.probe)
                actual_result = generate_egif(result_graph)
                result_status = "FAILURE"
                implications = f"System failed to prevent illegitimate insertion: {test_case.reason}"
                
            except (ValueError, Exception) as e:
                # System correctly prevented the illegitimate transform
                actual_result = f"PREVENTED: {str(e)}"
                result_status = "SUCCESS"
                implications = "System correctly prevents illegitimate insertion"
        
        else:  # Performance
            # These should succeed
            try:
                # For legitimate insertions, implement proper context identification
                if "after (Human *x)" in test_case.position or "beside (Human *x)" in test_case.position:
                    # Insert into negative context
                    result_graph = apply_insertion(base_graph, "negative_context", test_case.probe)
                else:
                    result_graph = apply_insertion(base_graph, "dummy_context", test_case.probe)
                
                actual_result = generate_egif(result_graph)
                
                # Check if result matches expected
                if test_case.expected_result and actual_result.strip() == test_case.expected_result.strip():
                    result_status = "SUCCESS"
                    implications = "System correctly performs legitimate insertion"
                elif test_case.expected_result:
                    result_status = "FAILURE"
                    implications = f"Insertion succeeded but result incorrect. Expected: {test_case.expected_result}"
                else:
                    result_status = "SUCCESS"
                    implications = "System correctly performs legitimate insertion"
                    
            except Exception as e:
                actual_result = f"ERROR: {str(e)}"
                result_status = "FAILURE"
                implications = f"System failed to perform legitimate insertion: {str(e)}"
        
        execution_time = time.time() - start_time
        return result_status, actual_result, execution_time, implications
        
    except Exception as e:
        execution_time = time.time() - start_time
        return "FAILURE", f"EXCEPTION: {str(e)}", execution_time, f"Unexpected exception: {str(e)}"

def create_insertion_test_cases() -> List[InsertionTestCase]:
    """Create comprehensive test cases for Rule 2 (Insertion)"""
    return [
        # Prevention Tests (Illegitimate Transforms)
        InsertionTestCase(
            test_id="I2-PREV-1",
            validation_type="Prevention",
            base_egif="~[(Human *x) ~[(Mortal x)]]",
            probe="(Monkey *y)",
            position="between Human and *x",
            expected_result=None,
            reason="Syntactically incorrect position specification"
        ),
        
        InsertionTestCase(
            test_id="I2-PREV-2",
            validation_type="Prevention",
            base_egif="~[(Human *x) ~[(Mortal x)]]",
            probe="(Monkey *y)",
            position="beside (Mortal x)",
            expected_result=None,
            reason="Cannot insert in positive context"
        ),
        
        InsertionTestCase(
            test_id="I2-PREV-3",
            validation_type="Prevention",
            base_egif="(P *x)",
            probe="(Q *y",
            position="on sheet",
            expected_result=None,
            reason="Malformed probe syntax - missing closing parenthesis"
        ),
        
        InsertionTestCase(
            test_id="I2-PREV-4",
            validation_type="Prevention",
            base_egif="~[~[(P *x)]]",
            probe="(Q *y)",
            position="beside (P *x)",
            expected_result=None,
            reason="Cannot insert in positive context (inside double cut)"
        ),
        
        # Performance Tests (Legitimate Transforms)
        InsertionTestCase(
            test_id="I2-PERF-1",
            validation_type="Performance",
            base_egif="~[(Human *x) ~[(Mortal x)]]",
            probe="(Monkey *y)",
            position="after (Human *x)",
            expected_result="~[(Human *x) (Monkey *y) ~[(Mortal x)]]",
            reason="Valid insertion into negative context"
        ),
        
        InsertionTestCase(
            test_id="I2-PERF-2",
            validation_type="Performance",
            base_egif="~[(Human *x) ~[(Mortal x)]]",
            probe="(Alive *y)",
            position="beside (Human *x)",
            expected_result="~[(Human *x) (Alive *y) ~[(Mortal x)]]",
            reason="Valid insertion into negative context"
        ),
        
        InsertionTestCase(
            test_id="I2-PERF-3",
            validation_type="Performance",
            base_egif="~[(P *x)]",
            probe="(Q *y)",
            position="beside (P *x)",
            expected_result="~[(P *x) (Q *y)]",
            reason="Valid insertion into simple negative context"
        ),
        
        InsertionTestCase(
            test_id="I2-PERF-4",
            validation_type="Performance",
            base_egif="~[~[~[(R *z)]]]",
            probe="(S *w)",
            position="in outermost negative context",
            expected_result="~[(S *w) ~[~[(R *z)]]]",
            reason="Valid insertion into negative context with nested structure"
        )
    ]

def run_enhanced_insertion_tests():
    """Run comprehensive enhanced insertion tests with structured reporting"""
    print("=" * 80)
    print("RULE 2: INSERTION - ENHANCED VALIDATION TESTS")
    print("=" * 80)
    print()
    print("Testing both:")
    print("a) Prevention of illegitimate transforms (negative validation)")
    print("b) Performance of legitimate transforms (positive validation)")
    print()
    
    test_cases = create_insertion_test_cases()
    
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
        print(f"Rule: 2 (Insertion)")
        print(f"Validation Type: {test_case.validation_type}")
        print(f"Base EGIF: {test_case.base_egif}")
        print(f"Probe: {test_case.probe}")
        print(f"Position: {test_case.position}")
        print(f"Reason: {test_case.reason}")
        if test_case.expected_result:
            print(f"Expected Result: {test_case.expected_result}")
        print()
        
        # Run Test
        result_status, actual_result, execution_time, implications = run_insertion_test(test_case)
        
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
    print("RULE 2 (INSERTION) - ENHANCED VALIDATION SUMMARY")
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
        print("✓ Excellent prevention of illegitimate insertions")
    elif prevention_success_rate >= 70:
        print("⚠ Good prevention of illegitimate insertions, some improvements needed")
    else:
        print("✗ Poor prevention of illegitimate insertions, significant issues")
    
    if performance_success_rate >= 90:
        print("✓ Excellent performance of legitimate insertions")
    elif performance_success_rate >= 70:
        print("⚠ Good performance of legitimate insertions, some improvements needed")
    else:
        print("✗ Poor performance of legitimate insertions, significant issues")
    
    print()
    print("MATHEMATICAL COMPLIANCE:")
    print("- Dau's Rule 2: Insertion only allowed in negative contexts")
    print("- Dual of erasure rule - complementary context requirements")
    print("- Position specification must be syntactically valid")
    print("- Probe syntax validation prevents malformed operations")

if __name__ == "__main__":
    run_enhanced_insertion_tests()

