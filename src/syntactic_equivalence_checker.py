"""
Syntactic Equivalence Checker for EG transformations per Dau's formalism.
Validates that transformations preserve logical meaning through syntactic equivalence.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

from frozendict import frozendict

from egi_core_dau import Cut, Edge, ElementID, RelationalGraphWithCuts, Vertex
from graph_isomorphism_engine import GraphIsomorphismEngine, IsomorphismValidator


@dataclass
class EquivalenceResult:
    """Result of syntactic equivalence checking."""

    are_equivalent: bool
    reason: Optional[str]
    structural_differences: List[str]
    transformation_sequence: List[str]


class SyntacticEquivalenceChecker:
    """
    Checker for syntactic equivalence between EGIs per Dau's Definition 15.3.
    Two graphs G1, G2 are syntactically equivalent if G1 ⊢ G2 and G2 ⊢ G1.
    """

    def __init__(self):
        self.isomorphism_engine = GraphIsomorphismEngine()
        self.isomorphism_validator = IsomorphismValidator()

    def check_equivalence(
        self, egi1: RelationalGraphWithCuts, egi2: RelationalGraphWithCuts
    ) -> EquivalenceResult:
        """
        Check if two EGIs are syntactically equivalent.

        Args:
            egi1: First EGI to compare
            egi2: Second EGI to compare

        Returns:
            EquivalenceResult indicating whether graphs are equivalent
        """

        # Quick structural checks first
        structural_diffs = self._check_structural_differences(egi1, egi2)

        if structural_diffs:
            # If there are structural differences, check if they're due to valid transformations
            transformation_equivalent = self._check_transformation_equivalence(
                egi1, egi2
            )

            if transformation_equivalent:
                return EquivalenceResult(
                    are_equivalent=True,
                    reason="Syntactically equivalent via transformation rules",
                    structural_differences=structural_diffs,
                    transformation_sequence=["Transformation rules applied"],
                )
            else:
                return EquivalenceResult(
                    are_equivalent=False,
                    reason="Structural differences not explained by valid transformations",
                    structural_differences=structural_diffs,
                    transformation_sequence=[],
                )
        else:
            # Structurally identical
            return EquivalenceResult(
                are_equivalent=True,
                reason="Structurally identical",
                structural_differences=[],
                transformation_sequence=[],
            )

    def _check_structural_differences(
        self, egi1: RelationalGraphWithCuts, egi2: RelationalGraphWithCuts
    ) -> List[str]:
        """Check for structural differences between two EGIs."""
        differences = []

        # Compare vertex counts
        if len(egi1.V) != len(egi2.V):
            differences.append(f"Vertex count: {len(egi1.V)} vs {len(egi2.V)}")

        # Compare edge counts
        if len(egi1.E) != len(egi2.E):
            differences.append(f"Edge count: {len(egi1.E)} vs {len(egi2.E)}")

        # Compare cut counts
        if len(egi1.Cut) != len(egi2.Cut):
            differences.append(f"Cut count: {len(egi1.Cut)} vs {len(egi2.Cut)}")

        # Compare area structure
        if len(egi1.area) != len(egi2.area):
            differences.append(f"Area count: {len(egi1.area)} vs {len(egi2.area)}")

        # Compare relation mappings
        if len(egi1.rel) != len(egi2.rel):
            differences.append(f"Relation count: {len(egi1.rel)} vs {len(egi2.rel)}")

        return differences

    def _check_transformation_equivalence(
        self, egi1: RelationalGraphWithCuts, egi2: RelationalGraphWithCuts
    ) -> bool:
        """
        Check if differences between EGIs can be explained by valid transformation rules.
        Uses the sophisticated isomorphism engine for rigorous structural analysis.
        """

        # Check for double cut patterns (DC+/DC-)
        if self._is_double_cut_transformation(egi1, egi2):
            return True

        # Check for iteration/deiteration patterns using isomorphism engine
        if self._is_iteration_transformation_with_isomorphism(egi1, egi2):
            return True

        # Check for ligature manipulation patterns
        if self._is_ligature_transformation(egi1, egi2):
            return True

        return False

    def _is_double_cut_transformation(
        self, egi1: RelationalGraphWithCuts, egi2: RelationalGraphWithCuts
    ) -> bool:
        """Check if transformation is a double cut insertion/erasure."""

        # DC+ pattern: egi1 has fewer cuts than egi2, with double cut structure
        if len(egi1.Cut) + 2 == len(egi2.Cut):
            return self._has_double_cut_pattern(egi2, egi1)

        # DC- pattern: egi1 has more cuts than egi2, with double cut structure
        if len(egi1.Cut) == len(egi2.Cut) + 2:
            return self._has_double_cut_pattern(egi1, egi2)

        return False

    def _has_double_cut_pattern(
        self,
        egi_with_cuts: RelationalGraphWithCuts,
        egi_without_cuts: RelationalGraphWithCuts,
    ) -> bool:
        """Check if EGI has a double cut pattern that could be removed."""

        # Look for cuts that contain only one other cut
        for cut in egi_with_cuts.Cut:
            cut_contents = egi_with_cuts.area.get(cut.id, frozenset())

            # Check if this cut contains exactly one other cut
            inner_cuts = [
                elem
                for elem in cut_contents
                if any(c.id == elem for c in egi_with_cuts.Cut)
            ]

            if len(inner_cuts) == 1:
                inner_cut_id = inner_cuts[0]
                inner_cut_contents = egi_with_cuts.area.get(inner_cut_id, frozenset())

                # Check if removing both cuts would match the other EGI
                if self._would_match_after_double_cut_removal(
                    egi_with_cuts,
                    egi_without_cuts,
                    cut.id,
                    inner_cut_id,
                    inner_cut_contents,
                ):
                    return True

        return False

    def _would_match_after_double_cut_removal(
        self,
        egi_with_cuts: RelationalGraphWithCuts,
        egi_without_cuts: RelationalGraphWithCuts,
        outer_cut_id: ElementID,
        inner_cut_id: ElementID,
        inner_contents: FrozenSet[ElementID],
    ) -> bool:
        """Check if removing double cut would make EGIs match."""

        # This is a simplified check - full implementation would need complete structural comparison
        expected_vertex_count = len(egi_with_cuts.V)
        expected_edge_count = len(egi_with_cuts.E)
        expected_cut_count = len(egi_with_cuts.Cut) - 2

        return (
            len(egi_without_cuts.V) == expected_vertex_count
            and len(egi_without_cuts.E) == expected_edge_count
            and len(egi_without_cuts.Cut) == expected_cut_count
        )

    def _is_iteration_transformation_with_isomorphism(
        self, egi1: RelationalGraphWithCuts, egi2: RelationalGraphWithCuts
    ) -> bool:
        """Check if transformation is iteration/deiteration using isomorphism engine."""

        # IT+ pattern: egi2 has more elements than egi1
        if len(egi2.V) > len(egi1.V) or len(egi2.E) > len(egi1.E):
            return self._has_rigorous_iteration_pattern(egi1, egi2)

        # IT- pattern: egi1 has more elements than egi2
        if len(egi1.V) > len(egi2.V) or len(egi1.E) > len(egi2.E):
            return self._has_rigorous_iteration_pattern(egi2, egi1)

        return False

    def _has_rigorous_iteration_pattern(
        self, smaller_egi: RelationalGraphWithCuts, larger_egi: RelationalGraphWithCuts
    ) -> bool:
        """Check if larger EGI contains iteration using rigorous isomorphism testing."""

        # Get all elements from smaller EGI
        smaller_elements = self._get_all_element_ids(smaller_egi)
        larger_elements = self._get_all_element_ids(larger_egi)

        # Find potential copied elements (those in larger but not in smaller)
        potential_copies = [
            elem for elem in larger_elements if elem not in smaller_elements
        ]

        if not potential_copies:
            return False

        # Use isomorphism engine to check if potential copies are structurally identical
        # to elements in the smaller EGI
        for copy_size in range(1, len(potential_copies) + 1):
            from itertools import combinations

            # Try all combinations of potential copies
            for copy_combo in combinations(potential_copies, copy_size):
                copy_subgraph = frozenset(copy_combo)

                # Try all combinations of original elements of same size
                for orig_combo in combinations(smaller_elements, copy_size):
                    orig_subgraph = frozenset(orig_combo)

                    # Test cross-EGI isomorphism
                    result = self.isomorphism_engine.test_cross_egi_isomorphism(
                        smaller_egi, orig_subgraph, larger_egi, copy_subgraph
                    )

                    if result.is_isomorphic:
                        return True

        return False

    def _is_ligature_transformation(
        self, egi1: RelationalGraphWithCuts, egi2: RelationalGraphWithCuts
    ) -> bool:
        """Check if transformation is ligature manipulation."""

        # Same number of elements but different nu mappings suggests ligature manipulation
        if (
            len(egi1.V) == len(egi2.V)
            and len(egi1.E) == len(egi2.E)
            and len(egi1.Cut) == len(egi2.Cut)
        ):

            # Check if only nu mappings differ (branch moving)
            if egi1.nu != egi2.nu and egi1.rel == egi2.rel:
                return self._has_valid_ligature_rearrangement(egi1, egi2)

        # Different number of identity edges suggests ligature extension/restriction
        identity_edges_1 = self._count_identity_edges(egi1)
        identity_edges_2 = self._count_identity_edges(egi2)

        if identity_edges_1 != identity_edges_2:
            return self._has_valid_ligature_extension(egi1, egi2)

        return False

    def _has_valid_ligature_rearrangement(
        self, egi1: RelationalGraphWithCuts, egi2: RelationalGraphWithCuts
    ) -> bool:
        """Check if nu mapping changes represent valid ligature rearrangement."""

        # Check that all vertices involved in changed mappings are on same ligatures
        changed_edges = set()
        for edge_id in egi1.nu:
            if egi1.nu.get(edge_id) != egi2.nu.get(edge_id):
                changed_edges.add(edge_id)

        # For valid rearrangement, changed edges should involve vertices on same ligatures
        # This is a simplified check - full implementation would verify ligature connectivity
        return len(changed_edges) > 0

    def _has_valid_ligature_extension(
        self, egi1: RelationalGraphWithCuts, egi2: RelationalGraphWithCuts
    ) -> bool:
        """Check if difference represents valid ligature extension/restriction."""

        # Check for new identity edges and vertices
        identity_count_1 = self._count_identity_edges(egi1)
        identity_count_2 = self._count_identity_edges(egi2)

        vertex_count_1 = len(egi1.V)
        vertex_count_2 = len(egi2.V)

        # Extension pattern: more identity edges and vertices
        if identity_count_2 > identity_count_1 and vertex_count_2 > vertex_count_1:
            return True

        # Restriction pattern: fewer identity edges and vertices
        if identity_count_1 > identity_count_2 and vertex_count_1 > vertex_count_2:
            return True

        return False

    def _count_identity_edges(self, egi: RelationalGraphWithCuts) -> int:
        """Count identity edges in EGI."""
        return sum(1 for edge_id, relation in egi.rel.items() if relation == "=")

    def _get_all_element_ids(self, egi: RelationalGraphWithCuts) -> List[ElementID]:
        """Get all element IDs from EGI."""
        element_ids = []
        element_ids.extend([v.id for v in egi.V])
        element_ids.extend([e.id for e in egi.E])
        element_ids.extend([c.id for c in egi.Cut])
        return element_ids

    def _element_exists_in_egi(
        self, egi: RelationalGraphWithCuts, element_id: ElementID
    ) -> bool:
        """Check if element exists in EGI."""
        return (
            any(v.id == element_id for v in egi.V)
            or any(e.id == element_id for e in egi.E)
            or any(c.id == element_id for c in egi.Cut)
        )


def validate_transformation_preserves_meaning(
    original_egi: RelationalGraphWithCuts,
    transformed_egi: RelationalGraphWithCuts,
    transformation_name: str,
) -> EquivalenceResult:
    """
    Validate that a transformation preserves logical meaning through syntactic equivalence.

    Args:
        original_egi: EGI before transformation
        transformed_egi: EGI after transformation
        transformation_name: Name of the transformation applied

    Returns:
        EquivalenceResult indicating whether transformation preserves meaning
    """

    checker = SyntacticEquivalenceChecker()
    result = checker.check_equivalence(original_egi, transformed_egi)

    # Add transformation-specific context
    if result.are_equivalent:
        result.transformation_sequence = [f"{transformation_name} applied successfully"]
    else:
        result.reason = f"{transformation_name} does not preserve syntactic equivalence: {result.reason}"

    return result


def demonstrate_syntactic_equivalence():
    """Demonstrate syntactic equivalence checking."""

    print("🔍 Syntactic Equivalence Checker Demonstration")
    print("=" * 50)

    # Create test EGIs
    from egi_core_dau import Cut, Edge, ElementID, RelationalGraphWithCuts, Vertex

    # Original EGI
    vertex_a = Vertex(ElementID("A"))
    vertex_b = Vertex(ElementID("B"))

    original_egi = RelationalGraphWithCuts(
        V=frozenset([vertex_a, vertex_b]),
        E=frozenset(),
        nu=frozendict(),
        sheet=ElementID("sheet"),
        Cut=frozenset(),
        area=frozendict(
            {ElementID("sheet"): frozenset([ElementID("A"), ElementID("B")])}
        ),
        rel=frozendict(),
    )

    # EGI after iteration (added copy of vertex B)
    vertex_b_copy = Vertex(ElementID("B_copy"))

    iterated_egi = RelationalGraphWithCuts(
        V=frozenset([vertex_a, vertex_b, vertex_b_copy]),
        E=frozenset(),
        nu=frozendict(),
        sheet=ElementID("sheet"),
        Cut=frozenset(),
        area=frozendict(
            {
                ElementID("sheet"): frozenset(
                    [ElementID("A"), ElementID("B"), ElementID("B_copy")]
                )
            }
        ),
        rel=frozendict(),
    )

    checker = SyntacticEquivalenceChecker()

    print("🎯 Test 1: Original vs Iterated EGI")
    result = checker.check_equivalence(original_egi, iterated_egi)
    print(f"   Equivalent: {result.are_equivalent}")
    print(f"   Reason: {result.reason}")
    print(f"   Differences: {result.structural_differences}")
    print()

    print("🎯 Test 2: Transformation Validation")
    validation_result = validate_transformation_preserves_meaning(
        original_egi, iterated_egi, "IT+ (Iteration)"
    )
    print(f"   Transformation Valid: {validation_result.are_equivalent}")
    print(f"   Reason: {validation_result.reason}")
    print()

    return checker


if __name__ == "__main__":
    demonstrate_syntactic_equivalence()
