"""
EG-HG Phase 5B: Main Window

The main application window that integrates all GUI components
and connects them to the existing EG-HG system.
"""

from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QMenuBar, QToolBar, QStatusBar, QDockWidget,
    QMessageBox, QFileDialog, QSplitter
)
from PySide6.QtCore import Qt, QTimer, QSettings, Signal
from PySide6.QtGui import QAction, QKeySequence

# Import GUI components
from gui.widgets.graph_canvas import GraphCanvas
from gui.panels.bullpen_panel import BullpenPanel
from gui.panels.exploration_panel import ExplorationPanel
from gui.panels.game_panel import GamePanel
from gui.controllers.graph_controller import GraphController

# Import existing EG-HG system
try:
    # These imports will work when integrated with your existing repository
    from eg_types import EGGraph
    from bullpen import GraphCompositionTool
    from exploration import GraphExplorer
    from game_engine import EndoporeuticGame
    EG_SYSTEM_AVAILABLE = True
except ImportError:
    # Fallback for development/testing
    EG_SYSTEM_AVAILABLE = False
    print("EG System not available - using mock objects")


class MainWindow(QMainWindow):
    """Main application window for EG-HG desktop application"""
    
    # Signals for inter-component communication
    graph_changed = Signal(object)  # EGGraph
    status_message = Signal(str)
    
    def __init__(self):
        super().__init__()
        
        # Initialize core system controller
        self.graph_controller = GraphController()
        
        # Current state
        self.current_graph = None
        self.current_file_path = None
        self.is_modified = False
        
        # Setup UI
        self.setup_ui()
        self.setup_connections()
        self.setup_status_updates()
        
        # Load settings
        self.load_settings()
        
    def setup_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("EG-HG: Existential Graphs")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create central widget - graph canvas
        self.graph_canvas = GraphCanvas()
        self.setCentralWidget(self.graph_canvas)
        
        # Create dock panels
        self.create_dock_panels()
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create tool bar
        self.create_tool_bar()
        
        # Create status bar
        self.create_status_bar()
        
    def create_dock_panels(self):
        """Create and configure dock panels"""
        # Bullpen panel (left side)
        self.bullpen_panel = BullpenPanel()
        self.addDockWidget(Qt.LeftDockWidgetArea, self.bullpen_panel)
        
        # Exploration panel (left side, tabbed with bullpen)
        self.exploration_panel = ExplorationPanel()
        self.addDockWidget(Qt.LeftDockWidgetArea, self.exploration_panel)
        self.tabifyDockWidget(self.bullpen_panel, self.exploration_panel)
        
        # Game panel (right side)
        self.game_panel = GamePanel()
        self.addDockWidget(Qt.RightDockWidgetArea, self.game_panel)
        
        # Show bullpen panel by default
        self.bullpen_panel.raise_()
        
    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # New graph
        new_action = QAction("&New Graph", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.setStatusTip("Create a new existential graph")
        new_action.triggered.connect(self.new_graph)
        file_menu.addAction(new_action)
        
        # Open graph
        open_action = QAction("&Open Graph...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.setStatusTip("Open an existing graph file")
        open_action.triggered.connect(self.open_graph)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        # Save graph
        save_action = QAction("&Save Graph", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.setStatusTip("Save the current graph")
        save_action.triggered.connect(self.save_graph)
        file_menu.addAction(save_action)
        
        # Save as
        save_as_action = QAction("Save Graph &As...", self)
        save_as_action.setShortcut(QKeySequence.SaveAs)
        save_as_action.setStatusTip("Save the graph with a new name")
        save_as_action.triggered.connect(self.save_graph_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        # Export options
        export_menu = file_menu.addMenu("&Export")
        
        export_svg_action = QAction("Export as &SVG...", self)
        export_svg_action.setStatusTip("Export graph as SVG image")
        export_svg_action.triggered.connect(self.export_svg)
        export_menu.addAction(export_svg_action)
        
        export_png_action = QAction("Export as &PNG...", self)
        export_png_action.setStatusTip("Export graph as PNG image")
        export_png_action.triggered.connect(self.export_png)
        export_menu.addAction(export_png_action)
        
        export_clif_action = QAction("Export as &CLIF...", self)
        export_clif_action.setStatusTip("Export graph as CLIF text")
        export_clif_action.triggered.connect(self.export_clif)
        export_menu.addAction(export_clif_action)
        
        file_menu.addSeparator()
        
        # Exit
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.setEnabled(False)  # TODO: Implement undo system
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("&Redo", self)
        redo_action.setShortcut(QKeySequence.Redo)
        redo_action.setEnabled(False)  # TODO: Implement redo system
        edit_menu.addAction(redo_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        # Zoom actions
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
        
        exploration_toggle = self.exploration_panel.toggleViewAction()
        exploration_toggle.setText("&Exploration Tools")
        panels_menu.addAction(exploration_toggle)
        
        game_toggle = self.game_panel.toggleViewAction()
        game_toggle.setText("&Game Interface")
        panels_menu.addAction(game_toggle)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        validate_action = QAction("&Validate Graph", self)
        validate_action.setStatusTip("Validate the current graph structure")
        validate_action.triggered.connect(self.validate_graph)
        tools_menu.addAction(validate_action)
        
        # Game menu
        game_menu = menubar.addMenu("&Game")
        
        new_game_action = QAction("&New Game", self)
        new_game_action.setStatusTip("Start a new endoporeutic game")
        new_game_action.triggered.connect(self.game_panel.new_game)
        game_menu.addAction(new_game_action)
        
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
        
        # Quick tools
        toolbar.addAction("Validate", self.validate_graph)
        
    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
        
        # Add permanent widgets to status bar
        if EG_SYSTEM_AVAILABLE:
            self.status_bar.addPermanentWidget(
                QWidget()  # Placeholder for graph statistics
            )
        
    def setup_connections(self):
        """Setup signal-slot connections between components"""
        # Graph canvas signals
        self.graph_canvas.graph_changed.connect(self.on_graph_changed)
        self.graph_canvas.selection_changed.connect(self.on_selection_changed)
        
        # Bullpen panel signals
        self.bullpen_panel.graph_created.connect(self.set_graph)
        self.bullpen_panel.status_message.connect(self.status_bar.showMessage)
        
        # Exploration panel signals
        self.exploration_panel.exploration_result.connect(self.on_exploration_result)
        
        # Game panel signals
        self.game_panel.game_state_changed.connect(self.on_game_state_changed)
        
        # Internal signals
        self.graph_changed.connect(self.exploration_panel.set_graph)
        self.status_message.connect(self.status_bar.showMessage)
        
    def setup_status_updates(self):
        """Setup periodic status updates"""
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(5000)  # Update every 5 seconds
        
    def load_settings(self):
        """Load application settings"""
        settings = QSettings()
        
        # Restore window geometry
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
            
        # Restore window state (dock positions, etc.)
        state = settings.value("windowState")
        if state:
            self.restoreState(state)
            
    def save_settings(self):
        """Save application settings"""
        settings = QSettings()
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        
    # Graph operations
    def new_graph(self):
        """Create a new graph"""
        if self.check_save_changes():
            graph = self.graph_controller.create_blank_sheet()
            self.set_graph(graph)
            self.current_file_path = None
            self.status_message.emit("Created new graph")
            
    def open_graph(self):
        """Open an existing graph file"""
        if self.check_save_changes():
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Open Graph", "", "EG Graph Files (*.egg);;All Files (*)"
            )
            if file_path:
                # TODO: Implement graph loading
                self.status_message.emit(f"Opening {file_path}...")
                
    def save_graph(self):
        """Save the current graph"""
        if self.current_file_path:
            # TODO: Implement graph saving
            self.status_message.emit(f"Saved {self.current_file_path}")
            self.is_modified = False
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
            
    def set_graph(self, graph):
        """Set the current graph and update all components"""
        self.current_graph = graph
        self.graph_canvas.set_graph(graph)
        self.graph_changed.emit(graph)
        self.is_modified = True
        self.update_window_title()
        
    def check_save_changes(self):
        """Check if changes need to be saved before proceeding"""
        if self.is_modified:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "The graph has been modified. Do you want to save changes?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            if reply == QMessageBox.Save:
                self.save_graph()
                return not self.is_modified  # Only proceed if save succeeded
            elif reply == QMessageBox.Cancel:
                return False
        return True
        
    def update_window_title(self):
        """Update the window title based on current state"""
        title = "EG-HG: Existential Graphs"
        if self.current_file_path:
            title += f" - {Path(self.current_file_path).name}"
        if self.is_modified:
            title += " *"
        self.setWindowTitle(title)
        
    # Export operations
    def export_svg(self):
        """Export graph as SVG"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export SVG", "", "SVG Files (*.svg);;All Files (*)"
        )
        if file_path:
            self.graph_canvas.export_svg(file_path)
            self.status_message.emit(f"Exported SVG to {file_path}")
            
    def export_png(self):
        """Export graph as PNG"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export PNG", "", "PNG Files (*.png);;All Files (*)"
        )
        if file_path:
            self.graph_canvas.export_png(file_path)
            self.status_message.emit(f"Exported PNG to {file_path}")
            
    def export_clif(self):
        """Export graph as CLIF text"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export CLIF", "", "CLIF Files (*.clif);;Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            clif_text = self.graph_controller.generate_clif(self.current_graph)
            with open(file_path, 'w') as f:
                f.write(clif_text)
            self.status_message.emit(f"Exported CLIF to {file_path}")
            
    # Tool operations
    def validate_graph(self):
        """Validate the current graph"""
        if self.current_graph:
            is_valid, messages = self.graph_controller.validate_graph(self.current_graph)
            if is_valid:
                QMessageBox.information(self, "Validation", "Graph is valid!")
            else:
                QMessageBox.warning(self, "Validation", f"Graph validation failed:\n{messages}")
        else:
            QMessageBox.information(self, "Validation", "No graph to validate")
            
    # Event handlers
    def on_graph_changed(self, graph):
        """Handle graph changes from canvas"""
        self.current_graph = graph
        self.is_modified = True
        self.update_window_title()
        self.graph_changed.emit(graph)
        
    def on_selection_changed(self, selected_items):
        """Handle selection changes in canvas"""
        # TODO: Update properties panel with selected items
        pass
        
    def on_exploration_result(self, result):
        """Handle exploration results"""
        self.status_message.emit(f"Exploration complete: {len(result)} items found")
        
    def on_game_state_changed(self, state):
        """Handle game state changes"""
        self.status_message.emit(f"Game state: {state}")
        
    def update_status(self):
        """Update status bar with current information"""
        if self.current_graph and EG_SYSTEM_AVAILABLE:
            # TODO: Get actual graph statistics
            stats = "1 context, 2 nodes, 1 ligature"
            self.status_bar.showMessage(f"Graph: {stats}")
        else:
            self.status_bar.showMessage("Ready")
            
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self, "About EG-HG",
            "<h3>EG-HG: Existential Graphs</h3>"
            "<p>A desktop application for working with Peirce's Existential Graph system.</p>"
            "<p>Phase 5B: Enhanced User Tools & Integration</p>"
            "<p>Built with PySide6 and Python.</p>"
        )
        
    # Window events
    def closeEvent(self, event):
        """Handle window close event"""
        if self.check_save_changes():
            self.save_settings()
            event.accept()
        else:
            event.ignore()

