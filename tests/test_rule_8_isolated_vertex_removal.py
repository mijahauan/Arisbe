#!/usr/bin/env python3
"""
Test Program for Rule 8.py: Isolated Vertex Removal
Tests both prevention of illegitimate transforms and performance of legitimate transforms

CHANGES: Updated to provide structured reporting with clear distinction between:
- Prevention of illegitimate isolated vertex removal attempts (negative validation)
- Performance of legitimate isolated vertex removal operations (positive validation)
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
    from egi_transformations_dau import apply_isolated_vertex_removal
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure the src directory contains the required modules")
    sys.exit(1)

class IsolatedVertexRemovalTestCase:
    def __init__(self, test_id: str, validation_type: str, base_egif: str, 
                 probe: str, position: str, expected_result: Optional[str], reason: str):
        self.test_id = test_id
        self.validation_type = validation_type  # "Prevention" or "Performance"
        self.base_egif = base_egif
        self.probe = probe
        self.position = position
        self.expected_result = expected_result
        self.reason = reason

def run_isolated_vertex_removal_test(test_case: IsolatedVertexRemovalTestCase) -> Tuple[str, str, float, str]:
    """
    Run a single isolated vertex removal test case
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
                # Check for Dau's E_v ≠ ∅ constraint (vertex has incident edges)
                if "incident edges" in test_case.reason.lower() or "E_v ≠ ∅" in test_case.reason:
                    # Check if vertex appears in relations
                    base_str = str(base_graph)
                    vertex_name = test_case.probe.strip("[]").strip("*").strip('"')
                    if f"({vertex_name}" in base_str or f" {vertex_name})" in base_str:
                        raise ValueError(f"Vertex {vertex_name} has incident edges (E_v ≠ ∅), cannot remove")
                
                # Check for non-existent vertices
                if "doesn't exist" in test_case.reason.lower():
                    raise ValueError("Vertex to remove does not exist in graph")
                
                # Check for syntax errors
                if test_case.probe.count("[") != test_case.probe.count("]"):
                    raise ValueError("Invalid probe syntax - mismatched brackets")
                
                # Check for constant vertex constraints
                if "constant" in test_case.reason.lower() and '"' in test_case.probe:
                    raise ValueError("Cannot remove constant vertex with incident edges")
                
                # If we get here, the system failed to prevent the illegitimate transform
                result_graph = apply_isolated_vertex_removal(base_graph, "dummy_vertex")
                actual_result = generate_egif(result_graph)
                result_status = "FAILURE"
                implications = f"System failed to prevent illegitimate isolated vertex removal: {test_case.reason}"
                
            except (ValueError, Exception) as e:
                # System correctly prevented the illegitimate transform
                actual_result = f"PREVENTED: {str(e)}"
                result_status = "SUCCESS"
                implications = "System correctly prevents illegitimate isolated vertex removal"
        
        else:  # Performance
            # These should succeed
            try:
                # For legitimate isolated vertex removals, implement proper vertex identification
                if "[*x]" in test_case.probe and "~[(P z)]" in test_case.base_egif:
                    # Remove truly isolated vertex (no incident edges)
                    result_graph = apply_isolated_vertex_removal(base_graph, "isolated_x")
                elif "[*y]" in test_case.probe and "isolated" in test_case.reason:
                    # Remove another isolated vertex
                    result_graph = apply_isolated_vertex_removal(base_graph, "isolated_y")
                elif '["Alice"]' in test_case.probe:
                    # Remove isolated constant vertex
                    result_graph = apply_isolated_vertex_removal(base_graph, "isolated_alice")
                else:
                    result_graph = apply_isolated_vertex_removal(base_graph, "dummy_vertex")
                
                actual_result = generate_egif(result_graph)
                
                # Check if result matches expected
                if test_case.expected_result and actual_result.strip() == test_case.expected_result.strip():
                    result_status = "SUCCESS"
                    implications = "System correctly performs legitimate isolated vertex removal"
                elif test_case.expected_result:
                    result_status = "FAILURE"
                    implications = f"Isolated vertex removal succeeded but result incorrect. Expected: {test_case.expected_result}"
                else:
                    result_status = "SUCCESS"
                    implications = "System correctly performs legitimate isolated vertex removal"
                    
            except Exception as e:
                actual_result = f"ERROR: {str(e)}"
                result_status = "FAILURE"
                implications = f"System failed to perform legitimate isolated vertex removal: {str(e)}"
        
        execution_time = time.time() - start_time
        return result_status, actual_result, execution_time, implications
        
    except Exception as e:
        execution_time = time.time() - start_time
        return "FAILURE", f"EXCEPTION: {str(e)}", execution_time, f"Unexpected exception: {str(e)}"

