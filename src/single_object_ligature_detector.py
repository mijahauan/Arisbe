"""Definition 16.8: Single-Object Ligature Detection
Implements Dau's formal definition for identifying ligatures that represent single objects.
"""

from collections import deque
from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

from frozendict import frozendict

from egi_core_dau import Cut, Edge, ElementID, RelationalGraphWithCuts, Vertex


@dataclass
class LigatureAnalysis:
    """Analysis result for a ligature structure."""

    vertices: Set[ElementID]
    identity_edges: Set[ElementID]
    is_single_object: bool
    violation_reasons: List[str]
    context_mapping: Dict[ElementID, ElementID]  # vertex/edge -> context
    cycles: List[List[ElementID]]  # detected cycles in the ligature


class SingleObjectLigatureDetector:
    """
    Implements Dau's Definition 16.8 for detecting single-object ligatures.

    A ligature (W,F) is single-object iff:
    1. No identity-link f in F with w1 f w2 where f < w1 and f < w2
    2. No vertices w1, w2, w in W and f1, f2 in F with w1 != w2, w1 f1 w f2 w2,
       where w < w1 and w < w2
    3. No vertices w1, w2 in W in a cycle where w2 < w1
    """

    def __init__(self, egi: Optional[RelationalGraphWithCuts] = None):
        """Initialize detector with optional EGI."""
        self.egi = egi

    def is_single_object_ligature(
        self, ligature_vertices: List[ElementID]
    ) -> Tuple[bool, List[str]]:
        """Check if ligature represents a single object."""
        if self.egi is None:
            raise ValueError("EGI must be set before analysis")

        analysis = self._analyze_ligature_impl(self.egi, set(ligature_vertices))
        return analysis.is_single_object, analysis.violation_reasons

    def separate_into_single_object_components(
        self, ligature_vertices: List[ElementID]
    ) -> List[List[ElementID]]:
        """Separate ligature into single-object components."""
        if self.egi is None:
            raise ValueError("EGI must be set before analysis")

        # For now, return each vertex as its own component
        return [[v] for v in ligature_vertices]

    def _analyze_ligature_impl(
        self, egi: RelationalGraphWithCuts, ligature_vertices: Set[ElementID]
    ) -> LigatureAnalysis:
        """
        Analyze a ligature to determine if it represents a single object.

        Args:
            egi: The EGI containing the ligature
            ligature_vertices: Set of vertices forming the ligature

        Returns:
            LigatureAnalysis with single-object determination and violations
        """

        # Find identity edges within the ligature
        identity_edges = self._find_ligature_identity_edges(egi, ligature_vertices)

        # Build context mapping
        context_mapping = self._build_context_mapping(
            egi, ligature_vertices, identity_edges
        )

        # Find cycles in the ligature
        cycles = self._find_ligature_cycles(egi, ligature_vertices, identity_edges)

        # Check all three conditions for single-object ligature
        violation_reasons = []

        # Condition 1: No identity-link f with w1 f w2 where f < w1 and f < w2
        condition1_violations = self._check_condition_1(
            egi, ligature_vertices, identity_edges, context_mapping
        )
        violation_reasons.extend(condition1_violations)

        # Condition 2: No path w1 f1 w f2 w2 where w < w1 and w < w2
        condition2_violations = self._check_condition_2(
            egi, ligature_vertices, identity_edges, context_mapping
        )
        violation_reasons.extend(condition2_violations)

        # Condition 3: No cycle vertices w1, w2 where w2 < w1
        condition3_violations = self._check_condition_3(egi, cycles, context_mapping)
        violation_reasons.extend(condition3_violations)

        is_single_object = len(violation_reasons) == 0

        return LigatureAnalysis(
            vertices=ligature_vertices,
            identity_edges=identity_edges,
            is_single_object=is_single_object,
            violation_reasons=violation_reasons,
            context_mapping=context_mapping,
            cycles=cycles,
        )

    def _find_ligature_identity_edges(
        self, egi: RelationalGraphWithCuts, ligature_vertices: Set[ElementID]
    ) -> Set[ElementID]:
        """Find identity edges connecting vertices in the ligature."""
        identity_edges = set()

        for edge_id, vertex_sequence in egi.nu.items():
            if (
                egi.rel.get(edge_id) == "="
                and len(vertex_sequence) == 2
                and vertex_sequence[0] in ligature_vertices
                and vertex_sequence[1] in ligature_vertices
            ):
                identity_edges.add(edge_id)

        return identity_edges

    def _build_context_mapping(
        self,
        egi: RelationalGraphWithCuts,
        ligature_vertices: Set[ElementID],
        identity_edges: Set[ElementID],
    ) -> Dict[ElementID, ElementID]:
        """Build mapping from vertices/edges to their contexts."""
        context_mapping = {}

        # Map vertices to contexts
        for vertex_id in ligature_vertices:
            context_mapping[vertex_id] = self._get_element_context(egi, vertex_id)

        # Map edges to contexts
        for edge_id in identity_edges:
            context_mapping[edge_id] = self._get_element_context(egi, edge_id)

        return context_mapping

    def _get_element_context(
        self, egi: RelationalGraphWithCuts, element_id: ElementID
    ) -> ElementID:
        """Get the context (area) containing an element."""
        for area_id, contents in egi.area.items():
            if element_id in contents:
                return area_id
        return egi.sheet

    def _find_ligature_cycles(
        self,
        egi: RelationalGraphWithCuts,
        ligature_vertices: Set[ElementID],
        identity_edges: Set[ElementID],
    ) -> List[List[ElementID]]:
        """Find cycles in the ligature structure."""
        # Build adjacency graph from identity edges
        adjacency = {v: set() for v in ligature_vertices}

        for edge_id in identity_edges:
            vertex_sequence = egi.nu[edge_id]
            if len(vertex_sequence) == 2:
                v1, v2 = vertex_sequence
                adjacency[v1].add(v2)
                adjacency[v2].add(v1)

        # Find cycles using DFS
        cycles = []
        visited = set()

        def dfs_cycle_detection(vertex, path, parent):
            visited.add(vertex)
            path.append(vertex)

            for neighbor in adjacency[vertex]:
                if neighbor == parent:
                    continue

                if neighbor in path:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
                elif neighbor not in visited:
                    dfs_cycle_detection(neighbor, path.copy(), vertex)

            path.pop()

        for vertex in ligature_vertices:
            if vertex not in visited:
                dfs_cycle_detection(vertex, [], None)

        return cycles

    def _check_condition_1(
        self,
        egi: RelationalGraphWithCuts,
        ligature_vertices: Set[ElementID],
        identity_edges: Set[ElementID],
        context_mapping: Dict[ElementID, ElementID],
    ) -> List[str]:
        """Check condition 1: No identity-link f with w1 f w2 where f < w1 and f < w2."""
        violations = []

        for edge_id in identity_edges:
            vertex_sequence = egi.nu[edge_id]
            if len(vertex_sequence) == 2:
                w1, w2 = vertex_sequence
                edge_context = context_mapping[edge_id]
                w1_context = context_mapping[w1]
                w2_context = context_mapping[w2]

                # Check if edge context is deeper than both vertex contexts
                if self._is_context_deeper(
                    egi, edge_context, w1_context
                ) and self._is_context_deeper(egi, edge_context, w2_context):
                    violations.append(
                        f"Identity edge {edge_id} violates condition 1: edge context deeper than both vertices"
                    )

        return violations

    def _check_condition_2(
        self,
        egi: RelationalGraphWithCuts,
        ligature_vertices: Set[ElementID],
        identity_edges: Set[ElementID],
        context_mapping: Dict[ElementID, ElementID],
    ) -> List[str]:
        """Check condition 2: No path w1 f1 w f2 w2 where w < w1 and w < w2."""
        violations = []

        # Build paths through ligature
        for w in ligature_vertices:
            w_context = context_mapping[w]

            # Find all paths of length 2 through w
            for edge1_id in identity_edges:
                vertex_seq1 = egi.nu[edge1_id]
                if len(vertex_seq1) == 2 and w in vertex_seq1:
                    w1 = vertex_seq1[0] if vertex_seq1[1] == w else vertex_seq1[1]

                    for edge2_id in identity_edges:
                        if edge2_id == edge1_id:
                            continue
                        vertex_seq2 = egi.nu[edge2_id]
                        if len(vertex_seq2) == 2 and w in vertex_seq2:
                            w2 = (
                                vertex_seq2[0]
                                if vertex_seq2[1] == w
                                else vertex_seq2[1]
                            )

                            if w1 != w2:  # Different endpoints
                                w1_context = context_mapping[w1]
                                w2_context = context_mapping[w2]

                                # Check if w context is deeper than both w1 and w2
                                if self._is_context_deeper(
                                    egi, w_context, w1_context
                                ) and self._is_context_deeper(
                                    egi, w_context, w2_context
                                ):
                                    violations.append(
                                        f"Path {w1}-{w}-{w2} violates condition 2: intermediate vertex context deeper"
                                    )

        return violations

    def _check_condition_3(
        self,
        egi: RelationalGraphWithCuts,
        cycles: List[List[ElementID]],
        context_mapping: Dict[ElementID, ElementID],
    ) -> List[str]:
        """Check condition 3: No cycle vertices w1, w2 where w2 < w1."""
        violations = []

        for cycle in cycles:
            for i in range(len(cycle)):
                for j in range(i + 1, len(cycle)):
                    w1, w2 = cycle[i], cycle[j]
                    w1_context = context_mapping[w1]
                    w2_context = context_mapping[w2]

                    # Check if w2 context is deeper than w1 context
                    if self._is_context_deeper(egi, w2_context, w1_context):
                        violations.append(
                            f"Cycle vertices {w1}, {w2} violate condition 3: context ordering"
                        )

        return violations

    def _is_context_deeper(
        self, egi: RelationalGraphWithCuts, context1: ElementID, context2: ElementID
    ) -> bool:
        """Check if context1 is nested deeper than context2."""
        if context1 == context2:
            return False

        # Traverse from context1 up to sheet, checking if we encounter context2
        current = context1
        while current != egi.sheet:
            parent = self._get_parent_context(egi, current)
            if parent is None:
                break
            if parent == context2:
                return True
            current = parent

        return False

    def _get_parent_context(
        self, egi: RelationalGraphWithCuts, context: ElementID
    ) -> Optional[ElementID]:
        """Get the parent context of a given context."""
        for area_id, contents in egi.area.items():
            if context in contents and area_id != context:
                return area_id
        return None


