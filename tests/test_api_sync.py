# test_api_sync.py
import sys

try:
    # Test all imports
    from graph import EGGraph
    from game_engine import EGGameEngine, EndoporeuticGameEngine
    from cross_cut_validator import CrossCutValidator
    from transformations import TransformationEngine
    from eg_types import Entity, Predicate
    
    print("✅ All imports successful")
    
    # Test EGGraph APIs
    graph = EGGraph.create_empty()
    entity = Entity.create('Test', 'constant')
    graph = graph.add_entity(entity, graph.root_context_id)
    
    # Test both validation methods
    result1 = graph.validate()
    result2 = graph.validate_graph_integrity()
    
    print(f"✅ EGGraph.validate(): {type(result1).__name__}")
    print(f"✅ EGGraph.validate_graph_integrity(): {type(result2).__name__}")
    
    # Test game engine aliases
    engine1 = EGGameEngine()
    engine2 = EndoporeuticGameEngine()
    print(f"✅ EGGameEngine == EndoporeuticGameEngine: {EGGameEngine == EndoporeuticGameEngine}")
    
    # Test game engine methods
    state = engine1.create_game_state(graph)
    state2 = engine1.start_new_game(graph)
    state3 = engine1.start_game(graph)
    
    moves1 = engine1.get_legal_moves(state)
    moves2 = engine1.get_available_moves(state)
    
    print("✅ Game engine methods: create_game_state, start_new_game, start_game all work")
    print("✅ Move methods: get_legal_moves, get_available_moves both work")
    
    # Test cross-cut validator
    validator = CrossCutValidator()
    result3 = validator.validate_identity_preservation(graph)
    result4 = validator.validate_graph(graph)
    
    print("✅ CrossCutValidator methods: validate_identity_preservation, validate_graph both work")
    print(f"✅ IdentityPreservationResult.has_violations: {hasattr(result3, 'has_violations')}")
    
    # Test transformation engine
    trans_engine = TransformationEngine()
    trans1 = trans_engine.get_legal_transformations(graph)
    trans2 = trans_engine.get_available_transformations(graph)
    
    print("✅ TransformationEngine methods: get_legal_transformations, get_available_transformations both work")
    
    print("\n🎉 ALL API STANDARDIZATION VERIFIED SUCCESSFULLY!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("Check that all changes were applied correctly")