"""
Core graph structure for Existential Graphs.

This module provides the main EGGraph class that combines nodes, edges,
contexts, and ligatures into a comprehensive, immutable graph structure
with full support for Peirce's logical operations.
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
    Node, Edge, Context, Ligature,
    NodeId, EdgeId, ContextId, LigatureId, ItemId,
    NodeType, EdgeType, ContextType,
    new_node_id, new_edge_id, new_context_id, new_ligature_id,
    EGError, ContextError, LigatureError, ValidationError
)
from .context import ContextManager

class EGGraph:
    """
    Immutable representation of an Existential Graph.
    
    This class combines nodes, edges, contexts, and ligatures into a unified
    graph structure with comprehensive operations for manipulation and analysis.
    """
    
    def __init__(
        self,
        nodes: Optional[PMapType[NodeId, Node]] = None,
        edges: Optional[PMapType[EdgeId, Edge]] = None,
        context_manager: Optional[ContextManager] = None,
        ligatures: Optional[PMapType[LigatureId, Ligature]] = None
    ):
        """
        Initialize an existential graph.
        
        Args:
            nodes: Mapping of node IDs to nodes.
            edges: Mapping of edge IDs to edges.
            context_manager: Manager for context hierarchy.
            ligatures: Mapping of ligature IDs to ligatures.
        """
        self._nodes = nodes or PMap()
        self._edges = edges or PMap()
        self._context_manager = context_manager or ContextManager()
        self._ligatures = ligatures or PMap()
        
        # Cache for performance
        self._node_to_edges_cache: Optional[PMapType[NodeId, PSetType[EdgeId]]] = None
        self._item_to_context_cache: Optional[PMapType[ItemId, ContextId]] = None
    
    @property
    def nodes(self) -> PMapType[NodeId, Node]:
        """Get all nodes in the graph."""
        return self._nodes
    
    @property
    def edges(self) -> PMapType[EdgeId, Edge]:
        """Get all edges in the graph."""
        return self._edges
    
    @property
    def contexts(self) -> PMapType[ContextId, Context]:
        """Get all contexts in the graph."""
        return self._context_manager.contexts
    
    @property
    def ligatures(self) -> PMapType[LigatureId, Ligature]:
        """Get all ligatures in the graph."""
        return self._ligatures
    
    @property
    def context_manager(self) -> ContextManager:
        """Get the context manager."""
        return self._context_manager
    
    @property
    def root_context(self) -> Context:
        """Get the root context (Sheet of Assertion)."""
        return self._context_manager.root_context
    
    def _invalidate_caches(self) -> None:
        """Invalidate internal caches."""
        self._node_to_edges_cache = None
        self._item_to_context_cache = None
    
    def _build_node_to_edges_cache(self) -> PMapType[NodeId, PSetType[EdgeId]]:
        """Build cache mapping nodes to their incident edges."""
        if self._node_to_edges_cache is not None:
            return self._node_to_edges_cache
        
        cache = {}
        for node_id in self._nodes:
            cache[node_id] = PSet()
        
        for edge_id, edge in self._edges.items():
            for node_id in edge.nodes:
                if node_id in cache:
                    cache[node_id] = cache[node_id].add(edge_id)
        
        self._node_to_edges_cache = PMap(cache)
        return self._node_to_edges_cache
    
    def _build_item_to_context_cache(self) -> PMapType[ItemId, ContextId]:
        """Build cache mapping items to their containing contexts."""
        if self._item_to_context_cache is not None:
            return self._item_to_context_cache
        
        cache = {}
        for context_id, context in self._context_manager.contexts.items():
            for item_id in context.contained_items:
                cache[item_id] = context_id
        
        self._item_to_context_cache = PMap(cache)
        return self._item_to_context_cache
    
    # Node operations
    
    def get_node(self, node_id: NodeId) -> Node:
        """
        Get a node by its ID.
        
        Args:
            node_id: The ID of the node.
            
        Returns:
            The requested node.
            
        Raises:
            EGError: If the node does not exist.
        """
        try:
            return self._nodes[node_id]
        except KeyError:
            raise EGError(f"Node {node_id} not found")
    
    def has_node(self, node_id: NodeId) -> bool:
        """Check if a node exists in the graph."""
        return node_id in self._nodes
    
    def add_node(
        self,
        node_type: NodeType,
        context_id: Optional[ContextId] = None,
        **properties
    ) -> Tuple[EGGraph, Node]:
        """
        Add a new node to the graph.
        
        Args:
            node_type: The type of node to create.
            context_id: The context to add the node to. If None, uses root.
            **properties: Additional properties for the node.
            
        Returns:
            A tuple of (new_graph, created_node).
        """
        if context_id is None:
            context_id = self._context_manager.root_context.id
        
        node = Node(node_type=node_type, properties=PMap(properties))
        new_nodes = self._nodes.set(node.id, node)
        new_context_manager = self._context_manager.add_item_to_context(node.id, context_id)
        
        return self._evolve(
            nodes=new_nodes,
            context_manager=new_context_manager
        ), node
    
    def remove_node(self, node_id: NodeId) -> EGGraph:
        """
        Remove a node from the graph.
        
        Args:
            node_id: The ID of the node to remove.
            
        Returns:
            A new graph with the node removed.
            
        Raises:
            EGError: If the node does not exist or is connected to edges.
        """
        if node_id not in self._nodes:
            raise EGError(f"Node {node_id} not found")
        
        # Check if node is connected to any edges
        incident_edges = self.get_incident_edges(node_id)
        if incident_edges:
            edge_ids = [str(edge.id) for edge in incident_edges]
            raise EGError(f"Cannot remove node {node_id}: connected to edges {edge_ids}")
        
        # Remove from context
        context_id = self.find_item_context(node_id)
        new_context_manager = self._context_manager
        if context_id is not None:
            new_context_manager = self._context_manager.remove_item_from_context(node_id, context_id)
        
        # Remove from ligatures
        new_ligatures = self._ligatures
        for ligature_id, ligature in self._ligatures.items():
            if node_id in ligature.nodes:
                updated_ligature = ligature.evolve(nodes=ligature.nodes.remove(node_id))
                if updated_ligature.is_empty:
                    new_ligatures = new_ligatures.remove(ligature_id)
                else:
                    new_ligatures = new_ligatures.set(ligature_id, updated_ligature)
        
        new_nodes = self._nodes.remove(node_id)
        
        return self._evolve(
            nodes=new_nodes,
            context_manager=new_context_manager,
            ligatures=new_ligatures
        )
    
    def update_node(self, node_id: NodeId, **changes) -> EGGraph:
        """
        Update a node with new properties.
        
        Args:
            node_id: The ID of the node to update.
            **changes: Changes to apply to the node.
            
        Returns:
            A new graph with the node updated.
        """
        node = self.get_node(node_id)
        updated_node = node.evolve(**changes)
        new_nodes = self._nodes.set(node_id, updated_node)
        
        return self._evolve(nodes=new_nodes)
    
    # Edge operations
    
    def get_edge(self, edge_id: EdgeId) -> Edge:
        """
        Get an edge by its ID.
        
        Args:
            edge_id: The ID of the edge.
            
        Returns:
            The requested edge.
            
        Raises:
            EGError: If the edge does not exist.
        """
        try:
            return self._edges[edge_id]
        except KeyError:
            raise EGError(f"Edge {edge_id} not found")
    
    def has_edge(self, edge_id: EdgeId) -> bool:
        """Check if an edge exists in the graph."""
        return edge_id in self._edges
    
    def add_edge(
        self,
        edge_type: EdgeType,
        nodes: List[NodeId],
        context_id: Optional[ContextId] = None,
        **properties
    ) -> Tuple[EGGraph, Edge]:
        """
        Add a new edge to the graph.
        
        Args:
            edge_type: The type of edge to create.
            nodes: List of node IDs that the edge connects.
            context_id: The context to add the edge to. If None, uses root.
            **properties: Additional properties for the edge.
            
        Returns:
            A tuple of (new_graph, created_edge).
            
        Raises:
            EGError: If any of the nodes do not exist.
        """
        if context_id is None:
            context_id = self._context_manager.root_context.id
        
        # Validate that all nodes exist
        for node_id in nodes:
            if node_id not in self._nodes:
                raise EGError(f"Node {node_id} not found")
        
        edge = Edge(
            edge_type=edge_type,
            nodes=PVector(nodes),
            properties=PMap(properties)
        )
        new_edges = self._edges.set(edge.id, edge)
        new_context_manager = self._context_manager.add_item_to_context(edge.id, context_id)
        
        # If this is an equality edge, update ligatures
        new_ligatures = self._ligatures
        if edge_type == 'equality':
            new_ligatures = self._update_ligatures_for_equality(edge, new_ligatures)
        
        return self._evolve(
            edges=new_edges,
            context_manager=new_context_manager,
            ligatures=new_ligatures
        ), edge
    
    def remove_edge(self, edge_id: EdgeId) -> EGGraph:
        """
        Remove an edge from the graph.
        
        Args:
            edge_id: The ID of the edge to remove.
            
        Returns:
            A new graph with the edge removed.
        """
        if edge_id not in self._edges:
            raise EGError(f"Edge {edge_id} not found")
        
        edge = self._edges[edge_id]
        
        # Remove from context
        context_id = self.find_item_context(edge_id)
        new_context_manager = self._context_manager
        if context_id is not None:
            new_context_manager = self._context_manager.remove_item_from_context(edge_id, context_id)
        
        # If this is an equality edge, update ligatures
        new_ligatures = self._ligatures
        if edge.edge_type == 'equality':
            new_ligatures = self._remove_equality_from_ligatures(edge, new_ligatures)
        
        # If this is a cut, remove all contained items
        if edge.edge_type == 'cut':
            context = self._context_manager.get_context(context_id) if context_id else None
            if context and edge_id in context.contained_items:
                # This edge represents a context, remove all its contents
                items_to_remove = self._context_manager.get_all_items_in_subtree(edge_id)
                # TODO: Implement recursive removal of contained items
        
        new_edges = self._edges.remove(edge_id)
        
        return self._evolve(
            edges=new_edges,
            context_manager=new_context_manager,
            ligatures=new_ligatures
        )
    
    def update_edge(self, edge_id: EdgeId, **changes) -> EGGraph:
        """
        Update an edge with new properties.
        
        Args:
            edge_id: The ID of the edge to update.
            **changes: Changes to apply to the edge.
            
        Returns:
            A new graph with the edge updated.
        """
        edge = self.get_edge(edge_id)
        updated_edge = edge.evolve(**changes)
        new_edges = self._edges.set(edge_id, updated_edge)
        
        return self._evolve(edges=new_edges)
    
    # Graph traversal operations
    
    def get_incident_edges(self, node_id: NodeId) -> List[Edge]:
        """
        Get all edges incident to a node.
        
        Args:
            node_id: The ID of the node.
            
        Returns:
            A list of edges connected to the node.
        """
        if node_id not in self._nodes:
            raise EGError(f"Node {node_id} not found")
        
        cache = self._build_node_to_edges_cache()
        edge_ids = cache.get(node_id, PSet())
        return [self._edges[edge_id] for edge_id in edge_ids]
    
    def get_neighbors(self, node_id: NodeId) -> Set[NodeId]:
        """
        Get all nodes connected to a given node.
        
        Args:
            node_id: The ID of the node.
            
        Returns:
            A set of neighboring node IDs.
        """
        neighbors = set()
        for edge in self.get_incident_edges(node_id):
            for neighbor_id in edge.nodes:
                if neighbor_id != node_id:
                    neighbors.add(neighbor_id)
        return neighbors
    
    def find_path(self, start_node: NodeId, end_node: NodeId) -> Optional[List[NodeId]]:
        """
        Find a path between two nodes using breadth-first search.
        
        Args:
            start_node: The starting node ID.
            end_node: The ending node ID.
            
        Returns:
            A list of node IDs representing the path, or None if no path exists.
        """
        if start_node == end_node:
            return [start_node]
        
        visited = set()
        queue = [(start_node, [start_node])]
        
        while queue:
            current_node, path = queue.pop(0)
            
            if current_node in visited:
                continue
            
            visited.add(current_node)
            
            for neighbor in self.get_neighbors(current_node):
                if neighbor == end_node:
                    return path + [neighbor]
                
                if neighbor not in visited:
                    queue.append((neighbor, path + [neighbor]))
        
        return None
    
    # Context operations
    
    def find_item_context(self, item_id: ItemId) -> Optional[ContextId]:
        """
        Find the context containing an item.
        
        Args:
            item_id: The ID of the item.
            
        Returns:
            The ID of the containing context, or None if not found.
        """
        cache = self._build_item_to_context_cache()
        return cache.get(item_id)
    
    def get_items_in_context(self, context_id: ContextId) -> Set[ItemId]:
        """
        Get all items in a specific context.
        
        Args:
            context_id: The ID of the context.
            
        Returns:
            A set of item IDs in the context.
        """
        return self._context_manager.get_items_in_context(context_id)
    
    def move_item_to_context(
        self,
        item_id: ItemId,
        target_context_id: ContextId
    ) -> EGGraph:
        """
        Move an item to a different context.
        
        Args:
            item_id: The ID of the item to move.
            target_context_id: The ID of the target context.
            
        Returns:
            A new graph with the item moved.
        """
        current_context_id = self.find_item_context(item_id)
        if current_context_id is None:
            raise EGError(f"Item {item_id} not found in any context")
        
        new_context_manager = self._context_manager.move_item(
            item_id, current_context_id, target_context_id
        )
        
        return self._evolve(context_manager=new_context_manager)
    
    # Ligature operations
    
    def trace_ligature(self, item_id: ItemId) -> Ligature:
        """
        Trace the complete ligature containing an item.
        
        Args:
            item_id: The ID of a node or equality edge in the ligature.
            
        Returns:
            The complete ligature containing the item.
            
        Raises:
            LigatureError: If the item is not part of any ligature.
        """
        # Find existing ligature containing this item
        for ligature in self._ligatures.values():
            if (item_id in ligature.nodes or 
                (isinstance(item_id, EdgeId) and item_id in ligature.edges)):
                return ligature
        
        # If not found, create a new ligature by tracing connections
        if item_id in self._nodes:
            return self._trace_ligature_from_node(item_id)
        elif item_id in self._edges:
            edge = self._edges[item_id]
            if edge.edge_type == 'equality':
                return self._trace_ligature_from_equality(item_id)
        
        raise LigatureError(f"Item {item_id} is not part of any ligature")
    
    def _trace_ligature_from_node(self, node_id: NodeId) -> Ligature:
        """Trace a ligature starting from a node."""
        visited_nodes = set()
        visited_edges = set()
        queue = [node_id]
        
        while queue:
            current_node = queue.pop(0)
            if current_node in visited_nodes:
                continue
            
            visited_nodes.add(current_node)
            
            # Find all equality edges connected to this node
            for edge in self.get_incident_edges(current_node):
                if edge.edge_type == 'equality' and edge.id not in visited_edges:
                    visited_edges.add(edge.id)
                    # Add other nodes connected by this equality edge
                    for connected_node in edge.nodes:
                        if connected_node not in visited_nodes:
                            queue.append(connected_node)
        
        return Ligature(
            nodes=PSet(visited_nodes),
            edges=PSet(visited_edges)
        )
    
    def _trace_ligature_from_equality(self, edge_id: EdgeId) -> Ligature:
        """Trace a ligature starting from an equality edge."""
        edge = self._edges[edge_id]
        if edge.nodes:
            return self._trace_ligature_from_node(edge.nodes[0])
        else:
            return Ligature(edges=PSet([edge_id]))
    
    def _update_ligatures_for_equality(
        self,
        equality_edge: Edge,
        ligatures: PMapType[LigatureId, Ligature]
    ) -> PMapType[LigatureId, Ligature]:
        """Update ligatures when an equality edge is added."""
        if not equality_edge.nodes:
            # Create a new ligature with just this edge
            new_ligature = Ligature(edges=PSet([equality_edge.id]))
            return ligatures.set(new_ligature.id, new_ligature)
        
        # Find existing ligatures for the connected nodes
        connected_ligatures = []
        for node_id in equality_edge.nodes:
            for ligature_id, ligature in ligatures.items():
                if node_id in ligature.nodes:
                    connected_ligatures.append((ligature_id, ligature))
                    break
        
        if not connected_ligatures:
            # Create new ligature
            new_ligature = Ligature(
                nodes=PSet(equality_edge.nodes),
                edges=PSet([equality_edge.id])
            )
            return ligatures.set(new_ligature.id, new_ligature)
        
        # Merge existing ligatures
        merged_ligature = Ligature(
            nodes=PSet(equality_edge.nodes),
            edges=PSet([equality_edge.id])
        )
        
        new_ligatures = ligatures
        for ligature_id, ligature in connected_ligatures:
            merged_ligature = merged_ligature.union(ligature)
            new_ligatures = new_ligatures.remove(ligature_id)
        
        return new_ligatures.set(merged_ligature.id, merged_ligature)
    
    def _remove_equality_from_ligatures(
        self,
        equality_edge: Edge,
        ligatures: PMapType[LigatureId, Ligature]
    ) -> PMapType[LigatureId, Ligature]:
        """Update ligatures when an equality edge is removed."""
        # Find the ligature containing this edge
        target_ligature_id = None
        for ligature_id, ligature in ligatures.items():
            if equality_edge.id in ligature.edges:
                target_ligature_id = ligature_id
                break
        
        if target_ligature_id is None:
            return ligatures
        
        target_ligature = ligatures[target_ligature_id]
        new_ligatures = ligatures.remove(target_ligature_id)
        
        # Remove the edge from the ligature
        updated_edges = target_ligature.edges.remove(equality_edge.id)
        
        if not updated_edges:
            # If no edges left, create separate ligatures for each node
            for node_id in target_ligature.nodes:
                node_ligature = Ligature(nodes=PSet([node_id]))
                new_ligatures = new_ligatures.set(node_ligature.id, node_ligature)
        else:
            # Reconstruct ligature(s) without this edge
            # This is complex and may result in multiple ligatures
            # For now, create a single ligature with remaining edges
            updated_ligature = target_ligature.evolve(edges=updated_edges)
            new_ligatures = new_ligatures.set(updated_ligature.id, updated_ligature)
        
        return new_ligatures
    
    # Utility methods
    
    def _evolve(self, **changes) -> EGGraph:
        """Create a new graph with the specified changes."""
        new_graph = EGGraph.__new__(EGGraph)
        new_graph._nodes = changes.get('nodes', self._nodes)
        new_graph._edges = changes.get('edges', self._edges)
        new_graph._context_manager = changes.get('context_manager', self._context_manager)
        new_graph._ligatures = changes.get('ligatures', self._ligatures)
        new_graph._invalidate_caches()
        return new_graph
    
    def validate(self) -> List[str]:
        """
        Validate the consistency of the graph.
        
        Returns:
            A list of validation error messages. Empty if valid.
        """
        errors = []
        
        # Validate context hierarchy
        errors.extend(self._context_manager.validate_context_hierarchy())
        
        # Validate that all edge nodes exist
        for edge_id, edge in self._edges.items():
            for node_id in edge.nodes:
                if node_id not in self._nodes:
                    errors.append(f"Edge {edge_id} references non-existent node {node_id}")
        
        # Validate that all items in contexts exist
        for context_id, context in self._context_manager.contexts.items():
            for item_id in context.contained_items:
                if (item_id not in self._nodes and 
                    item_id not in self._edges):
                    errors.append(f"Context {context_id} contains non-existent item {item_id}")
        
        # Validate ligatures
        for ligature_id, ligature in self._ligatures.items():
            for node_id in ligature.nodes:
                if node_id not in self._nodes:
                    errors.append(f"Ligature {ligature_id} references non-existent node {node_id}")
            
            for edge_id in ligature.edges:
                if edge_id not in self._edges:
                    errors.append(f"Ligature {ligature_id} references non-existent edge {edge_id}")
                elif self._edges[edge_id].edge_type != 'equality':
                    errors.append(f"Ligature {ligature_id} contains non-equality edge {edge_id}")
        
        return errors
    
    def __str__(self) -> str:
        """String representation of the graph."""
        return (f"EGGraph({len(self._nodes)} nodes, {len(self._edges)} edges, "
                f"{len(self._context_manager.contexts)} contexts, {len(self._ligatures)} ligatures)")
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"EGGraph(nodes={len(self._nodes)}, edges={len(self._edges)}, "
                f"contexts={len(self._context_manager.contexts)}, ligatures={len(self._ligatures)})")


