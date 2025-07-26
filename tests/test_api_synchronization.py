"""
API Synchronization Verification Tests (Fixed for pytest.ini)

This test suite verifies that all API standardization changes have been
properly applied and are working correctly.
"""

import pytest

# Import using the module structure that works with pytest.ini
from graph import EGGraph
from game_engine import EGGameEngine, EndoporeuticGameEngine
from cross_cut_validator import CrossCutValidator
from transformations import TransformationEngine
from eg_types import Entity, Predicate


class TestAPIStandardization:
    """Test suite for API standardization verification."""
    
    def test_imports_successful(self):
        """Test that all required modules can be imported."""
        # This test passes if we get here without import errors
        assert True, "All imports successful"
    
    def test_egraph_validate_method(self):
        """Test the new EGGraph.validate() method."""
        graph = EGGraph.create_empty()
        
        # Test new validate() method exists
        assert hasattr(graph, 'validate'), "EGGraph should have validate() method"
        
        # Test it returns structured result
        result = graph.validate()
        assert hasattr(result, 'is_valid'), "Result should have is_valid attribute"
        assert hasattr(result, 'errors'), "Result should have errors attribute"
        assert hasattr(result, 'warnings'), "Result should have warnings attribute"
        
        # Test result values for empty graph
        assert result.is_valid == True, "Empty graph should be valid"
        assert result.errors == [], "Empty graph should have no errors"
        assert isinstance(result.warnings, list), "Warnings should be a list"
    
    def test_egraph_backward_compatibility(self):
        """Test that original validation method still works."""
        graph = EGGraph.create_empty()
        
        # Test original method still exists
        assert hasattr(graph, 'validate_graph_integrity'), "Original method should still exist"
        
        # Test it returns list of errors
        errors = graph.validate_graph_integrity()
        assert isinstance(errors, list), "Should return list of errors"
        assert errors == [], "Empty graph should have no errors"
    
    def test_game_engine_class_alias(self):
        """Test that EGGameEngine is an alias for EndoporeuticGameEngine."""
        # Test that both classes exist
        assert EGGameEngine is not None, "EGGameEngine should exist"
        assert EndoporeuticGameEngine is not None, "EndoporeuticGameEngine should exist"
        
        # Test that they are the same class
        assert EGGameEngine == EndoporeuticGameEngine, "EGGameEngine should be alias for EndoporeuticGameEngine"
        
        # Test instantiation works for both
        engine1 = EGGameEngine()
        engine2 = EndoporeuticGameEngine()
        
        assert type(engine1) == type(engine2), "Both should create same type"
    
    def test_game_engine_method_aliases(self):
        """Test game engine method aliases."""
        engine = EGGameEngine()
        graph = EGGraph.create_empty()
        
        # Add some content to make a valid game graph
        entity = Entity.create('Test', 'constant')
        graph = graph.add_entity(entity, graph.root_context_id)
        
        # Test original method exists
        assert hasattr(engine, 'create_game_state'), "Original create_game_state should exist"
        
        # Test new alias methods exist
        assert hasattr(engine, 'start_new_game'), "start_new_game alias should exist"
        assert hasattr(engine, 'start_game'), "start_game alias should exist"
        assert hasattr(engine, 'get_available_moves'), "get_available_moves alias should exist"
        
        # Test that methods work
        state1 = engine.create_game_state(graph)
        state2 = engine.start_new_game(graph)
        state3 = engine.start_game(graph)
        
        assert state1 is not None, "create_game_state should return valid state"
        assert state2 is not None, "start_new_game should return valid state"
        assert state3 is not None, "start_game should return valid state"
        
        # Test move methods
        moves1 = engine.get_legal_moves(state1)
        moves2 = engine.get_available_moves(state1)
        
        assert isinstance(moves1, list), "get_legal_moves should return list"
        assert isinstance(moves2, list), "get_available_moves should return list"
    
    def test_cross_cut_validator_enhancements(self):
        """Test cross-cut validator enhancements."""
        validator = CrossCutValidator()
        graph = EGGraph.create_empty()
        
        # Test original method exists
        assert hasattr(validator, 'validate_identity_preservation'), "Original method should exist"
        
        # Test new alias method exists
        assert hasattr(validator, 'validate_graph'), "validate_graph alias should exist"
        
        # Test both methods work
        result1 = validator.validate_identity_preservation(graph)
        result2 = validator.validate_graph(graph)
        
        assert result1 is not None, "validate_identity_preservation should return result"
        assert result2 is not None, "validate_graph should return result"
        
        # Test new has_violations property
        assert hasattr(result1, 'has_violations'), "Result should have has_violations property"
        assert hasattr(result2, 'has_violations'), "Result should have has_violations property"
        
        # Test property works
        assert isinstance(result1.has_violations, bool), "has_violations should be boolean"
        assert result1.has_violations == False, "Empty graph should have no violations"
    
    def test_transformation_engine_alias(self):
        """Test transformation engine method alias."""
        engine = TransformationEngine()
        graph = EGGraph.create_empty()
        
        # Test original method exists
        assert hasattr(engine, 'get_legal_transformations'), "Original method should exist"
        
        # Test new alias method exists
        assert hasattr(engine, 'get_available_transformations'), "Alias method should exist"
        
        # Test both methods work and return same result
        trans1 = engine.get_legal_transformations(graph)
        trans2 = engine.get_available_transformations(graph)
        
        assert trans1 == trans2, "Both methods should return identical results"
        assert isinstance(trans1, dict), "Should return dictionary"
    
    def test_api_consistency_with_content(self):
        """Test API consistency with a graph that has content."""
        # Create a graph with some content
        graph = EGGraph.create_empty()
        
        # Add entities
        socrates = Entity.create("Socrates", "constant")
        graph = graph.add_entity(socrates, graph.root_context_id)
        
        # Add predicate
        person_pred = Predicate.create("Person", [socrates.id], arity=1)
        graph = graph.add_predicate(person_pred, graph.root_context_id)
        
        # Test validation APIs
        result = graph.validate()
        assert result.is_valid, "Graph with content should be valid"
        
        errors = graph.validate_graph_integrity()
        assert len(errors) == 0, "Graph with content should have no errors"
        
        # Test cross-cut validation
        validator = CrossCutValidator()
        cross_result = validator.validate_graph(graph)
        assert not cross_result.has_violations, "Simple graph should have no cross-cut violations"
        
        # Test transformation engine
        trans_engine = TransformationEngine()
        transformations = trans_engine.get_available_transformations(graph)
        assert isinstance(transformations, dict), "Should return transformation dictionary"
        
        # Test game engine
        engine = EGGameEngine()
        game_state = engine.start_new_game(graph)
        moves = engine.get_available_moves(game_state)
        assert isinstance(moves, list), "Should return list of moves"


class TestPerformanceRegression:
    """Test that API changes don't impact performance."""
    
    def test_validation_performance(self):
        """Test that validation performance is maintained."""
        import time
        
        # Create a moderately complex graph
        graph = EGGraph.create_empty()
        
        for i in range(50):  # Smaller test for CI
            entity = Entity.create(f'Entity_{i}', 'constant')
            graph = graph.add_entity(entity, graph.root_context_id)
            
            if i % 10 == 0:
                predicate = Predicate.create(f'Pred_{i}', [entity.id], arity=1)
                graph = graph.add_predicate(predicate, graph.root_context_id)
        
        # Test validation performance
        start_time = time.time()
        result = graph.validate()
        validation_time = time.time() - start_time
        
        assert result.is_valid, "Complex graph should be valid"
        assert validation_time < 1.0, f"Validation should be fast, took {validation_time:.3f}s"


if __name__ == "__main__":
    # Allow running as script for quick testing
    pytest.main([__file__, "-v"])

