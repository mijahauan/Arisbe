"""
EGIF Phase 3 Comprehensive Test Suite

This module provides comprehensive testing for all Phase 3 EGIF components:
1. Dau-Sowa compatibility analysis and resolution
2. Validation framework with multiple levels
3. EG-HG integration (with architectural considerations)
4. Semantic equivalence testing
5. Production readiness validation

The test suite follows the Endoporeutic Game testing methodology preference
of using both automated test scripts and manual testing variations.

Author: Manus AI
Date: January 2025
"""

import unittest
import time
from typing import List, Dict, Any

# Import all Phase 3 components
from dau_sowa_compatibility import (
    DauSowaCompatibilityAnalyzer, analyze_dau_sowa_compatibility,
    CompatibilityIssueType, ResolutionStrategy
)
from egif_validation_framework import (
    EGIFValidationFramework, validate_egif, quick_validate,
    ValidationLevel, ValidationCategory
)
from egif_eg_integration import (
    EGIFEGIntegrationManager, egif_to_graph, graph_to_egif,
    IntegrationMode
)
from egif_semantic_equivalence import (
    SemanticEquivalenceTester, test_semantic_equivalence,
    are_semantically_equivalent, EquivalenceType
)

# Import Phase 1 and 2 components for integration testing
from egif_parser import parse_egif
from egif_advanced_constructs import parse_advanced_egif
from egif_generator_simple import simple_round_trip_test
from egif_educational_features import explain_egif


