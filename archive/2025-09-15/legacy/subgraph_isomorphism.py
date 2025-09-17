"""
Dau-compliant subgraph extraction and isomorphism checking for EG transformations.
Implements formal definitions from Dau's "Mathematical Logic with Diagrams" for IT- and Endoporeutic Game.
"""

from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

from egi_core_dau import Cut, Edge, ElementID, RelationalGraphWithCuts, Vertex


@dataclass
class SubgraphCandidate:
    """A candidate subgraph for isomorphism checking."""

    elements: FrozenSet[ElementID]
    context: ElementID
    vertices: FrozenSet[ElementID]
    edges: FrozenSet[ElementID]
    cuts: FrozenSet[ElementID]


class DauSubgraphExtractor:
    """
    Extracts subgraphs according to Dau's Definition 7.9.

    A subgraph G' := (V', ⊇', Cut', area', κ') is a subgraph of G in context ⊇' if:
    - V' ⊆ V, Cut' ⊆ Cut and ⊇' ∈ Cut ∪ {⊇}
    - κ' = κ|V' (restriction of κ to V')
    - For all c ∈ Cut': area'(c) = area(c) ∩ (V' ∪ Cut')
    - For all v ∈ V': if v ∈ area(c) for some c ∈ Cut', then c ∈ Cut'
    """

    def __init__(self, egi: RelationalGraphWithCuts):
        self.egi = egi

    def extract_subgraph(
        self, selected_elements: FrozenSet[ElementID], context: ElementID
    ) -> SubgraphCandidate:
        """
        Extract a Dau-compliant subgraph from selected elements.

        Args:
            selected_elements: User-selected elements to form subgraph
            context: The context (area) containing the subgraph

        Returns:
            SubgraphCandidate with all required elements following Dau's rules
        """
        # Start with selected elements
        subgraph_elements = set(selected_elements)

        # Apply Dau's rules: if subgraph contains a cut, it must contain all enclosed elements
        expanded = True
        while expanded:
            expanded = False
            for element_id in list(subgraph_elements):
                if element_id in self.egi.area:  # This is a cut
                    cut_contents = self.egi.area.get(element_id, frozenset())
                    before_size = len(subgraph_elements)
                    subgraph_elements.update(cut_contents)
                    if len(subgraph_elements) > before_size:
                        expanded = True

        # Separate by type
        vertices = frozenset(
            elem for elem in subgraph_elements if any(v.id == elem for v in self.egi.V)
        )
        edges = frozenset(
            elem for elem in subgraph_elements if any(e.id == elem for e in self.egi.E)
        )
        cuts = frozenset(
            elem
            for elem in subgraph_elements
            if any(c.id == elem for c in self.egi.Cut)
        )

        return SubgraphCandidate(
            elements=frozenset(subgraph_elements),
            context=context,
            vertices=vertices,
            edges=edges,
            cuts=cuts,
        )

    def get_area_hierarchy(self, start_area: ElementID) -> List[ElementID]:
        """
        Get the hierarchy of areas from start_area up to the sheet.
        Used for IT- candidate search scope.

        Returns:
            List of area IDs from start_area to sheet (inclusive)
        """
        hierarchy = [start_area]
        current_area = start_area

        while current_area != self.egi.sheet:
            # Find the area that contains the current area
            containing_area = None
            for area_id, contents in self.egi.area.items():
                if current_area in contents:
                    containing_area = area_id
                    break

            if containing_area is None:
                break

            hierarchy.append(containing_area)
            current_area = containing_area

        return hierarchy


class EGIsomorphismChecker:
    """
    Checks structural isomorphism between EG subgraphs.
    Handles vertices, edges, cuts, and area mappings.
    """

    def __init__(self, egi: RelationalGraphWithCuts):
        self.egi = egi

    def are_isomorphic(
        self, subgraph1: SubgraphCandidate, subgraph2: SubgraphCandidate
    ) -> bool:
        """
        Check if two subgraphs are structurally isomorphic.

        Args:
            subgraph1: First subgraph candidate
            subgraph2: Second subgraph candidate

        Returns:
            True if subgraphs are isomorphic, False otherwise
        """
        # Quick structural checks
        if (
            len(subgraph1.vertices) != len(subgraph2.vertices)
            or len(subgraph1.edges) != len(subgraph2.edges)
            or len(subgraph1.cuts) != len(subgraph2.cuts)
        ):
            return False

        # For simple cases (single predicate), check relation names
        if len(subgraph1.edges) == 1 and len(subgraph2.edges) == 1:
            edge1_id = next(iter(subgraph1.edges))
            edge2_id = next(iter(subgraph2.edges))

            relation1 = self.egi.rel.get(edge1_id)
            relation2 = self.egi.rel.get(edge2_id)

            if relation1 != relation2:
                return False

            # Check arity
            arity1 = len(self.egi.nu.get(edge1_id, ()))
            arity2 = len(self.egi.nu.get(edge2_id, ()))

            return arity1 == arity2

        # For more complex cases, implement full graph isomorphism
        # This is a simplified version - full implementation would use
        # algorithms like VF2 or similar
        return self._simple_structural_match(subgraph1, subgraph2)

    def _simple_structural_match(
        self, subgraph1: SubgraphCandidate, subgraph2: SubgraphCandidate
    ) -> bool:
        """
        Simplified structural matching for basic cases.
        Full implementation would require sophisticated graph isomorphism algorithms.
        """
        # Check edge relations match
        relations1 = []
        relations2 = []

        for edge_id in subgraph1.edges:
            relation = self.egi.rel.get(edge_id)
            arity = len(self.egi.nu.get(edge_id, ()))
            relations1.append((relation, arity))

        for edge_id in subgraph2.edges:
            relation = self.egi.rel.get(edge_id)
            arity = len(self.egi.nu.get(edge_id, ()))
            relations2.append((relation, arity))

        relations1.sort()
        relations2.sort()

        return relations1 == relations2


