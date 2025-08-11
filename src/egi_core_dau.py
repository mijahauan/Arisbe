"""
Dau-compliant Existential Graph Instance (EGI) core implementation.
Follows Frithjof Dau's exact 6+1 component definition from "Mathematical Logic with Diagrams".

This implementation replaces the previous "Context" model with Dau's formal:
- 6-component Relational Graph with Cuts: (V, E, ν, ⊤, Cut, area)  
- 7th component: rel mapping for relation names
- Proper area/context distinction for diagram generation
- Support for isolated vertices ("heavy dots")
"""

from dataclasses import dataclass
from typing import FrozenSet, Dict, Set, List, Optional, Tuple, Union, Any
from frozendict import frozendict
import uuid
from abc import ABC, abstractmethod


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
    V: FrozenSet[Vertex]                                    # Component 1: Vertices
    E: FrozenSet[Edge]                                      # Component 2: Edges
    nu: frozendict[ElementID, VertexSequence]              # Component 3: ν mapping
    sheet: ElementID                                        # Component 4: ⊤ sheet of assertion
    Cut: FrozenSet[Cut]                                     # Component 5: Cuts
    area: frozendict[ElementID, FrozenSet[ElementID]]       # Component 6: area mapping
    
    # 7th component for relation names
    rel: frozendict[ElementID, RelationName]               # Component 7: relation mapping
    
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
        
        object.__setattr__(self, '_vertex_map', frozendict(vertex_map))
        object.__setattr__(self, '_edge_map', frozendict(edge_map))
        object.__setattr__(self, '_cut_map', frozendict(cut_map))
        
        # Validate Dau's constraints
        self._validate_dau_constraints()
    
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
        all_elements = {v.id for v in self.V} | {e.id for e in self.E} | {c.id for c in self.Cut}
        
        # Constraint a) c₁ ≠ c₂ ⇒ area(c₁) ∩ area(c₂) = ∅
        context_ids = [c.id for c in self.Cut] + [self.sheet]
        for i, c1 in enumerate(context_ids):
            for c2 in context_ids[i+1:]:
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
            raise ValueError(f"Area coverage mismatch. Missing: {missing}, Extra: {extra}")
        
        # Constraint c) c ∉ area^n(c) for each c ∈ Cut ∪ {⊤} and n ∈ ℕ
        # This prevents cycles in the area containment
        for context_id in context_ids:
            if self._has_area_cycle(context_id):
                raise ValueError(f"Context {context_id} has area containment cycle")
    
    def _has_area_cycle(self, start_context: ElementID, visited: Optional[Set[ElementID]] = None) -> bool:
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
    
    def with_vertex(self, vertex: Vertex) -> 'RelationalGraphWithCuts':
        """Create new graph with additional vertex in sheet of assertion."""
        return self.with_vertex_in_context(vertex, self.sheet)
    
    def with_vertex_in_context(self, vertex: Vertex, context_id: ElementID) -> 'RelationalGraphWithCuts':
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
            rel=self.rel
        )
    
    def with_edge(self, edge: Edge, vertex_sequence: VertexSequence, 
                  relation_name: RelationName, context_id: ElementID = None) -> 'RelationalGraphWithCuts':
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
            rel=frozendict(new_rel)
        )
    
    def with_cut(self, cut: Cut, context_id: ElementID = None) -> 'RelationalGraphWithCuts':
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
            rel=self.rel
        )
    
    def with_vertex_moved_to_context(self, vertex_id: ElementID, new_context_id: ElementID) -> 'RelationalGraphWithCuts':
        """Return a new graph with the given vertex relocated to a different context.
        Preserves all other components; validates that vertex exists and context exists.
        """
        # Validate vertex exists
        if vertex_id not in {v.id for v in self.V}:
            raise ValueError(f"Vertex {vertex_id} not found")
        # Validate target context exists
        if new_context_id != self.sheet and new_context_id not in {c.id for c in self.Cut}:
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
            rel=self.rel
        )
    
    def without_element(self, element_id: ElementID) -> 'RelationalGraphWithCuts':
        """Create new graph without specified element."""
        if element_id in {v.id for v in self.V}:
            return self._without_vertex(element_id)
        elif element_id in {e.id for e in self.E}:
            return self._without_edge(element_id)
        elif element_id in {c.id for c in self.Cut}:
            return self._without_cut(element_id)
        else:
            raise ValueError(f"Element {element_id} not found")
    
    def _without_vertex(self, vertex_id: ElementID) -> 'RelationalGraphWithCuts':
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
            rel=self.rel
        )
    
    def _without_edge(self, edge_id: ElementID) -> 'RelationalGraphWithCuts':
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
            rel=new_rel
        )
    
    def _without_cut(self, cut_id: ElementID) -> 'RelationalGraphWithCuts':
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
            rel=self.rel
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
        rel=frozendict()
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
            if self.counter < 26:
                name = chr(ord('x') + self.counter)
            else:
                name = f"x{self.counter - 25}"
            
            if name not in self.used_names:
                self.used_names.add(name)
                self.counter += 1
                return name
            
            self.counter += 1
    
    def reserve_name(self, name: str):
        """Reserve a variable name."""
        self.used_names.add(name)


if __name__ == "__main__":
    # Test the Dau-compliant implementation
    print("=== Testing Dau-Compliant 6+1 Component Model ===")
    
    # Create empty graph
    graph = create_empty_graph()
    print(f"✓ Empty graph created: {len(graph.V)} vertices, {len(graph.E)} edges, {len(graph.Cut)} cuts")
    
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

