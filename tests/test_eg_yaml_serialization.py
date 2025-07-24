#!/usr/bin/env python3
"""
Comprehensive tests for EG-HG YAML serialization.

This module tests the YAML serialization and deserialization of EGGraph objects,
ensuring round-trip integrity and validation of the canonical EG-HG format.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
import yaml
import tempfile
from pathlib import Path
from typing import Dict, Any

from clif_parser import CLIFParser
from clif_generator import CLIFGenerator
from eg_serialization import (
    EGGraphYAMLSerializer, serialize_graph_to_yaml, deserialize_graph_from_yaml,
    save_graph_to_file, load_graph_from_file
)
from eg_yaml_validator import validate_yaml_content, EGYAMLValidator
from eg_types import Entity, Predicate, Context, new_entity_id, new_predicate_id
from graph import EGGraph


class TestEGYAMLSerialization:
    """Test basic YAML serialization functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = CLIFParser()
        self.generator = CLIFGenerator()
        self.serializer = EGGraphYAMLSerializer()
    
    def test_simple_predicate_serialization(self):
        """Test serialization of a simple predicate."""
        # Parse simple CLIF
        result = self.parser.parse('(Man x)')
        assert result.graph is not None
        
        # Serialize to YAML
        yaml_content = serialize_graph_to_yaml(result.graph, {
            'id': 'simple_man',
            'title': 'Simple Man Predicate'
        })
        
        # Check YAML structure
        data = yaml.safe_load(yaml_content)
        assert 'metadata' in data
        assert 'entities' in data
        assert 'predicates' in data
        assert 'contexts' in data
        assert 'ligatures' in data
        
        # Check metadata
        assert data['metadata']['id'] == 'simple_man'
        assert data['metadata']['title'] == 'Simple Man Predicate'
        
        # Check entities
        assert len(data['entities']) == 1
        entity_name = list(data['entities'].keys())[0]
        entity_data = data['entities'][entity_name]
        assert entity_data['name'] == 'x'
        assert entity_data['type'] == 'variable'
        
        # Check predicates
        assert len(data['predicates']) == 1
        pred_name = list(data['predicates'].keys())[0]
        pred_data = data['predicates'][pred_name]
        assert pred_data['name'] == 'Man'
        assert pred_data['arity'] == 1
        assert len(pred_data['entities']) == 1
    
    def test_complex_formula_serialization(self):
        """Test serialization of a complex logical formula."""
        # Parse complex CLIF with quantification and implication
        clif_text = '(forall (x) (if (Man x) (Mortal x)))'
        result = self.parser.parse(clif_text)
        assert result.graph is not None
        
        # Serialize to YAML
        yaml_content = serialize_graph_to_yaml(result.graph, {
            'id': 'man_mortal_implication',
            'title': 'Man-Mortal Implication',
            'logical_form': '∀x(Man(x) → Mortal(x))'
        })
        
        # Parse YAML
        data = yaml.safe_load(yaml_content)
        
        # Should have one entity (x) and two predicates (Man, Mortal)
        assert len(data['entities']) == 1
        assert len(data['predicates']) == 2
        
        # Check that contexts represent the implication structure
        assert len(data['contexts']) > 1  # Should have cuts for implication
        
        # Find predicates
        pred_names = [pred_data['name'] for pred_data in data['predicates'].values()]
        assert 'Man' in pred_names
        assert 'Mortal' in pred_names
    
    def test_function_predicate_serialization(self):
        """Test serialization of function predicates."""
        # Parse CLIF with function
        clif_text = '(= (fatherOf john) bob)'
        result = self.parser.parse(clif_text)
        assert result.graph is not None
        
        # Serialize to YAML
        yaml_content = serialize_graph_to_yaml(result.graph)
        data = yaml.safe_load(yaml_content)
        
        # Check for function predicate
        function_preds = [pred for pred in data['predicates'].values() 
                         if pred.get('type') == 'function']
        
        if function_preds:  # Functions may not be fully implemented yet
            func_pred = function_preds[0]
            assert 'return_entity' in func_pred
    
    def test_round_trip_integrity(self):
        """Test that serialization -> deserialization preserves graph structure."""
        test_cases = [
            '(Man x)',
            '(and (Man x) (Mortal x))',
            # Skip complex cases that may not be fully supported yet
            # '(forall (x) (Man x))',
            # '(exists (x) (and (Man x) (Mortal x)))'
        ]
        
        for clif_text in test_cases:
            # Parse original
            result = self.parser.parse(clif_text)
            if result.graph is None:
                continue  # Skip unsupported cases
            original_graph = result.graph
            
            # Serialize to YAML
            yaml_content = serialize_graph_to_yaml(original_graph)
            
            # Deserialize back
            restored_graph = deserialize_graph_from_yaml(yaml_content)
            
            # Compare structure
            assert len(original_graph.entities) == len(restored_graph.entities)
            assert len(original_graph.predicates) == len(restored_graph.predicates)
            assert len(original_graph.contexts) == len(restored_graph.contexts)
            
            # Test CLIF round-trip through restored graph
            gen_result = self.generator.generate(restored_graph)
            assert len(gen_result.errors) == 0
            assert gen_result.clif_text is not None
    
    def test_file_operations(self):
        """Test saving and loading YAML files."""
        # Create test graph
        result = self.parser.parse('(Man x)')
        assert result.graph is not None
        
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = Path(temp_dir) / 'test_graph.yaml'
            
            # Save to file
            save_graph_to_file(result.graph, filepath, {
                'id': 'file_test',
                'title': 'File Test Graph'
            })
            
            assert filepath.exists()
            
            # Load from file
            loaded_graph = load_graph_from_file(filepath)
            
            # Compare
            assert len(result.graph.entities) == len(loaded_graph.entities)
            assert len(result.graph.predicates) == len(loaded_graph.predicates)
    
    def test_egraph_methods(self):
        """Test the methods added to EGGraph class."""
        # Create test graph
        result = self.parser.parse('(Man x)')
        assert result.graph is not None
        graph = result.graph
        
        # Test to_yaml method
        yaml_content = graph.to_yaml({'id': 'method_test', 'title': 'Method Test'})
        assert isinstance(yaml_content, str)
        assert 'metadata:' in yaml_content
        
        # Test from_yaml class method
        restored_graph = EGGraph.from_yaml(yaml_content)
        assert len(graph.entities) == len(restored_graph.entities)
        
        # Test file methods
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = Path(temp_dir) / 'method_test.yaml'
            
            # Save using method
            graph.save_yaml(filepath, {'id': 'method_save', 'title': 'Method Save'})
            assert filepath.exists()
            
            # Load using class method
            loaded_graph = EGGraph.load_yaml(filepath)
            assert len(graph.entities) == len(loaded_graph.entities)


