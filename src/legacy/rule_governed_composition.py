"""
Rule-governed graph composition system with baby steps approach.
Implements sophisticated composition patterns while maintaining EG rule compliance.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from frozendict import frozendict
from immutable_transformation_architecture import ContextType, TransformationRuleType
from simple_graph_builder import GraphUtterance, SimpleGraphBuilder

from egi_core_dau import Cut, Edge, ElementID, RelationalGraphWithCuts, Vertex


class CompositionPattern(Enum):
    """Patterns for rule-governed graph composition."""

    SEQUENTIAL_BUILDING = "sequential_building"
    PARALLEL_CONSTRUCTION = "parallel_construction"
    NESTED_CONTEXTS = "nested_contexts"
    ITERATIVE_REFINEMENT = "iterative_refinement"
    CONDITIONAL_BRANCHING = "conditional_branching"


class ValidationLevel(Enum):
    """Levels of rule validation during composition."""

    STRICT = "strict"  # Every step must be valid
    PERMISSIVE = "permissive"  # Allow some rule bending for exploration
    ADVISORY = "advisory"  # Warn but don't block invalid steps


@dataclass
class CompositionRule:
    """Rule for graph composition patterns."""

    rule_id: str
    name: str
    description: str
    preconditions: List[Callable[[RelationalGraphWithCuts], bool]]
    transformation_sequence: List[Dict[str, Any]]
    postconditions: List[Callable[[RelationalGraphWithCuts], bool]]
    pattern_type: CompositionPattern


@dataclass
class CompositionPlan:
    """Plan for building a complex graph through composition."""

    plan_id: str
    title: str
    description: str
    target_pattern: CompositionPattern
    composition_steps: List[Dict[str, Any]]
    validation_level: ValidationLevel
    expected_outcome: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)


class RuleGovernedComposer:
    """System for rule-governed graph composition with validation."""

    def __init__(self, validation_level: ValidationLevel = ValidationLevel.STRICT):
        self.builder = SimpleGraphBuilder()
        self.validation_level = validation_level
        self.composition_rules: Dict[str, CompositionRule] = {}
        self.composition_plans: Dict[str, CompositionPlan] = {}
        self.active_compositions: Dict[str, str] = (
            {}
        )  # composition_id -> current_egi_id

        # Initialize built-in composition rules
        self._initialize_composition_rules()

    def _initialize_composition_rules(self):
        """Initialize built-in composition rules."""

        # Rule: Simple conjunction through vertex addition
        conjunction_rule = CompositionRule(
            rule_id="simple_conjunction",
            name="Simple Conjunction",
            description="Build conjunction by adding vertices sequentially",
            preconditions=[lambda egi: True],  # Always applicable
            transformation_sequence=[
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "element_type": "vertex",
                    "justification": "Add vertex for conjunction",
                }
            ],
            postconditions=[lambda egi: len(egi.V) > 0],
            pattern_type=CompositionPattern.SEQUENTIAL_BUILDING,
        )
        self.composition_rules[conjunction_rule.rule_id] = conjunction_rule

        # Rule: Binary relation construction
        relation_rule = CompositionRule(
            rule_id="binary_relation",
            name="Binary Relation",
            description="Build binary relation with two vertices and connecting edge",
            preconditions=[lambda egi: len(egi.V) >= 2],
            transformation_sequence=[
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "element_type": "edge",
                    "justification": "Connect vertices with relation",
                }
            ],
            postconditions=[lambda egi: len(egi.E) > 0],
            pattern_type=CompositionPattern.SEQUENTIAL_BUILDING,
        )
        self.composition_rules[relation_rule.rule_id] = relation_rule

        # Rule: Negation through cut insertion
        negation_rule = CompositionRule(
            rule_id="simple_negation",
            name="Simple Negation",
            description="Apply negation by inserting cut around elements",
            preconditions=[lambda egi: len(egi.V) > 0 or len(egi.E) > 0],
            transformation_sequence=[
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "element_type": "cut",
                    "justification": "Insert cut for negation",
                }
            ],
            postconditions=[lambda egi: len(egi.Cut) > 0],
            pattern_type=CompositionPattern.NESTED_CONTEXTS,
        )
        self.composition_rules[negation_rule.rule_id] = negation_rule

    def create_composition_plan(
        self,
        title: str,
        description: str,
        pattern: CompositionPattern,
        composition_steps: List[Dict[str, Any]],
    ) -> str:
        """Create a plan for complex graph composition."""
        plan_id = str(uuid.uuid4())

        plan = CompositionPlan(
            plan_id=plan_id,
            title=title,
            description=description,
            target_pattern=pattern,
            composition_steps=composition_steps,
            validation_level=self.validation_level,
            expected_outcome=self._analyze_expected_outcome(composition_steps),
        )

        self.composition_plans[plan_id] = plan
        return plan_id

    def execute_composition_plan(self, plan_id: str) -> str:
        """Execute a composition plan to build a graph."""
        plan = self.composition_plans.get(plan_id)
        if not plan:
            raise ValueError(f"Composition plan {plan_id} not found")

        # Start with empty context
        current_egi_id = self.builder.create_empty_context()
        self.active_compositions[plan_id] = current_egi_id

        executed_steps = []

        for i, step in enumerate(plan.composition_steps):
            try:
                # Validate preconditions if strict mode
                if self.validation_level == ValidationLevel.STRICT:
                    current_egi = self.builder.pipeline.get_egi_state(current_egi_id)
                    if not self._validate_step_preconditions(step, current_egi):
                        raise ValueError(f"Step {i+1} preconditions not met")

                # Execute transformation step
                new_egi_id = self.builder.pipeline.apply_transformation(
                    source_egi_id=current_egi_id,
                    rule_type=step["rule_type"],
                    transformation_data=step["transformation_data"],
                    context_type=ContextType.ERGASTERION,
                    logical_justification=step.get(
                        "justification", f"Composition step {i+1}"
                    ),
                )

                executed_steps.append(step)
                current_egi_id = new_egi_id
                self.active_compositions[plan_id] = current_egi_id

                # Validate postconditions
                if self.validation_level == ValidationLevel.STRICT:
                    new_egi = self.builder.pipeline.get_egi_state(new_egi_id)
                    if not self._validate_step_postconditions(step, new_egi):
                        print(f"Warning: Step {i+1} postconditions not fully satisfied")

            except Exception as e:
                if self.validation_level == ValidationLevel.STRICT:
                    raise e
                else:
                    print(f"Warning: Step {i+1} failed: {e}")
                    continue

        return current_egi_id

    def build_logical_expression(
        self, expression_type: str, components: List[Dict[str, Any]]
    ) -> str:
        """Build a logical expression through rule-governed composition."""

        if expression_type == "conjunction":
            return self._build_conjunction(components)
        elif expression_type == "disjunction":
            return self._build_disjunction(components)
        elif expression_type == "implication":
            return self._build_implication(components)
        elif expression_type == "negation":
            return self._build_negation(components)
        else:
            raise ValueError(f"Unknown expression type: {expression_type}")

    def _build_conjunction(self, components: List[Dict[str, Any]]) -> str:
        """Build conjunction through sequential vertex insertion."""
        steps = []

        for i, component in enumerate(components):
            steps.append(
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "vertex",
                        "element_id": component.get("id", f"v{i+1}"),
                        "target_area": "sheet",
                    },
                    "justification": f"Add component {i+1} for conjunction",
                }
            )

        plan_id = self.create_composition_plan(
            title="Conjunction Expression",
            description=f"Conjunction of {len(components)} components",
            pattern=CompositionPattern.SEQUENTIAL_BUILDING,
            composition_steps=steps,
        )

        return self.execute_composition_plan(plan_id)

    def _build_disjunction(self, components: List[Dict[str, Any]]) -> str:
        """Build disjunction through double negation (De Morgan's law)."""
        # ∨ = ¬(¬A ∧ ¬B) - disjunction as negation of conjunction of negations
        steps = []

        # First, create negated components
        for i, component in enumerate(components):
            # Add vertex
            steps.append(
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "vertex",
                        "element_id": component.get("id", f"v{i+1}"),
                        "target_area": "sheet",
                    },
                    "justification": f"Add component {i+1}",
                }
            )

            # Negate it with cut
            steps.append(
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "cut",
                        "element_id": f"neg_{i+1}",
                        "target_area": "sheet",
                        "enclosed_elements": frozenset(
                            [component.get("id", f"v{i+1}")]
                        ),
                    },
                    "justification": f"Negate component {i+1}",
                }
            )

        # Finally, negate the whole conjunction
        all_elements = []
        for i, component in enumerate(components):
            all_elements.extend([component.get("id", f"v{i+1}"), f"neg_{i+1}"])

        steps.append(
            {
                "rule_type": TransformationRuleType.INSERTION,
                "transformation_data": {
                    "element_type": "cut",
                    "element_id": "outer_neg",
                    "target_area": "sheet",
                    "enclosed_elements": frozenset(all_elements),
                },
                "justification": "Apply outer negation for disjunction",
            }
        )

        plan_id = self.create_composition_plan(
            title="Disjunction Expression",
            description=f"Disjunction of {len(components)} components via De Morgan's law",
            pattern=CompositionPattern.NESTED_CONTEXTS,
            composition_steps=steps,
        )

        return self.execute_composition_plan(plan_id)

    def _build_implication(self, components: List[Dict[str, Any]]) -> str:
        """Build implication A → B as ¬A ∨ B."""
        if len(components) != 2:
            raise ValueError("Implication requires exactly 2 components")

        antecedent = components[0]
        consequent = components[1]

        steps = [
            # Add antecedent
            {
                "rule_type": TransformationRuleType.INSERTION,
                "transformation_data": {
                    "element_type": "vertex",
                    "element_id": antecedent.get("id", "antecedent"),
                    "target_area": "sheet",
                },
                "justification": "Add antecedent",
            },
            # Add consequent
            {
                "rule_type": TransformationRuleType.INSERTION,
                "transformation_data": {
                    "element_type": "vertex",
                    "element_id": consequent.get("id", "consequent"),
                    "target_area": "sheet",
                },
                "justification": "Add consequent",
            },
            # Negate antecedent
            {
                "rule_type": TransformationRuleType.INSERTION,
                "transformation_data": {
                    "element_type": "cut",
                    "element_id": "neg_antecedent",
                    "target_area": "sheet",
                    "enclosed_elements": frozenset(
                        [antecedent.get("id", "antecedent")]
                    ),
                },
                "justification": "Negate antecedent for implication",
            },
        ]

        plan_id = self.create_composition_plan(
            title="Implication Expression",
            description="Implication A → B as ¬A ∨ B",
            pattern=CompositionPattern.NESTED_CONTEXTS,
            composition_steps=steps,
        )

        return self.execute_composition_plan(plan_id)

    def _build_negation(self, components: List[Dict[str, Any]]) -> str:
        """Build negation by wrapping components in cut."""
        if len(components) != 1:
            raise ValueError("Negation requires exactly 1 component")

        component = components[0]

        steps = [
            # Add component
            {
                "rule_type": TransformationRuleType.INSERTION,
                "transformation_data": {
                    "element_type": "vertex",
                    "element_id": component.get("id", "v1"),
                    "target_area": "sheet",
                },
                "justification": "Add component to be negated",
            },
            # Negate with cut
            {
                "rule_type": TransformationRuleType.INSERTION,
                "transformation_data": {
                    "element_type": "cut",
                    "element_id": "negation_cut",
                    "target_area": "sheet",
                    "enclosed_elements": frozenset([component.get("id", "v1")]),
                },
                "justification": "Apply negation with cut",
            },
        ]

        plan_id = self.create_composition_plan(
            title="Negation Expression",
            description="Simple negation with cut",
            pattern=CompositionPattern.NESTED_CONTEXTS,
            composition_steps=steps,
        )

        return self.execute_composition_plan(plan_id)

    def _validate_step_preconditions(
        self, step: Dict[str, Any], egi: RelationalGraphWithCuts
    ) -> bool:
        """Validate preconditions for a composition step."""
        # Simplified validation - could be more sophisticated
        rule_type = step.get("rule_type")
        element_type = step.get("transformation_data", {}).get("element_type")

        if rule_type == TransformationRuleType.INSERTION:
            if element_type == "edge":
                # Need at least 2 vertices for edge
                return len(egi.V) >= 2
            elif element_type == "cut":
                # Need at least 1 element to enclose
                return len(egi.V) > 0 or len(egi.E) > 0

        return True

    def _validate_step_postconditions(
        self, step: Dict[str, Any], egi: RelationalGraphWithCuts
    ) -> bool:
        """Validate postconditions for a composition step."""
        # Simplified validation
        rule_type = step.get("rule_type")
        element_type = step.get("transformation_data", {}).get("element_type")

        if rule_type == TransformationRuleType.INSERTION:
            if element_type == "vertex":
                return len(egi.V) > 0
            elif element_type == "edge":
                return len(egi.E) > 0
            elif element_type == "cut":
                return len(egi.Cut) > 0

        return True

    def _analyze_expected_outcome(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze expected outcome of composition steps."""
        vertex_count = 0
        edge_count = 0
        cut_count = 0

        for step in steps:
            if step.get("rule_type") == TransformationRuleType.INSERTION:
                element_type = step.get("transformation_data", {}).get("element_type")
                if element_type == "vertex":
                    vertex_count += 1
                elif element_type == "edge":
                    edge_count += 1
                elif element_type == "cut":
                    cut_count += 1

        return {
            "expected_vertices": vertex_count,
            "expected_edges": edge_count,
            "expected_cuts": cut_count,
            "total_elements": vertex_count + edge_count + cut_count,
        }

    def analyze_composition(self, composition_id: str) -> Dict[str, Any]:
        """Analyze a completed composition."""
        if composition_id not in self.active_compositions:
            return {"error": "Composition not found"}

        final_egi_id = self.active_compositions[composition_id]
        final_egi = self.builder.pipeline.get_egi_state(final_egi_id)

        if not final_egi:
            return {"error": "Final EGI not found"}

        return {
            "composition_id": composition_id,
            "final_state": {
                "vertices": len(final_egi.V),
                "edges": len(final_egi.E),
                "cuts": len(final_egi.Cut),
                "total_elements": len(final_egi.V)
                + len(final_egi.E)
                + len(final_egi.Cut),
            },
            "validation_level": self.validation_level.value,
            "rule_compliance": (
                "strict"
                if self.validation_level == ValidationLevel.STRICT
                else "permissive"
            ),
        }


def demonstrate_rule_governed_composition():
    """Demonstrate rule-governed graph composition."""

    print("⚖️  Rule-Governed Graph Composition")
    print("=" * 35)

    composer = RuleGovernedComposer(ValidationLevel.STRICT)

    # Build logical expressions
    expressions = [
        {
            "type": "conjunction",
            "components": [{"id": "A"}, {"id": "B"}, {"id": "C"}],
            "description": "A ∧ B ∧ C",
        },
        {"type": "negation", "components": [{"id": "P"}], "description": "¬P"},
        {
            "type": "implication",
            "components": [{"id": "P"}, {"id": "Q"}],
            "description": "P → Q",
        },
        {
            "type": "disjunction",
            "components": [{"id": "X"}, {"id": "Y"}],
            "description": "X ∨ Y",
        },
    ]

    built_expressions = []

    for expr in expressions:
        print(f"\n🔧 Building: {expr['description']}")

        try:
            final_egi_id = composer.build_logical_expression(
                expr["type"], expr["components"]
            )

            # Analyze the result
            final_egi = composer.builder.pipeline.get_egi_state(final_egi_id)
            if final_egi:
                print(
                    f"   Result: {len(final_egi.V)}V, {len(final_egi.E)}E, {len(final_egi.Cut)}C"
                )
                print(f"   EGI ID: {final_egi_id[:8]}...")
                built_expressions.append(final_egi_id)

        except Exception as e:
            print(f"   Error: {e}")

    print(f"\n📊 Summary:")
    print(f"   Expressions built: {len(built_expressions)}")
    print(f"   Validation level: {composer.validation_level.value}")
    print(f"   Composition rules: {len(composer.composition_rules)}")
    print(f"   Active compositions: {len(composer.active_compositions)}")

    return composer, built_expressions


if __name__ == "__main__":
    demonstrate_rule_governed_composition()
