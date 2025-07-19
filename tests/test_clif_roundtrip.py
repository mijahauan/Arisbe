import sys; sys.path.append("src")
"""
Comprehensive round-trip tests for CLIF parsing and generation with function symbols.

This module tests that Parse → Generate → Parse produces semantically identical graphs,
with special focus on function symbol preservation and semantic consistency.
"""

import pytest
from typing import List, Dict, Any

import sys
import os

from clif_parser import CLIFParser
from clif_generator import CLIFGenerator, CLIFRoundTripValidator
from eg_types import Entity, Predicate


class TestCLIFRoundTripFunctions:
    """Test round-trip integrity for function symbols."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = CLIFParser()
        self.generator = CLIFGenerator()
        self.validator = CLIFRoundTripValidator()
    
    def _perform_roundtrip(self, clif_text: str) -> Dict[str, Any]:
        """Perform a complete round-trip test and return results."""
        # Step 1: Parse original CLIF
        parse_result1 = self.parser.parse(clif_text)
        assert len(parse_result1.errors) == 0, f"Parse errors: {parse_result1.errors}"
        assert parse_result1.graph is not None, "Parse failed to produce graph"
        
        # Step 2: Generate CLIF from parsed graph
        gen_result = self.generator.generate(parse_result1.graph)
        assert len(gen_result.errors) == 0, f"Generation errors: {gen_result.errors}"
        assert gen_result.clif_text is not None, "Generation failed to produce CLIF"
        
        # Step 3: Parse generated CLIF
        parse_result2 = self.parser.parse(gen_result.clif_text)
        assert len(parse_result2.errors) == 0, f"Re-parse errors: {parse_result2.errors}"
        assert parse_result2.graph is not None, "Re-parse failed to produce graph"
        
        # Step 4: Validate round-trip integrity
        validation = self.validator.validate_round_trip(parse_result1.graph, parse_result2.graph)
        
        return {
            'original_clif': clif_text,
            'generated_clif': gen_result.clif_text,
            'original_graph': parse_result1.graph,
            'roundtrip_graph': parse_result2.graph,
            'validation': validation
        }
    
    def test_simple_function_roundtrip(self):
        """Test round-trip for simple function terms."""
        clif_text = "(Person (fatherOf Socrates))"
        result = self._perform_roundtrip(clif_text)
        
        assert result['validation']['valid'], f"Round-trip validation failed: {result['validation']['errors']}"
        
        # Verify semantic preservation
        original = result['original_graph']
        roundtrip = result['roundtrip_graph']
        
        # Should have same number of entities and predicates
        assert len(original.entities) == len(roundtrip.entities)
        assert len(original.predicates) == len(roundtrip.predicates)
        
        # Should have one function predicate and one relation predicate
        function_preds = [p for p in original.predicates.values() 
                         if hasattr(p, 'predicate_type') and p.predicate_type == 'function']
        relation_preds = [p for p in original.predicates.values() 
                         if not hasattr(p, 'predicate_type') or p.predicate_type == 'relation']
        
        assert len(function_preds) == 1, "Should have exactly one function predicate"
        assert len(relation_preds) == 1, "Should have exactly one relation predicate"
        assert function_preds[0].name == 'fatherOf'
        assert relation_preds[0].name == 'Person'
    
    def test_nested_function_roundtrip(self):
        """Test round-trip for nested function terms."""
        clif_text = "(Wise (fatherOf (motherOf Socrates)))"
        result = self._perform_roundtrip(clif_text)
        
        assert result['validation']['valid'], f"Round-trip validation failed: {result['validation']['errors']}"
        
        # Verify nested structure is preserved
        original = result['original_graph']
        
        # Should have 3 entities: Socrates, motherOf(Socrates), fatherOf(motherOf(Socrates))
        assert len(original.entities) == 3
        
        # Should have 3 predicates: motherOf, fatherOf, Wise
        assert len(original.predicates) == 3
        
        # Check that function predicates exist
        function_names = [p.name for p in original.predicates.values() 
                         if hasattr(p, 'predicate_type') and p.predicate_type == 'function']
        assert 'motherOf' in function_names
        assert 'fatherOf' in function_names
    
    def test_function_with_multiple_arguments_roundtrip(self):
        """Test round-trip for functions with multiple arguments."""
        clif_text = "(Person (childOf Socrates Plato))"
        result = self._perform_roundtrip(clif_text)
        
        assert result['validation']['valid'], f"Round-trip validation failed: {result['validation']['errors']}"
        
        original = result['original_graph']
        
        # Should have 3 entities: Socrates, Plato, childOf(Socrates, Plato)
        assert len(original.entities) == 3
        
        # Should have 2 predicates: childOf (function), Person (relation)
        assert len(original.predicates) == 2
        
        # Verify function predicate has correct arity
        function_pred = next(p for p in original.predicates.values() 
                           if hasattr(p, 'predicate_type') and p.predicate_type == 'function')
        assert function_pred.name == 'childOf'
        assert function_pred.arity == 3  # 2 arguments + 1 return entity
    
    def test_function_in_quantified_expression_roundtrip(self):
        """Test round-trip for functions in quantified expressions."""
        clif_text = "(exists (x) (Person (fatherOf x)))"
        result = self._perform_roundtrip(clif_text)
        
        assert result['validation']['valid'], f"Round-trip validation failed: {result['validation']['errors']}"
        
        original = result['original_graph']
        
        # Should have 2 entities: x (variable), fatherOf(x) (functional_term)
        assert len(original.entities) == 2
        
        # Should have 2 predicates: fatherOf (function), Person (relation)
        assert len(original.predicates) == 2
    
    def test_function_in_equality_roundtrip(self):
        """Test round-trip for functions in equality statements."""
        clif_text = "(= (fatherOf Socrates) Plato)"
        result = self._perform_roundtrip(clif_text)
        
        assert result['validation']['valid'], f"Round-trip validation failed: {result['validation']['errors']}"
        
        original = result['original_graph']
        
        # Should have 3 entities: Socrates, fatherOf(Socrates), Plato
        assert len(original.entities) == 3
        
        # Should have 2 predicates: fatherOf (function), = (relation)
        assert len(original.predicates) == 2
    
    def test_zero_arity_function_roundtrip(self):
        """Test round-trip for zero-arity functions."""
        clif_text = "(Person (currentTime))"
        result = self._perform_roundtrip(clif_text)
        
        assert result['validation']['valid'], f"Round-trip validation failed: {result['validation']['errors']}"
        
        original = result['original_graph']
        
        # Should have 1 entity: currentTime() (functional_term)
        assert len(original.entities) == 1
        
        # Should have 2 predicates: currentTime (function), Person (relation)
        assert len(original.predicates) == 2
        
        # Verify zero-arity function
        function_pred = next(p for p in original.predicates.values() 
                           if hasattr(p, 'predicate_type') and p.predicate_type == 'function')
        assert function_pred.name == 'currentTime'
        assert function_pred.arity == 1  # 0 arguments + 1 return entity
    
    def test_function_entity_reuse_roundtrip(self):
        """Test round-trip for reused function entities."""
        clif_text = "(and (Person (fatherOf Socrates)) (Wise (fatherOf Socrates)))"
        result = self._perform_roundtrip(clif_text)
        
        assert result['validation']['valid'], f"Round-trip validation failed: {result['validation']['errors']}"
        
        original = result['original_graph']
        
        # Should have 2 entities: Socrates, fatherOf(Socrates) (reused)
        assert len(original.entities) == 2
        
        # Should have 3 predicates: fatherOf (function), Person (relation), Wise (relation)
        assert len(original.predicates) == 3
        
        # Verify function entity is reused
        function_entities = [e for e in original.entities.values() 
                           if hasattr(e, 'entity_type') and e.entity_type == 'functional_term']
        assert len(function_entities) == 1, "Function entity should be reused"
    
    def test_complex_mixed_expression_roundtrip(self):
        """Test round-trip for complex expressions mixing functions and relations."""
        clif_text = "(and (Person Socrates) (= (fatherOf Socrates) (teacherOf Plato)) (Wise (fatherOf Socrates)))"
        result = self._perform_roundtrip(clif_text)
        
        assert result['validation']['valid'], f"Round-trip validation failed: {result['validation']['errors']}"
        
        original = result['original_graph']
        
        # Should have appropriate number of entities and predicates
        assert len(original.entities) >= 4  # Socrates, Plato, fatherOf(Socrates), teacherOf(Plato)
        assert len(original.predicates) >= 5  # Person, fatherOf, teacherOf, =, Wise
        
        # Verify function predicates exist
        function_names = [p.name for p in original.predicates.values() 
                         if hasattr(p, 'predicate_type') and p.predicate_type == 'function']
        assert 'fatherOf' in function_names
        assert 'teacherOf' in function_names


class TestCLIFGenerationEdgeCases:
    """Test edge cases in CLIF generation for function symbols."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = CLIFParser()
        self.generator = CLIFGenerator()
    
    def test_function_without_return_entity(self):
        """Test generation of function predicate without return_entity field."""
        # This tests backward compatibility
        clif_text = "(Person Socrates)"
        parse_result = self.parser.parse(clif_text)
        
        # Manually modify predicate to be a function without return_entity
        predicate = list(parse_result.graph.predicates.values())[0]
        modified_predicate = Predicate.create(
            name=predicate.name,
            entities=list(predicate.entities),
            arity=predicate.arity,
            predicate_type='function',  # Make it a function
            return_entity=None,  # But no return entity
            properties=dict(predicate.properties)
        )
        
        # Replace in graph
        graph = parse_result.graph
        graph = graph.remove_predicate(predicate.id)
        graph = graph.add_predicate(modified_predicate, graph.root_context_id)
        
        # Should generate without errors (fallback to regular predicate)
        gen_result = self.generator.generate(graph)
        assert len(gen_result.errors) == 0
        assert gen_result.clif_text is not None
    
    def test_orphaned_functional_entity(self):
        """Test generation when functional entity has no corresponding function predicate."""
        clif_text = "(Person Socrates)"
        parse_result = self.parser.parse(clif_text)
        
        # Manually add a functional entity without corresponding function predicate
        from eg_types import Entity, new_entity_id
        orphaned_entity = Entity.create(
            name="orphaned_function_result",
            entity_type="functional_term"
        )
        
        graph = parse_result.graph.add_entity(orphaned_entity, parse_result.graph.root_context_id)
        
        # Should generate without errors (use entity name as fallback)
        gen_result = self.generator.generate(graph)
        assert len(gen_result.errors) == 0
        assert gen_result.clif_text is not None


