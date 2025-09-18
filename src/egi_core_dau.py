"""
Dau-compliant Existential Graph Instance (EGI) core implementation.
Follows Frithjof Dau's exact 6+1 component definition from "Mathematical Logic with Diagrams".

This implementation replaces the previous "Context" model with Dau's formal:
- 6-component Relational Graph with Cuts: (V, E, ν, ⊤, Cut, area)
- 7th component: rel mapping for relation names
- Proper area/context distinction for diagram generation
- Support for isolated vertices ("heavy dots")
"""

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

from frozendict import frozendict

# Type aliases for clarity
ElementID = str
VertexSequence = Tuple[ElementID, ...]
RelationName = str


@dataclass(frozen=True)
class Vertex:
    """Vertex in Dau's formalism - can be generic (*x) or constant ("Socrates")."""

    id: ElementID
    label: Optional[str] = None  # None for generic, string for constant
    is_generic: bool = True

    def __post_init__(self):
        if self.label is not None and self.is_generic:
            raise ValueError("Constant vertex cannot be generic")
        if self.label is None and not self.is_generic:
            raise ValueError("Generic vertex must have no label")


@dataclass(frozen=True)
class Edge:
    """Edge in Dau's formalism - represents a relation with incident vertices."""

    id: ElementID
    # Note: ν mapping and relation names are handled separately in the main structure


@dataclass(frozen=True)
class Cut:
    """Cut in Dau's formalism - represents negation context."""

    id: ElementID


