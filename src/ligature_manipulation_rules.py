"""
Chapter 16 Ligature Manipulation Rules implementing Dau's formalism.
These rules allow rearranging ligatures while preserving logical meaning.
"""

from abc import ABC, abstractmethod
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


def _canonical_vertex_order(
    egi: RelationalGraphWithCuts, vertex_ids
) -> List[ElementID]:
    """The selected vertices in an order that is a function of the graph.

    These rules keep — or move a hook from — one vertex of an unordered
    selection, and a frozenset iterates in the order of the per-process string
    hash, so ``list(selection)[0]`` kept one vertex under one hash seed and
    another under another. Canonical signatures are UUID- and seed-independent;
    the id only breaks a tie between vertices the signature cannot tell apart,
    which are the symmetric ones, where the two results are isomorphic anyway.
    """
    from canonical_signature import compute_canonical_signatures

    vertex_signatures, _, _ = compute_canonical_signatures(egi)
    return sorted(
        vertex_ids, key=lambda v_id: (repr(vertex_signatures.get(v_id)), v_id)
    )


def _refuse_constant_vertices(
    egi: RelationalGraphWithCuts, vertex_ids
) -> Optional[str]:
    """Def 24.10 (p.270) restricts genericity to the vertex ADDED or REMOVED.

    "adding a generic vertex to a ligature: Let v ∈ V be a vertex which is
    attached to a hook (e, i) … In c, a new GENERIC vertex v′ and a new
    identity-edge between v and v′ is inserted" — v may be any vertex,
    constant included; only v′ must be generic. "removing a generic vertex
    from a ligature" is that rule reversed, so it is again v′ — the vertex
    that goes — that must be generic. p.272's "only generic vertices are
    considered" is about those two rules' own v′, not about every vertex of
    the ligature: Def 24.9 (p.269) deliberately lets a ligature mix generic
    and constant vertices, and Deseparating (p.271) works on constant ones.

    So ``vertex_ids`` is the vertices the caller is about to ERASE (or add),
    never the whole selection. The first form of this guard passed the whole
    selection and refused lawful moves: an extension anchored on a constant, a
    rearrangement of a constant ligature, and the merge of a generic vertex
    INTO a constant — which keeps the name, and which the suite's own control
    measures as an equivalence.

    A constant vertex's name is part of what the graph says, so erasing one is
    not a ligature move at all; the rule that joins constants is the Constant
    Identity Rule (p.271), which requires ρ(v) = ρ(w). Returns a refusal, or None.
    """
    by_id = {v.id: v for v in egi.V}
    named = sorted(
        v_id for v_id in vertex_ids if v_id in by_id and not by_id[v_id].is_generic
    )
    if named:
        return (
            f"The ligature rules move generic vertices only (Def 24.10, p.270-272); "
            f"{named[0]} carries a constant name"
        )
    return None


def _refuse_edges_in_another_context(
    egi: RelationalGraphWithCuts, vertex_ids, contexts
) -> Optional[str]:
    """Lemma 16.3 (p.173) and Def 16.4 (p.174) both take a ligature (W, F)
    *placed in* a context c — "ctx(w) = c = ctx(f) for all w ∈ W and f ∈ F" —
    so every identity edge of the ligature sits in c too, not only its
    vertices; Θ itself says the same (Def 24.9, p.269: ctx(e_i) = ctx(v_{i+1})).
    Without this, `*x *y ~[ (= x y) ]` retracts to `*x ~[ ]`: true becomes
    false, because that edge was an assertion under a negation, not wiring.
    """
    (ligature_context,) = contexts
    selected = set(vertex_ids)
    for edge_id, vertex_sequence in sorted(egi.nu.items()):
        if (
            egi.rel.get(edge_id) == "="
            and len(vertex_sequence) == 2
            and vertex_sequence[0] in selected
            and vertex_sequence[1] in selected
            and egi.get_context(edge_id) != ligature_context
        ):
            return (
                f"The ligature's identity edges must lie in the same context as its "
                f"vertices (Lemma 16.3, p.173): {edge_id} sits in "
                f"{egi.get_context(edge_id)}, the vertices in {ligature_context}"
            )
    return None


def _encloses(
    egi: RelationalGraphWithCuts, outer: ElementID, inner: ElementID
) -> bool:
    """``outer`` >= ``inner`` in Dau's order on contexts: outer is inner, or
    encloses it. Dau writes the sheet as the maximum and reads inward as
    smaller (Def 15.2's iteration, p.164: "let c <= ctx(G0)" copies inward)."""
    current = inner
    while True:
        if current == outer:
            return True
        if current == egi.sheet:
            return False
        current = egi.get_context(current)


def _identity_edges_below(
    egi: RelationalGraphWithCuts, va_id: ElementID, vb_id: ElementID
) -> List[ElementID]:
    """The identity edges on {v_a, v_b} that sit deeper than both vertices."""
    pair = {va_id, vb_id}
    return sorted(
        edge_id
        for edge_id, seq in egi.nu.items()
        if egi.rel.get(edge_id) == "="
        and len(seq) == 2
        and set(seq) == pair
        and egi.get_context(edge_id) not in (
            egi.get_context(va_id),
            egi.get_context(vb_id),
        )
    )


