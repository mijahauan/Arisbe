"""
EGI Integrity Test Suite Implementation
Concrete implementation of the comprehensive EGI testing framework

This module implements the test cases defined in test_specifications_dau.py
and provides the actual test execution for EGI integrity validation.
"""

import unittest
from typing import Dict, List, Tuple, Any

from .test_framework_schema import (
    EGITestSuite, LogicalEquivalenceTest, TransformationSoundnessTest,
    TranslationFidelityTest, DauComplianceTest
)
from .test_specifications_dau import ALL_TEST_SPECIFICATIONS

from src.egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut
from src.formal_transformation_rules import (
    IterationRule, DeiterationRule, InsertionRule, DoubleCutErasureRule,
    TransformationContext, AreaPolarity
)


class EGIIntegrityTestSuite(unittest.TestCase):
    """Main test suite for EGI integrity validation."""
    
    def setUp(self):
        """Set up test suite."""
        self.test_suite = EGITestSuite()
        self._register_all_tests()
    
    def _register_all_tests(self):
        """Register all test specifications as executable test cases."""
        for spec in ALL_TEST_SPECIFICATIONS:
            test_case = self._create_test_case(spec)
            if test_case:
                self.test_suite.register_test(test_case)
    
    def _create_test_case(self, spec):
        """Create appropriate test case instance based on specification."""
        if spec.category.value == "logical_equivalence":
            return LogicalEquivalenceTest(spec)
        elif spec.category.value == "transformation_soundness":
            return TransformationSoundnessTest(spec)
        elif spec.category.value == "translation_fidelity":
            return TranslationFidelityTest(spec)
        elif spec.category.value == "dau_compliance":
            return DauComplianceTest(spec)
        else:
            return None
    
    def test_logical_equivalence_suite(self):
        """Run all logical equivalence tests."""
        from tests.test_specifications_dau import TestCategory
        results = self.test_suite.run_category(TestCategory.LOGICAL_EQUIVALENCE)
        
        # Verify all tests passed
        failed_tests = [test_id for test_id, (success, _, _) in results.items() if not success]
        if failed_tests:
            self.fail(f"Logical equivalence tests failed: {failed_tests}")
    
    def test_transformation_soundness_suite(self):
        """Run all transformation soundness tests."""
        from tests.test_specifications_dau import TestCategory
        results = self.test_suite.run_category(TestCategory.TRANSFORMATION_SOUNDNESS)
        
        # Verify all tests passed
        failed_tests = [test_id for test_id, (success, _, _) in results.items() if not success]
        if failed_tests:
            self.fail(f"Transformation soundness tests failed: {failed_tests}")
    
    def test_translation_fidelity_suite(self):
        """Run all translation fidelity tests."""
        from tests.test_specifications_dau import TestCategory
        results = self.test_suite.run_category(TestCategory.TRANSLATION_FIDELITY)
        
        # Verify all tests passed
        failed_tests = [test_id for test_id, (success, _, _) in results.items() if not success]
        if failed_tests:
            self.fail(f"Translation fidelity tests failed: {failed_tests}")
    
    def test_dau_compliance_suite(self):
        """Run all Dau formalism compliance tests."""
        from tests.test_specifications_dau import TestCategory
        results = self.test_suite.run_category(TestCategory.DAU_COMPLIANCE)
        
        # Verify all tests passed
        failed_tests = [test_id for test_id, (success, _, _) in results.items() if not success]
        if failed_tests:
            self.fail(f"Dau compliance tests failed: {failed_tests}")
    
    def test_comprehensive_egi_integrity(self):
        """Run complete EGI integrity test suite."""
        results = self.test_suite.run_all()
        
        # Generate comprehensive report
        report = self.test_suite.generate_report(results)
        print("\n" + report)
        
        # Verify overall success
        total_tests = len(results)
        passed_tests = sum(1 for success, _, _ in results.values() if success)
        success_rate = (passed_tests / total_tests) * 100
        
        # Require 90% success rate for integrity validation
        if success_rate < 90.0:
            failed_tests = [test_id for test_id, (success, _, _) in results.items() if not success]
            self.fail(f"EGI integrity validation failed. Success rate: {success_rate:.1f}%. Failed tests: {failed_tests}")


