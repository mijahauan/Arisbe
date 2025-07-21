#!/usr/bin/env python3

"""
EGRF Schema Validation Module

Provides JSON schema validation for EGRF documents to ensure format compliance
and logical consistency.
"""

import json
import os
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

try:
    import jsonschema
    from jsonschema import validate, ValidationError
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False


class EGRFSchemaValidator:
    """Validates EGRF documents against the JSON schema."""
    
    def __init__(self):
        self.schema = self._load_schema()
    
    def _load_schema(self) -> Dict[str, Any]:
        """Load the EGRF JSON schema."""
        schema_path = Path(__file__).parent / "egrf_schema.json"
        
        try:
            with open(schema_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"EGRF schema not found at {schema_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in EGRF schema: {e}")
    
    def validate(self, egrf_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate EGRF data against the schema.
        
        Args:
            egrf_data: EGRF document as dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not JSONSCHEMA_AVAILABLE:
            return True, "jsonschema not available - validation skipped"
        
        try:
            validate(instance=egrf_data, schema=self.schema)
            return True, None
        except ValidationError as e:
            return False, f"Schema validation error: {e.message}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def validate_file(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate an EGRF file against the schema.
        
        Args:
            file_path: Path to EGRF file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            with open(file_path, 'r') as f:
                egrf_data = json.load(f)
            return self.validate(egrf_data)
        except FileNotFoundError:
            return False, f"File not found: {file_path}"
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON in file: {e}"
        except Exception as e:
            return False, f"Error reading file: {str(e)}"
    
    def get_schema_version(self) -> str:
        """Get the schema version."""
        return self.schema.get("properties", {}).get("version", {}).get("enum", ["unknown"])[0]
    
    def get_required_fields(self) -> List[str]:
        """Get the list of required fields in EGRF documents."""
        return self.schema.get("required", [])


def validate_egrf(egrf_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Convenience function to validate EGRF data.
    
    Args:
        egrf_data: EGRF document as dictionary
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    validator = EGRFSchemaValidator()
    return validator.validate(egrf_data)


def validate_egrf_file(file_path: str) -> Tuple[bool, Optional[str]]:
    """
    Convenience function to validate an EGRF file.
    
    Args:
        file_path: Path to EGRF file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    validator = EGRFSchemaValidator()
    return validator.validate_file(file_path)

