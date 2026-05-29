#!/usr/bin/env python3
"""
Arisbe - Home for Existential Graph Inquiry

Named after Charles Sanders Peirce's home in northeast New Jersey,
Arisbe serves as the intellectual workspace for Existential Graph inquiry.

Entry point: Integrated doorway interface
Users enter through the home screen and navigate to Organon/Ergasterion/Agon.

Architecture:
- Home: Central doorway interface with component selection
- Organon: Browser for corpus management and graph navigation
- Ergasterion: Workshop for diagram creation and editing
- Agon: Competition arena for logical evaluation and games
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

# Import the integrated home interface
from arisbe_home import IntegratedArisbeWindow


def main():
    """Main entry point for Arisbe with integrated home interface."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Arisbe")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Arisbe Project")
    
    # Create and show integrated home window with Peirce's house
    main_window = IntegratedArisbeWindow()
    main_window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
