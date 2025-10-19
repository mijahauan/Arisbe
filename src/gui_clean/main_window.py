"""
MainWindow - Top-level application window with mode switcher.

Provides three modes:
- Organon: Exploration and tomos management
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
        """Create the Organon mode widget."""
        from gui_clean.organon.organon_mode import OrganonMode
        
        organon = OrganonMode(self.diagram_controller)
        organon.edit_in_ergasterion.connect(self._on_edit_in_ergasterion)
        return organon
    
    def _create_ergasterion_widget(self) -> QWidget:
        """Create the Ergasterion mode widget."""
        from gui_clean.ergasterion.ergasterion_mode import ErgasterionMode
        
        ergasterion = ErgasterionMode(self.diagram_controller)
        ergasterion.uod_modified.connect(self._on_uod_modified_from_ergasterion)
        ergasterion.new_uod_created.connect(self._on_new_uod_from_ergasterion)
        ergasterion.send_to_agon.connect(self._on_send_to_agon_from_ergasterion)
        ergasterion.cancelled.connect(self._on_ergasterion_cancelled)
        return ergasterion
    
    def _on_save_to_organon_old(self) -> QWidget:
        """Create the Ergasterion mode widget (OLD PLACEHOLDER)."""
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
        
        # View menu
        view_menu = menu_bar.addMenu("&View")
        
        # Theme submenu
        theme_menu = view_menu.addMenu("&Theme")
        
        light_action = theme_menu.addAction("☀️ Light Mode")
        light_action.triggered.connect(lambda: self._set_theme("light"))
        
        dark_action = theme_menu.addAction("🌙 Dark Mode")
        dark_action.triggered.connect(lambda: self._set_theme("dark"))
        
        system_action = theme_menu.addAction("💻 System Default")
        system_action.triggered.connect(lambda: self._set_theme("system"))
        
        # Help menu
        help_menu = menu_bar.addMenu("&Help")
        about_action = help_menu.addAction("&About Arisbe")
        about_action.triggered.connect(self._on_about)
    
    def _setup_status_bar(self):
        """Create the status bar."""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        status_bar.showMessage("Ready - No graph loaded")
    
    def _on_mode_changed(self, index: int):
        """Handle mode tab change."""
        modes = ["Organon", "Ergasterion", "Agon"]
        if 0 <= index < len(modes):
            self.statusBar().showMessage(f"Switched to {modes[index]} mode")
    
    def _on_edit_in_ergasterion(self, data):
        """Handle request to edit EGI in Ergasterion."""
        # Handle tuple format (EGI, source UoD)
        if isinstance(data, tuple):
            egi, source_uod = data
        else:
            egi = data
            source_uod = None
        
        # Switch to Ergasterion tab
        self.mode_tabs.setCurrentIndex(1)
        
        # Load EGI into Ergasterion
        ergasterion_widget = self.mode_tabs.widget(1)
        if hasattr(ergasterion_widget, 'load_egi_for_editing'):
            ergasterion_widget.load_egi_for_editing(egi, source_uod)
            if source_uod:
                self.statusBar().showMessage(f"Loaded '{source_uod.name}' for practice in Ergasterion")
            else:
                self.statusBar().showMessage("Graph loaded in Ergasterion for editing")
    
    def _on_uod_modified_from_ergasterion(self, modified_uod):
        """Handle modified UoD returned from Ergasterion."""
        # Switch back to Organon tab
        self.mode_tabs.setCurrentIndex(0)
        
        # Pass the modified UoD to Organon for saving
        organon_widget = self.mode_tabs.widget(0)
        if hasattr(organon_widget, 'handle_modified_uod_from_ergasterion'):
            organon_widget.handle_modified_uod_from_ergasterion(modified_uod)
            self.statusBar().showMessage(f"Returned to Organon with modifications to '{modified_uod.name}'")
        else:
            self.statusBar().showMessage("Returned to Organon")
    
    def _on_new_uod_from_ergasterion(self, new_uod):
        """Handle new UoD created in Ergasterion to be added to tomos."""
        # Switch back to Organon tab
        self.mode_tabs.setCurrentIndex(0)
        
        # Pass the new UoD to Organon for addition to tomos
        organon_widget = self.mode_tabs.widget(0)
        if hasattr(organon_widget, 'handle_new_uod_from_ergasterion'):
            organon_widget.handle_new_uod_from_ergasterion(new_uod)
            self.statusBar().showMessage(f"New diagram '{new_uod.name}' ready to add to tomos")
        else:
            self.statusBar().showMessage("Returned to Organon with new diagram")
    
    def _on_send_to_agon_from_ergasterion(self, uod):
        """Handle UoD sent to Agon for Endoporeutic Game."""
        # Switch to Agon tab
        self.mode_tabs.setCurrentIndex(2)
        
        # Pass UoD to Agon (when Agon is implemented)
        agon_widget = self.mode_tabs.widget(2)
        if hasattr(agon_widget, 'load_uod_for_game'):
            agon_widget.load_uod_for_game(uod)
            self.statusBar().showMessage(f"Loaded '{uod.name}' in Agon for Endoporeutic Game")
        else:
            # Agon not yet implemented
            self.mode_tabs.setCurrentIndex(0)  # Go back to Organon
            QMessageBox.information(
                self,
                "Agon Coming Soon",
                f"Agon mode is not yet implemented.\n\n"
                f"The diagram '{uod.name}' is ready to use in the\n"
                f"Endoporeutic Game once Agon is complete."
            )
            self.statusBar().showMessage("Agon mode coming soon")
    
    def _on_ergasterion_cancelled(self):
        """Handle cancellation from Ergasterion."""
        # Switch back to Organon tab without changes
        self.mode_tabs.setCurrentIndex(0)
        self.statusBar().showMessage("Returned to Organon (no changes)")
    
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
    
    def _set_theme(self, theme: str):
        """
        Set the application theme.
        
        Args:
            theme: "light", "dark", or "system"
        """
        app = self.window().windowHandle().screen().name()  # Get QApplication instance
        from PySide6.QtWidgets import QApplication
        
        if theme == "light":
            # Light theme - clean, minimal stylesheet
            QApplication.instance().setStyleSheet("""
                QMainWindow, QWidget {
                    background-color: #ffffff;
                    color: #000000;
                }
                QTabWidget::pane {
                    border: 1px solid #cccccc;
                    background-color: #ffffff;
                }
                QTabBar::tab {
                    background-color: #f0f0f0;
                    color: #000000;
                    padding: 8px 16px;
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background-color: #ffffff;
                    border-bottom: 2px solid #0078d4;
                }
                QMenuBar {
                    background-color: #f0f0f0;
                    color: #000000;
                }
                QMenuBar::item:selected {
                    background-color: #e0e0e0;
                }
                QMenu {
                    background-color: #ffffff;
                    color: #000000;
                    border: 1px solid #cccccc;
                }
                QMenu::item:selected {
                    background-color: #e0e0e0;
                }
                QStatusBar {
                    background-color: #f0f0f0;
                    color: #000000;
                }
            """)
            self.statusBar().showMessage("☀️ Switched to Light Mode")
            
        elif theme == "dark":
            # Dark theme - modern dark style
            QApplication.instance().setStyleSheet("""
                QMainWindow, QWidget {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QTabWidget::pane {
                    border: 1px solid #3c3c3c;
                    background-color: #2b2b2b;
                }
                QTabBar::tab {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    padding: 8px 16px;
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background-color: #2b2b2b;
                    border-bottom: 2px solid #0078d4;
                }
                QMenuBar {
                    background-color: #3c3c3c;
                    color: #ffffff;
                }
                QMenuBar::item:selected {
                    background-color: #4c4c4c;
                }
                QMenu {
                    background-color: #2b2b2b;
                    color: #ffffff;
                    border: 1px solid #3c3c3c;
                }
                QMenu::item:selected {
                    background-color: #3c3c3c;
                }
                QStatusBar {
                    background-color: #3c3c3c;
                    color: #ffffff;
                }
                QLabel {
                    color: #ffffff;
                }
            """)
            self.statusBar().showMessage("🌙 Switched to Dark Mode")
            
        else:  # system
            # Clear custom stylesheet to use system default
            QApplication.instance().setStyleSheet("")
            self.statusBar().showMessage("💻 Using System Default Theme")
    
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
            "<li>📚 <b>Organon</b>: Exploration and tomos management</li>"
            "<li>🔨 <b>Ergasterion</b>: Interactive editing and practice</li>"
            "<li>⚔️ <b>Agon</b>: Formal reasoning and gameplay</li>"
            "</ul>"
        )
