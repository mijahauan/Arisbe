#!/usr/bin/env python3
"""
EG-HG YAML Validator

This module provides validation functionality for EG-HG YAML files using JSON Schema.
It ensures that YAML files conform to the canonical EG-HG format and contain
valid Existential Graph structures.
"""

import json
import yaml
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import jsonschema
from jsonschema import validate, ValidationError, Draft7Validator

from eg_types import ValidationError as EGValidationError


class EGYAMLValidationError(EGValidationError):
    """Exception raised for EG-HG YAML validation errors."""
    pass


class EGYAMLValidator:
    """
    Validator for EG-HG YAML files using JSON Schema.
    
    This class provides comprehensive validation of EG-HG YAML files,
    including schema validation, semantic consistency checks, and
    Existential Graph structure validation.
    """
    
    def __init__(self, schema_path: Optional[Union[str, Path]] = None):
        """
        Initialize the validator with a JSON Schema.
        
        Args:
            schema_path: Path to the JSON Schema file. If None, uses the default schema.
        """
        if schema_path is None:
            # Use the default schema from the same directory
            schema_path = Path(__file__).parent / "eg_yaml_schema.json"
        
        self.schema_path = Path(schema_path)
        self.schema = self._load_schema()
        self.validator = Draft7Validator(self.schema)
    
    def _load_schema(self) -> Dict[str, Any]:
        """Load the JSON Schema from file."""
        try:
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise EGYAMLValidationError(f"Schema file not found: {self.schema_path}")
        except json.JSONDecodeError as e:
            raise EGYAMLValidationError(f"Invalid JSON in schema file: {e}")
    
    def validate_yaml_content(self, yaml_content: str) -> Dict[str, Any]:
        """
        Validate YAML content against the EG-HG schema.
        
        Args:
            yaml_content: YAML string to validate
            
        Returns:
            Dictionary containing validation results
            
        Raises:
            EGYAMLValidationError: If validation fails
        """
        # Parse YAML
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise EGYAMLValidationError(f"Invalid YAML format: {e}")
        
        if data is None:
            raise EGYAMLValidationError("YAML content is empty")
        
        # Validate against schema
        schema_errors = self._validate_schema(data)
        
        # Perform semantic validation
        semantic_errors = self._validate_semantics(data)
        
        # Combine results
        all_errors = schema_errors + semantic_errors
        
        return {
            'valid': len(all_errors) == 0,
            'errors': all_errors,
            'schema_errors': schema_errors,
            'semantic_errors': semantic_errors,
            'data': data
        }
    
    def validate_yaml_file(self, filepath: Union[str, Path]) -> Dict[str, Any]:
        """
        Validate a YAML file against the EG-HG schema.
        
        Args:
            filepath: Path to the YAML file
            
        Returns:
            Dictionary containing validation results
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise EGYAMLValidationError(f"File not found: {filepath}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                yaml_content = f.read()
        except IOError as e:
            raise EGYAMLValidationError(f"Error reading file {filepath}: {e}")
        
        result = self.validate_yaml_content(yaml_content)
        result['filepath'] = str(filepath)
        
        return result
    
    def _validate_schema(self, data: Dict[str, Any]) -> List[str]:
        """Validate data against JSON Schema."""
        errors = []
        
        try:
            self.validator.validate(data)
        except ValidationError as e:
            # Convert jsonschema errors to readable format
            errors.append(self._format_schema_error(e))
            
            # Collect all errors, not just the first one
            for error in self.validator.iter_errors(data):
                if error != e:  # Avoid duplicate
                    errors.append(self._format_schema_error(error))
        
        return errors
    
    def _format_schema_error(self, error: ValidationError) -> str:
        """Format a JSON Schema validation error for readability."""
        path = " -> ".join(str(p) for p in error.absolute_path) if error.absolute_path else "root"
        return f"Schema error at {path}: {error.message}"
    
    def _validate_semantics(self, data: Dict[str, Any]) -> List[str]:
        """Validate semantic consistency of EG-HG data."""
        errors = []
        
        # Extract sections
        entities = data.get('entities', {})
        predicates = data.get('predicates', {})
        contexts = data.get('contexts', {})
        ligatures = data.get('ligatures', [])
        
        # Validate entity references in predicates
        errors.extend(self._validate_entity_references(entities, predicates))
        
        # Validate context references
        errors.extend(self._validate_context_references(contexts, entities, predicates))
        
        # Validate context hierarchy
        errors.extend(self._validate_context_hierarchy(contexts))
        
        # Validate ligature references
        errors.extend(self._validate_ligature_references(ligatures, entities, predicates))
        
        # Validate predicate arity consistency
        errors.extend(self._validate_predicate_arity(predicates))
        
        # Validate function predicates
        errors.extend(self._validate_function_predicates(predicates, entities))
        
        return errors
    
    def _validate_entity_references(self, entities: Dict[str, Any], 
                                   predicates: Dict[str, Any]) -> List[str]:
        """Validate that predicates reference existing entities."""
        errors = []
        
        for pred_name, pred_data in predicates.items():
            for entity_name in pred_data.get('entities', []):
                if entity_name not in entities:
                    errors.append(f"Predicate '{pred_name}' references unknown entity '{entity_name}'")
            
            # Check return entity for functions
            if pred_data.get('type') == 'function' and 'return_entity' in pred_data:
                return_entity = pred_data['return_entity']
                if return_entity not in entities:
                    errors.append(f"Function predicate '{pred_name}' references unknown return entity '{return_entity}'")
        
        return errors
    
    def _validate_context_references(self, contexts: Dict[str, Any], 
                                    entities: Dict[str, Any], 
                                    predicates: Dict[str, Any]) -> List[str]:
        """Validate context references in entities and predicates."""
        errors = []
        
        # Check entity context references
        for entity_name, entity_data in entities.items():
            if 'context' in entity_data:
                context_name = entity_data['context']
                if context_name not in contexts:
                    errors.append(f"Entity '{entity_name}' references unknown context '{context_name}'")
        
        # Check predicate context references
        for pred_name, pred_data in predicates.items():
            if 'context' in pred_data:
                context_name = pred_data['context']
                if context_name not in contexts:
                    errors.append(f"Predicate '{pred_name}' references unknown context '{context_name}'")
        
        # Check context containment references
        all_items = set(entities.keys()) | set(predicates.keys()) | set(contexts.keys())
        
        for context_name, context_data in contexts.items():
            for item_name in context_data.get('contains', []):
                if item_name not in all_items:
                    errors.append(f"Context '{context_name}' contains unknown item '{item_name}'")
        
        return errors
    
    def _validate_context_hierarchy(self, contexts: Dict[str, Any]) -> List[str]:
        """Validate the context hierarchy structure."""
        errors = []
        
        # Find root contexts (no parent)
        root_contexts = [name for name, data in contexts.items() 
                        if data.get('parent') is None]
        
        if len(root_contexts) == 0:
            errors.append("No root context found (context with no parent)")
        elif len(root_contexts) > 1:
            errors.append(f"Multiple root contexts found: {root_contexts}")
        
        # Check parent references
        for context_name, context_data in contexts.items():
            parent = context_data.get('parent')
            if parent is not None:
                if parent not in contexts:
                    errors.append(f"Context '{context_name}' references unknown parent '{parent}'")
                elif parent == context_name:
                    errors.append(f"Context '{context_name}' cannot be its own parent")
        
        # Check for cycles in hierarchy
        errors.extend(self._detect_context_cycles(contexts))
        
        # Validate nesting levels
        errors.extend(self._validate_nesting_levels(contexts))
        
        return errors
    
    def _detect_context_cycles(self, contexts: Dict[str, Any]) -> List[str]:
        """Detect cycles in the context hierarchy."""
        errors = []
        
        def has_cycle(context_name: str, visited: set, path: List[str]) -> bool:
            if context_name in visited:
                cycle_start = path.index(context_name)
                cycle = " -> ".join(path[cycle_start:] + [context_name])
                errors.append(f"Cycle detected in context hierarchy: {cycle}")
                return True
            
            if context_name not in contexts:
                return False
            
            visited.add(context_name)
            path.append(context_name)
            
            parent = contexts[context_name].get('parent')
            if parent is not None:
                if has_cycle(parent, visited, path):
                    return True
            
            visited.remove(context_name)
            path.pop()
            return False
        
        for context_name in contexts:
            has_cycle(context_name, set(), [])
        
        return errors
    
    def _validate_nesting_levels(self, contexts: Dict[str, Any]) -> List[str]:
        """Validate that nesting levels are consistent with hierarchy."""
        errors = []
        
        def get_expected_level(context_name: str) -> int:
            context_data = contexts.get(context_name)
            if not context_data:
                return -1
            
            parent = context_data.get('parent')
            if parent is None:
                return 0  # Root context
            else:
                parent_level = get_expected_level(parent)
                return parent_level + 1 if parent_level >= 0 else -1
        
        for context_name, context_data in contexts.items():
            declared_level = context_data.get('nesting_level', 0)
            expected_level = get_expected_level(context_name)
            
            if expected_level >= 0 and declared_level != expected_level:
                errors.append(f"Context '{context_name}' has nesting_level {declared_level} "
                            f"but should be {expected_level} based on hierarchy")
        
        return errors
    
    def _validate_ligature_references(self, ligatures: List[Dict[str, Any]], 
                                     entities: Dict[str, Any], 
                                     predicates: Dict[str, Any]) -> List[str]:
        """Validate ligature references to entities and predicates."""
        errors = []
        
        for i, ligature in enumerate(ligatures):
            # Check entity references
            for entity_name in ligature.get('entities', []):
                if entity_name not in entities:
                    errors.append(f"Ligature {i} references unknown entity '{entity_name}'")
            
            # Check predicate references
            for pred_name in ligature.get('predicates', []):
                if pred_name not in predicates:
                    errors.append(f"Ligature {i} references unknown predicate '{pred_name}'")
            
            # Check that ligature has at least some references
            entity_count = len(ligature.get('entities', []))
            predicate_count = len(ligature.get('predicates', []))
            
            if entity_count + predicate_count < 2:
                errors.append(f"Ligature {i} must connect at least 2 items")
        
        return errors
    
    def _validate_predicate_arity(self, predicates: Dict[str, Any]) -> List[str]:
        """Validate that predicate arity matches the number of entities."""
        errors = []
        
        for pred_name, pred_data in predicates.items():
            declared_arity = pred_data.get('arity', 0)
            actual_arity = len(pred_data.get('entities', []))
            
            if declared_arity != actual_arity:
                errors.append(f"Predicate '{pred_name}' declares arity {declared_arity} "
                            f"but has {actual_arity} entities")
        
        return errors
    
    def _validate_function_predicates(self, predicates: Dict[str, Any], 
                                     entities: Dict[str, Any]) -> List[str]:
        """Validate function predicate constraints."""
        errors = []
        
        for pred_name, pred_data in predicates.items():
            if pred_data.get('type') == 'function':
                # Functions should have a return entity
                if 'return_entity' not in pred_data:
                    errors.append(f"Function predicate '{pred_name}' missing return_entity")
                else:
                    return_entity = pred_data['return_entity']
                    
                    # Return entity should exist
                    if return_entity not in entities:
                        errors.append(f"Function predicate '{pred_name}' has unknown return_entity '{return_entity}'")
                    
                    # Return entity should not be in the entities list (it's the result, not an argument)
                    if return_entity in pred_data.get('entities', []):
                        errors.append(f"Function predicate '{pred_name}' has return_entity '{return_entity}' "
                                    f"also listed as an argument entity")
        
        return errors


# Convenience functions
def validate_yaml_content(yaml_content: str, schema_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Validate YAML content against the EG-HG schema.
    
    Args:
        yaml_content: YAML string to validate
        schema_path: Optional path to custom schema file
        
    Returns:
        Dictionary containing validation results
    """
    validator = EGYAMLValidator(schema_path)
    return validator.validate_yaml_content(yaml_content)


