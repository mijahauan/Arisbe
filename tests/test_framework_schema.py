"""
Comprehensive EGI Testing Framework Schema
Based on Dau's formalism chapters 11-21

This module defines the testing architecture for ensuring EGI integrity
across transformations, translations, and semantic equivalence.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from src.egi_core_dau import RelationalGraphWithCuts


class TestCategory(Enum):
    """Categories of EGI tests based on Dau's formalism."""
    
    LOGICAL_EQUIVALENCE = "logical_equivalence"
    TRANSFORMATION_SOUNDNESS = "transformation_soundness" 
    TRANSLATION_FIDELITY = "translation_fidelity"
    DAU_COMPLIANCE = "dau_compliance"
    SEMANTIC_PRESERVATION = "semantic_preservation"


class TestType(Enum):
    """Type of test probe."""
    
    SUCCESS_VALIDATION = "success_validation"  # Valid input should succeed
    ERROR_DETECTION = "error_detection"        # Invalid input should fail
    EQUIVALENCE_CHECK = "equivalence_check"    # Two items should be equivalent
    INVARIANT_CHECK = "invariant_check"        # Property should be preserved


@dataclass
class DauReference:
    """Reference to Dau's formalism."""
    
    chapter: int
    section: Optional[str] = None
    theorem: Optional[str] = None
    definition: Optional[str] = None
    page: Optional[int] = None
    
    def __str__(self) -> str:
        ref = f"Chapter {self.chapter}"
        if self.section:
            ref += f", Section {self.section}"
        if self.theorem:
            ref += f", Theorem {self.theorem}"
        if self.definition:
            ref += f", Definition {self.definition}"
        if self.page:
            ref += f" (p. {self.page})"
        return ref


@dataclass
class TestSpecification:
    """Complete specification for an EGI test."""
    
    # Identification
    test_id: str
    title: str
    category: TestCategory
    test_type: TestType
    
    # Documentation
    rationale: str
    dau_reference: DauReference
    description: str
    expected_result: str
    
    # Test data
    input_data: Dict[str, Any]
    expected_output: Optional[Any] = None
    validation_criteria: Optional[Dict[str, Any]] = None
    
    # Metadata
    priority: str = "medium"  # high, medium, low
    complexity: str = "simple"  # simple, moderate, complex
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class EGITestCase(ABC):
    """Abstract base class for EGI test cases."""
    
    def __init__(self, spec: TestSpecification):
        self.spec = spec
    
    @abstractmethod
    def setup(self) -> None:
        """Set up test fixtures."""
        pass
    
    @abstractmethod
    def execute(self) -> Any:
        """Execute the test."""
        pass
    
    @abstractmethod
    def validate(self, result: Any) -> Tuple[bool, str]:
        """Validate test result."""
        pass
    
    def run(self) -> Tuple[bool, str, Any]:
        """Run complete test cycle."""
        try:
            self.setup()
            result = self.execute()
            success, message = self.validate(result)
            return success, message, result
        except Exception as e:
            return False, f"Test failed with exception: {str(e)}", None


class LogicalEquivalenceTest(EGITestCase):
    """Test logical equivalence between EGIs."""
    
    def setup(self) -> None:
        self.egi1 = self.spec.input_data["egi1"]
        self.egi2 = self.spec.input_data["egi2"]
    
    def execute(self) -> bool:
        # Use semantic evaluation engine to check equivalence
        from src.dau_semantic_evaluation_tests import SemanticEvaluationEngine
        engine = SemanticEvaluationEngine()
        return engine.are_logically_equivalent(self.egi1, self.egi2)
    
    def validate(self, result: bool) -> Tuple[bool, str]:
        expected = self.spec.expected_output
        if result == expected:
            return True, f"Logical equivalence correctly determined: {result}"
        else:
            return False, f"Expected {expected}, got {result}"


class TransformationSoundnessTest(EGITestCase):
    """Test that transformations preserve semantic meaning."""
    
    def setup(self) -> None:
        self.input_egi = self.spec.input_data["input_egi"]
        self.transformation_rule = self.spec.input_data["transformation_rule"]
        self.transformation_context = self.spec.input_data.get("context")
    
    def execute(self) -> Tuple[RelationalGraphWithCuts, bool]:
        # Apply transformation
        result = self.transformation_rule.apply_transformation(
            self.transformation_context or self._create_context()
        )
        
        if not result.success:
            return None, False
        
        # Check semantic equivalence
        from src.dau_semantic_evaluation_tests import SemanticEvaluationEngine
        engine = SemanticEvaluationEngine()
        equivalent = engine.are_logically_equivalent(
            self.input_egi, result.result_egi
        )
        
        return result.result_egi, equivalent
    
    def validate(self, result: Tuple[RelationalGraphWithCuts, bool]) -> Tuple[bool, str]:
        output_egi, is_equivalent = result
        
        if output_egi is None:
            return False, "Transformation failed to produce output"
        
        if not is_equivalent:
            return False, "Transformation did not preserve semantic equivalence"
        
        return True, "Transformation preserved semantic equivalence"
    
    def _create_context(self):
        from src.formal_transformation_rules import TransformationContext, AreaPolarity
        return TransformationContext(
            source_egi=self.input_egi,
            target_area="sheet",
            selected_subgraph=frozenset(),
            area_polarity=AreaPolarity.POSITIVE,
            nesting_depth=0
        )


