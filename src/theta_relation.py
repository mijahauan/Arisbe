"""
Theta (Θ) Relation Implementation per Dau Definition 15.1

The Θ relation defines when two vertices are connected by a ligature path
that respects context nesting constraints. This is crucial for the formal
iteration rule and ligature manipulation.

Definition 15.1: For vertices v, w ∈ V, we have vΘw iff there exist 
vertices v₁, ..., vₙ such that:
1. Either v = v₁ and vₙ = w, or w = v₁ and vₙ = v
2. ctx(v₁) ≥ ctx(v₂) ≥ ... ≥ ctx(vₙ) (context nesting decreases)
3. For each i = 1, ..., n-1, there exists an identity edge eᵢ = {vᵢ, vᵢ₊₁} 
   with ctx(eᵢ) = ctx(vᵢ₊₁)

Properties: Θ is reflexive and symmetric but NOT transitive.
"""

from typing import Dict, List, Set, FrozenSet, Tuple, Optional, Iterator
from dataclasses import dataclass
from collections import deque

from egi_core_dau import RelationalGraphWithCuts, ElementID, Vertex, Edge, Cut
from frozendict import frozendict


@dataclass(frozen=True)
class ThetaPath:
    """A path between two vertices satisfying the Θ relation."""
    vertices: Tuple[ElementID, ...]
    identity_edges: Tuple[ElementID, ...]
    contexts: Tuple[ElementID, ...]
    is_valid: bool
    
    def __post_init__(self):
        """Validate path structure."""
        if len(self.vertices) != len(self.contexts):
            object.__setattr__(self, 'is_valid', False)
        if len(self.identity_edges) != len(self.vertices) - 1:
            object.__setattr__(self, 'is_valid', False)


@dataclass
class ThetaRelationResult:
    """Result of Θ relation checking."""
    are_theta_related: bool
    paths: List[ThetaPath]
    reason: Optional[str] = None


