"""
Comprehensive test sequences demonstrating each EG transformation rule.
Tests each rule systematically with various EGI configurations.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

from frozendict import frozendict

from egi_core_dau import Cut, Edge, ElementID, RelationalGraphWithCuts, Vertex
from formal_transformation_rules import (
    AreaPolarity,
    FormalTransformationEngine,
    TransformationContext,
    TransformationResult,
)


@dataclass
class TestSequence:
    """A sequence of transformations to test a specific rule."""

    sequence_id: str
    rule_name: str
    description: str
    initial_egi: RelationalGraphWithCuts
    test_steps: List[Dict[str, Any]]
    expected_outcomes: List[Dict[str, Any]]


@dataclass
class TestResult:
    """Result of executing a test sequence."""

    sequence_id: str
    rule_name: str
    steps_executed: int
    steps_successful: int
    final_egi: Optional[RelationalGraphWithCuts]
    step_results: List[TransformationResult]
    overall_success: bool
    error_messages: List[str]


class TransformationRuleTestSuite:
    """Comprehensive test suite for all EG transformation rules."""

    def __init__(self):
        self.engine = FormalTransformationEngine()
        self.test_sequences: List[TestSequence] = []
        self.test_results: List[TestResult] = []

        # Initialize test sequences for each rule
        self._create_dc_plus_tests()
        self._create_dc_minus_tests()
        self._create_insertion_tests()
        self._create_erasure_tests()
        self._create_iteration_tests()
        self._create_deiteration_tests()

    def _create_simple_egi(
        self, vertices: List[str], edges: List[Tuple[str, List[str], str]] = None
    ) -> RelationalGraphWithCuts:
        """Create a simple EGI for testing."""
        vertex_objects = [Vertex(ElementID(v)) for v in vertices]
        edge_objects = []
        nu_mapping = {}
        rel_mapping = {}

        if edges:
            for edge_id, vertex_sequence, relation_name in edges:
                edge_obj = Edge(ElementID(edge_id))
                edge_objects.append(edge_obj)
                nu_mapping[ElementID(edge_id)] = tuple(
                    ElementID(v) for v in vertex_sequence
                )
                rel_mapping[ElementID(edge_id)] = relation_name

        all_elements = [ElementID(v) for v in vertices] + [
            ElementID(e[0]) for e in (edges or [])
        ]

        return RelationalGraphWithCuts(
            V=frozenset(vertex_objects),
            E=frozenset(edge_objects),
            nu=frozendict(nu_mapping),
            sheet=ElementID("sheet"),
            Cut=frozenset(),
            area=frozendict({ElementID("sheet"): frozenset(all_elements)}),
            rel=frozendict(rel_mapping),
        )

    def _create_dc_plus_tests(self):
        """Create test sequences for DC+ (Double Cut Insertion)."""

        # Test 1: DC+ on empty area
        empty_egi = RelationalGraphWithCuts(
            V=frozenset(),
            E=frozenset(),
            nu=frozendict(),
            sheet=ElementID("sheet"),
            Cut=frozenset(),
            area=frozendict({ElementID("sheet"): frozenset()}),
            rel=frozendict(),
        )

        self.test_sequences.append(
            TestSequence(
                sequence_id="dc_plus_empty",
                rule_name="DC+",
                description="Insert double cut on empty sheet",
                initial_egi=empty_egi,
                test_steps=[
                    {
                        "target_area": ElementID("sheet"),
                        "selected_subgraph": frozenset(),
                        "description": "Insert empty double cut",
                    }
                ],
                expected_outcomes=[{"vertices": 0, "edges": 0, "cuts": 2}],
            )
        )

        # Test 2: DC+ around single vertex
        single_vertex_egi = self._create_simple_egi(["A"])

        self.test_sequences.append(
            TestSequence(
                sequence_id="dc_plus_single_vertex",
                rule_name="DC+",
                description="Insert double cut around single vertex",
                initial_egi=single_vertex_egi,
                test_steps=[
                    {
                        "target_area": ElementID("sheet"),
                        "selected_subgraph": frozenset([ElementID("A")]),
                        "description": "Enclose vertex A in double cut",
                    }
                ],
                expected_outcomes=[{"vertices": 1, "edges": 0, "cuts": 2}],
            )
        )

        # Test 3: DC+ around multiple elements
        multi_element_egi = self._create_simple_egi(
            ["A", "B"], [("R", ["A", "B"], "Relation")]
        )

        self.test_sequences.append(
            TestSequence(
                sequence_id="dc_plus_multiple",
                rule_name="DC+",
                description="Insert double cut around multiple elements",
                initial_egi=multi_element_egi,
                test_steps=[
                    {
                        "target_area": ElementID("sheet"),
                        "selected_subgraph": frozenset(
                            [ElementID("A"), ElementID("R")]
                        ),
                        "description": "Enclose vertex A and edge R in double cut",
                    }
                ],
                expected_outcomes=[{"vertices": 2, "edges": 1, "cuts": 2}],
            )
        )

    def _create_dc_minus_tests(self):
        """Create test sequences for DC- (Double Cut Erasure)."""

        # Create EGI with proper double cut structure for DC- testing
        # This creates: sheet -> outer_cut -> inner_cut (empty)
        outer_cut = Cut(ElementID("outer_cut"))
        inner_cut = Cut(ElementID("inner_cut"))

        double_cut_egi = RelationalGraphWithCuts(
            V=frozenset([Vertex(ElementID("P"))]),
            E=frozenset(),
            nu=frozendict(),
            sheet=ElementID("sheet"),
            Cut=frozenset([outer_cut, inner_cut]),
            area=frozendict(
                {
                    ElementID("sheet"): frozenset(
                        [ElementID("P"), ElementID("outer_cut")]
                    ),
                    ElementID("outer_cut"): frozenset([ElementID("inner_cut")]),
                    ElementID("inner_cut"): frozenset(),
                }
            ),
            rel=frozendict(),
        )

        self.test_sequences.append(
            TestSequence(
                sequence_id="dc_minus_basic",
                rule_name="DC-",
                description="Remove double cut pattern",
                initial_egi=double_cut_egi,
                test_steps=[
                    {
                        "target_area": ElementID("sheet"),
                        "selected_subgraph": frozenset([ElementID("outer_cut")]),
                        "description": "Remove double cut pattern",
                    }
                ],
                expected_outcomes=[{"vertices": 1, "edges": 0, "cuts": 0}],
            )
        )

    def _create_insertion_tests(self):
        """Create test sequences for INS (Insertion)."""

        # Create EGI with negative area for insertion
        base_egi = self._create_simple_egi(["A"])

        # Apply DC+ to create negative area
        dc_result = self.engine.apply_rule(
            "DC+", base_egi, ElementID("sheet"), frozenset()
        )

        if dc_result.success:
            self.test_sequences.append(
                TestSequence(
                    sequence_id="ins_negative_area",
                    rule_name="INS",
                    description="Insert vertex in negative area",
                    initial_egi=dc_result.result_egi,
                    test_steps=[
                        {
                            "target_area": ElementID("dc_inner_1"),
                            "selected_subgraph": frozenset([ElementID("new_vertex_B")]),
                            "description": "Insert vertex B in negative area",
                        }
                    ],
                    expected_outcomes=[{"vertices": 2, "edges": 0, "cuts": 2}],
                )
            )

        # Test insertion failure in positive area - this should actually succeed
        # since we're testing that INS correctly rejects positive areas
        positive_egi = self._create_simple_egi(["X", "Y"])

        self.test_sequences.append(
            TestSequence(
                sequence_id="ins_positive_failure",
                rule_name="INS",
                description="Attempt insertion in positive area (should fail)",
                initial_egi=positive_egi,
                test_steps=[
                    {
                        "target_area": ElementID("sheet"),
                        "selected_subgraph": frozenset(
                            [ElementID("Z")]
                        ),  # Simple vertex ID
                        "description": "Try to insert vertex Z in positive area",
                    }
                ],
                expected_outcomes=[
                    {"success": False, "error_contains": "negatively-enclosed"}
                ],
            )
        )

    def _create_erasure_tests(self):
        """Create test sequences for ERA (Erasure)."""

        # Test erasure from positive area
        multi_vertex_egi = self._create_simple_egi(["A", "B", "C"])

        self.test_sequences.append(
            TestSequence(
                sequence_id="era_positive_area",
                rule_name="ERA",
                description="Erase vertex from positive area",
                initial_egi=multi_vertex_egi,
                test_steps=[
                    {
                        "target_area": ElementID("sheet"),
                        "selected_subgraph": frozenset([ElementID("B")]),
                        "description": "Erase vertex B from sheet",
                    }
                ],
                expected_outcomes=[{"vertices": 2, "edges": 0, "cuts": 0}],
            )
        )

        # Test erasure with edge
        edge_egi = self._create_simple_egi(
            ["X", "Y"], [("connects", ["X", "Y"], "Connects")]
        )

        self.test_sequences.append(
            TestSequence(
                sequence_id="era_with_edge",
                rule_name="ERA",
                description="Erase edge from positive area",
                initial_egi=edge_egi,
                test_steps=[
                    {
                        "target_area": ElementID("sheet"),
                        "selected_subgraph": frozenset([ElementID("connects")]),
                        "description": "Erase edge 'connects'",
                    }
                ],
                expected_outcomes=[{"vertices": 2, "edges": 0, "cuts": 0}],
            )
        )

    def _create_iteration_tests(self):
        """Create test sequences for IT+ (Iteration)."""

        # Test iteration of single vertex
        single_egi = self._create_simple_egi(["P"])

        self.test_sequences.append(
            TestSequence(
                sequence_id="it_plus_vertex",
                rule_name="IT+",
                description="Iterate single vertex",
                initial_egi=single_egi,
                test_steps=[
                    {
                        "target_area": ElementID("sheet"),
                        "selected_subgraph": frozenset([ElementID("P")]),
                        "description": "Create copy of vertex P",
                    }
                ],
                expected_outcomes=[{"vertices": 2, "edges": 0, "cuts": 0}],
            )
        )

        # Test iteration of edge with vertices
        relation_egi = self._create_simple_egi(
            ["A", "B"], [("loves", ["A", "B"], "Loves")]
        )

        self.test_sequences.append(
            TestSequence(
                sequence_id="it_plus_relation",
                rule_name="IT+",
                description="Iterate relation with vertices",
                initial_egi=relation_egi,
                test_steps=[
                    {
                        "target_area": ElementID("sheet"),
                        "selected_subgraph": frozenset(
                            [ElementID("A"), ElementID("loves")]
                        ),
                        "description": "Iterate vertex A and edge loves",
                    }
                ],
                expected_outcomes=[{"vertices": 3, "edges": 2, "cuts": 0}],
            )
        )

    def _create_deiteration_tests(self):
        """Create test sequences for IT- (Deiteration)."""

        # Create EGI with duplicated elements for deiteration
        base_egi = self._create_simple_egi(["Q"])

        # First iterate to create duplicate
        iteration_result = self.engine.apply_rule(
            "IT+", base_egi, ElementID("sheet"), frozenset([ElementID("Q")])
        )

        if iteration_result.success:
            self.test_sequences.append(
                TestSequence(
                    sequence_id="it_minus_vertex",
                    rule_name="IT-",
                    description="Deiterate duplicated vertex",
                    initial_egi=iteration_result.result_egi,
                    test_steps=[
                        {
                            "target_area": ElementID("sheet"),
                            "selected_subgraph": frozenset([ElementID("Q_copy")]),
                            "description": "Remove copy of vertex Q",
                        }
                    ],
                    expected_outcomes=[{"vertices": 1, "edges": 0, "cuts": 0}],
                )
            )

    def execute_test_sequence(self, sequence: TestSequence) -> TestResult:
        """Execute a single test sequence."""
        step_results = []
        current_egi = sequence.initial_egi
        error_messages = []

        for i, step in enumerate(sequence.test_steps):
            try:
                result = self.engine.apply_rule(
                    sequence.rule_name,
                    current_egi,
                    step["target_area"],
                    step["selected_subgraph"],
                )

                step_results.append(result)

                if result.success:
                    current_egi = result.result_egi
                else:
                    error_messages.append(f"Step {i+1}: {result.error_message}")

            except Exception as e:
                error_messages.append(f"Step {i+1}: Exception - {str(e)}")
                step_results.append(
                    TransformationResult(
                        success=False,
                        result_egi=None,
                        error_message=str(e),
                        changes_made={},
                    )
                )

        successful_steps = sum(1 for r in step_results if r.success)
        overall_success = successful_steps == len(sequence.test_steps)

        # Check expected outcomes
        if sequence.expected_outcomes:
            expected = sequence.expected_outcomes[-1]  # Check final outcome

            if "success" in expected and not expected["success"]:
                # This test expects failure - success means the rule correctly rejected the operation
                overall_success = not step_results[-1].success
                if "error_contains" in expected:
                    error_text = step_results[-1].error_message or ""
                    overall_success = (
                        overall_success and expected["error_contains"] in error_text
                    )
            else:
                # Check EGI structure
                if current_egi:
                    if "vertices" in expected:
                        overall_success = (
                            overall_success
                            and len(current_egi.V) == expected["vertices"]
                        )
                    if "edges" in expected:
                        overall_success = (
                            overall_success and len(current_egi.E) == expected["edges"]
                        )
                    if "cuts" in expected:
                        overall_success = (
                            overall_success and len(current_egi.Cut) == expected["cuts"]
                        )

        return TestResult(
            sequence_id=sequence.sequence_id,
            rule_name=sequence.rule_name,
            steps_executed=len(sequence.test_steps),
            steps_successful=successful_steps,
            final_egi=current_egi,
            step_results=step_results,
            overall_success=overall_success,
            error_messages=error_messages,
        )

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test sequences and return comprehensive results."""
        print("🧪 EG Transformation Rule Test Suite")
        print("=" * 40)

        rule_results = {}
        total_sequences = len(self.test_sequences)
        total_passed = 0

        for sequence in self.test_sequences:
            print(f"\n🎯 Testing {sequence.rule_name}: {sequence.description}")

            result = self.execute_test_sequence(sequence)
            self.test_results.append(result)

            if sequence.rule_name not in rule_results:
                rule_results[sequence.rule_name] = {
                    "passed": 0,
                    "total": 0,
                    "tests": [],
                }

            rule_results[sequence.rule_name]["total"] += 1
            rule_results[sequence.rule_name]["tests"].append(result)

            if result.overall_success:
                rule_results[sequence.rule_name]["passed"] += 1
                total_passed += 1
                print(
                    f"   ✅ PASS - {result.steps_successful}/{result.steps_executed} steps successful"
                )

                if result.final_egi:
                    print(
                        f"   Result: {len(result.final_egi.V)}V, {len(result.final_egi.E)}E, {len(result.final_egi.Cut)}C"
                    )
            else:
                print(
                    f"   ❌ FAIL - {result.steps_successful}/{result.steps_executed} steps successful"
                )
                for error in result.error_messages:
                    print(f"   Error: {error}")

        # Summary by rule
        print(f"\n📊 Test Results by Rule:")
        for rule_name, results in rule_results.items():
            success_rate = results["passed"] / results["total"] * 100
            print(
                f"   {rule_name}: {results['passed']}/{results['total']} ({success_rate:.0f}%)"
            )

        print(f"\n📋 Overall Summary:")
        print(f"   Total sequences: {total_sequences}")
        print(f"   Passed: {total_passed}")
        print(f"   Success rate: {total_passed/total_sequences*100:.1f}%")

        return {
            "total_sequences": total_sequences,
            "total_passed": total_passed,
            "success_rate": total_passed / total_sequences,
            "rule_results": rule_results,
            "detailed_results": self.test_results,
        }

    def get_rule_summary(self, rule_name: str) -> Dict[str, Any]:
        """Get detailed summary for a specific rule."""
        rule_tests = [r for r in self.test_results if r.rule_name == rule_name]

        if not rule_tests:
            return {"error": f"No tests found for rule {rule_name}"}

        passed = sum(1 for t in rule_tests if t.overall_success)

        return {
            "rule_name": rule_name,
            "tests_run": len(rule_tests),
            "tests_passed": passed,
            "success_rate": passed / len(rule_tests),
            "test_details": [
                {
                    "sequence_id": t.sequence_id,
                    "success": t.overall_success,
                    "steps": f"{t.steps_successful}/{t.steps_executed}",
                    "errors": t.error_messages,
                }
                for t in rule_tests
            ],
        }


def run_comprehensive_rule_tests():
    """Run the comprehensive transformation rule test suite."""
    test_suite = TransformationRuleTestSuite()
    return test_suite.run_all_tests()


if __name__ == "__main__":
    results = run_comprehensive_rule_tests()

    if results["success_rate"] >= 0.8:
        print(f"\n🎉 Transformation rules are working well!")
        print(f"   {results['total_passed']}/{results['total_sequences']} tests passed")
    else:
        print(f"\n⚠️  Some transformation rules need attention.")
        print(f"   Review failed tests for debugging.")
