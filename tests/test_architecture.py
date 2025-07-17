#!/usr/bin/env python3
"""
Test suite for the redesigned EG-HG architecture with correct hypergraph mapping.

This test suite validates that the new Entity-Predicate architecture works correctly
and produces the expected existential graph representations.
"""

import sys
import traceback
from typing import List, Dict, Any

# Import the redesigned modules
try:
    # Try importing as modules first
    import src.eg_types as eg_types
    import src.graph as graph_module
    
    from src.eg_types import (
        Entity, Predicate, Context,
        EntityId, PredicateId, ContextId,
        new_entity_id, new_predicate_id, new_context_id,
        create_simple_assertion, validate_predicate_entity_connection,
        EntityError, PredicateError, ContextError, ValidationError
    )
    from src.graph import (
        EGGraph,
        create_unary_assertion, create_binary_assertion, create_existential_assertion
    )
    print("✅ Successfully imported redesigned modules")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


def test_entity_creation():
    """Test Entity class creation and properties."""
    print("\n🧪 Testing Entity Creation...")
    
    # Test variable entity
    var_entity = Entity.create_variable("x")
    assert var_entity.is_variable
    assert not var_entity.is_constant
    assert not var_entity.is_anonymous
    assert var_entity.name == "x"
    print("✅ Variable entity creation works")
    
    # Test constant entity
    const_entity = Entity.create_constant("Socrates")
    assert not const_entity.is_variable
    assert const_entity.is_constant
    assert not const_entity.is_anonymous
    assert const_entity.name == "Socrates"
    print("✅ Constant entity creation works")
    
    # Test anonymous entity
    anon_entity = Entity.create_anonymous()
    assert not anon_entity.is_variable
    assert not anon_entity.is_constant
    assert anon_entity.is_anonymous
    assert anon_entity.name.startswith("entity_")
    print("✅ Anonymous entity creation works")
    
    # Test property setting
    entity_with_prop = var_entity.set_property("test", "value")
    assert entity_with_prop.properties["test"] == "value"
    assert var_entity.properties.get("test") is None  # Original unchanged
    print("✅ Entity property setting works")


def test_predicate_creation():
    """Test Predicate class creation and operations."""
    print("\n🧪 Testing Predicate Creation...")
    
    # Create some entities
    socrates = Entity.create_constant("Socrates")
    mary = Entity.create_constant("Mary")
    x = Entity.create_variable("x")
    
    # Test unary predicate
    person_pred = Predicate.create("Person", [socrates.id])
    assert person_pred.name == "Person"
    assert person_pred.arity == 1
    assert person_pred.is_unary
    assert not person_pred.is_binary
    assert socrates.id in person_pred.connected_entities
    print("✅ Unary predicate creation works")
    
    # Test binary predicate
    loves_pred = Predicate.create("Loves", [mary.id, socrates.id])
    assert loves_pred.name == "Loves"
    assert loves_pred.arity == 2
    assert not loves_pred.is_unary
    assert loves_pred.is_binary
    assert mary.id in loves_pred.connected_entities
    assert socrates.id in loves_pred.connected_entities
    print("✅ Binary predicate creation works")
    
    # Test adding entity to predicate
    expanded_pred = person_pred.add_entity(x.id)
    assert expanded_pred.arity == 2
    assert x.id in expanded_pred.connected_entities
    assert person_pred.arity == 1  # Original unchanged
    print("✅ Predicate entity addition works")
    
    # Test removing entity from predicate
    reduced_pred = loves_pred.remove_entity(mary.id)
    assert reduced_pred.arity == 1
    assert mary.id not in reduced_pred.connected_entities
    assert socrates.id in reduced_pred.connected_entities
    print("✅ Predicate entity removal works")


def test_context_creation():
    """Test Context class creation and operations."""
    print("\n🧪 Testing Context Creation...")
    
    # Create root context
    root_context = Context.create("sheet_of_assertion")
    assert root_context.is_root
    assert root_context.is_positive
    assert not root_context.is_negative
    assert root_context.depth == 0
    print("✅ Root context creation works")
    
    # Create child context
    child_context = Context.create("existential", root_context.id, depth=1)
    assert not child_context.is_root
    assert not child_context.is_positive
    assert child_context.is_negative
    assert child_context.depth == 1
    assert child_context.parent_context == root_context.id
    print("✅ Child context creation works")
    
    # Test adding items to context
    entity = Entity.create_variable("x")
    predicate = Predicate.create("Person", [entity.id])
    
    context_with_entity = root_context.add_entity(entity.id)
    assert entity.id in context_with_entity.contained_entities
    assert entity.id not in root_context.contained_entities  # Original unchanged
    
    context_with_predicate = context_with_entity.add_predicate(predicate.id)
    assert predicate.id in context_with_predicate.contained_predicates
    assert entity.id in context_with_predicate.contained_entities
    print("✅ Context item addition works")


