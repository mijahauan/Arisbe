"""
Final comprehensive test suite for the fixed CLIF parser and generator.

This test suite validates that all API compatibility issues have been resolved
and that the Entity-Predicate architecture works correctly.
"""

import pytest
from typing import Dict, List, Set

# Import the fixed modules
from src.clif_parser import CLIFParser, CLIFParseResult
from src.clif_generator import CLIFGenerator, CLIFGenerationResult, CLIFRoundTripValidator
from src.graph import EGGraph
from src.eg_types import Entity, Predicate, Context, EntityId, PredicateId


class TestCLIFParserFinal:
    """Final test suite for the fixed CLIF parser."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = CLIFParser()
    
    def test_simple_atomic_predicate(self):
        """Test parsing simple atomic predicate: (Person Socrates)"""
        clif_text = "(Person Socrates)"
        result = self.parser.parse(clif_text)
        
        assert result.graph is not None, f"Parse failed with errors: {result.errors}"
        assert len(result.errors) == 0, f"Unexpected errors: {result.errors}"
        
        graph = result.graph
        
        # Should create one entity and one predicate
        assert len(graph.entities) == 1, f"Expected 1 entity, got {len(graph.entities)}"
        assert len(graph.predicates) == 1, f"Expected 1 predicate, got {len(graph.predicates)}"
        
        # Check entity
        entity = list(graph.entities.values())[0]
        assert entity.name == "Socrates"
        assert entity.entity_type == "constant"
        
        # Check predicate
        predicate = list(graph.predicates.values())[0]
        assert predicate.name == "Person"
        assert predicate.arity == 1
        assert entity.id in predicate.entities
    
    def test_binary_predicate(self):
        """Test parsing binary predicate: (Loves Mary John)"""
        clif_text = "(Loves Mary John)"
        result = self.parser.parse(clif_text)
        
        assert result.graph is not None, f"Parse failed with errors: {result.errors}"
        assert len(result.errors) == 0, f"Unexpected errors: {result.errors}"
        
        graph = result.graph
        
        # Should create two entities and one predicate
        assert len(graph.entities) == 2, f"Expected 2 entities, got {len(graph.entities)}"
        assert len(graph.predicates) == 1, f"Expected 1 predicate, got {len(graph.predicates)}"
        
        # Check entities
        entity_names = {entity.name for entity in graph.entities.values()}
        assert entity_names == {"Mary", "John"}
        
        # Check predicate
        predicate = list(graph.predicates.values())[0]
        assert predicate.name == "Loves"
        assert predicate.arity == 2
        assert len(predicate.entities) == 2
    
    def test_zero_arity_predicate(self):
        """Test parsing zero-arity predicate: (Raining)"""
        clif_text = "(Raining)"
        result = self.parser.parse(clif_text)
        
        assert result.graph is not None, f"Parse failed with errors: {result.errors}"
        assert len(result.errors) == 0, f"Unexpected errors: {result.errors}"
        
        graph = result.graph
        
        # Should create no entities and one predicate
        assert len(graph.entities) == 0, f"Expected 0 entities, got {len(graph.entities)}"
        assert len(graph.predicates) == 1, f"Expected 1 predicate, got {len(graph.predicates)}"
        
        # Check predicate
        predicate = list(graph.predicates.values())[0]
        assert predicate.name == "Raining"
        assert predicate.arity == 0
        assert len(predicate.entities) == 0
    
    def test_existential_quantification(self):
        """Test parsing existential quantification: (exists (x) (Person x))"""
        clif_text = "(exists (x) (Person x))"
        result = self.parser.parse(clif_text)
        
        assert result.graph is not None, f"Parse failed with errors: {result.errors}"
        assert len(result.errors) == 0, f"Unexpected errors: {result.errors}"
        
        graph = result.graph
        
        # Should create one entity (variable) and one predicate
        assert len(graph.entities) == 1, f"Expected 1 entity, got {len(graph.entities)}"
        assert len(graph.predicates) == 1, f"Expected 1 predicate, got {len(graph.predicates)}"
        
        # Check entity
        entity = list(graph.entities.values())[0]
        assert entity.name == "x"
        assert entity.entity_type == "variable"
        
        # Check predicate
        predicate = list(graph.predicates.values())[0]
        assert predicate.name == "Person"
        assert entity.id in predicate.entities
        
        # Check context structure
        assert len(graph.contexts) >= 2, f"Expected at least 2 contexts, got {len(graph.contexts)}"
    
    def test_conjunction_with_shared_variable(self):
        """Test parsing conjunction with shared variable: (exists (x) (and (Person x) (Mortal x)))"""
        clif_text = "(exists (x) (and (Person x) (Mortal x)))"
        result = self.parser.parse(clif_text)
        
        assert result.graph is not None, f"Parse failed with errors: {result.errors}"
        assert len(result.errors) == 0, f"Unexpected errors: {result.errors}"
        
        graph = result.graph
        
        # Should create one entity (shared variable) and two predicates
        assert len(graph.entities) == 1, f"Expected 1 entity, got {len(graph.entities)}"
        assert len(graph.predicates) == 2, f"Expected 2 predicates, got {len(graph.predicates)}"
        
        # Check entity
        entity = list(graph.entities.values())[0]
        assert entity.name == "x"
        assert entity.entity_type == "variable"
        
        # Check predicates
        predicate_names = {pred.name for pred in graph.predicates.values()}
        assert predicate_names == {"Person", "Mortal"}
        
        # Both predicates should connect to the same entity (Line of Identity)
        for predicate in graph.predicates.values():
            assert entity.id in predicate.entities, f"Entity {entity.id} not in predicate {predicate.name}"


class TestCLIFGeneratorFinal:
    """Final test suite for the fixed CLIF generator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.generator = CLIFGenerator()
    
    def test_generate_simple_predicate(self):
        """Test generating CLIF from simple predicate graph."""
        # Create graph with one entity and one predicate
        graph = EGGraph.create_empty()
        
        # Add entity
        entity = Entity.create(name="Socrates", entity_type="constant")
        graph = graph.add_entity(entity, graph.root_context_id)
        
        # Add predicate
        predicate = Predicate.create(name="Person", entities=[entity.id], arity=1)
        graph = graph.add_predicate(predicate, graph.root_context_id)
        
        # Generate CLIF
        result = self.generator.generate(graph)
        
        assert result.clif_text is not None, f"Generation failed with errors: {result.errors}"
        assert len(result.errors) == 0, f"Unexpected errors: {result.errors}"
        assert "Person" in result.clif_text
        assert "Socrates" in result.clif_text
    
    def test_generate_binary_predicate(self):
        """Test generating CLIF from binary predicate graph."""
        # Create graph with two entities and one predicate
        graph = EGGraph.create_empty()
        
        # Add entities
        entity1 = Entity.create(name="Mary", entity_type="constant")
        entity2 = Entity.create(name="John", entity_type="constant")
        graph = graph.add_entity(entity1, graph.root_context_id)
        graph = graph.add_entity(entity2, graph.root_context_id)
        
        # Add predicate
        predicate = Predicate.create(name="Loves", entities=[entity1.id, entity2.id], arity=2)
        graph = graph.add_predicate(predicate, graph.root_context_id)
        
        # Generate CLIF
        result = self.generator.generate(graph)
        
        assert result.clif_text is not None, f"Generation failed with errors: {result.errors}"
        assert len(result.errors) == 0, f"Unexpected errors: {result.errors}"
        assert "Loves" in result.clif_text
        assert "Mary" in result.clif_text
        assert "John" in result.clif_text
    
    def test_generate_zero_arity_predicate(self):
        """Test generating CLIF from zero-arity predicate graph."""
        # Create graph with zero-arity predicate
        graph = EGGraph.create_empty()
        
        # Add predicate
        predicate = Predicate.create(name="Raining", entities=[], arity=0)
        graph = graph.add_predicate(predicate, graph.root_context_id)
        
        # Generate CLIF
        result = self.generator.generate(graph)
        
        assert result.clif_text is not None, f"Generation failed with errors: {result.errors}"
        assert len(result.errors) == 0, f"Unexpected errors: {result.errors}"
        assert "Raining" in result.clif_text


