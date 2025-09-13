#!/usr/bin/env python3
"""
Agon - The Arisbe Reasoning and Game Interface

This is the main entry point for Agon, the reasoning component of the 
three-part Arisbe UX architecture (Organon/Ergasterion/Agon).
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from gui.agon_interface import AgonInterface
from PySide6.QtWidgets import QApplication


def launch_agon_standalone():
    """Launch Agon in standalone mode."""
    app = QApplication(sys.argv)
    agon = AgonInterface()
    agon.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(launch_agon_standalone())