@dataclass(frozen=True)
class RelationalGraphWithCuts:
    """
    Dau's exact 6+1 component definition of Relational Graph with Cuts.

    Components (Definition 12.1):
    1. V - finite set of vertices
    2. E - finite set of edges
    3. ν - mapping from edges to vertex sequences
    4. ⊤ - sheet of assertion (single element)
    5. Cut - finite set of cuts
    6. area - mapping defining containment
    7. rel - mapping from edges to relation names (7th component)

    Constraints:
    - V, E, Cut are pairwise disjoint
    - ⊤ ∉ V ∪ E ∪ Cut
    - area satisfies all formal constraints from Definition 12.1
    """

    # Core 6 components from Dau's Definition 12.1
    V: FrozenSet[Vertex]  # Component 1: Vertices
    E: FrozenSet[Edge]  # Component 2: Edges
    nu: frozendict[ElementID, VertexSequence]  # Component 3: ν mapping
    sheet: ElementID  # Component 4: ⊤ sheet of assertion
    Cut: FrozenSet[Cut]  # Component 5: Cuts
    area: frozendict[ElementID, FrozenSet[ElementID]]  # Component 6: area mapping

    # 7th component for relation names
    rel: frozendict[ElementID, RelationName]  # Component 7: relation mapping

    # Optional Dau Alphabet (C, F, R, ar) and rho mapping for constants-on-vertices
    # These are optional to maintain backward compatibility. If provided (non-empty),
    # additional validations will be enforced.
    alphabet: Optional["AlphabetDAU"] = None
    rho: frozendict[ElementID, Optional[str]] = (
        frozendict()
    )  # vertex_id -> constant name or None
    
    # Variable name mapping for preserving semantic names across translations
    # Maps vertex_id -> variable name (e.g., "x", "y", "z") for generic vertices
    variable_names: frozendict[ElementID, str] = frozendict()

    # Hierarchical index for efficient nesting operations
    # This is integral to EGI logic, not just spatial representation
    hierarchical_index: Optional["HierarchicalIndex"] = None

    # Derived mappings for efficiency
    _vertex_map: frozendict[ElementID, Vertex] = None
    _edge_map: frozendict[ElementID, Edge] = None
    _cut_map: frozendict[ElementID, Cut] = None

    def __post_init__(self):
        """Validate Dau's formal constraints and build derived mappings."""
        # Build derived mappings
        vertex_map = {v.id: v for v in self.V}
        edge_map = {e.id: e for e in self.E}
        cut_map = {c.id: c for c in self.Cut}

        object.__setattr__(self, "_vertex_map", frozendict(vertex_map))
        object.__setattr__(self, "_edge_map", frozendict(edge_map))
        object.__setattr__(self, "_cut_map", frozendict(cut_map))

        # Initialize hierarchical index if not provided
        if object.__getattribute__(self, "hierarchical_index") is None:
            from hierarchical_index import HierarchicalIndex

            hierarchical_index = HierarchicalIndex()

            # Add sheet first
            hierarchical_index.add_area(self.sheet)

            # Add all cut areas with proper nesting
            # This requires analyzing the area mapping to determine parent-child relationships
            self._build_hierarchical_index(hierarchical_index)

            object.__setattr__(self, "hierarchical_index", hierarchical_index)

        # Validate Dau's constraints
        self._validate_dau_constraints()
        # Validate optional AlphabetDAU / rho if present
        self._validate_alphabet_and_rho()

    def _build_hierarchical_index(self, hierarchical_index):
        """Build hierarchical index from area mapping."""
        # Find containment relationships from area mapping
        # area[parent] contains child means child is nested in parent

        # Build parent-child relationships
        child_to_parent = {}
        for parent_area, contents in self.area.items():
            for element_id in contents:
                if element_id in {c.id for c in self.Cut}:
                    # This element is a cut, so it's a child area
                    child_to_parent[element_id] = parent_area

        # Add areas in order: sheet first, then by nesting level
        added_areas = {self.sheet}

        # Keep adding areas until all cuts are processed
        remaining_cuts = {c.id for c in self.Cut}

        while remaining_cuts:
            # Find cuts whose parents are already added
            ready_to_add = []
            for cut_id in remaining_cuts:
                parent = child_to_parent.get(cut_id, self.sheet)
                if parent in added_areas:
                    ready_to_add.append((cut_id, parent))

            if not ready_to_add:
                # This shouldn't happen with valid area mappings
                break

            # Add the ready cuts
            for cut_id, parent in ready_to_add:
                hierarchical_index.add_area(cut_id, parent)
                added_areas.add(cut_id)
                remaining_cuts.remove(cut_id)

    def _validate_dau_constraints(self):
        """Validate all constraints from Dau's Definition 12.1."""

        # Constraint: V, E, Cut are pairwise disjoint
        v_ids = {v.id for v in self.V}
        e_ids = {e.id for e in self.E}
        c_ids = {c.id for c in self.Cut}

        if v_ids & e_ids:
            raise ValueError("V and E must be disjoint")
        if v_ids & c_ids:
            raise ValueError("V and Cut must be disjoint")
        if e_ids & c_ids:
            raise ValueError("E and Cut must be disjoint")

        # Constraint: ⊤ ∉ V ∪ E ∪ Cut
        all_element_ids = v_ids | e_ids | c_ids
        if self.sheet in all_element_ids:
            raise ValueError("Sheet of assertion must not be in V ∪ E ∪ Cut")

        # Constraint: ν maps edges to vertex sequences
        for edge_id, vertex_seq in self.nu.items():
            if edge_id not in e_ids:
                raise ValueError(f"ν maps non-edge {edge_id}")
            for vertex_id in vertex_seq:
                if vertex_id not in v_ids:
                    raise ValueError(f"ν maps edge {edge_id} to non-vertex {vertex_id}")

        # All edges must have ν mapping
        for edge_id in e_ids:
            if edge_id not in self.nu:
                raise ValueError(f"Edge {edge_id} missing ν mapping")

        # Constraint: rel maps edges to relation names
        for edge_id in e_ids:
            if edge_id not in self.rel:
                raise ValueError(f"Edge {edge_id} missing relation name mapping")

        # Constraint: area mapping constraints
        self._validate_area_constraints()

    def _validate_area_constraints(self):
        """Validate area mapping constraints from Definition 12.1."""
        all_contexts = set(self.Cut) | {self.sheet}
        all_elements = (
            {v.id for v in self.V} | {e.id for e in self.E} | {c.id for c in self.Cut}
        )

        # Constraint a) c₁ ≠ c₂ ⇒ area(c₁) ∩ area(c₂) = ∅
        context_ids = [c.id for c in self.Cut] + [self.sheet]
        for i, c1 in enumerate(context_ids):
            for c2 in context_ids[i + 1 :]:
                area1 = self.area.get(c1, frozenset())
                area2 = self.area.get(c2, frozenset())
                if area1 & area2:
                    raise ValueError(f"Areas of {c1} and {c2} must be disjoint")

        # Constraint b) V ∪ E ∪ Cut = ⋃ area(d)
        all_in_areas = set()
        for context_id in context_ids:
            all_in_areas |= self.area.get(context_id, frozenset())

        if all_elements != all_in_areas:
            missing = all_elements - all_in_areas
            extra = all_in_areas - all_elements
            raise ValueError(
                f"Area coverage mismatch. Missing: {missing}, Extra: {extra}"
            )

        # Constraint c) c ∉ area^n(c) for each c ∈ Cut ∪ {⊤} and n ∈ ℕ
        # This prevents cycles in the area containment
        for context_id in context_ids:
            if self._has_area_cycle(context_id):
                raise ValueError(f"Context {context_id} has area containment cycle")

    def _has_area_cycle(
        self, start_context: ElementID, visited: Optional[Set[ElementID]] = None
    ) -> bool:
        """Check if context has cycle in area containment."""
        if visited is None:
            visited = set()

        if start_context in visited:
            return True

        visited.add(start_context)

        # Check all cuts in this context's area
        for element_id in self.area.get(start_context, frozenset()):
            if element_id in self._cut_map:
                if self._has_area_cycle(element_id, visited.copy()):
                    return True

        return False

    def _validate_alphabet_and_rho(self):
        """If an AlphabetDAU is provided, validate arities, membership, and rho labels.
        This keeps the core backward compatible by making these checks conditional.
        """
        if self.alphabet is None:
            return
        alph = self.alphabet
        # Ensure ar(c)==1 for all c in C
        for c in alph.C:
            if alph.ar.get(c, 1) != 1:
                raise ValueError(
                    f"Alphabet arity for constant '{c}' must be 1, got {alph.ar.get(c)}"
                )
        # All rel names used by edges must be declared in C ∪ F ∪ R
        declared = alph.C | alph.F | alph.R
        for edge_id, name in self.rel.items():
            if name not in declared:
                raise ValueError(
                    f"Relation name '{name}' (edge {edge_id}) not in Alphabet (C∪F∪R)"
                )
            # If arity is known, enforce |ν(e)| == ar(name)
            if name in alph.ar:
                expected = alph.ar[name]
                got = len(self.nu.get(edge_id, tuple()))
                if got != expected:
                    raise ValueError(
                        f"Arity mismatch for '{name}': expected {expected}, got {got} (edge {edge_id})"
                    )
        # Validate rho: vertex ids must exist; labels must be constants in C or None
        for vid, const_name in self.rho.items():
            if vid not in self._vertex_map:
                raise ValueError(f"rho refers to unknown vertex '{vid}'")
            if const_name is not None and const_name not in alph.C:
                raise ValueError(
                    f"rho assigns '{const_name}' to {vid}, but it is not in Alphabet.C"
                )

    # Core access methods

    def get_vertex(self, vertex_id: ElementID) -> Vertex:
        """Get vertex by ID."""
        if vertex_id not in self._vertex_map:
            raise ValueError(f"Vertex {vertex_id} not found")
        return self._vertex_map[vertex_id]

    def get_edge(self, edge_id: ElementID) -> Edge:
        """Get edge by ID."""
        if edge_id not in self._edge_map:
            raise ValueError(f"Edge {edge_id} not found")
        return self._edge_map[edge_id]

    def get_cut(self, cut_id: ElementID) -> Cut:
        """Get cut by ID."""
        if cut_id not in self._cut_map:
            raise ValueError(f"Cut {cut_id} not found")
        return self._cut_map[cut_id]

    def get_relation_name(self, edge_id: ElementID) -> RelationName:
        """Get relation name for edge."""
        if edge_id not in self.rel:
            raise ValueError(f"Edge {edge_id} has no relation name")
        return self.rel[edge_id]

    def get_incident_vertices(self, edge_id: ElementID) -> VertexSequence:
        """Get incident vertices for edge via ν mapping."""
        if edge_id not in self.nu:
            raise ValueError(f"Edge {edge_id} has no ν mapping")
        return self.nu[edge_id]

    # Area and context methods (Dau's critical distinction)

    def get_area(self, context_id: ElementID) -> FrozenSet[ElementID]:
        """Get area of context - direct contents only (non-recursive)."""
        return self.area.get(context_id, frozenset())

    def get_context(self, element_id: ElementID) -> ElementID:
        """Get the context that directly contains this element."""
        for context_id, area_elements in self.area.items():
            if element_id in area_elements:
                return context_id
        raise ValueError(f"Element {element_id} not found in any context")

    def get_full_context(self, context_id: ElementID) -> FrozenSet[ElementID]:
        """
        Get full context of a cut - all elements it contributes to SoA (recursive).
        This is Dau's context concept: ⋃ area^n(c) for all n.
        """
        result = set()
        to_process = {context_id}

        while to_process:
            current = to_process.pop()
            current_area = self.area.get(current, frozenset())

            for element_id in current_area:
                if element_id not in result:
                    result.add(element_id)
                    # If element is a cut, add its area to processing
                    if element_id in self._cut_map:
                        to_process.add(element_id)

        return frozenset(result)

    def get_nesting_depth(self, element_id: ElementID) -> int:
        """Get nesting depth of element (number of cuts enclosing it)."""
        depth = 0
        current_context = self.get_context(element_id)

        while current_context != self.sheet:
            depth += 1
            current_context = self.get_context(current_context)

        return depth

    def is_evenly_enclosed(self, element_id: ElementID) -> bool:
        """Check if element is evenly enclosed (Dau's Definition 12.4)."""
        return self.get_nesting_depth(element_id) % 2 == 0

    def is_oddly_enclosed(self, element_id: ElementID) -> bool:
        """Check if element is oddly enclosed (Dau's Definition 12.4)."""
        return self.get_nesting_depth(element_id) % 2 == 1

    def is_positive_context(self, context_id: ElementID) -> bool:
        """Check if context is positive (sheet or oddly enclosed cut)."""
        if context_id == self.sheet:
            return True
        return self.is_oddly_enclosed(context_id)

    def is_negative_context(self, context_id: ElementID) -> bool:
        """Check if context is negative (evenly enclosed cut)."""
        return not self.is_positive_context(context_id)

    # Hook operations (Definition 12.9)

    def get_hooks(self, edge_id: ElementID) -> List[Tuple[ElementID, int]]:
        """Get all hooks for an edge as (edge_id, position) pairs."""
        if edge_id not in self.nu:
            raise ValueError(f"Edge {edge_id} not found")
        vertex_seq = self.nu[edge_id]
        return [
            (edge_id, i + 1) for i in range(len(vertex_seq))
        ]  # 1-indexed as per Dau

    def get_vertex_at_hook(self, edge_id: ElementID, position: int) -> ElementID:
        """Get vertex attached to hook (edge_id, position)."""
        if edge_id not in self.nu:
            raise ValueError(f"Edge {edge_id} not found")
        vertex_seq = self.nu[edge_id]
        if position < 1 or position > len(vertex_seq):
            raise ValueError(f"Invalid hook position {position} for edge {edge_id}")
        return vertex_seq[position - 1]  # Convert to 0-indexed

    def get_vertex_hooks(self, vertex_id: ElementID) -> List[Tuple[ElementID, int]]:
        """Get all hooks that vertex is attached to."""
        hooks = []
        for edge_id, vertex_seq in self.nu.items():
            for i, vid in enumerate(vertex_seq):
                if vid == vertex_id:
                    hooks.append((edge_id, i + 1))  # 1-indexed
        return hooks

    def is_branching_point(self, vertex_id: ElementID) -> bool:
        """Check if vertex is a branching point (attached to more than 2 hooks)."""
        return len(self.get_vertex_hooks(vertex_id)) > 2

    def get_branch_count(self, vertex_id: ElementID) -> int:
        """Get number of branches (hooks) for vertex."""
        return len(self.get_vertex_hooks(vertex_id))
    
    def get_all_elements(self) -> FrozenSet[ElementID]:
        """Get all element IDs in the EGI (vertices, edges, cuts)."""
        vertex_ids = {v.id for v in self.V}
        edge_ids = {e.id for e in self.E}
        cut_ids = {c.id for c in self.Cut}
        return frozenset(vertex_ids | edge_ids | cut_ids)

    def replace_vertex_on_hook(
        self, edge_id: ElementID, position: int, new_vertex_id: ElementID
    ) -> "RelationalGraphWithCuts":
        """Replace vertex on hook (edge_id, position) with new vertex (Definition 12.9)."""
        if edge_id not in self.nu:
            raise ValueError(f"Edge {edge_id} not found")
        if new_vertex_id not in {v.id for v in self.V}:
            raise ValueError(f"New vertex {new_vertex_id} not found")

        vertex_seq = list(self.nu[edge_id])
        if position < 1 or position > len(vertex_seq):
            raise ValueError(f"Invalid hook position {position}")

        # Check dominating nodes constraint
        edge_context = self.get_context(edge_id)
        new_vertex_context = self.get_context(new_vertex_id)
        if not self._context_dominates(edge_context, new_vertex_context):
            raise ValueError(
                f"Dominating nodes constraint violated: ctx({edge_id}) ≰ ctx({new_vertex_id})"
            )

        vertex_seq[position - 1] = new_vertex_id
        new_nu = dict(self.nu)
        new_nu[edge_id] = tuple(vertex_seq)

        return RelationalGraphWithCuts(
            V=self.V,
            E=self.E,
            nu=frozendict(new_nu),
            sheet=self.sheet,
            Cut=self.Cut,
            area=self.area,
            rel=self.rel,
            alphabet=self.alphabet,
            rho=self.rho,
        )

    # Ligature operations (Definition 12.8)

    def get_identity_edges(self) -> FrozenSet[ElementID]:
        """Get all identity edges (edges with relation name '=')."""
        return frozenset(
            edge_id for edge_id, rel_name in self.rel.items() if rel_name == "="
        )

    def get_ligature_graph(
        self,
    ) -> Tuple[FrozenSet[ElementID], FrozenSet[Tuple[ElementID, ElementID]]]:
        """Get ligature graph (V, Eid) as vertex set and edge pairs."""
        identity_edges = self.get_identity_edges()
        edge_pairs = set()

        for edge_id in identity_edges:
            vertex_seq = self.nu[edge_id]
            if len(vertex_seq) == 2:
                # Use unordered representation as Dau suggests: e = {v1, v2}
                v1, v2 = vertex_seq
                edge_pairs.add((min(v1, v2), max(v1, v2)))  # Canonical ordering

        vertex_ids = {v.id for v in self.V}
        return vertex_ids, frozenset(edge_pairs)

    def get_identity_edge_as_set(self, edge_id: ElementID) -> FrozenSet[ElementID]:
        """Get identity edge as unordered set {v1, v2} per Dau's suggestion."""
        if edge_id not in self.get_identity_edges():
            raise ValueError(f"Edge {edge_id} is not an identity edge")

        vertex_seq = self.nu[edge_id]
        if len(vertex_seq) != 2:
            raise ValueError(f"Identity edge {edge_id} must be binary")

        return frozenset(vertex_seq)

    def get_ligatures(self) -> List[FrozenSet[ElementID]]:
        """Get all ligatures as connected components of identity edges."""
        vertex_ids, edge_pairs = self.get_ligature_graph()

        # Build adjacency list
        adjacency = {vid: set() for vid in vertex_ids}
        for v1, v2 in edge_pairs:
            adjacency[v1].add(v2)
            adjacency[v2].add(v1)

        # Find connected components using DFS
        visited = set()
        ligatures = []

        for vertex_id in vertex_ids:
            if vertex_id not in visited:
                component = set()
                stack = [vertex_id]

                while stack:
                    current = stack.pop()
                    if current not in visited:
                        visited.add(current)
                        component.add(current)
                        stack.extend(adjacency[current] - visited)

                ligatures.append(frozenset(component))

        return ligatures

    def get_vertex_ligature(self, vertex_id: ElementID) -> FrozenSet[ElementID]:
        """Get the ligature containing the specified vertex."""
        ligatures = self.get_ligatures()
        for ligature in ligatures:
            if vertex_id in ligature:
                return ligature
        return frozenset({vertex_id})  # Isolated vertex is its own ligature

    # Utility methods

    def is_vertex_isolated(self, vertex_id: ElementID) -> bool:
        """Check if vertex is isolated (not incident to any edge)."""
        for edge_id, vertex_seq in self.nu.items():
            if vertex_id in vertex_seq:
                return False
        return True

    def get_isolated_vertices(self) -> FrozenSet[ElementID]:
        """Get all isolated vertices."""
        isolated = set()
        for vertex in self.V:
            if self.is_vertex_isolated(vertex.id):
                isolated.add(vertex.id)
        return frozenset(isolated)

    def has_dominating_nodes(self) -> bool:
        """Check if graph has dominating nodes (Dau's Definition 12.5)."""
        for edge_id, vertex_seq in self.nu.items():
            edge_context = self.get_context(edge_id)
            for vertex_id in vertex_seq:
                vertex_context = self.get_context(vertex_id)
                # Check if ctx(e) ≤ ctx(v) (edge context dominates vertex context)
                if not self._context_dominates(edge_context, vertex_context):
                    return False
        return True

    def _context_dominates(self, context1: ElementID, context2: ElementID) -> bool:
        """Check if context1 ≤ context2 in Dau's ordering."""
        if context1 == context2:
            return True

        # Check if context1 is in area^n(context2) for some n
        current = context2
        while current != self.sheet:
            if context1 == current:
                return True
            current = self.get_context(current)

        return context1 == self.sheet

    # Creation methods

    def with_vertex(self, vertex: Vertex) -> "RelationalGraphWithCuts":
        """Create new graph with additional vertex in sheet of assertion."""
        return self.with_vertex_in_context(vertex, self.sheet)

    def with_vertex_in_context(
        self, vertex: Vertex, context_id: ElementID
    ) -> "RelationalGraphWithCuts":
        """Create new graph with additional vertex in specified context."""
        if vertex.id in {v.id for v in self.V}:
            raise ValueError(f"Vertex {vertex.id} already exists")

        # Validate context exists
        if context_id != self.sheet and context_id not in {c.id for c in self.Cut}:
            raise ValueError(f"Context {context_id} does not exist")

        new_V = self.V | {vertex}
        new_area = dict(self.area)
        context_area = new_area.get(context_id, frozenset())
        new_area[context_id] = context_area | {vertex.id}

        return RelationalGraphWithCuts(
            V=new_V,
            E=self.E,
            nu=self.nu,
            sheet=self.sheet,
            Cut=self.Cut,
            area=frozendict(new_area),
            rel=self.rel,
            alphabet=self.alphabet,
            rho=self.rho,
        )

    def with_edge(
        self,
        edge: Edge,
        vertex_sequence: VertexSequence,
        relation_name: RelationName,
        context_id: ElementID = None,
    ) -> "RelationalGraphWithCuts":
        """Create new graph with additional edge."""
        if edge.id in {e.id for e in self.E}:
            raise ValueError(f"Edge {edge.id} already exists")

        # Validate vertex sequence
        for vertex_id in vertex_sequence:
            if vertex_id not in {v.id for v in self.V}:
                raise ValueError(f"Vertex {vertex_id} not found")

        if context_id is None:
            context_id = self.sheet

        new_E = self.E | {edge}
        new_nu = dict(self.nu)
        new_nu[edge.id] = vertex_sequence
        new_rel = dict(self.rel)
        new_rel[edge.id] = relation_name
        new_area = dict(self.area)
        context_area = new_area.get(context_id, frozenset())
        new_area[context_id] = context_area | {edge.id}

        return RelationalGraphWithCuts(
            V=self.V,
            E=new_E,
            nu=frozendict(new_nu),
            sheet=self.sheet,
            Cut=self.Cut,
            area=frozendict(new_area),
            rel=frozendict(new_rel),
            alphabet=self.alphabet,
            rho=self.rho,
        )

    # Transformation Rules (Definition 12.14)

    def apply_isomorphism(
        self,
        vertex_mapping: Dict[ElementID, ElementID],
        edge_mapping: Dict[ElementID, ElementID],
        cut_mapping: Dict[ElementID, ElementID],
    ) -> "RelationalGraphWithCuts":
        """Apply isomorphism transformation (Definition 12.14)."""
        # Create new vertices with mapped IDs
        new_vertices = set()
        for v in self.V:
            new_id = vertex_mapping.get(v.id, v.id)
            new_vertices.add(Vertex(id=new_id, label=v.label, is_generic=v.is_generic))

        # Create new edges with mapped IDs
        new_edges = set()
        for e in self.E:
            new_id = edge_mapping.get(e.id, e.id)
            new_edges.add(Edge(id=new_id))

        # Create new cuts with mapped IDs
        new_cuts = set()
        for c in self.Cut:
            new_id = cut_mapping.get(c.id, c.id)
            new_cuts.add(Cut(id=new_id))

        # Map ν function
        new_nu = {}
        for edge_id, vertex_seq in self.nu.items():
            new_edge_id = edge_mapping.get(edge_id, edge_id)
            new_vertex_seq = tuple(vertex_mapping.get(vid, vid) for vid in vertex_seq)
            new_nu[new_edge_id] = new_vertex_seq

        # Map area function
        new_area = {}
        sheet_mapped = (
            cut_mapping.get(self.sheet, self.sheet)
            if self.sheet in cut_mapping
            else self.sheet
        )
        for context_id, elements in self.area.items():
            new_context_id = (
                cut_mapping.get(context_id, context_id)
                if context_id != self.sheet
                else sheet_mapped
            )
            new_elements = set()
            for elem_id in elements:
                if elem_id in vertex_mapping:
                    new_elements.add(vertex_mapping[elem_id])
                elif elem_id in edge_mapping:
                    new_elements.add(edge_mapping[elem_id])
                elif elem_id in cut_mapping:
                    new_elements.add(cut_mapping[elem_id])
                else:
                    new_elements.add(elem_id)
            new_area[new_context_id] = frozenset(new_elements)

        # Map rel function
        new_rel = {}
        for edge_id, rel_name in self.rel.items():
            new_edge_id = edge_mapping.get(edge_id, edge_id)
            new_rel[new_edge_id] = rel_name

        # Map rho function
        new_rho = {}
        for vertex_id, const_name in self.rho.items():
            new_vertex_id = vertex_mapping.get(vertex_id, vertex_id)
            new_rho[new_vertex_id] = const_name

        return RelationalGraphWithCuts(
            V=frozenset(new_vertices),
            E=frozenset(new_edges),
            nu=frozendict(new_nu),
            sheet=sheet_mapped,
            Cut=frozenset(new_cuts),
            area=frozendict(new_area),
            rel=frozendict(new_rel),
            alphabet=self.alphabet,
            rho=frozendict(new_rho),
        )

    def change_identity_edge_orientation(
        self, edge_id: ElementID
    ) -> "RelationalGraphWithCuts":
        """Change orientation of identity edge (Definition 12.14)."""
        if edge_id not in self.rel or self.rel[edge_id] != "=":
            raise ValueError(f"Edge {edge_id} is not an identity edge")

        vertex_seq = self.nu[edge_id]
        if len(vertex_seq) != 2:
            raise ValueError(f"Identity edge {edge_id} must be binary")

        # Reverse the vertex sequence
        new_vertex_seq = (vertex_seq[1], vertex_seq[0])
        new_nu = dict(self.nu)
        new_nu[edge_id] = new_vertex_seq

        return RelationalGraphWithCuts(
            V=self.V,
            E=self.E,
            nu=frozendict(new_nu),
            sheet=self.sheet,
            Cut=self.Cut,
            area=self.area,
            rel=self.rel,
            alphabet=self.alphabet,
            rho=self.rho,
        )

    def add_vertex_to_ligature(
        self,
        edge_id: ElementID,
        hook_position: int,
        new_vertex: Vertex,
        context_id: ElementID,
    ) -> "RelationalGraphWithCuts":
        """Add vertex to ligature (Definition 12.14)."""
        if edge_id not in self.nu:
            raise ValueError(f"Edge {edge_id} not found")

        vertex_seq = self.nu[edge_id]
        if hook_position < 1 or hook_position > len(vertex_seq):
            raise ValueError(f"Invalid hook position {hook_position}")

        old_vertex_id = vertex_seq[hook_position - 1]

        # Validate context constraint: ctx(old_vertex) ≥ context ≥ ctx(edge)
        old_vertex_context = self.get_context(old_vertex_id)
        edge_context = self.get_context(edge_id)
        if not (
            self._context_dominates(context_id, old_vertex_context)
            and self._context_dominates(edge_context, context_id)
        ):
            raise ValueError("Context constraint violated for ligature transformation")

        # Add new vertex to specified context
        graph_with_vertex = self.with_vertex_in_context(new_vertex, context_id)

        # Create new identity edge between old vertex and new vertex
        import uuid

        identity_edge = Edge(id=f"id_edge_{uuid.uuid4().hex[:8]}")
        graph_with_identity = graph_with_vertex.with_edge(
            identity_edge, (old_vertex_id, new_vertex.id), "=", context_id
        )

        # Replace old vertex with new vertex on the hook
        return graph_with_identity.replace_vertex_on_hook(
            edge_id, hook_position, new_vertex.id
        )

    def remove_vertex_from_ligature(
        self, vertex_id: ElementID
    ) -> "RelationalGraphWithCuts":
        """Remove vertex from ligature (reverse of add_vertex_to_ligature)."""
        # Find identity edges connected to this vertex
        identity_edges = []
        for edge_id in self.get_identity_edges():
            vertex_seq = self.nu[edge_id]
            if vertex_id in vertex_seq:
                identity_edges.append(edge_id)

        if len(identity_edges) != 1:
            raise ValueError(
                f"Vertex {vertex_id} must be connected to exactly one identity edge for removal"
            )

        identity_edge_id = identity_edges[0]
        vertex_seq = self.nu[identity_edge_id]
        other_vertex_id = vertex_seq[1] if vertex_seq[0] == vertex_id else vertex_seq[0]

        # Find all non-identity edges connected to vertex_id and redirect to other_vertex_id
        new_nu = dict(self.nu)
        for edge_id, seq in self.nu.items():
            if edge_id != identity_edge_id:  # Skip the identity edge we're removing
                new_seq = tuple(
                    other_vertex_id if vid == vertex_id else vid for vid in seq
                )
                if new_seq != seq:
                    new_nu[edge_id] = new_seq

        # Remove the identity edge
        del new_nu[identity_edge_id]

        # Remove vertex and identity edge from areas
        new_area = {}
        for context_id, elements in self.area.items():
            new_elements = elements - {vertex_id, identity_edge_id}
            new_area[context_id] = new_elements

        # Remove from other mappings
        new_rel = {
            eid: name for eid, name in self.rel.items() if eid != identity_edge_id
        }
        new_rho = {vid: name for vid, name in self.rho.items() if vid != vertex_id}

        return RelationalGraphWithCuts(
            V=frozenset(v for v in self.V if v.id != vertex_id),
            E=frozenset(e for e in self.E if e.id != identity_edge_id),
            nu=frozendict(new_nu),
            sheet=self.sheet,
            Cut=self.Cut,
            area=frozendict(new_area),
            rel=frozendict(new_rel),
            alphabet=self.alphabet,
            rho=frozendict(new_rho),
        )

    def with_cut(
        self, cut: Cut, context_id: ElementID = None
    ) -> "RelationalGraphWithCuts":
        """Create new graph with additional cut."""
        if cut.id in {c.id for c in self.Cut}:
            raise ValueError(f"Cut {cut.id} already exists")

        if context_id is None:
            context_id = self.sheet

        new_Cut = self.Cut | {cut}
        new_area = dict(self.area)
        # Add cut to parent context
        parent_area = new_area.get(context_id, frozenset())
        new_area[context_id] = parent_area | {cut.id}
        # Initialize empty area for new cut
        new_area[cut.id] = frozenset()

        return RelationalGraphWithCuts(
            V=self.V,
            E=self.E,
            nu=self.nu,
            sheet=self.sheet,
            Cut=new_Cut,
            area=frozendict(new_area),
            rel=self.rel,
            alphabet=self.alphabet,
            rho=self.rho,
        )

    def with_vertex_moved_to_context(
        self, vertex_id: ElementID, new_context_id: ElementID
    ) -> "RelationalGraphWithCuts":
        """Return a new graph with the given vertex relocated to a different context.
        Preserves all other components; validates that vertex exists and context exists.
        """
        # Validate vertex exists
        if vertex_id not in {v.id for v in self.V}:
            raise ValueError(f"Vertex {vertex_id} not found")
        # Validate target context exists
        if new_context_id != self.sheet and new_context_id not in {
            c.id for c in self.Cut
        }:
            raise ValueError(f"Context {new_context_id} does not exist")
        # If already in target context, return self
        current_context = self.get_context(vertex_id)
        if current_context == new_context_id:
            return self
        # Update area: remove from old, add to new
        new_area = dict(self.area)
        # Remove from current context
        current_area = new_area.get(current_context, frozenset())
        if vertex_id in current_area:
            new_area[current_context] = current_area - {vertex_id}
        # Add to new context
        target_area = new_area.get(new_context_id, frozenset())
        new_area[new_context_id] = target_area | {vertex_id}
        return RelationalGraphWithCuts(
            V=self.V,
            E=self.E,
            nu=self.nu,
            sheet=self.sheet,
            Cut=self.Cut,
            area=frozendict(new_area),
            rel=self.rel,
            alphabet=self.alphabet,
            rho=self.rho,
        )

    def without_element(self, element_id: ElementID) -> "RelationalGraphWithCuts":
        """Create new graph without specified element."""
        if element_id in {v.id for v in self.V}:
            return self._without_vertex(element_id)
        elif element_id in {e.id for e in self.E}:
            return self._without_edge(element_id)
        elif element_id in {c.id for c in self.Cut}:
            return self._without_cut(element_id)
        else:
            raise ValueError(f"Element {element_id} not found")

    def _without_vertex(self, vertex_id: ElementID) -> "RelationalGraphWithCuts":
        """Remove vertex and update area mappings."""
        new_V = frozenset(v for v in self.V if v.id != vertex_id)
        new_area = dict(self.area)

        # Remove vertex from its context's area
        for context_id, area_elements in new_area.items():
            if vertex_id in area_elements:
                new_area[context_id] = area_elements - {vertex_id}

        return RelationalGraphWithCuts(
            V=new_V,
            E=self.E,
            nu=self.nu,
            sheet=self.sheet,
            Cut=self.Cut,
            area=frozendict(new_area),
            rel=self.rel,
            alphabet=self.alphabet,
            rho=self.rho,
        )

    def _without_edge(self, edge_id: ElementID) -> "RelationalGraphWithCuts":
        """Remove edge and update mappings."""
        new_E = frozenset(e for e in self.E if e.id != edge_id)
        new_nu = frozendict({k: v for k, v in self.nu.items() if k != edge_id})
        new_rel = frozendict({k: v for k, v in self.rel.items() if k != edge_id})
        new_area = dict(self.area)

        # Remove edge from its context's area
        for context_id, area_elements in new_area.items():
            if edge_id in area_elements:
                new_area[context_id] = area_elements - {edge_id}

        return RelationalGraphWithCuts(
            V=self.V,
            E=new_E,
            nu=new_nu,
            sheet=self.sheet,
            Cut=self.Cut,
            area=frozendict(new_area),
            rel=new_rel,
            alphabet=self.alphabet,
            rho=self.rho,
        )

    def _without_cut(self, cut_id: ElementID) -> "RelationalGraphWithCuts":
        """Remove cut and redistribute its contents."""
        if cut_id not in {c.id for c in self.Cut}:
            raise ValueError(f"Cut {cut_id} not found")

        # Get parent context and cut's contents
        parent_context = self.get_context(cut_id)
        cut_contents = self.area.get(cut_id, frozenset())

        new_Cut = frozenset(c for c in self.Cut if c.id != cut_id)
        new_area = dict(self.area)

        # Remove cut from parent's area
        parent_area = new_area[parent_context]
        new_area[parent_context] = (parent_area - {cut_id}) | cut_contents

        # Remove cut's area mapping
        del new_area[cut_id]

        return RelationalGraphWithCuts(
            V=self.V,
            E=self.E,
            nu=self.nu,
            sheet=self.sheet,
            Cut=new_Cut,
            area=frozendict(new_area),
            rel=self.rel,
            alphabet=self.alphabet,
            rho=self.rho,
        )