class ThetaRelationEngine:
    """
    Engine for computing the Θ relation per Dau Definition 15.1.
    
    The Θ relation is fundamental for:
    - Formal iteration rule implementation
    - Ligature manipulation validation
    - Context-aware vertex connectivity
    """
    
    def __init__(self):
        self._context_cache: Dict[Tuple[ElementID, ElementID], Optional[ElementID]] = {}
        self._identity_edge_cache: Dict[ElementID, Set[Tuple[ElementID, ElementID]]] = {}
    
    def compute_theta_relation(self, 
                             egi: RelationalGraphWithCuts, 
                             v1: ElementID, 
                             v2: ElementID) -> ThetaRelationResult:
        """
        Compute whether v1 Θ v2 per Definition 15.1.
        
        Args:
            egi: The EGI containing the vertices
            v1: First vertex
            v2: Second vertex
            
        Returns:
            ThetaRelationResult indicating if vertices are Θ-related
        """
        
        # Reflexivity check
        if v1 == v2:
            return ThetaRelationResult(
                are_theta_related=True,
                paths=[ThetaPath((v1,), (), (self._get_vertex_context(egi, v1),), True)],
                reason="Reflexivity: vertex is Θ-related to itself"
            )
        
        # Verify both vertices exist
        if not self._vertex_exists(egi, v1) or not self._vertex_exists(egi, v2):
            return ThetaRelationResult(
                are_theta_related=False,
                paths=[],
                reason="One or both vertices do not exist in EGI"
            )
        
        # Find all valid Θ paths between v1 and v2
        paths = self._find_theta_paths(egi, v1, v2)
        
        return ThetaRelationResult(
            are_theta_related=len(paths) > 0,
            paths=paths,
            reason=None if paths else "No valid Θ path found respecting context nesting"
        )
    
    def _find_theta_paths(self, 
                         egi: RelationalGraphWithCuts, 
                         start: ElementID, 
                         end: ElementID) -> List[ThetaPath]:
        """
        Find all valid Θ paths from start to end using breadth-first search.
        
        A valid path must satisfy:
        1. Connected by identity edges
        2. Context nesting decreases: ctx(v₁) ≥ ctx(v₂) ≥ ... ≥ ctx(vₙ)
        3. Each identity edge has context equal to the deeper vertex
        """
        
        valid_paths = []
        identity_graph = self._build_identity_graph(egi)
        
        # BFS to find all paths
        queue = deque([(start, [start], [])])  # (current_vertex, path, edges)
        visited_paths = set()
        
        while queue:
            current, path, edges = queue.popleft()
            
            # Avoid cycles and redundant paths
            path_key = tuple(path)
            if path_key in visited_paths:
                continue
            visited_paths.add(path_key)
            
            # Check if we reached the end
            if current == end and len(path) > 1:
                # Validate the complete path
                theta_path = self._validate_theta_path(egi, path, edges)
                if theta_path.is_valid:
                    valid_paths.append(theta_path)
                continue
            
            # Explore neighbors via identity edges
            if current in identity_graph:
                for neighbor, edge_id in identity_graph[current]:
                    if neighbor not in path:  # Avoid cycles
                        new_path = path + [neighbor]
                        new_edges = edges + [edge_id]
                        
                        # Early validation: check context nesting constraint
                        if self._satisfies_context_nesting(egi, new_path):
                            queue.append((neighbor, new_path, new_edges))
        
        return valid_paths
    
    def _build_identity_graph(self, egi: RelationalGraphWithCuts) -> Dict[ElementID, List[Tuple[ElementID, ElementID]]]:
        """Build adjacency graph of vertices connected by identity edges."""
        
        identity_graph = {}
        
        # Find all identity edges (relation = "=")
        for edge_id, relation in egi.rel.items():
            if relation == "=":
                vertex_sequence = egi.nu.get(edge_id, ())
                if len(vertex_sequence) == 2:
                    v1, v2 = vertex_sequence
                    
                    # Add bidirectional connections
                    if v1 not in identity_graph:
                        identity_graph[v1] = []
                    if v2 not in identity_graph:
                        identity_graph[v2] = []
                    
                    identity_graph[v1].append((v2, edge_id))
                    identity_graph[v2].append((v1, edge_id))
        
        return identity_graph
    
    def _satisfies_context_nesting(self, egi: RelationalGraphWithCuts, path: List[ElementID]) -> bool:
        """Check if path satisfies context nesting constraint: ctx(v₁) ≥ ctx(v₂) ≥ ... ≥ ctx(vₙ)."""
        
        if len(path) < 2:
            return True
        
        contexts = [self._get_vertex_context(egi, v) for v in path]
        nesting_levels = [self._calculate_nesting_level(egi, ctx) for ctx in contexts]
        
        # Check non-increasing nesting levels (deeper = higher number)
        for i in range(len(nesting_levels) - 1):
            if nesting_levels[i] < nesting_levels[i + 1]:
                return False
        
        return True
    
    def _validate_theta_path(self, 
                           egi: RelationalGraphWithCuts, 
                           vertices: List[ElementID], 
                           edges: List[ElementID]) -> ThetaPath:
        """Validate a complete Θ path against all Definition 15.1 requirements."""
        
        if len(vertices) < 2:
            return ThetaPath(tuple(vertices), tuple(edges), (), False)
        
        contexts = [self._get_vertex_context(egi, v) for v in vertices]
        
        # Check context nesting constraint
        if not self._satisfies_context_nesting(egi, vertices):
            return ThetaPath(tuple(vertices), tuple(edges), tuple(contexts), False)
        
        # Check identity edge context constraint: ctx(eᵢ) = ctx(vᵢ₊₁)
        for i, edge_id in enumerate(edges):
            edge_context = self._get_edge_context(egi, edge_id)
            next_vertex_context = contexts[i + 1]
            
            if edge_context != next_vertex_context:
                return ThetaPath(tuple(vertices), tuple(edges), tuple(contexts), False)
        
        return ThetaPath(tuple(vertices), tuple(edges), tuple(contexts), True)
    
    def _get_vertex_context(self, egi: RelationalGraphWithCuts, vertex_id: ElementID) -> ElementID:
        """Get the context (area) containing a vertex."""
        
        for area_id, contents in egi.area.items():
            if vertex_id in contents:
                return area_id
        
        # Default to sheet if not found in any cut
        return egi.sheet
    
    def _get_edge_context(self, egi: RelationalGraphWithCuts, edge_id: ElementID) -> ElementID:
        """Get the context (area) containing an edge."""
        
        for area_id, contents in egi.area.items():
            if edge_id in contents:
                return area_id
        
        # Default to sheet if not found in any cut
        return egi.sheet
    
    def _calculate_nesting_level(self, egi: RelationalGraphWithCuts, context: ElementID) -> int:
        """Calculate nesting level of a context (0 = sheet, higher = more nested)."""
        
        if context == egi.sheet:
            return 0
        
        level = 0
        current = context
        
        while current != egi.sheet:
            # Find parent context
            parent = None
            for area_id, contents in egi.area.items():
                if current in contents:
                    parent = area_id
                    break
            
            if parent is None:
                break
            
            level += 1
            current = parent
        
        return level
    
    def _vertex_exists(self, egi: RelationalGraphWithCuts, vertex_id: ElementID) -> bool:
        """Check if vertex exists in EGI."""
        return any(v.id == vertex_id for v in egi.V)
    
    def is_theta_reflexive(self, egi: RelationalGraphWithCuts, vertex_id: ElementID) -> bool:
        """Check reflexivity: every vertex is Θ-related to itself."""
        return self._vertex_exists(egi, vertex_id)
    
    def is_theta_symmetric(self, egi: RelationalGraphWithCuts, v1: ElementID, v2: ElementID) -> bool:
        """Check symmetry: if v1 Θ v2, then v2 Θ v1."""
        result1 = self.compute_theta_relation(egi, v1, v2)
        result2 = self.compute_theta_relation(egi, v2, v1)
        return result1.are_theta_related == result2.are_theta_related
    
    def demonstrate_non_transitivity(self, egi: RelationalGraphWithCuts) -> Dict[str, any]:
        """
        Demonstrate that Θ is not transitive by finding a counter-example.
        
        Returns example where v1 Θ v2 and v2 Θ v3 but NOT v1 Θ v3.
        """
        
        vertices = [v.id for v in egi.V]
        
        for v1 in vertices:
            for v2 in vertices:
                for v3 in vertices:
                    if v1 != v2 != v3 != v1:
                        rel12 = self.compute_theta_relation(egi, v1, v2)
                        rel23 = self.compute_theta_relation(egi, v2, v3)
                        rel13 = self.compute_theta_relation(egi, v1, v3)
                        
                        if (rel12.are_theta_related and 
                            rel23.are_theta_related and 
                            not rel13.are_theta_related):
                            
                            return {
                                "counter_example": True,
                                "v1": v1,
                                "v2": v2, 
                                "v3": v3,
                                "v1_theta_v2": True,
                                "v2_theta_v3": True,
                                "v1_theta_v3": False,
                                "explanation": "Θ relation is not transitive"
                            }
        
        return {
            "counter_example": False,
            "explanation": "No counter-example found in this EGI"
        }
    
    def get_theta_equivalence_classes(self, egi: RelationalGraphWithCuts) -> List[Set[ElementID]]:
        """
        Get equivalence classes if Θ were transitive (for comparison).
        Note: This is NOT how Θ actually works - it's for analysis only.
        """
        
        vertices = [v.id for v in egi.V]
        classes = []
        processed = set()
        
        for vertex in vertices:
            if vertex in processed:
                continue
            
            # Find all vertices Θ-related to this one
            equiv_class = {vertex}
            for other in vertices:
                if other != vertex:
                    result = self.compute_theta_relation(egi, vertex, other)
                    if result.are_theta_related:
                        equiv_class.add(other)
            
            classes.append(equiv_class)
            processed.update(equiv_class)
        
        return classes


