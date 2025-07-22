"""
EGRF (Existential Graph Rendering Format) Module

This module provides functionality for converting between EG-CL-Manus2 data structures
and EGRF format, enabling visual representation of existential graphs while preserving
logical integrity.

Key Components:
- egrf_types: Core EGRF data structures and validation
- egrf_generator: EG-CL-Manus2 → EGRF conversion
- egrf_parser: EGRF → EG-CL-Manus2 conversion
- egrf_schema: JSON schema validation
- egrf_serializer: JSON serialization utilities

Usage:
    from egrf import EGRFGenerator, EGRFParser, EGRFDocument
    
    # Generate EGRF from EG-CL-Manus2
    generator = EGRFGenerator()
    egrf_doc = generator.generate(eg_graph)
    
    # Parse EGRF back to EG-CL-Manus2
    parser = EGRFParser()
    result = parser.parse(egrf_doc)
    if result.is_successful:
        reconstructed_graph = result.graph
"""

from .egrf_types import (
    EGRFDocument, Entity, Predicate, Context, 
    Point, Size, Connection, Label, Bounds,
    EntityVisual, PredicateVisual, ContextVisual, LigatureVisual,
    Stroke, Fill, Font, Canvas, Metadata, Semantics, Marker
)

# Import generator
from .egrf_generator import EGRFGenerator, LayoutConstraints

# Import parser
from .egrf_parser import EGRFParser, ParseResult, EGRFParseError, parse_egrf, parse_egrf_from_json, parse_egrf_from_file

# Import serialization
from .egrf_serializer import EGRFSerializer

__version__ = "1.0.0"
__author__ = "EG-CL-Manus2 Project"

__all__ = [
    # Core types
    'EGRFDocument', 'Entity', 'Predicate', 'Context',
    'Point', 'Size', 'Connection', 'Label', 'Bounds',
    'EntityVisual', 'PredicateVisual', 'ContextVisual', 'LigatureVisual',
    'Stroke', 'Fill', 'Font', 'Canvas', 'Metadata', 'Semantics', 'Marker',
    
    # Generator
    'EGRFGenerator', 'LayoutConstraints',
    
    # Parser
    'EGRFParser', 'ParseResult', 'EGRFParseError', 
    'parse_egrf', 'parse_egrf_from_json', 'parse_egrf_from_file',
    
    # Serialization
    'EGRFSerializer'
]

