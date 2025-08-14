#!/usr/bin/env python3
"""
Arisbe Existential Graph Works
Main Application Framework

A comprehensive platform for working with Existential Graphs following
Frithjof Dau's formalism, featuring three integrated applications:
- Bullpen: Graph editor with Warmup and Practice modes
- Browser: Universe of Discourse explorer and corpus manager
- Endoporeutic Game: Formal game interface

Author: Arisbe Project
License: MIT
"""

import sys
from typing import Optional
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QMenuBar, QStatusBar, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QFont

# Import salvaged components
from src.canonical import get_canonical_pipeline
from src.diagram_renderer_dau import DiagramRendererDau


class ArisbeEGWorks(QMainWindow):
    """
    Main application window for Arisbe Existential Graph Works.
    
    Provides tabbed interface for three main applications:
    - Bullpen: Primary graph editor
    - Browser: Content explorer (stub)
    - Endoporeutic Game: Game interface (stub)
    """
    
    def __init__(self):
        super().__init__()
        
        # Application metadata
        self.app_name = "Arisbe Existential Graph Works"
        self.version = "1.0.0"
        
        # Initialize canonical pipeline
        self.pipeline = get_canonical_pipeline()
        
        # Setup UI
        self._setup_window()
        self._create_menu_bar()
        self._create_main_interface()
        self._create_status_bar()
        
        # Initialize applications
        self._initialize_applications()
        
        print(f"✓ {self.app_name} initialized successfully")
    
    def _setup_window(self):
        """Configure main window properties."""
        self.setWindowTitle(self.app_name)
        self.setGeometry(100, 100, 1400, 900)
        
        # Set application icon if available
        try:
            self.setWindowIcon(QIcon("assets/arisbe_icon.png"))
        except:
            pass  # Icon not required
        
        # Set minimum size for usability
        self.setMinimumSize(1000, 700)
    
    def _create_menu_bar(self):
        """Create application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        file_menu.addAction("&New Graph", self._new_graph, "Ctrl+N")
        file_menu.addAction("&Open...", self._open_file, "Ctrl+O")
        file_menu.addAction("&Save", self._save_file, "Ctrl+S")
        file_menu.addAction("Save &As...", self._save_as_file, "Ctrl+Shift+S")
        file_menu.addSeparator()
        file_menu.addAction("&Import EGIF...", self._import_egif)
        file_menu.addAction("&Export EGIF...", self._export_egif)
        file_menu.addSeparator()
        file_menu.addAction("E&xit", self.close, "Ctrl+Q")
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        edit_menu.addAction("&Undo", self._undo, "Ctrl+Z")
        edit_menu.addAction("&Redo", self._redo, "Ctrl+Y")
        edit_menu.addSeparator()
        edit_menu.addAction("&Copy", self._copy, "Ctrl+C")
        edit_menu.addAction("&Paste", self._paste, "Ctrl+V")
        edit_menu.addAction("&Delete", self._delete, "Delete")
        
        # View menu
        view_menu = menubar.addMenu("&View")
        view_menu.addAction("&Zoom In", self._zoom_in, "Ctrl+=")
        view_menu.addAction("Zoom &Out", self._zoom_out, "Ctrl+-")
        view_menu.addAction("&Reset Zoom", self._reset_zoom, "Ctrl+0")
        view_menu.addSeparator()
        view_menu.addAction("Show &Annotations", self._toggle_annotations)
        
        # Mode menu (for Bullpen)
        mode_menu = menubar.addMenu("&Mode")
        mode_menu.addAction("&Warmup Mode", self._set_warmup_mode)
        mode_menu.addAction("&Practice Mode", self._set_practice_mode)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        help_menu.addAction("&About", self._show_about)
        help_menu.addAction("&Documentation", self._show_documentation)
    
    def _create_main_interface(self):
        """Create main tabbed interface."""
        # Central widget with tab interface
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Main tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        layout.addWidget(self.tab_widget)
        
        # Create application tabs
        self._create_bullpen_tab()
        self._create_browser_tab()
        self._create_game_tab()
        
        # Set Bullpen as default active tab
        self.tab_widget.setCurrentIndex(0)
    
    def _create_bullpen_tab(self):
        """Create Bullpen (graph editor) tab."""
        from apps.bullpen.bullpen_app import BullpenApp
        
        try:
            self.bullpen_app = BullpenApp(self.pipeline)
            self.tab_widget.addTab(self.bullpen_app, "Bullpen")
            print("✓ Bullpen application loaded")
        except Exception as e:
            # Fallback if Bullpen not ready
            placeholder = QWidget()
            layout = QVBoxLayout(placeholder)
            layout.addWidget(QLabel("Bullpen Graph Editor\n(Loading...)"))
            self.tab_widget.addTab(placeholder, "Bullpen")
            print(f"⚠ Bullpen placeholder: {e}")
    
    def _create_browser_tab(self):
        """Create Browser (content explorer) tab - STUB."""
        browser_widget = QWidget()
        layout = QVBoxLayout(browser_widget)
        
        # Stub content
        title = QLabel("Browser - Universe of Discourse Explorer")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        
        description = QLabel(
            "Browse and explore the evolving Universe of Discourse.\n"
            "Access corpus examples, user collections, and work-in-progress graphs.\n\n"
            "[This application will be implemented in future releases]"
        )
        description.setAlignment(Qt.AlignCenter)
        description.setStyleSheet("color: #666; font-style: italic;")
        
        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addStretch()
        
        self.tab_widget.addTab(browser_widget, "Browser")
        print("✓ Browser stub created")
    
    def _create_game_tab(self):
        """Create Endoporeutic Game tab - STUB."""
        game_widget = QWidget()
        layout = QVBoxLayout(game_widget)
        
        # Stub content
        title = QLabel("Endoporeutic Game")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        
        description = QLabel(
            "Formal game interface for Existential Graph transformations.\n"
            "Practice logical reasoning through structured gameplay.\n\n"
            "[This application will be implemented in future releases]"
        )
        description.setAlignment(Qt.AlignCenter)
        description.setStyleSheet("color: #666; font-style: italic;")
        
        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addStretch()
        
        self.tab_widget.addTab(game_widget, "Endoporeutic Game")
        print("✓ Endoporeutic Game stub created")
    
    def _create_status_bar(self):
        """Create application status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Default status message
        self.status_bar.showMessage(f"{self.app_name} ready")
        
        # Add version info to right side
        version_label = QLabel(f"v{self.version}")
        version_label.setStyleSheet("color: #666;")
        self.status_bar.addPermanentWidget(version_label)
    
    def _initialize_applications(self):
        """Initialize application-specific components."""
        # Set up inter-app communication
        self._setup_app_communication()
        
        # Initialize shared services
        self._initialize_corpus_manager()
        
        # Set up auto-save timer
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self._auto_save)
        self.auto_save_timer.start(300000)  # Auto-save every 5 minutes
    
    def _setup_app_communication(self):
        """Set up communication between applications."""
        # Event bus for cross-app messaging
        self.app_events = {}
        
        # Shared data store
        self.shared_data = {
            'current_graph': None,
            'clipboard': None,
            'recent_files': [],
            'user_preferences': {}
        }
    
    def _initialize_corpus_manager(self):
        """Initialize corpus management system."""
        try:
            from src.corpus_manager import CorpusManager
            self.corpus_manager = CorpusManager()
            print("✓ Corpus manager initialized")
        except Exception as e:
            print(f"⚠ Corpus manager not available: {e}")
            self.corpus_manager = None
    
    # Menu action implementations
    def _new_graph(self):
        """Create new graph."""
        if hasattr(self, 'bullpen_app'):
            self.bullpen_app.new_graph()
        self.status_bar.showMessage("New graph created")
    
    def _open_file(self):
        """Open file dialog."""
        # Implementation will delegate to active app
        self.status_bar.showMessage("Open file...")
    
    def _save_file(self):
        """Save current file."""
        # Implementation will delegate to active app
        self.status_bar.showMessage("File saved")
    
    def _save_as_file(self):
        """Save as dialog."""
        # Implementation will delegate to active app
        self.status_bar.showMessage("Save as...")
    
    def _import_egif(self):
        """Import EGIF file."""
        if hasattr(self, 'bullpen_app'):
            self.bullpen_app.import_egif()
    
    def _export_egif(self):
        """Export EGIF file."""
        if hasattr(self, 'bullpen_app'):
            self.bullpen_app.export_egif()
    
    def _undo(self):
        """Undo last action."""
        current_app = self._get_current_app()
        if hasattr(current_app, 'undo'):
            current_app.undo()
    
    def _redo(self):
        """Redo last undone action."""
        current_app = self._get_current_app()
        if hasattr(current_app, 'redo'):
            current_app.redo()
    
    def _copy(self):
        """Copy selection."""
        current_app = self._get_current_app()
        if hasattr(current_app, 'copy'):
            current_app.copy()
    
    def _paste(self):
        """Paste from clipboard."""
        current_app = self._get_current_app()
        if hasattr(current_app, 'paste'):
            current_app.paste()
    
    def _delete(self):
        """Delete selection."""
        current_app = self._get_current_app()
        if hasattr(current_app, 'delete_selection'):
            current_app.delete_selection()
    
    def _zoom_in(self):
        """Zoom in."""
        current_app = self._get_current_app()
        if hasattr(current_app, 'zoom_in'):
            current_app.zoom_in()
    
    def _zoom_out(self):
        """Zoom out."""
        current_app = self._get_current_app()
        if hasattr(current_app, 'zoom_out'):
            current_app.zoom_out()
    
    def _reset_zoom(self):
        """Reset zoom to 100%."""
        current_app = self._get_current_app()
        if hasattr(current_app, 'reset_zoom'):
            current_app.reset_zoom()
    
    def _toggle_annotations(self):
        """Toggle annotation display."""
        if hasattr(self, 'bullpen_app'):
            self.bullpen_app.toggle_annotations()
    
    def _set_warmup_mode(self):
        """Set Bullpen to Warmup mode."""
        if hasattr(self, 'bullpen_app'):
            self.bullpen_app.set_mode('warmup')
            self.status_bar.showMessage("Warmup mode activated")
    
    def _set_practice_mode(self):
        """Set Bullpen to Practice mode."""
        if hasattr(self, 'bullpen_app'):
            self.bullpen_app.set_mode('practice')
            self.status_bar.showMessage("Practice mode activated")
    
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            f"About {self.app_name}",
            f"""
            <h3>{self.app_name}</h3>
            <p>Version {self.version}</p>
            <p>A comprehensive platform for working with Existential Graphs 
            following Frithjof Dau's formalism.</p>
            <p><b>Applications:</b></p>
            <ul>
            <li><b>Bullpen:</b> Graph editor with Warmup and Practice modes</li>
            <li><b>Browser:</b> Universe of Discourse explorer</li>
            <li><b>Endoporeutic Game:</b> Formal game interface</li>
            </ul>
            <p>Built on the canonical EGIF ↔ EGI ↔ EGDF pipeline.</p>
            """
        )
    
    def _show_documentation(self):
        """Show documentation."""
        self.status_bar.showMessage("Documentation...")
    
    def _auto_save(self):
        """Perform auto-save."""
        current_app = self._get_current_app()
        if hasattr(current_app, 'auto_save'):
            current_app.auto_save()
    
    def _get_current_app(self):
        """Get currently active application widget."""
        return self.tab_widget.currentWidget()
    
    def closeEvent(self, event):
        """Handle application close event."""
        # Check for unsaved changes
        if hasattr(self, 'bullpen_app') and self.bullpen_app.has_unsaved_changes():
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Save:
                self._save_file()
                event.accept()
            elif reply == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
                return
        
        # Clean shutdown
        print(f"✓ {self.app_name} shutting down")
        event.accept()


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Arisbe Existential Graph Works")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Arisbe Project")
    
    # Create and show main window
    window = ArisbeEGWorks()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