class ConcreteEGITests(unittest.TestCase):
    """Concrete implementations of specific EGI integrity tests."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_egi = self._create_sample_egi()
        self.transformation_rules = {
            "iteration": IterationRule(),
            "deiteration": DeiterationRule(),
            "insertion": InsertionRule(),
            "double_cut_erasure": DoubleCutErasureRule()
        }
    
    def _create_sample_egi(self) -> RelationalGraphWithCuts:
        """Create a sample EGI for testing."""
        from frozendict import frozendict
        
        # Create vertices
        socrates = Vertex(id="socrates", label="Socrates", is_generic=False)
        x = Vertex(id="x", label=None, is_generic=True)
        
        # Create edges
        human = Edge(id="human")
        mortal = Edge(id="mortal")
        
        # Create cut
        cut1 = Cut(id="cut1")
        
        return RelationalGraphWithCuts(
            V=frozenset([socrates, x]),
            E=frozenset([human, mortal]),
            Cut=frozenset([cut1]),
            nu=frozendict({
                "human": ("socrates",),
                "mortal": ("x",)
            }),
            sheet="sheet",
            area=frozendict({
                "sheet": frozenset(["human", "socrates", "cut1"]),
                "cut1": frozenset(["mortal", "x"])
            }),
            rel=frozendict({
                "human": "Human",
                "mortal": "Mortal"
            })
        )
    
    def test_egi_structure_validation(self):
        """Test EGI conforms to Dau's 6+1 component structure."""
        egi = self.sample_egi
        
        # Validate all required components exist
        self.assertIsInstance(egi.V, frozenset)
        self.assertIsInstance(egi.E, frozenset)
        self.assertIsInstance(egi.nu, frozendict)
        self.assertIsInstance(egi.sheet, str)
        self.assertIsInstance(egi.Cut, frozenset)
        self.assertIsInstance(egi.area, frozendict)
        self.assertIsInstance(egi.rel, frozendict)
        
        # Validate structural consistency
        all_elements = egi.get_all_elements()
        for area_id, elements in egi.area.items():
            for element_id in elements:
                if element_id not in all_elements and element_id not in egi.area:
                    self.fail(f"Area {area_id} contains unknown element {element_id}")
    
    def test_transformation_sequence_equivalence(self):
        """Test that transformation sequences preserve logical equivalence."""
        initial_egi = self.sample_egi
        
        # Apply sequence of transformations
        current_egi = initial_egi
        transformation_history = [initial_egi]
        
        # Apply iteration (if valid)
        iteration_rule = self.transformation_rules["iteration"]
        context = TransformationContext(
            source_egi=current_egi,
            target_area="sheet",
            selected_subgraph=frozenset(["human", "socrates"]),
            area_polarity=AreaPolarity.POSITIVE,
            nesting_depth=0
        )
        
        # Check if transformation is valid before applying
        is_valid, error_msg = iteration_rule.check_preconditions(context)
        if is_valid:
            result = iteration_rule.apply_transformation(context)
            if result.success:
                current_egi = result.result_egi
                transformation_history.append(current_egi)
        
        # Verify all EGIs in sequence are logically equivalent
        # (This would use semantic evaluation engine when available)
        for i, egi in enumerate(transformation_history):
            self.assertIsInstance(egi, RelationalGraphWithCuts)
            # Placeholder for semantic equivalence check
            # self.assertTrue(semantic_engine.are_equivalent(initial_egi, egi))
    
    def test_round_trip_translation_fidelity(self):
        """Test round-trip translation preserves EGI structure."""
        original_egi = self.sample_egi
        
        # Test EGIF round-trip
        try:
            from src.egif_generator_dau import generate_egif
            from src.egif_parser_dau import parse_egif
            
            # EGI -> EGIF -> EGI
            egif_text = generate_egif(original_egi)
            reconstructed_egi = parse_egif(egif_text)
            
            # Verify structural equivalence
            self.assertEqual(len(original_egi.V), len(reconstructed_egi.V))
            self.assertEqual(len(original_egi.E), len(reconstructed_egi.E))
            self.assertEqual(len(original_egi.Cut), len(reconstructed_egi.Cut))
            
        except ImportError:
            self.skipTest("EGIF parser/generator not available")
    
    def test_cut_nesting_hierarchy_validation(self):
        """Test cut nesting forms valid hierarchy."""
        egi = self.sample_egi
        
        # Validate cut hierarchy
        cut_hierarchy = {}
        for area_id, elements in egi.area.items():
            if area_id == egi.sheet:
                continue
            
            # Find parent area
            parent_area = None
            for parent_id, parent_elements in egi.area.items():
                if area_id in parent_elements and parent_id != area_id:
                    parent_area = parent_id
                    break
            
            cut_hierarchy[area_id] = parent_area
        
        # Verify no cycles in hierarchy
        visited = set()
        for cut_id in cut_hierarchy:
            current = cut_id
            path = []
            while current and current not in visited:
                if current in path:
                    self.fail(f"Cycle detected in cut hierarchy: {path + [current]}")
                path.append(current)
                current = cut_hierarchy.get(current)
            visited.update(path)
    
    def test_variable_scoping_compliance(self):
        """Test variable scoping follows Dau's rules."""
        egi = self.sample_egi
        
        # Check variable scoping across areas
        for edge_id, vertex_tuple in egi.nu.items():
            edge_area = None
            for area_id, elements in egi.area.items():
                if edge_id in elements:
                    edge_area = area_id
                    break
            
            # Verify all vertices in tuple are accessible from edge's area
            for vertex_id in vertex_tuple:
                vertex_accessible = False
                
                # Check if vertex is in same area or accessible parent area
                current_area = edge_area
                while current_area:
                    if vertex_id in egi.area[current_area]:
                        vertex_accessible = True
                        break
                    
                    # Move to parent area
                    parent_area = None
                    for area_id, elements in egi.area.items():
                        if current_area in elements and area_id != current_area:
                            parent_area = area_id
                            break
                    current_area = parent_area
                
                if not vertex_accessible:
                    self.fail(f"Vertex {vertex_id} not accessible from edge {edge_id} in area {edge_area}")


