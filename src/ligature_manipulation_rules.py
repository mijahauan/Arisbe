"""
Chapter 16 Ligature Manipulation Rules implementing Dau's formalism.
These rules allow rearranging ligatures while preserving logical meaning.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, FrozenSet
from dataclasses import dataclass
from abc import ABC, abstractmethod

from egi_core_dau import RelationalGraphWithCuts, ElementID, Vertex, Edge, Cut
from frozendict import frozendict
from formal_transformation_rules import FormalTransformationRule, TransformationContext, TransformationResult


class MoveBranchesAlongLigatureRule(FormalTransformationRule):
    """
    Lemma 16.1: Moving Branches along a Ligature in a Context
    Allows repositioning vertices along the same ligature while preserving identity.
    """
    
    def get_rule_name(self) -> str:
        return "MOVE_BRANCHES (Move Branches Along Ligature)"
    
    def check_preconditions(self, context: TransformationContext) -> Tuple[bool, Optional[str]]:
        """
        Requires two vertices on the same ligature in the same context.
        """
        if len(context.selected_subgraph) != 2:
            return False, "Must select exactly two vertices for branch moving"
        
        vertices = list(context.selected_subgraph)
        va_id, vb_id = vertices[0], vertices[1]
        
        # Verify both are vertices
        egi = context.source_egi
        va = self._get_vertex_by_id(egi, va_id)
        vb = self._get_vertex_by_id(egi, vb_id)
        
        if not va or not vb:
            return False, "Selected elements must be vertices"
        
        # Check if vertices are in same context
        va_context = self._get_vertex_context(egi, va_id)
        vb_context = self._get_vertex_context(egi, vb_id)
        
        if va_context != vb_context:
            return False, "Vertices must be in the same context for branch moving"
        
        # Check if vertices are on the same ligature (connected by identity edges)
        if not self._vertices_on_same_ligature(egi, va_id, vb_id):
            return False, "Vertices must be on the same ligature (vaΘvb relation)"
        
        return True, None
    
    def apply_transformation(self, context: TransformationContext) -> TransformationResult:
        """Apply branch moving by repositioning vertex on ligature."""
        precondition_ok, error_msg = self.check_preconditions(context)
        if not precondition_ok:
            return TransformationResult(False, None, error_msg, {})
        
        try:
            egi = context.source_egi
            vertices = list(context.selected_subgraph)
            va_id, vb_id = vertices[0], vertices[1]
            
            # Find edge with hook attached to va that we want to move to vb
            edge_to_modify = None
            hook_position = None
            
            for edge_id, vertex_sequence in egi.nu.items():
                for i, vertex_id in enumerate(vertex_sequence):
                    if vertex_id == va_id:
                        edge_to_modify = edge_id
                        hook_position = i
                        break
                if edge_to_modify:
                    break
            
            if not edge_to_modify:
                return TransformationResult(False, None, "No edge found attached to source vertex", {})
            
            # Create new nu mapping with vertex replaced
            new_nu = dict(egi.nu)
            old_sequence = list(new_nu[edge_to_modify])
            old_sequence[hook_position] = vb_id
            new_nu[edge_to_modify] = tuple(old_sequence)
            
            result_egi = RelationalGraphWithCuts(
                V=egi.V,
                E=egi.E,
                nu=frozendict(new_nu),
                sheet=egi.sheet,
                Cut=egi.Cut,
                area=egi.area,
                rel=egi.rel
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
                    "hook_position": hook_position
                }
            )
            
        except Exception as e:
            return TransformationResult(False, None, str(e), {})
    
    def _get_vertex_by_id(self, egi: RelationalGraphWithCuts, vertex_id: ElementID) -> Optional[Vertex]:
        """Get vertex by ID."""
        for v in egi.V:
            if v.id == vertex_id:
                return v
        return None
    
    def _get_vertex_context(self, egi: RelationalGraphWithCuts, vertex_id: ElementID) -> ElementID:
        """Get the context (area) containing this vertex."""
        for area_id, contents in egi.area.items():
            if vertex_id in contents:
                return area_id
        return egi.sheet  # Default to sheet
    
    def _vertices_on_same_ligature(self, egi: RelationalGraphWithCuts, va_id: ElementID, vb_id: ElementID) -> bool:
        """Check if two vertices are connected by identity edges (same ligature)."""
        # Build ligature graph from identity edges
        identity_edges = []
        for edge_id, vertex_sequence in egi.nu.items():
            if egi.rel.get(edge_id) == "=":  # Identity relation
                if len(vertex_sequence) == 2:
                    identity_edges.append((vertex_sequence[0], vertex_sequence[1]))
        
        # Use graph traversal to check connectivity
        return self._vertices_connected_by_identity(identity_edges, va_id, vb_id)
    
    def _vertices_connected_by_identity(self, identity_edges: List[Tuple[ElementID, ElementID]], 
                                      va_id: ElementID, vb_id: ElementID) -> bool:
        """Check if two vertices are connected through identity edges."""
        # Build adjacency list
        graph = {}
        for v1, v2 in identity_edges:
            if v1 not in graph:
                graph[v1] = []
            if v2 not in graph:
                graph[v2] = []
            graph[v1].append(v2)
            graph[v2].append(v1)
        
        # BFS to check connectivity
        if va_id not in graph or vb_id not in graph:
            return False
        
        visited = set()
        queue = [va_id]
        visited.add(va_id)
        
        while queue:
            current = queue.pop(0)
            if current == vb_id:
                return True
            
            for neighbor in graph.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        return False


class ExtendRestrictLigatureRule(FormalTransformationRule):
    """
    Lemma 16.2: Extending or Restricting a Ligature in a Context
    Allows adding new identity networks to existing ligatures.
    """
    
    def get_rule_name(self) -> str:
        return "EXTEND_LIGATURE (Extend or Restrict Ligature)"
    
    def check_preconditions(self, context: TransformationContext) -> Tuple[bool, Optional[str]]:
        """
        Requires a vertex on an existing ligature and specification of new identity network.
        """
        if len(context.selected_subgraph) != 1:
            return False, "Must select exactly one vertex for ligature extension"
        
        vertex_id = next(iter(context.selected_subgraph))
        egi = context.source_egi
        
        # Verify it's a vertex
        if not any(v.id == vertex_id for v in egi.V):
            return False, "Selected element must be a vertex"
        
        # Check if vertex is on a ligature (has identity connections)
        has_identity_connections = False
        for edge_id, vertex_sequence in egi.nu.items():
            if egi.rel.get(edge_id) == "=" and vertex_id in vertex_sequence:
                has_identity_connections = True
                break
        
        if not has_identity_connections:
            return False, "Selected vertex must be on an existing ligature"
        
        return True, None
    
    def apply_transformation(self, context: TransformationContext) -> TransformationResult:
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
            identity_edge_1_id = ElementID(f"id_edge_{base_vertex_id}_{new_vertex_1_id}")
            identity_edge_2_id = ElementID(f"id_edge_{new_vertex_1_id}_{new_vertex_2_id}")
            
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
            current_area_contents = new_area_mapping.get(base_vertex_context, frozenset())
            new_area_mapping[base_vertex_context] = current_area_contents | frozenset([
                new_vertex_1_id, new_vertex_2_id, identity_edge_1_id, identity_edge_2_id
            ])
            
            result_egi = RelationalGraphWithCuts(
                V=new_vertices,
                E=new_edges,
                nu=frozendict(new_nu),
                sheet=egi.sheet,
                Cut=egi.Cut,
                area=frozendict(new_area_mapping),
                rel=frozendict(new_rel)
            )
            
            return TransformationResult(
                success=True,
                result_egi=result_egi,
                error_message=None,
                changes_made={
                    "rule": "EXTEND_LIGATURE",
                    "base_vertex": str(base_vertex_id),
                    "new_vertices": [str(new_vertex_1_id), str(new_vertex_2_id)],
                    "new_identity_edges": [str(identity_edge_1_id), str(identity_edge_2_id)],
                    "context": str(base_vertex_context)
                }
            )
            
        except Exception as e:
            return TransformationResult(False, None, str(e), {})
    
    def _get_vertex_context(self, egi: RelationalGraphWithCuts, vertex_id: ElementID) -> ElementID:
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
    
    def check_preconditions(self, context: TransformationContext) -> Tuple[bool, Optional[str]]:
        """
        Requires selection of ligature vertices and specification of target vertex.
        """
        if len(context.selected_subgraph) < 2:
            return False, "Must select at least 2 vertices forming a ligature for retraction"
        
        egi = context.source_egi
        selected_vertices = list(context.selected_subgraph)
        
        # Verify all selected elements are vertices
        for vertex_id in selected_vertices:
            if not any(v.id == vertex_id for v in egi.V):
                return False, f"Selected element {vertex_id} is not a vertex"
        
        # Check if vertices form a connected ligature
        if not self._vertices_form_ligature(egi, selected_vertices):
            return False, "Selected vertices must form a connected ligature"
        
        # Check if all vertices are in the same context
        contexts = set()
        for vertex_id in selected_vertices:
            vertex_context = self._get_vertex_context(egi, vertex_id)
            contexts.add(vertex_context)
        
        if len(contexts) > 1:
            return False, "All ligature vertices must be in the same context for retraction"
        
        return True, None
    
    def apply_transformation(self, context: TransformationContext) -> TransformationResult:
        """Apply ligature retraction by collapsing to single vertex."""
        precondition_ok, error_msg = self.check_preconditions(context)
        if not precondition_ok:
            return TransformationResult(False, None, error_msg, {})
        
        try:
            egi = context.source_egi
            ligature_vertices = list(context.selected_subgraph)
            
            # Choose first vertex as target (w0 in Dau's notation)
            target_vertex_id = ligature_vertices[0]
            vertices_to_remove = set(ligature_vertices[1:])
            
            # Find all identity edges within the ligature
            ligature_edges = set()
            for edge_id, vertex_sequence in egi.nu.items():
                if (egi.rel.get(edge_id) == "=" and 
                    len(vertex_sequence) == 2 and
                    vertex_sequence[0] in ligature_vertices and
                    vertex_sequence[1] in ligature_vertices):
                    ligature_edges.add(edge_id)
            
            # Update nu mapping: redirect all edges from removed vertices to target vertex
            new_nu = dict(egi.nu)
            for edge_id, vertex_sequence in egi.nu.items():
                if edge_id not in ligature_edges:  # Don't modify ligature edges (they'll be removed)
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
            
            result_egi = RelationalGraphWithCuts(
                V=frozenset(new_vertices),
                E=frozenset(new_edges),
                nu=frozendict(new_nu),
                sheet=egi.sheet,
                Cut=egi.Cut,
                area=frozendict(new_area_mapping),
                rel=frozendict(new_rel)
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
                    "ligature_size": len(ligature_vertices)
                }
            )
            
        except Exception as e:
            return TransformationResult(False, None, str(e), {})
    
    def _vertices_form_ligature(self, egi: RelationalGraphWithCuts, vertices: List[ElementID]) -> bool:
        """Check if vertices form a connected ligature via identity edges."""
        if len(vertices) < 2:
            return False
        
        # Build graph of identity connections
        identity_graph = {}
        for vertex_id in vertices:
            identity_graph[vertex_id] = set()
        
        for edge_id, vertex_sequence in egi.nu.items():
            if (egi.rel.get(edge_id) == "=" and 
                len(vertex_sequence) == 2 and
                vertex_sequence[0] in vertices and
                vertex_sequence[1] in vertices):
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
    
    def _get_vertex_context(self, egi: RelationalGraphWithCuts, vertex_id: ElementID) -> ElementID:
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
    
    def check_preconditions(self, context: TransformationContext) -> Tuple[bool, Optional[str]]:
        """
        Requires selection of ligature vertices and specification of new structure.
        """
        if len(context.selected_subgraph) < 2:
            return False, "Must select at least 2 vertices forming a ligature for rearrangement"
        
        egi = context.source_egi
        selected_vertices = list(context.selected_subgraph)
        
        # Verify all selected elements are vertices
        for vertex_id in selected_vertices:
            if not any(v.id == vertex_id for v in egi.V):
                return False, f"Selected element {vertex_id} is not a vertex"
        
        # Check if vertices form a connected ligature
        if not self._vertices_form_ligature(egi, selected_vertices):
            return False, "Selected vertices must form a connected ligature"
        
        # Check if all vertices are in the same context
        contexts = set()
        for vertex_id in selected_vertices:
            vertex_context = self._get_vertex_context(egi, vertex_id)
            contexts.add(vertex_context)
        
        if len(contexts) > 1:
            return False, "All ligature vertices must be in the same context for rearrangement"
        
        return True, None
    
    def apply_transformation(self, context: TransformationContext) -> TransformationResult:
        """Apply ligature rearrangement by replacing structure."""
        precondition_ok, error_msg = self.check_preconditions(context)
        if not precondition_ok:
            return TransformationResult(False, None, error_msg, {})
        
        try:
            egi = context.source_egi
            ligature_vertices = list(context.selected_subgraph)
            ligature_context = self._get_vertex_context(egi, ligature_vertices[0])
            
            # Step 1: Retract existing ligature to single vertex
            retraction_rule = RetractLigatureRule()
            retraction_context = TransformationContext(
                source_egi=egi,
                target_area=ligature_context,
                selected_subgraph=frozenset(ligature_vertices),
                area_polarity=context.area_polarity,
                nesting_depth=context.nesting_depth
            )
            
            retraction_result = retraction_rule.apply_transformation(retraction_context)
            if not retraction_result.success:
                return TransformationResult(False, None, f"Retraction failed: {retraction_result.error_message}", {})
            
            intermediate_egi = retraction_result.result_egi
            target_vertex = ligature_vertices[0]  # The vertex we retracted to
            
            # Step 2: Create new ligature structure by directly adding vertices and identity edges
            # Since we retracted to a single vertex, we need to manually create the new arrangement
            from egi_core_dau import Vertex, Edge
            import uuid
            
            # Create new vertices for the rearranged ligature
            new_vertex_id = ElementID(f"{target_vertex}_rearranged")
            new_vertex = Vertex(new_vertex_id)
            
            # Create identity edge connecting original and new vertex
            identity_edge_id = ElementID(f"id_{target_vertex}_{new_vertex_id}")
            identity_edge = Edge(identity_edge_id)
            
            # Update EGI components
            new_vertices = intermediate_egi.V | {new_vertex}
            new_edges = intermediate_egi.E | {identity_edge}
            
            # Update nu mapping for the identity edge
            new_nu = dict(intermediate_egi.nu)
            new_nu[identity_edge_id] = (target_vertex, new_vertex_id)
            
            # Update area mapping to include new elements in same context
            new_area = dict(intermediate_egi.area)
            current_area_contents = set(new_area[ligature_context])
            new_area[ligature_context] = frozenset(current_area_contents | {new_vertex_id, identity_edge_id})
            
            # Update relation mapping
            new_rel = dict(intermediate_egi.rel)
            new_rel[identity_edge_id] = "="
            
            # Create result EGI
            result_egi = RelationalGraphWithCuts(
                V=new_vertices,
                E=new_edges,
                nu=frozendict(new_nu),
                sheet=intermediate_egi.sheet,
                Cut=intermediate_egi.Cut,
                area=frozendict(new_area),
                rel=frozendict(new_rel)
            )
            
            extension_result = TransformationResult(True, result_egi, None, {
                "rule": "REARRANGE_LIGATURE",
                "rearranged_vertex": str(target_vertex),
                "new_vertex": str(new_vertex_id),
                "identity_edge": str(identity_edge_id),
                "context": str(ligature_context)
            })
            
            return TransformationResult(
                success=True,
                result_egi=extension_result.result_egi,
                error_message=None,
                changes_made={
                    "rule": "REARRANGE_LIGATURE",
                    "original_vertices": [str(v) for v in ligature_vertices],
                    "context": str(ligature_context),
                    "retraction_changes": retraction_result.changes_made,
                    "extension_changes": extension_result.changes_made
                }
            )
            
        except Exception as e:
            return TransformationResult(False, None, str(e), {})
    
    def _vertices_form_ligature(self, egi: RelationalGraphWithCuts, vertices: List[ElementID]) -> bool:
        """Check if vertices form a connected ligature via identity edges."""
        if len(vertices) < 2:
            return False
        
        # Build graph of identity connections
        identity_graph = {}
        for vertex_id in vertices:
            identity_graph[vertex_id] = set()
        
        for edge_id, vertex_sequence in egi.nu.items():
            if (egi.rel.get(edge_id) == "=" and 
                len(vertex_sequence) == 2 and
                vertex_sequence[0] in vertices and
                vertex_sequence[1] in vertices):
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
    
    def _get_vertex_context(self, egi: RelationalGraphWithCuts, vertex_id: ElementID) -> ElementID:
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
            "REARRANGE_LIGATURE": LigatureRearrangementRule()
        }
    
    def apply_rule(self, rule_name: str, source_egi: RelationalGraphWithCuts,
                   target_area: ElementID, selected_subgraph: FrozenSet[ElementID]) -> TransformationResult:
        """Apply a ligature manipulation rule to an EGI."""
        
        if rule_name not in self.rules:
            return TransformationResult(
                success=False,
                result_egi=None,
                error_message=f"Unknown ligature rule: {rule_name}",
                changes_made={}
            )
        
        rule = self.rules[rule_name]
        
        # Create transformation context (ligature rules don't depend on polarity)
        from formal_transformation_rules import TransformationContext, AreaPolarity
        context = TransformationContext(
            source_egi=source_egi,
            target_area=target_area,
            selected_subgraph=selected_subgraph,
            area_polarity=AreaPolarity.POSITIVE,  # Not relevant for ligature rules
            nesting_depth=0  # Not relevant for ligature rules
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
    from egi_core_dau import RelationalGraphWithCuts, ElementID, Vertex, Edge
    
    # Create vertices connected by identity
    vertex_a = Vertex(ElementID("A"))
    vertex_b = Vertex(ElementID("B"))
    vertex_c = Vertex(ElementID("C"))
    
    # Create identity edge connecting A and B
    identity_edge = Edge(ElementID("id_AB"))
    
    test_egi = RelationalGraphWithCuts(
        V=frozenset([vertex_a, vertex_b, vertex_c]),
        E=frozenset([identity_edge]),
        nu=frozendict({
            ElementID("id_AB"): (ElementID("A"), ElementID("B"))
        }),
        sheet=ElementID("sheet"),
        Cut=frozenset(),
        area=frozendict({
            ElementID("sheet"): frozenset([ElementID("A"), ElementID("B"), ElementID("C"), ElementID("id_AB")])
        }),
        rel=frozendict({
            ElementID("id_AB"): "="
        })
    )
    
    engine = LigatureManipulationEngine()
    
    print(f"Starting EGI: {len(test_egi.V)} vertices, {len(test_egi.E)} edges")
    print(f"Identity connections: A—B (via identity edge)")
    print()
    
    # Test ligature extension
    print("🎯 Test 1: Extend Ligature from vertex A")
    result = engine.apply_rule(
        "EXTEND_LIGATURE",
        test_egi,
        ElementID("sheet"),
        frozenset([ElementID("A")])
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
