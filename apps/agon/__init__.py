"""
Agon - Peirce's Endoporeutic Game Component

The Agon provides users with the means to play Peirce's Endoporeutic Game
and thereby build a Universe of Discourse.

Core Features:
- Interactive gameplay following Peirce's endoporeutic rules
- Universe of Discourse construction and management
- Game state tracking and validation
- Educational progression through game scenarios
- Collaborative discourse building
"""

from .agon_game import AgonGame
from .universe_builder import UniverseBuilder
from .game_controller import GameController

__all__ = ['AgonGame', 'UniverseBuilder', 'GameController']