class TestCLIFRoundTripFinal:
    """Final test suite for CLIF round-trip conversion."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = CLIFParser()
        self.generator = CLIFGenerator()
        self.validator = CLIFRoundTripValidator()
    
    def test_simple_predicate_roundtrip(self):
        """Test round-trip conversion for simple predicate."""
        original_clif = "(Person Socrates)"
        
        # Parse to graph
        parse_result = self.parser.parse(original_clif)
        assert parse_result.graph is not None, f"Parse failed: {parse_result.errors}"
        assert len(parse_result.errors) == 0
        
        # Generate back to CLIF
        gen_result = self.generator.generate(parse_result.graph)
        assert gen_result.clif_text is not None, f"Generation failed: {gen_result.errors}"
        assert len(gen_result.errors) == 0
        
        # Parse the generated CLIF again
        reparse_result = self.parser.parse(gen_result.clif_text)
        assert reparse_result.graph is not None, f"Reparse failed: {reparse_result.errors}"
        assert len(reparse_result.errors) == 0
        
        # Compare graph structures
        original_graph = parse_result.graph
        roundtrip_graph = reparse_result.graph
        
        # Should have same number of entities and predicates
        assert len(original_graph.entities) == len(roundtrip_graph.entities)
        assert len(original_graph.predicates) == len(roundtrip_graph.predicates)
    
    def test_binary_predicate_roundtrip(self):
        """Test round-trip conversion for binary predicate."""
        original_clif = "(Loves Mary John)"
        
        # Parse to graph
        parse_result = self.parser.parse(original_clif)
        assert parse_result.graph is not None, f"Parse failed: {parse_result.errors}"
        
        # Generate back to CLIF
        gen_result = self.generator.generate(parse_result.graph)
        assert gen_result.clif_text is not None, f"Generation failed: {gen_result.errors}"
        
        # Parse the generated CLIF again
        reparse_result = self.parser.parse(gen_result.clif_text)
        assert reparse_result.graph is not None, f"Reparse failed: {reparse_result.errors}"
        
        # Compare graph structures
        original_graph = parse_result.graph
        roundtrip_graph = reparse_result.graph
        
        assert len(original_graph.entities) == len(roundtrip_graph.entities)
        assert len(original_graph.predicates) == len(roundtrip_graph.predicates)


class TestArchitecturalCorrectnessFinal:
    """Final test suite to validate the correct Entity-Predicate architecture."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = CLIFParser()
    
    def test_entities_are_lines_of_identity(self):
        """Test that entities represent Lines of Identity correctly."""
        clif_text = "(exists (x) (and (Person x) (Mortal x)))"
        result = self.parser.parse(clif_text)
        
        assert result.graph is not None, f"Parse failed: {result.errors}"
        graph = result.graph
        
        # Should have exactly one entity (the Line of Identity for x)
        assert len(graph.entities) == 1
        entity = list(graph.entities.values())[0]
        assert entity.name == "x"
        assert entity.entity_type == "variable"
        
        # Both predicates should connect to the same entity
        assert len(graph.predicates) == 2
        for predicate in graph.predicates.values():
            assert entity.id in predicate.entities
    
    def test_predicates_are_hyperedges(self):
        """Test that predicates are hyperedges connecting entities."""
        clif_text = "(Loves Mary John)"
        result = self.parser.parse(clif_text)
        
        assert result.graph is not None, f"Parse failed: {result.errors}"
        graph = result.graph
        
        # Should have two entities and one predicate
        assert len(graph.entities) == 2
        assert len(graph.predicates) == 1
        
        # Predicate should connect both entities
        predicate = list(graph.predicates.values())[0]
        assert len(predicate.entities) == 2
        
        # All entities should be connected by the predicate
        entity_ids = {entity.id for entity in graph.entities.values()}
        assert set(predicate.entities) == entity_ids
    
    def test_constants_vs_variables(self):
        """Test proper distinction between constants and variables."""
        clif_text = "(exists (x) (Loves x Mary))"
        result = self.parser.parse(clif_text)
        
        assert result.graph is not None, f"Parse failed: {result.errors}"
        graph = result.graph
        
        # Should have two entities: one variable, one constant
        assert len(graph.entities) == 2
        
        entity_types = {entity.entity_type for entity in graph.entities.values()}
        assert entity_types == {"variable", "constant"}
        
        # Check specific entities
        entities_by_name = {entity.name: entity for entity in graph.entities.values()}
        assert entities_by_name["x"].entity_type == "variable"
        assert entities_by_name["Mary"].entity_type == "constant"


