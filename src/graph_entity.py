"""
GraphEntity - DEPRECATED: Backward Compatibility Bridge

This module is DEPRECATED and maintained only for backward compatibility.
All new code should import from universe_of_discourse instead.

The fundamental entity in Arisbe is the Universe of Discourse (UoD),
not a static graph entity. This module provides compatibility aliases
to ease the transition.

Migration:
    OLD: from graph_entity import GraphEntity, EntityCategory, EntityMetadata
    NEW: from universe_of_discourse import UniverseOfDiscourse, UoDCategory, UoDMetadata

See: UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md for the philosophical foundation
"""

# Import everything from the new module
from universe_of_discourse import (
    # New names (recommended)
    UniverseOfDiscourse,
    UoDType,
    UoDCategory,
    UoDMetadata,
    
    # Backward compatibility aliases (deprecated, will be removed in future)
    GraphEntity,
    EntityType,
    EntityCategory,
    EntityMetadata,
)

# Re-export for backward compatibility
__all__ = [
    # New names
    'UniverseOfDiscourse',
    'UoDType',
    'UoDCategory',
    'UoDMetadata',
    
    # Old names (deprecated)
    'GraphEntity',
    'EntityType',
    'EntityCategory',
    'EntityMetadata',
]

# Deprecation notice for developers
import warnings

def _deprecation_warning():
    """Show deprecation warning when importing old names."""
    warnings.warn(
        "graph_entity module is deprecated. Use universe_of_discourse instead.\n"
        "See UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md for details.",
        DeprecationWarning,
        stacklevel=3
    )

# Uncomment this line to enable deprecation warnings during migration:
# _deprecation_warning()

# ===== END OF FILE =====
# Original implementation has been moved to universe_of_discourse.py
# This file now serves only as a backward compatibility bridge.
# After all code is migrated, this file can be removed entirely.
