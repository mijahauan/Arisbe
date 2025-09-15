"""
Transformation Validation Pipeline.
Integrates EGI validity analysis into the transformation workflow to ensure correctness.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from egi_core_dau import RelationalGraphWithCuts
from egi_validity_analyzer import (
    EGIValidityAnalyzer,
    ValidationReport,
    ValidationSeverity,
)
from egif_generator_dau import generate_egif
from egif_parser_dau import parse_egif
from egif_transformation_interface import (
    EGIFTransformationInterface,
    TransformationRequest,
    TransformationResponse,
)
from formal_transformation_rules import FormalTransformationEngine


class ValidationPolicy(Enum):
    """Validation policy levels for transformations."""

    STRICT = "strict"  # Fail on any error or critical issue
    STANDARD = "standard"  # Fail on critical issues only
    PERMISSIVE = "permissive"  # Allow all transformations, log issues
    DISABLED = "disabled"  # No validation


@dataclass
class TransformationValidationResult:
    """Result of transformation validation."""

    transformation_id: str
    is_valid: bool
    pre_validation: ValidationReport
    post_validation: ValidationReport
    transformation_response: TransformationResponse
    policy_applied: ValidationPolicy
    validation_passed: bool
    issues_introduced: List[str] = field(default_factory=list)
    issues_resolved: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class TransformationValidationPipeline:
    """
    Comprehensive validation pipeline for EG transformations.

    Ensures that:
    1. Source EGI is valid before transformation
    2. Transformation rules are applied correctly
    3. Result EGI maintains validity
    4. No structural errors are introduced
    5. Logical consistency is preserved
    """

    def __init__(self, policy: ValidationPolicy = ValidationPolicy.STANDARD):
        self.validator = EGIValidityAnalyzer()
        self.transformation_interface = EGIFTransformationInterface()
        self.policy = policy
        self.validation_history: List[TransformationValidationResult] = []

    def validate_transformation(
        self,
        request: TransformationRequest,
        existing_egi: Optional[RelationalGraphWithCuts] = None,
        transformation_id: Optional[str] = None,
    ) -> TransformationValidationResult:
        """
        Validate a complete transformation workflow.

        Steps:
        1. Parse and validate source EGI
        2. Apply transformation
        3. Validate result EGI
        4. Compare pre/post validation reports
        5. Apply validation policy
        """

        if not transformation_id:
            transformation_id = f"transform_{len(self.validation_history) + 1:04d}"

        # Step 1: Pre-transformation validation
        try:
            source_egi = existing_egi or parse_egif(request.source_egif)
            pre_validation = self.validator.analyze_egi(
                source_egi, request.source_egif, f"{transformation_id}_pre"
            )
        except Exception as e:
            # Create error validation result
            return self._create_error_result(
                transformation_id, request, f"Source EGI parsing failed: {e}"
            )

        # Check if we should proceed based on pre-validation
        if not self._should_proceed_with_transformation(pre_validation):
            return self._create_blocked_result(
                transformation_id,
                request,
                pre_validation,
                "Pre-transformation validation failed",
            )

        # Step 2: Apply transformation
        try:
            transformation_response = (
                self.transformation_interface.apply_transformation(
                    request, existing_egi
                )
            )
        except Exception as e:
            return self._create_error_result(
                transformation_id,
                request,
                f"Transformation failed: {e}",
                pre_validation,
            )

        # Step 3: Post-transformation validation
        if transformation_response.success and transformation_response.result_egi:
            try:
                post_validation = self.validator.analyze_egi(
                    transformation_response.result_egi,
                    transformation_response.result_egif,
                    f"{transformation_id}_post",
                )
            except Exception as e:
                return self._create_error_result(
                    transformation_id,
                    request,
                    f"Post-transformation validation failed: {e}",
                    pre_validation,
                    transformation_response,
                )
        else:
            # Transformation failed, create empty post-validation
            post_validation = ValidationReport(
                egi_id=f"{transformation_id}_post",
                source_egif=None,
                is_valid=False,
                issues=[],
                statistics={},
                metadata={"error": "Transformation failed"},
            )

        # Step 4: Analyze validation changes
        issues_introduced, issues_resolved = self._analyze_validation_changes(
            pre_validation, post_validation
        )

        # Step 5: Apply validation policy
        validation_passed = self._apply_validation_policy(
            pre_validation, post_validation, transformation_response
        )

        # Create result
        result = TransformationValidationResult(
            transformation_id=transformation_id,
            is_valid=transformation_response.success and post_validation.is_valid,
            pre_validation=pre_validation,
            post_validation=post_validation,
            transformation_response=transformation_response,
            policy_applied=self.policy,
            validation_passed=validation_passed,
            issues_introduced=issues_introduced,
            issues_resolved=issues_resolved,
            metadata={
                "timestamp": datetime.now().isoformat(),
                "rule_applied": request.rule_name,
                "target_area": request.target_area_description,
            },
        )

        # Store in history
        self.validation_history.append(result)

        return result

    def _should_proceed_with_transformation(
        self, pre_validation: ValidationReport
    ) -> bool:
        """Determine if transformation should proceed based on pre-validation."""

        if self.policy == ValidationPolicy.DISABLED:
            return True
        elif self.policy == ValidationPolicy.PERMISSIVE:
            return True
        elif self.policy == ValidationPolicy.STANDARD:
            return not pre_validation.has_critical_issues()
        elif self.policy == ValidationPolicy.STRICT:
            return pre_validation.is_valid

        return True

    def _apply_validation_policy(
        self,
        pre_validation: ValidationReport,
        post_validation: ValidationReport,
        transformation_response: TransformationResponse,
    ) -> bool:
        """Apply validation policy to determine if result is acceptable."""

        if self.policy == ValidationPolicy.DISABLED:
            return True
        elif self.policy == ValidationPolicy.PERMISSIVE:
            return transformation_response.success
        elif self.policy == ValidationPolicy.STANDARD:
            return (
                transformation_response.success
                and not post_validation.has_critical_issues()
            )
        elif self.policy == ValidationPolicy.STRICT:
            return (
                transformation_response.success
                and post_validation.is_valid
                and not self._has_new_errors(pre_validation, post_validation)
            )

        return True

    def _has_new_errors(
        self, pre_validation: ValidationReport, post_validation: ValidationReport
    ) -> bool:
        """Check if new errors were introduced."""

        pre_errors = len(
            pre_validation.get_issues_by_severity(ValidationSeverity.ERROR)
        )
        pre_critical = len(
            pre_validation.get_issues_by_severity(ValidationSeverity.CRITICAL)
        )

        post_errors = len(
            post_validation.get_issues_by_severity(ValidationSeverity.ERROR)
        )
        post_critical = len(
            post_validation.get_issues_by_severity(ValidationSeverity.CRITICAL)
        )

        return (post_errors > pre_errors) or (post_critical > pre_critical)

    def _analyze_validation_changes(
        self, pre_validation: ValidationReport, post_validation: ValidationReport
    ) -> Tuple[List[str], List[str]]:
        """Analyze what validation issues were introduced or resolved."""

        pre_issue_descriptions = {issue.description for issue in pre_validation.issues}
        post_issue_descriptions = {
            issue.description for issue in post_validation.issues
        }

        issues_introduced = list(post_issue_descriptions - pre_issue_descriptions)
        issues_resolved = list(pre_issue_descriptions - post_issue_descriptions)

        return issues_introduced, issues_resolved

    def _create_error_result(
        self,
        transformation_id: str,
        request: TransformationRequest,
        error_message: str,
        pre_validation: Optional[ValidationReport] = None,
        transformation_response: Optional[TransformationResponse] = None,
    ) -> TransformationValidationResult:
        """Create an error validation result."""

        if not pre_validation:
            pre_validation = ValidationReport(
                egi_id=f"{transformation_id}_pre",
                source_egif=request.source_egif,
                is_valid=False,
                issues=[],
                statistics={},
                metadata={"error": "Pre-validation failed"},
            )

        if not transformation_response:
            transformation_response = TransformationResponse(
                success=False,
                result_egif="",
                result_egi=None,
                error_message=error_message,
                transformation_details={},
            )

        post_validation = ValidationReport(
            egi_id=f"{transformation_id}_post",
            source_egif=None,
            is_valid=False,
            issues=[],
            statistics={},
            metadata={"error": error_message},
        )

        return TransformationValidationResult(
            transformation_id=transformation_id,
            is_valid=False,
            pre_validation=pre_validation,
            post_validation=post_validation,
            transformation_response=transformation_response,
            policy_applied=self.policy,
            validation_passed=False,
            issues_introduced=[error_message],
            issues_resolved=[],
            metadata={"error": error_message},
        )

    def _create_blocked_result(
        self,
        transformation_id: str,
        request: TransformationRequest,
        pre_validation: ValidationReport,
        reason: str,
    ) -> TransformationValidationResult:
        """Create a blocked validation result."""

        transformation_response = TransformationResponse(
            success=False,
            result_egif="",
            result_egi=None,
            error_message=f"Transformation blocked: {reason}",
            transformation_details={},
        )

        post_validation = ValidationReport(
            egi_id=f"{transformation_id}_post",
            source_egif=None,
            is_valid=False,
            issues=[],
            statistics={},
            metadata={"blocked": reason},
        )

        return TransformationValidationResult(
            transformation_id=transformation_id,
            is_valid=False,
            pre_validation=pre_validation,
            post_validation=post_validation,
            transformation_response=transformation_response,
            policy_applied=self.policy,
            validation_passed=False,
            issues_introduced=[reason],
            issues_resolved=[],
            metadata={"blocked": reason},
        )

    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of all validation results."""

        if not self.validation_history:
            return {"total_transformations": 0}

        total = len(self.validation_history)
        successful = sum(1 for r in self.validation_history if r.is_valid)
        validation_passed = sum(
            1 for r in self.validation_history if r.validation_passed
        )

        # Count issues by type
        total_issues_introduced = sum(
            len(r.issues_introduced) for r in self.validation_history
        )
        total_issues_resolved = sum(
            len(r.issues_resolved) for r in self.validation_history
        )

        # Rule usage statistics
        rule_usage = {}
        for result in self.validation_history:
            rule = result.metadata.get("rule_applied", "unknown")
            rule_usage[rule] = rule_usage.get(rule, 0) + 1

        return {
            "total_transformations": total,
            "successful_transformations": successful,
            "validation_passed": validation_passed,
            "success_rate": successful / total if total > 0 else 0,
            "validation_pass_rate": validation_passed / total if total > 0 else 0,
            "total_issues_introduced": total_issues_introduced,
            "total_issues_resolved": total_issues_resolved,
            "net_issues": total_issues_introduced - total_issues_resolved,
            "rule_usage": rule_usage,
            "policy": self.policy.value,
        }

    def export_validation_report(self) -> Dict[str, Any]:
        """Export comprehensive validation report."""

        return {
            "summary": self.get_validation_summary(),
            "policy": self.policy.value,
            "validation_history": [
                {
                    "transformation_id": result.transformation_id,
                    "is_valid": result.is_valid,
                    "validation_passed": result.validation_passed,
                    "rule_applied": result.metadata.get("rule_applied"),
                    "issues_introduced": len(result.issues_introduced),
                    "issues_resolved": len(result.issues_resolved),
                    "pre_validation_issues": len(result.pre_validation.issues),
                    "post_validation_issues": len(result.post_validation.issues),
                    "transformation_success": result.transformation_response.success,
                    "metadata": result.metadata,
                }
                for result in self.validation_history
            ],
        }


