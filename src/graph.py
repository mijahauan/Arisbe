"""
Unified graph operations for the EG-HG rebuild project.

This module provides the EGGraph class that combines all components
(contexts, nodes, edges, ligatures) with comprehensive graph traversal
and manipulation operations.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Iterator
from dataclasses import dataclass, replace
from collections import defaultdict, deque
import uuid

from .eg_types import (
    Node, Edge, Context, Ligature,
    NodeId, EdgeId, ContextId, LigatureId, ItemId,
    new_node_id, new_edge_id, new_context_id, new_ligature_id,
    EGError, NodeError, EdgeError, ContextError, LigatureError,
    pmap, pset
)
from .context import ContextManager


@dataclass(frozen=True)
class EGGraph:
    """Unified existential graph with comprehensive operations.
    
    This class combines contexts, nodes, edges, and ligatures into a single
    immutable graph structure with comprehensive traversal and manipulation
    operations.
    """
    
    context_manager: ContextManager
    nodes: pmap  # Dict[NodeId, Node]
    edges: pmap  # Dict[EdgeId, Edge]
    ligatures: pmap  # Dict[LigatureId, Ligature]
    
    @classmethod
    def create_empty(cls) -> 'EGGraph':
        """Create an empty existential graph with just the root context."""
        context_manager = ContextManager()
        return cls(
            context_manager=context_manager,
            nodes=pmap(),
            edges=pmap(),
            ligatures=pmap()
        )
    
    @property
    def root_context_id(self) -> ContextId:
        """Get the ID of the root context (Sheet of Assertion)."""
        return self.context_manager.root_context.id
    
    # Node operations
    def add_node(self, node: Node, context_id: Optional[ContextId] = None) -> 'EGGraph':
        """Add a node to the graph in the specified context.
        
        Args:
            node: The node to add.
            context_id: The context to add the node to. If None, uses root context.
            
        Returns:
            A new EGGraph with the node added.
            
        Raises:
            ContextError: If the context doesn't exist.
        """
        if context_id is None:
            context_id = self.root_context_id
        
        # Add node to the nodes collection
        new_nodes = self.nodes.set(node.id, node)
        
        # Add node to the specified context
        new_context_manager = self.context_manager.add_item_to_context(context_id, node.id)
        
        return replace(self, nodes=new_nodes, context_manager=new_context_manager)
    
    def remove_node(self, node_id: NodeId) -> 'EGGraph':
        """Remove a node from the graph.
        
        Args:
            node_id: The ID of the node to remove.
            
        Returns:
            A new EGGraph with the node removed.
            
        Raises:
            NodeError: If the node doesn't exist.
        """
        if node_id not in self.nodes:
            raise NodeError(f"Node {node_id} not found")
        
        # Remove node from nodes collection
        new_nodes = self.nodes.remove(node_id)
        
        # Remove node from any edges
        new_edges = self.edges
        for edge_id, edge in self.edges.items():
            if node_id in edge.nodes:
                updated_edge = edge.remove_node(node_id)
                new_edges = new_edges.set(edge_id, updated_edge)
        
        # Remove node from any ligatures
        new_ligatures = self.ligatures
        for ligature_id, ligature in self.ligatures.items():
            if node_id in ligature.nodes:
                updated_ligature = replace(ligature, nodes=ligature.nodes.remove(node_id))
                new_ligatures = new_ligatures.set(ligature_id, updated_ligature)
        
        # Remove node from its context
        context_id = self.context_manager.find_item_context(node_id)
        new_context_manager = self.context_manager
        if context_id is not None:
            new_context_manager = self.context_manager.remove_item_from_context(context_id, node_id)
        
        return replace(self, 
                      nodes=new_nodes, 
                      edges=new_edges, 
                      ligatures=new_ligatures,
                      context_manager=new_context_manager)
    
    def get_node(self, node_id: NodeId) -> Optional[Node]:
        """Get a node by its ID."""
        return self.nodes.get(node_id)
    
    # Edge operations
    def add_edge(self, edge: Edge, context_id: Optional[ContextId] = None) -> 'EGGraph':
        """Add an edge to the graph in the specified context.
        
        Args:
            edge: The edge to add.
            context_id: The context to add the edge to. If None, uses root context.
            
        Returns:
            A new EGGraph with the edge added.
            
        Raises:
            ContextError: If the context doesn't exist.
            NodeError: If any of the edge's nodes don't exist.
        """
        if context_id is None:
            context_id = self.root_context_id
        
        # Validate that all nodes in the edge exist
        for node_id in edge.nodes:
            if node_id not in self.nodes:
                raise NodeError(f"Node {node_id} not found")
        
        # Add edge to the edges collection
        new_edges = self.edges.set(edge.id, edge)
        
        # Add edge to the specified context
        new_context_manager = self.context_manager.add_item_to_context(context_id, edge.id)
        
        return replace(self, edges=new_edges, context_manager=new_context_manager)
    
    def remove_edge(self, edge_id: EdgeId) -> 'EGGraph':
        """Remove an edge from the graph.
        
        Args:
            edge_id: The ID of the edge to remove.
            
        Returns:
            A new EGGraph with the edge removed.
            
        Raises:
            EdgeError: If the edge doesn't exist.
        """
        if edge_id not in self.edges:
            raise EdgeError(f"Edge {edge_id} not found")
        
        # Remove edge from edges collection
        new_edges = self.edges.remove(edge_id)
        
        # Remove edge from any ligatures
        new_ligatures = self.ligatures
        for ligature_id, ligature in self.ligatures.items():
            if edge_id in ligature.edges:
                updated_ligature = replace(ligature, edges=ligature.edges.remove(edge_id))
                new_ligatures = new_ligatures.set(ligature_id, updated_ligature)
        
        # Remove edge from its context
        context_id = self.context_manager.find_item_context(edge_id)
        new_context_manager = self.context_manager
        if context_id is not None:
            new_context_manager = self.context_manager.remove_item_from_context(context_id, edge_id)
        
        return replace(self, 
                      edges=new_edges, 
                      ligatures=new_ligatures,
                      context_manager=new_context_manager)
    
    def get_edge(self, edge_id: EdgeId) -> Optional[Edge]:
        """Get an edge by its ID."""
        return self.edges.get(edge_id)
    
    # Ligature operations
    def add_ligature(self, ligature: Ligature) -> 'EGGraph':
        """Add a ligature to the graph.
        
        Args:
            ligature: The ligature to add.
            
        Returns:
            A new EGGraph with the ligature added.
            
        Raises:
            NodeError: If any of the ligature's nodes don't exist.
            EdgeError: If any of the ligature's edges don't exist.
        """
        # Validate that all nodes and edges in the ligature exist
        for node_id in ligature.nodes:
            if node_id not in self.nodes:
                raise NodeError(f"Node {node_id} not found")
        
        for edge_id in ligature.edges:
            if edge_id not in self.edges:
                raise EdgeError(f"Edge {edge_id} not found")
        
        # Add ligature to the ligatures collection
        new_ligatures = self.ligatures.set(ligature.id, ligature)
        
        return replace(self, ligatures=new_ligatures)
    
    def remove_ligature(self, ligature_id: LigatureId) -> 'EGGraph':
        """Remove a ligature from the graph.
        
        Args:
            ligature_id: The ID of the ligature to remove.
            
        Returns:
            A new EGGraph with the ligature removed.
            
        Raises:
            LigatureError: If the ligature doesn't exist.
        """
        if ligature_id not in self.ligatures:
            raise LigatureError(f"Ligature {ligature_id} not found")
        
        # Remove ligature from ligatures collection
        new_ligatures = self.ligatures.remove(ligature_id)
        
        return replace(self, ligatures=new_ligatures)
    
    def get_ligature(self, ligature_id: LigatureId) -> Optional[Ligature]:
        """Get a ligature by its ID."""
        return self.ligatures.get(ligature_id)
    
    # Context operations
    def create_context(self, context_type: str, parent_id: Optional[ContextId] = None,
                      name: Optional[str] = None) -> Tuple['EGGraph', Context]:
        """Create a new context in the graph.
        
        Args:
            context_type: The type of context to create.
            parent_id: The ID of the parent context. If None, uses root context.
            name: Optional name for the context.
            
        Returns:
            A tuple of (new_graph, new_context).
            
        Raises:
            ContextError: If the parent context doesn't exist.
        """
        new_context_manager, new_context = self.context_manager.create_context(
            context_type, parent_id, name
        )
        
        return replace(self, context_manager=new_context_manager), new_context
    
    # Graph traversal operations
    def find_incident_edges(self, node_id: NodeId) -> List[Edge]:
        """Find all edges incident to a node.
        
        Args:
            node_id: The ID of the node.
            
        Returns:
            A list of edges that contain the node.
        """
        incident_edges = []
        for edge in self.edges.values():
            if node_id in edge.nodes:
                incident_edges.append(edge)
        return incident_edges
    
    def get_neighbors(self, node_id: NodeId) -> Set[NodeId]:
        """Get all nodes connected to a given node through edges.
        
        Args:
            node_id: The ID of the node.
            
        Returns:
            A set of node IDs that are neighbors of the given node.
        """
        neighbors = set()
        for edge in self.find_incident_edges(node_id):
            for neighbor_id in edge.nodes:
                if neighbor_id != node_id:
                    neighbors.add(neighbor_id)
        return neighbors
    
    def find_path(self, start_node_id: NodeId, end_node_id: NodeId) -> Optional[List[NodeId]]:
        """Find a path between two nodes using breadth-first search.
        
        Args:
            start_node_id: The starting node ID.
            end_node_id: The ending node ID.
            
        Returns:
            A list of node IDs representing the path, or None if no path exists.
        """
        if start_node_id == end_node_id:
            return [start_node_id]
        
        if start_node_id not in self.nodes or end_node_id not in self.nodes:
            return None
        
        queue = deque([(start_node_id, [start_node_id])])
        visited = {start_node_id}
        
        while queue:
            current_node, path = queue.popleft()
            
            for neighbor_id in self.get_neighbors(current_node):
                if neighbor_id == end_node_id:
                    return path + [neighbor_id]
                
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, path + [neighbor_id]))
        
        return None
    
    def find_connected_components(self) -> List[Set[NodeId]]:
        """Find all connected components in the graph.
        
        Returns:
            A list of sets, where each set contains the node IDs in a connected component.
        """
        visited = set()
        components = []
        
        for node_id in self.nodes:
            if node_id not in visited:
                component = set()
                stack = [node_id]
                
                while stack:
                    current = stack.pop()
                    if current not in visited:
                        visited.add(current)
                        component.add(current)
                        
                        for neighbor in self.get_neighbors(current):
                            if neighbor not in visited:
                                stack.append(neighbor)
                
                components.append(component)
        
        return components
    
    def trace_ligature_path(self, item_id: ItemId) -> Optional[Ligature]:
        """Trace the ligature path containing a given item.
        
        Args:
            item_id: The ID of the item (node or edge) to trace.
            
        Returns:
            The ligature containing the item, or None if not found.
        """
        for ligature in self.ligatures.values():
            if item_id in ligature.nodes or item_id in ligature.edges:
                return ligature
        return None
    
    def get_items_in_context(self, context_id: ContextId) -> Set[ItemId]:
        """Get all items (nodes and edges) in a specific context.
        
        Args:
            context_id: The ID of the context.
            
        Returns:
            A set of item IDs in the context.
        """
        return self.context_manager.get_items_in_context(context_id)
    
    def get_nodes_in_context(self, context_id: ContextId) -> List[Node]:
        """Get all nodes in a specific context.
        
        Args:
            context_id: The ID of the context.
            
        Returns:
            A list of nodes in the context.
        """
        item_ids = self.get_items_in_context(context_id)
        nodes = []
        for item_id in item_ids:
            if item_id in self.nodes:
                nodes.append(self.nodes[item_id])
        return nodes
    
    def get_edges_in_context(self, context_id: ContextId) -> List[Edge]:
        """Get all edges in a specific context.
        
        Args:
            context_id: The ID of the context.
            
        Returns:
            A list of edges in the context.
        """
        item_ids = self.get_items_in_context(context_id)
        edges = []
        for item_id in item_ids:
            if item_id in self.edges:
                edges.append(self.edges[item_id])
        return edges
    
    # Validation operations
    def validate_graph_consistency(self) -> List[str]:
        """Validate the consistency of the entire graph.
        
        Returns:
            A list of error messages. Empty list means no errors.
        """
        errors = []
        
        # Validate context hierarchy
        errors.extend(self.context_manager.validate_context_hierarchy())
        
        # Validate that all edge nodes exist
        for edge_id, edge in self.edges.items():
            for node_id in edge.nodes:
                if node_id not in self.nodes:
                    errors.append(f"Edge {edge_id} references non-existent node {node_id}")
        
        # Validate that all ligature items exist
        for ligature_id, ligature in self.ligatures.items():
            for node_id in ligature.nodes:
                if node_id not in self.nodes:
                    errors.append(f"Ligature {ligature_id} references non-existent node {node_id}")
            
            for edge_id in ligature.edges:
                if edge_id not in self.edges:
                    errors.append(f"Ligature {ligature_id} references non-existent edge {edge_id}")
        
        # Validate that all items are in some context
        all_context_items = set()
        for context_id in self.context_manager.contexts:
            all_context_items.update(self.get_items_in_context(context_id))
        
        for node_id in self.nodes:
            if node_id not in all_context_items:
                errors.append(f"Node {node_id} is not in any context")
        
        for edge_id in self.edges:
            if edge_id not in all_context_items:
                errors.append(f"Edge {edge_id} is not in any context")
        
        return errors
    
    # Utility methods
    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get statistics about the graph.
        
        Returns:
            A dictionary containing various graph statistics.
        """
        return {
            'num_contexts': len(self.context_manager.contexts),
            'num_nodes': len(self.nodes),
            'num_edges': len(self.edges),
            'num_ligatures': len(self.ligatures),
            'connected_components': len(self.find_connected_components()),
            'max_context_depth': max(ctx.depth for ctx in self.context_manager.contexts.values()),
        }
    
    def __str__(self) -> str:
        """String representation of the graph."""
        stats = self.get_graph_statistics()
        return (f"EGGraph(contexts={stats['num_contexts']}, "
                f"nodes={stats['num_nodes']}, "
                f"edges={stats['num_edges']}, "
                f"ligatures={stats['num_ligatures']})")

