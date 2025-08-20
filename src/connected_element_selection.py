"""
Connected Element Selection System for EGI GUI

This module implements selection highlighting that shows the logical dependencies
between predicates, vertices, and ligatures in Existential Graphs. When a user
selects an element, all connected elements are highlighted to show the impact
of potential operations like deletion or movement.

Based on Dau's canonical formalism where ligatures represent identity relationships
that can cross cut boundaries, maintaining logical coherence across contexts.
"""

from typing import Set, Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge


class SelectionType(Enum):
    """Types of element selection in the EGI GUI"""
    VERTEX = "vertex"
    PREDICATE = "predicate" 
    LIGATURE = "ligature"
    CUT = "cut"
    AREA = "area"


@dataclass
class SelectionHighlight:
    """Represents elements to highlight for a selection"""
    primary_element: str  # The directly selected element ID
    connected_vertices: Set[str]  # Vertices connected via ligatures
    connected_predicates: Set[str]  # Predicates connected via ligatures
    affected_ligatures: Set[Tuple[str, str]]  # Ligature connections (vertex_id, predicate_id)
    crossing_cuts: Set[str]  # Cut IDs that ligatures cross
    logical_area: str  # The logical area containing the primary element
    single_object_ligatures: Set[Tuple[str, ...]]  # Single-object ligature networks (vertex_ids)