def test_transformation_validation_pipeline():
    """Test the transformation validation pipeline."""
    print("=== Testing Transformation Validation Pipeline ===")

    # Test with different policies
    for policy in [ValidationPolicy.STRICT, ValidationPolicy.STANDARD]:
        print(f"\n--- Testing with {policy.value.upper()} policy ---")

        pipeline = TransformationValidationPipeline(policy)

        # Test 1: Valid transformation
        print("\n--- Test 1: Valid Transformation ---")
        try:
            request = TransformationRequest(
                source_egif='(Human "Socrates")',
                rule_name="DC+",
                target_area_description="sheet",
                operation_details={},
                description="Add double cut around Socrates",
            )

            result = pipeline.validate_transformation(request)

            print(f"Transformation valid: {result.is_valid}")
            print(f"Validation passed: {result.validation_passed}")
            print(f"Issues introduced: {len(result.issues_introduced)}")
            print(f"Issues resolved: {len(result.issues_resolved)}")

        except Exception as e:
            print(f"Test 1 failed: {e}")

        # Test 2: Get summary
        print("\n--- Test 2: Validation Summary ---")
        summary = pipeline.get_validation_summary()
        print(f"Total transformations: {summary['total_transformations']}")
        print(f"Success rate: {summary['success_rate']:.2%}")
        print(f"Validation pass rate: {summary['validation_pass_rate']:.2%}")
        print(f"Net issues: {summary['net_issues']}")

    return pipeline


if __name__ == "__main__":
    test_transformation_validation_pipeline()
