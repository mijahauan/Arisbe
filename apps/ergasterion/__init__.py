"""
Ergasterion - Existential Graph Workshop Component

The Ergasterion provides users with the means to compose and practice 
transformations on Existential Graphs.

Core Features:
- Interactive EG composition and editing
- Formal transformation rules (Erasure, Insertion, Iteration, Deiteration, Double Cut)
- Mode-aware editing (Warmup vs Practice modes)
- Transformation validation and proof tracking
- Visual transformation previews and guidance
"""

from .ergasterion_workshop import ErgasterionWorkshop
from .transformation_engine import TransformationEngine
from .composition_editor import CompositionEditor

__all__ = ['ErgasterionWorkshop', 'TransformationEngine', 'CompositionEditor']
