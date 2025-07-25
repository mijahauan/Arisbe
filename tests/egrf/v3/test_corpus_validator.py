"""
Tests for the EGRF v3.0 corpus validator.
"""

import os
import json
import unittest
from unittest.mock import patch, mock_open, MagicMock

from egrf.v3.corpus_validator import (
    CorpusExample,
    CorpusLoader,
    EGRFValidator,
    validate_corpus
)


class TestCorpusExample(unittest.TestCase):
    """Tests for the CorpusExample class."""
    
    def test_from_index_entry(self):
        """Test creating a corpus example from an index entry."""
        # Mock file operations
        mock_metadata = '{"id": "test_example", "description": "Test example"}'
        mock_eg_hg = '# EG-HG representation'
        mock_clif = '(cl:text (P))'
        mock_egrf = '{"metadata": {"id": "test_example"}}'
        mock_index = '{"examples": [{"id": "test_example", "category": "test", "path": "test/test_example"}]}'
        
        mock_files = {
            '/corpus/corpus_index.json': mock_index,
            '/corpus/test/test_example.json': mock_metadata,
            '/corpus/test/test_example.eg-hg': mock_eg_hg,
            '/corpus/test/test_example.clif': mock_clif,
            '/corpus/test/test_example.egrf': mock_egrf
        }
        
        def mock_open_file(filename, mode='r'):
            if filename in mock_files:
                file_mock = mock_open(read_data=mock_files[filename]).return_value
                file_mock.__enter__.return_value = file_mock
                return file_mock
            raise FileNotFoundError(f"File not found: {filename}")
        
        def mock_json_load(f):
            # Try to get content based on what was opened
            content = f.read()
            return json.loads(content)
        
        with patch('builtins.open', mock_open_file), \
             patch('os.path.exists', lambda path: path in mock_files), \
             patch('json.load', mock_json_load):
            
            entry = {
                "id": "test_example",
                "category": "test",
                "path": "test/test_example"
            }
            
            example = CorpusExample.from_index_entry(entry, '/corpus')
            
            self.assertEqual(example.id, "test_example")
            self.assertEqual(example.metadata["id"], "test_example")
            self.assertEqual(example.eg_hg_data, mock_eg_hg)
            self.assertEqual(example.clif_data, mock_clif)
            # Parse the JSON string to a dictionary for comparison
            self.assertEqual(json.loads(mock_egrf)["metadata"]["id"], "test_example")


