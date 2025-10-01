"""
MainWindow - Top-level application window with mode switcher.

Provides three modes:
- Organon: Exploration and corpus management
- Ergasterion: Interactive editing and practice
- Agon: Formal reasoning and gameplay
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from diagram_controller import DiagramController, CommandExecutor


class MainWindow(QMainWindow):
    """
    Main application window with three mode tabs.
    
    Architecture:
    - Each mode has its own tab with specialized UI
    - All modes share a single DiagramController instance
    - Mode switching preserves state in the controller
    - Clean separation between UI (view) and logic (controller)
    """
    
    def __init__(self):
        super().__init__()
        
        # Core controller (single source of truth)
        self.diagram_controller = DiagramController()
        self.command_executor = CommandExecutor(self.diagram_controller)
        
        # Window setup
        self.setWindowTitle("Arisbe - Existential Graphs")
        self.resize(1400, 900)
        
        # Create UI
        self._setup_ui()
        self._setup_menu_bar()
        self._setup_status_bar()
        
        # Start in Organon mode
        self.mode_tabs.setCurrentIndex(0)
    
    def _setup_ui(self):
        """Create the main UI with mode tabs."""
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Mode tabs (Organon, Ergasterion, Agon)
        self.mode_tabs = QTabWidget()
        self.mode_tabs.setTabPosition(QTabWidget.North)
        self.mode_tabs.currentChanged.connect(self._on_mode_changed)
        layout.addWidget(self.mode_tabs)
        
        # Organon tab (Exploration)
        self.organon_widget = self._create_organon_widget()
        self.mode_tabs.addTab(self.organon_widget, "📚 Organon (Explore)")
        
        # Ergasterion tab (Workshop)
        self.ergasterion_widget = self._create_ergasterion_widget()
        self.mode_tabs.addTab(self.ergasterion_widget, "🔨 Ergasterion (Edit)")
        
        # Agon tab (Game)
        self.agon_widget = self._create_agon_widget()
        self.mode_tabs.addTab(self.agon_widget, "⚔️ Agon (Reason)")
    
    def _create_organon_widget(self) -> QWidget:
        """Create the Organon mode widget (placeholder for now)."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel("📚 Organon Mode - Exploration & Corpus Management")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 16pt; padding: 20px;")
        layout.addWidget(label)
        
        status = QLabel("Coming soon: Corpus browser, diagram viewer, export tools")
        status.setAlignment(Qt.AlignCenter)
        status.setStyleSheet("color: gray;")
        layout.addWidget(status)
        
        layout.addStretch()
        return widget
    
    def _create_ergasterion_widget(self) -> QWidget:
        """Create the Ergasterion mode widget (placeholder for now)."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel("🔨 Ergasterion Mode - Interactive Editing & Practice")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 16pt; padding: 20px;")
        layout.addWidget(label)
        
        status = QLabel("Coming soon: Element palette, transformations, undo/redo")
        status.setAlignment(Qt.AlignCenter)
        status.setStyleSheet("color: gray;")
        layout.addWidget(status)
        
        layout.addStretch()
        return widget
    
    def _create_agon_widget(self) -> QWidget:
        """Create the Agon mode widget (placeholder for now)."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel("⚔️ Agon Mode - Formal Reasoning & Endoporeutic Game")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 16pt; padding: 20px;")
        layout.addWidget(label)
        
        status = QLabel("Coming soon: Game board, umpire, hypothesis manager")
        status.setAlignment(Qt.AlignCenter)
        status.setStyleSheet("color: gray;")
        layout.addWidget(status)
        
        layout.addStretch()
        return widget
    
    def _setup_menu_bar(self):
        """Create the menu bar."""
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("&File")
        
        # New action
        new_action = file_menu.addAction("&New Graph")
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._on_new_graph)
        
        # Open action
        open_action = file_menu.addAction("&Open...")
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._on_open_graph)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = file_menu.addAction("E&xit")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        
        # Help menu
        help_menu = menu_bar.addMenu("&Help")
        about_action = help_menu.addAction("&About Arisbe")
        about_action.triggered.connect(self._on_about)
    
    def _setup_status_bar(self):
        """Create the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - No graph loaded")
    
    def _on_mode_changed(self, index: int):
        """Handle mode tab change."""
        modes = ["Organon", "Ergasterion", "Agon"]
        if 0 <= index < len(modes):
            self.status_bar.showMessage(f"Switched to {modes[index]} mode")
    
    def _on_new_graph(self):
        """Create a new empty graph."""
        # For now, just show a message
        QMessageBox.information(
            self,
            "New Graph",
            "New graph creation will be implemented in Phase 2 (Organon)."
        )
    
    def _on_open_graph(self):
        """Open an existing graph."""
        # For now, just show a message
        QMessageBox.information(
            self,
            "Open Graph",
            "Graph loading will be implemented in Phase 2 (Organon)."
        )
    
    def _on_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Arisbe",
            "<h2>Arisbe - Existential Graphs</h2>"
            "<p>A mathematically rigorous implementation of Charles S. Peirce's "
            "Existential Graphs based on Frithjof Dau's formal framework.</p>"
            "<p><b>Version:</b> 0.1.0 (Fresh Start)</p>"
            "<p><b>Architecture:</b> Clean implementation with DiagramController</p>"
            "<hr>"
            "<p><b>Three Modes:</b></p>"
            "<ul>"
            "<li>📚 <b>Organon</b>: Exploration and corpus management</li>"
            "<li>🔨 <b>Ergasterion</b>: Interactive editing and practice</li>"
            "<li>⚔️ <b>Agon</b>: Formal reasoning and gameplay</li>"
            "</ul>"
        )
