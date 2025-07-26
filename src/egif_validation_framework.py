"""
EGIF Validation Framework - Phase 3 Implementation

This module provides comprehensive validation for EGIF implementations,
ensuring correctness, consistency, and educational value. It validates:

1. Syntactic correctness (lexical and parsing validation)
2. Semantic consistency (logical coherence and meaning preservation)
3. Educational effectiveness (learning outcome validation)
4. Dau-Sowa compatibility (mathematical rigor vs practical convenience)
5. Round-trip integrity (bidirectional conversion accuracy)
6. Performance characteristics (efficiency and scalability)

The framework supports multiple validation levels from basic syntax checking
to advanced semantic equivalence testing.

Author: Manus AI
Date: January 2025
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union, Callable
from dataclasses import dataclass
from enum import Enum
import re
import time
from abc import ABC, abstractmethod

from egif_parser import EGIFParseResult, parse_egif
from egif_advanced_constructs import parse_advanced_egif, FunctionSymbol, CoreferencePattern, ScrollPattern
from egif_generator_simple import SimpleEGIFGenerator, SimpleEGIFGenerationResult, simple_round_trip_test
from egif_educational_features import EGIFEducationalSystem, explain_egif
from dau_sowa_compatibility import DauSowaCompatibilityAnalyzer, analyze_dau_sowa_compatibility


class ValidationLevel(Enum):
    """Validation thoroughness levels."""
    BASIC = 1           # Syntax and basic parsing
    STANDARD = 2        # + Semantic consistency
    COMPREHENSIVE = 3   # + Educational validation
    EXPERT = 4          # + Dau-Sowa compatibility
    PRODUCTION = 5      # + Performance and stress testing


class ValidationCategory(Enum):
    """Categories of validation tests."""
    SYNTACTIC = "syntactic"
    SEMANTIC = "semantic"
    EDUCATIONAL = "educational"
    COMPATIBILITY = "compatibility"
    PERFORMANCE = "performance"
    ROUND_TRIP = "round_trip"
    STRESS = "stress"


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """Result of a single validation test."""
    test_name: str
    category: ValidationCategory
    severity: ValidationSeverity
    passed: bool
    message: str
    details: Dict[str, Any]
    execution_time: float
    suggestions: List[str]
    
    def get_formatted_result(self) -> str:
        """Get formatted validation result."""
        status = "✅ PASS" if self.passed else "❌ FAIL"
        severity_icon = {
            ValidationSeverity.INFO: "ℹ️",
            ValidationSeverity.WARNING: "⚠️",
            ValidationSeverity.ERROR: "🚫",
            ValidationSeverity.CRITICAL: "🔥"
        }
        
        lines = []
        lines.append(f"{status} {severity_icon[self.severity]} {self.test_name}")
        lines.append(f"Category: {self.category.value.title()}")
        lines.append(f"Message: {self.message}")
        lines.append(f"Execution Time: {self.execution_time:.3f}s")
        
        if self.details:
            lines.append("Details:")
            for key, value in self.details.items():
                lines.append(f"  {key}: {value}")
        
        if self.suggestions:
            lines.append("Suggestions:")
            for suggestion in self.suggestions:
                lines.append(f"  • {suggestion}")
        
        return "\n".join(lines)


@dataclass
class ValidationReport:
    """Comprehensive validation report."""
    source: str
    validation_level: ValidationLevel
    total_tests: int
    passed_tests: int
    failed_tests: int
    total_time: float
    results: List[ValidationResult]
    summary: Dict[ValidationCategory, Dict[str, int]]
    recommendations: List[str]
    
    def get_success_rate(self) -> float:
        """Get overall success rate."""
        return (self.passed_tests / self.total_tests) * 100 if self.total_tests > 0 else 0
    
    def get_formatted_report(self) -> str:
        """Get formatted validation report."""
        lines = []
        lines.append("🔍 EGIF Validation Report")
        lines.append("=" * 60)
        lines.append(f"Source: {self.source}")
        lines.append(f"Validation Level: {self.validation_level.name}")
        lines.append(f"Success Rate: {self.get_success_rate():.1f}% ({self.passed_tests}/{self.total_tests})")
        lines.append(f"Total Execution Time: {self.total_time:.3f}s")
        
        # Category summary
        lines.append(f"\n📊 Category Summary:")
        for category, stats in self.summary.items():
            passed = stats.get('passed', 0)
            total = stats.get('total', 0)
            rate = (passed / total * 100) if total > 0 else 0
            lines.append(f"  {category.value.title()}: {passed}/{total} ({rate:.1f}%)")
        
        # Failed tests
        failed_results = [r for r in self.results if not r.passed]
        if failed_results:
            lines.append(f"\n❌ Failed Tests ({len(failed_results)}):")
            for result in failed_results:
                lines.append(f"\n{result.get_formatted_result()}")
        
        # Recommendations
        if self.recommendations:
            lines.append(f"\n💡 Recommendations:")
            for rec in self.recommendations:
                lines.append(f"  • {rec}")
        
        return "\n".join(lines)


class ValidationTest(ABC):
    """Abstract base class for validation tests."""
    
    def __init__(self, name: str, category: ValidationCategory, severity: ValidationSeverity):
        self.name = name
        self.category = category
        self.severity = severity
    
    @abstractmethod
    def run(self, egif_source: str, context: Dict[str, Any]) -> ValidationResult:
        """Run the validation test."""
        pass


class SyntacticValidationTest(ValidationTest):
    """Tests for syntactic correctness."""
    
    def __init__(self, name: str, severity: ValidationSeverity = ValidationSeverity.ERROR):
        super().__init__(name, ValidationCategory.SYNTACTIC, severity)


class BasicParsingTest(SyntacticValidationTest):
    """Test basic EGIF parsing."""
    
    def __init__(self):
        super().__init__("Basic Parsing", ValidationSeverity.CRITICAL)
    
    def run(self, egif_source: str, context: Dict[str, Any]) -> ValidationResult:
        start_time = time.time()
        
        try:
            result = parse_egif(egif_source, educational_mode=True)
            execution_time = time.time() - start_time
            
            if result.errors:
                return ValidationResult(
                    test_name=self.name,
                    category=self.category,
                    severity=self.severity,
                    passed=False,
                    message=f"Parsing failed with {len(result.errors)} errors",
                    details={"errors": [str(e.message) for e in result.errors[:3]]},
                    execution_time=execution_time,
                    suggestions=["Check syntax for missing brackets or parentheses",
                               "Verify proper use of defining labels (*)",
                               "Ensure balanced brackets and parentheses"]
                )
            else:
                return ValidationResult(
                    test_name=self.name,
                    category=self.category,
                    severity=self.severity,
                    passed=True,
                    message="Parsing successful",
                    details={"entities": len(result.entities), "predicates": len(result.predicates)},
                    execution_time=execution_time,
                    suggestions=[]
                )
        
        except Exception as e:
            execution_time = time.time() - start_time
            return ValidationResult(
                test_name=self.name,
                category=self.category,
                severity=self.severity,
                passed=False,
                message=f"Parsing exception: {str(e)}",
                details={"exception_type": type(e).__name__},
                execution_time=execution_time,
                suggestions=["Check for invalid characters or malformed syntax"]
            )


class AdvancedParsingTest(SyntacticValidationTest):
    """Test advanced EGIF parsing with constructs."""
    
    def __init__(self):
        super().__init__("Advanced Parsing", ValidationSeverity.ERROR)
    
    def run(self, egif_source: str, context: Dict[str, Any]) -> ValidationResult:
        start_time = time.time()
        
        try:
            result = parse_advanced_egif(egif_source, educational_mode=True)
            execution_time = time.time() - start_time
            
            advanced_features = 0
            if hasattr(result, 'function_symbols'):
                advanced_features += len(result.function_symbols)
            if hasattr(result, 'coreference_patterns'):
                advanced_features += len(result.coreference_patterns)
            if hasattr(result, 'scroll_patterns'):
                advanced_features += len(result.scroll_patterns)
            
            return ValidationResult(
                test_name=self.name,
                category=self.category,
                severity=self.severity,
                passed=True,
                message="Advanced parsing successful",
                details={
                    "entities": len(result.entities),
                    "predicates": len(result.predicates),
                    "advanced_features": advanced_features
                },
                execution_time=execution_time,
                suggestions=[]
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            return ValidationResult(
                test_name=self.name,
                category=self.category,
                severity=self.severity,
                passed=False,
                message=f"Advanced parsing failed: {str(e)}",
                details={"exception_type": type(e).__name__},
                execution_time=execution_time,
                suggestions=["Check advanced construct syntax (functions, scrolls)",
                           "Verify proper use of -> operator for functions",
                           "Ensure correct nesting of conditional structures"]
            )


class RoundTripTest(ValidationTest):
    """Test bidirectional conversion integrity."""
    
    def __init__(self):
        super().__init__("Round-trip Conversion", ValidationCategory.ROUND_TRIP, ValidationSeverity.ERROR)
    
    def run(self, egif_source: str, context: Dict[str, Any]) -> ValidationResult:
        start_time = time.time()
        
        try:
            success, generated, messages = simple_round_trip_test(egif_source)
            execution_time = time.time() - start_time
            
            return ValidationResult(
                test_name=self.name,
                category=self.category,
                severity=self.severity,
                passed=success,
                message="Round-trip successful" if success else "Round-trip failed",
                details={
                    "original": egif_source,
                    "generated": generated,
                    "messages": messages[:3] if messages else []
                },
                execution_time=execution_time,
                suggestions=["Check for semantic equivalence even if syntax differs",
                           "Verify entity ordering consistency",
                           "Ensure proper handling of constants vs variables"] if not success else []
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            return ValidationResult(
                test_name=self.name,
                category=self.category,
                severity=self.severity,
                passed=False,
                message=f"Round-trip exception: {str(e)}",
                details={"exception_type": type(e).__name__},
                execution_time=execution_time,
                suggestions=["Check generator implementation",
                           "Verify parse result structure"]
            )


class EducationalValidationTest(ValidationTest):
    """Test educational effectiveness."""
    
    def __init__(self):
        super().__init__("Educational Analysis", ValidationCategory.EDUCATIONAL, ValidationSeverity.WARNING)
    
    def run(self, egif_source: str, context: Dict[str, Any]) -> ValidationResult:
        start_time = time.time()
        
        try:
            report = explain_egif(egif_source)
            execution_time = time.time() - start_time
            
            # Check for educational content quality
            has_concepts = "Concepts Identified" in report
            has_visual_mapping = "EGIF ↔ Graphical Mapping" in report
            has_explanations = "Detailed Concept Explanations" in report
            has_learning_level = "Learning Level" in report
            
            quality_score = sum([has_concepts, has_visual_mapping, has_explanations, has_learning_level])
            
            return ValidationResult(
                test_name=self.name,
                category=self.category,
                severity=self.severity,
                passed=quality_score >= 3,
                message=f"Educational quality score: {quality_score}/4",
                details={
                    "has_concepts": has_concepts,
                    "has_visual_mapping": has_visual_mapping,
                    "has_explanations": has_explanations,
                    "has_learning_level": has_learning_level
                },
                execution_time=execution_time,
                suggestions=["Add more complex constructs for richer educational content",
                           "Include visual mappings for better understanding",
                           "Provide concept explanations for learning"] if quality_score < 3 else []
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            return ValidationResult(
                test_name=self.name,
                category=self.category,
                severity=self.severity,
                passed=False,
                message=f"Educational analysis failed: {str(e)}",
                details={"exception_type": type(e).__name__},
                execution_time=execution_time,
                suggestions=["Check educational system implementation"]
            )


class CompatibilityValidationTest(ValidationTest):
    """Test Dau-Sowa compatibility."""
    
    def __init__(self):
        super().__init__("Dau-Sowa Compatibility", ValidationCategory.COMPATIBILITY, ValidationSeverity.WARNING)
    
    def run(self, egif_source: str, context: Dict[str, Any]) -> ValidationResult:
        start_time = time.time()
        
        try:
            report = analyze_dau_sowa_compatibility(egif_source)
            execution_time = time.time() - start_time
            
            has_issues = "compatibility issue(s) detected" in report
            no_issues = "No compatibility issues detected" in report
            
            return ValidationResult(
                test_name=self.name,
                category=self.category,
                severity=self.severity,
                passed=no_issues,
                message="No compatibility issues" if no_issues else "Compatibility issues detected",
                details={"has_compatibility_issues": has_issues},
                execution_time=execution_time,
                suggestions=["Review Dau-Sowa compatibility report for resolution strategies",
                           "Consider educational preference for resolution",
                           "Maintain consistency with Peirce's principles"] if has_issues else []
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            return ValidationResult(
                test_name=self.name,
                category=self.category,
                severity=self.severity,
                passed=False,
                message=f"Compatibility analysis failed: {str(e)}",
                details={"exception_type": type(e).__name__},
                execution_time=execution_time,
                suggestions=["Check compatibility analyzer implementation"]
            )


class PerformanceValidationTest(ValidationTest):
    """Test performance characteristics."""
    
    def __init__(self):
        super().__init__("Performance", ValidationCategory.PERFORMANCE, ValidationSeverity.INFO)
    
    def run(self, egif_source: str, context: Dict[str, Any]) -> ValidationResult:
        start_time = time.time()
        
        # Run multiple iterations for performance measurement
        iterations = 10
        parse_times = []
        
        try:
            for _ in range(iterations):
                iter_start = time.time()
                result = parse_egif(egif_source, educational_mode=False)
                parse_times.append(time.time() - iter_start)
            
            execution_time = time.time() - start_time
            avg_parse_time = sum(parse_times) / len(parse_times)
            max_parse_time = max(parse_times)
            
            # Performance thresholds
            good_threshold = 0.01  # 10ms
            acceptable_threshold = 0.1  # 100ms
            
            if avg_parse_time <= good_threshold:
                performance_rating = "Excellent"
                passed = True
            elif avg_parse_time <= acceptable_threshold:
                performance_rating = "Good"
                passed = True
            else:
                performance_rating = "Needs Improvement"
                passed = False
            
            return ValidationResult(
                test_name=self.name,
                category=self.category,
                severity=self.severity,
                passed=passed,
                message=f"Performance rating: {performance_rating}",
                details={
                    "avg_parse_time": f"{avg_parse_time:.4f}s",
                    "max_parse_time": f"{max_parse_time:.4f}s",
                    "iterations": iterations
                },
                execution_time=execution_time,
                suggestions=["Optimize parser for complex constructs",
                           "Consider caching for repeated parsing",
                           "Profile bottlenecks in parsing logic"] if not passed else []
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            return ValidationResult(
                test_name=self.name,
                category=self.category,
                severity=self.severity,
                passed=False,
                message=f"Performance test failed: {str(e)}",
                details={"exception_type": type(e).__name__},
                execution_time=execution_time,
                suggestions=["Check for infinite loops or excessive recursion"]
            )


class EGIFValidationFramework:
    """
    Comprehensive validation framework for EGIF implementations.
    
    Provides multiple validation levels from basic syntax checking to
    advanced semantic and educational validation.
    """
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.STANDARD):
        """Initialize the validation framework."""
        self.validation_level = validation_level
        self.test_suite = self._build_test_suite()
    
    def _build_test_suite(self) -> List[ValidationTest]:
        """Build test suite based on validation level."""
        tests = []
        
        # Basic level - syntax and parsing
        if self.validation_level.value >= ValidationLevel.BASIC.value:
            tests.extend([
                BasicParsingTest(),
                AdvancedParsingTest(),
            ])
        
        # Standard level - add semantic tests
        if self.validation_level.value >= ValidationLevel.STANDARD.value:
            tests.extend([
                RoundTripTest(),
            ])
        
        # Comprehensive level - add educational validation
        if self.validation_level.value >= ValidationLevel.COMPREHENSIVE.value:
            tests.extend([
                EducationalValidationTest(),
            ])
        
        # Expert level - add compatibility validation
        if self.validation_level.value >= ValidationLevel.EXPERT.value:
            tests.extend([
                CompatibilityValidationTest(),
            ])
        
        # Production level - add performance validation
        if self.validation_level.value >= ValidationLevel.PRODUCTION.value:
            tests.extend([
                PerformanceValidationTest(),
            ])
        
        return tests
    
    def validate(self, egif_source: str, context: Optional[Dict[str, Any]] = None) -> ValidationReport:
        """Run comprehensive validation on EGIF source."""
        if context is None:
            context = {}
        
        start_time = time.time()
        results = []
        
        # Run all tests
        for test in self.test_suite:
            try:
                result = test.run(egif_source, context)
                results.append(result)
            except Exception as e:
                # Create error result for failed test
                error_result = ValidationResult(
                    test_name=test.name,
                    category=test.category,
                    severity=ValidationSeverity.CRITICAL,
                    passed=False,
                    message=f"Test execution failed: {str(e)}",
                    details={"exception_type": type(e).__name__},
                    execution_time=0.0,
                    suggestions=["Check test implementation"]
                )
                results.append(error_result)
        
        total_time = time.time() - start_time
        
        # Calculate summary statistics
        passed_tests = sum(1 for r in results if r.passed)
        failed_tests = len(results) - passed_tests
        
        # Category summary
        summary = {}
        for category in ValidationCategory:
            category_results = [r for r in results if r.category == category]
            if category_results:
                summary[category] = {
                    'total': len(category_results),
                    'passed': sum(1 for r in category_results if r.passed)
                }
        
        # Generate recommendations
        recommendations = self._generate_recommendations(results)
        
        return ValidationReport(
            source=egif_source,
            validation_level=self.validation_level,
            total_tests=len(results),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            total_time=total_time,
            results=results,
            summary=summary,
            recommendations=recommendations
        )
    
    def _generate_recommendations(self, results: List[ValidationResult]) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        # Check for critical failures
        critical_failures = [r for r in results if not r.passed and r.severity == ValidationSeverity.CRITICAL]
        if critical_failures:
            recommendations.append("Address critical parsing failures before proceeding")
        
        # Check for educational issues
        educational_failures = [r for r in results if not r.passed and r.category == ValidationCategory.EDUCATIONAL]
        if educational_failures:
            recommendations.append("Enhance educational content for better learning outcomes")
        
        # Check for compatibility issues
        compatibility_failures = [r for r in results if not r.passed and r.category == ValidationCategory.COMPATIBILITY]
        if compatibility_failures:
            recommendations.append("Review Dau-Sowa compatibility for mathematical consistency")
        
        # Check for performance issues
        performance_failures = [r for r in results if not r.passed and r.category == ValidationCategory.PERFORMANCE]
        if performance_failures:
            recommendations.append("Optimize performance for production use")
        
        # General recommendations
        success_rate = (len([r for r in results if r.passed]) / len(results)) * 100 if results else 0
        if success_rate < 80:
            recommendations.append("Overall validation success rate is below 80% - review implementation")
        elif success_rate >= 95:
            recommendations.append("Excellent validation results - ready for production use")
        
        return recommendations


# Convenience functions
def validate_egif(egif_source: str, level: ValidationLevel = ValidationLevel.STANDARD) -> ValidationReport:
    """Validate EGIF source with specified validation level."""
    framework = EGIFValidationFramework(level)
    return framework.validate(egif_source)


def quick_validate(egif_source: str) -> bool:
    """Quick validation - returns True if basic validation passes."""
    framework = EGIFValidationFramework(ValidationLevel.BASIC)
    report = framework.validate(egif_source)
    return report.get_success_rate() >= 100


# Example usage and testing
if __name__ == "__main__":
    print("EGIF Validation Framework Test")
    print("=" * 50)
    
    # Test cases with different complexity levels
    test_cases = [
        # Basic valid case
        "(Person *john)",
        
        # Advanced constructs
        "(add 2 3 -> *sum)",
        
        # Complex case
        "(Person *x) [If (Mortal x) [Then (Finite x)]]",
        
        # Invalid case
        "(Person *john",  # Missing closing parenthesis
        
        # Educational rich case
        "(Loves *x *y) (Knows y *z) [= x z]",
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case}")
        print("-" * 60)
        
        try:
            # Run comprehensive validation
            report = validate_egif(test_case, ValidationLevel.EXPERT)
            print(report.get_formatted_report())
            
        except Exception as e:
            print(f"Validation failed: {e}")
        
        if i < len(test_cases):
            print("\n" + "=" * 80)
    
    print("\n" + "=" * 80)
    print("Validation Levels Available:")
    print("=" * 80)
    
    for level in ValidationLevel:
        print(f"• {level.name}: Level {level.value}")
    
    print("\n" + "=" * 80)
    print("EGIF Validation Framework Phase 3 implementation complete!")
    print("Provides comprehensive validation from syntax to educational effectiveness.")

