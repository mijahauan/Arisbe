"""
Comprehensive test cases for basic graph utterances through transformation sequences.
Tests the fundamental capability of building graphs through rule-governed transformations.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from frozendict import frozendict
from immutable_transformation_architecture import ContextType, TransformationRuleType
from rule_governed_composition import RuleGovernedComposer, ValidationLevel
from simple_graph_builder import SimpleGraphBuilder

from egi_core_dau import Cut, Edge, ElementID, RelationalGraphWithCuts, Vertex


@dataclass
class TestCase:
    """Test case for graph utterance building."""

    test_id: str
    name: str
    description: str
    expected_outcome: Dict[str, int]
    transformation_sequence: List[Dict[str, Any]]
    validation_checks: List[str]

    def validate_result(self, final_egi: RelationalGraphWithCuts) -> Dict[str, bool]:
        """Validate the final EGI against expected outcomes."""
        results = {}

        # Check element counts
        results["vertex_count"] = len(final_egi.V) == self.expected_outcome.get(
            "vertices", 0
        )
        results["edge_count"] = len(final_egi.E) == self.expected_outcome.get(
            "edges", 0
        )
        results["cut_count"] = len(final_egi.Cut) == self.expected_outcome.get(
            "cuts", 0
        )

        # Check total elements
        total_expected = sum(self.expected_outcome.values())
        total_actual = len(final_egi.V) + len(final_egi.E) + len(final_egi.Cut)
        results["total_elements"] = total_actual == total_expected

        return results


class GraphUtteranceTestSuite:
    """Test suite for graph utterance building."""

    def __init__(self):
        self.builder = SimpleGraphBuilder()
        self.composer = RuleGovernedComposer(ValidationLevel.STRICT)
        self.test_cases: Dict[str, TestCase] = {}
        self.test_results: Dict[str, Dict[str, Any]] = {}

        # Initialize test cases
        self._create_basic_test_cases()
        self._create_logical_test_cases()
        self._create_relational_test_cases()
        self._create_complex_test_cases()

    def _create_basic_test_cases(self):
        """Create basic graph building test cases."""

        # Test 1: Empty to single vertex
        self.test_cases["empty_to_vertex"] = TestCase(
            test_id="empty_to_vertex",
            name="Empty to Single Vertex",
            description="Build simplest possible graph - one vertex",
            expected_outcome={"vertices": 1, "edges": 0, "cuts": 0},
            transformation_sequence=[
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "vertex",
                        "element_id": "v1",
                        "target_area": "sheet",
                    },
                    "justification": "Insert single vertex",
                }
            ],
            validation_checks=["vertex_count", "total_elements"],
        )

        # Test 2: Two vertices (conjunction)
        self.test_cases["two_vertices"] = TestCase(
            test_id="two_vertices",
            name="Two Vertices Conjunction",
            description="Two vertices expressing conjunction through spatial juxtaposition",
            expected_outcome={"vertices": 2, "edges": 0, "cuts": 0},
            transformation_sequence=[
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "vertex",
                        "element_id": "v1",
                        "target_area": "sheet",
                    },
                    "justification": "Insert first vertex",
                },
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "vertex",
                        "element_id": "v2",
                        "target_area": "sheet",
                    },
                    "justification": "Insert second vertex for conjunction",
                },
            ],
            validation_checks=["vertex_count", "total_elements"],
        )

        # Test 3: Simple negation
        self.test_cases["simple_negation"] = TestCase(
            test_id="simple_negation",
            name="Simple Negation",
            description="Single vertex under negation (cut)",
            expected_outcome={"vertices": 1, "edges": 0, "cuts": 1},
            transformation_sequence=[
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "vertex",
                        "element_id": "v1",
                        "target_area": "sheet",
                    },
                    "justification": "Insert vertex to be negated",
                },
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "cut",
                        "element_id": "c1",
                        "target_area": "sheet",
                        "enclosed_elements": frozenset(["v1"]),
                    },
                    "justification": "Insert cut around vertex for negation",
                },
            ],
            validation_checks=["vertex_count", "cut_count", "total_elements"],
        )

    def _create_logical_test_cases(self):
        """Create logical expression test cases."""

        # Test 4: Three-way conjunction
        self.test_cases["three_conjunction"] = TestCase(
            test_id="three_conjunction",
            name="Three-way Conjunction",
            description="Three vertices expressing A ∧ B ∧ C",
            expected_outcome={"vertices": 3, "edges": 0, "cuts": 0},
            transformation_sequence=[
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "vertex",
                        "element_id": "A",
                        "target_area": "sheet",
                    },
                    "justification": "Insert vertex A",
                },
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "vertex",
                        "element_id": "B",
                        "target_area": "sheet",
                    },
                    "justification": "Insert vertex B",
                },
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "vertex",
                        "element_id": "C",
                        "target_area": "sheet",
                    },
                    "justification": "Insert vertex C",
                },
            ],
            validation_checks=["vertex_count", "total_elements"],
        )

        # Test 5: Double negation
        self.test_cases["double_negation"] = TestCase(
            test_id="double_negation",
            name="Double Negation",
            description="Vertex under double negation ¬¬P",
            expected_outcome={"vertices": 1, "edges": 0, "cuts": 2},
            transformation_sequence=[
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "vertex",
                        "element_id": "P",
                        "target_area": "sheet",
                    },
                    "justification": "Insert vertex P",
                },
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "cut",
                        "element_id": "inner_cut",
                        "target_area": "sheet",
                        "enclosed_elements": frozenset(["P"]),
                    },
                    "justification": "First negation",
                },
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "cut",
                        "element_id": "outer_cut",
                        "target_area": "sheet",
                        "enclosed_elements": frozenset(["inner_cut"]),
                    },
                    "justification": "Second negation (double negation)",
                },
            ],
            validation_checks=["vertex_count", "cut_count", "total_elements"],
        )

    def _create_relational_test_cases(self):
        """Create relational graph test cases."""

        # Test 6: Binary relation
        self.test_cases["binary_relation"] = TestCase(
            test_id="binary_relation",
            name="Binary Relation",
            description="Two vertices connected by binary relation",
            expected_outcome={"vertices": 2, "edges": 1, "cuts": 0},
            transformation_sequence=[
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "vertex",
                        "element_id": "alice",
                        "target_area": "sheet",
                    },
                    "justification": "Insert vertex Alice",
                },
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "vertex",
                        "element_id": "bob",
                        "target_area": "sheet",
                    },
                    "justification": "Insert vertex Bob",
                },
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "edge",
                        "element_id": "knows",
                        "target_area": "sheet",
                        "vertex_sequence": ("alice", "bob"),
                        "relation_name": "Knows",
                    },
                    "justification": "Connect with 'knows' relation",
                },
            ],
            validation_checks=["vertex_count", "edge_count", "total_elements"],
        )

        # Test 7: Negated relation
        self.test_cases["negated_relation"] = TestCase(
            test_id="negated_relation",
            name="Negated Relation",
            description="Binary relation under negation",
            expected_outcome={"vertices": 2, "edges": 1, "cuts": 1},
            transformation_sequence=[
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "vertex",
                        "element_id": "alice",
                        "target_area": "sheet",
                    },
                    "justification": "Insert vertex Alice",
                },
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "vertex",
                        "element_id": "bob",
                        "target_area": "sheet",
                    },
                    "justification": "Insert vertex Bob",
                },
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "edge",
                        "element_id": "likes",
                        "target_area": "sheet",
                        "vertex_sequence": ("alice", "bob"),
                        "relation_name": "Likes",
                    },
                    "justification": "Connect with 'likes' relation",
                },
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "cut",
                        "element_id": "negation",
                        "target_area": "sheet",
                        "enclosed_elements": frozenset(["bob", "likes"]),
                    },
                    "justification": "Negate 'Alice likes Bob'",
                },
            ],
            validation_checks=[
                "vertex_count",
                "edge_count",
                "cut_count",
                "total_elements",
            ],
        )

    def _create_complex_test_cases(self):
        """Create complex graph test cases."""

        # Test 8: Ternary relation
        self.test_cases["ternary_relation"] = TestCase(
            test_id="ternary_relation",
            name="Ternary Relation",
            description="Three vertices connected by ternary relation",
            expected_outcome={"vertices": 3, "edges": 1, "cuts": 0},
            transformation_sequence=[
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "vertex",
                        "element_id": "alice",
                        "target_area": "sheet",
                    },
                    "justification": "Insert vertex Alice",
                },
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "vertex",
                        "element_id": "bob",
                        "target_area": "sheet",
                    },
                    "justification": "Insert vertex Bob",
                },
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "vertex",
                        "element_id": "book",
                        "target_area": "sheet",
                    },
                    "justification": "Insert vertex Book",
                },
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "edge",
                        "element_id": "gives",
                        "target_area": "sheet",
                        "vertex_sequence": ("alice", "book", "bob"),
                        "relation_name": "Gives",
                    },
                    "justification": "Connect with ternary 'gives' relation",
                },
            ],
            validation_checks=["vertex_count", "edge_count", "total_elements"],
        )

        # Test 9: Mixed conjunction and negation
        self.test_cases["mixed_conjunction_negation"] = TestCase(
            test_id="mixed_conjunction_negation",
            name="Mixed Conjunction and Negation",
            description="A ∧ ¬B - conjunction with one negated component",
            expected_outcome={"vertices": 2, "edges": 0, "cuts": 1},
            transformation_sequence=[
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "vertex",
                        "element_id": "A",
                        "target_area": "sheet",
                    },
                    "justification": "Insert vertex A",
                },
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "vertex",
                        "element_id": "B",
                        "target_area": "sheet",
                    },
                    "justification": "Insert vertex B",
                },
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "cut",
                        "element_id": "neg_B",
                        "target_area": "sheet",
                        "enclosed_elements": frozenset(["B"]),
                    },
                    "justification": "Negate B for A ∧ ¬B",
                },
            ],
            validation_checks=["vertex_count", "cut_count", "total_elements"],
        )

    def run_test_case(self, test_id: str) -> Dict[str, Any]:
        """Run a specific test case."""
        test_case = self.test_cases.get(test_id)
        if not test_case:
            return {"error": f"Test case {test_id} not found"}

        try:
            # Build the graph utterance
            utterance_id = self.builder.build_graph_utterance(
                title=test_case.name,
                description=test_case.description,
                building_steps=test_case.transformation_sequence,
            )

            # Get the final EGI
            final_egi = self.builder.get_utterance_egi(utterance_id)
            if not final_egi:
                return {"error": "Failed to get final EGI"}

            # Validate results
            validation_results = test_case.validate_result(final_egi)

            # Analyze the utterance
            analysis = self.builder.analyze_utterance(utterance_id)

            result = {
                "test_id": test_id,
                "name": test_case.name,
                "status": "PASSED" if all(validation_results.values()) else "FAILED",
                "validation_results": validation_results,
                "final_state": analysis["final_state"],
                "expected_outcome": test_case.expected_outcome,
                "transformation_steps": len(test_case.transformation_sequence),
                "utterance_id": utterance_id,
            }

            self.test_results[test_id] = result
            return result

        except Exception as e:
            result = {
                "test_id": test_id,
                "name": test_case.name,
                "status": "ERROR",
                "error": str(e),
                "expected_outcome": test_case.expected_outcome,
            }
            self.test_results[test_id] = result
            return result

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test cases."""
        results = {}
        passed = 0
        failed = 0
        errors = 0

        print("🧪 Running Graph Utterance Test Suite")
        print("=" * 40)

        for test_id in self.test_cases.keys():
            result = self.run_test_case(test_id)
            results[test_id] = result

            status = result["status"]
            if status == "PASSED":
                passed += 1
                print(f"✅ {result['name']}: PASSED")
            elif status == "FAILED":
                failed += 1
                print(f"❌ {result['name']}: FAILED")
                print(f"   Expected: {result['expected_outcome']}")
                print(f"   Actual: {result['final_state']}")
            else:
                errors += 1
                print(f"💥 {result['name']}: ERROR - {result['error']}")

        summary = {
            "total_tests": len(self.test_cases),
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "success_rate": passed / len(self.test_cases) if self.test_cases else 0,
            "results": results,
        }

        print(f"\n📊 Test Summary:")
        print(f"   Total tests: {summary['total_tests']}")
        print(f"   Passed: {summary['passed']}")
        print(f"   Failed: {summary['failed']}")
        print(f"   Errors: {summary['errors']}")
        print(f"   Success rate: {summary['success_rate']:.1%}")

        return summary

    def get_test_case_details(self, test_id: str) -> Dict[str, Any]:
        """Get detailed information about a test case."""
        test_case = self.test_cases.get(test_id)
        if not test_case:
            return {"error": "Test case not found"}

        return {
            "test_id": test_id,
            "name": test_case.name,
            "description": test_case.description,
            "expected_outcome": test_case.expected_outcome,
            "transformation_steps": len(test_case.transformation_sequence),
            "validation_checks": test_case.validation_checks,
            "sequence_details": [
                {
                    "step": i + 1,
                    "rule": step["rule_type"].value,
                    "justification": step["justification"],
                }
                for i, step in enumerate(test_case.transformation_sequence)
            ],
        }


def run_comprehensive_tests():
    """Run comprehensive test suite for graph utterances."""

    test_suite = GraphUtteranceTestSuite()

    # Run all tests
    summary = test_suite.run_all_tests()

    # Show detailed results for failed tests
    if summary["failed"] > 0 or summary["errors"] > 0:
        print(f"\n🔍 Detailed Analysis of Issues:")
        for test_id, result in summary["results"].items():
            if result["status"] != "PASSED":
                details = test_suite.get_test_case_details(test_id)
                print(f"\n❌ {details['name']}:")
                print(f"   Description: {details['description']}")
                print(f"   Steps: {details['transformation_steps']}")
                if "validation_results" in result:
                    failed_checks = [
                        k for k, v in result["validation_results"].items() if not v
                    ]
                    print(f"   Failed checks: {failed_checks}")

    return test_suite, summary


if __name__ == "__main__":
    run_comprehensive_tests()
