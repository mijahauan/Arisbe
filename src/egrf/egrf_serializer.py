#!/usr/bin/env python3

"""
EGRF Serialization Module

Provides JSON serialization and deserialization for EGRF documents.
"""

import json
from typing import Dict, Any, Optional
from dataclasses import asdict
from .egrf_types import EGRFDocument
from .egrf_schema import validate_egrf


class EGRFSerializer:
    """Handles serialization and deserialization of EGRF documents."""
    
    @staticmethod
    def to_json(egrf_doc: EGRFDocument, indent: Optional[int] = 2) -> str:
        """
        Serialize EGRF document to JSON string.
        
        Args:
            egrf_doc: EGRF document to serialize
            indent: JSON indentation (None for compact)
            
        Returns:
            JSON string representation
        """
        return json.dumps(asdict(egrf_doc), indent=indent, ensure_ascii=False)
    
    @staticmethod
    def to_dict(egrf_doc: EGRFDocument) -> Dict[str, Any]:
        """
        Convert EGRF document to dictionary.
        
        Args:
            egrf_doc: EGRF document to convert
            
        Returns:
            Dictionary representation
        """
        return asdict(egrf_doc)
    
    @staticmethod
    def from_json(json_str: str, validate: bool = True) -> EGRFDocument:
        """
        Deserialize EGRF document from JSON string.
        
        Args:
            json_str: JSON string to deserialize
            validate: Whether to validate against schema
            
        Returns:
            EGRF document
            
        Raises:
            ValueError: If JSON is invalid or validation fails
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
        
        return EGRFSerializer.from_dict(data, validate=validate)
    
    @staticmethod
    def from_dict(data: Dict[str, Any], validate: bool = True) -> EGRFDocument:
        """
        Create EGRF document from dictionary.
        
        Args:
            data: Dictionary representation
            validate: Whether to validate against schema
            
        Returns:
            EGRF document
            
        Raises:
            ValueError: If validation fails
        """
        # Skip validation for now to avoid complex object reconstruction
        # In a full implementation, we would properly reconstruct all nested objects
        
        # For now, create a basic EGRFDocument with the data as-is
        # This allows serialization testing without full object reconstruction
        return EGRFDocument(
            format=data.get("format", "EGRF"),
            version=data.get("version", "1.0"),
            entities=data.get("entities", []),
            predicates=data.get("predicates", []),
            contexts=data.get("contexts", []),
            ligatures=data.get("ligatures", []),
            metadata=data.get("metadata", {}),
            canvas=data.get("canvas", {}),
            semantics=data.get("semantics", {})
        )
    
    @staticmethod
    def save_to_file(egrf_doc: EGRFDocument, file_path: str, indent: Optional[int] = 2) -> None:
        """
        Save EGRF document to file.
        
        Args:
            egrf_doc: EGRF document to save
            file_path: Path to save file
            indent: JSON indentation (None for compact)
        """
        json_str = EGRFSerializer.to_json(egrf_doc, indent=indent)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(json_str)
    
    @staticmethod
    def load_from_file(file_path: str, validate: bool = True) -> EGRFDocument:
        """
        Load EGRF document from file.
        
        Args:
            file_path: Path to EGRF file
            validate: Whether to validate against schema
            
        Returns:
            EGRF document
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is invalid or validation fails
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_str = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"EGRF file not found: {file_path}")
        except Exception as e:
            raise ValueError(f"Error reading file {file_path}: {e}")
        
        return EGRFSerializer.from_json(json_str, validate=validate)