class TestCorpusLoader(unittest.TestCase):
    """Tests for the CorpusLoader class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_index = {
            "version": "1.0.0",
            "examples": [
                {
                    "id": "example1",
                    "category": "test",
                    "path": "test/example1"
                },
                {
                    "id": "example2",
                    "category": "test",
                    "path": "test/example2"
                }
            ]
        }
    
    def test_load_all_examples(self):
        """Test loading all examples from the corpus."""
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=json.dumps(self.mock_index))), \
             patch('json.load', return_value=self.mock_index), \
             patch('src.egrf.v3.corpus_validator.CorpusExample.from_index_entry') as mock_from_index:
            
            mock_from_index.side_effect = lambda entry, root: CorpusExample(
                id=entry["id"],
                category=entry["category"],
                path=entry["path"],
                metadata={"id": entry["id"]}
            )
            
            loader = CorpusLoader('/corpus')
            examples = loader.load_all_examples()
            
            self.assertEqual(len(examples), 2)
            self.assertIn("example1", examples)
            self.assertIn("example2", examples)
            self.assertEqual(examples["example1"].id, "example1")
            self.assertEqual(examples["example2"].id, "example2")
    
    def test_load_example(self):
        """Test loading a specific example from the corpus."""
        with patch('src.egrf.v3.corpus_validator.load_corpus_index', return_value=self.mock_index), \
             patch('src.egrf.v3.corpus_validator.CorpusExample.from_index_entry') as mock_from_index:

            mock_from_index.return_value = CorpusExample(
                id="example1",
                category="test",
                path="test/example1",
                metadata={"id": "example1"},
                eg_hg="# EG-HG representation",
                clif="(cl:text (P))",
                egrf={"metadata": {"id": "example1"}}
            )

            loader = CorpusLoader('/corpus')
            example = loader.load_example("example1")

            self.assertIsNotNone(example)
            self.assertEqual(example.id, "example1")
            
        # Test loading non-existent example
        with patch('src.egrf.v3.corpus_validator.load_corpus_index', return_value=self.mock_index):
            loader = CorpusLoader('/corpus')
            with self.assertRaises(ValueError) as context:
                loader.load_example("non_existent")
            
            self.assertIn("not found in corpus index", str(context.exception))
    
    def test_get_examples_by_category(self):
        """Test getting examples by category."""
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=json.dumps(self.mock_index))), \
             patch('json.load', return_value=self.mock_index), \
             patch('src.egrf.v3.corpus_validator.CorpusExample.from_index_entry') as mock_from_index:
            
            mock_from_index.side_effect = lambda entry, root: CorpusExample(
                id=entry["id"],
                category=entry["category"],
                path=entry["path"],
                metadata={"id": entry["id"]}
            )
            
            loader = CorpusLoader('/corpus')
            examples = loader.get_examples_by_category("test")
            
            self.assertEqual(len(examples), 2)
            self.assertEqual(examples[0].id, "example1")
            self.assertEqual(examples[1].id, "example2")
            
            # Test getting examples from non-existent category
            examples = loader.get_examples_by_category("non_existent")
            self.assertEqual(len(examples), 0)


class TestEGRFValidator(unittest.TestCase):
    """Tests for the EGRFValidator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = EGRFValidator()
        
        # Valid EGRF representation
        self.valid_egrf = {
            "metadata": {
                "id": "test_example",
                "version": "3.0.0",
                "description": "Test example"
            },
            "elements": {
                "sheet": {
                    "id": "sheet",
                    "type": "context",
                    "semantic_type": "sheet",
                    "nesting_level": 0
                },
                "outer_cut": {
                    "id": "outer_cut",
                    "type": "context",
                    "semantic_type": "cut",
                    "nesting_level": 1
                },
                "inner_cut": {
                    "id": "inner_cut",
                    "type": "context",
                    "semantic_type": "cut",
                    "nesting_level": 2
                },
                "p_predicate": {
                    "id": "p_predicate",
                    "type": "predicate",
                    "label": "P",
                    "arity": 0
                },
                "q_predicate": {
                    "id": "q_predicate",
                    "type": "predicate",
                    "label": "Q",
                    "arity": 0
                }
            },
            "containment": {
                "outer_cut": "sheet",
                "inner_cut": "outer_cut",
                "p_predicate": "outer_cut",
                "q_predicate": "inner_cut"
            },
            "connections": []
        }
        
        # Valid corpus example
        self.valid_example = CorpusExample(
            id="test_implication",
            category="test",
            path="test/test_implication",
            metadata={"id": "test_implication"},
            eg_hg="# EG-HG representation",
            clif="(cl:text (implies P Q))",
            egrf=self.valid_egrf
        )
    
    def test_validate_example(self):
        """Test validating a corpus example."""
        is_valid, errors = self.validator.validate_example(self.valid_example)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        
        # Test with missing EG-HG
        example = CorpusExample(
            id="test_example",
            category="test",
            path="test/test_example",
            metadata={"id": "test_example"},
            eg_hg=None,
            clif="(cl:text (P))",
            egrf=self.valid_egrf
        )
        
        is_valid, errors = self.validator.validate_example(example)
        self.assertFalse(is_valid)
        self.assertEqual(len(errors), 1)
        self.assertIn("Missing EG-HG", errors[0])
    
    def test_validate_egrf_structure(self):
        """Test validating EGRF structure."""
        errors = self.validator._validate_egrf_structure(self.valid_egrf)
        self.assertEqual(len(errors), 0)
        
        # Test with missing metadata
        egrf = {
            "elements": self.valid_egrf["elements"],
            "containment": self.valid_egrf["containment"]
        }
        
        errors = self.validator._validate_egrf_structure(egrf)
        self.assertEqual(len(errors), 1)
        self.assertIn("Missing required section: metadata", errors[0])
        
        # Test with missing sheet of assertion
        egrf = {
            "metadata": self.valid_egrf["metadata"],
            "elements": {
                "outer_cut": self.valid_egrf["elements"]["outer_cut"],
                "inner_cut": self.valid_egrf["elements"]["inner_cut"],
                "p_predicate": self.valid_egrf["elements"]["p_predicate"],
                "q_predicate": self.valid_egrf["elements"]["q_predicate"]
            },
            "containment": self.valid_egrf["containment"]
        }
        
        errors = self.validator._validate_egrf_structure(egrf)
        self.assertEqual(len(errors), 1)
        self.assertIn("Missing sheet of assertion", errors[0])
    
    def test_check_circular_containment(self):
        """Test checking for circular containment."""
        # Valid containment
        containment = {
            "outer_cut": "sheet",
            "inner_cut": "outer_cut",
            "p_predicate": "outer_cut",
            "q_predicate": "inner_cut"
        }

        try:
            self.validator._check_circular_containment(containment)
        except ValueError:
            self.fail("_check_circular_containment raised ValueError unexpectedly!")

        # Circular containment
        containment = {
            "outer_cut": "sheet",
            "inner_cut": "outer_cut",
            "sheet": "inner_cut"  # Creates a cycle
        }

        with self.assertRaises(ValueError) as context:
            self.validator._check_circular_containment(containment)
        
        self.assertIn("Circular containment", str(context.exception))
    
    def test_validate_nesting_levels(self):
        """Test validating nesting levels."""
        errors = self.validator._validate_nesting_levels(self.valid_egrf)
        self.assertEqual(len(errors), 0)
        
        # Test with incorrect nesting level
        egrf = dict(self.valid_egrf)
        egrf["elements"] = dict(self.valid_egrf["elements"])
        egrf["elements"]["inner_cut"] = dict(self.valid_egrf["elements"]["inner_cut"])
        egrf["elements"]["inner_cut"]["nesting_level"] = 3  # Should be 2
        
        errors = self.validator._validate_nesting_levels(egrf)
        self.assertEqual(len(errors), 1)
        self.assertIn("incorrect nesting_level", errors[0])
    
    def test_validate_implication_structure(self):
        """Test validating implication structure."""
        errors = self.validator._validate_implication_structure(self.valid_egrf)
        self.assertEqual(len(errors), 0)
        
        # Test with missing inner cut
        egrf = dict(self.valid_egrf)
        egrf["elements"] = dict(self.valid_egrf["elements"])
        egrf["containment"] = dict(self.valid_egrf["containment"])
        
        del egrf["elements"]["inner_cut"]
        del egrf["containment"]["inner_cut"]
        egrf["containment"]["q_predicate"] = "outer_cut"
        
        errors = self.validator._validate_implication_structure(egrf)
        self.assertEqual(len(errors), 1)
        self.assertIn("Missing inner cut", errors[0])
        
        # Test with missing antecedent
        egrf = dict(self.valid_egrf)
        egrf["elements"] = dict(self.valid_egrf["elements"])
        egrf["containment"] = dict(self.valid_egrf["containment"])
        
        del egrf["elements"]["p_predicate"]
        del egrf["containment"]["p_predicate"]
        
        errors = self.validator._validate_implication_structure(egrf)
        self.assertEqual(len(errors), 1)
        self.assertIn("Missing antecedent", errors[0])
    
    def test_validate_containment_hierarchy(self):
        """Test validating containment hierarchy."""
        errors = self.validator._validate_containment_hierarchy(self.valid_egrf)
        self.assertEqual(len(errors), 0)
        
        # Test with missing element
        egrf = dict(self.valid_egrf)
        egrf["elements"] = dict(self.valid_egrf["elements"])
        egrf["containment"] = dict(self.valid_egrf["containment"])
        
        egrf["containment"]["missing_element"] = "sheet"
        
        errors = self.validator._validate_containment_hierarchy(egrf)
        self.assertEqual(len(errors), 1)
        self.assertIn("not found in elements", errors[0])
        
        # Test with element missing container
        egrf = dict(self.valid_egrf)
        egrf["elements"] = dict(self.valid_egrf["elements"])
        egrf["containment"] = dict(self.valid_egrf["containment"])
        
        egrf["elements"]["orphan"] = {
            "id": "orphan",
            "type": "predicate",
            "label": "Orphan",
            "arity": 0
        }
        
        errors = self.validator._validate_containment_hierarchy(egrf)
        self.assertEqual(len(errors), 1)
        self.assertIn("has no container", errors[0])


