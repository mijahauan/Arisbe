#!/usr/bin/env python3
"""
Dau's Formal Subgraph Model (Definition 12.10)
Implements mathematically rigorous subgraphs for Existential Graph transformations

CHANGES: Replaces informal EGIF probe matching with Dau's formal subgraph model.
Ensures mathematical compliance with Definition 12.10 constraints including edge
completeness, context consistency, and proper area mapping.
"""

import sys
import os
from typing import Set, Dict, Optional, List, Tuple, FrozenSet
from dataclasses import dataclass, field
from frozendict import frozendict

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from egi_core_dau import (
        RelationalGraphWithCuts, Vertex, Edge, Cut, ElementID,
        create_vertex, create_edge, create_cut
    )
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure the DAU-compliant modules are available")
    sys.exit(1)


class SubgraphValidationError(Exception):
    """Exception raised when subgraph violates Definition 12.10 constraints."""
    pass


@dataclass(frozen=True)
class DAUSubgraph:
    """
    Formal subgraph according to Dau's Definition 12.10.
    
    A subgraph G' := (V',E',ν',>',Cut',area') of G := (V,E,ν,>,Cut,area)
    in context >' satisfies all constraints from Definition 12.10.
    """
    
    # Core components (following Definition 12.10)
    V_prime: FrozenSet[Vertex]                    # Vertices in subgraph
    E_prime: FrozenSet[Edge]                      # Edges in subgraph  
    Cut_prime: FrozenSet[Cut]                     # Cuts in subgraph
    root_context: ElementID                       # >' - root context of subgraph
    
    # Derived mappings (computed from parent graph)
    nu_prime: frozendict                          # ν' = ν|E' - vertex mapping restriction
    area_prime: frozendict                        # area' - area mapping for subgraph
    
    # Reference to parent graph for validation
    parent_graph: RelationalGraphWithCuts
    
    # Additional properties
    is_closed: bool = field(default=False)       # Whether this is a closed subgraph
    
    def __post_init__(self):
        """Validate Definition 12.10 constraints after initialization."""
        self._validate_definition_12_10()
    
    def _validate_definition_12_10(self):
        """Validate all constraints from Dau's Definition 12.10."""
        
        # Constraint 1: Subset relations
        self._validate_subset_relations()
        
        # Constraint 2: Root context validity  
        self._validate_root_context()
        
        # Constraint 3: Vertex mapping preservation
        self._validate_vertex_mapping()
        
        # Constraint 4: Area mapping constraints
        self._validate_area_mapping()
        
        # Constraint 5: Context consistency
        self._validate_context_consistency()
        
        # Constraint 6: Edge completeness
        self._validate_edge_completeness()
        
        # Constraint 7: Vertex completeness (for closed subgraphs)
        if self.is_closed:
            self._validate_vertex_completeness()
    
    def _validate_subset_relations(self):
        """Validate V' ⊆ V, E' ⊆ E, Cut' ⊆ Cut."""
        parent_V = {v.id for v in self.parent_graph.V}
        parent_E = {e.id for e in self.parent_graph.E}
        parent_Cut = {c.id for c in self.parent_graph.Cut}
        
        subgraph_V = {v.id for v in self.V_prime}
        subgraph_E = {e.id for e in self.E_prime}
        subgraph_Cut = {c.id for c in self.Cut_prime}
        
        if not subgraph_V.issubset(parent_V):
            raise SubgraphValidationError(f"V' not subset of V: {subgraph_V - parent_V}")
        
        if not subgraph_E.issubset(parent_E):
            raise SubgraphValidationError(f"E' not subset of E: {subgraph_E - parent_E}")
        
        if not subgraph_Cut.issubset(parent_Cut):
            raise SubgraphValidationError(f"Cut' not subset of Cut: {subgraph_Cut - parent_Cut}")
    
    def _validate_root_context(self):
        """Validate >' ∈ Cut ∪ {>}."""
        all_contexts = {c.id for c in self.parent_graph.Cut} | {self.parent_graph.sheet}
        
        if self.root_context not in all_contexts:
            raise SubgraphValidationError(f"Root context {self.root_context} not in Cut ∪ {{>}}")
    
    def _validate_vertex_mapping(self):
        """Validate ν' = ν|E' (restriction of ν to E')."""
        for edge in self.E_prime:
            parent_mapping = self.parent_graph.nu.get(edge.id)
            subgraph_mapping = self.nu_prime.get(edge.id)
            
            if parent_mapping != subgraph_mapping:
                raise SubgraphValidationError(
                    f"Vertex mapping mismatch for edge {edge.id}: "
                    f"parent={parent_mapping}, subgraph={subgraph_mapping}"
                )
    
    def _validate_area_mapping(self):
        """Validate area mapping constraints from Definition 12.10."""
        # area'(>') = area(>') ∩ (V' ∪ E' ∪ Cut')
        subgraph_elements = ({v.id for v in self.V_prime} | 
                           {e.id for e in self.E_prime} | 
                           {c.id for c in self.Cut_prime})
        
        parent_root_area = self.parent_graph.area.get(self.root_context, frozenset())
        expected_root_area = parent_root_area & subgraph_elements
        actual_root_area = self.area_prime.get(self.root_context, frozenset())
        
        if expected_root_area != actual_root_area:
            raise SubgraphValidationError(
                f"Root area mapping incorrect: expected={expected_root_area}, actual={actual_root_area}"
            )
        
        # area'(c') = area(c') for each c' ∈ Cut'
        for cut in self.Cut_prime:
            parent_area = self.parent_graph.area.get(cut.id, frozenset())
            subgraph_area = self.area_prime.get(cut.id, frozenset())
            
            if parent_area != subgraph_area:
                raise SubgraphValidationError(
                    f"Area mapping mismatch for cut {cut.id}: "
                    f"parent={parent_area}, subgraph={subgraph_area}"
                )
    
    def _validate_context_consistency(self):
        """Validate ctx(x) ∈ Cut' ∪ {>'} for each x ∈ V' ∪ E' ∪ Cut'."""
        valid_contexts = {c.id for c in self.Cut_prime} | {self.root_context}
        
        # Check vertices
        for vertex in self.V_prime:
            vertex_context = self.parent_graph.get_context(vertex.id)
            if vertex_context not in valid_contexts:
                raise SubgraphValidationError(
                    f"Vertex {vertex.id} context {vertex_context} not in Cut' ∪ {{>'}}"
                )
        
        # Check edges
        for edge in self.E_prime:
            edge_context = self.parent_graph.get_context(edge.id)
            if edge_context not in valid_contexts:
                raise SubgraphValidationError(
                    f"Edge {edge.id} context {edge_context} not in Cut' ∪ {{>'}}"
                )
        
        # Check cuts
        for cut in self.Cut_prime:
            cut_context = self.parent_graph.get_context(cut.id)
            if cut_context not in valid_contexts:
                raise SubgraphValidationError(
                    f"Cut {cut.id} context {cut_context} not in Cut' ∪ {{>'}}"
                )
    
    def _validate_edge_completeness(self):
        """Validate Ve' ⊆ V' for each edge e' ∈ E' (edge completeness)."""
        subgraph_vertex_ids = {v.id for v in self.V_prime}
        
        for edge in self.E_prime:
            incident_vertices = set(self.parent_graph.get_incident_vertices(edge.id))
            
            if not incident_vertices.issubset(subgraph_vertex_ids):
                missing_vertices = incident_vertices - subgraph_vertex_ids
                raise SubgraphValidationError(
                    f"Edge {edge.id} has incident vertices not in V': {missing_vertices}"
                )
    
    def _validate_vertex_completeness(self):
        """Validate Ev' ⊆ E' for each vertex v' ∈ V' (vertex completeness for closed subgraphs)."""
        subgraph_edge_ids = {e.id for e in self.E_prime}
        
        for vertex in self.V_prime:
            incident_edges = set()
            
            # Find all edges incident to this vertex in parent graph
            for edge in self.parent_graph.E:
                if vertex.id in self.parent_graph.get_incident_vertices(edge.id):
                    incident_edges.add(edge.id)
            
            if not incident_edges.issubset(subgraph_edge_ids):
                missing_edges = incident_edges - subgraph_edge_ids
                raise SubgraphValidationError(
                    f"Vertex {vertex.id} has incident edges not in E': {missing_edges}"
                )
    
    @classmethod
    def create_subgraph(cls, parent_graph: RelationalGraphWithCuts,
                       vertex_ids: Set[str], edge_ids: Set[str], cut_ids: Set[str],
                       root_context: ElementID, is_closed: bool = False) -> 'DAUSubgraph':
        """
        Create a DAUSubgraph with proper validation.
        
        Args:
            parent_graph: The parent graph containing this subgraph
            vertex_ids: Set of vertex IDs to include in subgraph
            edge_ids: Set of edge IDs to include in subgraph  
            cut_ids: Set of cut IDs to include in subgraph
            root_context: Root context >' for the subgraph
            is_closed: Whether this should be a closed subgraph
            
        Returns:
            Validated DAUSubgraph instance
            
        Raises:
            SubgraphValidationError: If subgraph violates Definition 12.10
        """
        
        # Build vertex, edge, and cut sets
        V_prime = frozenset(v for v in parent_graph.V if v.id in vertex_ids)
        E_prime = frozenset(e for e in parent_graph.E if e.id in edge_ids)
        Cut_prime = frozenset(c for c in parent_graph.Cut if c.id in cut_ids)
        
        # Build restricted vertex mapping
        nu_prime_dict = {}
        for edge in E_prime:
            nu_prime_dict[edge.id] = parent_graph.nu[edge.id]
        nu_prime = frozendict(nu_prime_dict)
        
        # Build area mapping
        area_prime_dict = {}
        
        # area'(>') = area(>') ∩ (V' ∪ E' ∪ Cut')
        subgraph_elements = vertex_ids | edge_ids | cut_ids
        parent_root_area = parent_graph.area.get(root_context, frozenset())
        area_prime_dict[root_context] = parent_root_area & subgraph_elements
        
        # area'(c') = area(c') for each c' ∈ Cut'
        for cut in Cut_prime:
            area_prime_dict[cut.id] = parent_graph.area.get(cut.id, frozenset())
        
        area_prime = frozendict(area_prime_dict)
        
        return cls(
            V_prime=V_prime,
            E_prime=E_prime,
            Cut_prime=Cut_prime,
            root_context=root_context,
            nu_prime=nu_prime,
            area_prime=area_prime,
            parent_graph=parent_graph,
            is_closed=is_closed
        )
    
    def get_all_element_ids(self) -> Set[ElementID]:
        """Get all element IDs in this subgraph."""
        return ({v.id for v in self.V_prime} | 
                {e.id for e in self.E_prime} | 
                {c.id for c in self.Cut_prime})
    
    def contains_element(self, element_id: ElementID) -> bool:
        """Check if element is contained in this subgraph."""
        return element_id in self.get_all_element_ids()
    
    def is_enclosed_by(self, context_id: ElementID) -> bool:
        """Check if this subgraph is enclosed by the given context."""
        return self.parent_graph.get_context(self.root_context) == context_id or \
               self.parent_graph.is_context_enclosed_by(self.root_context, context_id)
    
    def get_context_polarity(self) -> str:
        """Get the polarity (positive/negative) of the subgraph's root context."""
        if self.parent_graph.is_positive_context(self.root_context):
            return "positive"
        else:
            return "negative"
    
    def __str__(self) -> str:
        """String representation of the subgraph."""
        return (f"DAUSubgraph(V'={len(self.V_prime)}, E'={len(self.E_prime)}, "
                f"Cut'={len(self.Cut_prime)}, >'={self.root_context}, "
                f"closed={self.is_closed})")
    
    def __repr__(self) -> str:
        return self.__str__()


