"""
Updated tests for the redesigned EG-HG core types with correct hypergraph mapping.

This test suite validates the new Entity-Predicate architecture while preserving
all the quality standards and test patterns from the original test suite.
"""

import pytest
import uuid
from hypothesis import given, strategies as st

from src.eg_types import (
    Entity, Predicate, Context,
    EntityId, PredicateId, ContextId,
    new_entity_id, new_predicate_id, new_context_id,
    EntityError, PredicateError, ContextError, ValidationError,
    create_simple_assertion, validate_predicate_entity_connection,
    pmap, pset
)


class TestIdentifierGeneration:
    """Test ID generation functions."""
    
    def test_entity_id_generation(self):
        """Test that entity IDs are unique."""
        id1 = new_entity_id()
        id2 = new_entity_id()
        assert id1 != id2
        assert isinstance(id1, uuid.UUID)
        assert isinstance(id2, uuid.UUID)
    
    def test_predicate_id_generation(self):
        """Test that predicate IDs are unique."""
        id1 = new_predicate_id()
        id2 = new_predicate_id()
        assert id1 != id2
        assert isinstance(id1, uuid.UUID)
        assert isinstance(id2, uuid.UUID)
    
    def test_context_id_generation(self):
        """Test that context IDs are unique."""
        id1 = new_context_id()
        id2 = new_context_id()
        assert id1 != id2
        assert isinstance(id1, uuid.UUID)
        assert isinstance(id2, uuid.UUID)


class TestEntity:
    """Test the Entity class (replaces Node tests)."""
    
    def test_entity_creation_variable(self):
        """Test creating a variable entity."""
        entity = Entity.create_variable("x")
        assert entity.is_variable
        assert not entity.is_constant
        assert not entity.is_anonymous
        assert entity.name == "x"
        assert entity.variable_name == "x"
        assert entity.constant_name is None
        assert len(entity.properties) == 0
        assert entity.id is not None
    
    def test_entity_creation_constant(self):
        """Test creating a constant entity."""
        entity = Entity.create_constant("Socrates")
        assert not entity.is_variable
        assert entity.is_constant
        assert not entity.is_anonymous
        assert entity.name == "Socrates"
        assert entity.constant_name == "Socrates"
        assert entity.variable_name is None
        assert len(entity.properties) == 0
        assert entity.id is not None
    
    def test_entity_creation_anonymous(self):
        """Test creating an anonymous entity."""
        entity = Entity.create_anonymous()
        assert not entity.is_variable
        assert not entity.is_constant
        assert entity.is_anonymous
        assert entity.name.startswith("entity_")
        assert entity.variable_name is None
        assert entity.constant_name is None
        assert len(entity.properties) == 0
        assert entity.id is not None
    
    def test_entity_creation_with_properties(self):
        """Test creating an entity with properties."""
        properties = {'type': 'individual', 'domain': 'person'}
        entity = Entity.create_variable("x", properties=properties)
        assert entity.properties == pmap(properties)
    
    def test_entity_immutability(self):
        """Test that entities are immutable."""
        entity = Entity.create_variable("x")
        original_id = entity.id
        original_name = entity.name
        
        # Setting a property should return a new entity
        new_entity = entity.set_property('type', 'individual')
        assert entity.id == original_id  # Original unchanged
        assert entity.name == original_name  # Original unchanged
        assert 'type' not in entity.properties  # Original unchanged
        assert new_entity.id == original_id  # Same ID
        assert new_entity.name == original_name  # Same name
        assert new_entity.properties['type'] == 'individual'  # New entity has property
    
    def test_entity_set_property(self):
        """Test setting properties on an entity."""
        entity = Entity.create_variable("x")
        new_entity = entity.set_property('type', 'individual')
        
        assert new_entity.properties['type'] == 'individual'
        assert 'type' not in entity.properties  # Original unchanged
    
    def test_entity_remove_property(self):
        """Test removing properties from an entity."""
        entity = Entity.create_variable("x", properties={'type': 'individual', 'domain': 'person'})
        new_entity = entity.remove_property('type')
        
        assert 'type' not in new_entity.properties
        assert new_entity.properties['domain'] == 'person'
        assert entity.properties['type'] == 'individual'  # Original unchanged
    
    def test_entity_string_representation(self):
        """Test string representation of entities."""
        var_entity = Entity.create_variable("x")
        const_entity = Entity.create_constant("Socrates")
        anon_entity = Entity.create_anonymous()
        
        var_str = str(var_entity)
        const_str = str(const_entity)
        anon_str = str(anon_entity)
        
        assert 'Entity' in var_str and 'x' in var_str
        assert 'Entity' in const_str and 'Socrates' in const_str
        assert 'Entity' in anon_str


