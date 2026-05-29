"""
Main application entry point for Arisbe GUI.

Clean implementation using production-ready components:
- DiagramController for state management
- LayoutDTO for rendering
- GraphvizSVGRenderer for correct SVG output
- Zero legacy dependencies

Usage:
    python -m src.gui_clean.main_application
    
Or from repo root:
    python src/gui_clean/main_application.py
"""

import sys
from pathlib import Path

# Ensure src/ is on path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication

from gui_clean.main_window import MainWindow


def main():
    """Launch the Arisbe GUI application."""
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Arisbe")
    app.setOrganizationName("Arisbe Project")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