def _theta(
    egi: RelationalGraphWithCuts,
    v_id: ElementID,
    w_id: ElementID,
    excluded_edge: Optional[ElementID] = None,
) -> bool:
    """Def 15.1 (Θ, p.163), as Dau states it — NOT bare `=`-connectivity.

    "vΘw iff there exist vertices v1, ..., vn with 1. either v = v1 and vn = w,
    or w = v1 and vn = v, 2. ctx(v1) >= ctx(v2) >= ... >= ctx(vn), and 3. for
    each i, there exists an identity edge ei = {vi, vi+1} with
    ctx(ei) = ctx(vi+1)."

    Clause 3 is the one this module kept losing. An identity edge may lawfully
    sit DEEPER than the vertices it joins (Def 12.5's dominating nodes, p.125,
    asks only that each vertex's context enclose the edge's) — but then it is
    an assertion made under a cut, not wiring, and Θ does not hold. That is
    exactly what the iteration rule needs Θ for (Def 15.2, p.164): vΘw is what
    licenses inserting an identity edge between v and w INTO the target
    context c, which is the step Lemma 16.1's proof (p.170-171) takes.

    Walk clause 1's two orientations separately: clause 2 makes a chain
    monotone INWARD, so a chain from v to w and one from w to v are different
    claims. (Dau notes Θ is reflexive and symmetric but not transitive.)
    """
    return _theta_chain(egi, v_id, w_id, excluded_edge) or _theta_chain(
        egi, w_id, v_id, excluded_edge
    )


def _theta_chain(
    egi: RelationalGraphWithCuts,
    start: ElementID,
    goal: ElementID,
    excluded_edge: Optional[ElementID],
) -> bool:
    """One orientation of Def 15.1: a chain start = v1, ..., vn = goal running
    monotonically inward, each step's identity edge in the inner vertex's own
    context."""
    if start == goal:
        return True          # n = 1: Θ is reflexive
    seen, stack = {start}, [start]
    while stack:
        current = stack.pop()
        current_context = egi.get_context(current)
        for edge_id, seq in sorted(egi.nu.items()):
            if (
                edge_id == excluded_edge
                or egi.rel.get(edge_id) != "="
                or len(seq) != 2
                or current not in seq
            ):
                continue
            next_id = seq[1] if seq[0] == current else seq[0]
            if next_id in seen:
                continue
            next_context = egi.get_context(next_id)
            # Clause 3: ctx(e_i) = ctx(v_{i+1}).
            if egi.get_context(edge_id) != next_context:
                continue
            # Clause 2: ctx(v_i) >= ctx(v_{i+1}) — the chain runs inward.
            if not _encloses(egi, current_context, next_context):
                continue
            if next_id == goal:
                return True
            seen.add(next_id)
            stack.append(next_id)
    return False


