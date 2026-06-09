"""
Graph Isomorphism Engine for Existential Graphs

This module provides comprehensive graph isomorphism testing for EGI structures,
serving as the foundation for:
1. IT- (deiteration) transformation validation
2. Endoporeutic Game proof verification
3. General structural equivalence checking

Implementation uses NetworkX VF2 (Vento-Foggia) algorithm, which is polynomial
in the number of nodes in practice — replacing the previous O(n!) enumeration.

EGI subgraphs are encoded as NetworkX MultiDiGraphs:
  - Vertices     → nodes with ntype='v', label, is_generic
  - Edges (n-ary)→ nodes with ntype='e', rel, arity
  - Cuts         → nodes with ntype='c'
  - ν(e, pos)=v  → MultiDiGraph edge e→v with etype='nu', pos=pos
  - area(c) ∋ x  → MultiDiGraph edge c→x with etype='contains'
"""

from dataclasses import dataclass
from typing import Dict, FrozenSet, Iterator, List, Optional, Set, Tuple

import networkx as nx
from networkx.algorithms.isomorphism import MultiDiGraphMatcher

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

    Uses NetworkX VF2 (polynomial) instead of O(n!) permutation enumeration.

    Implements Dau's requirements for structural identity:
    - Vertex identity: same label and generic status
    - Edge identity: same relation name (κ) and ordered vertex sequence (ν)
    - Cut identity: same containment structure recursively
    """

    # ------------------------------------------------------------------
    # NetworkX graph encoding
    # ------------------------------------------------------------------

    def _build_nx_graph(
        self,
        egi: RelationalGraphWithCuts,
        subgraph_ids: FrozenSet[ElementID],
    ) -> nx.MultiDiGraph:
        """
        Encode an EGI subgraph as a NetworkX MultiDiGraph.

        Nodes carry structural attributes; edges carry relation type and
        position in ν sequences so VF2 can enforce ordering.
        """
        G = nx.MultiDiGraph()
        v_ids = {v.id for v in egi.V}
        e_ids = {e.id for e in egi.E}
        c_ids = {c.id for c in egi.Cut}

        for elem_id in subgraph_ids:
            if elem_id in v_ids:
                v = next(v for v in egi.V if v.id == elem_id)
                G.add_node(elem_id, ntype="v", label=v.label, is_generic=v.is_generic)
            elif elem_id in e_ids:
                G.add_node(
                    elem_id,
                    ntype="e",
                    rel=egi.rel.get(elem_id, ""),
                    arity=len(egi.nu.get(elem_id, ())),
                )
            elif elem_id in c_ids:
                G.add_node(elem_id, ntype="c", label=None, is_generic=False)
            else:
                raise ValueError(f"Unknown element ID: {elem_id}")

        # ν edges: edge_node → vertex_node with position
        for elem_id in subgraph_ids:
            if elem_id in e_ids:
                for pos, vid in enumerate(egi.nu.get(elem_id, ())):
                    if vid in subgraph_ids:
                        G.add_edge(elem_id, vid, etype="nu", pos=pos)

        # Containment edges: cut_node → contained_element
        for elem_id in subgraph_ids:
            if elem_id in c_ids:
                for contained_id in egi.area.get(elem_id, frozenset()):
                    if contained_id in subgraph_ids:
                        G.add_edge(elem_id, contained_id, etype="contains", pos=0)

        return G

    @staticmethod
    def _node_match(n1: dict, n2: dict) -> bool:
        """VF2 node compatibility: same element type and attributes."""
        if n1["ntype"] != n2["ntype"]:
            return False
        if n1["ntype"] == "v":
            return n1["label"] == n2["label"] and n1["is_generic"] == n2["is_generic"]
        if n1["ntype"] == "e":
            return n1["rel"] == n2["rel"] and n1["arity"] == n2["arity"]
        return True  # cuts: structural match only

    @staticmethod
    def _edge_match(e1_dict: dict, e2_dict: dict) -> bool:
        """
        VF2 edge compatibility for MultiDiGraph.
        e1_dict / e2_dict are {key: attrs} dicts for all parallel edges.
        Edges match if they have the same multiset of (etype, pos) pairs.
        """
        sig1 = tuple(sorted((d["etype"], d.get("pos", 0)) for d in e1_dict.values()))
        sig2 = tuple(sorted((d["etype"], d.get("pos", 0)) for d in e2_dict.values()))
        return sig1 == sig2

    def _mapping_from_nx(
        self,
        nx_mapping: Dict,  # G1_node_id -> G2_node_id
        egi1: RelationalGraphWithCuts,
        egi2: RelationalGraphWithCuts,
    ) -> IsomorphismMapping:
        """Convert a raw NetworkX node mapping to IsomorphismMapping."""
        v_ids1 = {v.id for v in egi1.V}
        e_ids1 = {e.id for e in egi1.E}
        c_ids1 = {c.id for c in egi1.Cut}

        vertex_mapping: Dict[ElementID, ElementID] = {}
        edge_mapping: Dict[ElementID, ElementID] = {}
        cut_mapping: Dict[ElementID, ElementID] = {}

        for orig, mapped in nx_mapping.items():
            if orig in v_ids1:
                vertex_mapping[orig] = mapped
            elif orig in e_ids1:
                edge_mapping[orig] = mapped
            elif orig in c_ids1:
                cut_mapping[orig] = mapped

        return IsomorphismMapping(vertex_mapping, edge_mapping, cut_mapping)

    # ------------------------------------------------------------------
    # Public API (unchanged)
    # ------------------------------------------------------------------

    def test_subgraph_isomorphism(
        self,
        egi: RelationalGraphWithCuts,
        subgraph1: FrozenSet[ElementID],
        subgraph2: FrozenSet[ElementID],
    ) -> IsomorphismResult:
        """
        Test if two subgraphs within the same EGI are structurally isomorphic.
        Uses NetworkX VF2 (polynomial) instead of O(n!) permutation.
        """
        if len(subgraph1) != len(subgraph2):
            return IsomorphismResult(False, None, "Different number of elements")
        if len(subgraph1) == 0:
            return IsomorphismResult(True, IsomorphismMapping({}, {}, {}), None)

        G1 = self._build_nx_graph(egi, subgraph1)
        G2 = self._build_nx_graph(egi, subgraph2)
        gm = MultiDiGraphMatcher(G1, G2, self._node_match, self._edge_match)

        if not gm.is_isomorphic():
            return IsomorphismResult(False, None, "No valid structural mapping found")

        nx_mapping = next(gm.isomorphisms_iter())
        return IsomorphismResult(
            True, self._mapping_from_nx(nx_mapping, egi, egi), None
        )

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
        if len(subgraph1) != len(subgraph2):
            return IsomorphismResult(False, None, "Different number of elements")
        if len(subgraph1) == 0:
            return IsomorphismResult(True, IsomorphismMapping({}, {}, {}), None)

        G1 = self._build_nx_graph(egi1, subgraph1)
        G2 = self._build_nx_graph(egi2, subgraph2)
        gm = MultiDiGraphMatcher(G1, G2, self._node_match, self._edge_match)

        if not gm.is_isomorphic():
            return IsomorphismResult(False, None, "No valid structural mapping found")

        nx_mapping = next(gm.isomorphisms_iter())
        return IsomorphismResult(
            True, self._mapping_from_nx(nx_mapping, egi1, egi2), None
        )

    def find_isomorphic_subgraphs(
        self,
        egi: RelationalGraphWithCuts,
        target_subgraph: FrozenSet[ElementID],
        search_areas: List[ElementID],
    ) -> List[Tuple[ElementID, FrozenSet[ElementID], IsomorphismMapping]]:
        """
        Find all subgraphs isomorphic to target_subgraph within specified areas.
        Used for IT- deiteration validation.

        Uses VF2 subgraph isomorphism: embeds target as a sub-pattern of each
        area graph rather than enumerating all same-size combinations.

        The search graph for an area is built from that area's *recursive*
        contents (every cut's interior, transitively), so a target that is a
        whole cut-subtree — a cut plus everything nested inside it — can be
        embedded.  Without this, only the area's direct members are present and
        a cut copy is unmatchable because its contents (in deeper areas) are
        missing.  Each raw VF2 hit is then filtered to a valid deiteration
        source by ``_match_is_rooted_subtree``: the image must be a union of
        *full* subtrees rooted at the search area's own level (no slicing
        through a cut, no copy buried inside a sibling cut — that would not be
        an enclosing occurrence).

        Returns:
            List of (area_id, matching_subgraph, mapping) tuples
        """
        if not target_subgraph:
            return []

        G_target = self._build_nx_graph(egi, target_subgraph)
        matches = []

        for area_id in search_areas:
            search_ids = self._recursive_area_contents(egi, area_id)
            if len(search_ids) < len(target_subgraph):
                continue

            G_area = self._build_nx_graph(egi, search_ids)
            gm = MultiDiGraphMatcher(G_area, G_target, self._node_match, self._edge_match)

            for nx_mapping in gm.subgraph_isomorphisms_iter():
                # nx_mapping: area_node -> target_node  (area is the "bigger" graph)
                # Reverse: target_node -> area_node
                reverse = {v: k for k, v in nx_mapping.items()}
                matched_ids = frozenset(reverse[t] for t in target_subgraph if t in reverse)
                if len(matched_ids) != len(target_subgraph):
                    continue
                if not self._match_is_rooted_subtree(egi, matched_ids, area_id):
                    continue
                iso_mapping = self._mapping_from_nx(reverse, egi, egi)
                matches.append((area_id, matched_ids, iso_mapping))

        return matches

    @staticmethod
    def _recursive_area_contents(
        egi: RelationalGraphWithCuts, area_id: ElementID
    ) -> FrozenSet[ElementID]:
        """All elements within ``area_id``, descending through nested cuts."""
        collected: Set[ElementID] = set()
        frontier = list(egi.area.get(area_id, frozenset()))
        while frontier:
            elem = frontier.pop()
            if elem in collected:
                continue
            collected.add(elem)
            # If this element is a cut, descend into its interior.
            frontier.extend(egi.area.get(elem, frozenset()))
        return frozenset(collected)

    @staticmethod
    def _match_is_rooted_subtree(
        egi: RelationalGraphWithCuts,
        matched_ids: FrozenSet[ElementID],
        area_id: ElementID,
    ) -> bool:
        """
        A deiteration source must be a union of *full* subtrees rooted at the
        search area's level.  Two conditions, together, enforce that:

        - *rooted-in-area*: every matched element sits directly in ``area_id``
          or inside a cut that is itself matched — so the match doesn't reach
          down into a sibling cut (a non-enclosing, deeper area).
        - *closed cuts*: every matched cut contributes all of its direct
          contents — so the match doesn't slice through a cut (which would make
          e.g. ``~[(P)]`` spuriously match a copy inside ``~[(P)(Q)]``).
        """
        c_ids = {c.id for c in egi.Cut}
        # Parent area of each element (the area whose contents include it).
        parent: Dict[ElementID, ElementID] = {}
        for a, contents in egi.area.items():
            for elem in contents:
                parent[elem] = a

        for m in matched_ids:
            p = parent.get(m)
            if p != area_id and p not in matched_ids:
                return False  # reaches outside the rooted subtrees

        for m in matched_ids:
            if m in c_ids:
                if not egi.area.get(m, frozenset()) <= matched_ids:
                    return False  # cut sliced — contents missing
        return True

    # ------------------------------------------------------------------
    # Legacy helpers retained for any external callers
    # ------------------------------------------------------------------

    def _categorize_elements(
        self, egi: RelationalGraphWithCuts, elements: FrozenSet[ElementID]
    ) -> Tuple[List[ElementID], List[ElementID], List[ElementID]]:
        """Categorize elements into vertices, edges, and cuts."""
        v_ids = {v.id for v in egi.V}
        e_ids = {e.id for e in egi.E}
        c_ids = {c.id for c in egi.Cut}
        vertices, edges, cuts = [], [], []
        for eid in elements:
            if eid in v_ids:
                vertices.append(eid)
            elif eid in e_ids:
                edges.append(eid)
            elif eid in c_ids:
                cuts.append(eid)
            else:
                raise ValueError(f"Unknown element ID: {eid}")
        return vertices, edges, cuts

    def _get_vertex_by_id(
        self, egi: RelationalGraphWithCuts, vertex_id: ElementID
    ) -> Vertex:
        """Get vertex by ID from EGI."""
        for v in egi.V:
            if v.id == vertex_id:
                return v
        raise ValueError(f"Vertex {vertex_id} not found")


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
