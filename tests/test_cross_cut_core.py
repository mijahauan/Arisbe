"""
Core tests for cross-cut ligature validation system.

This simplified test suite focuses on the core functionality of the cross-cut
validation system without complex graph construction.
"""

import sys

import unittest
from typing import Set, Dict, List

from eg_types import Entity, Predicate, Context, EntityId, PredicateId, ContextId
from graph import EGGraph
from cross_cut_validator import CrossCutValidator, CrossCutType, CrossCutInfo


class TestCrossCutCore(unittest.TestCase):
    """Test core cross-cut validation functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = CrossCutValidator()
    
    def test_validator_initialization(self):
        """Test that the cross-cut validator initializes correctly."""
        validator = CrossCutValidator()
        self.assertIsNotNone(validator)
    
    def test_empty_graph_analysis(self):
        """Test cross-cut analysis on an empty graph."""
        graph = EGGraph.create_empty()
        
        # Analyze cross-cuts
        cross_cuts = self.validator.analyze_cross_cuts(graph)
        
        # Should be empty
        self.assertEqual(len(cross_cuts), 0)
    
    def test_identity_preservation_empty_graph(self):
        """Test identity preservation validation on empty graph."""
        graph = EGGraph.create_empty()
        
        # Validate identity preservation
        result = self.validator.validate_identity_preservation(graph)
        
        # Should be preserved (vacuously true)
        self.assertTrue(result.is_preserved)
        self.assertEqual(len(result.violations), 0)
    
    def test_transformation_constraints_empty_graph(self):
        """Test transformation constraint validation on empty graph."""
        graph = EGGraph.create_empty()
        
        # Test various transformation constraints
        violations = self.validator.validate_transformation_constraints(
            graph, "insertion", set(), graph.context_manager.root_context.id
        )
        
        # Should not have violations for insertion into empty graph
        self.assertEqual(len(violations), 0)
    
    def test_cross_cut_info_creation(self):
        """Test creation of CrossCutInfo objects."""
        cross_cut = CrossCutInfo(
            entity_id="test_entity",
            cross_cut_type=CrossCutType.SIMPLE_CROSS,
            contexts={"context1", "context2"},
            depth_span=2,
            predicates_involved={"pred1", "pred2"}
        )
        
        self.assertEqual(cross_cut.entity_id, "test_entity")
        self.assertEqual(cross_cut.cross_cut_type, CrossCutType.SIMPLE_CROSS)
        self.assertEqual(len(cross_cut.contexts), 2)
        self.assertEqual(cross_cut.depth_span, 2)
    
    def test_cross_cut_type_enum(self):
        """Test CrossCutType enum values."""
        self.assertEqual(CrossCutType.SIMPLE_CROSS.value, "simple_cross")
        self.assertEqual(CrossCutType.MULTI_CROSS.value, "multi_cross")
        self.assertEqual(CrossCutType.NESTED_CROSS.value, "nested_cross")
        self.assertEqual(CrossCutType.LIGATURE_CROSS.value, "ligature_cross")
    
    def test_entity_context_mapping_empty(self):
        """Test entity-context mapping on empty graph."""
        graph = EGGraph.create_empty()
        
        # Build entity-context mapping
        mapping = self.validator._build_entity_context_mapping(graph)
        
        # Should be empty
        self.assertEqual(len(mapping), 0)
    
    def test_basic_graph_with_entity(self):
        """Test basic graph operations with a single entity."""
        graph = EGGraph.create_empty()
        
        # Create and add entity
        entity = Entity.create(entity_type="constant", name="Socrates", id="socrates")
        graph = graph.add_entity(entity)
        
        # Verify entity was added
        self.assertIn("socrates", graph.entities)
        self.assertEqual(graph.entities["socrates"].name, "Socrates")
        
        # Analyze cross-cuts (should be none with single entity)
        cross_cuts = self.validator.analyze_cross_cuts(graph)
        self.assertEqual(len(cross_cuts), 0)
    
    def test_basic_graph_with_predicate(self):
        """Test basic graph operations with a single predicate."""
        graph = EGGraph.create_empty()
        
        # Create and add entity
        entity = Entity.create(entity_type="constant", name="Socrates", id="socrates")
        graph = graph.add_entity(entity)
        
        # Create and add predicate
        predicate = Predicate.create(name="Person", entities=["socrates"], id="pred1")
        graph = graph.add_predicate(predicate)
        
        # Verify predicate was added
        self.assertIn("pred1", graph.predicates)
        self.assertEqual(graph.predicates["pred1"].name, "Person")
        
        # Analyze cross-cuts (should be none with single context)
        cross_cuts = self.validator.analyze_cross_cuts(graph)
        self.assertEqual(len(cross_cuts), 0)
    
    def test_validator_helper_methods(self):
        """Test validator helper methods."""
        graph = EGGraph.create_empty()
        
        # Test entity contexts method
        entity_contexts = self.validator._get_entity_contexts("nonexistent", graph)
        self.assertEqual(len(entity_contexts), 0)
        
        # Test build entity context mapping
        mapping = self.validator._build_entity_context_mapping(graph)
        self.assertIsInstance(mapping, dict)
    
    def test_transformation_constraint_types(self):
        """Test different transformation constraint types."""
        graph = EGGraph.create_empty()
        root_context = graph.context_manager.root_context.id
        
        # Test different transformation types
        transformation_types = ["insertion", "erasure", "iteration", "deiteration"]
        
        for trans_type in transformation_types:
            violations = self.validator.validate_transformation_constraints(
                graph, trans_type, set(), root_context
            )
            # Should not fail on empty graph
            self.assertIsInstance(violations, list)


class TestCrossCutValidatorMethods(unittest.TestCase):
    """Test specific methods of the CrossCutValidator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = CrossCutValidator()
        self.graph = EGGraph.create_empty()
    
    def test_analyze_cross_cuts_method(self):
        """Test the analyze_cross_cuts method."""
        result = self.validator.analyze_cross_cuts(self.graph)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)  # Empty graph
    
    def test_validate_identity_preservation_method(self):
        """Test the validate_identity_preservation method."""
        result = self.validator.validate_identity_preservation(self.graph)
        self.assertTrue(hasattr(result, 'is_preserved'))
        self.assertTrue(hasattr(result, 'violations'))
        self.assertTrue(hasattr(result, 'warnings'))
        self.assertTrue(hasattr(result, 'cross_cuts'))
    
    def test_validate_transformation_constraints_method(self):
        """Test the validate_transformation_constraints method."""
        root_context = self.graph.context_manager.root_context.id
        result = self.validator.validate_transformation_constraints(
            self.graph, "insertion", set(), root_context
        )
        self.assertIsInstance(result, list)
    
    def test_build_entity_context_mapping_method(self):
        """Test the _build_entity_context_mapping method."""
        result = self.validator._build_entity_context_mapping(self.graph)
        self.assertIsInstance(result, dict)
    
    def test_get_entity_contexts_method(self):
        """Test the _get_entity_contexts method."""
        result = self.validator._get_entity_contexts("test_entity", self.graph)
        self.assertIsInstance(result, set)