class TestPredicate:
    """Test the Predicate class (replaces Edge tests)."""
    
    def test_predicate_creation_with_defaults(self):
        """Test creating a predicate with default values."""
        predicate = Predicate.create("Person", [])
        assert predicate.name == "Person"
        assert predicate.arity == 0
        assert len(predicate.connected_entities) == 0
        assert len(predicate.properties) == 0
        assert predicate.id is not None
    
    def test_predicate_creation_with_entities(self):
        """Test creating a predicate with connected entities."""
        entity1_id = new_entity_id()
        entity2_id = new_entity_id()
        entities = [entity1_id, entity2_id]
        
        predicate = Predicate.create("Loves", entities)
        assert predicate.name == "Loves"
        assert predicate.arity == 2
        assert predicate.is_binary
        assert not predicate.is_unary
        assert entity1_id in predicate.connected_entities
        assert entity2_id in predicate.connected_entities
    
    def test_predicate_unary(self):
        """Test unary predicate properties."""
        entity_id = new_entity_id()
        predicate = Predicate.create("Person", [entity_id])
        
        assert predicate.arity == 1
        assert predicate.is_unary
        assert not predicate.is_binary
        assert entity_id in predicate.connected_entities
    
    def test_predicate_binary(self):
        """Test binary predicate properties."""
        entity1_id = new_entity_id()
        entity2_id = new_entity_id()
        predicate = Predicate.create("Loves", [entity1_id, entity2_id])
        
        assert predicate.arity == 2
        assert not predicate.is_unary
        assert predicate.is_binary
        assert entity1_id in predicate.connected_entities
        assert entity2_id in predicate.connected_entities
    
    def test_predicate_add_entity(self):
        """Test adding an entity to a predicate."""
        predicate = Predicate.create("Person", [])
        entity_id = new_entity_id()
        
        new_predicate = predicate.add_entity(entity_id)
        assert entity_id in new_predicate.connected_entities
        assert new_predicate.arity == 1
        assert predicate.arity == 0  # Original unchanged
    
    def test_predicate_remove_entity(self):
        """Test removing an entity from a predicate."""
        entity1_id = new_entity_id()
        entity2_id = new_entity_id()
        predicate = Predicate.create("Loves", [entity1_id, entity2_id])
        
        new_predicate = predicate.remove_entity(entity1_id)
        assert entity1_id not in new_predicate.connected_entities
        assert entity2_id in new_predicate.connected_entities
        assert new_predicate.arity == 1
        assert predicate.arity == 2  # Original unchanged
    
    def test_predicate_remove_nonexistent_entity(self):
        """Test removing a non-existent entity from a predicate."""
        entity1_id = new_entity_id()
        entity2_id = new_entity_id()
        predicate = Predicate.create("Person", [entity1_id])
        
        # Should return the same predicate if entity doesn't exist
        new_predicate = predicate.remove_entity(entity2_id)
        assert new_predicate == predicate
    
    def test_predicate_with_properties(self):
        """Test creating a predicate with properties."""
        properties = {'arity_type': 'binary', 'domain': 'social'}
        predicate = Predicate.create("Loves", [], properties=properties)
        assert predicate.properties == pmap(properties)
    
    def test_predicate_string_representation(self):
        """Test string representation of predicates."""
        entity1_id = new_entity_id()
        entity2_id = new_entity_id()
        predicate = Predicate.create("Loves", [entity1_id, entity2_id])
        str_repr = str(predicate)
        assert 'Loves' in str_repr
        assert '/2' in str_repr  # Arity notation