def create_empty_graph() -> RelationalGraphWithCuts:
    """Create empty graph (Dau's G_∅)."""
    sheet_id = f"sheet_{uuid.uuid4().hex[:8]}"

    return RelationalGraphWithCuts(
        V=frozenset(),
        E=frozenset(),
        nu=frozendict(),
        sheet=sheet_id,
        Cut=frozenset(),
        area=frozendict({sheet_id: frozenset()}),
        rel=frozendict(),
        alphabet=None,
        rho=frozendict(),
    )


def create_vertex(label: Optional[str] = None, is_generic: bool = True) -> Vertex:
    """Create new vertex with unique ID."""
    vertex_id = f"v_{uuid.uuid4().hex[:8]}"
    return Vertex(id=vertex_id, label=label, is_generic=is_generic)


def create_edge() -> Edge:
    """Create new edge with unique ID."""
    edge_id = f"e_{uuid.uuid4().hex[:8]}"
    return Edge(id=edge_id)


def create_cut() -> Cut:
    """Create new cut with unique ID."""
    cut_id = f"c_{uuid.uuid4().hex[:8]}"
    return Cut(id=cut_id)


# Alphabet for variable naming
class Alphabet:
    """Manages variable naming for EGIF generation."""

    def __init__(self):
        self.used_names = set()
        self.counter = 0

    def get_fresh_name(self) -> str:
        """Get fresh variable name."""
        while True:
            if self.counter < 3:  # Only use x, y, z
                name = chr(ord("x") + self.counter)
            else:
                # After z, use x1, x2, x3, etc.
                name = f"x{self.counter - 2}"

            if name not in self.used_names:
                self.used_names.add(name)
                self.counter += 1
                return name

            self.counter += 1

    def reserve_name(self, name: str):
        """Reserve a variable name."""
        self.used_names.add(name)


