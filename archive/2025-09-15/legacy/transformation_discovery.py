"""
Transformation Discovery for Selected Subgraphs

Analyzes selected subgraphs to determine legal transformation rules available
to the user, creating the critical workflow: select → discover → transform.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from subgraph_extractor import SelectionParameters, SubgraphExtractionResult
from transformation_engine import OperationRequest, OperationType
from transformation_rules import (
    TransformationContext,
    TransformationRule,
    TransformationRuleType,
    ValidationResult,
)

from egi_core_dau import Cut, Edge, ElementID, RelationalGraphWithCuts, Vertex


class TransformationAvailability(Enum):
    """Availability status of a transformation rule."""

    AVAILABLE = "available"  # Rule can be applied
    CONTEXTUALLY_INVALID = "contextually_invalid"  # Wrong context (positive/negative)
    STRUCTURALLY_INVALID = "structurally_invalid"  # Missing required elements
    ALREADY_APPLIED = "already_applied"  # Transformation already exists
    REQUIRES_EXPANSION = "requires_expansion"  # Need to expand selection


@dataclass
class AvailableTransformation:
    """A transformation rule available for a selected subgraph."""

    rule_type: TransformationRuleType
    operation_type: OperationType
    availability: TransformationAvailability

    # Context information
    target_elements: Set[ElementID] = field(default_factory=set)
    required_context: Optional[ElementID] = None
    context_polarity: Optional[str] = None  # "positive" or "negative"

    # User-friendly information
    description: str = ""
    explanation: str = ""
    example_operation: Optional[OperationRequest] = None

    # Validation details
    validation_result: Optional[ValidationResult] = None
    missing_requirements: List[str] = field(default_factory=list)


@dataclass
class TransformationDiscoveryResult:
    """Result of transformation discovery for a subgraph."""

    success: bool
    selected_elements: Set[ElementID] = field(default_factory=set)

    # Available transformations by category
    available_transformations: List[AvailableTransformation] = field(
        default_factory=list
    )
    contextually_invalid: List[AvailableTransformation] = field(default_factory=list)
    structurally_invalid: List[AvailableTransformation] = field(default_factory=list)

    # Analysis metadata
    analyzed_contexts: Set[ElementID] = field(default_factory=set)
    context_polarities: Dict[ElementID, str] = field(default_factory=dict)

    # Error information
    error_message: str = ""
    warnings: List[str] = field(default_factory=list)


class TransformationDiscoveryEngine:
    """
    Discovers legal transformation rules for selected subgraphs.

    Analyzes the selection context, polarity, and structure to determine
    which EG transformation rules can be legally applied.
    """

    def __init__(
        self, transformation_rules: Dict[TransformationRuleType, TransformationRule]
    ):
        self.transformation_rules = transformation_rules

        # Rule-to-operation mappings
        self.rule_operations = {
            TransformationRuleType.INSERTION: [
                OperationType.ADD_VERTEX,
                OperationType.ADD_EDGE,
                OperationType.ADD_CUT,
            ],
            TransformationRuleType.ERASURE: [
                OperationType.REMOVE_VERTEX,
                OperationType.REMOVE_EDGE,
                OperationType.REMOVE_CUT,
            ],
            TransformationRuleType.ITERATION: [OperationType.ITERATE_SUBGRAPH],
            TransformationRuleType.DEITERATION: [OperationType.DEITERATE_ELEMENT],
            TransformationRuleType.DOUBLE_CUT: [
                OperationType.ADD_DOUBLE_CUT,
                OperationType.REMOVE_DOUBLE_CUT,
            ],
        }

        # Context requirements for rules
        self.context_requirements = {
            TransformationRuleType.INSERTION: "negative",
            TransformationRuleType.ERASURE: "positive",
            TransformationRuleType.ITERATION: "any",
            TransformationRuleType.DEITERATION: "any",
            TransformationRuleType.DOUBLE_CUT: "any",
        }

    def discover_transformations(
        self, egi: RelationalGraphWithCuts, extraction_result: SubgraphExtractionResult
    ) -> TransformationDiscoveryResult:
        """
        Discover available transformations for a selected subgraph.
        """
        if not extraction_result.success:
            return TransformationDiscoveryResult(
                success=False,
                error_message="Cannot discover transformations for failed extraction",
            )

        selected_elements = extraction_result.selected_elements

        try:
            # Analyze contexts and polarities
            context_analysis = self._analyze_contexts(egi, selected_elements)

            # Discover transformations for each rule type
            available_transformations = []
            contextually_invalid = []
            structurally_invalid = []

            for rule_type, rule in self.transformation_rules.items():
                transformations = self._discover_rule_transformations(
                    egi, selected_elements, rule_type, rule, context_analysis
                )

                for transformation in transformations:
                    if (
                        transformation.availability
                        == TransformationAvailability.AVAILABLE
                    ):
                        available_transformations.append(transformation)
                    elif (
                        transformation.availability
                        == TransformationAvailability.CONTEXTUALLY_INVALID
                    ):
                        contextually_invalid.append(transformation)
                    else:
                        structurally_invalid.append(transformation)

            return TransformationDiscoveryResult(
                success=True,
                selected_elements=selected_elements,
                available_transformations=available_transformations,
                contextually_invalid=contextually_invalid,
                structurally_invalid=structurally_invalid,
                analyzed_contexts=context_analysis["contexts"],
                context_polarities=context_analysis["polarities"],
            )

        except Exception as e:
            return TransformationDiscoveryResult(
                success=False, error_message=f"Discovery failed: {str(e)}"
            )

    def _analyze_contexts(
        self, egi: RelationalGraphWithCuts, selected_elements: Set[ElementID]
    ) -> Dict[str, Any]:
        """Analyze contexts and polarities for selected elements."""
        contexts = set()
        polarities = {}

        for element_id in selected_elements:
            try:
                context_id = egi.get_context(element_id)
                contexts.add(context_id)

                # Determine polarity (simplified - would need full nesting analysis)
                nesting_depth = egi.get_nesting_depth(element_id)
                polarity = "positive" if nesting_depth % 2 == 0 else "negative"
                polarities[context_id] = polarity

            except Exception:
                continue

        return {"contexts": contexts, "polarities": polarities}

    def _discover_rule_transformations(
        self,
        egi: RelationalGraphWithCuts,
        selected_elements: Set[ElementID],
        rule_type: TransformationRuleType,
        rule: TransformationRule,
        context_analysis: Dict[str, Any],
    ) -> List[AvailableTransformation]:
        """Discover transformations for a specific rule type."""
        transformations = []

        # Get operations for this rule type
        operations = self.rule_operations.get(rule_type, [])

        for operation_type in operations:
            transformation = self._analyze_operation_availability(
                egi,
                selected_elements,
                rule_type,
                operation_type,
                rule,
                context_analysis,
            )
            transformations.append(transformation)

        return transformations

    def _analyze_operation_availability(
        self,
        egi: RelationalGraphWithCuts,
        selected_elements: Set[ElementID],
        rule_type: TransformationRuleType,
        operation_type: OperationType,
        rule: TransformationRule,
        context_analysis: Dict[str, Any],
    ) -> AvailableTransformation:
        """Analyze availability of a specific operation."""

        # Create example operation request
        example_operation = self._create_example_operation(
            operation_type, selected_elements
        )

        # Create transformation context
        context = TransformationContext(
            target_elements=selected_elements, operation_type=operation_type
        )

        # Validate with the rule
        validation_result = rule.validate(egi, context)

        # Determine availability
        availability = self._determine_availability(
            validation_result, rule_type, context_analysis
        )

        # Generate user-friendly information
        description, explanation = self._generate_descriptions(
            operation_type, rule_type, availability, selected_elements
        )

        return AvailableTransformation(
            rule_type=rule_type,
            operation_type=operation_type,
            availability=availability,
            target_elements=selected_elements,
            description=description,
            explanation=explanation,
            example_operation=example_operation,
            validation_result=validation_result,
            missing_requirements=(
                validation_result.suggestions if validation_result else []
            ),
        )

    def _create_example_operation(
        self, operation_type: OperationType, selected_elements: Set[ElementID]
    ) -> OperationRequest:
        """Create an example operation request."""
        # This would create appropriate operation requests based on type
        # For now, simplified implementation
        return OperationRequest(
            operation_type=operation_type,
            target_elements=list(selected_elements)[:1] if selected_elements else [],
            parameters={},
        )

    def _determine_availability(
        self,
        validation_result: Optional[ValidationResult],
        rule_type: TransformationRuleType,
        context_analysis: Dict[str, Any],
    ) -> TransformationAvailability:
        """Determine availability based on validation and context."""

        if not validation_result:
            return TransformationAvailability.STRUCTURALLY_INVALID

        if validation_result.is_valid:
            return TransformationAvailability.AVAILABLE

        # Check if it's a context issue
        required_polarity = self.context_requirements.get(rule_type)
        if required_polarity and required_polarity != "any":
            current_polarities = set(context_analysis["polarities"].values())
            if required_polarity not in current_polarities:
                return TransformationAvailability.CONTEXTUALLY_INVALID

        return TransformationAvailability.STRUCTURALLY_INVALID

    def _generate_descriptions(
        self,
        operation_type: OperationType,
        rule_type: TransformationRuleType,
        availability: TransformationAvailability,
        selected_elements: Set[ElementID],
    ) -> Tuple[str, str]:
        """Generate user-friendly descriptions."""

        operation_descriptions = {
            OperationType.ADD_VERTEX: (
                "Add Vertex",
                "Insert a new vertex in negative context",
            ),
            OperationType.ADD_EDGE: (
                "Add Edge",
                "Insert a new edge connecting vertices",
            ),
            OperationType.ADD_CUT: ("Add Cut", "Insert a new cut around elements"),
            OperationType.REMOVE_VERTEX: (
                "Remove Vertex",
                "Erase vertex from positive context",
            ),
            OperationType.REMOVE_EDGE: (
                "Remove Edge",
                "Erase edge from positive context",
            ),
            OperationType.REMOVE_CUT: ("Remove Cut", "Erase cut from positive context"),
            OperationType.ITERATE_SUBGRAPH: (
                "Iterate",
                "Copy subgraph to deeper context",
            ),
            OperationType.DEITERATE_ELEMENT: ("De-iterate", "Remove iterated element"),
            OperationType.ADD_DOUBLE_CUT: (
                "Add Double Cut",
                "Add double cut around selection",
            ),
            OperationType.REMOVE_DOUBLE_CUT: ("Remove Double Cut", "Remove double cut"),
        }

        description, base_explanation = operation_descriptions.get(
            operation_type, ("Unknown Operation", "Unknown transformation")
        )

        # Add availability context
        if availability == TransformationAvailability.AVAILABLE:
            explanation = f"{base_explanation} (Ready to apply)"
        elif availability == TransformationAvailability.CONTEXTUALLY_INVALID:
            explanation = f"{base_explanation} (Wrong context - need {self.context_requirements.get(rule_type, 'unknown')} polarity)"
        elif availability == TransformationAvailability.STRUCTURALLY_INVALID:
            explanation = f"{base_explanation} (Missing required elements)"
        else:
            explanation = f"{base_explanation} (Not available)"

        return description, explanation


class SubgraphTransformationWorkflow:
    """
    Integrates subgraph selection with transformation discovery for user workflow.
    """

    def __init__(self, discovery_engine: TransformationDiscoveryEngine):
        self.discovery_engine = discovery_engine

    def analyze_selection(
        self, egi: RelationalGraphWithCuts, extraction_result: SubgraphExtractionResult
    ) -> TransformationDiscoveryResult:
        """Analyze a subgraph selection to discover available transformations."""
        return self.discovery_engine.discover_transformations(egi, extraction_result)

    def get_transformation_menu(
        self, discovery_result: TransformationDiscoveryResult
    ) -> Dict[str, Any]:
        """Generate a user-friendly transformation menu."""
        if not discovery_result.success:
            return {"error": discovery_result.error_message, "available": []}

        menu = {"available": [], "contextually_invalid": [], "help": []}

        # Available transformations
        for transformation in discovery_result.available_transformations:
            menu["available"].append(
                {
                    "id": f"{transformation.rule_type.value}_{transformation.operation_type.value}",
                    "name": transformation.description,
                    "description": transformation.explanation,
                    "rule_type": transformation.rule_type.value,
                    "operation_type": transformation.operation_type.value,
                }
            )

        # Contextually invalid (with help)
        for transformation in discovery_result.contextually_invalid:
            menu["contextually_invalid"].append(
                {
                    "name": transformation.description,
                    "reason": transformation.explanation,
                    "help": f"Select elements in {transformation.context_polarity} context to enable this transformation",
                }
            )

        # General help
        menu["help"] = [
            "Select connected elements to see more transformation options",
            "Transformation rules depend on context polarity (positive/negative)",
            "Some rules require specific element types or relationships",
        ]

        return menu

    def create_operation_request(
        self,
        discovery_result: TransformationDiscoveryResult,
        transformation_id: str,
        additional_parameters: Dict[str, Any] = None,
    ) -> Optional[OperationRequest]:
        """Create an operation request from a selected transformation."""

        # Find the transformation
        for transformation in discovery_result.available_transformations:
            tid = f"{transformation.rule_type.value}_{transformation.operation_type.value}"
            if tid == transformation_id:
                if transformation.example_operation:
                    operation = transformation.example_operation
                    if additional_parameters:
                        operation.parameters.update(additional_parameters)
                    return operation

        return None