def validate_yaml_file(filepath: Union[str, Path], schema_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Validate a YAML file against the EG-HG schema.
    
    Args:
        filepath: Path to the YAML file
        schema_path: Optional path to custom schema file
        
    Returns:
        Dictionary containing validation results
    """
    validator = EGYAMLValidator(schema_path)
    return validator.validate_yaml_file(filepath)


def is_valid_yaml(yaml_content: str, schema_path: Optional[Union[str, Path]] = None) -> bool:
    """
    Check if YAML content is valid according to the EG-HG schema.
    
    Args:
        yaml_content: YAML string to validate
        schema_path: Optional path to custom schema file
        
    Returns:
        True if valid, False otherwise
    """
    try:
        result = validate_yaml_content(yaml_content, schema_path)
        return result['valid']
    except EGYAMLValidationError:
        return False


def is_valid_yaml_file(filepath: Union[str, Path], schema_path: Optional[Union[str, Path]] = None) -> bool:
    """
    Check if a YAML file is valid according to the EG-HG schema.
    
    Args:
        filepath: Path to the YAML file
        schema_path: Optional path to custom schema file
        
    Returns:
        True if valid, False otherwise
    """
    try:
        result = validate_yaml_file(filepath, schema_path)
        return result['valid']
    except EGYAMLValidationError:
        return False

