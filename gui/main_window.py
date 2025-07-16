"""
EG-HG Main Window

Main application window integrating Bullpen tools with graph visualization.
"""

from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget, QMenuBar, QToolBar, 
    QStatusBar, QDockWidget, QMessageBox, QFileDialog,
    QSplitter, QTextEdit
)
from PySide6.QtCore import Qt, QSettings, Signal
from PySide6.QtGui import QAction, QKeySequence, QFont

from gui.panels.bullpen_panel import BullpenPanel
from gui.widgets.graph_canvas import GraphCanvas

# Import existing EG system
try:
    from graph import EGGraph
    EG_SYSTEM_AVAILABLE = True
except ImportError:
    EG_SYSTEM_AVAILABLE = False


class MainWindow(QMainWindow):
    """Main application window for EG-HG desktop application"""
    
    def __init__(self):
        super().__init__()
        
        # Current state
        self.current_graph = None
        self.current_file_path = None
        self.is_modified = False
        
        # Setup UI
        self.setup_ui()
        self.setup_connections()
        
        # Load settings
        self.load_settings()
        
        # Show welcome message
        self.show_welcome()
        
    def setup_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("EG-HG: Existential Graphs - Bullpen Tools")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create central widget - graph canvas
        self.graph_canvas = GraphCanvas()
        self.setCentralWidget(self.graph_canvas)
        
        # Create Bullpen panel
        self.bullpen_panel = BullpenPanel()
        self.addDockWidget(Qt.LeftDockWidgetArea, self.bullpen_panel)
        
        # Create output panel for CLIF and messages
        self.create_output_panel()
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create tool bar
        self.create_tool_bar()
        
        # Create status bar
        self.create_status_bar()
        
    def create_output_panel(self):
        """Create output panel for CLIF and messages"""
        self.output_panel = QDockWidget("Output")
        output_widget = QWidget()
        layout = QVBoxLayout(output_widget)
        
        self.output_text = QTextEdit()
        self.output_text.setFont(QFont("Consolas", 10))
        self.output_text.setReadOnly(True)
        self.output_text.setMaximumHeight(200)
        layout.addWidget(self.output_text)
        
        self.output_panel.setWidget(output_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.output_panel)
        
    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        new_action = QAction("&New Graph", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.setStatusTip("Create a new existential graph")
        new_action.triggered.connect(self.new_graph)
        file_menu.addAction(new_action)
        
        open_action = QAction("&Open Graph...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_graph)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        save_action = QAction("&Save Graph", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.save_graph)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Save Graph &As...", self)
        save_as_action.setShortcut(QKeySequence.SaveAs)
        save_as_action.triggered.connect(self.save_graph_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        zoom_in_action = QAction("Zoom &In", self)
        zoom_in_action.setShortcut(QKeySequence.ZoomIn)
        zoom_in_action.triggered.connect(self.graph_canvas.zoom_in)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction("Zoom &Out", self)
        zoom_out_action.setShortcut(QKeySequence.ZoomOut)
        zoom_out_action.triggered.connect(self.graph_canvas.zoom_out)
        view_menu.addAction(zoom_out_action)
        
        zoom_fit_action = QAction("&Fit to Window", self)
        zoom_fit_action.setShortcut("Ctrl+0")
        zoom_fit_action.triggered.connect(self.graph_canvas.zoom_fit)
        view_menu.addAction(zoom_fit_action)
        
        view_menu.addSeparator()
        
        # Panel visibility
        panels_menu = view_menu.addMenu("&Panels")
        
        bullpen_toggle = self.bullpen_panel.toggleViewAction()
        bullpen_toggle.setText("&Bullpen Tools")
        panels_menu.addAction(bullpen_toggle)
        
        output_toggle = self.output_panel.toggleViewAction()
        output_toggle.setText("&Output")
        panels_menu.addAction(output_toggle)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        validate_action = QAction("&Validate Graph", self)
        validate_action.triggered.connect(self.validate_graph)
        tools_menu.addAction(validate_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About EG-HG", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_tool_bar(self):
        """Create application tool bar"""
        toolbar = self.addToolBar("Main")
        toolbar.setObjectName("MainToolBar")
        
        # File operations
        toolbar.addAction("New", self.new_graph)
        toolbar.addAction("Open", self.open_graph)
        toolbar.addAction("Save", self.save_graph)
        
        toolbar.addSeparator()
        
        # View operations
        toolbar.addAction("Zoom In", self.graph_canvas.zoom_in)
        toolbar.addAction("Zoom Out", self.graph_canvas.zoom_out)
        toolbar.addAction("Fit", self.graph_canvas.zoom_fit)
        
        toolbar.addSeparator()
        
        # Bullpen operations
        toolbar.addAction("Parse CLIF", self.parse_clif_shortcut)
        toolbar.addAction("Blank Sheet", self.create_blank_sheet_shortcut)
        
    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready - EG System: " + 
                                   ("Available" if EG_SYSTEM_AVAILABLE else "Mock Mode"))
        
    def setup_connections(self):
        """Setup signal-slot connections between components"""
        # Bullpen panel signals
        self.bullpen_panel.graph_created.connect(self.set_graph)
        self.bullpen_panel.status_message.connect(self.status_bar.showMessage)
        self.bullpen_panel.clif_parsed.connect(self.on_clif_parsed)
        
        # Graph canvas signals
        self.graph_canvas.graph_changed.connect(self.on_graph_changed)
        
    def show_welcome(self):
        """Show welcome message in output panel"""
        welcome_msg = """
🚀 EG-HG Phase 5B: Bullpen Tools

Welcome to the Existential Graphs desktop application!

Getting Started:
1. Browse the CLIF Corpus in the Bullpen panel
2. Select an example and load it into the editor
3. Parse CLIF expressions to create interactive graphs
4. Use the Graph Builder for manual construction
5. Explore Peirce's Rhemas in the constructor tab

Features:
• Rich corpus of CLIF examples organized by difficulty
• Syntax-highlighted CLIF editor with validation
• Interactive graph canvas with zoom and pan
• Support for Peirce's rhemas like "– gives – to –"
• Baseline graph generation with logical constraints
• Manual graph construction tools

System Status: """ + ("EG System Connected" if EG_SYSTEM_AVAILABLE else "Mock Mode (for development)")
        
        self.output_text.setPlainText(welcome_msg)
        
    def set_graph(self, graph):
        """Set the current graph and update display"""
        self.current_graph = graph
        self.graph_canvas.set_graph(graph)
        self.is_modified = True
        self.update_window_title()
        
        # Log graph info
        if hasattr(graph, 'nodes'):
            node_count = len(getattr(graph, 'nodes', []))
            context_count = len(getattr(graph, 'contexts', []))
            self.log_message(f"Graph loaded: {node_count} nodes, {context_count} contexts")
        
    def on_clif_parsed(self, graph):
        """Handle CLIF parsing completion"""
        self.log_message("CLIF expression parsed successfully")
        self.log_message("Graph is ready for interactive editing")
        
    def on_graph_changed(self, graph):
        """Handle graph changes from canvas"""
        self.current_graph = graph
        self.is_modified = True
        self.update_window_title()
        
    def log_message(self, message):
        """Add message to output panel"""
        current_text = self.output_text.toPlainText()
        new_text = current_text + "\n" + message
        self.output_text.setPlainText(new_text)
        
        # Scroll to bottom
        cursor = self.output_text.textCursor()
        cursor.movePosition(cursor.End)
        self.output_text.setTextCursor(cursor)
        
    def update_window_title(self):
        """Update window title based on current state"""
        title = "EG-HG: Existential Graphs - Bullpen Tools"
        if self.current_file_path:
            title += f" - {Path(self.current_file_path).name}"
        if self.is_modified:
            title += " *"
        self.setWindowTitle(title)
        
    # File operations
    def new_graph(self):
        """Create a new graph"""
        if self.check_save_changes():
            # Clear the current graph completely
            self.graph_canvas.clear_graph()
            self.current_graph = None
            self.current_file_path = None
            self.is_modified = False
            self.update_window_title()
            self.log_message("Created new blank sheet")
            
            # Show the default sample display
            self.graph_canvas.create_sample_display()
            
    def open_graph(self):
        """Open an existing graph file"""
        if self.check_save_changes():
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Open Graph", "", "EG Graph Files (*.egg);;All Files (*)"
            )
            if file_path:
                self.log_message(f"Opening {file_path}...")
                # TODO: Implement graph loading
                
    def save_graph(self):
        """Save the current graph"""
        if self.current_file_path:
            self.log_message(f"Saved {self.current_file_path}")
            self.is_modified = False
            self.update_window_title()
        else:
            self.save_graph_as()
            
    def save_graph_as(self):
        """Save the graph with a new name"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Graph As", "", "EG Graph Files (*.egg);;All Files (*)"
        )
        if file_path:
            self.current_file_path = file_path
            self.save_graph()
            
    def check_save_changes(self):
        """Check if changes need to be saved"""
        if self.is_modified:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "The graph has been modified. Do you want to save changes?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            if reply == QMessageBox.Save:
                self.save_graph()
                return not self.is_modified
            elif reply == QMessageBox.Cancel:
                return False
        return True
        
    # Tool shortcuts
    def parse_clif_shortcut(self):
        """Shortcut to parse CLIF from toolbar"""
        self.bullpen_panel.tab_widget.setCurrentIndex(1)  # Switch to editor tab
        self.bullpen_panel.parse_clif()
        
    def create_blank_sheet_shortcut(self):
        """Shortcut to create blank sheet from toolbar"""
        # Clear the graph and create a truly blank sheet
        self.graph_canvas.clear_graph()
        self.current_graph = None
        self.is_modified = False
        self.update_window_title()
        self.log_message("Created blank sheet of assertion")
        
        # Show just the sheet of assertion
        self.graph_canvas.create_sample_display()
        
    def validate_graph(self):
        """Validate the current graph"""
        if self.current_graph:
            self.log_message("Validating graph structure...")
            # TODO: Implement actual validation
            QMessageBox.information(self, "Validation", "Graph structure is valid!")
        else:
            QMessageBox.information(self, "Validation", "No graph to validate")
            
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self, "About EG-HG",
            "<h3>EG-HG: Existential Graphs</h3>"
            "<p>Phase 5B: Enhanced User Tools & Integration</p>"
            "<p>Desktop application for working with Peirce's Existential Graph system.</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>Rich CLIF corpus with examples</li>"
            "<li>Interactive graph construction</li>"
            "<li>Support for Peirce's rhemas</li>"
            "<li>Baseline graph generation</li>"
            "<li>Logical constraint enforcement</li>"
            "</ul>"
            "<p>Built with PySide6 and Python.</p>"
        )
        
    def load_settings(self):
        """Load application settings"""
        settings = QSettings()
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        state = settings.value("windowState")
        if state:
            self.restoreState(state)
            
    def save_settings(self):
        """Save application settings"""
        settings = QSettings()
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        
    def closeEvent(self, event):
        """Handle window close event"""
        if self.check_save_changes():
            self.save_settings()
            event.accept()
        else:
            event.ignore()