class TestCLIFRoundTripValidator:
    """Test the round-trip validator functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = CLIFParser()
        self.validator = CLIFRoundTripValidator()
    
    def test_validator_detects_entity_count_mismatch(self):
        """Test that validator detects entity count mismatches."""
        # Create two graphs with different entity counts
        graph1 = self.parser.parse("(Person Socrates)").graph
        graph2 = self.parser.parse("(and (Person Socrates) (Wise Plato))").graph
        
        validation = self.validator.validate_round_trip(graph1, graph2)
        
        assert not validation['valid']
        assert any('Entity count mismatch' in error for error in validation['errors'])
    
    def test_validator_detects_predicate_count_mismatch(self):
        """Test that validator detects predicate count mismatches."""
        # Create two graphs with different predicate counts
        graph1 = self.parser.parse("(Person Socrates)").graph
        graph2 = self.parser.parse("(and (Person Socrates) (Wise Socrates))").graph
        
        validation = self.validator.validate_round_trip(graph1, graph2)
        
        assert not validation['valid']
        assert any('Predicate count mismatch' in error for error in validation['errors'])
    
    def test_validator_passes_identical_graphs(self):
        """Test that validator passes for identical graphs."""
        graph1 = self.parser.parse("(Person (fatherOf Socrates))").graph
        graph2 = self.parser.parse("(Person (fatherOf Socrates))").graph
        
        validation = self.validator.validate_round_trip(graph1, graph2)
        
        assert validation['valid']
        assert len(validation['errors']) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

