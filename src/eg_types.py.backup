"""
Redesigned foundational types for the EG-HG project with correct hypergraph mapping.

This module provides robust, immutable data structures for representing
existential graphs using the correct hypergraph mapping:
- Entities (Lines of Identity) as primary nodes
- Predicates (Relations) as hyperedges connecting entities
- Contexts (Cuts) as logical scopes containing entities and predicates
"""

import uuid
from typing import Dict, List, Optional, Set, Any, NewType, Union
from pyrsistent import pmap, pset, pvector, PMap, PSet, PVector
from dataclasses import dataclass, replace
from copy import deepcopy

# Type definitions for the correct hypergraph mapping
EntityId = NewType('EntityId', uuid.UUID)
PredicateId = NewType('PredicateId', uuid.UUID)
ContextId = NewType('ContextId', uuid.UUID)
ItemId = Union[EntityId, PredicateId]  # Items that can be in contexts
Properties = Dict[str, Any]

# ID generation functions
def new_entity_id() -> EntityId:
    """Generate a new unique entity ID."""
    return EntityId(uuid.uuid4())

def new_predicate_id() -> PredicateId:
    """Generate a new unique predicate ID."""
    return PredicateId(uuid.uuid4())

def new_context_id() -> ContextId:
    """Generate a new unique context ID."""
    return ContextId(uuid.uuid4())

# Exception hierarchy
class EGError(Exception):
    """Base class for all exceptions in the EG system."""
    pass

class EntityError(EGError):
    """Exception raised for errors related to entities."""
    pass

class PredicateError(EGError):
    """Exception raised for errors related to predicates."""
    pass

class ContextError(EGError):
    """Exception raised for errors related to contexts."""
    pass

class ValidationError(EGError):
    """Exception raised for validation errors in the EG system.
    
    This is used when operations would violate logical constraints or
    when input data doesn't meet validation requirements.
    """
    pass

# Core data structures with correct hypergraph mapping

@dataclass(frozen=True)
class Entity:
    """Represents an entity (Line of Identity) in an existential graph.
    
    Entities are the primary nodes in the hypergraph, representing things that exist.
    They correspond to variables and constants in CLIF expressions and are visually
    rendered as Lines of Identity in Peirce's notation.
    """
    
    id: EntityId
    variable_name: Optional[str]  # For variables (x, y, z) in CLIF
    constant_name: Optional[str]  # For constants (Socrates, Mary) in CLIF
    properties: PMap
    
    @classmethod
    def create_variable(cls, variable_name: str, properties: Optional[Dict[str, Any]] = None,
                       id: Optional[EntityId] = None) -> 'Entity':
        """Create a new entity representing a variable."""
        return cls(
            id=id or new_entity_id(),
            variable_name=variable_name,
            constant_name=None,
            properties=pmap(properties or {})
        )
    
    @classmethod
    def create_constant(cls, constant_name: str, properties: Optional[Dict[str, Any]] = None,
                       id: Optional[EntityId] = None) -> 'Entity':
        """Create a new entity representing a constant."""
        return cls(
            id=id or new_entity_id(),
            variable_name=None,
            constant_name=constant_name,
            properties=pmap(properties or {})
        )
    
    @classmethod
    def create_anonymous(cls, properties: Optional[Dict[str, Any]] = None,
                        id: Optional[EntityId] = None) -> 'Entity':
        """Create a new anonymous entity (for complex expressions)."""
        return cls(
            id=id or new_entity_id(),
            variable_name=None,
            constant_name=None,
            properties=pmap(properties or {})
        )
    
    @property
    def name(self) -> str:
        """Get the display name of this entity."""
        if self.constant_name:
            return self.constant_name
        elif self.variable_name:
            return self.variable_name
        else:
            return f"entity_{str(self.id)[:8]}"
    
    @property
    def is_variable(self) -> bool:
        """Check if this entity represents a variable."""
        return self.variable_name is not None
    
    @property
    def is_constant(self) -> bool:
        """Check if this entity represents a constant."""
        return self.constant_name is not None
    
    @property
    def is_anonymous(self) -> bool:
        """Check if this entity is anonymous."""
        return self.variable_name is None and self.constant_name is None
    
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
        return f"Entity({self.name})"