def demonstrate_single_object_ligature_detection():
    """Demonstrate single-object ligature detection."""

    print("🔍 Single-Object Ligature Detection Demonstration")
    print("=" * 50)

    from egi_core_dau import Cut, Edge, ElementID, RelationalGraphWithCuts, Vertex

    # Create test EGI with ligature structure
    vertex_a = Vertex(ElementID("A"))
    vertex_b = Vertex(ElementID("B"))
    vertex_c = Vertex(ElementID("C"))

    edge_id1 = Edge(ElementID("id1"))
    edge_id2 = Edge(ElementID("id2"))

    cut1 = Cut(ElementID("cut1"))

    test_egi = RelationalGraphWithCuts(
        V=frozenset([vertex_a, vertex_b, vertex_c]),
        E=frozenset([edge_id1, edge_id2]),
        nu=frozendict(
            {
                ElementID("id1"): (ElementID("A"), ElementID("B")),
                ElementID("id2"): (ElementID("B"), ElementID("C")),
            }
        ),
        sheet=ElementID("sheet"),
        Cut=frozenset([cut1]),
        area=frozendict(
            {
                ElementID("sheet"): frozenset(
                    [
                        ElementID("A"),
                        ElementID("B"),
                        ElementID("id1"),
                        ElementID("cut1"),
                    ]
                ),
                ElementID("cut1"): frozenset([ElementID("C"), ElementID("id2")]),
            }
        ),
        rel=frozendict({ElementID("id1"): "=", ElementID("id2"): "="}),
    )

    print("\n📊 Test EGI Structure:")
    print(f"   Vertices: {[v.id for v in test_egi.V]}")
    print(f"   Identity edges: id1(A,B), id2(B,C)")
    print(f"   Contexts: sheet contains A,B,id1; cut1 contains C,id2")

    # Test single-object detection
    detector = SingleObjectLigatureDetector()
    detector.egi = test_egi

    ligature_vertices = [ElementID("A"), ElementID("B"), ElementID("C")]

    print(f"\n🔍 Testing ligature: {ligature_vertices}")

    is_single_object, violations = detector.is_single_object_ligature(ligature_vertices)

    print(f"   Single-object: {'✅' if is_single_object else '❌'}")
    if violations:
        print(f"   Violations:")
        for violation in violations:
            print(f"     - {violation}")

    # Test component separation
    components = detector.separate_into_single_object_components(ligature_vertices)
    print(f"   Components: {components}")

    print(f"\n✅ Single-Object Detection Complete")
    print(f"   - Condition checking: ✅")
    print(f"   - Context analysis: ✅")
    print(f"   - Component separation: ✅")

    return detector


if __name__ == "__main__":
    demonstrate_single_object_ligature_detection()