class TestValidateCorpus(unittest.TestCase):
    """Tests for the validate_corpus function."""
    
    def test_validate_corpus(self):
        """Test validating the entire corpus."""
        with patch('src.egrf.v3.corpus_validator.CorpusLoader') as mock_loader:
            
            # Mock loader
            mock_loader_instance = MagicMock()
            mock_loader.return_value = mock_loader_instance
            
            # Mock get_example_ids method
            mock_loader_instance.get_example_ids.return_value = ["example1", "example2"]
            
            # Mock examples
            example1 = MagicMock()
            example1.id = "example1"
            example1.validate_all.return_value = (True, [])
            
            example2 = MagicMock()
            example2.id = "example2"
            example2.validate_all.return_value = (False, ["Error 1", "Error 2"])
            
            # Mock load_example method
            def mock_load_example(example_id):
                if example_id == "example1":
                    return example1
                elif example_id == "example2":
                    return example2
                
            mock_loader_instance.load_example.side_effect = mock_load_example
            
            valid_count, total_count, errors = validate_corpus('/corpus')
            
            self.assertEqual(valid_count, 1)
            self.assertEqual(total_count, 2)
            self.assertEqual(len(errors), 2)  # Two error messages from example2
            self.assertIn("example2: Error 1", errors)
            self.assertIn("example2: Error 2", errors)


if __name__ == '__main__':
    unittest.main()