class ConnectedElementSelector:
    """
    Analyzes EGI structure to determine connected elements for selection highlighting.
    
    Implements Dau's principle that ligatures represent identity relationships that
    transcend cut boundaries, so selection must show all logically connected elements
    regardless of their spatial containment in different areas.
    """
    
    def __init__(self, egi: RelationalGraphWithCuts):
        self.egi = egi
        self._ligature_cache = {}
        self._single_object_ligatures = {}  # Cache for single-object ligature detection
        self._rebuild_ligature_cache()
    
    def _rebuild_ligature_cache(self):
        """Build cache of ligature connections for efficient lookup"""
        self._ligature_cache = {
            'vertex_to_predicates': {},  # vertex_id -> set of predicate_ids
            'predicate_to_vertices': {},  # predicate_id -> set of vertex_ids
            'ligature_connections': set()  # set of (vertex_id, predicate_id) tuples
        }
        
        # Build connections from nu mapping
        for edge_id, vertex_mappings in self.egi.nu.items():
            if edge_id not in self._ligature_cache['predicate_to_vertices']:
                self._ligature_cache['predicate_to_vertices'][edge_id] = set()
            
            for vertex_id in vertex_mappings:
                # Add vertex -> predicate mapping
                if vertex_id not in self._ligature_cache['vertex_to_predicates']:
                    self._ligature_cache['vertex_to_predicates'][vertex_id] = set()
                self._ligature_cache['vertex_to_predicates'][vertex_id].add(edge_id)
                
                # Add predicate -> vertex mapping
                self._ligature_cache['predicate_to_vertices'][edge_id].add(vertex_id)
                
                # Add ligature connection
                self._ligature_cache['ligature_connections'].add((vertex_id, edge_id))
        
        # Build single-object ligature cache
        self._detect_single_object_ligatures()
    
    def _detect_single_object_ligatures(self):
        """
        Detect single-object ligatures using Dau's formalism.
        
        A single-object ligature is a connected component of lines of identity where
        all branches refer to the same individual object. This is determined by
        analyzing the branching structure and semantic constraints.
        """
        self._single_object_ligatures = {}
        
        # Find connected components of vertices through ligatures
        visited_vertices = set()
        ligature_networks = []
        
        for vertex_id in self._ligature_cache['vertex_to_predicates']:
            if vertex_id in visited_vertices:
                continue
                
            # Perform DFS to find connected component
            network = self._find_ligature_network(vertex_id, visited_vertices)
            if len(network) > 1:  # Only consider multi-vertex networks
                ligature_networks.append(network)
        
        # Analyze each network to determine if it's single-object
        for network in ligature_networks:
            if self._is_single_object_network(network):
                # Store as single-object ligature
                network_key = tuple(sorted(network))
                self._single_object_ligatures[network_key] = {
                    'vertices': network,
                    'is_decomposable': self._is_decomposable_ligature(network)
                }
    
    def _find_ligature_network(self, start_vertex: str, visited: set) -> set:
        """Find all vertices connected to start_vertex through ligatures (DFS)"""
        network = set()
        stack = [start_vertex]
        
        while stack:
            vertex_id = stack.pop()
            if vertex_id in visited:
                continue
                
            visited.add(vertex_id)
            network.add(vertex_id)
            
            # Find connected vertices through shared predicates
            predicates = self._ligature_cache['vertex_to_predicates'].get(vertex_id, set())
            for pred_id in predicates:
                connected_vertices = self._ligature_cache['predicate_to_vertices'].get(pred_id, set())
                for connected_vertex in connected_vertices:
                    if connected_vertex not in visited:
                        stack.append(connected_vertex)
        
        return network
    
    def _is_single_object_network(self, vertex_network: set) -> bool:
        """
        Determine if a ligature network represents a single object.
        
        Based on Dau's criteria:
        1. All vertices in the network should have compatible semantic roles
        2. No contradictory predicate attachments
        3. Structural consistency for identity interpretation
        """
        # For now, implement a conservative heuristic:
        # A network is single-object if it forms a connected tree structure
        # without semantic contradictions
        
        if len(vertex_network) <= 1:
            return True
            
        # Check for structural consistency
        total_connections = 0
        for vertex_id in vertex_network:
            predicates = self._ligature_cache['vertex_to_predicates'].get(vertex_id, set())
            # Count connections within the network
            for pred_id in predicates:
                pred_vertices = self._ligature_cache['predicate_to_vertices'].get(pred_id, set())
                network_connections = pred_vertices.intersection(vertex_network)
                if len(network_connections) > 1:
                    total_connections += 1
        
        # Single-object ligatures typically have tree-like structure
        # (n-1 connections for n vertices in a tree)
        expected_connections = len(vertex_network) - 1
        return total_connections >= expected_connections
    
    def _is_decomposable_ligature(self, vertex_network: set) -> bool:
        """
        Determine if a single-object ligature can be decomposed for parsing.
        
        Decomposable ligatures can be simplified during graph analysis.
        """
        # Simple heuristic: ligatures with more than 2 vertices are decomposable
        return len(vertex_network) > 2
    
    def get_single_object_ligatures_for_vertex(self, vertex_id: str) -> Set[Tuple[str, ...]]:
        """Get all single-object ligatures containing the given vertex"""
        containing_ligatures = set()
        for ligature_key, ligature_info in self._single_object_ligatures.items():
            if vertex_id in ligature_info['vertices']:
                containing_ligatures.add(ligature_key)
        return containing_ligatures
    
    def get_selection_highlight(self, element_id: str, selection_type: SelectionType) -> SelectionHighlight:
        """
        Get all elements that should be highlighted when the given element is selected.
        
        Args:
            element_id: ID of the selected element
            selection_type: Type of element being selected
            
        Returns:
            SelectionHighlight containing all connected elements
        """
        if selection_type == SelectionType.VERTEX:
            return self._get_vertex_selection(element_id)
        elif selection_type == SelectionType.PREDICATE:
            return self._get_predicate_selection(element_id)
        elif selection_type == SelectionType.LIGATURE:
            return self._get_ligature_selection(element_id)
        elif selection_type == SelectionType.CUT:
            return self._get_cut_selection(element_id)
        else:
            # Default empty selection
            return SelectionHighlight(
                primary_element=element_id,
                connected_vertices=set(),
                connected_predicates=set(),
                affected_ligatures=set(),
                crossing_cuts=set(),
                logical_area="",
                single_object_ligatures=set()
            )
    
    def _get_vertex_selection(self, vertex_id: str) -> SelectionHighlight:
        """Get selection highlight for a vertex"""
        connected_predicates = self._ligature_cache['vertex_to_predicates'].get(vertex_id, set())
        
        # Find all vertices connected through shared predicates (ligature branching)
        connected_vertices = set()
        for pred_id in connected_predicates:
            other_vertices = self._ligature_cache['predicate_to_vertices'].get(pred_id, set())
            connected_vertices.update(other_vertices - {vertex_id})
        
        # Build affected lines of identity (forming ligatures)
        affected_ligatures = set()
        for pred_id in connected_predicates:
            affected_ligatures.add((vertex_id, pred_id))
        
        # Find crossing cuts
        crossing_cuts = self._find_crossing_cuts(vertex_id, connected_predicates)
        
        # Get logical area
        logical_area = self._find_logical_area(vertex_id)
        
        # Get single-object ligatures containing this vertex
        single_object_ligatures = self.get_single_object_ligatures_for_vertex(vertex_id)
        
        return SelectionHighlight(
            primary_element=vertex_id,
            connected_vertices=connected_vertices,
            connected_predicates=connected_predicates,
            affected_ligatures=affected_ligatures,
            crossing_cuts=crossing_cuts,
            logical_area=logical_area,
            single_object_ligatures=single_object_ligatures
        )
    
    def _get_predicate_selection(self, predicate_id: str) -> SelectionHighlight:
        """Get selection highlight for a predicate"""
        connected_vertices = self._ligature_cache['predicate_to_vertices'].get(predicate_id, set())
        
        # Find predicates connected through shared vertices
        connected_predicates = set()
        for vertex_id in connected_vertices:
            other_predicates = self._ligature_cache['vertex_to_predicates'].get(vertex_id, set())
            connected_predicates.update(other_predicates - {predicate_id})
        
        # Build affected ligatures
        affected_ligatures = set()
        for vertex_id in connected_vertices:
            affected_ligatures.add((vertex_id, predicate_id))
        
        # Find crossing cuts
        crossing_cuts = self._find_crossing_cuts_for_predicate(predicate_id, connected_vertices)
        
        # Get logical area
        logical_area = self._find_logical_area(predicate_id)
        
        # Get single-object ligatures involving connected vertices
        single_object_ligatures = set()
        for vertex_id in connected_vertices:
            single_object_ligatures.update(self.get_single_object_ligatures_for_vertex(vertex_id))
        
        return SelectionHighlight(
            primary_element=predicate_id,
            connected_vertices=connected_vertices,
            connected_predicates=connected_predicates,
            affected_ligatures=affected_ligatures,
            crossing_cuts=crossing_cuts,
            logical_area=logical_area,
            single_object_ligatures=single_object_ligatures
        )
    
    def _get_ligature_selection(self, ligature_spec: str) -> SelectionHighlight:
        """Get selection highlight for a ligature (vertex_id:predicate_id)"""
        # Parse ligature specification
        if ':' in ligature_spec:
            vertex_id, predicate_id = ligature_spec.split(':', 1)
        else:
            # Fallback - treat as vertex selection
            return self._get_vertex_selection(ligature_spec)
        
        # Highlight both endpoints and their connections
        vertex_highlight = self._get_vertex_selection(vertex_id)
        predicate_highlight = self._get_predicate_selection(predicate_id)
        
        # Merge highlights
        return SelectionHighlight(
            primary_element=ligature_spec,
            connected_vertices=vertex_highlight.connected_vertices | predicate_highlight.connected_vertices,
            connected_predicates=vertex_highlight.connected_predicates | predicate_highlight.connected_predicates,
            affected_ligatures=vertex_highlight.affected_ligatures | predicate_highlight.affected_ligatures,
            crossing_cuts=vertex_highlight.crossing_cuts | predicate_highlight.crossing_cuts,
            logical_area=vertex_highlight.logical_area,
            single_object_ligatures=vertex_highlight.single_object_ligatures | predicate_highlight.single_object_ligatures
        )
    
    def _get_cut_selection(self, cut_id: str) -> SelectionHighlight:
        """Get selection highlight for a cut (shows all contained elements)"""
        # Find all elements in this cut's context
        contained_vertices = set()
        contained_predicates = set()
        
        # Find vertices in this area
        for vertex in self.egi.V:
            if self._find_logical_area(vertex.id) == cut_id:
                contained_vertices.add(vertex.id)
        
        # Find predicates in this area  
        for edge in self.egi.E:
            if self._find_logical_area(edge.id) == cut_id:
                contained_predicates.add(edge.id)
        
        # Find all ligatures involving these elements
        affected_ligatures = set()
        for vertex_id in contained_vertices:
            predicates = self._ligature_cache['vertex_to_predicates'].get(vertex_id, set())
            for pred_id in predicates:
                affected_ligatures.add((vertex_id, pred_id))
        
        # Get single-object ligatures involving contained vertices
        single_object_ligatures = set()
        for vertex_id in contained_vertices:
            single_object_ligatures.update(self.get_single_object_ligatures_for_vertex(vertex_id))
        
        return SelectionHighlight(
            primary_element=cut_id,
            connected_vertices=contained_vertices,
            connected_predicates=contained_predicates,
            affected_ligatures=affected_ligatures,
            crossing_cuts=set(),  # Cut doesn't cross itself
            logical_area=cut_id,
            single_object_ligatures=single_object_ligatures
        )
    
    def _find_crossing_cuts(self, vertex_id: str, connected_predicates: Set[str]) -> Set[str]:
        """Find cuts that ligatures cross between vertex and its connected predicates"""
        crossing_cuts = set()
        vertex_area = self._find_logical_area(vertex_id)
        
        for pred_id in connected_predicates:
            pred_area = self._find_logical_area(pred_id)
            if vertex_area != pred_area:
                # Ligature crosses between different areas
                crossing_cuts.update(self._find_boundary_cuts(vertex_area, pred_area))
        
        return crossing_cuts
    
    def _find_crossing_cuts_for_predicate(self, predicate_id: str, connected_vertices: Set[str]) -> Set[str]:
        """Find cuts that ligatures cross between predicate and its connected vertices"""
        crossing_cuts = set()
        pred_area = self._find_logical_area(predicate_id)
        
        for vertex_id in connected_vertices:
            vertex_area = self._find_logical_area(vertex_id)
            if pred_area != vertex_area:
                # Ligature crosses between different areas
                crossing_cuts.update(self._find_boundary_cuts(pred_area, vertex_area))
        
        return crossing_cuts
    
    def _find_logical_area(self, element_id: str) -> str:
        """Find the logical area (context) containing an element"""
        # Check vertices
        for vertex in self.egi.V:
            if vertex.id == element_id:
                return self._get_vertex_context(vertex)
        
        # Check edges/predicates
        for edge in self.egi.E:
            if edge.id == element_id:
                return self._get_edge_context(edge)
        
        # Default to sheet
        return "sheet"
    
    def _get_vertex_context(self, vertex: Vertex) -> str:
        """Get the context containing a vertex"""
        # Find the most specific context containing this vertex using area mapping
        for area_id, area_contents in self.egi.area.items():
            if vertex.id in area_contents:
                return area_id
        return "sheet"
    
    def _get_edge_context(self, edge: Edge) -> str:
        """Get the context containing an edge"""
        # Find the most specific context containing this edge using area mapping
        for area_id, area_contents in self.egi.area.items():
            if edge.id in area_contents:
                return area_id
        return "sheet"
    
    def _find_boundary_cuts(self, area1: str, area2: str) -> Set[str]:
        """Find cuts that form boundaries between two logical areas"""
        # Simplified implementation - in practice this would analyze
        # the context hierarchy to find intervening cuts
        boundary_cuts = set()
        
        # If areas are different, there's at least one boundary
        if area1 != area2:
            # Add both areas as potential boundaries
            if area1 != "sheet":
                boundary_cuts.add(area1)
            if area2 != "sheet":
                boundary_cuts.add(area2)
        
        return boundary_cuts


