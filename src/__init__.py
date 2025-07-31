"""
Arisbe: Dau-Compliant Existential Graphs System

A mathematically rigorous implementation of Peirce's Existential Graphs
based on Frithjof Dau's formal specification.

Main modules:
- egi_core_dau: Dau's 6+1 component model
- egif_parser_dau: EGIF parsing with isolated vertex support
- egif_generator_dau: EGIF generation with area/context distinction
- egi_transformations_dau: All 8 canonical transformation rules
- egi_cli_dau: Comprehensive command-line interface
"""

__version__ = "2.0.1"
__author__ = "Arisbe Development Team"
__description__ = "Dau-Compliant Existential Graphs System"

# Core exports
from egi_core_dau import (
    RelationalGraphWithCuts,
    Vertex, Edge, Cut, ElementID,
    create_vertex, create_edge, create_cut,
    create_empty_graph
)

from egif_parser_dau import parse_egif
from egif_generator_dau import generate_egif

from egi_transformations_dau import (
    apply_erasure, apply_insertion, apply_iteration, apply_de_iteration,
    apply_double_cut_addition, apply_double_cut_removal,
    apply_isolated_vertex_addition, apply_isolated_vertex_removal,
    TransformationError
)

__all__ = [
    # Core classes
    'RelationalGraphWithCuts', 'Vertex', 'Edge', 'Cut', 'ElementID',
    
    # Factory functions
    'create_vertex', 'create_edge', 'create_cut', 'create_empty_graph',
    
    # EGIF processing
    'parse_egif', 'generate_egif',
    
    # Transformations
    'apply_erasure', 'apply_insertion', 'apply_iteration', 'apply_de_iteration',
    'apply_double_cut_addition', 'apply_double_cut_removal',
    'apply_isolated_vertex_addition', 'apply_isolated_vertex_removal',
    
    # Exceptions
    'TransformationError'
]