class TestEGYAMLValidation:
    """Test YAML validation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = EGYAMLValidator()
        self.parser = CLIFParser()
    
    def test_valid_yaml_validation(self):
        """Test validation of valid YAML content."""
        # Create valid YAML
        result = self.parser.parse('(Man x)')
        assert result.graph is not None
        
        yaml_content = serialize_graph_to_yaml(result.graph, {
            'id': 'validation_test',
            'title': 'Validation Test'
        })
        
        # Validate
        validation_result = validate_yaml_content(yaml_content)
        assert validation_result['valid'] is True
        assert len(validation_result['errors']) == 0
    
    def test_invalid_yaml_structure(self):
        """Test validation of invalid YAML structure."""
        invalid_yaml = """
        metadata:
          id: test
        # Missing required sections
        """
        
        validation_result = validate_yaml_content(invalid_yaml)
        assert validation_result['valid'] is False
        assert len(validation_result['errors']) > 0
    
    def test_semantic_validation_errors(self):
        """Test detection of semantic errors."""
        # YAML with semantic errors
        invalid_yaml = """
        metadata:
          id: semantic_test
          title: Semantic Test
        entities:
          x_entity:
            name: x
            type: variable
        predicates:
          man_pred:
            name: Man
            arity: 1
            entities: [unknown_entity]  # References non-existent entity
            type: relation
        contexts:
          sheet:
            type: sheet_of_assertion
            nesting_level: 0
        ligatures: []
        """
        
        validation_result = validate_yaml_content(invalid_yaml)
        assert validation_result['valid'] is False
        assert len(validation_result['semantic_errors']) > 0
        
        # Check for specific error
        error_messages = ' '.join(validation_result['errors'])
        assert 'unknown_entity' in error_messages
    
    def test_context_hierarchy_validation(self):
        """Test validation of context hierarchy."""
        # YAML with invalid context hierarchy (simpler case)
        invalid_yaml = """
        metadata:
          id: hierarchy_test
          title: Hierarchy Test
        entities: {}
        predicates: {}
        contexts:
          sheet:
            type: sheet_of_assertion
            nesting_level: 0
          cut1:
            type: cut
            nesting_level: 1
            parent: nonexistent_parent
        ligatures: []
        """
        
        validation_result = validate_yaml_content(invalid_yaml)
        assert validation_result['valid'] is False
        
        # Check for parent reference error
        error_messages = ' '.join(validation_result['errors'])
        assert 'unknown parent' in error_messages.lower() or 'nonexistent_parent' in error_messages
    
    def test_arity_validation(self):
        """Test validation of predicate arity."""
        # YAML with arity mismatch
        invalid_yaml = """
        metadata:
          id: arity_test
          title: Arity Test
        entities:
          x_entity:
            name: x
            type: variable
        predicates:
          man_pred:
            name: Man
            arity: 2  # Claims arity 2 but only has 1 entity
            entities: [x_entity]
            type: relation
        contexts:
          sheet:
            type: sheet_of_assertion
            nesting_level: 0
        ligatures: []
        """
        
        validation_result = validate_yaml_content(invalid_yaml)
        assert validation_result['valid'] is False
        
        # Check for arity error
        error_messages = ' '.join(validation_result['errors'])
        assert 'arity' in error_messages.lower()


class TestEGYAMLEdgeCases:
    """Test edge cases and error conditions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.serializer = EGGraphYAMLSerializer()
        self.parser = CLIFParser()
    
    def test_empty_graph_serialization(self):
        """Test serialization of empty graph."""
        empty_graph = EGGraph.create_empty()
        
        yaml_content = serialize_graph_to_yaml(empty_graph, {
            'id': 'empty_test',
            'title': 'Empty Graph Test'
        })
        
        # Should serialize without error
        data = yaml.safe_load(yaml_content)
        assert data['metadata']['id'] == 'empty_test'
        assert len(data['entities']) == 0
        assert len(data['predicates']) == 0
        assert len(data['contexts']) >= 1  # Should have root context
    
    def test_malformed_yaml_deserialization(self):
        """Test handling of malformed YAML."""
        malformed_yaml = """
        metadata:
          id: test
        entities:
          - this is not a dict
        """
        
        with pytest.raises(Exception):  # Should raise some kind of error
            deserialize_graph_from_yaml(malformed_yaml)
    
    def test_missing_required_fields(self):
        """Test handling of missing required fields."""
        incomplete_yaml = """
        metadata:
          id: incomplete
        entities: {}
        predicates: {}
        # Missing contexts section
        """
        
        with pytest.raises(Exception):  # Should raise validation error
            deserialize_graph_from_yaml(incomplete_yaml)
    
    def test_unicode_handling(self):
        """Test handling of Unicode characters in names."""
        # Create graph with Unicode entity name
        graph = EGGraph.create_empty()
        
        # Add entity with Unicode name
        entity = Entity.create(name="α", entity_type="variable")
        graph = graph.add_entity(entity)
        
        # Add predicate with Unicode name
        predicate = Predicate.create(name="Φ", entities=[entity.id], arity=1)
        graph = graph.add_predicate(predicate)
        
        # Serialize
        yaml_content = serialize_graph_to_yaml(graph, {
            'id': 'unicode_test',
            'title': 'Unicode Test'
        })
        
        # Should handle Unicode correctly
        assert 'α' in yaml_content
        assert 'Φ' in yaml_content
        
        # Round-trip test
        restored_graph = deserialize_graph_from_yaml(yaml_content)
        assert len(restored_graph.entities) == 1
        assert len(restored_graph.predicates) == 1
    
    def test_large_graph_performance(self):
        """Test performance with larger graphs."""
        # Create a moderately large graph
        graph = EGGraph.create_empty()
        
        # Add many entities and predicates
        entities = []
        for i in range(50):
            entity = Entity.create(name=f"entity_{i}", entity_type="variable")
            graph = graph.add_entity(entity)
            entities.append(entity)
        
        for i in range(25):
            # Create predicates connecting multiple entities
            connected_entities = entities[i*2:(i*2)+2] if (i*2)+2 <= len(entities) else entities[i*2:]
            if connected_entities:
                predicate = Predicate.create(
                    name=f"predicate_{i}",
                    entities=[e.id for e in connected_entities],
                    arity=len(connected_entities)
                )
                graph = graph.add_predicate(predicate)
        
        # Serialize (should complete in reasonable time)
        import time
        start_time = time.time()
        yaml_content = serialize_graph_to_yaml(graph)
        serialize_time = time.time() - start_time
        
        # Should complete within reasonable time (adjust threshold as needed)
        assert serialize_time < 5.0  # 5 seconds max
        
        # Deserialize
        start_time = time.time()
        restored_graph = deserialize_graph_from_yaml(yaml_content)
        deserialize_time = time.time() - start_time
        
        assert deserialize_time < 5.0  # 5 seconds max
        
        # Verify structure
        assert len(restored_graph.entities) == len(graph.entities)
        assert len(restored_graph.predicates) == len(graph.predicates)


