#!/usr/bin/env python3
"""
EG-HG Phase 5B: Desktop Application Entry Point

This is the main entry point for the EG-HG desktop application.
It sets up the PySide6 application and integrates with the existing
EG-HG system in the src/ directory.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path for imports
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings, QStandardPaths
from PySide6.QtGui import QIcon

from gui.main_window import MainWindow


def setup_application():
    """Configure the QApplication with proper settings"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("EG-HG")
    app.setApplicationDisplayName("Existential Graphs - Hypergraphs")
    app.setApplicationVersion("5B.0.1")
    app.setOrganizationName("EG-HG Project")
    app.setOrganizationDomain("eg-hg.org")
    
    # Set application icon (if available)
    icon_path = Path(__file__).parent / "resources" / "icons" / "app_icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    return app


def main():
    """Main application entry point"""
    # Create and configure application
    app = setup_application()
    
    # Create main window
    main_window = MainWindow()
    
    # Show the window
    main_window.show()
    
    # Start the event loop
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

