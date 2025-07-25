"""
Arisbe: Existential Graphs Implementation

A comprehensive, academically rigorous implementation of Charles Sanders Peirce's 
Existential Graphs with full compliance to Frithjof Dau's formal mathematical framework.
"""

__version__ = "1.0.0-dau-compliant"
__author__ = "Arisbe Development Team"
__description__ = "Existential Graphs: A Dau-Compliant Implementation"

# Core exports for easy importing
from .eg_types import (
    Entity, Predicate, Context, Ligature,
    EntityId, PredicateId, ContextId, LigatureId,
    new_entity_id, new_predicate_id, new_context_id, new_ligature_id,
    EGError, EntityError, PredicateError, ContextError, LigatureError, ValidationError
)

from .graph import EGGraph
from .clif_parser import CLIFParser, CLIFParseResult
from .clif_generator import CLIFGenerator, CLIFGenerationResult
from .transformations import TransformationEngine
from .game_engine import EGGameEngine, EndoporeuticGameEngine

__all__ = [
    # Core types
    'Entity', 'Predicate', 'Context', 'Ligature',
    'EntityId', 'PredicateId', 'ContextId', 'LigatureId',
    'new_entity_id', 'new_predicate_id', 'new_context_id', 'new_ligature_id',
    
    # Main classes
    'EGGraph', 'CLIFParser', 'CLIFGenerator', 'TransformationEngine',
    'EGGameEngine', 'EndoporeuticGameEngine',
    
    # Result types
    'CLIFParseResult', 'CLIFGenerationResult',
    
    # Exceptions
    'EGError', 'EntityError', 'PredicateError', 'ContextError', 
    'LigatureError', 'ValidationError',
    
    # Package metadata
    '__version__', '__author__', '__description__'
]

