#!/usr/bin/env python3
"""
EG-HG Phase 5B: Desktop Application Entry Point

Main entry point for the EG-HG desktop application with Bullpen tools.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path for imports
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings
from PySide6.QtGui import QIcon

# Test imports from existing system
try:
    from graph import EGGraph
    from bullpen import GraphCompositionTool
    from clif_parser import CLIFParser
    from clif_generator import CLIFGenerator
    print("✅ EG System imports successful")
    EG_SYSTEM_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ EG System import failed: {e}")
    EG_SYSTEM_AVAILABLE = False

from gui.main_window import MainWindow


def setup_application():
    """Configure the QApplication with proper settings"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("EG-HG Bullpen")
    app.setApplicationDisplayName("Existential Graphs - Bullpen Tools")
    app.setApplicationVersion("5B.1.0")
    app.setOrganizationName("EG-HG Project")
    
    return app


def main():
    """Main application entry point"""
    print("🚀 Starting EG-HG Phase 5B Desktop Application")
    print(f"📁 Project root: {Path(__file__).parent}")
    print(f"📦 EG System available: {EG_SYSTEM_AVAILABLE}")
    
    # Create and configure application
    app = setup_application()
    
    # Create main window
    main_window = MainWindow()
    
    # Show the window
    main_window.show()
    
    print("✅ Application started successfully")
    
    # Start the event loop
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

