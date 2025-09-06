#!/usr/bin/env python3
"""
Ergasterion - The Arisbe Workshop for Existential Graph Composition and Practice

This is the main entry point for Ergasterion, supporting both standalone use
and integration with Organon through the handoff protocol.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from drawing_editor_refactored import RefactoredDrawingEditor
from organon_ergasterion_protocol import GraphHandoffPackage, OrganonErgasterionBridge
from PySide6.QtWidgets import QApplication


def launch_ergasterion_standalone():
    """Launch Ergasterion in standalone mode."""
    app = QApplication(sys.argv)
    editor = RefactoredDrawingEditor()
    editor.show()
    return app.exec()


def launch_ergasterion_with_handoff(package: GraphHandoffPackage):
    """Launch Ergasterion with a handoff package from Organon."""
    app = QApplication(sys.argv)
    editor = RefactoredDrawingEditor()
    
    # Initialize with handoff package
    success = editor.launch_with_handoff(package)
    if not success:
        print(f"Failed to initialize handoff for {package.graph_id}")
        return 1
    
    editor.show()
    return app.exec()


if __name__ == "__main__":
    # For now, launch in standalone mode
    # In full integration, this would check for handoff arguments
    sys.exit(launch_ergasterion_standalone())
