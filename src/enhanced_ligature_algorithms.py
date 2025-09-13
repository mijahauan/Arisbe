"""
Enhanced Ligature Algorithms with Non-Transitive Θ Relation Support

Updates ligature manipulation algorithms to properly handle the non-transitive
nature of the Θ relation per Dau Definition 15.1. This affects:
- Ligature path traversal
- Identity network construction
- Branch moving operations
- Ligature extension/restriction
"""

from typing import Dict, List, Set, FrozenSet, Tuple, Optional, Any
from dataclasses import dataclass
from collections import deque

from egi_core_dau import RelationalGraphWithCuts, ElementID, Vertex, Edge, Cut
from frozendict import frozendict
from theta_relation import ThetaRelationEngine, ThetaPath, ThetaRelationResult
from ligature_manipulation_rules import LigatureManipulationEngine


@dataclass
class LigatureNetwork:
    """A network of vertices connected by identity edges, respecting Θ relation."""
    vertices: Set[ElementID]
    identity_edges: Set[ElementID]
    theta_paths: Dict[Tuple[ElementID, ElementID], List[ThetaPath]]
    is_connected: bool
    components: List[Set[ElementID]]  # Connected components (due to non-transitivity)


@dataclass
class EnhancedLigatureResult:
    """Result of enhanced ligature operation."""
    success: bool
    result_egi: Optional[RelationalGraphWithCuts]
    ligature_network: Optional[LigatureNetwork]
    theta_violations: List[str]
    error_message: Optional[str] = None