class DeletionImpactAnalyzer:
    """
    Analyzes the impact of element deletion operations on ligatures and logical structure.
    
    Implements Dau's canonical rules for handling cut-crossing ligatures during
    vertex and predicate deletion operations.
    """
    
    def __init__(self, egi: RelationalGraphWithCuts, selector: ConnectedElementSelector):
        self.egi = egi
        self.selector = selector
    
    def analyze_vertex_deletion(self, vertex_id: str) -> Dict[str, any]:
        """
        Analyze the impact of deleting a vertex.
        
        Returns:
            Dictionary containing:
            - affected_ligatures: Ligatures that will be removed
            - orphaned_predicates: Predicates that lose all connections
            - remaining_connections: Ligatures that remain after deletion
            - cut_crossing_impact: Changes to cut-crossing ligature structure
        """
        highlight = self.selector.get_selection_highlight(vertex_id, SelectionType.VERTEX)
        
        # Ligatures that will be removed
        affected_ligatures = highlight.affected_ligatures
        
        # Check for orphaned predicates
        orphaned_predicates = set()
        for pred_id in highlight.connected_predicates:
            pred_vertices = self.selector._ligature_cache['predicate_to_vertices'].get(pred_id, set())
            if pred_vertices <= {vertex_id}:  # Only connected to this vertex
                orphaned_predicates.add(pred_id)
        
        # Remaining connections after deletion
        remaining_connections = set()
        for ligature in self.selector._ligature_cache['ligature_connections']:
            if ligature[0] != vertex_id:  # Vertex not involved
                remaining_connections.add(ligature)
        
        return {
            'affected_ligatures': affected_ligatures,
            'orphaned_predicates': orphaned_predicates,
            'remaining_connections': remaining_connections,
            'cut_crossing_impact': highlight.crossing_cuts,
            'logical_area': highlight.logical_area
        }
    
    def analyze_predicate_deletion(self, predicate_id: str) -> Dict[str, any]:
        """
        Analyze the impact of deleting a predicate.
        
        Returns:
            Dictionary containing:
            - affected_ligatures: Ligatures that will be removed
            - orphaned_vertices: Vertices that lose all connections
            - remaining_connections: Ligatures that remain after deletion
            - cut_crossing_impact: Changes to cut-crossing ligature structure
        """
        highlight = self.selector.get_selection_highlight(predicate_id, SelectionType.PREDICATE)
        
        # Ligatures that will be removed
        affected_ligatures = highlight.affected_ligatures
        
        # Check for orphaned vertices
        orphaned_vertices = set()
        for vertex_id in highlight.connected_vertices:
            vertex_predicates = self.selector._ligature_cache['vertex_to_predicates'].get(vertex_id, set())
            if vertex_predicates <= {predicate_id}:  # Only connected to this predicate
                orphaned_vertices.add(vertex_id)
        
        # Remaining connections after deletion
        remaining_connections = set()
        for ligature in self.selector._ligature_cache['ligature_connections']:
            if ligature[1] != predicate_id:  # Predicate not involved
                remaining_connections.add(ligature)
        
        return {
            'affected_ligatures': affected_ligatures,
            'orphaned_vertices': orphaned_vertices,
            'remaining_connections': remaining_connections,
            'cut_crossing_impact': highlight.crossing_cuts,
            'logical_area': highlight.logical_area
        }
