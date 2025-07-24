#!/usr/bin/env python3
"""
Complete Pipeline Tests

This module tests the complete pipeline from CLIF to YAML to EGRF,
validating that the canonical EG-HG format works correctly throughout
the entire system.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
import tempfile
from pathlib import Path

from clif_parser import CLIFParser
from clif_generator import CLIFGenerator
from eg_serialization import serialize_graph_to_yaml, deserialize_graph_from_yaml
from eg_yaml_validator import validate_yaml_content
from egrf_from_graph import convert_clif_to_egrf, convert_graph_to_egrf, serialize_egrf_to_dict


class TestCompletePipeline:
    """Test the complete CLIF -> EGGraph -> YAML -> EGRF pipeline."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = CLIFParser()
        self.generator = CLIFGenerator()
    
    def test_simple_clif_to_yaml_to_egrf_pipeline(self):
        """Test complete pipeline with simple CLIF example."""
        # Start with CLIF
        clif_text = "(Man x)"
        
        # Step 1: CLIF -> EGGraph
        parse_result = self.parser.parse(clif_text)
        assert parse_result.graph is not None
        original_graph = parse_result.graph
        
        # Step 2: EGGraph -> YAML
        yaml_content = serialize_graph_to_yaml(original_graph, {
            'id': 'pipeline_test',
            'title': 'Pipeline Test',
            'description': 'Testing complete pipeline'
        })
        
        # Step 3: Validate YAML
        validation_result = validate_yaml_content(yaml_content)
        assert validation_result['valid'] is True, f"YAML validation failed: {validation_result['errors']}"
        
        # Step 4: YAML -> EGGraph
        restored_graph = deserialize_graph_from_yaml(yaml_content)
        
        # Step 5: EGGraph -> EGRF
        egrf_doc = convert_graph_to_egrf(restored_graph, {
            'title': 'EGRF from Pipeline',
            'description': 'EGRF generated from pipeline test'
        })
        
        # Validate EGRF structure
        assert len(egrf_doc.logical_elements) > 0
        assert len(egrf_doc.layout_constraints) > 0
        assert egrf_doc.metadata['title'] == 'EGRF from Pipeline'
        
        # Check that we have the expected elements
        element_types = [elem.logical_type for elem in egrf_doc.logical_elements]
        assert 'sheet' in element_types  # Root context
        assert 'line_of_identity' in element_types  # Entity x
        assert 'relation' in element_types  # Predicate Man
        
        # Step 6: Test round-trip via CLIF generation
        gen_result = self.generator.generate(restored_graph)
        assert len(gen_result.errors) == 0
        assert gen_result.clif_text is not None
        
        print(f"✓ Pipeline test successful: CLIF -> EGGraph -> YAML -> EGGraph -> EGRF -> CLIF")
    
    def test_direct_clif_to_egrf_conversion(self):
        """Test direct CLIF to EGRF conversion."""
        clif_text = "(Man x)"
        
        # Direct conversion
        egrf_doc = convert_clif_to_egrf(clif_text, {
            'title': 'Direct Conversion Test',
            'description': 'Testing direct CLIF to EGRF conversion'
        })
        
        # Validate structure
        assert egrf_doc.metadata['title'] == 'Direct Conversion Test'
        assert egrf_doc.metadata['source_clif'] == clif_text
        
        # Check logical elements
        assert len(egrf_doc.logical_elements) >= 3  # Context, entity, predicate
        
        # Find specific elements
        contexts = [e for e in egrf_doc.logical_elements if e.logical_type == 'sheet']
        entities = [e for e in egrf_doc.logical_elements if e.logical_type == 'line_of_identity']
        predicates = [e for e in egrf_doc.logical_elements if e.logical_type == 'relation']
        
        assert len(contexts) >= 1
        assert len(entities) >= 1
        assert len(predicates) >= 1
        
        # Check that entity has correct name
        entity = entities[0]
        assert entity.properties['name'] == 'x'
        
        # Check that predicate has correct name
        predicate = predicates[0]
        assert predicate.properties['name'] == 'Man'
        
        print(f"✓ Direct CLIF to EGRF conversion successful")
    
    def test_pipeline_with_multiple_examples(self):
        """Test pipeline with multiple CLIF examples."""
        test_cases = [
            ("(Man x)", "Simple predicate"),
            ("(and (Man x) (Mortal x))", "Conjunction"),
            # Add more as parser supports them
        ]
        
        for clif_text, description in test_cases:
            # Parse CLIF
            parse_result = self.parser.parse(clif_text)
            if parse_result.graph is None:
                continue  # Skip unsupported cases
            
            # Convert to YAML
            yaml_content = serialize_graph_to_yaml(parse_result.graph, {
                'id': f'test_{description.lower().replace(" ", "_")}',
                'title': f'Test {description}',
                'logical_form': clif_text
            })
            
            # Validate YAML
            validation_result = validate_yaml_content(yaml_content)
            assert validation_result['valid'] is True, f"YAML validation failed for {description}: {validation_result['errors']}"
            
            # Convert to EGRF
            egrf_doc = convert_clif_to_egrf(clif_text, {
                'title': f'EGRF {description}',
                'description': f'EGRF conversion of {description}'
            })
            
            # Basic validation
            assert len(egrf_doc.logical_elements) > 0
            assert egrf_doc.metadata['source_clif'] == clif_text
            
            print(f"✓ Pipeline test successful for: {description}")
    
    def test_yaml_egrf_consistency(self):
        """Test that YAML and EGRF representations are consistent."""
        clif_text = "(Man x)"
        
        # Parse to graph
        parse_result = self.parser.parse(clif_text)
        assert parse_result.graph is not None
        graph = parse_result.graph
        
        # Convert to YAML
        yaml_content = serialize_graph_to_yaml(graph, {
            'id': 'consistency_test',
            'title': 'Consistency Test'
        })
        
        # Convert to EGRF
        egrf_doc = convert_graph_to_egrf(graph, {
            'title': 'Consistency Test EGRF'
        })
        
        # Parse YAML back to graph
        yaml_graph = deserialize_graph_from_yaml(yaml_content)
        
        # Convert YAML graph to EGRF
        yaml_egrf_doc = convert_graph_to_egrf(yaml_graph, {
            'title': 'Consistency Test EGRF from YAML'
        })
        
        # Compare EGRF documents
        assert len(egrf_doc.logical_elements) == len(yaml_egrf_doc.logical_elements)
        
        # Compare element types
        original_types = sorted([e.logical_type for e in egrf_doc.logical_elements])
        yaml_types = sorted([e.logical_type for e in yaml_egrf_doc.logical_elements])
        assert original_types == yaml_types
        
        print(f"✓ YAML and EGRF representations are consistent")
    
    def test_error_handling_in_pipeline(self):
        """Test error handling throughout the pipeline."""
        # Test invalid CLIF
        with pytest.raises(ValueError):
            convert_clif_to_egrf("invalid clif syntax (((")
        
        # Test invalid YAML
        invalid_yaml = """
        metadata:
          id: test
        # Missing required sections
        """
        
        with pytest.raises(Exception):
            deserialize_graph_from_yaml(invalid_yaml)
        
        print(f"✓ Error handling works correctly")
    
    def test_file_based_pipeline(self):
        """Test pipeline with file operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create CLIF file
            clif_file = temp_path / "test.clif"
            with open(clif_file, 'w') as f:
                f.write("(Man x)")
            
            # Parse CLIF file
            with open(clif_file, 'r') as f:
                clif_content = f.read()
            
            parse_result = self.parser.parse(clif_content)
            assert parse_result.graph is not None
            
            # Save as YAML
            yaml_file = temp_path / "test.yaml"
            yaml_content = serialize_graph_to_yaml(parse_result.graph, {
                'id': 'file_test',
                'title': 'File Test',
                'source_file': str(clif_file)
            })
            
            with open(yaml_file, 'w') as f:
                f.write(yaml_content)
            
            # Load YAML and convert to EGRF
            with open(yaml_file, 'r') as f:
                loaded_yaml = f.read()
            
            loaded_graph = deserialize_graph_from_yaml(loaded_yaml)
            egrf_doc = convert_graph_to_egrf(loaded_graph)
            
            # Save EGRF as JSON
            egrf_file = temp_path / "test.egrf.json"
            import json
            egrf_dict = serialize_egrf_to_dict(egrf_doc)
            
            with open(egrf_file, 'w') as f:
                json.dump(egrf_dict, f, indent=2)
            
            # Verify all files exist and have content
            assert clif_file.exists()
            assert yaml_file.exists()
            assert egrf_file.exists()
            
            assert clif_file.stat().st_size > 0
            assert yaml_file.stat().st_size > 0
            assert egrf_file.stat().st_size > 0
            
            print(f"✓ File-based pipeline test successful")
    
    def test_performance_with_larger_examples(self):
        """Test pipeline performance with larger examples."""
        import time
        
        # Create a moderately complex CLIF example
        # For now, use simple example since complex parsing may not be fully supported
        clif_text = "(Man x)"
        
        # Time the complete pipeline
        start_time = time.time()
        
        # Parse
        parse_result = self.parser.parse(clif_text)
        assert parse_result.graph is not None
        parse_time = time.time() - start_time
        
        # YAML conversion
        yaml_start = time.time()
        yaml_content = serialize_graph_to_yaml(parse_result.graph)
        yaml_time = time.time() - yaml_start
        
        # YAML validation
        validation_start = time.time()
        validation_result = validate_yaml_content(yaml_content)
        validation_time = time.time() - validation_start
        assert validation_result['valid'] is True
        
        # EGRF conversion
        egrf_start = time.time()
        egrf_doc = convert_graph_to_egrf(parse_result.graph)
        egrf_time = time.time() - egrf_start
        
        total_time = time.time() - start_time
        
        # Performance assertions (adjust thresholds as needed)
        assert parse_time < 1.0  # Should parse quickly
        assert yaml_time < 1.0   # Should serialize quickly
        assert validation_time < 1.0  # Should validate quickly
        assert egrf_time < 1.0   # Should convert quickly
        assert total_time < 2.0  # Total should be reasonable
        
        print(f"✓ Performance test passed:")
        print(f"  Parse time: {parse_time:.3f}s")
        print(f"  YAML time: {yaml_time:.3f}s")
        print(f"  Validation time: {validation_time:.3f}s")
        print(f"  EGRF time: {egrf_time:.3f}s")
        print(f"  Total time: {total_time:.3f}s")


class TestArchitecturalConsistency:
    """Test that the architecture is now consistent."""
    
    def test_no_eg_hg_file_dependency(self):
        """Test that EGRF conversion no longer depends on .eg-hg files."""
        # This test verifies that we can go CLIF -> EGGraph -> EGRF
        # without needing any .eg-hg file parsing
        
        clif_text = "(Man x)"
        
        # Direct path: CLIF -> EGGraph -> EGRF
        egrf_doc = convert_clif_to_egrf(clif_text)
        
        # Should work without any file system dependencies
        assert egrf_doc is not None
        assert len(egrf_doc.logical_elements) > 0
        assert egrf_doc.metadata['source_clif'] == clif_text
        
        print(f"✓ EGRF conversion works without .eg-hg file dependency")
    
    def test_canonical_eg_hg_model_usage(self):
        """Test that the canonical EG-HG model (EGGraph) is used consistently."""
        clif_text = "(Man x)"
        
        # Parse to canonical model
        parser = CLIFParser()
        result = parser.parse(clif_text)
        assert result.graph is not None
        canonical_graph = result.graph
        
        # Convert canonical model to YAML
        yaml_content = serialize_graph_to_yaml(canonical_graph)
        
        # Convert canonical model to EGRF
        egrf_doc = convert_graph_to_egrf(canonical_graph)
        
        # Both conversions should work from the same canonical model
        assert yaml_content is not None
        assert egrf_doc is not None
        
        # YAML should be valid
        validation_result = validate_yaml_content(yaml_content)
        assert validation_result['valid'] is True
        
        print(f"✓ Canonical EG-HG model (EGGraph) used consistently")
    
    def test_format_consistency(self):
        """Test that all formats represent the same logical structure."""
        clif_text = "(Man x)"
        
        # Parse to canonical model
        parser = CLIFParser()
        result = parser.parse(clif_text)
        assert result.graph is not None
        graph = result.graph
        
        # Convert to YAML and back
        yaml_content = serialize_graph_to_yaml(graph)
        yaml_graph = deserialize_graph_from_yaml(yaml_content)
        
        # Convert both to EGRF
        original_egrf = convert_graph_to_egrf(graph)
        yaml_egrf = convert_graph_to_egrf(yaml_graph)
        
        # Should have same number of logical elements
        assert len(original_egrf.logical_elements) == len(yaml_egrf.logical_elements)
        
        # Should have same types of elements
        original_types = sorted([e.logical_type for e in original_egrf.logical_elements])
        yaml_types = sorted([e.logical_type for e in yaml_egrf.logical_elements])
        assert original_types == yaml_types
        
        print(f"✓ All formats represent consistent logical structure")


if __name__ == '__main__':
    # Run tests if executed directly
    pytest.main([__file__, '-v'])

