"""
Test suite for transformation rules with Entity-Predicate architecture.

This test suite validates that the transformation rules work correctly
with the new Entity-Predicate hypergraph model.
"""

import pytest
from typing import Set

from src.eg_types import Entity, Predicate, Context, EntityId, PredicateId, ContextId
from src.graph import EGGraph
from src.transformations import (
    TransformationEngine, TransformationType, TransformationResult
)


class TestTransformationEngineEntityPredicate:
    """Test the transformation engine with Entity-Predicate architecture."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = TransformationEngine()
        
        # Create a simple test graph with entities and predicates
        self.graph = EGGraph.create_empty()
        
        # Add some entities
        self.socrates = Entity.create(name="Socrates", entity_type="constant")
        self.x = Entity.create(name="x", entity_type="variable")
        self.y = Entity.create(name="y", entity_type="variable")
        
        self.graph = self.graph.add_entity(self.socrates, self.graph.root_context_id)
        self.graph = self.graph.add_entity(self.x, self.graph.root_context_id)
        self.graph = self.graph.add_entity(self.y, self.graph.root_context_id)
        
        # Add some predicates
        self.person_socrates = Predicate.create(
            name="Person", 
            entities=[self.socrates.id], 
            arity=1
        )
        self.mortal_x = Predicate.create(
            name="Mortal", 
            entities=[self.x.id], 
            arity=1
        )
        self.loves_xy = Predicate.create(
            name="Loves", 
            entities=[self.x.id, self.y.id], 
            arity=2
        )
        
        self.graph = self.graph.add_predicate(self.person_socrates, self.graph.root_context_id)
        self.graph = self.graph.add_predicate(self.mortal_x, self.graph.root_context_id)
        self.graph = self.graph.add_predicate(self.loves_xy, self.graph.root_context_id)
    
    def test_double_cut_insertion(self):
        """Test double cut insertion transformation."""
        # Apply double cut insertion around the Person(Socrates) predicate
        target_items = {self.person_socrates.id}
        
        attempt = self.engine.apply_transformation(
            self.graph,
            TransformationType.DOUBLE_CUT_INSERTION,
            target_items=target_items,
            target_context=self.graph.root_context_id,
            subgraph_items=target_items
        )
        
        assert attempt.result == TransformationResult.SUCCESS
        assert attempt.result_graph is not None
        
        # Check that two new contexts were created
        original_context_count = len(self.graph.context_manager.contexts)
        new_context_count = len(attempt.result_graph.context_manager.contexts)
        assert new_context_count == original_context_count + 2
        
        # Check that the predicate was moved to the inner context
        assert self.person_socrates.id not in attempt.result_graph.context_manager.get_items_in_context(self.graph.root_context_id)
    
    def test_erasure_from_negative_context(self):
        """Test erasure transformation from a negative context."""
        # First create a negative context (cut)
        graph, cut_context = self.graph.create_context('cut', self.graph.root_context_id, 'Test Cut')
        
        # Add a predicate to the negative context
        test_predicate = Predicate.create(name="Test", entities=[self.x.id], arity=1)
        graph = graph.add_predicate(test_predicate, cut_context.id)
        
        # Apply erasure to remove the predicate from the negative context
        attempt = self.engine.apply_transformation(
            graph,
            TransformationType.ERASURE,
            target_items={test_predicate.id}
        )
        
        assert attempt.result == TransformationResult.SUCCESS
        assert attempt.result_graph is not None
        
        # Check that the predicate was removed
        assert test_predicate.id not in attempt.result_graph.predicates
    
    def test_insertion_into_positive_context(self):
        """Test insertion transformation into a positive context."""
        # Define a subgraph to insert
        subgraph = {
            'entities': [
                {'name': 'NewEntity', 'entity_type': 'variable'}
            ],
            'predicates': [
                {'name': 'NewPredicate', 'entities': [], 'arity': 0}
            ]
        }
        
        attempt = self.engine.apply_transformation(
            self.graph,
            TransformationType.INSERTION,
            target_context=self.graph.root_context_id,
            subgraph=subgraph
        )
        
        assert attempt.result == TransformationResult.SUCCESS
        assert attempt.result_graph is not None
        
        # Check that new items were added
        original_entity_count = len(self.graph.entities)
        original_predicate_count = len(self.graph.predicates)
        new_entity_count = len(attempt.result_graph.entities)
        new_predicate_count = len(attempt.result_graph.predicates)
        
        assert new_entity_count == original_entity_count + 1
        assert new_predicate_count == original_predicate_count + 1
    
    def test_iteration_to_same_level(self):
        """Test iteration transformation to the same context level."""
        # Create another positive context at the same level
        graph, sibling_context = self.graph.create_context('assertion', self.graph.root_context_id, 'Sibling')
        
        # Apply iteration to copy a predicate to the sibling context
        target_items = {self.person_socrates.id, self.socrates.id}
        
        attempt = self.engine.apply_transformation(
            graph,
            TransformationType.ITERATION,
            target_items=target_items,
            target_context=sibling_context.id
        )
        
        assert attempt.result == TransformationResult.SUCCESS
        assert attempt.result_graph is not None
        
        # Check that items were copied (not moved)
        assert self.person_socrates.id in attempt.result_graph.predicates  # Original still exists
        
        # Check that new items were created in the target context
        sibling_items = attempt.result_graph.context_manager.get_items_in_context(sibling_context.id)
        assert len(sibling_items) > 0
    
    def test_entity_join(self):
        """Test entity join transformation."""
        # Create two entities that should be joined
        entity1 = Entity.create(name="a", entity_type="variable")
        entity2 = Entity.create(name="b", entity_type="variable")
        
        graph = self.graph.add_entity(entity1, self.graph.root_context_id)
        graph = graph.add_entity(entity2, self.graph.root_context_id)
        
        # Create predicates using these entities
        pred1 = Predicate.create(name="P", entities=[entity1.id], arity=1)
        pred2 = Predicate.create(name="Q", entities=[entity2.id], arity=1)
        
        graph = graph.add_predicate(pred1, self.graph.root_context_id)
        graph = graph.add_predicate(pred2, self.graph.root_context_id)
        
        # Apply entity join
        attempt = self.engine.apply_transformation(
            graph,
            TransformationType.ENTITY_JOIN,
            target_items={entity1.id, entity2.id}
        )
        
        assert attempt.result == TransformationResult.SUCCESS
        assert attempt.result_graph is not None
        
        # Check that entities were merged
        original_entity_count = len(graph.entities)
        new_entity_count = len(attempt.result_graph.entities)
        assert new_entity_count == original_entity_count - 1  # Two entities merged into one
    
    def test_entity_sever(self):
        """Test entity sever transformation."""
        # Create an entity used by multiple predicates
        shared_entity = Entity.create(name="shared", entity_type="variable")
        graph = self.graph.add_entity(shared_entity, self.graph.root_context_id)
        
        # Create multiple predicates using the shared entity
        pred1 = Predicate.create(name="P", entities=[shared_entity.id], arity=1)
        pred2 = Predicate.create(name="Q", entities=[shared_entity.id], arity=1)
        
        graph = graph.add_predicate(pred1, self.graph.root_context_id)
        graph = graph.add_predicate(pred2, self.graph.root_context_id)
        
        # Apply entity sever
        attempt = self.engine.apply_transformation(
            graph,
            TransformationType.ENTITY_SEVER,
            target_items={shared_entity.id}
        )
        
        assert attempt.result == TransformationResult.SUCCESS
        assert attempt.result_graph is not None
        
        # Check that the shared entity was split
        original_entity_count = len(graph.entities)
        new_entity_count = len(attempt.result_graph.entities)
        assert new_entity_count > original_entity_count  # Entity was split
    
    def test_invalid_erasure_from_positive_context(self):
        """Test that erasure fails when attempted on positive context."""
        # Try to erase from the root context (positive)
        attempt = self.engine.apply_transformation(
            self.graph,
            TransformationType.ERASURE,
            target_items={self.person_socrates.id}
        )
        
        assert attempt.result == TransformationResult.PRECONDITION_FAILED
        assert "positive context" in attempt.error_message.lower()
    
    def test_invalid_insertion_into_negative_context(self):
        """Test that insertion fails when attempted on negative context."""
        # Create a negative context (cut)
        graph, cut_context = self.graph.create_context('cut', self.graph.root_context_id, 'Test Cut')
        
        # Try to insert into the negative context
        subgraph = {
            'entities': [{'name': 'Test', 'entity_type': 'variable'}],
            'predicates': []
        }
        
        attempt = self.engine.apply_transformation(
            graph,
            TransformationType.INSERTION,
            target_context=cut_context.id,
            subgraph=subgraph
        )
        
        assert attempt.result == TransformationResult.PRECONDITION_FAILED
        assert "negative context" in attempt.error_message.lower()
    
    def test_get_legal_transformations(self):
        """Test getting legal transformations for a graph state."""
        legal_transformations = self.engine.get_legal_transformations(self.graph)
        
        # Should include basic transformations
        assert TransformationType.DOUBLE_CUT_INSERTION in legal_transformations
        assert TransformationType.INSERTION in legal_transformations
        
        # Should not include erasure for positive context items
        if TransformationType.ERASURE in legal_transformations:
            # If erasure is listed, it should have empty target sets for positive context
            erasure_targets = legal_transformations[TransformationType.ERASURE]
            assert len(erasure_targets) == 0
    
    def test_transformation_history(self):
        """Test that transformation history is properly recorded."""
        initial_history_length = len(self.engine.transformation_history)
        
        # Apply a transformation
        self.engine.apply_transformation(
            self.graph,
            TransformationType.DOUBLE_CUT_INSERTION,
            target_context=self.graph.root_context_id,
            subgraph_items=set()
        )
        
        # Check that history was updated
        assert len(self.engine.transformation_history) == initial_history_length + 1
        
        # Check that the history entry contains expected information
        last_attempt = self.engine.transformation_history[-1]
        assert last_attempt.transformation_type == TransformationType.DOUBLE_CUT_INSERTION
        assert last_attempt.source_graph == self.graph
    
    def test_entity_consistency_validation(self):
        """Test that entity consistency is validated after transformations."""
        # Create a graph with inconsistent entity references (for testing)
        # This would normally be caught by the validation
        
        # Apply a valid transformation first
        attempt = self.engine.apply_transformation(
            self.graph,
            TransformationType.DOUBLE_CUT_INSERTION,
            target_context=self.graph.root_context_id,
            subgraph_items=set()
        )
        
        assert attempt.result == TransformationResult.SUCCESS
        
        # The validation should pass for a properly constructed transformation
        validation_result = self.engine._validate_entity_consistency(attempt.result_graph)
        assert validation_result.is_valid


class TestTransformationValidation:
    """Test transformation validation logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = TransformationEngine()
        self.graph = EGGraph.create_empty()
        
        # Add basic entities and predicates
        self.entity = Entity.create(name="test", entity_type="variable")
        self.graph = self.graph.add_entity(self.entity, self.graph.root_context_id)
        
        self.predicate = Predicate.create(name="Test", entities=[self.entity.id], arity=1)
        self.graph = self.graph.add_predicate(self.predicate, self.graph.root_context_id)
    
    def test_validate_entity_join_preconditions(self):
        """Test validation of entity join preconditions."""
        # Valid case: multiple entities
        entity2 = Entity.create(name="test2", entity_type="variable")
        graph = self.graph.add_entity(entity2, self.graph.root_context_id)
        
        result = self.engine._validate_entity_join_preconditions(
            graph, {self.entity.id, entity2.id}
        )
        assert result.is_valid
        
        # Invalid case: single entity
        result = self.engine._validate_entity_join_preconditions(
            self.graph, {self.entity.id}
        )
        assert not result.is_valid
        assert "at least 2" in result.error_message
        
        # Invalid case: non-entity item
        result = self.engine._validate_entity_join_preconditions(
            self.graph, {self.predicate.id}
        )
        assert not result.is_valid
        assert "not an entity" in result.error_message
    
    def test_validate_entity_sever_preconditions(self):
        """Test validation of entity sever preconditions."""
        # Create entity used by multiple predicates
        pred2 = Predicate.create(name="Test2", entities=[self.entity.id], arity=1)
        graph = self.graph.add_predicate(pred2, self.graph.root_context_id)
        
        # Valid case: entity used by multiple predicates
        result = self.engine._validate_entity_sever_preconditions(
            graph, {self.entity.id}
        )
        assert result.is_valid
        
        # Invalid case: entity used by only one predicate
        result = self.engine._validate_entity_sever_preconditions(
            self.graph, {self.entity.id}
        )
        assert not result.is_valid
        assert "multiple predicates" in result.error_message


if __name__ == "__main__":
    pytest.main([__file__])