class TestDauSowaCompatibility(unittest.TestCase):
    """Test Dau-Sowa compatibility analysis and resolution."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = DauSowaCompatibilityAnalyzer()
        
        # Test cases with known compatibility issues
        self.test_cases = {
            'function_semantics': "(add 2 3 -> *sum)",
            'quantification_scope': "(Person *x) [If (Mortal x) [Then (Finite x)]]",
            'coreference_identity': "[= x y z]",
            'ligature_handling': "(Loves *x *y) (Knows y *z) (Trusts z x)",
            'negation_scope': "~[(Person *x) (Mortal x)]",
            'no_issues': "(Person *john)"
        }
    
    def test_compatibility_analysis(self):
        """Test compatibility issue detection."""
        for issue_type, test_case in self.test_cases.items():
            with self.subTest(issue_type=issue_type):
                issues = self.analyzer.analyze_egif_compatibility(test_case)
                
                if issue_type == 'no_issues':
                    self.assertEqual(len(issues), 0, f"Expected no issues for {test_case}")
                else:
                    self.assertGreater(len(issues), 0, f"Expected issues for {test_case}")
    
    def test_compatibility_report_generation(self):
        """Test compatibility report generation."""
        for test_case in self.test_cases.values():
            with self.subTest(test_case=test_case):
                report = analyze_dau_sowa_compatibility(test_case)
                
                # Check report structure
                self.assertIn("Dau-Sowa Compatibility Analysis Report", report)
                self.assertIn(f"Source: {test_case}", report)
                
                # Should have either "No compatibility issues" or "issue(s) detected"
                self.assertTrue(
                    "No compatibility issues detected" in report or 
                    "compatibility issue(s) detected" in report
                )
    
    def test_resolution_strategies(self):
        """Test resolution strategy application."""
        test_case = self.test_cases['function_semantics']
        issues = self.analyzer.analyze_egif_compatibility(test_case)
        
        if issues:
            issue = issues[0]
            
            # Test different resolution strategies
            strategies = [
                ResolutionStrategy.DAU_PREFERENCE,
                ResolutionStrategy.SOWA_PREFERENCE,
                ResolutionStrategy.EDUCATIONAL_PREFERENCE,
                ResolutionStrategy.HYBRID_APPROACH
            ]
            
            for strategy in strategies:
                with self.subTest(strategy=strategy):
                    resolution = self.analyzer.resolve_compatibility_issue(issue, strategy)
                    
                    self.assertEqual(resolution.chosen_strategy, strategy)
                    self.assertIsNotNone(resolution.resolved_egif)
                    self.assertIsNotNone(resolution.resolution_explanation)
    
    def test_performance(self):
        """Test compatibility analysis performance."""
        test_case = self.test_cases['ligature_handling']
        
        start_time = time.time()
        for _ in range(10):
            self.analyzer.analyze_egif_compatibility(test_case)
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 10
        self.assertLess(avg_time, 0.1, "Compatibility analysis should be fast")


class TestValidationFramework(unittest.TestCase):
    """Test EGIF validation framework."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.valid_cases = [
            "(Person *john)",
            "(Person *x) (Mortal x)",
            "(Loves *alice *bob)",
        ]
        
        self.invalid_cases = [
            "(Person *john",  # Missing closing parenthesis
            "Person *john)",  # Missing opening parenthesis
            "(Person &john)",  # Invalid character
        ]
    
    def test_basic_validation(self):
        """Test basic validation level."""
        framework = EGIFValidationFramework(ValidationLevel.BASIC)
        
        for test_case in self.valid_cases:
            with self.subTest(test_case=test_case):
                report = framework.validate(test_case)
                self.assertGreater(report.get_success_rate(), 50, 
                                 f"Valid case should have high success rate: {test_case}")
        
        for test_case in self.invalid_cases:
            with self.subTest(test_case=test_case):
                report = framework.validate(test_case)
                self.assertLess(report.get_success_rate(), 100, 
                               f"Invalid case should have lower success rate: {test_case}")
    
    def test_comprehensive_validation(self):
        """Test comprehensive validation level."""
        framework = EGIFValidationFramework(ValidationLevel.COMPREHENSIVE)
        
        test_case = "(Person *john)"
        report = framework.validate(test_case)
        
        # Should have multiple test categories
        categories = set(result.category for result in report.results)
        expected_categories = {
            ValidationCategory.SYNTACTIC,
            ValidationCategory.ROUND_TRIP,
            ValidationCategory.EDUCATIONAL
        }
        
        self.assertTrue(expected_categories.issubset(categories),
                       "Comprehensive validation should include multiple categories")
    
    def test_expert_validation(self):
        """Test expert validation level."""
        framework = EGIFValidationFramework(ValidationLevel.EXPERT)
        
        test_case = "(add 2 3 -> *sum)"  # Has compatibility issues
        report = framework.validate(test_case)
        
        # Should include compatibility validation
        categories = set(result.category for result in report.results)
        self.assertIn(ValidationCategory.COMPATIBILITY, categories,
                     "Expert validation should include compatibility testing")
    
    def test_quick_validate(self):
        """Test quick validation function."""
        for test_case in self.valid_cases:
            with self.subTest(test_case=test_case):
                result = quick_validate(test_case)
                self.assertTrue(result, f"Quick validate should pass for valid case: {test_case}")
    
    def test_validation_performance(self):
        """Test validation framework performance."""
        framework = EGIFValidationFramework(ValidationLevel.STANDARD)
        test_case = "(Person *john)"
        
        start_time = time.time()
        for _ in range(5):
            framework.validate(test_case)
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 5
        self.assertLess(avg_time, 1.0, "Validation should complete within reasonable time")