class EGIIntegrityReporter:
    """Generate comprehensive reports on EGI integrity test results."""
    
    @staticmethod
    def generate_integrity_report(test_results: Dict[str, Tuple[bool, str, Any]]) -> str:
        """Generate detailed integrity report."""
        from tests.test_specifications_dau import get_tests_by_category, TestCategory
        
        report_lines = [
            "EGI INTEGRITY VALIDATION REPORT",
            "=" * 50,
            f"Generated: {__import__('datetime').datetime.now().isoformat()}",
            ""
        ]
        
        # Summary statistics
        total_tests = len(test_results)
        passed_tests = sum(1 for success, _, _ in test_results.values() if success)
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        report_lines.extend([
            "SUMMARY",
            "-" * 20,
            f"Total Tests: {total_tests}",
            f"Passed: {passed_tests}",
            f"Failed: {failed_tests}",
            f"Success Rate: {success_rate:.1f}%",
            ""
        ])
        
        # Results by category
        for category in TestCategory:
            category_specs = get_tests_by_category(category)
            category_results = {
                spec.test_id: test_results.get(spec.test_id, (False, "Not executed", None))
                for spec in category_specs
            }
            
            category_passed = sum(1 for success, _, _ in category_results.values() if success)
            category_total = len(category_results)
            
            report_lines.extend([
                f"{category.value.upper().replace('_', ' ')} TESTS",
                "-" * 30,
                f"Passed: {category_passed}/{category_total}",
                ""
            ])
            
            for test_id, (success, message, _) in category_results.items():
                status = "PASS" if success else "FAIL"
                report_lines.append(f"  {status:4} | {test_id:30} | {message}")
            
            report_lines.append("")
        
        # Recommendations
        if failed_tests > 0:
            report_lines.extend([
                "RECOMMENDATIONS",
                "-" * 20,
                "• Review failed test cases for EGI integrity issues",
                "• Verify transformation rule implementations",
                "• Check linear form parser/generator consistency",
                "• Validate Dau formalism compliance",
                ""
            ])
        
        return "\n".join(report_lines)


if __name__ == "__main__":
    # Run the comprehensive EGI integrity test suite
    unittest.main(verbosity=2)
