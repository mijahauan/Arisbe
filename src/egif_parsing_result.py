#!/usr/bin/env python3
"""
EGIF Parsing Result - Preserves variable names for display without polluting Dau's formal model.

This module provides a clean separation between:
- Dau's formal EGI structure (pure logical model)
- Display metadata (variable names, parsing context)
"""

from dataclasses import dataclass
from typing import Dict
from egi_core_dau import RelationalGraphWithCuts, ElementID


@dataclass(frozen=True)
class EGIFParsingResult:
    """
    Result of EGIF parsing that preserves both the formal EGI and display metadata.
    
    This maintains Dau's pure formal model while providing the information needed
    for proper variable name display in renderers.
    """
    
    # Dau's formal EGI structure (6+1 components)
    egi: RelationalGraphWithCuts
    
    # Display metadata (not part of formal model)
    variable_names: Dict[ElementID, str]  # vertex_id -> original variable name (e.g., "x", "y")
    
    def get_display_name(self, vertex_id: ElementID) -> str:
        """
        Get the display name for a vertex.
        
        Returns:
        - Original variable name (e.g., "x", "y") for generic vertices
        - Constant value (e.g., "Socrates") for constant vertices
        - Fallback to vertex ID if no display name available
        """
        # Check if this is a constant vertex
        vertex = self.egi.get_vertex(vertex_id)
        if vertex and vertex.label:
            return vertex.label  # Constant vertex - show the constant value
        
        # Check for variable name
        if vertex_id in self.variable_names:
            return self.variable_names[vertex_id]  # Generic vertex - show variable name
        
        # Fallback to vertex ID
        return vertex_id
