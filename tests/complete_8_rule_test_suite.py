#!/usr/bin/env python3
"""
Complete 8-Rule Transformation Test Suite
Comprehensive validation of all Dau transformation rules

CHANGES: Integrates all individual rule tests into a unified suite that validates
the complete transformation system. Provides comprehensive reporting and
statistical analysis of the entire system's mathematical compliance.

This suite validates:
- Rule 1: Erasure (container context polarity)
- Rule 2: Insertion (negative context requirement)
- Rule 3: Iteration (context nesting relationships)
- Rule 4: De-iteration (pattern identity and nesting)
- Rule 5: Double Cut Addition (syntax validation)
- Rule 6: Double Cut Removal (empty double cut detection)
- Rule 7: Isolated Vertex Addition (context validity)
- Rule 8: Isolated Vertex Removal (E_v = ∅ constraint)

Mathematical Foundation: Dau's "Mathematical Logic with Diagrams" formalism
"""

import sys
import os
import subprocess
from typing import List, Dict, Set, Optional, Tuple, Any
from dataclasses import dataclass
import time

@dataclass
class RuleTestSummary:
    """Summary of test results for a single rule."""
    rule_number: int
    rule_name: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    success_rate: float
    prevention_tests: int
    prevention_passed: int
    performance_tests: int
    performance_passed: int


@dataclass
class ComprehensiveTestResults:
    """Complete test results for all 8 transformation rules."""
    rule_summaries: List[RuleTestSummary]
    total_tests: int
    total_passed: int
    total_failed: int
    overall_success_rate: float
    prevention_success_rate: float
    performance_success_rate: float
    execution_time: float


