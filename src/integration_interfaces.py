"""
Standardized interfaces for Arisbe codebase integration.

This module defines the canonical interfaces that all subsystems should implement
to ensure coherent integration and avoid interface incompatibilities.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol

from egi_core_dau import EGI
from formal_transformation_rules import (
    AreaPolarity,
    TransformationContext,
    TransformationResult,
)


class PolarityProvider(Protocol):
    """Canonical interface for area polarity calculation."""

    def get_polarity(self, area_id: str) -> AreaPolarity:
        """Get polarity of an area using standardized interface."""
        ...

    def get_nesting_level(self, area_id: str) -> Optional[int]:
        """Get nesting level of an area."""
        ...


class TransformationValidator(Protocol):
    """Standard interface for transformation validation."""

    def validate_transformation(self, context: TransformationContext) -> bool:
        """Validate if a transformation is legal in the given context."""
        ...

    def get_validation_errors(self, context: TransformationContext) -> List[str]:
        """Get detailed validation error messages."""
        ...


class HistoryTracker(Protocol):
    """Standard interface for transformation history tracking."""

    def record_transformation(
        self, before: EGI, after: EGI, rule: str, context: Dict[str, Any]
    ) -> None:
        """Record a transformation in the history."""
        ...

    def get_history(self) -> List[Dict[str, Any]]:
        """Get the complete transformation history."""
        ...

    def can_undo(self) -> bool:
        """Check if undo operation is available."""
        ...


class TheoremValidator(Protocol):
    """Interface for Dau theorem correspondence validation."""

    def validate_theorem_compliance(self, egi: EGI) -> bool:
        """Validate EGI against Dau's theoretical requirements."""
        ...

    def run_theorem_tests(self) -> Dict[str, bool]:
        """Run all theorem correspondence tests."""
        ...


class CorpusManager(Protocol):
    """Standard interface for corpus management."""

    def add_egi(self, egi: EGI, metadata: Dict[str, Any]) -> str:
        """Add EGI to corpus and return unique identifier."""
        ...

    def get_egi(self, identifier: str) -> Optional[EGI]:
        """Retrieve EGI by identifier."""
        ...

    def search_corpus(self, query: Dict[str, Any]) -> List[str]:
        """Search corpus and return matching identifiers."""
        ...


@dataclass
class IntegrationContext:
    """Context object for cross-subsystem operations."""

    polarity_provider: PolarityProvider
    transformation_validator: TransformationValidator
    history_tracker: HistoryTracker
    theorem_validator: Optional[TheoremValidator] = None
    corpus_manager: Optional[CorpusManager] = None


class IntegrationManager:
    """Central manager for coordinating between integrated subsystems."""

    def __init__(self, context: IntegrationContext):
        self.context = context

    def validate_and_transform(
        self, egi: EGI, transformation_rule: str, target_area: str
    ) -> Optional[EGI]:
        """Perform validated transformation with full integration."""
        # Create transformation context
        polarity = self.context.polarity_provider.get_polarity(target_area)
        nesting_level = self.context.polarity_provider.get_nesting_level(target_area)

        transform_context = TransformationContext(
            source_egi=egi,
            target_area=target_area,
            transformation_rule=transformation_rule,
            area_polarity=polarity,
            nesting_level=nesting_level or 0,
        )

        # Validate transformation
        if not self.context.transformation_validator.validate_transformation(
            transform_context
        ):
            errors = self.context.transformation_validator.get_validation_errors(
                transform_context
            )
            print(f"Transformation validation failed: {errors}")
            return None

        # Apply transformation (placeholder - actual implementation depends on rule)
        # This would delegate to the appropriate transformation engine
        result_egi = self._apply_transformation(transform_context)

        if result_egi:
            # Record in history
            self.context.history_tracker.record_transformation(
                before=egi,
                after=result_egi,
                rule=transformation_rule,
                context={"target_area": target_area, "polarity": polarity.value},
            )

            # Validate theorem compliance if available
            if self.context.theorem_validator:
                if not self.context.theorem_validator.validate_theorem_compliance(
                    result_egi
                ):
                    print("Warning: Result EGI may not comply with Dau's theorems")

        return result_egi

    def _apply_transformation(self, context: TransformationContext) -> Optional[EGI]:
        """Apply the actual transformation - to be implemented by specific engines."""
        # This is where we would delegate to the appropriate transformation engine
        # based on the transformation rule
        raise NotImplementedError(
            "Transformation application to be implemented by engines"
        )


# Legacy adapter classes for backward compatibility


class LegacyPolarityAdapter:
    """Adapter to make legacy polarity functions compatible with new interface."""

    def __init__(self, hierarchical_index):
        self.hierarchical_index = hierarchical_index

    def calculate_area_polarity(self, egi, area_id):
        """Legacy interface that delegates to standardized implementation."""
        polarity_str = self.hierarchical_index.get_polarity(str(area_id))
        return (
            AreaPolarity.POSITIVE
            if polarity_str == "positive"
            else AreaPolarity.NEGATIVE
        )

    def _calculate_area_polarity_and_depth(self, egi, area_id):
        """Legacy interface for polarity and depth calculation."""
        polarity = self.calculate_area_polarity(egi, area_id)
        depth = self.hierarchical_index.get_nesting_level(str(area_id)) or 0
        return polarity, depth


class StandardPolarityProvider:
    """Standard implementation of PolarityProvider using HierarchicalIndex."""

    def __init__(self, hierarchical_index):
        self.hierarchical_index = hierarchical_index

    def get_polarity(self, area_id: str) -> AreaPolarity:
        """Get polarity using O(1) hierarchical index lookup."""
        polarity_str = self.hierarchical_index.get_polarity(area_id)
        if polarity_str is None:
            return AreaPolarity.POSITIVE  # Default for sheet
        return (
            AreaPolarity.POSITIVE
            if polarity_str == "positive"
            else AreaPolarity.NEGATIVE
        )

    def get_nesting_level(self, area_id: str) -> Optional[int]:
        """Get nesting level using O(1) hierarchical index lookup."""
        return self.hierarchical_index.get_nesting_level(area_id)
