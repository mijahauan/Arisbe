"""
Graph Isomorphism Engine for Existential Graphs

This module provides comprehensive graph isomorphism testing for EGI structures,
serving as the foundation for:
1. IT- (deiteration) transformation validation
2. Endoporeutic Game proof verification
3. General structural equivalence checking

The implementation follows Dau's formal requirements for structural identity
in Beta Existential Graphs.
"""

from dataclasses import dataclass
from itertools import permutations
from typing import Dict, FrozenSet, Iterator, List, Optional, Set, Tuple

from egi_core_dau import Cut, Edge, ElementID, RelationalGraphWithCuts, Vertex


@dataclass(frozen=True)
class IsomorphismMapping:
    """Complete mapping between two isomorphic subgraphs."""

    vertex_mapping: Dict[ElementID, ElementID]
    edge_mapping: Dict[ElementID, ElementID]
    cut_mapping: Dict[ElementID, ElementID]

    @property
    def complete_mapping(self) -> Dict[ElementID, ElementID]:
        """Get complete element mapping."""
        mapping = {}
        mapping.update(self.vertex_mapping)
        mapping.update(self.edge_mapping)
        mapping.update(self.cut_mapping)
        return mapping


@dataclass(frozen=True)
class IsomorphismResult:
    """Result of isomorphism testing."""

    is_isomorphic: bool
    mapping: Optional[IsomorphismMapping]
    reason: Optional[str]  # Explanation if not isomorphic