class TestCrossCutIntegration(unittest.TestCase):
    """Test integration aspects of cross-cut validation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = CrossCutValidator()
    
    def test_validator_with_real_graph(self):
        """Test validator with a graph containing actual entities and predicates."""
        graph = EGGraph.create_empty()
        
        # Add entity
        entity = Entity.create(entity_type="constant", name="Socrates", id="socrates")
        graph = graph.add_entity(entity)
        
        # Add predicate
        predicate = Predicate.create(name="Person", entities=["socrates"], id="pred1")
        graph = graph.add_predicate(predicate)
        
        # Test all validator methods
        cross_cuts = self.validator.analyze_cross_cuts(graph)
        self.assertIsInstance(cross_cuts, list)
        
        identity_result = self.validator.validate_identity_preservation(graph)
        self.assertTrue(identity_result.is_preserved)
        
        constraint_violations = self.validator.validate_transformation_constraints(
            graph, "insertion", set(), graph.context_manager.root_context.id
        )
        self.assertIsInstance(constraint_violations, list)
    
    def test_cross_cut_detection_logic(self):
        """Test the core logic of cross-cut detection."""
        # This test validates that the cross-cut detection logic works
        # even if we can't easily construct complex cross-cut scenarios
        
        graph = EGGraph.create_empty()
        
        # The validator should handle any graph gracefully
        try:
            cross_cuts = self.validator.analyze_cross_cuts(graph)
            identity_result = self.validator.validate_identity_preservation(graph)
            
            # All should complete without errors
            self.assertTrue(True)  # If we get here, the methods work
            
        except Exception as e:
            self.fail(f"Cross-cut validation failed with error: {e}")
    
    def test_validator_error_handling(self):
        """Test that validator handles edge cases gracefully."""
        graph = EGGraph.create_empty()
        
        # Test with invalid transformation type
        violations = self.validator.validate_transformation_constraints(
            graph, "invalid_transformation", set(), graph.context_manager.root_context.id
        )
        
        # Should return empty list or handle gracefully
        self.assertIsInstance(violations, list)
        
        # Test with invalid entity ID
        entity_contexts = self.validator._get_entity_contexts("nonexistent_entity", graph)
        self.assertIsInstance(entity_contexts, set)
        self.assertEqual(len(entity_contexts), 0)


if __name__ == '__main__':
    unittest.main()