@dataclass(frozen=True)
class Predicate:
    """Represents a predicate (relation) in an existential graph.
    
    Predicates are hyperedges in the hypergraph, connecting multiple entities
    to express relationships or properties. They correspond to predicate symbols
    in CLIF expressions and are visually rendered as rectangular labels attached
    to Lines of Identity in Peirce's notation.
    """
    
    id: PredicateId
    name: str                      # Predicate name (Person, Loves, etc.)
    arity: int                     # Number of entities this predicate connects
    connected_entities: PVector    # Ordered list of EntityIds
    properties: PMap
    
    @classmethod
    def create(cls, name: str, connected_entities: Optional[List[EntityId]] = None,
               properties: Optional[Dict[str, Any]] = None,
               id: Optional[PredicateId] = None) -> 'Predicate':
        """Create a new predicate with proper defaults."""
        entities = pvector(connected_entities or [])
        return cls(
            id=id or new_predicate_id(),
            name=name,
            arity=len(entities),
            connected_entities=entities,
            properties=pmap(properties or {})
        )
    
    def add_entity(self, entity_id: EntityId) -> 'Predicate':
        """Return a new predicate with the specified entity added."""
        new_entities = self.connected_entities.append(entity_id)
        return replace(self, 
                      connected_entities=new_entities,
                      arity=len(new_entities))
    
    def remove_entity(self, entity_id: EntityId) -> 'Predicate':
        """Return a new predicate with the specified entity removed."""
        try:
            index = self.connected_entities.index(entity_id)
            new_entities = self.connected_entities.delete(index)
            return replace(self,
                          connected_entities=new_entities,
                          arity=len(new_entities))
        except ValueError:
            return self  # Entity not found, return unchanged
    
    def replace_entity(self, old_entity_id: EntityId, new_entity_id: EntityId) -> 'Predicate':
        """Return a new predicate with an entity replaced."""
        try:
            index = self.connected_entities.index(old_entity_id)
            new_entities = self.connected_entities.set(index, new_entity_id)
            return replace(self, connected_entities=new_entities)
        except ValueError:
            return self  # Entity not found, return unchanged
    
    def set_property(self, key: str, value: Any) -> 'Predicate':
        """Return a new predicate with the specified property set."""
        new_properties = self.properties.set(key, value)
        return replace(self, properties=new_properties)
    
    @property
    def is_unary(self) -> bool:
        """Check if this is a unary predicate (property)."""
        return self.arity == 1
    
    @property
    def is_binary(self) -> bool:
        """Check if this is a binary predicate (relation)."""
        return self.arity == 2
    
    @property
    def is_nary(self) -> bool:
        """Check if this is an n-ary predicate (n > 2)."""
        return self.arity > 2
    
    def __str__(self) -> str:
        return f"Predicate({self.name}/{self.arity})"


