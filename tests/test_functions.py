"""
Test suite for function symbol support in CLIF parser.

This module tests the Dau compliance extensions for function symbols,
ensuring that functional terms are correctly parsed and represented
in the Entity-Predicate hypergraph architecture.
"""

import pytest
from typing import Dict, List, Set

# Import the modules
from src.clif_parser import CLIFParser, CLIFParseResult
from src.eg_types import Entity, Predicate, Context, EntityId, PredicateId
from src.graph import EGGraph


class TestFunctionSupport:
    """Test suite for function symbol support in CLIF parser."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = CLIFParser()
    
    def test_simple_function_term(self):
        """Test parsing simple function term: (Person (fatherOf Socrates))"""
        clif_text = "(Person (fatherOf Socrates))"
        result = self.parser.parse(clif_text)
        
        assert result.graph is not None
        assert len(result.errors) == 0
        
        graph = result.graph
        
        # Should create 2 entities: Socrates and the result of fatherOf(Socrates)
        assert len(graph.entities) == 2
        
        # Should create 2 predicates: fatherOf function and Person relation
        assert len(graph.predicates) == 2
        
        # Find the entities
        socrates_entity = None
        father_result_entity = None
        for entity in graph.entities.values():
            if entity.name == "Socrates":
                socrates_entity = entity
            elif entity.entity_type == "functional_term":
                father_result_entity = entity
        
        assert socrates_entity is not None
        assert socrates_entity.entity_type == "constant"
        assert father_result_entity is not None
        
        # Find the predicates
        father_predicate = None
        person_predicate = None
        for predicate in graph.predicates.values():
            if predicate.name == "fatherOf":
                father_predicate = predicate
            elif predicate.name == "Person":
                person_predicate = predicate
        
        assert father_predicate is not None
        assert father_predicate.predicate_type == "function"
        assert father_predicate.arity == 2  # input + output
        assert father_predicate.return_entity == father_result_entity.id
        assert socrates_entity.id in father_predicate.entities
        assert father_result_entity.id in father_predicate.entities
        
        assert person_predicate is not None
        assert person_predicate.predicate_type == "relation"
        assert person_predicate.arity == 1
        assert father_result_entity.id in person_predicate.entities
    
    def test_nested_function_terms(self):
        """Test parsing nested function terms: (GrandfatherOf (fatherOf (fatherOf Socrates)))"""
        clif_text = "(GrandfatherOf (fatherOf (fatherOf Socrates)))"
        result = self.parser.parse(clif_text)
        
        assert result.graph is not None
        assert len(result.errors) == 0
        
        graph = result.graph
        
        # Should create 3 entities: Socrates, fatherOf(Socrates), fatherOf(fatherOf(Socrates))
        assert len(graph.entities) == 3
        
        # Should create 3 predicates: 2 fatherOf functions and 1 GrandfatherOf relation
        assert len(graph.predicates) == 3
        
        # Check that we have the right number of function predicates
        function_predicates = [p for p in graph.predicates.values() if p.predicate_type == "function"]
        relation_predicates = [p for p in graph.predicates.values() if p.predicate_type == "relation"]
        
        assert len(function_predicates) == 2
        assert len(relation_predicates) == 1
        
        # Check that all function predicates have return entities
        for func_pred in function_predicates:
            assert func_pred.return_entity is not None
            assert func_pred.name == "fatherOf"
    
    def test_function_with_multiple_arguments(self):
        """Test parsing function with multiple arguments: (Equals (sumOf 2 3) 5)"""
        clif_text = "(Equals (sumOf 2 3) 5)"
        result = self.parser.parse(clif_text)
        
        assert result.graph is not None
        assert len(result.errors) == 0
        
        graph = result.graph
        
        # Should create 4 entities: 2, 3, 5, and sumOf(2,3)
        assert len(graph.entities) == 4
        
        # Should create 2 predicates: sumOf function and Equals relation
        assert len(graph.predicates) == 2
        
        # Find the sumOf function predicate
        sum_predicate = None
        for predicate in graph.predicates.values():
            if predicate.name == "sumOf":
                sum_predicate = predicate
                break
        
        assert sum_predicate is not None
        assert sum_predicate.predicate_type == "function"
        assert sum_predicate.arity == 3  # 2 inputs + 1 output
        assert sum_predicate.return_entity is not None
        
        # Find the Equals relation predicate
        equals_predicate = None
        for predicate in graph.predicates.values():
            if predicate.name == "Equals":
                equals_predicate = predicate
                break
        
        assert equals_predicate is not None
        assert equals_predicate.predicate_type == "relation"
        assert equals_predicate.arity == 2
    
    def test_function_in_quantified_expression(self):
        """Test parsing function in quantified expression: (exists (x) (Person (fatherOf x)))"""
        clif_text = "(exists (x) (Person (fatherOf x)))"
        result = self.parser.parse(clif_text)
        
        assert result.graph is not None
        assert len(result.errors) == 0
        
        graph = result.graph
        
        # Should create 2 entities: x (variable) and fatherOf(x) (functional term)
        assert len(graph.entities) == 2
        
        # Should create 2 predicates: fatherOf function and Person relation
        assert len(graph.predicates) == 2
        
        # Check that we have one variable entity
        variable_entities = [e for e in graph.entities.values() if e.entity_type == "variable"]
        assert len(variable_entities) == 1
        assert variable_entities[0].name == "x"
        
        # Check that we have one functional term entity
        functional_entities = [e for e in graph.entities.values() if e.entity_type == "functional_term"]
        assert len(functional_entities) == 1
        
        # Check that we have one function predicate and one relation predicate
        function_predicates = [p for p in graph.predicates.values() if p.predicate_type == "function"]
        relation_predicates = [p for p in graph.predicates.values() if p.predicate_type == "relation"]
        
        assert len(function_predicates) == 1
        assert len(relation_predicates) == 1
        
        assert function_predicates[0].name == "fatherOf"
        assert relation_predicates[0].name == "Person"
    
    def test_function_in_equality(self):
        """Test parsing function in equality: (= (fatherOf Socrates) Sophroniscus)"""
        clif_text = "(= (fatherOf Socrates) Sophroniscus)"
        result = self.parser.parse(clif_text)
        
        assert result.graph is not None
        assert len(result.errors) == 0
        
        graph = result.graph
        
        # Should create 3 entities: Socrates, Sophroniscus, and fatherOf(Socrates)
        assert len(graph.entities) == 3
        
        # Should create 2 predicates: fatherOf function and = relation
        assert len(graph.predicates) == 2
        
        # Find the equality predicate
        equality_predicate = None
        for predicate in graph.predicates.values():
            if predicate.name == "=":
                equality_predicate = predicate
                break
        
        assert equality_predicate is not None
        assert equality_predicate.predicate_type == "relation"
        assert equality_predicate.arity == 2
        
        # Find the function predicate
        function_predicate = None
        for predicate in graph.predicates.values():
            if predicate.name == "fatherOf":
                function_predicate = predicate
                break
        
        assert function_predicate is not None
        assert function_predicate.predicate_type == "function"
        assert function_predicate.return_entity is not None
    
    def test_zero_arity_function(self):
        """Test parsing zero-arity function (constant function): (Person (currentTime))"""
        clif_text = "(Person (currentTime))"
        result = self.parser.parse(clif_text)
        
        assert result.graph is not None
        assert len(result.errors) == 0
        
        graph = result.graph
        
        # Should create 1 entity: the result of currentTime()
        assert len(graph.entities) == 1
        
        # Should create 2 predicates: currentTime function and Person relation
        assert len(graph.predicates) == 2
        
        # Find the currentTime function predicate
        time_predicate = None
        for predicate in graph.predicates.values():
            if predicate.name == "currentTime":
                time_predicate = predicate
                break
        
        assert time_predicate is not None
        assert time_predicate.predicate_type == "function"
        assert time_predicate.arity == 1  # 0 inputs + 1 output
        assert time_predicate.return_entity is not None
    
    def test_function_entity_reuse(self):
        """Test that identical function calls reuse the same entity."""
        clif_text = "(and (Person (fatherOf Socrates)) (Wise (fatherOf Socrates)))"
        result = self.parser.parse(clif_text)
        
        assert result.graph is not None
        assert len(result.errors) == 0
        
        graph = result.graph
        
        # Should create 2 entities: Socrates and fatherOf(Socrates)
        # The fatherOf(Socrates) entity should be reused
        assert len(graph.entities) == 2
        
        # Should create 3 predicates: 1 fatherOf function, Person relation, Wise relation
        assert len(graph.predicates) == 3
        
        # Find the function predicate
        function_predicates = [p for p in graph.predicates.values() if p.predicate_type == "function"]
        assert len(function_predicates) == 1
        
        father_predicate = function_predicates[0]
        father_result_entity_id = father_predicate.return_entity
        
        # Check that both Person and Wise predicates reference the same result entity
        person_predicate = None
        wise_predicate = None
        for predicate in graph.predicates.values():
            if predicate.name == "Person":
                person_predicate = predicate
            elif predicate.name == "Wise":
                wise_predicate = predicate
        
        assert person_predicate is not None
        assert wise_predicate is not None
        assert father_result_entity_id in person_predicate.entities
        assert father_result_entity_id in wise_predicate.entities
    
    def test_backward_compatibility(self):
        """Test that existing non-function parsing still works correctly."""
        clif_text = "(and (Person Socrates) (Wise Socrates))"
        result = self.parser.parse(clif_text)
        
        assert result.graph is not None
        assert len(result.errors) == 0
        
        graph = result.graph
        
        # Should create 1 entity: Socrates
        assert len(graph.entities) == 1
        
        # Should create 2 predicates: Person and Wise relations
        assert len(graph.predicates) == 2
        
        # All predicates should be relations
        for predicate in graph.predicates.values():
            assert predicate.predicate_type == "relation"
            assert predicate.return_entity is None
        
        # Find Socrates entity
        socrates_entity = list(graph.entities.values())[0]
        assert socrates_entity.name == "Socrates"
        assert socrates_entity.entity_type == "constant"
        
        # Both predicates should reference Socrates
        for predicate in graph.predicates.values():
            assert socrates_entity.id in predicate.entities