def create_minimal_subgraph(parent_graph: RelationalGraphWithCuts,
                          element_ids: Set[ElementID],
                          root_context: Optional[ElementID] = None) -> DAUSubgraph:
    """
    Create minimal subgraph containing the given elements.
    
    Automatically includes all necessary elements to satisfy Definition 12.10
    constraints (edge completeness, context consistency, etc.).
    
    Args:
        parent_graph: Parent graph
        element_ids: Set of element IDs that must be included
        root_context: Root context (auto-determined if None)
        
    Returns:
        Minimal valid DAUSubgraph
    """
    
    vertices = set()
    edges = set()
    cuts = set()
    
    # Categorize initial elements
    for element_id in element_ids:
        if any(v.id == element_id for v in parent_graph.V):
            vertices.add(element_id)
        elif any(e.id == element_id for e in parent_graph.E):
            edges.add(element_id)
        elif any(c.id == element_id for c in parent_graph.Cut):
            cuts.add(element_id)
    
    # Apply edge completeness: if edge included, include all incident vertices
    for edge_id in list(edges):
        incident_vertices = parent_graph.get_incident_vertices(edge_id)
        vertices.update(incident_vertices)
    
    # Determine root context if not provided
    if root_context is None:
        # Find the least common ancestor context of all elements
        contexts = []
        for element_id in vertices | edges | cuts:
            contexts.append(parent_graph.get_context(element_id))
        
        # For simplicity, use the first context (could be improved)
        root_context = contexts[0] if contexts else parent_graph.sheet
    
    # Include necessary cuts to satisfy context consistency
    all_contexts = set()
    for element_id in vertices | edges | cuts:
        element_context = parent_graph.get_context(element_id)
        all_contexts.add(element_context)
    
    # Add cuts that are contexts of our elements (excluding root context)
    for context_id in all_contexts:
        if context_id != root_context and context_id != parent_graph.sheet:
            cuts.add(context_id)
    
    return DAUSubgraph.create_subgraph(
        parent_graph=parent_graph,
        vertex_ids=vertices,
        edge_ids=edges,
        cut_ids=cuts,
        root_context=root_context,
        is_closed=False
    )


if __name__ == "__main__":
    print("Dau's formal subgraph model loaded successfully")
    print("Use DAUSubgraph.create_subgraph() to create mathematically rigorous subgraphs")
    print("All subgraphs automatically validate Definition 12.10 constraints")

