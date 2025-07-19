
# test_performance.py
import time
import sys

from graph import EGGraph
from eg_types import Entity, Predicate

def test_performance():
    """Verify that API changes don't impact performance."""
    graph = EGGraph.create_empty()
    
    # Create a moderately complex graph
    start_time = time.time()
    
    for i in range(100):
        entity = Entity.create(f'Entity_{i}', 'constant')
        graph = graph.add_entity(entity, graph.root_context_id)
        
        if i % 10 == 0:
            predicate = Predicate.create(f'Pred_{i}', [entity.id], arity=1)
            graph = graph.add_predicate(predicate, graph.root_context_id)
    
    creation_time = time.time() - start_time
    
    # Test validation performance
    start_time = time.time()
    result = graph.validate()
    validation_time = time.time() - start_time
    
    print(f"✅ Graph creation (100 entities): {creation_time:.3f}s")
    print(f"✅ Validation time: {validation_time:.3f}s")
    print(f"✅ Graph is valid: {result.is_valid}")
    
    # Performance should be sub-second for this size
    assert creation_time < 1.0, "Performance regression in graph creation"
    assert validation_time < 0.1, "Performance regression in validation"
    
    print("✅ Performance maintained")

if __name__ == "__main__":
    test_performance()