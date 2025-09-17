"""
Comprehensive transformation testing framework for validating EG transformation rules.
Tests all transformation rules with various graph structures and edge cases.
"""

import json
import time
import traceback
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from composition_transformer import CompositionTransformer

from egi_core_dau import ElementID, RelationalGraphWithCuts
from egif_generator_dau import generate_egif
from egif_parser_dau import parse_egif
from egif_transformation_interface import (
    EGIFTransformationInterface,
    TransformationRequest,
)


class TestResult(Enum):
    """Test result status."""

    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"
    SKIP = "SKIP"


@dataclass
class TransformationTest:
    """A single transformation test case."""

    test_id: str
    rule_name: str
    description: str
    source_egif: str
    target_area: str
    operation_details: Dict[str, Any]
    expected_result: Optional[str]  # Expected EGIF result, None if should fail
    should_succeed: bool
    category: str = "basic"
    tags: List[str] = None


@dataclass
class TestExecutionResult:
    """Result of executing a transformation test."""

    test: TransformationTest
    result: TestResult
    actual_egif: Optional[str]
    error_message: Optional[str]
    execution_time: float
    details: Dict[str, Any]


class TransformationTestSuite:
    """Comprehensive test suite for transformation rules."""

    def __init__(self):
        self.interface = EGIFTransformationInterface()
        self.composition_transformer = CompositionTransformer()
        self.tests: List[TransformationTest] = []
        self._setup_test_cases()

    def _setup_test_cases(self):
        """Set up comprehensive test cases for all transformation rules."""

        # INS (Insertion) Tests
        self._add_ins_tests()

        # ERA (Erasure) Tests
        self._add_era_tests()

        # DC+ (Double Cut Insertion) Tests
        self._add_dc_plus_tests()

        # DC- (Double Cut Erasure) Tests
        self._add_dc_minus_tests()

        # IT+ (Iteration) Tests
        self._add_it_plus_tests()

        # IT- (Deiteration) Tests
        self._add_it_minus_tests()

        # Composition Context Tests
        self._add_composition_tests()

        # Edge Case Tests
        self._add_edge_case_tests()

    def _add_ins_tests(self):
        """Add INS (Insertion) transformation tests."""

        # Basic insertion into negative area
        self.tests.append(
            TransformationTest(
                test_id="ins_001",
                rule_name="INS",
                description="Insert simple predicate into double cut",
                source_egif="~[ ~[ ] ]",
                target_area="negative_area",
                operation_details={"insert_content": '(Human "Socrates")'},
                expected_result="~[ ~[ *x (Human x) ] ]",
                should_succeed=True,
                category="insertion",
                tags=["basic", "negative_area"],
            )
        )

        # Insertion into deeper negative area
        self.tests.append(
            TransformationTest(
                test_id="ins_002",
                rule_name="INS",
                description="Insert predicate into deeper negative context",
                source_egif="~[ ~[ ~[ ] ] ]",
                target_area="negative_area",
                operation_details={"insert_content": '(Mortal "Plato")'},
                expected_result=None,  # Will be determined dynamically
                should_succeed=True,
                category="insertion",
                tags=["deep_context", "negative_area"],
            )
        )

        # Invalid insertion into positive area (should fail)
        self.tests.append(
            TransformationTest(
                test_id="ins_003",
                rule_name="INS",
                description="Attempt insertion into positive area (should fail)",
                source_egif='(Human "Aristotle")',
                target_area="sheet",
                operation_details={"insert_content": '(Wise "Aristotle")'},
                expected_result=None,
                should_succeed=False,
                category="insertion",
                tags=["error_case", "positive_area"],
            )
        )

    def _add_era_tests(self):
        """Add ERA (Erasure) transformation tests."""

        # Basic erasure from positive area
        self.tests.append(
            TransformationTest(
                test_id="era_001",
                rule_name="ERA",
                description="Erase predicate from sheet",
                source_egif='(Human "Socrates") (Mortal "Socrates")',
                target_area="sheet",
                operation_details={
                    "selected_elements": ["human_edge"]
                },  # Will be resolved dynamically
                expected_result='(Mortal "Socrates")',
                should_succeed=True,
                category="erasure",
                tags=["basic", "positive_area"],
            )
        )

        # Erasure from cut area
        self.tests.append(
            TransformationTest(
                test_id="era_002",
                rule_name="ERA",
                description="Erase content from cut area",
                source_egif='~[ (Wise "Plato") ]',
                target_area="cut_area",
                operation_details={"selected_elements": ["wise_edge"]},
                expected_result="~[ ]",
                should_succeed=True,
                category="erasure",
                tags=["cut_area", "negative_area"],
            )
        )

    def _add_dc_plus_tests(self):
        """Add DC+ (Double Cut Insertion) transformation tests."""

        # Basic double cut insertion
        self.tests.append(
            TransformationTest(
                test_id="dc_plus_001",
                rule_name="DC+",
                description="Insert double cut around content",
                source_egif='(Human "Socrates")',
                target_area="sheet",
                operation_details={"selected_elements": []},
                expected_result='~[ ~[ (Human "Socrates") ] ]',
                should_succeed=True,
                category="double_cut",
                tags=["basic", "insertion"],
            )
        )

    def _add_dc_minus_tests(self):
        """Add DC- (Double Cut Erasure) transformation tests."""

        # Basic double cut erasure
        self.tests.append(
            TransformationTest(
                test_id="dc_minus_001",
                rule_name="DC-",
                description="Remove double cut structure",
                source_egif='~[ ~[ (Human "Socrates") ] ]',
                target_area="outer_cut",
                operation_details={"selected_elements": []},
                expected_result='(Human "Socrates")',
                should_succeed=True,
                category="double_cut",
                tags=["basic", "erasure"],
            )
        )

    def _add_it_plus_tests(self):
        """Add IT+ (Iteration) transformation tests."""

        # Basic iteration
        self.tests.append(
            TransformationTest(
                test_id="it_plus_001",
                rule_name="IT+",
                description="Iterate predicate to nested area",
                source_egif='(Wise "Socrates") ~[ ]',
                target_area="sheet",
                operation_details={
                    "selected_elements": ["wise_edge"],
                    "destination_area": "cut_area",
                },
                expected_result='(Wise "Socrates") ~[ (Wise "Socrates") ]',
                should_succeed=True,
                category="iteration",
                tags=["basic", "copy"],
            )
        )

    def _add_it_minus_tests(self):
        """Add IT- (Deiteration) transformation tests."""

        # Basic deiteration with isomorphic subgraphs
        self.tests.append(
            TransformationTest(
                test_id="it_minus_001",
                rule_name="IT-",
                description="Deiterate duplicate predicate",
                source_egif='(Wise "Socrates") ~[ (Wise "Socrates") ]',
                target_area="cut_area",
                operation_details={"selected_elements": ["wise_copy_edge"]},
                expected_result='(Wise "Socrates") ~[ ]',
                should_succeed=True,
                category="deiteration",
                tags=["basic", "isomorphism"],
            )
        )

    def _add_composition_tests(self):
        """Add composition context transformation tests."""

        # Composition session workflow
        self.tests.append(
            TransformationTest(
                test_id="comp_001",
                rule_name="COMPOSITION",
                description="Complete composition workflow",
                source_egif="",  # Will use composition transformer
                target_area="",
                operation_details={"workflow": "standard_session"},
                expected_result=None,
                should_succeed=True,
                category="composition",
                tags=["workflow", "session"],
            )
        )

    def _add_edge_case_tests(self):
        """Add edge case and error condition tests."""

        # Empty graph transformations
        self.tests.append(
            TransformationTest(
                test_id="edge_001",
                rule_name="INS",
                description="Insert into empty graph",
                source_egif="",
                target_area="sheet",
                operation_details={"insert_content": '(Test "value")'},
                expected_result=None,
                should_succeed=False,
                category="edge_case",
                tags=["empty", "error"],
            )
        )

        # Invalid area references
        self.tests.append(
            TransformationTest(
                test_id="edge_002",
                rule_name="ERA",
                description="Erase from non-existent area",
                source_egif='(Human "Socrates")',
                target_area="invalid_area",
                operation_details={"selected_elements": []},
                expected_result=None,
                should_succeed=False,
                category="edge_case",
                tags=["invalid_area", "error"],
            )
        )

    def run_test(self, test: TransformationTest) -> TestExecutionResult:
        """Execute a single transformation test."""
        start_time = time.time()

        try:
            if test.rule_name == "COMPOSITION":
                return self._run_composition_test(test, start_time)
            else:
                return self._run_transformation_test(test, start_time)

        except Exception as e:
            execution_time = time.time() - start_time
            return TestExecutionResult(
                test=test,
                result=TestResult.ERROR,
                actual_egif=None,
                error_message=str(e),
                execution_time=execution_time,
                details={"exception": traceback.format_exc()},
            )

    def _run_transformation_test(
        self, test: TransformationTest, start_time: float
    ) -> TestExecutionResult:
        """Run a standard transformation test."""

        # Resolve dynamic target areas and elements
        source_egif = test.source_egif
        target_area = self._resolve_target_area(source_egif, test.target_area)
        operation_details = self._resolve_operation_details(
            source_egif, test.operation_details
        )

        # Create transformation request
        request = TransformationRequest(
            source_egif=source_egif,
            rule_name=test.rule_name,
            target_area_description=target_area,
            operation_details=operation_details,
            description=test.description,
        )

        # Execute transformation
        response = self.interface.apply_transformation(request)
        execution_time = time.time() - start_time

        # Evaluate result
        if test.should_succeed:
            if response.success:
                result = TestResult.PASS
                actual_egif = response.result_egif
                error_message = None
            else:
                result = TestResult.FAIL
                actual_egif = None
                error_message = response.error_message
        else:
            if not response.success:
                result = TestResult.PASS
                actual_egif = None
                error_message = "Expected failure occurred"
            else:
                result = TestResult.FAIL
                actual_egif = response.result_egif
                error_message = "Expected failure but transformation succeeded"

        return TestExecutionResult(
            test=test,
            result=result,
            actual_egif=actual_egif,
            error_message=error_message,
            execution_time=execution_time,
            details={
                "response_success": response.success,
                "response_error": response.error_message,
            },
        )

    def _run_composition_test(
        self, test: TransformationTest, start_time: float
    ) -> TestExecutionResult:
        """Run a composition workflow test."""

        try:
            # Test composition session workflow
            session = self.composition_transformer.start_composition_session(
                "standard", "test_session", "Test composition workflow"
            )

            # Insert a predicate
            response = self.composition_transformer.insert_in_composition_area(
                '(Test "composition")'
            )

            execution_time = time.time() - start_time

            if response.success:
                result = TestResult.PASS
                actual_egif = response.result_egif
                error_message = None
            else:
                result = TestResult.FAIL
                actual_egif = None
                error_message = response.error_message

            return TestExecutionResult(
                test=test,
                result=result,
                actual_egif=actual_egif,
                error_message=error_message,
                execution_time=execution_time,
                details={"session_id": session.session_id},
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return TestExecutionResult(
                test=test,
                result=TestResult.ERROR,
                actual_egif=None,
                error_message=str(e),
                execution_time=execution_time,
                details={"exception": traceback.format_exc()},
            )

    def _resolve_target_area(self, source_egif: str, target_area_desc: str) -> str:
        """Resolve dynamic target area descriptions."""
        if not source_egif:
            return "sheet"

        try:
            egi = parse_egif(source_egif)

            if target_area_desc == "negative_area":
                # Find first negative area
                for area_id in egi.area.keys():
                    depth = self._calculate_nesting_depth(area_id, egi)
                    if depth % 2 == 1:  # Negative area
                        return str(area_id)
                return "sheet"

            elif target_area_desc == "cut_area":
                # Find first cut area
                for cut in egi.Cut:
                    return str(cut.id)
                return "sheet"

            elif target_area_desc == "outer_cut":
                # Find outermost cut
                for cut in egi.Cut:
                    # Check if this cut is not contained by any other cut
                    is_contained = False
                    for other_cut in egi.Cut:
                        if cut.id != other_cut.id:
                            other_contents = egi.area.get(other_cut.id, frozenset())
                            if cut.id in other_contents:
                                is_contained = True
                                break
                    if not is_contained:
                        return str(cut.id)
                return "sheet"

        except Exception as e:
            print(f"Error resolving target area {target_area_desc}: {e}")
            pass

        return target_area_desc

    def _resolve_operation_details(
        self, source_egif: str, operation_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve dynamic operation details like element IDs."""
        resolved = dict(operation_details)

        # For now, return as-is. In future iterations, we can add
        # dynamic element ID resolution based on the source EGIF

        return resolved

    def _calculate_nesting_depth(self, area_id, egi):
        """Calculate nesting depth by counting containing cuts."""
        depth = 0
        for cut in egi.Cut:
            cut_contents = egi.area.get(cut.id, frozenset())
            if area_id in cut_contents:
                depth += 1
        return depth

    def run_all_tests(
        self, categories: Optional[List[str]] = None, tags: Optional[List[str]] = None
    ) -> List[TestExecutionResult]:
        """Run all tests, optionally filtered by categories or tags."""

        tests_to_run = self.tests

        if categories:
            tests_to_run = [t for t in tests_to_run if t.category in categories]

        if tags:
            tests_to_run = [
                t for t in tests_to_run if any(tag in (t.tags or []) for tag in tags)
            ]

        results = []
        for test in tests_to_run:
            result = self.run_test(test)
            results.append(result)

        return results

    def generate_test_report(
        self, results: List[TestExecutionResult]
    ) -> Dict[str, Any]:
        """Generate a comprehensive test report."""

        total_tests = len(results)
        passed = len([r for r in results if r.result == TestResult.PASS])
        failed = len([r for r in results if r.result == TestResult.FAIL])
        errors = len([r for r in results if r.result == TestResult.ERROR])

        # Group by category
        by_category = {}
        for result in results:
            category = result.test.category
            if category not in by_category:
                by_category[category] = {
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "errors": 0,
                }

            by_category[category]["total"] += 1
            if result.result == TestResult.PASS:
                by_category[category]["passed"] += 1
            elif result.result == TestResult.FAIL:
                by_category[category]["failed"] += 1
            elif result.result == TestResult.ERROR:
                by_category[category]["errors"] += 1

        # Failed tests details
        failed_tests = [
            r for r in results if r.result in [TestResult.FAIL, TestResult.ERROR]
        ]

        return {
            "summary": {
                "total_tests": total_tests,
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "success_rate": (passed / total_tests * 100) if total_tests > 0 else 0,
            },
            "by_category": by_category,
            "failed_tests": [
                {
                    "test_id": r.test.test_id,
                    "description": r.test.description,
                    "result": r.result.value,
                    "error_message": r.error_message,
                }
                for r in failed_tests
            ],
            "execution_times": {
                "total": sum(r.execution_time for r in results),
                "average": (
                    sum(r.execution_time for r in results) / len(results)
                    if results
                    else 0
                ),
                "slowest": (
                    max(results, key=lambda r: r.execution_time) if results else None
                ),
            },
        }


def run_comprehensive_tests():
    """Run the comprehensive transformation test suite."""
    print("=== Comprehensive Transformation Testing Framework ===")

    suite = TransformationTestSuite()

    print(f"Total test cases: {len(suite.tests)}")

    # Run all tests
    print("\nRunning all tests...")
    results = suite.run_all_tests()

    # Generate report
    report = suite.generate_test_report(results)

    # Print summary
    print(f"\n=== Test Results Summary ===")
    print(f"Total Tests: {report['summary']['total_tests']}")
    print(f"Passed: {report['summary']['passed']}")
    print(f"Failed: {report['summary']['failed']}")
    print(f"Errors: {report['summary']['errors']}")
    print(f"Success Rate: {report['summary']['success_rate']:.1f}%")

    # Print by category
    print(f"\n=== Results by Category ===")
    for category, stats in report["by_category"].items():
        print(f"{category}: {stats['passed']}/{stats['total']} passed")

    # Print failed tests
    if report["failed_tests"]:
        print(f"\n=== Failed Tests ===")
        for failed in report["failed_tests"]:
            print(f"❌ {failed['test_id']}: {failed['description']}")
            if failed["error_message"]:
                print(f"   Error: {failed['error_message']}")

    return report


if __name__ == "__main__":
    run_comprehensive_tests()