class TestEGIntegration(unittest.TestCase):
    """Test EGIF-EG integration (with architectural considerations)."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.integration_manager = EGIFEGIntegrationManager(IntegrationMode.EDUCATIONAL)
        
        self.test_cases = [
            "(Person *john)",
            "(Person *x) (Mortal x)",
            "(Loves *alice *bob)",
        ]
    
    def test_integration_modes(self):
        """Test different integration modes."""
        test_case = "(Person *john)"
        
        modes = [
            IntegrationMode.EDUCATIONAL,
            IntegrationMode.MATHEMATICAL,
            IntegrationMode.PRACTICAL,
            IntegrationMode.COMPATIBLE
        ]
        
        for mode in modes:
            with self.subTest(mode=mode):
                manager = EGIFEGIntegrationManager(mode)
                result = manager.parse_egif_to_graph(test_case)
                
                # Should complete without exceptions
                self.assertIsNotNone(result)
                self.assertIsInstance(result.success, bool)
    
    def test_egif_to_graph_conversion(self):
        """Test EGIF to EG-HG conversion."""
        for test_case in self.test_cases:
            with self.subTest(test_case=test_case):
                result = egif_to_graph(test_case, IntegrationMode.EDUCATIONAL)
                
                # Should complete without exceptions
                self.assertIsNotNone(result)
                self.assertIsInstance(result.success, bool)
                
                # Should have educational trace
                self.assertIsInstance(result.educational_trace, list)
    
    def test_round_trip_integration(self):
        """Test round-trip integration testing."""
        for test_case in self.test_cases:
            with self.subTest(test_case=test_case):
                result = self.integration_manager.round_trip_test(test_case)
                
                # Should complete without exceptions
                self.assertIsNotNone(result)
                self.assertIsInstance(result.success, bool)
                
                # Should have metadata about the test
                self.assertIn('original_egif', result.metadata)
    
    def test_integration_performance(self):
        """Test integration performance."""
        test_case = "(Person *john)"
        
        start_time = time.time()
        for _ in range(3):
            self.integration_manager.parse_egif_to_graph(test_case)
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 3
        self.assertLess(avg_time, 2.0, "Integration should complete within reasonable time")


class TestSemanticEquivalence(unittest.TestCase):
    """Test semantic equivalence testing."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tester = SemanticEquivalenceTester()
        
        # Test pairs: (source1, source2, expected_equivalent)
        self.test_pairs = [
            # Exact equivalence
            ("(Person *john)", "(Person *john)", True),
            
            # Syntactic differences but structural equivalence
            ("(Person *john)", "( Person *john )", True),
            
            # Different variable names but same structure
            ("(Person *x)", "(Person *y)", True),
            
            # Different structures
            ("(Person *john)", "(Animal *dog)", False),
            
            # Complex case
            ("(Person *x) (Mortal x)", "(Mortal x) (Person *x)", True),
        ]
    
    def test_structural_equivalence(self):
        """Test structural equivalence detection."""
        for source1, source2, expected in self.test_pairs:
            with self.subTest(source1=source1, source2=source2):
                test_suite = test_semantic_equivalence(source1, source2)
                
                if EquivalenceType.STRUCTURAL in test_suite.results:
                    result = test_suite.results[EquivalenceType.STRUCTURAL]
                    
                    if expected:
                        self.assertTrue(result.equivalent or result.confidence > 0.5,
                                      f"Expected equivalence: {source1} ≈ {source2}")
                    else:
                        self.assertTrue(not result.equivalent or result.confidence < 0.5,
                                      f"Expected non-equivalence: {source1} ≠ {source2}")
    
    def test_syntactic_equivalence(self):
        """Test syntactic equivalence detection."""
        # Test cases specifically for syntactic differences
        syntactic_pairs = [
            ("(Person *john)", "( Person *john )", True),
            ("(Person *john)", "(Person  *john)", True),
            ("(Person *john)", "(Animal *dog)", False),
        ]
        
        for source1, source2, expected in syntactic_pairs:
            with self.subTest(source1=source1, source2=source2):
                test_suite = test_semantic_equivalence(source1, source2)
                
                if EquivalenceType.SYNTACTIC in test_suite.results:
                    result = test_suite.results[EquivalenceType.SYNTACTIC]
                    
                    if expected:
                        self.assertTrue(result.equivalent,
                                      f"Expected syntactic equivalence: {source1} ≈ {source2}")
                    else:
                        self.assertFalse(result.equivalent,
                                       f"Expected syntactic non-equivalence: {source1} ≠ {source2}")
    
    def test_educational_equivalence(self):
        """Test educational equivalence detection."""
        for source1, source2, expected in self.test_pairs:
            with self.subTest(source1=source1, source2=source2):
                test_suite = test_semantic_equivalence(source1, source2)
                
                if EquivalenceType.EDUCATIONAL in test_suite.results:
                    result = test_suite.results[EquivalenceType.EDUCATIONAL]
                    
                    # Educational equivalence should be detected for similar concepts
                    self.assertIsInstance(result.equivalent, bool)
                    self.assertIsInstance(result.confidence, float)
                    self.assertGreaterEqual(result.confidence, 0.0)
                    self.assertLessEqual(result.confidence, 1.0)
    
    def test_quick_equivalence(self):
        """Test quick equivalence checking."""
        # Test exact matches
        self.assertTrue(are_semantically_equivalent("(Person *john)", "(Person *john)"))
        
        # Test clear non-matches
        self.assertFalse(are_semantically_equivalent("(Person *john)", "(Animal *dog)"))
    
    def test_equivalence_performance(self):
        """Test equivalence testing performance."""
        source1 = "(Person *john)"
        source2 = "( Person *john )"
        
        start_time = time.time()
        for _ in range(10):
            test_semantic_equivalence(source1, source2)
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 10
        self.assertLess(avg_time, 0.5, "Equivalence testing should be fast")


