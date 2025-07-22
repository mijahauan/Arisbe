"""
EGRF (Existential Graph Rendering Format) Module v3.0

This module provides functionality for converting between EG-HG data structures
and EGRF v3.0 format using logical containment architecture.

Key Components:
- v3.logical_types: Core logical data structures and constraints
- v3.containment_hierarchy: Nesting relationships and validation
- v3.logical_generator: EG-HG → EGRF v3.0 conversion

EGRF v3.0 Features:
- Logical containment instead of absolute coordinates
- Platform-independent layout constraints
- Auto-sizing from content
- User movement validation within logical bounds
- Cross-platform GUI compatibility

Usage:
    from egrf.v3 import create_logical_predicate, create_logical_context
    
    # Create logical elements
    predicate = create_logical_predicate(
        id="pred-1", 
        name="Person", 
        container="sheet_of_assertion"
    )
    
    context = create_logical_context(
        id="cut-1",
        name="Negation Cut", 
        container="sheet_of_assertion"
    )

Version History:
- v1.0.0: Absolute coordinate system (archived)
- v3.0.0: Logical containment architecture (current)
"""

# Import v3.0 logical types
try:
    from .v3.logical_types import (
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
    
except ImportError:
    # v3.0 modules not yet implemented
    __all__ = []

__version__ = "3.0.0-dev"
__author__ = "EG-HG Project"

# Legacy v1.0 compatibility note
def _show_migration_notice():
    """Show migration notice for v1.0 users."""
    print("""
    EGRF v3.0 Migration Notice:
    
    EGRF v3.0 introduces breaking changes with logical containment architecture.
    v1.0 absolute coordinate files are not compatible with v3.0.
    
    v1.0 implementation is preserved in:
    - Tag: v1.0.1
    - Branch: archive/egrf-v1.0-absolute-coordinates
    
    For v3.0 usage examples, see EGRF_Quick_Start_Tutorial.md
    """)

# Show migration notice on import (can be disabled by setting environment variable)
import os
if os.getenv('EGRF_HIDE_MIGRATION_NOTICE') != '1':
    _show_migration_notice()

