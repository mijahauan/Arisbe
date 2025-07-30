"""
Arisbe - Existential Graphs Implementation
Based on Frithjof Dau's formalism
"""

__version__ = "1.0.0"
__author__ = "Arisbe Project"
__description__ = "Mathematically rigorous implementation of Existential Graphs"

# Core exports
from .egi_core import EGI, Context, Vertex, Edge, ElementID, ElementType
from .egif_parser import parse_egif
from .egif_generator import generate_egif
from .egi_yaml import serialize_egi_to_yaml, deserialize_egi_from_yaml
from .egi_transformations import EGITransformer, TransformationRule, TransformationError

__all__ = [
    'EGI', 'Context', 'Vertex', 'Edge', 'ElementID', 'ElementType',
    'parse_egif', 'generate_egif',
    'serialize_egi_to_yaml', 'deserialize_egi_from_yaml',
    'EGITransformer', 'TransformationRule', 'TransformationError'
]

