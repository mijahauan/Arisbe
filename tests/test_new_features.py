# test_new_features.py
import sys

from graph import EGGraph
from game_engine import EGGameEngine, EndoporeuticGameEngine
from cross_cut_validator import CrossCutValidator
from transformations import TransformationEngine
from eg_types import Entity, Predicate

def test_new_validation_api():
    """Test the new structured validation API."""
    graph = EGGraph.create_empty()
    
    # Test new validate() method
    result = graph.validate()
    assert hasattr(result, 'is_valid')
    assert hasattr(result, 'errors')
    assert hasattr(result, 'warnings')
    assert result.is_valid == True
    assert result.errors == []
    print("✅ New validation API working")

def test_cross_cut_enhancements():
    """Test cross-cut validator enhancements."""
    validator = CrossCutValidator()
    graph = EGGraph.create_empty()
    
    # Test new validate_graph method
    result = validator.validate_graph(graph)
    assert hasattr(result, 'has_violations')
    assert result.has_violations == False
    print("✅ Cross-cut validator enhancements working")

def test_game_engine_aliases():
    """Test game engine class and method aliases."""
    # Test class alias
    engine = EGGameEngine()
    assert isinstance(engine, EndoporeuticGameEngine)
    
    # Test method aliases
    graph = EGGraph.create_empty()
    entity = Entity.create('Test', 'constant')
    graph = graph.add_entity(entity, graph.root_context_id)
    
    state1 = engine.start_new_game(graph)
    state2 = engine.start_game(graph)
    moves = engine.get_available_moves(state1)
    
    assert state1 is not None
    assert state2 is not None
    assert isinstance(moves, list)
    print("✅ Game engine aliases working")

def test_transformation_aliases():
    """Test transformation engine method aliases."""
    engine = TransformationEngine()
    graph = EGGraph.create_empty()
    
    # Test method alias
    trans1 = engine.get_legal_transformations(graph)
    trans2 = engine.get_available_transformations(graph)
    
    assert trans1 == trans2  # Should return identical results
    print("✅ Transformation engine aliases working")

if __name__ == "__main__":
    test_new_validation_api()
    test_cross_cut_enhancements()
    test_game_engine_aliases()
    test_transformation_aliases()
    print("\n🎉 ALL NEW FEATURES VERIFIED!")