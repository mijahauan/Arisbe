"""
Ligature management system for Existential Graphs.

This module provides sophisticated algorithms for detecting, tracing,
and manipulating ligatures (connected components of identity relations)
in existential graphs.
"""

from __future__ import annotations
from typing import Dict, List, Set, Optional, Tuple, Iterator, Union
from pyrsistent import PMap, PSet, PVector
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    PMapType = PMap
    PSetType = PSet
else:
    PMapType = PMap
    PSetType = PSet

from .eg_types import (
    Node, Edge, Ligature,
    NodeId, EdgeId, LigatureId, ItemId,
    new_ligature_id, LigatureError, ValidationError
)

class LigatureManager:
    """
    Manages ligatures (connected components of identity) in an existential graph.
    
    This class provides algorithms for detecting, tracing, and manipulating
    the identity relationships represented by ligatures in Peirce's system.
    """
    
    def __init__(
        self,
        nodes: PMapType[NodeId, Node],
        edges: PMapType[EdgeId, Edge]
    ):
        """
        Initialize the ligature manager.
        
        Args:
            nodes: Mapping of node IDs to nodes.
            edges: Mapping of edge IDs to edges.
        """
        self._nodes = nodes
        self._edges = edges
        self._ligatures_cache: Optional[PMapType[LigatureId, Ligature]] = None
        self._node_to_ligature_cache: Optional[PMapType[NodeId, LigatureId]] = None
        self._edge_to_ligature_cache: Optional[PMapType[EdgeId, LigatureId]] = None
    
    def _invalidate_caches(self) -> None:
        """Invalidate internal caches."""
        self._ligatures_cache = None
        self._node_to_ligature_cache = None
        self._edge_to_ligature_cache = None
    
    def _get_equality_edges(self) -> List[Edge]:
        """Get all equality edges in the graph."""
        return [edge for edge in self._edges.values() if edge.edge_type == 'equality']
    
    def _build_adjacency_graph(self) -> Dict[NodeId, Set[NodeId]]:
        """
        Build an adjacency graph of nodes connected by equality edges.
        
        Returns:
            A dictionary mapping each node to its neighbors via equality.
        """
        adjacency = {node_id: set() for node_id in self._nodes}
        
        for edge in self._get_equality_edges():
            nodes = list(edge.nodes)
            for i, node1 in enumerate(nodes):
                for j, node2 in enumerate(nodes):
                    if i != j and node1 in adjacency and node2 in adjacency:
                        adjacency[node1].add(node2)
        
        return adjacency
    
    def detect_all_ligatures(self) -> PMapType[LigatureId, Ligature]:
        """
        Detect all ligatures in the graph using connected components analysis.
        
        Returns:
            A mapping of ligature IDs to ligatures.
        """
        if self._ligatures_cache is not None:
            return self._ligatures_cache
        
        adjacency = self._build_adjacency_graph()
        visited_nodes = set()
        ligatures = {}
        
        # Find connected components of nodes
        for start_node in self._nodes:
            if start_node in visited_nodes:
                continue
            
            # Perform DFS to find connected component
            component_nodes = set()
            component_edges = set()
            stack = [start_node]
            
            while stack:
                current_node = stack.pop()
                if current_node in visited_nodes:
                    continue
                
                visited_nodes.add(current_node)
                component_nodes.add(current_node)
                
                # Find equality edges connecting to this node
                for edge in self._get_equality_edges():
                    if current_node in edge.nodes:
                        component_edges.add(edge.id)
                        # Add other nodes from this edge
                        for neighbor in edge.nodes:
                            if neighbor not in visited_nodes:
                                stack.append(neighbor)
            
            # Create ligature for this component
            if component_nodes or component_edges:
                ligature = Ligature(
                    nodes=PSet(component_nodes),
                    edges=PSet(component_edges)
                )
                ligatures[ligature.id] = ligature
        
        # Handle isolated equality edges (edges with no nodes)
        for edge in self._get_equality_edges():
            if not edge.nodes:  # Edge with no nodes
                # Check if this edge is already in a ligature
                already_included = False
                for ligature in ligatures.values():
                    if edge.id in ligature.edges:
                        already_included = True
                        break
                
                if not already_included:
                    ligature = Ligature(edges=PSet([edge.id]))
                    ligatures[ligature.id] = ligature
        
        self._ligatures_cache = PMap(ligatures)
        return self._ligatures_cache
    
    def find_ligature_containing_node(self, node_id: NodeId) -> Optional[Ligature]:
        """
        Find the ligature containing a specific node.
        
        Args:
            node_id: The ID of the node.
            
        Returns:
            The ligature containing the node, or None if not found.
        """
        ligatures = self.detect_all_ligatures()
        for ligature in ligatures.values():
            if node_id in ligature.nodes:
                return ligature
        return None
    
    def find_ligature_containing_edge(self, edge_id: EdgeId) -> Optional[Ligature]:
        """
        Find the ligature containing a specific equality edge.
        
        Args:
            edge_id: The ID of the edge.
            
        Returns:
            The ligature containing the edge, or None if not found.
        """
        if edge_id not in self._edges:
            return None
        
        edge = self._edges[edge_id]
        if edge.edge_type != 'equality':
            return None
        
        ligatures = self.detect_all_ligatures()
        for ligature in ligatures.values():
            if edge_id in ligature.edges:
                return ligature
        return None
    
    def trace_ligature_from_item(self, item_id: ItemId) -> Optional[Ligature]:
        """
        Trace the complete ligature starting from a node or equality edge.
        
        Args:
            item_id: The ID of a node or equality edge.
            
        Returns:
            The complete ligature containing the item, or None if not found.
        """
        if item_id in self._nodes:
            return self.find_ligature_containing_node(item_id)
        elif item_id in self._edges:
            return self.find_ligature_containing_edge(item_id)
        else:
            return None
    
    def get_ligature_boundary_nodes(self, ligature: Ligature) -> Set[NodeId]:
        """
        Get nodes in a ligature that are connected to non-equality edges.
        
        These are the "boundary" nodes where the ligature interfaces with
        the rest of the graph structure.
        
        Args:
            ligature: The ligature to analyze.
            
        Returns:
            A set of boundary node IDs.
        """
        boundary_nodes = set()
        
        for node_id in ligature.nodes:
            # Check if this node is connected to any non-equality edges
            for edge in self._edges.values():
                if (edge.edge_type != 'equality' and 
                    node_id in edge.nodes):
                    boundary_nodes.add(node_id)
                    break
        
        return boundary_nodes
    
    def split_ligature_at_nodes(
        self,
        ligature: Ligature,
        split_nodes: Set[NodeId]
    ) -> List[Ligature]:
        """
        Split a ligature by removing specific nodes and their connections.
        
        This operation is used when nodes are removed from the graph or
        when ligatures need to be severed during transformations.
        
        Args:
            ligature: The ligature to split.
            split_nodes: The nodes to remove from the ligature.
            
        Returns:
            A list of resulting ligatures after the split.
        """
        if not split_nodes.intersection(ligature.nodes):
            return [ligature]  # No nodes to split
        
        # Remove split nodes and their associated edges
        remaining_nodes = ligature.nodes - split_nodes
        remaining_edges = set()
        
        for edge_id in ligature.edges:
            edge = self._edges[edge_id]
            # Keep edge only if all its nodes are still in the ligature
            if all(node_id in remaining_nodes for node_id in edge.nodes):
                remaining_edges.add(edge_id)
        
        if not remaining_nodes and not remaining_edges:
            return []  # Ligature completely removed
        
        # Find connected components in the remaining structure
        adjacency = {}
        for node_id in remaining_nodes:
            adjacency[node_id] = set()
        
        for edge_id in remaining_edges:
            edge = self._edges[edge_id]
            nodes = list(edge.nodes)
            for i, node1 in enumerate(nodes):
                for j, node2 in enumerate(nodes):
                    if i != j and node1 in adjacency and node2 in adjacency:
                        adjacency[node1].add(node2)
        
        # Find connected components
        visited = set()
        components = []
        
        for start_node in remaining_nodes:
            if start_node in visited:
                continue
            
            component_nodes = set()
            component_edges = set()
            stack = [start_node]
            
            while stack:
                current_node = stack.pop()
                if current_node in visited:
                    continue
                
                visited.add(current_node)
                component_nodes.add(current_node)
                
                # Find edges in this component
                for edge_id in remaining_edges:
                    edge = self._edges[edge_id]
                    if current_node in edge.nodes:
                        component_edges.add(edge_id)
                
                # Add neighbors
                for neighbor in adjacency.get(current_node, set()):
                    if neighbor not in visited:
                        stack.append(neighbor)
            
            if component_nodes or component_edges:
                component = Ligature(
                    nodes=PSet(component_nodes),
                    edges=PSet(component_edges)
                )
                components.append(component)
        
        return components
    
    def merge_ligatures(self, ligatures: List[Ligature]) -> Ligature:
        """
        Merge multiple ligatures into a single ligature.
        
        This operation is used when equality edges are added that connect
        previously separate ligatures.
        
        Args:
            ligatures: The ligatures to merge.
            
        Returns:
            A single merged ligature.
        """
        if not ligatures:
            return Ligature()
        
        if len(ligatures) == 1:
            return ligatures[0]
        
        merged_nodes = set()
        merged_edges = set()
        
        for ligature in ligatures:
            merged_nodes.update(ligature.nodes)
            merged_edges.update(ligature.edges)
        
        return Ligature(
            nodes=PSet(merged_nodes),
            edges=PSet(merged_edges)
        )
    
    def add_equality_edge(
        self,
        edge: Edge,
        current_ligatures: PMapType[LigatureId, Ligature]
    ) -> PMapType[LigatureId, Ligature]:
        """
        Update ligatures when an equality edge is added.
        
        Args:
            edge: The equality edge being added.
            current_ligatures: The current ligature mapping.
            
        Returns:
            Updated ligature mapping.
        """
        if edge.edge_type != 'equality':
            return current_ligatures
        
        # Find existing ligatures that contain the edge's nodes
        affected_ligatures = []
        remaining_ligatures = {}
        
        for ligature_id, ligature in current_ligatures.items():
            is_affected = False
            for node_id in edge.nodes:
                if node_id in ligature.nodes:
                    is_affected = True
                    break
            
            if is_affected:
                affected_ligatures.append(ligature)
            else:
                remaining_ligatures[ligature_id] = ligature
        
        # Create new ligature with the edge
        new_ligature_nodes = set(edge.nodes)
        new_ligature_edges = {edge.id}
        
        # Merge with affected ligatures
        for ligature in affected_ligatures:
            new_ligature_nodes.update(ligature.nodes)
            new_ligature_edges.update(ligature.edges)
        
        # Create the merged ligature
        merged_ligature = Ligature(
            nodes=PSet(new_ligature_nodes),
            edges=PSet(new_ligature_edges)
        )
        
        remaining_ligatures[merged_ligature.id] = merged_ligature
        return PMap(remaining_ligatures)
    
    def remove_equality_edge(
        self,
        edge: Edge,
        current_ligatures: PMapType[LigatureId, Ligature]
    ) -> PMapType[LigatureId, Ligature]:
        """
        Update ligatures when an equality edge is removed.
        
        Args:
            edge: The equality edge being removed.
            current_ligatures: The current ligature mapping.
            
        Returns:
            Updated ligature mapping.
        """
        if edge.edge_type != 'equality':
            return current_ligatures
        
        # Find the ligature containing this edge
        target_ligature = None
        target_ligature_id = None
        remaining_ligatures = {}
        
        for ligature_id, ligature in current_ligatures.items():
            if edge.id in ligature.edges:
                target_ligature = ligature
                target_ligature_id = ligature_id
            else:
                remaining_ligatures[ligature_id] = ligature
        
        if target_ligature is None:
            return current_ligatures  # Edge not found in any ligature
        
        # Remove the edge from the ligature
        updated_edges = target_ligature.edges.remove(edge.id)
        
        # Check if the ligature is still connected without this edge
        if not updated_edges:
            # No edges left, create separate single-node ligatures
            for node_id in target_ligature.nodes:
                node_ligature = Ligature(nodes=PSet([node_id]))
                remaining_ligatures[node_ligature.id] = node_ligature
        else:
            # Reconstruct ligature(s) without this edge
            # This may result in multiple disconnected ligatures
            temp_manager = LigatureManager(
                self._nodes,
                PMap({eid: self._edges[eid] for eid in updated_edges})
            )
            
            # Find connected components in the remaining edges
            new_ligatures = temp_manager.detect_all_ligatures()
            for ligature in new_ligatures.values():
                # Only include ligatures that contain nodes from the original
                if ligature.nodes.intersection(target_ligature.nodes):
                    remaining_ligatures[ligature.id] = ligature
        
        return PMap(remaining_ligatures)
    
    def validate_ligatures(
        self,
        ligatures: PMapType[LigatureId, Ligature]
    ) -> List[str]:
        """
        Validate the consistency of ligatures.
        
        Args:
            ligatures: The ligatures to validate.
            
        Returns:
            A list of validation error messages.
        """
        errors = []
        
        # Check that all referenced nodes and edges exist
        for ligature_id, ligature in ligatures.items():
            for node_id in ligature.nodes:
                if node_id not in self._nodes:
                    errors.append(f"Ligature {ligature_id} references non-existent node {node_id}")
            
            for edge_id in ligature.edges:
                if edge_id not in self._edges:
                    errors.append(f"Ligature {ligature_id} references non-existent edge {edge_id}")
                else:
                    edge = self._edges[edge_id]
                    if edge.edge_type != 'equality':
                        errors.append(f"Ligature {ligature_id} contains non-equality edge {edge_id}")
        
        # Check that each node appears in at most one ligature
        node_to_ligature = {}
        for ligature_id, ligature in ligatures.items():
            for node_id in ligature.nodes:
                if node_id in node_to_ligature:
                    other_ligature_id = node_to_ligature[node_id]
                    errors.append(
                        f"Node {node_id} appears in multiple ligatures: "
                        f"{ligature_id} and {other_ligature_id}"
                    )
                else:
                    node_to_ligature[node_id] = ligature_id
        
        # Check that each equality edge appears in at most one ligature
        edge_to_ligature = {}
        for ligature_id, ligature in ligatures.items():
            for edge_id in ligature.edges:
                if edge_id in edge_to_ligature:
                    other_ligature_id = edge_to_ligature[edge_id]
                    errors.append(
                        f"Edge {edge_id} appears in multiple ligatures: "
                        f"{ligature_id} and {other_ligature_id}"
                    )
                else:
                    edge_to_ligature[edge_id] = ligature_id
        
        # Check ligature connectivity
        for ligature_id, ligature in ligatures.items():
            if ligature.nodes and ligature.edges:
                # Verify that the ligature is actually connected
                if not self._is_ligature_connected(ligature):
                    errors.append(f"Ligature {ligature_id} is not connected")
        
        return errors
    
    def _is_ligature_connected(self, ligature: Ligature) -> bool:
        """
        Check if a ligature represents a connected component.
        
        Args:
            ligature: The ligature to check.
            
        Returns:
            True if the ligature is connected.
        """
        if not ligature.nodes:
            return True  # Empty or edge-only ligatures are considered connected
        
        # Build adjacency graph for this ligature
        adjacency = {node_id: set() for node_id in ligature.nodes}
        
        for edge_id in ligature.edges:
            if edge_id in self._edges:
                edge = self._edges[edge_id]
                nodes = list(edge.nodes)
                for i, node1 in enumerate(nodes):
                    for j, node2 in enumerate(nodes):
                        if i != j and node1 in adjacency and node2 in adjacency:
                            adjacency[node1].add(node2)
        
        # Check if all nodes are reachable from the first node
        if not ligature.nodes:
            return True
        
        start_node = next(iter(ligature.nodes))
        visited = set()
        stack = [start_node]
        
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            
            for neighbor in adjacency.get(current, set()):
                if neighbor not in visited:
                    stack.append(neighbor)
        
        return len(visited) == len(ligature.nodes)
    
    def get_ligature_statistics(
        self,
        ligatures: PMapType[LigatureId, Ligature]
    ) -> Dict[str, int]:
        """
        Get statistics about the ligatures in the graph.
        
        Args:
            ligatures: The ligatures to analyze.
            
        Returns:
            A dictionary of statistics.
        """
        stats = {
            'total_ligatures': len(ligatures),
            'total_nodes_in_ligatures': 0,
            'total_edges_in_ligatures': 0,
            'single_node_ligatures': 0,
            'multi_node_ligatures': 0,
            'largest_ligature_size': 0,
            'average_ligature_size': 0.0
        }
        
        sizes = []
        for ligature in ligatures.values():
            size = len(ligature.nodes) + len(ligature.edges)
            sizes.append(size)
            
            stats['total_nodes_in_ligatures'] += len(ligature.nodes)
            stats['total_edges_in_ligatures'] += len(ligature.edges)
            
            if len(ligature.nodes) == 1:
                stats['single_node_ligatures'] += 1
            elif len(ligature.nodes) > 1:
                stats['multi_node_ligatures'] += 1
        
        if sizes:
            stats['largest_ligature_size'] = max(sizes)
            stats['average_ligature_size'] = sum(sizes) / len(sizes)
        
        return stats