class MoveBranchesAlongLigatureRule(FormalTransformationRule):
    """
    Lemma 16.1: Moving Branches along a Ligature in a Context
    Allows repositioning vertices along the same ligature while preserving identity.
    """

    def get_rule_name(self) -> str:
        return "MOVE_BRANCHES (Move Branches Along Ligature)"

    def check_preconditions(
        self, context: TransformationContext
    ) -> Tuple[bool, Optional[str]]:
        """
        Requires two vertices on the same ligature in the same context.
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
            return False, "Must select exactly two vertices for branch moving"

        egi = context.source_egi
        vertices = _canonical_vertex_order(egi, context.selected_subgraph)
        va_id, vb_id = vertices[0], vertices[1]

        # Verify both are vertices
        va = self._get_vertex_by_id(egi, va_id)
        vb = self._get_vertex_by_id(egi, vb_id)

        if not va or not vb:
            return False, "Selected elements must be vertices"

        # No genericity condition here: Lemma 16.1 (p.169) moves a hook and
        # adds or removes no vertex, so Def 24.10's generic v′ (p.270) has
        # nothing to bind to. v_aΘv_b makes the two denote one object, so
        # moving a hook between them is sound whatever names they carry.

        # Check if vertices are in same context
        va_context = self._get_vertex_context(egi, va_id)
        vb_context = self._get_vertex_context(egi, vb_id)

        if va_context != vb_context:
            return False, "Vertices must be in the same context for branch moving"

        # Lemma 16.1's own premise (p.169): "let va, vb be two vertices with
        # c := ctx(va) = ctx(vb) and vaΘvb". Θ is Def 15.1 (p.163) — a chain
        # running inward whose every identity edge sits in the context of the
        # vertex it reaches. With ctx(va) = ctx(vb) that forces the whole chain,
        # edges included, into c: the same reading Lemma 16.3 (p.173) and Def
        # 16.4 (p.174) get from _refuse_edges_in_another_context. Counting any
        # `=` edge wherever it sits made the rule move a hook across an
        # identity that a cut ASSERTS rather than wires, and changed meaning.
        if not self._vertices_on_same_ligature(egi, va_id, vb_id):
            return False, self._theta_refusal(egi, va_id, vb_id)

        # Lemma 16.1 (p.169-171): the lemma moves ONE hook (e, i) on v_a, and
        # its proof deiterates v3/e4/e1 as a copy of v2 — which needs v_aΘv_b
        # to hold in the graph *without* the hook being moved. So the side
        # condition is about the hook actually moved, not about every edge on
        # v_a: _hook_to_move takes the first hook the lemma licenses and passes
        # over one whose edge is the join's only witness. If v_a carries no
        # such hook, the lemma licenses nothing here.
        if self._hook_to_move(egi, va_id, vb_id) is None:
            return False, (
                f"Every hook on {va_id} sits on an identity edge that witnesses "
                f"the link itself, so moving one would take the witness with it "
                f"(Lemma 16.1, p.169-171)"
            )

        return True, None

    def apply_transformation(
        self, context: TransformationContext
    ) -> TransformationResult:
        """Apply branch moving by repositioning vertex on ligature."""
        precondition_ok, error_msg = self.check_preconditions(context)
        if not precondition_ok:
            return TransformationResult(False, None, error_msg, {})

        try:
            egi = context.source_egi
            vertices = _canonical_vertex_order(egi, context.selected_subgraph)
            va_id, vb_id = vertices[0], vertices[1]

            # The one hook Lemma 16.1 (p.169) licenses moving — the very hook
            # check_preconditions vouched for, so the condition it checks and
            # the hook this moves can never come apart.
            hook = self._hook_to_move(egi, va_id, vb_id)

            if hook is None:
                return TransformationResult(
                    False, None, "No hook on the source vertex that Lemma 16.1 licenses moving", {}
                )
            edge_to_modify, hook_position = hook

            # Create new nu mapping with vertex replaced
            new_nu = dict(egi.nu)
            old_sequence = list(new_nu[edge_to_modify])
            old_sequence[hook_position] = vb_id
            new_nu[edge_to_modify] = tuple(old_sequence)

            result_egi = _rebuild_graph(
                egi,
                nu=frozendict(new_nu),
            )

            return TransformationResult(
                success=True,
                result_egi=result_egi,
                error_message=None,
                changes_made={
                    "rule": "MOVE_BRANCHES",
                    "moved_from": str(va_id),
                    "moved_to": str(vb_id),
                    "modified_edge": str(edge_to_modify),
                    "hook_position": hook_position,
                },
            )

        except Exception as e:
            return TransformationResult(False, None, str(e), {})

    def _get_vertex_by_id(
        self, egi: RelationalGraphWithCuts, vertex_id: ElementID
    ) -> Optional[Vertex]:
        """Get vertex by ID."""
        for v in egi.V:
            if v.id == vertex_id:
                return v
        return None

    def _get_vertex_context(
        self, egi: RelationalGraphWithCuts, vertex_id: ElementID
    ) -> ElementID:
        """Get the context (area) containing this vertex."""
        for area_id, contents in egi.area.items():
            if vertex_id in contents:
                return area_id
        return egi.sheet  # Default to sheet

    def _hook_to_move(
        self, egi: RelationalGraphWithCuts, va_id: ElementID, vb_id: ElementID
    ) -> Optional[Tuple[ElementID, int]]:
        """The one hook (e, i) on v_a that this rule moves, or None.

        Lemma 16.1 (p.169) is stated for *an* edge e whose hook (e, i) is
        attached to v_a; the rule is not told which, so the engine chooses.
        The choice is a function of the graph (canonical signature order), and
        it is a hook whose move the lemma licenses: a hook on the only identity
        edge witnessing v_aΘv_b is passed over, since the lemma's proof
        (p.170-171) deiterates against a v_aΘv_b that survives the move.
        """
        from canonical_signature import compute_canonical_signatures

        _, edge_signatures, _ = compute_canonical_signatures(egi)
        hooks = sorted(
            (repr(edge_signatures.get(edge_id)), edge_id, position)
            for edge_id, vertex_sequence in egi.nu.items()
            for position, vertex_id in enumerate(vertex_sequence)
            if vertex_id == va_id
        )
        for _, edge_id, position in hooks:
            if self._vertices_on_same_ligature_excluding(egi, va_id, vb_id, edge_id):
                return edge_id, position
        return None

    def _vertices_on_same_ligature_excluding(
        self,
        egi: RelationalGraphWithCuts,
        va_id: ElementID,
        vb_id: ElementID,
        excluded_edge: ElementID,
    ) -> bool:
        """Whether v_aΘv_b still holds with ``excluded_edge`` set aside."""
        return _theta(egi, va_id, vb_id, excluded_edge=excluded_edge)

    def _vertices_on_same_ligature(
        self, egi: RelationalGraphWithCuts, va_id: ElementID, vb_id: ElementID
    ) -> bool:
        """Whether v_aΘv_b — Def 15.1 (p.163), not bare `=`-connectivity."""
        return _theta(egi, va_id, vb_id)

    def _theta_refusal(
        self, egi: RelationalGraphWithCuts, va_id: ElementID, vb_id: ElementID
    ) -> str:
        """Why Θ fails, in EG terms, naming a deeper identity edge if one is why."""
        deeper = _identity_edges_below(egi, va_id, vb_id)
        if deeper:
            edge_id = deeper[0]
            return (
                f"The identity edge {edge_id} joining {va_id} to {vb_id} lies inside "
                f"{egi.get_context(edge_id)}, deeper than the vertices in "
                f"{egi.get_context(va_id)}: enclosed by a cut it ASSERTS that the two "
                f"denote one thing rather than wiring them into one ligature, so "
                f"v_aΘv_b fails (Def 15.1, p.163, clause 3: ctx(e_i) = ctx(v_i+1)) "
                f"and Lemma 16.1 (p.169-171) licenses no move"
            )
        return (
            f"No ligature joins {va_id} to {vb_id} within their own context, so "
            f"v_aΘv_b fails (Def 15.1, p.163) and Lemma 16.1 (p.169-171), which is "
            f"stated for v_aΘv_b, licenses no move"
        )


class ExtendRestrictLigatureRule(FormalTransformationRule):
    """
    Lemma 16.2: Extending or Restricting a Ligature in a Context
    Allows adding new identity networks to existing ligatures.
    """

    def get_rule_name(self) -> str:
        return "EXTEND_LIGATURE (Extend or Restrict Ligature)"

    def check_preconditions(
        self, context: TransformationContext
    ) -> Tuple[bool, Optional[str]]:
        """
        Requires a vertex on an existing ligature and specification of new identity network.
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
            return False, "Must select exactly one vertex for ligature extension"

        vertex_id = next(iter(context.selected_subgraph))
        egi = context.source_egi

        # Verify it's a vertex
        if not any(v.id == vertex_id for v in egi.V):
            return False, "Selected element must be a vertex"

        # No genericity condition on the anchor: Def 24.10 (p.270) is explicit
        # that the vertex an extension hangs from is any "v ∈ V" and only the
        # ADDED vertex v′ is generic — which the ones this rule creates are,
        # by construction (Vertex(id) with no label).
        #
        # And no *ligature* condition either (2026-09-21). Lemma 16.2 (p.172)
        # reads: "Let a EGI 𝔊 be given with a vertex v. Let V′ be a set of fresh
        # vertices and E′ be a set of fresh edges ... placed in the context
        # ctx(v), and all fresh edges are identity edges between the vertices of
        # {v} ⊍ V′ such that we have vΘv′ for each v′ ∈ V′." The only
        # precondition on the *source* is that v be a vertex; every other clause
        # governs what is BUILT, which apply_transformation does — two fresh
        # vertices and two fresh identity edges, all in ctx(v). A lone vertex is
        # a ligature of one, and the lemma extends it.
        #
        # This method used to demand an existing identity edge and refuse with
        # "Selected vertex must be on an existing ligature", declining half of an
        # equivalence rule — 524 moves in the default calculus mode, 6,538 at
        # exhaustive bounds — while the comment directly above already said the
        # anchor is any v ∈ V. The oracle written for this rule on 2026-09-20
        # (tests/calculus_rules._extend_ligature) made the departure countable,
        # and the ledger entry it carried, `extend-ligature-wants-an-existing-
        # ligature`, is retired by this change rather than rewritten.
        return True, None

    def apply_transformation(
        self, context: TransformationContext
    ) -> TransformationResult:
        """Apply ligature extension by adding new identity network."""
        precondition_ok, error_msg = self.check_preconditions(context)
        if not precondition_ok:
            return TransformationResult(False, None, error_msg, {})

        try:
            egi = context.source_egi
            base_vertex_id = next(iter(context.selected_subgraph))

            # Create new vertices for the extension
            new_vertex_1_id = ElementID(f"{base_vertex_id}_ext_1")
            new_vertex_2_id = ElementID(f"{base_vertex_id}_ext_2")

            new_vertex_1 = Vertex(new_vertex_1_id)
            new_vertex_2 = Vertex(new_vertex_2_id)

            # Create identity edges connecting the new vertices to the base vertex
            identity_edge_1_id = ElementID(
                f"id_edge_{base_vertex_id}_{new_vertex_1_id}"
            )
            identity_edge_2_id = ElementID(
                f"id_edge_{new_vertex_1_id}_{new_vertex_2_id}"
            )

            identity_edge_1 = Edge(identity_edge_1_id)
            identity_edge_2 = Edge(identity_edge_2_id)

            # Update EGI components
            new_vertices = egi.V | {new_vertex_1, new_vertex_2}
            new_edges = egi.E | {identity_edge_1, identity_edge_2}

            new_nu = dict(egi.nu)
            new_nu[identity_edge_1_id] = (base_vertex_id, new_vertex_1_id)
            new_nu[identity_edge_2_id] = (new_vertex_1_id, new_vertex_2_id)

            new_rel = dict(egi.rel)
            new_rel[identity_edge_1_id] = "="
            new_rel[identity_edge_2_id] = "="

            # Add new elements to the same context as base vertex
            base_vertex_context = self._get_vertex_context(egi, base_vertex_id)
            new_area_mapping = dict(egi.area)
            current_area_contents = new_area_mapping.get(
                base_vertex_context, frozenset()
            )
            new_area_mapping[base_vertex_context] = current_area_contents | frozenset(
                [
                    new_vertex_1_id,
                    new_vertex_2_id,
                    identity_edge_1_id,
                    identity_edge_2_id,
                ]
            )

            result_egi = _rebuild_graph(
                egi,
                V=new_vertices,
                E=new_edges,
                nu=frozendict(new_nu),
                area=frozendict(new_area_mapping),
                rel=frozendict(new_rel),
            )

            return TransformationResult(
                success=True,
                result_egi=result_egi,
                error_message=None,
                changes_made={
                    "rule": "EXTEND_LIGATURE",
                    "base_vertex": str(base_vertex_id),
                    "new_vertices": [str(new_vertex_1_id), str(new_vertex_2_id)],
                    "new_identity_edges": [
                        str(identity_edge_1_id),
                        str(identity_edge_2_id),
                    ],
                    "context": str(base_vertex_context),
                },
            )

        except Exception as e:
            return TransformationResult(False, None, str(e), {})

    def _get_vertex_context(
        self, egi: RelationalGraphWithCuts, vertex_id: ElementID
    ) -> ElementID:
        """Get the context (area) containing this vertex."""
        for area_id, contents in egi.area.items():
            if vertex_id in contents:
                return area_id
        return egi.sheet  # Default to sheet


