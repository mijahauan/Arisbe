"""
Updated graph operations for the EG-HG rebuild project with Entity/Predicate support.

This module extends the EGGraph class to support both the traditional Node/Edge
architecture and the new Entity/Predicate architecture for correct hypergraph mapping.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Iterator
from dataclasses import dataclass, replace
from collections import defaultdict, deque
import uuid

from eg_types import (
    Node, Edge, Context, Ligature, Entity, Predicate,
    NodeId, EdgeId, ContextId, LigatureId, EntityId, PredicateId, ItemId,
    new_node_id, new_edge_id, new_context_id, new_ligature_id, new_entity_id, new_predicate_id,
    EGError, NodeError, EdgeError, ContextError, LigatureError, EntityError, PredicateError,
    pmap, pset, pvector
)
from context import ContextManager


@dataclass(frozen=True)
class EGGraph:
    """Unified existential graph with comprehensive operations.
    
    This class combines contexts, nodes, edges, ligatures, entities, and predicates
    into a single immutable graph structure with comprehensive traversal and
    manipulation operations.
    """
    
    context_manager: ContextManager
    nodes: pmap  # Dict[NodeId, Node]
    edges: pmap  # Dict[EdgeId, Edge]
    ligatures: pmap  # Dict[LigatureId, Ligature]
    entities: pmap  # Dict[EntityId, Entity]
    predicates: pmap  # Dict[PredicateId, Predicate]
    
    @classmethod
    def create_empty(cls) -> 'EGGraph':
        """Create an empty existential graph with just the root context."""
        context_manager = ContextManager()
        return cls(
            context_manager=context_manager,
            nodes=pmap(),
            edges=pmap(),
            ligatures=pmap(),
            entities=pmap(),
            predicates=pmap()
        )
    
    @property
    def root_context_id(self) -> ContextId:
        """Get the ID of the root context (Sheet of Assertion)."""
        return self.context_manager.root_context.id
    
    @property
    def contexts(self) -> pmap:
        """Get all contexts in the graph."""
        return self.context_manager.contexts
    
    # Context operations
    def get_items_in_context(self, context_id: ContextId) -> Set[ItemId]:
        """Get all items directly contained in a context."""
        return self.context_manager.get_items_in_context(context_id)
    
    def get_nodes_in_context(self, context_id: ContextId) -> List[Node]:
        """Get all nodes in a specific context."""
        items = self.get_items_in_context(context_id)
        nodes = []
        for item_id in items:
            if item_id in self.nodes:
                nodes.append(self.nodes[item_id])
        return nodes
    
    def get_edges_in_context(self, context_id: ContextId) -> List[Edge]:
        """Get all edges in a specific context."""
        items = self.get_items_in_context(context_id)
        edges = []
        for item_id in items:
            if item_id in self.edges:
                edges.append(self.edges[item_id])
        return edges
    
    def get_entities_in_context(self, context_id: ContextId) -> List[Entity]:
        """Get all entities in a specific context."""
        items = self.get_items_in_context(context_id)
        entities = []
        for item_id in items:
            if item_id in self.entities:
                entities.append(self.entities[item_id])
        return entities
    
    def get_predicates_in_context(self, context_id: ContextId) -> List[Predicate]:
        """Get all predicates in a specific context."""
        items = self.get_items_in_context(context_id)
        predicates = []
        for item_id in items:
            if item_id in self.predicates:
                predicates.append(self.predicates[item_id])
        return predicates
    
    # Node operations (existing)
    def add_node(self, node: Node, context_id: Optional[ContextId] = None) -> 'EGGraph':
        """Add a node to the graph in the specified context."""
        if context_id is None:
            context_id = self.root_context_id
        
        new_nodes = self.nodes.set(node.id, node)
        new_context_manager = self.context_manager.add_item_to_context(context_id, node.id)
        
        return replace(self, nodes=new_nodes, context_manager=new_context_manager)
    
    def remove_node(self, node_id: NodeId) -> 'EGGraph':
        """Remove a node from the graph."""
        if node_id not in self.nodes:
            raise NodeError(f"Node {node_id} not found")
        
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
    
    # Edge operations (existing)
    def add_edge(self, edge: Edge, context_id: Optional[ContextId] = None) -> 'EGGraph':
        """Add an edge to the graph in the specified context."""
        if context_id is None:
            context_id = self.root_context_id
        
        # Validate that all nodes in the edge exist
        for node_id in edge.nodes:
            if node_id not in self.nodes:
                raise NodeError(f"Node {node_id} not found")
        
        new_edges = self.edges.set(edge.id, edge)
        new_context_manager = self.context_manager.add_item_to_context(context_id, edge.id)
        
        return replace(self, edges=new_edges, context_manager=new_context_manager)
    
    def remove_edge(self, edge_id: EdgeId) -> 'EGGraph':
        """Remove an edge from the graph."""
        if edge_id not in self.edges:
            raise EdgeError(f"Edge {edge_id} not found")
        
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
    
    # Entity operations (new)
    def add_entity(self, entity: Entity, context_id: Optional[ContextId] = None) -> 'EGGraph':
        """Add an entity to the graph in the specified context."""
        if context_id is None:
            context_id = self.root_context_id
        
        new_entities = self.entities.set(entity.id, entity)
        new_context_manager = self.context_manager.add_item_to_context(context_id, entity.id)
        
        return replace(self, entities=new_entities, context_manager=new_context_manager)
    
    def remove_entity(self, entity_id: EntityId) -> 'EGGraph':
        """Remove an entity from the graph."""
        if entity_id not in self.entities:
            raise EntityError(f"Entity {entity_id} not found")
        
        new_entities = self.entities.remove(entity_id)
        
        # Remove entity from any predicates
        new_predicates = self.predicates
        for predicate_id, predicate in self.predicates.items():
            if entity_id in predicate.entities:
                updated_predicate = predicate.remove_entity(entity_id)
                new_predicates = new_predicates.set(predicate_id, updated_predicate)
        
        # Remove entity from its context
        context_id = self.context_manager.find_item_context(entity_id)
        new_context_manager = self.context_manager
        if context_id is not None:
            new_context_manager = self.context_manager.remove_item_from_context(context_id, entity_id)
        
        return replace(self, 
                      entities=new_entities, 
                      predicates=new_predicates,
                      context_manager=new_context_manager)
    
    def get_entity(self, entity_id: EntityId) -> Optional[Entity]:
        """Get an entity by its ID."""
        return self.entities.get(entity_id)
    
    # Predicate operations (new)
    def add_predicate(self, predicate: Predicate, context_id: Optional[ContextId] = None) -> 'EGGraph':
        """Add a predicate to the graph in the specified context."""
        if context_id is None:
            context_id = self.root_context_id
        
        # Validate that all entities in the predicate exist
        for entity_id in predicate.entities:
            if entity_id not in self.entities:
                raise EntityError(f"Entity {entity_id} not found")
        
        new_predicates = self.predicates.set(predicate.id, predicate)
        new_context_manager = self.context_manager.add_item_to_context(context_id, predicate.id)
        
        return replace(self, predicates=new_predicates, context_manager=new_context_manager)
    
    def remove_predicate(self, predicate_id: PredicateId) -> 'EGGraph':
        """Remove a predicate from the graph."""
        if predicate_id not in self.predicates:
            raise PredicateError(f"Predicate {predicate_id} not found")
        
        new_predicates = self.predicates.remove(predicate_id)
        
        # Remove predicate from its context
        context_id = self.context_manager.find_item_context(predicate_id)
        new_context_manager = self.context_manager
        if context_id is not None:
            new_context_manager = self.context_manager.remove_item_from_context(context_id, predicate_id)
        
        return replace(self, 
                      predicates=new_predicates,
                      context_manager=new_context_manager)
    
    def get_predicate(self, predicate_id: PredicateId) -> Optional[Predicate]:
        """Get a predicate by its ID."""
        return self.predicates.get(predicate_id)
    
    # Ligature operations (existing)
    def add_ligature(self, ligature: Ligature) -> 'EGGraph':
        """Add a ligature to the graph."""
        new_ligatures = self.ligatures.set(ligature.id, ligature)
        return replace(self, ligatures=new_ligatures)
    
    def remove_ligature(self, ligature_id: LigatureId) -> 'EGGraph':
        """Remove a ligature from the graph."""
        if ligature_id not in self.ligatures:
            raise LigatureError(f"Ligature {ligature_id} not found")
        
        new_ligatures = self.ligatures.remove(ligature_id)
        return replace(self, ligatures=new_ligatures)
    
    def get_ligature(self, ligature_id: LigatureId) -> Optional[Ligature]:
        """Get a ligature by its ID."""
        return self.ligatures.get(ligature_id)
    
    # Context operations (updated)
    def create_context(self, context_type: str, parent_id: Optional[ContextId] = None,
                      name: Optional[str] = None) -> Tuple['EGGraph', Context]:
        """Create a new context in the graph.
        
        Args:
            context_type: The type of context to create
            parent_id: The ID of the parent context. If None, uses root context.
            name: Optional name for the context
            
        Returns:
            A tuple of (new_graph, new_context)
            
        Raises:
            ContextError: If the parent context doesn't exist.
        """
        new_context_manager, new_context = self.context_manager.create_context(
            context_type, parent_id, name
        )
        
        return replace(self, context_manager=new_context_manager), new_context
    
    # Graph traversal operations (existing)
    def find_incident_edges(self, node_id: NodeId) -> List[Edge]:
        """Find all edges incident to a node."""
        incident_edges = []
        for edge in self.edges.values():
            if node_id in edge.nodes:
                incident_edges.append(edge)
        return incident_edges
    
    def get_neighbors(self, node_id: NodeId) -> Set[NodeId]:
        """Get all nodes connected to a given node through edges."""
        neighbors = set()
        for edge in self.find_incident_edges(node_id):
            for neighbor_id in edge.nodes:
                if neighbor_id != node_id:
                    neighbors.add(neighbor_id)
        return neighbors
    
    # Entity-Predicate specific operations (new)
    def find_predicates_for_entity(self, entity_id: EntityId) -> List[Predicate]:
        """Find all predicates that connect to an entity."""
        connected_predicates = []
        for predicate in self.predicates.values():
            if entity_id in predicate.entities:
                connected_predicates.append(predicate)
        return connected_predicates
    
    def get_entities_in_predicate(self, predicate_id: PredicateId) -> List[Entity]:
        """Get all entities connected by a predicate."""
        predicate = self.get_predicate(predicate_id)
        if predicate is None:
            return []
        
        entities = []
        for entity_id in predicate.entities:
            entity = self.get_entity(entity_id)
            if entity is not None:
                entities.append(entity)
        return entities
    
    # Validation operations
    def validate_graph_integrity(self) -> List[str]:
        """Validate the integrity of the graph structure."""
        errors = []
        
        # Check that all entities referenced by predicates exist
        for predicate in self.predicates.values():
            for entity_id in predicate.entities:
                if entity_id not in self.entities:
                    errors.append(f"Predicate {predicate.id} references non-existent entity {entity_id}")
        
        # Check that all nodes referenced by edges exist
        for edge in self.edges.values():
            for node_id in edge.nodes:
                if node_id not in self.nodes:
                    errors.append(f"Edge {edge.id} references non-existent node {node_id}")
        
        # Check context integrity
        context_errors = self.context_manager.validate_integrity()
        errors.extend(context_errors)
        
        return errors

    def validate(self) -> 'ValidationResult':
        """Validate the graph and return a structured result.
        
        This is an alias method that provides a standardized validation interface
        compatible with test expectations and other validation patterns in the system.
        """
        from dataclasses import dataclass
        
        @dataclass
        class ValidationResult:
            is_valid: bool
            errors: List[str]
            warnings: List[str] = None
            
            def __post_init__(self):
                if self.warnings is None:
                    self.warnings = []
        
        errors = self.validate_graph_integrity()
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=[]
        )