class TranslationFidelityTest(EGITestCase):
    """Test round-trip translation fidelity between linear forms."""
    
    def setup(self) -> None:
        self.source_format = self.spec.input_data["source_format"]
        self.target_format = self.spec.input_data["target_format"]
        self.source_text = self.spec.input_data["source_text"]
    
    def execute(self) -> Tuple[str, RelationalGraphWithCuts, str]:
        # Parse source format to EGI
        source_egi = self._parse_format(self.source_format, self.source_text)
        
        # Generate target format from EGI
        target_text = self._generate_format(self.target_format, source_egi)
        
        return self.source_text, source_egi, target_text
    
    def validate(self, result: Tuple[str, RelationalGraphWithCuts, str]) -> Tuple[bool, str]:
        source_text, egi, target_text = result
        
        # Parse target back to EGI
        target_egi = self._parse_format(self.target_format, target_text)
        
        # Check structural equivalence
        from src.graph_isomorphism_engine import GraphIsomorphismEngine
        engine = GraphIsomorphismEngine()
        iso_result = engine.test_subgraph_isomorphism(
            egi, frozenset(egi.get_all_elements()),
            frozenset(target_egi.get_all_elements())
        )
        
        if iso_result.is_isomorphic:
            return True, f"Round-trip translation preserved structure"
        else:
            return False, f"Round-trip translation lost fidelity: {iso_result.reason}"
    
    def _parse_format(self, format_name: str, text: str) -> RelationalGraphWithCuts:
        if format_name == "EGIF":
            from src.egif_parser_dau import parse_egif
            return parse_egif(text)
        elif format_name == "CGIF":
            from src.cgif_parser_dau import parse_cgif
            return parse_cgif(text)
        elif format_name == "CLIF":
            from src.clif_parser_dau import parse_clif
            return parse_clif(text)
        else:
            raise ValueError(f"Unknown format: {format_name}")
    
    def _generate_format(self, format_name: str, egi: RelationalGraphWithCuts) -> str:
        if format_name == "EGIF":
            from src.egif_generator_dau import generate_egif
            return generate_egif(egi)
        elif format_name == "CGIF":
            from src.cgif_generator_dau import generate_cgif
            return generate_cgif(egi)
        elif format_name == "CLIF":
            from src.clif_generator_dau import generate_clif
            return generate_clif(egi)
        else:
            raise ValueError(f"Unknown format: {format_name}")


class DauComplianceTest(EGITestCase):
    """Test compliance with specific Dau formalism requirements."""
    
    def setup(self) -> None:
        self.test_function = self.spec.input_data["test_function"]
        self.test_args = self.spec.input_data.get("test_args", [])
        self.test_kwargs = self.spec.input_data.get("test_kwargs", {})
    
    def execute(self) -> Any:
        return self.test_function(*self.test_args, **self.test_kwargs)
    
    def validate(self, result: Any) -> Tuple[bool, str]:
        expected = self.spec.expected_output
        validation_criteria = self.spec.validation_criteria or {}
        
        if "exact_match" in validation_criteria:
            if result == expected:
                return True, "Exact match achieved"
            else:
                return False, f"Expected {expected}, got {result}"
        
        if "type_check" in validation_criteria:
            expected_type = validation_criteria["type_check"]
            if isinstance(result, expected_type):
                return True, f"Type check passed: {type(result)}"
            else:
                return False, f"Expected type {expected_type}, got {type(result)}"
        
        # Default validation
        return True, "Test completed successfully"


class EGITestSuite:
    """Collection of EGI tests organized by category."""
    
    def __init__(self):
        self.tests: Dict[TestCategory, List[EGITestCase]] = {
            category: [] for category in TestCategory
        }
        self.test_registry: Dict[str, EGITestCase] = {}
    
    def register_test(self, test_case: EGITestCase) -> None:
        """Register a test case."""
        category = test_case.spec.category
        self.tests[category].append(test_case)
        self.test_registry[test_case.spec.test_id] = test_case
    
    def run_category(self, category: TestCategory) -> Dict[str, Tuple[bool, str, Any]]:
        """Run all tests in a category."""
        results = {}
        for test_case in self.tests[category]:
            results[test_case.spec.test_id] = test_case.run()
        return results
    
    def run_all(self) -> Dict[str, Tuple[bool, str, Any]]:
        """Run all registered tests."""
        results = {}
        for category in TestCategory:
            category_results = self.run_category(category)
            results.update(category_results)
        return results
    
    def get_test_by_id(self, test_id: str) -> Optional[EGITestCase]:
        """Get test case by ID."""
        return self.test_registry.get(test_id)
    
    def generate_report(self, results: Dict[str, Tuple[bool, str, Any]]) -> str:
        """Generate test report."""
        total_tests = len(results)
        passed_tests = sum(1 for success, _, _ in results.values() if success)
        failed_tests = total_tests - passed_tests
        
        report = [
            "EGI Test Suite Report",
            "=" * 50,
            f"Total Tests: {total_tests}",
            f"Passed: {passed_tests}",
            f"Failed: {failed_tests}",
            f"Success Rate: {(passed_tests/total_tests)*100:.1f}%",
            "",
            "Test Results:",
            "-" * 30
        ]
        
        for test_id, (success, message, _) in results.items():
            status = "PASS" if success else "FAIL"
            report.append(f"{status:4} | {test_id:30} | {message}")
        
        return "\n".join(report)