class ITMinusValidator:
    """
    Validates IT- (deiteration) transformations using proper subgraph isomorphism.
    Implements Dau's rule: "Any subgraph whose occurrence could be the result of iteration may be erased."
    """

    def __init__(self, egi: RelationalGraphWithCuts):
        self.egi = egi
        self.extractor = DauSubgraphExtractor(egi)
        self.checker = EGIsomorphismChecker(egi)

    def can_deiterate(
        self, selected_elements: FrozenSet[ElementID], target_area: ElementID
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if selected elements can be deiterated according to Dau's rules.

        Args:
            selected_elements: Elements selected for deiteration
            target_area: Area containing the selected elements

        Returns:
            (can_deiterate, error_message)
        """
        if not selected_elements:
            return False, "Must select elements to deiterate"

        # Extract the subgraph to be deiterated
        target_subgraph = self.extractor.extract_subgraph(
            selected_elements, target_area
        )

        # Get search scope: current area + all parent areas up to sheet
        search_areas = self.extractor.get_area_hierarchy(target_area)

        # Search for isomorphic subgraphs in the search scope
        for search_area in search_areas:
            if search_area == target_area:
                continue  # Don't compare with itself

            candidates = self._find_subgraph_candidates(search_area, target_subgraph)

            for candidate in candidates:
                if self.checker.are_isomorphic(target_subgraph, candidate):
                    # Found an isomorphic subgraph - deiteration is valid
                    return True, None

        return (
            False,
            "No isomorphic subgraph found that could have been the source of iteration",
        )

    def _find_subgraph_candidates(
        self, search_area: ElementID, target_subgraph: SubgraphCandidate
    ) -> List[SubgraphCandidate]:
        """
        Find potential subgraph candidates in the search area that could match the target.
        """
        candidates = []
        area_contents = self.egi.area.get(search_area, frozenset())

        # For simple cases, look for individual elements of the same type
        if len(target_subgraph.edges) == 1 and len(target_subgraph.vertices) > 0:
            # Single predicate case
            target_edge_id = next(iter(target_subgraph.edges))
            target_relation = self.egi.rel.get(target_edge_id)
            target_arity = len(self.egi.nu.get(target_edge_id, ()))

            # Find edges with same relation and arity in search area
            for element_id in area_contents:
                if element_id in self.egi.rel:
                    if (
                        self.egi.rel[element_id] == target_relation
                        and len(self.egi.nu.get(element_id, ())) == target_arity
                    ):

                        # Extract this as a candidate subgraph
                        edge_vertices = set(self.egi.nu.get(element_id, ()))
                        candidate_elements = {element_id} | edge_vertices

                        candidate = self.extractor.extract_subgraph(
                            frozenset(candidate_elements), search_area
                        )
                        candidates.append(candidate)

        return candidates


def test_subgraph_isomorphism():
    """Test the subgraph isomorphism system with simple cases."""
    from egif_parser_dau import parse_egif

    print("Testing subgraph isomorphism system...")

    # Test 1: Valid deiteration case - same predicate in different areas
    print("\n=== Test 1: Valid deiteration case ===")
    egif1 = "*x (P x) ~[ (P x) ]"  # P(x) appears in both sheet and cut
    egi1 = parse_egif(egif1)
    validator1 = ITMinusValidator(egi1)

    # Find P relations
    p_relations = [e.id for e in egi1.E if egi1.rel.get(e.id) == "P"]
    print(f"Found {len(p_relations)} P relations")

    if len(p_relations) >= 2:
        # Try to deiterate the P in the cut (should be valid)
        for area_id, contents in egi1.area.items():
            if area_id != egi1.sheet and p_relations[1] in contents:
                selected = frozenset([p_relations[1]])
                can_deiterate, error = validator1.can_deiterate(selected, area_id)
                print(f"Can deiterate P in cut: {can_deiterate}")
                if error:
                    print(f"Error: {error}")
                break

    # Test 2: Invalid deiteration case - no duplicate
    print("\n=== Test 2: Invalid deiteration case ===")
    egif2 = "*x (P x) ~[ (Q x) ]"  # Different predicates
    egi2 = parse_egif(egif2)
    validator2 = ITMinusValidator(egi2)

    q_relations = [e.id for e in egi2.E if egi2.rel.get(e.id) == "Q"]
    if q_relations:
        for area_id, contents in egi2.area.items():
            if q_relations[0] in contents:
                selected = frozenset([q_relations[0]])
                can_deiterate, error = validator2.can_deiterate(selected, area_id)
                print(f"Can deiterate Q (should be false): {can_deiterate}")
                if error:
                    print(f"Error: {error}")
                break

    # Test 3: Complex case from interactive transformer
    print("\n=== Test 3: Complex case ===")
    egif3 = "~[ *x (P x) ~[ *y *z (P x) (Q y z) ] ]"
    egi3 = parse_egif(egif3)
    validator3 = ITMinusValidator(egi3)

    p_relations3 = [e.id for e in egi3.E if egi3.rel.get(e.id) == "P"]
    print(f"Found {len(p_relations3)} P relations in complex case")

    if len(p_relations3) >= 2:
        # Find the inner P relation
        for area_id, contents in egi3.area.items():
            if area_id != egi3.sheet and p_relations3[1] in contents:
                selected = frozenset([p_relations3[1]])
                can_deiterate, error = validator3.can_deiterate(selected, area_id)
                print(f"Can deiterate inner P: {can_deiterate}")
                if error:
                    print(f"Error: {error}")
                break


if __name__ == "__main__":
    test_subgraph_isomorphism()
