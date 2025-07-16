"""
EG-HG Phase 5B: PySide6 GUI Package

This package provides the desktop GUI interface for the EG-HG system.
It integrates with the existing core system in the src/ directory.
"""

__version__ = "5B.0.1"
__author__ = "EG-HG Project"

# GUI package imports
from .main_window import MainWindow
from .widgets.graph_canvas import GraphCanvas
from .panels.bullpen_panel import BullpenPanel
from .panels.exploration_panel import ExplorationPanel
from .panels.game_panel import GamePanel

__all__ = [
    "MainWindow",
    "GraphCanvas", 
    "BullpenPanel",
    "ExplorationPanel",
    "GamePanel"
]