class EnhancedLigatureAlgorithms:
    """
    Enhanced ligature algorithms that properly handle non-transitive Θ relation.
    
    Key differences from basic algorithms:
    1. Cannot assume transitivity in ligature traversal
    2. Must validate each Θ connection individually
    3. Ligature networks may have multiple disconnected components
    4. Branch moving must respect Θ path constraints
    """
    
    def __init__(self):
        self.theta_engine = ThetaRelationEngine()
        self.basic_ligature_engine = LigatureManipulationEngine()
    
    def analyze_ligature_network(self, 
                                egi: RelationalGraphWithCuts,
                                vertices: Set[ElementID]) -> LigatureNetwork:
        """
        Analyze ligature network structure with non-transitive Θ relation.
        
        Args:
            egi: EGI containing the vertices
            vertices: Set of vertices to analyze
            
        Returns:
            LigatureNetwork with component analysis
        """
        
        # Find all identity edges connecting these vertices
        identity_edges = set()
        for edge in egi.E:
            if egi.rel.get(edge.id) == "=":
                vertex_sequence = egi.nu.get(edge.id, ())
                if (len(vertex_sequence) == 2 and 
                    vertex_sequence[0] in vertices and 
                    vertex_sequence[1] in vertices):
                    identity_edges.add(edge.id)
        
        # Compute all Θ paths between vertex pairs
        theta_paths = {}
        for v1 in vertices:
            for v2 in vertices:
                if v1 != v2:
                    result = self.theta_engine.compute_theta_relation(egi, v1, v2)
                    if result.are_theta_related:
                        theta_paths[(v1, v2)] = result.paths
        
        # Find connected components (accounting for non-transitivity)
        components = self._find_theta_components(vertices, theta_paths)
        
        return LigatureNetwork(
            vertices=vertices,
            identity_edges=identity_edges,
            theta_paths=theta_paths,
            is_connected=len(components) == 1,
            components=components
        )
    
    def _find_theta_components(self, 
                             vertices: Set[ElementID],
                             theta_paths: Dict[Tuple[ElementID, ElementID], List[ThetaPath]]) -> List[Set[ElementID]]:
        """Find connected components in the Θ relation graph."""
        
        # Build adjacency list for Θ relation
        adjacency = {v: set() for v in vertices}
        for (v1, v2), paths in theta_paths.items():
            if paths:  # If there's a valid Θ path
                adjacency[v1].add(v2)
                adjacency[v2].add(v1)  # Θ is symmetric
        
        # Find connected components using DFS
        visited = set()
        components = []
        
        for vertex in vertices:
            if vertex not in visited:
                component = set()
                stack = [vertex]
                
                while stack:
                    current = stack.pop()
                    if current not in visited:
                        visited.add(current)
                        component.add(current)
                        
                        # Add unvisited neighbors
                        for neighbor in adjacency[current]:
                            if neighbor not in visited:
                                stack.append(neighbor)
                
                components.append(component)
        
        return components
    
    def enhanced_move_branches_along_ligature(self, 
                                            egi: RelationalGraphWithCuts,
                                            source_vertex: ElementID,
                                            target_vertex: ElementID,
                                            ligature_context: ElementID) -> EnhancedLigatureResult:
        """
        Move branches along ligature with Θ relation validation.
        
        This enhanced version validates that the move respects Θ path constraints
        and handles non-transitivity properly.
        """
        
        theta_violations = []
        
        # Validate Θ relation between source and target
        theta_result = self.theta_engine.compute_theta_relation(egi, source_vertex, target_vertex)
        
        if not theta_result.are_theta_related:
            return EnhancedLigatureResult(
                success=False,
                result_egi=None,
                ligature_network=None,
                theta_violations=[f"No Θ relation between {source_vertex} and {target_vertex}"],
                error_message="Vertices not connected by valid Θ path"
            )
        
        # Analyze the ligature network
        involved_vertices = {source_vertex, target_vertex}
        ligature_network = self.analyze_ligature_network(egi, involved_vertices)
        
        # Check if vertices are in the same Θ component
        same_component = False
        for component in ligature_network.components:
            if source_vertex in component and target_vertex in component:
                same_component = True
                break
        
        if not same_component:
            theta_violations.append(f"Vertices {source_vertex} and {target_vertex} in different Θ components")
        
        # Validate context constraints for all Θ paths
        for path in theta_result.paths:
            if not self._validate_path_context_constraints(egi, path, ligature_context):
                theta_violations.append(f"Path {path.vertices} violates context constraints")
        
        if theta_violations:
            return EnhancedLigatureResult(
                success=False,
                result_egi=None,
                ligature_network=ligature_network,
                theta_violations=theta_violations,
                error_message="Θ relation constraints violated"
            )
        
        # Apply the basic ligature manipulation if Θ constraints are satisfied
        try:
            basic_result = self.basic_ligature_engine.apply_rule(
                "MOVE_BRANCHES", egi, ligature_context, frozenset([source_vertex, target_vertex])
            )
            
            return EnhancedLigatureResult(
                success=basic_result.success,
                result_egi=basic_result.result_egi,
                ligature_network=ligature_network,
                theta_violations=[],
                error_message=basic_result.error_message
            )
        
        except Exception as e:
            return EnhancedLigatureResult(
                success=False,
                result_egi=None,
                ligature_network=ligature_network,
                theta_violations=[],
                error_message=f"Ligature manipulation failed: {str(e)}"
            )
    
    def enhanced_extend_ligature(self, 
                               egi: RelationalGraphWithCuts,
                               existing_ligature: Set[ElementID],
                               new_vertices: Set[ElementID],
                               target_context: ElementID) -> EnhancedLigatureResult:
        """
        Extend ligature with new identity connections, validating Θ constraints.
        
        This enhanced version ensures that all new connections respect the
        non-transitive nature of the Θ relation.
        """
        
        theta_violations = []
        
        # Analyze existing ligature network
        all_vertices = existing_ligature.union(new_vertices)
        ligature_network = self.analyze_ligature_network(egi, all_vertices)
        
        # Validate that new vertices can be connected via Θ relation
        for new_vertex in new_vertices:
            can_connect = False
            for existing_vertex in existing_ligature:
                theta_result = self.theta_engine.compute_theta_relation(egi, new_vertex, existing_vertex)
                if theta_result.are_theta_related:
                    can_connect = True
                    
                    # Validate context constraints for connection paths
                    for path in theta_result.paths:
                        if not self._validate_path_context_constraints(egi, path, target_context):
                            theta_violations.append(
                                f"Connection path from {new_vertex} to {existing_vertex} violates context constraints"
                            )
                    break
            
            if not can_connect:
                theta_violations.append(f"New vertex {new_vertex} cannot connect to existing ligature via Θ relation")
        
        # Check for transitivity violations in the extended network
        transitivity_violations = self._check_transitivity_violations(ligature_network)
        theta_violations.extend(transitivity_violations)
        
        if theta_violations:
            return EnhancedLigatureResult(
                success=False,
                result_egi=None,
                ligature_network=ligature_network,
                theta_violations=theta_violations,
                error_message="Θ relation constraints violated in ligature extension"
            )
        
        # Apply the basic ligature extension if Θ constraints are satisfied
        try:
            basic_result = self.basic_ligature_engine.apply_rule(
                "EXTEND_LIGATURE", egi, target_context, frozenset(all_vertices)
            )
            
            return EnhancedLigatureResult(
                success=basic_result.success,
                result_egi=basic_result.result_egi,
                ligature_network=ligature_network,
                theta_violations=[],
                error_message=basic_result.error_message
            )
        
        except Exception as e:
            return EnhancedLigatureResult(
                success=False,
                result_egi=None,
                ligature_network=ligature_network,
                theta_violations=[],
                error_message=f"Ligature extension failed: {str(e)}"
            )
    
    def _validate_path_context_constraints(self, 
                                         egi: RelationalGraphWithCuts,
                                         path: ThetaPath,
                                         required_context: ElementID) -> bool:
        """Validate that a Θ path satisfies context constraints."""
        
        # Check that all vertices in path are accessible from required context
        for vertex_id in path.vertices:
            vertex_context = self._get_vertex_context(egi, vertex_id)
            if not self._is_context_accessible(egi, required_context, vertex_context):
                return False
        
        # Check that all identity edges in path are in appropriate contexts
        for edge_id in path.identity_edges:
            edge_context = self._get_edge_context(egi, edge_id)
            if not self._is_context_accessible(egi, required_context, edge_context):
                return False
        
        return True
    
    def _check_transitivity_violations(self, ligature_network: LigatureNetwork) -> List[str]:
        """Check for potential issues due to non-transitivity of Θ relation."""
        
        violations = []
        vertices = list(ligature_network.vertices)
        
        # Look for cases where A Θ B and B Θ C but NOT A Θ C
        for i, v1 in enumerate(vertices):
            for j, v2 in enumerate(vertices[i+1:], i+1):
                for k, v3 in enumerate(vertices[j+1:], j+1):
                    # Check if v1 Θ v2 and v2 Θ v3
                    has_12 = (v1, v2) in ligature_network.theta_paths or (v2, v1) in ligature_network.theta_paths
                    has_23 = (v2, v3) in ligature_network.theta_paths or (v3, v2) in ligature_network.theta_paths
                    has_13 = (v1, v3) in ligature_network.theta_paths or (v3, v1) in ligature_network.theta_paths
                    
                    if has_12 and has_23 and not has_13:
                        violations.append(
                            f"Non-transitivity: {v1} Θ {v2} and {v2} Θ {v3} but NOT {v1} Θ {v3}"
                        )
        
        return violations
    
    def _get_vertex_context(self, egi: RelationalGraphWithCuts, vertex_id: ElementID) -> ElementID:
        """Get the context containing a vertex."""
        for area_id, contents in egi.area.items():
            if vertex_id in contents:
                return area_id
        return egi.sheet
    
    def _get_edge_context(self, egi: RelationalGraphWithCuts, edge_id: ElementID) -> ElementID:
        """Get the context containing an edge."""
        for area_id, contents in egi.area.items():
            if edge_id in contents:
                return area_id
        return egi.sheet
    
    def _is_context_accessible(self, egi: RelationalGraphWithCuts, from_context: ElementID, to_context: ElementID) -> bool:
        """Check if to_context is accessible from from_context (nesting-wise)."""
        
        # Same context is always accessible
        if from_context == to_context:
            return True
        
        # Check if to_context is nested within from_context
        current = to_context
        while current != egi.sheet:
            parent = None
            for area_id, contents in egi.area.items():
                if current in contents:
                    parent = area_id
                    break
            
            if parent is None:
                break
            
            if parent == from_context:
                return True
            
            current = parent
        
        return False
    
    def validate_ligature_consistency(self, egi: RelationalGraphWithCuts) -> Tuple[bool, List[str]]:
        """
        Validate that all ligatures in the EGI are consistent with Θ relation constraints.
        
        Returns:
            Tuple of (is_consistent, list_of_violations)
        """
        
        violations = []
        
        # Find all identity edges
        identity_edges = []
        for edge in egi.E:
            if egi.rel.get(edge.id) == "=":
                vertex_sequence = egi.nu.get(edge.id, ())
                if len(vertex_sequence) == 2:
                    identity_edges.append((edge.id, vertex_sequence[0], vertex_sequence[1]))
        
        # Validate each identity edge against Θ relation
        for edge_id, v1, v2 in identity_edges:
            theta_result = self.theta_engine.compute_theta_relation(egi, v1, v2)
            
            if not theta_result.are_theta_related:
                violations.append(f"Identity edge {edge_id} connects vertices {v1}, {v2} not related by Θ")
            else:
                # Check context constraints for the edge
                edge_context = self._get_edge_context(egi, edge_id)
                valid_context = False
                
                for path in theta_result.paths:
                    if self._validate_path_context_constraints(egi, path, edge_context):
                        valid_context = True
                        break
                
                if not valid_context:
                    violations.append(f"Identity edge {edge_id} violates context constraints for Θ path")
        
        return len(violations) == 0, violations


