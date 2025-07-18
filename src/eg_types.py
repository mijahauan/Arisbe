"""
Foundational types for the EG-HG rebuild project.

This module provides robust, immutable data structures for representing
existential graphs, including nodes, edges, contexts, ligatures, entities, and predicates.
"""

import uuid
from typing import Dict, List, Optional, Set, Any, NewType, Union
from pyrsistent import pmap, pset, pvector, PMap, PSet, PVector
from dataclasses import dataclass, replace
from copy import deepcopy

# Type definitions
NodeId = NewType('NodeId', uuid.UUID)
EdgeId = NewType('EdgeId', uuid.UUID)
ContextId = NewType('ContextId', uuid.UUID)
LigatureId = NewType('LigatureId', uuid.UUID)
EntityId = NewType('EntityId', uuid.UUID)
PredicateId = NewType('PredicateId', uuid.UUID)
ItemId = uuid.UUID  # Can be any of the above IDs
NodeType = NewType('NodeType', str)
EdgeType = NewType('EdgeType', str)
ContextType = NewType('ContextType', str)
Properties = Dict[str, Any]

# ID generation functions
def new_node_id() -> NodeId:
    """Generate a new unique node ID."""
    return NodeId(uuid.uuid4())

def new_edge_id() -> EdgeId:
    """Generate a new unique edge ID."""
    return EdgeId(uuid.uuid4())

def new_context_id() -> ContextId:
    """Generate a new unique context ID."""
    return ContextId(uuid.uuid4())

def new_ligature_id() -> LigatureId:
    """Generate a new unique ligature ID."""
    return LigatureId(uuid.uuid4())

def new_entity_id() -> EntityId:
    """Generate a new unique entity ID."""
    return EntityId(uuid.uuid4())

def new_predicate_id() -> PredicateId:
    """Generate a new unique predicate ID."""
    return PredicateId(uuid.uuid4())

# Exception hierarchy
class EGError(Exception):
    """Base class for all exceptions in the EG system."""
    pass

class NodeError(EGError):
    """Exception raised for errors related to nodes."""
    pass

class EdgeError(EGError):
    """Exception raised for errors related to edges."""
    pass

class ContextError(EGError):
    """Exception raised for errors related to contexts."""
    pass

class LigatureError(EGError):
    """Exception raised for errors related to ligatures."""
    pass

class EntityError(EGError):
    """Exception raised for errors related to entities."""
    pass

class PredicateError(EGError):
    """Exception raised for errors related to predicates."""
    pass

class ValidationError(EGError):
    """Exception raised for validation errors in the EG system.
    
    This is used when operations would violate logical constraints or
    when input data doesn't meet validation requirements.
    """
    pass

# Core data structures using regular classes with immutability
@dataclass(frozen=True)
class Node:
    """Represents a node in an existential graph."""
    
    id: NodeId
    node_type: str
    properties: PMap
    
    @classmethod
    def create(cls, node_type: str, properties: Optional[Dict[str, Any]] = None, 
               id: Optional[NodeId] = None) -> 'Node':
        """Create a new node with proper defaults."""
        return cls(
            id=id or new_node_id(),
            node_type=node_type,
            properties=pmap(properties or {})
        )
    
    def set(self, key: str, value: Any) -> 'Node':
        """Return a new node with the specified property set."""
        new_properties = self.properties.set(key, value)
        return replace(self, properties=new_properties)
    
    def remove(self, key: str) -> 'Node':
        """Return a new node with the specified property removed."""
        if key not in self.properties:
            return self
        new_properties = self.properties.remove(key)
        return replace(self, properties=new_properties)
    
    def __str__(self) -> str:
        return f"Node({self.node_type}, {dict(self.properties)})"


@dataclass(frozen=True)
class Edge:
    """Represents an edge in an existential graph."""
    
    id: EdgeId
    edge_type: str
    nodes: PSet
    properties: PMap
    
    @classmethod
    def create(cls, edge_type: str, nodes: Optional[Set[NodeId]] = None,
               properties: Optional[Dict[str, Any]] = None,
               id: Optional[EdgeId] = None) -> 'Edge':
        """Create a new edge with proper defaults."""
        return cls(
            id=id or new_edge_id(),
            edge_type=edge_type,
            nodes=pset(nodes or set()),
            properties=pmap(properties or {})
        )
    
    def add_node(self, node_id: NodeId) -> 'Edge':
        """Return a new edge with the specified node added."""
        new_nodes = self.nodes.add(node_id)
        return replace(self, nodes=new_nodes)
    
    def remove_node(self, node_id: NodeId) -> 'Edge':
        """Return a new edge with the specified node removed."""
        if node_id not in self.nodes:
            return self
        new_nodes = self.nodes.remove(node_id)
        return replace(self, nodes=new_nodes)
    
    def set(self, key: str, value: Any) -> 'Edge':
        """Return a new edge with the specified property set."""
        new_properties = self.properties.set(key, value)
        return replace(self, properties=new_properties)
    
    def __str__(self) -> str:
        return f"Edge({self.edge_type}, nodes={len(self.nodes)})"