class TestContext:
    """Test the updated Context class."""
    
    def test_context_creation_with_defaults(self):
        """Test creating a context with default values."""
        context = Context.create("sheet")
        assert context.context_type == "sheet"
        assert context.parent_context is None
        assert context.depth == 0
        assert len(context.contained_entities) == 0
        assert len(context.contained_predicates) == 0
        assert len(context.properties) == 0
        assert context.id is not None
    
    def test_context_add_entity(self):
        """Test adding an entity to a context."""
        context = Context.create("sheet")
        entity_id = new_entity_id()
        
        new_context = context.add_entity(entity_id)
        assert entity_id in new_context.contained_entities
        assert len(new_context.contained_entities) == 1
        assert len(context.contained_entities) == 0  # Original unchanged
    
    def test_context_add_predicate(self):
        """Test adding a predicate to a context."""
        context = Context.create("sheet")
        predicate_id = new_predicate_id()
        
        new_context = context.add_predicate(predicate_id)
        assert predicate_id in new_context.contained_predicates
        assert len(new_context.contained_predicates) == 1
        assert len(context.contained_predicates) == 0  # Original unchanged
    
    def test_context_remove_entity(self):
        """Test removing an entity from a context."""
        entity1_id = new_entity_id()
        entity2_id = new_entity_id()
        context = Context.create("sheet", contained_entities={entity1_id, entity2_id})
        
        new_context = context.remove_entity(entity1_id)
        assert entity1_id not in new_context.contained_entities
        assert entity2_id in new_context.contained_entities
        assert len(new_context.contained_entities) == 1
        assert len(context.contained_entities) == 2  # Original unchanged
    
    def test_context_remove_predicate(self):
        """Test removing a predicate from a context."""
        pred1_id = new_predicate_id()
        pred2_id = new_predicate_id()
        context = Context.create("sheet", contained_predicates={pred1_id, pred2_id})
        
        new_context = context.remove_predicate(pred1_id)
        assert pred1_id not in new_context.contained_predicates
        assert pred2_id in new_context.contained_predicates
        assert len(new_context.contained_predicates) == 1
        assert len(context.contained_predicates) == 2  # Original unchanged
    
    def test_context_polarity(self):
        """Test context polarity based on depth."""
        positive = Context.create("sheet", depth=0)
        negative = Context.create("cut", depth=1)
        double_negative = Context.create("cut", depth=2)
        
        assert positive.is_positive
        assert not positive.is_negative
        assert negative.is_negative
        assert not negative.is_positive
        assert double_negative.is_positive  # Double negative
        assert not double_negative.is_negative
    
    def test_context_with_parent(self):
        """Test creating a context with a parent."""
        parent_id = new_context_id()
        context = Context.create("cut", parent_context=parent_id, depth=1)
        
        assert context.parent_context == parent_id
        assert context.depth == 1
        assert not context.is_root
    
    def test_context_string_representation(self):
        """Test string representation of contexts."""
        entity_id = new_entity_id()
        predicate_id = new_predicate_id()
        context = Context.create("cut", depth=1, 
                                contained_entities={entity_id},
                                contained_predicates={predicate_id})
        str_repr = str(context)
        assert 'cut' in str_repr
        assert 'depth=1' in str_repr
        assert 'entities=1' in str_repr
        assert 'predicates=1' in str_repr


class TestUtilityFunctions:
    """Test utility functions for the new architecture."""
    
    def test_create_simple_assertion_unary(self):
        """Test creating a simple unary assertion."""
        entities, predicate = create_simple_assertion("Person", ["Socrates"])
        
        assert len(entities) == 1
        assert entities[0].name == "Socrates"
        assert entities[0].is_constant
        assert predicate.name == "Person"
        assert predicate.arity == 1
        assert entities[0].id in predicate.connected_entities
    
    def test_create_simple_assertion_binary(self):
        """Test creating a simple binary assertion."""
        entities, predicate = create_simple_assertion("Loves", ["Mary", "John"])
        
        assert len(entities) == 2
        assert entities[0].name == "Mary"
        assert entities[1].name == "John"
        assert all(e.is_constant for e in entities)
        assert predicate.name == "Loves"
        assert predicate.arity == 2
        assert all(e.id in predicate.connected_entities for e in entities)
    
    def test_create_simple_assertion_with_variables(self):
        """Test creating an assertion with variables."""
        entities, predicate = create_simple_assertion("Person", ["x"])
        
        assert len(entities) == 1
        assert entities[0].name == "x"
        assert entities[0].is_variable
        assert predicate.name == "Person"
        assert predicate.arity == 1
    
    def test_validate_predicate_entity_connection(self):
        """Test validation of predicate-entity connections."""
        entity = Entity.create_constant("Socrates")
        predicate = Predicate.create("Person", [entity.id])
        entities_dict = {entity.id: entity}
        
        # Valid connection
        errors = validate_predicate_entity_connection(predicate, entities_dict)
        assert len(errors) == 0
        
        # Invalid connection - predicate references non-existent entity
        other_entity_id = new_entity_id()
        bad_predicate = Predicate.create("Person", [other_entity_id])
        errors = validate_predicate_entity_connection(bad_predicate, entities_dict)
        assert len(errors) > 0


