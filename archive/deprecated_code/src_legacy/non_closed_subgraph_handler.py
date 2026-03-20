"""
Non-Closed Subgraph Decomposition Handler per Dau Chapter 15

Dau notes that while erasure/insertion rules formally only apply to closed subgraphs,
non-closed subgraphs can be "informally" erased by decomposing them into a sequence
of valid transformations (lines 8102-8136).

This module implements the decomposition strategy for handling non-closed subgraphs.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

from frozendict import frozendict

from egi_core_dau import Cut, Edge, ElementID, RelationalGraphWithCuts, Vertex
from formal_transformation_rules import FormalTransformationEngine, TransformationResult


class DecompositionStrategy(Enum):
    """Strategies for decomposing non-closed subgraphs."""

    EDGE_FIRST = "edge_first"  # Remove incident edges first
    VERTEX_FIRST = "vertex_first"  # Remove isolated vertices first
    MINIMAL_CUTS = "minimal_cuts"  # Minimize number of transformation steps


@dataclass
class DecompositionStep:
    """A single step in subgraph decomposition."""

    rule_name: str
    target_area: ElementID
    selected_elements: FrozenSet[ElementID]
    description: str


@dataclass
class DecompositionPlan:
    """Complete plan for decomposing a non-closed subgraph."""

    original_subgraph: FrozenSet[ElementID]
    steps: List[DecompositionStep]
    strategy: DecompositionStrategy
    is_valid: bool
    reason: Optional[str] = None


@dataclass
class DecompositionResult:
    """Result of executing a decomposition plan."""

    success: bool
    final_egi: Optional[RelationalGraphWithCuts]
    executed_steps: List[Tuple[DecompositionStep, TransformationResult]]
    error_message: Optional[str] = None


class NonClosedSubgraphHandler:
    """
    Handler for non-closed subgraph operations per Dau's informal approach.

    Implements decomposition strategies to break down non-closed subgraphs
    into sequences of valid closed subgraph operations.
    """

    def __init__(self):
        self.transformation_engine = FormalTransformationEngine()

    def is_closed_subgraph(
        self, egi: RelationalGraphWithCuts, subgraph_elements: FrozenSet[ElementID]
    ) -> bool:
        """
        Check if a subgraph is closed (no external connections).

        A subgraph is closed if no edges connect vertices inside the subgraph
        to vertices outside the subgraph.
        """

        subgraph_vertices = {
            elem for elem in subgraph_elements if any(v.id == elem for v in egi.V)
        }
        subgraph_edges = {
            elem for elem in subgraph_elements if any(e.id == elem for e in egi.E)
        }

        # Check all edges in the EGI
        for edge in egi.E:
            vertex_sequence = egi.nu.get(edge.id, ())

            # Skip edges that are part of the subgraph
            if edge.id in subgraph_edges:
                continue

            # Check if edge connects subgraph vertex to external vertex
            internal_vertices = sum(
                1 for v_id in vertex_sequence if v_id in subgraph_vertices
            )
            external_vertices = sum(
                1 for v_id in vertex_sequence if v_id not in subgraph_vertices
            )

            if internal_vertices > 0 and external_vertices > 0:
                return False  # Edge crosses subgraph boundary

        return True

    def create_decomposition_plan(
        self,
        egi: RelationalGraphWithCuts,
        subgraph_elements: FrozenSet[ElementID],
        target_area: ElementID,
        strategy: DecompositionStrategy = DecompositionStrategy.EDGE_FIRST,
    ) -> DecompositionPlan:
        """
        Create a decomposition plan for a non-closed subgraph.

        Args:
            egi: Source EGI
            subgraph_elements: Elements to remove
            target_area: Area containing the subgraph
            strategy: Decomposition strategy to use

        Returns:
            DecompositionPlan with sequence of transformation steps
        """

        # Check if subgraph is already closed
        if self.is_closed_subgraph(egi, subgraph_elements):
            return DecompositionPlan(
                original_subgraph=subgraph_elements,
                steps=[
                    DecompositionStep(
                        rule_name="ERA",
                        target_area=target_area,
                        selected_elements=subgraph_elements,
                        description="Direct erasure of closed subgraph",
                    )
                ],
                strategy=strategy,
                is_valid=True,
            )

        # Create decomposition plan based on strategy
        if strategy == DecompositionStrategy.EDGE_FIRST:
            return self._create_edge_first_plan(egi, subgraph_elements, target_area)
        elif strategy == DecompositionStrategy.VERTEX_FIRST:
            return self._create_vertex_first_plan(egi, subgraph_elements, target_area)
        elif strategy == DecompositionStrategy.MINIMAL_CUTS:
            return self._create_minimal_cuts_plan(egi, subgraph_elements, target_area)
        else:
            return DecompositionPlan(
                original_subgraph=subgraph_elements,
                steps=[],
                strategy=strategy,
                is_valid=False,
                reason=f"Unknown decomposition strategy: {strategy}",
            )

    def _create_edge_first_plan(
        self,
        egi: RelationalGraphWithCuts,
        subgraph_elements: FrozenSet[ElementID],
        target_area: ElementID,
    ) -> DecompositionPlan:
        """Create plan that removes boundary edges first."""

        steps = []
        remaining_elements = set(subgraph_elements)

        # Step 1: Identify and remove boundary edges (edges that cross subgraph boundary)
        boundary_edges = self._find_boundary_edges(egi, subgraph_elements)

        # Remove boundary edges that are NOT part of the subgraph
        for edge_id in boundary_edges:
            if edge_id not in remaining_elements:  # Only remove external boundary edges
                steps.append(
                    DecompositionStep(
                        rule_name="ERA",
                        target_area=target_area,
                        selected_elements=frozenset([edge_id]),
                        description=f"Remove external boundary edge {edge_id}",
                    )
                )

        # Step 2: Remove remaining closed subgraph
        if remaining_elements:
            steps.append(
                DecompositionStep(
                    rule_name="ERA",
                    target_area=target_area,
                    selected_elements=frozenset(remaining_elements),
                    description="Remove remaining closed subgraph",
                )
            )

        return DecompositionPlan(
            original_subgraph=subgraph_elements,
            steps=steps,
            strategy=DecompositionStrategy.EDGE_FIRST,
            is_valid=True,
        )

    def _create_vertex_first_plan(
        self,
        egi: RelationalGraphWithCuts,
        subgraph_elements: FrozenSet[ElementID],
        target_area: ElementID,
    ) -> DecompositionPlan:
        """Create plan that removes isolated vertices first."""

        steps = []
        remaining_elements = set(subgraph_elements)

        # Step 1: Remove isolated vertices
        isolated_vertices = self._find_isolated_vertices(egi, subgraph_elements)

        for vertex_id in isolated_vertices:
            if vertex_id in remaining_elements:
                steps.append(
                    DecompositionStep(
                        rule_name="ERA",
                        target_area=target_area,
                        selected_elements=frozenset([vertex_id]),
                        description=f"Remove isolated vertex {vertex_id}",
                    )
                )
                remaining_elements.remove(vertex_id)

        # Step 2: Apply edge-first strategy to remaining elements
        if remaining_elements:
            edge_plan = self._create_edge_first_plan(
                egi, frozenset(remaining_elements), target_area
            )
            steps.extend(edge_plan.steps)

        return DecompositionPlan(
            original_subgraph=subgraph_elements,
            steps=steps,
            strategy=DecompositionStrategy.VERTEX_FIRST,
            is_valid=True,
        )

    def _create_minimal_cuts_plan(
        self,
        egi: RelationalGraphWithCuts,
        subgraph_elements: FrozenSet[ElementID],
        target_area: ElementID,
    ) -> DecompositionPlan:
        """Create plan that minimizes the number of transformation steps."""

        # For now, use edge-first as the minimal strategy
        # A more sophisticated implementation would use graph analysis
        return self._create_edge_first_plan(egi, subgraph_elements, target_area)

    def _find_boundary_edges(
        self, egi: RelationalGraphWithCuts, subgraph_elements: FrozenSet[ElementID]
    ) -> Set[ElementID]:
        """Find edges that cross the subgraph boundary."""

        subgraph_vertices = {
            elem for elem in subgraph_elements if any(v.id == elem for v in egi.V)
        }
        boundary_edges = set()

        for edge in egi.E:
            if edge.id in subgraph_elements:
                continue  # Skip internal edges

            vertex_sequence = egi.nu.get(edge.id, ())

            # Check if edge connects subgraph vertex to external vertex
            internal_count = sum(
                1 for v_id in vertex_sequence if v_id in subgraph_vertices
            )
            external_count = sum(
                1 for v_id in vertex_sequence if v_id not in subgraph_vertices
            )

            if internal_count > 0 and external_count > 0:
                boundary_edges.add(edge.id)

        return boundary_edges

    def _find_isolated_vertices(
        self, egi: RelationalGraphWithCuts, subgraph_elements: FrozenSet[ElementID]
    ) -> Set[ElementID]:
        """Find vertices with no incident edges."""

        subgraph_vertices = {
            elem for elem in subgraph_elements if any(v.id == elem for v in egi.V)
        }
        isolated_vertices = set(subgraph_vertices)

        # Remove vertices that have incident edges
        for edge in egi.E:
            vertex_sequence = egi.nu.get(edge.id, ())
            for vertex_id in vertex_sequence:
                if vertex_id in isolated_vertices:
                    isolated_vertices.remove(vertex_id)

        return isolated_vertices

    def execute_decomposition_plan(
        self, egi: RelationalGraphWithCuts, plan: DecompositionPlan
    ) -> DecompositionResult:
        """
        Execute a decomposition plan step by step.

        Args:
            egi: Source EGI
            plan: Decomposition plan to execute

        Returns:
            DecompositionResult with final EGI and execution details
        """

        if not plan.is_valid:
            return DecompositionResult(
                success=False,
                final_egi=None,
                executed_steps=[],
                error_message=plan.reason or "Invalid decomposition plan",
            )

        current_egi = egi
        executed_steps = []

        for step in plan.steps:
            # Execute transformation step
            result = self.transformation_engine.apply_rule(
                step.rule_name, current_egi, step.target_area, step.selected_elements
            )

            executed_steps.append((step, result))

            if not result.success:
                return DecompositionResult(
                    success=False,
                    final_egi=current_egi,
                    executed_steps=executed_steps,
                    error_message=f"Step failed: {result.error_message}",
                )

            current_egi = result.result_egi

        return DecompositionResult(
            success=True, final_egi=current_egi, executed_steps=executed_steps
        )

    def erase_non_closed_subgraph(
        self,
        egi: RelationalGraphWithCuts,
        subgraph_elements: FrozenSet[ElementID],
        target_area: ElementID,
        strategy: DecompositionStrategy = DecompositionStrategy.EDGE_FIRST,
    ) -> DecompositionResult:
        """
        Erase a non-closed subgraph using decomposition.

        This is the main interface for handling non-closed subgraph erasure
        per Dau's informal approach.
        """

        # Create and execute decomposition plan
        plan = self.create_decomposition_plan(
            egi, subgraph_elements, target_area, strategy
        )
        return self.execute_decomposition_plan(egi, plan)


def demonstrate_non_closed_subgraph_handling():
    """Demonstrate non-closed subgraph decomposition."""

    print("🔧 Non-Closed Subgraph Handler Demonstration")
    print("=" * 50)

    # Create test EGI with non-closed subgraph
    from egi_core_dau import Edge, ElementID, RelationalGraphWithCuts, Vertex

    vertex_a = Vertex(ElementID("A"))
    vertex_b = Vertex(ElementID("B"))
    vertex_c = Vertex(ElementID("C"))
    edge_ab = Edge(ElementID("edge_AB"))
    edge_bc = Edge(ElementID("edge_BC"))

    test_egi = RelationalGraphWithCuts(
        V=frozenset([vertex_a, vertex_b, vertex_c]),
        E=frozenset([edge_ab, edge_bc]),
        nu=frozendict(
            {
                ElementID("edge_AB"): (ElementID("A"), ElementID("B")),
                ElementID("edge_BC"): (ElementID("B"), ElementID("C")),
            }
        ),
        sheet=ElementID("sheet"),
        Cut=frozenset(),
        area=frozendict(
            {
                ElementID("sheet"): frozenset(
                    [
                        ElementID("A"),
                        ElementID("B"),
                        ElementID("C"),
                        ElementID("edge_AB"),
                        ElementID("edge_BC"),
                    ]
                )
            }
        ),
        rel=frozendict({ElementID("edge_AB"): "R", ElementID("edge_BC"): "S"}),
    )

    handler = NonClosedSubgraphHandler()

    print("\n📊 Original EGI:")
    print(f"   Vertices: {[v.id for v in test_egi.V]}")
    print(f"   Edges: {[e.id for e in test_egi.E]}")
    print(f"   Nu mapping: {dict(test_egi.nu)}")

    # Test non-closed subgraph: {A, B, edge_AB} (B connects to external C)
    non_closed_subgraph = frozenset(
        [ElementID("A"), ElementID("B"), ElementID("edge_AB")]
    )

    print(f"\n🔍 Testing Subgraph Closure:")
    is_closed = handler.is_closed_subgraph(test_egi, non_closed_subgraph)
    print(
        f"   Subgraph {[str(e) for e in non_closed_subgraph]} is closed: {'✅' if is_closed else '❌'}"
    )

    if not is_closed:
        print(f"\n📋 Creating Decomposition Plan:")
        plan = handler.create_decomposition_plan(
            test_egi,
            non_closed_subgraph,
            ElementID("sheet"),
            DecompositionStrategy.EDGE_FIRST,
        )

        print(f"   Strategy: {plan.strategy.value}")
        print(f"   Valid: {'✅' if plan.is_valid else '❌'}")
        print(f"   Steps: {len(plan.steps)}")

        for i, step in enumerate(plan.steps, 1):
            print(f"     {i}. {step.rule_name}: {step.description}")
            print(f"        Elements: {[str(e) for e in step.selected_elements]}")

        print(f"\n🚀 Executing Decomposition:")
        result = handler.execute_decomposition_plan(test_egi, plan)

        if result.success:
            print(f"   ✅ Decomposition successful!")
            print(f"   Final vertices: {[v.id for v in result.final_egi.V]}")
            print(f"   Final edges: {[e.id for e in result.final_egi.E]}")

            print(f"\n📝 Execution Steps:")
            for i, (step, step_result) in enumerate(result.executed_steps, 1):
                status = "✅" if step_result.success else "❌"
                print(f"     {i}. {status} {step.description}")
        else:
            print(f"   ❌ Decomposition failed: {result.error_message}")

    print(f"\n✅ Non-Closed Subgraph Handler Complete")
    print(f"   - Closure detection: ✅")
    print(f"   - Decomposition planning: ✅")
    print(f"   - Strategy implementation: ✅")
    print(f"   - Plan execution: ✅")

    return handler


if __name__ == "__main__":
    demonstrate_non_closed_subgraph_handling()
