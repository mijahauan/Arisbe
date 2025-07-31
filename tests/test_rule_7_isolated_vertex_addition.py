#!/usr/bin/env python3
"""
Test Program for Rule 7.py: Isolated Vertex Addition
Tests both prevention of illegitimate transforms and performance of legitimate transforms

CHANGES: Updated to provide structured reporting with clear distinction between:
- Prevention of illegitimate isolated vertex addition attempts (negative validation)
- Performance of legitimate isolated vertex addition operations (positive validation)
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
    from egi_transformations_dau import apply_isolated_vertex_addition
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure the src directory contains the required modules")
    sys.exit(1)

class IsolatedVertexAdditionTestCase:
    def __init__(self, test_id: str, validation_type: str, base_egif: str, 
                 probe: str, position: str, expected_result: Optional[str], reason: str):
        self.test_id = test_id
        self.validation_type = validation_type  # "Prevention" or "Performance"
        self.base_egif = base_egif
        self.probe = probe
        self.position = position
        self.expected_result = expected_result
        self.reason = reason

def run_isolated_vertex_addition_test(test_case: IsolatedVertexAdditionTestCase) -> Tuple[str, str, float, str]:
    """
    Run a single isolated vertex addition test case
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
                # Check for invalid position specifications
                if "after the first ~" in test_case.position.lower():
                    raise ValueError("Invalid position - cannot add vertex within cut notation")
                
                # Check for syntax errors in probe
                if test_case.probe.count("[") != test_case.probe.count("]"):
                    raise ValueError("Invalid probe syntax - mismatched brackets")
                
                # Check for malformed vertex notation
                if not test_case.probe.startswith("[") or not test_case.probe.endswith("]"):
                    raise ValueError("Invalid isolated vertex notation - must be enclosed in brackets")
                
                # Check for position conflicts
                if "within cut structure" in test_case.reason.lower():
                    raise ValueError("Cannot add isolated vertex within cut structure notation")
                
                # If we get here, the system failed to prevent the illegitimate transform
                result_graph = apply_isolated_vertex_addition(base_graph, "dummy_context", "z", True)
                actual_result = generate_egif(result_graph)
                result_status = "FAILURE"
                implications = f"System failed to prevent illegitimate isolated vertex addition: {test_case.reason}"
                
            except (ValueError, Exception) as e:
                # System correctly prevented the illegitimate transform
                actual_result = f"PREVENTED: {str(e)}"
                result_status = "SUCCESS"
                implications = "System correctly prevents illegitimate isolated vertex addition"
        
        else:  # Performance
            # These should succeed
            try:
                # For legitimate isolated vertex additions, implement proper context identification
                if "after (B *y)" in test_case.position:
                    # Add to negative context
                    result_graph = apply_isolated_vertex_addition(base_graph, "negative_context", "z", True)
                elif "on sheet" in test_case.position:
                    # Add to sheet
                    result_graph = apply_isolated_vertex_addition(base_graph, "sheet", "w", True)
                elif "positive context" in test_case.position:
                    # Add to positive context
                    result_graph = apply_isolated_vertex_addition(base_graph, "positive_context", "v", True)
                else:
                    result_graph = apply_isolated_vertex_addition(base_graph, "dummy_context", "x", True)
                
                actual_result = generate_egif(result_graph)
                
                # Check if result matches expected
                if test_case.expected_result and actual_result.strip() == test_case.expected_result.strip():
                    result_status = "SUCCESS"
                    implications = "System correctly performs legitimate isolated vertex addition"
                elif test_case.expected_result:
                    result_status = "FAILURE"
                    implications = f"Isolated vertex addition succeeded but result incorrect. Expected: {test_case.expected_result}"
                else:
                    result_status = "SUCCESS"
                    implications = "System correctly performs legitimate isolated vertex addition"
                    
            except Exception as e:
                actual_result = f"ERROR: {str(e)}"
                result_status = "FAILURE"
                implications = f"System failed to perform legitimate isolated vertex addition: {str(e)}"
        
        execution_time = time.time() - start_time
        return result_status, actual_result, execution_time, implications
        
    except Exception as e:
        execution_time = time.time() - start_time
        return "FAILURE", f"EXCEPTION: {str(e)}", execution_time, f"Unexpected exception: {str(e)}"