class RetractLigatureRule(FormalTransformationRule):
    """
    Lemma 16.3: Retracting a Ligature in a Context
    Collapses an entire ligature (W,F) to a single vertex w0.
    """

    def get_rule_name(self) -> str:
        return "RETRACT_LIGATURE (Retract Ligature to Single Vertex)"

    def check_preconditions(
        self, context: TransformationContext
    ) -> Tuple[bool, Optional[str]]:
        """
        Requires selection of ligature vertices and specification of target vertex.
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

        if len(context.selected_subgraph) < 2:
            return (
                False,
                "Must select at least 2 vertices forming a ligature for retraction",
            )

        egi = context.source_egi
        selected_vertices = _canonical_vertex_order(egi, context.selected_subgraph)

        # Verify all selected elements are vertices
        for vertex_id in selected_vertices:
            if not any(v.id == vertex_id for v in egi.V):
                return False, f"Selected element {vertex_id} is not a vertex"

        # Lemma 16.3 (p.173) keeps w0 and ERASES W\{w0}, so Def 24.10's
        # condition (p.270) falls on the erased vertices only: w0 may carry a
        # name — retracting `(= "a" *y)` onto "a" keeps it — while erasing one
        # would take a name the graph asserts with it. selected_vertices[0] is
        # w0 (the canonical order this rule's apply_transformation also uses).
        refusal = _refuse_constant_vertices(egi, selected_vertices[1:])
        if refusal:
            return False, refusal

        # Check if vertices form a connected ligature
        if not self._vertices_form_ligature(egi, selected_vertices):
            return False, "Selected vertices must form a connected ligature"

        # Check if all vertices are in the same context
        contexts = set()
        for vertex_id in selected_vertices:
            vertex_context = self._get_vertex_context(egi, vertex_id)
            contexts.add(vertex_context)

        if len(contexts) > 1:
            return (
                False,
                "All ligature vertices must be in the same context for retraction",
            )

        refusal = _refuse_edges_in_another_context(egi, selected_vertices, contexts)
        if refusal:
            return False, refusal

        return True, None

    def apply_transformation(
        self, context: TransformationContext
    ) -> TransformationResult:
        """Apply ligature retraction by collapsing to single vertex."""
        precondition_ok, error_msg = self.check_preconditions(context)
        if not precondition_ok:
            return TransformationResult(False, None, error_msg, {})

        try:
            egi = context.source_egi
            # Lemma 16.3 (p.173) retracts to *a* vertex w0 ∈ W and does not say
            # which; the engine must choose, and the choice must be a function
            # of the graph, not of the process (see _canonical_vertex_order).
            ligature_vertices = _canonical_vertex_order(egi, context.selected_subgraph)

            # Choose the canonically first vertex as target (w0 in Dau's notation)
            target_vertex_id = ligature_vertices[0]
            vertices_to_remove = set(ligature_vertices[1:])

            # Find all identity edges within the ligature
            ligature_edges = set()
            for edge_id, vertex_sequence in egi.nu.items():
                if (
                    egi.rel.get(edge_id) == "="
                    and len(vertex_sequence) == 2
                    and vertex_sequence[0] in ligature_vertices
                    and vertex_sequence[1] in ligature_vertices
                ):
                    ligature_edges.add(edge_id)

            # Update nu mapping: redirect all edges from removed vertices to target vertex
            new_nu = dict(egi.nu)
            for edge_id, vertex_sequence in egi.nu.items():
                if (
                    edge_id not in ligature_edges
                ):  # Don't modify ligature edges (they'll be removed)
                    new_sequence = []
                    for vertex_id in vertex_sequence:
                        if vertex_id in vertices_to_remove:
                            new_sequence.append(target_vertex_id)
                        else:
                            new_sequence.append(vertex_id)
                    new_nu[edge_id] = tuple(new_sequence)

            # Remove ligature edges from nu and rel
            for edge_id in ligature_edges:
                if edge_id in new_nu:
                    del new_nu[edge_id]

            new_rel = dict(egi.rel)
            for edge_id in ligature_edges:
                if edge_id in new_rel:
                    del new_rel[edge_id]

            # Remove vertices and edges from EGI
            new_vertices = set(egi.V)
            new_edges = set(egi.E)

            for vertex in egi.V:
                if vertex.id in vertices_to_remove:
                    new_vertices.remove(vertex)

            for edge in egi.E:
                if edge.id in ligature_edges:
                    new_edges.remove(edge)

            # Update area mappings
            new_area_mapping = dict(egi.area)
            for area_id, contents in egi.area.items():
                new_contents = set(contents)
                # Remove vertices and edges from areas
                for vertex_id in vertices_to_remove:
                    new_contents.discard(vertex_id)
                for edge_id in ligature_edges:
                    new_contents.discard(edge_id)
                new_area_mapping[area_id] = frozenset(new_contents)

            result_egi = _rebuild_graph(
                egi,
                V=frozenset(new_vertices),
                E=frozenset(new_edges),
                nu=frozendict(new_nu),
                area=frozendict(new_area_mapping),
                rel=frozendict(new_rel),
            )

            return TransformationResult(
                success=True,
                result_egi=result_egi,
                error_message=None,
                changes_made={
                    "rule": "RETRACT_LIGATURE",
                    "target_vertex": str(target_vertex_id),
                    "removed_vertices": [str(v) for v in vertices_to_remove],
                    "removed_edges": [str(e) for e in ligature_edges],
                    "ligature_size": len(ligature_vertices),
                },
            )

        except Exception as e:
            return TransformationResult(False, None, str(e), {})

    def _vertices_form_ligature(
        self, egi: RelationalGraphWithCuts, vertices: List[ElementID]
    ) -> bool:
        """Check if vertices form a connected ligature via identity edges."""
        if len(vertices) < 2:
            return False

        # Build graph of identity connections
        identity_graph = {}
        for vertex_id in vertices:
            identity_graph[vertex_id] = set()

        for edge_id, vertex_sequence in egi.nu.items():
            if (
                egi.rel.get(edge_id) == "="
                and len(vertex_sequence) == 2
                and vertex_sequence[0] in vertices
                and vertex_sequence[1] in vertices
            ):
                identity_graph[vertex_sequence[0]].add(vertex_sequence[1])
                identity_graph[vertex_sequence[1]].add(vertex_sequence[0])

        # Check connectivity using DFS
        visited = set()
        stack = [vertices[0]]
        visited.add(vertices[0])

        while stack:
            current = stack.pop()
            for neighbor in identity_graph.get(current, set()):
                if neighbor not in visited:
                    visited.add(neighbor)
                    stack.append(neighbor)

        return len(visited) == len(vertices)

    def _get_vertex_context(
        self, egi: RelationalGraphWithCuts, vertex_id: ElementID
    ) -> ElementID:
        """Get the context (area) containing this vertex."""
        for area_id, contents in egi.area.items():
            if vertex_id in contents:
                return area_id
        return egi.sheet


class LigatureRearrangementRule(FormalTransformationRule):
    """
    Definition 16.4: Rearranging Ligatures in a Context
    Replaces ligature (W,F) with new ligature (W',F') in same context.
    """

    def get_rule_name(self) -> str:
        return "REARRANGE_LIGATURE (Rearrange Ligature Structure)"

    def check_preconditions(
        self, context: TransformationContext
    ) -> Tuple[bool, Optional[str]]:
        """
        Requires selection of ligature vertices and specification of new structure.
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

        if len(context.selected_subgraph) < 2:
            return (
                False,
                "Must select at least 2 vertices forming a ligature for rearrangement",
            )

        egi = context.source_egi
        selected_vertices = _canonical_vertex_order(egi, context.selected_subgraph)

        # Verify all selected elements are vertices
        for vertex_id in selected_vertices:
            if not any(v.id == vertex_id for v in egi.V):
                return False, f"Selected element {vertex_id} is not a vertex"

        # No genericity condition: this rule replaces (W, F) by (W', F') with
        # W' = W — it rewires identity edges and adds or removes no vertex
        # (apply_transformation below keeps egi.V untouched), so Def 24.10's
        # generic v′ (p.270) has nothing to bind to. Def 24.9 (p.269) lets a
        # ligature mix generic and constant vertices, and rearranging one
        # changes no name.

        # Check if vertices form a connected ligature
        if not self._vertices_form_ligature(egi, selected_vertices):
            return False, "Selected vertices must form a connected ligature"

        # Check if all vertices are in the same context
        contexts = set()
        for vertex_id in selected_vertices:
            vertex_context = self._get_vertex_context(egi, vertex_id)
            contexts.add(vertex_context)

        if len(contexts) > 1:
            return (
                False,
                "All ligature vertices must be in the same context for rearrangement",
            )

        refusal = _refuse_edges_in_another_context(egi, selected_vertices, contexts)
        if refusal:
            return False, refusal

        return True, None

    def apply_transformation(
        self, context: TransformationContext
    ) -> TransformationResult:
        """Apply Dau Definition 16.4 ligature rearrangement.

        Constructs a new identity-edge set F' that realizes the same
        ligature partition as F, with the same vertex set W. Only
        identity edges that sit in the same area as the selected
        vertices are rewired; edges in other areas (notably edges that
        cross into descendant cuts) are preserved as-is, which keeps the
        cut hierarchy unchanged.
        """
        precondition_ok, error_msg = self.check_preconditions(context)
        if not precondition_ok:
            return TransformationResult(False, None, error_msg, {})

        try:
            egi = context.source_egi
            selected_vertices = _canonical_vertex_order(egi, context.selected_subgraph)
            ligature_context = self._get_vertex_context(egi, selected_vertices[0])

            # Find the full ligature containing the selection.
            ligature: FrozenSet[ElementID] = frozenset()
            for component in egi.get_ligatures():
                if selected_vertices[0] in component:
                    ligature = component
                    break
            if not ligature:
                return TransformationResult(
                    False, None, "Selected vertex is not part of any ligature.", {}
                )

            context_area = egi.area.get(ligature_context, frozenset())

            # Local subset of the ligature that sits in the selected area.
            local_vertices = sorted(v for v in ligature if v in context_area)
            if len(local_vertices) < 2:
                return TransformationResult(
                    False, None,
                    "Need at least two ligature vertices in the selected context.",
                    {},
                )

            # Identity edges to be replaced: identity edges whose endpoints are
            # both local and which themselves sit in the selected area.
            local_vertex_set = set(local_vertices)
            old_edges: Set[ElementID] = set()
            for edge_id, vertex_seq in egi.nu.items():
                if (
                    egi.rel.get(edge_id) == "="
                    and len(vertex_seq) == 2
                    and edge_id in context_area
                    and vertex_seq[0] in local_vertex_set
                    and vertex_seq[1] in local_vertex_set
                ):
                    old_edges.add(edge_id)

            # Canonical replacement: a star at the lexically-smallest local
            # vertex. Reversed nu order witnesses an actual structural
            # difference even when |local_vertices| == 2.
            center = local_vertices[0]
            new_edge_pairs: Dict[ElementID, Tuple[ElementID, ElementID]] = {}
            for spoke in local_vertices[1:]:
                new_eid = ElementID(f"id_rearr_{center}_{spoke}")
                new_edge_pairs[new_eid] = (spoke, center)

            new_E = (
                {e for e in egi.E if e.id not in old_edges}
                | {Edge(eid) for eid in new_edge_pairs}
            )
            new_nu = {
                k: v for k, v in egi.nu.items() if k not in old_edges
            }
            new_nu.update(new_edge_pairs)
            new_rel = {
                k: v for k, v in egi.rel.items() if k not in old_edges
            }
            new_rel.update({eid: "=" for eid in new_edge_pairs})

            new_area = dict(egi.area)
            ctx_contents = set(new_area.get(ligature_context, frozenset()))
            ctx_contents -= old_edges
            ctx_contents |= set(new_edge_pairs.keys())
            new_area[ligature_context] = frozenset(ctx_contents)

            result_egi = _rebuild_graph(
                egi,
                E=frozenset(new_E),
                nu=frozendict(new_nu),
                area=frozendict(new_area),
                rel=frozendict(new_rel),
            )

            # Self-check: F' must realize the same partition as F.
            original_partition = frozenset(
                frozenset(c) for c in egi.get_ligatures()
            )
            new_partition = frozenset(
                frozenset(c) for c in result_egi.get_ligatures()
            )
            if new_partition != original_partition:
                return TransformationResult(
                    False, None,
                    "Rearrangement broke the ligature partition.",
                    {},
                )

            return TransformationResult(
                success=True,
                result_egi=result_egi,
                error_message=None,
                changes_made={
                    "rule": "REARRANGE_LIGATURE",
                    "context": str(ligature_context),
                    "removed_identity_edges": sorted(str(e) for e in old_edges),
                    "added_identity_edges": sorted(
                        str(e) for e in new_edge_pairs
                    ),
                },
            )

        except Exception as e:
            return TransformationResult(False, None, str(e), {})

    def _vertices_form_ligature(
        self, egi: RelationalGraphWithCuts, vertices: List[ElementID]
    ) -> bool:
        """Check if vertices form a connected ligature via identity edges."""
        if len(vertices) < 2:
            return False

        # Build graph of identity connections
        identity_graph = {}
        for vertex_id in vertices:
            identity_graph[vertex_id] = set()

        for edge_id, vertex_sequence in egi.nu.items():
            if (
                egi.rel.get(edge_id) == "="
                and len(vertex_sequence) == 2
                and vertex_sequence[0] in vertices
                and vertex_sequence[1] in vertices
            ):
                identity_graph[vertex_sequence[0]].add(vertex_sequence[1])
                identity_graph[vertex_sequence[1]].add(vertex_sequence[0])

        # Check connectivity using DFS
        visited = set()
        stack = [vertices[0]]
        visited.add(vertices[0])

        while stack:
            current = stack.pop()
            for neighbor in identity_graph.get(current, set()):
                if neighbor not in visited:
                    visited.add(neighbor)
                    stack.append(neighbor)

        return len(visited) == len(vertices)

    def _get_vertex_context(
        self, egi: RelationalGraphWithCuts, vertex_id: ElementID
    ) -> ElementID:
        """Get the context (area) containing this vertex."""
        for area_id, contents in egi.area.items():
            if vertex_id in contents:
                return area_id
        return egi.sheet