@dataclass(frozen=True)
class Context:
    """Represents a context (cut) in an existential graph."""
    
    id: ContextId
    context_type: str
    parent_context: Optional[ContextId]
    depth: int
    contained_items: PSet
    properties: PMap
    
    @classmethod
    def create(cls, context_type: str, parent_context: Optional[ContextId] = None,
               depth: int = 0, contained_items: Optional[Set[ItemId]] = None,
               properties: Optional[Dict[str, Any]] = None, 
               id: Optional[ContextId] = None) -> 'Context':
        """Create a new context with proper defaults."""
        return cls(
            id=id or new_context_id(),
            context_type=context_type,
            parent_context=parent_context,
            depth=depth,
            contained_items=pset(contained_items or set()),
            properties=pmap(properties or {})
        )
    
    def add_item(self, item_id: ItemId) -> 'Context':
        """Return a new context with the specified item added."""
        new_items = self.contained_items.add(item_id)
        return replace(self, contained_items=new_items)
    
    def remove_item(self, item_id: ItemId) -> 'Context':
        """Return a new context with the specified item removed."""
        if item_id not in self.contained_items:
            return self
        new_items = self.contained_items.remove(item_id)
        return replace(self, contained_items=new_items)
    
    def with_items(self, items: Set[ItemId]) -> 'Context':
        """Return a new context with the specified items."""
        return replace(self, contained_items=pset(items))
    
    def set_property(self, key: str, value: Any) -> 'Context':
        """Return a new context with the specified property set."""
        new_properties = self.properties.set(key, value)
        return replace(self, properties=new_properties)
    
    @property
    def is_positive(self) -> bool:
        """Check if this context has positive polarity (even depth)."""
        return self.depth % 2 == 0
    
    @property
    def is_negative(self) -> bool:
        """Check if this context has negative polarity (odd depth)."""
        return self.depth % 2 == 1
    
    def __str__(self) -> str:
        return f"Context({self.context_type}, depth={self.depth}, items={len(self.contained_items)})"


@dataclass(frozen=True)
class Ligature:
    """Represents a ligature (equality relationship) in an existential graph."""
    
    id: LigatureId
    nodes: PSet
    edges: PSet
    properties: PMap
    
    @classmethod
    def create(cls, nodes: Optional[Set[NodeId]] = None,
               edges: Optional[Set[EdgeId]] = None,
               properties: Optional[Dict[str, Any]] = None,
               id: Optional[LigatureId] = None) -> 'Ligature':
        """Create a new ligature with proper defaults."""
        return cls(
            id=id or new_ligature_id(),
            nodes=pset(nodes or set()),
            edges=pset(edges or set()),
            properties=pmap(properties or {})
        )
    
    def add_node(self, node_id: NodeId) -> 'Ligature':
        """Return a new ligature with the specified node added."""
        new_nodes = self.nodes.add(node_id)
        return replace(self, nodes=new_nodes)
    
    def add_edge(self, edge_id: EdgeId) -> 'Ligature':
        """Return a new ligature with the specified edge added."""
        new_edges = self.edges.add(edge_id)
        return replace(self, edges=new_edges)
    
    def union(self, other: 'Ligature') -> 'Ligature':
        """Return a new ligature that is the union of this and another ligature."""
        new_nodes = self.nodes.union(other.nodes)
        new_edges = self.edges.union(other.edges)
        return replace(self, nodes=new_nodes, edges=new_edges)
    
    def __str__(self) -> str:
        return f"Ligature(nodes={len(self.nodes)}, edges={len(self.edges)})"