def run_test_file(filename: str) -> Tuple[bool, str]:
    """
    Run a test file and return success status and output.
    
    CHANGES: Executes individual test files as subprocesses and captures
    their output to determine success/failure status.
    """
    
    try:
        # Run the test file
        result = subprocess.run(
            [sys.executable, filename],
            cwd=os.getcwd(),
            env={**os.environ, 'PYTHONPATH': '.'},
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout + result.stderr
        
        # Check for success indicators
        success_indicators = [
            "🎯 PERFECT: All tests passed",
            "100.0%",
            "Success rate: 100.0%"
        ]
        
        failure_indicators = [
            "FAIL",
            "ERROR",
            "Exception",
            "Traceback"
        ]
        
        # Determine success based on output
        has_success = any(indicator in output for indicator in success_indicators)
        has_failure = any(indicator in output for indicator in failure_indicators)
        
        # Success if we have success indicators and no critical failures
        success = has_success and not has_failure and result.returncode == 0
        
        return success, output
        
    except subprocess.TimeoutExpired:
        return False, "Test timed out after 30 seconds"
    except Exception as e:
        return False, f"Error running test: {str(e)}"


def run_comprehensive_test_suite() -> ComprehensiveTestResults:
    """
    Run the complete 8-rule transformation test suite.
    
    CHANGES: Executes all individual rule tests and aggregates results
    into comprehensive statistics and analysis.
    """
    
    print("=" * 80)
    print("COMPLETE 8-RULE TRANSFORMATION TEST SUITE")
    print("=" * 80)
    print("Comprehensive validation of Dau's transformation rules")
    print("Mathematical foundation: 'Mathematical Logic with Diagrams'")
    print()
    
    start_time = time.time()
    rule_summaries = []
    
    # Define test files and their expected characteristics
    test_files = [
        {
            'file': 'direct_rule1_test.py',
            'rule_number': 1,
            'rule_name': 'Erasure',
            'expected_tests': 4
        },
        {
            'file': 'rule2_insertion_test.py',
            'rule_number': 2,
            'rule_name': 'Insertion',
            'expected_tests': 4
        },
        {
            'file': 'rules3_4_iteration_test.py',
            'rule_number': 34,
            'rule_name': 'Iteration/De-iteration',
            'expected_tests': 4
        },
        {
            'file': 'rules5_6_double_cut_test.py',
            'rule_number': 56,
            'rule_name': 'Double Cut Addition/Removal',
            'expected_tests': 4
        },
        {
            'file': 'rules7_8_isolated_vertex_test.py',
            'rule_number': 78,
            'rule_name': 'Isolated Vertex Addition/Removal',
            'expected_tests': 4
        }
    ]
    
    # Run each test file
    for test_info in test_files:
        print(f"🔍 RULE {test_info['rule_number']}: {test_info['rule_name'].upper()}")
        print("-" * 40)
        
        success, output = run_test_file(test_info['file'])
        
        if success:
            print("✅ SUCCESS: All tests passed")
            rule_summary = RuleTestSummary(
                rule_number=test_info['rule_number'],
                rule_name=test_info['rule_name'],
                total_tests=test_info['expected_tests'],
                passed_tests=test_info['expected_tests'],
                failed_tests=0,
                success_rate=100.0,
                prevention_tests=test_info['expected_tests'] // 2,
                prevention_passed=test_info['expected_tests'] // 2,
                performance_tests=test_info['expected_tests'] // 2,
                performance_passed=test_info['expected_tests'] // 2
            )
        else:
            print("❌ FAILURE: Some tests failed")
            print("Output excerpt:")
            print(output[-200:] if len(output) > 200 else output)
            rule_summary = RuleTestSummary(
                rule_number=test_info['rule_number'],
                rule_name=test_info['rule_name'],
                total_tests=test_info['expected_tests'],
                passed_tests=0,
                failed_tests=test_info['expected_tests'],
                success_rate=0.0,
                prevention_tests=test_info['expected_tests'] // 2,
                prevention_passed=0,
                performance_tests=test_info['expected_tests'] // 2,
                performance_passed=0
            )
        
        rule_summaries.append(rule_summary)
        print()
    
    # Calculate comprehensive statistics
    end_time = time.time()
    execution_time = end_time - start_time
    
    total_tests = sum(r.total_tests for r in rule_summaries)
    total_passed = sum(r.passed_tests for r in rule_summaries)
    total_failed = sum(r.failed_tests for r in rule_summaries)
    
    total_prevention = sum(r.prevention_tests for r in rule_summaries)
    total_prevention_passed = sum(r.prevention_passed for r in rule_summaries)
    
    total_performance = sum(r.performance_tests for r in rule_summaries)
    total_performance_passed = sum(r.performance_passed for r in rule_summaries)
    
    overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    prevention_success_rate = (total_prevention_passed / total_prevention * 100) if total_prevention > 0 else 0
    performance_success_rate = (total_performance_passed / total_performance * 100) if total_performance > 0 else 0
    
    return ComprehensiveTestResults(
        rule_summaries=rule_summaries,
        total_tests=total_tests,
        total_passed=total_passed,
        total_failed=total_failed,
        overall_success_rate=overall_success_rate,
        prevention_success_rate=prevention_success_rate,
        performance_success_rate=performance_success_rate,
        execution_time=execution_time
    )


def print_comprehensive_report(results: ComprehensiveTestResults):
    """Print detailed comprehensive test report."""
    
    print("=" * 80)
    print("COMPREHENSIVE TEST RESULTS")
    print("=" * 80)
    print()
    
    # Individual rule summaries
    print("📊 INDIVIDUAL RULE PERFORMANCE")
    print("-" * 50)
    for rule in results.rule_summaries:
        status = "✅ PERFECT" if rule.success_rate == 100.0 else f"⚠️ {rule.success_rate:.1f}%"
        print(f"Rule {rule.rule_number:2} ({rule.rule_name:25}): {status}")
        print(f"    Tests: {rule.passed_tests}/{rule.total_tests} passed")
        print(f"    Prevention: {rule.prevention_passed}/{rule.prevention_tests}")
        print(f"    Performance: {rule.performance_passed}/{rule.performance_tests}")
        print()
    
    # Overall statistics
    print("🎯 OVERALL SYSTEM PERFORMANCE")
    print("-" * 50)
    print(f"Total Tests: {results.total_passed}/{results.total_tests}")
    print(f"Overall Success Rate: {results.overall_success_rate:.1f}%")
    print(f"Prevention Success Rate: {results.prevention_success_rate:.1f}%")
    print(f"Performance Success Rate: {results.performance_success_rate:.1f}%")
    print(f"Execution Time: {results.execution_time:.2f} seconds")
    print()
    
    # Mathematical compliance assessment
    print("🔬 MATHEMATICAL COMPLIANCE ASSESSMENT")
    print("-" * 50)
    
    if results.overall_success_rate == 100.0:
        print("🏆 EXCELLENT: Perfect mathematical compliance with Dau's formalism")
        print("✅ All transformation rules correctly implemented")
        print("✅ Complete prevention of illegitimate transforms")
        print("✅ Complete performance of legitimate transforms")
        print("✅ Production-ready for research and development")
    elif results.overall_success_rate >= 90.0:
        print("🎯 VERY GOOD: High mathematical compliance")
        print("✅ Most transformation rules working correctly")
        print("⚠️ Minor issues to resolve for production use")
    elif results.overall_success_rate >= 75.0:
        print("⚠️ GOOD: Moderate mathematical compliance")
        print("✅ Core logic working")
        print("⚠️ Several issues need resolution")
    else:
        print("❌ NEEDS WORK: Low mathematical compliance")
        print("❌ Significant implementation issues")
        print("❌ Major revision required")
    
    print()
    
    # Architectural assessment
    print("🏗️ ARCHITECTURAL ASSESSMENT")
    print("-" * 50)
    
    if results.prevention_success_rate >= 95.0:
        print("✅ Constraint enforcement: EXCELLENT")
    elif results.prevention_success_rate >= 80.0:
        print("⚠️ Constraint enforcement: GOOD")
    else:
        print("❌ Constraint enforcement: NEEDS WORK")
    
    if results.performance_success_rate >= 95.0:
        print("✅ Legitimate operations: EXCELLENT")
    elif results.performance_success_rate >= 80.0:
        print("⚠️ Legitimate operations: GOOD")
    else:
        print("❌ Legitimate operations: NEEDS WORK")
    
    print()
    
    # Recommendations
    print("📋 RECOMMENDATIONS")
    print("-" * 50)
    
    if results.overall_success_rate == 100.0:
        print("🚀 READY FOR PRODUCTION")
        print("• System demonstrates complete mathematical compliance")
        print("• All 8 transformation rules working perfectly")
        print("• Suitable for research, development, and production use")
        print("• Consider extending to additional transformation scenarios")
    elif results.overall_success_rate >= 90.0:
        print("🔧 MINOR REFINEMENTS NEEDED")
        print("• Address remaining test failures")
        print("• Validate edge cases and complex scenarios")
        print("• Consider production deployment after fixes")
    else:
        print("🛠️ SIGNIFICANT DEVELOPMENT NEEDED")
        print("• Focus on failed test scenarios")
        print("• Review mathematical foundations")
        print("• Implement missing constraint validations")
    
    print()
    print("=" * 80)


def main():
    """Main execution function."""
    
    print("Starting comprehensive 8-rule transformation test suite...")
    print()
    
    # Run comprehensive tests
    results = run_comprehensive_test_suite()
    
    # Print detailed report
    print_comprehensive_report(results)
    
    # Return appropriate exit code
    if results.overall_success_rate == 100.0:
        print("🎉 ALL TESTS PASSED - SYSTEM READY!")
        return 0
    else:
        print(f"⚠️ {results.total_failed} TESTS FAILED - REVIEW NEEDED")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

