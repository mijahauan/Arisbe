"""
EG-HG GUI Widgets Package

Custom Qt widgets for displaying and interacting with existential graphs.
"""

from .graph_canvas import GraphCanvas
from .context_widget import ContextWidget
from .node_widget import NodeWidget
from .edge_widget import EdgeWidget

__all__ = [
    "GraphCanvas",
    "ContextWidget", 
    "NodeWidget",
    "EdgeWidget"
]