@dataclass(frozen=True)
class Entity:
    """Represents an entity (Line of Identity) in an existential graph.
    
    Entities represent things that exist - variables, constants, or anonymous entities.
    In Peirce's notation, these are the Lines of Identity that connect predicates.
    """
    
    id: EntityId
    name: Optional[str]
    entity_type: str  # 'variable', 'constant', 'anonymous'
    properties: PMap
    
    @classmethod
    def create(cls, name: Optional[str] = None, entity_type: str = 'anonymous',
               properties: Optional[Dict[str, Any]] = None,
               id: Optional[EntityId] = None) -> 'Entity':
        """Create a new entity with proper defaults."""
        return cls(
            id=id or new_entity_id(),
            name=name,
            entity_type=entity_type,
            properties=pmap(properties or {})
        )
    
    def set_property(self, key: str, value: Any) -> 'Entity':
        """Return a new entity with the specified property set."""
        new_properties = self.properties.set(key, value)
        return replace(self, properties=new_properties)
    
    def remove_property(self, key: str) -> 'Entity':
        """Return a new entity with the specified property removed."""
        if key not in self.properties:
            return self
        new_properties = self.properties.remove(key)
        return replace(self, properties=new_properties)
    
    def __str__(self) -> str:
        return f"Entity({self.name or 'anonymous'}, {self.entity_type})"


@dataclass(frozen=True)
class Predicate:
    """Represents a predicate (hyperedge) in an existential graph.
    
    Predicates represent relations that connect entities. In hypergraph terms,
    predicates are hyperedges that can connect multiple entities.
    
    Extended to support Dau's function symbols:
    - predicate_type distinguishes between 'relation' and 'function'
    - return_entity identifies the result entity for functions
    """
    
    id: PredicateId
    name: str
    entities: PVector  # List of EntityId in order
    arity: int
    properties: PMap
    predicate_type: str = 'relation'  # 'relation' or 'function' - default for backward compatibility
    return_entity: Optional[EntityId] = None  # For functions, the entity representing the result
    
    @classmethod
    def create(cls, name: str, entities: Optional[List[EntityId]] = None,
               arity: Optional[int] = None,
               predicate_type: str = 'relation',
               return_entity: Optional[EntityId] = None,
               properties: Optional[Dict[str, Any]] = None,
               id: Optional[PredicateId] = None) -> 'Predicate':
        """Create a new predicate with proper defaults."""
        entities_list = entities or []
        return cls(
            id=id or new_predicate_id(),
            name=name,
            entities=pvector(entities_list),
            arity=arity if arity is not None else len(entities_list),
            properties=pmap(properties or {}),
            predicate_type=predicate_type,
            return_entity=return_entity
        )
    
    def add_entity(self, entity_id: EntityId) -> 'Predicate':
        """Return a new predicate with the specified entity added."""
        new_entities = self.entities.append(entity_id)
        return replace(self, entities=new_entities, arity=len(new_entities))
    
    def remove_entity(self, entity_id: EntityId) -> 'Predicate':
        """Return a new predicate with the specified entity removed."""
        try:
            index = self.entities.index(entity_id)
            new_entities = self.entities.delete(index)
            return replace(self, entities=new_entities, arity=len(new_entities))
        except ValueError:
            return self
    
    def set_property(self, key: str, value: Any) -> 'Predicate':
        """Return a new predicate with the specified property set."""
        new_properties = self.properties.set(key, value)
        return replace(self, properties=new_properties)
    
    @property
    def is_function(self) -> bool:
        """Check if this predicate represents a function."""
        return self.predicate_type == 'function'
    
    @property
    def is_relation(self) -> bool:
        """Check if this predicate represents a relation."""
        return self.predicate_type == 'relation'
    
    def __str__(self) -> str:
        type_str = f", {self.predicate_type}" if self.predicate_type != 'relation' else ""
        return f"Predicate({self.name}, arity={self.arity}{type_str})"


# Export all public symbols
__all__ = [
    # Types
    'NodeId', 'EdgeId', 'ContextId', 'LigatureId', 'EntityId', 'PredicateId', 'ItemId',
    'NodeType', 'EdgeType', 'ContextType', 'Properties',
    
    # ID generators
    'new_node_id', 'new_edge_id', 'new_context_id', 'new_ligature_id',
    'new_entity_id', 'new_predicate_id',
    
    # Core classes
    'Node', 'Edge', 'Context', 'Ligature', 'Entity', 'Predicate',
    
    # Exceptions
    'EGError', 'NodeError', 'EdgeError', 'ContextError', 'LigatureError', 
    'EntityError', 'PredicateError', 'ValidationError',
    
    # Pyrsistent imports for convenience
    'pmap', 'pset', 'pvector'
]