class GraphIsomorphismEngine:
    """
    Engine for testing structural isomorphism between EGI subgraphs.

    Implements Dau's requirements for structural identity:
    - Vertex identity: same label and generic status
    - Edge identity: same relation name (κ) and vertex sequence structure (ν)
    - Cut identity: same internal structure recursively
    - Preservation of all structural relationships
    """

    def test_subgraph_isomorphism(
        self,
        egi: RelationalGraphWithCuts,
        subgraph1: FrozenSet[ElementID],
        subgraph2: FrozenSet[ElementID],
    ) -> IsomorphismResult:
        """
        Test if two subgraphs within the same EGI are structurally isomorphic.

        Args:
            egi: The EGI containing both subgraphs
            subgraph1: First subgraph element IDs
            subgraph2: Second subgraph element IDs

        Returns:
            IsomorphismResult indicating if isomorphic and the mapping if so
        """
        # Basic size check
        if len(subgraph1) != len(subgraph2):
            return IsomorphismResult(False, None, "Different number of elements")

        # Empty subgraphs are trivially isomorphic
        if len(subgraph1) == 0:
            return IsomorphismResult(True, IsomorphismMapping({}, {}, {}), None)

        # Categorize elements by type
        sg1_vertices, sg1_edges, sg1_cuts = self._categorize_elements(egi, subgraph1)
        sg2_vertices, sg2_edges, sg2_cuts = self._categorize_elements(egi, subgraph2)

        # Must have same number of each element type
        if (
            len(sg1_vertices) != len(sg2_vertices)
            or len(sg1_edges) != len(sg2_edges)
            or len(sg1_cuts) != len(sg2_cuts)
        ):
            return IsomorphismResult(
                False, None, "Different element type distributions"
            )

        # Try all possible mappings
        for mapping in self._generate_possible_mappings(
            sg1_vertices, sg1_edges, sg1_cuts, sg2_vertices, sg2_edges, sg2_cuts
        ):

            if self._validate_structural_mapping(egi, mapping):
                return IsomorphismResult(True, mapping, None)

        return IsomorphismResult(False, None, "No valid structural mapping found")

    def test_cross_egi_isomorphism(
        self,
        egi1: RelationalGraphWithCuts,
        subgraph1: FrozenSet[ElementID],
        egi2: RelationalGraphWithCuts,
        subgraph2: FrozenSet[ElementID],
    ) -> IsomorphismResult:
        """
        Test isomorphism between subgraphs in different EGIs.
        Used for Endoporeutic Game proof validation.
        """
        # Basic size check
        if len(subgraph1) != len(subgraph2):
            return IsomorphismResult(False, None, "Different number of elements")

        # Empty subgraphs are trivially isomorphic
        if len(subgraph1) == 0:
            return IsomorphismResult(True, IsomorphismMapping({}, {}, {}), None)

        # Categorize elements in both EGIs
        sg1_vertices, sg1_edges, sg1_cuts = self._categorize_elements(egi1, subgraph1)
        sg2_vertices, sg2_edges, sg2_cuts = self._categorize_elements(egi2, subgraph2)

        # Must have same number of each element type
        if (
            len(sg1_vertices) != len(sg2_vertices)
            or len(sg1_edges) != len(sg2_edges)
            or len(sg1_cuts) != len(sg2_cuts)
        ):
            return IsomorphismResult(
                False, None, "Different element type distributions"
            )

        # Try all possible mappings
        for mapping in self._generate_possible_mappings(
            sg1_vertices, sg1_edges, sg1_cuts, sg2_vertices, sg2_edges, sg2_cuts
        ):

            if self._validate_cross_egi_mapping(egi1, egi2, mapping):
                return IsomorphismResult(True, mapping, None)

        return IsomorphismResult(False, None, "No valid structural mapping found")

    def find_isomorphic_subgraphs(
        self,
        egi: RelationalGraphWithCuts,
        target_subgraph: FrozenSet[ElementID],
        search_areas: List[ElementID],
    ) -> List[Tuple[ElementID, FrozenSet[ElementID], IsomorphismMapping]]:
        """
        Find all subgraphs isomorphic to target_subgraph within specified areas.
        Used for IT- deiteration validation.

        Returns:
            List of (area_id, matching_subgraph, mapping) tuples
        """
        matches = []

        for area_id in search_areas:
            area_contents = egi.area.get(area_id, frozenset())

            # Find all possible subgraphs of the same size
            for candidate_subgraph in self._generate_subgraphs_of_size(
                area_contents, len(target_subgraph)
            ):

                result = self.test_subgraph_isomorphism(
                    egi, target_subgraph, candidate_subgraph
                )
                if result.is_isomorphic:
                    matches.append((area_id, candidate_subgraph, result.mapping))

        return matches

    def _categorize_elements(
        self, egi: RelationalGraphWithCuts, elements: FrozenSet[ElementID]
    ) -> Tuple[List[ElementID], List[ElementID], List[ElementID]]:
        """Categorize elements into vertices, edges, and cuts."""
        vertices = []
        edges = []
        cuts = []

        vertex_ids = {v.id for v in egi.V}
        edge_ids = {e.id for e in egi.E}
        cut_ids = {c.id for c in egi.Cut}

        for element_id in elements:
            if element_id in vertex_ids:
                vertices.append(element_id)
            elif element_id in edge_ids:
                edges.append(element_id)
            elif element_id in cut_ids:
                cuts.append(element_id)
            else:
                raise ValueError(f"Unknown element ID: {element_id}")

        return vertices, edges, cuts

    def _generate_possible_mappings(
        self,
        sg1_vertices: List[ElementID],
        sg1_edges: List[ElementID],
        sg1_cuts: List[ElementID],
        sg2_vertices: List[ElementID],
        sg2_edges: List[ElementID],
        sg2_cuts: List[ElementID],
    ) -> Iterator[IsomorphismMapping]:
        """Generate all possible mappings between categorized elements."""

        # Generate all permutations for each element type
        for vertex_perm in permutations(sg2_vertices):
            vertex_mapping = dict(zip(sg1_vertices, vertex_perm))

            for edge_perm in permutations(sg2_edges):
                edge_mapping = dict(zip(sg1_edges, edge_perm))

                for cut_perm in permutations(sg2_cuts):
                    cut_mapping = dict(zip(sg1_cuts, cut_perm))

                    yield IsomorphismMapping(vertex_mapping, edge_mapping, cut_mapping)

    def _validate_structural_mapping(
        self, egi: RelationalGraphWithCuts, mapping: IsomorphismMapping
    ) -> bool:
        """Validate that mapping preserves all structural relationships within single EGI."""

        # Validate vertex structural identity
        for orig_v_id, mapped_v_id in mapping.vertex_mapping.items():
            if not self._vertices_structurally_identical(
                egi, orig_v_id, egi, mapped_v_id
            ):
                return False

        # Validate edge structural identity
        for orig_e_id, mapped_e_id in mapping.edge_mapping.items():
            if not self._edges_structurally_identical(
                egi, orig_e_id, egi, mapped_e_id, mapping
            ):
                return False

        # Validate cut structural identity
        for orig_c_id, mapped_c_id in mapping.cut_mapping.items():
            if not self._cuts_structurally_identical(
                egi, orig_c_id, egi, mapped_c_id, mapping
            ):
                return False

        return True

    def _validate_cross_egi_mapping(
        self,
        egi1: RelationalGraphWithCuts,
        egi2: RelationalGraphWithCuts,
        mapping: IsomorphismMapping,
    ) -> bool:
        """Validate mapping between elements in different EGIs."""

        # Validate vertex structural identity across EGIs
        for orig_v_id, mapped_v_id in mapping.vertex_mapping.items():
            if not self._vertices_structurally_identical(
                egi1, orig_v_id, egi2, mapped_v_id
            ):
                return False

        # Validate edge structural identity across EGIs
        for orig_e_id, mapped_e_id in mapping.edge_mapping.items():
            if not self._edges_structurally_identical(
                egi1, orig_e_id, egi2, mapped_e_id, mapping
            ):
                return False

        # Validate cut structural identity across EGIs
        for orig_c_id, mapped_c_id in mapping.cut_mapping.items():
            if not self._cuts_structurally_identical(
                egi1, orig_c_id, egi2, mapped_c_id, mapping
            ):
                return False

        return True

    def _vertices_structurally_identical(
        self,
        egi1: RelationalGraphWithCuts,
        v1_id: ElementID,
        egi2: RelationalGraphWithCuts,
        v2_id: ElementID,
    ) -> bool:
        """Check if two vertices are structurally identical per Dau's requirements."""

        v1 = self._get_vertex_by_id(egi1, v1_id)
        v2 = self._get_vertex_by_id(egi2, v2_id)

        # Must have identical label and generic status
        return v1.label == v2.label and v1.is_generic == v2.is_generic

    def _edges_structurally_identical(
        self,
        egi1: RelationalGraphWithCuts,
        e1_id: ElementID,
        egi2: RelationalGraphWithCuts,
        e2_id: ElementID,
        mapping: IsomorphismMapping,
    ) -> bool:
        """Check if two edges are structurally identical per Dau's requirements."""

        # Must have same relation name (κ mapping)
        rel1 = egi1.rel.get(e1_id, "")
        rel2 = egi2.rel.get(e2_id, "")
        if rel1 != rel2:
            return False

        # Must have structurally equivalent vertex sequences (ν mapping)
        seq1 = egi1.nu.get(e1_id, ())
        seq2 = egi2.nu.get(e2_id, ())

        if len(seq1) != len(seq2):
            return False

        # Check that vertex sequences map correctly
        complete_mapping = mapping.complete_mapping
        for v1_id, v2_id in zip(seq1, seq2):
            expected_v2_id = complete_mapping.get(v1_id)
            if expected_v2_id != v2_id:
                return False

        return True

    def _cuts_structurally_identical(
        self,
        egi1: RelationalGraphWithCuts,
        c1_id: ElementID,
        egi2: RelationalGraphWithCuts,
        c2_id: ElementID,
        mapping: IsomorphismMapping,
    ) -> bool:
        """Check if two cuts are structurally identical per Dau's requirements."""

        # Get cut contents
        contents1 = egi1.area.get(c1_id, frozenset())
        contents2 = egi2.area.get(c2_id, frozenset())

        if len(contents1) != len(contents2):
            return False

        # Check that all contents map correctly
        complete_mapping = mapping.complete_mapping
        for element1_id in contents1:
            expected_element2_id = complete_mapping.get(element1_id)
            if expected_element2_id not in contents2:
                return False

        return True

    def _get_vertex_by_id(
        self, egi: RelationalGraphWithCuts, vertex_id: ElementID
    ) -> Vertex:
        """Get vertex by ID from EGI."""
        for v in egi.V:
            if v.id == vertex_id:
                return v
        raise ValueError(f"Vertex {vertex_id} not found")

    def _generate_subgraphs_of_size(
        self, elements: FrozenSet[ElementID], size: int
    ) -> Iterator[FrozenSet[ElementID]]:
        """Generate all possible subgraphs of specified size from element set."""
        from itertools import combinations

        for combo in combinations(elements, size):
            yield frozenset(combo)