class TestExceptions:
    """Test the exception hierarchy."""
    
    def test_exception_hierarchy(self):
        """Test that all exceptions inherit from base error."""
        # Note: Assuming EGError is renamed to a base error in the new architecture
        assert issubclass(EntityError, Exception)
        assert issubclass(PredicateError, Exception)
        assert issubclass(ContextError, Exception)
        assert issubclass(ValidationError, Exception)
    
    def test_exception_creation(self):
        """Test creating exceptions."""
        entity_error = EntityError("Entity error message")
        predicate_error = PredicateError("Predicate error message")
        context_error = ContextError("Context error message")
        validation_error = ValidationError("Validation error message")
        
        assert str(entity_error) == "Entity error message"
        assert str(predicate_error) == "Predicate error message"
        assert str(context_error) == "Context error message"
        assert str(validation_error) == "Validation error message"


class TestPropertyBasedTypes:
    """Property-based tests for the redesigned types."""
    
    @given(st.text(min_size=1, max_size=50))
    def test_entity_property_roundtrip(self, property_value):
        """Test that entity properties can be set and retrieved."""
        entity = Entity.create_variable("x")
        new_entity = entity.set_property('test_prop', property_value)
        assert new_entity.properties['test_prop'] == property_value
    
    @given(st.text(min_size=1, max_size=20))
    def test_variable_entity_names(self, var_name):
        """Test that variable entities can have various names."""
        # Filter out names that would be treated as constants
        if var_name.islower() and var_name.isalpha():
            entity = Entity.create_variable(var_name)
            assert entity.is_variable
            assert entity.name == var_name
            assert entity.variable_name == var_name
    
    @given(st.text(min_size=1, max_size=20))
    def test_constant_entity_names(self, const_name):
        """Test that constant entities can have various names."""
        # Filter out problematic names
        if const_name and not const_name.isspace():
            entity = Entity.create_constant(const_name)
            assert entity.is_constant
            assert entity.name == const_name
            assert entity.constant_name == const_name
    
    @given(st.sets(st.integers(), min_size=0, max_size=10))
    def test_predicate_entities_roundtrip(self, entity_indices):
        """Test that predicate entities can be set and retrieved."""
        # Convert integers to actual entity IDs
        entity_ids = [new_entity_id() for _ in entity_indices]
        predicate = Predicate.create("TestPredicate", entity_ids)
        
        assert predicate.arity == len(entity_ids)
        for entity_id in entity_ids:
            assert entity_id in predicate.connected_entities
    
    @given(st.integers(min_value=0, max_value=100))
    def test_context_size_consistency(self, num_entities):
        """Test that context size is consistent with added entities."""
        context = Context.create("sheet")
        entity_ids = [new_entity_id() for _ in range(num_entities)]
        
        for entity_id in entity_ids:
            context = context.add_entity(entity_id)
        
        assert len(context.contained_entities) == num_entities
        for entity_id in entity_ids:
            assert entity_id in context.contained_entities


class TestArchitecturalCorrectness:
    """Test that the new architecture correctly represents EG concepts."""
    
    def test_entity_represents_line_of_identity(self):
        """Test that entities properly represent Lines of Identity."""
        # Same entity can be connected to multiple predicates (shared identity)
        socrates = Entity.create_constant("Socrates")
        person_pred = Predicate.create("Person", [socrates.id])
        mortal_pred = Predicate.create("Mortal", [socrates.id])
        
        # Both predicates connect to the same entity (Line of Identity)
        assert socrates.id in person_pred.connected_entities
        assert socrates.id in mortal_pred.connected_entities
        
        # This represents: Socrates is both a Person and Mortal
        # Connected by the same Line of Identity
    
    def test_predicate_represents_hyperedge(self):
        """Test that predicates properly represent hyperedges."""
        # A predicate can connect multiple entities
        mary = Entity.create_constant("Mary")
        john = Entity.create_constant("John")
        loves_pred = Predicate.create("Loves", [mary.id, john.id])
        
        # The predicate is a hyperedge connecting both entities
        assert loves_pred.arity == 2
        assert mary.id in loves_pred.connected_entities
        assert john.id in loves_pred.connected_entities
        
        # This represents: Mary loves John
        # The "Loves" relation connects the two entities
    
    def test_context_represents_logical_scope(self):
        """Test that contexts properly represent logical scopes."""
        # Entities and predicates exist within logical scopes
        root_context = Context.create("sheet")
        existential_context = Context.create("cut", parent_context=root_context.id, depth=1)
        
        # Variable entity exists within existential scope
        x = Entity.create_variable("x")
        person_pred = Predicate.create("Person", [x.id])
        
        scoped_context = existential_context.add_entity(x.id)
        scoped_context = scoped_context.add_predicate(person_pred.id)
        
        assert x.id in scoped_context.contained_entities
        assert person_pred.id in scoped_context.contained_predicates
        assert scoped_context.is_negative  # Existential quantification
        
        # This represents: (exists x) (Person x)
        # The variable x and predicate Person(x) are in the same scope