@dataclass(frozen=True)
class Context:
    """Represents a context (cut) in an existential graph.
    
    Contexts define logical scopes containing entities and predicates.
    They correspond to quantifier scopes in CLIF expressions and are
    visually rendered as cuts (oval boundaries) in Peirce's notation.
    """
    
    id: ContextId
    context_type: str
    parent_context: Optional[ContextId]
    depth: int
    contained_entities: PSet       # EntityIds in this context
    contained_predicates: PSet     # PredicateIds in this context
    properties: PMap
    
    @classmethod
    def create(cls, context_type: str, parent_context: Optional[ContextId] = None,
               depth: int = 0, 
               contained_entities: Optional[Set[EntityId]] = None,
               contained_predicates: Optional[Set[PredicateId]] = None,
               properties: Optional[Dict[str, Any]] = None, 
               id: Optional[ContextId] = None) -> 'Context':
        """Create a new context with proper defaults."""
        return cls(
            id=id or new_context_id(),
            context_type=context_type,
            parent_context=parent_context,
            depth=depth,
            contained_entities=pset(contained_entities or set()),
            contained_predicates=pset(contained_predicates or set()),
            properties=pmap(properties or {})
        )
    
    def add_entity(self, entity_id: EntityId) -> 'Context':
        """Return a new context with the specified entity added."""
        new_entities = self.contained_entities.add(entity_id)
        return replace(self, contained_entities=new_entities)
    
    def remove_entity(self, entity_id: EntityId) -> 'Context':
        """Return a new context with the specified entity removed."""
        if entity_id not in self.contained_entities:
            return self
        new_entities = self.contained_entities.remove(entity_id)
        return replace(self, contained_entities=new_entities)
    
    def add_predicate(self, predicate_id: PredicateId) -> 'Context':
        """Return a new context with the specified predicate added."""
        new_predicates = self.contained_predicates.add(predicate_id)
        return replace(self, contained_predicates=new_predicates)
    
    def remove_predicate(self, predicate_id: PredicateId) -> 'Context':
        """Return a new context with the specified predicate removed."""
        if predicate_id not in self.contained_predicates:
            return self
        new_predicates = self.contained_predicates.remove(predicate_id)
        return replace(self, contained_predicates=new_predicates)
    
    def get_all_items(self) -> Set[ItemId]:
        """Get all items (entities and predicates) in this context."""
        return set(self.contained_entities) | set(self.contained_predicates)
    
    @property
    def is_positive(self) -> bool:
        """Check if this context has positive polarity (even depth)."""
        return self.depth % 2 == 0
    
    @property
    def is_negative(self) -> bool:
        """Check if this context has negative polarity (odd depth)."""
        return self.depth % 2 == 1
    
    @property
    def is_root(self) -> bool:
        """Check if this is the root context (Sheet of Assertion)."""
        return self.parent_context is None
    
    def __str__(self) -> str:
        return f"Context({self.context_type}, depth={self.depth}, entities={len(self.contained_entities)}, predicates={len(self.contained_predicates)})"


# Utility functions for working with the new architecture

def create_simple_assertion(predicate_name: str, entity_names: List[str]) -> tuple[List[Entity], Predicate]:
    """Create entities and a predicate for a simple assertion.
    
    Args:
        predicate_name: Name of the predicate
        entity_names: Names of entities (constants or variables)
        
    Returns:
        Tuple of (entities_list, predicate)
    """
    entities = []
    entity_ids = []
    
    for name in entity_names:
        if name.islower() and len(name) == 1:
            # Single lowercase letter = variable
            entity = Entity.create_variable(name)
        else:
            # Otherwise = constant
            entity = Entity.create_constant(name)
        entities.append(entity)
        entity_ids.append(entity.id)
    
    predicate = Predicate.create(predicate_name, entity_ids)
    
    return entities, predicate


def validate_predicate_entity_connection(predicate: Predicate, entities: Dict[EntityId, Entity]) -> List[str]:
    """Validate that a predicate's connected entities exist and are valid.
    
    Args:
        predicate: The predicate to validate
        entities: Dictionary of all entities in the graph
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    for entity_id in predicate.connected_entities:
        if entity_id not in entities:
            errors.append(f"Predicate {predicate.name} references non-existent entity {entity_id}")
    
    if predicate.arity != len(predicate.connected_entities):
        errors.append(f"Predicate {predicate.name} arity mismatch: declared {predicate.arity}, actual {len(predicate.connected_entities)}")
    
    return errors


# Export all public symbols
__all__ = [
    # Types
    'EntityId', 'PredicateId', 'ContextId', 'ItemId', 'Properties',
    
    # ID generators
    'new_entity_id', 'new_predicate_id', 'new_context_id',
    
    # Core classes
    'Entity', 'Predicate', 'Context',
    
    # Utility functions
    'create_simple_assertion', 'validate_predicate_entity_connection',
    
    # Exceptions
    'EGError', 'EntityError', 'PredicateError', 'ContextError', 'ValidationError',
    
    # Pyrsistent imports for convenience
    'pmap', 'pset', 'pvector'
]

