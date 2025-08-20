"""
Organon - Existential Graph Browser Component

The Organon provides users with the means to import and explore 
Existential Graphs within the Arisbe system.

Core Features:
- Import EGs from various formats (EGIF, YAML, JSON)
- Browse and search the corpus of examples
- Visualize EGs with professional rendering
- Export EGs in multiple formats
- Navigate graph structures and relationships
"""

from .organon_browser import OrganonBrowser
# from .corpus_explorer import CorpusExplorer  # TODO: Implement when needed
# from .graph_viewer import GraphViewer  # TODO: Implement when needed

__all__ = ['OrganonBrowser']