def test_simple_assertion_creation():
    """Test creating simple assertions using utility functions."""
    print("\n🧪 Testing Simple Assertion Creation...")
    
    # Test create_simple_assertion utility
    entities, predicate = create_simple_assertion("Person", ["Socrates"])
    assert len(entities) == 1
    assert entities[0].name == "Socrates"
    assert entities[0].is_constant
    assert predicate.name == "Person"
    assert predicate.arity == 1
    assert entities[0].id in predicate.connected_entities
    print("✅ Simple assertion creation works")
    
    # Test with multiple entities
    entities, predicate = create_simple_assertion("Loves", ["Mary", "John"])
    assert len(entities) == 2
    assert entities[0].name == "Mary"
    assert entities[1].name == "John"
    assert predicate.name == "Loves"
    assert predicate.arity == 2
    print("✅ Multi-entity assertion creation works")
    
    # Test with variables
    entities, predicate = create_simple_assertion("Person", ["x"])
    assert len(entities) == 1
    assert entities[0].name == "x"
    assert entities[0].is_variable
    print("✅ Variable assertion creation works")


def test_graph_creation():
    """Test EGGraph creation and basic operations."""
    print("\n🧪 Testing Graph Creation...")
    
    # Test empty graph creation
    graph = EGGraph.create_empty()
    assert len(graph.entities) == 0
    assert len(graph.predicates) == 0
    assert len(graph.contexts) == 1  # Root context
    assert graph.root_context_id in graph.contexts
    print("✅ Empty graph creation works")
    
    # Test simple assertion graph
    graph = create_unary_assertion("Person", "Socrates")
    assert len(graph.entities) == 1
    assert len(graph.predicates) == 1
    assert len(graph.contexts) == 1
    
    # Verify the entity
    socrates_entity = list(graph.entities.values())[0]
    assert socrates_entity.name == "Socrates"
    assert socrates_entity.is_constant
    
    # Verify the predicate
    person_predicate = list(graph.predicates.values())[0]
    assert person_predicate.name == "Person"
    assert person_predicate.arity == 1
    assert socrates_entity.id in person_predicate.connected_entities
    print("✅ Simple assertion graph creation works")
    
    # Test binary assertion graph
    graph = create_binary_assertion("Loves", "Mary", "John")
    assert len(graph.entities) == 2
    assert len(graph.predicates) == 1
    
    entities = list(graph.entities.values())
    entity_names = {e.name for e in entities}
    assert "Mary" in entity_names
    assert "John" in entity_names
    
    loves_predicate = list(graph.predicates.values())[0]
    assert loves_predicate.name == "Loves"
    assert loves_predicate.arity == 2
    print("✅ Binary assertion graph creation works")


def test_existential_graph():
    """Test existential quantification graph creation."""
    print("\n🧪 Testing Existential Graph Creation...")
    
    # Create existential assertion: (exists (x) (Person x))
    graph = create_existential_assertion("Person", "x")
    assert len(graph.entities) == 1
    assert len(graph.predicates) == 1
    assert len(graph.contexts) == 2  # Root + existential context
    
    # Verify the variable entity
    x_entity = list(graph.entities.values())[0]
    assert x_entity.name == "x"
    assert x_entity.is_variable
    
    # Verify the predicate
    person_predicate = list(graph.predicates.values())[0]
    assert person_predicate.name == "Person"
    assert x_entity.id in person_predicate.connected_entities
    
    # Verify contexts
    contexts = list(graph.contexts.values())
    root_context = next(c for c in contexts if c.is_root)
    existential_context = next(c for c in contexts if not c.is_root)
    
    assert existential_context.context_type == "existential"
    assert existential_context.parent_context == root_context.id
    assert existential_context.depth == 1
    assert x_entity.id in existential_context.contained_entities
    assert person_predicate.id in existential_context.contained_predicates
    print("✅ Existential graph creation works")


def test_graph_operations():
    """Test graph manipulation operations."""
    print("\n🧪 Testing Graph Operations...")
    
    # Start with empty graph
    graph = EGGraph.create_empty()
    
    # Add an entity
    socrates = Entity.create_constant("Socrates")
    graph = graph.add_entity(socrates)
    assert socrates.id in graph.entities
    assert socrates.id in graph.contexts[graph.root_context_id].contained_entities
    print("✅ Entity addition works")
    
    # Add a predicate
    person_pred = Predicate.create("Person", [socrates.id])
    graph = graph.add_predicate(person_pred)
    assert person_pred.id in graph.predicates
    assert person_pred.id in graph.contexts[graph.root_context_id].contained_predicates
    print("✅ Predicate addition works")
    
    # Test finding predicates for entity
    predicates_for_socrates = graph.find_predicates_for_entity(socrates.id)
    assert len(predicates_for_socrates) == 1
    assert predicates_for_socrates[0].name == "Person"
    print("✅ Finding predicates for entity works")
    
    # Test finding entities for predicate
    entities_for_person = graph.find_entities_for_predicate(person_pred.id)
    assert len(entities_for_person) == 1
    assert entities_for_person[0].name == "Socrates"
    print("✅ Finding entities for predicate works")
    
    # Test removing entity (should also update predicate)
    graph = graph.remove_entity(socrates.id)
    assert socrates.id not in graph.entities
    updated_predicate = graph.get_predicate(person_pred.id)
    assert len(updated_predicate.connected_entities) == 0
    print("✅ Entity removal and predicate update works")