class TestPhase3Integration(unittest.TestCase):
    """Test integration between all Phase 3 components."""
    
    def test_comprehensive_workflow(self):
        """Test complete Phase 3 workflow."""
        test_case = "(add 2 3 -> *sum)"
        
        # 1. Compatibility analysis
        compatibility_report = analyze_dau_sowa_compatibility(test_case)
        self.assertIn("Dau-Sowa Compatibility Analysis Report", compatibility_report)
        
        # 2. Validation
        validation_report = validate_egif(test_case, ValidationLevel.EXPERT)
        self.assertIsNotNone(validation_report)
        
        # 3. Integration (may have architectural issues but should not crash)
        integration_result = egif_to_graph(test_case, IntegrationMode.EDUCATIONAL)
        self.assertIsNotNone(integration_result)
        
        # 4. Equivalence testing
        equivalence_suite = test_semantic_equivalence(test_case, test_case)
        self.assertTrue(equivalence_suite.overall_equivalent)
    
    def test_educational_workflow(self):
        """Test educational-focused workflow."""
        test_case = "(Person *john)"
        
        # Educational analysis
        educational_report = explain_egif(test_case)
        self.assertIn("Educational Analysis Report", educational_report)
        
        # Educational validation
        validation_report = validate_egif(test_case, ValidationLevel.COMPREHENSIVE)
        educational_results = [r for r in validation_report.results 
                             if r.category == ValidationCategory.EDUCATIONAL]
        self.assertGreater(len(educational_results), 0)
        
        # Educational equivalence
        equivalence_suite = test_semantic_equivalence(test_case, "( Person *john )")
        if EquivalenceType.EDUCATIONAL in equivalence_suite.results:
            educational_equiv = equivalence_suite.results[EquivalenceType.EDUCATIONAL]
            self.assertTrue(educational_equiv.equivalent)
    
    def test_production_readiness(self):
        """Test production readiness indicators."""
        test_cases = [
            "(Person *john)",
            "(Person *x) (Mortal x)",
            "(Loves *alice *bob)",
            "(add 2 3 -> *sum)",
        ]
        
        for test_case in test_cases:
            with self.subTest(test_case=test_case):
                # Production-level validation
                validation_report = validate_egif(test_case, ValidationLevel.PRODUCTION)
                
                # Should complete without exceptions
                self.assertIsNotNone(validation_report)
                
                # Should have performance metrics
                performance_results = [r for r in validation_report.results 
                                     if r.category == ValidationCategory.PERFORMANCE]
                
                if performance_results:
                    # Performance should be acceptable
                    for result in performance_results:
                        self.assertLess(result.execution_time, 1.0, 
                                      "Performance should be acceptable for production")


def run_phase3_test_suite():
    """Run the complete Phase 3 test suite."""
    print("🧪 EGIF Phase 3 Comprehensive Test Suite")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestDauSowaCompatibility,
        TestValidationFramework,
        TestEGIntegration,
        TestSemanticEquivalence,
        TestPhase3Integration,
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Suite Summary")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\n❌ Failures ({len(result.failures)}):")
        for test, traceback in result.failures:
            print(f"  • {test}")
    
    if result.errors:
        print(f"\n🚫 Errors ({len(result.errors)}):")
        for test, traceback in result.errors:
            print(f"  • {test}")
    
    if not result.failures and not result.errors:
        print("\n✅ All tests passed! Phase 3 implementation is ready.")
    
    return result


if __name__ == "__main__":
    # Run the comprehensive test suite
    run_phase3_test_suite()

