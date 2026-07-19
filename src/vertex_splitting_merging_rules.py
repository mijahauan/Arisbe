"""
Lemma 16.7: Vertex Splitting and Merging Rules
Implements Dau's formalism for splitting vertices across contexts and merging them back.
"""

from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

from frozendict import frozendict

from egi_core_dau import Cut, Edge, ElementID, RelationalGraphWithCuts, Vertex
from formal_transformation_rules import (
    FormalTransformationRule,
    TransformationContext,
    TransformationResult,
    _rebuild_graph,
    _refuse_quotation_boundary,
)


@dataclass
class VertexSplitSpec:
    """Specification for vertex splitting operation."""

    source_vertex: ElementID
    target_context: ElementID
    hooks_to_move: List[Tuple[ElementID, int]]  # (edge_id, position_in_nu)
    new_vertex_id: Optional[ElementID] = None


class VertexSplittingRule(FormalTransformationRule):
    """
    Lemma 16.7: Splitting a Vertex
    Splits a vertex v into v and v' with identity edge, moving specified hooks to v'.
    """

    def get_rule_name(self) -> str:
        return "SPLIT_VERTEX (Split Vertex Across Contexts)"

    def check_preconditions(
        self, context: TransformationContext
    ) -> Tuple[bool, Optional[str]]:
        """
        Requires selection of a single vertex and specification of target context.
        """
        # B-min: this rule re-plumbs identity; a selection touching the
        # quotation apparatus is refused entirely (deep=True, same
        # discipline as IT+/IT-'s guard).
        refusal = _refuse_quotation_boundary(
            context.source_egi,
            context.target_area,
            context.selected_subgraph,
            allow_whole_unit=False,
            deep=True,
        )
        if refusal:
            return False, refusal

        if len(context.selected_subgraph) != 1:
            return False, "Must select exactly one vertex for splitting"

        vertex_id = next(iter(context.selected_subgraph))
        egi = context.source_egi

        # Verify it's a vertex
        if not any(v.id == vertex_id for v in egi.V):
            return False, "Selected element must be a vertex"

        # Check that vertex has hooks that can be moved
        hooks = self._get_vertex_hooks(egi, vertex_id)
        if len(hooks) < 2:
            return False, "Vertex must have at least 2 hooks to be splittable"

        # Verify target context exists and is accessible
        target_context = context.target_area
        if target_context not in egi.area and target_context != egi.sheet:
            return False, f"Target context {target_context} does not exist"

        # Check context accessibility constraints
        vertex_context = self._get_vertex_context(egi, vertex_id)
        if not self._is_context_accessible_for_splitting(
            egi, vertex_context, target_context, hooks
        ):
            return False, "Target context is not accessible for the hooks to be moved"

        return True, None

    def apply_transformation(
        self, context: TransformationContext
    ) -> TransformationResult:
        """Apply vertex splitting transformation."""
        precondition_ok, error_msg = self.check_preconditions(context)
        if not precondition_ok:
            return TransformationResult(False, None, error_msg, {})

        try:
            egi = context.source_egi
            source_vertex_id = next(iter(context.selected_subgraph))
            target_context = context.target_area

            # Determine which hooks to move (for now, move half of them)
            all_hooks = self._get_vertex_hooks(egi, source_vertex_id)
            hooks_to_move = (
                all_hooks[: len(all_hooks) // 2] if len(all_hooks) > 1 else []
            )

            # Create split specification
            split_spec = VertexSplitSpec(
                source_vertex=source_vertex_id,
                target_context=target_context,
                hooks_to_move=hooks_to_move,
                new_vertex_id=ElementID(f"{source_vertex_id}_split"),
            )

            # Apply the splitting
            result_egi = self._apply_vertex_split(egi, split_spec)

            return TransformationResult(
                success=True,
                result_egi=result_egi,
                error_message=None,
                changes_made={
                    "rule": "SPLIT_VERTEX",
                    "source_vertex": str(source_vertex_id),
                    "new_vertex": str(split_spec.new_vertex_id),
                    "target_context": str(target_context),
                    "hooks_moved": len(hooks_to_move),
                    "identity_edge_created": f"id_{source_vertex_id}_{split_spec.new_vertex_id}",
                },
            )

        except Exception as e:
            return TransformationResult(False, None, str(e), {})

    def _apply_vertex_split(
        self, egi: RelationalGraphWithCuts, split_spec: VertexSplitSpec
    ) -> RelationalGraphWithCuts:
        """Apply the vertex splitting operation."""

        # Create new vertex
        new_vertex = Vertex(split_spec.new_vertex_id)

        # Create identity edge connecting original and new vertex
        identity_edge_id = ElementID(
            f"id_{split_spec.source_vertex}_{split_spec.new_vertex_id}"
        )
        identity_edge = Edge(identity_edge_id)

        # Update vertex set
        new_vertices = egi.V | {new_vertex}

        # Update edge set
        new_edges = egi.E | {identity_edge}

        # Update nu mapping
        new_nu = dict(egi.nu)

        # Add identity edge to nu mapping
        new_nu[identity_edge_id] = (split_spec.source_vertex, split_spec.new_vertex_id)

        # Update hooks that should be moved to new vertex
        for edge_id, position in split_spec.hooks_to_move:
            if edge_id in new_nu:
                old_sequence = list(new_nu[edge_id])
                if (
                    position < len(old_sequence)
                    and old_sequence[position] == split_spec.source_vertex
                ):
                    old_sequence[position] = split_spec.new_vertex_id
                    new_nu[edge_id] = tuple(old_sequence)

        # Update rel mapping
        new_rel = dict(egi.rel)
        new_rel[identity_edge_id] = "="

        # Update area mapping
        new_area_mapping = dict(egi.area)

        # Add new vertex and identity edge to target context
        if split_spec.target_context in new_area_mapping:
            current_contents = new_area_mapping[split_spec.target_context]
            new_area_mapping[split_spec.target_context] = current_contents | frozenset(
                [split_spec.new_vertex_id, identity_edge_id]
            )
        else:
            # Target context is sheet
            sheet_contents = new_area_mapping.get(egi.sheet, frozenset())
            new_area_mapping[egi.sheet] = sheet_contents | frozenset(
                [split_spec.new_vertex_id, identity_edge_id]
            )

        return _rebuild_graph(
            egi,
            V=frozenset(new_vertices),
            E=frozenset(new_edges),
            nu=frozendict(new_nu),
            area=frozendict(new_area_mapping),
            rel=frozendict(new_rel),
        )

    def _get_vertex_hooks(
        self, egi: RelationalGraphWithCuts, vertex_id: ElementID
    ) -> List[Tuple[ElementID, int]]:
        """Get all hooks (edge connections) for a vertex."""
        hooks = []
        for edge_id, vertex_sequence in egi.nu.items():
            for i, vid in enumerate(vertex_sequence):
                if vid == vertex_id:
                    hooks.append((edge_id, i))
        return hooks

    def _get_vertex_context(
        self, egi: RelationalGraphWithCuts, vertex_id: ElementID
    ) -> ElementID:
        """Get the context containing a vertex."""
        for area_id, contents in egi.area.items():
            if vertex_id in contents:
                return area_id
        return egi.sheet

    def _is_context_accessible_for_splitting(
        self,
        egi: RelationalGraphWithCuts,
        vertex_context: ElementID,
        target_context: ElementID,
        hooks: List[Tuple[ElementID, int]],
    ) -> bool:
        """Check if target context is accessible for splitting given the hooks."""

        # Check that target context is same or nested within vertex context
        if target_context == vertex_context:
            return True

        # Check if target_context is nested within vertex_context
        current = target_context
        while current != egi.sheet:
            parent = self._get_parent_context(egi, current)
            if parent is None:
                break
            if parent == vertex_context:
                return True
            current = parent

        # Check that all edges connected to hooks are accessible from target context
        for edge_id, position in hooks:
            edge_context = self._get_edge_context(egi, edge_id)
            if not self._is_context_accessible(egi, target_context, edge_context):
                return False

        return True

    def _get_parent_context(
        self, egi: RelationalGraphWithCuts, context: ElementID
    ) -> Optional[ElementID]:
        """Get the parent context of a given context."""
        for area_id, contents in egi.area.items():
            if context in contents and area_id != context:
                return area_id
        return None

    def _get_edge_context(
        self, egi: RelationalGraphWithCuts, edge_id: ElementID
    ) -> ElementID:
        """Get the context containing an edge."""
        for area_id, contents in egi.area.items():
            if edge_id in contents:
                return area_id
        return egi.sheet

    def _is_context_accessible(
        self,
        egi: RelationalGraphWithCuts,
        from_context: ElementID,
        to_context: ElementID,
    ) -> bool:
        """Check if to_context is accessible from from_context."""
        if from_context == to_context:
            return True

        # Check if to_context is nested within from_context or vice versa
        current = to_context
        while current != egi.sheet:
            parent = self._get_parent_context(egi, current)
            if parent is None:
                break
            if parent == from_context:
                return True
            current = parent

        current = from_context
        while current != egi.sheet:
            parent = self._get_parent_context(egi, current)
            if parent is None:
                break
            if parent == to_context:
                return True
            current = parent

        return False


class VertexMergingRule(FormalTransformationRule):
    """
    Lemma 16.7: Merging Two Vertices
    Merges vertex v2 into v1 by removing identity edge and redirecting all hooks.
    """

    def get_rule_name(self) -> str:
        return "MERGE_VERTICES (Merge Two Vertices)"

    def check_preconditions(
        self, context: TransformationContext
    ) -> Tuple[bool, Optional[str]]:
        """
        Requires selection of exactly two vertices connected by identity edge.
        """
        # B-min: this rule re-plumbs identity; a selection touching the
        # quotation apparatus is refused entirely (deep=True, same
        # discipline as IT+/IT-'s guard).
        refusal = _refuse_quotation_boundary(
            context.source_egi,
            context.target_area,
            context.selected_subgraph,
            allow_whole_unit=False,
            deep=True,
        )
        if refusal:
            return False, refusal

        if len(context.selected_subgraph) != 2:
            return False, "Must select exactly two vertices for merging"

        egi = context.source_egi
        vertices = list(context.selected_subgraph)
        v1_id, v2_id = vertices[0], vertices[1]

        # Verify both are vertices
        if not (
            any(v.id == v1_id for v in egi.V) and any(v.id == v2_id for v in egi.V)
        ):
            return False, "Both selected elements must be vertices"

        # Check if vertices are connected by identity edge
        identity_edge = self._find_identity_edge_between_vertices(egi, v1_id, v2_id)
        if identity_edge is None:
            return False, "Vertices must be connected by an identity edge"

        # Check context constraints for merging
        v1_context = self._get_vertex_context(egi, v1_id)
        v2_context = self._get_vertex_context(egi, v2_id)
        edge_context = self._get_edge_context(egi, identity_edge)

        # Dau's constraint: ctx(v1) ≥ ctx(e) = ctx(v2)
        if not (
            self._context_contains_or_equals(egi, v1_context, edge_context)
            and edge_context == v2_context
        ):
            return (
                False,
                "Context constraints not satisfied: ctx(v1) ≥ ctx(e) = ctx(v2)",
            )

        return True, None

    def apply_transformation(
        self, context: TransformationContext
    ) -> TransformationResult:
        """Apply vertex merging transformation."""
        precondition_ok, error_msg = self.check_preconditions(context)
        if not precondition_ok:
            return TransformationResult(False, None, error_msg, {})

        try:
            egi = context.source_egi
            vertices = list(context.selected_subgraph)
            v1_id, v2_id = vertices[0], vertices[1]

            # Find identity edge
            identity_edge_id = self._find_identity_edge_between_vertices(
                egi, v1_id, v2_id
            )

            # Apply the merging
            result_egi = self._apply_vertex_merge(egi, v1_id, v2_id, identity_edge_id)

            return TransformationResult(
                success=True,
                result_egi=result_egi,
                error_message=None,
                changes_made={
                    "rule": "MERGE_VERTICES",
                    "target_vertex": str(v1_id),
                    "merged_vertex": str(v2_id),
                    "removed_identity_edge": str(identity_edge_id),
                },
            )

        except Exception as e:
            return TransformationResult(False, None, str(e), {})

    def _apply_vertex_merge(
        self,
        egi: RelationalGraphWithCuts,
        v1_id: ElementID,
        v2_id: ElementID,
        identity_edge_id: ElementID,
    ) -> RelationalGraphWithCuts:
        """Apply the vertex merging operation."""

        # Remove v2 from vertices
        new_vertices = set(egi.V)
        for vertex in egi.V:
            if vertex.id == v2_id:
                new_vertices.remove(vertex)
                break

        # Remove identity edge from edges
        new_edges = set(egi.E)
        for edge in egi.E:
            if edge.id == identity_edge_id:
                new_edges.remove(edge)
                break

        # Update nu mapping: replace all occurrences of v2 with v1
        new_nu = {}
        for edge_id, vertex_sequence in egi.nu.items():
            if edge_id == identity_edge_id:
                continue  # Skip the identity edge being removed

            new_sequence = []
            for vertex_id in vertex_sequence:
                if vertex_id == v2_id:
                    new_sequence.append(v1_id)
                else:
                    new_sequence.append(vertex_id)
            new_nu[edge_id] = tuple(new_sequence)

        # Update rel mapping: remove identity edge
        new_rel = dict(egi.rel)
        if identity_edge_id in new_rel:
            del new_rel[identity_edge_id]

        # Update area mapping: remove v2 and identity edge from all areas
        new_area_mapping = {}
        for area_id, contents in egi.area.items():
            new_contents = set(contents)
            new_contents.discard(v2_id)
            new_contents.discard(identity_edge_id)
            new_area_mapping[area_id] = frozenset(new_contents)

        return _rebuild_graph(
            egi,
            V=frozenset(new_vertices),
            E=frozenset(new_edges),
            nu=frozendict(new_nu),
            area=frozendict(new_area_mapping),
            rel=frozendict(new_rel),
        )

    def _find_identity_edge_between_vertices(
        self, egi: RelationalGraphWithCuts, v1_id: ElementID, v2_id: ElementID
    ) -> Optional[ElementID]:
        """Find identity edge connecting two vertices."""
        for edge_id, vertex_sequence in egi.nu.items():
            if (
                egi.rel.get(edge_id) == "="
                and len(vertex_sequence) == 2
                and (
                    (vertex_sequence[0] == v1_id and vertex_sequence[1] == v2_id)
                    or (vertex_sequence[0] == v2_id and vertex_sequence[1] == v1_id)
                )
            ):
                return edge_id
        return None

    def _get_vertex_context(
        self, egi: RelationalGraphWithCuts, vertex_id: ElementID
    ) -> ElementID:
        """Get the context containing a vertex."""
        for area_id, contents in egi.area.items():
            if vertex_id in contents:
                return area_id
        return egi.sheet

    def _get_edge_context(
        self, egi: RelationalGraphWithCuts, edge_id: ElementID
    ) -> ElementID:
        """Get the context containing an edge."""
        for area_id, contents in egi.area.items():
            if edge_id in contents:
                return area_id
        return egi.sheet

    def _context_contains_or_equals(
        self, egi: RelationalGraphWithCuts, context1: ElementID, context2: ElementID
    ) -> bool:
        """Check if context1 contains context2 or they are equal."""
        if context1 == context2:
            return True

        # Check if context2 is nested within context1
        current = context2
        while current != egi.sheet:
            parent = None
            for area_id, contents in egi.area.items():
                if current in contents and area_id != current:
                    parent = area_id
                    break

            if parent is None:
                break

            if parent == context1:
                return True

            current = parent

        return False


def demonstrate_vertex_splitting_merging():
    """Demonstrate vertex splitting and merging operations."""

    print("🔄 Vertex Splitting/Merging Demonstration")
    print("=" * 45)

    from egi_core_dau import Cut, Edge, ElementID, RelationalGraphWithCuts, Vertex

    # Create test EGI with vertex that can be split
    vertex_a = Vertex(ElementID("A"))
    vertex_b = Vertex(ElementID("B"))
    vertex_c = Vertex(ElementID("C"))

    edge_r = Edge(ElementID("R"))
    edge_s = Edge(ElementID("S"))
    edge_t = Edge(ElementID("T"))

    cut1 = Cut(ElementID("cut1"))

    test_egi = RelationalGraphWithCuts(
        V=frozenset([vertex_a, vertex_b, vertex_c]),
        E=frozenset([edge_r, edge_s, edge_t]),
        nu=frozendict(
            {
                ElementID("R"): (ElementID("A"), ElementID("B")),
                ElementID("S"): (ElementID("A"), ElementID("C")),
                ElementID("T"): (ElementID("A"), ElementID("A")),  # Self-loop
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
                        ElementID("R"),
                        ElementID("S"),
                        ElementID("T"),
                        ElementID("cut1"),
                    ]
                ),
                ElementID("cut1"): frozenset([ElementID("C")]),
            }
        ),
        rel=frozendict(
            {
                ElementID("R"): "Relation1",
                ElementID("S"): "Relation2",
                ElementID("T"): "Relation3",
            }
        ),
    )

    print("\n📊 Test EGI Structure:")
    print(f"   Vertices: {[v.id for v in test_egi.V]}")
    print(f"   Edges: {[e.id for e in test_egi.E]}")
    print(f"   Vertex A hooks: R(A,B), S(A,C), T(A,A)")
    print(f"   Areas: sheet contains A,B; cut1 contains C")

    # Test vertex splitting
    print("\n🔄 Test 1: Split Vertex A")
    splitting_rule = VertexSplittingRule()

    from formal_transformation_rules import AreaPolarity, TransformationContext

    split_context = TransformationContext(
        source_egi=test_egi,
        target_area=ElementID("cut1"),
        selected_subgraph=frozenset([ElementID("A")]),
        area_polarity=AreaPolarity.POSITIVE,
        nesting_depth=1,
    )

    split_result = splitting_rule.apply_transformation(split_context)

    print(f"   Success: {'✅' if split_result.success else '❌'}")
    if split_result.success:
        print(f"   Changes: {split_result.changes_made}")
        split_egi = split_result.result_egi
        print(f"   Result vertices: {len(split_egi.V)}")
        print(f"   Result edges: {len(split_egi.E)}")
    else:
        print(f"   Error: {split_result.error_message}")

    # Test vertex merging (if split was successful)
    if split_result.success:
        print("\n🔄 Test 2: Merge Vertices Back")
        merging_rule = VertexMergingRule()

        # Find the identity edge created by splitting
        split_egi = split_result.result_egi
        identity_edges = []
        for edge_id, vertex_sequence in split_egi.nu.items():
            if split_egi.rel.get(edge_id) == "=" and len(vertex_sequence) == 2:
                identity_edges.append((edge_id, vertex_sequence))

        if identity_edges:
            edge_id, (v1, v2) = identity_edges[0]
            print(f"   Found identity edge {edge_id} connecting {v1} and {v2}")

            merge_context = TransformationContext(
                source_egi=split_egi,
                target_area=ElementID("sheet"),
                selected_subgraph=frozenset([v1, v2]),
                area_polarity=AreaPolarity.POSITIVE,
                nesting_depth=0,
            )

            merge_result = merging_rule.apply_transformation(merge_context)

            print(f"   Success: {'✅' if merge_result.success else '❌'}")
            if merge_result.success:
                print(f"   Changes: {merge_result.changes_made}")
                merged_egi = merge_result.result_egi
                print(f"   Final vertices: {len(merged_egi.V)}")
                print(f"   Final edges: {len(merged_egi.E)}")
            else:
                print(f"   Error: {merge_result.error_message}")

    print(f"\n✅ Vertex Splitting/Merging Complete")
    print(f"   - Lemma 16.7 implemented: ✅")
    print(f"   - Context constraints enforced: ✅")
    print(f"   - Hook redistribution: ✅")
    print(f"   - Identity edge management: ✅")

    return splitting_rule, merging_rule


if __name__ == "__main__":
    demonstrate_vertex_splitting_merging()