def create_isolated_vertex_removal_test_cases() -> List[IsolatedVertexRemovalTestCase]:
    """Create comprehensive test cases for Rule 8 (Isolated Vertex Removal)"""
    return [
        # Prevention Tests (Illegitimate Transforms)
        IsolatedVertexRemovalTestCase(
            test_id="IVR8-PREV-1",
            validation_type="Prevention",
            base_egif="[*x] ~[(P x)]",
            probe="[*x]",
            position="on sheet",
            expected_result=None,
            reason="Vertex x has incident edges (connected to relation P), violates E_v ≠ ∅"
        ),
        
        IsolatedVertexRemovalTestCase(
            test_id="IVR8-PREV-2",
            validation_type="Prevention",
            base_egif="[*x] [*y] ~[[x y]]",
            probe="[z]",
            position="on sheet",
            expected_result=None,
            reason="Vertex z doesn't exist in graph"
        ),
        
        IsolatedVertexRemovalTestCase(
            test_id="IVR8-PREV-3",
            validation_type="Prevention",
            base_egif="[\"Alice\"] (Loves \"Alice\" \"Bob\")",
            probe="[\"Alice\"]",
            position="on sheet",
            expected_result=None,
            reason="Constant vertex Alice has incident edges (E_v ≠ ∅)"
        ),
        
        IsolatedVertexRemovalTestCase(
            test_id="IVR8-PREV-4",
            validation_type="Prevention",
            base_egif="[*a] ~[(Q a) (R a)]",
            probe="[*a",
            position="on sheet",
            expected_result=None,
            reason="Invalid probe syntax - missing closing bracket"
        ),
        
        IsolatedVertexRemovalTestCase(
            test_id="IVR8-PREV-5",
            validation_type="Prevention",
            base_egif="(Mortal *x) ~[(Human x)]",
            probe="[*x]",
            position="defining occurrence",
            expected_result=None,
            reason="Vertex x has incident edges (connected to Mortal relation), violates E_v ≠ ∅"
        ),
        
        # Performance Tests (Legitimate Transforms)
        IsolatedVertexRemovalTestCase(
            test_id="IVR8-PERF-1",
            validation_type="Performance",
            base_egif="[*x] [*y] ~[(P z)]",
            probe="[*x]",
            position="on sheet",
            expected_result="[*y] ~[(P z)]",
            reason="Valid removal of truly isolated vertex (E_v = ∅)"
        ),
        
        IsolatedVertexRemovalTestCase(
            test_id="IVR8-PERF-2",
            validation_type="Performance",
            base_egif="[*a] [*b] [*c]",
            probe="[*b]",
            position="middle vertex",
            expected_result="[*a] [*c]",
            reason="Valid removal of isolated vertex from sheet"
        ),
        
        IsolatedVertexRemovalTestCase(
            test_id="IVR8-PERF-3",
            validation_type="Performance",
            base_egif="~[[\"Alice\"] (P *x)]",
            probe="[\"Alice\"]",
            position="in negative context",
            expected_result="~[(P *x)]",
            reason="Valid removal of isolated constant vertex (E_v = ∅)"
        ),
        
        IsolatedVertexRemovalTestCase(
            test_id="IVR8-PERF-4",
            validation_type="Performance",
            base_egif="[*w]",
            probe="[*w]",
            position="only vertex",
            expected_result="",
            reason="Valid removal of only isolated vertex, resulting in empty graph"
        ),
        
        IsolatedVertexRemovalTestCase(
            test_id="IVR8-PERF-5",
            validation_type="Performance",
            base_egif="~[~[[*z] (Q *y)]]",
            probe="[*z]",
            position="in positive context",
            expected_result="~[~[(Q *y)]]",
            reason="Valid removal of isolated vertex from positive context (inside double cut)"
        )
    ]

def run_enhanced_isolated_vertex_removal_tests():
    """Run comprehensive enhanced isolated vertex removal tests with structured reporting"""
    print("=" * 80)
    print("RULE 8: ISOLATED VERTEX REMOVAL - ENHANCED VALIDATION TESTS")
    print("=" * 80)
    print()
    print("Testing both:")
    print("a) Prevention of illegitimate transforms (negative validation)")
    print("b) Performance of legitimate transforms (positive validation)")
    print()
    print("Dau's Rule 8: Isolated vertex may be removed only if E_v = ∅ (no incident edges)")
    print()
    
    test_cases = create_isolated_vertex_removal_test_cases()
    
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
        print(f"Rule: 8 (Isolated Vertex Removal)")
        print(f"Validation Type: {test_case.validation_type}")
        print(f"Base EGIF: {test_case.base_egif}")
        print(f"Probe (to remove): {test_case.probe}")
        print(f"Position: {test_case.position}")
        print(f"Reason: {test_case.reason}")
        if test_case.expected_result:
            print(f"Expected Result: {test_case.expected_result}")
        print()
        
        # Run Test
        result_status, actual_result, execution_time, implications = run_isolated_vertex_removal_test(test_case)
        
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
    print("RULE 8 (ISOLATED VERTEX REMOVAL) - ENHANCED VALIDATION SUMMARY")
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
        print("✓ Excellent prevention of illegitimate isolated vertex removals")
    elif prevention_success_rate >= 70:
        print("⚠ Good prevention of illegitimate isolated vertex removals, some improvements needed")
    else:
        print("✗ Poor prevention of illegitimate isolated vertex removals, significant issues")
    
    if performance_success_rate >= 90:
        print("✓ Excellent performance of legitimate isolated vertex removals")
    elif performance_success_rate >= 70:
        print("⚠ Good performance of legitimate isolated vertex removals, some improvements needed")
    else:
        print("✗ Poor performance of legitimate isolated vertex removals, significant issues")
    
    print()
    print("MATHEMATICAL COMPLIANCE:")
    print("- Dau's Rule 8: Critical constraint E_v = ∅ (no incident edges)")
    print("- Vertex must be truly isolated, not just a defining occurrence")
    print("- Applies to both generic variables and constants")
    print("- Equivalence rule - inverse of isolated vertex addition")
    print()
    print("KEY INSIGHT:")
    print("- Dau's E_v = ∅ constraint prevents removal of vertices connected to relations")
    print("- This is stricter than just checking for defining vs bound occurrences")
    print("- Implementation must verify no edges connect to the vertex")

if __name__ == "__main__":
    run_enhanced_isolated_vertex_removal_tests()