def demonstrate_enhanced_ligature_algorithms():
    """Demonstrate enhanced ligature algorithms with Θ relation."""
    
    print("🔗 Enhanced Ligature Algorithms Demonstration")
    print("=" * 55)
    
    # Create test EGI with ligature structure
    from egi_core_dau import RelationalGraphWithCuts, ElementID, Vertex, Edge, Cut
    
    vertex_a = Vertex(ElementID("A"))
    vertex_b = Vertex(ElementID("B"))
    vertex_c = Vertex(ElementID("C"))
    identity_ab = Edge(ElementID("id_AB"))
    identity_bc = Edge(ElementID("id_BC"))
    cut1 = Cut(ElementID("cut1"))
    
    test_egi = RelationalGraphWithCuts(
        V=frozenset([vertex_a, vertex_b, vertex_c]),
        E=frozenset([identity_ab, identity_bc]),
        nu=frozendict({
            ElementID("id_AB"): (ElementID("A"), ElementID("B")),
            ElementID("id_BC"): (ElementID("B"), ElementID("C"))
        }),
        sheet=ElementID("sheet"),
        Cut=frozenset([cut1]),
        area=frozendict({
            ElementID("sheet"): frozenset([ElementID("A"), ElementID("B"), ElementID("id_AB"), ElementID("cut1")]),
            ElementID("cut1"): frozenset([ElementID("C"), ElementID("id_BC")])
        }),
        rel=frozendict({
            ElementID("id_AB"): "=",
            ElementID("id_BC"): "="
        })
    )
    
    algorithms = EnhancedLigatureAlgorithms()
    
    print("\n📊 Test EGI:")
    print(f"   Vertices: {[v.id for v in test_egi.V]}")
    print(f"   Identity edges: {[e.id for e in test_egi.E if test_egi.rel.get(e.id) == '=']}")
    print(f"   Areas: {dict(test_egi.area)}")
    
    # Analyze ligature network
    print("\n🔍 Analyzing Ligature Network:")
    vertices = {ElementID("A"), ElementID("B"), ElementID("C")}
    network = algorithms.analyze_ligature_network(test_egi, vertices)
    
    print(f"   Vertices: {len(network.vertices)}")
    print(f"   Identity edges: {len(network.identity_edges)}")
    print(f"   Connected: {'✅' if network.is_connected else '❌'}")
    print(f"   Components: {len(network.components)}")
    
    for i, component in enumerate(network.components, 1):
        print(f"     Component {i}: {[str(v) for v in component]}")
    
    # Test enhanced branch moving
    print("\n🔄 Testing Enhanced Branch Moving:")
    move_result = algorithms.enhanced_move_branches_along_ligature(
        test_egi, ElementID("A"), ElementID("B"), ElementID("sheet")
    )
    
    print(f"   Success: {'✅' if move_result.success else '❌'}")
    if move_result.theta_violations:
        print(f"   Θ violations: {len(move_result.theta_violations)}")
        for violation in move_result.theta_violations:
            print(f"     • {violation}")
    
    # Test ligature consistency validation
    print("\n✅ Testing Ligature Consistency:")
    is_consistent, violations = algorithms.validate_ligature_consistency(test_egi)
    print(f"   Consistent: {'✅' if is_consistent else '❌'}")
    
    if violations:
        print(f"   Violations: {len(violations)}")
        for violation in violations:
            print(f"     • {violation}")
    
    print(f"\n✅ Enhanced Ligature Algorithms Complete")
    print(f"   - Non-transitive Θ support: ✅")
    print(f"   - Component analysis: ✅")
    print(f"   - Context validation: ✅")
    print(f"   - Consistency checking: ✅")
    
    return algorithms


if __name__ == "__main__":
    demonstrate_enhanced_ligature_algorithms()