class LigatureManipulationEngine:
    """Engine for applying ligature manipulation rules from Dau Chapter 16."""

    def __init__(self):
        self.rules = {
            "MOVE_BRANCHES": MoveBranchesAlongLigatureRule(),
            "EXTEND_LIGATURE": ExtendRestrictLigatureRule(),
            "RETRACT_LIGATURE": RetractLigatureRule(),
            "REARRANGE_LIGATURE": LigatureRearrangementRule(),
        }

    def apply_rule(
        self,
        rule_name: str,
        source_egi: RelationalGraphWithCuts,
        target_area: ElementID,
        selected_subgraph: FrozenSet[ElementID],
    ) -> TransformationResult:
        """Apply a ligature manipulation rule to an EGI."""

        if rule_name not in self.rules:
            return TransformationResult(
                success=False,
                result_egi=None,
                error_message=f"Unknown ligature rule: {rule_name}",
                changes_made={},
            )

        rule = self.rules[rule_name]

        # Create transformation context (ligature rules don't depend on polarity)
        from formal_transformation_rules import AreaPolarity, TransformationContext

        context = TransformationContext(
            source_egi=source_egi,
            target_area=target_area,
            selected_subgraph=selected_subgraph,
            area_polarity=AreaPolarity.POSITIVE,  # Not relevant for ligature rules
            nesting_depth=0,  # Not relevant for ligature rules
        )

        # Apply the rule
        return rule.apply_transformation(context)

    def get_available_rules(self) -> List[str]:
        """Get list of available ligature manipulation rules."""
        return list(self.rules.keys())

    def describe_rule(self, rule_name: str) -> str:
        """Get description of a ligature manipulation rule."""
        if rule_name not in self.rules:
            return f"Unknown rule: {rule_name}"

        return self.rules[rule_name].get_rule_name()


