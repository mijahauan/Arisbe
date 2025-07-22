#!/usr/bin/env python3

"""
EGRF Round-trip Conversion Tests (Fixed)

Tests round-trip conversion between EG-CL-Manus2 and EGRF formats.
Fixed to use proper pytest assertions instead of return statements.
"""

import unittest
import json

# Import EG-CL-Manus2 types
from graph import EGGraph
from eg_types import Entity, Predicate
from egrf import EGRFGenerator, EGRFParser, EGRFSerializer


def test_simple_round_trip():
    """Test simple round-trip conversion."""
    print("🔄 Testing Simple Round-trip Conversion")
    
    # Create original graph
    original_graph = EGGraph.create_empty()
    
    # Add entity
    entity = Entity.create(name="Socrates", entity_type="constant")
    original_graph = original_graph.add_entity(entity, original_graph.root_context_id)
    
    # Add predicates
    person_pred = Predicate.create(name="Person", entities=[entity.id])
    mortal_pred = Predicate.create(name="Mortal", entities=[entity.id])
    original_graph = original_graph.add_predicate(person_pred, original_graph.root_context_id)
    original_graph = original_graph.add_predicate(mortal_pred, original_graph.root_context_id)
    
    print(f"  1. Original graph: {len(original_graph.entities)} entities, {len(original_graph.predicates)} predicates")
    
    # Generate EGRF
    generator = EGRFGenerator()
    egrf_doc = generator.generate(original_graph)
    print(f"  2. EGRF generated: {len(egrf_doc.entities)} entities, {len(egrf_doc.predicates)} predicates")
    
    # Test JSON serialization
    json_str = EGRFSerializer.to_json(egrf_doc)
    egrf_doc_restored = EGRFSerializer.from_json(json_str, validate=False)
    print("  3. JSON round-trip successful")
    
    # Parse back
    parser = EGRFParser(validation_enabled=False)
    result = parser.parse(egrf_doc_restored)
    
    # Use assertions instead of returning values
    assert result.is_successful, f"Parsing failed: {result.errors}"
    
    reconstructed_graph = result.graph
    print(f"  4. Parsing successful: {len(reconstructed_graph.entities)} entities, {len(reconstructed_graph.predicates)} predicates")
    
    # Validate structure
    assert len(original_graph.entities) == len(reconstructed_graph.entities), "Entity count mismatch"
    assert len(original_graph.predicates) == len(reconstructed_graph.predicates), "Predicate count mismatch"
    
    # Check entity names
    original_entity_names = {e.name for e in original_graph.entities.values()}
    reconstructed_entity_names = {e.name for e in reconstructed_graph.entities.values()}
    assert original_entity_names == reconstructed_entity_names, "Entity names don't match"
    
    # Check predicate names
    original_predicate_names = {p.name for p in original_graph.predicates.values()}
    reconstructed_predicate_names = {p.name for p in reconstructed_graph.predicates.values()}
    assert original_predicate_names == reconstructed_predicate_names, "Predicate names don't match"
    
    print("  5. ✓ All validations passed")
    print("🎉 Simple round-trip test completed successfully!")


def test_empty_graph_round_trip():
    """Test round-trip conversion with empty graph."""
    print("🔄 Testing Empty Graph Round-trip")
    
    # Create empty graph
    original_graph = EGGraph.create_empty()
    print("  1. Empty graph created")
    
    # Generate EGRF
    generator = EGRFGenerator()
    egrf_doc = generator.generate(original_graph)
    print("  2. EGRF generated for empty graph")
    
    # Parse back
    parser = EGRFParser(validation_enabled=False)
    result = parser.parse(egrf_doc)
    
    # Use assertions instead of returning values
    assert result.is_successful, f"Empty graph parsing failed: {result.errors}"
    
    reconstructed_graph = result.graph
    
    # Validate empty structure
    assert len(reconstructed_graph.entities) == 0, "Empty graph should have no entities"
    assert len(reconstructed_graph.predicates) == 0, "Empty graph should have no predicates"
    
    print("  3. ✓ Empty graph round-trip successful")


def test_parser_error_handling():
    """Test parser error handling with invalid input."""
    print("🔄 Testing Parser Error Handling")
    
    parser = EGRFParser(validation_enabled=False)
    
    # Test invalid JSON
    result = parser.parse_from_json("invalid json")
    assert not result.is_successful, "Invalid JSON should fail"
    assert len(result.errors) > 0, "Should have error messages"
    assert "JSON parsing failed" in result.errors[0], "Should indicate JSON parsing failure"
    print("  1. ✓ Invalid JSON properly rejected")
    
    # Test empty JSON object
    result = parser.parse_from_json("{}")
    # Empty JSON should be handled gracefully
    assert result.is_successful, "Empty JSON should be accepted"
    print("  2. ✓ Empty JSON handled gracefully")
    
    print("✓ Error handling tests completed")


class TestEGRFRoundTrip(unittest.TestCase):
    """Unit test class for EGRF round-trip conversion."""
    
    def test_comprehensive_round_trip(self):
        """Test comprehensive round-trip with complex graph."""
        # Create complex graph
        original_graph = EGGraph.create_empty()
        
        # Add multiple entities
        entities = []
        for i in range(3):
            entity = Entity.create(name=f"Entity_{i}", entity_type="constant")
            original_graph = original_graph.add_entity(entity, original_graph.root_context_id)
            entities.append(entity)
        
        # Add predicates with different arities
        pred1 = Predicate.create(name="Unary", entities=[entities[0].id])
        pred2 = Predicate.create(name="Binary", entities=[entities[0].id, entities[1].id])
        pred3 = Predicate.create(name="Ternary", entities=[entities[0].id, entities[1].id, entities[2].id])
        
        original_graph = original_graph.add_predicate(pred1, original_graph.root_context_id)
        original_graph = original_graph.add_predicate(pred2, original_graph.root_context_id)
        original_graph = original_graph.add_predicate(pred3, original_graph.root_context_id)
        
        # Round-trip conversion
        generator = EGRFGenerator()
        parser = EGRFParser(validation_enabled=False)
        
        egrf_doc = generator.generate(original_graph)
        result = parser.parse(egrf_doc)
        
        self.assertTrue(result.is_successful)
        
        reconstructed_graph = result.graph
        
        # Validate structure preservation
        self.assertEqual(len(original_graph.entities), len(reconstructed_graph.entities))
        self.assertEqual(len(original_graph.predicates), len(reconstructed_graph.predicates))
        
        # Validate names preservation
        original_entity_names = {e.name for e in original_graph.entities.values()}
        reconstructed_entity_names = {e.name for e in reconstructed_graph.entities.values()}
        self.assertEqual(original_entity_names, reconstructed_entity_names)
        
        original_predicate_names = {p.name for p in original_graph.predicates.values()}
        reconstructed_predicate_names = {p.name for p in reconstructed_graph.predicates.values()}
        self.assertEqual(original_predicate_names, reconstructed_predicate_names)


if __name__ == '__main__':
    # Run standalone tests
    print("🚀 Starting EGRF Round-trip Conversion Tests")
    
    try:
        test_simple_round_trip()
        test_empty_graph_round_trip()
        test_parser_error_handling()
        
        print("\n📊 Test Results: All standalone tests passed")
        print("🎉 All round-trip tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise
    
    # Run unit tests
    print("\n🧪 Running unit tests...")
    unittest.main(verbosity=2, exit=False)