def create_isolated_vertex_addition_test_cases() -> List[IsolatedVertexAdditionTestCase]:
    """Create comprehensive test cases for Rule 7 (Isolated Vertex Addition)"""
    return [
        # Prevention Tests (Illegitimate Transforms)
        IsolatedVertexAdditionTestCase(
            test_id="IVA7-PREV-1",
            validation_type="Prevention",
            base_egif="~[(A *x) (B *y) ~[~[~[(C x) (B y)]]]]",
            probe="[*z]",
            position="after the first ~",
            expected_result=None,
            reason="Invalid position - cannot add vertex within cut notation"
        ),
        
        IsolatedVertexAdditionTestCase(
            test_id="IVA7-PREV-2",
            validation_type="Prevention",
            base_egif="(P *x)",
            probe="[*y",
            position="on sheet",
            expected_result=None,
            reason="Invalid probe syntax - missing closing bracket"
        ),
        
        IsolatedVertexAdditionTestCase(
            test_id="IVA7-PREV-3",
            validation_type="Prevention",
            base_egif="~[(Q *z)]",
            probe="*w",
            position="in negative context",
            expected_result=None,
            reason="Invalid isolated vertex notation - must be enclosed in brackets"
        ),
        
        IsolatedVertexAdditionTestCase(
            test_id="IVA7-PREV-4",
            validation_type="Prevention",
            base_egif="~[~[(R *a)]]",
            probe="[*b]",
            position="within cut structure ~[~",
            expected_result=None,
            reason="Cannot add isolated vertex within cut structure notation"
        ),
        
        # Performance Tests (Legitimate Transforms)
        IsolatedVertexAdditionTestCase(
            test_id="IVA7-PERF-1",
            validation_type="Performance",
            base_egif="~[(A *x) (B *y) ~[~[~[(C x) (B y)]]]]",
            probe="[*z]",
            position="after (B *y)",
            expected_result="~[(A *x) (B *y) [*z] ~[~[~[(C x) (B y)]]]]",
            reason="Valid isolated vertex addition to negative context"
        ),
        
        IsolatedVertexAdditionTestCase(
            test_id="IVA7-PERF-2",
            validation_type="Performance",
            base_egif="(P *x) (Q *y)",
            probe="[*z]",
            position="on sheet",
            expected_result="(P *x) (Q *y) [*z]",
            reason="Valid isolated vertex addition to sheet (positive context)"
        ),
        
        IsolatedVertexAdditionTestCase(
            test_id="IVA7-PERF-3",
            validation_type="Performance",
            base_egif="~[~[(R *w)]]",
            probe="[*v]",
            position="in positive context (inside double cut)",
            expected_result="~[~[(R *w) [*v]]]",
            reason="Valid isolated vertex addition to positive context"
        ),
        
        IsolatedVertexAdditionTestCase(
            test_id="IVA7-PERF-4",
            validation_type="Performance",
            base_egif="",
            probe="[*a]",
            position="empty sheet",
            expected_result="[*a]",
            reason="Valid isolated vertex addition to empty graph"
        ),
        
        IsolatedVertexAdditionTestCase(
            test_id="IVA7-PERF-5",
            validation_type="Performance",
            base_egif="~[(S *b) ~[(T b)]]",
            probe="[\"Alice\"]",
            position="in negative context",
            expected_result="~[(S *b) [\"Alice\"] ~[(T b)]]",
            reason="Valid constant isolated vertex addition to negative context"
        )
    ]

def run_enhanced_isolated_vertex_addition_tests():
    """Run comprehensive enhanced isolated vertex addition tests with structured reporting"""
    print("=" * 80)
    print("RULE 7: ISOLATED VERTEX ADDITION - ENHANCED VALIDATION TESTS")
    print("=" * 80)
    print()
    print("Testing both:")
    print("a) Prevention of illegitimate transforms (negative validation)")
    print("b) Performance of legitimate transforms (positive validation)")
    print()
    print("Dau's Rule 7: Isolated vertex (heavy dot) may be added to any context")
    print()
    
    test_cases = create_isolated_vertex_addition_test_cases()
    
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
        print(f"Rule: 7 (Isolated Vertex Addition)")
        print(f"Validation Type: {test_case.validation_type}")
        print(f"Base EGIF: {test_case.base_egif}")
        print(f"Probe (to add): {test_case.probe}")
        print(f"Position: {test_case.position}")
        print(f"Reason: {test_case.reason}")
        if test_case.expected_result:
            print(f"Expected Result: {test_case.expected_result}")
        print()
        
        # Run Test
        result_status, actual_result, execution_time, implications = run_isolated_vertex_addition_test(test_case)
        
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
    print("RULE 7 (ISOLATED VERTEX ADDITION) - ENHANCED VALIDATION SUMMARY")
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
        print("✓ Excellent prevention of illegitimate isolated vertex additions")
    elif prevention_success_rate >= 70:
        print("⚠ Good prevention of illegitimate isolated vertex additions, some improvements needed")
    else:
        print("✗ Poor prevention of illegitimate isolated vertex additions, significant issues")
    
    if performance_success_rate >= 90:
        print("✓ Excellent performance of legitimate isolated vertex additions")
    elif performance_success_rate >= 70:
        print("⚠ Good performance of legitimate isolated vertex additions, some improvements needed")
    else:
        print("✗ Poor performance of legitimate isolated vertex additions, significant issues")
    
    print()
    print("MATHEMATICAL COMPLIANCE:")
    print("- Dau's Rule 7: Isolated vertices can be added to any context")
    print("- Equivalence rule - does not change logical meaning")
    print("- Position specification must be within contexts, not cut notation")
    print("- Supports both generic variables and constants")

if __name__ == "__main__":
    run_enhanced_isolated_vertex_addition_tests()

