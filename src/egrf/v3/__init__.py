"""
EGRF v3.0 - Logical Containment Architecture

This module implements the logical containment architecture for EGRF v3.0,
providing platform-independent layout constraints and automatic sizing.

Core Modules:
- logical_types: Core data structures and constraints
- containment_hierarchy: Nesting relationships and validation  
- logical_generator: EG-HG → EGRF v3.0 conversion

Key Features:
- Logical containment instead of absolute coordinates
- Platform-independent constraints
- Auto-sizing from content
- User movement validation
- Cross-platform compatibility

Usage:
    from egrf.v3 import create_logical_predicate, LogicalContext
    
    predicate = create_logical_predicate(
        id="pred-1",
        name="Person", 
        container="sheet_of_assertion"
    )
"""

from .logical_types import (
    # Basic types
    LogicalPoint, LogicalSize, LogicalBounds, SpacingConstraint,
    
    # Constraint types
    PositioningType, ContainerType, SizeConstraints, SpacingConstraints,
    MovementConstraints, LayoutConstraints, ContainmentRelationship,
    
    # Element types
    LogicalProperties, LogicalElement, PredicateProperties, LogicalPredicate,
    EntityProperties, PathConstraints, ConnectionPoint, LogicalEntity,
    ContextProperties, LogicalContext,
    
    # Ligature types
    CutCrossing, LigatureConstraints, LogicalLigature,
    
    # Factory functions
    create_logical_predicate, create_logical_context, create_logical_entity
)

__version__ = "3.0.0-dev"

__all__ = [
    # Basic types
    'LogicalPoint', 'LogicalSize', 'LogicalBounds', 'SpacingConstraint',
    
    # Constraint types
    'PositioningType', 'ContainerType', 'SizeConstraints', 'SpacingConstraints',
    'MovementConstraints', 'LayoutConstraints', 'ContainmentRelationship',
    
    # Element types
    'LogicalProperties', 'LogicalElement', 'PredicateProperties', 'LogicalPredicate',
    'EntityProperties', 'PathConstraints', 'ConnectionPoint', 'LogicalEntity',
    'ContextProperties', 'LogicalContext',
    
    # Ligature types
    'CutCrossing', 'LigatureConstraints', 'LogicalLigature',
    
    # Factory functions
    'create_logical_predicate', 'create_logical_context', 'create_logical_entity'
]