def test_graph_validation():
    """Test graph validation functionality."""
    print("\n🧪 Testing Graph Validation...")
    
    # Test valid graph
    graph = create_unary_assertion("Person", "Socrates")
    errors = graph.validate_graph_consistency()
    assert len(errors) == 0
    print("✅ Valid graph validation works")
    
    # Test graph statistics
    stats = graph.get_graph_statistics()
    assert stats['num_entities'] == 1
    assert stats['num_predicates'] == 1
    assert stats['num_contexts'] == 1
    assert stats['entities_by_type']['constants'] == 1
    assert stats['predicates_by_arity']['unary'] == 1
    print("✅ Graph statistics work")
    
    # Test simple representation
    simple_repr = graph.to_simple_representation()
    assert 'entities' in simple_repr
    assert 'predicates' in simple_repr
    assert 'contexts' in simple_repr
    assert 'root_context' in simple_repr
    print("✅ Simple representation works")


def test_shared_entities():
    """Test finding shared entities between predicates (Lines of Identity)."""
    print("\n🧪 Testing Shared Entities (Lines of Identity)...")
    
    # Create graph with shared entity
    graph = EGGraph.create_empty()
    
    # Add shared entity
    socrates = Entity.create_constant("Socrates")
    graph = graph.add_entity(socrates)
    
    # Add two predicates sharing the entity
    person_pred = Predicate.create("Person", [socrates.id])
    mortal_pred = Predicate.create("Mortal", [socrates.id])
    graph = graph.add_predicate(person_pred)
    graph = graph.add_predicate(mortal_pred)
    
    # Test finding shared entities
    shared = graph.find_shared_entities(person_pred.id, mortal_pred.id)
    assert len(shared) == 1
    assert shared[0].name == "Socrates"
    print("✅ Shared entity detection works (Lines of Identity)")
    
    # Test with no shared entities
    mary = Entity.create_constant("Mary")
    graph = graph.add_entity(mary)
    loves_pred = Predicate.create("Loves", [mary.id])
    graph = graph.add_predicate(loves_pred)
    
    no_shared = graph.find_shared_entities(person_pred.id, loves_pred.id)
    assert len(no_shared) == 0
    print("✅ No shared entity detection works")


def run_all_tests():
    """Run all tests and report results."""
    print("🚀 Running Redesigned Architecture Tests...")
    print("=" * 60)
    
    test_functions = [
        test_entity_creation,
        test_predicate_creation,
        test_context_creation,
        test_simple_assertion_creation,
        test_graph_creation,
        test_existential_graph,
        test_graph_operations,
        test_graph_validation,
        test_shared_entities
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} FAILED: {e}")
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! The redesigned architecture is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
        return False


def demonstrate_correct_mapping():
    """Demonstrate the correct hypergraph mapping with examples."""
    print("\n🎯 Demonstrating Correct Hypergraph Mapping...")
    print("=" * 60)
    
    print("\n📝 Example 1: (Person Socrates)")
    graph1 = create_unary_assertion("Person", "Socrates")
    print("Correct Interpretation:")
    print("  - Entity: 'Socrates' (Line of Identity)")
    print("  - Predicate: 'Person' (hyperedge connecting to Socrates)")
    print(f"  - Graph: {graph1}")
    
    print("\n📝 Example 2: (Loves Mary John)")
    graph2 = create_binary_assertion("Loves", "Mary", "John")
    print("Correct Interpretation:")
    print("  - Entity: 'Mary' (Line of Identity)")
    print("  - Entity: 'John' (Line of Identity)")
    print("  - Predicate: 'Loves' (hyperedge connecting Mary and John)")
    print(f"  - Graph: {graph2}")
    
    print("\n📝 Example 3: (exists (x) (Person x))")
    graph3 = create_existential_assertion("Person", "x")
    print("Correct Interpretation:")
    print("  - Context: Existential scope for variable x")
    print("  - Entity: 'x' (Line of Identity within scope)")
    print("  - Predicate: 'Person' (hyperedge connecting to x)")
    print(f"  - Graph: {graph3}")
    
    print("\n✅ This demonstrates the correct hypergraph mapping:")
    print("   - Entities (things that exist) → Primary nodes")
    print("   - Predicates (relations) → Hyperedges connecting entities")
    print("   - Contexts (cuts) → Logical scopes containing entities and predicates")


if __name__ == "__main__":
    success = run_all_tests()
    demonstrate_correct_mapping()
    
    if success:
        print("\n🎉 Architecture redesign is complete and validated!")
        print("✅ Ready to proceed with Phase 2: CLIF Parser redesign")
    else:
        print("\n❌ Architecture issues need to be resolved before proceeding")
        sys.exit(1)