# Test data for parametrized tests
CLIF_TEST_CASES = [
    {
        'clif': '(Person Socrates)',
        'description': 'Simple atomic predicate',
        'expected_entities': 1,
        'expected_predicates': 1
    },
    {
        'clif': '(Loves Mary John)',
        'description': 'Binary predicate',
        'expected_entities': 2,
        'expected_predicates': 1
    },
    {
        'clif': '(Raining)',
        'description': 'Zero-arity predicate',
        'expected_entities': 0,
        'expected_predicates': 1
    },
    {
        'clif': '(exists (x) (Person x))',
        'description': 'Existential quantification',
        'expected_entities': 1,
        'expected_predicates': 1
    },
    {
        'clif': '(exists (x) (and (Person x) (Mortal x)))',
        'description': 'Conjunction with shared variable',
        'expected_entities': 1,
        'expected_predicates': 2
    }
]


class TestParametrizedCLIFCasesFinal:
    """Parametrized tests for various CLIF cases."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = CLIFParser()
    
    @pytest.mark.parametrize("test_case", CLIF_TEST_CASES, ids=[case['description'] for case in CLIF_TEST_CASES])
    def test_clif_parsing(self, test_case):
        """Test parsing various CLIF expressions."""
        clif_text = test_case['clif']
        result = self.parser.parse(clif_text)
        
        assert result.graph is not None, f"Parse failed for {test_case['description']}: {result.errors}"
        assert len(result.errors) == 0, f"Unexpected errors for {test_case['description']}: {result.errors}"
        
        graph = result.graph
        
        # Check expected counts
        assert len(graph.entities) == test_case['expected_entities'], \
            f"Wrong entity count for: {test_case['description']}"
        assert len(graph.predicates) == test_case['expected_predicates'], \
            f"Wrong predicate count for: {test_case['description']}"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])

