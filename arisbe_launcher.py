#!/usr/bin/env python3
"""
Arisbe Application Launcher

Unified launcher for the three main components of the Arisbe system:
1. Organon (Browser) - Import and explore Existential Graphs
2. Ergasterion (Workshop) - Compose and practice transformations
3. Agon (Endoporeutic Game) - Play Peirce's game and build Universe of Discourse
"""

import sys
import os
from pathlib import Path
from typing import Optional

# Add src and apps to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent / 'apps'))

try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QFrame, QMessageBox, QSplitter, QTextEdit,
        QGroupBox, QStatusBar
    )
    from PySide6.QtGui import QFont, QPixmap, QPainter, QColor, QBrush
    from PySide6.QtCore import Qt, QTimer
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False
    print("PySide6 not available - install with: pip install PySide6")

class ArisbeMainLauncher(QMainWindow):
    """
    Main launcher window for the Arisbe application suite.
    
    Provides access to all three main components with descriptions
    and navigation between them.
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arisbe - Existential Graphs System")
        self.setGeometry(200, 200, 800, 600)
        
        # Component windows
        self.organon_window = None
        self.ergasterion_window = None
        self.agon_window = None
        
        self._setup_ui()
        self._setup_status_bar()
        
    def _setup_ui(self):
        """Setup the main user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Header
        header = self._create_header()
        main_layout.addWidget(header)
        
        # Component selection
        components = self._create_components_section()
        main_layout.addWidget(components)
        
        # Footer
        footer = self._create_footer()
        main_layout.addWidget(footer)
        
    def _create_header(self) -> QWidget:
        """Create the application header."""
        header = QFrame()
        header.setFrameStyle(QFrame.Box)
        header.setStyleSheet("background-color: #f0f0f0; padding: 20px;")
        
        layout = QVBoxLayout(header)
        
        # Title
        title = QLabel("Arisbe")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Existential Graphs System")
        subtitle.setFont(QFont("Arial", 14))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #666;")
        layout.addWidget(subtitle)
        
        # Description
        description = QLabel(
            "A comprehensive system for working with Charles Sanders Peirce's "
            "Existential Graphs, featuring browsing, composition, and interactive gameplay."
        )
        description.setFont(QFont("Arial", 10))
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        description.setStyleSheet("color: #888; margin-top: 10px;")
        layout.addWidget(description)
        
        return header
        
    def _create_components_section(self) -> QWidget:
        """Create the main components selection section."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # Organon component
        organon_card = self._create_component_card(
            "Organon",
            "Browser",
            "Import and explore Existential Graphs in the Arisbe system.\n\n"
            "Features:\n"
            "• Import from EGIF, YAML, JSON formats\n"
            "• Browse corpus of examples\n"
            "• Professional rendering with Dau compliance\n"
            "• Export in multiple formats\n"
            "• Structure analysis and exploration",
            self._launch_organon
        )
        layout.addWidget(organon_card)
        
        # Ergasterion component
        ergasterion_card = self._create_component_card(
            "Ergasterion",
            "Workshop",
            "Compose and practice transformations on Existential Graphs.\n\n"
            "Features:\n"
            "• Interactive EG composition and editing\n"
            "• Formal transformation rules\n"
            "• Mode-aware editing (Warmup vs Practice)\n"
            "• Transformation validation and proof tracking\n"
            "• Visual transformation previews",
            self._launch_ergasterion
        )
        layout.addWidget(ergasterion_card)
        
        # Agon component
        agon_card = self._create_component_card(
            "Agon",
            "Endoporeutic Game",
            "Play Peirce's Endoporeutic Game and build a Universe of Discourse.\n\n"
            "Features:\n"
            "• Interactive gameplay following Peirce's rules\n"
            "• Universe of Discourse construction\n"
            "• Game state tracking and validation\n"
            "• Educational progression through scenarios\n"
            "• Collaborative discourse building",
            self._launch_agon
        )
        layout.addWidget(agon_card)
        
        return widget
        
    def _create_component_card(self, title: str, subtitle: str, description: str, 
                              launch_callback) -> QWidget:
        """Create a component card."""
        card = QGroupBox()
        card.setStyleSheet("""
            QGroupBox {
                border: 2px solid #ddd;
                border-radius: 10px;
                margin: 10px;
                padding: 20px;
                background-color: white;
            }
            QGroupBox:hover {
                border-color: #4CAF50;
            }
        """)
        
        layout = QVBoxLayout(card)
        
        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #333; margin-bottom: 5px;")
        layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel(subtitle)
        subtitle_label.setFont(QFont("Arial", 12))
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: #666; margin-bottom: 15px;")
        layout.addWidget(subtitle_label)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setFont(QFont("Arial", 9))
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #555; line-height: 1.4;")
        layout.addWidget(desc_label)
        
        layout.addStretch()
        
        # Launch button
        launch_btn = QPushButton(f"Launch {title}")
        launch_btn.setFont(QFont("Arial", 12, QFont.Bold))
        launch_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        launch_btn.clicked.connect(launch_callback)
        layout.addWidget(launch_btn)
        
        return card
        
    def _create_footer(self) -> QWidget:
        """Create the application footer."""
        footer = QFrame()
        footer.setFrameStyle(QFrame.Box)
        footer.setStyleSheet("background-color: #f8f8f8; padding: 10px;")
        
        layout = QHBoxLayout(footer)
        
        # System info
        info_label = QLabel("Arisbe v1.0.0 - Built with EGDF serialization and 9-phase layout pipeline")
        info_label.setFont(QFont("Arial", 8))
        info_label.setStyleSheet("color: #666;")
        layout.addWidget(info_label)
        
        layout.addStretch()
        
        # Validation status
        self.validation_label = QLabel("System Status: Checking...")
        self.validation_label.setFont(QFont("Arial", 8))
        self.validation_label.setStyleSheet("color: #666;")
        layout.addWidget(self.validation_label)
        
        # Check system status
        QTimer.singleShot(1000, self._check_system_status)
        
        return footer
        
    def _setup_status_bar(self):
        """Setup status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Select a component to launch")
        
    def _check_system_status(self):
        """Check system integrity status."""
        try:
            # Check if serialization integrity is valid
            from egdf_structural_lock import EGDFStructuralProtector
            
            protector = EGDFStructuralProtector()
            if protector.lock_file.exists():
                is_valid, errors = protector.validate_structural_integrity()
                if is_valid:
                    self.validation_label.setText("System Status: ✅ Protected")
                    self.validation_label.setStyleSheet("color: green;")
                else:
                    self.validation_label.setText("System Status: ⚠️ Issues")
                    self.validation_label.setStyleSheet("color: orange;")
            else:
                self.validation_label.setText("System Status: ❓ Unprotected")
                self.validation_label.setStyleSheet("color: gray;")
                
        except Exception as e:
            self.validation_label.setText("System Status: ❌ Error")
            self.validation_label.setStyleSheet("color: red;")
            
    def _launch_organon(self):
        """Launch the Organon browser component."""
        try:
            if self.organon_window is None:
                from organon.organon_browser import OrganonBrowser
                self.organon_window = OrganonBrowser()
                
            self.organon_window.show()
            self.organon_window.raise_()
            self.organon_window.activateWindow()
            
            self.status_bar.showMessage("Launched Organon - Existential Graph Browser")
            
        except Exception as e:
            QMessageBox.critical(
                self, "Launch Error", 
                f"Failed to launch Organon:\n{e}\n\nEnsure PySide6 is installed and all dependencies are available."
            )
            
    def _launch_ergasterion(self):
        """Launch the Ergasterion workshop component."""
        try:
            if self.ergasterion_window is None:
                from ergasterion.ergasterion_workshop import ErgasterionWorkshop
                self.ergasterion_window = ErgasterionWorkshop()
                
            self.ergasterion_window.show()
            self.ergasterion_window.raise_()
            self.ergasterion_window.activateWindow()
            
            self.status_bar.showMessage("Launched Ergasterion - Existential Graph Workshop")
            
        except Exception as e:
            QMessageBox.critical(
                self, "Launch Error", 
                f"Failed to launch Ergasterion:\n{e}\n\nEnsure PySide6 is installed and all dependencies are available."
            )
            
    def _launch_agon(self):
        """Launch the Agon game component."""
        try:
            if self.agon_window is None:
                from agon.agon_game import AgonGame
                self.agon_window = AgonGame()
                
            self.agon_window.show()
            self.agon_window.raise_()
            self.agon_window.activateWindow()
            
            self.status_bar.showMessage("Launched Agon - Peirce's Endoporeutic Game")
            
        except Exception as e:
            QMessageBox.critical(
                self, "Launch Error", 
                f"Failed to launch Agon:\n{e}\n\nEnsure PySide6 is installed and all dependencies are available."
            )

def main():
    """Main function to run Arisbe launcher."""
    if not PYSIDE6_AVAILABLE:
        print("PySide6 is required to run Arisbe")
        print("Install with: pip install PySide6")
        return 1
        
    app = QApplication(sys.argv)
    app.setApplicationName("Arisbe")
    app.setApplicationVersion("1.0.0")
    app.setApplicationDisplayName("Arisbe - Existential Graphs System")
    
    # Set application style
    app.setStyleSheet("""
        QMainWindow {
            background-color: #fafafa;
        }
    """)
    
    launcher = ArisbeMainLauncher()
    launcher.show()
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