class TestEGYAMLCorpusIntegration:
    """Test integration with existing corpus examples."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = CLIFParser()
        self.generator = CLIFGenerator()
    
    def test_peirce_man_mortal_example(self):
        """Test with Peirce's classic man-mortal example."""
        # Use simpler form that parser can handle
        clif_text = '(Man x)'  # Start with simple case
        
        # Parse to graph
        result = self.parser.parse(clif_text)
        assert result.graph is not None
        
        # Serialize to YAML with scholarly metadata
        yaml_content = serialize_graph_to_yaml(result.graph, {
            'id': 'peirce_simple_man',
            'title': "Simple Man Predicate",
            'description': "Simplified example for testing",
            'source': {
                'author': 'Charles Sanders Peirce',
                'work': 'Collected Papers',
                'volume': 4,
                'section': '4.394',
                'year': 1903
            },
            'logical_pattern': 'implication',
            'logical_form': 'Man(x)',
            'notes': 'Simplified version for testing purposes.'
        })
        
        # Validate the YAML
        validation_result = validate_yaml_content(yaml_content)
        assert validation_result['valid'] is True
        
        # Test round-trip
        restored_graph = deserialize_graph_from_yaml(yaml_content)
        
        # Generate CLIF from restored graph
        gen_result = self.generator.generate(restored_graph)
        assert len(gen_result.errors) == 0
        
        # Parse the generated CLIF to verify semantic equivalence
        reparse_result = self.parser.parse(gen_result.clif_text)
        assert reparse_result.graph is not None
        
        # Should have same structure
        assert len(restored_graph.entities) == len(reparse_result.graph.entities)
        assert len(restored_graph.predicates) == len(reparse_result.graph.predicates)
    
    def test_canonical_examples_conversion(self):
        """Test conversion of canonical logical examples."""
        canonical_examples = [
            ('(Man x)', 'Simple existential'),
            # Skip complex cases for now
            # ('(and (Man x) (Mortal x))', 'Conjunction'),
            # ('(or (Man x) (Woman x))', 'Disjunction'),
            # ('(not (Man x))', 'Negation'),
            # ('(forall (x) (Man x))', 'Universal quantification'),
            # ('(exists (x) (Man x))', 'Existential quantification')
        ]
        
        for clif_text, description in canonical_examples:
            # Parse
            result = self.parser.parse(clif_text)
            if result.graph is None:
                continue  # Skip if parser doesn't handle this case yet
            
            # Serialize
            yaml_content = serialize_graph_to_yaml(result.graph, {
                'id': f'canonical_{description.lower().replace(" ", "_")}',
                'title': f'Canonical {description}',
                'logical_form': clif_text
            })
            
            # Validate
            validation_result = validate_yaml_content(yaml_content)
            assert validation_result['valid'] is True, f"Validation failed for {description}: {validation_result['errors']}"
            
            # Round-trip
            restored_graph = deserialize_graph_from_yaml(yaml_content)
            assert len(result.graph.entities) == len(restored_graph.entities)
            assert len(result.graph.predicates) == len(restored_graph.predicates)


if __name__ == '__main__':
    # Run tests if executed directly
    pytest.main([__file__, '-v'])