def demonstrate_ligature_manipulation():
    """Demonstrate ligature manipulation rules."""

    print("🔗 Ligature Manipulation Rules Demonstration (Dau Chapter 16)")
    print("=" * 60)

    # Create test EGI with ligature
    from egi_core_dau import Edge, ElementID, RelationalGraphWithCuts, Vertex

    # Create vertices connected by identity
    vertex_a = Vertex(ElementID("A"))
    vertex_b = Vertex(ElementID("B"))
    vertex_c = Vertex(ElementID("C"))

    # Create identity edge connecting A and B
    identity_edge = Edge(ElementID("id_AB"))

    test_egi = RelationalGraphWithCuts(
        V=frozenset([vertex_a, vertex_b, vertex_c]),
        E=frozenset([identity_edge]),
        nu=frozendict({ElementID("id_AB"): (ElementID("A"), ElementID("B"))}),
        sheet=ElementID("sheet"),
        Cut=frozenset(),
        area=frozendict(
            {
                ElementID("sheet"): frozenset(
                    [ElementID("A"), ElementID("B"), ElementID("C"), ElementID("id_AB")]
                )
            }
        ),
        rel=frozendict({ElementID("id_AB"): "="}),
    )

    engine = LigatureManipulationEngine()

    print(f"Starting EGI: {len(test_egi.V)} vertices, {len(test_egi.E)} edges")
    print(f"Identity connections: A—B (via identity edge)")
    print()

    # Test ligature extension
    print("🎯 Test 1: Extend Ligature from vertex A")
    result = engine.apply_rule(
        "EXTEND_LIGATURE", test_egi, ElementID("sheet"), frozenset([ElementID("A")])
    )

    if result.success:
        print(f"   ✅ SUCCESS: {result.changes_made}")
        extended_egi = result.result_egi
        print(f"   Result: {len(extended_egi.V)} vertices, {len(extended_egi.E)} edges")
    else:
        print(f"   ❌ FAILED: {result.error_message}")

    print()
    return engine, test_egi


if __name__ == "__main__":
    demonstrate_ligature_manipulation()