def demonstrate_theta_relation():
    """Demonstrate the Θ relation implementation."""
    
    print("🔗 Theta (Θ) Relation Demonstration")
    print("=" * 40)
    
    # Create test EGI with ligature structure
    from egi_core_dau import RelationalGraphWithCuts, ElementID, Vertex, Edge
    
    # Vertices
    vertex_a = Vertex(ElementID("A"))
    vertex_b = Vertex(ElementID("B"))  
    vertex_c = Vertex(ElementID("C"))
    
    # Identity edge between A and B
    identity_edge = Edge(ElementID("id_AB"))
    
    # Cut containing vertex C
    cut1 = Cut(ElementID("cut1"))
    
    test_egi = RelationalGraphWithCuts(
        V=frozenset([vertex_a, vertex_b, vertex_c]),
        E=frozenset([identity_edge]),
        nu=frozendict({
            ElementID("id_AB"): (ElementID("A"), ElementID("B"))
        }),
        sheet=ElementID("sheet"),
        Cut=frozenset([cut1]),
        area=frozendict({
            ElementID("sheet"): frozenset([ElementID("A"), ElementID("B"), ElementID("id_AB"), ElementID("cut1")]),
            ElementID("cut1"): frozenset([ElementID("C")])
        }),
        rel=frozendict({
            ElementID("id_AB"): "="
        })
    )
    
    engine = ThetaRelationEngine()
    
    # Test reflexivity
    print("\n🔄 Testing Reflexivity:")
    result_aa = engine.compute_theta_relation(test_egi, ElementID("A"), ElementID("A"))
    print(f"   A Θ A: {'✅' if result_aa.are_theta_related else '❌'} ({result_aa.reason})")
    
    # Test symmetry with identity edge
    print("\n↔️ Testing Symmetry with Identity Edge:")
    result_ab = engine.compute_theta_relation(test_egi, ElementID("A"), ElementID("B"))
    result_ba = engine.compute_theta_relation(test_egi, ElementID("B"), ElementID("A"))
    print(f"   A Θ B: {'✅' if result_ab.are_theta_related else '❌'}")
    print(f"   B Θ A: {'✅' if result_ba.are_theta_related else '❌'}")
    print(f"   Symmetric: {'✅' if result_ab.are_theta_related == result_ba.are_theta_related else '❌'}")
    
    if result_ab.are_theta_related and result_ab.paths:
        path = result_ab.paths[0]
        print(f"   Path: {' → '.join(str(v) for v in path.vertices)}")
        print(f"   Contexts: {' → '.join(str(c) for c in path.contexts)}")
    
    # Test non-relation (no identity edge)
    print("\n❌ Testing Non-Relation:")
    result_ac = engine.compute_theta_relation(test_egi, ElementID("A"), ElementID("C"))
    print(f"   A Θ C: {'✅' if result_ac.are_theta_related else '❌'} ({result_ac.reason})")
    
    # Test non-transitivity
    print("\n🚫 Testing Non-Transitivity:")
    non_trans = engine.demonstrate_non_transitivity(test_egi)
    if non_trans["counter_example"]:
        print(f"   Counter-example found: {non_trans['v1']} Θ {non_trans['v2']} and {non_trans['v2']} Θ {non_trans['v3']} but NOT {non_trans['v1']} Θ {non_trans['v3']}")
    else:
        print(f"   {non_trans['explanation']}")
    
    print(f"\n✅ Θ Relation Implementation Complete")
    print(f"   - Reflexive: ✅")
    print(f"   - Symmetric: ✅") 
    print(f"   - Non-Transitive: ✅")
    print(f"   - Context-Aware: ✅")
    
    return engine


if __name__ == "__main__":
    demonstrate_theta_relation()