@dataclass(frozen=True)
class AlphabetDAU:
    """Dau's Alphabet (C, F, R, ar). Use with RelationalGraphWithCuts to enable
    arity and membership validations. Set ar(c)=1 implicitly for c∈C unless provided.
    """

    C: FrozenSet[str] = frozenset()
    F: FrozenSet[str] = frozenset()
    R: FrozenSet[str] = frozenset()
    ar: frozendict[str, int] = frozendict()

    def with_defaults(self) -> "AlphabetDAU":
        """Return a copy where all constants have arity 1 in ar if not already set."""
        updated = dict(self.ar)
        for c in self.C:
            if c not in updated:
                updated[c] = 1
        return AlphabetDAU(C=self.C, F=self.F, R=self.R, ar=frozendict(updated))


if __name__ == "__main__":
    # Test the Dau-compliant implementation
    print("=== Testing Dau-Compliant 6+1 Component Model ===")

    # Create empty graph
    graph = create_empty_graph()
    print(
        f"✓ Empty graph created: {len(graph.V)} vertices, {len(graph.E)} edges, {len(graph.Cut)} cuts"
    )

    # Add isolated vertex (heavy dot)
    vertex = create_vertex(label=None, is_generic=True)  # Generic vertex has no label
    graph = graph.with_vertex(vertex)
    print(f"✓ Added isolated vertex: {vertex.id}")
    print(f"  Is isolated: {graph.is_vertex_isolated(vertex.id)}")

    # Add relation
    edge = create_edge()
    vertex2 = create_vertex(label="Socrates", is_generic=False)  # Constant vertex
    graph = graph.with_vertex(vertex2)
    graph = graph.with_edge(edge, (vertex.id, vertex2.id), "loves")
    print(f"✓ Added relation 'loves' between {vertex.id} and {vertex2.id}")

    # Add cut
    cut = create_cut()
    graph = graph.with_cut(cut)
    print(f"✓ Added cut: {cut.id}")

    # Test area vs context distinction
    sheet_area = graph.get_area(graph.sheet)
    sheet_context = graph.get_full_context(graph.sheet)
    print(f"✓ Sheet area: {len(sheet_area)} elements")
    print(f"✓ Sheet context: {len(sheet_context)} elements")

    # Test constraints
    print(f"✓ Has dominating nodes: {graph.has_dominating_nodes()}")
    print(f"✓ Isolated vertices: {len(graph.get_isolated_vertices())}")

    print("\n=== Dau-Compliant Model Test Complete ===")
