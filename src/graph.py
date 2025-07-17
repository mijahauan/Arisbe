"""
Redesigned graph operations for the EG-HG project with correct hypergraph mapping.

This module provides the EGGraph class using the correct hypergraph architecture:
- Entities (Lines of Identity) as primary nodes
- Predicates (Relations) as hyperedges connecting entities
- Contexts (Cuts) as logical scopes containing entities and predicates
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Iterator
from dataclasses import dataclass, replace
from collections import defaultdict, deque
import uuid

from .eg_types import (
    Entity, Predicate, Context,
    EntityId, PredicateId, ContextId, ItemId,
    new_entity_id, new_predicate_id, new_context_id,
    EGError, EntityError, PredicateError, ContextError, ValidationError,
    pmap, pset, pvector,
    create_simple_assertion, validate_predicate_entity_connection
)


@dataclass(frozen=True)
class EGGraph:
    """Existential graph with correct hypergraph mapping.
    
    This class represents an existential graph using the proper hypergraph structure:
    - Entities represent things that exist (Lines of Identity)
    - Predicates represent relations connecting entities (hyperedges)
    - Contexts represent logical scopes (cuts) containing entities and predicates
    """
    
    entities: pmap              # Dict[EntityId, Entity]
    predicates: pmap            # Dict[PredicateId, Predicate]
    contexts: pmap              # Dict[ContextId, Context]
    root_context_id: ContextId  # ID of the Sheet of Assertion
    
    @classmethod
    def create_empty(cls) -> 'EGGraph':
        """Create an empty existential graph with just the root context (Sheet of Assertion)."""
        root_context = Context.create(
            context_type="sheet_of_assertion",
            parent_context=None,
            depth=0
        )
        
        return cls(
            entities=pmap(),
            predicates=pmap(),
            contexts=pmap({root_context.id: root_context}),
            root_context_id=root_context.id
        )
    
    @classmethod
    def create_from_simple_assertion(cls, predicate_name: str, entity_names: List[str]) -> 'EGGraph':
        """Create a graph from a simple assertion like (Person Socrates).
        
        Args:
            predicate_name: Name of the predicate
            entity_names: Names of entities (constants or variables)
            
        Returns:
            A new EGGraph containing the assertion
        """
        graph = cls.create_empty()
        entities, predicate = create_simple_assertion(predicate_name, entity_names)
        
        # Add entities to the graph
        for entity in entities:
            graph = graph.add_entity(entity)
        
        # Add predicate to the graph
        graph = graph.add_predicate(predicate)
        
        return graph
    
    # Entity operations
    def add_entity(self, entity: Entity, context_id: Optional[ContextId] = None) -> 'EGGraph':
        """Add an entity to the graph in the specified context.
        
        Args:
            entity: The entity to add
            context_id: The context to add the entity to. If None, uses root context.
            
        Returns:
            A new EGGraph with the entity added
            
        Raises:
            ContextError: If the context doesn't exist
        """
        if context_id is None:
            context_id = self.root_context_id
        
        if context_id not in self.contexts:
            raise ContextError(f"Context {context_id} not found")
        
        # Add entity to entities collection
        new_entities = self.entities.set(entity.id, entity)
        
        # Add entity to the specified context
        context = self.contexts[context_id]
        updated_context = context.add_entity(entity.id)
        new_contexts = self.contexts.set(context_id, updated_context)
        
        return replace(self, entities=new_entities, contexts=new_contexts)
    
    def remove_entity(self, entity_id: EntityId) -> 'EGGraph':
        """Remove an entity from the graph.
        
        Args:
            entity_id: The ID of the entity to remove
            
        Returns:
            A new EGGraph with the entity removed
            
        Raises:
            EntityError: If the entity doesn't exist
        """
        if entity_id not in self.entities:
            raise EntityError(f"Entity {entity_id} not found")
        
        # Remove entity from entities collection
        new_entities = self.entities.remove(entity_id)
        
        # Remove entity from any predicates
        new_predicates = self.predicates
        for predicate_id, predicate in self.predicates.items():
            if entity_id in predicate.connected_entities:
                updated_predicate = predicate.remove_entity(entity_id)
                new_predicates = new_predicates.set(predicate_id, updated_predicate)
        
        # Remove entity from its context
        context_id = self.find_entity_context(entity_id)
        new_contexts = self.contexts
        if context_id is not None:
            context = self.contexts[context_id]
            updated_context = context.remove_entity(entity_id)
            new_contexts = new_contexts.set(context_id, updated_context)
        
        return replace(self, 
                      entities=new_entities, 
                      predicates=new_predicates,
                      contexts=new_contexts)
    
    def get_entity(self, entity_id: EntityId) -> Optional[Entity]:
        """Get an entity by its ID."""
        return self.entities.get(entity_id)
    
    def find_entity_context(self, entity_id: EntityId) -> Optional[ContextId]:
        """Find the context containing a specific entity."""
        for context_id, context in self.contexts.items():
            if entity_id in context.contained_entities:
                return context_id
        return None
    
    # Predicate operations
    def add_predicate(self, predicate: Predicate, context_id: Optional[ContextId] = None) -> 'EGGraph':
        """Add a predicate to the graph in the specified context.
        
        Args:
            predicate: The predicate to add
            context_id: The context to add the predicate to. If None, uses root context.
            
        Returns:
            A new EGGraph with the predicate added
            
        Raises:
            ContextError: If the context doesn't exist
            EntityError: If any connected entities don't exist
        """
        if context_id is None:
            context_id = self.root_context_id
        
        if context_id not in self.contexts:
            raise ContextError(f"Context {context_id} not found")
        
        # Validate that all connected entities exist
        validation_errors = validate_predicate_entity_connection(predicate, dict(self.entities))
        if validation_errors:
            raise EntityError("; ".join(validation_errors))
        
        # Add predicate to predicates collection
        new_predicates = self.predicates.set(predicate.id, predicate)
        
        # Add predicate to the specified context
        context = self.contexts[context_id]
        updated_context = context.add_predicate(predicate.id)
        new_contexts = self.contexts.set(context_id, updated_context)
        
        return replace(self, predicates=new_predicates, contexts=new_contexts)
    
    def remove_predicate(self, predicate_id: PredicateId) -> 'EGGraph':
        """Remove a predicate from the graph.
        
        Args:
            predicate_id: The ID of the predicate to remove
            
        Returns:
            A new EGGraph with the predicate removed
            
        Raises:
            PredicateError: If the predicate doesn't exist
        """
        if predicate_id not in self.predicates:
            raise PredicateError(f"Predicate {predicate_id} not found")
        
        # Remove predicate from predicates collection
        new_predicates = self.predicates.remove(predicate_id)
        
        # Remove predicate from its context
        context_id = self.find_predicate_context(predicate_id)
        new_contexts = self.contexts
        if context_id is not None:
            context = self.contexts[context_id]
            updated_context = context.remove_predicate(predicate_id)
            new_contexts = new_contexts.set(context_id, updated_context)
        
        return replace(self, predicates=new_predicates, contexts=new_contexts)
    
    def get_predicate(self, predicate_id: PredicateId) -> Optional[Predicate]:
        """Get a predicate by its ID."""
        return self.predicates.get(predicate_id)
    
    def find_predicate_context(self, predicate_id: PredicateId) -> Optional[ContextId]:
        """Find the context containing a specific predicate."""
        for context_id, context in self.contexts.items():
            if predicate_id in context.contained_predicates:
                return context_id
        return None
    
    # Context operations
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
            ContextError: If the parent context doesn't exist
        """
        if parent_id is None:
            parent_id = self.root_context_id
        
        if parent_id not in self.contexts:
            raise ContextError(f"Parent context {parent_id} not found")
        
        parent_context = self.contexts[parent_id]
        new_context = Context.create(
            context_type=context_type,
            parent_context=parent_id,
            depth=parent_context.depth + 1
        )
        
        if name:
            new_context = new_context.set_property("name", name)
        
        new_contexts = self.contexts.set(new_context.id, new_context)
        new_graph = replace(self, contexts=new_contexts)
        
        return new_graph, new_context
    
    def remove_context(self, context_id: ContextId) -> 'EGGraph':
        """Remove a context and all its contents from the graph.
        
        Args:
            context_id: The ID of the context to remove
            
        Returns:
            A new EGGraph with the context removed
            
        Raises:
            ContextError: If trying to remove the root context
        """
        if context_id == self.root_context_id:
            raise ContextError("Cannot remove root context")
        
        if context_id not in self.contexts:
            raise ContextError(f"Context {context_id} not found")
        
        context = self.contexts[context_id]
        
        # Remove all entities in the context
        new_entities = self.entities
        for entity_id in context.contained_entities:
            new_entities = new_entities.remove(entity_id)
        
        # Remove all predicates in the context
        new_predicates = self.predicates
        for predicate_id in context.contained_predicates:
            new_predicates = new_predicates.remove(predicate_id)
        
        # Remove the context itself
        new_contexts = self.contexts.remove(context_id)
        
        return replace(self, 
                      entities=new_entities,
                      predicates=new_predicates, 
                      contexts=new_contexts)
    
    def get_context(self, context_id: ContextId) -> Optional[Context]:
        """Get a context by its ID."""
        return self.contexts.get(context_id)
    
    # Graph traversal and analysis operations
    def find_predicates_for_entity(self, entity_id: EntityId) -> List[Predicate]:
        """Find all predicates that connect to a specific entity.
        
        Args:
            entity_id: The ID of the entity
            
        Returns:
            A list of predicates connected to the entity
        """
        connected_predicates = []
        for predicate in self.predicates.values():
            if entity_id in predicate.connected_entities:
                connected_predicates.append(predicate)
        return connected_predicates
    
    def find_entities_for_predicate(self, predicate_id: PredicateId) -> List[Entity]:
        """Find all entities connected to a specific predicate.
        
        Args:
            predicate_id: The ID of the predicate
            
        Returns:
            A list of entities connected to the predicate
        """
        predicate = self.get_predicate(predicate_id)
        if not predicate:
            return []
        
        connected_entities = []
        for entity_id in predicate.connected_entities:
            entity = self.get_entity(entity_id)
            if entity:
                connected_entities.append(entity)
        
        return connected_entities
    
    def find_shared_entities(self, predicate_id1: PredicateId, predicate_id2: PredicateId) -> List[Entity]:
        """Find entities that are shared between two predicates (Lines of Identity).
        
        Args:
            predicate_id1: ID of the first predicate
            predicate_id2: ID of the second predicate
            
        Returns:
            A list of entities shared between the predicates
        """
        pred1 = self.get_predicate(predicate_id1)
        pred2 = self.get_predicate(predicate_id2)
        
        if not pred1 or not pred2:
            return []
        
        shared_entity_ids = set(pred1.connected_entities) & set(pred2.connected_entities)
        shared_entities = []
        
        for entity_id in shared_entity_ids:
            entity = self.get_entity(entity_id)
            if entity:
                shared_entities.append(entity)
        
        return shared_entities
    
    def get_entities_in_context(self, context_id: ContextId) -> List[Entity]:
        """Get all entities in a specific context.
        
        Args:
            context_id: The ID of the context
            
        Returns:
            A list of entities in the context
        """
        context = self.get_context(context_id)
        if not context:
            return []
        
        entities = []
        for entity_id in context.contained_entities:
            entity = self.get_entity(entity_id)
            if entity:
                entities.append(entity)
        
        return entities
    
    def get_predicates_in_context(self, context_id: ContextId) -> List[Predicate]:
        """Get all predicates in a specific context.
        
        Args:
            context_id: The ID of the context
            
        Returns:
            A list of predicates in the context
        """
        context = self.get_context(context_id)
        if not context:
            return []
        
        predicates = []
        for predicate_id in context.contained_predicates:
            predicate = self.get_predicate(predicate_id)
            if predicate:
                predicates.append(predicate)
        
        return predicates
    
    # Validation operations
    def validate_graph_consistency(self) -> List[str]:
        """Validate the consistency of the entire graph.
        
        Returns:
            A list of error messages. Empty list means no errors.
        """
        errors = []
        
        # Validate that root context exists
        if self.root_context_id not in self.contexts:
            errors.append("Root context not found")
            return errors  # Can't continue without root context
        
        # Validate context hierarchy
        for context_id, context in self.contexts.items():
            if context.parent_context is not None:
                if context.parent_context not in self.contexts:
                    errors.append(f"Context {context_id} has non-existent parent {context.parent_context}")
        
        # Validate that all predicate entities exist
        for predicate_id, predicate in self.predicates.items():
            validation_errors = validate_predicate_entity_connection(predicate, dict(self.entities))
            errors.extend(validation_errors)
        
        # Validate that all entities are in some context
        all_context_entities = set()
        for context in self.contexts.values():
            all_context_entities.update(context.contained_entities)
        
        for entity_id in self.entities:
            if entity_id not in all_context_entities:
                errors.append(f"Entity {entity_id} is not in any context")
        
        # Validate that all predicates are in some context
        all_context_predicates = set()
        for context in self.contexts.values():
            all_context_predicates.update(context.contained_predicates)
        
        for predicate_id in self.predicates:
            if predicate_id not in all_context_predicates:
                errors.append(f"Predicate {predicate_id} is not in any context")
        
        return errors
    
    # Utility methods
    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get statistics about the graph.
        
        Returns:
            A dictionary containing various graph statistics
        """
        return {
            'num_contexts': len(self.contexts),
            'num_entities': len(self.entities),
            'num_predicates': len(self.predicates),
            'max_context_depth': max(ctx.depth for ctx in self.contexts.values()) if self.contexts else 0,
            'entities_by_type': {
                'variables': len([e for e in self.entities.values() if e.is_variable]),
                'constants': len([e for e in self.entities.values() if e.is_constant]),
                'anonymous': len([e for e in self.entities.values() if e.is_anonymous])
            },
            'predicates_by_arity': {
                'unary': len([p for p in self.predicates.values() if p.is_unary]),
                'binary': len([p for p in self.predicates.values() if p.is_binary]),
                'nary': len([p for p in self.predicates.values() if p.is_nary])
            }
        }
    
    def to_simple_representation(self) -> Dict[str, Any]:
        """Convert the graph to a simple dictionary representation for debugging.
        
        Returns:
            A dictionary representation of the graph
        """
        return {
            'entities': {
                str(entity_id): {
                    'name': entity.name,
                    'type': 'variable' if entity.is_variable else 'constant' if entity.is_constant else 'anonymous'
                }
                for entity_id, entity in self.entities.items()
            },
            'predicates': {
                str(predicate_id): {
                    'name': predicate.name,
                    'arity': predicate.arity,
                    'connected_entities': [str(eid) for eid in predicate.connected_entities]
                }
                for predicate_id, predicate in self.predicates.items()
            },
            'contexts': {
                str(context_id): {
                    'type': context.context_type,
                    'depth': context.depth,
                    'entities': [str(eid) for eid in context.contained_entities],
                    'predicates': [str(pid) for pid in context.contained_predicates]
                }
                for context_id, context in self.contexts.items()
            },
            'root_context': str(self.root_context_id)
        }
    
    def __str__(self) -> str:
        """String representation of the graph."""
        stats = self.get_graph_statistics()
        return (f"EGGraph(contexts={stats['num_contexts']}, "
                f"entities={stats['num_entities']}, "
                f"predicates={stats['num_predicates']})")


# Utility functions for creating common graph patterns

def create_unary_assertion(predicate_name: str, entity_name: str) -> EGGraph:
    """Create a graph with a unary assertion like (Person Socrates).
    
    Args:
        predicate_name: Name of the predicate
        entity_name: Name of the entity
        
    Returns:
        A new EGGraph containing the assertion
    """
    return EGGraph.create_from_simple_assertion(predicate_name, [entity_name])


def create_binary_assertion(predicate_name: str, entity1_name: str, entity2_name: str) -> EGGraph:
    """Create a graph with a binary assertion like (Loves Mary John).
    
    Args:
        predicate_name: Name of the predicate
        entity1_name: Name of the first entity
        entity2_name: Name of the second entity
        
    Returns:
        A new EGGraph containing the assertion
    """
    return EGGraph.create_from_simple_assertion(predicate_name, [entity1_name, entity2_name])


def create_existential_assertion(predicate_name: str, variable_name: str) -> EGGraph:
    """Create a graph with an existential assertion like (exists (x) (Person x)).
    
    Args:
        predicate_name: Name of the predicate
        variable_name: Name of the variable
        
    Returns:
        A new EGGraph containing the existential assertion
    """
    # Create empty graph
    graph = EGGraph.create_empty()
    
    # Create existential context
    graph, existential_context = graph.create_context("existential")
    
    # Create variable entity
    variable_entity = Entity.create_variable(variable_name)
    graph = graph.add_entity(variable_entity, existential_context.id)
    
    # Create predicate connecting to the variable
    predicate = Predicate.create(predicate_name, [variable_entity.id])
    graph = graph.add_predicate(predicate, existential_context.id)
    
    return graph