class IsomorphismValidator:
    """
    High-level validator for common isomorphism testing scenarios.
    Provides convenient interfaces for IT- and Endoporeutic Game use cases.
    """

    def __init__(self):
        self.engine = GraphIsomorphismEngine()

    def validate_deiteration_candidate(
        self,
        egi: RelationalGraphWithCuts,
        target_subgraph: FrozenSet[ElementID],
        target_area: ElementID,
        nesting_hierarchy: List[ElementID],
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate IT- deiteration by finding isomorphic subgraph in nesting hierarchy.

        Returns:
            (is_valid, error_message)
        """
        # Search areas in nesting hierarchy (excluding target area itself)
        search_areas = [area for area in nesting_hierarchy if area != target_area]

        matches = self.engine.find_isomorphic_subgraphs(
            egi, target_subgraph, search_areas
        )

        if matches:
            return True, None
        else:
            return False, "No structurally identical subgraph found in nest of cuts"

    def validate_endoporeutic_claim(
        self,
        domain_egi: RelationalGraphWithCuts,
        claim_egi: RelationalGraphWithCuts,
        domain_subgraph: FrozenSet[ElementID],
        claim_subgraph: FrozenSet[ElementID],
    ) -> Tuple[bool, Optional[IsomorphismMapping]]:
        """
        Validate Endoporeutic Game claim by testing cross-EGI isomorphism.

        Returns:
            (is_valid, mapping_if_valid)
        """
        result = self.engine.test_cross_egi_isomorphism(
            domain_egi, domain_subgraph, claim_egi, claim_subgraph
        )

        if result.is_isomorphic:
            return True, result.mapping
        else:
            return False, None
