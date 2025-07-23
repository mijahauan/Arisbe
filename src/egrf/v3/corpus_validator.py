"""
EGRF v3.0 Corpus Validator.

This module provides tools for validating the EGRF v3.0 corpus examples against
the EG-HG and CLIF representations to ensure logical correctness.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class CorpusExample:
    """Represents a corpus example with all its representations."""
    
    id: str
    category: str
    path: str
    metadata: Dict[str, Any]
    eg_hg: Optional[str] = None
    clif: Optional[str] = None
    egrf: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_index_entry(cls, entry: Dict[str, Any], corpus_root: str) -> 'CorpusExample':
        """Create a corpus example from an index entry.
        
        Args:
            entry: Dictionary with id, category, and path.
            corpus_root: Root directory of the corpus.
            
        Returns:
            New corpus example.
        """
        example_id = entry["id"]
        category = entry["category"]
        path = entry["path"]
        
        # Load metadata
        metadata_path = os.path.join(corpus_root, f"{path}.json")
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Create example
        example = cls(
            id=example_id,
            category=category,
            path=path,
            metadata=metadata
        )
        
        # Load EG-HG if available
        eg_hg_path = os.path.join(corpus_root, f"{path}.eg-hg")
        if os.path.exists(eg_hg_path):
            with open(eg_hg_path, 'r') as f:
                example.eg_hg = f.read()
        
        # Load CLIF if available
        clif_path = os.path.join(corpus_root, f"{path}.clif")
        if os.path.exists(clif_path):
            with open(clif_path, 'r') as f:
                example.clif = f.read()
        
        # Load EGRF if available
        egrf_path = os.path.join(corpus_root, f"{path}.egrf")
        if os.path.exists(egrf_path):
            with open(egrf_path, 'r') as f:
                example.egrf = json.load(f)
        
        return example


class CorpusLoader:
    """Loads and manages the corpus examples."""
    
    def __init__(self, corpus_root: str):
        """Initialize the corpus loader.
        
        Args:
            corpus_root: Root directory of the corpus.
        """
        self.corpus_root = corpus_root
        self.examples = {}
        self.index = None
        
        # Load the corpus index
        index_path = os.path.join(corpus_root, "corpus_index.json")
        if os.path.exists(index_path):
            with open(index_path, 'r') as f:
                self.index = json.load(f)
        else:
            logger.error(f"Corpus index not found at {index_path}")
    
    def load_all_examples(self) -> Dict[str, CorpusExample]:
        """Load all examples from the corpus.
        
        Returns:
            Dictionary of corpus examples by ID.
        """
        if not self.index:
            logger.error("Corpus index not loaded")
            return {}
        
        for entry in self.index["examples"]:
            example_id = entry["id"]
            try:
                example = CorpusExample.from_index_entry(entry, self.corpus_root)
                self.examples[example_id] = example
            except Exception as e:
                logger.error(f"Error loading example {example_id}: {e}")
        
        return self.examples
    
    def load_example(self, example_id: str) -> Optional[CorpusExample]:
        """Load a specific example from the corpus.
        
        Args:
            example_id: ID of the example to load.
            
        Returns:
            Corpus example, or None if not found.
        """
        if not self.index:
            logger.error("Corpus index not loaded")
            return None
        
        for entry in self.index["examples"]:
            if entry["id"] == example_id:
                try:
                    example = CorpusExample.from_index_entry(entry, self.corpus_root)
                    self.examples[example_id] = example
                    return example
                except Exception as e:
                    logger.error(f"Error loading example {example_id}: {e}")
                    return None
        
        logger.error(f"Example {example_id} not found in corpus index")
        return None
    
    def get_examples_by_category(self, category: str) -> List[CorpusExample]:
        """Get all examples in a specific category.
        
        Args:
            category: Category to filter by.
            
        Returns:
            List of corpus examples in the category.
        """
        if not self.examples:
            self.load_all_examples()
        
        return [example for example in self.examples.values() if example.category == category]


class EGRFValidator:
    """Validates EGRF v3.0 examples against EG-HG and CLIF representations."""
    
    def __init__(self):
        """Initialize the EGRF validator."""
        pass
    
    def validate_example(self, example: CorpusExample) -> Tuple[bool, List[str]]:
        """Validate a corpus example.
        
        Args:
            example: Corpus example to validate.
            
        Returns:
            Tuple of (is_valid, error_messages).
        """
        errors = []
        
        # Check if all required files are present
        if not example.eg_hg:
            errors.append(f"Missing EG-HG representation for {example.id}")
        
        if not example.clif:
            errors.append(f"Missing CLIF representation for {example.id}")
        
        if not example.egrf:
            errors.append(f"Missing EGRF representation for {example.id}")
        
        # If any required file is missing, return early
        if errors:
            return False, errors
        
        # Validate EGRF structure
        egrf_errors = self._validate_egrf_structure(example.egrf)
        errors.extend(egrf_errors)
        
        # Validate logical consistency
        consistency_errors = self._validate_logical_consistency(example)
        errors.extend(consistency_errors)
        
        # Validate containment hierarchy
        containment_errors = self._validate_containment_hierarchy(example.egrf)
        errors.extend(containment_errors)
        
        return len(errors) == 0, errors
    
    def _validate_egrf_structure(self, egrf: Dict[str, Any]) -> List[str]:
        """Validate the structure of an EGRF representation.
        
        Args:
            egrf: EGRF representation.
            
        Returns:
            List of error messages.
        """
        errors = []
        
        # Check required sections
        required_sections = ["metadata", "elements", "containment"]
        for section in required_sections:
            if section not in egrf:
                errors.append(f"Missing required section: {section}")
        
        # If any required section is missing, return early
        if errors:
            return errors
        
        # Check metadata
        required_metadata = ["id", "version", "description"]
        for field in required_metadata:
            if field not in egrf["metadata"]:
                errors.append(f"Missing required metadata field: {field}")
        
        # Check elements
        if not egrf["elements"]:
            errors.append("Elements section is empty")
        else:
            # Check for sheet of assertion
            sheet_found = False
            for element_id, element in egrf["elements"].items():
                if element.get("type") == "context" and element.get("semantic_type") == "sheet":
                    sheet_found = True
                    break
            
            if not sheet_found:
                errors.append("Missing sheet of assertion")
            
            # Check element types
            for element_id, element in egrf["elements"].items():
                if "type" not in element:
                    errors.append(f"Element {element_id} missing type")
                elif element["type"] not in ["context", "predicate", "entity"]:
                    errors.append(f"Element {element_id} has invalid type: {element['type']}")
        
        # Check containment
        if not egrf["containment"]:
            errors.append("Containment section is empty")
        else:
            # Check for circular containment
            try:
                self._check_circular_containment(egrf["containment"])
            except ValueError as e:
                errors.append(str(e))
        
        return errors
    
    def _check_circular_containment(self, containment: Dict[str, str]) -> None:
        """Check for circular containment relationships.
        
        Args:
            containment: Dictionary mapping element IDs to container IDs.
            
        Raises:
            ValueError: If circular containment is detected.
        """
        visited = set()
        path = []
        
        def dfs(element_id):
            if element_id in path:
                cycle = path[path.index(element_id):] + [element_id]
                raise ValueError(f"Circular containment detected: {' -> '.join(cycle)}")
            
            if element_id in visited:
                return
            
            visited.add(element_id)
            path.append(element_id)
            
            container_id = containment.get(element_id)
            if container_id:
                dfs(container_id)
            
            path.pop()
        
        for element_id in containment:
            if element_id not in visited:
                dfs(element_id)
    
    def _validate_logical_consistency(self, example: CorpusExample) -> List[str]:
        """Validate the logical consistency of an example.
        
        Args:
            example: Corpus example to validate.
            
        Returns:
            List of error messages.
        """
        errors = []
        
        # Check nesting levels
        nesting_errors = self._validate_nesting_levels(example.egrf)
        errors.extend(nesting_errors)
        
        # Check double-cut implication structure
        if "implication" in example.id.lower():
            implication_errors = self._validate_implication_structure(example.egrf)
            errors.extend(implication_errors)
        
        return errors
    
    def _validate_nesting_levels(self, egrf: Dict[str, Any]) -> List[str]:
        """Validate the nesting levels in an EGRF representation.
        
        Args:
            egrf: EGRF representation.
            
        Returns:
            List of error messages.
        """
        errors = []
        
        # Build containment tree
        containment_tree = {}
        for element_id, container_id in egrf["containment"].items():
            if container_id not in containment_tree:
                containment_tree[container_id] = []
            containment_tree[container_id].append(element_id)
        
        # Find root (sheet of assertion)
        root = None
        for element_id, element in egrf["elements"].items():
            if element.get("type") == "context" and element.get("semantic_type") == "sheet":
                root = element_id
                break
        
        if not root:
            return ["Missing sheet of assertion"]
        
        # Calculate expected nesting levels
        expected_levels = {}
        
        def calculate_levels(element_id, level):
            expected_levels[element_id] = level
            for child_id in containment_tree.get(element_id, []):
                calculate_levels(child_id, level + 1)
        
        calculate_levels(root, 0)
        
        # Check nesting levels
        for element_id, element in egrf["elements"].items():
            if element.get("type") == "context":
                if "nesting_level" not in element:
                    errors.append(f"Context {element_id} missing nesting_level")
                elif element_id in expected_levels and element["nesting_level"] != expected_levels[element_id]:
                    errors.append(f"Context {element_id} has incorrect nesting_level: {element['nesting_level']} (expected {expected_levels[element_id]})")
        
        return errors
    
    def _validate_implication_structure(self, egrf: Dict[str, Any]) -> List[str]:
        """Validate the double-cut implication structure in an EGRF representation.
        
        Args:
            egrf: EGRF representation.
            
        Returns:
            List of error messages.
        """
        errors = []
        
        # Find sheet of assertion
        sheet = None
        for element_id, element in egrf["elements"].items():
            if element.get("type") == "context" and element.get("semantic_type") == "sheet":
                sheet = element_id
                break
        
        if not sheet:
            return ["Missing sheet of assertion"]
        
        # Find outer cut (directly contained in sheet)
        outer_cuts = []
        for element_id, container_id in egrf["containment"].items():
            if container_id == sheet and egrf["elements"].get(element_id, {}).get("type") == "context" and egrf["elements"].get(element_id, {}).get("semantic_type") == "cut":
                outer_cuts.append(element_id)
        
        if not outer_cuts:
            errors.append("Missing outer cut for implication")
            return errors
        
        if len(outer_cuts) > 1:
            errors.append(f"Multiple outer cuts found: {outer_cuts}")
            return errors
        
        outer_cut = outer_cuts[0]
        
        # Find inner cut (directly contained in outer cut)
        inner_cuts = []
        for element_id, container_id in egrf["containment"].items():
            if container_id == outer_cut and egrf["elements"].get(element_id, {}).get("type") == "context" and egrf["elements"].get(element_id, {}).get("semantic_type") == "cut":
                inner_cuts.append(element_id)
        
        if not inner_cuts:
            errors.append("Missing inner cut for implication")
            return errors
        
        if len(inner_cuts) > 1:
            errors.append(f"Multiple inner cuts found: {inner_cuts}")
            return errors
        
        inner_cut = inner_cuts[0]
        
        # Check for antecedent in outer cut
        antecedent_found = False
        for element_id, container_id in egrf["containment"].items():
            if container_id == outer_cut and egrf["elements"].get(element_id, {}).get("type") == "predicate":
                antecedent_found = True
                break
        
        if not antecedent_found:
            errors.append("Missing antecedent predicate in outer cut")
        
        # Check for consequent in inner cut
        consequent_found = False
        for element_id, container_id in egrf["containment"].items():
            if container_id == inner_cut and egrf["elements"].get(element_id, {}).get("type") == "predicate":
                consequent_found = True
                break
        
        if not consequent_found:
            errors.append("Missing consequent predicate in inner cut")
        
        return errors
    
    def _validate_containment_hierarchy(self, egrf: Dict[str, Any]) -> List[str]:
        """Validate the containment hierarchy in an EGRF representation.
        
        Args:
            egrf: EGRF representation.
            
        Returns:
            List of error messages.
        """
        errors = []
        
        # Check that all elements in containment have corresponding elements
        for element_id, container_id in egrf["containment"].items():
            if element_id not in egrf["elements"]:
                errors.append(f"Element {element_id} in containment not found in elements")
            
            if container_id not in egrf["elements"]:
                errors.append(f"Container {container_id} for element {element_id} not found in elements")
        
        # Check that all elements except sheet have a container
        for element_id, element in egrf["elements"].items():
            if element.get("type") == "context" and element.get("semantic_type") == "sheet":
                if element_id in egrf["containment"]:
                    errors.append(f"Sheet of assertion {element_id} should not have a container")
            elif element_id not in egrf["containment"]:
                errors.append(f"Element {element_id} has no container")
        
        return errors


def validate_corpus(corpus_root: str) -> Tuple[int, int, List[str]]:
    """Validate all examples in the corpus.
    
    Args:
        corpus_root: Root directory of the corpus.
        
    Returns:
        Tuple of (valid_count, total_count, error_messages).
    """
    loader = CorpusLoader(corpus_root)
    examples = loader.load_all_examples()
    
    validator = EGRFValidator()
    valid_count = 0
    total_count = len(examples)
    all_errors = []
    
    for example_id, example in examples.items():
        is_valid, errors = validator.validate_example(example)
        
        if is_valid:
            valid_count += 1
            logger.info(f"✅ {example_id}: Valid")
        else:
            error_message = f"❌ {example_id}: Invalid"
            logger.error(error_message)
            for error in errors:
                logger.error(f"  - {error}")
            all_errors.append(f"{error_message}: {', '.join(errors)}")
    
    return valid_count, total_count, all_errors


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        corpus_root = sys.argv[1]
    else:
        corpus_root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "corpus")
    
    valid_count, total_count, errors = validate_corpus(corpus_root)
    
    print(f"\nValidation complete: {valid_count}/{total_count} examples valid")
    
    if errors:
        print(f"\n{len(errors)} examples have errors:")
        for error in errors:
            print(f"  {error}")
        sys.exit(1)
    else:
        print("\nAll examples are valid!")
        sys.exit(0)

